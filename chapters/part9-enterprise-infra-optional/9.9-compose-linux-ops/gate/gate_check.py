"""L5.7 扩展 · 部署前配置检查 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l99", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l99"] = module
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
            "gate": "L5.7-runtime-config",
            "module": str(module_path),
            "passed": passed,
            "total": total,
            "ok": passed == total,
            "checks": self.rows,
        }
        (HERE / "gate_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if passed == total else 1


def settings(**overrides) -> dict:
    base = {
        "database_url": "postgresql://app:secret@db:5432/app",
        "redis_url": "redis://cache:6379/0",
        "qdrant_url": "http://qdrant:6333",
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

    def test_valid():
        expect(core.configuration_errors(settings()) == (), f"合法配置不应报错：{core.configuration_errors(settings())}")

    def test_database():
        expect(core.configuration_errors(settings(database_url="sqlite:///app.db")), "非 postgresql 应报错")

    def test_redis_qdrant():
        expect(core.configuration_errors(settings(redis_url="http://cache")), "非 redis 应报错")
        expect(core.configuration_errors(settings(qdrant_url="grpc://qdrant")), "非 http 应报错")

    def test_production_password():
        errors = core.configuration_errors(settings(database_url="postgresql://app:change-me@db/app", app_env="production"))
        expect(any("change-me" in e or "示例" in e for e in errors), f"生产示例密码应报错：{errors}")
        expect(core.configuration_errors(settings(database_url="postgresql://app:change-me@db/app")) == (), "开发环境不应报错")

    def test_multiple():
        errors = core.configuration_errors(settings(database_url="sqlite://x", redis_url="http://x", qdrant_url="grpc://x"))
        expect(len(errors) == 3, f"应一次报 3 项：{errors}")

    gate.check("01 合法配置", test_valid)
    gate.check("02 数据库协议", test_database)
    gate.check("03 Redis/Qdrant 协议", test_redis_qdrant)
    gate.check("04 生产示例密码", test_production_password)
    gate.check("05 多错误收集", test_multiple)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
