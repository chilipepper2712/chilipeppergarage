"""Mazda CX-5 (KF) 2.0 2WD, 2020, VN-assembled.

Units: metres. Axes: Z up, +Y forward, +X = right side of driver. Origin: ground, centre of wheelbase.

Dimensions (bonbanh, 2.0 Premium 2020): 4550 x 1840 x 1680, WB 2700, clearance 200, tyre 225/55R19.
Tracks 1595/1595: NOT verified (from memory) -> TBD.
Profile MEASURED from blueprints/cx5_2020/blueprint.png (side view 193.3 px/m, calibrated on the
wheelbase; length 4.537 / height 1.67 check out). The front/rear views are drawn 4% larger than the
side view (body 1.913 m wide vs 1.840 spec), so their readings are divided by 1.04.
Texture painted in the KEY ramp (blue); the viewer applies the car's default colour.
"""
import numpy as np

NAME = "cx5_2020"
LENGTH, WIDTH, HEIGHT = 4.550, 1.840, 1.680
WHEELBASE = 2.700
TRACK_F, TRACK_R = 1.595, 1.595          # TBD - unverified
TYRE = (225, 55, 19)
CLEARANCE = 0.200
ARCH_R = 0.43

Y_NOSE, Y_TAIL = 2.28, -2.25
AXLES = (WHEELBASE / 2, -WHEELBASE / 2)

Y_COWL = 1.049
Y_ROOF_FRONT = 0.12
Y_ROOF_REAR = -1.78                      # end of the roof spoiler
Y_REAR_GLASS_BOT = -2.06
Y_HOOD_FRONT = 2.26
SIDE_GLASS_REAR = -1.5005                # small rear quarter glass ends here

DOOR_LINES = (0.92, -0.33, -0.92)
DOOR_R_TOP_END = -1.1995
B_PILLAR = (-0.41, -0.25)

PAINT = "blue"
DEFAULT_PAINT = "red"

K = dict(
    z_top=[(2.28, .86), (2.24, .93), (2.14, .97), (2.0, 1.015), (1.78, 1.063), (1.5, 1.105),
           (1.35, 1.13), (1.2, 1.146), (Y_COWL, 1.142), (0.92, 1.20), (0.7, 1.348), (0.48, 1.46),
           (0.26, 1.56), (Y_ROOF_FRONT, 1.596), (-0.25, 1.643), (-0.6, 1.648), (-1.0, 1.632),
           (-1.35, 1.612), (-1.5, 1.59), (Y_ROOF_REAR, 1.55), (-1.85, 1.43), (-1.98, 1.33),
           (Y_REAR_GLASS_BOT, 1.27), (-2.16, 1.23), (-2.25, 1.10)],
    z_belt=[(2.28, .82), (2.24, .90), (2.14, .95), (2.0, 1.0), (1.78, 1.035), (1.5, 1.07),
            (1.2, 1.10), (Y_COWL, 1.12), (0.85, 1.155), (0.0, 1.175), (-1.2, 1.21), (-1.5, 1.23),
            (Y_ROOF_REAR, 1.24), (Y_REAR_GLASS_BOT, 1.20), (-2.16, 1.15), (-2.25, 1.04)],
    x_belt=[(2.28, .50), (2.24, .62), (2.14, .72), (2.0, .80), (1.78, .84), (1.5, .85),
            (-1.5, .85), (Y_ROOF_REAR, .84), (Y_REAR_GLASS_BOT, .80), (-2.16, .74), (-2.25, .58)],
    x_top=[(Y_COWL, .66), (0.6, .60), (0.0, .56), (-1.0, .55), (-1.5, .52), (Y_ROOF_REAR, .50),
           (-1.98, .53), (Y_REAR_GLASS_BOT, .56)],
    x_max=[(2.28, .55), (2.24, .66), (2.14, .76), (2.0, .85), (1.78, .90), (1.5, .92), (1.35, .92),
           (0.0, .915), (-1.35, .92), (-1.78, .91), (-2.06, .87), (-2.16, .81), (-2.25, .66)],
    z_mid=[(2.28, .55), (2.14, .62), (1.78, .72), (1.5, .78), (-1.5, .80), (-2.06, .80), (-2.25, .70)],
    z_sill=[(2.28, .32), (2.14, .27), (1.78, .24), (0.92, .21), (-0.92, .21), (-1.78, .27),
            (-2.06, .31), (-2.25, .36)],
    z_floor=[(2.28, .30), (2.14, .25), (1.78, .21), (0.92, CLEARANCE), (-0.92, CLEARANCE),
             (-1.78, .22), (-2.06, .28), (-2.25, .34)],
)

