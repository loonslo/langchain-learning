from customer_support.assistant import REFUSAL
from customer_support.workflow import build_graph


def test_graph_stops_invalid_and_refuses_without_evidence():
    calls = []
    graph = build_graph(lambda q: calls.append(q) or [], lambda *_: "编造")
    assert graph.invoke({"question": "  "})["error"] == "问题不能为空" and calls == []
    assert graph.invoke({"question": "未知"})["answer"] == REFUSAL
