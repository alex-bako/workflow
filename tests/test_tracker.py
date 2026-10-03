from contextlib import redirect_stdout
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/agentic-workflow"
SCRIPT = PLUGIN / "scripts/tracker.py"
EVAL = PLUGIN / "evals/tracker"
SPEC = importlib.util.spec_from_file_location("tracker", SCRIPT)
tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tracker)

P = tracker.load_policy(EVAL / "tracker-policy.json")
B = "tracer-bullet"
PLAN_EMPTY = "<!-- aw:plan:start -->\n<!-- aw:plan:end -->"


def item(n, title, status="Ready", labels=("roadmap",), **kw):
    out = {"number": n, "title": title, "state": "OPEN", "status": status, "labels": list(labels), "assignees": [],
           "blocked_by": [], "parent": None, "milestone": None, "body": "", "open_prs": [], "comments": []}
    out.update(kw)
    return out


def bullet(n, title, parent, status="Backlog", **kw):
    return item(n, title, status, (B,), parent=parent, **kw)


def card_body(cid, *texts):
    return "Card.\n\n### Tracer bullets\n\n" + "".join(f"{i}. `{cid}.T{i}` — {t}\n" for i, t in enumerate(texts, 1))


class TrackerCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        shutil.copy(EVAL / "tracker-policy.json", self.dir)
        self.policy_path = self.dir / "tracker-policy.json"
        self.write_order(["S1.3", "S1.1", "S1.2"])
        self.state_path = self.dir / "state.json"
        self.log_path = Path(str(self.state_path) + ".log")
        self.set_state([])

    def write_order(self, ids):
        (self.dir / "ROADMAP.md").write_text("# R\n\n### Next up\n\n" + "".join(f"- {i} — x\n" for i in ids)
                                            + "\n### Later\n\n- S9.9 — later\n")

    def set_state(self, items, **extra):
        self.state_path.write_text(json.dumps({"viewer": "dev", "repo": "acme/shop", "items": items, **extra}))

    def policy(self, **changes):
        p = json.loads(self.policy_path.read_text())
        p.update(changes)
        self.policy_path.write_text(json.dumps(p))

    def run_cli(self, *args, policy=True, cwd=None):
        env = {**os.environ, "AW_TRACKER_GH": str(EVAL / "gh"), "AW_FAKE_GH_STATE": str(self.state_path)}
        argv = [sys.executable, str(SCRIPT)] + (["--policy", str(self.policy_path)] if policy else []) + list(args)
        p = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=cwd or ROOT)
        lines = p.stdout.splitlines()
        self.assertEqual(len(lines), 1, p.stdout + p.stderr)
        out = json.loads(lines[0])
        # Codex shows stdout only: every result repeats its exit code.
        self.assertEqual((out.pop("ok"), out.pop("exit")), (p.returncode == 0, p.returncode), p.stdout)
        return p.returncode, out, p.stderr

    def ok(self, *args):
        code, out, err = self.run_cli(*args)
        self.assertEqual(code, 0, (out, err))
        return out

    def state(self):
        return {i["number"]: i for i in json.loads(self.state_path.read_text())["items"]}

    def log(self):
        return [json.loads(l) for l in self.log_path.read_text().splitlines()] if self.log_path.exists() else []

    def numbers(self, out):
        return [c["number"] for c in out["candidates"]]


class SelectionTests(TrackerCase):
    def test_sample_board_order_and_every_skip_reason(self):
        shutil.copy(EVAL / "state.json", self.state_path)
        shutil.copy(EVAL / "ROADMAP.md", self.dir)
        out = self.ok("next")
        self.assertEqual(self.numbers(out), [4, 6, 11])
        self.assertEqual(out["candidates"][0]["kind"], "bullet")
        self.assertEqual(out["candidates"][0]["card"], 2)
        self.assertEqual(out["skipped"], {"excluded_label": 1, "blocked": 1, "assigned": 1, "open_pr": 1,
                                          "not_startable": 1, "in_progress_without_bullets": 1})
        self.assertEqual(out["in_flight"], [])  # #2 and #10 are cards in progress, not bullets
        self.assertEqual(out["authority"], str((self.dir / "ROADMAP.md").resolve()))
        self.assertEqual(self.log(), [])

    def test_started_card_bullet_before_new_cards_then_policy_order_unlisted_last(self):
        self.set_state([
            item(1, "S7.7 — Unlisted"),
            item(2, "S1.2 — Third"),
            item(3, "S1.3 — First"),
            item(4, "S5.5 — Started, unlisted", "In progress", assignees=["dev"]),
            bullet(5, "S5.5.T1 — Bullet", 4),
            item(6, "S8.8 — Unlisted later"),
        ])
        out = self.ok("next", "--limit", "10")
        self.assertEqual(self.numbers(out), [5, 3, 2, 1, 6])
        self.assertEqual(self.numbers(self.ok("next")), [5, 3, 2])

    def test_each_skip_reason_alone_keeps_the_card_out(self):
        cases = {
            "blocked": dict(blocked_by=[9]),
            "assigned": dict(assignees=["ana"]),
            "open_pr": dict(open_prs=[30]),
            "excluded_label": dict(labels=["roadmap", "epic"]),
            "not_startable": dict(status="Backlog"),
            "in_progress_without_bullets": dict(status="In progress", assignees=["ana"]),
        }
        for reason, kw in cases.items():
            with self.subTest(reason):
                kw = {"status": "Ready", **kw}
                self.set_state([item(1, "S1.3 — Card", **kw), item(9, "Z — unrelated blocker", None, labels=[])])
                out = self.ok("next")
                self.assertEqual(out["candidates"], [])
                self.assertEqual(out["skipped"], {reason: 1})

    def test_closed_blocker_does_not_block_and_backlog_startable_by_policy(self):
        self.set_state([item(1, "S1.3 — Card", "Backlog", blocked_by=[2]), item(2, "S1.1 — Done", "Done", state="CLOSED")])
        self.assertEqual(self.ok("next")["candidates"], [])
        p = json.loads(self.policy_path.read_text())
        p["items"]["startable_states"] = ["ready", "backlog"]
        self.policy_path.write_text(json.dumps(p))
        self.assertEqual(self.numbers(self.ok("next")), [1])

    def test_bullets_run_in_sequence(self):
        base = [item(1, "S1.3 — Card", "In progress", assignees=["dev"]),
                bullet(2, "S1.3.T1 — First", 1), bullet(3, "S1.3.T2 — Second", 1)]
        self.set_state(base)
        self.assertEqual(self.numbers(self.ok("next")), [2])
        taken = copy.deepcopy(base)
        taken[1].update(assignees=["dev"], status="In progress")
        self.set_state(taken)
        out = self.ok("next")
        self.assertEqual(out["candidates"], [])
        self.assertEqual(out["skipped"], {"bullet_taken": 1})
        done = copy.deepcopy(base)
        done[1].update(state="CLOSED", status="Done")
        self.set_state(done)
        self.assertEqual(self.numbers(self.ok("next")), [3])
        done[2].update(state="CLOSED", status="Done")
        self.set_state(done)
        self.assertEqual(self.ok("next")["skipped"], {"bullets_done": 1})

    def test_started_card_of_someone_else_yields_nothing(self):
        self.set_state([item(1, "S1.3 — Card", "In progress", assignees=["ana"]), bullet(2, "S1.3.T1 — First", 1)])
        out = self.ok("next")
        self.assertEqual((out["candidates"], out["skipped"]), ([], {"assigned": 1}))
        p = json.loads(self.policy_path.read_text())
        p["assignee"] = "ana"
        self.policy_path.write_text(json.dumps(p))
        self.assertEqual(self.numbers(self.ok("next")), [2])

    def test_skip_reasons_are_the_stable_names_in_order(self):
        shutil.copy(EVAL / "state.json", self.state_path)
        out = self.ok("next")
        self.assertEqual(list(out["skipped"]), [r for r in tracker.SKIP_REASONS if r in out["skipped"]])
        self.assertLessEqual(set(out["skipped"]), set(tracker.SKIP_REASONS))
        self.assertNotIn(0, out["skipped"].values())

    def test_limit_below_one_is_usage(self):
        for limit in ("0", "-1"):
            self.assertEqual(self.run_cli("next", "--limit", limit)[0], 2)

    def test_in_flight_lists_only_bullets_with_card_branch_and_phase(self):
        self.set_state([item(1, "S1.3 — Card", "In progress", assignees=["dev"]),
                        bullet(2, "S1.3.T1 — First", 1, "In review", assignees=["dev"],
                               comments=["<!-- aw:claim branch=feat/x phase=review -->\nClaimed."]),
                        item(3, "S1.4 — Hand-run card", "In progress", assignees=["ana"])])
        out = self.ok("next")
        self.assertEqual(out["in_flight"], [{"number": 2, "id": "S1.3.T1", "card": 1, "assignees": ["dev"],
                                             "status": "in_review", "branch": "feat/x", "phase": "review"}])
        self.assertEqual(out["skipped"], {"in_progress_without_bullets": 1, "bullet_taken": 1})

    def test_pagination_reads_every_page(self):
        cards = [item(n, f"S2.{n} — Card", assignees=["ana"]) for n in range(1, 151)]
        cards[139]["assignees"] = []
        self.set_state(cards)
        out = self.ok("next")
        self.assertEqual(self.numbers(out), [140])
        self.assertEqual(out["skipped"], {"assigned": 149})

    def test_other_repo_items_and_unlabelled_issues_are_ignored(self):
        self.set_state([item(1, "S1.3 — Card"), item(2, "Chore", labels=[])], repo="acme/other")
        self.assertEqual(self.ok("next")["candidates"], [])


