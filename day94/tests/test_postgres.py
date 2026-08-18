from src.enterprise_support.postgres import ConversationMessage, PostgresConversationStore


class Cursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))

    def fetchall(self):
        # 仓储的 SQL 已按 created_at DESC 查询；测试替身模拟数据库返回顺序。
        return [("assistant", "请提供订单号"), ("user", "退款")]

    def close(self):
        pass


class Connection:
    def __init__(self):
        self.cursor_instance = Cursor()
        self.commits = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1


def test_repository_sets_transaction_local_tenant_and_parameterizes_message():
    conn = Connection()
    PostgresConversationStore(conn).append(
        tenant_id="shop-a",
        user_id="u1",
        session_id="s1",
        message=ConversationMessage("user", "x'); DROP TABLE conversation_messages;--"),
    )
    scope, insert = conn.cursor_instance.calls
    assert scope[1] == ("shop-a",)
    assert "DROP TABLE" not in insert[0]
    assert insert[1][-1].startswith("x')")
    assert conn.commits == 1


def test_history_scope_comes_from_authenticated_tenant_not_sql_string_formatting():
    conn = Connection()
    messages = PostgresConversationStore(conn).history(
        tenant_id="shop-b", user_id="u2", session_id="s2"
    )
    assert [message.content for message in messages] == ["退款", "请提供订单号"]
    assert conn.cursor_instance.calls[0][1] == ("shop-b",)
