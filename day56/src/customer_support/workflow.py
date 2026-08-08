"""LangGraph 控制流：非法输入提前结束，无证据拒答，有证据才生成。"""

from __future__ import annotations
from typing import Callable, TypedDict
from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph
from .assistant import PROMPT, REFUSAL, SupportAnswer


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


class WorkflowAssistant:
    """把 LangGraph 适配回主程序一直使用的 ``ask`` 接口。"""

    def __init__(self, assistant):
        self.assistant = assistant
        self.graph = build_graph(assistant.retriever.invoke, self._generate)

    def _generate(self, question: str, documents: list[Document]) -> str:
        context = "\n\n".join(document.page_content for document in documents)
        messages = PROMPT.invoke({"context": context, "question": question}).to_messages()
        response = self.assistant.model.invoke(messages)
        return str(getattr(response, "content", response)).strip() or REFUSAL

    def ask(self, question: str) -> SupportAnswer:
        state = self.graph.invoke({"question": question})
        if state.get("error"):
            raise ValueError(state["error"])
        return SupportAnswer(state["answer"], tuple(state.get("sources", ())))
