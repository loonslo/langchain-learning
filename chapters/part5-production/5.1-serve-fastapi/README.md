# 5.1 FastAPI 服务：让模型能力成为接口

[全书目录](../../README.md) · [上一章 4.15](../../part4-agents-langgraph/4.15-framework-landscape/README.md) · [下一章 5.2](../5.2-reliability-retry/README.md)

- **目标**：把命令行问答包装成 HTTP 服务，并补上上线必须回答的四个问题：怎么查问题、上游挂了会不会死、花了多少钱、答得好不好。
- **前置**：2.6（RAG 链）、5.2（超时与重试）。本章用 5.4 的 `sqlite_persistence.py` 保存问答记录，先当黑盒用，5.4 再详细讲。
- **环境**：调用真实模型，加本地 embedding 模型；需要 `fastapi`、`uvicorn`。
- **命令**：`python tools/run_chapter.py 5.1 run_server.py`，然后打开 http://127.0.0.1:8000/docs

## 问题

“能返回答案”只是及格线。一个能上生产的 LLM 服务还要能回答：

1. 出问题了怎么查？`trace_id` 贯穿请求、日志和数据库。
2. 上游挂了服务会不会死？启动降级 + 异常兜底，不裸奔 500。
3. 这个月花了多少钱？每次请求落库 token、成本和延迟。
4. 答得好不好？`/feedback` 收集点赞点踩，回流评测集。

## 概念

- **接口**：`/chat` 问答并落库；`/feedback` 提交点赞点踩；`/stats` 按天统计请求数、失败率、成本和 p95；`/history` 按用户分页查历史；`/health` 存活探针（不查依赖，永远秒回）；`/ready` 就绪探针（依赖没准备好返回 503）。
- **lifespan 与优雅降级**：启动时建库失败不让进程退出，服务照常起、`/health` 正常、`/ready` 返回 503。运维看到的是“活着但没就绪”，而不是反复重启的容器。
- **`trace_id`**：中间件为每个请求生成（或沿用请求头 `X-Trace-Id`），写进响应头、日志和数据库，三处对上号即可定位。
- **请求模型的约束**：`Field(max_length=...)` 挡住“超长 prompt 打爆成本”，FastAPI 自动返回 422。
- **可测的写法**：`build_answer_fn(retriever, llm)` 是工厂函数，测试时可以传入假的检索器和模型，整条接口链路不碰真实模型。
- **成本估算**：单价来自环境变量（`PRICE_IN_PER_M`、`PRICE_OUT_PER_M`），不写死在代码里。

## 流程

1. 启动：`store.migrate()` 建表 → 建立检索器和回答函数（失败则记录错误并以未就绪状态启动）。
2. `/chat`：校验请求 → 检索一次（同时拿到答案、来源和 token 用量）→ 估算成本 → 落库 → 返回答案、来源、`conversation_id` 和 `trace_id`。
3. 前端拿 `conversation_id` 调 `/feedback`；`/stats`、`/history` 直接查库。

## 代码导读

[serve_fastapi.py](serve_fastapi.py)：按【一】RAG 链 → 【二】启动与降级 → 【三】中间件 → 【四】请求响应模型 → 【五】接口的顺序阅读。[run_server.py](run_server.py) 是本机启动入口，支持 `--host`、`--port`。

## 练习

1. 启动服务，在 `/docs` 里调用 `/chat`，观察响应头里的 `X-Trace-Id`，再到日志和 `/history` 里找到同一个 id。
2. 故意把 `RAG_DOC_PATH` 指向不存在的文件启动服务，验证 `/health` 正常、`/ready` 返回 503。
3. 发一个超过 1000 字的问题，观察 422 响应。
4. 提交一次点踩，再查 `/stats`。

## 运行与边界

- 会调用真实模型并产生费用；服务默认只监听 `127.0.0.1`，放进容器时要用 `--host 0.0.0.0`（5.5）。
- 本章没有认证、限流和多租户，只是服务边界；这些在第 7 篇和 capstone 中补充。
- `CORS_ORIGINS` 默认是 `*`，生产要收窄成自己的域名。
