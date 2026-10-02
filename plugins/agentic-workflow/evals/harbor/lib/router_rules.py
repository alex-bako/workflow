"""RewardKit criteria shared by the router tasks (E12 and its control).

prepare.py copies this file into each router task's tests/ as _router_rules.py; the
leading underscore makes it load before the step's case.py. Every criterion is
shared, so this file registers no score itself. A criterion returns False rather
than raise: an exception aborts the RewardKit run and no reward is written.

Step 1 grades the packet at /app/review-packet.md; step 2 grades the paired
reviewer's /app/review-report.json.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

from rewardkit import criterion

EXPECTED = Path(__file__).with_name("expected.json")
PACKET = "review-packet.md"
REPORT = "review-report.json"
ORDER = ("identity", "contract", "change map", "must read", "skip", "lenses", "evidence")
HEADING = re.compile(
    r"^\s*(?P<hash>#{1,6}\s*)?(?P<bold>\*\*|__)?\s*(?:\d+[.)]\s*)?"
    r"(?P<name>identity|contracts?|change[ -]?map|must[ -]?read|skip|lenses|evidence|ledger)"
    r"\b(?P<rest>.*)$", re.I)
# path:N, path:LN, path#LN, optionally -M / -LM
REF = re.compile(r"(?P<path>[\w./-]+\.(?:md|mjs|json))(?::L?|#L)(?P<a>\d+)"
                 r"(?:\s*[-–]\s*L?(?P<b>\d+))?")
# ":10" or ":15-16" after a file the section already named
PATH = re.compile(r"[\w./-]+\.(?:md|mjs|json)")
SHORT = re.compile(r"(?<![\w./-]):L?(?P<a>\d+)(?:\s*[-–]\s*L?(?P<b>\d+))?")
# "L10:" or "L15-16:" opening an item under a heading that named the file
BARE_L = re.compile(r"^\W*L(?P<a>\d+)(?:\s*[-–]\s*L?(?P<b>\d+))?(?=\s*:)")
LINES = re.compile(r"(?:\.mjs:L?|\.mjs`?,?\s+|#L|\bL|\blines?\s+|\(|\|\s*)(?P<a>\d+)(?:\s*[-–]\s*L?(?P<b>\d+))?")
NOISE_SKIP = (("src/generated", "schema.mjs"), ("package-lock.json",), ("legacy",),
              ("discounts",))
NOISE_ANY = ("src/generated", "schema.mjs", "package-lock", "legacy", "discounts")
ALLOWED = re.compile(r"[^\n]*packet could not cover[^\n]*", re.I)
# Verdict phrases only: Lenses and Must read legitimately name risks with ordinary
# words (bug, broken, defect, finding), so those are not in the list.
VERDICT = re.compile(
    r"\b(?:approve[sd]?|approval|lgtm|looks good|ship it|ready to merge|safe to merge"
    r"|verdict|must[- ]fix|blockers?|incorrect|is wrong"
    r"|(?:is|are|looks|seems) (?:correct|fine|safe|ok)|no (?:issues|problems|regressions))\b",
    re.I)
LEDGER_EMPTY = re.compile(r"^(?:re-?review(?: only)?\W*)?(?:none|n/?a|not applicable|empty|(?:first|initial) (?:review|packet|round)"
                          r"|no prior|not an? re-?review|no re-?review)\b", re.I)
# Must read: the caller's reason has to state the unit risk, never wave it through.
UNIT = re.compile(r"\bcents?\b|\bunits?\b|\bdollars?\b", re.I)
RISK = re.compile(r"chang|now returns|outside (?:the|this) diff|not in the diff|untested"
                  r"|no test|not tested|break|mismatch|risk|still (?:treats|expects|assumes|prints)",
                  re.I)
DISMISSIVE = re.compile(r"\b(?:already|consistent|unaffected|not affected|nothing to check"
                        r"|safe|no risk|no change needed|fine)\b", re.I)


def _read(ws, rel):
    try:
        return (ws / rel).read_text(errors="ignore")
    except OSError:
        return ""


def _sections(text):
    """{name: body text} for the first occurrence of each known heading, plus order."""
    found, order, current = {}, [], None
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            rest = m["rest"].strip()
            content = rest.lstrip("*_ ").lstrip(":").lstrip("*_ ").strip()
            if m["hash"] or m["bold"] or rest.lstrip("*_ ").startswith(":") or not rest:
                name = re.sub(r"[ -]+", " ", m["name"].lower())
                name = {"contracts": "contract", "changemap": "change map",
                        "mustread": "must read"}.get(name.replace(" ", ""), name)
                if name in found:
                    current = None  # a repeated heading ends the section; first wins
                    continue
                found[name], current = [content] if content else [], name
                order.append(name)
                continue
        if current:
            found[current].append(line)
    return {k: "\n".join(v) for k, v in found.items()}, order


def _packet(ws):
    return _sections(_read(ws, PACKET))[0]


def _items(body):
    """Top-level bullets, table rows or paragraphs, with their continuation lines
    (indented lines, nested bullets, block quotes) joined."""
    items, gap = [], True
    for line in body.splitlines():
        s = line.strip()
        if not s:
            gap = True
            continue
        bullet = not line[:1].isspace() and re.match(r"([-*+|]|\d+[.)])\s", s)
        if not items or bullet or (gap and not s.startswith(">")):
            items.append(s)
        else:
            items[-1] += " " + s
        gap = False
    return items


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[`\"'*_“”‘’]", "", text)).lower()


def _span(m):
    a = int(m["a"])
    return a, int(m["b"] or a)


def _refs(section):
    """(item, path, first, last line) for every `path:N[-M]` ref. A bare `:N` takes the
    file of the ref before it, else the file a heading item ("From `x.md`:") named. The
    refs of a heading item ("Acceptance (`x.md:8-11`):") cover the items under it that
    carry none of their own."""
    out, last, block = [], "", []
    for item in _items(section):
        full = list(REF.finditer(item))
        short = list(SHORT.finditer(item)) + list(BARE_L.finditer(item))
        own = [(m["path"], *_span(m)) for m in full]
        for m in short:
            before = [f["path"] for f in full if f.end() <= m.start()]
            if before or last:
                own.append((before[-1] if before else last, *_span(m)))
        heading = item.rstrip(" *_").endswith(":")
        if full:
            last = full[-1]["path"]
        elif not short and heading and PATH.search(item):
            last = PATH.findall(item)[-1]
        if heading:
            block = own
        out += [(item, *ref) for ref in (own or block)]
    return out


def _cites(section, suffix, line, fragments, max_span):
    """An item with a `<...suffix>:N[-M]` ref covering `line` and one of `fragments`."""
    return any(path.endswith(suffix) and a <= line <= b and b - a < max_span
               and any(f in _norm(item) for f in fragments)
               for item, path, a, b in _refs(section))


def _git(ws, *args):
    # The image's `git` on PATH is a logging wrapper; the verifier calls the real one.
    try:
        return subprocess.run(["/usr/bin/git", "-C", str(ws), *args],
                              capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _expected():
    try:
        return json.loads(EXPECTED.read_text())
    except (OSError, ValueError):
        return {}


# ---- step 1: the packet ---------------------------------------------------------

@criterion(shared=True)
def packet_exists_within_150_lines(workspace: Path) -> bool:
    text = _read(workspace, PACKET)
    return bool(text.strip()) and len(text.splitlines()) <= 150


@criterion(shared=True)
def packet_sections_in_order_without_ledger(workspace: Path) -> bool:
    found, order = _sections(_read(workspace, PACKET))
    if [n for n in order if n in ORDER] != list(ORDER):
        return False
    ledger = _norm(ALLOWED.sub(" ", found.get("ledger", ""))).strip(" .:-")
    return not ledger or (len(ledger) <= 200 and LEDGER_EMPTY.match(ledger) is not None
                          and not REF.search(ledger))


@criterion(shared=True)
def identity_names_exact_base_and_head(workspace: Path) -> bool:
    identity = _packet(workspace).get("identity", "").lower()
    tokens = set(re.findall(r"\b[0-9a-f]{7,40}\b", identity))
    shas = [_git(workspace, "rev-parse", ref).strip() for ref in ("base", "main")]
    return all(len(s) == 40 and any(s.startswith(t) for t in tokens) for s in shas)


@criterion(shared=True)
def contract_quotes_caller_acceptance_at_plan_line_10(workspace: Path) -> bool:
    return _cites(_packet(workspace).get("contract", ""), "T1.md", 10,
                  ("works in cents", "printed amount is unchanged"), 5)


@criterion(shared=True)
def contract_quotes_invariant_at_plan_lines_15_16(workspace: Path) -> bool:
    contract = _packet(workspace).get("contract", "")
    frags = ("integer number of cents", "no float arithmetic")
    return any(_cites(contract, "T1.md", n, frags, 5) for n in (15, 16))


@criterion(shared=True)
def contract_refs_point_at_real_lines_not_whole_documents(workspace: Path) -> bool:
    files = _expected().get("files", {})
    refs = _refs(_packet(workspace).get("contract", ""))
    for _, path, a, b in refs:
        path = path.removeprefix("/app/")
        hits = [f for f in files if f == path or f.endswith("/" + path)]
        if not hits or a < 1 or b < a or b - a >= 20:
            return False
        if b > len(_read(workspace, hits[0]).splitlines()):
            return False
    return bool(refs)


@criterion(shared=True)
def must_read_names_invoice_caller_with_range_and_unit_reason(workspace: Path) -> bool:
    for item in _items(_packet(workspace).get("must read", "")):
        if "invoice.mjs" not in item:
            continue
        spans = [_span(m) for m in LINES.finditer(item)]
        reason = _norm(item)
        if any(a <= 13 and b >= 9 for a, b in spans) and UNIT.search(reason) \
                and RISK.search(reason) and not DISMISSIVE.search(reason):
            return True
    return False


@criterion(shared=True)
def change_map_lists_invoice(workspace: Path) -> bool:
    return "invoice.mjs" in _packet(workspace).get("change map", "")


@criterion(shared=True)
def skip_lists_noise_and_must_read_excludes_it(workspace: Path) -> bool:
    packet = _packet(workspace)
    skip = packet.get("skip", "")
    # What an item sends the reviewer to read is its head, before the reason. "None: grep
    # over src, test, legacy found no other caller" sends nobody to read legacy.
    must = "\n".join(re.split(r"\s[—–-]\s|\(|(?<=[`\d]):\s", i, maxsplit=1)[0]
                     for i in _items(packet.get("must read", ""))
                     if not re.match(r"[-*+|\s]*(?:none|nothing)\b", i, re.I))
    return (all(any(x in skip for x in group) for group in NOISE_SKIP)
            and not any(x in must for x in NOISE_ANY))


@criterion(shared=True)
def packet_states_no_review_verdict(workspace: Path) -> bool:
    text = _read(workspace, PACKET)
    return bool(text.strip()) and VERDICT.search(ALLOWED.sub(" ", text)) is None


@criterion(shared=True, description="no file in /app changed except {outputs}; git state is base + head")
def workspace_unchanged_except(workspace: Path, outputs: list) -> bool:
    expected = _expected()
    if not expected:
        return False
    actual = {}
    for p in sorted(workspace.rglob("*")):
        rel = p.relative_to(workspace).as_posix()
        if p.is_file() and rel.split("/")[0] != ".git" and rel not in outputs:
            actual[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    status = [line for line in _git(workspace, "status", "--porcelain", "-uall").splitlines()
              if line[3:] not in outputs]
    changed = sorted(_git(workspace, "diff", "--name-only", "base", "HEAD").split())
    return (actual == expected["files"] and not status
            and changed == expected["changed"]
            and _git(workspace, "rev-list", "--count", "--all").strip() == "2"
            and _git(workspace, "symbolic-ref", "--short", "HEAD").strip() == "main"
            and not _git(workspace, "stash", "list").strip())


# ---- step 2: the paired reviewer -------------------------------------------------

def _report(ws):
    try:
        data = json.loads(_read(ws, REPORT))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _findings(ws):
    items = _report(ws).get("findings")
    return [f for f in items if isinstance(f, dict)] if isinstance(items, list) else []


def _text(value):
    return value if isinstance(value, str) else ""


def _log(name):
    """Calls logged by the image's PATH stubs during this step ("" when none)."""
    try:
        return (Path("/var/log") / name).read_text(errors="ignore")
    except FileNotFoundError:
        return ""
    except OSError:
        return None


