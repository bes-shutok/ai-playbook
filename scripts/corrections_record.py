#!/usr/bin/env python3
"""Shared corrections-record machinery for graded review certification.

The module owns: the corrections row schema (kinds ``script-verified`` and
``operator-acked`` over the plan and code families, with the vacuous-row
and empty-array edges); the seal-recorded anchor leg over the on-disk
``.ai-playbook/review-certs/<artifact-slug>.md`` file (the seal is read
from the working tree, never from git); the per-hop digest
binding to bytes re-derived from git (the seal's round-start bytes as hop
0); the linkage and terminal legs; seal integrity (the sidecar range
against the seal's certified range and hop-commit dating; the
append-only-entries duty is producer-side); the subject-bound
operator ack receipt whose witness record path is injected by the caller;
the seal slug shape gate (a slug outside the safe kebab shape refuses as a
schema error at the seal-path derivation, never echoing the slug); the
advisory-lock corrections append keyed on the artifact slug; the
excluded-region scanner for plan bytes (fences, inline spans, indented
code, setext underlines, thematic breaks, table delimiter rows, link
destinations); and the hermetic scratch-repo fixture builder shared by the
classifier selftests.

Retirement record (2026-10-11 seal-home re-point): the committed-history
seal witness is retired. The former ``committed_seal_text`` git read and
``entry_introduce_commit`` walk carried edited-entry detection and the
introduction-dating refusals; the witness was squash-orphaned
(docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md)
and dead after the 2026-10-10 untrack of all review content (commits
1dc2ae029, 6933f6c58), the seal being an untracked run artifact since.
Digest mutation is detected against the current on-disk seal file only;
review 2026-12.

Library first: importing has no side effects. Every refusal reason starts
with MARKER_PREFIX and avoids BANNED_LITERALS, so callers route the
corrections family on the marker alone. Consumers: the plan and code
delta classifiers, the staging validator, and the readiness gate.
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

# Routing contract: callers dispatch on MARKER_PREFIX first; the banned
# literals are the other families' routing substrings and must never
# appear inside a corrections reason.
MARKER_PREFIX = "corrections verification: "
BANNED_LITERALS = ("source_digest", "source_kind")

LEG_REASONS = {
    "schema": "schema refusal",
    "vacuous": "vacuous rule",
    "anchor": "anchor leg refused",
    "binding": "digest-binding leg refused",
    "linkage": "linkage leg refused",
    "terminal": "terminal leg refused",
    "seal": "seal leg refused",
    "receipt": "ack-receipt leg refused",
    "classify": "classification leg refused",
    "append": "append refused",
}


def leg_reason(leg, detail):
    return "%s%s: %s" % (MARKER_PREFIX, LEG_REASONS[leg], detail)


KIND_SCRIPT_VERIFIED = "script-verified"
KIND_OPERATOR_ACKED = "operator-acked"
ROW_KINDS = (KIND_SCRIPT_VERIFIED, KIND_OPERATOR_ACKED)
FAMILY_PLAN = "plan"
FAMILY_CODE = "code"
FAMILIES = (FAMILY_PLAN, FAMILY_CODE)

SHARED_ROW_KEYS = frozenset(
    ("kind", "before_digest", "after_digest", "hunks", "recorded_at",
     "recorded_by"))
PLAN_EVIDENCE_KEYS = frozenset(("evidence_commit",))
CODE_EVIDENCE_KEYS = frozenset(
    ("before_base", "before_head", "after_base", "after_head"))
RECEIPT_KEYS = frozenset(
    ("directive", "authorization_witness", "classifier_gap_row"))
HUNK_KEYS = frozenset(("header", "digest"))

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")

SEAL_DIR_RELPATH = ".ai-playbook/review-certs"
SEAL_ROUND_RE = re.compile(r"^## round (\d+)$")
SEAL_FIELD_RE = re.compile(r"^([a-z_]+): (.*)$")
BACKLOG_DIR_RELPATH = "docs/history/backlog"

# The seal slug shape (r1 fix fold): the artifact slug is interpolated into
# the seal relpath, so it must be a strict path-safe token before any path
# is derived: lowercase kebab segments of letters and digits joined by
# single hyphens, with no slashes, dots, whitespace, or separators. A slug
# carrying a banned routing literal would leak that literal into every leg
# reason or degradation message quoting the seal path, so the shape gate
# refuses it as a schema error, and the refusal never echoes the slug; the
# reserved-substring clause precedes the shape clause, so a slug carrying a
# banned literal is named as exactly that.
SEAL_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_SHAPE_RULE = (
    "the artifact slug must be a lowercase kebab token (letters and "
    "digits joined by single hyphens) with no slashes, dots, whitespace, "
    "separators, or reserved routing substrings")


class CorrectionsSchemaError(Exception):
    """A row, array, or record operand violating the schema; the message
    is a full prefixed reason."""


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def hermetic_git_env():
    """The subprocess environment for every git call: the host GIT_*
    family is dropped and the config pointers are parked on /dev/null."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_CONFIG_SYSTEM"] = "/dev/null"
    return env


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, env=hermetic_git_env())


def git_text(repo, *args):
    proc = run_git(repo, *args)
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace")


