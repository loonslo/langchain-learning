#!/usr/bin/env python3
"""插图体检：用浏览器实测每张图里每个 <text> 的外接框，判断是否超出画布。

为什么必须单独做这一层：SVG 的 text **不会自动换行**，中文标签写长了就会冲出画布。
而这类溢出发生在 SVG 内部，版心几何自检（量的是整页留白）完全看不见，
整页缩略图也看不出来——只有把每个 text 的外接框量出来才查得到。

同时量三件事：
  1. 文字是否超出 viewBox（画布）边界
  2. 文字是否超出所在的圆角矩形（框内溢出）
  3. 整张图的高度是否超过一页可用高度（否则会被分页切断）

用法：
    python tools/fig_check.py out/tutorial.html
"""
import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# A4 可用高度：297mm - 上下页边距（17mm + 15mm），再减掉页眉页脚
PAGE_USABLE_MM = 297 - 17 - 15
MM_PER_PX = 25.4 / 96.0

JS = r"""
() => {
  const out = [];
  const figs = document.querySelectorAll('svg.dia');
  figs.forEach((svg, i) => {
    const vb = svg.getAttribute('viewBox').split(/\s+/).map(Number);
    const [, , vw, vh] = vb;
    const sr = svg.getBoundingClientRect();
    const scale = sr.width / vw;                 // 用户单位 → CSS px
    const bad = [];
    const boxes = [];
    svg.querySelectorAll('text').forEach(t => {
      const r = t.getBoundingClientRect();
      // 转回用户单位（相对画布左上角）
      const x0 = (r.left - sr.left) / scale;
      const x1 = (r.right - sr.left) / scale;
      const y0 = (r.top - sr.top) / scale;
      const y1 = (r.bottom - sr.top) / scale;
      const txt = (t.textContent || '').slice(0, 22);
      if (x0 < -1.5 || x1 > vw + 1.5 || y0 < -1.5 || y1 > vh + 1.5) {
        bad.push({kind: 'canvas', txt,
                  box: [x0, y0, x1, y1].map(v => Math.round(v * 10) / 10)});
      }
      boxes.push({txt, x0, y0, x1, y1});
    });
    // 文字互相重叠：多行文本换行后撞上下面一行，是图元高度写死的典型症状
    for (let a = 0; a < boxes.length; a++) {
      for (let b = a + 1; b < boxes.length; b++) {
        const A = boxes[a], B = boxes[b];
        const ox = Math.min(A.x1, B.x1) - Math.max(A.x0, B.x0);
        const oy = Math.min(A.y1, B.y1) - Math.max(A.y0, B.y0);
        if (ox > 1.5 && oy > 1.5) {
          bad.push({kind: 'overlap', txt: A.txt + ' ✕ ' + B.txt,
                    box: [Math.round(ox * 10) / 10, Math.round(oy * 10) / 10]});
        }
      }
    }
    out.push({i: i + 1, vw, vh, w: Math.round(sr.width), h: Math.round(sr.height),
              bad});
  });
  return out;
}
"""


async def run(html):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": 900, "height": 1200})
        await pg.goto("file://" + os.path.abspath(html).replace("\\", "/"),
                      wait_until="networkidle")
        data = await pg.evaluate(JS)
        await b.close()
    return data


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    data = asyncio.run(run(sys.argv[1]))
    print(f"共 {len(data)} 张图")
    issues = 0
    for d in data:
        # 图上实际渲染高度（mm）：用户单位高度 × 缩放比 × px→mm
        h_mm = d["h"] * MM_PER_PX
        if h_mm > PAGE_USABLE_MM:
            print(f"  ⚠ 图 {d['i']}：高 {h_mm:.0f}mm > 一页可用 {PAGE_USABLE_MM:.0f}mm，会被分页切断")
            issues += 1
        for bd in d["bad"]:
            print(f"  ⚠ 图 {d['i']}：文字「{bd['txt']}」超出画布 {bd['box']}（画布 {d['vw']}×{d['vh']}）")
            issues += 1
    print("✓ 插图体检通过" if not issues else f"✗ 发现 {issues} 处问题")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
