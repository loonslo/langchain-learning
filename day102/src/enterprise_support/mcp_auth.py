"""MCP HTTP resource server 的授权内核；token 验证器由企业 IdP 注入。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AccessClaims:
    subject: str
    audience: frozenset[str]
    scopes: frozenset[str]
    tenant_id: str


class TokenVerifier(Protocol):
    def verify(self, bearer_token: str) -> AccessClaims: ...


@dataclass(frozen=True)
class McpToolPolicy:
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
        claims = self.verifier.verify(bearer_token)
        authorize_tool(claims, policy, resource_audience=self.audience, approved=approved)
        return claims
