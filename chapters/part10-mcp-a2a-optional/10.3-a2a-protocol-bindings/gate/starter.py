"""L10 扩展 · A2A JSON-RPC 绑定 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/a2a_api.py。实现 A2AApplication.dispatch，然后运行：

    python chapters/part10-mcp-a2a-optional/10.3-a2a-protocol-bindings/gate/gate_check.py
"""

from __future__ import annotations


class TaskNotFound(KeyError):
    pass


class A2AApplication:
    def send(self, params: dict) -> dict:
        raise NotImplementedError

    def get(self, task_id: str) -> dict:
        raise NotImplementedError

    def cancel(self, task_id: str) -> dict:
        raise NotImplementedError

    def dispatch(self, payload: dict) -> dict:
        """处理 JSON-RPC 请求。

        - jsonrpc != "2.0" 或缺 method -> -32600；
        - params 非对象 -> -32602；
        - 未知 method -> -32601；
        - TaskNotFound -> -32001；KeyError -> -32602；ValueError -> -32602；
        - 成功 -> {"jsonrpc":"2.0","id":..., "result": ...}。
        """
        raise NotImplementedError("实现 JSON-RPC 分发")
