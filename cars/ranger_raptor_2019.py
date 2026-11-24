"""Ford Ranger Raptor 2019 (T6 facelift based), 2.0 Bi-Turbo diesel, 10AT, double cab.

Units: metres. Axes: Z up, +Y forward, +X = right side of driver. Origin: ground, centre of wheelbase.

Specs: 5398 x 2028 x 1873, WB 3220, tracks 1710/1710, clearance 283, tyre 285/70R17, ~2330 kg.
Profile MEASURED from blueprints/ranger_raptor_2019/blueprint.png. The drawing is ~2% inconsistent:
scaled on the wheelbase it is 5.28 m long and 1.82 m tall, scaled on length/height its wheelbase reads
3.295 m. Shapes are read at 127.6 px/m (length & height match spec); the axles stay at the spec 3220 mm,
so arches sit ~4 cm off the drawing but true to the car.
Pickup bed: the loft runs at bed-rail height and the bed tub is cut out from the top ("bed" feature).
Texture painted in the KEY ramp (blue); the viewer applies the car's default colour.
"""
import math
import numpy as np

NAME = "ranger_raptor_2019"
LENGTH, WIDTH, HEIGHT = 5.398, 2.028, 1.873
WHEELBASE = 3.220
TRACK_F, TRACK_R = 1.710, 1.710
TYRE = (285, 70, 17)
CLEARANCE = 0.283
ARCH_R = 0.55
TYRE_R = (TYRE[2] * 25.4 + 2 * TYRE[0] * TYRE[1] / 100) / 2000

Y_NOSE, Y_TAIL = 2.53, -2.86
AXLES = (WHEELBASE / 2, -WHEELBASE / 2)

Y_COWL = 1.225
Y_ROOF_FRONT = 0.45
Y_ROOF_REAR = -0.98          # cab back (rear window is painted on the cab's back wall)
Y_REAR_GLASS_BOT = -1.0      # behind this: bed (deck)
Y_TAILGATE = -2.79           # only the last panel is the tailgate; bed sides stay body
Y_HOOD_FRONT = 2.50
SIDE_GLASS_REAR = -0.98

DOOR_LINES = (1.06, -0.13, -1.06)
DOOR_R_TOP_END = -1.06
B_PILLAR = (-0.21, -0.04)

PAINT = "blue"
DEFAULT_PAINT = "white"

K = dict(
    z_top=[(2.53, 1.18), (2.48, 1.25), (2.40, 1.24), (2.2, 1.28), (2.0, 1.31), (1.6, 1.37), (1.4175, 1.39),
           (Y_COWL, 1.38), (1.06, 1.46), (0.83, 1.62), (0.59, 1.74), (Y_ROOF_FRONT, 1.79), (0.2, 1.84),
           (0.0, 1.865), (-0.5, 1.87), (-0.9, 1.865), (Y_ROOF_REAR, 1.86), (-1.06, 1.36), (-2.80, 1.36),
           (-2.86, .73)],
    z_belt=[(2.53, 1.10), (2.48, 1.20), (2.40, 1.21), (2.2, 1.25), (2.0, 1.28), (1.6, 1.33), (Y_COWL, 1.35),
            (0.8, 1.36), (0.0, 1.37), (Y_ROOF_REAR, 1.37), (-1.06, 1.33), (-2.80, 1.33), (-2.86, .70)],
    x_belt=[(2.53, .55), (2.48, .70), (2.40, .80), (2.2, .85), (Y_COWL, .86), (-1.06, .86), (-2.80, .88),
            (-2.86, .80)],
    x_top=[(Y_COWL, .75), (Y_ROOF_FRONT, .66), (0.0, .64), (Y_ROOF_REAR, .64)],
    # fender flares stick out to 1.01 over both axles; cab and bed sides sit at ~0.89-0.92
    x_max=[(2.53, .70), (2.48, .85), (2.40, .95), (2.2, 1.0), (2.16, 1.01), (1.06, 1.01), (0.95, .89),
           (-0.95, .89), (-1.06, 1.0), (-2.16, 1.0), (-2.25, .97), (-2.40, .93), (-2.80, .92), (-2.86, .88)],
    z_mid=[(2.53, .75), (2.40, .85), (2.2, .95), (-2.2, .95), (-2.80, .95), (-2.86, .62)],
    z_sill=[(2.53, .50), (2.40, .52), (2.16, .55), (1.06, .40), (-1.06, .40), (-2.16, .55), (-2.80, .50),
            (-2.86, .48)],
    z_floor=[(2.53, .48), (2.40, .45), (2.16, .40), (1.06, .32), (-1.06, .32), (-2.16, .40), (-2.80, .47),
             (-2.86, .46)],
)

