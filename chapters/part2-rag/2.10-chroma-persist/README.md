# 2.10 向量库持久化：下次启动不再从头建立

[全书目录](../../README.md) · [上一章 2.9](../2.9-query-rewrite/README.md) · [下一章 2.11](../2.11-multimodal-rerank/README.md)

- **目标**：把内存里的 FAISS 换成自带持久化的 Chroma，做到“建一次库，之后直接加载”。
- **前置**：2.7；`langchain-chroma`；本地 embedding 模型。
- **环境**：离线，不调用聊天模型。
- **命令**：`python tools/run_chapter.py 2.10`（运行两次，对比启动速度）

## 问题

前面的 RAG 每次运行都要重新做 embedding，程序一关就没了。文档不常变化时，应该建一次库并落盘，之后直接加载。

## 概念

- **`persist_directory`**：Chroma 向量库落盘的目录。
- **建库与加载**：目录不存在时，加载 → 切分 → 向量化 → 落盘；目录已存在时，直接加载，省掉重新 embedding。
- **FAISS 与 Chroma**：FAISS 轻量，适合小项目和内存场景，落盘要手动 `save_local`；Chroma 自带持久化，适合需要保存、需要增量更新的场景。规模更大时可了解 pgvector、Milvus。

## 流程

1. `build_or_load` 检查 `chroma_db/` 是否存在。
2. 不存在：读取示例文档，切分（`chunk_size=300`、`overlap=50`），`Chroma.from_documents(..., persist_directory=...)` 建库并落盘。
3. 已存在：`Chroma(persist_directory=..., embedding_function=...)` 直接加载。
4. 对“RAG 是什么”检索，打印召回的片段。

## 代码导读

[chroma_persist.py](chroma_persist.py)：重点看 `build_or_load` 里“目录是否存在”这一个判断，以及两种构造方式的区别。

## 练习

1. 运行两次，对比第一次和第二次的启动速度和输出。
2. 修改 `chunk_size` 后再运行，观察结果为什么没有变化。
3. 删除 `chroma_db/` 后再运行，确认库被重建。

## 运行与边界

- 向量库落盘在当前章节目录下的 `chroma_db/`（已被 `.gitignore` 忽略）。
- 脚本只判断目录是否存在：文档或切分参数改变后，旧库不会自动更新，必须手动删除 `chroma_db/` 重建。
- 本章没有做增量更新，也没有处理并发写入。
