// Performance tab: part picking, live stats, dyno + quarter-mile runs. Runs after the 3D module;
// talks to it through window.__garage (state, apply, setLower). Sim = window.PerfSim, data = #perfdata.
const G = window.__garage, S = window.PerfSim;
const DATA = JSON.parse(document.getElementById("perfdata").textContent);
const CARS = DATA.cars, CAT = DATA.parts;
const $ = id => document.getElementById(id);
const COL = { stock: "#5b8fd6", tuned: "#cf7a1f" };   // validated pair (dark surface); stock also dashed

// one option list per group; "" = none / stock
const ROWS = [
  ["intake", "Hút khí", [["", "Zin"], ["intake", "Lọc gió"]]],
  ["exhaust", "Pô", [["", "Zin"], ["axleback", "Axle-back"], ["catback", "Cat-back"]]],
  ["tune", "ECU / map", [["", "Zin"], ["remap1", "Stage 1"], ["remap2", "Stage 2"], ["ecu", "ECU rời"]]],
  ["forced", "Tăng áp", [["", "Không"], ["turbokit", "Turbo kit"]]],
  ["shifter", "Cần số", [["", "Zin"], ["shortshifter", "Short shifter"]]],
  ["pedal", "Chân ga", [["", "Zin"], ["pedalchip", "Chip"]]],
  ["susp", "Gầm", [["", "Zin"], ["springs", "Lò xo hạ"], ["coilover", "Coilover"]]],
  ["brace", "Thanh giằng", [["", "Không"], ["strutbar", "Lắp"]]],
  ["cage", "Khung", [["", "Không"], ["rollcage", "Roll cage"]]],
  ["tyre", "Vỏ xe", [["tyre_eco", "Tiết kiệm"], ["tyre_stock", "Zin"], ["tyre_sport", "Thể thao"], ["tyre_semi", "Bán slick"], ["tyre_drag", "Drag"]]],
];
const EMPTY = () => ({ intake: "", exhaust: "", tune: "", forced: "", shifter: "", pedal: "", susp: "", brace: "", cage: "", tyre: "tyre_stock" });
let perf = EMPTY();
const part = id => CAT.parts.find(p => p.id === id);
const car = () => CARS[G.state.car];

function allowed(id) {
  const p = part(id); if (!p || !p.only) return true;
  const c = car();
  if (p.only.type && !p.only.type.includes(c.engine.type)) return false;
  if (p.only.trans && !p.only.trans.includes(c.trans)) return false;
  return true;
}
const groupOf = id => part(id)?.group;

// picking a part pulls in what it requires; dropping a requirement drops what needed it
function pick(group, id) {
  const added = [];
  perf[group] = id;
  const want = id ? (part(id).requires || []) : [];
  for (const r of want) if (perf[groupOf(r)] !== r) { perf[groupOf(r)] = r; added.push(part(r).name); }
  for (const [g, v] of Object.entries(perf)) {
    if (!v) continue;
    const req = part(v).requires || [];
    if (req.some(r => perf[groupOf(r)] !== r)) perf[g] = "";
  }
  syncSuspension();
  render();
  const p = id && part(id);
  $("perfNote").textContent = p ? (added.length ? `Đã lắp kèm: ${added.join(", ")}. ` : "") + (p.note || "") : "";
}

// suspension drives ride height: springs = fixed 35 mm, coilover = slider 0-60, stock = 0
function syncSuspension() {
  const slider = $("lower"), s = perf.susp;
  const mm = s === "springs" ? 35 : s === "coilover" ? (G.state.lower || 50) : 0;
  slider.disabled = s !== "coilover";
  $("lowerHint").textContent = s === "coilover" ? "Coilover: chỉnh độ cao 0–60 mm." :
    s === "springs" ? "Lò xo hạ: cố định 35 mm." : "Cần lò xo hạ hoặc coilover (tab Hiệu năng).";
  G.setLower(mm);
}

