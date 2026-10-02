# Focused delegation

Coordinator owns product questions, architecture, slice contracts, dispatch,
adjudication, integration and checkpoints. The coordinating session runs on the
`coordinator` tier of [model tiers](#model-tiers). Delegate bounded work; handle
one grep or a trivial edit locally. A graph node does not imply a new agent.

## Role defaults

| Role | Tier / effort | Scope / turn budget |
| --- | --- | --- |
| aw-scout | light / low | Locate files, symbols, callers; 8 turns |
| aw-researcher | standard / medium | Verify scoped docs/source facts; 12 turns |
| aw-builder | standard / medium | Implement a clear bounded contract; 24 turns |
| aw-refuter | deep / high | Independently inspect diff and rerun relevant checks; 16 turns |
| aw-debugger | deep / high | Hard root-cause diagnosis after a reproduced failure; 16 turns |
| aw-product-owner | standard / medium | Tracker steward: one script mode, returns a work order; 12 turns |
| aw-qa | standard / medium | Verify a frozen bullet against plan and QA baselines; 20 turns |
| aw-router | standard / medium | Write the review packet for a frozen bullet; 10 turns |
| aw-arbiter | deep / high | Review gate: one verdict from the whole review ledger; 8 turns |
| aw-planner | planner / high | Write the plan for one claimed bullet; 20 turns |

## Model tiers

Roles name a tier, never a model. `models.json` in the plugin root maps each tier
to a Claude and a Codex model; it is the only place model names live.

| Tier | Used by |
| --- | --- |
| light | aw-scout |
| standard | aw-researcher, aw-builder, aw-product-owner, aw-qa, aw-router |
| deep | aw-refuter, aw-debugger, aw-arbiter; the coordinating session |
| planner | aw-planner only |

The coordinating session (dispatch, adjudication, Git, the loop) runs on the tier
`models.json` names as `coordinator` (`deep`). The `planner` tier is used by
`aw-planner` only. No role inherits the session's model. To change models, edit
`models.json` and run `python3 scripts/sync_profiles.py` from the repository root;
it stamps the native profiles, and the release check fails when they drift.

These are starting choices, not a measured cost/quality ranking. Check actual
model availability. Use the tier's explicit model and effort, never the
coordinator's. If a model is unavailable, select the smallest available suitable
one and record the substitution. After a bounded failure, narrow the contract
before escalating one tier, at most to `deep`; the `planner` tier is never an
escalation. Never weaken a required review to save tokens.

Use [Mem0-only memory](memory.md) before dispatch. Native host agents are the
default; supply the compact role brief directly, with the tools the task needs.
No Python launcher or profile installation is required. `scripts/run_worker.py`
is optional when explicit plugin/MCP isolation is desired and code tools suffice.
It must not be the default for browser QA or other tasks needing omitted tools.

Claude loads the native `agents/*.md` profiles. Codex profiles are distributed in
`codex-agents/`; `scripts/setup_agents.py` installs them into its native agents
directory. Codex plugins do not install these files automatically. If native
profiles are unavailable but explicit model dispatch exists, send the profile's
instructions and model/effort with a fresh-context spawn. In Codex collaboration
tools use `fork_turns="none"`; custom profile model settings take precedence over
spawn overrides, so use a general agent with the same instructions for an
explicit escalation. Never silently claim a profile/model was loaded.

## Dispatch contract

Before every delegation, write a compact brief with these fields. Include the
worker's Caveman/Ponytail instructions explicitly when not using a native profile.

```text
Goal: one observable result; role, tier and resolved model/effort.
Scope: exact worktree, files/symbols or URLs; snapshot/base; relevant callers.
Write permission: owned files, allowed test/scratch outputs; everything else excluded.
Known facts: domain terms, accepted decisions, relevant previous findings; source refs.
Memory status: verified query/scope/IDs (or verified empty); unavailable + error if failed.
Checks: acceptance conditions; concrete commands or facts to verify.
Exclusions: no adjacent refactor, no graph writes, no child agents, no external messages.
Budget: role turn limit; report <=200 words (scout <=120); artifact path for overflow.
Return: status complete|partial|blocked; result; files/lines or URLs; checks with actual
        command + exit/result; unverified items; artifact paths; next action.
```

Require Caveman throughout worker communication: terse precise fragments, no
filler, no repeated brief, locations over code dumps. Preserve exact identifiers,
commands, errors, domain terms and necessary evidence. Keep source code, user-facing
copy and formal requirements readable; token compression must not corrupt them.
Require Ponytail throughout work: inspect the real path/callers, reuse existing
code, stdlib and native features; smallest correct change; no speculative layers;
prove behavior. Never remove safety, validation, accessibility or error handling
for brevity. These portable rules are embedded in every profile; separate Caveman
and Ponytail installations are not required. Do not load full skill libraries
again. Every role consumes the coordinator's Mem0 context packet; no Obsidian or
other memory tools, duplicate recall, or worker-written memory/checkpoints.

Default at most two active workers, bounded by host capacity. Parallelize only
independent work. One owner per edited file; shared contracts serialize writers.
Builders are not alone: preserve others' edits. Freeze source before review;
read-only research/review may run together. Never use the builder as its own
independent refuter. Reviewers may produce only assigned evidence/test outputs.

Reuse a worker for related fixes while its scope/context remains useful. No
recursive delegation or large agent/team workflow unless explicitly requested
with a cap. Stop an off-scope or repeating worker; retain its useful evidence and
diagnose and rebrief or reassign with a changed approach. Worker limits bound an
invocation; they are not delivery repair caps or a reason to ask the user to retry.
A turn limit or incomplete output is partial,
never success. Claude enforces maxTurns; Codex budgets are coordinator-enforced
(no invented per-role maxTurns config). Close idle agents before starting more.

Long logs and analysis go to the assigned scratch file; downstream agents read
that file directly. Promote essential evidence to durable handoff artifacts before
discarding scratch. Checkpoint role/model, worker handle, owned files, artifact
paths, snapshot, findings and next action. Recover from files, not giant transcripts.

## Delivery loop roles

The [delivery loop](loop.md) adds five roles. `aw-planner` writes the claimed
bullet's plan from the work order; the coordinator accepts it or returns it with
corrections. It never edits source, writes the tracker, mutates Git or dispatches.
`aw-product-owner` is the [tracker steward](tracker.md#steward) and the one exception to "no external
messages": it may make the tracker writes its brief grants, only through the
tracker script, authorized by the project's tracker policy and the user's request
to deliver. Nothing else leaves the machine; it never hand-writes tracker queries
and never dispatches. `aw-qa` verifies a frozen snapshot against the plan and the
QA baselines; it never fixes, and its findings return through the coordinator to
the builder. `aw-router` writes the review packet; it never reviews. Both are
separate from the builder and from each other's judgement: builder checks do not
replace QA, QA results enter the packet as evidence rather than a verdict, and
refuters still review independently. `aw-qa` needs browser tools for UI bullets,
so its Claude profile restricts only edit and agent tools; dispatch it natively
for UI work, not through the isolated launcher. `aw-arbiter` is the
[review gate](review.md#review-ledger-and-gate): after each adjudicated round it
reads every round in the ledger and writes one verdict. It never reviews the
change, edits source, runs checks or dispatches. It is separate from the reviewers
and from the coordinator's adjudication, and its verdict binds the coordinator:
only the findings it lists go to the builder, and no round starts without its
`repair` or `replan`.

## Compaction

The isolated Codex process sets `model_auto_compact_token_limit = 200000` with
`total` scope. This leaves the coordinator unchanged. Inspection of Codex's role
override implementation shows native roles project only selected config fields;
do not claim per-role compaction or MCP isolation from arbitrary TOML settings.
Native workers inherit their parent's compaction settings. Use the isolated
process path when the explicit 200k worker policy is required.

`scripts/setup_agents.py --claude-settings <settings.json>` sets
`env.CLAUDE_CODE_AUTO_COMPACT_WINDOW` to `"200000"`, preserving unrelated settings.
Start a new session. This supported setting applies to **the main session and
every subagent**, capped by the model's actual capacity. Claude has no per-agent
environment frontmatter. Default automatic compaction begins around 95% (~190k),
not exactly 200k; this is a compaction window, not a hard token budget.

For session-only use: `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000 claude ...`.
Do not set DISABLE_AUTO_COMPACT, DISABLE_COMPACT or autoCompactEnabled=false;
existing disabling/percentage overrides must be
reported and reconciled with the user's requested policy before claiming it works.
Setting shell env in a child process cannot change an already-running parent.
The setup command reports settings-file conflicts rather than silently disabling
user configuration. Recheck shell/managed overrides when starting a workflow.
