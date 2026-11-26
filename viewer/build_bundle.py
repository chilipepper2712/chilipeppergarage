"""Inline every model + texture into index.html (index.src.html + bundle -> index.html).

The mobile artifact viewer refuses the page's side files (HTTP 403), so nothing is fetched:
geometry ships as base64 (rebuilt into a GLB in JS), textures as data: image URIs that the page
attaches itself (CSP allows data: images, but not data: fetches, so GLTFLoader never loads them)."""
import json, struct, base64, pathlib, glob

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARS = ["mazda2_2013", "civic_fd_2008", "cx5_2020", "mini_f55_2018", "ranger_raptor_2019", "xpander_2020"]
SRC = {"env/garage": ROOT / "out/env/garage.glb", "env/tunnel": ROOT / "out/env/tunnel.glb", "env/wall_items": ROOT / "out/env/wall_items.glb"}
for car in CARS:
    SRC[car] = ROOT / f"out/{car}/{car}.glb"
    for f in sorted(glob.glob(str(ROOT / f"out/{car}/parts/*.glb"))):
        stem = pathlib.Path(f).stem
        if stem.endswith("_stock") and not stem.startswith("wheel_"):
            continue                      # stock panels come with the car itself
        SRC[f"{car}/parts/{stem}"] = pathlib.Path(f)


def pack(path):
    b = path.read_bytes(); off, js, binc = 12, None, b""
    while off < len(b):
        ln, typ = struct.unpack_from("<I4s", b, off); off += 8
        if typ == b"JSON": js = json.loads(b[off:off + ln])
        elif typ == b"BIN\x00": binc = b[off:off + ln]
        off += ln
    imgs = []
    for im in js.get("images", []):
        bv = js["bufferViews"][im["bufferView"]]
        o = bv.get("byteOffset", 0)
        imgs.append("data:image/png;base64," + base64.b64encode(binc[o:o + bv["byteLength"]]).decode())
    tex_src = [t["source"] for t in js.get("textures", [])]
    mat_img = {}
    for m in js.get("materials", []):
        bct = m.get("pbrMetallicRoughness", {}).pop("baseColorTexture", None)
        if bct is not None:
            mat_img[m["name"]] = tex_src[bct["index"]]
        m.pop("emissiveTexture", None)
    for k in ("images", "textures", "samplers"):
        js.pop(k, None)
    return dict(gltf=js, bin=base64.b64encode(binc).decode(), images=imgs, matImg=mat_img)


bundle = {k: pack(p) for k, p in SRC.items()}
blob = json.dumps(bundle, separators=(",", ":")).replace("</", "<\\/")
src = (ROOT / "viewer/index.src.html").read_text()
assert "<!--BUNDLE-->" in src
out = src.replace("<!--BUNDLE-->", f'<script id="bundle" type="application/json">{blob}</script>')
# performance: simulator (classic script), its data, and the UI module (must run after the 3D module)
perf = {"db": json.loads((ROOT / "data/garage-db.json").read_text()),
        "parts": json.loads((ROOT / "perf/parts.json").read_text())}
out = out.replace("<!--PERF-->", "<script>" + (ROOT / "perf/sim.js").read_text() + "</script>\n<script>" + (ROOT / "perf/db.js").read_text() + "</script>\n<script>" + (ROOT / "perf/model.js").read_text() + "</script>\n<script>" + (ROOT / "perf/planner.js").read_text() + "</script>\n"
                  + '<script id="perfdata" type="application/json">' + json.dumps(perf, ensure_ascii=False).replace("</", "<\\/") + "</script>")
assert out.rstrip().endswith("</script>")
out = out.rstrip() + '\n<script type="module">\n' + (ROOT / "viewer/perf-ui.js").read_text() + "</script>\n"
out = out.rstrip() + '\n<script type="module">\n' + (ROOT / "viewer/tunnel.js").read_text() + "</script>\n"
out = out.rstrip() + '\n<script type="module">\n' + (ROOT / "viewer/wall.js").read_text() + "</script>\n"
(ROOT / "viewer/index.html").write_text(out)
print(len(bundle), "assets,", round(len(out) / 1e6, 2), "MB")
