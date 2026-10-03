#!/usr/bin/env python3
"""Issue tracker steward script. Contract: references/tracker.md.

python3 tracker.py [--policy PATH] init|next|show|work-order|bullets|claim|plan|set|file|rank|note|audit ...

Every GitHub access is one named GraphQL operation run through `gh api graphql`, except
`init` resolving the current repository with `gh repo view` (AW_TRACKER_GH replaces `gh`).
Output: one compact JSON object on stdout; it repeats the exit code as `exit` (and `ok`).
Exit 0 ok, 2 usage/policy, 3 refused (`reason`), 4 gh failed (stderr passed through).
"""
import argparse
from collections import Counter
import functools
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

STATE_KEYS = ("backlog", "ready", "in_progress", "in_review", "blocked", "done")
PLAN_START, PLAN_END = "<!-- aw:plan:start -->", "<!-- aw:plan:end -->"
PLAN_RE = re.compile(re.escape(PLAN_START) + r".*?" + re.escape(PLAN_END), re.S)
CLAIM_RE = re.compile(r"<!-- aw:claim branch=(\S*) phase=(\S*) -->")
MAX_BODY = 65000
SKIP_REASONS = ("blocked", "assigned", "open_pr", "excluded_label", "not_startable", "in_progress_without_bullets",
                "bullet_taken", "bullets_done", "untriaged", "open_decisions")
PRIORITIES = ("urgent", "soon", "later")
SECTION_CAP = 120  # ponytail: lines of one authority section in the output; raise when cards outgrow it

# ponytail: first:N ceilings (50 blockers, 50 sub-issues, 20 labels); paginate those when a project outgrows them.
STATUS = "fieldValueByName(name:$field){... on ProjectV2ItemFieldSingleSelectValue{name}}"
ISSUE = ("number title state repository{nameWithOwner} labels(first:20){nodes{name}} assignees(first:10){nodes{login}} "
         "parent{number state} blockedBy(first:50){nodes{number state}} "
         "closedByPullRequestsReferences(first:10,includeClosedPrs:false){nodes{number state}}")
SUB = "number title state labels(first:20){nodes{name}} assignees(first:10){nodes{login}}"
PROJECT = ("repositoryOwner(login:$powner){... on ProjectV2Owner{projectV2(number:$pnumber){id "
           "field(name:$field){... on ProjectV2SingleSelectField{id options{id name}}}")
WHO = "viewer{id login} who:user(login:$login) @include(if:$named){id login} "
Q_ITEMS = ("query AwItems($powner:String!,$pnumber:Int!,$field:String!,$after:String,$login:String!,$named:Boolean!){"
           + WHO + PROJECT +
           " items(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{id " + STATUS +
           " content{... on Issue{" + ISSUE + " subIssues(first:50){nodes{" + SUB + "}}}}}}}}}}")
Q_ISSUE = ("query AwIssue($powner:String!,$pnumber:Int!,$field:String!,$owner:String!,$name:String!,$number:Int!,"
           "$label:String!,$login:String!,$named:Boolean!){" + WHO + PROJECT + "}}} repository(owner:$owner,name:$name){id label(name:$label){id} issueTypes(first:50){nodes{id name}} "
           "issue(number:$number){id body milestone{id title} " + ISSUE + " comments(last:50){nodes{body}} "
           "projectItems(first:20){nodes{id project{id} " + STATUS + "}} subIssues(first:50){nodes{" + SUB +
           " projectItems(first:20){nodes{id project{id} " + STATUS + "}}}}}}}")
Q_COMMENTS = "query AwComments($owner:String!,$name:String!){repository(owner:$owner,name:$name){%s}}"
M_CREATE = "mutation AwCreateIssue($input:CreateIssueInput!){createIssue(input:$input){issue{id number}}}"
M_ADD = ("mutation AwAddItem($project:ID!,$content:ID!){addProjectV2ItemById(input:{projectId:$project,"
         "contentId:$content}){item{id}}}")
M_STATUS = ("mutation AwSetStatus($project:ID!,$item:ID!,$fieldId:ID!,$option:String!){updateProjectV2ItemFieldValue("
            "input:{projectId:$project,itemId:$item,fieldId:$fieldId,value:{singleSelectOptionId:$option}}){clientMutationId}}")
M_ASSIGN = ("mutation AwAssign($id:ID!,$users:[ID!]!){addAssigneesToAssignable(input:{assignableId:$id,"
            "assigneeIds:$users}){clientMutationId}}")
M_COMMENT = "mutation AwComment($id:ID!,$body:String!){addComment(input:{subjectId:$id,body:$body}){clientMutationId}}"
M_BODY = "mutation AwSetBody($id:ID!,$body:String!){updateIssue(input:{id:$id,body:$body}){clientMutationId}}"
# Found issues: the found and priority labels by alias, then every open issue's title for the similarity check.
Q_REPO = ("query AwRepo($powner:String!,$pnumber:Int!,$field:String!,$owner:String!,$name:String!,$found:String!,"
          "$urgent:String!,$soon:String!,$later:String!){" + PROJECT + "}}} repository(owner:$owner,name:$name){id "
          "issueTypes(first:50){nodes{id name}} found:label(name:$found){id} urgent:label(name:$urgent){id} "
          "soon:label(name:$soon){id} later:label(name:$later){id}}}")
Q_OPEN = ("query AwOpenIssues($owner:String!,$name:String!,$after:String){repository(owner:$owner,name:$name){"
          "issues(states:OPEN,first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{number title "
          "labels(first:20){nodes{name}}}}}}")
M_LABEL = ("mutation AwAddLabels($id:ID!,$labels:[ID!]!){addLabelsToLabelable(input:{labelableId:$id,"
           "labelIds:$labels}){clientMutationId}}")
M_UNLABEL = ("mutation AwRemoveLabels($id:ID!,$labels:[ID!]!){removeLabelsFromLabelable(input:{labelableId:$id,"
             "labelIds:$labels}){clientMutationId}}")
# init: the repository's settings, the draft's labels by alias, and its linked boards or the named one (20 boards).
BOARD = ("number title closed owner{... on Organization{login} ... on User{login}} "
         "fields(first:50){nodes{... on ProjectV2SingleSelectField{name options{name}}}}")
Q_INIT = ("query AwInit($owner:String!,$name:String!,$powner:String!,$pnumber:Int!,$named:Boolean!,$card:String!,"
          "$bullet:String!,$found:String!,$urgent:String!,$soon:String!,$later:String!){"
          "repository(owner:$owner,name:$name){nameWithOwner defaultBranchRef{name} rebaseMergeAllowed squashMergeAllowed "
          "mergeCommitAllowed mergeQueue{id} issueTypes(first:50){nodes{name}} "
          "projectsV2(first:20) @skip(if:$named){nodes{" + BOARD + "}} cards:issues(labels:[$card],states:OPEN){totalCount} "
          "card:label(name:$card){id} bullet:label(name:$bullet){id} found:label(name:$found){id} "
          "urgent:label(name:$urgent){id} soon:label(name:$soon){id} later:label(name:$later){id}} "
          "repositoryOwner(login:$powner) @include(if:$named){... on ProjectV2Owner{projectV2(number:$pnumber){" + BOARD + "}}}}")
