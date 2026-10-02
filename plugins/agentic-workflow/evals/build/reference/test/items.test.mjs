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
  assert.deepEqual(parseItem("Read #Lisp SICP #books https://x.test #lisp").tags, ["lisp", "books"]);
});

test("tag tokens are removed from the title", () => {
  assert.equal(parseItem("Read #Lisp SICP #books https://x.test").title, "Read SICP");
});

test("a line without tags has no tags", () => {
  assert.deepEqual(parseItem("Call Ana").tags, []);
});
