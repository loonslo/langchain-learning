# Day90 · few-shot 意图契约

今天不让模型自由输出“我觉得这是退款问题”。客服分流首先要有有限的意图枚举、few-shot
示例和严格校验：模型不认识的类别必须回到 `unknown`，而不是猜一个业务动作。

## 今日交付

- `intent.py`：few-shot prompt 与模型输出的 JSON 契约校验。
- `contracts.py`：后续工作流共用的意图、槽位和响应类型。
- `tests/test_intent.py`：验证合法意图、未知意图和字段缺失都被正确处理。

## 验收

```bash
python tools/materialize_enterprise_day.py 90
cd .build/day90/enterprise-support
python -m pytest -q
```

## 边界

few-shot 是改善分类一致性的上下文示例，不是训练，也不能替代评测集。
