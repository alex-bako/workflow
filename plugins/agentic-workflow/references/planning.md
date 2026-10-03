# Guided feature planning

`aw-feature` is the planning-only entry point in both clients. It owns the journey;
`aw-discover` still works alone for a PRD and `aw-roadmap` alone for roadmap work.
Use one conversation and one document owner combining Product Engineer judgment
(user value, usability, scope, success) with Senior Staff Engineer judgment
(contracts, dependencies, failure modes, operability and maintainability).

Planning is where the effort pays: every decision settled here is a stall the
delivery loop never hits. Spend it on behavior, boundaries and slicing, not on
code-level detail of distant work.

## Interview and progressive detail

Start with the description and relevant current evidence, then [grill](grilling.md):
rounds of the open-decision frontier, each question with a recommendation and
tradeoff. If supplied requirements already settle the decisions, proceed to the
documents. Recompute the frontier from the answers; do not walk a fixed checklist
regardless of what is already known.

Cover the actual user/problem, primary and failure scenarios, success measures,
in/out of scope, business rules/domain terms, constraints/integrations, quality
requirements and delivery priorities as relevant. Ask product questions in plain
language; translate the answers into engineering implications yourself. Verify
technical facts in scoped code/docs rather than asking the user to locate files.
A small feature needs a short interview, not every category or a platform design.

Draft documents as answers arrive. Label user decisions, sourced facts, proposed
assumptions and open decisions distinctly. Put the `Open decisions` list and next
action in the checkpoint. Mem0 remains the sole shared recall/lesson provider;
docs and checkpoints are exact task artifacts. Do not save a duplicate transcript
or invoke another interviewer/model for every answer. Use a bounded scout/researcher
only for an actual unknown; workers receive the existing compact context packet.

A draft may use provisional choices, but a material open decision blocks accepted
planning completion. Reuse explicit acceptance already present in the
conversation. At the end show the concrete bundle and the slicing review below,
and ask only for remaining material decisions and the user's confirmation;
optional details can be explicitly deferred.
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

Each acceptance line must be false before its bullet lands: not already true, not
satisfiable only by a sibling, not a restatement of the request. A wide
mechanical change (rename, signature or data migration) that cannot land as one
green vertical slice is its own first bullet, a prefactor that makes the later
bullets easy, or an expand, migrate and contract sequence of bullets.

Each card carries its decisions in its authority section: `Decisions:` items,
each with its source, and `Open decisions:` items, each with its question,
recommendation and the bullet it binds (`- Q2 (T3): ...`). Dash items, never
numbered, so they cannot be read as bullets. The tracker does not hand out the
bullets these hold ([open decisions](tracker.md#selection-rule-next)); `aw-plan ahead`
settles them with the user.

**Slicing review.** Before the roadmap is accepted, show the user each milestone's
bullets with their dependencies and ask, as one grilling round, whether the
granularity is right, whether the dependencies are right and which bullets to
merge or split.

The first slice must be small and useful. Later milestones need testable outcomes
and dependencies, not speculative file-by-file code plans. Defer concrete code
snippets and exact commands to `aw-plan`, grounded in the code when that slice is
ready. Do not label planned milestones shipped or estimate dates without evidence.
Before finishing, ensure every in-scope requirement is covered or explicitly
deferred, each referenced milestone/bullet exists, dependencies are acyclic, and
milestone exit gates cover the product success criteria. Link every output in the
handoff; a roadmap listing names alone is incomplete.

## Resumption

Keep a short Progress section in an existing planning document: accepted decisions,
remaining assumptions, the `Open decisions` list, document links and next action.
Read that and the actual documents to resume on the open frontier; do not repeat
answered questions. No Git repo,
Python helper, graph or structured evidence file is required.

Planning completion requires the agreed document bundle, an empty frontier and
the user's confirmation. Report actual paths and acceptance status, then stop before implementation.
A later implementation request reuses the bundle and the selected slice's plan.
For users retaining legacy structured state, the optional [runtime](runtime.md)
supports planning runs; its JSON artifact checks are not part of normal skill use.
