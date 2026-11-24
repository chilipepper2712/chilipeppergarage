"""Mitsubishi Xpander 1.5 AT, 2020 (MPV, 7 seats) - representative model for the MPV body type.

Units: metres. Axes: Z up, +Y forward, +X = right side of driver. Origin: ground, centre of wheelbase.

Dimensions (data/garage-db.json): 4475 x 1750 x 1730, WB 2775, clearance 205, tyre 205/55R16.
The blueprint's own dimension lines read 4500 x 1800 x 1750 (with roof rails and arch flares) and tracks
1520 / 1510; those tracks are used here.
Profile MEASURED from blueprints/xpander_2020/blueprint.jpg (CAD line drawing, side/front/rear only,
79.9 px/m calibrated on the wheelbase). There is no top view: plan widths are read from the front and rear
views at each height and interpolated along the car, so the plan taper at the corners is an estimate.
The image is small (655 px wide, ~12 mm per pixel), fine for the low-poly look but not for small details.
Texture painted in the KEY ramp (blue); the viewer applies the car's default colour.
"""
import numpy as np

NAME = "xpander_2020"
LENGTH, WIDTH, HEIGHT = 4.475, 1.750, 1.730
WHEELBASE = 2.775
TRACK_F, TRACK_R = 1.520, 1.510          # blueprint dimension lines
TYRE = (205, 55, 16)
CLEARANCE = 0.205
ARCH_R = 0.40

Y_NOSE, Y_TAIL = 2.21, -2.28
AXLES = (WHEELBASE / 2, -WHEELBASE / 2)

Y_COWL = 1.50                            # long, low hood meets a very raked windscreen
Y_ROOF_FRONT = 0.43
Y_ROOF_REAR = -2.00                      # end of the roof spoiler
Y_REAR_GLASS_BOT = -2.19
Y_HOOD_FRONT = 2.19
SIDE_GLASS_REAR = -1.95                  # rear quarter glass runs almost to the tailgate

DOOR_LINES = (0.97, 0.36, -1.21)
DOOR_R_TOP_END = -1.21
B_PILLAR = (0.30, 0.42)

PAINT = "blue"
DEFAULT_PAINT = "white"

K = dict(
    z_top=[(2.21, .90), (2.18, .94), (2.0, 1.01), (1.8, 1.06), (1.6, 1.11), (Y_COWL, 1.14),
           (1.2, 1.27), (0.9, 1.40), (0.6, 1.55), (Y_ROOF_FRONT, 1.63), (0.2, 1.675), (-0.5, 1.69),
           (-1.5, 1.685), (-1.85, 1.675), (Y_ROOF_REAR, 1.64), (-2.1, 1.47), (Y_REAR_GLASS_BOT, 1.24),
           (-2.25, 1.12), (-2.28, 1.0)],
    z_belt=[(2.21, .88), (2.18, .92), (2.0, .99), (1.7, 1.06), (Y_COWL, 1.09), (1.15, 1.10),
            (0.5, 1.14), (0.0, 1.165), (-1.0, 1.18), (-1.4, 1.25), (-1.8, 1.28), (-2.1, 1.24),
            (Y_REAR_GLASS_BOT, 1.20), (-2.25, 1.08), (-2.28, .98)],
    x_belt=[(2.21, .50), (2.18, .62), (2.1, .72), (1.9, .79), (1.5, .815), (-1.8, .815),
            (-2.1, .78), (Y_REAR_GLASS_BOT, .74), (-2.25, .68), (-2.28, .56)],
    x_top=[(Y_COWL, .70), (Y_ROOF_FRONT, .63), (0.0, .62), (-1.5, .62), (-1.9, .60),
           (-2.1, .58), (Y_REAR_GLASS_BOT, .62)],
    x_max=[(2.21, .56), (2.18, .68), (2.1, .79), (1.9, .865), (1.6, .885), (0.0, .875),
           (-1.7, .885), (-2.0, .87), (Y_REAR_GLASS_BOT, .81), (-2.25, .75), (-2.28, .64)],
    z_mid=[(2.21, .55), (2.1, .62), (1.8, .72), (1.5, .78), (-1.5, .80), (-2.1, .80), (-2.28, .72)],
    z_sill=[(2.21, .36), (2.1, .30), (1.8, .28), (0.97, .27), (-1.0, .27), (-1.9, .30),
            (-2.1, .33), (-2.28, .42)],
    z_floor=[(2.21, .33), (2.1, .27), (1.8, .24), (0.97, CLEARANCE), (-1.0, CLEARANCE),
             (-1.9, .26), (-2.1, .30), (-2.28, .40)],
)

