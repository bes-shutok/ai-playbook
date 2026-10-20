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
operator ack receipt whose witness record path is injected by the caller
(code-family rows keep that turn-record resolution); the canonical
correction-row digest (lowercase SHA-256 over the row's canonical JSON,
excluding only receipt.authorization_witness); the plan-family
primary-state authorization route (the receipt names the fixed
scheduler-state selector and the verifier matches the unique
correction_authorizations entry from the already-resolved primary
checkout, a fully verified authorization letting that hop bypass only
the classification leg; the injected turn-record route is retired for
plan-family rows and refuses through the named receipt legs); the
acknowledgment writer (``record_correction_authorization``, the
production distinct-session append into the primary state file's
``correction_authorizations`` array under the scheduler-turn targeted
edit class, deriving its writer identity from the shared
session-channel helper and confirming the append by read-back); the
optional author_session_id row key
(operator-acked plan-family rows only, absent-tolerated on legacy rows);
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
import sys
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

# The operator-acked plan-family route: the receipt names this fixed
# selector, and the verifier reads the named array from the primary
# checkout's scheduler state file (the already-resolved primary-checkout
# path is injected by the caller; a caller-selected witness path never
# selects authority for plan-family rows).
SCHEDULER_STATE_RELPATH = ".ai-playbook/scheduler-state.json"
CORRECTION_AUTHORIZATIONS_KEY = "correction_authorizations"
ACK_STATE_SELECTOR = "%s#%s" % (SCHEDULER_STATE_RELPATH,
                                CORRECTION_AUTHORIZATIONS_KEY)
# One correction_authorizations entry: the row digest plus the copied
# row subject (audit readability); a copied field contradicting the
# matched row refuses.
AUTHORIZATION_ENTRY_KEYS = frozenset(
    ("row_digest", "writer_session_id", "operator_direction", "recorded_at",
     "author_session_id", "artifact_path", "before_digest", "after_digest",
     "evidence_commit", "hunk_digests"))
# The emitting session identity recorded on operator-acked plan-family
# rows only; absent on legacy rows and on every other kind or family.
AUTHOR_SESSION_KEY = "author_session_id"

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")

SEAL_DIR_RELPATH = ".ai-playbook/review-certs"
SEAL_ROUND_RE = re.compile(r"^## round (\d+)$")
SEAL_FIELD_RE = re.compile(r"^([a-z_]+): (.*)$")
LANDED_ANCHOR_SCAN_LIMIT = 400
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
    # Operator-acked plan-family rows may carry the emitting session's
    # author_session_id (absent-tolerated, so every archived row recorded
    # before the key existed re-validates unchanged); no other kind or
    # family ever carries it.
    optional = frozenset((AUTHOR_SESSION_KEY,)) \
        if kind == KIND_OPERATOR_ACKED and fam == FAMILY_PLAN \
        else frozenset()
    missing = sorted(expected - actual)
    extra = sorted(actual - expected - optional)
    if missing:
        return _schema("missing required key(s) %s for kind %s family %s"
                       % (missing, kind, fam))
    if extra:
        return _schema("unexpected key(s) %s" % extra)
    if optional and AUTHOR_SESSION_KEY in actual:
        value = row[AUTHOR_SESSION_KEY]
        if not isinstance(value, str) or not value.strip():
            return _schema("author_session_id is not a non-empty string")
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


def correction_row_digest(row):
    """The correction row identity: the lowercase SHA-256 of the
    canonical JSON encoding (sorted keys, compact separators) of the
    full correction row, excluding only ``receipt.authorization_witness``
    so the fixed selector does not create a cycle."""
    payload = dict(row)
    receipt = payload.get("receipt")
    if isinstance(receipt, dict):
        trimmed = dict(receipt)
        trimmed.pop("authorization_witness", None)
        payload["receipt"] = trimmed
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_hex(canonical.encode("utf-8"))


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


def commit_object_status(repo, object_id):
    """'present' only for a commit object, 'missing' only for a
    conclusive absent-object result, and 'error' otherwise (malformed
    ids, wrong object types, or any other Git failure). An ambiguous or
    otherwise inconclusive plumbing error never converts to 'missing'."""
    if not isinstance(object_id, str) or not HEX40_RE.match(object_id):
        return "error"
    exists = run_git(repo, "cat-file", "-e", object_id)
    if exists.returncode == 1:
        return "missing"
    if exists.returncode != 0:
        return "error"
    kind = git_text(repo, "cat-file", "-t", object_id)
    if kind is None:
        return "error"
    return "present" if kind.strip() == "commit" else "error"


