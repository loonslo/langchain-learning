"""
customer_service/config.py · 配置：复用根目录 common.py，只加客服项目自己的路径
==========================================================
与 capstone/config.py 同一套路：换机器 / 换 key 只改根目录 .env。
OFFLINE 模式：没配 DEEPSEEK_API_KEY 时全链路走规则/检索兜底，
评估与回归测试不花一分钱也能跑（与 evals 平台同思路）。
==========================================================
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # 让 import common 生效

from common import get_llm  # noqa: E402,F401  复用 LLM 工厂（temperature=0 可复现）

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
REPORTS_DIR = BASE / "reports"
DB_PATH = Path(os.getenv("CS_DB_PATH", BASE / "cs.db"))  # 会话+工单 SQLite（day44）；CI 可用环境变量指到临时目录
FAQ_FILE = DATA_DIR / "faq.md"
EVAL_SET = DATA_DIR / "eval_set.json"

# 没有 key → 离线模式：意图走规则、FAQ 走 BM25 直出，保证 pytest/CI 可跑
OFFLINE = not os.getenv("DEEPSEEK_API_KEY")

INTENTS = ("faq", "order", "complaint", "chitchat")
