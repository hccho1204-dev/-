"""
모벨붕붕 추억여행 — 신나고 즐거운 150 BPM 팝 비트, 정확히 20초 (50비트, 1비트 = 0.4초)
코드로 직접 합성 → 저작권 걱정 없음, 상업적 사용 가능.

  b0~3   인트로   : 마림바 + '붕붕' 효과음
  b4~43  메인     : 통통 튀는 킥·박수·베이스 + 마림바 멜로디 + 반짝이 종소리
  b44~48 엔딩     : 매 비트 팡! + 콘페티 효과음
  b48    마지막 한 방
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 150
B = 60 / BPM
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(150)
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


# C - G - Am - F (4비트씩)
PROG = [([60, 64, 67], 36), ([55, 59, 62], 43), ([57, 60, 64], 45), ([53, 57, 60], 41)]
MEL = [72, 76, 79, 76, 74, 76, 72, 67, 69, 72, 76, 74, 72, 71, 72, 79]
K, C, H = kick(), clap(), hat()

for b in range(50):
    t = b * B
    ch, root = PROG[(b // 4) % 4]
    pos = b % 4
    # 마림바 멜로디 (8분음표)
    if b < 48:
        for k in range(2):
            m = MEL[(b * 2 + k) % 16]
            add(marimba(m), t + k * B / 2, 0.35 if b >= 4 else 0.45, 0.25 if k else -0.25)
    if b < 4:
        if b in (1, 3):
            add(vroom(), t, 0.5)
        continue
    if b >= 44:
        if b < 48:
            add(K, t, 0.9)
            add(C, t, 0.4)
            add(pop(84 + (b - 44) * 3), t, 0.35, (b % 2) * 0.6 - 0.3)
            add(bell(84 + (b - 44) * 2), t, 0.3)
        continue
    # 통통 튀는 4비트 킥
    add(K, t, 0.85)
    if pos in (1, 3):
        add(C, t, 0.55, 0.1)
    add(H, t + B / 2, 0.5, -0.3)
    add(H, t + B / 4, 0.22, 0.3)
    add(H, t + 3 * B / 4, 0.22, 0.3)
    # 오프비트 베이스
    add(bass(root, B * 0.45), t + B / 2, 0.5)
    # 코드 스탭 (2, 4박)
    if pos in (1, 3):
        add(chord([m + 12 for m in ch], B * 0.4, 0.3), t, 0.22)
    # 반짝이 종소리 (장면 시작마다)
    if b % 8 == 4:
        add(bell(84), t, 0.35, 0.4)
        add(boing(), t + B * 0.5, 0.25, -0.3)

add(impact(1.0), 0.0, 0.5)
for sb in (4, 12, 20, 28, 36):
    add(whoosh(B * 1.5), sb * B - B * 1.3, 0.25)
add(impact(1.2), 44 * B, 0.6)
add(impact(1.6), 48 * B, 0.85)
add(chord([60, 64, 67, 72, 76], 1.0, 0.35), 48 * B, 0.45)
add(bell(96, 1.0), 48 * B, 0.35)

t = np.arange(N) / SR
duck = 1 - 0.3 * np.exp(-((t % B) / 0.06)) * ((t > 4 * B) & (t < 44 * B))
mix *= duck[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.4) / np.tanh(1.4) * 0.92
fade = np.ones(N)
fade[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
mix *= fade[:, None]
os.makedirs("out", exist_ok=True)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("out/music.wav 생성 완료 (정확히 20초, 150 BPM)")
