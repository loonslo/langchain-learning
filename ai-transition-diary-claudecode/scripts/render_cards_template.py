#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转行日记 — 小红书学习卡片渲染模板（每天复用）

用法：
  1. 只改下面 ===== 每天编辑区 ===== 的 DAY / DATE / OUTDIR 和 D（内容）。
  2. 其余渲染逻辑、配色、布局、署名都已固定，无需改动。
  3. 运行： python render_cards_template.py
  4. 图片输出到 OUTDIR，文件名形如 {DATE}-AI-Day{DAY}-0N-xxx.png，最后一张固定为 glossary。

风格约定（与 SKILL.md / style-checklist.md 一致）：
  - 图里只放“框体 + 流程”，不放代码块（完整代码只在 Word 附件）。
  - 沿用/之前讲过的部分 kind="fade"（灰化 + “沿用”标签）；
    今天新增/重点 kind="now"（彩色高亮 + “今天重点/今天新增”标签）。
  - 竖版 3:4、米白网格纸、深灰字、蓝/青/绿区分色；红绿只用于前后对比图。
  - 彩框内强调用左侧色条，禁止彩框套白框；盒内文字垂直居中。
  - 封面左上“转行日记 · DayN” + 紧跟 @handle；每张内容图角落带淡署名。
  - 保存前做基础边界检查，发现文字或卡片越界就报错。