REPO_RE = r"[\w.-]+/[\w.-]+"
# First use: default labels, conventional column names, and the extra names a column may carry for a state.
INIT_LABELS = {"card": "roadmap", "bullet": "tracer-bullet", "found": "found",
               "urgent": "priority:urgent", "soon": "priority:soon", "later": "priority:later"}
COLUMNS = {"backlog": "Backlog", "ready": "Ready", "in_progress": "In progress", "in_review": "In review",
           "blocked": "Blocked", "done": "Done"}
ALIASES = {"ready": ("todo",), "in_progress": ("doing",), "in_review": ("review",)}


class Usage(Exception):
    pass


class Refused(Exception):
    def __init__(self, reason, detail, **extra):
        super().__init__(detail)
        self.reason, self.detail, self.extra = reason, detail, extra


class GhFailed(Exception):
    def __init__(self, op, message):
        super().__init__(message)
        self.op, self.message = op, message


# ---------------------------------------------------------------- policy

def load_policy(path):
    path = Path(path)
    try:
        p = json.loads(path.read_text())
    except OSError:
        raise Usage(f"no tracker policy at {path}; ask the user where the policy lives")
    except ValueError as e:
        raise Usage(f"tracker policy {path} is not valid JSON: {e}")
    try:
        if not re.fullmatch(REPO_RE, p["repo"]):
            raise Usage("policy repo must be owner/name")
        proj, states, items, bullets = p["project"], p["states"], p["items"], p["bullets"]
        if not isinstance(proj["owner"], str) or not isinstance(proj["number"], int):
            raise Usage("policy project needs owner (string) and number (integer)")
        proj.setdefault("status_field", "Status")
        missing = [k for k in STATE_KEYS if not isinstance(states.get(k), str)]
        if missing:
            raise Usage(f"policy states lacks {missing}")
        if not isinstance(items["label"], str) or not isinstance(bullets["label"], str):
            raise Usage("policy items.label and bullets.label must be strings")
        items.setdefault("exclude_labels", [])
        items.setdefault("startable_states", ["ready"])
        if not set(items["startable_states"]) <= set(STATE_KEYS):
            raise Usage(f"policy startable_states must be among {list(STATE_KEYS)}")
        pattern = re.compile(bullets["pattern"], re.M)
        if not {"id", "text"} <= set(pattern.groupindex):
            raise Usage("policy bullets.pattern needs groups id and text")
        p["_pattern"] = pattern
        base = path.resolve().parent
        if p.get("authority"):
            p["authority"] = str(base / p["authority"])
        if p.get("order"):
            p["order"]["file"] = str(base / p["order"]["file"])
            re.compile(p["order"]["id_pattern"])
        p.setdefault("assignee", "@me")
        found = p.get("found")
        if found is not None and (not isinstance(found["label"], str)
                                  or not all(isinstance(found["priorities"].get(k), str) for k in PRIORITIES)):
            raise Usage(f"policy found needs label and priorities {list(PRIORITIES)} (strings)")
    except (KeyError, TypeError, AttributeError) as e:
        raise Usage(f"policy {path} is missing or mistypes {e}")
    except re.error as e:
        raise Usage(f"policy regex invalid: {e}")
    return p


def load_order(policy):
    o = policy.get("order")
    if not o:
        return []
    try:
        lines = Path(o["file"]).read_text().splitlines()
    except OSError:
        raise Usage(f"order file {o['file']} not readable")
    start = o.get("start")
    if start:
        at = next((i for i, l in enumerate(lines) if l.startswith(start)), None)
        if at is None:
            raise Usage(f"order start {start!r} not found in {o['file']}")
        lines = lines[at + 1:]
    end, ids = o.get("end"), []
    for line in lines:
        if end and line.startswith(end):
            break
        ids += [i for i in re.findall(o["id_pattern"], line) if i not in ids]
    return ids


# ---------------------------------------------------------------- pure logic

def card_id(title):
    return title.split(" — ", 1)[0].strip()


def summary(text):
    m = re.match(r"(.+?[.!?])(?:\s|$)", text)
    s = (m[1] if m else text).strip().rstrip(".")
    return s if len(s) <= 90 else s[:89].rstrip() + "…"


def parse_bullets(body, pattern):
    return [(m["id"].strip(), m["text"].strip()) for m in pattern.finditer((body or "").replace("\r\n", "\n"))]


@functools.lru_cache(maxsize=8)  # ponytail: per process; the CLI is one-shot, so the file cannot change under it
def read_lines(path):
    try:
        return Path(path).read_text().splitlines()
    except OSError:
        return None


def authority_section(policy, cid, cap=SECTION_CAP):
    """The authority file's section for a card id: heading, 1-based line range and text, verbatim, its first `cap`
    lines (None: all, for gating). The section runs from the first heading naming the id to the next heading of the
    same or a higher level."""
    path = policy.get("authority")
    if not path or not cid:
        return None
    lines = read_lines(path)
    if lines is None:
        return {"file": path, "error": "not readable"}
    head = re.compile(r"(#+)\s.*(?<![\w.])" + re.escape(cid) + r"(?![\w.])")
    for i, line in enumerate(lines):
        m = head.match(line)
        if m:
            end = next((j for j in range(i + 1, len(lines)) if re.match(r"#{1,%d}\s" % len(m[1]), lines[j])), len(lines))
            while not lines[end - 1].strip():
                end -= 1
            return {"file": path, "heading": line.strip(), "lines": [i + 1, end],
                    "text": "\n".join(lines[i:end][:cap]), "truncated": cap is not None and end - i > cap}
    return {"file": path, "error": f"no heading names {cid}"}


def authority_of(policy, f, cap=SECTION_CAP):
    """The authority of an issue read with its body: its card's section of the authority file; the issue body itself
    for a found issue, and for a card when the policy names no authority file."""
    if policy.get("authority") and kind(policy, f) != "found":
        return authority_section(policy, f["id"], cap)
    return {"issue": url(policy, f["number"]), "text": f["body"]}


def open_decisions(text):
    """Items of the first `Open decisions:` field of a card's authority: its inline text, else the list items under it
    (blank lines before the first; under a field that is itself a list item, only deeper items; an indented
    non-list line continues the item above). `none`, `(none)`, `-` or `n/a` mean none."""
    lines = (text or "").splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^([ \t]*)([-*>][ \t]+)?[*_]*Open decisions[*_]*[ \t]*:[*_]*[ \t]*(.*)$", line, re.I)
        if not m:
            continue
        items, floor = [m[3]], len(m[1].expandtabs(4)) + (1 if m[2] else 0)
        last = floor
        for nxt in ([] if m[3].strip() else lines[i + 1:]):
            item = re.match(r"^([ \t]*)[-*][ \t]+(.*)$", nxt)
            indent = len(re.match(r"[ \t]*", nxt)[0].expandtabs(4))
            if not nxt.strip() and len(items) == 1:
                continue
            if item and indent >= floor:
                items.append(item[2])
                last = indent
            elif not item and nxt.strip() and len(items) > 1 and indent > last:
                items[-1] += " " + nxt.strip()
            else:
                break
        return [x.strip() for x in items if x.strip() and x.strip().strip("().").casefold() not in ("none", "-", "—", "n/a")]
    return []


