#!/usr/bin/env python3
"""유튜브 챕터 인트로 4종 + 구독 아웃트로 4종 (흑백) — HyperFrames 프로젝트 생성·렌더·효과음 합성.

사용법:
  python3 build.py              # 8개 전부
  python3 build.py intro-v2     # 하나만
문구는 아래 TEXT만 바꾸면 된다.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(ROOT, "_shared", "node_modules")
OUT = os.path.join(ROOT, "out")

TEXT = {
    "chapter_label": "CHAPTER",
    "chapter_no": "01",
    "chapter_title": "핵심 정리",
    "outro_lead": "영상이 도움이 되셨다면",
    "sub": "구독",
    "like": "좋아요",
    "bell": "알림 설정",
}

BLACK, WHITE, GREY = "#0A0A0A", "#F5F5F5", "#8A8A8A"

# 아이콘 (Material Icons 경로)
THUMB = '<svg viewBox="0 0 24 24" class="ico"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>'
BELL = '<svg viewBox="0 0 24 24" class="ico"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>'
PLAY = '<svg viewBox="0 0 24 24" class="ico"><path d="M8 5v14l11-7z"/></svg>'


def chars(s, cls="ch"):
    return "".join(f'<span class="{cls}">{"&nbsp;" if c == " " else c}</span>' for c in s)


T = TEXT
VARIANTS = {}

# ───────────────────────── 챕터 인트로 (3초) ─────────────────────────

VARIANTS["intro-v1"] = dict(
    title="와이프 바", duration=3.0, desc="흰 바가 화면을 가르고 지나가 제목의 밑줄로 변신. 글자는 아래에서 위로 마스크 리빌.",
    sfx=[(0.0, "whoosh"), (0.62, "pop"), (2.45, "tick")],
    css=f"""
#root{{background:{BLACK};}}
.bar{{position:absolute;left:0;top:596px;height:8px;width:1920px;background:{WHITE};transform-origin:left center;}}
.wrap{{position:absolute;left:220px;top:390px;}}
.label{{font:500 34px Pretendard;letter-spacing:.42em;color:{GREY};}}
.label b{{color:{WHITE};font-weight:700;}}
.title{{margin-top:18px;font:900 190px/1 Pretendard;color:{WHITE};letter-spacing:-.03em;overflow:hidden;padding-bottom:8px;}}
.title .ch{{display:inline-block;}}
""",
    body=f"""
<div class="bar"></div>
<div class="wrap">
  <div class="label">{T['chapter_label']} <b>{T['chapter_no']}</b></div>
  <div class="title">{chars(T['chapter_title'])}</div>
</div>""",
    js="""
tl.fromTo('.bar',{x:-1920,scaleX:1},{x:0,duration:.42,ease:'expo.out'},0);
tl.to('.bar',{scaleX:.19,x:220,duration:.45,ease:'expo.inOut'},.42);
tl.to('.bar',{y:-262,duration:.35,ease:'power3.inOut'},.62);
tl.fromTo('.label',{opacity:0,y:20},{opacity:1,y:0,duration:.35,ease:'power3.out'},.55);
tl.fromTo('.title .ch',{yPercent:110},{yPercent:0,duration:.5,ease:'back.out(1.6)',stagger:.05},.6);
tl.fromTo('.wrap',{scale:1},{scale:1.03,duration:1.8,ease:'none',transformOrigin:'left center'},1.2);
tl.to('.bar',{scaleX:.42,duration:.4,ease:'power3.out'},2.4);
""",
)

VARIANTS["intro-v2"] = dict(
    title="빅 넘버", duration=3.0, desc="화면을 채운 외곽선 숫자 01이 내려앉고 아래에서 위로 검정으로 차오름. 옆으로 제목이 밀려 들어옴.",
    sfx=[(0.0, "hit"), (0.55, "whoosh"), (1.05, "pop")],
    css=f"""
