"""vLLM 启动配置：生成参数列表而非可注入的 shell 字符串。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VllmServeSpec:
    model: str
    host: str = "0.0.0.0"
    port: int = 8000
    tensor_parallel_size: int = 1
    max_model_len: int = 8192
    gpu_memory_utilization: float = 0.9
    api_key_env: str = "VLLM_API_KEY"


def validate_vllm_spec(spec: VllmServeSpec) -> tuple[str, ...]:
    errors: list[str] = []
    if not spec.model.strip() or any(char.isspace() for char in spec.model):
        errors.append("model 必须是非空模型 ID 或本地路径，且不能含空白")
    if not 1 <= spec.port <= 65535:
        errors.append("port 必须在 1–65535")
    if not 1 <= spec.tensor_parallel_size <= 16:
        errors.append("tensor_parallel_size 必须在 1–16")
    if not 512 <= spec.max_model_len <= 262_144:
        errors.append("max_model_len 必须在 512–262144")
    if not 0.5 <= spec.gpu_memory_utilization <= 0.98:
        errors.append("gpu_memory_utilization 必须在 0.5–0.98")
    if not spec.api_key_env or "=" in spec.api_key_env:
        errors.append("api_key_env 必须引用环境变量名")
    return tuple(errors)


def vllm_command(spec: VllmServeSpec) -> tuple[str, ...]:
    errors = validate_vllm_spec(spec)
    if errors:
        raise ValueError("；".join(errors))
    return (
        "vllm", "serve", spec.model,
        "--host", spec.host,
        "--port", str(spec.port),
        "--tensor-parallel-size", str(spec.tensor_parallel_size),
        "--max-model-len", str(spec.max_model_len),
        "--gpu-memory-utilization", str(spec.gpu_memory_utilization),
        "--api-key", f"${{{spec.api_key_env}}}",
    )
