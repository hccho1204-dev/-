"""
경쾌한 120 BPM 일렉트로 팝 비트를 직접 합성합니다 (외부 음원 X → 저작권 100% 자유, 상업적 사용 가능).
20초 = 40비트 = 10마디. 영상 모션은 이 비트(0.5초 간격)에 정확히 맞춰져 있습니다.

실행: python3 music.py  →  out/music.wav
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM          # 0.5초
DUR = 22.0  # 20초 비트 + 2초 엔딩 여운
N = int(SR * DUR)
rng = np.random.default_rng(7)

mix = np.zeros((N, 2))


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l = gain * np.sqrt(0.5 * (1 - pan))
    r = gain * np.sqrt(0.5 * (1 + pan))
    mix[i:i + len(sig), 0] += sig * l
    mix[i:i + len(sig), 1] += sig * r


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = int(a * SR)
    if na > 0:
        e[:na] *= np.linspace(0, 1, na)
    return e


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.04)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.18)
    s += 0.4 * rng.standard_normal(n) * np.exp(-t / 0.004)
    return np.tanh(s * 1.8)


def clap():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # 간단한 하이패스
    noise = np.diff(noise, prepend=0)
    e = np.exp(-t / 0.09)
    for off in (0.0, 0.012, 0.024):
        k = int(off * SR)
        e[k:] += 0.6 * np.exp(-t[: n - k] / 0.01)
    return noise * e * 0.5


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    s = np.diff(rng.standard_normal(n), prepend=0)
    s = np.diff(s, prepend=0)
    return s * np.exp(-t / (0.08 if open_ else 0.015)) * 0.25


def saw(freq, dur, detune=0.006):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for d in (-detune, 0, detune):
        s += 2 * ((t * freq * (1 + d)) % 1) - 1
    return s / 3


def lowpass(x, alpha):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note(m)
    s = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t)
    return lowpass(s * env(n, 0.003, 0.18), 0.12)


def stab(chord, dur):
    s = sum(saw(note(m), dur) for m in chord) / len(chord)
    n = len(s)
    return lowpass(s * env(n, 0.004, 0.12), 0.25)


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = rng.standard_normal(n)
    out = np.zeros(n)
    acc = 0.0
    a = np.linspace(0.02, 0.6, n)
    for i in range(n):
        acc += a[i] * (s[i] - acc)
        out[i] = acc
    return out * (t / dur) ** 2 * 0.8


def impact():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    f = 30 + 80 * np.exp(-t / 0.08)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.5)
    s += 0.3 * lowpass(rng.standard_normal(n), 0.3) * np.exp(-t / 0.3)
    return np.tanh(s * 2)


# 코드 진행: Am - F - C - G (마디마다)
prog = [
    ([57, 60, 64], 45),
    ([53, 57, 60], 41),
    ([48, 52, 55], 36),
    ([55, 59, 62], 43),
]

K, C, H, HO = kick(), clap(), hat(), hat(True)

for beat in range(40):
    t = beat * BEAT
    bar = beat // 4
    pos = beat % 4
    chord, root = prog[bar % 4]

    build = 28 <= beat < 32       # 14~16초: 빌드업
    outro = beat >= 38            # 19초~: 엔딩

    if outro:
        continue

    # 킥: 4-on-the-floor (빌드업 마지막엔 16분 롤)
    if build and beat >= 30:
        for k in range(4):
            add(K, t + k * BEAT / 4, 0.55 + 0.1 * k)
    elif beat >= 2 or pos == 0:
        add(K, t, 0.9)

    # 클랩: 2, 4박
    if pos in (1, 3) and beat >= 4:
        add(C, t, 0.55, 0.1)

    # 하이햇 8분/16분
    if beat >= 4:
        add(H, t + BEAT / 2, 0.6, -0.3)
        if beat >= 16:
            add(H, t + BEAT / 4, 0.3, 0.3)
            add(H, t + 3 * BEAT / 4, 0.3, 0.3)
    if pos == 3 and beat >= 8:
        add(HO, t + BEAT / 2, 0.4, -0.2)

    # 베이스: 오프비트 펌핑
    if beat >= 4 and not build:
        add(bass(root, BEAT / 2 * 0.9), t + BEAT / 2, 0.55)
        add(bass(root + 12, BEAT / 4 * 0.9), t + 3 * BEAT / 4, 0.3)

    # 신스 스탭: 싱코페이션 리듬
    if beat >= 8 and not build:
        add(stab(chord, 0.2), t, 0.35, -0.4)
        if pos in (1, 3):
            add(stab([m + 12 for m in chord], 0.15), t + 0.75 * BEAT, 0.25, 0.4)

# 빌드업 라이저 (14~16초) + 드롭 임팩트 (16초) + 엔딩 임팩트 (19초)
add(riser(2.0), 14.0, 0.6)
add(impact(), 0.0, 0.7)
add(impact(), 16.0, 0.9)
add(impact(), 19.0, 1.0)
add(stab([57, 60, 64, 69], 1.0) * np.linspace(1, 0, int(1.0 * SR)), 19.0, 0.5)

# 엔딩 여운 (19~22초): 부드러운 패드 + 인스타 아이디 등장(19.5초) '팅' 효과음
pad_len = 2.9
pad = sum(saw(note(m), pad_len, 0.004) for m in [57, 64, 69, 71, 76]) / 5
pad = lowpass(pad, 0.06)
pn = len(pad)
pe = np.minimum(np.linspace(0, 1, pn) * 6, 1) * np.linspace(1, 0, pn) ** 1.5
add(pad * pe, 19.05, 0.55)
pl = int(0.6 * SR)
tp = np.arange(pl) / SR
ping = (np.sin(2 * np.pi * note(88) * tp) + 0.5 * np.sin(2 * np.pi * note(95) * tp)) * np.exp(-tp / 0.15)
add(ping, 19.5, 0.35, 0.2)

# 사이드체인 느낌(킥에 맞춰 살짝 눌러주기) + 마스터
t = np.arange(N) / SR
duck = 1 - 0.35 * np.exp(-((t % BEAT) / 0.08)) * (t < 19)
mix *= duck[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.4) / np.tanh(1.4) * 0.92
fade = np.ones(N)
fade[-int(0.3 * SR):] = np.linspace(1, 0, int(0.3 * SR))
mix *= fade[:, None]

os.makedirs("out", exist_ok=True)
pcm = (mix * 32767).astype(np.int16)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("out/music.wav 생성 완료 (22초, 120 BPM)")