def git_bytes(repo, *args):
    proc = run_git(repo, *args)
    if proc.returncode != 0:
        return None
    return proc.stdout


# ---------------------------------------------------------------------------
# Row schema
# ---------------------------------------------------------------------------


def row_keys(kind, family):
    keys = set(SHARED_ROW_KEYS)
    keys |= set(PLAN_EVIDENCE_KEYS if family == FAMILY_PLAN
                else CODE_EVIDENCE_KEYS)
    if kind == KIND_OPERATOR_ACKED:
        keys.add("receipt")
    return keys


def _schema(detail):
    return leg_reason("schema", detail)


def row_schema_reason(row, family=None):
    """The prefixed schema refusal for a row, or None when it validates.
    Type checks always precede indexing, so a malformed row is a schema
    error naming the violated rule, never an index crash."""
    if not isinstance(row, dict):
        return _schema("row is not a JSON object")
    kind = row.get("kind")
    if kind not in ROW_KINDS:
        return _schema("unknown kind %r (kinds: %s)"
                       % (kind, ", ".join(ROW_KINDS)))
    fam = family
    if fam is None:
        if "evidence_commit" in row:
            fam = FAMILY_PLAN
        elif "before_base" in row or "after_base" in row:
            fam = FAMILY_CODE
        else:
            return _schema("row carries no family evidence fields")
    if fam not in FAMILIES:
        return _schema("unknown family %r" % (fam,))
    expected = row_keys(kind, fam)
    actual = set(row)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        return _schema("missing required key(s) %s for kind %s family %s"
                       % (missing, kind, fam))
    if extra:
        return _schema("unexpected key(s) %s" % extra)
    for field in ("before_digest", "after_digest"):
        if not isinstance(row[field], str) or not HEX64_RE.match(row[field]):
            return _schema("%s is not a hex64 digest" % field)
    if row["before_digest"] == row["after_digest"]:
        return _schema("before_digest equals after_digest: a vacuous row")
    hunks = row["hunks"]
    if not isinstance(hunks, list) or not hunks:
        return _schema("hunks is empty: a vacuous row")
    for index, hunk in enumerate(hunks):
        if not isinstance(hunk, dict) or set(hunk) != HUNK_KEYS:
            return _schema("hunk %d lacks the exact key set %s"
                           % (index, sorted(HUNK_KEYS)))
        if not isinstance(hunk["header"], str) or not hunk["header"]:
            return _schema("hunk %d header is not a non-empty string"
                           % index)
        if not isinstance(hunk["digest"], str) or not HEX64_RE.match(
                hunk["digest"]):
            return _schema("hunk %d digest is not a hex64 digest" % index)
    for field in ("recorded_at", "recorded_by"):
        if not isinstance(row[field], str) or not row[field]:
            return _schema("%s is not a non-empty string" % field)
    if kind == KIND_OPERATOR_ACKED:
        receipt = row["receipt"]
        if not isinstance(receipt, dict):
            return _schema("receipt is not a JSON object")
        r_missing = sorted(RECEIPT_KEYS - set(receipt))
        r_extra = sorted(set(receipt) - RECEIPT_KEYS)
        if r_missing:
            return _schema("receipt missing required key(s) %s" % r_missing)
        if r_extra:
            return _schema("receipt carries unexpected key(s) %s" % r_extra)
        for field in sorted(RECEIPT_KEYS):
            if not isinstance(receipt[field], str) or not receipt[field]:
                return _schema("receipt %s is not a non-empty string"
                               % field)
    return None


def validate_row(row, family=None):
    reason = row_schema_reason(row, family)
    if reason is not None:
        raise CorrectionsSchemaError(reason)


def corrections_array_reason(value):
    """The prefixed schema refusal for a corrections array value. Absent
    (None) means absent; an empty array is the empty-array schema error."""
    if value is None:
        return None
    if not isinstance(value, list):
        return _schema("corrections is not an array")
    if not value:
        return _schema("corrections array is empty (the empty-array edge)")
    for row in value:
        reason = row_schema_reason(row)
        if reason is not None:
            return reason
    return None


def validate_corrections_array(value):
    reason = corrections_array_reason(value)
    if reason is not None:
        raise CorrectionsSchemaError(reason)


def load_corrections(path):
    """The corrections rows from a JSON record operand: either a bare
    array or an object carrying a corrections member. Absent member means
    an empty history is being created and yields an empty list."""
    raw = Path(path).read_bytes()
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise CorrectionsSchemaError(
            _schema("record operand is not decodable JSON"))
    if isinstance(doc, dict):
        rows = doc.get("corrections")
        if rows is None:
            return []
        validate_corrections_array(rows)
        return rows
    validate_corrections_array(doc)
    return doc


# ---------------------------------------------------------------------------
# Git primitives over resolved inputs
# ---------------------------------------------------------------------------


def resolve_commit(repo, ref):
    text = git_text(repo, "rev-parse", "--verify", "%s^{commit}" % ref)
    if text is None:
        return None
    return text.strip() or None


def is_ancestor(repo, ancestor, descendant="HEAD"):
    """True, False, or None on a git plumbing failure."""
    proc = run_git(repo, "merge-base", "--is-ancestor", ancestor,
                   descendant)
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def commit_date(repo, commit):
    """The committer date as int, or None on a plumbing failure."""
    text = git_text(repo, "show", "-s", "--format=%ct", commit)
    if text is None:
        return None
    try:
        return int(text.strip())
    except ValueError:
        return None


