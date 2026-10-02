import { test } from "node:test";
import assert from "node:assert/strict";
import { parseItem } from "../src/items.mjs";
import { filterByTag } from "../src/filter.mjs";

test("filters by tag case-insensitively", () => {
  const items = ["A #cs", "B #books", "C #CS"].map(parseItem);
  assert.deepEqual(filterByTag(items, "Cs").map(item => item.title), ["A", "C"]);
});
