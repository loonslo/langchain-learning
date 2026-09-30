# 课程审查与订正验证 · 2026-09-30

按七项要求（精简、层次、衔接、初学者视角、订正错误、代码注释、文字精炼）审查整个课程，随后按确认做了清理并修了两个遗留问题（混合检索的证据门槛、拒答附引用）。只改工作区文件，不动 Git 索引，不提交、不推送。开工前的工作区快照在忽略目录 `.tmp/review-backup-20260929/`（不含 `.env`）。

## 发现并订正的主要问题

**断链**

- `tools/run_chapter.py` 把工作目录切到章节目录，但示例文档在仓库根目录，2.1 等 17 个脚本找不到文件。共用资料移到 `chapters/shared-data/`，路径由 `common.py` 的 `SHARED_DATA_DIR`、`SAMPLE_DOC`、`LONG_DOC` 提供。
- 评测集靠工作目录传递，3.4 → 3.5 → 3.2/3.3/3.6/3.7 互相找不到。改为共用目录；3.7 读取评测集并可写出失败样本，3.10 自带 `failures_sample.json`（7 条合成记录）并支持 `--input`。
- 示例文档曾被长文替换，评测集和问题仍按原短文写。恢复短文为 `test_doc.txt`，长文改名 `long_article.txt`（2.1、2.7、2.8 使用）。
- 依赖缺失：新增 `requirements-course.txt`；`0.1` 自检按“从哪一篇开始需要”分组，只有必需组缺失才返回 1。
- 5 处写死的本机路径、CI 工作流分支（`main` → `master`）、`.env.example` 中容器路径陷阱。

**文字与代码不一致**

- 1.1、1.7、4.12、4.14/4.7、5.5（容器外无法访问）、5.2 标题（实际没有异步）、3.10（引用已删除的工具）等章节的说明与代码不符，已改。
- 8.6（未校验参数）、8.7（无完成标记、前端不用 SSE）、8.10（导出没有预期结果）、9.1（非法类别抛错而非回到 unknown）、9.6（本模块不绑定参数）、9.7（缓存故障不降级）、10.4（越权路径无测试）的说明，按代码实际行为改写。
- 乱码范围表述（“里程碑 X / stepN至里程碑 Y”“stepN–60”“章节 8.1–87”等）逐处订正。
- 82 个章节 README 重复模板段落占比 19.5% → 1.8%；29 个项目步骤 README 由 14.9 万字符精简为 4.9 万，重复占比 9.0% → 5.0%（余下为生成器的还原命令）。章节头部改为“目标 / 前置 / 环境 / 命令”列表。

**实际缺陷（已修并补测试）**

| 位置 | 问题 | 修正 |
|---|---|---|
| 8.9 `evaluate_gate` | 必需层没有报告时门禁照样放行 | 新增 `required_layers`，缺层记入 `missing_layers` 并阻断 |
| 8.8 `percentile` | 向下取整，小样本丢掉最慢请求 | 改为 nearest-rank；7.7 / step2 `report` 同改，并拒绝空样本 |
| 8.7 `parse_sse` | `data:` 后的空白被全部去掉 | 只去掉一个空格，符合规范 |
| 9.3 `parse_model_json` | 只要传了 `repair` 就先调用它，合法输出也多花一次模型调用 | 原输出校验失败后才调用一次 |
| 9.5 `history` | 查询没有 `tenant_id` 条件，读完不结束事务 | 应用层加 `tenant_id`，读后 `commit` |
| 10.2 状态表 | `working → auth-required` 不被允许 | 加入迁移表 |
| 10.3 `dispatch` | `TaskNotFound` 被 `KeyError` 分支截获，返回 -32602 | 调整分支顺序，返回 -32001；`/v1/message:stream` 补 400 处理 |
| 10.4 越权路径 | 因上一条被误报为“订单服务暂时不可用” | 随状态表修正；新增测试 |
| 2.1 `load_split_formats.py` | `Language.SQL` 不存在；切分结果是 str 而不是 Document；jsonl 处理有误 | 去掉 `.sql` 映射，用 `create_documents` 包装，补 md 来源 |
| capstone `answer_with_usage` | 只有回答**严格等于**“文档中没有提到”才当作拒答；真实模型答“文档中没有提到。”就被附上引用（即上轮 4 passed / 2 failed 的原因） | 新增 `is_refusal`：去掉空白、引号和标点后以拒答话术开头才算拒答；6 条确定性测试（改前 4 条失败） |
| 旗舰 m1/step1、m2/step2、m5/step1 | 模型按提示词拒答时仍附来源，评测的引用判定会失败，`escalate` 也因“有来源”不建工单 | 回答等于 `REFUSAL` 时来源为空；补 3 条测试 |
| 旗舰 m1/step4 `KeywordRetriever` | 没有证据门槛：单个汉字命中就召回，混合检索后“没有证据就不调用模型”基本不触发 | 问题里的词（英文词、中文双字词）至少命中 2 个才返回，词不足时要求全部命中；补 3 条测试 |

