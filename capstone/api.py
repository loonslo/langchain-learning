"""
capstone/api.py · FastAPI 服务 + SQLite 落库 + 健康检查
==========================================================
整合 day35/38/39：把知识库问答包成 HTTP 接口，每次问答落 SQLite，
带健康检查。启动时建一次库（全局复用）。
依赖：pip install fastapi uvicorn
运行：uvicorn capstone.api:app --reload   （在仓库根目录执行）
==========================================================
"""

import sqlite3
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

import config as C
from knowledge_base import KnowledgeBase

app = FastAPI(title="企业知识库 Agent")
_kb = KnowledgeBase().build()      # 启动建一次库
_chain = _kb.chain()


def _log(user_id: str, q: str, a: str):
    with sqlite3.connect(C.DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS qa(
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, question TEXT,
            answer TEXT, created_at TEXT)""")
        conn.execute("INSERT INTO qa(user_id,question,answer,created_at) VALUES(?,?,?,?)",
                     (user_id, q, a, datetime.now().isoformat(timespec="seconds")))


class ChatReq(BaseModel):
    question: str
    user_id: str = "anon"


class ChatResp(BaseModel):
    answer: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResp)
def chat(req: ChatReq):
    ans = _chain.invoke(req.question)
    _log(req.user_id, req.question, ans)
    return ChatResp(answer=ans)


@app.get("/history")
def history(user_id: str = "anon", limit: int = 10):
    with sqlite3.connect(C.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT question,answer,created_at FROM qa WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, limit)).fetchall()
        except sqlite3.OperationalError:
            rows = []
    return [dict(r) for r in rows]
