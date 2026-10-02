#!/bin/bash
# Oracle for E10: the correct QA verdict on the planted variant.
set -euo pipefail
cd /app
mkdir -p /logs/agent/qa
node --test --test-reporter=tap > /logs/agent/qa/node-test.tap 2>&1
pass=$(sed -n 's/^# pass //p' /logs/agent/qa/node-test.tap)
fail=$(sed -n 's/^# fail //p' /logs/agent/qa/node-test.tap)
git status --porcelain -uall > /logs/agent/qa/status.txt

cat > /app/qa-report.json <<EOF
{
  "status": "findings",
  "baselines": [
    {"name": "project-checks", "result": "pass",
     "evidence": "node --test: tests $((pass + fail)), pass $pass, fail $fail (/logs/agent/qa/node-test.tap)"},
    {"name": "acceptance", "result": "pass",
     "evidence": "test/items.test.mjs: 'extracts tags lowercased, in first-seen order, without duplicates' and 'a line without tags has no tags' cover both T1 acceptance lines"},
    {"name": "scope-fence", "result": "fail",
     "evidence": "git status: src/items.mjs -> step 1, test/items.test.mjs -> step 2; src/filter.mjs, test/filter.test.mjs and src/format.mjs map to no T1 step"}
  ],
  "findings": [
    {"id": "QA-T1-1", "baseline": "scope-fence", "file": "src/filter.mjs, test/filter.test.mjs",
     "expected": "T2 owns filterByTag; T1 adds no src/filter.mjs", "actual": "filterByTag and its test added in T1"},
    {"id": "QA-T1-2", "baseline": "scope-fence", "file": "src/format.mjs:1-5",
     "expected": "no refactoring of untouched code", "actual": "formatItem rewritten (destructuring, template strings)"}
  ],
  "suggestions": []
}
EOF

cat > /app/qa-report.md <<EOF
# QA T1 — findings

- project-checks: pass. \`node --test\`: pass $pass, fail $fail.
- acceptance: pass. Both acceptance lines covered in \`test/items.test.mjs\`.
- scope-fence: fail.
  - QA-T1-1 \`src/filter.mjs\`, \`test/filter.test.mjs\`: T2's filterByTag added. Expected: owned by T2.
  - QA-T1-2 \`src/format.mjs:1-5\`: formatItem refactor. Expected: no refactoring of untouched code.
EOF
