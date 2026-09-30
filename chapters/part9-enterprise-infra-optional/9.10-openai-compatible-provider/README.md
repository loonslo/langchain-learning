# 9.10 兼容模型接口：配置相同也要核对能力

[全书目录](../../README.md) · [上一章 9.9](../9.9-compose-linux-ops/README.md) · [下一章 9.11](../9.11-vllm-gpu/README.md)

- **目标**：让业务代码只依赖 `base_url + model + 凭据引用`，不绑定具体厂商 SDK：云 API、Ollama、vLLM 都通过同一份最小 OpenAI 兼容配置接入。
- **前置**：9.9（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.10-openai-compatible-provider`，进入 `.build/enterprise/9.10-openai-compatible-provider/enterprise-support` 后运行 `python -m pytest -q`

## 问题

云 API 与本机推理可能提供类似接口，业务代码可以减少厂商耦合。但兼容地址格式不代表工具调用、流式或结构化输出行为全部一致。

## 概念

Provider 保存端点、模型和凭据引用；兼容接口统一请求形状；能力验证确认应用实际需要的特性。

## 流程

1. 构造 OpenAICompatibleProvider。
2. validate_provider 检查端点和凭据引用。
3. 业务层消费配置。
4. 对所需能力做独立契约测试。

## 本章交付

- `providers.py`：云模型 / 自托管模型共用的端点与配置校验。
- `tests/test_providers.py`：验证 `/v1` 边界、密钥只引用环境变量和开发/生产 URL 约束。

## 代码导读

providers.py 先读配置字段，再读校验规则，观察开发和生产配置范围的区别。

实现文件：

- [providers.py](src/enterprise_support/providers.py)

## 练习

为云端和本机端点各写一份无真实凭据的配置，列出还要验证的流式、工具与输出行为。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.10-openai-compatible-provider
cd .build/enterprise/9.10-openai-compatible-provider/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

本章配置校验不发起模型请求；真实端点的兼容性、质量和认证尚未验收。

OpenAI 兼容只解决调用接口，不保证 chat template、工具调用、JSON schema、embedding 或 token 统计语义完全相同。替换推理框架后必须回放评测集（7.1 / step3 的离线评测，以及 8.10 导出的回归样本）。
