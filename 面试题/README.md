# 小林面试笔记 · 大模型面试题（98 题）

> 来源：https://xiaolinnote.com/ai/  
> 抓取时间：2026-09-21  
> 共 5 个专题、98 道题，按原网站结构分类。每题收录「面试现场复盘 + 💡简要回答 + 📝详细解析 + 🎯面试总结」，LangChain 专题另含 📚参考资料。  
> 说明：正文配图未复制，需要时请打开对应原页面查看。

---

## 专题总览

| # | 专题 | 题量 | 笔记文件 | 原站专题页 |
| --- | --- | --- | --- | --- |
| 1 | Agent | 24 | [01-Agent面试题.md](01-Agent面试题.md) | [原站](https://xiaolinnote.com/ai/agent/agent_info.html) |
| 2 | RAG | 21 | [02-RAG面试题.md](02-RAG面试题.md) | [原站](https://xiaolinnote.com/ai/rag/rag_info.html) |
| 3 | LLM 工具调用 | 18 | [03-LLM工具调用面试题.md](03-LLM工具调用面试题.md) | [原站](https://xiaolinnote.com/ai/tools/tools_info.html) |
| 4 | 大模型工程 | 23 | [04-大模型工程面试题.md](04-大模型工程面试题.md) | [原站](https://xiaolinnote.com/ai/llm/llm_info.html) |
| 5 | LangChain 框架 | 12 | [05-LangChain框架面试题.md](05-LangChain框架面试题.md) | [原站](https://xiaolinnote.com/ai/langchain/langchain_info.html) |
| — | **合计** | **98** | — | — |

---

## 题目索引

### 1. Agent（24 题）

> 笔记文件：[01-Agent面试题.md](01-Agent面试题.md) ｜ 原站专题页：https://xiaolinnote.com/ai/agent/agent_info.html

- [1. 什么是 Agent？与大模型有什么本质不同？](01-Agent面试题.md#q1)
- [2. Agent 的基本架构由哪些核心组件构成？](01-Agent面试题.md#q2)
- [3. Workflow，Agent，Tools 这三个的概念和区别介绍一下？](01-Agent面试题.md#q3)
- [4. 了解哪些其他的 Agent 设计范式？Agent 和 Workflow 的区别是什么？](01-Agent面试题.md#q4)
- [5. Agent 推理模式有哪些？ReAct 是啥？具体是怎么实现的？](01-Agent面试题.md#q5)
- [6. ReAct、Plan-and-Execute、Reflection 三种范式有什么核心区别？实际项目中该如何选型？](01-Agent面试题.md#q6)
- [7. 复杂任务怎么做的任务拆分？为什么要拆分？效果如何提升？](01-Agent面试题.md#q7)
- [8. 请你介绍一下 AI Agent 的记忆机制，并说明在实际开发中应该如何设计记忆模块？](01-Agent面试题.md#q8)
- [9. Agent 的长短期记忆系统怎么做的？记忆是怎么存的？粒度是多少？怎么用的？](01-Agent面试题.md#q9)
- [10. 什么是 Multi-Agent？](01-Agent面试题.md#q10)
- [11. 说说 Single-Agent 和 Multi-Agent 的设计方案？](01-Agent面试题.md#q11)
- [12. Agent 记忆压缩通常有哪些方法？](01-Agent面试题.md#q12)
- [13. 在工程实践中，为什么有时候选择「手搓」Agent，而不是直接用成熟框架？](01-Agent面试题.md#q13)
- [14. 如何赋予 LLM 规划能力？](01-Agent面试题.md#q14)
- [15. 讲讲 Agent 的反思机制？为什么要用反思？具体怎么实现？](01-Agent面试题.md#q15)
- [16. 如何设计多 Agent 的协作与动态切换机制？](01-Agent面试题.md#q16)
- [17. Agent 的上下文工程怎么设计？](01-Agent面试题.md#q17)
- [18. Agent 的多轮对话状态如何管理？如何防止跑偏并支持中断恢复？](01-Agent面试题.md#q18)
- [19. 如何评估一个 Agent 的效果？评测集和指标怎么设计？](01-Agent面试题.md#q19)
- [20. Agent 为什么会出现路径震荡、重复调用和死循环？怎么检测和治理？](01-Agent面试题.md#q20)
- [21. 线上 Agent 延迟明显升高时，如何通过 Trace 定位和优化？](01-Agent面试题.md#q21)
- [22. Multi-Agent 系统如何处理子 Agent 超时、失联和并发修改冲突？](01-Agent面试题.md#q22)
- [23. Agent 的「任务幻觉」是什么？如何避免没有执行工具却声称任务已经完成？](01-Agent面试题.md#q23)
- [24. 大模型或 Agent 连接数据库时，如何防止越权、敏感数据泄漏和查询幻觉？](01-Agent面试题.md#q24)

### 2. RAG（21 题）

> 笔记文件：[02-RAG面试题.md](02-RAG面试题.md) ｜ 原站专题页：https://xiaolinnote.com/ai/rag/rag_info.html

- [1. 什么是 RAG？详细描述一个完整 RAG 系统的工作流程？](02-RAG面试题.md#q1)
- [2. 大模型的 RAG 主要用来解决什么问题？](02-RAG面试题.md#q2)
- [3. 相比直接微调 LLM，RAG 解决了什么问题？微调和 RAG 各自的优劣势是什么？](02-RAG面试题.md#q3)
- [4. RAG 中的文档是怎么存的？粒度是多大？详细说说文档切割（Chunking）策略？](02-RAG面试题.md#q4)
- [5. 怎么规避语义被切割掉的问题？](02-RAG面试题.md#q5)
- [6. 在 RAG 中 Embedding 究竟是什么？如何选择和评估一个 Embedding 模型？](02-RAG面试题.md#q6)
- [7. Embedding 有哪几种算法你了解过吗？](02-RAG面试题.md#q7)
- [8. 什么是向量数据库？有没有做过向量数据库的对比选型？](02-RAG面试题.md#q8)
- [9. 讲讲你用的向量数据库？数据量级是多大？性能如何？遇到过性能瓶颈吗？](02-RAG面试题.md#q9)
- [10. 你使用 RAG 给大模型一个输入，系统是怎样的工作流程？](02-RAG面试题.md#q10)
- [11. 请你介绍一下向量检索和关键词检索的区别？](02-RAG面试题.md#q11)
- [12. 如何润色用户的 Query（Query Rewrite）？目的是什么？](02-RAG面试题.md#q12)
- [13. 什么是多路召回？具体怎么做？](02-RAG面试题.md#q13)
- [14. RAG 检索优化策略有哪些？](02-RAG面试题.md#q14)
- [15. 了解哪些更复杂的 RAG 范式？](02-RAG面试题.md#q15)
- [16. 在什么场景下，你会选择使用图数据库来增强传统的向量检索？](02-RAG面试题.md#q16)
- [17. 如何规避 RAG 系统中大模型的幻觉？](02-RAG面试题.md#q17)
- [18. 怎么量化你的 RAG 效果？](02-RAG面试题.md#q18)
- [19. RAG 知识库如何实现动态与持续更新？](02-RAG面试题.md#q19)
- [20. 在实际落地中，你觉得 RAG 最难的地方是哪里？](02-RAG面试题.md#q20)
- [21. 不同来源的文档发生知识冲突时，RAG 应该信谁？](02-RAG面试题.md#q21)

### 3. LLM 工具调用（18 题）

> 笔记文件：[03-LLM工具调用面试题.md](03-LLM工具调用面试题.md) ｜ 原站专题页：https://xiaolinnote.com/ai/tools/tools_info.html

- [1. 什么是 Function Calling？原理是什么？](03-LLM工具调用面试题.md#q1)
- [2. LLM 是如何学会调用外部工具的？](03-LLM工具调用面试题.md#q2)
- [3. 大模型的 Function Call 能力是怎么训练出来的？](03-LLM工具调用面试题.md#q3)
- [4. 什么是 MCP（模型上下文协议）？讲讲它的核心内容？](03-LLM工具调用面试题.md#q4)
- [5. MCP 由哪几部分组成？](03-LLM工具调用面试题.md#q5)
- [6. MCP 和 Function Calling 有什么区别？有没有实际跑过 MCP？](03-LLM工具调用面试题.md#q6)
- [7. Function Calling 也属于工具调用，请问什么场景下使用 Function Calling，什么场景下使用 MCP？](03-LLM工具调用面试题.md#q7)
- [8. 为什么有些特定的推理模型不支持 MCP 协议？](03-LLM工具调用面试题.md#q8)
- [9. Skill 是什么？](03-LLM工具调用面试题.md#q9)
- [10. MCP 和 Agent Skill 的区别是什么？](03-LLM工具调用面试题.md#q10)
- [11. Function Calling、Skill、MCP 这三个有什么区别？](03-LLM工具调用面试题.md#q11)
- [12. 什么是 A2A 协议？它和 MCP 协议的区别是什么？](03-LLM工具调用面试题.md#q12)
- [13. MCP 协议通常采用什么通信方式？](03-LLM工具调用面试题.md#q13)
- [14. 说说 WebSocket 和 SSE 通信的区别及局限性？](03-LLM工具调用面试题.md#q14)
- [15. 为什么要用 WebRTC 协议？它和 WebSocket 在 AI 对话流中的核心差异是什么？](03-LLM工具调用面试题.md#q15)
- [16. 有没有用过大模型的网关框架？网关层解决了什么问题？](03-LLM工具调用面试题.md#q16)
- [17. 工具很多时，Agent 如何做 Tool Routing，减少 Token 并避免选错工具？](03-LLM工具调用面试题.md#q17)
- [18. 工具调用格式非法、参数错误、超时或失败时，Agent 如何容错？](03-LLM工具调用面试题.md#q18)

### 4. 大模型工程（23 题）

> 笔记文件：[04-大模型工程面试题.md](04-大模型工程面试题.md) ｜ 原站专题页：https://xiaolinnote.com/ai/llm/llm_info.html

- [1. 什么是大语言模型？和传统 NLP 模型有什么区别？](04-大模型工程面试题.md#q1)
- [2. 讲讲 Transformer 架构基本原理？Encoder 和 Decoder 是什么？](04-大模型工程面试题.md#q2)
- [3. 多头注意力（MHA）有哪些局限？MQA、GQA、Flash Attention 怎么解决？](04-大模型工程面试题.md#q3)
- [4. 大模型的位置编码是干什么用的？sin/cos、RoPE、ALiBi 有什么区别？](04-大模型工程面试题.md#q4)
- [5. 什么是大模型项目的分词器？原理是什么？](04-大模型工程面试题.md#q5)
- [6. 大模型是怎么训练出来的？](04-大模型工程面试题.md#q6)
- [7. 什么是 Scaling Law？大模型的「涌现能力」是怎么回事？](04-大模型工程面试题.md#q7)
- [8. 大模型微调的方案有哪些？](04-大模型工程面试题.md#q8)
- [9. 请讲一下 LoRA 技术，除了减少参数量，它还有哪些优点？](04-大模型工程面试题.md#q9)
- [10. SFT 之后还有哪些 Post-Training？RLHF、DPO、GRPO、拒绝采样什么关系？](04-大模型工程面试题.md#q10)
- [11. 大模型的 DPO 和 PPO 的区别是什么？](04-大模型工程面试题.md#q11)
- [12. 大模型生成文本时的解码策略有哪些？贪心、Beam Search、采样分别什么时候用？](04-大模型工程面试题.md#q12)
- [13. 大模型的参数：温度值、Top-P、Top-K 分别是什么？各个场景下的最佳设置是什么？](04-大模型工程面试题.md#q13)
- [14. KV Cache 是什么？Prompt Caching 的原理是什么？](04-大模型工程面试题.md#q14)
- [15. 大模型量化是什么？INT8/INT4/AWQ/GPTQ 怎么选？](04-大模型工程面试题.md#q15)
- [16. 如何写好 Prompt？分享下 Prompt 工程实践经验？](04-大模型工程面试题.md#q16)
- [17. 什么是 CoT？为啥效果好？它有什么缺点或局限性？](04-大模型工程面试题.md#q17)
- [18. 大模型为什么会出现幻觉？怎么缓解？](04-大模型工程面试题.md#q18)
- [19. MoE 混合专家模型是什么？DeepSeek V3、Qwen 为什么用 MoE？](04-大模型工程面试题.md#q19)
- [20. 大模型部署有哪些主流方案？vLLM、TGI、llama.cpp、SGLang 实际项目里怎么选？](04-大模型工程面试题.md#q20)
- [21. 大模型能力评测指标有哪些？](04-大模型工程面试题.md#q21)
- [22. 对比使用过哪些主流大模型？你们项目中最终选用了哪个模型？为什么？](04-大模型工程面试题.md#q22)
- [23. 为什么长上下文会出现 Lost in the Middle？上下文窗口越大越好吗？](04-大模型工程面试题.md#q23)

### 5. LangChain 框架（12 题）

> 笔记文件：[05-LangChain框架面试题.md](05-LangChain框架面试题.md) ｜ 原站专题页：https://xiaolinnote.com/ai/langchain/langchain_info.html

- [1. 你了解过哪些 AI Agent 开发框架？](05-LangChain框架面试题.md#q1)
- [2. 如何理解 LangChain 中的 Chain？](05-LangChain框架面试题.md#q2)
- [3. LangChain 的底层架构与实现原理是什么？](05-LangChain框架面试题.md#q3)
- [4. 使用 LangChain 构建 Agent 的核心步骤是什么？](05-LangChain框架面试题.md#q4)
- [5. 在 LangChain 中，如何为 Agent 注册工具？](05-LangChain框架面试题.md#q5)
- [6. LangChain 如何实现短期记忆和长期记忆？](05-LangChain框架面试题.md#q6)
- [7. LangChain 和 LlamaIndex 有什么区别？](05-LangChain框架面试题.md#q7)
- [8. 请你谈谈 LangChain4j 这类 Java 生态的 LangChain 衍生框架，主要帮开发者解决了哪些核心问题？它的核心适用场景是什么？](05-LangChain框架面试题.md#q8)
- [9. 请你详细说说 LangChain 和 LangGraph 的核心区别是什么？](05-LangChain框架面试题.md#q9)
- [10. LangGraph 相比于 LangChain 有哪些核心优势？更适配哪些 Agent 场景？](05-LangChain框架面试题.md#q10)
- [11. LangChain 大版本升级有哪些核心变化？](05-LangChain框架面试题.md#q11)
- [12. Deep Research 的实现逻辑和适用场景是什么？](05-LangChain框架面试题.md#q12)

---

## 使用说明

- 每个题目在笔记文件中都带有 `<a id="qN"></a>` 锚点，点击上方索引即可跳转到对应题目。
- 同一专题内题目按原站顺序排列，便于与网页对照阅读。
- 每题标题下方都有「> 原文链接：…」，可直接跳转到该题网页原文。
- 代码块、表格均按原文保留；原文中的配图未复制，需要时请打开对应原页面查看。
