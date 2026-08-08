"""Day65 图控制流：检索文档也先经过注入过滤，再进入生成节点。"""

from __future__ import annotations

from typing import Callable, TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph

from .assistant import PROMPT, REFUSAL, SupportAnswer
from .security import filter_documents


class SupportState(TypedDict, total=False):
    question: str
    documents: list[Document]
    blocked_chunks: list[str]
    answer: str
    sources: list[str]
    error: str


def build_graph(
    retrieve: Callable[[str], list[Document]],
    generate: Callable[[str, list[Document]], str],
):
    def validate(state):
        question = " ".join(state.get("question", "").split())
        return {"question": question, "error": "问题不能为空" if not question else ""}

    def retrieve_node(state):
        safe, blocked = filter_documents(retrieve(state["question"]))
        return {"documents": safe, "blocked_chunks": blocked}

    def answer_node(state):
        documents = state.get("documents", [])
        if not documents:
            return {"answer": REFUSAL, "sources": []}
        return {
            "answer": generate(state["question"], documents),
            "sources": list(
                dict.fromkeys(document.metadata["source"] for document in documents)
            ),
        }

    graph = StateGraph(SupportState)
    graph.add_node("validate", validate)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer", answer_node)
    graph.add_edge(START, "validate")
    graph.add_conditional_edges(
        "validate",
        lambda state: "stop" if state["error"] else "go",
        {"stop": END, "go": "retrieve"},
    )
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


class WorkflowAssistant:
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
