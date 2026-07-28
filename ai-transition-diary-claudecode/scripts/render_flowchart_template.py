#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代码流程图解模版 (Code Flowchart) for 转行日记.

真实节点名 + 图例 + 编号流程说明 + 循环示意，横版 3:2，Mermaid 风格。
用法：把本文件复制进 dayN/，只编辑底部的 `SCENES` 数据块（节点/边/图例/流程说明/
循环或要点面板），然后运行：

    OUTDIR=<dayN> python render_flowchart_template.py

引擎（ENGINE 以下）固定：调色板、节点/菱形/胶囊画法、边自动贴框、箭头、图例条、
面板与循环示意、标题换行、边界与碰撞审计都由引擎处理。审计失败时修正 SCENES，
不要关闭审计或改引擎绕过问题。

每个 scene 画一张图，对应当天代码里的一个 build_*/图函数。节点用真实函数/节点名
（START/agent/tools_condition/tools/END 等）。边可给 `via` 折点做条件分支或回边。
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

# ============================================================================
# ENGINE — 固定。调色板、画法、自动贴框、图例、面板、循环示意。
# ============================================================================
W, H = 1560, 1075
BG=(250,250,252); INK=(45,55,72); SUB=(107,114,128); PANEL_B=(176,182,194)
ACC=(37,99,180)
SAFE_X0, SAFE_X1 = 32, W-32
TITLE_TOP, TITLE_MAX_W = 24, 1320
FLOW_Y0, FLOW_Y1 = 630, 955
LEGEND_Y0, LEGEND_Y1 = 968, 1052
BLUE=((219,234,254),(59,130,246)); YEL=((254,243,199),(217,145,11))
PUR=((238,222,255),(147,51,234));  GRN=((187,247,208),(34,160,84))
RED=((254,202,202),(224,72,72));   ORG=((255,235,210),(226,98,26))
NOTE=((254,249,195),(180,130,10))

def _ff(c):
    for p in c:
        if os.path.exists(p): return p
    return None
_R=_ff(["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf","C:/Windows/Fonts/msyh.ttc","/System/Library/Fonts/PingFang.ttc"])
_B=_ff(["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc","C:/Windows/Fonts/msyhbd.ttc","C:/Windows/Fonts/simhei.ttf"]) or _R
_fc={}
def font(s,bold=False):
    k=(s,bold)
    if k not in _fc: _fc[k]=ImageFont.truetype(_B if bold else _R, s)
    return _fc[k]

def new_canvas():
    img=Image.new("RGB",(W,H),BG); return img, ImageDraw.Draw(img)

def ctext(d,cx,cy,lines,fnt,fill,leading=1.25):
    if isinstance(lines,str): lines=[lines]
    asc,desc=fnt.getmetrics(); lh=int((asc+desc)*leading); y=cy-lh*len(lines)/2
    for ln in lines:
        w=d.textlength(ln,font=fnt); d.text((cx-w/2,y),ln,font=fnt,fill=fill); y+=lh

def wrap(d,text,fnt,maxw):
    toks=[]; run=""
    for ch in text:
        if ord(ch)>0x2E80 or ch in "，。、：（）→/·":
            if run: toks.append(run); run=""
            toks.append(ch)
        elif ch==" ":
            if run: toks.append(run); run=""
            toks.append(" ")
        else: run+=ch
    if run: toks.append(run)
    lines=[]; cur=""
    for t in toks:
        if d.textlength(cur+t,font=fnt)<=maxw or not cur: cur+=t
        else: lines.append(cur); cur="" if t==" " else t
    if cur: lines.append(cur)
    return lines

def _line_height(fnt, leading=1.25):
    asc,desc=fnt.getmetrics(); return int((asc+desc)*leading)

def _centered_text_boxes(d,cx,cy,lines,fnt,leading=1.25,pad=0):
    if isinstance(lines,str): lines=[lines]
    lh=_line_height(fnt,leading); y=cy-lh*len(lines)/2; boxes=[]
    for ln in lines:
        box=d.textbbox((0,0),ln,font=fnt); w=box[2]-box[0]; h=box[3]-box[1]
        boxes.append((cx-w/2-pad,y+box[1]-pad,cx+w/2+pad,y+box[3]+pad))
        y+=lh
    return boxes

def _rect(n,pad=0):
    return (n["x"]-n["w"]/2-pad,n["y"]-n["h"]/2-pad,
            n["x"]+n["w"]/2+pad,n["y"]+n["h"]/2+pad)

