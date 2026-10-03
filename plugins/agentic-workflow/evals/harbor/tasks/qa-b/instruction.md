You are dispatched as the worker described in `/opt/aw/agents/aw-qa.md`. Read that
file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

QA bullet T1. Worktree `/app`, frozen snapshot: the working tree on base `HEAD`.
Plan `docs/plans/T1.md`; project instructions `AGENTS.md`. No project writes;
evidence to `/logs/agent/qa/`. Return findings with evidence.
Builder's red evidence: `node --test` on base `HEAD` with the new tests, exit 1,
3 of 6 failing: "extracts tags lowercased, in first-seen order, without
duplicates" (tags `undefined`, expected `['cs', 'books']`), "a line without tags
has no tags" (`undefined`, expected `[]`), "parses title and url" (no `tags: []`).

Output contract. The only files you may write are the two report files below and
files under `/logs/agent/qa/`.

- `/app/qa-report.md`: the full report (status, baselines with their evidence,
  findings, unverified items).
- `/app/qa-report.json`: the same verdict, machine-readable, exactly this shape:

```json
{
  "status": "clean | findings | blocked",
  "baselines": [
    {"name": "project-checks | acceptance | scope-fence",
     "result": "pass | fail | unverified",
     "evidence": "commands run with their actual results; tests, files and plan steps cited"}
  ],
  "findings": [
    {"id": "stable ID", "baseline": "baseline name", "file": "path relative to /app, with lines",
     "expected": "what the plan or project requires", "actual": "what the snapshot does"}
  ],
  "suggestions": ["optional, non-blocking"]
}
```

One `baselines` entry per baseline named above. `clean` means no findings and every
baseline passed; `blocked` means a baseline could not run. Use `[]` for no findings.
