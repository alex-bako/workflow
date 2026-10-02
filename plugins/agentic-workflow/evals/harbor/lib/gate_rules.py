"""RewardKit criteria shared by the review-gate tasks (E14, aw-arbiter).

prepare.py copies this file into each gate task's tests/ as _gate_rules.py (the
leading underscore loads it before case.py) together with expected.json, the
hashes of every workspace file. Every criterion is shared and returns False
instead of raising: an exception aborts RewardKit and no reward is written.

Facts are graded by finding ID and class word, not by phrasing: IDs compare
case-insensitively, a class field counts by the first class word it contains
("Advisory (style)" is advisory), list entries may be IDs or objects with an
`id`, and `after_round` may be a number or a digit string. `reason` is prose and
only has to be present.
"""
import hashlib
import json
import re
from pathlib import Path

from rewardkit import criterion

EXPECTED = Path(__file__).with_name("expected.json")
VERDICT = "gate-verdict.json"
CLASSES = ("actionable", "advisory", "rejected")
ID = re.compile(r"\bR\d+-[A-Z]+\d+\b", re.I)
LISTS = ("repair", "reclassified", "repeats", "found_work")


def _verdict(ws):
    try:
        data = json.loads((ws / VERDICT).read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _text(value):
    return value if isinstance(value, str) else ""


def _id(value):
    """The finding ID an entry names: a string, or an object's `id`."""
    if isinstance(value, dict):
        value = value.get("id")
    match = ID.search(_text(value))
    return match.group(0).upper() if match else None


def _ids(ws, key):
    items = _verdict(ws).get(key)
    return [_id(i) for i in items] if isinstance(items, list) else [None]


def _entries(ws, key):
    items = _verdict(ws).get(key)
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


def _class(value):
    found = [(m.start(), m.group(0)) for c in CLASSES
             for m in [re.search(rf"\b{c}\b", _text(value), re.I)] if m]
    return min(found)[1].lower() if found else None


@criterion(shared=True)
def verdict_file_exists_and_parses(workspace: Path) -> bool:
    data = _verdict(workspace)
    if not data or _verdict_word(data) not in ("stop", "repair", "replan", "ask"):
        return False
    if not all(isinstance(data.get(k), list) for k in LISTS):
        return False
    if None in _ids(workspace, "repair") + _ids(workspace, "found_work"):
        return False
    if not all(isinstance(e, dict) and _id(e) for k in ("reclassified", "repeats")
               for e in data[k]):
        return False
    return _round(data) is not None and bool(_text(data.get("reason")).strip())


def _verdict_word(data):
    match = re.fullmatch(r"\W*(stop|repair|replan|ask)\W*", _text(data.get("verdict")), re.I)
    return match.group(1).lower() if match else None


def _round(data):
    value = data.get("after_round")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return int(value.strip()) if isinstance(value, str) and value.strip().isdigit() else None


@criterion(shared=True, description="the verdict is {verdict}")
def verdict_is(workspace: Path, verdict: str) -> bool:
    return _verdict_word(_verdict(workspace)) == verdict


@criterion(shared=True, description="after_round is {number}")
def after_round_is(workspace: Path, number: int) -> bool:
    return _round(_verdict(workspace)) == number


@criterion(shared=True, description="repair lists exactly {ids}")
def repair_is_exactly(workspace: Path, ids: list) -> bool:
    got = _ids(workspace, "repair")
    return len(got) == len(set(got)) and set(got) == {i.upper() for i in ids}


@criterion(shared=True, description="found_work lists exactly {ids}")
def found_work_is_exactly(workspace: Path, ids: list) -> bool:
    got = _ids(workspace, "found_work")
    return len(got) == len(set(got)) and set(got) == {i.upper() for i in ids}


@criterion(shared=True, description="{finding} reclassified to {to}")
def reclassified_to(workspace: Path, finding: str, to) -> bool:
    """`to` is a class, or a list of classes the contract allows equally."""
    allowed = {to} if isinstance(to, str) else set(to)
    return any(_id(e) == finding.upper() and _class(e.get("to")) in allowed
               for e in _entries(workspace, "reclassified"))


@criterion(shared=True, description="repeats lists exactly {pairs}")
def repeats_are_exactly(workspace: Path, pairs: dict) -> bool:
    entries = _entries(workspace, "repeats")
    got = {}
    for e in entries:
        got.setdefault(_id(e), set()).update(m.upper() for m in ID.findall(_text(e.get("of"))))
    return (len(entries) == len(got)
            and set(got) == {k.upper() for k in pairs}
            and all(got[k.upper()] == {of.upper()} for k, of in pairs.items()))


@criterion(shared=True, description="{ids} keep the class actionable")
def stay_actionable(workspace: Path, ids: list) -> bool:
    keep = {i.upper() for i in ids}
    moved = {_id(e) for e in _entries(workspace, "reclassified")
             if _class(e.get("to")) != "actionable"}
    return not keep & (moved | set(_ids(workspace, "repeats")) | set(_ids(workspace, "found_work")))


@criterion(shared=True)
def never_raises_a_class(workspace: Path) -> bool:
    return not any(_class(e.get("to")) == "actionable" and _class(e.get("from")) != "actionable"
                   for e in _entries(workspace, "reclassified"))


@criterion(shared=True)
def ledger_plan_and_source_unchanged_only_verdict_written(workspace: Path) -> bool:
    try:
        expected = json.loads(EXPECTED.read_text())["files"]
    except (OSError, ValueError, KeyError):
        return False
    actual = {p.relative_to(workspace).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(workspace.rglob("*")) if p.is_file()}
    return actual.pop(VERDICT, None) is not None and actual == expected
