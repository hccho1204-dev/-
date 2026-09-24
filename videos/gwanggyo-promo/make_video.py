# -*- coding: utf-8 -*-
"""
광교오후학교 x 블레스50플러스 — 코믹 반전 숏폼 홍보 영상 생성기
"비 내리는 밤, 20년 만의 재회… 그런데 이유는 이중주차?"

실행:  python3 make_video.py
결과:  gwanggyo_promo_shorts.mp4 (1080x1920 세로, 약 60초, 30fps)

필요 패키지: pip install pillow numpy imageio-ffmpeg
폰트는 처음 실행 시 Google Fonts 저장소에서 자동으로 내려받는다.
"""
import math
import os
import random
import subprocess
import urllib.request
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(HERE, "fonts"))
OUT = os.path.join(HERE, "gwanggyo_promo_shorts.mp4")
W, H = 1080, 1920
FPS = 30
DUR = 60.0
SR = 44100

# ---------------------------------------------------------------- fonts
FONT_URLS = {
    "title": "https://raw.githubusercontent.com/google/fonts/main/ofl/blackhansans/BlackHanSans-Regular.ttf",
    "comic": "https://raw.githubusercontent.com/google/fonts/main/ofl/jua/Jua-Regular.ttf",
    "drama": "https://raw.githubusercontent.com/google/fonts/main/ofl/gowunbatang/GowunBatang-Bold.ttf",
}


def font_path(key):
    os.makedirs(FONT_DIR, exist_ok=True)
    p = os.path.join(FONT_DIR, os.path.basename(FONT_URLS[key]))
    if not os.path.exists(p):
        urllib.request.urlretrieve(FONT_URLS[key], p)
    return p


_fcache = {}


def F(key, size):
    k = (key, int(size))
    if k not in _fcache:
        _fcache[k] = ImageFont.truetype(font_path(key), int(size))
    return _fcache[k]


# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x):
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, x):
    return a + (b - a) * x


def mix(c1, c2, x):
    return tuple(int(lerp(a, b, x)) for a, b in zip(c1, c2))


class Cam:
    """월드 좌표 -> 화면 좌표 변환 (9:16 크롭)"""

    def __init__(self, x0, y0, cw):
        self.x0, self.y0, self.cw = x0, y0, cw
        self.ch = cw * H / W
        self.s = W / cw

    def p(self, x, y):
        return ((x - self.x0) * self.s, (y - self.y0) * self.s)

    def box(self):
        return (self.x0, self.y0, self.x0 + self.cw, self.y0 + self.ch)


def cam_lerp(a, b, x):
    return Cam(lerp(a.x0, b.x0, x), lerp(a.y0, b.y0, x), lerp(a.cw, b.cw, x))


class Pen:
    """카메라를 적용해서 그려주는 그리기 도구"""

    def __init__(self, draw, cam):
        self.d, self.c = draw, cam

    def ell(self, cx, cy, rx, ry, fill, outline=None, w=0):
        x0, y0 = self.c.p(cx - rx, cy - ry)
        x1, y1 = self.c.p(cx + rx, cy + ry)
        self.d.ellipse([x0, y0, x1, y1], fill=fill, outline=outline, width=max(1, int(w * self.c.s)) if outline else 0)

    def poly(self, pts, fill, outline=None, w=0):
        self.d.polygon([self.c.p(x, y) for x, y in pts], fill=fill, outline=outline,
                       width=max(1, int(w * self.c.s)) if outline else 0)

    def rect(self, x0, y0, x1, y1, fill, r=0):
        a, b = self.c.p(x0, y0)
        c, d = self.c.p(x1, y1)
        if r:
            self.d.rounded_rectangle([a, b, c, d], radius=r * self.c.s, fill=fill)
        else:
            self.d.rectangle([a, b, c, d], fill=fill)

    def line(self, pts, fill, w):
        self.d.line([self.c.p(x, y) for x, y in pts], fill=fill, width=max(1, int(w * self.c.s)), joint="curve")

    def arc(self, cx, cy, rx, ry, a0, a1, fill, w):
        x0, y0 = self.c.p(cx - rx, cy - ry)
        x1, y1 = self.c.p(cx + rx, cy + ry)
        self.d.arc([x0, y0, x1, y1], a0, a1, fill=fill, width=max(1, int(w * self.c.s)))

    def pie(self, cx, cy, rx, ry, a0, a1, fill):
        x0, y0 = self.c.p(cx - rx, cy - ry)
        x1, y1 = self.c.p(cx + rx, cy + ry)
        self.d.pieslice([x0, y0, x1, y1], a0, a1, fill=fill)


# ---------------------------------------------------------------- world (아파트 앞 주차장)
WW, WH = 2160, 4400
GROUND = 2750
FEET = 3080
MAN_X, WOMAN_X = 1190, 1640

SKY_TOP, SKY_BOT = (8, 12, 30), (38, 44, 78)


