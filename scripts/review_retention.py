#!/usr/bin/env python3
"""Review artifact retention helper (review staging and infra quality
plan, Task 2).

The helper gives the review corpus a lifecycle without ever making a
deletion implicit. It scans the review directories for record-shaped
files (``*.md`` staging docs and ``*.stats.json`` sidecars), groups them
into record units by shared base name in one directory (a staging doc
and its matching ``.stats.json`` sidecar are one unit), and classifies
each unit against the retention cutoff:

- ``candidates``: complete pairs whose leading filename date (``YYYY-MM-DD``
  prefix) is strictly before the cutoff. These are what a prune removes,
  each pair as one unit.
- ``unpaired_retained``: a Markdown half or a sidecar half with its twin
  missing. Unpaired records are NEVER auto-pruned; they are retained and
  reported for explicit review.
- ``undated_retained``: record-shaped files without a leading filename
  date. Undated files are NEVER auto-pruned.
- ``in_window_retained``: complete pairs dated on or after the cutoff.
- ``kept_by_rule``: would-be candidates excluded by an explicit
  ``--keep PATH`` rule (a file path or a directory prefix).

Cutoff semantics: the cutoff is today minus N calendar months (default
three, overridable per run with ``--months N`` or per repository with the
optional ``review_retention_months`` facts key read from the `````toml`
fence in ``.ai-playbook/facts.md``). The filename date alone decides
candidacy; filesystem mtime is never consulted. The configured ``tmp_dir``
(the ``tmp_dir`` facts key, default ``docs/tmp/``) is never scanned, not
even when a ``--reviews-dir`` override points at its parent.

Modes:

- dry run (the default, also with the explicit ``--dry-run`` flag):
  print the deterministic candidate report naming directory, filename
  date, record kind, and pairing for every candidate; no document bodies
  are ever printed. Two consecutive runs on an unchanged tree emit
  byte-identical reports.
- ``--prune``: delete the candidate pairs as units. Deletion is
  manifest-gated: ``--from-manifest PATH`` must name a manifest whose
  recorded candidate set (paths AND per-file SHA-256 hashes) still
  matches the directory exactly, otherwise the helper aborts non-zero
  with zero deletions.
- ``--manifest PATH``: write the sanitized manifest (schema, mode,
  cutoff, counts, per-path SHA-256 hashes) of the candidate set in dry
  run mode, or of the deleted set after a completed prune. The manifest
  carries paths, hashes, and counts only; no review text and no document
  bodies.
- ``docs-branch-commit`` subcommand: the full docs-branch deletion
  transaction behind ``--prune``'s durability gap. The docs-branch skill
  is add-only: a live file absent from disk is RESTORED from the branch
  unless it was explicitly removed in the latest docs commit, so only an
  explicit-delete commit makes a prune durable. The subcommand requires
  ``--from-manifest`` (the same drift gate as ``--prune``), then (1)
  builds a temporary ``git worktree`` of the docs branch (default
  ``docs``, ``--docs-branch`` override; the live checkout never holds
  the branch), (2) removes the manifest-matched candidate paths there,
  (3) commits and VERIFIES the removals (the latest branch commit must
  record each path as deleted and the tip must no longer track it),
  and only then (4) removes the live shadow files with the same
  pairing-aware prune as ``--prune``. With no docs branch the leg is
  reported as skipped and NOTHING is mutated on either branch or live
  tree. Any failure before the live prune leaves every live file in
  place; exit taxonomy: 0 on success, 1 on a refusal (manifest drift, a
  failed docs-branch step or verification, a failed unlink mid-prune),
  2 on a usage error (bad ``--months``, ``--prune`` or
  ``docs-branch-commit`` without ``--from-manifest``, ``--dry-run`` or
  ``--prune`` combined with the subcommand, an unreadable or unsupported
  manifest).

Standard library only.
"""

from __future__ import annotations

import argparse
import calendar
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# Documented default retention window (calendar months). A repository can
# override it with the optional facts key below; a run can override both
# with --months N.
DEFAULT_RETENTION_MONTHS = 3

MONTHS_KEY = "review_retention_months"

REVIEWS_DIR_KEY = "reviews_dir"

TMP_DIR_KEY = "tmp_dir"

DEFAULT_REVIEWS_DIR = "docs/reviews/"

DEFAULT_TMP_DIR = "docs/tmp/"

MANIFEST_SCHEMA = "review-retention-manifest/1"

# Default shadow branch of the docs-branch skill; --docs-branch overrides.
DEFAULT_DOCS_BRANCH = "docs"

