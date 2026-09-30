import pytest

from src.enterprise_support.sql_guard import (
    CatalogQuery,
    QueryCatalog,
    SqlPolicyError,
    reject_expensive_plan,
    validate_read_only_sql,
)


def test_catalog_allows_parameterized_read_only_query_for_authorized_role():
    catalog = QueryCatalog(
        {"order_status": CatalogQuery("SELECT id,status FROM orders WHERE id=%s LIMIT 1", frozenset({"support"}))},
        allowed_tables={"orders"},
    )
    assert catalog.get("order_status", ["support"]).startswith("SELECT")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM orders WHERE id=1",
        "WITH x AS (DELETE FROM orders RETURNING id) SELECT * FROM x LIMIT 1",
        "SELECT * FROM orders; DROP TABLE orders",
    ],
)
def test_dynamic_sql_rejects_write_and_multi_statement_bypasses(sql):
    with pytest.raises(SqlPolicyError):
        validate_read_only_sql(sql, allowed_tables={"orders"})


def test_plan_gate_rejects_unbounded_sequential_scan():
    with pytest.raises(SqlPolicyError):
        reject_expensive_plan([{"Plan": {"Node Type": "Seq Scan", "Plan Rows": 1_000_000}}])


def test_catalog_rejects_unknown_query_and_unauthorized_role():
    catalog = QueryCatalog(
        {"order_status": CatalogQuery("SELECT id FROM orders WHERE id=%s LIMIT 1", frozenset({"support"}))},
        allowed_tables={"orders"},
    )
    with pytest.raises(SqlPolicyError):
        catalog.get("delete_all", ["support"])
    with pytest.raises(PermissionError):
        catalog.get("order_status", ["guest"])
