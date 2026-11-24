// Database -> simulator input. Facts come from data/garage-db.json; every simulation assumption that is
// NOT a published figure is derived here, in one place, so it can be read and changed.
(function (root) {
  "use strict";
  const RIM_KG = { 14: 14, 15: 16, 16: 18, 17: 19, 18: 22, 19: 24, 20: 27 };   // wheel + tyre, per corner
  const tyreR = t => (t[2] * 25.4 + 2 * t[0] * t[1] / 100) / 2000;

  function engine(e) {
    const kw = e.hp / 1.341;
    if (e.type === "na") return { type: "na", kw, nm: e.nm, rpmT: e.rpmT, rpmP: e.rpmP, redline: e.redline, idle: 750 };
    return { type: e.type, kw, nm: e.nm, rpmT0: e.rpmT0, rpmT1: e.rpmT1, rpmP: e.rpmP, redline: e.redline, idle: 750 };
  }

  // model used to draw a car: its own model if it has one, else its body type's representative
  function modelOf(db, key) {
    const c = db.cars[key], b = db.bodyTypes[c.body];
    return c.model || b.model || b.fallback;
  }

  function toSim(db, key) {
    const c = db.cars[key], b = db.bodyTypes[c.body], m = db.models[modelOf(db, key)];
    const [L, W, H, WB] = c.dims.map(v => v / 1000);
    const pickup = c.body === "pickup", diesel = c.engine.type === "diesel";
    const fit = c.fit || {};
    return {
      key, name: c.name, chassis: c.chassis, fun: c.fun,
      engine: engine(c.engine),
      trans: c.trans, gears: c.gears, final: c.final, drive: c.drive,
      // drivetrain efficiency: typical value for the gearbox type
      eff: (c.trans === "mt" ? 0.92 : c.trans === "cvt" ? 0.80 : diesel ? 0.82 : 0.86),   // belt CVT loses more
      frontShare: b.front, hcg: b.hcg, wheelbase: WB,
      mass: c.kerb + 75,                                   // kerb weight + driver
      tyreR: tyreR(c.tyre), rimIn: c.tyre[2], wheelKg: (RIM_KG[c.tyre[2]] || 20) + (pickup ? 8 : 0),
      // frontal area: measured on the car's own model, or on the body model scaled by width x height
      area: m.area * (W * H) / (m.dims[1] / 1000 * m.dims[2] / 1000) * (c.model ? 1 : 1),
      cda: fit.cda ?? 0.33 * m.area * (W * H) / (m.dims[1] / 1000 * m.dims[2] / 1000),
      cl: c.cl || b.cl,
      shiftTime: c.trans === "mt" ? 0.33 : 0.25, throttleTau: diesel ? 0.30 : 0.20,
      launchRpm: Math.round(c.engine.rpmP * 0.6), stallRpm: diesel ? 2000 : 2300,
      engineInertia: diesel ? 1.6 : 1,
      target0100: c.t0100, targetVmax: c.vmax, kT: fit.kT ?? 1,
    };
  }

  // values shown to people: is this field from a source (true) or an estimate (false)?
  const sourced = (db, key, field) => !(db.cars[key].est || []).some(f => f === field || f.startsWith(field + "."));
  function sourcesUsed(db) {
    const ids = new Set();
    for (const c of Object.values(db.cars)) for (const id of Object.values(c.src || {})) ids.add(id);
    return [...ids].map(id => db.sources[id].name);
  }

  const api = { toSim, modelOf, sourced, sourcesUsed, tyreR };
  if (typeof module !== "undefined") module.exports = api; else root.GarageDB = api;
})(typeof window !== "undefined" ? window : globalThis);