# docs_branch_leg statuses (deterministic report values).
DOCS_LEG_NA = "not-applicable"  # dry-run and plain --prune modes
DOCS_LEG_COMMITTED = "committed"  # explicit-delete commit recorded and verified
DOCS_LEG_NOOP = "no-tracked-deletions"  # branch exists, candidates not tracked there
DOCS_LEG_SKIPPED = "skipped-no-branch"  # no repo or no docs branch; zero mutations

# The filename date is the leading YYYY-MM-DD of the filename, followed by
# a separator or the end of the name. Anything else is undated and never
# auto-pruned.
_FILENAME_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?=[.-]|$)")

# The review-kind infixes the live corpus uses between the date stamp and
# the slug (mirrors review_record_selection.REVIEW_KIND_INFIXES); the bare
# ``review-`` kind is recognized separately, everything else is ``other``.
_RECORD_KIND_INFIXES = (
    "plan-review-",
    "branch-review-",
    "code-review-",
    "exec-review-",
)

_BARE_REVIEW_INFIX = "review-"

# Module-level date source for the cutoff computation. The seam mirrors
# review_record_selection.DATE_SOURCE so a future test can freeze the
# cutoff without swapping the datetime module.
DATE_SOURCE = datetime.date.today

MAX_RETENTION_MONTHS = 1200


class RetentionRefused(Exception):
    """The helper refuses a mutation; the message is actionable (exit 1)."""


class RetentionUsageError(Exception):
    """An invalid invocation or an unusable input (exit 2)."""


@dataclass
class RecordUnit:
    """One record unit: the files sharing a base name in one directory.

    A complete unit (``markdown`` and ``sidecar`` both present) is a pair
    and is the only pruneable shape; every other shape is retained and
    reported.
    """

    directory: Path
    base: str
    markdown: Path | None = None
    sidecar: Path | None = None

    @property
    def pairing(self) -> str:
        if self.markdown is not None and self.sidecar is not None:
            return "pair"
        if self.markdown is not None:
            return "unpaired-markdown"
        return "unpaired-sidecar"

    @property
    def filename_date(self) -> date | None:
        return _filename_date(self.base)

    @property
    def kind(self) -> str:
        return _record_kind(self.base)

    @property
    def files(self) -> list[Path]:
        return [path for path in (self.markdown, self.sidecar) if path is not None]


@dataclass
class Classification:
    """The retention buckets over one discovered corpus."""

    candidates: list[RecordUnit] = field(default_factory=list)
    unpaired: list[RecordUnit] = field(default_factory=list)
    undated: list[RecordUnit] = field(default_factory=list)
    in_window: list[RecordUnit] = field(default_factory=list)
    kept: list[tuple[RecordUnit, Path]] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Filename grammar: date, kind, unit base.
# --------------------------------------------------------------------------- #
def _filename_date(base: str) -> date | None:
    """The leading filename date of a record base, or None when undated.

    A syntactically matching prefix that is not a real calendar date (for
    example month 13) counts as undated: fail closed, never auto-prune.
    """
    match = _FILENAME_DATE_RE.match(base)
    if match is None:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def _record_kind(base: str) -> str:
    """The review record kind carried by the base name after the date."""
    rest = base
    date_match = re.match(r"\d{4}-\d{2}-\d{2}-", base)
    if date_match is not None:
        rest = base[date_match.end():]
    for infix in _RECORD_KIND_INFIXES:
        if rest.startswith(infix):
            return infix[:-1]
    if rest.startswith(_BARE_REVIEW_INFIX):
        return "review"
    return "other"


def _record_role(filename: str) -> str | None:
    """markdown, sidecar, or None for a non-record-shaped filename."""
    if filename.endswith(".stats.json"):
        return "sidecar"
    if filename.endswith(".md"):
        return "markdown"
    return None


def _unit_base(filename: str) -> str | None:
    """The shared base name of a record file, or None when not a record."""
    if filename.endswith(".stats.json"):
        return filename[: -len(".stats.json")]
    if filename.endswith(".md"):
        return filename[:-3]
    return None


# --------------------------------------------------------------------------- #
# Cutoff arithmetic (calendar months, day-clamped).
# --------------------------------------------------------------------------- #
def _shift_months(today: date, months: int) -> date:
    """Today minus ``months`` calendar months, clamped to a real day.

    2026-03-31 minus one month is 2026-02-28: the cutoff is a real date in
    the target month, never an overflowed fake one.
    """
    total = today.year * 12 + (today.month - 1) - months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(today.day, last_day))


