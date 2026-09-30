#!/usr/bin/env python3
"""构建教程 HTML。

用法：python build.py
产出：out/tutorial.html 与 out/toc.json（供 render.py 定位章节页码）

工作顺序（见 生产流水线.md）：定原型 → 建内容表 → 写正文 → 做图 → 渲染自检。
本文件负责「组装」：把 content/ 下各章产出的 HTML 拼成一份完整文档。
"""
import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
OUT = os.path.join(HERE, "out")
sys.path.insert(0, CONTENT)

import comp  # noqa: E402
from comp import toc_row  # noqa: E402

# 章节顺序：key -> 模块名
ORDER = [
    ("1", "m01"),
    ("2", "m02"),
    ("3", "m03"),
    ("4", "m04"),
    ("5", "m05"),
    ("6", "m06"),
    ("7", "m07"),
    ("8", "m08"),
    ("9", "m09"),
    ("10", "m10"),
    ("11", "m11"),
]

# 目录条目：页码由 render.py 回填。
# ⚠️ 每个 toc_row 必须写在一行内——跨行会让回填正则匹配不到，页码静默停在初始值。
TOC_ROWS = [
    toc_row("序章", "序章　为什么从零开始也能走通", 2),
    toc_row("1", "第 1 章　让程序先会说话：模型调用基础", 10),
    toc_row("2", "第 2 章　让它有据可依：RAG 检索增强", 17),
    toc_row("3", "第 3 章　把「感觉不错」变成数据：评测与质量门", 28),
    toc_row("4", "第 4 章　让它自己干活：Agent 与 LangGraph", 38),
    toc_row("5", "第 5 章　做成能上线的服务：工程化与模型认知", 50),
    toc_row("6", "第 6 章　做一个真产品：企业客服与工单 Copilot", 61),
    toc_row("7", "第 7 章　把测试变成护城河：AI 自动化测试专项", 69),
    toc_row("8", "第 8 章　把对话变成业务契约", 77),
    toc_row("9", "第 9 章　接入企业数据与本地模型", 82),
    toc_row("10", "第 10 章　让 Agent 之间协作：MCP 与 A2A", 90),
    toc_row("11", "第 11 章　工具箱：怎么判断一个 AI 项目靠不靠谱", 96),
]

TOC_KEYS = ["序章", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]

ANCHOR_PAT = {
    "序章": r"^\s*序章\s*$",
}


def pangu(html):
    """中英文之间加空格（跑在最终行内 HTML 上，跳过 pre/code 与标签）。"""
    parts = re.split(r"(<pre[\s\S]*?</pre>|<code[\s\S]*?</code>|<[^>]+>)", html)
    out = []
    for seg in parts:
        if seg.startswith("<"):
            out.append(seg)
            continue
        s = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9@#$%])", r"\1 \2", seg)
        s = re.sub(r"([A-Za-z0-9@#$%])([\u4e00-\u9fff])", r"\1 \2", s)
        out.append(s)
    return "".join(out)


def load(mod):
    try:
        m = importlib.import_module(mod)
        importlib.reload(m)
        return m
    except ModuleNotFoundError:
        print(f"  · 跳过缺失模块 {mod}")
        return None


def build():
    os.makedirs(OUT, exist_ok=True)
    comp.reset_fig()

    front = load("front")
    cover = front.cover() if front else "<div class='page cover'><h1>（封面缺失）</h1></div>"
    prologue = front.prologue() if front else ""
    toc_html = front.toc(TOC_ROWS) if front else ""
    acts = front.ACTS if front else {}

    body = [cover, prologue, toc_html]

    # 篇间幕页的位置：在指定章之前插入
    act_before = {"1": "一", "4": "二", "6": "三", "7": "四"}

    for key, mod in ORDER:
        if key in act_before and acts:
            body.append(acts[act_before[key]])
        m = load(mod)
        if m is None:
            continue
        body.append(m.chapter())

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>从零到独立交付 AI 项目</title>
<style>
{open(os.path.join(HERE, 'assets', 'base.css'), encoding='utf-8').read()}
{open(os.path.join(CONTENT, 'extra.css'), encoding='utf-8').read()}
</style></head>
<body>
{''.join(body)}
</body></html>"""

    html = pangu(html)

    # 未插值的组件调用检查（见 生产流水线.md 坑 1）
    bad = re.findall(r"\{(?:fig|box|pull|bignum|chapter|srcbox|SIDE|KEYPOINT)\(", html)
    assert not bad, f"未插值的组件调用：{bad}"

    out_html = os.path.join(OUT, "tutorial.html")
    open(out_html, "w", encoding="utf-8").write(html)

    anchors = []
    for key in TOC_KEYS:
        pat = ANCHOR_PAT.get(key, rf"^\s*第 {re.escape(key)} 章\s*$")
        anchors.append({"key": key, "pattern": pat})
    json.dump(anchors, open(os.path.join(OUT, "toc.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"  ✓ 已写出 {out_html}（{len(html)/1024:.0f} KB，{len(ORDER)} 个章节位）")


if __name__ == "__main__":
    build()
