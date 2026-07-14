"""
backgrounds.py — generates the SciPy 2026 slide background images.

Outputs (all 1920x1080):
  hero.png / hero-bare.png — title hero: sage diagonal gradient with a faint
    plot grid, a stream of two-tone (cream + deep-aqua) scatter markers with
    thin dark outlines flowing in from the lower-left, and right-aligned white
    Lato text (bare = no text, for reveal.js to overlay its own).
  thankyou-bare.png — closing slide: light background with the same faint grid
    and a sparse teal/orange scatter, a nod to the hero's points.

Requires: numpy, Pillow, and the Lato family. Fonts are resolved by
_find_font_dir() — vendored in ./fonts by default, else the Linux system path.
Run: python3 backgrounds.py  ->  writes all of the above.
"""
import os, numpy as np, math, random
from PIL import Image, ImageFilter, ImageDraw, ImageFont

W, H = 1920, 1080

def _find_font_dir():
    """Prefer Lato vendored beside this script, else the Linux system path."""
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (os.path.join(here, "fonts"), "/usr/share/fonts/truetype/lato/"):
        if os.path.isdir(c) and any(f.startswith("Lato") for f in os.listdir(c)):
            return c
    return os.path.join(here, "fonts")

FONT_DIR = _find_font_dir()

# ---------- helpers ----------
def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")

def fnt(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)

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

_ring_cache = {}
def _ring_sprite(r):
    """Hollow ring (scatter-marker outline) with ~1px antialiasing."""
    r = max(2, int(round(r)))
    if r in _ring_cache:
        return _ring_cache[r]
    w = max(1.2, r * 0.12)
    s = r * 2 + 4; c = (s - 1) / 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    outer = np.clip(r - d + 0.5, 0, 1)
    inner = np.clip((r - w) - d + 0.5, 0, 1)
    alpha = np.clip(outer - inner, 0, 1)
    _ring_cache[r] = alpha
    return alpha

def stamp_dots(dots, color, sprite=_dot_sprite, alpha_scale=1.0):
    """Alpha-accumulate single-color sprites so overlaps stay clean (no rings)."""
    A = np.zeros((H, W), np.float32)
    for x, y, r, a in dots:
        spr = sprite(r); s = spr.shape[0]; half = s // 2
        x0, y0 = int(x) - half, int(y) - half
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        dx1, dy1 = min(W, x0 + s), min(H, y0 + s)
        if dx1 <= dx0 or dy1 <= dy0:
            continue
        sub = spr[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0)] * (a / 255.0 * alpha_scale)
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
    for _ in range(220):  # ambient scatter, weighted toward bottom
        x = rng.random() * W
        y = (rng.random() ** 0.6) * H
        r = rng.uniform(2, 9)
        a = rng.uniform(30, 120) * (0.4 + 0.6 * (y / H))
        dots.append((x, y, r, a))
    x0 = W * 0.14  # shift the stream's dense start rightward for visual balance
    for _ in range(170):  # bright stream, rising as it peters out to the right
        t = rng.random() ** 1.8
        cx = x0 + t * W * right
        cy = H * (0.80 - 0.22 * t) + rng.gauss(0, 58)
        cx += rng.gauss(0, 42); cy += rng.gauss(0, 32)
        r = rng.uniform(3, 16) * (1.1 - 0.45 * t)
        a = rng.uniform(120, 235) * (1.05 - 0.30 * t)
        dots.append((cx, cy, r, a))
    for _ in range(28):  # faint stragglers drifting up-right toward the title
        cx = rng.uniform(W * 0.34, W * 0.62)
        cy = rng.uniform(H * 0.42, H * 0.66)
        dots.append((cx, cy, rng.uniform(2, 8), rng.uniform(35, 110)))
    for _ in range(16):  # sparse markers filling the empty upper-left
        cx = rng.uniform(0, W * 0.30)
        cy = rng.uniform(H * 0.08, H * 0.44)
        dots.append((cx, cy, rng.uniform(2, 7), rng.uniform(30, 95)))
    for _ in range(20):  # faint stragglers scattered around the lower-left cluster
        cx = rng.uniform(0, W * 0.30)
        cy = rng.uniform(H * 0.58, H * 0.98)
        dots.append((cx, cy, rng.uniform(2, 8), rng.uniform(35, 110)))
    for _ in range(12):  # big anchor dots, lower-left of center
        x = rng.uniform(W * 0.12, W * 0.34); y = rng.uniform(H * 0.72, H * 0.92)
        dots.append((x, y, rng.uniform(10, 22), rng.uniform(180, 245)))
    return dots

# ---------- compose ----------
def grid_overlay(step=120, color=(255, 255, 255), alpha=16):
    """Faint plot-style gridlines, so the scatter reads as a chart."""
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for x in range(0, W, step):
        gd.line([(x, 0), (x, H)], fill=color + (alpha,), width=1)
    for y in range(0, H, step):
        gd.line([(0, y), (W, y)], fill=color + (alpha,), width=1)
    return g

