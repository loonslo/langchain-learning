import pytest

from ai_testing.rag_eval import RetrievalCase, evaluate_retrieval


def test_rag_metrics_distinguish_recall_precision_rank_and_citation():
    metrics = evaluate_retrieval(
        [
            RetrievalCase(
                "refund",
                relevant_sources=("refund.md",),
                retrieved_sources=("faq.md", "refund.md"),
                cited_sources=("refund.md",),
            )
        ],
        k=2,
    )

    assert metrics.recall_at_k == 1.0
    assert metrics.precision_at_k == 0.5
    assert metrics.mrr == 0.5
    assert metrics.citation_coverage == 1.0


def test_empty_retrieval_is_a_recall_failure_and_invalid_k_is_rejected():
    metrics = evaluate_retrieval([RetrievalCase("x", ("faq.md",), ())])

    assert metrics.recall_at_k == 0.0
    assert metrics.precision_at_k == 0.0
    with pytest.raises(ValueError, match="k"):
        evaluate_retrieval([], k=0)
