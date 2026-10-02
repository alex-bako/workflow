#!/bin/bash
# Oracle for E14 (gate-c): replan; the third local round still raises demonstrated defects.
set -euo pipefail
cat > /app/gate-verdict.json <<'EOF'
{
  "after_round": 3,
  "verdict": "replan",
  "repair": ["R3-C1", "R3-X1"],
  "reclassified": [],
  "repeats": [],
  "found_work": [],
  "reason": "Rule 4: local round 3 of 3 still has actionable R3-C1 and R3-X1, no earlier replan: replan."
}
EOF
