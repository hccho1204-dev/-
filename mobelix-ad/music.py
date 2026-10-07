"""
모벨릭스 광고 음악 — 144 BPM 퐁크/트랩 비트, 정확히 20초 (48비트, 1비트 = 0.4167초)
코드로 직접 합성 → 저작권 걱정 없음, 상업적 사용 가능.

  b0~5   인트로   : 카우벨 리프 + 라이저
  b6     드롭     : 임팩트 한 방
  b6~29  그루브   : 킥·클랩 + 16분 하이햇 + 808 슬라이드 + 카우벨 멜로디
  b30~38 그리드   : 하이햇 32분 + 스네어 롤 빌드업
  b39~44 엔딩     : 매 비트 '팡' (화면 요소가 튀어나옴)
  b45    마지막 한 방
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 144
B = 60 / BPM
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(96)
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



def b808(m, dur, glide_from=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = note(m)
    f = np.full(n, f0)
    if glide_from is not None:
        f = f0 + (note(glide_from) - f0) * np.exp(-t / 0.06)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    s = np.tanh(s * 2.2) * np.exp(-t / (dur * 0.8))
    s[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return s


def epiano(ms, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * note(m) * t) * (1 + 0.3 * np.sin(2 * np.pi * 5 * t)) + 0.25 * np.sin(4 * np.pi * note(m) * t) for m in ms) / len(ms)
    return s * np.exp(-t / (dur * 0.5)) * np.minimum(1, t / 0.005 + 1e-9)



def cowbell(m, dur=0.18):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note(m)
    s = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.48 * t))
    s = lowpass(s * 0.5, 0.35)
    return s * np.exp(-t / 0.06)


# Dm - Bb - Gm - A (2마디씩 = 8비트)
PROG = [38, 34, 31, 33]
RIFF = [74, 77, 81, 77, 74, 72, 74, 69]   # 16분음표 카우벨 리프
K, C, H, S = kick(), clap(), hat(0.008), snare()

for b in range(48):
    t = b * B
    root = PROG[(b // 8) % 4]
    pos = b % 4
    # 카우벨 리프 (8분음표 2개/비트)
    if b < 39:
        for k in range(2):
            m = RIFF[(b * 2 + k) % 8] + (0 if (b // 8) % 2 == 0 else -2)
            add(cowbell(m), t + k * B / 2, 0.22 if b >= 6 else 0.3, 0.2 if k else -0.2)
    if b < 6:
        if b >= 4:
            for k in range(4):
                add(S, t + k * B / 4, 0.2 + 0.08 * k + 0.15 * (b - 4))
        continue
    if 39 <= b < 45:          # 엔딩: 매 비트 팡
        add(K, t, 1.0)
        add(C, t, 0.45)
        add(pop(84 + (b - 39) * 3), t, 0.35, (b % 2) * 0.6 - 0.3)
        add(b808(root + 12, B * 0.9, root + 19), t, 0.55)
        continue
    if b >= 45:
        continue
    build = 36 <= b < 39
    # 킥: 1, 3박 + 당김
    if pos in (0, 2):
        add(K, t, 1.0)
    if pos == 3:
        add(K, t + B * 0.5, 0.75)
    if build:
        div = 4 if b < 38 else 8
        for k in range(div):
            add(S, t + k * B / div, 0.25 + 0.04 * k + 0.1 * (b - 36))
    elif pos in (1, 3):
        add(C, t, 0.7)
    # 하이햇: 16분, 그리드 구간은 32분
    div = 8 if b >= 30 else 4
    for k in range(div):
        add(H, t + k * B / div, 0.45 if k % 2 == 0 else 0.25, -0.3 if k % 2 else 0.3)
    # 808 슬라이드
    if pos == 0:
        add(b808(root, B * 1.8, root + 12 if (b // 4) % 2 else None), t, 0.8)
    if pos == 2:
        add(b808(root + 5, B * 0.8, root), t + B * 0.5, 0.55)

add(impact(), 0.0, 0.6)
add(whoosh(B * 4), 2 * B, 0.45)
add(impact(), 6 * B, 1.0)
add(whoosh(B * 2), 18 * B - B * 1.5, 0.35)
add(whoosh(B * 2), 30 * B - B * 1.5, 0.35)
add(whoosh(B * 3), 36 * B, 0.5)
add(impact(1.2), 39 * B, 0.85)
add(impact(2.0), 45 * B, 1.0)
add(epiano([62, 65, 69, 74, 77], 1.4), 45 * B, 0.4)

mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.6) / np.tanh(1.6) * 0.92
fade = np.ones(N)
fade[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
mix *= fade[:, None]
os.makedirs("out", exist_ok=True)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("out/music.wav 생성 완료 (정확히 20초, 144 BPM)")
