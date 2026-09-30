"""MCP HTTP resource server 的授权内核；token 验证器由企业 IdP 注入。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AccessClaims:
    """令牌声明（由 TokenVerifier 验证签名后得到）：主体、目标资源 audience、scope 和租户。"""

    subject: str
    audience: frozenset[str]
    scopes: frozenset[str]
    tenant_id: str


class TokenVerifier(Protocol):
    """令牌验证接口，由企业 IdP 对接实现；本章不验证签名。"""

    def verify(self, bearer_token: str) -> AccessClaims: ...


@dataclass(frozen=True)
class McpToolPolicy:
    """工具的授权策略：需要的 scope，以及是否要人工审批。"""

    name: str
    required_scope: str
    requires_human_approval: bool = False


class McpAuthorizationError(PermissionError):
    pass


def authorize_tool(
    claims: AccessClaims,
    policy: McpToolPolicy,
    *,
    resource_audience: str,
    approved: bool = False,
) -> None:
    """依次检查：令牌是否签发给本资源（audience）、是否有工具所需的 scope、高风险工具是否已审批。
    任一项不满足就抛 McpAuthorizationError。
    """
    if resource_audience not in claims.audience:
        raise McpAuthorizationError("token 未签发给当前 MCP resource")
    if policy.required_scope not in claims.scopes:
        raise McpAuthorizationError("token 缺少调用该工具的 scope")
    if policy.requires_human_approval and not approved:
        raise McpAuthorizationError("高风险工具必须经过用户或人工审批")


class McpResourceServer:
    def __init__(self, verifier: TokenVerifier, *, audience: str) -> None:
        self.verifier = verifier
        self.audience = audience

    def authorize(self, bearer_token: str, policy: McpToolPolicy, *, approved: bool = False) -> AccessClaims:
        """验证令牌后执行 authorize_tool，返回声明；租户和身份以声明为准，不信任请求参数。"""
        claims = self.verifier.verify(bearer_token)
        authorize_tool(claims, policy, resource_audience=self.audience, approved=approved)
        return claims
