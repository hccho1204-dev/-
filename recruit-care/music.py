"""
요양보호사 리크루팅 영상 음악 — 120 BPM, 정확히 20초 (40비트, 1비트 = 0.5초)
코드로 직접 합성 → 저작권 걱정 없음, 상업적 사용 가능.

  b0~15  (0~8초)   WANTED 구간 : 밝은 패드 + 초침 소리 + 가벼운 킥
  b14~16           라이저(빌드업)
  b16~32 (8~16초)  전환 구간 : 밝은 메이저 코드로 터짐, 경쾌한 그루브
  b32~38 (16~19초) 엔딩     : 매 비트 '팡' → 화면 요소가 튀어나옴
  b38              마지막 한 방

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
rng = np.random.default_rng(21)
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



def tick():
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.004)


def pad(ms, dur):
    s = sum(saw(note(m), dur, (-0.006, 0, 0.006)) for m in ms) / len(ms)
    n = len(s)
    e = np.minimum(np.linspace(0, 1, n) * 4, 1) * np.minimum(np.linspace(1, 0, n) * 4, 1)
    return lowpass(s * e, 0.05)


K, C, H, HO = kick(), clap(), hat(), hat(0.06)

# ---- 공감 구간 (0~8초): Am - F - C - G, 어둡고 잔잔하게
SAD = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]  # 밝은 C-G-Am-F
for bar in range(4):
    add(pad(SAD[bar], 2.1), bar * 2.0, 0.5)
    for k in range(4):
        m = SAD[bar][[0, 2, 1, 2][k]] + 12
        add(pluck(m, 0.5) * 0.7, bar * 2.0 + k * B, 0.18, 0.3 if k % 2 else -0.3)
for b in range(16):
    add(tick(), b * B, 0.12, 0.4)                 # 시계 초침
    add(K, b * B, 0.45 if b >= 8 else 0.3)        # 가벼운 킥 (점점 세게)
    if b >= 8 and b % 2 == 1:
        add(C, b * B, 0.3)
add(whoosh(1.5), 6.5, 0.5)

# ---- 전환 구간 (8~16초): C - G - Am - F, 밝게
HAPPY = [([60, 64, 67, 72], 48), ([55, 59, 62, 67], 43), ([57, 60, 64, 69], 45), ([53, 57, 60, 65], 41)]
ARP = [0, 1, 2, 3, 2, 1, 3, 2]
for b in range(16, 38):
    t = b * B
    ch, root = HAPPY[(b // 4) % 4]
    pos = b % 4
    ending = b >= 32
    if ending:
        add(K, t, 0.8)
        add(chord([m + 12 for m in ch], B * 0.9, 0.35), t, 0.45)
        add(pop(84 + (b - 32) * 2), t, 0.25, (b % 2) * 0.6 - 0.3)
        continue
    add(K, t, 0.95)
    if pos in (1, 3):
        add(C, t, 0.55, 0.1)
    add(H, t + B / 2, 0.6, -0.3)
    add(H, t + B / 4, 0.25, 0.3)
    add(H, t + 3 * B / 4, 0.25, 0.3)
    if pos == 3:
        add(HO, t + B / 2, 0.4)
    add(bass(root - 12, B * 0.45), t + B / 2, 0.55)
    add(chord(ch, B * 0.7, 0.25), t, 0.25)
    for k in range(4):
        add(pluck(ch[ARP[(b * 4 + k) % 8]] + 12), t + k * B / 4, 0.14, 0.3 if k % 2 else -0.3)

add(impact(), 8.0, 1.0)                 # 전환의 순간
add(whoosh(1.0), 15.0, 0.4)
add(impact(1.2), 16.0, 0.7)
add(impact(2.0), 19.0, 0.9)             # 마지막 한 방
add(chord([60, 64, 67, 72, 76], 1.0, 0.3), 19.0, 0.5)

t = np.arange(N) / SR
duck = 1 - 0.38 * np.exp(-((t % B) / 0.07)) * ((t > 8) & (t < 16))
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
print("out/music.wav 생성 완료 (정확히 20초, 120 BPM)")