def build_world():
    img = Image.new("RGB", (WW, WH))
    d = ImageDraw.Draw(img)
    for y in range(GROUND):
        d.line([(0, y), (WW, y)], fill=mix(SKY_TOP, SKY_BOT, y / GROUND))
    rnd = random.Random(7)
    # 먼 산/건물 실루엣
    for i in range(14):
        x = i * 170 - 40
        h = rnd.randint(500, 900)
        d.rectangle([x, GROUND - 1300 - h, x + 150, GROUND - 1100], fill=(22, 26, 48))
    # 아파트 단지
    blocks = [(-60, 700, 820, "101동"), (860, 520, 1500, "102동"), (1560, 820, 2240, "103동")]
    for x0, top, x1, name in blocks:
        d.rectangle([x0, top, x1, GROUND], fill=(46, 50, 72))
        d.rectangle([x0, top, x1, top + 40], fill=(58, 62, 86))
        d.text(((x0 + x1) / 2, top + 110), name, font=F("title", 110), fill=(140, 146, 175), anchor="mm")
        for fy in range(top + 200, GROUND - 160, 120):
            for fx in range(x0 + 50, x1 - 80, 130):
                lit = rnd.random() < 0.38
                col = (255, 214, 130) if lit else (30, 34, 54)
                if lit and rnd.random() < 0.3:
                    col = (190, 220, 255)
                d.rectangle([fx, fy, fx + 80, fy + 70], fill=col)
                d.line([fx - 6, fy + 76, fx + 86, fy + 76], fill=(70, 74, 98), width=6)
    # 1층 필로티 / 화단
    d.rectangle([0, GROUND - 140, WW, GROUND], fill=(36, 40, 58))
    for x in range(0, WW, 90):
        d.ellipse([x - 30, GROUND - 200, x + 90, GROUND - 60], fill=(24, 48, 40))
    # 바닥 (젖은 아스팔트)
    for y in range(GROUND, WH):
        k = (y - GROUND) / (WH - GROUND)
        d.line([(0, y), (WW, y)], fill=mix((40, 42, 56), (22, 24, 34), k))
    # 주차선
    for x in range(-40, WW, 460):
        d.polygon([(x, GROUND + 20), (x + 16, GROUND + 20), (x - 60, WH), (x - 90, WH)], fill=(170, 170, 160))
    d.line([(0, GROUND + 20), (WW, GROUND + 20)], fill=(170, 170, 160), width=14)
    # 가로등
    lx = 2010
    d.rectangle([lx - 14, 1500, lx + 14, FEET - 60], fill=(60, 64, 80))
    d.rectangle([lx - 120, 1480, lx + 20, 1510], fill=(60, 64, 80))
    d.ellipse([lx - 170, 1490, lx - 70, 1540], fill=(255, 236, 170))
    # 불빛 반사 웅덩이
    for (px, py, rx) in [(1500, 3350, 360), (600, 3600, 300), (1900, 3200, 200)]:
        d.ellipse([px - rx, py - 40, px + rx, py + 40], fill=(58, 62, 84))
        for k in range(6):
            d.line([(px - rx * 0.6 + k * 50, py - 6), (px - rx * 0.6 + k * 50 + 30, py - 6)], fill=(120, 110, 90), width=4)
    # 가로등 빛 번짐
    glow = Image.new("L", (WW, WH), 0)
    gd = ImageDraw.Draw(glow)
    gd.polygon([(lx - 150, 1530), (lx - 90, 1530), (lx + 200, FEET + 200), (lx - 520, FEET + 200)], fill=60)
    gd.ellipse([lx - 260, 1400, lx + 40, 1640], fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.composite(Image.new("RGB", (WW, WH), (255, 225, 150)), img, glow)
    d = ImageDraw.Draw(img)
    # 남자 차 (정면, 주차칸 안) — 파란 소형 SUV
    draw_car_front(Pen(d, Cam(0, 0, W)), 330, 2990, 0.98, (46, 92, 150), plate="12가 3456")
    # 여자 차 (측면, 이중주차) — 흰색 세단, 남자 차 앞을 가로막음
    draw_car_side(Pen(d, Cam(0, 0, W)), 20, 3420, 1.0, (230, 230, 236))
    return img


def draw_car_front(pen, cx, bottom, k, body, plate="", wiper=None, people=None):
    """정면 자동차. cx=중심, bottom=바퀴 아래."""
    u = 100 * k
    # 바퀴
    pen.rect(cx - 3.3 * u, bottom - 0.9 * u, cx - 2.3 * u, bottom, (18, 18, 22), r=0.2 * u)
    pen.rect(cx + 2.3 * u, bottom - 0.9 * u, cx + 3.3 * u, bottom, (18, 18, 22), r=0.2 * u)
    # 차체
    dark = mix(body, (0, 0, 0), 0.35)
    pen.poly([(cx - 2.6 * u, bottom - 4.4 * u), (cx + 2.6 * u, bottom - 4.4 * u),
              (cx + 3.1 * u, bottom - 2.7 * u), (cx - 3.1 * u, bottom - 2.7 * u)], dark)
    # 앞유리
    glass = (40, 58, 88)
    pen.poly([(cx - 2.35 * u, bottom - 4.2 * u), (cx + 2.35 * u, bottom - 4.2 * u),
              (cx + 2.8 * u, bottom - 2.9 * u), (cx - 2.8 * u, bottom - 2.9 * u)], glass)
    if people:
        people(pen, cx, bottom - 2.9 * u, u)
    pen.rect(cx - 3.5 * u, bottom - 2.9 * u, cx + 3.5 * u, bottom - 0.6 * u, body, r=0.45 * u)
    pen.poly([(cx - 2.2 * u, bottom - 4.15 * u), (cx - 1.5 * u, bottom - 4.15 * u),
              (cx - 2.3 * u, bottom - 3.0 * u), (cx - 2.65 * u, bottom - 3.0 * u)], (70, 90, 124))
    # 와이퍼
    angs = wiper if wiper is not None else (-8, -8)
    for side, ang in zip((-1, 1), angs):
        px, py = cx + side * 0.55 * u - 0.9 * u, bottom - 2.95 * u
        if side == 1:
            px = cx + 1.3 * u
        a = math.radians(180 - ang) if side == -1 else math.radians(180 - ang)
        L = 2.1 * u
        ex, ey = px + math.cos(a) * L * -1, py - math.sin(a) * L * -1
        ex, ey = px + math.cos(math.radians(ang)) * L, py - math.sin(math.radians(ang)) * L
        pen.line([(px, py), (ex, ey)], (15, 15, 18), 0.12 * u)
    # 헤드라이트, 그릴, 번호판
    pen.ell(cx - 2.55 * u, bottom - 2.1 * u, 0.55 * u, 0.32 * u, (255, 244, 200))
    pen.ell(cx + 2.55 * u, bottom - 2.1 * u, 0.55 * u, 0.32 * u, (255, 244, 200))
    pen.rect(cx - 1.4 * u, bottom - 2.3 * u, cx + 1.4 * u, bottom - 1.7 * u, (30, 30, 36), r=0.15 * u)
    pen.rect(cx - 1.1 * u, bottom - 1.45 * u, cx + 1.1 * u, bottom - 0.95 * u, (240, 240, 240), r=0.06 * u)
    if plate:
        x, y = pen.c.p(cx, bottom - 1.2 * u)
        pen.d.text((x, y), plate, font=F("title", 0.36 * u * pen.c.s), fill=(20, 20, 20), anchor="mm")
    # 사이드미러
    pen.ell(cx - 3.75 * u, bottom - 3.1 * u, 0.35 * u, 0.25 * u, dark)
    pen.ell(cx + 3.75 * u, bottom - 3.1 * u, 0.35 * u, 0.25 * u, dark)


def draw_car_side(pen, x0, bottom, k, body):
    """측면 세단. x0=왼쪽 끝."""
    u = 100 * k
    L = 8.0 * u
    dark = mix(body, (0, 0, 0), 0.3)
    pen.rect(x0, bottom - 2.2 * u, x0 + L, bottom - 0.55 * u, body, r=0.6 * u)
    pen.poly([(x0 + 1.9 * u, bottom - 2.1 * u), (x0 + 2.9 * u, bottom - 3.6 * u), (x0 + 5.4 * u, bottom - 3.6 * u),
              (x0 + 6.6 * u, bottom - 2.1 * u)], body)
    pen.poly([(x0 + 2.3 * u, bottom - 2.2 * u), (x0 + 3.1 * u, bottom - 3.35 * u), (x0 + 4.1 * u, bottom - 3.35 * u),
              (x0 + 4.1 * u, bottom - 2.2 * u)], (40, 58, 88))
    pen.poly([(x0 + 4.3 * u, bottom - 2.2 * u), (x0 + 4.3 * u, bottom - 3.35 * u), (x0 + 5.25 * u, bottom - 3.35 * u),
              (x0 + 6.1 * u, bottom - 2.2 * u)], (40, 58, 88))
    pen.line([(x0 + 0.3 * u, bottom - 1.6 * u), (x0 + L - 0.3 * u, bottom - 1.6 * u)], dark, 0.06 * u)
    pen.line([(x0 + 4.2 * u, bottom - 2.2 * u), (x0 + 4.2 * u, bottom - 0.7 * u)], dark, 0.05 * u)
    for wx in (x0 + 1.6 * u, x0 + 6.4 * u):
        pen.ell(wx, bottom - 0.6 * u, 0.75 * u, 0.75 * u, (18, 18, 22))
        pen.ell(wx, bottom - 0.6 * u, 0.38 * u, 0.38 * u, (150, 150, 160))
    pen.ell(x0 + L - 0.25 * u, bottom - 1.75 * u, 0.25 * u, 0.2 * u, (255, 244, 200))
    pen.rect(x0 + 0.02 * u, bottom - 1.95 * u, x0 + 0.3 * u, bottom - 1.5 * u, (220, 40, 40), r=0.08 * u)


# ---------------------------------------------------------------- characters
SKIN = (240, 200, 170)
SKIN_M = (222, 178, 146)


def draw_man(pen, fx, fy, t, pose="up", talk=False, height=1000, shiver=True):
    u = height / 100.0
    sx = math.sin(t * 38) * 0.25 * u if shiver else 0
    fx += sx
    coat = (92, 78, 60)
    coat_d = (70, 58, 44)
    # 다리/구두
    pen.rect(fx - 9 * u, fy - 40 * u, fx - 1.5 * u, fy - 2 * u, (34, 34, 42))
    pen.rect(fx + 1.5 * u, fy - 40 * u, fx + 9 * u, fy - 2 * u, (34, 34, 42))
    pen.rect(fx - 11 * u, fy - 3.5 * u, fx - 1 * u, fy, (20, 16, 14), r=1.5 * u)
    pen.rect(fx + 1 * u, fy - 3.5 * u, fx + 11 * u, fy, (20, 16, 14), r=1.5 * u)
    # 트렌치코트
    bow = 1.0 if pose == "down" else 0.0
    pen.poly([(fx - 14 * u, fy - 77 * u), (fx + 14 * u, fy - 77 * u), (fx + 17 * u, fy - 30 * u),
              (fx - 17 * u, fy - 30 * u)], coat)
    pen.poly([(fx - 3 * u, fy - 77 * u), (fx + 3 * u, fy - 77 * u), (fx + 1 * u, fy - 30 * u), (fx - 1 * u, fy - 30 * u)],
             coat_d)
    pen.poly([(fx - 5 * u, fy - 77 * u), (fx, fy - 66 * u), (fx + 5 * u, fy - 77 * u)], (230, 230, 235))  # 셔츠
    pen.line([(fx - 16.5 * u, fy - 50 * u), (fx + 16.5 * u, fy - 50 * u)], coat_d, 1.8 * u)  # 벨트
    for by in (-70, -62, -54):
        pen.ell(fx - 5 * u, fy + by * u, 0.9 * u, 0.9 * u, (40, 30, 20))
    # 팔
    droop = 2 * u * bow
    for sgn in (-1, 1):
        pen.poly([(fx + sgn * 13 * u, fy - 76 * u), (fx + sgn * 17.5 * u, fy - 73 * u),
                  (fx + sgn * 19.5 * u, fy - 42 * u + droop), (fx + sgn * 15 * u, fy - 42 * u + droop)], coat_d)
        pen.ell(fx + sgn * 17.2 * u, fy - 40 * u + droop, 2.6 * u, 2.9 * u, SKIN_M)
    # 머리
    hx, hy = fx + (2.5 * u if pose == "down" else 0.8 * u), fy - (84 * u if pose == "down" else 88 * u)
    pen.rect(fx - 3 * u, fy - 81 * u, fx + 3 * u, fy - 75 * u, SKIN_M)
    pen.ell(hx, hy, 9 * u, 10.5 * u, SKIN)
    pen.ell(hx - 9 * u, hy + 1 * u, 1.8 * u, 2.6 * u, SKIN_M)
    pen.ell(hx + 9 * u, hy + 1 * u, 1.8 * u, 2.6 * u, SKIN_M)
    hair = (48, 48, 54)
    # 젖은 머리 (가르마 + 흰머리)
    pen.pie(hx, hy - 1 * u, 9.6 * u, 10 * u, 180, 360, hair)
    pen.poly([(hx - 9.6 * u, hy - 1 * u), (hx - 8.5 * u, hy + 3 * u), (hx - 7 * u, hy - 2 * u)], hair)
    pen.poly([(hx - 2 * u, hy - 9 * u), (hx + 1 * u, hy - 1.5 * u), (hx + 4 * u, hy - 9 * u)], hair)  # 젖어서 내려온 앞머리
    pen.line([(hx - 5 * u, hy - 8 * u), (hx - 2 * u, hy - 9.6 * u)], (150, 150, 158), 0.7 * u)
    pen.line([(hx + 4 * u, hy - 9 * u), (hx + 7 * u, hy - 6.5 * u)], (150, 150, 158), 0.7 * u)
    ey = hy + 1.5 * u
    if pose == "down":
        # 고개 숙임: 감은 눈
        pen.arc(hx - 3.6 * u, ey + 1 * u, 2 * u, 1.2 * u, 0, 180, (40, 30, 30), 0.6 * u)
        pen.arc(hx + 4.4 * u, ey + 1 * u, 2 * u, 1.2 * u, 0, 180, (40, 30, 30), 0.6 * u)
        pen.line([(hx - 5.5 * u, ey - 2.5 * u), (hx - 1.5 * u, ey - 1.2 * u)], hair, 0.8 * u)
        pen.line([(hx + 2.5 * u, ey - 1.2 * u), (hx + 6.5 * u, ey - 2.5 * u)], hair, 0.8 * u)
    else:
        # 애절한 눈썹 (八자)
        pen.line([(hx - 6 * u, ey - 3 * u), (hx - 1.5 * u, ey - 4.6 * u)], hair, 0.9 * u)
        pen.line([(hx + 2.5 * u, ey - 4.6 * u), (hx + 7 * u, ey - 3 * u)], hair, 0.9 * u)
        for ex in (hx - 3.2 * u, hx + 4.6 * u):
            pen.ell(ex, ey, 1.3 * u, 1.5 * u, (255, 255, 255))
            pen.ell(ex + 0.5 * u, ey, 0.85 * u, 1.05 * u, (30, 24, 24))
            pen.ell(ex + 0.8 * u, ey - 0.4 * u, 0.3 * u, 0.3 * u, (255, 255, 255))
        pen.line([(hx - 5 * u, ey + 2.3 * u), (hx - 1.8 * u, ey + 2.6 * u)], SKIN_M, 0.4 * u)  # 다크서클
    # 코, 수염, 입
    pen.line([(hx + 1 * u, ey + 0.5 * u), (hx + 1.8 * u, ey + 4 * u), (hx + 0.4 * u, ey + 4.3 * u)], SKIN_M, 0.5 * u)
    for i in range(14):
        a = i / 13 * math.pi
        pen.ell(hx + 0.6 * u + math.cos(a) * 5.5 * u, ey + 6 * u + math.sin(a) * 2.2 * u, 0.25 * u, 0.25 * u, (150, 130, 120))
    my = ey + 6.2 * u
    if talk:
        pen.ell(hx + 0.6 * u, my, 1.9 * u, 1.3 * u, (110, 40, 40))
    else:
        pen.line([(hx - 1.3 * u, my), (hx + 2.5 * u, my + 0.2 * u)], (120, 70, 60), 0.5 * u)
    # 빗물 방울 (몸에서 뚝뚝)
    for i in range(5):
        ph = (t * 1.3 + i * 0.37) % 1.0
        dx = (-12 + i * 6) * u
        pen.ell(fx + dx, fy - 30 * u + ph * 28 * u, 0.5 * u, 0.9 * u, (170, 200, 230))


def draw_woman(pen, fx, fy, t, teary=0.0, talk=False, height=930, walking=False, umbrella=True):
    u = height / 100.0
    bob = abs(math.sin(t * 7)) * 1.2 * u if walking else 0
    fy2 = fy - bob
    coat = (170, 34, 48)
    coat_d = (130, 24, 36)
    # 다리
    step = math.sin(t * 7) * 3 * u if walking else 0
    pen.rect(fx - 6 * u + step, fy - 34 * u, fx - 1.5 * u + step, fy - 2 * u, (40, 36, 44))
    pen.rect(fx + 1.5 * u - step, fy - 34 * u, fx + 6 * u - step, fy - 2 * u, (40, 36, 44))
    pen.rect(fx - 7.5 * u + step, fy - 3 * u, fx - 0.5 * u + step, fy, (20, 18, 20), r=1.2 * u)
    pen.rect(fx + 0.5 * u - step, fy - 3 * u, fx + 7.5 * u - step, fy, (20, 18, 20), r=1.2 * u)
    # 긴 머리 (뒤)
    hx, hy = fx - 0.8 * u, fy2 - 87 * u
    hair = (24, 18, 20)
    pen.poly([(hx - 10.5 * u, hy - 2 * u), (hx + 10.5 * u, hy - 2 * u), (hx + 12.5 * u, hy + 25 * u),
              (hx - 12.5 * u, hy + 25 * u)], hair)
    # 코트
    pen.poly([(fx - 11 * u, fy2 - 74 * u), (fx + 11 * u, fy2 - 74 * u), (fx + 16 * u, fy2 - 30 * u),
              (fx - 16 * u, fy2 - 30 * u)], coat)
    pen.line([(fx, fy2 - 72 * u), (fx, fy2 - 31 * u)], coat_d, 0.7 * u)
    pen.line([(fx - 14 * u, fy2 - 50 * u), (fx + 14 * u, fy2 - 50 * u)], coat_d, 1.4 * u)
    pen.poly([(fx - 4 * u, fy2 - 74 * u), (fx, fy2 - 66 * u), (fx + 4 * u, fy2 - 74 * u)], (240, 226, 210))
    # 왼팔 (가방)
    pen.poly([(fx + 10 * u, fy2 - 73 * u), (fx + 14 * u, fy2 - 70 * u), (fx + 15.5 * u, fy2 - 44 * u),
              (fx + 11.5 * u, fy2 - 44 * u)], coat_d)
    pen.ell(fx + 13.5 * u, fy2 - 42 * u, 2.2 * u, 2.5 * u, SKIN_M)
    pen.rect(fx + 11 * u, fy2 - 44 * u, fx + 19 * u, fy2 - 34 * u, (60, 40, 30), r=1.2 * u)
    # 오른팔 (우산 들기)
    if umbrella:
        pen.poly([(fx - 10 * u, fy2 - 73 * u), (fx - 14 * u, fy2 - 70 * u), (fx - 12 * u, fy2 - 55 * u),
                  (fx - 8 * u, fy2 - 56 * u)], coat_d)
        pen.ell(fx - 9 * u, fy2 - 57 * u, 2.2 * u, 2.5 * u, SKIN_M)
        pen.line([(fx - 9 * u, fy2 - 55 * u), (fx - 9 * u, fy2 - 124 * u)], (60, 60, 64), 0.7 * u)
        pen.arc(fx - 10.5 * u, fy2 - 55 * u, 1.5 * u, 1.8 * u, 0, 180, (60, 60, 64), 0.7 * u)
    else:
        pen.poly([(fx - 10 * u, fy2 - 73 * u), (fx - 14 * u, fy2 - 70 * u), (fx - 15.5 * u, fy2 - 44 * u),
                  (fx - 11.5 * u, fy2 - 44 * u)], coat_d)
        pen.ell(fx - 13.5 * u, fy2 - 42 * u, 2.2 * u, 2.5 * u, SKIN_M)
    # 얼굴
    pen.rect(fx - 2.5 * u, fy2 - 78 * u, fx + 2.5 * u, fy2 - 72 * u, SKIN_M)
    pen.ell(hx, hy, 8.4 * u, 10 * u, SKIN)
    pen.pie(hx, hy - 1 * u, 9.2 * u, 10.2 * u, 180, 360, hair)
    pen.poly([(hx - 9.2 * u, hy - 1 * u), (hx - 8.4 * u, hy + 10 * u), (hx - 6.5 * u, hy - 3 * u)], hair)
    pen.poly([(hx + 9.2 * u, hy - 1 * u), (hx + 8.4 * u, hy + 10 * u), (hx + 6.5 * u, hy - 3 * u)], hair)
    pen.poly([(hx - 7 * u, hy - 7 * u), (hx - 1 * u, hy - 3 * u), (hx + 2 * u, hy - 10 * u)], hair)  # 앞머리
    ey = hy + 1.5 * u
    red = mix(SKIN, (230, 90, 90), teary)
    for ex in (hx - 3.6 * u, hx + 2.8 * u):
        if teary > 0:
            pen.ell(ex - 0.2 * u, ey + 0.4 * u, 2.3 * u, 2.1 * u, red)
        pen.ell(ex, ey, 1.4 * u, 1.6 * u, (255, 255, 255))
        pen.ell(ex - 0.4 * u, ey + 0.1 * u, 1.0 * u, 1.2 * u, (34, 20, 20))
        pen.ell(ex - 0.1 * u, ey - 0.4 * u, 0.35 * u, 0.35 * u, (255, 255, 255))
        if teary > 0.3:
            pen.ell(ex - 0.9 * u, ey + 0.6 * u, 0.3 * u, 0.3 * u, (255, 255, 255))
        pen.line([(ex - 1.8 * u, ey - 1.2 * u), (ex - 2.2 * u, ey - 1.8 * u)], hair, 0.35 * u)  # 속눈썹
    # 슬픈 눈썹
    pen.line([(hx - 6 * u, ey - 3.2 * u), (hx - 1.8 * u, ey - 4.4 * u)], hair, 0.6 * u)
    pen.line([(hx + 0.8 * u, ey - 4.4 * u), (hx + 5 * u, ey - 3.2 * u)], hair, 0.6 * u)
    # 눈물
    if teary > 0.5:
        for i, ex in enumerate((hx - 3.6 * u, hx + 2.8 * u)):
            ph = ((t * 0.9 + i * 0.5) % 1.0)
            pen.ell(ex - 0.3 * u, ey + 2.5 * u + ph * 7 * u, 0.55 * u, 0.9 * u, (180, 220, 255))
    pen.line([(hx - 0.8 * u, ey + 1 * u), (hx - 1.4 * u, ey + 3.8 * u), (hx - 0.4 * u, ey + 4 * u)], SKIN_M, 0.4 * u)
    my = ey + 6 * u
    if talk:
        pen.ell(hx - 0.6 * u, my, 1.6 * u, 1.2 * u, (160, 40, 60))
    else:
        pen.line([(hx - 2.4 * u, my), (hx + 1.2 * u, my)], (190, 60, 80), 0.6 * u)
    pen.ell(hx - 5.5 * u, ey + 3.4 * u, 1.3 * u, 0.7 * u, mix(SKIN, (240, 140, 140), 0.5 + 0.5 * teary))
    pen.ell(hx + 4.6 * u, ey + 3.4 * u, 1.3 * u, 0.7 * u, mix(SKIN, (240, 140, 140), 0.5 + 0.5 * teary))
    # 우산 캐노피 (투명 비닐 느낌: 윤곽선 + 살)
    if umbrella:
        ux, uy = fx - 9 * u, fy2 - 124 * u
        pen.pie(ux, uy + 14 * u, 30 * u, 16 * u, 180, 360, (54, 60, 96))
        for k in range(-3, 4):
            pen.line([(ux, uy - 2 * u), (ux + k * 10 * u, uy + 14 * u)], (90, 98, 140), 0.4 * u)
        pen.arc(ux, uy + 14 * u, 30 * u, 16 * u, 180, 360, (140, 150, 190), 0.6 * u)
        pen.line([(ux, uy - 2 * u), (ux, uy - 5 * u)], (60, 60, 64), 0.8 * u)


def draw_husband(pen, cx, cy, t, state="calm", talk=False, size=100, pale=0.0):
    u = size / 20.0
    skin = mix(SKIN, (180, 200, 220), pale)
    pen.ell(cx, cy + 10 * u, 10 * u, 5 * u, (70, 90, 70))  # 어깨 (녹색 카디건)
    pen.ell(cx, cy, 8.5 * u, 9.5 * u, skin)
    pen.pie(cx, cy - 2 * u, 8.8 * u, 8.2 * u, 180, 360, (30, 26, 26))
    pen.ell(cx - 8.3 * u, cy + 0.5 * u, 1.5 * u, 2.3 * u, skin)
    pen.ell(cx + 8.3 * u, cy + 0.5 * u, 1.5 * u, 2.3 * u, skin)
    ey = cy + 1 * u
    # 안경
    for ex in (cx - 3.4 * u, cx + 3.4 * u):
        pen.ell(ex, ey, 2.6 * u, 2.2 * u, (255, 255, 255), outline=(30, 30, 30), w=0.45 * u)
        if state == "stiff":
            pen.ell(ex, ey, 0.5 * u, 0.5 * u, (20, 20, 20))
        else:
            pen.ell(ex + 0.4 * u, ey + 0.2 * u, 0.9 * u, 1.0 * u, (20, 20, 20))
    pen.line([(cx - 0.8 * u, ey), (cx + 0.8 * u, ey)], (30, 30, 30), 0.4 * u)
    if state == "stiff":
        pen.line([(cx - 5.5 * u, ey - 3.8 * u), (cx - 1.5 * u, ey - 3 * u)], (30, 26, 26), 0.7 * u)
        pen.line([(cx + 1.5 * u, ey - 3 * u), (cx + 5.5 * u, ey - 3.8 * u)], (30, 26, 26), 0.7 * u)
        pen.rect(cx - 2.2 * u, cy + 5.2 * u, cx + 2.2 * u, cy + 5.8 * u, (80, 40, 40))
        # 충격 세로줄
        for k in range(5):
            x = cx - 4 * u + k * 2 * u
            pen.line([(x, cy - 7 * u), (x, cy - 3.2 * u)], (90, 110, 180), 0.35 * u)
    else:
        pen.line([(cx - 5 * u, ey - 4.2 * u), (cx - 1.5 * u, ey - 3.4 * u)], (30, 26, 26), 0.6 * u)
        pen.line([(cx + 1.5 * u, ey - 3.8 * u), (cx + 5 * u, ey - 4.6 * u)], (30, 26, 26), 0.6 * u)
        if talk:
            pen.ell(cx, cy + 5.5 * u, 1.4 * u, 1.1 * u, (110, 40, 40))
        else:
            pen.line([(cx - 1.5 * u, cy + 5.5 * u), (cx + 1.5 * u, cy + 5.3 * u)], (120, 60, 60), 0.4 * u)


# ---------------------------------------------------------------- screen-space overlays
_rain = [(random.Random(i).uniform(0, W), random.Random(i * 3 + 1).uniform(0, H), random.Random(i * 7).uniform(0.7, 1.3))
         for i in range(260)]


def draw_rain(d, t, strength=1.0):
    n = int(len(_rain) * strength)
    for (x0, y0, v) in _rain[:n]:
        y = (y0 + t * 2300 * v) % (H + 120) - 60
        x = (x0 + t * 260 * v) % W
        L = 55 * v
        d.line([(x, y), (x + L * 0.11, y + L)], fill=(170, 190, 215), width=2)


def text_c(d, xy, txt, font, fill, stroke=6, stroke_fill=(0, 0, 0), anchor="mm"):
    d.text(xy, txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor=anchor)


def wrap(txt, font, maxw):
    words = txt.split(" ")
    lines, cur = [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if font.getlength(test) <= maxw or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


SPEAKER_COL = {"여자": (255, 120, 140), "남자": (120, 190, 255), "남편": (140, 230, 140)}


def draw_sub(img, t, line):
    """자막 박스 (하단)"""
    t0, t1, who, txt, style = line
    if not (t0 <= t < t1):
        return
    a = clamp((t - t0) / 0.15) * clamp((t1 - t) / 0.12)
    d = ImageDraw.Draw(img, "RGBA")
    comic = style in ("comic", "punch")
    font = F("comic", 76) if comic else F("drama", 64)
    if style == "punch":
        font = F("title", 96)
    if comic:
        txt = txt.replace("…", "...")
    lines = wrap(txt, font, 940)
    lh = font.size * 1.3
    base_y = 1540
    total_h = lh * len(lines)
    y0 = base_y - total_h / 2
    if not comic:
        d.rectangle([0, y0 - 70, W, y0 + total_h + 40], fill=(0, 0, 0, int(120 * a)))
    if who:
        col = SPEAKER_COL.get(who, (255, 255, 255))
        tf = F("title", 44)
        tw = tf.getlength(who) + 44
        d.rounded_rectangle([W / 2 - tw / 2, y0 - 62, W / 2 + tw / 2, y0 - 8], radius=24,
                            fill=col + (int(235 * a),))
        d.text((W / 2, y0 - 35), who, font=tf, fill=(20, 20, 20, int(255 * a)), anchor="mm")
    for i, ln in enumerate(lines):
        y = y0 + lh * (i + 0.5)
        dx = dy = 0
        fill = (255, 255, 255, int(255 * a))
        if style == "punch":
            dx, dy = random.uniform(-6, 6), random.uniform(-6, 6)
            fill = (255, 226, 60, int(255 * a))
        elif style == "comic":
            fill = (255, 255, 255, int(255 * a))
        d.text((W / 2 + dx, y + dy), ln, font=font, fill=fill, stroke_width=8 if comic else 4,
               stroke_fill=(0, 0, 0, int(255 * a)), anchor="mm")


def draw_direction(img, t, item):
    t0, t1, txt = item
    if not (t0 <= t < t1):
        return
    a = clamp((t - t0) / 0.2) * clamp((t1 - t) / 0.2)
    d = ImageDraw.Draw(img, "RGBA")
    f = F("drama", 46)
    tw = f.getlength(txt)
    d.rounded_rectangle([W / 2 - tw / 2 - 30, 300, W / 2 + tw / 2 + 30, 380], radius=14, fill=(0, 0, 0, int(150 * a)))
    d.text((W / 2, 340), txt, font=f, fill=(230, 230, 230, int(255 * a)), anchor="mm")


def draw_header(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, 260):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(170 * (1 - y / 260))))
    # 광교오후학교 배지
    f = F("title", 54)
    txt = "광교오후학교"
    tw = f.getlength(txt)
    d.rounded_rectangle([40, 70, 40 + tw + 60, 160], radius=45, fill=(255, 140, 40, 240))
    d.text((70 + tw / 2, 115), txt, font=f, fill=(255, 255, 255), anchor="mm")
    # 블레스50플러스 배지
    f2 = F("title", 40)
    txt2 = "블레스50플러스"
    tw2 = f2.getlength(txt2)
    x1 = W - 40
    d.rounded_rectangle([x1 - tw2 - 50, 82, x1, 148], radius=33, fill=(255, 255, 255, 230))
    d.text((x1 - 25 - tw2 / 2, 115), txt2, font=f2, fill=(30, 60, 140), anchor="mm")
    # 하단 띠
    d.rectangle([0, H - 110, W, H], fill=(0, 0, 0, 150))
    d.text((W / 2, H - 55), "광교오후학교 X 블레스50플러스  |  오후 드라마 극장", font=F("comic", 40),
           fill=(255, 220, 160), anchor="mm")


