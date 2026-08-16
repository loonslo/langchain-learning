# Day11–Day20 详细章节概括：把 RAG 做得更像真实系统，并开始评测

这一组的主线是：先理解模型和 RAG 的底层，再提升真实文档处理、检索质量和持久化能力，最后从“看起来能答”进入“用数据证明答得好不好”。

## Day11 · 了解 LLM 内部原理

代码在：[day11/day11_llm_principles.py](../day11/day11_llm_principles.py)

Day11 做的事情是：**前九天一直在“用”模型，这一天补上模型内部的基本认知，让你能解释成本、语义检索和幻觉从哪里来。**

### 1. 先理解 token 和成本

```python
text = "RAG 是检索增强生成"
print(len(text))
print(int(len(text) * 1.5))
```

这里用粗略估算帮助理解：模型不是按 Python 的“字符数”直接处理文本，而是按 token 处理。token 数量会影响调用成本，也会影响上下文窗口能放多少内容。

实际 token 数取决于模型 tokenizer，所以代码中的估算不是计费依据，只是建立直觉。

### 2. 理解 embedding 为什么能做语义检索

Day8 已经调用过 embedding，这一天把原理拆开：

```python
vector_a = embeddings.embed_query("怎么做向量检索")
vector_b = embeddings.embed_query("FAISS 如何查相似文本")
```

再用余弦相似度比较两个向量：

```text
向量方向越接近 → 语义通常越相近
```

所以 embedding 不是“给文字编号”，而是把文字映射到一个可以计算距离的空间；Day8 的 FAISS 就是在这个空间里找近邻。

### 3. 用一句话理解 attention

Attention 可以理解为：模型处理当前 token 时，会根据上下文决定哪些位置更值得关注。它不是简单从左到右只看前一个字，而是通过上下文关系理解“这个词和哪些词有关”。

这一天不要求手写 Transformer，也不要求推导公式，目标是能把 token、embedding、attention 放在正确的层次上。

### 4. 为什么模型会幻觉？

模型本质是根据上下文预测下一个最可能的 token：

```text
语言上听起来合理 ≠ 事实上一​​定有证据
```

因此模型不是数据库查询器，不知道时也可能生成一个流畅答案。RAG、拒答 Prompt、来源引用和评测，都是在给这种生成能力加事实边界。

### 5. Day11 最终要记住什么？

```text
token      → 成本和上下文长度
embedding  → 语义相似度
attention  → 利用上下文关系
幻觉       → 预测文本，不等于查事实
```

## Day12 · 处理 PDF、保留来源并封装 RAG

代码在：[day12/day12_rag_pdf_sources.py](../day12/day12_rag_pdf_sources.py)

Day12 做的事情是：**把 Day9 的单 txt、平铺式 RAG，升级成支持 PDF、带来源溯源、可复用和可测试的 RAG。**

### 1. 统一加载 txt 和 PDF

```python
def load_document(file_path: str) -> list[Document]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        ...
    elif ext == ".pdf":
        ...
```

无论输入是 txt 还是 PDF，函数都返回 `Document` 列表。这样后面的切块、向量化和检索不需要关心原始文件格式。

### 2. 把来源写进 metadata

```python
Document(
    page_content=text,
    metadata={
        "source": file_name,
        "page": page_number,
    },
)
```

回答时不只返回答案，还可以返回“来自哪个文件、哪一页”。这让 RAG 从“生成一个答案”变成“生成一个带证据的答案”。

### 3. 把建库和问答封装成函数

Day9 的代码全部写在一个脚本里，Day12 开始拆成类似：

```python
build_retriever(path)
build_rag_chain(retriever)
```

好处是：主程序可以调用，测试可以注入假 retriever，后续服务化也能复用同一套组件。

### 4. 修正“过度拒答”

Prompt 不应该只写“没有完整答案就拒答”。更合理的规则是：

```text
有部分相关证据 → 基于证据回答并说明边界
完全没有相关证据 → 明确拒答
```

否则检索已经拿到相关内容，模型却因为证据不够完整而直接说“不知道”，会造成过度拒答。

