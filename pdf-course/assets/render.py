#!/usr/bin/env python3
"""教程渲染器（Windows 适配版）：HTML → PDF，自动回填目录页码，并做机械化排版自检。

基于 huashu-report 的 assets/render.py，按 huashu-report-windows 适配层改写：
  1. poppler(pdfinfo/pdftotext/pdftoppm) → PyMuPDF（Windows 通常没有 poppler）
  2. Playwright 用本机 Chrome（channel="chrome"），免下载 Chromium
  3. geometry_check 用 pix.stride 取行（PyMuPDF 按 4 字节对齐，stride 可能 > width，
     直接用 samples[y*w:y*w+w] 会读到错位字节，量出"看似合理但全错"的留白）
  4. ANCHORS 从 out/toc.json 读（章节多，硬编码不现实）

用法：
    python render.py build.py out/tutorial.html "out/AI应用开发 零基础到交付.pdf"
    python render.py build.py out/tutorial.html "out/AI应用开发 零基础到交付.pdf" --check-only
"""
import asyncio, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# toc.json 由 build.py 写在「输出目录」里，和 HTML 同级；不是 assets/ 下。
# 这里只给默认值，实际以 main() 收到的 html 路径为准（见 resolve_toc_json）。
TOC_JSON = os.path.join(os.path.dirname(HERE), "out", "toc.json")


def resolve_toc_json(html_path):
    """toc.json 与 HTML 输出同目录——按调用时传入的 html 路径解析，避免写死目录。"""
    return os.path.join(os.path.dirname(os.path.abspath(html_path)), "toc.json")

REPORT_TITLE = "从零到独立交付 AI 项目"
MIN_MM_A4 = {"left": 12, "right": 12, "top": 10, "bottom": 13}
MIN_MM = MIN_MM_A4

FOOTER_TPL = """
<div style="width:100%;font-size:7pt;color:#8a8a8a;
     font-family:'Microsoft YaHei',sans-serif;padding:0 19mm;">
  <div style="float:left">{title}</div>
  <div style="float:right"><span class="pageNumber"></span></div>
</div>"""
BLANK = '<div style="height:0"></div>'


def load_anchors(toc_json=None):
    """读章节锚点。**找不到文件必须大声报错**——静默返回空列表会让回填整条链路空转，
    却仍然打印「目录页码已收敛」，把「目录页码全是初始值」这个硬伤伪装成成功（踩过）。"""
    path = toc_json or TOC_JSON
    if not os.path.exists(path):
        print(f"⚠ 读不到章节锚点文件：{path}")
        print("  目录页码不会回填——检查 build.py 是否成功写出了 toc.json，"
              "以及路径是否指向 HTML 所在目录。")
        return []
    data = json.load(open(path, encoding="utf-8"))
    if not data:
        print(f"⚠ 章节锚点文件为空：{path}")
    return [(d["key"], d["pattern"]) for d in data]


async def _render(html, pdf, title):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel="chrome")
        pg = await b.new_page()
        await pg.goto("file://" + os.path.abspath(html).replace("\\", "/"), wait_until="networkidle")
        await pg.pdf(path=pdf, format="A4", print_background=True,
                     display_header_footer=True,
                     header_template=BLANK,
                     footer_template=FOOTER_TPL.format(title=title),
                     margin={"top": "17mm", "bottom": "15mm",
                             "left": "19mm", "right": "19mm"})
        await b.close()


def _doc(pdf):
    import pymupdf
    return pymupdf.open(pdf)


def page_count(pdf):
    return _doc(pdf).page_count


def page_texts(pdf, n):
    d = _doc(pdf)
    return {p: d[p - 1].get_text() for p in range(1, n + 1)}


def _find_toc_page(pages):
    """找目录页：含独立「目录」标题的页里，取「标题 + 页码」行最多的那一页。

    不能用「含独立目录行的最大页码」——正文里也可能出现独立的「目录」二字
    （本书附录 B 的代码地图就有一张目录结构表），max() 会把它当成目录页，
    于是所有章节都被判成「在目录之前」而跳过，只有豁免的序章能被定位到（踩过）。
    """
    cands = [p for p in pages if re.search(r"^\s*目录\s*$", pages[p], re.M)]
    if not cands:
        return 0
    return max(cands, key=lambda p: len(
        re.findall(r"\S[^\n]*?\s+\d{1,3}\s*$", pages[p], re.M)))


HEAD_LINES = 6


