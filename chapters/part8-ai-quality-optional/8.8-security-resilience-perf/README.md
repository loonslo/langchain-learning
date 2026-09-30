# 8.8 安全、韧性与性能：一起验证服务预算

[全书目录](../../README.md) · [上一章 8.7](../8.7-api-sse-e2e/README.md) · [下一章 8.9](../8.9-ci-layered-gate/README.md)

- **目标**：安全边界、故障恢复和性能预算必须一起测试。
- **前置**：8.7（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.8-security-resilience-perf`，进入 `.build/quality/8.8-security-resilience-perf/ai-testing` 后运行 `python -m pytest -q`

## 问题

服务有了重试后可能更稳，也可能更慢。输入边界、重试策略和延迟目标需要放在一起检查，才能判断用户是否在可接受时间内得到可靠结果。

## 概念

RetryPolicy 规定有限重试（线性退避）；输入校验只拦截空输入、超长和控制字符，不识别提示注入（见 4.12、7.5）；SLO 是服务目标；p95 是 95% 的请求都不超过的延迟。

## 流程

1. 校验输入。
2. 模拟临时或永久错误。
3. 执行有限退避。
4. 收集延迟样本。
5. 计算分位数并检查 SLO。

```text
HTTP input → validate_input → bounded retry → latency/error samples → SLO gate
```

## 衔接与新增

章节 8.7 验证 HTTP 连接点；章节 8.8 为这些连接点补充输入校验、有限重试、退避和 p95 SLO，避免“能通”被误认为“可靠”。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/resilience.py` | 新增 | 输入边界、重试预算、百分位延迟和 SLO 判定 |
| `tests/test_resilience.py` | 新增 | 验证暂时失败恢复、坏输入、性能门和小样本分位数 |

## 代码导读

resilience.py 先读 RetryPolicy 与 call_with_retry，再读 validate_input、percentile 和 meets_slo，核对失败和边界样本。

实现文件：

- [resilience.py](src/ai_testing/resilience.py)

## 练习

使用不实际等待的测试时钟模拟两次失败后成功，检查次数；加入一条极慢请求，观察平均值与 p95 的区别。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.8-security-resilience-perf
cd .build/quality/8.8-security-resilience-perf/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

离线样本只验证计算口径和判定算法；真实并发、吞吐和上游限流需要在受控的压测环境里另行测量。
