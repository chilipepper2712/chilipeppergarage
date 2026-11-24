"""MINI Cooper S 5-door (F55), 2018 facelift, 6-speed manual.

Units: metres. Axes: Z up, +Y forward, +X = right side of driver. Origin: ground, centre of wheelbase.

Dimensions from the blueprint's own dimension lines (vector-templates, 2018 Cooper S 5-door):
4013 x 1727 x 1424, WB 2567. Calibrated on the drawn wheelbase line: 256.7 px = 2.567 m -> 100 px/m.
Tyre 205/45R17 (Cooper S standard), tracks 1501/1501 and clearance 130 NOT verified -> TBD.
The blueprint has a text watermark across the body, so the profile is read off a metric grid by hand.
Texture painted in the KEY ramp (blue); the viewer applies the car's default colour.
"""
import numpy as np

NAME = "mini_f55_2018"
LENGTH, WIDTH, HEIGHT = 4.013, 1.727, 1.424
WHEELBASE = 2.567
TRACK_F, TRACK_R = 1.501, 1.501          # TBD - unverified
TYRE = (205, 45, 17)
CLEARANCE = 0.130                        # TBD - unverified
ARCH_R = 0.36

Y_NOSE, Y_TAIL = 2.12, -1.88
AXLES = (WHEELBASE / 2, -WHEELBASE / 2)

Y_COWL = 1.0315
Y_ROOF_FRONT = 0.48
Y_ROOF_REAR = -1.4095
Y_REAR_GLASS_BOT = -1.6435
Y_HOOD_FRONT = 2.09
SIDE_GLASS_REAR = -1.2835

DOOR_LINES = (0.9235, -0.30, -0.9235)
DOOR_R_TOP_END = -1.0315
B_PILLAR = (-0.40, -0.30)

PAINT = "blue"
DEFAULT_PAINT = "green"

K = dict(
    z_top=[(2.12, .64), (2.07, .82), (2.0, .885), (1.85, .915), (1.6, .935), (1.3, .965), (Y_COWL, 1.0),
           (0.75, 1.20), (Y_ROOF_FRONT, 1.37), (0.3, 1.40), (-0.5, 1.42), (-1.2, 1.42), (-1.32, 1.405),
           (Y_ROOF_REAR, 1.39), (-1.5355, 1.22), (Y_REAR_GLASS_BOT, 1.05), (-1.75, 1.01), (-1.81, .82),
           (-1.88, .60)],
    z_belt=[(2.12, .60), (2.07, .79), (2.0, .865), (1.85, .90), (1.6, .915), (1.3, .945), (Y_COWL, .98),
            (0.6, 1.01), (0.0, 1.02), (-1.3, 1.03), (Y_REAR_GLASS_BOT, 1.02), (-1.75, .97), (-1.81, .78),
            (-1.88, .56)],
    # Mini shoulder: widest point high on the side, then a short ledge in to an upright glasshouse
    x_belt=[(2.12, .55), (2.07, .66), (2.0, .72), (1.85, .74), (1.6, .72), (Y_COWL, .70), (0.0, .69),
            (Y_REAR_GLASS_BOT, .69), (-1.75, .70), (-1.81, .66), (-1.88, .58)],
    x_top=[(Y_COWL, .66), (Y_ROOF_FRONT, .60), (0.0, .60), (-1.0, .60), (Y_ROOF_REAR, .58),
           (Y_REAR_GLASS_BOT, .55)],
    x_max=[(2.12, .62), (2.07, .72), (2.0, .80), (1.85, .845), (1.6, .865), (0.0, .865), (-1.6, .865),
           (-1.75, .84), (-1.81, .80), (-1.88, .70)],
    z_mid=[(2.12, .42), (2.0, .62), (1.6, .80), (-1.6, .82), (-1.75, .80), (-1.88, .50)],
    z_sill=[(2.12, .21), (2.0, .20), (1.6435, .19), (-1.6435, .20), (-1.81, .23), (-1.88, .24)],
    z_floor=[(2.12, .19), (2.0, .16), (1.6435, CLEARANCE), (-1.6435, CLEARANCE), (-1.81, .20), (-1.88, .22)],
)

