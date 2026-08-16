# Day21–Day30 详细章节概括：从 RAG 评测进入 Agent 和 LangGraph

这一组的主线是：把评测集补完整、接入可观测和回归实验，再把视角从“最终答案”扩展到 Agent 的行为轨迹，最后开始用 LangGraph 管理分支、循环、状态和工具调用。

## Day21 · 补齐评测集并接入 RAGAS

代码在：[day21/day21_eval_dataset_ragas.py](../day21/day21_eval_dataset_ragas.py)

Day21 做的事情是：**把拒答和引用准确性纳入评测，并第一次接入行业常见的 RAGAS 指标。**

### 1. 补两类最容易被忽略的题

资料外问题：

```python
{
    "question": "LangChain 是哪一年发布的？",
    "reference": "文档未提及，应拒答",
    "expect_source": None,
    "type": "refuse",
    "should_refuse": True,
}
```

引用题则要求答案不仅正确，还要命中期望来源。这样评测集覆盖了事实题、跨段落题、拒答题和引用题。

### 2. 准备 RAGAS 需要的输入

RAGAS 需要把一次问答整理成：

```python
{
    "question": question,
    "answer": answer,
    "contexts": retrieved_contexts,
    "ground_truth": reference,
}
```

`contexts` 是真实召回的文档片段，不能只把最终 Prompt 或假上下文填进去，否则测到的不是实际检索质量。

### 3. 接入忠实度、相关性和上下文精度

```text
faithfulness       → 答案是否忠于召回上下文
answer_relevancy   → 答案是否真正回答问题
context_precision  → 召回内容是否足够相关
```

代码使用 DeepSeek 和本地 embedding 适配 RAGAS，避免把所有能力绑定到 OpenAI。

### 4. Day21 最终要记住什么？

> 拒答题测幻觉底线，引用题测证据可追溯性；RAGAS 只是统一计算工具，单一评测数据源 `eval_set_full.json` 才是核心资产。

## Day22 · 用 LangSmith 看 trace 和在线评估

代码在：[day22/day22_langsmith_eval.py](../day22/day22_langsmith_eval.py)

Day22 做的事情是：**让每次 RAG 调用都留下可视化 trace，并把评测集变成可以在线跑实验的 dataset。**

### 1. 用环境变量打开 trace

```python
os.environ["LANGSMITH_TRACING"] = "true"
os.environ.setdefault("LANGSMITH_PROJECT", "rag-day21")
```

只要配置 `LANGSMITH_API_KEY`，普通 LangChain/LangGraph 调用就会自动上报，不需要在每一行代码中手动插入日志。

### 2. trace 能看见什么？

一次 RAG 请求可以拆成：

```text
用户问题
  → retriever 找到哪些块
  → 上下文拼成什么样
  → Prompt 发给模型什么内容
  → 模型返回什么
```

最终答案错时，trace 可以帮助判断是检索错、上下文拼接错、Prompt 约束失效，还是模型生成错。

### 3. 在线评估和本地指标的区别

本地指标适合快速开发和离线回归；LangSmith dataset + experiment 适合保存版本、比较实验和在网页上查看趋势。

### 4. Day22 最终要记住什么？

> 指标告诉你“结果差不差”，trace 帮你定位“具体哪一步差”。可观测性是调试 AI 应用的基础，不是上线后才临时补的日志。

## Day23 · 做 baseline/candidate 回归实验

代码在：[day23/day23_eval_regression_curve.py](../day23/day23_eval_regression_curve.py)

Day23 做的事情是：**让稳定版本和候选版本在同一评测集上真实运行，再用质量、延迟和错误率判断候选版本是否退化。**

### 1. 两个版本分别代表什么？

```text
baseline → temperature=0，要求基于上下文回答并标来源
candidate → 放松来源和拒答要求，用来暴露回归风险
```

两个版本都走真实的文档、embedding、retriever 和 LLM，而不是写两个假的字符串函数。

### 2. 对比三类结果

```text
质量指标        → 关键词、来源、拒答等是否变差
P50/P99 latency  → 中位数和尾部延迟是否变慢
Error Rate       → 超时、网络和代码异常是否增加
```

回答质量差不等于运行时 Error。模型答错、引用缺失和拒答错误属于质量问题；只有程序抛异常才算 runtime error。

### 3. 为什么要同一份 dataset？

如果 baseline 和 candidate 使用不同问题，结果无法公平比较。固定 dataset 后，Prompt、chunk、模型或代码每次变化都可以画出回归曲线。

### 4. Day23 最终要记住什么？

