// Garage views: Xưởng (the bay), Phụ tùng độ (standing in front of the pegboard), Dyno (the car rolls onto
// the chassis dyno in the front-left cell). Hầm gió stays in tunnel.js; this module hands over to it.
// The dyno cell's two screens are live canvases: idle pages cycle like a running PC, and during a run
// they show rpm / wheel horsepower from the simulator while the wheels spin.
import * as THREE from "three";

const G = window.__garage;
const $ = id => document.getElementById(id);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

// cell anchors (env/anchors.json, Blender -> three: x, z, -y)
const DYNO = { x: -3.4, roll: 5.0 };                 // roller line, world z
const BOARD = { x: 5.46, y: 1.32, zc: 0.9, w: 5.4 };

// the dyno cell gets its own overhead light (on the work-light dimmer, so it follows the intro)
const cellLight = new THREE.SpotLight("#eef3ff", 9, 9, 0.85, 0.55, 1.3);
cellLight.position.set(DYNO.x + 0.6, 3.9, DYNO.roll - 1.3); cellLight.target.position.set(DYNO.x, 0, DYNO.roll - 1.3);
G.scene.add(cellLight, cellLight.target); G.GARAGE_OBJS.push(cellLight); G.dimReg("work", cellLight);

let view = "garage", camTween = null, carTween = null, garageCam = null;
const ease = k => (k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2);

function tweenCam(pos, target, ms = 900) {
  return new Promise(res => {
    camTween = { t0: performance.now() - (reduce ? 1e6 : 0), ms, p0: G.camera.position.clone(), q0: G.controls.target.clone(), p1: pos, q1: target, res };
  });
}
function tweenCar(pos, ms = 1300) {
  return new Promise(res => { carTween = { t0: performance.now() - (reduce ? 1e6 : 0), ms, a: G.carRoot.position.clone(), b: pos, res }; });
}
function wheelbase() { const c = window.__perf && window.__perf.cars[G.state.car]; return c ? c.wheelbase : 2.7; }
const dynoCarPos = () => new THREE.Vector3(DYNO.x, 0, DYNO.roll - wheelbase() / 2);

function partsCam() {
  const asp = G.camera.aspect, half = Math.atan(Math.tan(THREE.MathUtils.degToRad(G.camera.fov / 2)) * asp);
  const d = Math.max(3.6, (BOARD.w / 2 + 0.35) / Math.tan(half));
  return { pos: new THREE.Vector3(BOARD.x - d, BOARD.y + 0.15, BOARD.zc), target: new THREE.Vector3(BOARD.x, BOARD.y, BOARD.zc) };
}
function dynoCam() {
  const c = dynoCarPos();
  return { pos: new THREE.Vector3(c.x + 4.6, 2.3, c.z - 4.3), target: new THREE.Vector3(c.x - 0.3, 0.7, c.z + 0.7) };
}

async function go(name) {
  if (name === view) return;
  if (window.__wall) window.__wall.unpin();
  if (G.getRoom() === "tunnel") { await window.__tunnel.setRoom("garage"); G.carRoot.position.set(G.BAY_X, 0, 0); }
  if (view === "garage") garageCam = { pos: G.camera.position.clone(), target: G.controls.target.clone() };
  if ($("tSpin").checked) { $("tSpin").checked = false; }
  G.carRoot.rotation.y = Math.PI;
  const prev = view; view = name; press(name);
  const jobs = [];
  if (name === "dyno") { const c = dynoCam(); jobs.push(tweenCam(c.pos, c.target, 1200), tweenCar(dynoCarPos())); }
  else {
    if (prev === "dyno") jobs.push(tweenCar(new THREE.Vector3(G.BAY_X, 0, 0)));
    if (name === "parts") { const c = partsCam(); jobs.push(tweenCam(c.pos, c.target)); }
    else { const c = garageCam || { pos: new THREE.Vector3(-3.1, 2.4, 5.6), target: new THREE.Vector3(1.4, 0.75, -0.5) }; jobs.push(tweenCam(c.pos.clone(), c.target.clone())); }
  }
  await Promise.all(jobs);
}
function press(name) { document.querySelectorAll("#rooms [data-room]").forEach(b => b.setAttribute("aria-pressed", b.dataset.room === name)); }

