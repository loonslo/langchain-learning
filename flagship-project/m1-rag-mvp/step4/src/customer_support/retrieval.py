"""生产混合检索：BM25 风格关键词排序与语义排序通过 RRF 融合。"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from langchain_core.documents import Document


ASCII_WORD = re.compile(r"[a-zA-Z0-9_-]+")
CHINESE_RUN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """产生英文词、中文单字和中文双字词，兼顾精确业务名与自然问法。"""

    normalized = text.lower()
    tokens = ASCII_WORD.findall(normalized)
    for run in CHINESE_RUN.findall(normalized):
        tokens.extend(run)
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
    return tokens


def content_terms(text: str) -> set[str]:
    """判断“有没有证据”用的词：英文词和中文双字词，不含单个汉字。

    单个汉字（“会”“怎”“天”）到处都有，命中一个字说明不了问题和资料相关。
    """

    return {
        token
        for token in tokenize(text)
        if not (len(token) == 1 and CHINESE_RUN.fullmatch(token))
    }


class Retriever(Protocol):
    def invoke(self, question: str) -> list[Document]: ...


@dataclass
class KeywordRetriever:
    """无需外部服务的 BM25 关键词检索器，只返回“有证据”的片段。

    BM25 分数只负责排序；能不能返回，先看问题里的词（英文词、中文双字词）命中了几个：
    至少命中 min_matches 个；问题本身的词不足 min_matches 个时，要求全部命中。
    这样“今天天气怎么样”不会因为撞上“会”“怎”之类的常用字就召回片段，
    step1 的“没有证据就不调用模型、直接拒答”在混合检索后仍然成立。
    """

    documents: list[Document]
    k: int = 3
    k1: float = 1.5
    b: float = 0.75
    min_matches: int = 2

    def __post_init__(self) -> None:
        if self.min_matches < 1:
            raise ValueError("min_matches 必须大于 0")
        self._tokens = [tokenize(document.page_content) for document in self.documents]
        self._terms = [content_terms(document.page_content) for document in self.documents]
        self._document_frequency = Counter(
            token for tokens in self._tokens for token in set(tokens)
        )
        self._average_length = (
            sum(len(tokens) for tokens in self._tokens) / len(self._tokens)
            if self._tokens
            else 0.0
        )

    def invoke(self, question: str) -> list[Document]:
        """按 BM25 分数取前 k 个“有证据”的片段：问题里的词至少命中 min_matches 个才可能返回，问题词不足时要求全部命中。"""
        query_tokens = set(tokenize(question))
        query_terms = content_terms(question)
        if not query_terms or not self.documents:
            return []
        needed = min(self.min_matches, len(query_terms))
        scores = [self._score(tokens, query_tokens) for tokens in self._tokens]
        ranked = sorted(
            (
                index
                for index in range(len(self.documents))
                if len(query_terms & self._terms[index]) >= needed
            ),
            key=lambda index: (
                -scores[index],
                str(self.documents[index].metadata.get("chunk_id", index)),
            ),
        )
        return [self.documents[index] for index in ranked if scores[index] > 0][: self.k]

    def _score(self, tokens: list[str], query_tokens: set[str]) -> float:
        if not tokens or not self._average_length:
            return 0.0
        frequencies = Counter(tokens)
        total = 0.0
        document_count = len(self.documents)
        for token in query_tokens:
            frequency = frequencies[token]
            if not frequency:
                continue
            document_frequency = self._document_frequency[token]
            inverse_frequency = math.log(
                1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            denominator = frequency + self.k1 * (
                1 - self.b + self.b * len(tokens) / self._average_length
            )
            total += inverse_frequency * frequency * (self.k1 + 1) / denominator
        return total


@dataclass
class HybridRetriever:
    """对同一个用户问题执行两路检索并返回统一排名。"""

    semantic: Retriever
    keyword: Retriever
    limit: int = 3

    def invoke(self, question: str) -> list[Document]:
        return reciprocal_rank_fusion(
            [self.semantic.invoke(question), self.keyword.invoke(question)],
            limit=self.limit,
        )


def reciprocal_rank_fusion(
    rankings: list[list[Document]], limit: int = 3
) -> list[Document]:
    """RRF：每个排名里第 r 名得 1/(60+r) 分，按 chunk_id 累加；两路都命中的片段得分更高。
    返回得分最高的 limit 个，同分按 chunk_id 排序。文档必须有 metadata['chunk_id']。
    """
    if limit < 1:
        raise ValueError("limit 必须大于 0")
    scores: dict[str, float] = {}
    documents: dict[str, Document] = {}
    for ranking in rankings:
        for rank, document in enumerate(ranking, 1):
            key = str(document.metadata["chunk_id"])
            documents[key] = document
            scores[key] = scores.get(key, 0.0) + 1 / (60 + rank)
    keys = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
    return [documents[key] for key in keys]
