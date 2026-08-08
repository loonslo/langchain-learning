from customer_support.thread_store import Message, SQLiteThreadStore


def test_the_product_thread_store_creates_a_verified_backup(tmp_path):
    store = SQLiteThreadStore(tmp_path / "threads.db")
    store.append("shop", "alice", "t1", Message("user", "退款"))

    target = store.backup_to(tmp_path / "backup.db")

    assert SQLiteThreadStore(target).load("shop", "alice", "t1") == [
        Message("user", "退款")
    ]
