"""L5.5 容器与配置 · 离线 gate 验收。"""

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
    spec = importlib.util.spec_from_file_location("candidate_l55", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l55"] = module
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
            "gate": "L5.5-docker",
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

    def dockerfile() -> str:
        return core.render_dockerfile()

    def test_structure():
        text = dockerfile()
        for token in ("FROM python", "WORKDIR /app", "EXPOSE 8000", "CMD"):
            expect(token in text, f"Dockerfile 缺 {token}")
        expect("0.0.0.0" in text, "CMD 必须监听 0.0.0.0")
        req = text.find("COPY requirements")
        code = text.find("COPY . .")
        expect(0 <= req < code, "应先 COPY requirements 再 COPY 代码（分层缓存）")
        expect("--no-cache-dir" in text, "pip install 应加 --no-cache-dir")

    def test_no_secrets():
        text = dockerfile().lower()
        for bad in ("sk-", "api_key=", "password=", "add http"):
            expect(bad not in text, f"Dockerfile 不应含 {bad}")

    def test_dockerignore():
        text = core.render_dockerignore()
        for token in (".env", ".git", ".venv", "__pycache__"):
            expect(token in text, f".dockerignore 缺 {token}")

    def test_audit_clean():
        expect(core.audit(dockerfile()) == [], f"生成的 Dockerfile 不应有问题：{core.audit(dockerfile())}")

    def test_audit_bad():
        bad = "FROM python:3.11\nCOPY . .\nADD https://evil/x .\nENV API_KEY=abc\nCMD ['python','x']\n"
        issues = core.audit(bad)
        expect(any("EXPOSE" in i for i in issues), f"应报缺 EXPOSE：{issues}")
        expect(any(".env" in i.lower() or "key" in i.lower() or "secret" in i.lower() for i in issues), f"应报密钥：{issues}")
        expect(any("ADD" in i for i in issues), f"应报 ADD 远端：{issues}")
        expect(any("USER" in i or "root" in i.lower() for i in issues), f"应报 root 运行：{issues}")

    gate.check("01 Dockerfile 结构", test_structure)
    gate.check("02 无明文密钥", test_no_secrets)
    gate.check("03 .dockerignore", test_dockerignore)
    gate.check("04 审计生成文件", test_audit_clean)
    gate.check("05 审计坏文件", test_audit_bad)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
