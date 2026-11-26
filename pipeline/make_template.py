"""Generate the base sedan block-out used as a starting point for hand-shaped body-type models.

usage: python pipeline/make_template.py            -> models/template/sedan_template.blend (+ .glb preview)

Conventions (same as the generated cars):
  metres, Z up, nose toward +Y, +X = driver's right; origin on the ground, midway between the axles.
The body shell is ONE mesh ("shape") so seams stay welded while it is reshaped; parts are vertex groups
(bumper_F, bumper_R, hood, tailgate, fender_FL/FR, door_FL/FR/RL/RR, skirt_L/R, body).
pipeline/template_export.py splits it into objects with those names and exports a GLB.
"""
import os, math
import bpy, bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "models", "template")

AX = 1.35                       # half wheelbase (2.70 m)
TYRE_R, TYRE_W, TRACK = 0.316, 0.205, 1.52
COWL, REAR_BASE = 0.85, -1.15   # where the cabin starts / ends on the lower body
WS_TOP, RG_TOP = 0.32, -0.80   # windscreen top / rear glass top
ROOF_Z = 1.45

# stations along the car: y, half width, floor, sill, rocker top, arch top, belt, deck edge, crown
S = [
    (2.25, .60, .33, .36, .42, .52, .64, .68, .02),
    (2.15, .79, .24, .30, .40, .58, .71, .75, .03),
    (1.95, .855, .20, .28, .40, .63, .76, .81, .04),
    (AX + .36, .87, .17, .27, .40, .66, .80, .85, .045),
    (AX, .875, .16, .27, .40, .67, .83, .88, .05),
    (AX - .36, .875, .16, .27, .40, .68, .86, .91, .05),
    (COWL, .875, .16, .27, .40, .68, .87, .93, .04),
    (0.45, .88, .16, .27, .40, .68, .88, .93, .04),
    (0.0, .88, .16, .27, .40, .68, .89, .94, .04),
    (-0.45, .88, .16, .27, .40, .68, .90, .95, .04),
    (-AX + .36, .875, .16, .27, .40, .68, .91, .96, .04),
    (REAR_BASE, .875, .16, .27, .40, .67, .92, .97, .04),
    (-AX, .87, .17, .27, .40, .67, .92, .985, .04),
    (-AX - .36, .86, .19, .28, .40, .65, .92, .985, .035),
    (-1.95, .84, .22, .30, .42, .64, .91, .975, .03),
    (-2.15, .79, .27, .33, .44, .62, .88, .95, .02),
    (-2.25, .62, .33, .38, .46, .60, .84, .90, .01),
]
NH = 9                           # points per half ring, bottom centre -> top centre
ARCHES = [(AX + .36, AX - .36), (-AX + .36, -AX - .36)]

MATS = {"paint": (0.80, 0.82, 0.85), "glass": (0.06, 0.12, 0.15), "plastic": (0.05, 0.05, 0.055),
        "light_F": (0.90, 0.92, 0.95), "light_R": (0.55, 0.02, 0.02), "chrome": (0.6, 0.62, 0.65),
        "tyre": (0.02, 0.02, 0.02), "rim": (0.45, 0.46, 0.48)}


def half(st):
    y, w, fl, sill, rock, arch, belt, deck, cr = st
    return [(0, fl), (w * .62, fl), (w * .97, sill), (w, rock), (w, arch), (w * .985, belt),
            (w * .86, deck), (w * .45, deck + cr * .7), (0, deck + cr)]


def ring_xz(st):
    h = half(st)
    right = h                                              # j = 0..8
    left = [(-x, z) for x, z in reversed(h[1:-1])]         # mirror of 7..1
    return right + left                                    # 16 points, closed


def side_j(k):
    """ring index -> (half index j, side) ; side +1 right, -1 left, 0 centre"""
    if k == 0: return 0, 0
    if k <= NH - 1: return k, (0 if k == NH - 1 else 1)
    return 2 * (NH - 1) - k, -1


