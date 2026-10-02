#!/bin/bash
# Oracle, step 2: the reviewer finds the caller defect named under Must read.
set -euo pipefail
cd /app
mkdir -p /logs/agent/review
node --test > /logs/agent/review/node-test.txt 2>&1 || true
line=$(node --input-type=module -e 'import { invoiceLine } from "/app/src/invoice.mjs";
console.log(invoiceLine({ name: "Tea", price: "3.50", quantity: 2 }));')
echo "$line" > /logs/agent/review/invoice-line.txt

cat > /app/review-report.json <<EOF
{
  "status": "findings",
  "findings": [
    {"id": "RV-T1-1", "severity": "major", "file": "src/invoice.mjs:12",
     "impact": "invoiceLine prints integer cents as dollars: price 3.50 x2 prints '$line', expected 'Tea x2 @ \$3.50 = \$7.00' (docs/plans/T1.md:10)",
     "evidence": "node -e invoiceLine({name:'Tea',price:'3.50',quantity:2}) -> '$line'; parseAmount now returns cents (src/money.mjs:11); invoiceLine still formats with toFixed (src/invoice.mjs:12); no test covers it",
     "fix": "format with formatAmount(unit) and formatAmount(sum); add test/invoice.test.mjs"}
  ],
  "unverified": []
}
EOF
cat > /app/review-report.md <<EOF
# Review T1 — findings

- RV-T1-1 (major) \`src/invoice.mjs:12\`: \`invoiceLine\` prints cents as dollars: \`$line\`.
  Expected "Tea x2 @ \$3.50 = \$7.00" per \`docs/plans/T1.md:10\`. Fix: use \`formatAmount\`.
- Checks: \`node --test\` passes; no test covers the invoice.
EOF
