# Issue tracker: policy, script and steward

Use when project work is tracked as issues on a board (GitHub Issues with a
Projects board) and delivery should take "the next issue". The authority file
(roadmap or milestones) owns scope, dependencies and order. The tracker mirrors
it and records who works on what. Where they disagree the authority file wins
and the difference is reported as drift, never silently repaired.

## Units

The tracker repository holds the issues. Code may live elsewhere: a card names the
code repositories it lands in, and a bullet can need a pull request in more than
one of them.

- **Card:** one tracked roadmap item, one issue. Its body lists tracer bullets.
- **Bullet:** one tracer bullet, a sub-issue of its card, created when the card is
  first picked. A bullet is the unit of planning, implementation, review, pull
  request and merge. Its issue body holds the accepted plan.
- **Found issue:** unplanned work recorded while delivering (a flaky test, a defect
  outside the scope fence). A standalone issue with the found label and one
  priority label. It is a work item like a bullet, with its plan in its body. Its
  id is its title.

## Tracker policy

A project-owned JSON file, changed only on the user's decision. Default path
`tracker-policy.json` in the project root; otherwise pass `--policy`. It is the
standing authorization for tracker writes and, where it says so, for merge. No
policy: no tracker writes. `init` drafts one from the repository and its board;
the user confirms the draft before it is used.