def vignette_mask():
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([-300, -200, W + 300, H + 200], fill=255)
    return m.filter(ImageFilter.GaussianBlur(160))


VIG = None


# ---------------------------------------------------------------- script / timeline
SUBS = [
    (6.0, 7.9, "여자", "…너였어?", "drama"),
    (8.0, 9.9, "남자", "20년 만이네.", "drama"),
    (10.0, 12.2, "여자", "왜 아무 말도 안 했어?", "drama"),
    (12.3, 14.9, "남자", "네 목소리 들으면… 못 할 것 같아서.", "drama"),
    (16.5, 18.4, "여자", "나 결혼했어.", "drama"),
    (18.5, 19.9, "남자", "알아.", "drama"),
    (20.0, 22.2, "여자", "그런데 왜 자꾸 전화해?", "drama"),
    (22.8, 25.3, "남자", "네가… 나갈 때까지 기다리려고.", "drama"),
    (25.4, 28.3, "여자", "내가… 그 사람을 떠나길 바라는 거야?", "drama"),
    (30.0, 30.9, "남자", "아니.", "drama"),
    (30.9, 33.3, "남자", "차를 빼줘야 내가 나가지.", "punch"),
    (36.2, 38.0, "여자", "…밀면 되잖아.", "comic"),
    (38.1, 40.0, "남자", "사이드 채웠잖아.", "comic"),
    (42.2, 44.0, "남편", "여보, 누구야?", "comic"),
    (44.1, 46.8, "남자", "제가… 아내분 때문에 못 잊고…", "drama"),
    (48.0, 50.5, "남자", "…못 움직이고 있었습니다.", "punch"),
]

