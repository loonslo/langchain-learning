# B2a Gate 验证记录 · 2026-10-18

B2 拆成 B2a（检索主链 2.1–2.3）和 B2b（2.6–2.11）。本记录只覆盖 B2a：新增闭卷骨架、离线验收、README 任务书和 workbook；参考实现未修改。

## 范围

| 章节 | v2 路径 | 验收项 | 新增 |
|---|---|---|---|
| 2.1 加载与切分 | L2.1 核心 | 6 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| 2.2 向量化与召回 | L2.2 核心 | 9 | 同上 |
| 2.3 最小 RAG | L2.3 核心 | 10 | 同上 |

## 实际执行

### 1. 参考解

| Gate | 结果 |
|---|---|
| 2.1 | 6/6 passed |
| 2.2 | 9/9 passed |
| 2.3 | 10/10 passed |

### 2. 默认骨架

3 个 gate 用默认 `gate/starter.py` 运行都是 0 通过（`NotImplementedError`），退出码 1。这是预期行为。

### 3. 现有回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 262 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <3 个 gate 目录>
All checks passed!
```

## 覆盖的故障

| 章节 | 主要故障 |
|---|---|
| 2.1 | 不存在文件、空文本、非法 chunk/overlap、doc 缺字段、source 丢失 |
| 2.2 | 零向量、维度不一致、重复 ID、k=0、空索引、外部引用污染 |
| 2.3 | 无证据仍调用模型、检索异常、模型超时、空回答、预算裁剪、来源重复 |

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。
- **没有调用真实 embedding/模型**：2.1 只读 txt；2.2 用二维假向量；2.3 用假检索/假模型。
- **没有验证真实检索质量**：切分、embedding、MMR、prompt 效果都未验证。
- **没有改参考实现**：`load_split.py`、`embed_retrieve.py`、`minimal_rag.py` 均未修改。

## 复现

```bash
python chapters/part2-rag/2.1-load-split/gate/gate_check.py
python chapters/part2-rag/2.2-embed-retrieve/gate/gate_check.py
python chapters/part2-rag/2.3-minimal-rag/gate/gate_check.py
```

默认检查骨架，应 0 通过；实现后可用 `--module 你的实现.py`。

## 边界

- B2a 只覆盖 2.1–2.3；2.4/2.5 在样板批次已完成。
- B2b（2.6–2.11）未开始：PDF 溯源、切分策略、混合检索、查询改写、持久化、重排。
- gate 只验证结构/边界，真实 RAG 质量仍要评测集和真实模型。
