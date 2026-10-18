"""L5.6 pytest 回归 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
rag_regression.py。实现下面四个函数，然后运行：

    python chapters/part5-production/5.8-pytest-regression/gate/gate_check.py
"""

from __future__ import annotations

REFUSE_HINTS = ["没有提到", "未提到", "未提及", "我不知道", "无法回答", "文档中没有"]


def normalize(text: str) -> str:
    """NFKC 归一化 + 小写 + 去所有空白；非字符串 -> ValueError。"""
    raise NotImplementedError("实现归一化")


def refused(answer: str) -> bool:
    """归一化后出现任一拒答提示词 -> True。"""
    raise NotImplementedError("实现拒答判断")


def missing_keyword(answer: str, groups: list) -> str | None:
    """返回第一个未覆盖的关键词组（组内任选其一即覆盖）；全覆盖 -> None。

    groups 元素可以是字符串或字符串列表；空组 -> ValueError。
    """
    raise NotImplementedError("实现关键词检查")


def merge_cases(base: list[dict], extra: list[dict]) -> list[dict]:
    """按 id 合并，extra 覆盖同 id 的 base；保持 base 顺序，新增追加。"""
    raise NotImplementedError("实现用例合并")


def summarize(results: list[dict]) -> dict:
    """汇总 total/passed/failed/skipped；空列表全 0。"""
    raise NotImplementedError("实现结果汇总")
