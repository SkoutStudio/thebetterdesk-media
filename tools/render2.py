"""Styled video templates for @thebetterdesk.
Styles: test (find-the-odd-one grid + countdown), dialogue (me vs my brain chat),
notes (typed note on paper), quiz (true/false + countdown), countdown (ranked list).
Usage: python3 make_audio2.py <ids> && python3 render2.py <ids>"""
import json, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont
from render import make_bg, bg_frame, font, BOLD, SEMI, YELLOW, WHITE, W, H, wrap_words, chunks_for

base = "/home/claude"
FPS = 30
DARK = (14, 16, 30)
GREEN, RED, PINK = (80, 220, 140), (255, 80, 90), (190, 120, 255)
INTER_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

def header(img, label, light=False):
    d = ImageDraw.Draw(img)
    f = font(SEMI, 40); tw = d.textlength(label, font=f)
    x0 = (W - tw) / 2 - 34
    d.rounded_rectangle([x0, 230, x0 + tw + 68, 300], radius=35, fill=YELLOW)
    d.text((W / 2, 265), label, font=f, fill=(20, 20, 30), anchor="mm")
    d.text((W / 2, 345), "@thebetterdesk", font=font(SEMI, 32), fill=(60, 60, 70) if light else (220, 220, 235), anchor="mm")

def progress(img, t, dur, col=YELLOW):
    ImageDraw.Draw(img).rectangle([0, 0, int(W * t / dur), 12], fill=col)

def karaoke(img, ch, t, y_center=1640, size=64, maxw=920):
    cur = next((c for c in ch if c["start"] <= t < c["end"]), None)
    if cur is None:
        prev = [c for c in ch if c["end"] <= t and t - c["end"] < 0.3]
        cur = prev[-1] if prev else None
    if not cur: return
    d = ImageDraw.Draw(img); f = font(BOLD, size)
    lines = wrap_words(d, cur["words"], f, maxw); lh = int(size * 1.25)
    y = y_center - lh * len(lines) / 2; k = 0
    active = next((j for j, (a, b) in enumerate(cur["wt"]) if a <= t < b), -1)
    for ln in lines:
        lw = d.textlength(" ".join(ln), font=f); x = (W - lw) / 2
        for w in ln:
            d.text((x, y), w, font=f, fill=YELLOW if k == active else WHITE, stroke_width=6, stroke_fill=(10, 10, 20))
            x += d.textlength(w + " ", font=f); k += 1
        y += lh

def hook_text(img, lines, accent, y=None, size=112, light=False):
    d = ImageDraw.Draw(img); f = font(BOLD, size)
    while max(d.textlength(l, font=f) for l in lines) > 980: f = font(BOLD, f.size - 4)
    y = y if y is not None else 960 - len(lines) * f.size * 1.25 / 2
    for line in lines:
        lw = d.textlength(line, font=f); x = (W - lw) / 2
        for w in line.split():
            hit = w.strip("?.!,:").lower() == accent.lower()
            col = YELLOW if hit else ((20, 20, 30) if light else WHITE)
            kw = dict(stroke_width=0) if light else dict(stroke_width=8, stroke_fill=(10, 10, 20))
            if light and hit:
                tw = d.textlength(w, font=f); d.rectangle([x - 6, y + f.size * 0.25, x + tw + 6, y + f.size * 1.1], fill=YELLOW); col = (20, 20, 30)
            d.text((x, y), w, font=f, fill=col, **kw)
            x += d.textlength(w + " ", font=f)
        y += int(f.size * 1.25)
    return y

def active_item(tl, t):
    return next((it for it in tl if it["start"] <= t < it["end"]), None)

