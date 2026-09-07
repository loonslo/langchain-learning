# -*- coding: utf-8 -*-
"""Render wide source-overview flowcharts for learning Step1, Step2 and Step3.

The renderer reuses the local wide-map drawing primitives used for the existing
Step4 overview, but keeps each earlier step's actual graph contract explicit.
"""

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
    SIGN,
    SUB,
    W,
    YELLOW,
    YELLOW_DARK,
    check_rect,
    cross_grid,
    dotted_callout,
    font,
    label,
    node_box,
    node_diamond,
    node_pill,
    note,
    poly_arrow,
)


STYLES = {
    "reuse": (GRAY, GRAY_DARK),
    "change": (BLUE, BLUE_DARK),
    "decision": (YELLOW, YELLOW_DARK),
    "success": (GREEN, GREEN_DARK),
    "risk": (RED_NOTE, RED_DARK),
}


def draw_node(draw, item: dict) -> None:
    fill, outline = STYLES[item.get("style", "change")]
    shape = item["shape"]
    args = (
        draw,
        item["x"],
        item["y"],
        item["w"],
        item["h"],
        item["title"],
        item.get("sub"),
        fill,
        outline,
        item.get("size", 22),
    )
    if shape == "pill":
        node_pill(
            draw,
            item["x"],
            item["y"],
            item["w"],
            item["h"],
            item["title"],
            fill,
            outline,
            item.get("size", 24),
        )
    elif shape == "diamond":
        node_diamond(*args)
    else:
        node_box(*args, radius=item.get("radius", 12))


def draw_edges(draw, edges: list[dict]) -> None:
    for item in edges:
        poly_arrow(
            draw,
            item["points"],
            color=item.get("color", ORANGE),
            width=item.get("width", 3),
            dashed=item.get("dashed", False),
        )
        if item.get("label"):
            label(
                draw,
                item["label_x"],
                item["label_y"],
                item["label"],
                item.get("label_color", ORANGE_DARK),
                item.get("label_size", 17),
            )


