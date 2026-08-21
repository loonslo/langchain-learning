# Day83 · RAG 自动化测试

> 今天解决：只看最终答案，不知道是没召回、排错了，还是引用错了。
>
> 第一性原则：RAG 必须把召回、排序和引用分层测量。

## 与 Day82 的文件衔接

Day82 保证响应契约；Day83 消费 Day81 的评测用例，独立评估 Day78 混合检索返回的来源列表，不需要调用真实 LLM。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/rag_eval.py` | 新增 | Recall@k、Precision@k、MRR 和引用覆盖率 |
| `tests/test_rag_eval.py` | 新增 | 验证命中、误召回、排序和空结果 |

## 真实调用链

```text
EvalDataset → Day78 Retriever/ChatResponse → RetrievalCase → RAG metrics
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 83
cd .build/day83/ai-testing
python -m pytest -q
```

## 今日边界

离线来源指标不能证明自然语言回答忠实；生成质量和 Judge 校准会在后续 Day84 处理。
