---
name: aw-review
description: Coordinate independent code reviews, adjudicate findings, perform scoped rereviews and verify a slice without endless review loops.
---

# Review and verify

Read [the shared contract](../../references/workflow.md) and
[review protocol](../../references/review.md). In `verify`, run final required
checks; in `review`, coordinate independent `aw-refuter` agents using the
[delegation policy](../../references/subagents.md). Refuters inspect source without
editing it and independently rerun relevant checks; allow assigned test outputs.

Review the acceptance criteria, domain invariants, changed behavior and affected
callers on one frozen snapshot. The default perspectives are a specialized host
reviewer and a real cross-model reviewer. Scope specialists to the risk; do not
automatically launch a panel. Join every required result, including failures.

Adjudicate findings before edits. Retain IDs, impact, evidence and reasons for
actionable/advisory/rejected dispositions. Ask for new evidence before reopening
an unchanged rejected finding. Never suppress a demonstrated serious issue just
because it is outside the original diff.

After a repair, rereview the changed region, affected integration paths and prior
actionable findings. Do not restart an unrelated full audit. Broaden when contracts
or risk changed. Count incomplete reviewer retries; missing output is not clean.
Use the run's repair/attempt limits and stop for diagnosis when exhausted.

For final verification, check required reviews still cover the current snapshot,
all acceptance criteria are satisfied, and required checks passed. Record actual
command results. Disclose unverified environments. Route to ready only when
all required evidence is complete; otherwise repair or escalate.

At `pr_review`, follow [delivery policy](../../references/delivery.md): wait for
expected remote reviews, inspect all incoming findings and checks on the latest
head, repair valid findings in their original bullet, and update/recheck the same
PR. PR creation, green CI alone and an empty inbox are not completion.
