// Wind tunnel room: home-built tunnel scene, smoke streamlines shaped on the car's real silhouette,
// lights-off mode, and reference aero numbers. Talks to the 3D module through window.__garage and to
// the performance module through window.__perf. Visual, not a fluid solver (see the note in the panel).
import * as THREE from "three";

const G = window.__garage, P = { current: () => window.__perf.current(), stock: () => window.__perf.stock(), variant: o => window.__perf.variant(o) };
const DATA = JSON.parse(document.getElementById("perfdata").textContent);
const CAT = DATA.parts;
const $ = id => document.getElementById(id);
const RHO = 1.2;
const f1 = n => n.toLocaleString("vi-VN", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const f2 = n => n.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const f3 = n => n.toLocaleString("vi-VN", { minimumFractionDigits: 3, maximumFractionDigits: 3 });

let fanW = 0, room = null, blades = null, tunnelEnv = null, loading = null;
const lights = new THREE.Group(), dark = new THREE.Group(), flow = new THREE.Group();
let wind = 100, darkMode = false, smokeOn = true, aero = null;
const saved = {};

// ---- room -----------------------------------------------------------------------------
async function ensureRoom() {
  if (room) return;
  room = await G.load("env/tunnel");
  G.prepMaterials(room, "env");
  room.traverse(o => {
    if (o.name === "fan_blades") blades = o;
    if (o.isMesh && o.material.name === "epoxy") { o.material.roughness = 0.34; o.material.envMapIntensity = 0.6; }
    if (o.isMesh && o.material.name === "EMIT_fan") o.material.color.setScalar(4.5);
  });
  // spin the blades about the fan axis (Blender (0,-5.7,1.55), axis Y -> three (0,1.55,5.7), axis Z)
  const pivot = new THREE.Group(); pivot.position.set(0, 1.55, 5.7);
  room.add(pivot); blades.removeFromParent(); pivot.add(blades); blades.position.set(0, -1.55, -5.7);
  blades.userData.pivot = pivot;
  // room lights: three LED strips, warm light through the fan, a soft fill
  lights.add(new THREE.HemisphereLight("#d6e2f2", "#2a2620", 0.5));
  for (const x of [-1.3, 0, 1.3]) {
    const l = new THREE.RectAreaLight("#e8f1ff", 5, 0.1, 8.2); l.position.set(x, 3.42, -0.5); l.lookAt(x, 0, -0.5); lights.add(l);
  }
  const fanLight = new THREE.PointLight("#ffe2b0", 14, 9, 1.4); fanLight.position.set(0, 1.55, 5.2); lights.add(fanLight);
  const key = new THREE.SpotLight("#f4f7ff", 4, 0, Math.PI / 4, 0.8, 0);
  key.position.set(0, 3.3, 0); key.target.position.set(0, 0, 0); key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  lights.add(key, key.target);
  // lights-off mode: only cyan rim lights from behind and above, the smoke does the rest
  for (const [x, y, z] of [[-2.6, 2.4, -3.2], [2.6, 2.4, -3.2], [0, 3.2, 2.4]]) {
    const r = new THREE.RectAreaLight("#4fd2ff", 6, 3, 0.25); r.position.set(x, y, z); r.lookAt(0, 0.7, 0); dark.add(r);
  }
  dark.add(new THREE.HemisphereLight("#0a2030", "#000000", 0.08));
  G.scene.add(room, lights, dark, flow);
}

function envFor(mode) {
  if (mode === "garage") return G.garageEnv;
  if (!tunnelEnv) {
    const fv = flow.visible, dv = dark.visible;
    G.carRoot.visible = false; flow.visible = false; dark.visible = false;
    tunnelEnv = G.pmrem.fromScene(G.scene, 0.03).texture;
    G.carRoot.visible = true; flow.visible = fv; dark.visible = dv;
  }
  return tunnelEnv;
}

async function setRoom(mode) {
  if (mode === G.getRoom()) return;
  if (mode === "tunnel") {
    $("rooms").querySelector('[data-room="tunnel"] .rl').textContent = "ĐANG TẢI…";
    loading ||= ensureRoom(); await loading;
    $("rooms").querySelector('[data-room="tunnel"] .rl').textContent = "HẦM GIÓ";
  }
  const t = mode === "tunnel";
  for (const o of G.GARAGE_OBJS) o.visible = !t;
  room.visible = lights.visible = flow.visible = t; dark.visible = false;
  lights.visible = t;
  G.setRoomMode(mode);
  if (t) {
    saved.cam = G.camera.position.clone(); saved.target = G.controls.target.clone(); saved.rot = G.carRoot.rotation.y;
    saved.fog = G.scene.fog; saved.bloom = [G.bloom.strength, G.bloom.threshold];
    G.carRoot.rotation.y = Math.PI;
    G.scene.fog = null;
    G.scene.environment = envFor("tunnel");
    const s = G.CARS[G.state.car].cam || 1;
    G.controls.target.set(0, 0.85, 0.3);
    G.camera.position.set(8.4 * s, 1.05, 1.4);
    G.controls.maxDistance = 11 * s;
    applyDark();
    rebuild();
  } else {
    G.scene.environment = G.garageEnv; G.scene.fog = saved.fog;
    [G.bloom.strength, G.bloom.threshold] = saved.bloom || [G.bloom.strength, G.bloom.threshold];
    if (saved.cam) { G.camera.position.copy(saved.cam); G.controls.target.copy(saved.target); }
    G.renderer.toneMappingExposure = 0.95;
    G.scene.background = new THREE.Color("#050505");
  }
  document.querySelectorAll("#rooms [data-room]").forEach(b => b.setAttribute("aria-pressed", b.dataset.room === mode));
  const tab = document.querySelector('.tabs [data-tab="aero"]');
  tab.hidden = !t;
  (t ? tab : document.querySelector('.tabs [data-tab="ext"]')).click();
}

function applyDark() {
  if (G.getRoom() !== "tunnel") return;
  lights.visible = !darkMode; dark.visible = darkMode;
  room.traverse(o => { if (o.isMesh && o.material.isMeshBasicMaterial) o.material.color.setScalar(darkMode ? 0.05 : (o.material.name === "EMIT_fan" ? 4.5 : 3)); });
  G.scene.environment = darkMode ? null : envFor("tunnel");
  G.scene.background = new THREE.Color(darkMode ? "#000000" : "#050505");
  G.bloom.strength = darkMode ? 0.55 : 0.35; G.bloom.threshold = darkMode ? 0.7 : 0.96;
  G.renderer.toneMappingExposure = darkMode ? 1.1 : 0.95;
  lineMat.uniforms.uDark.value = darkMode ? 1 : 0;
  smokeMat.uniforms.uDark.value = darkMode ? 1 : 0;
}

// ---- streamlines ------------------------------------------------------------------------
// Work in carRoot-local space: the car's nose points to local -Z, so air flows -Z -> +Z.
const Z0 = -4.0, Z1 = 6.3, DZ = 0.04, NZ = Math.round((Z1 - Z0) / DZ) + 1;
const SLICES = [-0.42, 0, 0.42], G0 = 0.24, HTOP = 3.3;
const HEIGHTS = []; for (let h = 0.08; h <= 2.35; h += 0.105) HEIGHTS.push(h);
const ray = new THREE.Raycaster();
const carMeshes = () => { const out = []; G.carRoot.traverse(o => { if (o.isMesh && o.visible && isShown(o)) out.push(o); }); return out; };
function isShown(o) { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; }

// three r160 crashes interpolating normals on degenerate (zero-area) triangles; the sampling only needs
// hit points, so raycast with the normal attribute set aside
function cast(meshes) {
  const kept = meshes.map(m => { const n = m.geometry.attributes.normal; if (n) m.geometry.deleteAttribute("normal"); return n; });
  try { return ray.intersectObjects(meshes, false)[0]; }
  finally { meshes.forEach((m, i) => kept[i] && m.geometry.setAttribute("normal", kept[i])); }
}

function profile(x, meshes) {
  const top = new Float32Array(NZ), bot = new Float32Array(NZ).fill(99);
  const o = new THREE.Vector3(), down = new THREE.Vector3(0, -1, 0), up = new THREE.Vector3(0, 1, 0);
  G.carRoot.updateMatrixWorld(true);
  const rot = new THREE.Quaternion().setFromRotationMatrix(G.carRoot.matrixWorld);
  for (let i = 0; i < NZ; i++) {
    const z = Z0 + i * DZ;
    o.set(x, 4, z); G.carRoot.localToWorld(o); ray.set(o, down.clone().applyQuaternion(rot)); ray.far = 5;
    const h = cast(meshes);
    if (h) {
      top[i] = G.carRoot.worldToLocal(h.point.clone()).y;
      o.set(x, 0.01, z); G.carRoot.localToWorld(o); ray.set(o, up.clone().applyQuaternion(rot)); ray.far = 3;
      const u = cast(meshes);
      if (u) bot[i] = G.carRoot.worldToLocal(u.point.clone()).y;
    }
  }
  return { top, bot };
}

function frontalArea(meshes) {
  const step = 0.04, o = new THREE.Vector3(), dir = new THREE.Vector3(0, 0, 1);
  const rot = new THREE.Quaternion().setFromRotationMatrix(G.carRoot.matrixWorld);
  let hits = 0;
  for (let x = -1.2; x <= 1.2; x += step) for (let y = 0.02; y <= 2.1; y += step) {
    o.set(x, y, -8); G.carRoot.localToWorld(o); ray.set(o, dir.clone().applyQuaternion(rot)); ray.far = 16;
    if (cast(meshes)) hits++;
  }
  return hits * step * step;
}

const lineMat = new THREE.ShaderMaterial({
  uniforms: { uT: { value: 0 }, uWind: { value: 1 }, uDark: { value: 0 } },
  vertexShader: `attribute float s; attribute float w; attribute float seed; uniform float uT; uniform float uWind;
    varying float vS; varying float vW; varying float vSeed;
    void main(){ vS=s; vW=w; vSeed=seed; vec3 p=position;
      float n = sin(p.z*5.1 - uT*7.0*uWind + seed*13.0) + 0.6*sin(p.z*11.7 - uT*11.0*uWind + seed*5.0);
      p.y += n * w * 0.07; p.x += cos(p.z*4.3 - uT*6.0*uWind + seed*7.0) * w * 0.10;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(p,1.); }`,
  fragmentShader: `uniform float uT; uniform float uWind; uniform float uDark; varying float vS; varying float vW; varying float vSeed;
    void main(){
      float pulse = pow(fract(vS*7.0 - uT*0.55*uWind - vSeed), 5.0);
      float a = (0.18 + 0.82*pulse) * smoothstep(0.0,0.05,vS) * (1.0 - smoothstep(0.85,1.0,vS)) * (1.0 - 0.55*vW);
      vec3 col = mix(vec3(0.85,0.88,0.9), vec3(0.25,0.8,1.0), uDark);
      gl_FragColor = vec4(col * a * mix(0.3, 0.55, uDark), 1.0); }`,
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
});
const smokeMat = new THREE.ShaderMaterial({
  uniforms: { uDark: { value: 0 }, uScale: { value: 400 } },
  vertexShader: `attribute float a; varying float vA; uniform float uScale;
    void main(){ vA=a; vec4 mv=modelViewMatrix*vec4(position,1.); gl_PointSize=max(1.,0.16*uScale/-mv.z); gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform float uDark; varying float vA; void main(){ vec2 q=gl_PointCoord-.5; float d=1.-smoothstep(.2,.5,length(q));
      vec3 col=mix(vec3(0.8,0.82,0.85), vec3(0.2,0.65,0.95), uDark); gl_FragColor=vec4(col*vA*d*mix(0.12,0.35,uDark),1.); }`,
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
});
let smoke = null, wakeInfo = { z: 2, h: 1, W: 0.5 };

function rebuild() {
  if (G.getRoom() !== "tunnel" || !room) return;
  clearTimeout(rebuild.t);
  rebuild.t = setTimeout(() => {
    const meshes = carMeshes();
    aero = computeAero(meshes);
    buildLines(meshes);
    render();
  }, 60);
}

function buildLines(meshes) {
  flow.clear();
  flow.position.copy(G.carRoot.position); flow.rotation.copy(G.carRoot.rotation);
  const W = THREE.MathUtils.clamp((aero.tuned.cd - 0.27) / 0.22, 0.15, 1);
  let tailZ = -9, tailTop = 0, maxTop = 0;
  const profs = SLICES.map(x => profile(x, meshes));
  for (const { top } of profs) for (let i = 0; i < NZ; i++) if (top[i] > 0) { tailZ = Math.max(tailZ, Z0 + i * DZ); maxTop = Math.max(maxTop, top[i]); }
  for (const { top } of profs) for (let i = 0; i < NZ; i++) { const z = Z0 + i * DZ; if (top[i] > 0 && z > tailZ - 0.45) tailTop = Math.max(tailTop, top[i]); }
  wakeInfo = { z: tailZ, h: tailTop, W };
  const sF = 0.45, sB = 0.35 + 0.9 * W;
  const pos = [], sArr = [], wArr = [], seedArr = [];
  SLICES.forEach((x, si) => {
    const { top, bot } = profs[si];
    // envelope with look-ahead in front and a lazy recovery behind (the wake)
    const D = new Float32Array(NZ), Bt = new Float32Array(NZ);
    for (let i = 0; i < NZ; i++) {
      let d = G0, b = G0;
      for (let j = Math.max(0, i - 80); j < Math.min(NZ, i + 30); j++) {
        if (top[j] <= 0) continue;
        const dz = (i - j) * DZ, sg = dz < 0 ? sF : sB;
        d = Math.max(d, G0 + (top[j] - G0) * Math.exp(-((dz / sg) ** 2)));
        if (dz * dz < 0.09) b = Math.min(b, Math.max(0.02, bot[j]));
      }
      D[i] = d; Bt[i] = b;
    }
    HEIGHTS.forEach((h0, hi) => {
      const seed = (si * 37 + hi * 11) % 17 / 17;
      for (let i = 0; i < NZ - 1; i++) {
        for (const k of [i, i + 1]) {
          const z = Z0 + k * DZ;
          const y = h0 >= G0 ? D[k] + (h0 - G0) * (HTOP - D[k]) / (HTOP - G0) : h0 * Bt[k] / G0;
          const behind = z - tailZ;
          const near = Math.exp(-Math.max(0, h0 - tailTop * 0.9) / 0.35);
          const w = behind > 0 ? W * near * Math.exp(-behind / (1.2 + 2 * W)) * Math.min(1, behind / 0.3) : 0;
          pos.push(x, y, z); sArr.push((z - Z0) / (Z1 - Z0)); wArr.push(w); seedArr.push(seed);
        }
      }
    });
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("s", new THREE.Float32BufferAttribute(sArr, 1));
  g.setAttribute("w", new THREE.Float32BufferAttribute(wArr, 1));
  g.setAttribute("seed", new THREE.Float32BufferAttribute(seedArr, 1));
  flow.add(new THREE.LineSegments(g, lineMat));
  // wake smoke puffs
  const N = 700, sp = new Float32Array(N * 3), sa = new Float32Array(N);
  const sg = new THREE.BufferGeometry();
  sg.setAttribute("position", new THREE.BufferAttribute(sp, 3)); sg.setAttribute("a", new THREE.BufferAttribute(sa, 1));
  smoke = new THREE.Points(sg, smokeMat);
  smoke.userData = { life: Float32Array.from({ length: N }, () => Math.random()), seed: Float32Array.from({ length: N }, () => Math.random() * 100) };
  for (let i = 0; i < N; i++) spawnPuff(i, true);
  smoke.visible = smokeOn;
  flow.add(smoke);
}
function spawnPuff(i, fresh) {
  const p = smoke.geometry.attributes.position.array, u = smoke.userData;
  p[i * 3] = (Math.random() - .5) * 1.4;
  p[i * 3 + 1] = 0.12 + Math.random() * Math.max(0.3, wakeInfo.h);
  p[i * 3 + 2] = wakeInfo.z - 0.05 + Math.random() * (fresh ? 3 : 0.2);
  u.life[i] = fresh ? Math.random() : 0;
}
function stepSmoke(dt, t) {
  if (!smoke || !smoke.visible) return;
  const p = smoke.geometry.attributes.position.array, a = smoke.geometry.attributes.a.array, u = smoke.userData;
  const v = wind / 3.6 * 0.12, W = wakeInfo.W;
  for (let i = 0; i < a.length; i++) {
    u.life[i] += dt * (0.25 + wind / 300);
    if (u.life[i] > 1 || p[i * 3 + 2] > Z1) spawnPuff(i, false);
    const s = u.seed[i];
    p[i * 3 + 2] += v * dt * (0.6 + 0.4 * Math.sin(s));
    p[i * 3] += Math.sin(t * 2.1 + s) * dt * W * 0.6 * (wind / 100);
    p[i * 3 + 1] += (Math.cos(t * 1.7 + s * 2) * W * 0.5 - 0.05) * dt * (wind / 100);
    a[i] = wind > 0 ? Math.sin(Math.PI * u.life[i]) * W * Math.exp(-(p[i * 3 + 2] - wakeInfo.z) / 2.5) : 0;
  }
  smoke.geometry.attributes.position.needsUpdate = true; smoke.geometry.attributes.a.needsUpdate = true;
}

// ---- numbers ----------------------------------------------------------------------------------
function cls(build, car, lowerMM) {
  let f = car.cl[0], r = car.cl[1];
  for (const [slot, v] of [["bumper_F", build.bumper_F], ["bumper_R", build.bumper_R], ["skirt", build.skirt], ["spoiler", build.spoiler]]) {
    const e = CAT.body[slot] && CAT.body[slot][v];
    if (e) { f += e.clf || 0; r += e.clr || 0; }
  }
  f -= lowerMM / 1000; r -= lowerMM / 1000;
  return [f, r];
}
let areaCache = { key: "", A: 2 };
function computeAero(meshes) {
  const car = G.CARS[G.state.car], data = window.__perf.cars[G.state.car], st = G.state;
  const key = [st.car, st.bumper_F, st.bumper_R, st.skirt, st.spoiler, st.wheel, st.lower].join("|");
  if (areaCache.key !== key) areaCache = { key, A: frontalArea(meshes) };
  const A = areaCache.A;
  const tuned = P.current(), stock = P.stock();
  const ext = { bumper_F: st.bumper_F, bumper_R: st.bumper_R, skirt: st.skirt, spoiler: st.spoiler };
  const mk = (r, build, lower, area) => ({ cda: r.vehicle.cda, area, cd: r.vehicle.cda / area, cl: r.cl, vmax: r.raw.vmax, raw: r.raw });
  // stock frontal area: same car without wing/lip; the difference is small, reuse unless a wing is fitted
  const A0 = areaCache.stockA?.[st.car] || A;
  if (st.spoiler === "none" && st.bumper_F === "stock") { areaCache.stockA = { ...(areaCache.stockA || {}), [st.car]: A }; }
  // the same build without any aero parts: what the wing / lip / diffuser actually buy in a drag run
  const bare = P.variant({ bumper_F: "stock", bumper_R: "stock", skirt: "stock", spoiler: "none" });
  return { tuned: mk(tuned, ext, st.lower, A), stock: mk(stock, {}, 0, A0), bare: mk(bare, {}, st.lower, A), car, drive: data.drive };
}

function forces(a) {
  const v = wind / 3.6, q = 0.5 * RHO * v * v;
  return { drag: q * a.cda, pkw: q * a.cda * v / 1000, lf: q * a.area * a.cl[0], lr: q * a.area * a.cl[1] };
}
const liftTxt = n => (Math.abs(n) < 0.5 ? "0 N" : n > 0 ? `nâng ${Math.round(n)} N` : `ép ${Math.round(-n)} N`);

function render() {
  $("windVal").textContent = `${wind} km/h`;
  if (!aero) return;
  const t = aero.tuned, s = aero.stock, ft = forces(t), fs = forces(s);
  const tile = (ic, k, v, d) => `<div class="stat"><span class="k">${IC(ic)}${k}</span><span class="v">${v}</span><span class="d">${d}</span></div>`;
  $("aeroStats").innerHTML =
    tile("wind", "Cd", "~" + f3(t.cd), "suy từ Cd·A") +
    tile("square", "Mặt trước", `~${f2(t.area)} m²`, "đo trên model") +
    tile("weight", "Lực cản", `~${Math.round(ft.drag)} N`, `Cd·A ${f3(t.cda)} m²`) +
    tile("bolt", "Công suất thắng gió", `~${f1(ft.pkw * 1.341)} hp`, `ở ${wind} km/h`);
  const row = (n, a, b, fmt, better) => {
    const c = Math.abs(a - b) < 1e-6 ? "" : better(a, b) ? "up" : "down";
    return `<tr><td>${n}</td><td>${fmt(a)}</td><td class="${c}">${fmt(b)}</td></tr>`;
  };
  $("aeroTable").innerHTML = `<tr><th>(~ ước lượng)</th><th>Zin</th><th>Bản độ</th></tr>` +
    row("Cd·A (m²)", s.cda, t.cda, f3, (a, b) => b < a) +
    row("Lực cản", fs.drag, ft.drag, v => `${Math.round(v)} N`, (a, b) => b < a) +
    row("Cầu trước", fs.lf, ft.lf, liftTxt, (a, b) => b < a) +
    row("Cầu sau", fs.lr, ft.lr, liftTxt, (a, b) => b < a) +
    row("Tốc độ tối đa", s.vmax, t.vmax, v => `${Math.round(v)} km/h`, (a, b) => b > a);
  const facts = [];
  facts.push(`Lực cản tăng theo <b>bình phương</b> tốc độ: từ 100 lên 200 km/h lực cản ×4, công suất cần để thắng gió ×8. Ở ${wind} km/h, xe này cần ${f1(ft.pkw * 1.341)} hp chỉ để đẩy không khí.`);
  facts.push(wakeInfo.W > 0.6 ? `Đuôi xe cắt đứng nên dòng khí <b>tách ra sớm</b>, để lại vùng xoáy lớn phía sau. Vùng xoáy kéo xe lại, đó là lý do SUV và bán tải cản gió nhiều.`
    : `Đuôi xe vuốt dần nên dòng khí <b>bám theo thân</b> lâu hơn, vùng xoáy phía sau nhỏ.`);
  if (G.state.spoiler === "gt_wing") facts.push(`GT wing đổi hướng dòng khí lên trên để <b>ép đuôi xe xuống</b> (${liftTxt(ft.lr - forces({ ...t, cl: [t.cl[0], t.cl[1] + 0.2] }).lr)} ở tốc độ này), đổi lại tăng cản và giảm tốc độ tối đa.`);
  else if (G.state.spoiler === "roof_ext") facts.push(`Đuôi gió nối dài giúp dòng khí <b>rời mui gọn hơn</b>, giảm lực nâng ở đuôi một chút.`);
  const hasAero = G.state.spoiler !== "none" || G.state.bumper_F !== "stock" || G.state.bumper_R !== "stock" || G.state.skirt !== "stock";
  if (hasAero) {
    const b = aero.bare.raw, r = t.raw, axle = aero.drive === "fwd" ? "cầu trước" : "cầu sau";
    const dq = (r.t402 - b.t402), dv = r.vmax - b.vmax;
    const q60 = 0.5 * RHO * (60 / 3.6) ** 2 * t.area, q160 = 0.5 * RHO * (160 / 3.6) ** 2 * t.area;
    const ax = aero.drive === "fwd" ? 0 : 1, dn = c => Math.max(0, -c.cl[ax]);
    facts.push(`Trong drag 1/4 dặm, đồ khí động gần như <b>không giúp bám</b>: xe chỉ thiếu bám lúc đề pa, khi tốc độ còn thấp. ${dn(t) > 0 ? `Lực ép ở ${axle} (cầu dẫn động) chỉ khoảng ${Math.round(dn(t) * q60)} N ở 60 km/h, lên ${Math.round(dn(t) * q160)} N ở 160 km/h.` : `Với bản độ này ${axle} (cầu dẫn động) vẫn bị <b>nâng</b> nhẹ, không có lực ép nào để thêm bám.`}`);
    facts.push(`So với cùng bản độ nhưng bỏ hết cánh, cản, ốp: 1/4 dặm <b>${dq >= 0 ? "chậm hơn" : "nhanh hơn"} ${f2(Math.abs(dq))} s</b>, tốc độ tối đa ${dv <= 0 ? "giảm" : "tăng"} ${Math.abs(Math.round(dv))} km/h. Cánh gió có giá trị khi vào cua tốc độ cao, không phải khi chạy thẳng.`);
    if (aero.drive === "fwd" && G.state.spoiler === "gt_wing") facts.push(`Xe này <b>cầu trước</b>: GT wing ép đuôi xe, tức là ép bánh không kéo. Lực ép đó không chuyển thành độ bám khi tăng tốc.`);
  }
  if (G.state.lower > 0) facts.push(`Hạ gầm ${G.state.lower} mm làm ít không khí lọt xuống gầm hơn, giảm lực nâng cả hai cầu.`);
  if (G.state.bumper_F !== "stock") facts.push(`Cản ${G.state.bumper_F === "lip" ? "có lip" : "sport"} chặn bớt khí chui xuống gầm ở đầu xe, tạo <b>lực ép cầu trước</b> nhẹ.`);
  $("aeroFacts").innerHTML = facts.map(f => `<li>${f}</li>`).join("");
}

// ---- wiring ---------------------------------------------------------------------------------------
// only the tunnel button is handled here; Xưởng / Phụ tùng độ / Dyno live in views.js, which calls back into setRoom
document.querySelector('#rooms [data-room="tunnel"]').addEventListener("click", () => setRoom("tunnel"));
window.__tunnel = { setRoom };
$("wind").addEventListener("input", e => { wind = +e.target.value; lineMat.uniforms.uWind.value = wind / 100; render(); });
$("tDark").addEventListener("change", e => { darkMode = e.target.checked; applyDark(); });
$("tSmoke").addEventListener("change", e => { smokeOn = e.target.checked; if (smoke) smoke.visible = smokeOn; });
G.HOOKS.change.push(rebuild);
document.querySelector("aside").addEventListener("click", e => { if (e.target.closest("#tab-perf")) rebuild(); });
G.HOOKS.frame.push((dt, t) => {
  if (G.getRoom() !== "tunnel") return;
  // fan spins up / down with some inertia instead of jumping to the slider speed
  if (blades) { fanW += (wind / 100 * 8 - fanW) * Math.min(1, dt * 1.2); blades.userData.pivot.rotation.z -= dt * fanW; }
  lineMat.uniforms.uT.value = t; lineMat.visible = wind > 0;
  stepSmoke(dt, t);
  smokeMat.uniforms.uScale.value = G.renderer.domElement.height * 0.5 / Math.tan(THREE.MathUtils.degToRad(G.camera.fov / 2));
});
