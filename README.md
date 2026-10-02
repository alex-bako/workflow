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

### 5. Work through an issue board

If your roadmap items are GitHub issues on a Projects board, add
`tracker-policy.json` to the project root. It maps your board to the workflow:

```json
{
  "repo": "owner/name",
  "project": {"owner": "owner", "number": 1, "status_field": "Status"},
  "states": {"backlog": "Backlog", "ready": "Ready", "in_progress": "In progress",
             "in_review": "In review", "blocked": "Blocked", "done": "Done"},
  "items": {"label": "roadmap", "startable_states": ["ready"]},
  "bullets": {"label": "tracer-bullet", "pattern": "^\\d+\\. `(?P<id>[^`]+)` — (?P<text>.+)$"},
  "authority": "docs/roadmap/ROADMAP.md",
  "merge": {"allowed": false, "method": "rebase"}
}
```

Then say:

```text
/agentic-workflow:aw-next Implement the next issue.
```

Each pass delivers one tracer bullet as its own sub-issue and pull request, then
takes the next one. Your session is the coordinator: it dispatches the agents below,
accepts the plan, decides on review findings and owns Git.

| Stage | Agent | What it does |
| --- | --- | --- |
| Pick | `aw-product-owner` | Picks and claims the next bullet on the board through the bundled tracker script, and returns a work order |
| Plan | `aw-planner` | Writes the plan: acceptance lines, scope fence, a check for every acceptance line |
| Publish | `aw-product-owner` | Writes the accepted plan into the bullet's issue |
| Implement | `aw-builder` | Builds that bullet and nothing else |
| QA | `aw-qa` | Runs the project checks and maps every change to a plan step |
| Review | `aw-router`, two `aw-refuter` | The router writes a short review packet; a Claude and a Codex reviewer review from it |
| Gate | `aw-arbiter` | Decides after each round: repair, stop, replan or ask you |
| Pull request | coordinator | Commits, opens the pull request, works through its reviews, merges when allowed |

It stops and reports when the board has nothing ready or access is missing, and
asks you when a decision is not settled by your roadmap, plans or code. For a
product spread over several repositories, list them under `repos` in the policy. It merges only
when you set `"merge": {"allowed": true}` and every review and check has passed;
with `false` it leaves each pull request ready for you. The script uses your `gh`
login, which needs the `repo` and `project` scopes (`gh auth refresh -s project`).
All policy keys are in the [tracker reference](plugins/agentic-workflow/references/tracker.md).

**Use it in another repository.** You need a GitHub Projects board linked to the
repository with a single-select `Status` field, your roadmap items as open issues
carrying the card label (`roadmap` unless you change it), and `gh` logged in with
the `repo` and `project` scopes. You do not have to write the policy: run `aw-next`
in that repository, or `python3 <plugin>/scripts/tracker.py init` (add
`--project OWNER/NUMBER` when several boards are linked). It drafts
`tracker-policy.json` from the repository and board, lists what is missing (a
column, a label with the `gh label create` command for it), changes nothing on
GitHub, and `aw-next` waits for your go-ahead. Check three things in the draft:
`items.label`, the label that marks a card; `bullets.pattern`, how a card's body
lists its tracer bullets (the default reads a numbered list); and `merge.allowed`,
which stays `false` until you set it. `authority` and `order` are optional: without
an order file, cards are taken in issue-number order.

**Review rounds stop on nitpicks.** Reviewers always find something. After every
review round, a separate gate agent reads all earlier rounds of that bullet (kept in
a review ledger next to its plan) and decides what happens next. Only a finding that
demonstrates a real problem (a failing test, a broken acceptance line, wrong
behavior at the cited line) is fixed; style, naming and "consider" suggestions get
a one-line answer and no code change, and a point already answered does not come
back without new evidence. When nothing real is left, the loop stops. If the third
round of local review, or of pull-request review, still finds real problems, the
coordinator stops patching and rethinks the plan or design once; if problems remain
after that, it asks you, with a summary of every round.

**Unplanned problems are filed, not fixed on the side.** A flaky test, a defect next
to the change or a problem seen after merge is never fixed inside the current
bullet. The Product Owner agent collects the evidence (command, output, how often it
fails), checks for an existing issue, files or extends one and ranks it `urgent`,
`soon` or `later`. `aw-next` picks found issues up by rank, urgent ones first, and
tells you at the end of each pass what it filed. Enable it in the policy:

```json
"found": {"label": "found", "issue_type": "Bug",
          "priorities": {"urgent": "priority:urgent", "soon": "priority:soon", "later": "priority:later"}}
```

The labels must exist in the tracker repository:

```sh
gh label create found --description "Found while delivering" -R owner/name
gh label create priority:urgent -R owner/name
gh label create priority:soon -R owner/name
gh label create priority:later -R owner/name
```

To reorder, change an issue's priority label on GitHub; the agent never lowers a
rank you set.

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
| `aw-next` | Deliver the next tracer bullet from an issue board, then continue |
| `aw-eval` | Evaluate a skill change against realistic scenarios; optional plugin development tool |
| `aw-context` | Retrieve relevant Mem0 context and prepare worker briefs |

## First-time setup

Install and authenticate the coding client(s) you will use. **The skills do not
require Python, a graph runtime, JSON state or an agent-launch script.** They work
from your project documents and a short Progress section in the selected plan.
Use your normal project tools for builds and tests. The one exception is `aw-next`:
its tracker script needs Python 3.10+ (standard library only) and the `gh` CLI.

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

## Models

Agent roles name a tier, never a model, so the same roles run in Claude Code and
in Codex. [`models.json`](plugins/agentic-workflow/models.json) maps each tier to a
Claude and a Codex model and is the only place model names live.

| Tier | Used by |
| --- | --- |
| `light` | `aw-scout` |
| `standard` | `aw-researcher`, `aw-builder`, `aw-product-owner`, `aw-qa`, `aw-router` |
| `deep` | `aw-refuter`, `aw-debugger`, `aw-arbiter`, and the coordinating session |
| `planner` | `aw-planner` only |

Run your session on the `deep` tier's model. The `planner` tier writes
tracer-bullet plans in the delivery loop and nothing else; no role inherits the
session's model. To change models, edit `models.json` and run
`python3 scripts/sync_profiles.py` to restamp the bundled profiles; the release
check fails when a profile and the mapping disagree.

## Evaluate the skills

Use `aw-eval` when changing a skill, not for every delivery task. It runs
[behavioral scenarios](plugins/agentic-workflow/references/evals.md) against
held-out criteria: E1–E6 by a prose protocol, and the role and loop cases E7–E21
(pick, claim conflict, refused write, QA, router, one loop pass, review gate, found
work, builder, planner) as 21 [Harbor tasks](plugins/agentic-workflow/evals/harbor/README.md) whose
RewardKit verifiers score the files, exit states and logs a run leaves. Harbor (with
Docker and uv) is an optional development tool, not a plugin dependency, and these
model-behavior evals are separate from the helper's unit tests.

```sh
uv tool install harbor
H=plugins/agentic-workflow/evals/harbor
python3 $H/prepare.py                                  # rebuild bundle and fixtures
harbor run -p $H/tasks -a oracle -o /tmp/aw-jobs -y    # self-check: every task 1.0
harbor run -p $H/tasks -a nop -o /tmp/aw-jobs -y       # self-check: every task 0.0
harbor run -p $H/tasks -a claude-code -m anthropic/<model> --env-file <credential file> \
  -k 3 -o /tmp/aw-jobs                                 # real run, 3 attempts per task
CODEX_FORCE_AUTH_JSON=1 harbor run -p $H/tasks -a codex -m openai/<model> \
  -k 3 -o /tmp/aw-jobs                                 # same tasks with your Codex login
```

Run a changed role on every model its tier maps to, and compare revisions with the
same agent, model and `-k`. Do not run `prepare.py` while a job is in progress: it
regenerates the fixtures the verifiers compare against.

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
- [Issue board tracker policy and script](plugins/agentic-workflow/references/tracker.md)
- [Delivery loop, scope fence, QA and merge rules](plugins/agentic-workflow/references/loop.md)
- [Agent roles, model tiers and budgets](plugins/agentic-workflow/references/subagents.md)
- [Mem0 and worker isolation](plugins/agentic-workflow/references/memory.md)
- [Optional legacy graph commands and migrations](plugins/agentic-workflow/references/runtime.md)
- [Optional project knowledge graph](plugins/agentic-workflow/references/knowledge.md)

For plugin development, run `python3 -m unittest discover -s tests -v` and
`python3 scripts/check_release.py`, which validates both plugin manifests, the
required files and the profiles' model lines. Tests use temporary Git repositories
and make no model calls.
