import pytest

from src.enterprise_support.mcp_auth import AccessClaims, McpAuthorizationError, McpToolPolicy, authorize_tool


CLAIMS = AccessClaims("u1", frozenset({"https://mcp.example/orders"}), frozenset({"orders.read"}), "shop-a")


def test_mcp_tool_requires_resource_bound_audience_and_scope():
    policy = McpToolPolicy("get_order", "orders.read")
    authorize_tool(CLAIMS, policy, resource_audience="https://mcp.example/orders")
    with pytest.raises(McpAuthorizationError):
        authorize_tool(CLAIMS, policy, resource_audience="https://mcp.example/payments")


def test_high_risk_tool_requires_explicit_approval_even_with_scope():
    policy = McpToolPolicy("cancel_order", "orders.read", requires_human_approval=True)
    with pytest.raises(McpAuthorizationError):
        authorize_tool(CLAIMS, policy, resource_audience="https://mcp.example/orders")
