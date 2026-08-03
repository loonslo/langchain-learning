# 简历项目描述与证据边界（Day67）

> 求职定位：测试工程师转 AI 应用/质量工程。卖点不是“调过模型 API”，而是能把概率性模型放进可测试、可回归、可观测的工程边界。

## 当前可直接写进简历的版本

**企业知识库问答与自动化评测平台｜个人项目**

使用 LangChain、LangGraph、Chroma、FastAPI 和 DeepSeek 构建企业文档问答原型，并围绕检索权限、回归评测、认证、监控和部署准备补齐工程边界。

- 支持 TXT、Markdown、PDF 文档解析，组合向量检索与 BM25；答案来源由应用根据实际召回文档生成，避免模型伪造引用。
- 基于文件 SHA-256 和确定性 chunk ID 实现增量同步；重复同步不重复写入，文档更新和删除可定位到旧 chunk。
- 在向量查询前应用文档 ACL，BM25 只为授权子集建索引；每个租户使用独立持久化目录，并通过 JWT claims 传递可信身份。
- 构建 6 条版本化评测用例和 CI 门禁。2026-07-29 本地真实 DeepSeek 运行结果：拒答 2/2、关键词命中 4/4、失败 0；该小样本结果只证明当前回归集通过，不代表通用准确率。
- FastAPI 接口加入认证、限流、权限/知识版本感知 TTL 缓存、请求 ID、PII 脱敏和租户级延迟/错误率/token/成本指标；用 pytest 覆盖关键安全边界。
- 提供 Dockerfile 和部署说明，但截至当前没有可核验的本机 Docker 构建或公网部署，因此不写“已上线”。

## 只按真实熟练度写关键词

- 可深入追问：RAG、混合检索、文档切分、ACL、多租户、JWT、自动化评测、pytest、FastAPI、可观测性、缓存、CI 门禁。
- 有代码练习但不是本项目交付：MCP、RAGAS、LangSmith、ReAct、Plan-and-Execute。
- 了解级：LoRA、LlamaIndex、AutoGen。没有做过的实现不放进项目成果。

## Agent 能力的准确说法

`capstone/service.py` 只允许白名单动作进入 `capstone/approval.py`。审批状态持久化到 SQLite，并校验租户、审批角色、过期和一次性决策；当前仍缺少真实外部副作用执行器、取消/撤销流程和加密状态存储。MCP 练习存在于 Day40，不在当前 capstone 运行链路中。

## 作品证据清单

- 入口与运行说明：`capstone/README.md`
- 评测集与最新报告：`capstone/data/eval_set.json`、`capstone/data/eval_report.md`
- 生产边界测试：`capstone/test_production.py`
- CI 门禁：`.github/workflows/eval-gate.yml`
- 本地压测报告：`reports/loadtest_*.json`

截图、GitHub Actions 红绿记录、公开仓库地址和线上地址只有真实存在时再添加。`python -m capstone.evidence_audit` 会自动检查一部分证据是否齐全。

## 面试表达纪律

- 区分“已实现”“本地验证”“设计预留”“生产仍需补齐”。
- 所有数字都带样本量、时间、环境和计算口径。
- 不把安全词表当完整合规方案，不把本地 HS256 token 当企业 IdP，不把 Dockerfile 当已部署。