```json
{
  "repo": "owner/name",
  "project": {"owner": "owner", "number": 1, "status_field": "Status"},
  "states": {"backlog": "Backlog", "ready": "Ready", "in_progress": "In progress",
             "in_review": "In review", "blocked": "Blocked", "done": "Done"},
  "items": {"label": "roadmap", "exclude_labels": ["epic"], "startable_states": ["ready"]},
  "bullets": {"label": "tracer-bullet", "pattern": "^\\d+\\. `(?P<id>[^`]+)` — (?P<text>.+)$",
              "issue_type": "Task"},
  "authority": "docs/roadmap/MILESTONES.md",
  "order": {"file": "docs/roadmap/MILESTONES.md", "start": "### Next up", "end": "### ",
            "id_pattern": "\\b[A-Z]\\d+\\.\\d+\\b"},
  "assignee": "@me",
  "repos": {"default": "app", "named_by": "the card's Repos line; a card without one uses the default",
            "known": {"app": {"repo": "owner/app", "base": "main"},
                      "core": {"repo": "owner/core", "base": "main", "merge": "queue"}}},
  "found": {"label": "found", "issue_type": "Bug",
            "priorities": {"urgent": "priority:urgent", "soon": "priority:soon", "later": "priority:later"}},
  "merge": {"allowed": false, "method": "rebase"},
  "notes": ["Free-text project conventions the steward repeats in its work order."]
}
```

| Key | Meaning |
| --- | --- |
| `states` | Board column for each workflow state. All six keys are required. |
| `items.label` / `exclude_labels` | Which issues are cards, and which are never handed out. |
| `items.startable_states` | States a new card may be picked from. Add `backlog` when blocked-by links mirror the authority file exactly. |
| `bullets.pattern` | Multiline regex with groups `id` and `text`, matched against the card body. |
| `bullets.issue_type` | Optional issue type for bullet sub-issues. |
| `authority` | Optional. The roadmap or milestones file that owns scope and order. |
| `order` | Optional; without it cards are taken in issue-number order. Priority order: first appearance of each card id between `start` and the next line starting with `end`. Paths resolve against the policy file's directory. Unlisted cards sort last, by issue number. |
| `repos` | Optional, for products spread over several repositories. `repo` above is where the issues live; `repos.known` lists the code repositories a bullet may land in, each with its base branch and, when it differs, its merge method (`rebase`, `squash`, `merge`, or `queue` for a merge queue). The script reads a card's repositories from the first `Repos:` or `Repositories:` line in its body or its authority section (for example `**Repos:** cloud, adoc`), else `default`. `named_by` tells people how cards name them. No local paths: checkouts differ per machine and are found by remote URL. |
| `found` | Optional; enables found issues. `label` marks them, `priorities` names the label for each of the three ranks (all three required), `issue_type` is optional. The labels must exist in the tracker repository. |
| `merge.allowed` | `true` lets the delivery loop merge under the [loop's merge conditions](loop.md#merge). Absent or `false`: never merge. |

## Script

```sh
python3 <plugin>/scripts/tracker.py [--policy <path>] <command>
```

Python standard library only. Every GitHub access goes through the `gh` CLI the
user authenticated; the script holds no credentials. `AW_TRACKER_GH` replaces the
`gh` executable for tests and evals. Output is one compact JSON object on stdout
that repeats the exit code as `exit` and `ok`, so an agent that sees only stdout
still sees it. Exit 0 success, 2 usage or policy error, 3 refused by a rule below
(`reason` in the output), 4 `gh` failed (`message`, also on stderr, and the
`failed_write`; nothing is retried). An error after some writes went through lists
them under `writes`. A refused `claim` carries `next_candidates`, as `next` returns
them. N is an issue number, or for `show`, `work-order` and `claim` also a card or
bullet id that names exactly one issue. Every
write command reads current state first and skips writes that already hold, so a
repeated command is safe. Agents never hand-write tracker queries.

| Command | Effect |
| --- | --- |
| `init [--repo OWNER/NAME] [--project OWNER/NUMBER] [--out PATH]` | Read-only on the tracker. Draft a policy for a repository that has none and write it to PATH (default: the `--policy` path). Refuse `exists` when the file exists, `ambiguous` (listing the `choices`) when the repository has several open boards and none is named, `no_board` when it has none. A board without a single-select Status field is a usage error. Output: `policy` (the path), `detected` and `missing`. See [first use](#first-use). |
| `next [--limit N]` | Read-only. `candidates` (default 3, at least 1) in order, each card or bullet with the `authority` section of its card; `in_flight` (bullets and found issues in progress, in review or blocked, with card, branch and phase from the claim comment); `skipped` counts by reason. |
| `show N [--body]` | Read-only. Number, id, title, kind, state, status, assignees, labels, parent, blockers, linked pull requests, and the card's bullets in order: each listed in the body, with its sub-issue `number` and status once `bullets` created it (`null` before). |
| `work-order N` | Read-only. Every fact of the [work order](#steward) for N in one call: `kind`, the card or found `item`, the `bullet` this pass delivers, `siblings_out_of_scope`, the `authority` section verbatim (for a found issue, or any item when the policy has no authority file, the issue body under `issue` and `text`), `repositories`, `dependencies` with state, the last `claimed` branch and phase, `plan_published`, `claim` (the `number` to claim first: the found issue or bullet itself, a started card's current bullet, else the card; `allowed`, else the `reason` `claim` would refuse with), `alternates` with their authority sections, `drift` touching N, `policy_notes`. |
| `bullets N` | Refuse when card N is taken or blocked. Else create its missing bullet sub-issues from its body: title `<id> — <summary>`, bullet text, card link, empty plan section, the card's milestone, the bullet label; added to the board as backlog. A rerun finishes an interrupted add: a bullet on the board without a status gets backlog. |
| `claim N [--branch B] [--phase P]` | Re-read N; refuse when taken or blocked, and for a bullet also when its parent card is closed, assigned to someone else or excluded. Else assign, set in progress (and the parent card when N is a bullet), post one claim comment. A repeated claim by the same assignee writes nothing. Branch and phase are single tokens without whitespace or angle brackets. |
| `plan N --file F` | Replace the section between `<!-- aw:plan:start -->` and `<!-- aw:plan:end -->` in N's body with F, appending the section when absent. Refuse `too_large` when the resulting body exceeds 65,000 characters; a plan file that itself contains a marker is a usage error. |
| `set N <state> [--comment T]` | Set the board state; optional single comment. Never closes or reopens. |
| `file --title T --body-file F --priority P [--found-in N] [--type TYPE] [--new]` | Refuse `similar` (listing the matches) when an open issue has a similar or identical title, unless `--new`. Else create a found issue: title, body from F plus a `Found in #N` line, the found label and the label of rank P, the issue type; added to the board as ready. An open found issue with the same title and the same resulting body is this command run before: it is only completed, `created: false`. |
| `rank N <priority>` | Replace the priority label of found issue N; put it in the ready column when it has no column or sits in backlog. Refuse `not_found` when N lacks the found label, `taken` when N is closed. |
| `note N --file F` | Post F as one comment on N. An identical existing comment is not posted again. |
| `audit` | Read-only. Drift list with codes. |

