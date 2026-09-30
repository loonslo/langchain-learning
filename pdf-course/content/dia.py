"""图表原语库：把常见的概念形状（流程 / 循环 / 分层 / 对比 / 状态机 / 时间轴 /
序列 / 量级）封装成函数，让正文里每张图只需三五行代码。

为什么要有这一层：一本书要几十张图，如果每张都手写 SVG，一是慢，二是风格必然漂。
这里把「配色 / 字号 / 圆角 / 箭头 / 换行」全部收口，正文只管表达结构。

约定（与 base.css 一致，改配色只改这里）：
  画布宽 680 用户单位，经 `.figbody svg{width:100%}` 缩放到版心约 172mm，
  1 用户单位 ≈ 0.72pt。所以图内 font-size="13" ≈ 正文 9.3pt。

**SVG 的 text 不会自动换行**——所有长文本都过 `_wrap()` 按字宽估算切行，
否则中文长标签会直接冲出画布（这类溢出几何自检也量不出来，因为它在 SVG 内部）。
"""
import re

BRAND = "#14505e"      # 品牌色：主流程、标题
ACCENT = "#a4551f"     # 第二强调：负向、风险
INK = "#231f20"        # 正文近黑
MUTE = "#6b6b6b"       # 次级说明
RULE = "#d8d8d8"       # 分隔线
SOFT = "#e8ecee"       # 浅描边
PANEL = "#f4f7f8"      # 浅底
PANEL2 = "#faf7f2"     # 暖底（第二组）
OK = "#2f7d52"         # 正向/通过

FONT = "'Microsoft YaHei','Helvetica Neue',Arial,sans-serif"

_UID = {"n": 0}


def _uid():
    _UID["n"] += 1
    return f"d{_UID['n']}"


def reset_uid():
    _UID["n"] = 0


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _cw(ch):
    """粗略字宽：CJK 记 1.0，ASCII 记 0.55（够用，不追求精确）。"""
    o = ord(ch)
    return 1.0 if o > 0x2E80 else 0.55


def _wrap(s, maxw):
    """按「CJK 字宽」切行。maxw 单位是 CJK 字数。"""
    lines, cur, acc = [], "", 0.0
    for ch in str(s):
        if ch == "\n":
            lines.append(cur); cur, acc = "", 0.0
            continue
        c = _cw(ch)
        if acc + c > maxw and cur:
            lines.append(cur); cur, acc = "", 0.0
        cur += ch; acc += c
    if cur:
        lines.append(cur)
    return lines or [""]


def _text(x, y, lines, size=13, fill=INK, anchor="start", weight="400", lh=None):
    """多行文本。lines 可以是字符串（自动切行由调用方负责）或列表。"""
    if isinstance(lines, str):
        lines = [lines]
    lh = lh or size * 1.42
    out = []
    for i, ln in enumerate(lines):
        dy = 0 if i == 0 else lh
        out.append(f'<tspan x="{x:g}" dy="{dy:g}">{_esc(ln)}</tspan>')
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'font-family="{FONT}">' + "".join(out) + "</text>")


def _rect(x, y, w, h, fill="#ffffff", stroke=SOFT, rx=3, sw=1):
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}"/>')


def _defs_arrow(uid, color=BRAND):
    return (f'<defs><marker id="{uid}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>')


def _arrow(x1, y1, x2, y2, uid, color=BRAND, sw=1.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" '
            f'stroke-width="{sw:g}" marker-end="url(#{uid})"{d}/>')


def _svg(w, h, body, cls="dia"):
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img">{body}</svg>')


# ══════════════════════════════════════════════════════════════════
# 1. 流程：一串方框 + 箭头。最常用。
# ══════════════════════════════════════════════════════════════════

