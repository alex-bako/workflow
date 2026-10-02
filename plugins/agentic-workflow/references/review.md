# Review protocol

## Inputs to each independent reviewer

- Slice objective, acceptance criteria, domain terms/invariants, explicit exclusions.
- Repository/worktree and immutable base/head or working-tree fingerprint.
- Changed files, relevant callers/contracts and instructions to inspect.
- Evidence of checks already performed, with honest limitations.
- Initial broad slice review or scoped rereview; for rereview include prior IDs,
  dispositions, repairs and affected integration paths.
- Review packet: when the delivery loop runs, reviewers start from the `aw-router`
  packet instead of the whole branch ([review packet](loop.md#review-packet)).

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
field first. Use the isolated worker launcher (the refuter's `deep` tier):

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

Keep optional refactorings outside the repair scope. Convergence is decided by the
review gate below, not by the coordinator's or a reviewer's appetite for another
round.

## Review ledger and gate

Review rounds are expensive and reviewers always find something. Only a
demonstrated violation earns a repair, and only a repair earns another round.

**Ledger.** One JSON file per work item, next to its plan (`<plan name>.review.json`).
The coordinator appends every round after adjudicating it. After a gate only a
finding's `disposition` and `answer` change; earlier rounds are never rewritten
otherwise.

```json
{"item": "S1.2.T1",
 "rounds": [{"round": 1, "stage": "local", "snapshot": "<head or fingerprint>",
   "reviewers": [{"name": "claude", "status": "complete"}, {"name": "codex", "status": "complete"}],
   "findings": [{"id": "R1-C1", "reviewer": "claude", "severity": "P1", "location": "src/a.mjs:10",
     "claim": "...", "evidence": "...", "class": "actionable",
     "disposition": "open", "answer": "", "repeats": null}]}],
 "gates": [{"after_round": 1, "verdict": "repair", "repair": ["R1-C1"], "reclassified": [],
   "repeats": [], "found_work": [], "reason": "..."}]}
```

`stage` is `local` or `remote` (pull request reviews). `class` is `actionable`,
`advisory` or `rejected` as defined above. `disposition` is `open`, `repaired`,
`answered` (one line in `answer`, no code change), `rejected`, or `filed #N` for
[found work](loop.md#found-work). `repeats` names the earlier finding it restates.

**Gate.** After each adjudicated round and before any repair or further round,
dispatch `aw-arbiter` with the ledger and the plan. It reads every round, not only
the last, and writes one verdict. The verdict binds the coordinator, which copies
it into `gates`.

1. *Reclassify.* A finding stays actionable only when its evidence demonstrates the
   violation: a failing command or reproduction, a quoted contract line (acceptance,
   invariant, scope fence) the change breaks, or wrong behavior shown at the cited
   location. Style, naming, wording, optional refactors, "could" and "consider"
   without a demonstration, and wishes for tests of untouched code are advisory
   whatever severity the reviewer or the coordinator gave them. A wish that belongs
   to a sibling bullet's deliverable is advisory or rejected; neither is
   actionable. The gate only screens out: it never raises a class.
2. *Repeats.* A finding that restates an earlier answered or rejected one without
   new evidence is rejected as a repeat. The same advisory raised by both reviewers
   is still advisory.
3. *Out of scope but real.* A demonstrated defect outside the scope fence is not
   repaired here; it becomes found work and its disposition is `filed #N`. It
   does not count as actionable for the verdict.
4. *Verdict.*
   - `stop`: the latest round has no actionable finding and no earlier actionable
     finding is still `open`. Advisory findings get a one-line answer in the
     ledger and no code change. The review loop ends.
   - `repair`: the listed actionable IDs go to the builder, and nothing else does.
     One rereview follows, from a delta packet covering that repair.
   - `replan`: the third round of the stage that still raised actionable findings.
     More rounds will not converge. The coordinator diagnoses the cause across the
     whole ledger (plan defect, design defect, missing test, reviewer disagreement),
     replans or repairs the design once, and one rereview follows.
   - `ask`: actionable findings remain after the replan's rereview. The coordinator
     asks the user one question with the ledger summarized by round.

The coordinator may contest a reclassification once per round by adding evidence
to the finding and running the gate again. It never starts a round or sends a
finding to a builder without a `repair` or `replan` verdict. Remote review rounds
enter the same ledger and pass the same gate; the round count restarts at the
pull request. A project's stricter stopping rule still applies. A reviewer that did
not complete leaves coverage incomplete whatever the verdict says.

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
