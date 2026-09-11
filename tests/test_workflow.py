"""Behavior checks use disposable Git repositories; no model calls or credentials."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/agentic-workflow/scripts/workflow.py"
spec = importlib.util.spec_from_file_location("workflow", SCRIPT)
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name).resolve()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Workflow Test")
        (self.project / "scope.md").write_text("Accepted behavior\n")
        (self.project / "app.py").write_text("value = 1\n")
        self.git("add", ".")
        self.git("commit", "-m", "initial")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.project), *args], stderr=subprocess.PIPE)

    def cli(self, *args, evidence=None, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project), *args], input=json.dumps(evidence) if evidence is not None else None, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if success else 1, result.stderr)
        return json.loads(result.stdout if success else result.stderr)

    def advance(self, outcome, evidence, success=True):
        state = self.cli("status", "sample")
        return self.cli("advance", "sample", outcome, "--revision", str(state["revision"]), "--evidence", "-", evidence=evidence, success=success)

    def reach_review(self, delivery="local"):
        self.cli("init", "sample", "--slice", "M1.T1", "--delivery", delivery)
        for _ in range(5):
            self.advance("complete", {"summary": "Stage evidence inspected", "artifacts": ["scope.md"], "required_checks": ["python3 app.py", "git diff --check"]})
        return self.cli("status", "sample")

    def clean(self):
        fingerprint = self.cli("snapshot")["fingerprint"]
        return {"summary": "Independent reviews complete", "reviews": [
            {"reviewer": who, "status": "complete", "fingerprint": fingerprint, "evidence": "review-output.json", "findings": []}
            for who in ["specialist", "cross-model"]]}

    def checks(self):
        fingerprint = self.cli("snapshot")["fingerprint"]
        return {"summary": "Acceptance verified", "acceptance_complete": True, "checks": [
            {"command": command, "exit_code": 0, "fingerprint": fingerprint, "evidence": "checks.log"}
            for command in ["python3 app.py", "git diff --check"]]}

    def test_full_run_survives_fresh_processes_and_requires_all_checks(self):
        self.reach_review()
        self.assertEqual(self.advance("clean", self.clean())["node"], "verify")
        missing = self.checks()
        missing["checks"].pop()
        self.advance("pass", missing, success=False)
        self.assertEqual(self.cli("status", "sample")["node"], "verify")
        self.assertEqual(self.advance("pass", self.checks())["node"], "ready")
        self.assertEqual(self.advance("finish", {"summary": "Local-only delivery complete"})["node"], "done")
        self.assertEqual(self.advance("next", {"summary": "Next dependency-ready slice", "slice": "M1.T2"})["node"], "plan")

    def test_illegal_transition_and_stale_writer_leave_state_unchanged(self):
        initial = self.cli("init", "sample")
        self.advance("clean", {"summary": "skip work"}, success=False)
        self.cli("note", "sample", "--revision", "0", "--evidence", "-", evidence={"next_action": "Ask the domain question"})
        self.cli("note", "sample", "--revision", "0", "--evidence", "-", evidence={"next_action": "stale writer"}, success=False)
        state = self.cli("status", "sample")
        self.assertEqual(initial["node"], state["node"])
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["last_event"]["evidence"]["next_action"], "Ask the domain question")

    def test_incomplete_missing_stale_and_actionable_reviews_cannot_pass(self):
        self.reach_review()
        evidence = self.clean()
        evidence["reviews"].pop()
        self.advance("clean", evidence, success=False)
        for field, value in [("status", "incomplete"), ("fingerprint", "old"), ("findings", [{"id": "R1", "disposition": "actionable", "reason": "Missing authorization"}])]:
            evidence = self.clean()
            evidence["reviews"][0][field] = value
            self.advance("clean", evidence, success=False)
        self.assertEqual(self.cli("status", "sample")["node"], "review")

    def test_changed_work_invalidates_review_and_recovery_preserves_edits(self):
        self.reach_review()
        self.advance("clean", self.clean())
        old_checks = self.checks()
        (self.project / "app.py").write_text("value = 2\n")
        self.advance("pass", old_checks, success=False)
        state = self.cli("status", "sample")
        recovered = self.cli("recover", "sample", "--revision", str(state["revision"]), "--evidence", "-", evidence={"reason": "Inspected a concurrent fix", "next_action": "Review changed behavior"})
        self.assertEqual(recovered["node"], "review")
        self.assertEqual((self.project / "app.py").read_text(), "value = 2\n")
        self.advance("clean", self.clean())
        self.advance("pass", old_checks, success=False)
        self.assertEqual(self.advance("pass", self.checks())["node"], "ready")

    def publish(self, reviewers=None, checks=None, success=True):
        head = self.cli("snapshot")["head"]
        return self.advance("published", {"summary": "Published verified slice", "pull_request": {
            "url": "https://github.com/example/project/pull/1", "head": head,
            "reviewers": reviewers if reviewers is not None else ["remote-reviewer"],
            "checks": checks if checks is not None else ["ci"]}}, success=success)

    def remote_clean(self):
        current = self.cli("snapshot")
        return {"summary": "Remote inbox and checks inspected", "head": current["head"],
                "evidence": "remote-inbox.json", "inbox_complete": True, "pending_reviews": [],
                "reviews": [{"reviewer": "remote-reviewer", "status": "complete",
                             "fingerprint": current["fingerprint"], "evidence": "remote-review.json", "findings": []}],
                "checks": [{"name": "ci", "status": "success", "head": current["head"], "evidence": "ci.json"}]}

    def test_pr_creation_and_empty_stale_or_pending_reviews_cannot_finish(self):
        self.reach_review("pull-request")
        self.advance("clean", self.clean())
        self.advance("pass", self.checks())
        self.advance("finish", {"summary": "PR created, stop now"}, success=False)
        self.assertEqual(self.publish()["node"], "pr_review")
        self.assertEqual(self.cli("status", "sample")["review_attempts"], 0)
        head = self.cli("snapshot")["head"]
        for _ in range(5):
            self.assertEqual(self.advance("pending", {"summary": "Reviewer queued", "head": head,
                "evidence": "queue.json", "next_action": "Wait for remote-reviewer"})["node"], "pr_review")
        for key, value in [("reviews", []), ("head", "old"), ("inbox_complete", False), ("pending_reviews", ["remote-reviewer"]), ("checks", [])]:
            evidence = self.remote_clean(); evidence[key] = value
            self.advance("clean", evidence, success=False)
        for status in ("pending", "failure"):
            evidence = self.remote_clean(); evidence["checks"][0]["status"] = status
            self.advance("clean", evidence, success=False)
        self.assertEqual(self.advance("clean", self.remote_clean())["node"], "done")

    def test_remote_finding_is_repaired_amended_and_reviewed_on_new_head(self):
        self.reach_review("pull-request")
        self.advance("clean", self.clean()); self.advance("pass", self.checks()); self.publish()
        old = self.remote_clean()
        self.assertEqual(self.advance("fix", {"summary": "Valid remote finding", "head": old["head"],
            "evidence": "remote-review.json", "findings": [{"id": "PR1", "disposition": "actionable", "reason": "M1.T1 invariant broken"}]})["node"], "repair")
        (self.project / "app.py").write_text("value = 2\n")
        count = self.git("rev-list", "--count", "HEAD")
        self.git("add", "app.py"); self.git("commit", "--amend", "--no-edit")
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), count)
        self.advance("complete", {"summary": "M1.T1 commit amended with repair", "artifacts": ["app.py"]})
        self.advance("clean", self.clean(), success=False)
        evidence = self.clean(); evidence["reviews"][0]["findings"] = [{"id": "PR1", "disposition": "resolved", "reason": "Repair and regression checked"}]
        self.advance("clean", evidence); self.advance("pass", self.checks())
        self.assertEqual(self.cli("status", "sample")["review_attempts"], 1)
        self.advance("finish", {"summary": "Local fix done"}, success=False)
        self.advance("next", {"summary": "Skip pending PR", "slice": "M1.T2"}, success=False)
        self.publish(reviewers=["remote-reviewer", "security-bot"], checks=["ci", "lint"])
        self.advance("clean", old, success=False)
        self.advance("clean", self.remote_clean(), success=False)
        evidence = self.remote_clean()
        evidence["reviews"].append({**evidence["reviews"][0], "reviewer": "security-bot"})
        evidence["checks"].append({**evidence["checks"][0], "name": "lint"})
        self.assertEqual(self.advance("clean", evidence)["node"], "done")

    def test_legacy_graph_upgrade_preserves_history_and_budgets(self):
        self.reach_review()
        status = self.cli("status", "sample")
        path = Path(status["state_path"]); state = json.loads(path.read_text())
        for name in ("ready", "pr_review"):
            state["graph"]["nodes"].pop(name)
        state["graph"]["nodes"]["verify"]["edges"]["pass"] = "done"
        state["node"] = "done"; state["repair_rounds"] = 2
        state["findings"] = {"R1": {"id": "R1", "disposition": "resolved", "reason": "Verified"}}
        path.write_text(json.dumps(state))
        result = self.cli("upgrade-delivery", "sample", "--revision", str(state["revision"]), "--evidence", "-",
            evidence={"delivery": "pull-request", "next_action": "Record existing PR and wait for reviews"})
        self.assertEqual(result["node"], "ready")
        self.assertEqual(result["repair_rounds"], 2)
        upgraded = json.loads(path.read_text())
        self.assertEqual(upgraded["history"][:-1], state["history"])
        self.assertEqual(upgraded["history"][-1]["node"], "done")
        self.assertEqual(upgraded["history"][-1]["target"], "ready")
        self.assertEqual(upgraded["findings"], state["findings"])
        self.advance("finish", {"summary": "Cannot skip remote review after migration"}, success=False)

    def test_legacy_upgrade_rejects_changed_custom_routing_without_writes(self):
        status = self.cli("init", "sample")
        path = Path(status["state_path"]); state = json.loads(path.read_text())
        for name in ("ready", "pr_review"):
            state["graph"]["nodes"].pop(name)
        state["graph"]["nodes"]["verify"]["edges"]["pass"] = "done"
        state["graph"]["nodes"]["done"]["edges"]["next"] = "discovery"
        path.write_text(json.dumps(state)); before = path.read_bytes()
        self.cli("upgrade-delivery", "sample", "--revision", "0", "--evidence", "-",
            evidence={"delivery": "pull-request", "next_action": "Migrate"}, success=False)
        self.assertEqual(path.read_bytes(), before)

    def test_repair_limit_escalates_and_replan_does_not_reset_it(self):
        self.reach_review()
        findings = {"summary": "Valid finding", "findings": [{"id": "R1", "disposition": "actionable", "reason": "Invariant broken"}]}
        for _ in range(2):
            self.assertEqual(self.advance("fix", findings)["node"], "repair")
            self.advance("complete", {"summary": "Repair evidence", "artifacts": ["app.py"]})
        self.assertEqual(self.advance("fix", findings)["node"], "escalate")
        result = self.advance("replan", {"summary": "Root cause identified", "decision": "Clarify invariant before repair", "next_action": "Revise plan"})
        self.assertEqual(result["repair_rounds"], 3)

    def test_previous_actionable_finding_cannot_disappear(self):
        self.reach_review()
        self.advance("fix", {"summary": "Valid finding", "findings": [{"id": "R1", "disposition": "actionable", "reason": "Invariant broken"}]})
        self.advance("complete", {"summary": "Repair implemented", "artifacts": ["app.py"]})
        self.advance("clean", self.clean(), success=False)
        evidence = self.clean()
        evidence["reviews"][0]["findings"] = [{"id": "R1", "disposition": "resolved", "reason": "Regression case and repair inspected"}]
        self.assertEqual(self.advance("clean", evidence)["node"], "verify")

    def test_repeated_incomplete_reviews_escalate(self):
        self.reach_review()
        for _ in range(4):
            state = self.advance("incomplete", {"summary": "Reviewer unavailable"})
        self.assertEqual(state["node"], "escalate")

    def test_snapshot_tracks_untracked_staged_mode_and_symlink_changes(self):
        original = workflow.snapshot(self.project)["fingerprint"]
        other = self.project / "new.py"
        other.write_text("new work")
        untracked = workflow.snapshot(self.project)["fingerprint"]
        self.assertNotEqual(original, untracked)
        self.git("add", "new.py")
        self.assertNotEqual(untracked, workflow.snapshot(self.project)["fingerprint"])
        before_mode = workflow.snapshot(self.project)["fingerprint"]
        other.chmod(0o755)
        self.assertNotEqual(before_mode, workflow.snapshot(self.project)["fingerprint"])
        link = self.project / "link"
        link.symlink_to("app.py")
        before_link = workflow.snapshot(self.project)["fingerprint"]
        link.unlink()
        link.symlink_to("scope.md")
        self.assertNotEqual(before_link, workflow.snapshot(self.project)["fingerprint"])

    def test_worktree_identity_and_task_paths_are_guarded(self):
        self.cli("init", "sample")
        self.cli("init", "../escape", success=False)
        self.cli("init", "sample", success=False)
        path = self.project / "other-worktree"
        self.git("worktree", "add", "-b", "other", str(path))
        result = subprocess.run([sys.executable, str(SCRIPT), "--project", str(path), "status", "sample"], capture_output=True)
        self.assertEqual(result.returncode, 1)


class KnowledgeTests(unittest.TestCase):
    def graph(self):
        return {"nodes": [{"id": key, "kind": "slice", "label": key, "status": status, "source": "roadmap.md"} for key, status in [("A", "accepted"), ("B", "accepted"), ("C", "proposed"), ("D", "accepted")]],
                "edges": [{"from": "A", "to": key, "relation": "depends_on", "source": "roadmap.md"} for key in ["B", "C", "D"]]}

    def test_bounded_context_reports_truncation_and_excludes_proposals(self):
        graph = self.graph()
        result = workflow.knowledge_context(graph, "A", 2, 2)
        self.assertTrue(result["truncated"])
        self.assertEqual([n["id"] for n in result["nodes"]], ["A", "B"])
        result = workflow.knowledge_context(graph, "A", 2, 10)
        self.assertEqual({n["id"] for n in result["nodes"]}, {"A", "B", "D"})

    def test_dangling_edges_and_dependency_cycles_are_rejected(self):
        graph = self.graph()
        graph["edges"][0]["to"] = "missing"
        with self.assertRaises(ValueError):
            workflow.knowledge_context(graph, None, 2, 15)
        graph = self.graph()
        graph["edges"].append({"from": "B", "to": "A", "relation": "depends_on", "source": "roadmap.md"})
        with self.assertRaises(ValueError):
            workflow.knowledge_context(graph, None, 2, 15)


if __name__ == "__main__":
    unittest.main()
