"""
Day 35 · 把 RAG 包成 HTTP 接口（FastAPI）
==========================================================
测试工程师转 AI 应用开发

到现在 RAG 还只能在命令行跑。要给别人用、要接前端，得做成 HTTP 服务。
这节用 FastAPI 把 Day10 的 RAG 包成 /chat 接口。

知识点：
1. FastAPI 定义接口 + Pydantic 定义请求/响应结构（自带类型校验和文档）
2. 启动时建一次库（全局复用），请求时只跑问答，不重复 embedding
3. 怎么启动、怎么测

依赖：pip install fastapi uvicorn
运行：uvicorn day35_serve_fastapi:app --reload
测试：浏览器打开 http://127.0.0.1:8000/docs 直接点（FastAPI 自动生成的接口文档），
      或命令行：curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\":\"RAG 是什么\"}"
==========================================================
"""

from fastapi import FastAPI
from pydantic import BaseModel
from day11_rag_pdf_sources import build_retriever, build_rag_chain

app = FastAPI(title="RAG 知识库问答")

# 关键点：建库放在模块加载时（服务启动时）只做一次，存成全局变量。
# 这样每个请求只跑"检索+生成"，不会每次都重新切割、embedding。
retriever = build_retriever("test_doc.txt")
rag_chain = build_rag_chain(retriever)


# 用 Pydantic 定义请求体和响应体：FastAPI 会自动校验类型、自动生成接口文档
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health():
    """健康检查：部署后用它确认服务活着（负载均衡/k8s 探针都靠这种接口）。"""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """问答接口：收到问题 → 跑 RAG → 返回答案。"""
    answer = rag_chain.invoke(req.question)
    return ChatResponse(answer=answer)


# ----------------------------------------------------------
# 小结：
# - FastAPI = Python 写 HTTP 接口最省事的框架，Pydantic 负责请求/响应的类型校验
# - 重活（建库）放启动时做一次，请求只做轻活，是服务化的基本套路
# - /docs 自动生成可交互文档，调试接口不用自己写前端
#
# 进阶（了解）：上传文档接口 /upload、流式返回（StreamingResponse 配 .stream()）、
#              多用户会话隔离——用到再加。
#
# 动手练习：加一个 /upload 接口，让用户上传 txt/pdf 后针对它问答
# ----------------------------------------------------------
