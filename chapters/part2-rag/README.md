# 第 2 篇：检索增强生成 RAG

先把资料读对并找到证据，再组织回答。每次增加切分、融合、改写或重排，都保留固定问题作比较。

先修：第 1 篇。

- [2.1 · L2.1 加载与切分（Gate）](2.1-load-split/README.md)（离线 gate）
- [2.2 · L2.2 向量化与召回（Gate）](2.2-embed-retrieve/README.md)（离线 gate；参考实现需本地 embedding）
- [2.3 · L2.3 最小 RAG（Gate）](2.3-minimal-rag/README.md)（离线 gate；参考实现需真实模型 + embedding）
- [2.4 · L2.9 RAG 评测基线（Gate）](2.4-eval-seed/README.md)（离线 gate）
- [2.5 · L1.6 手写 Harness（Gate）](2.5-raw-sdk-rag-agent-loop/README.md)（离线 gate，参考实现可选真实模型）
- [2.6 · L2.3 扩展：PDF 与来源（Gate）](2.6-pdf-sources/README.md)（离线 gate；参考实现需真实模型 + embedding）
- [2.7 · L2.4 切分策略（Gate）](2.7-chunk-strategy/README.md)（离线 gate；参考实现需本地 embedding）
- [2.8 · L2.5 混合检索（Gate）](2.8-hybrid-search/README.md)（离线 gate；参考实现需本地 embedding）
- [2.9 · L2.6 查询改写（Gate）](2.9-query-rewrite/README.md)（离线 gate；参考实现需真实模型 + embedding）
- [2.10 · L2.7 向量库持久化（Gate）](2.10-chroma-persist/README.md)（离线 gate；参考实现需本地 embedding）
- [2.11 · L2.8 重排与多模态（Gate）](2.11-multimodal-rerank/README.md)（离线 gate；参考实现需 reranker，多模态选做）

[返回全书目录](../README.md)
