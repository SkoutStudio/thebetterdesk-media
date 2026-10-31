import json, os, sys
sys.path.insert(0, "/home/claude")
from PIL import Image, ImageDraw, ImageFont
from render import make_bg, bg_frame, font, BOLD, SEMI, YELLOW, WHITE, W, H

base = "/home/claude"
LOGO = Image.open(f"{base}/out/thebetterdesk_logo.png").resize((90, 90))
mask = Image.new("L", (90, 90), 0); ImageDraw.Draw(mask).ellipse([0, 0, 90, 90], fill=255)
GREY = (200, 205, 225)

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if cur and d.textlength(t, font=f) > maxw:
            out.append(cur); cur = w
        else:
            cur = t
    if cur: out.append(cur)
    return out

def base_slide(bg, seed_t, idx, total, tag):
    img = bg_frame(bg, seed_t).convert("RGBA")
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 60)); img = Image.alpha_composite(img, dark)
    d = ImageDraw.Draw(img)
    # header: logo + handle
    img.paste(LOGO, (90, 200), mask)
    d.text((200, 245), "@thebetterdesk", font=font(SEMI, 38), fill=WHITE, anchor="lm")
    # tag pill right
    f = font(SEMI, 32); tw = d.textlength(tag, font=f)
    d.rounded_rectangle([W - 90 - tw - 48, 218, W - 90, 272], radius=27, fill=YELLOW)
    d.text((W - 90 - (tw + 48) / 2, 245), tag, font=f, fill=(20, 20, 30), anchor="mm")
    # counter
    d.text((W / 2, 1560), f"{idx}/{total}", font=font(SEMI, 34), fill=GREY, anchor="mm")
    # dots
    return img, d

def draw_lines(d, lines, f, y, accent=None, lh=1.18, color=WHITE):
    for ln in lines:
        words = ln.split(); lw = d.textlength(ln, font=f); x = (W - lw) / 2
        for w in words:
            col = YELLOW if accent and w.strip("?.!,") == accent.strip("?.!,") else color
            d.text((x, y), w, font=f, fill=col, stroke_width=6, stroke_fill=(10, 10, 20))
            x += d.textlength(w + " ", font=f)
        y += int(f.size * lh)
    return y

def make(c):
    seed = sum(map(ord, c["id"]))
    bg = make_bg(seed)
    total = len(c["slides"]) + 2
    outdir = f"{base}/out/{c['id']}"; os.makedirs(outdir, exist_ok=True)
    # cover
    img, d = base_slide(bg, 0, 1, total, c["tag"])
    f = font(BOLD, 128)
    lines = c["cover"]
    while max(d.textlength(l, font=f) for l in lines) > 960: f = font(BOLD, f.size - 6)
    y = 960 - len(lines) * f.size * 1.18 / 2 - 60
    y = draw_lines(d, lines, f, y, c["accent"])
    d.text((W / 2, y + 60), c["sub"], font=font(SEMI, 50), fill=GREY, anchor="mm")
    d.text((W / 2, 1460), "swipe  →", font=font("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 46), fill=YELLOW, anchor="mm")
    img.convert("RGB").save(f"{outdir}/01.jpg", quality=92)
    # content slides
    for i, (num, title, body) in enumerate(c["slides"], start=2):
        img, d = base_slide(bg, i * 3.0, i, total, c["tag"])
        # big number
        d.text((W / 2, 560), num, font=font(BOLD, 220), fill=YELLOW, anchor="mm", stroke_width=6, stroke_fill=(10, 10, 20))
        ft = font(BOLD, 92)
        tl = wrap(d, title, ft, 940)
        while len(tl) > 3: ft = font(BOLD, ft.size - 6); tl = wrap(d, title, ft, 940)
        y = draw_lines(d, tl, ft, 760)
        fb = font(SEMI, 52)
        if "FIX:" in body:
            pre, fix = body.split("FIX:", 1)
            y = draw_lines(d, wrap(d, pre.strip(), fb, 900), fb, y + 50, color=GREY, lh=1.3)
            y += 30
            box = wrap(d, fix.strip(), fb, 820)
            bh = int(len(box) * fb.size * 1.3) + 120
            d.rounded_rectangle([110, y, W - 110, y + bh], radius=30, fill=(28, 26, 52), outline=YELLOW, width=4)
            d.text((W / 2, y + 45), "FIX", font=font(BOLD, 40), fill=YELLOW, anchor="mm")
            draw_lines(d, box, fb, y + 85, lh=1.3)
        else:
            draw_lines(d, wrap(d, body, fb, 900), fb, y + 50, color=GREY, lh=1.3)
        img.convert("RGB").save(f"{outdir}/{i:02d}.jpg", quality=92)
    # end slide
    img, d = base_slide(bg, 40, total, total, c["tag"])
    a, b, cta = c["end"]
    fa = font(BOLD, 100)
    y = draw_lines(d, wrap(d, a, fa, 940), fa, 680)
    fb2 = font(BOLD, 60); y = draw_lines(d, wrap(d, b, fb2, 900), fb2, y + 40, color=YELLOW)
    fc = font(SEMI, 46); tw = d.textlength(cta, font=fc)
    d.rounded_rectangle([(W - tw) / 2 - 40, y + 90, (W + tw) / 2 + 40, y + 190], radius=50, outline=WHITE, width=4)
    d.text((W / 2, y + 140), cta, font=fc, fill=WHITE, anchor="mm")
    img.convert("RGB").save(f"{outdir}/{total:02d}.jpg", quality=92)
    print(c["id"], total, "slides")

if __name__ == "__main__":
    for c in json.load(open(f"{base}/carousels.json")): make(c)
