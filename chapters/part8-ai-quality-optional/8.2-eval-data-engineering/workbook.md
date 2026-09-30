# 章节 8.2 工作簿 · 评测集与测试数据工程

## 0. 变更闭环

| 文件 | 状态 | 它接到哪个旧能力 |
|---|---|---|
| `src/ai_testing/dataset.py` | 新增 | 接收 章节 8.1 风险场景，提供统一 EvalCase |
| `tests/test_dataset.py` | 新增 | 保护 schema、版本和坏数据路径 |

## 1. 思考

1. 为什么“退款”问题必须同时保存 expected_keywords 和 expected_sources？
2. 拒答用例为什么不能强制填写答案关键词？
3. 标签切片如何支持 smoke、regression、security 三层运行？

## 2. 验收

- [ ] JSON 往返后 tuple 字段语义不变。
- [ ] 坏用例能够在运行模型前被发现。
- [ ] 重复 ID 失败关闭。

## 3. 本章结论

评测集是测试输入的单一来源；业务代码、评测器和 CI 不应各自维护一份问题列表。
