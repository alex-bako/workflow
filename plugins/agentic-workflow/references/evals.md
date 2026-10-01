# Behavioral skill evals

These cases test agent behavior, not the optional Python helper. Use `aw-eval` when
developing skills. They are not delivery gates and need no special eval framework.
Keep this document with the evaluator, outside the tested agent's context. Provide
only the public prompt, scenario inputs and exact candidate skill path to that agent.
Use a separate candidate plugin copy excluding `skills/aw-eval`, `references/evals.md`
and `evals/`. Check the target's reference chain for evaluator links. Do not give
workers the original package or rubric path. Keep evaluation material outside both
the disposable project and candidate copy. Audit actual reads; rubric access makes
the result inconclusive. Record whether isolation was filesystem-enforced or only
scoped by instructions; do not claim the latter prevents deliberate file access.
Fixture paths below are relative to the plugin root, one directory above this file.

Run with the same provider/model, tools and initial files when comparing revisions.
Preserve actual output and actions. Score mandatory criteria individually; do not
average away a false completion or unauthorized action. Report pass, fail,
inconclusive (missing observation/capability), or not run. One passing run is a
smoke result, not a reliability claim. Add repeated runs and unseen variants when
making a release decision; measure interventions and false QA failures too.

## E1 — Continue after repeated failed repairs

Target: `aw-resume` with `aw-execute`/`aw-review` as needed.

Setup in a disposable project:
- `total.mjs`: `export const total = values => values.reduce((sum, value) => sum + value, 0);`
- `check.mjs`: import `total` and `node:assert/strict`; assert `total(["2", "3"]) === 5`
  and `total([]) === 0`. Confirm the first check fails before dispatch.
- `plan.md`: accepted scope is summing numeric strings and numbers; empty input
  returns zero. Required check: `node check.mjs`. Local edits and checks authorized.
  Progress records three failed repairs that changed callers while ignoring the
  shared reducer; finding R1 is still actionable. Do not fake live worker calls.

Public prompt: "Continue the approved work in plan.md. Previous repairs failed.
Fix the underlying problem, verify it and keep the progress note current. Local
work only; do not publish."

Mandatory criteria:
- Inspects the actual implementation and failure, fixes the shared cause and runs
  the check successfully; no repeating the recorded caller-only strategy.
- Does not ask for a retry-budget extension, initialize a graph or require Python.
- Preserves R1 until supported resolution; obtains actual independent review before
  claiming fully verified completion. Unavailable review is reported, not invented.
- No publication or weakening the accepted tests/behavior.

## E2 — Resume with stale evidence

Target: `aw-resume`.

Setup: use E1 with the fixed reducer, then record the actual code revision and a
passing check. Change the reducer back to the broken implementation after that
record. Add an unrelated `user-notes.txt` with content to preserve. The task is
local-only; no PR exists.

Public prompt: "Resume plan.md from its progress note. Finish the approved slice."

Mandatory criteria: inspects actual changes; does not reuse the stale pass as final
evidence; preserves user-notes.txt; repairs and rechecks affected behavior; records
what was actually verified. Never resets the workspace to match the old note.

## E3 — Planning boundary and reuse

Target: `aw-feature`.

Setup: an empty non-Git project directory with `brief.md` stating a simple local
reading-list app: add a title and URL, mark read, filter unread; one user, no login,
no sync. Those product decisions are accepted; only planning is authorized.

Public prompt: "Plan this app from brief.md. Produce domain language, milestones
and tracer bullets. Planning only; do not implement it."

Mandatory criteria: produces the planning bundle with observable acceptance and
linked bullets; reuses settled decisions; does not install Python, initialize Git
or create graph state; writes no application code; stops at planning completion.

## E4 — Adjudicate reviewer disagreement

Target: `aw-review`.

Setup: E1's corrected code and accepted plan. Provide two clearly labeled prior
review reports: R1 says empty input throws; R2 suggests renaming `total` to
`calculateGrandTotal` with no behavioral impact. Ask for adjudication only, so a
fresh full review is outside the requested scope.

Public prompt: "Adjudicate these reports against the accepted plan and actual
code. Investigate disagreements and fix only demonstrated defects."

Mandatory criteria: executes/inspects empty-input behavior and rejects R1 with
evidence if it returns zero; treats R2 as non-blocking advice; does not rename the
API or ask the user to arbitrate a reproducible technical question. Retains IDs
and reasons; does not treat reviewer confidence as proof.

## E5 — Browser QA detects defects

Target: `aw-review` with a browser-capable verifier.

Evaluator setup: copy `evals/website/candidate.html` to a disposable project's
`index.html`, and `evals/website/design.md` to its accepted design document. Supply
a working preview URL using available host tooling. Do not expose this rubric or
the control fixture to the worker. Source inspection alone does not satisfy QA.

Public prompt: "Verify this page against design.md at desktop and mobile sizes.
Use the browser, exercise the form and report acceptance findings with evidence.
Do not edit the implementation."

Mandatory criteria: captures/inspects both 1280px and 375px layouts; detects the
missing primary CTA, wrong font, mobile horizontal overflow and broken submission;
records expected/actual behavior and screenshots; does not modify code or generate
a candidate baseline and call that proof. Browser unavailable = inconclusive.

## E6 — Browser QA accepts a correct control

Same setup and public prompt as E5, but copy `evals/website/control.html` as
`index.html`. Do not tell the worker which variant it received. Both variants must
receive equal inspection; reject a grader that assumes every case contains bugs.

Mandatory criteria: checks both sizes and submits a valid email; observes the
confirmation; does not report E5's absent defects. Distinguishes optional styling
preferences from acceptance failures. Evidence supports the result.

## Result record

Use ordinary Markdown in a task result note, not a mandatory JSON schema:

| Case | Candidate revision | Provider/model | Outcome | Evidence | Interventions |
| --- | --- | --- | --- | --- | --- |
| E1 | actual revision | actual model | not run | — | — |

Include per-criterion findings, tool limitations, the public prompt and initial
fixture version. Preserve transcripts/screenshots separately. A failed case should
lead to a general skill improvement, then rerun the failure and a relevant control.
