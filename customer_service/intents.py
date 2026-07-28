"""
customer_service/intents.py · 意图分类：客服的第一道路由（复用 Day32 结构化输出）
==========================================================
为什么不用关键词 in 匹配做主方案：自由文本脆（Day32 的教训）。
生产方案 = Pydantic 结构化输出，模型只能从枚举里选一个，代码拿确定字段。

离线兜底 = 规则分类：CI / 无 key 环境可跑，同时它就是评估里的 baseline——
"规则 vs LLM 意图准确率对比"本身就是一条护城河故事。
==========================================================
"""

from typing import Literal

from pydantic import BaseModel, Field

import config as C


class Intent(BaseModel):
    """强约束：intent 只能是四类之一（Day32 同款）。"""
    intent: Literal["faq", "order", "complaint", "chitchat"] = Field(
        description="用户消息的意图：faq=咨询产品/政策，order=查订单物流退款进度，"
                    "complaint=投诉/强烈不满，chitchat=寒暄闲聊"
    )
    reason: str = Field(description="一句话分类依据（便于观测与失败归因）")


# ---- 规则 baseline（离线模式 / 对照组）----
_RULES = [
    ("complaint", ["投诉", "太差", "垃圾", "生气", "举报", "退钱", "骗"]),
    ("order",     ["订单", "物流", "快递", "发货", "到哪", "退款进度", "单号"]),
    ("chitchat",  ["你好", "在吗", "谢谢", "再见", "早上好", "哈哈"]),
]


def classify_rule(text: str) -> Intent:
    for intent, kws in _RULES:
        if any(k in text for k in kws):
            return Intent(intent=intent, reason=f"命中规则关键词（{intent}）")
    return Intent(intent="faq", reason="未命中规则，默认按咨询处理")


def classify_llm(text: str) -> Intent:
    """LLM 结构化分类（Day32 的 PydanticOutputParser 方案，兼容 DeepSeek）。"""
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.output_parsers import PydanticOutputParser

    parser = PydanticOutputParser(pydantic_object=Intent)
    llm = C.get_llm()
    msg = llm.invoke([
        SystemMessage(content="你是客服意图分类器。只输出 JSON。\n"
                              + parser.get_format_instructions()),
        HumanMessage(content=text),
    ])
    return parser.parse(msg.content)


def classify(text: str) -> Intent:
    if C.OFFLINE:
        return classify_rule(text)
    try:
        return classify_llm(text)
    except Exception:                    # LLM 失败降级到规则（Day31 可靠性思路）
        return classify_rule(text)
