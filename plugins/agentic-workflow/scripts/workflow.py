#!/usr/bin/env python3
"""Local work routing and curated graph lookup. Python 3.10+, Git, macOS/Linux."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from graphlib import TopologicalSorter

PLUGIN = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def git(project, *args):
    return subprocess.check_output(["git", "-C", str(project), *args], stderr=subprocess.PIPE)


def repository(project):
    return Path(os.fsdecode(git(project, "rev-parse", "--show-toplevel")).strip()).resolve()


def snapshot(project):
    """Hash current files/index, not merely HEAD. Ignored files are outside the contract."""
    digest = hashlib.sha256()
    def add(value):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    head_result = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify", "HEAD"], capture_output=True)
    head = head_result.stdout if head_result.returncode == 0 else b""
    add(head)
    add(git(project, "ls-files", "--stage", "-z"))
    paths = set(git(project, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0")) - {b""}
    for raw in sorted(paths):
        path = project / os.fsdecode(raw)
        add(raw)
        if path.is_symlink():
            add(b"link:" + os.fsencode(os.readlink(path)))
        elif path.is_file():
            add(str(path.stat().st_mode & 0o777).encode())
            with path.open("rb") as handle:
                content = hashlib.file_digest(handle, "sha256").digest() if hasattr(hashlib, "file_digest") else hashlib.sha256(handle.read()).digest()
            add(content)
        elif path.is_dir():
            # Gitlinks need their own content identity; ordinary files cannot be directories.
            require((path / ".git").exists(), f"Cannot fingerprint directory replacing tracked file: {raw!r}")
            add(snapshot(path)["fingerprint"].encode())
        else:
            add(b"missing")
    branch = git(project, "rev-parse", "--abbrev-ref", "HEAD").decode().strip() if head else None
    return {"project": str(project), "head": head.decode().strip() or None,
            "branch": branch, "fingerprint": digest.hexdigest()}


def validate_graph(graph):
    nodes = graph.get("nodes", {})
    require(graph.get("version") == 1 and graph.get("start") in nodes, "Invalid graph version/start")
    require("escalate" in nodes and "done" in nodes, "Graph needs escalate and done nodes")
    require(type(graph.get("max_repairs")) is int and graph["max_repairs"] >= 0, "Invalid max_repairs")
    limit = graph.get("max_review_attempts", graph["max_repairs"] + 2)
    require(type(limit) is int and limit > 0, "Invalid max_review_attempts")
    reviewers = graph.get("required_reviewers")
    require(isinstance(reviewers, list) and reviewers and all(isinstance(r, str) and r for r in reviewers) and len(set(reviewers)) == len(reviewers), "Required reviewer IDs must be unique and nonempty")
    for name, node in nodes.items():
        require(node.get("gate") in {"artifacts", "review", "tests", "decision", "next"}, f"Unknown gate at {name}")
        require(isinstance(node.get("skill"), str) and isinstance(node.get("role"), str), f"Missing skill/role at {name}")
        require(isinstance(node.get("edges"), dict) and all(target in nodes for target in node["edges"].values()), f"Invalid edges at {name}")
    return graph


def artifact_paths(project, evidence):
    artifacts = evidence.get("artifacts")
    require(isinstance(artifacts, list) and artifacts, "At least one artifact is required")
    for name in artifacts:
        require(isinstance(name, str), "Artifact paths must be strings")
        path = (project / name).resolve()
        require(path.is_relative_to(project) and path.is_file(), f"Missing or external artifact: {name}")


def check_review(state, evidence, current):
    reviews = evidence.get("reviews")
    require(isinstance(reviews, list), "reviews must be a list")
    ids = [r.get("reviewer") for r in reviews]
    require(len(ids) == len(set(ids)), "Duplicate reviewer IDs")
    require(set(state["graph"]["required_reviewers"]) <= set(ids), "Required independent review is missing")
    ledger = dict(state.get("findings", {}))
    for review in reviews:
        require(review.get("status") == "complete", "Failed/incomplete review is not clean")
        require(review.get("fingerprint") == current["fingerprint"], "Review evidence is stale")
        require(review.get("evidence"), "Review needs its output/log reference")
        require(isinstance(review.get("findings"), list), "Each review needs an explicit findings list")
        for finding in review["findings"]:
            require(finding.get("id") and finding.get("reason"), "Finding needs ID and adjudication reason")
            require(finding.get("disposition") in {"resolved", "advisory", "rejected"}, "Unresolved actionable finding")
            ledger[finding["id"]] = finding
    require(all(f["disposition"] != "actionable" for f in ledger.values()), "Earlier actionable finding disappeared without adjudication")
    state["findings"] = ledger


def advance(state, outcome, evidence, current):
    graph = state["graph"]
    node = graph["nodes"][state["node"]]
    require(outcome in node["edges"], f"Illegal outcome {outcome!r} at {state['node']}")
    require(isinstance(evidence, dict) and isinstance(evidence.get("summary"), str) and evidence["summary"].strip(), "Evidence needs a nonempty summary")
    target = node["edges"][outcome]
    gate = node["gate"]
    if outcome == "complete" and gate == "artifacts":
        artifact_paths(Path(state["project"]), evidence)
        if state["node"] == "plan":
            checks = evidence.get("required_checks")
            require(isinstance(checks, list) and checks and all(isinstance(c, str) and c.strip() for c in checks), "Plan must name required check commands")
            state["required_checks"] = list(dict.fromkeys(checks))
    if gate == "review":
        state["review_attempts"] += 1
        if outcome == "fix":
            findings = evidence.get("findings")
            require(isinstance(findings, list) and findings, "Fix outcome needs adjudicated findings")
            for finding in findings:
                require(finding.get("id") and finding.get("reason") and finding.get("disposition") == "actionable", "Fix finding needs id, reason and actionable disposition")
                state.setdefault("findings", {})[finding["id"]] = finding
        if outcome == "clean":
            check_review(state, evidence, current)
            state["reviewed_fingerprint"] = current["fingerprint"]
    if gate == "tests" and outcome == "pass":
        require(state.get("reviewed_fingerprint") == current["fingerprint"], "Final code lacks current clean review coverage")
        checks = evidence.get("checks")
        require(isinstance(checks, list) and checks, "Required checks must be recorded")
        required = state.get("required_checks")
        require(required and set(required) <= {c.get("command") for c in checks}, "A planned required check is missing")
        require(evidence.get("acceptance_complete") is True, "Acceptance criteria are incomplete")
        for check in checks:
            require(check.get("command") and check.get("evidence"), "Check needs command and output reference")
            require(type(check.get("exit_code")) is int and check["exit_code"] == 0, "Required check did not pass")
            require(check.get("fingerprint") == current["fingerprint"], "Test evidence is stale")
    if gate == "decision":
        require(evidence.get("decision") and evidence.get("next_action"), "Escalation needs a diagnosis/decision and next action")
        additional = evidence.get("additional_repairs", 0)
        require(type(additional) is int and additional >= 0, "additional_repairs must be nonnegative")
        if additional:
            require(evidence.get("authorization"), "Extending a review budget needs the user's authorization reference")
            graph["max_repairs"] += additional
            graph["max_review_attempts"] = graph.get("max_review_attempts", state["review_attempts"]) + additional + 1
    if gate == "next":
        require(isinstance(evidence.get("slice"), str) and evidence["slice"].strip() and evidence["slice"] != state["slice"], "Next requires a different slice ID")
        state["slice"] = evidence["slice"]
        state["repair_rounds"] = state["review_attempts"] = 0
        state.pop("reviewed_fingerprint", None)
        state.pop("required_checks", None)
        state["findings"] = {}
    if target == "repair":
        state["repair_rounds"] += 1
        state.pop("reviewed_fingerprint", None)
    limit = graph.get("max_review_attempts", graph["max_repairs"] + 2)
    if (target == "repair" and state["repair_rounds"] > graph["max_repairs"]) or (gate == "review" and outcome != "clean" and state["review_attempts"] >= limit):
        target = "escalate"
    state["history"].append({"node": state["node"], "outcome": outcome, "target": target,
                             "evidence": evidence, "snapshot": current, "at": now()})
    state["node"] = target
    state["snapshot"] = current
    state["revision"] += 1
    return state


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path, data):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def knowledge_context(graph, seed, hops, limit):
    require(isinstance(graph.get("nodes"), list) and isinstance(graph.get("edges"), list), "Knowledge graph needs nodes and edges arrays")
    for node in graph["nodes"]:
        require(isinstance(node.get("id"), str) and node["id"] and node.get("kind") and node.get("label") and node.get("source"), "Node needs id, kind, label and provenance")
        require(node.get("status") in {"accepted", "proposed", "superseded"}, "Invalid node status")
    nodes = {n["id"]: n for n in graph["nodes"]}
    require(len(nodes) == len(graph["nodes"]), "Duplicate node ID")
    dependencies = {key: set() for key in nodes}
    for edge in graph["edges"]:
        require(edge.get("from") in nodes and edge.get("to") in nodes, "Dangling edge")
        require(edge.get("relation") and edge.get("source"), "Edge needs relation and provenance")
        require(edge.get("status", "accepted") in {"accepted", "proposed", "superseded"}, "Invalid edge status")
        if edge["relation"] == "depends_on" and edge.get("status", "accepted") == "accepted":
            dependencies[edge["from"]].add(edge["to"])
    tuple(TopologicalSorter(dependencies).static_order())
    if seed is None:
        return {"valid": True, "nodes": len(nodes), "edges": len(graph["edges"])}
    require(seed in nodes, f"Unknown seed: {seed}")
    require(0 <= hops <= 5 and 1 <= limit <= 100, "Use hops 0..5 and limit 1..100")
    accepted = {key for key, node in nodes.items() if node.get("status") == "accepted"}
    require(seed in accepted, "Seed must be accepted; inspect proposed/superseded nodes explicitly")
    edges = [e for e in graph["edges"] if e.get("status", "accepted") == "accepted" and e["from"] in accepted and e["to"] in accepted]
    selected, frontier = [seed], {seed}
    omitted = False
    for _ in range(hops):
        neighbors = {other for e in edges for endpoint, other in [(e["from"], e["to"]), (e["to"], e["from"])] if endpoint in frontier} - set(selected)
        available = sorted(neighbors)
        room = limit - len(selected)
        omitted |= len(available) > room
        frontier = set(available[:room])
        selected.extend(sorted(frontier))
        if not frontier:
            break
    return {"nodes": [nodes[key] for key in selected],
            "edges": [e for e in edges if e["from"] in selected and e["to"] in selected],
            "truncated": omitted, "hops": hops, "coverage": "bounded neighborhood, not exhaustive"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("snapshot")
    sub.add_parser("list")
    init = sub.add_parser("init")
    init.add_argument("task")
    init.add_argument("--slice", default="discovery")
    init.add_argument("--graph", default=str(PLUGIN / "graphs/development.json"))
    for command in ["status", "advance", "note", "recover"]:
        cmd = sub.add_parser(command)
        cmd.add_argument("task")
        if command != "status":
            cmd.add_argument("--revision", type=int, required=True)
            cmd.add_argument("--evidence", required=True, help="JSON file; '-' reads stdin")
        if command == "advance":
            cmd.add_argument("outcome")
    context = sub.add_parser("context")
    context.add_argument("graph")
    context.add_argument("--seed")
    context.add_argument("--hops", type=int, default=2)
    context.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()
    if args.command == "context":
        return knowledge_context(read(args.graph), args.seed, args.hops, args.limit)
    project = repository(args.project)
    if args.command == "snapshot":
        return snapshot(project)
    common = Path(os.fsdecode(git(project, "rev-parse", "--git-common-dir")).strip())
    directory = (project / common).resolve() / "agentic-workflow"
    directory.mkdir(exist_ok=True)
    if args.command == "list":
        return {"runs": [p.stem for p in sorted(directory.glob("*.json"))], "directory": str(directory)}
    require(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", args.task), "Invalid task ID")
    path = directory / (args.task + ".json")
    # ponytail: one short lock per repository; use per-task locks if contention is measured.
    with (directory / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = snapshot(project)
        if args.command == "init":
            require(not path.exists(), "Task already exists; use status/resume")
            graph = validate_graph(read(args.graph))
            state = {"version": 1, "task": args.task, "slice": args.slice, "project": str(project),
                     "graph": graph, "node": graph["start"], "revision": 0,
                     "snapshot": current, "repair_rounds": 0, "review_attempts": 0, "history": []}
            atomic_write(path, state)
        else:
            state = read(path)
            require(state["project"] == str(project), f"Run belongs to worktree {state['project']}; use that worktree")
            if args.command != "status":
                require(args.revision == state["revision"], "Stale revision; reread status")
                evidence = json.load(sys.stdin) if args.evidence == "-" else read(args.evidence)
                if args.command == "advance":
                    # Working edits are expected in these nodes, but not during frozen review/verification.
                    if state["node"] in {"review", "verify", "done"}:
                        require(current == state["snapshot"], "Work changed during review/verification; use recover before advancing")
                    state = advance(state, args.outcome, evidence, current)
                else:
                    require(isinstance(evidence, dict) and evidence.get("next_action"), "Checkpoint needs next_action")
                    if args.command == "recover":
                        require(evidence.get("reason"), "Recovery needs an explanation of changed work")
                        if state["node"] in {"review", "verify", "done"}:
                            state["node"] = "review"
                        state.pop("reviewed_fingerprint", None)
                        state["snapshot"] = current
                    state["history"].append({"node": state["node"], "outcome": args.command, "evidence": evidence, "snapshot": current, "at": now()})
                    state["revision"] += 1
                atomic_write(path, state)
        node = state["graph"]["nodes"][state["node"]]
        return {"state_path": str(path), "task": state["task"], "slice": state["slice"],
                "node": state["node"], "role": node["role"], "skill": node["skill"],
                "outcomes": list(node["edges"]), "revision": state["revision"],
                "work_changed": current != state["snapshot"], "current_snapshot": current,
                "repair_rounds": state["repair_rounds"], "review_attempts": state["review_attempts"],
                "findings": state.get("findings", {}),
                "last_event": state["history"][-1] if state["history"] else None}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), indent=2))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