### 5. Day12 最终要记住什么？

```text
真实文档 → 统一加载 → 带来源切块 → 检索 → 带引用回答
```

真实 RAG 的合格标准不只是“能答”，还包括来源可追溯、模块可复用、无证据时行为明确。

## Day13 · 对比 chunk 切割策略

代码在：[day13/day13_rag_chunk_strategy.py](../day13/day13_rag_chunk_strategy.py)

Day13 做的事情是：**不凭感觉设置 chunk 参数，而是用同一个问题对比不同切割策略，看切块如何影响检索。**

### 1. 代码设置三组对照

```python
STRATEGIES = [
    {"name": "小块 + 无重叠", "chunk_size": 50, "chunk_overlap": 0},
    {"name": "小块 + 有重叠", "chunk_size": 50, "chunk_overlap": 20},
    {"name": "大块 + 有重叠", "chunk_size": 500, "chunk_overlap": 30},
]
```

同一个查询：

```python
QUERY = "RAG 为什么能减少幻觉"
```

每组只改变切割参数，再观察召回的文档块内容和数量，避免多个变量同时变化导致无法判断原因。

### 2. `chunk_size` 影响什么？

```text
太小 → 精确，但一个完整答案可能被拆到两个块里
太大 → 语义完整，但混入更多无关内容
```

切块直接影响后续 embedding 和检索。embedding 再准确，如果输入 chunk 本身把答案切断，召回也可能只拿到半句话。

### 3. `chunk_overlap` 解决什么问题？

相邻 chunk 保留一部分重叠内容，可以降低答案刚好落在切分边界时的信息损失；代价是重复内容增加，向量数量和上下文成本也会增加。

### 4. 中文分隔符为什么重要？

中文文档不像英文天然以空格分词。代码优先按段落、换行、句号和逗号切，最后才逐字符切，保证尽量保留中文语义边界。

### 5. Day13 最终要记住什么？

> Chunk 策略是 RAG 的质量参数，不是固定常数。应该通过召回效果、引用准确性和生成质量一起调，而不是看到教程里的 `chunk_size=500` 就照抄。

## Day14 · 向量检索加 BM25 混合检索

代码在：[day14/day14_rag_hybrid_search.py](../day14/day14_rag_hybrid_search.py)

Day14 做的事情是：**让语义检索和关键词检索互相补位，解决专有名词、编号和型号容易被向量检索漏掉的问题。**

### 1. 两种检索各自擅长什么？

```text
向量检索 → “意思相近”
BM25     → “词出现得准确、频率高”
```

问“FAISS 是什么”时，向量检索可能召回很多“向量库”的近义内容，但不一定把包含 FAISS 这个词的块排在最前；BM25 可以补上精确匹配。

### 2. 代码使用 BM25 和 Ensemble

```python
bm25 = BM25Retriever.from_documents(chunks)
vector = FAISS.from_documents(chunks, embeddings).as_retriever()
hybrid = EnsembleRetriever(
    retrievers=[vector, bm25],
    weights=[0.5, 0.5],
)
```

两路检索分别排名，再根据权重合并结果。生产实现常用 RRF 思路：一个文档在多个结果中都靠前，就获得更高综合排名，同时去重。

### 3. 中文 BM25 的坑

BM25 默认可能按空格分词，而中文句子通常没有空格。整句话被当成一个 token 后，关键词检索就会失效。

所以生产需要传入中文分词函数，例如 jieba 分词或字符 bigram；否则“接上 BM25”不代表真的得到了关键词能力。

### 4. Day14 最终要记住什么？

```text
向量检索负责语义覆盖
BM25 负责精确词命中
混合排序负责综合两种证据
```

## Day15 · 用 Multi-Query 和 HyDE 改写查询

代码在：[day15/day15_rag_query_rewrite.py](../day15/day15_rag_query_rewrite.py)

Day15 做的事情是：**当用户问得太短、太口语或用词和文档不一致时，先改写查询，再去检索。**

### 1. Multi-Query：一个问题变成多个问法

