# B2b Gate 验证记录 · 2026-10-18

B2b 覆盖 L2 检索进阶的 6 章：2.6、2.7、2.8、2.9、2.10、2.11。每章新增闭卷骨架、离线验收、README 任务书和 gate workbook；参考实现未修改。B2a（2.1–2.3）见 [gate-b2a-validation.md](gate-b2a-validation.md)。

## 范围

| 章节 | v2 路径 | 验收项 | 新增 |
|---|---|---|---|
| 2.6 PDF 与来源 | L2.3 扩展 | 9 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| 2.7 切分策略 | L2.4 | 7 | 同上 |
| 2.8 混合检索 | L2.5 | 7 | 同上 |
| 2.9 查询改写 | L2.6 | 9 | 同上 |
| 2.10 持久化 | L2.7 | 9 | 同上 |
| 2.11 重排/多模态 | L2.8 | 8 | 同上 |

## 实际执行

### 1. 参考解

| Gate | 结果 |
|---|---|
| 2.6 | 9/9 passed |
| 2.7 | 7/7 passed |
| 2.8 | 7/7 passed |
| 2.9 | 9/9 passed |
| 2.10 | 9/9 passed |
| 2.11 | 8/8 passed |

### 2. 默认骨架

6 个 gate 用默认 `gate/starter.py` 运行都是 0 通过（`NotImplementedError`），退出码 1。这是预期行为。

### 3. 现有回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 263 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <6 个 gate 目录>
All checks passed!
```

## 覆盖的故障

| 章节 | 主要故障 |
|---|---|
| 2.6 | 空白页、非法页/来源、未知页码、伪造来源、无引用 |
| 2.7 | 空文本、非法 max_chars、段落/句子/硬切边界、空块、超长 |
| 2.8 | RRF 权重、同路重复、空排名、k/weights 非法、同分稳定 |
| 2.9 | 编号/重复/超条数、空输出、无新查询、模型异常、空问题 |
| 2.10 | 缺/坏文件、重复 ID、维度/metadata 错、k/查询维度、外部引用 |
| 2.11 | 排序/top-k、同分稳定、空候选、非法 score、输入不被修改、recall@k |

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。
- **没有调用真实 embedding/模型/reranker/PDF**：2.6 只处理页文本；2.8 只实现 RRF；2.10 用 JSON；2.11 用假打分器。
- **没有验证真实检索质量**：切分、混合、改写、持久化、重排的真实效果都未验证。
- **没有改参考实现**：`pdf_sources.py`、`chunk_strategy.py`、`hybrid_search.py`、`query_rewrite.py`、`chroma_persist.py`、`multimodal_rerank.py` 均未修改。

## 复现

```bash
python chapters/part2-rag/2.6-pdf-sources/gate/gate_check.py
python chapters/part2-rag/2.7-chunk-strategy/gate/gate_check.py
python chapters/part2-rag/2.8-hybrid-search/gate/gate_check.py
python chapters/part2-rag/2.9-query-rewrite/gate/gate_check.py
python chapters/part2-rag/2.10-chroma-persist/gate/gate_check.py
python chapters/part2-rag/2.11-multimodal-rerank/gate/gate_check.py
```

默认检查骨架，应 0 通过；实现后可用 `--module 你的实现.py`。

## 边界

- B2a + B2b 覆盖 2.1–2.11 全部 11 章；但 2.6–2.11 的 gate 是“结构/边界”验收，不是真实质量验收。
- 下一批 B3 是 L3 评测的 7 章，未开始。
- gate 只验证结构/边界；真实 RAG 质量仍要评测集和真实模型。
