"""
Day 24 · prompt A/B 对比 + judge 一致性校验
==========================================================
测试工程师转 AI 应用开发 · 阶段2 评测做深（护城河）

两件事：
1. prompt A/B：两版 prompt（如 strict / helpful）在同一评测集上对比打分，用数据选 prompt，
   不靠"我觉得这版顺眼"。
2. judge 一致性：LLM-as-judge 自己也会错。抽样人工标注，校验 judge 打分和人工的一致率——
   知道"我的裁判有多准"，才敢信它的数。一致率太低就别用这个 judge。

实现复用评测平台模块：evals/prompt_ab_judge_agreement.py
结果落 reports/prompt_ab_judge_agreement.json。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_ab_and_agreement():
    cmd = [sys.executable, "-m", "evals.prompt_ab_judge_agreement"]
    print("运行：", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT)
    print("\n结果在 reports/prompt_ab_judge_agreement.json：两版 prompt 的对比分 + judge 与人工一致率。")


if __name__ == "__main__":
    run_ab_and_agreement()
    print("\n要点：prompt 用 A/B 数据选，不靠感觉；judge 先和人工对齐、知道它多准再信它。")
