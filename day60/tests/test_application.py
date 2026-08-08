from customer_support.application import SupportApplication
from customer_support.assistant import SupportAnswer
from customer_support.conversation import PersistentHistory
from customer_support.thread_store import SQLiteThreadStore


class Assistant:
    def __init__(self):
        self.questions = []

    def ask(self, question):
        self.questions.append(question)
        return SupportAnswer(question, ("faq.md",))


def test_product_follow_up_survives_history_object_restart(tmp_path):
    path = tmp_path / "threads.db"
    SupportApplication(Assistant(), PersistentHistory(SQLiteThreadStore(path))).ask(
        "退款多久？", session_id="t1", tenant_id="shop", user_id="alice"
    )
    assistant = Assistant()
    SupportApplication(assistant, PersistentHistory(SQLiteThreadStore(path))).ask(
        "那发票呢？", session_id="t1", tenant_id="shop", user_id="alice"
    )

    assert "上一问题：退款多久？" in assistant.questions[-1]