def holding(items, bullet_id):
    """The open decisions that hold bullet `bullet_id`: an item's `(T2, T3)` tag, before its first colon, names the
    bullets it binds; an untagged item binds the whole card. With no bullet known (a card not yet split into
    sub-issues), every item holds: `next` cannot read the card body, so the card waits for all of them."""
    def tags(x):
        m = re.match(r"^[^:(]*\(([^)]*)\)", x)
        return re.findall(r"T\d+", m[1]) if m else []
    if not bullet_id:
        return list(items)
    short = bullet_id.rsplit(".", 1)[-1]
    return [x for x in items if not tags(x) or short in tags(x)]


def repos_of(policy, body):
    """Code repositories of a card: the names on the first `Repos:` or `Repositories:` line of `body` (the card body, then its authority
    section; list markers and emphasis allowed), else the policy default, each from repos.known."""
    repos = policy.get("repos")
    method = (policy.get("merge") or {}).get("method")
    if not repos:
        return [{"repo": policy["repo"], "base": None, "merge": method}]
    line = re.search(r"^[ \t>*_-]*Repo(?:s|sitories)?:[*_]*[ \t]*(.+)$", body or "", re.M | re.I)
    names = re.findall(r"[\w.-]+", line[1]) if line else [repos.get("default")]
    known = repos.get("known") or {}
    return [{"name": n, **known[n], "merge": known[n].get("merge") or method} if n in known
            else {"name": n, "error": "not in policy repos.known"} for n in names if n]


def bullet_body(text, card):
    return f"{text}\n\nCard: #{card}\n\n{PLAN_START}\n{PLAN_END}\n"


def replace_plan(body, plan):
    section = f"{PLAN_START}\n{plan.strip(chr(10))}\n{PLAN_END}"
    body = (body or "").replace("\r\n", "\n")
    if PLAN_RE.search(body):
        return PLAN_RE.sub(lambda _: section, body, count=1)
    return (body.rstrip("\n") + "\n\n" if body.strip() else "") + section + "\n"


def nodes(conn):
    return (conn or {}).get("nodes") or []


def facts(node):
    parent = node.get("parent") or {}
    return {
        "number": node["number"], "title": node["title"], "id": card_id(node["title"]), "state": node["state"],
        "labels": [l["name"] for l in nodes(node.get("labels"))],
        "assignees": [a["login"] for a in nodes(node.get("assignees"))],
        "parent": parent.get("number"), "parent_state": parent.get("state"),
        "blockers": [{"number": b["number"], "state": b["state"]} for b in nodes(node.get("blockedBy"))],
        "prs": [p["number"] for p in nodes(node.get("closedByPullRequestsReferences")) if p["state"] == "OPEN"],
        "subs": [facts(s) for s in nodes(node.get("subIssues"))],
        "status": None, "item_id": None, "on_board": False,
    }


def kind(policy, f):
    if policy["bullets"]["label"] in f["labels"]:
        return "bullet"
    if policy["items"]["label"] in f["labels"]:
        return "card"
    found = policy.get("found")
    return "found" if found and found["label"] in f["labels"] else "other"


def priority(policy, f):
    """Rank of a found issue; None (untriaged) unless it has exactly one priority label."""
    ranks = [r for r in PRIORITIES if policy["found"]["priorities"][r] in f["labels"]]
    return ranks[0] if len(ranks) == 1 else None


def words(title):
    return set(re.findall(r"[^\W\d_]{3,}", (title or "").casefold()))


def similar(a, b):
    """At least half of the words of three or more letters of both titles together are shared:
    2 * shared >= (words of a + words of b) / 2. Case and punctuation are ignored; no words, not similar."""
    wa, wb = words(a), words(b)
    return bool(wa and wb) and 4 * len(wa & wb) >= len(wa) + len(wb)


def excluded(policy, f):
    return bool(set(f["labels"]) & set(policy["items"]["exclude_labels"]))


def open_blockers(f):
    return [b["number"] for b in f["blockers"] if b["state"] == "OPEN"]


def bullet_key(f):
    """Bullet order: natural sort of the id (T2 before T10), then issue number."""
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", f["id"])], f["number"]


def bullets_of(policy, card, board):
    """Bullet sub-issues in bullet order, with board facts when on the board."""
    subs = [board.get(s["number"], s) for s in card["subs"] if kind(policy, s) == "bullet"]
    return sorted(subs, key=bullet_key)


def bullet_view(policy, card):
    """A card's bullets in order: the ones its body lists, joined with their sub-issues by id. `number` is None
    until `bullets` has created the sub-issue."""
    subs = {b["id"]: b for b in bullets_of(policy, card, {})}
    out = [{"id": bid, "text": text} for bid, text in parse_bullets(card.get("body"), policy["_pattern"])]
    listed = {b["id"] for b in out}
    out += [{"id": i, "text": b["title"].split(" — ", 1)[-1]} for i, b in subs.items() if i not in listed]
    for b in out:
        sub = subs.get(b["id"]) or {}
        b.update(number=sub.get("number"), state=sub.get("state"), assignees=sub.get("assignees", []),
                 status=state_key(policy, sub["status"]) if sub.get("status") else None)
    return out


def state_key(policy, column):
    return next((k for k, v in policy["states"].items() if v == column), column)


def rank(order, f):
    cid = f["id"]
    return (order.index(cid) if cid in order else len(order), f["number"])


def unavailable(f, startable):
    """Skip reason of a card without bullets or a found issue; None when it may be handed out."""
    return ("not_startable" if f["status"] not in startable
            else "blocked" if open_blockers(f)
            else "assigned" if f["assignees"]
            else "open_pr" if f["prs"] else None)


def select(policy, board, order, me):
    """Selection rule of tracker.md: (candidates, skipped counts, ids of cards held by open decisions)."""
    st = policy["states"]
    taken_cols = {st["in_progress"], st["in_review"]}
    startable = {st[k] for k in policy["items"]["startable_states"]}
    started, new, found, skipped, held = [], [], {r: [] for r in PRIORITIES}, Counter(), []
    for f in board.values():
        k = kind(policy, f)
        if f["state"] != "OPEN" or k not in ("card", "found"):
            continue
        if k == "found":
            r = priority(policy, f)
            reason = "untriaged" if r is None else unavailable(f, startable)
            if reason:
                skipped[reason] += 1
            else:
                found[r].append((f["number"], f, None))
            continue
        if excluded(policy, f):
            skipped["excluded_label"] += 1
            continue
        # ponytail: board items carry no body, so without an authority file only `claim` sees a card body's open decisions.
        items = open_decisions((authority_section(policy, f["id"], None) or {}).get("text")) if policy.get("authority") else []
        bullets = bullets_of(policy, f, board)
        if bullets:
            b = next((b for b in bullets if b["state"] == "OPEN"), None)
            if f["assignees"] and f["assignees"] != [me]:
                skipped["assigned"] += 1
            elif b is None:
                skipped["bullets_done"] += 1
            elif b["assignees"] or b["status"] in taken_cols:
                skipped["bullet_taken"] += 1
            elif open_blockers(b):
                skipped["blocked"] += 1
            elif holding(items, b["id"]):
                skipped["open_decisions"] += 1
                held.append(f["id"])
            else:
                started.append((rank(order, f), b, f))
            continue
        reason = "in_progress_without_bullets" if f["status"] == st["in_progress"] else unavailable(f, startable)
        if not reason and holding(items, None):
            reason = "open_decisions"
            held.append(f["id"])
        if reason:
            skipped[reason] += 1
        else:
            new.append((rank(order, f), f, None))

    def by_key(xs):
        return sorted(xs, key=lambda t: t[0])

    out = []
    for _, f, card in (by_key(found["urgent"]) + by_key(started) + by_key(found["soon"]) + by_key(new)
                       + by_key(found["later"])):
        c = {"number": f["number"], "id": f["id"], "title": f["title"], "kind": kind(policy, f),
             "card": card["number"] if card else None, "url": url(policy, f["number"])}
        if c["kind"] == "found":
            c["priority"] = priority(policy, f)
        out.append(c)
    return out, {r: skipped[r] for r in SKIP_REASONS if skipped[r]}, held


