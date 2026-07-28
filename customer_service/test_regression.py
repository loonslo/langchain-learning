"""
customer_service/test_regression.py · pytest 回归（离线可跑，进 CI 门禁）
==========================================================
与 capstone/test_regression.py 同思路：宽松断言 + 指标阈值，不做精确字符串匹配。
运行：pytest customer_service/test_regression.py -v
==========================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evaluation
import graph
import intents
import tools


def test_intent_rules():
    assert intents.classify_rule("我要投诉你们").intent == "complaint"
    assert intents.classify_rule("订单 A1001 到哪了").intent == "order"
    assert intents.classify_rule("你好在吗").intent == "chitchat"
    assert intents.classify_rule("退货政策是什么").intent == "faq"


def test_order_tool():
    assert tools.extract_order_id("查一下 A1001 的物流") == "A1001"
    assert "已发货" in tools.query_order("A1001")
    assert "没有查到" in tools.query_order("Z9999")


def test_graph_routes_and_answers():
    out = graph.chat("t-faq", "退货政策是什么样的")
    assert out["intent"] == "faq" and "退货" in out["answer"]

    out = graph.chat("t-order", "帮我查订单 A1002")
    assert out["intent"] == "order" and "A1002" in out["answer"]

    out = graph.chat("t-comp", "太差了我要投诉")
    assert out["escalated"] and "工单" in out["answer"]


def test_multiturn_order_reference():
    """多轮指代：第二轮不带单号，应从会话历史里找回 A1003。"""
    sid = "t-multi"
    graph.chat(sid, "帮我查下订单 A1003")
    out = graph.chat(sid, "就是刚才那个订单，物流呢")
    assert "A1003" in out["answer"]


def test_eval_metrics_gate():
    """质量门禁：指标掉到阈值以下即测试失败（CI 挡合并）。"""
    m = evaluation.run()
    assert m["intent_acc"] >= 0.9
    assert m["resolution_rate"] >= 0.7
    assert m["escalation_correct"] >= 0.9
