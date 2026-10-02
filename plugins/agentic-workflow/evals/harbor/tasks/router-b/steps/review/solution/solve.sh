#!/bin/bash
# Oracle, step 2: the control change is correct; the reviewer reports it clean.
set -euo pipefail
cd /app
mkdir -p /logs/agent/review
node --test > /logs/agent/review/node-test.txt 2>&1
cat > /app/review-report.json <<'EOF'
{"status": "clean", "findings": [], "unverified": []}
EOF
cat > /app/review-report.md <<'EOF'
# Review T1 — clean

- `node --test` passes 6/6, including `test/invoice.test.mjs`.
- `src/invoice.mjs:12` prints through `formatAmount`; `src/cart.mjs:7` sums cents.
EOF
