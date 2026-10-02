#!/bin/bash
# Oracle for E8: the claim is refused as taken; write nothing, return #7 from a fresh next.
set -euo pipefail
T="python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json"
cmd="$T claim 6 --branch feat/u1.4-item-notes --phase plan"
set +e; out=$($cmd 2>&1); code=$?; set -e
$T next > /dev/null
python3 - "$cmd" "$code" "$out" <<'PY'
import json, sys
cmd, code, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
order = {
    "status": "partial",
    "item": {"number": 6, "id": "U1.4", "title": "U1.4 — Item notes",
             "url": "https://github.com/acme/shop/issues/6"},
    "bullet": None, "authority": {"file": "ROADMAP.md", "heading": "U1.4 — Item notes"},
    "repositories": [], "dependencies": [], "acceptance": [], "siblings_out_of_scope": [],
    "branch": "feat/u1.4-item-notes", "plan": "none",
    "next_step": "claim #7 U1.5 if the coordinator chooses it",
    "alternates": [], "next_candidate": {"number": 7, "id": "U1.5"},
    "writes_made": [], "writes_refused": [{"command": cmd, "exit": code, "output": out}],
    "writes_not_made": ["claim #6", "bullets 6", "claim of bullet T1"],
    "drift": [], "policy_notes": [],
}
json.dump(order, open("/app/work-order.json", "w"), indent=1, ensure_ascii=False)
open("/app/work-order.md", "w").write(f"# Claim #6 refused\n\n`{cmd}` exit {code}: {out}\n\nNext candidate: #7 U1.5.\n")
PY
