"""RewardKit criteria shared by the planner tasks (E18-E21).

prepare.py copies this file into each plan task's tests/ as _plan_rules.py. Every
criterion is shared, so this file registers no score itself. A criterion must
return False rather than raise: an exception aborts the whole RewardKit run and no
reward is written.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

from rewardkit import criterion

EXPECTED = Path(__file__).with_name("expected.json")
PLAN = "docs/plans/T1.md"
REPORT = "plan-report.json"
ROADMAP = "docs/roadmap/ROADMAP.md"
STATUSES = {"complete", "blocked"}


def _report(ws):
    try:
        data = json.loads((ws / REPORT).read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _text(value):
    return value if isinstance(value, str) else ""


def _flat(text):
    """Whitespace collapsed and backticks dropped, so a quote wrapped over lines or wrapped whole in code
    markup (inner backticks cannot nest) still matches."""
    return " ".join(_text(text).replace("`", "").split())


def _plan(ws):
    try:
        return (ws / PLAN).read_text(errors="ignore")
    except OSError:
        return ""


def _dicts(value):
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def _t1_lines(ws):
    """The T1 acceptance lines of the committed roadmap, without the list marker and `T1: ` prefix."""
    try:
        text = (ws / ROADMAP).read_text()
    except OSError:
        return []
    return [m.strip() for m in re.findall(r"^- T1: (.+)$", text, re.M)]


def _git(ws, *args):
    return subprocess.run(["git", "-C", str(ws), *args], capture_output=True, text=True).stdout


@criterion(shared=True)
def plan_report_exists_and_parses(workspace: Path) -> bool:
    data = _report(workspace)
    mapping, questions = data.get("acceptance_mapping"), data.get("open_questions")
    return (data.get("status") in STATUSES and isinstance(mapping, list) and isinstance(questions, list)
            and all(isinstance(m, dict) and _text(m.get("line")).strip() and _text(m.get("check")).strip()
                    for m in mapping)
            and all(isinstance(q, dict) and _text(q.get("question")).strip() for q in questions))


@criterion(shared=True)
def writes_only_the_plan(workspace: Path) -> bool:
    """No source, roadmap or Git change: the only new files are the plan and the report."""
    expected = json.loads(EXPECTED.read_text())["files"]
    actual = {p.relative_to(workspace).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(workspace.rglob("*"))
              if p.is_file() and p.relative_to(workspace).parts[0] != ".git"}
    extra = set(actual) - set(expected) - {PLAN, REPORT}
    return (all(actual.get(rel) == sha for rel, sha in expected.items()) and not extra
            and _git(workspace, "rev-list", "--count", "--all").strip() == "1"
            and _git(workspace, "symbolic-ref", "--short", "HEAD").strip() == "main"
            and not _git(workspace, "stash", "list").strip())


@criterion(shared=True)
def plan_quotes_t1_acceptance_verbatim(workspace: Path) -> bool:
    plan, lines = _flat(_plan(workspace)), _t1_lines(workspace)
    return bool(lines) and all(_flat(line) in plan for line in lines)


@criterion(shared=True)
def every_t1_line_mapped_to_a_test_check(workspace: Path) -> bool:
    mapping = _dicts(_report(workspace).get("acceptance_mapping"))
    lines = _t1_lines(workspace)
    return bool(lines) and all(
        any(_flat(line) in _flat(m.get("line")) and re.search(r"test", _text(m.get("check")), re.I)
            for m in mapping)
        for line in lines)


@criterion(shared=True)
def mapping_excludes_sibling_acceptance(workspace: Path) -> bool:
    return not any(re.search(r"filterByTag|summary\(items\)", _text(m.get("line")))
                   for m in _dicts(_report(workspace).get("acceptance_mapping")))


@criterion(shared=True)
def fence_names_t2_and_t3_out_of_scope(workspace: Path) -> bool:
    """Each sibling bullet named on one line with the deliverable it owns."""
    plan = _plan(workspace)
    return (re.search(r"^.*\bT2\b.*filter.*$", plan, re.M | re.I) is not None
            and re.search(r"^.*\bT3\b.*summary.*$", plan, re.M | re.I) is not None)


@criterion(shared=True)
def plan_targets_t1_files(workspace: Path) -> bool:
    plan = _plan(workspace)
    return "src/items.mjs" in plan and "test/items.test.mjs" in plan


@criterion(shared=True)
def plan_names_the_existing_expectation_that_breaks(workspace: Path) -> bool:
    """The `parses title and url` test compares the whole object, so adding `tags` breaks it.
    ponytail: phrase list grown from real plans (whole/full/deep/exact object); a judge if it keeps growing."""
    return re.search(r"parses title and url|deep[- ]?equal|(?:whole|full|deep|exact|entire)[- ](?:item[- ])?object"
                     r"|existing\b[^.\n]{0,40}?\b(?:test|expectation|assertion)s?\b",
                     _plan(workspace), re.I) is not None


@criterion(shared=True)
def plan_adds_a_migration_step_and_bumps_the_version(workspace: Path) -> bool:
    """docs/storage.md: a new item field is a step in src/migrations.mjs and STORE_VERSION 3, not a patch in loadItems."""
    plan = _plan(workspace)
    return ("src/migrations.mjs" in plan
            and re.search(r"(?:STORE_VERSION|version)\D{0,25}\b3\b|\b2\s*(?:→|->|to)\s*3\b", plan, re.I) is not None)


@criterion(shared=True)
def plan_tests_a_list_saved_at_version_2(workspace: Path) -> bool:
    plan = _plan(workspace)
    return "list-v2" in plan and "store.test.mjs" in plan


@criterion(shared=True)
def reports_complete_without_questions(workspace: Path) -> bool:
    data = _report(workspace)
    return data.get("status") == "complete" and data.get("open_questions") == [] and data.get("plan") == PLAN


@criterion(shared=True, description="blocked with exactly one open question matching {pattern}, with a recommendation")
def one_open_question_with_recommendation(workspace: Path, pattern: str) -> bool:
    data = _report(workspace)
    questions = _dicts(data.get("open_questions"))
    return (data.get("status") == "blocked" and len(questions) == 1
            and re.search(pattern, _text(questions[0].get("question")), re.I) is not None
            and bool(_text(questions[0].get("recommendation")).strip()))
