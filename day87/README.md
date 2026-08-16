# Day87 · 安全、韧性与性能

> 今天解决：接口会重试但可能无限重试，输入能进来但没有边界，性能也没有 SLO。
>
> 第一性原则：安全边界、故障恢复和性能预算必须一起测试。

## 与 Day86 的文件衔接

Day86 验证 HTTP 连接点；Day87 为这些连接点补充输入校验、有限重试、退避和 p95 SLO，避免“能通”被误认为“可靠”。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/resilience.py` | 新增 | 输入边界、重试预算、百分位延迟和 SLO 判定 |
| `tests/test_resilience.py` | 新增 | 验证暂时失败恢复、坏输入和性能门 |

## 真实调用链

```text
HTTP input → validate_input → bounded retry → latency/error samples → SLO gate
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 87
cd .build/day87/ai-testing
python -m pytest -q
```

## 今日边界

离线样本只能验证判定算法；真实吞吐、并发和上游限流仍需要受控压测环境。
