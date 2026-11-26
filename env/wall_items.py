"""Mod parts for the pegboard wall: one small low-poly object per catalogue item, in the garage palette.

usage: python env/wall_items.py   -> out/env/wall_items.glb

Each object is named after the catalogue key (perf/parts.json mods, or body_<slot>_<option>) and carries
extras {"mount": "wall" | "floor" | "shelf", "w": width_m, "h": height_m}. Authoring frame (Blender):
the board is the XZ plane, parts stick out toward -Y; wall parts have their origin at the back centre,
floor / shelf parts at the bottom back centre. Parts are drawn ~1.3x real size so they read at pixel
resolution. Generic on purpose: a bumper only has to read as "a bumper", not fit a particular car.
"""
import os, sys, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "env")

# swatch colours (garage palette; metal greys are in the viewer's "metal" PBR class)
C = dict(metal0="#3a3d42", metal1="#5d6168", metal2="#878c94", metal3="#b3b8bf", chrome="#8c939c",
         black="#1c1d22", black2="#2a2b31", tyre="#1b1b1e", tyre2="#26262a",
         red="#a31519", red2="#d42b2b", yellow="#dca21a", yellow2="#f5c94a", green="#25783d",
         card="#a0784a", card2="#7d5a34", label="#e6e6de", carbon="#121216", orange="#e08a1c")
SW = 4


class Item:
    def __init__(self, key, mount):
        self.key, self.mount = key, mount
        self.bm = bmesh.new(); self.col = {}

    def _tag(self, faces, c):
        for f in faces: self.col[f] = c

    def box(self, c, lo, hi):
        r = bmesh.ops.create_cube(self.bm, size=1)
        vs = r["verts"]
        for v in vs:
            v.co = Vector([(lo[i] + hi[i]) / 2 + v.co[i] * (hi[i] - lo[i]) for i in range(3)])
        self._tag({f for v in vs for f in v.link_faces}, c)

    def cyl(self, c, centre, r, h, axis="z", seg=10, r2=None):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
        vs = res["verts"]
        rot = {"z": Matrix.Identity(3), "x": Matrix.Rotation(math.pi / 2, 3, "Y"), "y": Matrix.Rotation(math.pi / 2, 3, "X")}[axis]
        for v in vs: v.co = rot @ v.co + Vector(centre)
        self._tag({f for v in vs for f in v.link_faces}, c)

    def ring(self, c, centre, r, t, axis="z", seg=10):
        """a coil turn / tyre: thin torus approximated by a short tube"""
        self.cyl(c, centre, r, t, axis, seg)

    def beam(self, c, a, b, w):
        a, b = Vector(a), Vector(b); d = b - a; L = d.length
        res = bmesh.ops.create_cube(self.bm, size=1)
        q = d.to_track_quat("Z", "Y")
        for v in res["verts"]:
            v.co = q.to_matrix() @ Vector((v.co.x * w, v.co.y * w, v.co.z * L)) + (a + b) / 2
        self._tag({f for v in res["verts"] for f in v.link_faces}, c)

    def hooks(self, xs, z):
        for x in xs: self.beam("metal2", (x, 0, z), (x, -0.06, z + 0.02), 0.012)


