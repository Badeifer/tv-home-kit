import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from wall import *
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wallpaper.jpg')
# Aurora: green and violet curtains over a dark range, mirrored in a still lake.
c = canvas()
gradient(c, [(0, '#020611'), (0.5, '#061A2B'), (0.62, '#0B2436'), (1, '#01040A')])
stars(c, n=1100, seed=2, top=0.6, brightness=0.9)
aurora(c, colors=('#38FFC1', '#7A4DFF'), base=0.47, height=0.36, waves=3, seed=6, strength=1.1)
aurora(c, colors=('#2BD9FF', '#C04DFF'), base=0.36, height=0.22, waves=2, seed=13, strength=0.30)
ridge(c, '#07131F', 0.55, 0.20, seed=4, haze='#0C2233')
ridge(c, '#030A12', 0.61, 0.10, seed=9)
water_reflection(c, 0.64, strength=0.55, color='#01040A')
shade_bottom(c, 0.64, 0.7)
vignette(c, 0.45)
save(c, OUT)

