"""Convert a Kenney Car Kit vehicle (CC0, kenney.nl) into a garage model the viewer can use.

usage: python pipeline/kenney_import.py <kenney.glb> <name> <L> <W> <H> [--ref cx5_2020]
  L W H: real size in mm the body is stretched to (Kenney cars are toy-proportioned).
  --ref: an existing model whose wheel parts (our rims) are copied for this model.

What it does:
  * turns the car so the nose points +Y and the left side is -X (our convention);
  * stretches the BODY to L x W x H; Kenney's own wheels are dropped, their centres become
    SOCKET_wheel_FL/FR/RL/RR so our rims mount there;
  * re-colours every face into our pixel palette by sampling Kenney's colormap: the car's main
    colour becomes the KEY paint ramp (so the viewer can repaint it), light blue -> glass,
    dark -> plastic, greys -> metal, white at the nose -> headlamp, red at the tail -> tail lamp;
    each face is UV-mapped onto a solid swatch of a small palette atlas.
Output: out/<name>/<name>.glb + out/<name>/parts/wheel_*.glb (copied from --ref).
"""
import sys, os, shutil, glob, colorsys, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import palette as PAL

SW = 4                                     # texels per swatch in the atlas


def argv():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ref = "cx5_2020"
    if "--ref" in a:
        i = a.index("--ref"); ref = a[i + 1]; a = a[:i] + a[i + 2:]
    return a[0], a[1], float(a[2]) / 1000, float(a[3]) / 1000, float(a[4]) / 1000, ref


