# 10.1 MCP 授权与审批：工具连接后还要检查身份

[全书目录](../../README.md) · [上一章 9.12](../../part9-enterprise-infra-optional/9.12-inference-benchmark/README.md) · [下一章 10.2](../10.2-a2a-agent-card-task/README.md)

- **目标**：为企业 HTTP MCP 实现授权策略：受保护资源、token audience、scope、用户同意和审计（不实现 OAuth IdP，只实现 resource server 必须执行的策略）。
- **前置**：9.12（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 10.1-mcp-auth-approval`，进入 `.build/enterprise/10.1-mcp-auth-approval/enterprise-support` 后运行 `python -m pytest -q`

## 问题

连通远端工具之后，下一步是确认谁能调用什么。读取订单和提交退款需要不同范围，写工具还可能需要针对具体动作的审批。

## 概念

AccessClaims 描述可信令牌声明；audience 限制目标资源；scope 限制工具能力；审批约束高影响动作。解析声明与验证签名来源应由明确边界负责。

## 流程

1. 验证令牌并取得声明。
2. 核对目标与有效范围。
3. authorize_tool 检查工具策略。
4. 必要时确认审批。
5. 受控资源服务才执行工具。

## 本章交付

- `mcp_auth.py`：token claims 校验、工具 scope 与高风险工具审批规则。
- `tests/test_mcp_auth.py`：验证错误 audience、缺 scope、写操作未审批都会被拒绝。

## 代码导读

mcp_auth.py 先读 TokenVerifier 与 McpToolPolicy，再读 authorize_tool 和 McpResourceServer，关注拒绝在执行前发生。

实现文件：

- [mcp_auth.py](src/enterprise_support/mcp_auth.py)

## 练习

用离线声明分别模拟错误目标、缺范围和缺审批，核对每项拒绝原因，再写出正常读取的授权条件。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 10.1-mcp-auth-approval
cd .build/enterprise/10.1-mcp-auth-approval/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

示例不搭建真实 OAuth 身份提供方；离线声明测试不能代替真实令牌验签、同意与审计。

真正的 OAuth issuer、JWKS key rotation 和企业 SSO 是外部身份平台职责。MCP Server 不能信任客户端传来的 user_id，也不能把 access token 转发给不相关的下游工具。
