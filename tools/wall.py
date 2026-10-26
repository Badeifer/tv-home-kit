"""Wallpaper building blocks for tv-home skins. Every function draws into a float RGB canvas
(H x W x 3, values 0..1) so layers blend without banding; save() adds grain and writes a JPEG.

The launcher puts the clock top-left and the dock across the lower third, so keep the brightest
detail upper-right or centre and let the bottom fall dark (use vignette() or shade_bottom()).
"""
import numpy as np
from PIL import Image

W, H = 1920, 1080


def hex_rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def canvas(color='#000000'):
    return np.ones((H, W, 3)) * hex_rgb(color)


def _grid():
    y, x = np.mgrid[0:H, 0:W]
    return x / W, y / H


def gradient(c, stops):
    """Vertical gradient. stops: [(0.0, '#hex'), (0.6, '#hex'), (1.0, '#hex')], top to bottom."""
    t = np.linspace(0, 1, H)
    pos = [p for p, _ in stops]
    cols = np.array([hex_rgb(h) for _, h in stops])
    for ch in range(3):
        c[:, :, ch] = np.interp(t, pos, cols[:, ch])[:, None]
    return c


def glow(c, cx, cy, radius, color, strength=1.0):
    """Soft additive light. cx, cy in 0..1 of width/height, radius in 0..1 of width."""
    x, y = _grid()
    d = np.sqrt((x - cx) ** 2 + ((y - cy) * H / W) ** 2) / radius
    c += np.exp(-d ** 2 * 2.5)[..., None] * hex_rgb(color) * strength
    return c


def stars(c, n=900, seed=1, top=0.75, brightness=1.0):
    """Starfield in the top `top` of the frame, fewer near the horizon."""
    rng = np.random.default_rng(seed)
    xs = rng.integers(0, W, n)
    ys = (rng.random(n) ** 1.6 * H * top).astype(int)
    b = rng.random(n) ** 3 * brightness
    tint = rng.random((n, 3)) * 0.15 + 0.85
    for x, y, v, t in zip(xs, ys, b, tint):
        c[y, x] += v * t
        if v > 0.5:  # a few bright stars get a small cross of light
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    c[y + dy, x + dx] += v * t * 0.35
    return c


def aurora(c, colors=('#2CF2B4', '#7B5CFF'), base=0.42, height=0.32, waves=3, seed=4, strength=0.9):
    """Curtains of aurora: bright lower edge at `base` (0..1 of height) fading upward over `height`."""
    rng = np.random.default_rng(seed)
    x, y = _grid()
    out = np.zeros_like(c)
    for i in range(waves):
        f1, f2 = rng.uniform(1.5, 4), rng.uniform(5, 11)
        p1, p2 = rng.uniform(0, 6.28, 2)
        edge = base + 0.035 * np.sin(x * f1 * 6.28 + p1) + 0.012 * np.sin(x * f2 * 6.28 + p2) - i * 0.04
        rel = (edge - y) / height  # 0 at the lower edge, 1 at the top of the curtain
        # Bright just above the lower edge, a soft fade below it, a long thin fade upward.
        above = np.where(rel > 0, np.exp(-rel * 2.6) * (1 - np.exp(-rel * 30)), 0)
        below = 0.35 * np.exp(-np.abs(rel) * 14)
        body = np.maximum(above, below)
        # Fine vertical rays: a sum of uneven sines so the streaks don't look regular.
        rays = sum(np.sin(x * rng.uniform(60, 240) + rng.uniform(0, 6.28)) for _ in range(4)) / 4
        rays = 0.45 + 0.55 * np.clip(rays + 0.4, 0, 1) ** 1.5
        mix = np.clip(rel, 0, 1)[..., None]
        col = hex_rgb(colors[0]) * (1 - mix) + hex_rgb(colors[-1]) * mix
        across = 0.55 + 0.45 * np.sin(x * rng.uniform(1, 2.5) * 6.28 + rng.uniform(0, 6.28))
        out += (body * rays * across)[..., None] * col / waves
    c += out * strength
    return c


def ridge(c, color, base, amp, seed=0, roughness=0.55, octaves=7, haze=None):
    """Mountain/hill silhouette filled below a fractal ridge line at `base` (0..1 of height)."""
    rng = np.random.default_rng(seed)
    xs = np.linspace(0, 1, W)
    line = np.zeros(W)
    a, freq = 1.0, 2
    for _ in range(octaves):
        pts = rng.uniform(-1, 1, freq + 1)
        line += a * np.interp(xs, np.linspace(0, 1, freq + 1), pts)
        a *= roughness
        freq *= 2
    line = base - line / 2 * amp
    yy = np.arange(H)[:, None] / H
    mask = (yy >= line[None, :]).astype(float)
    col = hex_rgb(color)
    if haze:  # fade the top of the range toward a haze colour for depth
        depth = np.clip((yy - line[None, :]) / 0.25, 0, 1)[..., None]
        col = hex_rgb(haze) * (1 - depth) + col * depth
    c[:] = c * (1 - mask[..., None]) + col * mask[..., None]
    return c