def locate(pdf, anchors):
    """定位每章起始页。跳过目录页本身（目录里也印着章节标题）。

    锚点只在**页首前几行**里匹配：正文里也会出现独立成行的「第 4 章」——
    第 3 章末尾那句「后面第 4 章的 4.15…」折行后正好如此，全文匹配会把它
    当成章首页，目录页码就填错了一章（踩过）。章首页的 cnum 固定在前三行内。
    """
    n = page_count(pdf)
    pages = page_texts(pdf, n)
    toc_page = _find_toc_page(pages)
    found = {}
    for p in sorted(pages):
        head = "\n".join(pages[p].split("\n")[:HEAD_LINES])
        for key, pat in anchors:
            if key in found:
                continue
            if p <= toc_page and key not in ("序章",):
                continue
            if re.search(pat, head, re.M):
                found[key] = p
    return found, n


def patch_toc(builder, found):
    t = open(builder, encoding="utf-8").read()
    orig = t
    for key, no in found.items():
        t = re.sub(rf'(toc_row\(\s*"{re.escape(key)}"\s*,\s*"[^"]*"\s*,\s*)\d+',
                   rf'\g<1>{no}', t)
    if t != orig:
        open(builder, "w", encoding="utf-8").write(t)
    return t != orig


# ── 几何自检：逐页实测四边留白（PyMuPDF 版） ────────────────
GEO_DPI = 40
_MM = 25.4 / GEO_DPI
INK = 200
FULLBLEED = 0.35
FOOTER_BAND_MM = 12


def geometry_check(pdf):
    issues, fullbleed, blank_bottom = [], [], []
    band = int(FOOTER_BAND_MM / _MM)
    import pymupdf
    doc = pymupdf.open(pdf)
    for pno in range(1, doc.page_count + 1):
        pix = doc[pno - 1].get_pixmap(dpi=GEO_DPI, colorspace=pymupdf.csGRAY)
        w, h, stride = pix.width, pix.height, pix.stride
        sm = pix.samples
        # stride 修正：PyMuPDF 按 4 字节对齐，stride 可能 > width
        px = b"".join(sm[y * stride: y * stride + w] for y in range(h))
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


EM_BUDGET = 6
LEN_SPREAD = 2.0


