"""L1.2 输出控制 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l12", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l12"] = module
    spec.loader.exec_module(module)
    return module


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class Gate:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def check(self, name: str, fn) -> None:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            self.rows.append({"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
        else:
            self.rows.append({"name": name, "ok": True, "error": ""})

    def report(self, module_path: Path) -> int:
        passed = sum(row["ok"] for row in self.rows)
        total = len(self.rows)
        for row in self.rows:
            mark = "PASS" if row["ok"] else "FAIL"
            print(f"[{mark}] {row['name']}" + ("" if row["ok"] else f"  <- {row['error']}"))
        print(f"\n{passed}/{total} passed")
        if passed != total:
            print("gate 未通过：先修 FAIL 项，不要打开参考实现。")
        out = {
            "gate": "L1.2-output-control",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def make_clock(values: list[float]):
    state = {"i": 0}

    def clock() -> float:
        index = min(state["i"], len(values) - 1)
        state["i"] += 1
        return values[index]

    return clock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_defaults():
        req = core.build_request()
        expect(req == {"temperature": 0.0, "max_tokens": 512, "stop": []}, f"默认参数不对：{req}")

    def test_custom():
        req = core.build_request(1.2, 100, ["\n\n"])
        expect(req["temperature"] == 1.2 and req["max_tokens"] == 100 and req["stop"] == ["\n\n"], f"参数不对：{req}")

    def test_rejects_bad_request():
        bad = [
            {"temperature": -0.1},
            {"temperature": 2.1},
            {"max_tokens": 0},
            {"max_tokens": 9000},
            {"max_tokens": True},
            {"stop": "not-a-list"},
            {"stop": [""]},
            {"stop": ["a", "b", "c", "d", "e"]},
        ]
        for kwargs in bad:
            try:
                core.build_request(**kwargs)
            except core.RequestError:
                continue
            raise AssertionError(f"应拒绝非法参数：{kwargs}")

    def test_collect_normal():
        result = core.collect_stream(["a", "b", "c"], clock=make_clock([10.0, 10.05]))
        expect(result["text"] == "abc", f"text 不对：{result['text']}")
        expect(result["chunks"] == 3, f"chunks 不对：{result['chunks']}")
        expect(result["first_chunk_ms"] == 50, f"first_chunk_ms 不对：{result['first_chunk_ms']}")
        expect(result["error"] is None, f"error 应为 None：{result['error']}")

    def test_collect_empty():
        result = core.collect_stream([], clock=make_clock([1.0]))
        expect(result["error"] == "empty_stream", f"空流应报 empty_stream：{result}")
        expect(result["text"] == "" and result["chunks"] == 0, "空流 text/chunks 不对")
        expect(result["first_chunk_ms"] == -1, "空流 first_chunk_ms 应为 -1")

    def test_collect_bad_chunk():
        result = core.collect_stream(["a", 123, "c"], clock=make_clock([1.0, 1.1]))
        expect(result["error"] == "bad_chunk", f"非字符串片段应报 bad_chunk：{result}")
        expect(result["text"] == "a", "应保留此前已拼接内容")

    def test_collect_model_error():
        def broken():
            yield "a"
            raise RuntimeError("stream down")

        result = core.collect_stream(broken(), clock=make_clock([1.0, 1.1]))
        expect(result["error"] == "model_error", f"迭代异常应报 model_error：{result}")
        expect(result["text"] == "a", "应保留已收到内容")

    def test_stream_passes_request():
        seen = {}

        def chat(request):
            seen.update(request)
            return iter(["你", "好"])

        request = {"temperature": 0.0, "max_tokens": 10, "stop": []}
        result = core.stream_text(chat, request)
        expect(seen == request, f"request 没有原样传入：{seen}")
        expect(result["text"] == "你好" and result["error"] is None, f"结果不对：{result}")

    def test_stream_timeout():
        def chat(_request):
            raise TimeoutError("timeout")

        result = core.stream_text(chat, {})
        expect(result["error"] == "timeout", f"超时应报 timeout：{result}")

    def test_stream_model_error():
        def chat(_request):
            raise RuntimeError("boom")

        result = core.stream_text(chat, {})
        expect(result["error"] == "model_error", f"异常应报 model_error：{result}")

    gate.check("01 默认请求参数", test_defaults)
    gate.check("02 自定义请求参数", test_custom)
    gate.check("03 拒绝非法请求参数", test_rejects_bad_request)
    gate.check("04 正常流式收集", test_collect_normal)
    gate.check("05 空流边界", test_collect_empty)
    gate.check("06 非字符串片段", test_collect_bad_chunk)
    gate.check("07 迭代异常保留已收内容", test_collect_model_error)
    gate.check("08 请求原样传入", test_stream_passes_request)
    gate.check("09 流式调用超时", test_stream_timeout)
    gate.check("10 流式调用异常", test_stream_model_error)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
