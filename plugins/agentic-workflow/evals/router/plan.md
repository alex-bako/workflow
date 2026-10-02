# T1 — Prices in integer cents

Card: M2.1 — Exact money (bullets: T1 prices in cents, T2 percentage discounts,
T3 order export). Bullet: T1. Status: accepted.

## Acceptance

- `parseAmount` returns integer cents: `"12.50"` → `1250`, `"$3"` → `300`.
- `formatAmount` takes integer cents and prints dollars: `1250` → `"$12.50"`.
- Every caller of `parseAmount` or `formatAmount` works in cents; every printed amount is unchanged for the same input.
- Invalid input still throws `RangeError`, and so does a total above
  `Number.MAX_SAFE_INTEGER` cents (it cannot be printed exactly).

## Invariants

- Money is an integer number of cents between parsing and formatting; no float
  arithmetic on dollars.

## Scope fence

Delivers: the cents contract of `src/money.mjs` and the callers that depend on it.
Out of scope:
- T2 owns percentage discounts (`src/discounts/`).
- T3 owns the order export.
- `legacy/` is retired and untouched.

## Steps

1. `src/money.mjs`: `parseAmount` returns cents; `formatAmount` takes cents.
2. Callers: `src/cart.mjs` sums cents and drops the float rounding.
3. Tests: `test/money.test.mjs`, `test/cart.test.mjs` for cents and no float drift.
4. Housekeeping: regenerate `src/generated/schema.mjs` (price description);
   version 0.4.0 in `package.json` and `package-lock.json`.

## Checks

- `node --test` passes.

## Progress

- Implemented and committed for review.
