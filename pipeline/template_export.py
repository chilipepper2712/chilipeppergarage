"""Check and export a hand-shaped body-type model made from models/template/sedan_template.blend.

usage: python pipeline/template_export.py <file.blend> <name>
   ->  out/<name>/<name>_shape.glb  (+ a printed checklist)

What it does:
  1. checks the conventions (axes, size, nose toward +Y, required groups / sockets / wheels);
  2. splits the "shape" mesh into one object per vertex group (bumper_F, hood, door_FL, ...);
     a face goes to the first group in PRIORITY that holds all of its vertices, else to "body";
  3. exports body parts, mirrors, wheels, sockets and the MODS collection to one GLB.
Exit code 1 if a check fails.
"""
import sys, os
import bpy, bmesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIORITY = ["bumper_F", "bumper_R", "hood", "tailgate", "fender_FL", "fender_FR",
            "door_FL", "door_FR", "door_RL", "door_RR", "skirt_L", "skirt_R"]
REQUIRED_GROUPS = ["bumper_F", "bumper_R", "skirt_L", "skirt_R"]
REQUIRED_SOCKETS = ["wheel_FL", "wheel_FR", "wheel_RL", "wheel_RR", "spoiler"]


def main(path, name):
    bpy.ops.wm.open_mainfile(filepath=path)
    problems, notes = [], []
    shape = bpy.data.objects.get("shape")
    if not shape:
        print("FAIL: no object named 'shape'"); sys.exit(1)
    bpy.context.view_layer.objects.active = shape
    for o in bpy.data.objects: o.hide_set(False) if o.name in bpy.context.view_layer.objects else None
    for lc in bpy.context.view_layer.layer_collection.children: lc.hide_viewport = False; lc.exclude = False

    # apply object transforms so the checks see real coordinates
    M = shape.matrix_world
    co = [M @ v.co for v in shape.data.vertices]
    xs, ys, zs = [c.x for c in co], [c.y for c in co], [c.z for c in co]
    L, W, H = max(ys) - min(ys), max(xs) - min(xs), max(zs) - min(zs)
    notes.append(f"size L {L:.2f} x W {W:.2f} x H {max(zs):.2f} m")
    if not (3.0 < L < 6.0): problems.append(f"length {L:.2f} m: model must be in metres, nose along Y")
    if W > L: problems.append("wider than long: nose must point along +Y, not X")
    if min(zs) < -0.05 or min(zs) > 0.4: problems.append(f"lowest point z={min(zs):.2f}: origin must be on the ground")
    if abs(sum(xs) / len(xs)) > 0.05: problems.append("not centred on X (car centre line must be x = 0)")

    groups = {g.name: g.index for g in shape.vertex_groups}
    for g in REQUIRED_GROUPS:
        if g not in groups: problems.append(f"missing vertex group '{g}'")
    for s in REQUIRED_SOCKETS:
        if not bpy.data.objects.get("SOCKET_" + s): problems.append(f"missing empty 'SOCKET_{s}'")
    for k in ("FL", "FR", "RL", "RR"):
        w, s = bpy.data.objects.get("wheel_" + k), bpy.data.objects.get("SOCKET_wheel_" + k)
        if not w: problems.append(f"missing wheel_{k}")
        elif s and (w.matrix_world.translation - s.matrix_world.translation).length > 0.01:
            problems.append(f"wheel_{k} is not on SOCKET_wheel_{k}")
    fl = bpy.data.objects.get("SOCKET_wheel_FL")
    if fl and fl.matrix_world.translation.y < 0: problems.append("front wheels are at -Y: nose must point toward +Y")
    if fl and fl.matrix_world.translation.x > 0: problems.append("FL wheel at +X: left side of the car is -X")

    # split the shell by vertex group
    me = shape.data
    vg = [{g.group for g in v.groups} for v in me.vertices]
    owner = []
    for p in me.polygons:
        common = set.intersection(*[vg[i] for i in p.vertices]) if p.vertices else set()
        owner.append(next((g for g in PRIORITY if g in groups and groups[g] in common), "body"))
    counts = {}
    for g in set(owner):
        bm = bmesh.new(); bm.from_mesh(me); bm.transform(M)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f, o in zip(bm.faces, owner) if o != g], context="FACES")
        nm = bpy.data.meshes.new(g); bm.to_mesh(nm); bm.free()
        for m in me.materials: nm.materials.append(m)
        ob = bpy.data.objects.new(g, nm); bpy.context.scene.collection.objects.link(ob)
        counts[g] = len(nm.polygons)
    bpy.data.objects.remove(shape)
    notes.append("parts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    total = sum(counts.values())
    notes.append(f"body faces {total}" + ("  (aim for 500-1200)" if not 300 <= total <= 1500 else ""))
    mods = bpy.data.collections.get("MODS")
    notes.append("mods: " + (", ".join(o.name for o in mods.objects if not o.parent) if mods else "none"))

    for n in notes: print("  " + n)
    for p in problems: print("FAIL: " + p)
    if problems: sys.exit(1)
    out = os.path.join(ROOT, "out", name); os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, f"{name}_shape.glb")
    bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", use_visible=False, export_yup=True, export_apply=True)
    print("OK ->", dst)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(os.path.abspath(a[0]), a[1])
