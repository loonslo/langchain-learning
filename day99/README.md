# Day99 · 开源模型接入：OpenAI 兼容 Provider 契约

业务代码不应该知道模型来自云 API、Ollama 还是 vLLM。今天先定义最小 OpenAI 兼容配置，
让客服工作流只依赖 `base_url + model + 凭据引用`，而非绑定具体厂商 SDK。

## 今日交付

- `providers.py`：云模型 / 自托管模型共用的端点与配置校验。
- `tests/test_providers.py`：验证 `/v1` 边界、密钥只引用环境变量和开发/生产 URL 约束。

## 今日边界

OpenAI 兼容只解决调用接口，不保证 chat template、工具调用、JSON schema、embedding 或
token 统计语义完全相同。替换推理框架后必须回放 Day53/Day89 的评测集。