EXTRA_STATIONS = [2.21, 2.18, 2.1, 2.0, 1.2, 0.9, 0.6, 0.43, 0.2, -0.5, -1.4, -1.85, -2.0, -2.1,
                  -2.19, -2.25, -2.28]

SOCKETS_EXTRA = {
    "hood": (0, 1.85, 1.05), "roof": (0, -0.6, 1.69), "spoiler": (0, Y_ROOF_REAR, 1.64),
    "exhaust": (0.45, Y_TAIL, .40), "grille": (0, Y_NOSE, .73),
}
MIRROR = dict(y=1.27, z=1.17, x_in=0.80, length=0.21, size=(0.11, 0.12))
EXTRA_PARTS = ("headlight_L", "headlight_R")
SWAP_PARTS = ("bumper_F", "bumper_R", "skirt_L", "skirt_R")


def _xb(y):
    return float(np.interp(y, *zip(*sorted(K["x_belt"]))))


def _zb(y):
    return float(np.interp(y, *zip(*sorted(K["z_belt"]))))


FEATURES = [
    # "Dynamic Shield": chrome-framed upper grille bar between the lamp pods
    dict(name="grille", kind="grille", part="bumper_F", depth=0.04, taper=0.03,
         outline=[("f", -0.26, .785), ("f", 0.26, .785), ("f", 0.26, .675), ("f", -0.26, .675)]),
    # wide lower grille under it
    dict(name="grille_low", kind="grille", part="bumper_F", depth=0.05, taper=0.04,
         outline=[("f", -0.38, .53), ("f", 0.38, .53), ("f", 0.36, .31), ("f", -0.36, .31)]),
    # main headlamp pods, low and square, set into the bumper corners
    dict(name="headlamp", kind="headlamp", part="headlight_{s}", mirror=True, depth=0.02,
         back="normal", taper=0.03,
         outline=[("f", 0.51, .86), ("f", 0.78, .86), ("f", 0.80, .60), ("f", 0.53, .57)]),
    # plate recess on the tailgate
    dict(name="plate_rear", kind="recess", part="tailgate", depth=0.02, taper=0.02,
         outline=[("r", -0.20, .70), ("r", 0.20, .70), ("r", 0.20, .83), ("r", -0.20, .83)]),
]


