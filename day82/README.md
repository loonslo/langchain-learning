# Day82 · Mock、契约与不变量测试

> 今天解决：Mock 测试都通过了，但真实 API 字段变了，或业务规则被悄悄破坏。
>
> 第一性原则：替身验证行为，契约和不变量验证边界。

## 与 Day81 的文件衔接

Day81 产出结构化评测输入；Day82 给 Day78 `/chat` 响应建立稳定契约，后续 RAG 评测和浏览器 E2E 都可以复用。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/contracts.py` | 新增 | 校验字段结构与拒答/工单不变量 |
| `tests/test_contracts.py` | 新增 | 验证正常、坏结构和业务冲突 |

## 真实调用链

```text
Day78 ChatResponse → validate_chat_response → assert_invariants → 测试结果
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 82
cd .build/day82/ai-testing
python -m pytest -q
```

## 今日边界

契约测试不能证明模型回答正确；它只保证接口形状和关键业务不变量不会被 Mock 掩盖。
