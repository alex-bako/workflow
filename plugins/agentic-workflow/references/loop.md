# Delivery loop: one tracer bullet at a time

The `aw-next` skill runs this loop. The main session is the coordinator and acts
as staff engineer: it accepts plans, dispatches, answers workers' questions,
adjudicates findings and owns Git. Workers are the roles in [focused delegation](subagents.md).
The tracker contract is in [tracker.md](tracker.md). One pass delivers exactly one
bullet; the loop then takes the next one until a stop condition holds.

```text
pick -> plan -> publish plan -> implement -> QA loop -> review loop
     -> pull request -> PR review loop -> merge -> sync -> pick ...
```

## Authority

The user's request to deliver the next issue, together with the project's tracker
policy, authorizes: tracker writes, local implementation, commits on the bullet's
branch, publishing its pull request, replying on that pull request, and merge only
when the policy sets `merge.allowed`. Nothing here authorizes deployment, changes
to the authority file's scope, or work on another bullet.

Ask the user only for an **open question**: a decision the authority file (its
`Decisions:` items included), accepted decision records, accepted plans, project
instructions and the code do not settle. Ask every open question of the bullet
together as one [grilling](grilling.md#asking-a-round) round, numbered, each with
a recommendation; set the bullet to blocked with the round in its comment, and
wait. Never answer a decision on the user's behalf. Everything else is the
coordinator's call. Record each call and its source in the plan's Decisions. A
call that would qualify as a decision record is proposed in the stage 11 report,
not written. Questions are cheaper before the loop: `aw-plan ahead` settles a
card's decisions with the user, and the tracker does not hand out a bullet or card
held by an open decision.

## Scope fence

A pass implements one bullet and nothing else. The fence is written at planning
and enforced at every later stage.

- The plan has a **Scope fence** section: the behavior and files this bullet
  delivers, and each sibling bullet of the card named as out of scope with the
  deliverable it owns.
- A plan that cannot meet the bullet's acceptance without a sibling's deliverable
  is a planning defect. Replan: narrow to a stub or seam the bullet legitimately
  owns, or record that the bullets must be re-split. Re-splitting changes the
  authority file and is an open question for the user, not a reason to build two
  bullets.
- Builder briefs carry the fence under Exclusions. A builder that needs something
  outside it returns `blocked` with one question; it does not build it.
- QA maps every changed file and hunk to a plan step. Unmapped work is a finding:
  trim it, or replan when the plan was wrong. Extra work is not a bonus.
- Reviewers receive the fence. A finding that asks for a sibling's deliverable is
  rejected as out of scope unless it demonstrates a defect in this bullet.
- A real defect outside the fence is [found work](#found-work): filed, not fixed here.

## Stages

1. **Reconcile.** Run the steward in `next` mode. If `in_flight` holds a bullet
   whose branch or plan Progress belongs to this session or worktree, resume it at
   its recorded stage instead of picking. A blocked bullet resumes only when the
   found issue or question named in its Progress is resolved; steward `sync` then
   sets it in progress. Never take over someone else's bullet.
2. **Pick.** The same `next` result serves stages 1 and 2. Steward `claim`: for a
   new card it claims the card, creates the bullet sub-issues, then claims the
   first bullet. The work order is the hand-off to planning. No candidate: stop
   and report why (counts by reason, drift); cards skipped for `open_decisions`
   wait for `aw-plan ahead`.
3. **Plan.** The coordinator dispatches `aw-planner` with the work order; it
   writes the plan with `aw-plan` and does its own bounded lookups. The plan quotes
   the acceptance lines verbatim (it is the contract QA and reviewers read), lists
   the decisions it rests on with their sources, names the scope fence, maps every
   acceptance line to a check that fails at the base commit, and lists the QA
   baselines that apply. The coordinator answers the planner's open decisions from
   the authority file, records and code, or raises the rest as open questions.
   **Plan review**, when the bullet touches persisted data or migrations, auth or
   security, a contract across repositories or a decision record, or the plan is
   a re-plan or came back partial: one `aw-refuter` with target `plan` from the
   vendor the planner did not use (a Claude-hosted loop runs Codex through
   `run_worker.py --client codex --role aw-refuter`). The coordinator adjudicates
   its findings and returns accepted ones as corrections; at most one correction
   round, then a check of what changed. Without a trigger, record the skip in
   Progress. The coordinator accepts the plan when no `OPEN` decision remains and
   every acceptance line has a check, or returns it with corrections; there is no
   user gate unless an open question exists.
4. **Publish the plan.** Steward `plan`: the accepted plan goes into the bullet
   issue body. The plan file stays the working copy and holds Progress. Republish
   after any accepted plan change.
5. **Implement.** `aw-execute` with `aw-builder`. The brief gives the plan path,
   the fence and the acceptance lines, so the builder starts without rediscovery.
   Builders' questions come back to the coordinator, which answers from the plan
   and authority file, amends and republishes the plan, or raises an open question.
6. **QA loop.** `aw-qa` verifies a frozen snapshot against the baselines below.
   Findings go to the builder; QA rechecks what the repair touched. Repeat until QA
   reports no finding. QA never edits source.
7. **Review loop.** `aw-router` writes the review packet. A Claude `aw-refuter` and
   a Codex refuter review the same snapshot from the same packet, in parallel,
   every round. The coordinator adjudicates under the [review protocol](review.md)
   and appends the round to the review ledger. Then `aw-arbiter` runs the
   [review gate](review.md#review-ledger-and-gate) over every round so far. Only
   the findings its `repair` verdict lists return to the builder, then QA for the
   affected baselines, then one rereview from a delta packet. `stop` ends the loop;
   nitpicks are answered in the ledger, never repaired. `replan` and `ask` are
   handled as the gate defines. An unavailable reviewer is incomplete coverage,
   never a pass.
8. **Pull request.** One coherent commit for the bullet ([delivery policy](delivery.md)).
   The pull request closes the bullet issue and links the plan and evidence; for
   the card's last open bullet it also closes the card, so cards that depend on it
   unblock (`set` never closes issues).
   Steward `sync`: in review. See [several repositories](#several-repositories)
   when the bullet lands in more than one.
9. **PR review loop.** Follow the delivery policy for incoming remote reviews. Each
   remote round is adjudicated into the same ledger and passes the same gate;
   repairs fold into the bullet commit and pass QA and a delta rereview before the
   next push. The gate and the project's stopping rule decide when remote rounds end.
10. **Merge.** See below. Steward `sync`: merged; the card when its last bullet
    merged.
11. **Continue.** Update Progress, report the [found work](#found-work) of this
    pass (filed with its priority, or unfiled), return lessons for verified Mem0
    storage, close idle workers, then go to stage 1.

Stop when: no candidate exists; an open question waits for the user; required
access or authority is missing (report exactly what is needed; this is not a
question to decide). A stop is reported with the state of every
in-flight bullet and the exact next action. A pass that cannot merge leaves its
pull request ready and reports it; the loop may continue only with a bullet that
does not depend on the unmerged one.

## Found work

Work nobody planned shows up at every stage: a flaky test, a defect in a
neighboring area, a failing check unrelated to the change, a problem seen only
after merge. It is never fixed inside the current bullet and never lost.

- Anyone who sees it reports it to the coordinator with what was observed. The
  coordinator gathers the evidence the issue needs (the debugger or QA measures
  what is missing, for example how often a test fails) and dispatches the steward
  in `intake` mode. A nitpick is not found work.
- The steward checks for an existing issue, files or extends one with the
  evidence, and ranks it: `urgent`, `soon` or `later`
  ([tracker contract](tracker.md#found-issues)). The user is told at the end of
  the pass, not asked. The user reorders by changing the priority label.
- A found issue is a work item like a bullet: `next` hands it out by its rank, it
  gets a plan in its issue body, the same QA, review and merge conditions, and its
  own pull request. Its scope fence is the issue's acceptance lines.
- When found work stops the current bullet from passing its checks, rank it
  `urgent`, set the bullet blocked with a link to it, name the issue in the plan's
  Progress, and continue the loop: `next` returns the urgent issue first and the
  bullet resumes afterwards through stage 1.
- Without the policy's `found` key nothing is filed: the coordinator records the
  observation and evidence in the plan's Progress and reports it at stage 11 as
  unfiled found work.

## Several repositories

The work order names the code repositories of the card, from the policy's `repos`.
The plan states which of them this bullet changes and in what order. Find each
checkout by its remote URL and work in a worktree of that repository from its
policy base branch; never guess a path. QA, the review packet and both reviews
cover every repository the bullet changed, as one snapshot per repository.

One pull request per repository, each containing only this bullet. Every pull
request references the bullet issue by its full `owner/repo#number`; only the one
merged last carries the closing keywords (the bullet, and the card when this is
its last open bullet). Merge in dependency order (a contract
before its consumer), each under the merge conditions and with that repository's
method. The bullet is in review until the last one merges. A repository the card
does not name is outside the fence.

## QA baselines

Always, on the frozen snapshot, with evidence for each:

1. **Project checks.** The repository's own gates: tests, lint, type-check, format
   and project guard scripts, as named by the plan and project instructions.
2. **Acceptance and plan.** Every acceptance line and every plan step demonstrated
   by a command, test or observation. New behavior has a test that fails without
   the change: the builder's red evidence names it (QA reruns it green itself),
   or the plan gives a cannot-be-red reason.
3. **Scope fence.** Every changed file and hunk maps to a plan step; nothing from a
   sibling bullet; no adjacent refactor.
4. **Browser and design QA** for UI bullets, as in the [review protocol](review.md#browser-and-design-qa).

A baseline that cannot run is reported unverified with the reason. QA findings
have stable IDs, the baseline they break, location, expected and actual.

## Review packet

Reviews are slow when reviewers choose their own context. The packet chooses it.
`aw-router` reads the frozen diff and the plan and writes one file, at most 150
lines, that both reviewers receive instead of the conversation, the whole plan or
the whole branch.

- **Identity:** bullet id, worktree, base and head (the bullet's own base, not the
  default branch), or the working-tree fingerprint.
- **Contract:** acceptance lines, scope fence and invariants, each copied word for
  word with its own file and line; not paraphrased or merged, not whole documents.
- **Change map:** changed files grouped by plan step, with the hunks that carry risk.
- **Must read:** files or symbols outside the diff that the change can break
  (callers, contracts, tests), each with line range and a one-line reason.
- **Skip:** generated files, lockfiles, sibling-bullet areas, unrelated directories.
  Must read never repeats a changed file or names anything Skip names; a concern
  about a skipped file is a lens. The router checks a skipped area itself and
  states the result under Skip.
- **Lenses:** the risks present in this change (authorization, SQL, concurrency,
  UI state, migration) for reviewers to apply.
- **Evidence:** checks QA already ran on this snapshot with results, and the
  targeted commands worth rerunning.
- **Ledger:** on rereview, prior finding IDs, dispositions and the repair diff as a
  revision range or file list, not quoted.

Reviewers start from the packet and leave it only to confirm or refute a specific
suspected defect. No history, blame or earlier pull-request archaeology unless
the packet names it. A rereview covers the repair and its affected paths. A
reviewer that finds the packet missing something material says so in its report;
the coordinator corrects the packet rather than widening every review.

## Merge

Merge the bullet's pull request only when all hold on the latest published head:

- the tracker policy sets `merge.allowed`;
- every acceptance line of the bullet is demonstrated and QA is clean;
- both local reviewers completed with no actionable finding left;
- every expected remote review completed and the project's stopping rule holds;
- required checks passed;
- no open question is pending for this bullet;
- the pull request contains only this bullet.

Use the repository's merge method from the policy (`repos.known.<name>.merge`,
else `merge.method`). Fetch head, reviews and checks once more
immediately before merging. Anything missing: do not merge; leave the pull request
ready, record what is missing and report it.
