"""Mazda 2 (DE) hatchback 1.5 MT, 2013, VN-assembled.

Units: metres. Axes: Z up, +Y forward, +X = right side of driver.
Origin: ground, centre of wheelbase.

Dimensions source: bonbanh.com (Mazda 2 2013): 3885 x 1695 x 1475, WB 2490,
clearance 140, tyre 185/55R15.
Track front/rear 1475/1465: NOT verified (from memory) -> TBD in spec.

Profile curves MEASURED from blueprints/mazda2_2013/blueprint.jpg
(4-view, 123.3 px/m calibrated on wheelbase; roof height check 1.464 vs 1.475 spec).
Blueprint nose is clipped ~6 px by the image edge -> front overhang taken from spec.
"""
import numpy as np

NAME = "mazda2_2013"
LENGTH, WIDTH, HEIGHT = 3.885, 1.695, 1.475
WHEELBASE = 2.490
TRACK_F, TRACK_R = 1.475, 1.465          # TBD - unverified
TYRE = (185, 55, 15)                     # width mm, aspect %, rim inch
CLEARANCE = 0.140
ARCH_R = 0.352                           # blueprint: flare edge ~0.39, opening ~0.33

Y_NOSE = 2.04
Y_TAIL = -1.84
AXLES = (WHEELBASE / 2, -WHEELBASE / 2)

# greenhouse spans from cowl (A-pillar base) to rear glass bottom
Y_COWL = 1.004
Y_ROOF_FRONT = 0.30
Y_ROOF_REAR = -1.30                      # end of roof spoiler
Y_REAR_GLASS_BOT = -1.602
Y_HOOD_FRONT = 1.97                      # in front of this the top belongs to the bumper
SIDE_GLASS_REAR = -1.126                 # rear door glass ends here (D-pillar behind)

# front door front edge, B-pillar split, rear door rear edge (top)
DOOR_LINES = (0.898, -0.25, -0.898)
DOOR_R_TOP_END = -1.126                  # rear door's upper part reaches over the arch
B_PILLAR = (-0.33, -0.20)

PAINT = "blue"

# ---- profile keys (Y, value), measured -----------------------------------
K = dict(
    z_top=[(2.04, .60), (2.00, .71), (1.94, .80), (1.85, .855), (1.72, .90), (1.50, .945),
           (1.25, .98), (Y_COWL, 1.02), (0.70, 1.22), (0.50, 1.33), (0.30, 1.43),
           (0.10, 1.465), (-0.30, 1.47), (-0.80, 1.46), (-1.10, 1.44), (-1.30, 1.42),
           (-1.45, 1.28), (-1.602, 1.12), (-1.70, 1.03), (-1.78, .94), (-1.84, .80)],
    z_belt=[(2.04, .56), (2.00, .665), (1.94, .75), (1.85, .80), (1.72, .845), (1.50, .885),
            (1.25, .91), (Y_COWL, .93), (0.50, .94), (0.0, .975), (-0.50, 1.02),
            (-1.10, 1.075), (-1.30, 1.08), (-1.45, 1.07), (-1.602, 1.04), (-1.70, .99),
            (-1.78, .90), (-1.84, .77)],
    x_belt=[(2.04, .22), (2.00, .42), (1.94, .56), (1.85, .66), (1.72, .72), (1.50, .74),
            (-1.10, .74), (-1.30, .73), (-1.50, .70), (-1.65, .64), (-1.78, .52), (-1.84, .36)],
    x_top=[(Y_COWL, .66), (0.60, .62), (0.30, .575), (-0.50, .555), (-1.10, .54),
           (-1.30, .52), (-1.45, .505), (-1.602, .50)],
    x_max=[(2.04, .30), (2.00, .48), (1.94, .60), (1.85, .72), (1.72, .80), (1.602, .835),
           (1.25, .845), (0.898, .835), (0.0, .83), (-0.898, .835), (-1.25, .845),
           (-1.50, .83), (-1.602, .80), (-1.72, .72), (-1.80, .55), (-1.84, .32)],
    z_mid=[(2.04, .46), (1.94, .52), (1.72, .58), (1.50, .62), (-1.50, .62), (-1.72, .66),
           (-1.84, .70)],
    z_sill=[(2.04, .30), (1.94, .26), (1.72, .24), (1.602, .22), (-1.602, .22), (-1.72, .26),
            (-1.84, .30)],
    z_floor=[(2.04, .27), (1.94, .24), (1.72, .18), (1.602, CLEARANCE), (-1.602, CLEARANCE),
             (-1.72, .20), (-1.84, .27)],
)

EXTRA_STATIONS = [2.04, 2.00, 1.94, 1.85, 1.72, 0.60, 0.30, -0.25, -0.60, -1.30,
                  -1.70, -1.78, -1.84]

