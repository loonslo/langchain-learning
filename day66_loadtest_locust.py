"""
Day66 · 负载压测（locust）：把"能跑"变成"扛得住"，并且能进 CI
==========================================================
测试工程师转 AI 应用开发 · 阶段6 上线补全

`docker run` 起来 ≠ 扛得住并发。但 LLM 服务的压测和普通 Web 服务有两点根本不同：

  ① 压测会【真烧钱】。20 并发压 60 秒 = 上千次模型调用。
     所以必须分两种模式，别混着跑：
       fake 模式  —— 上游换成固定延迟的假函数，量的是【我自己的服务】
                     能扛多少（FastAPI 线程池 + SQLite 数据层）。不花钱，能进 CI。
       real 模式  —— 打真模型，量的是【端到端】表现。花钱，手动跑，跑前先算账。
     搞不清这个区分，压出来的数字没有任何解释力。

  ② 瓶颈通常【不在你的代码里】，而在上游模型的响应时间和限流。
     所以光看"客户端总耗时"没用，你得能回答："这 3 秒里，多少是模型在想，
     多少是我的请求在排队？"

  ★ 本文件的核心方法：客户端 p95 与服务端 p95 对照。
     locust 量的是【客户端总耗时】（网络 + 排队 + 处理）；
     Day41 的 /chat 响应体里带了 latency_ms，是【服务端纯处理耗时】。
     两者相减 ≈ 排队时间。这个差值直接告诉你该往哪优化：
       差值小、两个都高  → 上游模型慢     → 换模型 / 减 token / 加缓存
       差值大           → 你的并发不够   → 加线程池 / 加副本 / 加限流
     这一条是压测报告里最值钱的结论，也是面试时最能体现"会分析"的地方。

压测完自动按 SLO 判定并给出【退出码】，可以直接挂进 CI（呼应 Day58 质量门禁）。

用法
----
1) 压假后端（不花钱，CI 用；本文件会自己把服务起起来）：
     python day66_loadtest_locust.py --fake --users 20 --time 30s --upstream-ms 800

2) 压真服务（先 uvicorn day41_serve_fastapi:app 起好）：
     python day66_loadtest_locust.py --host http://127.0.0.1:8000 --users 10 --time 60s

3) 交互式 UI（自己看拐点）：
     locust -f day66_loadtest_locust.py --host http://127.0.0.1:8000
     浏览器开 http://localhost:8089

依赖：pip install locust uvicorn
==========================================================
"""

from __future__ import annotations

import itertools
import json
import os
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPORTS = Path(__file__).parent / "reports"
SERVER_SIDE_FILE = REPORTS / "loadtest_server_side.json"

# ---- SLO：压测的通过标准。没有标准的压测只是"跑了一下"，不是测试 ----
# 环境变量可覆盖，方便不同环境（本地/预发/生产）用不同的线。
SLO = {
    "p95_ms": float(os.getenv("SLO_P95_MS", "3000")),          # 客户端 p95 上限
    "error_rate_pct": float(os.getenv("SLO_ERROR_PCT", "1.0")),  # 失败率上限
    "min_rps": float(os.getenv("SLO_MIN_RPS", "3")),            # 吞吐下限
}


# ============================================================
# 【一】locust 脚本：混合流量，而不是只压一个接口
# ============================================================
# 只压 /chat 压出来的数字是骗人的：真实流量里还有查历史、提反馈、探针，
# 它们同样要抢线程池和数据库连接。权重按真实业务比例配。
#
# ⚠️ 这个 import 必须加条件，踩过坑：`import locust` 会执行 gevent 的
# monkey.patch_all()，把【整个进程】的 socket / threading 全换成协程版。
# 本文件既被 locust 进程 import（需要 locust），又被下面的编排器直接运行
# （只需要 subprocess + httpx）。编排器进程一旦被 gevent patch 掉，
# 它自己的 HTTP 探活和子进程管理就会出各种诡异问题——而且不报错，只是行为不对。
# 判据：只有 locust 先启动、再来 import 本文件时，sys.modules 里才有 locust。
_UNDER_LOCUST = "locust" in sys.modules

