# 课程用途命名与书稿正文验证 · 2026-09-28

按本次用户反馈，当前课程不再使用日期编号作为文件用途，也不再把源码作为目录的第一入口。调整保留已有教学业务与个人工作簿，不提交或推送 Git。

## 已完成的调整

- 62 个文件改为用途名称：59 个章节练习脚本及 3 个辅助工具或文档。示例包括 rag_regression.py、tool_calling.py、pdf_sources.py、generate_project_guides.py 和 project_task.py。旧对应只保留在历史迁移档案。
- 82 个章节都有 README 正文和 workbook；29 个旗舰项目步骤都补写场景、职责、过程预测与验收观察。代码链接位于概念和流程说明之后，完整技术说明作为参考保留。
- 全书目录、分篇目录和项目目录首先链接文字教程。第 5.8 章额外展开正例、拒答、环境跳过、严格模式和延迟判断的具体例子，并提供合成测试文档。
- 导入、命令、输出文件、前端标签和运行元数据采用当前用途名称。Chroma 集合名使用合法英文前缀，身份测试中的合成密钥也使用用途名。
- 章节运行入口设置共享导入路径与本章工作目录，异常后恢复调用者目录。新增 FastAPI 本机启动入口；回归脚本支持转发 pytest 参数。
- 教程生成器只更新实现参考，保留已写的书稿正文和已有学习记录。

源文件调整前的本机恢复副本位于忽略目录 .tmp/course-book-backup；历史原型与归档文件不进入当前阅读路线。

## 实际验证

Windows，项目虚拟环境，Python 3.14.4，pytest 9.0.3。下表是本次离线检查，未调用真实聊天模型。

| 检查 | 实际命令或范围 | 结果 |
|---|---|---|
| 工具、新增示例与整合实现 | 根目录：python -m pytest tools chapters/test_new_lessons.py capstone/test_production.py -q | 53 passed |
| 旗舰首步 | 根目录：python -m pytest -c flagship-project/m1-rag-mvp/step1/pyproject.toml flagship-project/m1-rag-mvp/step1/tests --basetemp=.tmp/pytest-flagship-first -q | 7 passed |
| 旗舰累计后端 | 还原 flagship m8-evidence-final-frontend/step2，在快照目录执行 python -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q | 48 passed |
| 质量专项累计 | 还原 quality 8.10-production-feedback-loop，同上测试命令 | 25 passed |
| 企业专项累计 | 还原 enterprise 10.4-cross-agent-delegation，在快照目录执行 python -m pytest -q | 41 passed |
| 代码规范 | python -m ruff check tools capstone/milestones.py capstone/project_task.py chapters/part5-production/5.1-serve-fastapi/run_server.py | 通过 |
| 最小 MCP | python tools/run_chapter.py 1.6 minimal_client.py | 真实本机协议发现 add，返回 5，非法参数被拒绝 |
| 线性状态图 | python tools/run_chapter.py 4.2 graph_basics.py | 节点顺序和最终状态符合预期 |
| 回归脚本收集 | python tools/run_chapter.py 5.8 --collect-only -q | 6 条测试可收集；未运行真实模型 |
| 启动参数 | 5.1 run_server.py --help；6.2 --help | 正常退出，不启动服务或训练 |
| 基线与证据入口 | capstone.project_baseline --json；capstone.milestones --strict-evidence --json | 基线 15 项通过；28 个能力记录无缺失文件 |
| 内容与路径审计 | 当前源码语法、82 个章节正文、29 个项目步骤、55 个累积快照与相对链接 | 全部可定位，无语法错误或失效相对文件链接 |

离线测试合计 **174 passed**。初次累计测试遇到 Windows 默认临时目录拒绝访问，以及改名后的集合名不合法；已改用快照内临时目录并修正英文运行标识，重新执行后通过。测试出现依赖弃用提示，不影响本次结果。

## 保留的限制

本次未重跑真实模型回归。上一轮已执行的结果仍为 4 passed / 2 failed：拒答仍附引用，详见 [上一轮记录](course-restructure-validation.md)，该业务问题保持待修状态。

真实模型质量、远端 CI、浏览器端到端、数据库与缓存服务、GPU、部署、容量和灾难恢复未因这次文档与命名调整完成验收。第 3.7 和 3.10 的默认评测资产仍待补齐，正文已说明前提。

课程内容完成与个人学习完成分别记录。本次结果只证明命名、文字入口及相关离线运行边界已调整。
