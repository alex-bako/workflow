import { test } from "node:test";
import assert from "node:assert/strict";
import { parseAmount, formatAmount } from "../src/money.mjs";

test("parses dollars", () => {
  assert.equal(parseAmount("12.50"), 12.5);
  assert.equal(parseAmount("$3"), 3);
});

test("rejects bad input", () => {
  assert.throws(() => parseAmount("abc"), RangeError);
  assert.throws(() => parseAmount("-1"), RangeError);
});

test("formats dollars", () => {
  assert.equal(formatAmount(12.5), "$12.50");
});
