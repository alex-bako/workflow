---
name: aw-plan
description: Plan one executable tracer bullet using its roadmap context, domain model and current code, with concrete contracts and verification steps.
---

# Slice planning

Read [the shared contract](../../references/workflow.md). Load the roadmap index,
selected slice/dependencies, relevant PRD/domain sections and accepted decisions.
Use `aw-context` to locate related sources when present, then inspect code/callers.

1. Verify the slice dependencies and actual implementation state. Identify seams,
   existing helpers, contracts and tests to reuse. Do not plan against historical
   documents when current execution authority has superseded them.
2. Write one plan: objective and exclusions; acceptance mapping; affected files and
   interfaces; implementation order; failure/security behavior; tests; migration
   and rollback considerations when relevant; risks and unresolved decisions.
3. Include concrete snippets for important interfaces, invariants, state changes,
   or difficult test cases. Label illustrative snippets; verify names/signatures
   against current code. Do not duplicate every implementation line in the plan.
4. Define worker-sized tasks only where they can be independently owned. Specify
   dependencies, allowed edit scope, required context and expected evidence.
   Keep tightly coupled changes together; parallelism is optional.
5. Choose required checks and reviewer perspectives for the risk. Resolve models
   from the [delegation policy](../../references/subagents.md), checking actual
   availability; record role/model/effort, scope, budget and substitutions. Keep
   architecture judgment with the coordinator. Record review policy before coding.
6. Ask one material question at a time; proceed on already accepted instructions.
   If a domain ambiguity changes behavior, revisit `aw-domain` and downstream
   acceptance rather than burying a product decision in a code snippet.

Exit: the next slice can be implemented without guessing material behavior.
Output the plan path, acceptance mapping, required checks/reviewers and next action.
Planning alone does not authorize implementation.
