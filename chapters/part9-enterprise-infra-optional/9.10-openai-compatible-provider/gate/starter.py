"""L5.8 扩展 · OpenAI 兼容配置 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/providers.py。实现下面两个函数，然后运行：

    python chapters/part9-enterprise-infra-optional/9.10-openai-compatible-provider/gate/gate_check.py
"""

from __future__ import annotations


def chat_completions_url(base_url: str) -> str:
    """拼接 base_url（去末尾 /）+ "/chat/completions"；非字符串/空 -> ValueError。"""
    raise NotImplementedError("实现 URL 拼接")


def validate_provider(provider: dict) -> tuple[str, ...]:
    """只校验配置形状，不发请求；返回错误列表（空=通过）。

    provider 字段：name/base_url/model/api_key_env/app_env。
    校验：
    - base_url 是 http(s) 完整 URL；
    - path 必须以 /v1 结束；
    - model 非空；
    - api_key_env 是环境变量名（非空、不含 "="）；
    - app_env=production 时必须 https。
    """
    raise NotImplementedError("实现配置校验")
