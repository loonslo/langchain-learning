from fastapi.testclient import TestClient

from customer_support.api import create_app
from customer_support.application import ApplicationResult
from customer_support.assistant import SupportAnswer
from customer_support.auth import Identity, TokenVerifier


class Product:
    def handle(self, question, **context):
        return ApplicationResult(
            SupportAnswer(f"{context['user_id']}:{question}", ("faq.md",))
        )

    def plan_sync(self, previous):
        raise AssertionError("本测试不走同步路径")


def test_final_api_rejects_missing_token_and_uses_signed_identity():
    verifier = TokenVerifier("day76-test-secret-at-least-32-bytes")
    token = verifier.issue(Identity("shop", "alice"))
    client = TestClient(create_app(Product(), verifier))

    assert client.post("/chat", json={"question": "退款"}).status_code == 401
    response = client.post(
        "/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "退款"},
    )
    assert response.json()["answer"] == "alice:退款"
