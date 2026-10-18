# L2.7 向量库持久化 · Gate（原 2.10）

[全书目录](../../README.md) · [上一章 2.9](../2.9-query-rewrite/README.md) · [下一章 2.11](../2.11-multimodal-rerank/README.md)

- **能力**：把向量记录写入 JSON、落盘、重新加载；校验重复 ID/维度/坏文件。
- **v2 路径**：L2.7 / 核心（Gate；持久化）
- **前置**：2.2（向量与索引）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `chroma_persist.py`。
- **验收命令**：

```bash
python chapters/part2-rag/2.10-chroma-persist/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

持久化不是“把内存对象 dump 成 JSON”这么简单：

- 文件不存在/损坏时，服务要能明确报错；
- ID 重复会覆盖旧记录；
- 维度不一致会让查询崩；
- 加载后 metadata 丢失，引用就断了；
- 写入时持有外部列表引用，后续修改污染索引。

这个 gate 用临时 JSON 文件做落盘/加载往返，不依赖 Chroma。

## 任务

实现 `gate/starter.py` 的 `PersistentVectorStore`：

| 方法 | 你要交付的行为 |
|---|---|
| `add` | 校验长度/ID/维度/metadata；保存副本 |
| `search` | 余弦排序 top-k；空库 `[]`；维度/k 错误报 `StoreError` |
| `save` | 写 UTF-8 JSON；失败报 `StoreError` |
| `load` | 读 JSON；缺文件/坏 JSON/缺字段/重复 ID 报 `StoreError` |

关键口径：

- `metadata` 缺省为等长空 dict；长度必须一致。
- ID 非空且不重复；向量维度一致。
- `k < 1`、查询维度不一致 -> `StoreError`。
- 内部保存 `vector`/`metadata` 副本，不持有外部引用。
- JSON 至少包含 `id/vector/metadata`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 保存后重新加载 | 排序与 metadata 一致 |
| 2 | 文件不存在 | `StoreError` |
| 3 | 坏 JSON | `StoreError` |
| 4 | 重复 ID | `StoreError` |
| 5 | 维度不一致 | `StoreError` |
| 6 | metadata 长度不一致 | `StoreError` |
| 7 | `k=0` | `StoreError` |
| 8 | 外部修改传入向量/metadata | 索引不变 |

## 验收标准

`gate_check.py` 的 9 项全部 PASS：

- 写入/检索、保存/加载往返、缺文件、坏 JSON、重复 ID、维度/metadata、空库/k、查询维度、外部引用。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么加载时要重新校验 ID/维度，而不是直接信任文件？
2. 文档更新后，旧库怎么失效？本章的目录判断够吗？
3. JSON 持久化和 Chroma 持久化的差别是什么？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（9/9）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 2.10
```

对照时只回答：

1. 参考实现用 `persist_directory` 判断建库/加载；它会不会检测文档变化？
2. Chroma 的落盘格式对你是黑盒；本 gate 的 JSON 格式暴露了哪些必须校验的字段？
3. 如果要支持增量更新/删除，最小改动是什么？

## 概念地图

- **持久化**：把向量、ID、metadata 落盘；下次加载不再 embedding。
- **加载校验**：文件可能损坏/过期；ID/维度/字段必须重新校验。
- **失效**：文档/切分参数变化后，旧库不能自动更新；需要版本或重建。
- **副本**：内部保存副本，避免外部引用污染。
- **选型**：JSON 适合教学/小规模；Chroma/FAISS/pgvector 各有适用边界。

## 边界

- gate 用 JSON 文件，不依赖 Chroma；不验证真实向量库性能/并发。
- 通过 gate 只证明落盘/加载/校验结构正确。
- 增量更新、版本失效、并发写入未实现。