def _validate_months(months: int, origin: str) -> int:
    if not isinstance(months, int) or months < 1 or months > MAX_RETENTION_MONTHS:
        raise RetentionUsageError(
            f"{origin} must be an integer between 1 and {MAX_RETENTION_MONTHS} "
            f"(calendar months); got {months!r}"
        )
    return months


# --------------------------------------------------------------------------- #
# Facts file (the existing TOML-fence pattern).
# --------------------------------------------------------------------------- #
def _facts_value(start_dir: Path, key: str) -> str | None:
    """Read one ``key = value`` line from the repo facts TOML fence.

    Mirrors the existing facts TOML pattern (the `````toml` fence in
    ``.ai-playbook/facts.md``): the first fenced block only, quoted values
    preferred, bare values accepted. Returns None when the file or the key
    is absent; never raises.
    """
    facts_path = Path(start_dir) / ".ai-playbook" / "facts.md"
    if not facts_path.is_file():
        return None
    try:
        text = facts_path.read_text(encoding="utf-8")
    except OSError:
        return None
    quoted = re.compile(r"^\s*" + re.escape(key) + r'\s*=\s*"([^"]*)"\s*$')
    bare = re.compile(r"^\s*" + re.escape(key) + r"\s*=\s*([^\s#]+)\s*$")
    in_toml = False
    for line in text.splitlines():
        if not in_toml:
            if line.lstrip().startswith("```toml"):
                in_toml = True
            continue
        if line.lstrip().startswith("```"):
            break
        match = quoted.match(line)
        if match is not None:
            return match.group(1).strip()
        match = bare.match(line)
        if match is not None:
            return match.group(1).strip()
    return None


def _resolve_months(start_dir: Path, flag_months: int | None) -> tuple[int, str]:
    """Resolve the retention window: flag, then facts key, then default."""
    if flag_months is not None:
        return _validate_months(flag_months, "--months"), "flag"
    raw = _facts_value(start_dir, MONTHS_KEY)
    if raw is not None:
        try:
            months = int(raw, 10)
        except ValueError:
            raise RetentionUsageError(
                f"the facts key {MONTHS_KEY} must be an integer number of "
                f"calendar months; got {raw!r}"
            ) from None
        return _validate_months(months, f"facts key {MONTHS_KEY}"), "facts"
    return DEFAULT_RETENTION_MONTHS, "default"


def _resolve_against(raw: str | Path, anchor: Path) -> Path:
    """Resolve a configured path against the anchor (the process cwd).

    Relative facts values (``docs/reviews/``) anchor at the cwd, matching
    the existing facts resolution behavior; the result is realpathed so
    every later comparison and every printed path is one canonical
    spelling.
    """
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = anchor / path
    return Path(os.path.realpath(path))


# --------------------------------------------------------------------------- #
# Discovery and classification.
# --------------------------------------------------------------------------- #
def _is_excluded(path: Path, excluded_roots: list[Path]) -> bool:
    """True when ``path`` is an excluded root or lives under one.

    Both sides are realpathed by the callers, so the comparison is on one
    canonical spelling and a tmp-dir subtree is skipped even when a
    ``--reviews-dir`` override points at its parent.
    """
    for root in excluded_roots:
        if path == root:
            return True
        try:
            path.relative_to(root)
        except ValueError:
            continue
        return True
    return False


def _realpath(path: Path) -> Path:
    return Path(os.path.realpath(path))


def discover(
    reviews_dirs: list[Path], excluded_roots: list[Path]
) -> tuple[list[RecordUnit], list[Path]]:
    """Walk the reviews directories and group record files into units.

    Only ``*.md`` and ``*.stats.json`` files are record-shaped; everything
    else is invisible to retention. The excluded roots (the tmp dir) are
    pruned from the walk so their subtree is never scanned. Units come
    back sorted by (directory, base); missing directories are reported,
    not fatal.
    """
    units: dict[tuple[str, str], RecordUnit] = {}
    missing: list[Path] = []
    for reviews_dir in reviews_dirs:
        if not reviews_dir.is_dir():
            missing.append(reviews_dir)
            continue
        for root, dirs, files in os.walk(reviews_dir):
            root_path = Path(root)
            dirs[:] = sorted(
                name
                for name in dirs
                if not _is_excluded(_realpath(root_path / name), excluded_roots)
            )
            for filename in sorted(files):
                path = root_path / filename
                if _is_excluded(_realpath(path), excluded_roots):
                    continue
                role = _record_role(filename)
                if role is None:
                    continue
                base = _unit_base(filename)
                if not base:
                    continue
                key = (str(root_path), base)
                unit = units.get(key)
                if unit is None:
                    unit = RecordUnit(directory=root_path, base=base)
                    units[key] = unit
                if role == "markdown":
                    unit.markdown = path
                else:
                    unit.sidecar = path
    ordered = sorted(
        units.values(), key=lambda unit: (str(unit.directory), unit.base)
    )
    return ordered, missing