EXTRA_STATIONS = [2.53, 2.48, 2.40, 2.2, 0.83, 0.59, 0.45, 0.2, -0.13, -0.5, -0.85, -0.98, -2.40, -2.80, -2.86]

SOCKETS_EXTRA = {
    "hood": (0, 1.9, 1.33), "roof": (0, -0.3, 1.87), "spoiler": (0, -0.95, 1.86),
    "exhaust": (-0.62, Y_TAIL + 0.1, .45), "grille": (0, Y_NOSE, 1.05),
}
MIRROR = dict(y=0.86, z=1.45, x_in=0.86, length=0.21, size=(0.12, 0.15))
EXTRA_PARTS = ("headlight_L", "headlight_R")
SWAP_PARTS = ("bumper_F", "bumper_R", "skirt_L", "skirt_R")


FEATURES = [
    dict(name="grille", kind="grille", part="bumper_F", depth=0.05, taper=0.02,
         outline=[("f", -0.55, .95), ("f", 0.55, .95), ("f", 0.58, 1.05), ("f", 0.50, 1.18),
                  ("f", -0.50, 1.18), ("f", -0.58, 1.05)]),
    dict(name="grille_low", kind="grille", part="bumper_F", depth=0.04, taper=0.03,
         outline=[("f", -0.48, .62), ("f", 0.48, .62), ("f", 0.48, .73), ("f", -0.48, .73)]),
    dict(name="headlamp", kind="headlamp", part="headlight_{s}", mirror=True, depth=0.015, back="normal",
         taper=0.03, outline=[("f", 0.56, 1.02), ("f", 0.86, 1.00), ("f", 0.89, 1.10), ("f", 0.85, 1.17),
                              ("f", 0.60, 1.17), ("f", 0.55, 1.10)]),
    dict(name="fog", kind="fog", part="bumper_F", mirror=True, depth=0.03, taper=0.08,
         outline=[("f", 0.68, .66), ("f", 0.85, .66), ("f", 0.86, .79), ("f", 0.70, .80), ("f", 0.66, .73)]),
    # the bed tub, cut from the top down to the floor 0.50 below the rails
    dict(name="bed", kind="bed", part="body", depth=0.50, taper=0.0,
         outline=[("t", -0.78, -2.74), ("t", 0.78, -2.74), ("t", 0.78, -1.12), ("t", -0.78, -1.12)]),
]

# 3x5 pixel glyphs for the grille lettering
_GLYPH = {"F": ["###", "#..", "##.", "#..", "#.."], "O": ["###", "#.#", "#.#", "#.#", "###"],
          "R": ["##.", "#.#", "##.", "#.#", "#.#"], "D": ["##.", "#.#", "#.#", "#.#", "##."]}


def _letters(x, z, text="FORD", x0=-0.44, w=0.19, gap=0.04, zb=0.985, h=0.11):
    hit = np.zeros(len(x), bool)
    for i, ch in enumerate(text):
        lx = x0 + i * (w + gap)
        u = ((x - lx) / w * 3).astype(int); v = ((zb + h - z) / h * 5).astype(int)
        inside = (x >= lx) & (x < lx + w) & (z <= zb + h) & (z > zb)
        g = _GLYPH[ch]
        for gv in range(5):
            for gu in range(3):
                if g[gv][gu] == "#":
                    hit |= inside & (u == gu) & (v == gv)
    return hit