class ShowTests(TrackerCase):
    def test_show_card_with_bullets_blockers_and_prs(self):
        self.set_state([item(1, "S1.3 — Card", blocked_by=[5], open_prs=[40], milestone="Stage 1", body="text"),
                        bullet(2, "S1.3.T1 — One", 1), bullet(3, "S1.3.T2 — Two", 1, status=None),
                        item(5, "S1.1 — Blocker", state="CLOSED", status="Done")])
        out = self.ok("show", "1")
        self.assertEqual((out["kind"], out["status"], out["milestone"], out["pull_requests"]), ("card", "ready", "Stage 1", [40]))
        self.assertEqual(out["blockers"], [{"number": 5, "state": "CLOSED"}])
        self.assertEqual([(b["id"], b["status"]) for b in out["bullets"]], [("S1.3.T1", "backlog"), ("S1.3.T2", None)])
        self.assertNotIn("body", out)
        self.assertEqual(self.ok("show", "1", "--body")["body"], "text")
        self.assertEqual(self.ok("show", "2")["kind"], "bullet")


    def test_show_by_card_id_lists_planned_bullets_before_sub_issues_exist(self):
        self.set_state([item(1, "S1.3 — Card", body=card_body("S1.3", "One.", "Two.")), bullet(2, "S1.3.T1 — One", 1)])
        out = self.ok("show", "S1.3")
        self.assertEqual(out["number"], 1)
        self.assertEqual([(b["id"], b["text"], b["number"]) for b in out["bullets"]],
                         [("S1.3.T1", "One.", 2), ("S1.3.T2", "Two.", None)])
        self.assertEqual(self.run_cli("show", "S7.7")[0], 2)


class WorkOrderTests(TrackerCase):
    def setUp(self):
        super().setUp()
        (self.dir / "ROADMAP.md").write_text(
            "# R\n\n### Next up\n\n- S1.3 — x\n- S1.2 — y\n\n### Later\n\n"
            "#### S1.3 — Search\n\nAcceptance: works.\n\n#### S1.2 — Other\n\nNot startable until decided.\n")

    def board(self, **kw):
        return [item(1, "S1.3 — Search", body=card_body("S1.3", "One.", "Two."), blocked_by=[5], **kw),
                item(5, "S1.1 — Base", state="CLOSED", status="Done"), item(7, "S1.2 — Other")]

    def test_one_read_only_call_carries_the_whole_work_order(self):
        self.set_state(self.board())
        out = self.ok("work-order", "S1.3")
        self.assertEqual((out["kind"], out["item"]["number"], out["claim"]), ("card", 1, {"number": 1, "allowed": True}))
        self.assertEqual((out["bullet"]["id"], out["bullet"]["text"], out["bullet"]["number"]), ("S1.3.T1", "One.", None))
        self.assertEqual(out["siblings_out_of_scope"], ["S1.3.T2 — Two."])
        self.assertEqual((out["authority"]["heading"], out["authority"]["text"]), ("#### S1.3 — Search", "#### S1.3 — Search\n\nAcceptance: works."))
        self.assertEqual(out["dependencies"], [{"number": 5, "state": "CLOSED", "id": "S1.1"}])
        self.assertEqual([(a["number"], a["authority"]["text"].splitlines()[-1]) for a in out["alternates"]],
                         [(7, "Not startable until decided.")])
        self.assertFalse(out["plan_published"])
        self.assertEqual(self.log(), [])

    def test_without_an_authority_file_the_card_body_is_the_authority(self):
        self.set_state(self.board())
        p = json.loads(self.policy_path.read_text())
        del p["authority"]
        self.policy_path.write_text(json.dumps(p))
        body = self.state()[1]["body"]
        self.assertEqual(self.ok("work-order", "S1.3")["authority"], {"issue": tracker.url(P, 1), "text": body})

    def test_open_decisions_in_the_authority_keep_a_card_out_until_settled(self):
        roadmap = self.dir / "ROADMAP.md"
        settled = roadmap.read_text().replace("Acceptance: works.", "Acceptance: works.\nDecisions:\n- D1: hide — user\nOpen decisions: none")
        roadmap.write_text(settled.replace("Open decisions: none", "**Open decisions**:\n\n- Q1 (T2): notify? → rec: no\n- Q2: who may archive?"))
        self.set_state(self.board())
        out = self.ok("next")
        self.assertEqual((self.numbers(out), out["skipped"], out["open_decisions"]), ([7], {"open_decisions": 1}, ["S1.3"]))
        claim = self.ok("work-order", "S1.3")["claim"]
        self.assertEqual((claim["allowed"], claim["reason"]), (False, "open_decisions"))
        self.assertIn("Q2: who may archive?", claim["detail"])
        self.assertIn("Q1 (T2)", claim["detail"])  # not yet split: a tagged item holds the card too
        code, out, _ = self.run_cli("claim", "S1.3")
        self.assertEqual((code, out["reason"], out["writes"]), (3, "open_decisions", []))
        self.assertEqual([c["number"] for c in out["next_candidates"]], [7])
        roadmap.write_text(settled.replace("Open decisions: none", "Open decisions:\n- Q1 (T1): notify? → rec: no"))
        out = self.ok("next")  # not yet split: `next` cannot see the first bullet, so any item holds the card
        self.assertEqual((self.numbers(out), out["open_decisions"]), ([7], ["S1.3"]))
        self.assertEqual(self.run_cli("claim", "S1.3")[1]["reason"], "open_decisions")  # claim agrees
        roadmap.write_text(settled.replace("Open decisions: none", "Open decisions:\n- Q1 (T2): notify? → rec: no"))
        self.set_state([item(1, "S1.3 — Search", "Ready", body=card_body("S1.3", "One.", "Two.")),
                        bullet(2, "S1.3.T1 — One", 1), bullet(3, "S1.3.T2 — Two", 1)])
        self.assertEqual(self.numbers(self.ok("next")), [2])  # split: only T2 is held, so T1 starts
        self.assertEqual(self.ok("claim", "S1.3")["number"], 1)
        self.set_state([item(1, "S1.3 — Search", "In progress", assignees=["dev"]), bullet(2, "S1.3.T1 — One", 1, state="CLOSED"),
                        bullet(3, "S1.3.T2 — Two", 1)])
        self.assertEqual(self.ok("next")["skipped"], {"open_decisions": 1})
        self.assertEqual(self.run_cli("claim", "S1.3.T2")[1]["reason"], "open_decisions")
        roadmap.write_text(settled)
        self.assertEqual(self.ok("claim", "S1.3.T2")["number"], 3)

    def test_open_decisions_field_formats(self):
        od = tracker.open_decisions
        self.assertEqual(od("Open decisions: pick a format\n- not part of it"), ["pick a format"])
        self.assertEqual(od("**Open decisions:**\n\n- Q1: a\n* Q2: b\n\n- Acceptance: other list"), ["Q1: a", "Q2: b"])
        self.assertEqual(od("- Outcome: x\n- Open decisions: none\n- Acceptance: works.\n- Repos: acme/shop"), [])
        self.assertEqual(od("- Open decisions:\n  - Q1: a\n- Acceptance: works."), ["Q1: a"])
        for none in ("none", "(none)", "None.", "n/a", "—"):
            self.assertEqual(od(f"Open decisions: {none}"), [])
        self.assertEqual(od("Decisions:\n- D1: x"), [])
        held = tracker.holding(["Q1 (T2, T3): x", "Q2: y (T9)", "Q3 (S1.3.T4): z"], "S1.3.T3")
        self.assertEqual(held, ["Q1 (T2, T3): x", "Q2: y (T9)"])  # a tag counts only before the first colon
        self.assertEqual(tracker.holding(["Q1 (T2): x"], None), ["Q1 (T2): x"])  # no bullet known: every item holds
        wrapped = "Open decisions:\n- Q1 (T2): a long question\n  that wraps\n- Q2 (T1): b\n\nRisks: none"
        self.assertEqual(od(wrapped), ["Q1 (T2): a long question that wraps", "Q2 (T1): b"])
        self.assertEqual(od("- Open decisions:\n  - Q1: a\n    wrapped\n  - Q2: b\n- Acceptance: x"), ["Q1: a wrapped", "Q2: b"])

    def test_claim_refuses_when_the_authority_file_cannot_be_read(self):
        self.set_state(self.board())
        (self.dir / "ROADMAP.md").unlink()
        code, out, _ = self.run_cli("claim", "S1.3")
        self.assertEqual((code, out["reason"], out["writes"]), (3, "open_decisions", []))

    def test_open_decisions_past_the_section_cap_still_hold_the_card(self):
        roadmap = self.dir / "ROADMAP.md"
        filler = "".join(f"- line {i}\n" for i in range(tracker.SECTION_CAP + 5))
        roadmap.write_text(roadmap.read_text().replace("Acceptance: works.", f"Acceptance: works.\n{filler}\nOpen decisions:\n- Q9: late?"))
        self.set_state(self.board())
        self.assertEqual(self.ok("next")["open_decisions"], ["S1.3"])
        self.assertEqual(self.run_cli("claim", "S1.3")[1]["reason"], "open_decisions")

    def test_without_an_authority_file_claim_reads_open_decisions_from_the_card_body(self):
        self.set_state([item(1, "S1.3 — Search", body=card_body("S1.3", "One.") + "\nOpen decisions:\n- Q1: format?\n")])
        p = json.loads(self.policy_path.read_text())
        del p["authority"]
        self.policy_path.write_text(json.dumps(p))
        code, out, _ = self.run_cli("claim", "1")
        self.assertEqual((out["reason"], out["next_candidates"]), ("open_decisions", []))  # never offered again

    def test_taken_item_reports_the_refusal_claim_would_give(self):
        self.set_state(self.board(status="In progress", assignees=["sam"]))
        self.assertEqual(self.ok("work-order", "1")["claim"]["reason"], "taken")
        self.set_state([item(1, "S1.3 — Search", "In progress", assignees=["dev"]),
                        bullet(2, "S1.3.T1 — One", 1), bullet(3, "S1.3.T2 — Two", 1)])
        self.assertEqual(self.ok("work-order", "3")["claim"]["reason"], "blocked")
        claim = self.ok("work-order", "S1.3")["claim"]  # a started card: claim its current bullet
        self.assertEqual((claim["number"], claim["allowed"]), (2, True))
        self.assertEqual(self.ok("claim", "S1.3.T1")["number"], 2)

    def test_refused_claim_offers_next_candidates_with_their_authority(self):
        self.set_state(self.board(status="In progress", assignees=["sam"]))
        code, out, _ = self.run_cli("claim", "1")
        self.assertEqual((code, out["reason"], out["writes"]), (3, "taken", []))
        self.assertEqual([(c["number"], c["authority"]["heading"]) for c in out["next_candidates"]], [(7, "#### S1.2 — Other")])
        self.assertEqual(self.log(), [])


