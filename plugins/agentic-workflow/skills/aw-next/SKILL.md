---
name: aw-next
description: Implement the next issue from the project's board, one tracer bullet per pass, through plan, build, QA, review, pull request and policy-gated merge, then continue. Use for "implement the next issue", "do the next tracer bullet" or "work through the board".
---

# Deliver the next tracer bullet

Read [the shared contract](../../references/workflow.md), [the delivery loop](../../references/loop.md)
and [the tracker contract](../../references/tracker.md). They own the rules; this is
the order of moves. One pass = one bullet. Building a sibling bullet is a defect.

1. Locate the tracker policy: `tracker-policy.json` in the project root or the path
   the user or project instructions name. None exists: run `init` yourself ([first use](../../references/tracker.md#first-use)),
   show the user the draft path, `detected` and `missing`, and wait for their
   confirmation; no tracker write and no steward dispatch before it.
2. The plugin root is two directories above this skill's folder. Every steward brief
   carries the exact command `python3 <plugin root>/scripts/tracker.py --policy <policy>`
   with both paths absolute.
3. Steward `next`. Resume an `in_flight` bullet whose branch or plan Progress belongs
   to this session or worktree at its recorded stage; never take over another's. A
   `blocked` one resumes only when the found issue or question its Progress names is
   resolved (`show` it); steward `sync` sets it in progress. Until then, or else,
   steward `claim` the first candidate. None: stop, report reasons and drift.
4. Dispatch `aw-planner` with the work order; the plan carries the acceptance lines
   verbatim, scope fence, acceptance checks and QA baselines. Answer its question
   from the authority file or raise it as an open question; accept the plan when
   nothing material is guessed, else return it with corrections. Steward `plan`
   writes it into the bullet issue; republish after accepted changes.
5. `aw-execute`: builder briefs carry plan path, acceptance lines and the fence under
   Exclusions. Answer builder questions from the plan and authority file.
6. QA loop: `aw-qa` on a frozen snapshot; findings go to the builder; QA rechecks the
   repair. Repeat until QA reports no finding.
7. Review loop, every round: `aw-router` writes the packet, then a Claude `aw-refuter`
   and a real Codex refuter review the same snapshot and packet in parallel. Codex
   runs through the host's Codex review path or `python3 <plugin root>/scripts/run_worker.py
   --client codex --role aw-refuter`. Adjudicate with `aw-review` and append the round
   to the [review ledger](../../references/review.md#review-ledger-and-gate); then
   `aw-arbiter` gates it. Its verdict binds: `repair` IDs only go to builder, QA,
   delta packet, rereview; `stop` ends the loop with advisories answered in the
   ledger; `replan` and `ask` as the gate defines. An unavailable reviewer is
   incomplete, never a pass.
8. Commit once and open the pull request per [delivery policy](../../references/delivery.md);
   it closes the bullet, and the card too when this is its last open bullet
   ([several repositories](../../references/loop.md#several-repositories) when it
   spans them). Steward `sync`: in review.
9. PR review loop per delivery policy: each remote round enters the same ledger and
   gate (stage `remote`); repairs fold into the bullet commit and pass QA and a delta
   rereview before each push.
10. Merge only under [loop.md "Merge"](../../references/loop.md#merge); else leave the
    pull request ready and report what is missing. Steward `sync`: merged.
11. Update Progress, report the found work of this pass (filed with its rank, or
    unfiled), return
    lessons for verified Mem0 storage, close idle workers, go to step 3.

[Found work](../../references/loop.md#found-work) at any step (a flaky test, a defect
outside the fence) is reported to you, never fixed in this bullet: gather its
evidence, then steward `intake` files or extends and ranks it. Found work that stops
this bullet's checks: rank `urgent`, set the bullet blocked with a link, name the
issue in Progress, continue.
`next` hands out found issues like bullets (candidate `kind`). A policy without
`found` disables filing: record the observation and evidence in plan Progress and
report it at step 11 as unfiled found work; it is never dropped.

Stop when no candidate exists, an open question waits, or access or authority is
missing; report every in-flight bullet and the exact next action. Ask only open
questions, one with a recommendation; steward `sync` sets the bullet blocked with it.

Briefs follow [the dispatch contract](../../references/subagents.md), plus:
- `aw-product-owner`: mode; tracker command and policy path; granted write commands;
  issue number; branch and phase (claim), plan file (plan) or transition and evidence URL (sync);
  intake: observation, evidence artifact paths, found-in item, body file path.
- `aw-planner`: work order; authority-file section; worktree; plan path; absolute path
  of `skills/aw-plan/SKILL.md`; on return, the prior plan and corrections.
- `aw-qa`: snapshot (worktree, base/head or fingerprint); plan path; acceptance lines;
  fence; baselines with the project's check commands; prior QA IDs and repair diff.
- `aw-router`: bullet id; worktree; the bullet's own base and head or fingerprint;
  plan path; QA evidence; packet path; on rereview the finding ledger and repair diff.
- `aw-arbiter`: ledger path; plan path; stage (`local` or `remote`); verdict path.
