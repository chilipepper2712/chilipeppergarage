"""Parametric wheel (tyre + rim decal). Rims swap across every car: only scale by tyre size.

Texture 128x128 @ 128 px/m (2x body density - deliberate, rims are the hero item).
Layout (px, row 0 = top): outer disc centre (40,40) r = tyre_r*128 ; inner disc (104,40) ;
tread strip rows 104..127.
"""
import math, os
import numpy as np
import bpy, bmesh
import palette as PAL

TEX, DENS = 128, 128
SEG = 12

STOCK_RIM = dict(style="spoke", spokes=5, spoke_w=0.030, hub_r=0.055, lip=0.014,
                 color="metal", dish=0.0)

CONCAVE = (0.03, 0.06)     # aftermarket rims: face sunk 3 cm at the rim edge, 6 cm at the hub

# aftermarket rims: universal, scaled only by the car's tyre size. Generic shapes of common aftermarket
# designs, no maker names or logos. The face is painted in the "rimkey" ramp so the viewer can recolour it
# (chrome grey / bronze / black / white); a polished lip ("lip_metal") stays bare metal whatever the colour.
RIMS = {
    "stock":  STOCK_RIM,
    "six":    dict(style="six", spokes=6, hub_r=0.05, lip=0.012, color="rimkey", concave=CONCAVE),
    "eight":  dict(style="eight", spokes=8, hub_r=0.045, lip=0.012, color="rimkey", concave=CONCAVE),
    "five":   dict(style="five", spokes=5, hub_r=0.05, lip=0.042, color="rimkey", concave=CONCAVE, lip_metal=True),
    "ysp":    dict(style="ysp", spokes=5, hub_r=0.045, lip=0.012, color="rimkey", concave=CONCAVE),
    "mesh":   dict(style="mesh", spokes=14, spoke_w=0.006, hub_r=0.05, lip=0.016, color="rimkey", concave=CONCAVE),
    "rally":  dict(style="rally", spokes=12, hub_r=0.07, lip=0.014, color="rimkey", concave=CONCAVE),
    "window": dict(style="window", spokes=12, hub_r=0.06, lip=0.014, color="rimkey", concave=CONCAVE),
    "tri":    dict(style="tri", spokes=3, hub_r=0.055, lip=0.03, color="rimkey", concave=CONCAVE, lip_metal=True),
}


def ang(th, n, twist=0.0):
    """angle from the nearest of n spokes (radians, -pi/n..pi/n), spoke 0 pointing up"""
    return (th + math.pi / 2 + twist) % (2 * math.pi / n) - math.pi / n


def face_mask(style, rim, r, th, r_in):
    """spoke / face pixels between the hub and the inner edge of the lip (r_in)"""
    n, u = rim["spokes"], np.clip(r / r_in, 0, 1)
    perp = lambda d: np.abs(r * np.sin(d))
    if style == "six":                     # thick straight spokes flaring toward the rim
        return perp(ang(th, n)) < 0.017 + 0.012 * u
    if style == "eight":                   # thin spokes splitting into a narrow pair toward the rim
        d = ang(th, n); off = 0.11 * np.clip((u - 0.45) / 0.55, 0, 1)
        return (np.abs(r * np.sin(d - off)) < 0.0085) | (np.abs(r * np.sin(d + off)) < 0.0085)
    if style == "five":                    # wide spokes, broad at the hub, narrowing into the deep lip
        return perp(ang(th, n)) < 0.034 - 0.016 * u
    if style == "ysp":                     # five spokes forking into a Y that meets the next fork at the rim
        d = ang(th, n); k = np.clip((u - 0.5) / 0.5, 0, 1) * (math.pi / n) * 0.82
        stem = (perp(d) < 0.012) & (u < 0.56)
        return stem | (np.abs(r * np.sin(d - k)) < 0.0105) & (u >= 0.5) | (np.abs(r * np.sin(d + k)) < 0.0105) & (u >= 0.5)
    if style == "mesh":                    # cross-laced mesh: two spoke sets twisted against each other + inner ring
        tw = u * 1.1
        d1, d2 = ang(th, n, tw), ang(th, n, -tw)
        w = rim["spoke_w"] * (0.6 + 0.6 * u)
        return (np.abs(r * np.sin(d1)) < w) | (np.abs(r * np.sin(d2)) < w) | (np.abs(r - r_in * 0.55) < 0.005)
    if style == "rally":                   # twelve straight even spokes from a solid centre
        return perp(ang(th, n)) < 0.0085
    if style == "window":                  # solid face with one ring of trapezoid windows
        d = ang(th, n)
        win = (np.abs(d) < (math.pi / n) * (0.3 + 0.35 * u)) & (u > 0.36) & (u < 0.9)
        return ~win
    if style == "tri":                     # three broad swept spokes
        return perp(ang(th, n, 0.55 * u)) < 0.03 + 0.012 * u
    return perp(ang(th, n)) < rim.get("spoke_w", 0.02)


