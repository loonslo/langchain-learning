# 三张白板内容总结

## 图片一：基础 RAG 主链与生成扩展

- 左侧把 Load、Split、Embedding、Storage 串成资料准备区。
- 中间解释 Augmented：检索结果经 `format_docs` 变成 `context`，原问题经 `RunnablePassthrough` 保留为 `question`，两路一起填入 Prompt。
- 右侧展开 Generation：`Prompt → LLM → Parser`。
- 下方补充多轮记忆、流式输出、批量调用、工具调用和结构化输出。
- `RunnableWithMessageHistory` 是包在主链外面的记忆中间件；真正存储历史的是 `get_session_history(session_id)` 返回的 History 对象。

## 图片二：离线建库基础

- Load：把 PDF、CSV、Markdown 或文本读成 `Document`，同时保留 `metadata`。
- Split：按段落、换行、标点等边界切块，控制 `chunk_size` 与 `chunk_overlap`。
- Embedding：把文档块转换为固定维度向量；在线问题必须使用同一个模型。
- Storage：向量与原文、metadata 一起保存，用于后续相似度检索。

## 图片三：生产化检索增强

- 查询改写：按问题选择指代消解、Multi-Query、Decomposition、HyDE 或 Step-back。
- 多路召回：向量检索与 BM25 关键词检索并行运行。
- 融合：使用 `EnsembleRetriever` 加权，或使用 RRF 按排名融合。
- 重排：cross-encoder 对候选重新评分，留下更准确的 Top-K。
- 父块回查：通过 `parent_map[child_id]` 把命中的小块还原为更完整的父块。
- 增强与生成：`format_docs → context → Prompt → LLM → Parser`。

## 合并后的真实流程

离线：资料变化 → Load → Document → Split → Embedding / BM25 → 双路索引。

在线：用户问题 → 查询改写 → 并行召回 → 融合 → 重排 → Top-K 父块 → Augment → Prompt → LLM → Parser → 最终回答。

会话记忆：`session_id → RunnableWithMessageHistory → Prompt 注入 history → 回答后保存新一轮`。

工具调用与结构化输出属于可选扩展，不是每次请求都会经过的固定步骤。