def _overlap(a,b):
    return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])

def _point_in_rect(p,r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]

def _orient(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def _segments_intersect(a,b,c,d):
    o1,o2,o3,o4=_orient(a,b,c),_orient(a,b,d),_orient(c,d,a),_orient(c,d,b)
    if o1==0 and min(a[0],b[0])<=c[0]<=max(a[0],b[0]) and min(a[1],b[1])<=c[1]<=max(a[1],b[1]): return True
    if o2==0 and min(a[0],b[0])<=d[0]<=max(a[0],b[0]) and min(a[1],b[1])<=d[1]<=max(a[1],b[1]): return True
    if o3==0 and min(c[0],d[0])<=a[0]<=max(c[0],d[0]) and min(c[1],d[1])<=a[1]<=max(c[1],d[1]): return True
    if o4==0 and min(c[0],d[0])<=b[0]<=max(c[0],d[0]) and min(c[1],d[1])<=b[1]<=max(c[1],d[1]): return True
    return (o1>0)!=(o2>0) and (o3>0)!=(o4>0)

def _segment_hits_rect(a,b,r):
    if _point_in_rect(a,r) or _point_in_rect(b,r): return True
    x0,y0,x1,y1=r
    return any(_segments_intersect(a,b,c,d) for c,d in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))])

def _title_layout(d,title):
    fnt=font(42,bold=True); lines=wrap(d,title,fnt,TITLE_MAX_W)
    if len(lines)>2:
        raise ValueError(f"title needs more than 2 lines: {title!r}")
    lh=_line_height(fnt,1.18); cy=TITLE_TOP+lh*len(lines)/2
    boxes=_centered_text_boxes(d,W/2,cy,lines,fnt,1.18,6)
    if any(b[0]<SAFE_X0 or b[2]>SAFE_X1 for b in boxes):
        raise ValueError(f"title exceeds safe frame: {title!r}")
    return lines,fnt,cy,max(b[3] for b in boxes)

def _node_text_spec(d,n):
    """Return draw specs that fit the actual node interior, including diamonds."""
    shape=n.get("shape","box")
    if shape=="pill":
        sizes=[(30,False,None),(27,False,None),(24,False,None),(21,False,None)]
    elif shape=="box":
        sizes=[(30,False,21),(27,False,19),(24,False,18),(21,False,16),(18,False,14)]
    else:
        sizes=[(24,False,16),(22,False,15),(20,False,14),(18,False,13),(16,False,12)]
    title=n["title"]; sub=n.get("sub")
    for ts,_,ss in sizes:
        tf=font(ts,bold=True); sf=font(ss) if sub and ss else None
        if sub:
            tcy=n["y"]-12; scy=n["y"]+16
            specs=[(title,tf,tcy),(sub,sf,scy)]
        else:
            specs=[(title,tf,n["y"])]
        boxes=[]
        for text,fnt,cy in specs: boxes += _centered_text_boxes(d,n["x"],cy,[text],fnt,1.15,5)
        if shape=="diamond":
            hw,hh=n["w"]/2,n["h"]/2; ok=True
            for b in boxes:
                far_y=max(abs(b[1]-n["y"]),abs(b[3]-n["y"]))
                allowed=hw*(1-far_y/hh)-8
                if allowed<=0 or max(abs(b[0]-n["x"]),abs(b[2]-n["x"]))>allowed: ok=False
            if ok: return specs,boxes
        else:
            r=_rect(n,0)
            if all(b[0]>=r[0]+8 and b[2]<=r[2]-8 and b[1]>=r[1]+6 and b[3]<=r[3]-6 for b in boxes):
                return specs,boxes
    raise ValueError(f"node text does not fit {shape} {n['title']!r}; shorten text or enlarge node")

def _ah(d,x,y,ang,color,size=15,width=4):
    for da in (math.radians(148),math.radians(-148)):
        d.line([(x,y),(x+size*math.cos(ang+da),y+size*math.sin(ang+da))],fill=color,width=width)

def poly_arrow(d,pts,color=INK,width=4):
    d.line(pts,fill=color,width=width,joint="curve")
    (x0,y0),(x1,y1)=pts[-2],pts[-1]
    _ah(d,x1,y1,math.atan2(y1-y0,x1-x0),color,width=width)

