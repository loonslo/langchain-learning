# 4.8 规划与执行：让计划进度成为显式状态

[全书目录](../../README.md) · [上一章 4.7](../4.7-structured-routing/README.md) · [下一章 4.9](../4.9-observability/README.md)

- **目标**：了解主流的 Agent 规划范式，并动手实现“先规划、再逐步执行”的 Plan-and-Execute。
- **前置**：4.5。
- **环境**：【一】只打印文字，离线；【二】调用真实模型（`DEEPSEEK_API_KEY`）。
- **命令**：`python tools/run_chapter.py 4.8`

## 问题

ReAct 走一步看一步，灵活但费 token，也不容易审计。对多步、确定性强的任务，可以先让模型把任务拆成有序的步骤清单，再逐条执行：计划显式、过程可控、便于审计。

## 概念

- **范式速查**：ReAct（边想边做）、Plan-and-Execute（先规划再执行）、Reflexion（反思后重试）、ReWOO（先规划并引用变量，减少调用）、Tree of Thoughts（多路径搜索）。何时用哪个，看任务是否可预先拆解、对成本和可控性的要求。
- **Plan-and-Execute**：planner 出清单，executor 按游标逐步执行，条件边控制“还有没有下一步”。
- **优点与缺点**：更可控、更可审计，计划和进度都是显式状态；缺点是计划一旦错了后面全错，进阶做法是在执行中重新规划（replan）。
- **多 Agent 框架的定位**（LangGraph、AutoGen、CrewAI、A2A）在文件里有一张速查表；多 Agent 协作在 4.14。

## 流程

1. 【一】打印规划范式速查、多 Agent 框架定位，以及一个 supervisor 编排骨架。
2. 【二】`planner` 把任务拆成步骤清单，`executor` 按 `cursor` 逐步执行，`has_more` 决定继续还是结束；`recursion_limit` 给足，避免步骤多时被安全阀拦下。

## 代码导读

[plan_and_execute.py](plan_and_execute.py)：先浏览 `PLANNING_PARADIGMS` 速查表，再看 `State`（计划、已完成、游标）和 `planner`、`executor`、`has_more` 三个函数。

## 练习

1. 运行【二】，观察计划清单和每一步的执行输出。
2. 手动把某一步的计划改错，看后面的步骤会怎样受影响，体会“计划错了全错”。
3. 设计一个 replan 节点：某步失败时重新生成剩余计划。

## 运行与边界

- 【二】调用真实模型并产生费用；规划质量取决于模型，需要评测验证。
- 速查表是学习用的概括，各框架的能力会变化，选型见 4.15。
