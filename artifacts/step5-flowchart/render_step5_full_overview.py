# -*- coding: utf-8 -*-
"""Render the wide Step4 source overview requested by the user.

This intentionally uses a wide source-map layout: one main route, the three
early exits, and the lower supervisor loop are visible on the same canvas.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 2800, 1220
BG = (252, 252, 253)
INK = (42, 51, 67)
SUB = (103, 112, 126)
GRID = (226, 230, 236)
ORANGE = (244, 137, 34)
ORANGE_DARK = (202, 104, 20)
BLUE = (218, 231, 255)
BLUE_DARK = (102, 148, 248)
GRAY = (239, 241, 245)
GRAY_DARK = (142, 151, 164)
YELLOW = (255, 242, 199)
YELLOW_DARK = (226, 161, 38)
GREEN = (218, 248, 225)
GREEN_DARK = (38, 156, 84)
RED = (255, 222, 222)
RED_DARK = (222, 83, 83)
ORANGE_NOTE = (255, 246, 226)
ORANGE_NOTE_DARK = (231, 154, 60)
RED_NOTE = (255, 232, 232)
SIGN = (164, 170, 182)


def _font_path(*paths: str) -> str | None:
    for path in paths:
        if os.path.exists(path):
            return path
    return None


REGULAR = _font_path(
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)
BOLD = _font_path(
    "C:/Windows/Fonts/msyhbd.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
) or REGULAR
_FONTS: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False):
    key = (size, bold)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(BOLD if bold else REGULAR, size)
    return _FONTS[key]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textlength(candidate, font=fnt) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def line_height(fnt, leading: float = 1.28) -> int:
    ascent, descent = fnt.getmetrics()
    return int((ascent + descent) * leading)


def draw_lines(draw, x: float, y: float, lines: list[str], fnt, fill=INK, gap=0):
    lh = line_height(fnt) + gap
    for index, line in enumerate(lines):
        draw.text((x, y + index * lh), line, font=fnt, fill=fill)
    return y + len(lines) * lh


def centered(draw, cx: float, cy: float, text: str, fnt, fill=INK):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    draw.text((cx - (bbox[2] - bbox[0]) / 2, cy - (bbox[3] - bbox[1]) / 2),
              text, font=fnt, fill=fill)


def centered_block(draw, cx: float, cy: float, title: str, sub: str | None,
                  title_size=25, sub_size=17):
    title_font = font(title_size, True)
    sub_font = font(sub_size)
    title_lines = wrap(draw, title, title_font, 330)
    sub_lines = wrap(draw, sub, sub_font, 330) if sub else []
    title_lh = line_height(title_font)
    sub_lh = line_height(sub_font)
    total = len(title_lines) * title_lh + (8 if sub_lines else 0) + len(sub_lines) * sub_lh
    y = cy - total / 2
    for line in title_lines:
        centered(draw, cx, y + title_lh / 2, line, title_font)
        y += title_lh
    if sub_lines:
        y += 8
        for line in sub_lines:
            centered(draw, cx, y + sub_lh / 2, line, sub_font, SUB)
            y += sub_lh


def rounded(draw, box, fill, outline, radius=14, width=3):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def node_box(draw, x, y, w, h, title, sub=None, fill=BLUE, outline=BLUE_DARK,
             title_size=25, radius=12):
    rounded(draw, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), fill, outline, radius, 3)
    centered_block(draw, x, y, title, sub, title_size, 17)


def node_pill(draw, x, y, w, h, title, fill=GRAY, outline=GRAY_DARK, title_size=24):
    rounded(draw, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), fill, outline, h / 2, 3)
    centered(draw, x, y, title, font(title_size, True))


def node_diamond(draw, x, y, w, h, title, sub=None, fill=YELLOW,
                 outline=YELLOW_DARK, title_size=24):
    points = [(x, y - h / 2), (x + w / 2, y), (x, y + h / 2), (x - w / 2, y)]
    draw.polygon(points, fill=fill)
    draw.line(points + [points[0]], fill=outline, width=3, joint="curve")
    centered_block(draw, x, y, title, sub, title_size, 16)


def arrowhead(draw, x, y, angle, color=ORANGE, size=13, width=3):
    for delta in (math.radians(150), math.radians(-150)):
        draw.line((x, y, x + size * math.cos(angle + delta),
                   y + size * math.sin(angle + delta)), fill=color, width=width)


def poly_arrow(draw, points, color=ORANGE, width=3, dashed=False):
    for start, end in zip(points, points[1:]):
        x0, y0 = start
        x1, y1 = end
        if dashed:
            length = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / length, (y1 - y0) / length
            pos = 0
            while pos < length:
                end_pos = min(pos + 10, length)
                draw.line((x0 + ux * pos, y0 + uy * pos,
                           x0 + ux * end_pos, y0 + uy * end_pos), fill=color, width=width)
                pos += 17
        else:
            draw.line((x0, y0, x1, y1), fill=color, width=width, joint="curve")
    x0, y0 = points[-2]
    x1, y1 = points[-1]
    arrowhead(draw, x1, y1, math.atan2(y1 - y0, x1 - x0), color, width=width)


def label(draw, x, y, text, color=INK, size=18, bg=BG):
    fnt = font(size)
    bbox = draw.textbbox((0, 0), text, font=fnt)
    pad_x, pad_y = 8, 4
    draw.rectangle((x - (bbox[2] - bbox[0]) / 2 - pad_x,
                    y - (bbox[3] - bbox[1]) / 2 - pad_y,
                    x + (bbox[2] - bbox[0]) / 2 + pad_x,
                    y + (bbox[3] - bbox[1]) / 2 + pad_y), fill=bg)
    centered(draw, x, y, text, fnt, color)


def note(draw, x, y, w, h, title, lines, fill=ORANGE_NOTE, outline=ORANGE_NOTE_DARK,
         title_color=INK, size=18):
    box = (x, y, x + w, y + h)
    draw.rounded_rectangle(box, radius=5, fill=fill, outline=outline, width=2)
    draw.text((x + 18, y + 15), title, font=font(size, True), fill=title_color)
    cursor = y + 52
    body_font = font(size - 2)
    for text in lines:
        rows = wrap(draw, text, body_font, w - 36)
        cursor = draw_lines(draw, x + 18, cursor, rows, body_font, INK, gap=1)
        cursor += 6


def cross_grid(draw):
    for x in range(70, W - 40, 82):
        for y in range(48, H - 25, 82):
            draw.line((x - 3, y, x + 3, y), fill=GRID, width=1)
            draw.line((x, y - 3, x, y + 3), fill=GRID, width=1)


def dotted_callout(draw, start, end, color=(180, 185, 194), via=None):
    points = [start] + list(via or []) + [end]
    poly_arrow(draw, points, color=color, width=2, dashed=True)


def check_rect(name, x, y, w, h):
    if x - w / 2 < 35 or x + w / 2 > W - 35 or y - h / 2 < 35 or y + h / 2 > 1125:
        raise ValueError(f"{name} leaves the safe frame")


def main():
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    cross_grid(draw)

    title = "Step5 完整 Graph 流程图 · Supervisor 动态并行 + MCP 成本计算"
    draw.text((52, 22), title, font=font(38, True), fill=INK)
    draw.text((W - 52, 30), "@测试阿甲", font=font(18), fill=SIGN, anchor="ra")

    # Notes explain the Step5 contract without turning the image into a source dump.
    note(draw, 50, 90, 520, 225, "GraphState：Step5 共享状态", [
        "question / route / work_items",
        "completed_items / evidence",
        "errors / trace / supervisor_steps",
        "context / final_answer",
        "Reducer：并行结果由 Graph 累积",
    ], size=19)
    note(draw, 610, 90, 650, 225, "Step4 → Step5 核心变化", [
        "Step4：specialist 逐个执行 collect()",
        "Step5：Send 为每个 WorkItem 派隔离专家",
        "同一 parallel_group 可同一 super-step 并行",
        "后续 group 只收到前序 evidence",
        "evidence / errors / trace 由 Reducer 合并",
    ], size=19)
    note(draw, 1310, 90, 540, 225, "plan / supervisor / dispatch", [
        "WorkItem：id / source / instruction / group",
        "request_id 前缀后去重任务",
        "优先派发最早未完成的 parallel_group",
        "max_tool_calls + max_supervisor_steps",
        "完成或预算触发后才汇聚",
    ], size=19)
    note(draw, 1900, 90, 850, 225, "MCP 与 Step5 边界", [
        "adapters[item.source].collect()：web / sql / mcp",
        "MCP：Tools + Resources + Prompts → Evidence",
        "specialist 异常 → errors + trace，再回 supervisor",
        "requires_approval 只是字段，尚未接审批节点",
        "当前 Step5 生成后直接交付，不含 review / publish",
    ], fill=RED_NOTE, outline=RED_DARK, size=19)

    # Main route nodes.
    nodes = {
        "start": (165, 690, 130, 58),
        "intake": (390, 690, 155, 72),
        "route": (650, 690, 175, 84),
        "after": (930, 690, 230, 140),
        "clarify": (1300, 370, 195, 72),
        "out": (1700, 460, 210, 72),
        "restricted": (2080, 550, 230, 72),
        "plan": (1120, 900, 185, 78),
        "supervisor": (1450, 900, 190, 78),
        "dispatch": (1770, 900, 220, 130),
        "specialist": (1770, 1080, 220, 82),
        "compose": (2070, 900, 220, 82),
        "generate": (2290, 690, 190, 78),
        "end": (2610, 690, 140, 58),
    }
    for name, (x, y, w, h) in nodes.items():
        check_rect(name, x, y, w, h)

    # Main and branch edges are drawn first so nodes stay visually on top.
    poly_arrow(draw, [(230, 690), (312, 690)], width=3)
    poly_arrow(draw, [(468, 690), (562, 690)], width=3)
    poly_arrow(draw, [(737, 690), (815, 690)], width=3)
    poly_arrow(draw, [(930, 620), (930, 370), (1202, 370)], width=3)
    label(draw, 1080, 340, "missing_information 非空", ORANGE_DARK, 17)
    poly_arrow(draw, [(875, 635), (875, 460), (1590, 460)], width=3)
    label(draw, 1110, 430, "in_scope = false", ORANGE_DARK, 17)
    poly_arrow(draw, [(930, 760), (930, 900), (1027, 900)], width=3)
    label(draw, 980, 830, "否则：可执行", ORANGE_DARK, 17)
    poly_arrow(draw, [(2385, 690), (2540, 690)], width=3)
    label(draw, 270, 660, "规范化", ORANGE_DARK, 17)
    label(draw, 520, 660, "model.route", ORANGE_DARK, 17)

    # Early exits share the same terminal. The trunk is deliberately explicit.
    poly_arrow(draw, [(1397, 370), (2450, 370)], width=3)
    poly_arrow(draw, [(1805, 460), (2450, 460)], width=3)
    draw.line((2450, 370, 2450, 690), fill=ORANGE, width=3)
    poly_arrow(draw, [(2450, 690), (2540, 690)], width=3)

    # The lower execution loop.
    poly_arrow(draw, [(1212, 900), (1355, 900)], width=3)
    poly_arrow(draw, [(1545, 900), (1660, 900)], width=3)
    poly_arrow(draw, [(1880, 900), (1960, 900)], width=3)
    label(draw, 1920, 865, "否：完成/超限", ORANGE_DARK, 17)
    poly_arrow(draw, [(1770, 965), (1770, 1039)], width=3)
    label(draw, 1825, 1005, "是", ORANGE_DARK, 17)
    # specialist always returns to supervisor; success and errors share this loop.
    poly_arrow(draw, [(1650, 1080), (1370, 1080), (1370, 940)], width=3)
    label(draw, 1500, 1020, "回边（循环）", ORANGE_DARK, 17)
    poly_arrow(draw, [(2070, 859), (2070, 730), (2195, 730)], width=3)
    label(draw, 2100, 760, "Evidence 已汇聚", ORANGE_DARK, 17)

    # Nodes.
    node_pill(draw, 165, 690, 130, 58, "START", GREEN, GREEN_DARK, 24)
    node_box(draw, 390, 690, 155, 72, "intake", "Step4 沿用", GRAY, GRAY_DARK, 24)
    node_box(draw, 650, 690, 175, 84, "route", "结构化 route", GRAY, GRAY_DARK, 24)
    node_diamond(draw, 930, 690, 230, 140, "after_route", "互斥分支", YELLOW, YELLOW_DARK, 22)
    node_box(draw, 1300, 370, 195, 72, "clarify", "missing_information", GRAY, GRAY_DARK, 22)
    node_box(draw, 1700, 460, 210, 72, "out_of_scope", "in_scope = false", GRAY, GRAY_DARK, 21)
    node_box(draw, 1120, 900, 185, 78, "plan", "任务分组 / 去重", BLUE, BLUE_DARK, 22)
    node_box(draw, 1450, 900, 190, 78, "supervisor", "steps + pending", BLUE, BLUE_DARK, 22)
    node_diamond(draw, 1770, 900, 220, 130, "dispatch", "pending 且未超限?", YELLOW, YELLOW_DARK, 21)
    node_box(draw, 1770, 1080, 250, 82, "specialist", "隔离上下文 · collect()", BLUE, BLUE_DARK, 20)
    node_box(draw, 2070, 900, 220, 82, "compose_context", "source / URL / warning", BLUE, BLUE_DARK, 20)
    node_box(draw, 2290, 690, 190, 78, "generate", "+ trace", GREEN, GREEN_DARK, 23)
    node_pill(draw, 2610, 690, 140, 58, "END", GREEN, GREEN_DARK, 24)

    # Explanatory callouts connect to the actual changed stages.
    dotted_callout(draw, (1100, 315), (1500, 860))
    dotted_callout(draw, (1590, 315), (1120, 860))
    dotted_callout(draw, (2350, 315), (1880, 1035), RED_DARK,
                   via=[(1950, 315), (1950, 980)])

    note(draw, 55, 910, 610, 180, "specialist：Step4 → Step5", [
        "Step4：一个任务 → 一个 collect()",
        "Step5：Send 为每个 WorkItem 派专家",
        "只收 item + request_id + 前序证据",
        "成功 / 异常都标记完成并回 supervisor",
    ], size=18)
    note(draw, 2200, 900, 520, 190, "Step5 的输出边界", [
        "compose_context 只收本请求 Evidence",
        "source / reference / warning 继续保留",
        "generate 直接写 final_answer",
        "当前没有 review / approval / publish",
    ], size=18)

    # Compact legend in the same visual language as the reference image.
    legend_y = 1150
    draw.text((55, legend_y - 15), "图例", font=font(20, True), fill=INK)
    node_box(draw, 185, legend_y, 125, 45, "沿用", None, GRAY, GRAY_DARK, 17, 8)
    node_box(draw, 360, legend_y, 125, 45, "Step5 改动", None, BLUE, BLUE_DARK, 16, 8)
    node_diamond(draw, 560, legend_y, 70, 45, "判断", None, YELLOW, YELLOW_DARK, 15)
    node_box(draw, 740, legend_y, 125, 45, "异常/降级", None, RED_NOTE, RED_DARK, 16, 8)
    draw.text((W - 55, legend_y - 12), "宽幅总览：主线、互斥分支、动态 fan-out、循环与边界", font=font(18), fill=SUB, anchor="ra")

    output_dir = Path(os.environ.get("OUTDIR", Path(__file__).parent))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "step5-full-overview.png"
    image.save(output)
    print(f"saved {output}")
    print("OK: rendered wide Step5 overview")


if __name__ == "__main__":
    main()
