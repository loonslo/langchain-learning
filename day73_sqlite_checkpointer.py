"""
Day 73 · checkpointer 落盘：SqliteSaver 让"重启不失忆"
==========================================================
测试工程师转 AI 应用开发  ← 1-33 补充包（Agent 段·补缺口：持久化落盘）

Day35 讲了 checkpointer 给 Agent 加记忆，但从 Day35 到 Day39 全程用的是
InMemorySaver——它把状态存在【内存】里：进程一退，记忆全没。Demo 没问题，
可真实服务会重启（发版、崩溃、扩缩容），InMemorySaver 一重启，所有人的
会话状态清零。这在生产是事故。

解法一行到位：把 InMemorySaver 换成【落盘】的 checkpointer——SqliteSaver
（本机/单机）或 PostgresSaver（生产）。状态写进数据库文件，进程重启后，
用同一个 thread_id 还能把上次的会话接着聊。compile 只改一个参数，图逻辑不动。

三段：
【一】InMemorySaver 的坑：新建一个（模拟重启）就读不到上次的状态。
【二】SqliteSaver：两次独立打开同一个 .sqlite 文件（模拟两次运行/重启），
    第二次还能读到第一次存的会话——因为状态在磁盘文件里，不在内存。
【三】写法：from_conn_string（with 上下文）/ 直接构造两种；换 Postgres 同理。

依赖：pip install langgraph-checkpoint-sqlite  （没装本文件会提示并跳过第二段）
衔接：Day35 用 InMemorySaver 建立记忆概念；今天把它落盘上生产；
      长期记忆 Store（Day72）同样要落盘，道理一致。
==========================================================
"""

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage

# SqliteSaver 在独立子包里，可能没装——优雅降级，保证本文件始终能跑
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

DB = "day73_checkpoints.sqlite"   # checkpoint 落盘到这个文件


# —— 一个不调 LLM 的最小对话图：便于无 API key 也能验证"记忆在不在" ——
# turn 节点根据"目前累积了多少条消息"生成回复；MessagesState 的 add_messages
# 会自动把每轮消息累积起来（多轮记忆的本质，见 Day29）。
def make_graph(checkpointer):
    def turn(state: MessagesState) -> dict:
        n = len(state["messages"])   # 含本轮刚进来的用户消息
        return {"messages": [AIMessage(content=f"收到，我这条之前已经有 {n} 条消息在记忆里")]}

    g = StateGraph(MessagesState)
    g.add_node("turn", turn)
    g.add_edge(START, "turn")
    g.add_edge("turn", END)
    return g.compile(checkpointer=checkpointer)


# ============================================================
# 【一】InMemorySaver：重启即丢
# ============================================================
def demo_inmemory_lost():
    cfg = {"configurable": {"thread_id": "t1"}}

    app1 = make_graph(InMemorySaver())
    app1.invoke({"messages": [HumanMessage(content="你好，这是第一轮")]}, cfg)
    print("  存入后，app1 里 thread=t1 有",
          len(app1.get_state(cfg).values["messages"]), "条消息")

    # 模拟"重启"：新建另一个 InMemorySaver（等于新进程的空内存）
    app2 = make_graph(InMemorySaver())
    st = app2.get_state(cfg)
    print("  重启(新建 InMemorySaver)后读同一 thread：",
          f"{len(st.values['messages'])} 条" if st.values else "空 → 记忆丢了 ✗")


# ============================================================
# 【二】SqliteSaver：落盘，重启还在
# ============================================================
def demo_sqlite_persist():
    if not HAS_SQLITE:
        print("  未安装 langgraph-checkpoint-sqlite，跳过。")
        print("  安装后即可验证落盘：pip install langgraph-checkpoint-sqlite")
        return

    cfg = {"configurable": {"thread_id": "t1"}}

    # —— 第一次运行：打开 db 文件，存一轮，然后关闭连接（模拟进程结束）——
    with SqliteSaver.from_conn_string(DB) as saver:
        app = make_graph(saver)
        app.invoke({"messages": [HumanMessage(content="你好，这是第一轮")]}, cfg)
        n = len(app.get_state(cfg).values["messages"])
        print(f"  第一次运行：存入并关闭，thread=t1 现有 {n} 条消息")

    # —— 第二次运行：重新打开【同一个 db 文件】（模拟重启进程）——
    with SqliteSaver.from_conn_string(DB) as saver:
        app = make_graph(saver)
        st = app.get_state(cfg)
        n = len(st.values["messages"]) if st.values else 0
        print(f"  重启后再打开：读到 thread=t1 的 {n} 条消息 → 记忆还在 ✓")

        # 而且能直接接着聊——历史自动带上（不用手动塞回）
        app.invoke({"messages": [HumanMessage(content="我们聊到哪了？")]}, cfg)
        print(f"  续聊一轮后共 {len(app.get_state(cfg).values['messages'])} 条（历史被自动带上）")


# ============================================================
# 【三】两种写法 + 生产选型（示意，不执行）
# ============================================================
WRITE_STYLES = """
写法A（推荐，自动开关连接）：
    with SqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
        app = graph.compile(checkpointer=saver)
        ...   # 用完自动关连接

写法B（长驻服务，手动持有连接）：
    import sqlite3
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    saver = SqliteSaver(conn)
    app = graph.compile(checkpointer=saver)

生产：换 PostgresSaver（langgraph-checkpoint-postgres），
    from_conn_string("postgresql://...")，其余一模一样——落盘选型只改这一行。
"""


if __name__ == "__main__":
    print("===== 【一】InMemorySaver：重启即丢 =====")
    demo_inmemory_lost()
    print("\n===== 【二】SqliteSaver：落盘，重启还在 =====")
    demo_sqlite_persist()
    print("\n===== 【三】写法与生产选型 =====")
    print(WRITE_STYLES)


# ----------------------------------------------------------
# 小结：
# - InMemorySaver 把状态存内存，进程一退全丢——只能用于 demo/测试，不能上生产。
# - SqliteSaver 把每步 checkpoint 落到 .sqlite 文件；重启后用同一 thread_id
#   还能读回会话、接着聊。改的只是 compile 的 checkpointer 参数，图逻辑不动。
# - 验证思路：两次独立打开同一 db 文件（模拟重启），第二次读得到第一次的状态。
# - 生产默认 PostgresSaver（复用现成 Postgres、少维护一个组件）；写法与 Sqlite 一致。
#
# 面试话术：
#   "Demo 我用 InMemorySaver，但它重启即丢，上不了生产。上线时我把 checkpointer
#    换成 SqliteSaver 或 PostgresSaver 落盘——就改 compile 一个参数。这样服务发版、
#    崩溃重启后，用户的会话状态还在，能接着聊。生产我默认 Postgres：复用已有库、
#    少维护一个组件。"
#
# 动手练习：把 make_graph 的 turn 换成真实 LLM（bind 一个工具），用 SqliteSaver 落盘；
#          跑一轮后【真的重新运行本文件】，验证多轮对话历史续得上（而不是从零开始）。
# ----------------------------------------------------------
