"""受控订单查询：订单编号与可信用户身份必须同时匹配。"""

from dataclasses import dataclass


class OrderNotFound(Exception):
    pass


class ForbiddenOrder(Exception):
    pass


@dataclass(frozen=True)
class Order:
    order_id: str
    user_id: str
    status: str


class OrderRepository:
    def __init__(self, orders):
        self.orders = {x.order_id: x for x in orders}

    def get_for_user(self, order_id: str, user_id: str) -> Order:
        order = self.orders.get(order_id)
        if not order:
            raise OrderNotFound(order_id)
        if order.user_id != user_id:
            raise ForbiddenOrder(order_id)
        return order
