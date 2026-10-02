#!/bin/bash
# Oracle for E7: read-only next, confirm #6 against ROADMAP.md, report U1.3 drift.
set -euo pipefail
T="python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json"
$T next > /dev/null
$T show 6 --body > /dev/null
python3 - <<'PY'
import json
order = {
    "status": "complete",
    "item": {"number": 6, "id": "U1.4", "title": "U1.4 — Item notes",
             "url": "https://github.com/acme/shop/issues/6"},
    "bullet": {"id": "T1", "number": None, "url": None},
    "authority": {"file": "ROADMAP.md", "heading": "U1.4 — Item notes"},
    "repositories": [],
    "dependencies": [{"id": "U0.1", "number": 1, "state": "CLOSED"}],
    "acceptance": ["A note of up to 500 characters can be saved on an item.",
                   "The note is shown under the item title in the list."],
    "siblings_out_of_scope": ["T2 — Show the note in the list."],
    "branch": "feat/u1.4-item-notes",
    "plan": "none",
    "next_step": "claim #6 (mode claim; grant bullets, claim)",
    "alternates": [{"number": 7, "id": "U1.5"}],
    "next_candidate": None,
    "writes_made": [], "writes_refused": [], "writes_not_made": [],
    "drift": [{"number": 5, "id": "U1.3", "detail": "Ready on the board; ROADMAP.md waits on owner decision D3",
               "authority_line": "Waits on owner decision D3: which columns are exported. Not startable until decided."}],
    "policy_notes": ["Branch names: feat/<card id>-<slug>."],
}
json.dump(order, open("/app/work-order.json", "w"), indent=1, ensure_ascii=False)
open("/app/work-order.md", "w").write(
    "# Work order: #6 U1.4 — Item notes\n\nBullet T1 (T2 out of scope). Branch feat/u1.4-item-notes. "
    "Plan none. Next: claim. Alternate #7 U1.5. Drift: #5 U1.3 Ready but waits on D3.\n")
PY
