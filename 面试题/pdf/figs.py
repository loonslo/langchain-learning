# -*- coding: utf-8 -*-
"""内联 SVG 图表库。全部手写 SVG，不依赖图表库（打印矢量、无 fetch 问题）。

配色为视觉方向「工程网格」：黑白灰 + 单一功能色。
所有形状都显式写 fill，不依赖 CSS 类——类名在打印上下文里不可靠。
图中出现的比例与曲线一律标注「示意」，不编造精确测量值。
"""

INK, MUTE, MUTE2 = "#1c1c1c", "#6b6b6b", "#9a9a9a"
RULE, RULESOFT, LIGHT = "#d8d8d8", "#e8ecee", "#f7f8f9"
BRAND, ACCENT, PAPER = "#1b4fd8", "#b45309", "#ffffff"

FONT = "Helvetica Neue, Microsoft YaHei, PingFang SC, sans-serif"
MONO = "Consolas, Cascadia Mono, Courier New, monospace"

W = 660  # 版心宽度 ≈ 172mm @96dpi


def _svg(h, body, w=W):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" height="auto" '
            f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">'
            f'{body}</svg>')


def _t(x, y, s, size=10, fill=INK, anchor="start", weight="400", mono=False, op=1):
    fam = f' font-family="{MONO}"' if mono else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" opacity="{op}"{fam}>'
            f'{s}</text>')


def _box(x, y, w, h, label, sub="", fill=PAPER, stroke=RULE, tcol=INK,
         size=11, sw=1.1, rx=2):
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
         f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>']
    cy = y + h / 2 + (size * 0.36 if not sub else -1)
    o.append(_t(x + w / 2, cy, label, size=size, fill=tcol,
                anchor="middle", weight="700"))
    if sub:
        o.append(_t(x + w / 2, cy + 14, sub, size=8.4, fill=MUTE, anchor="middle"))
    return "".join(o)


