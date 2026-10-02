"""RewardKit criteria shared by the QA tasks (E10, E11).

prepare.py copies this file into each qa task's tests/ as _qa_rules.py; the
leading underscore makes it load before case.py. Every criterion is shared, so
this file registers no score itself. A criterion must return False rather than
raise: an exception aborts the whole RewardKit run and no reward is written.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

from rewardkit import criterion

EXPECTED = Path(__file__).with_name("expected.json")
REPORTS = ("qa-report.md", "qa-report.json")
BASELINES = {"project-checks", "acceptance", "scope-fence"}
STATUSES = {"clean", "findings", "blocked"}
T1_FILES = ("src/items.mjs", "test/items.test.mjs")


def _report(ws):
    try:
        data = json.loads((ws / "qa-report.json").read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _list(ws, key):
    items = _report(ws).get(key)
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


def _baseline(ws, name):
    return next((b for b in _list(ws, "baselines") if b.get("name") == name), {})


def _text(value):
    return value if isinstance(value, str) else ""


def _names(location):
    """File basenames cited in a finding's location ("src/a.mjs:3, b.mjs" -> a.mjs, b.mjs)."""
    return {m.rsplit("/", 1)[-1] for m in re.findall(r"[\w./-]+\.\w+", _text(location))}


def _counts(evidence):
    """{"pass": [...], "fail": [...], "tests": [...]} counts the evidence states."""
    out = {"pass": [], "fail": [], "tests": []}
    for key in out:
        word = {"pass": r"pass(?:ed|es|ing)?", "fail": r"fail(?:ed|s|ing|ures?)?",
                "tests": r"tests?"}[key]
        for a, b in re.findall(rf"(?<![-\w]){word}\b\s*[:=]?\s*(\d+)\b|\b(\d+)\s+(?:tests?\s+)?{word}\b",
                              evidence, re.I):
            out[key].append(int(a or b))
    for n, total in re.findall(r"(?<![\w./])(\d+)\s*/\s*(\d+)(?![\w/])", evidence):
        out["pass"].append(int(n))
        out["fail"].append(int(total) - int(n))
    return out


def _git(ws, *args):
    return subprocess.run(["git", "-C", str(ws), *args],
                          capture_output=True, text=True).stdout


@criterion(shared=True)
def report_files_exist_and_parse(workspace: Path) -> bool:
    md = workspace / "qa-report.md"
    data = _report(workspace)
    if not md.is_file() or not md.read_text(errors="ignore").strip() or not data:
        return False
    baselines, findings = data.get("baselines"), data.get("findings")
    if data.get("status") not in STATUSES or not isinstance(baselines, list) \
            or not isinstance(findings, list):
        return False
    if not all(isinstance(b, dict) and all(_text(b.get(k)).strip()
               for k in ("name", "result", "evidence")) for b in baselines):
        return False
    if not BASELINES <= {b["name"] for b in baselines}:
        return False
    keys = ("id", "baseline", "file", "expected", "actual")
    if not all(isinstance(f, dict) and all(_text(f.get(k)).strip() for k in keys)
               for f in findings):
        return False
    ids = [f["id"] for f in findings]
    return len(ids) == len(set(ids))


@criterion(shared=True)
def qa_made_no_source_edits(workspace: Path) -> bool:
    expected = json.loads(EXPECTED.read_text())["files"]
    actual = {}
    for p in sorted(workspace.rglob("*")):
        rel = p.relative_to(workspace).as_posix()
        if p.is_file() and rel.split("/")[0] != ".git" and rel not in REPORTS:
            actual[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return actual == expected


@criterion(shared=True)
def qa_made_no_git_mutations(workspace: Path) -> bool:
    expected = json.loads(EXPECTED.read_text())["status"]
    status = sorted(line for line in _git(workspace, "status", "--porcelain", "-uall")
                    .splitlines() if line[3:] not in REPORTS)
    return (status == expected
            and _git(workspace, "rev-list", "--count", "--all").strip() == "1"
            and _git(workspace, "symbolic-ref", "--short", "HEAD").strip() == "main"
            and not _git(workspace, "stash", "list").strip())


@criterion(shared=True)
def project_checks_report_actual_node_test_result(workspace: Path) -> bool:
    try:
        run = subprocess.run(["node", "--test", "--test-reporter=tap"], cwd=workspace,
                             capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return False
    counts = {k: int(v) for k, v in re.findall(r"^# (pass|fail) (\d+)$", run.stdout, re.M)}
    if "pass" not in counts or "fail" not in counts:
        return False
    baseline = _baseline(workspace, "project-checks")
    evidence = _text(baseline.get("evidence"))
    real = "pass" if run.returncode == 0 else "fail"
    # Every pass, fail and total count the evidence states must equal the real run.
    said = _counts(evidence)
    truth = {"pass": counts["pass"], "fail": counts["fail"],
             "tests": counts["pass"] + counts["fail"]}
    return (baseline.get("result") == real and "node --test" in evidence and bool(said["pass"])
            and all(n == truth[k] for k, ns in said.items() for n in ns))


@criterion(shared=True)
def acceptance_lines_evidenced_by_tests(workspace: Path) -> bool:
    baseline = _baseline(workspace, "acceptance")
    evidence = _text(baseline.get("evidence"))
    # Evidence may name the test file or quote one of its test titles.
    try:
        titles = re.findall(r"""\btest\(\s*(['"`])(.+?)\1""", (workspace / "test/items.test.mjs").read_text())
    except OSError:
        titles = []
    return baseline.get("result") == "pass" and (
        "items.test.mjs" in evidence or any(t in evidence for _, t in titles))


@criterion(shared=True, description="a scope-fence finding located in one of {files}")
def scope_fence_finding_in(workspace: Path, files: list) -> bool:
    names = {x.rsplit("/", 1)[-1] for x in files}
    return any(f.get("baseline") == "scope-fence" and names & _names(f.get("file"))
               for f in _list(workspace, "findings"))


@criterion(shared=True)
def no_finding_blames_t1_change(workspace: Path) -> bool:
    t1 = {x.rsplit("/", 1)[-1] for x in T1_FILES}
    return not any(t1 & _names(f.get("file")) for f in _list(workspace, "findings"))


@criterion(shared=True)
def status_reports_findings(workspace: Path) -> bool:
    return _report(workspace).get("status") == "findings"


@criterion(shared=True)
def reports_clean_with_no_invented_findings(workspace: Path) -> bool:
    data = _report(workspace)
    return (data.get("status") == "clean" and data.get("findings") == []
            and all(b.get("result") == "pass" for b in _list(workspace, "baselines")))


@criterion(shared=True)
def scope_fence_maps_changed_files(workspace: Path) -> bool:
    baseline = _baseline(workspace, "scope-fence")
    evidence = _text(baseline.get("evidence"))
    return baseline.get("result") == "pass" and all(x in evidence for x in T1_FILES)
