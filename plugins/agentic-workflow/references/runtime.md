# Local runtime

Requirements: Python 3.10+, Git, macOS or Linux. No pip packages, model APIs,
background hooks or network calls. Find the plugin root from the loaded SKILL.md;
run the helper by absolute path while targeting the user's project explicitly.

```sh
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project init feature-name --slice M1.T1
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project status feature-name
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project snapshot
```

`status` returns node, skill, role, allowed outcomes, revision, current snapshot,
changed-work flag, last event and the complete state file path. Load that state
file when you need older findings or handoff notes. `list` locates existing runs.
The state stores a copy of the orchestration graph; plugin upgrades do not silently
change an active run. Separate worktrees share the run directory but each task
is bound to one worktree. Use a unique task ID per independently running slice.

## Record outcomes

Prepare evidence as JSON outside tracked work (the run directory is convenient).
Use an exact revision from status; a stale writer is rejected. The coordinator
alone writes checkpoints. Worker results are inputs, not permission to advance.

```sh
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project advance feature-name complete --revision 0 --evidence /path/to/evidence.json
```

For discovery/domain/roadmap/execute/repair:

```json
{"summary":"Recorded the agreed scope and remaining assumptions.","artifacts":["docs/product/PRD.md"],"next_action":"Define domain terms from the primary scenario."}
```

Artifact paths must resolve to real files inside the project. Existing files are
valid evidence only after the agent verifies they satisfy the stage. At `plan`,
also include `required_checks`, a nonempty list of exact commands agreed in the
plan (for example `["npm test", "npm run typecheck"]`). Final verification must
cover every command in that list. Use the project's real commands, not these
examples indiscriminately. Documentation-only work can name its real validation
command; do not invent a passing test to bypass a gate.

Review outcome `clean` requires:

```json
{
  "summary":"Both required reviewers completed and findings were adjudicated.",
  "reviews":[
    {"reviewer":"specialist","status":"complete","fingerprint":"SNAPSHOT_VALUE","evidence":"/path/to/specialist-result.json","findings":[]},
    {"reviewer":"cross-model","status":"complete","fingerprint":"SNAPSHOT_VALUE","evidence":"/path/to/claude-result.json","findings":[]}
  ]
}
```

Each nonempty finding needs `id`, `disposition` and `reason`. Clean accepts
`resolved`, `advisory`, or `rejected`. Keep previous actionable findings represented
with their resolution evidence. Earlier actionable IDs cannot disappear from a
clean result without explicit adjudication. Unresolved findings route `fix` with
`findings: [{"id":"R1","disposition":"actionable","reason":"Concrete impact and evidence"}]`
in evidence. The run retains this ledger across repairs and replans; a new slice
starts a fresh ledger. Missing/failed reviewer output routes `incomplete`; store why
and which reviewer needs retry. Do not rerun already-current reviewers unnecessarily.

`verify` outcome `pass` requires the latest clean review snapshot, acceptance
completion, and every planned required check:

```json
{
  "summary":"Slice acceptance and required checks passed.",
  "acceptance_complete":true,
  "checks":[{"command":"npm test","exit_code":0,"fingerprint":"SNAPSHOT_VALUE","evidence":"/path/to/test-output.txt"}]
}
```

The helper validates structure, matching fingerprints, reviewer coverage, planned
check coverage, allowed outcomes and budgets. It does not run commands, attest
that evidence text is truthful, or independently decide product acceptance. The
host must actually run checks and inspect reviewer outputs. Logs should live in
the run directory so writing them does not change the reviewed worktree.

## Handoff and recovery

```sh
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project note feature-name --revision 4 --evidence /path/to/handoff.json
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project recover feature-name --revision 5 --evidence /path/to/recovery.json
```

`note` requires `next_action`. Include current findings, completed work, pending
agent/process/PR identifiers and relevant artifact paths. It retains the original
snapshot, so taking a note cannot hide unexpected changes during review.

`recover` requires `next_action` and `reason`. Inspect changed work first. It
invalidates clean-review coverage and routes frozen review/verify/done nodes back
to review. It does not edit working files or reset repair/review counters.

The fingerprint covers HEAD, index entries, tracked working files (including
deletions, modes and symlinks), non-ignored untracked files, and initialized
submodule content. Ignored files, external services and runtime environment are
outside this fingerprint. Record environment/version evidence and rerun checks
when those inputs change. Treat an uninitialized submodule as missing coverage
until initialized and inspected. Pause writers while fingerprinting/reviewing;
the file hash is not a filesystem-wide atomic snapshot.

State lives under `<git-common-dir>/agentic-workflow/`, outside tracked files.
Atomic replacement, an OS lock and revision checks prevent torn writes and stale
coordinator updates. Records survive client/process restarts; Git pushes do not
transfer them. Keep the worktree and explicitly preserve/transfer uncommitted and
untracked files when moving machines. This is resumption of work, not a backup or
a promise to restore another client's hidden context or running processes.

## Budgets and extending the graph

Default: two repair rounds; four non-clean review attempts at most before
escalation. `escalate → replan` needs `summary`, `decision`, and `next_action`.
Replanning does not reset counters. Only after an explicit user-authorized budget
extension may that evidence include positive `additional_repairs` plus an
`authorization` reference. A new slice (`done → next`, with `slice`) resets counts.

For project-specific nodes or reviewers, copy `graphs/development.json` into the
project, edit explicit edges/skill/role/gate, then initialize with `--graph PATH`.
Available gates are artifacts, review, tests, decision and next. Preserve the
standard plan/review/repair/verify/escalate/done semantics; custom nodes normally
use the artifact gate. Keep required reviewers explicit and add a behavioral test
for any new route. Graph extensions cannot grant tool or external-action authority.
