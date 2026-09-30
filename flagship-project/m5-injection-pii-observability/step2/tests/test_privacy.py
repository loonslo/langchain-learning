from customer_support.privacy import redact


def test_pii_is_removed_but_order_id_remains():
    text, kinds = redact("手机13812345678 邮箱a@example.com 订单A1")
    assert (
        "138" not in text
        and "example" not in text
        and "A1" in text
        and kinds == ("phone", "email")
    )