class BulletTests(TrackerCase):
    long = ("Failing search spec: every query returns matching products ranked by title match and then by recency, "
            "with no duplicates. The spec fails on main.")

    def card(self, **kw):
        return item(1, "S1.3 — Search", milestone="Stage 1", body=card_body("S1.3", self.long, "Wire the box. Then results."), **kw)

    def test_creates_sub_issues_in_body_order_and_is_idempotent(self):
        self.set_state([self.card()])
        out = self.ok("bullets", "1")
        made = self.state()
        self.assertEqual([b["number"] for b in out["bullets"]], [2, 3])
        first, second = made[2], made[3]
        self.assertEqual(second["title"], "S1.3.T2 — Wire the box")
        self.assertTrue(first["title"].startswith("S1.3.T1 — Failing search spec"))
        self.assertLessEqual(len(first["title"].split(" — ", 1)[1]), 90)
        for b in (first, second):
            self.assertEqual((b["parent"], b["labels"], b["milestone"], b["status"], b.get("type")), (1, [B], "Stage 1", "Backlog", "Task"))
            self.assertIn("Card: #1", b["body"])
            self.assertIn(PLAN_EMPTY, b["body"])
        self.assertIn(self.long, first["body"])
        writes = len(self.log())
        again = self.ok("bullets", "1")
        self.assertEqual(again["writes"], [])
        self.assertEqual([b["created"] for b in again["bullets"]], [False, False])
        self.assertEqual(len(self.log()), writes)

    def test_creates_only_missing_and_boards_an_existing_bullet(self):
        self.set_state([self.card(), bullet(7, "S1.3.T1 — Existing", 1, status=None)])
        out = self.ok("bullets", "1")
        self.assertEqual([(b["number"], b["created"]) for b in out["bullets"]], [(7, False), (8, True)])
        self.assertEqual(self.state()[7]["status"], "Backlog")
        self.assertEqual([e["op"] for e in self.log()], ["AwAddItem", "AwSetStatus", "AwCreateIssue", "AwAddItem", "AwSetStatus"])

    def test_rerun_finishes_an_add_whose_status_write_failed(self):
        self.set_state([self.card()], fail=["AwSetStatus"])
        self.assertEqual(self.run_cli("bullets", "1")[0], 4)
        self.assertEqual(self.state()[2]["status"] or None, None)
        state = json.loads(self.state_path.read_text())
        state["fail"] = []
        self.state_path.write_text(json.dumps(state))
        self.ok("bullets", "1")
        self.assertEqual({n: i["status"] for n, i in self.state().items() if n != 1}, {2: "Backlog", 3: "Backlog"})

    def test_issue_type_omitted_when_repository_lacks_it(self):
        p = json.loads(self.policy_path.read_text())
        p["bullets"]["issue_type"] = "Story"
        self.policy_path.write_text(json.dumps(p))
        self.set_state([self.card()])
        self.ok("bullets", "1")
        self.assertNotIn("issueTypeId", self.log()[0]["variables"]["input"])

    def test_taken_or_blocked_card_is_refused_before_any_write(self):
        cases = [("taken", dict(status="In progress", assignees=["sam"])), ("taken", dict(assignees=["sam"])),
                 ("taken", dict(status="In review")), ("blocked", dict(blocked_by=[9]))]
        for reason, kw in cases:
            with self.subTest(reason=reason, **{k: str(v) for k, v in kw.items()}):
                self.set_state([self.card(**kw), item(9, "Z — blocker", None, labels=[])])
                code, out, _ = self.run_cli("bullets", "1")
                self.assertEqual((code, out["reason"], out["writes"]), (3, reason, []))
                self.assertEqual(self.log(), [])
        self.set_state([self.card(status="In progress", assignees=["dev"])])
        self.assertEqual(len(self.ok("bullets", "1")["bullets"]), 2)

    def test_sample_card_assigned_to_someone_else_gets_no_bullets(self):
        shutil.copy(EVAL / "state.json", self.state_path)
        board = json.loads(self.state_path.read_text())
        six = next(i for i in board["items"] if i["number"] == 6)
        six.update(assignees=["sam"], status="In progress")
        self.state_path.write_text(json.dumps(board))
        code, out, _ = self.run_cli("bullets", "6")
        self.assertEqual((code, out["reason"], out["writes"]), (3, "taken", []))
        self.assertEqual(self.log(), [])

    def test_bullet_order_is_by_id_not_issue_number(self):
        self.set_state([item(1, "S1.3 — Search", "In progress", assignees=["dev"], body=card_body("S1.3", "One.", "Two.")),
                        bullet(2, "S1.3.T2 — Two", 1)])
        made = self.ok("bullets", "1")["bullets"]
        self.assertEqual([(b["number"], b["id"], b["created"]) for b in made], [(3, "S1.3.T1", True), (2, "S1.3.T2", False)])
        self.assertEqual(self.numbers(self.ok("next")), [3])
        self.assertEqual([b["id"] for b in self.ok("show", "1")["bullets"]], ["S1.3.T1", "S1.3.T2"])
        code, out, _ = self.run_cli("claim", "2")
        self.assertEqual((code, out["reason"]), (3, "blocked"))
        self.assertEqual(self.ok("claim", "3")["number"], 3)

    def test_natural_id_order(self):
        subs = [{"id": i, "number": n} for i, n in (("A1.T10", 1), ("A1.T2", 2), ("A1.T1", 4), ("A1.T1", 3))]
        self.assertEqual([(s["id"], s["number"]) for s in sorted(subs, key=tracker.bullet_key)],
                         [("A1.T1", 3), ("A1.T1", 4), ("A1.T2", 2), ("A1.T10", 1)])

    def test_refusals_write_nothing(self):
        self.set_state([item(1, "S1.3 — No bullets", body="Nothing listed."), item(2, "S1 — Epic", labels=["roadmap", "epic"],
                        body=card_body("S1", "x")), bullet(3, "S1.3.T1 — b", 1)])
        for n, reason in (("1", "no_bullets"), ("2", "not_a_card"), ("3", "not_a_card")):
            code, out, _ = self.run_cli("bullets", n)
            self.assertEqual((code, out["reason"], out["writes"]), (3, reason, []))
        self.assertEqual(self.log(), [])