def _matching_keep(unit: RecordUnit, keep_paths: list[Path]) -> Path | None:
    """The first keep rule matching one of the unit's files, if any.

    A keep rule matches by exact file path or by directory prefix (the
    kept subtree). Deterministic: keep paths are compared in their sorted
    order.
    """
    resolved_files = [_realpath(path) for path in unit.files]
    for keep in keep_paths:
        for path in resolved_files:
            if path == keep:
                return keep
            try:
                path.relative_to(keep)
            except ValueError:
                continue
            return keep
    return None


def classify(
    units: list[RecordUnit], cutoff: date, keep_paths: list[Path]
) -> Classification:
    """Fill the retention buckets for one cutoff and keep-rule set.

    Bucket order decides precedence: undated first (never auto-pruned),
    then unpaired (retained for explicit review regardless of window),
    then the window comparison on the filename date, then the keep rules.
    A record dated exactly on the cutoff is in-window, not stale.
    """
    result = Classification()
    for unit in units:
        unit_date = unit.filename_date
        if unit_date is None:
            result.undated.append(unit)
            continue
        if unit.pairing != "pair":
            result.unpaired.append(unit)
            continue
        if unit_date >= cutoff:
            result.in_window.append(unit)
            continue
        keep_hit = _matching_keep(unit, keep_paths)
        if keep_hit is not None:
            result.kept.append((unit, keep_hit))
        else:
            result.candidates.append(unit)
    return result


# --------------------------------------------------------------------------- #
# Deterministic report.
# --------------------------------------------------------------------------- #
def _unit_line(unit: RecordUnit, keep: Path | None = None) -> str:
    """One unit line: directory, filename date, kind, pairing, base.

    Structured fields only; no document bodies ever.
    """
    shown_date = unit.filename_date.isoformat() if unit.filename_date else "none"
    line = (
        f"- dir={unit.directory} date={shown_date} kind={unit.kind} "
        f"pairing={unit.pairing} base={unit.base}"
    )
    if keep is not None:
        line += f" keep={keep}"
    return line


def render_report(
    mode: str,
    cutoff: date,
    months: int,
    months_source: str,
    tmp_dir: Path,
    reviews_dirs: list[Path],
    missing_dirs: list[Path],
    keep_paths: list[Path],
    buckets: Classification,
    deletions_performed: int,
    manifest_check: str,
    docs_branch_leg: str,
    docs_branch: str,
) -> str:
    """Render the byte-stable retention report.

    Determinism rules: no timestamps, every section in a fixed order,
    every unit list in the discovery sort order, every path in its
    canonical resolved spelling. Two consecutive runs on an unchanged
    tree emit identical bytes.
    """
    lines: list[str] = []
    lines.append("review retention report")
    lines.append(f"mode: {mode}")
    lines.append(f"cutoff: {cutoff.isoformat()}")
    lines.append(f"months: {months} (source: {months_source})")
    lines.append(f"tmp_dir (never scanned): {tmp_dir}")
    lines.append("reviews_dirs:")
    for directory in reviews_dirs:
        lines.append(f"- {directory}")
    if missing_dirs:
        lines.append("reviews_dirs_missing:")
        for directory in missing_dirs:
            lines.append(f"- {directory}")
    lines.append("keep_paths:")
    if keep_paths:
        for keep in keep_paths:
            lines.append(f"- {keep}")
    else:
        lines.append("- (none)")
    candidate_files = 2 * len(buckets.candidates)
    lines.append(
        f"candidates: {len(buckets.candidates)} unit(s), "
        f"{candidate_files} file(s)"
    )
    for unit in buckets.candidates:
        lines.append(_unit_line(unit))
    lines.append(f"unpaired_retained: {len(buckets.unpaired)} unit(s)")
    for unit in buckets.unpaired:
        lines.append(_unit_line(unit))
    lines.append(f"undated_retained: {len(buckets.undated)} unit(s)")
    for unit in buckets.undated:
        lines.append(_unit_line(unit))
    lines.append(f"in_window_retained: {len(buckets.in_window)} unit(s)")
    lines.append(f"kept_by_rule: {len(buckets.kept)} unit(s)")
    for unit, keep in buckets.kept:
        lines.append(_unit_line(unit, keep=keep))
    lines.append(f"docs_branch_leg: {docs_branch_leg} (branch: {docs_branch})")
    lines.append(
        "summary: "
        f"mode={mode} "
        f"candidate_units={len(buckets.candidates)} "
        f"candidate_files={candidate_files} "
        f"unpaired_retained={len(buckets.unpaired)} "
        f"undated_retained={len(buckets.undated)} "
        f"in_window_retained={len(buckets.in_window)} "
        f"kept_by_rule={len(buckets.kept)} "
        f"deletions_performed={deletions_performed} "
        f"manifest_check={manifest_check} "
        f"docs_branch_leg={docs_branch_leg}"
    )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Sanitized manifest.
