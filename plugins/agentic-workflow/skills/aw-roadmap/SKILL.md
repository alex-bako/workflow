---
name: aw-roadmap
description: Turn accepted product scope and domain language into dependency-ordered milestones of vertical tracer-bullet slices.
---

# Roadmap

Read [the shared contract](../../references/workflow.md), accepted PRD/domain
sections, and existing architecture. Reuse an existing roadmap rather than reset it.

1. Define milestones by user-observable outcomes. Each tracer bullet exercises a
   complete path through the layers it needs, including verification. Avoid
   horizontal milestones such as “all tables, then all APIs, then all UI.”
2. For each stable slice ID record: outcome, requirement/term IDs, dependencies,
   repository ownership, important contracts, acceptance examples and checks,
   exclusions, risks, and the sources to read first. Keep dependency relationships
   explicit and acyclic. Identify the earliest useful executable slice.
3. Resolve decisions that affect several slices before scheduling dependent work.
   Ask one guided question at a time if the decision needs product/domain input.
   Separate exploration spikes from shippable slices and give spikes exit evidence.
4. Distinguish shipped/current behavior from intended behavior. Keep historical
   plans labeled as historical; maintain one current execution index. Update graph
   `depends_on` edges and requirement links if `aw-context` is in use.
5. Challenge slicing and dependencies with a bounded independent perspective when
   requested/available. Do not rewrite all accepted scope during every review.

Exit: each milestone has coherent value, slices have testable acceptance, blocked
dependencies are visible, and the next slice is implementable. Produce the roadmap
and a recommended next slice. Defer code-level detail to `aw-plan`.
