#!/usr/bin/env python3
"""Document ownership registry validator (plans doc-ownership-lifecycle, Task 1).

Three subcommands plus a hermetic ``--selftest``:

- ``validate``: registry integrity. Required fields, duplicate identity,
  duplicate SOT declarations, successor cycles, alias target resolution,
  completed-history files missing registry entries, audit-note token
  format. Exit 0 with warnings when only warn-tier findings; exit 1 on
  any hard finding. A missing registry file fails OPEN (exit 0, single
  warn hint).
- ``check-writes``: gate a list of changed paths against immutable
  completed-history directories. Input channels: paths as argv, or one
  entry per line on stdin via ``--stdin`` (callers feed the union of
  working-tree and committed-since-session-start changes so non-ASCII
  paths compare correctly, e.g.
  ``git -c core.quotePath=false status --porcelain`` and
  ``git -c core.quotePath=false diff --name-status --no-renames``
  output). Each
  stdin line MAY carry a change-type prefix: either ``XY PATH``
  porcelain form (e.g. ``AM docs/plans/completed/x.md``; the
  leading-space worktree form `` M path`` parses the same way) or
  name-status form (``A<TAB>path``). Renames parse on the porcelain
  form ONLY (``R  old -> new``) and only when the porcelain status
  starts with ``R``: for every other status a `` -> `` sequence in the
  path text is filename data, and the whole rest of the line is the
  literal path (r6 F1; an ``M``/``??`` line naming an arrow-bearing
  file gates that full path, never a phantom split). For genuine
  renames BOTH sides are gated, the old side as
  a deletion-typed entry (a rename out of an immutable dir is the
  artifact leaving; HARD unless audit-noted) and the new side with the
  rename letter (licensed when it is a registered lifecycle src).
  Tab-form rename lines are rejected (usage exit 2): the one prescribed
  name-status feeder pins ``--no-renames``, so no caller emits them.
  A bare path line (no letter) still parses and keeps the legacy
  semantics at warn tier. Exit 1 naming each unprotected immutable
  path; exit 0 otherwise. A name-status line whose letter is not one
  of git's documented ``A/M/D/R/T/C`` letters is a usage-level parse
  error (exit 2), never a silent bare path; a backslash-bearing input
  path is likewise rejected (exit 2; git emits forward slashes only).
  Mirrors (``docs/history/context/confluence/``) and ephemera
  (``docs/history/reviews/``, ``docs/tmp/``) are exempt. Registered-src
  lifecycle exemption, bounded to the transition: a path whose
  normalized form equals the ``src`` of a row with ``state`` completed
  or superseded is licensed ONLY for a clean add or rename (porcelain
  staged column exactly ``A`` or ``R`` with a blank second column;
  name-status exactly ``A`` or ``R<digits>``; conflict statuses like
  ``AA``/``AU`` are NOT licensed). An untracked ``??`` on a registered
  lifecycle src is the freeze move arriving: warn tier with a
  stage-the-move hint, not a gate trip. The same src written with
  ``M``/``D`` or any other letter is a HARD unprotected write; a bare
  line (no letter) passes at warn tier with a verify duty. Unregistered
  paths and multiply-claimed srcs stay gated regardless of letter. An
  audit note in the registry row for the path is the corruption
  override; the note must be removed after the licensed write lands.
  The lifecycle exemption compares the UNFOLDED normalized path
  against the registry src's stored spelling (byte equality; r6 F2):
  a case-variant add of a registered src is not the licensed
  transition; on folding platforms it takes the warn-tier verify path
  naming the near-match. Audit-note defects found in the registry row
  scan are counted separately from write findings in the summary line
  (r6 F6). A missing registry file fails OPEN (warn, never exit 1).

Trust boundary (F5): the change-type letters and paths on stdin are
asserted by the feeding command and are only as trustworthy as that
command. The validator does NOT re-derive change types from git; a
caller (or actor) that relabels an ``M`` as an ``A`` defeats the
letter-bounded exemption. The letters bound the registered-src
exemption only; unregistered immutable paths stay gated regardless of
letter.
- ``inventory``: list completed-history files with no registry row; the
  migration backlog. Exit 0 except on hard parse errors; a malformed
  registry table (unknown header, shifted row) is a hard parse error in
  every subcommand. Only the
  FIRST Markdown table in the registry file is parsed; prose and any
  later tables after a non-table line are ignored. Escaped pipes
  (``\\|``) inside cells are unescaped, per Markdown table convention.

Fail-closed CLI: an unknown flag exits 2 with a usage error, never a
silent pass. The validator never auto-reclassifies anything; it only
reports.

Registry file format (Markdown table, one row per document identity):

    | identity | sot | state | archived | reason | src | successor | aliases | audit |

- ``identity``: stable kebab-case concept identifier (REQUIRED).
- ``sot``: ``yes`` when this row declares living-SOT ownership (REQUIRED
  semantics: use ``no`` when it does not).
- ``state``: ``living`` | ``completed`` | ``superseded`` (REQUIRED).
- ``archived``: freeze date (``YYYY-MM-DD`` or empty for living rows).
- ``reason``: why the freeze happened (free text, may be empty).
- ``src``: repo-relative path of the artifact this row registers.
- ``successor``: identity of the superseding document (``superseded_by``).
- ``aliases``: comma-separated repo-relative paths that historically
  pointed at this identity.
- ``audit``: free-text audit note; non-empty on a completed-history row
  is the explicit override that licenses an otherwise immutable write.
  A non-empty audit cell on a completed/superseded row must begin with
  the dated confirmation token ``user-approved YYYY-MM-DD:`` (the
  ADR-0001 user-confirmation precondition made checkable); the date must
  be a real calendar date not in the future (one-day clock skew
  tolerated: an approval legitimately minted today in a timezone ahead
  of the validator host passes near midnight; two or more days ahead
  fails). Both ``validate`` and ``check-writes`` report a HARD finding
  for a malformed note (a self-minted or ill-dated note licenses
  nothing).

Facts keys (read via ``scripts/facts_paths.py`` helpers from
``<root>/.ai-playbook/facts.md``, TOML-fence block; missing file or key
falls back to the default, so pre-registry repos fail open):

- ``plans_completed_dir`` (default ``docs/plans/completed/``)
- ``backlog_completed_dir`` (default ``docs/history/backlog/completed/``)
- ``doc_registry_rel`` (default ``docs/maintenance/document-registry.md``)

Immutable completed-history directories (write-gated):

- the resolved ``plans_completed_dir`` and ``backlog_completed_dir``
- ``docs/history/context/`` minus its ``confluence/`` mirror subtree
- ``docs/history/feature-notes/``

Stdlib only. Repo-relative paths only; no PII.
"""

from __future__ import annotations

import contextlib
import datetime
import io
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_PLANS_COMPLETED_DIR = "docs/plans/completed/"
DEFAULT_BACKLOG_COMPLETED_DIR = "docs/history/backlog/completed/"
DEFAULT_DOC_REGISTRY_REL = "docs/maintenance/document-registry.md"

CONTEXT_DIR = "docs/history/context/"
CONFLUENCE_MIRROR_DIR = "docs/history/context/confluence/"
FEATURE_NOTES_DIR = "docs/history/feature-notes/"
EPHEMERA_DIRS = ("docs/history/reviews/", "docs/tmp/")

REGISTRY_COLUMNS = [
    "identity", "sot", "state", "archived", "reason",
    "src", "successor", "aliases", "audit",
]

USAGE = (
    "usage: doc_registry_validator.py [--root PATH] {validate|check-writes|inventory}\n"
    "       doc_registry_validator.py check-writes [--stdin] [path ...]\n"
    "       doc_registry_validator.py --selftest\n"
)


# --------------------------------------------------------------------------- #
# Facts resolution (helpers from scripts/facts_paths.py where they fit).
# --------------------------------------------------------------------------- #

def _import_facts_paths():
    """Import the sibling facts_paths module when available (never fatal)."""
    here = Path(__file__).resolve().parent
    for candidate in (here,):
        module_path = candidate / "facts_paths.py"
        if module_path.is_file():
            sys.path.insert(0, str(candidate))
            try:
                import facts_paths  # noqa: F401  (peer leaf, stdlib-only)
                return facts_paths
            except ImportError:
                pass
    return None


def resolve_repo_relative_key(root: Path, key: str, default: str) -> str:
    """Resolve a repo-relative facts key anchored at ``root``.

    Uses ``facts_paths.resolve_toml_key_raw`` (raw value parser) when the
    sibling module is importable, so repo-relative values anchor at the
    root rather than the process CWD. Falls back to the default when the
    facts file, key, or module is absent.
    """
    facts_paths = _import_facts_paths()
    if facts_paths is not None:
        try:
            raw = facts_paths.resolve_toml_key_raw(root, key)
            if raw:
                return raw
        except Exception as exc:
            print("warn: facts key %s unresolved (%s); using default %s"
                  % (key, exc, default), file=sys.stderr)
    return default


def _is_root_escaping(p: str) -> bool:
    """True when a normalized posix path escapes the repo root."""
    return p == ".." or p.startswith("../")