def drift(policy, board, open_issues=()):
    """Drift of the board, plus found issues among `open_issues` (the repository's) that are not on it."""
    st, out = policy["states"], []

    def add(code, f, detail):
        out.append({"code": code, "number": f["number"], "id": f["id"], "detail": detail})

    for i in open_issues:
        if i["number"] not in board and kind(policy, i) == "found":
            f = {**i, "id": card_id(i["title"])}
            if priority(policy, f) is None:
                add("found_untriaged", f, "needs exactly one priority label; not on the board")
            else:
                add("not_on_board", f, "found issue not on the board")

    for f in sorted(board.values(), key=lambda f: f["number"]):
        k = kind(policy, f)
        if k == "other" or excluded(policy, f):
            continue
        s = f["status"]
        if f["state"] == "CLOSED" and s != st["done"]:
            add("closed_not_done", f, f"closed but status {s!r}")
        if f["state"] == "OPEN" and s == st["done"]:
            add("done_but_open", f, "status Done but issue open")
        if f["state"] == "OPEN" and s == st["ready"] and open_blockers(f):
            add("startable_but_blocked", f, f"status {s!r} with open blockers {open_blockers(f)}")
        if f["state"] == "OPEN" and s == st["in_progress"] and not f["assignees"]:
            add("in_progress_unassigned", f, "in progress without assignee")
        if k == "bullet" and f["state"] == "OPEN" and f["parent_state"] == "CLOSED":
            add("bullet_open_card_closed", f, f"card #{f['parent']} closed")
        if k == "found" and f["state"] == "OPEN" and priority(policy, f) is None:
            add("found_untriaged", f, "needs exactly one priority label")
        if k == "card":
            for b in bullets_of(policy, f, board):
                if not b["on_board"]:
                    add("not_on_board", b, f"bullet of #{f['number']} not on the board")
    return out


def url(policy, n):
    return f"https://github.com/{policy['repo']}/issues/{n}"


def norm(name):
    return re.sub(r"[\s-]+", "", name).casefold()


def map_states(columns):
    """First use: each state to the column whose name, without case, spaces or hyphens, equals the state's
    name or one of its aliases; None when no column does."""
    by = {}
    for c in columns:
        by.setdefault(norm(c), c)
    return {k: next((by[n] for n in (k.replace("_", ""),) + ALIASES.get(k, ()) if n in by), None) for k in STATE_KEYS}


def merge_method(repo):
    """`queue` when the default branch has a merge queue, else the first allowed of rebase, squash, merge."""
    if repo.get("mergeQueue"):
        return "queue"
    allowed = [m for m, key in (("rebase", "rebaseMergeAllowed"), ("squash", "squashMergeAllowed"),
                                ("merge", "mergeCommitAllowed")) if repo.get(key)]
    return allowed[0] if allowed else "merge"


# ---------------------------------------------------------------- GitHub

