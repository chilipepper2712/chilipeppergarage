"""Home-built wind tunnel room (reference: hobby tunnel with a big fan, safety grille, hazard-striped
turntable; built from OSB, egg-crate foam and LED strips rather than a pro facility).

Same rules as the garage: metres, Z up, 64 px/m tileable pixel textures, world-metre UVs.
The car sits at the origin with its nose toward -Y (the viewer turns every car to face the open side);
the fan is in front of the nose at -Y and blows toward +Y. Output: out/env/tunnel.glb + tunnel_anchors.json.
"""
import os, sys, math, json
import numpy as np
import bpy, bmesh
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import garage_env as GE
from garage_env import Builder, shade, noise, blobs, hx, t_emit, t_steel, t_yellow, t_simple, RNG

OUT, TEX_DIR = GE.OUT, GE.TEX_DIR
W, Y0, Y1, H = 3.4, -7.2, 6.6, 3.6          # half width, fan end, back wall, ceiling
FAN_Y, FAN_Z, FAN_R = -5.7, 1.55, 1.38


def t_osb():
    n = 64
    img = shade(["#7a5a33", "#93703f", "#a9824b", "#bf9659", "#d1a96a"], 0.55 + noise(n, .35), spread=1.0)
    yy, xx = np.mgrid[0:n, 0:n]
    for _ in range(60):                                    # pressed strands
        x, y = RNG.integers(0, n, 2); L = RNG.integers(3, 8)
        img[y % n, (x + np.arange(L)) % n] = hx(RNG.choice(["#5f4426", "#c99d5c", "#8a6638"]))
    img[(xx == 0) | (yy == 0)] = hx("#4a3620")            # panel seams every metre
    return img


def t_foam():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx % 16) / 16 - .5, (yy % 16) / 16 - .5        # pyramids, 25 cm
    lum = 0.55 + 0.35 * np.where(np.abs(u) > np.abs(v), np.sign(u) * .6, -np.sign(v) * .8) * (np.maximum(np.abs(u), np.abs(v)) > .05)
    return shade(["#1c1d20", "#26282c", "#33363b", "#43474d"], lum + noise(n, .08), spread=.4)


