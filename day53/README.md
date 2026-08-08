# Day53 · 用真实产品链执行离线评测

固定评测题不是用户入口，而是版本升级前可以重复运行的质量基准。自由提问继续使用默认交互模式。

## 与 Day52 的文件衔接

| 文件 | 今天的状态 | 为什么必须一起看 |
|---|---|---|
| `src/customer_support/evaluation.py` | 新增 | 读取固定用例并调用正式 `assistant.ask()` |
| `src/customer_support/settings.py` | 修改旧文件 | 在多文档配置上增加 `evaluation_path` |
| `data/eval_cases.json` | 新增 | 提供可重复的答案与来源验收输入 |
| `src/customer_support/knowledge.py` | 继承未改 | 评测仍使用 Day52 的多文档摄取和检索 |
| `src/customer_support/assistant.py` | 继承未改 | 评测不复制问答逻辑，直接复用业务入口 |
| `src/customer_support/bootstrap.py` | 继承未改 | 两个入口都由同一个组合入口创建正式依赖 |

用 `python tools/day_change_report.py 53` 核对实际变更。

## 当天交付

- `data/eval_cases.json` 保存问题、答案关键词、期望来源和拒答要求。
- `evaluation.py` 分别判断回答和引用，输出可定位结果。
- 评测作为独立开发验收程序，不进入用户问答界面。
- 评测程序创建真实 embedding、Retriever 和 LLM，再执行评测集。
- 任一用例失败时进程返回非零退出码，可供后续 CI 使用。

## PyCharm 中的两个运行配置

- 用户主程序：Module name 为 `customer_support.app`。
- 开发评测：Module name 为 `customer_support.evaluation`。

用户平时只运行第一个配置。

## 真实评测链

```text
eval_cases.json
  → load_cases
  → 真实 CustomerSupportAssistant.ask
  → 多文档检索 + LLM
  → answer_ok + citation_ok
  → 评测报告和退出码
```

## 在 PyCharm 运行

还原 Day53 后，将 `.build/day53/customer-support/src` 标记为 Sources Root，Working directory 选择 `.build/day53/customer-support`，再选择对应模块运行配置。

真实评测需要模型环境可用。自动测试会替代昂贵外部依赖来验证评测规则，但当天完成标准还包括运行一次真实评测程序。

Day54 将改进真实检索器，并用同一个评测程序比较结果。
