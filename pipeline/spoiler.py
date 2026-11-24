"""Parametric spoilers, built in car space around the profile's `spoiler` socket.
Painted with the same palette/painter as the body (band 30 = carbon, 31 = body paint)."""
import math, types
import numpy as np
import bpy, bmesh


def _box(bm, lay, pts8, band):
    """pts8: 4 'front' verts then 4 'back' verts, both rings in the same winding."""
    v = [bm.verts.new(p) for p in pts8]
    q = [(0, 1, 2, 3), (7, 6, 5, 4)] + [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)]
    for f in q:
        fc = bm.faces.new([v[i] for i in f])
        fc[lay] = band(fc) if callable(band) else band


def build(style, sock, P):
    """sock: (x, y, z) of the spoiler socket. P: params (overrides)."""
    _, ys, zs = sock
    bm = bmesh.new()
    lay = bm.faces.layers.int.new("band")
    if style == "roof_ext":
        w0, w1 = P.get("w", 0.50), P.get("w", 0.50) - 0.04
        L, drop, t = P.get("length", 0.15), P.get("drop", 0.03), 0.025
        y0, y1 = ys + 0.02, ys - L
        z0, z1 = zs + 0.012, zs + 0.012 - drop
        pts = [(-w0, y0, z0 - t), (w0, y0, z0 - t), (w0, y0, z0), (-w0, y0, z0),
               (-w1, y1, z1 - t * .4), (w1, y1, z1 - t * .4), (w1, y1, z1), (-w1, y1, z1)]
        _box(bm, lay, pts, lambda f: 31 if f.calc_center_median().z > 0 and f.normal.z > 0.3 else 30)
    elif style == "gt_wing":
        span, chord = P.get("span", 0.66), P.get("chord", 0.22)
        h, aoa = P.get("height", 0.11), math.radians(P.get("aoa", 8))
        zc, yc = zs + h, ys - 0.12
        def foil(x):
            le = (x, yc + chord / 2 * math.cos(aoa), zc - chord / 2 * math.sin(aoa))
            te = (x, yc - chord / 2 * math.cos(aoa), zc + chord / 2 * math.sin(aoa))
            top = (x, yc + chord * 0.1, zc + 0.022)
            bot = (x, yc + chord * 0.1, zc - 0.006)
            return [le, top, te, bot]
        _box(bm, lay, foil(-span) + foil(span), 30)
        for sx in (-1, 1):                               # end plates
            x0, x1 = sx * (span + 0.002), sx * (span + 0.012)
            yA, yB = yc + chord * 0.62, yc - chord * 0.68
            zA, zB = zc - 0.05, zc + 0.07
            pts = [(x0, yA, zA), (x0, yB, zA), (x0, yB, zB), (x0, yA, zB),
                   (x1, yA, zA), (x1, yB, zA), (x1, yB, zB), (x1, yA, zB)]
            _box(bm, lay, pts, 30)
            ux = sx * P.get("upright_x", 0.34)            # uprights
            pts = [(ux - .01, ys + .03, zs - .01), (ux + .01, ys + .03, zs - .01),
                   (ux + .01, ys - .05, zs - .01), (ux - .01, ys - .05, zs - .01),
                   (ux - .01, yc + .03, zc), (ux + .01, yc + .03, zc),
                   (ux + .01, yc - .05, zc), (ux - .01, yc - .05, zc)]
            _box(bm, lay, pts, 30)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:                                   # re-evaluate band now normals are right
        if style == "roof_ext":
            f[lay] = 31 if f.normal.z > 0.3 else 30
    me = bpy.data.meshes.new(f"spoiler_{style}")
    bm.to_mesh(me); bm.free()
    n = len(me.polygons)
    me.attributes.new("part", "INT", "FACE").data.foreach_set("value", [0] * n)
    me.attributes.new("glass", "BOOLEAN", "FACE").data.foreach_set("value", [False] * n)
    me.attributes.new("ring_v", "FLOAT", "POINT").data.foreach_set("value", [0.0] * len(me.vertices))
    me.uv_layers.new(name="UV1_atlas")
    o = bpy.data.objects.new(f"spoiler_{style}", me)
    bpy.context.scene.collection.objects.link(o)
    return o


def paint_profile(car):
    return types.SimpleNamespace(PAINT=car.PAINT, B_PILLAR=(9, 9),
                                 paint=lambda P, N, V, g, b, C, B: np.full(len(P), -1, int))