def label(d,cx,cy,text,fnt,color=INK,halo=BG):
    if isinstance(text,str): text=[text]
    asc,desc=fnt.getmetrics(); lh=int((asc+desc)*1.15)
    wmax=max(d.textlength(t,font=fnt) for t in text); tot=lh*len(text)
    d.rectangle((cx-wmax/2-6,cy-tot/2-2,cx+wmax/2+6,cy+tot/2+2),fill=halo)
    y=cy-tot/2
    for t in text:
        w=d.textlength(t,font=fnt); d.text((cx-w/2,y),t,font=fnt,fill=color); y+=lh

def dashed_rect(d,x0,y0,x1,y1,color,dash=13,gap=9,width=2,r=18):
    def seg(a,b):
        x,y=a; ex,ey=b; L=math.hypot(ex-x,ey-y)
        if L==0: return
        ux,uy=(ex-x)/L,(ey-y)/L; p=0
        while p<L:
            sx,sy=x+ux*p,y+uy*p; e=min(p+dash,L)
            d.line([(sx,sy),(x+ux*e,y+uy*e)],fill=color,width=width); p+=dash+gap
    seg((x0+r,y0),(x1-r,y0)); seg((x0+r,y1),(x1-r,y1)); seg((x0,y0+r),(x0,y1-r)); seg((x1,y0+r),(x1,y1-r))
    for ax,ay,s,e in [(x0+r,y0+r,180,270),(x1-r,y0+r,270,360),(x1-r,y1-r,0,90),(x0+r,y1-r,90,180)]:
        d.arc((ax-r,ay-r,ax+r,ay+r),s,e,fill=color,width=width)

def _pill(d,n):
    f,b=n["pal"]; x,y,w,h=n["x"],n["y"],n["w"],n["h"]
    d.rounded_rectangle((x-w/2,y-h/2,x+w/2,y+h/2),radius=h/2,fill=f,outline=b,width=4)
    specs,_=_node_text_spec(d,n)
    for text,fnt,cy in specs: ctext(d,x,cy,[text],fnt,INK if text==n["title"] else SUB,leading=1.15)
def _box(d,n):
    f,b=n["pal"]; x,y,w,h=n["x"],n["y"],n["w"],n["h"]
    d.rounded_rectangle((x-w/2,y-h/2,x+w/2,y+h/2),radius=n.get("r",16),fill=f,outline=b,width=4)
    specs,_=_node_text_spec(d,n)
    for text,fnt,cy in specs: ctext(d,x,cy,[text],fnt,INK if text==n["title"] else SUB,leading=1.15)
def _diamond(d,n):
    f,b=n["pal"]; x,y,w,h=n["x"],n["y"],n["w"],n["h"]
    pts=[(x,y-h/2),(x+w/2,y),(x,y+h/2),(x-w/2,y)]; d.polygon(pts,fill=f); d.line(pts+[pts[0]],fill=b,width=4)
    specs,_=_node_text_spec(d,n)
    for text,fnt,cy in specs: ctext(d,x,cy,[text],fnt,INK if text==n["title"] else SUB,leading=1.15)
def draw_node(d,n):
    {"pill":_pill,"box":_box,"diamond":_diamond}[n["shape"]](d,n)

def anchor(n,tx,ty):
    """节点边界上朝向 (tx,ty) 的点，让箭头正好贴框。"""
    cx,cy=n["x"],n["y"]; hw,hh=n["w"]/2,n["h"]/2; dx,dy=tx-cx,ty-cy
    if dx==0 and dy==0: return cx,cy
    if n["shape"]=="diamond": t=1.0/(abs(dx)/hw+abs(dy)/hh)
    else: t=1.0/max(abs(dx)/hw,abs(dy)/hh)
    return cx+dx*t, cy+dy*t

def _edge_points(nodes,e):
    A=nodes[e["a"]]; B=nodes[e["b"]]; via=e.get("via",[])
    p0=anchor(A,*(via[0] if via else (B["x"],B["y"])))
    p1=anchor(B,*(via[-1] if via else (A["x"],A["y"])))
    return [p0]+via+[p1]

def _edge_label_geometry(d,nodes,e):
    if not e.get("label"): return None
    pts=_edge_points(nodes,e)
    if "lx" in e: lx,ly=e["lx"],e["ly"]
    else: lx,ly=(pts[0][0]+pts[1][0])/2,(pts[0][1]+pts[1][1])/2-22
    lines=e["label"] if isinstance(e["label"],list) else [e["label"]]
    fnt=font(23); lh=_line_height(fnt,1.15)
    w=max(d.textlength(t,font=fnt) for t in lines); h=lh*len(lines)
    return lx,ly,(lx-w/2-8,ly-h/2-5,lx+w/2+8,ly+h/2+5)