class ClaimTests(TrackerCase):
    def board(self):
        return [item(1, "S1.3 — Card", "In progress", assignees=["dev"]),
                bullet(2, "S1.3.T1 — First", 1, state="CLOSED", status="Done"),
                bullet(3, "S1.3.T2 — Second", 1), bullet(4, "S1.3.T3 — Third", 1)]

    def test_claim_bullet_assigns_sets_card_and_bullet_in_progress_and_comments(self):
        b = self.board()
        b[0].update(status="Ready", assignees=[])
        self.set_state(b)
        out = self.ok("claim", "3", "--branch", "feat/s1.3-search", "--phase", "plan")
        s = self.state()
        self.assertEqual((s[3]["assignees"], s[3]["status"], s[1]["status"]), (["dev"], "In progress", "In progress"))
        self.assertEqual(len(s[3]["comments"]), 1)
        self.assertIn("<!-- aw:claim branch=feat/s1.3-search phase=plan -->", s[3]["comments"][0])
        self.assertEqual(out["writes"], ["assign #3 dev", "status #3 In progress", "status #1 In progress", "comment #3 claim"])
        self.assertEqual(s[1]["comments"], [])
        writes = len(self.log())
        self.assertEqual(self.ok("claim", "3", "--branch", "feat/s1.3-search", "--phase", "plan")["writes"], [])
        self.assertEqual(len(self.log()), writes)
        flight = {f["number"]: (f["card"], f["branch"], f["phase"]) for f in self.ok("next")["in_flight"]}
        self.assertEqual(flight, {3: (1, "feat/s1.3-search", "plan")})

    def test_branch_or_phase_that_breaks_the_marker_is_usage(self):
        self.set_state(self.board())
        for flag, value in (("--branch", "feat/a b"), ("--phase", "plan now"), ("--branch", "x-->"), ("--phase", "a>b"),
                            ("--branch", "")):
            with self.subTest(flag=flag, value=value):
                self.assertEqual(self.run_cli("claim", "3", flag, value)[0], 2)
        self.assertEqual(self.log(), [])

    def test_claim_new_card_puts_it_on_the_board_when_missing(self):
        self.set_state([item(1, "S1.3 — Card", None)])
        out = self.ok("claim", "1")
        self.assertEqual(out["writes"], ["assign #1 dev", "add #1 to board", "status #1 In progress", "comment #1 claim"])
        self.assertEqual(self.state()[1]["status"], "In progress")

    def test_refusals_write_nothing(self):
        cases = [
            ("taken", lambda b: b[2].update(assignees=["ana"])),
            ("taken", lambda b: b[2].update(status="In review", assignees=["dev"])),
            ("taken", lambda b: b[2].update(status="In progress")),
            ("taken", lambda b: b[2].update(state="CLOSED")),
            ("blocked", lambda b: b[2].update(blocked_by=[9])),
            ("blocked", lambda b: b[1].update(state="OPEN", status="Backlog")),
            ("not_a_card", lambda b: b[2].update(labels=["docs"])),
        ]
        for reason, change in cases:
            with self.subTest(reason):
                b = self.board() + [item(9, "Z — blocker", None, labels=[])]
                change(b)
                self.set_state(b)
                before = self.state_path.read_text()
                code, out, _ = self.run_cli("claim", "3")
                self.assertEqual((code, out["reason"], out["writes"]), (3, reason, []))
                self.assertEqual(self.state_path.read_text(), before)
                self.assertEqual(self.log(), [])

    def test_bullet_of_a_taken_closed_or_excluded_card_is_refused_before_any_write(self):
        cases = [("taken", dict(assignees=["ana"])), ("taken", dict(state="CLOSED")),
                 ("not_a_card", dict(labels=["roadmap", "epic"]))]
        for reason, change in cases:
            with self.subTest(**{k: str(v) for k, v in change.items()}):
                b = self.board()
                b[0].update(change)
                self.set_state(b)
                before = self.state_path.read_text()
                code, out, _ = self.run_cli("claim", "3")
                self.assertEqual((code, out["reason"], out["writes"]), (3, reason, []))
                self.assertEqual(self.state_path.read_text(), before)
                self.assertEqual(self.log(), [])

    def test_later_bullet_blocked_while_earlier_open(self):
        self.set_state(self.board())
        code, out, _ = self.run_cli("claim", "4")
        self.assertEqual((code, out["reason"]), (3, "blocked"))
        self.assertIn("[3]", out["detail"])

    def test_excluded_card_is_not_handed_out(self):
        self.set_state([item(1, "S1 — Epic", labels=["roadmap", "epic"])])
        self.assertEqual(self.run_cli("claim", "1")[1]["reason"], "not_a_card")


class PlanTests(TrackerCase):
    def plan_file(self, text):
        path = self.dir / "plan.md"
        path.write_text(text)
        return str(path)

    def test_replaces_section_and_repeat_is_a_noop(self):
        self.set_state([bullet(1, "S1.3.T1 — b", None, body=f"Intro.\n\n{PLAN_EMPTY}\n\nTail.\n")])
        f = self.plan_file("## Plan\n\nStep one.\n")
        out = self.ok("plan", "1", "--file", f)
        self.assertEqual(out["writes"], ["plan #1"])
        self.assertEqual(self.state()[1]["body"],
                         "Intro.\n\n<!-- aw:plan:start -->\n## Plan\n\nStep one.\n<!-- aw:plan:end -->\n\nTail.\n")
        self.assertEqual(self.ok("plan", "1", "--file", f)["writes"], [])
        self.ok("plan", "1", "--file", self.plan_file("v2"))
        self.assertEqual(self.state()[1]["body"].count("aw:plan:start"), 1)
        self.assertIn("\nv2\n", self.state()[1]["body"])

    def test_appends_section_when_absent(self):
        self.set_state([bullet(1, "S1.3.T1 — b", None, body="Intro.")])
        self.ok("plan", "1", "--file", self.plan_file("Plan."))
        self.assertEqual(self.state()[1]["body"], "Intro.\n\n<!-- aw:plan:start -->\nPlan.\n<!-- aw:plan:end -->\n")

    def test_plan_containing_a_marker_is_usage_and_writes_nothing(self):
        self.set_state([bullet(1, "S1.3.T1 — b", None, body="Intro.")])
        for marker in (tracker.PLAN_START, tracker.PLAN_END):
            with self.subTest(marker):
                self.assertEqual(self.run_cli("plan", "1", "--file", self.plan_file(f"a\n{marker}\nb"))[0], 2)
        self.assertEqual(self.state()[1]["body"], "Intro.")
        self.assertEqual(self.log(), [])

    def test_too_large_writes_nothing_and_missing_file_is_usage(self):
        self.set_state([bullet(1, "S1.3.T1 — b", None, body="Intro.")])
        code, out, _ = self.run_cli("plan", "1", "--file", self.plan_file("x" * 65000))
        self.assertEqual((code, out["reason"]), (3, "too_large"))
        code, out, _ = self.run_cli("plan", "1", "--file", str(self.dir / "missing.md"))
        self.assertEqual(code, 2)
        self.assertEqual(self.log(), [])


class SetTests(TrackerCase):
    def test_set_status_and_comment_then_repeat_is_noop_and_never_closes(self):
        self.set_state([item(1, "S1.3 — Card", "In progress", assignees=["dev"])])
        out = self.ok("set", "1", "in_review", "--comment", "Pull request #40 opened.")
        self.assertEqual(out["writes"], ["status #1 In review", "comment #1"])
        self.assertEqual(self.ok("set", "1", "in_review", "--comment", "Pull request #40 opened.")["writes"], [])
        self.ok("set", "1", "done")
        s = self.state()[1]
        self.assertEqual((s["status"], s["state"], s["comments"]), ("Done", "OPEN", ["Pull request #40 opened."]))
        self.assertEqual({e["op"] for e in self.log()}, {"AwSetStatus", "AwComment"})

    def test_unknown_state_is_usage_error(self):
        self.set_state([item(1, "S1.3 — Card")])
        self.assertEqual(self.run_cli("set", "1", "In review")[0], 2)
        self.assertEqual(self.log(), [])