def paint(P, N, V, glass, body_col, C, B):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    out = np.full(len(P), -1, int)
    ng = ~glass & (B < 20)
    front = (y > 2.3) & (N[:, 1] > 0.15) & ng
    rear = (y < -2.7) & (N[:, 1] < -0.15) & ng
    side = (np.abs(N[:, 0]) > 0.5) & ng

    out[(B == 20) & _letters(-x, z)] = C["metal3"]    # FORD lettering (seen from the front, car-left is viewer-right)
    lens = B == 22
    out[lens & (np.hypot(ax - 0.75, z - 1.085) < 0.045)] = C["chrome_hi"]
    out[lens & (np.abs(z - 1.02) < 0.008)] = C["amber"]
    out[(B == 21) & (np.hypot(ax - 0.77, z - 0.73) < 0.035)] = C["chrome_hi"]
    out[front & (z < 0.62)] = C["plastic"]                                     # black lower bumper
    out[front & (ax < 0.30) & (z < 0.55)] = C["metal1"]                        # skid plate
    fp = front & (ax < 0.20) & (z > 0.75) & (z < 0.85)
    out[fp] = C["plate"]
    out[fp & (np.abs(z - 0.80) < 0.018) & (ax < 0.16) & ((np.floor(x * 64) % 3) != 0)] = C["black"]

    # cab back: rear window painted on the wall between roof and bed
    cw = ng & (y < -0.94) & (y > -1.08) & (N[:, 1] < -0.4) & (z > 1.60) & (z < 1.75) & (ax < 0.62)
    out[cw] = C["glass2"]
    out[ng & (y < -0.94) & (y > -1.08) & (N[:, 1] < -0.4) & (z > 1.58) & (z < 1.77) & (ax < 0.64) & ~cw] = C["black"]

    # rear: vertical 3-cell lamps, tailgate handle + badge, black step bumper with plate
    tl = (y < -2.72) & (ax > 0.75) & (ax < 0.875) & (z > 0.85) & (z < 1.27) & ng
    out[tl] = C["tail"]
    out[tl & ((np.floor((z - 0.85) / 0.14) % 3) == 2)] = C["tail_hi"]
    out[tl & (np.abs(((z - 0.85) % 0.14)) < 0.01)] = C["black"]
    out[rear & (ax < 0.10) & (np.abs(z - 1.225) < 0.025)] = C["black"]
    out[rear & (((x / 0.1) ** 2 + ((z - 1.10) / 0.03) ** 2) < 1)] = C["chrome"]
    out[rear & (z < 0.74)] = C["plastic"]
    rp = rear & (ax < 0.20) & (z > 0.55) & (z < 0.66)
    out[rp] = C["plate"]
    out[rp & (np.abs(z - 0.605) < 0.018) & (ax < 0.16) & ((np.floor(x * 64) % 3) != 0)] = C["black"]

    # black fender flares over both axles, rockers, fender vent, handles, fuel door
    for ya in AXLES:
        rr = np.hypot(y - ya, z - TYRE_R)
        out[ng & (ax > 0.86) & (rr < ARCH_R + 0.17) & (rr > ARCH_R - 0.05) & (z > 0.3)] = C["plastic"]
    out[side & (z < 0.47) & (y < 1.05) & (y > -1.05)] = C["plastic"]
    out[side & (y > 1.05) & (y < 1.25) & (np.abs(z - 1.15) < 0.03)] = C["black"]
    zb = np.interp(y, *zip(*sorted(K["z_belt"])))
    for y0, y1 in ((-0.02, 0.21), (-0.92, -0.69)):
        out[side & (y > y0) & (y < y1) & (np.abs(z - 1.18) < 0.02)] = C["black"]
    fd = side & (x > 0) & (np.abs(y + 1.35) < 0.10) & (np.abs(z - 1.18) < 0.06) & \
        ((np.abs(np.abs(y + 1.35) - 0.10) < 0.009) | (np.abs(np.abs(z - 1.18) - 0.06) < 0.009))
    out[fd] = C["seam_" + PAINT]
    return out


_LIP_K = dict(z_sill=[(2.53, .46), (2.40, .48), (2.25, .52)], z_floor=[(2.53, .44), (2.40, .41), (2.25, .37)])
VARIANTS = {
    "lip": dict(parts=["bumper_F"], K=_LIP_K),
    "sport": dict(
        parts=["bumper_F"], K=_LIP_K, features_remove=("grille_low",),
        features_add=[dict(name="grille_sport", kind="grille", part="bumper_F", depth=0.06, taper=0.03,
                           outline=[("f", -0.60, .55), ("f", 0.60, .55), ("f", 0.58, .76), ("f", -0.58, .76)])]),
    "diffuser": dict(
        parts=["bumper_R"],
        K=dict(z_sill=[(-2.80, .44), (-2.86, .42)], z_floor=[(-2.80, .40), (-2.86, .40)]),
        features_add=[dict(name=f"diff{i}", kind="grille", part="bumper_R", depth=0.05,
                           outline=[("r", x0, .44), ("r", x0 + 0.14, .44), ("r", x0 + 0.14, .52), ("r", x0, .52)])
                      for i, x0 in enumerate((-0.55, -0.25, 0.11, 0.41))]),
    "skirt": dict(parts=["skirt_L", "skirt_R"], set=dict(SKIRT_DROP=0.06)),
}