DIRS = [
    (3.0, 5.8, "[비 내리는 밤. 아파트 앞.]"),
    (15.0, 16.4, "[여자의 눈시울이 붉어진다]"),
    (22.3, 23.6, "[남자가 고개를 숙인다]"),
    (28.3, 30.0, "[음악이 절정으로…]"),
    (40.0, 41.2, "[여자가 차에 탄다]"),
    (41.2, 42.2, "[조수석 창문이 내려간다]"),
    (46.8, 48.0, "[남편의 얼굴이 굳는다]"),
    (50.5, 53.5, "[와이퍼만 처량하게 움직인다]"),
]

CLOSE = Cam(820, 1690, 1300)          # 두 사람 투샷
CLOSE_IN = Cam(900, 1830, 1120)       # 살짝 푸시인
MAN_CU = Cam(MAN_X - 380, 2020, 760)  # 남자 얼굴 클로즈업
WOMAN_CU = Cam(WOMAN_X - 380, 2090, 760)
WIDE = Cam(0, 780, 2160 * 0.94)      # 전경 (차 공개)


def talking(t, who):
    for (t0, t1, w_, _, _) in SUBS:
        if w_ == who and t0 + 0.1 <= t < t1 - 0.25:
            return int(t * 9) % 2 == 0
    return False


