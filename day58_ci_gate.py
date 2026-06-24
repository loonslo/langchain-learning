"""
Day 58 · CI 评测门禁（最硬的作品点）★
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目

"测试转 AI"讲一万句，不如一条 CI：改坏 prompt → 评测红 → PR 被挡住。

实现两件：
- capstone/ci_gate.py：建库→跑评测→和阈值比，跌破阈值 exit 1。
- .github/workflows/eval-gate.yml：PR 触发，跑 pytest + ci_gate，失败就拦 merge。

本驱动在本机跑一次 ci_gate，看绿/红。验收：故意删掉 prompt 里的拒答约束、push PR，CI 应红。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    print("== 本机跑一次评测门禁（exit 0 绿 / exit 1 红）==")
    r = subprocess.run([sys.executable, "ci_gate.py"], cwd=ROOT / "capstone")
    print(f"\nci_gate 退出码：{r.returncode}（0=通过允许合并；非0=拦截）")
    print("\nCI 配置：.github/workflows/eval-gate.yml —— PR 触发 pytest + 这个门禁。")
    print("演示：删掉 knowledge_base.chain() 里的拒答约束 → push PR → CI 评测红、merge 被挡。")
    print("这就是测试背景在 AI 岗最硬的作品点：质量门禁挡在合并之前。")
