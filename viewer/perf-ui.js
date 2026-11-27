// Performance + comparison tabs. Runs after the 3D module and talks to it through window.__garage.
// Model: window.GarageModel (perf/model.js) on top of window.PerfSim (perf/sim.js); data in #perfdata.
const G = window.__garage, S = window.PerfSim, M = window.GarageModel;
const DATA = JSON.parse(document.getElementById("perfdata").textContent);
const DB = DATA.db, CAT = DATA.parts;
const CARS = Object.fromEntries(Object.keys(DB.cars).map(k => [k, window.GarageDB.toSim(DB, k)]));
const EST = (k, f) => !window.GarageDB.sourced(DB, k, f);
const $ = id => document.getElementById(id);
const COL = { stock: "#3987e5", tuned: "#d95926" };          // validated categorical slots 1-2 (dark)
const OTHER = ["#199e70", "#c98500", "#d55181"];              // slots 3-5, fixed per pick, never repainted
const NAMES = Object.fromEntries(Object.entries(DB.cars).map(([k, c]) => [k, c.short]));
const FLAG = '<svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 1.5v13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M4.2 2.2h8.6l-2 3.1 2 3.2H4.2z" fill="currentColor"/></svg>';

let sel = new Set(), tier = "eco", preset = "zin";
const openInfo = new Set();
const others = new Map();                       // carKey -> colour slot
const car = () => CARS[G.state.car];
const mod = k => M.modOf(CAT, k);
const ext = () => ({ bumper_F: G.state.bumper_F, bumper_R: G.state.bumper_R, skirt: G.state.skirt, spoiler: G.state.spoiler, wheel: G.state.wheel, lower: G.state.lower });
const stockCache = {};
const stockOf = key => (stockCache[key] ||= M.resolve(CARS[key], [], "eco", {}, CAT));
const current = () => M.resolve(car(), [...sel], tier, ext(), CAT);
function vehicles() { return { stock: stockOf(G.state.car).vehicle, tuned: current().vehicle }; }
const peak = (v, k) => S.dyno(v).reduce((a, b) => (b[k] > a[k] ? b : a));
const f1 = n => n.toLocaleString("vi-VN", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const f2 = n => n.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fr = ([a, b]) => (a === b ? `${a} tr` : `${a}–${b} tr`);

// ---- picking ---------------------------------------------------------------------------
function toggle(key, on) {
  const m = mod(key);
  if (on) {
    if (m.excl) for (const k of [...sel]) if (k !== key && mod(k).excl === m.excl) sel.delete(k);
    sel.add(key);
    for (const r of m.requires || []) { if (!sel.has(r)) { const rm = mod(r); if (rm.excl) for (const k of [...sel]) if (mod(k).excl === rm.excl) sel.delete(k); sel.add(r); } }
  } else sel.delete(key);
  for (const k of [...sel]) if ((mod(k).requires || []).some(r => !sel.has(r))) sel.delete(k);   // drop orphans
  preset = null; refresh();
}
function applyPreset(k) {
  const p = CAT.presets[k];
  preset = k; sel = new Set(p.keys.filter(key => M.allowed(mod(key), car())));
  Object.assign(G.state, p.ext);
  G.apply().then(() => { preset = k; refresh(); });
  refresh();
}
function syncSuspension() {
  const slider = $("lower"), co = sel.has("coilover"), sp = sel.has("springs");
  const mm = co ? (G.state.lower || 50) : sp ? 35 : 0;
  slider.disabled = !co;
  $("lowerHint").innerHTML = IC("spring") + " " + (co ? "Coilover: 0–60 mm" : sp ? "Lò xo hạ: 35 mm" : "Cần coilover / lò xo hạ");
  if (G.state.lower !== mm) G.setLower(mm);
}

// ---- performance tab ---------------------------------------------------------------------
$("flagLegend").innerHTML = Object.entries(CAT.dk).map(([l, t]) => `<span><span class="dk-${l}">${FLAG}</span>${t}</span>`).join("");
const presetEl = $("presetChips");
for (const [k, p] of Object.entries(CAT.presets)) {
  const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = p.label; b.dataset.perfpreset = k;
  b.addEventListener("click", () => applyPreset(k)); presetEl.append(b);
}
document.querySelectorAll("#tiers button").forEach(b => b.addEventListener("click", () => { tier = b.dataset.tier; refresh(); }));

function renderMods() {
  const c = car();
  for (const g of ["spec", "comfort", "feel"]) {
    const el = $(`mods-${g}`); el.innerHTML = "";
    for (const m of CAT.mods.filter(x => x.group === g)) {
      const ok = M.allowed(m, c), t = M.tierOf(m, tier);
      if (!ok) sel.delete(m.key);
      const level = t.dk || m.dk, note = t.dkNote ?? m.dkNote;
      const why = m.only && m.only.trans ? "Xe số tự động, không áp dụng" : "Chỉ cho máy hút khí tự nhiên";
      const req = (m.requires || []).map(r => mod(r).label);
      const item = document.createElement("div"); item.className = "mod";
      item.innerHTML = `<div class="mod-line"><label class="mod-row${ok ? "" : " off"}">
          <input type="checkbox" ${sel.has(m.key) ? "checked" : ""} ${ok ? "" : "disabled"}>
          <span class="mod-main"><span>${m.label}</span><span class="mod-sub">${ok ? `${t.brand} · ${fr(t.price)}${req.length ? ` · kèm ${req.join(", ")}` : ""}` : why}</span></span>
          <span class="flag dk-${level}" title="${CAT.dk[level]}${note ? `: ${note}` : ""}">${FLAG}${level === "risk" ? "<span>Nên gỡ</span>" : ""}</span></label>
        <button type="button" class="qbtn" aria-expanded="${openInfo.has(m.key)}" aria-label="${m.label} là gì">${IC("q")}</button></div>
        <div class="mod-info"${openInfo.has(m.key) ? "" : " hidden"}>${m.info}${note ? `<br><span class="dk-${level}">${CAT.dk[level]}: ${note}.</span>` : ""}</div>`;
      item.querySelector("input").addEventListener("change", e => toggle(m.key, e.target.checked));
      item.querySelector(".qbtn").addEventListener("click", e => {
        openInfo.has(m.key) ? openInfo.delete(m.key) : openInfo.add(m.key);
        e.currentTarget.setAttribute("aria-expanded", openInfo.has(m.key));
        item.querySelector(".mod-info").hidden = !openInfo.has(m.key);
      });
      el.append(item);
    }
  }
}

function stats() {
  const a = stockOf(G.state.car), b = current();
  const ra = a.raw, rb = b.raw;
  const tile = (ic, k, v, d, better) => `<div class="stat"><span class="k">${IC(ic)}${k}</span><span class="v">${v}</span><span class="d ${better === undefined ? "" : better ? "up" : "down"}">${d}</span></div>`;
  const dt = (x, y, u) => (Math.abs(y - x) < 0.005 ? "= zin" : `${y < x ? "−" : "+"}${f2(Math.abs(y - x))} ${u}`);
  const same = (x, y) => Math.abs(x - y) < 0.005;
  const k = G.state.car, modded = JSON.stringify(rb.t100) !== JSON.stringify(ra.t100) || sel.size > 0;
  const T = (est) => (est ? "~" : "");
  $("stats").innerHTML =
    tile("bolt", "Công suất bánh", `~${Math.round(b.vehicle && peak(b.vehicle, "whp").whp)} whp`, rb.hp - ra.hp > 0.5 ? `+${Math.round(rb.hp - ra.hp)} hp` : "= zin", rb.hp - ra.hp > 0.5 ? true : undefined) +
    tile("timer", "0–100 km/h", `${T(modded || EST(k, "t0100"))}${f2(DB.cars[k].t0100 * rb.t100 / ra.t100)} s`, dt(ra.t100, rb.t100, "s"), same(ra.t100, rb.t100) ? undefined : rb.t100 < ra.t100) +
    tile("flag", "1/4 dặm", `~${f2(rb.t402)} s`, `về đích ${Math.round(rb.v402)} km/h`) +
    tile("weight", "Khối lượng", `${T(EST(k, "kerb") || Math.round(rb.kg - ra.kg) !== 0)}${Math.round(rb.kg)} kg`, Math.round(rb.kg - ra.kg) ? `${rb.kg > ra.kg ? "+" : "−"}${Math.abs(Math.round(rb.kg - ra.kg))} kg` : "= zin",
      Math.round(rb.kg - ra.kg) ? rb.kg < ra.kg : undefined);
  $("funFill").style.width = `${b.fun}%`; $("funVal").textContent = `${b.fun}/100`;
  $("priceTotal").textContent = fr(b.price);
  const items = [...sel].map(k => [mod(k).label, M.tierOf(mod(k), tier).price]);
  const e = ext(), exteriorBits = [];
  for (const [slot, v] of [["bumper_F", e.bumper_F], ["bumper_R", e.bumper_R], ["skirt", e.skirt], ["spoiler", e.spoiler]])
    if (CAT.body[slot] && CAT.body[slot][v]) exteriorBits.push(CAT.body[slot][v].price);
  if (e.wheel !== "stock") exteriorBits.push(CAT.wheels[e.wheel].price);
  const exSum = exteriorBits.reduce((a, p) => [a[0] + p[0], a[1] + p[1]], [0, 0]);
  $("priceBreak").innerHTML = items.length || exSum[1] ? items.map(([l, p]) => `${l}: ${fr(p)}`).join("<br>") + (exSum[1] ? `${items.length ? "<br>" : ""}Ngoại thất: ${fr(exSum)}` : "") : "Chưa chọn món nào.";
  $("dkList").innerHTML = b.dk.length ? b.dk.map(d => `<span class="dk-${d.level}">${FLAG}</span> ${d.label}: ${CAT.dk[d.level].toLowerCase()}${d.note ? `, ${d.note}` : ""}`).join("<br>")
    : (items.length ? '<span class="dk-pass">' + FLAG + "</span> Cả bản độ qua đăng kiểm." : "");
}

function refresh() {
  document.querySelectorAll("#tiers button").forEach(b => b.setAttribute("aria-pressed", b.dataset.tier === tier));
  document.querySelectorAll("#presetChips [data-perfpreset]").forEach(b => b.setAttribute("aria-pressed", b.dataset.perfpreset === preset));
  renderMods(); syncSuspension(); stats(); renderCompare();
}

// ---- comparison tab ------------------------------------------------------------------------
let cmpMode = "bar";
const AX = CAT.axes;
const RAWAX = [r => `${Math.round(r.vmax)} km/h`, r => `0–100 ${f2(r.t100)} s`, r => `${Math.round(r.hpPerT)} hp/tấn`];
function cmpSeries() {
  const a = stockOf(G.state.car), b = current();
  const list = [{ key: G.state.car, name: `${NAMES[G.state.car]} zin`, col: COL.stock, r: a }, { key: G.state.car, tuned: true, name: `${NAMES[G.state.car]} bản độ`, col: COL.tuned, r: b }];
  for (const [k, slot] of others) list.push({ key: k, name: `${NAMES[k]} zin`, col: OTHER[slot], r: stockOf(k), other: true });
  return list;
}
function renderCarChips() {
  const el = $("cmpCars"); el.innerHTML = "";
  for (const k of Object.keys(CARS)) {
    if (k === G.state.car) continue;
    const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = NAMES[k];
    const on = others.has(k);
    b.setAttribute("aria-pressed", on);
    if (on) b.style.borderColor = OTHER[others.get(k)];
    b.disabled = !on && others.size >= 3;
    b.addEventListener("click", () => {
      if (others.has(k)) others.delete(k);
      else { const used = new Set(others.values()); others.set(k, [0, 1, 2].find(i => !used.has(i))); }
      renderCompare();
    });
    el.append(b);
  }
}
document.querySelectorAll("#cmpMode button").forEach(b => b.addEventListener("click", () => {
  cmpMode = b.dataset.m;
  document.querySelectorAll("#cmpMode button").forEach(x => x.setAttribute("aria-pressed", x === b));
  renderCompare();
}));

function renderCompare() {
  if ($("tab-cmp").hidden) return;
  renderCarChips();
  const L = cmpSeries();
  $("cmpLegend").innerHTML = L.map(s => `<span><i style="border-color:${s.col};border-top-width:8px"></i>${s.name}</span>`).join("");
  const box = $("cmpChart"); box.innerHTML = "";
  if (cmpMode === "bar") {
    const wrap = document.createElement("div"); wrap.className = "cbars";
    AX.forEach((ax, i) => {
      const a = L[0].r.scores[i], b = L[1].r.scores[i], d = Math.round((b - a) * 10) / 10;
      const rawTxt = i < 3 ? `${RAWAX[i](L[0].r.raw)} → ${RAWAX[i](L[1].r.raw).replace("0–100 ", "")}` : (d ? `${d > 0 ? "+" : ""}${f1(d)} điểm` : "như zin");
      const blk = document.createElement("div"); blk.className = "cax";
      blk.innerHTML = `<div class="cax-h"><span>${ax}</span><span>${rawTxt}</span></div>` + L.map(s => {
        const v = s.r.scores[i];
        const tip = `${s.name} · ${ax}: ${f1(v)}/10${i < 3 ? ` (${RAWAX[i](s.r.raw)})` : ""}`;
        return `<div class="crow" title="${tip}"><div class="ctrack"><div class="cfill" style="width:${v * 10}%;background:${s.col}"></div></div><span class="cval">${f1(v)}</span></div>`;
      }).join("");
      wrap.append(blk);
    });
    box.append(wrap);
  } else {
    // radar: own-car before/after, then one small radar per compared car (only two shapes per chart)
    const grid = document.createElement("div"); grid.className = "radars"; box.append(grid);
    const fig = (cls, cap, pairs) => {
      const f = document.createElement("figure"); if (cls) f.className = cls;
      const cv = document.createElement("canvas"); f.append(cv);
      const c = document.createElement("figcaption"); c.textContent = cap; f.append(c);
      grid.append(f); requestAnimationFrame(() => radar(cv, pairs, cls === "big"));
    };
    fig("big", "Trước / sau khi độ", [L[0], L[1]]);
    for (const s of L.slice(2)) fig("", `Bản độ vs ${s.name}`, [L[1], s]);
  }
  // tables
  const head = `<tr><th></th>${L.map(s => `<th style="border-bottom:2px solid ${s.col}">${s.name.replace(" bản độ", " độ")}</th>`).join("")}</tr>`;
  // stock columns show the published figure (or ~estimate); the build column scales it by the simulated change
  const db = k => DB.cars[k];
  const fig = s => {
    const k = s.key, c = db(k), st = stockOf(k).raw, r = s.r.raw, tuned = s.tuned;
    const hp = c.engine.hp * (tuned ? r.hp / st.hp : 1), nm = c.engine.nm * (tuned ? r.nm / st.nm : 1);
    const kg = c.kerb + (tuned ? r.kg - st.kg : 0);
    return { hp, nm, kg, hpt: hp / kg * 1000, t100: tuned ? c.t0100 * r.t100 / st.t100 : c.t0100, t402: r.t402, vmax: tuned ? c.vmax * r.vmax / st.vmax : c.vmax,
      e: { hp: tuned && Math.abs(r.hp - st.hp) > 0.5 || EST(k, "engine"), nm: tuned && Math.abs(r.nm - st.nm) > 0.5 || EST(k, "engine.nm"),
           kg: tuned && Math.abs(r.kg - st.kg) > 0.5 || EST(k, "kerb"), t100: tuned && Math.abs(r.t100 - st.t100) > 0.004 || EST(k, "t0100"),
           t402: true, vmax: tuned && Math.abs(r.vmax - st.vmax) > 0.4 || EST(k, "vmax") } };
  };
  const F = L.map(fig);
  F.forEach(f => { f.e.hpt = f.e.hp || f.e.kg; });
  const rows = [
    ["Công suất", "hp", v => `${Math.round(v)} hp`, 1], ["Mô-men", "nm", v => `${Math.round(v)} Nm`, 1],
    ["Khối lượng", "kg", v => `${Math.round(v)} kg`, -1], ["hp/tấn", "hpt", v => Math.round(v), 1],
    ["0–100 km/h", "t100", v => `${f2(v)} s`, -1], ["1/4 dặm", "t402", v => `${f2(v)} s`, -1],
    ["Tốc độ tối đa", "vmax", v => `${Math.round(v)} km/h`, 1],
  ];
  const cls = (a, b, dir) => (Math.abs(a - b) < 1e-3 ? "" : (b - a) * dir > 0 ? "up" : "down");
  $("cmpRaw").innerHTML = head + rows.map(([n, f, fmt, dir]) => `<tr><td>${n}</td>${F.map((x, j) =>
    `<td class="${j === 1 ? cls(F[0][f], x[f], dir) : ""}">${x.e[f] ? "~" : ""}${fmt(x[f])}</td>`).join("")}</tr>`).join("");
  $("cmpScore").innerHTML = head + [...AX.map((ax, i) => [ax, s => s.r.scores[i]]), ["Lái vui", s => s.r.fun / 10]].map(([n, val]) =>
    `<tr><td>${n}</td>${L.map((s, j) => `<td class="${j === 1 ? cls(val(L[0]), val(s), 1) : ""}">${f1(val(s))}</td>`).join("")}</tr>`).join("");
}

function radar(cv, pairs, big) {
  const r0 = cv.getBoundingClientRect(), dpr = Math.min(devicePixelRatio, 2);
  cv.width = r0.width * dpr; cv.height = r0.height * dpr;
  const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = r0.width, cx = W / 2, cy = W / 2 + (big ? 4 : 2), R = W / 2 - (big ? 68 : 14);
  const n = AX.length, ang = i => -Math.PI / 2 + i * 2 * Math.PI / n;
  const P = (i, v) => [cx + Math.cos(ang(i)) * R * v / 10, cy + Math.sin(ang(i)) * R * v / 10];
  g.strokeStyle = "rgba(138,144,155,.18)"; g.lineWidth = 1;
  for (let k = 2; k <= 10; k += 2) { g.beginPath(); for (let i = 0; i <= n; i++) { const [x, y] = P(i % n, k); i ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
  for (let i = 0; i < n; i++) { g.beginPath(); g.moveTo(cx, cy); g.lineTo(...P(i, 10)); g.stroke(); }
  if (big) {
    g.fillStyle = "#8a909b"; g.font = "11px 'Be Vietnam Pro', system-ui, sans-serif"; g.textBaseline = "middle";
    AX.forEach((ax, i) => { const [x, y] = P(i, 11.6); g.textAlign = Math.abs(x - cx) < 4 ? "center" : x < cx ? "right" : "left"; g.fillText(ax, x, y); });
  }
  const pts = [];
  pairs.forEach((s, j) => {
    g.beginPath(); s.r.scores.forEach((v, i) => { const [x, y] = P(i, v); i ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath();
    g.fillStyle = s.col + "29"; g.fill(); g.strokeStyle = s.col; g.lineWidth = 2; g.setLineDash(j === 0 && !s.other && pairs[1] && !pairs[1].other ? [5, 4] : []); g.stroke(); g.setLineDash([]);
    s.r.scores.forEach((v, i) => { const [x, y] = P(i, v); pts.push({ x, y, s, i, v });
      g.fillStyle = "#16181d"; g.beginPath(); g.arc(x, y, big ? 4.5 : 3.5, 0, 7); g.fill(); g.fillStyle = s.col; g.beginPath(); g.arc(x, y, big ? 3.5 : 2.5, 0, 7); g.fill(); });
  });
  cv.title = pairs.map(s => `${s.name}: ${s.r.scores.map((v, i) => `${AX[i]} ${f1(v)}`).join(", ")}`).join("\n");
}
// ---- results overlay ------------------------------------------------------------------
const cv = $("resCanvas"), tip = $("resTip");
let anim = 0, mode = "whp", lastDyno = null;
function canvasCtx() {
  const r = cv.getBoundingClientRect(), dpr = Math.min(devicePixelRatio, 2);
  cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr);
  const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { g, W: r.width, H: r.height };
}
function niceMax(v) { const p = Math.pow(10, Math.floor(Math.log10(v))); return Math.ceil(v / p / 0.5) * 0.5 * p; }
function open(title, dynoMode) {
  cancelAnimationFrame(anim);
  $("results").hidden = false; $("resTitle").textContent = title;
  $("dynoMode").hidden = !dynoMode; tip.hidden = true;
}
$("resClose").addEventListener("click", () => { cancelAnimationFrame(anim); $("results").hidden = true; });

function runDyno() {
  open("Dyno · công suất bánh", true);
  const { stock, tuned } = vehicles();
  lastDyno = { a: S.dyno(stock, 100), b: S.dyno(tuned, 100) };
  const pa = peak(stock, "whp"), pb = peak(tuned, "whp"), qa = peak(stock, "nm"), qb = peak(tuned, "nm");
  $("resTable").innerHTML = `<tr><th></th><th>Công suất đỉnh</th><th>Mô-men đỉnh</th></tr>
    <tr><td>Zin</td><td>${Math.round(pa.whp)} whp @ ${pa.rpm}</td><td>${Math.round(qa.nm * stock.car.eff)} Nm @ ${qa.rpm}</td></tr>
    <tr><td>Bản độ</td><td>${Math.round(pb.whp)} whp @ ${pb.rpm}</td><td>${Math.round(qb.nm * tuned.car.eff)} Nm @ ${qb.rpm}</td></tr>`;
  $("resNote").textContent = "Công suất đo tại bánh (đã trừ hao hụt truyền động). Mô-men tính tại trục khuỷu nhân hiệu suất truyền động.";
  const t0 = performance.now();
  window.__dynoRun = { t0, dur: 2200, a: lastDyno.a, b: lastDyno.b };      // the dyno room's screens and wheels follow this
  const step = now => { drawDyno(Math.min(1, (now - t0) / 2200)); if (now - t0 < 2200) anim = requestAnimationFrame(step); };
  anim = requestAnimationFrame(step);
}
function series(k) {
  const pick = d => (k === "whp" ? d.whp : d.nm * car().eff);
  return [lastDyno.a.map(d => [d.rpm, pick(d)]), lastDyno.b.map(d => [d.rpm, pick(d)])];
}
function drawDyno(prog = 1) {
  const { g, W, H } = canvasCtx();
  const [A, B] = series(mode), unit = mode === "whp" ? "whp" : "Nm";
  const xMax = Math.max(A.at(-1)[0], B.at(-1)[0]), xMin = 1000, yMax = niceMax(Math.max(...B.map(p => p[1]), ...A.map(p => p[1])) * 1.08);
  const L = 44, R = 78, T = 8, Bm = 24;
  const X = x => L + (x - xMin) / (xMax - xMin) * (W - L - R), Y = y => T + (1 - y / yMax) * (H - T - Bm);
  g.clearRect(0, 0, W, H);
  g.font = "11px 'JetBrains Mono', monospace"; g.fillStyle = "#8a909b"; g.strokeStyle = "rgba(138,144,155,.18)"; g.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = yMax * i / 4; g.beginPath(); g.moveTo(L, Y(y)); g.lineTo(W - R, Y(y)); g.stroke();
    g.textAlign = "right"; g.fillText(Math.round(y), L - 6, Y(y) + 4);
  }
  g.textAlign = "center";
  for (let r = 1000; r <= xMax; r += 1000) g.fillText(`${r / 1000}k`, X(r), H - 6);
  g.textAlign = "left"; g.fillText(unit, 4, T + 10);
  const cut = xMin + (xMax - xMin) * prog;
  const line = (pts, col, dash) => {
    g.save(); g.beginPath(); g.rect(0, 0, X(cut), H); g.clip();
    g.strokeStyle = col; g.lineWidth = 2; g.lineJoin = "round"; g.setLineDash(dash);
    g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)))); g.stroke(); g.restore();
  };
  line(A, COL.stock, [6, 4]); line(B, COL.tuned, []);
  if (prog >= 1) {     // direct labels at the line ends, in text ink with a colour key
    const lab = (pts, col, txt, dy) => {
      const [x, y] = pts.at(-1); g.fillStyle = col; g.fillRect(X(x) + 6, Y(y) + dy - 4, 8, 2);
      g.fillStyle = "#e6e2d8"; g.fillText(txt, X(x) + 18, Y(y) + dy);
    };
    const ya = Y(A.at(-1)[1]), yb = Y(B.at(-1)[1]), sep = Math.abs(ya - yb) < 14 ? 8 : 0;
    lab(A, COL.stock, `Zin`, yb > ya ? -sep : sep); lab(B, COL.tuned, `Độ`, yb > ya ? sep : -sep);
  }
  $("resLegend").innerHTML = `<span><i style="border-color:${COL.stock};border-top-style:dashed"></i>Zin</span><span><i style="border-color:${COL.tuned}"></i>Bản độ</span>`;
  cv.onmousemove = e => {
    if (!lastDyno) return;
    const r = cv.getBoundingClientRect(), px = e.clientX - r.left;
    const rpm = Math.max(xMin, Math.min(xMax, xMin + (px - L) / (W - L - R) * (xMax - xMin)));
    const near = pts => pts.reduce((a, b) => (Math.abs(b[0] - rpm) < Math.abs(a[0] - rpm) ? b : a));
    const a = near(A), b = near(B);
    drawDyno(1);
    g.strokeStyle = "rgba(230,226,216,.35)"; g.setLineDash([]); g.beginPath(); g.moveTo(X(b[0]), T); g.lineTo(X(b[0]), H - Bm); g.stroke();
    for (const [p, c] of [[a, COL.stock], [b, COL.tuned]]) { g.fillStyle = "#0e0f12"; g.beginPath(); g.arc(X(p[0]), Y(p[1]), 5, 0, 7); g.fill(); g.fillStyle = c; g.beginPath(); g.arc(X(p[0]), Y(p[1]), 4, 0, 7); g.fill(); }
    tip.hidden = false;
    tip.innerHTML = `${b[0]} vòng/phút<br>Zin ${Math.round(a[1])} ${unit}<br>Độ ${Math.round(b[1])} ${unit}`;
    tip.style.left = `${Math.min(X(b[0]) + 10, W - 130)}px`; tip.style.top = `8px`;
  };
  cv.onmouseleave = () => { tip.hidden = true; drawDyno(1); };
}
document.querySelectorAll("#dynoMode button").forEach(b => b.addEventListener("click", () => {
  mode = b.dataset.m;
  document.querySelectorAll("#dynoMode button").forEach(x => x.setAttribute("aria-pressed", x === b));
  $("resTitle").textContent = mode === "whp" ? "Dyno · công suất bánh" : "Dyno · mô-men";
  if (lastDyno) drawDyno(1);
}));

