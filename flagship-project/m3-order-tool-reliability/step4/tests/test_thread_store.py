from customer_support.thread_store import Message, SQLiteThreadStore


def test_messages_persist_and_are_isolated(tmp_path):
    path = tmp_path / "chat.db"
    SQLiteThreadStore(path).append("a", "alice", "t1", Message("user", "秘密"))
    store = SQLiteThreadStore(path)
    assert store.load("a", "alice", "t1") == [Message("user", "秘密")]
    assert store.load("b", "alice", "t1") == []
