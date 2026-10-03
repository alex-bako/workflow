---
name: aw-plan
description: Plan tracer bullets. `ahead [N]` grills the next cards' open decisions with the user before delivery reaches them; otherwise plan one bullet from its roadmap context, domain model, decision records and current code, with concrete contracts and checks that fail before the change.
---

# Slice planning

Read [the shared contract](../../references/workflow.md) and [grilling](../../references/grilling.md).
Load the roadmap index, selected slice/dependencies, relevant PRD/domain sections,
accepted decisions and the decision records whose title or summary touches the
area. Use `aw-context` to locate related sources when present, then inspect
code/callers. Inside the [delivery loop](../../references/loop.md) `aw-planner`
writes the plan and the coordinator accepts it; the skill stays valid for direct,
interactive planning.

## Ahead: settle the next cards with the user

`aw-plan ahead [N]` (default 3) moves the delivery loop's questions to now, while
the user is present. Take the next N open cards in roadmap order (`show` a card
for its bullets) and, in dependency order, map each card's design tree: behavior
its acceptance leaves open, choices shared by its bullets, domain terms, each
bullet's test seam, and acceptance that would already pass or that only a sibling
can meet. Grill all N cards together, each question labeled with its card and
bullet. Write each answer into the card's authority section as a `Decisions:`
item with its source as it settles; what stays open is an `Open decisions:` item
with its recommendation, tagged before its first colon with the bullets it holds
(`- Q2 (T3): ...`; untagged holds the card); a vague concern goes to the
milestone's risks. Offer decision records that qualify. Report each card as ready
(no open decision) or with what remains. Writes only the authority file and
decision records; without an authority file the card's issue body is its
authority, edited with the user's go-ahead (for example
`gh issue edit N --body-file F`). No plans and no other tracker writes: moving a card to ready
stays with the user or a granted steward `set`.

## One bullet

1. Verify the slice dependencies and actual implementation state. Identify seams,
   existing helpers, contracts and tests to reuse. Do not plan against historical
   documents when current execution authority has superseded them. The card's
   `Decisions:` items are settled; an `Open decisions:` item that binds this bullet
   is an open decision now. A plan that would contradict a decision record raises
   an open decision citing it; it never overrides the record.
2. Write one plan: objective and exclusions; **Decisions**: each material decision
   the plan rests on that the acceptance lines do not state, with its source
   (authority line, record, user answer, `file:line`, or for a non-material choice
   a coordinator call with its reason) or `OPEN` with a recommendation and why authority and code do not
   settle it; the acceptance mapping as a table, acceptance line (verbatim) | test
   seam | check | why it fails at the base commit (`cannot be red: <reason>` for a
   documentation, performance or visual line, which then names its QA baseline);
   test seams, existing and highest first, ideally one; affected files and
   interfaces; implementation order, starting with a prefactor inside the fence
   when it makes the change easy; failure/security behavior; migration and
   rollback when relevant; risks; a scope fence naming this bullet's behavior and
   files and each sibling bullet out of scope. A bullet that cannot meet its
   acceptance without a sibling's deliverable is a planning defect
   ([scope fence](../../references/loop.md#scope-fence)).
3. Include concrete snippets for important interfaces, invariants, state changes,
   or difficult test cases. Label illustrative snippets; verify names/signatures
   against current code. Do not duplicate every implementation line in the plan.
4. Define worker-sized tasks only where they can be independently owned. Specify
   dependencies, allowed edit scope, required context and expected evidence.
   Keep tightly coupled changes together; parallelism is optional.
5. Choose required checks and reviewer perspectives for the risk. Take each role's
   tier from the [delegation policy](../../references/subagents.md#model-tiers),
   checking actual availability; record role/tier/effort, scope, budget and
   substitutions. Keep architecture judgment with the coordinator. Record review
   policy before coding.
6. Open decisions. Interactive: grill them in rounds and confirm the test seam
   with the user when more than one fits. Delegated: return every `OPEN` decision
   whose prerequisites are settled, each with its recommendation, and still write
   the plan with the steps that depend on them marked provisional. If a domain
   ambiguity changes behavior, revisit `aw-domain` and downstream acceptance
   rather than burying a product decision in a code snippet.

Exit: no `OPEN` decision remains and every acceptance line has a check that fails
before the change, so the slice can be implemented without guessing material
behavior. Output the plan path, acceptance mapping, required checks/reviewers and
next action. Planning alone does not authorize implementation.