function runDrag() {
  open("Drag 1/4 dặm · zin vs bản độ", false);
  cv.onmousemove = null; cv.onmouseleave = null;
  const { stock, tuned } = vehicles();
  const A = S.drag(stock), B = S.drag(tuned);
  const paint = G.state.paint;
  const rows = [["60 ft (18 m)", "t60"], ["0–100 km/h", "t100"], ["1/8 dặm (201 m)", "t201"], ["1/4 dặm (402 m)", "t402"]];
  const diff = (x, y) => (Math.abs(y - x) < 0.005 ? "—" : `${y < x ? "−" : "+"}${f2(Math.abs(y - x))}`);
  $("resTable").innerHTML = `<tr><th>Mốc</th><th>Zin</th><th>Bản độ</th><th>Chênh</th></tr>` +
    rows.map(([n, k]) => `<tr><td>${n}</td><td>${f2(A.slip[k])} s</td><td>${f2(B.slip[k])} s</td><td>${diff(A.slip[k], B.slip[k])}</td></tr>`).join("") +
    `<tr><td>Tốc độ về đích</td><td>${Math.round(A.slip.v402)} km/h</td><td>${Math.round(B.slip.v402)} km/h</td><td></td></tr>`;
  const illegal = B.slip.t402 < 11.5 && !sel.has("rollcage");
  $("resNote").textContent = illegal ? "Không hợp lệ ở giải: chạy dưới 11,5 s bắt buộc có khung bảo vệ." :
    `Mô phỏng ${car().trans === "mt" ? "đề pa giữ vòng tua rồi nhả côn" : "đạp ga từ vòng tua không tải"}; không tính thời gian phản xạ của tài xế.`;
  // christmas tree, then both cars run in real time
  const t0 = performance.now(), lead = 1.6, end = Math.max(A.slip.t402, B.slip.t402) + 0.8;
  const at = (tr, t) => { let p = tr[0]; for (const q of tr) { if (q.t > t) break; p = q; } return p; };
  const step = now => {
    const tt = (now - t0) / 1000, t = tt - lead;
    const { g, W, H } = canvasCtx();
    g.clearRect(0, 0, W, H);
    const Lx = 56, Rx = W - 18, lane = (H - 40) / 2;
    g.font = "11px 'JetBrains Mono', monospace";
    for (let i = 0; i < 2; i++) {
      const y0 = 10 + i * lane;
      g.fillStyle = "#16181d"; g.fillRect(Lx, y0, Rx - Lx, lane - 8);
      g.strokeStyle = "rgba(230,226,216,.15)"; g.setLineDash([6, 8]); g.beginPath(); g.moveTo(Lx, y0 + lane - 8); g.lineTo(Rx, y0 + lane - 8); g.stroke(); g.setLineDash([]);
      g.fillStyle = "#8a909b"; g.textAlign = "right"; g.fillText(i ? "Độ" : "Zin", Lx - 8, y0 + lane / 2);
    }
    g.fillStyle = "#e6e2d8"; g.fillRect(Rx - 2, 6, 3, H - 34);            // finish line
    g.fillStyle = "#8a909b"; g.textAlign = "center";
    for (const [m, lbl] of [[18.288, "60ft"], [201.168, "1/8"], [402.336, "1/4"]]) g.fillText(lbl, Lx + (Rx - Lx) * m / 402.336, H - 6);
    // tree: three ambers then green
    const lights = t < 0 ? Math.min(3, Math.floor((tt / lead) * 4)) : 4;
    for (let k = 0; k < 4; k++) { g.fillStyle = k < lights ? (k === 3 ? "#5fd16f" : "#f2a33a") : "#2a2e36"; g.fillRect(14, 12 + k * 14, 18, 10); }
    for (const [i, R, col] of [[0, A, COL.stock], [1, B, COL.tuned]]) {
      const p = t <= 0 ? { x: 0, kmh: 0 } : at(R.trace, t);
      const x = Lx + (Rx - Lx) * Math.min(1, p.x / 402.336), y0 = 10 + i * lane, ch = lane - 22;
      g.fillStyle = col; g.fillRect(x - 26, y0 + 6, 26, ch * 0.6);                // pixel car: body
      g.fillStyle = "#0e0f12"; g.fillRect(x - 22, y0 + 6 + ch * 0.6, 6, 5); g.fillRect(x - 9, y0 + 6 + ch * 0.6, 6, 5);
      g.fillStyle = "#e6e2d8"; g.textAlign = "left";
      const done = t >= R.slip.t402;
      g.fillText(done ? `${f2(R.slip.t402)} s · ${Math.round(R.slip.v402)} km/h` : `${Math.round(p.kmh || 0)} km/h`, Math.min(x + 6, Rx - 150), y0 + lane / 2 + 2);
    }
    if (tt < lead + end) anim = requestAnimationFrame(step);
  };
  anim = requestAnimationFrame(step);
  $("resLegend").innerHTML = `<span><i style="border-color:${COL.stock}"></i>Zin</span><span><i style="border-color:${COL.tuned}"></i>Bản độ · sơn ${paint.toLowerCase()}</span>`;
}

