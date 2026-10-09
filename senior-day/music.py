"""
70대 어르신의 모벨릭스 하루 (에너지 버전) — 따뜻하고 신나는 132 BPM 팝, 정확히 20초 (44비트, 1비트 = 0.4545초)
코드로 직접 합성 → 저작권 걱정 없음, 상업적 사용 가능.

  b0~3   인트로   : 우쿨렐레 스트럼 + 붕 효과음 + 박수 빌드업
  b4~35  메인     : 4비트 킥 + 박수 + 탬버린 16분 + 통통 베이스 + 마림바 멜로디 + 우쿨렐레
  b36~41 엔딩     : 매 비트 팡! + 종소리 계단
  b42    마지막 한 방
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 132
B = 60 / BPM
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(132)
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



def strum(ms, dur=0.35, down=True):
    # 우쿨렐레 느낌: 짧은 플럭을 15ms 간격으로 긁기
    out = np.zeros(int((dur + 0.08) * SR))
    order = ms if down else ms[::-1]
    for i, m in enumerate(order):
        p = pluck(m, dur)
        k = int(i * 0.015 * SR)
        out[k:k + len(p)] += p[:len(out) - k]
    return out / len(ms)


def shaker():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    s = np.diff(rng.standard_normal(n), prepend=0)
    return s * np.exp(-t / 0.012) * np.minimum(1, t / 0.004 + 1e-9) * 0.25


# C - Am - F - G (4비트씩), 따뜻한 메이저
PROG = [([60, 64, 67, 72], 36), ([57, 60, 64, 69], 33), ([53, 57, 60, 65], 41), ([55, 59, 62, 67], 43)]
MEL = [76, 74, 72, 74, 76, 79, 76, 72, 74, 72, 69, 72, 74, 76, 79, 81]
K, C, H, SH = kick(), clap(), hat(), shaker()

for b in range(44):
    t = b * B
    ch, root = PROG[(b // 4) % 4]
    pos = b % 4
    # 우쿨렐레 스트럼 (다운-업)
    if b < 42:
        add(strum([m + 12 for m in ch[:3]] + [ch[0] + 24], 0.3, True), t, 0.32, -0.2)
        add(strum([m + 12 for m in ch[:3]] + [ch[0] + 24], 0.2, False), t + B * 0.5, 0.2, -0.2)
    if b < 4:
        if b in (1, 3):
            add(vroom(), t, 0.45)
        for k in range(b + 1):
            add(C, t + k * B / (b + 1), 0.25 + 0.08 * b)
        continue
    if b >= 36:
        if b < 42:
            add(K, t, 0.95)
            add(C, t, 0.45)
            add(pop(84 + (b - 36) * 2), t, 0.3, (b % 2) * 0.6 - 0.3)
            add(bell(84 + (b - 36) * 2), t, 0.3)
        continue
    # 4비트 킥 + 2,4박 박수
    add(K, t, 0.9)
    if pos in (1, 3):
        add(C, t, 0.6, 0.1)
    # 탬버린 16분 + 오프비트 하이햇
    for k in range(4):
        add(SH, t + k * B / 4, 0.5 if k % 2 else 0.3, 0.35)
    add(H, t + B / 2, 0.4, -0.3)
    # 통통 베이스 (8분 옥타브)
    add(bass(root, B * 0.4), t, 0.45)
    add(bass(root + 12, B * 0.3), t + B / 2, 0.35)
    # 마림바 멜로디
    for k in range(2):
        add(marimba(MEL[(b * 2 + k) % 16]), t + k * B / 2, 0.33, 0.25 if k else -0.05)
    # 장면 바뀔 때 종소리 + 붕
    if b % 6 == 4:
        add(bell(84), t, 0.35, 0.4)
        add(boing(), t + B * 0.5, 0.22, -0.3)

add(impact(1.0), 0.0, 0.45)
for sb in (4, 10, 16, 22, 28):
    add(whoosh(B * 1.5), sb * B - B * 1.3, 0.22)
add(whoosh(B * 2), 34 * B, 0.35)
add(impact(1.2), 36 * B, 0.6)
add(impact(1.6), 42 * B, 0.85)
add(chord([60, 64, 67, 72, 76], 1.0, 0.35), 42 * B, 0.45)
add(bell(96, 1.0), 42 * B, 0.35)

t = np.arange(N) / SR
duck = 1 - 0.32 * np.exp(-((t % B) / 0.06)) * ((t > 4 * B) & (t < 36 * B))
mix *= duck[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.45) / np.tanh(1.45) * 0.92
fade = np.ones(N)
fade[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
mix *= fade[:, None]
os.makedirs("out", exist_ok=True)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("out/music.wav 생성 완료 (정확히 20초, 132 BPM)")