class Tracker:
    def __init__(self, policy):
        self.policy, self.gh, self.writes = policy, os.environ.get("AW_TRACKER_GH", "gh"), []
        self.me = None  # policy assignee login, set by board()
        self.field = "Status"
        if policy:  # init runs without one
            self.owner, self.name = policy["repo"].split("/")
            self.field = policy["project"]["status_field"]

    def run(self, op, args, stdin=None):
        try:
            p = subprocess.run([self.gh, *args], capture_output=True, text=True, input=stdin)
        except OSError as e:
            raise GhFailed(op, str(e))
        if p.returncode:
            self.fail(op, p.stderr or p.stdout or f"gh exited {p.returncode}")
        try:
            return json.loads(p.stdout)
        except ValueError:
            raise GhFailed(op, f"unparseable gh output: {p.stdout[:300]}")

    def call(self, query, variables):
        op = re.match(r"\s*(?:query|mutation)\s+(\w+)", query)[1]
        data = self.run(op, ["api", "graphql", "--input", "-"], json.dumps({"query": query, "variables": variables}))
        if data.get("errors"):
            self.fail(op, "; ".join(e.get("message", "") for e in data["errors"]))
        return data["data"]

    def fail(self, op, message):
        # GitHub rejects field(name:) for a name the project lacks; that is a policy error, not a gh failure.
        if "Could not resolve to a Unions::ProjectV2FieldConfiguration" in message:
            raise Usage(f"project has no field {self.field!r}")
        raise GhFailed(op, message)

    def write(self, what, query, variables):
        try:
            data = self.call(query, variables)
        except GhFailed as e:
            e.what = what
            raise
        self.writes.append(what)
        return data

    def number(self, ref, board=None):
        """Issue number of a number or a card id; an id must name exactly one issue on the board."""
        if isinstance(ref, int):
            return ref
        hits = sorted(f["number"] for f in (board or self.board()).values() if f["id"] == ref)
        if len(hits) != 1:
            raise Usage(f"id {ref!r} names {len(hits)} issues on the board {hits}; use the issue number")
        return hits[0]

    def pvars(self):
        login = self.policy["assignee"]
        return {"powner": self.policy["project"]["owner"], "pnumber": self.policy["project"]["number"], "field": self.field,
                "login": "" if login == "@me" else login, "named": login != "@me"}

    def columns(self, proj, *keys):
        """Policy error unless every named state is an option of the status field; run before the first write."""
        missing = [self.policy["states"][k] for k in keys if self.policy["states"][k] not in proj["options"]]
        if missing:
            raise Usage(f"board field {self.field!r} has no option {missing}")

    def project(self, data):
        p = ((data.get("repositoryOwner") or {}).get("projectV2")) or {}
        if not p.get("field"):
            raise Usage(f"project has no single-select field {self.field!r}")
        return {"id": p["id"], "field": p["field"]["id"], "options": {o["name"]: o["id"] for o in p["field"]["options"]}}

    def board(self):
        board, after = {}, None
        while True:
            data = self.call(Q_ITEMS, {**self.pvars(), "after": after})
            self.me = (data.get("who") or data["viewer"])["login"]
            items = data["repositoryOwner"]["projectV2"]["items"]
            for it in items["nodes"]:
                c = it.get("content") or {}
                if "number" not in c or c["repository"]["nameWithOwner"].lower() != self.policy["repo"].lower():
                    continue
                f = facts(c)
                f.update(status=(it.get("fieldValueByName") or {}).get("name"), item_id=it["id"], on_board=True)
                board[f["number"]] = f
            if not items["pageInfo"]["hasNextPage"]:
                break
            after = items["pageInfo"]["endCursor"]
        for f in board.values():
            for s in f["subs"]:
                if s["number"] in board:
                    s.update(status=board[s["number"]]["status"], on_board=True)
        return board

    def issue(self, n):
        data = self.call(Q_ISSUE, {**self.pvars(), "owner": self.owner, "name": self.name, "number": n,
                                   "label": self.policy["bullets"]["label"]})
        proj, repo = self.project(data), data["repository"]
        node = repo["issue"]
        f = facts(node)
        f.update(node_id=node["id"], body=(node.get("body") or "").replace("\r\n", "\n"),
                 milestone=node.get("milestone"), comments=[c["body"].replace("\r\n", "\n") for c in nodes(node.get("comments"))])
        for target, src in [(f, node)] + list(zip(f["subs"], nodes(node.get("subIssues")))):
            mine = [i for i in nodes(src.get("projectItems")) if i["project"]["id"] == proj["id"]]
            if mine:
                target.update(item_id=mine[0]["id"], on_board=True,
                              status=(mine[0].get("fieldValueByName") or {}).get("name"))
        f["ctx"] = {"project": proj, "me": data.get("who") or data["viewer"], "repo_id": repo["id"],
                    "label_id": (repo.get("label") or {}).get("id"),
                    "types": {t["name"]: t["id"] for t in nodes(repo.get("issueTypes"))}}
        return f

    def comments(self, numbers):
        """Latest comments of several issues: one aliased query per 50 issues."""
        out, numbers = {}, list(numbers)
        for i in range(0, len(numbers), 50):
            part = numbers[i:i + 50]
            q = Q_COMMENTS % " ".join(f"i{n}:issue(number:{n}){{comments(last:50){{nodes{{body}}}}}}" for n in part)
            repo = self.call(q, {"owner": self.owner, "name": self.name})["repository"]
            out.update({n: [c["body"] for c in nodes(repo[f"i{n}"]["comments"])] for n in part})
        return out

    def found_ctx(self):
        """Project, repository and found/priority label ids; usage error naming each label the repository lacks."""
        fp = self.policy.get("found")
        if not fp:
            raise Usage("policy has no found key; found issues are disabled")
        names = {"found": fp["label"], **{r: fp["priorities"][r] for r in PRIORITIES}}
        data = self.call(Q_REPO, {"powner": self.policy["project"]["owner"], "pnumber": self.policy["project"]["number"],
                                  "field": self.field, "owner": self.owner, "name": self.name, **names})
        proj, repo = self.project(data), data["repository"]
        missing = [names[k] for k in names if not repo.get(k)]
        if missing:
            raise Usage(f"labels {missing} do not exist in {self.policy['repo']}; create them")
        return {"project": proj, "repo_id": repo["id"], "types": {t["name"]: t["id"] for t in nodes(repo.get("issueTypes"))},
                "labels": {names[k]: repo[k]["id"] for k in names}}

    def open_issues(self):
        out, after = [], None
        while True:
            issues = self.call(Q_OPEN, {"owner": self.owner, "name": self.name, "after": after})["repository"]["issues"]
            out += [{"number": n["number"], "title": n["title"], "labels": [l["name"] for l in nodes(n.get("labels"))]}
                    for n in issues["nodes"]]
            if not issues["pageInfo"]["hasNextPage"]:
                return out
            after = issues["pageInfo"]["endCursor"]

    def ensure_status(self, f, key, proj):
        column = self.policy["states"][key]
        if f["on_board"] and f["status"] == column:
            return
        self.columns(proj, key)
        if not f["on_board"]:
            item = self.write(f"add #{f['number']} to board", M_ADD, {"project": proj["id"], "content": f["node_id"]})
            f.update(item_id=item["addProjectV2ItemById"]["item"]["id"], on_board=True)
        self.write(f"status #{f['number']} {column}", M_STATUS, {"project": proj["id"], "item": f["item_id"],
                                                                 "fieldId": proj["field"], "option": proj["options"][column]})
        f["status"] = column


def last_claim(comments):
    found = None
    for c in comments:
        for m in CLAIM_RE.finditer(c):
            found = {"branch": m[1] or None, "phase": m[2] or None}
    return found


# ---------------------------------------------------------------- commands

def cmd_init(t, args):
    """Draft a policy from the repository and its board (tracker.md "First use"). Reads only; writes the draft file."""
    out = Path(args.out or args.policy)
    if out.exists():
        raise Refused("exists", f"{out} exists; edit it, or pass --out for another path")
    repo = args.repo or t.run("AwRepoView", ["repo", "view", "--json", "nameWithOwner"])["nameWithOwner"]
    if not re.fullmatch(REPO_RE, repo):
        raise Usage(f"repository must be owner/name, got {repo!r}")
    owner, name = repo.split("/")
    powner, pnumber = args.project or ("", 0)
    data = t.call(Q_INIT, {"owner": owner, "name": name, "powner": powner, "pnumber": pnumber,
                           "named": bool(args.project), **INIT_LABELS})
    r = data["repository"]
    if args.project:
        boards = [((data.get("repositoryOwner") or {}).get("projectV2"))]
        if not boards[0]:
            raise Usage(f"no project {powner}/{pnumber}")
    else:
        boards = [b for b in nodes(r.get("projectsV2")) if not b.get("closed")]
    ref = [{"project": f"{b['owner']['login']}/{b['number']}", "title": b["title"]} for b in boards]
    if not boards:
        raise Refused("no_board", f"no open project is linked to {repo}; link one or pass --project OWNER/NUMBER")
    if len(boards) > 1:
        raise Refused("ambiguous", f"{len(boards)} projects are linked to {repo}; pass --project OWNER/NUMBER",
                      choices=ref)
    board = boards[0]
    field = next((f for f in nodes(board.get("fields")) if f.get("name") == "Status"), None)
    if not field:
        raise Usage(f"project {ref[0]['project']} has no single-select field 'Status'")
    columns = [o["name"] for o in field["options"]]
    states = map_states(columns)
    types = [i["name"] for i in nodes(r.get("issueTypes"))]
    base, method = (r.get("defaultBranchRef") or {}).get("name"), merge_method(r)
    bullets = {"label": INIT_LABELS["bullet"], "pattern": r"^(?P<id>\d+)\. (?P<text>.+)$"}
    found = {"label": INIT_LABELS["found"], "priorities": {k: INIT_LABELS[k] for k in PRIORITIES}}
    if "Task" in types:
        bullets["issue_type"] = "Task"
    if "Bug" in types:
        found["issue_type"] = "Bug"
    policy = {
        "repo": repo,
        "project": {"owner": board["owner"]["login"], "number": board["number"], "status_field": "Status"},
        "states": {k: states[k] or COLUMNS[k] for k in STATE_KEYS},
        "items": {"label": INIT_LABELS["card"], "startable_states": ["ready"]},
        "bullets": bullets,
        "assignee": "@me",
        "repos": {"default": name, "named_by": "the card's Repos line; a card without one uses the default",
                  "known": {name: {"repo": repo, "base": base, "merge": method}}},
        "found": found,
        "merge": {"allowed": False},
        "notes": ["Replace this line with the project's conventions the steward repeats in its work order."],
    }
    missing = [{"what": "state", "name": k, "fix": f"add the column {COLUMNS[k]!r} to the board's Status field, "
                f"or set states.{k} to an existing column"} for k in STATE_KEYS if not states[k]]
    missing += [{"what": "label", "name": n, "fix": f"gh label create {shlex.quote(n)} -R {repo}"}
                for k, n in INIT_LABELS.items() if not r.get(k)]
    if not r["cards"]["totalCount"]:
        missing.append({"what": "cards", "name": INIT_LABELS["card"],
                        "fix": f"add the {INIT_LABELS['card']!r} label to the open issues that are roadmap cards"})
    try:
        with open(out, "x") as fh:
            fh.write(json.dumps(policy, indent=2, ensure_ascii=False) + "\n")
    except FileExistsError:
        raise Refused("exists", f"{out} exists; edit it, or pass --out for another path")
    except OSError as e:
        raise Usage(f"cannot write {out}: {e}")
    detected = {"repo": repo, "project": ref[0]["project"], "title": board["title"], "columns": columns, "states": states,
                "default_branch": base, "merge": method, "labels": [n for k, n in INIT_LABELS.items() if r.get(k)],
                "issue_types": types, "open_cards": r["cards"]["totalCount"]}
    return {"policy": str(out.resolve()), "detected": detected, "missing": missing}


