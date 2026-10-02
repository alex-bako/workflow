#!/bin/bash
# Oracle for E14 (gate-a): stop; the P1 style finding is advisory, the renaming a repeat.
set -euo pipefail
cat > /app/gate-verdict.json <<'EOF'
{
  "after_round": 2,
  "verdict": "stop",
  "repair": [],
  "reclassified": [
    {"id": "R2-X1", "from": "actionable", "to": "advisory", "reason": "readability wish; no failing command, contract line or wrong behavior shown"},
    {"id": "R2-X2", "from": "advisory", "to": "rejected", "reason": "repeat of R1-X1, answered in round 1, no new evidence"}
  ],
  "repeats": [{"id": "R2-X2", "of": "R1-X1"}],
  "found_work": [],
  "reason": "Rule 4: no actionable finding left after local round 2 of 2; stop. R2-C1, R2-C2 and R2-X1 are advisory, R2-X2 a repeat."
}
EOF