def normalize_repo_path(path: str) -> str:
    """Normalize a path string (facts value or changed-path input) to a
    clean repo-relative posix path: strip surrounding whitespace and
    quotes (git C-quoted paths; a no-op for facts TOML values), strip a
    leading slash (absolute spellings resolve as repo-relative, never a
    crash), and collapse ``./`` prefixes and duplicate separators via
    ``posixpath.normpath`` (an un-normalized ``./``-prefixed dir would
    silently fail the immutability prefix match). Root-escaping results
    (``..`` components) return ``""``: they can never equal a
    repo-relative path, so gating on them would be dead code and walking
    them would leave the repo root (F8).
    """
    p = path.strip().strip('"')
    if not p:
        return ""
    if p.startswith("/"):
        p = p[1:]
    p = posixpath.normpath(p)
    if _is_root_escaping(p):
        return ""
    return p


def _fold(path: str) -> str:
    """Fold a repo-relative path for comparison so case-variant
    spellings gate identically on case-insensitive filesystems
    (darwin, windows); identity on case-sensitive ones (F6).

    ``os.path.normcase`` folds only on Windows, so darwin (whose
    default APFS/HFS+ volumes are case-insensitive) folds explicitly
    via ``str.lower``.
    """
    if sys.platform == "darwin":
        return path.lower()
    return os.path.normcase(path)


def resolve_config(root: Path) -> dict:
    """Resolve all directory/registry facts values anchored at ``root``.

    Root-escaping values (``..`` components) never match repo-relative
    paths and would silently disable a gate family, so they warn and
    fall back to the documented default (fail-open-with-hint, F8).
    """
    cfg = {}
    for key, default in (
        ("plans_completed_dir", DEFAULT_PLANS_COMPLETED_DIR),
        ("backlog_completed_dir", DEFAULT_BACKLOG_COMPLETED_DIR),
        ("doc_registry_rel", DEFAULT_DOC_REGISTRY_REL),
    ):
        raw = resolve_repo_relative_key(root, key, default)
        value = normalize_repo_path(raw)
        if raw.strip() and not value:
            print("warn: facts key %s value %r escapes the repo root;"
                  " using default %s" % (key, raw, default),
                  file=sys.stderr)
            value = normalize_repo_path(default)
        cfg[key] = value
    return cfg


