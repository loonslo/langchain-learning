"""
customer_service/graph.py · 客服主图：意图路由 → 四条处理分支（LangGraph）
==========================================================
结构（复用 Day27-32 全套）：

    START → classify → [faq | order | complaint | chitchat] → END

- classify：intents.classify（结构化输出 / 规则兜底）
- faq：FAQ 检索问答（带多轮历史）
- order：抽订单号 → 查询工具；抽不到就追问（多轮的意义所在）
- complaint：建工单 + 标记转人工（Day70 计划：升级成 Day36 的 interrupt 真·HITL）
- chitchat：礼貌寒暄，不浪费检索/工具调用（成本意识，Day43）
==========================================================
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

import config as C
import faq
import intents
import session
import tools


class CSState(TypedDict):
    session_id: str
    question: str
    intent: str
    answer: str
    escalated: bool     # 是否已转人工


def classify_node(state: CSState) -> dict:
    it = intents.classify(state["question"])
    return {"intent": it.intent}


def faq_node(state: CSState) -> dict:
    hist = session.history(state["session_id"])
    hist_text = "\n".join(f"{m['role']}: {m['content']}" for m in hist)
    return {"answer": faq.answer(state["question"], hist_text), "escalated": False}


def order_node(state: CSState) -> dict:
    oid = tools.extract_order_id(state["question"])
    if not oid:
        # 在最近历史里找订单号——"就是昨天那个订单"这类指代靠它
        for m in reversed(session.history(state["session_id"])):
            oid = tools.extract_order_id(m["content"])
            if oid:
                break
    if not oid:
        return {"answer": "请提供订单号（如 A1001），我帮您查询。", "escalated": False}
    return {"answer": tools.query_order(oid), "escalated": False}


def complaint_node(state: CSState) -> dict:
    tid = session.create_ticket(state["session_id"], state["question"])
    return {
        "answer": f"非常抱歉给您带来不好的体验。已为您创建工单 #{tid}，"
                  "人工客服将尽快联系您。",
        "escalated": True,
    }


def chitchat_node(state: CSState) -> dict:
    return {"answer": "您好，我是智能客服，可以帮您咨询产品、查订单、处理售后问题。",
            "escalated": False}


def route(state: CSState) -> str:
    return state["intent"]          # 结构化字段直接路由，不解析自由文本


def build_app():
    g = StateGraph(CSState)
    g.add_node("classify", classify_node)
    g.add_node("faq", faq_node)
    g.add_node("order", order_node)
    g.add_node("complaint", complaint_node)
    g.add_node("chitchat", chitchat_node)
    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", route,
                            {i: i for i in C.INTENTS})
    for i in C.INTENTS:
        g.add_edge(i, END)
    return g.compile()


def chat(session_id: str, question: str) -> dict:
    """对外唯一入口：一轮对话（读历史 → 跑图 → 落库）。"""
    session.init_db()
    app = build_app()
    out = app.invoke({"session_id": session_id, "question": question,
                      "intent": "", "answer": "", "escalated": False})
    session.append(session_id, "user", question, out["intent"])
    session.append(session_id, "assistant", out["answer"])
    return out
