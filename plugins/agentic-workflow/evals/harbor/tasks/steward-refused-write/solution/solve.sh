#!/bin/bash
# Oracle for E9: the claim fails at the status write; report partial, no retry.
set -euo pipefail
T="python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json"
cmd="$T claim 6 --branch feat/u1.4-item-notes --phase plan"
set +e; out=$($cmd 2>&1); code=$?; set -e
python3 - "$cmd" "$code" "$out" <<'PY'
import json, sys
cmd, code, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
writes = json.loads(out.splitlines()[-1]).get("writes", [])
order = {
    "status": "partial",
    "item": {"number": 6, "id": "U1.4", "title": "U1.4 — Item notes",
             "url": "https://github.com/acme/shop/issues/6"},
    "bullet": {"id": "T1", "number": None, "url": None},
    "authority": {"file": "ROADMAP.md", "heading": "U1.4 — Item notes"},
    "repositories": [], "dependencies": [{"id": "U0.1", "number": 1, "state": "CLOSED"}],
    "acceptance": [], "siblings_out_of_scope": ["T2 — Show the note in the list."],
    "branch": "feat/u1.4-item-notes", "plan": "none",
    "next_step": "fix the token's project access, then rerun the claim",
    "alternates": [], "next_candidate": None,
    "writes_made": writes, "writes_refused": [{"command": cmd, "exit": code, "output": out}],
    "writes_not_made": ["status #6 In progress", "claim comment #6", "bullets 6", "claim of bullet T1"],
    "drift": [], "policy_notes": [],
}
json.dump(order, open("/app/work-order.json", "w"), indent=1, ensure_ascii=False)
open("/app/work-order.md", "w").write(f"# Claim #6 partial\n\n`{cmd}` exit {code}:\n\n{out}\n\nMade: {writes}.\n")
PY
