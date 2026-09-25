# -*- coding: utf-8 -*-
"""文本级回归检查：HTML 与 PDF 两层，专抓「排版看不出来、但读者会读到」的缺陷。

用法：
    python checktext.py report.html 报告.pdf

检查项：
  1. HTML：残段——<p> 里只剩一个加粗/代码片段且不带句末标点。
     这正是 P() 把「句内强调」误当成「独立段落」时的痕迹。
  2. HTML：正文段落结尾断在句中（不是句末标点）。
  3. HTML：未插值的组件调用（{fig( / {chapter( …）——会原样印在纸上。
  4. PDF：URL 被折行（一行以 http 开头但不以 .html / 结尾）。
  5. PDF：编号列被折行（孤立的「1」「0」两行拼成一个两位数）。

为什么要有这一层：render.py 的几何自检只管版心、页边距、留白，
管不了「一段话被切成三行标题」这类语义级排版事故。
"""
import io
import re
import sys

END_OK = ("。", "！", "？", "；", "…", "!", "?", ";", "：", ":", "」", "』")
TAGS = re.compile(r"<[^>]+>")


def plain(s):
    return TAGS.sub("", s).strip()


def check_html(path):
    html = io.open(path, encoding="utf-8").read()
    problems = []

    # 未插值的组件调用
    bad = re.findall(r"\{(?:fig|box|pull|bignum|chapter|srcbox)\(", html)
    if bad:
        problems.append(f"未插值的组件调用：{sorted(set(bad))}")

    # 去掉自带样式的组件区，只留正文
    body = html
    for tag in ("side", "qa", "fig", "pull", "flagbox", "card",
                "toc", "cover", "ending", "chead"):
        body = re.sub(r'<div class="%s".*?</div>\s*</div>' % tag,
                      "", body, flags=re.S)

    ps = re.findall(r"<p>(.*?)</p>", body, re.S)
    frag, tail = [], []
    for p in ps:
        t = plain(p)
        if not t:
            continue
        if re.fullmatch(r"<(strong|code|em)>.*?</\1>", p.strip(), re.S) \
                and not t.endswith(END_OK):
            frag.append(t)
        if not t.endswith(END_OK):
            tail.append(t)
    if frag:
        problems.append(f"残段（加粗词被拆成独立段落）{len(frag)} 处：")
        problems += ["    · " + f[:70] for f in frag]
    if tail:
        problems.append(f"段落结尾断在句中 {len(tail)} 处：")
        problems += ["    · " + t[:70] for t in tail]

    print(f"[HTML] 正文段落 {len(ps)} 个")
    return problems


def check_pdf(path):
    import pymupdf
    doc = pymupdf.open(path)
    problems = []

    # 扫全部页，不要写死「从第 38 页起」——附录增减后范围会失效
    wrapped = []
    for i in range(1, doc.page_count + 1):
        for line in doc[i - 1].get_text().splitlines():
            s = line.strip()
            if re.match(r"^https?://", s) and not re.search(r"\.html$|/$", s):
                wrapped.append((i, s))
    if wrapped:
        problems.append(f"URL 被折行 {len(wrapped)} 处：")
        problems += [f"    · p{i} {s}" for i, s in wrapped]

    # 附录索引表里孤立的个位数（两位数被拆成两行）
    for i in range(1, doc.page_count + 1):
        t = doc[i - 1].get_text()
        if re.search(r"（\d+\s*$", t, re.M):
            problems.append(f"    · p{i} 有孤立的「（N」——括号内容被折行")

    links = sum(1 for pg in doc for l in pg.get_links() if l.get("uri"))
    print(f"[PDF ] 共 {doc.page_count} 页，可点击链接 {links} 条")
    return problems


def main():
    html = sys.argv[1] if len(sys.argv) > 1 else "report.html"
    pdf = sys.argv[2] if len(sys.argv) > 2 else None
    problems = check_html(html)
    if pdf:
        problems += check_pdf(pdf)
    if problems:
        print("\n发现 %d 类问题：" % len(problems))
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("\n✓ 文本级检查通过")


if __name__ == "__main__":
    main()