def flow(steps, direction="h", note=None, title=None, tone=None):
    """流程链。steps 是 [(主文本, 副文本)] 或 [主文本]。

    direction="h" 横向（步骤 ≤ 4 个）；"v" 纵向（步骤多或文字长）。
    tone: 可给 {"idx": [0,2], "color": ACCENT} 给特定步骤换色。
    """
    steps = [s if isinstance(s, (list, tuple)) else (s, "") for s in steps]
    tone = tone or {}
    hot = set(tone.get("idx", []))
    hcol = tone.get("color", ACCENT)
    uid = _uid()
    body = [_defs_arrow(uid)]
    top = 0
    if title:
        body.append(_text(0, 14, title, size=13, fill=MUTE, weight="700"))
        top = 26

    if direction == "h":
        n = len(steps)
        gap = 30
        bw = (680 - gap * (n - 1)) / n
        # 方框高度按最“高”的一格算：写死高度时，副文本一换行就会溢出方框下沿
        cells = []
        for main, sub in steps:
            ml = _wrap(main, (bw - 20) / 13)
            sl = _wrap(sub, (bw - 18) / 11) if sub else []
            cells.append((ml, sl))
        bh = max(22 + 18 * len(ml) + (8 + 16 * len(sl) if sl else 0) + 12
                 for ml, sl in cells)
        for i, (ml, sl) in enumerate(cells):
            x = i * (bw + gap)
            col = hcol if i in hot else BRAND
            body.append(_rect(x, top, bw, bh, fill=PANEL, stroke=SOFT))
            body.append(f'<rect x="{x:g}" y="{top:g}" width="2.6" height="{bh:g}" '
                        f'fill="{col}" rx="1.3"/>')
            body.append(_text(x + bw / 2, top + 22, ml, size=13, fill=INK,
                              anchor="middle", weight="700"))
            if sl:
                body.append(_text(x + bw / 2, top + 22 + 18 * len(ml) + 8, sl,
                                  size=11, fill=MUTE, anchor="middle"))
            if i < n - 1:
                y = top + bh / 2
                body.append(_arrow(x + bw + 5, y, x + bw + gap - 5, y, uid))
        h = top + bh
    else:
        # 纵向：主文本一行、副文本另起一行并淡色。行高按内容自适应，
        # 不写死——写死的话主文本一换行就会和副文本叠在一起。
        bw = 680
        gap = 20
        rows = []
        for main, sub in steps:
            ml = _wrap(main, 46)
            sl = _wrap(sub, 58) if sub else []
            hh = 16 + 19 * len(ml) + (16 * len(sl) + 5 if sl else 0) + 14
            rows.append((ml, sl, hh))
        y = top
        for i, (ml, sl, hh) in enumerate(rows):
            col = hcol if i in hot else BRAND
            body.append(_rect(0, y, bw, hh, fill=PANEL, stroke=SOFT))
            body.append(f'<rect x="0" y="{y:g}" width="2.6" height="{hh:g}" '
                        f'fill="{col}" rx="1.3"/>')
            body.append(_text(16, y + 22, ml, size=13, fill=INK, weight="700"))
            if sl:
                body.append(_text(16, y + 22 + 19 * len(ml) + 6, sl, size=11, fill=MUTE))
            if i < len(rows) - 1:
                body.append(_arrow(bw / 2, y + hh + 2, bw / 2, y + hh + gap - 2, uid))
            y += hh + gap
        h = y - gap

    if note:
        body.append(_text(0, h + 20, _wrap(note, 60), size=11, fill=MUTE))
        h += 16 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 2. 循环：中间一个核心，四周若干步骤，箭头绕回来。
# ══════════════════════════════════════════════════════════════════

