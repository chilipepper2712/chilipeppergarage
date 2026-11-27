// Dyno room: its own space off the garage (env/dyno_env.py), like the wind tunnel. Entering it, the car
// drives in through the roll-up door and stops with its front axle on the rollers; the wheels turn with
// the distance covered. The console screen and the wall monitor are live canvases: idle pages cycle like
// a running PC, during a run they show rpm / wheel horsepower from the simulator while the wheels spin.
import * as THREE from "three";

const G = window.__garage;
const $ = id => document.getElementById(id);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

// env/dyno_anchors.json (Blender -> three: x, z, -y)
const ROLL = 1.35;                 // roller line, world z
const DOOR = -7.0;                 // door wall, world z
const WHEEL_R = 0.31;

let room = null, loading = null, roomEnv = null, drive = null, inside = false, arrival = Promise.resolve();
const lights = new THREE.Group();
const saved = {};

async function ensureRoom() {
  if (room) return;
  room = await G.load("env/dyno");
  G.prepMaterials(room, "env");
  room.traverse(o => { if (o.isMesh && o.material.name === "dynoplate") { o.material.roughness = 0.55; o.material.metalness = 0.35; } });
  lights.add(new THREE.HemisphereLight("#cfd9e8", "#2a2620", 1.1));
  for (const x of [-1.4, 1.4]) {
    const l = new THREE.RectAreaLight("#e8f1ff", 4.5, 0.1, 9); l.position.set(x, 3.42, -0.3); l.lookAt(x, 0, -0.3); lights.add(l);
  }
  const key = new THREE.SpotLight("#f4f7ff", 9, 10, 0.75, 0.6, 1.2);
  key.position.set(0.6, 3.6, 0.6); key.target.position.set(0, 0, 0.4); key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  lights.add(key, key.target);
  // floor flood behind the car (env/dyno_anchors.json "flood"), on the rear bumper, like the garage's work lights
  const flood = new THREE.SpotLight("#fff1dc", 6, 8, 0.62, 0.75, 1.2);
  flood.position.set(1.611, 0.27, -4.706); flood.target.position.set(0, 0.5, -2.6); lights.add(flood, flood.target);
  // warm bounce up in the roof so the trusses read (the LED battens hang below them)
  for (const z of [-3.2, 1.8]) { const r = new THREE.PointLight("#ffd9a8", 4, 7, 1.4); r.position.set(0, 3.55, z); lights.add(r); }
  const fan = new THREE.PointLight("#9fc4ff", 3, 4, 1.6); fan.position.set(0, 0.8, 3.4); lights.add(fan);
  const door = new THREE.PointLight("#ffcf8a", 2.5, 6, 1.6); door.position.set(0, 2.6, -8.5); lights.add(door);
  room.visible = lights.visible = false;
  G.scene.add(room, lights);
  attachScreens();
}

function envFor() {
  if (!roomEnv) {
    G.carRoot.visible = false;
    roomEnv = G.pmrem.fromScene(G.scene, 0.03).texture;
    G.carRoot.visible = true;
  }
  return roomEnv;
}

const wheelbase = () => { const c = window.__perf && window.__perf.cars[G.state.car]; return c ? c.wheelbase : 2.7; };
const parkZ = () => ROLL - wheelbase() / 2;          // car origin sits midway between the axles
function cam() {
  const s = G.CARS[G.state.car].cam || 1, z = parkZ();
  return { pos: new THREE.Vector3(4.3 * s, 2.7, z + 4.4 * s), target: new THREE.Vector3(-0.5, 0.6, z - 1.5) };
}

// switch the scene over; returns once the car has stopped on the rollers
async function enter() {
  if (inside) return;
  loading ||= ensureRoom(); await loading;
  inside = true;
  saved.cam = G.camera.position.clone(); saved.target = G.controls.target.clone();
  saved.fog = G.scene.fog; saved.max = G.controls.maxDistance; saved.exp = G.renderer.toneMappingExposure;
  for (const o of G.GARAGE_OBJS) o.visible = false;
  room.visible = lights.visible = true;
  G.setRoomMode("dyno");
  G.scene.fog = null;
  G.scene.environment = envFor();
  G.renderer.toneMappingExposure = 1.15;
  G.carRoot.rotation.y = Math.PI;
  const c = cam();
  G.camera.position.copy(c.pos); G.controls.target.copy(c.target);
  G.controls.maxDistance = 9.5 * (G.CARS[G.state.car].cam || 1);
  const tab = document.querySelector('.tabs [data-tab="perf"]'); if (tab) tab.click();
  const z1 = parkZ();
  if (reduce) { G.carRoot.position.set(0, 0, z1); return; }
  const z0 = DOOR - 3.2;
  G.carRoot.position.set(0, 0, z0);
  arrival = new Promise(res => { drive = { t: 0, ms: 2600, z0, z1, last: z0, res }; });
  await arrival;
}

