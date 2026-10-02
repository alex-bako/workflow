#!/usr/bin/env python3
"""(Re)generate the ignored build inputs of every Harbor task under tasks/.

Each task names its case in tests/case.json ({"kind": ..., ...}). For every task
this writes environment/bundle/ (the sanitized plugin, mounted at /opt/aw), the
kind's fixture files, and copies lib/<kind>_rules.py to tests/_<kind>_rules.py.
Stdlib only. Run it after any plugin or fixture change, then `harbor run`.
`prepare.py TASK...` prepares only the named tasks, so a running job keeps its inputs.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[1]
EVALS = PLUGIN / "evals"
BUNDLE_PARTS = ("agents", "references", "skills", "scripts")
# Evaluator material never enters the agent's container.
EXCLUDED = ("references/evals.md", "skills/aw-eval")
LEAK_MARKERS = ("evals.md", "aw-eval", "evals/")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def fresh(path):
    shutil.rmtree(path, ignore_errors=True)
    return path


def tree(root):
    """{relative posix path: sha256} of every file under root."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def build_bundle(dest):
    fresh(dest)
    for part in BUNDLE_PARTS:
        shutil.copytree(PLUGIN / part, dest / part, ignore=IGNORE)
    shutil.copy2(PLUGIN / "models.json", dest / "models.json")  # run_worker.py maps tiers through it
    for rel in EXCLUDED:
        target = dest / rel
        shutil.rmtree(target) if target.is_dir() else target.unlink()
    leaks = [rel for rel in tree(dest)
             if any(m in (dest / rel).read_text(errors="ignore") for m in LEAK_MARKERS)]
    if leaks:
        sys.exit(f"bundle links evaluator material: {', '.join(leaks)}")


