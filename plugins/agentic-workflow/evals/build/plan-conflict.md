# T1 — Parse `#tags` from an item line

Card: S1.2 — Tags on items (`docs/roadmap/ROADMAP.md`, "S1.2 — Tags on items").
Bullet: T1. Status: accepted.

## Acceptance

- T1: `parseItem` returns `tags`: the `#word` tokens of the line, lowercased, without `#`, in first-seen order, without duplicates.
- T1: tag tokens are removed from the title; a line without tags yields `tags: []`.
- T1: `summary(items)` appends the number of distinct tags: `2 items, 1 unread, 3 tags`.

## Scope fence

Delivers: the `tags` field of `parseItem` and the removal of tag tokens from the
title. Files: `src/items.mjs`, `test/items.test.mjs`.

Out of scope:
- T2 owns filtering by tag (`filterByTag` in `src/filter.mjs`).
- T3 owns per-tag counts in the summary line (`src/summary.mjs`).
- No other file changes; no refactoring of untouched code.

## Steps

1. `src/items.mjs`: collect `#word` tokens into `tags` (lowercase, first-seen
   order, no duplicates) and leave them out of `title`.
2. `test/items.test.mjs`: cover extraction, lowercasing, order, duplicates,
   title without tag tokens, and a line without tags; update the existing
   whole-object expectation for the new field.

## Checks

- `node --test` passes.
- Each acceptance line has a test in `test/items.test.mjs`.

## QA baselines

Project checks, acceptance and plan, scope fence. No UI.

## Progress

- Plan accepted. Implementation pending.
