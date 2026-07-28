#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic card renderer for 转行日记 (AI Transition Diary).

Copy this file into the day's folder (dayN/), set DAY / DATE below (or pass them
as env vars), edit ONLY the `D` content dict, then run:

    OUTDIR=<dayN> python render_cards_template.py

Everything under the "ENGINE" banner is fixed on purpose: palette, the fade vs
highlight rule, the @测试阿甲 signature, vertical centering, title wrapping, and
the bounds audit. You should almost never need to touch it — describe the day in
`D` and let the engine lay it out, so every day in the series looks the same and
the only thing that changes is the content.

Fade / highlight is driven by each node's `kind`, which must match the draft's
今昨代码差异 classification:
    "now"   -> today's highlight, accent color + 今天重点/今天新增 tag
    "fade"  -> reused, muted gray + 沿用 tag
    "plain" -> neutral (cycles blue / teal / green)
A node may also set "shape": "decision" to render as a diamond (判断点); the same
fade/highlight rules apply to diamonds, it is just a different shape.

The bounds audit measures every card, text block, arrow, badge, signature and
footer against the outer safe frame and raises AssertionError (越界/触底) if
anything overflows. A clean run means bounds passed. On an assertion, shorten the
offending copy or drop a row in `D` and rerun — do not widen the frame.
"""

import os
import sys

# ============================================================================
# CONTENT — edit this block only.
# ============================================================================
DAY = os.environ.get("DAY", "14")
DATE = os.environ.get("DATE", "2026-06-24")

D = {
    "cover": {
        "title": "RAG 总搜不到答案?可能是问题问得太短",
        "subtitle": "一个问题拆成好几个问法再搜，命中率立刻不一样",
        # small horizontal idea-flow band along the lower area
        "flow": ["原问题", "改写成多个问法", "分别检索", "合并去重", "回答"],
    },
    "pipeline": {
        "title": "今天补在整条流程的哪一步",
        # the whole RAG pipeline; reused stages fade, today's new layer highlights
        "stages": [
            {"label": "加载文档", "kind": "fade"},
            {"label": "切分", "kind": "fade"},
            {"label": "向量化", "kind": "fade"},
            {"label": "多查询改写", "kind": "now", "tag": "今天新增"},
            {"label": "检索", "kind": "fade"},
            {"label": "回答", "kind": "fade"},
        ],
    },
    "compare": {
        "title": "同一个问题，改写前后差在哪",
        "before": {"label": "只用原问题", "detail": "问得太短，关键词对不上，漏掉相关段落"},
        "after": {"label": "拆成多个问法", "detail": "换几种说法分别搜，命中此前漏掉的段落"},
    },
    "methods": [
        {
            "type": "linear",
            "title": "多查询改写：一个问题，多种问法",
            "steps": [
                {"label": "拿到原问题", "kind": "fade"},
                {"label": "让模型改写出几个等价问法", "kind": "now", "tag": "今天重点"},
                {"label": "每个问法各搜一遍再合并", "kind": "now", "tag": "今天新增"},
            ],
        },
        {
            "type": "branch",
            "title": "检索质量不够就再改写一轮",
            "graph": {
                "nodes": [
                    {"id": "q", "label": "改写问法", "kind": "fade"},
                    {"id": "r", "label": "检索", "kind": "fade"},
                    {"id": "j", "label": "质量够了吗", "kind": "now",
                     "shape": "decision", "tag": "今天新增"},
                    {"id": "a", "label": "生成回答", "kind": "fade"},
                ],
                # (from, to, label, loopback)
                "edges": [
                    ("q", "r", "", False),
                    ("r", "j", "", False),
                    ("j", "a", "达标", False),
                    ("j", "q", "不够，再改写", True),
                ],
            },
            # real example values from today's run, stacked vertically (2-3 steps)
            "trace": [
                {"step": "第1轮", "value": "quality=1 → 未达标"},
                {"step": "第2轮", "value": "quality=2 → 未达标"},
                {"step": "第3轮", "value": "quality=4 → 达标，结束"},
            ],
        },
    ],
    "glossary": {
        "title": "关键知识点",
        "terms": [
            {"term": "MultiQueryRetriever", "def": "把一个问题自动改写成多个问法再分别检索的检索器"},
            {"term": "Multi-Query", "def": "多查询改写的思路：换几种说法搜，减少漏检"},
            {"term": "HyDE", "def": "先让模型假想一个答案，再拿这个假答案去检索"},
            {"term": "EnsembleRetriever", "def": "把多个检索器的结果按权重融合成一个排序"},
        ],
    },
    # ---- 代码对照解读卡（默认已启用，每天最多一张；不需要就删掉整个 code_explain）----
    # 唯一允许在图里放真实代码的卡：精简代码 + 对应关系彩点映射 + 流程图 + 结论横幅。
    # 渲染在方法卡之后、关键知识点卡之前。两段代码并排对比用 layout="wide"；
    # 单段逐行拆解用 layout="single"（竖版 3:4）。节点 label 保持一行短词，别放 \\n。
    "code_explain": [
        {
            "layout": "wide",              # "wide"=两段代码并排(4:3方)；"single"=竖版单框
            "title": "为什么这两个写法本质上一样?",
            "subtitle": "手搭 ReAct Agent vs create_react_agent 一行版",
            "equals": True,                # 两个 code_blocks 间画大等号
            "code_blocks": [
                {"label": "手搭版（自己搭图）", "kind": "plain",
                 "lines": [
                     'llm_with_tools = llm.bind_tools(TOOLS)',
                     'g.add_node("agent", agent)',
                     'g.add_node("tools", ToolNode(TOOLS))',
                     'g.add_conditional_edges("agent", tools_condition)',
                     'g.add_edge("tools", "agent")',
                 ],
                 "caption": "显式把每个节点和边都写出来"},
                {"label": "一行版（官方封装）", "kind": "plain",
                 "lines": [
                     'create_react_agent(',
                     '    get_llm(temperature=0),',
                     '    tools=TOOLS,',
                     '    prompt="你是一个会用工具的助手...",',
                     ')',
                 ],
                 "caption": "把同样的骨架提前封装好了"},
            ],
            "flow": {
                "note": "模型接收 messages，可能直接回答，也可能要求调工具",
                "nodes": [
                    {"id": "start", "label": "START", "kind": "plain"},
                    {"id": "agent", "label": "agent 节点", "kind": "now"},
                    {"id": "cond", "label": "有 tool_calls?", "kind": "plain",
                     "shape": "decision"},
                    {"id": "end", "label": "END", "kind": "plain"},
                    {"id": "tools", "label": "tools 执行", "kind": "plain",
                     "row": 1, "under": "cond"},
                ],
                "edges": [                 # (from, to, label, loopback)
                    ("start", "agent", "", False),
                    ("agent", "cond", "", False),
                    ("cond", "end", "否", False),
                    ("cond", "tools", "是", False),
                    ("tools", "agent", "结果带回，再想一轮", True),
                ],
            },
            "mapping": {
                "title": "对应关系",
                "rows": [
                    {"code": "bind_tools(TOOLS)", "meaning": "让模型知道可用工具", "ci": 0},
                    {"code": "ToolNode(TOOLS)", "meaning": "执行工具", "ci": 1},
                    {"code": "tools_condition", "meaning": "判断是否继续调用工具", "ci": 2},
                    {"code": "tools → agent", "meaning": "把结果回传给模型", "ci": 0},
                    {"code": "prompt=...", "meaning": "给 Agent 设定行为规则", "ci": 1},
                ],
            },
            "conclusion": "create_react_agent 不是另一种 Agent，而是把手搭版那张图帮你提前搭好了。",
        },
    ],
}

# ============================================================================
# ENGINE — fixed layout, palette, fading, signature, bounds audit.
# Editing below this line changes the look of every day in the series.
# ============================================================================
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1080, 1440          # vertical 3:4
MARGIN = 64
SAFE = (MARGIN, MARGIN, W - MARGIN, H - MARGIN)
HANDLE = "@测试阿甲"

# palette
BG = (250, 249, 246)
GRID = (233, 231, 225)
INK = (46, 46, 46)
SUBINK = (110, 110, 110)
ACCENT = (232, 116, 59)          # today's highlight (warm, pops on blue/teal/green)
ACCENT_FILL = (252, 238, 229)
FADE_LINE = (188, 188, 188)
FADE_FILL = (240, 240, 240)
FADE_INK = (150, 150, 150)
BOX_COLORS = [(59, 125, 216), (47, 166, 166), (70, 160, 90)]  # blue / teal / green
BOX_FILLS = [(233, 241, 251), (230, 245, 245), (233, 245, 237)]
RED = (214, 69, 69)
RED_FILL = (250, 233, 233)
GREEN = (70, 160, 90)
GREEN_FILL = (233, 245, 237)

# ---- fonts ----------------------------------------------------------------
def _find_font(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

_SANS = _find_font([
    # Linux (sandbox)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    # Windows
    "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyh.ttf",
    "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyhbd.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
])
_SANS_BOLD = _find_font([
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]) or _SANS

if _SANS is None:
    sys.stderr.write("No CJK-capable font found. Install Noto Sans CJK or "
                     "Microsoft YaHei.\n")
    sys.exit(2)

_font_cache = {}
def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        path = _SANS_BOLD if bold else _SANS
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[key] = ImageFont.truetype(_SANS, size)
    return _font_cache[key]

# ---- bounds audit ---------------------------------------------------------
class Bounds:
    """Collects every drawn rect and asserts it stays inside the safe frame."""
    def __init__(self):
        self.items = []
    def check(self, name, x0, y0, x1, y1):
        self.items.append((name, x0, y0, x1, y1))
        sx0, sy0, sx1, sy1 = SAFE
        msgs = []
        if x0 < sx0 - 1 or x1 > sx1 + 1:
            msgs.append(f"越界(横向) x=[{x0:.0f},{x1:.0f}] 超出 [{sx0},{sx1}]")
        if y0 < sy0 - 1:
            msgs.append(f"越界(顶部) y0={y0:.0f} < {sy0}")
        if y1 > sy1 + 1:
            msgs.append(f"触底 y1={y1:.0f} > {sy1}")
        assert not msgs, f"[{name}] " + "; ".join(msgs)

# ---- text helpers ---------------------------------------------------------
def _tokens(text):
    """Split into tokens: each CJK char its own token, latin runs kept whole."""
    out, buf = [], ""
    for ch in text:
        if ch == " ":
            if buf:
                out.append(buf); buf = ""
            out.append(" ")
        elif ord(ch) > 0x2E80:  # CJK & friends
            if buf:
                out.append(buf); buf = ""
            out.append(ch)
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out

def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for tok in _tokens(text):
        trial = cur + tok
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = "" if tok == " " else tok
    if cur.strip() or not lines:
        lines.append(cur.rstrip())
    return lines

def text_block(draw, cx, cy, text, fnt, fill, max_w, align="center",
               leading=1.28):
    """Draw wrapped text centered vertically on cy. Returns (top, bottom)."""
    lines = wrap(draw, text, fnt, max_w)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * leading)
    total = lh * len(lines)
    top = cy - total / 2
    y = top
    for ln in lines:
        w = draw.textlength(ln, font=fnt)
        if align == "center":
            x = cx - w / 2
        elif align == "left":
            x = cx
        else:
            x = cx - w
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return top, top + total

# ---- background & chrome --------------------------------------------------
def new_card():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 44):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 44):
        d.line([(0, y), (W, y)], fill=GRID, width=1)
    return img, d

def signature(d, b):
    f = font(24)
    w = d.textlength(HANDLE, font=f)
    x, y = W - MARGIN - w, H - MARGIN - 30
    d.text((x, y), HANDLE, font=f, fill=(200, 200, 200))
    b.check("signature", x, y, x + w, y + 30)

def rounded(d, box, radius, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline,
                        width=width)

def title_bar(d, b, title, y=MARGIN + 6):
    f = font(46, bold=True)
    lines = wrap(d, title, f, W - 2 * MARGIN)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.2)
    top = y
    yy = top
    for ln in lines:
        d.text((MARGIN, yy), ln, font=f, fill=INK)
        yy += lh
    d.line([(MARGIN, yy + 6), (MARGIN + 90, yy + 6)], fill=ACCENT, width=6)
    bottom = yy + 16
    b.check("title", MARGIN, top, W - MARGIN, bottom)
    return bottom

# ---- node styling by kind -------------------------------------------------
def style_for(kind, plain_idx=0):
    if kind == "now":
        return ACCENT, ACCENT_FILL, INK, ACCENT
    if kind == "fade":
        return FADE_LINE, FADE_FILL, FADE_INK, FADE_LINE
    c = BOX_COLORS[plain_idx % len(BOX_COLORS)]
    fll = BOX_FILLS[plain_idx % len(BOX_FILLS)]
    return c, fll, INK, c

def tag_for(node):
    if "tag" in node:
        return node["tag"]
    if node.get("kind") == "fade":
        return "沿用"
    return None

def draw_tag(d, b, x, y, text, color):
    f = font(22, bold=True)
    tw = d.textlength(text, font=f) + 20
    rounded(d, (x, y, x + tw, y + 34), 8, fill=color)
    d.text((x + 10, y + 5), text, font=f, fill=(255, 255, 255))
    b.check("tag", x, y, x + tw, y + 34)
    return tw

def draw_box(d, b, cx, top, w, h, node, plain_idx=0, name="box"):
    line, fill, ink, _ = style_for(node.get("kind", "plain"), plain_idx)
    x0, x1 = cx - w / 2, cx + w / 2
    rounded(d, (x0, top, x1, top + h), 16, fill=fill, outline=line, width=3)
    b.check(name, x0, top, x1, top + h)
    tag = tag_for(node)
    text_top = top + (18 if tag else 0)
    text_block(d, cx, (text_top + top + h) / 2, node["label"], font(30, bold=True),
               ink, w - 40)
    if tag:
        draw_tag(d, b, x0 + 14, top + 12, tag, style_for(node["kind"])[3])
    return top + h

def draw_diamond(d, b, cx, top, w, h, node, name="decision"):
    line, fill, ink, _ = style_for(node.get("kind", "plain"))
    cy = top + h / 2
    pts = [(cx, top), (cx + w / 2, cy), (cx, top + h), (cx - w / 2, cy)]
    d.polygon(pts, fill=fill, outline=line)
    # thicker outline
    d.line(pts + [pts[0]], fill=line, width=3)
    b.check(name, cx - w / 2, top, cx + w / 2, top + h)
    text_block(d, cx, cy, node["label"], font(27, bold=True), ink, w - 80)
    tag = tag_for(node)
    if tag:
        draw_tag(d, b, cx - w / 2 + 4, top - 6, tag, style_for(node["kind"])[3])
    return top + h

def arrow(d, x0, y0, x1, y1, color=INK, width=3):
    d.line([(x0, y0), (x1, y1)], fill=color, width=width)
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    L = 14
    for da in (math.radians(150), math.radians(-150)):
        d.line([(x1, y1),
                (x1 + L * math.cos(ang + da), y1 + L * math.sin(ang + da))],
               fill=color, width=width)

# ============================================================================
# CARD RENDERERS
# ============================================================================
def render_cover(spec):
    img, d = new_card()
    b = Bounds()
    # top: series chip + handle
    chip = f"转行日记 · Day{DAY}"
    cf = font(28, bold=True)
    cw = d.textlength(chip, font=cf) + 28
    rounded(d, (MARGIN, MARGIN, MARGIN + cw, MARGIN + 46), 12, fill=INK)
    d.text((MARGIN + 14, MARGIN + 8), chip, font=cf, fill=(255, 255, 255))
    b.check("chip", MARGIN, MARGIN, MARGIN + cw, MARGIN + 46)
    hx = MARGIN + cw + 20
    d.text((hx, MARGIN + 10), HANDLE, font=font(26), fill=SUBINK)
    b.check("handle", hx, MARGIN + 10, hx + d.textlength(HANDLE, font=font(26)),
            MARGIN + 40)

    # title block (upper-middle)
    _, tb = text_block(d, W / 2, 470, spec["title"], font(60, bold=True), INK,
                       W - 2 * MARGIN - 20)
    b.check("cover-title", MARGIN, 470 - 240, W - MARGIN, tb)
    # subtitle
    _, sb = text_block(d, W / 2, tb + 90, spec["subtitle"], font(34), SUBINK,
                       W - 2 * MARGIN - 60)
    b.check("cover-sub", MARGIN, tb + 40, W - MARGIN, sb)

    # lower idea-flow band
    flow = spec["flow"]
    band_y = 1120
    n = len(flow)
    gap = 26
    avail = W - 2 * MARGIN
    bw = (avail - gap * (n - 1)) / n
    x = MARGIN
    for i, label in enumerate(flow):
        col = ACCENT if i == n - 1 else BOX_COLORS[i % 3]
        fll = ACCENT_FILL if i == n - 1 else BOX_FILLS[i % 3]
        rounded(d, (x, band_y, x + bw, band_y + 92), 12, fill=fll, outline=col,
                width=3)
        text_block(d, x + bw / 2, band_y + 46, label, font(24, bold=True), INK,
                   bw - 16)
        b.check(f"flow{i}", x, band_y, x + bw, band_y + 92)
        if i < n - 1:
            arrow(d, x + bw + 4, band_y + 46, x + bw + gap - 4, band_y + 46,
                  color=SUBINK, width=3)
        x += bw + gap
    signature(d, b)
    return img

def render_pipeline(spec):
    img, d = new_card()
    b = Bounds()
    y = title_bar(d, b, spec["title"])
    stages = spec["stages"]
    n = len(stages)
    top = y + 60
    box_h = 96
    gap = 44
    avail_h = SAFE[3] - top - 60
    step = (avail_h) / n
    box_h = min(box_h, step - gap)
    plain_i = 0
    cx = W / 2
    for i, st in enumerate(stages):
        bt = top + i * step
        if st.get("kind") not in ("now", "fade"):
            draw_box(d, b, cx, bt, 560, box_h, st, plain_i, f"stage{i}")
            plain_i += 1
        else:
            draw_box(d, b, cx, bt, 560, box_h, st, 0, f"stage{i}")
        if i < n - 1:
            arrow(d, cx, bt + box_h + 4, cx, bt + step - 4, color=SUBINK)
    signature(d, b)
    return img

def render_compare(spec):
    img, d = new_card()
    b = Bounds()
    y = title_bar(d, b, spec["title"])
    top = y + 70
    card_h = 380
    gap = 70
    # before (red) then after (green) — the only card allowed red/green
    for idx, (key, line, fill, badge) in enumerate([
        ("before", RED, RED_FILL, "改写前"),
        ("after", GREEN, GREEN_FILL, "改写后")]):
        bt = top + idx * (card_h + gap)
        x0, x1 = MARGIN, W - MARGIN
        rounded(d, (x0, bt, x1, bt + card_h), 20, fill=fill, outline=line, width=3)
        b.check(f"cmp-{key}", x0, bt, x1, bt + card_h)
        draw_tag(d, b, x0 + 20, bt + 20, badge, line)
        s = spec[key]
        text_block(d, W / 2, bt + 150, s["label"], font(40, bold=True), INK,
                   x1 - x0 - 80)
        text_block(d, W / 2, bt + 270, s["detail"], font(30), INK,
                   x1 - x0 - 100)
    signature(d, b)
    return img

def render_linear(spec):
    img, d = new_card()
    b = Bounds()
    y = title_bar(d, b, spec["title"])
    steps = spec["steps"]
    n = len(steps)
    top = y + 70
    avail_h = SAFE[3] - top - 60
    step = avail_h / n
    box_h = min(150, step - 50)
    plain_i = 0
    cx = W / 2
    for i, st in enumerate(steps):
        bt = top + i * step
        pi = plain_i
        if st.get("kind") not in ("now", "fade"):
            plain_i += 1
        # numbered step
        draw_box(d, b, cx, bt, 640, box_h, st, pi, f"step{i}")
        nf = font(30, bold=True)
        d.ellipse((cx - 640 / 2 - 2, bt + box_h / 2 - 22,
                   cx - 640 / 2 + 42, bt + box_h / 2 + 22), fill=INK)
        d.text((cx - 640 / 2 + 12, bt + box_h / 2 - 18), str(i + 1), font=nf,
               fill=(255, 255, 255))
        if i < n - 1:
            arrow(d, cx, bt + box_h + 4, cx, bt + step - 4, color=SUBINK)
    signature(d, b)
    return img

def render_branch(spec):
    img, d = new_card()
    b = Bounds()
    y = title_bar(d, b, spec["title"])
    g = spec["graph"]
    nodes = {nd["id"]: nd for nd in g["nodes"]}
    order = [nd["id"] for nd in g["nodes"]]
    # ---- top half: graph structure ----
    graph_top = y + 50
    graph_bottom = 900
    node_h = 92
    n = len(order)
    slot = (graph_bottom - graph_top) / n
    cx = W / 2 - 40  # leave room on right for loop-back arrow
    pos = {}
    for i, nid in enumerate(order):
        nd = nodes[nid]
        bt = graph_top + i * slot + (slot - node_h) / 2
        if nd.get("shape") == "decision":
            draw_diamond(d, b, cx, bt, 300, node_h + 24, nd, f"node-{nid}")
            pos[nid] = (cx, bt, bt + node_h + 24)
        else:
            draw_box(d, b, cx, bt, 380, node_h, nd, 0, f"node-{nid}")
            pos[nid] = (cx, bt, bt + node_h)
    # edges
    ef = font(22)
    for frm, to, label, loopback in g["edges"]:
        fx, fy0, fy1 = pos[frm]
        tx, ty0, ty1 = pos[to]
        if loopback:
            # route on the right side back up to an earlier node
            rx = cx + 250
            ymid_from = (fy0 + fy1) / 2
            ymid_to = (ty0 + ty1) / 2
            d.line([(fx + 190, ymid_from), (rx, ymid_from)], fill=ACCENT, width=3)
            d.line([(rx, ymid_from), (rx, ymid_to)], fill=ACCENT, width=3)
            arrow(d, rx, ymid_to, cx + 190, ymid_to, color=ACCENT)
            if label:
                lw = d.textlength(label, font=ef)
                d.text((rx - lw - 8, (ymid_from + ymid_to) / 2 - 14), label,
                       font=ef, fill=ACCENT)
                b.check("edge-loop-label", rx - lw - 8, ymid_to, rx, ymid_from)
        else:
            arrow(d, fx, fy1 + 4, tx, ty0 - 4, color=SUBINK)
            if label:
                lw = d.textlength(label, font=ef)
                d.text((fx + 20, (fy1 + ty0) / 2 - 14), label, font=ef,
                       fill=SUBINK)
    # ---- bottom half: trace strip (轨迹条) ----
    trace = spec.get("trace", [])
    if trace:
        d.text((MARGIN, graph_bottom + 20), "运行轨迹", font=font(28, bold=True),
               fill=INK)
        tb_top = graph_bottom + 70
        tn = len(trace)
        avail = SAFE[3] - tb_top - 40
        th = min(120, (avail - (tn - 1) * 18) / tn)
        for i, tr in enumerate(trace):
            bt = tb_top + i * (th + 18)
            x0, x1 = MARGIN, W - MARGIN
            rounded(d, (x0, bt, x1, bt + th), 12, fill=BOX_FILLS[0],
                    outline=BOX_COLORS[0], width=2)
            b.check(f"trace{i}", x0, bt, x1, bt + th)
            d.text((x0 + 24, bt + th / 2 - 18), tr["step"],
                   font=font(28, bold=True), fill=BOX_COLORS[0])
            text_block(d, x0 + 260, bt + th / 2, tr["value"], font(28), INK,
                       x1 - x0 - 300, align="left")
    signature(d, b)
    return img

def render_glossary(spec):
    img, d = new_card()
    b = Bounds()
    y = title_bar(d, b, spec["title"])
    terms = spec["terms"]
    top = y + 60
    n = len(terms)
    avail = SAFE[3] - top - 40
    ch = min(210, (avail - (n - 1) * 22) / n)
    for i, t in enumerate(terms):
        bt = top + i * (ch + 22)
        x0, x1 = MARGIN, W - MARGIN
        col = BOX_COLORS[i % 3]
        rounded(d, (x0, bt, x1, bt + ch), 14, fill=(255, 255, 255),
                outline=col, width=2)
        # left accent bar instead of nested white box
        d.rectangle((x0, bt, x0 + 10, bt + ch), fill=col)
        b.check(f"term{i}", x0, bt, x1, bt + ch)
        d.text((x0 + 34, bt + 22), t["term"], font=font(34, bold=True), fill=col)
        text_block(d, x0 + 34, bt + ch - 44, t["def"], font(27), INK,
                   x1 - x0 - 70, align="left")
    signature(d, b)
    return img

# ============================================================================
# CODE-EXPLAIN CARD (代码对照解读卡) — additive card type.
# Shows REAL short code + 对应关系 dot-mapping + flow + 结论 banner.
# This is the ONLY card allowed to contain source code; every other card stays
# code-free. Vertical 3:4 by default; set "layout": "wide" for a 4:3 canvas when
# comparing two code blocks side by side (Day30-style 手搭版 = 一行版).
# ============================================================================
import re as _re
import math as _math

_MONO = _find_font([
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf",
    "/System/Library/Fonts/Menlo.ttc",
]) or _SANS
_MONO_BOLD = _find_font([
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "C:/Windows/Fonts/consolab.ttf",
]) or _MONO

def mono(size, bold=False):
    key = ("mono", size, bold)
    if key not in _font_cache:
        path = _MONO_BOLD if bold else _MONO
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[key] = ImageFont.truetype(_MONO, size)
    return _font_cache[key]

# code syntax colors (muted, print-friendly)
CODE_KW = (150, 92, 196)
CODE_STR = (70, 150, 90)
CODE_CALL = (47, 140, 150)
CODE_COMMENT = (165, 165, 165)
CODE_INK = (60, 60, 66)
YELLOW_FILL = (255, 247, 214)
YELLOW_LINE = (228, 188, 60)
YELLOW_INK = (120, 90, 20)
_PY_KW = {"import", "from", "def", "return", "class", "if", "else", "elif",
          "for", "while", "in", "and", "or", "not", "None", "True", "False",
          "with", "as", "lambda", "yield", "is", "pass", "break", "continue",
          "try", "except", "raise", "global"}

def _code_tokens(line):
    pat = _re.compile(r'(#.*)|("[^"]*"|\'[^\']*\')|([A-Za-z_]\w*)|(\s+)|([^\sA-Za-z_]+)')
    toks = []
    for m in pat.finditer(line):
        comment, string, ident, ws, other = m.groups()
        if comment is not None:
            toks.append((comment, CODE_COMMENT))
        elif string is not None:
            toks.append((string, CODE_STR))
        elif ident is not None:
            after = line[m.end():m.end() + 1]
            if ident in _PY_KW:
                toks.append((ident, CODE_KW))
            elif after == "(":
                toks.append((ident, CODE_CALL))
            else:
                toks.append((ident, CODE_INK))
        elif ws is not None:
            toks.append((ws, CODE_INK))
        else:
            toks.append((other, CODE_INK))
    return toks

def _measure_code(d, line, size):
    """Width of a code line, ASCII in mono + CJK in the sans fallback font."""
    mf, sf = mono(size), font(size)
    total = 0
    for ch in line:
        total += d.textlength(ch, font=(sf if ord(ch) > 0x2E80 else mf))
    return total

def _fit_mono(d, lines, max_w, start=27, lo=15):
    size = start
    while size > lo:
        if all(_measure_code(d, ln, size) <= max_w for ln in lines):
            return size
        size -= 1
    return lo

def draw_code_line(d, x, y, line, size):
    """Draw a code line; CJK chars use the sans font so they are not tofu."""
    mf, sf = mono(size), font(size)
    for tok, col in _code_tokens(line):
        for ch in tok:
            fnt = sf if ord(ch) > 0x2E80 else mf
            d.text((x, y), ch, font=fnt, fill=col)
            x += d.textlength(ch, font=fnt)

def _code_accent(block, ci):
    kind = block.get("kind", "plain")
    if kind == "now":
        return ACCENT, ACCENT_FILL
    if kind == "fade":
        return FADE_LINE, FADE_FILL
    return BOX_COLORS[ci % 3], BOX_FILLS[ci % 3]

def draw_code_box(d, b, x0, y0, w, block, name, ci=0, msize=None):
    accent, _ = _code_accent(block, ci)
    hf = font(28, bold=True)
    d.text((x0, y0), block["label"], font=hf, fill=accent)
    lbl_w = d.textlength(block["label"], font=hf)
    if block.get("tag"):
        draw_tag(d, b, x0 + lbl_w + 16, y0 - 2, block["tag"], accent)
    header_h = sum(hf.getmetrics()) + 10
    frame_top = y0 + header_h
    pad = 20
    lines = block["lines"]
    if msize is None:
        msize = _fit_mono(d, lines, w - 2 * pad)
    mf = mono(msize)
    lh = int(sum(mf.getmetrics()) * 1.32)
    frame_h = pad * 2 + lh * len(lines)
    rounded(d, (x0, frame_top, x0 + w, frame_top + frame_h), 12,
            fill=(252, 251, 248), outline=accent, width=2)
    b.check(name + "-frame", x0, frame_top, x0 + w, frame_top + frame_h)
    ty = frame_top + pad
    for ln in lines:
        draw_code_line(d, x0 + pad, ty, ln, msize)
        ty += lh
    bottom = frame_top + frame_h
    if block.get("caption"):
        cf = font(24, bold=True)
        clines = wrap(d, block["caption"], cf, w)
        clh = int(sum(cf.getmetrics()) * 1.2)
        cy = bottom + 12
        for cl in clines:
            cw = d.textlength(cl, font=cf)
            d.text((x0 + w / 2 - cw / 2, cy), cl, font=cf, fill=accent)
            cy += clh
        bottom = cy
    b.check(name, x0, y0, x0 + w, bottom)
    return bottom

def draw_mapping(d, b, x0, y0, w, mapping, name):
    tf = font(32, bold=True)
    d.text((x0, y0), mapping.get("title", "对应关系"), font=tf, fill=INK)
    d.line([(x0, y0 + sum(tf.getmetrics()) + 4),
            (x0 + 70, y0 + sum(tf.getmetrics()) + 4)], fill=ACCENT, width=5)
    ty = y0 + sum(tf.getmetrics()) + 20
    rows = mapping["rows"]
    rowh = 46
    mfc = mono(24, bold=True)
    af = font(26)
    mf_mean = font(26)
    for i, row in enumerate(rows):
        cy = ty + i * rowh + rowh / 2
        col = BOX_COLORS[row.get("ci", i) % 3]
        d.ellipse((x0 + 2, cy - 8, x0 + 18, cy + 8), fill=col)
        cx = x0 + 34
        d.text((cx, cy - 15), row["code"], font=mfc, fill=col)
        cw = d.textlength(row["code"], font=mfc)
        ax = cx + cw + 16
        d.text((ax, cy - 16), "→", font=af, fill=SUBINK)
        d.text((ax + 34, cy - 15), row["meaning"], font=mf_mean, fill=INK)
    bottom = ty + len(rows) * rowh
    b.check(name, x0, y0, x0 + w, bottom)
    return bottom

def draw_conclusion(d, b, y0, text):
    x0, x1 = MARGIN, W - MARGIN
    label = "结论"
    lf = font(30, bold=True)
    lw = d.textlength(label, font=lf) + 24
    f = font(31, bold=True)
    body_w = x1 - x0 - 40 - lw - 16
    lines = wrap(d, text, f, body_w)
    lh = int(sum(f.getmetrics()) * 1.3)
    h = max(lh * len(lines) + 36, 78)
    cy = y0 + h / 2
    rounded(d, (x0, y0, x1, y0 + h), 16, fill=YELLOW_FILL, outline=YELLOW_LINE,
            width=3)
    # label pill + text both vertically centered on the box mid-line (anchor lm)
    rounded(d, (x0 + 20, cy - 22, x0 + 20 + lw, cy + 22), 10, fill=YELLOW_LINE)
    d.text((x0 + 32, cy), label, font=lf, fill=(255, 255, 255), anchor="lm")
    tx = x0 + 20 + lw + 16
    first_cy = cy - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        d.text((tx, first_cy + i * lh), ln, font=f, fill=YELLOW_INK,
               anchor="lm")
    b.check("conclusion", x0, y0, x1, y0 + h)
    return y0 + h

def _fit_label(d, text, w, h, bold=True, start=27, lo=16):
    for size in range(start, lo - 1, -1):
        fnt = font(size, bold=bold)
        lines = wrap(d, text, fnt, w)
        lh = int(sum(fnt.getmetrics()) * 1.14)
        if len(lines) * lh <= h and all(d.textlength(l, font=fnt) <= w
                                        for l in lines):
            return fnt, lines, lh
    fnt = font(lo, bold=bold)
    lines = wrap(d, text, fnt, w)
    lh = int(sum(fnt.getmetrics()) * 1.14)
    return fnt, lines, lh

def _label_centered(d, cx, cy, fnt, lines, lh, ink):
    top = cy - len(lines) * lh / 2
    for i, ln in enumerate(lines):
        lw = d.textlength(ln, font=fnt)
        d.text((cx - lw / 2, top + i * lh), ln, font=fnt, fill=ink)

def _flow_box(d, b, cx, cy, w, h, node, ci, name):
    line, fill, ink, _ = style_for(node.get("kind", "plain"), ci)
    rounded(d, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 14,
            fill=fill, outline=line, width=3)
    b.check(name, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    fnt, lines, lh = _fit_label(d, node["label"], w - 22, h - 14)
    _label_centered(d, cx, cy, fnt, lines, lh, ink)

def _flow_diamond(d, b, cx, cy, w, h, node, name):
    line, fill, ink, _ = style_for(node.get("kind", "plain"))
    pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2),
           (cx - w / 2, cy)]
    d.polygon(pts, fill=fill, outline=line)
    d.line(pts + [pts[0]], fill=line, width=3)
    b.check(name, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    fnt, lines, lh = _fit_label(d, node["label"], w * 0.66, h * 0.72)
    _label_centered(d, cx, cy, fnt, lines, lh, ink)

def draw_flow_h(d, b, x0, y0, w, flow, name):
    nodes = flow["nodes"]
    by_id = {n["id"]: n for n in nodes}
    row0 = [n for n in nodes if n.get("row", 0) == 0]
    row1 = [n for n in nodes if n.get("row", 0) == 1]
    n0 = len(row0)
    gap = 72
    nw = min(248, (w - gap * (n0 - 1)) / n0)
    nh = 86
    dia_w = min(272, nw + 48)
    dia_h = 96
    top = y0
    note = flow.get("note")
    if note:
        nf = font(23)
        nlines = wrap(d, note, nf, w * 0.5)
        nlh = int(sum(nf.getmetrics()) * 1.2)
        nbh = nlh * len(nlines) + 24
        nbw = min(w * 0.56, max(d.textlength(l, font=nf) for l in nlines) + 40)
        nbx = x0 + w * 0.28
        d.rounded_rectangle((nbx, top, nbx + nbw, top + nbh), radius=12,
                            outline=BOX_COLORS[0], width=2)
        yy = top + 12
        for l in nlines:
            d.text((nbx + 20, yy), l, font=nf, fill=BOX_COLORS[0])
            yy += nlh
        b.check(name + "-note", nbx, top, nbx + nbw, top + nbh)
        top += nbh + 10
    row0_cy = top + dia_h / 2
    total = nw * n0 + gap * (n0 - 1)
    startx = x0 + (w - total) / 2
    pos = {}
    for i, nd in enumerate(row0):
        cx = startx + i * (nw + gap) + nw / 2
        if nd.get("shape") == "decision":
            _flow_diamond(d, b, cx, row0_cy, dia_w, dia_h, nd,
                          name + "-" + nd["id"])
            pos[nd["id"]] = (cx, row0_cy, dia_w / 2, dia_h / 2)
        else:
            _flow_box(d, b, cx, row0_cy, nw, nh, nd, i, name + "-" + nd["id"])
            pos[nd["id"]] = (cx, row0_cy, nw / 2, nh / 2)
    row1_cy = row0_cy + dia_h / 2 + nh / 2 + 42
    for nd in row1:
        under = by_id[nd["id"]].get("under")
        cx = pos[under][0] if under in pos else x0 + w / 2
        _flow_box(d, b, cx, row1_cy, nw, nh, nd, 2, name + "-" + nd["id"])
        pos[nd["id"]] = (cx, row1_cy, nw / 2, nh / 2)
    has_loop = any(e[3] for e in flow.get("edges", []))
    ef = font(23, bold=True)
    elh = int(sum(ef.getmetrics()))
    for frm, to, label, loopback in flow.get("edges", []):
        fx, fy, fhw, fhh = pos[frm]
        tx, ty2, thw, thh = pos[to]
        if loopback:
            ry = row1_cy + nh / 2 + 26
            d.line([(fx, fy + fhh), (fx, ry)], fill=ACCENT, width=3)
            d.line([(fx, ry), (tx, ry)], fill=ACCENT, width=3)
            arrow(d, tx, ry, tx, ty2 + thh + 2, color=ACCENT)
            if label:
                lw2 = d.textlength(label, font=ef)
                d.text((min(fx, tx) + abs(fx - tx) / 2 - lw2 / 2, ry + 8),
                       label, font=ef, fill=ACCENT)
        elif abs(fy - ty2) > 20:
            arrow(d, fx, fy + fhh, tx, ty2 - thh, color=SUBINK)
            if label:
                d.text((fx + 20, (fy + fhh + ty2 - thh) / 2 - elh / 2), label,
                       font=ef, fill=SUBINK)
        else:
            arrow(d, fx + fhw, fy, tx - thw, ty2, color=SUBINK)
            if label:
                lw2 = d.textlength(label, font=ef)
                seg_mid = (fx + fhw + tx - thw) / 2
                d.text((seg_mid - lw2 / 2, fy - elh - 12), label,
                       font=ef, fill=SUBINK)
    if has_loop:
        bottom = row1_cy + nh / 2 + 26 + 8 + elh + 8
    elif row1:
        bottom = row1_cy + nh / 2
    else:
        bottom = row0_cy + dia_h / 2
    b.check(name, x0, y0, x0 + w, bottom + 4)
    return bottom

def render_code_explain(spec):
    global W, H, SAFE
    wide = spec.get("layout") == "wide"
    oldW, oldH, oldSAFE = W, H, SAFE
    if wide:
        W, H = 1440, 1440
        SAFE = (MARGIN, MARGIN, W - MARGIN, H - MARGIN)
    try:
        img, d = new_card()
        b = Bounds()
        y = title_bar(d, b, spec["title"])
        if spec.get("subtitle"):
            sf = font(30)
            d.text((MARGIN, y + 8), spec["subtitle"], font=sf, fill=SUBINK)
            y += 8 + sum(sf.getmetrics())
        y += 30

        blocks = spec.get("code_blocks", [])
        inner = W - 2 * MARGIN
        if len(blocks) >= 2 and spec.get("equals"):
            eq_w = 70
            bw = (inner - eq_w) / 2
            shared = _fit_mono(d, blocks[0]["lines"] + blocks[1]["lines"],
                               bw - 40, start=24, lo=15)
            b0 = draw_code_box(d, b, MARGIN, y, bw, blocks[0], "codeA", 0,
                               msize=shared)
            b1 = draw_code_box(d, b, MARGIN + bw + eq_w, y, bw, blocks[1],
                               "codeB", 1, msize=shared)
            ef = font(72, bold=True)
            ew = d.textlength("=", font=ef)
            d.text((MARGIN + bw + eq_w / 2 - ew / 2, y + 40), "=", font=ef,
                   fill=ACCENT)
            code_bottom = max(b0, b1)
        else:
            code_bottom = y
            for i, blk in enumerate(blocks):
                code_bottom = draw_code_box(d, b, MARGIN, code_bottom, inner,
                                            blk, f"code{i}", i)
                code_bottom += 26
        yb = code_bottom + 18

        if spec.get("flow"):
            yb = draw_flow_h(d, b, MARGIN, yb, inner, spec["flow"],
                             "flow") + 24
        if spec.get("mapping"):
            yb = draw_mapping(d, b, MARGIN, yb, inner, spec["mapping"],
                              "mapping") + 18

        if spec.get("conclusion"):
            draw_conclusion(d, b, yb + 2, spec["conclusion"])

        signature(d, b)
        return img
    finally:
        W, H, SAFE = oldW, oldH, oldSAFE

# ============================================================================
# DRIVE
# ============================================================================
def main():
    outdir = os.environ.get("OUTDIR", ".")
    os.makedirs(outdir, exist_ok=True)
    prefix = f"{DATE}-AI-Day{DAY}"

    cards = []
    cards.append(("cover", render_cover(D["cover"])))
    cards.append(("pipeline", render_pipeline(D["pipeline"])))
    cards.append(("compare", render_compare(D["compare"])))
    for i, m in enumerate(D["methods"]):
        if m["type"] == "branch":
            img = render_branch(m)
            name = m.get("name", f"method{i+1}-branch")
        else:
            img = render_linear(m)
            name = m.get("name", f"method{i+1}")
        cards.append((name, img))
    for i, ce in enumerate(D.get("code_explain", [])):
        cards.append((ce.get("name", f"code-explain{i+1}"),
                      render_code_explain(ce)))
    cards.append(("glossary", render_glossary(D["glossary"])))

    saved = []
    for idx, (name, img) in enumerate(cards, start=1):
        path = os.path.join(outdir, f"{prefix}-{idx:02d}-{name}.png")
        img.save(path)
        saved.append(path)
        print("saved", path)

    # contact sheet for one-glance review (do not open full-res PNGs one by one)
    cols = len(cards)
    thumb_w = 300
    thumb_h = int(thumb_w * H / W)
    sheet = Image.new("RGB", (cols * (thumb_w + 16) + 16, thumb_h + 32),
                      (255, 255, 255))
    x = 16
    for _, img in cards:
        sheet.paste(img.resize((thumb_w, thumb_h)), (x, 16))
        x += thumb_w + 16
    cpath = os.path.join(outdir, f"{prefix}-contact-sheet.png")
    sheet.save(cpath)
    print("saved", cpath)
    print(f"\nOK: rendered {len(cards)} cards, bounds audit passed.")


if __name__ == "__main__":
    main()
