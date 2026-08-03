"""最终离线验收清单；任一关键安全行为失败都不能毕业。"""

REQUIRED = (
    "rag_answer",
    "refusal",
    "citation",
    "order_isolation",
    "injection_block",
    "ticket",
    "persistence",
    "quality_gate",
    "backup",
)


def accept(results: dict[str, bool]):
    missing = [name for name in REQUIRED if not results.get(name, False)]
    return {"passed": not missing, "failed": missing}
