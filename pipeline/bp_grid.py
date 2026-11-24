"""Overlay a metric grid on a blueprint view for reading coordinates.
usage: bp_grid.py img out x0 y0 x1 y1 scale_px_m origin_x origin_y axis_u(+1/-1) zoom"""
import sys
from PIL import Image, ImageDraw
img, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7])
s, ox, oy, au, Z = float(sys.argv[7]), float(sys.argv[8]), float(sys.argv[9]), int(sys.argv[10]), int(sys.argv[11])
im = Image.open(img).convert("RGB").crop((x0, y0, x1, y1))
im = im.resize((im.width * Z, im.height * Z), Image.NEAREST)
d = ImageDraw.Draw(im)
def px(u, v):  # metres -> zoomed px
    return ((ox + au * u * s - x0) * Z, (oy - v * s - y0) * Z)
import math
for i in range(-40, 41):
    u = i / 10
    X, _ = px(u, 0)
    if 0 <= X < im.width:
        c = (255, 0, 0) if i % 5 == 0 else (255, 170, 170)
        d.line([(X, 0), (X, im.height)], fill=c, width=1)
        if i % 5 == 0: d.text((X + 2, 2), f"{u:.1f}", fill=(200, 0, 0))
for j in range(-20, 25):
    v = j / 10
    _, Y = px(0, v)
    if 0 <= Y < im.height:
        c = (0, 0, 255) if j % 5 == 0 else (170, 170, 255)
        d.line([(0, Y), (im.width, Y)], fill=c, width=1)
        d.text((2, Y + 1), f"{v:.1f}", fill=(0, 0, 200))
im.save(out)
