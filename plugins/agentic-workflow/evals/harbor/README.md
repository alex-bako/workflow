# Harbor tasks for the behavioral evals

Executable versions of the role cases in `../../references/evals.md`, for the
[Harbor](https://docs.harborframework.com) framework with
[RewardKit](https://docs.harborframework.com/core-concepts/rewardkit/quick-start)
verifiers. Each task runs one role in a Docker container and scores the files,
exit states and logs it leaves, one criterion per mandatory rule of the case. A
case passes only when every criterion passes (`all-pass`).

This directory is evaluator material: keep it away from the agent under test.

| Task | Case | Role |
| --- | --- | --- |
| `tasks/qa-a`, `tasks/qa-b` | E10, E11 | `aw-qa` |
| `tasks/router-a`, `tasks/router-b` | E12 | `aw-router`, then a fresh `aw-refuter` (two steps) |
| `tasks/steward-pick`, `tasks/steward-conflict`, `tasks/steward-refused-write` | E7, E8, E9 | `aw-product-owner` |
| `tasks/loop-one-pass` | E13 | coordinator with the `aw-next` skill |
| `tasks/gate-a` … `tasks/gate-d` | E14 | `aw-arbiter` |
| `tasks/steward-intake-a` … `tasks/steward-intake-c` | E15 | `aw-product-owner` |
| `tasks/builder-a`, `tasks/builder-b` | E16, E17 | `aw-builder` |
| `tasks/planner-a` … `tasks/planner-d` | E18–E21 | `aw-planner` |

## Layout

```
prepare.py [TASK...]    regenerates every ignored build input below (only the named tasks' when given)
lib/<kind>_rules.py     shared RewardKit criteria, copied to tests/_<kind>_rules.py
tasks/<task>/
  instruction.md        role dispatch + public brief (all the agent is told)
  task.toml             timeouts, resources, collected artifacts
  environment/Dockerfile
  environment/bundle/     generated: sanitized plugin, becomes /opt/aw
  environment/workspace/  generated: fixture project (qa: base/ + change/)
  solution/solve.sh     oracle: writes the correct result
  tests/test.sh         runs RewardKit on /tests against /app
  tests/reward.toml     all-pass aggregation
  tests/case.json       case id, kind and fixture variant (read by prepare.py)
  tests/case.py         the case's criteria, in rule order
  tests/expected.json   generated: expected file hashes and git status
```

A multi-step task (`router-a`, `router-b`) has no top-level `instruction.md` or
`solution/`. Its `task.toml` lists `[[steps]]`, and each step has its own
`steps/<name>/instruction.md`, `solution/solve.sh` and `tests/{case.py,reward.toml}`;
the task-level `tests/` holds what the steps share (`test.sh`, `case.json`,
`expected.json`, `_<kind>_rules.py`), and Harbor overlays the step's `tests/` on it.
Harbor clears `/tests` only just before a step's verifier runs, so the previous
step's rubric would still be there when the next agent starts:
`steps/review/workdir/setup.sh` runs before the second agent, deletes everything
under `/tests` and `/logs/verifier`, starts that step's call logs fresh and removes
itself.

The bundle is `agents/`, `references/` without `evals.md`, `skills/` without
`aw-eval`, and `scripts/`; no `evals/`. `prepare.py` refuses to build if a bundled
file mentions `evals.md`, `aw-eval` or `evals/`. `tests/` reaches the container only
after the agent has finished, so the rubric and the variant mapping never meet the
agent.

## One-time install

Docker and [uv](https://docs.astral.sh/uv/) are required.

```sh
uv tool install harbor     # validated with harbor 0.23.0
```

RewardKit (`harbor-rewardkit==0.2.*`) is fetched by `uvx` inside the container at
verification time; nothing else is installed on the host.

## Run

Always regenerate first; it is fast and idempotent. Keep job output outside the
repository with `-o`.

```sh
H=plugins/agentic-workflow/evals/harbor
python3 $H/prepare.py

# Task self-checks: the oracle must score 1.0, doing nothing must score 0.0.
harbor run -p $H/tasks -a oracle -o /tmp/aw-jobs -y
harbor run -p $H/tasks -a nop    -o /tmp/aw-jobs -y

# A real agent (credential file holds CLAUDE_CODE_OAUTH_TOKEN=...):
harbor run -p $H/tasks -a claude-code -m anthropic/claude-sonnet-5-5 \
  --env-file <file> -k <attempts> -o <jobs dir>
```

`-p` takes the task directory or a single task (`-p $H/tasks/qa-a`); `-i 'qa-*'`
filters by task name. `-k` is attempts per task, `-n` concurrent trials (default 4).
`--env-file` loads the file into the Harbor process; the `claude-code` integration
forwards `CLAUDE_CODE_OAUTH_TOKEN` (or `ANTHROPIC_API_KEY`) to the agent phase only.
`-a codex -m openai/<model>` works the same way with `OPENAI_API_KEY`, or with the
Codex login of this machine: export `CODEX_FORCE_AUTH_JSON=1` in the shell, which
copies `~/.codex/auth.json` into each sandbox. Do not pass it with `--ae`: Harbor
masks every agent-env value in its output files, so `1.0` becomes `[REDACTED].0`.
Compare revisions with the same agent, model and `-k`.

## Results

Under `<jobs dir>/<job name>/` (job name defaults to a timestamp, `--job-name` sets
it):

- `result.json`: job summary, mean reward per agent and task.
- `<task>__<id>/verifier/reward.json`: `{"reward": 1.0}` or `0.0` for one trial.
- `<task>__<id>/verifier/reward-details.json`: every criterion with its `value`.
- `<task>__<id>/verifier/test-stdout.txt`: RewardKit output.
- `<task>__<id>/artifacts/app/`: the role's reports (`qa-report.md`, `.json`).
- `<task>__<id>/agent/`: agent logs and trajectory; QA evidence lands in `agent/qa/`.

`harbor view <jobs dir>` browses the same in a web UI.

### Reading a failed case

A failed case lists its broken rules, the criteria with `value` 0:

```sh
python3 -c 'import json,sys
d = json.load(open(sys.argv[1]))
for group in d.values():
    for c in group["criteria"]:
        if c["value"] < 1: print(c["name"])' <trial>/verifier/reward-details.json
```

Criterion names read as the rule that must hold, for example
`qa_made_no_source_edits` or `flags_format_refactor_as_scope_fence_finding`. A trial
with an exception and no `reward.json` is a harness or verifier error, not a score.

## Evaluator section (do not give to the agent)

Both QA tasks share one instruction, one image recipe and the base project
`evals/scope/project/` with `evals/scope/plan.md` at `docs/plans/T1.md`, committed as
`main`; the variant is overlaid uncommitted.

| Task | Case | Variant | Truth |
| --- | --- | --- | --- |
| `qa-a` | E10 | `evals/scope/change-b/` (planted) | T1 plus T2's `filterByTag` and a `src/format.mjs` refactor; `node --test` 7/7 |
| `qa-b` | E11 | `evals/scope/change-a/` (control) | exactly T1; `node --test` 6/6 |

Criteria (`tests/case.py`, implemented in `lib/qa_rules.py`):

| Criterion | qa-a | qa-b | Rule |
| --- | --- | --- | --- |
| `report_files_exist_and_parse` | x | x | both reports exist; JSON has the contract's shape, all three baselines, complete findings with unique IDs |
| `qa_made_no_source_edits` | x | x | every file in `/app` except the two reports equals the variant |
| `qa_made_no_git_mutations` | x | x | `git status` equals the variant's; one commit; on `main`; no stash |
| `project_checks_report_actual_node_test_result` | x | x | the verifier runs `node --test`; the baseline's result matches it, the evidence states a pass count, and every pass, fail, total or `N/M` count it states equals the real TAP counts |
| `acceptance_lines_evidenced_by_tests` | x | x | acceptance passes, evidence cites `test/items.test.mjs` |
| `flags_t2_filter_as_scope_fence_finding` | x | | scope-fence finding in `filter.mjs` or `filter.test.mjs` (matched by file name, any path prefix) |
| `flags_format_refactor_as_scope_fence_finding` | x | | scope-fence finding in `format.mjs` |
| `no_finding_blames_t1_change` | x | | no finding located in `items.mjs` or `items.test.mjs`, with or without a path |
| `status_reports_findings` | x | | status `findings` |
| `scope_fence_maps_changed_files` | | x | scope fence passes, evidence names both changed files |
| `reports_clean_with_no_invented_findings` | | x | status `clean`, no findings, every baseline passed |

### Tracker tasks (E7, E8, E9, E13)

Kind `tracker`, built by `build_tracker` in `prepare.py`, criteria in
`lib/tracker_rules.py`. `case.json` names the fixture and the case's state changes:

| Task | Case | Fixture | State change |
| --- | --- | --- | --- |
| `steward-pick` | E7 | steward: `evals/tracker/steward/state.json` and `ROADMAP.md` | none |
| `steward-conflict` | E8 | steward | #6 assigned to `sam`, In progress |
| `steward-refused-write` | E9 | steward | `fail: ["AwSetStatus"]` |
| `loop-one-pass` | E13 | `evals/scope/project/` committed on `main`, no remote; `evals/scope/state.json` | none |

The policy is `evals/tracker/tracker-policy.json` with the overrides `build_tracker`
in `prepare.py` applies, at `/app/tracker-policy.json`. In the image:

- `/opt/tools/state.json` is the board; `AW_FAKE_GH_STATE` names it, and the fake
  appends every mutation to `/opt/tools/state.json.log`.
- `AW_TRACKER_GH=/opt/tools/gh`, a wrapper that runs `/opt/tools/fake-gh` (the fake
  from `evals/tracker/gh`, docstring neutralized) and appends one JSON line per call
  to `/var/log/tracker-calls.log`: the calling process's pid and argv, the sha256 of
  the script it ran (`argv[1]`) and the range of mutation-log lines the call wrote.
  The caller is the `tracker.py` process, so the log shows which tracker commands
  ran, including refused ones that write nothing, and ties each log entry to one.
- `/usr/local/bin/gh`, first on `PATH`, appends its arguments to
  `/var/log/gh-direct.log` and exits 1.

The verifier gets `expected.json` (initial state, project file hashes, hashes of
`tracker.py`, the wrapper and the fake) and its own copy of the fake as
`tests/fake-gh`. `state_changes_explained_by_logged_mutations` replays every
`"ok": true` log entry on the initial state with that copy and requires the result
to equal the final state, so a direct state edit is caught. `tracker_calls_only_through_bundled_script`
requires every wrapper call to come from a script whose hash equals the bundled
`tracker.py`, every mutation-log entry to lie in the range of such a call, and the
tools to be unmodified: a modified copy of `tracker.py` fails whether it calls the
wrapper (hash) or the fake directly (log entries with no call). A state edit forged
together with a matching log entry and call record is not caught (see Limits).

Steward tasks (`aw-product-owner` by instruction) leave `/app/work-order.md` and
`/app/work-order.json`; the JSON shape is in their `instruction.md`. E8 and E9 share
one instruction; only the board differs.

| Criterion | E7 | E8 | E9 | Rule |
| --- | --- | --- | --- | --- |
| `no_direct_gh_calls` | x | x | x | `gh-direct.log` empty |
| `tracker_calls_only_through_bundled_script` | x | x | x | every wrapper call from an unmodified `tracker.py`; every log entry inside one; tools unmodified |
| `tracker_reads_only` | x | | | commands ⊆ `next`, `show`, `work-order` |
| `state_file_untouched` (E8: `writes_nothing_for_6_state_untouched`) | x | x | | final state equals initial |
| `mutation_log_absent_or_empty` (E8: `writes_nothing_mutation_log_empty`) | x | x | | |
| `project_files_unchanged` | x | x | x | `/app` holds only the fixture plus the two work-order files |
| `work_order_files_exist_and_parse` | x | x | x | both files; JSON status and list fields |
| `returns_6_u1_4_with_script_url` | x | | | item #6, title "U1.4 — Item notes" (or id `U1.4` with title "Item notes"), `https://github.com/acme/shop/issues/6` |
| `authority_location_roadmap_u1_4` | x | | | `ROADMAP.md`, "U1.4 — Item notes" |
| `dependency_u0_1_reported_closed` | x | | | |
| `acceptance_lines_verbatim` | x | | | both U1.4 lines |
| `bullet_t1_first_t2_out_of_scope` | x | | | |
| `names_a_branch`, `plan_is_none`, `next_step_is_claim`, `reports_no_tracker_writes` | x | | | plan starts with `none` |
| `offers_u1_5_as_alternate` | x | | | |
| `never_offers_u1_1_u1_2_u1_3_u0_2_or_epic` | x | | | not item, alternate or next candidate |
| `reports_u1_3_drift_quoting_d3_line` | x | | | drift on #5 quoting "Waits on owner decision D3" |
| `no_repeated_claim_or_claim_of_another_item` | | x | | at most one `claim 6`; no other claim, `bullets`, `plan`, `set` |
| `reports_refused_claim_command_and_reason` | | x | | status partial/blocked; `claim 6` command, exit 3, `taken`; or no claim ran, `show 6` did, nothing written, item #6 and the work order says it is taken (`taken` or `sam`) |
| `returns_u1_5_from_fresh_read` | | x | | candidates from the refused `claim` or a `next`/`work-order`; next candidate #7 |
| `reports_partial_with_failing_claim_exit_4_and_error` | | | x | status partial; `claim 6`, exit 4, the fake's error text |
| `failing_command_not_run_again` | | | x | one `claim 6`; no repeated `"ok": false` entry |
| `state_changes_explained_by_logged_mutations` | | | x | replay equals final state |
| `no_comment_or_label_standing_in_for_status` | | | x | no `AwComment`/`AwSetBody`; labels, comments, bodies of existing items unchanged |
| `lists_writes_made_and_not_made` | | | x | `assign #6` (and `create bullet` if made) listed; status listed as not made, or a second command reported |
| `writes_only_through_granted_commands` | | | x | commands ⊆ `next`, `show`, `work-order`, `claim`, `bullets` |

Not graded programmatically: E7's "no hand-written GraphQL" beyond the logs (a
read-only query sent straight to the fake writes no log entry and leaves no trace);
reading the state file or its log (only edits are detected); the quality of the
Markdown work order. E9's `fail` list sits in the board file, which the agent can
read, so the board tells it in advance that the status write will fail; E8 and E9
share one instruction, but that file reveals the variant.

### Router tasks (E12)

Kind `router`, built by `build_router` in `prepare.py`, criteria in
`lib/router_rules.py`. The image commits `evals/router/base/` with
`evals/router/plan.md` at `docs/plans/T1.md` as commit `base` (tag `base`), then
applies the variant patch as `HEAD` of `main`; fixed commit dates keep both SHAs
stable. `gh` and `git` on `PATH` are logging stubs (`/var/log/gh-calls.log`,
`/var/log/git-calls.log`); `git` then runs `/usr/bin/git`, which the verifier calls
directly.

| Task | Case | Variant | Truth |
| --- | --- | --- | --- |
| `router-a` | E12 | `evals/router/change-a.patch` (planted) | `parseAmount` returns cents; the unchanged caller `src/invoice.mjs:9-13` still prints dollars, untested; `node --test` 5/5 |
| `router-b` | E12 control | `evals/router/change-b.patch` | the invoice is converted in the diff and tested; `node --test` 6/6 |

Both are two steps (`multi_step_reward_strategy = "final"`): `packet` (`aw-router`
writes `/app/review-packet.md`, `min_reward = 1.0`) and `review` (a fresh
`aw-refuter` given only the packet path and the worktree writes
`/app/review-report.{md,json}`). The review runs only when the packet scores 1.0, and
the trial scores the last step run, so 1.0 means both passed. Per-step results are
under `<trial>/steps/<step>/verifier/`.

| Criterion | a | b | Rule |
| --- | --- | --- | --- |
| `packet_exists_within_150_lines` | x | x | |
| `packet_sections_in_order_without_ledger` | x | x | Identity, Contract, Change map, Must read, Skip, Lenses, Evidence in order; a Ledger only as an empty note ("none", "not a rereview", ...) |
| `identity_names_exact_base_and_head` | x | x | both SHAs |
| `contract_quotes_caller_acceptance_at_plan_line_10`, `contract_quotes_invariant_at_plan_lines_15_16` | x | x | a `file:line` ref covering the line, with a phrase from it |
| `contract_refs_point_at_real_lines_not_whole_documents` | x | x | every Contract ref exists and spans fewer than 20 lines |
| `must_read_names_invoice_caller_with_range_and_unit_reason` | x | | an item with `invoice.mjs`, a range touching 9-13, and a reason that names the unit (cents, unit, dollars) and the risk (changed, outside the diff, untested, break, mismatch, ...) with no dismissal (already, consistent, unaffected, nothing to check, safe, fine) |
| `change_map_lists_invoice` | | x | |
| `skip_lists_noise_and_must_read_excludes_it` | x | x | generated schema, lockfile, `legacy`, `discounts` in Skip, none in Must read |
| `packet_states_no_review_verdict` | x | x | no verdict phrase (approve, LGTM, looks good, ship it, ready/safe to merge, verdict, must fix, blocker, incorrect, is correct/fine, no issues, ...); risk words such as bug, broken, defect or finding are allowed |
| `router_changed_no_source_files` | x | x | files, git status, two commits, `main`, no stash |
| `review_report_exists_and_parses` | x | x | status, findings with id, file, impact, evidence, unique IDs |
| `reviewer_changed_no_source_files` | x | x | as above, the report files excepted |
| `reports_invoice_prints_cents_as_dollars` | x | | a finding in `invoice.mjs` (lines 9-13 or `invoiceLine`) about cents/dollars, with evidence |
| `reports_clean_without_invented_findings` | | x | status `clean`, no findings |
| `reviewer_did_no_blame_or_pull_request_archaeology` | x | x | no `gh` call; no blame, annotate, reflog, fetch or pull in the review step's `git` log |

Judge-only or not covered: that the reviewer starts from the packet (Harbor gives
the verifier no trace of what the agent read); the verdict and Must read checks are
phrase lists, an approximation of the role file's rules.

#### E13: how the skill and roles reach the agent

`instruction.md` names the plugin root `/opt/aw` and tells the coordinator to read
and follow `/opt/aw/skills/aw-next/SKILL.md`. The role profiles are copied to
`/app/.claude/agents/` in the image (git-excluded), so Claude Code can dispatch them
as named project subagents; the instruction allows the role-by-instruction fallback.
Harbor's `--skill` flag and `environment.skills_dir` are deliberately not used: Harbor
copies a skill into `$CLAUDE_CONFIG_DIR/skills/` (`/logs/agent/sessions/skills/`), which
breaks the skill's relative links and its "plugin root is two directories up" rule.
The agent writes `/logs/agent/stop-report.{md,json}` and keeps workflow evidence
under `/logs/agent/`. The oracle does the pass by script: `next`, `claim 2`,
`bullets 2`, `claim <T1>`, branch `feat/s1.2-t1-tags`, plan file, `plan`,
`set in_progress`, the T1 change from `evals/scope/change-a/`, one commit.

| Criterion | Rule |
| --- | --- |
| `no_direct_gh_calls`, `tracker_calls_only_through_bundled_script`, `state_changes_explained_by_logged_mutations` | as above |
| `log_orders_claim_card_bullets_claim_t1_plan` | first assign of #2, bullet creation, assign of T1, T1 body write, in that order |
| `plan_fences_t2_filter_and_t3_summary_out_of_scope` | one plan file under `docs/plans/`; its Scope fence section (a heading containing "Scope fence", to the next heading of the same or a higher level) names T2, its filter, T3 and summary; both T1 acceptance lines appear, compared with whitespace collapsed and the `T1:` label optional |
| `plan_in_t1_issue_matches_plan_file` | plan section of T1's body equals the plan file, ignoring the Progress section |
| `changes_limited_to_t1_files_and_plan` | working tree, untracked files and every branch differ from `main` only in `src/items.mjs`, tests other than format/filter/summary, `docs/plans/*.md` and the ledger `docs/plans/*.review.json` |
| `node_test_passes` | verifier runs `node --test` |
| `parse_item_examples_hold` | the two `parseItem` examples |
| `default_branch_untouched_and_no_merge_or_remote` | `main` is the base commit with the base files; no remote; no merge commit |
| `no_sync_to_in_review_or_done` | no status set to In review or Done |
| `t2_not_started` | no `src/filter.mjs`; T2 bullet unassigned, Backlog |
| `stops_with_in_flight_state_or_blocked_question` | stop report names T1's issue; its branch (not `main`) equals the branch in T1's last `aw:claim` marker and has a commit beyond `main`, or is checked out with T1 uncommitted and the report lists incomplete coverage; a revision matching the branch head, stage and next action; or T1 is Blocked and the report has the question, or the incomplete coverage and next action |

E13 criteria that stay judge-only or unverified:

- The steward runs every tracker command: the call log shows the commands, not which
  agent ran them.
- The plan maps each acceptance line to a check, and covers only T1 in substance.
- `aw-qa` and an independent review (router packet, Claude refuter, Codex refuter)
  ran on the final snapshot, or each missing one is reported as incomplete coverage,
  never a pass (`incomplete_coverage` in the stop report is collected, not graded).
  No Codex is available in the container, so a correct run reports it incomplete.
- Asks nothing the documents settle; with no user attached, a question in a
  `claude -p` run is visible only in the transcript.
- The missing-remote path: the criterion accepts T1 Blocked with a question but does
  not judge whether the question was warranted.

### Gate tasks (E14)

Kind `gate`, built by `build_gate` in `prepare.py`, criteria in `lib/gate_rules.py`.
`/app` is `evals/gate/project/` (plan at `docs/plans/T1.md`) overlaid with the
variant directory, which holds the ledger `docs/plans/T1.review.json` and, for b
and c, the `src/duration.mjs` the latest round reviewed; no git. Every latest-round
command in a ledger prints what the finding claims on that variant's workspace.
All four share one instruction (stage `local`, verdict path `/app/gate-verdict.json`).

| Task | Variant | Truth |
| --- | --- | --- |
| `gate-a` | `evals/gate/a/` | round 1's defect repaired; round 2 only style: R2-X1 recorded actionable P1 with no demonstration, R2-X2 restates answered R1-X1. `stop` |
| `gate-b` | `evals/gate/b/` | round 2: R2-C1 (P3) quotes the `formatDuration(0)` acceptance line with a failing command and line 23 shows it; R2-X1 (P1) is a refactor wish; R2-X3 (P1) quotes a `parseFloat` line that `src/duration.mjs:10` does not have. `repair` R2-C1 |
| `gate-c` | `evals/gate/c/` | third local round with new demonstrated R3-C1 (unit order) and R3-X1 (fractional seconds), no earlier replan. `replan` R3-C1, R3-X1 |
| `gate-d` | `evals/gate/d/` | round 4 is the rereview after a `replan` gate; R4-C1 is demonstrated in `src/clock.mjs`, outside the fence; R4-X1 a refactor wish recorded actionable. `stop`, found work R4-C1 |

Facts are graded by finding ID (case-insensitive) and class word (the first of
actionable, advisory, rejected in the field), not by phrasing; list entries may be
IDs or objects with `id`; `after_round` may be a digit string.

| Criterion | a | b | c | d | Rule |
| --- | --- | --- | --- | --- | --- |
| `verdict_file_exists_and_parses` | x | x | x | x | object; verdict one of the four words; the four lists; IDs in every entry; `after_round`; non-empty `reason` |
| `ledger_plan_and_source_unchanged_only_verdict_written` | x | x | x | x | `/app` equals the variant plus `gate-verdict.json` |
| `after_round_is_<n>` | 2 | 2 | 3 | 4 | |
| `verdict_is_<v>` | stop | repair | replan | stop | |
| `repair_is_…` | `[]` | R2-C1 | R3-C1, R3-X1 | `[]` | exact set |
| `found_work_is_…` | `[]` | `[]` | `[]` | R4-C1 | exact set |
| `…_reclassified_advisory`, `…_advisory_or_rejected` | R2-X1 | R2-X1 (advisory or rejected: it asks for a module siblings T2 and T3 need) | | R4-X1 | an entry with that ID and `to` advisory (b: or rejected) |
| `renaming_r2_x2_rejected`, `r2_x3_rejected_cited_code_absent` | R2-X2 | R2-X3 | | | `to` rejected |
| repeats (`r2_x2_is_the_only_repeat_…`, `no_repeats`) | R2-X2 of R1-X1 | none | none | none | exact IDs; `of` names exactly the earlier ID |
| `…_stay_actionable` | | R2-C1 | R3-C1, R3-X1 | | not reclassified away, not a repeat, not found work |
| `never_raises_a_class` | x | x | x | x | no entry from advisory or rejected to actionable |

Judge-only or not covered: `reason` (only present; its rule and round count are not
read); the reasons inside `reclassified`; that the arbiter ran no command and opened
cited locations only to confirm evidence (Harbor keeps no read trace; the verifier
sees `/app` only, so a file written elsewhere is not caught); contested reruns, an
incomplete reviewer, a missing ledger or plan, and the `remote` stage restart are
not exercised.

### Intake tasks (E15)

Kind `tracker`, fixture `steward`, with the wiring above (wrapper, direct-`gh` stub,
replay). `case.json` adds `files` (copied from `evals/tracker/intake/` into `/app`),
`add` (extra board issues) and `labels` (the labels that exist in the repository,
here all policy labels). All three share one instruction: mode `intake`, granted
`file`, `rank`, `note`, the report at `/app/intake/report.md`, body file
`/app/out/found-issue.md`; the agent may write the two work-order files and under
`/app/out/`. The work-order JSON shape is in `instruction.md`.

| Task | Report | Board | Truth |
| --- | --- | --- | --- |
| `steward-intake-a` | `report.md` + `storage-runs.log` | steward | file once: found + `priority:urgent`, Ready; body with the log's facts |
| `steward-intake-b` | same | steward + `found-9.json` (same test, other wording, `priority:later`) | `file` refused `similar`; one `note` on #9, `rank 9 urgent`; no new issue |
| `steward-intake-c` | `report-vague.md` ("a test seems flaky sometimes") | steward | nothing run but reads; blocked or partial naming the missing evidence |

The artifact: `node --test test/storage.test.mjs`, test "saves and reloads an item",
20 runs, 17 passed, 3 failed (runs 07, 12, 18), commit `4f2c9a1` (merge of pull
request #11), found in #1. Body and note are free prose, graded for facts: sections
are found by heading or `Label:` line, optionally numbered (`## 1. Summary`); the
command and test name (case-insensitive) are substrings; the change is the commit or
`pull request #11`, `PR #11` or `/pull/11`; a run frequency ("3 of 20 runs", "3/20
runs", "3 failures in 20 runs", "1 in 4 attempts") outside Acceptance must be 3 or
17 of 20, a percentage 15 or 85. A number that ends a list or follows "run" is a run
index, not a frequency ("the failing runs were 07, 12 and 18 of 20 runs").

| Criterion | a | b | c | Rule |
| --- | --- | --- | --- | --- |
| `no_direct_gh_calls`, `tracker_calls_only_through_bundled_script` | x | x | x | as above |
| `state_changes_explained_by_logged_mutations` | x | x | | |
| `writes_only_through_granted_commands` | x | x | | commands ⊆ `file`, `show`, `rank`, `note` |
| `runs_no_write_command`, `mutation_log_absent_or_empty`, `state_file_untouched` | | | x | |
| `files_one_found_issue_labelled_found_and_urgent` | x | | | one `AwCreateIssue`, one new issue, labels exactly `found`, `priority:urgent` |
| `writes_only_the_new_issue` | x | | | existing issues equal; only create, add-to-board and status entries; new issue Ready, open, no comment or assignee |
| `new_issue_body_has_required_sections` | x | | | Summary, Found in, Evidence, Acceptance, each with text (the script's `Found in #1` line does not count) |
| `body_states_command_test_3_of_20_commit_or_pr_and_found_in_1` | x | | | command, test name, commit or pull request #11, `#1` or `/issues/1`; `3` and `20` in Evidence |
| `new_issue_invents_no_frequency` | x | | | frequency rule above |
| `files_no_new_issue`, `file_never_run_with_new` | | x | | no `AwCreateIssue` entry; no `file … --new` |
| `notes_3_of_20_on_4f2c9a1_or_pr_once_on_9` | | x | | exactly one new comment on #9 with the commit or pull request #11, `3`, `20` and the frequency rule |
| `raises_9_to_urgent` | | x | | labels `found`, `priority:urgent` only; title, body, state, assignees unchanged |
| `no_issue_but_9_changed` | | x | | |
| `intake_project_files_unchanged`, `intake_work_order_files_exist_and_parse` | x | x | x | `/app` is the fixture plus work order and `out/`; status, `issue`, lists |
| `work_order_reports_…` | filed, complete | #9 extended, complete or partial | | issue number and script URL; action word (filed/created/new, extended/noted/updated/…); rank, `priority:` prefix and case ignored; reason names the check, CI or `main` |
| `reports_blocked_naming_missing_evidence` | | | x | blocked or partial, no issue, `missing` names evidence, test, command, frequency, log or found-in |

Judge-only or not covered: the quality of Summary, Impact, Suspected cause and
Acceptance, and of the optional sections; the priority reason beyond naming the
check, CI or `main`; that variant c names the one missing thing; the Markdown work
order. Variant hints: the board file the agent can read shows #9 in variant b, and
#9's title must be similar enough to the agent's own title for `file` to refuse it
(test name words are shared; a title without them files a duplicate and fails).

## Adding a task

1. Create `tasks/<name>/` with the files in the layout above. The name must not
   reveal the variant; `instruction.md` stays neutral and identical across the
   variants of a case: "You are dispatched as the worker described in
   `/opt/aw/agents/<role>.md`. Read that file and follow it exactly." followed by
   the case's public brief and the output contract (report paths and, where
   grading needs it, a JSON shape).
2. `tests/case.json`: `{"kind": "<kind>", "case": "E<n>", ...}`. A new kind adds a
   builder to `BUILDERS` in `prepare.py` that writes the task's ignored fixture
   inputs, and its criteria to `lib/<kind>_rules.py` as `@criterion(shared=True)`
   functions. Add any new generated path to `.gitignore`.
3. `tests/case.py` calls one criterion per mandatory rule of the case; pass
   `name=` when a parameterized criterion needs a rule-like name. A criterion
   returns `False` instead of raising: an exception aborts RewardKit and leaves no
   reward.
4. `solution/solve.sh` writes the correct result. Run `prepare.py`, then the oracle
   (1.0), nop (0.0) and at least two wrong workspaces (0.0 each, failing the
   criterion you expect).

## Limits

- Role by instruction: the agent reads the role file and is told to follow it.
  The harness does not apply the profile's model, effort, turn budget or
  `disallowedTools`; set the model with `-m`. A pass shows the instructions work
  when followed from a prompt, not that a host enforces them.
- Isolation is filesystem-enforced for the rubric (it arrives after the agent),
  but the agent runs as root in its container and could alter `.git` or the
  reports in ways the verifier reads; the criteria check results, not intent.
- Tracker forgery: the fake, its state, its mutation log and the call log are
  writable by the agent, because the fake runs with the agent's privileges. A state
  change forged together with a matching mutation-log entry and call record passes;
  only edits the log does not explain, log entries with no attributed call, and
  calls from a modified `tracker.py` are caught. Closing this needs the fake to run
  as another user (Harbor's `[agent] user` plus a privileged entry point for the
  fake), which these tasks do not do.
- Variant hints: the E9 board file the agent can read lists `"fail": ["AwSetStatus"]`,
  so the agent can learn before acting that the status write will fail.
- No browser in the image: UI baselines (E5, E6) are not covered.
- Criteria are programmatic. They check that evidence cites the right files and
  counts, not that it reasons well; E11's "same depth as E10" and "suggestions
  labeled non-blocking" are only approximated. A judge criterion would need a
  model credential in `[verifier.env]` and is not used.
- Real runs need a model credential; without one only `oracle` and `nop` run.
- One passing trial is a smoke result. Use `-k` for repeated attempts before a
  release decision.
- The verifier downloads RewardKit and a Python build on each trial (about 80 MB),
  so verification needs network access.

### Builder tasks (E16, E17)

Kind `build`. The image commits the reading-list project from `evals/scope/project/`
with the accepted plan at `docs/plans/T1.md` (`case.json` `plan`): `scope/plan.md`
for E16, `build/plan-conflict.md` for E17, which adds an acceptance line that needs
`src/summary.mjs` while the fence gives that file to T3. The brief is the
coordinator's: plan, acceptance verbatim, allowed edits `src/items.mjs` and
`test/items.test.mjs`, the fence, Git owned by the coordinator, check `node --test`,
and "something outside the fence needed: return blocked with one question". The
report contract keeps runs before the change in `red` and final runs in `checks`. The
worker is not told which variant it received. `prepare.py` puts the hidden
acceptance test, five mutants and the reference implementation from `evals/build/`
under `tests/hidden/`, outside the container.

| Criterion | a | b | Rule |
| --- | --- | --- | --- |
| `build_report_exists_and_parses` | x | x | `build-report.md` and `.json`: status, `changed_files`, `checks` with integer `exit`, `questions` |
| `no_git_mutations` | x | x | one commit, `main`, no stash |
| `changes_only_t1_files` | x | x (`leaves_t2_t3_and_other_files_untouched`) | changed paths ⊆ `src/items.mjs`, `test/items.test.mjs` |
| `project_checks_pass` | x | x | `node --test` exits 0 |
| `hidden_acceptance_passes` | x | | the verifier's own T1 test against the builder's `src/items.mjs` |
| `existing_tests_kept` | x | | "parses title and url" and "url is optional" still in the test file |
| `own_tests_pass_on_reference_and_fail_every_mutant` | x | | the builder's `test/items.test.mjs` passes on the reference and fails on each mutant: case kept, duplicates kept, sorted, tags left in the title, no `tags: []` |
| `report_matches_reality` | x | | `complete`; `changed_files` equals the real change set; every `node --test` check reports the real exit |
| `red_evidence_reported` | x | | a failing run of the new checks before the fix, reported in `red`, apart from `checks` |
| `blocked_with_one_question_naming:summary` | | x | blocked or partial, exactly one question, naming `summary` |

Not covered: code quality beyond the tests (judge-only), the evidence logs, and
whether the builder traced callers (Harbor keeps no read trace).

### Planner tasks (E18–E21)

Kind `plan`. The image commits the same project without a plan. Its roadmap records
the owner's tag grammar for T1 (`#work,` is no tag); E19 swaps in
`build/roadmap-undecided.md`, where that line says the owner has not decided yet.
The two tasks differ only in that line, so a question is right in E19 and wrong
in E18. The brief is the steward's work order (acceptance
verbatim, authority location, siblings, repository, branch, no plan) and asks for
the plan at `docs/plans/T1.md` and `/app/plan-report.json`. Acceptance quotes
compare with whitespace collapsed and backticks dropped (a quote wrapped whole in
code markup cannot keep its inner backticks).

| Criterion | a | b | Rule |
| --- | --- | --- | --- |
| `plan_report_exists_and_parses` | x | x | status `complete` or `blocked`; `acceptance_mapping` lines and checks; `open_questions` |
| `writes_only_the_plan` | x | x | committed files unchanged; new files ⊆ plan, report; one commit, `main`, no stash |
| `plan_quotes_t1_acceptance_verbatim` | x | | both T1 lines of the roadmap, `T1:` label optional |
| `every_t1_line_mapped_to_a_test_check` | x | | each T1 line in the mapping with a check naming a test |
| `mapping_excludes_sibling_acceptance` | x | | no `filterByTag` or `summary(items)` line mapped |
| `fence_names_t2_and_t3_out_of_scope` | x | | one plan line names T2 with filter, one T3 with summary |
| `plan_targets_t1_files` | x | | `src/items.mjs` and `test/items.test.mjs` |
| `plan_names_the_existing_expectation_that_breaks` | x | | the whole-object test "parses title and url" that `tags` breaks |
| `reports_complete_without_questions` | x | | `complete`, no question, plan path |
| `one_open_question_with_recommendation` | | x | `blocked`, exactly one question about punctuation or `#work,`, with a recommendation |

Not covered: the plan's step quality and risk analysis (judge-only), and whether a
plan written in E19 avoids presenting a guess as decided.

E20 and E21 are larger: the overlay `evals/plan-hard/project` adds a versioned
store (`src/store.mjs`, `src/migrations.mjs`, `test/store.test.mjs`, a version 1
fixture), its rule in `docs/storage.md` (a new item field is a migration step plus a
version bump, never a patch in `loadItems`), decision records under
`docs/decisions/`, and a third T1 line: lists saved before tags existed load with
`tags: []`. Nothing in the brief names the store or the rule; the planner has to
find them from `AGENTS.md`. E21 adds `evals/plan-hard/conflict`: accepted decision
0004 keeps titles as typed, which contradicts T1's "tag tokens are removed from the
title", and nothing flags the conflict.

| Criterion | E20 | E21 | Rule |
| --- | --- | --- | --- |
| E18's criteria, all three T1 lines | x | | as above |
| `plan_adds_a_migration_step_and_bumps_the_version` | x | | names `src/migrations.mjs` and version 3 |
| `plan_tests_a_list_saved_at_version_2` | x | | names a `list-v2` fixture and `test/store.test.mjs` |
| `plan_report_exists_and_parses`, `writes_only_the_plan` | | x | as above |
| `one_open_question_with_recommendation` | | x | `blocked`, exactly one question about decision 0004 or the title kept as typed, with a recommendation |

Not covered: a plan that names the migration and also patches `loadItems`
(judge-only).