def paint(P, N, V, glass, body_col, C, B):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    ax = np.abs(x)
    out = np.full(len(P), -1, int)
    ng = ~glass & (B < 20)
    front = (y > 1.95) & (N[:, 1] > 0.15) & ng
    rear = (y < -2.05) & (N[:, 1] < -0.15) & ng
    side = (np.abs(N[:, 0]) > 0.5) & ng

    lens = B == 22
    out[lens & (np.abs(z - 0.80) < 0.03)] = C["chrome_hi"]                     # projector row
    out[lens & (np.abs(z - 0.66) < 0.012)] = C["chrome"]
    # slim LED daytime lamps high up on the shield, along the hood shut line
    out[front & (ax > 0.42) & (ax < 0.80) & (np.abs(z - 0.94 + 0.05 * (ax - 0.42)) < 0.014)] = C["light_w"]
    # chrome "X" shield arms wrapping the grille
    arm = front & (ax > 0.26) & (ax < 0.50) & (np.abs(z - (0.70 - 0.35 * (ax - 0.26))) < 0.016)
    out[arm] = C["chrome"]
    out[(B == 20) & (np.abs(z - 0.73) < 0.012)] = C["chrome"]
    out[front & (ax < 0.07) & (np.abs(z - 0.86) < 0.04)] = C["chrome"]         # badge
    fp = front & (ax < 0.165) & (z > 0.37) & (z < 0.49)
    out[fp] = C["plate"]
    out[fp & (np.abs(z - 0.43) < 0.02) & (ax < 0.13) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    fog = front & (((ax - 0.52) ** 2 + (z - 0.44) ** 2) < 0.045 ** 2)
    out[fog] = C["light_w"]
    out[front & (z < 0.30)] = C["plastic"]

    # L-shaped tail lamps: horizontal bar on the tailgate edge + vertical leg down the D-pillar
    tl = (y < -2.0) & ng & (((ax > 0.30) & (ax < 0.62) & (z > 1.08) & (z < 1.23)) |
                            ((ax > 0.56) & (z > 0.92) & (z < 1.23)))
    out[tl] = C["tail"]
    out[tl & (z > 1.18)] = C["tail_hi"]
    out[rear & (ax > 0.66) & (z > 0.51) & (z < 0.72) & (ax < 0.76)] = C["tail"]   # bumper reflectors
    rp = (B == 23) & (ax < 0.15) & (z > 0.71) & (z < 0.82)
    out[rp] = C["plate"]
    out[rp & (np.abs(z - 0.765) < 0.02) & (ax < 0.12) & ((np.floor(x * 64) % 3) != 0)] = C["black"]
    out[rear & (np.abs(z - 1.02) < 0.035) & (ax < 0.06)] = C["chrome"]           # badge
    out[rear & (np.abs(z - 0.90) < 0.008) & (ax < 0.48)] = C["chrome"]           # tailgate garnish
    out[rear & (z < 0.45)] = C["plastic"]

    # heavy black cladding: arch flares, rocker, lower doors
    for ya in AXLES:
        r = np.hypot(y - ya, z - TYRE_R)
        out[side & (r < ARCH_R + 0.08) & (r > ARCH_R - 0.05) & (z > 0.2)] = C["plastic"]
    out[side & (z < 0.36) & (y < 1.9) & (y > -1.9)] = C["plastic"]
    # door handles
    zb = np.interp(y, *zip(*sorted(K["z_belt"])))
    for y0, y1 in ((0.47, 0.62), (-0.95, -0.80)):
        out[side & (y > y0) & (y < y1) & (z > zb - 0.14) & (z < zb - 0.11)] = C["black"]
    # fuel door, right rear quarter
    fd = side & (x > 0) & (np.abs(y + 1.75) < 0.09) & (np.abs(z - 0.95) < 0.07) & \
        ((np.abs(np.abs(y + 1.75) - 0.09) < 0.009) | (np.abs(np.abs(z - 0.95) - 0.07) < 0.009))
    out[fd] = C["seam_" + PAINT]
    return out


TYRE_R = (TYRE[2] * 25.4 + 2 * TYRE[0] * TYRE[1] / 100) / 2000

_LIP_K = dict(z_sill=[(2.21, .33), (2.1, .27), (1.85, .26)], z_floor=[(2.21, .30), (2.1, .24), (1.85, .225)])
VARIANTS = {
    "lip": dict(parts=["bumper_F"], K=_LIP_K),
    "sport": dict(
        parts=["bumper_F"], K=_LIP_K, features_remove=("grille_low",),
        features_add=[
            dict(name="grille_sport", kind="grille", part="bumper_F", depth=0.06, taper=0.03,
                 outline=[("f", -0.46, .30), ("f", 0.46, .30), ("f", 0.42, .52), ("f", -0.42, .52)]),
            dict(name="intake", kind="grille", part="bumper_F", mirror=True, depth=0.05, taper=0.06,
                 outline=[("f", 0.56, .31), ("f", 0.78, .31), ("f", 0.80, .42), ("f", 0.60, .48)]),
        ]),
    "diffuser": dict(
        parts=["bumper_R"],
        K=dict(z_sill=[(-2.1, .29), (-2.28, .36)], z_floor=[(-2.1, .26), (-2.28, .33)]),
        features_add=[
            dict(name=f"diff{i}", kind="grille", part="bumper_R", depth=0.05,
                 outline=[("r", x0, .35), ("r", x0 + 0.12, .35), ("r", x0 + 0.12, .41), ("r", x0, .41)])
            for i, x0 in enumerate((-0.40, -0.15, 0.03, 0.28))]),
    "skirt": dict(parts=["skirt_L", "skirt_R"], set=dict(SKIRT_DROP=0.045)),
}
