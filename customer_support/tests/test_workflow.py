"""验证 LangGraph 路由和它与既有助手的适配。"""

from types import SimpleNamespace

from langchain_core.documents import Document

from src.assistant import REFUSAL, CustomerSupportAssistant
from src.workflow import WorkflowAssistant, build_graph


def test_graph_stops_invalid_and_refuses_without_evidence():
    calls = []
    graph = build_graph(
        lambda question: calls.append(question) or [],
        lambda *_: AssertionError("无证据时不应生成回答"),
    )

    assert graph.invoke({"question": "  "})["error"] == "问题不能为空"
    assert calls == []
    assert graph.invoke({"question": "未知"})["answer"] == REFUSAL


def test_workflow_adapter_generates_from_retrieved_documents_once():
    document = Document(
        page_content="退款审核通过后 3–5 个工作日到账。",
        metadata={"source": "refund.md"},
    )

    class Retriever:
        def __init__(self):
            self.calls = 0

        def invoke(self, _question):
            self.calls += 1
            return [document]

    class Model:
        def __init__(self):
            self.calls = 0

        def invoke(self, _messages):
            self.calls += 1
            return SimpleNamespace(content="退款需要 3–5 个工作日。")

    retriever = Retriever()
    model = Model()
    result = WorkflowAssistant(CustomerSupportAssistant(retriever, model)).ask("退款多久到账？")

    assert result.text == "退款需要 3–5 个工作日。"
    assert result.sources == ("refund.md",)
    assert retriever.calls == 1
    assert model.calls == 1
