---
name: aw-discover
description: Develop a feature or app idea into a PRD through a grilling interview of product and engineering decisions.
---

# Discover

Read [the shared contract](../../references/workflow.md) and
[grilling](../../references/grilling.md). Act as Product Engineer
and Senior Staff Engineer together. For an idea-to-roadmap/milestone request,
coordinate through `aw-feature` and the shared planning documents; a standalone PRD request
still ends at this stage.

1. Start from the user's description and existing product/docs/code. Summarize the
   problem, intended user, desired outcome, and assumptions in a short draft.
2. Grill the frontier in rounds. Cover actual user scenarios, current
   alternatives, success measures, scope/non-goals, constraints, risky
   integrations, and failure behavior as relevant. Recommend an answer and
   explain its tradeoff for each question. Do not turn a simple feature into a full business plan.
3. Maintain a single PRD with stable requirement IDs. Include problem, users,
   primary flows, requirements and observable acceptance criteria, non-goals,
   constraints, risks, explicit assumptions, and unresolved decisions. Distinguish
   must-have behavior from suggestions. Keep detailed examples in linked sections.
4. Use one lead document owner. When a second perspective is requested/available,
   ask for a bounded challenge of assumptions and missing scenarios; reconcile
   findings into the same draft, not a second competing PRD. Do not invent a
   second model's review.
5. Record terminology ambiguities for `aw-domain`. Discovery and domain modeling
   can revisit each other. Finish when the frontier is empty: scope and observable
   success are coherent, remaining questions are explicitly non-blocking or
   deferred by the user, and the user confirms.

Output the PRD path, its acceptance status, and the next material question or
handoff. For an active graph, use outcome `complete` only with established scope
acceptance and artifact evidence. Stop at the requested stage unless a broader
workflow is already authorized.
