"""
Day 54 · 真实数据接入 + 增量同步
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目（企业第一梯队）

企业知识库天天增删改，全量重建又慢又贵。增量同步只处理变化的文件：
新增入库、改过的先删旧块再入新块、删掉的从向量库清掉。判断"变没变"靠内容 hash。

实现在 capstone/connector.py（以本地文件夹为数据源；换 Notion/DB 只改 _scan_source）。
本驱动跑一次同步。验收：改/删一个 docs/ 文件再跑，检索结果跟着变。
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    print("== 跑一次增量同步（先确保已 build 过：python capstone/main.py build）==")
    subprocess.run([sys.executable, "connector.py"], cwd=ROOT / "capstone")
    print("\n验收：改一个 docs/ 文件重跑本脚本，检索跟着变；删一个文件它不再被检索到。")
    print("要点：增量同步 = 只处理变化的，不全量重建——这是真实数据接入的及格线。")
