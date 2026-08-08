# Day71 工作簿 · 向量库迁移契约

## 0. 先确认本日变更闭环

| 文件 | 状态 | 它接到哪个旧文件/入口 | 如果不接会发生什么 |
|---|---|---|---|
| `deployment/pgvector_schema.sql` | 新增 | 待填写 | 待填写 |
| `src/customer_support/vector_store.py` | 新增 | 待填写 | 待填写 |
| `tests/test_sync_vector_store.py` | 新增 | 待填写 | 待填写 |
| `tests/test_vector_store_contract.py` | 新增 | 待填写 | 待填写 |
| `src/customer_support/sync.py` | 修改旧文件 | 待填写 | 待填写 |

真实链路：`scan/plan → apply_plan → VectorStore.upsert/delete_source`

## 1. 从 Day70 继续

1. 前一天暴露的真实问题是什么？Chroma 不能代表最终共享存储（请用自己的话重写）
2. 今天哪些旧文件被修改？为什么只新增模块还不够？待填写。
3. 哪些继承文件虽然未改，却仍参与今天的调用链？待填写。

## 2. 运行与证据

1. 哪条测试证明新能力已从正式入口可达？待填写。
2. 哪条测试保护失败、安全或隔离边界？待填写。
3. 运行 `materialize_day.py 71`，记录累计测试数量和结果：待填写。
4. 暂时断开一个集成点，观察哪条测试失败，然后恢复：待填写。

## 3. 今日结论

1. 今天仍不能证明什么？schema 存在不等于已完成远端迁移（补充你的判断）
2. 用 60 秒说明：旧问题 → 新增能力 → 修改旧文件 → 调用链 → 测试证据 → 边界。
