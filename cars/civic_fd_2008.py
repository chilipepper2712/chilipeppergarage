"""Honda Civic 8th gen sedan, 1.8 MT (VN: FD, 2006-2011).

Units: metres. Axes: Z up, +Y forward, +X = right side of driver. Origin: ground, centre of wheelbase.

Dimensions (VN, bonbanh 2007/2008 1.8): 4540 x 1750 x 1450, WB 2700, tracks 1500/1530,
clearance 170, tyre 195/65R15.
Profile MEASURED from blueprints/civic_fd_2008/blueprint.png (US 2006 sedan, 49.6 px/m, calibrated
on the wheelbase; length 4.515 m checks out). The blueprint roof reads 1.49 m vs 1.45 spec, so heights
above 0.65 m are compressed to the VN figure (lower body and tyres already match).
Blueprint is the US car (FA): rear lamps are drawn the VN/Asian FD way instead (wider, onto the lid).
Texture is painted in the KEY ramp (blue); the viewer applies the car's default colour (white).
"""
import numpy as np

NAME = "civic_fd_2008"
LENGTH, WIDTH, HEIGHT = 4.540, 1.750, 1.450
WHEELBASE = 2.700
TRACK_F, TRACK_R = 1.500, 1.530
TYRE = (195, 65, 15)
CLEARANCE = 0.170
ARCH_R = 0.37

Y_NOSE, Y_TAIL = 2.26, -2.25
AXLES = (WHEELBASE / 2, -WHEELBASE / 2)

Y_COWL = 1.35                # windshield base: after a short flat cowl plateau (blueprint 1.46 -> 1.30)
Y_ROOF_FRONT = 0.25
Y_ROOF_REAR = -1.1095
Y_REAR_GLASS_BOT = -1.72
Y_HOOD_FRONT = 2.18
SIDE_GLASS_REAR = -1.2205

DOOR_LINES = (0.98, -0.25, -0.98)
DOOR_R_TOP_END = -1.2205
B_PILLAR = (-0.36, -0.22)

PAINT = "blue"               # key ramp; default colour set by the viewer
DEFAULT_PAINT = "white"


def Z(z):
    """blueprint height -> VN height (compress above 0.65 m: 1.49 -> 1.45)"""
    return z if z < 0.65 else 0.65 + (z - 0.65) * (1.45 - 0.65) / (1.49 - 0.65)


def _k(pts):
    return [(y, round(Z(z), 4)) for y, z in pts]


# z_top measured column by column off the blueprint silhouette (see README in blueprints/)
K = dict(
    z_top=_k([(2.26, .50), (2.20, .66), (2.11, .755), (2.03, .80), (1.95, .84), (1.78, .90),
              (1.62, .94), (1.4795, .972), (Y_COWL, .98), (1.22, 1.018), (1.06, 1.099), (0.90, 1.179),
              (0.74, 1.24), (0.57, 1.32), (0.41, 1.38), (0.25, 1.42), (0.0, 1.462), (-0.15, 1.482),
              (-0.80, 1.482), (-0.96, 1.462), (Y_ROOF_REAR, 1.42), (-1.28, 1.36), (-1.44, 1.30),
              (-1.60, 1.22), (Y_REAR_GLASS_BOT, 1.15), (-1.88, 1.12), (-2.05, 1.10),
              (-2.17, 1.115),                                  # duck-tail lip on the trunk edge
              (-2.21, 1.05), (-2.25, .98)]),
    z_belt=_k([(2.26, .47), (2.20, .61), (2.11, .70), (2.03, .755), (1.95, .795), (1.78, .855),
               (1.62, .90), (1.4795, .93), (Y_COWL, .945), (1.0, .975), (0.5, .99), (0.0, 1.0),
               (-0.6, 1.03), (Y_ROOF_REAR, 1.055), (-1.45, 1.07), (Y_REAR_GLASS_BOT, 1.075),
               (-2.05, 1.06), (-2.17, 1.07), (-2.21, 1.0), (-2.25, .90)]),
    x_belt=[(2.26, .30), (2.20, .55), (2.11, .70), (1.95, .79), (1.65, .82), (Y_COWL, .82),
            (-1.45, .82), (Y_REAR_GLASS_BOT, .80), (-2.05, .77), (-2.17, .70), (-2.21, .62), (-2.25, .50)],
    x_top=[(Y_COWL, .69), (1.0, .65), (0.5, .58), (0.0, .54), (-0.6, .54), (Y_ROOF_REAR, .55),
           (-1.45, .60), (Y_REAR_GLASS_BOT, .66)],
    x_max=[(2.26, .40), (2.20, .60), (2.10, .73), (1.90, .83), (1.72, .868), (1.35, .876), (0.0, .87),
           (-1.35, .876), (-1.72, .868), (-1.95, .85), (-2.10, .80), (-2.20, .70), (-2.25, .50)],
    z_mid=[(2.26, .40), (2.11, .50), (1.80, .58), (1.50, .62), (-1.50, .64), (-2.0, .66), (-2.25, .62)],
    z_sill=[(2.26, .30), (2.10, .28), (1.72, .26), (-1.72, .25), (-2.10, .36), (-2.25, .38)],
    z_floor=[(2.26, .28), (2.10, .22), (1.72, CLEARANCE), (-1.72, CLEARANCE), (-2.10, .30), (-2.25, .34)],
)

