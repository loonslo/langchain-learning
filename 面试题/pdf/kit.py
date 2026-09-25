# -*- coding: utf-8 -*-
"""组件库：正文块、图表编号、侧栏、面试追问、表格。

约定：
  · 组件调用必须写在 f-string 里（或在普通字符串里用 + 拼接）。
    普通字符串里写 {fig(...)} 会把源码原样印在纸上——render.py 的
    机械自检专门扫这个痕迹。
  · fig() 的编号由调用顺序决定，所以内容模块必须由 build.py 按顺序调用。
"""

import re

BRAND, ACCENT, MUTE = "#1b4fd8", "#b45309", "#6b6b6b"

# ── 来源表：唯一真相。编号即上标编号。 ───────────────────
SOURCES = [
    ("小林面试笔记 · Agent 专题（24 题）",
     "https://xiaolinnote.com/ai/agent/agent_info.html"),
    ("小林面试笔记 · RAG 专题（21 题）",
     "https://xiaolinnote.com/ai/rag/rag_info.html"),
    ("小林面试笔记 · LLM 工具调用专题（18 题）",
     "https://xiaolinnote.com/ai/tools/tools_info.html"),
    ("小林面试笔记 · 大模型工程专题（23 题）",
     "https://xiaolinnote.com/ai/llm/llm_info.html"),
    ("小林面试笔记 · LangChain 框架专题（12 题）",
     "https://xiaolinnote.com/ai/langchain/langchain_info.html"),
]
_NO = {k: i + 1 for i, k in enumerate(
    ["agent", "rag", "tools", "llm", "langchain"])}


def cite(key):
    """上标引用。key 不在 SOURCES 里直接抛错，不静默兜底。"""
    if key not in _NO:
        raise KeyError(f"未知来源 key：{key}")
    return _Rich(f'<sup class="cite">{_NO[key]}</sup>')


# ── 基础 ──────────────────────────────────────────────────
# 组件产出物用 str 子类打标记，这样 P() 才能区分两种语义：
#   · 全是纯字符串   → 每个参数是一段（序章对话、尾声问答）
#   · 含组件产出物   → 这是「一句话里的强调」，必须合成一段
# 不这么做的话，P("…是", E("目标"), "。所以…") 会被拆成三段，
# 句中的加粗词单独占一行——这是最伤可读性的排版事故。
class _Rich(str):
    __slots__ = ()


_TAG = re.compile(r"<[^>]+>")
# 自成一句的结尾标点：加粗引导句以它收尾时，独立成段
_SENT_END = ("。", "！", "？", "；", "!", "?", ";")


def E(s):
    """强调（字重）。中文不用斜体。"""
    return _Rich(f"<strong>{s}</strong>")


def C(s):
    """行内代码 / 字段名。"""
    return _Rich(f"<code>{s}</code>")


def _plain(s):
    """剥掉标签，只留可见文字，用于判断句末标点。"""
    return _TAG.sub("", s).rstrip()


def P(*parts):
    if not any(isinstance(p, _Rich) for p in parts):
        return "".join(f"<p>{p}</p>" for p in parts)
    # 加粗引导句自成一句（以句末标点收尾）→ 独立成段，后面照常递归
    if isinstance(parts[0], _Rich) and _plain(parts[0]).endswith(_SENT_END):
        return f"<p>{parts[0]}</p>" + P(*parts[1:])
    # 其余情况（冒号标签、句内强调）→ 合并成一段，run-in 排法
    return f'<p>{"".join(parts)}</p>'


def UL(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


# ── 章首 ──────────────────────────────────────────────────
def chapter(num, title, hook):
    return (f'<div class="chead"><div class="cnum">第 {num} 章</div>'
            f'<h2>{title}</h2><p class="chook">{hook}</p></div>')


def frontmatter_head(title, hook):
    return (f'<div class="chead"><h2>{title}</h2>'
            f'<p class="chook">{hook}</p></div>')


def h3(t):
    return f"<h3>{t}</h3>"


def h4(t):
    return f"<h4>{t}</h4>"


# ── 图表 ──────────────────────────────────────────────────
_FIGN = [0]


def fig(svg, title, src=None):
    _FIGN[0] += 1
    n = _FIGN[0]
    s = f'<div class="src">{src}</div>' if src else ""
    return (f'<div class="fig"><div class="figtitle">图 {n}　{title}</div>'
            f'{svg}{s}</div>')


def fig_count():
    return _FIGN[0]


# ── 侧栏 ──────────────────────────────────────────────────
def side(label, *paras):
    body = "".join(f"<p>{p}</p>" for p in paras)
    return (f'<div class="side"><span class="lbl">{label}</span>{body}</div>')


# ── 面试追问 ──────────────────────────────────────────────
def qa(q, a):
    return f'<div class="qa"><p class="q">{q}</p><p class="a">{a}</p></div>'


def qa_block(*items):
    return "".join(qa(q, a) for q, a in items)


# ── 红旗清单 ──────────────────────────────────────────────
def flag(label, rows):
    body = "".join(f"<li>{r}</li>" for r in rows)
    return (f'<div class="flagbox"><span class="lbl">{label}</span>'
            f'<ul>{body}</ul></div>')


# ── 表格 ──────────────────────────────────────────────────
def tbl(headers, rows, widths=None, cls=""):
    if widths:
        cols = "".join(f'<col style="width:{w}%">' for w in widths)
        cg = f"<colgroup>{cols}</colgroup>"
    else:
        cg = ""
    th = "".join(f"<th>{h}</th>" for h in headers)
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                 for r in rows)
    klass = f' class="{cls}"' if cls else ""
    return (f'<table{klass}>{cg}<thead><tr>{th}</tr></thead>'
            f'<tbody>{tb}</tbody></table>')


def link(url):
    """可点击的链接。Chrome 打印成 PDF 时会保留为链接注释。"""
    return _Rich(f'<a href="{url}">{url}</a>')


# ── 大数字行 ──────────────────────────────────────────────
def bignums(items):
    inner = "".join(
        f'<div class="item"><div class="v">{v}</div>'
        f'<div class="k">{k}</div></div>' for v, k in items)
    return f'<div class="bignums">{inner}</div>'


# ── 引文 ──────────────────────────────────────────────────
def pull(text):
    return f'<div class="pull"><p>{text}</p></div>'


def card(title, meta):
    return f'<div class="card"><p class="t">{title}</p><p class="m">{meta}</p></div>'


def crumb(text):
    return f'<div class="crumb">{text}</div>'


def pagewrap(crumb_text, body):
    """一个容器 = 一章。页眉放进 thead，跨页时自动重复。"""
    return (f'<table class="pagewrap"><thead><tr><td>'
            f'{crumb(crumb_text)}</td></tr></thead><tbody><tr><td>'
            f'{body}</td></tr></tbody></table>')