def camera(t):
    if t < 3.0:
        return cam_lerp(Cam(660, 1500, 1500), CLOSE, ease(t / 3))
    if t < 15.0:
        return cam_lerp(CLOSE, CLOSE_IN, ease((t - 3) / 12))
    if t < 16.5:
        return cam_lerp(CLOSE_IN, WOMAN_CU, ease((t - 15) / 0.8))
    if t < 17.3:
        return cam_lerp(WOMAN_CU, CLOSE_IN, ease((t - 16.5) / 0.8))
    if t < 28.3:
        return CLOSE_IN
    if t < 33.3:
        c = cam_lerp(CLOSE_IN, MAN_CU, ease((t - 28.3) / 1.6))
        # 절정에서 미세한 흔들림
        return Cam(c.x0 + math.sin(t * 13) * 3, c.y0 + math.cos(t * 11) * 3, c.cw)
    if t < 33.7:
        return MAN_CU  # 정적 (프리즈)
    if t < 35.2:
        return cam_lerp(MAN_CU, WIDE, ease((t - 33.7) / 1.5))
    return WIDE


def render_world_scene(world, t):
    cam = camera(t)
    frame = world.resize((W, H), Image.BILINEAR, box=cam.box())
    d = ImageDraw.Draw(frame)
    pen = Pen(d, cam)
    # 여자 위치
    if t < 3.0:
        wx, walking = None, False
    elif t < 6.0:
        wx, walking = lerp(WOMAN_X + 900, WOMAN_X, ease((t - 3) / 2.8)), t < 5.8
    elif t < 39.8:
        wx, walking = WOMAN_X, False
    else:
        wx, walking = lerp(WOMAN_X, 700, ease((t - 39.8) / 1.4)), True
    pose = "down" if 22.3 <= t < 28.6 else "up"
    frozen = 33.3 <= t < 33.7
    tt = 33.3 if frozen else t
    draw_man(pen, MAN_X, FEET, tt, pose=pose, talk=talking(t, "남자") and not frozen, shiver=not frozen)
    if wx is not None:
        teary = clamp((t - 15.0) / 1.2) if t < 33.3 else 0.6
        draw_woman(pen, wx, FEET + 10, t, teary=teary, talk=talking(t, "여자"), walking=walking)
    return frame, cam


