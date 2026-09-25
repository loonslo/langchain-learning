# -*- coding: utf-8 -*-
"""逐页自检：把 PDF 每页渲成 PNG，并拼成 12 页一张的检查表。

用法：
    python sheet.py 报告.pdf [起始页] [结束页]

输出到 自检/ 下：p-XX.png（单页，100dpi）与 sheet-N.png（检查表）。
排版缺陷不是均匀分布的——集中在最复杂的那几页（长表、宽图、附录），
所以每一页都要进过眼睛，只是分辨率分两档。
"""
import os, sys
import pymupdf
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "自检")
COLS, ROWS = 4, 3
TW = 430          # 每格缩略图宽度
LABEL_H = 18


def main():
    pdf = sys.argv[1]
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 6
    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(pdf)
    n = doc.page_count
    hi = min(hi, n)

    thumbs = []
    for pno in range(lo, hi + 1):
        pix = doc[pno - 1].get_pixmap(dpi=100)
        p = os.path.join(OUT, f"p-{pno:02d}.png")
        pix.save(p)
        thumbs.append((pno, p))

    for i in range(0, len(thumbs), COLS * ROWS):
        chunk = thumbs[i:i + COLS * ROWS]
        ims = []
        for pno, p in chunk:
            im = Image.open(p).convert("RGB")
            h = int(im.height * TW / im.width)
            ims.append((pno, im.resize((TW, h), Image.LANCZOS)))
        cw, ch = TW, max(im.height for _, im in ims) + LABEL_H
        sheet = Image.new("RGB", (cw * COLS, ch * ROWS), "white")
        d = ImageDraw.Draw(sheet)
        for k, (pno, im) in enumerate(ims):
            r, c = divmod(k, COLS)
            x, y = c * cw, r * ch
            d.rectangle([x, y, x + cw - 1, y + im.height + LABEL_H - 1],
                        outline="#bbbbbb")
            d.text((x + 6, y + 4), f"P{pno}", fill="#c0392b")
            sheet.paste(im, (x, y + LABEL_H))
        out = os.path.join(OUT, f"sheet-{i // (COLS * ROWS) + 1}.png")
        sheet.save(out)
        print("已生成", out, f"（第 {chunk[0][0]}–{chunk[-1][0]} 页）")
    print(f"共 {n} 页，单页 PNG 在 {OUT}")


if __name__ == "__main__":
    main()
