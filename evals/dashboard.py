"""
生成一个零依赖 HTML 评测看板。

运行：
    python -m evals.run_eval_platform
    python -m evals.agent_trajectory_eval
    python -m evals.dashboard
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_history() -> list[dict]:
    path = REPORTS / "eval_runs.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(name: str) -> dict:
    path = REPORTS / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    rows = load_history()
    latest = rows[-1] if rows else {}
    agent = load_json("agent_trajectory_eval.json")
    html_rows = "\n".join(
        "<tr>" + "".join(f"<td>{r.get(k, '')}</td>" for k in ["run_id", "commit", "prompt_variant", "pass_rate", "avg_latency_ms", "total_cost_usd", "failures"]) + "</tr>"
        for r in rows[-20:]
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>RAG / Agent 评测看板</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
    h1 {{ font-size: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; }}
    .metric strong {{ display: block; font-size: 24px; margin-top: 6px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; }}
  </style>
</head>
<body>
  <h1>RAG / Agent 评测看板</h1>
  <div class="grid">
    <div class="metric">RAG 通过率<strong>{latest.get('pass_rate', 'n/a')}</strong></div>
    <div class="metric">平均延迟 ms<strong>{latest.get('avg_latency_ms', 'n/a')}</strong></div>
    <div class="metric">总成本 USD<strong>{latest.get('total_cost_usd', 'n/a')}</strong></div>
    <div class="metric">Agent 轨迹通过率<strong>{agent.get('agent_trajectory_pass_rate', 'n/a')}</strong></div>
  </div>
  <h2>最近评测运行</h2>
  <table>
    <thead><tr><th>run_id</th><th>commit</th><th>prompt</th><th>pass_rate</th><th>latency</th><th>cost</th><th>failures</th></tr></thead>
    <tbody>{html_rows}</tbody>
  </table>
</body>
</html>
"""
    out = REPORTS / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"看板已生成：{out}")


if __name__ == "__main__":
    main()
