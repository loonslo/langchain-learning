"""L4.6 扩展 · 检查点与上下文 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
checkpoint_context.py。实现下面两类接口，然后运行：

    python chapters/part4-agents-langgraph/4.10-checkpoint-context/gate/gate_check.py
"""

from __future__ import annotations


class CheckpointStore:
    """按 thread_id 保存/读取 state 快照；内存实现。"""

    def save(self, thread_id: str, state: dict) -> None:
        """保存副本；thread_id 为空 -> ValueError。"""
        raise NotImplementedError("实现保存")

    def load(self, thread_id: str) -> dict | None:
        """读取副本；不存在 -> None。"""
        raise NotImplementedError("实现加载")

    def clear(self, thread_id: str) -> None:
        """删除指定会话；不存在不报错。"""
        raise NotImplementedError("实现清除")


def trim_history(messages: list[dict], max_items: int, keep_system: bool = True) -> list[dict]:
    """按条数裁剪上下文。

    - max_items < 1 -> ValueError；
    - keep_system=True 且首条 role=system -> 保留它 + 最近 max_items-1 条；
    - 否则保留最近 max_items 条；
    - 不修改输入；max_items 大于长度时返回全部。
    """
    raise NotImplementedError("实现上下文裁剪")
