"""
Day 34 · 可观测性与调试：Agent 出了问题怎么查（护城河）
==========================================================
测试工程师转 AI 应用开发  ← 补生产缺口#4（承接 Day33，垫 Day35）

Agent 最难的不是搭出来，是"它答错了，你不知道错在哪一步"。
生产 Agent 必须"每一步看得见、可复盘"。这正是测试背景的护城河：
别人只会让 Agent 跑，你能把它的每一步轨迹结构化落盘，出错时定位到具体节点。

三层可观测，从内到外：
【一】stream_mode 四件套：看清图内部每一步在干什么（Day36 只用了 updates，这里补全）。
    - "updates"：每个节点这一步改了 state 的哪些字段（调试首选）
    - "values" ：每步之后完整 state 长啥样
    - "messages"：逐 token 流式输出（做打字机效果）
    - "debug"  ：最详细，含节点进出、耗时
【二】结构化轨迹落盘：把每一步（节点名/耗时/输入输出摘要）写成 JSONL，一行一步。
    出错时 grep 一下就知道哪步慢、哪步崩——比 print 强在可检索、可回归对比。
【三】LangSmith 追踪：设两个环境变量就自动把每次运行上报，网页上看完整调用树。
    （呼应 Day22 LangSmith 评测——同一套追踪，一个用来看、一个用来评。）

衔接：Day33 会规划了；上持久化(Day35)前先学会"看得见"；Day37 的 print 轨迹在这升级成可复盘落盘。
==========================================================
"""

import json
import os
import time
from pathlib import Path
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,
    )


# —— 一个多步小图，用来演示"怎么把它看透" ——
class State(TypedDict):
    topic: str
    draft: str
    review: str


def plan(state: State) -> dict:
    time.sleep(0.05)   # 模拟耗时，方便看到各步时长差异
    return {"draft": f"关于「{state['topic']}」的初稿"}


def write(state: State) -> dict:
    time.sleep(0.12)
    return {"draft": state["draft"] + "：三段式展开…"}


def review(state: State) -> dict:
    time.sleep(0.03)
    return {"review": "审校通过"}


def build():
    g = StateGraph(State)
    g.add_node("plan", plan)
    g.add_node("write", write)
    g.add_node("review", review)
    g.add_edge(START, "plan")
    g.add_edge("plan", "write")
    g.add_edge("write", "review")
    g.add_edge("review", END)
    return g.compile()


# ============================================================
# 【一】stream_mode 四件套：看清每一步
# ============================================================
def demo_stream_modes():
    app = build()
    inp = {"topic": "LangGraph 可观测性", "draft": "", "review": ""}

    print("① updates —— 每个节点改了哪些字段（调试首选）：")
    for chunk in app.stream(dict(inp), stream_mode="updates"):
        print("   ", chunk)

    print("\n② values —— 每步之后的完整 state：")
    for chunk in app.stream(dict(inp), stream_mode="values"):
        print("   ", chunk)
        # print("   ", {k: (v[:20] + "…" if isinstance(v, str) and len(v) > 20 else v)
        #                 for k, v in chunk.items()})

    print("\n③ debug —— 最详细（节点进出/类型）：")
    for chunk in app.stream(dict(inp), stream_mode="debug"):
        print("   ", chunk)
        # print("   ", chunk.get("type"), "→", chunk.get("payload", {}).get("name", ""))
    # ④ messages 模式需要节点产出 LLM 消息才有意义，见文末动手练习


# ============================================================
# 【二】结构化轨迹落盘：每步一行 JSONL，可检索、可回归
# ============================================================
def run_with_trace(app, inp: dict, trace_path: str) -> dict:
    """跑图的同时，把每一步写成结构化轨迹（比 print 强：可 grep、可 diff、可回归）。"""
    Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
    last_state = dict(inp)
    with open(trace_path, "w", encoding="utf-8") as f:
        t0 = time.time()
        for chunk in app.stream(dict(inp), stream_mode="updates"):
            for node, update in chunk.items():
                record = {
                    "ts": round(time.time() - t0, 3),   # 相对耗时，看哪步慢
                    "node": node,                        # 哪个节点
                    "update_keys": list(update.keys()),  # 改了哪些字段
                    "preview": {k: str(v)[:40] for k, v in update.items()},
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                last_state.update(update)
    return last_state


def demo_trace():
    app = build()
    trace = "reports/day34_trace.jsonl"
    run_with_trace(app, {"topic": "轨迹落盘", "draft": "", "review": ""}, trace)
    print(f"轨迹已落盘：{trace}，逐行如下：")
    for line in Path(trace).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        print(f"   +{r['ts']}s  {r['node']:8s}  改了 {r['update_keys']}")
    print("→ 出错时：grep 报错节点、按 ts 找最慢步、和上次 trace 做 diff 看回归。")





if __name__ == "__main__":
    print("===== 【一】stream_mode 四件套 =====")
    demo_stream_modes()
    print("\n===== 【二】结构化轨迹落盘（护城河）=====")
    demo_trace()



# ----------------------------------------------------------
# 小结：
# - Agent 生产的隐形门槛是可观测：答错了要能定位到"哪一步、为什么"。
# - stream_mode：updates 看增量（调试首选）、values 看全量、messages 逐 token、debug 最细。
# - 结构化轨迹落盘（JSONL 每步一行）胜过 print：可检索、可回归 diff、可算每步耗时。
#
# 面试话术：
#   "我不靠猜调 Agent：每一步都结构化落盘（节点名/耗时/输入输出摘要），出错时能定位到
#    具体哪一步、为什么错，还能和上次的 trace 做 diff 看有没有回归——这套'每步可观测、
#    可复盘'正是我测试背景的护城河，而不是反复重跑碰运气。"
#
# 动手练习：给 Day37 的搜索 Agent 用 stream_mode='messages' 做打字机流式输出，
#          同时把每步轨迹用本节 run_with_trace 落盘到 reports/，出错时按 trace 复盘。
# ----------------------------------------------------------
