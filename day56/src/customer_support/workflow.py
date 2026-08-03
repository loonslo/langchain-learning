"""LangGraph 控制流：非法输入提前结束，无证据拒答，有证据才生成。"""

from __future__ import annotations
from typing import Callable, TypedDict
from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph
from .assistant import REFUSAL


class SupportState(TypedDict, total=False):
    question: str
    documents: list[Document]
    answer: str
    sources: list[str]
    error: str


def build_graph(retrieve: Callable[[str], list[Document]], generate: Callable[[str, list[Document]], str]):
    def validate(s):
        q = " ".join(s.get("question", "").split())
        return {"question": q, "error": "问题不能为空" if not q else ""}

    def retrieve_node(s):
        return {"documents": retrieve(s["question"])}

    def answer_node(s):
        docs = s.get("documents", [])
        return (
            {
                "answer": generate(s["question"], docs),
                "sources": list(dict.fromkeys(d.metadata["source"] for d in docs)),
            }
            if docs
            else {"answer": REFUSAL, "sources": []}
        )

    graph = StateGraph(SupportState)
    graph.add_node("validate", validate)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer", answer_node)
    graph.add_edge(START, "validate")
    graph.add_conditional_edges(
        "validate", lambda s: "stop" if s["error"] else "go", {"stop": END, "go": "retrieve"}
    )
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)
    return graph.compile()
