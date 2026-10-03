# Shared operating contract

Read once per session when using an `aw-*` skill. Resolve links relative to the
loaded skill; the plugin root is two directories above its folder. Never write
project artifacts into the installed plugin/cache.

## Authority and scope

Use the user's current instructions and existing authorization. Inspect project
instructions and reuse its document paths. Accepted requirements govern intended
behavior; code/tests establish observed behavior. Record conflicts. Memories and
old checkpoints provide context, not new authority. Never invent approval.

Act as Product Engineer and Senior Staff Engineer together. Ask material
questions by [grilling](grilling.md): rounds of the open-decision frontier, each
question with a recommendation and tradeoff. Inspect evidence before asking. Reuse prior answers and distinguish decisions from assumptions. Optional
preferences do not block unrelated work. Planning alone does not authorize code,
publication, merge, deployment or external messages.

## Artifacts and context

Prefer existing files. Otherwise use:
- `docs/product/PRD.md`: product problem, scope, acceptance and assumptions.
- `docs/domain/DOMAIN.md`: terms, scenarios, invariants and boundaries.
- `docs/roadmap/ROADMAP.md`: milestone/slice index and dependencies.
- `docs/roadmap/milestones/<milestone-id>.md`: milestones and vertical bullets.
- `docs/plans/<slice>.md`: implementation plan and a short Progress section.
- Decision records where the project keeps them, else `docs/adr/NNNN-slug.md`
  ([when to write one](grilling.md#recording)).

Read the selected slice and relevant sources, not every document. Use accepted
domain terms; flag substantive drift without cosmetic rename campaigns. Existing
relationship indexes may locate sources but are optional and not authoritative.

## Coordinator-led delivery

These skills run directly in the host agent. No Python helper, graph initialization,
JSON evidence, worker launcher or setup command is required. Use the accepted plan,
actual code and its Progress section as the working state. If no suitable document
exists, keep one task note in the project's usual location. Record scope/authority,
worktree and revision, completed work, actual check results, outstanding findings,
active agent/PR IDs and the next action. Update at meaningful handoffs or
interruptions, not after every tool call.

For planning use `aw-feature` and [planning guidance](planning.md), with one human
conversation. Planning ends with documents. For delivery start from the approved
slice instead of repeating discovery. Choose implementation, investigation, review
and QA in the order the work needs. Skills are tools, not mandatory sequential
gates. Run checks early; reuse evidence while code, environment and scope still match.

Recovery belongs to the coordinator. There is no fixed repair/review-attempt cap
and no user escalation because a counter expired, except that the
[review gate](review.md#review-ledger-and-gate) bounds review rounds. Diagnose
repeated failures, reproduce disputed findings, change the approach, split work or
reassign it. Record what was learned and why the next attempt differs. Do not
repeat an unchanged failing action. For temporary limits checkpoint and resume when
available. Ask the user only when progress needs their product judgment, authority
or unavailable access. Preserve acceptance criteria while adapting the technical
approach.

Before delegation read [focused delegation](subagents.md). Native workers are the
normal path; handle small work directly. Keep one owner per edited file and one
coordinator for progress notes. Reviewers inspect a stable snapshot independently
from its builder. One independent reviewer is the default; add perspectives for
actual risk or project policy. Preserve already agreed requirements. Do not
impersonate an unavailable reviewer or claim unperformed checks.

Scripts and graphs remain optional compatibility utilities. Read [runtime.md](runtime.md)
only for existing runs or when structured tracking is explicitly desired. Old state
files can instead be read directly and carried into the progress note: preserve
findings, scope, evidence and pending operations, mark the note as the current
handoff, and leave original records intact. Do not maintain competing state stores.

## Memory and resumption

Preserve actual worktrees and files. Inspect changes against the recorded revision;
a note does not back up work or restore running processes. Resolve pending operation
IDs before retrying mutations. Transfer actual work only through authorized means.

Follow [Mem0-only memory](memory.md). Retrieve relevant facts once and supply compact
worker context. Mem0 is the sole shared recall/lesson provider; project plans and
progress notes hold exact task state. If unavailable, report the error and continue
from sufficient project evidence. Do not substitute another memory provider or
claim persistence without verification.

## Completion

Finish only when acceptance, required checks and independent review cover the
final code, with no unresolved actionable findings. A timeout, missing tool or
incomplete reviewer output is not success. Keep finding IDs and adjudication reasons;
reopen rejected findings only with new evidence. Changed code invalidates affected
coverage. For UI changes use [browser/design QA](review.md#browser-and-design-qa).

Read [delivery policy](delivery.md) before Git publication. When PR delivery is
authorized, create/reuse the PR, address incoming actionable findings and verify
required reviews/checks on the latest head. Do not infer merge/deploy authority.
The single merge exception is a project tracker policy with `merge.allowed`, under
[the loop's merge conditions](loop.md#merge).