> 版本升级不能只看一个新例子答得好不好，必须和旧版本在同一套问题上对照，并分别看质量、性能和程序稳定性。

## Day24 · Prompt A/B 和裁判一致性

代码在：[day24/day24_prompt_ab_judge.py](../day24/day24_prompt_ab_judge.py)

Day24 做的事情是：**用实验而不是直觉选择 Prompt，并检查 LLM judge 的判断是否接近人工判断。**

### 1. Prompt A/B 的基本流程

```text
同一份 dataset
  → Prompt A 跑一遍
  → Prompt B 跑一遍
  → 比较关键词、来源、拒答、judge 分数
```

这样可以验证某版 Prompt 是否真的提高了质量，而不是因为某几道题恰好表现好。

### 2. judge 也要和人工对照

```text
人工标签 + LLM judge 分数
  → agreement
  → 找出 judge 和人工意见不一致的 case
```

如果裁判模型把“听起来合理但无上下文依据”的答案判高分，说明裁判 Prompt 或模型还需要校准。

### 3. dataset 和 experiment 的关系

```text
dataset    → 问题、参考答案、人工评分
experiment → 某一版模型/Prompt 在 dataset 上跑出的结果
```

同一个 dataset 上跑多次 experiment，才可以直观比较 A/B。

### 4. Day24 最终要记住什么？

> Prompt 选择是实验问题，judge 可靠性也是实验问题；不要用一份未经校准的模型分数替代人工标准。

## Day25 · 评测 Agent 的行为轨迹

代码在：[day25/day25_agent_trajectory_eval.py](../day25/day25_agent_trajectory_eval.py)

Day25 做的事情是：**从只看 RAG 最终答案，升级到检查 Agent 整个思考—行动过程。**

### 1. RAG 评测看什么？

```text
最终答案有没有关键词
有没有引用来源
该拒答时有没有拒答
```

它关注 Agent 最后“说了什么”。

### 2. Agent 评测看什么？

```text
expected_ok  → 该调用的工具是否调用
forbidden_ok → 禁止的工具是否被调用
completed    → 任务是否完成
step_count   → 是否绕远路或陷入循环
```

例如 Agent 最后说“已提交审批”，但轨迹中实际调用了删除数据库工具，RAG 评测可能通过，Agent 轨迹评测必须失败。

### 3. Day25 最终要记住什么？

> 对 Agent 来说，回答体面不等于行为安全。工具名、工具参数、调用顺序、审批状态和步数都应该进入测试结果。

## Day26 · 生产级失败诊断

代码在：[day26/day26_eval_report_failures.py](../day26/day26_eval_report_failures.py)

Day26 做的事情是：**回答一条失败到底坏在检索、上下文、生成还是拒答，而不是只报告“这题错了”。**

### 1. 先用便宜硬指标分流

```text
refusal_ok
keyword_score
citation_score
```

这些指标测的是字符串或规则，不能直接证明语义正确，但可以把失败先分成“疑似拒答问题、疑似关键词问题、疑似引用问题”。

### 2. 再用 DeepEval 做语义复核

```text
Faithfulness        → 答案是否忠于召回上下文
Answer Relevancy    → 是否答非所问
Contextual Precision → 召回内容是否真正相关
```

代码只有在 live 模式且有真实 `retrieval_context` 时才做二级诊断；缺少参考答案的指标会跳过，而不是用空字符串算出一个假分数。

### 3. Day26 不负责发布判决

Day26 的职责是产出失败证据和根因分布；后面的质量门负责根据证据阻止发布。诊断和门禁拆开，避免一个文件同时做“解释失败”和“决定是否放行”两件事。

### 4. Day26 最终要记住什么？

> 失败诊断要分层：便宜规则负责分流，LLM 评估负责语义复核，最终结论必须保留证据和不确定性。

## Day27 · LangGraph 线性图基础

代码在：[day27/day27_langgraph_basics.py](../day27/day27_langgraph_basics.py)

Day27 做的事情是：**从 LCEL 的一条直线进入 LangGraph，先理解 State、Node、Edge 三个最小组件。**

### 1. 定义贯穿全流程的 State

```python
class DraftState(TypedDict):
    topic: str
    draft: str
    polished: str
```

State 是图中所有节点共享的数据。节点不需要互相直接调用，而是读取 state 并返回要更新的字段。

### 2. Node 和 Edge 分别是什么？

```text
Node → 一个处理函数，读 state，返回部分更新
Edge → 连接节点，规定下一步走哪里
START → 图的入口
END   → 图的出口
```

最小流程类似：

```text
START → draft_node → polish_node → END
```

### 3. 为什么今天只做线性图？

