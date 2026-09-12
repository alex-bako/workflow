---
name: aw-resume
description: Resume or coordinate an existing development graph across Codex and Claude using durable run state and verified working files.
---

# Resume and coordinate

Read [the shared contract](../../references/workflow.md) and
[runtime instructions](../../references/runtime.md).

1. Locate the project and task ID. List saved runs if ambiguous; do not silently
   pick the newest unrelated task. Read status, retained notes, graph node and
   history. Verify repository/worktree, branch, code snapshot and dependencies.
2. If work differs, inspect the diff and reconcile what actually happened. Keep
   unrelated edits. Invalidate stale tests/reviews, document the new next action,
   and use the recovery command before advancing. Never reset or checkout files
   merely to make the checkpoint match. Missing worktree means restore actual
   work from an authorized backup/patch or report what is missing.
3. Resolve pending processes/agents/PR operations from actual status. Do not replay
   a mutation just because its completion message was lost. Record known external
   identifiers before retrying. A checkpoint restores workflow state, not process
   execution or another client's hidden conversation.
4. Retrieve only relevant Mem0 project memories and existing graph neighbors.
   Follow artifact authority and domain language; do not reload the entire history.
5. Execute the returned skill/role, record its outcome/evidence with the current
   revision, and inspect the next route. Continue while authorized and executable.
   Stop for a material user decision, missing capability, or escalation. Do not
   busy-loop on an unchanged node or record fabricated evidence to advance.
6. At escalation use a bounded `aw-debugger` only for hard root-cause uncertainty;
   keep routine diagnosis local. Diagnose repeated findings, inadequate tests, scope churn, or
   conflicting requirements. Propose a concrete revised plan. Replanning retains
   the repair count; starting a new slice is the only normal counter reset.

When the saved planning graph is at `done` with no outgoing edges, report the
PRD, domain vocabulary, roadmap and milestone artifacts and stop. Do not migrate
it to PR delivery or infer implementation authorization. Resume its unanswered
interview question through `aw-feature` if planning is still in progress.

At `ready`, follow [delivery policy](../../references/delivery.md): continue the
next authorized bullet, finish local-only delivery, or publish/reuse the PR and
enter `pr_review`. Never stop successfully just because a PR was created. Resume
pending reviewer/run IDs against the actual current head; repair, amend the owning
bullet and recheck the same PR until remote coverage is complete. For old saved
graphs, apply the documented compatibility protocol without resetting budgets.
At done, report verified completion and PR review/check evidence. A milestone may
continue with the next dependency-ready slice. Neither completion nor resumption
authorizes merging/deployment.
