---
name: aw-feature
description: Guide a new feature or app from an idea through one-question-at-a-time discovery to a PRD, domain language, product roadmap and milestone documents. Planning only.
---

# Feature planning journey

Read [the shared contract](../../references/workflow.md) and
[feature planning](../../references/planning.md). Coordinate the existing
`aw-discover`, `aw-domain` and `aw-roadmap` skills directly from the project documents.
No graph or Python helper is required.
One coordinator acts as both Product Engineer and Senior Staff Engineer; do not
spawn two interviewers or ask the user to invoke each stage manually.

1. Start from the user's description. Inspect only relevant existing docs/code and
   scoped Mem0 recall. Identify the desired user outcome and the most consequential
   unknown. If a material unknown remains, ask exactly one guided question,
   recommend an answer with its tradeoff, then wait. Otherwise proceed using the
   supplied answers. Do not bundle questions or fill missing answers with guesses.
2. Record each answer and its implications in the draft documents and a short Progress section.
   Keep the current stage, pending question, accepted decisions, assumptions,
   blockers and next action. Reuse answers across product and engineering work;
   reconcile contradictions with one focused question. Continue the same interview
   across stage boundaries without requiring repeated permission already given.
3. Progress discovery -> domain -> roadmap as their material questions are settled.
   Use the existing stage skills; `aw-roadmap` must write/update milestone documents
   as well as the roadmap. Preserve existing IDs, paths, completed work and authority.
   Do not request code-level decisions for distant milestones before they matter.
4. Check the document bundle for requirement coverage, consistent domain terms,
   acyclic dependencies and observable milestone/slice acceptance. Present a short
   synthesis with links and any remaining material decision. Use established user
   answers/instructions as acceptance evidence; ask once if material acceptance is
   still missing. Do not mark unanswered assumptions accepted or loop on approval.
5. At planning done, report actual PRD/domain/roadmap/milestone paths, acceptance
   status and the first dependency-ready slice. Stop before code, feature commits,
   pushes or PRs. Later explicit implementation authorization starts/resumes a
   delivery from these accepted artifacts; do not repeat planning just to populate state.

For a paused interview, use its saved pending question rather than restart discovery.
For no Git repository, write the planning docs in the user's chosen project folder
and retain the interview progress there; do not initialize Git or a runtime just
to satisfy this skill.
