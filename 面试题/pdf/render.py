#!/usr/bin/env python3
"""报告渲染器（Windows 版）：HTML → PDF，自动回填目录页码，并做机械化排版自检。

用法：
    python render.py build.py 报告.html 报告.pdf
    python render.py build.py 报告.html 报告.pdf --check-only

与 huashu-report 原版 assets/render.py 的差异（全部因为 Windows 上没有 poppler）：
  1. pdfinfo / pdftotext / pdftoppm  →  PyMuPDF（一个库顶三个工具）
  2. Playwright 用本机 Chrome：launch(channel="chrome")
  3. geometry_check 里 pix.stride 不一定等于 pix.width（PyMuPDF 按 4 字节对齐），
     必须用 stride 切片，否则量出「看似合理但全是错的」留白。
  4. locate() 的例外集合加上「序章」——序章排在目录之前，否则永远定位不到。
  5. figs 正则同时认中文「图 N」和英文「Figure N」。
"""
import asyncio, os, re, subprocess, sys

import pymupdf

# ── 配置 ───────────────────────────────────────────────────
REPORT_TITLE = "Agent 面试通读本"

MIN_MM_A4 = {"left": 12, "right": 12, "top": 10, "bottom": 13}
MIN_MM = MIN_MM_A4

# 目录条目 key -> 在 PDF 文本中定位该章起始页的正则
# key 必须与 build.py 里 toc_row("<key>", ...) 的第一个参数完全一致
# ⚠️ 标题里的 letter-spacing 会让 PDF 文本层出现「序 章」这样的间隔，
#    所以每个模式都用 \s* 允许字间空格，否则永远定位不到。
ANCHORS = [
    ("序章", r"^\s*序\s*章"),
    ("1", r"^\s*第\s*1\s*章"),
    ("2", r"^\s*第\s*2\s*章"),
    ("3", r"^\s*第\s*3\s*章"),
    ("4", r"^\s*第\s*4\s*章"),
    ("5", r"^\s*第\s*5\s*章"),
    ("6", r"^\s*第\s*6\s*章"),
    ("7", r"^\s*第\s*7\s*章"),
    ("8", r"^\s*第\s*8\s*章"),
    ("尾声", r"^\s*尾\s*声"),
    ("附录 A", r"附\s*录\s*A"),
    ("附录 B", r"附\s*录\s*B"),
]

FOOTER_TPL = """
<div style="width:100%;font-size:7pt;color:#8a8a8a;
     font-family:'Microsoft YaHei','PingFang SC',sans-serif;padding:0 19mm;">
  <div style="float:left">{title}</div>
  <div style="float:right"><span class="pageNumber"></span></div>
</div>"""
BLANK = '<div style="height:0"></div>'


async def _render(html, pdf, title):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel="chrome")
        pg = await b.new_page()
        await pg.goto("file://" + os.path.abspath(html), wait_until="networkidle")
        await pg.pdf(path=pdf, format="A4", print_background=True,
                     display_header_footer=True,
                     header_template=BLANK,
                     footer_template=FOOTER_TPL.format(title=title),
                     margin={"top": "17mm", "bottom": "15mm",
                             "left": "19mm", "right": "19mm"})
        await b.close()


# ── PyMuPDF 版的三件套 ─────────────────────────────────────
def _doc(pdf):
    return pymupdf.open(pdf)


def page_count(pdf):
    with _doc(pdf) as d:
        return d.page_count


def page_texts(pdf, n):
    with _doc(pdf) as d:
        return {p: d[p - 1].get_text() for p in range(1, n + 1)}


def locate(pdf, anchors):
    """定位每章起始页。跳过目录页本身，否则每章都会被定位到目录那一页。"""
    n = page_count(pdf)
    pages = page_texts(pdf, n)
    toc_pages = [p for p in pages
                 if re.match(r"\s*目录\s*[|｜]", pages[p])
                 or re.search(r"^\s*目录\s*$", pages[p], re.M)]
    toc_page = max(toc_pages) if toc_pages else 0
    found = {}
    for p in sorted(pages):
        for key, pat in anchors:
            if key in found:
                continue
            # 目录之前只允许匹配排在目录前面的条目（序章）
            if p <= toc_page and key not in ("序章",):
                continue
            if re.search(pat, pages[p], re.M):
                found[key] = p
    return found, n


def patch_toc(builder, found):
    """把实际页码写回生成器的 toc_row 调用。toc_row(...) 必须写在一行内。"""
    t = open(builder, encoding="utf-8").read()
    orig = t
    for key, no in found.items():
        t = re.sub(rf'(toc_row\(\s*"{re.escape(key)}"\s*,\s*"[^"]*"\s*,\s*)\d+',
                   rf'\g<1>{no}', t)
    if t != orig:
        open(builder, "w", encoding="utf-8").write(t)
    return t != orig


# ── 几何自检：逐页实测四边留白 ─────────────────────────────
GEO_DPI = 40
_MM = 25.4 / GEO_DPI
INK = 200
FULLBLEED = 0.35
FOOTER_BAND_MM = 12


