# Review protocol

## Inputs to each independent reviewer

- Slice objective, acceptance criteria, domain terms/invariants, explicit exclusions.
- Repository/worktree and immutable base/head or working-tree fingerprint.
- Changed files, relevant callers/contracts and instructions to inspect.
- Evidence of checks already performed, with honest limitations.
- Initial broad slice review or scoped rereview; for rereview include prior IDs,
  dispositions, repairs and affected integration paths.

Require no source edits, no recursive reviewers, concrete impact and source
locations. Use `aw-refuter` from [focused delegation](subagents.md), including its
Caveman/Ponytail contract. Independently inspect the diff and rerun relevant
checks; builder reports alone cannot establish verification. Allow only assigned
test/evidence outputs. Parallel checks need isolated output paths or sequential
execution if they share caches/databases. Distinguish observed facts from assumptions
and return explicit completion status. “I would run…” is not a passed check.

Default to one native independent reviewer separate from the builder. Add a
specialist or cross-provider reviewer when risk or project policy requires it.
For a specialist, select expertise
based on actual risk (for example authorization/SQL, Rust ownership or UI behavior).
For `cross-model` from Codex, invoke real Claude Code with `claude -p`; from Claude,
use an available real Codex review path. If unavailable, record incomplete and
explain the missing capability. Never replace independent review with a fictional
persona while preserving its claimed identity.

The following launcher is optional for isolated cross-model reviews. Normally
dispatch through the host directly with the required tools. For the launcher, write the bounded brief and its `Memory status:`
field first. Use the isolated worker launcher (Opus for the Claude refuter):

```sh
python3 /path/to/plugin/scripts/run_worker.py --client claude --role aw-refuter \
  --project /path/to/worktree --brief /path/to/review-brief.txt \
  --output /path/to/new-review-output.json
```

From Claude, select `--client codex` for the real Codex refuter. The coordinator
has already retrieved Mem0 context; the child needs no memory-server tools.
Native profiles remain available in already minimal sessions, with the isolation
limits described in [memory.md](memory.md). Bash permits actual checks; it is
not a read-only sandbox. The brief forbids source edits and Git mutations. Inherit
host permissions, never broaden them for tests; unavailable checks are incomplete.
Check the actual environment's hooks, MCP and plugins before treating the invocation
as isolated. Do not disable
the user's configuration globally. CLI output JSON is an envelope: inspect errors,
termination reason and the returned review text/structured result. A zero shell
exit alone is insufficient. Save raw output. No permissions bypass flags.

The brief asks for `status` (complete/incomplete), `scope`, and `findings`: each
finding has stable ID, severity, file/line, concrete impact, evidence and suggested
fix. Enforce the chosen scope while allowing serious newly discovered issues.
The coordinator adds adjudication; do not ask a reviewer to accept its own output
as authoritative. Keep the full ledger in checkpoint evidence or linked artifacts.

## Adjudication and convergence

Actionable: demonstrated correctness, security, data integrity, or accepted
requirement violation. Advisory: useful improvement without such a violation.
Rejected: invalid, already covered, unsupported, or outside accepted scope without
demonstrated serious impact. Explain the classification with evidence. Severity
alone does not settle validity, and stylistic preferences do not automatically block.

Fix root causes, preserve IDs across rereviews, and include resolution evidence.
Do not silently drop an earlier unresolved finding. Reopen an unchanged rejected
finding only on new evidence. After fixes, review affected contracts/callers and
the repair; avoid fresh audits of untouched areas. A changed base, policy, contract,
or important integration may require broader review. Required coverage must hold
on the final snapshot, even when evidence is carried forward with a reasoned
scope assessment. Do not simply replace an old fingerprint with a new one.

The coordinator owns convergence without a fixed attempt cap. Diagnose repeated
findings, reviewer disagreement, missing tests or a design defect; change strategy
and record new evidence instead of repeating an unchanged review. Reassign a stuck
worker or use targeted diagnosis. Ask the user only when their judgment, authority
or access is necessary. Keep optional refactorings outside the repair scope.

## Final verification

Run all planned required checks on the final snapshot. Also inspect acceptance
examples, terminology/invariants and changed interfaces. Check integration effects
across completed slices when finishing a milestone. Reuse CI/local evidence only
when code, environment and command scope still match. Do not duplicate a broad
local and CI model review automatically when both would examine the same inputs.

For commit ownership and post-publication feedback, follow [delivery policy](delivery.md).
PR delivery remains active through required remote review completion. Preserve
finding IDs and resolution evidence across local and remote feedback.

## Browser and design QA

For UI work, a verifier separate from the builder opens the preview of the reviewed
version using available browser tools (native, CLI or MCP). The optional isolated
worker launcher does not supply browser MCP tools; choose a capable native worker
or shell-driven browser tooling rather than silently skipping QA.

Use the approved design/reference and acceptance criteria: routes, viewports,
important interaction states and test data. Exercise controls and error paths;
check layout, typography, content, overflow, keyboard access and relevant console/
network failures. Save screenshots and expected/actual findings tied to criteria
and the tested version. Recheck affected behavior after fixes.

A screenshot baseline detects changes; it does not prove a new design is correct.
Compare with the approved artifact before accepting a new baseline. Do not weaken
assertions or refresh baselines merely to make failures disappear. If design intent
is materially missing, identify the precise decision needed; unavailable browser
verification remains unverified, never an invented pass.
