// Pegboard wall: every picked part hangs on the long board behind the car (boxed parts and tyres sit on
// the low shelf under it) instead of being fitted to the car. Seen from the normal garage angle; parts
// appear one after another with a little swing. Hover or tap one to see what it is; tap pins the card,
// which has a button to take the part off.
import * as THREE from "three";

const G = window.__garage;
const $ = id => document.getElementById(id);
const FLAG = '<svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 1.5v13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M4.2 2.2h8.6l-2 3.1 2 3.2H4.2z" fill="currentColor"/></svg>';
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

// anchors from env/anchors.json (Blender xyz -> three: x, z, -y)
const BOARD = { x: 5.46, y0: 0.3, y1: 2.34, z0: 3.6, z1: -1.8 };          // board plane, world (three) coords
const ITEM = 1.2;                                                          // parts drawn 20% larger again for readability
const ROWS = [                                                             // board rows, top to bottom
  { y: 2.04, keys: ["body_spoiler_gt_wing", "body_spoiler_roof_ext", "body_bumper_F_lip", "body_bumper_F_sport", "body_bumper_R_diffuser", "body_skirt_skirt"] },
  { y: 1.38, keys: ["coilover", "springs", "comfortshock", "strutbar", "swaybar", "brakes", "rollcage"] },
  { y: 0.72, keys: ["intake", "turbokit", "axleback", "catback", "shortshift", "lightweight"] },
];
const FLOOR = ["perftire", "semislick", "dragradial", "comforttire"];
const SHELFK = ["remap", "pedalbox", "soundproof", "bushings"];
const BODY = {
  body_spoiler_gt_wing: ["spoiler", "gt_wing", "Cánh gió GT"], body_spoiler_roof_ext: ["spoiler", "roof_ext", "Đuôi gió nối dài"],
  body_bumper_F_lip: ["bumper_F", "lip", "Lip cản trước"], body_bumper_F_sport: ["bumper_F", "sport", "Cản trước thể thao"],
  body_bumper_R_diffuser: ["bumper_R", "diffuser", "Diffuser cản sau"], body_skirt_skirt: ["skirt", "skirt", "Ốp sườn hạ"],
};
const STOCK = { bumper_F: "stock", bumper_R: "stock", skirt: "stock", spoiler: "none" };

const root = new THREE.Group(); root.name = "mod_wall";
G.scene.add(root); G.GARAGE_OBJS.push(root);
const protos = {};
let ready = false;

// a soft light washing the board (on the work-light dimmer, so it comes on with the intro sequence)
const wash = new THREE.SpotLight("#f2f4f8", 8, 8, 1.05, 0.6, 1.4);
wash.position.set(3.1, 3.4, 0.9); wash.target.position.set(BOARD.x, 1.3, 0.9);
G.scene.add(wash, wash.target); G.GARAGE_OBJS.push(wash); G.dimReg("work", wash);

G.load("env/wall_items").then(g => {
  G.prepMaterials(g, "wheel");
  g.traverse(o => { if (o.isMesh && o.parent === g) protos[o.name] = o; });
  for (const o of Object.values(protos)) { o.removeFromParent(); o.castShadow = true; o.receiveShadow = true; }
  ready = true;
});

// ---- what should be on the wall ---------------------------------------------------------
function wanted() {
  const P = window.__perf; if (!P) return [];
  const keys = P.selected();
  for (const [k, [slot, opt]] of Object.entries(BODY)) if (G.state[slot] === opt) keys.push(k);
  return keys.filter(k => protos[k]);
}
const hung = new Map();              // key -> { obj, t0, from, to }
function layout(keys) {
  const pos = {};
  const width = Math.abs(BOARD.z1 - BOARD.z0) - 0.16, mid = (BOARD.z0 + BOARD.z1) / 2;
  for (const row of ROWS) {
    const ks = row.keys.filter(k => keys.includes(k));
    if (!ks.length) continue;
    const ws = ks.map(k => protos[k].userData.w * ITEM), gap = 0.12;
    const total = ws.reduce((a, b) => a + b, 0) + gap * (ks.length - 1);
    const s = Math.min(1, width / total) * ITEM;
    let z = mid + (total * s) / 2;                                   // board runs toward -z
    ks.forEach((k, i) => {
      const w = ws[i] * s / ITEM; z -= w / 2;
      pos[k] = { p: new THREE.Vector3(BOARD.x, row.y, z), s, mount: "wall" };
      z -= w / 2 + gap * s / ITEM;
    });
  }
  // on the floor along the foot of the board: boxes from the near end, the tyre at the far end
  SHELFK.filter(k => keys.includes(k)).forEach((k, i) => { pos[k] = { p: new THREE.Vector3(BOARD.x, 0, BOARD.z0 - 0.5 - i * 0.56), s: ITEM, mount: "shelf" }; });
  FLOOR.filter(k => keys.includes(k)).forEach((k, i) => { pos[k] = { p: new THREE.Vector3(BOARD.x, 0, BOARD.z1 + 0.55 + i * 0.5), s: ITEM, mount: "floor" }; });
  return pos;
}

