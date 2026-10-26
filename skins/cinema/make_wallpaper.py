import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from wall import *
from PIL import ImageFilter
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wallpaper.jpg')

# Cinema, from a reference image. Warm black. A bright arc glows in the lower right; around
# it, fine gold rings widen up to the top edge, rows of dots ride the rings just above it, and a bundle of
# lines flows in from behind the greeting, joins the rings and runs out along the horizon to the right.
AX, AY = 0.735, 0.585          # centre shared by the arc and its rings, 0..1 of width / height
ARX, ARY = 0.148, 0.300        # the bright arc's radii (its crown sits near y = 0.285)


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def seg(d, s, a, b, v, w=1.1):
    if v > 2:
        d.line([a[0] * W * s, a[1] * H * s, b[0] * W * s, b[1] * H * s], fill=int(min(v, 255)), width=max(1, int(w * s)))


def ring_pts(k, a0=math.radians(192), a1=math.radians(352), n=360):
    return [(AX + ARX * k * math.cos(a0 + (a1 - a0) * i / n), AY + ARY * k * math.sin(a0 + (a1 - a0) * i / n), i / n)
            for i in range(n + 1)]


def rings(d, s):
    # Concentric rings, spacing widening outward; each fades at its feet and with distance from the arc.
    ks = [1.0 + 0.10 * j + 0.01 * j * j for j in range(1, 7)]
    for j, k in enumerate(ks):
        base = 140 * math.exp(-j / 3.0)
        pts = ring_pts(k, math.radians(205), math.radians(345))
        for (x0, y0, t0), (x1, y1, t1) in zip(pts, pts[1:]):
            t = (t0 + t1) / 2
            seg(d, s, (x0, y0), (x1, y1), base * math.sin(math.pi * t) ** 0.5)


def flow(d, s):
    # Lines from behind the greeting: they dip, rise to meet the rings' left side, and follow the
    # horizon under the arc to the right edge.
    for i in range(26):
        pts = []
        for k in range(0, 401):
            x = 0.26 + k / 400 * 0.80
            u = smooth((x - 0.30) / 0.30)                  # entry curve, from high left down to the horizon
            y_entry = 0.20 + i * 0.010
            y_hor = 0.470 + i * 0.0042 + 0.012 * math.sin(x * 9 + i * 0.3)
            y = y_entry * (1 - u) + y_hor * u + 0.035 * math.sin(math.pi * u) * (1 - i / 30)
            pts.append((x, y))
        fade = lambda x: smooth((x - 0.27) / 0.16) * smooth((1.06 - x) / 0.10)
        for a, b in zip(pts, pts[1:]):
            seg(d, s, a, b, (120 - i * 3.2) * fade((a[0] + b[0]) / 2))


def fan(d, s):
    # The sweep: lines rising from beside the arc's left foot, fanning out to the top edge.
    for i in range(24):
        p0 = (0.42 + i * 0.0035, 0.47 - i * 0.002)
        p1 = (0.57 + i * 0.006, 0.36 - i * 0.004)
        p2 = (0.58 + i * 0.015, -0.03)
        prev = None
        for k in range(0, 301):
            t = k / 300
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            if prev:
                seg(d, s, prev, (x, y), (150 - i * 4) * smooth(t / 0.25) * smooth((1.05 - t) / 0.3))
            prev = (x, y)


def arc(d, s):
    pts = ring_pts(1.0, math.radians(186), math.radians(354), 480)
    for (x0, y0, t0), (x1, y1, t1) in zip(pts, pts[1:]):
        t = (t0 + t1) / 2
        seg(d, s, (x0, y0), (x1, y1), 255 * math.sin(math.pi * t) ** 0.45, w=2.4)


def dots(d, s):
    # Rows of dots riding the rings just outside the arc, densest at the crown, thinning outward and at the sides.
    for j in range(9):
        k = 1.07 + 0.045 * j
        n = int(150 + 22 * j)
        for i in range(n + 1):
            a = math.radians(200 + 140 * i / n)
            t = i / n
            x, y = AX + ARX * k * math.cos(a), AY + ARY * k * math.sin(a)
            v = 210 * math.exp(-j / 4.5) * math.sin(math.pi * t) ** 1.4
            if v < 12:
                continue
            r = (1.15 - 0.05 * j) * s
            d.ellipse([x * W * s - r, y * H * s - r, x * W * s + r, y * H * s + r], fill=int(v))


def bloom(layer, radius):
    return np.asarray(Image.fromarray((np.clip(layer, 0, 1) * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(radius)), dtype=np.float64) / 255


c = canvas()
gradient(c, [(0, '#0C0806'), (0.40, '#120C08'), (0.62, '#0D0906'), (1, '#060403')])
glow(c, 0.74, 0.34, 0.34, '#4A2A10', 0.75)       # the room's warm haze
glow(c, 0.64, 0.36, 0.12, '#B06A28', 0.45)       # hot spot at the arc's upper left
glow(c, AX, AY - 0.05, 0.16, '#3A2010', 0.25)    # light inside the arc

r_lines, f_lines = deco_layer(rings), deco_layer(flow) * 0.8 + deco_layer(fan)
ink(c, r_lines, '#D9A15C', 0.75)
ink(c, f_lines, '#D9A15C', 0.70)
ink(c, bloom(r_lines + f_lines, 3), '#B87430', 0.6)
dl = deco_layer(dots)
ink(c, dl, '#F0BC7A', 1.5)
a = deco_layer(arc)
ink(c, a, '#FFE2B0', 1.2)
for radius, amt in ((3, 1.6), (10, 1.4), (28, 1.1), (70, 0.8)):
    ink(c, bloom(a, radius), '#F0A050', amt)

shade_bottom(c, 0.60, 0.80)
vignette(c, 0.30)
save(c, OUT, grain=0.006)
