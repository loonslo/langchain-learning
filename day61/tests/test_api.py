from fastapi.testclient import TestClient
from customer_support.api import create_app
from customer_support.application import ApplicationResult
from customer_support.assistant import SupportAnswer


class Fake:
    def ask(self, q):
        return SupportAnswer(q, ("faq.md",))


def test_api_schema_and_validation():
    client = TestClient(create_app(Fake()))
    assert client.post("/chat", json={"question": "退款"}).json()["sources"] == ["faq.md"]
    assert client.post("/chat", json={"question": ""}).status_code == 422


class Product:
    def handle(self, question, **context):
        return ApplicationResult(
            SupportAnswer(f"{context['session_id']}:{question}", ("faq.md",)),
            "T-1",
        )


def test_api_calls_the_cumulative_product_not_a_new_chat_implementation():
    response = TestClient(create_app(Product())).post(
        "/chat", json={"question": "退款", "session_id": "s1"}
    )

    assert response.json()["answer"] == "s1:退款"
    assert response.json()["ticket_id"] == "T-1"