def blob_bytes(repo, commit, path):
    return git_bytes(repo, "cat-file", "blob", "%s:%s" % (commit, path))


def diff_bytes(repo, base, head):
    return git_bytes(repo, "diff", "%s...%s" % (base, head))


def touches_path(repo, commit, path):
    """True when the commit's own diff changes path; None on a plumbing
    failure. --root keeps a repository's seed commit a valid witness."""
    text = git_text(repo, "diff-tree", "-r", "--name-only", "--no-commit-id",
                    "--root", commit, "--", path)
    if text is None:
        return None
    return bool(text.strip())


# ---------------------------------------------------------------------------
# Certification seal
# ---------------------------------------------------------------------------


class SealEntry:
    """One parsed seal entry: the round number, its key: value fields,
    and the exact block text (``block`` is write-only since the
    committed-history witness retired; parse_seal still fills it)."""

    def __init__(self, round_number, fields, block):
        self.round = round_number
        self.fields = fields
        self.block = block


def slug_shape_reason(slug):
    """The prefixed schema refusal for a seal slug outside the safe kebab
    shape, or None when the slug is path-safe. The reserved routing
    substring clause precedes the shape clause so a slug carrying a banned
    literal is named as exactly that; the refusal names the rule and never
    echoes the slug (echoing would leak a banned routing literal into a
    corrections reason)."""
    if not isinstance(slug, str) or not slug:
        return _schema("%s: the slug is not a non-empty string"
                       % SLUG_SHAPE_RULE)
    for literal in BANNED_LITERALS:
        if literal in slug:
            return _schema("%s: the slug carries a reserved routing "
                           "substring" % SLUG_SHAPE_RULE)
    if not SEAL_SLUG_RE.match(slug):
        return _schema("%s: the slug fails the shape" % SLUG_SHAPE_RULE)
    return None


def validate_slug_shape(slug):
    reason = slug_shape_reason(slug)
    if reason is not None:
        raise CorrectionsSchemaError(reason)


def seal_relpath(artifact_path, slug=None):
    if slug:
        validate_slug_shape(slug)
    name = slug if slug else Path(artifact_path).stem
    return "%s/%s.md" % (SEAL_DIR_RELPATH, name)


def parse_seal(text):
    """The seal entries in file order. A malformed header or field line
    yields an unparsable marker consumed by the caller as an unresolvable
    seal."""
    entries = []
    current = None
    for line in text.splitlines():
        header = SEAL_ROUND_RE.match(line)
        if header:
            current = (int(header.group(1)), [])
            entries.append(current)
            continue
        if current is None:
            continue
        field = SEAL_FIELD_RE.match(line)
        if field:
            current[1].append((field.group(1), field.group(2)))
        elif line.strip():
            return None
    parsed = []
    for number, lines in entries:
        parsed.append(SealEntry(number, dict(lines),
                                "\n".join(["## round %d" % number]
                                          + ["%s: %s" % kv
                                             for kv in lines])))
    return parsed


def seal_text(repo, rel):
    """The seal bytes on disk under the repo root, or None when the file
    is absent or unreadable (the seal is read from the working tree,
    never from git)."""
    try:
        return (Path(repo) / rel).read_text(encoding="utf-8")
    except OSError:
        return None


def load_seal_entry(repo, rel, round_number):
    """The single seal entry for the round, or None when the seal is
    unresolvable (missing file, unparsable text, absent or duplicated
    round). The seal is read from the working tree, never from git."""
    text = seal_text(repo, rel)
    if text is None:
        return None
    entries = parse_seal(text)
    if entries is None:
        return None
    matching = [e for e in entries if e.round == round_number]
    if len(matching) != 1:
        return None
    entry = matching[0]
    for key in ("artifact", "round_start_commit", "round_start_digest",
                "round_close_commit"):
        value = entry.fields.get(key)
        if not value:
            return None
    if not HEX40_RE.match(entry.fields["round_start_commit"]):
        return None
    if not HEX64_RE.match(entry.fields["round_start_digest"]):
        return None
    if not HEX40_RE.match(entry.fields["round_close_commit"]):
        return None
    return entry


# ---------------------------------------------------------------------------
# Operator ack receipt (subject-bound, out-of-band resolution)
# ---------------------------------------------------------------------------

_WITNESS_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*): (.*)$")
_TRAILER_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z-]*-by: .*$")