```text
用户问题：怎么减少幻觉？
  → 如何让 RAG 减少模型幻觉？
  → 检索增强生成为什么能降低幻觉？
  → 知识库问答如何避免无依据回答？
```

每个改写问题分别检索，最后合并结果。这样可以扩大召回覆盖，减少单一表达方式造成的漏检。

### 2. HyDE：先生成假设答案，再拿它检索

```text
原问题 → LLM 生成一个假设答案
       → 用假设答案做 embedding
       → 到知识库中找相似文档
```

用户问题可能只有几个关键词，而假设答案通常更接近文档的完整措辞，所以有机会提高语义命中率。

但假设答案不是真实证据，只能用于检索，不能直接当最终回答依据。

### 3. 这一天带来的工程取舍

查询改写会增加模型调用、延迟和成本，也可能把错误理解放大。因此要和原始查询做对照，用评测确认召回真的变好，而不是只看某一个案例。

### 4. Day15 最终要记住什么？

> RAG 的召回效果不仅取决于向量库，还取决于“你拿什么文本去检索”。查询改写是在召回前做 Context Engineering。

## Day16 · 用 Chroma 持久化向量库

代码在：[day16/day16_rag_chroma_persist.py](../day16/day16_rag_chroma_persist.py)

Day16 做的事情是：**解决 Day8/Day9 每次启动都要重新 embedding、程序结束向量库就消失的问题。**

### 1. 建库和加载分成两个分支

```python
def build_or_load(file_path="test_doc.txt"):
    embeddings = get_embeddings()
    if os.path.exists(PERSIST_DIR):
        return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings,
        )
    return Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=PERSIST_DIR,
    )
```

第一次运行：加载文档、切块、embedding、写入 Chroma；第二次运行：发现目录存在，直接加载，不再重复计算。

### 2. FAISS 和 Chroma 的区别

```text
FAISS  → 轻量内存索引，适合学习和临时实验
Chroma → 带持久化能力，适合本地应用反复启动
```

FAISS 也可以手动 `save_local()`，但 Chroma 把持久化路径直接纳入向量库对象，使用方式更接近应用需要。

### 3. Day16 最终要记住什么？

```text
文档变化时 → 建库并落盘
文档没变化 → 直接加载已有向量库
```

RAG 建库是相对昂贵的离线过程，问答是在线过程；不要把两者混在每次请求里。

## Day17 · 多模态读图和 reranker 重排

代码在：[day17/day17_rag_multimodal_rerank.py](../day17/day17_rag_multimodal_rerank.py)

Day17 做的事情是：**补齐真实资料里的图片/扫描件处理，并把“粗召回很多结果”优化成“精排后只给模型少量好结果”。**

### 1. 让视觉模型理解图片

纯文本 loader 读不了截图、拍照合同和扫描件。代码把图片转成 base64，再作为多模态消息发给支持视觉的模型：

```text
图片文件
  → base64
  → image_url / 多模态 message
  → 视觉模型理解图中文字或图意
```

在不同产品里，可以选择 OCR 后进入普通文本 RAG，也可以让视觉模型直接描述图片。

### 2. 为什么需要 reranker？

向量检索为了不漏证据，通常会多召回，例如 top8；但把 top8 全塞给 LLM 会增加噪声和 token 成本。

```text
向量检索：快、召回广、允许有噪声
reranker：慢、排序准、只保留少量候选
```

代码使用 `ContextualCompressionRetriever` 和 `CrossEncoderReranker`，对候选文档逐个重新判断相关性，最后只留下 top3。

### 3. Day17 最终要记住什么？

> 工业级 RAG 常见结构是“粗召回 + 精排 + 生成”。召回率和精确率不一定由同一个组件同时解决。

## Day18 · 手写 RAG 评测指标

代码在：[day18/day18_eval_basics.py](../day18/day18_eval_basics.py)

Day18 做的事情是：**把“这次回答看起来不错”变成可以重复计算的评测结果。**

### 1. 评测集必须包含期望行为

```python
{
    "question": "RAG 是什么",
    "keywords": ["检索", "生成"],
    "should_refuse": False,
}
```

对于资料外问题：

