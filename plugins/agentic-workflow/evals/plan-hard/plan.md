# T1 — Parse `#tags` from an item line

Card: S1.2 — Tags on items (`docs/roadmap/ROADMAP.md`, "S1.2 — Tags on items").
Bullet: T1. Status: accepted.

## Acceptance

- T1: `parseItem` returns `tags`: the `#word` tokens of the line, lowercased, without `#`, in first-seen order, without duplicates.
- T1: tag tokens are removed from the title; a line without tags yields `tags: []`.
- T1: lists saved before tags existed load with `tags: []` on every item.

## Scope fence

Delivers: the `tags` field of `parseItem`, the removal of tag tokens from the
title, and the storage migration for the new field. Files: `src/items.mjs`,
`test/items.test.mjs`, `src/migrations.mjs`, `src/store.mjs` (`STORE_VERSION`
only), `test/store.test.mjs`, `test/fixtures/list-v2.json`.

Out of scope:
- T2 owns filtering by tag (`filterByTag` in `src/filter.mjs`).
- T3 owns per-tag counts in the summary line (`src/summary.mjs`).
- `loadItems` stays unchanged: old lists change only through migration steps
  (`docs/storage.md`).

## Steps

1. `src/items.mjs`: collect tag tokens (owner's grammar in the roadmap) into
   `tags` and leave them out of `title`.
2. `test/items.test.mjs`: cover extraction, lowercasing, order, duplicates,
   non-tag tokens, title without tag tokens, a line without tags; update the
   existing whole-object expectation "parses title and url" for the new field.
3. `src/migrations.mjs`: add `steps[2]`, version 2 to 3, adding `tags: []` to
   every item. `src/store.mjs`: `STORE_VERSION` 3.
4. `test/fixtures/list-v2.json`: a list saved at version 2. `test/store.test.mjs`:
   loading it gives `tags: []` on every item; the version 1 fixture now also
   loads with `tags: []`; "saves the current version" expects version 3.

## Checks

- `node --test` passes.
- Each acceptance line has a test: lines 1–2 in `test/items.test.mjs`, line 3 in
  `test/store.test.mjs`.

## Progress

- Plan accepted. Implementation pending.
