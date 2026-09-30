# 4.11 流式与人工介入：暂停在需要决定的位置

[全书目录](../../README.md) · [上一章 4.10](../4.10-checkpoint-context/README.md) · [下一章 4.12](../4.12-tool-safety-search/README.md)

- **目标**：用流式输出观察图的每一步，用 `interrupt` 在高风险动作前暂停等人确认。
- **前置**：4.10。
- **环境**：离线，不调用模型；HITL 部分需要你在终端输入 `yes` / `no`。
- **命令**：`python tools/run_chapter.py 4.11`

## 问题

长任务让用户干等，体验差，也看不出走到了哪一步。另一方面，删除数据、发邮件、付款这类高风险动作，不能让模型自己拍板，应先暂停，把动作交给人确认。

## 概念

- **streaming**：`app.stream()` 边执行边吐出每一步（走到哪个节点、state 怎么变），既改善体验，也方便观察。`stream_mode="updates"` 返回每个节点的增量更新。
- **`interrupt()`**：在节点里调用，图暂停并把待确认的动作抛给人；`Command(resume=值)` 恢复，`interrupt()` 处得到的就是这个值。
- **HITL 依赖 checkpointer**：暂停要能存档、再恢复，所以 `compile` 必须传 `checkpointer`。“暂停”存在检查点里，不在进程里：图停在 `interrupt` 之后，`invoke` 已经返回，等待 `input()` 的只是普通 Python 代码。所以审批人也可以是另一个进程或网页（capstone 的 HITL API 就是这样做的）。
- **两道防线**：`interrupt` 等人审批，加上危险工具只做模拟，绝不接真实的删除、发送、支付权限。

## 流程

1. `demo_streaming`：流式打印每个节点的增量更新，能看到图停在哪一步等人。
2. `run_hitl`：第一次 `invoke` 运行到 `interrupt` 停下，返回里带 `__interrupt__` → 终端询问你 → 用 `Command(resume=你的输入)` 再 `invoke` 一次继续。输入 `yes` 才执行（模拟）删除，否则取消。
3. 依次审批两个任务（`report.docx`、`db_backup.sql`）。

## 代码导读

[streaming_hitl.py](streaming_hitl.py)：先看 `confirm` 节点里的 `interrupt` 和返回值，再看 `run_hitl` 怎样两次调用同一个 `thread_id`。

## 练习

1. 对第一个任务输入 `yes`，对第二个输入 `no`，比较结果。
2. 把 `confirm` 改成“只有金额大于 1000 才 `interrupt`，否则直接放行”。
3. 用不同的 `thread_id` 同时开两个任务，验证它们互不影响。

## 运行与边界

- 删除是模拟的，只修改 state，不碰真实文件。
- 内存检查点不跨进程；有副作用的工具在恢复后可能重复执行，需要幂等性（5.4、7.4）。