EXTRA_STATIONS = [2.26, 2.20, 2.11, 2.03, 1.90, 0.6, 0.25, -0.25, -0.6, -1.95, -2.10, -2.17, -2.21, -2.25]

SOCKETS_EXTRA = {
    "hood": (0, 1.8, .9), "roof": (0, -0.4, 1.45), "spoiler": (0, -2.10, Z(1.11)),
    "exhaust": (-0.45, Y_TAIL, .3), "grille": (0, Y_NOSE, .45),
}

MIRROR = dict(y=0.67, z=Z(1.02), x_in=0.78, length=0.22, size=(0.10, 0.12))
EXTRA_PARTS = ("headlight_L", "headlight_R")
SWAP_PARTS = ("bumper_F", "bumper_R", "skirt_L", "skirt_R")


def _xb(y):
    return float(np.interp(y, *zip(*sorted(K["x_belt"]))))


def _zb(y):
    return float(np.interp(y, *zip(*sorted(K["z_belt"]))))


FEATURES = [
    # thin V-shaped upper grille between the headlamps (H badge in the middle)
    dict(name="grille_up", kind="grille", part="bumper_F", depth=0.02, taper=0.03,
         outline=[("f", -0.44, .735), ("f", -0.2, .668), ("f", 0.0, .635), ("f", 0.2, .668),
                  ("f", 0.44, .735), ("f", 0.40, .752), ("f", 0.2, .70), ("f", 0.0, .672),
                  ("f", -0.2, .70), ("f", -0.40, .752)]),
    # wide lower intake slot
    dict(name="grille_low", kind="grille", part="bumper_F", depth=0.05, taper=0.03,
         outline=[("f", -0.52, .31), ("f", 0.52, .31), ("f", 0.55, .385), ("f", -0.55, .385)]),
    # swept headlamps: inner tip at the grille, top edge on the hood shut line, tail onto the fender
    dict(name="headlamp", kind="headlamp", part="headlight_{s}", mirror=True, depth=0.015,
         back="normal", taper=0.03,
         outline=[("f", 0.25, .70)]
         + [("n", _xb(y) - 0.01, y, _zb(y) - 0.012) for y in (2.17, 2.08, 1.98, 1.88, 1.80)]
         + [("s", 1.74, .835), ("s", 1.82, .79), ("s", 1.95, .725), ("f", 0.62, .655),
            ("f", 0.45, .655), ("f", 0.33, .672)]),
    # plate recess on the trunk lid between the lamps
    dict(name="plate_rear", kind="recess", part="tailgate", depth=0.02, taper=0.02,
         outline=[("r", -0.25, .735), ("r", 0.25, .735), ("r", 0.24, .865), ("r", -0.24, .865)]),
]


