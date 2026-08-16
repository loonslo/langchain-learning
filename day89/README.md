# Day89 · 线上质量闭环

> 今天解决：用户点踩被记录了，但没有可靠地回到测试集，质量问题无法形成改进闭环。
>
> 第一性原则：反馈先审查，再进入回归；线上数据不能自动污染生产行为。

## 与 Day88 的文件衔接

Day88 的 CI 门禁可以阻止已知回归；Day89 接收 Day79/Day78 的负反馈，把 bad case 放进人工审查队列，审核通过后生成回归 fixture。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `PROJECT_README.md` | 新增 | 总结 Day80–89 的专项闭环和边界 |
| `src/ai_testing/feedback_loop.py` | 新增 | 去重、审查、批准和回归集导出 |
| `tests/test_feedback_loop.py` | 新增 | 验证负反馈队列和审核后导出 |

## 真实调用链

```text
Day79 feedback → BadCase → review_queue → human approve → regression.json → Day88 CI gate
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 89
cd .build/day89/ai-testing
python -m pytest -q
```

## 今日边界

导出回归用例不等于已经修复问题；下一轮必须重新运行评测、确认指标改善，再把结果纳入发布证据。
