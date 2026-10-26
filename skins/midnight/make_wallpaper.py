import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from wall import *
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wallpaper.jpg')
# Midnight: a mountain lake under a low moon, cold blue haze, very dark lower third for the dock.
c = canvas()
gradient(c, [(0, '#03050C'), (0.45, '#0B1630'), (0.62, '#1A2A4A'), (1, '#02040A')])
stars(c, n=700, seed=3, top=0.55, brightness=0.8)
glow(c, 0.74, 0.30, 0.30, '#3D6BB3', 0.30)
glow(c, 0.74, 0.30, 0.035, '#E8EEFF', 1.6)
glow(c, 0.74, 0.30, 0.012, '#FFFFFF', 2.5)
ridge(c, '#0E1A33', 0.52, 0.22, seed=11, haze='#22355A')
ridge(c, '#08101F', 0.58, 0.16, seed=5, haze='#16243F')
ridge(c, '#040811', 0.63, 0.10, seed=8)
water_reflection(c, 0.66, strength=0.5, color='#02040A')
shade_bottom(c, 0.62, 0.75)
vignette(c, 0.5)
save(c, OUT)

