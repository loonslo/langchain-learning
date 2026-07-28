"""
customer_service/tools.py · 业务工具：查订单/查物流（模拟数据，复用 Day05/Day38 思路）
==========================================================
安全原则（Day37）：工具只读模拟数据，不做真实写操作；
真实接入时把 _FAKE_ORDERS 换成 API/DB 查询即可，接口不变。
==========================================================
"""

import re

_FAKE_ORDERS = {
    "A1001": {"status": "已发货", "carrier": "顺丰", "eta": "预计明天送达"},
    "A1002": {"status": "待发货", "carrier": "-", "eta": "48 小时内发出"},
    "A1003": {"status": "退款中", "carrier": "-", "eta": "3~5 个工作日原路退回"},
}


def extract_order_id(text: str) -> str | None:
    m = re.search(r"[A-Z]\d{4}", text)
    return m.group(0) if m else None


def query_order(order_id: str) -> str:
    o = _FAKE_ORDERS.get(order_id)
    if not o:
        return f"没有查到订单 {order_id}，请核对订单号"
    return f"订单 {order_id}：{o['status']}（{o['carrier']}），{o['eta']}"
