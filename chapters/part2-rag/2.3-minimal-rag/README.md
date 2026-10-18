# L2.3 最小 RAG · Gate（原 2.3）

[全书目录](../../README.md) · [上一章 2.2](../2.2-embed-retrieve/README.md) · [下一章 2.4](../2.4-eval-seed/README.md)

- **能力**：检索 → 拼带来源的上下文 → 生成 → 引用/拒答；无证据不调用模型。
- **v2 路径**：L2.3 / 核心（Gate；最小 RAG）
- **前置**：2.2（向量化与召回）。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 故障分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `minimal_rag.py`。
- **验收命令**：

```bash
python chapters/part2-rag/2.3-minimal-rag/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

“检索到了”不等于“回答有依据”。最小 RAG 最容易出这些事：

- 没检索到也调用模型，模型开始编；
- 上下文拼了来源，但回答的 `sources` 是模型编的；
- 检索/模型异常直接崩，用户看到 500；
- 上下文超预算，塞爆请求或截断关键事实；
- 拒答时仍附来源，制造“有证据”的假象。

这个 gate 用假检索/假模型，把 RAG 拆成 **上下文、来源、拒答、失败出口** 四件事。

## 任务

实现 `gate/starter.py` 的两个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `format_context` | 每段加 `[source]` 标记；按预算只放得下的片段；空列表返回 `""` |
| `answer_with_rag` | 检索 → 拼上下文 → 调模型 → 返回 answer/sources/refused/error |

关键口径：

- 空问题 -> `ValueError`。
- 无检索结果 -> `refused=True`，`answer="文档中没有提到。"`，**不调用** `chat_fn`。
- `sources` 来自实际进入上下文的片段，去重、按出现顺序。
- 检索异常 -> `error="retrieval_error"`；模型超时 -> `timeout`；其他异常 -> `model_error`；空回答 -> `empty_response`。
- `max_context_chars` 预算包含 `[source]\n` 前缀和块间分隔符；放不下的片段不进入上下文，也不进入 `sources`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 无检索结果 | 拒答，不调用模型 |
| 2 | 检索函数抛异常 | `retrieval_error`，不崩 |
| 3 | 模型超时 | `timeout`，不崩 |
| 4 | 模型返回空白 | `empty_response` |
| 5 | 上下文预算只够第一段 | `sources` 只有第一段 |
| 6 | 两段同来源 | `sources` 去重 |
| 7 | 空问题 | `ValueError` |
| 8 | 片段缺 text/source | `ValueError` |

## 验收标准

`gate_check.py` 的 10 项全部 PASS：

- 上下文格式/非法输入；有证据、无证据、空问题。
- 检索异常、模型超时、空回答、预算、来源去重。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么无证据时要“不调用模型”，而不是让模型自己判断？
2. `sources` 应该由谁生成：模型还是程序？为什么？
3. 上下文预算应该包含来源标记吗？不计入会怎样？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（10/10）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 2.3
```

对照时只回答：

1. 参考实现用 LCEL 字典并行组装 context/question；你的 gate 在哪一步做同样的事？
2. 参考实现的 prompt 要求“没有就说不知道”，但回答不带来源；这和本 gate 的 `sources` 差在哪？
3. 参考实现没有预算裁剪；把 `max_context_chars` 加进去，需要改哪几处？

## 概念地图

- **RAG 四层**：召回、上下文、生成、拒答/引用；答错时先定位层。
- **上下文预算**：片段、来源标记、分隔符都占 token；超预算要裁剪。
- **程序生成来源**：`sources` 应来自进入上下文的片段，不应让模型自由编。
- **无证据拒答**：没有候选就不调用模型，省钱且避免幻觉。
- **可读失败**：检索/模型异常转成 `error`，让上层降级。

## 边界

- gate 用假检索/假模型，不验证真实 RAG 质量。
- 通过 gate 只证明上下文/引用/拒答结构正确。
- MMR、FAISS、真实 prompt 效果见参考实现；评测见 2.9。
