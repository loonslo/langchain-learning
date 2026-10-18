"""L3.4 LLM Judge 与校准 · 离线 gate 验收。

用法（仓库根目录）：
    python chapters/part3-evals/3.3-llm-judge/gate/gate_check.py
    python chapters/part3-evals/3.3-llm-judge/gate/gate_check.py --module 你的实现.py

默认检查同目录 starter.py。全部 PASS 时退出码为 0，并写出 gate_report.json。
不调用真实模型；裁判输出由脚本注入。
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    sys.path.insert(0, str(CHAPTER))
    spec = importlib.util.spec_from_file_location("candidate_l34", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l34"] = module
    spec.loader.exec_module(module)
    return module


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float) -> bool:
    return abs(float(actual) - expected) < 1e-9


class Gate:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def check(self, name: str, fn) -> None:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - gate 要报告所有失败
            self.rows.append(
                {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
            )
        else:
            self.rows.append({"name": name, "ok": True, "error": ""})

    def report(self, module_path: Path) -> int:
        passed = sum(row["ok"] for row in self.rows)
        total = len(self.rows)
        for row in self.rows:
            mark = "PASS" if row["ok"] else "FAIL"
            suffix = "" if row["ok"] else f"  <- {row['error']}"
            print(f"[{mark}] {row['name']}{suffix}")
        print(f"\n{passed}/{total} passed")
        if passed != total:
            print("gate 未通过：先修 FAIL 项，不要打开参考实现。")
        out = {
            "gate": "L3.4-judge-calibration",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return 0 if passed == total else 1


SAMPLES = [
    {"id": "s01", "human_pass": True, "judge_score": 5},
    {"id": "s02", "human_pass": True, "judge_score": 4},
    {"id": "s03", "human_pass": True, "judge_score": 3},
    {"id": "s04", "human_pass": True, "judge_score": 2},
    {"id": "s05", "human_pass": False, "judge_score": 1},
    {"id": "s06", "human_pass": False, "judge_score": 2},
    {"id": "s07", "human_pass": False, "judge_score": 5},
    {"id": "s08", "human_pass": False, "judge_score": 4},
    {"id": "s09", "human_pass": True, "judge_score": 5},
    {"id": "s10", "human_pass": False, "judge_score": 1},
    {"id": "s11", "human_pass": True, "judge_score": 4},
    {"id": "s12", "human_pass": False, "judge_score": 3},
]


class ScriptedLLM:
    def __init__(self, replies: list[str | Exception]) -> None:
        self.replies = list(replies)
        self.calls: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.calls.append(prompt)
        if not self.replies:
            raise AssertionError("llm_fn 调用次数超过脚本预设")
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_prompt_contains_fields_and_rubric():
        prompt = core.build_prompt("退款多久", "3个工作日", "3个工作日到账", "退款审核通过后3个工作日到账。")
        for part in ("退款多久", "3个工作日", "3个工作日到账", "退款审核通过后3个工作日到账。"):
            expect(part in prompt, f"prompt 缺少字段：{part}")
        expect("1" in prompt and "5" in prompt, "prompt 应说明 1–5 分")
        expect("只看意思" in prompt or "不纠结" in prompt, "prompt 应说明只看意思")
        expect("上下文" in prompt and ("编造" in prompt or "依据" in prompt), "prompt 应约束依据上下文")

    def test_parse_plain_json():
        verdict = core.parse_verdict('{"score": 4, "reason": "基本正确"}')
        expect(verdict == {"score": 4, "reason": "基本正确"}, f"解析结果不对：{verdict}")

    def test_parse_fenced_json():
        text = '```json\n{"score": 5, "reason": "完全正确"}\n```'
        verdict = core.parse_verdict(text)
        expect(verdict["score"] == 5, f"围栏 JSON 解析失败：{verdict}")

    def test_parse_json_with_prose():
        text = '判断如下：{"score": 3, "reason": "部分正确"}。以上。'
        verdict = core.parse_verdict(text)
        expect(verdict["score"] == 3, f"带说明文字的 JSON 解析失败：{verdict}")

    def test_parse_rejects_bad_payloads():
        bad = [
            "not json",
            '{"score": 0, "reason": "x"}',
            '{"score": 6, "reason": "x"}',
            '{"score": true, "reason": "x"}',
            '{"score": 4, "reason": "   "}',
            '{"score": 4}',
        ]
        for text in bad:
            try:
                core.parse_verdict(text)
            except core.JudgeFormatError:
                continue
            raise AssertionError(f"应拒绝非法输出：{text}")

    def test_judge_returns_attempts():
        llm = ScriptedLLM(['{"score": 4, "reason": "ok"}'])
        verdict = core.judge("q", "a", "ref", "ctx", llm)
        expect(verdict["score"] == 4 and verdict["attempts"] == 1, f"结果不对：{verdict}")
        expect(len(llm.calls) == 1, "合法输出不应重试")

    def test_judge_retries_invalid_then_valid():
        llm = ScriptedLLM(["not json", '{"score": 5, "reason": "ok"}'])
        verdict = core.judge("q", "a", "ref", "ctx", llm)
        expect(verdict["score"] == 5 and verdict["attempts"] == 2, f"结果不对：{verdict}")

    def test_judge_retries_llm_exception_then_valid():
        llm = ScriptedLLM([TimeoutError("upstream timeout"), '{"score": 4, "reason": "ok"}'])
        verdict = core.judge("q", "a", "ref", "ctx", llm)
        expect(verdict["score"] == 4 and verdict["attempts"] == 2, f"结果不对：{verdict}")

    def test_judge_raises_after_attempts():
        llm = ScriptedLLM(["bad", "still bad"])
        try:
            core.judge("q", "a", "ref", "ctx", llm)
        except core.JudgeFormatError:
            return
        raise AssertionError("两次非法输出后应抛 JudgeFormatError")

    def test_judge_rejects_zero_attempts():
        try:
            core.judge("q", "a", "ref", "ctx", ScriptedLLM([]), attempts=0)
        except ValueError:
            return
        raise AssertionError("attempts=0 应抛 ValueError")

    def test_calibrate_metrics():
        rows = copy.deepcopy(SAMPLES)
        report = core.calibrate(rows, lambda sample: sample["judge_score"])
        expect(report["total"] == 12, f"total 不对：{report['total']}")
        expect(close(report["agreement"], 8 / 12), f"agreement 不对：{report['agreement']}")
        expect(report["confusion"] == {"tp": 4, "tn": 4, "fp": 2, "fn": 2}, f"混淆矩阵不对：{report['confusion']}")
        expect(report["disagreements"] == ["s03", "s04", "s07", "s08"], f"不一致列表不对：{report['disagreements']}")
        expect(close(report["mean_score"], 39 / 12), f"mean_score 不对：{report['mean_score']}")
        expect(rows == SAMPLES, "calibrate 不应修改输入")

    def test_calibrate_catches_always_pass_judge():
        report = core.calibrate(copy.deepcopy(SAMPLES), lambda sample: 5)
        expect(close(report["agreement"], 0.5), f"全判通过时 agreement 应为 0.5：{report['agreement']}")
        expect(len(report["disagreements"]) == 6, "应列出 6 条不一致")
        expect(report["confusion"] == {"tp": 6, "tn": 0, "fp": 6, "fn": 0}, f"混淆矩阵不对：{report['confusion']}")

    def test_calibrate_rejects_bad_samples():
        bad_cases = [
            [{"id": "x", "human_pass": True}],
            [
                {"id": "x", "human_pass": True, "judge_score": 4},
                {"id": "x", "human_pass": False, "judge_score": 2},
            ],
            [{"id": "x", "human_pass": "yes", "judge_score": 4}],
            [{"id": "x", "human_pass": True, "judge_score": 6}],
        ]
        for samples in bad_cases:
            try:
                core.calibrate(samples, lambda sample: sample["judge_score"])
            except ValueError:
                continue
            raise AssertionError(f"应拒绝非法样本：{samples}")

    def test_calibrate_empty():
        report = core.calibrate([], lambda sample: 4)
        expect(report["total"] == 0, "空样本 total 应为 0")
        expect(close(report["agreement"], 0.0), "空样本 agreement 应为 0.0")
        expect(close(report["mean_score"], 0.0), "空样本 mean_score 应为 0.0")

    gate.check("01 prompt 包含四项与评分规则", test_prompt_contains_fields_and_rubric)
    gate.check("02 解析纯 JSON", test_parse_plain_json)
    gate.check("03 解析围栏 JSON", test_parse_fenced_json)
    gate.check("04 解析带说明文字的 JSON", test_parse_json_with_prose)
    gate.check("05 拒绝非法裁判输出", test_parse_rejects_bad_payloads)
    gate.check("06 合法输出不重试", test_judge_returns_attempts)
    gate.check("07 非法输出后重试成功", test_judge_retries_invalid_then_valid)
    gate.check("08 模型异常后重试成功", test_judge_retries_llm_exception_then_valid)
    gate.check("09 重试耗尽后抛错", test_judge_raises_after_attempts)
    gate.check("10 拒绝 attempts=0", test_judge_rejects_zero_attempts)
    gate.check("11 校准指标与混淆矩阵", test_calibrate_metrics)
    gate.check("12 抓住全判通过的裁判", test_calibrate_catches_always_pass_judge)
    gate.check("13 拒绝非法样本", test_calibrate_rejects_bad_samples)
    gate.check("14 空样本边界", test_calibrate_empty)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
