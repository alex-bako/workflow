You are dispatched as the worker described in `/opt/aw/agents/aw-refuter.md`. Read
that file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

Review bullet T1. Start from the review packet `/app/review-packet.md`; it names
the snapshot (base..head in worktree `/app`), the contract and what to read.
Report actionable findings with evidence. No project writes; evidence to
`/logs/agent/review/`.

Output contract. The only files you may write are the two report files below and
files under `/logs/agent/review/`.

- `/app/review-report.md`: the full review (status, findings, checks run with
  their results, unverified items).
- `/app/review-report.json`: the same result, machine-readable, exactly this shape:

```json
{
  "status": "clean | findings | blocked",
  "findings": [
    {"id": "stable ID", "severity": "blocker | major | minor",
     "file": "path relative to /app:line", "impact": "demonstrated impact",
     "evidence": "commands run or code read, with actual results", "fix": "suggested fix"}
  ],
  "unverified": ["what could not be checked, and why"]
}
```

`findings` holds actionable findings only; `clean` means there are none. Use `[]`
for none.
