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
    """产生英文词、中文单字和中文双字词。"""

    normalized = text.lower()
    tokens = ASCII_WORD.findall(normalized)
    for run in CHINESE_RUN.findall(normalized):
        tokens.extend(run)
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
    return tokens


class Retriever(Protocol):
    def invoke(self, question: str) -> list[Document]: ...


@dataclass
class KeywordRetriever:
    documents: list[Document]
    k: int = 3
    k1: float = 1.5
    b: float = 0.75

    def __post_init__(self) -> None:
        self._tokens = [tokenize(document.page_content) for document in self.documents]
        self._document_frequency = Counter(
            token for tokens in self._tokens for token in set(tokens)
        )
        self._average_length = (
            sum(len(tokens) for tokens in self._tokens) / len(self._tokens)
            if self._tokens
            else 0.0
        )

    def invoke(self, question: str) -> list[Document]:
        query_tokens = set(tokenize(question))
        if not query_tokens or not self.documents:
            return []
        scores = [self._score(tokens, query_tokens) for tokens in self._tokens]
        ranked = sorted(
            range(len(self.documents)),
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
