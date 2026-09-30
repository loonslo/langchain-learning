#!/usr/bin/env python3
"""图元画廊：把 dia.py 的所有原语各画一遍，渲成一张 PNG 供目视检查。

用途：改 dia.py 之后先跑这个，确认图元本身没问题，再去改正文——
否则一个图元出错会污染几十张图，排查成本高得多。

用法：
    python tools/dia_gallery.py            # 产出 out/gallery.html + out/gallery.png
"""
import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "content"))

import dia  # noqa: E402


def build():
    g = []
    g.append(dia.flow([
        ("问题", "用户输入"), ("检索", "找相关资料"),
        ("生成", "带着资料回答"), ("引用", "标出来源"),
    ], note="横向流程：步骤 ≤ 4 个时用这个。"))

    g.append(dia.flow([
        ("第一步：把用户的问题做向量化", "Embedding"),
        ("第二步：在向量库里找最接近的若干块", "top-k 检索"),
        ("第三步：把找到的块拼进提示词", "拼上下文"),
    ], direction="v", note="纵向流程：步骤多、文字长时用这个。"))

    g.append(dia.loop([
        ("想：我该做什么", "推理"), ("做：调一个工具", "行动"),
        ("看：工具返回什么", "观察"),
    ], center="再想一次，直到不需要工具为止",
       note="循环图：表达「一轮一轮转」的过程。"))

    g.append(dia.loop([
        ("模型给候选块打分", ""), ("按分数取前几名", ""),
        ("把结果交给下一环", ""), ("下一环再筛一次", ""),
    ], center="rerank 就是在这个环里再筛一遍",
       note="步骤 4 个时也稳（一排 + 底部回环）。"))

    g.append(dia.layers([
        ("接口层", "验身份、限流、幂等"),
        ("业务层", "检索、生成、工具调用"),
        ("数据层", "向量库、订单库、会话表"),
    ], note="分层图：表达职责边界。", tone={"idx": [0], "color": dia.ACCENT}))

    g.append(dia.compare(
        ("向量检索", ["按语义找，能命中同义说法", "对专有名词、编号不敏感", "需要模型算向量"]),
        ("关键词检索 BM25", ["按字面匹配，专有名词很准", "同义说法完全找不到", "不需要模型，很快"]),
        note="对比图：两种做法各有取舍时用这个。"))

    g.append(dia.states([
        ("已提交", "任务收到了"), ("处理中", "正在做", "轮询"),
        ("完成", "有结果了", "成功"), ("失败", "给得出原因", "出错"),
    ], note="状态图：表达有生命周期的任务。", tone={"idx": [3], "color": dia.ACCENT}))

    g.append(dia.timeline([
        ("阶段 1", "把产品立起来", "知识问答 + 查订单"),
        ("阶段 2", "做成能上线的服务", "身份、幂等、观测"),
        ("阶段 3", "交付与演示", "压测、备份、前端"),
    ], note="时间轴：表达分阶段演进。"))

    g.append(dia.seq(["客服 Agent", "订单 Agent"], [
        (0, 1, "委托：查订单 A12345"), (1, 0, "需要补充信息", True),
        (0, 1, "补上订单号"), (1, 0, "返回订单状态", True),
    ], note="序列图：表达跨服务来回。"))

    g.append(dia.bars([
        ("只调模型一次", 30, "30ms"),
        ("加一次向量检索", 95, "95ms"),
        ("加一次重排序 rerank", 260, "260ms"),
    ], note="量级图：让数字的大小关系一眼可见。"))

    g.append(dia.cards([
        ("幻觉", "模型编出不存在的事实"),
        ("越权", "拿到了不该看的数据"),
        ("注入", "文档里藏指令被照着执行"),
        ("漂移", "改了 A 处，B 处悄悄变坏"),
    ], cols=2, note="卡片网格：并列的几类问题。"))

    g.append(dia.stack([
        ("排队", 12), ("检索", 22), ("重排", 30), ("生成", 36),
    ], note="堆叠条：一次请求的耗时构成。"))

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>
body{{font-family:'Microsoft YaHei',sans-serif;margin:12mm;background:#fff;color:#231f20}}
h3{{font-size:13pt;color:#14505e;border-top:1px solid #d8d8d8;padding-top:6mm;margin:10mm 0 4mm}}
.figbody svg{{display:block;width:100%;height:auto}}
.figtitle{{font-size:11pt;font-weight:700;margin:0 0 1.6mm}}
</style></head><body>
<h1 style="font-size:18pt">图元画廊</h1>
{''.join(f'<h3>图元 {i + 1}</h3><figure class="fig"><div class="figbody">{s}</div></figure>'
         for i, s in enumerate(g))}
</body></html>"""
    out_html = os.path.join(ROOT, "out", "gallery.html")
    open(out_html, "w", encoding="utf-8").write(html)
    return out_html, os.path.join(ROOT, "out", "gallery.png")


async def shoot(html, png):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": 900, "height": 1200})
        await pg.goto("file://" + os.path.abspath(html).replace("\\", "/"),
                      wait_until="networkidle")
        await pg.screenshot(path=png, full_page=True)
        # 逐个图元单独截图：整页缩略图看不清图内文字是否溢出画布，
        # 而 SVG 内部溢出几何自检量不到，只能放大看。
        figs = await pg.query_selector_all("figure.fig")
        d = os.path.join(os.path.dirname(png), "gallery")
        os.makedirs(d, exist_ok=True)
        for i, f in enumerate(figs, 1):
            await f.screenshot(path=os.path.join(d, f"g{i:02d}.png"))
        print(f"  单图 → {d}（{len(figs)} 张）")
        await b.close()


if __name__ == "__main__":
    h, png = build()
    asyncio.run(shoot(h, png))
    print(f"  画廊 HTML → {h}")
    print(f"  画廊 PNG  → {png}")
