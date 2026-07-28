"""
Day 72 · 长期记忆 Store：跨会话记住"这个用户是谁"
==========================================================
测试工程师转 AI 应用开发  ← 1-33 补充包（Agent 段·补缺口：长期记忆）

Day35 的 checkpointer 让 Agent 有了"记忆"，但那是【短期记忆】：
按 thread_id 隔离，只在【同一个会话内】有效。用户明天新开一轮对话（换 thread），
checkpointer 里那份历史就跟这轮无关了——对新会话等于"失忆"。

企业 Agent 要的是【长期记忆】：跨会话记住"这个用户叫什么、什么背景、偏好什么"。
这靠 LangGraph 的 Store。它和 checkpointer 是两套东西、各管一段：

  checkpointer（Day35） = 短期：一个会话(thread)内的状态快照，多轮/中断恢复靠它
  Store（今天）         = 长期：跨会话、按用户存的记忆，换 thread 也还在

三段：
【一】Store 基础：put / get / search，用 namespace 分层按用户隔离。
【二】图里用 Store：compile(store=...)，节点用 `*, store` 注入，跨会话读写。
【三】对比：同一个 app 换 thread_id，checkpointer 忘了上一会话，Store 还记得。

衔接：Day35 短期记忆(checkpointer)；今天长期记忆(Store)。生产里两者常一起用——
      会话内靠 checkpointer，跨会话靠 Store。capstone 的"认得老用户"就靠它。
      注意：本文件用 InMemoryStore 演示（重启即丢）；真长期要落盘 Store
      （PostgresStore 等），落盘思路和 Day73 的 SqliteSaver 一致。
==========================================================
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore


# ============================================================
# 【一】Store 基础：put / get / search（不涉及图，先认清 API）
# ============================================================
def demo_store_basics():
    store = InMemoryStore()
    # namespace 是一个 tuple，按层级隔离——把不同用户的记忆分开放，互不串
    ns = ("user", "u1", "memories")
    # put(namespace, key, value)：value 必须是 dict
    store.put(ns, "name", {"value": "ajar"})
    store.put(ns, "background", {"value": "测试工程师转 AI 应用开发"})
    store.put(ns, "pref", {"value": "中文、简洁、以转行为第一目标"})

    # get(namespace, key) → Item，取 .value 拿回存进去的 dict
    print("  get name →", store.get(ns, "name").value["value"])
    # search(namespace_prefix) → 该用户名下所有记忆条目
    print("  search 全部记忆 →",
          [(it.key, it.value["value"]) for it in store.search(ns)])
    # 换个用户 namespace，读不到 u1 的记忆（天然隔离）
    print("  换 u2 读 name →", store.get(("user", "u2", "memories"), "name"))


# ============================================================
# 【二】图里用 Store：节点用 `*, store` 注入，跨会话读写
# ============================================================
class ChatState(TypedDict):
    user_id: str      # 谁在说话——长期记忆按它隔离
    message: str      # 用户这轮说的话
    reply: str        # 助手回复


def remember(state: ChatState, *, store: BaseStore) -> dict:
    """从用户消息里抽取"值得长期记住的事"，写进 Store。
    这里用最朴素的规则抽取（"我叫X"→记住名字）；真实项目可换 LLM 抽取记忆。"""
    ns = (state["user_id"], "memories")
    msg = state["message"]
    if "我叫" in msg:
        name = msg.split("我叫")[-1].strip("，。！、 ")
        store.put(ns, "name", {"value": name})
        print(f"  [remember] 写入长期记忆：name = {name}")
    return {}


def respond(state: ChatState, *, store: BaseStore) -> dict:
    """回复前先查长期记忆——认不认得这个用户，就看 Store 里有没有他。"""
    ns = (state["user_id"], "memories")
    item = store.get(ns, "name")
    who = item.value["value"] if item else "朋友"
    return {"reply": f"你好，{who}！（这句里的名字来自长期记忆，换会话也认得你）"}


def build_app():
    g = StateGraph(ChatState)
    g.add_node("remember", remember)
    g.add_node("respond", respond)
    g.add_edge(START, "remember")
    g.add_edge("remember", "respond")
    g.add_edge("respond", END)
    # 同时挂两套记忆：checkpointer 管会话内、store 管跨会话
    return g.compile(checkpointer=InMemorySaver(), store=InMemoryStore())


# ============================================================
# 【三】对比：换 thread_id（新会话），checkpointer 忘了、Store 还记得
# ============================================================
def demo_cross_session():
    app = build_app()

    # —— 会话1（thread s1）：告诉它我叫谁 ——
    app.invoke({"user_id": "u1", "message": "你好，我叫 ajar", "reply": ""},
               {"configurable": {"thread_id": "s1"}})

    # —— 会话2（thread s2，全新会话）：只说"你好"，不再自报名字 ——
    # checkpointer 按 thread 隔离：s2 里没有 s1 的对话历史（短期记忆断了）；
    # 但 Store 按 user_id 存：s2 依然读得到 u1 的 name（长期记忆还在）。
    r2 = app.invoke({"user_id": "u1", "message": "你好", "reply": ""},
                    {"configurable": {"thread_id": "s2"}})
    print("  换新会话(s2) 只说'你好' →", r2["reply"])

    # —— 换个用户 u2 的新会话：Store 里没有 u2 → 认不出 ——
    r3 = app.invoke({"user_id": "u2", "message": "你好", "reply": ""},
                    {"configurable": {"thread_id": "s3"}})
    print("  换新用户(u2) →", r3["reply"])


if __name__ == "__main__":
    print("===== 【一】Store 基础：put / get / search =====")
    demo_store_basics()
    print("\n===== 【二/三】图里用 Store：跨会话记住用户 =====")
    demo_cross_session()


# ----------------------------------------------------------
# 小结：
# - 两种记忆分工：checkpointer=短期(会话内，按 thread_id)；Store=长期(跨会话，按 user_id)。
# - Store 三件事：put(namespace, key, dict) 写、get 取、search(prefix) 列；namespace 用
#   tuple 分层做隔离（不同用户/不同类别互不串）。
# - 图里用：compile(store=...) 挂上，节点签名加 `*, store: BaseStore` 就能注入读写。
# - 换 thread_id 后 checkpointer 断了历史，但 Store 还认得用户——这就是"长期记忆"。
# - InMemoryStore 重启即丢，只用于学习/测试；生产用落盘 Store（PostgresStore 等），
#   落盘道理同 Day73 的 SqliteSaver。
#
# 面试话术：
#   "短期记忆和长期记忆我分开做：会话内的多轮上下文用 checkpointer 按 thread 存；
#    跨会话'记住这个用户是谁、什么偏好'用 Store 按 user_id 存。换一个会话，
#    checkpointer 的历史不串，但 Store 里的用户画像还在——这才是企业 Agent
#    '认得老用户、越用越懂你'的做法，而不是每次都从零开始。"
#
# 动手练习：给 respond 接上 LLM，把 Store 里读到的用户背景拼进 system prompt
#          （如"这是个测试转 AI 的用户，多用测试术语类比"），做出"千人千面"的回复。
# ----------------------------------------------------------
