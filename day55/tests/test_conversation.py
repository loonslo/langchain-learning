from customer_support.conversation import History, Turn


def test_follow_up_uses_only_same_session_and_history_is_bounded():
    history = History(max_turns=1)
    history.add("a", Turn("退款多久", "3 天"))
    history.add("a", Turn("发票多久", "30 天"))
    assert "发票多久" in history.standalone("a", "那地址呢？")
    assert history.standalone("b", "那地址呢？") == "那地址呢？"