def tree_blob_bytes(repo, commit, path):
    """(bytes, None) when the commit's tree carries a blob at path,
    (None, None) when the path is absent from that tree (a non-match),
    and (None, reason) on any git plumbing failure over the ls-tree or
    the blob read."""
    listing = git_text(repo, "ls-tree", commit, "--", path)
    if listing is None:
        return None, ("git plumbing failed while reading the tree of %s"
                      % commit)
    if not listing.strip():
        return None, None
    blob = git_bytes(repo, "cat-file", "blob", "%s:%s" % (commit, path))
    if blob is None:
        return None, ("git plumbing failed while reading the blob %s:%s"
                      % (commit, path))
    return blob, None


def resolve_landed_anchor(repo, artifact_path, digest, head_sha,
                          limit=LANDED_ANCHOR_SCAN_LIMIT):
    """Return (anchor, scan_error) using the caller's pinned HEAD id."""
    text = git_text(repo, "rev-list", "--first-parent", "-n", str(limit),
                    head_sha)
    if text is None:
        return None, "git plumbing failed while enumerating first-parent history"
    for commit in text.split():
        candidate, read_error = tree_blob_bytes(repo, commit, artifact_path)
        if read_error is not None:
            return None, read_error
        if candidate is not None and sha256_hex(candidate) == digest:
            return commit, None
    return None, None


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


def seal_text(repo, rel):
    """The seal bytes on disk under the repo root, or None when the file
    is absent or unreadable (the seal is read from the working tree,
    never from git)."""
    try:
        return (Path(repo) / rel).read_text(encoding="utf-8")
    except OSError:
        return None


# Legacy one-line seal rows: the exact prose shapes present in the
# committed seal corpus (the pipe rows carrying ``round-start commit`` /
# ``round-start ... digest`` labels and the dash-prefixed ``rN <date>
# <path> round-start ... round-start-digest ... round-close ...`` rows),
# recognized by an anchored grammar and normalized into the same entry
# model as block records. A row-shaped line whose labeled fields do not
# all extract stays prose (the round lookup then reports the seal
# unresolvable), never a partially filled entry.
_LEGACY_ROW_RE = re.compile(r"^(?:- )?r(\d+) (.+)$")
_LEGACY_ARTIFACT_RE = re.compile(r"\bartifact (\S+)")
_LEGACY_PATH_RE = re.compile(r"(?:^| )(\S+/\S+)")
_LEGACY_START_COMMIT_A_RE = re.compile(r"\bround-start commit ([0-9a-f]+)")
_LEGACY_START_PAIR_B_RE = re.compile(
    r"\bround-start ([0-9a-f]+) digest ([0-9a-f]+)\b")
_LEGACY_START_PAIR_C_RE = re.compile(
    r"\bround-start ([0-9a-f]+) round-start-digest ([0-9a-f]+)")
_LEGACY_START_DIGEST_A_RE = re.compile(r"\bround-start digest ([0-9a-f]+)\b")
_LEGACY_START_DIGEST_C_RE = re.compile(
    r"\bround-start-digest ([0-9a-f]+)\b")
_LEGACY_CLOSE_COMMIT_A_RE = re.compile(r"\bround-close commit ([0-9a-f]+)")
_LEGACY_CLOSE_COMMIT_B_RE = re.compile(r"\bround-close ([0-9a-f]+)\b")


def _legacy_row_entry(line):
    """One recognized legacy one-line seal row as a SealEntry, or None for
    every other line. The grammar extracts exactly the canonical fields;
    a row missing any of them is not an entry."""
    match = _LEGACY_ROW_RE.match(line)
    if match is None:
        return None
    body = match.group(2)
    artifact_match = _LEGACY_ARTIFACT_RE.search(body)
    artifact = artifact_match.group(1) if artifact_match else None
    if artifact is None:
        path_match = _LEGACY_PATH_RE.search(body)
        artifact = path_match.group(1) if path_match else None
    if artifact is None:
        return None
    pair_b = _LEGACY_START_PAIR_B_RE.search(body)
    pair_c = _LEGACY_START_PAIR_C_RE.search(body)
    start_a = _LEGACY_START_COMMIT_A_RE.search(body)
    if start_a is not None:
        start_commit = start_a.group(1)
    elif pair_b is not None:
        start_commit = pair_b.group(1)
    elif pair_c is not None:
        start_commit = pair_c.group(1)
    else:
        return None
    digest_a = _LEGACY_START_DIGEST_A_RE.search(body)
    if digest_a is not None:
        start_digest = digest_a.group(1)
    elif pair_b is not None:
        start_digest = pair_b.group(2)
    elif pair_c is not None:
        start_digest = pair_c.group(2)
    else:
        return None
    close_a = _LEGACY_CLOSE_COMMIT_A_RE.search(body)
    if close_a is not None:
        close_commit = close_a.group(1)
    else:
        close_b = _LEGACY_CLOSE_COMMIT_B_RE.search(body)
        close_commit = close_b.group(1) if close_b else None
    if close_commit is None:
        return None
    fields = {
        "artifact": artifact,
        "round_start_commit": start_commit,
        "round_start_digest": start_digest,
        "round_close_commit": close_commit,
    }
    return SealEntry(int(match.group(1)), fields, line)


