import { migrate } from "./migrations.mjs";

// Version of the saved list file ({ version, items }); see docs/storage.md.
export const STORE_VERSION = 2;

export function saveItems(items) {
  return JSON.stringify({ version: STORE_VERSION, items });
}

export function loadItems(text) {
  return migrate(JSON.parse(text), STORE_VERSION).items;
}
