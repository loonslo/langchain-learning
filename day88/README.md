# Day88 · CI 分层门禁与 flaky 防护

> 今天解决：测试结果都在报告里，但 CI 不知道什么时候应该阻止合并；偶发失败又污染了判断。
>
> 第一性原则：质量门必须失败关闭，flaky 必须被识别而不是被静默重跑掩盖。

## 与 Day87 的文件衔接

Day87 产出安全、重试和 SLO 结果；Day88 将 unit、contract、RAG eval、安全和性能分层汇总，作为发布前单一判定。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/ci_gate.py` | 新增 | 分层结果、失败关闭和 flaky 检测 |
| `tests/test_ci_gate.py` | 新增 | 验证必需层、可选层和偶发失败 |

## 真实调用链

```text
pytest / RAG / security / SLO → LayerResult → evaluate_gate → CI exit decision
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 88
cd .build/day88/ai-testing
python -m pytest -q
```

## 今日边界

门禁只能判断提交是否满足既定标准，不能替代测试集设计、人工复核和线上监控。
