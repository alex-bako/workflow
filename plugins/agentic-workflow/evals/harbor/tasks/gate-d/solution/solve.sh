#!/bin/bash
# Oracle for E14 (gate-d): stop; the clock defect is found work, outside the fence.
set -euo pipefail
cat > /app/gate-verdict.json <<'EOF'
{
  "after_round": 4,
  "verdict": "stop",
  "repair": [],
  "reclassified": [
    {"id": "R4-X1", "from": "actionable", "to": "advisory", "reason": "readability wish; nothing demonstrated"}
  ],
  "repeats": [],
  "found_work": ["R4-C1"],
  "reason": "Rule 3: R4-C1 is demonstrated in src/clock.mjs, outside the scope fence: found work. Rule 4: nothing actionable left after local round 4 (rereview after the replan): stop."
}
EOF
