import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from wall import *
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wallpaper.jpg')
# Synthwave: striped sunset sun over a neon floor grid, magenta and cyan on near-black.
c = canvas()
gradient(c, [(0, '#05010D'), (0.35, '#1A0630'), (0.60, '#4A0D4F'), (0.62, '#0A0214'), (1, '#030008')])
stars(c, n=380, seed=7, top=0.5, brightness=0.6)
retro_sun(c, cx=0.66, cy=0.47, r=0.15, top='#FFE07A', bottom='#FF2E88')
ridge(c, '#12052A', 0.585, 0.10, seed=21, roughness=0.45, octaves=5, haze='#3A0E5E')
perspective_grid(c, horizon=0.62, color='#FF3EC8', spacing=0.07, lines=30, strength=0.75)
glow(c, 0.10, 0.95, 0.35, '#00E5FF', 0.12)
shade_bottom(c, 0.70, 0.55)
vignette(c, 0.45)
save(c, OUT)
