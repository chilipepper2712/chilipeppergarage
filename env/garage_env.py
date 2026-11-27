"""Low-poly pixel-texture garage (reference: old brick workshop with mezzanine).

Same rules as the cars: metres, Z up, 64 px/m texel density. Textures are small tileable
pixel tiles (palette + Bayer dither); every face gets world-metre UVs so the density holds
everywhere. Output: out/env/garage.glb (one object per material; EMIT_* = unlit).

Car sits at the origin. Room: x -5.5..5.5, y -7 (open side, camera) .. +6 (back wall).
"""
import os, sys, math
import numpy as np
import bpy, bmesh
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "env"); os.makedirs(OUT, exist_ok=True)
TEX_DIR = os.path.join(OUT, "tex"); os.makedirs(TEX_DIR, exist_ok=True)
PX = 64
RNG = np.random.default_rng(7)
BAY = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + .5) / 16

W, Y0, Y1 = 5.5, -7.0, 6.0          # half width, open side, back wall
EAVE, RIDGE = 4.4, 6.0
MZ_Y, MZ_Z, MZ_X0, MZ_X1 = 3.0, 2.7, -3.2, 4.2   # mezzanine front edge, deck top, x range


# ------------------------------------------------------------------ textures
def hx(h): return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def shade(ramp, lum, spread=0.6):
    """lum (H,W) 0..1 -> RGB via ordered dither on a colour ramp."""
    H, Wd = lum.shape
    r = np.array([hx(c) for c in ramp], np.uint8)
    b = np.tile(BAY, (H // 4 + 1, Wd // 4 + 1))[:H, :Wd]
    i = np.clip(np.round(np.clip(lum, 0, 1) * (len(r) - 1) + (b - .5) * spread), 0, len(r) - 1).astype(int)
    return r[i]


def noise(n, amp=0.12):
    return (RNG.random((n, n)) - .5) * amp


def blobs(n, k, rad, amp):
    """soft tileable stains"""
    yy, xx = np.mgrid[0:n, 0:n]
    out = np.zeros((n, n))
    for _ in range(k):
        cx, cy, r = RNG.random() * n, RNG.random() * n, rad * (0.5 + RNG.random())
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                d = np.hypot(xx - cx - ox, yy - cy - oy)
                out += np.clip(1 - d / r, 0, 1) * amp
    return out


def t_floor():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    tile = (xx // 32) + 2 * (yy // 32)
    base = 0.55 + np.array([0.04, -0.03, 0.0, 0.06])[tile] + noise(n, .18) - blobs(n, 3, 14, .12)
    img = shade(["#3f3a33", "#544d43", "#6a6256", "#81786a", "#988e7e"], base)
    grout = (xx % 32 == 0) | (yy % 32 == 0)
    img[grout] = hx("#2a2621")
    return img


def t_brick():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    row = yy // 5; off = (row % 2) * 8
    bid = ((xx + off) // 16) + row * 7
    lum = 0.55 + ((bid * 37 % 11) / 11 - .5) * .25 + noise(n, .15) - blobs(n, 2, 12, .1)
    img = shade(["#5e554b", "#746a5e", "#8a8072", "#a09685", "#b4ab99"], lum)
    mortar = (yy % 5 == 4) | ((xx + off) % 16 == 15)
    img[mortar] = hx("#4a433b")
    return img


def t_plaster(dark=False):
    n = 64
    lum = 0.6 + noise(n, .14) - blobs(n, 4, 16, .14)
    ramp = ["#4a3e31", "#5c4e3e", "#6f604c", "#827159"] if dark else \
        ["#6f6150", "#85765f", "#9a8a70", "#ad9d82", "#beb093"]
    img = shade(ramp, lum)
    if not dark:                                   # hairline cracks
        for _ in range(2):
            x, y = RNG.integers(0, n, 2)
            for _ in range(40):
                img[y % n, x % n] = hx("#4f4436")
                x += RNG.integers(-1, 2); y += 1
    return img


def t_wood(dark=False):
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    plank = yy // 10
    lum = 0.5 + ((plank * 29 % 7) / 7 - .5) * .3 + np.sin(xx / 3.0 + plank * 2.1) * .06 + noise(n, .12)
    ramp = ["#22170e", "#302113", "#402c19", "#523921"] if dark else ["#3a2616", "#52361f", "#6b4729", "#855a34"]
    img = shade(ramp, lum)
    img[yy % 10 == 9] = hx("#1a110a")
    return img


def t_metal_roof():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    lum = 0.45 + np.where(xx % 6 < 3, .15, -.1) + noise(n, .1) - blobs(n, 2, 18, .1)
    return shade(["#181a1c", "#24272a", "#31353a", "#40454b"], lum)


def t_steel():
    n = 64
    lum = 0.5 + noise(n, .2) - blobs(n, 3, 10, .12)
    return shade(["#1b1d20", "#26292d", "#33373c", "#43484e", "#575d64"], lum)


def t_window():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    pane = (xx // 16) + (yy // 16) * 4
    lum = 0.75 + ((pane * 13 % 5) / 5 - .5) * .3 - blobs(n, 3, 12, .2) + noise(n, .1)
    img = shade(["#8f978f", "#b3bbb2", "#d4dbd1", "#eef2ea", "#ffffff"], lum)
    img[(xx % 16 < 1) | (yy % 16 < 1)] = hx("#2a2a28")
    return img


def t_pegboard():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#6d5236", "#82633f", "#977449"], 0.55 + noise(n, .15))
    img[(xx % 4 == 1) & (yy % 4 == 1)] = hx("#3a2a1a")
    # tool silhouettes: spanners and a hammer
    for i, x0 in enumerate((6, 18, 30)):
        img[10:34 - i * 4, x0:x0 + 2] = hx("#8d939a"); img[8:12, x0 - 1:x0 + 3] = hx("#b4bac1")
    img[12:16, 44:58] = hx("#5a5f66"); img[16:34, 50:52] = hx("#6b4729")
    img[40:44, 8:40] = hx("#a3191a")                       # red level
    return img


def t_pegwhite():
    """white painted pegboard: 25 mm hole pitch at 64 px/m -> a hole every 2 px would alias; 4 px (~6 cm)"""
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#b9bcbf", "#cdd0d2", "#dcdfe1"], 0.6 + noise(n, .08))
    img[(xx % 4 == 1) & (yy % 4 == 1)] = hx("#55595e")
    return img


def t_dynoplate():
    """blue powder-coated diamond plate"""
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#1a3a9e", "#2149bf", "#2b58d6"], 0.6 + noise(n, .06))
    a = ((xx + yy) % 8 < 2) & ((yy // 4) % 2 == 0); b = ((xx - yy) % 8 < 2) & ((yy // 4) % 2 == 1)
    img[a | b] = hx("#4f7cf0")
    return img


def t_hazard():
    """yellow / black diagonal safety stripes"""
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#c99a17", "#e3b52a"], 0.6 + noise(n, .06))
    img[((xx + yy) // 8) % 2 == 1] = hx("#16161a")
    return img


def t_leather():
    """cognac leather with soft pleat seams"""
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#8e4a18", "#a65a1f", "#b96a26", "#c97a2e"], 0.55 + noise(n, .06))
    img[(xx % 8 == 0)] = hx("#7d4116")                    # seam: one step darker, every ~12 cm
    return img


def t_crate():
    """red plastic soda crate: rails with dark bottle openings"""
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#8f1010", "#b71a17", "#d7271f"], 0.6 + noise(n, .08))
    hole = ((xx % 8) >= 2) & ((xx % 8) <= 6) & ((yy % 16) >= 5) & ((yy % 16) <= 12)
    img[hole] = hx("#3a0707")
    return img


def t_wiremesh():
    """black perforated steel sheet"""
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#141416", "#1f1f24", "#2b2b31"], 0.55 + noise(n, .1))
    img[((xx + (yy // 2 % 2)) % 2 == 0) & (yy % 2 == 0)] = hx("#4a4b52")
    return img


def t_simple(ramp, stripe=None, stripe_col=None, rows=False):
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(ramp, 0.55 + noise(n, .16) - blobs(n, 2, 12, .1))
    if stripe is not None:
        a, b = stripe
        img[(yy >= a) & (yy < b)] = shade(stripe_col, 0.55 + noise(n, .14))[(yy >= a) & (yy < b)]
    return img


def t_grate():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#1c1e20", "#2b2e31", "#3c4044"], 0.5 + noise(n, .2))
    img[(xx % 5 < 2)] = hx("#0b0c0d")
    return img


def t_puddle():
    n = 64
    lum = 0.35 + noise(n, .2)
    img = shade(["#26231e", "#332f28", "#423d34", "#7d776b"], lum, spread=0.9)
    return img


def t_emit(col):
    return np.tile(np.array(hx(col), np.uint8), (8, 8, 1))


def t_yellow():
    n = 64
    img = shade(["#6e5208", "#9c760d", "#c99a17", "#e3b52a"], 0.6 + noise(n, .18) - blobs(n, 3, 10, .14))
    yy, xx = np.mgrid[0:n, 0:n]
    scuff = RNG.random((n, n)) < 0.035                      # chipped paint
    img[scuff] = hx("#2a2722")
    return img


def neon(lines, w_m, h_m, tube, core, halo, font_px, draw_extra=None, density=64):
    """Neon sign texture: single-stroke tubes (thin font) + hot core + 1px halo, on black."""
    from PIL import ImageDraw, ImageFont, ImageFilter
    W, H = int(w_m * density), int(h_m * density)
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    if lines:
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", font_px)
        hs = [d.textbbox((0, 0), t, font=f) for t in lines]
        total = sum(b[3] - b[1] for b in hs) + (len(lines) - 1) * font_px * 0.35
        y = (H - total) / 2
        for t, b in zip(lines, hs):
            d.text(((W - (b[2] - b[0])) / 2 - b[0], y - b[1]), t, font=f, fill=255)
            y += (b[3] - b[1]) + font_px * 0.35
    if draw_extra:
        draw_extra(d, W, H)
    a = np.array(m) > 110                                   # crisp pixel tubes
    core_m = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))) > 0
    halo_m = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    img = np.zeros((H, W, 3), np.uint8)
    img[halo_m] = hx(halo); img[a] = hx(tube); img[core_m] = hx(core)
    return img


def chili(d, W, H):
    """purple outline of a chili pepper: bent pod tapering to a tip + calyx + curled stem"""
    P0, P1, P2 = np.array([.34, .30]), np.array([.40, .86]), np.array([.86, .84])
    L, R = [], []
    for i in range(29):
        t = i / 28
        p = (1 - t) ** 2 * P0 + 2 * (1 - t) * t * P1 + t * t * P2
        dp = 2 * (1 - t) * (P1 - P0) + 2 * t * (P2 - P1)
        n = np.array([-dp[1], dp[0]]) / np.linalg.norm(dp)
        r = .13 * (1 - t) ** 0.75 + .006
        L.append(tuple((p + n * r) * [W, H])); R.append(tuple((p - n * r) * [W, H]))
    d.line(L + R[::-1] + [L[0]], fill=255, width=2, joint="curve")
    cx, cy = P0 * [W, H]
    d.line([(cx - W * .15, cy - H * .02), (cx - W * .05, cy - H * .07), (cx + W * .05, cy - H * .07),
            (cx + W * .15, cy - H * .02)], fill=255, width=2, joint="curve")               # calyx
    d.line([(cx, cy - H * .07), (cx - W * .02, cy - H * .16), (cx + W * .04, cy - H * .23),
            (cx + W * .12, cy - H * .24)], fill=255, width=2, joint="curve")                # stem


def t_epoxy():
    n = 64
    lum = 0.45 + noise(n, .08) - blobs(n, 3, 11, .16)          # oil stains
    img = shade(["#1f2324", "#2a2f30", "#363c3d", "#454c4d"], lum, spread=0.4)
    fleck = RNG.random((n, n)) < 0.02
    img[fleck] = hx("#5d6566")
    return img


TEXTURES = {
    "floor": t_floor, "brick": t_brick, "plaster": t_plaster, "plaster_low": lambda: t_plaster(True),
    "wood": t_wood, "beam": lambda: t_wood(True), "roof": t_metal_roof, "steel": t_steel,
    "window": t_window, "pegboard": t_pegboard, "pegwhite": t_pegwhite, "grate": t_grate, "puddle": t_puddle,
    "cardboard": lambda: t_simple(["#5d452c", "#765838", "#8f6c46"], (28, 33), ["#b8a77f", "#cfc09a"]),
    "barrel_o": lambda: t_simple(["#7a350c", "#a54d15", "#cc6b22", "#e08a3c"], (20, 34), ["#1c2a40", "#284062", "#35557f"]),
    "barrel_b": lambda: t_simple(["#16233a", "#223656", "#2e4a74"], (24, 32), ["#a54d15", "#cc6b22"]),
    "bucket": lambda: t_simple(["#8c908e", "#adb1ae", "#cdd1cd", "#e6e9e6"]),
    "rubber": lambda: t_simple(["#121212", "#1b1b1b", "#262626"]),
    "red": lambda: t_simple(["#5e0b0b", "#8a1414", "#b52222", "#d63a3a"]),
    "ladder": lambda: t_simple(["#7a3f10", "#a85a1b", "#d27a2c"]),
    "paper": lambda: t_simple(["#a9a493", "#c4bfad", "#dcd7c6"]),
    "EMIT_lamp": lambda: t_emit("#fff1c4"), "EMIT_strip": lambda: t_emit("#ffd994"),
    "EMIT_window": t_window,
    "dynoplate": t_dynoplate, "dynoblue": lambda: t_simple(["#1b3fb0", "#2350d0", "#2f62e8"]), "hazard": t_hazard,
    "console": lambda: t_simple(["#8d9298", "#a7acb2", "#bfc3c8"]),
    "EMIT_dynoA": lambda: t_emit("#0c1a2a"), "EMIT_dynoB": lambda: t_emit("#0c1a2a"),
    "leather": t_leather, "crate": t_crate, "wiremesh": t_wiremesh,
    "blacksteel": lambda: t_simple(["#141416", "#1c1c20", "#26262b"]),
    "yellow": t_yellow, "epoxy": t_epoxy, "neon_back": lambda: t_simple(["#121214", "#18181b", "#1f1f23"]),
    "EMIT_work": lambda: t_emit("#fff6e4"),
    "EMIT_neon_red": lambda: neon(["CHILI PEPPER", "GARAGE"], 1.95, 0.825, "#ff2a1f", "#ffd2c4", "#4a0805", 18),
    "EMIT_neon_purple": lambda: neon([], 1.0, 1.0, "#b13cff", "#f0d2ff", "#2c0848", 1, chili),
}


# ------------------------------------------------------------------ geometry
class Builder:
    def __init__(self):
        self.bms = {}
        self.fixed = {}          # faces with hand-set UVs (signs), skipped by world_uvs

    def bm(self, mat):
        if mat not in self.bms:
            b = bmesh.new(); b.loops.layers.uv.new("UV1_atlas"); self.bms[mat] = b
        return self.bms[mat]

    def quad(self, mat, pts, flip=False):
        b = self.bm(mat)
        vs = [b.verts.new(p) for p in (pts[::-1] if flip else pts)]
        return b.faces.new(vs)

    def quad_uv(self, mat, pts, uvs):
        f = self.quad(mat, pts)
        self.fixed.setdefault(mat, []).append((f, uvs))
        return f

    def box(self, mat, lo, hi, skip=()):
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        F = {
            "-x": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            "+x": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "+y": [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)],
            "-z": [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
            "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        }
        for k, p in F.items():
            if k not in skip:
                self.quad(mat, p)

    def beam(self, mat, a, b, w, h=None):
        """box between two points (any direction) with square-ish section w x h"""
        a, b = np.array(a, float), np.array(b, float)
        d = b - a; L = np.linalg.norm(d); d /= L
        up = np.array([0, 0, 1.0]) if abs(d[2]) < .9 else np.array([1.0, 0, 0])
        s = np.cross(d, up); s /= np.linalg.norm(s); u = np.cross(s, d)
        h = h or w
        ring = lambda c: [c + s * w / 2 + u * h / 2, c - s * w / 2 + u * h / 2,
                          c - s * w / 2 - u * h / 2, c + s * w / 2 - u * h / 2]
        r0, r1 = ring(a), ring(b)
        self.quad(mat, [tuple(p) for p in r0[::-1]])
        self.quad(mat, [tuple(p) for p in r1])
        for i in range(4):
            j = (i + 1) % 4
            self.quad(mat, [tuple(r0[i]), tuple(r0[j]), tuple(r1[j]), tuple(r1[i])])

    def cyl(self, mat, c, r, h, seg=8, axis="z", caps=True):
        cx, cy, cz = c
        def P(a, t):
            ca, sa = r * math.cos(a), r * math.sin(a)
            if axis == "z": return (cx + ca, cy + sa, cz + t)
            if axis == "y": return (cx + ca, cy + t, cz + sa)
            return (cx + t, cy + ca, cz + sa)
        A = [2 * math.pi * i / seg for i in range(seg)]
        for i in range(seg):
            j = (i + 1) % seg
            self.quad(mat, [P(A[i], 0), P(A[j], 0), P(A[j], h), P(A[i], h)])
        if caps:
            self.quad(mat, [P(a, h) for a in A])
            self.quad(mat, [P(a, 0) for a in A[::-1]])


def world_uvs(b, cyl_like=False):
    uvl = b.loops.layers.uv.active
    for f in b.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co
            if ax == 2: u, v = co.x, co.y
            elif ax == 0: u, v = co.y * (1 if n.x > 0 else -1), co.z
            else: u, v = co.x * (-1 if n.y > 0 else 1), co.z
            l[uvl].uv = (u, v)          # 1 UV unit = 1 m = one 64 px tile


def build():
    B = Builder()
    # floor + puddles + drain
    B.quad("floor", [(-W, Y0, 0), (W, Y0, 0), (W, Y1, 0), (-W, Y1, 0)])
    B.quad("grate", [(0.2, 1.7, .004), (1.0, 1.7, .004), (1.0, 2.2, .004), (0.2, 2.2, .004)])
    # service bay: epoxy-coated slab between the bay lines (glossy, oil-stained), no standing water
    BX = 0.5                                     # bay centre x: one floor tile toward the pegboard
    B.quad("epoxy", [(BX - 1.45, -2.9, .002), (BX + 1.45, -2.9, .002), (BX + 1.45, 2.3, .002), (BX - 1.45, 2.3, .002)])
    # walls (normals inward so the room reads from inside; backface culling opens the dollhouse)
    B.quad("plaster_low", [(-W, Y0, 0), (-W, Y1, 0), (-W, Y1, 1.2), (-W, Y0, 1.2)])
    B.quad("plaster_low", [(W, Y0, 0), (W, Y0, 1.2), (W, Y1, 1.2), (W, Y1, 0)])
    # left wall with a high window band
    win_l = (-2.0, 2.4, 2.8, 4.1)              # y0, y1, z0, z1
    def wall_with_window(x, win, flip):
        y0w, y1w, z0w, z1w = win
        segs = [(Y0, y0w, 1.2, EAVE), (y1w, Y1, 1.2, EAVE), (y0w, y1w, 1.2, z0w), (y0w, y1w, z1w, EAVE)]
        for a, b_, z0, z1 in segs:
            B.quad("plaster", [(x, a, z0), (x, a, z1), (x, b_, z1), (x, b_, z0)], flip=flip)
        B.quad("EMIT_window", [(x, y0w, z0w), (x, y0w, z1w), (x, y1w, z1w), (x, y1w, z0w)], flip=flip)
        for z in (z0w - .06, z1w):           # sill + lintel
            B.box("steel", (x - .08 if x > 0 else x, y0w - .06, z), (x if x > 0 else x + .08, y1w + .06, z + .06))
    wall_with_window(-W, win_l, True)
    wall_with_window(W, (-3.4, 1.6, 2.4, 4.1), False)
    # back wall: brick, gable to the ridge
    B.quad("brick", [(-W, Y1, 0), (-W, Y1, EAVE), (W, Y1, EAVE), (W, Y1, 0)], flip=True)
    B.quad("brick", [(-W, Y1, EAVE), (0, Y1, RIDGE), (W, Y1, EAVE)], flip=True)
    # roof
    B.quad("roof", [(-W, Y0, EAVE), (0, Y0, RIDGE), (0, Y1, RIDGE), (-W, Y1, EAVE)], flip=True)
    B.quad("roof", [(W, Y0, EAVE), (W, Y1, EAVE), (0, Y1, RIDGE), (0, Y0, RIDGE)], flip=True)
    # trusses: rafters + tie beam every 2.6 m, ridge beam
    for y in np.arange(Y1 - 0.4, Y0, -2.6):
        B.beam("beam", (-W, y, EAVE - .05), (0, y, RIDGE - .12), .16, .22)
        B.beam("beam", (W, y, EAVE - .05), (0, y, RIDGE - .12), .16, .22)
        B.beam("beam", (-W, y, EAVE - .1), (W, y, EAVE - .1), .14, .18)
    B.beam("beam", (0, Y0, RIDGE - .2), (0, Y1, RIDGE - .2), .18, .2)
    # pipes: run along the right wall, a down-pipe on the left
    B.cyl("bucket", (W - .15, Y0, 3.25), .07, Y1 - Y0, 8, axis="y", caps=False)
    B.cyl("bucket", (W - .15, -4.0, 0.0), .07, 3.3, 8, axis="z", caps=False)
    B.cyl("steel", (-W + .12, -5.6, 0.0), .05, EAVE, 6, axis="z", caps=False)

    # mezzanine deck, steel edge beam, posts, railing
    B.box("wood", (MZ_X0, MZ_Y, MZ_Z - .06), (MZ_X1, Y1, MZ_Z))
    B.box("steel", (MZ_X0, MZ_Y, MZ_Z - .3), (MZ_X1, MZ_Y + .12, MZ_Z - .06))
    B.box("steel", (MZ_X0, MZ_Y, MZ_Z - .3), (MZ_X0 + .12, Y1, MZ_Z - .06))
    for x in (MZ_X0, 0.5, MZ_X1 - .12):
        B.box("steel", (x, MZ_Y, 0), (x + .12, MZ_Y + .12, MZ_Z - .3))
    for x in np.linspace(MZ_X0 + 1.0, MZ_X1, 6):
        B.box("steel", (x - .03, MZ_Y, MZ_Z), (x + .03, MZ_Y + .05, MZ_Z + 1.0))
    B.box("steel", (MZ_X0 + 1.0, MZ_Y, MZ_Z + .95), (MZ_X1, MZ_Y + .06, MZ_Z + 1.02))
    B.box("steel", (MZ_X0 + 1.0, MZ_Y, MZ_Z + .5), (MZ_X1, MZ_Y + .04, MZ_Z + .54))
    # stairs on the left, rising toward the back
    n, run, rise = 13, 0.25, MZ_Z / 13
    sx0, sx1 = MZ_X0 - .9, MZ_X0 - .05
    for i in range(n):
        y = MZ_Y - (n - i) * run
        B.box("steel", (sx0, y, (i + 1) * rise - .04), (sx1, y + run, (i + 1) * rise))
    for x in (sx0 - .05, sx1):
        B.beam("steel", (x + .025, MZ_Y - n * run - .1, 0.08), (x + .025, MZ_Y + .05, MZ_Z), .05, .22)
        B.beam("steel", (x + .025, MZ_Y - n * run, 1.0), (x + .025, MZ_Y, MZ_Z + 1.0), .04, .04)
        for k in range(0, n + 1, 4):
            y = MZ_Y - (n - k) * run
            B.box("steel", (x, y, k * rise), (x + .04, y + .04, k * rise + 1.0))
    # stuff on the mezzanine
    B.box("cardboard", (1.0, 4.8, MZ_Z), (2.0, 5.6, MZ_Z + .5))
    B.box("paper", (-1.0, 4.6, MZ_Z), (0.4, 5.5, MZ_Z + .35))
    B.cyl("barrel_o", (-2.2, 5.3, MZ_Z), .3, .9, 10)

    # workshop under the mezzanine: light strip, pegboard, benches, stool, gas bottle
    B.box("EMIT_strip", (-1.8, 4.2, MZ_Z - .36), (2.4, 4.32, MZ_Z - .3))
    B.quad("pegboard", [(-1.6, Y1 - .02, 1.05), (2.4, Y1 - .02, 1.05), (2.4, Y1 - .02, 2.2), (-1.6, Y1 - .02, 2.2)])
    for x0, x1 in ((-1.5, 0.6), (0.9, 2.3)):
        B.box("wood", (x0, 5.3, .86), (x1, 5.95, .92))
        for x in (x0 + .05, x1 - .1):
            for y in (5.32, 5.85):
                B.box("steel", (x, y, 0), (x + .05, y + .05, .86))
        B.box("wood", (x0 + .05, 5.32, .18), (x1 - .05, 5.9, .22))
    B.box("steel", (-0.2, 5.4, .92), (0.3, 5.7, 1.05))              # vice / toolbox
    B.box("red", (1.2, 5.5, .92), (1.7, 5.8, 1.15))
    B.cyl("wood", (0.0, 4.6, 0), .16, .55, 6)                         # stool
    B.cyl("red", (2.8, 5.55, 0), .16, 1.1, 8)                         # gas bottle
    B.cyl("steel", (2.8, 5.55, 1.1), .05, .12, 6)

    # right side: the mod wall. One long white pegboard (no seams) centred under the window band
    # (window y -3.4..1.6, z 2.4..4.1) so the daylight still comes in; ladder and the tyre stack moved to
    # the far end. Board spans y -3.6..1.8, z 0.3..2.34.
    PB = (W - .02, -3.6, 1.8, 0.3, 2.34)                 # x, y0, y1, z0, z1 (anchors -> viewer)
    B.quad("pegwhite", [(PB[0], PB[1], PB[3]), (PB[0], PB[1], PB[4]), (PB[0], PB[2], PB[4]), (PB[0], PB[2], PB[3])])
    for (lo, hi) in (((PB[1] - .05, PB[3] - .05), (PB[2] + .05, PB[3])), ((PB[1] - .05, PB[4]), (PB[2] + .05, PB[4] + .05)),
                     ((PB[1] - .05, PB[3]), (PB[1], PB[4])), ((PB[2], PB[3]), (PB[2] + .05, PB[4]))):
        B.box("steel", (W - .06, lo[0], lo[1]), (W, hi[0], hi[1]))
    B.peg = {"pegboard": (PB[0], (PB[1] + PB[2]) / 2, (PB[3] + PB[4]) / 2), "pegboard_size": (PB[2] - PB[1], PB[4] - PB[3], 0)}
    # the dyno has its own room now (env/dyno_env.py); the front-left corner is free floor

    # lounge in front of the board: a soda-crate table with a wooden top, two black wire-mesh side chairs
    # soda-crate table: red crate on four tapered wooden legs, wooden top
    tx, ty = W - 1.5, -0.9
    for dx in (-.17, .17):
        for dy in (-.24, .24):
            B.beam("wood", (tx + dx * 1.1, ty + dy * 1.08, 0), (tx + dx, ty + dy, .14), .045)
    B.box("crate", (tx - .2, ty - .28, .14), (tx + .2, ty + .28, .46))
    B.box("wood", (tx - .25, ty - .34, .46), (tx + .25, ty + .34, .49))
    # wire-mesh side chairs facing the table
    def chair(cx, cy, face):                                         # face = +1 looks toward +y, -1 toward -y
        f = face
        for dx in (-.24, .24):
            B.beam("blacksteel", (cx + dx, cy - f * .24, 0), (cx + dx * .95, cy + f * .02, .38), .02)   # back legs
            B.beam("blacksteel", (cx + dx, cy + f * .26, 0), (cx + dx * .95, cy + f * .2, .38), .02)    # front legs
        B.quad("wiremesh", [(cx - .25, cy + f * .24, .4), (cx + .25, cy + f * .24, .4), (cx + .25, cy - f * .14, .36), (cx - .25, cy - f * .14, .36)][::f])
        B.quad("wiremesh", [(cx - .25, cy - f * .14, .36), (cx + .25, cy - f * .14, .36), (cx + .25, cy - f * .32, .8), (cx - .25, cy - f * .32, .8)][::f])
        for dx in (-.25, .25):
            B.beam("blacksteel", (cx + dx, cy - f * .14, .36), (cx + dx, cy - f * .32, .8), .02)
    chair(W - 1.55, -2.15, 1)
    chair(W - 1.55, 0.35, -1)
    for i in range(4):                                               # tyre stack and ladder past the board's far end
        B.cyl("rubber", (W - .5, 2.45, .02 + i * .2), .3, .19, 10)
    for y in (2.95, 3.4):
        B.beam("ladder", (W - .62, y, 0), (W - .08, y, 2.35), .05, .06)
    for k in range(7):
        z = .3 + k * .3; x = W - .62 + .54 * z / 2.35
        B.beam("ladder", (x, 2.95, z), (x, 3.4, z), .03)
    B.cyl("barrel_o", (W - .6, -5.0, 0), .3, .9, 10)
    B.cyl("barrel_b", (W - 1.3, -5.5, 0), .3, .9, 10)
    B.cyl("barrel_b", (-W + .6, 1.2, 0), .3, .9, 10)
    B.cyl("red", (W - 2.0, -2.8, 0), .12, .35, 6)                     # red jerrycan-ish
    for x, y, a in ((-0.9, -4.6, .3), (3.2, 3.6, .1)):
        c, s = math.cos(a), math.sin(a)
        pts = [(x + c * dx - s * dy, y + s * dx + c * dy, .005) for dx, dy in ((-.3, -.2), (.3, -.2), (.3, .2), (-.3, .2))]
        B.quad("paper", pts)

    # ---- work lights (garage style), aimed at the bumpers ----------------------------
    # car nose faces -Y in env space (the viewer turns the car to face the open side)
    def placed(origin, yaw):
        c, s_ = math.cos(yaw), math.sin(yaw)
        return lambda p: (origin[0] + p[0] * c - p[1] * s_, origin[1] + p[0] * s_ + p[1] * c, origin[2] + p[2])

    def lamp_head(T, cx, cz, w, h, d, body="steel"):
        B.beam(body, T((cx, -d / 2, cz)), T((cx, d / 2, cz)), w, h)                 # housing
        B.beam("steel", T((cx, d / 2, cz)), T((cx, d / 2 + .012, cz)), w + .02, h + .02)  # bezel
        a, b = w / 2 - .028, h / 2 - .028
        y = d / 2 + .014
        B.quad("EMIT_work", [T((cx - a, y, cz - b)), T((cx - a, y, cz + b)), T((cx + a, y, cz + b)), T((cx + a, y, cz - b))])
        return T((cx, y, cz))

    LAMPS = {}
    # floor flood light (stand + U frame), front-right of the nose
    o = (1.95, -3.55, 0.0); yaw = math.atan2(1.55, -1.45) - math.pi / 2   # face the front bumper
    T = placed(o, yaw)
    for x in (-.17, .17):
        B.beam("yellow", T((x, -.2, .025)), T((x, .2, .025)), .035)
        for y in (-.21, .21):
            B.beam("rubber", T((x, y - .02, .025)), T((x, y + .02, .025)), .042)
        B.beam("yellow", T((x, 0, .03)), T((x, 0, .46)), .03)
    B.beam("yellow", T((-.17, 0, .04)), T((.17, 0, .04)), .03)
    B.beam("yellow", T((-.17, 0, .46)), T((.17, 0, .46)), .03)
    B.beam("rubber", T((-.1, 0, .465)), T((.1, 0, .465)), .042)
    for x in (-.17, .17):
        B.beam("steel", T((x, -.02, .27)), T((x * .8, -.02, .27)), .03)
    LAMPS["floor"] = lamp_head(T, 0, .27, .30, .24, .09)

    # twin halogen on a tripod, behind the car toward the rear bumper
    o = (2.15, 3.45, 0.0); yaw = math.atan2(-1.65, -1.65) - math.pi / 2   # rear-right, clear of the chili sign
    T = placed(o, yaw)
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        foot = (math.cos(a) * .48, math.sin(a) * .48, .02)
        B.beam("yellow", T((0, 0, .55)), T(foot), .028)
        B.beam("rubber", T((foot[0], foot[1], .0)), T((foot[0], foot[1], .06)), .04)
    B.beam("yellow", T((0, 0, .5)), T((0, 0, 1.62)), .036)
    B.beam("rubber", T((0, 0, .98)), T((0, 0, 1.08)), .05)
    B.beam("yellow", T((-.36, 0, 1.62)), T((.36, 0, 1.62)), .035, .03)
    for x in (-.21, .21):
        B.beam("steel", T((x - .1, 0, 1.63)), T((x - .1, 0, 1.78)), .015)
        B.beam("steel", T((x + .1, 0, 1.63)), T((x + .1, 0, 1.78)), .015)
        LAMPS[f"tripod{'L' if x < 0 else 'R'}"] = lamp_head(T, x, 1.79, .2, .15, .11, body="yellow")
        for gx in (-.06, 0, .06):                                    # wire guard
            B.beam("steel", T((x + gx, .075, 1.72)), T((x + gx, .075, 1.86)), .008)
        B.beam("rubber", T((x - .05, 0, 1.875)), T((x + .05, 0, 1.875)), .025)
    B.lamps = LAMPS

    # ---- neon signs --------------------------------------------------------------------------
    # red "CHILI PEPPER / GARAGE" on the stair-side (left) wall, facing into the room (+x)
    # 25% smaller than first pass, tubes mounted straight on the plaster (no backing box)
    x = -W + .02; y0, y1, z0, z1 = -3.525, -1.575, 1.5875, 2.4125
    B.quad_uv("EMIT_neon_red", [(x + .03, y0, z0), (x + .03, y1, z0), (x + .03, y1, z1), (x + .03, y0, z1)],
              [(0, 0), (1, 0), (1, 1), (0, 1)])
    # purple chili outline under the mezzanine, back wall left of the pegboard, facing -y
    yw = Y1 - .04; x0, x1, z0, z1 = -2.95, -1.95, 1.15, 2.15
    B.box("steel", (x0 - .05, yw - .03, z0 - .05), (x1 + .05, Y1, z1 + .05))
    B.quad("neon_back", [(x0, yw - .031, z0), (x1, yw - .031, z0), (x1, yw - .031, z1), (x0, yw - .031, z1)])
    B.quad_uv("EMIT_neon_purple", [(x0, yw - .05, z0), (x0, yw - .05, z1), (x1, yw - .05, z1), (x1, yw - .05, z0)],
              [(0, 0), (0, 1), (1, 1), (1, 0)])
    B.signs = {"red": ((x + .05, (y0 + y1) / 2, 2.0), (1.95, 0.825)),
               "purple": (((x0 + x1) / 2, yw - .07, 1.65), (1.0, 1.0))}

    # hanging lamp over the car
    B.cyl("steel", (0, 0.2, 4.4), .01, RIDGE - 4.4 - .2, 4)
    B.cyl("steel", (0, 0.2, 4.25), .22, .15, 8, caps=False)
    B.cyl("EMIT_lamp", (0, 0.2, 4.22), .1, .06, 8)
    return B


def make_material(name, png):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(png)
    t.interpolation = "Closest"; t.extension = "REPEAT"
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    B = build()
    stats = {}
    for mat, b in B.bms.items():
        b.normal_update()
        world_uvs(b)
        uvl = b.loops.layers.uv.active
        for f, uvs in B.fixed.get(mat, []):
            for l, uv in zip(f.loops, uvs):
                l[uvl].uv = uv
        png = os.path.join(TEX_DIR, f"{mat}.png")
        Image.fromarray(TEXTURES[mat]()).save(png)
        me = bpy.data.meshes.new(mat); b.to_mesh(me); b.free()
        me.materials.append(make_material(mat, png))
        o = bpy.data.objects.new(mat, me); bpy.context.scene.collection.objects.link(o)
        stats[mat] = len(me.vertices)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "garage.glb"), export_format="GLB")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "garage.blend"))
    print("verts", sum(stats.values()), stats)
    import json
    anchors = {k: [round(c, 3) for c in v] for k, v in {**B.lamps, **B.peg}.items()}
    anchors.update({f"sign_{k}": [round(c, 3) for c in v[0]] for k, v in B.signs.items()})
    json.dump(anchors, open(os.path.join(OUT, "anchors.json"), "w"), indent=1)
    print("anchors (blender xyz)", anchors)


if __name__ == "__main__":
    main()
