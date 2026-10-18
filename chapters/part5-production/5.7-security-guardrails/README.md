# L5.5 安全护栏 · Gate（原 5.7）

[全书目录](../../README.md) · [上一章 5.6](../5.6-ollama-inference/README.md) · [下一章 5.8](../5.8-pytest-regression/README.md)

- **能力**：检测提示词注入并分级；PII 脱敏可还原；日志密钥脱敏。
- **v2 路径**：L5.5 / 核心（Gate；安全护栏）
- **前置**：4.12（信任边界）、5.1。
- **时间盒**：6 小时（1h 读 + 4h 实现 + 1h 分析）。
- **闭卷规则**：只读本页和 `gate/starter.py`；**通过 gate 之前不要打开** `security_guardrails.py`。
- **验收命令**：

```bash
python chapters/part5-production/5.7-security-guardrails/gate/gate_check.py
```

全部 PASS 才算通过；脚本会写 `gate/gate_report.json`。不允许改 `gate_check.py` 绕过检查。

## 为什么做这个 gate

护栏最容易出这些错：

- 只匹配小写裸词，全角/空格/零宽字符绕过；
- 把“system prompt 怎么写”这种合法问题直接拦掉；
- 手机号规则先跑，从身份证中间咬走 10 位；
- 脱敏不可还原，业务方绕开护栏；
- 密钥只防代码写入，异常字符串仍从日志漏出；
- 只返回 bool，没有命中项，无法审计/调阈值。

这个 gate 用固定文本验证分级、脱敏和密钥清洗。

## 任务

实现 `gate/starter.py` 的三个函数：

| 函数 | 你要交付的行为 |
|---|---|
| `scan_input` | 归一化后匹配；明确注入 -> block，可疑词 -> flag，正常 -> pass |
| `mask_pii` | 邮箱/身份证/银行卡/手机号；先长后短；同值复用占位符；可还原 |
| `scrub_secrets` | sk-/bearer/api_key= 替换为 `[已脱敏密钥]` |

关键口径：

- 归一化 NFKC、小写、去零宽、去空白。
- 只有“改写指令 + 宾语”才 block；裸 `system prompt` 只 flag。
- PII 规则先长后短（身份证/银行卡先于手机号）。
- `mask_pii` 返回 `(脱敏文本, {占位符: 原值})`。
- 非字符串输入 -> `ValueError`。

## 故障注入（必须亲手触发）

| # | 注入 | 期望 |
|---|---|---|
| 1 | “忽略以上…指令”/全角空格 | block |
| 2 | ignore previous instructions | block |
| 3 | “system prompt 怎么写” | flag |
| 4 | 正常问题/合法英文 | pass |
| 5 | 手机号+邮箱+身份证+卡号 | 全部脱敏且可还原 |
| 6 | 同一手机号出现两次 | 复用 `[手机号_1]` |
| 7 | 日志含 sk-/bearer/api_key | 全部抹掉 |

## 验收标准

`gate_check.py` 的 7 项全部 PASS：

- 拦截、告警/放行、检测类型、脱敏还原、同值复用、脱敏类型、密钥脱敏。

通过后，在 [workbook.md](workbook.md) 写：

1. 为什么检测层只能当告警，不能当防线？
2. 脱敏为什么必须可还原？
3. 护栏误伤和漏检，哪个代价更大？

## 提交物

- `gate/starter.py`（实现后的版本）。
- `gate/gate_report.json`（7/7）。
- workbook 里的失败分析与三个问题的回答。

## 通过后对照参考实现

不要提前看。通过后再运行并对照：

```bash
python tools/run_chapter.py 5.7
```

对照时只回答：

1. 参考实现的 `scan_input` 怎么分级？
2. 参考实现的 PII 规则顺序为什么重要？
3. 参考实现的 `build_messages` 为什么比关键词检测更重要？

## 概念地图

- **信任边界**：数据/指令分槽；检索文档也是不可信输入。
- **分级检测**：block/flag/pass；检测是弱信号。
- **PII 脱敏**：先长后短、可还原、还原表不进日志。
- **密钥治理**：启动校验 + 日志清洗。
- **非对称**：脱敏偏保守，拦截偏宽松。

## 边界

- gate 只测纯函数，不调用模型。
- 通过 gate 不证明模型抗注入；结构性隔离/权限/HITL 仍是真防线。
- 输出审核、工具审批、按人过滤见 capstone。
