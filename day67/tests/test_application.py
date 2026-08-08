from customer_support.application import ApplicationResult
from customer_support.assistant import SupportAnswer
from customer_support.observability import ObservedApplication, Recorder


class Product:
    def handle(self, question, **kwargs):
        return ApplicationResult(SupportAnswer(question, ()))


def test_real_product_call_is_observed_without_recording_question():
    recorder = Recorder()
    app = ObservedApplication(Product(), recorder)

    app.handle("退款多久到账？", tenant_id="shop")

    assert recorder.records[0].operation == "support.handle"
    assert recorder.records[0].tenant == "shop"
    assert not hasattr(recorder.records[0], "question")
