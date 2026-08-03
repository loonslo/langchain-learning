from fastapi.testclient import TestClient
from customer_support.api import create_app
from customer_support.assistant import SupportAnswer


class Fake:
    def ask(self, q):
        return SupportAnswer(q, ("faq.md",))


def test_api_schema_and_validation():
    client = TestClient(create_app(Fake()))
    assert client.post("/chat", json={"question": "退款"}).json()["sources"] == ["faq.md"]
    assert client.post("/chat", json={"question": ""}).status_code == 422
