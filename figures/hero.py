"""
hero.py — generates hero.png, the SciPy 2026 title hero image.

Composition: olive-green diagonal gradient background, a stream of cream
"data points" flowing in from the lower-left, and right-aligned Lato text
(title / subtitle / authors / team). No plot panel.

Requires: numpy, Pillow, and the Lato font family installed at FONT_DIR.
Run: python3 hero.py  ->  writes hero.png (1920x1080).
"""
import numpy as np, math, random
from PIL import Image, ImageFilter, ImageDraw, ImageFont

W, H = 1920, 1080
FONT_DIR = "/usr/share/fonts/truetype/lato/"

# ---------- helpers ----------
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")

def fnt(name, size):
    return ImageFont.truetype(FONT_DIR + name, size)

def gradient(c1, c2, angle_deg):
    """Linear gradient across the canvas. angle 0 = L->R, 90 = top->bottom."""
    a = math.radians(angle_deg)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = math.cos(a) * (xx / W) + math.sin(a) * (yy / H)
    u = (u - u.min()) / (u.max() - u.min())
    c1 = np.array(c1, np.float32); c2 = np.array(c2, np.float32)
    return c1[None, None, :] * (1 - u[..., None]) + c2[None, None, :] * u[..., None]

# ---------- points ----------
_sprite_cache = {}
def _dot_sprite(r):
    """Crisp-edged disk with ~1px antialiasing (no feathered dissolve)."""
    r = max(2, int(round(r)))
    if r in _sprite_cache:
        return _sprite_cache[r]
    s = r * 2 + 4; c = (s - 1) / 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    alpha = np.clip(r - d + 0.5, 0, 1)
    _sprite_cache[r] = alpha
    return alpha

def stamp_dots(dots, color):
    """Alpha-accumulate single-color dots so overlaps stay clean (no rings)."""
    A = np.zeros((H, W), np.float32)
    for x, y, r, a in dots:
        spr = _dot_sprite(r); s = spr.shape[0]; half = s // 2
        x0, y0 = int(x) - half, int(y) - half
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        dx1, dy1 = min(W, x0 + s), min(H, y0 + s)
        if dx1 <= dx0 or dy1 <= dy0:
            continue
        sub = spr[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0)] * (a / 255.0)
        reg = A[dy0:dy1, dx0:dx1]
        A[dy0:dy1, dx0:dx1] = sub + reg * (1 - sub)
    out = np.zeros((H, W, 4), np.float32)
    out[..., 0], out[..., 1], out[..., 2] = color
    out[..., 3] = np.clip(A, 0, 1) * 255
    return Image.fromarray(out.astype(np.uint8), "RGBA")

def gen_dots(seed=1, right=0.50):
    """Ambient scatter + a bright stream from the lower-left that tapers off
    to the right (density biased low via t**1.8) + a few big anchor dots."""
    rng = random.Random(seed)
    dots = []
    for _ in range(440):  # ambient scatter, weighted toward bottom
        x = rng.random() * W
        y = (rng.random() ** 0.6) * H
        r = rng.uniform(2, 9)
        a = rng.uniform(30, 120) * (0.4 + 0.6 * (y / H))
        dots.append((x, y, r, a))
    for _ in range(340):  # bright stream, petering out to the right
        t = rng.random() ** 1.8
        cx = t * W * right
        cy = H * (0.80 - 0.13 * t) + rng.gauss(0, 58)
        cx += rng.gauss(0, 42); cy += rng.gauss(0, 32)
        r = rng.uniform(3, 16) * (1.1 - 0.45 * t)
        a = rng.uniform(120, 235) * (1.05 - 0.30 * t)
        dots.append((cx, cy, r, a))
    for _ in range(22):  # big anchor dots, bottom-left
        x = rng.uniform(0, W * 0.18); y = rng.uniform(H * 0.72, H * 0.92)
        dots.append((x, y, rng.uniform(10, 22), rng.uniform(180, 245)))
    return dots

# ---------- compose ----------
def main(out="hero.png", text=True):
    canvas = to_img(gradient(hex2rgb("#52704F"), hex2rgb("#B3B19D"), 55)).convert("RGBA")

    # keep points out of the lower-right text block
    dots = [d for d in gen_dots(1, right=0.50) if not (d[0] > 900 and d[1] > 760)]
    layer = stamp_dots(dots, (244, 241, 228)).filter(ImageFilter.GaussianBlur(0.15))
    canvas.alpha_composite(layer)

    img = canvas.convert("RGB")

    if not text:  # bare background (e.g. for reveal.js to overlay its own text)
        img.save(out)
        print("saved", out)
        return

    d = ImageDraw.Draw(img)
    WHITE = (255, 255, 255)
    SUB = (210, 220, 208)
    RT = 1852  # shared right margin for all text

    def dr(t, y, f, c):  # right-aligned line
        w = d.textlength(t, font=f)
        d.text((RT - w, y), t, font=f, fill=c)

    def drs(t, y, f, c, tr=5):  # right-aligned, letter-spaced line
        cx = RT - (sum(d.textlength(ch, font=f) + tr for ch in t) - tr)
        for ch in t:
            d.text((cx, y), ch, font=f, fill=c)
            cx += d.textlength(ch, font=f) + tr

    dr("It’s (still) very", 140, fnt("Lato-Black.ttf", 124), WHITE)
    dr("bad to be wrong", 278, fnt("Lato-Black.ttf", 124), WHITE)
    drs("AGENTS FOR CORRECT, TRANSPARENT,", 476, fnt("Lato-Medium.ttf", 56), SUB)
    drs("AND REPRODUCIBLE DATA ANALYSIS", 550, fnt("Lato-Medium.ttf", 56), SUB)
    dr("Sara Altman & Simon Couch", 762, fnt("Lato-MediumItalic.ttf", 66), WHITE)
    dr("AI Core Team @ Posit", 862, fnt("Lato-Medium.ttf", 58), WHITE)

    img.save(out)
    print("saved", out)

if __name__ == "__main__":
    main("hero.png", text=True)
    main("hero-bare.png", text=False)
