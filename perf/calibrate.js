// node perf/calibrate.js  -> stock 0-100 / quarter mile per car vs the claimed 0-100
const S = require("./sim.js");
const cars = require("./cars.json").cars;
const catalog = { parts: [{ id: "tyre_stock", group: "tyre", fx: { mu: 1.0, crr: 0.011 } }] };
for (const [k, c] of Object.entries(cars)) {
  const v = S.build(c, [], catalog);
  const { slip } = S.drag(v);
  const peak = S.dyno(v).reduce((a, b) => (b.hp > a.hp ? b : a));
  console.log(`${k.padEnd(20)} 0-100 ${slip.t100.toFixed(2)}s (claim ${c.target0100})  60ft ${slip.t60.toFixed(2)}  1/4 ${slip.t402.toFixed(2)}s @ ${slip.v402.toFixed(0)} km/h  peak ${peak.hp.toFixed(0)} hp @${peak.rpm}`);
}
