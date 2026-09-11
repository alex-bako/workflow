# Focused delegation

Coordinator owns product questions, architecture, slice contracts, dispatch,
adjudication, integration and checkpoints. Keep the user's coordinator model
(for example Astra/Fable). Delegate bounded work; handle one grep or a trivial
edit locally. A graph node does not imply a new agent.

## Role defaults

| Role | Codex model / effort | Claude model / effort | Scope / turn budget |
| --- | --- | --- | --- |
| aw-scout | gpt-5.6-luna / low | haiku / low | Locate files, symbols, callers; 8 turns |
| aw-researcher | gpt-5.6-terra / medium | sonnet / medium | Verify scoped docs/source facts; 12 turns |
| aw-builder | gpt-5.6-terra / medium | sonnet / medium | Implement a clear bounded contract; 24 turns |
| aw-refuter | gpt-5.6-sol / high | opus / high | Independently inspect diff and rerun relevant checks; 16 turns |
| aw-debugger | gpt-5.6-sol / high | opus / high | Hard root-cause diagnosis after a reproduced failure; 16 turns |

These are starting choices, not a measured cost/quality ranking. Check actual
model availability. Use explicit model and effort, never accidental coordinator
inheritance. If a model is unavailable, select the smallest available suitable
one and record the substitution. After a bounded failure, narrow the contract
before escalating one tier; use the coordinator's frontier model only when the
remaining uncertainty merits it. Never weaken a required review to save tokens.

Use [Mem0-only memory and isolation](memory.md) before dispatch. Strict minimal
workers run through `scripts/run_worker.py`; the coordinator provides verified
Mem0 context and the child loads only its role instructions and code tools.
Native dispatch is an option for an already minimal session, with the limits below.

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
Goal: one observable result; role and selected model/effort.
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
rebrief once, then diagnose/escalate. A turn limit or incomplete output is partial,
never success. Claude enforces maxTurns; Codex budgets are coordinator-enforced
(no invented per-role maxTurns config). Close idle agents before starting more.

Long logs and analysis go to the assigned scratch file; downstream agents read
that file directly. Promote essential evidence to durable handoff artifacts before
discarding scratch. Checkpoint role/model, worker handle, owned files, artifact
paths, snapshot, findings and next action. Recover from files, not giant transcripts.

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
