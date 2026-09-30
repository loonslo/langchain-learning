"""不调用大模型也能运行的 RAG 召回、排序和引用评测。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalCase:
    """一条检索评测样本：应命中的来源、实际召回的来源（按排名）、答案实际引用的来源。"""

    case_id: str
    relevant_sources: tuple[str, ...]
    retrieved_sources: tuple[str, ...]
    cited_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalMetrics:
    """四个指标在所有样本上的平均值。"""

    recall_at_k: float
    precision_at_k: float
    mrr: float
    citation_coverage: float


def _safe_average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate_retrieval(cases: list[RetrievalCase], k: int = 3) -> RetrievalMetrics:
    """对每个样本取前 k 个召回结果（先截取再去重），计算后取平均：

    - recall@k：命中的相关来源 ÷ 全部相关来源；
    - precision@k：命中数 ÷ 去重后的召回数；
    - MRR：第一个相关来源排名的倒数，没有命中记 0；
    - citation_coverage：被引用的相关来源 ÷ 全部相关来源。

    relevant_sources 为空（应拒答）的样本：recall 和 citation_coverage 记 1.0，
    precision 和 MRR 恒为 0.0。混入拒答样本会拉低 precision 和 MRR，应按样本类型分开看。
    """
    if k < 1:
        raise ValueError("k 必须大于 0")
    recalls: list[float] = []
    precisions: list[float] = []
    reciprocal_ranks: list[float] = []
    citation_coverages: list[float] = []

    for case in cases:
        relevant = set(case.relevant_sources)
        retrieved = list(dict.fromkeys(case.retrieved_sources[:k]))
        hits = [source for source in retrieved if source in relevant]
        recalls.append(len(set(hits)) / len(relevant) if relevant else 1.0)
        precisions.append(len(hits) / len(retrieved) if retrieved else 0.0)
        reciprocal_ranks.append(
            next((1 / index for index, source in enumerate(retrieved, 1) if source in relevant), 0.0)
        )
        cited = set(case.cited_sources)
        citation_coverages.append(len(cited & relevant) / len(relevant) if relevant else 1.0)

    return RetrievalMetrics(
        recall_at_k=_safe_average(recalls),
        precision_at_k=_safe_average(precisions),
        mrr=_safe_average(reciprocal_ranks),
        citation_coverage=_safe_average(citation_coverages),
    )
