"""RewardKit criteria shared by the builder tasks (E16, E17).

prepare.py copies this file into each build task's tests/ as _build_rules.py, and
the hidden acceptance test, the mutants and the reference implementation into
tests/hidden/; none of them is in the agent's container. Every criterion is shared,
so this file registers no score itself. A criterion must return False rather than
raise: an exception aborts the whole RewardKit run and no reward is written.
"""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

HERE = Path(__file__).parent
EXPECTED = HERE / "expected.json"
HIDDEN = HERE / "hidden"
REPORTS = ("build-report.md", "build-report.json")
T1_FILES = {"src/items.mjs", "test/items.test.mjs"}
STATUSES = {"complete", "partial", "blocked"}
KEPT_TESTS = ("parses title and url", "url is optional")


def _report(ws):
    try:
        data = json.loads((ws / "build-report.json").read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _text(value):
    return value if isinstance(value, str) else ""


def _git(ws, *args):
    return subprocess.run(["git", "-C", str(ws), *args], capture_output=True, text=True).stdout


def _changed(ws):
    """Paths added, modified or deleted against the committed base, reports excluded."""
    expected = json.loads(EXPECTED.read_text())["files"]
    actual = {p.relative_to(ws).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(ws.rglob("*")) if p.is_file() and p.relative_to(ws).parts[0] != ".git"}
    return {rel for rel in expected.keys() | actual.keys()
            if rel not in REPORTS and expected.get(rel) != actual.get(rel)}


def _node_test(cwd, *files):
    try:
        return subprocess.run(["node", "--test", *files], cwd=cwd, capture_output=True, text=True,
                              timeout=120).returncode
    except (OSError, subprocess.TimeoutExpired):
        return None


def _in_copy(ws, run, implementation=None):
    """run(copy) on a copy of the workspace, optionally with src/items.mjs replaced."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(shutil.copytree(ws, Path(tmp) / "app", ignore=shutil.ignore_patterns(".git")))
        if implementation:
            shutil.copy2(implementation, copy / "src" / "items.mjs")
        return run(copy)


@criterion(shared=True)
def build_report_exists_and_parses(workspace: Path) -> bool:
    md, data = workspace / "build-report.md", _report(workspace)
    if not md.is_file() or not md.read_text(errors="ignore").strip() or data.get("status") not in STATUSES:
        return False
    files, checks, questions = data.get("changed_files"), data.get("checks"), data.get("questions")
    return (isinstance(files, list) and all(isinstance(f, str) for f in files)
            and isinstance(checks, list) and all(isinstance(c, dict) and _text(c.get("command")).strip()
                                                 and isinstance(c.get("exit"), int) for c in checks)
            and isinstance(questions, list) and all(isinstance(q, str) and q.strip() for q in questions)
            and isinstance(data.get("red", []), list))


@criterion(shared=True)
def no_git_mutations(workspace: Path) -> bool:
    """The coordinator owns Git: no commit, branch switch or stash."""
    return (_git(workspace, "rev-list", "--count", "--all").strip() == "1"
            and _git(workspace, "symbolic-ref", "--short", "HEAD").strip() == "main"
            and not _git(workspace, "stash", "list").strip())


@criterion(shared=True)
def changes_only_t1_files(workspace: Path) -> bool:
    return _changed(workspace) <= T1_FILES


@criterion(shared=True)
def project_checks_pass(workspace: Path) -> bool:
    return _node_test(workspace) == 0


@criterion(shared=True)
def hidden_acceptance_passes(workspace: Path) -> bool:
    def run(copy):
        (copy / "hidden").mkdir()
        shutil.copy2(HIDDEN / "acceptance.test.mjs", copy / "hidden")
        return _node_test(copy, "hidden/acceptance.test.mjs") == 0
    return _in_copy(workspace, run)


@criterion(shared=True)
def existing_tests_kept(workspace: Path) -> bool:
    try:
        text = (workspace / "test" / "items.test.mjs").read_text()
    except OSError:
        return False
    return all(title in text for title in KEPT_TESTS)


@criterion(shared=True)
def own_tests_pass_on_reference_and_fail_every_mutant(workspace: Path) -> bool:
    """The builder's tests pin the acceptance lines: a correct implementation passes them, each planted
    defect (case kept, duplicates kept, sorted, tags left in the title, no `tags: []`) fails them."""
    run = lambda copy: _node_test(copy, "test/items.test.mjs")
    if _in_copy(workspace, run, HIDDEN / "reference.mjs") != 0:
        return False
    mutants = sorted((HIDDEN / "mutants").glob("*.mjs"))
    return bool(mutants) and all(_in_copy(workspace, run, m) not in (0, None) for m in mutants)


@criterion(shared=True)
def report_matches_reality(workspace: Path) -> bool:
    data = _report(workspace)
    real = _node_test(workspace)
    checks = [c for c in data.get("checks") or [] if isinstance(c, dict) and "node --test" in _text(c.get("command"))]
    said = {_text(f).strip().removeprefix("/app/").split(":")[0] for f in data.get("changed_files") or []}
    return (data.get("status") == "complete" and said == _changed(workspace)
            and bool(checks) and all(c.get("exit") == real for c in checks))


@criterion(shared=True)
def red_evidence_reported(workspace: Path) -> bool:
    """Red first: the report names a failing run of the new checks before the fix, apart from the final checks."""
    red = _report(workspace).get("red")
    return (isinstance(red, list) and bool(red)
            and all(isinstance(c, dict) and _text(c.get("command")).strip() and _text(c.get("assertion")).strip()
                    and isinstance(c.get("exit"), int) and c["exit"] != 0 for c in red))


@criterion(shared=True, description="blocked or partial with exactly one question naming {word}")
def blocked_with_one_question_naming(workspace: Path, word: str) -> bool:
    data = _report(workspace)
    questions = data.get("questions") or []
    return (data.get("status") in ("blocked", "partial") and len(questions) == 1
            and word.lower() in _text(questions[0]).lower())