// back to the garage (synchronous: the other rooms take over right after)
function leave() {
  if (!inside) return;
  inside = false;
  if (drive) { const r = drive.res; drive = null; r(); }
  room.visible = lights.visible = false;
  for (const o of G.GARAGE_OBJS) o.visible = true;
  G.setRoomMode("garage");
  G.scene.fog = saved.fog; G.scene.environment = G.garageEnv;
  G.controls.maxDistance = saved.max; G.renderer.toneMappingExposure = saved.exp;
  G.camera.position.copy(saved.cam); G.controls.target.copy(saved.target);
  G.carRoot.position.set(G.BAY_X, 0, 0);
}
window.__dyno = { enter, leave, inside: () => inside, ready: () => arrival };     // ready: the car has stopped on the rollers

// ---- screens --------------------------------------------------------------------------
const SW = 160, SH = 100;
const screens = [];
function attachScreens() {
  [["EMIT_dynoA", 0], ["EMIT_dynoB", 1]].forEach(([name, page0]) => {
    const o = room.getObjectByName(name);
    if (!o) return;
    const cv = document.createElement("canvas"); cv.width = SW; cv.height = SH;
    const tex = new THREE.CanvasTexture(cv); tex.magFilter = tex.minFilter = THREE.NearestFilter; tex.colorSpace = THREE.SRGBColorSpace;
    o.traverse(m => { if (m.isMesh) { m.material = new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }); m.material.color.setScalar(1.25); } });
    screens.push({ g: cv.getContext("2d"), tex, page0 });
  });
}
const C = { bg: "#071320", grid: "#12324c", line: "#3fd0ff", hot: "#ffb43a", text: "#cfe8ff", dim: "#5f86a6", ok: "#7be08a" };
const demoCurve = t => Math.sin(t * Math.PI * 0.9) * 0.85 + 0.1 * t;
function draw(s, now) {
  const g = s.g, run = window.__dynoRun, t = now / 1000;
  g.fillStyle = C.bg; g.fillRect(0, 0, SW, SH);
  g.font = "8px monospace"; g.textBaseline = "top";
  if (run && now - run.t0 < run.dur + 6000) {
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
  const page = drive ? 0 : (Math.floor(t / 3.5) + s.page0) % 3;     // while the car rolls in: the waiting page
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

// another car picked while in the room: put its front axle on the rollers
G.HOOKS.change.push(() => { if (inside && !drive) G.carRoot.position.set(0, 0, parkZ()); });

// ---- per frame --------------------------------------------------------------------------
// rolling in: coast through the door, brake gently onto the rollers (ease-out); wheels turn by distance
const easeOut = k => 1 - (1 - k) ** 3;
let lastDraw = 0;
G.HOOKS.frame.push(dt => {
  if (!inside) return;
  const now = performance.now();
  if (drive) {
    drive.t += Math.min(dt, 1 / 30) * 1000;          // capped: the first frames in the room compile shaders, don't skip the drive
    const k = Math.min(1, drive.t / drive.ms), z = drive.z0 + (drive.z1 - drive.z0) * easeOut(k);
    G.carRoot.position.set(0, 0, z);
    for (const w of G.wheelGroup.children) w.rotateX(-(z - drive.last) / WHEEL_R);
    drive.last = z;
    if (k >= 1) { const r = drive.res; drive = null; r(); }
  }
  if (screens.length && now - lastDraw > 120) {       // ~8 refreshes a second: reads as a working PC, stays cheap
    lastDraw = now;
    for (const s of screens) { draw(s, now); s.tex.needsUpdate = true; }
  }
  const run = window.__dynoRun;
  if (run && now - run.t0 < run.dur) {
    const k = (now - run.t0) / run.dur;
    for (const w of G.wheelGroup.children) w.rotateX(-(8 + 70 * k) * dt);
  }
});
