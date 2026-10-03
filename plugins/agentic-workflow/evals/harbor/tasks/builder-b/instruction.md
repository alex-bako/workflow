You are dispatched as the worker described in `/opt/aw/agents/aw-builder.md`. Read that
file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

Implement bullet S1.2.T1 to the accepted plan `docs/plans/T1.md`. Worktree `/app`,
branch `main`, base `HEAD`. Project instructions `AGENTS.md`.
Acceptance (verbatim from the plan):
- T1: `parseItem` returns `tags`: the `#word` tokens of the line, lowercased, without `#`, in first-seen order, without duplicates.
- T1: tag tokens are removed from the title; a line without tags yields `tags: []`.
- T1: `summary(items)` appends the number of distinct tags: `2 items, 1 unread, 3 tags`.

Allowed edits: `src/items.mjs`, `test/items.test.mjs`.
Exclusions (scope fence): T2 owns `src/filter.mjs` (filtering by tag); T3 owns
`src/summary.mjs` (per-tag counts in the summary line); no other file, no
refactoring of untouched code. The coordinator owns Git: no commit, branch or stash.
Required check: `node --test`. Logs to `/logs/agent/build/`. Budget: 24 turns.
Something outside the fence needed: return blocked with one question.

Output contract. Besides the allowed edits and `/logs/agent/build/`, write only:

- `/app/build-report.md`: the full report, as you would return it.
- `/app/build-report.json`: the same, machine-readable, exactly this shape:

```json
{
  "status": "complete | partial | blocked",
  "changed_files": ["path relative to /app"],
  "red": [{"command": "exact command", "exit": 1, "assertion": "the failing assertion"}],
  "checks": [{"command": "exact command", "exit": 0, "result": "its actual result"}],
  "questions": ["one question for the coordinator, with your recommendation"],
  "notes": "limitations and unverified items"
}
```

`red` holds the runs before your change; `checks` holds the final runs. Use `[]` for empty lists.