#root{{background:{WHITE};}}
.num{{position:absolute;left:150px;top:150px;font:900 760px/1 Pretendard;letter-spacing:-.06em;}}
.num .o{{color:transparent;-webkit-text-stroke:5px {BLACK};}}
.num .f{{position:absolute;inset:0;color:{BLACK};clip-path:inset(100% 0 0 0);}}
.side{{position:absolute;left:1060px;top:410px;}}
.label{{font:700 34px Pretendard;letter-spacing:.42em;color:{BLACK};}}
.rule{{width:520px;height:6px;background:{BLACK};margin:22px 0 26px;transform-origin:left;}}
.title{{font:900 150px/1 Pretendard;color:{BLACK};letter-spacing:-.03em;overflow:hidden;}}
.title span{{display:inline-block;}}
""",
    body=f"""
<div class="num"><span class="o">{T['chapter_no']}</span><span class="f">{T['chapter_no']}</span></div>
<div class="side">
  <div class="label">{T['chapter_label']}</div>
  <div class="rule"></div>
  <div class="title"><span>{T['chapter_title']}</span></div>
</div>""",
    js="""
tl.fromTo('.num',{scale:1.9,opacity:0,transformOrigin:'30% 50%'},{scale:1,opacity:1,duration:.55,ease:'expo.out'},0);
tl.fromTo('.num .f',{clipPath:'inset(100% 0 0 0)'},{clipPath:'inset(0% 0 0 0)',duration:.6,ease:'power3.inOut'},.5);
tl.fromTo('.label',{opacity:0,x:40},{opacity:1,x:0,duration:.35,ease:'power3.out'},.85);
tl.fromTo('.rule',{scaleX:0},{scaleX:1,duration:.45,ease:'expo.out'},.9);
tl.fromTo('.title span',{xPercent:110},{xPercent:0,duration:.55,ease:'expo.out'},1.0);
tl.fromTo('.num',{x:0},{x:-30,duration:1.9,ease:'none'},1.1);
tl.fromTo('.side',{x:0},{x:20,duration:1.9,ease:'none'},1.1);
""",
)

VARIANTS["intro-v3"] = dict(
    title="반전 스플릿", duration=3.0, desc="흰 판이 화면을 가로지르며 글자 색을 실시간으로 뒤집음(흑↔백). 마지막엔 흰 화면에 검정 제목.",
    sfx=[(0.0, "whoosh"), (0.95, "whoosh"), (2.05, "hit")],
    css=f"""
#root{{background:{BLACK};}}
.panel{{position:absolute;top:0;left:0;height:1080px;width:960px;background:{WHITE};}}
.txt{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:{WHITE};mix-blend-mode:difference;}}
.label{{font:700 36px Pretendard;letter-spacing:.5em;margin-left:.5em;}}
.title{{font:900 230px/1.05 Pretendard;letter-spacing:-.03em;margin-top:10px;}}
.title .ch{{display:inline-block;}}
""",
    body=f"""
<div class="panel"></div>
<div class="txt">
  <div class="label">{T['chapter_label']} {T['chapter_no']}</div>
  <div class="title">{chars(T['chapter_title'])}</div>
</div>""",
    js="""
tl.fromTo('.panel',{x:-960},{x:0,duration:.5,ease:'expo.out'},0);
tl.fromTo('.title .ch',{opacity:0,scale:.6},{opacity:1,scale:1,duration:.4,ease:'back.out(2)',stagger:.05},.25);
tl.fromTo('.label',{opacity:0},{opacity:1,duration:.3},.4);
tl.to('.panel',{x:960,duration:.7,ease:'power4.inOut'},.95);
tl.to('.panel',{x:0,width:1920,duration:.6,ease:'expo.inOut'},2.0);
tl.fromTo('.txt',{scale:1},{scale:1.05,duration:2.4,ease:'none'},.6);
""",
)

GRID_V = "".join(f'<div class="gv" style="left:{x}px"></div>' for x in range(160, 1920, 320))
GRID_H = "".join(f'<div class="gh" style="top:{y}px"></div>' for y in range(180, 1080, 180))
VARIANTS["intro-v4"] = dict(
    title="그리드 카운터", duration=3.0, desc="격자가 그려지고 큰 번호가 00→01로 넘어가며, 제목 글자가 위에서 떨어져 안착. 하단 진행선.",
    sfx=[(0.15, "tick"), (0.3, "tick"), (0.45, "tick"), (0.7, "click"), (0.95, "pop"), (1.1, "pop")],
    css=f"""
