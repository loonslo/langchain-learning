from langchain_core.documents import Document
from customer_support.retrieval import reciprocal_rank_fusion


def doc(key):
    return Document(page_content=key, metadata={"chunk_id": key})


def test_document_found_by_both_channels_ranks_first_and_is_unique():
    result = reciprocal_rank_fusion([[doc("a"), doc("b")], [doc("b"), doc("c")]])
    assert [d.metadata["chunk_id"] for d in result] == ["b", "a", "c"]
