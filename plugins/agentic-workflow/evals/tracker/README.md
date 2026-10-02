# Tracker fake

A stand-in for `gh` that lets `scripts/tracker.py` run against a JSON board with
no network. `tests/test_tracker.py` and tracker evals use it.

## Run

Copy `state.json` first; the fake rewrites the file it is given.

```sh
cp plugins/agentic-workflow/evals/tracker/state.json /tmp/board.json
export AW_TRACKER_GH=$PWD/plugins/agentic-workflow/evals/tracker/gh
export AW_FAKE_GH_STATE=/tmp/board.json
cd plugins/agentic-workflow/evals/tracker   # tracker-policy.json is read from the cwd
python3 ../../scripts/tracker.py next
python3 ../../scripts/tracker.py --policy tracker-policy.json claim 6 --branch feat/s1.3-search
```

| Variable | Meaning |
| --- | --- |
| `AW_TRACKER_GH` | Executable `tracker.py` runs instead of `gh`. |
| `AW_FAKE_GH_STATE` | Board state file. Mutations change it in place. |

Every mutating call appends one JSON line `{"op", "variables", "ok"}` to
`<state path>.log`, including a call failed through `fail` (`"ok": false`), so a
test can prove what was written and that nothing was retried. Reads are not logged.

## State

```json
{"viewer": "dev",
 "repo": "acme/shop",
 "fail": ["AwComment"],
 "labels": ["roadmap", "tracer-bullet", "found", "priority:urgent", "priority:soon", "priority:later"],
 "items": [{"number": 1, "title": "S1.1 — Title", "state": "OPEN", "status": "Ready",
            "labels": ["roadmap"], "assignees": [], "blocked_by": [2], "parent": null,
            "milestone": "Stage 1", "body": "...", "open_prs": [20], "comments": ["..."]}]}
```

- `viewer`: login of the authenticated user (`@me`).
- `repo`: optional, default `acme/shop`; reported as each issue's repository.
- `fail`: optional; these operations exit 1 with `gh: Resource not accessible by
  personal access token (<op>)` on stderr.
- `labels` (top level): optional; the labels that exist in the repository. A
  lookup of any other name returns `null`, as GitHub does. Absent: every name resolves.
- `status`: board column, `null` when the issue is not on the board, `""` when it
  is on the board without a column (after `AwAddItem`).
- `state`: `OPEN` or `CLOSED`. `parent` makes the issue a sub-issue; sub-issues are
  listed by number. A blocker missing from `items` counts as open.
- `open_prs`: open pull requests that close the issue.
- Issues created by the fake get the next free number above every issue and pull
  request number, and `type` when an issue type was requested.
- For `init` only, all optional: `boards` (default one board `{"owner": <repo
  owner>, "number": 1}`), each with `title`, `columns` (Status options, default as
  below), `closed` and `linked` (default `true`; an unlinked board is found only by
  `--project`); `default_branch` (`main`); `merge_methods` (default all of `merge`,
  `squash`, `rebase`); `merge_queue` (`false`).
- `issue_types`: optional, default Task, Bug, Feature.

The board's single-select field is always `Status`, with options Backlog, Ready,
In progress, In review, Blocked, Done; any other field name fails as GitHub does
(`Could not resolve to a Unions::ProjectV2FieldConfiguration with the name <name>`).

## Operations

Names usable in `fail`. All go through `gh api graphql --input -`, except
`AwRepoView`: `gh repo view --json nameWithOwner`, answered with `repo`.

| Operation | Kind | Used by |
| --- | --- | --- |
| `AwRepoView` | read | `init` without `--repo` |
| `AwInit` | query | `init` (repository settings, labels by alias, linked or named boards) |
| `AwItems` | query | `next`, `audit` (project items, 100 per page) |
| `AwComments` | query | `next` (comments of in-flight bullets, aliased per issue) |
| `AwIssue` | query | `show`, `bullets`, `claim`, `plan`, `set`, `file` (repeat), `rank`, `note` |
| `AwRepo` | query | `file`, `rank` (repository, issue types, found and priority labels by alias) |
| `AwOpenIssues` | query | `file` (open issues for the similarity check, 100 per page) |
| `AwCreateIssue` | mutation | `bullets`, `file` |
| `AwAddItem` | mutation | `bullets`, `claim`, `set`, `file`, `rank` (issue not on the board) |
| `AwSetStatus` | mutation | `bullets`, `claim`, `set`, `file`, `rank` |
| `AwAssign` | mutation | `claim` |
| `AwComment` | mutation | `claim`, `set --comment`, `note` |
| `AwSetBody` | mutation | `plan` |
| `AwAddLabels` | mutation | `rank` |
| `AwRemoveLabels` | mutation | `rank` |

## Sample board

`state.json` with `tracker-policy.json` and `ROADMAP.md` (the authority and order
file): `next` offers S1.1.T2 (#4, next bullet of a started card), then S1.3 (#6)
and S1.8 (#11, unlisted, last). It skips the epic (#1), S1.2 (blocked by #2), S1.4
(assigned), S1.5 (open pull request), S1.6 (Backlog) and S1.7 (in progress without
bullets); no bullet is in flight. `audit` reports S1.2 `startable_but_blocked` and S1.9 `closed_not_done`.
The policy enables found issues (`found` label, `priority:urgent|soon|later`); the
sample board has none.

`steward/state.json` and `steward/ROADMAP.md` are the board and authority file of
the steward eval cases (E7–E9).
