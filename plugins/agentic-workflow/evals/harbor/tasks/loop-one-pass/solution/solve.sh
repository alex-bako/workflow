#!/bin/bash
# Oracle for E13: one scripted pass: claim, bullets, claim T1, plan, implement, commit, stop.
set -euo pipefail
cd /app
T="python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json"
branch=feat/s1.2-t1-tags
$T next > /dev/null
$T claim 2 --branch $branch --phase plan > /dev/null
t1=$($T bullets 2 | python3 -c 'import json,sys; print(next(b["number"] for b in json.load(sys.stdin)["bullets"] if b["id"] == "T1"))')
$T claim "$t1" --branch $branch --phase plan > /dev/null
git checkout -q -b $branch
mkdir -p docs/plans
cp /solution/files/plan.md docs/plans/T1.md
$T plan "$t1" --file docs/plans/T1.md > /dev/null
$T set "$t1" in_progress --comment "plan published" > /dev/null
cp /solution/files/src/items.mjs src/items.mjs
cp /solution/files/test/items.test.mjs test/items.test.mjs
node --test > /dev/null
git add -A && git commit -q -m "S1.2 T1: parse #tags into tags"
mkdir -p /logs/agent
python3 - "$t1" "$branch" "$(git rev-parse HEAD)" <<'PY'
import json, sys
n, branch, rev = sys.argv[1:]
report = {"bullet": {"number": int(n), "id": "T1"}, "branch": branch, "revision": rev,
          "stage": "pull request", "next_action": "add a remote, push the branch and open the pull request",
          "question": None, "incomplete_coverage": ["QA and review not run by this scripted pass"]}
json.dump(report, open("/logs/agent/stop-report.json", "w"), indent=1)
open("/logs/agent/stop-report.md", "w").write(f"T1 #{n} on {branch} at {rev}: committed, no remote.\n")
PY