def _arrow(x1, y1, x2, y2, color=MUTE, dash="", sw=1.1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{sw}"{d} marker-end="url(#ah)"/>')


def _defs(color=MUTE):
    return (f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
            f'<marker id="ahb" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{BRAND}"/></marker></defs>')


# ── 图 1　七层知识地图 ─────────────────────────────────────
def fig_map():
    rows = [
        ("01", "Agent 到底是什么", "循环、工具、记忆、目标——和 Workflow 的分界", "Agent Q1–Q4"),
        ("02", "它怎么想：推理与规划", "ReAct / Plan-and-Execute / Reflection，以及任务拆分", "Agent Q5–Q7, Q14"),
        ("03", "它怎么动手：工具调用", "Function Calling、MCP、Skill、A2A 与容错", "工具调用 Q1–Q18"),
        ("04", "它怎么记住：记忆机制", "线程内 State 与跨线程 Store，压缩与遗忘", "Agent Q8–Q9, Q12"),
        ("05", "它怎么变成系统：多 Agent", "协作、动态切换、状态管理与死循环治理", "Agent Q10–Q11, Q16–Q22"),
        ("06", "它怎么活下来：工程化", "上下文、RAG、评估、可观测、安全、成本", "Agent Q17–Q24, RAG Q1–Q21"),
        ("07", "它怎么搭起来：框架选型", "LangChain、LangGraph、LlamaIndex 与手搓的边界", "LangChain Q1–Q12"),
        ("08", "工具箱：面试前 48 小时", "四段式回答、高频追问、红旗清单", "——"),
    ]
    h = 26 + len(rows) * 44 + 8
    o = [_defs()]
    o.append(_t(0, 12, "从下往上：越靠上越接近工程现场；越靠下越是地基", 9, MUTE2))
    y = 26
    for i, (num, title, desc, src) in enumerate(rows):
        last = (i == len(rows) - 1)
        o.append(f'<rect x="0" y="{y}" width="{W}" height="38" fill="'
                 f'{LIGHT if last else PAPER}"/>')
        o.append(f'<rect x="0" y="{y}" width="2.6" height="38" fill="'
                 f'{ACCENT if last else BRAND}"/>')
        o.append(_t(12, y + 24, num, 12, ACCENT if last else BRAND, mono=True,
                    weight="700"))
        o.append(_t(40, y + 17, title, 11.5, INK, weight="700"))
        o.append(_t(40, y + 31, desc, 9, MUTE))
        o.append(_t(W - 4, y + 17, src, 8.2, MUTE2, anchor="end", mono=True))
        o.append(f'<line x1="0" y1="{y+38}" x2="{W}" y2="{y+38}" stroke="{RULESOFT}" '
                 f'stroke-width="1"/>')
        y += 44
    return _svg(h, "".join(o))


# ── 图 2　Agent 的最小循环 ─────────────────────────────────
def fig_loop():
    h = 300
    o = [_defs()]
    b1 = _box(30, 46, 140, 40, "思考", "下一步该做什么")
    b2 = _box(245, 46, 140, 40, "行动", "调用一个工具")
    b3 = _box(460, 46, 170, 40, "观察", "读回工具的结果")
    o += [b1, b2, b3]
    o.append(_arrow(170, 66, 243, 66))
    o.append(_arrow(385, 66, 458, 66))
    o.append(_t(206, 58, "需要外部信息", 8.2, MUTE, anchor="middle"))
    o.append(_t(421, 58, "拿到结果", 8.2, MUTE, anchor="middle"))

    o.append(_box(30, 152, 140, 40, "记忆", "上一轮发生了什么", fill=LIGHT))
    o.append(_box(245, 152, 140, 40, "工具", "真实世界的接口", fill=LIGHT))
    o.append(_box(460, 152, 170, 40, "输出", "已经能回答了", fill=PAPER,
                  stroke=BRAND, tcol=BRAND))
    o.append(_arrow(100, 150, 100, 88, RULE))
    o.append(_arrow(315, 150, 315, 88, RULE))
    o.append(_arrow(545, 88, 545, 150, BRAND))
    o.append(_t(553, 122, "判断：够了", 8.2, BRAND))

    o.append(f'<path d="M 545 192 L 545 240 L 100 240 L 100 194" fill="none" '
             f'stroke="{BRAND}" stroke-width="1.2" stroke-dasharray="4 3" '
             f'marker-end="url(#ahb)"/>')
    o.append(_t(322, 255, "把观察到的结果回灌进上下文，重新思考", 8.6, BRAND,
                anchor="middle"))
    o.append(_t(0, 288, "这个「思考→行动→观察」的圈就是 Agent 的全部秘密。"
                        "差别只在：谁决定圈停不停、圈里的信息存在哪。", 9, MUTE))
    return _svg(h, "".join(o))


# ── 图 3　三种推理范式 ─────────────────────────────────────
def fig_paradigms():
    h = 268
    o = [_defs()]
    cols = [
        ("ReAct", "边想边做", BRAND,
         ["思考", "行动", "观察", "思考", "行动", "观察", "回答"],
         "一步一验证。灵活，但步数多、贵。"),
        ("Plan-and-Execute", "先画图再走", INK,
         ["出计划", "步骤1", "步骤2", "步骤3", "汇总回答", "", ""],
         "计划一次成型。快，但计划错了会一路错下去。"),
        ("Reflection", "做完回头看", ACCENT,
         ["产出初稿", "自我批评", "修订", "再批评", "定稿", "", ""],
         "用一次额外调用换质量。适合写作与代码。"),
    ]
    x = 0
    cw = 208
    for name, tag, col, steps, note in cols:
        o.append(f'<rect x="{x}" y="6" width="{cw-16}" height="{h-46}" fill="{PAPER}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
        o.append(f'<rect x="{x}" y="6" width="{cw-16}" height="3" fill="{col}"/>')
        o.append(_t(x + 12, 30, name, 11.5, col, weight="700"))
        o.append(_t(x + cw - 28, 30, tag, 8.4, MUTE, anchor="end"))
        y = 46
        for s in steps:
            if not s:
                y += 26
                continue
            o.append(f'<rect x="{x+12}" y="{y}" width="{cw-40}" height="20" rx="1.5" '
                     f'fill="{LIGHT}" stroke="{RULESOFT}" stroke-width="1"/>')
            o.append(_t(x + 22, y + 14, s, 8.8, INK))
            if s != steps[-1] and y + 26 < h - 60:
                o.append(_arrow(x + 22 + 4, y + 20, x + 22 + 4, y + 25, RULE, sw=.9))
            y += 26
        o.append(_t(x + 12, h - 26, note, 8.4, MUTE))
        x += cw
    return _svg(h, "".join(o))


# ── 图 4　一次对话里，上下文窗口被谁吃掉了 ─────────────────
def fig_budget():
    h = 176
    o = [_defs()]
    segs = [
        ("系统提示词", 6, BRAND, "你写死的角色与规则"),
        ("工具定义", 14, "#4a6fb5", "每个工具的 JSON Schema"),
        ("历史消息", 32, MUTE2, "越长越占地方"),
        ("检索 / 工具结果", 33, RULESOFT, "最不可控的一块"),
        ("留给模型回答", 15, PAPER, "被挤没了，就开始胡说"),
    ]
    x, y, w, bh = 0, 40, W, 46
    for name, pct, col, note in segs:
        sw = w * pct / 100
        o.append(f'<rect x="{x}" y="{y}" width="{sw}" height="{bh}" fill="{col}" '
                 f'stroke="{PAPER}" stroke-width="1.4"/>')
        if pct >= 12:
            o.append(_t(x + sw / 2, y + 21, f"{pct}%", 11, PAPER if col != RULESOFT
                        and col != PAPER else INK, anchor="middle", weight="700"))
            o.append(_t(x + sw / 2, y + 35, name, 8.4,
                        PAPER if col != RULESOFT and col != PAPER else INK,
                        anchor="middle"))
        x += sw
    o.append(_t(0, 28, "窗口总容量 = 100%（示意：真实比例随项目变化）", 9, MUTE2))
    ly = 104
    for i, (name, pct, col, note) in enumerate(segs):
        o.append(f'<rect x="0" y="{ly}" width="9" height="9" fill="{col}" '
                 f'stroke="{RULE}" stroke-width=".6"/>')
        o.append(_t(15, ly + 8.4, name, 9, INK, weight="700"))
        o.append(_t(130, ly + 8.4, note, 8.6, MUTE))
        ly += 14
    o.append(f'<line x1="0" y1="{y+bh}" x2="{W}" y2="{y+bh}" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    return _svg(h, "".join(o))


# ── 图 5　记忆的两套作用域 ─────────────────────────────────
def fig_memory():
    h = 262
    o = [_defs()]
    o.append(f'<rect x="0" y="8" width="322" height="200" fill="{PAPER}" '
             f'stroke="{BRAND}" stroke-width="1.2"/>')
    o.append(f'<rect x="0" y="8" width="322" height="3" fill="{BRAND}"/>')
    o.append(_t(14, 34, "线程内：跟着这次会话走", 11.5, BRAND, weight="700"))
    o.append(_t(14, 50, "thread_id = 会话的身份证", 8.6, MUTE, mono=True))
    o.append(_box(14, 62, 292, 34, "Agent State", "消息 + 当前步骤 + 中间结果"))
    o.append(_arrow(160, 100, 160, 116, BRAND))
    o.append(_box(14, 118, 292, 34, "Checkpointer", "按 thread_id 存状态快照"))
    o.append(_box(14, 160, 292, 34, "用途", "多轮对话 / 断点恢复 / 人工审批",
                  fill=LIGHT))
    o.append(_t(14, 232, "换一个 thread_id，这套记忆就看不到了。", 8.8, MUTE))

    o.append(f'<rect x="338" y="8" width="322" height="200" fill="{PAPER}" '
             f'stroke="{ACCENT}" stroke-width="1.2"/>')
    o.append(f'<rect x="338" y="8" width="322" height="3" fill="{ACCENT}"/>')
    o.append(_t(352, 34, "跨线程：跟着用户走", 11.5, ACCENT, weight="700"))
    o.append(_t(352, 50, "namespace = (租户, 用户, 记忆类型)", 8.6, MUTE, mono=True))
    o.append(_box(352, 62, 292, 34, "Store", "key → value 的长期仓库"))
    o.append(_arrow(498, 100, 498, 116, ACCENT))
    o.append(_box(352, 118, 292, 34, "召回方式", "按 key 精确取，或向量语义搜"))
    o.append(_box(352, 160, 292, 34, "用途", "用户偏好 / 历史经验 / 工作规则",
                  fill=LIGHT))
    o.append(_t(352, 232, "换会话仍在——所以身份必须来自可信来源。", 8.8, MUTE))
    o.append(_t(0, 254, "两套东西解决的问题不同：一个回答「这次任务走到哪了」，"
                        "一个回答「以后还要记住什么」。", 9, MUTE))
    return _svg(h, "".join(o))


# ── 图 6　一次工具调用的完整链路 ───────────────────────────
def fig_toolcall():
    h = 246
    o = [_defs()]
    lanes = [("用户", 40), ("Agent", 190), ("模型", 340), ("运行时", 480), ("外部工具", 600)]
    for name, x in lanes:
        o.append(_t(x, 16, name, 9, MUTE, anchor="middle", weight="700"))
        o.append(f'<line x1="{x}" y1="26" x2="{x}" y2="{h-30}" stroke="{RULESOFT}" '
                 f'stroke-width="1" stroke-dasharray="2 3"/>')
    steps = [
        (0, 1, "提出问题", INK),
        (1, 2, "把问题 + 工具清单一起发过去", INK),
        (2, 3, "「我要调 order_query，参数 X」", BRAND),
        (3, 4, "执行真正的函数（鉴权在这里做）", BRAND),
        (4, 3, "返回结果或错误", MUTE),
        (3, 2, "以 ToolMessage 形式回灌", MUTE),
        (2, 1, "模型决定：再调一次，还是给答案", INK),
        (1, 0, "最终回答", INK),
    ]
    y = 44
    for a, b, label, col in steps:
        x1, x2 = lanes[a][1], lanes[b][1]
        o.append(_arrow(x1, y, x2, y, col, sw=1.1))
        mid = (x1 + x2) / 2
        anchor = "middle"
        o.append(_t(mid, y - 5, label, 8.2, col, anchor=anchor))
        y += 24
    o.append(_t(0, h - 12, "关键：模型只生成「调用请求」，真正执行的是应用侧代码。"
                           "所以权限校验必须放在运行时那一列，不能指望模型自觉。", 9, MUTE))
    return _svg(h, "".join(o))


# ── 图 7　Function Calling / MCP / Skill 各管一层 ──────────
def fig_layers():
    h = 236
    o = [_defs()]
    bands = [
        ("Skill", "把一套「怎么做这件事」打包：步骤、脚本、参考资料",
         "面向任务", ACCENT, 8),
        ("MCP", "把工具、资源、提示词变成跨应用可复用的标准接口",
         "面向连接", BRAND, 74),
        ("Function Calling", "模型与运行时之间的调用约定：要调谁、传什么参数",
         "面向协议", INK, 140),
    ]
    for name, desc, tag, col, y in bands:
        o.append(f'<rect x="0" y="{y}" width="{W}" height="56" fill="{PAPER}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
        o.append(f'<rect x="0" y="{y}" width="3" height="56" fill="{col}"/>')
        o.append(_t(16, y + 24, name, 12, col, weight="700"))
        o.append(_t(16, y + 42, desc, 9, MUTE))
        o.append(_t(W - 8, y + 24, tag, 8.6, MUTE2, anchor="end"))
    o.append(_arrow(330, 140, 330, 132, MUTE, sw=.9))
    o.append(_arrow(330, 74, 330, 66, MUTE, sw=.9))
    o.append(_t(0, 222, "它们不是互相替代的关系：一次调用里，Function Calling 是动词，"
                        "MCP 是插头标准，Skill 是打包好的操作手册。", 9, MUTE))
    return _svg(h, "".join(o))


# ── 图 8　RAG 的两条链路 ───────────────────────────────────
def fig_rag():
    h = 226
    o = [_defs()]
    o.append(_t(0, 14, "离线：把资料变成可检索的东西", 10, BRAND, weight="700"))
    off = ["接入", "解析", "切分", "向量化", "入库"]
    x = 0
    bw = 118
    for i, s in enumerate(off):
        o.append(f'<rect x="{x}" y="24" width="{bw-14}" height="30" rx="2" '
                 f'fill="{LIGHT}" stroke="{RULESOFT}" stroke-width="1"/>')
        o.append(_t(x + (bw - 14) / 2, 43, s, 9.4, INK, anchor="middle"))
        if i < len(off) - 1:
            o.append(_arrow(x + bw - 14, 39, x + bw - 3, 39, RULE, sw=.9))
        x += bw
    o.append(_t(0, 78, "在线：回答这一次提问", 10, ACCENT, weight="700"))
    on = ["改写问题", "多路召回", "重排", "拼上下文", "生成回答"]
    x = 0
    for i, s in enumerate(on):
        o.append(f'<rect x="{x}" y="88" width="{bw-14}" height="30" rx="2" '
                 f'fill="{PAPER}" stroke="{ACCENT}" stroke-width="1"/>')
        o.append(_t(x + (bw - 14) / 2, 107, s, 9.4, INK, anchor="middle"))
        if i < len(on) - 1:
            o.append(_arrow(x + bw - 14, 103, x + bw - 3, 103, ACCENT, sw=.9))
        x += bw
    o.append(f'<path d="M 52 58 L 52 74 L 590 74 L 590 88" fill="none" '
             f'stroke="{MUTE2}" stroke-width="1" stroke-dasharray="4 3" '
             f'marker-end="url(#ah)"/>')
    o.append(_t(330, 152, "检索到的内容会被塞进上下文窗口——所以 RAG 的成败，"
                          "一半取决于切分与召回质量。", 9, MUTE, anchor="middle"))
    o.append(_t(0, 190, "RAG 解决的是「模型不知道你的私有资料」。它不解决"
                        "「模型不按资料说话」——那是幻觉与引用溯源的问题。", 9, MUTE))
    return _svg(h, "".join(o))


# ── 图 9　LangChain 与 LangGraph 的分层 ────────────────────
def fig_stack():
    h = 214
    o = [_defs()]
    layers = [
        ("LangChain v1（高层 Agent 框架）",
         "create_agent、模型、工具、结构化输出、middleware", BRAND, 8),
        ("LangGraph（低层编排框架与运行时）",
         "State、Node、Edge、分支、并行、子图、interrupt、checkpointer", INK, 70),
        ("模型与存储（可替换）",
         "各家模型 SDK、向量库、数据库、任务队列", MUTE2, 132),
    ]
    for name, desc, col, y in layers:
        o.append(f'<rect x="0" y="{y}" width="{W}" height="52" fill="{PAPER}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
        o.append(f'<rect x="0" y="{y}" width="3" height="52" fill="{col}"/>')
        o.append(_t(16, y + 22, name, 11.5, col, weight="700"))
        o.append(_t(16, y + 39, desc, 8.8, MUTE))
    o.append(_arrow(W / 2, 70, W / 2, 62, MUTE, sw=.9))
    o.append(_arrow(W / 2, 132, W / 2, 124, MUTE, sw=.9))
    o.append(_t(0, 200, "create_agent 返回的就是一张编译好的 LangGraph。"
                        "所以「用了 LangChain 就没有持久化」是错的。", 9, MUTE))
    return _svg(h, "".join(o))


# ── 图 10　四段式回答框架 ──────────────────────────────────
def fig_answer():
    h = 210
    o = [_defs()]
    segs = [
        ("① 先给边界", "「Agent 和 Workflow 不是一回事」——\n用一句话把定义钉住", BRAND),
        ("② 再给结构", "循环 / 工具 / 记忆 / 目标\n四件套，或你项目里的实际分层", INK),
        ("③ 给一个真实约束", "权限、幂等、成本、延迟——\n挑一个你踩过的", MUTE2),
        ("④ 给判断的边界", "「这个方案在什么情况下不成立」\n——主动降级，反而加分", ACCENT),
    ]
    x = 0
    cw = W / 4
    for i, (title, body, col) in enumerate(segs):
        o.append(f'<rect x="{x}" y="6" width="{cw-10}" height="{h-52}" fill="{PAPER}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
        o.append(f'<rect x="{x}" y="6" width="{cw-10}" height="3" fill="{col}"/>')
        o.append(_t(x + 12, 34, title, 10.5, col, weight="700"))
        for j, line in enumerate(body.split("\n")):
            o.append(_t(x + 12, 54 + j * 15, line, 8.8, MUTE))
        if i < 3:
            o.append(_arrow(x + cw - 10, h / 2 - 20, x + cw - 2, h / 2 - 20, RULE, sw=.9))
        x += cw
    o.append(f'<line x1="0" y1="{h-38}" x2="{W}" y2="{h-38}" stroke="{RULE}" '
             f'stroke-width="1"/>')
    o.append(_t(0, h - 18, "四段缺一段都不致命，缺两段就会被追问到底。"
                           "记住顺序：先钉定义，再讲结构，然后才是你的项目。", 9, MUTE))
    return _svg(h, "".join(o))


# ── 图 11　Lost in the Middle（示意） ──────────────────────
def fig_middle():
    h = 214
    o = [_defs()]
    ox, oy, pw, ph = 56, 24, 560, 130
    o.append(f'<line x1="{ox}" y1="{oy+ph}" x2="{ox+pw}" y2="{oy+ph}" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    o.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy+ph}" stroke="{INK}" '
             f'stroke-width="1.2"/>')
    o.append(_t(ox - 10, oy + 8, "高", 8.6, MUTE, anchor="end"))
    o.append(_t(ox - 10, oy + ph, "低", 8.6, MUTE, anchor="end"))
    o.append(_t(ox - 10, oy + ph / 2, "准确率", 8.6, MUTE, anchor="middle"))
    pts = [(0, 0.10), (0.1, 0.06), (0.25, 0.36), (0.4, 0.62), (0.5, 0.70),
           (0.62, 0.58), (0.78, 0.34), (0.9, 0.10), (1.0, 0.04)]
    d = " ".join(
        f'{"M" if i == 0 else "L"} {ox + x*pw:.1f} {oy + y*ph:.1f}'
        for i, (x, y) in enumerate(pts))
    o.append(f'<path d="{d}" fill="none" stroke="{BRAND}" stroke-width="1.8"/>')
    o.append(_t(ox + 2, oy + ph + 16, "开头", 8.6, MUTE))
    o.append(_t(ox + pw / 2, oy + ph + 16, "中间", 8.6, MUTE, anchor="middle"))
    o.append(_t(ox + pw, oy + ph + 16, "结尾", 8.6, MUTE, anchor="end"))
    o.append(_t(ox + pw * 0.34, oy + ph * 0.62, "开头和结尾记得住", 8.6, BRAND))
    o.append(_t(ox + pw * 0.62, oy + ph * 0.30, "中间最容易被忽略", 8.6, ACCENT))
    o.append(_t(0, h - 24, "纵轴是「关键信息出现在该位置时，模型答对的概率」，"
                           "横轴是信息在长输入里的位置。曲线为示意形状，"
                           "具体幅度随模型与任务变化。", 8.6, MUTE))
    o.append(_t(0, h - 8, "结论：上下文窗口大，不等于有效上下文长。"
                          "把关键信息放在开头或结尾，比塞进中间更稳。", 9, INK))
    return _svg(h, "".join(o))


# ── 图 12　评估的四个层次 ──────────────────────────────────
def fig_eval():
    h = 216
    o = [_defs()]
    rows = [
        ("端到端", "用户问题 → 最终答案", "通过率、满意度、人工抽检", BRAND, 8),
        ("轨迹", "走了哪几步、调了哪些工具", "工具选择正确率、步数、无效调用", INK, 58),
        ("单步", "这一次工具调用对不对", "参数准确率、格式合法率", MUTE2, 108),
        ("成本与延迟", "为了这个结果花了多少", "P95 延迟、Token、搜索费用", ACCENT, 158),
    ]
    for name, what, metric, col, y in rows:
        o.append(f'<rect x="0" y="{y}" width="{W}" height="44" fill="{PAPER}" '
                 f'stroke="{RULE}" stroke-width="1"/>')
        o.append(f'<rect x="0" y="{y}" width="3" height="44" fill="{col}"/>')
        o.append(_t(16, y + 19, name, 10.6, col, weight="700"))
        o.append(_t(16, y + 35, what, 8.6, MUTE))
        o.append(_t(W - 8, y + 19, metric, 8.8, INK, anchor="end"))
        o.append(_t(W - 8, y + 35, "只看这一层会误判", 8.2, MUTE2, anchor="end"))
    o.append(_t(0, h - 4, "只测最后一层，你只知道「坏了」；"
                          "把四层都测，你才知道「坏在哪」。", 9, INK))
    return _svg(h, "".join(o))
