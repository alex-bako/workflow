import { test } from "node:test";
import assert from "node:assert/strict";
import { cartTotal } from "../src/cart.mjs";

test("totals cart lines", () => {
  assert.equal(cartTotal([{ name: "Tea", price: "3.50", quantity: 2 }, { name: "Mug", price: "$0.10", quantity: 3 }]), "$7.30");
});
