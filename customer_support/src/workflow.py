"""用 LangGraph 显式表示客服问答的验证、检索与回答步骤。"""

from collections.abc import Callable
from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph

from src.assistant import CustomerSupportAssistant, REFUSAL, SupportAnswer


class SupportState(TypedDict, total=False):
    """在各个工作流节点之间传递的数据。"""

    question: str
    documents: list[Document]
    answer: str
    sources: list[str]
    error: str | None


def build_graph(
    retrieve: Callable[[str], list[Document]],
    generate: Callable[[str, list[Document]], SupportAnswer],
):
    """创建一张“验证 → 检索 → 回答”的状态图。"""

    def validate(state: SupportState) -> dict[str, str | None]:
        # 统一空白字符，后续节点只处理清理过的问题。
        question = " ".join(state.get("question", "").split())
        return {
            "question": question,
            "error": "问题不能为空" if not question else None,
        }

    def retrieve_node(state: SupportState) -> dict[str, list[Document]]:
        return {"documents": retrieve(state["question"])}

    def answer_node(state: SupportState) -> dict[str, str | list[str]]:
        documents = state.get("documents", [])
        if not documents:
            return {"answer": REFUSAL, "sources": []}

        # generate 直接复用 CustomerSupportAssistant 的“基于已有证据回答”逻辑，
        # 因此不会在图内重复检索，也不会再次进入整张图。
        result = generate(state["question"], documents)
        return {"answer": result.text, "sources": list(result.sources)}

    graph = StateGraph(SupportState)
    graph.add_node("validate", validate)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer", answer_node)
    graph.add_edge(START, "validate")
    graph.add_conditional_edges(
        "validate",
        lambda state: "stop" if state.get("error") else "go",
        {"stop": END, "go": "retrieve"},
    )
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


class WorkflowAssistant:
    """将 LangGraph 适配为主程序一直使用的 ``ask(question)`` 接口。"""

    def __init__(self, assistant: CustomerSupportAssistant):
        self.assistant = assistant
        self.graph = build_graph(assistant.retriever.invoke, self._generate)

    def _generate(self, question: str, documents: list[Document]) -> SupportAnswer:
        """为 ``answer`` 节点提供生成能力；输入必须与 build_graph 的约定一致。"""
        return self.assistant.answer_from_documents(question, documents)

    def ask(self, question: str) -> SupportAnswer:
        """执行图并转换回稳定的业务结果；验证失败时保持原有的 ValueError 约定。"""
        state = self.graph.invoke({"question": question})
        if state.get("error"):
            raise ValueError(state["error"])
        return SupportAnswer(state["answer"], tuple(state.get("sources", [])))
