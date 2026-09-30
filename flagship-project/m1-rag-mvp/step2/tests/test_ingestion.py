from langchain_core.embeddings import Embeddings

from customer_support.ingestion import ingest_directory
from customer_support.knowledge import build_retriever
from customer_support.settings import PROJECT_ROOT


class ConstantEmbeddings(Embeddings):
    """只替代昂贵 embedding 服务；Chroma 和生产摄取链仍使用真实实现。"""

    def embed_documents(self, texts):
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0]


def test_multi_document_chunks_have_stable_traceable_ids():
    directory = PROJECT_ROOT / "data" / "knowledge"
    first, second = ingest_directory(directory), ingest_directory(directory)
    assert {d.metadata["source_id"] for d in first} >= {"refund", "shipping"}
    assert [d.metadata["chunk_id"] for d in first] == [
        d.metadata["chunk_id"] for d in second
    ]


def test_production_retriever_builds_from_the_whole_directory():
    directory = PROJECT_ROOT / "data" / "knowledge"
    retriever = build_retriever(
        directory,
        ConstantEmbeddings(),
        k=10,
        threshold=0.0,
    )

    documents = retriever.invoke("退款和配送政策")

    assert {document.metadata["source"] for document in documents} >= {
        "refund.md",
        "shipping.md",
    }
