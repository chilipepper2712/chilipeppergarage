"""GLB -> self-contained glTF JSON (buffer embedded as base64), for hosts that don't serve .glb."""
import sys, json, struct, base64, pathlib
for src in sys.argv[1:]:
    b = pathlib.Path(src).read_bytes()
    assert b[:4] == b"glTF"
    off, js, binc = 12, None, b""
    while off < len(b):
        ln, typ = struct.unpack_from("<I4s", b, off); off += 8
        chunk = b[off:off + ln]; off += ln
        if typ == b"JSON": js = json.loads(chunk)
        elif typ == b"BIN\x00": binc = chunk
    if js.get("buffers"):
        js["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binc).decode()
    pathlib.Path(src).with_suffix(".json").write_text(json.dumps(js, separators=(",", ":")))