let sig = "";
function sync() {
  const keys = wanted(), pos = layout(keys);
  // take down what is no longer picked
  for (const [k, h] of hung) if (!pos[k]) { root.remove(h.obj); hung.delete(k); }
  // move what stays, queue what is new (hung one after another)
  let delay = 0, added = 0;
  for (const k of keys) {
    const L = pos[k]; if (!L) continue;
    const h = hung.get(k);
    if (h) { h.from = h.obj.position.clone(); h.to = L.p; h.t0 = performance.now(); h.move = true; h.obj.scale.setScalar(L.s); continue; }
    const obj = protos[k].clone(); obj.userData.key = k;
    obj.rotation.y = -Math.PI / 2;                     // authored facing -Y (Blender) -> faces into the room
    obj.scale.setScalar(L.s);
    obj.position.copy(L.p).add(new THREE.Vector3(0, L.mount === "floor" ? 0 : 0.25, 0));
    obj.visible = false;
    hung.set(k, { obj, t0: performance.now() + delay * 1000, from: obj.position.clone(), to: L.p, mount: L.mount, fresh: true });
    root.add(obj);
    delay += reduce ? 0 : 0.16; added++;
  }
  return added;
}

// ---- animation: drop onto the hook, then a damped swing ---------------------------------
G.HOOKS.frame.push(() => {
  if (!ready) return;
  const s = wanted().sort().join(",") + "|" + G.state.car;
  if (s !== sig) { const first = !sig; sig = s; const n = sync(); }
  const now = performance.now();
  for (const h of hung.values()) {
    const t = (now - h.t0) / 1000;
    if (t < 0) continue;
    h.obj.visible = true;
    const k = Math.min(1, t / 0.28), e = 1 - (1 - k) ** 3;
    h.obj.position.lerpVectors(h.from, h.to, e);
    if (h.fresh && h.mount === "wall") h.obj.rotation.x = reduce ? 0 : Math.sin(t * 9) * 0.22 * Math.exp(-t * 2.6);
    if (t > 2) { h.fresh = false; h.obj.rotation.x = 0; }
  }
});

// ---- hover / tap: what is this part ----------------------------------------------------
const tip = document.createElement("div"); tip.id = "wallTip"; tip.hidden = true; $("bay").append(tip);
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
let pinned = null;
function pick(ev) {
  const r = G.renderer.domElement.getBoundingClientRect();
  ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, G.camera);
  const hit = ray.intersectObjects([...hung.values()].map(h => h.obj).filter(o => o.visible), true)[0];
  if (!hit) return null;
  let o = hit.object; while (o && !o.userData.key) o = o.parent;
  return o ? o.userData.key : null;
}
function describe(k) {
  const P = window.__perf;
  if (BODY[k]) { const [slot, opt, name] = BODY[k]; return { name, sub: `Đồ ngoại thất · ${P.bodyPrice(slot, opt)}`, dk: null }; }
  const i = P.info(k);
  return { name: i.label, sub: `${i.brand} · ${i.price}`, dk: i.dkText, lv: i.dk };
}
function show(k, x, y, pin) {
  const d = describe(k), bay = $("bay").getBoundingClientRect();
  const flag = d.dk ? `<i class="dk-${d.lv}" title="${d.dk}" aria-label="${d.dk}">${FLAG}</i>` : "";
  tip.innerHTML = `<b>${flag}${d.name}</b><span>${d.sub}</span>`
    + (pin ? `<button type="button" class="ghost" id="wallDrop">Gỡ món này</button>` : "");
  tip.hidden = false;
  tip.style.left = Math.min(bay.width - 250, Math.max(8, x - bay.left + 14)) + "px";
  tip.style.top = Math.max(8, y - bay.top - 10) + "px";
  if (pin) $("wallDrop").addEventListener("click", e => {
    e.stopPropagation();
    if (BODY[k]) { G.state[BODY[k][0]] = STOCK[BODY[k][0]]; G.apply(); } else window.__perf.drop(k);
    pinned = null; tip.hidden = true;
  });
}
const canvas = G.renderer.domElement;
canvas.addEventListener("pointermove", ev => {
  if (ev.pointerType !== "mouse" || pinned) return;
  const k = pick(ev);
  if (k) { show(k, ev.clientX, ev.clientY, false); canvas.style.cursor = "pointer"; } else { tip.hidden = true; canvas.style.cursor = ""; }
});
let down = null;
canvas.addEventListener("pointerdown", ev => { down = [ev.clientX, ev.clientY]; });
canvas.addEventListener("pointerup", ev => {
  if (!down || Math.hypot(ev.clientX - down[0], ev.clientY - down[1]) > 6) return;     // a drag orbits, not a tap
  const k = pick(ev);
  if (k) { pinned = k; show(k, ev.clientX, ev.clientY, true); } else { pinned = null; tip.hidden = true; }
});
window.__wall = { hung, root, wanted, ready: () => ready };