def draw_reveal_labels(img, t, cam):
    if t < 35.2:
        return
    d = ImageDraw.Draw(img, "RGBA")
    a = clamp((t - 35.2) / 0.3)
    # 남자 차 / 여자 차 라벨
    mx, my = cam.p(330, 2560)
    wx_, wy = cam.p(420, 3420 - 330)
    f = F("comic", 54)
    for (x, y, txt, col, dy) in [(mx, my, "남자 차", (120, 190, 255), -80), (wx_, wy, "여자 차 (이중주차)", (255, 120, 140), 130)]:
        tw = f.getlength(txt)
        by = y + dy
        d.line([(x, y), (x, by)], fill=col + (int(255 * a),), width=6)
        d.rounded_rectangle([x - tw / 2 - 24, by - 40, x + tw / 2 + 24, by + 40], radius=20, fill=col + (int(240 * a),))
        d.text((x, by), txt, font=f, fill=(20, 20, 20, int(255 * a)), anchor="mm")
    # 사이드 브레이크 아이콘
    if t >= 38.1:
        b = ease_out_back((t - 38.1) / 0.4)
        cx, cy = cam.p(760, 3060)
        r = 58 * b
        if r > 2:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 40, 40, 240), outline=(255, 255, 255), width=5)
            d.text((cx, cy), "P", font=F("title", int(70 * b) + 1), fill=(255, 255, 255), anchor="mm")
            d.text((cx, cy + r + 34), "사이드 ON", font=F("comic", 40), fill=(255, 255, 255), stroke_width=5,
                   stroke_fill=(0, 0, 0), anchor="mm")
    # 휴대폰: 부재중 전화 18통
    if 35.4 <= t < 40.0:
        b = ease_out_back((t - 35.4) / 0.45)
        shake = math.sin(t * 60) * 6 if (t - 35.4) % 1.0 < 0.35 else 0
        pw, ph = 360 * b, 560 * b
        if pw > 10:
            cx, cy = W - 250 + shake, 640
            d.rounded_rectangle([cx - pw / 2 - 12, cy - ph / 2 - 12, cx + pw / 2 + 12, cy + ph / 2 + 12], radius=50 * b,
                                fill=(20, 20, 24, 255))
            d.rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], radius=40 * b, fill=(245, 245, 250, 255))
            if b > 0.8:
                d.text((cx, cy - 200), "여자의 휴대폰", font=F("comic", 34), fill=(120, 120, 130), anchor="mm")
                d.ellipse([cx - 70, cy - 150, cx + 70, cy - 10], fill=(230, 60, 60))
                d.text((cx, cy - 80), "18", font=F("title", 80), fill=(255, 255, 255), anchor="mm")
                d.text((cx, cy + 50), "부재중 전화", font=F("title", 58), fill=(220, 40, 40), anchor="mm")
                d.text((cx, cy + 120), "18통", font=F("title", 70), fill=(30, 30, 30), anchor="mm")
                d.text((cx, cy + 200), "(모르는 번호)", font=F("comic", 34), fill=(120, 120, 130), anchor="mm")


# ---------------------------------------------------------------- scene 3: 여자 차 앞
def build_car_bg():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(1150):
        d.line([(0, y), (W, y)], fill=mix(SKY_TOP, SKY_BOT, y / 1150))
    rnd = random.Random(3)
    d.rectangle([-20, 250, 700, 1150], fill=(46, 50, 72))
    d.rectangle([740, 380, 1100, 1150], fill=(46, 50, 72))
    for fy in range(330, 1100, 90):
        for fx in list(range(20, 680, 100)) + list(range(770, 1080, 100)):
            if fy < 400 and fx > 740:
                continue
            col = (255, 214, 130) if rnd.random() < 0.4 else (30, 34, 54)
            d.rectangle([fx, fy, fx + 60, fy + 50], fill=col)
    for y in range(1150, H):
        d.line([(0, y), (W, y)], fill=mix((44, 46, 60), (22, 24, 34), (y - 1150) / (H - 1150)))
    return img.filter(ImageFilter.GaussianBlur(6))


def render_car_scene(bg, t):
    frame = bg.copy()
    d = ImageDraw.Draw(frame)
    zoom = 1.0 + 0.04 * ease((t - 41.0) / 12)
    cam = Cam(W / 2 - W / zoom / 2, 200 - 0, W / zoom)
    cam = Cam(W / 2 - W / zoom / 2, (H - H / zoom) / 2, W / zoom)
    pen = Pen(d, cam)
    # 와이퍼 각도
    if t >= 50.3:
        ph = (t - 50.3) * 1.6 * 2 * math.pi
        ang = 20 + 70 * (0.5 - 0.5 * math.cos(ph))
        wip = (ang, ang)
    else:
        wip = (12, 12)
    husband_out = ease((t - 41.2) / 0.8)

    def people(pen_, cx, by, u):
        # 운전석의 여자 (앞유리 너머)
        hh = 3.2 * u
        draw_woman(pen_, cx - 1.3 * u, by + 0.62 * hh, t, teary=0.4, talk=talking(t, "여자"), height=hh, umbrella=False)

    draw_car_front(pen, 400, 1560, 1.05, (232, 232, 238), plate="34나 7890", wiper=wip, people=people)
    # 조수석 창문 밖으로 고개 내민 남편
    stiff = t >= 46.8
    pale = clamp((t - 46.8) / 0.4) if stiff else 0
    # 남자 (오른쪽, 비 맞으며)
    draw_man(pen, 950, 1740, t, pose="down" if t >= 48.0 else "up", talk=talking(t, "남자"), height=820)
    hx = lerp(640, 785, husband_out)
    draw_husband(pen, hx, 1130, t, state="stiff" if stiff else "calm", talk=talking(t, "남편"), size=200, pale=pale)
    # 굳음 효과
    if stiff:
        dd = ImageDraw.Draw(frame, "RGBA")
        k = ease_out_back((t - 46.8) / 0.35)
        text_c(dd, (800, 880 - 40 * k), "(굳음)", F("comic", int(56 * max(k, 0.1))), (170, 200, 255), stroke=6)
    # 끼익 효과
    if t >= 50.5:
        dd = ImageDraw.Draw(frame, "RGBA")
        if int((t - 50.3) * 3.2) % 2 == 0:
            text_c(dd, (250, 720), "끼익~", F("comic", 70), (255, 255, 255), stroke=7)
        else:
            text_c(dd, (560, 690), "끼익~", F("comic", 70), (255, 255, 255), stroke=7)
    return frame