```python
{
    "question": "文档里讲量子计算吗",
    "keywords": [],
    "should_refuse": True,
}
```

没有“期望答案/是否拒答”的评测数据，就无法判断模型答得对不对。

### 2. 计算拒答正确率和关键词命中率

代码通过 `looks_like_refuse()` 判断回答是否包含“我不知道、未提及、无法回答”等拒答提示，再统计：

```text
拒答正确率 = 应该拒答且确实拒答的题数 / 应该拒答的题数
关键词命中率 = 命中核心关键词的题数 / 有关键词的应答题数
```

这些指标不完美，但便宜、透明、可解释，适合先建立回归基线。

### 3. Day18 最终要记住什么？

> 评测的第一步不是安装一个评测库，而是造好带期望的评测集，再用带分母的指标重复计算。

## Day19 · 让另一个 LLM 当裁判

代码在：[day19/day19_eval_llm_judge.py](../day19/day19_eval_llm_judge.py)

Day19 做的事情是：**解决关键词匹配太死板的问题，让另一个 LLM 从语义角度评估答案。**

### 1. 定义裁判返回格式

```python
class Verdict(BaseModel):
    score: int = Field(description="1-5 分")
    reason: str = Field(description="打分理由，一句话")
```

裁判不是返回一大段解释，而是返回分数和理由，方便统计，也保留了可追溯证据。

### 2. 评两个不同维度

```text
correctness → 和标准答案比，意思是否正确
faithfulness → 是否只根据上下文，是否编造
```

一个答案可能“结论碰巧正确”，但上下文里没有依据；这时 correctness 可能高，faithfulness 应该低。把两个维度拆开，才能区分“答对”和“有证据地答对”。

### 3. 为什么设置 `temperature=0`？

```python
judge_llm = get_llm(temperature=0).with_structured_output(Verdict)
```

裁判输出本身也会有随机性。固定 temperature 有助于回归比较，但不能保证裁判绝对正确；后续还需要人工校准和一致性检查。

### 4. Day19 最终要记住什么？

> LLM-as-judge 比关键词更接近人工判断，但裁判也是一个需要被测试和校准的模型，不能把它的分数直接当真值。

## Day20 · 正式建立评测集

代码在：[day20/day20_eval_dataset_build.py](../day20/day20_eval_dataset_build.py)

Day20 做的事情是：**把前两天的评测示例升级成可版本管理、可复用的评测数据资产。**

### 1. 先固定一条样本的 schema

```text
id             → 用例唯一编号
question       → 用户问题
reference      → 人写的标准答案
keywords       → 关键词指标需要命中的词
expect_source  → 应该召回的来源
type           → fact / multi_hop / refuse / citation
should_refuse  → 是否应该拒答
```

固定字段后，Day18 的规则指标、Day19 的裁判、后面的 RAGAS 和 pytest 才能共同消费同一份数据。

### 2. 第一批覆盖两类题

```text
事实问答 → 答案在一个片段里，考检索准不准、回答对不对
跨段落问答 → 答案要综合多个片段，考召回是否完整、模型是否会整合
```

拒答和引用准确性会在 Day21 继续补齐。

### 3. 为什么用 JSON？

评测数据和代码分离后，可以：

- 单独版本管理和 review；
- 被不同评测工具复用；
- 记录失败 case；
- 在 Prompt、chunk 或模型变化后反复回归。

### 4. Day20 最终要记住什么？

```text
评测集 = RAG 的自动化回归用例库
```

它不是随手写几道示例题，而是覆盖业务题型、期望答案、来源和拒答边界的数据资产。

## Day11–Day20 总结：这一组到底升级了什么？

```text
理解 token / embedding / 幻觉
  → 真实 PDF + 来源
  → 调 chunk 策略
  → 混合检索
  → 查询改写
  → 向量库持久化
  → 图片和重排
  → 手写评测指标
  → LLM 裁判
  → 评测集数据资产
```

Day20 结束时，你不仅会搭 RAG，还应该能解释检索为什么失败、答案从哪里来、质量如何量化，以及后续如何把问题变成可重复的回归用例。
