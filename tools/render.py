import json, subprocess, sys, math, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

base = "/home/claude"
W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
YELLOW = (255, 216, 77)
WHITE = (255, 255, 255)

def font(p, s): return ImageFont.truetype(p, s)

# ---------- background: big blurred blobs, panned slowly ----------
def make_bg(seed):
    import random
    random.seed(seed)
    bw, bh = 1500, 2500
    img = Image.new("RGB", (bw, bh), (12, 18, 38))
    # vertical gradient
    d = ImageDraw.Draw(img)
    for y in range(bh):
        t = y / bh
        c = (int(12 + 20 * t), int(18 + 6 * t), int(38 + 40 * t))
        d.line([(0, y), (bw, y)], fill=c)
    blob = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blob)
    cols = [(88, 70, 255, 120), (255, 120, 90, 80), (40, 200, 220, 90), (180, 80, 255, 100)]
    for i in range(6):
        r = random.randint(250, 480)
        x, y = random.randint(0, bw), random.randint(0, bh)
        bd.ellipse([x - r, y - r, x + r, y + r], fill=cols[i % 4])
    blob = blob.filter(ImageFilter.GaussianBlur(140))
    img.paste(blob, (0, 0), blob)
    return img

def bg_frame(bg, t):
    ox = 210 + 200 * math.sin(t * 0.25)
    oy = 290 + 280 * math.sin(t * 0.17 + 1)
    return bg.crop((int(ox), int(oy), int(ox) + W, int(oy) + H))

def pill(img, label):
    d = ImageDraw.Draw(img)
    f = font(SEMI, 40)
    tw = d.textlength(label, font=f)
    x0 = (W - tw) / 2 - 34
    d.rounded_rectangle([x0, 250, x0 + tw + 68, 320], radius=35, fill=(255, 216, 77))
    d.text((W / 2, 285), label, font=f, fill=(20, 20, 30), anchor="mm")
    f2 = font(SEMI, 34)
    d.text((W / 2, 370), "@thebetterdesk", font=f2, fill=(255, 255, 255, 180), anchor="mm")

def wrap_words(d, words, f, maxw):
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if cur and d.textlength(test, font=f) > maxw:
            lines.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur: lines.append(cur)
    return lines

def draw_caption(img, words, active, scale=1.0, size=90):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(BOLD, size)
    lines = wrap_words(d, words, f, 900)
    lh = int(size * 1.25)
    total = lh * len(lines)
    y = 960 - total / 2
    k = 0
    for ln in lines:
        lw = d.textlength(" ".join(ln), font=f)
        x = (W - lw) / 2
        for w in ln:
            col = YELLOW if k == active else WHITE
            d.text((x, y), w, font=f, fill=col, stroke_width=7, stroke_fill=(10, 10, 20))
            x += d.textlength(w + " ", font=f)
            k += 1
        y += lh
    if scale != 1.0:
        sw, sh = int(W * scale), int(H * scale)
        layer2 = layer.resize((sw, sh), Image.LANCZOS)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer.paste(layer2, ((W - sw) // 2, (H - sh) // 2))
    img.paste(layer, (0, 0), layer)

def chunks_for(timeline):
    out = []
    for item in timeline:
        words = item["text"].split()
        groups, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 4 or re.search(r"[.,!?]$", w) and len(cur) >= 2:
                groups.append(cur); cur = []
        if cur:
            if groups and len(cur) == 1: groups[-1] += cur
            else: groups.append(cur)
        total_chars = sum(len(w) + 1 for w in words)
        t = item["start"]; dur = item["end"] - item["start"]
        for g in groups:
            gl = sum(len(w) + 1 for w in g)
            gd = dur * gl / total_chars
            wt, tt = [], t
            for w in g:
                wd = gd * (len(w) + 1) / gl
                wt.append((tt, tt + wd)); tt += wd
            out.append({"words": g, "start": t, "end": t + gd, "wt": wt})
            t += gd
    return out

def make_cover(s, bg):
    img = bg_frame(bg, 0).convert("RGBA")
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 70))
    img = Image.alpha_composite(img, dark)
    pill(img, s["label"])
    d = ImageDraw.Draw(img)
    f = font(BOLD, 118)
    y = 820
    for line in s["cover"]:
        # render with accent word in yellow
        words = line.split()
        lw = d.textlength(line, font=f)
        if lw > 980:
            f = font(BOLD, int(118 * 980 / lw))
            lw = d.textlength(line, font=f)
        x = (W - lw) / 2
        for w in words:
            col = YELLOW if w == s["accent"] or s["accent"] in w and len(s["accent"]) > 3 else WHITE
            d.text((x, y), w, font=f, fill=col, stroke_width=8, stroke_fill=(10, 10, 20))
            x += d.textlength(w + " ", font=f)
        y += 150
    f3 = font(SEMI, 40)
    d.rounded_rectangle([270, 1180, 810, 1250], radius=14, outline=(255, 255, 255), width=3)
    d.text((W / 2, 1215), "THE FOCUS BLUEPRINT", font=f3, fill=WHITE, anchor="mm")
    return img.convert("RGB")

def render(sid):
    s = [x for x in json.load(open(f"{base}/scripts.json")) if x["id"] == sid][0]
    tl = json.load(open(f"{base}/out/v{sid}_timeline.json"))
    dur = tl["duration"]
    bg = make_bg(sid)
    cover = make_cover(s, bg)
    cover.save(f"{base}/out/v{sid}_cover.png")
    ch = chunks_for(tl["timeline"])
    n = int(dur * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", f"{base}/out/v{sid}_silent.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        if i == 0 or (ch and t < ch[0]["start"]):
            p.stdin.write(cover.tobytes()); continue
        img = bg_frame(bg, t).convert("RGBA")
        pill(img, s["label"])
        cur = None
        for c in ch:
            if c["start"] <= t < c["end"]: cur = c; break
        if cur is None:
            # hold the last finished chunk briefly in gaps
            prev = [c for c in ch if c["end"] <= t and t - c["end"] < 0.3]
            if prev: cur = prev[-1]
        if cur:
            active = -1
            for j, (a, b) in enumerate(cur["wt"]):
                if a <= t < b: active = j
            age = t - cur["start"]
            scale = 0.88 + 0.12 * min(1, age / 0.12)
            draw_caption(img, cur["words"], active, scale)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, int(W * t / dur), 12], fill=YELLOW)
        p.stdin.write(img.convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    # mix voice with soft pad, mux, embed cover as thumbnail
    pad = ("aevalsrc='0.5*(sin(2*PI*220*t)+0.8*sin(2*PI*277.18*t)+0.7*sin(2*PI*329.63*t)+0.4*sin(2*PI*110*t))"
           "*(0.6+0.4*sin(2*PI*0.2*t))':s=24000:d=" + f"{dur:.2f}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{base}/out/v{sid}_silent.mp4", "-i", f"{base}/out/v{sid}_voice.wav",
                    "-f", "lavfi", "-i", pad, "-i", f"{base}/out/v{sid}_cover.png",
                    "-filter_complex", f"[2:a]lowpass=f=900,volume=0.035,afade=t=in:d=1,afade=t=out:st={dur-1.2:.2f}:d=1.2[m];[1:a]volume=1.0[v];[v][m]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-map", "3:v", "-c:v:0", "copy", "-c:v:1", "png", "-disposition:v:1", "attached_pic",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
                    f"{base}/out/FocusTip_{sid}.mp4"], check=True)
    print("done", sid)

if __name__ == "__main__":
    for a in sys.argv[1:]: render(int(a))