# ---------------------------------------------------------------- ending card
def render_end(t):
    lt = t - 53.5
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(H):
        d.line([(0, y), (W, y)], fill=mix((255, 150, 60), (190, 40, 80), y / H))
    # 햇살
    cx, cy = W / 2, 820
    for k in range(18):
        a = math.radians(k * 20 + lt * 12)
        d.polygon([(cx, cy), (cx + math.cos(a) * 1600, cy + math.sin(a) * 1600),
                   (cx + math.cos(a + 0.17) * 1600, cy + math.sin(a + 0.17) * 1600)], fill=(255, 255, 255, 28))
    t1 = clamp(lt / 0.4)
    text_c(d, (W / 2, 330), "차는 못 빼드려도,", F("comic", 78), (255, 255, 255, int(255 * t1)), stroke=7)
    if lt > 0.8:
        k = ease_out_back((lt - 0.8) / 0.4)
        text_c(d, (W / 2, 450), "인생 2막 길은 열어드립니다!", F("title", int(84 * max(k, 0.05))), (255, 236, 90), stroke=8)
    if lt > 1.8:
        k = ease_out_back((lt - 1.8) / 0.5)
        s = max(k, 0.05)
        pw = 900 * s
        d.rounded_rectangle([W / 2 - pw / 2, 720 - 170 * s, W / 2 + pw / 2, 720 + 190 * s], radius=int(60 * s),
                            fill=(255, 255, 255, 240))
        d.text((W / 2, 680), "광교오후학교", font=F("title", int(150 * s) + 1), fill=(240, 110, 30), anchor="mm")
        d.text((W / 2, 825), "with 블레스50플러스", font=F("title", int(70 * s) + 1), fill=(30, 60, 140), anchor="mm")
    if lt > 3.0:
        a = clamp((lt - 3.0) / 0.4)
        text_c(d, (W / 2, 1060), "50+ 오후 인생,", F("comic", 76), (255, 255, 255, int(255 * a)), stroke=7)
        text_c(d, (W / 2, 1160), "멈춰 서 있지 말고 다시 움직이세요", F("comic", 64), (255, 255, 255, int(255 * a)), stroke=7)
    if lt > 3.8:
        a = clamp((lt - 3.8) / 0.3)
        pulse = 1 + 0.05 * math.sin(lt * 8)
        bw, bh = 760 * pulse, 150 * pulse
        d.rounded_rectangle([W / 2 - bw / 2, 1380 - bh / 2, W / 2 + bw / 2, 1380 + bh / 2], radius=75,
                            fill=(30, 60, 140, int(250 * a)))
        d.text((W / 2, 1380), "지금 바로 문의하세요!", font=F("title", int(66 * pulse)), fill=(255, 255, 255, int(255 * a)),
               anchor="mm")
        text_c(d, (W / 2, 1530), "프로필 링크 / 댓글로 문의 주세요", F("comic", 50), (255, 255, 255, int(255 * a)), stroke=6)
    # 작은 차 한 대가 드디어 빠져나감
    if lt > 1.0:
        x = lerp(-420, W + 420, clamp((lt - 1.0) / 4.5))
        pen = Pen(ImageDraw.Draw(img), Cam(0, 0, W))
        draw_car_side(pen, x - 300, 1790, 0.75, (46, 92, 150))
        text_c(d, (x, 1560), "드디어 출발~!", F("comic", 44), (255, 255, 255), stroke=5)
    return img


# ---------------------------------------------------------------- hook (0~3초)
def draw_hook(img, t):
    if t >= 3.0:
        return
    d = ImageDraw.Draw(img, "RGBA")
    a = clamp((3.0 - t) / 0.4)
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(110 * a)))
    k = ease_out_back(t / 0.5)
    text_c(d, (W / 2, 700), "비 오는 밤,", F("drama", int(80 * max(k, 0.05))), (255, 255, 255, int(255 * a)), stroke=5)
    text_c(d, (W / 2, 820), "20년 만에 나타난 남자", F("title", int(104 * max(k, 0.05))), (255, 230, 90, int(255 * a)),
           stroke=8)
    if t > 0.9:
        k2 = ease_out_back((t - 0.9) / 0.4)
        text_c(d, (W / 2, 990), "그가 기다린 진짜 이유는...?", F("comic", int(72 * max(k2, 0.05))), (255, 255, 255, int(255 * a)),
               stroke=7)
    if t > 1.8:
        text_c(d, (W / 2, 1130), "(끝까지 보세요)", F("comic", 52), (255, 180, 180, int(255 * a)), stroke=5)


# ---------------------------------------------------------------- audio
def adsr_note(freq, dur, sr=SR, amp=0.3, kind="piano"):
    n = int(dur * sr)
    tt = np.arange(n) / sr
    if kind == "piano":
        sig = (np.sin(2 * np.pi * freq * tt) + 0.45 * np.sin(2 * np.pi * 2 * freq * tt) * np.exp(-tt * 3)
               + 0.2 * np.sin(2 * np.pi * 3 * freq * tt) * np.exp(-tt * 5) + 0.08 * np.sin(2 * np.pi * 4.01 * freq * tt) * np.exp(-tt * 7))
        env = np.exp(-tt * 2.2) * np.minimum(1, tt / 0.004)
    elif kind == "bell":
        sig = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * 2.76 * freq * tt) * np.exp(-tt * 6)
        env = np.exp(-tt * 3.5) * np.minimum(1, tt / 0.003)
    elif kind == "brass":
        vib = 1 + 0.012 * np.sin(2 * np.pi * 5.5 * tt) * np.minimum(1, tt / 0.3)
        ph = 2 * np.pi * np.cumsum(freq * vib) / sr
        sig = sum((1 / k) * np.sin(k * ph) for k in range(1, 9))
        env = np.minimum(1, tt / 0.04) * np.minimum(1, (dur - tt) / 0.08)
    else:
        sig = np.sin(2 * np.pi * freq * tt)
        env = np.minimum(1, tt / 0.01) * np.minimum(1, (dur - tt) / 0.05)
    return (sig * env * amp).astype(np.float32)


def nfreq(name):
    notes = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((notes[n] + (o - 4) * 12) / 12)


def add(buf, sig, t):
    i = int(t * SR)
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i]


def lowpass(x, a):
    y = np.empty_like(x)
    acc = 0.0
    # 1차 IIR 저역통과 (벡터화: 청크 반복)
    out = np.zeros_like(x)
    b = 1 - a
    # scipy 없이 빠르게: 누적 방식
    from itertools import accumulate
    out = np.fromiter(accumulate(x, lambda p, v: p * a + v * b), dtype=np.float32, count=len(x))
    return out


