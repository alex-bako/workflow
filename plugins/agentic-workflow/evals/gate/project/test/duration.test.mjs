import { test } from "node:test";
import assert from "node:assert/strict";
import { formatDuration, parseDuration } from "../src/duration.mjs";

test("parses whole seconds", () => {
  assert.equal(parseDuration("90s"), 90);
  assert.equal(parseDuration("1h30m"), 5400);
  assert.equal(parseDuration("2d"), 172800);
});

test("rejects malformed durations", () => {
  for (const bad of ["", "5", "1h1h"]) assert.throws(() => parseDuration(bad), RangeError);
});

test("formats seconds", () => {
  assert.equal(formatDuration(5400), "1h30m");
});