def parse_seal(text):
    """The seal entries in file order. A malformed header or field line
    yields an unparsable marker consumed by the caller as an unresolvable
    seal. A legacy one-line seal row outside any block (the committed
    corpus's prose shape) normalizes to an entry when its labeled fields
    all extract; row-shaped prose that does not parse stays skipped."""
    entries = []
    current = None
    for line in text.splitlines():
        header = SEAL_ROUND_RE.match(line)
        if header:
            current = (int(header.group(1)), [])
            entries.append(current)
            continue
        if current is None:
            legacy = _legacy_row_entry(line)
            if legacy is not None:
                entries.append(legacy)
            continue
        field = SEAL_FIELD_RE.match(line)
        if field:
            current[1].append((field.group(1), field.group(2)))
        elif line.strip():
            return None
    parsed = []
    for item in entries:
        if isinstance(item, SealEntry):
            parsed.append(item)
            continue
        number, lines = item
        parsed.append(SealEntry(number, dict(lines),
                                "\n".join(["## round %d" % number]
                                          + ["%s: %s" % kv
                                             for kv in lines])))
    return parsed


def load_seal_entry(repo, rel, round_number, family=FAMILY_PLAN):
    """The single seal entry for the round and family, or None when the
    seal is unresolvable (missing file, unparsable text, zero or multiple
    family matches, or a failing field shape). Plan-family entries select
    by the numeric round header with no family field or ``family: plan``;
    code-family entries select by ``family: code`` plus ``staging_round:
    rN`` and never by the block number alone, so plan and code entries
    sharing a staging number coexist and duplicates refuse. The seal is
    read from the working tree, never from git."""
    text = seal_text(repo, rel)
    if text is None:
        return None
    entries = parse_seal(text)
    if entries is None:
        return None
    if family == FAMILY_CODE:
        token = "r%d" % round_number
        matching = [e for e in entries
                    if e.fields.get("family") == FAMILY_CODE
                    and e.fields.get("staging_round") == token]
    else:
        matching = [e for e in entries
                    if e.round == round_number
                    and e.fields.get("family", FAMILY_PLAN) == FAMILY_PLAN]
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


def _classifier_gap_reason(receipt, repo_root, hunks):
    """The prefixed receipt-leg refusal for the receipt's classifier-gap
    row (outside the backlog directory, dangling, or not quoting a
    refused hunk digest), or None when the committed gap row preserves
    the unclassified-hunk evidence."""
    gap_rel = receipt["classifier_gap_row"]
    gap_norm = os.path.normpath(gap_rel).replace(os.sep, "/")
    if gap_norm.startswith("../") or not gap_norm.startswith(
            BACKLOG_DIR_RELPATH + "/"):
        return leg_reason(
            "receipt", "classifier gap row %s is outside %s/"
            % (gap_rel, BACKLOG_DIR_RELPATH))
    gap_path = Path(repo_root) / gap_rel
    if not gap_path.is_file():
        return leg_reason(
            "receipt", "dangling classifier gap row path: %s" % gap_rel)
    gap_text = gap_path.read_text(encoding="utf-8", errors="replace")
    for hunk in hunks:
        if hunk["digest"] not in gap_text:
            return leg_reason(
                "receipt", "classifier gap row does not quote refused hunk "
                "digest %s" % hunk["digest"])
    return None


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
    reason = _classifier_gap_reason(receipt, repo_root, row["hunks"])
    if reason is not None:
        return False, reason
    return True, "receipt resolved against %s" % witness_path


# ---------------------------------------------------------------------------
# Correction authorizations (the plan-family primary-state witness)
# ---------------------------------------------------------------------------