class ColumnTests(TrackerCase):
    def test_missing_column_is_usage_before_any_write(self):
        cases = [("in_progress", "Doing", "claim", [item(1, "S1.3 — Card")]),
                 ("backlog", "Todo", "bullets", [item(1, "S1.3 — Card", body=card_body("S1.3", "One.", "Two."))]),
                 ("in_review", "Reviewing", "set", [item(1, "S1.3 — Card", None)])]
        good = json.loads(self.policy_path.read_text())
        for key, column, cmd, items in cases:
            with self.subTest(cmd):
                p = copy.deepcopy(good)
                p["states"][key] = column
                self.policy_path.write_text(json.dumps(p))
                self.set_state(items)
                code, out, _ = self.run_cli(cmd, "1", *(["in_review"] if cmd == "set" else []))
                self.assertEqual((code, out["error"]), (2, "usage"))
                self.assertIn(column, out["message"])
                self.assertEqual(self.log(), [])

    def test_misnamed_status_field_is_usage(self):
        self.set_state([item(1, "S1.3 — Card")])
        p = json.loads(self.policy_path.read_text())
        p["project"]["status_field"] = "Statuss"
        self.policy_path.write_text(json.dumps(p))
        for args in (("next",), ("audit",), ("show", "1"), ("claim", "1")):
            with self.subTest(args):
                code, out, _ = self.run_cli(*args)
                self.assertEqual((code, out["error"]), (2, "usage"))
                self.assertIn("Statuss", out["message"])
        self.assertEqual(self.log(), [])

    def test_error_after_writes_reports_them(self):
        def late(t, args):
            t.writes.append("status #1 Ready")
            raise tracker.Usage("late")
        out = io.StringIO()
        with mock.patch.object(tracker, "cmd_audit", late), mock.patch.object(tracker, "load_policy", lambda _: P), \
                redirect_stdout(out):
            self.assertEqual(tracker.main(["audit"]), 2)
        self.assertEqual(json.loads(out.getvalue())["writes"], ["status #1 Ready"])


class AuditTests(TrackerCase):
    def test_each_drift_code(self):
        self.set_state([
            item(1, "S1.1 — Closed not done", "In review", state="CLOSED", assignees=["dev"]),
            item(2, "S1.2 — Done but open", "Done", assignees=["dev"]),
            item(3, "S1.3 — Startable but blocked", "Ready", blocked_by=[2]),
            item(4, "S1.4 — Unassigned", "In progress"),
            item(5, "S1.5 — Closed card", "Done", state="CLOSED"),
            bullet(6, "S1.5.T1 — Open bullet", 5),
            item(7, "S1.7 — Card", "In progress", assignees=["dev"]),
            bullet(8, "S1.7.T1 — Off board", 7, status=None),
            item(9, "S1 — Epic in progress", "In progress", labels=["roadmap", "epic"]),
            item(10, "S1.10 — Healthy", "Ready"),
        ])
        out = self.ok("audit")
        self.assertEqual(sorted((d["code"], d["number"]) for d in out["drift"]), sorted([
            ("closed_not_done", 1), ("done_but_open", 2), ("startable_but_blocked", 3), ("in_progress_unassigned", 4),
            ("bullet_open_card_closed", 6), ("not_on_board", 8)]))
        self.assertEqual(out["count"], 6)
        self.assertEqual(self.log(), [])

    def test_blocked_backlog_is_not_drift_even_when_backlog_is_startable(self):
        p = json.loads(self.policy_path.read_text())
        p["items"]["startable_states"] = ["ready", "backlog"]
        self.policy_path.write_text(json.dumps(p))
        self.set_state([item(1, "S1.1 — Backlog blocked", "Backlog", blocked_by=[3]),
                        item(2, "S1.2 — Ready blocked", "Ready", blocked_by=[3]), item(3, "S1.3 — Blocker", "Backlog")])
        self.assertEqual([(d["code"], d["number"]) for d in self.ok("audit")["drift"]], [("startable_but_blocked", 2)])


class FailureTests(TrackerCase):
    def test_failed_write_exits_4_reports_applied_writes_and_does_not_retry(self):
        self.set_state([item(1, "S1.3 — Card")], fail=["AwComment"])
        code, out, err = self.run_cli("claim", "1")
        self.assertEqual(code, 4)
        self.assertIn("Resource not accessible by personal access token", err)
        self.assertIn("Resource not accessible", out.pop("message"))
        self.assertEqual(out, {"error": "gh_failed", "operation": "AwComment", "failed_write": "comment #1 claim",
                               "writes": ["assign #1 dev", "status #1 In progress"]})
        self.assertEqual([(e["op"], e["ok"]) for e in self.log()], [("AwAssign", True), ("AwSetStatus", True), ("AwComment", False)])

    def test_failed_read_exits_4_without_writes(self):
        self.set_state([item(1, "S1.3 — Card")], fail=["AwItems"])
        code, out, err = self.run_cli("next")
        self.assertEqual((code, out["operation"]), (4, "AwItems"))
        self.assertIn("Resource not accessible", err)
        self.set_state([item(1, "S1.3 — Card")], fail=["AwIssue"])
        self.assertEqual(self.run_cli("claim", "1")[0], 4)
        self.assertEqual(self.log(), [])


class PolicyTests(TrackerCase):
    def test_missing_and_invalid_policy_exit_2(self):
        self.set_state([item(1, "S1.3 — Card")])
        good = self.policy_path.read_text()
        p = json.loads(good)
        variants = {
            "missing": None,
            "not json": "{",
            "missing state": {**p, "states": {k: v for k, v in p["states"].items() if k != "blocked"}},
            "pattern groups": {**p, "bullets": {**p["bullets"], "pattern": "^(.+)$"}},
            "bad repo": {**p, "repo": "acme"},
            "bad startable": {**p, "items": {**p["items"], "startable_states": ["soon"]}},
            "order start absent": {**p, "order": {**p["order"], "start": "### Nowhere"}},
            "order file absent": {**p, "order": {**p["order"], "file": "nope.md"}},
        }
        for name, content in variants.items():
            with self.subTest(name):
                if content is None:
                    self.policy_path.unlink()
                else:
                    self.policy_path.write_text(content if isinstance(content, str) else json.dumps(content))
                code, out, _ = self.run_cli("next")
                self.assertEqual((code, out["error"]), (2, "usage"))
                self.policy_path.write_text(good)
        self.assertEqual(self.log(), [])

    def test_default_policy_path_and_relative_order_resolution(self):
        self.set_state([item(1, "S7.7 — Unlisted"), item(2, "S1.2 — Listed")])
        code, out, _ = self.run_cli("next", policy=False, cwd=self.dir)
        self.assertEqual((code, self.numbers(out)), (0, [2, 1]))
        code, out, _ = self.run_cli("next", policy=False, cwd=ROOT)
        self.assertEqual(code, 2)

    def test_bad_arguments_are_usage_errors(self):
        self.assertEqual(self.run_cli("claim")[0], 2)
        self.assertEqual(self.run_cli("frobnicate")[0], 2)


def found(n, title, prio="soon", status="Ready", **kw):
    return item(n, title, status, ("found",) + ((f"priority:{prio}",) if prio else ()), **kw)


LABELS = ["roadmap", "epic", B, "found", "priority:urgent", "priority:soon", "priority:later"]


