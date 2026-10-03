#!/bin/bash
# Oracle for E16: the reference implementation and tests, with an honest report.
set -euo pipefail
cd /app
mkdir -p /logs/agent/build
cp /solution/files/test/items.test.mjs test/items.test.mjs
set +e
node --test > /logs/agent/build/node-test-red.log 2>&1
red=$?
set -e
cp /solution/files/src/items.mjs src/items.mjs
set +e
node --test > /logs/agent/build/node-test.log 2>&1
code=$?
set -e
summary=$(grep -E '^. (pass|fail) ' /logs/agent/build/node-test.log | tr '\n' ' ')
cat > /app/build-report.json <<EOF
{
  "status": "complete",
  "changed_files": ["src/items.mjs", "test/items.test.mjs"],
  "red": [{"command": "node --test", "exit": $red, "assertion": "tags missing from parseItem (/logs/agent/build/node-test-red.log)"}],
  "checks": [{"command": "node --test", "exit": $code, "result": "$summary(/logs/agent/build/node-test.log)"}],
  "questions": [],
  "notes": "none"
}
EOF
printf 'Status: complete. T1 tags in src/items.mjs; tests in test/items.test.mjs. node --test exit %s.\n' "$code" > /app/build-report.md