def load_correction_authorizations(primary_checkout):
    """(entries, None) with entries the primary state file's
    correction_authorizations array (an absent member reads as empty), or
    (None, prefixed receipt-leg refusal) when the scheduler state file is
    absent or unreadable, not decodable JSON, not a JSON object, or the
    named member is not an array."""
    state_path = Path(primary_checkout) / SCHEDULER_STATE_RELPATH
    try:
        raw = state_path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        # OSError covers an absent path and an unreadable one; ValueError
        # covers invalid UTF-8 bytes (UnicodeDecodeError), refused as
        # malformed state, never an escaping crash.
        return None, leg_reason(
            "receipt", "unresolvable witness: the scheduler state file %s "
            "is absent or unreadable" % SCHEDULER_STATE_RELPATH)
    try:
        doc = json.loads(raw)
    except ValueError:
        return None, leg_reason(
            "receipt", "unresolvable witness: the scheduler state file %s "
            "is not decodable JSON" % SCHEDULER_STATE_RELPATH)
    if not isinstance(doc, dict):
        return None, leg_reason(
            "receipt", "unresolvable witness: the scheduler state file %s "
            "is not a JSON object" % SCHEDULER_STATE_RELPATH)
    entries = doc.get(CORRECTION_AUTHORIZATIONS_KEY)
    if entries is None:
        return [], None
    if not isinstance(entries, list):
        return None, leg_reason(
            "receipt", "malformed correction_authorizations: the %s member "
            "is not an array" % CORRECTION_AUTHORIZATIONS_KEY)
    return entries, None


def authorization_entry_reason(row, entry, artifact_path):
    """The prefixed receipt-leg refusal for a matched
    correction_authorizations entry that is malformed, whose copied
    subject contradicts the matched row, or whose writer session does
    not differ from the row's authoring session; None when the entry
    accepts. The exact row-digest match itself is the caller's
    (resolve_state_authorization selects the unique entry by
    correction_row_digest); this function never re-derives it."""
    author = row.get(AUTHOR_SESSION_KEY)
    if not isinstance(author, str) or not author.strip():
        # Without the row's own identity both writer-distinctness checks
        # would silently no-op, so the state route refuses; archived
        # legacy rows never reach this route.
        return leg_reason(
            "receipt", "unbound author session: the operator-acked "
            "plan-family row carries no nonempty author_session_id")
    if not isinstance(entry, dict):
        return leg_reason(
            "receipt", "malformed correction_authorizations entry: it is "
            "not a JSON object")
    missing = sorted(AUTHORIZATION_ENTRY_KEYS - set(entry))
    extra = sorted(set(entry) - AUTHORIZATION_ENTRY_KEYS)
    if missing:
        return leg_reason(
            "receipt", "malformed correction_authorizations entry: missing "
            "required key(s) %s" % missing)
    if extra:
        return leg_reason(
            "receipt", "malformed correction_authorizations entry: "
            "unexpected key(s) %s" % extra)
    reason = malformed_row_digest_reason([entry])
    if reason is not None:
        return reason
    for field in sorted(AUTHORIZATION_ENTRY_KEYS - {"hunk_digests"}):
        value = entry[field]
        if not isinstance(value, str) or not value.strip():
            return leg_reason(
                "receipt", "malformed correction_authorizations entry: %s "
                "is not a non-empty string" % field)
    digests = entry["hunk_digests"]
    if not isinstance(digests, list) or not digests or any(
            not isinstance(d, str) or not HEX64_RE.match(d)
            for d in digests):
        return leg_reason(
            "receipt", "malformed correction_authorizations entry: "
            "hunk_digests is not a non-empty ordered list of hex64 digests")
    if entry["writer_session_id"] == entry["author_session_id"]:
        return leg_reason(
            "receipt", "authorization written by the recording session: "
            "writer_session_id equals the entry's author_session_id %r"
            % entry["author_session_id"])
    if entry["writer_session_id"] == author:
        return leg_reason(
            "receipt", "authorization written by the recording session: "
            "writer_session_id equals the row's author_session_id %r"
            % author)
    copied = (
        (AUTHOR_SESSION_KEY, author),
        ("artifact_path", artifact_path),
        ("before_digest", row["before_digest"]),
        ("after_digest", row["after_digest"]),
        ("evidence_commit", row["evidence_commit"]),
        ("recorded_at", row["recorded_at"]),
    )
    for field, expected in copied:
        if expected is not None and entry[field] != expected:
            return leg_reason(
                "receipt", "subject mismatch: the entry's copied %s "
                "contradicts the matched row" % field)
    if digests != [h["digest"] for h in row["hunks"]]:
        return leg_reason(
            "receipt", "subject mismatch: the entry's copied hunk digests "
            "contradict the matched row's ordered hunk digests")
    if entry["operator_direction"] != row["receipt"]["directive"]:
        return leg_reason(
            "receipt", "subject mismatch: the entry operator_direction "
            "does not match the receipt directive")
    return None


def entries_matching_row_digest(entries, digest):
    """The shared by-digest selector over a correction_authorizations
    array: the verifier's unique-match leg and the acknowledgment
    writer's idempotent-append leg both select entries through this one
    match, so duplicate semantics cannot drift between reading and
    writing. A non-dict member is never a match here; shape refusals for
    such members belong to the malformed_row_digest_reason pre-scan, so
    they surface as malformed state, never a silent non-match."""
    return [e for e in entries
            if isinstance(e, dict) and e.get("row_digest") == digest]


