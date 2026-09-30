# 课程重构验证记录 · 2026-09-28

本轮保留已有物理迁移，并完成计划中的工具、CI、文档、总地图与客服阅读入口调整；按用户后续选择，将新增章节一起补齐。未提交或推送 Git，原工作区其他改动保留。

## 本轮结果

- 学习入口改为 `chapters/README.md`，105 个历史内容索引对应当前真实目录；独立章节、旗舰项目与选修项目线分开导航。
- 三条累积项目线统一使用 `tools/materialize.py`，删除 4 个旧脚本；`--diff` 提供变更报告，旗舰项目输出按完整里程碑 / 步骤隔离。
- 修复 `generate_day_guides.py` 的路径与 snapshot 调用；用截获输出的方式验证生成器，不重新覆盖现有教程。
- CI 首步从新的旗舰项目目录运行测试；其余 capstone 检查保持在仓库根目录。同步修复项目基线、里程碑与面试证据里的旧路径。
- 新增 0.1 / 0.2、2.4、3.1、4.1、4.15，并给已有 1.6 补最小 MCP 入门。七个位置均有正文与工作簿；运行例子覆盖环境、协议、RAG 指标、失败定位和有界 Agent 循环。
- 旧大纲、分段总览、白板与 ADR 移到 `docs/legacy/` 并标注历史编号。客服原型保留在 `archive/`（2026-09-30 已删除，内容仍在 Git 历史里，见 `docs/course-review-validation.md`），capstone 的入门路线按实际文件调整。

这只表示课程内容与结构调整完成。历史章节内容和验收证据尚待逐一核实，不代表个人学完课程。

## 实际执行的检查

执行环境：Windows，仓库 `.venv`，Python 3.14.4，pytest 9.0.3。为完成验证，向该本机环境安装了缺失的现有锁定依赖 cachetools / rank-bm25 / redis，以及仓库锁定的 ruff；未修改依赖清单。

| 检查 | 命令与工作目录 | 结果 |
|---|---|---|
| 工具与新增章节 | 根目录 `python -m pytest tools chapters/test_new_lessons.py -q` | 24 passed |
| 旗舰项目首步 | 根目录 `python -m pytest -c flagship-project/m1-rag-mvp/step1/pyproject.toml flagship-project/m1-rag-mvp/step1/tests -q` | 7 passed |
| capstone 生产边界 | 根目录 `python -m pytest capstone/test_production.py -q` | 28 passed，离线替身 |
| 最终教学项目 | `python tools/materialize.py flagship m8-evidence-final-frontend/step3`；在输出目录运行 `python -m pytest -q` | 48 passed |
| AI 质量专项 | `python tools/materialize.py quality 8.10-production-feedback-loop`；在输出目录运行 `python -m pytest -q` | 25 passed |
| 企业专项 | `python tools/materialize.py enterprise 10.4-cross-agent-delegation`；在输出目录运行 `python -m pytest -q` | 41 passed，未连接数据库 / GPU 服务 |
| 里程碑证据 | 根目录 `python -m capstone.milestones --strict-evidence` | 退出码 0，只证明所列文件存在 |
| 项目基线 | 根目录 `python -m capstone.project_baseline --json` | 15 项检查通过，包含 fake knowledge 的最小链路 |
| 差异报告 | 根目录 `python tools/materialize.py flagship m3-order-tool-reliability/step2 --diff` | 新增 2、修改 2、继承 33 |
| 本机例子 | `run_chapter.py` 运行 0.1、1.6 的 `minimal_client.py`、2.4、3.1、4.1 | 均退出 0；MCP 为真实本机协议往返，不调用 LLM |
| 静态检查 | 对本轮修改的工具、验收辅助代码和新章节执行 `python -m ruff check ...` | 通过 |
| 路径与命令审计 | 核对 105 个映射、55 个累计快照与 144 份当前入口文档 | 无失效相对链接，无旧还原命令 |

离线测试合计 173 项通过。不同项目在独立进程、各自配置与临时测试目录中运行，不把它们混在一个同名包环境里。

## 真实模型回归：未通过

已执行 `python -m pytest capstone/test_regression.py -v --basetemp=.tmp/pytest-live`。本机确认模型配置与 embedding 缓存存在，仅处理仓库公开评测资料；设置 `CAPSTONE_DATA_DIR` 到 `.tmp/course-refactor-live-data`，并显式指定原评测集，避免覆盖已有应用数据。

结果：**4 passed，2 failed**。`f01` / `f02` / `f03` / `m01` 通过；`r01` / `r02` 中模型回答“文档中没有提到”，拒答判断通过，但 `AssistResult.citations` 仍包含检索到的文档，因此“拒答不应附加无关引用”断言失败。

定位线索：`capstone/knowledge_base.py` 的 `answer_with_usage` 在有检索文档时拼接来源与结构化引用，没有将模型最终拒答单独分流。本轮未修改该业务函数或评测断言；此项已加入 TASKS，不能将真实模型回归记为通过。

## 未验证的边界

远端 GitHub CI、Python 3.11 的完整执行、staging、浏览器 E2E、PostgreSQL / Redis / Qdrant / GPU 服务与真实容量、恢复验收未执行。章节 3.9 / 3.10 保留的历史评测工具链依赖当前缺失的 `evals/`，仍需单独恢复或替换。

现有未跟踪的 PDF 教程、分析与编辑器资料未改动，其中旧编号仅属于各自历史内容；本轮只整理当前课程入口与其路径依赖。旧文件内容的可恢复副本在本机忽略目录 `.tmp/course-refactor-backup/`，不作为共享项目证据。

框架说明参照 [LangChain 官方概览](https://docs.langchain.com/oss/python/langchain/overview)、[LangGraph 工作流与 Agent](https://docs.langchain.com/oss/python/langgraph/workflows-agents)、[MCP 服务教程](https://modelcontextprotocol.io/docs/develop/build-server) 与 [Pydantic AI 官方介绍](https://pydantic.dev/docs/ai/overview/)；选型章节说明其课程取舍与未验证项。
