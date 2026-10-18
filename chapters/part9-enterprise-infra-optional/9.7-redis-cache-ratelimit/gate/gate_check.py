"""L5.8 Redis 缓存/限流 · 离线 gate 验收。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCOPE = {"tenant_id": "t1", "knowledge_version": "k1", "acl_version": "a1", "model": "m1"}


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.ttl: dict[str, int] = {}
        self.fail = False

    def get(self, key):
        if self.fail:
            raise ConnectionError("down")
        return self.data.get(key)

    def set(self, key, value, *, ex):
        if self.fail:
            raise ConnectionError("down")
        self.data[key] = value
        self.ttl[key] = ex

    def incr(self, key):
        if self.fail:
            raise ConnectionError("down")
        value = int(self.data.get(key, "0")) + 1
        self.data[key] = str(value)
        return value

    def expire(self, key, seconds):
        if self.fail:
            raise ConnectionError("down")
        self.ttl[key] = seconds


def load_module(path: Path):
    if not path.exists():
        raise SystemExit(f"找不到实现文件：{path}")
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("candidate_l97", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_l97"] = module
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
            "gate": "L5.8-redis",
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

    def test_key():
        base = core.cache_key(SCOPE, "  RAG   是什么 ")
        expect(base.startswith("answer:"), f"前缀不对：{base}")
        expect(core.cache_key(SCOPE, "rag 是什么") == base or core.cache_key(SCOPE, "RAG 是什么") == core.cache_key(SCOPE, "  RAG   是什么 "), "空白/大小写归一化不一致")
        changed = dict(SCOPE, tenant_id="t2")
        expect(core.cache_key(changed, "RAG 是什么") != base, "租户变化应换键")
        try:
            core.cache_key(SCOPE, 1)
        except ValueError:
            return
        raise AssertionError("非字符串问题应报错")

    def test_cache():
        redis = FakeRedis()
        cache = core.RedisAnswerCache(redis, ttl_seconds=60)
        expect(cache.get(SCOPE, "q") is None, "未命中应 None")
        cache.set(SCOPE, "q", "answer")
        expect(cache.get(SCOPE, "q") == "answer", "应命中")
        expect(list(redis.ttl.values()) == [60], f"应设置 TTL：{redis.ttl}")

    def test_bytes():
        redis = FakeRedis()
        cache = core.RedisAnswerCache(redis, ttl_seconds=60)
        cache.set(SCOPE, "q", "answer")
        key = core.cache_key(SCOPE, "q")
        redis.data[key] = b"bytes-answer"
        expect(cache.get(SCOPE, "q") == "bytes-answer", "bytes 应 decode")

    def test_rate():
        limiter = core.FixedWindowRateLimiter(FakeRedis(), limit=2, window_seconds=60)
        expect(limiter.allow("t1", "u1", "w1") is True, "第 1 次应放行")
        expect(limiter.allow("t1", "u1", "w1") is True, "第 2 次应放行")
        expect(limiter.allow("t1", "u1", "w1") is False, "第 3 次应拒绝")
        expect(limiter.allow("t1", "u2", "w1") is True, "不同用户应独立")

    def test_fail_closed():
        redis = FakeRedis()
        limiter = core.FixedWindowRateLimiter(redis, limit=2, window_seconds=60)
        redis.fail = True
        try:
            limiter.allow("t1", "u1", "w1")
        except RuntimeError:
            return
        raise AssertionError("Redis 故障应 RuntimeError（失败关闭）")

    gate.check("01 缓存键", test_key)
    gate.check("02 缓存读写/TTL", test_cache)
    gate.check("03 bytes 解码", test_bytes)
    gate.check("04 固定窗口限流", test_rate)
    gate.check("05 失败关闭", test_fail_closed)
    return gate.report(module_path)


if __name__ == "__main__":
    raise SystemExit(main())
