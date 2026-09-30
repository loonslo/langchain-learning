# 2.11 重排与多模态：增加能力后仍要保留证据

[全书目录](../../README.md) · [上一章 2.10](../2.10-chroma-persist/README.md) · [下一章 3.1](../../part3-evals/3.1-error-analysis/README.md)

- **目标**：用 reranker 对召回结果精排，并了解怎样把图片交给视觉模型。
- **前置**：2.7。
- **环境**：reranker 部分需要本地 `bge-reranker-base` 模型；多模态部分需要一个视觉模型的密钥和一张图片（仓库不附带）。
- **命令**：`python tools/run_chapter.py 2.11`

## 问题

向量检索为了不漏掉相关内容，往往会多召回（如 top8），但塞给模型太多片段，既增加噪声又费 token。另一方面，用户的资料常是截图、扫描件，纯文本加载器读不了。

## 概念

- **粗召回 + 精排**：向量检索快但粗，先多召回；reranker（cross-encoder）把问题和每个候选放在一起打分，更准但更慢，只对候选精排并保留最相关的 `top_n` 个。这是常见的两段式做法。
- **何时需要**：候选多、对精度要求高、token 预算紧时；小库的简单问答可以不上。
- **多模态**：把图片编码成 base64，与文字一起放进一条 human 消息，发给支持视觉的模型。纯文本模型（如 `deepseek-chat`）不支持图片。

## 流程

reranker：

1. 切分长文章（`chunk_size=160`、`overlap=30`），建 FAISS，粗召回 `k=8`。
2. `CrossEncoderReranker` 精排，保留 `top_n=3`，用 `ContextualCompressionRetriever` 包装。
3. 对同一个问题“LangGraph 适合哪些场景”，分别打印粗召回 top8 和精排 top3。

多模态：`ask_image` 读取图片并编码，通过 `VLM_MODEL`、`VLM_API_KEY`、`VLM_BASE_URL` 配置的视觉模型提问；没有 `sample_scan.png` 时跳过这一部分。

## 代码导读

[multimodal_rerank.py](multimodal_rerank.py)：先读第二部分 `build_rerank_retriever`，再读第一部分 `ask_image`。`ContextualCompressionRetriever`、`CrossEncoderReranker` 在 `langchain_classic.retrievers`，`HuggingFaceCrossEncoder` 在 `langchain_community.cross_encoders`。

## 练习

1. 对比粗召回 top8 与精排 top3，哪些片段被提前、哪些被剔除。
2. 把 `top_n` 从 3 调到 1，看是否漏掉跨段落的答案。
3. 准备一张截图，配置视觉模型后运行多模态部分。

## 运行与边界

- 没有下载 `bge-reranker-base` 时，reranker 部分会报错并提示下载（`snapshot_download('BAAI/bge-reranker-base')`），路径可用 `RERANKER_MODEL_PATH` 覆盖。
- 精排提高的是候选顺序，不能补回粗召回已经漏掉的内容，也不能保证回答正确。
- 视觉模型的 OCR 与理解结果可能出错，需要抽样核对。
- 小结：RAG 答错时，先分清是检索没召回相关内容，还是召回了但生成时编造。前者调切分、混合检索、查询改写、重排，后者调 prompt、换模型、加忠实度约束。