class FoundSelectionTests(TrackerCase):
    def test_order_urgent_bullet_soon_card_later_oldest_first(self):
        self.set_state([
            item(1, "S1.3 — New card"),
            item(2, "S5.5 — Started", "In progress", assignees=["dev"]), bullet(3, "S5.5.T1 — Bullet", 2),
            found(10, "Later two", "later"), found(4, "Soon one"), found(6, "Urgent two", "urgent"),
            found(5, "Urgent one", "urgent"), found(7, "Soon two"), found(8, "Later one", "later"),
        ])
        out = self.ok("next", "--limit", "10")
        self.assertEqual(self.numbers(out), [5, 6, 3, 4, 7, 1, 8, 10])
        self.assertEqual([c["kind"] for c in out["candidates"]],
                         ["found", "found", "bullet", "found", "found", "card", "found", "found"])
        self.assertEqual(out["candidates"][0], {"number": 5, "id": "Urgent one", "title": "Urgent one", "kind": "found",
                                                "card": None, "url": "https://github.com/acme/shop/issues/5",
                                                "priority": "urgent"})
        self.assertNotIn("priority", out["candidates"][2])

    def test_untriaged_is_skipped_and_reported_as_drift(self):
        self.set_state([found(1, "No rank", None), item(2, "Two ranks", labels=["found", "priority:soon", "priority:later"]),
                        found(3, "Ranked")])
        out = self.ok("next")
        self.assertEqual((self.numbers(out), out["skipped"]), ([3], {"untriaged": 2}))
        self.assertEqual([(d["code"], d["number"]) for d in self.ok("audit")["drift"]],
                         [("found_untriaged", 1), ("found_untriaged", 2)])

    def test_taken_or_unstartable_found_issue_is_not_a_candidate(self):
        cases = {"assigned": dict(assignees=["ana"]), "blocked": dict(blocked_by=[9]), "open_pr": dict(open_prs=[30]),
                 "not_startable": dict(status="Backlog")}
        for reason, kw in cases.items():
            with self.subTest(reason):
                self.set_state([found(1, "Flaky test", "urgent", **kw), item(9, "Z — blocker", None, labels=[])])
                out = self.ok("next")
                self.assertEqual((out["candidates"], out["skipped"]), ([], {reason: 1}))

    def test_claimed_found_issue_is_in_flight(self):
        self.set_state([found(1, "Flaky test", "urgent")])
        self.assertEqual(self.ok("claim", "1", "--branch", "fix/flaky")["kind"], "found")
        out = self.ok("next")
        self.assertEqual(out["in_flight"], [{"number": 1, "id": "Flaky test", "card": None, "assignees": ["dev"],
                                             "status": "in_progress", "branch": "fix/flaky", "phase": None}])
        self.assertEqual(out["skipped"], {"not_startable": 1})

    def test_bullet_blocked_by_found_work_stays_in_flight_until_resumed(self):
        self.set_state([item(1, "S1.3 — Card", "In progress", assignees=["dev"]),
                        bullet(2, "S1.3.T1 — First", 1, "Ready"), bullet(3, "S1.3.T2 — Second", 1)], labels=LABELS)
        self.ok("claim", "2", "--branch", "feat/s1.3", "--phase", "review")
        self.ok("set", "2", "blocked", "--comment", "Blocked by found issue #4.")
        (self.dir / "b.md").write_text("Evidence.")
        self.assertEqual(self.ok("file", "--title", "Webhook test flaky", "--body-file", str(self.dir / "b.md"),
                                 "--priority", "urgent", "--found-in", "2")["number"], 4)
        blocked = {"number": 2, "id": "S1.3.T1", "card": 1, "assignees": ["dev"], "status": "blocked",
                   "branch": "feat/s1.3", "phase": "review"}
        out = self.ok("next")
        self.assertEqual((self.numbers(out), out["in_flight"]), ([4], [blocked]))
        state = json.loads(self.state_path.read_text())
        next(i for i in state["items"] if i["number"] == 4).update(state="CLOSED", status="Done")
        self.state_path.write_text(json.dumps(state))
        out = self.ok("next")  # the found issue is done: the blocked bullet is still there to resume
        self.assertEqual((out["candidates"], out["in_flight"]), ([], [blocked]))
        self.ok("set", "2", "in_progress", "--comment", "Resumed: #4 closed.")
        self.assertEqual(self.ok("next")["in_flight"][0]["status"], "in_progress")

    def test_found_issue_off_the_board_is_drift(self):
        self.set_state([found(1, "Flaky search test", None, status=None), item(2, "S1.3 — Card"),
                        found(3, "Slow export", "soon", status=None), found(4, "Closed", None, status=None, state="CLOSED"),
                        item(5, "Chore", None, labels=[])], labels=LABELS)
        self.assertEqual([(d["code"], d["number"]) for d in self.ok("audit")["drift"]],
                         [("found_untriaged", 1), ("not_on_board", 3)])

    def test_without_found_policy_nothing_changes_and_file_rank_are_usage(self):
        p = json.loads(self.policy_path.read_text())
        del p["found"]
        self.policy_path.write_text(json.dumps(p))
        self.set_state([found(1, "Flaky test", None), item(2, "S1.3 — Card")])
        out = self.ok("next")
        self.assertEqual((self.numbers(out), out["skipped"]), ([2], {}))
        self.assertEqual(self.ok("audit")["drift"], [])
        self.assertEqual(self.ok("show", "1")["kind"], "other")
        (self.dir / "b.md").write_text("x")
        for args in (("file", "--title", "T", "--body-file", str(self.dir / "b.md"), "--priority", "soon"),
                     ("rank", "1", "soon")):
            with self.subTest(args[0]):
                code, out, _ = self.run_cli(*args)
                self.assertEqual((code, out["error"]), (2, "usage"))
                self.assertIn("found", out["message"])
        self.assertEqual(self.log(), [])


class FileTests(TrackerCase):
    def body(self, text="## Summary\nThe checkout test fails 3 of 20 runs.\n"):
        path = self.dir / "body.md"
        path.write_text(text)
        return str(path)

    def file(self, *extra, title="Checkout test flaky on CI", prio="urgent"):
        return self.run_cli("file", "--title", title, "--body-file", self.body(), "--priority", prio, *extra)

    def test_creates_found_issue_on_the_board_and_repeat_writes_nothing(self):
        self.set_state([item(1, "S1.3 — Card")], labels=LABELS)
        code, out, _ = self.file("--found-in", "1")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, {"number": 2, "title": "Checkout test flaky on CI", "kind": "found", "priority": "urgent",
                               "created": True, "url": "https://github.com/acme/shop/issues/2",
                               "writes": ["create found issue", "add #2 to board", "status #2 Ready"]})
        s = self.state()[2]
        self.assertEqual((s["labels"], s["type"], s["status"], s["parent"]), (["found", "priority:urgent"], "Bug", "Ready", None))
        self.assertEqual(s["body"], "## Summary\nThe checkout test fails 3 of 20 runs.\n\nFound in #1\n")
        writes = len(self.log())
        code, again, _ = self.file("--found-in", "1", "--new")
        self.assertEqual((code, again["created"], again["number"], again["writes"]), (0, False, 2, []))
        self.assertEqual(len(self.log()), writes)
        self.assertEqual(self.numbers(self.ok("next")), [2, 1])
        self.assertEqual(self.ok("show", "2")["kind"], "found")

    def test_found_in_line_not_repeated_and_type_override_or_omitted(self):
        self.set_state([], labels=LABELS)
        self.run_cli("file", "--title", "A", "--body-file", self.body("Found in #4\n"), "--priority", "later",
                     "--found-in", "4", "--type", "Feature")
        self.run_cli("file", "--title", "Unrelated words entirely", "--body-file", self.body(""), "--priority", "later",
                     "--found-in", "4", "--type", "Story")
        s = self.state()
        self.assertEqual((s[1]["body"], s[1]["type"]), ("Found in #4\n", "Feature"))
        self.assertEqual((s[2]["body"], s[2].get("type")), ("Found in #4\n", None))

    def test_similar_open_title_is_refused_unless_new(self):
        self.set_state([item(1, "S1.4 — Checkout: flaky test on CI!"), found(2, "Login page broken", state="CLOSED"),
                        found(3, "Search slow")], labels=LABELS)
        code, out, _ = self.file()
        self.assertEqual((code, out["reason"], out["writes"]), (3, "similar", []))
        self.assertEqual(out["matches"], [{"number": 1, "title": "S1.4 — Checkout: flaky test on CI!",
                                           "url": "https://github.com/acme/shop/issues/1"}])
        self.assertEqual(self.log(), [])
        code, out, _ = self.file("--new")
        self.assertEqual((code, out["created"]), (0, True))
        code, out, _ = self.file(title="Login page broken")  # the similar issue is closed
        self.assertEqual((code, out["created"]), (0, True))

    def test_same_title_with_new_evidence_is_similar_not_a_repeat(self):
        for prio in ("later", None):  # filed by the steward earlier, or by a person without a rank
            with self.subTest(prio=prio):
                self.set_state([found(1, "Checkout test flaky on CI", prio, body="seen once")], labels=LABELS)
                code, out, _ = self.file()
                self.assertEqual((code, out["reason"], [m["number"] for m in out["matches"]], out["writes"]),
                                 (3, "similar", [1], []))
                self.assertEqual(self.log(), [])
                self.assertEqual(self.state()[1]["body"], "seen once")
        code, out, _ = self.file("--new")  # a different problem under the same title is still filed
        self.assertEqual((code, out["created"], out["number"]), (0, True, 2))
        self.set_state([item(1, "Fix it", labels=[])], labels=LABELS)  # identical title without long words
        self.assertEqual(self.run_cli("file", "--title", "fix it", "--body-file", self.body(), "--priority", "soon")[1]["reason"],
                         "similar")

    def test_missing_found_or_priority_label_is_usage_before_any_write(self):
        for missing in ("found", "priority:later"):
            with self.subTest(missing):
                self.set_state([], labels=[l for l in LABELS if l != missing])
                code, out, _ = self.file(prio="soon")
                self.assertEqual((code, out["error"]), (2, "usage"))
                self.assertIn(repr(missing), out["message"])
                self.assertEqual(self.log(), [])

    def test_partial_failure_lists_applied_writes_and_repeat_completes(self):
        self.set_state([], labels=LABELS, fail=["AwSetStatus"])
        code, out, _ = self.file()
        self.assertIn("Resource not accessible", out.pop("message"))
        self.assertEqual(out, {"error": "gh_failed", "operation": "AwSetStatus", "failed_write": "status #1 Ready",
                               "writes": ["create found issue", "add #1 to board"]})
        self.assertEqual(code, 4)
        state = json.loads(self.state_path.read_text())
        state["fail"] = []
        self.state_path.write_text(json.dumps(state))
        code, out, _ = self.file()
        self.assertEqual((code, out["created"], out["writes"]), (0, False, ["status #1 Ready"]))
        self.assertEqual(len(self.state()), 1)


