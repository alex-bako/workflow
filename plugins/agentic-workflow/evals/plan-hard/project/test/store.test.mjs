import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { saveItems, loadItems } from "../src/store.mjs";

const fixture = name => readFileSync(new URL(`fixtures/${name}`, import.meta.url), "utf8");

test("saves the current version", () => {
  assert.equal(saveItems([{ title: "Read SICP", url: null, read: false }]),
    '{"version":2,"items":[{"title":"Read SICP","url":null,"read":false}]}');
});

test("round trip", () => {
  const items = [{ title: "Read SICP", url: "https://example.com/sicp", read: true }];
  assert.deepEqual(loadItems(saveItems(items)), items);
});

test("loads a version 1 list", () => {
  assert.deepEqual(loadItems(fixture("list-v1.json")), [
    { title: "Read SICP", url: "https://example.com/sicp", read: true },
    { title: "Call Ana", url: null, read: false },
  ]);
});
