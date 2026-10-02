#!/bin/bash
# Oracle for E14 (gate-b): repair exactly the demonstrated R2-C1.
set -euo pipefail
cat > /app/gate-verdict.json <<'EOF'
{
  "after_round": 2,
  "verdict": "repair",
  "repair": ["R2-C1"],
  "reclassified": [
    {"id": "R2-X1", "from": "actionable", "to": "advisory", "reason": "refactor wish for later bullets; nothing demonstrated"},
    {"id": "R2-X3", "from": "actionable", "to": "rejected", "reason": "unsupported: src/duration.mjs:10 uses Number.parseInt and PATTERN admits digits only; the quoted parseFloat line is not there"}
  ],
  "repeats": [],
  "found_work": [],
  "reason": "Rule 4: R2-C1 is demonstrated (acceptance line, failing command, line 23); local round 2 of 2, below 3: repair."
}
EOF
