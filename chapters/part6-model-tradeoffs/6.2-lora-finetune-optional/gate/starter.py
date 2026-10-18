"""L6.2 LoRA 质量门禁 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
lora_finetune.py。实现下面两个函数，然后运行：

    python chapters/part6-model-tradeoffs/6.2-lora-finetune-optional/gate/gate_check.py
"""

from __future__ import annotations


def quality_gate(base_score: float, adapter_score: float, *, min_adapter: float = 0.75,
                 min_gain: float = 0.25) -> dict:
    """比较基座与适配器的 held-out 得分。

    返回 {"passed": bool, "reasons": list[str]}：
    - adapter_score >= min_adapter；
    - adapter_score - base_score >= min_gain；
    - 得分必须在 [0,1]，否则 ValueError。
    """
    raise NotImplementedError("实现质量门禁")


def validate_training_config(lr: float, epochs: int, rank: int, alpha: int) -> tuple[str, ...]:
    """校验 LoRA 超参，返回错误列表。

    lr 在 1e-4–2e-4；epochs >=1；rank >=1；alpha >=1；否则记录错误。
    """
    raise NotImplementedError("实现超参校验")
