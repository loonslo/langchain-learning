"""组件库：教程正文的所有 HTML 片段都由这里产出。

关键设计（来自 huashu-report-windows 第九节）：
`P(*parts)` 同时承担「多段」和「段内强调」两种调用，一眼分不清意图。
这里用 _Rich 类型标记区分：全纯字符串 → 每个参数一段；
含组件 → 看首参剥掉标签后是否以句末标点收尾，是则自成一段，否则 run-in 合成一段。
"""
import re

class _Rich(str):
    __slots__ = ()


def E(s):
    """行内强调（加粗）。"""
    return _Rich(f"<strong>{s}</strong>")


def C(s):
    """行内代码。"""
    return _Rich(f"<code>{s}</code>")


def A(s, href):
    """链接（Chrome 打印保留链接注释）。"""
    return _Rich(f'<a href="{href}">{s}</a>')


def NW(s):
    """不折行（用于「（18 题）」这类括号内容）。"""
    return _Rich(f'<span class="nw">{s}</span>')


_TAG = re.compile(r"<[^>]+>")
_SENT_END = ("。", "！", "？", "；", "!", "?", ";")


def P(*parts):
    if not any(isinstance(p, _Rich) for p in parts):
        return "".join(f"<p>{p}</p>" for p in parts)
    if isinstance(parts[0], _Rich) and _TAG.sub("", parts[0]).rstrip().endswith(_SENT_END):
        return f"<p>{parts[0]}</p>" + P(*parts[1:])
    return f'<p>{"".join(parts)}</p>'


def H3(s):
    return f"<h3>{s}</h3>"


def H4(s):
    return f"<h4>{s}</h4>"


def UL(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def OL(items):
    return "<ol>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"


def CODE(lines, lang=""):
    """代码块。lines 是字符串或字符串列表。"""
    if isinstance(lines, str):
        lines = lines.split("\n")
    body = "\n".join(lines)
    return f'<pre class="code"><code>{body}</code></pre>'


def TABLE(headers, rows, widths=None):
    """数据表。列必须有可见边界（base.css 已加竖分隔线）。"""
    if widths:
        cols = "".join(f'<col style="width:{w}%">' for w in widths)
        colgroup = f"<colgroup>{cols}</colgroup>"
    else:
        colgroup = ""
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<table>{colgroup}<thead><tr>{th}</tr></thead>'
            f"<tbody>{trs}</tbody></table>")


def SIDE(title, *parts):
    """侧栏：放白话解释、口径、易错点。读者可跳过也可细看。"""
    body = "".join(parts)
    t = f'<div class="side-t">{title}</div>' if title else ""
    return f'<aside class="side">{t}{body}</aside>'


def KEYPOINT(*parts):
    """小结框：一句陈述，不是命令。"""
    return f'<div class="keypoint">{"".join(parts)}</div>'


def VERIFY(*parts):
    """验证框：怎么观察到它生效了。"""
    return f'<div class="verify"><div class="v-t">怎么知道它生效了</div>{"".join(parts)}</div>'


def TRAP(*parts):
    """易错框：描述「这样做的代价」，不做道德判词。"""
    return f'<div class="trap"><div class="v-t">容易出问题的地方</div>{"".join(parts)}</div>'


def RUN(items):
    """章末「怎么跑这一章」：[(标签, 内容), ...]。

    固定七项，顺序一致，缺项显式写「无」——每章都能按同一张表复现。
    """
    rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in items)
    return ('<div class="runbox"><div class="run-t">怎么跑这一章</div>'
            f'<table class="runtab"><tbody>{rows}</tbody></table></div>')


def TASK(text):
    """章末动手任务：改一个条件、观察结果、留下证据。"""
    return (f'<div class="taskbox"><div class="task-t">动手：改一个条件，看它怎么变</div>'
            f"<p>{text}</p></div>")


def CHECKLIST(items):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<div class="checklist"><div class="v-t">这一章留下的几点</div><ul>{lis}</ul></div>'


def HOOK(text):
    """章末钩子——不是小结，是把下一章的问题提出来。"""
    return f'<p class="hook">{text}</p>'


_FIGN = {"n": 0}


def FIG(svg, title, src=None):
    """插图。title 写结论不写主题；src 是数据源行。

    编号是右上角的空心小圆数字，只作检索锚点。
    纵横比高的图（纵向流程链等）在 76mm 封顶下会缩成「邮票」——
    按 viewBox 自动加 .fig-tall，封顶放宽到 150mm（阈值 0.62 实测覆盖
    序章 5 层递进图 ratio≈0.69，不误伤普通横图和图表）。
    """
    _FIGN["n"] += 1
    n = _FIGN["n"]
    tall = ""
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if m:
        vw, vh = float(m.group(1)), float(m.group(2))
        if vw and vh / vw >= 0.62:
            tall = " fig-tall"
    num = f'<span class="fignum">{n}</span>'
    cap = f'<div class="figtitle">{title}</div>'
    s = f'<div class="src">{src}</div>' if src else ""
    return (f'<figure class="fig{tall}" data-fig="{n}">{num}'
            f'<div class="figbody">{svg}</div>{cap}{s}</figure>')


def reset_fig():
    _FIGN["n"] = 0


def CHAPTER(num, title, hook, key):
    """章首页：章号 + 标题 + 一句钩子。

    章号里的数字单独包一层 span：`.cnum` 有 letter-spacing，直接作用在
    「第 10 章」上会把两位数拆成「第 1 0 章」（实测踩过）。数字层归零字距。
    """
    return (f'<div class="chead" id="{key}">'
            f'<div class="cnum">第 <span class="cnum-n">{num}</span> 章</div>'
            f'<h2>{title}</h2>'
            f'<p class="chook">{hook}</p></div>')


def PAGEWRAP(crumb, body):
    """分页容器：一个容器 = 一章，页眉放 thead 保证跨页重复。"""
    return (f'<table class="pagewrap"><thead><tr><td>'
            f'<div class="crumb">{crumb}</div></td></tr></thead>'
            f"<tbody><tr><td>{body}</td></tr></tbody></table>")


def ACT(n, name, one_line):
    """幕间页：整页、居中、极简。"""
    return (f'<table class="pagewrap actpage"><thead><tr><td></td></tr></thead><tbody><tr><td>'
            f'<div class="act"><div class="act-n">第 {n} 篇</div>'
            f'<div class="act-name">{name}</div>'
            f'<div class="act-line">{one_line}</div></div>'
            f"</td></tr></tbody></table>")


def toc_row(key, title, page, level=1):
    """目录行。必须写在一行内，否则页码回填的正则匹配不到。"""
    cls = "toc1" if level == 1 else "toc2"
    return f'<div class="tocrow {cls}"><span class="toc-t">{title}</span><span class="toc-d"></span><span class="toc-p">{page}</span></div>'
