# Shared operating contract

Read this once per session when using an `aw-*` skill. Resolve all links relative
to the loaded skill file; the plugin root is two directories above its folder.
Never write project artifacts into the installed plugin/cache.

## Authority and scope

Use the user's current instructions and existing authorization. Inspect project
instructions and reuse its document paths. Accepted requirements and decisions
govern intended behavior; code/tests establish observed behavior. Record a
conflict instead of silently treating either as the other. Memories and graph
edges are pointers with provenance, not new authority.

Use product-engineering judgment (value, usability, scope) and principal-engineering
judgment (contracts, failure modes, maintainability) together. Ask one material
question at a time, with a recommendation and tradeoff. Inspect available evidence
before asking. Record stated answers separately from assumptions. Reuse prior
answers; an existing instruction to proceed is sufficient. Missing optional
preferences do not block unrelated work. Drafts remain drafts until the user's
instructions/answers establish acceptance; do not invent approval.

## Artifacts and context

Prefer existing files. Otherwise use:
- `docs/product/PRD.md`: product problem, scope, acceptance and assumptions.
- `docs/domain/DOMAIN.md`: ubiquitous language, scenarios, invariants, boundaries.
- `docs/roadmap/ROADMAP.md`: milestone/slice index and dependencies.
- `docs/plans/<slice>.md`: next-slice implementation plan.
- `docs/workflow/knowledge.json`: optional curated relationship index.
- `docs/workflow/project.md`: only project-specific paths, checks, roles or policy overrides.

Read the index and selected slice, then relevant sections and symbols. Do not load
all plans or a full PRD into every worker. Use graph context to locate sources,
then inspect those sources. Maintain mandatory coverage even when graph context
is incomplete. Use accepted domain terms in questions, artifacts, code and tests.
Flag substantive terminology drift; avoid cosmetic rename campaigns.

## Execution graph

For a multi-stage or resumable request, use `scripts/workflow.py` as described in
[runtime.md](runtime.md). The graph returns a skill and role; the host executes
that step, gathers evidence, and records an allowed outcome. It is a local routing
and checkpoint helper, not a daemon or model scheduler. Individual skills can
also run standalone without initializing a graph. A standalone stage does not
authorize implementation or any later stage.

The default lifecycle is discovery → domain → roadmap → plan → execute → review
→ verify → done, with repair, replan and escalation edges. Reviewers may run
concurrently on one frozen snapshot; join all required results before advancing.
Independent slices use separate task IDs and worktrees. Advance to the next slice
only when dependencies are complete. A node is a unit of work, not a requirement
to launch another agent. The same coordinator can perform lightweight nodes.

The coordinator is the only checkpoint writer. Before delegation read
[focused delegation](subagents.md): use its explicit scout/researcher/builder/
refuter/debugger models, bounded brief, Caveman/Ponytail worker contract and
two-worker default. Workers return results/artifact paths and never advance the
graph. Keep product/architecture judgment with the coordinator; use fresh focused
contexts for workers. If independent review is required but unavailable, mark it
incomplete rather than impersonating another model.

## Memory and resumption

Save a checkpoint at stage boundaries, review adjudication, and handoff. Include
the next action, outstanding findings and references; retain the worktree and any
uncommitted files. The helper detects changed work but does not back it up or
restore processes. On another machine transfer the actual Git state, working
files, and run records through an authorized mechanism before resuming.

Follow [Mem0-only memory](memory.md). The coordinator retrieves relevant Mem0
facts once and supplies a bounded packet to each worker. Mem0 is the sole recall
and durable-lesson provider; do not read/write Obsidian or another memory backend.
Verify writes and cross-client namespace alignment. If unavailable, report the
error and use explicit project artifacts for authorized work; never silently
substitute another provider or claim persistence. Keep exact execution state in
the existing checkpoints.

## Completion

Complete a slice only when acceptance criteria, required tests and required
independent review cover the final code snapshot, with no unresolved actionable
findings. An unavailable tool, budget cap, timeout or parse error is incomplete.
The repair limit triggers diagnosis, never success. Keep advisories/rejections
with reasons so they are not rediscovered without new evidence.

Ready-for-PR is distinct from merged/deployed. Create a PR when within the user's
requested scope; reuse an existing PR rather than duplicating it. Do not assume
authorization to merge, publish, deploy, or message others from a plan/review task.
