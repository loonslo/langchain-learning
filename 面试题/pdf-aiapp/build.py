# -*- coding: utf-8 -*-
"""组装 HTML。目录页码由 render.py 回填到这个文件里——所以 toc_row(...)
   的每一次调用都必须写在一行内，且页码是字面整数。"""
import io, os, sys

import kit
import content_a, content_b, content_c, content_d

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "report.html")


def toc_row(key, name, page):
    """key 必须与 render.py 的 ANCHORS 完全一致。name 里不能出现双引号。"""
    return (f'<div class="l1"><span class="nm">{name}</span>'
            f'<span class="pg">{page}</span></div>')


def toc_sub(text):
    return f'<div class="l2">{text}</div>'


def toc_page():
    b = []
    b.append('<h2>目录</h2>')
    b.append('<div class="toc">')

    b.append('<div class="grp">开篇</div>')
    b.append(toc_row("序章", "序章　那 90 秒里该说的话", 2))
    b.append(toc_sub("一个会翻车的现场 · 这本书怎么用"))

    b.append('<div class="grp">地基：Agent 是什么</div>')
    b.append(toc_row("1", "第 1 章　Agent 到底是什么", 4))
    b.append(toc_sub("三个想当然的答案 · 四件套 · Agent 与 Workflow 的边界 · 什么时候不该用"))
    b.append(toc_row("2", "第 2 章　Agent 怎么想：推理与规划", 8))
    b.append(toc_sub("ReAct · Plan-and-Execute · Reflection · 任务拆分的判据"))
    b.append(toc_row("3", "第 3 章　Agent 怎么动手：工具调用", 12))
    b.append(toc_sub("Function Calling 链路 · 工具定义 · Tool Routing · 可信参数 · MCP · Skill · 网关 · 容错"))

    b.append('<div class="grp">系统：Agent 怎么活</div>')
    b.append(toc_row("4", "第 4 章　Agent 怎么记住：记忆机制", 21))
    b.append(toc_sub("两套作用域 · 裁剪删除摘要 · 长期记忆写什么 · 什么不该记"))
    b.append(toc_row("5", "第 5 章　Agent 怎么变成系统：多 Agent", 26))
    b.append(toc_sub("多 Agent 的三个理由 · 三种设计方案 · 交接 · 超时失联冲突 · 死循环治理"))
    b.append(toc_row("6", "第 6 章　Agent 怎么活下来：工程化", 31))
    b.append(toc_sub("上下文工程 · 采样参数与缓存 · 长上下文陷阱 · RAG 全链路 · 评估 · 可观测 · 幻觉 · 安全"))

    b.append('<div class="grp">落地：怎么搭、怎么答</div>')
    b.append(toc_row("7", "第 7 章　模型这一层：Prompt、部署与选型", 42))
    b.append(toc_sub("Prompt 五要素 · CoT · MoE · 部署框架怎么选 · 模型能力评测 · 模型选型"))
    b.append(toc_row("8", "第 8 章　Agent 怎么搭起来：框架选型", 47))
    b.append(toc_sub("框架地图 · 搭建七步走 · 工具注册 · LangChain 的四次演进 · 什么时候下沉 LangGraph · 手搓的边界"))
    b.append(toc_row("9", "第 9 章　工具箱：面试前 48 小时", 54))
    b.append(toc_sub("四段式回答 · 高频追问速查 · 陷阱回答 · 项目经历类问题怎么答 · 完整示范回答 · 反问面试官"))
    b.append(toc_row("尾声", "尾声　回到那 90 秒", 61))
    b.append(toc_sub("一段可以直接用的完整回答"))

    b.append("</div>")
    return kit.pagewrap("目录 | AI 应用开发面试指南", "".join(b))


def build():
    css = io.open(os.path.join(HERE, "base.css"), encoding="utf-8").read()

    body = []
    body.append(content_a.cover())
    body.append(content_a.preface())
    body.append(toc_page())
    body.append(content_a.ch1())
    body.append(content_a.ch2())
    body.append(content_b.ch3())
    body.append(content_b.ch4())
    body.append(content_b.ch5())
    body.append(content_c.ch6())
    body.append(content_c.ch7_model())
    body.append(content_c.ch8_framework())
    body.append(content_d.ch9_toolkit())
    body.append(content_d.ending())

    html = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<title>AI 应用开发面试指南</title><style>' + css + '</style></head>'
        '<body>' + "".join(body) + '</body></html>')

    # 未插值的组件调用会原样印在纸上，这里先拦一道
    import re
    bad = re.findall(r"\{(?:fig|box|pull|bignum|chapter|srcbox)\(", html)
    assert not bad, f"未插值的组件调用：{set(bad)}"

    io.open(OUT_HTML, "w", encoding="utf-8", newline="\n").write(html)
    print(f"已生成 {OUT_HTML}（{len(html)} 字符，{kit.fig_count()} 张图）")


if __name__ == "__main__":
    build()