EXTRA_STATIONS = [2.28, 2.24, 2.14, 2.0, 0.7, 0.48, 0.26, 0.12, -0.33, -0.6, -1.0, -1.85, -1.98,
                  -2.06, -2.16, -2.25]

SOCKETS_EXTRA = {
    "hood": (0, 1.7, 1.09), "roof": (0, -0.5, 1.648), "spoiler": (0, Y_ROOF_REAR, 1.55),
    "exhaust": (0.56, Y_TAIL, .37), "grille": (0, Y_NOSE, .78),
}
MIRROR = dict(y=0.47, z=1.21, x_in=0.80, length=0.22, size=(0.11, 0.12))
EXTRA_PARTS = ("headlight_L", "headlight_R")
SWAP_PARTS = ("bumper_F", "bumper_R", "skirt_L", "skirt_R")


def _xb(y):
    return float(np.interp(y, *zip(*sorted(K["x_belt"]))))


def _zb(y):
    return float(np.interp(y, *zip(*sorted(K["z_belt"]))))


FEATURES = [
    # big shield grille (front view, /1.04)
    dict(name="grille", kind="grille", part="bumper_F", depth=0.05, taper=0.03,
         outline=[("f", -0.44, .93), ("f", 0.44, .93), ("f", 0.48, .86), ("f", 0.38, .70),
                  ("f", 0.22, .625), ("f", 0.0, .615), ("f", -0.22, .625), ("f", -0.38, .70),
                  ("f", -0.48, .86)]),
    # lower intake under the plate
    dict(name="grille_low", kind="grille", part="bumper_F", depth=0.04, taper=0.04,
         outline=[("f", -0.42, .40), ("f", 0.42, .40), ("f", 0.40, .50), ("f", -0.40, .50)]),
    # slim headlamps: inner tip at the grille corner, top edge on the hood shut line
    dict(name="headlamp", kind="headlamp", part="headlight_{s}", mirror=True, depth=0.015,
         back="normal", taper=0.03,
         outline=[("f", 0.49, .885)]
         + [("n", _xb(y) - 0.01, y, _zb(y) - 0.012) for y in (2.24, 2.18, 2.10, 2.02, 1.95)]
         + [("s", 1.96, .935), ("s", 2.08, .885), ("f", 0.80, .835), ("f", 0.62, .835), ("f", 0.53, .855)]),
    # plate recess on the tailgate
    dict(name="plate_rear", kind="recess", part="tailgate", depth=0.02, taper=0.02,
         outline=[("r", -0.20, .83), ("r", 0.20, .83), ("r", 0.20, .985), ("r", -0.20, .985)]),
]


