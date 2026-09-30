from customer_support.application import ApplicationResult
from customer_support.assistant import SupportAnswer
from customer_support.privacy import PrivacyApplication


class Product:
    def handle(self, question, **kwargs):
        return ApplicationResult(SupportAnswer(question, ()))


def test_product_audit_keeps_only_the_redacted_question():
    app = PrivacyApplication(Product())
    result = app.handle("手机号13812345678，查订单A1")

    assert "13812345678" in result.answer.text
    assert app.audit_log == [
        {"question": "手机号[PHONE]，查订单A1", "pii_kinds": ("phone",)}
    ]