def resolve_repo_root(explicit: str | None) -> Path:
    """Resolve the repo root: explicit flag, else git toplevel, else cwd."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return Path(out).resolve()
    except Exception:
        pass
    return Path.cwd().resolve()


# --------------------------------------------------------------------------- #
# Registry parsing.
# --------------------------------------------------------------------------- #

def registry_path(root: Path, cfg: dict) -> Path:
    return root / cfg["doc_registry_rel"]


# Fixture roots created by make_fixture; cleaned by cmd_selftest.
_FIXTURE_ROOTS: list[Path] = []


class RegistryParseError(Exception):
    """Malformed registry table (unknown header or shifted row)."""


def parse_registry(path: Path) -> list[dict] | None:
    """Parse the registry Markdown table; None when the file is absent.

    Returns a list of row dicts keyed by REGISTRY_COLUMNS. The header
    row must list exactly the expected columns in the documented order
    (strict equality; a reordered header is a parse error, not a
    silently accepted deviation); a renamed or unknown header raises
    RegistryParseError, as does a data row whose cell count differs
    from the column count (a shifted row would silently misassign
    every later cell) and a backslash-run of two or more before a pipe
    (ambiguous Markdown escaping; fail closed, F9).
    """
    if not path.is_file():
        return None
    rows: list[dict] = []
    col_order: list[str] | None = None
    for lineno, line in enumerate(path.read_text(encoding="utf-8")
                                  .splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if col_order is not None:
                # The first table ended at this non-table line; later
                # tables (notes, legends) are prose, not registry rows.
                break
            continue
        # Fail closed on backslash-runs of 2+ before a pipe: the
        # single-char lookbehind would treat the pipe as escaped, but
        # Markdown escape parity (even run = literal backslashes) makes
        # the intent ambiguous; a parse error beats silent misparse.
        if re.search(r"\\{2,}\|", stripped):
            raise RegistryParseError(
                "registry row at line %d contains a backslash-run of"
                " two or more before a pipe (ambiguous escaping)"
                % lineno)
        # Split on UNESCAPED pipes only; `\|` inside a cell is the
        # Markdown convention for a literal pipe, so unescape after.
        cells = [c.strip().replace("\\|", "|")
                 for c in re.split(r"(?<!\\)\|", stripped.strip("|"))]
        if col_order is None:
            # First table line is the header; strict equality with the
            # one documented column order.
            lowered = [c.lower() for c in cells]
            if lowered != REGISTRY_COLUMNS:
                raise RegistryParseError(
                    "registry header at line %d does not match the"
                    " expected columns %s (got %s)"
                    % (lineno, REGISTRY_COLUMNS, lowered))
            col_order = lowered
            continue
        if all(re.fullmatch(r":?-{1,}:?", c) for c in cells if cells):
            continue  # separator row (any GFM alignment form)
        if len(cells) != len(col_order):
            raise RegistryParseError(
                "registry row at line %d has %d cell(s), expected %d;"
                " omitted or extra cells shift every later column"
                % (lineno, len(cells), len(col_order)))
        row = {col: "" for col in REGISTRY_COLUMNS}
        for col, value in zip(col_order, cells):
            row[col] = value
        rows.append(row)
    return rows


def registered_src_paths(rows: list[dict]) -> set[str]:
    """All repo-relative src and alias paths claimed by registry rows
    (case-folded so case-variant spellings cannot bypass gates)."""
    claimed = set()
    for row in rows:
        src = row.get("src", "").strip()
        if src:
            claimed.add(_fold(normalize_repo_path(src)))
        for alias in split_aliases(row.get("aliases", "")):
            claimed.add(_fold(normalize_repo_path(alias)))
    return claimed


def split_aliases(raw: str) -> list[str]:
    return [a.strip() for a in raw.split(",") if a.strip()]


# --------------------------------------------------------------------------- #
# Path classification (immutable / exempt / ordinary).
# --------------------------------------------------------------------------- #

def is_exempt(path: str) -> bool:
    """Mirrors (confluence/) and ephemera (reviews/, tmp/) are exempt."""
    return (path == CONFLUENCE_MIRROR_DIR.rstrip("/")
            or path.startswith(CONFLUENCE_MIRROR_DIR)
            or any(path == d.rstrip("/") or path.startswith(d)
                   for d in EPHEMERA_DIRS))


def is_immutable(path: str, cfg: dict) -> bool:
    """True when the path is under a completed-history (immutable) dir.

    Both sides are case-folded first: on case-insensitive filesystems a
    write to a case-variant spelling lands in the immutable dir while
    byte-exact matching would classify it mutable (F6). On
    case-sensitive platforms the fold is identity.
    """
    if is_exempt(path):
        return False
    folded = _fold(path)
    immutable_dirs = [
        cfg["plans_completed_dir"],
        cfg["backlog_completed_dir"],
        CONTEXT_DIR,
        FEATURE_NOTES_DIR,
    ]
    for d in immutable_dirs:
        d = d if d.endswith("/") else d + "/"
        folded_dir = _fold(d)
        if folded == folded_dir.rstrip("/") or folded.startswith(folded_dir):
            return True
    return False


def completed_history_dirs(cfg: dict) -> list[str]:
    return [
        cfg["plans_completed_dir"],
        cfg["backlog_completed_dir"],
        CONTEXT_DIR,
        FEATURE_NOTES_DIR,
    ]


def list_completed_files(root: Path, cfg: dict) -> list[str]:
    """Repo-relative files under every completed-history dir that exists."""
    found: list[str] = []
    for d in completed_history_dirs(cfg):
        base = root / d
        if not base.is_dir():
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for name in filenames:
                full = Path(dirpath) / name
                rel = full.relative_to(root).as_posix()
                if not is_exempt(rel):
                    found.append(rel)
    return sorted(found)


# --------------------------------------------------------------------------- #
# Change-type line parsing (stdin channel).
# --------------------------------------------------------------------------- #

_PORCELAIN_STATUS_CHARS = set("ADMRUTCX?!.")
_NAME_STATUS_LETTER_RE = re.compile(r"[AMDRTC]\d*")
_AUDIT_TOKEN_RE = re.compile(r"user-approved \d{4}-\d{2}-\d{2}: \S")


class ChangeLineError(Exception):
    """Unparseable change-type line (usage-level, exit 2)."""


def is_licensed_transition(change_type: str) -> bool:
    """True only for a CLEAN add or rename (F3).

    Porcelain XY: the staged (first) column is exactly ``A`` or ``R``
    and the second column is blank (``A ``, ``R ``); conflict statuses
    (``AA``, ``AU``, ``AM``) are not licensed. Name-status: exactly
    ``A`` or ``R<digits>``. Everything else is not the transition.
    """
    if len(change_type) == 2:
        return change_type[0] in "AR" and change_type[1] == " "
    return bool(_NAME_STATUS_LETTER_RE.fullmatch(change_type)
                and change_type[0] in "AR")


def audit_note_valid(audit: str) -> bool:
    """A non-empty audit note on a completed/superseded row must begin
    with the dated confirmation token ``user-approved YYYY-MM-DD:``
    (ADR-0001 user-confirmation precondition; F6). The date must parse
    as a real calendar date (not month 99 / day 99) and must not be in
    the future (an approval cannot post-date today; r5 F7). One-day
    clock skew is tolerated (r6 F7): a legitimately-today approval
    minted in a timezone ahead of the validator host passes near
    midnight; two or more days ahead still fails."""
    if not _AUDIT_TOKEN_RE.match(audit):
        return False
    date_str = audit[len("user-approved "):].split(":", 1)[0]
    try:
        approved = datetime.date.fromisoformat(date_str)
    except ValueError:
        return False
    return approved <= datetime.date.today() + datetime.timedelta(days=1)


def parse_change_line(line: str) -> list[tuple[str, str | None]]:
    """Parse one stdin line into a list of ``(path, change_type)``
    entries (renames yield two: old side then new side).

    Classification happens on the RAW line (only the newline is
    stripped; F1): leading whitespace is status-column data
    (`` M path``), never decoration. Accepted forms:

    - Porcelain ``XY PATH`` (``len >= 3``, first two chars a valid XY
      pair with at most one blank, third char a space): status
      ``s[:2]``, path ``s[3:]``. Rename semantics apply ONLY when the
      porcelain status starts with ``R`` (r6 F1): a porcelain rename
      ``R  old -> new`` yields the old side typed ``D`` (the artifact
      is leaving; gated exactly like a deletion) and the new side with
      ``s[:2]``. For any other status a `` -> `` sequence is filename
      data: the whole rest is the literal path, never a split.
    - Name-status ``L<TAB>path`` with ``L`` one of ``A/M/D/R/T/C``
      (optionally score-suffixed). A tab line with an unrecognized
      letter, or a tab-form rename (two paths), raises
      ChangeLineError (usage exit 2; the prescribed name-status feeder
      pins ``--no-renames``, F10/F13).
    - Bare path (``change_type=None``; legacy semantics at warn tier).

    Blank lines return ``[]``.
    """
    s = line.rstrip("\n")
    if not s.strip():
        return []
    if "\t" in s:
        parts = s.split("\t")
        letter = parts[0].strip()
        if not _NAME_STATUS_LETTER_RE.fullmatch(letter):
            raise ChangeLineError(
                "unrecognized name-status letter %r (expected one of"
                " A/M/D/R/T/C, optionally score-suffixed)" % letter)
        if len(parts) != 2 or letter.startswith("R"):
            # R with a score suffix implies a rename line (old TAB new);
            # a bare R<TAB>path is ambiguous. No prescribed feeder emits
            # either (done pins --no-renames); fail closed.
            raise ChangeLineError(
                "tab-form rename lines are not supported (feed porcelain"
                " 'R  old -> new' or run name-status with --no-renames)")
        return [(parts[1].strip(), letter)]
    if (len(s) >= 3 and s[2] == " "
            and (s[0] in _PORCELAIN_STATUS_CHARS
                 or s[1] in _PORCELAIN_STATUS_CHARS)
            and (s[0] in _PORCELAIN_STATUS_CHARS or s[0] == " ")
            and (s[1] in _PORCELAIN_STATUS_CHARS or s[1] == " ")):
        status, rest = s[:2], s[3:].strip()
        if status[0] == "R" and " -> " in rest:
            # Rename semantics are bounded to the rename letter (r6
            # F1): only a porcelain status starting with R may split on
            # the arrow. For every other status the arrow is filename
            # data and the whole rest is the literal path.
            if rest.count(" -> ") != 1:
                # Ambiguous: a filename itself contains the arrow
                # sequence, so either side of any split could be the
                # separator. Fail closed (exit 2) rather than gate the
                # wrong path (r5 F3).
                raise ChangeLineError(
                    "ambiguous porcelain rename line %r (the ' -> '"
                    " separator occurs more than once); rename the file"
                    " to remove the arrow sequence or feed paths"
                    " explicitly" % s)
            old, new = rest.split(" -> ", 1)
            if " -> " in old or " -> " in new:
                # r5 F3 second clause: either side of the split still
                # containing the arrow sequence is ambiguous the same
                # way; fail closed rather than gate the wrong path.
                raise ChangeLineError(
                    "ambiguous porcelain rename line %r (a split side"
                    " still contains the ' -> ' sequence); rename the"
                    " file to remove the arrow sequence or feed paths"
                    " explicitly" % s)
            return [(old.strip(), "D"), (new.strip(), status)]
        return [(rest, status)]
    return [(s.strip(), None)]


# --------------------------------------------------------------------------- #
# Subcommands.
# --------------------------------------------------------------------------- #

def successor_cycles(rows: list[dict]) -> list[str]:
    """Detect cycles in the successor (superseded_by) identity graph."""
    successor_of = {}
    for row in rows:
        ident = row.get("identity", "").strip()
        succ = row.get("successor", "").strip()
        if ident and succ:
            successor_of[ident] = succ
    cycles: list[str] = []
    seen_done: set[str] = set()
    for start in successor_of:
        if start in seen_done:
            continue
        walked: list[str] = []
        node = start
        while node in successor_of and node not in seen_done:
            if node in walked:
                cycle = walked[walked.index(node):] + [node]
                cycles.append(" -> ".join(cycle))
                seen_done.update(cycle[:-1])
                break
            walked.append(node)
            node = successor_of[node]
        else:
            seen_done.update(walked)
        seen_done.update(walked)
    return cycles


def cmd_validate(root: Path, cfg: dict, out: io.StringIO) -> int:
    reg_path = registry_path(root, cfg)
    try:
        rows = parse_registry(reg_path)
    except RegistryParseError as exc:
        print("HARD registry parse error: %s" % exc, file=out)
        return 1
    if rows is None:
        print("warn: registry file absent at %s (pre-registry repo;"
              " fail open; run inventory for the migration backlog;"
              " a mis-set doc_registry_rel facts key produces the same"
              " symptom)" % cfg["doc_registry_rel"], file=out)
        return 0

    hard = 0
    warns = 0

    # Required fields: identity and state.
    by_identity: dict[str, list[dict]] = {}
    for row in rows:
        for field in ("identity", "state"):
            if not row.get(field, "").strip():
                print("HARD missing required field '%s' in registry row"
                      " (src=%s)" % (field, row.get("src", "") or "?"),
                      file=out)
                hard += 1
        # Enum validation (documented values only).
        sot = row.get("sot", "").strip().lower()
        if sot and sot not in ("yes", "no"):
            print("HARD invalid sot value '%s' in registry row (src=%s);"
                  " expected yes or no"
                  % (row.get("sot", ""), row.get("src", "") or "?"),
                  file=out)
            hard += 1
        state = row.get("state", "").strip().lower()
        if state and state not in ("living", "completed", "superseded"):
            print("HARD invalid state value '%s' in registry row (src=%s);"
                  " expected living, completed, or superseded"
                  % (row.get("state", ""), row.get("src", "") or "?"),
                  file=out)
            hard += 1
        # F6: a non-empty audit note on a completed/superseded row must
        # carry the dated user-confirmation token; a self-minted note
        # must not license an immutable write.
        audit = row.get("audit", "").strip()
        if state in ("completed", "superseded") and audit \
                and not audit_note_valid(audit):
            print("HARD malformed audit note '%s' in registry row"
                  " (src=%s); an override note must begin with"
                  " 'user-approved YYYY-MM-DD:' (ADR-0001 user"
                  " confirmation)" % (audit, row.get("src", "") or "?"),
                  file=out)
            hard += 1
        ident = row.get("identity", "").strip()
        if ident:
            by_identity.setdefault(ident, []).append(row)

    # Duplicate identity (hard).
    for ident, group in by_identity.items():
        if len(group) > 1:
            sot_rows = [r for r in group
                        if r.get("sot", "").strip().lower() == "yes"]
            if len(sot_rows) > 1:
                print("HARD duplicate sot: %d rows declare SOT ownership"
                      " of identity '%s'" % (len(sot_rows), ident), file=out)
            else:
                print("HARD duplicate identity: '%s' declared by %d rows"
                      % (ident, len(group)), file=out)
            hard += 1

    # Successor cycles (hard).
    for cycle in successor_cycles(rows):
        print("HARD successor cycle: %s" % cycle, file=out)
        hard += 1

    # Dangling successor identities (warn): a successor no row declares
    # breaks the supersession chain silently (typo or never created).
    declared_identities = set(by_identity)
    for row in rows:
        succ = row.get("successor", "").strip()
        ident = row.get("identity", "").strip()
        if succ and succ not in declared_identities:
            print("warn: successor identity '%s' of '%s' is not declared"
                  " by any registry row" % (succ, ident or "?"), file=out)
            warns += 1

    # Stale aliases (warn).
    for row in rows:
        for alias in split_aliases(row.get("aliases", "")):
            rel = normalize_repo_path(alias)
            if not (root / rel).exists():
                print("warn: stale alias '%s' (identity '%s') does not"
                      " exist on disk" % (rel, row.get("identity", "?")),
                      file=out)
                warns += 1

    # Completed-history files without registry entries (warn, fail open).
    claimed = registered_src_paths(rows)
    for rel in list_completed_files(root, cfg):
        if _fold(rel) not in claimed:
            print("warn: unregistered completed-history file: %s" % rel,
                  file=out)
            warns += 1

    print("validate: %d hard finding(s), %d warn(s), %d registry row(s)"
          % (hard, warns, len(rows)), file=out)
    return 1 if hard else 0


def cmd_check_writes(root: Path, cfg: dict, entries: list[tuple[str, str | None]],
                     out: io.StringIO) -> int:
    """Gate changed paths (with optional change-type letters) against
    immutable completed-history directories.

    ``entries`` pairs each raw path with its optional change type
    (``None`` for letter-less argv/bare-stdin lines). Registered-src
    exemption is bounded to the add/rename transition (F1): a completed
    or superseded src with an ``A``/``R`` letter is the licensed
    archive move; any other letter is a HARD unprotected write; no
    letter passes at warn tier with a verify duty.
    """
    reg_path = registry_path(root, cfg)
    try:
        rows = parse_registry(reg_path)
    except RegistryParseError as exc:
        print("HARD registry parse error: %s" % exc, file=out)
        return 1
    if rows is None:
        print("warn: registry file absent at %s (pre-registry repo;"
              " write gate fails open)" % cfg["doc_registry_rel"], file=out)
        return 0

    # Multiply-claimed srcs: two identities registering one path is a
    # registry defect; the path stays gated (no lifecycle exemption, no
    # override) until the duplicate is deduplicated.
    src_idents: dict[str, set[str]] = {}
    for row in rows:
        src = _fold(normalize_repo_path(row.get("src", "")))
        ident = row.get("identity", "").strip()
        if src and ident:
            src_idents.setdefault(src, set()).add(ident)
    multi_claimed = {src for src, ids in src_idents.items() if len(ids) > 1}
    for src in sorted(multi_claimed):
        print("warn: src %s is registered by multiple identities (%s);"
              " it stays gated until deduplicated"
              % (src, ", ".join(sorted(src_idents[src]))), file=out)

    # Registered-src lifecycle exemption, bounded to the transition:
    # the src of a completed or superseded row is licensed only for the
    # add/rename change type (the plans and rfc-design completion
    # transitions); body edits and deletions stay gated.
    # r6 F2: the exemption compares the UNFOLDED normalized path
    # against the registry src's stored spelling (byte equality); the
    # fold still classifies the immutable-directory prefix and feeds
    # the near-match warn tier for case-variant adds.
    lifecycle_srcs: set[str] = set()      # exact (unfolded) spellings
    lifecycle_folded: dict[str, str] = {}  # folded src -> stored spelling
    overrides: set[str] = set()
    hard = 0        # unprotected immutable write findings
    note_hard = 0   # registry audit-note defects (row scan, r6 F6)
    for row in rows:
        audit = row.get("audit", "").strip()
        src_norm = normalize_repo_path(row.get("src", ""))
        src = _fold(src_norm)
        state = row.get("state", "").strip().lower()
        # r6 F4: the audit-note token check fires regardless of
        # multi-claim status; the multi-claim continue below must not
        # hide a malformed note on a multiply-claimed src row.
        if state in ("completed", "superseded") and audit \
                and not audit_note_valid(audit):
            # r5 F1: check-writes enforces the same token contract as
            # validate; a self-minted or ill-dated note licenses
            # nothing (HARD, not a silent override).
            print("HARD invalid audit note '%s' on registry row"
                  " for %s; an override note must begin with a"
                  " real, non-future 'user-approved YYYY-MM-DD:'"
                  " token (ADR-0001 user confirmation)"
                  % (audit, src), file=out)
            note_hard += 1
        if not src or src in multi_claimed:
            continue
        if state in ("completed", "superseded"):
            lifecycle_srcs.add(src_norm)
            lifecycle_folded.setdefault(src, src_norm)
            if audit:
                if not audit_note_valid(audit):
                    continue  # already reported (and counted) above
                print("warn: standing override active for %s;"
                      " clear the audit note after the licensed write"
                      " lands" % src, file=out)
                overrides.add(src)
        elif audit:
            print("warn: audit note on non-completed row (state=%s)"
                  " does not create an override for %s" % (state, src),
                  file=out)

    for raw, change_type in entries:
        rel = normalize_repo_path(raw)
        if not rel or not is_immutable(rel, cfg):
            continue
        frel = _fold(rel)
        if frel in overrides:
            print("override: immutable path %s has an audit-noted"
                  " registry row" % rel, file=out)
            continue
        if rel in lifecycle_srcs:
            if change_type is not None and "?" in change_type:
                # F4: untracked at a registered lifecycle src is the
                # freeze move arriving before staging; warn with the
                # cause, do not steer to the audit-note override.
                print("warn: untracked registered lifecycle src %s;"
                      " stage the move (git add) so the change type"
                      " can be checked; the audit-note override is for"
                      " genuine M/D findings only" % rel, file=out)
                continue
            if change_type is not None and is_licensed_transition(
                    change_type):
                print("licensed lifecycle add: %s is the registered src"
                      " of a completed/superseded registry row and the"
                      " change type (%s) is the add/rename transition"
                      % (rel, change_type), file=out)
                continue
            if change_type is None:
                # Backward-compatible bare line: the channel carries no
                # change type, so the gate cannot discriminate the
                # archive move from a body edit; pass at warn tier with
                # an explicit verify duty.
                print("warn: registered lifecycle src %s written with no"
                      " change-type letter; assuming the freeze move;"
                      " verify this is the archive transition, not a"
                      " body edit (feed git status --porcelain or"
                      " git diff --name-status output to discriminate)"
                      % rel, file=out)
                continue
            print("HARD immutable path written without override: %s"
                  " (change type %s; the registered-src exemption"
                  " licenses only the add/rename transition; body"
                  " edits and deletions need an audit-note override)"
                  % (rel, change_type), file=out)
            hard += 1
            continue
        if (change_type is not None
                and is_licensed_transition(change_type)
                and frel in lifecycle_folded):
            # r6 F2: a case-variant add of a registered lifecycle src
            # is not byte-equal to the stored spelling, so it is NOT
            # the licensed transition; on folding platforms it takes
            # the warn-tier verify path naming the near-match (like a
            # bare line) instead of a silent licensed add.
            print("warn: case-variant add of registered lifecycle src;"
                  " %s is not the registered spelling %s; on"
                  " case-insensitive filesystems this may be the same"
                  " file; verify it is the archive transition for the"
                  " registered src, not a distinct new artifact"
                  % (rel, lifecycle_folded[frel]), file=out)
            continue
        print("HARD immutable path written without override: %s" % rel,
              file=out)
        hard += 1
    print("check-writes: %d unprotected immutable write(s) of %d path(s),"
          " %d registry audit-note defect(s)" % (hard, len(entries),
                                                  note_hard), file=out)
    return 1 if hard or note_hard else 0


def cmd_inventory(root: Path, cfg: dict, out: io.StringIO) -> int:
    reg_path = registry_path(root, cfg)
    try:
        rows = parse_registry(reg_path)
    except RegistryParseError as exc:
        print("HARD registry parse error: %s" % exc, file=out)
        return 1
    if rows is None:
        print("warn: registry file absent at %s; ALL completed-history"
              " files are the migration backlog"
              % cfg["doc_registry_rel"], file=out)
        rows = []
    claimed = registered_src_paths(rows)
    missing = [rel for rel in list_completed_files(root, cfg)
               if _fold(rel) not in claimed]
    for rel in missing:
        print("backlog: unregistered completed-history file: %s" % rel,
              file=out)
    print("inventory: %d unregistered of %d completed-history file(s)"
          % (len(missing), len(list_completed_files(root, cfg))), file=out)
    return 0


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #

def run(argv: list[str], stdin_text: str = "") -> tuple[int, str]:
    """Execute the CLI in-process; returns (exit_code, stdout_text)."""
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        code = _dispatch(argv, stdin_text, buf)
    return code, buf.getvalue()


def _dispatch(argv: list[str], stdin_text: str, out: io.StringIO) -> int:
    args = list(argv)
    root_explicit: str | None = None
    channel: str | None = None
    paths: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            if arg == "--root":
                i += 1
                if i >= len(args):
                    print("error: --root requires a value\n" + USAGE,
                          file=sys.stderr)
                    return 2
                root_explicit = args[i]
            elif arg == "--stdin":
                if channel is not None:
                    print("error: conflicting input channels\n" + USAGE,
                          file=sys.stderr)
                    return 2
                channel = "stdin"
            elif arg == "--selftest":
                return cmd_selftest()
            else:
                print("error: unknown flag: %s\n%s" % (arg, USAGE),
                      file=sys.stderr)
                return 2
        elif arg in ("validate", "check-writes", "inventory"):
            subcommand = arg
            rest = args[i + 1:]
            for rest_arg in rest:
                if rest_arg.startswith("--"):
                    if rest_arg == "--stdin":
                        if channel is not None and channel != "stdin":
                            print("error: conflicting input channels\n"
                                  + USAGE, file=sys.stderr)
                            return 2
                        channel = "stdin"
                    elif rest_arg == "--root":
                        print("error: --root must precede the subcommand\n"
                              + USAGE, file=sys.stderr)
                        return 2
                    else:
                        print("error: unknown flag: %s\n%s" % (rest_arg, USAGE),
                              file=sys.stderr)
                        return 2
                else:
                    paths.append(rest_arg)
            break
        else:
            print("error: unrecognized argument: %s\n%s" % (arg, USAGE),
                  file=sys.stderr)
            return 2
        i += 1
    else:
        print("error: missing subcommand\n" + USAGE, file=sys.stderr)
        return 2

    root = resolve_repo_root(root_explicit)
    cfg = resolve_config(root)

    if subcommand == "validate":
        return cmd_validate(root, cfg, out)
    if subcommand == "inventory":
        return cmd_inventory(root, cfg, out)
    # check-writes: gather (path, change-type) entries from the channel.
    if channel == "stdin" and paths:
        # F7: key the conflict check on channel state, not parsed
        # entries; empty stdin must not silently discard argv paths.
        print("error: --stdin cannot be combined with argv paths\n"
              + USAGE, file=sys.stderr)
        return 2
    if channel == "stdin":
        text = stdin_text if stdin_text else sys.stdin.read()
        entries = []
        try:
            for line in text.splitlines():
                entries.extend(parse_change_line(line))
        except ChangeLineError as exc:
            print("error: %s\n%s" % (exc, USAGE), file=sys.stderr)
            return 2
    elif paths:
        entries = [(p, None) for p in paths]
    else:
        print("error: check-writes needs paths (argv or --stdin)\n"
              + USAGE, file=sys.stderr)
        return 2
    # F16: reject backslash-bearing input paths (fail closed; git
    # emits forward slashes, and normpath keeps backslashes so a
    # converted spelling could never be trusted to be a rename).
    for raw, _change_type in entries:
        if "\\" in raw:
            print("error: backslash-bearing path %r rejected (git emits"
                  " forward slashes)\n%s" % (raw, USAGE), file=sys.stderr)
            return 2
    return cmd_check_writes(root, cfg, entries, out)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    code, output = run(args)
    if output:
        sys.stdout.write(output)
    return code


# --------------------------------------------------------------------------- #
# Selftest (hermetic: every fixture owns its facts under a temp dir).
# --------------------------------------------------------------------------- #

FIXTURE_FACTS = """# fixture facts