**注释与说明**

- 第 1–6 篇脚本头部统一为“做什么 / 怎么运行 / 前置”；8–10 篇、旗舰项目补充语义型 docstring（返回值含义、失败行为、已知局限）。
- 旗舰 m1/step4 的 README 说明关键词一路的证据门槛及其原因。

## 按确认执行的清理

已删除：`archive/customer_support-prototype/.venv` 和根目录 `venv/`（两个旧虚拟环境，`archive` 从 1.2 GB 降到 1.8 MB）、1.6 的 `debug_weather.py`（同时去掉 README 中的对应行）、根目录 `Dockerfile.example`、`.dockerignore.example`、`requirements.example.txt`（`capstone/DEPLOY.md` 的对应步骤改为直接使用根目录 `Dockerfile`）、`artifacts/` 整个目录、`reports/` 中的历史输出。小文件和 `reports/`、`artifacts/` 的内容先备份到 `.tmp/deleted-backup-20260930/`（被忽略，确认无误后可自行删除）；两个虚拟环境不备份，可重新创建。

没有照删的三处，都是因为它们被引用：

- `_capstone_driver.py` 被 `python -m capstone.improvement_loop`（里程碑验收命令）依赖，改为移入 `capstone/driver.py` 并更新导入，根目录不再有它。
- `reports/prompt_ab_judge_agreement.json`：`python -m capstone.interview_evidence --strict-evidence` 把它当作证据文件。
- `reports/loadtest_20260729_234712.json` 与 `loadtest-20260729-234704-26564-final.json`：`capstone/docs/portfolio/` 引用的压测数字（23 个请求、0 失败、6.033 rps）来自这次运行。

`reports/README.md` 已按现状重写。

随后又按确认删除整个 `archive/`（客服原型 `customer_support-prototype`，含 67 个已暂存文件）。这些文件的旧路径（`customer_support/`、`day31_40/` 等）仍在 Git 历史里，磁盘快照备份在 `.tmp/deleted-backup-20260930/archive-worktree/`；`AGENTS.md` 和根 `README.md` 里的对应说明已删除。

## 实际验证

Windows，项目虚拟环境（`.venv`，Python 3.14.4），pytest 9.0.3。除表中标明的一次 capstone 真实模型回归外，其余验证未调用真实聊天模型（相关密钥在验证进程里置空）。

