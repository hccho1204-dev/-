"""대본(scenes.json) → script.txt, voice.wav, timing.json
문장(세그먼트)마다 따로 음성을 만들어 이어 붙이므로 정확한 시간표가 나온다."""
import json, re, sys
import numpy as np, soundfile as sf, sherpa_onnx

MODEL = sys.argv[1]  # vits-mimic3-ko_KO-kss_low 폴더
SPEED = 1.08
GAP, SCENE_GAP = 0.18, 0.35

SAY = [  # 화면용 표기 → 읽기용 발음 (숫자·영문)
    ("5.5", "오 점 오"), ("279쌍", "이백칠십구 쌍"), ("1.7배", "일 점 칠 배"),
    ("17,000개", "만 칠천 개"), ("15초", "십오 초"), ("100개", "백 개"),
    ("1,938개", "천구백삼십팔 개"), ("1,267개", "천이백육십칠 개"),
    ("11가지", "열한 가지"), ("11개", "열한 개"), ("1.2초", "일 점 이 초"),
    ("3D", "쓰리디"), ("10장", "열 장"), ("9개 중 9개", "아홉 개 중 아홉 개"),
    ("5개", "다섯 개"), ("24장", "스물네 장"), ("1분", "일 분"), ("0부터", "영부터"),
    ("0원", "영 원"), ("60개", "육십 개"), ("30%", "삼십 퍼센트"), ("1초", "일 초"),
    ("PPT", "피피티"), ("UI", "유아이"), ("AI", "에이아이"), ("X,", "엑스,"),
]

def say(t):
    for a, b in SAY:
        t = t.replace(a, b)
    t = re.sub(r"[\"'“”‘’]", "", t)
    left = re.findall(r"[0-9A-Za-z]+", t)
    if left:
        print("⚠️ 읽기 변환 안 된 문자:", left, "|", t)
    return t

cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=f"{MODEL}/ko_KO-kss_low.onnx", lexicon="",
        tokens=f"{MODEL}/tokens.txt", data_dir=f"{MODEL}/espeak-ng-data"), num_threads=4))
tts = sherpa_onnx.OfflineTts(cfg)
SR = tts.sample_rate

scenes = json.load(open("scenes.json", encoding="utf-8"))
audio, t, timing, lines = [], 0.4, [], []
audio.append(np.zeros(int(0.4 * SR), np.float32))
for i, sc in enumerate(scenes):
    s0, segs = t, []
    for txt in sc["segs"]:
        a = tts.generate(say(txt), sid=0, speed=SPEED)
        x = np.asarray(a.samples, np.float32)
        # 앞뒤 무음 다듬기
        nz = np.where(np.abs(x) > 0.01)[0]
        if len(nz): x = x[max(0, nz[0] - 400): nz[-1] + 800]
        segs.append({"text": txt, "start": round(t, 3), "end": round(t + len(x) / SR, 3)})
        audio.append(x); t += len(x) / SR
        audio.append(np.zeros(int(GAP * SR), np.float32)); t += GAP
        lines.append(txt)
    hold = sc.get("hold", SCENE_GAP)
    audio.append(np.zeros(int(hold * SR), np.float32)); t += hold
    timing.append({"scene": i, "tpl": sc["tpl"], "start": round(s0, 3), "end": round(t, 3), "segs": segs})
    print(f"장면 {i:2d} {sc['tpl']:9s} {s0:7.2f}~{t:7.2f}")

sf.write("voice_raw.wav", np.concatenate(audio), SR)
json.dump({"duration": round(t, 3), "scenes": timing}, open("timing.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open("script.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("총 길이", round(t, 1), "초")