```toml
plans_completed_dir = "docs/plans/completed/"
backlog_completed_dir = "docs/history/backlog/completed/"
doc_registry_rel = "docs/maintenance/document-registry.md"
```
"""


def make_fixture(prefix: str, registry_body: str = "",
                 extra_files: list[str] | None = None,
                 with_facts: bool = True,
                 facts_body: str | None = None) -> Path:
    """Build a hermetic repo-like tree under a fresh temp dir.

    Every root is registered in ``_FIXTURE_ROOTS``; ``cmd_selftest``
    removes all of them in a ``finally`` so a run leaves no fixture
    directories behind on the host.
    """
    root = Path(tempfile.mkdtemp(prefix="doc-registry-" + prefix + "-"))
    _FIXTURE_ROOTS.append(root)
    if with_facts:
        facts = root / ".ai-playbook" / "facts.md"
        facts.parent.mkdir(parents=True, exist_ok=True)
        facts.write_text(facts_body or FIXTURE_FACTS, encoding="utf-8")
    if registry_body:
        reg = root / DEFAULT_DOC_REGISTRY_REL
        reg.parent.mkdir(parents=True, exist_ok=True)
        reg.write_text(registry_body, encoding="utf-8")
    for rel in (extra_files or []):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture content\n", encoding="utf-8")
    return root


def registry_header() -> str:
    return (
        "| identity | sot | state | archived | reason | src | successor"
        " | aliases | audit |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )


class Selftest:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        self.count += 1
        if condition:
            print("ok  " + name)
        else:
            print("FAIL " + name + (": " + detail if detail else ""))
            self.failures.append(name)

    def expect(self, name: str, code: int, output: str,
               want_code: int, want_substr: str = "",
               forbid_substr: str = "") -> None:
        ok = code == want_code
        detail = "exit=%d output=%r" % (code, output)
        if ok and want_substr:
            ok = want_substr in output
        if ok and forbid_substr:
            ok = forbid_substr not in output
        self.check(name, ok, detail)


def cmd_selftest() -> int:
    st = Selftest()
    try:
        _run_selftest_checks(st)
    finally:
        # Every fixture root is removed (F12: no leaked temp dirs), even
        # when a check raises mid-run.
        for fixture_root in _FIXTURE_ROOTS:
            shutil.rmtree(fixture_root, ignore_errors=True)
        _FIXTURE_ROOTS.clear()
    print()
    if st.failures:
        print("selftest FAILED: %d of %d checks failed: %s"
              % (len(st.failures), st.count, ", ".join(st.failures)))
        return 1
    print("selftest OK: %d checks passed" % st.count)
    return 0


def _run_selftest_checks(st: Selftest) -> None:
    # Hard finding: duplicate identity.
    root = make_fixture("dup-identity", registry_header() +
                        "| doc-a | yes | living |  |  | docs/a.md |  |  |  |\n"
                        "| doc-a | no | completed | 2026-01-01 | r | docs/b.md |  |  |  |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_duplicate_identity_fails", code, output, 1,
              want_substr="duplicate identity")

    # Hard finding: duplicate SOT declaration.
    root = make_fixture("dup-sot", registry_header() +
                        "| doc-a | yes | living |  |  | docs/a.md |  |  |  |\n"
                        "| doc-a | yes | living |  |  | docs/b.md |  |  |  |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_duplicate_sot_fails", code, output, 1,
              want_substr="duplicate sot")

    # Hard finding: missing required field (identity, state).
    for missing in ("identity", "state"):
        header = registry_header()
        cols = ["doc-x", "no", "completed", "2026-01-01", "r",
                "docs/plans/completed/x.md", "", "", ""]
        cols[REGISTRY_COLUMNS.index(missing)] = ""
        root = make_fixture("missing-" + missing, header +
                            "| " + " | ".join(cols) + " |\n",
                            extra_files=["docs/plans/completed/x.md"])
        code, output = run(["--root", str(root), "validate"])
        st.expect("test_missing_required_field_fails_" + missing,
                  code, output, 1, want_substr="required")

    # Hard finding: successor cycle A <-> B.
    root = make_fixture("cycle", registry_header() +
                        "| doc-a | no | superseded | 2026-01-01 | r |"
                        " docs/plans/completed/a.md | doc-b |  |  |\n"
                        "| doc-b | no | superseded | 2026-01-01 | r |"
                        " docs/plans/completed/b.md | doc-a |  |  |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_successor_cycle_fails", code, output, 1,
              want_substr="cycle")

    # check-writes: an UNREGISTERED immutable path fails (the registry
    # row registers a different src, so no lifecycle exemption applies).
    root = make_fixture("immutable", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/other.md |  |  |  |\n",
                        extra_files=["docs/other.md"])
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/a.md"])
    st.expect("test_immutable_write_fails", code, output, 1,
              want_substr="docs/plans/completed/a.md")

    # check-writes: the src of a completed/superseded registry row with
    # NO change-type letter (argv/bare-stdin legacy channel) passes at
    # warn tier with a verify duty; an unregistered sibling under the
    # same dir still fails.
    root = make_fixture("lifecycle", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n")
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/a.md"])
    st.expect("test_registered_lifecycle_src_passes_warn_tier", code,
              output, 0, want_substr="verify this is the archive transition")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="docs/plans/completed/a.md\n")
    st.expect("test_bare_stdin_registered_src_warns", code, output, 0,
              want_substr="no change-type letter")
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/b.md"])
    st.expect("test_unregistered_sibling_under_same_dir_fails", code,
              output, 1, want_substr="docs/plans/completed/b.md")

    # check-writes: audit-noted override on a completed row passes
    # (warn names the cleanup duty: clear the note after the write).
    root = make_fixture("override", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " user-approved 2026-09-10: correction |\n")
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/a.md"])
    st.expect("test_immutable_write_override_passes", code, output, 0,
              want_substr="override")
    st.check("test_standing_override_warn_names_cleanup",
             "clear the audit note after the licensed write lands"
             in output, repr(output))

    # check-writes: an audit note on a LIVING row creates no override,
    # and aliases are never overridden.
    root = make_fixture("override-living", registry_header() +
                        "| doc-a | yes | living |  |  | docs/a.md |  |"
                        " docs/plans/completed/old.md | 2026-09-10 note |\n",
                        extra_files=["docs/a.md",
                                     "docs/plans/completed/old.md"])
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/a.md",
                        "docs/plans/completed/old.md"])
    ok = (code == 1 and "docs/plans/completed/a.md" in output
          and "docs/plans/completed/old.md" in output
          and "HARD immutable path written" in output)
    st.check("test_immutable_write_override_living_row_fails", ok,
             "exit=%d output=%r" % (code, output))

    # Hard finding: enum typos (sot/state) rejected.
    root = make_fixture("enum-sot", registry_header() +
                        "| doc-a | yeas | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n",
                        extra_files=["docs/plans/completed/a.md"])
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_invalid_sot_fails", code, output, 1,
              want_substr="invalid sot")
    root = make_fixture("enum-state", registry_header() +
                        "| doc-a | no | finishd | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n",
                        extra_files=["docs/plans/completed/a.md"])
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_invalid_state_fails", code, output, 1,
              want_substr="invalid state")

    # Hard finding: unknown/renamed registry header rejected.
    renamed = ("| id | sot | state | archived | reason | src | successor"
               " | aliases | audit |\n"
               "|---|---|---|---|---|---|---|---|---|\n"
               "| doc-a | no | completed | 2026-01-01 | r |"
               " docs/plans/completed/a.md |  |  |  |\n")
    root = make_fixture("header-renamed", renamed)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_header_mismatch_fails", code, output, 1,
              want_substr="parse error")

    # F10: strict header equality; a reordered header is a loud parse
    # error, not a silently accepted deviation (zero consumers rely on
    # reorder acceptance).
    reordered = ("| sot | identity | state | archived | reason | src"
                 " | successor | aliases | audit |\n"
                 "|---|---|---|---|---|---|---|---|---|\n"
                 "| no | doc-a | completed | 2026-01-01 | r |"
                 " docs/plans/completed/a.md |  |  |  |\n")
    root = make_fixture("header-reordered", reordered)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_header_reordered_fails_closed", code, output, 1,
              want_substr="parse error")

    # Hard finding: row cell count must equal the column count.
    shifted = (registry_header() +
               "| doc-a | no | completed | 2026-01-01 | r |"
               " docs/plans/completed/a.md |  |\n")
    root = make_fixture("row-shifted", shifted)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_row_cell_count_mismatch_fails", code, output, 1,
              want_substr="parse error")

    # check-writes honors a non-default plans_completed_dir from facts.
    custom_facts = ("# fixture facts\n\n```toml\n"
                    "plans_completed_dir = \"docs/archived-plans/\"\n"
                    "backlog_completed_dir ="
                    " \"docs/history/backlog/completed/\"\n"
                    "doc_registry_rel ="
                    " \"docs/maintenance/document-registry.md\"\n```\n")
    root = make_fixture("facts-custom-dirs", registry_header(),
                        extra_files=["docs/archived-plans/old.md"],
                        facts_body=custom_facts)
    code, output = run(["--root", str(root), "check-writes",
                        "docs/archived-plans/old.md"])
    st.expect("test_check_writes_custom_facts_dir_fails", code, output, 1,
              want_substr="docs/archived-plans/old.md")

    # Warn tier: stale alias target.
    root = make_fixture("stale-alias", registry_header() +
                        "| doc-a | yes | living |  |  | docs/a.md |  |"
                        " docs/old-link.md |  |\n",
                        extra_files=["docs/a.md"])
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_stale_alias_warns", code, output, 0,
              want_substr="alias")

    # Warn tier: completed-history file missing from registry (fail open).
    root = make_fixture("legacy", registry_header() +
                        "| doc-a | yes | living |  |  | docs/a.md |  |  |  |\n",
                        extra_files=["docs/a.md",
                                     "docs/plans/completed/legacy.md"])
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_missing_legacy_entry_warns", code, output, 0,
              want_substr="unregistered")

    # Inventory names exactly the unregistered file.
    code, output = run(["--root", str(root), "inventory"])
    ok = (code == 0 and "docs/plans/completed/legacy.md" in output
          and "docs/a.md" not in output)
    st.check("test_inventory_lists_missing_entries", ok,
             "exit=%d output=%r" % (code, output))

    # Mirror paths exempt.
    root = make_fixture("mirror", registry_header())
    for path in ("docs/history/context/confluence/page.md",):
        code, output = run(["--root", str(root), "check-writes", path])
        st.expect("test_mirror_paths_exempt", code, output, 0,
                  forbid_substr=path)

    # Ephemera exempt.
    root = make_fixture("ephemera", registry_header())
    for path in ("docs/history/reviews/r.md", "docs/tmp/t.md"):
        code, output = run(["--root", str(root), "check-writes", path])
        st.expect("test_ephemera_exempt_" + path.replace("/", "_"),
                  code, output, 0, forbid_substr=path)

    # Absent registry: validate fails open with one warn hint.
    root = make_fixture("no-registry")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_validate_absent_registry_fails_open", code, output, 0,
              want_substr="warn")

    # Absent registry: check-writes --stdin fails open (never exit 1).
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="docs/plans/completed/a.md\n")
    st.expect("test_check_writes_absent_registry_fails_open", code, output,
              0, want_substr="warn")

    # stdin channel: only the immutable path is named.
    root = make_fixture("stdin", registry_header())
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="README.md\ndocs/plans/completed/a.md\n"
                                  "scripts/x.py\n")
    ok = (code == 1 and "docs/plans/completed/a.md" in output
          and "README.md" not in output
          and output.count("immutable") >= 1)
    st.check("test_check_writes_stdin_channel", ok,
             "exit=%d output=%r" % (code, output))

    # argv channel: same discrimination.
    code, output = run(["--root", str(root), "check-writes",
                        "README.md", "docs/plans/completed/a.md",
                        "scripts/x.py"])
    ok = (code == 1 and "docs/plans/completed/a.md" in output
          and "README.md" not in output)
    st.check("test_check_writes_argv_channel", ok,
             "exit=%d output=%r" % (code, output))

    # Hard finding: successor self-loop (a row superseding itself).
    root = make_fixture("self-loop", registry_header() +
                        "| doc-a | no | superseded | 2026-01-01 | r |"
                        " docs/plans/completed/a.md | doc-a |  |  |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_successor_selfloop_fails", code, output, 1,
              want_substr="cycle")

    # Warn tier: dangling successor identity (declared by no row).
    root = make_fixture("dangling-successor", registry_header() +
                        "| doc-a | no | superseded | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |"
                        " nonexistent-identity |  |  |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_dangling_successor_warns", code, output, 0,
              want_substr="is not declared by any registry row")

    # Warn + hard: a src claimed by two identities stays gated even when
    # one claimant carries an audit note (no override, no lifecycle
    # exemption, until the duplicate is deduplicated).
    root = make_fixture("dup-src", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " user-approved 2026-09-10: note |\n"
                        "| doc-b | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n")
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/a.md"])
    st.expect("test_duplicate_src_stays_gated", code, output, 1,
              want_substr="multiple identities")

    # Parser: an escaped pipe inside a free-text cell is literal text,
    # not a delimiter (Markdown table convention).
    root = make_fixture("escaped-pipe", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 |"
                        " fix A \\| B | docs/plans/completed/a.md |"
                        "  |  |  |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_escaped_pipe_cell_parses", code, output, 0,
              forbid_substr="parse error")

    # Parser: only the FIRST table is parsed; a notes section with its
    # own two-column table after the registry table is prose, not rows.
    root = make_fixture("second-table", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n"
                        "\n## Notes\n\n"
                        "| note | detail |\n|---|---|\n"
                        "| a | b |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_second_table_ignored", code, output, 0,
              forbid_substr="parse error")

    # Facts normalization: a ./-prefixed dir still gates (no silent
    # bypass), and an absolute spelling resolves cleanly (no traceback).
    dotted_facts = ("# fixture facts\n\n```toml\n"
                    "plans_completed_dir = \"./docs/plans/completed/\"\n"
                    "backlog_completed_dir ="
                    " \"./docs/history/backlog/completed/\"\n"
                    "doc_registry_rel ="
                    " \"./docs/maintenance/document-registry.md\"\n```\n")
    root = make_fixture("facts-dotted", registry_header(),
                        facts_body=dotted_facts)
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/a.md"])
    st.expect("test_dotted_facts_dir_still_gates", code, output, 1,
              want_substr="docs/plans/completed/a.md")
    absolute_facts = ("# fixture facts\n\n```toml\n"
                      "plans_completed_dir = \"/docs/plans/completed/\"\n"
                      "backlog_completed_dir ="
                      " \"/docs/history/backlog/completed/\"\n"
                      "doc_registry_rel ="
                      " \"/docs/maintenance/document-registry.md\"\n```\n")
    root = make_fixture("facts-absolute", registry_header(),
                        extra_files=["docs/plans/completed/a.md"],
                        facts_body=absolute_facts)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_absolute_facts_dir_resolves_cleanly", code, output, 0,
              forbid_substr="Traceback")

    # check-writes: all four immutable dir families gate by default
    # (backlog-completed, non-mirror context, feature-notes; the default
    # plans-completed family is covered by the fixtures above).
    root = make_fixture("immutable-families", registry_header())
    for path in ("docs/history/backlog/completed/b.md",
                 "docs/history/context/c.md",
                 "docs/history/feature-notes/f.md"):
        code, output = run(["--root", str(root), "check-writes", path])
        st.expect("test_immutable_dir_" + path.replace("/", "_"),
                  code, output, 1, want_substr=path)

    # Unknown flag: fail closed with usage error.
    code, output = run(["--root", str(root), "check-writes", "--st", "din"])
    st.expect("test_unknown_flag_fails_closed", code, output, 2,
              want_substr="usage")

    # Unknown flag: the removed --diff channel is now a usage error
    # (fail closed on the retired channel, never a silent pass).
    code, output = run(["--root", str(root), "check-writes", "--diff"])
    st.expect("test_removed_diff_channel_fails_closed", code, output, 2,
              want_substr="usage")

    # F1: the registered-src exemption is bounded to the add/rename
    # transition. Registered src + clean add/rename letter = licensed
    # (exit 0, informational); registered src + M/D letter = HARD
    # without an audit note; unregistered immutable path fails
    # regardless of letter; name-status lines carry letters too.
    root = make_fixture("f1-lifecycle", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="A  docs/plans/completed/a.md\n")
    st.expect("test_registered_src_add_letter_passes", code, output, 0,
              want_substr="licensed lifecycle add")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="AM docs/plans/completed/a.md\n")
    st.expect("test_registered_src_add_then_modify_not_licensed", code,
              output, 1,
              want_substr="immutable path written without override")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="R  docs/old.md -> docs/plans/completed/a.md\n")
    st.expect("test_registered_src_rename_letter_passes", code, output, 0,
              want_substr="licensed lifecycle add")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M  docs/plans/completed/a.md\n")
    st.expect("test_registered_src_modify_letter_fails", code, output, 1,
              want_substr="immutable path written without override")
    # F1: leading-space worktree porcelain forms keep their status
    # column (unstaged M/D of a registered src is HARD; unregistered
    # immutable path with a leading-space letter still fails).
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text=" M docs/plans/completed/a.md\n")
    st.expect("test_leading_space_modify_registered_src_fails", code,
              output, 1,
              want_substr="immutable path written without override")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text=" D docs/plans/completed/a.md\n")
    st.expect("test_leading_space_delete_registered_src_fails", code,
              output, 1,
              want_substr="immutable path written without override")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text=" M docs/plans/completed/b.md\n")
    st.expect("test_leading_space_modify_unregistered_fails", code,
              output, 1, want_substr="docs/plans/completed/b.md")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text=" D docs/plans/completed/b.md\n")
    st.expect("test_leading_space_delete_unregistered_fails", code,
              output, 1, want_substr="docs/plans/completed/b.md")
    # F2: a rename OUT of an immutable dir gates the old side (typed
    # as a deletion); a rename INTO a registered lifecycle src is the
    # licensed freeze move.
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="R  docs/plans/completed/a.md -> docs/live/a.md\n")
    st.expect("test_rename_out_of_immutable_dir_fails", code, output, 1,
              want_substr="docs/plans/completed/a.md")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="R  docs/tmp/x.md -> docs/plans/completed/a.md\n")
    st.expect("test_rename_into_registered_src_licensed", code, output,
              0, want_substr="licensed lifecycle add")
    # F3: conflict statuses are not licensed adds.
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="AA docs/plans/completed/a.md\n")
    st.expect("test_conflict_status_not_licensed", code, output, 1,
              want_substr="immutable path written without override")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="AU docs/plans/completed/a.md\n")
    st.expect("test_conflict_status_au_not_licensed", code, output, 1,
              want_substr="immutable path written without override")
    # F4: untracked at a registered lifecycle src is the freeze move
    # arriving; warn tier naming the cause, no override steer.
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="?? docs/plans/completed/a.md\n")
    st.expect("test_untracked_registered_src_warns_stage_move", code,
              output, 0, want_substr="stage the move")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="A\tdocs/plans/completed/a.md\n")
    st.expect("test_name_status_add_letter_passes", code, output, 0,
              want_substr="licensed lifecycle add")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M\tdocs/plans/completed/a.md\n")
    st.expect("test_name_status_modify_letter_fails", code, output, 1,
              want_substr="immutable path written without override")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="A  docs/plans/completed/b.md\n")
    st.expect("test_unregistered_add_letter_still_fails", code, output, 1,
              want_substr="docs/plans/completed/b.md")
    # F10: recognized-but-uncommon letters (T) parse and gate; unknown
    # letters and tab-form renames are usage errors (exit 2).
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="T\tdocs/plans/completed/a.md\n")
    st.expect("test_typechange_letter_gates_hard", code, output, 1,
              want_substr="docs/plans/completed/a.md")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="X\tdocs/plans/completed/a.md\n")
    st.expect("test_unknown_name_status_letter_fails_closed", code,
              output, 2, want_substr="usage")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="R100\tdocs/old.md\tdocs/new.md\n")
    st.expect("test_tab_rename_line_fails_closed", code, output, 2,
              want_substr="usage")
    # F16: backslash-bearing input paths are rejected (fail closed).
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M  docs\\plans\\completed\\a.md\n")
    st.expect("test_backslash_stdin_path_fails_closed", code, output, 2,
              want_substr="usage")
    # F7: --stdin plus argv paths is a usage error even with empty
    # stdin (channel state, not parsed content, decides).
    code, output = run(["--root", str(root), "check-writes", "--stdin",
                        "docs/plans/completed/a.md"], stdin_text="")
    st.expect("test_stdin_channel_with_argv_paths_fails_closed", code,
              output, 2, want_substr="usage")

    # F6: audit-note token format on completed rows (validate).
    root = make_fixture("f6-audit-valid", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " user-approved 2026-09-10: fixed broken link |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_audit_note_valid_token_passes", code, output, 0,
              forbid_substr="malformed audit note")
    root = make_fixture("f6-audit-malformed", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " self-approved fix |\n")
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_audit_note_malformed_token_fails", code, output, 1,
              want_substr="malformed audit note")

    # r5 F7: the audit-token date must be a real calendar date, not in
    # the future (shape-only matching let 9999-99-99 and future dates
    # license immutable writes).
    for label, bad_date in (("month_99", "2026-99-10"),
                            ("day_99", "2026-09-99"),
                            ("future", "2099-01-01")):
        root = make_fixture("f7-audit-" + label, registry_header() +
                            "| doc-a | no | completed | 2026-01-01 | r |"
                            " docs/plans/completed/a.md |  |  |"
                            " user-approved %s: fix |\n" % bad_date)
        code, output = run(["--root", str(root), "validate"])
        st.expect("test_audit_note_impossible_date_" + label + "_fails",
                  code, output, 1, want_substr="malformed audit note")
        code, output = run(["--root", str(root), "check-writes",
                            "--stdin"],
                           stdin_text="M  docs/plans/completed/a.md\n")
        st.expect("test_audit_note_impossible_date_" + label
                  + "_no_override", code, output, 1,
                  want_substr="immutable path written without override")

    # r5 F1: check-writes enforces the same token contract as validate;
    # a self-minted note on the override row licenses nothing.
    root = make_fixture("f1-selfminted-override", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " self-approved quick fix |\n")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M  docs/plans/completed/a.md\n")
    st.expect("test_check_writes_selfminted_note_hard_fails", code,
              output, 1, want_substr="invalid audit note")
    # r6 F6: the summary counts the row-scan audit-note defect
    # separately from write findings.
    st.check("test_check_writes_summary_counts_note_defect_separately",
             "1 registry audit-note defect" in output, repr(output))

    # r6 F4: a malformed audit note on a multiply-claimed src row is
    # reported by standalone check-writes too (the multi-claim
    # continue must not hide it).
    root = make_fixture("f4-dup-src-bad-note", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " self-approved note |\n"
                        "| doc-b | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="A  docs/plans/completed/a.md\n")
    st.expect("test_multi_claimed_row_bad_audit_note_reported", code,
              output, 1, want_substr="invalid audit note")

    # r6 F7: one-day clock skew tolerated. An approval dated tomorrow
    # (minted today in a timezone ahead of the host) passes; the day
    # after tomorrow still fails.
    skew_ok = (datetime.date.today()
               + datetime.timedelta(days=1)).isoformat()
    skew_bad = (datetime.date.today()
                + datetime.timedelta(days=2)).isoformat()
    root = make_fixture("f7-skew-ok", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " user-approved %s: fix |\n" % skew_ok)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_audit_note_tomorrow_passes", code, output, 0,
              forbid_substr="malformed audit note")
    root = make_fixture("f7-skew-bad", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " user-approved %s: fix |\n" % skew_bad)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_audit_note_day_after_tomorrow_fails", code, output, 1,
              want_substr="malformed audit note")

    # r5 F3: a porcelain rename whose path text contains the arrow
    # sequence is ambiguous; fail closed (exit 2), never a silent
    # misparse. A clean rename still parses both sides.
    root = make_fixture("f3-arrow-rename", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="R  docs/live/a -> b ->"
                       " docs/plans/completed/zz.md\n")
    st.expect("test_arrow_bearing_rename_fails_closed", code, output, 2,
              want_substr="usage")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="R  docs/live/x -> y.md ->"
                       " docs/plans/completed/a.md\n")
    st.expect("test_arrow_bearing_rename_into_src_fails_closed", code,
              output, 2, want_substr="ambiguous")

    # r6 F1: the arrow split is bounded to the rename letter. Any other
    # status carries the arrow as filename data: the whole rest is the
    # literal path and gates as itself (no phantom split entries).
    root = make_fixture("f1-arrow-norename", registry_header())
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M  docs/plans/completed/report ->"
                       " final.md\n")
    st.expect("test_single_arrow_modify_gates_full_literal_path", code,
              output, 1,
              want_substr="docs/plans/completed/report -> final.md")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="?? docs/plans/completed/c -> d.md\n")
    st.expect("test_single_arrow_untracked_gates_full_literal_path", code,
              output, 1, want_substr="docs/plans/completed/c -> d.md")
    # Bypass direction: a non-rename arrow line whose truncated prefix
    # is a registered src must gate the full real path, never exit as a
    # phantom licensed add.
    root = make_fixture("f1-arrow-bypass", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M  docs/plans/completed/a.md ->"
                       " evil.md\n")
    st.expect("test_single_arrow_licensed_prefix_no_bypass", code, output,
              1, want_substr="docs/plans/completed/a.md -> evil.md",
              forbid_substr="licensed lifecycle add")

    # F1: a registered src with an M letter plus an audit note passes
    # with the standing-override warn (the corruption override path).
    root = make_fixture("f1-override", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |"
                        " user-approved 2026-09-10: correction |\n")
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M  docs/plans/completed/a.md\n")
    st.expect("test_registered_src_modify_with_audit_note_passes", code,
              output, 0, want_substr="override")
    st.check("test_modify_override_warns_cleanup",
             "clear the audit note after the licensed write lands"
             in output, repr(output))

    # F3: single-dash and centered GFM alignment separators are
    # separator rows, not data (no phantom enum/cycle findings).
    centered = ("| identity | sot | state | archived | reason | src"
                " | successor | aliases | audit |\n"
                "|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|\n"
                "| doc-a | no | completed | 2026-01-01 | r |"
                " docs/plans/completed/a.md |  |  |  |\n")
    root = make_fixture("separator-centered", centered)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_centered_separator_row_parses_clean", code, output, 0,
              forbid_substr=":-:")

    # F5: a C-quoted stdin path is unquoted before comparison (macOS
    # NFD filenames arrive quoted from git without quotePath=false).
    root = make_fixture("quoted-path", registry_header())
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text='"docs/plans/completed/a b.md"\n')
    st.expect("test_quoted_stdin_path_named_unquoted", code, output, 1,
              want_substr="docs/plans/completed/a b.md")

    # F6/F11 (r5 F2): gates and exemption sets compare case-folded
    # spellings. The fold trait is anchored OUTSIDE the code under
    # test: an unconditional delegation check plus concrete
    # platform-conditional expectations, so deleting _fold's body
    # (identity) fails the suite on darwin/win32. The gate fixtures
    # then derive their expected exit codes from that anchored trait.
    folds = sys.platform in ("darwin", "win32")
    st.check("test_fold_delegates_to_platform_case_rule",
             _fold("AbC") == ("abc" if sys.platform == "darwin"
                              else os.path.normcase("AbC")),
             "_fold('AbC')=%r" % _fold("AbC"))
    st.check("test_fold_concrete_expectation",
             _fold("A") == ("a" if folds else "A"),
             "_fold('A')=%r folds=%r" % (_fold("A"), folds))
    root = make_fixture("case-variant", registry_header() +
                        "| doc-a | no | completed | 2026-01-01 | r |"
                        " docs/plans/completed/a.md |  |  |  |\n")
    cfg = resolve_config(root)
    variant = "docs/plans/COMPLETED/a.md"
    st.check("test_case_variant_immutable_tracks_fold",
             is_immutable(variant, cfg) == folds,
             "is_immutable=%r folds=%r"
             % (is_immutable(variant, cfg), folds))
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text="M  " + variant + "\n")
    # Registered src + M is HARD whenever the variant folds into the
    # registered lowercase src; on identity platforms the variant is
    # simply not immutable (exit 0, not gated).
    st.expect("test_case_variant_registered_src_gates_via_fold", code,
              output, 1 if folds else 0,
              want_substr="immutable path written without override"
              if folds else "")
    unregistered_variant = "docs/plans/COMPLETED/zz.md"
    code, output = run(["--root", str(root), "check-writes", "--stdin"],
                       stdin_text=unregistered_variant + "\n")
    st.expect("test_case_variant_unregistered_gates_via_fold", code,
              output, 1 if folds else 0,
              want_substr=unregistered_variant if folds else "")
    # The claimed set itself is stored folded (portable identity check).
    from_doc_registry = parse_registry(
        root / DEFAULT_DOC_REGISTRY_REL) or []
    st.check("test_claimed_set_stored_folded",
             all(p == _fold(p)
                 for p in registered_src_paths(from_doc_registry)),
             repr(registered_src_paths(from_doc_registry)))

    # r6 F5: the fold-family gate assertions run with _fold pinned to
    # str.lower AND to identity on EVERY platform, so both traits are
    # anchored regardless of host (a regression removing the darwin
    # fold fails the suite on Linux too). Each pinned run asserts the
    # gate fires iff folding is active.
    real_fold = _fold
    try:
        for pin_label, pinned_fold, fold_active in (
                ("lower", str.lower, True),
                ("identity", lambda p: p, False)):
            globals()["_fold"] = pinned_fold
            root = make_fixture("f5-fold-" + pin_label, registry_header() +
                                "| doc-a | no | completed | 2026-01-01 | r |"
                                " docs/plans/completed/a.md |  |  |  |\n")
            cfg = resolve_config(root)
            variant = "docs/plans/COMPLETED/a.md"
            st.check("test_fold_pin_" + pin_label + "_immutable_trait",
                     is_immutable(variant, cfg) is fold_active,
                     "is_immutable=%r fold_active=%r"
                     % (is_immutable(variant, cfg), fold_active))
            code, output = run(["--root", str(root), "check-writes",
                                "--stdin"],
                               stdin_text="M  " + variant + "\n")
            if fold_active:
                st.expect("test_fold_pin_" + pin_label
                          + "_variant_write_gates", code, output, 1,
                          want_substr="immutable path written without"
                          " override")
            else:
                st.expect("test_fold_pin_" + pin_label
                          + "_variant_write_passes", code, output, 0,
                          forbid_substr="immutable path written without"
                          " override")
            unregistered_variant = "docs/plans/COMPLETED/zz.md"
            code, output = run(["--root", str(root), "check-writes",
                                "--stdin"],
                               stdin_text=unregistered_variant + "\n")
            if fold_active:
                st.expect("test_fold_pin_" + pin_label
                          + "_unregistered_gates", code, output, 1,
                          want_substr=unregistered_variant)
            else:
                st.expect("test_fold_pin_" + pin_label
                          + "_unregistered_passes", code, output, 0,
                          forbid_substr=unregistered_variant)
            # r6 F2 trait under the same pin: a case-variant add of a
            # registered src is a near-match warn (never a licensed
            # add) when folding, and a plain unregistered hard gate
            # when not.
            code, output = run(["--root", str(root), "check-writes",
                                "--stdin"],
                               stdin_text="A  docs/plans/completed/A.md\n")
            if fold_active:
                st.expect("test_fold_pin_" + pin_label
                          + "_case_variant_add_near_match_warns", code,
                          output, 0,
                          want_substr="docs/plans/completed/a.md",
                          forbid_substr="licensed lifecycle add")
            else:
                st.expect("test_fold_pin_" + pin_label
                          + "_case_variant_add_still_gates", code, output,
                          1, want_substr="docs/plans/completed/A.md")
    finally:
        globals()["_fold"] = real_fold

    # F8: a root-escaping facts value warns and falls back to the
    # documented default instead of silently disabling the gate family.
    escaping_facts = ("# fixture facts\n\n```toml\n"
                      "plans_completed_dir = \"../shared/completed/\"\n"
                      "backlog_completed_dir ="
                      " \"docs/history/backlog/completed/\"\n"
                      "doc_registry_rel ="
                      " \"docs/maintenance/document-registry.md\"\n```\n")
    root = make_fixture("facts-escaping", registry_header(),
                        facts_body=escaping_facts)
    code, output = run(["--root", str(root), "check-writes",
                        "docs/plans/completed/a.md"])
    st.expect("test_root_escaping_facts_value_falls_back", code, output,
              1, want_substr="escapes the repo root")

    # F9: a backslash-run of two or more before a pipe is a parse
    # error (fail closed on ambiguous Markdown escaping).
    run_line = ("| doc-a | no | completed | 2026-01-01 |"
                " fix A \\\\| B | docs/plans/completed/a.md |"
                "  |  |  |\n")
    root = make_fixture("backslash-run", registry_header() + run_line)
    code, output = run(["--root", str(root), "validate"])
    st.expect("test_backslash_run_before_pipe_fails_closed", code, output,
              1, want_substr="parse error")


if __name__ == "__main__":
    sys.exit(main())
