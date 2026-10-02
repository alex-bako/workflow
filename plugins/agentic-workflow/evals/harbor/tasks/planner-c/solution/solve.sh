#!/bin/bash
# Oracle for E20: the reference plan, with the migration, and its report.
set -euo pipefail
cd /app
cp /solution/files/T1.md docs/plans/T1.md
cat > /app/plan-report.json <<'EOF'
{
  "status": "complete",
  "plan": "docs/plans/T1.md",
  "acceptance_mapping": [
    {"line": "T1: `parseItem` returns `tags`: the `#word` tokens of the line, lowercased, without `#`, in first-seen order, without duplicates.",
     "check": "test/items.test.mjs: extraction, lowercasing, order, duplicates"},
    {"line": "T1: tag tokens are removed from the title; a line without tags yields `tags: []`.",
     "check": "test/items.test.mjs: title without tag tokens; line without tags"},
    {"line": "T1: lists saved before tags existed load with `tags: []` on every item.",
     "check": "test/store.test.mjs: loads test/fixtures/list-v2.json and list-v1.json with tags: []"}
  ],
  "required_checks": ["node --test"],
  "open_questions": []
}
EOF
