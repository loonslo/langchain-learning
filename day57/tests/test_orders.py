import pytest
from customer_support.orders import ForbiddenOrder, Order, OrderRepository


def test_order_query_enforces_ownership():
    repo = OrderRepository([Order("A1", "alice", "已发货")])
    assert repo.get_for_user("A1", "alice").status == "已发货"
    with pytest.raises(ForbiddenOrder):
        repo.get_for_user("A1", "bob")
