---
name: aw-eval
description: Evaluate changes to agent skills using isolated behavioral scenarios, held-out acceptance criteria and evidence from actual actions. Use for skill development, not routine delivery.
---

# Evaluate a skill change

Read [the eval scenarios and protocol](../../references/evals.md). This is an
optional skill-development tool; no Python runner, graph or paid eval platform is
required. Do not run it automatically during ordinary planning or delivery. The
numbered steps are the prose protocol for E1–E6; E7–E21 run as Harbor tasks (below).

1. Identify the candidate plugin path/revision and the behavior being changed.
   Choose the smallest relevant scenarios. Include a known-good control for QA.
   Use the previous plugin revision as baseline when comparison is requested;
   never modify the user's installed cache to switch versions.
2. Prepare a disposable project outside the user's working repository, following
   the scenario setup. Copy the candidate plugin to a separate test bundle, excluding
   `skills/aw-eval`, `references/evals.md` and `evals/`. Check that target skills and
   their references do not link to evaluator material. Supply the worker only the
   test project and sanitized bundle paths, never the original package/rubric path.
   Preserve the same inputs for baseline and candidate. Use available host tools;
   record missing browser/delegation capabilities. Use filesystem restrictions when
   available; a scoped prompt alone is not a technical filesystem sandbox.
3. Dispatch the task to a fresh native agent with the scenario's public prompt,
   sandbox path and exact SKILL.md path in the sanitized bundle (for a role case,
   the role's `agents/<role>.md` instructions, model and effort instead). Instruct it to load that skill
   and referenced guidance. Do not give it this evaluator skill, scoring rubric,
   planted-defect list or your conversation history. Audit reads for rubric access;
   contamination makes a run inconclusive. If isolated dispatch is
   unavailable, provide a separate-session handoff and mark execution not run;
   do not simulate a worker and score your own prediction as a result.
4. Observe actual tool calls, files, checks and final output. Stop at the scenario
   boundary, not after the worker's unverified claim of success. The eval sandbox
   grants no production, publication or messaging authority. A bounded evaluator
   timeout protects the test run; it is not a delivery repair-attempt policy.
5. Score each criterion pass/fail/not-observed with a concrete trace or artifact
   reference. A mandatory criterion that fails fails the case. Missing capability
   or incomplete evidence makes the run inconclusive. Independent grading is
   preferred; the implementation agent cannot certify its own result.
6. Report results in a short Markdown table: case, skill revision, provider/model,
   outcome, evidence, interventions and tool limitations. Compare identical cases
   when a baseline ran; otherwise state that no comparison was measured. Start
   with one smoke run; repeat promising changes before relying on them. Turn real
   failures into new cases without teaching the skill the specific answer.

## Role and loop cases with Harbor (E7–E21)

These cases are [Harbor tasks](../../evals/harbor/README.md) whose verifiers score
the files, exit states and logs a run leaves; steps 2–5 above are built in. Harbor
(with Docker and uv) is an optional development tool: ordinary delivery and the
other skills never need it. E1–E6 keep the steps above.

1. `H=plugins/agentic-workflow/evals/harbor; python3 $H/prepare.py` after every
   plugin or fixture change; it rebuilds the sanitized bundle and fixtures.
2. Sanity: `harbor run -p $H/tasks -a oracle -o <jobs> -y` must score 1.0 per task
   and `-a nop` 0.0; otherwise the task, not the agent, is broken.
3. Real run: `harbor run -p $H/tasks [-i '<task glob>'] -a claude-code -m <model>
   --env-file <credential file> -k <attempts> -o <jobs> --job-name <name>`. Never
   print the credential file.
4. Per trial read `verifier/reward.json` (1.0 or 0.0) and
   `verifier/reward-details.json`; criteria with `value` below 1 are the broken
   rules. A trial without `reward.json` is a harness error, not a score.
5. Baseline versus candidate: check out each plugin revision in its own disposable
   worktree (copy the current `evals/` into one that predates these tasks), run
   `prepare.py` and the same command with the same agent, model, `-k` and task
   filter in each, then compare pass rates and broken rules per task.

Keep raw evidence outside the package and a concise result note in the project's
chosen location. Do not claim these behavioral evals passed because helper unit
tests passed. Do not claim isolation from instructions alone; verify dispatch.
