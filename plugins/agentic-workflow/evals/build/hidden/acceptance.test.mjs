// Hidden T1 acceptance, run by the verifier against the builder's src/items.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseItem } from "../src/items.mjs";

test("tags: lowercased, without #, first-seen order, no duplicates", () => {
  assert.deepEqual(parseItem("Plan #Zeta trip #alpha #ZETA https://t.test #Alpha").tags, ["zeta", "alpha"]);
});

test("tag tokens are removed from the title", () => {
  const item = parseItem("Plan #Zeta trip #alpha https://t.test");
  assert.equal(item.title, "Plan trip");
  assert.equal(item.url, "https://t.test");
});

test("a line without tags yields tags: []", () => {
  assert.deepEqual(parseItem("Call Ana https://a.test").tags, []);
  assert.deepEqual(parseItem("  Call Ana  ").tags, []);
});

test("existing fields are unchanged", () => {
  const item = parseItem("Read SICP https://example.com/sicp");
  assert.equal(item.title, "Read SICP");
  assert.equal(item.url, "https://example.com/sicp");
  assert.equal(item.read, false);
});
