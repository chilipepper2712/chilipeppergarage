// Budget planner ("Ớt lên đồ"): picks mods and exterior parts for one car so the build fits a budget,
// weighted by what the owner wants (comfort / fun / speed / looks). Greedy on gain per million dong,
// priced at the TOP of each part's price range so the suggestion never runs over the budget.
// Parts that should come off for inspection ("risk") are never suggested.
(function (root) {
  "use strict";
  const M = root.GarageModel || (typeof require !== "undefined" ? require("./model.js") : null);

  // how much each goal values a build, measured against stock
  const LOOK = { bumper_F: { lip: 1, sport: 1.5 }, bumper_R: { diffuser: 1 }, skirt: { skirt: 0.8 },
    spoiler: { roof_ext: 0.6, gt_wing: 1.5 }, wheel: { six: 1.5, eight: 1.5, five: 1.7, ysp: 1.3, mesh: 1.5, rally: 1.4, window: 1.3, tri: 1.6 } };
  const LOOK_MOD = { coilover: 1.2, springs: 1.0, axleback: 0.5, catback: 0.7 };

  function value(r, s, build, goals) {
    let v = 0;
    const d = i => r.scores[i] - s.scores[i];
    if (goals.em) v += 1.4 * d(6);
    else v += 0.15 * Math.min(0, d(6));                          // nobody likes a harsher car for nothing
    if (goals.vui) v += (r.fun - s.fun) / 8 + 0.6 * d(3) + 0.3 * d(4);
    if (goals.nhanh) v += 2.2 * d(1) + 0.8 * d(0) + 0.6 * d(2);
    if (goals.ngau) {
      for (const [slot, opt] of Object.entries(build.ext)) v += (LOOK[slot] && LOOK[slot][opt]) || 0;
      for (const k of build.keys) v += LOOK_MOD[k] || 0;
    }
    for (const x of r.dk) if (x.level === "warn") v -= 0.25;    // "depends on the station"
    return v;
  }

  function candidates(car, cat, tier) {
    const out = [];
    for (const m of cat.mods) {
      if (!M.allowed(m, car)) continue;
      const t = M.tierOf(m, tier), level = t.dk || m.dk;
      if (level === "risk" || m.key === "rollcage") continue;
      out.push({ kind: "mod", key: m.key, excl: m.excl || null, hi: t.price[1] });
    }
    for (const [slot, opts] of Object.entries(cat.body))
      for (const [opt, e] of Object.entries(opts)) out.push({ kind: "ext", slot, opt, hi: e.price[1] });
    for (const [opt, w] of Object.entries(cat.wheels))
      if (opt !== "stock") out.push({ kind: "ext", slot: "wheel", opt, hi: M.tierOf(w, tier).price[1] });
    return out;
  }

  const STOCK_EXT = { bumper_F: "stock", bumper_R: "stock", skirt: "stock", spoiler: "none", wheel: "stock" };

  // budget in millions of dong; goals = { em, vui, nhanh, ngau }
  function plan(car, cat, budget, goals, tier = "eco") {
    const exclOf = k => (cat.mods.find(m => m.key === k) || {}).excl;
    const stock = M.resolve(car, [], tier, STOCK_EXT, cat);
    const build = { keys: [], ext: {} };
    const evalB = b => { const r = M.resolve(car, b.keys, tier, { ...STOCK_EXT, ...b.ext }, cat); return { r, v: value(r, stock, b, goals) }; };
    let cur = evalB(build), spent = 0;
    const pool = candidates(car, cat, tier);
    for (;;) {
      let best = null;
      for (const c of pool) {
        if (spent + c.hi > budget) continue;
        if (c.kind === "mod" && (build.keys.includes(c.key) || (c.excl && build.keys.some(k => exclOf(k) === c.excl)))) continue;
        if (c.kind === "ext" && build.ext[c.slot]) continue;
        const nb = c.kind === "mod" ? { keys: [...build.keys, c.key], ext: build.ext } : { keys: build.keys, ext: { ...build.ext, [c.slot]: c.opt } };
        const e = evalB(nb), gain = e.v - cur.v;
        if (gain < 0.05) continue;
        const ratio = gain / Math.max(1, c.hi);
        if (!best || ratio > best.ratio) best = { c, nb, e, ratio };
      }
      if (!best) break;
      build.keys = best.nb.keys; build.ext = best.nb.ext; cur = best.e; spent += best.c.hi;
    }
    return { keys: build.keys, ext: { ...STOCK_EXT, ...build.ext }, price: cur.r.price, result: cur.r, stock };
  }

  const api = { plan };
  if (typeof module !== "undefined") module.exports = api; else root.GaragePlanner = api;
})(typeof window !== "undefined" ? window : globalThis);
