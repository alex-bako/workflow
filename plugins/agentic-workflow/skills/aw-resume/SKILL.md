---
name: aw-resume
description: Coordinate or resume approved work from plans and actual code, owning implementation, independent verification and recovery without scripted phase gates.
---

# Coordinate delivery

Read [the shared contract](../../references/workflow.md). Work directly in the host;
no Python scripts, graph run, JSON evidence or special setup is required.

1. Locate the requested plan and its Progress section or existing handoff. Inspect
   repository/worktree, code changes and dependencies. Reuse accepted product/domain
   decisions. Start a brief progress note if absent; do not restart feature discovery.
   A planning-only request stays planning-only until implementation is authorized.
2. Reconcile recorded work with actual files, checks, agents and PR status. Preserve
   unrelated changes. Invalidate stale evidence; never reset code to match a note.
   Resolve pending operation IDs before retrying so resumption does not duplicate
   commits, PRs or other mutations. A note does not restore running processes.
3. Choose the next useful action: implement, investigate, delegate a focused task,
   review, exercise the application or repair a demonstrated defect. Use `aw-execute`
   and `aw-review` as needed, not as a compulsory sequence. Keep routine decisions
   and orchestration local; use native agents when separation or expertise helps.
4. Own recovery. For repeated failure inspect new evidence and change strategy,
   narrow the problem, reproduce it, or reassign work. Adjudicate reviewer disputes
   against accepted behavior. There is no repair-attempt ceiling or permission
   request to continue fixing. Do not rerun an unchanged failed approach. Temporary
   provider limits need a resumable note and a supported wait, not a product question.
5. Continue within existing authority. Ask the user only for a material product
   choice, additional authority, or access you cannot obtain. Do not weaken acceptance
   or review requirements to claim completion. Update progress at meaningful
   handoffs: what changed, evidence, unresolved findings and the next action.
6. Finish when the actual final version satisfies acceptance, required checks and
   independent review. For UI work include browser/design QA as described in
   [review guidance](../../references/review.md). Disclose unavailable verification.
   Follow [delivery policy](../../references/delivery.md) for authorized publication
   and incoming reviews; creating a PR alone is not verified delivery.

For legacy graph runs, read the state file directly and preserve findings, authority,
pending IDs and evidence in the progress note; mark which handoff is current. Keep
the old records intact. Use [the optional helper](../../references/runtime.md) only
if structured graph tracking is still desired. Old retry caps do not require user
approval to continue. Neither resumption nor completion authorizes merge/deploy.
