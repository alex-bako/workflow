import { test } from "node:test";
import assert from "node:assert/strict";
import { formatItem } from "../src/format.mjs";
import { summary } from "../src/summary.mjs";

test("formats read and unread rows", () => {
  assert.equal(formatItem({ title: "A", url: "https://a.test", read: true }), "[x] A <https://a.test>");
  assert.equal(formatItem({ title: "B", url: null, read: false }), "[ ] B");
});

test("summarizes counts", () => {
  assert.equal(summary([{ read: true }, { read: false }]), "2 items, 1 unread");
});
