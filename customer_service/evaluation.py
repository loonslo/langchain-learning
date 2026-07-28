"""
customer_service/evaluation.py · 客服评估：意图准确率 / 解决率 / 转人工率 / 多轮
==========================================================
★护城河模块：和 capstone/evaluation.py 是同一套方法论，换了业务指标——
知识库看"拒答率+关键词命中"，客服看：
  - intent_acc   意图分类准确率（路由错=后面全错，最上游指标）
  - resolution   解决率（非转人工回答且命中期望关键词）
  - escalation   转人工率（该转的转了=对；不该转的转了=误伤）
  - multiturn    多轮指代能否靠会话历史解决
离线可跑（规则意图 + BM25 FAQ），配 key 后同一份评估集测 LLM 版，直接对比。
==========================================================
"""

import json
import uuid
from datetime import datetime

import config as C
import graph


def load_eval_set() -> list[dict]:
    return json.loads(C.EVAL_SET.read_text(encoding="utf-8"))


def _check(case: dict, out: dict) -> dict:
    intent_ok = out["intent"] == case["intent"]
    kw_ok = all(k in out["answer"] for k in case.get("keywords", []))
    esc_expected = bool(case.get("escalate"))
    esc_ok = out["escalated"] == esc_expected
    resolved = (not out["escalated"]) and kw_ok
    return {"question": case["question"], "intent_expected": case["intent"],
            "intent_got": out["intent"], "intent_ok": intent_ok,
            "kw_ok": kw_ok, "esc_ok": esc_ok, "resolved": resolved,
            "answer": out["answer"]}


def run() -> dict:
    rows, failures = [], []
    n_turns = esc_count = 0

    for case in load_eval_set():
        turns = case.get("session") or [case]
        sid = f"eval-{uuid.uuid4().hex[:8]}"     # 每条用例独立会话，互不污染
        for t in turns:
            out = graph.chat(sid, t["question"])
            r = _check(t, out)
            rows.append(r)
            n_turns += 1
            esc_count += int(out["escalated"])
            if not (r["intent_ok"] and r["kw_ok"] and r["esc_ok"]):
                failures.append(r)

    m = {
        "mode": "offline" if C.OFFLINE else "live",
        "turns": n_turns,
        "intent_acc": sum(r["intent_ok"] for r in rows) / n_turns,
        "resolution_rate": sum(r["resolved"] for r in rows) / n_turns,
        "escalation_rate": esc_count / n_turns,
        "escalation_correct": sum(r["esc_ok"] for r in rows) / n_turns,
    }

    C.REPORTS_DIR.mkdir(exist_ok=True)
    report = [f"# 客服评估报告 {datetime.now():%Y-%m-%d %H:%M}（{m['mode']}）\n"]
    report.append(f"- 意图准确率: {m['intent_acc']:.0%}")
    report.append(f"- 解决率: {m['resolution_rate']:.0%}")
    report.append(f"- 转人工率: {m['escalation_rate']:.0%}（判定正确 {m['escalation_correct']:.0%}）")
    report.append(f"\n## 失败用例（{len(failures)}）\n")
    for f in failures:
        report.append(f"- Q: {f['question']} | 意图 {f['intent_expected']}→{f['intent_got']}"
                      f" | 命中={f['kw_ok']} | A: {f['answer'][:60]}")
    (C.REPORTS_DIR / "latest_report.md").write_text("\n".join(report), encoding="utf-8")
    (C.REPORTS_DIR / "failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(m, ensure_ascii=False, indent=2))
    print(f"报告已写入 {C.REPORTS_DIR / 'latest_report.md'}")
    return m


if __name__ == "__main__":
    run()