// ---- wiring ---------------------------------------------------------------------------------
$("runDyno").addEventListener("click", async () => {
  if (window.__views) { await window.__views.go("dyno"); if (window.__views.current() !== "dyno") return; }   // left the room mid drive-in
  runDyno();
});
$("runDrag").addEventListener("click", runDrag);
document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".tabs button").forEach(x => x.setAttribute("aria-selected", x === b));
  for (const t of ["ext", "perf", "cmp", "aero"]) $(`tab-${t}`).hidden = b.dataset.tab !== t;
  stats(); renderCompare();
}));
// exterior presets only touch body kit / wheels; ride height stays with the suspension pick
document.querySelectorAll("[data-car]").forEach(b => b.addEventListener("click", () => setTimeout(() => {
  sel.clear(); preset = "zin"; others.delete(G.state.car); $("results").hidden = true; refresh();
}, 0)));
document.querySelector("aside").addEventListener("click", e => {
  if (e.target.closest("#tab-ext [data-slot]")) {                 // hand-picked body kit / wheel
    preset = null;
    document.querySelectorAll("#presetChips [data-perfpreset]").forEach(b => b.setAttribute("aria-pressed", "false"));
  }
  if (e.target.closest("#tab-perf, #tab-cmp, #presetChips")) return;
  setTimeout(() => { syncSuspension(); stats(); renderCompare(); }, 0);
});
$("lower").addEventListener("input", () => { if (sel.has("coilover")) { stats(); renderCompare(); } });
addEventListener("resize", () => { if (cmpMode === "radar") renderCompare(); });
refresh();
// Ớt lên đồ: budget + goals -> a build; applyBuild puts it on the car like a preset would
function applyBuild(keys, extOver) {
  sel = new Set(keys.filter(key => M.allowed(mod(key), car())));
  Object.assign(G.state, extOver);
  return G.apply().then(() => { preset = null; refresh(); });
}
window.__perf = { cars: CARS, current: () => current(), stock: () => stockOf(G.state.car),
  variant: over => M.resolve(car(), [...sel], tier, { ...ext(), ...over }, CAT),
  plan: (budget, goals) => GaragePlanner.plan(car(), CAT, budget, goals, tier),
  applyBuild, label: key => mod(key).label,
  // pegboard wall: what is picked, and how to describe / drop one item
  selected: () => [...sel],
  info: key => { const m = mod(key), t = M.tierOf(m, tier), lv = t.dk || m.dk; return { label: m.label, brand: t.brand, price: fr(t.price), dk: lv, dkText: CAT.dk[lv] }; },
  bodyPrice: (slot, opt) => fr(CAT.body[slot][opt].price),
  drop: key => toggle(key, false) };