### Selection rule (`next`)

1. **Next bullet of a started card.** A card with bullet sub-issues is started. Its
   first open bullet, in bullet id order (`T2` before `T10`), is a candidate when
   every earlier bullet is closed, the bullet has no open blocker and is neither
   assigned nor in progress or in review, and the card is not assigned to someone
   other than the policy assignee.
2. **New card.** Open, state in `startable_states`, no open blocker, no assignee,
   no open linked pull request, no bullet sub-issue, no excluded label.
3. **Found issue.** Open, the found label, exactly one priority label, state in
   `startable_states`, no open blocker, no assignee, no open linked pull request.
4. Order: `urgent` found issues; next bullets of started cards; `soon` found
   issues; new cards; `later` found issues. Cards in policy order, found issues
   oldest first. Each candidate carries its `kind`: `bullet`, `card` or `found`.

A started card whose next bullet is taken yields nothing: bullets of one card run
in sequence. A card in progress without bullet sub-issues is someone else's work
and is skipped. Cards and bullets are told apart by label, since a card may itself
be a sub-issue of an epic. `skipped` reasons: `blocked`, `assigned`, `open_pr`,
`excluded_label`, `not_startable`, `in_progress_without_bullets`, `bullet_taken`,
`bullets_done`, `untriaged` (a found issue without exactly one priority label).

### Refusals

`taken`: closed; in review or done; assigned to anyone but the policy assignee; or
in progress without being assigned to the policy assignee. `blocked`: an open
blocker, or an earlier bullet of the same card still open. `not_a_card`,
`no_bullets` (pattern matched nothing), `too_large`, `similar`, `not_found`. A
refusal writes nothing. Titles are similar when the words of three or more letters
they share, compared without case, number at least half the average word count of
the two titles. Only titles are compared, against every open issue.
Policy and usage errors, including a state whose board column does not exist, are
detected before the first write. So is a found or priority label missing from the
repository; the message names the label to create.

### Drift codes (`audit`)

`closed_not_done`, `done_but_open`, `startable_but_blocked` (in the ready column
with an open blocker), `in_progress_unassigned`, `bullet_open_card_closed`,
`not_on_board` (a bullet of a card on the board, or a ranked open found issue; a
card missing from the board is not visible to the script), `found_untriaged` (an
open found issue, on the board or not, without exactly one priority label).

## First use

`init` asks the tracker what it can know and leaves the rest to the user. Without
`--repo` it uses the repository of the current directory.

- **Detected:** the repository; its board and Status field; the six states, matched
  to the board's columns by name without case, spaces or hyphens (`ready` also
  matches "To do" and "Todo", `in_progress` "Doing", `in_review` "Review"); the
  default branch and the merge method the repository allows (`queue` when the
  default branch has a merge queue) as the single entry of `repos`; which of the
  labels the draft names exist; the issue types.
- **Defaults the user reviews:** `items.label` `roadmap`, `startable_states`
  `["ready"]`, `bullets.label` `tracer-bullet`, a bullet pattern for a numbered
  list (`^(?P<id>\d+)\. (?P<text>.+)$`), the `found` block with its label and
  three priority labels, `assignee` `@me`. `authority` and `order` are left out:
  without them cards are taken in issue-number order and the steward confirms a
  card from its own body.
