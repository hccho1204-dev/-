"""목소리 대조 (N7): 음성 인식으로 문장별 발음을 대본과 비교한다.

사용법: python3 check_voice.py <voice.wav> <timing.json> <ASR모델폴더>
  ASR 모델: sherpa-onnx-streaming-zipformer-korean-2024-06-16
  (github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/ 에서 내려받기)
숫자·영문이 든 문장은 읽는 방식이 달라 비교에서 뺀다.
평균 일치율 0.8 미만이면 종료코드 1 (= 목소리 교체)
"""
import difflib, json, re, sys
import numpy as np, soundfile as sf, sherpa_onnx

if len(sys.argv) != 4:
    sys.exit(__doc__)
wav, timing, M = sys.argv[1:]
rec = sherpa_onnx.OnlineRecognizer.from_transducer(
    tokens=f"{M}/tokens.txt", encoder=f"{M}/encoder-epoch-99-avg-1.int8.onnx",
    decoder=f"{M}/decoder-epoch-99-avg-1.onnx", joiner=f"{M}/joiner-epoch-99-avg-1.int8.onnx",
    num_threads=2, sample_rate=16000)
x, sr = sf.read(wav, dtype="float32")
if x.ndim > 1: x = x.mean(axis=1)
idx = np.round(np.arange(0, len(x), sr / 16000)).astype(int); y = x[idx[idx < len(x)]]
hangul = lambda s: re.sub(r"[^가-힣]", "", s)
res = []
for sc in json.load(open(timing, encoding="utf-8"))["scenes"]:
    for g in sc["segs"]:
        if re.search(r"[0-9A-Za-z]", g["text"]):
            continue
        st = rec.create_stream()
        st.accept_waveform(16000, y[int(g["start"] * 16000): int(g["end"] * 16000)])
        st.accept_waveform(16000, np.zeros(8000, np.float32)); st.input_finished()
        while rec.is_ready(st): rec.decode_stream(st)
        hyp = rec.get_result(st)
        res.append((difflib.SequenceMatcher(None, hangul(g["text"]), hangul(hyp)).ratio(), g["text"], hyp))
avg = sum(r for r, *_ in res) / len(res)
print(f"비교 문장 {len(res)}개 · 평균 일치율 {avg:.2f} · 0.6 미만 {sum(r < .6 for r, *_ in res)}개")
for r, t, h in sorted(res)[:8]:
    print(f"  {r:.2f} | 대본: {t} | 들린 말: {h}")
print("✅ 통과" if avg >= .8 else "❌ 목소리 교체 필요")
sys.exit(0 if avg >= .8 else 1)
