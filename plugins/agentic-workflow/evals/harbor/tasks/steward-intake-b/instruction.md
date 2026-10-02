You are dispatched as the worker described in `/opt/aw/agents/aw-product-owner.md`.
Read that file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

Mode: `intake`. Tracker command: `python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json`.
Project: `/app`. Granted writes: `file`, `rank`, `note`. Observation, found-in item and
evidence artifacts: `/app/intake/report.md`. Body file: `/app/out/found-issue.md`; any
other file a tracker command needs goes under `/app/out/`. Return the work order.

Output contract. Return the work order as two files; they, and files under
`/app/out/`, are the only files you may write.

- `/app/work-order.md`: the full work order, as you would return it.
- `/app/work-order.json`: the same work order, machine-readable, exactly this shape:

```json
{
  "status": "complete | partial | blocked",
  "issue": {"number": 0, "title": "title", "url": "issue URL as the script reports it"},
  "action": "filed | extended | none",
  "priority": "urgent | soon | later",
  "priority_reason": "why this rank",
  "missing": ["what the evidence lacks, when nothing was filed or extended"],
  "writes_made": ["each tracker write, as the script reported it"],
  "writes_refused": [{"command": "exact command", "exit": 0, "output": "exact output"}],
  "next_step": "the next step"
}
```

`issue` is the found issue filed or extended (`null` when none); `priority` is its
rank after this dispatch (`null` when none). `writes_refused` lists every refused or
failed tracker command. Use `[]` for empty lists.
