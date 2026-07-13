"""
Day 26 · 生产级失败诊断（DeepEval）—— 纯诊断版
===========================================================
测试工程师转 AI 应用开发  ★护城河：失败诊断能力★

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
职责边界（第一性）
  本文件只做一件事：**诊断**——回答"这条失败到底坏在哪一层"。
  发布判决（门禁）不在这里做，统一归 Day58：
    capstone/ci_gate.py + .github/workflows/eval-gate.yml
  一个文件一个职责：诊断出证据 → 门禁拿证据拦 PR。两套判决就是分叉。

两层诊断（诚实分工）
  ── 一级分流：复用 run_eval_platform 已算好的硬指标做「弱信号」分组
     硬指标（refusal_ok / keyword_score / citation_score）测的是字符串，
     测不准语义，所以只用来分组标注「疑似层」，不做结论。便宜、无需 key。

  ── 二级复核：DeepEval 维度分（仅 live 模式，吃真实 retrieval_context）
     Faithfulness       : 答案是否忠于召回上下文（揪出幻觉）
     AnswerRelevancy    : 答案是否切题（揪出答非所问）
     ContextualPrecision: 召回内容是否真相关（揪出检索层问题）
       ⚠ 需要参考答案（ground truth）；case 缺 reference 时**跳过该指标**
         并明确标注，绝不喂空串算出垃圾分。
     DeepEval 也是 LLM-as-judge，有固有漏检，结论一律标注「证据/建议」。

运行方式
  python -m evals.run_eval_platform --mode live   # 1. 先回填真实 retrieval_context
  python day26_eval_report_failures.py            # 2. 自动推断模式并诊断
  python day26_eval_report_failures.py --limit 5  # 3. 控制 LLM 评测条数（控成本）

  offline 模式（failures.json 无真实 context）只做一级分流，不调框架。

产出：reports/diagnosis_day26.json（失败根因分布 + 每条证据）
下游：capstone/ci_gate.py（Day58）读评测结果做发布判决
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import argparse
import json
import sys
from pathlib import Path

REPORTS = Path(__file__).resolve().parent / "reports"
FAILURES = REPORTS / "failures.json"
DIAGNOSIS = REPORTS / "diagnosis_day26.json"

# 与 run_eval_platform 一致的硬指标阈值（仅用于一级弱信号分流）
CITE_THRESHOLD = 0.67
KEYWORD_THRESHOLD = 0.67
# DeepEval 维度分低于此值时，在证据里标注「疑似」（只是标注，不是判决）
DIM_FLAG = 0.7


# ═══════════════════════════════════════════════════════════════
# 一、加载失败库（带真实 retrieval_context 才可信）
# ═══════════════════════════════════════════════════════════════

def load_failures() -> tuple[list[dict], str]:
    """返回 (失败列表, failures.json 来源模式)。

    来源模式通过是否携带真实 retrieval_context 推断：
      - 任一失败 case 带非空 retrieval_context → live 产物（维度分可信）
      - 否则 → offline 产物（只能做一级分流）
    """
    if not FAILURES.exists():
        print("[WARN] 未找到 reports/failures.json")
        print("  请先运行：python -m evals.run_eval_platform --mode live")
        sys.exit(2)
    data = json.loads(FAILURES.read_text(encoding="utf-8"))
    failures = [d for d in data if not d.get("passed", True)]
    is_live = any((f.get("retrieval_context") or "").strip() for f in failures)
    return failures, ("live" if is_live else "offline")


# ═══════════════════════════════════════════════════════════════
# 二、一级分流：硬指标弱信号分组（零依赖，明确标注「疑似/待复核」）
# ═══════════════════════════════════════════════════════════════

def classify_by_hard_metrics(failure: dict) -> tuple[str, str]:
    """用硬指标做「弱信号」分组。只分组，不判决——判决靠二级复核。"""
    refusal_ok = failure.get("refusal_ok", True)
    keyword = failure.get("keyword_score", 1.0)
    citation = failure.get("citation_score", 1.0)

    if not refusal_ok:
        return ("拒答逻辑层(疑似)", "refusal_ok=False：建议复核拒答决策是否正确")
    if citation < CITE_THRESHOLD:
        return ("检索/引用层(疑似)", f"citation_score={citation:.2f} < {CITE_THRESHOLD}：建议用 ContextualPrecision 复核")
    if keyword < KEYWORD_THRESHOLD:
        return ("生成层(疑似)", f"keyword_score={keyword:.2f} < {KEYWORD_THRESHOLD}：建议用 Faithfulness/AnswerRelevancy 复核")
    return ("其他/未覆盖(疑似)", "硬指标通过但整体未通过，需人工复核（如工具调用约束）")


# ═══════════════════════════════════════════════════════════════
# 三、二级复核：DeepEval 维度分（成熟框架，吃真实 retrieval_context）
# ═══════════════════════════════════════════════════════════════

def measure_with_deepeval(failure: dict) -> dict:
    """对单条失败 case 调 DeepEval 算维度分。需 DEEPSEEK_API_KEY。

    诚实规则：
      - 无 retrieval_context → 上游数据不完整，直接不算（调用方已拦）
      - 无 reference/expected_output → ContextualPrecision 跳过并标注，
        不喂空 ground truth 算垃圾分
    """
    from dotenv import load_dotenv
    load_dotenv()

    from deepeval.models.llms.deepseek_model import DeepSeekModel
    from deepeval.metrics import (
        FaithfulnessMetric,
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
    )
    from deepeval.test_case import LLMTestCase

    eval_model = DeepSeekModel(model="deepseek-chat")
    retrieval_context = failure.get("retrieval_context") or ""
    expected_output = failure.get("reference") or failure.get("expected_output") or ""

    tc = LLMTestCase(
        input=failure.get("question", failure.get("case_id", "")),
        actual_output=failure.get("answer", ""),
        expected_output=expected_output,
        retrieval_context=[retrieval_context] if retrieval_context else [],
    )

    out = {}
    # 每条指标独立 try，单条失败不拖垮整轮诊断
    try:
        m = FaithfulnessMetric(model=eval_model, async_mode=False)
        out["faithfulness"] = round(m.measure(tc), 3)
    except Exception as e:
        out["faithfulness"] = f"error:{e}"
    try:
        m = AnswerRelevancyMetric(model=eval_model, async_mode=False)
        out["answer_relevancy"] = round(m.measure(tc), 3)
    except Exception as e:
        out["answer_relevancy"] = f"error:{e}"
    if expected_output.strip():
        try:
            m = ContextualPrecisionMetric(model=eval_model, async_mode=False)
            out["contextual_precision"] = round(m.measure(tc), 3)
        except Exception as e:
            out["contextual_precision"] = f"error:{e}"
    else:
        out["contextual_precision"] = "skipped:缺参考答案(reference)，不喂空 ground truth"
    return out


def dims_to_evidence(dims: dict) -> str:
    """把维度分翻译成可读证据（标注为建议，非判决）。"""
    ev = []
    for key, label in [
        ("faithfulness", "答案不忠于上下文(疑似幻觉)"),
        ("answer_relevancy", "答案不切题(疑似答非所问)"),
        ("contextual_precision", "召回不相关(疑似检索层问题)"),
    ]:
        val = dims.get(key)
        if isinstance(val, (int, float)) and val < DIM_FLAG:
            ev.append(f"{label}({key}={val})")
    return "；".join(ev) if ev else "框架维度分均正常（或部分指标跳过，见明细）"


# ═══════════════════════════════════════════════════════════════
# 四、主诊断流程
# ═══════════════════════════════════════════════════════════════

def run_diagnosis(failures: list[dict], mode: str, source_mode: str, limit: int | None) -> list[dict]:
    if not failures:
        print("[OK] 失败库为空，无需诊断。")
        return []

    print("=" * 64)
    print(f"  Day26 失败诊断 · 模式={mode} · 失败数={len(failures)}"
          + (f" · 本轮框架复核前 {limit} 条（--limit 控成本）" if limit else ""))
    print(f"  数据来源: failures.json 推断为 [{source_mode}]"
          + ("（含真实 retrieval_context，维度分可信）" if source_mode == "live"
             else "（无 retrieval_context，只做一级分流；请先 run_eval_platform --mode live）"))
    print("=" * 64)
    print()

    results = []
    measured = 0
    for f in failures:
        layer, reason = classify_by_hard_metrics(f)

        ctx = (f.get("retrieval_context") or "").strip()
        if mode == "live" and ctx and (limit is None or measured < limit):
            dims = measure_with_deepeval(f)
            measured += 1
            evidence = dims_to_evidence(dims)
        elif mode == "live" and not ctx:
            dims = {}
            evidence = "⚠ 无 retrieval_context：请先 run_eval_platform --mode live 回填"
        elif mode == "live":
            dims = {}
            evidence = f"超出 --limit={limit}，本轮未做框架复核（一级分流仍有效）"
        else:
            dims = {}
            evidence = "offline：仅一级分流，未调框架（--mode live 复核）"

        print(f"  [{layer}] {f['case_id']} ({f['type']})")
        print(f"      keyword={f.get('keyword_score')}  citation={f.get('citation_score')}  refusal_ok={f.get('refusal_ok')}")
        print(f"      -> {reason}")
        print(f"      问题    : {f.get('question', '')}")
        print(f"      真实回答: {f.get('answer', '')}")
        print(f"      参考答案: {f.get('reference', '')}")
        if ctx:
            shown = ctx[:400] + (" …(已截断)" if len(ctx) > 400 else "")
            print(f"      召回上下文({len(ctx)}字): {shown}")
        else:
            print(f"      召回上下文: (空)")
        if dims:
            print(f"      DeepEval维度分: {dims}")
        print(f"      证据: {evidence}")
        print()

        results.append({
            "case_id": f["case_id"],
            "type": f["type"],
            "layer_suspected": layer,
            "reason": reason,
            "keyword_score": f.get("keyword_score"),
            "citation_score": f.get("citation_score"),
            "refusal_ok": f.get("refusal_ok"),
            "deepeval": dims,
            "evidence": evidence,
        })

    summary = {}
    for r in results:
        summary[r["layer_suspected"]] = summary.get(r["layer_suspected"], 0) + 1

    print("=" * 64)
    print("  失败根因分布（一级弱信号分流 + 二级框架证据）")
    print("=" * 64)
    for layer, cnt in summary.items():
        print(f"  {layer}: {cnt} 条")

    REPORTS.mkdir(exist_ok=True)
    DIAGNOSIS.write_text(
        json.dumps({"mode": mode, "summary": summary, "results": results},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n  诊断结果已写入 {DIAGNOSIS}")
    print("  发布判决（门禁）请走 Day58：python capstone/ci_gate.py")
    return results


# ═══════════════════════════════════════════════════════════════
# 五、入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Day26 生产级失败诊断（纯诊断，门禁在 Day58）")
    parser.add_argument("--mode", choices=["offline", "live"], default=None,
                        help="offline=仅一级分流（无 key）；live=DeepEval 维度分复核。"
                             "默认由 failures.json 是否含真实 retrieval_context 自动推断。")
    parser.add_argument("--limit", type=int, default=None,
                        help="live 模式下最多对前 N 条做框架复核（控制 token 成本）")
    args = parser.parse_args()

    failures, source_mode = load_failures()
    mode = args.mode or source_mode
    if args.mode and args.mode != source_mode:
        print(f"[WARN] 显式 --mode={args.mode}，但 failures.json 推断为 {source_mode} 产物。"
              f"将以 {mode} 逻辑执行（维度分可信度以数据为准）。")

    run_diagnosis(failures, mode, source_mode, args.limit)


if __name__ == "__main__":
    main()
