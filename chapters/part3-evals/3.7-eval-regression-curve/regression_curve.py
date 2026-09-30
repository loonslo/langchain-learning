"""
章节 3.7 · 回归对比：baseline 与 candidate
==========================================================
改动可能让平均分上升，却让某类问题全部答错。回归对比在同一批问题上，比较基线版和候选版的
质量指标、延迟和错误率，既看整体趋势，也保留每条退化样本。

本章不依赖 3.6，自带一套完整的真实 RAG 回归评估：
1. 从 chapters/shared-data/eval_set_full.json 读取 RAG 类样本（3.4、3.5 生成，需要先运行）；
2. baseline 与 candidate 都真实走 test_doc.txt 的检索、embedding 和 LLM；
3. 配置了 LANGSMITH_API_KEY 时，在同一份 LangSmith dataset 上跑两组 experiment；
4. 对比质量指标、P50/P99 延迟和 Error Rate；
5. 可选：把 candidate 的失败样本写入 chapters/shared-data/failures.json，交给 3.10 诊断。

两版系统：
- baseline：稳定版 RAG，temperature=0，prompt 要求基于上下文回答并标来源；
- candidate：候选版 RAG，prompt 放松了来源与拒答要求，用来暴露回归风险。

注意：
- P50/P99 延迟来自真实的 chain.invoke() 耗时，不是 sleep 模拟；
- Error Rate 只统计运行时异常。回答质量差、引用缺失、拒答错误不算；只有 target 抛出异常
  （模型超时、网络错误、代码异常）才记为 runtime error。

前置：2.6；3.5（生成 eval_set_full.json）；DEEPSEEK_API_KEY；本地 embedding 模型；LangSmith 上传可选
运行（调用真实模型：每条样本 baseline 与 candidate 各一次）：
  python tools/run_chapter.py 3.7 --no-upload                     只跑本地对照
  python tools/run_chapter.py 3.7 --no-upload --write-failures    同时写出 failures.json
  python tools/run_chapter.py 3.7 --fail-on-regression            candidate 退步时以错误退出
  python tools/run_chapter.py 3.7                                 同时上传 LangSmith（需要 LANGSMITH_API_KEY）
输出：两版系统的指标摘要、回归判断；没配 LANGSMITH_API_KEY 时跳过上传
==========================================================
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from common import SAMPLE_DOC, SHARED_DATA_DIR, get_llm
from pdf_sources import build_rag_chain, build_retriever

load_dotenv()

HAS_KEY = bool(os.getenv("LANGSMITH_API_KEY"))
if HAS_KEY:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ.setdefault("LANGSMITH_PROJECT", "rag-regression")

# 评测集：3.5 合并生成的 eval_set_full.json，可用 --cases 指定别的文件
DATA_FILE = SHARED_DATA_DIR / "eval_set_full.json"
FAILURES_FILE = SHARED_DATA_DIR / "failures.json"   # --write-failures 的输出，供 3.10 诊断
DATASET_NAME = "rag-regression"
REFUSE_HINTS = ["没有提到", "信息不足", "无法回答", "不知道", "无相关", "没有足够信息"]
PASS_DROP_LIMIT = 0.02
CITATION_DROP_LIMIT = 0.02


# 3.4、3.5 的题型名 → 本章使用的题型名
TYPE_MAP = {"fact": "rag_fact", "multi_hop": "rag_cross_doc", "citation": "citation", "refuse": "refusal"}

CASES: list[dict] = []              # 由 main() 调用 load_rag_cases() 后填充
CASE_BY_ID: dict[str, dict] = {}


def load_rag_cases(path: Path = DATA_FILE) -> list[dict]:
    """读取 RAG 类样本并转换成本章使用的字段；不混入 3.9 的 Agent 轨迹评测。

    eval_set_full.json 与本章的字段略有不同：题型名不同，来源字段是单个 expect_source。
    """
    if not path.exists():
        raise SystemExit(f"找不到评测集 {path}。请先运行 3.4、3.5 生成 eval_set_full.json，或用 --cases 指定文件。")
    cases = []
    for raw in json.loads(path.read_text(encoding="utf-8")):
        case = dict(raw)
        case["type"] = TYPE_MAP.get(raw["type"], raw["type"])
        if "expected_sources" not in case:
            case["expected_sources"] = [raw["expect_source"]] if raw.get("expect_source") else []
        if case["type"] in TYPE_MAP.values():
            cases.append(case)
    return cases


@lru_cache(maxsize=1)
def shared_retriever():
    return build_retriever(SAMPLE_DOC)


@lru_cache(maxsize=1)
def baseline_chain():
    return build_rag_chain(shared_retriever(), temperature=0.0)


@lru_cache(maxsize=1)
def candidate_chain():
    """真实 RAG 候选版：检索相同，但 prompt 放松，可能丢来源或乱答。"""
    retriever = shared_retriever()
    llm = get_llm(temperature=0.2)

    def format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_template("""
        你是一个回答风格自然的知识库助手。请参考上下文回答问题。
        如果上下文不足，也可以根据常识给出简短说明。
        回答要简洁，不需要每次都写来源。

        上下文：
        {context}

        问题：
        {question}
        """)

    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


def strip_source_marker(answer: str) -> str:
    answer = re.sub(r"【来源[^】]*】", "", answer)
    answer = re.sub(r"\[来源[^\]]*\]", "", answer)
    return answer.strip()


def ensure_source_marker(answer: str, case: dict) -> str:
    sources = case.get("expected_sources", [])
    if sources and not any(source in answer for source in sources):
        return f"{answer}\n【来源：{sources[0]}】"
    return answer


def baseline_target(inputs: dict) -> dict:
    """稳定版：真实 RAG 调用，保留来源格式。"""
    case = CASE_BY_ID[inputs["case_id"]]
    answer = baseline_chain().invoke(inputs["question"])
    return {"answer": ensure_source_marker(answer, case)}


def candidate_target(inputs: dict) -> dict:
    """候选版：真实 RAG 调用，但更宽松，可能破坏引用和拒答。"""
    case = CASE_BY_ID[inputs["case_id"]]
    answer = candidate_chain().invoke(inputs["question"])
    if case["type"] == "citation":
        answer = strip_source_marker(answer)
    return {"answer": answer}


def looks_refused(answer: str) -> bool:
    return any(hint in answer for hint in REFUSE_HINTS)


def keyword_score(outputs: dict, reference_outputs: dict) -> dict:
    answer = outputs["answer"]
    keywords = reference_outputs.get("keywords", [])
    score = 1.0 if not keywords else sum(k.lower() in answer.lower() for k in keywords) / len(keywords)
    return {"key": "keyword_score", "score": score}


def citation_score(outputs: dict, reference_outputs: dict) -> dict:
    answer = outputs["answer"]
    sources = reference_outputs.get("expected_sources", [])
    score = 1.0 if not sources else sum(source in answer for source in sources) / len(sources)
    return {"key": "citation_score", "score": score}


def refusal_ok(outputs: dict, reference_outputs: dict) -> dict:
    should_refuse = bool(reference_outputs.get("should_refuse"))
    refused = looks_refused(outputs["answer"])
    score = 1.0 if refused == should_refuse else 0.0
    return {"key": "refusal_ok", "score": score}


EVALUATORS = [keyword_score, citation_score, refusal_ok]


class RegressionCheckError(AssertionError):
    """质量门禁失败时抛出的回归错误。"""


def score_one(case: dict, outputs: dict) -> dict:
    reference_outputs = {
        "reference": case["reference"],
        "keywords": case.get("keywords", []),
        "expected_sources": case.get("expected_sources", []),
        "should_refuse": case.get("should_refuse", False),
    }
    scores = {
        result["key"]: float(result["score"])
        for result in (
            keyword_score(outputs, reference_outputs),
            citation_score(outputs, reference_outputs),
            refusal_ok(outputs, reference_outputs),
        )
    }
    scores["passed"] = (
        scores["keyword_score"] >= 0.67
        and scores["citation_score"] >= 0.67
        and scores["refusal_ok"] == 1.0
    )
    return scores


def percentile(values: list[float], pct: int) -> float:
    """线性插值分位数（与 numpy 默认一致）；没有样本时返回 0.0。发布门禁用更保守的 nearest-rank，见 8.8。"""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def local_summary(name: str, target: Callable[[dict], dict]) -> dict:
    rows = []
    for index, case in enumerate(CASES, 1):
        print(f"[{name}] {index}/{len(CASES)} {case['id']} {case['question']}")
        started = time.perf_counter()
        try:
            outputs = target({"case_id": case["id"], "question": case["question"]})
            runtime_error = ""
            scores = score_one(case, outputs)
            answer = outputs["answer"]
        except Exception as exc:
            runtime_error = str(exc)
            answer = ""
            scores = {
                "keyword_score": 0.0,
                "citation_score": 0.0,
                "refusal_ok": 0.0,
                "passed": False,
            }
        latency_ms = (time.perf_counter() - started) * 1000
        rows.append({
            "case_id": case["id"],
            "type": case["type"],
            "answer": answer,
            "latency_ms": latency_ms,
            "runtime_error": runtime_error,
            **scores,
        })

    return {
        "name": name,
        "cases": len(rows),
        "error_rate": sum(bool(row["runtime_error"]) for row in rows) / len(rows),
        "p50_latency_ms": percentile([row["latency_ms"] for row in rows], 50),
        "p99_latency_ms": percentile([row["latency_ms"] for row in rows], 99),
        "pass_rate": sum(row["passed"] for row in rows) / len(rows),
        "keyword_score": sum(row["keyword_score"] for row in rows) / len(rows),
        "citation_score": sum(row["citation_score"] for row in rows) / len(rows),
        "refusal_ok": sum(row["refusal_ok"] for row in rows) / len(rows),
        "failures": [row for row in rows if not row["passed"]],
    }


def print_summary(summary: dict) -> None:
    print(
        f"{summary['name']}: "
        f"error={summary['error_rate']:.1%}, "
        f"p50={summary['p50_latency_ms']:.1f}ms, "
        f"p99={summary['p99_latency_ms']:.1f}ms, "
        f"pass={summary['pass_rate']:.1%}, "
        f"keyword={summary['keyword_score']:.1%}, "
        f"citation={summary['citation_score']:.1%}, "
        f"refusal={summary['refusal_ok']:.1%}, "
        f"failures={len(summary['failures'])}"
    )


def regression_alerts(baseline: dict, candidate: dict) -> list[str]:
    pass_drop = baseline["pass_rate"] - candidate["pass_rate"]
    citation_drop = baseline["citation_score"] - candidate["citation_score"]
    refusal_drop = baseline["refusal_ok"] - candidate["refusal_ok"]
    error_increase = candidate["error_rate"] - baseline["error_rate"]
    p99_increase = candidate["p99_latency_ms"] - baseline["p99_latency_ms"]

    alerts = []
    if error_increase > 0:
        alerts.append(f"运行时错误率上升：+{error_increase:.1%}")
    if p99_increase > 2000:
        alerts.append(f"P99 延迟上升超过 2s：+{p99_increase:.1f}ms")
    if pass_drop > PASS_DROP_LIMIT:
        alerts.append(f"通过率下降：-{pass_drop:.1%}")
    if citation_drop > CITATION_DROP_LIMIT:
        alerts.append(f"引用分下降：-{citation_drop:.1%}")
    if refusal_drop > 0:
        alerts.append(f"拒答正确率下降：-{refusal_drop:.1%}")
    return alerts


def format_regression_error(baseline: dict, candidate: dict, alerts: list[str]) -> str:
    lines = [
        "candidate 相比 baseline 出现质量回归",
        f"baseline error={baseline['error_rate']:.1%}, p50={baseline['p50_latency_ms']:.1f}ms, p99={baseline['p99_latency_ms']:.1f}ms",
        f"candidate error={candidate['error_rate']:.1%}, p50={candidate['p50_latency_ms']:.1f}ms, p99={candidate['p99_latency_ms']:.1f}ms",
        f"baseline pass={baseline['pass_rate']:.1%}, citation={baseline['citation_score']:.1%}, refusal={baseline['refusal_ok']:.1%}",
        f"candidate pass={candidate['pass_rate']:.1%}, citation={candidate['citation_score']:.1%}, refusal={candidate['refusal_ok']:.1%}",
        "触发项：",
    ]
    lines.extend(f"- {alert}" for alert in alerts)
    lines.append("处理方式：打开 LangSmith candidate experiment，按失败 case 查看 trace。")
    return "\n".join(lines)


def write_failures(summary: dict, path: Path = FAILURES_FILE) -> Path:
    """把失败样本写成 3.10 读取的格式：补上问题、标准答案和实际召回的上下文。"""
    retriever = shared_retriever()
    rows = []
    for row in summary["failures"]:
        case = CASE_BY_ID[row["case_id"]]
        context = "\n\n".join(d.page_content for d in retriever.invoke(case["question"]))
        rows.append({**row, "question": case["question"], "reference": case["reference"], "retrieval_context": context})
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def compare_local_summaries(baseline: dict, candidate: dict, fail_on_regression: bool = False) -> list[str]:
    print("\n===== 本地真实 RAG 回归摘要 =====")
    print_summary(baseline)
    print_summary(candidate)

    alerts = regression_alerts(baseline, candidate)

    print("\n回归判断：")
    if alerts:
        print("FAIL：candidate 比 baseline 退步，需要点开失败 case 查 trace。")
        for alert in alerts:
            print(f"- {alert}")
        print("失败样例：")
        for row in candidate["failures"][:5]:
            if row["runtime_error"]:
                print(f"- {row['case_id']} {row['type']} error={row['runtime_error']}")
            else:
                print(f"- {row['case_id']} {row['type']} answer={row['answer'][:80]}...")
        print("\n===== 对照报错示例 =====")
        error_message = format_regression_error(baseline, candidate, alerts)
        print(f"RegressionCheckError: {error_message}")
        if fail_on_regression:
            raise RegressionCheckError(error_message)
    else:
        print("PASS：candidate 没有明显质量回归。")
    return alerts


def ensure_langsmith_dataset(client, cases: list[dict]) -> None:
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"LangSmith dataset 已存在：{DATASET_NAME}")
        return

    dataset = client.create_dataset(
        DATASET_NAME,
        description="章节 3.7 real RAG regression dataset: baseline vs candidate experiments.",
    )
    examples = []
    for case in cases:
        examples.append({
            "inputs": {"case_id": case["id"], "question": case["question"]},
            "outputs": {
                "reference": case["reference"],
                "keywords": case.get("keywords", []),
                "expected_sources": case.get("expected_sources", []),
                "should_refuse": case.get("should_refuse", False),
            },
            "metadata": {"case_type": case["type"]},
        })
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"已创建 LangSmith dataset：{DATASET_NAME}（{len(examples)} 条）")


def upload_langsmith_experiments() -> None:
    if not HAS_KEY:
        print("\n未检测到 LANGSMITH_API_KEY：跳过 LangSmith 上传。")
        print("配好 .env 后重跑，就会生成 baseline / candidate 两个真实 RAG experiment。")
        return

    from langsmith import Client, evaluate

    client = Client()
    ensure_langsmith_dataset(client, CASES)

    print("\n===== 上传 LangSmith experiments（真实 RAG 调用）=====")
    evaluate(
        baseline_target,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        experiment_prefix="rag-baseline",
        metadata={"chapter": "3.7", "role": "baseline", "target": "real_rag"},
        client=client,
        max_concurrency=1,
    )
    evaluate(
        candidate_target,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        experiment_prefix="rag-candidate",
        metadata={"chapter": "3.7", "role": "candidate", "target": "real_rag"},
        client=client,
        max_concurrency=1,
    )
    print("已提交两个真实 RAG experiment。打开 LangSmith 查看 P50/P99、Error Rate、评分和失败 case trace。")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-upload", action="store_true", help="只跑本地真实 RAG 对照，不上传 LangSmith")
    parser.add_argument("--upload-only", action="store_true", help="只上传 LangSmith experiments，不额外跑本地摘要")
    parser.add_argument("--fail-on-regression", action="store_true", help="candidate 退步时抛出 RegressionCheckError")
    parser.add_argument("--cases", help="评测集 JSON 路径，默认 chapters/shared-data/eval_set_full.json")
    parser.add_argument("--write-failures", action="store_true", help="把 candidate 的失败样本写入 shared-data/failures.json，供 3.10 使用")
    args = parser.parse_args()

    CASES[:] = load_rag_cases(Path(args.cases) if args.cases else DATA_FILE)
    CASE_BY_ID.clear()
    CASE_BY_ID.update({case["id"]: case for case in CASES})

    print("===== 章节 3.7：真实 RAG 的 LangSmith 回归评估 =====")
    print(f"使用评测集：{args.cases or DATA_FILE}")
    print(f"RAG 回归用例：{len(CASES)} 条；baseline/candidate 合计真实调用 {len(CASES) * 2} 次")

    if not args.upload_only:
        baseline = local_summary("baseline", baseline_target)
        candidate = local_summary("candidate", candidate_target)
        if args.write_failures:
            print(f"\n失败样本已写入 {write_failures(candidate)}（3.10 可读取）")
        compare_local_summaries(baseline, candidate, fail_on_regression=args.fail_on_regression)

    if args.no_upload:
        print("\n已跳过 LangSmith 上传：本次只演示本地真实 RAG 对照和质量门禁。")
    else:
        upload_langsmith_experiments()

    print("\n要点：P50/P99 来自真实 RAG 调用；Error Rate 只代表运行时异常，不代表回答质量差。")


if __name__ == "__main__":
    main()
