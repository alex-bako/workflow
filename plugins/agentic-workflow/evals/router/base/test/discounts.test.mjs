import { test } from "node:test";
import assert from "node:assert/strict";
import { findRule, isValidPercent } from "../src/discounts/rules.mjs";

test("finds rules by code", () => {
  assert.equal(findRule([{ code: "TEN", percent: 10 }], " ten ").percent, 10);
  assert.equal(findRule([], "TEN"), null);
  assert.equal(isValidPercent(95), false);
});