def build_shell():
    bm = bmesh.new()
    rings = []
    for st in S:
        rings.append([bm.verts.new((x, st[0], z)) for x, z in ring_xz(st)])
    n = len(rings[0])
    seg = {}                                               # face -> (station gap, ring segment k)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(n):
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            seg[f] = (i, k)
    # end caps: bridge right and left halves
    caps = {}
    for idx, r, flip in ((0, rings[0], False), (len(rings) - 1, rings[-1], True)):
        for j in range(NH - 1):
            kr0, kr1 = j, j + 1
            kl0, kl1 = (n - j) % n, n - j - 1
            vs = [r[kr0], r[kr1], r[kl1], r[kl0]] if j not in (0, NH - 2) else None
            if j == 0: vs = [r[0], r[1], r[n - 1]]
            elif j == NH - 2: vs = [r[NH - 2], r[NH - 1], r[n - (NH - 2)]]
            f = bm.faces.new(vs[::-1] if flip else vs)
            caps[f] = (idx, j)
    bm.normal_update()

    # wheel arches: open the side below the arch top between the arch stations
    ys = [st[0] for st in S]
    kill = []
    for f, (i, k) in seg.items():
        y0, y1 = ys[i], ys[i + 1]
        j, side = side_j(k)
        jn, _ = side_j((k + 1) % n)
        jlo = min(j, jn)
        if side != 0 and jlo in (1, 2, 3) and any(min(a, b) <= min(y0, y1) and max(y0, y1) <= max(a, b) for a, b in ARCHES):
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    seg = {f: v for f, v in seg.items() if f.is_valid}

    # cabin: extrude the deck between cowl and rear glass base, then shape it into the greenhouse
    i0, i1 = ys.index(COWL), ys.index(REAR_BASE)
    top = [f for f, (i, k) in seg.items() if i0 <= i < i1 and min(side_j(k)[0], side_j((k + 1) % n)[0]) >= 6]
    res = bmesh.ops.extrude_face_region(bm, geom=top, use_keep_orig=False)
    new_v = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
    new_f = [e for e in res["geom"] if isinstance(e, bmesh.types.BMFace)]
    for v in new_v:
        x, y, z = v.co
        t = (y - REAR_BASE) / (COWL - REAR_BASE)
        yy = RG_TOP + t * (WS_TOP - RG_TOP)
        edge = abs(x) > 0.5
        v.co = Vector((x * 0.80, yy, ROOF_Z + (0.0 if edge else 0.035 * (1 - abs(x) / 0.4))))
    bmesh.ops.delete(bm, geom=[f for f in top if f.is_valid], context="FACES")   # the deck under the cabin
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    cabin_faces = set(new_f)
    side_glass = [f for f in bm.faces if f not in cabin_faces and f not in seg and f not in caps]
    return bm, seg, caps, cabin_faces, set(side_glass), ys, n


def assign(bm, seg, caps, cabin, glass, ys, n):
    """part (vertex group) and material for every face"""
    part, mat = {}, {}
    for f in bm.faces:
        c = f.calc_center_median()
        x, y, z = c
        if f in cabin:
            part[f], mat[f] = "body", "paint"; continue
        if f in glass:
            part[f], mat[f] = "body", "glass"; continue
        if f in caps:
            idx, j = caps[f]
            front = idx == 0
            if j >= 5: part[f] = "hood" if front else "tailgate"
            else: part[f] = "bumper_F" if front else "bumper_R"
            mat[f] = "plastic" if j == 0 else ("light_F" if front and j == 4 else ("light_R" if not front and j in (4, 5) else "paint"))
            continue
        i, k = seg[f]
        j = min(side_j(k)[0], side_j((k + 1) % n)[0])
        L = "L" if x < 0 else "R"
        upper = j >= 5
        if y >= 1.95 and not upper: p = "bumper_F"
        elif y <= -1.95 and not upper: p = "bumper_R"
        elif upper and j >= 6 and y >= COWL: p = "hood"
        elif upper and j >= 6 and y <= REAR_BASE: p = "tailgate"
        elif 2 <= j <= 4 and COWL <= y <= 1.95 and j >= 3: p = f"fender_F{L}"
        elif j in (3, 4) and 0.0 <= y <= COWL: p = f"door_F{L}"
        elif j in (3, 4) and -AX + .36 <= y <= 0.0: p = f"door_R{L}"
        elif j == 2 and -AX + .36 <= y <= AX - .36: p = f"skirt_{L}"
        else: p = "body"
        part[f] = p
        m = "paint"
        if j <= 1: m = "plastic"
        if p == "bumper_F" and j == 4 and abs(x) > 0.45: m = "light_F"
        if y <= -1.95 and j == 5 and abs(x) > 0.40: m = "light_R"
        mat[f] = m
    return part, mat


