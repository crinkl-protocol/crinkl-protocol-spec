#!/usr/bin/env node
// Standalone evaluator for the Data-Density Reserve depletion curve.
//
// Reads the calibration constants from protocol/applications/economics/parameters.json
// and asserts the computed depletion entitlement at every case in
// conformance/vectors/v1/vectors/economics.dataDensityReserve.depletionCurve.v1.json.
//
// D(G) = min(cap_tokens, c * ln(1 + G / K_usd))
//
// Execution semantics: the paper (protocol/applications/economics/data-density-reserve.md
// §04) states execution uses integer fixed-point arithmetic over six-decimal token base
// units, and that the exact value at $500B (69,999,999.995828 CRINKL) sits "slightly below"
// the cap. A plain round() of the double-precision result lands one base unit high
// (69,999,999.995829); flooring to base units reproduces the paper's exact figure, so this
// script floors rather than rounds, matching the stated fixed-point behavior.
//
// No third-party dependencies; Node's built-in Math.log is the only transcendental
// function used.

import { readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

function readJson(relativePath) {
  const fullPath = path.join(repoRoot, relativePath);
  return JSON.parse(readFileSync(fullPath, "utf8"));
}

const parameters = readJson("protocol/applications/economics/parameters.json");
const vector = readJson(
  "conformance/vectors/v1/vectors/economics.dataDensityReserve.depletionCurve.v1.json"
);

if (vector.kind !== "economics.dataDensityReserve.depletionCurve.v1") {
  console.error(`[density-reserve-curve] unexpected vector kind: ${vector.kind}`);
  process.exit(1);
}

const decimals = parameters.decimals;
if (decimals !== 6) {
  console.error(`[density-reserve-curve] unexpected decimals: ${decimals}`);
  process.exit(1);
}
const baseUnitsPerToken = 10 ** decimals;

const capTokens = parameters.depletion_curve.cap_tokens;
const c = Number.parseFloat(parameters.depletion_curve.c);
const K = Number.parseFloat(parameters.depletion_curve.K_usd);

if (!Number.isFinite(c) || !Number.isFinite(K) || !Number.isFinite(capTokens)) {
  console.error("[density-reserve-curve] non-finite calibration constant in parameters.json");
  process.exit(1);
}

// D(G) in base units, floored (never rounded up past the enforced cap).
function depletionBaseUnits(gUsd) {
  const rawTokens = c * Math.log(1 + gUsd / K);
  const cappedTokens = Math.min(capTokens, rawTokens);
  return Math.floor(cappedTokens * baseUnitsPerToken);
}

function formatCrinkl(baseUnits) {
  const whole = Math.trunc(baseUnits / baseUnitsPerToken);
  const frac = String(baseUnits % baseUnitsPerToken).padStart(decimals, "0");
  return `${whole}.${frac}`;
}

let failures = 0;
for (const testCase of vector.cases) {
  const gUsd = Number.parseInt(testCase.cumulative_qualified_gmv_usd, 10);
  const expected = BigInt(testCase.expected_depletion_entitlement_base_units);
  const actual = BigInt(depletionBaseUnits(gUsd));
  const status = actual === expected ? "OK" : "FAIL";
  if (actual !== expected) failures += 1;
  console.log(
    `[density-reserve-curve] ${status} ${testCase.id}: G=$${testCase.cumulative_qualified_gmv_usd} ` +
      `expected=${formatCrinkl(Number(expected))} actual=${formatCrinkl(Number(actual))} ` +
      `(base units expected=${expected} actual=${actual})`
  );
}

// Cross-check the design invariant that the exact $500B figure is strictly below the cap,
// matching the paper's "slightly below the cap" hedge in §04.
const capBaseUnits = BigInt(capTokens) * BigInt(baseUnitsPerToken);
const g500b = vector.cases.find(
  (c_) => c_.cumulative_qualified_gmv_usd === "500000000000"
);
if (g500b) {
  const g500bBaseUnits = BigInt(g500b.expected_depletion_entitlement_base_units);
  if (g500bBaseUnits >= capBaseUnits) {
    console.error(
      "[density-reserve-curve] FAIL invariant: $500B entitlement is not below the cap"
    );
    failures += 1;
  } else {
    console.log(
      `[density-reserve-curve] OK invariant: $500B entitlement (${g500bBaseUnits}) is below the cap (${capBaseUnits})`
    );
  }
}

if (failures > 0) {
  console.error(`[density-reserve-curve] FAIL: ${failures} case(s) mismatched`);
  process.exit(1);
}

console.log(`[density-reserve-curve] OK: ${vector.cases.length} case(s) matched`);
