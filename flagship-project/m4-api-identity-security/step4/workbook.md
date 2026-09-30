# 里程碑 7.4 / step4 工作簿 · 增量知识同步

## 0. 先确认本步变更闭环

| 文件 | 状态 | 它接到哪个旧文件/入口 | 如果不接会发生什么 |
|---|---|---|---|
| `src/customer_support/sync.py` | 新增 | 待填写 | 待填写 |
| `tests/test_sync.py` | 新增 | 待填写 | 待填写 |
| `src/customer_support/api.py` | 修改旧文件 | 待填写 | 待填写 |
| `src/customer_support/runtime.py` | 修改旧文件 | 待填写 | 待填写 |
| `tests/test_api.py` | 修改旧文件 | 待填写 | 待填写 |

真实链路：`HTTP /knowledge/sync-plan → SyncingApplication → scan/plan → knowledge_path`

## 1. 从 里程碑 7.4 / step3 继续

1. 前一步暴露的真实问题是什么？全量重建昂贵且删除资料会残留（请用自己的话重写）
2. 本节哪些旧文件被修改？为什么只新增模块还不够？待填写。
3. 哪些继承文件虽然未改，却仍参与本节的调用链？待填写。

## 2. 运行与证据

1. 哪条测试证明新能力已从正式入口可达？待填写。
2. 哪条测试保护失败、安全或隔离边界？待填写。
3. 运行 `tools/materialize.py flagship m4-api-identity-security/step4`，记录累计测试数量和结果：待填写。
4. 暂时断开一个集成点，观察哪条测试失败，然后恢复：待填写。

## 3. 本节结论

1. 本节仍不能证明什么？执行向量事务和失败恢复仍待实现（补充你的判断）
2. 用 60 秒说明：旧问题 → 新增能力 → 修改旧文件 → 调用链 → 测试证据 → 边界。
