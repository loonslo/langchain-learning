"""验证多文档摄取和真实检索器的连接方式。"""

from langchain_core.embeddings import Embeddings

from src.ingestion import ingest_directory
from src.knowledge import build_retriever
from src.settings import PROJECT_ROOT


class ConstantEmbeddings(Embeddings):
    """只替代昂贵 embedding 服务；生产摄取与 Chroma 仍使用真实实现。"""

    def embed_documents(self, texts):
        # 为每段文字返回同一个极小向量：足以驱动测试，但不会下载或运行真实 embedding 模型。
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0]


def test_multi_document_chunks_have_stable_traceable_ids():
    # 连续摄取两次同一资料，编号必须相同，才能可靠定位某个文档块。
    directory = PROJECT_ROOT / "data" / "knowledge"
    first, second = ingest_directory(directory), ingest_directory(directory)
    assert {document.metadata["source_id"] for document in first} >= {
        "refund",
        "shipping",
    }
    assert [document.metadata["chunk_id"] for document in first] == [
        document.metadata["chunk_id"] for document in second
    ]


def test_production_retriever_builds_from_the_whole_directory():
    # 这里构建的仍是生产 Retriever，只把昂贵的向量模型替换为 ConstantEmbeddings。
    retriever = build_retriever(
        PROJECT_ROOT / "data" / "knowledge",
        ConstantEmbeddings(),
        k=10,
        threshold=0.0,
    )

    documents = retriever.invoke("退款和配送政策")

    assert {document.metadata["source"] for document in documents} >= {
        "refund.md",
        "shipping.md",
    }
