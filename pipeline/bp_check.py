"""Overlay the built model on its blueprint (all 4 views) to check proportions.

usage: python bp_check.py <car_name>
Reads blueprints/<car>/calib.json and out/<car>/<car>.glb, writes out/<car>/<car>_bp_check.png
"""
import sys, os, json
import numpy as np
import bpy
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
car = sys.argv[1]
cal = json.load(open(os.path.join(ROOT, "blueprints", car, "calib.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "out", car, car + ".glb"))

tris = []
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.context.scene.objects:
    if ob.type != "MESH":
        continue
    me = ob.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    M = np.array(ob.matrix_world)
    co = np.array([v.co for v in me.vertices])
    co = (np.c_[co, np.ones(len(co))] @ M.T)[:, :3]
    # glTF import is Y-up -> blender Z-up already handled by importer
    for t in me.loop_triangles:
        tris.append(co[list(t.vertices)])
tris = np.array(tris)

Z = 3
bp = Image.open(os.path.join(ROOT, "blueprints", car, cal["image"])).convert("RGB")
bp = bp.resize((bp.width * Z, bp.height * Z), Image.NEAREST)
ov = Image.new("RGBA", bp.size, (0, 0, 0, 0))
d = ImageDraw.Draw(ov)
s = cal["px_per_m"]
for view, v in cal["views"].items():
    ox, oy = v["origin"]
    ua, va = v["u"], v["v"]          # e.g. ["-y", "z"]
    sv = s * v.get("scale", 1.0)       # per-view drawing scale (some blueprints draw views at different sizes)
    def axis(a, P):
        sgn = -1 if a[0] == "-" else 1
        return sgn * P[..., "xyz".index(a[-1])]
    U = (ox + axis(ua, tris) * sv) * Z
    V = (oy - axis(va, tris) * sv) * Z
    for i in range(len(tris)):
        d.polygon(list(zip(U[i], V[i])), fill=(255, 40, 40, 70))
out = Image.alpha_composite(bp.convert("RGBA"), ov).convert("RGB")
path = os.path.join(ROOT, "out", car, car + "_bp_check.png")
out.save(path)
print(path)