def build_qa(task, case):
    """E10/E11: base project committed in the image, variant overlaid uncommitted."""
    scope = EVALS / "scope"
    ws = fresh(task / "environment" / "workspace")
    base, change = ws / "base", ws / "change"
    shutil.copytree(scope / "project", base, ignore=IGNORE)
    (base / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    shutil.copy2(scope / "plan.md", base / "docs" / "plans" / "T1.md")
    shutil.copytree(scope / case["variant"], change, ignore=IGNORE)
    base_files, changed = tree(base), tree(change)
    expected = {
        "files": {**base_files, **changed},
        "status": sorted((" M " if rel in base_files else "?? ") + rel for rel in changed),
    }
    (task / "tests" / "expected.json").write_text(json.dumps(expected, indent=1) + "\n")


# --- router (E12) -------------------------------------------------------------
def build_router(task, case):
    """E12: base + plan committed (tag `base`); the image commits the variant patch as head."""
    import subprocess
    import tempfile
    router = EVALS / "router"
    ws = fresh(task / "environment" / "workspace")
    base = ws / "base"
    shutil.copytree(router / "base", base, ignore=IGNORE)
    (base / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    shutil.copy2(router / "plan.md", base / "docs" / "plans" / "T1.md")
    patch = shutil.copy2(router / case["patch"], ws / "head.patch")
    with tempfile.TemporaryDirectory() as tmp:
        head = shutil.copytree(base, Path(tmp) / "head")
        git = ["git", "apply", str(patch)]
        numstat = subprocess.run(git[:2] + ["--numstat"] + git[2:], cwd=head, check=True,
                                 capture_output=True, text=True).stdout
        subprocess.run(git, cwd=head, check=True)
        expected = {"files": tree(head),
                    "changed": sorted(line.split("\t")[2] for line in numstat.splitlines())}
    (task / "tests" / "expected.json").write_text(json.dumps(expected, indent=1) + "\n")
# --- end router ---------------------------------------------------------------


# --- tracker (E7-E9, E13) -----------------------------------------------------
# /opt/tools/gh (AW_TRACKER_GH) runs the fake and records, per call, the calling
# process's argv, the sha256 of the script it ran and the range of mutation-log lines
# the call wrote, so the verifier can tie every log entry to an unmodified tracker.py.
# The stub installed as `gh` first on PATH records and refuses any direct call.
TRACKER_WRAPPER = r"""#!/usr/bin/env python3
import hashlib, json, os, subprocess, sys
log = os.environ.get("AW_FAKE_GH_STATE", "/opt/tools/state.json") + ".log"
def lines():
    try:
        with open(log, "rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0
ppid = os.getppid()
try:
    with open(f"/proc/{ppid}/cmdline", "rb") as fh:
        argv = [a.decode(errors="replace") for a in fh.read().split(b"\0")[:-1]]
    script = os.path.join(os.readlink(f"/proc/{ppid}/cwd"), argv[1]) if len(argv) > 1 else ""
    with open(script, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
except (OSError, IndexError):
    argv, script, sha = [], "", None
before = lines()
code = subprocess.run([sys.executable, "/opt/tools/fake-gh", *sys.argv[1:]]).returncode
with open("/var/log/tracker-calls.log", "a") as fh:
    fh.write(json.dumps({"pid": ppid, "argv": argv, "script": script, "sha": sha,
                         "log": [before, lines()]}) + "\n")
sys.exit(code)
"""
DIRECT_GH = """#!/bin/sh
echo "$*" >> /var/log/gh-direct.log
echo "gh: not available here" >&2
exit 1
"""


def build_tracker(task, case):
    """E7-E9, E15 (fixture steward) and E13 (fixture loop): project, policy, board, tools."""
    env, tests = task / "environment", task / "tests"
    tools, ws = fresh(env / "tools"), fresh(env / "workspace")
    tools.mkdir(parents=True)
    expected = {}
    if case["fixture"] == "loop":
        scope = EVALS / "scope"
        base = shutil.copytree(scope / "project", ws / "base", ignore=IGNORE)
        state = json.loads((scope / "state.json").read_text())
        authority = "docs/roadmap/ROADMAP.md"
        files = shutil.copytree(scope / "change-a", fresh(task / "solution" / "files"), ignore=IGNORE)
        plan = (scope / "plan.md").read_text()
        (files / "plan.md").write_text(plan)
        expected["acceptance"] = [line[2:] for line in plan.splitlines() if line.startswith("- T1:")]
    else:
        steward = EVALS / "tracker" / "steward"
        state = json.loads((steward / "state.json").read_text())
        base = ws / "base"
        base.mkdir(parents=True)
        shutil.copy2(steward / "ROADMAP.md", base / "ROADMAP.md")
        authority = "ROADMAP.md"
    for number, fields in case.get("set", {}).items():
        next(i for i in state["items"] if i["number"] == int(number)).update(fields)
    if case.get("fail"):
        state["fail"] = case["fail"]
    # intake (E15): report files under /app, extra board issues, the repository's labels
    intake = EVALS / "tracker" / "intake"
    for dest, src in case.get("files", {}).items():
        (base / dest).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(intake / src, base / dest)
    state["items"] += [json.loads((intake / src).read_text()) for src in case.get("add", [])]
    if "labels" in case:
        state["labels"] = case["labels"]
    policy = json.loads((EVALS / "tracker" / "tracker-policy.json").read_text())
    policy.update(authority=authority, merge={"allowed": False, "method": "rebase"},
                  items={"label": "roadmap", "exclude_labels": ["epic"], "startable_states": ["ready"]})
    policy["order"].update(file=authority, start="### Next up", end="### ")
    policy["bullets"]["label"] = "tracer-bullet"
    (base / "tracker-policy.json").write_text(json.dumps(policy, indent=1, ensure_ascii=False) + "\n")
    (tools / "state.json").write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n")
    fake = (EVALS / "tracker" / "gh").read_text().split("\n")
    fake[1] = '"""Local tracker backend for tracker.py."""'  # neutral in-container wording
    (tools / "fake-gh").write_text("\n".join(fake))
    shutil.copy2(tools / "fake-gh", tests / "fake-gh")  # the verifier replays the log with it
    (tools / "gh").write_text(TRACKER_WRAPPER)
    (tools / "direct-gh").write_text(DIRECT_GH)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    expected.update(initial=state, files=tree(base), hashes={
        "/opt/tools/gh": sha(tools / "gh"), "/opt/tools/fake-gh": sha(tools / "fake-gh"),
        "/opt/aw/scripts/tracker.py": sha(env / "bundle" / "scripts" / "tracker.py")})
    (tests / "expected.json").write_text(json.dumps(expected, indent=1, ensure_ascii=False) + "\n")
# --- end tracker --------------------------------------------------------------


# --- gate (E14) ---------------------------------------------------------------
def build_gate(task, case):
    """E14: the project with plan, overlaid by the variant's ledger and sources; no git."""
    gate = EVALS / "gate"
    ws = shutil.copytree(gate / "project", fresh(task / "environment" / "workspace"), ignore=IGNORE)
    shutil.copytree(gate / case["variant"], ws, ignore=IGNORE, dirs_exist_ok=True)
    (task / "tests" / "expected.json").write_text(json.dumps({"files": tree(ws)}, indent=1) + "\n")
# --- end gate -----------------------------------------------------------------


# --- build and plan (E16-E19) -------------------------------------------------
def scope_project(task):
    ws = shutil.copytree(EVALS / "scope" / "project", fresh(task / "environment" / "workspace"), ignore=IGNORE)
    (ws / "docs" / "plans").mkdir(parents=True, exist_ok=True)
    return ws


def build_build(task, case):
    """E16/E17: the project with the accepted plan, committed; hidden acceptance test and mutants for the verifier."""
    ws = scope_project(task)
    shutil.copy2(EVALS / case["plan"], ws / "docs" / "plans" / "T1.md")
    shutil.copytree(EVALS / "build" / "hidden", fresh(task / "tests" / "hidden"), ignore=IGNORE)
    shutil.copy2(EVALS / "build" / "reference" / "src" / "items.mjs", task / "tests" / "hidden" / "reference.mjs")
    shutil.copytree(EVALS / "build" / "reference", fresh(task / "solution" / "files"), ignore=IGNORE)
    (task / "tests" / "expected.json").write_text(json.dumps({"files": tree(ws)}, indent=1) + "\n")


def build_plan(task, case):
    """E18-E21: the project without a plan, committed; overlays (later wins) and the roadmap may vary it."""
    ws = scope_project(task)
    for overlay in case.get("overlays", []):
        shutil.copytree(EVALS / overlay, ws, dirs_exist_ok=True, ignore=IGNORE)
    if case.get("roadmap"):
        shutil.copy2(EVALS / case["roadmap"], ws / "docs" / "roadmap" / "ROADMAP.md")
    files = fresh(task / "solution" / "files")
    files.mkdir(parents=True)
    shutil.copy2(EVALS / case.get("solution", "scope/plan.md"), files / "T1.md")
    (task / "tests" / "expected.json").write_text(json.dumps({"files": tree(ws)}, indent=1) + "\n")
# --- end build and plan -------------------------------------------------------


BUILDERS = {"qa": build_qa}
BUILDERS["build"] = build_build  # builder (E16, E17)
BUILDERS["plan"] = build_plan  # planner (E18-E21)
BUILDERS["router"] = build_router  # router (E12)
BUILDERS["tracker"] = build_tracker  # tracker (E7-E9, E13)
BUILDERS["gate"] = build_gate  # gate (E14)


def main():
    only = set(sys.argv[1:])
    for task in sorted(p for p in (HERE / "tasks").iterdir() if p.is_dir() and (not only or p.name in only)):
        case = json.loads((task / "tests" / "case.json").read_text())
        build_bundle(task / "environment" / "bundle")
        BUILDERS[case["kind"]](task, case)
        rules = HERE / "lib" / f"{case['kind']}_rules.py"
        if rules.exists():
            shutil.copy2(rules, task / "tests" / f"_{case['kind']}_rules.py")
        print(f"prepared {task.name}")


if __name__ == "__main__":
    main()
