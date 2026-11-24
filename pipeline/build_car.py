"""Generic low-poly car builder.

usage: python build_car.py <profile_module_name>

Pipeline:
  profile curves -> station rings -> loft mesh (+caps, mirrors)
  -> face labels (band / part / glass) -> UV1 smart-project @ fixed texel density
  -> UV2 wrap projection into shared template -> 3D-procedural pixel paint into UV1
  -> split into panels -> sockets + wheels -> export GLB/FBX/.blend -> previews
"""
import sys, os, math, importlib, json
import numpy as np
import bpy, bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "cars"))
sys.path.insert(0, HERE)
import palette as PAL
import wheel as WHEEL
import features as FEAT
import spoiler as SPOIL

TEXEL = 64            # px per metre, body (spec)
RING_N = 12
BANDS = ["floor", "rocker", "lower", "upper", "window", "roof"]

# ---------------------------------------------------------------- helpers
def curve(prof, key):
    pts = sorted(prof.K[key])
    xs, ys = zip(*pts)
    return lambda y: float(np.interp(y, xs, ys))


def tyre_radius(t):
    w, a, rim = t
    return (rim * 25.4 + 2 * w * a / 100) / 2000.0


def stations(prof, R):
    ys = set(round(y, 4) for y in prof.EXTRA_STATIONS)
    for ya in prof.AXLES:
        for f in (-1, -.7, -.35, 0, .35, .7, 1):
            ys.add(round(ya + f * R, 4))
    ys = sorted(ys, reverse=True)
    # merge stations closer than 3 cm
    out = []
    for y in ys:
        if not out or out[-1] - y > 0.03:
            out.append(y)
    return out


def build_rings(prof):
    r_t = tyre_radius(prof.TYRE)
    R = getattr(prof, "ARCH_R", r_t + 0.048)
    S = stations(prof, R)
    c = {k: curve(prof, k) for k in prof.K}
    rings = []
    meta = []
    for y in S:
        deck = y > prof.Y_COWL + 1e-4 or y < prof.Y_REAR_GLASS_BOT - 1e-4
        x3, z3 = c["x_max"](y), c["z_mid"](y)
        x4, z4 = c["x_belt"](y), c["z_belt"](y)
        zt = c["z_top"](y)
        if deck:
            x5, z5 = x4 - 0.12, zt - 0.015
        else:
            x5, z5 = c["x_top"](y), zt - 0.04
        zs, zf = c["z_sill"](y), c["z_floor"](y)
        arch = None
        for ya in prof.AXLES:
            dy = abs(y - ya)
            if dy < R - 1e-4:
                arch = r_t + math.sqrt(R * R - dy * dy)
            elif dy <= R + 1e-4:
                arch = zs
        if arch is not None:
            p2 = (x3 - 0.05, max(arch, zs))
            p1 = (x3 - 0.27, max(arch, zs))
        else:
            p2 = (x3 - 0.05, zs)
            p1 = (x3 - 0.22, zf)
            drop = getattr(prof, "SKIRT_DROP", None)
            if drop and prof.AXLES[1] + R < y < prof.AXLES[0] - R:
                p1 = (x3 - 0.045, zs - drop)
        z3 = max(z3, p2[1] + 0.07)
        half = [p1, p2, (x3, z3), (x4, z4), (x5, z5)]
        ring = [(0, y, zf)]
        ring += [(hx, y, hz) for hx, hz in half]
        ring += [(0, y, zt)]
        ring += [(-hx, y, hz) for hx, hz in reversed(half)]
        rings.append(ring)
        meta.append(dict(y=y, deck=deck, arch=arch is not None))
    return S, rings, R


# ring index -> (band, side, v)
def edge_band(j):
    # edges j: 0..5 right side bottom->top, 6..11 left top->bottom
    if j <= 5:
        return j, "R"
    return 11 - j, "L"


RING_V = [0, 1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]