def draw_edge(d,nodes,e):
    pts=_edge_points(nodes,e)
    poly_arrow(d,pts,e.get("color",INK))
    if e.get("label"):
        lx,ly,_=_edge_label_geometry(d,nodes,e)
        label(d,lx,ly,e["label"],font(23),e.get("lcol",INK))

def collision_audit(d,sc):
    errors=[]; nodes=sc["nodes"]
    try: _,_,_,title_bottom=_title_layout(d,sc["title"])
    except ValueError as exc: errors.append(str(exc)); title_bottom=110

    node_items=list(nodes.items())
    for nid,n in node_items:
        r=_rect(n)
        if r[0]<SAFE_X0 or r[2]>SAFE_X1 or r[1]<title_bottom+18 or r[3]>FLOW_Y0-14:
            errors.append(f"node {nid!r} leaves main-flow safe area or touches title/panels: {r}")
        try: _node_text_spec(d,n)
        except ValueError as exc: errors.append(f"node {nid!r}: {exc}")
    for i,(aid,a) in enumerate(node_items):
        for bid,b in node_items[i+1:]:
            if _overlap(_rect(a,6),_rect(b,6)): errors.append(f"nodes overlap: {aid!r} and {bid!r}")

    note_rects=[]
    for i,nt in enumerate(sc.get("notes",[]),1):
        r=(nt["x"]-nt["w"]/2,nt["y"]-nt["h"]/2,nt["x"]+nt["w"]/2,nt["y"]+nt["h"]/2)
        note_rects.append(r)
        if r[0]<SAFE_X0 or r[2]>SAFE_X1 or r[1]<title_bottom+12 or r[3]>FLOW_Y0-14:
            errors.append(f"note {i} leaves main-flow safe area: {r}")
        boxes=_centered_text_boxes(d,nt["x"],nt["y"],nt["text"],font(22),1.25,5)
        if any(b[0]<r[0]+8 or b[2]>r[2]-8 or b[1]<r[1]+6 or b[3]>r[3]-6 for b in boxes):
            errors.append(f"note {i} text overflows its frame")
        for nid,n in node_items:
            if _overlap(r,_rect(n,6)): errors.append(f"note {i} overlaps node {nid!r}")

    all_segments=[]; label_boxes=[]
    for i,e in enumerate(sc["edges"],1):
        if e.get("a") not in nodes or e.get("b") not in nodes:
            errors.append(f"edge {i} references unknown node"); continue
        pts=_edge_points(nodes,e); segs=list(zip(pts,pts[1:])); all_segments.extend((i,a,b) for a,b in segs)
        for nid,n in node_items:
            if nid in (e["a"],e["b"]): continue
            if any(_segment_hits_rect(a,b,_rect(n,5)) for a,b in segs):
                errors.append(f"edge {i} crosses unrelated node {nid!r}")
        geo=_edge_label_geometry(d,nodes,e)
        if geo:
            _,_,box=geo
            if box[0]<SAFE_X0 or box[2]>SAFE_X1 or box[1]<title_bottom+8 or box[3]>FLOW_Y0-8:
                errors.append(f"edge {i} label leaves safe area: {box}")
            for nid,n in node_items:
                if _overlap(box,_rect(n,5)): errors.append(f"edge {i} label overlaps node {nid!r}")
            label_boxes.append((i,box))
    for i,(aid,a) in enumerate(label_boxes):
        for bid,b in label_boxes[i+1:]:
            if _overlap(a,b): errors.append(f"edge labels overlap: {aid} and {bid}")
    for eid,box in label_boxes:
        expanded=(box[0]-6,box[1]-6,box[2]+6,box[3]+6)
        for sid,a,b in all_segments:
            if _segment_hits_rect(a,b,expanded): errors.append(f"edge {eid} label touches arrow segment from edge {sid}")

    if errors:
        joined="\n  - ".join(errors)
        raise ValueError(f"layout audit failed for {sc.get('name','<scene>')}:\n  - {joined}")

