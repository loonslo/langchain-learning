# 8.2 评测数据工程：数据也要有契约

[全书目录](../../README.md) · [上一章 8.1](../8.1-risk-modeling/README.md) · [下一章 8.3](../8.3-mock-contract-invariant/README.md)

- **目标**：评测数据本身也是产品资产，必须可校验、可回放、可版本化。
- **前置**：8.1（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.2-eval-data-engineering`，进入 `.build/quality/8.2-eval-data-engineering/ai-testing` 后运行 `python -m pytest -q`

## 问题

测试集从十条增长到上百条后，重复问题、缺字段和不正确来源会让分数失真。本章给评测数据建立结构、校验和版本思路。

## 概念

EvalCase 统一单条输入与预期；EvalDataset 管理集合。可回放需要稳定标识和明确数据范围，样本标签方便按风险分组检查。

## 流程

1. 定义样本字段。
2. 校验每条输入。
3. 检查集合中的标识和覆盖。
4. 将同一份数据提供给后续检索、评委与门禁。

```text
RiskMatrix → EvalDataset → validate → tag slice → RAG/Judge/CI
```

## 衔接与新增

章节 8.1 用风险矩阵决定优先级；章节 8.2 把高风险场景写成结构化 `EvalCase`，后续 RAG、Judge 和 CI 都消费同一份数据。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/dataset.py` | 新增 | 用例 schema、校验、标签切片和 JSON 持久化 |
| `tests/test_dataset.py` | 新增 | 验证回放、版本和坏数据失败路径 |

## 代码导读

dataset.py 按 EvalCase、EvalDataset 的顺序阅读，确认它拒绝哪些不合法数据，再对照测试样本。

实现文件：

- [dataset.py](src/ai_testing/dataset.py)

## 练习

加入重复标识和缺少预期的合成用例，预测错误位置；补充一条真实业务边界后说明它属于哪个风险标签。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.2-eval-data-engineering
cd .build/quality/8.2-eval-data-engineering/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

结构校验不能证明答案标注正确，仍需对照来源人工复核，线上数据进入集合前还应审查。

数据集结构正确不代表参考答案正确；参考答案仍需要人工审查和后续 Judge 校准。