def items():
    out = []
    def add(key, mount):
        it = Item(key, mount); out.append(it); return it

    # --- suspension ---------------------------------------------------------------
    it = add("coilover", "wall")                          # red spring around a shock, top mount, bracket
    it.cyl("metal2", (0, -.07, 0), .028, .52, "z", 8)
    for k in range(7): it.ring("red2", (0, -.07, -.14 + k * .045), .055, .022, "z", 10)
    it.cyl("metal1", (0, -.07, .26), .07, .03, "z", 8); it.box("metal0", (-.05, -.11, -.30), (.05, -.03, -.24))
    it.hooks((0,), .29)
    it = add("springs", "wall")                           # pair of short lowering springs
    for x in (-.08, .08):
        for k in range(5): it.ring("red", (x, -.06, -.09 + k * .045), .05, .02, "z", 10)
    it.hooks((-.08, .08), .14)
    it = add("comfortshock", "wall")                      # plain shock with a black dust boot
    it.cyl("metal3", (0, -.06, .12), .02, .2, "z", 8); it.cyl("black", (0, -.06, -.08), .034, .32, "z", 8)
    it.box("metal0", (-.045, -.1, -.26), (.045, -.02, -.22)); it.hooks((0,), .23)
    it = add("strutbar", "wall")                          # tower brace: bar + two plates
    it.beam("red", (-.48, -.05, 0), (.48, -.05, 0), .035)
    for x in (-.5, .5): it.box("metal1", (x - .07, -.08, -.07), (x + .07, -.02, .07))
    it.hooks((-.3, .3), .03)
    it = add("swaybar", "wall")                           # U-shaped anti-roll bar
    it.beam("black2", (-.42, -.05, 0), (.42, -.05, 0), .028)
    for x in (-.42, .42): it.beam("black2", (x, -.05, 0), (x * 1.05, -.05, -.22), .026)
    it.hooks((-.2, .2), .02)
    it = add("rollcage", "wall")                          # small hoop section of a cage
    for x in (-.32, .32): it.beam("metal1", (x, -.05, -.32), (x * .85, -.05, .32), .03)
    it.beam("metal1", (-.27, -.05, .32), (.27, -.05, .32), .03); it.beam("metal1", (-.32, -.05, -.32), (.27, -.05, .32), .026)
    it.hooks((-.2, .2), .34)
    # --- brakes / engine ------------------------------------------------------------
    it = add("brakes", "wall")                            # drilled disc + red caliper
    it.cyl("metal2", (0, -.03, 0), .17, .03, "y", 14); it.cyl("metal0", (0, -.05, 0), .07, .03, "y", 10)
    it.box("red2", (.08, -.08, .02), (.2, -.03, .16)); it.hooks((0,), .19)
    it = add("intake", "wall")                            # cone filter on a chrome pipe
    it.cyl("red", (-.12, -.09, 0), .085, .2, "x", 10, r2=.05); it.cyl("chrome", (.08, -.09, 0), .04, .26, "x", 8)
    it.hooks((0,), .1)
    it = add("turbokit", "wall")                          # snail housing + compressor + flange
    it.cyl("metal1", (0, -.1, 0), .14, .12, "y", 12); it.cyl("metal3", (.15, -.1, .05), .07, .14, "x", 10)
    it.box("metal0", (-.06, -.14, -.22), (.06, -.06, -.12)); it.hooks((0,), .15)
    it = add("axleback", "wall")                          # short muffler + tip
    it.cyl("chrome", (0, -.08, 0), .08, .34, "x", 10); it.cyl("metal3", (.24, -.08, 0), .045, .14, "x", 8)
    it.cyl("metal1", (-.24, -.08, 0), .028, .14, "x", 6); it.hooks((-.08, .08), .09)
    it = add("catback", "wall")                           # long pipe + muffler + tip
    it.cyl("metal1", (-.26, -.08, 0), .03, .5, "x", 6); it.cyl("chrome", (.12, -.08, 0), .085, .32, "x", 10)
    it.cyl("metal3", (.33, -.08, 0), .05, .12, "x", 8); it.hooks((-.3, .1), .1)
    it = add("shortshift", "wall")                        # lever with a ball knob and base plate
    it.beam("metal2", (0, -.05, -.16), (0, -.05, .14), .018); it.cyl("black", (0, -.05, .17), .04, .07, "z", 8)
    it.box("metal0", (-.06, -.08, -.2), (.06, -.02, -.16)); it.hooks((0,), .1)
    it = add("lightweight", "wall")                       # carbon panel (bonnet skin)
    it.box("carbon", (-.32, -.04, -.22), (.32, -.01, .22)); it.box("black2", (-.32, -.045, .15), (.32, -.04, .18))
    it.hooks((-.2, .2), .24)
    # --- tyres lean on the floor under the board -----------------------------------
    for key, band in (("perftire", "metal2"), ("semislick", "yellow"), ("dragradial", "red2"), ("comforttire", "green")):
        it = add(key, "floor")
        w = .3 if key == "dragradial" else .22
        it.cyl("tyre", (0, -w / 2 - .02, .31), .31, w, "y", 14); it.cyl("tyre2", (0, -w / 2 - .03, .31), .19, w + .01, "y", 12)
        it.cyl(band, (0, -w - .035, .31), .25, .006, "y", 14)
    # --- boxed parts on the shelf ---------------------------------------------------
    for key, lab in (("remap", "orange"), ("pedalbox", "yellow"), ("soundproof", "green"), ("bushings", "red")):
        it = add(key, "shelf")
        it.box("card", (-.2, -.36, 0), (.2, -.02, .26)); it.box("card2", (-.2, -.37, .2), (.2, -.36, .26))
        it.box(lab, (-.12, -.372, .06), (.12, -.365, .16)); it.box("label", (-.1, -.375, .09), (.04, -.37, .13))
    # --- generic body kit ------------------------------------------------------------
    it = add("body_spoiler_gt_wing", "wall")
    it.box("black2", (-.6, -.16, .06), (.6, -.04, .1)); it.box("red", (-.62, -.17, -.02), (-.58, -.03, .12))
    it.box("red", (.58, -.17, -.02), (.62, -.03, .12))
    for x in (-.3, .3): it.beam("black", (x, -.1, .06), (x, -.1, -.16), .03)
    it.hooks((-.3, .3), .12)
    it = add("body_spoiler_roof_ext", "wall")             # ducktail lip
    it.box("metal2", (-.45, -.06, -.03), (.45, -.02, .03)); it.box("metal1", (-.45, -.14, .02), (.45, -.02, .05))
    it.hooks((-.25, .25), .07)
    it = add("body_bumper_F_lip", "wall")                 # front splitter lip
    it.box("metal1", (-.6, -.12, -.02), (.6, -.02, .02)); it.box("metal1", (-.66, -.1, -.015), (-.6, -.02, .05))
    it.box("metal1", (.6, -.1, -.015), (.66, -.02, .05)); it.hooks((-.3, .3), .04)
    it = add("body_bumper_F_sport", "wall")               # bumper cover with three intakes
    it.box("metal2", (-.62, -.1, -.14), (.62, -.02, .14))
    for x0, x1 in ((-.5, -.25), (-.15, .15), (.25, .5)): it.box("black", (x0, -.105, -.1), (x1, -.1, .04))
    it.hooks((-.4, .4), .16)
    it = add("body_bumper_R_diffuser", "wall")            # plate with fins
    it.box("metal1", (-.5, -.05, -.02), (.5, -.02, .02))
    for x in (-.36, -.12, .12, .36): it.box("black", (x - .012, -.14, -.1), (x + .012, -.02, .02))
    it.hooks((-.25, .25), .04)
    it = add("body_skirt_skirt", "wall")                  # side skirt strip
    it.box("metal2", (-.7, -.06, -.04), (.7, -.02, .04)); it.box("metal1", (-.7, -.08, -.06), (.7, -.04, -.03))
    it.hooks((-.4, .4), .06)
    return out


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    names = list(C)
    cols = 8; rows = (len(names) + cols - 1) // cols
    img = bpy.data.images.new("wall_items_pal", cols * SW, rows * SW, alpha=False)
    img.colorspace_settings.name = "sRGB"
    px = np.zeros((rows * SW, cols * SW, 4)); px[..., 3] = 1
    uv = {}
    for i, n in enumerate(names):
        cx, cy = i % cols, i // cols
        px[cy * SW:(cy + 1) * SW, cx * SW:(cx + 1) * SW, :3] = np.array([int(C[n][j:j + 2], 16) for j in (1, 3, 5)]) / 255
        uv[n] = ((cx + .5) / cols, (cy + .5) / rows)
    img.pixels[:] = px.ravel(); img.update(); img.pack()
    mat = bpy.data.materials.new("wall_items"); mat.use_nodes = True
    nt = mat.node_tree; t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    for it in items():
        bm = it.bm; uvl = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            for l in f.loops: l[uvl].uv = uv[it.col.get(f, "metal1")]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        vs = np.array([v.co[:] for v in bm.verts])
        me = bpy.data.meshes.new(it.key); bm.to_mesh(me); bm.free()
        me.materials.append(mat)
        o = bpy.data.objects.new(it.key, me); bpy.context.scene.collection.objects.link(o)
        o["mount"] = it.mount
        o["w"] = round(float(vs[:, 0].max() - vs[:, 0].min()), 3)
        o["h"] = round(float(vs[:, 2].max() - vs[:, 2].min()), 3)
        o["top"] = round(float(vs[:, 2].max()), 3)
        o["bottom"] = round(float(vs[:, 2].min()), 3)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "wall_items.glb"), export_format="GLB", export_extras=True)
    print("wall items:", len(bpy.data.objects))


if __name__ == "__main__":
    main()