def legend_bar(d,items):
    y0,y1=LEGEND_Y0,LEGEND_Y1; dashed_rect(d,40,y0,1520,y1,PANEL_B)
    f=font(24); bf=font(24,bold=True); cy=(y0+y1)/2
    seg=[(sh,pal,lab,64+d.textlength(lab,font=f)) for sh,pal,lab in items]
    lead=d.textlength("图例：",font=bf)+16; total=sum(x[3] for x in seg)+46*(len(seg)-1)+lead
    content_x0,content_x1=58,1375
    if total>content_x1-content_x0:
        raise ValueError("legend is too wide; shorten labels")
    x=content_x0+(content_x1-content_x0-total)/2; d.text((x,cy-16),"图例：",font=bf,fill=INK); x+=lead
    for sh,pal,lab,w in seg:
        fl,b=pal; cx=x+28
        if sh=="box": d.rounded_rectangle((cx-28,cy-16,cx+28,cy+16),radius=8,fill=fl,outline=b,width=3)
        elif sh=="diamond":
            pts=[(cx,cy-18),(cx+28,cy),(cx,cy+18),(cx-28,cy)]; d.polygon(pts,fill=fl); d.line(pts+[pts[0]],fill=b,width=3)
        else: d.rounded_rectangle((cx-28,cy-15,cx+28,cy+15),radius=15,fill=fl,outline=b,width=3)
        d.text((x+64,cy-15),lab,font=f,fill=INK); x+=w+46
    sig="@测试阿甲"; sf=font(18); sw=d.textlength(sig,font=sf)
    d.text((1498-sw,cy-12),sig,font=sf,fill=(160,165,176))

def flow_panel(d,x0,y0,x1,y1,items):
    dashed_rect(d,x0,y0,x1,y1,PANEL_B)
    d.text((x0+26,y0+16),"流程说明",font=font(27,bold=True),fill=ACC)
    yy=y0+60; fnt=font(20); numf=font(20,bold=True)
    for i,(col,text) in enumerate(items,1):
        cx=x0+38; cy=yy+15
        d.ellipse((cx-16,cy-16,cx+16,cy+16),outline=col,width=3)
        nw=d.textlength(str(i),font=numf); d.text((cx-nw/2,cy-14),str(i),font=numf,fill=col)
        lines=wrap(d,text,fnt,x1-x0-108); ty=cy-len(lines)*26/2+1
        for ln in lines: d.text((x0+68,ty),ln,font=fnt,fill=INK); ty+=26
        yy+=max(40,len(lines)*26+8)
    if yy>y1-14: raise ValueError(f"flow panel overflow: bottom={yy:.0f}, limit={y1-14}")

def loop_panel(d,x0,y0,x1,y1,spec):
    dashed_rect(d,x0,y0,x1,y1,PANEL_B)
    d.text((x0+26,y0+16),"循环示意（可能多轮）",font=font(27,bold=True),fill=ACC)
    (an,ap),(bn,bp)=spec["a"],spec["b"]; lcx=x0+120; ay=y0+96; by=y0+200
    _box(d,{"x":lcx,"y":ay,"w":150,"h":58,"pal":ap,"title":an,"r":12})
    _box(d,{"x":lcx,"y":by,"w":150,"h":58,"pal":bp,"title":bn,"r":12})
    poly_arrow(d,[(lcx-78,ay+8),(lcx-112,ay+26),(lcx-112,by-26),(lcx-78,by-8)],INK,3)
    poly_arrow(d,[(lcx+78,by-8),(lcx+112,by-26),(lcx+112,ay+26),(lcx+78,ay+8)],INK,3)
    ty=y0+92; tf=font(18)
    for t in spec.get("trace",[]):
        lines=wrap(d,t,tf,x1-(x0+250)-20)
        for ln in lines: d.text((x0+250,ty),ln,font=tf,fill=INK); ty+=24
        ty+=2
    if ty>y1-58: raise ValueError(f"loop trace overflow: bottom={ty:.0f}, limit={y1-58}")
    if spec.get("note"):
        lines=wrap(d,spec["note"],font(20),x1-x0-52)
        if len(lines)>1: raise ValueError("loop note is too long; shorten it")
        d.text((x0+26,y1-40),lines[0],font=font(20),fill=SUB)

def note_panel(d,x0,y0,x1,y1,spec):
    dashed_rect(d,x0,y0,x1,y1,PANEL_B)
    d.text((x0+26,y0+16),spec["title"],font=font(27,bold=True),fill=ACC)
    yy=y0+62; lf=font(21)
    for ln in spec.get("lines",[]):
        lines=wrap(d,ln,lf,x1-x0-52)
        for row in lines: d.text((x0+26,yy),row,font=lf,fill=INK); yy+=30
        yy+=8
    for text,pal in spec.get("cards",[]):
        yy+=8; _box(d,{"x":(x0+x1)/2,"y":yy+34,"w":x1-x0-100,"h":70,"pal":pal,"title":text,"r":12}); yy+=82
    if yy>y1-14: raise ValueError(f"note panel overflow: bottom={yy:.0f}, limit={y1-14}")