def paint(P, N, V, glass, body_col, C, B):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    out = np.full(len(P), -1, int)
    ng = ~glass & (B < 20)
    front = (y > 2.0) & (N[:, 1] > 0.15) & ng
    rear = (y < -2.0) & (N[:, 1] < -0.15) & ng

    lens = B == 22
    d2 = (ax - 0.55) ** 2 + (z - 0.73) ** 2
    out[lens & (d2 < 0.04 ** 2)] = C["chrome_hi"]
    out[lens & (d2 < 0.018 ** 2)] = C["chrome"]
    out[lens & (y < 1.86)] = C["amber"]                                     # side marker
    out[(B == 20) & (ax < 0.05) & (np.abs(z - 0.655) < 0.03)] = C["chrome"]  # H badge
    fp = front & (ax < 0.17) & (z > 0.405) & (z < 0.515)                     # VN plate on the bumper
    out[fp] = C["plate"]
    out[fp & (np.abs(z - 0.46) < 0.018) & (ax < 0.14) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[front & (z < 0.285)] = C["plastic"]

    # FD rear lamps: wide, wrapping the corner and stepping onto the trunk lid
    tl = (y < -1.98) & (ax > 0.32) & (z > Z(0.81)) & (z < Z(1.0)) & ng & \
        (z > Z(0.81) + np.clip(0.45 - ax, 0, 1) * 0.35)
    out[tl] = C["tail"]
    out[tl & (z > Z(0.93))] = C["tail_hi"]
    out[tl & (ax > 0.45) & (ax < 0.56) & (z < Z(0.87))] = C["light_w"]      # reverse lamp
    rp = (B == 23) & (ax < 0.17) & (z > 0.745) & (z < 0.855)
    out[rp] = C["plate"]
    out[rp & (np.abs(z - 0.80) < 0.02) & (ax < 0.14) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[rear & (np.abs(z - 0.88) < 0.008) & (ax < 0.26) & (y < -2.1)] = C["chrome"]  # garnish over plate
    out[rear & (z < 0.37)] = C["plastic"]
    out[rear & (ax > 0.55) & (ax < 0.70) & (np.abs(z - 0.45) < 0.015)] = C["tail"]  # reflectors

    side = (np.abs(N[:, 0]) > 0.5) & ng
    zb = np.interp(y, *zip(*sorted(K["z_belt"])))
    for y0, y1 in ((-0.17, -0.02), (-1.10, -0.94)):                           # handles
        out[side & (y > y0) & (y < y1) & (z > zb - 0.125) & (z < zb - 0.09)] = C["black"]
    fd = side & (x > 0) & (np.abs(np.hypot(y + 1.41, z - Z(0.92)) - 0.065) < 0.009)
    out[fd] = C["seam_" + PAINT]
    out[side & (z < 0.31) & (y < 1.66) & (y > -1.66)] = C["plastic"]       # rocker
    out[side & (np.abs(z - Z(0.88)) < 0.006) & (y < 0.95) & (y > -1.6)] = C["seam_" + PAINT]  # shoulder crease
    return out


_LIP_K = dict(z_sill=[(2.26, .27), (2.10, .235), (1.75, .24)],
              z_floor=[(2.26, .24), (2.10, .19), (1.75, .155)])

VARIANTS = {
    "lip": dict(parts=["bumper_F"], K=_LIP_K),
    "sport": dict(
        parts=["bumper_F"], K=_LIP_K, features_remove=("grille_low",),
        features_add=[
            dict(name="grille_sport", kind="grille", part="bumper_F", depth=0.06, taper=0.03,
                 outline=[("f", -0.46, .27), ("f", 0.46, .27), ("f", 0.52, .40), ("f", 0.30, .43),
                          ("f", -0.30, .43), ("f", -0.52, .40)]),
            dict(name="intake", kind="grille", part="bumper_F", mirror=True, depth=0.05, taper=0.06,
                 outline=[("f", 0.58, .28), ("f", 0.72, .28), ("f", 0.76, .36), ("f", 0.72, .47),
                          ("f", 0.61, .45), ("f", 0.57, .37)]),
        ]),
    "diffuser": dict(
        parts=["bumper_R"],
        K=dict(z_sill=[(-2.10, .31), (-2.25, .32)], z_floor=[(-2.10, .25), (-2.25, .28)]),
        features_add=[
            dict(name=f"diff{i}", kind="grille", part="bumper_R", depth=0.05,
                 outline=[("r", x0, .325), ("r", x0 + 0.11, .325), ("r", x0 + 0.11, .385),
                          ("r", x0, .385)])
            for i, x0 in enumerate((-0.42, -0.18, 0.07, 0.31))]),
    "skirt": dict(parts=["skirt_L", "skirt_R"], set=dict(SKIRT_DROP=0.045)),
}
