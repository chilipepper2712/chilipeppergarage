"""GLB -> web bundle that survives a strict CSP (no data:/blob: fetches):
  <name>.json : glTF JSON + geometry buffer as base64 in "x_bin" (rebuilt into a GLB in JS)
  <name>_imgN.png : textures as plain files, referenced by relative uri
usage: glb2web.py out_dir file.glb ..."""
import sys, json, struct, base64, pathlib
outdir = pathlib.Path(sys.argv[1]); outdir.mkdir(parents=True, exist_ok=True)
for src in sys.argv[2:]:
    src = pathlib.Path(src); b = src.read_bytes(); assert b[:4] == b"glTF"
    off, js, binc = 12, None, b""
    while off < len(b):
        ln, typ = struct.unpack_from("<I4s", b, off); off += 8
        if typ == b"JSON": js = json.loads(b[off:off + ln])
        elif typ == b"BIN\x00": binc = b[off:off + ln]
        off += ln
    for i, im in enumerate(js.get("images", [])):
        if "bufferView" in im:
            bv = js["bufferViews"][im.pop("bufferView")]
            data = binc[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
            name = f"{src.stem}_img{i}.png"
            (outdir / name).write_bytes(data)
            im["uri"] = name; im.pop("mimeType", None)
    js["x_bin"] = base64.b64encode(binc).decode()
    (outdir / (src.stem + ".json")).write_text(json.dumps(js, separators=(",", ":")))
    print(src.stem, len(js.get("images", [])), "images")