def draw_dashnote(d,nt):
    x,y,w,h=nt["x"],nt["y"],nt["w"],nt["h"]
    dashed_rect(d,x-w/2,y-h/2,x+w/2,y+h/2,NOTE[1])
    ctext(d,x,y,nt["text"],font(22),INK)
    tx,ty=nt["to"]; d.line([(x,y+h/2),(tx,ty-24)],fill=NOTE[1],width=3); _ah(d,tx,ty-24,math.pi/2,NOTE[1],width=3)

def render_scene(sc,outdir):
    img,d=new_canvas()
    collision_audit(d,sc)
    title_lines,title_font,title_cy,_=_title_layout(d,sc["title"])
    ctext(d,W/2,title_cy,title_lines,title_font,INK,leading=1.18)
    for nt in sc.get("notes",[]): draw_dashnote(d,nt)
    for e in sc["edges"]: draw_edge(d,sc["nodes"],e)
    for n in sc["nodes"].values(): draw_node(d,n)
    flow_panel(d,40,FLOW_Y0,1000,FLOW_Y1,sc["flow"])
    side=sc["side"]
    (loop_panel if side["type"]=="loop" else note_panel)(d,1040,FLOW_Y0,1520,FLOW_Y1,side)
    legend_bar(d,sc["legend"])
    p=os.path.join(outdir,f"{sc['name']}.png"); img.save(p); print("saved",p)

def main():
    outdir=os.environ.get("OUTDIR","."); os.makedirs(outdir,exist_ok=True)
    for sc in SCENES: render_scene(sc,outdir)
    # contact sheet is QA-only; include every scene, two columns.
    tw=760; th=int(tw*H/W); cols=2; rows=max(1,math.ceil(len(SCENES)/cols))
    sheet=Image.new("RGB",(tw*cols+30,th*rows+10*(rows+1)),(255,255,255))
    for i,sc in enumerate(SCENES):
        im=Image.open(os.path.join(outdir,f"{sc['name']}.png")).resize((tw,th))
        r,c=divmod(i,cols); sheet.paste(im,(10+c*(tw+10),10+r*(th+10)))
    cs=os.path.join(outdir,f"{PREFIX}-flow-contact-sheet.png"); sheet.save(cs); print("saved",cs)
    print(f"\nOK: rendered {len(SCENES)} flowcharts.")

# ============================================================================
# DATA — 只改这里。DAY/DATE + SCENES（每张一个 scene）。
# 示例内容是 Day31（节点容错与重试）的四张：build_fallback / build_retry /
# build_tool_safe / with_timeout。换成当天代码里的真实图。
# ============================================================================
DAY=os.environ.get("DAY","31")
DATE=os.environ.get("DATE","2026-07-16")
PREFIX=f"{DATE}-AI-Day{DAY}"