# --------------------------------------------------------------------------- #
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_entries(buckets: Classification) -> list[dict]:
    """Per-file entries (path, sha256, role, unit_base, date) for candidates.

    The manifest carries paths and hashes only: no review text and no
    document bodies ever reach it.
    """
    entries: list[dict] = []
    for unit in buckets.candidates:
        unit_date = unit.filename_date
        for path, role in (
            (unit.markdown, "markdown"),
            (unit.sidecar, "sidecar"),
        ):
            if path is None:
                continue
            entries.append(
                {
                    "path": str(_realpath(path)),
                    "sha256": _sha256_file(path),
                    "role": role,
                    "unit_base": unit.base,
                    "date": unit_date.isoformat() if unit_date else "",
                }
            )
    entries.sort(key=lambda entry: entry["path"])
    return entries


def build_manifest(
    mode: str,
    cutoff: date,
    months: int,
    months_source: str,
    reviews_dirs: list[Path],
    keep_paths: list[Path],
    entries: list[dict],
    buckets: Classification,
    deleted_files: int | None,
) -> dict:
    counts = {
        "candidate_units": len(buckets.candidates),
        "candidate_files": 2 * len(buckets.candidates),
        "unpaired_retained": len(buckets.unpaired),
        "undated_retained": len(buckets.undated),
        "in_window_retained": len(buckets.in_window),
        "kept_by_rule": len(buckets.kept),
    }
    if deleted_files is not None:
        counts["deleted_files"] = deleted_files
    return {
        "schema": MANIFEST_SCHEMA,
        "mode": mode,
        "cutoff": cutoff.isoformat(),
        "months": months,
        "months_source": months_source,
        "counts": counts,
        # The caller passes the entries computed BEFORE any deletion, so a
        # prune-completion manifest carries the verified pre-deletion
        # hashes instead of re-reading the removed files.
        "candidates": entries,
        "reviews_dirs": [str(directory) for directory in reviews_dirs],
        "keep_paths": [str(keep) for keep in keep_paths],
    }


def load_manifest(path: Path) -> dict:
    """Load and structurally validate a retention manifest (exit 2 on junk)."""
    if not path.is_file():
        raise RetentionUsageError(
            f"manifest not found: {path}; run a dry run with --manifest PATH "
            "to record the candidate set first"
        )
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RetentionUsageError(f"unreadable manifest {path}: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != MANIFEST_SCHEMA:
        raise RetentionUsageError(
            f"unsupported manifest schema in {path}: expected "
            f"{MANIFEST_SCHEMA!r}"
        )
    entries = doc.get("candidates")
    if not isinstance(entries, list):
        raise RetentionUsageError(
            f"manifest {path} carries no candidates list"
        )
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("path"), str)
            or not isinstance(entry.get("sha256"), str)
        ):
            raise RetentionUsageError(
                f"manifest {path} has a candidate entry without string "
                "path and sha256 fields"
            )
    return doc


def drift_lines(recorded: list[dict], current: list[dict]) -> list[str]:
    """Compare a recorded candidate set against the freshly scanned one.

    The sets must match exactly (same paths, same per-file hashes); any
    missing, added, or content-changed file is drift and blocks the prune.
    """
    recorded_map = {_realpath(Path(e["path"])): e["sha256"] for e in recorded}
    current_map = {_realpath(Path(e["path"])): e["sha256"] for e in current}
    lines: list[str] = []
    for path in sorted(set(recorded_map) - set(current_map)):
        lines.append(f"drift missing_from_directory: {path}")
    for path in sorted(set(current_map) - set(recorded_map)):
        lines.append(f"drift added_in_directory: {path}")
    for path in sorted(set(recorded_map) & set(current_map)):
        if recorded_map[path] != current_map[path]:
            lines.append(f"drift content_changed: {path}")
    return lines


