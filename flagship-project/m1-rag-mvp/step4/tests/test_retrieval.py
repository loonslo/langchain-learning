from langchain_core.documents import Document
from customer_support.assistant import REFUSAL, CustomerSupportAssistant
from customer_support.retrieval import (
    HybridRetriever,
    KeywordRetriever,
    reciprocal_rank_fusion,
)


def doc(key):
    return Document(page_content=key, metadata={"chunk_id": key})


def test_document_found_by_both_channels_ranks_first_and_is_unique():
    result = reciprocal_rank_fusion([[doc("a"), doc("b")], [doc("b"), doc("c")]])
    assert [d.metadata["chunk_id"] for d in result] == ["b", "a", "c"]


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


FAQ = Document(
    page_content="人工客服工作时间为周一至周五，客服会在下一个工作日处理",
    metadata={"chunk_id": "faq", "source": "customer_faq.md"},
)


def test_keyword_retriever_ignores_matches_on_common_single_characters():
    retriever = KeywordRetriever([FAQ])

    assert retriever.invoke("今天天气怎么样") == []
    assert retriever.invoke("帮我写一首诗") == []


def test_one_matched_word_is_not_enough_unless_the_question_has_only_one_word():
    refund = Document(page_content="退款审核通过后 3–5 个工作日到账", metadata={"chunk_id": "refund"})

    assert KeywordRetriever([refund]).invoke("退款政策怎么样") == []
    assert KeywordRetriever([refund], min_matches=1).invoke("退款政策怎么样") == [refund]
    assert KeywordRetriever([refund]).invoke("退款") == [refund]


def test_irrelevant_question_leaves_hybrid_empty_so_the_assistant_refuses_without_the_model():
    class Model:
        def invoke(self, _messages):
            raise AssertionError("没有证据时不应调用模型")

    hybrid = HybridRetriever(EmptySemanticRetriever(), KeywordRetriever([FAQ]), limit=3)

    assert CustomerSupportAssistant(hybrid, Model()).ask("今天天气怎么样").text == REFUSAL
