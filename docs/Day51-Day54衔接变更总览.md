# Day51–Day54 学习衔接：每天哪些旧文件被接上了

Day51–Day54 不是四个互不相关的 RAG 示例，而是同一个客服产品连续四次变更。每天阅读时要同时回答两件事：

1. 今天新增了什么能力？
2. 为了让这个能力真正进入产品主链，哪些旧文件被修改了？哪些旧文件虽然没改，仍然在运行？

可以在仓库根目录运行下面的命令查看机器根据实际文件重建出的差异：

```powershell
python tools/day_change_report.py 52
python tools/day_change_report.py 53
python tools/day_change_report.py 54
```

## Day51：建立基线

| 文件 | 状态 | 在主链中的职责 |
|---|---|---|
| `src/customer_support/settings.py` | 新建 | 把单个 FAQ 文件路径和模型配置交给组合入口 |
| `src/customer_support/knowledge.py` | 新建 | 单文件加载、切块、向量检索 |
| `src/customer_support/bootstrap.py` | 新建 | 创建 embedding、Retriever、LLM 并组装助手 |
| `src/customer_support/assistant.py` | 新建 | 检索、有证据回答、无证据拒答、来源返回 |
| `src/customer_support/app.py` | 新建 | 接收用户输入并展示答案 |

基线链路是：

```text
settings.knowledge_path（单个 Markdown）
  → knowledge.load_chunks / build_retriever
  → bootstrap.build_assistant
  → assistant.ask
  → app.run_interactive
```

## Day52：新增摄取层，同时改写两个旧接口

| 文件 | 状态 | 今天必须看懂的变化 |
|---|---|---|
| `src/customer_support/ingestion.py` | 新增 | 从“加载一个文件”扩展为“遍历目录、切块、补 `source_id`/`chunk_id`” |
| `src/customer_support/settings.py` | 修改旧文件 | `knowledge_path` 从 `customer_faq.md` 改为 `data/knowledge/` 目录 |
| `src/customer_support/knowledge.py` | 修改旧文件 | 不再调用单文件 `load_chunks`，改为调用 `ingest_directory` |
| `data/knowledge/refund.md` | 新增 | 第二份知识来源 |
| `data/knowledge/shipping.md` | 新增 | 第三份知识来源 |
| `src/customer_support/bootstrap.py` | 继承未改 | 仍按同一接口把 `settings.knowledge_path` 传给 `build_retriever` |
| `src/customer_support/assistant.py` | 继承未改 | 不知道单文件/多文件差异，继续消费统一 Retriever |

因此 Day52 的真实变化不是“多了一个 `ingestion.py`”，而是：

```text
settings（文件 → 目录）
  → knowledge（调用 ingestion.ingest_directory）
  → bootstrap（沿用同一 build_retriever 接口）
  → assistant（沿用同一 ask 规则）
  → app
```

## Day53：在多文档主链旁边接入评测，不复制问答实现

| 文件 | 状态 | 今天必须看懂的变化 |
|---|---|---|
| `src/customer_support/evaluation.py` | 新增 | 读取固定评测集，调用真实 `assistant.ask()`，分别判断答案和引用 |
| `src/customer_support/settings.py` | 修改旧文件 | 在保留多文档 `knowledge_path` 的基础上增加 `evaluation_path` |
| `data/eval_cases.json` | 新增 | 固定问题、答案关键词、期望来源和拒答要求 |
| `src/customer_support/bootstrap.py` | 继承未改 | 评测仍通过它创建正式 Retriever 和模型 |
| `src/customer_support/knowledge.py` | 继承未改 | 仍使用 Day52 的目录摄取 |
| `src/customer_support/assistant.py` | 继承未改 | 评测不另写一套回答逻辑，统一调用 `ask()` |

Day53 有两条入口，但只有一条业务主链：

```text
app.py ───────────────┐
                      ├→ bootstrap → knowledge/ingestion → assistant.ask
evaluation.py ────────┘
```

## Day54：新增混合检索，并改写旧的知识库装配点

| 文件 | 状态 | 今天必须看懂的变化 |
|---|---|---|
| `src/customer_support/retrieval.py` | 新增 | 提供关键词检索、语义/关键词结果融合和 `chunk_id` 去重 |
| `src/customer_support/knowledge.py` | 修改旧文件 | 用同一批 ingestion chunks 创建语义通道和关键词通道，返回 `HybridRetriever`，并保留 Day52 的 `load_chunks` 导出 |
| `src/customer_support/ingestion.py` | 继承未改 | 仍是两路检索共同消费的唯一文档入口 |
| `src/customer_support/settings.py` | 继承未改 | 仍提供目录路径、`k` 和阈值 |
| `src/customer_support/evaluation.py` | 继承未改 | 自动获得混合检索，不需要另改评测逻辑 |
| `src/customer_support/bootstrap.py` | 继承未改 | 仍只调用统一的 `build_retriever` |

Day54 的串联关系是：

```text
settings.knowledge_path
  → knowledge.ingest_directory
  → 同一批 chunks
      ├→ Chroma 语义检索
      └→ KeywordRetriever 关键词检索
              ↓
          HybridRetriever / RRF
              ↓
      bootstrap → assistant.ask → app 或 evaluation
```

## 阅读顺序与验收问题

每天先看当天表格里的“修改旧文件”，再看“新增文件”，最后沿主链验证：

- Day52：如果只新增 `ingestion.py`，`settings` 仍指向文件、`knowledge` 仍调用单文件加载，新增能力是否会生效？
- Day53：如果评测自己重新实现检索或回答，评测结果能代表用户主程序吗？
- Day54：如果只写 `retrieval.py` 而不修改 `knowledge.py`，`bootstrap` 返回的还是 Day52 的普通语义 Retriever 吗？
- 每天：哪些文件是“继承未改”，它们为什么仍然是今天运行链的一部分？

`tools/day_change_report.py` 负责回答“实际哪些文件变了”；本文件和各日 `README.md` / `workbook.md` 负责回答“为什么这些文件必须一起读”。