# --------------------------------------------------------------------------- #
# Prune (pairing-aware deletion).
# --------------------------------------------------------------------------- #
def prune_units(units: list[RecordUnit]) -> int:
    """Delete each candidate pair as one unit; report a torn state loudly.

    The sidecar is removed before the Markdown half. If any unlink fails,
    the refusal names the exact torn state (which half of which unit was
    already removed) so the caller can repair explicitly.
    """
    deleted = 0
    for unit in units:
        removed_here: list[str] = []
        for path in (unit.sidecar, unit.markdown):
            if path is None:
                continue
            try:
                path.unlink()
            except OSError as exc:
                raise RetentionRefused(
                    f"failed to remove {path} ({exc}); the record unit "
                    f"{unit.base} is now torn: already removed in this step: "
                    f"{removed_here or 'nothing'}; remove or restore the "
                    "remaining half explicitly before retrying"
                ) from exc
            removed_here.append(path.name)
            deleted += 1
    return deleted


# --------------------------------------------------------------------------- #
# docs-branch deletion transaction (the explicit-delete producer).
# --------------------------------------------------------------------------- #
def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run one git invocation against ``repo`` with captured output."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _git_refuses(repo: Path, *args: str) -> bool:
    return _git(repo, *args, check=False).returncode != 0


def _validate_docs_branch(branch: str) -> str:
    """Validate the --docs-branch override (exit 2 on a junk name).

    The docs-branch skill's single-branch invariant allows exactly one
    shadow branch per repository (its name is ``docs``); the override
    exists for hermetic tests, so namespaced ``docs/...`` style variants
    are rejected here as the skill forbids them.
    """
    if (
        not branch
        or branch != branch.strip()
        or branch.startswith("-")
        or any(character.isspace() for character in branch)
        or "/" in branch
    ):
        raise RetentionUsageError(
            "--docs-branch must be a single branch name without whitespace "
            f"or path separators; got {branch!r}"
        )
    return branch