# ---------------- TEST: find the odd one ----------------
def scene_test(s, tl, ch, t, dur, bg, cover=False):
    img = bg_frame(bg, t).convert("RGBA")
    img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, 90)))
    header(img, s["label"])
    g = s["grid"]; rows, cols = g["rows"], g["cols"]
    d = ImageDraw.Draw(img)
    cell = min(900 / cols, 930 / rows); gx = (W - cell * cols) / 2; gy = 600
    f = font(INTER_B, int(cell * 0.72))
    d.rounded_rectangle([gx - 30, gy - 30, gx + cell * cols + 30, gy + cell * rows + 30], radius=36, fill=(250, 248, 240))
    for r in range(rows):
        for c in range(cols):
            ch_ = g["odd"] if [r, c] == g["pos"] else g["base"]
            d.text((gx + cell * (c + .5), gy + cell * (r + .5)), ch_, font=f, fill=(25, 25, 35), anchor="mm")
    pause = next(it for it in tl if "pause" in it)
    rev = next(it for it in tl if it.get("reveal"))
    if cover:
        from PIL import ImageFilter
        img = img.filter(ImageFilter.GaussianBlur(14))
        img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (10, 10, 25, 120)))
        header(img, s["label"]); hook_text(img, s["cover"], s["accent"], size=120)
        return img
    if pause["start"] <= t < pause["end"]:
        left = math.ceil(pause["end"] - t)
        pulse = 1 + 0.15 * (1 - ((pause["end"] - t) % 1))
        fs = int(150 * pulse)
        d.text((W / 2, 480), str(left), font=font(BOLD, fs), fill=YELLOW if left > 3 else RED, anchor="mm", stroke_width=8, stroke_fill=(10, 10, 20))
    if t >= rev["start"]:
        r, c = g["pos"]; cx, cy = gx + cell * (c + .5), gy + cell * (r + .5)
        k = ease((t - rev["start"]) / 0.35); rad = cell * (0.9 + 1.5 * (1 - k))
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=RED, width=12)
    if not (pause["start"] <= t < pause["end"]):
        karaoke(img, ch, t, y_center=1700, size=62)
    return img

# ---------------- DIALOGUE: me vs my brain ----------------
def scene_dialogue(s, tl, ch, t, dur, bg, cover=False):
    img = Image.new("RGBA", (W, H), (16, 18, 32)); header(img, s["label"])
    d = ImageDraw.Draw(img)
    if cover:
        hook_text(img, s["cover"], s["accent"], size=124)
        return img
    shown = [it for it in tl if it["start"] <= t and it.get("who")]
    f = font(SEMI, 50); bubbles = []
    for it in shown:
        who = it["who"]
        if who == "narrator":
            bubbles.append((who, [it["text"]], it)); continue
        bubbles.append((who, [" ".join(l) for l in wrap_words(d, it["text"].split(), f, 640)], it))
    # layout from bottom up
    y = 1560; placed = []
    for who, lines, it in reversed(bubbles):
        h = 70 + 64 * len(lines) + (50 if who != "narrator" else 0)
        y -= h + 30
        placed.append((y, h, who, lines, it))
        if y < 420: break
    for y0, h, who, lines, it in placed:
        if y0 < 400: continue
        k = ease((t - it["start"]) / 0.25)
        dy = int(40 * (1 - k))
        if who == "narrator":
            fn = font(BOLD, 58)
            for i, ln in enumerate(wrap_words(d, lines[0].split(), fn, 900)):
                d.text((W / 2, y0 + 40 + i * 72 + dy), " ".join(ln), font=fn, fill=YELLOW, anchor="mm")
            continue
        wmax = max(d.textlength(l, font=f) for l in lines) + 80
        if who == "brain":
            x0, col, tcol, name = 70, PINK, WHITE, "MY BRAIN"
        else:
            x0, col, tcol, name = W - 70 - max(wmax, 260), YELLOW, (20, 20, 30), "ME"
        x1 = x0 + max(wmax, 260)
        d.text((x0 + 10 if who == "brain" else x1 - 10, y0 + dy), name, font=font(BOLD, 34), fill=col, anchor="la" if who == "brain" else "ra")
        d.rounded_rectangle([x0, y0 + 50 + dy, x1, y0 + h + dy], radius=36, fill=col)
        for i, ln in enumerate(lines):
            d.text((x0 + 40, y0 + 85 + i * 64 + dy), ln, font=f, fill=tcol)
    progress(img, t, dur)
    return img

