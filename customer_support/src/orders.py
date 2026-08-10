"""受控订单查询：订单编号与可信用户身份必须同时匹配。"""

from dataclasses import dataclass


class OrderNotFound(Exception):
    """订单编号在仓库中不存在。"""


class ForbiddenOrder(Exception):
    """订单存在，但不属于当前已认证用户。"""


@dataclass(frozen=True)
class Order:
    """订单查询所需的最小只读快照。

    ``user_id`` 是订单归属校验依据；``frozen=True`` 防止查询结果在传递途中被修改。
    """

    order_id: str
    user_id: str
    status: str


class OrderRepository:
    """以内存字典保存订单，并执行“订单号 + 用户”双重校验。"""

    def __init__(self, orders):
        """按订单号建立索引，使一次查询无需遍历全部订单。"""

        # 字典推导式以 order_id 为键；若输入中编号重复，最后一条记录会覆盖前一条。
        self.orders = {x.order_id: x for x in orders}

    def get_for_user(self, order_id: str, user_id: str) -> Order:
        """仅当订单存在且属于指定用户时返回订单，否则抛出对应业务异常。"""

        order = self.orders.get(order_id)
        if not order:
            raise OrderNotFound(order_id)
        # 先查存在性再校验归属，调用层可按需要区分两种失败原因。
        if order.user_id != user_id:
            raise ForbiddenOrder(order_id)
        return order
