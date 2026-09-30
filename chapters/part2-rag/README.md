# 第 2 篇：检索增强生成 RAG

先把资料读对并找到证据，再组织回答。每次增加切分、融合、改写或重排，都保留固定问题作比较。

先修：第 1 篇。

- [2.1 文档加载与切分：资料如何进入系统](2.1-load-split/README.md)（离线）
- [2.2 向量化与召回：先找到可能相关的片段](2.2-embed-retrieve/README.md)（本地 embedding）
- [2.3 最小 RAG：让回答依据检索资料](2.3-minimal-rag/README.md)（真实模型 + 本地 embedding）
- [2.4 RAG 评测种子：从五个问题开始](2.4-eval-seed/README.md)（离线）
- [2.5 裸 SDK 与循环：看清框架封装了什么](2.5-raw-sdk-rag-agent-loop/README.md)（离线可读，有密钥时调用模型）
- [2.6 PDF 与来源溯源：答案要能回到原文](2.6-pdf-sources/README.md)（真实模型 + 本地 embedding）
- [2.7 切分策略：让完整事实留在片段里](2.7-chunk-strategy/README.md)（本地 embedding）
- [2.8 混合检索：同时照顾语义和精确词](2.8-hybrid-search/README.md)（本地 embedding）
- [2.9 查询改写：把用户的话转成更好检索的问题](2.9-query-rewrite/README.md)（真实模型 + 本地 embedding）
- [2.10 向量库持久化：下次启动不再从头建立](2.10-chroma-persist/README.md)（本地 embedding）
- [2.11 重排与多模态：增加能力后仍要保留证据](2.11-multimodal-rerank/README.md)（本地 reranker，多模态部分选做）

[返回全书目录](../README.md)