def offer(p, board, candidates):
    """Candidates with the authority section of their card, so a contradiction is visible in the same output."""
    for c in candidates:
        if c["kind"] != "found":
            c["authority"] = authority_section(p, board[c["card"]]["id"] if c["card"] else c["id"])
    return candidates


def cmd_next(t, args):
    p = t.policy
    order = load_order(p)
    board = t.board()
    candidates, skipped, held = select(p, board, order, t.me)
    offer(p, board, candidates[:args.limit])
    # Blocked work items stay in flight so stage 1 resumes them once their blocker is resolved.
    columns = {p["states"]["in_progress"], p["states"]["in_review"], p["states"]["blocked"]}
    live = [f for f in sorted(board.values(), key=lambda f: f["number"])
            if f["state"] == "OPEN" and f["status"] in columns and kind(p, f) in ("bullet", "found")]
    comments = t.comments(f["number"] for f in live) if live else {}
    flight = []
    for f in live:
        claim = last_claim(comments[f["number"]]) or {}
        flight.append({"number": f["number"], "id": f["id"], "card": f["parent"], "assignees": f["assignees"],
                       "status": state_key(p, f["status"]), "branch": claim.get("branch"), "phase": claim.get("phase")})
    out = {"candidates": candidates[:args.limit], "in_flight": flight, "skipped": skipped, "authority": p.get("authority")}
    if held:
        out["open_decisions"] = held
    return out


def cmd_show(t, args):
    p, f = t.policy, t.issue(t.number(args.number))
    out = {"number": f["number"], "id": f["id"], "title": f["title"], "kind": kind(p, f), "state": f["state"],
           "status": state_key(p, f["status"]) if f["status"] else None, "assignees": f["assignees"], "labels": f["labels"],
           "milestone": (f["milestone"] or {}).get("title"), "parent": f["parent"], "blockers": f["blockers"],
           "bullets": bullet_view(p, f),
           "pull_requests": f["prs"], "url": url(p, f["number"])}
    if args.body:
        out["body"] = f["body"]
    return out


def cmd_work_order(t, args):
    """Read-only. The facts of the steward's work order for one card, bullet or found issue, in one call."""
    p, board = t.policy, t.board()
    f = t.issue(t.number(args.number, board))
    k = kind(p, f)
    card = t.issue(f["parent"]) if k == "bullet" and f["parent"] else f if k == "card" else None
    bullets = bullet_view(p, card) if card else []
    bullet = next((b for b in bullets if (b["number"] == f["number"] if k == "bullet" else b["state"] != "CLOSED")), None)
    item = card or f
    work = f if k != "card" else t.issue(bullet["number"]) if bullet and bullet["number"] else f
    # The issue `claim` takes first: the found issue or bullet itself, a started card's current bullet, a new card.
    claim = {"number": work["number"]}
    try:
        claimable(t, work)
        claim["allowed"] = True
    except Refused as e:
        claim.update(allowed=False, reason=e.reason, detail=e.detail)
    mine = {item["number"], f["number"]} | {b["number"] for b in bullets if b["number"]}
    candidates, _, _ = select(p, board, load_order(p), t.me)
    plan = PLAN_RE.search(work["body"])
    section = authority_of(p, item)
    return {
        "kind": k,
        "item": {"number": item["number"], "id": item["id"], "title": item["title"], "url": url(p, item["number"]),
                 "state": item["state"], "status": state_key(p, item["status"]) if item["status"] else None,
                 "assignees": item["assignees"]},
        "bullet": bullet and {**bullet, "url": url(p, bullet["number"]) if bullet["number"] else None},
        "siblings_out_of_scope": [f"{b['id']} — {b['text']}" for b in bullets if b is not bullet],
        "authority": section,
        "repositories": repos_of(p, "\n".join([item["body"] or "", (section or {}).get("text", "")])),
        "dependencies": [{**b, "id": board[b["number"]]["id"] if b["number"] in board else None} for b in item["blockers"]],
        "claimed": last_claim(work["comments"]),
        "plan_published": bool(plan and plan[0] != f"{PLAN_START}\n{PLAN_END}"),
        "claim": claim,
        "alternates": offer(p, board, [c for c in candidates if c["number"] not in mine and c["card"] not in mine][:3]),
        "drift": [d for d in drift(p, board) if d["number"] in mine],
        "policy_notes": p.get("notes", []),
    }


def require_card(p, f):
    if kind(p, f) != "card" or excluded(p, f):
        raise Refused("not_a_card", f"#{f['number']} is not a {p['items']['label']} card that may be handed out")


def require_free(p, f):
    """Refuse `taken` or `blocked`; True when f is already the policy assignee's."""
    st, me = p["states"], f["ctx"]["me"]["login"]
    mine = f["assignees"] == [me]
    if (f["state"] != "OPEN" or (f["assignees"] and not mine) or f["status"] in (st["in_review"], st["done"])
            or (f["status"] == st["in_progress"] and not mine)):
        raise Refused("taken", f"#{f['number']} state {f['state']}, status {f['status']!r}, assignees {f['assignees']}")
    if open_blockers(f):
        raise Refused("blocked", f"#{f['number']} has open blockers {open_blockers(f)}")
    return mine


