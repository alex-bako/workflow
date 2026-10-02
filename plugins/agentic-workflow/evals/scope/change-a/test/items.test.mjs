import { test } from "node:test";
import assert from "node:assert/strict";
import { parseItem } from "../src/items.mjs";

test("parses title and url", () => {
  assert.deepEqual(parseItem("Read SICP https://example.com/sicp"), {
    title: "Read SICP", url: "https://example.com/sicp", read: false, tags: [],
  });
});

test("url is optional", () => {
  assert.equal(parseItem("  Call Ana  ").url, null);
  assert.equal(parseItem("  Call Ana  ").title, "Call Ana");
});

test("extracts tags lowercased, in first-seen order, without duplicates", () => {
  const item = parseItem("Read #CS SICP https://example.com/sicp #books #cs");
  assert.deepEqual(item.tags, ["cs", "books"]);
  assert.equal(item.title, "Read SICP");
});

test("a line without tags has no tags", () => {
  assert.deepEqual(parseItem("Call Ana").tags, []);
});
