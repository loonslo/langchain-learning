# 2.9 查询改写：把用户的话转成更好检索的问题

[全书目录](../../README.md) · [上一章 2.8](../2.8-hybrid-search/README.md) · [下一章 2.10](../2.10-chroma-persist/README.md)

- **目标**：用 Multi-Query 和 HyDE 改写查询，改善短问题和口语化问题的召回。
- **前置**：2.7；`DEEPSEEK_API_KEY`；`langchain-classic`。
- **环境**：调用真实模型，加本地 embedding 模型。
- **命令**：`python tools/run_chapter.py 2.9`

## 问题

用户问得很短，或者用词和文档不一样，检索容易漏掉相关内容。可以让模型先把问题改写，再去检索。

## 概念

- **Multi-Query**：让 LLM 把一个问题改写成多条不同的说法，分别检索后合并去重，覆盖更全。
- **HyDE**：先让 LLM 对问题生成一个“假设答案”（内容不一定准），再用它去检索。答案的措辞通常比原问题更接近文档正文，更容易命中。
- **代价**：两种方法都会增加 LLM 调用次数，更慢也更贵，需要按效果权衡是否开启。

## 流程

1. 建立基础检索器（`k=3`）；改写用的 LLM 设 `temperature=0`，保持稳定。
2. 原始问题“向量怎么存”直接检索。
3. `MultiQueryRetriever.from_llm` 改写后检索。
4. 手写 HyDE：`hyde_chain` 生成假设答案，再用它检索。

## 代码导读

[query_rewrite.py](query_rewrite.py)：先看基础检索器，再对比三段输出。HyDE 只有几行，重点理解“为什么用假设答案检索”。`MultiQueryRetriever` 已迁到 `langchain_classic.retrievers`。

## 练习

1. 故意问一个很短、很口语的问题，对比三种方式（原始、Multi-Query、HyDE）的召回差异。
2. 打印 HyDE 生成的假设答案，判断它与文档措辞有多接近。
3. 问一个资料里没有的问题，观察改写是否会把无关内容“召回”进来。

## 运行与边界

- 调用真实模型并产生费用；需要本地 embedding 模型。
- 改写不保证召回更准，也可能引入噪声；必须用同一评测集比较开启前后的结果（第 3 篇）。