def longdoc_check(html):
    issues = []
    if not html or not os.path.exists(html):
        return issues
    doc = open(html, encoding="utf-8").read()
    chunks = re.split(r'<table class="pagewrap"', doc)[1:]
    bodies = [(i, re.sub(r"<[^>]+>", "", c), c) for i, c in enumerate(chunks, 1)]
    cand = [(i, b, c) for i, b, c in bodies if len(b) > 1200]
    if len(cand) < 6:
        return issues
    med = sorted(len(b) for _, b, _ in cand)[len(cand) // 2]
    chaps = [(i, b, c) for i, b, c in cand if med / 5 <= len(b) <= med * 5]
    if len(chaps) < 6:
        return issues
    over = [(i, len(re.findall(r"<em[ >]", c))) for i, _, c in chaps
            if len(re.findall(r"<em[ >]", c)) > EM_BUDGET]
    if over:
        issues.append(f"加粗超预算的章（>{EM_BUDGET} 处）：{over}")
    lens = [(i, len(b)) for i, b, _ in chaps]
    lo = min(L for _, L in lens); hi = max(L for _, L in lens)
    # 只对「正文章」比长度：序章和附录在结构上就不是散文章（附录基本是表格，
    # 剥掉标签后字符数天然偏低），把它们算进来必然误报。
    def _crumb(c):
        m = re.search(r'<div class="crumb">(.*?)</div>', c, re.S)
        return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    prose = [(i, L, _crumb(c)) for (i, L), (_, _, c) in zip(lens, chaps)
             if not re.match(r"^(序章|附录)", _crumb(c))]
    if len(prose) >= 6:
        plo = min(L for _, L, _ in prose); phi = max(L for _, L, _ in prose)
        print(f"  正文章长度 {plo}–{phi} 字符（{phi/plo:.1f} 倍）："
              + "、".join(f"{t.split('　')[0]}={L}" for _, L, t in prose))
        # 4~5 倍以内由「各章覆盖天数不同」解释得通，不作为缺陷；
        # 超过 5 倍才像是残章（写漏了），这时才值得拦。
        if phi > plo * 5.0:
            thin = [t.split("　")[0] for _, L, t in prose if L < (plo + phi) / 3]
            issues.append(f"正文章长差 {phi/plo:.1f} 倍（最短 {plo}、最长 {phi} 字符），"
                          f"疑似残章：{thin}")
    txt = re.sub(r"<[^>]+>", "", doc)
    gaps = re.findall(r"[。，：；？！」』）][ \t](?=[一-鿿「（])", txt)
    if gaps:
        issues.append(f"中文标点后残留空格 {len(gaps)} 处")
    return issues


def selfcheck(pdf, html=None):
    n = page_count(pdf)
    pages = page_texts(pdf, n)
    full = "\n".join(pages.values())
    issues = []

    # 图表编号只认 HTML 里真正的 <figure data-fig="N">，不用正文正则找「图 + 数字」：
    # 后者会命中普通文字——本书表格里「…变成显式图」紧接下一行的「57」（下一个章节编号），
    # 就被读成了「图 57」，于是报出一个根本不存在的图表编号（踩过）。
    doc = open(html, encoding="utf-8").read() if html and os.path.exists(html) else ""
    figs = re.findall(r'data-fig="(\d+)"', doc)
    if figs and "Exhibit" in full:
        issues.append("图表编号混用了 Figure 和 Exhibit")
    dup = [f for f in set(figs) if figs.count(f) > 1]
    if dup:
        issues.append(f"图表编号重复：{dup}")

    toc_p = _find_toc_page(pages) or None
    if toc_p:
        printed = re.findall(r"(\S[^\n]*?)\s+(\d{1,3})\s*$", pages[toc_p], re.M)
        if not printed:
            issues.append("目录页里没找到任何页码——检查 toc_row 是否渲染出来了")
        else:
            # 页码全一样 = 回填失败（通常是锚点文件没读到，回填空转），
            # 而不是「所有章都在同一页」。这条以前靠人眼看出来，现在机器拦。
            nos = [n for _, n in printed]
            if len(nos) >= 4 and len(set(nos)) == 1:
                issues.append(f"目录页码全部是 {nos[0]}——回填没生效，检查章节锚点")

    # 幕间页（「第 N 篇」）本来就是整页极简设计，不能算「内容极少」——
    # 假警报会训练人忽略整份自检，所以显式排除。
    act_pat = re.compile(r"第\s*[一二三四五六七八九十]\s*篇")
    thin = [p for p, t in pages.items()
            if p > 1 and len(t.strip()) < 120 and not act_pat.search(t)]
    if thin:
        issues.append(f"内容极少的页：{thin}")

    if re.search(r"\('<(figure|div|table)", full):
        issues.append("检测到 tuple 渲染痕迹——f-string 里多写了逗号")

    # 占位符检测：只认占位符**形状**。TODO/XXX/TBD 必须大小写敏感——
    # 正文里的代码示例（如 class Xxx:）会被大小写不敏感的正则误报，
    # 而假警报会训练人忽略整份自检（见 huashu-report-windows 第六节）。
    for pat, flags in ((r"placeholder", re.I),
                       (r"(?<![\w-])TODO(?![\w-])", 0),
                       (r"(?<![\w-])XXX(?![\w-])", 0),
                       (r"(?<![\w-])TBD(?![\w-])", 0),
                       (r"[\[【（(]\s*待[补補定]", 0),
                       (r"待[补補定]\s*[\]】）)]", 0),
                       (r"^\s*待[补補定]\s*$", re.M),
                       (r"\{\{[^}]*\}\}", 0)):
        if re.search(pat, full, flags):
            issues.append(f"正文里残留占位符：{pat}")

    issues += geometry_check(pdf)
    issues += longdoc_check(html)

    print(f"共 {n} 页，{len(set(figs))} 张图")
    if issues:
        print("⚠ 机械自检发现：")
        for i in issues:
            print("  -", i)
    else:
        print("✓ 机械自检通过")
    print(EYE_ONLY)
    return issues


EYE_ONLY = """
机械+几何检查查不出下面这些——必须把每页渲染成 PNG 用眼睛看：
  1. 相邻列内容在列缝处粘连
  2. 负值被画成零高度
  3. 图表标注被版心切掉
  4. 居中标注在最边上那个点被切
  5. 视觉锚数字被拦腰折断
  6. Y 轴不从零开始
  7. 内容跨页时页眉丢失；长表跨页时表头没重复
  8. 双列组件里某一列塌成一个字宽
  9. 全出血页（封面/章首页）的内部留白与字号层级
"""


def add_navigation(pdf, html):
    """给 PDF 加书签，并把目录页的条目做成可点击的内部跳转。

    Chrome 的 print-to-PDF 既不会写书签，也不会把目录做成链接——
    本书正文反复要求「翻到某章」「打开某个目录」，这两样得在 PDF 层补。
    """
    import pymupdf
    if not html or not os.path.exists(html):
        return
    doc = pymupdf.open(pdf)
    n = doc.page_count
    pages = {p: doc[p - 1].get_text() for p in range(1, n + 1)}
    toc_page = _find_toc_page(pages)
    if not toc_page:
        print("⚠ 没找到目录页，跳过书签与目录链接")
        return

    doc_html = open(html, encoding="utf-8").read()
    seq = []
    for m in re.finditer(r"<(h2|h3)[^>]*>(.*?)</\1>", doc_html, re.S):
        t = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        t = re.sub(r"\s+", " ", t.replace("\n", " "))
        if t and t != "目录":
            seq.append((1 if m.group(1) == "h2" else 2, t))
    if not seq:
        print("⚠ HTML 里没找到标题块，跳过书签")
        return

    # 比较前去掉所有空白：小节标题在 PDF 文本层里可能被折行，
    # 而 HTML 里是一整行——不归一化，二级书签会漏掉绝大多数。
    def _norm(s):
        return re.sub(r"\s+", "", s)

    npages = {p: _norm(t) for p, t in pages.items()}

    def find_in(title, lo, hi):
        key = _norm(title)
        for q in range(lo, hi + 1):
            if key in npages[q]:
                return q
        return None

    toc, cursor = [], toc_page + 1
    for i, (level, title) in enumerate(seq):
        if i == 0:
            # 序章排在目录之前，单独在目录页之前找。
            p = find_in(title, 1, toc_page)
        else:
            # 单调推进，但下界不能低于目录页之后：序章的小节会把游标留在
            # 目录之前，于是第 1 章会误命中目录页里那条同名目录行（踩过）。
            p = find_in(title, max(cursor, toc_page + 1), n)
        if p is None:
            continue
        cursor = p
        toc.append([level, title, p])
    if not toc:
        print("⚠ 一个标题都没定位到，跳过书签")
        return

    doc.set_toc(toc)
    print(f"  ✓ 书签 {len(toc)} 条（一级 {sum(1 for t in toc if t[0] == 1)} 章）")

    # 反向核对：目录页上印的页码必须和书签定位到的章首页一致。
    # 这两个数字来自两套独立逻辑（文本层锚点 vs 标题定位），
    # 不一致说明至少一套错了——不核对就会把错页码静静印在书上。
    printed = dict(re.findall(r"(\S[^\n]*?)\s+(\d{1,3})\s*$", pages[toc_page], re.M))
    mism = []
    for level, title, target in toc:
        if level != 1:
            continue
        for row, no in printed.items():
            if title in row and no.isdigit() and int(no) != target:
                mism.append(f"{title[:18]}：目录印 {no}，实际在第 {target} 页")
    if mism:
        print("⚠ 目录页码与书签页码不一致：")
        for m in mism:
            print("  -", m)

    # 目录条目 → 内部跳转。
    # 逐条调用 page.insert_link 时，同一页上只有最后一个会被保留
    # （PyMuPDF 1.28 实测：插 4 条只剩 1 条）。必须先把链接串全部构造好，
    # 再用一次 _addAnnot_FromString 写进去。
    import pymupdf.utils as putils
    page = doc[toc_page - 1]
    annots = []
    for level, title, target in toc:
        if level != 1 or target == toc_page:
            continue                    # 目录里只有章条目，小节不列
        for r in page.search_for(title):
            annots.append(putils.getLinkText(
                page, {"kind": pymupdf.LINK_GOTO, "from": r, "page": target - 1}))
    if annots:
        page._addAnnot_FromString(tuple(annots))
    print(f"  ✓ 目录页 {len(annots)} 个跳转链接")

    try:
        doc.save(pdf, incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    except Exception as e:                      # 增量保存失败就整份重写
        print(f"  增量保存不可用（{e}），改为整份重写")
        tmp = pdf + ".tmp"
        doc.save(tmp)
        doc.close()
        os.replace(tmp, pdf)
        return
    doc.close()


def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    builder, html, pdf = sys.argv[1:4]
    if "--check-only" in sys.argv:
        selfcheck(pdf, html); return

    anchors = load_anchors(resolve_toc_json(html))
    if not anchors:
        print("⚠ 没有章节锚点，跳过目录页码回填（渲染继续，但目录会停在初始页码）")
        subprocess.run([sys.executable, builder], check=True)
        asyncio.run(_render(html, pdf, REPORT_TITLE))
        selfcheck(pdf, html)
        add_navigation(pdf, html)
        return
    for round_no in range(1, 6):
        subprocess.run([sys.executable, builder], check=True)
        asyncio.run(_render(html, pdf, REPORT_TITLE))
        found, n = locate(pdf, anchors)
        missing = [k for k, _ in anchors if k not in found]
        if missing:
            print(f"⚠ 第 {round_no} 轮未定位到：{missing}")
        if not found:
            print(f"⚠ 第 {round_no} 轮一个章节都没定位到——不会回填，也不算收敛")
            break
        if not patch_toc(builder, found):
            print(f"第 {round_no} 轮：目录页码已收敛（{n} 页）")
            break
        print(f"第 {round_no} 轮：回填页码 {found}")
    else:
        print("⚠ 5 轮仍未收敛")

    selfcheck(pdf, html)
    add_navigation(pdf, html)


if __name__ == "__main__":
    main()
