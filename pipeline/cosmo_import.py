"""Convert a car from Cosmo's "Low Poly Cars" pack (cosmo-art.itch.io, user-modified) into a garage body model.

usage: python pipeline/cosmo_import.py <car.fbx> <name> <L> <W> <H> [--ref civic_fd_2008] [--grid 1000x720@40] [--nose -y|+y]

LICENCE: the pack may be used in the app but its files may not be redistributed, even edited. So the
source FBX lives in private/ and the converted model in out/<name>/; both are git-ignored. Only the
bundled viewer (the app itself) carries the model.

What it does (same contract as kenney_import.py):
  * turns the car so the nose points +Y (the pack's cars face -Y) and the left side is -X;
  * stretches the BODY to L x W x H (the pack is toy-proportioned: wide, big wheels); the pack's own
    wheels are dropped, their centres become SOCKET_wheel_FL/FR/RL/RR so our rims mount there;
  * colours faces into our palette. The pack paints by UV into a colour grid (texture-palette.png,
    1000 x 720 px, 40 px cells: 24 hue columns + a grey column). The texture itself isn't needed: each
    face's cell tells its role. Grey cells: the one with the most upward-facing area is the body paint
    -> our KEY ramp (the viewer repaints it, shaded by face angle); darker greys -> plastic trim,
    lighter -> bare metal. Glass and lamps keep their own roles (head / tail by end of the car).
Output: out/<name>/<name>.glb + out/<name>/parts/wheel_*.glb (copied from --ref).
"""
import sys, os, shutil, glob, math, json, colorsys
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import palette as PAL

SW = 4                                     # texels per swatch in the atlas


def argv():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    opt = {"--ref": "civic_fd_2008", "--grid": "1000x720@40", "--nose": "-y"}
    for k in list(opt):
        if k in a:
            i = a.index(k); opt[k] = a[i + 1]; a = a[:i] + a[i + 2:]
    return a[0], a[1], float(a[2]) / 1000, float(a[3]) / 1000, float(a[4]) / 1000, opt


