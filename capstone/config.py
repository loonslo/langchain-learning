"""
capstone/config.py · 项目统一配置 + 复用上游 common
==========================================================
毕业项目把前面 day01-44 的能力整合成一个真实应用。
为了不重复造轮子，模型/embedding 仍走仓库根目录的 common.py。
本文件负责：把根目录加进 import 路径、再导出全项目要用的配置与工厂。
==========================================================
"""

import os
import sys
from pathlib import Path

# 让 capstone 子包能 import 到根目录的 common.py
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common import get_llm, get_embeddings, ZH_SEPARATORS  # noqa: E402

# ---- 项目路径 ----
HERE = Path(__file__).resolve().parent
DOCS_DIR = HERE / "docs"          # 放知识库源文档（txt/pdf/md）
CHROMA_DIR = str(HERE / "data" / "chroma")   # 向量库落盘
DB_PATH = str(HERE / "data" / "app.db")      # 业务数据库（对话记录）
EVAL_SET = HERE / "data" / "eval_set.json"   # 评测集
REPORT_PATH = HERE / "data" / "eval_report.md"
FAILURES_PATH = HERE / "data" / "failures.json"

# 检索参数
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
TOP_K = 4

__all__ = ["get_llm", "get_embeddings", "ZH_SEPARATORS",
           "DOCS_DIR", "CHROMA_DIR", "DB_PATH", "EVAL_SET",
           "REPORT_PATH", "FAILURES_PATH", "CHUNK_SIZE", "CHUNK_OVERLAP", "TOP_K"]
