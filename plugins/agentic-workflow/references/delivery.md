# Tracer-bullet commits and PR review

Apply before committing/pushing a slice, creating a PR, or resuming PR feedback.
The coordinator owns Git mutations and remote state. Reviewers receive a frozen
working-tree fingerprint or local commit and never commit/push the builder's work.

## One coherent commit per tracer bullet

Default: implement the bullet, run its checks and independent local reviews on
uncommitted changes, adjudicate and repair, then commit the accepted result once.
A local provisional commit is also allowed when the reviewer needs a commit SHA;
keep it unpushed until the bullet's actionable local findings are addressed.

Keep the bullet ID, base SHA, provisional/final commit SHA and finding IDs in the
run notes. Every valid finding belongs to the affected original bullet, including
findings received after another bullet started or after a PR was opened. Repair
that bullet's contract/tests; do not disguise its fix as a new tracer bullet.
For a finding spanning bullets, record all affected bullets and assign the root
cause to its owning commit; verify the affected integration paths.

Amend an owned provisional tip commit. For an earlier owned bullet commit, fold
the scoped repair into that commit with a targeted rebase/autosquash; temporary
fixup commits must be folded before publishing. Preserve later bullets and
unrelated edits. Do not amend whichever commit happens to be HEAD, squash an
entire milestone, or rewrite someone else's commits. Source changes still need
the required scoped local rereviews and checks before push.

Committing/amending changes the recorded revision even when source content is
identical. Record old/new SHA and compare actual contents, modes, renames and
submodules. Update the progress note and re-establish current review and test
evidence. Only users retaining the optional graph need its `recover` command.
Carry coverage forward only with an inspected, recorded reason
that its inputs are unchanged; rerun affected checks/reviews when they changed.
Never relabel a stale fingerprint without this assessment. Commit before final
verification when using provisional commits to avoid unnecessary recovery.

For an already published, workflow-owned feature branch, fold valid PR repairs
into their original bullet commits too. Before rewriting, verify ownership,
branch policy and the exact remote tip. Publish with an explicit expected-SHA
lease; a changed remote tip requires inspection, never a blind retry or plain
force push. Shared/protected branches or someone else's commits require an
agreed compatible history strategy. Never rewrite the default branch. This
workflow authorizes no unrelated branch mutation, merge or deployment.

## Publication and review

Record the authorized delivery boundary in the plan/progress note. Local-only work
ends after local acceptance. For PR delivery, publish/reuse the PR, save its URL and
head, and continue through required remote reviews. Never recreate an existing PR.
The optional graph helper uses `ready` and `pr_review` for these states; its commands
are not required to publish or track feedback.

Before publishing, determine expected remote reviewers/bots and required check
names from project policy, PR requests and actual configured workflows. Include
an expected review even if its job has not appeared yet. Persist that coverage
with the PR URL and published head SHA. Expand coverage when policy or review
requests add reviewers/checks; retain earlier requirements. Do not remove a missing/failed
reviewer or check to make acceptance pass. Do not invent remote reviewer requirements
if project policy requires only the
already completed independent local review. An actually requested remote review
must still complete; an empty inbox alone is not evidence of that.

While awaiting remote review:

1. Fetch the current PR head, requested/submitted reviews, inline review threads,
   issue comments and check/workflow runs. Read all relevant pages and retain raw
   evidence with source IDs/URLs and head association. PR body/comments alone
   are not the complete review inbox. Inspect bot output even when its job is green.
2. Wait for each expected review to finish, including delayed jobs and requested
   humans. A missing, queued, running, failed or cancelled review is incomplete.
   Green CI is not proof review finished. A quiet inbox or elapsed timeout is not
   approval. Use explicit completion signals from the actual reviewer/run; recheck
   the inbox after completion so late comments are included.
3. Adjudicate findings with the existing review protocol. Preserve source IDs,
   bullet ownership and actionable/advisory/rejected/resolved reasons. An outdated
   or resolved GitHub thread is not proof the underlying issue was fixed. Fix
   valid findings; retain reasons for advisory/rejected ones. Do not post replies
   or resolve remote threads unless that communication is authorized.
4. Repair actionable findings, recheck affected behavior and independent coverage.
   Amend/fold into the original bullet, update the same PR, record its new head,
   and wait again for required remote coverage/checks on that head. Preserve the
   finding ledger and evidence. Broaden local coverage for cross-bullet fixes.
5. Completion is allowed only after all expected reviews completed, every incoming
   finding was adjudicated with no actionable item left, and required checks
   passed for the latest published head. Fetch head and inbox once more immediately
   before recording completion. New work/head changes invalidate old coverage;
   recover and reconcile rather than overwriting the recorded SHA.

Poll lightweight status in bounded waits (normally 30–60 seconds); fetch large
outputs only when status changes. Keep the task active while reviews run. Record
pending work when status changes, with pending IDs and next action; unchanged polls
need no new note. Failed review retrieval is incomplete, not acceptance. Diagnose
repeat failures or wait with backoff; no retry count requires user escalation.
If a host/session limit or unavailable human prevents further waiting, preserve
the PR identifiers and a resumable pending status. Use a supported durable wake-up when
available and authorized; never claim a background monitor exists when it does
not. A waiting task is unfinished, not a successful completion.

`gh pr checks --watch` watches checks only. Use the host's GitHub connector or
GitHub CLI/API for reviews, comments, paginated threads and the current head too.
Prefer concise status reads; the graph helper itself never polls GitHub, pushes,
rewrites commits or fabricates review evidence.

## Optional structured runs

Legacy runs embed their graph. Normally read the saved evidence into the current
progress note, retaining the original records. If structured tracking is desired,
do not reset an active run to obtain new edges.
For a compatible saved graph without `ready`/`pr_review`, inspect its actual PR
status and use `upgrade-delivery` with the current revision and delivery scope
(see runtime.md). It preserves history, findings and counters, routing old `done`
to `ready`. Recover unexpected working changes first, then record an existing PR
with `published`; do not create a duplicate. Custom incompatible graphs need a
reviewed migration preserving their semantics. Never treat an old local `done`
as completed PR delivery. Old attempt limits are ignored by the updated helper.
