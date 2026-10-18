"""L2.6 查询改写 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l29b", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l29b"] = module
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
            "gate": "L2.6-query-rewrite",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_prompt():
        prompt = core.build_rewrite_prompt("向量怎么存", [{"role": "user", "content": "你好"}])
        expect("向量怎么存" in prompt, "prompt 缺原问题")
        expect("你好" in prompt, "prompt 缺历史")
        expect("一行一条" in prompt or "每行一条" in prompt, "prompt 应要求一行一条")

    def test_parse():
        text = "1. 如何存储向量\n2) 向量持久化\n- 向量库落盘\n2) 向量持久化\n\n"
        rows = core.parse_rewrites(text, max_queries=5)
        expect(rows == ["如何存储向量", "向量持久化", "向量库落盘"], f"解析不对：{rows}")

    def test_parse_limit():
        rows = core.parse_rewrites("1. a\n2. b\n3. c", max_queries=2)
        expect(rows == ["a", "b"], f"max_queries 未生效：{rows}")
        for max_queries in (0, -1):
            try:
                core.parse_rewrites("a", max_queries=max_queries)
            except ValueError:
                continue
            raise AssertionError("max_queries<1 应抛 ValueError")

    def test_rewrite_ok():
        result = core.rewrite_query("向量怎么存", lambda prompt: "1. 如何存储向量\n2. 向量持久化")
        expect(result["queries"] == ["向量怎么存", "如何存储向量", "向量持久化"], f"改写结果不对：{result}")
        expect(result["error"] is None, f"error 应为 None：{result}")

    def test_rewrite_max_queries():
        result = core.rewrite_query("向量怎么存", lambda prompt: "1. a\n2. b", max_queries=2)
        expect(result["queries"] == ["向量怎么存", "a"], f"应截断到 2 条：{result}")

    def test_rewrite_empty():
        result = core.rewrite_query("向量怎么存", lambda prompt: "   ")
        expect(result["queries"] == ["向量怎么存"], f"空输出应回退原问题：{result}")
        expect(result["error"] == "empty_rewrite", f"error 不对：{result}")

    def test_rewrite_no_new_query():
        result = core.rewrite_query("向量怎么存", lambda prompt: "1. 向量怎么存")
        expect(result["queries"] == ["向量怎么存"], f"重复原问题应回退：{result}")
        expect(result["error"] == "empty_rewrite", f"error 不对：{result}")

    def test_rewrite_model_error():
        def boom(prompt):
            raise TimeoutError("timeout")

        result = core.rewrite_query("向量怎么存", boom)
        expect(result["queries"] == ["向量怎么存"], f"异常应回退原问题：{result}")
        expect(result["error"] == "model_error", f"error 不对：{result}")

    def test_rewrite_validation():
        for args, kwargs in ((("  ", lambda p: "x"), {}), (("q", lambda p: "x"), {"max_queries": 0})):
            try:
                core.rewrite_query(*args, **kwargs)
            except ValueError:
                continue
            raise AssertionError("非法参数应抛 ValueError")

    gate.check("01 改写 prompt", test_prompt)
    gate.check("02 解析编号/去重", test_parse)
    gate.check("03 max_queries 解析限制", test_parse_limit)
    gate.check("04 正常改写", test_rewrite_ok)
    gate.check("05 改写条数限制", test_rewrite_max_queries)
    gate.check("06 空输出回退", test_rewrite_empty)
    gate.check("07 无新查询回退", test_rewrite_no_new_query)
    gate.check("08 模型异常回退", test_rewrite_model_error)
    gate.check("09 参数校验", test_rewrite_validation)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
