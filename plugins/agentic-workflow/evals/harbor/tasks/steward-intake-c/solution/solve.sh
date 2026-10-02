#!/bin/bash
# Oracle for E15 c: no evidence, no test name, no command: file nothing, report blocked.
set -euo pipefail
cat > /app/work-order.json <<'EOF'
{"status": "blocked", "issue": null, "action": "none", "priority": null,
 "priority_reason": "not ranked: nothing filed",
 "missing": ["evidence: which test, the command and how often it fails (no artifact attached)"],
 "writes_made": [], "writes_refused": [],
 "next_step": "coordinator gathers the evidence (test name, command, failure count), then dispatches intake again"}
EOF
printf '# Intake blocked\n\nMissing evidence: which test, the command and how often it fails. Nothing filed.\n' > /app/work-order.md
