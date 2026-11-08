"""Voice + timeline for styled videos (render2.py).
Lines can be plain strings or dicts:
  {"t": text, "who": "me"|"brain"|"narrator", ...extra scene keys}
  {"pause": seconds, "countdown": true}   -> silence with ticking
Timeline keeps every extra key so render2.py can drive scenes."""
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

base = "/home/claude"
k = Kokoro(f"{base}/tts/kokoro.onnx", f"{base}/tts/voices.bin")
VOICES = {"me": ("am_michael", 1.08), "brain": ("af_bella", 1.12), "narrator": ("am_michael", 1.05), None: ("am_michael", 1.08)}
GAP, SR = 0.28, 24000

def tick(n_sec):
    out = np.zeros(int(n_sec * SR), dtype=np.float32)
    t = np.arange(int(0.05 * SR)) / SR
    click = (0.35 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90)).astype(np.float32)
    for s in range(int(n_sec)):
        i = int(s * SR)
        out[i:i + len(click)] += click
    return out

def build(s):
    chunks, timeline, t = [np.zeros(int(0.6 * SR), dtype=np.float32)], [], 0.6
    for raw in s["lines"]:
        item = {"t": raw} if isinstance(raw, str) else dict(raw)
        if "pause" in item:
            a = tick(item["pause"]) if item.get("countdown") else np.zeros(int(item["pause"] * SR), dtype=np.float32)
            item.update({"text": "", "start": t, "end": t + item["pause"]})
            timeline.append(item); chunks.append(a); t += item["pause"]
            continue
        voice, speed = VOICES[item.get("who")]
        a, sr = k.create(item["t"], voice=voice, speed=speed, lang="en-us")
        a = a.astype(np.float32)
        idx = np.where(np.abs(a) > 0.01)[0]
        if len(idx): a = a[max(0, idx[0] - 600): idx[-1] + 1200]
        d = len(a) / SR
        item.update({"text": item.pop("t"), "start": t, "end": t + d})
        timeline.append(item)
        chunks += [a, np.zeros(int(GAP * SR), dtype=np.float32)]
        t += d + GAP
    chunks.append(np.zeros(int(0.8 * SR), dtype=np.float32))
    audio = np.concatenate(chunks)
    sf.write(f"{base}/out/v{s['id']}_voice.wav", audio, SR)
    json.dump({"duration": len(audio) / SR, "timeline": timeline}, open(f"{base}/out/v{s['id']}_timeline.json", "w"), indent=1)
    print(s["id"], round(len(audio) / SR, 1), "s")

if __name__ == "__main__":
    os.makedirs(f"{base}/out", exist_ok=True)
    ids = [int(a) for a in sys.argv[1:]]
    for s in json.load(open(f"{base}/scripts.json")):
        if s["id"] in ids: build(s)
