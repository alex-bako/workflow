---
name: aw-feature
description: Guide a new feature or app from an idea through a grilling interview (rounds of open decisions, each with a recommendation) to a PRD, domain language, product roadmap and milestone documents. Planning only.
---

# Feature planning journey

Read [the shared contract](../../references/workflow.md),
[feature planning](../../references/planning.md) and [grilling](../../references/grilling.md).
Coordinate the existing `aw-discover`, `aw-domain` and `aw-roadmap` skills directly
from the project documents.
No graph or Python helper is required.
One coordinator acts as both Product Engineer and Senior Staff Engineer; do not
spawn two interviewers or ask the user to invoke each stage manually.

1. Start from the user's description. Inspect relevant existing docs/code, decision
   records and scoped Mem0 recall. State the desired user outcome, then map the
   design tree of what is still undecided. Answer facts yourself; never ask the
   user what the code or docs say.
2. Grill: ask the frontier in rounds, each question with a recommendation and its
   tradeoff, and wait for the answers. Challenge terms against the domain document
   and claims against the code as they come up; send look-and-feel questions to a
   prototype or spike. Record each answer in the draft documents and in Progress:
   stage, `Open decisions`, accepted decisions with their sources, assumptions,
   blockers and next action. Continue the same interview across stage boundaries
   without asking again for permission already given.
3. Progress discovery -> domain -> roadmap as their frontiers empty. Use the
   existing stage skills; `aw-roadmap` must write/update milestone documents as
   well as the roadmap, with each card's `Decisions:` and `Open decisions:`.
   Preserve existing IDs, paths, completed work and authority. Do not grill
   code-level decisions for distant milestones before they matter. Offer a
   decision record when one qualifies.
4. Check the bundle: requirement coverage, consistent domain terms, acyclic
   dependencies, acceptance that is false before its bullet, and observable
   milestone/slice acceptance. Run the slicing review with the user as one round.
   Planning is done when the frontier is empty and the user confirms the shared
   understanding; explicit acceptance already in the conversation counts. Do not mark unanswered assumptions accepted or loop on approval.
5. At planning done, report actual PRD/domain/roadmap/milestone paths, acceptance
   status, cards still holding open decisions and the first dependency-ready
   slice. Recommend `aw-plan ahead` for the next cards before delivery starts.
   Stop before code, feature commits, pushes or PRs. Later explicit implementation
   authorization starts/resumes a delivery from these accepted artifacts; do not
   repeat planning just to populate state.

For a paused interview, resume on its saved `Open decisions` rather than restart
discovery. For no Git repository, write the planning docs in the user's chosen
project folder and retain the interview progress there; do not initialize Git or
a runtime just to satisfy this skill.
