from langchain_core.documents import Document

from customer_support.retrieval import (
    HybridRetriever,
    KeywordRetriever,
    reciprocal_rank_fusion,
)


def doc(key):
    return Document(page_content=key, metadata={"chunk_id": key})


def test_document_found_by_both_channels_ranks_first_and_is_unique():
    result = reciprocal_rank_fusion([[doc("a"), doc("b")], [doc("b"), doc("c")]])
    assert [document.metadata["chunk_id"] for document in result] == ["b", "a", "c"]


def test_keyword_retriever_finds_exact_business_policy():
    documents = [
        Document(
            page_content="退款审核通过后 3–5 个工作日到账",
            metadata={"chunk_id": "refund", "source": "refund.md"},
        ),
        Document(
            page_content="订单发货后联系承运商申请改派",
            metadata={"chunk_id": "shipping", "source": "shipping.md"},
        ),
    ]
    result = KeywordRetriever(documents, k=1).invoke("退款多久到账？")
    assert result[0].metadata["source"] == "refund.md"


class EmptySemanticRetriever:
    def invoke(self, _question):
        return []


def test_hybrid_retriever_uses_keyword_results_when_semantic_channel_is_empty():
    refund = Document(
        page_content="退款审核通过后 3–5 个工作日到账",
        metadata={"chunk_id": "refund", "source": "refund.md"},
    )
    hybrid = HybridRetriever(
        EmptySemanticRetriever(), KeywordRetriever([refund]), limit=3
    )
    assert hybrid.invoke("退款多久到账？") == [refund]
