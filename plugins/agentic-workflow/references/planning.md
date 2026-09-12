# Guided feature planning

`aw-feature` is the planning-only entry point in both clients. It owns the journey;
`aw-discover` still works alone for a PRD and `aw-roadmap` alone for roadmap work.
Use one conversation and one document owner combining Product Engineer judgment
(user value, usability, scope, success) with Senior Staff Engineer judgment
(contracts, dependencies, failure modes, operability and maintainability).

## Interview and progressive detail

Start with the description and relevant current evidence. When material unknowns
remain, ask one highest-impact unresolved question per turn and wait for its answer.
If supplied requirements already settle the decisions, proceed to the documents. Give two or three useful
choices when appropriate, recommend one and explain the tradeoff. A single
question must not disguise several unrelated decisions. Adapt the next question
to the answer; do not walk a fixed checklist regardless of what is already known.

Cover the actual user/problem, primary and failure scenarios, success measures,
in/out of scope, business rules/domain terms, constraints/integrations, quality
requirements and delivery priorities as relevant. Ask product questions in plain
language; translate the answers into engineering implications yourself. Verify
technical facts in scoped code/docs rather than asking the user to locate files.
A small feature needs a short interview, not every category or a platform design.

Draft documents as answers arrive. Label user decisions, sourced facts, proposed
assumptions and unresolved questions distinctly. Put a pending question and next
action in the checkpoint. Mem0 remains the sole shared recall/lesson provider;
docs and checkpoints are exact task artifacts. Do not save a duplicate transcript
or invoke another interviewer/model for every answer. Use a bounded scout/researcher
only for an actual unknown; workers receive the existing compact context packet.

A draft may use provisional choices, but material unanswered behavior blocks
accepted planning completion. Reuse explicit acceptance already present in the
conversation. At the end show the concrete bundle and ask only for a remaining
material decision/acceptance; optional unresolved details can be explicitly deferred.
Planning authorization permits writing these documents, not implementing the feature.

## Output contract

Reuse the project's layout (including combined MILESTONES files or existing card
folders); do not create a competing roadmap. For an existing app/new feature,
update scoped sections or create a linked feature document without replacing the
whole product PRD. For new layouts, use:

- `docs/product/PRD.md`: problem, users, success, flows, stable requirement IDs,
  accepted scope/non-goals, constraints, assumptions and open decisions.
- `docs/domain/DOMAIN.md`: ubiquitous language, examples/counterexamples, invariants
  and boundaries only where meanings/rules differ. Reuse these terms everywhere.
- `docs/roadmap/ROADMAP.md`: current product direction, user-value milestone order,
  stable IDs, outcome/status, dependencies, scope/requirement links and links to
  each milestone document. This is the navigation index, not a second full spec.
- `docs/roadmap/milestones/<milestone-id>.md`: one handoff document per milestone
  by default, with the minimum detail below. A project's combined milestone file
  is equivalent when every milestone has an unambiguous linked section.

Each milestone needs its user outcome and observable exit gate; scope/non-goals;
requirement/domain references; entry dependencies; risks/material decisions; and
ordered vertical tracer bullets. Each bullet has a stable ID, user scenario,
end-to-end boundary, explicit dependencies/ownership, acceptance examples and
verification approach, exclusions and first sources to inspect. Include negative,
permission and recovery behavior when relevant. Mark spikes with exit evidence.
Do not turn layers such as database/API/UI into separate delivery milestones.

The first slice must be small and useful. Later milestones need testable outcomes
and dependencies, not speculative file-by-file code plans. Defer concrete code
snippets and exact commands to `aw-plan`, grounded in the code when that slice is
ready. Do not label planned milestones shipped or estimate dates without evidence.
Before finishing, ensure every in-scope requirement is covered or explicitly
deferred, each referenced milestone/bullet exists, dependencies are acyclic, and
milestone exit gates cover the product success criteria. Link every output in the
handoff; a roadmap listing names alone is incomplete.

## Planning graph and resumption

With a Git repository, initialize one planning run using the existing helper:

```sh
python3 /path/to/plugin/scripts/workflow.py --project /path/to/project init feature-planning --graph /path/to/plugin/graphs/planning.json
```

Use the actual feature/task ID. `status`/`note`/`advance` work as documented in
runtime.md. On each user answer, keep the pending question/decisions in a `note`;
advance a stage only after its output and material decisions are ready. A genuine
conflict with no agreed path can route `blocked` to `escalate`; record the conflict
and next action. Once resolved, `replan` requires the decision and next action,
then reconciles discovery using existing answers. An ordinary unanswered interview
question stays at its current stage with a pending note; it is not escalation. Notes may
reference evolving documents; they do not hide changed work or confer acceptance.

For `complete`, use normal artifact evidence plus `artifact_roles`, mapping each
role to its artifact paths. Discovery requires `prd`; domain requires `domain`.
Roadmap requires the complete bundle, including existing unchanged sources:

```json
{
  "summary": "User decisions reconciled; milestone coverage and dependencies checked.",
  "artifacts": ["docs/product/PRD.md", "docs/domain/DOMAIN.md", "docs/roadmap/ROADMAP.md", "docs/roadmap/milestones/M1.md"],
  "artifact_roles": {
    "prd": ["docs/product/PRD.md"],
    "domain": ["docs/domain/DOMAIN.md"],
    "roadmap": ["docs/roadmap/ROADMAP.md"],
    "milestones": ["docs/roadmap/milestones/M1.md"]
  },
  "next_action": "Planning complete; await a request to plan/implement the first slice."
}
```

List all actual milestone documents; multiple roles can point to the same existing
file when the project combines them. The helper checks presence/path containment
and named role coverage; the coordinator verifies contents, traceability and actual
acceptance. File existence does not prove the interview happened or decisions were
accepted. Never substitute empty placeholder documents to pass the gate.

Planning `done` has no outgoing implementation edge. `aw-resume` must honor that
terminal state instead of launching the next slice. For changed work after planning `done`,
`recover` returns to roadmap; mid-stage recovery keeps the current stage. Revisit
domain/discovery if the change requires it.
The development graph and active development runs remain unchanged. To implement
later, reconcile these accepted artifacts with current code in a new/matching
development run, then perform the selected slice's detailed `aw-plan` stage.