# ---------------- NOTES: typed note ----------------
PAPER, INK = (250, 247, 238), (28, 28, 36)
def scene_notes(s, tl, ch, t, dur, bg, cover=False):
    img = Image.new("RGBA", (W, H), PAPER); d = ImageDraw.Draw(img)
    for y in range(560, 1800, 86): d.line([(80, y), (W - 80, y)], fill=(225, 220, 205), width=2)
    d.line([(150, 420), (150, 1800)], fill=(240, 170, 170), width=3)
    header(img, s["label"], light=True)
    if cover:
        hook_text(img, s["cover"], s["accent"], size=118, light=True); return img
    fh = font(BOLD, 58)
    while d.textlength(s["heading"], font=fh) > 820: fh = font(BOLD, fh.size - 2)
    d.text((180, 430), s["heading"], font=fh, fill=INK)
    d.rectangle([180, 505, 180 + d.textlength(s["heading"], font=fh), 515], fill=YELLOW)
    f = font(SEMI, 48); y = 560 + 20; n = 0
    for it in tl[1:]:
        if it["start"] > t: break
        n += 1
        frac = min(1, (t - it["start"]) / max(0.1, (it["end"] - it["start"]) * 0.85))
        text = it["text"]; vis = text[: int(len(text) * frac)]
        lines = wrap_words(d, vis.split(), f, 800) if vis else []
        last = it is tl[-1]
        if not last: d.text((180, y + 14), f"{n}.", font=font(BOLD, 48), fill=(200, 150, 20))
        for ln in lines:
            d.text((250 if not last else 180, y + 14), " ".join(ln), font=f if not last else font(BOLD, 48), fill=INK if not last else (200, 120, 20))
            y += 86
        full = len(wrap_words(d, text.split(), f, 800))
        y += 86 * (full - len(lines)) + 20
        if frac < 1 and lines:
            cx = 250 + d.textlength(" ".join(lines[-1]), font=f) + 8
            if int(t * 2) % 2 == 0: d.rectangle([cx, y - 86 + 20 - 86 * (full - len(lines)) - 20, cx + 5, y - 86 + 70 - 86 * (full - len(lines)) - 20], fill=INK)
    progress(img, t, dur, col=(240, 180, 30))
    return img

# ---------------- QUIZ: true / false ----------------
def scene_quiz(s, tl, ch, t, dur, bg, cover=False):
    img = bg_frame(bg, t).convert("RGBA")
    img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, 80)))
    header(img, s["label"]); d = ImageDraw.Draw(img)
    if cover:
        hook_text(img, s["cover"], s["accent"], size=124); return img
    qs = [it for it in tl if it.get("q")]
    cur_q = [it for it in qs if it["start"] <= t]
    if cur_q:
        q = cur_q[-1]; qi = qs.index(q) + 1
        nxt = tl[tl.index(q) + 1:]
        pause = next(it for it in nxt if "pause" in it); rev = next(it for it in nxt if it.get("reveal"))
        d.text((W / 2, 470), f"QUESTION {qi}/{len(qs)}", font=font(BOLD, 46), fill=YELLOW, anchor="mm")
        d.rounded_rectangle([90, 540, W - 90, 980], radius=40, fill=(250, 248, 240))
        fq = font(BOLD, 64); lines = wrap_words(d, q["q"].split(), fq, 800)
        while len(lines) > 4: fq = font(BOLD, fq.size - 4); lines = wrap_words(d, q["q"].split(), fq, 800)
        yy = 760 - len(lines) * fq.size * 1.2 / 2
        for ln in lines:
            d.text((W / 2, yy + fq.size * 0.6), " ".join(ln), font=fq, fill=(20, 20, 30), anchor="mm"); yy += fq.size * 1.2
        answered = t >= rev["start"]
        for i, opt in enumerate(["TRUE", "FALSE"]):
            x0 = 110 + i * 450; box = [x0, 1040, x0 + 410, 1180]
            col = (255, 255, 255, 40)
            fill = (40, 44, 70)
            if answered: fill = GREEN if opt == rev["reveal"] else (60, 60, 70)
            d.rounded_rectangle(box, radius=30, fill=fill, outline=WHITE, width=4)
            d.text(((box[0] + box[2]) / 2, 1110), opt, font=font(BOLD, 64), fill=WHITE, anchor="mm")
        if pause["start"] <= t < pause["end"]:
            left = math.ceil(pause["end"] - t)
            d.text((W / 2, 1340), str(left), font=font(BOLD, int(150 * (1 + 0.15 * (1 - ((pause["end"] - t) % 1))))), fill=YELLOW, anchor="mm", stroke_width=8, stroke_fill=(10, 10, 20))
        else:
            karaoke(img, ch, t, y_center=1420, size=60)
    else:
        hook_text(img, s["cover"], s["accent"], size=110)
        karaoke(img, ch, t, y_center=1500, size=60)
    progress(img, t, dur)
    return img

