# 8.6 Agent 自动化测试：约束动作而不只看答案

[全书目录](../../README.md) · [上一章 8.5](../8.5-judge-calibration/README.md) · [下一章 8.7](../8.7-api-sse-e2e/README.md)

- **目标**：Agent 的行为轨迹是产品输出，必须测试工具、审批和步数。
- **前置**：8.5（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.6-agent-trajectory-testing`，进入 `.build/quality/8.6-agent-trajectory-testing/ai-testing` 后运行 `python -m pytest -q`

## 问题

在客服业务中，查订单和发起退款有不同权限。即使最终回复正确，中间工具越权、缺审批或重复执行也必须算失败。

## 概念

TraceStep 描述一步动作；TrajectoryPolicy 描述允许的工具、最大步数和需要审批的写工具；`validate_trajectory` 把这些约束变成可运行的规则。`TraceStep.arguments` 只做记录，本章代码不校验参数。

## 流程

1. 采集或构造轨迹（`TraceStep` 列表）。
2. 检查总步数不超过 `max_steps`，步骤编号从 1 连续递增。
3. 逐步检查：`tool` 动作的工具必须在白名单内，写工具必须已审批；动作名只能是 tool、retrieve、respond、refuse。
4. 返回全部违规描述，空列表表示合规；不会在第一处违规就停止。

```text
Agent trace → TrajectoryPolicy → 工具/审批/步数检查 → 违规列表（空 = 合规）
```

## 衔接与新增

章节 8.5 校准回答质量；章节 8.6 把旗舰后端（7.8 / step2）里的订单查询、工单和检索分支抽象成可审计的轨迹策略。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/trajectory.py` | 新增 | 工具白名单、写操作审批、步骤预算和动作校验 |
| `tests/test_trajectory.py` | 新增 | 验证只读成功、越权和超步数 |

## 代码导读

trajectory.py 先读 TraceStep 与 TrajectoryPolicy，再读 validate_trajectory，确认每项规则如何从事件字段获得证据。

实现文件：

- [trajectory.py](src/ai_testing/trajectory.py)

## 练习

构造相同答案的安全轨迹和越权轨迹，比较判定；再让写动作缺少审批，写出应在哪个边界停止。选做：让策略按工具校验 `arguments` 里的必填参数，并补一个测试。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.6-agent-trajectory-testing
cd .build/quality/8.6-agent-trajectory-testing/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

当前工具库校验合成事件，真实业务还需保证采集事件可靠且审批对应具体动作。

轨迹合法不代表答案正确；它只证明 Agent 没有违反工具和控制流边界。
