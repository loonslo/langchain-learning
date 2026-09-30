import pytest

from src.enterprise_support.vllm import VllmServeSpec, validate_vllm_spec, vllm_command


def test_vllm_command_is_an_argument_list_and_never_embeds_secret_value():
    command = vllm_command(VllmServeSpec("Qwen/Qwen3-8B"))
    assert command[:3] == ("vllm", "serve", "Qwen/Qwen3-8B")
    assert "${VLLM_API_KEY}" in command


def test_vllm_rejects_unsafe_or_impossible_resource_values():
    errors = validate_vllm_spec(VllmServeSpec("", tensor_parallel_size=0, gpu_memory_utilization=1.2))
    assert len(errors) == 3
    with pytest.raises(ValueError):
        vllm_command(VllmServeSpec("model with space"))