def malformed_row_digest_reason(entries):
    """The prefixed malformed refusal when any array member is not a JSON
    object or any entry's row_digest fails the hex64 shape: a
    shape-malformed entry is malformed state, never a silent non-match
    (it would otherwise fall through to the missing-witness refusal and
    hide the broken witness)."""
    for entry in entries:
        if not isinstance(entry, dict):
            return leg_reason(
                "receipt", "malformed correction_authorizations entry: an "
                "array member is not a JSON object")
        value = entry.get("row_digest")
        if not isinstance(value, str) or not HEX64_RE.match(value):
            return leg_reason(
                "receipt", "malformed correction_authorizations entry: "
                "row_digest is not a hex64 digest")
    return None


def resolve_state_authorization(row, primary_checkout, repo_root,
                                artifact_path, witness_path=None):
    """Resolve an operator-acked plan-family row's receipt against the
    correction_authorizations array of the primary checkout's scheduler
    state file. The receipt must name the fixed selector; a caller-supplied
    witness path never selects authority. Returns (True, detail) or
    (False, prefixed ack-receipt reason)."""
    receipt = row["receipt"]
    named = receipt["authorization_witness"]
    if os.path.normpath(named) != os.path.normpath(ACK_STATE_SELECTOR):
        return False, leg_reason(
            "receipt", "unresolvable witness: the receipt names %r; "
            "plan-family authority is selected only by the fixed selector "
            "%r, never by a caller-selected path" % (named,
                                                     ACK_STATE_SELECTOR))
    if witness_path is not None:
        return False, leg_reason(
            "receipt", "unresolvable witness: a caller-selected witness "
            "path does not select authority for plan-family rows")
    entries, reason = load_correction_authorizations(primary_checkout)
    if reason is not None:
        return False, reason
    reason = malformed_row_digest_reason(entries)
    if reason is not None:
        return False, reason
    digest = correction_row_digest(row)
    matches = entries_matching_row_digest(entries, digest)
    if not matches:
        return False, leg_reason(
            "receipt", "no correction_authorizations entry matches the row "
            "digest %s" % digest)
    if len(matches) > 1:
        return False, leg_reason(
            "receipt", "non-unique correction_authorizations match: %d "
            "entries share the row digest %s" % (len(matches), digest))
    reason = authorization_entry_reason(row, matches[0], artifact_path)
    if reason is not None:
        return False, reason
    reason = _classifier_gap_reason(receipt, repo_root, row["hunks"])
    if reason is not None:
        return False, reason
    return True, "authorization resolved from %s" % SCHEDULER_STATE_RELPATH


# ---------------------------------------------------------------------------
# Acknowledgment writer (the durable distinct-session record)
# ---------------------------------------------------------------------------


def session_identity():
    """The invoking session's identity from the shared session-channel
    helper, invoked as a subprocess per that helper's contract (it is
    the single source of the channel value; cores never import it). Any
    invocation failure reads as an empty identity, which every consumer
    refuses fail-closed: a broken helper never mints an identity."""
    helper = Path(__file__).resolve().parent / "session_channel.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(helper)],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout


def resolve_primary_checkout(repo):
    """The primary checkout root: the first entry of ``git worktree list
    --porcelain`` over the repo the caller passes (the same recipe every
    production consumer applies before handing this module the
    already-resolved path). Returns the path string, or None on a git
    plumbing failure or a malformed listing."""
    text = git_text(repo, "worktree", "list", "--porcelain")
    if text is None:
        return None
    for line in text.splitlines():
        if line.startswith("worktree "):
            return line[len("worktree "):].strip() or None
    return None