def parse_witness_fields(text):
    fields = {}
    for line in text.splitlines():
        match = _WITNESS_FIELD_RE.match(line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def resolve_ack_receipt(row, witness_path, repo_root, artifact_path):
    """Resolve an operator-acked row's receipt against the witness record
    path injected by the caller (fixtures inject a hermetic turn record;
    production injects the scheduler state file's turn record). Returns
    (True, detail) or (False, prefixed ack-receipt reason)."""
    receipt = row["receipt"]
    named = receipt["authorization_witness"]
    if os.path.normpath(named) != os.path.normpath(str(witness_path)):
        return False, leg_reason(
            "receipt", "unresolvable witness: the receipt names %r but "
            "resolution was given %r" % (named, str(witness_path)))
    try:
        text = Path(witness_path).read_text(encoding="utf-8")
    except OSError:
        return False, leg_reason(
            "receipt", "unresolvable witness: %s is unreadable"
            % witness_path)
    lines = [l for l in text.splitlines() if l.strip()]
    non_trailer = [l for l in lines if not _TRAILER_LINE_RE.match(l)]
    if not non_trailer and lines:
        return False, leg_reason(
            "receipt", "commit-trailer-only witness is not a turn record")
    fields = parse_witness_fields(text)
    for required in ("writer", "operator_direction"):
        if required not in fields:
            return False, leg_reason(
                "receipt", "witness is not a turn record: missing the %r "
                "named field" % required)
    if fields["writer"] == row["recorded_by"]:
        return False, leg_reason(
            "receipt", "turn record written by the recording session: the "
            "writer field equals the row's recorded_by %r"
            % row["recorded_by"])
    if fields["operator_direction"] != receipt["directive"]:
        return False, leg_reason(
            "receipt", "subject mismatch: the witness operator_direction "
            "field does not match the receipt directive")
    subject = (artifact_path, row["before_digest"], row["after_digest"])
    for member in subject:
        if member not in text:
            return False, leg_reason(
                "receipt", "subject mismatch: the witness does not echo "
                "%r" % member)
    gap_rel = receipt["classifier_gap_row"]
    gap_norm = os.path.normpath(gap_rel).replace(os.sep, "/")
    if gap_norm.startswith("../") or not gap_norm.startswith(
            BACKLOG_DIR_RELPATH + "/"):
        return False, leg_reason(
            "receipt", "classifier gap row %s is outside %s/"
            % (gap_rel, BACKLOG_DIR_RELPATH))
    gap_path = Path(repo_root) / gap_rel
    if not gap_path.is_file():
        return False, leg_reason(
            "receipt", "dangling classifier gap row path: %s" % gap_rel)
    gap_text = gap_path.read_text(encoding="utf-8", errors="replace")
    for hunk in row["hunks"]:
        if hunk["digest"] not in gap_text:
            return False, leg_reason(
                "receipt", "classifier gap row does not quote refused hunk "
                "digest %s" % hunk["digest"])
    return True, "receipt resolved against %s" % witness_path


# ---------------------------------------------------------------------------
# Advisory-lock corrections append
# ---------------------------------------------------------------------------

_APPEND_LOCK_DEADLINE = 5.0


def corrections_lock_path(repo_root, slug):
    git_dir = git_text(repo_root, "rev-parse", "--absolute-git-dir")
    base = Path(git_dir.strip()) if git_dir else Path(repo_root) / ".git"
    return base / ("corrections-lock-%s.lock" % slug)


def append_corrections(record_path, new_rows, repo_root, slug,
                       expect_sha256=None, family=None, timeout=None):
    """Append rows to a JSON corrections record under the advisory lock
    keyed on the artifact slug. Returns (True, sha256 of the written
    bytes) or (False, prefixed append refusal naming the concurrent-round
    possibility beside an unwitnessed mutation)."""
    deadline = time.monotonic() + (timeout if timeout is not None
                                   else _APPEND_LOCK_DEADLINE)
    for row in new_rows:
        try:
            validate_row(row, family)
        except CorrectionsSchemaError as exc:
            return False, str(exc)
    lock_path = corrections_lock_path(repo_root, slug)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+")
    try:
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    return False, leg_reason(
                        "append", "advisory lock busy: a concurrent "
                        "certification round may hold the lock beside an "
                        "unwitnessed mutation; re-derive from disk and "
                        "retry")
                time.sleep(0.05)
        path = Path(record_path)
        try:
            raw = path.read_bytes() if path.exists() else b""
        except OSError as exc:
            return False, leg_reason(
                "append", "record unreadable under the advisory lock: %s"
                % exc)
        if expect_sha256 is not None and sha256_hex(raw) != expect_sha256:
            return False, leg_reason(
                "append", "the record changed under the advisory lock: a "
                "concurrent certification round or an unwitnessed "
                "mutation; re-derive from disk and retry")
        if raw:
            try:
                doc = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return False, _schema(
                    "record operand is not decodable JSON")
            if not isinstance(doc, dict):
                return False, _schema(
                    "record operand is not a JSON object")
            existing = doc.get("corrections")
        else:
            doc = {}
            existing = None
        reason = corrections_array_reason(existing)
        if reason is not None and existing is not None:
            return False, reason
        rows = list(existing or [])
        rows.extend(new_rows)
        doc["corrections"] = rows
        written = (json.dumps(doc, indent=2, sort_keys=True)
                   + "\n").encode()
        try:
            path.write_bytes(written)
        except OSError as exc:
            return False, leg_reason(
                "append", "record not writable under the advisory lock: %s"
                % exc)
        return True, sha256_hex(written)
    finally:
        try:
            fcntl.flock(handle, fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


# ---------------------------------------------------------------------------
# Excluded-region scanner
# ---------------------------------------------------------------------------

_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LIST_MARKER_RE = re.compile(r"^(\s*)([-*+]|\d{1,9}[.)])(\s|$)")
_THEMATIC_RE = re.compile(
    r"^ {0,3}(?:\*(?: *\*){2,}|-(?: *-){2,}|_(?: *_){2,})[ \t]*$")
_SETEXT_RE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
_DELIM_ROW_RE = re.compile(
    r"^\s*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)+\|?[ \t]*$")
_AUTOLINK_RE = re.compile(
    r"<(?:[A-Za-z][A-Za-z0-9+.\-]*:[^<>\s]*|[\w.+-]+@[\w-]+(?:\.[\w-]+)+)>")


def _indent_columns(prefix):
    """The display column where a leading whitespace prefix ends, a tab
    counted as four columns."""
    column = 0
    for ch in prefix:
        column += 4 - (column % 4) if ch == "\t" else 1
    return column


def _closing_fence(line, char, length):
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:
        return False
    body = stripped.rstrip(" \t")
    return (bool(body) and set(body) == {char} and len(body) >= length)


def _inline_excluded_spans(line, base):
    """Char spans of inline code spans, ](...) link destinations, and
    <...> autolinks on one non-block-excluded line."""
    spans = []
    code_spans = []
    i, n = 0, len(line)
    while i < n:
        if line[i] == "`":
            j = i
            while j < n and line[j] == "`":
                j += 1
            run = "`" * (j - i)
            k, close = j, -1
            while True:
                k = line.find(run, k)
                if k == -1:
                    break
                end = k + (j - i)
                if (k == 0 or line[k - 1] != "`") and (
                        end >= n or line[end] != "`"):
                    close = end
                    break
                k = end
            if close != -1:
                spans.append((base + i, base + close))
                code_spans.append((i, close))
                i = close
            else:
                i = j
            continue
        i += 1
    segments = []
    cursor = 0
    for start, end in code_spans:
        segments.append((cursor, start))
        cursor = end
    segments.append((cursor, n))
    for seg_start, seg_end in segments:
        seg = line[seg_start:seg_end]
        i = 0
        while i < len(seg):
            if seg.startswith("](", i):
                depth, j = 1, i + 2
                while j < len(seg) and depth:
                    ch = seg[j]
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                    j += 1
                if depth == 0:
                    spans.append((base + seg_start + i + 1,
                                  base + seg_start + j))
                    i = j
                    continue
                i += 1
                continue
            if seg[i] == "<":
                match = _AUTOLINK_RE.match(seg, i)
                if match:
                    spans.append((base + seg_start + i,
                                  base + seg_start + match.end()))
                    i = match.end()
                    continue
            i += 1
    return spans


def scan_excluded(text):
    """(char_spans, excluded_line_numbers) for the plan-bytes excluded
    regions: fences (unclosed extends to end of file), indented code
    blocks after a blank line including list nesting, setext underlines,
    thematic breaks, table delimiter rows, and the inline spans."""
    lines = text.splitlines()
    spans = []
    excluded_lines = set()
    fence_char = None
    fence_len = 0
    prev_text = False
    prev_blank = True
    prev_code = False
    list_stack = []
    offset = 0
    for index, line in enumerate(lines):
        lineno = index + 1
        line_start = offset
        line_end = line_start + len(line)
        offset = line_end + 1
        if fence_char is not None:
            excluded_lines.add(lineno)
            spans.append((line_start, line_end))
            if _closing_fence(line, fence_char, fence_len):
                fence_char = None
                prev_text = False
                prev_blank = False
                prev_code = False
            continue
        open_match = _FENCE_OPEN_RE.match(line)
        indent = len(line) - len(line.lstrip(" "))
        if open_match and indent <= 3:
            run = open_match.group(1)
            info = line[open_match.end():]
            if not (run[0] == "`" and "`" in info):
                excluded_lines.add(lineno)
                spans.append((line_start, line_end))
                fence_char = run[0]
                fence_len = len(run)
                prev_text = False
                prev_blank = False
                prev_code = False
                continue
        if not line.strip():
            prev_blank = True
            prev_text = False
            continue
        columns = _indent_columns(line[:len(line) - len(line.lstrip())])
        threshold = 4 + (list_stack[-1][1] if list_stack else 0)
        if (prev_blank or prev_code) and columns >= threshold:
            excluded_lines.add(lineno)
            spans.append((line_start, line_end))
            prev_code = True
            prev_text = False
            continue
        prev_code = False
        if prev_text and _SETEXT_RE.match(line):
            excluded_lines.add(lineno)
            spans.append((line_start, line_end))
            prev_text = False
            continue
        if _THEMATIC_RE.match(line):
            excluded_lines.add(lineno)
            spans.append((line_start, line_end))
            prev_text = False
            continue
        if "|" in line and _DELIM_ROW_RE.match(line):
            excluded_lines.add(lineno)
            spans.append((line_start, line_end))
            prev_text = False
            continue
        marker = _LIST_MARKER_RE.match(line)
        if marker:
            marker_col = _indent_columns(marker.group(1))
            content_col = marker_col + len(marker.group(2)) + (
                1 if marker.group(3) == " " else 0)
            while list_stack and list_stack[-1][0] >= marker_col:
                list_stack.pop()
            list_stack.append((marker_col, content_col))
            prev_text = True
            prev_blank = False
            continue
        while list_stack and list_stack[-1][0] >= columns:
            list_stack.pop()
        prev_text = True
        prev_blank = False
        spans.extend(_inline_excluded_spans(line, line_start))
    return spans, excluded_lines


def excluded_char_spans(text):
    return scan_excluded(text)[0]


def excluded_line_numbers(text):
    return scan_excluded(text)[1]


def span_excluded(text, start, end):
    """True when [start, end) overlaps any excluded region."""
    for span_start, span_end in excluded_char_spans(text):
        if span_start < end and start < span_end:
            return True
    return False


def line_fully_excluded(text, line_no):
    """True when every character of the 1-based line's content lies in an
    excluded region (blank lines are never excluded)."""
    lines = text.splitlines()
    if line_no < 1 or line_no > len(lines):
        return False
    line = lines[line_no - 1]
    if not line.strip():
        return False
    start = sum(len(l) + 1 for l in lines[:line_no - 1])
    end = start + len(line)
    covered_to = start
    for span_start, span_end in sorted(excluded_char_spans(text)):
        if span_start > covered_to:
            return False
        covered_to = max(covered_to, span_end)
        if covered_to >= end:
            return True
    return covered_to >= end


# ---------------------------------------------------------------------------
# Corrections verification (the legs)
# ---------------------------------------------------------------------------

_ANCHOR_COMMIT_LABELS = {
    "round_start_commit": "round-start commit",
    "round_close_commit": "round-close commit",
}


def verify_corrections(repo, artifact_path, family, round_number,
                       source_digest, rows, current_bytes=None,
                       certified_range=None, head="HEAD", classify=None,
                       witness_path=None, slug=None, seal_repo=None,
                       record_declared=False):
    """Run every verification leg over a declared corrections record.
    Returns (True, success message) or (False, prefixed refusal reason).
    Plan family: per-hop bytes are plan blobs at evidence commits, hop 0
    the seal's round-start blob, the terminal leg the current bytes. Code
    family: per-hop bytes are regenerated three-dot diffs over the row's
    refs, the first hop's before refs equal the seal's certified range,
    and the terminal leg is the branch head."""
    try:
        for row in rows:
            validate_row(row, family)
    except CorrectionsSchemaError as exc:
        return False, str(exc)
    srepo = seal_repo if seal_repo is not None else repo
    try:
        rel = seal_relpath(artifact_path, slug)
    except CorrectionsSchemaError as exc:
        return False, str(exc)
    entry = load_seal_entry(srepo, rel, round_number)
    if entry is None:
        return False, leg_reason(
            "anchor", "the seal file %s has no resolvable entry for round "
            "%d" % (rel, round_number))
    if entry.fields.get("artifact") != artifact_path:
        return False, leg_reason(
            "anchor", "the seal entry names artifact %r, not %r"
            % (entry.fields.get("artifact"), artifact_path))
    # Anchor: the entry's commits must be reachable and its bytes
    # re-derive to the round-start digest from git.
    for key in ("round_close_commit", "round_start_commit"):
        anchored = is_ancestor(srepo, entry.fields[key])
        if anchored is None:
            return False, leg_reason(
                "anchor", "git plumbing failed over %s"
                % entry.fields[key])
        if anchored is False:
            return False, leg_reason(
                "anchor", "the seal entry's %s is not an ancestor of HEAD"
                % _ANCHOR_COMMIT_LABELS[key])
    start_commit = entry.fields["round_start_commit"]
    if family == FAMILY_PLAN:
        start_bytes = blob_bytes(srepo, start_commit, artifact_path)
        if start_bytes is None:
            return False, leg_reason(
                "anchor", "the round-start blob for %s at %s is "
                "unresolvable" % (artifact_path, start_commit))
    else:
        base = entry.fields.get("reviewed_base")
        tip = entry.fields.get("reviewed_head")
        if not base or not tip:
            return False, leg_reason(
                "anchor", "the seal entry carries no certified range")
        start_bytes = diff_bytes(srepo, base, tip)
        if start_bytes is None:
            return False, leg_reason(
                "anchor", "the round-start diff %s...%s is unresolvable"
                % (base, tip))
    if sha256_hex(start_bytes) != entry.fields["round_start_digest"]:
        return False, leg_reason(
            "anchor", "the round-start bytes do not re-hash to the seal "
                      "entry's round-start digest")
    # Seal-integrity dating (r1 fold): an honest round's round-start
    # commit never postdates its round-close commit (honest rounds always
    # start at or before close). A consistent move of the latest round's
    # entry re-points round_start_commit at a later commit carrying the
    # attacker's bytes and re-declares the moved digest, re-binding
    # arbitrary semantic edits through the zero-hop arm; the ordering
    # violation refuses naming the seal leg before any digest is
    # accepted.
    start_date = commit_date(srepo, start_commit)
    close_date = commit_date(srepo, entry.fields["round_close_commit"])
    if start_date is None or close_date is None:
        return False, leg_reason(
            "seal", "git plumbing failed over seal commit dates")
    if start_date > close_date:
        return False, leg_reason(
            "seal", "the round-start commit postdates the round-close "
                    "commit: the seal entry's anchors were moved")
    if family == FAMILY_CODE and certified_range is not None:
        sealed = (entry.fields.get("reviewed_base"),
                  entry.fields.get("reviewed_head"))
        declared = (certified_range.get("base"),
                    certified_range.get("head"))
        if sealed != declared:
            return False, leg_reason(
                "seal", "the sidecar range %s differs from the seal's "
                "certified range %s" % (declared, sealed))
    if not rows:
        if record_declared:
            return False, leg_reason(
                "vacuous", "a declared corrections record carries zero "
                "hops")
        if source_digest == entry.fields["round_start_digest"]:
            return True, ("%schain verified: zero hops, the declared "
                          "digest equals the round %d round-start digest"
                          % (MARKER_PREFIX, round_number))
        return False, leg_reason(
            "anchor", "bare rewrite: the declared digest matches neither "
                      "the round-start digest nor a verifying chain")
    # Per-hop legs: declared linkage, evidence validity and dating, then
    # the digest binding to bytes re-derived from git.
    hop_bytes = start_bytes
    prev_row = None
    history = [(start_bytes, start_bytes)]
    for index, row in enumerate(rows):
        if prev_row is not None and \
                row["before_digest"] != prev_row["after_digest"]:
            return False, leg_reason(
                "linkage", "row %d declares a before digest differing "
                "from row %d's after digest" % (index, index - 1))
        if family == FAMILY_PLAN:
            evidence = row["evidence_commit"]
            if not HEX40_RE.match(evidence) or \
                    resolve_commit(repo, evidence) is None:
                return False, leg_reason(
                    "binding", "evidence commit %s is unresolvable"
                    % evidence)
            ancestor = is_ancestor(repo, evidence)
            if ancestor is None:
                return False, leg_reason(
                    "binding", "git plumbing failed over evidence commit "
                               "%s" % evidence)
            if ancestor is False:
                return False, leg_reason(
                    "binding", "evidence commit %s is not an ancestor of "
                               "HEAD" % evidence)
            touched = touches_path(repo, evidence, artifact_path)
            if touched is None:
                return False, leg_reason(
                    "binding", "git plumbing failed over evidence commit "
                               "%s" % evidence)
            if not touched:
                return False, leg_reason(
                    "binding", "evidence commit %s does not commit the "
                               "artifact path %s"
                               % (evidence, artifact_path))
        else:
            if prev_row is None:
                before = (row["before_base"], row["before_head"])
                sealed = (entry.fields.get("reviewed_base"),
                          entry.fields.get("reviewed_head"))
                if before != sealed:
                    return False, leg_reason(
                        "seal", "row 0's before refs %s differ from the "
                                "seal's certified range %s"
                                % (before, sealed))
            else:
                if row["before_base"] != prev_row["after_head"]:
                    return False, leg_reason(
                        "linkage", "row %d's after base is not the "
                                   "previous row's after head" % index)
            if resolve_commit(repo, row["before_head"]) is None or \
                    resolve_commit(repo, row["after_head"]) is None:
                return False, leg_reason(
                    "binding", "row %d names an unresolvable ref" % index)
            chained = is_ancestor(repo, row["after_base"],
                                  row["after_head"])
            if chained is None:
                return False, leg_reason(
                    "binding", "git plumbing failed over row %d refs"
                               % index)
            if chained is False:
                return False, leg_reason(
                    "linkage", "row %d's after head does not descend "
                               "from its after base" % index)
        evidence_ref = (row["evidence_commit"] if family == FAMILY_PLAN
                        else row["after_head"])
        evidence_date = commit_date(repo, evidence_ref)
        if evidence_date is None:
            return False, leg_reason(
                "seal", "git plumbing failed over hop commit dates")
        if evidence_date < close_date:
            return False, leg_reason(
                "seal", "hop commit dated before the seal entry's "
                        "round-close commit")
        if sha256_hex(hop_bytes) != row["before_digest"]:
            return False, leg_reason(
                "binding", "declared before digest does not match the "
                           "bytes re-derived from %s"
                           % ("the seal round-start blob" if index == 0
                              else "the previous hop's evidence"))
        if family == FAMILY_PLAN:
            after_bytes = blob_bytes(repo, row["evidence_commit"],
                                     artifact_path)
            if after_bytes is None:
                return False, leg_reason(
                    "binding", "the plan blob at evidence commit %s is "
                               "unresolvable" % row["evidence_commit"])
        else:
            after_bytes = diff_bytes(repo, row["after_base"],
                                     row["after_head"])
            if after_bytes is None:
                return False, leg_reason(
                    "binding", "the diff %s...%s is unresolvable"
                               % (row["after_base"], row["after_head"]))
        if sha256_hex(after_bytes) != row["after_digest"]:
            return False, leg_reason(
                "binding", "declared after digest does not match the "
                           "bytes re-derived at this hop's evidence")
        hop_bytes = after_bytes
        history.append((history[-1][1], after_bytes))
        prev_row = row
    # Terminal leg.
    if family == FAMILY_PLAN:
        if current_bytes is None:
            return False, leg_reason(
                "terminal", "no current bytes were provided")
        if sha256_hex(current_bytes) != rows[-1]["after_digest"]:
            return False, leg_reason(
                "terminal", "the chain's last after digest does not match "
                            "the current bytes")
    else:
        head_commit = resolve_commit(repo, head)
        if head_commit is None:
            return False, leg_reason(
                "terminal", "the branch head %s is unresolvable" % head)
        if head_commit != rows[-1]["after_head"]:
            return False, leg_reason(
                "terminal", "the chain's last after head is not the "
                            "branch head")
    # The declared digest is accepted from the round-start digest or from
    # a verified chain's terminal; anything else is a bare rewrite.
    terminal_digest = rows[-1]["after_digest"]
    if source_digest not in (entry.fields["round_start_digest"],
                             terminal_digest):
        return False, leg_reason(
            "anchor", "bare rewrite: the declared digest matches neither "
                      "the round-start digest nor a verifying chain")
    # Ack receipts resolve out of band against the injected witness path.
    for index, row in enumerate(rows):
        if row["kind"] != KIND_OPERATOR_ACKED:
            continue
        if witness_path is None:
            return False, leg_reason(
                "receipt", "unresolvable witness: no witness record path "
                           "was provided")
        resolved, message = resolve_ack_receipt(row, witness_path, repo,
                                                artifact_path)
        if not resolved:
            return False, message
    # Classification hook: the caller re-runs its own classifier over the
    # re-derived bytes; a non-exempt verdict refuses the leg.
    if classify is not None:
        for index, (old_bytes, new_bytes) in enumerate(history[1:]):
            unclassified = classify(old_bytes, new_bytes)
            if unclassified:
                return False, leg_reason(
                    "classify", "hunk(s) not exempt at hop %d: %s"
                                % (index, unclassified[0]))
    return True, "%schain verified: %d hop(s) anchored at round %d via " \
                 "seal %s" % (MARKER_PREFIX, len(rows), round_number, rel)


# ---------------------------------------------------------------------------
# Hermetic scratch-repo fixture builder
# ---------------------------------------------------------------------------


class ScratchRepo:
    """A throwaway git repo for selftests: TemporaryDirectory with
    addCleanup teardown, the GIT_* family dropped, config parked on
    /dev/null, per-repo identity, and explicitly pinned author and
    committer dates on every commit."""

    def __init__(self, test_case, name="repo"):
        self.temp_directory = tempfile.TemporaryDirectory(
            prefix="corrections-record-scratch-")
        test_case.addCleanup(self.temp_directory.cleanup)
        self.root = Path(self.temp_directory.name) / name
        self.root.mkdir(parents=True)
        self._clock = 1700000000
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "fixture")

    def git(self, *args, check=True, date=None):
        env = hermetic_git_env()
        if date is not None:
            env["GIT_AUTHOR_DATE"] = "@%d +0000" % date
            env["GIT_COMMITTER_DATE"] = "@%d +0000" % date
        proc = subprocess.run(
            ["git", "-C", str(self.root)] + list(args),
            capture_output=True, text=True, env=env)
        if check and proc.returncode != 0:
            raise AssertionError((args, proc.returncode, proc.stderr))
        return proc

    def next_date(self):
        self._clock += 60
        return self._clock

    def write_file(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes)
                         else content.encode("utf-8"))

    def commit_all(self, message, date=None, allow_empty=False):
        stamp = date if date is not None else self.next_date()
        self.git("add", "-A")
        args = ["commit", "-q", "-m", message]
        if allow_empty:
            args.append("--allow-empty")
        self.git(*args, date=stamp)
        return self.head()

    def commit_file(self, rel, content, message, date=None):
        self.write_file(rel, content)
        return self.commit_all(message, date=date)

    def commit_allow_empty(self, message, date=None):
        return self.commit_all(message, date=date, allow_empty=True)

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def _seal_entry_block(self, round_number, artifact_rel, start_commit,
                          start_digest, close_commit, reviewed=None):
        lines = [
            "## round %d" % round_number,
            "artifact: %s" % artifact_rel,
            "round_start_commit: %s" % start_commit,
            "round_start_digest: %s" % start_digest,
            "round_close_commit: %s" % close_commit,
        ]
        if reviewed is not None:
            base, tip, digest = reviewed
            lines.append("reviewed_base: %s" % base)
            lines.append("reviewed_head: %s" % tip)
            lines.append("range_digest: %s" % digest)
        return "\n".join(lines)

    def append_seal_entry(self, slug, round_number, artifact_rel,
                          start_commit, start_digest, close_commit,
                          reviewed=None, date=None, message=None):
        rel = seal_relpath(artifact_rel, slug)
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        block = self._seal_entry_block(round_number, artifact_rel,
                                       start_commit, start_digest,
                                       close_commit, reviewed)
        text = path.read_text() if path.exists() else ""
        path.write_text(text + ("\n\n" if text else "") + block + "\n")
        return self.commit_all(
            message or ("seal: round %d" % round_number), date=date)

    def write_seal_entry(self, slug, round_number, artifact_rel,
                         start_commit, start_digest, close_commit,
                         reviewed=None, date=None, message=None):
        rel = seal_relpath(artifact_rel, slug)
        block = self._seal_entry_block(round_number, artifact_rel,
                                       start_commit, start_digest,
                                       close_commit, reviewed)
        self.write_file(rel, block + "\n")
        return self.commit_all(
            message or ("seal: round %d" % round_number), date=date)


def build_scratch_repo(test_case, name="repo"):
    return ScratchRepo(test_case, name)