def retro_sun(c, cx=0.68, cy=0.50, r=0.16, top='#FFD36E', bottom='#FF2E88', bands=7):
    """Synthwave sun: vertical gradient disc cut by widening horizontal gaps toward its bottom."""
    x, y = _grid()
    dx, dy = (x - cx), (y - cy) * H / W
    inside = (dx ** 2 + dy ** 2) <= r ** 2
    t = np.clip((y - (cy - r * W / H)) / (2 * r * W / H), 0, 1)[..., None]
    col = hex_rgb(top) * (1 - t) + hex_rgb(bottom) * t
    rel = (y - cy) / (r * W / H)  # -1 top .. 1 bottom
    gaps = np.zeros_like(inside)
    for i in range(bands):
        g0 = 0.05 + i * 0.13
        gaps |= (rel > g0) & (rel < g0 + 0.015 + i * 0.012)
    m = (inside & ~gaps)[..., None]
    c[:] = np.where(m, col, c)
    return glow(c, cx, cy, r * 2.2, bottom, 0.35)


def perspective_grid(c, horizon=0.62, color='#FF3EC8', spacing=0.08, lines=26, strength=0.9):
    """Neon floor grid from the horizon down, lines thinning and fading toward the horizon."""
    x, y = _grid()
    below = y > horizon
    depth = np.where(below, (y - horizon) / (1 - horizon), 1e-3)
    z = 1 / np.maximum(depth, 1e-3)
    hz = np.abs(((z * spacing * 6) % 1) - 0.5)
    hline = np.exp(-(hz / (0.02 * z)) ** 2) * below
    px = (x - 0.5) / np.maximum(depth, 1e-3)
    vz = np.abs(((px * lines / 6) % 1) - 0.5)
    vline = np.exp(-(vz / (0.012 / np.maximum(depth, 0.02))) ** 2) * below
    fade = np.clip(depth * 3, 0, 1)
    c += (np.maximum(hline, vline) * fade)[..., None] * hex_rgb(color) * strength
    return glow(c, 0.5, horizon, 0.5, color, 0.18)


def water_reflection(c, horizon, strength=0.45, color='#000814'):
    """Mirror everything above `horizon` into the area below it, darkened and rippled."""
    hy = int(H * horizon)
    span = H - hy
    src = c[max(0, hy - span):hy][::-1]
    rows = np.arange(src.shape[0])
    shift = (np.sin(rows * 0.9) * (1 + rows / 40)).astype(int)
    ref = np.stack([np.roll(src[i], shift[i], axis=0) for i in rows])
    k = np.linspace(strength, strength * 0.2, ref.shape[0])[:, None, None]
    c[hy:hy + ref.shape[0]] = ref * k + hex_rgb(color) * (1 - k)
    return c


def shade_bottom(c, start=0.55, amount=0.85):
    """Darken from `start` (0..1 of height) to the bottom, where the dock sits."""
    t = np.clip((np.arange(H) / H - start) / (1 - start), 0, 1) ** 1.4
    c *= (1 - t * amount)[:, None, None]
    return c


def vignette(c, amount=0.45):
    x, y = _grid()
    d = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.71
    c *= (1 - amount * d ** 2)[..., None]
    return c


