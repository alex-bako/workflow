---
name: aw-review
description: Coordinate independent code reviews, adjudicate findings, perform scoped rereviews and verify a slice without endless review loops.
---

# Review and verify

Read [the shared contract](../../references/workflow.md) and
[review protocol](../../references/review.md). Run relevant checks and coordinate
independent review in the order the task needs, using the
[delegation policy](../../references/subagents.md). Refuters inspect source without
editing it and independently rerun relevant checks; allow assigned test outputs.

Review the acceptance criteria, domain invariants, changed behavior and affected
callers on one stable snapshot. Default to one independent reviewer separate from
the builder. Add specialist or cross-provider review when risk or project policy
warrants it; preserve agreed coverage. Join required results, including failures.

Adjudicate findings before edits. Retain IDs, impact, evidence and reasons for
actionable/advisory/rejected dispositions. Ask for new evidence before reopening
an unchanged rejected finding. Never suppress a demonstrated serious issue just
because it is outside the original diff; outside the scope fence it becomes
[found work](../../references/loop.md#found-work).

Append each adjudicated round to the review ledger and run the
[review gate](../../references/review.md#review-ledger-and-gate) (`aw-arbiter`)
before any repair or further round. Its verdict binds: repair only the IDs it
lists, answer advisories in the ledger, stop, replan or ask as it says. After a
repair, rereview the changed region, affected integration paths and prior
actionable findings. Do not restart an unrelated full audit. Broaden when contracts
or risk changed. Missing output is not clean. Do not weaken acceptance to end the loop.

For final verification, check required reviews still cover the current snapshot,
all acceptance criteria are satisfied, and required checks passed. Record actual
command results in the progress note. Disclose unverified environments. Complete
only when the evidence supports acceptance; otherwise continue investigation or
repair. For UI changes perform browser/design QA from the review protocol.

When PR delivery is authorized, follow [delivery policy](../../references/delivery.md): wait for
expected remote reviews, inspect all incoming findings and checks on the latest
head, append each remote round to the same ledger and gate (stage `remote`), repair
only the IDs its verdict lists in their original bullet, and update/recheck the same
PR. PR creation, green CI alone and an empty inbox are not completion.
