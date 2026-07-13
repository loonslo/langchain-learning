"""
阶段2评测平台：质量 + 成本 + 延迟 + 失败用例 + 回归记录。

默认 offline 模式使用可复现的演示回答，保证没 API key 也能跑通看板链路。
需要真实评测时运行：
    python -m evals.run_eval_platform --mode live

给初学者的流程说明：
1. 加载 evals/eval_cases.json 中的评测用例。
2. 对每个用例生成答案（offline 用固定演示答案，live 用真实 RAG 链）。
3. 用 keyword_score / citation_score / refusal_ok 判定是否通过。
4. 记录延迟、token、成本，汇总成 summary。
5. 把结果追加到 reports/eval_runs.csv，供 dashboard 画回归曲线。
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

# 判定拒答时用到的关键词
REFUSE_HINTS = ["没有提到", "信息不足", "无法回答", "我不知道", "无相关", "未提及"]

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "eval_cases.json"
REPORTS = ROOT / "reports"
HISTORY = REPORTS / "eval_runs.csv"
FAILURES = REPORTS / "failures.json"
LATEST = REPORTS / "latest_report.md"


def load_cases() -> list[dict]:
    """加载评测用例。"""
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def git_rev() -> str:
    """获取当前 git commit 短 hash，用于把评测结果和代码版本关联。"""
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True)
        return out.strip()
    except Exception:
        return "no-git"


def offline_answer(case: dict, prompt_variant: str) -> str:
    """离线演示答案：不调用真实 LLM，保证没 API key 也能跑。

    strict/helpful 两版答案略有差异，模拟 prompt A/B 的效果。
    """
    if case.get("should_refuse"):
        return "文档中没有提到，信息不足，无法回答。"

    suffix = "【来源：test_doc.txt】" if case.get("expected_sources") else ""
    if prompt_variant == "strict":
        return f"{case['reference']} {suffix}".strip()
    return f"{case['reference']} 简单说，要用评测集和回归指标持续验证。{suffix}".strip()


def _get_retriever():
    """构建 retriever 并缓存：整轮评测只建一次向量库，避免每条 case 重复建库（慢 + 刷屏）。"""
    from day12_rag_pdf_sources import build_retriever
    if _get_retriever._cache is None:
        _get_retriever._cache = build_retriever("test_doc.txt")
    return _get_retriever._cache
_get_retriever._cache = None


def _get_chain(prompt_variant: str):
    """构建 RAG chain 并缓存（同 variant 只建一次）。"""
    from day12_rag_pdf_sources import build_rag_chain
    cache = _get_chain._cache
    if prompt_variant not in cache:
        retriever = _get_retriever()
        temperature = 0.0 if prompt_variant == "strict" else 0.2
        cache[prompt_variant] = build_rag_chain(retriever, temperature=temperature)
    return cache[prompt_variant]
_get_chain._cache = {}


def live_answer(case: dict, prompt_variant: str) -> tuple[str, str]:
    """真实答案：调用 day12 的 RAG 链生成，并回填真实检索上下文。

    返回 (answer, retrieval_context)。retrieval_context 是真实召回的
    文本拼接，供 day26 用 DeepEval 这类成熟框架算 Faithfulness /
    ContextualPrecision —— 没有它，框架指标就是无本之木（自证循环）。

    retriever / chain 整轮只构建一次（见 _get_retriever / _get_chain 缓存），
    不会每条 case 重复建向量库，也不会刷屏 day12 的「共切成 N 块」日志。
    """
    retriever = _get_retriever()
    docs = retriever.invoke(case["question"])
    retrieval_context = "\n\n".join(d.page_content for d in docs)

    chain = _get_chain(prompt_variant)
    answer = chain.invoke(case["question"])
    return answer, retrieval_context


def looks_refused(answer: str) -> bool:
    """判断答案是否看起来像拒答。"""
    return any(h in answer for h in REFUSE_HINTS)


def score_case(case: dict, answer: str) -> dict:
    """对单个用例打分。

    指标：
    - refusal_ok    : 拒答行为是否符合预期
    - keyword_score : 关键词命中比例
    - citation_score: 期望来源命中比例
    - passed        : 综合是否通过
    """
    refused = looks_refused(answer)
    should_refuse = bool(case.get("should_refuse"))

    # 只有期望拒答时才要求答案拒答；否则答案不应拒答。
    refusal_ok = (refused == should_refuse)

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
    """粗略估算 token 数和成本。

    这里按"2 个字符 ≈ 1 个 token"估算，价格按 $2/M tokens 计算。
    真实项目应使用分词器和实际模型价格。
    """
    tokens = max(1, len(answer) // 2)
    return tokens, round(tokens * 0.000002, 6)


def run(mode: str, prompt_variant: str) -> dict:
    """跑一轮评测并写入历史记录。"""
    REPORTS.mkdir(exist_ok=True)
    cases = load_cases()
    results = []
    total_latency = total_tokens = total_cost = 0.0

    for case in cases:
        started = time.perf_counter()
        if mode == "live":
            answer, retrieval_context = live_answer(case, prompt_variant)
        else:
            answer = offline_answer(case, prompt_variant)
            retrieval_context = ""   # offline 无真实检索，框架指标需 live 才有意义
        latency_ms = (time.perf_counter() - started) * 1000
        tokens, cost = estimate_cost(answer)
        result = score_case(case, answer)
        result.update({
            "latency_ms": round(latency_ms, 1),
            "tokens": tokens,
            "cost_usd": cost,
            "retrieval_context": retrieval_context,
            # 透传原始用例字段，供 day26 调 DeepEval 时构造完整 LLMTestCase
            # （ContextualPrecision 需要 expected_output=reference；input 需要真实 question）
            "question": case.get("question", ""),
            "reference": case.get("reference", ""),
        })
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
    """把 summary 追加到 CSV，作为回归曲线数据源。"""
    exists = HISTORY.exists()
    with HISTORY.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(summary)


def write_report(summary: dict, failures: list[dict]) -> None:
    """生成 Markdown 格式的最新报告。"""
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
        lines.append(
            f"- `{item['case_id']}` {item['type']} "
            f"keyword={item['keyword_score']} citation={item['citation_score']} "
            f"refusal_ok={item['refusal_ok']}"
        )
    LATEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="阶段2 RAG 评测平台")
    parser.add_argument("--mode", choices=["offline", "live"], default="offline", help="offline=演示答案，live=真实 LLM")
    parser.add_argument("--prompt", choices=["strict", "helpful"], default="strict", help="prompt 变体")
    args = parser.parse_args()
    print(json.dumps(run(args.mode, args.prompt), ensure_ascii=False, indent=2))
