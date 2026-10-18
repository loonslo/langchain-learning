"""L1.4 上下文与记忆 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
context_memory.py。实现下面两个部分，然后运行：

    python chapters/part1-foundations/1.4-context-memory/gate/gate_check.py
"""


class MemoryError(ValueError):
    """会话或消息不合法。"""


class SessionMemory:
    """按 session_id 隔离的内存历史。"""

    def __init__(self) -> None:
        self._data: dict[str, list[dict]] = {}

    def add(self, session_id: str, role: str, content: str) -> None:
        """追加一条消息。

        要求：
        - session_id 非空；role 只能是 system/user/assistant；content 是字符串；
        - 不合法抛 MemoryError。
        """
        raise NotImplementedError("实现会话追加")

    def get(self, session_id: str) -> list[dict]:
        """返回该会话的消息副本；没有会话返回 []。"""
        raise NotImplementedError("实现会话读取")

    def clear(self, session_id: str) -> None:
        """清空该会话；不存在时静默返回。"""
        raise NotImplementedError("实现会话清空")


def trim_history(messages: list[dict], max_chars: int) -> list[dict]:
    """按字符预算裁剪历史。

    要求：
    - max_chars < 0 抛 ValueError；
    - 空列表返回 []；
    - system 消息永远保留，按原顺序放在最前（可以超预算）；
    - 非 system 消息从最新往前选，遇到第一条放不下的就停止；
    - 不截断单条消息，不修改输入，输出保持时间顺序；
    - 消息缺 role/content 或 content 不是字符串，抛 ValueError。
    """
    raise NotImplementedError("实现历史裁剪")
