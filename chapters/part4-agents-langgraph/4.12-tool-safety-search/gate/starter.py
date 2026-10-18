"""L4.10 扩展 · 搜索信任边界 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
tool_safety_search.py。实现下面两个函数，然后运行：

    python chapters/part4-agents-langgraph/4.12-tool-safety-search/gate/gate_check.py
"""

from __future__ import annotations

TAG = "untrusted_search_results"


def as_untrusted(text: str) -> str:
    """把外部资料包进 <untrusted_search_results> 标签。

    要求：
    - 先删除文本里伪造的同名开/闭标签，防止提前闭合；
    - 输出形如 "<tag>\\n{cleaned}\\n</tag>"；
    - 非字符串 -> ValueError。
    """
    raise NotImplementedError("实现不可信资料包装")


def detect_injection(text: str) -> list[str]:
    """返回命中的提示词注入特征，保持检查顺序。

    至少覆盖：
    - "忽略之前" / "忽略以上"
    - "ignore previous" / "ignore all previous"
    - "system prompt" / "系统提示词"
    - "已通过审核"
    无命中 -> []；非字符串 -> ValueError。
    """
    raise NotImplementedError("实现注入检测")
