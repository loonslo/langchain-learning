"""L9 扩展 · A2A 任务状态机 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/a2a.py。实现 InMemoryTaskStore，然后运行：

    python chapters/part10-mcp-a2a-optional/10.2-a2a-agent-card-task/gate/gate_check.py
"""

from __future__ import annotations

TERMINAL = {"completed", "canceled", "failed", "rejected"}
ALLOWED = {
    "submitted": {"working", "canceled", "rejected", "auth-required"},
    "working": {"input-required", "auth-required", "completed", "canceled", "failed"},
    "input-required": {"working", "canceled", "failed"},
    "auth-required": {"working", "canceled", "failed"},
}


class TaskNotFound(KeyError):
    pass


class TaskTransitionError(ValueError):
    pass


class InMemoryTaskStore:
    def submit(self, *, message_id: str, message: dict, context_id: str | None = None) -> dict:
        """创建任务；同一 message_id 重复提交返回已有任务；空 message_id -> ValueError。"""
        raise NotImplementedError("实现提交")

    def get(self, task_id: str) -> dict:
        """不存在 -> TaskNotFound。"""
        raise NotImplementedError("实现读取")

    def transition(self, task_id: str, state: str, status_message: str = "") -> dict:
        """按 ALLOWED 迁移；终态/非法迁移 -> TaskTransitionError。"""
        raise NotImplementedError("实现状态迁移")