def main():
    src, name, L, W, H, opt = argv()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(src))
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    wheels = [o for o in meshes if o.name.lower().startswith("wheel")]
    bodies = [o for o in meshes if o not in wheels]
    rot = Matrix.Rotation(math.pi, 4, "Z") if opt["--nose"] == "-y" else Matrix.Identity(4)

    # palette atlas
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
        px[cy * SW:(cy + 1) * SW, cx * SW:(cx + 1) * SW, :3] = np.array(PAL._hex(h)) / 255.0
        uvs[h] = ((cx + 0.5) * SW / (cols * SW), (cy + 0.5) * SW / (rows * SW))
    img.colorspace_settings.name = "sRGB"
    img.pixels[:] = px.ravel(); img.update(); img.pack()   # unpacked generated images export as black

    gw, rest = opt["--grid"].split("x"); gh, cell = rest.split("@"); gw, gh, cell = int(gw), int(gh), int(cell)
    GREY_COL = gw // cell - 1
    def grid_cell(f):
        u = sum(l[uvl].uv.x for l in f.loops) / len(f.loops); v = sum(l[uvl].uv.y for l in f.loops) / len(f.loops)
        return int(u * gw // cell), int((1 - v) * gh // cell)      # column, row (row 0 = top, lighter)

    # wheel centres (after the turn)
    WC = []
    for o in wheels:
        bb = [rot @ o.matrix_world @ Vector(q) for q in o.bound_box]
        WC.append(sum(bb, Vector()) / 8)

    # body meshes -> one bmesh in world space, keeping each face's source material name
    bm = bmesh.new(); mats = []
    for o in bodies:
        tmp = bmesh.new(); tmp.from_mesh(o.data); tmp.transform(rot @ o.matrix_world)
        names = [m.name if m else "" for m in o.data.materials]
        for f in tmp.faces: mats.append(names[f.material_index] if names else "")
        me_tmp = bpy.data.meshes.new("t"); tmp.to_mesh(me_tmp); tmp.free()
        bm.from_mesh(me_tmp)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table(); bm.normal_update()

    # stretch to real size, origin midway between the axles, ground at z = 0
    vs = np.array([v.co[:] for v in bm.verts]); lo, hi = vs.min(0), vs.max(0)
    k = Vector((W / (hi[0] - lo[0]), L / (hi[1] - lo[1]), H / hi[2]))        # the pack sits its tyres on z = 0
    ys = [c.y for c in WC]; ymid = (max(ys) + min(ys)) / 2 if ys else (lo[1] + hi[1]) / 2
    for v in bm.verts:
        v.co = Vector((v.co.x * k.x, (v.co.y - ymid) * k.y, v.co.z * k.z))
    bm.normal_update()
    ys2 = [v.co.y for v in bm.verts]; yF, yR = max(ys2), min(ys2)
    # which grey cell is the paint: the one covering most upward-facing area
    up = {}
    for i, f in enumerate(bm.faces):
        col, row = grid_cell(f)
        if col == GREY_COL and mats[i].lower().startswith("metallic") and f.normal.z > 0.6: up[row] = up.get(row, 0) + f.calc_area()
    paint_row = max(up, key=up.get) if up else None
    print("paint = grey row", paint_row, {r: round(a, 2) for r, a in sorted(up.items())})

    stats = {}
    for i, f in enumerate(bm.faces):
        m = mats[i].lower(); c = f.calc_center_median(); nz = f.normal.z
        front = c.y > yF - 0.6; rear = c.y < yR + 0.6
        col, row = grid_cell(f)
        if m.startswith("glass"):
            cls = "#3d8494" if nz > 0.4 else "#17414d"
        elif m.startswith("light"):
            cls = "#dfe2e5" if front else "#d3262b" if rear else "#e08a1c"
        elif col == GREY_COL and row == paint_row:      # body paint, shaded by face angle so the facets read
            cls = blue[3] if nz > 0.25 else blue[2] if nz > -0.3 else blue[1]   # one step only: scene lights do the rest
        elif col == GREY_COL and paint_row is not None and row > paint_row:   # darker grey: plastic trim / underbody
            cls = "#111113" if c.z < 0.3 or nz < -0.5 else "#1c1d22"
        elif col == GREY_COL:                          # lighter grey: bare metal, chrome
            cls = "#b3b8bf" if row <= 6 else "#878c94"
        elif col <= 1 and row >= 6:                    # red cells: tail lamps / reflectors
            cls = "#d3262b" if rear else "#7a0d10"
        else:
            cls = "#2a2b31"
        stats[cls] = stats.get(cls, 0) + f.calc_area()
        for l in f.loops: l[uvl].uv = uvs[cls]

    me = bpy.data.meshes.new("body"); bm.to_mesh(me); bm.free()
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o)
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    me.materials.clear(); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = False
    body = bpy.data.objects.new("body", me); bpy.context.scene.collection.objects.link(body)

    # sockets at the pack's wheel centres; our rims (sized for --ref's tyre) touch the ground
    t = json.load(open(os.path.join(ROOT, "data", "garage-db.json")))["models"][opt["--ref"]]["tyre"]
    rref = (t[2] * 25.4 + 2 * t[0] * t[1] / 100) / 2000
    for c in WC:
        key = ("F" if c.y > ymid else "R") + ("L" if c.x < 0 else "R")
        e = bpy.data.objects.new("SOCKET_wheel_" + key, None)
        e.location = (c.x * k.x, (c.y - ymid) * k.y, rref)
        bpy.context.scene.collection.objects.link(e)
    out = os.path.join(ROOT, "out", name); os.makedirs(os.path.join(out, "parts"), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + ".glb"), export_format="GLB", export_yup=True)
    for f_ in glob.glob(os.path.join(ROOT, "out", opt["--ref"], "parts", "wheel_*.glb")):
        shutil.copy(f_, os.path.join(out, "parts"))
    tot = sum(stats.values())
    print(f"{name}: stretch x{k.x:.3f} y{k.y:.3f} z{k.z:.3f}, faces {len(me.polygons)}, verts {len(me.vertices)}, "
          f"wheelbase {(max(ys) - min(ys)) * k.y:.3f} m, track {abs(WC[0].x) * 2 * k.x:.3f} m")
    print("  colour share: " + ", ".join(f"{c} {a / tot:.0%}" for c, a in sorted(stats.items(), key=lambda t: -t[1])))


if __name__ == "__main__":
    main()