def loop(steps, center="", note=None):
    """循环图：一排步骤 + 底部回环箭头。

    不用「步骤绕圆摆放」——那需要按角度算坐标，步骤数一变就重叠，
    而且中文标签宽窄不一，绕圆几乎必然压线。改成一排 + 底部回环，
    结构一眼看清，步骤数 2~5 都稳。
    """
    steps = [s if isinstance(s, (list, tuple)) else (s, "") for s in steps]
    uid = _uid()
    body = [_defs_arrow(uid)]
    n = len(steps)
    gap = 30
    bw = (680 - gap * (n - 1)) / n
    cells = []
    for main, sub in steps:
        ml = _wrap(main, (bw - 20) / 13)
        sl = _wrap(sub, (bw - 18) / 11) if sub else []
        cells.append((ml, sl))
    bh = max(18 + 18 * len(ml) + (8 + 16 * len(sl) if sl else 0) + 12
             for ml, sl in cells)
    for i, (ml, sl) in enumerate(cells):
        x = i * (bw + gap)
        body.append(_rect(x, 0, bw, bh, fill=PANEL, stroke=SOFT))
        body.append(f'<rect x="{x:g}" y="0" width="2.6" height="{bh:g}" fill="{BRAND}" rx="1.3"/>')
        body.append(_text(x + bw / 2, 22, ml, size=13,
                          fill=INK, anchor="middle", weight="700"))
        if sl:
            body.append(_text(x + bw / 2, 22 + 18 * len(ml) + 8, sl, size=11,
                              fill=MUTE, anchor="middle"))
        if i < n - 1:
            y = bh / 2
            body.append(_arrow(x + bw + 5, y, x + bw + gap - 5, y, uid))

    # 回环：从最后一格底部绕回第一格底部
    ry = bh + 36
    xa = n * bw + (n - 1) * gap - bw / 2      # 最后一格中心
    xb = bw / 2                               # 第一格中心
    body.append(f'<path d="M{xa:g},{bh + 3:g} V{ry:g} H{xb:g} V{bh + 3:g}" '
                f'fill="none" stroke="{BRAND}" stroke-width="1.4" '
                f'marker-end="url(#{uid})"/>')
    if center:
        body.append(_text((xa + xb) / 2, ry - 7, _wrap(center, 24), size=11.5,
                          fill=BRAND, anchor="middle", weight="700"))
    h = ry + 6
    if note:
        body.append(_text(0, h + 16, _wrap(note, 60), size=11, fill=MUTE))
        h += 12 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 3. 分层：自上而下的横条，表达「层级 / 边界」。
# ══════════════════════════════════════════════════════════════════