def record_correction_authorization(repo, row, operator_direction,
                                    artifact_path):
    """The production acknowledgment writer (the 2026-10-18
    corrections-chain-operator-ack plan, Task 3): append the durable
    correction_authorizations entry binding an operator-acked plan-family
    row's digest to a distinct later session after an explicit operator
    direction. The write is a targeted state edit under the existing
    scheduler-turn writer class: one member changes, the rest of the
    document rides through, and the edit goes through a temp file plus
    atomic replace with the one-retry drift guard.

    The writer session identity is derived internally from the shared
    session-channel helper and is never a caller argument; the write
    target is always the primary checkout's scheduler state file resolved
    through the first-entry worktree-list resolver over ``repo``, never a
    caller-supplied path or a worktree-local copy. Returns (True,
    detail) or (False, prefixed refusal). An exact repeated write is
    idempotent (one entry per row digest); a same-digest entry with a
    different writer identity or subject refuses as a conflicting
    duplicate. After the atomic replace the writer reads the state file
    back and confirms the appended digest, refusing with a named loss
    instead of reporting success; state loss stays fail-closed and
    requires a fresh operator direction."""
    try:
        validate_row(row, FAMILY_PLAN)
    except CorrectionsSchemaError as exc:
        return False, str(exc)
    if row["kind"] != KIND_OPERATOR_ACKED:
        return False, leg_reason(
            "append", "the acknowledgment writer records only an "
            "operator-acked plan-family row")
    author = row.get(AUTHOR_SESSION_KEY)
    if not isinstance(author, str) or not author.strip():
        return False, leg_reason(
            "append", "unbound author session: the operator-acked "
            "plan-family row carries no nonempty author_session_id")
    if not isinstance(operator_direction, str) or \
            not operator_direction.strip():
        return False, leg_reason(
            "append", "the operator direction is empty: the "
            "acknowledgment requires an explicit operator direction")
    if operator_direction != row["receipt"]["directive"]:
        return False, leg_reason(
            "append", "subject mismatch: the operator direction does not "
            "match the receipt directive")
    writer = session_identity()
    if not writer.strip():
        return False, leg_reason(
            "append", "unbound writer session: the writer session "
            "identity is empty (every supported session source is unset "
            "or empty); the acknowledgment is refused")
    if writer == author:
        return False, leg_reason(
            "append", "authorization written by the recording session: "
            "the writer session identity equals the row's "
            "author_session_id %r" % author)
    digest = correction_row_digest(row)
    # recorded_at is a copied subject field bound to the row (the
    # verifier refuses a copied timestamp contradicting the matched row),
    # so the entry carries the row's own stamp, never the writer's wall
    # clock; every copied field is byte-equal to the matched row.
    entry = {
        "row_digest": digest,
        "writer_session_id": writer,
        "operator_direction": operator_direction,
        "recorded_at": row["recorded_at"],
        "author_session_id": author,
        "artifact_path": artifact_path,
        "before_digest": row["before_digest"],
        "after_digest": row["after_digest"],
        "evidence_commit": row["evidence_commit"],
        "hunk_digests": [h["digest"] for h in row["hunks"]],
    }
    # The writer only writes entries the verifier accepts: the same
    # copied-subject and writer-distinctness legs run over the prepared
    # entry before any byte is touched.
    reason = authorization_entry_reason(row, entry, artifact_path)
    if reason is not None:
        return False, reason
    primary = resolve_primary_checkout(repo)
    if primary is None:
        return False, leg_reason(
            "append", "git plumbing failed while resolving the primary "
            "checkout; no state file was selected")
    state_path = Path(primary) / SCHEDULER_STATE_RELPATH
    for _attempt in range(2):
        try:
            raw = state_path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            return False, leg_reason(
                "receipt", "unresolvable witness: the scheduler state "
                "file %s is absent or unreadable" % SCHEDULER_STATE_RELPATH)
        try:
            doc = json.loads(raw)
        except ValueError:
            return False, leg_reason(
                "receipt", "unresolvable witness: the scheduler state "
                "file %s is not decodable JSON" % SCHEDULER_STATE_RELPATH)
        if not isinstance(doc, dict):
            return False, leg_reason(
                "receipt", "unresolvable witness: the scheduler state "
                "file %s is not a JSON object" % SCHEDULER_STATE_RELPATH)
        current = doc.get(CORRECTION_AUTHORIZATIONS_KEY)
        if current is None:
            current = []
        if not isinstance(current, list):
            return False, leg_reason(
                "receipt", "malformed correction_authorizations: the %s "
                "member is not an array" % CORRECTION_AUTHORIZATIONS_KEY)
        reason = malformed_row_digest_reason(current)
        if reason is not None:
            return False, reason
        existing = entries_matching_row_digest(current, digest)
        if len(existing) > 1:
            return False, leg_reason(
                "append", "non-unique correction_authorizations match: %d "
                "entries share the row digest %s" % (len(existing), digest))
        if len(existing) == 1:
            if existing[0] == entry:
                return True, "ack append idempotent: the authorization is " \
                             "already present for row digest %s; no second " \
                             "entry written" % digest
            return False, leg_reason(
                "append", "conflicting correction_authorizations "
                "duplicate: an entry already carries the row digest %s "
                "with a different writer identity or subject; exact "
                "repeats are idempotent, conflicts refuse" % digest)
        doc[CORRECTION_AUTHORIZATIONS_KEY] = current + [entry]
        written = json.dumps(doc, indent=2, sort_keys=True) + "\n"
        tmp_path = state_path.with_name(
            "%s.ack-tmp-%d" % (state_path.name, os.getpid()))
        try:
            tmp_path.write_text(written, encoding="utf-8")
            # Targeted-edit drift guard: re-read immediately before the
            # replace and retry once; the precondition re-evaluates on
            # the fresh bytes. The re-read refuses through the same
            # absent-or-unreadable leg as the pre-read: a concurrent
            # corrupt replace surfaces as a decode error (ValueError),
            # never an escaping crash.
            try:
                fresh = state_path.read_text(encoding="utf-8")
            except (OSError, ValueError):
                return False, leg_reason(
                    "receipt", "unresolvable witness: the scheduler state "
                    "file %s is absent or unreadable"
                    % SCHEDULER_STATE_RELPATH)
            if fresh == raw:
                os.replace(tmp_path, state_path)
                break
        except OSError as exc:
            return False, leg_reason(
                "append", "the scheduler state file is not writable: %s"
                % exc)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    else:
        return False, leg_reason(
            "append", "the scheduler state file drifted twice during the "
            "acknowledgment append; no write was performed")
    # Read-back: the append is only reported after the written file
    # carries the digest; a lost append is a named loss, never a silent
    # success, and requires a fresh operator direction.
    entries_after, reason = load_correction_authorizations(primary)
    if reason is not None or \
            not entries_matching_row_digest(entries_after or [], digest):
        return False, leg_reason(
            "append", "ack append lost: the appended row digest %s is "
            "absent from %s after the write; the acknowledgment is not "
            "recorded and requires a fresh operator direction"
            % (digest, SCHEDULER_STATE_RELPATH))
    return True, "authorization recorded: row digest %s appended to %s in " \
                 "the primary checkout" % (digest, SCHEDULER_STATE_RELPATH)


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
                       record_declared=False, primary_checkout=None):
    """Run every verification leg over a declared corrections record.
    Returns (True, success message) or (False, prefixed refusal reason).
    The ``head`` argument resolves once at entry into the verification
    snapshot id that every HEAD-dependent leg (the anchor checks, the
    plan-family evidence ancestry, the code-family terminal comparison,
    and the landed-anchor resolver scan) consumes; no callee resolves
    symbolic HEAD again.
    Plan family: per-hop bytes are plan blobs at evidence commits, hop 0
    the seal's round-start blob, the terminal leg the current bytes. Code
    family: per-hop bytes are regenerated three-dot diffs over the row's
    refs, the first hop's before refs equal the seal's certified range,
    and the terminal leg is the branch head. primary_checkout is the
    already-resolved primary checkout root: a plan-family operator-acked
    row resolves its receipt against the primary state file's
    correction_authorizations array through the receipt's fixed selector,
    and only a fully verified authorization lets that hop bypass the
    classification leg. Every production consumer resolves the primary
    checkout (the first `git worktree list --porcelain` entry) and passes
    it in; with primary_checkout None a plan-family acked row refuses
    through the named receipt legs (a caller-selected witness path never
    selects authority, and its absence stays the missing-witness
    refusal), so the legacy turn-record route is retired for the plan
    family. Code-family rows keep the injected witness_path resolution
    and the classify verdict."""
    try:
        for row in rows:
            validate_row(row, family)
    except CorrectionsSchemaError as exc:
        return False, str(exc)
    # Verifier snapshot contract: the supplied head resolves exactly once
    # here, and every HEAD-dependent leg below consumes this one local id;
    # no callee resolves symbolic HEAD again.
    head_sha = resolve_commit(repo, head)
    if head_sha is None:
        return False, leg_reason(
            "terminal", "the branch head %s is unresolvable" % head)
    srepo = seal_repo if seal_repo is not None else repo
    try:
        rel = seal_relpath(artifact_path, slug)
    except CorrectionsSchemaError as exc:
        return False, str(exc)
    entry = load_seal_entry(srepo, rel, round_number, family)
    if entry is None:
        return False, leg_reason(
            "anchor", "the seal file %s has no resolvable entry for round "
            "%d" % (rel, round_number))
    if entry.fields.get("artifact") != artifact_path:
        return False, leg_reason(
            "anchor", "the seal entry names artifact %r, not %r"
            % (entry.fields.get("artifact"), artifact_path))
    # Anchor: the entry's commits must be reachable and its bytes
    # re-derive to the round-start digest from git. A plan-family anchor
    # the squash landing orphaned resolves through the first-parent
    # ancestor whose plan blob carries the sealed bytes (byte identity,
    # never the recorded sha); a moved anchor without byte identity
    # still refuses.
    anchors = dict((key, entry.fields[key])
                   for key in ("round_close_commit", "round_start_commit"))
    landed_anchor = None
    for key in ("round_close_commit", "round_start_commit"):
        object_state = commit_object_status(srepo, anchors[key])
        if object_state == "error":
            return False, leg_reason("anchor", "Git cannot classify commit object %s" % anchors[key])
        if object_state == "missing":
            anchored = False
        else:
            anchored = is_ancestor(srepo, anchors[key], descendant=head_sha)
            if anchored is None:
                return False, leg_reason(
                    "anchor", "git plumbing failed over %s" % anchors[key])
        if anchored is False:
            if family == FAMILY_CODE:
                return False, leg_reason(
                    "anchor", "the seal entry's %s is not an ancestor of HEAD"
                    % _ANCHOR_COMMIT_LABELS[key])
            scan_error = None
            if landed_anchor is None and family == FAMILY_PLAN:
                landed_anchor, scan_error = resolve_landed_anchor(
                    srepo, artifact_path,
                    entry.fields["round_start_digest"], head_sha)
            if scan_error is not None:
                return False, leg_reason("anchor", scan_error)
            if landed_anchor is None:
                return False, leg_reason(
                    "anchor", "the seal entry's %s is not an ancestor of HEAD "
                    "and no first-parent ancestor carries the sealed "
                    "round-start bytes at %s"
                    % (_ANCHOR_COMMIT_LABELS[key], artifact_path))
            anchors[key] = landed_anchor
    start_commit = anchors["round_start_commit"]
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
    close_date = commit_date(srepo, anchors["round_close_commit"])
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
            verified = ("%schain verified: zero hops, the declared "
                        "digest equals the round %d round-start digest"
                        % (MARKER_PREFIX, round_number))
            if landed_anchor is not None:
                verified += ("; squash-orphaned seal anchors resolved "
                             "through HEAD-ancestor %s" % landed_anchor)
            return True, verified
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
            ancestor = is_ancestor(repo, evidence, descendant=head_sha)
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
        if head_sha != rows[-1]["after_head"]:
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
    # Ack receipts resolve out of band. A plan-family row resolves ONLY
    # through the primary state file's correction_authorizations array via
    # the receipt's fixed selector: every production consumer resolves the
    # primary checkout and passes it in (Task 2 of the 2026-10-18
    # corrections-chain plan), so the injected turn-record route is
    # retired for plan-family rows - a caller-selected witness path never
    # selects authority, and its absence stays the missing-witness
    # refusal. Only after every other leg has passed does a fully
    # verified state authorization mark its hop as classifier-bypassable
    # (kind-aware: the bypass never touches script-verified or code-family
    # rows, and code-family rows keep the injected turn-record
    # resolution).
    state_acked_hops = set()
    for index, row in enumerate(rows):
        if row["kind"] != KIND_OPERATOR_ACKED:
            continue
        if family == FAMILY_PLAN:
            if primary_checkout is not None:
                resolved, message = resolve_state_authorization(
                    row, primary_checkout, repo, artifact_path,
                    witness_path=witness_path)
                if not resolved:
                    return False, message
                state_acked_hops.add(index)
                continue
            if witness_path is not None:
                return False, leg_reason(
                    "receipt", "unresolvable witness: a caller-selected "
                               "witness path does not select authority for "
                               "plan-family rows")
            return False, leg_reason(
                "receipt", "unresolvable witness: no witness record path "
                           "was provided")
        if witness_path is None:
            return False, leg_reason(
                "receipt", "unresolvable witness: no witness record path "
                           "was provided")
        resolved, message = resolve_ack_receipt(row, witness_path, repo,
                                                artifact_path)
        if not resolved:
            return False, message
    # Classification hook: the caller re-runs its own classifier over the
    # re-derived bytes; a non-exempt verdict refuses the leg. A hop whose
    # operator-acked plan-family row just verified through the primary
    # state authorization is the only bypass.
    if classify is not None:
        for index, (old_bytes, new_bytes) in enumerate(history[1:]):
            if index in state_acked_hops:
                continue
            unclassified = classify(old_bytes, new_bytes)
            if unclassified:
                return False, leg_reason(
                    "classify", "hunk(s) not exempt at hop %d: %s"
                                % (index, unclassified[0]))
    verified = "%schain verified: %d hop(s) anchored at round %d via " \
               "seal %s" % (MARKER_PREFIX, len(rows), round_number, rel)
    if landed_anchor is not None:
        verified += ("; squash-orphaned seal anchors resolved through "
                     "HEAD-ancestor %s" % landed_anchor)
    return True, verified


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
            # The code-family producer's fields: family-aware seal lookup
            # selects the code entry by these, never the block number.
            lines.append("family: %s" % FAMILY_CODE)
            lines.append("staging_round: r%d" % round_number)
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
