"""
쇼릴용 음악: 144 BPM 퓨처하우스 스타일, 정확히 20초 (= 48비트 = 12마디).
코드로 직접 합성 → 저작권 걱정 없음, 상업적 사용 가능.

구간 (비트 번호 b, 1비트 = 0.4167초)
  b0~5    인트로     : 임팩트 + 플럭 아르페지오
  b6~25   그루브     : 킥·클랩·하이햇·베이스
  b26~35  풀 밴드    : 슈퍼소우 코드, b32~35 스네어 롤 빌드업
  b36~41  드롭       : 최고 에너지 (몽타주 구간)
  b42~47  엔딩       : 매 비트 '팡' 스탭 → 화면 요소가 하나씩 튀어나옴

실행: python3 music.py  →  out/music.wav
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 144
B = 60 / BPM
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
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


# F#m - D - A - E  (마디마다 교체)
PROG = [([54, 57, 61, 66], 42), ([50, 54, 57, 62], 38), ([57, 61, 64, 69], 45), ([52, 56, 59, 64], 40)]
ARP = [0, 1, 2, 3, 2, 1, 3, 2]
K, C, S, H, HO = kick(), clap(), snare(), hat(), hat(0.06)

for b in range(48):
    t = b * B
    bar, pos = b // 4, b % 4
    ch, root = PROG[bar % 4]
    intro = b < 6
    build = 32 <= b < 36
    drop = 36 <= b < 42
    ending = b >= 42

    # 플럭 아르페지오 (16분음표)
    if b < 42:
        for k in range(2 if intro else 4):
            m = ch[ARP[(b * 4 + k) % 8]] + 12
            add(pluck(m), t + k * B / (2 if intro else 4), 0.22 if not drop else 0.16, 0.3 if k % 2 else -0.3)

    if intro:
        continue

    if ending:
        # 엔딩: 매 비트 코드 스탭 + 팝 사운드 → 화면 요소가 튀어나오는 타이밍
        if b < 47:
            add(K, t, 0.8)
            add(chord([m + 12 for m in ch], B * 0.9, 0.35), t, 0.45)
            add(pop(84 + (b - 42) * 2), t, 0.25, (b % 2) * 0.6 - 0.3)
        continue

    # 킥
    if build and b >= 34:
        for k in range(4):
            add(K, t + k * B / 4, 0.5 + 0.1 * k)
    else:
        add(K, t, 0.95)
    # 클랩 / 스네어 롤
    if build:
        div = 2 if b < 34 else 4
        for k in range(div):
            add(S, t + k * B / div, 0.25 + 0.1 * (b - 32) + 0.03 * k)
    elif pos in (1, 3):
        add(C, t, 0.6, 0.1)
    # 하이햇
    add(H, t + B / 2, 0.7, -0.3)
    if b >= 16:
        add(H, t + B / 4, 0.3, 0.3)
        add(H, t + 3 * B / 4, 0.3, 0.3)
    if pos == 3:
        add(HO, t + B / 2, 0.5, -0.2)
    # 베이스 (오프비트)
    if b >= 16 and not build:
        add(bass(root - 12, B * 0.45), t + B / 2, 0.6)
    # 슈퍼소우 코드
    if b >= 26 and not build:
        add(chord(ch, B * 0.8, 0.3 if drop else 0.15), t, 0.35 if drop else 0.22, 0)
        if drop:
            add(chord([m + 12 for m in ch], B * 0.4, 0.4), t + B / 2, 0.2)

# 효과음
add(impact(), 0.0, 0.8)                        # 오프닝
add(whoosh(B * 2), 6 * B - B * 2, 0.35)         # 섹션 전환 휙
add(whoosh(B * 2), 16 * B - B * 2, 0.35)
add(whoosh(B * 2), 26 * B - B * 2, 0.35)
add(whoosh(B * 4), 32 * B, 0.6)                 # 빌드업 라이저
add(impact(), 36 * B, 1.0)                      # 드롭
add(whoosh(B), 41 * B, 0.4)
add(impact(1.2), 42 * B, 0.8)                   # 엔딩 시작
add(impact(2.0), 47 * B, 0.9)                   # 마지막 한 방
add(chord([54, 61, 66, 69, 73], 1.4, 0.3), 47 * B, 0.5)

# 사이드체인 + 마스터
t = np.arange(N) / SR
duck = 1 - 0.4 * np.exp(-((t % B) / 0.07)) * ((t > 6 * B) & (t < 42 * B))
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
print("out/music.wav 생성 완료 (정확히 20초, 144 BPM, 48비트)")
