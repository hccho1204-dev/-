"""
캘리그라피 영상 음악: 64 BPM 잔잔한 피아노 발라드, 정확히 41.25초 (11마디, 글씨 1장 = 1마디). 직접 합성 → 저작권 걱정 없음.
실행: python3 music.py → out/music.wav
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 64   # 1마디 = 3.75초, 사진 1장 = 1마디
B = 60 / BPM
DUR = 41.25
N = int(SR * DUR)
rng = np.random.default_rng(7)
mix = np.zeros((N, 2))


def add(sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N or i < 0:
        return
    sig = sig[: N - i]
    mix[i:i + len(sig), 0] += sig * gain * np.sqrt(0.5 * (1 - pan))
    mix[i:i + len(sig), 1] += sig * gain * np.sqrt(0.5 * (1 + pan))


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def onepole(x, a):
    # 간단한 로우패스 (블록 단위 근사 없이 정확히)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def env(n, a, d, rel=0.0):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    if rel:
        nr = min(n, int(rel * SR))
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def musicbox(m, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note(m)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9)
    s += 0.35 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / 0.35)
    s += 0.18 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.08)
    s[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return s


def bell(m, dur=2.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note(m)
    mod = 1.2 * np.exp(-t / 0.4) * np.sin(2 * np.pi * f * 3.5 * t)
    s = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 0.8)
    return s * env(n, 0.003, 10)


def epiano(m, dur):
    n = int((dur + 0.6) * SR)
    t = np.arange(n) / SR
    f = note(m)
    mod = 0.8 * np.exp(-t / 0.25) * np.sin(2 * np.pi * f * t)
    s = np.sin(2 * np.pi * f * t + mod) + 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / 0.3)
    s *= 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    return s * env(n, 0.004, 0.9, rel=0.3)


def pad(ms, dur, cut=0.03, att=0.6):
    n = int((dur + 0.8) * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for m in ms:
        for d in (-0.006, 0, 0.006):
            s += 2 * ((t * note(m) * (1 + d) + rng.random()) % 1) - 1
    s = onepole(s / (len(ms) * 3), cut)
    e = np.minimum(1, t / att) * np.where(t > dur, np.exp(-(t - dur) / 0.3), 1)
    return s * e


def bass(m, dur):
    n = int((dur + 0.3) * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * note(m) * t) + 0.15 * np.sin(4 * np.pi * note(m) * t)
    return s * env(n, 0.01, dur * 0.9, rel=0.25)


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 46 + 70 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)


def snap():
    n = int(0.2 * SR)
    t = np.arange(n) / SR
    s = onepole(np.diff(rng.standard_normal(n), prepend=0), 0.5)
    return s * np.exp(-t / 0.04) * 0.6


def shaker():
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    s = np.diff(rng.standard_normal(n), prepend=0)
    return s * np.minimum(1, t / 0.01) * np.exp(-t / 0.025) * 0.15


def swell(dur):
    n = int(dur * SR)
    x = onepole(rng.standard_normal(n), 0.08)
    return x * np.linspace(0, 1, n) ** 2.5


def boom(len_=2.5):
    n = int(len_ * SR)
    t = np.arange(n) / SR
    f = 38 + 30 * np.exp(-t / 0.1)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)



BAR = 4 * B
# C - Am - F - G - C - Em - Am - F - Dm - G - C
PROG = [([48, 52, 55, 60], 36), ([45, 52, 57, 60], 33), ([41, 53, 57, 60], 29), ([43, 55, 59, 62], 31),
        ([48, 52, 55, 64], 36), ([40, 55, 59, 64], 28), ([45, 52, 57, 60], 33), ([41, 53, 57, 65], 29),
        ([38, 53, 57, 62], 26), ([43, 55, 59, 65], 31), ([48, 52, 55, 64], 36)]
# 멜로디 (박, 음, 길이박)
MEL = {1: [(0, 76, 2), (2, 74, 1), (3, 72, 1)], 2: [(0, 72, 2), (2, 69, 2)], 3: [(0, 71, 1.5), (1.5, 72, 0.5), (2, 74, 2)],
       4: [(0, 76, 2), (2, 79, 1), (3, 76, 1)], 5: [(0, 79, 1.5), (1.5, 76, 0.5), (2, 74, 2)], 6: [(0, 72, 1), (1, 76, 1), (2, 81, 2)],
       7: [(0, 81, 1), (1, 79, 1), (2, 77, 1), (3, 76, 1)], 8: [(0, 74, 1.5), (1.5, 77, 0.5), (2, 81, 2)],
       9: [(0, 79, 2), (2, 83, 1), (3, 86, 1)], 10: [(0, 84, 4)]}
K = kick()
for bar, (ch, root) in enumerate(PROG):
    t0 = bar * BAR
    last = bar == len(PROG) - 1
    lv = 0.7 if bar == 0 else (1.0 if bar < 5 else 1.15)
    # 피아노 분산화음 (8분음표)
    pat = [0, 1, 2, 3, 2, 1, 2, 3]
    for k in range(1 if last else 8):
        m = ch[pat[k]] + (12 if pat[k] > 0 and ch[pat[k]] < 60 else 0)
        add(epiano(m, B * (3 if last else 0.9)), t0 + k * B / 2, 0.09 * lv, -0.3 + 0.2 * pat[k])
    if last:
        for i, m in enumerate(ch[1:] + [ch[1] + 12]):
            add(epiano(m, BAR * 1.6), t0 + 0.05 + i * 0.06, 0.12, -0.3 + i * 0.2)
    add(bass(root + 12 if root < 30 else root, BAR * (1.6 if last else 0.95)), t0, 0.32 * lv)
    if bar >= 4:
        add(pad([m for m in ch[1:]], BAR + (2.5 if last else 0), 0.02, 0.8), t0, 0.16 if bar < 9 else 0.22)
    for b, m, d in MEL.get(bar, []):
        add(epiano(m, B * d), t0 + b * B, 0.2, 0.1)
        add(musicbox(m + 12, 2.0), t0 + b * B, 0.07 if bar < 5 else 0.11, 0.25)
    # 심장박동 같은 부드러운 킥 (5마디부터)
    if 5 <= bar <= 9:
        add(K, t0, 0.32); add(K, t0 + 2 * B, 0.22)

for bar in range(1, 10):
    add(swell(0.6), bar * BAR - 0.6, 0.04)
add(swell(BAR), 8 * BAR, 0.12)
add(boom(3.0), 9 * BAR, 0.3)
for i, m in enumerate([84, 88, 91, 96, 100]):
    add(bell(m, 2.5), 10 * BAR + 0.2 + i * 0.12, 0.06, -0.4 + i * 0.2)

# 아주 옅은 공기감
mix[:, 0] += onepole(rng.standard_normal(N), 0.3) * 0.006
mix[:, 1] += onepole(rng.standard_normal(N), 0.3) * 0.006
# 간단한 리버브 (딜레이 합)
dry = mix.copy()
for d, g in [(0.083, 0.28), (0.131, 0.22), (0.197, 0.17), (0.271, 0.12), (0.353, 0.08)]:
    i = int(d * SR)
    mix[i:, 0] += dry[:-i, 1] * g
    mix[i:, 1] += dry[:-i, 0] * g

mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.2) / np.tanh(1.2) * 0.9
tt = np.arange(N) / SR
mix *= (np.clip((DUR - tt) / 2.0, 0, 1) ** 0.7 * np.clip(tt / 0.2, 0, 1))[:, None]

os.makedirs("out", exist_ok=True)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("out/music.wav 생성 완료 (41.25초, 64 BPM, 11마디)")
