# Agentic Workflow

One plugin for **Claude Code and Codex**: turn an idea into a plan, implement it in
small vertical slices, review the work, and resume where you left off.

## Everyday use

Open your project's repository or worktree in your coding tool. Use the commands
below in **Claude Code**. In **Codex**, replace `/agentic-workflow:aw-feature` with
`$aw-feature`, and use the same pattern for the other skills. You can also say
“Use aw-feature…” in plain language.

### 1. Plan a new feature or app

```text
/agentic-workflow:aw-feature I want to add team invitations to my app.
```

Just describe your idea. The skill already knows to:

- Act as both a Product Engineer and a Senior Staff Engineer.
- Ask one material question at a time and reuse your answers.
- Establish domain vocabulary, examples, business rules and relevant boundaries.
- Produce the PRD, product roadmap and milestone files, including vertical tracer
  bullets, dependencies and acceptance criteria.

**Planning stops before implementation.** You do not need to repeat these
instructions in your prompt. Existing project documents and naming are reused.

### 2. Prepare a specific tracer bullet

```text
/agentic-workflow:aw-plan Plan U2.2.T1 from docs/plans/U2-PLAN.md.
```

Replace the ID and file path with yours. This checks current code and dependencies,
then produces the detailed implementation plan, important contract snippets and
verification steps. Use it when the selected bullet still needs detailed planning.

### 3. Implement a planned card or tracer bullet

```text
/agentic-workflow:aw-resume Implement U2.2 from docs/plans/U2-PLAN.md.
Run tests and reviews, commit and push the feature branch, and create or
update its PR. Address incoming PR reviews. Do not merge.
```

The coordinator reconciles the plan with current progress, reuses the matching
run, and works through the selected scope. Review fixes stay with their original
tracer-bullet commits. PR creation starts the remote review phase; completion
requires the expected reviews and latest-head checks to finish without unresolved
actionable findings. A blocker or exhausted repair budget remains unfinished.

For local-only work, replace the publication instructions with **“Local changes
and reviews only; do not commit, push or create a PR.”**

### 4. Resume interrupted work

```text
/agentic-workflow:aw-resume Continue U2.2 from its saved workflow state.
```

Use the same worktree and include the saved task ID if several runs exist. This
continues the saved interview, implementation or review state within its existing
authorization. Planning runs stay planning-only until you request implementation.

## Which skill should I use?

Most work starts with **aw-feature** or continues with **aw-resume**. The individual
stages are also available when you only need one part:

| Skill | Use it for |
| --- | --- |
| `aw-feature` | An idea-to-planning interview, including domain and milestone documents |
| `aw-discover` | A PRD only |
| `aw-domain` | Domain vocabulary, examples, invariants and boundaries |
| `aw-roadmap` | A roadmap and milestone files from accepted requirements |
| `aw-plan` | A detailed plan for one tracer bullet |
| `aw-execute` | A bounded implementation or repair stage |
| `aw-review` | Independent reviews, finding adjudication and verification |
| `aw-resume` | Coordinate or resume the complete authorized workflow |
| `aw-context` | Retrieve relevant Mem0 context and prepare worker briefs |

## First-time setup

You need Git, Python 3.10+ and macOS or Linux. Install and authenticate the coding
clients you will use. The default cross-model review requires **both Claude Code
and Codex**. Configure **Mem0 in both clients** for shared recall; this plugin does
not provision Mem0 or supply its credentials.

Clone the repository once:

```sh
git clone https://github.com/alex-bako/workflow.git ~/work/agentic-workflow
```

Register the plugin with each client you use:

**Claude Code**

```sh
claude plugin marketplace add ~/work/agentic-workflow
claude plugin install agentic-workflow@agentic-workflow
```

**Codex**

```sh
codex plugin marketplace add ~/work/agentic-workflow
codex plugin add agentic-workflow@personal
```

This repository's Codex marketplace is named `personal`. If that name already
belongs to another marketplace, resolve the collision before registering it.

Install the focused Codex agent profiles and Claude compaction setting:

```sh
python3 ~/work/agentic-workflow/plugins/agentic-workflow/scripts/setup_agents.py \
  --codex-home ~/.codex --claude-settings ~/.claude/settings.json
```

Use only the relevant flag if you use one client. Setup preserves unrelated
settings and refuses conflicting agent files. Claude discovers its agents from
the plugin. **Restart your clients after installation or an update.**

The 200k Claude compaction window applies to the main session and subagents;
it is not a weekly usage cap. See [agent setup and limits](plugins/agentic-workflow/references/subagents.md#compaction).

## What happens automatically?

- **Planning graph:** discovery → domain language → roadmap and milestones → done.
- **Development graph:** slice plan → implementation → local reviews and repairs →
  verification → publication when authorized → remote reviews → done.
- **Focused workers:** smaller models handle bounded tasks; Caveman/Ponytail rules
  are embedded, so workers need no separate copies of those plugins.
- **Shared memory:** Mem0 is the only shared-memory provider. Workers receive small
  context packets; project documents and exact checkpoints remain local artifacts.

The coding client runs the workflow. The helper records state and validates
transitions; it does not run a background scheduler or survive a closed client as
an active monitor. Keep the worktree and use `aw-resume` after an interruption.

## Further details

- [Planning interview and document outputs](plugins/agentic-workflow/references/planning.md)
- [Commit history and PR review policy](plugins/agentic-workflow/references/delivery.md)
- [Agent roles, model choices and budgets](plugins/agentic-workflow/references/subagents.md)
- [Mem0 and worker isolation](plugins/agentic-workflow/references/memory.md)
- [Graph commands, checkpoints and migrations](plugins/agentic-workflow/references/runtime.md)
- [Optional project knowledge graph](plugins/agentic-workflow/references/knowledge.md)

For plugin development, run `python3 -m unittest discover -s tests -v` and validate
both plugin manifests. Tests use temporary Git repositories and make no model calls.
