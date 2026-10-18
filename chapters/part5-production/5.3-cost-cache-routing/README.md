# L5.2 扩展：成本/缓存/路由 · Gate（原 5.3）

[全书目录](../../README.md) · [上一章 5.2](../5.2-reliability-retry/README.md) · [下一章 5.4](../5.4-sqlite-persistence/README.md)

- **能力**：归一化缓存键；带 TTL 的缓存；按难度路由；估算路由节省比例。
- **v2 路径**：L5.2 / 核心（Gate；缓存/路由/成本）
- **前置**：5.2（可靠性/成本）。
- **时间盒**：5 小时（1h 读 + 3h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `cost_cache_routing.py`。
- **验收命令**：

```bash
python chapters/part5-production/5.3-cost-cache-routing/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

缓存和路由最容易出这些错：

- 缓存键不归一化，同一问题大小写/空格不同就未命中；
- 缓存永不过期，知识库更新后仍返回旧答案；
- 路由只看长度，长问候被送强模型、短复杂问题被送弱模型；
- 节省比例算成 `simple_ratio * (1 - strong/cheap)`，方向错；
- 价格/比例不校验，负成本。

这个 gate 用假时钟和纯函数验证缓存、路由和成本公式。

## 任务

实现 `gate/starter.py`：

| 接口 | 你要交付的行为 |
|---|---|
| `cache_key` | 去空白/压缩空白/小写后哈希；空问题报错 |
| `TTLCache` | `get(key, now)` 过期返回 None；`set` 记录时间；ttl<=0 报错 |
| `is_simple`/`route` | 短或问候 -> cheap，否则 strong；空问题报错 |
| `savings` | `simple_ratio*(1-cheap/strong)`；参数校验 |

关键口径：

- 缓存键对 `" RAG   是什么 "` 与 `"rag 是什么"` 必须相同。
- TTL 过期项要删除，不能留在内存。
- 价格必须 >0，cheap<=strong。
- 比例必须在 [0,1]。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | 大小写/空格不同的问题 | 同键 |
| 2 | now 超过 TTL | None |
| 3 | 缺 key | None |
| 4 | ttl=0 | `ValueError` |
| 5 | “你好”/长复杂问题 | cheap/strong |
| 6 | 比例 0.5、1/4 价 | 0.375 |
| 7 | 负比例/负价/cheap>strong | `ValueError` |

## 验收标准

`gate_check.py` 的 4 项全部 PASS：

- 缓存键、TTL 缓存、路由、节省估算。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么缓存键必须归一化？
2. TTL 和知识库更新失效，哪个更根本？
3. 路由节省比例的分母/方向怎么定？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（4/4）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 5.3
```

对照时只回答：

1. 参考实现的缓存有没有 TTL？
2. 参考实现的 `is_simple` 规则和你的差别？
3. embedding 路由为什么比关键词路由稳？

## 概念地图

- **缓存**：键归一化、TTL、失效。
- **路由**：简单走便宜、复杂走强模型。
- **节省**：简单占比 × 价差。
- **测量**：先量化成本，再优化。
- **边界**：生产缓存要防旧答案。

## 边界

- gate 用假时钟/纯函数，不调用真实模型。
- 通过 gate 只证明缓存/路由/公式正确。
- 真实命中率、分类准确率见参考实现与 3.x 评测。