def paint(P, N, V, glass, body_col, C, B):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    out = np.full(len(P), -1, int)
    ng = ~glass & (B < 20)
    front = (y > 2.05) & (N[:, 1] > 0.15) & ng
    rear = (y < -2.05) & (N[:, 1] < -0.15) & ng
    side = (np.abs(N[:, 0]) > 0.5) & ng

    lens = B == 22
    d2 = (ax - 0.70) ** 2 + (z - 0.89) ** 2
    out[lens & (d2 < 0.035 ** 2)] = C["chrome_hi"]
    out[lens & (np.abs(z - 0.865) < 0.008)] = C["chrome"]                     # DRL light guide
    out[(B == 20) & (ax < 0.07) & (np.abs(z - 0.80) < 0.06)] = C["chrome"]    # badge
    out[(B == 20) & (np.abs(z - 0.62 - 0.04 * (ax / 0.38) ** 2) < 0.012)] = C["chrome"]   # signature wing
    fp = front & (ax < 0.165) & (z > 0.365) & (z < 0.51)
    out[fp] = C["plate"]
    out[fp & (np.abs(z - 0.44) < 0.02) & (ax < 0.13) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[front & (ax > 0.48) & (ax < 0.82) & (np.abs(z - 0.495) < 0.012)] = C["light_w"]  # fog/DRL strips
    out[front & (z < 0.29)] = C["plastic"]

    tl = (y < -1.85) & (ax > 0.45) & (z > 1.02) & (z < 1.18) & ng
    out[tl] = C["tail"]
    out[tl & (z > 1.13)] = C["tail_hi"]
    out[tl & (((ax - 0.72) ** 2 + (z - 1.10) ** 2) < 0.03 ** 2)] = C["tail_hi"]
    rp = (B == 23) & (ax < 0.15) & (z > 0.84) & (z < 0.975)
    out[rp] = C["plate"]
    out[rp & (np.abs(z - 0.91) < 0.02) & (ax < 0.12) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[rear & (np.abs(z - 1.08) < 0.03) & (ax < 0.07)] = C["chrome"]         # badge
    out[rear & (z < 0.37)] = C["plastic"]
    tips = rear & (((ax - 0.56) ** 2 + (z - 0.37) ** 2) < 0.042 ** 2)
    out[tips] = C["chrome"]
    out[rear & (((ax - 0.56) ** 2 + (z - 0.37) ** 2) < 0.026 ** 2)] = C["black"]

    # black cladding: wheel-arch flares + rocker
    for ya in AXLES:
        r = np.hypot(y - ya, z - TYRE_R)
        out[side & (r < ARCH_R + 0.07) & (r > ARCH_R - 0.06) & (z > 0.2)] = C["plastic"]
    out[side & (z < 0.33) & (y < 1.8) & (y > -1.8)] = C["plastic"]
    zb = np.interp(y, *zip(*sorted(K["z_belt"])))
    for y0, y1 in ((-0.23, 0.0), (-1.04, -0.81)):
        out[side & (y > y0) & (y < y1) & (z > zb - 0.20) & (z < zb - 0.165)] = C["black"]
    fd = side & (x > 0) & (np.abs(y + 1.55) < 0.11) & (np.abs(z - 0.98) < 0.08) & \
        ((np.abs(np.abs(y + 1.55) - 0.11) < 0.009) | (np.abs(np.abs(z - 0.98) - 0.08) < 0.009))
    out[fd] = C["seam_" + PAINT]
    return out


TYRE_R = (TYRE[2] * 25.4 + 2 * TYRE[0] * TYRE[1] / 100) / 2000

_LIP_K = dict(z_sill=[(2.28, .29), (2.14, .24), (1.85, .23)], z_floor=[(2.28, .27), (2.14, .21), (1.85, .20)])
VARIANTS = {
    "lip": dict(parts=["bumper_F"], K=_LIP_K),
    "sport": dict(
        parts=["bumper_F"], K=_LIP_K, features_remove=("grille_low",),
        features_add=[
            dict(name="grille_sport", kind="grille", part="bumper_F", depth=0.06, taper=0.03,
                 outline=[("f", -0.52, .33), ("f", 0.52, .33), ("f", 0.56, .52), ("f", -0.56, .52)]),
            dict(name="intake", kind="grille", part="bumper_F", mirror=True, depth=0.05, taper=0.06,
                 outline=[("f", 0.62, .34), ("f", 0.80, .34), ("f", 0.84, .45), ("f", 0.66, .52), ("f", 0.60, .44)]),
        ]),
    "diffuser": dict(
        parts=["bumper_R"],
        K=dict(z_sill=[(-2.06, .27), (-2.25, .31)], z_floor=[(-2.06, .23), (-2.25, .28)]),
        features_add=[
            dict(name=f"diff{i}", kind="grille", part="bumper_R", depth=0.05,
                 outline=[("r", x0, .315), ("r", x0 + 0.12, .315), ("r", x0 + 0.12, .375), ("r", x0, .375)])
            for i, x0 in enumerate((-0.40, -0.15, 0.03, 0.28))]),
    "skirt": dict(parts=["skirt_L", "skirt_R"], set=dict(SKIRT_DROP=0.045)),
}
