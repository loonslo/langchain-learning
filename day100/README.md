# Day100 · vLLM 服务、GPU 配置与容器 Profile

Ollama 适合本机体验；企业自托管推理需要明确模型、GPU、上下文长度、并行度、认证和健康
检查。今天用结构化配置生成 `vllm serve` 参数，并把 GPU 服务放到可选 Compose profile。

## 今日交付

- `vllm.py`：安全构造 `vllm serve` 参数，避免 shell 字符串拼接。
- `compose.vllm.yaml`：只在 `--profile gpu` 时启动的 GPU 推理服务。
- `tests/test_vllm.py`：验证显存利用率、并行度和 API key 配置。

## 今日边界

命令能启动不代表容量足够。模型是否支持工具调用、结构化输出及中文 chat template，要由
Day101 基准和 RAG/客服回归集证明。
