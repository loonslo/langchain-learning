# 8.4 RAG 分层测试：召回、排名和引用分别检查

[全书目录](../../README.md) · [上一章 8.3](../8.3-mock-contract-invariant/README.md) · [下一章 8.5](../8.5-judge-calibration/README.md)

- **目标**：RAG 必须把召回、排序和引用分层测量。
- **前置**：8.3（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.4-rag-layered-testing`，进入 `.build/quality/8.4-rag-layered-testing/ai-testing` 后运行 `python -m pytest -q`

## 问题

最终答案错时，不能只得到一盏红灯。分层指标帮助判断相关来源是否进候选、排名是否靠前，以及输出引用有没有覆盖或乱带资料。

## 概念

RetrievalCase 记录相关来源；RetrievalMetrics 描述检索表现。召回与排序指标关注不同性质，引用完整性还需要与答案事实联系。

## 流程

1. 读取带来源标识的案例。
2. 提供实际召回列表。
3. `evaluate_retrieval(cases, k)` 取前 k 个召回结果，计算 recall@k、precision@k、MRR 和引用覆盖率（口径见函数注释）。
4. 应拒答（没有相关来源）的样本单独评估：它们的 precision 和 MRR 恒为 0，混在一起会拉低平均值。

```text
EvalDataset → 旗舰后端的检索结果（7.8 / step2）→ RetrievalCase → RAG metrics
```

## 衔接与新增

章节 8.3 保证响应契约；章节 8.4 消费 8.2 的评测用例，独立评估旗舰后端（7.8 / step2）混合检索返回的来源列表，不调用真实 LLM。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/rag_eval.py` | 新增 | Recall@k、Precision@k、MRR 和引用覆盖率 |
| `tests/test_rag_eval.py` | 新增 | 验证命中、误召回、排序和空结果 |

## 代码导读

rag_eval.py 先读案例和指标字段，再读 evaluate_retrieval 与空集合处理，确认负例和缺结果的含义。

实现文件：

- [rag_eval.py](src/ai_testing/rag_eval.py)

## 练习

保持候选不变只调整顺序，预测哪些指标变化；再加入重复或无关来源，解释总候选数与质量的关系。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.4-rag-layered-testing
cd .build/quality/8.4-rag-layered-testing/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

本章用离线来源列表验证指标，不执行真实向量检索，也不能证明生成的答案忠实于证据；生成质量和 Judge 校准在 8.5 处理。