def layers(rows, note=None, tone=None):
    """分层图。rows 是 [(标题, 说明)]，自上而下。tone 同 flow。"""
    tone = tone or {}
    hot = set(tone.get("idx", []))
    hcol = tone.get("color", ACCENT)
    body = []
    y = 0
    gap = 8
    for i, (title, desc) in enumerate(rows):
        col = hcol if i in hot else BRAND
        # 行高按内容算：标题一换行就会撞到下面的说明行
        tl = _wrap(title, 60)
        dl = _wrap(desc, 46) if desc else []
        rh = 12 + 18 * len(tl) + (16 * len(dl) + 4 if dl else 0) + 12
        body.append(_rect(0, y, 680, rh, fill=PANEL if i % 2 == 0 else "#ffffff",
                          stroke=SOFT))
        body.append(f'<rect x="0" y="{y:g}" width="3" height="{rh:g}" fill="{col}" rx="1.5"/>')
        body.append(_text(16, y + 24, tl, size=13, fill=INK, weight="700"))
        if dl:
            body.append(_text(16, y + 24 + 18 * len(tl) + 4, dl, size=11, fill=MUTE))
        y += rh + gap
    hh = y - gap
    if note:
        body.append(_text(0, hh + 20, _wrap(note, 60), size=11, fill=MUTE))
        hh += 16 + 16 * len(_wrap(note, 60))
    return _svg(680, hh + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 4. 对比：左右两栏，各带要点。表达「两种做法 / 两个概念」。
# ══════════════════════════════════════════════════════════════════

def compare(left, right, note=None, left_tone=BRAND, right_tone=ACCENT):
    """对比图。left/right = (标题, [要点...])。

    列高按每列实际累计的 y 取最大值，**不要**用「最长那条 × 条数」估算——
    两列条数不等、或某条换了两行时，估算值会偏小，脚注就会压在最后一条要点上
    （实测 119 张图里 28 处重叠全部出在这里）。
    """
    body = []
    colw = 326
    gap = 28
    bottom = 0
    for k, (side, items, col) in enumerate((
            (left, left[1], left_tone), (right, right[1], right_tone))):
        x = k * (colw + gap)
        tl = _wrap(side[0], 18)
        hh = 14 + 18 * len(tl) + 12
        body.append(_rect(x, 0, colw, hh, fill=col, stroke=col))
        body.append(_text(x + colw / 2, 14 + 18 * len(tl) - 6, tl, size=13,
                          fill="#ffffff", anchor="middle", weight="700"))
        y = hh + 12
        for it in items:
            ls = _wrap(it, 24)
            body.append(f'<circle cx="{x + 10:g}" cy="{y + 5:g}" r="3.2" fill="{col}"/>')
            body.append(_text(x + 22, y + 10, ls, size=12, fill=INK))
            y += len(ls) * 17 + 12
        bottom = max(bottom, y)
    h = bottom
    if note:
        body.append(_text(0, h + 20, _wrap(note, 60), size=11, fill=MUTE))
        h += 16 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 5. 状态机：一串状态 + 带标注的转移。表达「有生命周期的任务 / 工作流」。
# ══════════════════════════════════════════════════════════════════

def states(items, note=None, tone=None):
    """状态链。items = [(状态名, 说明)] 或 [(状态名, 说明, 边标签)]。"""
    tone = tone or {}
    hot = set(tone.get("idx", []))
    hcol = tone.get("color", ACCENT)
    uid = _uid()
    body = [_defs_arrow(uid)]
    n = len(items)
    gap = 34
    bw = (680 - gap * (n - 1)) / n
    # 方框高度按最高的一格算：状态名一换行就会撞到下面的说明行
    cells = []
    for it in items:
        nl = _wrap(it[0], (bw - 14) / 12)
        dl = _wrap(it[1], (bw - 12) / 10.5) if it[1] else []
        cells.append((nl, dl))
    bh = max(16 + 17 * len(nl) + (15 * len(dl) + 4 if dl else 0) + 12
             for nl, dl in cells)
    for i, (nl, dl) in enumerate(cells):
        it = items[i]
        edge = it[2] if len(it) > 2 else ""
        x = i * (bw + gap)
        col = hcol if i in hot else BRAND
        body.append(_rect(x, 0, bw, bh, fill="#ffffff", stroke=col, sw=1.4))
        body.append(_text(x + bw / 2, 24, nl, size=12,
                          fill=col, anchor="middle", weight="700"))
        if dl:
            body.append(_text(x + bw / 2, 24 + 17 * len(nl) + 8, dl, size=10,
                              fill=MUTE, anchor="middle"))
        if i < n - 1:
            y = bh / 2
            body.append(_arrow(x + bw + 4, y, x + bw + gap - 4, y, uid, color=col))
            if edge:
                body.append(_text(x + bw + gap / 2, y - 8, _wrap(edge, 5), size=9.5,
                                  fill=MUTE, anchor="middle"))
    h = bh
    if note:
        body.append(_text(0, h + 20, _wrap(note, 60), size=11, fill=MUTE))
        h += 16 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 6. 时间轴：横向推进，表达「一段时间的演进 / 分阶段」。
# ══════════════════════════════════════════════════════════════════

def timeline(items, note=None):
    """时间轴。items = [(标记, 标题)] 或 [(标记, 标题, 说明)]，顺序推进。

    说明可省略——调用方传两项元组时不该让整本书构建失败（踩过）。

    首尾节点必须内缩：居中的标签在最边上会直接冲出画布（几何自检查不到，
    因为溢出发生在 SVG 内部）。
    """
    body = []
    items = [(t[0], t[1], t[2] if len(t) > 2 else "") for t in items]
    n = len(items)
    y0 = 34
    L, R = 74, 606          # 内缩，给首尾的居中标签留出半宽
    body.append(f'<line x1="{L:g}" y1="{y0}" x2="{R:g}" y2="{y0}" stroke="{RULE}" '
                f'stroke-width="2"/>')
    step = (R - L) / max(n - 1, 1)
    for i, (tag, title, desc) in enumerate(items):
        x = L + i * step
        body.append(f'<circle cx="{x:g}" cy="{y0}" r="6" fill="{BRAND}"/>')
        body.append(_text(x, y0 - 14, tag, size=11, fill=BRAND, anchor="middle",
                          weight="700"))
        tl = _wrap(title, 11)
        body.append(_text(x, y0 + 34, tl, size=12, fill=INK,
                          anchor="middle", weight="700"))
        if desc:
            body.append(_text(x, y0 + 34 + 20 + 15 * len(tl),
                              _wrap(desc, 13), size=10, fill=MUTE, anchor="middle"))
    h = y0 + 34 + 40 + 46
    if note:
        body.append(_text(0, h + 14, _wrap(note, 60), size=11, fill=MUTE))
        h += 10 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 7. 序列：两个（或多个）角色之间来回的消息。表达「跨服务协作」。
# ══════════════════════════════════════════════════════════════════

def seq(actors, msgs, note=None):
    """序列图。actors = [角色名]，msgs = [(from_idx, to_idx, 文本, 是否返回)]。"""
    uid = _uid()
    body = [_defs_arrow(uid)]
    n = len(actors)
    step = 680 / n
    xs = [step * (i + 0.5) for i in range(n)]
    head_h = 40
    for i, a in enumerate(actors):
        body.append(_rect(xs[i] - 82, 0, 164, head_h, fill=PANEL, stroke=SOFT))
        body.append(_text(xs[i], 25, _wrap(a, 12), size=12, fill=INK,
                          anchor="middle", weight="700"))
    y = head_h + 26
    lifeline_bottom = y + 30 * len(msgs)
    # 生命线先画：后画会压在消息箭头上面
    for i in range(n):
        body.append(f'<line x1="{xs[i]:g}" y1="{head_h:g}" x2="{xs[i]:g}" '
                    f'y2="{lifeline_bottom + 14:g}" stroke="{RULE}" '
                    f'stroke-width="1" stroke-dasharray="3 4"/>')
    for m in msgs:
        a, b, txt = m[0], m[1], m[2]
        ret = m[3] if len(m) > 3 else False
        col = MUTE if ret else BRAND
        y += 30
        x1, x2 = xs[a], xs[b]
        body.append(_arrow(x1, y, x2, y, uid, color=col, sw=1.3,
                           dash="4 3" if ret else None))
        mid = (x1 + x2) / 2
        body.append(_text(mid, y - 8, _wrap(txt, 22), size=11, fill=col,
                          anchor="middle"))
    h = lifeline_bottom + 20
    if note:
        body.append(_text(0, h + 16, _wrap(note, 60), size=11, fill=MUTE))
        h += 12 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 8. 量级：横向条，表达「数字的大小关系」。比表格直观。
# ══════════════════════════════════════════════════════════════════

def bars(items, note=None, unit="", maxv=None, tone=None):
    """条形图。items = [(标签, 数值, 右侧文字)]。

    默认**不**高亮任何一条——高亮要由调用方明确指定（tone={"idx":[...]})，
    否则「第一条永远是橙色」会被读者当成有含义。
    """
    tone = tone or {}
    hot = set(tone.get("idx", []))
    hcol = tone.get("color", ACCENT)
    body = []
    n = len(items)
    row = 34
    label_w = 190
    bar_w = 300
    mx = maxv or max(v for _, v, _ in items)
    for i, (lab, v, txt) in enumerate(items):
        y = i * row
        body.append(_text(0, y + 18, _wrap(lab, 15), size=12, fill=INK))
        body.append(_rect(label_w, y + 6, bar_w, 16, fill="#f0f3f4", stroke="none", rx=2))
        bw = max(bar_w * (v / mx), 2)
        col = hcol if i in hot else BRAND
        body.append(f'<rect x="{label_w:g}" y="{y + 6:g}" width="{bw:g}" height="16" '
                    f'rx="2" fill="{col}"/>')
        body.append(_text(label_w + bar_w + 12, y + 19,
                          f"{txt}{unit}", size=11, fill=INK, weight="700"))
    h = n * row
    if note:
        body.append(_text(0, h + 14, _wrap(note, 60), size=11, fill=MUTE))
        h += 10 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 9. 卡片网格：并排的若干概念，表达「并列的几类东西」。
# ══════════════════════════════════════════════════════════════════

def cards(items, cols=2, note=None, tone=None):
    """卡片网格。items = [(标题, 说明)]。tone 同 flow。"""
    tone = tone or {}
    hot = set(tone.get("idx", []))
    hcol = tone.get("color", ACCENT)
    body = []
    gap = 16
    cw = (680 - gap * (cols - 1)) / cols
    rows = (len(items) + cols - 1) // cols
    maxh = 0
    heights = []
    for it in items:
        t = len(_wrap(it[0], (cw - 24) / 13))
        d = len(_wrap(it[1], (cw - 24) / 11)) if it[1] else 0
        heights.append(26 + t * 19 + (d * 16 + 8 if d else 0))
    maxh = max(heights) if heights else 60
    for i, (title, desc) in enumerate(items):
        r, c = divmod(i, cols)
        x = c * (cw + gap)
        y = r * (maxh + gap)
        col = hcol if i in hot else BRAND
        body.append(_rect(x, y, cw, maxh, fill=PANEL, stroke=SOFT))
        body.append(f'<rect x="{x:g}" y="{y:g}" width="{cw:g}" height="2.6" '
                    f'fill="{col}" rx="1.3"/>')
        body.append(_text(x + 12, y + 24, _wrap(title, (cw - 24) / 13), size=12.5,
                          fill=INK, weight="700"))
        if desc:
            body.append(_text(x + 12, y + 26 + 19 * len(_wrap(title, (cw - 24) / 13)) + 14,
                              _wrap(desc, (cw - 24) / 11), size=11, fill=MUTE))
    h = rows * maxh + (rows - 1) * gap
    if note:
        body.append(_text(0, h + 18, _wrap(note, 60), size=11, fill=MUTE))
        h += 14 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))


