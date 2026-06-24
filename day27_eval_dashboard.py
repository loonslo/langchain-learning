"""
Day 27 · 评测看板 + 阶段2 验收
==========================================================
测试工程师转 AI 应用开发 · 阶段2 收尾（首个可投作品）

评测做了一堆指标，面试时要能"拿出来给人看"。看板把质量/成本/延迟/回归曲线/失败用例
汇成一页 HTML，截图就能放进简历和作品集。

阶段2 验收：评测平台能单独 demo；拿得出带计算方法的数字
（"拒答召回率 X%、幻觉率 Y%，改 chunk 后到 Z%"）；能评 agent 轨迹，不止评 RAG。

实现复用 evals/dashboard.py。完整链路（先跑评测攒数据，再出看板）：
  python -m evals.run_eval_platform
  python -m evals.agent_trajectory_eval
  python -m evals.dashboard      # 生成 reports/dashboard.html
==========================================================
"""

import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_dashboard(open_browser: bool = False):
    for mod in ("evals.run_eval_platform", "evals.agent_trajectory_eval", "evals.dashboard"):
        print("运行：", mod)
        subprocess.run([sys.executable, "-m", mod], cwd=ROOT)
    html = ROOT / "reports" / "dashboard.html"
    print(f"\n看板已生成：{html}")
    if open_browser and html.exists():
        webbrowser.open(html.as_uri())


if __name__ == "__main__":
    build_dashboard()
    print("\n阶段2 验收：这页看板 = 你的首个可投作品。面试直接拿出'幻觉率 X%、失败分析'。")
