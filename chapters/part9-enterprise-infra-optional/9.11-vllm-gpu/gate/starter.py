"""L5.8 扩展 · vLLM 启动配置 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/vllm.py。实现下面两个函数，然后运行：

    python chapters/part9-enterprise-infra-optional/9.11-vllm-gpu/gate/gate_check.py
"""

from __future__ import annotations


def validate_vllm_spec(spec: dict) -> tuple[str, ...]:
    """返回配置错误（空元组=通过）。

    spec: model/host/port/tensor_parallel_size/max_model_len/
    gpu_memory_utilization/api_key_env。
    校验：model 非空且无空白；port 1–65535；tp 1–16；
    max_model_len 512–262144；gpu 0.5–0.98；api_key_env 非空且不含 "="。
    """
    raise NotImplementedError("实现 vLLM 配置校验")


def vllm_command(spec: dict) -> tuple[str, ...]:
    """返回 vllm serve 参数元组；不合法 -> ValueError；密钥只放 ${ENV} 占位符。"""
    raise NotImplementedError("实现命令生成")
