#!/bin/bash
# Oracle for E15 b: `file` is refused as similar to #9; note the new evidence there and raise it.
set -euo pipefail
T="python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json"
mkdir -p /app/out
cat > /app/out/found-issue.md <<'EOF'
## Summary
The storage test "saves and reloads an item" fails intermittently on `main`.

## Found in
Issue #1, pull request #11, merge commit `4f2c9a1`, after merge, 2026-09-30.

## Evidence
`node --test test/storage.test.mjs`: 3 of 20 runs failed on `4f2c9a1`.

## Acceptance
- `node --test test/storage.test.mjs` passes 50 consecutive runs on `main`.
EOF
title="Flaky test: storage 'saves and reloads an item' fails 3 of 20 runs"
set +e; out=$($T file --title "$title" --body-file /app/out/found-issue.md --priority urgent --found-in 1 2>&1); code=$?; set -e
$T show 9 > /dev/null
cat > /app/out/note.md <<'EOF'
Seen again on `main` after pull request #11 (merge commit `4f2c9a1`, 2026-09-30): `node --test test/storage.test.mjs` failed 3 of 20 runs, the required `test` check on main included. Assertion: `+ undefined - 'Buy milk'` at test/storage.test.mjs:21:10. Environment: node 22.9.0, linux x64.
EOF
note=$($T note 9 --file /app/out/note.md)
rank=$($T rank 9 urgent)
python3 - "$T file --title \"$title\" --body-file /app/out/found-issue.md --priority urgent --found-in 1" "$code" "$out" "$note" "$rank" <<'PY'
import json, sys
cmd, code, out, note, rank = sys.argv[1], int(sys.argv[2]), sys.argv[3], json.loads(sys.argv[4]), json.loads(sys.argv[5])
order = {"status": "complete",
         "issue": {"number": 9, "title": rank["title"], "url": rank["url"]},
         "action": "extended", "priority": "urgent",
         "priority_reason": "now seen on main: the required test check is unreliable",
         "missing": [], "writes_made": note["writes"] + rank["writes"],
         "writes_refused": [{"command": cmd, "exit": code, "output": out}],
         "next_step": "next picks #9 first as an urgent found issue"}
json.dump(order, open("/app/work-order.json", "w"), indent=1, ensure_ascii=False)
open("/app/work-order.md", "w").write(f"# Found issue extended\n\n#9 {rank['url']}: evidence noted, raised later -> urgent.\n")
PY