SOCKETS_EXTRA = {
    "hood": (0, 1.50, .94), "roof": (0, -0.40, 1.47), "spoiler": (0, Y_ROOF_REAR, 1.42),
    "exhaust": (-0.40, Y_TAIL, .25), "grille": (0, Y_NOSE, .43),
}

# blueprint: mirror at Y~0.55, z 0.92-1.05, reaches |x| 0.97
MIRROR = dict(y=0.55, z=0.985, x_in=0.73, length=0.24, size=(0.10, 0.13))


EXTRA_PARTS = ("headlight_L", "headlight_R")


def _xb(y):
    return float(np.interp(y, *zip(*sorted(K["x_belt"]))))


def _zb(y):
    return float(np.interp(y, *zip(*sorted(K["z_belt"]))))

# Recessed features cut into the body (outlines measured on the blueprint, metres).
# ("f", x, z) ray from front, ("r", x, z) from rear, ("s", y, z) from the right side.
FEATURES = [
    # lower "smile" grille: wide top, narrow bottom, rounded upper corners
    dict(name="grille_low", kind="grille", part="bumper_F", depth=0.045, taper=0.04,
         outline=[("f", -0.36, .33), ("f", 0.36, .33), ("f", 0.42, .43), ("f", 0.45, .50),
                  ("f", 0.43, .53), ("f", 0.0, .535), ("f", -0.43, .53), ("f", -0.45, .50),
                  ("f", -0.42, .43)]),
    # upper grille: thin band between the headlight tips
    dict(name="grille_up", kind="grille", part="bumper_F", depth=0.025, taper=0.05,
         outline=[("f", -0.30, .70), ("f", -0.15, .662), ("f", 0.15, .662), ("f", 0.30, .70),
                  ("f", 0.30, .735), ("f", 0.15, .746), ("f", -0.15, .746), ("f", -0.30, .735)]),
    # fog pods (bumper corners)
    dict(name="fog", kind="fog", part="bumper_F", mirror=True, depth=0.03, taper=0.08,
         outline=[("f", 0.53, .37), ("f", 0.66, .36), ("f", 0.70, .41), ("f", 0.66, .46),
                  ("f", 0.55, .47)]),
    # headlamp: teardrop, tip at the grille, tail swept back along the fender
    dict(name="headlamp", kind="headlamp", part="headlight_{s}", mirror=True, depth=0.015,
         back="normal", taper=0.03,
         outline=[("f", 0.30, .74)]
         + [("n", _xb(y) - 0.01, y, _zb(y) - 0.012) for y in (1.95, 1.88, 1.80, 1.71, 1.62)]
         + [("s", 1.53, .845), ("s", 1.60, .825), ("s", 1.72, .775), ("s", 1.84, .715),
            ("f", 0.60, .645), ("f", 0.48, .65), ("f", 0.38, .69)]),
    # rear plate recess on the bumper
    dict(name="plate_rear", kind="recess", part="bumper_R", depth=0.02, taper=0.02,
         outline=[("r", -0.37, .60), ("r", 0.37, .60), ("r", 0.33, .52), ("r", 0.28, .47),
                  ("r", -0.28, .47), ("r", -0.33, .52)]),
]


def _tri_mesh(x, z):
    return ((np.floor(x * 64) + np.floor(z * 64)) % 2) == 0


