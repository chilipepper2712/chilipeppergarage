// Garage views: Xưởng (the bay), Phụ tùng độ (standing in front of the pegboard). Dyno and Hầm gió are rooms
// of their own (dyno.js, tunnel.js); this module routes the four buttons and hands over to them.
import * as THREE from "three";

const G = window.__garage;
const $ = id => document.getElementById(id);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

const BOARD = { x: 5.46, y: 1.32, zc: 0.9, w: 5.4 };          // env/anchors.json, Blender -> three: x, z, -y

let view = "garage", camTween = null, garageCam = null;
const ease = k => (k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2);

function tweenCam(pos, target, ms = 900) {
  return new Promise(res => {
    camTween = { t0: performance.now() - (reduce ? 1e6 : 0), ms, p0: G.camera.position.clone(), q0: G.controls.target.clone(), p1: pos, q1: target, res };
  });
}
function partsCam() {
  const asp = G.camera.aspect, half = Math.atan(Math.tan(THREE.MathUtils.degToRad(G.camera.fov / 2)) * asp);
  const d = Math.max(3.6, (BOARD.w / 2 + 0.35) / Math.tan(half));
  return { pos: new THREE.Vector3(BOARD.x - d, BOARD.y + 0.15, BOARD.zc), target: new THREE.Vector3(BOARD.x, BOARD.y, BOARD.zc) };
}
async function go(name) {
  if (name === view) return name === "dyno" ? window.__dyno.ready() : undefined;
  if (window.__wall) window.__wall.unpin();
  if (G.getRoom() === "tunnel") { await window.__tunnel.setRoom("garage"); G.carRoot.position.set(G.BAY_X, 0, 0); }
  if (view === "dyno") window.__dyno.leave();
  if (view === "garage") garageCam = { pos: G.camera.position.clone(), target: G.controls.target.clone() };
  if ($("tSpin").checked) { $("tSpin").checked = false; }
  G.carRoot.rotation.y = Math.PI;
  view = name; press(name);
  camTween = null;
  if (name === "dyno") return window.__dyno.enter();
  const c = name === "parts" ? partsCam()
    : garageCam || { pos: new THREE.Vector3(-3.1, 2.4, 5.6), target: new THREE.Vector3(1.4, 0.75, -0.5) };
  await tweenCam(c.pos.clone(), c.target.clone());
}
function press(name) { document.querySelectorAll("#rooms [data-room]").forEach(b => b.setAttribute("aria-pressed", b.dataset.room === name)); }

for (const name of ["garage", "parts", "dyno"]) {
  const b = document.querySelector(`#rooms [data-room="${name}"]`);
  if (b) b.addEventListener("click", () => go(name));
}
// going into the wind tunnel: the car must be back on its spot first
document.querySelector('#rooms [data-room="tunnel"]').addEventListener("click", () => {
  if (view === "dyno") window.__dyno.leave();
  camTween = null; G.carRoot.position.set(0, 0, 0); view = "tunnel";
}, true);
window.__views = { go, current: () => view };

// ---- per frame ----------------------------------------------------------------------
G.HOOKS.frame.push(() => {
  if (!camTween) return;
  const k = Math.min(1, (performance.now() - camTween.t0) / camTween.ms), e = ease(k);
  G.camera.position.lerpVectors(camTween.p0, camTween.p1, e); G.controls.target.lerpVectors(camTween.q0, camTween.q1, e);
  if (k >= 1) { const r = camTween.res; camTween = null; r(); }
});
