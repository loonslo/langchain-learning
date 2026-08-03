from fastapi.testclient import TestClient
from customer_support.api import create_app
from customer_support.application import ApplicationResult
from customer_support.assistant import SupportAnswer
from customer_support.auth import Identity, TokenVerifier


class FakeApplication:
    def handle(
        self, identity: Identity, question: str, version: str = "v1", order_id: str = ""
    ):
        return ApplicationResult(
            SupportAnswer(f"{identity.user_id}:{question}", ("faq.md",))
        )


def test_api_uses_signed_identity_and_returns_final_contract():
    verifier = TokenVerifier("day76-test-secret-at-least-32-bytes")
    token = verifier.issue(Identity("shop", "alice"))
    client = TestClient(create_app(FakeApplication(), verifier))
    response = client.post(
        "/chat", headers={"Authorization": f"Bearer {token}"}, json={"question": "退款"}
    )
    assert response.json() == {
        "answer": "alice:退款",
        "sources": ["faq.md"],
        "ticket_id": None,
    }


def test_api_rejects_missing_identity_before_business_call():
    client = TestClient(
        create_app(
            FakeApplication(), TokenVerifier("day76-test-secret-at-least-32-bytes")
        )
    )
    assert client.post("/chat", json={"question": "退款"}).status_code == 401
