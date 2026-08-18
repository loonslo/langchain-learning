# Day102 · MCP HTTP 鉴权、最小权限与写工具审批

本地 stdio MCP 可以从环境读取凭据；企业 HTTP MCP 需要把受保护资源、token audience、
scope、用户同意和审计放到协议边界。今天不伪造 OAuth IdP，而是实现 MCP resource server
必须执行的授权策略。

## 今日交付

- `mcp_auth.py`：token claims 校验、工具 scope 与高风险工具审批规则。
- `tests/test_mcp_auth.py`：验证错误 audience、缺 scope、写操作未审批都会被拒绝。

## 今日边界

真正的 OAuth issuer、JWKS key rotation 和企业 SSO 是外部身份平台职责。MCP Server 不能
信任客户端传来的 user_id，也不能把 access token 转发给不相关的下游工具。
