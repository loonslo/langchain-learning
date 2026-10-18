"""L9 扩展 · MCP 授权 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/mcp_auth.py。实现 authorize_tool，然后运行：

    python chapters/part10-mcp-a2a-optional/10.1-mcp-auth-approval/gate/gate_check.py
"""

from __future__ import annotations


class McpAuthorizationError(PermissionError):
    pass


def authorize_tool(claims: dict, policy: dict, *, resource_audience: str, approved: bool = False) -> None:
    """依次检查 audience、scope、高风险审批；失败抛 McpAuthorizationError。

    claims: subject/audience(list)/scopes(list)/tenant_id
    policy: name/required_scope/requires_human_approval
    """
    raise NotImplementedError("实现 MCP 授权")
