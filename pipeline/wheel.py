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

# aftermarket rims: universal, scaled only by the car's tyre size
RIMS = {
    "stock": STOCK_RIM,
    "mesh":  dict(style="mesh", spokes=10, spoke_w=0.008, hub_r=0.045, lip=0.016, color="metal"),
    "dish":  dict(style="dish", spokes=5, spoke_w=0.022, hub_r=0.05, lip=0.045, color="metal"),
    "steel": dict(style="steel", spokes=6, spoke_w=0.0, hub_r=0.04, lip=0.02, color="black"),
    "black6": dict(style="spoke", spokes=6, spoke_w=0.020, hub_r=0.05, lip=0.010, color="black"),
}


def export_rim(prof, style, pdir):
    """One wheel (tyre + rim) as its own glb: origin = wheel centre, axle = X, outer face +X."""
    from PIL import Image
    rim = RIMS[style]
    tex = os.path.join(pdir, f"wheel_{style}.png")
    Image.fromarray(paint_wheel(prof.TYRE, rim)).save(tex)
    me = build_mesh(prof.TYRE, f"wheel_{style}")
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
    n = rim["spokes"]
    dth = (th + math.pi / 2) % (2 * math.pi / n) - math.pi / n
    perp = np.abs(r * np.sin(dth))
    sw = rim["spoke_w"] * (0.55 + 0.45 * r / r_rim)
    spoke = rimm & (perp < sw) & (np.abs(dth) < math.pi / 2)
    style = rim.get("style", "spoke")
    if style == "mesh":          # cross-laced mesh: two spoke sets twisted against each other
        tw = r / r_rim * 0.9
        d1 = (th + tw) % (2 * math.pi / n) - math.pi / n
        d2 = (th - tw) % (2 * math.pi / n) - math.pi / n
        spoke = rimm & ((np.abs(r * np.sin(d1)) < sw) | (np.abs(r * np.sin(d2)) < sw)) & (r > 0.05)
    elif style == "dish":        # wide polished lip, short spokes
        spoke = spoke & (r < r_rim - rim["lip"] + 0.004)
    elif style == "steel":       # steelie: solid disc with round holes
        holes = np.zeros_like(rimm)
        for k in range(n):
            a = 2 * math.pi * k / n
            cx, cy = 0.105 * math.cos(a), 0.105 * math.sin(a)
            holes |= np.hypot(dx - cx, dy - cy) < 0.024
        spoke = rimm & (r < r_rim - rim["lip"]) & ~holes & (r > 0.03)
    hub = rimm & (r < rim["hub_r"])
    face = lip | spoke | hub
    img[face] = PAL.dither(metal, lum[face], bay[face])
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


def build_mesh(tyre, name):
    w, r_rim, r_t = tyre_dims(tyre)
    DENS = dens_for(r_t)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UV1_atlas")
    outer, inner = [], []
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        outer.append(bm.verts.new((w / 2, r_t * math.cos(a), r_t * math.sin(a))))
        inner.append(bm.verts.new((-w / 2, r_t * math.cos(a), r_t * math.sin(a))))
    def disc_uv(cx, a):
        # (cos a, sin a) on Y,Z -> pixel; Y forward = image +x, Z up = image -row
        px = cx + r_t * DENS * math.cos(a); py = 40 - r_t * DENS * math.sin(a)
        return (px / TEX, 1 - py / TEX)
    f = bm.faces.new(outer)
    for l in f.loops:
        a = math.atan2(l.vert.co.z, l.vert.co.y); l[uvl].uv = disc_uv(40, a)
    f = bm.faces.new(list(reversed(inner)))
    for l in f.loops:
        a = math.atan2(l.vert.co.z, l.vert.co.y); l[uvl].uv = disc_uv(104, -a + math.pi)
    for i in range(SEG):
        j = (i + 1) % SEG
        f = bm.faces.new([outer[i], inner[i], inner[j], outer[j]])
        uu = [i / SEG, i / SEG, (i + 1) / SEG, (i + 1) / SEG]
        vv = [1 - 104 / TEX, 0.0, 0.0, 1 - 104 / TEX]
        for l, u, v in zip(f.loops, uu, vv):
            l[uvl].uv = (u, v)
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