for (const name of ["garage", "parts", "dyno"]) {
  const b = document.querySelector(`#rooms [data-room="${name}"]`);
  if (b) b.addEventListener("click", () => go(name));
}
// going into the wind tunnel: the car must be back on its spot first
document.querySelector('#rooms [data-room="tunnel"]').addEventListener("click", () => {
  camTween = carTween = null; G.carRoot.position.set(0, 0, 0); view = "tunnel";
}, true);
window.__views = { go, current: () => view };

// ---- dyno screens -------------------------------------------------------------------
const SW = 160, SH = 100;
const screens = [];
function attach(name, page0) {
  const o = G.scene.getObjectByName(name);
  if (!o) return false;
  const cv = document.createElement("canvas"); cv.width = SW; cv.height = SH;
  const tex = new THREE.CanvasTexture(cv); tex.magFilter = tex.minFilter = THREE.NearestFilter; tex.colorSpace = THREE.SRGBColorSpace;
  o.traverse(m => { if (m.isMesh) { m.material = new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }); m.material.color.setScalar(1.25); } });
  screens.push({ cv, g: cv.getContext("2d"), tex, page0 });
  return true;
}
let attached = false;
const C = { bg: "#071320", grid: "#12324c", line: "#3fd0ff", hot: "#ffb43a", text: "#cfe8ff", dim: "#5f86a6", ok: "#7be08a" };
function demoCurve(t) { return Math.sin(t * Math.PI * 0.9) * 0.85 + 0.1 * t; }
function draw(s, now) {
  const g = s.g, run = window.__dynoRun, t = now / 1000;
  g.fillStyle = C.bg; g.fillRect(0, 0, SW, SH);
  g.font = "8px monospace"; g.textBaseline = "top";
  const active = run && now - run.t0 < run.dur + 6000;
  if (active) {
    const k = Math.min(1, (now - run.t0) / run.dur), pts = run.b, n = Math.max(2, Math.round(k * pts.length));
    const maxHp = Math.max(...run.b.map(p => p.whp), ...run.a.map(p => p.whp)) * 1.1;
    const rpm0 = pts[0].rpm, rpm1 = pts[pts.length - 1].rpm;
    const X = r => 8 + (r - rpm0) / (rpm1 - rpm0) * (SW - 16), Y = v => SH - 12 - v / maxHp * (SH - 34);
    g.strokeStyle = C.grid; for (let i = 0; i < 5; i++) { g.beginPath(); g.moveTo(8, 22 + i * 16); g.lineTo(SW - 8, 22 + i * 16); g.stroke(); }
    g.strokeStyle = C.dim; g.beginPath(); run.a.forEach((p, i) => (i ? g.lineTo(X(p.rpm), Y(p.whp)) : g.moveTo(X(p.rpm), Y(p.whp)))); g.stroke();
    g.strokeStyle = C.hot; g.lineWidth = 2; g.beginPath();
    for (let i = 0; i < n; i++) (i ? g.lineTo(X(pts[i].rpm), Y(pts[i].whp)) : g.moveTo(X(pts[i].rpm), Y(pts[i].whp)));
    g.stroke(); g.lineWidth = 1;
    const cur = pts[n - 1];
    g.fillStyle = k < 1 ? (Math.floor(t * 4) % 2 ? C.hot : C.text) : C.ok;
    g.fillText(k < 1 ? "● ĐANG ĐO" : "✓ XONG", 6, 4);
    g.fillStyle = C.text;
    g.fillText(`${String(Math.round(cur.rpm)).padStart(4)} rpm`, 62, 4);
    g.fillText(`${Math.round(cur.whp)} whp`, 116, 4);
    return;
  }
  // idle: cycle pages like a live PC, numbers jitter
  const page = (Math.floor(t / 3.5) + s.page0) % 3;
  g.fillStyle = C.dim; g.fillText(["CHỜ XE", "LỊCH SỬ ĐO", "CẢM BIẾN"][page], 6, 4);
  g.fillText(new Date().toTimeString().slice(0, 8), SW - 46, 4);
  if (page === 0) {
    const rpm = 820 + Math.round(Math.sin(t * 7) * 20 + (Math.random() - .5) * 30);
    for (const [i, [lab, val, max]] of [["RPM", rpm, 8000], ["KM/H", 0, 260], ["°C", 86 + Math.round(Math.sin(t) * 2), 130]].entries()) {
      const cx = 30 + i * 50, cy = 58, r = 20;
      g.strokeStyle = C.grid; g.beginPath(); g.arc(cx, cy, r, Math.PI * .75, Math.PI * 2.25); g.stroke();
      const a = Math.PI * .75 + Math.min(1, val / max) * Math.PI * 1.5;
      g.strokeStyle = C.hot; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a) * (r - 3), cy + Math.sin(a) * (r - 3)); g.stroke();
      g.fillStyle = C.text; g.fillText(String(val), cx - 10, cy + 12); g.fillStyle = C.dim; g.fillText(lab, cx - 8, cy + 22);
    }
  } else if (page === 1) {
    g.strokeStyle = C.grid; for (let i = 0; i < 5; i++) { g.beginPath(); g.moveTo(8, 22 + i * 16); g.lineTo(SW - 8, 22 + i * 16); g.stroke(); }
    const sweep = (t % 3.5) / 3.5;
    g.strokeStyle = C.line; g.beginPath();
    for (let i = 0; i <= 60 * sweep; i++) { const u = i / 60, x = 8 + u * (SW - 16), y = SH - 12 - demoCurve(u) * (SH - 36); i ? g.lineTo(x, y) : g.moveTo(x, y); }
    g.stroke();
  } else {
    const rows = [["Nhiệt độ khí nạp", 31], ["Áp suất phòng", 1008], ["Độ ẩm", 64], ["Quạt gió", 0], ["Con lăn", 0]];
    rows.forEach(([lab, v], i) => {
      g.fillStyle = C.dim; g.fillText(lab, 8, 20 + i * 14);
      g.fillStyle = C.text; g.fillText(String(v + (Math.random() < .3 ? Math.round((Math.random() - .5) * 3) : 0)), 120, 20 + i * 14);
    });
    if (Math.floor(t * 2) % 2) { g.fillStyle = C.ok; g.fillRect(8, SH - 10, 5, 7); }
  }
}

