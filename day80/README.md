# Day80 · AI 测试策略与风险建模

> 今天解决：AI 项目测试很多，但不知道先测什么。
>
> 第一性原则：测试优先级必须由业务风险决定，而不是由模块数量决定。

## 与 Day79 的衔接

Day79 是浏览器前端对接；Day80 开始进入可选的 AI 自动化测试专项。测试对象仍是同一个 Day78 客服 Copilot，但测试工具独立放在 `ai_testing` 包中，不把测试逻辑混进业务代码。

## 今天新增

| 文件 | 作用 |
|---|---|
| `pyproject.toml` | 建立 Day80–89 专项的可还原 Python 基线 |
| `src/ai_testing/risk.py` | 风险登记、评分、分级和测试覆盖检查 |
| `tests/test_risk.py` | 验证风险排序、重复登记和覆盖缺口 |

## 真实调用链

```text
业务场景 → Risk(影响 × 发生可能性) → 优先级 → 测试覆盖缺口
```

## 运行

```bash
python tools/materialize_ai_testing_day.py 80
cd .build/day80/ai-testing
python -m pytest -q
```

## 今日边界

风险矩阵只能决定“先测什么”，不能证明功能已经正确；下一天会把风险中的业务场景转成可执行评测数据。
