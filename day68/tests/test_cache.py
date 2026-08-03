from customer_support.cache import AnswerCache


def test_cache_is_scoped_and_expires():
    now = [0]
    c = AnswerCache(10, lambda: now[0])
    c.put("a", "v1", "退款", "x")
    assert c.get("b", "v1", "退款") is None and c.get("a", "v2", "退款") is None
    now[0] = 11
    assert c.get("a", "v1", "退款") is None
