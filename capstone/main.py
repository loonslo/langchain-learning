"""
capstone/main.py · 项目 CLI 入口：一处把全流程串起来
==========================================================
用法（在 capstone/ 目录或仓库根目录跑）：
  python capstone/main.py build     # 建/重建知识库
  python capstone/main.py ask 你的问题
  python capstone/main.py eval      # 跑评测出报告
==========================================================
"""

import sys
import config as C
from knowledge_base import KnowledgeBase


def main(argv):
    if not argv:
        print(__doc__); return
    cmd = argv[0]
    if cmd == "build":
        KnowledgeBase().build(rebuild=True)
    elif cmd == "ask":
        kb = KnowledgeBase().build()
        print(kb.answer(" ".join(argv[1:]) or "知识库讲了什么？"))
    elif cmd == "eval":
        from evaluation import run
        kb = KnowledgeBase().build()
        print("评测：", run(kb))
    else:
        print("未知命令：", cmd); print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
