"""Dyno room: its own space off the garage (like the wind tunnel), so the car can drive straight in.

Layout (Blender, metres, Z up): the car drives in through a roll-up door at +Y and stops nose toward -Y
with its front axle over the rollers at y = ROLL. The viewer moves the car so its front axle lands on
the rollers (car origin y = ROLL + wheelbase / 2). In front of the nose: the blower fan. Left of the
car: the control console and a wall monitor (EMIT_dynoA / EMIT_dynoB, drawn live by the viewer).
Output: out/env/dyno.glb + dyno_anchors.json.
"""
import os, sys, json, math
import numpy as np
import bpy
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import garage_env as GE
from garage_env import Builder, shade, noise, t_emit, t_simple, RNG

OUT, TEX_DIR = GE.OUT, GE.TEX_DIR
W, Y0, Y1 = 3.6, -6.0, 7.0                   # half width, fan end, door wall
EAVE, RIDGE = 3.8, 5.0                        # gable roof like the garage
ROLL = -1.35                                # roller line
DOOR = (-1.7, 1.7, 2.9)                     # door opening x0, x1, top


def t_night():
    """what shows through the door: a dark lane under a street light"""
    n = 64; yy, xx = np.mgrid[0:n, 0:n]
    img = shade(["#05070b", "#0a0f18", "#111a28"], 0.35 + noise(n, .1) + 0.25 * (yy / n))
    img[RNG.random((n, n)) < .004] = GE.hx("#ffcf8a")
    return img


TEXTURES = {k: GE.TEXTURES[k] for k in ("floor", "plaster", "plaster_low", "steel", "rubber", "red", "grate", "dynoplate",
                                        "dynoblue", "hazard", "console", "blacksteel", "yellow", "EMIT_dynoA", "EMIT_dynoB",
                                        "cardboard", "paper", "brick", "roof", "beam", "EMIT_work")}
TEXTURES.update({"EMIT_led": lambda: t_emit("#e8f1ff"), "EMIT_night": t_night})


