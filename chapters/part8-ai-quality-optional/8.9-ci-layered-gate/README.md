# 8.9 CI 分层门禁：结果缺失也不能默认为通过

[全书目录](../../README.md) · [上一章 8.8](../8.8-security-resilience-perf/README.md) · [下一章 8.10](../8.10-production-feedback-loop/README.md)

- **目标**：质量门必须失败关闭，flaky 必须被识别而不是被静默重跑掩盖。
- **前置**：8.8（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.9-ci-layered-gate`，进入 `.build/quality/8.9-ci-layered-gate/ai-testing` 后运行 `python -m pytest -q`

## 问题

各类测试各自生成报告，发布流程却没有统一答案。我们把单元、契约、RAG、安全和性能结果组织为同一判定，并显式处理缺层与不稳定测试。

## 概念

`LayerResult` 描述一层证据（层名、是否通过、是否必需）；`GateReport` 汇总判定；flaky 指同一测试的历史结果时好时坏。声明为必需的层没有报告时按缺失处理并阻断；反复重跑直到变绿不能替代原因分析。

## 流程

1. 收集各层结果。
2. `required_layers` 声明的层必须都有结果，缺的记入 `missing_layers`。
3. 必需层必须通过；可选层失败只记录。
4. 历史结果里既有成功又有失败的测试记为 flaky。
5. `evaluate_gate` 返回 `GateReport`：是否放行，以及失败层、缺失层和 flaky 测试。

```text
pytest / RAG / security / SLO → LayerResult → evaluate_gate → CI exit decision
```

## 衔接与新增

章节 8.8 产出安全、重试和 SLO 结果；章节 8.9 将 unit、contract、RAG eval、安全和性能分层汇总，作为发布前单一判定。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/ci_gate.py` | 新增 | 分层结果、失败关闭和 flaky 检测 |
| `tests/test_ci_gate.py` | 新增 | 验证必需层失败、缺层、可选层和偶发失败 |

## 代码导读

ci_gate.py 先读层和报告的数据类型，再读 `flaky_tests` 与 `evaluate_gate`，关注缺层为何算失败。

实现文件：

- [ci_gate.py](src/ai_testing/ci_gate.py)

## 练习

传入 `required_layers=("unit", "rag-eval")` 但只给出 unit 的结果，预测门禁结论；把同一测试的成功失败记录混合，说明不稳定结果为何需要单独处理。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.9-ci-layered-gate
cd .build/quality/8.9-ci-layered-gate/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

门禁可信度取决于输入证据真实、指标口径稳定和 CI 确实执行；本章不是已发布服务的证明。

门禁只能判断提交是否满足既定标准，不能替代测试集设计、人工复核和线上监控。