def render(spec: dict, output_dir: Path) -> Path:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    cross_grid(draw)

    draw.text((52, 22), spec["title"], font=font(38, True), fill=INK)
    draw.text((W - 52, 30), "@测试阿甲", font=font(18), fill=SIGN, anchor="ra")

    for item in spec["top_notes"]:
        note(
            draw,
            item["x"],
            item["y"],
            item["w"],
            item["h"],
            item["title"],
            item["lines"],
            fill=item.get("fill", ORANGE_NOTE),
            outline=item.get("outline", ORANGE_NOTE_DARK),
            size=item.get("size", 18),
        )

    for name, item in spec["nodes"].items():
        check_rect(name, item["x"], item["y"], item["w"], item["h"])

    draw_edges(draw, spec["edges"])

    for item in spec["nodes"].values():
        draw_node(draw, item)

    for item in spec.get("callouts", []):
        dotted_callout(
            draw,
            item["start"],
            item["end"],
            item.get("color", (180, 185, 194)),
            via=item.get("via"),
        )

    for item in spec["bottom_notes"]:
        note(
            draw,
            item["x"],
            item["y"],
            item["w"],
            item["h"],
            item["title"],
            item["lines"],
            fill=item.get("fill", ORANGE_NOTE),
            outline=item.get("outline", ORANGE_NOTE_DARK),
            size=item.get("size", 18),
        )

    legend_y = 1150
    draw.text((55, legend_y - 15), "图例", font=font(20, True), fill=INK)
    node_box(draw, 185, legend_y, 125, 45, "沿用", None, GRAY, GRAY_DARK, 17, 8)
    node_box(draw, 360, legend_y, 125, 45, "本步变化", None, BLUE, BLUE_DARK, 16, 8)
    node_diamond(draw, 560, legend_y, 70, 45, "判断", None, YELLOW, YELLOW_DARK, 15)
    node_box(draw, 740, legend_y, 125, 45, "边界/风险", None, RED_NOTE, RED_DARK, 15, 8)
    draw.text(
        (W - 55, legend_y - 12),
        spec["legend"],
        font=font(18),
        fill=SUB,
        anchor="ra",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / spec["filename"]
    image.save(output)
    print(f"saved {output}")
    return output


def edge(points, label_text=None, label_x=0, label_y=0, **kwargs):
    item = {"points": points, **kwargs}
    if label_text:
        item.update({"label": label_text, "label_x": label_x, "label_y": label_y})
    return item


def common_main_nodes(after_title: str, after_sub: str) -> dict:
    return {
        "start": {"shape": "pill", "x": 165, "y": 690, "w": 130, "h": 58,
                   "title": "START", "style": "success", "size": 24},
        "intake": {"shape": "box", "x": 390, "y": 690, "w": 155, "h": 72,
                   "title": "intake", "sub": "输入规范化", "style": "reuse", "size": 24},
        "route": {"shape": "box", "x": 650, "y": 690, "w": 175, "h": 84,
                  "title": "route", "sub": "结构化路由", "style": "change", "size": 24},
        "after": {"shape": "diamond", "x": 930, "y": 690, "w": 230, "h": 140,
                  "title": after_title, "sub": after_sub, "style": "decision", "size": 22},
        "generate": {"shape": "box", "x": 2290, "y": 690, "w": 190, "h": 78,
                      "title": "generate", "sub": "输出回答", "style": "success", "size": 23},
        "end": {"shape": "pill", "x": 2610, "y": 690, "w": 140, "h": 58,
                "title": "END", "style": "success", "size": 24},
    }


def early_exit_nodes(nodes: dict) -> None:
    nodes.update({
        "clarify": {"shape": "box", "x": 1300, "y": 370, "w": 195, "h": 72,
                    "title": "clarify", "sub": "补充信息", "style": "change", "size": 22},
        "out": {"shape": "box", "x": 1700, "y": 460, "w": 210, "h": 72,
                 "title": "out_of_scope", "sub": "范围外", "style": "change", "size": 21},
        "restricted": {"shape": "box", "x": 2080, "y": 550, "w": 230, "h": 72,
                        "title": "restricted_action", "sub": "需要审批", "style": "change", "size": 20},
    })


def early_exit_edges() -> list[dict]:
    return [
        edge([(930, 620), (930, 370), (1202, 370)], "missing_information 非空", 1060, 340),
        edge([(875, 635), (875, 460), (1590, 460)], "in_scope = false", 1110, 430),
        edge([(845, 655), (845, 550), (1965, 550)], "requires_approval = true", 1150, 520),
        edge([(1397, 370), (2450, 370)]),
        edge([(1805, 460), (2450, 460)]),
        edge([(2195, 550), (2450, 550)]),
        {"points": [(2450, 370), (2450, 690)], "width": 3},
        edge([(2450, 690), (2540, 690)]),
    ]


def step1_spec() -> dict:
    nodes = common_main_nodes("choose", "按 RouteDecision 分支")
    early_exit_nodes(nodes)
    nodes.update({
        "specialist": {"shape": "box", "x": 1210, "y": 900, "w": 230, "h": 84,
                       "title": "specialist", "sub": "reliable_lookup", "style": "change", "size": 22},
        "compose": {"shape": "box", "x": 1700, "y": 900, "w": 230, "h": 82,
                    "title": "compose_context", "sub": "Evidence → context", "style": "change", "size": 20},
    })
    edges = [
        edge([(230, 690), (312, 690)], "规范化", 270, 660),
        edge([(468, 690), (562, 690)], "model.route", 520, 660),
        edge([(737, 690), (815, 690)]),
        edge([(1045, 690), (2195, 690)], "sources 为空", 1630, 655),
        edge([(2385, 690), (2540, 690)]),
        *early_exit_edges(),
        edge([(930, 760), (930, 900), (1095, 900)], "sources 含 web", 1010, 830),
        edge([(1325, 900), (1585, 900)]),
        edge([(1700, 859), (1700, 730), (2195, 730)]),
    ]
    return {
        "title": "Step1 完整 Graph 流程图 · 可靠路由、搜索重试与降级",
        "filename": "step1-full-overview.png",
        "legend": "主线：路由后直接回答或进入 web 取证",
        "nodes": nodes,
        "edges": edges,
        "top_notes": [
            {"x": 50, "y": 90, "w": 520, "h": 225, "title": "GraphState：Step1 共享状态", "lines": [
                "question / route / evidence",
                "context / final_answer / errors",
                "Evidence：source / title / content",
                "reference / warning",
                "状态从 intake 一直流到 generate",
            ], "size": 19},
            {"x": 610, "y": 90, "w": 620, "h": 225, "title": "结构化路由边界", "lines": [
                "model.route(question, context) → RouteDecision",
                "choose 按固定顺序检查：范围、审批、缺信息",
                "sources 含 web → specialist",
                "否则 → generate",
                "不是用字符串猜测分支",
            ], "size": 18},
            {"x": 1270, "y": 90, "w": 610, "h": 225, "title": "Step1 的真实执行路径", "lines": [
                "web 分支才调用 evidence_adapter.collect()",
                "specialist → compose_context → generate",
                "无 web 来源时直接走 generate",
                "clarify / out_of_scope / restricted_action 直接结束",
            ], "size": 18},
            {"x": 1920, "y": 90, "w": 830, "h": 225, "title": "重试与降级边界", "lines": [
                "route / generate：RetryPolicy(max_attempts=3)",
                "reliable_lookup：瞬时错误最多 3 次，逐次退避",
                "PermanentToolError：直接抛出，不伪装成成功",
                "重试耗尽：返回 unavailable://web + warning=degraded",
                "errors 保留失败记录，流程仍可生成说明",
            ], "fill": RED_NOTE, "outline": RED_DARK, "size": 18},
        ],
        "bottom_notes": [
            {"x": 55, "y": 925, "w": 700, "h": 165, "title": "specialist：Step1 的取证节点", "lines": [
                "reliable_lookup(adapter, question, max_attempts=3)",
                "成功 → evidence；瞬时失败 → errors + 重试",
                "耗尽 → 单条不可用占位证据，不让 context 为空",
            ], "size": 18},
            {"x": 2050, "y": 925, "w": 700, "h": 165, "title": "generate 的输入边界", "lines": [
                "compose_context 统一拼接 [i] content + 来源",
                "generate 只消费 question 与 context",
                "不负责决定来源，也不执行外部 I/O",
            ], "size": 18},
        ],
        "callouts": [
            {"start": (1270, 315), "end": (650, 640)},
            {"start": (2250, 315), "end": (1210, 855), "color": RED_DARK,
             "via": [(1900, 315), (1900, 820)]},
        ],
    }


def step2_spec() -> dict:
    nodes = common_main_nodes("after_route", "decision.sources?")
    early_exit_nodes(nodes)
    nodes.update({
        "plan": {"shape": "box", "x": 1120, "y": 900, "w": 185, "h": 78,
                 "title": "plan", "sub": "WorkItem[]", "style": "change", "size": 23},
        "supervisor": {"shape": "box", "x": 1450, "y": 900, "w": 190, "h": 78,
                       "title": "supervisor", "sub": "pending cursor", "style": "change", "size": 22},
        "dispatch": {"shape": "diamond", "x": 1770, "y": 900, "w": 220, "h": 130,
                     "title": "dispatch", "sub": "还有未完成任务?", "style": "decision", "size": 22},
        "specialist": {"shape": "box", "x": 1770, "y": 1080, "w": 220, "h": 82,
                       "title": "specialist", "sub": "一次执行一个 WorkItem", "style": "change", "size": 20},
        "compose": {"shape": "box", "x": 2070, "y": 900, "w": 220, "h": 82,
                    "title": "compose_context", "sub": "join evidence", "style": "change", "size": 20},
    })
    edges = [
        edge([(230, 690), (312, 690)], "规范化", 270, 660),
        edge([(468, 690), (562, 690)], "model.route", 520, 660),
        edge([(737, 690), (815, 690)]),
        edge([(1045, 690), (2195, 690)], "sources 为空", 1630, 655),
        edge([(2385, 690), (2540, 690)]),
        *early_exit_edges(),
        edge([(930, 760), (930, 900), (1027, 900)], "存在 source", 970, 830),
        edge([(1212, 900), (1355, 900)]),
        edge([(1545, 900), (1660, 900)]),
        edge([(1880, 900), (1960, 900)], "否：完成", 1920, 865),
        edge([(1770, 965), (1770, 1039)], "是", 1825, 1005),
        edge([(1660, 1080), (1370, 1080), (1370, 940), (1450, 940)],
             "回边：completed_items 累积", 1510, 1020),
        edge([(2070, 859), (2070, 730), (2195, 730)]),
    ]
    return {
        "title": "Step2 完整 Graph 流程图 · 计划、游标调度与可观测循环",
        "filename": "step2-full-overview.png",
        "legend": "主线：route 后决定直接回答，或进入 plan → supervisor 循环",
        "nodes": nodes,
        "edges": edges,
        "top_notes": [
            {"x": 50, "y": 90, "w": 520, "h": 225, "title": "GraphState：Step2 共享状态", "lines": [
                "question / route / work_items",
                "completed_items / evidence",
                "context / final_answer",
                "trace：节点、耗时、任务计数",
                "列表字段通过 reducer 持续累积",
            ], "size": 19},
            {"x": 610, "y": 90, "w": 640, "h": 225, "title": "plan：从路由到可执行任务", "lines": [
                "model.plan(RouteDecision) → WorkItem[]",
                "每个任务带 id / source / objective",
                "plan 后先进入 supervisor",
                "supervisor 计算 pending，再交给 dispatch",
                "一次只取一个未完成任务",
            ], "size": 18},
            {"x": 1310, "y": 90, "w": 560, "h": 225, "title": "dispatch：显式游标循环", "lines": [
                "有 pending → specialist",
                "specialist 完成一个任务 → supervisor",
                "无 pending → compose_context",
                "completed_items 是循环进度",
            ], "size": 18},
            {"x": 1930, "y": 90, "w": 820, "h": 225, "title": "可观测性边界", "lines": [
                "每个关键节点记录 trace：node / duration_ms / count",
                "specialist 用 llm.invoke() 生成待取证说明",
                "随后写入 step02://task-id 的合成 Evidence",
                "run() 可 stream updates / values / messages / debug",
                "默认落盘 reports/day31_40_step02.jsonl",
            ], "fill": RED_NOTE, "outline": RED_DARK, "size": 18},
        ],
        "bottom_notes": [
            {"x": 55, "y": 925, "w": 700, "h": 165, "title": "specialist：Step2 的任务执行", "lines": [
                "找到第一个未完成 WorkItem",
                "llm.invoke() 只说明要查什么，不声称真实检索",
                "完成后返回 completed_items + evidence + trace",
            ], "size": 18},
            {"x": 2180, "y": 925, "w": 570, "h": 165, "title": "compose_context → generate", "lines": [
                "所有任务完成后统一拼接 evidence",
                "generate 调 model.generate(question, context)",
                "循环结束，回到主线并输出 final_answer",
            ], "size": 18},
        ],
        "callouts": [
            {"start": (1310, 315), "end": (1120, 855)},
            {"start": (1930, 315), "end": (1770, 1035), "color": RED_DARK,
             "via": [(1980, 315), (1980, 820)]},
        ],
    }


def step3_spec() -> dict:
    nodes = {
        "start": {"shape": "pill", "x": 145, "y": 690, "w": 130, "h": 58,
                   "title": "START", "style": "success", "size": 24},
        "manage": {"shape": "box", "x": 430, "y": 690, "w": 215, "h": 84,
                   "title": "manage_context", "sub": "摘要 + 最近4轮", "style": "change", "size": 20},
        "generate": {"shape": "box", "x": 760, "y": 690, "w": 190, "h": 78,
                      "title": "generate", "sub": "draft + status", "style": "change", "size": 22},
        "approval": {"shape": "box", "x": 1060, "y": 690, "w": 220, "h": 100,
                     "title": "approval", "sub": "节点内部判断", "style": "decision", "size": 22},
        "publish": {"shape": "box", "x": 2360, "y": 690, "w": 210, "h": 78,
                    "title": "publish", "sub": "保存确认后的报告", "style": "success", "size": 21},
        "end": {"shape": "pill", "x": 2670, "y": 690, "w": 130, "h": 58,
                "title": "END", "style": "success", "size": 24},
        "interrupt": {"shape": "box", "x": 1210, "y": 900, "w": 190, "h": 78,
                       "title": "interrupt()", "sub": "提交 draft + ask", "style": "change", "size": 21},
        "paused": {"shape": "box", "x": 1450, "y": 900, "w": 190, "h": 78,
                   "title": "__interrupt__", "sub": "第一次 invoke 返回", "style": "risk", "size": 19},
        "resume": {"shape": "box", "x": 1690, "y": 900, "w": 200, "h": 78,
                   "title": "Command(resume)", "sub": "同一 thread_id", "style": "change", "size": 19},
        "decision": {"shape": "diamond", "x": 1990, "y": 900, "w": 200, "h": 130,
                     "title": "approve?", "sub": "approve / reject", "style": "decision", "size": 22},
    }
    edges = [
        edge([(210, 690), (322, 690)], "开始新一轮", 265, 660),
        edge([(537, 690), (665, 690)], "窗口管理", 600, 660),
        edge([(855, 690), (950, 690)], "draft", 905, 655),
        edge([(1170, 690), (2255, 690)], "not_required / approval 返回", 1690, 655),
        edge([(2465, 690), (2605, 690)]),
        edge([(1060, 740), (1060, 900), (1115, 900)], "requires_approval", 1100, 830),
        edge([(1305, 900), (1355, 900)]),
        edge([(1545, 900), (1590, 900)]),
        edge([(1790, 900), (1890, 900)]),
        edge([(1990, 835), (1990, 790), (2180, 790), (2180, 730), (2255, 730)],
             "approve", 2125, 760),
        edge([(1990, 965), (1990, 1000), (2180, 1000), (2180, 730), (2255, 730)],
             "reject", 2125, 1030),
    ]
    return {
        "title": "Step3 完整 Graph 流程图 · 多轮上下文、Checkpoint 与人工确认",
        "filename": "step3-full-overview.png",
        "legend": "实线是 Graph 主线；下方展开 approval 节点内部的暂停/恢复",
        "nodes": nodes,
        "edges": edges,
        "top_notes": [
            {"x": 50, "y": 90, "w": 560, "h": 225, "title": "GraphState：Step3 共享状态", "lines": [
                "question / conversation_history",
                "history_summary / history_summarized_count",
                "recent_history / draft",
                "requires_approval / approval_status",
                "final_answer",
            ], "size": 18},
            {"x": 650, "y": 90, "w": 650, "h": 225, "title": "manage_context：控制模型视图", "lines": [
                "完整 conversation_history 用于审计，不直接进 Prompt",
                "已滑出最近 4 轮的旧记录才进入摘要",
                "history_summary + recent_history 控制 Token 和噪声",
                "generate 只读取摘要、最近对话和当前任务",
            ], "size": 18},
            {"x": 1340, "y": 90, "w": 590, "h": 225, "title": "Checkpoint：可恢复状态边界", "lines": [
                "run() 生成 thread_id 并放入 config",
                "InMemorySaver / SqliteSaver 保存中断时状态",
                "没有 checkpointer，第二次 invoke 无处恢复",
                "进程退出后仍可按持久化方案恢复",
            ], "fill": RED_NOTE, "outline": RED_DARK, "size": 18},
            {"x": 1970, "y": 90, "w": 780, "h": 225, "title": "HITL：人工确认而非自动执行", "lines": [
                "approval_status：not_required / pending / approved / rejected",
                "interrupt payload 只包含 draft 和确认问题",
                "approve / reject 都不会自动下单、贷款或付款",
                "publish 只保存最终报告，并写入完整历史",
            ], "fill": RED_NOTE, "outline": RED_DARK, "size": 18},
        ],
        "bottom_notes": [
            {"x": 55, "y": 925, "w": 760, "h": 165, "title": "审批分支是 approval 节点内部逻辑", "lines": [
                "requires_approval=false：approval 返回 {}，直接进入 publish",
                "requires_approval=true：interrupt() 让第一次 invoke 正常返回",
                "第二次 invoke 以 Command(resume=decision) 从断点继续",
            ], "size": 18},
            {"x": 2180, "y": 980, "w": 570, "h": 110, "title": "publish 的安全边界", "lines": [
                "reject → 未发布提示；approve → 保存 draft",
                "两者都追加 conversation_history",
            ], "size": 18},
        ],
        "callouts": [
            {"start": (1630, 315), "end": (1450, 855), "color": RED_DARK,
             "via": [(1630, 340), (1450, 780)]},
            {"start": (2350, 315), "end": (2360, 650)},
        ],
    }


def main() -> None:
    output_dir = Path(__file__).parent
    specs = [step1_spec(), step2_spec(), step3_spec()]
    for spec in specs:
        render(spec, output_dir)
    print("OK: rendered Step1, Step2 and Step3 wide overviews")


if __name__ == "__main__":
    main()
