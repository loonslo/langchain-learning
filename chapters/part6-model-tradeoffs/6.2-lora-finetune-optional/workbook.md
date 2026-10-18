# L5.10 扩展：LoRA 质量门禁 · Gate 记录

任务书见 [README](README.md)。先预测，再实现，最后填结果；通过 gate 之前不要打开 `lora_finetune.py`。

## Gate 结果

- 首次运行：x / 5
- FAIL 项与修正：待填写
- 最终：5 / 5
- `gate_report.json`：待填写

## 解释

1. 为什么不能只看 train loss？
2. 为什么适配器必须比基座明显更好？
3. LoRA 的 lr 为什么要比全参高一个量级？

## 未验证边界

- 不训练/不加载适配器。
- 真实 held-out 质量未验证。
