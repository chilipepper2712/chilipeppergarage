// Longitudinal drag/dyno simulator for the garage. Runs in the browser (window.PerfSim) and in node.
// Straight-line only: engine torque curve -> gearbox -> driven wheels, traction limited by the driven
// axle's load (with weight transfer), rolling + aero drag, shift time, throttle response lag.
(function (root) {
  "use strict";
  const G = 9.81, RHO = 1.2;
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

  function interp(pts, x) {
    if (x <= pts[0][0]) return pts[0][1];
    for (let i = 1; i < pts.length; i++) {
      if (x <= pts[i][0]) { const [x0, y0] = pts[i - 1], [x1, y1] = pts[i]; return lerp(y0, y1, (x - x0) / (x1 - x0)); }
    }
    return pts[pts.length - 1][1];
  }

  // stock engine torque curve (Nm vs rpm), shaped by engine type
  function stockCurve(e) {
    const tP = e.kw * 9549 / e.rpmP;                    // torque at the power peak
    if (e.type === "na") return [[e.idle, 0.62 * e.nm], [e.rpmT * 0.55, 0.82 * e.nm], [e.rpmT, e.nm],
      [e.rpmP, tP], [e.redline, 0.9 * e.kw * 9549 / e.redline]];
    if (e.type === "turbo") return [[e.idle, 0.42 * e.nm], [e.rpmT0, e.nm], [e.rpmT1, e.nm],
      [e.rpmP, tP], [e.redline, 0.93 * e.kw * 9549 / e.redline]];
    /* diesel */ return [[e.idle, 0.38 * e.nm], [1400, 0.8 * e.nm], [e.rpmT0, e.nm], [e.rpmT1, e.nm],
      [e.rpmP, tP], [e.redline, 0.82 * e.kw * 9549 / e.redline]];
  }

  // apply part effects -> resolved vehicle used by the sim
  function build(car, parts, catalog) {
    const e = car.engine, picked = parts.map(id => catalog.parts.find(p => p.id === id)).filter(Boolean);
    const sum = k => picked.reduce((a, p) => a + (fx(p, car)[k] || 0), 0);
    const mul = k => picked.reduce((a, p) => a * (fx(p, car)[k] ?? 1), 1);
    const curve0 = stockCurve(e);
    const tq = sum("tq"), pw = sum("pw"), boost = sum("boost");
    const redline = e.redline + sum("rev");
    const curve = rpm => {
      const base = interp(curve0, Math.min(rpm, e.redline)) * (rpm > e.redline ? (1 - (rpm - e.redline) / 4000) : 1);
      const s = smooth(e.type === "na" ? e.rpmT : e.rpmT1, e.rpmP, rpm);
      let m = 1 + tq * (1 - s) + pw * s;
      if (boost) m *= 1 + boost * smooth(2300, 3800, rpm);       // bolt-on turbo: spools up, then holds
      return base * m;
    };
    const tyre = picked.find(p => p.group === "tyre") || catalog.parts.find(p => p.id === "tyre_stock");
    const wheel = picked.find(p => p.group === "wheel");
    const wheelKg = car.wheelKg + (wheel ? fx(wheel, car).wheelKg || 0 : 0);
    return {
      car, picked, curve, redline,
      mass: car.mass + sum("kg") + 4 * (wheelKg - car.wheelKg),
      wheelKg, mu: fx(tyre, car).mu, crr: fx(tyre, car).crr,
      cda: car.cda * (1 + sum("cda")), hcg: car.hcg + sum("hcg"),
      shift: car.shiftTime * mul("shift"), tau: car.throttleTau * mul("tau"),
      lowerMM: Math.max(0, ...picked.map(p => fx(p, car).lower || 0)),
      // lift coefficients [front, rear] before ride height; lift(v) applies the ride height
      clBase: [(car.cl || [0, 0])[0] + sum("clf"), (car.cl || [0, 0])[1] + sum("clr")],
      area: car.area || 2.2,
      fun: clamp(car.fun + sum("fun"), 0, 100),
      price: picked.reduce((a, p) => a + priceOf(p, car), 0),
    };
  }
  const fx = (p, car) => Object.assign({}, p.fx || {}, (p.fxBy && p.fxBy[car.engine.type]) || {});
  const priceOf = (p, car) => Math.round((p.price || 0) * (p.priceByRim ? car.rimIn / 15 : 1) * 10) / 10;

  // positive = lift, negative = downforce; each 10 mm of lowering takes 0.01 off both axles
  const lift = v => v.clBase.map(c => c - v.lowerMM / 1000);

  function dyno(v, step = 250) {
    const out = [];
    for (let rpm = 1000; rpm <= v.redline; rpm += step) {
      const nm = v.curve(rpm), kw = nm * rpm / 9549;
      out.push({ rpm, nm, hp: kw * 1.341, whp: kw * 1.341 * v.car.eff });
    }
    return out;
  }

  // quarter-mile run; returns timeslip + trace sampled every 0.05 s
  function drag(v, opts = {}) {
    const c = v.car, r = c.tyreR, L = c.wheelbase, dt = 0.002;
    const g = c.gears, fd = c.final, n = g.length;
    const m = v.mass, wf = c.frontShare, cl = lift(v);
    const cvt = c.trans === "cvt", cvtTarget = c.engine.rpmP * 0.9;   // real CVTs run a little under peak power
    // model constants, calibrated once on the Mazda 2 (the only car with every spec verified)
    const K_WHEEL = 0.6, K_DRIVELINE = 12, K_ENGINE_I = 0.085;
    const rotMass = 4 * v.wheelKg * K_WHEEL + K_DRIVELINE;    // wheels + driveline, as equivalent mass
    // manual launch: revs held, throttle already open; automatic: driver floors it from idle
    let t = 0, x = 0, vel = 0, gear = 0, shiftLeft = 0, th = c.trans === "mt" ? 1 : 0, a = 0;
    const slip = { t60: null, t100: null, t201: null, t402: null, v402: null };
    const trace = []; let nextS = 0;
    const launch = c.trans === "mt" ? c.launchRpm : c.stallRpm;
    while (t < 40 && x < 402.336) {
      th += (1 - th) * dt / v.tau;
      const wheelRpm = vel / r * 60 / (2 * Math.PI);
      // CVT: gears = [lowest, highest] ratio; the box holds the engine near peak power
      const gr = cvt ? Math.min(g[0], Math.max(g[1], cvtTarget / Math.max(1e-6, wheelRpm * fd))) : g[gear];
      const ratio = gr * fd;
      let rpm = wheelRpm * ratio, drive = 0;
      if (shiftLeft > 0) {
        shiftLeft -= dt;
        drive = c.trans === "mt" ? 0 : 0.35;                   // AT keeps some torque through the shift
        if (shiftLeft <= 0 && c.trans === "mt") th = 0.45;      // manual: driver lifts, re-applies
      } else drive = 1;
      let mult = 1, slipping = false;
      if (rpm < launch && (gear === 0 || c.trans !== "mt")) {
        slipping = c.trans === "mt";
        if (c.trans !== "mt") mult = 1 + 0.9 * (1 - rpm / launch);   // torque converter multiplication
        rpm = launch;                                                 // clutch slip / converter stall
      }
      const engT = v.curve(Math.min(rpm, v.redline + 200)) * th * drive * mult;
      let F = engT * ratio * c.eff / r;
      const shareStatic = c.drive === "fwd" ? wf : c.drive === "rwd" ? 1 - wf : 1;
      const transfer = (c.drive === "fwd" ? -1 : c.drive === "rwd" ? 1 : 0) * m * a * v.hcg / L;
      // aero load on the driven axle: lift unloads it, downforce adds grip (grows with speed²)
      const q = 0.5 * RHO * vel * vel * v.area, [clf, clr] = cl;
      const aeroN = -q * (c.drive === "fwd" ? clf : c.drive === "rwd" ? clr : clf + clr);
      const Fmax = v.mu * Math.max(0, m * G * shareStatic + transfer + aeroN);
      if (F > Fmax) F = Fmax * 0.92;                          // wheelspin loses a little
      const Fr = v.crr * m * G + 0.5 * RHO * v.cda * vel * vel;
      // engine/flywheel inertia only loads the car once the clutch is locked
      const mEff = m + rotMass + (slipping ? 0 : K_ENGINE_I * ratio * ratio / (r * r) * (c.engineInertia || 1));
      a = Math.max(0, (F - Fr) / mEff);
      vel += a * dt; x += vel * dt; t += dt;
      if (!cvt && shiftLeft <= 0 && gear < n - 1 && rpm >= v.redline - 150) { gear++; shiftLeft = v.shift; }
      if (slip.t60 === null && x >= 18.288) slip.t60 = t;
      if (slip.t100 === null && vel >= 100 / 3.6) slip.t100 = t;
      if (slip.t201 === null && x >= 201.168) slip.t201 = t;
      if (t >= nextS) { trace.push({ t, x, kmh: vel * 3.6, rpm: Math.round(rpm), gear: gear + 1 }); nextS += 0.05; }
    }
    slip.t402 = t; slip.v402 = vel * 3.6;
    trace.push({ t, x, kmh: vel * 3.6, gear: gear + 1 });
    // per-car time factor (published stock 0-100 / simulated stock 0-100, see perf/calibrate.js)
    const k = c.kT || 1;
    if (k !== 1) {
      for (const f of ["t60", "t100", "t201", "t402"]) if (slip[f] !== null) slip[f] *= k;
      for (const p of trace) p.t *= k;
    }
    return { slip, trace };
  }

  // top speed: highest speed where tractive force in some gear (rpm <= redline) still beats drag
  function topSpeed(v) {
    const c = v.car, r = c.tyreR;
    let best = 0;
    for (let kmh = 60; kmh <= 320; kmh += 0.5) {
      const vel = kmh / 3.6, drag = v.crr * v.mass * G + 0.5 * RHO * v.cda * vel * vel;
      let ok = false;
      const ratios = c.trans === "cvt" ? Array.from({ length: 40 }, (_, i) => c.gears[0] + (c.gears[1] - c.gears[0]) * i / 39) : c.gears;
      for (const gr of ratios) {
        const rpm = vel / r * 60 / (2 * Math.PI) * gr * c.final;
        if (rpm > v.redline || rpm < 1500) continue;
        if (v.curve(rpm) * gr * c.final * c.eff / r >= drag) { ok = true; break; }
      }
      if (ok) best = kmh;
    }
    return Math.min(best, c.vmax || 999);
  }
  const api = { build, dyno, drag, topSpeed, lift, stockCurve, interp };
  if (typeof module !== "undefined") module.exports = api; else root.PerfSim = api;
})(typeof window !== "undefined" ? window : globalThis);
