"""
capstone/monitoring.py · 项目级监控（Day62 集成版）
==========================================================
day62 讲了原理，这里把它接进毕业项目：每次问答记一行，
/metrics 端点吐出整体健康度。和单条 SQLite 对话日志分开存，
监控看的是聚合趋势，不是某一条。
==========================================================
"""

import sqlite3
from datetime import datetime, timedelta

import config as C

_METRICS_DB = str(C.HERE / "data" / "metrics.db")


def _init():
    with sqlite3.connect(_METRICS_DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS req(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, tenant TEXT,
            latency_ms REAL, is_error INTEGER, tokens INTEGER, cost REAL)""")


def record(tenant: str, latency_ms: float, is_error: bool, tokens: int = 0, cost: float = 0.0):
    _init()
    with sqlite3.connect(_METRICS_DB) as c:
        c.execute("INSERT INTO req(ts,tenant,latency_ms,is_error,tokens,cost) VALUES(?,?,?,?,?,?)",
                  (datetime.now().isoformat(timespec="seconds"), tenant,
                   latency_ms, int(is_error), tokens, cost))


def _pct(vals, p):
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100
    lo = int(k); hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)


def health(window_minutes: int = 60) -> dict:
    _init()
    since = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
    with sqlite3.connect(_METRICS_DB) as c:
        rows = c.execute("SELECT latency_ms,is_error,tokens,cost FROM req WHERE ts>=?",
                         (since,)).fetchall()
    if not rows:
        return {"样本数": 0}
    lat = [r[0] for r in rows]; n = len(rows)
    return {
        "样本数": n,
        "p95延迟ms": _pct(lat, 95),
        "p99延迟ms": _pct(lat, 99),
        "错误率": round(sum(r[1] for r in rows) / n, 4),
        "总成本": round(sum(r[3] for r in rows), 4),
    }
