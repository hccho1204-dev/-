"""
인동 가을소풍 워크숍 영상 음악: 120 BPM 신나는 마림바 팝, 정확히 20초 (= 40비트).
코드로 직접 합성 → 저작권 걱정 없음.

구간 (비트 b, 1비트 = 0.5초)
  b0~6    타이틀      : 임팩트 + 마림바 리프
  b6~11   포스터      : 그루브 시작
  b11~22  1일차 일정  : 항목이 뜰 때마다 '뿅'
  b22~30  2일차 일정  : 같은 그루브, b28~30 스네어 빌드업
  b30~36  조 편성     : 드롭 (가장 신나는 구간)
  b36~40  엔딩        : 매 비트 스탭, b39 마지막 한 방

실행: python3 music.py  →  out/music.wav
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 120
B = 60 / BPM
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(29)
mix = np.zeros((N, 2))
def add(sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N:
        return
    sig = sig[: N - i]
    mix[i:i + len(sig), 0] += sig * gain * np.sqrt(0.5 * (1 - pan))
    mix[i:i + len(sig), 1] += sig * gain * np.sqrt(0.5 * (1 + pan))


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def lowpass(x, a):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def env(n, a, d):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def kick():
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = 48 + 140 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    s += 0.5 * rng.standard_normal(n) * np.exp(-t / 0.003)
    return np.tanh(s * 2.2)


def clap():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    s = np.diff(rng.standard_normal(n), prepend=0)
    e = np.exp(-t / 0.07)
    for off in (0.0, 0.01, 0.02):
        k = int(off * SR)
        e[k:] += 0.7 * np.exp(-t[: n - k] / 0.008)
    return s * e * 0.5


def snare():
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    s = 0.6 * np.diff(rng.standard_normal(n), prepend=0) * np.exp(-t / 0.05)
    s += 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
    return s


def hat(d=0.014):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    s = np.diff(np.diff(rng.standard_normal(n), prepend=0), prepend=0)
    return s * np.exp(-t / d) * 0.22


def saw(f, dur, voices=(-0.01, -0.004, 0, 0.004, 0.01)):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return sum(2 * ((t * f * (1 + d) + rng.random()) % 1) - 1 for d in voices) / len(voices)


def pluck(m, dur=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * note(m) * t) + 0.4 * np.sin(4 * np.pi * note(m) * t)
    s += 0.2 * (2 * ((t * note(m)) % 1) - 1)
    return s * env(n, 0.002, 0.07)


def chord(ms, dur, cut=0.2):
    s = sum(saw(note(m), dur) for m in ms) / len(ms)
    n = len(s)
    return lowpass(s * env(n, 0.01, dur * 0.6), cut)


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * note(m) * t) + 0.3 * np.tanh(3 * np.sin(2 * np.pi * note(m) * t))
    return s * env(n, 0.004, dur * 0.7)


def impact(len_=1.4):
    n = int(len_ * SR)
    t = np.arange(n) / SR
    f = 32 + 90 * np.exp(-t / 0.07)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    s += 0.35 * lowpass(rng.standard_normal(n), 0.25) * np.exp(-t / 0.35)
    return np.tanh(s * 2)


def whoosh(dur):
    n = int(dur * SR)
    a = np.linspace(0.01, 0.5, n)
    x = rng.standard_normal(n)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y * np.linspace(0, 1, n) ** 2


def pop(m):
    n = int(0.15 * SR)
    t = np.arange(n) / SR
    f = note(m) * (1 + 1.5 * np.exp(-t / 0.01))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05)



def marimba(m, dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.02)
    return s * np.exp(-t / 0.12)


def bell(m, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note(m)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) + 0.25 * np.sin(2 * np.pi * f * 5.4 * t)
    return s * np.exp(-t / 0.25) * 0.5


def boing(f0=180, f1=520, dur=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (t / dur) ** 0.5 + 25 * np.sin(2 * np.pi * 18 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)


def vroom(dur=0.35):
    # 귀여운 '붕' 소리 (낮은 톱니 + 피치 업)
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 70 + 90 * (t / dur)
    s = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return lowpass(s, 0.15) * np.minimum(1, t / 0.02) * np.exp(-t / 0.2)



# D - A - Bm - G (마디마다)
PROG = [([62, 66, 69], 38), ([61, 64, 69], 45), ([59, 62, 66], 47), ([59, 62, 67], 43)]
RIFF = [0, 2, 1, 2, 0, 2, 1, 2]
K, C, S, H, HO = kick(), clap(), snare(), hat(), hat(0.06)
ITEMS = [12, 13.5, 15, 16.5, 18, 23, 24, 25, 26, 27, 30.5, 31, 31.5, 32]

for b in range(40):
    t = b * B
    bar = b // 4
    ch, root = PROG[bar % 4]
    intro = b < 6
    build = 28 <= b < 30
    drop = 30 <= b < 36
    ending = b >= 36
    # 마림바 리프 (8분음표)
    if not ending:
        for k in range(2):
            m = ch[RIFF[(b * 2 + k) % 8]] + 12
            add(marimba(m), t + k * B / 2, 0.32 if not drop else 0.26, -0.3 if k else 0.3)
    if intro:
        if b >= 2:
            add(H, t + B / 2, 0.5, -0.2)
        continue
    if ending:
        if b < 39:
            add(K, t, 0.9)
            add(chord([m + 12 for m in ch], B * 0.8, 0.35), t, 0.45)
            add(bell(81 + (b - 36) * 2), t, 0.3, 0.3)
        continue
    # 킥
    if build:
        for k in range(4 if b == 29 else 2):
            add(S, t + k * B / (4 if b == 29 else 2), 0.35 + 0.1 * k)
        add(K, t, 0.8)
    else:
        add(K, t, 0.95)
        if b % 2 == 1:
            add(C, t, 0.55, 0.1)
    add(H, t + B / 2, 0.7, -0.3)
    if drop or b >= 11:
        add(H, t + B / 4, 0.25, 0.3)
        add(H, t + 3 * B / 4, 0.25, 0.3)
    if b % 4 == 3:
        add(HO, t + B / 2, 0.45, -0.2)
    # 베이스 (오프비트)
    add(bass(root - 12 if root > 40 else root, B * 0.45), t + B / 2, 0.6)
    # 코드 스탭
    if b >= 11 and not build:
        add(chord(ch, B * 0.35, 0.3 if drop else 0.2), t + B / 2, 0.28 if drop else 0.2)
    if drop:
        add(chord([m + 12 for m in ch], B * 0.3, 0.4), t, 0.2)
        add(bell(ch[(b % 3)] + 24), t + B / 2, 0.18, 0.4)

# 항목 등장 '뿅'
for i, b in enumerate(ITEMS):
    add(pop(86 + (i % 5) * 2), b * B, 0.3, (i % 2) * 0.6 - 0.3)

# 효과음
add(impact(), 0.0, 0.8)
add(boing(), 1.0 * B, 0.3)
add(whoosh(B * 2), 6 * B - B * 2, 0.4)
add(whoosh(B * 2), 11 * B - B * 2, 0.35)
add(whoosh(B * 2), 22 * B - B * 2, 0.35)
add(whoosh(B * 2), 28 * B, 0.55)
add(impact(), 30 * B, 1.0)
add(impact(1.2), 36 * B, 0.7)
add(impact(2.0), 39 * B, 0.9)
add(chord([62, 69, 74, 78, 81], 1.2, 0.3), 39 * B, 0.5)

# 사이드체인 + 마스터
tt = np.arange(N) / SR
duck = 1 - 0.35 * np.exp(-((tt % B) / 0.07)) * ((tt > 6 * B) & (tt < 36 * B))
mix *= duck[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.5) / np.tanh(1.5) * 0.92
fade = np.ones(N)
fade[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
mix *= fade[:, None]

os.makedirs("out", exist_ok=True)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("out/music.wav 생성 완료 (정확히 20초, 120 BPM, 40비트)")
