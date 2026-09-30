# 8.7 API、SSE 与端到端：用户到底收到了什么

[全书目录](../../README.md) · [上一章 8.6](../8.6-agent-trajectory-testing/README.md) · [下一章 8.8](../8.8-security-resilience-perf/README.md)

- **目标**：端到端测试要覆盖网络契约和用户实际收到的事件序列。
- **前置**：8.6（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.7-api-sse-e2e`，进入 `.build/quality/8.7-api-sse-e2e/ai-testing` 后运行 `python -m pytest -q`

## 问题

接口内部函数通过测试，网页仍可能把两个片段重复显示，或遇到断连后拿半个答案当完整结果。端到端验证把观察点移到真实交付边界。

## 概念

SSE 用事件流交付信息；`StreamEvent` 是解析后的事件（事件名、数据、可选 id）；`combine_text` 把 token/message 事件的文本按顺序拼成完整回答。事件解析和业务响应校验职责不同。本章代码不判断流是否完整：连接中途断开时，`combine_text` 仍会返回已收到的部分，调用方要自己确认收到了结束标记。

## 流程

1. 取得响应体文本（真实 HTTP 响应，或测试里手写的字符串）。
2. `parse_sse` 按空行切分事件，读取 `event:`、`id:`、`data:`；多行 `data:` 用换行连接。
3. `combine_text` 按顺序拼接 token/message 事件的文本；`data` 是 JSON 对象时取 `text` 字段。
4. 非流式接口的 JSON 响应用 `validate_e2e_response` 校验：先套用 8.3 的 ChatResponse 契约，再要求 `request_id`（若出现）是字符串。

```text
流式：HTTP 响应体 → parse_sse → combine_text → 断言最终文本
非流式：HTTP JSON → validate_e2e_response → 断言字段
```

## 衔接与新增

章节 8.6 验证 Agent 轨迹；章节 8.7 站在 HTTP 边界：用 `validate_e2e_response` 校验旗舰后端（7.8 / step2）`/chat` 的 JSON 响应，并提供 SSE 解析工具。旗舰后端和前端（7.8 / step3）目前都不使用流式输出，SSE 解析器用于以后接入的流式接口，练习时用手写事件串。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/api_e2e.py` | 新增 | SSE 解析、token 合并和 E2E 响应校验 |
| `tests/test_api_e2e.py` | 新增 | 验证事件名、事件 ID、多行数据、`data:` 空白和 `request_id` 校验 |

## 代码导读

api_e2e.py 先读 StreamEvent，再读解析、拼接与响应校验；对照测试中的事件名、事件 ID 和多行数据。

实现文件：

- [api_e2e.py](src/ai_testing/api_e2e.py)

## 练习

把一个事件拆成两段，或删掉结尾的事件，预测解析结果：`combine_text` 不去重，也不检查结尾，会照常返回已收到的文本。写出你会怎样检测被截断的流（例如约定一个 `done` 事件，并在测试里断言它存在）。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.7-api-sse-e2e
cd .build/quality/8.7-api-sse-e2e/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

解析器只处理手写的事件字符串，不能证明浏览器、代理和真实上游连接稳定；断连、超时和认证需要在受控的端到端环境里另行验证。
