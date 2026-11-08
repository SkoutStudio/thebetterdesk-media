# Production tools (@thebetterdesk)

Recreate the workspace: copy these files to /home/claude, `mkdir -p /home/claude/out && cp thebetterdesk_logo.png /home/claude/out/`.
Voice: `pip install --break-system-packages kokoro-onnx soundfile` and download
kokoro-v1.0.onnx + voices-v1.0.bin from github.com/thewh1teagle/kokoro-onnx releases (model-files-v1.0) into /home/claude/tts/.

- Videos: add entries to scripts.json (id, label, cover, accent, lines, caption) → `python3 make_audio.py <ids>` → `python3 render.py <ids>` → out/FocusTip_<id>.mp4 (voice am_michael, cover = first frame + embedded thumbnail).
- Carousels: add to carousels.json → `python3 carousel.py` → out/<id>/NN.jpg (1080x1920).
- Upload media to videos/ and slides/ in this repo; schedule in Metricool (brand 7784568, TikTok) using raw.githubusercontent.com URLs; tiktokData.title required, isAigc true.
- Posting slots: alternate 15:00 / 21:00 Europe/Athens, one post per day.

## Video styles (render2.py) — use a MIX every week
Same workspace as above. Add `"style"` to a scripts.json entry, then `python3 make_audio2.py <ids>` → `python3 render2.py preview <id> <t1> <t2>…` (contact sheet in out/preview_<id>.jpg, look at it) → `python3 render2.py <ids>` → out/FocusTip_<id>.mp4.
`lines` items can be strings or dicts: `{"t": text, "who": "me"|"brain"|"narrator"}`, `{"pause": 10, "countdown": true}` (silence + ticks).
- `test`  — find-the-odd-one grid + 10 s countdown + red circle reveal. Needs `"grid": {"base","odd","rows","cols","pos":[r,c]}` and lines with one pause and one `{"t":…, "reveal": true}`. Great for comments ("comment your time") and series ("part 2 is harder").
- `dialogue` — "Me vs my brain" chat bubbles, two voices (me = am_michael, brain = af_bella). Relatable → shares.
- `notes` — typed note on paper; needs `"heading"`. First line = title, last line = CTA. Saves.
- `quiz` — true/false: `{"t": question, "q": short text on card}`, `{"pause":3,"countdown":true}`, `{"t": answer, "reveal": "TRUE"|"FALSE"}`. Facts must be accurate. Comments ("your score /3").
- `countdown` — ranked list #5→#1: items `{"t":…, "rank": n, "rule": short label}`. Good for soft-sell of The Focus Blueprint methods.
- no style → classic captions video (render.py).
Draft examples of every style: tools/draft_posts.json.
