You are dispatched as the worker described in `/opt/aw/agents/aw-product-owner.md`.
Read that file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

Mode: `claim`. Tracker command: `python3 /opt/aw/scripts/tracker.py --policy /app/tracker-policy.json`.
Project: `/app`. Granted writes: `bullets`, `claim`. Item #6, branch `feat/u1.4-item-notes`,
phase `plan`. Return the work order.

Output contract. Return the work order as two files; they are the only files you
may write.

- `/app/work-order.md`: the full work order, as you would return it.
- `/app/work-order.json`: the same work order, machine-readable, exactly this shape:

```json
{
  "status": "complete | partial | blocked",
  "item": {"number": 0, "id": "card id", "title": "title", "url": "card URL as the script reports it"},
  "bullet": {"id": "bullet id", "number": null, "url": null},
  "authority": {"file": "path", "heading": "heading text"},
  "repositories": [{"repo": "owner/name", "base": "branch", "merge": "method"}],
  "dependencies": [{"id": "card id", "number": 0, "state": "OPEN | CLOSED"}],
  "acceptance": ["each acceptance line, verbatim"],
  "siblings_out_of_scope": ["each sibling bullet: id and summary"],
  "branch": "branch name",
  "plan": "existing plan path, or none",
  "next_step": "the next step",
  "alternates": [{"number": 0, "id": "card id"}],
  "next_candidate": {"number": 0, "id": "card id"},
  "writes_made": ["each tracker write, as the script reported it"],
  "writes_refused": [{"command": "exact command", "exit": 0, "output": "exact output"}],
  "writes_not_made": ["each granted write that was not made"],
  "drift": [{"number": 0, "id": "card id", "detail": "what differs",
             "authority_line": "the authority file's line, verbatim"}],
  "policy_notes": ["each policy note"]
}
```

`item` is the card the work order is about (`null` when none); `bullet.number` and
`bullet.url` are `null` until the bullet issue exists. `next_candidate` is the card
to take instead when the work order's own card cannot proceed, else `null`.
`writes_refused` lists every refused or failed tracker command. Use `[]` for empty
lists.
