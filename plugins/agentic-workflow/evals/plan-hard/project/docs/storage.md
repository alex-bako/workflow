# Saved lists

A saved list is `{ "version": N, "items": [...] }`, written by `saveItems` and read
by `loadItems` in `src/store.mjs`.

Every change to the shape of a saved item:

1. adds the step `steps[N]` (version N to N + 1) to `src/migrations.mjs`;
2. bumps `STORE_VERSION` in `src/store.mjs` to N + 1;
3. adds `test/fixtures/list-v<N>.json`, a list saved at the old version, and a test
   in `test/store.test.mjs` that loads it.

`loadItems` never patches fields itself: old lists change only through migration steps.
