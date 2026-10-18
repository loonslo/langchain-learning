# L2.5 混合检索 · Gate（原 2.8）

[全书目录](../../README.md) · [上一章 2.7](../2.7-chunk-strategy/README.md) · [下一章 2.9](../2.9-query-rewrite/README.md)

- **能力**：用 RRF 融合向量与 BM25 两路排名；处理权重、去重、同分和空结果。
- **v2 路径**：L2.5 / 核心（Gate；混合检索）
- **前置**：2.4（切分策略）、2.2（向量召回）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 对比分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `hybrid_search.py`。
- **验收命令**：

```bash
python chapters/part2-rag/2.8-hybrid-search/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

混合检索的难点不是“把两路结果拼起来”，而是融合规则要可解释：

- 两路都召回时，谁排前面？
- 同一路里重复 ID 怎么算？
- 权重调了，分数怎么变？
- 同分时顺序稳定吗？
- 一路为空、两路为空怎么办？

这个 gate 用 RRF 公式做确定性验收，不依赖 retriever/embedding。

## 任务

实现 `gate/starter.py` 的两个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `rrf_fuse` | 多路排名融合：`score += weight/(k+rank)`；去重；同分按首次出现 |
| `hybrid_search` | 两路结果融合后取 top-k；空输入返回 `[]` |

关键口径：

- `k` 必须 >=1；`weights` 缺省全 1；长度不一致或负数 -> `ValueError`。
- rank 从 1 开始；同一路里重复 ID 只按第一次出现计分，重复项仍占 rank。
- 同分按首次出现顺序稳定排列。
- `hybrid_search` 的 `k < 1` -> `ValueError`；两路都空 -> `[]`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | `[["a","b"],["b","a"]]` | 同分，a 在前 |
| 2 | 权重 `[1,0]` / `[0,1]` | 排序方向反转 |
| 3 | 同一路 `["a","a","b"]` | a 只计一次，b 排第 3 |
| 4 | 空 rankings / 全空 | `[]` |
| 5 | `k=0` | `ValueError` |
| 6 | weights 长度不一致/负数 | `ValueError` |
| 7 | 两路各一个 ID，k=1 | 按首次出现取 top1 |

## 验收标准

`gate_check.py` 的 7 项全部 PASS：

- RRF 公式、权重、去重、空输入、非法参数。
- 混合 top-k、空结果与 k 校验。

通过后，在 [workbook.md](workbook.md) 写：

1. RRF 为什么用 `1/(k+rank)`，而不是直接加原始分数？
2. 同一路里重复 ID 应该计一次还是多次？为什么？
3. 权重怎么定？只看一个查询够不够？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（7/7）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 2.8
```

对照时只回答：

1. 参考实现用 `EnsembleRetriever`，它内部的融合规则和你的 RRF 一样吗？
2. 参考实现为什么要给中文 BM25 传 `preprocess_func`？不传会怎样？
3. 参考实现只用 `Sharpe` 一个例子；这能证明混合检索更好吗？

## 概念地图

- **向量检索**：语义相近，但对专有名词/编号不敏感。
- **BM25**：关键词频率，精确词强，但不懂同义。
- **RRF**：只看排名，不看原始分数；简单、可解释、跨检索器通用。
- **权重**：按领域调；没有通用值，要用评测验证。
- **中文分词**：BM25 默认按空格，中文必须自定义分词。

## 边界

- gate 只实现 RRF，不实现 BM25/向量检索本身。
- 通过 gate 只证明融合规则正确，不证明混合检索在你的领域更好。
- 真实 BM25、中文分词、`EnsembleRetriever` 见参考实现。
