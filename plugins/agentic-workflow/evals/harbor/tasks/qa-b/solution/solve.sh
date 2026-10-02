#!/bin/bash
# Oracle for E11: the correct QA verdict on the control (exactly T1).
set -euo pipefail
cd /app
mkdir -p /logs/agent/qa
node --test --test-reporter=tap > /logs/agent/qa/node-test.tap 2>&1
pass=$(sed -n 's/^# pass //p' /logs/agent/qa/node-test.tap)
fail=$(sed -n 's/^# fail //p' /logs/agent/qa/node-test.tap)
git status --porcelain -uall > /logs/agent/qa/status.txt

cat > /app/qa-report.json <<EOF
{
  "status": "clean",
  "baselines": [
    {"name": "project-checks", "result": "pass",
     "evidence": "node --test: tests $((pass + fail)), pass $pass, fail $fail (/logs/agent/qa/node-test.tap)"},
    {"name": "acceptance", "result": "pass",
     "evidence": "test/items.test.mjs: 'extracts tags lowercased, in first-seen order, without duplicates' and 'a line without tags has no tags' cover both T1 acceptance lines"},
    {"name": "scope-fence", "result": "pass",
     "evidence": "git status: src/items.mjs -> step 1, test/items.test.mjs -> step 2; no other changes"}
  ],
  "findings": [],
  "suggestions": []
}
EOF

cat > /app/qa-report.md <<EOF
# QA T1 — clean

- project-checks: pass. \`node --test\`: pass $pass, fail $fail.
- acceptance: pass. Both acceptance lines covered in \`test/items.test.mjs\`.
- scope-fence: pass. \`src/items.mjs\` -> step 1, \`test/items.test.mjs\` -> step 2.
EOF
