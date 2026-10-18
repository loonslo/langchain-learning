# L2.6 查询改写 · Gate（原 2.9）

[全书目录](../../README.md) · [上一章 2.8](../2.8-hybrid-search/README.md) · [下一章 2.10](../2.10-chroma-persist/README.md)

- **能力**：构造改写 prompt；解析多行查询；空输出/模型异常时回退原问题。
- **v2 路径**：L2.6 / 核心（Gate；查询改写）
- **前置**：2.4（切分策略）、2.2（召回）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 失败分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `query_rewrite.py`。
- **验收命令**：

```bash
python chapters/part2-rag/2.9-query-rewrite/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

改写是“用 LLM 改善召回”，但也会引入新失败：

- 模型输出编号/解释/空行，直接拼进检索；
- 改写结果重复原问题，白多调一次模型；
- 模型超时/空输出，整条链路中断；
- 改写条数不设上限，成本和延迟失控；
- 改写引入噪声，把无关内容召回。

这个 gate 用脚本化 LLM，把“prompt → 解析 → 回退 → 截断”做成可验证链路。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `build_rewrite_prompt` | 包含原问题/历史；要求一行一条、不要编号 |
| `parse_rewrites` | 去编号、去空、去重、保序、限制条数 |
| `rewrite_query` | 调模型 → 解析 → 原问题在前 → 失败回退 |

关键口径：

- 空问题、`max_queries < 1` -> `ValueError`。
- `queries[0]` 永远是原问题。
- 模型空输出/解析后没有新查询 -> `queries=[原问题]`，`error="empty_rewrite"`。
- 模型异常 -> `queries=[原问题]`，`error="model_error"`。
- 正常结果去重后截断到 `max_queries`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 模型输出带 `1.`/`2)`/`-` 编号 | 解析后去掉编号 |
| 2 | 重复行 | 去重 |
| 3 | 超过 max_queries | 截断 |
| 4 | 空输出 | 回退原问题，`empty_rewrite` |
| 5 | 只输出原问题 | 回退原问题，`empty_rewrite` |
| 6 | 模型超时 | 回退原问题，`model_error` |
| 7 | 空问题/max_queries=0 | `ValueError` |

## 验收标准

`gate_check.py` 的 9 项全部 PASS：

- prompt、解析/去重、条数限制。
- 正常改写、截断、空输出、无新查询、模型异常、参数校验。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么改写结果要把原问题放第一位？
2. 改写条数上限应该由什么决定？
3. 改写后召回变多，怎么判断是“更全”还是“更多噪声”？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（9/9）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 2.9
```

对照时只回答：

1. 参考实现用 `MultiQueryRetriever.from_llm`，它怎么解析模型输出？你的解析器补了什么？
2. 参考实现的 HyDE 是“先答再检索”，和 Multi-Query 的差别在哪？
3. 参考实现没有条数/异常回退；上生产要先补哪几层？

## 概念地图

- **Multi-Query**：一题多问，覆盖不同说法；代价是多调 LLM。
- **HyDE**：先假设答案再检索，让查询措辞更接近文档。
- **解析**：模型输出不可信，必须去编号、去空、去重、限条数。
- **回退**：空输出/异常时回退原问题，保证主链路可用。
- **评测**：改写是否有效，要用同一评测集比较开启前后。

## 边界

- gate 用脚本化 LLM，不验证真实改写质量。
- 通过 gate 只证明 prompt/解析/回退结构正确。
- HyDE、MultiQueryRetriever 的真实效果见参考实现和第 3 篇评测。
