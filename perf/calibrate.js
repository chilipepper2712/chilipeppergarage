// node perf/calibrate.js [--write]
// Per car: fits the (unpublished) drag area so the stock top speed matches vmax, then stores a time
// factor kT = published 0-100 / simulated 0-100. Drivetrain efficiency stays at a typical value for the
// gearbox type (perf/db.js) instead of being bent to absorb test-condition differences.
// --write stores them under cars.<key>.fit in data/garage-db.json.
const fs = require("fs"), path = require("path");
const S = require("./sim.js"), D = require("./db.js");
const DBP = path.join(__dirname, "../data/garage-db.json");
const db = JSON.parse(fs.readFileSync(DBP, "utf8"));
const catalog = { parts: [{ id: "tyre_stock", group: "tyre", fx: { mu: 1.0, crr: 0.011 } }] };
const run = car => { const v = S.build(car, [], catalog); return { t100: S.drag(v).slip.t100, vmax: S.topSpeed(v), v }; };
function bisect(f, lo, hi, n = 30) { for (let i = 0; i < n; i++) { const mid = (lo + hi) / 2; f(mid) > 0 ? (hi = mid) : (lo = mid); } return (lo + hi) / 2; }

for (const key of Object.keys(db.cars)) {
  const c = db.cars[key]; delete c.fit;
  const car = D.toSim(db, key);
  car.cda = bisect(cda => run({ ...car, cda }).vmax < c.vmax ? 1 : -1, 0.3, 2.5);
  const r = run(car);
  // time factor: published 0-100 / simulated 0-100, applied to every simulated time for this car
  const kT = c.t0100 / r.t100;
  c.fit = { cda: +car.cda.toFixed(3), cd: +(car.cda / car.area).toFixed(3), kT: +kT.toFixed(3) };
  const flag = Math.abs(kT - 1) > 0.12 ? "  <- large correction" : "";
  console.log(`${key.padEnd(17)} sim 0-100 ${r.t100.toFixed(2)} vs ${c.t0100}  kT ${c.fit.kT}  vmax ${r.vmax} (${c.vmax})  CdA ${c.fit.cda}  Cd ${c.fit.cd}  1/4 ${(S.drag(r.v).slip.t402 * kT).toFixed(2)}${flag}`);
}
if (process.argv.includes("--write")) fs.writeFileSync(DBP, JSON.stringify(db, null, 1));
