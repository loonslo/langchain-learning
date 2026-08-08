# Day52 工作簿 · 多文档真正进入产品

## 0. 先看本日变更闭环

不要只打开新增的 `ingestion.py`。先完成下面这张表，再沿调用链阅读：

| 文件 | 相对 Day51 | 关键问题 |
|---|---|---|
| `settings.py` | 修改 | 路径为什么必须从文件改成目录？ |
| `knowledge.py` | 修改 | 它在哪里调用 `ingest_directory()`？ |
| `ingestion.py` | 新增 | 它输出的 chunks 被谁消费？ |
| `bootstrap.py` | 继承未改 | 为什么接口不变也能接上新实现？ |
| `assistant.py` | 继承未改 | 为什么业务问答规则不需要改？ |

先运行 `python tools/day_change_report.py 52`，再回答：如果删掉 `settings.py` 或 `knowledge.py` 的 Day52 版本，新增的摄取层还能进入主程序吗？

## 1. 对比 Day51 与 Day52

| 观察点 | Day51 | Day52 |
|---|---|---|
| knowledge_path 指向 | 待填写 | 待填写 |
| 实际摄取文档数 | 待填写 | 待填写 |
| 主程序可引用来源 | 待填写 | 待填写 |

## 2. 跟踪真实链路

补全：

> 知识目录 → ______ → chunks → ______ → bootstrap → assistant → 主程序

- `source_id` 的用途：待填写。
- `chunk_id` 稳定的用途：待填写。
- 为什么 ingestion 与 knowledge 不能互相导入：待填写。

## 3. 自由体验

| 自选问题 | 期望来源 | 实际来源 | 是否符合 |
|---|---|---|---|
| 退款问题 | refund.md | 待填写 | 待填写 |
| 配送问题 | shipping.md | 待填写 | 待填写 |
| 资料外问题 | 无 | 待填写 | 待填写 |

## 4. 当天验收

- 是否真实加载三份文档：待填写。
- 真实 build_retriever 是否读取整个目录：待填写。
- 累计测试结果：待填写。
- 当前还缺少的可重复质量证据：待填写。