def part_for(prof, band, side, ymid, cap=None, level=None, R=0.34):
    p = _part_for(prof, band, side, ymid, cap, level, R)
    ytg = getattr(prof, "Y_TAILGATE", None)        # pickups: only the last panel is the tailgate
    if ytg is not None and p == "tailgate" and cap is None and ymid >= ytg:
        p = "body"
    return p


def _part_for(prof, band, side, ymid, cap=None, level=None, R=0.34):
    yfa, yra = prof.AXLES
    f_bump, r_bump = yfa + R, yra - R
    dF, dM, dR = prof.DOOR_LINES
    s = side
    if cap == "front":
        return "bumper_F" if level <= 3 else "hood"
    if cap == "rear":
        return "bumper_R" if level <= 2 else "tailgate"
    if band == 1 and yfa - R > ymid > yra + R:
        return f"skirt_{s}"
    if band in (0, 1):
        if ymid > f_bump: return "bumper_F"
        if ymid < r_bump: return "bumper_R"
        return "body"
    if band == 2:
        if ymid > f_bump: return "bumper_F"
        if ymid > dF: return f"fender_F{s}"
        if ymid > dM: return f"door_F{s}"
        if ymid > dR: return f"door_R{s}"
        if ymid < r_bump: return "bumper_R"
        return "body"
    if band == 3:
        if ymid > f_bump: return "bumper_F"
        if ymid > dF: return f"fender_F{s}"
        if ymid > dM: return f"door_F{s}"
        if ymid > getattr(prof, "DOOR_R_TOP_END", dR): return f"door_R{s}"
        if ymid < prof.Y_REAR_GLASS_BOT + 0.04: return "tailgate"
        return "body"
    if band == 4:
        if ymid > prof.Y_HOOD_FRONT: return "bumper_F"
        if ymid > prof.Y_COWL: return "hood"
        if ymid < prof.Y_REAR_GLASS_BOT: return "tailgate"
        if dF >= ymid > dM: return f"door_F{s}"
        if dM >= ymid > getattr(prof, "DOOR_R_TOP_END", dR): return f"door_R{s}"
        return "body"
    # band 5
    if ymid > prof.Y_HOOD_FRONT: return "bumper_F"
    if ymid > prof.Y_COWL: return "hood"
    if ymid < prof.Y_ROOF_REAR: return "tailgate"
    return "body"


def glass_for(prof, band, ymid):
    if band == 4 and prof.SIDE_GLASS_REAR < ymid < prof.Y_COWL:
        return True
    if band == 5 and prof.Y_ROOF_FRONT < ymid < prof.Y_COWL:
        return True
    if band == 5 and prof.Y_REAR_GLASS_BOT < ymid < prof.Y_ROOF_REAR:
        return True
    return False


# ---------------------------------------------------------------- mesh
def build_mesh(prof):
    S, rings, R = build_rings(prof)
    verts = [v for ring in rings for v in ring]
    vparam = [RING_V[i] for _ in rings for i in range(RING_N)]
    faces, info = [], []
    vid = lambda s, i: s * RING_N + (i % RING_N)
    for k in range(len(S) - 1):
        ymid = (S[k] + S[k + 1]) / 2
        for j in range(RING_N):
            band, side = edge_band(j)
            faces.append([vid(k, j), vid(k, j + 1), vid(k + 1, j + 1), vid(k + 1, j)])
            info.append(dict(band=band, side=side, part=part_for(prof, band, side, ymid, R=R),
                             glass=glass_for(prof, band, ymid)))
    # ladder caps: levels 1..6 (p1..p5 pairs, p6 apex)
    for s, cap in ((0, "front"), (len(S) - 1, "rear")):
        R_ = lambda i: vid(s, i)          # right p_i = i, left p_i = 12 - i
        L_ = lambda i: vid(s, RING_N - i)
        faces.append([L_(1), vid(s, 0), R_(1), R_(2), L_(2)]); lv = [1]
        for i in (2, 3, 4):
            faces.append([L_(i), R_(i), R_(i + 1), L_(i + 1)]); lv.append(i)
        faces.append([L_(5), R_(5), vid(s, 6)]); lv.append(5)
        for l in lv:
            info.append(dict(band=10 + l, side="C", part=part_for(prof, None, "C", 0, cap, l, R),
                             glass=False))
    return verts, faces, info, vparam, S, R