#root{{background:{BLACK};}}
.gv{{position:absolute;top:0;width:1px;height:1080px;background:#262626;transform-origin:top;}}
.gh{{position:absolute;left:0;height:1px;width:1920px;background:#262626;transform-origin:left;}}
.counter{{position:absolute;left:160px;top:180px;height:360px;overflow:hidden;font:900 360px/1 Pretendard;color:{WHITE};letter-spacing:-.04em;font-variant-numeric:tabular-nums;}}
.counter .roll{{display:flex;flex-direction:column;}}
.label{{position:absolute;left:170px;top:146px;font:500 28px Pretendard;letter-spacing:.45em;color:{GREY};}}
.title{{position:absolute;left:160px;top:600px;font:900 200px/1 Pretendard;color:{WHITE};letter-spacing:-.03em;}}
.title .ch{{display:inline-block;}}
.prog{{position:absolute;left:160px;bottom:120px;width:1600px;height:4px;background:#262626;}}
.prog i{{position:absolute;inset:0;background:{WHITE};transform-origin:left;}}
""",
    body=f"""
{GRID_V}{GRID_H}
<div class="label">{T['chapter_label']}</div>
<div class="counter"><div class="roll"><span>00</span><span>{T['chapter_no']}</span></div></div>
<div class="title">{chars(T['chapter_title'])}</div>
<div class="prog"><i></i></div>""",
    js="""
tl.fromTo('.gv',{scaleY:0},{scaleY:1,duration:.5,ease:'power3.out',stagger:.04},0);
tl.fromTo('.gh',{scaleX:0},{scaleX:1,duration:.5,ease:'power3.out',stagger:.04},.05);
tl.fromTo('.label',{opacity:0},{opacity:1,duration:.3},.3);
tl.fromTo('.counter',{opacity:0},{opacity:1,duration:.15},.3);
tl.fromTo('.counter .roll',{y:0},{y:-360,duration:.45,ease:'expo.inOut'},.45);
tl.fromTo('.title .ch',{y:-160,opacity:0},{y:0,opacity:1,duration:.45,ease:'bounce.out',stagger:.07},.85);
tl.fromTo('.prog i',{scaleX:0},{scaleX:1,duration:2.8,ease:'none'},.2);
""",
)

# ───────────────────────── 구독 아웃트로 (5초) ─────────────────────────

CURSOR = '<svg class="cursor" viewBox="0 0 28 42"><polygon points="1,1 1,33 9,26 15,40 21,37 15,24 26,24" fill="#F5F5F5" stroke="#0A0A0A" stroke-width="2"/></svg>'
VARIANTS["outro-v1"] = dict(
    title="버튼 클릭", duration=5.0, desc="버튼 3개가 튀어나오고, 마우스 커서가 구독→좋아요→알림을 차례로 눌러 켜는 연출.",
    sfx=[(0.6, "pop"), (0.72, "pop"), (0.84, "pop"), (1.9, "click"), (2.8, "click"), (3.7, "click"), (3.75, "ding")],
    css=f"""
#root{{background:{BLACK};}}
.lead{{position:absolute;top:340px;width:1920px;text-align:center;font:700 72px Pretendard;color:{WHITE};letter-spacing:-.02em;}}
.row{{position:absolute;top:520px;width:1920px;display:flex;justify-content:center;gap:44px;}}
.btn{{position:relative;display:flex;align-items:center;gap:22px;height:132px;padding:0 60px;border-radius:66px;border:4px solid {WHITE};color:{WHITE};font:800 58px Pretendard;overflow:hidden;}}
.btn .fill{{position:absolute;inset:0;background:{WHITE};transform:scaleX(0);transform-origin:left;}}
.btn .lbl{{position:relative;display:flex;align-items:center;gap:22px;}}
.btn .ico{{width:58px;height:58px;fill:currentColor;}}
.btn.sub .alt{{position:absolute;left:0;top:0;opacity:0;}}
.cursor{{position:absolute;left:0;top:0;width:56px;height:84px;}}
""",
    body=f"""
<div class="lead">{T['outro_lead']}</div>
<div class="row">
  <div class="btn sub"><div class="fill"></div><div class="lbl">{PLAY}<span class="t1">{T['sub']}</span></div></div>
  <div class="btn like"><div class="fill"></div><div class="lbl">{THUMB}<span>{T['like']}</span></div></div>
  <div class="btn bell"><div class="fill"></div><div class="lbl">{BELL}<span>{T['bell']}</span></div></div>
</div>
{CURSOR}""",
    js="""
tl.fromTo('.lead',{opacity:0,y:30},{opacity:1,y:0,duration:.5,ease:'power3.out'},.15);
tl.fromTo('.btn',{scale:0,opacity:0},{scale:1,opacity:1,duration:.45,ease:'back.out(2.2)',stagger:.12},.6);
tl.fromTo('.cursor',{x:1500,y:1100},{x:620,y:610,duration:.7,ease:'power3.inOut'},1.15);
function press(sel,t){
  tl.to('.cursor',{scale:.82,duration:.08,yoyo:true,repeat:1,transformOrigin:'0 0'},t);
  tl.to(sel,{scale:.92,duration:.08,yoyo:true,repeat:1},t);
  tl.to(sel+' .fill',{scaleX:1,duration:.3,ease:'expo.out'},t+.05);
  tl.to(sel,{color:'#0A0A0A',duration:.1},t+.08);
}
press('.btn.sub',1.85);
tl.to('.btn.sub .t1',{text:'구독중',duration:0},1.95);
tl.to('.cursor',{x:1010,y:610,duration:.55,ease:'power3.inOut'},2.15);
press('.btn.like',2.75);
tl.fromTo('.btn.like .ico',{rotate:0},{rotate:-22,duration:.12,yoyo:true,repeat:1,transformOrigin:'50% 80%'},2.85);
tl.to('.cursor',{x:1420,y:610,duration:.55,ease:'power3.inOut'},3.05);
press('.btn.bell',3.65);
tl.fromTo('.btn.bell .ico',{rotate:0},{keyframes:[{rotate:18},{rotate:-16},{rotate:12},{rotate:-8},{rotate:0}],duration:.7,transformOrigin:'50% 10%'},3.72);
tl.to('.cursor',{x:1700,y:900,opacity:0,duration:.6,ease:'power2.in'},4.2);
""",
)

VARIANTS["outro-v2"] = dict(
    title="키네틱 타이포", duration=5.0, desc="'구독' '좋아요' '알림 설정'이 화면을 꽉 채우며 흑백 반전으로 연속 컷 → 마지막 한 줄 정리 화면.",
    sfx=[(0.0, "hit"), (0.85, "hit"), (1.7, "hit"), (2.6, "whoosh"), (3.1, "pop")],
    css=f"""
#root{{background:{WHITE};}}
.card{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:900 400px/1 Pretendard;letter-spacing:-.05em;opacity:0;}}
.c1{{background:{WHITE};color:{BLACK};}}
.c2{{background:{BLACK};color:{WHITE};}}
.c3{{background:{WHITE};color:{BLACK};font-size:330px;}}
.final{{position:absolute;inset:0;background:{BLACK};opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:{WHITE};}}
.final .lead{{font:500 52px Pretendard;color:{GREY};}}
.final .words{{margin-top:26px;font:900 130px/1 Pretendard;letter-spacing:-.03em;display:flex;gap:46px;align-items:center;}}
.final .dot{{width:22px;height:22px;border-radius:50%;background:{WHITE};}}
.final .ul{{margin-top:40px;width:1100px;height:8px;background:{WHITE};transform-origin:center;}}
""",
    body=f"""
<div class="card c1">{T['sub']}</div>
<div class="card c2">{T['like']}</div>
<div class="card c3">{T['bell']}</div>
<div class="final">
  <div class="lead">{T['outro_lead']}</div>
  <div class="words"><span class="w">{T['sub']}</span><i class="dot"></i><span class="w">{T['like']}</span><i class="dot"></i><span class="w">{T['bell']}</span></div>
  <div class="ul"></div>
</div>""",
    js="""
[['.c1',0],['.c2',.85],['.c3',1.7]].forEach(([s,t])=>{
  tl.set(s,{opacity:1},t);
  tl.fromTo(s,{scale:1.25,letterSpacing:'0.08em'},{scale:1,letterSpacing:'-0.05em',duration:.6,ease:'expo.out'},t);
});
tl.set('.final',{opacity:1},2.6);
tl.fromTo('.final',{clipPath:'circle(0% at 50% 50%)'},{clipPath:'circle(75% at 50% 50%)',duration:.5,ease:'expo.inOut'},2.6);
tl.fromTo('.final .lead',{opacity:0,y:20},{opacity:1,y:0,duration:.4},2.95);
tl.fromTo('.final .w, .final .dot',{opacity:0,y:60},{opacity:1,y:0,duration:.45,ease:'back.out(1.8)',stagger:.08},3.05);
tl.fromTo('.final .ul',{scaleX:0},{scaleX:1,duration:.6,ease:'expo.out'},3.5);
tl.fromTo('.final .words',{scale:1},{scale:1.03,duration:1.4,ease:'none'},3.6);
""",
)

VARIANTS["outro-v3"] = dict(
    title="엔드스크린 틀", duration=5.0, desc="유튜브 최종화면 요소(영상 2칸 + 구독 원) 자리를 선으로 그려 주는 실용형. 업로드 후 최종화면 요소를 이 위치에 맞추면 됨.",
    sfx=[(0.2, "whoosh"), (1.3, "pop"), (1.5, "pop"), (1.7, "pop")],
    css=f"""
#root{{background:{BLACK};}}
.lead{{position:absolute;left:150px;top:118px;font:800 64px Pretendard;color:{WHITE};letter-spacing:-.02em;}}
.lead small{{display:block;margin-top:10px;font:500 34px Pretendard;color:{GREY};letter-spacing:0;}}
svg.frames{{position:absolute;inset:0;width:1920px;height:1080px;}}
svg.frames rect,svg.frames circle{{fill:none;stroke:{WHITE};stroke-width:4;}}
.tag{{position:absolute;font:700 34px Pretendard;color:{WHITE};}}
.tag i{{display:inline-block;width:14px;height:14px;background:{WHITE};border-radius:50%;margin-right:14px;vertical-align:middle;}}
.ring{{position:absolute;left:1427px;top:448px;width:290px;height:290px;border-radius:50%;border:3px solid {WHITE};}}
.subtxt{{position:absolute;left:1422px;top:770px;width:300px;text-align:center;font:800 46px Pretendard;color:{WHITE};}}
.subico{{position:absolute;left:1522px;top:543px;width:100px;height:100px;fill:{WHITE};}}
""",
    body=f"""
<div class="lead">{T['outro_lead']}<small>{T['sub']} · {T['like']} · {T['bell']}</small></div>
<svg class="frames" viewBox="0 0 1920 1080">
  <rect class="r1" x="150" y="330" width="560" height="315" rx="14"/>
  <rect class="r2" x="760" y="330" width="560" height="315" rx="14"/>
  <circle class="c1" cx="1572" cy="593" r="145"/>
</svg>
<div class="tag t1" style="left:150px;top:672px"><i></i>다음 영상</div>
<div class="tag t2" style="left:760px;top:672px"><i></i>추천 영상</div>
<svg class="subico" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
<div class="ring"></div>
<div class="subtxt">{T['sub']}</div>""",
    js="""
['.r1','.r2'].forEach((s,i)=>{const L=2*(560+315);tl.fromTo(s,{strokeDasharray:L,strokeDashoffset:L},{strokeDashoffset:0,duration:.9,ease:'power2.inOut'},.2+i*.15);});
const C=2*Math.PI*145;tl.fromTo('.c1',{strokeDasharray:C,strokeDashoffset:C},{strokeDashoffset:0,duration:.9,ease:'power2.inOut'},.5);
tl.fromTo('.lead',{opacity:0,x:-40},{opacity:1,x:0,duration:.5,ease:'power3.out'},.1);
tl.fromTo('.tag',{opacity:0,y:16},{opacity:1,y:0,duration:.35,stagger:.2},1.3);
tl.fromTo('.subico',{scale:0},{scale:1,duration:.4,ease:'back.out(2.5)',transformOrigin:'50% 50%'},1.7);
tl.fromTo('.subtxt',{opacity:0},{opacity:1,duration:.3},1.8);
for(let k=0;k<3;k++){tl.fromTo('.ring',{scale:1,opacity:.9},{scale:1.35,opacity:0,duration:1,ease:'power2.out'},2.0+k*1.0);}
""",
)

VARIANTS["outro-v4"] = dict(
    title="벨 링 미니멀", duration=5.0, desc="흰 화면 중앙의 큰 종이 울리며 동심원이 퍼지고, 아래로 구독·좋아요·알림 설정 칩이 차례로 등장.",
    sfx=[(0.3, "pop"), (0.8, "ding"), (2.0, "pop"), (2.15, "pop"), (2.3, "pop")],
    css=f"""
#root{{background:{WHITE};}}
.bell{{position:absolute;left:810px;top:170px;width:300px;height:300px;fill:{BLACK};}}
.wave{{position:absolute;left:810px;top:170px;width:300px;height:300px;border-radius:50%;border:4px solid {BLACK};}}
.lead{{position:absolute;top:560px;width:1920px;text-align:center;font:800 76px Pretendard;color:{BLACK};letter-spacing:-.02em;}}
.chips{{position:absolute;top:700px;width:1920px;display:flex;justify-content:center;gap:30px;}}
.chip{{height:100px;padding:0 54px;border-radius:50px;background:{BLACK};color:{WHITE};font:700 48px/100px Pretendard;}}
.chip.o{{background:transparent;color:{BLACK};box-shadow:inset 0 0 0 4px {BLACK};}}
""",
    body=f"""
<div class="wave w1"></div><div class="wave w2"></div><div class="wave w3"></div>
<svg class="bell" viewBox="0 0 24 24"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>
<div class="lead">{T['outro_lead']}</div>
<div class="chips"><div class="chip">{T['sub']}</div><div class="chip o">{T['like']}</div><div class="chip o">{T['bell']}</div></div>""",
    js="""
tl.fromTo('.bell',{scale:0},{scale:1,duration:.5,ease:'back.out(2)',transformOrigin:'50% 50%'},.3);
tl.fromTo('.bell',{rotate:0},{keyframes:[{rotate:22},{rotate:-20},{rotate:15},{rotate:-10},{rotate:6},{rotate:0}],duration:1.1,ease:'power1.out',transformOrigin:'50% 8%'},.8);
['.w1','.w2','.w3'].forEach((s,i)=>tl.fromTo(s,{scale:.8,opacity:.6},{scale:2.1,opacity:0,duration:1.2,ease:'power2.out'},.8+i*.25));
tl.fromTo('.lead',{opacity:0,y:30},{opacity:1,y:0,duration:.5,ease:'power3.out'},1.6);
tl.fromTo('.chip',{opacity:0,y:40,scale:.8},{opacity:1,y:0,scale:1,duration:.45,ease:'back.out(2)',stagger:.15},2.0);
tl.fromTo('.bell',{y:0},{y:-12,duration:1.2,ease:'sine.inOut',yoyo:true,repeat:1},2.4);
""",
)


PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="UTF-8"><title>{title}</title>
<script src="assets/vendor/gsap.min.js"></script>
<script src="assets/vendor/TextPlugin.min.js"></script>
<style>
@font-face{{font-family:Pretendard;font-weight:500;src:url(assets/fonts/Pretendard-Medium.woff2) format('woff2');}}
@font-face{{font-family:Pretendard;font-weight:700;src:url(assets/fonts/Pretendard-Bold.woff2) format('woff2');}}
@font-face{{font-family:Pretendard;font-weight:800;src:url(assets/fonts/Pretendard-ExtraBold.woff2) format('woff2');}}
@font-face{{font-family:Pretendard;font-weight:900;src:url(assets/fonts/Pretendard-Black.woff2) format('woff2');}}
html,body{{margin:0;padding:0;width:1920px;height:1080px;overflow:hidden;background:#0A0A0A;}}
#root{{position:relative;width:1920px;height:1080px;overflow:hidden;font-family:Pretendard,sans-serif;}}
#root *{{box-sizing:border-box;}}
{css}
</style></head>
<body>
<div id="root" data-composition-id="master" data-width="1920" data-height="1080" data-start="0" data-duration="{duration}">
{body}
<script>
gsap.registerPlugin(TextPlugin);
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused:true}});
{js}
tl.set({{}},{{}},{duration});
window.__timelines["master"] = tl;
</script>
</div>
</body></html>
"""

# 효과음: ffmpeg로 직접 합성 (저작권 걱정 없음)
SFX = {
    "whoosh": "anoisesrc=d=0.5:c=pink:a=0.6,highpass=f=400,lowpass=f=5000,afade=t=in:d=0.22,afade=t=out:st=0.22:d=0.28",
    "pop": "aevalsrc='0.7*sin(2*PI*(500+1800*exp(-45*t))*t)*exp(-28*t)':d=0.14",
    "click": "aevalsrc='0.8*sin(2*PI*2800*t)*exp(-220*t)+0.4*sin(2*PI*1200*t)*exp(-120*t)':d=0.05",
    "tick": "aevalsrc='0.45*sin(2*PI*3600*t)*exp(-300*t)':d=0.03",
    "hit": "aevalsrc='0.9*sin(2*PI*(48+140*exp(-22*t))*t)*exp(-5*t)':d=0.6",
    "ding": "aevalsrc='0.35*(sin(2*PI*1318*t)+0.5*sin(2*PI*2637*t)+0.25*sin(2*PI*3955*t))*exp(-3.5*t)':d=1.3",
}


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit(f"실패: {' '.join(cmd[:4])}")
    return r


def build(name, v):
    d = os.path.join(ROOT, name)
    os.makedirs(os.path.join(d, "assets", "vendor"), exist_ok=True)
    os.makedirs(os.path.join(d, "assets", "fonts"), exist_ok=True)
    shutil.copy(os.path.join(SHARED, "gsap/dist/gsap.min.js"), os.path.join(d, "assets/vendor"))
    shutil.copy(os.path.join(SHARED, "gsap/dist/TextPlugin.min.js"), os.path.join(d, "assets/vendor"))
    for w in ("Medium", "Bold", "ExtraBold", "Black"):
        shutil.copy(os.path.join(SHARED, f"pretendard/dist/web/static/woff2/Pretendard-{w}.woff2"), os.path.join(d, "assets/fonts"))
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(PAGE.format(title=f"{name} {v['title']}", **{k: v[k] for k in ("css", "body", "js", "duration")}))

    silent = os.path.join(d, "renders", "silent.mp4")
    if not ("--audio-only" in sys.argv and os.path.exists(silent)):  # --audio-only: 효과음만 다시 섞기
        sh(["npx", "--yes", "hyperframes", "render", "-o", silent, "-q", "delivery", "--fps", "30"], cwd=d)

    # 효과음 배치 → 합성 → 영상과 합치기
    os.makedirs(OUT, exist_ok=True)
    final = os.path.join(OUT, f"{name}.mp4")
    inputs, chains, labels = [], [], []
    for i, (t, kind) in enumerate(v["sfx"]):
        inputs += ["-f", "lavfi", "-i", SFX[kind]]
        ms = int(t * 1000)
        chains.append(f"[{i + 1}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    fc = ";".join(chains) + f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0,apad,atrim=0:{v['duration']},alimiter=limit=0.7:level=disabled[a]"
    sh(["ffmpeg", "-v", "error", "-y", "-i", silent, *inputs, "-filter_complex", fc,
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final])
    print(f"✅ {name} ({v['title']}) → {os.path.relpath(final, ROOT)}")


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(VARIANTS)
    for n in names:
        build(n, VARIANTS[n])
