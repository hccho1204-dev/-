"""
모벨릭스 광고 음악 — 96 BPM 힙합/트랩 비트, 정확히 20초 (32비트, 1비트 = 0.625초)
코드로 직접 합성 → 저작권 걱정 없음, 상업적 사용 가능.

  b0~3   인트로   : 808 한 방 + 일렉트릭 피아노 코드
  b4~19  그루브   : 붐뱁 킥·스네어 + 트랩 하이햇 롤 + 808 베이스
  b20~25 하이라이트: 하이햇 더 촘촘하게
  b26~29 엔딩     : 매 비트 '팡' (화면 요소가 튀어나옴)
  b30    마지막 한 방
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 96
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


# Dm7 - Bbmaj7 - Gm7 - A7
PROG = [([62, 65, 69, 72], 38), ([58, 62, 65, 69], 34), ([55, 58, 62, 65], 31), ([57, 61, 64, 67], 33)]
K, C, H = kick(), clap(), hat(0.01)

for b in range(30):
    t = b * B
    bar, pos = b // 4, b % 4
    ch, root = PROG[bar % 4]
    if pos == 0:
        add(epiano(ch, B * 4), t, 0.32)
    if b < 4:
        if b == 0:
            add(b808(root, B * 3.5, root + 12), t, 0.8)
        continue
    if b >= 26:   # 엔딩: 매 비트 팡
        add(K, t, 0.9)
        add(C, t, 0.35)
        add(pop(86 + (b - 26) * 3), t, 0.3, (b % 2) * 0.6 - 0.3)
        add(b808(root, B * 0.9), t, 0.5)
        continue
    # 붐뱁 킥 패턴
    if pos == 0:
        add(K, t, 1.0)
    if pos == 1:
        add(K, t + B * 0.75, 0.7)
    if pos == 2:
        add(K, t + B * 0.5, 0.85)
    # 스네어(클랩) 2, 4박
    if pos in (1, 3):
        add(C, t, 0.7, 0.05)
    # 트랩 하이햇: 8분, 마디 끝엔 32분 롤
    dense = b >= 20
    div = 4 if dense else 2
    for k in range(div):
        add(H, t + k * B / div, 0.5 if k % 2 == 0 else 0.3, -0.25)
    if pos == 3:
        for k in range(8):
            add(H, t + B / 2 + k * B / 16, 0.18 + 0.03 * k, 0.3)
    # 808 베이스
    if pos == 0:
        add(b808(root, B * 1.6), t, 0.75)
    if pos == 2:
        add(b808(root + 7, B * 0.6, root), t + B * 0.5, 0.55)

add(impact(), 0.0, 0.7)
add(whoosh(B * 2), 4 * B - B * 1.5, 0.3)
add(whoosh(B * 2), 12 * B - B * 1.5, 0.3)
add(whoosh(B * 2), 20 * B - B * 1.5, 0.35)
add(impact(1.2), 20 * B, 0.6)
add(whoosh(B * 2), 26 * B - B * 1.5, 0.35)
add(impact(1.6), 30 * B, 0.95)
add(epiano([62, 65, 69, 72, 76], 1.2), 30 * B, 0.4)

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
print("out/music.wav 생성 완료 (정확히 20초, 96 BPM)")
