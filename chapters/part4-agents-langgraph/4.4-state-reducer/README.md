# 4.4 状态合并与 Reducer：并行结果如何留下来

[全书目录](../../README.md) · [上一章 4.3](../4.3-branch-loop/README.md) · [下一章 4.5](../4.5-react-agent/README.md)

- **目标**：理解节点返回的字段怎样合并进 state，会用 reducer 处理累加与并发写入。
- **前置**：4.3。
- **环境**：离线，不调用模型。
- **命令**：`python tools/run_chapter.py 4.4`

## 问题

节点 `return` 一个 dict，它是怎么并进整张图的 state 的？默认规则是覆盖：`{"x": 新值}` 会直接替换旧值。单线程的线性图没问题，但一旦要累加（把每步结果 append 进列表），或者多个节点在同一步写同一个字段（fan-out），覆盖就会丢数据，甚至让图直接报错。

## 概念

- **reducer**：字段的合并函数，用 `Annotated[类型, reducer]` 声明。LangGraph 每次拿“旧值 + 节点新返回值”交给 reducer，得到合并后的新值。
- 常见 reducer：不写 = 覆盖（后写入的胜出）；`operator.add` = 列表拼接或数字相加；`add_messages` = 消息专用合并；也可以自定义函数。
- **并发写同一字段必须有 reducer**：没有 reducer 时，框架直接抛 `InvalidUpdateError`，不是静默丢数据，而是图跑不起来。
- **reducer 只保证不丢，不保证有序**：并发分支完成的顺序没有定义；要稳定顺序，让产出带序号、消费端按序号排序。
- `MessagesState` 不是魔法，就是 `{"messages": Annotated[list, add_messages]}`。

## 流程

`state_reducer.py` 的五个演示：

1. 【一】默认覆盖与 `operator.add` 累加的对比。
2. 【二】fan-out：三个分支写同一字段，无 reducer 时报错，加上 `operator.add` 后正常。
3. 【二·补】想要有序：产出带序号，最后按序号排序。
4. 【三】`add_messages`：`MessagesState` 背后的合并逻辑。
5. 【三·补】自定义 reducer：只保留最近 N 条的滑动窗口。

## 代码导读

[state_reducer.py](state_reducer.py)：先看 `OverwriteState` 与 `AccumulateState` 两个 state 的区别，再看 `demo_fanout` 里为什么会抛 `InvalidUpdateError`，最后看 `keep_last_n`。

## 练习

1. 运行后对照输出，解释【一】里覆盖与累加的结果为什么不同。
2. 去掉 fan-out 里字段的 `Annotated[..., operator.add]`，确认会抛出 `InvalidUpdateError`。
3. 写一个自定义 reducer：合并字典，同名键取较大值。
4. 学完 4.14 后回来，把它的 fan-out 字段改成 `Annotated[list, operator.add]`，去掉手动拼接，验证并发下不再丢数据。

## 运行与边界

- 本章只演示合并规则，不涉及真实的并发执行时序。
- 4.5 的 `MessagesState` 就是 `add_messages` 的封装；4.14 的并行分支要用这里的 `operator.add`。
