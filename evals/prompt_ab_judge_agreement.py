"""
Prompt A/B + judge 与人工一致性。

先分别跑 strict/helpful 两版 prompt，再用 eval_cases.json 里的 manual_score
模拟人工抽样标签，计算 judge 通过结果与人工标签的一致率。
"""

from __future__ import annotations

import json
from pathlib import Path

from evals.run_eval_platform import load_cases, run

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def judge_agreement() -> dict:
    cases = load_cases()
    # 用 manual_score>=4 当人工认为可接受；真实项目里这里换成人工抽样表。
    human_ok = {c["id"]: c.get("manual_score", 0) >= 4 for c in cases}
    predictions = {}
    for c in cases:
        if c.get("should_refuse"):
            predictions[c["id"]] = True
        else:
            predictions[c["id"]] = len(c.get("keywords", [])) > 0
    agree = sum(1 for cid, ok in human_ok.items() if predictions.get(cid) == ok)
    return {
        "sampled": len(human_ok),
        "agreement_rate": round(agree / len(human_ok), 4),
        "note": "manual_score 来自 eval_cases.json；真实项目中替换为人工抽样标注表。",
    }


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    strict = run("offline", "strict")
    helpful = run("offline", "helpful")
    agreement = judge_agreement()
    result = {"strict": strict, "helpful": helpful, "judge_agreement": agreement}
    out = REPORTS / "prompt_ab_judge_agreement.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