def cmd_bullets(t, args):
    p, card = t.policy, t.issue(args.number)
    require_card(p, card)
    require_free(p, card)
    parsed = parse_bullets(card["body"], p["_pattern"])
    if not parsed:
        raise Refused("no_bullets", f"bullets.pattern matched nothing in #{card['number']}")
    ctx = card["ctx"]
    if not ctx["label_id"]:
        raise Usage(f"labels {[p['bullets']['label']]} do not exist in {p['repo']}; create them")
    t.columns(ctx["project"], "backlog")
    have = {s["id"]: s for s in card["subs"]}
    out = []
    for bid, text in parsed:
        b = have.get(bid)
        created = b is None
        if created:
            title = f"{bid} — {summary(text)}"
            inp = {"repositoryId": ctx["repo_id"], "title": title, "body": bullet_body(text, card["number"]),
                   "labelIds": [ctx["label_id"]], "parentIssueId": card["node_id"]}
            if card["milestone"]:
                inp["milestoneId"] = card["milestone"]["id"]
            if p["bullets"].get("issue_type") in ctx["types"]:
                inp["issueTypeId"] = ctx["types"][p["bullets"]["issue_type"]]
            made = t.write(f"create bullet {bid}", M_CREATE, {"input": inp})["createIssue"]["issue"]
            b = {"number": made["number"], "id": bid, "title": title, "on_board": False, "status": None, "node_id": made["id"]}
        if not b["on_board"] or not b.get("status"):  # also an add whose status write failed
            if "node_id" not in b:
                b["node_id"] = t.issue(b["number"])["node_id"]
            t.ensure_status(b, "backlog", ctx["project"])
        out.append({"number": b["number"], "id": bid, "title": b["title"], "created": created})
    return {"card": card["number"], "bullets": out}


def claimable(t, f):
    """Refuse what `claim` refuses, before any write. Returns (already mine, parent card of a bullet)."""
    p, k = t.policy, kind(t.policy, f)
    if k == "other" or (k == "card" and excluded(p, f)):
        raise Refused("not_a_card", f"#{f['number']} is neither a card, a bullet nor a found issue that may be handed out")
    mine = require_free(p, f)
    parent = None
    if k == "bullet":
        if not f["parent"]:
            raise Refused("not_a_card", f"bullet #{f['number']} has no parent card")
        parent = t.issue(f["parent"])
        me = f["ctx"]["me"]["login"]
        if parent["state"] != "OPEN" or (parent["assignees"] and parent["assignees"] != [me]):
            raise Refused("taken", f"parent card #{parent['number']} state {parent['state']}, assignees {parent['assignees']}")
        if excluded(p, parent):
            raise Refused("not_a_card", f"parent card #{parent['number']} carries an excluded label")
        earlier = [b["number"] for b in bullets_of(p, parent, {}) if bullet_key(b) < bullet_key(f) and b["state"] == "OPEN"]
        if earlier:
            raise Refused("blocked", f"earlier bullets of #{parent['number']} still open: {earlier}")
    card = parent or (f if k == "card" else None)
    if card:  # the bullet this claim leads to: the bullet itself, or a card's first open sub-issue, as `next` sees it
        first = f["id"] if k == "bullet" else next((b["id"] for b in bullets_of(p, f, {}) if b["state"] == "OPEN"), None)
        section = authority_of(p, card, None) or {}
        if section.get("error") == "not readable":  # fail closed: unread decisions are not settled ones
            raise Refused("open_decisions", f"cannot read {section['file']} to check card #{card['number']}'s open decisions")
        left = holding(open_decisions(section.get("text")), first)
        if left:
            raise Refused("open_decisions", f"card #{card['number']} has open decisions for {first or 'the card'}: {left}")
    return mine, parent


def cmd_claim(t, args):
    p, f = t.policy, t.issue(t.number(args.number))
    k, me = kind(p, f), f["ctx"]["me"]
    mine, parent = claimable(t, f)
    proj = f["ctx"]["project"]
    t.columns(proj, "in_progress")
    if not mine:
        t.write(f"assign #{f['number']} {me['login']}", M_ASSIGN, {"id": f["node_id"], "users": [me["id"]]})
    t.ensure_status(f, "in_progress", proj)
    if parent:
        t.ensure_status(parent, "in_progress", proj)
    want = {"branch": args.branch, "phase": args.phase}
    if last_claim(f["comments"]) != want:
        body = (f"<!-- aw:claim branch={args.branch or ''} phase={args.phase or ''} -->\n"
                f"Claimed by @{me['login']}" + (f" on branch `{args.branch}`" if args.branch else "")
                + (f", phase {args.phase}" if args.phase else "") + ".")
        t.write(f"comment #{f['number']} claim", M_COMMENT, {"id": f["node_id"], "body": body})
    return {"number": f["number"], "id": f["id"], "kind": k, "card": parent["number"] if parent else None,
            "assignee": me["login"], "branch": args.branch, "url": url(p, f["number"])}


def cmd_plan(t, args):
    try:
        plan = Path(args.file).read_text()
    except OSError:
        raise Usage(f"plan file {args.file} not readable")
    if PLAN_START in plan or PLAN_END in plan:
        raise Usage(f"plan file {args.file} contains a plan marker")
    f = t.issue(args.number)
    body = replace_plan(f["body"], plan)
    if len(body) > MAX_BODY:
        raise Refused("too_large", f"body would be {len(body)} characters, limit {MAX_BODY}")
    if body != f["body"]:
        t.write(f"plan #{f['number']}", M_BODY, {"id": f["node_id"], "body": body})
    return {"number": f["number"], "id": f["id"], "characters": len(body)}


def cmd_set(t, args):
    if args.state not in STATE_KEYS:
        raise Usage(f"state must be one of {list(STATE_KEYS)}")
    f = t.issue(args.number)
    t.columns(f["ctx"]["project"], args.state)
    t.ensure_status(f, args.state, f["ctx"]["project"])
    if args.comment and (not f["comments"] or f["comments"][-1] != args.comment):
        t.write(f"comment #{f['number']}", M_COMMENT, {"id": f["node_id"], "body": args.comment})
    return {"number": f["number"], "id": f["id"], "status": args.state}


def read_text(path, what):
    try:
        return Path(path).read_text().replace("\r\n", "\n")
    except OSError:
        raise Usage(f"{what} file {path} not readable")


def cmd_file(t, args):
    p, title = t.policy, args.title.strip()
    body = read_text(args.body_file, "body")
    if not title:
        raise Usage("title must not be empty")
    ctx = t.found_ctx()
    proj = ctx["project"]
    t.columns(proj, "ready")
    if args.found_in and f"Found in #{args.found_in}" not in body.splitlines():
        body = (body.rstrip("\n") + "\n\n" if body.strip() else "") + f"Found in #{args.found_in}\n"
    issues = t.open_issues()
    # A repeated command finds the issue it filed (found label, same title and body) and only completes it.
    # Same title with another body is new evidence or another problem: `similar` below, or `--new`.
    for i in issues:
        if i["title"].strip() == title and p["found"]["label"] in i["labels"]:
            f = t.issue(i["number"])
            if f["body"].strip() == body.strip():
                if f["status"] is None:
                    t.ensure_status(f, "ready", proj)
                return {"number": f["number"], "title": f["title"], "kind": "found", "priority": priority(p, f),
                        "created": False, "url": url(p, f["number"])}
    matches = [{"number": i["number"], "title": i["title"], "url": url(p, i["number"])} for i in issues
               if similar(title, i["title"]) or i["title"].strip().casefold() == title.casefold()]
    if matches and not args.new:
        raise Refused("similar", f"open issues with a similar title: {[m['number'] for m in matches]}", matches=matches)
    labels = [p["found"]["label"], p["found"]["priorities"][args.priority]]
    inp = {"repositoryId": ctx["repo_id"], "title": title, "body": body, "labelIds": [ctx["labels"][l] for l in labels]}
    issue_type = args.type or p["found"].get("issue_type")
    if issue_type in ctx["types"]:
        inp["issueTypeId"] = ctx["types"][issue_type]
    made = t.write("create found issue", M_CREATE, {"input": inp})["createIssue"]["issue"]
    f = {"number": made["number"], "node_id": made["id"], "on_board": False, "status": None}
    t.ensure_status(f, "ready", proj)
    return {"number": f["number"], "title": title, "kind": "found", "priority": args.priority, "created": True,
            "url": url(p, f["number"])}


