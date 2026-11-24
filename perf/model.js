// Garage build model: turns (car, picked mods, tier, exterior) into a sim vehicle, the 7-axis scores,
// real figures, price range and inspection flags. Pure functions; browser (window.GarageModel) + node.
(function (root) {
  "use strict";
  const S = root.PerfSim || (typeof require !== "undefined" ? require("./sim.js") : null);
  const clamp = v => Math.max(1, Math.min(10, v));
  // 1-10 scales from the benchmark app's 17-car dataset, so scores stay comparable with it
  const sTop = v => (v - 170) / (250 - 170) * 9 + 1;
  const sAccel = v => (11.5 - v) / (11.5 - 6.2) * 9 + 1;
  const sRatio = v => (v - 87.5) / (185.1 - 87.5) * 9 + 1;
  // diminishing returns: each extra chassis mod adds less than the one before
  const W = [1, 0.7, 0.5, 0.35, 0.25];
  const dim = arr => arr.slice().sort((a, b) => b - a).reduce((s, v, i) => s + v * (W[i] ?? 0.2), 0);

  const modOf = (cat, key) => cat.mods.find(m => m.key === key);
  const tierOf = (m, tier) => m.tiers[tier] || m.tiers.eco;
  const allowed = (m, car) => !m.only ||
    ((!m.only.type || m.only.type.includes(car.engine.type)) && (!m.only.trans || m.only.trans.includes(car.trans)));

  function resolve(car, keys, tier, ext, cat) {
    ext = ext || {};
    const simParts = [], dk = [], chassis = { h: [], b: [], d: [], e: [] };
    let lo = 0, hi = 0, fun = 0;
    const scoreAdd = sc => { for (const k in sc || {}) (k === "e" ? chassis.e.push(sc[k]) : chassis[k].push(sc[k])); };
    for (const key of keys) {
      const m = modOf(cat, key);
      if (!m || !allowed(m, car)) continue;
      const t = tierOf(m, tier);
      const phys = Object.assign({}, m.phys || {}, t.phys || {});
      const physBy = Object.assign({}, m.physBy || {}, t.physBy || {});
      phys.fun = m.fun || 0;
      simParts.push({ id: key, group: m.excl === "tyre" ? "tyre" : m.excl || m.group, price: (t.price[0] + t.price[1]) / 2, fx: phys, fxBy: physBy });
      scoreAdd(t.score || m.score);
      lo += t.price[0]; hi += t.price[1];
      const level = t.dk || m.dk, note = t.dkNote ?? m.dkNote;
      if (level !== "pass") dk.push({ key, label: m.label, level, note });
    }
    // exterior parts feed aero, wheel mass, scores and price too
    for (const [slot, v] of [["bumper_F", ext.bumper_F], ["bumper_R", ext.bumper_R], ["skirt", ext.skirt], ["spoiler", ext.spoiler]]) {
      const e = cat.body[slot] && cat.body[slot][v];
      if (!e) continue;
      simParts.push({ id: `body_${slot}_${v}`, group: "body", price: (e.price[0] + e.price[1]) / 2, fx: { cda: e.cda, fun: e.fun, clf: e.clf || 0, clr: e.clr || 0 } });
      lo += e.price[0]; hi += e.price[1];
    }
    const w = ext.wheel && cat.wheels[ext.wheel];
    if (w && ext.wheel !== "stock") {
      simParts.push({ id: `wheel_${ext.wheel}`, group: "wheel", price: (w.price[0] + w.price[1]) / 2, fx: { wheelKg: w.wheelKg, fun: 1 } });
      scoreAdd(w.score); lo += w.price[0]; hi += w.price[1];
    }
    const catalog = { parts: [...simParts, ...cat.parts] };
    const vehicle = S.build(car, simParts.map(p => p.id), catalog);
    if (ext.lower !== undefined && vehicle.lowerMM > 0) vehicle.lowerMM = ext.lower;   // coilover height slider
    const raw = figures(vehicle);
    const [h0, b0, d0, e0] = car.chassis;
    // bolt-on ceilings: handling / braking gain at most +3, drift +2, comfort stays within 1 .. stock+3
    const eSum = chassis.e.reduce((a, b) => a + b, 0);
    const scores = [
      clamp(sTop(raw.vmax)), clamp(sAccel(raw.t100)), clamp(sRatio(raw.hpPerT)),
      Math.min(10, h0 + 3, h0 + dim(chassis.h)),
      Math.min(10, b0 + 3, b0 + dim(chassis.b)),
      Math.max(1, Math.min(10, d0 + 2, d0 + chassis.d.reduce((a, b) => a + b, 0))),
      Math.max(1, Math.min(10, e0 + 3, e0 + eSum)),
    ].map(v => Math.round(v * 10) / 10);
    return { vehicle, raw, scores, price: [lo, hi], dk, fun: vehicle.fun, cl: S.lift(vehicle) };
  }

  function figures(v) {
    const run = S.drag(v), dy = S.dyno(v, 100);
    const pk = dy.reduce((a, b) => (b.hp > a.hp ? b : a)), tq = dy.reduce((a, b) => (b.nm > a.nm ? b : a));
    const kerb = v.mass - 75;
    return {
      hp: pk.hp, hpRpm: pk.rpm, whp: pk.whp, nm: tq.nm, nmRpm: tq.rpm, kg: kerb,
      hpPerT: pk.hp / kerb * 1000, t100: run.slip.t100, t402: run.slip.t402, v402: run.slip.v402,
      t60: run.slip.t60, vmax: S.topSpeed(v), run,
    };
  }

  const api = { resolve, allowed, modOf, tierOf };
  if (typeof module !== "undefined") module.exports = api; else root.GarageModel = api;
})(typeof window !== "undefined" ? window : globalThis);