def build_audio(path):
    n = int(DUR * SR)
    rng = np.random.default_rng(1)
    buf = np.zeros(n, np.float32)
    # 빗소리 (전 구간)
    noise = rng.standard_normal(n).astype(np.float32)
    rain = lowpass(noise, 0.55) * 0.05 + lowpass(noise, 0.9) * 0.04
    drops = np.zeros(n, np.float32)
    for _ in range(3000):
        i = rng.integers(0, n - 800)
        drops[i:i + 400] += (rng.standard_normal(400) * np.exp(-np.arange(400) / 60) * 0.03).astype(np.float32)
    rain_env = np.ones(n, np.float32)
    ts = np.arange(n) / SR
    rain_env[ts >= 53.5] = np.clip(1 - (ts[ts >= 53.5] - 53.5) / 1.0, 0.0, 1) * 1.0
    buf += (rain + drops) * rain_env

    # 애절한 피아노 (Am - F - C - G / Am - F - G - E), 6 ~ 33초
    music = np.zeros(n, np.float32)
    prog = [["A2", "E3", "A3", "C4", "E4", "C4", "A3", "E3"],
            ["F2", "C3", "F3", "A3", "C4", "A3", "F3", "C3"],
            ["C3", "G3", "C4", "E4", "G4", "E4", "C4", "G3"],
            ["G2", "D3", "G3", "B3", "D4", "B3", "G3", "D3"],
            ["A2", "E3", "A3", "C4", "E4", "C4", "A3", "E3"],
            ["F2", "C3", "F3", "A3", "C4", "A3", "F3", "C3"],
            ["G2", "D3", "G3", "B3", "D4", "B3", "G3", "D3"],
            ["E2", "B2", "E3", "G#3", "B3", "G#3", "E3", "B2"]]
    melody = [("E5", 2), ("D5", 1), ("C5", 1), ("C5", 2), ("B4", 2), ("C5", 1), ("D5", 1), ("E5", 2), ("D5", 2),
              ("C5", 2), ("B4", 1), ("A4", 1), ("A4", 3), ("B4", 1), ("C5", 2), ("E5", 2), ("B4", 4)]
    step = 0.31
    t = 0.6
    bar = 0
    while t < 33.0:
        chord = prog[bar % len(prog)]
        loud = 0.55 + 0.45 * clamp((t - 6) / 22) + (0.5 if t > 28.3 else 0)
        for k, nn in enumerate(chord):
            tt = t + k * step
            if tt >= 33.0:
                break
            add(music, adsr_note(nfreq(nn), 2.2, amp=0.07 * loud), tt)
        if t > 28.2:  # 절정: 옥타브 화음 강타
            for nn in chord[:5:2]:
                add(music, adsr_note(nfreq(nn) * 2, 2.5, amp=0.08 * loud), t)
            add(music, adsr_note(nfreq(chord[0]) / 2, 3.0, amp=0.12 * loud), t)
        t += step * 8
        bar += 1
    t = 6.0
    mi = 0
    beat = step * 2
    while t < 33.0:
        nn, ln = melody[mi % len(melody)]
        loud = 0.7 + 0.5 * clamp((t - 6) / 22) + (0.4 if t > 28.3 else 0)
        add(music, adsr_note(nfreq(nn), ln * beat + 1.2, amp=0.09 * loud), t)
        if t > 28.2:
            add(music, adsr_note(nfreq(nn) * 2, ln * beat + 1.2, amp=0.05 * loud), t)
        t += ln * beat
        mi += 1
    # 리버브
    ir_n = int(1.6 * SR)
    ir = (rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / (0.35 * SR))).astype(np.float32) * 0.02
    ir[0] = 1.0
    L = 1 << int(np.ceil(np.log2(n + ir_n)))
    wet = np.fft.irfft(np.fft.rfft(music, L) * np.fft.rfft(ir, L), L)[:n].astype(np.float32)
    wet[ts >= 33.0] = 0  # 음악 "뚝"
    fade = np.clip((33.0 - ts) / 0.02, 0, 1).astype(np.float32)
    buf += wet * fade * 0.9

    # 레코드 스크래치 (33.0초)
    dn = int(0.45 * SR)
    tt = np.arange(dn) / SR
    f = 900 * np.exp(-tt * 5) + 120
    ph = 2 * np.pi * np.cumsum(f) / SR
    scratch = (np.sign(np.sin(ph)) * 0.25 + rng.standard_normal(dn) * 0.25) * np.exp(-tt * 5)
    add(buf, scratch.astype(np.float32) * 0.6, 33.0)
    # 부재중 전화 진동 + 알림음
    for k in range(2):
        tt = np.arange(int(0.35 * SR)) / SR
        vib = (np.sin(2 * np.pi * 150 * tt) * (np.sin(2 * np.pi * 25 * tt) > 0)).astype(np.float32) * 0.25
        add(buf, vib, 35.4 + k * 1.0)
    add(buf, adsr_note(nfreq("E6"), 0.6, amp=0.15, kind="bell"), 35.45)
    add(buf, adsr_note(nfreq("B6"), 0.8, amp=0.15, kind="bell"), 35.6)
    # 사이드 브레이크 "드르륵"
    tt = np.arange(int(0.5 * SR)) / SR
    ratchet = (rng.standard_normal(len(tt)) * (np.sin(2 * np.pi * 30 * tt) > 0.7)).astype(np.float32) * 0.2
    add(buf, ratchet, 38.2)
    # 창문 내려가는 소리
    tt = np.arange(int(0.8 * SR)) / SR
    motor = (np.sin(2 * np.pi * (180 + 20 * tt) * tt) * 0.08 + rng.standard_normal(len(tt)) * 0.02).astype(np.float32)
    add(buf, motor, 41.2)
    # 두둥 (남편 굳음)
    for k, fr in enumerate([70, 55]):
        tt = np.arange(int(0.7 * SR)) / SR
        hit = (np.sin(2 * np.pi * fr * tt * (1 - 0.3 * tt)) * np.exp(-tt * 5)).astype(np.float32) * 0.6
        add(buf, hit, 46.8 + k * 0.28)
    # 와이퍼 끼익 + 슬픈 트롬본 (wah wah wah waaah)
    for k in range(5):
        tt = np.arange(int(0.22 * SR)) / SR
        fr = 1500 + 400 * np.sin(2 * np.pi * 7 * tt)
        sq = (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * tt / tt[-1])).astype(np.float32) * 0.05
        add(buf, sq, 50.3 + 0.3125 * k * 2 + 0.05)
    for i, (nn, dd) in enumerate([("D4", 0.45), ("C#4", 0.45), ("C4", 0.45), ("B3", 1.3)]):
        add(buf, adsr_note(nfreq(nn), dd, amp=0.11, kind="brass"), 50.6 + i * 0.5)
    # 엔딩 징글 (밝은 C장조)
    jt = 53.5
    for i, nn in enumerate(["C5", "E5", "G5", "C6", "E6"]):
        add(buf, adsr_note(nfreq(nn), 1.0, amp=0.12, kind="bell"), jt + i * 0.12)
    bouncy = [("C4", "E4", "G4"), ("F4", "A4", "C5"), ("G4", "B4", "D5"), ("C4", "E4", "G4")]
    for b_, ch in enumerate(bouncy * 2):
        for k in range(4):
            tt0 = jt + 0.8 + b_ * 0.8 + k * 0.2
            if tt0 > DUR - 0.4:
                break
            add(buf, adsr_note(nfreq(ch[k % 3]), 0.4, amp=0.06, kind="piano"), tt0)
            if k % 2 == 0:
                add(buf, adsr_note(nfreq(ch[0]) / 2, 0.5, amp=0.08, kind="piano"), tt0)
    buf *= np.clip((DUR - ts) / 0.8, 0, 1).astype(np.float32)
    peak = np.max(np.abs(buf))
    buf = buf / peak * 0.89
    pcm = (buf * 32767).astype(np.int16)
    stereo = np.stack([pcm, pcm], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


# ---------------------------------------------------------------- main render
def render_frame(t, world, carbg):
    global VIG
    if t >= 53.5:
        return render_end(t)
    if t >= 41.2:
        img = render_car_scene(carbg, t)
        cam = None
    else:
        img, cam = render_world_scene(world, t)
    d = ImageDraw.Draw(img)
    draw_rain(d, t, 1.0)
    # 드라마 구간은 푸르스름한 비네팅
    if t < 33.3:
        if VIG is None:
            VIG = vignette_mask()
        dark = Image.new("RGB", (W, H), (0, 0, 12))
        img = Image.composite(img, dark, VIG)
    # 음악 뚝! 순간 플래시
    if 33.3 <= t < 33.45:
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.6)
    if cam is not None:
        draw_reveal_labels(img, t, cam)
    draw_hook(img, t)
    draw_header(img, t)
    for it in DIRS:
        draw_direction(img, t, it)
    for s in SUBS:
        draw_sub(img, t, s)
    if 33.3 <= t < 35.0:
        d2 = ImageDraw.Draw(img, "RGBA")
        k = ease_out_back((t - 33.3) / 0.3)
        text_c(d2, (W / 2, 520), "(음악 뚝)", F("comic", int(90 * max(k, 0.05))), (255, 255, 255), stroke=8)
    return img


def main(preview=None):
    world = build_world()
    carbg = build_car_bg()
    if preview:
        os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
        for t in preview:
            render_frame(t, world, carbg).save(os.path.join(HERE, "preview", f"f_{t:05.1f}.jpg"), quality=85)
        return
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    wav = os.path.join(HERE, "_audio.wav")
    build_audio(wav)
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    nf = int(DUR * FPS)
    for i in range(nf):
        t = i / FPS
        random.seed(i)
        p.stdin.write(render_frame(t, world, carbg).convert("RGB").tobytes())
        if i % 150 == 0:
            print(f"{i}/{nf}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("done:", OUT)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        main(preview=[float(x) for x in sys.argv[2:]])
    else:
        main()