def cmd_rank(t, args):
    p = t.policy
    ctx = t.found_ctx()
    f = t.issue(args.number)
    if p["found"]["label"] not in f["labels"]:
        raise Refused("not_found", f"#{f['number']} lacks the {p['found']['label']!r} label")
    if f["state"] != "OPEN":
        raise Refused("taken", f"#{f['number']} is {f['state']}")
    t.columns(ctx["project"], "ready")
    labels = p["found"]["priorities"]
    want, stale = labels[args.priority], [labels[r] for r in PRIORITIES if r != args.priority and labels[r] in f["labels"]]
    if want not in f["labels"]:
        t.write(f"label #{f['number']} {want}", M_LABEL, {"id": f["node_id"], "labels": [ctx["labels"][want]]})
    if stale:
        t.write(f"unlabel #{f['number']} {', '.join(stale)}", M_UNLABEL,
                {"id": f["node_id"], "labels": [ctx["labels"][l] for l in stale]})
    if f["status"] in (None, p["states"]["backlog"]):
        t.ensure_status(f, "ready", ctx["project"])
    return {"number": f["number"], "title": f["title"], "priority": args.priority,
            "status": state_key(p, f["status"]) if f["status"] else None, "url": url(p, f["number"])}


def cmd_note(t, args):
    text = read_text(args.file, "note").strip()
    if not text:
        raise Usage(f"note file {args.file} is empty")
    f = t.issue(args.number)
    posted = text not in (c.strip() for c in f["comments"])
    if posted:
        t.write(f"comment #{f['number']}", M_COMMENT, {"id": f["node_id"], "body": text})
    return {"number": f["number"], "posted": posted, "url": url(t.policy, f["number"])}


def cmd_audit(t, args):
    board = t.board()
    # A found issue filed by a person without adding it to the board is visible only among open issues.
    out = drift(t.policy, board, t.open_issues() if t.policy.get("found") else ())
    out.sort(key=lambda d: d["number"])
    return {"drift": out, "count": len(out)}


def issue_ref(v):
    """An issue number, or a card id that `Tracker.number` resolves on the board."""
    return int(v) if v.isdigit() else v


def positive(v):
    if not v.isdigit() or int(v) < 1:
        raise argparse.ArgumentTypeError("must be an integer >= 1")
    return int(v)


def marker_value(v):
    """A value the claim marker can hold and read back: no whitespace, < or > (so no -->)."""
    if not re.fullmatch(r"[^\s<>]+", v):
        raise argparse.ArgumentTypeError(f"{v!r} must be non-empty without whitespace, < or >")
    return v


def repo_ref(v):
    if not re.fullmatch(REPO_RE, v):
        raise argparse.ArgumentTypeError(f"{v!r} must be OWNER/NAME")
    return v


def project_ref(v):
    m = re.fullmatch(r"([\w.-]+)/(\d+)", v)
    if not m:
        raise argparse.ArgumentTypeError(f"{v!r} must be OWNER/NUMBER")
    return m[1], int(m[2])


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


def parse(argv):
    ap = Parser(prog="tracker.py")
    ap.add_argument("--policy", default="tracker-policy.json")
    sub = ap.add_subparsers(dest="cmd", required=True, parser_class=Parser)
    i = sub.add_parser("init")
    i.add_argument("--repo", type=repo_ref)
    i.add_argument("--project", type=project_ref)
    i.add_argument("--out")
    sub.add_parser("next").add_argument("--limit", type=positive, default=3)
    s = sub.add_parser("show")
    s.add_argument("number", type=issue_ref)
    s.add_argument("--body", action="store_true")
    sub.add_parser("work-order").add_argument("number", type=issue_ref)
    sub.add_parser("bullets").add_argument("number", type=int)
    c = sub.add_parser("claim")
    c.add_argument("number", type=issue_ref)
    c.add_argument("--branch", type=marker_value)
    c.add_argument("--phase", type=marker_value)
    pl = sub.add_parser("plan")
    pl.add_argument("number", type=int)
    pl.add_argument("--file", required=True)
    se = sub.add_parser("set")
    se.add_argument("number", type=int)
    se.add_argument("state")
    se.add_argument("--comment")
    fi = sub.add_parser("file")
    fi.add_argument("--title", required=True)
    fi.add_argument("--body-file", required=True)
    fi.add_argument("--priority", required=True, choices=PRIORITIES)
    fi.add_argument("--found-in", type=positive)
    fi.add_argument("--type")
    fi.add_argument("--new", action="store_true")
    r = sub.add_parser("rank")
    r.add_argument("number", type=int)
    r.add_argument("priority", choices=PRIORITIES)
    n = sub.add_parser("note")
    n.add_argument("number", type=int)
    n.add_argument("--file", required=True)
    sub.add_parser("audit")
    return ap.parse_args(argv)


def emit(code, obj):
    """One JSON object carrying its own exit code: a caller that sees only stdout still knows the outcome."""
    print(json.dumps({"ok": code == 0, "exit": code, **obj}, ensure_ascii=False, separators=(",", ":")))
    return code


def main(argv=None):
    t = None
    try:
        args = parse(sys.argv[1:] if argv is None else argv)
        t = Tracker(None if args.cmd == "init" else load_policy(args.policy))
        out = globals()[f"cmd_{args.cmd.replace('-', '_')}"](t, args)
        if args.cmd in ("bullets", "claim", "plan", "set", "file", "rank", "note"):
            out["writes"] = t.writes
        return emit(0, out)
    except Usage as e:
        return emit(2, {"error": "usage", "message": str(e), **({"writes": t.writes} if t and t.writes else {})})
    except Refused as e:
        extra = dict(e.extra)
        if args.cmd == "claim":  # the fallback the steward returns, so a refusal needs no second call
            try:
                refused = {str(args.number), str(args.number).lstrip("#")}  # never offer the item just refused again
                extra["next_candidates"] = [c for c in cmd_next(t, argparse.Namespace(limit=4))["candidates"]
                                            if c["id"] not in refused and str(c["number"]) not in refused][:3]
            except (Usage, GhFailed):
                pass
        return emit(3, {"reason": e.reason, "detail": e.detail, **extra, "writes": t.writes if t else []})
    except GhFailed as e:
        sys.stderr.write(e.message if e.message.endswith("\n") else e.message + "\n")
        return emit(4, {"error": "gh_failed", "operation": e.op, "message": e.message.strip(),
                        "failed_write": getattr(e, "what", None), "writes": t.writes if t else []})


if __name__ == "__main__":
    sys.exit(main())
