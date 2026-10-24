"""
'버팀에 관한 다섯 문장' 쇼츠 음악: 72 BPM 잔잔한 로파이 피아노, 정확히 20초 (= 24비트 = 6마디).
코드로 직접 합성 → 저작권 걱정 없음.

구간 (마디 = 3.33초, 화면 장면과 1:1로 맞춤)
  1마디 Am  벼 들판      : 피아노 + 레코드 잡음만
  2마디 F   호수 위 집    : 킥·스냅·셰이커 들어옴
  3마디 C   나무 데크길
  4마디 G   장독대        : 마지막 문장 전 부드러운 상승
  5마디 F   마지막 문장    : 낮은 울림 + 오르골 멜로디
  6마디 C   엔딩 카드      : 화음이 길게 울리며 마무리

실행: python3 music.py  →  out/music.wav
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 72
B = 60 / BPM
DUR = 20.0
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
PROG = [([57, 60, 64, 67], 45), ([53, 57, 60, 64], 41), ([48, 52, 55, 60], 48),
        ([55, 59, 62, 65], 43), ([53, 57, 60, 64], 41), ([48, 52, 55, 60], 36)]
SW = 0.05   # 로파이 스윙 (뒷박을 살짝 늦게)
K, S, SH = kick(), snap(), shaker()
MEL = {4: [(0, 76), (1, 79), (2, 81), (3, 79)], 5: [(0, 76), (1.5, 72)]}

for bar, (ch, root) in enumerate(PROG):
    t0 = bar * BAR
    last = bar == 5
    # 피아노 코드 (1박 + 2박 뒷박)
    for i, m in enumerate(ch):
        add(epiano(m, BAR * (1.2 if last else 0.45)), t0 + i * 0.012, 0.16, -0.2 + i * 0.13)
        if not last:
            add(epiano(m, B * 0.6), t0 + 1.5 * B + SW + i * 0.01, 0.1, -0.2 + i * 0.13)
    # 높은 음 아르페지오 (8분음표, 스윙)
    if not last:
        for k in range(8):
            m = ch[[0, 2, 1, 3, 2, 1, 3, 2][k]] + 12
            add(epiano(m, B * 0.4), t0 + k * B / 2 + (SW if k % 2 else 0), 0.06 if k % 2 else 0.08, 0.35 if k % 2 else -0.35)
    add(pad([m - 12 for m in ch], BAR + (1.5 if last else 0), 0.02, 0.5), t0, 0.22)
    add(bass(root - (0 if root < 40 else 12), BAR * (1.3 if last else 0.9)), t0, 0.5)
    # 리듬 (2마디부터, 마지막 마디는 첫 박만)
    if bar >= 1 and not last:
        for b in range(4):
            tb = t0 + b * B
            if b in (0, 2):
                add(K, tb, 0.5)
            if b in (1, 3):
                add(S, tb, 0.35, -0.1)
            add(SH, tb + B / 2 + SW, 0.6, 0.4)
    if last:
        add(K, t0, 0.55)
    for off, m in MEL.get(bar, []):
        add(musicbox(m + 12, 2.0), t0 + off * B, 0.16, 0.2)
        add(bell(m, 2.0), t0 + off * B, 0.08, -0.2)

# 장면 전환 효과
for bar in range(1, 6):
    add(swell(0.5), bar * BAR - 0.5, 0.05)
add(swell(BAR * 0.9), 3 * BAR + BAR * 0.1, 0.1)
add(boom(), 4 * BAR, 0.4)
for i, m in enumerate([84, 88, 91, 96]):
    add(musicbox(m, 2.0), 5 * BAR + 0.4 + i * 0.09, 0.08, -0.3 + i * 0.2)

# 레코드 잡음 (쉬익 + 톡톡)
hiss = onepole(rng.standard_normal(N), 0.3) * 0.012
clicks = np.zeros(N)
idx = rng.integers(0, N, 90)
clicks[idx] = rng.uniform(0.05, 0.18, 90) * rng.choice([-1, 1], 90)
mix[:, 0] += hiss + clicks
mix[:, 1] += hiss + clicks

# 마스터
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.3) / np.tanh(1.3) * 0.9
tt = np.arange(N) / SR
mix *= (np.clip((DUR - tt) / 1.2, 0, 1) ** 0.7 * np.clip(tt / 0.2, 0, 1))[:, None]

os.makedirs("out", exist_ok=True)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("out/music.wav 생성 완료 (정확히 20초, 72 BPM, 6마디)")