def export_rim(prof, style, pdir):
    """One wheel (tyre + rim) as its own glb: origin = wheel centre, axle = X, outer face +X."""
    from PIL import Image
    rim = RIMS[style]
    tex = os.path.join(pdir, f"wheel_{style}.png")
    Image.fromarray(paint_wheel(prof.TYRE, rim)).save(tex)
    me = build_mesh(prof.TYRE, f"wheel_{style}", rim.get("concave"))
    mat = bpy.data.materials.new(f"wheel_{style}"); mat.use_nodes = True
    nt = mat.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.6
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(tex); t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    me.materials.append(mat)
    o = bpy.data.objects.new(f"wheel_{style}", me)
    bpy.context.scene.collection.objects.link(o)
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(pdir, f"wheel_{style}.glb"), export_format="GLB",
                              use_selection=True)
    bpy.data.objects.remove(o)


def tyre_dims(t):
    w, a, rim = t
    r_rim = rim * 25.4 / 2000
    return w / 1000, r_rim, r_rim + w * a / 100000


def dens_for(r_t):
    return min(DENS, 39.0 / r_t)


def paint_wheel(tyre, rim):
    w, r_rim, r_t = tyre_dims(tyre)
    DENS = dens_for(r_t)
    C = PAL.INDEX
    img = np.full((TEX, TEX), -1, int)
    yy, xx = np.mgrid[0:TEX, 0:TEX] + 0.5
    bay = PAL.BAYER4[(yy.astype(int)) % 4, (xx.astype(int)) % 4]
    # outer disc
    dx, dy = (xx - 40) / DENS, (yy - 40) / DENS
    r = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    lum = 0.55 + 0.35 * (-dx - dy) / np.maximum(r, 1e-6) * np.clip(r / r_rim, 0, 1)
    disc = r <= r_t + 0.5 / DENS
    tyre_m = disc & (r > r_rim)
    img[tyre_m] = PAL.dither(PAL.ramp("tyre"), 0.35 + 0.25 * lum[tyre_m], bay[tyre_m])
    img[disc & (r > r_t - 1.2 / DENS)] = C["tyre0"]
    rimm = disc & (r <= r_rim)
    metal = PAL.ramp(rim["color"])
    img[rimm] = C["black"]                                     # gaps / shadow
    img[rimm & (r < 0.14) & (r > 0.06)] = C["brake"]           # disc brake
    lip = rimm & (r > r_rim - rim["lip"])
    style = rim.get("style", "spoke")
    r_in = r_rim - rim["lip"]
    if style == "spoke":         # stock rim: the original generic spoke
        n = rim["spokes"]
        dth = (th + math.pi / 2) % (2 * math.pi / n) - math.pi / n
        sw = rim["spoke_w"] * (0.55 + 0.45 * r / r_rim)
        spoke = rimm & (np.abs(r * np.sin(dth)) < sw) & (np.abs(dth) < math.pi / 2)
    else:
        spoke = rimm & (r < r_in + 0.003) & face_mask(style, rim, r, th, r_in)
    hub = rimm & (r < rim["hub_r"])
    face = lip | spoke | hub
    img[face] = PAL.dither(metal, lum[face], bay[face])
    if rim.get("lip_metal"):     # polished lip + a ring of rivets, bare metal whatever colour the face gets
        m = lip & (r > r_in + 0.6 / DENS)
        img[m] = PAL.dither(PAL.ramp("metal"), 0.35 + 0.65 * lum[m], bay[m])
        for k in range(2 * 12):
            a = 2 * math.pi * k / 24
            img[rimm & (np.hypot(dx - (r_in + .006) * math.cos(a), dy - (r_in + .006) * math.sin(a)) < 0.0035)] = C["metal4"]
    img[rimm & (np.abs(r - (r_rim - rim["lip"])) < 0.6 / DENS)] = C["metal0"]
    img[rimm & (r < 0.022)] = C["metal1"]                      # centre cap
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        img[rimm & (np.hypot(dx - 0.04 * math.cos(a), dy - 0.04 * math.sin(a)) < 0.007)] = C["metal0"]
    # inner disc: dark
    dx2, dy2 = (xx - 104) / DENS, (yy - 40) / DENS
    r2 = np.hypot(dx2, dy2)
    img[r2 <= r_t] = C["tyre1"]
    img[r2 <= r_rim * 0.6] = C["metal0"]
    # tread strip rows 104..127
    tr = yy >= 104
    groove = ((xx.astype(int) % 6) < 1) | ((((yy.astype(int) - 104) % 8) < 1) & ((xx.astype(int) // 6) % 2 == 0))
    img[tr] = C["tyre2"]
    img[tr & groove] = C["tyre0"]
    img[tr & ((yy.astype(int) == 104) | (yy.astype(int) == 127))] = C["tyre1"]
    img = PAL.dilate(img, 2)
    return PAL.to_rgb(img)


def build_mesh(tyre, name, concave=None):
    """tyre + rim. concave=None: flat outer face (stock). concave=(edge, centre) in metres: the rim face is
    sunk into the tyre (barrel down to `edge`) and dished further to `centre` at the hub - a concave face."""
    w, r_rim, r_t = tyre_dims(tyre)
    DENS = dens_for(r_t)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV1_atlas")
    A = [2 * math.pi * i / SEG for i in range(SEG)]
    ring = lambda x, rr: [bm.verts.new((x, rr * math.cos(a), rr * math.sin(a))) for a in A]
    def duv(cx, rr, a):
        # (cos a, sin a) on Y,Z -> pixel; Y forward = image +x, Z up = image -row
        return ((cx + rr * DENS * math.cos(a)) / TEX, 1 - (40 - rr * DENS * math.sin(a)) / TEX)
    def face(vs, uvs):
        f = bm.faces.new(vs)
        for l, uv in zip(f.loops, uvs): l[uvl].uv = uv
    outer, inner = ring(w / 2, r_t), ring(-w / 2, r_t)
    if concave is None:
        face(outer, [duv(40, r_t, a) for a in A])
    else:
        edge, centre = concave
        rimo = ring(w / 2, r_rim)                       # tyre bead line on the outer face
        rimi = ring(w / 2 - edge, r_rim)                # rim edge, sunk into the tyre
        hub = bm.verts.new((w / 2 - centre, 0, 0))      # hub, deepest point
        for i in range(SEG):
            j = (i + 1) % SEG
            face([outer[i], outer[j], rimo[j], rimo[i]], [duv(40, r_t, A[i]), duv(40, r_t, A[j]), duv(40, r_rim, A[j]), duv(40, r_rim, A[i])])
            rl = r_rim - 0.006                          # barrel wall takes the lip's pixels
            face([rimo[i], rimo[j], rimi[j], rimi[i]], [duv(40, r_rim, A[i]), duv(40, r_rim, A[j]), duv(40, rl, A[j]), duv(40, rl, A[i])])
            face([rimi[i], rimi[j], hub], [duv(40, r_rim, A[i]), duv(40, r_rim, A[j]), (40 / TEX, 1 - 40 / TEX)])
    face(list(reversed(inner)), [duv(104, r_t, -a + math.pi) for a in reversed(A)])
    for i in range(SEG):
        j = (i + 1) % SEG
        face([outer[i], inner[i], inner[j], outer[j]],
             [(i / SEG, 1 - 104 / TEX), (i / SEG, 0.0), ((i + 1) / SEG, 0.0), ((i + 1) / SEG, 1 - 104 / TEX)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me


def build_wheels(prof, socks, outdir, rim=None):
    from PIL import Image
    rim = rim or getattr(prof, "RIM", STOCK_RIM)
    tex = os.path.join(outdir, f"{prof.NAME}_wheel_stock.png")
    Image.fromarray(paint_wheel(prof.TYRE, rim)).save(tex)
    me = build_mesh(prof.TYRE, "wheel_stock")
    mat = bpy.data.materials.new("wheel_stock"); mat.use_nodes = True
    nt = mat.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.6
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(tex); t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    me.materials.append(mat)
    for p in me.polygons: p.use_smooth = False
    objs = []
    for k, (x, y, z) in socks.items():
        if not k.startswith("wheel_"): continue
        o = bpy.data.objects.new(k, me)
        o.location = (x, y, z)
        if x < 0: o.rotation_euler = (0, 0, math.pi)      # outer face points outward
        bpy.context.scene.collection.objects.link(o)
        objs.append(o)
    w, r_rim, r_t = tyre_dims(prof.TYRE)
    return objs, dict(tyre=prof.TYRE, width_m=w, rim_r_m=round(r_rim, 4), tyre_r_m=round(r_t, 4),
                      verts=len(me.vertices), texture=TEX, density_px_m=DENS, rim=rim)
