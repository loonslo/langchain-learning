# 4.13 Text2SQL：先验证查询，再访问结构化数据

[全书目录](../../README.md) · [上一章 4.12](../4.12-tool-safety-search/README.md) · [下一章 4.14](../4.14-supervisor-fanout/README.md)

- **目标**：让 Agent 能查结构化数据：先验证 SQL 是否安全，再访问数据库，并按问题类型分流到 Text2SQL 或 RAG。
- **前置**：4.7；SQLite 基础。
- **环境**：离线，不调用模型；`app.db` 由脚本自己创建。
- **命令**：`python tools/run_chapter.py 4.13`

## 问题

RAG 适合问文档，企业里还有大量数据在数据库里：订单、财务指标、评测记录。要回答“示例科技最新一期营收是多少”，需要把自然语言变成只读 SQL，查询后再用人话解释结果。把生成 SQL 的工作交给模型时，安全必须由程序保证。

## 概念

- **Text2SQL 流程**：自然语言问题 → 生成只读 SQL → 校验 → 查询 SQLite → 解释结果。
- **`validate_sql` 是安全门**：只允许 `SELECT`；命中危险关键字（`insert`、`update`、`delete`、`drop`、`pragma` 等）就拦；`from`、`join` 后的表必须在白名单内；必须带 `LIMIT`。任何一条不过就抛错，绝不放行到数据库。
- **教学版用规则模拟生成 SQL**：`generate_sql` 用关键词规则代替模型，避免一上来就把安全性交给模型。以后换成 LLM 生成 SQL，`validate_sql` 也必须保留。
- **纵深防御**：生产环境再叠一层只读连接（`mode=ro`），即使 `validate_sql` 被绕过，也写不了库。
- **分流**：`route_question` 按关键词把结构化指标和历史对话交给 Text2SQL，其他问题交给 RAG。

## 流程

1. `init_demo_data` 建表 `sales`、`conversations` 并写入演示数据（可重复运行）。
2. 对四个问题分别 `route_question`；走 Text2SQL 的调用 `text2sql_answer`：`generate_sql` → `execute_sql`（内部先 `validate_sql`）→ `explain_result`。
3. 答案里附带实际执行的 SQL，方便溯源和排错。

## 代码导读

[text2sql_agent.py](text2sql_agent.py)：先看 `validate_sql` 的四道守卫，再看 `execute_sql` 里“先校验、后执行”的顺序，最后看 `route_question`。

## 练习

1. 构造几条危险 SQL（`DELETE`、多语句、非白名单表、不带 `LIMIT`），确认 `validate_sql` 都会拦截。
2. 让 `generate_sql` 故意输出一条带 `--` 注释或分号的 SQL，看守卫能否拦住，并思考哪里还不够严。
3. 把 `route_question` 换成 4.7 的结构化意图分类。

## 运行与边界

- 规则版守卫不是完整的 SQL 解析，只演示安全底线；生产需要更严格的解析和只读账号，见 9.6。
- 关键词分流会误判，真实系统要用评测集验证。
