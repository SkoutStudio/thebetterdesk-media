# Production tools (@thebetterdesk)

Recreate the workspace: copy these files to /home/claude, `mkdir -p /home/claude/out && cp thebetterdesk_logo.png /home/claude/out/`.
Voice: `pip install --break-system-packages kokoro-onnx soundfile` and download
kokoro-v1.0.onnx + voices-v1.0.bin from github.com/thewh1teagle/kokoro-onnx releases (model-files-v1.0) into /home/claude/tts/.

- Videos: add entries to scripts.json (id, label, cover, accent, lines, caption) → `python3 make_audio.py <ids>` → `python3 render.py <ids>` → out/FocusTip_<id>.mp4 (voice am_michael, cover = first frame + embedded thumbnail).
- Carousels: add to carousels.json → `python3 carousel.py` → out/<id>/NN.jpg (1080x1920).
- Upload media to videos/ and slides/ in this repo; schedule in Metricool (brand 7784568, TikTok) using raw.githubusercontent.com URLs; tiktokData.title required, isAigc true.
- Posting slots: alternate 15:00 / 21:00 Europe/Athens, one post per day.
