"""
Day 53 · Agent + MCP + HITL + agent 评测 接进项目
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目

把阶段3 的 LangGraph Agent（capstone/agent.py：知识库工具 + HITL 发布审批）
接进项目，并把阶段2 的 agent 轨迹评测（Day25 / evals/agent_trajectory_eval）接进来。
MCP 工具、Text2SQL 工具按需挂（Day38/Day40 已实现，接法相同）。

本驱动跑一次 capstone/agent.py 的 HITL 演示，再跑一次轨迹评测。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_agent_demo():
    # agent.py 用 import config 风格，按脚本在 capstone/ 下跑
    subprocess.run([sys.executable, "agent.py"], cwd=ROOT / "capstone")


def run_trajectory_eval():
    subprocess.run([sys.executable, "-m", "evals.agent_trajectory_eval"], cwd=ROOT)


if __name__ == "__main__":
    print("== 1) Agent + HITL 发布审批演示 ==")
    run_agent_demo()
    print("\n== 2) agent 轨迹评测（工具调用正确性 / 禁用工具 / 完成率）==")
    run_trajectory_eval()
    print("\n要点：项目内 Agent 能调工具、高风险动作等确认、且被轨迹评测覆盖。")
