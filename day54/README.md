# Day54 · 混合检索正式进入产品主链路

Day54 不只实现 RRF 算法，而是把语义检索、关键词检索和 RRF 全部接入 `bootstrap → assistant → 主程序`。

## 与 Day53 的文件衔接

| 文件 | 今天的状态 | 为什么必须一起看 |
|---|---|---|
| `src/customer_support/retrieval.py` | 新增 | 提供关键词检索、混合检索和 RRF 去重 |
| `src/customer_support/knowledge.py` | 修改旧文件 | 把同一批 ingestion chunks 接到语义和关键词两路，同时保留 Day52 的 `load_chunks` 导出 |
| `src/customer_support/ingestion.py` | 继承未改 | 两路检索共用的文档输入仍由它生成 |
| `src/customer_support/settings.py` | 继承未改 | 继续提供目录、k 和阈值配置 |
| `src/customer_support/evaluation.py` | 继承未改 | 自动复用新的 `build_retriever`，无需复制评测链 |
| `src/customer_support/bootstrap.py` | 继承未改 | 仍通过统一工厂把检索器交给 assistant |

用 `python tools/day_change_report.py 54` 核对实际变更；如果只新增 `retrieval.py` 而不改 `knowledge.py`，混合检索不会进入正式产品。

## 当天交付

- `KeywordRetriever` 提供本地 BM25 风格排序。
- `HybridRetriever` 对同一问题执行语义和关键词两路检索。
- `reciprocal_rank_fusion` 奖励共同命中文档并去重。
- `knowledge.build_retriever()` 默认返回 `HybridRetriever`。
- 用户主程序和独立评测程序全部自动使用混合检索。

## 真实调用链

```text
用户问题
  ├─ Chroma 语义检索 ─┐
  └─ BM25 关键词检索 ─┤
                       → RRF → CustomerSupportAssistant → 答案与来源
```

## 在 PyCharm 运行与比较

还原 Day54 后，将 `.build/day54/customer-support/src` 标记为 Sources Root，Working directory 选择 `.build/day54/customer-support`。用户问答运行模块 `customer_support.app`，开发评测运行模块 `customer_support.evaluation`。

建议尝试包含精确业务词的问题，再检查评测结果与引用来源。

## 完成标准

- 正式 `build_retriever()` 返回混合检索器。
- 语义检索无结果时，关键词通道仍能提供证据。
- 两路共同命中的文档只出现一次并获得更高排名。
- Day51～54 累计测试全部通过。
- 能通过主程序自由提问，并能通过独立评测程序运行真实回归。

Day54 结束时得到的是一个可使用、可回归的多文档混合检索客服产品版本；后续 Day55～78 必须继续修改这条产品链，而不能退回孤立组件模式。