def geometry_check(pdf):
    """每页实测内容离纸边的四边留白。返回 issue 列表。"""
    issues, fullbleed, blank_bottom = [], [], []
    band = int(FOOTER_BAND_MM / _MM)
    with _doc(pdf) as d:
        for pno in range(1, d.page_count + 1):
            pix = d[pno - 1].get_pixmap(dpi=GEO_DPI, colorspace=pymupdf.csGRAY)
            w, h, stride = pix.width, pix.height, pix.stride
            sm = pix.samples
            # ⚠️ stride 可能 > width（4 字节对齐）。直接 samples[y*w:...] 会错位。
            px = b"".join(sm[y * stride: y * stride + w] for y in range(h))
            if len(px) < w * h:
                continue
            if sum(1 for b in px if b < 245) / (w * h) > FULLBLEED:
                fullbleed.append(pno)
                continue
            xmin, xmax, ymin, ymax = w, -1, h, -1
            for y in range(h - band):
                row = px[y * w:(y + 1) * w]
                if min(row) >= INK:
                    continue
                lo = next(x for x, b in enumerate(row) if b < INK)
                hi = w - 1 - next(x for x, b in enumerate(reversed(row)) if b < INK)
                xmin, xmax = min(xmin, lo), max(xmax, hi)
                ymin, ymax = min(ymin, y), max(ymax, y)
            if xmax < 0:
                issues.append(f"第 {pno} 页整页空白")
                continue
            m = {"left": xmin * _MM, "right": (w - 1 - xmax) * _MM,
                 "top": ymin * _MM, "bottom": (h - 1 - ymax) * _MM}
            bad = {k: v for k, v in m.items() if v < MIN_MM[k]}
            if bad:
                s = "、".join(f"{k} {v:.1f}mm(下限{MIN_MM[k]})" for k, v in bad.items())
                issues.append(f"第 {pno} 页留白不足：{s}")
            y0 = int((h - band) * 0.65)
            zone = [px[y * w + x] for y in range(y0, h - band) for x in range(xmin, xmax + 1)]
            if zone and sum(1 for b in zone if b < INK) / len(zone) < 0.012:
                blank_bottom.append(pno)
    if fullbleed:
        print(f"  全出血页 {fullbleed} 跳过边距检查——这些页的内部留白肉眼确认")
    if blank_bottom:
        print(f"  下半页大面积留白候选：{blank_bottom}（章末正常，章内是分页容器切碎了）")
    return issues


# ── 机械自检 ───────────────────────────────────────────────
def selfcheck(pdf, html=None):
    n = page_count(pdf)
    pages = page_texts(pdf, n)
    full = "\n".join(pages.values())
    issues = []

    figs = re.findall(r"(?:图|Figure)\s*([0-9]+(?:\.[0-9]+)*)", full)
    if len(set(figs)) != len(figs):
        dup = [f for f in set(figs) if figs.count(f) > 1]
        issues.append(f"图表编号重复：{dup}")

    toc_p = next((p for p in sorted(pages)
                  if re.search(r"^\s*目录\s*$", pages[p], re.M)), None)
    if toc_p:
        printed = re.findall(r"(\S[^\n]*?)\s+(\d{1,3})\s*$", pages[toc_p], re.M)
        if not printed:
            issues.append("目录页里没找到任何页码——检查 toc_row 是否渲染出来了")

    thin = [p for p, t in pages.items() if p > 1 and len(t.strip()) < 120]
    if thin:
        issues.append(f"内容极少的页：{thin}")

    if re.search(r"\('<(figure|div|table)", full):
        issues.append("检测到 tuple 渲染痕迹——f-string 里多写了逗号")

    for pat in (r"placeholder", r"\bTODO\b", r"\bXXX\b", r"\bTBD\b",
                r"[\[【（(]\s*待[补補定]", r"待[补補定]\s*[\]】）)]",
                r"^\s*待[补補定]\s*$", r"\{\{[^}]*\}\}"):
        if re.search(pat, full, re.I | re.M):
            issues.append(f"正文里残留占位符：{pat}")

    # 未插值的组件调用（普通字符串里写了 {fig(...)}）
    if html and os.path.exists(html):
        doc = open(html, encoding="utf-8").read()
        bad = re.findall(r"\{(?:fig|box|pull|bignum|chapter|srcbox)\(", doc)
        if bad:
            issues.append(f"未插值的组件调用：{set(bad)}")

    issues += geometry_check(pdf)

    print(f"共 {n} 页，{len(set(figs))} 张图")
    if issues:
        print("⚠ 机械自检发现：")
        for i in issues:
            print("  -", i)
    else:
        print("✓ 机械自检通过")
    return issues


def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    builder, html, pdf = sys.argv[1:4]
    if "--check-only" in sys.argv:
        selfcheck(pdf, html); return

    for round_no in range(1, 6):
        subprocess.run([sys.executable, builder], check=True)
        asyncio.run(_render(html, pdf, REPORT_TITLE))
        found, n = locate(pdf, ANCHORS)
        missing = [k for k, _ in ANCHORS if k not in found]
        if missing:
            print(f"⚠ 第 {round_no} 轮未定位到：{missing}（检查 ANCHORS 正则）")
        if not patch_toc(builder, found):
            print(f"第 {round_no} 轮：目录页码已收敛（{n} 页）")
            break
        print(f"第 {round_no} 轮：回填页码 {found}")
    else:
        print("⚠ 5 轮仍未收敛——多半是某个 toc_row 跨行写了")

    selfcheck(pdf, html)


if __name__ == "__main__":
    main()
