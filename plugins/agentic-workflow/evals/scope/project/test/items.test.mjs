import { test } from "node:test";
import assert from "node:assert/strict";
import { parseItem } from "../src/items.mjs";

test("parses title and url", () => {
  assert.deepEqual(parseItem("Read SICP https://example.com/sicp"), {
    title: "Read SICP", url: "https://example.com/sicp", read: false,
  });
});

test("url is optional", () => {
  assert.equal(parseItem("  Call Ana  ").url, null);
  assert.equal(parseItem("  Call Ana  ").title, "Call Ana");
});