try:
    if not _UNDER_LOCUST:
        raise ImportError("非 locust 进程，跳过 gevent 补丁")
    from locust import HttpUser, between, events, task

    QUESTIONS = [
        "RAG 为什么能减少幻觉？",
        "向量检索和关键词检索有什么区别？",
        "怎么评估一个知识库问答系统好不好？",
        "文档更新了，索引要怎么同步？",
    ]

    # 服务端自报的处理耗时，用来和客户端耗时做对照（本文件的核心指标）
    _server_latencies: list[int] = []
    _conversation_ids: list[int] = []

    class ChatUser(HttpUser):
        """模拟一个真实用户：主要问问题，偶尔翻历史、偶尔给反馈。"""

        wait_time = between(1, 3)   # 请求间隔，贴近真人；设 0 是压极限不是压真实

        _seq = itertools.count()

        def on_start(self):
            # 每个虚拟用户一个独立 user_id：否则所有请求都落在同一个 user 上，
            # /history 的索引和分页压根压不到，数据分布也不真实。
            self.uid = f"lt_{next(ChatUser._seq)}"

        @task(10)
        def ask(self):
            with self.client.post(
                "/chat",
                json={"question": random.choice(QUESTIONS), "user_id": self.uid},
                name="/chat",
                catch_response=True,
            ) as r:
                if r.status_code != 200:
                    r.failure(f"HTTP {r.status_code}")
                    return
                body = r.json()
                # ★ 关键：把服务端自报的 latency_ms 收集起来。
                # 这是 Day41 的 ChatResponse 特意返回的字段，就是为了这一刻。
                _server_latencies.append(body["latency_ms"])
                _conversation_ids.append(body["conversation_id"])
                r.success()

        @task(2)
        def read_history(self):
            self.client.get(f"/history?user_id={self.uid}&limit=10", name="/history")

        @task(1)
        def give_feedback(self):
            if not _conversation_ids:
                return
            self.client.post(
                "/feedback",
                json={"conversation_id": random.choice(_conversation_ids), "rating": 1},
                name="/feedback",
            )

        @task(1)
        def health(self):
            self.client.get("/health", name="/health")

    @events.test_stop.add_listener
    def dump_server_side(environment, **kw):
        """压测结束时把服务端耗时落盘，交给下面的编排器做对照分析。"""
        REPORTS.mkdir(exist_ok=True)
        data = {"count": len(_server_latencies)}
        if _server_latencies:
            s = sorted(_server_latencies)
            data.update({
                "p50_ms": s[len(s) // 2],
                "p95_ms": s[int(len(s) * 0.95) - 1 if len(s) > 1 else 0],
                "max_ms": s[-1],
                "avg_ms": round(statistics.mean(s)),
            })
        SERVER_SIDE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

except ImportError:
    # 没装 locust 也能 import 本文件读说明（和 CI 里做条件跳过）
    ChatUser = None  # type: ignore


# ============================================================
# 【二】假后端：量"我的服务"，而不是"上游模型"
# ============================================================
def make_fake_app(upstream_ms: int | None = None):
    """复用 Day41 的真实 app，只把上游 LLM 换成固定延迟的假函数。

    为什么不另写一个假服务：那样压的就不是真代码了。
    这里换掉的只有【最外层那一次模型调用】，中间件、异常处理、
    Pydantic 校验、Day44 落库全部走真实路径 —— 压出来的数字才作数。
    Day41 把 answer_fn 设计成可注入（STATE 里的一个函数），
    就是为了这种时刻：测试和压测都能换掉上游，生产代码一行不改。

    uvicorn 用法：uvicorn "day66_loadtest_locust:make_fake_app" --factory
    """
    import types
    from contextlib import asynccontextmanager

    delay = (upstream_ms if upstream_ms is not None
             else int(os.getenv("FAKE_UPSTREAM_MS", "800"))) / 1000

    # 顶掉 day12：假后端不需要真的建向量库（否则光启动就几十秒）
    stub = types.ModuleType("day12_rag_pdf_sources")
    stub.build_retriever = lambda path: None
    sys.modules.setdefault("day12_rag_pdf_sources", stub)

    import day41_serve_fastapi as api

    def fake_answer(question: str) -> dict:
        time.sleep(delay)          # 模拟上游模型思考耗时（阻塞，和真实调用一样）
        return {
            "answer": "这是压测用的固定答案。【来源】handbook.pdf 第3页",
            "sources": ["handbook.pdf#p3"],
            "prompt_tokens": 420,
            "completion_tokens": 90,
        }

    original_lifespan = api.app.router.lifespan_context

    @asynccontextmanager
    async def patched(app):
        async with original_lifespan(app):
            api.STATE["answer_fn"] = fake_answer
            api.STATE["error"] = None
            yield

    api.app.router.lifespan_context = patched
    return api.app


# ============================================================
# 【三】编排器：跑压测 → 对照分析 → SLO 门禁 → 退出码
# ============================================================
def _get(url: str, timeout: float = 5):
    """本机探活/取数专用的 GET。

    trust_env=False 是【必须】的：CI 机器和公司网络常年设着 HTTP_PROXY /
    ALL_PROXY，httpx 默认会读环境变量，结果把发往 127.0.0.1 的请求也塞进代理，
    表现是"服务明明起着，探活却一直失败"。本机流量永远不该走代理。
    """
    import httpx
    with httpx.Client(trust_env=False, timeout=timeout) as c:
        return c.get(url)


def _read_locust_csv(prefix: str) -> dict:
    """读 locust 的 --csv 输出，取 Aggregated 那一行。

    列名在不同 locust 版本间有差异，所以按候选名逐个试，
    而不是写死一个 —— 这类"依赖外部工具输出格式"的地方必须写容错。
    """
    import csv

    path = Path(f"{prefix}_stats.csv")
    if not path.exists():
        raise FileNotFoundError(f"没找到 {path}，locust 可能没跑起来")

    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    agg = next((r for r in rows if r.get("Name") == "Aggregated"), rows[-1])

    def pick(*names, default=0.0):
        for n in names:
            if agg.get(n) not in (None, "", "N/A"):
                return float(agg[n])
        return default

    total = pick("Request Count", "# requests")
    fails = pick("Failure Count", "# failures")
    return {
        "requests": int(total),
        "failures": int(fails),
        "error_rate_pct": round(fails / total * 100, 2) if total else 0.0,
        "rps": round(pick("Requests/s"), 2),
        "avg_ms": round(pick("Average Response Time", "Average response time")),
        "p95_ms": round(pick("95%", "95%ile", "95%ile (ms)")),
        "max_ms": round(pick("Max Response Time", "Max response time")),
        # 各接口分开的明细，用来看是不是某个接口拖后腿
        "per_endpoint": {
            r["Name"]: {"n": r.get("Request Count"), "p95": r.get("95%")}
            for r in rows if r.get("Name") not in ("Aggregated", None)
        },
    }


def _fetch_cost(host: str) -> float | None:
    """从 /stats 读当天累计成本。压测前后各读一次，差值就是这次压测烧的钱。"""
    try:
        rows = _get(f"{host}/stats?days=1").json()["rows"]
        return sum(r["cost_usd"] or 0 for r in rows)
    except Exception:                      # noqa: BLE001
        return None


def run(host: str, users: int, spawn_rate: int, duration: str) -> dict:
    REPORTS.mkdir(exist_ok=True)
    prefix = str(REPORTS / "loadtest")
    SERVER_SIDE_FILE.unlink(missing_ok=True)

    cost_before = _fetch_cost(host)
    cmd = [
        sys.executable, "-m", "locust", "-f", __file__, "--host", host,
        "--headless", "-u", str(users), "-r", str(spawn_rate), "-t", duration,
        "--csv", prefix, "--only-summary",
    ]
    print(f"$ {' '.join(cmd)}\n")
    # 同样的道理：压本机时把代理变量清掉，否则请求会绕一圈代理，
    # 测出来的延迟里混着代理的开销，数据就没意义了。
    env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
    env["NO_PROXY"] = env["no_proxy"] = "127.0.0.1,localhost"
    subprocess.run(cmd, check=False, env=env)
    cost_after = _fetch_cost(host)

    client = _read_locust_csv(prefix)
    server = json.loads(SERVER_SIDE_FILE.read_text(encoding="utf-8")) \
        if SERVER_SIDE_FILE.exists() else {}

    def _endpoint_p95(name: str):
        v = client["per_endpoint"].get(name, {}).get("p95")
        try:
            return round(float(v))
        except (TypeError, ValueError):
            return None

    report = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "host": host, "users": users, "duration": duration,
        "client": client, "server": server,
        "health_p95_ms": _endpoint_p95("/health"),
        # ★ 排队时间 = 客户端耗时 − 服务端处理耗时
        "queue_ms": (round(client["p95_ms"] - server["p95_ms"])
                     if server.get("p95_ms") is not None else None),
        "cost_usd": (round(cost_after - cost_before, 6)
                     if None not in (cost_before, cost_after) else None),
    }
    return report