def add_mirrors(verts, faces, info, vparam, prof):
    m = prof.MIRROR
    sy, sz = m["size"]
    for sgn, s in ((1, "R"), (-1, "L")):
        x0 = sgn * m["x_in"]
        x1 = sgn * (m["x_in"] + m["length"])
        base = len(verts)
        # tapered box: inner face small (stalk), outer face full size
        pts = []
        for x, scale in ((x0, 0.45), (x1, 1.0)):
            for dy, dz in ((-sy / 2, -sz / 2), (sy / 2, -sz / 2), (sy / 2, sz / 2), (-sy / 2, sz / 2)):
                pts.append((x, m["y"] + dy * scale, m["z"] + dz * scale))
        verts += pts
        vparam += [0] * 8
        q = [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
        for f in q:
            faces.append([base + i for i in f])
            info.append(dict(band=-1, side=s, part=f"mirror_{s}", glass=False))


def make_object(name, verts, faces, info, vparam, extra_parts=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    parts = sorted(set(d["part"] for d in info) | set(extra_parts))
    a_part = me.attributes.new("part", "INT", "FACE")
    a_band = me.attributes.new("band", "INT", "FACE")
    a_glass = me.attributes.new("glass", "BOOLEAN", "FACE")
    a_v = me.attributes.new("ring_v", "FLOAT", "POINT")
    a_part.data.foreach_set("value", [parts.index(d["part"]) for d in info])
    a_band.data.foreach_set("value", [d["band"] for d in info])
    a_glass.data.foreach_set("value", [d["glass"] for d in info])
    a_v.data.foreach_set("value", vparam)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    # outward normals
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return ob, parts


# ---------------------------------------------------------------- UVs
def uv1_unwrap(ob):
    me = ob.data
    uv = me.uv_layers.new(name="UV1_atlas")
    me.uv_layers.active = uv
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.012,
                             area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    me = ob.data
    uv = me.uv_layers["UV1_atlas"]
    # normalise texel density: smallest power-of-2 texture that holds TEXEL px/m
    a3 = sum(p.area for p in me.polygons)
    uvs = np.zeros(len(me.loops) * 2); uv.data.foreach_get("uv", uvs); uvs = uvs.reshape(-1, 2)
    a2 = 0.0
    for p in me.polygons:
        pts = uvs[p.loop_start:p.loop_start + p.loop_total]
        x, y = pts[:, 0], pts[:, 1]
        a2 += 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    for size in (64, 128, 256, 512, 1024, 2048):
        d = math.sqrt(a2 * size * size / a3)
        if d >= TEXEL:
            break
    uvs *= TEXEL / d
    uv.data.foreach_set("uv", uvs.ravel())
    used = uvs.max(axis=0)
    return size, dict(density_px_m=TEXEL, texture=size, uv_extent=used.tolist(), surface_m2=a3)


# UV2 wrap template (shared by every car). metres on a 16 m canvas @ 64 px/m = 1024 px
WRAP_M = 16.0
WRAP_REGIONS = {                       # u0, v0, w, h (metres)
    "side_L": (0.25, 13.6, 6.5, 2.2),
    "side_R": (0.25, 11.0, 6.5, 2.2),
    "top":    (0.25, 8.2, 6.5, 2.4),
    "front":  (7.25, 11.0, 2.4, 2.2),
    "rear":   (10.0, 11.0, 2.4, 2.2),
}


def uv2_region(n, band):
    if band in (0, 1) or band == -1:
        return None
    if abs(n[0]) >= 0.55:
        return "side_R" if n[0] > 0 else "side_L"
    if n[2] >= 0.45:
        return "top"
    if n[1] > 0:
        return "front"
    if n[1] < 0:
        return "rear"
    return None


def uv2_project(reg, p):
    x, y, z = p
    u0, v0, w, h = WRAP_REGIONS[reg]
    if reg == "side_L": u, v = u0 + w / 2 - y, v0 + z
    elif reg == "side_R": u, v = u0 + w / 2 + y, v0 + z
    elif reg == "top": u, v = u0 + w / 2 + y, v0 + h / 2 + x
    elif reg == "front": u, v = u0 + w / 2 - x, v0 + z
    else: u, v = u0 + w / 2 + x, v0 + z
    return u / WRAP_M, v / WRAP_M


def uv2_unwrap(ob):
    me = ob.data
    uv = me.uv_layers.new(name="UV2_wrap")
    band = np.zeros(len(me.polygons), int); me.attributes["band"].data.foreach_get("value", band)
    regs = []
    for p in me.polygons:
        reg = uv2_region(p.normal, band[p.index])
        regs.append(reg)
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            if reg is None:
                uv.data[li].uv = (0.995, 0.005)
            else:
                uv.data[li].uv = uv2_project(reg, me.vertices[me.loops[li].vertex_index].co)
    return regs


# ---------------------------------------------------------------- paint
def raster(ob, size, uv_name):
    """Rasterise loop triangles into texel buffers."""
    me = ob.data
    me.calc_loop_triangles()
    uv = me.uv_layers[uv_name]
    nT = len(me.loop_triangles)
    tri_loops = np.zeros(nT * 3, int); me.loop_triangles.foreach_get("loops", tri_loops)
    tri_poly = np.zeros(nT, int); me.loop_triangles.foreach_get("polygon_index", tri_poly)
    uvs = np.zeros(len(me.loops) * 2); uv.data.foreach_get("uv", uvs); uvs = uvs.reshape(-1, 2)
    lv = np.zeros(len(me.loops), int); me.loops.foreach_get("vertex_index", lv)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    rv = np.zeros(len(me.vertices)); me.attributes["ring_v"].data.foreach_get("value", rv)
    fN = np.zeros(len(me.polygons) * 3); me.polygons.foreach_get("normal", fN); fN = fN.reshape(-1, 3)
    # polygon edge set (to know which triangle edges are real mesh edges)
    poly_edges = {}
    for p in me.polygons:
        vs = list(p.vertices)
        poly_edges[p.index] = {frozenset((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))}
    # face adjacency through edges
    edge_faces = {}
    for p in me.polygons:
        for e in poly_edges[p.index]:
            edge_faces.setdefault(e, []).append(p.index)

    fid = np.full((size, size), -1, int)
    P = np.zeros((size, size, 3)); V = np.zeros((size, size))
    EDGE = np.full((size, size, 3), 1e9)       # px distance to each tri edge
    EOTH = np.full((size, size, 3), -1, int)   # face on the other side of that edge (-1 none / diag)
    for t in range(nT):
        L = tri_loops[t * 3:t * 3 + 3]
        f = tri_poly[t]
        q = uvs[L] * size
        q[:, 1] = size - q[:, 1]
        vi = lv[L]
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        a, b, c = q
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9: continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        if not inside.any(): continue
        yy, xx = np.nonzero(inside); yy += y0; xx += x0
        W = np.stack([w0[inside], w1[inside], w2[inside]], 1)
        fid[yy, xx] = f
        P[yy, xx] = W @ co[vi]
        V[yy, xx] = W @ rv[vi]
        area2 = abs(den)
        for k in range(3):   # edge opposite vertex k
            va, vb = vi[(k + 1) % 3], vi[(k + 2) % 3]
            e = frozenset((va, vb))
            elen = np.linalg.norm(q[(k + 1) % 3] - q[(k + 2) % 3])
            EDGE[yy, xx, k] = W[:, k] * area2 / max(elen, 1e-6)
            if e in poly_edges[f]:
                fs = [g for g in edge_faces.get(e, []) if g != f]
                EOTH[yy, xx, k] = fs[0] if fs else -2
    return fid, P, V, EDGE, EOTH, fN


def paint_uv1(ob, prof, size):
    me = ob.data
    fid, P, V, EDGE, EOTH, fN = raster(ob, size, "UV1_atlas")
    nF = len(me.polygons)
    part = np.zeros(nF, int); me.attributes["part"].data.foreach_get("value", part)
    band = np.zeros(nF, int); me.attributes["band"].data.foreach_get("value", band)
    glass = np.zeros(nF, bool); me.attributes["glass"].data.foreach_get("value", glass)

    m = fid >= 0
    f = fid[m]; Pm = P[m]; N = fN[f]; Vm = V[m]
    C = PAL.INDEX
    body = PAL.ramp(prof.PAINT)
    gl = glass[f]
    idx = np.zeros(len(f), int)
    yy, xx = np.nonzero(m)
    bay = PAL.BAYER4[yy % 4, xx % 4]

    # body paint: baked light, ordered dither into the ramp
    lum = 0.50 + 0.26 * N[:, 2] + 0.16 * (Pm[:, 2] - 0.65) - 0.05 * np.abs(N[:, 1])
    idx[:] = PAL.dither(body, lum, bay, spread=0.22)
    # glass
    glum = 0.35 + 0.35 * N[:, 2] + 0.1 * (Pm[:, 2] - 1.0)
    streak = (np.floor((Pm[:, 1] * 0.8 + Pm[:, 2]) * 64) % 23) < 3
    gi = PAL.dither(PAL.ramp("glass"), glum + 0.25 * streak, bay)
    idx[gl] = gi[gl]
    # underbody
    ub = np.isin(band[f], (0, 1))
    idx[ub] = C["under"]

    # panel seams & glass frames from real mesh edges
    ED = EDGE[m]; EO = EOTH[m]
    for k in range(3):
        other = EO[:, k]
        has = other >= 0
        o = np.where(has, other, 0)
        diff_part = has & (part[o] != part[f])
        g_other = has & glass[o]
        near1 = ED[:, k] < 1.0
        near2 = ED[:, k] < 2.0
        # glass frame: glass texel next to non-glass face (or other panel's glass)
        fr = gl & near2 & has & (~g_other | diff_part)
        idx[fr] = C["black"]
        seam = ~gl & ~ub & near1 & ((diff_part & ~g_other) | (other == -2))
        idx[seam] = C["seam_" + prof.PAINT] if ("seam_" + prof.PAINT) in C else C["black"]
    # B-pillar blackout
    bp = gl & (Pm[:, 1] > prof.B_PILLAR[0]) & (Pm[:, 1] < prof.B_PILLAR[1])
    idx[bp] = C["black"]
    # recessed features (bands written by features.py)
    B = band[f]
    mesh = ((xx // 1 + yy // 1) % 2) == 0
    g = np.isin(B, (20, 21))
    idx[g] = np.where(mesh[g], C["black"], C["plastic"])
    hlm = B == 22
    idx[hlm] = PAL.dither(PAL.ramp("white"), 0.35 + 0.4 * N[hlm, 2] + 0.25 * N[hlm, 1], bay[hlm], 0.6)
    idx[B == 25] = C["black"]
    idx[B == 26] = C["metal1"]
    idx[B == 27] = body[0]
    idx[B == 28] = np.where((yy[B == 28] // 3) % 3 == 0, C["plastic"], C["black"])   # ribbed bed liner
    idx[B == 29] = C["plastic"]
    cf = B == 30                                   # carbon / black plastic
    idx[cf] = np.where(((xx[cf] // 2 + yy[cf] // 2) % 2) == 0, C["black"], C["plastic"])
    # car specific decals
    ov = prof.paint(Pm, N, Vm, gl, body, C, B)
    keep = (ov >= 0) & ~ub
    idx[keep] = ov[keep]

    img = np.full((size, size), -1, int)
    img[m] = idx
    img = PAL.dilate(img, 4)
    return PAL.to_rgb(img), img


# ---------------------------------------------------------------- scene
def make_material(name, png_path, use_alpha=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.75
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(png_path)
    tex.interpolation = "Closest"
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "UV1_atlas"
    nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def split_parts(ob, parts, mat):
    me = ob.data
    pa = np.zeros(len(me.polygons), int); me.attributes["part"].data.foreach_get("value", pa)
    objs = []
    for pid, pname in enumerate(parts):
        nm = me.copy()
        bm = bmesh.new(); bm.from_mesh(nm)
        lay = bm.faces.layers.int.get("part")
        bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if fc[lay] != pid], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(nm); bm.free()
        for p in nm.polygons: p.use_smooth = True
        nm.set_sharp_from_angle(angle=math.radians(38))
        nm.materials.clear()
        nm.materials.append(mat)
        o = bpy.data.objects.new(pname, nm)
        bpy.context.scene.collection.objects.link(o)
        objs.append(o)
    bpy.data.objects.remove(ob)
    return objs


def add_sockets(prof, r_t):
    socks = {}
    for nm, (y, tr) in (("F", (prof.AXLES[0], prof.TRACK_F)), ("R", (prof.AXLES[1], prof.TRACK_R))):
        socks[f"wheel_{nm}L"] = (-tr / 2, y, r_t)
        socks[f"wheel_{nm}R"] = (tr / 2, y, r_t)
    socks["bumper_F"] = (0, prof.Y_NOSE, 0.40)
    socks["bumper_R"] = (0, prof.Y_TAIL, 0.40)
    socks["skirt_L"] = (-max(v for _, v in prof.K["x_max"]), 0, 0.20)
    socks["skirt_R"] = (max(v for _, v in prof.K["x_max"]), 0, 0.20)
    socks.update(prof.SOCKETS_EXTRA)
    root = bpy.data.objects.new("sockets", None)
    bpy.context.scene.collection.objects.link(root)
    for k, p in socks.items():
        e = bpy.data.objects.new("SOCKET_" + k, None)
        e.empty_display_size = 0.08
        e.location = p
        e.parent = root
        bpy.context.scene.collection.objects.link(e)
    return socks


def render_previews(outdir, name, bounds):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.44, 0.47, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 2.6
    so = bpy.data.objects.new("sun", sun); so.rotation_euler = (math.radians(50), 0, math.radians(35))
    sc.collection.objects.link(so)
    bpy.ops.mesh.primitive_plane_add(size=30)
    fl = bpy.context.object
    fm = bpy.data.materials.new("floor"); fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.16, 0.17, 1)
    fl.data.materials.append(fm)
    cam = bpy.data.cameras.new("cam"); cam.lens = 50
    co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
    tgt = Vector((0, -0.1, 0.62))
    views = {"front34": (5.2, 6.0, 2.1), "side": (8.2, -0.1, 1.0), "rear34": (-5.2, -6.2, 2.4),
             "top": (0.01, -0.1, 11.0), "front": (0, 8.5, 0.9),
             "front_close": ((2.3, 4.6, 1.25), (0.0, 1.75, 0.62)),
             "rear_close": ((-2.0, -4.6, 1.3), (0.0, -1.7, 0.70))}
    paths = []
    for vn, pos in views.items():
        tgt = Vector((0, -0.1, 0.62))
        if isinstance(pos[0], tuple):
            pos, tgt = pos[0], Vector(pos[1])
        co.location = pos
        d = tgt - Vector(pos)
        co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(outdir, f"{name}_{vn}.png")
        bpy.ops.render.render(write_still=True)
        paths.append(sc.render.filepath)
    bpy.data.objects.remove(fl); bpy.data.objects.remove(co); bpy.data.objects.remove(so)
    return paths


def uv2_template(ob, regs, path, parts):
    from PIL import Image, ImageDraw
    S = 1024
    im = Image.new("RGBA", (S, S), (30, 30, 34, 255)); dr = ImageDraw.Draw(im)
    for nm, (u0, v0, w, h) in WRAP_REGIONS.items():
        box = [u0 / WRAP_M * S, S - (v0 + h) / WRAP_M * S, (u0 + w) / WRAP_M * S, S - v0 / WRAP_M * S]
        dr.rectangle(box, outline=(90, 90, 100, 255))
        dr.text((box[0] + 4, box[1] + 4), nm, fill=(140, 140, 150, 255))
    me = ob.data
    uv = me.uv_layers["UV2_wrap"]
    pa = np.zeros(len(me.polygons), int); me.attributes["part"].data.foreach_get("value", pa)
    rng = np.random.default_rng(3)
    cols = {i: tuple(int(c) for c in rng.integers(70, 200, 3)) for i in range(len(parts))}
    for p in me.polygons:
        if regs[p.index] is None: continue
        pts = [(uv.data[l].uv[0] * S, S - uv.data[l].uv[1] * S) for l in range(p.loop_start, p.loop_start + p.loop_total)]
        dr.polygon(pts, fill=cols[pa[p.index]] + (255,), outline=(20, 20, 20, 255))
    im.save(path)


def apply_variant(prof, vname):
    """Return a shallow copy of the profile with a variant's overrides merged in."""
    import types, copy
    v = prof.VARIANTS[vname]
    P = types.ModuleType(prof.__name__ + "__" + vname)
    P.__dict__.update({k: getattr(prof, k) for k in dir(prof) if not k.startswith("__")})
    K = copy.deepcopy(prof.K)
    for key, pts in v.get("K", {}).items():
        lo, hi = min(y for y, _ in pts), max(y for y, _ in pts)
        K[key] = [(y, z) for y, z in K[key] if not (lo <= y <= hi)] + list(pts)
    P.K = K
    feats = [f for f in prof.FEATURES if f["name"] not in v.get("features_remove", ())]
    P.FEATURES = feats + list(v.get("features_add", ()))
    for k, val in v.get("set", {}).items():
        setattr(P, k, val)
    return P, v["parts"]


def export_part(src, prof, pdir, fname):
    """Re-atlas one panel on its own texture (same palette, same 64 px/m) and export it.
    Origin stays at the car origin, so it drops straight into the stock car."""
    from PIL import Image
    me = src.data.copy()
    if "UV1_atlas" in me.uv_layers:
        me.uv_layers.remove(me.uv_layers["UV1_atlas"])
    o = bpy.data.objects.new(fname, me)
    bpy.context.scene.collection.objects.link(o)
    for x in bpy.context.selected_objects: x.select_set(False)
    size, info = uv1_unwrap(o)
    # unwrap appended UV1 after UV2; rebuild UV2 so UV1_atlas is TEXCOORD_0 in the glTF
    if "UV2_wrap" in me.uv_layers:
        w = np.zeros(len(me.loops) * 2); me.uv_layers["UV2_wrap"].data.foreach_get("uv", w)
        me.uv_layers.remove(me.uv_layers["UV2_wrap"])
        me.uv_layers.new(name="UV2_wrap").data.foreach_set("uv", w)
    assert me.uv_layers[0].name == "UV1_atlas"
    rgb, _ = paint_uv1(o, prof, size)
    tex = os.path.join(pdir, fname + ".png")
    Image.fromarray(rgb).save(tex)
    me.materials.clear(); me.materials.append(make_material(fname, tex))
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(pdir, fname + ".glb"), export_format="GLB",
                              use_selection=True)
    bpy.data.objects.remove(o)
    return dict(file=fname + ".glb", verts=len(me.vertices), texture=size)


def build_body(prof):
    verts, faces, info, vparam, S, R = build_mesh(prof)
    add_mirrors(verts, faces, info, vparam, prof)
    ob, parts = make_object(prof.NAME, verts, faces, info, vparam,
                            getattr(prof, "EXTRA_PARTS", ()))
    ob = FEAT.apply_features(ob, prof, parts)
    return ob, parts, S, R


def main(profname, variant=None):
    prof = importlib.import_module(profname)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    out = os.path.join(ROOT, "out", prof.NAME); os.makedirs(out, exist_ok=True)
    pdir = os.path.join(out, "parts"); os.makedirs(pdir, exist_ok=True)

    if variant:
        vprof, vparts = apply_variant(prof, variant)
        ob, parts, S, R = build_body(vprof)
        size, _ = uv1_unwrap(ob); uv2_unwrap(ob)
        mat = bpy.data.materials.new("tmp")
        objs = {o.name: o for o in split_parts(ob, parts, mat)}
        res = {p: export_part(objs[p], vprof, pdir, f"{p}_{variant}") for p in vparts}
        print(json.dumps(res, indent=1))
        return res

    ob, parts, S, R = build_body(prof)
    size, uvinfo = uv1_unwrap(ob)
    regs = uv2_unwrap(ob)
    from PIL import Image
    rgb, index = paint_uv1(ob, prof, size)
    tex_path = os.path.join(out, f"{prof.NAME}_uv1.png")
    Image.fromarray(rgb).save(tex_path)
    # palette-index map + palette strip: engine can recolour paint by swapping the ramp
    Image.fromarray(np.clip(index, 0, 255).astype(np.uint8)).save(os.path.join(out, f"{prof.NAME}_uv1_index.png"))
    Image.fromarray(PAL.RGB[None, :, :]).save(os.path.join(out, "palette.png"))
    uv2_template(ob, regs, os.path.join(out, f"{prof.NAME}_uv2_wrap_template.png"), parts)

    mat = make_material(prof.NAME, tex_path)
    nverts = len(ob.data.vertices); nfaces = len(ob.data.polygons)
    objs = split_parts(ob, parts, mat)
    swap = {}
    for o in objs:
        if o.name in getattr(prof, "SWAP_PARTS", ()):
            swap[o.name] = export_part(o, prof, pdir, f"{o.name}_stock")

    r_t = tyre_radius(prof.TYRE)
    socks = add_sockets(prof, r_t)
    for style in WHEEL.RIMS:
        WHEEL.export_rim(prof, style, pdir)
    for style in ("roof_ext", "gt_wing"):
        so = SPOIL.build(style, socks["spoiler"], {})
        export_part(so, SPOIL.paint_profile(prof), pdir, f"spoiler_{style}")
        bpy.data.objects.remove(so)
    wheel_objs, wheel_info = WHEEL.build_wheels(prof, socks, out)

    bpy.ops.export_scene.gltf(filepath=os.path.join(out, prof.NAME + ".glb"), export_format="GLB",
                              export_extras=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, prof.NAME + ".fbx"), path_mode="COPY",
                             embed_textures=True, axis_forward="Y", axis_up="Z")
    previews = render_previews(out, prof.NAME, None)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, prof.NAME + ".blend"))

    report = dict(car=prof.NAME, stations=len(S), body_verts=nverts, body_faces=nfaces,
                  parts=parts, swap_parts=swap, uv1=uvinfo, wheel=wheel_info, sockets=socks,
                  tyre_diameter_m=round(2 * r_t, 4), arch_radius_m=round(R, 4))
    with open(os.path.join(out, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
