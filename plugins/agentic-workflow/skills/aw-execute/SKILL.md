---
name: aw-execute
description: Implement an accepted tracer bullet or repair adjudicated findings with focused workers, tests and durable handoffs.
---

# Execute or repair

Read [the shared contract](../../references/workflow.md), selected plan and progress
note. Distinguish new implementation from repair using actual work and findings;
no graph or worker-launch script is required.

1. Inspect the actual worktree and callers before editing. Preserve existing user
   work. Implement the accepted behavior with existing patterns and domain terms.
2. Use `aw-builder` and the [delegation policy](../../references/subagents.md).
   Delegate only independent bounded tasks, with explicit edit ownership, input
   sources, acceptance criteria, and model/effort. Keep one coordinator as state
   writer. Workers are not alone: preserve others' changes and coordinate shared
   contracts. Avoid nested delegation. If tools lack subagents, work sequentially
   and disclose the limitation; do not claim independent review.
3. Implement a vertical path and meaningful behavior checks. Use a failing check
   first when practical, then the smallest correct fix. Test relevant failure and
   authorization paths. Reuse project test tooling; do not add a framework for
   this workflow. Run targeted checks while iterating and required checks before
   completion. Preserve exact commands, exit status and log paths.
4. In repair mode, act only on findings adjudicated actionable or new demonstrated
   breakage. Fix the root cause across affected callers. Keep advisory/refactoring
   work outside the repair unless necessary for correctness. Record each finding's
   disposition and evidence; do not silently drop unresolved findings.
5. Freeze edits while independent reviewers inspect a snapshot. Hand off a small
   brief: slice, accepted contracts/domain terms, base/head/snapshot, changed areas,
   tests, and known limitations. Use `aw-review`; never review your own output
   under an invented second-model identity.
6. At a boundary or interruption checkpoint next action, files, test evidence,
   outstanding findings and worker handles. Keep the worktree. A checkpoint is
   not a backup, and a past test result does not cover a new code snapshot.

Report what changed and what evidence supports it. Continue through the authorized
work; otherwise stop at the requested boundary. Return failed approaches and new
evidence to the coordinator, which owns recovery without a repair-attempt cap.

Before committing or pushing, follow [delivery policy](../../references/delivery.md).
Keep review repairs in their original tracer-bullet commit. Default to uncommitted
local review; provisional commits stay local and are amended before publication.