def t_diamond():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#3b3f44", "#53585f", "#6c727a", "#8a9099"], 0.55 + noise(n, .12) - blobs(n, 3, 12, .12))
    a = ((xx + yy) % 8 < 2) & ((xx // 4 + yy // 4) % 2 == 0)
    b = ((xx - yy) % 8 < 2) & ((xx // 4 + yy // 4) % 2 == 1)
    img[a | b] = hx("#a7adb5")
    return img


def t_hazard():
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = np.where((((xx + yy) // 8) % 2 == 0)[..., None], np.array(hx("#e2b21c"), np.uint8), np.array(hx("#16161a"), np.uint8))
    worn = RNG.random((n, n)) < .06
    img[worn] = hx("#6b6b62")
    return img.astype(np.uint8)


def t_canvas():
    return t_simple(["#5e5a45", "#757055", "#8b8565", "#9f9975"])


def t_fanblade():
    n = 64
    return shade(["#2a2d31", "#3a3e44", "#50555c", "#6a7078"], 0.5 + noise(n, .15) - blobs(n, 2, 10, .1))


TEXTURES = {
    "osb": t_osb, "foam": t_foam, "diamond": t_diamond, "hazard": t_hazard, "epoxy": GE.t_epoxy,
    "steel": t_steel, "yellow": t_yellow, "rubber": GE.TEXTURES["rubber"], "canvas": t_canvas,
    "fanblade": t_fanblade, "paper": GE.TEXTURES["paper"], "red": GE.TEXTURES["red"],
    "EMIT_led": lambda: t_emit("#e8f1ff"), "EMIT_fan": lambda: t_emit("#fff2d8"), "EMIT_screen": lambda: t_emit("#7fd0ff"),
}


def build():
    B = Builder()
    # shell: epoxy floor, OSB side walls and ceiling, foam back wall
    B.quad("epoxy", [(-W, Y0, 0), (W, Y0, 0), (W, Y1, 0), (-W, Y1, 0)])
    B.quad("osb", [(-W, Y0, 0), (-W, Y1, 0), (-W, Y1, H), (-W, Y0, H)])
    B.quad("osb", [(W, Y0, 0), (W, Y0, H), (W, Y1, H), (W, Y1, 0)])
    B.quad("osb", [(-W, Y0, H), (-W, Y1, H), (W, Y1, H), (W, Y0, H)])
    B.quad("foam", [(-W, Y1, 0), (-W, Y1, H), (W, Y1, H), (W, Y1, 0)], flip=True)
    B.quad("osb", [(-W, Y0, 0), (W, Y0, 0), (W, Y0, H), (-W, Y0, H)], flip=True)
    for x in (-W + .02, W - .02):                          # foam patches glued on the side walls
        for y0 in (-1.6, 1.4):
            sgn = 1 if x < 0 else -1
            B.quad("foam", [(x, y0, .9), (x, y0 + 2.2, .9), (x, y0 + 2.2, 2.9), (x, y0, 2.9)][::sgn])
    # studs and ceiling joists (2x4 look)
    for y in np.arange(Y0 + .6, Y1, 1.22):
        B.box("osb", (-W, y, H - .14), (W, y + .09, H))
    # LED strips along the ceiling
    for x in (-1.3, 0.0, 1.3):
        B.box("EMIT_led", (x - .04, -3.6, H - .2), (x + .04, 4.6, H - .17))
        B.box("steel", (x - .06, -3.6, H - .17), (x + .06, 4.6, H - .14))

    # turntable: diamond plate disc with a hazard ring
    B.cyl("diamond", (0, 0, 0), 2.55, .035, 32)
    seg = 40
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        r0, r1 = 2.55, 2.85
        B.quad("hazard", [(r0 * math.cos(a0), r0 * math.sin(a0), .006), (r1 * math.cos(a0), r1 * math.sin(a0), .006),
                          (r1 * math.cos(a1), r1 * math.sin(a1), .006), (r0 * math.cos(a1), r0 * math.sin(a1), .006)])
    # hazard lane to the fan
    for x in (-2.2, 2.2):
        B.quad("hazard", [(x - .09, Y0 + .3, .005), (x + .09, Y0 + .3, .005), (x + .09, -2.9, .005), (x - .09, -2.9, .005)])

    # fan: square steel frame, round shroud, motor pod, backlight; blades are their own object
    fy = FAN_Y
    B.box("steel", (-1.7, fy - .35, 0), (-1.55, fy + .15, 3.1))
    B.box("steel", (1.55, fy - .35, 0), (1.7, fy + .15, 3.1))
    B.box("steel", (-1.7, fy - .35, 2.95), (1.7, fy + .15, 3.1))
    B.box("steel", (-1.7, fy - .35, 0), (1.7, fy + .15, .15))
    B.cyl("steel", (0, fy - .3, FAN_Z), FAN_R + .07, .5, 28, axis="y", caps=False)
    B.cyl("steel", (0, fy - .45, FAN_Z), .26, .35, 12, axis="y")
    B.cyl("EMIT_fan", (0, fy - .62, FAN_Z), FAN_R, .02, 28, axis="y")       # light glowing through the blades
    for k in range(8):                                                        # motor struts
        a = k * math.pi / 4
        B.beam("steel", (0, fy - .35, FAN_Z), (FAN_R * math.cos(a), fy - .35, FAN_Z + FAN_R * math.sin(a)), .03)
    # safety grille: concentric rings + spokes in front of the blades
    for r in (0.35, 0.65, 0.95, 1.25):
        n = 24
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            B.beam("steel", (r * math.cos(a0), fy + .22, FAN_Z + r * math.sin(a0)), (r * math.cos(a1), fy + .22, FAN_Z + r * math.sin(a1)), .012)
    for k in range(12):
        a = k * math.pi / 6
        B.beam("steel", (.1 * math.cos(a), fy + .22, FAN_Z + .1 * math.sin(a)), (FAN_R * math.cos(a), fy + .22, FAN_Z + FAN_R * math.sin(a)), .012)
    # flow fence: chain-link panel on posts between fan and car
    for x in (-1.9, 0.0, 1.9):
        B.box("steel", (x - .03, -4.25, 0), (x + .03, -4.19, 2.5))
    for z in np.arange(.25, 2.5, .22):
        B.beam("steel", (-1.9, -4.22, z), (1.9, -4.22, z), .008)
    for x in np.arange(-1.9, 1.95, .22):
        B.beam("steel", (x, -4.22, .1), (x, -4.22, 2.5), .008)

    # props: sandbags on the fan frame feet, smoke wand on a tripod, laptop desk, cable reel
    for x in (-1.62, 1.62):
        for k in range(3):
            B.box("canvas", (x - .28, fy + .2 + k * .02, .0 + k * .13), (x + .28, fy + .55, .13 + k * .13))
    tx, ty = -1.75, -3.2
    for k in range(3):
        a = k * 2 * math.pi / 3
        B.beam("steel", (tx, ty, 1.1), (tx + .4 * math.cos(a), ty + .4 * math.sin(a), 0), .025)
    B.beam("steel", (tx, ty, 1.0), (tx, ty, 1.35), .03)
    B.beam("steel", (tx, ty, 1.3), (-.55, -2.65, .95), .02)                  # wand reaching the nose
    B.box("red", (tx - .2, ty - .2, 0), (tx + .2, ty + .2, .3))               # smoke machine
    B.box("osb", (1.9, 3.6, .74), (3.2, 4.4, .78))                            # desk
    for x in (1.95, 3.1):
        for y in (3.65, 4.3):
            B.box("steel", (x, y, 0), (x + .04, y + .04, .74))
    B.box("steel", (2.3, 3.9, .78), (2.75, 4.2, .8))                          # laptop base
    B.quad("EMIT_screen", [(2.3, 4.2, .8), (2.75, 4.2, .8), (2.75, 4.25, 1.08), (2.3, 4.25, 1.08)])
    B.cyl("yellow", (-2.8, 4.6, 0), .3, .25, 14)                              # cable reel
    B.cyl("rubber", (-2.8, 4.6, .25), .32, .04, 14)
    for i in range(3):                                                         # spare tyres
        B.cyl("rubber", (-2.85, -6.5, i * .2), .32, .19, 12)
    B.lamps = {"fan": (0, FAN_Y, FAN_Z), "screen": (2.52, 4.2, .95)}
    return B


def fan_blades():
    """seven swept blades + hub, separate object so the viewer can spin it about the fan axis"""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UV1_atlas")
    fy = FAN_Y + .05
    def quad(pts):
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        for l in f.loops: l[uv].uv = (l.vert.co.x, l.vert.co.z)
    for k in range(7):
        a = k * 2 * math.pi / 7
        for side in (0, 1):
            pts = []
            for r, da, dy in ((.22, -.18, -.06), (1.28, -.05, -.02), (1.28, .22, .06), (.22, .12, .04)):
                ang = a + da
                pts.append((r * math.cos(ang), fy + dy * (1 if side == 0 else 1) + (0.004 if side else -0.004), FAN_Z + r * math.sin(ang)))
            quad(pts if side == 0 else pts[::-1])
    n = 14
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        quad([(.24 * math.cos(a0), fy - .1, FAN_Z + .24 * math.sin(a0)), (.24 * math.cos(a1), fy - .1, FAN_Z + .24 * math.sin(a1)),
              (.24 * math.cos(a1), fy + .12, FAN_Z + .24 * math.sin(a1)), (.24 * math.cos(a0), fy + .12, FAN_Z + .24 * math.sin(a0))])
    quad([(.24 * math.cos(2 * math.pi * i / n), fy + .12, FAN_Z + .24 * math.sin(2 * math.pi * i / n)) for i in range(n)])
    return bm


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    B = build()
    stats = {}
    meshes = list(B.bms.items()) + [("fanblade", fan_blades())]
    for mat, b in meshes:
        b.normal_update()
        if mat != "fanblade":
            GE.world_uvs(b)
        png = os.path.join(TEX_DIR, f"tunnel_{mat}.png")
        Image.fromarray(TEXTURES[mat]()).save(png)
        me = bpy.data.meshes.new(mat); b.to_mesh(me); b.free()
        me.materials.append(GE.make_material(mat, png))
        o = bpy.data.objects.new("fan_blades" if mat == "fanblade" else mat, me)
        bpy.context.scene.collection.objects.link(o)
        stats[mat] = len(me.vertices)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "tunnel.glb"), export_format="GLB")
    json.dump({k: [round(c, 3) for c in v] for k, v in B.lamps.items()}, open(os.path.join(OUT, "tunnel_anchors.json"), "w"), indent=1)
    print("verts", sum(stats.values()), stats)


if __name__ == "__main__":
    main()
