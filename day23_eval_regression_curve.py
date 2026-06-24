"""
Day 23 · 评测集版本化 + 回归曲线
==========================================================
测试工程师转 AI 应用开发 · 阶段2 评测做深（护城河）

评测不是"跑一次出个数"。要能回答："我这次改 prompt/chunk，到底让质量变好还是变坏了？"
做法：评测集进 git（版本化）→ 每次改动跑一遍、把指标按 commit 记一行 →
画出指标随 commit 的回归曲线，一眼看出"哪次改动让幻觉率涨了"。

本课的实现放在可单独展示的评测平台模块 `evals/`：
- evals/eval_cases.json   评测集（进 git 版本化）
- evals/run_eval_platform.py  跑评测 + 把每次结果追加进 reports/eval_runs.csv（回归记录）
- reports/eval_runs.csv   每行 = 一次 commit 的通过率/延迟/token/成本/失败数 → 回归曲线的原料

这个 day 文件是入口说明 + 驱动；真正的平台代码复用 evals/，不重复造。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_platform(mode: str = "offline"):
    """跑一次评测平台，结果追加到 reports/eval_runs.csv 形成回归记录。
    offline 模式用可复现的演示回答，没 API key 也能跑通看曲线链路。"""
    cmd = [sys.executable, "-m", "evals.run_eval_platform", "--mode", mode]
    print("运行：", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT)
    print("\n回归记录在 reports/eval_runs.csv；多跑几次（每次改完代码）就有了回归曲线。")


if __name__ == "__main__":
    run_platform()
    print("\n要点：评测集版本化 = 进 git；回归曲线 = 指标随 commit 的走势。"
          "改坏了立刻在曲线上看到，这就是质量回归的护城河。")
