"""Recessed features (grilles, fog pods, headlights, plate recesses) cut into the body
with an exact boolean. Outlines come from the profile, measured off the blueprint.

Feature spec (in profile.FEATURES):
  dict(name, kind, part, mirror, depth, outline=[...], back="flat"|"normal")
  outline points: ("f", x, z)  -> ray along -Y from the front
                  ("r", x, z)  -> ray along +Y from the rear
                  ("s", y, z)  -> ray along -X from the right side (x>0)
                  ("n", x, y, z) -> nearest point on the surface
Face bands written on the cut faces (used by the painter):
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

KIND_BAND = {           # kind -> (back face band, wall band)
    "grille":   (20, 25),
    "fog":      (21, 25),
    "headlamp": (22, 26),
    "recess":   (23, 27),
    "bed":      (28, 29),          # pickup bed: floor liner, inner walls
}
FEATURE_BANDS = set(b for pair in KIND_BAND.values() for b in pair)


def _bvh(ob):
    me = ob.data
    return BVHTree.FromPolygons([v.co.copy() for v in me.vertices],
                                [list(p.vertices) for p in me.polygons])


def _hit(bvh, pt, sx):
    if pt[0] == "n":                          # explicit 3D point snapped to the surface
        _, x, y, z = pt
        loc, n, _, _ = bvh.find_nearest(Vector((sx * x, y, z)))
        return loc, n, -n
    kind, a, b = pt
    if kind == "t":                           # from the top: ("t", x, y), used for pickup beds
        o, d = Vector((sx * a, b, 6.0)), Vector((0, 0, -1))
    elif kind == "f":
        o, d = Vector((sx * a, 5.0, b)), Vector((0, -1, 0))
    elif kind == "r":
        o, d = Vector((sx * a, -5.0, b)), Vector((0, 1, 0))
    else:
        o, d = Vector((sx * 5.0, a, b)), Vector((-sx, 0, 0))
    loc, n, _, _ = bvh.ray_cast(o, d)
    if loc is None:
        raise RuntimeError(f"feature outline point {pt} misses the body")
    if n.dot(d) > 0:
        n = -n
    return loc, n, d


def build_cutter(ob, bvh, feat, sx, part_idx):
    hits = [_hit(bvh, p, sx) for p in feat["outline"]]
    if sx < 0:
        hits = hits[::-1]                     # keep winding after mirroring
    P = [h[0] for h in hits]
    c = sum(P, Vector()) / len(P)
    depth = feat["depth"]
    outer, inner = [], []
    if feat.get("back", "flat") == "flat":
        d = -hits[0][2]                        # direction pointing out of the body
        y_back = min((p.dot(d) for p in P)) - depth
        for p in P:
            outer.append(p + d * 0.08)
            q = p - d * (p.dot(d) - y_back)
            inner.append(q + (c - q) * feat.get("taper", 0.0))
    else:
        for p, n, _ in hits:
            outer.append(p + n * 0.08)
            q = p - n * depth
            inner.append(q + (c - q) * feat.get("taper", 0.0))
    bm = bmesh.new()
    vo = [bm.verts.new(v) for v in outer]
    vi = [bm.verts.new(v) for v in inner]
    k = len(vo)
    faces_wall = []
    fo = bm.faces.new(vo)
    fi = bm.faces.new(vi[::-1])
    for i in range(k):
        j = (i + 1) % k
        faces_wall.append(bm.faces.new([vo[i], vo[j], vi[j], vi[i]]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new("cut_" + feat["name"])
    bm.to_mesh(me); bm.free()
    back_band, wall_band = KIND_BAND[feat["kind"]]
    nF = len(me.polygons)
    bands = [wall_band] * nF
    bands[1] = back_band                       # face order: outer cap, inner cap, walls
    a = me.attributes
    a.new("part", "INT", "FACE").data.foreach_set("value", [part_idx] * nF)
    a.new("band", "INT", "FACE").data.foreach_set("value", bands)
    a.new("glass", "BOOLEAN", "FACE").data.foreach_set("value", [False] * nF)
    a.new("ring_v", "FLOAT", "POINT").data.foreach_set("value", [0.0] * len(me.vertices))
    o = bpy.data.objects.new(me.name, me)
    return o


def apply_features(ob, prof, parts):
    feats = getattr(prof, "FEATURES", [])
    if not feats:
        return ob
    bvh = _bvh(ob)
    coll = bpy.data.collections.new("cutters")
    bpy.context.scene.collection.children.link(coll)
    for feat in feats:
        sides = (1, -1) if feat.get("mirror") else (1,)
        for sx in sides:
            pname = feat["part"].replace("{s}", "R" if sx > 0 else "L")
            cut = build_cutter(ob, bvh, feat, sx, parts.index(pname))
            coll.objects.link(cut)
    mod = ob.modifiers.new("features", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.operand_type = "COLLECTION"
    mod.collection = coll
    mod.solver = "EXACT"
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True,
                                             depsgraph=dg)
    ob.modifiers.clear()
    old = ob.data
    ob.data = new_me
    bpy.data.meshes.remove(old)
    for c in list(coll.objects):
        bpy.data.objects.remove(c)
    bpy.data.collections.remove(coll)
    # boolean leaves ngons; triangulate concave ones only (keeps quads for the loft)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng:
        bmesh.ops.triangulate(bm, faces=ng)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob
