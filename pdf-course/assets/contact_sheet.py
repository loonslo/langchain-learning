#!/usr/bin/env python3
"""把 PDF 每页渲成 PNG，并拼成检查表——供逐页目视自检用。

为什么需要它：机械自检查不出「列缝粘连」「表格被切」「页眉丢失」这类缺陷，
必须把每页真的渲染出来用眼睛看（见 huashu-report 的 EYE_ONLY 清单）。
抽检对排版缺陷无效，所以要能低成本地扫完全部页。

用法：
    python contact_sheet.py "out/AI应用开发 零基础到交付.pdf" [--cols 3] [--rows 4] [--dpi 72]
产出：
    out/pages/pNN.png      每页单图（全尺寸，供放大细看）
    out/sheets/sheetN.png  拼版图（供整体扫）
"""
import os
import sys

import pymupdf
from PIL import Image, ImageDraw, ImageFont


def render_pages(pdf, outdir, dpi=110):
    os.makedirs(outdir, exist_ok=True)
    doc = pymupdf.open(pdf)
    paths = []
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(dpi=dpi)
        p = os.path.join(outdir, f"p{i + 1:03d}.png")
        pix.save(p)
        paths.append(p)
    return paths, doc.page_count


def sheet(paths, outdir, cols, rows, gap=10, label_h=22):
    os.makedirs(outdir, exist_ok=True)
    per = cols * rows
    sheets = []
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    for s in range((len(paths) + per - 1) // per):
        batch = paths[s * per:(s + 1) * per]
        ims = [Image.open(p).convert("RGB") for p in batch]
        w, h = ims[0].size
        W = cols * w + (cols + 1) * gap
        H = rows * (h + label_h) + (rows + 1) * gap
        canvas = Image.new("RGB", (W, H), (235, 235, 235))
        dr = ImageDraw.Draw(canvas)
        for k, im in enumerate(ims):
            r, c = divmod(k, cols)
            x = gap + c * (w + gap)
            y = gap + r * (h + label_h + gap)
            canvas.paste(im, (x, y))
            pno = s * per + k + 1
            dr.rectangle([x, y, x + w, y + h], outline=(150, 150, 150))
            dr.text((x + 4, y + h + 3), f"p{pno}", fill=(20, 20, 20), font=font)
        out = os.path.join(outdir, f"sheet{s + 1}.png")
        canvas.save(out)
        sheets.append(out)
    return sheets


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    pdf = sys.argv[1]

    def opt(name, default):
        return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default

    cols, rows, dpi = opt("--cols", 3), opt("--rows", 4), opt("--dpi", 72)
    here = os.path.dirname(os.path.abspath(pdf))
    paths, n = render_pages(pdf, os.path.join(here, "pages"), dpi=110)
    sheets = sheet(paths, os.path.join(here, "sheets"), cols, rows, )
    print(f"  已渲 {n} 页 → {os.path.join(here, 'pages')}")
    for s in sheets:
        print(f"  拼版 → {s}")


if __name__ == "__main__":
    main()