def main():
    src, name, L, W, H, ref = argv()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    wheels = {o.name: o for o in meshes if o.name.startswith("wheel")}
    bodies = [o for o in meshes if not o.name.startswith("wheel")]

    # orientation from the wheel names: front wheels must end at +Y, left wheels at -X
    def centre(o):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return sum(bb, Vector()) / 8
    fl = next((o for n, o in wheels.items() if "front" in n and "left" in n), None)
    rot = Matrix.Identity(4)
    if fl is not None:
        c = centre(fl)
        if c.y < 0: rot = Matrix.Rotation(math.pi, 4, "Z")
        c2 = rot @ c
        if c2.x > 0: print("warning: front-left wheel is on +X after turning; model may be mirrored")

    # palette atlas: list of swatch colours -> (u, v)
    blue = PAL.RAMPS["blue"]
    sw = [blue[1], blue[2], blue[3], blue[4], PAL.SINGLE["seam_blue"],
          "#17414d", "#3d8494", "#1c1d22", "#2a2b31", "#5d6168", "#878c94", "#b3b8bf",
          "#dfe2e5", "#d3262b", "#7a0d10", "#e08a1c", "#111113", "#e6e6de"]
    n = len(sw); cols = 8; rows = (n + cols - 1) // cols
    img = bpy.data.images.new(f"{name}_pal", cols * SW, rows * SW, alpha=False)
    px = np.zeros((rows * SW, cols * SW, 4)); px[..., 3] = 1
    uvs = {}
    for i, h in enumerate(sw):
        cx, cy = i % cols, i // cols
        rgb = np.array(PAL._hex(h)) / 255.0
        px[cy * SW:(cy + 1) * SW, cx * SW:(cx + 1) * SW, :3] = rgb
        uvs[h] = ((cx + 0.5) * SW / (cols * SW), (cy + 0.5) * SW / (rows * SW))
    img.colorspace_settings.name = "sRGB"
    img.pixels[:] = px.ravel(); img.update(); img.pack()   # unpacked generated images export as black

    # Kenney colormap pixels for sampling
    cmap = None
    for im in bpy.data.images:
        if im is not img and im.size[0] > 0:
            cmap = (np.array(im.pixels[:]).reshape(im.size[1], im.size[0], 4), im.size[0], im.size[1])
            break
    def sample(u, v):
        a, w_, h_ = cmap
        x = min(w_ - 1, max(0, int(u % 1 * w_))); y = min(h_ - 1, max(0, int(v % 1 * h_)))
        return a[y, x, :3]

    # wheel centres and radii, read now (the source objects are removed before export)
    WINFO = {}
    for n_, o in wheels.items():
        bb = [rot @ o.matrix_world @ Vector(q) for q in o.bound_box]
        WINFO[n_] = (sum(bb, Vector()) / 8, (max(p.z for p in bb) - min(p.z for p in bb)) / 2)

    # merge body meshes into one bmesh in world space (after the turn)
    bm = bmesh.new()
    for o in bodies:
        tmp = bmesh.new(); tmp.from_mesh(o.data)
        tmp.transform(rot @ o.matrix_world)
        me_tmp = bpy.data.meshes.new("t"); tmp.to_mesh(me_tmp); tmp.free()
        bm.from_mesh(me_tmp)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()

    # stretch body to real size; wheels get only the height factor (they stay round)
    vs = np.array([v.co[:] for v in bm.verts])
    lo, hi = vs.min(0), vs.max(0)
    k = Vector((W / (hi[0] - lo[0]), L / (hi[1] - lo[1]), H / hi[2]))
    ymid = (lo[1] + hi[1]) / 2
    # recentre: origin midway between the axles
    wc = {n_: c for n_, (c, r) in WINFO.items() if n_ != "wheel-back"}
    if wc:
        ys = [c.y for c in wc.values()]; ymid = (max(ys) + min(ys)) / 2
    for v in bm.verts:
        v.co = Vector(((v.co.x) * k.x, (v.co.y - ymid) * k.y, v.co.z * k.z))

    # colour classes per face
    face_rgb = []
    for f in bm.faces:
        uv = sum((l[uvl].uv for l in f.loops), Vector((0, 0))) / len(f.loops)
        face_rgb.append(sample(uv.x, uv.y))
    face_rgb = np.array(face_rgb)
    hsv = np.array([colorsys.rgb_to_hsv(*c) for c in face_rgb])
    areas = np.array([f.calc_area() for f in bm.faces])
    sat = (hsv[:, 1] > 0.35) & (hsv[:, 2] > 0.35)
    # the car's paint: hue bin with the most saturated area (ignoring blue glass-ish light tones)
    hb = np.round(hsv[:, 0] * 24) % 24
    best, besta = None, 0
    for b_ in np.unique(hb[sat]):
        a_ = areas[sat & (hb == b_)].sum()
        if a_ > besta: best, besta = b_, a_
    paint_mask = sat & (np.abs(((hb - best + 12) % 24) - 12) <= 1)
    Lmax = L / 2
    stats = {}
    for i, f in enumerate(bm.faces):
        r, g, b = face_rgb[i]; h, s, v = hsv[i]
        c = f.calc_center_median(); nrm = f.normal
        front = c.y > Lmax - 0.45 and nrm.y > 0.3
        rear = c.y < -Lmax + 0.45 and nrm.y < -0.3
        lum = 0.3 * r + 0.59 * g + 0.11 * b
        if paint_mask[i]:
            shade = blue[1] if v < 0.55 else blue[2] if v < 0.75 else blue[3] if v < 0.92 else blue[4]
            cls = shade
        elif 0.45 < h < 0.70 and lum > 0.6 and s < 0.45 and b > r + 0.04:   # pale blue: glass
            cls = "#3d8494" if v > 0.95 else "#17414d"
        elif s < 0.25 and lum > 0.88:                      # white
            cls = "#dfe2e5" if front else "#b3b8bf"
        elif lum < 0.18:
            cls = "#111113" if c.z < 0.35 else "#1c1d22"
        elif s < 0.3:
            cls = "#2a2b31" if lum < 0.35 else ("#5d6168" if lum < 0.55 else "#878c94")
        elif (h < 0.05 or h > 0.93) and s > 0.4:          # red
            cls = "#d3262b" if rear else "#7a0d10"
        elif 0.05 <= h < 0.17 and s > 0.4:                 # orange / yellow accents
            cls = "#e08a1c" if (front or rear) else blue[3]
        else:
            cls = blue[2]
        stats[cls] = stats.get(cls, 0) + areas[i]
        for l in f.loops: l[uvl].uv = uvs[cls]

    me = bpy.data.meshes.new("body"); bm.to_mesh(me); bm.free()
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o)
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    me.materials.clear(); me.materials.append(mat)
    body = bpy.data.objects.new("body", me); bpy.context.scene.collection.objects.link(body)

    # sockets at Kenney's wheel centres (stretched)
    import json
    t = json.load(open(os.path.join(ROOT, "data", "garage-db.json")))["models"][ref]["tyre"]
    rref = (t[2] * 25.4 + 2 * t[0] * t[1] / 100) / 2000
    names = {"front-left": "FL", "front-right": "FR", "back-left": "RL", "back-right": "RR"}
    radius = []
    for n_, (c, r) in WINFO.items():
        key = next((v_ for k_, v_ in names.items() if n_.endswith(k_)), None)
        if not key: continue
        radius.append(r * k.z)
        e = bpy.data.objects.new("SOCKET_wheel_" + key, None)
        e.location = (c.x * k.x, (c.y - ymid) * k.y, rref)   # our rims (sized for --ref's tyre) touch the ground
        bpy.context.scene.collection.objects.link(e)
    out = os.path.join(ROOT, "out", name); os.makedirs(os.path.join(out, "parts"), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + ".glb"), export_format="GLB", export_yup=True)
    for f_ in glob.glob(os.path.join(ROOT, "out", ref, "parts", "wheel_*.glb")):
        shutil.copy(f_, os.path.join(out, "parts"))
    tot = sum(stats.values())
    print(f"{name}: stretch x{k.x:.2f} y{k.y:.2f} z{k.z:.2f}, tris {len(me.polygons)}, wheel radius {np.mean(radius):.3f} m")
    print("  colour share: " + ", ".join(f"{c} {a / tot:.0%}" for c, a in sorted(stats.items(), key=lambda t: -t[1])))


if __name__ == "__main__":
    main()
