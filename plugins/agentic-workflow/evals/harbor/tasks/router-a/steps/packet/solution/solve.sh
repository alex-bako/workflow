#!/bin/bash
# Oracle, step 1: the packet for the planted variant (caller outside the diff).
set -euo pipefail
cd /app
base=$(git rev-parse base)
head=$(git rev-parse main)
cat > /app/review-packet.md <<EOF
# Review packet — T1

## Identity
- Bullet T1 (card M2.1 Exact money). Worktree \`/app\`.
- Base \`$base\` (tag base). Head \`$head\` (main).

## Contract
- \`docs/plans/T1.md:8\`: "\`parseAmount\` returns integer cents: \`"12.50"\` → \`1250\`, \`"\$3"\` → \`300\`."
- \`docs/plans/T1.md:10\`: "Every caller of \`parseAmount\` or \`formatAmount\` works in cents; every printed amount is unchanged for the same input."
- \`docs/plans/T1.md:15-16\`: "Money is an integer number of cents between parsing and formatting; no float arithmetic on dollars."
- \`src/money.mjs:5\`: "\`parseAmount\` @returns {number} the amount in integer cents, e.g. 1250".
- Scope fence \`docs/plans/T1.md:22-24\`: T2 owns \`src/discounts/\`; \`legacy/\` untouched.

## Change map
- Step 1: \`src/money.mjs:11\` parseAmount returns cents; \`:15-16\` formatAmount takes cents. Risk: unit of every return value.
- Step 2: \`src/cart.mjs:7\` drops the float rounding.
- Step 3: \`test/money.test.mjs\`, \`test/cart.test.mjs\`.
- Step 4: \`src/generated/schema.mjs\`, \`package.json\`, \`package-lock.json\` (description and version only).

## Must read
- \`src/invoice.mjs:9-13\` \`invoiceLine\`: calls \`parseAmount\`, whose unit changed to cents; formats with its own \`toFixed\`; outside the diff; no test covers it.

## Skip
- \`src/generated/schema.mjs\`: generated, never edited by hand.
- \`package-lock.json\`: lockfile version bump.
- \`legacy/\`: retired, nothing imports it.
- \`src/discounts/\`: sibling bullet T2.

## Lenses
- Money unit at every \`parseAmount\` / \`formatAmount\` boundary (cents vs dollars).
- Float arithmetic on amounts.

## Evidence
- QA: \`node --test\` on head, all pass.
- Rerun: \`node --test\`; \`git diff base..main -- src/money.mjs src/cart.mjs\`; \`grep -rn parseAmount src\`.
EOF
