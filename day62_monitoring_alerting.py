"""
Day62 · 生产监控 + 告警：p95/p99 延迟、错误率、token 成本趋势
==========================================================
测试工程师转 AI 应用开发 · 阶段6 上线补全

这天学什么：
- 单条 trace（day21 LangSmith）回答"这一次为什么错"；监控回答"整体健不健康"。
- 三个生产必看指标：延迟分位数（p95/p99，别看平均值）、错误率、每日成本趋势。
- 告警 = 指标越线就发信号，而不是等用户来报障。

为什么看分位数不看平均：平均值会被"大部分请求很快"掩盖掉长尾。
真正让用户骂街的是最慢那 5%（p95）。SLO 都是按分位数定的。

数据从哪来：复用业务库里每次请求落的一行日志（耗时、是否出错、token）。
这里用 SQLite 自带一个最小 metrics 表跑通，生产可换 Prometheus + Grafana。
==========================================================
"""

import sqlite3
import time
import random
from datetime import datetime, timedelta

DB = "metrics_demo.db"


def _init():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, latency_ms REAL, is_error INTEGER,
            tokens INTEGER, cost REAL)""")


def record(latency_ms: float, is_error: bool, tokens: int, cost: float):
    """每次请求结束时调一行——监控的原料就是这张表。"""
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO requests(ts,latency_ms,is_error,tokens,cost) VALUES(?,?,?,?,?)",
                  (datetime.now().isoformat(timespec="seconds"),
                   latency_ms, int(is_error), tokens, cost))


def _percentile(values: list[float], p: float) -> float:
    """p 分位（p=95 表示 95%）。手写一遍，理解 p95 是怎么算出来的。"""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)   # 线性插值


def health(window_minutes: int = 60) -> dict:
    """最近 window 内的整体健康度：延迟分位、错误率、成本。"""
    since = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
    with sqlite3.connect(DB) as c:
        rows = c.execute("SELECT latency_ms,is_error,tokens,cost FROM requests WHERE ts>=?",
                         (since,)).fetchall()
    if not rows:
        return {"样本数": 0}
    lat = [r[0] for r in rows]
    errors = sum(r[1] for r in rows)
    n = len(rows)
    return {
        "样本数": n,
        "p50延迟ms": round(_percentile(lat, 50), 1),
        "p95延迟ms": round(_percentile(lat, 95), 1),
        "p99延迟ms": round(_percentile(lat, 99), 1),
        "错误率": round(errors / n, 4),
        "总token": sum(r[2] for r in rows),
        "总成本": round(sum(r[3] for r in rows), 4),
    }


# ---- 告警：指标越线就触发，平时静默 ----
ALERT_RULES = {
    "错误率": ("错误率", 0.05),      # 错误率 > 5%
    "p95延迟": ("p95延迟ms", 8000),  # p95 > 8s
    "成本": ("总成本", 5.0),          # 当前窗口成本 > 5 元
}


def check_alerts(metrics: dict) -> list[str]:
    fired = []
    for name, (key, threshold) in ALERT_RULES.items():
        val = metrics.get(key, 0)
        if val > threshold:
            fired.append(f"告警[{name}]：{key}={val} 超过阈值 {threshold}")
    return fired


def daily_cost_trend(days: int = 7) -> list[tuple]:
    """每日成本趋势：看成本是不是在悄悄涨（缓存失效 / 模型选错都会暴露在这）。"""
    with sqlite3.connect(DB) as c:
        return c.execute(
            "SELECT substr(ts,1,10) d, ROUND(SUM(cost),4), COUNT(*) "
            "FROM requests GROUP BY d ORDER BY d DESC LIMIT ?", (days,)).fetchall()


def _seed_demo():
    """造一批模拟流量，方便没有真实流量也能看到效果。"""
    for _ in range(200):
        slow = random.random() < 0.05         # 5% 长尾慢请求
        lat = random.uniform(3000, 9000) if slow else random.uniform(400, 1500)
        err = random.random() < 0.03           # 3% 出错
        record(lat, err, tokens=random.randint(200, 1200), cost=random.uniform(0.002, 0.02))


if __name__ == "__main__":
    _init()
    _seed_demo()
    m = health()
    print("== 整体健康度（最近 60 分钟）==")
    for k, v in m.items():
        print(f"  {k}: {v}")
    print("\n== 告警检查 ==")
    alerts = check_alerts(m)
    print("\n".join("  " + a for a in alerts) if alerts else "  全部指标正常")
    print("\n== 每日成本趋势 ==")
    for d, cost, cnt in daily_cost_trend():
        print(f"  {d}: 成本 {cost}（{cnt} 次请求）")
    print("\n要点：监控看分位数和趋势，不看单条；阈值越线再告警，避免告警疲劳。")
