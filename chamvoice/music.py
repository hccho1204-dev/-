"""
참보이스앙상블 축하 영상 음악: 90 BPM 감성 피아노 + 오르골, 정확히 20초 (= 30비트).
코드로 직접 합성 → 저작권 걱정 없음. (인트로 오르골 선율도 직접 작곡)

구간 (비트 번호 b, 1비트 = 0.667초)
  b0~6    인트로     : 오르골 찬가풍 선율 + 합창 '아—' 패드 (촛불이 켜짐)
  b6~19   전개       : 일렉 피아노 아르페지오 + 베이스 + 패드, b15부터 셰이커
  b19~24  클라이맥스 : 부드러운 킥·스냅 + 현악 + 벨 멜로디 (웃음 장면)
  b24~30  엔딩       : F - G - C 해결, 마지막 C 화음이 길게 울림

실행: python3 music.py  →  out/music.wav
"""
import os
import wave
import numpy as np

SR = 44100
BPM = 90
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


# ---------- 인트로: 오르골 찬가풍 선율 (C E G | A G E | D) ----------
s0 = 0.3
t = s0
for m, d in [(72, 0.75), (76, 0.25), (79, 1), (81, 1), (79, 1), (74, 2)]:
    add(musicbox(m + 12, 2.2), t, 0.5, 0.15)
    add(musicbox(m, 2.2), t, 0.25, -0.15)
    t += d * B
add(pad([48, 55, 60, 64], 2 * B, 0.02, 0.8), s0 + B, 0.35)
add(pad([43, 50, 55, 59], 1.6 * B, 0.02, 0.5), s0 + 4 * B, 0.35)

# ---------- 코드 진행 (시작 비트, 길이, 화음, 베이스) ----------
C, G_B, Am, Em, F, G, Dm = [60, 64, 67], [59, 62, 67], [57, 60, 64], [55, 59, 64], [57, 60, 65], [59, 62, 67], [57, 62, 65]
PROG = [(6, 2, C, 48), (8, 2, G_B, 47), (10, 2, Am, 45), (12, 2, Em, 40), (14, 2, F, 41), (16, 3, G, 43),
        (19, 2, C, 48), (21, 2, Am, 45), (23, 1, G, 43), (24, 2, F, 41), (26, 2, G, 43), (28, 2, C, 36)]
ARP = [0, 1, 2, 1, 2, 3, 2, 1]
for b0, ln, ch, root in PROG:
    final = b0 == 28
    climax = 19 <= b0 < 28
    add(pad([m - 12 for m in ch] + [ch[0]], ln * B + (1.5 if final else 0), 0.025 if not climax else 0.04, 0.4), b0 * B, 0.3 if not climax else 0.38)
    add(bass(root, ln * B * 0.95 + (1.5 if final else 0)), b0 * B, 0.55)
    if final:
        for i, m in enumerate([60, 64, 67, 72, 76]):
            add(epiano(m, 2.5), 28 * B + i * 0.06, 0.22, -0.3 + i * 0.15)
        continue
    notes = ch + [ch[0] + 12]
    for k in range(ln * 2):
        m = notes[ARP[k % 8]] + 12
        add(epiano(m, B * 0.6), b0 * B + k * B / 2, 0.16 if k % 2 else 0.2, 0.3 if k % 2 else -0.3)
    if climax:   # 현악 느낌의 높은 패드
        add(pad([m + 12 for m in ch], ln * B, 0.06, 0.3), b0 * B, 0.18)

# ---------- 합창 '아—' (모음 느낌의 배음 + 비브라토) ----------
def choir(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(a * np.sin(k * ph) for k, a in [(1, 1), (2, 0.5), (3, 0.35), (4, 0.12), (5, 0.08)])
    e = np.minimum(1, t / 0.5) * np.minimum(1, (dur - t) / 0.6).clip(0)
    return s * e
for b0, ln, ch, root in PROG:
    if b0 >= 19:
        for i, mm in enumerate(ch):
            add(choir(mm, ln * B + (1.5 if b0 == 28 else 0.2)), b0 * B, 0.07, -0.4 + i * 0.4)
for mm in (60, 64, 67):
    add(choir(mm, 3.0), 1.0, 0.05, (mm - 64) * 0.1)

# ---------- 리듬 ----------
K, S, SH = kick(), snap(), shaker()
for b in range(15, 28):
    for k in range(2):
        add(SH, b * B + k * B / 2, 0.8 if k else 0.5, 0.4)
for b in range(19, 28):
    add(K, b * B, 0.55)
    if (b - 19) % 2 == 1:
        add(S, b * B, 0.45, -0.1)
add(K, 28 * B, 0.6)

# ---------- 벨 멜로디 (클라이맥스 ~ 엔딩) ----------
MEL = [(19, 79), (20, 84), (21, 83), (21.5, 81), (22, 76), (23, 79), (24, 77), (25, 81), (26, 83), (27, 86), (28, 84)]
for b, m in MEL:
    add(bell(m, 2.5 if b == 28 else 1.6), b * B, 0.22, 0.2)
    add(musicbox(m + 12, 1.2), b * B, 0.08, -0.25)

# ---------- 효과음 ----------
add(swell(3 * B), 16 * B, 0.12)          # 클라이맥스 전 부드러운 상승
add(boom(), 19 * B, 0.45)                 # 웃음 장면 진입
for i, m in enumerate([84, 88, 91, 96, 100]):   # 마지막 반짝
    add(musicbox(m, 2.0), 28 * B + 0.25 + i * 0.07, 0.12, -0.4 + i * 0.2)

# ---------- 마스터 ----------
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.3) / np.tanh(1.3) * 0.9
tt = np.arange(N) / SR
fade = np.clip((DUR - tt) / 1.2, 0, 1) ** 0.7
mix *= fade[:, None]

os.makedirs("out", exist_ok=True)
with wave.open("out/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("out/music.wav 생성 완료 (정확히 20초, 90 BPM, 30비트)")
