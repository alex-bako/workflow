# Optional legacy runtime

Normal skill use needs none of these commands or JSON records. Use plans and a
Progress section as described in [workflow.md](workflow.md). This helper remains
for existing structured runs and explicit opt-in use. It validates recorded
evidence; it does not control the host agent or schedule work.

Requirements: Python 3.10+, Git, macOS or Linux. No pip packages, model APIs,
background hooks or network calls. Find the plugin root from the loaded SKILL.md;
run the helper by absolute path while targeting the user's project explicitly.

```sh
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project init feature-name --slice M1.T1 --delivery pull-request
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project status feature-name
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project snapshot
```

`status` returns node, skill, role, allowed outcomes, revision, current snapshot,
changed-work flag, last event and the complete state file path. Load that state
file when you need older findings or handoff notes. `list` locates existing runs.
Use `--delivery pull-request` only when PR delivery is authorized; default `local`
stops after local acceptance.
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
  "summary":"Required independent review completed and findings were adjudicated.",
  "reviews":[
    {"reviewer":"independent","status":"complete","fingerprint":"SNAPSHOT_VALUE","evidence":"/path/to/review-result.json","findings":[]}
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
check coverage and allowed outcomes. It does not run commands, attest
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
invalidates clean-review coverage and routes frozen review/verify/ready/pr_review/done nodes back
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

## Recovery and extending the optional graph

Repair and review counters are telemetry only. There is no attempt cap or automatic
escalation, including for old saved graphs containing `max_repairs` or
`max_review_attempts`; those fields are ignored. No budget extension is required.
A run previously at `escalate` can record its diagnosis with `replan` and continue.
Counters, findings and review requirements remain intact. Alternatively carry the
state into the normal progress-note workflow without deleting the original record.
The coordinator changes strategy when attempts stop producing new evidence.

New development runs start at `plan`; reuse the existing accepted slice document.
They default to one `independent` reviewer. Saved/custom reviewer requirements are
preserved. Planning-only runs still stop before implementation.

For project-specific nodes or reviewers, copy `graphs/development.json` into the
project, edit explicit edges/skill/role/gate, then initialize with `--graph PATH`.
Available gates are artifacts, review, tests, decision, next, delivery and
pull_request. Preserve the
standard plan/review/repair/verify/done semantics; custom nodes normally
use the artifact gate. Keep required reviewers explicit and add a behavioral test
for any new route. Graph extensions cannot grant tool or external-action authority.

## Delivery and remote review evidence

Follow [delivery policy](delivery.md) for Git ownership, waiting and adjudication.
`verify pass` now returns `ready`. Local-only scope uses `finish`; a milestone may
use `next` before publishing. PR scope cannot use `finish`. After actual publishing
or updating the same PR, `ready published` records:

```json
{
  "summary": "Verified bullet commits published; remote reviews pending.",
  "pull_request": {
    "url": "https://github.com/OWNER/REPO/pull/NUMBER",
    "head": "CURRENT_COMMIT_SHA",
    "reviewers": ["configured-review-bot"],
    "checks": ["required-ci-job"]
  }
}
```

Use actual reviewer/check identities, not the example names. Reviewers cannot be
empty; checks may be empty only when project policy actually requires none.
The helper requires a clean worktree and matching local HEAD. The host verifies
the remote head and policy; the helper makes no network calls. Publication records
preserve reviewer/check requirements across repairs and allow newly required
reviewers/checks to be added. Reducing the recorded coverage is rejected.

At `pr_review`, use `pending` with `head`, fetched-output `evidence` and
`next_action`; a pending state never means completion. Unchanged polls need no
new event. `incomplete` records failed review retrieval/execution, consumes a
review attempt for telemetry; recovery remains coordinator-owned. `fix` also needs the normal actionable `findings`
list; include the owning bullet and original remote IDs in each finding/reason.
Repair follows the existing local graph, then publish the new head and wait again.

`pr_review clean` requires:

```json
{
  "summary": "All expected remote reviews and latest-head checks completed.",
  "head": "CURRENT_COMMIT_SHA",
  "evidence": "/path/to/final-paginated-inbox.json",
  "inbox_complete": true,
  "pending_reviews": [],
  "reviews": [{
    "reviewer": "configured-review-bot", "status": "complete",
    "fingerprint": "CURRENT_SNAPSHOT_VALUE",
    "evidence": "/path/to/actual-remote-review.json", "findings": []
  }],
  "checks": [{
    "name": "required-ci-job", "status": "success",
    "head": "CURRENT_COMMIT_SHA", "evidence": "/path/to/ci-result.json"
  }]
}
```

Include every incoming reviewer/finding, not just expected reviewers; adjudicate
with the normal ledger rules. Required checks must pass, and listed extra checks
must also be successful. A skipped/cancelled required job needs investigation,
not an invented success. Latest-head association and full inbox coverage are host
attestations backed by fetched outputs. The helper validates their structure,
expected coverage and snapshot; it cannot prove a remote review was fetched.

To migrate a compatible old saved graph without resetting the run:

```sh
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project upgrade-delivery feature-name --revision REVISION --evidence /path/to/migration.json
```

Evidence: `{"delivery":"pull-request","next_action":"Record existing PR and wait for its reviews"}`.
Recover changed work first. This adds delivery nodes, redirects verification to
ready, and moves old done to ready while preserving history, counters and findings.
It refuses graphs already migrated or with incompatible delivery edges. Inspect
custom graph semantics before any manual migration. Existing PR operations remain
subject to the same authorization as before the upgrade.

## Planning-only runs

For explicit structured planning, use `--graph /path/to/plugin/graphs/planning.json`
with local delivery. Normal `aw-feature` use needs no graph.
It reuses the existing interview and document skills; `done` has no implementation
edge. See [planning protocol and artifact evidence](planning.md). The helper
requires `artifact_roles` coverage for configured `required_artifact_roles` at
artifact gates. Paths must also appear in `artifacts` and resolve to project files.
This enforces output presence, not content quality or acceptance authenticity.

Planning recovery uses its declared `recovery_node` (`roadmap`) instead of the
development review node. Existing development graphs retain their review recovery.
A graph without review gates can omit reviewers using an empty list; development
review gates still require reviewer identities. Saved planning and development
runs stay separate; starting implementation needs its own authorized scope.