def judge(report: dict) -> tuple[bool, list[str]]:
    """按 SLO 判定。返回 (是否通过, 违规说明)。"""
    c, violations = report["client"], []
    if c["p95_ms"] > SLO["p95_ms"]:
        violations.append(f"p95 {c['p95_ms']}ms > SLO {SLO['p95_ms']:.0f}ms")
    if c["error_rate_pct"] > SLO["error_rate_pct"]:
        violations.append(f"失败率 {c['error_rate_pct']}% > SLO {SLO['error_rate_pct']}%")
    if c["rps"] < SLO["min_rps"]:
        violations.append(f"吞吐 {c['rps']} rps < SLO {SLO['min_rps']} rps")
    return not violations, violations


def print_report(report: dict) -> None:
    c, s = report["client"], report["server"]
    print("\n" + "=" * 60)
    print(f"压测报告  {report['ts']}   {report['users']} 并发 / {report['duration']}")
    print("=" * 60)
    print(f"  请求总数     {c['requests']}   失败 {c['failures']} ({c['error_rate_pct']}%)")
    print(f"  吞吐         {c['rps']} req/s")
    print(f"  客户端 p95   {c['p95_ms']} ms   （网络 + 排队 + 处理）")
    if s.get("p95_ms") is not None:
        share = report["queue_ms"] / c["p95_ms"] * 100 if c["p95_ms"] else 0
        print(f"  服务端 p95   {s['p95_ms']} ms   （纯处理，服务自报）")
        print(f"  → 排队时间   {report['queue_ms']} ms（占 {share:.0f}%）")

    # ★ 第二个、也是更硬的排队证据：/health 的 p95。
    # /health 不查依赖、不调模型，正常情况下是个位数毫秒。
    # 它一旦变慢，慢的只可能是"排队等线程"——因为它自己根本没有活要干。
    # 换句话说，/health 的延迟就是你服务的【排队指示灯】，
    # 比用总耗时去减更不容易被误读。这个技巧对任何线程池服务都通用。
    health_p95 = report.get("health_p95_ms")
    if health_p95 is not None:
        print(f"  /health p95  {health_p95} ms   （空接口，正常应是个位数）")

    print("\n  判读：")
    if health_p95 is not None and health_p95 > 100:
        print(f"    /health 都要 {health_p95}ms → 请求在排队等线程，")
        print("    瓶颈在【你自己的服务】：加线程池 / 加副本 / 加限流。")
    elif share > 40:
        print("    排队占比高 → 并发能力不足，加线程池 / 加副本 / 加限流。")
    else:
        print("    排队很少、耗时几乎全在处理上 → 瓶颈在【上游模型】：")
        print("    换更快的模型 / 压缩 prompt 减 token / 对高频问题加缓存。")
    if report["cost_usd"] is not None:
        print(f"  本次压测成本 ${report['cost_usd']}")
    print("\n  各接口 p95：")
    for name, v in c["per_endpoint"].items():
        print(f"    {name:<12} n={v['n']:<6} p95={v['p95']}ms")

    ok, violations = judge(report)
    print("\n" + ("-" * 60))
    if ok:
        print("  ✅ SLO 通过")
    else:
        print("  ❌ SLO 未通过：")
        for v in violations:
            print(f"     - {v}")
    print("=" * 60)


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="LLM 服务压测 + SLO 门禁")
    p.add_argument("--host", default="http://127.0.0.1:8000")
    p.add_argument("--users", type=int, default=20)
    p.add_argument("--spawn-rate", type=int, default=5)
    p.add_argument("--time", dest="duration", default="30s")
    p.add_argument("--fake", action="store_true", help="自动起假后端（不调真模型，不花钱）")
    p.add_argument("--upstream-ms", type=int, default=800, help="假后端模拟的上游耗时")
    p.add_argument("--port", type=int, default=8899)
    args = p.parse_args()

    server_proc = None
    if args.fake:
        host = f"http://127.0.0.1:{args.port}"
        env = {**os.environ, "FAKE_UPSTREAM_MS": str(args.upstream_ms),
               "APP_DB_PATH": str(REPORTS / "loadtest.db")}
        REPORTS.mkdir(exist_ok=True)
        Path(env["APP_DB_PATH"]).unlink(missing_ok=True)   # 每次压测用干净的库
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "day66_loadtest_locust:make_fake_app",
             "--factory", "--port", str(args.port), "--log-level", "warning"],
            cwd=str(Path(__file__).parent), env=env,
        )
        # 等服务就绪，最多 30 秒；轮询探活而不是 sleep 硬等
        last_err = "超时"
        for _ in range(60):
            try:
                r = _get(f"{host}/ready", timeout=1)
                if r.status_code == 200:
                    break
                last_err = f"HTTP {r.status_code}: {r.text[:120]}"
            except Exception as e:                         # noqa: BLE001
                last_err = f"{type(e).__name__}: {e}"[:150]
            time.sleep(0.5)
        else:
            # 把最后一次的失败原因打出来。探活失败只说"起不来"是最坑的日志：
            # 端口占用、依赖缺失、代理拦截，看起来都一模一样。
            print(f"假后端起不来 —— 最后一次探活：{last_err}")
            server_proc.terminate()
            return 1
        print(f"假后端已就绪：{host}（模拟上游耗时 {args.upstream_ms}ms）\n")
    else:
        host = args.host

    try:
        report = run(host, args.users, args.spawn_rate, args.duration)
        print_report(report)
        out = REPORTS / f"loadtest_{time.strftime('%Y%m%d_%H%M%S')}.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n报告已保存：{out}")
        return 0 if judge(report)[0] else 1     # 退出码给 CI 用
    finally:
        if server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())


