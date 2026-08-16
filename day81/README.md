# Day81 · 评测集与测试数据工程

> 今天解决：测试写了很多，但输入和预期结果没有版本、标签和校验。
>
> 第一性原则：评测数据本身也是产品资产，必须可校验、可回放、可版本化。

## 与 Day80 的文件衔接

Day80 用风险矩阵决定优先级；Day81 把高风险场景写成结构化 `EvalCase`，后续 RAG、Judge 和 CI 都消费同一份数据。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/dataset.py` | 新增 | 用例 schema、校验、标签切片和 JSON 持久化 |
| `tests/test_dataset.py` | 新增 | 验证回放、版本和坏数据失败路径 |

## 真实调用链

```text
RiskMatrix → EvalDataset → validate → tag slice → RAG/Judge/CI
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 81
cd .build/day81/ai-testing
python -m pytest -q
```

## 今日边界

数据集结构正确不代表参考答案正确；参考答案仍需要人工审查和后续 Judge 校准。