# ══════════════════════════════════════════════════════════════════
# 10. 堆叠条：表达「一次请求里各段耗时 / 成本占比」。
# ══════════════════════════════════════════════════════════════════

def stack(items, note=None, tone=None):
    """堆叠条。items = [(标签, 占比数值)]，会按比例横向排布。"""
    tone = tone or {}
    hot = set(tone.get("idx", []))
    hcol = tone.get("color", ACCENT)
    body = []
    total = sum(v for _, v in items) or 1
    x = 0
    H = 52
    for i, (lab, v) in enumerate(items):
        w = 680 * v / total
        col = hcol if i in hot else (BRAND if i % 2 == 0 else "#2f6f7d")
        body.append(f'<rect x="{x:g}" y="0" width="{w - 2:g}" height="{H}" rx="2" fill="{col}"/>')
        body.append(_text(x + w / 2, 24, _wrap(lab, max(w / 12, 3)), size=11,
                          fill="#ffffff", anchor="middle", weight="700"))
        body.append(_text(x + w / 2, 41, f"{v:g}", size=10.5, fill="#ffffff",
                          anchor="middle"))
        x += w
    h = H
    if note:
        body.append(_text(0, h + 16, _wrap(note, 60), size=11, fill=MUTE))
        h += 12 + 16 * len(_wrap(note, 60))
    return _svg(680, h + 6, "".join(body))
