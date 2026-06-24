"""
Day 59 · 端到端联调 + 一轮改进闭环
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目

两件事：
1. 端到端联调：上传→问答→引用→评测→trace 全流程跑顺，修 bug。
2. 一轮完整改进闭环（面试可讲，最有说服力的证据）：
   从失败用例库挑一个真实 case → 改 prompt/chunk/检索 → 评测验证变好 →
   回归曲线证明没弄坏别的。全程留痕。

本驱动跑一个最小 e2e：build → ask → eval（出报告 + 失败库），
失败库就是改进闭环的起点（capstone/data/failures.json）。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "capstone" / "main.py"

IMPROVEMENT_LOOP = """
改进闭环模板（挑一个 failures.json 里的 case 做，并记录）：
1. 现象：case「<问题>」答错，失败库归因「检索没召回 / 召回了生成错 / 应拒答却乱答」。
2. 假设：是 chunk 太大带噪 / 缺关键词召回 / prompt 拒答约束太松。
3. 改动：只改一处（如 chunk_size 或加 BM25 或收紧 prompt）。
4. 验证：重跑评测，这条过了，且 reports/eval_runs.csv 回归曲线整体没退。
5. 留痕：commit 写清"改了啥、为什么、指标从 X 到 Y"——面试直接讲这条。
"""


if __name__ == "__main__":
    print("== 端到端 smoke：build → ask → eval ==")
    for args in (["build"], ["ask", "知识库讲了什么？"], ["eval"]):
        subprocess.run([sys.executable, str(MAIN), *args], cwd=ROOT)
    print("\n失败用例库：capstone/data/failures.json —— 改进闭环从这里挑 case。")
    print(IMPROVEMENT_LOOP)