def build():
    B = Builder()
    # ---- shell, same materials as the garage: concrete floor, plaster band at the bottom, brick above,
    # gable roof on timber trusses; the door wall has a roll-up opening
    B.quad("floor", [(-W, Y0, 0), (W, Y0, 0), (W, Y1, 0), (-W, Y1, 0)])
    B.quad("plaster_low", [(-W, Y0, 0), (-W, Y1, 0), (-W, Y1, 1.2), (-W, Y0, 1.2)])
    B.quad("plaster_low", [(W, Y0, 0), (W, Y0, 1.2), (W, Y1, 1.2), (W, Y1, 0)])
    B.quad("brick", [(-W, Y0, 1.2), (-W, Y1, 1.2), (-W, Y1, EAVE), (-W, Y0, EAVE)])
    B.quad("brick", [(W, Y0, 1.2), (W, Y0, EAVE), (W, Y1, EAVE), (W, Y1, 1.2)])
    B.quad("brick", [(-W, Y0, 0), (-W, Y0, EAVE), (W, Y0, EAVE), (W, Y0, 0)])                # fan-end wall + gable
    B.quad("brick", [(-W, Y0, EAVE), (0, Y0, RIDGE), (W, Y0, EAVE)])
    dx0, dx1, dz = DOOR
    for a, b_, z0, z1 in ((-W, dx0, 0, EAVE), (dx1, W, 0, EAVE), (dx0, dx1, dz, EAVE)):     # door wall around the opening
        B.quad("brick", [(a, Y1, z0), (a, Y1, z1), (b_, Y1, z1), (b_, Y1, z0)], flip=True)
    B.quad("brick", [(-W, Y1, EAVE), (0, Y1, RIDGE), (W, Y1, EAVE)], flip=True)
    B.quad("roof", [(-W, Y0, EAVE), (0, Y0, RIDGE), (0, Y1, RIDGE), (-W, Y1, EAVE)], flip=True)
    B.quad("roof", [(W, Y0, EAVE), (W, Y1, EAVE), (0, Y1, RIDGE), (0, Y0, RIDGE)], flip=True)
    for y in np.arange(Y1 - 0.5, Y0, -2.6):                                                # trusses: rafters + tie beam
        B.beam("beam", (-W, y, EAVE - .05), (0, y, RIDGE - .12), .16, .22)
        B.beam("beam", (W, y, EAVE - .05), (0, y, RIDGE - .12), .16, .22)
        B.beam("beam", (-W, y, EAVE - .1), (W, y, EAVE - .1), .14, .18)
    B.beam("beam", (0, Y0, RIDGE - .2), (0, Y1, RIDGE - .2), .18, .2)
    for x in (-W / 2, W / 2):                                                               # purlins
        B.beam("beam", (x, Y0, EAVE + (RIDGE - EAVE) / 2 - .16), (x, Y1, EAVE + (RIDGE - EAVE) / 2 - .16), .1, .12)
    B.box("steel", (dx0 - .1, Y1 - .1, 0), (dx0, Y1 + .05, dz + .1))                      # door frame
    B.box("steel", (dx1, Y1 - .1, 0), (dx1 + .1, Y1 + .05, dz + .1))
    B.cyl("steel", (dx0 - .05, Y1 - .3, dz + .3), .26, dx1 - dx0 + .1, 12, axis="x")      # rolled-up shutter drum
    B.box("steel", (dx0, Y1 - .12, dz - .18), (dx1, Y1 - .06, dz))                         # bottom slat left showing
    # outside: a strip of yard and a dark backdrop
    B.quad("floor", [(-W, Y1, -.01), (W, Y1, -.01), (W, Y1 + 7, -.01), (-W, Y1 + 7, -.01)])
    B.quad("EMIT_night", [(-W, Y1 + 7, 0), (-W, Y1 + 7, 4), (W, Y1 + 7, 4), (W, Y1 + 7, 0)], flip=True)

    # ---- LED battens hung under the tie beams along the lane
    for x in (-1.4, 1.4):
        B.box("EMIT_led", (x - .04, -4.2, 3.44), (x + .04, 4.8, 3.47))
        B.box("steel", (x - .06, -4.2, 3.47), (x + .06, 4.8, 3.5))
        for y in np.arange(Y1 - 0.5, Y0, -2.6):
            if -4.2 < y < 4.8:
                B.beam("steel", (x, y, 3.5), (x, y, EAVE - .19), .015)

    # ---- dyno deck (blue diamond plate), rollers under the front axle, front wheel guards, drive-on ramp
    B.box("dynoplate", (-1.35, -3.3, 0), (1.35, 3.6, .03))
    B.box("rubber", (-1.0, ROLL - .3, .03), (1.0, ROLL + .3, .032))
    for dy in (-.17, .17):
        B.cyl("red", (-.95, ROLL + dy, .04), .085, 1.9, 10, axis="x")
    for x0 in (-1.35, .85):
        y0, y1 = ROLL - .6, ROLL + .6
        B.box("dynoblue", (x0, y0, .03), (x0 + .5, y1, .3))
        B.box("hazard", (x0 - .005, y0 - .005, .3), (x0 + .505, y1 + .005, .38))
        B.box("grate", (x0 + .05, y0 + .05, .381), (x0 + .45, y1 - .05, .385))
    B.box("rubber", (-.95, 3.6, 0), (.95, 4.2, .02))
    for x in (-1.55, 1.55):                                                                # hazard lines along the deck
        B.quad("hazard", [(x - .07, -3.3, .004), (x + .07, -3.3, .004), (x + .07, 4.2, .004), (x - .07, 4.2, .004)])

    # ---- blower fan in front of the nose
    fy = -3.9
    B.box("dynoblue", (-.6, fy - .3, .12), (.6, fy, 1.15))
    B.box("grate", (-.5, fy + .005, .22), (.5, fy + .015, 1.05))
    B.box("dynoblue", (-.35, fy - .55, .12), (.35, fy - .3, .95))
    for x in (-.5, .5):
        B.cyl("rubber", (x, fy - .2, .06), .06, .05, 8, axis="x")

    # ---- control console left of the nose, screen facing the car; wall monitor over it
    cx, cy = -2.55, -2.2
    B.box("console", (cx - .3, cy - .35, 0), (cx + .3, cy + .35, 1.1))
    B.box("console", (cx - .05, cy - .4, .9), (cx + .38, cy + .4, .95))                   # keyboard shelf
    B.box("steel", (cx - .14, cy - .02, 1.1), (cx - .1, cy + .02, 1.3))
    B.box("blacksteel", (cx - .1, cy - .33, 1.28), (cx + .02, cy + .33, 1.72))
    B.quad_uv("EMIT_dynoA", [(cx + .03, cy - .3, 1.31), (cx + .03, cy + .3, 1.31), (cx + .03, cy + .3, 1.69), (cx + .03, cy - .3, 1.69)],
              [(0, 0), (1, 0), (1, 1), (0, 1)])
    my = -0.2
    B.box("blacksteel", (-W, my - .5, 1.6), (-W + .06, my + .5, 2.2))
    B.quad_uv("EMIT_dynoB", [(-W + .07, my - .45, 1.64), (-W + .07, my + .45, 1.64), (-W + .07, my + .45, 2.16), (-W + .07, my - .45, 2.16)],
              [(0, 0), (1, 0), (1, 1), (0, 1)])
    B.box("blacksteel", (-W + .02, my - .02, .4), (-W + .05, my + .02, 1.6))               # cable down the wall

    # ---- props: exhaust extraction hose off the ceiling (left of the lane), tool cart, tyres, extinguisher, boxes
    hx, hy = -1.75, 4.4
    pts = [(hx, hy, EAVE - .1), (hx, hy, 2.6), (hx - .1, hy - .3, 1.6), (hx - .05, hy - .5, .9), (hx - .1, hy - .4, .45)]
    for a, b_ in zip(pts, pts[1:]):
        B.beam("rubber", a, b_, .14)
    B.cyl("steel", (hx - .1, hy - .4, .3), .1, .15, 8)
    tx, ty = -2.75, 1.5                                                                    # tool cart under the wall monitor
    B.box("red", (tx - .3, ty - .45, .25), (tx + .3, ty + .45, .95))
    B.box("steel", (tx - .32, ty - .47, .95), (tx + .32, ty + .47, .98))
    for k in range(3):
        B.box("steel", (tx - .31, ty - .4, .35 + k * .2), (tx - .3, ty + .4, .37 + k * .2))
    for x in (tx - .25, tx + .25):
        for y in (ty - .4, ty + .4):
            B.cyl("rubber", (x, y, .05), .05, .2, 6)
    for i in range(4):
        B.cyl("rubber", (2.85, 5.9, i * .2), .32, .19, 12)
    B.cyl("red", (-3.35, 2.45, 0), .09, .55, 8)                                            # extinguisher
    B.cyl("blacksteel", (-3.35, 2.45, .55), .03, .08, 6)
    # cardboard boxes against the walls (stacks, slightly offset like they were dumped there)
    stacks = {}
    for (x0, y0, w, d, h) in ((-3.5, 3.2, .7, .7, .5), (-3.45, 3.28, .55, .55, .4), (-3.52, 5.4, .6, .8, .55),
                              (-3.5, 5.48, .5, .6, .45), (-3.4, 4.35, .45, .5, .35),
                              (2.85, 2.5, .6, .7, .5), (2.92, 2.58, .5, .55, .4), (2.85, -5.6, .7, .6, .6), (2.93, -5.5, .55, .5, .45),
                              (-3.5, -5.6, .6, .55, .5)):
        key = (round(x0), round(y0))
        z = stacks.get(key, 0)
        x1 = min(x0 + w, W - .02) if x0 > 0 else x0 + w
        x0 = max(x0, -W + .02)
        B.box("cardboard", (x0, y0, z), (x1, y0 + d, z + h))
        stacks[key] = z + h
    B.box("paper", (-3.3, 4.45, .35), (-3.05, 4.75, .37))
    # floor flood light, same as the garage's, behind the car on the right (camera side), lit at the rear bumper
    lens = GE.floor_flood(B, (1.65, 4.75, 0.0), math.atan2(2.9 - 4.75, 0 - 1.65) - math.pi / 2)
    B.lamps = {"flood": lens, "roll": (0, ROLL, .04), "door": (0, Y1, 0), "fan": (0, fy, .6), "console": (cx, cy, 1.5)}
    return B


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    B = build()
    stats = {}
    for mat, b in B.bms.items():
        b.normal_update()
        GE.world_uvs(b)
        uvl = b.loops.layers.uv.active
        for f, uvs in B.fixed.get(mat, []):
            for l, uv in zip(f.loops, uvs):
                l[uvl].uv = uv
        png = os.path.join(TEX_DIR, f"dyno_{mat}.png")
        Image.fromarray(TEXTURES[mat]()).save(png)
        me = bpy.data.meshes.new(mat); b.to_mesh(me); b.free()
        me.materials.append(GE.make_material(mat, png))
        o = bpy.data.objects.new(mat, me); bpy.context.scene.collection.objects.link(o)
        stats[mat] = len(me.vertices)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "dyno.glb"), export_format="GLB")
    json.dump({k: [round(c, 3) for c in v] for k, v in B.lamps.items()}, open(os.path.join(OUT, "dyno_anchors.json"), "w"), indent=1)
    print("verts", sum(stats.values()), stats)


if __name__ == "__main__":
    main()