class RankTests(TrackerCase):
    def test_rank_replaces_priority_and_moves_backlog_to_ready_then_repeat_is_noop(self):
        self.set_state([found(1, "Flaky test", "later", "Backlog")], labels=LABELS)
        out = self.ok("rank", "1", "urgent")
        self.assertEqual(out, {"number": 1, "title": "Flaky test", "priority": "urgent", "status": "ready",
                               "url": "https://github.com/acme/shop/issues/1",
                               "writes": ["label #1 priority:urgent", "unlabel #1 priority:later", "status #1 Ready"]})
        self.assertEqual(self.state()[1]["labels"], ["found", "priority:urgent"])
        self.assertEqual(self.ok("rank", "1", "urgent")["writes"], [])

    def test_rank_untriaged_and_off_board_keeps_one_label_and_boards_it(self):
        self.set_state([item(1, "Two", None, labels=["found", "priority:soon", "priority:later"])], labels=LABELS)
        self.assertEqual(self.ok("rank", "1", "soon")["writes"],
                         ["unlabel #1 priority:later", "add #1 to board", "status #1 Ready"])
        self.assertEqual(self.state()[1]["labels"], ["found", "priority:soon"])

    def test_rank_leaves_a_started_issue_in_its_column(self):
        self.set_state([found(1, "Flaky", "later", "In progress", assignees=["dev"])], labels=LABELS)
        self.assertEqual(self.ok("rank", "1", "soon")["status"], "in_progress")
        self.assertEqual(self.state()[1]["status"], "In progress")

    def test_refusals_write_nothing(self):
        self.set_state([item(1, "S1.3 — Card"), found(2, "Done", state="CLOSED", status="Done")], labels=LABELS)
        for n, reason in (("1", "not_found"), ("2", "taken")):
            code, out, _ = self.run_cli("rank", n, "urgent")
            self.assertEqual((code, out["reason"], out["writes"]), (3, reason, []))
        self.assertEqual(self.log(), [])

    def test_missing_priority_label_is_usage(self):
        self.set_state([found(1, "Flaky")], labels=["found", "priority:soon", "priority:later"])
        code, out, _ = self.run_cli("rank", "1", "soon")
        self.assertEqual(code, 2)
        self.assertIn("'priority:urgent'", out["message"])
        self.assertEqual(self.log(), [])


class NoteTests(TrackerCase):
    def test_note_posts_once(self):
        self.set_state([found(1, "Flaky", comments=["Earlier."])])
        path = self.dir / "note.md"
        path.write_text("Seen again: 2 of 10 runs.\n")
        out = self.ok("note", "1", "--file", str(path))
        self.assertEqual(out, {"number": 1, "posted": True, "url": "https://github.com/acme/shop/issues/1",
                               "writes": ["comment #1"]})
        self.assertEqual(self.ok("note", "1", "--file", str(path)), {**out, "posted": False, "writes": []})
        self.assertEqual(self.state()[1]["comments"], ["Earlier.", "Seen again: 2 of 10 runs."])
        path.write_text(" \n")
        self.assertEqual(self.run_cli("note", "1", "--file", str(path))[0], 2)
        self.assertEqual(self.run_cli("note", "1", "--file", str(self.dir / "missing.md"))[0], 2)


class FoundWorkItemTests(TrackerCase):
    def test_claim_and_plan_work_on_a_found_issue(self):
        self.set_state([found(1, "Flaky", "urgent", body="Summary.")])
        out = self.ok("claim", "1")
        self.assertEqual((out["kind"], out["card"], out["writes"]),
                         ("found", None, ["assign #1 dev", "status #1 In progress", "comment #1 claim"]))
        (self.dir / "plan.md").write_text("Plan.")
        self.ok("plan", "1", "--file", str(self.dir / "plan.md"))
        self.assertEqual(self.state()[1]["body"], "Summary.\n\n<!-- aw:plan:start -->\nPlan.\n<!-- aw:plan:end -->\n")
        self.assertEqual(self.run_cli("bullets", "1")[1]["reason"], "not_a_card")

    def test_work_order_for_a_found_issue_carries_its_body_as_authority(self):
        body = "Summary.\n\n## Acceptance\n\n- `npm test` passes 20 of 20 runs.\n"
        self.set_state([found(1, "Flaky", "urgent", body=body)])
        out = self.ok("work-order", "1")
        self.assertEqual((out["kind"], out["authority"]), ("found", {"issue": tracker.url(P, 1), "text": body}))
        self.assertEqual(self.log(), [])

    def test_bullets_with_missing_bullet_label_is_usage_before_any_write(self):
        self.set_state([item(1, "S1.3 — Card", body=card_body("S1.3", "One."))], labels=["roadmap"])
        code, out, _ = self.run_cli("bullets", "1")
        self.assertEqual((code, out["error"]), (2, "usage"))
        self.assertIn(repr(B), out["message"])
        self.assertEqual(self.log(), [])

    def test_invalid_found_policy_is_usage(self):
        good = json.loads(self.policy_path.read_text())
        for name, found_key in (("no later", {"label": "found", "priorities": {"urgent": "u", "soon": "s"}}),
                                ("label not string", {**good["found"], "label": 1}), ("not object", "found")):
            with self.subTest(name):
                self.policy_path.write_text(json.dumps({**good, "found": found_key}))
                self.assertEqual(self.run_cli("next")[1]["error"], "usage")


class InitTests(TrackerCase):
    def init(self, *args, out="draft.json"):
        path = self.dir / out
        code, res, err = self.run_cli("init", "--out", str(path), *args)
        return code, res, path

    def drafted(self, *args, **state):
        self.set_state(state.pop("items", []), **state)
        code, res, path = self.init(*args)
        self.assertEqual(code, 0, res)
        self.assertEqual(res["policy"], str(path.resolve()))
        return res, json.loads(path.read_text()), tracker.load_policy(path)

    def test_sample_board_draft_round_trips_and_drives_next(self):
        shutil.copy(EVAL / "state.json", self.state_path)
        code, res, path = self.init()
        self.assertEqual((code, res["missing"]), (0, []))
        draft = json.loads(path.read_text())
        tracker.load_policy(path)
        self.assertEqual(draft["merge"], {"allowed": False})
        self.assertEqual(draft["repos"]["known"], {"shop": {"repo": "acme/shop", "base": "main", "merge": "rebase"}})
        self.assertEqual((draft["project"], draft["states"]), ({"owner": "acme", "number": 1, "status_field": "Status"},
                                                               P["states"]))
        self.assertEqual((draft["bullets"]["issue_type"], draft["found"]["issue_type"], len(draft["notes"])), ("Task", "Bug", 1))
        self.assertNotIn("authority", draft)
        self.assertNotIn("order", draft)
        self.assertEqual((res["detected"]["merge"], res["detected"]["open_cards"]), ("rebase", 9))
        code, out, _ = self.run_cli("--policy", str(path), "next", policy=False)
        self.assertEqual((code, self.numbers(out)), (0, [4, 6, 11]))
        self.assertEqual(self.log(), [])

    def test_default_board_columns_leave_three_states_missing(self):
        res, draft, _ = self.drafted(items=[item(1, "Card")], boards=[
            {"owner": "acme", "number": 3, "columns": ["Todo", "In Progress", "Done"]}])
        self.assertEqual(draft["states"], {"backlog": "Backlog", "ready": "Todo", "in_progress": "In Progress",
                                           "in_review": "In review", "blocked": "Blocked", "done": "Done"})
        self.assertEqual([(m["what"], m["name"]) for m in res["missing"]],
                         [("state", "backlog"), ("state", "in_review"), ("state", "blocked")])
        self.assertIn("'In review'", res["missing"][1]["fix"])
        self.assertEqual(res["detected"]["states"]["blocked"], None)
        self.assertEqual(draft["project"]["number"], 3)

    def test_missing_labels_and_cards_are_listed_with_fixes(self):
        res, _, _ = self.drafted(items=[item(1, "Chore", labels=[])], labels=["roadmap", "found"])
        self.assertEqual(res["detected"]["labels"], ["roadmap", "found"])
        self.assertEqual([(m["what"], m["name"], m["fix"]) for m in res["missing"]], [
            ("label", "tracer-bullet", "gh label create tracer-bullet -R acme/shop"),
            ("label", "priority:urgent", "gh label create priority:urgent -R acme/shop"),
            ("label", "priority:soon", "gh label create priority:soon -R acme/shop"),
            ("label", "priority:later", "gh label create priority:later -R acme/shop"),
            ("cards", "roadmap", "add the 'roadmap' label to the open issues that are roadmap cards")])

    def test_several_boards_are_ambiguous_until_one_is_named(self):
        boards = [{"owner": "acme", "number": 1, "title": "Roadmap"}, {"owner": "dev", "number": 4, "title": "Mine"},
                  {"owner": "acme", "number": 2, "closed": True}, {"owner": "acme", "number": 7, "linked": False}]
        self.set_state([item(1, "Card")], boards=boards)
        code, res, path = self.init()
        self.assertEqual((code, res["reason"], res["writes"]), (3, "ambiguous", []))
        self.assertEqual(res["choices"], [{"project": "acme/1", "title": "Roadmap"}, {"project": "dev/4", "title": "Mine"}])
        self.assertFalse(path.exists())
        for ref in ("dev/4", "acme/7"):  # a named board need not be linked
            with self.subTest(ref):
                code, res, path = self.init("--project", ref, out=f"{ref.replace('/', '-')}.json")
                self.assertEqual((code, res["detected"]["project"]), (0, ref))
        self.assertEqual(self.init("--project", "acme")[0], 2)
        self.assertEqual(self.log(), [])

    def test_no_board_refused(self):
        self.set_state([], boards=[{"owner": "acme", "number": 2, "closed": True}])
        code, res, path = self.init()
        self.assertEqual((code, res["reason"]), (3, "no_board"))
        self.assertFalse(path.exists())

    def test_existing_file_is_refused_and_untouched(self):
        self.set_state([], fail=["AwInit", "AwRepoView"])
        before = self.policy_path.read_text()
        for args in ((), ("--out", str(self.policy_path))):
            with self.subTest(args):
                code, res, _ = self.run_cli("init", *args)  # default output: the --policy path
                self.assertEqual((code, res["reason"], res["writes"]), (3, "exists", []))
        self.assertEqual(self.policy_path.read_text(), before)

    def test_default_output_is_the_policy_path_and_repository_of_the_cwd(self):
        self.policy_path.unlink()
        self.set_state([item(1, "Card")], repo="acme/app")
        code, res, _ = self.run_cli("init")
        self.assertEqual((code, res["policy"]), (0, str(self.policy_path.resolve())))
        self.assertEqual(tracker.load_policy(self.policy_path)["repo"], "acme/app")
        self.policy_path.unlink()
        self.set_state([], fail=["AwRepoView"])
        code, res, _ = self.run_cli("init")
        self.assertEqual((code, res["operation"]), (4, "AwRepoView"))
        self.assertEqual(self.run_cli("init", "--repo", "acme/shop")[0], 0)  # --repo skips the lookup
        self.assertEqual(tracker.load_policy(self.policy_path)["repo"], "acme/shop")

    def test_merge_method_issue_types_and_read_failure(self):
        for state, method in ((dict(merge_queue=True), "queue"), (dict(merge_methods=["merge", "squash"]), "squash"),
                              (dict(merge_methods=["merge"]), "merge")):
            with self.subTest(method):
                _, draft, _ = self.drafted(default_branch="trunk", issue_types=["Feature"], **state)
                (self.dir / "draft.json").unlink()
                self.assertEqual(draft["repos"]["known"]["shop"], {"repo": "acme/shop", "base": "trunk", "merge": method})
                self.assertEqual(draft["merge"], {"allowed": False})
                self.assertNotIn("issue_type", draft["bullets"])
                self.assertNotIn("issue_type", draft["found"])
        self.set_state([], fail=["AwInit"])
        code, res, path = self.init()
        self.assertEqual((code, res["operation"]), (4, "AwInit"))
        self.assertFalse(path.exists())
        self.assertEqual(self.log(), [])


