#!/bin/bash
# Oracle for E17: nothing outside the fence is built; one question goes back.
set -euo pipefail
cd /app
mkdir -p /logs/agent/build
cat > /app/build-report.json <<'EOF'
{
  "status": "blocked",
  "changed_files": [],
  "checks": [],
  "questions": ["Acceptance line 3 needs src/summary.mjs, which the fence gives to T3. Recommendation: move the distinct-tag count to T3 (replan T1 without it), then build T1."],
  "notes": "Nothing built: the plan contradicts its own scope fence."
}
EOF
printf 'Status: blocked. Acceptance needs src/summary.mjs (T3). Question returned.\n' > /app/build-report.md