def save(c, path, grain=0.012, seed=9):
    """Tone-map softly (no hard clipping of glows), add grain against banding, write a JPEG."""
    rng = np.random.default_rng(seed)
    c = 1 - np.exp(-c * 1.15)  # soft shoulder so overlapping glows roll off instead of clipping
    c = c / (1 - np.exp(-1.15))
    c += rng.normal(0, grain, c.shape)
    img = (np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(img).save(path, quality=92, optimize=True, progressive=True)


def curtain(c, x0, x1, color='#E0A060', folds=7, strength=0.55, seed=3):
    """Pleated stage curtain between x0 and x1 (0..1 of width), lit from its inner edge, fading up and down."""
    rng = np.random.default_rng(seed)
    x, y = _grid()
    inside = (x >= x0) & (x <= x1)
    t = np.clip((x - x0) / max(x1 - x0, 1e-6), 0, 1)
    phase = rng.uniform(0, 6.28)
    pleat = 0.5 + 0.5 * np.sin(t * folds * 6.28 + phase + 0.6 * np.sin(t * 13))
    pleat = pleat ** 1.3
    lit = t ** 1.5  # brighter towards the inner edge, where the light falls
    vertical = np.exp(-((y - 0.62) / 0.42) ** 2)
    c += (inside * pleat * (0.25 + 0.75 * lit) * vertical)[..., None] * hex_rgb(color) * strength
    return c


def rim_arc(c, cx, cy, r, color='#E8B070', width=0.004, strength=1.0, start=-0.6, end=1.35, fill='#0A0806'):
    """A huge dark disc with light catching its edge: a thin bright rim over an arc (angles in radians from
    the +x axis, y down), a soft halo outside it, and the disc itself a shade darker than the room."""
    x, y = _grid()
    dx, dy = (x - cx), (y - cy) * H / W
    d = np.sqrt(dx ** 2 + dy ** 2)
    ang = np.arctan2(dy, dx)
    on = ((ang >= start) & (ang <= end)).astype(float)
    # Fade the rim in and out along the arc so it never stops abruptly.
    span = end - start
    along = np.clip((ang - start) / span, 0, 1)
    taper = np.sin(along * np.pi) ** 0.8
    rim = np.exp(-((d - r) / width) ** 2) * on * taper
    halo = np.exp(-np.clip(d - r, 0, None) / (width * 9)) * (d > r) * on * taper * 0.35
    inner = np.exp(-np.clip(r - d, 0, None) / (width * 4)) * (d <= r) * on * taper * 0.25
    disc = (d <= r)[..., None]
    c[:] = np.where(disc, c * 0.55 + hex_rgb(fill) * 0.45, c)
    c += (rim + halo + inner)[..., None] * hex_rgb(color) * strength
    return c


def light_column(c, x0, width, color='#F0B060', top=0.25, bottom=0.62, strength=0.9):
    """A vertical slot of warm light (a lit doorway or pillar edge) with a soft spill around it."""
    x, y = _grid()
    across = np.exp(-((x - x0) / width) ** 2)
    spill = np.exp(-((x - x0) / (width * 8)) ** 2) * 0.18
    down = np.clip((y - top) / (bottom - top), 0, 1) ** 1.6 * (y <= bottom) + (y > bottom) * np.exp(-(y - bottom) / 0.02)
    c += ((across + spill) * down)[..., None] * hex_rgb(color) * strength
    return c


def stage_floor(c, edge=0.60, color='#2A1C12', sheen='#C88A4A', reflect=0.35):
    """A polished floor from `edge` down: warm dark wood, a thin lit lip at the edge, and a mirror of the room
    above it, blurred and fading, so lights pool on the floor."""
    hy = int(H * edge)
    span = H - hy
    src = c[max(0, hy - span):hy][::-1].copy()
    # Cheap vertical blur of the reflection.
    k = 9
    pad = np.pad(src, ((k, k), (0, 0), (0, 0)), mode='edge')
    blur = sum(pad[i:i + src.shape[0]] for i in range(2 * k + 1)) / (2 * k + 1)
    fade = np.linspace(reflect, 0.0, blur.shape[0])[:, None, None]
    base = hex_rgb(color) * np.linspace(1.0, 0.35, span)[:, None, None]
    c[hy:hy + blur.shape[0]] = base + blur * fade
    c[hy:hy + 2] += hex_rgb(sheen) * 0.15
    return c




def deco_layer(draw_fn, scale=4):
    """Crisp line art: draw_fn(draw, s) paints in white on a 4x RGBA canvas (s = pixel scale), which is
    downsampled to screen size, so hairlines come out sharp and anti-aliased. Returns an H x W alpha array 0..1."""
    from PIL import ImageDraw
    big = Image.new('L', (W * scale, H * scale), 0)
    draw_fn(ImageDraw.Draw(big), scale)
    small = big.resize((W, H), Image.LANCZOS)
    return np.asarray(small, dtype=np.float64) / 255.0


def ink(c, alpha, color, strength=1.0):
    """Add a deco_layer's lines to the canvas in one colour."""
    c += alpha[..., None] * hex_rgb(color) * strength
    return c


def velvet(c, strength=0.035, seed=5):
    """Fine vertical nap, like velvet or a pleated wall covering."""
    rng = np.random.default_rng(seed)
    cols = np.cumsum(rng.normal(0, 1, W))
    cols = (cols - np.convolve(cols, np.ones(41) / 41, mode='same'))
    cols = cols / (np.abs(cols).max() + 1e-6)
    c *= (1 + strength * cols)[None, :, None]
    return c
