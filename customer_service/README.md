# 智能客服 Agent（第二项目，Day67-71）

企业 AI 应用两大主流场景 = RAG 知识库 + 智能客服。capstone 覆盖前者，本项目覆盖后者。
**不从零造轮子**：组装已学过的组件，新增客服特有的路由、多轮会话、转人工与评估指标。

## 架构

```
用户消息 → classify(意图分类, Day32 结构化输出)
            ├─ faq        FAQ 检索问答（BM25，可升级 capstone 混合检索）
            ├─ order      抽订单号 → 查询工具（Day05/38）；缺单号→追问/查历史（多轮）
            ├─ complaint  建工单 + 转人工（Day70 升级为 Day36 interrupt 真·HITL）
            └─ chitchat   寒暄直答，不浪费检索/工具（Day43 成本意识）
会话历史 / 工单 → SQLite（Day44）
评估 → 意图准确率 / 解决率 / 转人工率 / 多轮指代（★护城河）
```

## 运行

```bash
python customer_service/main.py chat     # 多轮对话（无 key 走离线模式）
python customer_service/main.py eval     # 评估 + reports/latest_report.md
pytest customer_service/test_regression.py -v   # 回归 + 指标门禁
```

离线模式（无 `DEEPSEEK_API_KEY`）：意图走规则、FAQ 走 BM25 直出，CI 零成本可跑；
配 key 后同一份评估集测 LLM 版，规则 vs LLM 直接对比。

## Day67-71 任务安排

| Day | 任务 | 产出 / 验收 |
|-----|------|------------|
| 67 | 跑通骨架：读懂 graph.py 路由结构，`main.py chat` 走通四条分支；补 2 条 FAQ、2 条评估用例 | pytest 全绿 |
| 68 | 意图分类升级：配 key 跑 `classify_llm`，用评估集对比规则 vs LLM 的 intent_acc；给 LLM 分类加 few-shot | 报告里两组指标对比 |
| 69 | 多轮强化：order 分支的追问改成 LLM 澄清式提问；faq 分支把历史压缩进 prompt（Day78 上下文工程） | 多轮用例从 2 条加到 5 条且通过 |
| 70 | 真·HITL 转人工：complaint 分支改用 Day36 `interrupt()` + checkpointer，人工审批后恢复；工单状态流转 open→resolved | 演示暂停-恢复全流程 |
| 71 | 接入评估平台 + 收尾：指标写入 evals 的回归历史，接 CI 门禁；README 补面试话术 | CI 跑两个项目的门禁 |

## 面试话术（一句话版）

"我做了两个业务场景——企业知识库和智能客服——共用一套自动化评估平台：
知识库看拒答率和引用命中，客服看意图准确率、解决率、转人工率，
都进 pytest 回归和 CI 质量门禁。评估平台是我测试背景的护城河。"