线性图和 LCEL 暂时没有明显差别。Day27 先让你熟悉图的骨架，真正需要 LangGraph 的原因会在 Day28 出现：按条件分支、循环和保存状态。

### 4. Day27 最终要记住什么？

> LangGraph 不是“更复杂的 Prompt”，而是用 State、Node 和 Edge 描述一个可执行流程。

## Day28 · LangGraph 的分支和循环

代码在：[day28/day28_langgraph_basics.py](../day28/day28_langgraph_basics.py)

Day28 做的事情是：**让图根据 state 走不同路径，并把条件边指回前面节点形成循环。**

### 1. 用条件边做分支

```text
校验成功 → 检索
校验失败 → 拒绝
```

`conditional_edges` 会读取当前 state，返回下一个节点名称；这比在一个大函数里写很多嵌套 `if` 更容易观察和测试。

### 2. 用回边做循环

```text
agent → 有 tool_calls → tools → agent
      → 没有 tool_calls → END
```

图中的回边就是 Agent 循环的结构来源。代码使用 `recursion_limit` 防止模型或工具一直循环。

### 3. 它和 Day5/Day10 的关系

Day5 手写了两轮工具调用，Day10 手写了 while 风格 Agent loop。Day28 用 LangGraph 把同一个逻辑显式画成状态图，让框架负责状态传递和循环边界。

### 4. Day28 最终要记住什么？

```text
线性流程 → LCEL 足够
分支/循环/状态 → LangGraph 更合适
```

## Day29 · State reducer：并发更新如何合并

代码在：[day29/day29_state_reducer.py](../day29/day29_state_reducer.py)

Day29 做的事情是：**解决多个节点返回结果时，更新如何合并进同一个 state 的问题。**

### 1. 默认规则是覆盖

```python
state = {"items": ["a"]}
node_return = {"items": ["b"]}
```

默认情况下，结果是：

```python
{"items": ["b"]}
```

旧值被新值替换。单线程线性图可能没问题，但累加列表时会丢数据。

### 2. 用 reducer 声明合并规则

```python
class State(TypedDict):
    items: Annotated[list[str], operator.add]
```

这样新旧值会拼接：

```text
["a"] + ["b"] → ["a", "b"]
```

消息状态还可以使用 `add_messages`，自定义字段则可以写自己的合并函数。

### 3. 为什么 fan-out 必须理解 reducer？

多个并行节点同时写同一字段时，没有 reducer 可能直接触发 `InvalidUpdateError`；手动写 `state["x"] += ...` 又可能在真正并发时静默丢数据。

### 4. Day29 最终要记住什么？

> State 不只是一个字典，字段还需要定义更新语义：覆盖、累加、消息合并或自定义合并。

## Day30 · ReAct Agent：思考、调用工具、继续思考

代码在：[day30/day30_react_agent.py](../day30/day30_react_agent.py)

Day30 做的事情是：**把 Day5/Day10 的工具循环正式搭成 LangGraph Agent，并同时理解一行封装版本。**

### 1. 手搭 ReAct 图

```text
agent 节点：调用模型
  ↓ 有 tool_calls？
tools 节点：执行工具
  ↓ ToolMessage
回到 agent
  ↓ 没有 tool_calls
END
```

代码使用 `MessagesState` 保存消息，用 `ToolNode` 执行工具，用 `tools_condition` 判断下一步是回到 Agent 还是结束。

### 2. 和 Day5 手写流程有什么变化？

Day5 由程序员手动维护 `messages` 列表并执行每个工具；Day30 把这个循环拆成图节点，让状态、工具节点、条件边和结束条件更清楚。

### 3. 再看一行版 Agent

```python
agent = create_react_agent(model=llm, tools=[...])
```

封装版本适合快速开发；手搭版本适合调试、加入审批、增加特殊分支和面试解释。LangChain v1 的现代入口是 `langchain.agents.create_agent`，底层仍然是类似的图式编排。

### 4. Day30 最终要记住什么？

> ReAct 的本质是“模型判断 → 工具执行 → 结果回模型”的有条件循环，不是一句神秘 Prompt，也不是模型直接拥有执行权限。

## Day21–Day30 总结：这一组到底完成了什么？

```text
补齐评测集
  → RAGAS / LangSmith
  → baseline 回归
  → Prompt A/B
  → Agent 轨迹评测
  → 失败诊断
  → State / Node / Edge
  → 分支与循环
  → reducer
  → ReAct Agent
```

Day30 结束时，你应该能区分三件事：RAG 评估最终答案，Agent 评估行动轨迹，LangGraph 负责把复杂行动流程变成可控的状态图。
