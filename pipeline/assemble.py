"""Garage assembly test: stock car + swapped parts -> previews.

usage: python assemble.py <car> <build_name> key=value ...
  bumper_F=<variant>  bumper_R=<variant>  skirt=<variant>  wheel=<rim style>
  spoiler=<style>     lower=<metres>      paint=<ramp name>
Proves the swap contract: every part file shares the car origin, wheels sit on sockets.
"""
import sys, os, math, json
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_car as BC

car, name = sys.argv[1], sys.argv[2]
cfg = dict(a.split("=", 1) for a in sys.argv[3:])
out = os.path.join(ROOT, "out", car)
pdir = os.path.join(out, "parts")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(out, car + ".glb"))
objs = {o.name: o for o in bpy.context.scene.objects}


def imp(fname):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(pdir, fname))
    return [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]


def swap(stock_name, fname):
    if stock_name in objs:
        bpy.data.objects.remove(objs.pop(stock_name))
    return imp(fname)


for part in ("bumper_F", "bumper_R"):
    if part in cfg:
        swap(part, f"{part}_{cfg[part]}.glb")
if "skirt" in cfg:
    for s in "LR":
        swap(f"skirt_{s}", f"skirt_{s}_{cfg['skirt']}.glb")
if "spoiler" in cfg:
    imp(f"spoiler_{cfg['spoiler']}.glb")

lower = float(cfg.get("lower", 0))
if lower:
    for o in bpy.context.scene.objects:
        if o.parent is None and not o.name.startswith("wheel_") and not o.name.startswith("SOCKET"):
            o.location.z -= lower

if "wheel" in cfg:
    sockets = {o.name[7:]: o.matrix_world.translation.copy()
               for o in bpy.context.scene.objects if o.name.startswith("SOCKET_wheel_")}
    for k in list(objs):
        if k.startswith("wheel_") and k[6:8] in ("FL", "FR", "RL", "RR"):
            bpy.data.objects.remove(objs.pop(k))
    proto = imp(f"wheel_{cfg['wheel']}.glb")[0]
    for k, p in sockets.items():
        w = proto.copy()
        bpy.context.scene.collection.objects.link(w)
        w.location = (p.x, p.y, p.z + lower)        # wheels stay on the ground
        w.rotation_mode = "XYZ"
        w.rotation_euler = (0, 0, math.pi if p.x < 0 else 0)
    bpy.data.objects.remove(proto)

bdir = os.path.join(out, "builds"); os.makedirs(bdir, exist_ok=True)
paths = BC.render_previews(bdir, name, None)
with open(os.path.join(bdir, name + ".json"), "w") as fh:
    json.dump(cfg, fh, indent=1)
print(paths)
