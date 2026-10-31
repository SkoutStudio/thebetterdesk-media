import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

base = "/home/claude"
k = Kokoro(f"{base}/tts/kokoro.onnx", f"{base}/tts/voices.bin")
scripts = json.load(open(f"{base}/scripts.json"))
GAP = 0.28
os.makedirs(f"{base}/out", exist_ok=True)
ids=[int(a) for a in sys.argv[1:]]
for s in [x for x in scripts if not ids or x["id"] in ids]:
    sid = s["id"]
    chunks, timeline, t = [], [], 0.6  # small lead-in after cover
    sr = 24000
    chunks.append(np.zeros(int(0.6 * sr), dtype=np.float32))
    for line in s["lines"]:
        a, sr = k.create(line, voice="am_michael", speed=1.08, lang="en-us")
        a = a.astype(np.float32)
        # trim silence
        idx = np.where(np.abs(a) > 0.01)[0]
        if len(idx):
            a = a[max(0, idx[0] - 600): idx[-1] + 1200]
        d = len(a) / sr
        timeline.append({"text": line, "start": t, "end": t + d})
        chunks.append(a)
        chunks.append(np.zeros(int(GAP * sr), dtype=np.float32))
        t += d + GAP
    chunks.append(np.zeros(int(0.8 * sr), dtype=np.float32))
    audio = np.concatenate(chunks)
    sf.write(f"{base}/out/v{sid}_voice.wav", audio, sr)
    json.dump({"duration": len(audio) / sr, "timeline": timeline}, open(f"{base}/out/v{sid}_timeline.json", "w"), indent=1)
    print(sid, round(len(audio) / sr, 1))
