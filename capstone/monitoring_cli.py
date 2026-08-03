"""读取真实请求指标并执行可用于 CI/定时任务的告警判定。"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Literal

from capstone import monitoring


@dataclass(frozen=True)
class AlertRule:
    name: str
    metric: str
    threshold: float


@dataclass(frozen=True)
class AlertEvaluation:
    status: Literal["ok", "alert", "insufficient_data"]
    sample_count: int
    alerts: tuple[str, ...]


def evaluate_alerts(
    metrics: dict[str, int | float],
    *,
    min_samples: int = 20,
    rules: tuple[AlertRule, ...] | None = None,
) -> AlertEvaluation:
    """样本不足不能报告“健康”；达到最小样本后才执行阈值判断。"""
    if min_samples <= 0:
        raise ValueError("min_samples 必须大于 0")
    sample_count = int(metrics.get("样本数", 0))
    if sample_count < min_samples:
        return AlertEvaluation("insufficient_data", sample_count, ())
    active_rules = rules or (
        AlertRule("错误率", "错误率", 0.05),
        AlertRule("p95 延迟", "p95延迟ms", 8_000),
        AlertRule("窗口成本", "总成本", 5.0),
    )
    fired = tuple(
        f"{rule.name}: {rule.metric}={float(metrics[rule.metric]):g} > "
        f"{rule.threshold:g}"
        for rule in active_rules
        if float(metrics.get(rule.metric, 0)) > rule.threshold
    )
    return AlertEvaluation("alert" if fired else "ok", sample_count, fired)


def _demo_metrics() -> dict[str, int | float]:
    """确定性演示数据；不会污染生产指标库。"""
    return {
        "样本数": 100,
        "p50延迟ms": 620.0,
        "p95延迟ms": 8_400.0,
        "p99延迟ms": 11_200.0,
        "错误率": 0.02,
        "总token": 45_000,
        "总成本": 1.2,
        "缓存命中率": 0.31,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window-minutes", type=int, default=60)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--tenant")
    parser.add_argument("--min-samples", type=int, default=20)
    parser.add_argument("--max-error-rate", type=float, default=0.05)
    parser.add_argument("--max-p95-ms", type=float, default=8_000)
    parser.add_argument("--max-window-cost", type=float, default=5.0)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--fail-on-alert",
        action="store_true",
        help="告警或样本不足时返回非零退出码，适合 CI/定时任务",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.window_minutes <= 0
        or args.days <= 0
        or args.min_samples <= 0
        or args.max_error_rate < 0
        or args.max_p95_ms < 0
        or args.max_window_cost < 0
    ):
        raise SystemExit("窗口、样本数必须为正，告警阈值不能为负")
    metrics = (
        _demo_metrics()
        if args.demo
        else monitoring.health(args.window_minutes, tenant=args.tenant)
    )
    trend = (
        []
        if args.demo
        else monitoring.daily_cost_trend(args.days, tenant=args.tenant)
    )
    evaluation = evaluate_alerts(
        metrics,
        min_samples=args.min_samples,
        rules=(
            AlertRule("错误率", "错误率", args.max_error_rate),
            AlertRule("p95 延迟", "p95延迟ms", args.max_p95_ms),
            AlertRule("窗口成本", "总成本", args.max_window_cost),
        ),
    )
    payload = {
        "window_minutes": args.window_minutes,
        "tenant": args.tenant,
        "metrics": metrics,
        "evaluation": asdict(evaluation),
        "daily_cost_trend_utc": [
            {"date": day, "cost": cost, "requests": count}
            for day, cost, count in trend
        ],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"状态：{evaluation.status}，样本数：{evaluation.sample_count}")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        for alert in evaluation.alerts:
            print(f"  ALERT {alert}")
        if trend:
            print("最近有流量日期的成本（UTC）：")
            for day, cost, count in trend:
                print(f"  {day}: {cost:.6f} / {count} requests")
        print("告警通知、去重和静默窗口应交给 Alertmanager 等外部系统。")
    if args.fail_on_alert and evaluation.status != "ok":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
