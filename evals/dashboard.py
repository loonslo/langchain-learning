"""
生成一个零依赖 HTML 评测看板。

运行：
    python -m evals.run_eval_platform
    python -m evals.agent_trajectory_eval
    python -m evals.dashboard

看板读取：
- reports/eval_runs.csv        : RAG 评测历史（回归曲线）
- reports/agent_trajectory_eval.json : Agent 轨迹评测结果
- reports/latest_report.md     : 最新 Markdown 报告

输出：reports/dashboard.html
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

# HTML 看板模板。使用占位符 {{xxx}}，后续用 str.replace 填充。
# 零依赖：不引入任何前端框架或图表库，直接生成静态 HTML。
HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>RAG / Agent 评测看板</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #1f2937; background: #f9fafb; }
    h1 { font-size: 28px; margin-bottom: 8px; }
    .subtitle { color: #6b7280; margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; margin-bottom: 24px; }
    .metric { background: #fff; border: 1px solid #d1d5db; border-radius: 8px; padding: 16px; }
    .metric label { display: block; font-size: 12px; color: #6b7280; margin-bottom: 4px; }
    .metric strong { display: block; font-size: 26px; color: #111827; }
    .section { background: #fff; border: 1px solid #d1d5db; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
    .section h2 { margin-top: 0; font-size: 18px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #e5e7eb; padding: 10px; text-align: left; font-size: 14px; }
    th { background: #f3f4f6; font-weight: 600; }
    .pass { color: #059669; }
    .fail { color: #dc2626; }
    .note { color: #6b7280; font-size: 13px; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>RAG / Agent 评测看板</h1>
  <p class="subtitle">阶段2 收尾：把质量、成本、延迟、失败用例汇成一页，截图即可放进作品集。</p>

  <div class="grid">
    <div class="metric"><label>RAG 通过率</label><strong>{{pass_rate}}</strong></div>
    <div class="metric"><label>平均延迟 ms</label><strong>{{avg_latency_ms}}</strong></div>
    <div class="metric"><label>总成本 USD</label><strong>{{total_cost_usd}}</strong></div>
    <div class="metric"><label>Agent 轨迹通过率</label><strong>{{agent_trajectory_pass_rate}}</strong></div>
  </div>

  <div class="section">
    <h2>最近评测运行（回归曲线数据源）</h2>
    <table>
      <thead>
        <tr><th>run_id</th><th>commit</th><th>prompt</th><th>pass_rate</th><th>latency</th><th>cost</th><th>failures</th></tr>
      </thead>
      <tbody>{{history_rows}}</tbody>
    </table>
    <p class="note">注：数据来自 reports/eval_runs.csv。每次跑 python -m evals.run_eval_platform 都会追加一行。</p>
  </div>

  <div class="section">
    <h2>Agent 轨迹评测明细</h2>
    <table>
      <thead>
        <tr><th>case_id</th><th>问题</th><th>期望工具</th><th>禁用工具</th><th>通过</th><th>步骤数</th></tr>
      </thead>
      <tbody>{{agent_rows}}</tbody>
    </table>
    <p class="note">注：数据来自 reports/agent_trajectory_eval.json。 trajectory 评测看"该调的工具调了没、禁用工具调了没、有没有最终回答"。</p>
  </div>

  <div class="section">
    <h2>面试/作品集用法</h2>
    <ul>
      <li>指着通过率说："当前 RAG 通过 X%，Agent 轨迹通过 Y%。"</li>
      <li>指着失败用例说："这 Z 条失败里，A 条是检索没召回，B 条是召回了但生成错。"</li>
      <li>指着回归记录说："每次 commit 后都会跑一遍，形成回归曲线，防止改代码时退化。"</li>
    </ul>
  </div>
</body>
</html>
"""


def load_history() -> list[dict]:
    """加载 RAG 评测历史 CSV。"""
    path = REPORTS / "eval_runs.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_json(name: str) -> dict:
    """加载 reports 目录下的 JSON 文件。"""
    path = REPORTS / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def render_history_rows(rows: list[dict]) -> str:
    """把 CSV 行渲染成 HTML table rows。"""
    keys = ["run_id", "commit", "prompt_variant", "pass_rate", "avg_latency_ms", "total_cost_usd", "failures"]
    lines = []
    for r in rows[-20:]:
        cells = "".join(f"<td>{r.get(k, '')}</td>" for k in keys)
        lines.append(f"<tr>{cells}</tr>")
    return "\n".join(lines)


def render_agent_rows(agent_data: dict) -> str:
    """把 Agent 轨迹评测结果渲染成 HTML table rows。"""
    lines = []
    for r in agent_data.get("results", []):
        passed_class = "pass" if r["passed"] else "fail"
        passed_text = "✓ 通过" if r["passed"] else "✗ 失败"
        expected = ", ".join(r.get("expected_tools", [])) or "-"
        forbidden = ", ".join(r.get("forbidden_tools", [])) or "-"
        cells = [
            f"<td>{r['case_id']}</td>",
            f"<td>{r.get('question', '')}</td>",
            f"<td>{expected}</td>",
            f"<td>{forbidden}</td>",
            f"<td class='{passed_class}'>{passed_text}</td>",
            f"<td>{r.get('step_count', 0)}</td>",
        ]
        lines.append("<tr>" + "".join(cells) + "</tr>")
    return "\n".join(lines)


def main() -> None:
    """主流程：读取历史记录和 Agent 评测结果，生成 HTML 看板。"""
    REPORTS.mkdir(exist_ok=True)

    rows = load_history()
    latest = rows[-1] if rows else {}
    agent = load_json("agent_trajectory_eval.json")

    # 格式化数字：通过率转成百分比，延迟/成本保留原样
    pass_rate = f"{float(latest.get('pass_rate', 0)):.1%}" if latest else "n/a"
    avg_latency = latest.get("avg_latency_ms", "n/a") if latest else "n/a"
    total_cost = latest.get("total_cost_usd", "n/a") if latest else "n/a"
    agent_pass = f"{float(agent.get('agent_trajectory_pass_rate', 0)):.1%}" if agent else "n/a"

    html = (
        HTML_TEMPLATE
        .replace("{{pass_rate}}", pass_rate)
        .replace("{{avg_latency_ms}}", str(avg_latency))
        .replace("{{total_cost_usd}}", str(total_cost))
        .replace("{{agent_trajectory_pass_rate}}", agent_pass)
        .replace("{{history_rows}}", render_history_rows(rows))
        .replace("{{agent_rows}}", render_agent_rows(agent))
    )

    out = REPORTS / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"看板已生成：{out}")


if __name__ == "__main__":
    main()
