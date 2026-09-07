# -*- coding: utf-8 -*-
"""Render a wide node-by-node comparison of Step2, Step3 and Step4."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STEP4_RENDERER = ROOT / "自媒体" / "output" / "ai-transition-diary" / "day38"
sys.path.insert(0, str(STEP4_RENDERER))

from PIL import Image, ImageDraw  # noqa: E402

from render_day38_full_overview import (  # noqa: E402
    BG,
    BLUE,
    BLUE_DARK,
    GRAY,
    GRAY_DARK,
    GREEN,
    GREEN_DARK,
    H,
    INK,
    ORANGE,
    ORANGE_DARK,
    ORANGE_NOTE,
    ORANGE_NOTE_DARK,
    RED_DARK,
    RED_NOTE,
    SUB,
    W,
    YELLOW,
    YELLOW_DARK,
    cross_grid,
    font,
    note,
    rounded,
    wrap,
)


OUT_H = 2100
TABLE_X = 42
TABLE_Y = 365
HEADER_H = 68
ROW_H = 100
COLS = [
    (42, 270, "节点 / 函数"),
    (270, 865, "Step2：计划与可观测循环"),
    (865, 1500, "Step3：多轮上下文与人工确认"),
    (1500, 2265, "Step4：真实证据与安全取证"),
    (2265, 2758, "Step2 → Step4 的变化"),
]


ROWS = [
    {
        "node": "intake",
        "step2": "规范化 question；空问题抛 ValueError。",
        "step3": "无 intake 节点；图从 manage_context 开始。",
        "step4": "沿用 Step2：规范化 question；空问题抛 ValueError。",
        "change": "Step4 沿用。",
        "style": "reuse",
    },
    {
        "node": "manage_context",
        "step2": "无。",
        "step3": "完整历史用于审计；旧记录摘要；模型只看摘要 + 最近 4 轮。",
        "step4": "无。",
        "change": "Step3 专属能力。",
        "style": "change",
    },
    {
        "node": "route",
        "step2": "model.route() → RouteDecision → 保存 route 字典。",
        "step3": "无。",
        "step4": "仍用 RouteDecision；仅保留 web/sql；拦截未开放来源并写 errors + trace。",
        "change": "增加来源白名单、拦截留痕、耗时 trace。",
        "style": "change",
    },
    {
        "node": "after_route*",
        "step2": "按范围、审批、缺信息、sources 分支；有 sources → plan。",
        "step3": "无。",
        "step4": "分支顺序和拓扑沿用 Step2。",
        "change": "路由逻辑基本不变。",
        "style": "reuse",
    },
    {
        "node": "clarify",
        "step2": "计划前提示补充缺失信息。",
        "step3": "无。",
        "step4": "真实取证前提示补充缺失信息。",
        "change": "逻辑沿用，文案对应真实取证。",
        "style": "reuse",
    },
    {
        "node": "out_of_scope",
        "step2": "只负责编排家庭购车比较任务。",
        "step3": "无。",
        "step4": "只处理家庭购车公开资料与已录入数据。",
        "change": "范围边界更具体。",
        "style": "reuse",
    },
    {
        "node": "restricted_action",
        "step2": "只能制定比较计划；不能下单、贷款、付款。",
        "step3": "无。",
        "step4": "只能查询资料；不能下单、贷款、付款。",
        "change": "从“计划限制”变为“取证限制”。",
        "style": "reuse",
    },
    {
        "node": "plan",
        "step2": "model.plan() → list[WorkItem] → 保存 work_items 字典列表。",
        "step3": "无。",
        "step4": "过滤不支持来源；空计划创建 WorkItem 兜底；重排 parallel_group；记录任务数。",
        "change": "增加来源过滤、空计划兜底、任务组规范化。",
        "style": "change",
    },
    {
        "node": "supervisor",
        "step2": "比较 completed_items 与 work_items，只记录 pending 数量。",
        "step3": "无。",
        "step4": "增加 supervisor_steps；记录耗时；超过 10 轮触发预算护栏。",
        "change": "从 pending 观察器升级为带预算的循环控制点。",
        "style": "change",
    },
    {
        "node": "dispatch",
        "step2": "有未完成任务 → specialist；否则 → compose_context。",
        "step3": "无。",
        "step4": "先判断 supervisor_steps > 10；超限直接 compose_context；否则沿用 Step2。",
        "change": "增加循环超限出口。",
        "style": "change",
    },
    {
        "node": "specialist",
        "step2": "llm.invoke() 生成“待查询说明”；写入 step02://id 合成 Evidence。",
        "step3": "无。",
        "step4": "adapters[source].collect()；真实 Web/SQL Evidence；降级写 warning，异常写 errors。",
        "change": "从模型模拟执行升级为真实数据源执行。",
        "style": "change",
    },
    {
        "node": "compose_context",
        "step2": "只拼接 [i] content。",
        "step3": "无。",
        "step4": "拼接 source/title/content/reference，并保留 warning；记录汇聚数量。",
        "change": "增加来源可追溯和降级标记。",
        "style": "change",
    },
    {
        "node": "generate",
        "step2": "model.generate(question, context)；不记录生成 trace。",
        "step3": "根据 history_summary、recent_history、question 生成 draft，并设置 approval_status。",
        "step4": "model.generate(question, context)；增加生成耗时和字符数 trace。",
        "change": "Step4 沿用回答接口，输入变成真实证据上下文。",
        "style": "change",
    },
    {
        "node": "approval",
        "step2": "无。",
        "step3": "需要审批时 interrupt()；第一次 invoke 返回中断，第二次 resume 恢复。",
        "step4": "无。",
        "change": "Step3 专属 HITL 节点。",
        "style": "change",
    },
    {
        "node": "publish",
        "step2": "无独立发布节点；generate 后直接 END。",
        "step3": "approve 保存 draft；reject 返回未发布提示；追加 conversation_history。",
        "step4": "无独立发布节点；generate 后直接 END。",
        "change": "Step3 专属确认与历史写入口。",
        "style": "change",
    },
]


def text_block(draw, x, y, w, h, text, size=17, fill=INK, bold=False, padding=14):
    fnt = font(size, bold)
    lines = wrap(draw, text, fnt, w - padding * 2)
    ascent, descent = fnt.getmetrics()
    lh = int((ascent + descent) * 1.22)
    total = len(lines) * lh
    cursor = y + max(padding, (h - total) / 2)
    for line in lines:
        draw.text((x + padding, cursor), line, font=fnt, fill=fill)
        cursor += lh


def render() -> Path:
    image = Image.new("RGB", (W, OUT_H), BG)
    draw = ImageDraw.Draw(image)
    cross_grid(draw)

    draw.text((52, 22), "Step2 → Step4 全节点对比图 · 含 Step3 能力切片", font=font(38, True), fill=INK)
    draw.text((W - 52, 30), "@测试阿甲", font=font(18), fill=(164, 170, 182), anchor="ra")

    note(draw, 50, 90, 620, 225, "Step2：基准骨架", [
        "核心是 plan → supervisor → dispatch → specialist 回环",
        "specialist 用 LLM 产出待取证说明，不接真实 Web/SQL",
        "Evidence 先作为 step02://id 的合成结果",
    ], size=18)
    note(draw, 700, 90, 620, 225, "Step3：另一条能力切片", [
        "不沿用 Step2 的 route/plan/supervisor 主线",
        "新增 manage_context、approval、publish",
        "重点是历史摘要、checkpoint、interrupt/resume",
    ], size=18)
    note(draw, 1350, 90, 640, 225, "Step4：在 Step2 骨架上增强", [
        "route/plan/supervisor/dispatch 的骨架仍在",
        "specialist 改为真实 Web/SQL Adapter 执行",
        "errors、warning、reference、trace 和预算护栏进入主流程",
    ], fill=RED_NOTE, outline=RED_DARK, size=18)
    note(draw, 2020, 90, 730, 225, "阅读这张表的方式", [
        "同名节点：对照 Step2 与 Step4 的行为变化",
        "Step3 专属节点：Step2/Step4 标为“无”",
        "GraphState、Adapter 和 run() 属于节点外的横切变化",
    ], size=18)

    # Header.
    draw.rectangle((TABLE_X, TABLE_Y, 2758, TABLE_Y + HEADER_H), fill=(224, 232, 244), outline=BLUE_DARK, width=2)
    for x0, x1, title in COLS:
        draw.line((x0, TABLE_Y, x0, TABLE_Y + HEADER_H + len(ROWS) * ROW_H), fill=(180, 190, 205), width=2)
        text_block(draw, x0, TABLE_Y, x1 - x0, HEADER_H, title, size=19, bold=True)
    draw.line((2758, TABLE_Y, 2758, TABLE_Y + HEADER_H + len(ROWS) * ROW_H), fill=(180, 190, 205), width=2)

    for index, row in enumerate(ROWS):
        y = TABLE_Y + HEADER_H + index * ROW_H
        fill = (249, 251, 254) if index % 2 == 0 else (242, 246, 251)
        draw.rectangle((TABLE_X, y, 2758, y + ROW_H), fill=fill)
        draw.line((TABLE_X, y, 2758, y), fill=(206, 212, 221), width=1)

        style = row["style"]
        if style == "change":
            node_fill, node_outline = BLUE, BLUE_DARK
        else:
            node_fill, node_outline = GRAY, GRAY_DARK
        rounded(draw, (55, y + 17, 255, y + ROW_H - 17), node_fill, node_outline, radius=8, width=2)
        text_block(draw, 55, y + 17, 200, ROW_H - 34, row["node"], size=19, bold=True)

        text_block(draw, 270, y, 595, ROW_H, row["step2"], size=16)
        text_block(draw, 865, y, 635, ROW_H, row["step3"], size=16)
        text_block(draw, 1500, y, 765, ROW_H, row["step4"], size=16)
        change_fill = (255, 240, 240) if style == "change" else (255, 248, 229)
        draw.rectangle((2265, y, 2758, y + ROW_H), fill=change_fill)
        text_block(draw, 2265, y, 493, ROW_H, row["change"], size=16, fill=INK)

    bottom_y = TABLE_Y + HEADER_H + len(ROWS) * ROW_H + 34
    draw.text((55, bottom_y), "跨节点变化", font=font(20, True), fill=INK)
    draw.text((260, bottom_y), "Step4 保留 Step2 的 Graph 拓扑，真正新增的是数据源执行、证据可追溯、失败处理和循环预算；Step3 的持久化/HITL 不会自动出现在 Step4。", font=font(18), fill=SUB)
    draw.text((W - 55, bottom_y + 48), "Graph 节点：Step2 10 个 · Step3 4 个 · Step4 10 个；* after_route 是条件路由函数", font=font(18), fill=SUB, anchor="ra")

    output = Path(__file__).parent / "step2-to-step4-all-nodes-comparison.png"
    image.save(output)
    print(f"saved {output}")
    return output


if __name__ == "__main__":
    render()
