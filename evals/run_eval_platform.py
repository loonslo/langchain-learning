"""
阶段2评测平台：质量 + 成本 + 延迟 + 失败用例 + 回归记录。

默认 offline 模式使用可复现的演示回答，保证没 API key 也能跑通看板链路。
需要真实评测时运行：
    python -m evals.run_eval_platform --mode live
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

REFUSE_HINTS = ["没有提到", "信息不足", "无法回答", "不知道", "无相关"]
ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "eval_cases.json"
REPORTS = ROOT / "reports"
HISTORY = REPORTS / "eval_runs.csv"
FAILURES = REPORTS / "failures.json"
LATEST = REPORTS / "latest_report.md"


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def git_rev() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True)
        return out.strip()
    except Exception:
        return "no-git"


def offline_answer(case: dict, prompt_variant: str) -> str:
    if case.get("should_refuse"):
        return "文档中没有提到，信息不足，无法回答。"
    suffix = "【来源：test_doc.txt】" if case.get("expected_sources") else ""
    if prompt_variant == "strict":
        return f"{case['reference']} {suffix}".strip()
    return f"{case['reference']} 简单说，要用评测集和回归指标持续验证。{suffix}".strip()


def live_answer(case: dict, prompt_variant: str) -> str:
    from day11_rag_pdf_sources import build_retriever, build_rag_chain

    retriever = build_retriever("test_doc.txt")
    temperature = 0.0 if prompt_variant == "strict" else 0.2
    chain = build_rag_chain(retriever, temperature=temperature)
    return chain.invoke(case["question"])


def looks_refused(answer: str) -> bool:
    return any(h in answer for h in REFUSE_HINTS)


def score_case(case: dict, answer: str) -> dict:
    refused = looks_refused(answer)
    should_refuse = bool(case.get("should_refuse"))
    refusal_ok = (refused == should_refuse) if should_refuse else True

    keywords = case.get("keywords", [])
    keyword_hits = sum(1 for k in keywords if k.lower() in answer.lower())
    keyword_score = keyword_hits / len(keywords) if keywords else 1.0

    sources = case.get("expected_sources", [])
    source_hits = sum(1 for s in sources if s in answer)
    citation_score = source_hits / len(sources) if sources else 1.0

    passed = refusal_ok and keyword_score >= 0.67 and citation_score >= 0.67
    return {
        "case_id": case["id"],
        "type": case["type"],
        "passed": passed,
        "refusal_ok": refusal_ok,
        "keyword_score": round(keyword_score, 3),
        "citation_score": round(citation_score, 3),
        "answer": answer,
    }


def estimate_cost(answer: str) -> tuple[int, float]:
    tokens = max(1, len(answer) // 2)
    return tokens, round(tokens * 0.000002, 6)


def run(mode: str, prompt_variant: str) -> dict:
    REPORTS.mkdir(exist_ok=True)
    cases = load_cases()
    results = []
    total_latency = total_tokens = total_cost = 0.0

    for case in cases:
        started = time.perf_counter()
        answer = live_answer(case, prompt_variant) if mode == "live" else offline_answer(case, prompt_variant)
        latency_ms = (time.perf_counter() - started) * 1000
        tokens, cost = estimate_cost(answer)
        result = score_case(case, answer)
        result.update({"latency_ms": round(latency_ms, 1), "tokens": tokens, "cost_usd": cost})
        results.append(result)
        total_latency += latency_ms
        total_tokens += tokens
        total_cost += cost

    passed = sum(1 for r in results if r["passed"])
    failures = [r for r in results if not r["passed"]]
    summary = {
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "commit": git_rev(),
        "mode": mode,
        "prompt_variant": prompt_variant,
        "cases": len(results),
        "pass_rate": round(passed / len(results), 4),
        "avg_keyword_score": round(sum(r["keyword_score"] for r in results) / len(results), 4),
        "avg_citation_score": round(sum(r["citation_score"] for r in results) / len(results), 4),
        "avg_latency_ms": round(total_latency / len(results), 1),
        "total_tokens": int(total_tokens),
        "total_cost_usd": round(total_cost, 6),
        "failures": len(failures),
    }
    write_history(summary)
    FAILURES.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, failures)
    return summary


def write_history(summary: dict) -> None:
    exists = HISTORY.exists()
    with HISTORY.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(summary)


def write_report(summary: dict, failures: list[dict]) -> None:
    lines = [
        "# 最新评测报告",
        "",
        f"- run_id: `{summary['run_id']}`",
        f"- commit: `{summary['commit']}`",
        f"- mode: `{summary['mode']}` / prompt: `{summary['prompt_variant']}`",
        f"- 用例数: {summary['cases']}",
        f"- 通过率: {summary['pass_rate']:.1%}",
        f"- 平均关键词分: {summary['avg_keyword_score']:.1%}",
        f"- 平均引用分: {summary['avg_citation_score']:.1%}",
        f"- 平均延迟: {summary['avg_latency_ms']} ms",
        f"- token / 成本: {summary['total_tokens']} / ${summary['total_cost_usd']}",
        f"- 失败数: {summary['failures']}",
        "",
        "## 失败用例",
    ]
    if not failures:
        lines.append("无。")
    for item in failures[:20]:
        lines.append(f"- `{item['case_id']}` {item['type']} keyword={item['keyword_score']} citation={item['citation_score']}")
    LATEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    parser.add_argument("--prompt", choices=["strict", "helpful"], default="strict")
    args = parser.parse_args()
    print(json.dumps(run(args.mode, args.prompt), ensure_ascii=False, indent=2))