// exterior picks feed the sim too: aero (cda), wheel mass, price, fun
function picked() {
  const ids = Object.values(perf).filter(Boolean);
  const extra = [], st = G.state, b = CAT.body;
  const addBody = (slot, v) => { const e = b[slot] && b[slot][v]; if (e) extra.push({ id: `body_${slot}_${v}`, group: "body", price: e.price, fx: { cda: e.cda, fun: e.fun } }); };
  addBody("bumper_F", st.bumper_F); addBody("bumper_R", st.bumper_R); addBody("skirt", st.skirt); addBody("spoiler", st.spoiler);
  const w = CAT.wheels[st.wheel];
  if (w && st.wheel !== "stock") extra.push({ id: `wheel_${st.wheel}`, group: "wheel", price: w.price, fx: { wheelKg: w.wheelKg, fun: 1 } });
  return { ids: [...ids, ...extra.map(e => e.id)], catalog: { ...CAT, parts: [...CAT.parts, ...extra] } };
}
function vehicles() {
  const c = car(), p = picked();
  return { stock: S.build(c, [], CAT), tuned: S.build(c, p.ids, p.catalog) };
}
const peak = (v, k) => S.dyno(v).reduce((a, b) => (b[k] > a[k] ? b : a));
const f1 = n => n.toLocaleString("vi-VN", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const f2 = n => n.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function render() {
  const rows = $("perfRows"); rows.innerHTML = "";
  for (const [g, label, opts] of ROWS) {
    const n = document.createElement("span"); n.className = "name"; n.textContent = label;
    const box = document.createElement("div"); box.className = opts.length > 4 ? "seg wrap" : "seg"; box.setAttribute("role", "group"); box.setAttribute("aria-label", label);
    for (const [id, txt] of opts) {
      const b = document.createElement("button"); b.type = "button"; b.textContent = txt;
      const p = id && part(id);
      b.disabled = !!id && !allowed(id);
      b.title = b.disabled ? (p.only.trans ? "Chỉ cho xe số sàn" : "Chỉ cho máy hút khí tự nhiên") :
        p ? `${p.name} · ${f1(p.price * (p.priceByRim ? car().rimIn / 15 : 1))} triệu` : "";
      b.setAttribute("aria-pressed", perf[g] === id);
      b.addEventListener("click", () => pick(g, id));
      box.append(b);
    }
    rows.append(n, box);
  }
  stats();
}

function stats() {
  const { stock, tuned } = vehicles();
  const a = S.drag(stock).slip, b = S.drag(tuned).slip;
  const pa = peak(stock, "whp").whp, pb = peak(tuned, "whp").whp;
  const tile = (k, v, d, better) => `<div class="stat"><span class="k">${k}</span><span class="v">${v}</span><span class="d ${better === undefined ? "" : better ? "up" : "down"}">${d}</span></div>`;
  const dt = (x, y) => (Math.abs(y - x) < 0.005 ? "như zin" : `${y < x ? "−" : "+"}${f2(Math.abs(y - x))} s so với zin`);
  $("stats").innerHTML =
    tile("Công suất bánh", `${Math.round(pb)} whp`, pb - pa > 0.5 ? `+${Math.round(pb - pa)} whp so với zin` : "như zin", pb - pa > 0.5 ? true : undefined) +
    tile("0–100 km/h", `${f2(b.t100)} s`, dt(a.t100, b.t100), Math.abs(b.t100 - a.t100) < 0.005 ? undefined : b.t100 < a.t100) +
    tile("1/4 dặm", `${f2(b.t402)} s`, `${Math.round(b.v402)} km/h về đích`) +
    tile("Khối lượng", `${Math.round(tuned.mass)} kg`, Math.round(tuned.mass - stock.mass) ? `${tuned.mass > stock.mass ? "+" : "−"}${Math.abs(Math.round(tuned.mass - stock.mass))} kg` : "như zin",
      Math.round(tuned.mass - stock.mass) ? tuned.mass < stock.mass : undefined);
  $("funFill").style.width = `${tuned.fun}%`;
  $("funVal").textContent = `${tuned.fun}/100`;
  $("perfCost").textContent = `${f1(tuned.price)} triệu`;
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
  const illegal = B.slip.t402 < 11.5 && perf.cage !== "rollcage";
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
$("runDyno").addEventListener("click", runDyno);
$("runDrag").addEventListener("click", runDrag);
document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".tabs button").forEach(x => x.setAttribute("aria-selected", x === b));
  $("tab-ext").hidden = b.dataset.tab !== "ext"; $("tab-perf").hidden = b.dataset.tab !== "perf";
  stats();
}));
// presets and car switches reset the performance build to match
const PRESET_PERF = {
  stock: {},
  street: { intake: "intake", exhaust: "axleback", pedal: "pedalchip", susp: "springs", tyre: "tyre_sport" },
  sport: { intake: "intake", exhaust: "catback", tune: "remap2", shifter: "shortshifter", pedal: "pedalchip",
           susp: "coilover", brace: "strutbar", tyre: "tyre_semi" },
};
document.querySelectorAll("[data-preset]").forEach(b => b.addEventListener("click", () => setTimeout(() => {
  perf = Object.assign(EMPTY(), PRESET_PERF[b.dataset.preset]);
  for (const [g, v] of Object.entries(perf)) if (v && !allowed(v)) perf[g] = g === "tyre" ? "tyre_stock" : "";
  if (b.dataset.preset === "sport") G.state.lower = 50;
  syncSuspension(); render();
}, 0)));
document.querySelectorAll("[data-car]").forEach(b => b.addEventListener("click", () => setTimeout(() => {
  perf = EMPTY(); syncSuspension(); render(); $("results").hidden = true;
}, 0)));
// exterior changes (bumpers, wheels, spoiler) change aero / mass: refresh stats on any panel click
document.querySelector("aside").addEventListener("click", () => setTimeout(stats, 0));
$("lower").addEventListener("input", () => { if (perf.susp === "coilover") stats(); });
syncSuspension(); render();
