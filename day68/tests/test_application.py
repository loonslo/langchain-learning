from customer_support.application import ApplicationResult
from customer_support.assistant import SupportAnswer
from customer_support.cache import AnswerCache, CachedApplication


class Product:
    def __init__(self):
        self.calls = 0

    def handle(self, question, **kwargs):
        self.calls += 1
        return ApplicationResult(SupportAnswer(question, ("faq.md",)))


def test_cache_is_on_the_product_path_and_order_queries_bypass_it():
    product = Product()
    app = CachedApplication(product, AnswerCache(60, lambda: 0))
    app.handle("退款", tenant_id="shop", version="v1")
    app.handle("退款", tenant_id="shop", version="v1")
    assert product.calls == 1

    app.handle("订单", tenant_id="shop", order_id="A1")
    app.handle("订单", tenant_id="shop", order_id="A1")
    assert product.calls == 3