# ----------------------------------------------------------
# 小结（面试能直接讲的版本）：
# 1. LLM 服务压测必须分两种模式：fake 模式量【我的服务】容量（免费、可进 CI），
#    real 模式量【端到端】（烧钱、手动跑）。混着跑，数字没有解释力。
# 2. ★ 客户端 p95 − 服务端 p95 = 排队时间。这是判断"该优化谁"的关键：
#    排队占比高 → 我的并发不够；排队占比低而两者都高 → 上游模型慢。
#    能拿出这个对照，说明你会分析，而不只是会跑工具。
# 3. 压测要压【混合流量】。只压主接口，会漏掉查询接口抢线程池/连接的影响。
# 4. 压测必须有 SLO 和退出码，否则只是"跑了一下"，不是测试。
#    有了退出码就能挂进 CI（Day58），性能劣化和质量劣化一样被拦住。
# 5. 压测成本要算出来（/stats 前后差值）。这是 LLM 应用独有的一项，
#    面试里提到"我压测前会先估算这轮要烧多少钱"，是很强的工程成熟度信号。
# 6. 拐点判读：并发往上加，QPS 不再涨而 p95 陡升的那一点，就是当前架构上限。
#
# 接下来能做的：
# - 把 --fake 模式挂进 .github/workflows/eval-gate.yml，和 Day58 的质量门禁并列，
#   变成"质量 + 性能"双门禁。
# - 调 --upstream-ms 模拟上游变慢（800 → 3000），观察排队时间怎么被放大，
#   这是理解"为什么上游慢一点，你的服务会崩得很快"最直观的实验。
#
# 动手练习：固定 --upstream-ms 800，把 --users 从 5 逐步加到 80，
#           把每轮的 rps / 客户端 p95 / 排队时间记下来画成曲线，找出拐点。
# ----------------------------------------------------------
