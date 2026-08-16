# Day85 · Agent 自动化测试

> 今天解决：Agent 最后答对了，但中间调用了越权工具或执行了过多步骤。
>
> 第一性原则：Agent 的行为轨迹是产品输出，必须测试工具、参数、审批和步数。

## 与 Day84 的文件衔接

Day84 校准回答质量；Day85 把 Day78 的订单工具、工单和检索分支抽象成可审计的轨迹策略。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/trajectory.py` | 新增 | 工具白名单、写操作审批、步骤预算和动作校验 |
| `tests/test_trajectory.py` | 新增 | 验证只读成功、越权和超步数 |

## 真实调用链

```text
Agent trace → TrajectoryPolicy → tool/approval/step checks → pass or fail
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 85
cd .build/day85/ai-testing
python -m pytest -q
```

## 今日边界

轨迹合法不代表答案正确；它只证明 Agent 没有违反工具和控制流边界。