- **Always:** `merge.allowed` is `false`. Only the user turns it on.
- **Not detectable, review first:** which label marks a card and which labels are
  never handed out (`exclude_labels`, for example a parent or epic label), and how
  the card body lists its bullets. The default pattern gives bullets the bare
  numbers of the list as ids.
- **`missing`:** every state without a matching column (the user adds the column on
  the board), every label that does not exist (with the `gh label create` command),
  and a note when no open issue carries `items.label`.

The draft is the user's to edit and confirm. Nothing is written to the tracker,
and the loop makes no tracker write until the user has confirmed the policy and
`missing` is empty or accepted.

## Steward

`aw-product-owner` is the only role that runs write commands, and only those the
brief grants. Its tracker writes are assigned output, not external messages. It
does not dispatch other agents; it returns a work order to the coordinator.

| Mode | Commands | Returns |
| --- | --- | --- |
| `next` | `next`, then `work-order` for the first candidate | Work order for the first candidate that the authority file (else its own body) confirms, plus alternates, drift and `in_flight`. |
| `claim` | `work-order`. New card: `claim` the card, then `bullets`, then `claim` its first bullet. Started card: `claim` the bullet. Found issue: `claim` it. | Claimed work item, or the next candidate from the refusal's `next_candidates` when the first command is refused. |
| `plan` | `plan`, then `set in_progress` with a "plan published" comment | Bullet issue carrying the accepted plan. |
| `sync` | `set` | One transition: pull request opened, merged, blocked on a named decision or found issue, resumed after it, card finished. |
| `intake` | `file`, `rank`, `note`, `show` | One found issue filed, or an existing one extended and ranked, with the reason for its priority. |
| `audit` | `audit` | Drift, grouped, with the authority line for each. |

Work order fields: kind (bullet, card or found), id, issue URL, card URL, title, authority location
(file and heading; the issue for a found issue or a policy without an authority file), the code repositories the card names (each with repository,
base branch and merge method from the policy), dependencies and their state, acceptance lines verbatim, the
sibling bullets (out of scope), branch name, existing plan path or none, next
step, tracker writes made and refused, drift seen, policy notes.

### Found issues

The steward owns found issues from report to queue: it collects what the issue
needs, files it once and ranks it. The brief carries the observation and the
evidence artifacts; the steward does not run checks itself. It writes the body
file with these sections, then runs `file`:

The title names the failing test, check or command verbatim, so the same problem
filed again is refused `similar`.

- **Summary:** one sentence, the observable problem.
- **Found in:** work item, pull request or commit, stage, date.
- **Evidence:** exact command, output excerpt, how often it happens ("3 of 20
  runs"), first seen, environment.
- **Impact:** what it blocks or puts at risk.
- **Suspected cause:** labeled as an assumption; "unknown" is acceptable.
- **Acceptance:** verifiable lines ("the test passes 50 consecutive runs").
- **Repositories:** one line, `Repositories: cloud, adoc`, naming the code
  repositories it touches from the policy's `repos`.
- **Priority:** the rank and the reason.

Summary, Found in, Evidence and Acceptance are required; without them the steward
returns blocked with the one thing missing instead of filing a vague issue. On
`similar` it reads the matches with `show`: the same problem gets the new evidence
through `note` and, when warranted, a new rank; a different problem is filed with
`--new`. An untriaged found issue filed by a person is handled the same way: read
it, add what is missing with `note`, `rank` it.

Rank: `urgent` when the main branch or its required checks are broken or
unreliable, when data or security is at risk, or when it blocks work in flight;
`soon` for a real defect or debt that will hurt the next cards; `later` for the
rest. The user reorders by changing the label; the steward never lowers an
existing rank. A found issue has no authority section: the steward confirms it
from its own body (Acceptance present).

The steward never edits the authority file, plans, source, card bodies, titles,
dependency or hierarchy links (beyond `bullets`), labels (beyond `file` and
`rank`) or milestones; never closes or reopens an issue; never touches pull requests, branches or Git state. Issues are
closed by the pull request that delivers them. A refused or failed write is
reported with the exact command and output and is not worked around.
