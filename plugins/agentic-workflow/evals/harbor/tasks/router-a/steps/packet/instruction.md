You are dispatched as the worker described in `/opt/aw/agents/aw-router.md`. Read
that file and follow it exactly. It belongs to the plugin bundle at `/opt/aw`
(`references/`, `skills/`, `scripts/`); read from it only what that file and this
brief need. No coordinator context packet or memory is provided for this dispatch.

Brief:

Write the review packet for bullet T1. Worktree `/app`, base `base` (tag), head
`HEAD` of `main`; name both by commit SHA. Plan `docs/plans/T1.md`. QA evidence:
`node --test` on head, all pass. Packet path `/app/review-packet.md`.

Output contract. The only file you may write is `/app/review-packet.md`. Use the
section names from your role file as headings.
