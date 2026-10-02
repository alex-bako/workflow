You are dispatched as the worker described in `/opt/aw/agents/aw-planner.md`. Read that
file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

Plan bullet S1.2.T1. Worktree `/app` (read-only except the plan), project instructions
`AGENTS.md`. Write the plan to `docs/plans/T1.md`, following `/opt/aw/skills/aw-plan/SKILL.md`.
Work order (from the steward):
- Kind: bullet. Card S1.2 — Tags on items (#12); bullet S1.2.T1 (#13), "Parse `#tags`
  from an item line into `tags`".
- Authority: `docs/roadmap/ROADMAP.md`, heading "S1.2 — Tags on items".
- Dependencies: S1.1 (#11) closed.
- Acceptance (verbatim):
  - T1: `parseItem` returns `tags`: the `#word` tokens of the line, lowercased, without `#`, in first-seen order, without duplicates.
  - T1: tag tokens are removed from the title; a line without tags yields `tags: []`.
  - T1: lists saved before tags existed load with `tags: []` on every item.
- Siblings, out of scope: S1.2.T2 — Filter the list by one tag; S1.2.T3 — Show
  per-tag counts in the summary line.
- Repository: acme/reading-list, base `main`, merge rebase. Branch `feat/s1.2-tags`.
- Existing plan: none.

Output contract. Besides the plan, write only `/app/plan-report.json`, exactly this shape:

```json
{
  "status": "complete | blocked",
  "plan": "docs/plans/T1.md, or null when no plan was written",
  "acceptance_mapping": [{"line": "acceptance line, verbatim", "check": "the test or command that demonstrates it"}],
  "required_checks": ["command"],
  "open_questions": [{"question": "one material question", "recommendation": "your recommended answer"}]
}
```

`complete` means the bullet can be built without guessing material behavior;
otherwise `blocked`. Use `[]` for empty lists.
