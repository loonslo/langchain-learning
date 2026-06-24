"""
Day 55 · 文档级权限过滤（检索层）
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目（企业 RAG 最痛点、面试最常问）

A 部门的人不能从知识库问出 B 部门的机密。核心：权限必须在检索层做，不能靠 prompt——
靠 prompt 是把机密塞进上下文再求模型别说，一次注入就泄露。

实现在 capstone/permissions.py：每个 chunk 带权限 metadata，检索时按用户身份过滤，
无权的 chunk 根本进不了上下文。本驱动跑权限判定演示（不连模型）。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    print("== 权限判定演示：同一份文档，不同用户看到的不一样 ==")
    subprocess.run([sys.executable, "permissions.py"], cwd=ROOT / "capstone")
    print("\n验收：同一问题用户 A 和 B 召回到的来源不同。")
    print("面试话术：权限放检索层、用 can_see() 在召回后进 prompt 前过滤；"
          "放 prompt 是软约束，一次注入或模型抽风就泄露。")
