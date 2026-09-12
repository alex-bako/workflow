---
name: aw-discover
description: Develop a feature or app idea into a PRD through guided product and engineering questions, one at a time.
---

# Discover

Read [the shared contract](../../references/workflow.md). Act as Product Engineer
and Senior Staff Engineer together. For an idea-to-roadmap/milestone request,
coordinate through `aw-feature` and its planning graph; a standalone PRD request
still ends at this stage.

1. Start from the user's description and existing product/docs/code. Summarize the
   problem, intended user, desired outcome, and assumptions in a short draft.
2. Ask the highest-impact unresolved question, one at a time. Cover actual user
   scenarios, current alternatives, success measures, scope/non-goals, constraints,
   risky integrations, and failure behavior as relevant. Recommend an answer and
   explain its tradeoff. Do not turn a simple feature into a full business plan.
3. Maintain a single PRD with stable requirement IDs. Include problem, users,
   primary flows, requirements and observable acceptance criteria, non-goals,
   constraints, risks, explicit assumptions, and unresolved decisions. Distinguish
   must-have behavior from suggestions. Keep detailed examples in linked sections.
4. Use one lead document owner. When a second perspective is requested/available,
   ask for a bounded challenge of assumptions and missing scenarios; reconcile
   findings into the same draft, not a second competing PRD. Do not invent a
   second model's review.
5. Record terminology ambiguities for `aw-domain`. Discovery and domain modeling
   can revisit each other. Finish when scope and observable success are coherent,
   and unresolved questions are explicitly non-blocking or deferred by the user.

Output the PRD path, its acceptance status, and the next material question or
handoff. For an active graph, use outcome `complete` only with established scope
acceptance and artifact evidence. Stop at the requested stage unless a broader
workflow is already authorized.