EXTRA_STATIONS = [2.12, 2.07, 2.0, 1.85, 0.75, 0.48, -0.30, -0.6, -1.75, -1.81, -1.88]

SOCKETS_EXTRA = {
    "hood": (0, 1.6, .9), "roof": (0, -0.4, 1.42), "spoiler": (0, Y_ROOF_REAR, 1.39),
    "exhaust": (0.0, Y_TAIL, .24), "grille": (0, Y_NOSE, .6),
}
MIRROR = dict(y=0.47, z=1.02, x_in=0.79, length=0.21, size=(0.10, 0.13))
EXTRA_PARTS = ("headlight_L", "headlight_R")
SWAP_PARTS = ("bumper_F", "bumper_R", "skirt_L", "skirt_R")

TYRE_R = (TYRE[2] * 25.4 + 2 * TYRE[0] * TYRE[1] / 100) / 2000


def _circle(kind, cx, cz, r, n=10):
    import math
    return [(kind, cx + r * math.cos(2 * math.pi * k / n), cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


FEATURES = [
    # big hexagonal grille
    dict(name="grille", kind="grille", part="bumper_F", depth=0.05, taper=0.03,
         outline=[("f", -0.45, .72), ("f", 0.45, .72), ("f", 0.55, .62), ("f", 0.48, .50),
                  ("f", -0.48, .50), ("f", -0.55, .62)]),
    dict(name="grille_low", kind="grille", part="bumper_F", depth=0.04, taper=0.04,
         outline=[("f", -0.50, .22), ("f", 0.50, .22), ("f", 0.47, .35), ("f", -0.47, .35)]),
    # round headlamps sitting on the front of the wings
    dict(name="headlamp", kind="headlamp", part="headlight_{s}", mirror=True, depth=0.02,
         back="normal", taper=0.05, outline=_circle("f", 0.62, .80, .105)),
    dict(name="fog", kind="fog", part="bumper_F", mirror=True, depth=0.03, taper=0.1,
         outline=_circle("f", 0.62, .47, .055, 8)),
    # rounded plate recess on the tailgate
    dict(name="plate_rear", kind="recess", part="tailgate", depth=0.02, taper=0.02,
         outline=[("r", -0.33, .67), ("r", 0.33, .67), ("r", 0.35, .76), ("r", 0.33, .85),
                  ("r", -0.33, .85), ("r", -0.35, .76)]),
]


def paint(P, N, V, glass, body_col, C, B):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    out = np.full(len(P), -1, int)
    ng = ~glass & (B < 20)
    front = (y > 1.95) & (N[:, 1] > 0.15) & ng
    rear = (y < -1.7) & (N[:, 1] < -0.15) & ng
    side = (np.abs(N[:, 0]) > 0.5) & ng

    # contrast roof + blacked pillars (signature MINI look)
    roof = ng & (z > 1.33) & (y < Y_ROOF_FRONT + 0.05) & (y > Y_ROOF_REAR - 0.12)
    out[roof] = C["plastic"]
    out[glass & (((y < -0.90) & (y > -1.02)) | (y < -1.30) & (y > Y_ROOF_REAR))] = C["black"]   # C/D pillars

    lens = B == 22
    r = np.hypot(ax - 0.62, z - 0.80)
    out[lens & (np.abs(r - 0.085) < 0.012)] = C["light_w"]                    # LED ring
    out[lens & (r < 0.035)] = C["chrome_hi"]
    out[(B == 20) & (np.abs(z - 0.62) < 0.012)] = C["chrome"]                  # grille bar
    out[(B == 21) & (np.hypot(ax - 0.62, z - 0.47) < 0.03)] = C["chrome_hi"]
    out[(B == 20) & (z < 0.4) & (ax < 0.17) & (z > 0.24)] = C["plate"]        # plate in the lower intake
    hs = ng & (N[:, 2] > 0.5) & (ax < 0.2) & (y > 1.72) & (y < 1.95)         # Cooper S bonnet scoop
    out[hs] = C["black"]
    out[front & (z < 0.22)] = C["plastic"]

    e = ((ax - 0.65) / 0.07) ** 2 + ((z - 0.825) / 0.105) ** 2                 # vertical oval rear lamps
    tl = (y < -1.62) & (e < 1) & ng
    out[tl] = C["tail"]
    out[tl & ((np.abs(ax - 0.65) < 0.008) | (np.abs(z - 0.825) < 0.008))] = C["black"]   # Union Jack bars
    out[tl & (e > 0.7)] = C["tail_hi"]
    rp = (B == 23) & (ax < 0.16) & (z > 0.70) & (z < 0.82)
    out[rp] = C["plate"]
    out[rp & (np.abs(z - 0.76) < 0.02) & (ax < 0.13) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[rear & (z < 0.31)] = C["plastic"]
    for sx in (-0.07, 0.07):                                                   # centre twin exhaust
        out[rear & (np.hypot(x - sx, z - 0.24) < 0.036)] = C["chrome"]
        out[rear & (np.hypot(x - sx, z - 0.24) < 0.022)] = C["black"]
    out[rear & (np.abs(ax - 0.42) < 0.05) & (np.abs(z - 0.32) < 0.012)] = C["tail"]
    out[rear & (np.abs(ax - 0.62) < 0.06) & (z > 0.37) & (z < 0.47)] = C["black"]

    for ya in AXLES:                                                           # black arch flares
        rr = np.hypot(y - ya, z - TYRE_R)
        out[side & (rr < ARCH_R + 0.06) & (rr > ARCH_R - 0.04) & (z > 0.18)] = C["plastic"]
    out[side & (z < 0.27) & (y < 1.6) & (y > -1.6)] = C["plastic"]
    out[side & (np.abs(y - 0.98) < 0.06) & (np.abs(z - 0.85) < 0.02)] = C["black"]   # side scuttle
    zb = np.interp(y, *zip(*sorted(K["z_belt"])))
    for y0, y1 in ((-0.20, -0.02), (-0.88, -0.72)):
        out[side & (y > y0) & (y < y1) & (z > zb - 0.155) & (z < zb - 0.12)] = C["chrome"]
    return out


_LIP_K = dict(z_sill=[(2.12, .18), (2.0, .17), (1.75, .175)], z_floor=[(2.12, .16), (2.0, .13), (1.75, .125)])
VARIANTS = {
    "lip": dict(parts=["bumper_F"], K=_LIP_K),
    "sport": dict(
        parts=["bumper_F"], K=_LIP_K, features_remove=("grille_low", "fog"),
        features_add=[
            dict(name="grille_sport", kind="grille", part="bumper_F", depth=0.06, taper=0.03,
                 outline=[("f", -0.52, .19), ("f", 0.52, .19), ("f", 0.50, .38), ("f", -0.50, .38)]),
            dict(name="intake", kind="grille", part="bumper_F", mirror=True, depth=0.05, taper=0.06,
                 outline=[("f", 0.56, .22), ("f", 0.72, .24), ("f", 0.74, .44), ("f", 0.60, .48), ("f", 0.55, .36)]),
        ]),
    "diffuser": dict(
        parts=["bumper_R"],
        K=dict(z_sill=[(-1.81, .20), (-1.88, .21)], z_floor=[(-1.81, .17), (-1.88, .19)]),
        features_add=[
            dict(name=f"diff{i}", kind="grille", part="bumper_R", depth=0.05,
                 outline=[("r", x0, .215), ("r", x0 + 0.10, .215), ("r", x0 + 0.10, .27), ("r", x0, .27)])
            for i, x0 in enumerate((-0.45, -0.28, 0.18, 0.35))]),
    "skirt": dict(parts=["skirt_L", "skirt_R"], set=dict(SKIRT_DROP=0.04)),
}
