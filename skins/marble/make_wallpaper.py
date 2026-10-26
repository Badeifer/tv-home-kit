import os, sys, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from wall import *
from PIL import ImageFilter
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wallpaper.jpg')

# Marble: black stone cracked with gold leaf, after a reference image. Veins are
# branching random walks, thick ones flecked like glitter; the stone is mottled, never flat; the lower
# half is darkened so the tiles stay readable.
rnd = random.Random(11)


def walk(d, s, x, y, ang, length, width, depth):
    step = 7
    for _ in range(int(length / step)):
        # Cracks run nearly straight, then kink sharply.
        ang += rnd.gauss(0, 0.035) + (rnd.choice((-1, 1)) * rnd.uniform(0.3, 0.8) if rnd.random() < 0.025 else 0)
        nx, ny = x + math.cos(ang) * step, y + math.sin(ang) * step
        w = max(1, int(width * s * rnd.uniform(0.6, 1.4)))
        d.line([x * s, y * s, nx * s, ny * s], fill=int(min(255, 150 + width * 25)), width=w)
        x, y = nx, ny
        if depth < 2 and rnd.random() < 0.012:
            walk(d, s, x, y, ang + rnd.choice((-1, 1)) * rnd.uniform(0.5, 1.2), length * rnd.uniform(0.2, 0.5),
                 max(0.6, width * 0.55), depth + 1)
        if not (-50 < x < W + 50 and -50 < y < H + 50):
            return


def veins(d, s):
    for _ in range(46):
        edge = rnd.random()
        x, y = rnd.uniform(-20, W + 20), rnd.uniform(-20, H + 20)
        ang = rnd.uniform(-0.9, 0.9) + (math.pi if rnd.random() < 0.5 else 0)
        walk(d, s, x, y, ang, rnd.uniform(500, 1600), rnd.choice((0.8, 1.0, 1.4, 2.2, 3.2)), 0)
    # A few main seams: long and thick, the gold pooled wide in them.
    for _ in range(4):
        x, y = rnd.uniform(-20, W * 0.5), rnd.uniform(0.05, 0.95) * H
        walk(d, s, x, y, rnd.uniform(-0.45, 0.35), rnd.uniform(1200, 2200), rnd.uniform(3.5, 5.0), 2)
    # Hairlines: many faint short cracks between the seams.
    for _ in range(60):
        walk(d, s, rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0, 2 * math.pi), rnd.uniform(80, 300), 0.5, 2)

def fbm(octaves=6, seed=2):
    r = np.random.default_rng(seed)
    out = np.zeros((H, W))
    for o in range(octaves):
        n = 2 ** (o + 2)
        g = r.random((n * 9 // 16 + 2, n + 2))
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        out += np.asarray(img, dtype=np.float64) / 255 / (2 ** o)
    return out / out.max()


c = canvas('#050505')
stone = fbm()
c += (stone ** 4)[..., None] * hex_rgb('#1A1815') * 0.8
v = deco_layer(veins, scale=2)
# Veins run evenly across the whole stone. Only right under lines of text are they softened a little, so the
# words stay readable: the clock and greeting, the app name, and the two rows of tile labels.
_y, _x = np.mgrid[0:H, 0:W]
_x, _y = _x / W, _y / H
def band(x0, x1, y0, y1, soft=0.02):
    return (np.clip((_x - x0) / soft, 0, 1) * np.clip((x1 - _x) / soft, 0, 1)
            * np.clip((_y - y0) / soft, 0, 1) * np.clip((y1 - _y) / soft, 0, 1))
text = np.maximum.reduce([band(0.03, 0.44, 0.04, 0.22), band(0.04, 0.24, 0.35, 0.47),
                          band(0.05, 0.95, 0.655, 0.715), band(0.05, 0.95, 0.875, 0.93)])
v = v * (1 - 0.6 * text)
glitter = np.random.default_rng(4).random((H, W))
sparkle = 0.55 + 0.45 * (glitter > 0.55) + 0.6 * (glitter > 0.97)
ink(c, v * sparkle, '#D8A93E', 0.75)   # toned down so the tiles and text lead
ink(c, np.asarray(Image.fromarray((v * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float64) / 255, '#8A6420', 0.3)
shade_bottom(c, 0.80, 0.30)
vignette(c, 0.35)
save(c, OUT, grain=0.008)