def make_mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.08 if name in ("glass", "chrome") else 0.5
    m.diffuse_color = (*rgb, 1)
    return m


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def box_obj(name, c, lo, hi, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = Vector(((lo[0] + hi[0]) / 2 + v.co.x * (hi[0] - lo[0]), (lo[1] + hi[1]) / 2 + v.co.y * (hi[1] - lo[1]),
                       (lo[2] + hi[2]) / 2 + v.co.z * (hi[2] - lo[2])))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(bpy.data.materials[mat])
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    return o


def wheel_mesh():
    bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=TYRE_R, radius2=TYRE_R, depth=TYRE_W)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "Y"))
    # rim: inset the outer cap (+X) twice and push the centre in
    cap = [f for f in bm.faces if f.normal.x > 0.9]
    r1 = bmesh.ops.inset_region(bm, faces=cap, thickness=0.07)
    r2 = bmesh.ops.inset_region(bm, faces=cap, thickness=0.02, depth=-0.03)
    me = bpy.data.meshes.new("wheel"); bm.to_mesh(me)
    me.materials.append(bpy.data.materials["tyre"]); me.materials.append(bpy.data.materials["rim"])
    bm2 = bmesh.new(); bm2.from_mesh(me)
    for f in bm2.faces:
        c = f.calc_center_median()
        f.material_index = 1 if (f.normal.x > 0.9 and math.hypot(c.y, c.z) < TYRE_R - 0.06) else 0
    bm2.to_mesh(me); bm2.free(); bm.free()
    return me


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for k, v in MATS.items(): make_mat(k, v)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"

    c_shape, c_wheels, c_sock, c_mods = coll("SHAPE"), coll("WHEELS"), coll("SOCKETS"), coll("MODS")

    bm, seg, caps, cabin, glass, ys, n = build_shell()
    part, mat = assign(bm, seg, caps, cabin, glass, ys, n)
    names = list(MATS.keys())
    for f in bm.faces: f.material_index = names.index(mat[f])
    me = bpy.data.meshes.new("shape")
    bm.to_mesh(me)
    for m in names: me.materials.append(bpy.data.materials[m])
    me.use_mirror_x = True                     # edit symmetrically by default
    o = bpy.data.objects.new("shape", me); c_shape.objects.link(o)
    groups = ["body", "bumper_F", "bumper_R", "hood", "tailgate", "fender_FL", "fender_FR",
              "door_FL", "door_FR", "door_RL", "door_RR", "skirt_L", "skirt_R"]
    vg = {g: o.vertex_groups.new(name=g) for g in groups}
    faces_by = {}
    bm.faces.ensure_lookup_table()
    for f in bm.faces: faces_by.setdefault(part[f], []).append(f.index)
    for g, fids in faces_by.items():
        vids = sorted({v for fi in fids for v in me.polygons[fi].vertices})
        vg[g].add(vids, 1.0, "REPLACE")
    o["part_groups"] = ", ".join(groups)
    bm.free()

    # mirrors
    for side, sx in (("L", -1), ("R", 1)):
        box_obj(f"mirror_{side}", c_shape, (.80 if sx > 0 else -.98, 0.62, 0.92), (.98 if sx > 0 else -.80, 0.76, 1.02), "paint")

    # sockets
    def sock(name, loc):
        e = bpy.data.objects.new("SOCKET_" + name, None); e.empty_display_type = "ARROWS"; e.empty_display_size = .15
        e.location = loc; c_sock.objects.link(e); return e
    tx = TRACK / 2
    S_W = {"FL": (-tx, AX, TYRE_R), "FR": (tx, AX, TYRE_R), "RL": (-tx, -AX, TYRE_R), "RR": (tx, -AX, TYRE_R)}
    for k, v in S_W.items(): sock("wheel_" + k, v)
    for k, v in {"bumper_F": (0, 2.25, .40), "bumper_R": (0, -2.25, .42), "skirt_L": (-.88, 0, .27), "skirt_R": (.88, 0, .27),
                 "hood": (0, 1.5, .92), "roof": (0, -0.2, ROOF_Z + .03), "spoiler": (0, -2.10, .97), "exhaust": (.45, -2.25, .30),
                 "grille": (0, 2.25, .58)}.items():
        sock(k, v)

    # wheels: one mesh, four linked instances on the sockets (left ones turned to face out)
    wm = wheel_mesh()
    for k, (x, y, z) in S_W.items():
        w = bpy.data.objects.new("wheel_" + k, wm); w.location = (x, y, z)
        if x < 0: w.rotation_euler = (0, 0, math.pi)
        c_wheels.objects.link(w)

    # starter mod parts, in place (same origin as the car); hidden by default
    box_obj("bumper_F_lip", c_mods, (-.74, 2.02, .15), (.74, 2.30, .18), "plastic")
    d = box_obj("bumper_R_diffuser", c_mods, (-.62, -2.30, .18), (.62, -1.98, .21), "plastic")
    for i, x in enumerate((-.42, -.14, .14, .42)):
        box_obj(f"bumper_R_diffuser_fin{i}", c_mods, (x - .01, -2.30, .21), (x + .01, -2.02, .30), "plastic").parent = d
    for side, sx in (("L", -1), ("R", 1)):
        box_obj(f"skirt_{side}_skirt", c_mods, (min(sx * .84, sx * .93), -0.95, .20), (max(sx * .84, sx * .93), 0.95, .29), "plastic")
    box_obj("spoiler_roof_ext", c_mods, (-.62, -2.22, .97), (.62, -2.02, 1.02), "paint")
    wing = box_obj("spoiler_gt_wing", c_mods, (-.78, -2.32, 1.22), (.78, -2.02, 1.25), "plastic")
    for sx in (-.45, .45):
        box_obj(f"spoiler_gt_wing_post{'L' if sx < 0 else 'R'}", c_mods, (sx - .015, -2.18, .97), (sx + .015, -2.10, 1.22), "plastic").parent = wing
    for ob in c_mods.objects: ob.hide_set(True) if ob.name in bpy.context.view_layer.objects else None
    c_mods.hide_viewport = False
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.name == "MODS": lc.hide_viewport = True

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "sedan_template.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("saved", path, "faces", len(me.polygons), "verts", len(me.vertices))


if __name__ == "__main__":
    main()
