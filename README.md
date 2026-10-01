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
actionable findings. The coordinator owns recovery: diagnose, change approach or
reassign work without a fixed retry cap. It asks you only for decisions, authority
or access that it cannot obtain itself.

For local-only work, replace the publication instructions with **“Local changes
and reviews only; do not commit, push or create a PR.”**

### 4. Resume interrupted work

```text
/agentic-workflow:aw-resume Continue U2.2 from its saved workflow state.
```

Use the same worktree and point to the plan or progress note. The coordinator
reconciles that note with actual code, checks and pending operations before
continuing within existing authorization. Planning runs stay planning-only until you request implementation.

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
| `aw-resume` | Coordinate or resume approved work, including recovery and verification |
| `aw-eval` | Evaluate a skill change against realistic scenarios; optional plugin development tool |
| `aw-context` | Retrieve relevant Mem0 context and prepare worker briefs |

## First-time setup

Install and authenticate the coding client(s) you will use. **The skills do not
require Python, a graph runtime, JSON state or an agent-launch script.** They work
from your project documents and a short Progress section in the selected plan.
Use your normal project tools for builds and tests.

Native host agents are the default. One reviewer independent of the builder is the
starting point; add specialist/cross-provider review for risk or project policy.
Configure Mem0 for shared recall; unavailable memory does not block work supported
by project documents. The plugin does not provision credentials.

Install directly from the released marketplace—no manual clone needed:

**Claude Code**

```sh
claude plugin marketplace add https://github.com/alex-bako/workflow.git#stable
claude plugin install agentic-workflow@agentic-workflow
```

Restart Claude to load the skills. `aw-setup` is optional.

**Codex**

```sh
codex plugin marketplace add alex-bako/workflow --ref stable
codex plugin add agentic-workflow@agentic-workflow
```

Restart Codex to load the skills. **“Use aw-setup”** is optional.

Optional setup installs the bundled Codex profiles or configures Claude's
compaction window. This convenience helper needs Python 3.10+ on macOS/Linux;
it preserves unrelated settings and refuses conflicting files. You can instead
use native agents with coordinator-supplied role briefs, without running setup.

Already using the old local marketplace? See [migration and updates](docs/releases.md#installations-and-updates)
before registering the remote source.

The 200k Claude compaction window applies to the main session and subagents;
it is not a weekly usage cap. See [agent setup and limits](plugins/agentic-workflow/references/subagents.md#compaction).

## What happens automatically?

- **Human-led planning:** collaborative discovery, domain language, roadmap and
  milestone documents. Planning stops before implementation.
- **Coordinator-led delivery:** choose the next useful implementation, investigation,
  review or QA action. Preserve scope and acceptance; adapt the execution strategy.
- **Browser/design QA:** independently exercise UI changes against the accepted
  design, with screenshots and concrete findings. Do not accept a candidate's
  screenshot as its own proof of correctness.
- **Focused workers:** smaller models handle bounded tasks; Caveman/Ponytail rules
  are embedded, so workers need no separate copies of those plugins.
- **Shared memory:** Mem0 is the only shared-memory provider. Workers receive small
  context packets; project documents and exact checkpoints remain local artifacts.

The coding client runs the work; the plugin is not a background scheduler. Keep
the worktree and use `aw-resume` after an interruption. Existing Python scripts
and graphs remain optional compatibility utilities. Older saved findings and
review requirements are preserved; their retry counters no longer force escalation.

## Evaluate the skills

Use `aw-eval` when changing a skill, not for every delivery task. It runs selected
[behavioral scenarios](plugins/agentic-workflow/references/evals.md) in isolated
workspaces and scores observed actions and artifacts against held-out criteria.
Start with recovery, planning boundaries and website QA; compare old/new skill
versions using the same provider, model and case. No eval framework or Python
runner is required. These model-behavior evals are separate from the helper's unit
tests; passing one does not prove the other.

## Updates

**Claude Code:** run `claude plugin marketplace update agentic-workflow`, then
`claude plugin update agentic-workflow@agentic-workflow`.

**Codex:** run `codex plugin marketplace upgrade agentic-workflow`, then
`codex plugin add agentic-workflow@agentic-workflow`.

Restart after updating. Rerun optional `aw-setup` only if you use its installed profiles and their configuration changed.

## Further details

- [Releases, pinned versions and marketplace migration](docs/releases.md)
- [Planning interview and document outputs](plugins/agentic-workflow/references/planning.md)
- [Commit history and PR review policy](plugins/agentic-workflow/references/delivery.md)
- [Agent roles, model choices and budgets](plugins/agentic-workflow/references/subagents.md)
- [Mem0 and worker isolation](plugins/agentic-workflow/references/memory.md)
- [Optional legacy graph commands and migrations](plugins/agentic-workflow/references/runtime.md)
- [Optional project knowledge graph](plugins/agentic-workflow/references/knowledge.md)

For plugin development, run `python3 -m unittest discover -s tests -v` and validate
both plugin manifests. Tests use temporary Git repositories and make no model calls.
