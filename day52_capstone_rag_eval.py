"""
Day 52 · 把 RAG + Chroma 持久化 + 评测集接进项目（真实语料）
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目

把阶段1-2 的 RAG + Chroma + 评测接进 capstone，跑你自己的真实脏语料
（真实数据只在本地；公网 demo 换可公开语料）。本驱动调 capstone/main.py 把
"建库 → 问答 → 评测"一条龙跑通。

前置：把你的文档放进 capstone/docs/，根目录 .env 配好 DEEPSEEK_API_KEY + 本地 embedding。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "capstone" / "main.py"


def run(*args):
    subprocess.run([sys.executable, str(MAIN), *args], cwd=ROOT)


if __name__ == "__main__":
    print("== 1) 建/重建知识库（真实语料）==")
    run("build")
    print("\n== 2) 问答 ==")
    run("ask", "这个知识库讲了什么？")
    print("\n== 3) 跑评测出报告（capstone/data/eval_report.md）==")
    run("eval")
    print("\n要点：项目内能问答 + 跑评测，语料是真实脏数据；评测报告进 reports 留痕。")
