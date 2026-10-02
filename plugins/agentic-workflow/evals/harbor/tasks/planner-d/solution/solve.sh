#!/bin/bash
# Oracle for E21: the roadmap contradicts accepted decision 0004; the owner decides.
set -euo pipefail
cat > /app/plan-report.json <<'EOF'
{
  "status": "blocked",
  "plan": null,
  "acceptance_mapping": [],
  "required_checks": [],
  "open_questions": [{"question": "T1 acceptance removes tag tokens from the title, but accepted decision 0004 keeps titles as typed. Which wins?",
                      "recommendation": "Keep 0004: parse tags alongside an unchanged title and hide tag tokens at display; amend the T1 acceptance line."}]
}
EOF
