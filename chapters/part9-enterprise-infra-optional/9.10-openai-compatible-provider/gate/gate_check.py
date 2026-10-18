"""L5.8 扩展 · OpenAI 兼容配置 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l910", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l910"] = module
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
            "gate": "L5.8-provider",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def provider(**overrides) -> dict:
    base = {
        "name": "deepseek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
        "app_env": "development",
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

    def test_url():
        expect(core.chat_completions_url("https://x/v1/") == "https://x/v1/chat/completions", "URL 拼接不对")
        for bad in ("", None):
            try:
                core.chat_completions_url(bad)
            except ValueError:
                continue
            raise AssertionError("空/非字符串应报错")

    def test_valid():
        expect(core.validate_provider(provider()) == (), f"合法配置不应报错：{core.validate_provider(provider())}")

    def test_base_url():
        for url in ("api.deepseek.com/v1", "ftp://x/v1", "https://x/v2"):
            errors = core.validate_provider(provider(base_url=url))
            expect(errors, f"非法 base_url 应报错：{url}")

    def test_model_key():
        expect(core.validate_provider(provider(model="  ")), "空 model 应报错")
        expect(core.validate_provider(provider(api_key_env="")), "空 env 应报错")
        expect(core.validate_provider(provider(api_key_env="KEY=abc")), "env 含等号应报错")

    def test_production_https():
        errors = core.validate_provider(provider(base_url="http://x/v1", app_env="production"))
        expect(any("HTTPS" in e for e in errors), f"生产 http 应报错：{errors}")

    gate.check("01 URL 拼接", test_url)
    gate.check("02 合法配置", test_valid)
    gate.check("03 base_url 校验", test_base_url)
    gate.check("04 model/api_key_env", test_model_key)
    gate.check("05 生产 HTTPS", test_production_https)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