// ---- per frame ----------------------------------------------------------------------
let lastDraw = 0;
G.HOOKS.frame.push((dt) => {
  const now = performance.now();
  if (camTween) {
    const k = Math.min(1, (now - camTween.t0) / camTween.ms), e = ease(k);
    G.camera.position.lerpVectors(camTween.p0, camTween.p1, e); G.controls.target.lerpVectors(camTween.q0, camTween.q1, e);
    if (k >= 1) { const r = camTween.res; camTween = null; r(); }
  }
  if (carTween) {
    const k = Math.min(1, (now - carTween.t0) / carTween.ms), e = ease(k);
    G.carRoot.position.lerpVectors(carTween.a, carTween.b, e);
    if (k >= 1) { const r = carTween.res; carTween = null; r(); }
  }
  if (!attached) attached = attach("EMIT_dynoA", 0) & attach("EMIT_dynoB", 1) || screens.length > 0;
  // screens refresh ~8 times a second (reads as a working PC, keeps it cheap)
  if (screens.length && G.getRoom() === "garage" && now - lastDraw > 120) {
    lastDraw = now;
    for (const s of screens) { draw(s, now); s.tex.needsUpdate = true; }
  }
  // wheels spin on the rollers while a run is in progress
  const run = window.__dynoRun;
  if (run && view === "dyno" && now - run.t0 < run.dur) {
    const k = (now - run.t0) / run.dur;
    for (const w of G.wheelGroup.children) w.rotateX(-(8 + 70 * k) * dt);
  }
});
