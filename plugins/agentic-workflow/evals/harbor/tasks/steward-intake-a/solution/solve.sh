#!/bin/bash
# Oracle for E15 a: file the flaky test once with the artifact's evidence, ranked urgent.
set -euo pipefail
T="python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json"
mkdir -p /app/out
cat > /app/out/found-issue.md <<'EOF'
## Summary
The storage test "saves and reloads an item" fails intermittently on `main`.

## Found in
Issue #1 (U0.1 — Item storage), pull request #11, merge commit `4f2c9a1`, after merge, 2026-09-30.

## Evidence
- Command: `node --test test/storage.test.mjs` on commit `4f2c9a1`.
- Frequency: 3 of 20 runs failed (runs 07, 12, 18).
- Output: `AssertionError [ERR_ASSERTION]: Expected values to be strictly equal: + undefined - 'Buy milk'` at test/storage.test.mjs:21:10.
- First seen: 2026-09-30, required check `test` on `main`.
- Environment: node 22.9.0, linux x64, CI runner ubuntu-24.04.

## Impact
The required `test` check on `main` is unreliable; unrelated pull requests can fail it.

## Suspected cause
Assumption: unknown; the item reads back as undefined, possibly a save not awaited.

## Acceptance
- `node --test test/storage.test.mjs` passes 50 consecutive runs on `main`.

Repositories: shop

## Priority
urgent: a required check on the main branch is unreliable.
EOF
out=$($T file --title "Flaky test: storage 'saves and reloads an item' fails 3 of 20 runs" \
      --body-file /app/out/found-issue.md --priority urgent --found-in 1)
python3 - "$out" <<'PY'
import json, sys
res = json.loads(sys.argv[1])
order = {"status": "complete",
         "issue": {"number": res["number"], "title": res["title"], "url": res["url"]},
         "action": "filed", "priority": "urgent",
         "priority_reason": "the required test check on main is unreliable (3 of 20 runs fail)",
         "missing": [], "writes_made": res.get("writes", []), "writes_refused": [],
         "next_step": "next picks it first as an urgent found issue"}
json.dump(order, open("/app/work-order.json", "w"), indent=1, ensure_ascii=False)
open("/app/work-order.md", "w").write(f"# Found issue filed\n\n#{res['number']} {res['url']}, urgent: required check on main unreliable.\n")
PY