def docs_branch_commit_transaction(
    repo: Path, branch: str, live_paths: list[Path]
) -> tuple[str, list[str]]:
    """Record the candidate removals as an explicit-delete commit.

    Builds on the docs-branch skill's explicit-delete rule (only paths
    removed in the latest docs commit are dropped from the sync's
    restore path, so the commit is what makes a live prune durable):

    1. skip entirely (zero mutations) when ``repo`` is not a git repo or
       the branch does not exist;
    2. ``git worktree add`` the branch at a temp path OUTSIDE the repo;
       the live checkout never holds the branch;
    3. remove the branch-tracked candidate paths there and stage the
       removals;
    4. commit, then verify the commit: the latest branch commit must
       record every staged path as deleted (``--diff-filter=D``) and the
       branch tip must no longer track it;
    5. remove the temporary worktree on every path (success, refusal,
       exception).

    Returns ``(status, removed_rel_paths)``; raises ``RetentionRefused``
    on any git failure BEFORE the caller touches the live tree. When the
    branch exists but tracks none of the candidates there is nothing to
    record (and nothing a later sync could restore), so the live prune
    stays durable without a commit; that is the ``no-tracked-deletions``
    status, not a refusal.
    """
    if _git_refuses(repo, "rev-parse", "--git-dir"):
        return DOCS_LEG_SKIPPED, []
    if _git_refuses(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"):
        return DOCS_LEG_SKIPPED, []
    top = _git(repo, "rev-parse", "--show-toplevel").stdout.strip()
    top_real = _realpath(Path(top))
    rel_paths: list[str] = []
    for path in live_paths:
        real = _realpath(path)
        try:
            relative = real.relative_to(top_real)
        except ValueError:
            raise RetentionRefused(
                f"candidate path {real} lies outside the repository rooted "
                f"at {top_real}; it cannot be recorded on branch {branch}"
            ) from None
        rel_paths.append(relative.as_posix())
    rel_paths.sort()

    worktree_parent = Path(
        tempfile.mkdtemp(prefix="review-retention-docs-worktree.")
    )
    worktree = worktree_parent / "worktree"
    try:
        added = _git(repo, "worktree", "add", str(worktree), branch, check=False)
        if added.returncode != 0:
            raise RetentionRefused(
                f"failed to add a temporary worktree for branch {branch}: "
                f"{added.stderr.strip()}"
            )
        head = _git(worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if head != branch:
            raise RetentionRefused(
                f"the temporary worktree holds {head!r}, not {branch!r}; "
                "refusing to stage deletions outside the docs branch"
            )
        tracked: list[str] = []
        for rel in rel_paths:
            listed = _git(worktree, "ls-files", "--", rel, check=False)
            if listed.returncode != 0 or not listed.stdout.strip():
                continue
            tracked.append(rel)
            removed = _git(worktree, "rm", "-q", "-f", "--", rel, check=False)
            if removed.returncode != 0:
                raise RetentionRefused(
                    f"failed to stage the removal of {rel} in the temporary "
                    f"{branch} worktree: {removed.stderr.strip()}"
                )
        staged = sorted(
            set(
                _git(
                    worktree,
                    "diff",
                    "--cached",
                    "--name-only",
                    "--diff-filter=D",
                ).stdout.splitlines()
            )
        )
        if not staged:
            return DOCS_LEG_NOOP, []
        committed = _git(
            worktree,
            "commit",
            "-q",
            "-m",
            f"docs: review retention explicit delete of {len(staged)} "
            "pruned review path(s)",
            check=False,
        )
        if committed.returncode != 0:
            raise RetentionRefused(
                f"the {branch} retention commit failed: "
                f"{committed.stderr.strip()}"
            )
        # Verify BEFORE any live mutation: the latest branch commit must
        # record every staged path as a deletion and the tip must no
        # longer track it (the docs-branch skill's own explicit-delete
        # query shape, so its restore path will honor the removals).
        tip = _git(repo, "rev-parse", f"refs/heads/{branch}").stdout.strip()
        recorded = set(
            _git(
                repo,
                "diff-tree",
                "-r",
                "--no-commit-id",
                "--name-only",
                "--diff-filter=D",
                tip,
            ).stdout.splitlines()
        )
        unrecorded = [rel for rel in staged if rel not in recorded]
        if unrecorded:
            raise RetentionRefused(
                f"verification failed: the latest {branch} commit does not "
                f"record removals for: {', '.join(unrecorded)}"
            )
        for rel in staged:
            still_tracked = _git(
                repo,
                "ls-tree",
                "-r",
                "--name-only",
                f"refs/heads/{branch}",
                "--",
                rel,
                check=False,
            )
            if still_tracked.stdout.strip():
                raise RetentionRefused(
                    f"verification failed: {rel} is still tracked at the "
                    f"tip of {branch}"
                )
        return DOCS_LEG_COMMITTED, staged
    finally:
        _git(repo, "worktree", "remove", "--force", str(worktree), check=False)
        shutil.rmtree(worktree_parent, ignore_errors=True)
        _git(repo, "worktree", "prune", check=False)


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _add_scan_arguments(parser: argparse.ArgumentParser) -> None:
    """The arguments shared by the default mode and ``docs-branch-commit``."""
    parser.add_argument(
        "--from-manifest",
        metavar="PATH",
        help="manifest gating the mutation; its recorded candidate set must "
        "still match the directory exactly (paths and hashes)",
    )
    parser.add_argument(
        "--manifest",
        metavar="PATH",
        help="write the sanitized manifest: the candidate set in dry-run "
        "mode, the deleted set after a completed prune or transaction",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=None,
        help=f"retention window override in calendar months "
        f"(default: the {MONTHS_KEY} facts key, else "
        f"{DEFAULT_RETENTION_MONTHS})",
    )
    parser.add_argument(
        "--keep",
        action="append",
        default=[],
        metavar="PATH",
        help="exclude a file path (or a directory subtree) from candidacy; "
        "repeatable",
    )
    parser.add_argument(
        "--reviews-dir",
        action="append",
        default=[],
        metavar="PATH",
        help="reviews directory to scan; repeatable; overrides the "
        f"{REVIEWS_DIR_KEY} facts key",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="review_retention",
        description=(
            "Review artifact retention: deterministic dry-run candidate "
            "report, pairing-aware manifest-gated pruning, sanitized "
            "manifests, and the docs-branch-commit deletion transaction. "
            "Cutoff by filename date, never mtime; the tmp dir is never "
            "scanned; unpaired and undated records are never auto-pruned."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="explicit dry run (the default mode); deletes nothing",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="delete the manifest-matched candidate pairs as units in the "
        "LIVE tree only; requires --from-manifest; for a durable prune use "
        "the docs-branch-commit subcommand instead",
    )
    _add_scan_arguments(parser)
    subparsers = parser.add_subparsers(dest="command", metavar="subcommand")
    docs_commit = subparsers.add_parser(
        "docs-branch-commit",
        help="manifest-gated deletion transaction: commit the candidate "
        "removals as a verified explicit-delete commit on the docs branch "
        "through a temporary worktree, then remove the live shadow files",
        description=(
            "Full retention transaction: manifest drift gate, then an "
            "explicit-delete commit on the docs branch (default docs, "
            "--docs-branch override) built in a temporary worktree the "
            "live checkout never holds, verified, and only then the "
            "pairing-aware live prune. With no docs branch the leg is "
            "reported as skipped and nothing is mutated."
        ),
    )
    _add_scan_arguments(docs_commit)
    docs_commit.add_argument(
        "--docs-branch",
        default=DEFAULT_DOCS_BRANCH,
        metavar="BRANCH",
        help=f"shadow branch to record the deletions on "
        f"(default: {DEFAULT_DOCS_BRANCH})",
    )
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.dry_run and args.prune:
        raise RetentionUsageError(
            "--dry-run and --prune are mutually exclusive: the default mode "
            "is already a dry run"
        )
    is_transaction = args.command == "docs-branch-commit"
    if is_transaction and (args.dry_run or args.prune):
        raise RetentionUsageError(
            "docs-branch-commit is its own mode; do not combine it with "
            "--dry-run or --prune"
        )
    if is_transaction and not args.from_manifest:
        raise RetentionUsageError(
            "docs-branch-commit requires --from-manifest PATH: the "
            "transaction is manifest-gated, and the recorded candidate set "
            "must still match the directory exactly"
        )
    if args.prune and not args.from_manifest:
        raise RetentionUsageError(
            "--prune requires --from-manifest PATH: deletion is "
            "manifest-gated, and the recorded candidate set must still "
            "match the directory exactly"
        )

    anchor = Path.cwd()
    months, months_source = _resolve_months(anchor, args.months)
    today = DATE_SOURCE()
    cutoff = _shift_months(today, months)

    tmp_dir = _resolve_against(
        _facts_value(anchor, TMP_DIR_KEY) or DEFAULT_TMP_DIR, anchor
    )
    if args.reviews_dir:
        reviews_dirs = sorted(
            {_resolve_against(raw, anchor) for raw in args.reviews_dir}
        )
    else:
        reviews_raw = _facts_value(anchor, REVIEWS_DIR_KEY) or DEFAULT_REVIEWS_DIR
        reviews_dirs = [_resolve_against(reviews_raw, anchor)]
    keep_paths = sorted({_realpath(Path(raw)) for raw in args.keep})

    units, missing_dirs = discover(reviews_dirs, [tmp_dir])
    buckets = classify(units, cutoff, keep_paths)
    # Entries are computed once, BEFORE any mutation: the drift check and
    # the manifest both consume the same verified pre-deletion hashes.
    entries = candidate_entries(buckets)

    manifest_check = "skipped"
    if args.from_manifest:
        manifest = load_manifest(Path(args.from_manifest))
        drift = drift_lines(manifest["candidates"], entries)
        if drift:
            print(
                "ERROR: manifest drift: the recorded candidate set no "
                "longer matches the directory; zero deletions performed",
                file=sys.stderr,
            )
            for line in drift:
                print(line, file=sys.stderr)
            return 1
        manifest_check = "matched"

    docs_branch = DEFAULT_DOCS_BRANCH
    docs_leg = DOCS_LEG_NA
    deleted = 0
    if is_transaction:
        docs_branch = _validate_docs_branch(
            getattr(args, "docs_branch", DEFAULT_DOCS_BRANCH)
        )
        # The docs leg runs entirely before the live prune: any refusal
        # here leaves every live shadow file in place, and the skip case
        # (no repo, no docs branch) mutates nothing on either side.
        candidate_files = [
            path
            for unit in buckets.candidates
            for path in (unit.markdown, unit.sidecar)
            if path is not None
        ]
        docs_leg, _removed = docs_branch_commit_transaction(
            anchor, docs_branch, candidate_files
        )
        if docs_leg != DOCS_LEG_SKIPPED:
            deleted = prune_units(buckets.candidates)
        mode = "docs-branch-commit"
    elif args.prune:
        deleted = prune_units(buckets.candidates)
        mode = "prune"
    else:
        mode = "dry-run"

    if args.manifest:
        doc = build_manifest(
            mode,
            cutoff,
            months,
            months_source,
            reviews_dirs,
            keep_paths,
            entries,
            buckets,
            deleted_files=deleted if (args.prune or is_transaction) else None,
        )
        manifest_path = Path(args.manifest)
        manifest_path.write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print(
        render_report(
            mode=mode,
            cutoff=cutoff,
            months=months,
            months_source=months_source,
            tmp_dir=tmp_dir,
            reviews_dirs=reviews_dirs,
            missing_dirs=missing_dirs,
            keep_paths=keep_paths,
            buckets=buckets,
            deletions_performed=deleted,
            manifest_check=manifest_check,
            docs_branch_leg=docs_leg,
            docs_branch=docs_branch,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except RetentionRefused as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except RetentionUsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
