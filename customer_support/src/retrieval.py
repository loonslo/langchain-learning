"""生产混合检索：BM25 风格关键词排序与语义排序通过 RRF 融合。

这是“找资料”层。关键词检索擅长命中明确的业务词，语义检索擅长理解相近说法；
RRF（倒数排名融合）再综合两条检索通道的名次，降低单一路径漏检的概率。
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from langchain_core.documents import Document

# 正则表达式是描述文本匹配规则的语法：前者找连续的英文/数字词，后者找连续中文。
ASCII_WORD = re.compile(r"[a-zA-Z0-9_-]+")
CHINESE_RUN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """把文本拆成英文词、中文单字和中文双字词，供关键词检索计数。"""

    # 小写化让英文检索不受大小写影响，例如 ``VIP`` 和 ``vip`` 可视为同一个词。
    normalized = text.lower()
    tokens = ASCII_WORD.findall(normalized)
    for run in CHINESE_RUN.findall(normalized):
        # 中文没有天然空格分词。加入单字和相邻双字词，是无需额外分词模型的简化策略。
        tokens.extend(run)
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
    return tokens


class Retriever(Protocol):
    """统一检索器接口：给问题，返回按相关度排序的文档块。"""

    def invoke(self, question: str) -> list[Document]: ...


@dataclass
class KeywordRetriever:
    """用 BM25 思想给包含相同关键词的文档块打分并排序。

    它不调用大模型，所有统计量在初始化时由已有文档计算出来，适合作为语义检索的补充。
    """
    documents: list[Document]
    k: int = 3
    k1: float = 1.5
    b: float = 0.75

    def __post_init__(self) -> None:
        """在 dataclass 自动初始化字段后，预先计算检索时会反复使用的统计量。"""
        self._tokens = [tokenize(document.page_content) for document in self.documents]
        # document frequency（文档频率）表示“有多少篇文档出现了这个词”。
        self._document_frequency = Counter(
            token for tokens in self._tokens for token in set(tokens)
        )
        self._average_length = (
            sum(len(tokens) for tokens in self._tokens) / len(self._tokens)
            if self._tokens
            else 0.0
        )

    def invoke(self, question: str) -> list[Document]:
        """为问题中的每个词计算分数，返回得分大于零的前 k 个文档块。"""
        query_tokens = set(tokenize(question))
        if not query_tokens or not self.documents:
            return []
        scores = [self._score(tokens, query_tokens) for tokens in self._tokens]
        # 分数相同则按 chunk_id 排序，使重复运行时顺序保持稳定。
        ranked = sorted(
            range(len(self.documents)),
            key=lambda index: (
                -scores[index],
                str(self.documents[index].metadata.get("chunk_id", index)),
            ),
        )
        return [self.documents[index] for index in ranked if scores[index] > 0][: self.k]

    def _score(self, tokens: list[str], query_tokens: set[str]) -> float:
        """计算一个文档块与问题的 BM25 风格相关度分数。"""
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
            # 罕见词的区分度更高；常见词（例如“的”）对结果影响更小。
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
    """同时运行语义和关键词检索，并把它们的结果交给 RRF 融合。"""
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
    """按 RRF 规则融合多个“已排序的结果列表”。

    同一文档在多条列表中名次靠前时会累加更多分数。这里的 60 是常用平滑常数，
    用来避免第 1 名的优势过大；它不是资料数量或返回条数。
    """
    if limit < 1:
        raise ValueError("limit 必须大于 0")
    scores: dict[str, float] = {}
    documents: dict[str, Document] = {}
    for ranking in rankings:
        for rank, document in enumerate(ranking, 1):
            # enumerate(..., 1) 从第 1 名开始编号，而非 Python 默认的第 0 名。
            key = str(document.metadata["chunk_id"])
            documents[key] = document
            scores[key] = scores.get(key, 0.0) + 1 / (60 + rank)
    keys = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
    return [documents[key] for key in keys]