def main(out="hero.png", text=True, title_color=(255, 255, 255),
         sub_color=(28, 58, 56), author_italic=True,
         author_sizes=(66, 58), author_ys=(762, 862)):
    canvas = to_img(gradient(hex2rgb("#728A82"), hex2rgb("#BED0CA"), 55)).convert("RGBA")
    canvas.alpha_composite(grid_overlay())

    # keep points out of the lower-right text block
    dots = [d for d in gen_dots(1, right=0.50) if not (d[0] > 900 and d[1] > 760)]
    # two-tone: mostly cream, a scattering of deep-aqua accent dots. Each point is
    # a translucent fill with a crisp outline so it reads as a scatter marker.
    rng = random.Random(583)
    cream, accent = [], []
    for d in dots:
        (accent if rng.random() < 0.25 else cream).append(d)
    for pts, col in [(cream, (244, 241, 228)), (accent, hex2rgb("#33C6C6"))]:
        canvas.alpha_composite(stamp_dots(pts, col, alpha_scale=0.30))
    # thin dark outline on top of every marker so it reads as a data point
    canvas.alpha_composite(stamp_dots(cream + accent, (44, 50, 50), sprite=_ring_sprite, alpha_scale=0.85))

    img = canvas.convert("RGB")

    if not text:  # bare background (e.g. for reveal.js to overlay its own text)
        img.save(out)
        print("saved", out)
        return

    d = ImageDraw.Draw(img)
    WHITE = (255, 255, 255)
    RT = 1852  # shared right margin for all text

    def dr(t, y, f, c):  # right-aligned line
        w = d.textlength(t, font=f)
        d.text((RT - w, y), t, font=f, fill=c)

    def drs(t, y, f, c, tr=5):  # right-aligned, letter-spaced line
        cx = RT - (sum(d.textlength(ch, font=f) + tr for ch in t) - tr)
        for ch in t:
            d.text((cx, y), ch, font=f, fill=c)
            cx += d.textlength(ch, font=f) + tr

    dr("It’s (still) very", 140, fnt("Lato-Black.ttf", 124), title_color)
    dr("bad to be wrong", 278, fnt("Lato-Black.ttf", 124), title_color)
    drs("AGENTS FOR CORRECT, TRANSPARENT,", 476, fnt("Lato-Medium.ttf", 56), sub_color)
    drs("AND REPRODUCIBLE DATA ANALYSIS", 550, fnt("Lato-Medium.ttf", 56), sub_color)
    af = "Lato-MediumItalic.ttf" if author_italic else "Lato-Medium.ttf"
    dr("Sara Altman & Simon Couch", author_ys[0], fnt(af, author_sizes[0]), WHITE)
    dr("AI Core Team @ Posit", author_ys[1], fnt("Lato-Medium.ttf", author_sizes[1]), WHITE)

    img.save(out)
    print("saved", out)

def gen_dots_thankyou(seed=417, layout="corner"):
    """A sparse nod to the hero's scatter, kept clear of the centered 'thank
    you' text. Far fewer points than the hero.

    layout="corner": a short stream drifting up from the lower-right corner,
      with a few big anchor dots — the whole gesture pooled in one corner.
    layout="band":   the stream spread horizontally along the bottom edge, so
      the weight sits under the text rather than in the corner.
    """
    rng = random.Random(seed)
    dots = []
    if layout == "band":
        for _ in range(52):  # scatter riding along the bottom, densest at right
            t = rng.random() ** 1.3
            cx = W * (0.30 + 0.66 * (1 - t)) + rng.gauss(0, 60)
            cy = H * (0.88 - 0.10 * t) + rng.gauss(0, 40)
            r = rng.uniform(3, 14) * (1.05 - 0.35 * t)
            a = rng.uniform(120, 235) * (1.0 - 0.20 * t)
            dots.append((cx, cy, r, a))
        for _ in range(8):  # big anchor dots spread across the bottom
            x = rng.uniform(W * 0.34, W * 0.90); y = rng.uniform(H * 0.80, H * 0.94)
            dots.append((x, y, rng.uniform(9, 18), rng.uniform(180, 245)))
        return dots
    # layout == "corner"
    x0 = W * 0.92  # dense start in the lower-right, tapering up and leftward
    for _ in range(46):
        t = rng.random() ** 1.7
        cx = x0 - t * W * 0.42
        cy = H * (0.86 - 0.20 * t) + rng.gauss(0, 46)
        cx += rng.gauss(0, 38); cy += rng.gauss(0, 26)
        r = rng.uniform(3, 15) * (1.1 - 0.45 * t)
        a = rng.uniform(120, 235) * (1.05 - 0.30 * t)
        dots.append((cx, cy, r, a))
    for _ in range(10):  # a few big anchor dots in the lower-right
        x = rng.uniform(W * 0.70, W * 0.92); y = rng.uniform(H * 0.72, H * 0.92)
        dots.append((x, y, rng.uniform(9, 20), rng.uniform(180, 245)))
    return dots


def thankyou(out="thankyou-bare.png", layout="corner"):
    """Light-background companion to the hero for the closing slide: the same
    faint grid and two-tone (teal/orange) scatter markers, tinted to read on
    #F6FAFD, sparse and shifted below the centered text. See gen_dots_thankyou
    for the `layout` options."""
    canvas = Image.new("RGBA", (W, H), hex2rgb("#F6FAFD") + (255,))
    canvas.alpha_composite(grid_overlay(color=hex2rgb("#093A3E"), alpha=12))

    dots = [d for d in gen_dots_thankyou(layout=layout)
            if not (W * 0.30 < d[0] < W * 0.70 and H * 0.36 < d[1] < H * 0.64)]
    rng = random.Random(908)
    teal, accent = [], []
    for d in dots:
        (accent if rng.random() < 0.38 else teal).append(d)
    for pts, col in [(teal, hex2rgb("#33C6C6")), (accent, hex2rgb("#F37748"))]:
        canvas.alpha_composite(stamp_dots(pts, col, alpha_scale=0.42))
    canvas.alpha_composite(stamp_dots(teal + accent, hex2rgb("#093A3E"),
                                      sprite=_ring_sprite, alpha_scale=0.55))

    canvas.convert("RGB").save(out)
    print("saved", out)


if __name__ == "__main__":
    main("hero.png", title_color=(255, 255, 255), sub_color=(255, 255, 255),
         author_italic=False, author_sizes=(52, 44), author_ys=(776, 852))
    main("hero-bare.png", text=False)
    thankyou("thankyou-bare.png", layout="band")
