"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "..", "script.js"), "utf8");

function createCalculator(values) {
  const inputs = Object.fromEntries(Object.entries(values).map(([name, value]) => [name, { value: String(value) }]));
  const outputs = Object.fromEntries(["calc-gross", "calc-profit", "calc-break", "calc-message"].map((name) => [name, { textContent: "" }]));
  const listeners = {};
  const form = {
    elements: { namedItem: (name) => inputs[name] },
    addEventListener: (event, callback) => { listeners[event] = callback; }
  };
  const document = {
    querySelector: (selector) => selector === "#mini-calculator" ? form : outputs[selector.slice(1)] || null,
    querySelectorAll: () => [],
    documentElement: { classList: { add() {} } }
  };
  const window = { matchMedia: () => ({ matches: true }) };
  vm.runInNewContext(source, { document, window, console }, { filename: "script.js" });
  return { outputs, inputs, update: listeners.input };
}

const baseline = createCalculator({ units: 24, price: 12, cost: 4, expenses: 75, fee: 0 });
assert.equal(baseline.outputs["calc-gross"].textContent, "£288.00");
assert.equal(baseline.outputs["calc-profit"].textContent, "£117.00");
assert.equal(baseline.outputs["calc-break"].textContent, "£112.50");

const withFees = createCalculator({ units: 24, price: 12, cost: 4, expenses: 75, fee: 2 });
assert.equal(withFees.outputs["calc-profit"].textContent, "£111.24");
assert.equal(withFees.outputs["calc-break"].textContent, "£115.98");

const noPositiveContribution = createCalculator({ units: 1, price: 2, cost: 2, expenses: 20, fee: 0 });
assert.equal(noPositiveContribution.outputs["calc-break"].textContent, "Not available");

const noEventCosts = createCalculator({ units: 1, price: 5, cost: 2, expenses: 0, fee: 0 });
assert.equal(noEventCosts.outputs["calc-break"].textContent, "£0.00");

const largeExactValues = createCalculator({ units: 100000, price: 100000, cost: 99999, expenses: 1000000, fee: 0 });
assert.equal(largeExactValues.outputs["calc-gross"].textContent, "£10,000,000,000.00");
assert.equal(largeExactValues.outputs["calc-break"].textContent, "£100,000,000,000.00");

console.log("Calculator tests passed: baseline, fee rounding, unavailable break-even, zero event costs, and large exact amounts.");