# ---------------- COUNTDOWN: ranked list ----------------
def scene_countdown(s, tl, ch, t, dur, bg, cover=False):
    img = bg_frame(bg, t).convert("RGBA")
    img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, 80)))
    header(img, s["label"]); d = ImageDraw.Draw(img)
    if cover:
        hook_text(img, s["cover"], s["accent"], size=130); return img
    ranks = [it for it in tl if it.get("rank")]
    cur = [it for it in ranks if it["start"] <= t]
    # ladder of revealed ranks
    for i, rk in enumerate(sorted(ranks, key=lambda x: x["rank"])):
        y = 440 + i * 150; revealed = rk in cur; is_cur = cur and rk is cur[-1] and t < rk["end"] + 0.3
        fill = YELLOW if is_cur else ((40, 44, 70) if revealed else (30, 32, 50))
        tcol = (20, 20, 30) if is_cur else WHITE
        k = ease((t - rk["start"]) / 0.3) if revealed else 1
        x_off = int(300 * (1 - k)) if revealed else 0
        d.rounded_rectangle([90 + x_off, y, W - 90 + x_off, y + 120], radius=28, fill=fill)
        d.text((150 + x_off, y + 60), f"#{rk['rank']}", font=font(BOLD, 64), fill=tcol if revealed else (90, 90, 110), anchor="lm")
        label = rk["rule"] if revealed else "?"
        fr = font(BOLD, 50)
        while d.textlength(label, font=fr) > 680: fr = font(BOLD, fr.size - 2)
        d.text((290 + x_off, y + 60), label, font=fr, fill=tcol if revealed else (90, 90, 110), anchor="lm")
    karaoke(img, ch, t, y_center=1400, size=62)
    progress(img, t, dur)
    return img

SCENES = {"test": scene_test, "dialogue": scene_dialogue, "notes": scene_notes, "quiz": scene_quiz, "countdown": scene_countdown}

def render(sid):
    s = next(x for x in json.load(open(f"{base}/scripts.json")) if x["id"] == sid)
    tlj = json.load(open(f"{base}/out/v{sid}_timeline.json")); dur, tl = tlj["duration"], tlj["timeline"]
    ch = chunks_for([it for it in tl if it["text"]])
    bg = make_bg(sid); fn = SCENES[s["style"]]
    cover = fn(s, tl, ch, 0, dur, bg, cover=True).convert("RGB"); cover.save(f"{base}/out/v{sid}_cover.png")
    n = int(dur * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", f"{base}/out/v{sid}_silent.mp4"], stdin=subprocess.PIPE)
    first_t = tl[0]["start"]
    for i in range(n):
        t = i / FPS
        img = cover if t < first_t else fn(s, tl, ch, t, dur, bg).convert("RGB")
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    pad = ("aevalsrc='0.5*(sin(2*PI*220*t)+0.8*sin(2*PI*277.18*t)+0.7*sin(2*PI*329.63*t)+0.4*sin(2*PI*110*t))"
           "*(0.6+0.4*sin(2*PI*0.2*t))':s=24000:d=" + f"{dur:.2f}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{base}/out/v{sid}_silent.mp4", "-i", f"{base}/out/v{sid}_voice.wav",
                    "-f", "lavfi", "-i", pad, "-i", f"{base}/out/v{sid}_cover.png",
                    "-filter_complex", f"[2:a]lowpass=f=900,volume=0.035,afade=t=in:d=1,afade=t=out:st={dur-1.2:.2f}:d=1.2[m];[1:a]volume=1.0[v];[v][m]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-map", "3:v", "-c:v:0", "copy", "-c:v:1", "png", "-disposition:v:1", "attached_pic",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", f"{base}/out/FocusTip_{sid}.mp4"], check=True)
    print("done", sid, round(dur, 1))

def preview(sid, times):
    s = next(x for x in json.load(open(f"{base}/scripts.json")) if x["id"] == sid)
    tlj = json.load(open(f"{base}/out/v{sid}_timeline.json")); dur, tl = tlj["duration"], tlj["timeline"]
    ch = chunks_for([it for it in tl if it["text"]]); bg = make_bg(sid); fn = SCENES[s["style"]]
    ims = [fn(s, tl, ch, 0, dur, bg, cover=True).convert("RGB")] + [fn(s, tl, ch, tt, dur, bg).convert("RGB") for tt in times]
    sheet = Image.new("RGB", (len(ims) * 360, 640))
    for i, im in enumerate(ims): sheet.paste(im.resize((360, 640)), (i * 360, 0))
    sheet.save(f"{base}/out/preview_{sid}.jpg", quality=85)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        sid = int(sys.argv[2]); preview(sid, [float(x) for x in sys.argv[3:]])
    else:
        for a in sys.argv[1:]: render(int(a))
