"""L5.8 扩展 · vLLM 启动配置 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l911", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l911"] = module
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
            "gate": "L5.8-vllm",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def spec(**overrides) -> dict:
    base = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "host": "0.0.0.0",
        "port": 8000,
        "tensor_parallel_size": 1,
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.9,
        "api_key_env": "VLLM_API_KEY",
    }
    base.update(overrides)
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=str(HERE / "starter.py"))
    args = parser.parse_args()
    module_path = Path(args.module).resolve()
    core = load_module(module_path)
    gate = Gate()

    def test_valid():
        expect(core.validate_vllm_spec(spec()) == (), f"合法配置不应报错：{core.validate_vllm_spec(spec())}")

    def test_model():
        expect(core.validate_vllm_spec(spec(model="  ")), "空 model 应报错")
        expect(core.validate_vllm_spec(spec(model="bad model")), "含空白 model 应报错")

    def test_ranges():
        for key, value in (("port", 0), ("port", 70000), ("tensor_parallel_size", 0), ("tensor_parallel_size", 17), ("max_model_len", 100), ("gpu_memory_utilization", 0.1)):
            expect(core.validate_vllm_spec(spec(**{key: value})), f"{key}={value} 应报错")

    def test_env():
        expect(core.validate_vllm_spec(spec(api_key_env="")), "空 env 应报错")
        expect(core.validate_vllm_spec(spec(api_key_env="KEY=abc")), "env 含等号应报错")

    def test_command():
        command = core.vllm_command(spec())
        expect(command[:3] == ("vllm", "serve", "Qwen/Qwen2.5-7B-Instruct"), f"命令开头不对：{command}")
        expect("--tensor-parallel-size" in command, "缺 tensor-parallel-size")
        expect(command[-1] == "${VLLM_API_KEY}", f"密钥应占位：{command}")
        try:
            core.vllm_command(spec(port=0))
        except ValueError:
            return
        raise AssertionError("非法配置应抛 ValueError")

    gate.check("01 合法配置", test_valid)
    gate.check("02 model 校验", test_model)
    gate.check("03 数值范围", test_ranges)
    gate.check("04 env 校验", test_env)
    gate.check("05 命令生成", test_command)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
