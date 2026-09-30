"""
章节 0.1 · 环境自检
==========================================================
只检查三件事：解释器版本、依赖能否导入、配置是否存在。
不打印密钥，不连接模型或任何远端服务；通过也不代表账号有效或模型可用。

依赖按"从哪一篇开始需要"分组：缺哪一组，就知道会在哪一篇卡住。
分组里写的是 import 名，不是 pip 包名（例如 faiss-cpu 的导入名是 faiss）。

运行：python tools/run_chapter.py 0.1
退出码：0 = 解释器和必需依赖齐全；1 = 有缺项（可选项缺失不影响退出码）
==========================================================
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# 必需：第 1–5 篇的脚本会直接导入这些包
REQUIRED_GROUPS: dict[str, tuple[str, ...]] = {
    "第 1 篇 模型调用": ("dotenv", "langchain_core", "langchain_openai", "pydantic"),
    "第 2–3 篇 RAG 与评测": (
        "faiss",
        "langchain_community",
        "langchain_text_splitters",
        "langchain_huggingface",
        "langchain_classic",
        "langchain_chroma",
        "pypdf",
        "rank_bm25",
    ),
    "第 1、4 篇 MCP 与 Agent": ("langgraph", "mcp", "langchain_mcp_adapters"),
    "第 5 篇 服务化": ("fastapi", "uvicorn", "httpx", "pytest", "tenacity", "numpy"),
}

# 可选：只有对应章节用到，缺失时该章脚本会提示安装
OPTIONAL_GROUPS: dict[str, tuple[str, ...]] = {
    "1.6 mcp_agent.py（create_agent）": ("langchain",),
    "3.5 Ragas 评测": ("ragas", "datasets"),
    "3.6–3.8 LangSmith": ("langsmith",),
    "3.10 DeepEval 诊断": ("deepeval",),
    "4.10 长期记忆": ("langmem",),
    "4.12 联网搜索": ("tavily",),
    "5.6 本地 Ollama": ("ollama", "langchain_ollama"),
    "6.2 LoRA 微调": ("torch", "transformers", "peft"),
}


def missing_modules(names: tuple[str, ...]) -> list[str]:
    """返回 names 中无法导入的模块名。find_spec 只查是否安装，不真正导入。"""
    return [n for n in names if importlib.util.find_spec(n) is None]


def dotenv_has_key(name: str = "DEEPSEEK_API_KEY") -> bool:
    """.env 里是否为 name 填了非空值。只返回布尔值，不暴露内容。"""
    if importlib.util.find_spec("dotenv") is None:
        return False
    from dotenv import dotenv_values

    return bool((dotenv_values(ROOT / ".env").get(name) or "").strip())


def check_environment() -> dict[str, object]:
    required = {group: missing_modules(names) for group, names in REQUIRED_GROUPS.items()}
    optional = {group: missing_modules(names) for group, names in OPTIONAL_GROUPS.items()}
    return {
        "python": sys.version.split()[0],
        "python_supported": sys.version_info >= (3, 11),
        # 每组列出缺失的模块；空列表表示该组齐全
        "required_missing": required,
        "optional_missing": optional,
        # 只报告布尔值：密钥是否配置在 .env 或进程环境里；有值不代表密钥有效
        "dotenv_file_exists": (ROOT / ".env").is_file(),
        "dotenv_key_configured": dotenv_has_key(),
        "process_key_configured": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "external_services_checked": False,
    }


def main() -> int:
    report = check_environment()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    ok = report["python_supported"] and not any(report["required_missing"].values())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
