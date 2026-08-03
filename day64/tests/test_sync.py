from customer_support.sync import plan


def test_sync_distinguishes_change_and_delete():
    result = plan({"a": "old", "gone": "x"}, {"a": "new"})
    assert result.upsert == ("a",) and result.delete == ("gone",)