def paint(P, N, V, glass, body_col, C, B):
    """Car-specific decals painted in 3D, coordinates measured off the blueprint.
    B: face band per texel (20 grille, 21 fog, 22 headlamp lens, 23 recess back).
    Returns int array of palette indices, -1 = keep default."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    out = np.full(len(P), -1, int)
    ng = ~glass & (B < 20)
    front = (y > 1.78) & (N[:, 1] > 0.15) & ng
    rear = (y < -1.70) & (N[:, 1] < -0.15) & ng

    # headlamp lens: projector bowl + inner chrome
    lens = B == 22
    d2 = (ax - 0.62) ** 2 + (z - 0.75) ** 2
    out[lens & (d2 < 0.045 ** 2)] = C["chrome_hi"]
    out[lens & (d2 < 0.022 ** 2)] = C["chrome"]
    out[lens & (np.abs(z - 0.70) < 0.008) & (ax < 0.55)] = C["chrome"]     # light guide
    out[lens & (y < 1.62)] = C["amber"]                                     # side marker in tail
    # fog lamp inside the pod
    out[(B == 21) & (((ax - 0.62) ** 2 + (z - 0.415) ** 2) < 0.024 ** 2)] = C["chrome_hi"]
    # emblem + VN plate on the lower grille
    out[(B == 20) & (ax < 0.035) & (np.abs(z - 0.70) < 0.025)] = C["chrome"]
    fp = (B == 20) & (ax < 0.16) & (z > 0.45) & (z < 0.53)
    out[fp] = C["plate"]
    out[fp & (np.abs(z - 0.49) < 0.018) & (ax < 0.13) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[front & (z < 0.28)] = C["plastic"]                                   # lower lip

    # --- rear ---------------------------------------------------------
    tl = (y < -1.56) & (ax > 0.46) & (z > 0.86) & (z < 1.05) & ng & \
        (z > 0.86 + np.clip(0.74 - ax, 0, 1) * 0.25)
    out[tl] = C["tail"]
    out[tl & (z > 0.97)] = C["tail_hi"]
    out[tl & (ax > 0.66) & (z < 0.92)] = C["amber"]
    # tailgate lower shut line, plate recess, plate
    out[rear & (np.abs(z - 0.72) < 0.009) & (ax < 0.48)] = C["seam_" + PAINT]
    rp = (B == 23) & (ax < 0.16) & (z > 0.475) & (z < 0.585)
    out[rp] = C["plate"]
    out[rp & (np.abs(z - 0.525) < 0.022) & (ax < 0.13) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[rear & (z < 0.34)] = C["plastic"]                                   # diffuser
    out[rear & (np.abs(z - 0.37) < 0.012) & (ax < 0.43)] = C["black"]        # black stripe
    out[rear & (ax > 0.53) & (ax < 0.62) & (z > 0.40) & (z < 0.44)] = C["tail"]   # reflectors
    out[(y < -1.25) & (y > -1.42) & (z > 1.40) & ng & (N[:, 2] > 0.3)] = C["black"]  # spoiler lip

    # --- sides --------------------------------------------------------
    side = (np.abs(N[:, 0]) > 0.5) & ng
    zb = np.interp(y, *zip(*sorted(K["z_belt"])))
    # door handles (blueprint: front Y 0.20..0.36, rear Y -0.95..-0.78, ~0.11-0.14 under belt)
    for y0, y1 in ((0.20, 0.36), (-0.95, -0.78)):
        out[side & (y > y0) & (y < y1) & (z > zb - 0.135) & (z < zb - 0.10)] = C["black"]
    out[side & (np.abs(y - 0.98) < 0.025) & (np.abs(z - 0.68) < 0.012)] = C["amber"]  # repeater
    # fuel door, right rear quarter
    fd = side & (x > 0) & (np.abs(np.hypot(y + 1.45, z - 0.82) - 0.065) < 0.009)
    out[fd] = C["seam_" + PAINT]
    # rocker: black side-skirt strip
    out[side & (z < 0.27) & (y < 1.55) & (y > -1.55)] = C["plastic"]
    return out


# ---- swappable parts & aftermarket variants -------------------------------
# Every variant is built from the same profile, so its joint edges are the stock ones:
# it drops onto the stock car without fitting work.
SWAP_PARTS = ("bumper_F", "bumper_R", "skirt_L", "skirt_R")

_LIP_K = dict(
    z_sill=[(2.04, .25), (1.94, .21), (1.72, .20)],
    z_floor=[(2.04, .22), (1.94, .19), (1.72, .16)],
)

VARIANTS = {
    # front lip: bumper drops ~4-5 cm, lower edge painted black plastic
    "lip": dict(parts=["bumper_F"], K=_LIP_K),
    # sport: lip + wider/taller smile + vertical corner intakes instead of fog pods
    "sport": dict(
        parts=["bumper_F"], K=_LIP_K,
        features_remove=("grille_low", "fog"),
        features_add=[
            dict(name="grille_sport", kind="grille", part="bumper_F", depth=0.06, taper=0.03,
                 outline=[("f", -0.42, .27), ("f", 0.42, .27), ("f", 0.50, .42), ("f", 0.52, .52),
                          ("f", 0.48, .55), ("f", 0.0, .555), ("f", -0.48, .55), ("f", -0.52, .52),
                          ("f", -0.50, .42)]),
            dict(name="intake", kind="grille", part="bumper_F", mirror=True, depth=0.05,
                 taper=0.06,
                 outline=[("f", 0.57, .27), ("f", 0.68, .27), ("f", 0.72, .36), ("f", 0.70, .50),
                          ("f", 0.60, .50), ("f", 0.56, .40)]),
        ]),
    # rear diffuser: bumper drops, four channels cut in the lower edge
    "diffuser": dict(
        parts=["bumper_R"],
        K=dict(z_sill=[(-1.72, .22), (-1.84, .23)], z_floor=[(-1.72, .17), (-1.84, .20)]),
        features_add=[
            dict(name=f"diff{i}", kind="grille", part="bumper_R", depth=0.05,
                 outline=[("r", x0, .235), ("r", x0 + 0.10, .235), ("r", x0 + 0.10, .30),
                          ("r", x0, .30)])
            for i, x0 in enumerate((-0.40, -0.17, 0.07, 0.30))]),
    # side skirts: rocker drops 4.5 cm, door edge untouched
    "skirt": dict(parts=["skirt_L", "skirt_R"], set=dict(SKIRT_DROP=0.045)),
}
