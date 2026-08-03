"""向量存储契约：业务层不依赖 Chroma 或 pgvector 的具体实现。"""

from typing import Protocol
from langchain_core.documents import Document


class VectorStore(Protocol):
    def upsert(self, documents: list[Document]) -> None: ...
    def delete_source(self, source_id: str) -> None: ...
    def search(self, tenant_id: str, query: str, k: int) -> list[Document]: ...
