// Pegboard wall: every picked part hangs on the board (or stands on the shelf / floor) instead of being
// fitted to the car. Parts appear one after another with a little swing; hover or tap one to see what
// it is, tap again to pin the card (with a button to take it off). A "wall" camera view frames the board.
import * as THREE from "three";

const G = window.__garage;
const $ = id => document.getElementById(id);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

// anchors from env/anchors.json (Blender xyz -> three: x, z, -y)
const BOARD = { x: 5.46, y0: 0.55, y1: 2.65, z0: -0.95, z1: -3.25 };      // board plane, world (three) coords
const SHELF = { x: 5.38, y: 2.14, z0: 0.65, z1: -0.75 };                    // top of the kept shelf
const ROWS = [                                                             // board rows, top to bottom
  { y: 2.42, keys: ["body_spoiler_gt_wing", "body_spoiler_roof_ext", "body_bumper_F_lip", "body_bumper_F_sport"] },
  { y: 2.03, keys: ["body_bumper_R_diffuser", "body_skirt_skirt"] },
  { y: 1.55, keys: ["coilover", "springs", "comfortshock", "strutbar", "swaybar", "brakes", "rollcage"] },
  { y: 0.98, keys: ["intake", "turbokit", "axleback", "catback", "shortshift", "lightweight"] },
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
const wash = new THREE.SpotLight("#f2f4f8", 6, 6, 0.75, 0.6, 1.4);
wash.position.set(3.7, 3.1, -2.1); wash.target.position.set(BOARD.x, 1.6, -2.1);
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
    const ws = ks.map(k => protos[k].userData.w), gap = 0.1;
    const total = ws.reduce((a, b) => a + b, 0) + gap * (ks.length - 1);
    const s = Math.min(1, width / total);
    let z = mid + (total * s) / 2;                                   // board runs toward -z
    ks.forEach((k, i) => {
      const w = ws[i] * s; z -= w / 2;
      pos[k] = { p: new THREE.Vector3(BOARD.x, row.y, z), s, mount: "wall" };
      z -= w / 2 + gap * s;
    });
  }
  FLOOR.filter(k => keys.includes(k)).forEach((k, i) => { pos[k] = { p: new THREE.Vector3(BOARD.x - 0.05, 0.0, BOARD.z0 - 0.45 - i * 0.5), s: 1, mount: "floor" }; });
  SHELFK.filter(k => keys.includes(k)).forEach((k, i) => { pos[k] = { p: new THREE.Vector3(SHELF.x, SHELF.y, SHELF.z0 - i * 0.46), s: 1, mount: "shelf" }; });
  return pos;
}

let sig = "", wantWall = 0, wantCar = 0;
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
  if (s !== sig) { const first = !sig; sig = s; const n = sync(); if (n && !first && !document.body.classList.contains("intro")) wantWall = performance.now(); }
  // a build (Ớt) changes wheels and parts together: let the events settle, parts on the wall win
  const t = performance.now();
  if ((wantWall || wantCar) && t - Math.max(wantWall, wantCar) > 250) {
    if (wantWall) focusWall(); else focusCar();
    wantWall = wantCar = 0;
  }
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
  stepCam();
});

// ---- camera: car view <-> wall view -------------------------------------------------------
const WALL_VIEW = { pos: new THREE.Vector3(1.9, 1.85, 0.25), target: new THREE.Vector3(5.3, 1.55, -1.6) };
let carView = null, tween = null, view = "car";
function goTo(pos, target) {
  const c = G.controlsRef();
  tween = { t0: performance.now(), p0: G.camera.position.clone(), q0: c.target.clone(), p1: pos.clone(), q1: target.clone() };
  if (reduce) tween.t0 -= 1e6;
}
function stepCam() {
  if (!tween) return;
  const c = G.controlsRef(), k = Math.min(1, (performance.now() - tween.t0) / 900), e = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2;
  G.camera.position.lerpVectors(tween.p0, tween.p1, e); c.target.lerpVectors(tween.q0, tween.q1, e);
  if (k >= 1) tween = null;
}
function focusWall() {
  if (G.getRoom() !== "garage" || view === "wall") return;
  const c = G.controlsRef();
  carView = { pos: G.camera.position.clone(), target: c.target.clone() };
  view = "wall"; goTo(WALL_VIEW.pos, WALL_VIEW.target); syncBtn();
}
function focusCar() {
  if (view === "car") return;
  view = "car";
  if (carView) goTo(carView.pos, carView.target); else goTo(new THREE.Vector3(4.6, 1.75, 5.9), new THREE.Vector3(0, 0.65, 0));
  syncBtn();
}
// view toggle above the room buttons
const vb = document.createElement("button");
vb.type = "button"; vb.id = "viewBtn"; vb.className = "viewbtn";
$("roomBox").prepend(vb);
function syncBtn() { vb.innerHTML = view === "wall" ? `${IC("car")}<span>Xem xe</span>` : `${IC("grid")}<span>Tường đồ</span>`; vb.setAttribute("aria-pressed", view === "wall"); }
vb.addEventListener("click", () => (view === "wall" ? focusCar() : focusWall()));
syncBtn();
// things that change the car itself bring the camera back to it
let carSig = "";
G.HOOKS.change.push(() => {
  const s = [G.state.wheel, G.state.paint, G.state.lower, G.state.car].join("|");
  if (carSig && s !== carSig) wantCar = performance.now();
  carSig = s;
});
document.querySelector("#rooms")?.addEventListener("click", () => { view = "car"; tween = null; syncBtn(); });

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
  tip.innerHTML = `<b>${d.name}</b><span>${d.sub}</span>${d.dk ? `<span class="dk-${d.lv}">${d.dk}</span>` : ""}`
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
window.__wall = { hung, root, wanted, ready: () => ready, view: () => view };