"""
import os
from PIL import Image, ImageDraw, ImageFont

# ===================== 每天编辑区 =====================
DAY   = 14
DATE  = "2026-06-24"
HANDLE= "@测试阿甲"
SERIES= "转行日记"
OUTDIR= os.environ.get("OUTDIR", ".")  # 设成当天 dayN 文件夹

D = {
    # 封面
    "cover": {
        "title": ["RAG 总搜不到", "答案怎么办?"],
        "subtitle": ["可能是问题问得太短，", "搜之前先把问题改一改"],
        # 底部横向流程带（短问题 -> 改写 -> 命中），3 个节点
        "band": [("向量怎么存", "原问题 · 太短", "red"),
                 ("改写成多条", "查询改写", "blue"),
                 ("√ 命中正文", "搜到了", "green")],
        "footer": "提问的词，和资料里的词，经常对不上",
    },
    # 定位图：今天补在哪（旧步骤 fade，今天 now）
    "pipeline": {
        "kicker": ("今天的重点", "blue"),
        "title": "改动加在哪一步",
        "lead": "灰色是前几天就搭好的，今天只在“提问”之后加一层。",
        "steps": [  # (title, desc, kind, color, tag)
            ("提问", "你问一句话", "plain", "ink", None),
            ("查询改写", "把问题改写得更好搜", "now", "blue", "今天新增"),
            ("检索 · 向量库", "FAISS、Embedding", "fade", None, "沿用"),
            ("AI 回答", "照着检索到的段落作答", "fade", None, "沿用"),
        ],
        "footer": "每天图里只点亮当天新增的那一层",
    },
    # 前后对比图（唯一允许红/绿双色对比的卡）
    "compare": {
        "kicker": ("改写前 vs 改写后", "blue"),
        "title": "同一个问题，搜到的不一样",
        "left":  {"head": "原问题直接搜",
                  "rows": [("问：", None), ("向量怎么存", "bar"),
                           ("资料里写的是：", None), ("“向量的持久化方式”", "bar")],
                  "result": ["结果", "× 词对不上，漏了"]},
        "right": {"head": "改写后再搜",
                  "rows": [("LLM 改写成：", None),
                           ("如何存储向量", "bar"), ("向量的持久化方式", "bar"),
                           ("向量数据怎么保存", "bar"), ("分别去搜，再合并", None)],
                  "result": ["结果", "√ 命中了正文"]},
        "footer": "问题不变，换个说法去搜，答案就找回来了",
    },
    # 做法图（每个新方法一张，纯流程无代码）
    "methods": [
        {"kicker": ("做法一 · Multi-Query", "blue"),
         "title": "让问题多几种说法",
         "lead": "把一个问题交给 LLM 改写成好几条，分别去搜再合并。说法多了，更容易碰上对的那段。",
         "rows": [("沿用：base_ret 检索器", "昨天就搭好的向量检索", "fade", None, "沿用"),
                  ("LLM 把问题改写成多条", "向量怎么存 → 多种说法", "now", "blue", "今天重点"),
                  ("分别检索后合并去重", "召回更全的相关片段", "plain", "teal", None)],
         "footer": "一个问题扩成好几个，召回机会翻倍"},
        {"kicker": ("做法二 · HyDE", "green"),
         "title": "先编个答案，再去搜",
         "lead": "不拿问题去搜，先让 LLM 假装回答一遍，再拿这段假答案去搜。它更像资料正文，比口语问句更好对上。",
         "rows": [("沿用：同一个检索器", "还是昨天的 base_ret", "fade", None, "沿用"),
                  ("先让 LLM 假装答一遍", "造一段“假答案”", "now", "green", "今天重点"),
                  ("拿假答案去检索", "更像正文，更易命中", "plain", "teal", None)],
         "footer": "用“像正文的假答案”去搜，比口语问句更准"},
    ],
    # 最后一张：关键知识点小词典（必须保留）
    "glossary": {
        "kicker": ("关键知识点", "teal"),
        "title": "本节小结",
        "lead": "先分清这些名字各自解决哪一步问题，回看代码时更容易对上。",
        "items": [
            ("MultiQueryRetriever", "把一个问题改写成多条，再分别去检索。", "blue"),
            ("HyDE", "先生成一段像答案的文字，再拿它去找资料。", "green"),
            ("base_ret", "前面已经搭好的基础检索器，今天继续沿用。", "teal"),
        ],
        "footer": "术语不用硬背，先记住它解决了哪一步的问题",
    },
}
# =================== 每天编辑区结束 ===================

W, H = 1080, 1440; MARGIN = 40
BG=(246,244,237); GRID=(228,224,213); CARD=(255,255,255)
INK=(31,41,51); MUTE=(107,114,128)
BLUE=(37,99,235); BLUE_BG=(232,238,252)
TEAL=(13,148,136); TEAL_BG=(222,241,238)
RED=(214,74,74); RED_BG=(250,232,232)
GREEN=(22,140,90); GREEN_BG=(226,244,235)
FADE_BG=(238,239,241); FADE_INK=(160,165,172)
SIGN=(190,194,200); DARK=(20,26,34)
COLORS={"blue":(BLUE,BLUE_BG),"teal":(TEAL,TEAL_BG),"green":(GREEN,GREEN_BG),
        "red":(RED,RED_BG),"ink":(INK,(241,242,244))}
FONT_REGULAR_CANDIDATES=[
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_BOLD_CANDIDATES=[
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]
def _first_font(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No CJK font found. Install Noto Sans CJK or Microsoft YaHei.")
NOTO=_first_font(FONT_REGULAR_CANDIDATES)
NOTOB=_first_font(FONT_BOLD_CANDIDATES)
def _pick(p,want="SC"):
    for i in range(0,12):
        try:
            f=ImageFont.truetype(p,24,index=i); n=" ".join(f.getname())
            if want in n and "Mono" not in n: return i
        except Exception: break
    return 0
IDX_R=_pick(NOTO); IDX_B=_pick(NOTOB)
def font(s,b=False): return ImageFont.truetype(NOTOB if b else NOTO,s,index=IDX_B if b else IDX_R)
def lh(f): a,d=f.getmetrics(); return a+d
def canvas():
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    for x in range(0,W,36): d.line([(x,0),(x,H)],fill=GRID,width=1)
    for y in range(0,H,36): d.line([(0,y),(W,y)],fill=GRID,width=1)
    d.rounded_rectangle([MARGIN,MARGIN,W-MARGIN,H-MARGIN],radius=34,fill=CARD)
    return img,d
def assert_inside(inner, outer, label):
    ix0,iy0,ix1,iy1=inner; ox0,oy0,ox1,oy1=outer
    if ix0 < ox0 or iy0 < oy0 or ix1 > ox1 or iy1 > oy1:
        raise ValueError(f"{label} out of bounds: {inner} not inside {outer}")
def rr(d,box,r,fill=None):
    assert_inside(box,[MARGIN,MARGIN,W-MARGIN,H-MARGIN],"rounded box")
    d.rounded_rectangle(box,radius=r,fill=fill)
def tw(d,s,f): b=d.textbbox((0,0),s,font=f); return b[2]-b[0]
def chip(d,x,y,label,fg,bg,fs=30):
    f=font(fs,True); px,py=24,12; w=tw(d,label,f); th=lh(f)
    box=[x,y,x+w+px*2,y+th+py*2]; rr(d,box,(th+py*2)//2,bg)
    assert_inside([x+px,y+py,x+px+w,y+py+th],box,"chip text")
    d.text((x+px,y+py),label,font=f,fill=fg,anchor="la"); return y+th+py*2
def tag(d,xr,yc,text,fg,bg):
    f=font(24,True); w=tw(d,text,f); h=lh(f)+14
    rr(d,[xr-w-28,yc-h//2,xr,yc+h//2],h//2,bg)
    d.text((xr-w-14,yc),text,font=f,fill=fg,anchor="lm")
def wrap(d,s,f,maxw):
    out,cur=[],""
    for ch in s:
        if ch=="\n": out.append(cur); cur=""; continue
        if tw(d,cur+ch,f)<=maxw: cur+=ch
        else: out.append(cur); cur=ch
    if cur: out.append(cur)
    return out
def para(d,x,y,s,f,fill,maxw,gap=None):
    step=lh(f)+(gap if gap is not None else int(f.size*0.35))
    for ln in wrap(d,s,f,maxw):
        assert_inside([x,y,x+tw(d,ln,f),y+lh(f)],[CX0,MARGIN,CX1,H-MARGIN],"paragraph text")
        d.text((x,y),ln,font=f,fill=fill,anchor="la"); y+=step
    return y
def vblock(d,x,top,bottom,items,gap=12):
    hs=[lh(it[1]) for it in items]; total=sum(hs)+gap*(len(items)-1)
    y=top+((bottom-top)-total)//2
    for (t,f,fill),h in zip(items,hs): d.text((x,y),t,font=f,fill=fill,anchor="la"); y+=h+gap
def bar_line(d,x,y,text,f,barcol,textcol):
    h=lh(f); rr(d,[x,y+4,x+7,y+h-4],4,barcol)
    d.text((x+22,y),text,font=f,fill=textcol,anchor="la"); return y+h
def footer(d,text):
    f=font(30,True); bx0,bx1=MARGIN+24,W-MARGIN-24; th=lh(f)
    by1=H-MARGIN-28; by0=by1-(th+40); rr(d,[bx0,by0,bx1,by1],22,DARK)
    d.text(((bx0+bx1)//2,(by0+by1)//2),text,font=f,fill=(255,255,255),anchor="mm")
def sign(d):
    f=font(26,True); yc=MARGIN+56+(lh(font(30,True))+24)//2
    d.text((CX1,yc),HANDLE,font=f,fill=SIGN,anchor="rm")
def save(img,n): p=os.path.join(OUTDIR,n); img.save(p); print("saved",p)
CX0=MARGIN+30; CX1=W-MARGIN-30; CW=CX1-CX0

def flowbox(d,y,bh,title,desc,kind,color,tag_txt):
    if kind=="fade": bg=FADE_BG; tcol=FADE_INK; dcol=FADE_INK
    else: acc,accbg=COLORS[color or "blue"]; bg=accbg; tcol=acc; dcol=INK
    rr(d,[CX0,y,CX1,y+bh],18,bg)
    vblock(d,CX0+30,y,y+bh,[(title,font(34,True),tcol),(desc,font(28),dcol)],12)
    if tag_txt:
        if kind=="fade": tag(d,CX1-22,y+bh//2,tag_txt,FADE_INK,(230,231,233))
        else: tag(d,CX1-22,y+bh//2,tag_txt,tcol,(255,255,255))
    return y+bh
def arrow(d,y): d.text(((CX0+CX1)//2,y+22),"↓",font=font(36,True),fill=MUTE,anchor="mm"); return y+46

def render_cover():
    img,d=canvas(); c=D["cover"]
    y=MARGIN+70; top=y; lbl=f"{SERIES} · Day{DAY}"; ch_b=chip(d,CX0,y,lbl,TEAL,TEAL_BG,30)
    chip_r=CX0+tw(d,lbl,font(30,True))+48
    d.text((chip_r+26,(top+ch_b)//2),HANDLE,font=font(28,True),fill=MUTE,anchor="lm")
    y=MARGIN+230; f1=font(94,True)
    for ln in c["title"]: d.text((CX0,y),ln,font=f1,fill=INK,anchor="la"); y+=118
    y+=22; f2=font(40,True)
    for ln in c["subtitle"]: d.text((CX0,y),ln,font=f2,fill=BLUE,anchor="la"); y+=64
    bandtop=MARGIN+700; bh=300; aw=64; nw=(CW-aw*2)//3; x=CX0
    for i,(t,sub,col) in enumerate(c["band"]):
        acc,accbg=COLORS[col]; rr(d,[x,bandtop,x+nw,bandtop+bh],22,accbg)
        cx=x+nw//2; cy=bandtop+bh//2
        d.text((cx,cy-26),t,font=font(34,True),fill=acc,anchor="mm")
        d.text((cx,cy+34),sub,font=font(25),fill=MUTE,anchor="mm")
        x+=nw
        if i<len(c["band"])-1: d.text((x+aw//2,cy),"→",font=font(48,True),fill=MUTE,anchor="mm"); x+=aw
    footer(d,c["footer"]); save(img,f"{DATE}-AI-Day{DAY}-01-cover.png")

def render_pipeline():
    img,d=canvas(); p=D["pipeline"]; klab,kcol=p["kicker"]; acc,accbg=COLORS[kcol]
    y=MARGIN+56; chip(d,CX0,y,klab,acc,accbg,30); sign(d); y+=100
    d.text((CX0,y),p["title"],font=font(58,True),fill=INK,anchor="la"); y+=92
    y=para(d,CX0,y,p["lead"],font(31),MUTE,CW); y+=28
    bh=118
    for i,(t,sub,kind,col,tg) in enumerate(p["steps"]):
        y=flowbox(d,y,bh,t,sub,kind,col,tg)
        if i<len(p["steps"])-1: y=arrow(d,y)
    footer(d,p["footer"]); save(img,f"{DATE}-AI-Day{DAY}-02-pipeline.png")

def render_compare():
    img,d=canvas(); c=D["compare"]; klab,kcol=c["kicker"]; acc,accbg=COLORS[kcol]
    y=MARGIN+56; chip(d,CX0,y,klab,acc,accbg,30); sign(d); y+=100
    d.text((CX0,y),c["title"],font=font(50,True),fill=INK,anchor="la"); y+=112
    colw=(CW-30)//2; lx0=CX0; rx0=CX0+colw+30; ct=y; colh=760; pad=34
    rr(d,[lx0,ct,lx0+colw,ct+colh],22,RED_BG); rr(d,[rx0,ct,rx0+colw,ct+colh],22,GREEN_BG)
    d.text((lx0+pad,ct+28),c["left"]["head"],font=font(32,True),fill=RED,anchor="la")
    d.text((rx0+pad,ct+28),c["right"]["head"],font=font(32,True),fill=GREEN,anchor="la")
    mid_y=ct+colh-176
    def col(x0,spec,accent):
        yy=ct+108
        for txt,style in spec["rows"]:
            if style=="bar": yy=bar_line(d,x0+pad,yy,txt,font(30,True),accent,INK); yy+=20
            else: d.text((x0+pad,yy),txt,font=font(27),fill=MUTE,anchor="la"); yy+=46
        vblock(d,x0+pad,mid_y,ct+colh-24,
               [(spec["result"][0],font(29,True),accent),(spec["result"][1],font(31,True),accent)],14)
    col(lx0,c["left"],RED); col(rx0,c["right"],GREEN)
    footer(d,c["footer"]); save(img,f"{DATE}-AI-Day{DAY}-03-compare.png")

def render_methods():
    for idx,m in enumerate(D["methods"]):
        img,d=canvas(); klab,kcol=m["kicker"]; acc,accbg=COLORS[kcol]
        y=MARGIN+56; chip(d,CX0,y,klab,acc,accbg,30); sign(d); y+=100
        d.text((CX0,y),m["title"],font=font(56,True),fill=INK,anchor="la"); y+=92
        y=para(d,CX0,y,m["lead"],font(33),MUTE,CW); y+=30
        bh=140
        for i,(t,sub,kind,col,tg) in enumerate(m["rows"]):
            y=flowbox(d,y,bh,t,sub,kind,col,tg)
            if i<len(m["rows"])-1: y=arrow(d,y)
        footer(d,m["footer"])
        save(img,f"{DATE}-AI-Day{DAY}-{idx+4:02d}-method.png")


def render_glossary():
    g=D["glossary"]; img,d=canvas(); klab,kcol=g["kicker"]; acc,accbg=COLORS[kcol]
    y=MARGIN+56; chip(d,CX0,y,klab,acc,accbg,30); sign(d); y+=100
    title_font=font(58,True); d.text((CX0,y),g["title"],font=title_font,fill=INK,anchor="la")
    assert_inside([CX0,y,CX0+tw(d,g["title"],title_font),y+lh(title_font)],[CX0,MARGIN,CX1,H-MARGIN],"glossary title")
    y+=92
    y=para(d,CX0,y,g["lead"],font(31),MUTE,CW); y+=30
    items=g["items"]
    available=H-MARGIN-150-y
    gap=24
    bh=min(150, max(112, (available-gap*(len(items)-1))//max(1,len(items))))
    for term,desc,col in items:
        acc,accbg=COLORS[col]
        rr(d,[CX0,y,CX1,y+bh],18,accbg)
        rr(d,[CX0+24,y+28,CX0+32,y+bh-28],4,acc)
        vblock(d,CX0+54,y,y+bh,[(term,font(32,True),acc),(desc,font(27),INK)],10)
        y+=bh+gap
    footer(d,g["footer"])
    idx=len(D["methods"])+4
    save(img,f"{DATE}-AI-Day{DAY}-{idx:02d}-glossary.png")

if __name__=="__main__":
    os.makedirs(OUTDIR,exist_ok=True)
    render_cover(); render_pipeline(); render_compare(); render_methods(); render_glossary()
    print("done.")