class LogicTests(unittest.TestCase):
    def test_authority_section_runs_to_the_next_heading_of_same_or_higher_level(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "R.md"
            f.write_text("## A1 — x\n\n### A1.1 — One\n\nbody\n#### detail\nmore\n\n### A1.10 — Ten\n\nten\n")
            one = tracker.authority_section({"authority": str(f)}, "A1.1")
            self.assertEqual((one["lines"], one["text"].splitlines()[-1]), ([3, 7], "more"))
            self.assertEqual(tracker.authority_section({"authority": str(f)}, "A1.10")["text"], "### A1.10 — Ten\n\nten")
            self.assertIn("error", tracker.authority_section({"authority": str(f)}, "A2"))

    def test_repos_come_from_the_card_line_else_the_policy_default(self):
        p = {"repo": "acme/shop", "merge": {"method": "rebase"},
             "repos": {"default": "api", "known": {"api": {"repo": "acme/api", "base": "main"},
                                                    "web": {"repo": "acme/web", "base": "dev", "merge": "squash"}}}}
        self.assertEqual(tracker.repos_of(p, "Text.\nRepos: web, api\n"),
                         [{"name": "web", "repo": "acme/web", "base": "dev", "merge": "squash"},
                          {"name": "api", "repo": "acme/api", "base": "main", "merge": "rebase"}])
        self.assertEqual([r["name"] for r in tracker.repos_of(p, "No line.")], ["api"])
        self.assertEqual([r["name"] for r in tracker.repos_of(p, "Card.\n\n#### A1.1\n- **Repos:** web")], ["web"])
        self.assertIn("error", tracker.repos_of(p, "Repo: cli")[0])
        # Found-issue intake writes the label in full.
        self.assertEqual([r["name"] for r in tracker.repos_of(p, "## Acceptance\n- x\n\nRepositories: web\n")], ["web"])
        self.assertEqual(tracker.repos_of({"repo": "acme/shop"}, ""), [{"repo": "acme/shop", "base": None, "merge": None}])

    def test_state_mapping_by_normalized_name_or_alias(self):
        m = tracker.map_states
        self.assertEqual(m(["To Do", "in-progress", "In Review 👀", "Review", "DONE", "Back log"]),
                         {"backlog": "Back log", "ready": "To Do", "in_progress": "in-progress", "in_review": "Review",
                          "blocked": None, "done": "DONE"})
        self.assertEqual(m(["In Review 👀", "Doing", "Ready for QA", "Todo later", "Not done"]),
                         {"backlog": None, "ready": None, "in_progress": "Doing", "in_review": None, "blocked": None,
                          "done": None})
        self.assertEqual(m(["Ready", "To do"])["ready"], "Ready")  # the state's own name before an alias
        self.assertEqual(m(["ready", "Ready"])["ready"], "ready")  # duplicates: the first column
        self.assertEqual(m([]), dict.fromkeys(tracker.STATE_KEYS))

    def test_title_similarity(self):
        s = tracker.similar
        self.assertTrue(s("Checkout test flaky", "checkout TEST is flaky!"))  # case, punctuation, short words
        self.assertTrue(s("Flaky test", "Flaky checkout test times out"))  # 4*2 >= 2+5
        self.assertFalse(s("Flaky test", "Flaky checkout search page times out"))  # 4*2 < 2+6
        self.assertFalse(s("A to B", "a to b"))  # no word of three letters
        self.assertFalse(s("", ""))
        self.assertFalse(s("", "Flaky test"))
        self.assertTrue(s("S1.3 — Search", "Search"))  # ids and numbers are not words
        self.assertEqual(tracker.words("it's 2x-faster, e.g. UI"), {"faster"})

    def test_priority_needs_exactly_one_label(self):
        f = lambda *labels: {"labels": list(labels)}  # noqa: E731
        self.assertEqual(tracker.priority(P, f("found", "priority:soon")), "soon")
        self.assertIsNone(tracker.priority(P, f("found")))
        self.assertIsNone(tracker.priority(P, f("found", "priority:soon", "priority:urgent")))

    def test_summary_cuts_at_sentence_or_90_characters(self):
        self.assertEqual(tracker.summary("Add the box. Then the list."), "Add the box")
        self.assertEqual(tracker.summary("Version 1.2 ships, see `a.b`"), "Version 1.2 ships, see `a.b`")
        cut = tracker.summary("word " * 40)
        self.assertEqual(len(cut), 90)
        self.assertTrue(cut.endswith("…"))

    def test_parse_bullets_and_card_id(self):
        pattern = re.compile(json.loads((EVAL / "tracker-policy.json").read_text())["bullets"]["pattern"], re.M)
        body = "Intro\r\n\r\n1. `A1.1.T1` — First thing.\r\n2. `A1.1.T2` — Second.\r\n- not a bullet\r\n"
        self.assertEqual(tracker.parse_bullets(body, pattern), [("A1.1.T1", "First thing."), ("A1.1.T2", "Second.")])
        self.assertEqual(tracker.card_id("A1.1 — Title — with dash"), "A1.1")

    def test_replace_plan_keeps_text_outside_the_section(self):
        body = "a\n<!-- aw:plan:start -->\nold\n<!-- aw:plan:end -->\nb"
        self.assertEqual(tracker.replace_plan(body, "new\n"), "a\n<!-- aw:plan:start -->\nnew\n<!-- aw:plan:end -->\nb")
        self.assertEqual(tracker.replace_plan("", "p"), "<!-- aw:plan:start -->\np\n<!-- aw:plan:end -->\n")
        self.assertEqual(tracker.replace_plan("x", "\\1 $&"), "x\n\n<!-- aw:plan:start -->\n\\1 $&\n<!-- aw:plan:end -->\n")


if __name__ == "__main__":
    unittest.main()