| 检查 | 命令或范围 | 结果 |
|---|---|---|
| 工具与章节辅助测试 | `python -m pytest tools chapters/test_new_lessons.py -q` | 28 passed |
| 整合实现 | `python -m pytest capstone/test_production.py -q` | 34 passed |
| 真实模型回归 | `python -m pytest capstone/test_regression.py -v`（DeepSeek，6 个短问题，本地 embedding） | 6 passed，含 r01、r02；真实回答为“文档中没有提到。”，引用为 0 |
| CI 评测门禁 | `python -m capstone.ci_gate`（真实模型，同样的 6 条评测集） | 拒答 2/2、关键词 4/4、引用 4/4、失败 0，门禁通过；刷新了被忽略的 `capstone/data/eval_report.md` |
| 旗舰首步 | `python -m pytest -c flagship-project/m1-rag-mvp/step1/pyproject.toml flagship-project/m1-rag-mvp/step1/tests -q` | 9 passed |
| 旗舰累计后端 | 还原 `flagship m8-evidence-final-frontend/step2`，在快照目录执行 `python -m pytest --basetemp=.pytest-tmp -q` | 56 passed |
| 质量专项累计 | 还原 `quality 8.10-production-feedback-loop`，同上 | 28 passed |
| 企业专项累计 | 还原 `enterprise 10.4-cross-agent-delegation`，同上 | 46 passed |
| 里程碑证据 | `python -m capstone.milestones --strict-evidence` | 退出码 0，84 项文件存在 |
| 项目基线 | `python -m capstone.project_baseline --json` | 15 项全部通过 |
| 证据审计 | `python -m capstone.evidence_audit` | 7 项通过，1 项警告（无截图/GIF） |
| 环境自检 | `python tools/run_chapter.py 0.1` | 退出码 0；可选缺失 langchain、ragas、datasets、deepeval、langmem、peft |
| 离线章节运行 | `run_chapter.py` 运行 0.1、1.6 minimal_client、1.7、2.1（两个脚本）、2.2、2.4、2.7、2.8、2.10（两次）、3.1、3.4、3.5、3.9、3.10、4.2 graph_basics、4.9、4.13、5.4、5.5、5.7、6.1 | 均退出码 0，无 Traceback |
| 收集与帮助 | 5.8 `--collect-only -q`；3.7、5.1 `run_server.py`、6.2 的 `--help` | 正常退出 |
| 旗舰混合检索探测 | 还原 `m1-rag-mvp/step4`，用本地 embedding 模型（不调用聊天模型）对 6 个资料内、8 个无关问题调用 `build_retriever` | 资料内问题全部命中正确来源；无关问题（含评测集的“黑金会员权益？”）全部返回空 |
| 语法 | 292 个 Python 文件 `ast.parse` | 无语法错误 |
| 链接与头部 | 284 个 Markdown 的相对链接；82 个章节 README 头部字段 | 无失效链接；0.2、4.15 没有“命令”项（无代码章节） |
| 代码规范 | `python -m ruff check tools capstone chapters common.py flagship-project` | 12 条既有风格提示：E402×8（3.6 先设环境变量再导入；4.14、5.3 把导入放在各小节开头）、E731×2、F401×2（旗舰快照），未改动 |

离线测试合计 **201 passed**（28 + 34 + 9 + 56 + 28 + 46），比上一轮记录的 174 多 27 项（新增测试覆盖上表中的缺陷）；另有上表的真实模型回归 6 passed。该数字不包含远端服务或浏览器。

Windows 默认临时目录对 `tmp_path` 拒绝访问，所以累计测试统一使用 `--basetemp`。

## 未验证与限制

- 需要真实聊天模型的章节（1.1–1.5、1.8、2.3、2.6、3.2、3.3、3.6–3.8、4.3–4.8、4.10–4.12、4.14、5.1–5.3、5.6、5.8 的真实运行）只检查了脚本可解析、可收集、帮助可运行，没有运行；LangSmith、Ragas、DeepEval 在线评测、Ollama、GPU、Docker 构建同样没有运行。
- 第 9–10 篇只有离线替身：真实 PostgreSQL/RLS、Redis、Qdrant、vLLM、远端 MCP 与 A2A 互操作未验证；旗舰前端（`m8/step3`）的 `npm` 构建和浏览器端到端未运行。
- 真实模型回归只覆盖 capstone 的 6 条用例（f01–f03、m01、r01、r02），没有覆盖其他章节，也不代表总体准确率；旗舰混合检索的探测只到检索层。
- 本次为运行验证安装了 `faiss-cpu`、`pypdf` 到 `.venv`（已写入 `requirements-course.txt`）；运行章节产生的向量库、SQLite 文件在被忽略的路径下。
- `pdf-course/` 书稿没有重建；仅同步了改名章节的引用。
- 课程内容完成与个人学习完成分别记录。本记录只说明文字、代码和离线测试的一致性。
