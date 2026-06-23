"""
capstone/evaluation.py · 自动化评测：指标 + 报告 + 失败用例库
==========================================================
整合 day17-22：读评测集 → 跑 RAG → 算拒答率/关键词命中 → 出 markdown 报告
+ 归档失败用例。这是项目的★护城河模块。
==========================================================
"""

import json
from datetime import datetime
from pathlib import Path

import config as C
from knowledge_base import KnowledgeBase

REFUSE_HINTS = ["没有提到", "我不知道", "未提及", "无法回答", "未涉及", "找不到", "没有相关"]


def _refused(ans: str) -> bool:
    return any(h in ans for h in REFUSE_HINTS)


def load_eval_set() -> list[dict]:
    if not C.EVAL_SET.exists():
        raise FileNotFoundError(f"先准备评测集 {C.EVAL_SET}（见 data/eval_set.json 示例）")
    return json.loads(C.EVAL_SET.read_text(encoding="utf-8"))


def run(kb: KnowledgeBase) -> dict:
    chain = kb.chain()
    rows, failures = [], []
    refuse_total = refuse_ok = ans_total = kw_ok = 0

    for case in load_eval_set():
        q = case["question"]
        ans = chain.invoke(q)
        refused = _refused(ans)

        if case.get("should_refuse"):
            refuse_total += 1
            passed = refused
            refuse_ok += passed
        else:
            kws = case.get("keywords", [])
            passed = all(k in ans for k in kws) if kws else True
            if kws:
                ans_total += 1
                kw_ok += passed
        rows.append({"q": q, "passed": passed, "ans": ans})

        if not passed:
            ctx = [d.page_content for d in kb.retriever.invoke(q)]
            kws = case.get("keywords", [])
            retrieved_ok = any(any(k in c for k in kws) for c in ctx) if kws else None
            cause = ("召回了但生成错" if retrieved_ok else
                     "应拒答却乱答" if case.get("should_refuse") else "检索没召回")
            failures.append({"q": q, "ans": ans, "cause": cause})

    metrics = {
        "拒答正确率": f"{refuse_ok}/{refuse_total}" if refuse_total else "n/a",
        "关键词命中率": f"{kw_ok}/{ans_total}" if ans_total else "n/a",
        "失败数": len(failures),
    }
    _write_report(rows, failures, metrics)
    C.FAILURES_PATH.write_text(json.dumps(failures, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    return metrics


def _write_report(rows, failures, metrics):
    lines = [f"# RAG 评测报告", f"\n生成时间：{datetime.now():%Y-%m-%d %H:%M}", "\n## 指标\n"]
    for k, v in metrics.items():
        lines.append(f"- {k}：{v}")
    lines += ["\n## 逐条\n", "| 问题 | 通过 |", "|------|------|"]
    for r in rows:
        lines.append(f"| {r['q']} | {'✓' if r['passed'] else '✗'} |")
    if failures:
        lines.append("\n## 失败用例\n")
        for f in failures:
            lines.append(f"- **{f['q']}** — {f['cause']}")
    C.REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已写入 {C.REPORT_PATH}")


if __name__ == "__main__":
    kb = KnowledgeBase().build()
    print("评测结果：", run(kb))
