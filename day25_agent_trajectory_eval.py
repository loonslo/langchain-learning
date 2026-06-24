"""
Day 25 · Agent 评测：轨迹 / 工具调用 / 任务完成率
==========================================================
测试工程师转 AI 应用开发 · 阶段2 评测做深（护城河）★面试官一问就漏的地方

RAG 评测只测"答得对不对"；Agent 还得测"做得对不对"——这就是轨迹(trajectory)评测：
- 工具调用是否正确（该调 search 的时候调没调、参数对不对）；
- 有没有调禁用工具（比如真实删除/支付）；
- 步骤是否合理、有没有绕远路；
- 任务完成率。

评测对象从 RAG 扩到 Agent，是阶段2 区别于"只会跑 RAGAS"的关键。
实现复用 evals/agent_trajectory_eval.py（先用离线轨迹样本保证稳定；
真实项目把 Agent 跑出来的 trajectory 落盘再喂进来）。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_trajectory_eval():
    cmd = [sys.executable, "-m", "evals.agent_trajectory_eval"]
    print("运行：", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT)
    print("\n结果在 reports/agent_trajectory_eval.json：工具调用正确性、禁用工具命中、完成率。")


if __name__ == "__main__":
    run_trajectory_eval()
    print("\n要点：Agent 要测轨迹，不止测最终答案。评测集 = agentic loop 的反馈信号——"
          "Day39 会把搜索 Agent 的真实轨迹接进来跑一遍。")
