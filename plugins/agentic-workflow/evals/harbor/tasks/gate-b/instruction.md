You are dispatched as the worker described in `/opt/aw/agents/aw-arbiter.md`. Read
that file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

Gate the review loop of bullet T1 after its latest adjudicated round. Worktree
`/app`, read-only. Ledger `/app/docs/plans/T1.review.json`, plan
`/app/docs/plans/T1.md`, stage `local`. Verdict path `/app/gate-verdict.json`.
Return the verdict.

Output contract. `/app/gate-verdict.json` is the only file you may write: the
verdict JSON, exactly this shape:

```json
{
  "after_round": 0,
  "verdict": "stop | repair | replan | ask",
  "repair": ["finding id"],
  "reclassified": [{"id": "finding id", "from": "class", "to": "class", "reason": "why"}],
  "repeats": [{"id": "finding id", "of": "earlier finding id"}],
  "found_work": ["finding id"],
  "reason": "the rule and round count that decided it"
}
```

Use `[]` for empty lists.
