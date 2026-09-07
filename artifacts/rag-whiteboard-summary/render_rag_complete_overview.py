# -*- coding: utf-8 -*-
"""Render a single wide overview that consolidates the three RAG whiteboards."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
RENDERER_DIR = ROOT / "自媒体" / "output" / "ai-transition-diary" / "day38"
sys.path.insert(0, str(RENDERER_DIR))

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
    "input": (GRAY, GRAY_DARK),
    "process": (BLUE, BLUE_DARK),
    "merge": (YELLOW, YELLOW_DARK),
    "success": (GREEN, GREEN_DARK),
}


def draw_node(draw: ImageDraw.ImageDraw, item: dict) -> None:
    fill, outline = STYLES[item["style"]]
    if item["shape"] == "pill":
        node_pill(
            draw,
            item["x"],
            item["y"],
            item["w"],
            item["h"],
            item["title"],
            fill,
            outline,
            item.get("size", 20),
        )
    elif item["shape"] == "diamond":
        node_diamond(
            draw,
            item["x"],
            item["y"],
            item["w"],
            item["h"],
            item["title"],
            item.get("sub"),
            fill,
            outline,
            item.get("size", 18),
        )
    else:
        node_box(
            draw,
            item["x"],
            item["y"],
            item["w"],
            item["h"],
            item["title"],
            item.get("sub"),
            fill,
            outline,
            item.get("size", 18),
            item.get("radius", 12),
        )


def edge(draw, points, text=None, lx=0, ly=0, color=ORANGE, dashed=False):
    poly_arrow(draw, points, color=color, width=3, dashed=dashed)
    if text:
        label(draw, lx, ly, text, ORANGE_DARK, 16)


def assert_node_text(draw: ImageDraw.ImageDraw, name: str, item: dict) -> None:
    title_font = font(item.get("size", 18), True)
    title_width = draw.textbbox((0, 0), item["title"], font=title_font)[2]
    if title_width > item["w"] - 20:
        raise ValueError(f"title too wide for {name}: {item['title']}")
    if item.get("sub"):
        sub_font = font(max(14, item.get("size", 18) - 4))
        sub_width = draw.textbbox((0, 0), item["sub"], font=sub_font)[2]
        if sub_width > item["w"] - 18:
            raise ValueError(f"subtitle too wide for {name}: {item['sub']}")


def render(output: Path) -> None:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    cross_grid(draw)

    draw.text(
        (52, 22),
        "RAG 完整横版流程图 · 建库、查询优化、增强生成与会话记忆",
        font=font(36, True),
        fill=INK,
    )
    draw.text((W - 52, 30), "@测试阿甲", font=font(18), fill=SIGN, anchor="ra")

    top_notes = [
        {
            "x": 50,
            "y": 88,
            "w": 610,
            "h": 215,
            "title": "三张白板分别在讲什么",
            "lines": [
                "图一：基础 RAG 串联 + Prompt / LLM / Parser + 会话记忆",
                "图二：离线建库——Load / Split / Embedding / Storage",
                "图三：查询改写、混合召回、融合、重排与生产扩展",
                "总图把它们合成“离线准备 + 在线问答”两条真实流程",
            ],
        },
        {
            "x": 690,
            "y": 88,
            "w": 590,
            "h": 215,
            "title": "查询优化与检索",
            "lines": [
                "改写可选：指代消解 / Multi-Query / Decomposition",
                "HyDE / Step-back 也是可选策略，不是同时全跑",
                "并行召回：向量检索 + BM25 关键词检索",
                "融合用 EnsembleRetriever 或 RRF，再由 reranker 精排",
            ],
        },
        {
            "x": 1310,
            "y": 88,
            "w": 650,
            "h": 215,
            "title": "Augmented（增强）的准确位置",
            "lines": [
                "Top-K 子块可通过 parent_map[child_id] 回到父块",
                "format_docs：Document 列表 → context 文本",
                "LCEL 同时准备 context 与原问题 question",
                "增强完成于 context / question / history 被注入 Prompt",
            ],
        },
        {
            "x": 1990,
            "y": 88,
            "w": 760,
            "h": 215,
            "title": "生成、记忆与边界",
            "lines": [
                "主线：ChatPromptTemplate → ChatOpenAI → Parser",
                "RunnableWithMessageHistory 外包主链：调用前读，结束后写",
                "工具调用与 Pydantic 结构化输出是可选扩展分支",
                "Prompt 可降低幻觉；来源引用、评测与拒答仍需单独验证",
            ],
            "fill": RED_NOTE,
            "outline": RED_DARK,
        },
    ]
    for item in top_notes:
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
            size=17,
        )

    nodes = {
        "source": {"shape": "pill", "x": 130, "y": 480, "w": 150, "h": 56, "title": "资料变更", "style": "success", "size": 19},
        "load": {"shape": "box", "x": 350, "y": 480, "w": 175, "h": 74, "title": "Load", "sub": "PDF / CSV / MD", "style": "process", "size": 19},
        "document": {"shape": "box", "x": 585, "y": 480, "w": 185, "h": 74, "title": "Document", "sub": "text + metadata", "style": "process", "size": 18},
        "split": {"shape": "box", "x": 830, "y": 480, "w": 190, "h": 78, "title": "Split", "sub": "子块 + 父块映射", "style": "process", "size": 18},
        "embed": {"shape": "box", "x": 1090, "y": 420, "w": 185, "h": 74, "title": "Embedding", "sub": "文档块 → 向量", "style": "process", "size": 18},
        "vector": {"shape": "box", "x": 1340, "y": 420, "w": 190, "h": 74, "title": "Vector Store", "sub": "FAISS / Chroma", "style": "process", "size": 18},
        "bm25": {"shape": "box", "x": 1340, "y": 555, "w": 190, "h": 72, "title": "BM25 Index", "sub": "关键词索引", "style": "process", "size": 18},
        "ready": {"shape": "pill", "x": 1600, "y": 485, "w": 180, "h": 58, "title": "双路索引就绪", "style": "success", "size": 18},
        "user": {"shape": "pill", "x": 110, "y": 760, "w": 150, "h": 56, "title": "用户问题", "style": "input", "size": 19},
        "rewrite": {"shape": "box", "x": 340, "y": 760, "w": 190, "h": 78, "title": "Query Rewrite", "sub": "按问题选一种策略", "style": "process", "size": 17},
        "retrieve": {"shape": "box", "x": 590, "y": 760, "w": 190, "h": 78, "title": "并行召回", "sub": "Vector + BM25", "style": "process", "size": 18},
        "fusion": {"shape": "box", "x": 835, "y": 760, "w": 185, "h": 78, "title": "融合", "sub": "Ensemble / RRF", "style": "process", "size": 19},
        "rerank": {"shape": "box", "x": 1070, "y": 760, "w": 175, "h": 78, "title": "Rerank", "sub": "cross-encoder", "style": "process", "size": 19},
        "topk": {"shape": "box", "x": 1305, "y": 760, "w": 190, "h": 78, "title": "Top-K 父块", "sub": "parent_map[child_id]", "style": "process", "size": 18},
        "augment": {"shape": "diamond", "x": 1565, "y": 760, "w": 210, "h": 130, "title": "Augment", "sub": "context + question", "style": "merge", "size": 18},
        "prompt": {"shape": "box", "x": 1825, "y": 760, "w": 190, "h": 78, "title": "Prompt", "sub": "历史 + 上下文 + 问题", "style": "process", "size": 19},
        "llm": {"shape": "box", "x": 2070, "y": 760, "w": 175, "h": 78, "title": "LLM", "sub": "可选 tools 回环", "style": "process", "size": 19},
        "parser": {"shape": "box", "x": 2295, "y": 760, "w": 175, "h": 78, "title": "Parser", "sub": "文本 / 结构化", "style": "process", "size": 19},
        "answer": {"shape": "pill", "x": 2535, "y": 760, "w": 165, "h": 58, "title": "最终回答", "style": "success", "size": 19},
        "session": {"shape": "pill", "x": 1050, "y": 900, "w": 145, "h": 50, "title": "session_id", "style": "input", "size": 17},
        "history": {"shape": "box", "x": 1325, "y": 900, "w": 290, "h": 64, "title": "RunnableWithMessageHistory", "sub": "调用前读 / 结束后写", "style": "process", "size": 16},
    }

    for name, item in nodes.items():
        check_rect(name, item["x"], item["y"], item["w"], item["h"])
        assert_node_text(draw, name, item)

    # Offline indexing lane.
    edge(draw, [(205, 480), (262, 480)])
    edge(draw, [(437, 480), (492, 480)])
    edge(draw, [(677, 480), (735, 480)])
    edge(draw, [(925, 465), (998, 420)])
    edge(draw, [(1182, 420), (1245, 420)])
    edge(draw, [(925, 500), (1080, 555), (1245, 555)])
    edge(draw, [(1435, 420), (1510, 455), (1510, 475)])
    edge(draw, [(1435, 555), (1510, 520), (1510, 495)])

    # Online request lane.
    online_order = ["user", "rewrite", "retrieve", "fusion", "rerank", "topk", "augment", "prompt", "llm", "parser", "answer"]
    for left, right in zip(online_order, online_order[1:]):
        a, b = nodes[left], nodes[right]
        edge(draw, [(a["x"] + a["w"] / 2, a["y"]), (b["x"] - b["w"] / 2, b["y"])])

    # Reuse the prepared indexes during retrieval.
    edge(
        draw,
        [(1600, 514), (1600, 620), (590, 620), (590, 720)],
        "复用索引",
        1095,
        592,
    )

    # Session history: wrapper reads before Prompt, then writes the new turn.
    edge(draw, [(1122, 900), (1202, 900)], color=(160, 165, 174), dashed=True)
    dotted_callout(draw, (1447, 882), (1825, 720), (160, 165, 174), via=[(1660, 882), (1660, 835)])
    dotted_callout(draw, (2535, 790), (1447, 918), (160, 165, 174), via=[(2535, 900), (1500, 900)])
    label(draw, 1730, 870, "注入 history", (120, 126, 138), 15)
    label(draw, 2210, 910, "保存 user + AI 新一轮", (120, 126, 138), 15)

    for item in nodes.values():
        draw_node(draw, item)

    bottom_notes = [
        {
            "x": 55,
            "y": 965,
            "w": 790,
            "h": 125,
            "title": "离线建库的真实触发",
            "lines": [
                "资料、切块规则、Embedding 模型或索引结构变化时重建",
                "同一套 Embedding 必须同时用于文档块和在线问题",
            ],
        },
        {
            "x": 1955,
            "y": 965,
            "w": 795,
            "h": 125,
            "title": "在线问答的真实出口",
            "lines": [
                "主线返回文本或结构化结果；工具调用只在模型请求时回环",
                "回答完成后，RunnableWithMessageHistory 保存本轮对话",
            ],
        },
    ]
    for item in bottom_notes:
        note(
            draw,
            item["x"],
            item["y"],
            item["w"],
            item["h"],
            item["title"],
            item["lines"],
            fill=ORANGE_NOTE,
            outline=ORANGE_NOTE_DARK,
            size=17,
        )

    legend_y = 1150
    draw.text((55, legend_y - 15), "图例", font=font(20, True), fill=INK)
    node_box(draw, 190, legend_y, 135, 45, "输入/沿用", None, GRAY, GRAY_DARK, 16, 8)
    node_box(draw, 385, legend_y, 135, 45, "处理步骤", None, BLUE, BLUE_DARK, 16, 8)
    node_diamond(draw, 585, legend_y, 80, 48, "汇合", None, YELLOW, YELLOW_DARK, 15)
    node_pill(draw, 770, legend_y, 135, 45, "入口/出口", GREEN, GREEN_DARK, 16)
    draw.text(
        (W - 55, legend_y - 12),
        "上排：资料变化时建库；下排：每次用户提问；虚线：会话记忆读写",
        font=font(18),
        fill=SUB,
        anchor="ra",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"saved {output}")


if __name__ == "__main__":
    render(Path(__file__).parent / "rag-complete-overview.png")