SCENES=[
{ "name":f"{PREFIX}-flow-1-fallback",
  "title":"build_fallback() 流程图 · 节点级 try/except 降级",
  "legend":[("pill",GRN,"入口/出口"),("box",BLUE,"节点 (Node)"),("diamond",YEL,"条件判断 (try/except)"),("box",ORG,"降级出口")],
  "nodes":{
    "start":{"x":150,"y":340,"w":150,"h":72,"shape":"pill","pal":GRN,"title":"START"},
    "fetch":{"x":440,"y":340,"w":220,"h":96,"shape":"box","pal":BLUE,"title":"fetch 节点","sub":"执行 flaky_fetch()"},
    "cond":{"x":760,"y":340,"w":250,"h":150,"shape":"diamond","pal":YEL,"title":"外部调用成功?","sub":"try 正常 / except 异常"},
    "ok":{"x":1120,"y":205,"w":250,"h":96,"shape":"box","pal":GRN,"title":"返回真实数据","sub":"{result: data}"},
    "deg":{"x":1120,"y":475,"w":270,"h":104,"shape":"box","pal":ORG,"title":"返回降级值","sub":"（降级）稍后再试"},
    "end":{"x":1420,"y":340,"w":140,"h":72,"shape":"pill","pal":RED,"title":"END"},
  },
  "edges":[
    {"a":"start","b":"fetch","label":"进入","lx":278,"ly":295},
    {"a":"fetch","b":"cond"},
    {"a":"cond","b":"ok","via":[(760,205)],"label":"是（try）","lcol":GRN[1],"lx":870,"ly":158},
    {"a":"cond","b":"deg","via":[(760,475)],"label":"否","lcol":ORG[1],"lx":930,"ly":430},
    {"a":"ok","b":"end"},{"a":"deg","b":"end"},
  ],
  "flow":[(GRN[1],"START：图的入口"),(BLUE[1],"fetch 节点：调用可能失败的外部服务 flaky_fetch()"),
    (YEL[1],"外部调用成功？try 正常拿到数据；except 捕获异常"),(GRN[1],"成功 → 返回真实数据 {result: data}"),
    (ORG[1],"失败 → 不 re-raise，返回降级但可用的值，图继续往下"),(RED[1],"END：无论成功失败，图都正常结束，不崩")],
  "side":{"type":"note","title":"核心要点","lines":["except 里不 re-raise 是关键：","异常被吞掉并换成降级值，","整张图照常走到 END，","用户至少拿到可用回复，","而不是一个 500。"]},
},
{ "name":f"{PREFIX}-flow-2-retry",
  "title":"build_retry() 流程图 · RetryPolicy 瞬时错误自动重试",
  "legend":[("pill",GRN,"入口/出口"),("box",BLUE,"节点 (Node)"),("diamond",YEL,"条件判断"),("box",RED,"失败出口")],
  "nodes":{
    "start":{"x":140,"y":250,"w":150,"h":72,"shape":"pill","pal":GRN,"title":"START"},
    "work":{"x":410,"y":250,"w":220,"h":96,"shape":"box","pal":BLUE,"title":"work 节点","sub":"sometimes_fails()"},
    "condA":{"x":720,"y":250,"w":240,"h":150,"shape":"diamond","pal":YEL,"title":"抛可重试异常?","sub":"Timeout/Connection"},
    "ok":{"x":1010,"y":150,"w":230,"h":88,"shape":"box","pal":GRN,"title":"成功，拿到结果"},
    "end":{"x":1360,"y":250,"w":140,"h":72,"shape":"pill","pal":RED,"title":"END"},
    "condB":{"x":720,"y":480,"w":240,"h":150,"shape":"diamond","pal":YEL,"title":"重试次数 < 3?","sub":"max_attempts=3"},
    "fail":{"x":1050,"y":480,"w":240,"h":96,"shape":"box","pal":RED,"title":"达上限，抛出"},
  },
  "edges":[
    {"a":"start","b":"work","label":"进入","lx":256,"ly":200},
    {"a":"work","b":"condA"},
    {"a":"condA","b":"ok","via":[(1010,250)],"label":"否","lcol":GRN[1],"lx":868,"ly":200},
    {"a":"ok","b":"end"},
    {"a":"condA","b":"condB","label":"是","lcol":YEL[1],"lx":765,"ly":363},
    {"a":"condB","b":"fail","label":"否","lcol":RED[1],"lx":885,"ly":430},
    {"a":"condB","b":"work","via":[(410,480)],"label":"是","lcol":BLUE[1],"lx":500,"ly":430},
  ],
  "flow":[(BLUE[1],"work 节点：挂了 RetryPolicy(max_attempts=3)"),(YEL[1],"抛的是可重试异常吗？限流/超时/连接抖动才算"),
    (YEL[1],"是 → 看重试次数 < 3；否（成功）→ 直接继续"),(BLUE[1],"没到上限 → 框架自动重试，回到 work"),
    (RED[1],"到上限还失败 → 抛出（该失败就快速失败）")],
  "side":{"type":"loop","a":("work",BLUE),"b":("重试",YEL),"note":"框架自动重试到成功",
    "trace":["第1次：超时抛错 → 重试","第2次：超时抛错 → 重试","第3次：成功 → 拿到结果"]},
},
{ "name":f"{PREFIX}-flow-3-tool_safe",
  "title":"build_tool_safe() 流程图 · agent↔tools + 工具报错回喂",
  "legend":[("pill",GRN,"入口/出口"),("box",BLUE,"节点 (Node)"),("diamond",YEL,"条件判断 (Condition)"),("box",PUR,"工具节点 (ToolNode)")],
  "notes":[{"x":450,"y":176,"w":390,"h":112,"text":["LLM 调用失败 → try/except","返回降级 AIMessage（不崩图）"],"to":(440,340)}],
  "nodes":{
    "start":{"x":140,"y":340,"w":150,"h":72,"shape":"pill","pal":GRN,"title":"START"},
    "agent":{"x":440,"y":340,"w":220,"h":100,"shape":"box","pal":BLUE,"title":"agent (LLM 节点)","sub":"内部 try/except 降级"},
    "cond":{"x":780,"y":340,"w":260,"h":150,"shape":"diamond","pal":YEL,"title":"tools_condition","sub":"要调用工具吗?"},
    "end":{"x":1400,"y":340,"w":150,"h":72,"shape":"pill","pal":RED,"title":"END"},
    "tools":{"x":780,"y":560,"w":270,"h":100,"shape":"box","pal":PUR,"title":"tools (ToolNode)","sub":"handle_tool_errors=True"},
  },
  "edges":[
    {"a":"start","b":"agent","label":"进入","lx":272,"ly":295},
    {"a":"agent","b":"cond"},
    {"a":"cond","b":"end","label":["否","（不需要工具）"],"lx":1120,"ly":285},
    {"a":"cond","b":"tools","label":"是（需要工具）","lcol":PUR[1],"lx":900,"ly":462},
    {"a":"tools","b":"agent","via":[(440,560)],"label":"回喂","lcol":PUR[1],"lx":520,"ly":510},
  ],
  "flow":[(BLUE[1],"agent 节点：调 LLM；try/except 兜底，LLM 挂了返回降级消息不崩"),
    (YEL[1],"tools_condition：LLM 输出里有工具调用 → 去 tools；否则 → END"),
    (PUR[1],"tools：ToolNode(handle_tool_errors=True)，工具抛错包成 ToolMessage"),
    (PUR[1],"报错/结果回喂 agent，模型看到错能换个参数或说法再来一次")],
  "side":{"type":"loop","a":("agent",BLUE),"b":("tools",PUR),"note":"工具报错也不崩，回喂后继续",
    "trace":["除零报错 → 包成消息回喂","模型自己改口 → 再答"]},
},
{ "name":f"{PREFIX}-flow-4-timeout",
  "title":"with_timeout() 流程图 · 超时护栏",
  "legend":[("pill",GRN,"入口/出口"),("box",BLUE,"步骤"),("diamond",YEL,"条件判断"),("box",ORG,"降级出口")],
  "nodes":{
    "start":{"x":150,"y":340,"w":150,"h":72,"shape":"pill","pal":GRN,"title":"开始调用"},
    "fn":{"x":450,"y":340,"w":220,"h":96,"shape":"box","pal":BLUE,"title":"执行 fn()","sub":"记录耗时"},
    "cond":{"x":780,"y":340,"w":250,"h":150,"shape":"diamond","pal":YEL,"title":"耗时 > 上限?","sub":"seconds 阈值"},
    "ok":{"x":1130,"y":205,"w":250,"h":96,"shape":"box","pal":GRN,"title":"返回真实结果"},
    "deg":{"x":1130,"y":475,"w":270,"h":104,"shape":"box","pal":ORG,"title":"返回 on_timeout","sub":"缓存/降级数据"},
    "end":{"x":1420,"y":340,"w":140,"h":72,"shape":"pill","pal":RED,"title":"END"},
  },
  "edges":[
    {"a":"start","b":"fn","label":"调用","lx":282,"ly":295},
    {"a":"fn","b":"cond"},
    {"a":"cond","b":"ok","via":[(780,205)],"label":"否（快）","lcol":GRN[1],"lx":880,"ly":158},
    {"a":"cond","b":"deg","via":[(780,475)],"label":"是","lcol":ORG[1],"lx":945,"ly":430},
    {"a":"ok","b":"end"},{"a":"deg","b":"end"},
  ],
  "flow":[(BLUE[1],"执行 fn()，同时记录起止耗时"),(YEL[1],"耗时是否超过 seconds 上限？"),
    (GRN[1],"没超 → 返回真实结果"),(ORG[1],"超了 → 返回 on_timeout 降级值，别让慢调用拖垮整条请求")],
  "side":{"type":"note","title":"真实示例","lines":["阈值 seconds = 0.5s"],
    "cards":[("快调用 0.2s < 0.5s → 真实数据",GRN),("慢调用 1.5s > 0.5s → 降级",ORG)]},
},
]

if __name__=="__main__":
    main()
