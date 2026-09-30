# 9.11 vLLM 选修：服务配置先于 GPU 实验

[全书目录](../../README.md) · [上一章 9.10](../9.10-openai-compatible-provider/README.md) · [下一章 9.12](../9.12-inference-benchmark/README.md)

- **目标**：用结构化配置生成 `vllm serve` 的参数列表（模型、GPU、上下文长度、并行度、认证），并把 GPU 服务放到可选的 Compose profile。
- **前置**：9.10（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.11-vllm-gpu`，进入 `.build/enterprise/9.11-vllm-gpu/enterprise-support` 后运行 `python -m pytest -q`

## 问题

准备自托管推理时，不应直接复制一个启动命令。模型、显存、上下文、并行和认证都要形成可审查配置，之后再运行和测量。

## 概念

VllmServeSpec 描述启动要求；参数列表避免拼接任意 shell 代码；GPU profile 将可选硬件服务与基本依赖分开。`vllm_command` 输出的密钥参数是 `${VLLM_API_KEY}` 占位符，交给 Compose 或 shell 展开；直接传给 `subprocess.run` 会把占位符当作密钥。容器内监听 `0.0.0.0`，宿主机端口只映射到 `127.0.0.1`。

## 流程

1. 整理模型与硬件要求。
2. validate_vllm_spec 检查配置。
3. vllm_command 生成参数。
4. 对照容器 profile 后在相应环境启动。

## 本章交付

- `vllm.py`：安全构造 `vllm serve` 参数，避免 shell 字符串拼接。
- `compose.vllm.yaml`：只在 `--profile gpu` 时启动的 GPU 推理服务。
- `tests/test_vllm.py`：验证显存利用率、并行度和 API key 配置。

## 代码导读

vllm.py 先读配置类型，再看验证和命令生成；compose.vllm.yaml 描述可选服务，需与实际硬件对照。

实现文件：

- [vllm.py](src/enterprise_support/vllm.py)

## 练习

只生成并审查参数，解释上下文长度与并行度为何影响资源；写下启动前必须确认的硬件和模型条件。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.11-vllm-gpu
cd .build/enterprise/9.11-vllm-gpu/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

本次不部署 GPU 服务，生成命令不代表模型能加载或吞吐达标。

命令能启动不代表容量足够。模型是否支持工具调用、结构化输出及中文 chat template，要由章节 9.12 基准和 RAG/客服回归集证明。