@criterion(shared=True)
def review_report_exists_and_parses(workspace: Path) -> bool:
    data = _report(workspace)
    findings = data.get("findings")
    if not _read(workspace, "review-report.md").strip() or not isinstance(findings, list):
        return False
    if data.get("status") not in {"clean", "findings", "blocked"}:
        return False
    keys = ("id", "file", "impact", "evidence")
    if not all(isinstance(f, dict) and all(_text(f.get(k)).strip() for k in keys)
               for f in findings):
        return False
    ids = [f["id"] for f in findings]
    return len(ids) == len(set(ids))


@criterion(shared=True)
def reports_invoice_prints_cents_as_dollars(workspace: Path) -> bool:
    for f in _findings(workspace):
        where = _text(f.get("file"))
        lines = [int(n) for n in re.findall(r"invoice\.mjs:L?(\d+)", where)]
        text = _norm(" ".join(_text(f.get(k)) for k in ("impact", "evidence", "fix")))
        if "invoice.mjs" in where and (any(9 <= n <= 13 for n in lines)
                                       or "invoiceline" in _norm(where + text)) \
                and re.search(r"cent|dollar|\b100\b|350", text) and _text(f.get("evidence")).strip():
            return True
    return False


@criterion(shared=True)
def reports_clean_without_invented_findings(workspace: Path) -> bool:
    data = _report(workspace)
    return data.get("status") == "clean" and data.get("findings") == []


@criterion(shared=True)
def reviewer_did_no_blame_or_pull_request_archaeology(workspace: Path) -> bool:
    git_log, gh_log = _log("git-calls.log"), _log("gh-calls.log")
    if git_log is None or gh_log is None:
        return False
    # Not `remote`: the Claude Code harness itself runs `git remote` at startup.
    banned = {"blame", "annotate", "reflog", "fetch", "pull"}
    calls = [line.split() for line in git_log.splitlines()]
    return not gh_log.strip() and not any(banned & set(c) for c in calls)
