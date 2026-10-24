#!/usr/bin/env python3
"""Prompt-log origin checker: flags PLAN-PROMPTS.md entries whose every
origin is served.

The tracked rolling prompt log docs/history/backlog/PLAN-PROMPTS.md holds
one ``## <slug>`` section per ready-to-dispatch authoring entry, each
listing its backlog origins. The log's own prune rule removes an entry
when its plan file lands, but nothing mechanical verifies the landed
log, so an all-served entry can sit dispatchable for hours past its
plan's full lifecycle (the witnessed 2026-09-30 drift). This checker
reads the log (sections after the entry-template fence only; the fenced
template placeholders are never parsed as an entry), collects each
entry's ``Origins:`` lines, and classifies every origin:

- SERVED when the origin file's first ``Status:`` line (bullet or bare,
  at any header depth, first such line only) reads ``done`` or
  ``covered``, or when the origin file is absent from the backlog top
  level because it sits in a served archive state directory
  (``completed/``, ``rejected/``, resolved by basename and reported
  with the resolved path relative to the backlog directory), or when
  the earlier lookups left the origin live and it is absent from the
  HEAD tree (an uncommitted working-tree re-add is dirt, not presence)
  while its resolved backlog-relative path (the backlog directory's
  repo-relative path joined with the basename) carries a reachable
  deletion commit, reported as ``deleted in <commit>`` (the
  covered-row deletion shape; the commit witnesses the removal for
  audit, never the completion itself).
- DEFERRED when the origin file resolves only into the deferred archive
  state directory (``deferred/``): a deferral is still-actionable work,
  neither completed nor rejected, so it carries its own line class and
  never serves an entry.
- LIVE otherwise: a present file with no or a novel status and no
  HEAD-tree deletion evidence, or an absent file with no deletion
  commit. A missing
  or unparseable status is not by itself a finding; only done/covered
  prefixes and absent files are findings, so the checker stays
  fail-open for novel statuses and fail-closed only for the witnessed
  drift classes.

The deleted-origin arm is consulted only for an origin the earlier
lookups left live, at this check layer (the shared classifier also
serves the collateral mode, where a deletion outside the audited range
must not flip the verdict). A git plumbing failure on its lookup
(nonzero exit, timeout, missing binary, non-decodable output, an
argument the git process refuses) is no deletion evidence: one
``deletion-lookup:`` stderr line per failed lookup naming the origin
path and the failure class, one ``deletion-lookup failures: N`` stdout
line per invocation when any lookup failed, never an uncaught
exception; a log outside any git repository silences the arm outright.

An entry is STALE only when EVERY origin is served (a mixed entry still
carries unlanded work and stays, and a deferred origin is unlanded
work). Exit 1 for a stale entry, 0 otherwise. Frozen entries are
checked like any other: a frozen entry whose origins are all served is
exactly the witnessed wedge, and the freeze rule itself already orders
its prune.

The ``--prune-audit --base <ref>`` mode is the log's removal audit: it
walks the commits that touched the log in ``base..HEAD`` oldest-first,
parses each removal from the log diff (a deleted ``## <slug>`` heading
outside the entry-template fence; fence state starts each hunk from the
removal commit's own pre- and post-image and is then tracked through the
added, removed, and context lines, so state survives hunk boundaries),
and classifies every removed entry against its plan-file witness at the
removal commit's tree: PRUNE-OK when a plans-root file, its
``completed/`` archive twin, or the plan-directory shape's charter path
``<slug>/PLAN.md`` at either depth (keyed on the slug directory name)
carries the slug as hyphen-bounded segments; SUPERSEDED-IN-COMMIT (report-only, never a flag) when the same
commit also adds an entry heading; REMOVED-WITHOUT-WITNESS (the flag)
otherwise. The audit enumerates both tracked rolling logs: when the
audited path is one of the two logs, its sibling
(``docs/history/backlog/EXEC-PROMPTS.md`` or
``docs/history/backlog/PLAN-PROMPTS.md``) rides the same audit window,
so one invocation covers both. Beside the plan-file witness, the audit
accepts the ad-hoc-superseded removal class's receipt witness (added
2026-10-06, the two-mode loop policy plan): a removal whose own commit
message carries ``EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>``
naming the removed slug, with the landing commit resolving to an
existing commit, is PRUNE-OK (the recorded landing commit digest
substitutes for the plans-root witness where no plan file exists); a
receipt naming a different slug, or whose landing commit does not
resolve, never witnesses. The audit also accepts the log charter's own
receipt ledger form (the in-log ``PLAN-PROMPTS-PRUNE:`` /
``EXEC-PROMPTS-PRUNE:`` line per removed entry, trailing rationale
prose tolerated): when the removal's own log post-image carries such a
line naming the removed slug and its token resolves (a commit digest,
or a path present in the removal commit's tree), the removal is
PRUNE-OK (log ledger receipt). A newly added line of that same shape
whose token is the literal ``landing`` (the logs' receipt form for a
removal receipted in its own commit) is the in-commit receipt and
joins the same log-ledger count; the match is a per-log
``(slug, token)`` count delta between the log's pre-image and
post-image, so a pre-existing (earlier) ``landing`` line never
qualifies and a sibling-log receipt cannot cross-witness. The evidence
classes keep that fixed precedence: plan-file witness, then
commit-message receipt, then the
log's own ledger line; a removal classified by an earlier class never
consults later ones, and each log's removals consult only that log's
post-image. The audit classifies mechanically; the
consultative leg adjudicates: ranges are expected to start after the
pNNN-to-dispatch-log transition, and the landing leg never spans the
pre-plan-era wave commits. Exit 1 when any removal lacks its witness,
0 otherwise, 3 for a tool error (a missing log at the audit path, an
unresolvable base ref, or a git plumbing failure), each with the final
``OUTCOME:`` line per scripts/OUTCOME_CONTRACT.md.

The default log path resolves against this script's own repo root,
never the caller's cwd (the pins sweep promises run-from-anywhere and
never cds); an explicit log path is audited in the repository that
contains it, and every git plumbing call passes the audited repository
root as its working directory. Stdlib plus the sibling shared resolver
(``plan_shape.py`` beside this script, the charter filename's grammar
home) only; no network.
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path
from typing import TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    # The charter filename is the shared resolver's grammar constant (the
    # one grammar derivation every consumer imports); the prune-witness
    # grammar only matches the charter path in the ls-tree listing.
    from plan_shape import CHARTER_FILENAME
except ImportError:  # deployment gap: the witness grammar fails closed (tool error)
    CHARTER_FILENAME = None  # type: ignore[assignment]

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
DEFAULT_LOG_REL = "docs/history/backlog/PLAN-PROMPTS.md"
# The served archive states: a file found under one of these classifies
# its origin as served (work complete). The deferred state is
# deliberately absent from this tuple: a deferral is still-actionable
# work, so it resolves through its own named constant and lookup below
# and never serves an entry.
ARCHIVE_DIR_NAMES = ("completed", "rejected")
# The deferred archive state: an operator deferral order moves a row
# here; a hit resolves for reporting only.
DEFERRED_DIR_NAME = "deferred"
# The still-actionable note carried by a deferred origin's report
# detail: a deferral is neither completed nor rejected, so it never
# serves its entry.
DEFERRED_NOTE = "still actionable: deferred is neither completed nor rejected"
# The deleted-origin arm's stderr diagnostic prefix: one line per failed
# lookup, naming the origin path and the failure class.
DELETION_LOOKUP_PREFIX = "deletion-lookup"
PLANS_ROOT_REL = "docs/history/plans"

# The two tracked rolling logs: the prune-audit and the collateral
# discovery each enumerate both, the audited log's sibling riding the
# same audit window (the ad-hoc-superseded
# removal class lands in either log, so one window must cover both).
SIBLING_LOG_RELS = {
    "docs/history/backlog/PLAN-PROMPTS.md": "docs/history/backlog/EXEC-PROMPTS.md",
    "docs/history/backlog/EXEC-PROMPTS.md": "docs/history/backlog/PLAN-PROMPTS.md",
}
# The ad-hoc-superseded removal class's receipt line (the pruning commit's
# own message): the removed slug and the landing commit digest that
# substitutes for the plans-root witness where no plan file exists.
RECEIPT_LINE_RE = re.compile(
    r"^EXEC-PROMPTS-PRUNE:[ \t]+(\S+)[ \t]+->[ \t]+(\S+)[ \t]*$",
    re.MULTILINE,
)

# The receipt ledger's line grammar, scoped to the rolling log's own
# receipt lines (one per removed entry per the log charter): both
# prefixes are accepted and trailing rationale prose after the token is
# tolerated, because the real lines read
# ``PLAN-PROMPTS-PRUNE: <slug> -> <token> (<reason prose>)``. This is
# the in-log ledger grammar only; the commit-message scan above keeps
# its strict anchored end-of-line shape unchanged.
LEDGER_RECEIPT_LINE_RE = re.compile(
    r"^(?:PLAN-PROMPTS-PRUNE|EXEC-PROMPTS-PRUNE):[ \t]+(\S+)[ \t]+->[ \t]+(\S+)",
    re.MULTILINE,
)

# One entry per ``## <slug>`` section, per the log's entry template.
ENTRY_HEADING_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$")
ORIGINS_HEADER_RE = re.compile(r"^[ \t]*Origins[ \t]*:[ \t]*$")
ORIGIN_ITEM_RE = re.compile(r"^[ \t]*-[ \t]+(\S+\.md)[ \t]*$")
# Any line opening with a fence toggles fenced state; the entry template
# lives inside one, and its placeholder ``## <short-slug>`` heading and
# ``Origins:`` lines must never parse as an entry.
FENCE_LINE_RE = re.compile(r"^[ \t]*```")

# The corpus status shapes ``Status: open`` and ``- **Status:** covered
# (...): optional bullet, optional bold around the label and the value.
STATUS_LINE_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]*)?(?:\*\*)?[ \t]*status(?:\*\*)?[ \t]*:"
    r"[ \t]*(?:\*\*)?[ \t]*(.+?)[ \t]*$",
    re.IGNORECASE,
)
# served status VALUES; a hyphenated continuation such as ``done-phony``
# is not a done declaration (mirrors the backlog corpus gate).
SERVED_STATUS_RE = re.compile(r"^(?:done|covered)(?![A-Za-z0-9_-])", re.IGNORECASE)

# The prune-audit mode's patch hunk header (unified diff): the 1-based
# old and new start lines drive the per-hunk fence-state bootstrap.
HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
ZERO_SHA_RE = re.compile(r"^0+$")


class AuditToolError(Exception):
    """A git plumbing failure inside the prune-audit walk; carried to the
    mode's tool-error exit with the final OUTCOME line."""


def parse_entries(text: str) -> list[tuple[str, list[str]]]:
    """(slug, origin paths) per ``## `` section after the template fence,
    in file order. Content inside a fenced block is skipped entirely."""
    entries: list[tuple[str, list[str]]] = []
    slug: str | None = None
    origins: list[str] = []
    in_origins = False
    in_fence = False
    for line in text.splitlines():
        if FENCE_LINE_RE.match(line):
            in_fence = not in_fence
            in_origins = False
            continue
        if in_fence:
            continue
        heading = ENTRY_HEADING_RE.match(line)
        if heading:
            if slug is not None:
                entries.append((slug, origins))
            slug = heading.group(1).strip()
            origins = []
            in_origins = False
            continue
        if slug is None:
            continue
        if in_origins:
            item = ORIGIN_ITEM_RE.match(line)
            if item:
                origins.append(item.group(1))
                continue
            in_origins = False
        if ORIGINS_HEADER_RE.match(line):
            in_origins = True
    if slug is not None:
        entries.append((slug, origins))
    return entries


def first_status(origin_path: Path) -> str | None:
    """The file's first ``Status:`` line value (bullet or bare, at any
    header depth), or None when the file has none or is unreadable."""
    try:
        text = origin_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        match = STATUS_LINE_RE.match(line)
        if match:
            return match.group(1)
    return None


def resolve_in_state(state: str, basename: str, backlog_dir: Path) -> Path | None:
    """The origin's file inside one backlog archive state directory,
    resolved by basename (sorted first match), or None."""
    state_dir = backlog_dir / state
    if not state_dir.is_dir():
        return None
    for found in sorted(state_dir.rglob(basename)):
        if found.is_file():
            return found
    return None


def resolve_archive_path(basename: str, backlog_dir: Path) -> Path | None:
    """The origin's file inside a served archive state directory (the
    completed and rejected states, probed in that fixed order for the
    sorted first-match determinism), or None."""
    for state in ARCHIVE_DIR_NAMES:
        found = resolve_in_state(state, basename, backlog_dir)
        if found is not None:
            return found
    return None


def resolve_deferred_path(basename: str, backlog_dir: Path) -> Path | None:
    """The origin's file inside the deferred archive state directory,
    resolved by basename (sorted first match), or None. A hit here
    resolves for reporting only: it never serves an entry."""
    return resolve_in_state(DEFERRED_DIR_NAME, basename, backlog_dir)


def classify_origin(origin: str, backlog_dir: Path) -> tuple[str, str]:
    """(classification, report detail) for one logged origin path, the
    classification one of ``served``, ``deferred``, or ``live``. The
    detail is the raw status text for a served-by-status origin, the
    resolved archive path relative to the backlog directory for a
    served-by-archive origin, the resolved deferred path relative to the
    backlog directory plus the still-actionable note for a deferred
    origin, and empty for a live origin. Top-level presence and the
    served archive pair always win over the deferred lookup when the
    same basename exists in several states."""
    basename = Path(origin.replace("\\", "/")).name
    top = backlog_dir / basename
    if top.is_file():
        status = first_status(top)
        if status is not None and SERVED_STATUS_RE.match(status):
            return "served", status
        return "live", ""
    archived = resolve_archive_path(basename, backlog_dir)
    if archived is not None:
        return "served", archived.relative_to(backlog_dir).as_posix()
    deferred = resolve_deferred_path(basename, backlog_dir)
    if deferred is not None:
        resolved = deferred.relative_to(backlog_dir).as_posix()
        return "deferred", f"{resolved} ({DEFERRED_NOTE})"
    return "live", ""


def _git_failure_class(exc: BaseException) -> str:
    """The stable failure-class token for one raised git plumbing call;
    the deletion-lookup diagnostic names it verbatim."""
    if isinstance(exc, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(exc, FileNotFoundError):
        return "git-missing"
    if isinstance(exc, UnicodeDecodeError):
        return "decode-error"
    if isinstance(exc, ValueError):
        return "invalid-argument"
    return "os-error"


def _report_deletion_failure(subject: str, failure: str, detail: str = "") -> None:
    """One stderr diagnostic line per failed deletion lookup: the stable
    prefix, the origin path, the failure class, then the plumbing
    stderr flattened onto the same line."""
    parts = [DELETION_LOOKUP_PREFIX, subject, failure]
    flat = " ".join(detail.split())
    if flat:
        parts.append(flat)
    print(": ".join(parts), file=sys.stderr)


class _DeletionEvidence:
    """The check_log layer's deleted-origin lookup (the covered-row
    deletion served class), memoized per resolved backlog-relative path
    within one invocation.

    The arm never lives in the shared classifier: classify_origin has a
    second production consumer at the collateral mode's head-side call
    against the live repository, where a deletion outside the audited
    range must not flip the head-served verdict (the base-side call
    classifies an extracted base tree outside any repository and is
    shielded by its base-present conjunct). The repository root is resolved once from the log path
    with ``git rev-parse --show-toplevel``; a nonzero probe is the
    ordinary non-repository shape and silences the arm without a
    diagnostic. Any plumbing failure on a lookup (nonzero exit,
    timeout, missing binary, non-decodable output, an argument the
    process layer refuses such as an embedded NUL) degrades to no
    deletion evidence: one
    stderr diagnostic line naming the origin path and the failure
    class, one increment of ``failures`` for the per-invocation stdout
    summary, never a raised exception."""

    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._root: Path | None = None
        self._backlog_rel: str | None = None
        self._root_probed = False
        self._root_failed = False
        self._root_failure = ""
        self._root_reported = False
        self._evidence: dict[str, str | None] = {}
        self.failures = 0

    def deletion_detail(self, basename: str) -> str | None:
        """``deleted in <commit>`` when the basename's resolved path is
        HEAD-tree-absent and a HEAD-reachable commit deleted it, else
        None. The gate and the walk run at most once per resolved path
        per invocation."""
        root, backlog_rel = self._resolve_root()
        if root is None or backlog_rel is None:
            if self._root_failed and not self._root_reported:
                self._root_reported = True
                self._fail(
                    basename, self._root_failure, "git rev-parse --show-toplevel"
                )
            return None
        resolved_rel = f"{backlog_rel}/{basename}"
        if resolved_rel in self._evidence:
            return self._evidence[resolved_rel]
        commit = self._lookup(root, resolved_rel)
        detail = f"deleted in {commit}" if commit is not None else None
        self._evidence[resolved_rel] = detail
        return detail

    def _resolve_root(self) -> tuple[Path | None, str | None]:
        """(repository root, backlog repo-relative directory) resolved
        once per invocation from the log path. A nonzero probe is the
        quiet non-repository shape; a raised probe marks the arm failed
        for the invoking origin's diagnostic."""
        if not self._root_probed:
            self._root_probed = True
            try:
                probe = run_git(
                    self._log_path.resolve().parent, "rev-parse", "--show-toplevel"
                )
            except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
                self._root_failed = True
                self._root_failure = _git_failure_class(exc)
            else:
                if probe.returncode == 0 and probe.stdout.strip():
                    try:
                        root = Path(probe.stdout.strip()).resolve()
                        self._backlog_rel = (
                            self._log_path.resolve().parent.relative_to(root).as_posix()
                        )
                        self._root = root
                    except ValueError:
                        pass
        if self._root is None:
            return None, None
        return self._root, self._backlog_rel

    def _lookup(self, root: Path, resolved_rel: str) -> str | None:
        """The deletion commit for one resolved path, or None without
        evidence. The HEAD-tree absence gate runs first: a path present
        at HEAD was re-added after any deletion, so the deletion class
        never consults it."""
        try:
            present = (
                run_git(root, "cat-file", "-e", f"HEAD:{resolved_rel}").returncode
                == 0
            )
        except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
            self._fail(resolved_rel, _git_failure_class(exc))
            return None
        if present:
            return None
        try:
            proc = run_git(
                root,
                "log",
                "--diff-filter=D",
                "-1",
                "--format=%H",
                "--",
                f":(literal){resolved_rel}",
            )
        except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
            self._fail(resolved_rel, _git_failure_class(exc))
            return None
        if proc.returncode != 0:
            self._fail(resolved_rel, "nonzero-exit", proc.stderr)
            return None
        commit = proc.stdout.strip()
        return commit or None

    def _fail(self, subject: str, failure: str, detail: str = "") -> None:
        self.failures += 1
        _report_deletion_failure(subject, failure, detail)


def check_log(log_path: Path, out: TextIO) -> int:
    """Check every entry of the log, print one line per origin plus a
    verdict line per stale entry, and return 1 only for a stale entry
    (an entry whose every origin is served). A live origin consults the
    deleted-origin arm last: served only behind a reachable deletion
    commit and a HEAD-tree absence."""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    backlog_dir = log_path.resolve().parent
    deletion = _DeletionEvidence(log_path)
    stale: list[str] = []
    for slug, origins in parse_entries(text):
        if not origins:
            # Fail-open: a malformed entry without an Origins block is
            # not a witnessed drift class.
            continue
        all_served = True
        for origin in origins:
            classification, detail = classify_origin(origin, backlog_dir)
            name = Path(origin.replace("\\", "/")).name
            if classification == "served":
                out.write(f"SERVED: {slug} -> {name} [{detail}]\n")
            elif classification == "deferred":
                # Still-actionable work: its own line class, never
                # SERVED, never counted toward the all-served predicate.
                all_served = False
                out.write(f"DEFERRED: {slug} -> {name} [{detail}]\n")
            else:
                # The deleted-origin arm, consulted only after every
                # earlier lookup left the origin live.
                deleted = deletion.deletion_detail(name)
                if deleted is not None:
                    out.write(f"SERVED: {slug} -> {name} [{deleted}]\n")
                else:
                    all_served = False
                    out.write(f"LIVE: {slug} -> {name}\n")
        if all_served:
            stale.append(slug)
    if deletion.failures:
        out.write(f"deletion-lookup failures: {deletion.failures}\n")
    for slug in stale:
        out.write(
            f"STALE: {slug}: every origin served;"
            " prune per the log's prune rule\n"
        )
    return 1 if stale else 0


def run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    """One git plumbing call, pinned to the audited repository root as
    its working directory so the run-from-anywhere promise holds."""
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=120
    )


def write_tool_error(
    out: TextIO, message: str, prefix: str = "prune-audit"
) -> int:
    """The audit mode's tool-error exit: evidence line, then the final
    OUTCOME line, exit 3 (never a silent pass). The prefix names the
    invoking mode (the collateral discovery mode passes its own)."""
    out.write(f"{prefix}: {message}\n")
    out.write("OUTCOME: tool_error\n")
    return 3


def heading_slug(line: str) -> str | None:
    """The entry slug when the line is a ``## <slug>`` heading, else
    None; callers track fence state before consulting this."""
    match = ENTRY_HEADING_RE.match(line)
    if match is None:
        return None
    slug = match.group(1).strip()
    return slug or None


def fence_state_before(lines: list[str], start_line: int) -> bool:
    """The file's fence state before its 1-based line ``start_line``: an
    odd count of fence lines above the hunk start means the hunk's region
    begins inside the entry-template fence. Derived from the commit's own
    pre- or post-image, so a hunk that never shows the template fence
    still classifies correctly."""
    if start_line <= 1:
        return False
    toggles = sum(
        1 for line in lines[: start_line - 1] if FENCE_LINE_RE.match(line)
    )
    return toggles % 2 == 1


def parse_patch_removals(
    patch: str, old_text: str, new_text: str
) -> tuple[list[str], list[str]]:
    """(removed, added) entry slugs from one commit's log patch. A deleted
    or added ``## <slug>`` heading outside the entry-template fence is
    parsed; fence state bootstraps per hunk from the pre- and post-image
    line counts and is then tracked through the added, removed, and
    context lines, so state survives hunk boundaries."""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    removed: list[str] = []
    added: list[str] = []
    old_fence = False
    new_fence = False
    in_hunk = False
    for line in patch.splitlines():
        if not in_hunk or line.startswith("@@"):
            header = HUNK_HEADER_RE.match(line)
            if header is None:
                continue
            old_fence = fence_state_before(old_lines, int(header.group(1)))
            new_fence = fence_state_before(new_lines, int(header.group(3)))
            in_hunk = True
            continue
        if line.startswith("\\"):
            continue
        if line.startswith("+"):
            content = line[1:]
            if FENCE_LINE_RE.match(content):
                new_fence = not new_fence
            elif not new_fence:
                slug = heading_slug(content)
                if slug:
                    added.append(slug)
        elif line.startswith("-"):
            content = line[1:]
            if FENCE_LINE_RE.match(content):
                old_fence = not old_fence
            elif not old_fence:
                slug = heading_slug(content)
                if slug:
                    removed.append(slug)
        elif line.startswith(" "):
            # A context line exists in both images and moves both sides'
            # fence state together.
            content = line[1:]
            if FENCE_LINE_RE.match(content):
                old_fence = not old_fence
                new_fence = not new_fence
        # Anything else inside a hunk (an empty-context rendering
        # artifact) carries no heading or fence content of its own.
    return removed, added


def basename_carries_slug(slug: str, basename: str) -> bool:
    """True when the basename (minus a trailing ``.md``) carries the slug
    as a run of hyphen-bounded segments: ``a-b`` matches ``x-a-b-y`` and
    never a basename that embeds the slug as a substring of one segment,
    and a slug whose segment run is longer than the basename's never
    matches."""
    if not slug:
        return False
    stem = basename[: -len(".md")] if basename.endswith(".md") else basename
    parts = stem.split("-")
    slug_parts = slug.split("-")
    span = len(slug_parts)
    if span > len(parts):
        return False
    return any(
        parts[i : i + span] == slug_parts for i in range(len(parts) - span + 1)
    )


def git_blob_text(repo_root: Path, blob_sha: str) -> str:
    proc = run_git(repo_root, "cat-file", "blob", blob_sha)
    if proc.returncode != 0:
        raise AuditToolError(
            f"git cat-file blob {blob_sha} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def diff_blob_texts(raw_header: str, repo_root: Path) -> tuple[str, str]:
    """(old, new) log texts at the diffed commit, read from the diff-tree
    raw header's blob ids; an all-zero side is the absent file."""
    old_text = new_text = ""
    for line in raw_header.splitlines():
        if not line.startswith(":"):
            continue
        fields = line[1:].split("\t", 1)[0].split()
        if len(fields) < 5:
            continue
        old_sha, new_sha = fields[2], fields[3]
        if not ZERO_SHA_RE.match(old_sha):
            old_text = git_blob_text(repo_root, old_sha)
        if not ZERO_SHA_RE.match(new_sha):
            new_text = git_blob_text(repo_root, new_sha)
        break  # the pathspec names one file; the first raw line is the log
    return old_text, new_text


def witness_candidates(repo_root: Path, commit: str) -> list[tuple[str, str]]:
    """(basename, repo-relative path) for plan files at the plans root
    top level or its ``completed/`` archive twin, at the commit's tree.

    The plan-directory shape rides the same depth grammar one part
    deeper: the charter path ``<slug>/PLAN.md`` is a candidate keyed on
    the slug directory name, both at the plans root and under
    ``completed/`` (the plan-directory-shape plan's prune-witness terms).
    A missing sibling ``plan_shape.py`` (the charter filename's home) is
    a tool error, never a silent skip of the charter arms.
    """
    if CHARTER_FILENAME is None:
        raise AuditToolError(
            "sibling plan_shape.py missing next to the checker copy: deploy it "
            "beside this script (the home copy keeps it as a symlink; cp -P "
            "preserves that)"
        )
    proc = run_git(repo_root, "ls-tree", "-r", "--name-only", commit, "--", PLANS_ROOT_REL)
    if proc.returncode != 0:
        raise AuditToolError(f"git ls-tree failed for {commit}: {proc.stderr.strip()}")
    candidates: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        parts = path.split("/")
        if len(parts) == 4 and tuple(parts[:3]) == ("docs", "history", "plans"):
            candidates.append((parts[3], path))
        elif len(parts) == 5 and tuple(parts[:4]) == (
            "docs",
            "history",
            "plans",
            "completed",
        ):
            candidates.append((parts[4], path))
        elif len(parts) == 5 and parts[4] == CHARTER_FILENAME and tuple(parts[:3]) == (
            "docs",
            "history",
            "plans",
        ):
            candidates.append((parts[3], path))
        elif len(parts) == 6 and parts[5] == CHARTER_FILENAME and tuple(parts[:4]) == (
            "docs",
            "history",
            "plans",
            "completed",
        ):
            candidates.append((parts[4], path))
    return candidates


def commit_resolves(repo_root: Path, token: str) -> bool:
    """True when the token resolves to an existing commit (the receipt
    witness's landing-commit resolution; a non-matching slug or a landing
    commit that does not resolve never witnesses)."""
    proc = run_git(
        repo_root, "rev-parse", "--verify", "--quiet", f"{token}^{{commit}}"
    )
    return proc.returncode == 0


def ledger_token_resolves(repo_root: Path, commit: str, token: str) -> bool:
    """True when a log-ledger receipt token resolves for the removal
    commit: the digest shape through the existing commit probe, or the
    path shape through one tree-membership probe of the removal commit's
    tree (``git cat-file -e <sha>:<path>``); a token resolving to neither
    never witnesses."""
    if commit_resolves(repo_root, token):
        return True
    proc = run_git(repo_root, "cat-file", "-e", f"{commit}:{token}")
    return proc.returncode == 0


def newly_added_receipt_pairs(
    old_text: str, post_text: str
) -> list[tuple[str, str]]:
    """(slug, token) pairs for the receipt ledger lines one commit newly
    adds to one log: the per-log ``(slug, token)`` count delta between
    the log's pre-image and post-image, walked in post-image order, so
    only a newly added line qualifies and a pre-existing identical line
    never does."""
    pre = Counter(LEDGER_RECEIPT_LINE_RE.findall(old_text))
    added: list[tuple[str, str]] = []
    for pair in LEDGER_RECEIPT_LINE_RE.findall(post_text):
        if pre.get(pair, 0):
            pre[pair] -= 1
        else:
            added.append(pair)
    return added


def walk_audit_commits(
    repo_root: Path, commits: list[str], log_rels: list[str], out: TextIO
) -> tuple[int, int, int, int]:
    """Print one classification line per removal, oldest commit first,
    and return (removals, ledger_receipts, flagged, warnings). Raises
    AuditToolError on a git plumbing failure. ``log_rels`` is the
    enumerated rolling logs (the audited log plus its sibling when it
    names one). The log-ledger count includes the in-commit receipt
    class (a newly added same-log ``landing`` line naming the removed
    slug)."""
    removals = 0
    ledger_receipts = 0
    flagged = 0
    warnings = 0
    for sha in commits:
        meta = run_git(repo_root, "show", "-s", "--format=%h%x00%s%x00%B", sha)
        if meta.returncode != 0:
            raise AuditToolError(f"git show failed for {sha}: {meta.stderr.strip()}")
        short, _, rest = meta.stdout.strip().partition("\x00")
        subject, _, body = rest.partition("\x00")
        receipts = RECEIPT_LINE_RE.findall(body)
        per_log: list[tuple[list[str], list[str], str, str]] = []
        for log_rel in log_rels:
            patch = run_git(
                repo_root,
                "diff-tree",
                "--root",
                "-r",
                "--no-commit-id",
                "-p",
                sha,
                "--",
                log_rel,
            )
            raw = run_git(
                repo_root,
                "diff-tree",
                "--root",
                "-r",
                "--no-commit-id",
                sha,
                "--",
                log_rel,
            )
            if patch.returncode != 0 or raw.returncode != 0:
                raise AuditToolError(
                    f"git diff-tree failed for {sha}: "
                    f"{(patch.stderr or raw.stderr).strip()}"
                )
            old_text, new_text = diff_blob_texts(raw.stdout, repo_root)
            removed, added = parse_patch_removals(patch.stdout, old_text, new_text)
            # The post-image stays materialized per touched log: a
            # removal is witnessed only by a ledger line in its own
            # log's post-image, never the sibling's.
            per_log.append((removed, added, new_text, old_text))
        # The receipt-without-removal warning class (warning-only, added
        # by the landing-conflict-intent-union plan): the shared per-log
        # receipt delta (newly_added_receipt_pairs) applied to each
        # log's pre- and post-images, so a commit adding a receipt line
        # while removing no entry from that same log becomes visible
        # without changing any exit code.
        for log_rel, (removed, _, post_text, old_text) in zip(log_rels, per_log):
            if newly_added_receipt_pairs(old_text, post_text) and not removed:
                warnings += 1
                out.write(f"RECEIPT-WITHOUT-REMOVAL: {short} {log_rel}\n")
        if not any(removed for removed, _, _, _ in per_log):
            continue
        candidates = witness_candidates(repo_root, sha)
        for removed, added, post_text, old_text in per_log:
            added_receipts = newly_added_receipt_pairs(old_text, post_text)
            for slug in removed:
                removals += 1
                if added:
                    # The sanctioned editorial merge shape: report-only, and
                    # never a flag regardless of witnesses.
                    out.write(f"SUPERSEDED-IN-COMMIT: {slug} (commit {short})\n")
                    continue
                witness = next(
                    (
                        path
                        for basename, path in candidates
                        if basename_carries_slug(slug, basename)
                    ),
                    None,
                )
                if witness is not None:
                    out.write(f"PRUNE-OK: {slug} -> {witness}\n")
                    continue
                landing = next(
                    (
                        token
                        for rslug, token in receipts
                        if rslug == slug and commit_resolves(repo_root, token)
                    ),
                    None,
                )
                if landing is not None:
                    out.write(
                        f"PRUNE-OK: {slug} -> {landing}"
                        " (EXEC-PROMPTS-PRUNE receipt)\n"
                    )
                    continue
                # Third evidence class: the touched log's own receipt
                # ledger line naming the removed slug (a removal
                # classified by an earlier class never consults this
                # one). A line newly added by this very commit with the
                # literal token ``landing`` is the logs' same-commit
                # receipt form: the in-commit receipt. Any other token
                # must resolve (a commit digest, or a path in the
                # removal commit's tree); an earlier unresolvable
                # ``landing`` line and a sibling-log receipt never
                # witness here.
                in_commit = next(
                    (
                        token
                        for rslug, token in added_receipts
                        if rslug == slug and token == "landing"
                    ),
                    None,
                )
                if in_commit is not None:
                    ledger_receipts += 1
                    out.write(
                        f"PRUNE-OK: {slug} -> landing (in-commit receipt)\n"
                    )
                    continue
                ledger = next(
                    (
                        token
                        for rslug, token in LEDGER_RECEIPT_LINE_RE.findall(post_text)
                        if rslug == slug
                        and ledger_token_resolves(repo_root, sha, token)
                    ),
                    None,
                )
                if ledger is not None:
                    ledger_receipts += 1
                    out.write(
                        f"PRUNE-OK: {slug} -> {ledger} (log ledger receipt)\n"
                    )
                    continue
                flagged += 1
                out.write(
                    f"REMOVED-WITHOUT-WITNESS: {slug} (commit {short} {subject})\n"
                )
    return removals, ledger_receipts, flagged, warnings


def prune_audit(log_path: Path, repo_root: Path, base_ref: str, out: TextIO) -> int:
    """Audit base..HEAD removals of the prompt log against plan-file
    witnesses at each removal commit; returns the exit code and writes
    the evidence plus the final OUTCOME line."""
    try:
        log_rel = log_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return write_tool_error(
            out, f"prompt log sits outside the repository root: {log_path}"
        )
    verified = run_git(
        repo_root, "rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"
    )
    if verified.returncode != 0:
        return write_tool_error(out, f"base ref does not resolve to a commit: {base_ref}")
    base_commit = verified.stdout.strip()
    # The audit enumerates both rolling logs: the audited log plus its
    # sibling when the audited path names one (one window covers both).
    log_rels = [log_rel]
    sibling = SIBLING_LOG_RELS.get(log_rel)
    if sibling is not None and sibling != log_rel:
        log_rels.append(sibling)
    listing = run_git(
        repo_root,
        "rev-list",
        "--reverse",
        f"{base_commit}..HEAD",
        "--",
        *log_rels,
    )
    if listing.returncode != 0:
        return write_tool_error(out, f"git rev-list failed: {listing.stderr.strip()}")
    commits = listing.stdout.split()
    try:
        removals, ledger_receipts, flagged, warnings = walk_audit_commits(
            repo_root, commits, log_rels, out
        )
    except AuditToolError as exc:
        return write_tool_error(out, str(exc))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        return write_tool_error(out, f"git plumbing failure: {exc}")
    out.write(
        f"prune-audit summary: {removals} removals "
        f"({ledger_receipts} by log ledger) across {len(commits)} "
        f"log-touching commit(s) in {base_ref}..HEAD, "
        f"{warnings} warning(s)\n"
    )
    if flagged:
        out.write("OUTCOME: fail\n")
        return 1
    out.write("OUTCOME: pass\n")
    return 0


def prune_audit_cli(log_arg: str | None, base_ref: str | None, out: TextIO) -> int:
    """Resolve the audited log and its repository, then run the audit.
    The default log is this script's own repo root's tracked log; an
    explicit log path is audited in the repository that contains it (the
    caller's cwd is never consulted)."""
    if not base_ref:
        return write_tool_error(out, "--base <ref> is required with --prune-audit")
    if log_arg:
        log_path = Path(log_arg).expanduser()
        if not log_path.is_file():
            return write_tool_error(out, f"prompt log not found: {log_path}")
        log_path = log_path.resolve()
        probe = run_git(log_path.parent, "rev-parse", "--show-toplevel")
        if probe.returncode != 0 or not probe.stdout.strip():
            return write_tool_error(
                out, f"prompt log is not inside a git repository: {log_path}"
            )
        repo_root = Path(probe.stdout.strip()).resolve()
    else:
        log_path = REPO_ROOT / DEFAULT_LOG_REL
        if not log_path.is_file():
            return write_tool_error(out, f"prompt log not found: {log_path}")
        repo_root = REPO_ROOT
    return prune_audit(log_path, repo_root, base_ref, out)


def _collateral_log_pass(
    log_file: Path,
    backlog_rel: str,
    repo_root: Path,
    base_commit: str,
    base_backlog: Path,
    log_name: str | None,
    out: TextIO,
) -> None:
    """One log's discovery pass: one ``COLLATERAL-SERVED`` line per
    qualifying entry (every origin served at HEAD or served at base and
    deleted in the range, at least one origin's served state produced in
    the range). ``log_name`` None keeps the audited log's exact line
    format; a sibling pass appends the sibling log's repo-relative name
    field to each line it writes."""
    for slug, origins in parse_entries(
        log_file.read_text(encoding="utf-8", errors="replace")
    ):
        if not origins:
            continue
        range_produced: list[str] = []
        composite_holds = True
        for origin in origins:
            basename = Path(origin.replace("\\", "/")).name
            origin_rel = f"{backlog_rel}/{basename}"
            head_class, _ = classify_origin(origin, repo_root / backlog_rel)
            head_present = (
                run_git(
                    repo_root,
                    "cat-file",
                    "-e",
                    f"HEAD:{origin_rel}",
                ).returncode
                == 0
            )
            base_class, _ = classify_origin(basename, base_backlog)
            base_present = (
                run_git(
                    repo_root,
                    "cat-file",
                    "-e",
                    f"{base_commit}:{origin_rel}",
                ).returncode
                == 0
            )
            head_served = head_class == "served"
            base_served = base_class == "served" and base_present
            if not head_served and not (base_served and not head_present):
                composite_holds = False
                break
            if head_served and not base_served:
                range_produced.append(basename)
            elif base_served and not head_present:
                range_produced.append(basename)
        if composite_holds and range_produced:
            field = f" [{log_name}]" if log_name is not None else ""
            out.write(
                f"COLLATERAL-SERVED: {slug} -> {' '.join(range_produced)}{field}\n"
            )


def collateral_served(
    log_path: Path, repo_root: Path, base_ref: str, out: TextIO
) -> int:
    """Read-only discovery of collateral served entries (the prompt-log
    collateral-served-prune plan): one ``COLLATERAL-SERVED`` line per log
    entry every origin of which is served at HEAD or was served at base
    and deleted inside the base..HEAD range, when at least one origin's
    served state was produced inside that range. A line names only the
    range-produced origins' basenames: an origin served identically at
    base and HEAD is evidence-excluded while the entry still lists, and a
    composite failure (an origin absent at both, or a base-side live or
    deferred row the range deleted) never lists. The base-side verdicts
    reuse ``classify_origin`` unchanged against a temporary extraction of
    the base commit's backlog directory outside the repository; the mode
    writes nothing to the repository. The deletion arm keys on
    tree-absence at HEAD, never on the classifier's ``live`` verdict (a
    present unserved row also classifies ``live``). The enumeration
    mirrors the prune audit's: both rolling logs ride one invocation from
    the same ``SIBLING_LOG_RELS`` mapping, the audited log's lines keep
    their exact format while the sibling's lines carry its repo-relative
    name field, and a sibling absent from the tree fails open with the
    audited log's listing alone."""
    try:
        rel = log_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return write_tool_error(
            out,
            f"prompt log sits outside the repository root: {log_path}",
            prefix="collateral-served",
        )
    backlog_rel = rel.rsplit("/", 1)[0]
    verified = run_git(
        repo_root, "rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"
    )
    if verified.returncode != 0:
        return write_tool_error(
            out,
            f"base ref does not resolve to a commit: {base_ref}",
            prefix="collateral-served",
        )
    base_commit = verified.stdout.strip()
    archive = subprocess.run(
        ["git", "archive", base_commit, "--", backlog_rel],
        cwd=repo_root,
        capture_output=True,
        timeout=120,
    )
    if archive.returncode != 0:
        return write_tool_error(
            out,
            "git archive of the base backlog failed: "
            f"{archive.stderr.decode(errors='replace').strip()}",
            prefix="collateral-served",
        )
    with tempfile.TemporaryDirectory() as tmp:
        base_backlog = Path(tmp) / "backlog"
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
            strip_prefix = f"{backlog_rel}/"
            for member in tar.getmembers():
                stripped = member.name
                if stripped.startswith(strip_prefix):
                    stripped = stripped[len(strip_prefix):]
                if not stripped or stripped.startswith(".."):
                    continue
                member.name = stripped
                tar.extract(member, base_backlog, filter="data")
        _collateral_log_pass(
            log_path, backlog_rel, repo_root, base_commit, base_backlog, None, out
        )
        # The enumeration mirrors the prune audit's: the audited log's
        # sibling rides the same invocation. A sibling absent from the
        # tree fails open: the audited log alone lists, the exit stays 0.
        sibling_rel = SIBLING_LOG_RELS.get(rel)
        if sibling_rel is not None and sibling_rel != rel:
            sibling_path = repo_root / sibling_rel
            if sibling_path.is_file():
                _collateral_log_pass(
                    sibling_path,
                    backlog_rel,
                    repo_root,
                    base_commit,
                    base_backlog,
                    sibling_rel,
                    out,
                )
    out.write(
        f"collateral-served summary: discovery over {base_ref}..HEAD "
        "(read-only listing; pruning stays the author's receipted rider edit)\n"
    )
    out.write("OUTCOME: pass\n")
    return 0


def collateral_served_cli(
    log_arg: str | None, base_ref: str | None, out: TextIO
) -> int:
    """Resolve the discovered log and its repository, then run the
    read-only discovery; the resolution mirrors --prune-audit's."""
    if not base_ref:
        return write_tool_error(
            out, "--base <ref> is required with --collateral-served",
            prefix="collateral-served",
        )
    if log_arg:
        log_path = Path(log_arg).expanduser()
        if not log_path.is_file():
            return write_tool_error(
                out, f"prompt log not found: {log_path}",
                prefix="collateral-served",
            )
        log_path = log_path.resolve()
        probe = run_git(log_path.parent, "rev-parse", "--show-toplevel")
        if probe.returncode != 0 or not probe.stdout.strip():
            return write_tool_error(
                out,
                f"prompt log is not inside a git repository: {log_path}",
                prefix="collateral-served",
            )
        repo_root = Path(probe.stdout.strip()).resolve()
    else:
        log_path = REPO_ROOT / DEFAULT_LOG_REL
        if not log_path.is_file():
            return write_tool_error(
                out, f"prompt log not found: {log_path}",
                prefix="collateral-served",
            )
        repo_root = REPO_ROOT
    return collateral_served(log_path, repo_root, base_ref, out)


def selftest() -> int:
    """Exercise the verdicts against fixture logs: an all-served entry
    must be STALE (exit 1), a mixed entry must stay, and a deferred-only
    entry must stay open (exit 0, its DEFERRED line, no STALE)."""
    done = "2026-10-01-selftest-done-origin.md"
    archived = "2026-10-01-selftest-archived-origin.md"
    deferred = "2026-10-01-selftest-deferred-origin.md"
    live = "2026-10-01-selftest-live-origin.md"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / done).write_text(
            "# fixture origin\n\nStatus: done (fixture witness)\n",
            encoding="utf-8",
        )
        archive = root / "completed"
        archive.mkdir()
        (archive / archived).write_text(
            "# fixture origin moved to the archive\n", encoding="utf-8"
        )
        deferred_dir = root / "deferred"
        deferred_dir.mkdir()
        (deferred_dir / deferred).write_text(
            "# fixture origin moved to the deferred archive\n", encoding="utf-8"
        )
        (root / live).write_text(
            "# fixture origin\n\n- **Status:** open\n", encoding="utf-8"
        )
        template = (
            "Entry template (one section per entry):\n\n"
            "```\n## <short-slug>\n\nOrigins:\n"
            "- docs/history/backlog/<origin>.md\n```\n"
        )
        stale_entry = (
            "## selftest-stale\n\nAdded: fixture\n\nOrigins:\n"
            f"- docs/history/backlog/{done}\n"
            f"- docs/history/backlog/{archived}\n\n"
            "Urgency: fixture\n\nPrompt: fixture\n\n"
            "Rejected alternatives:\n- none\n\n"
        )
        mixed_entry = (
            "## selftest-mixed\n\nAdded: fixture\n\nOrigins:\n"
            f"- docs/history/backlog/{archived}\n"
            f"- docs/history/backlog/{live}\n\n"
            "Urgency: fixture\n\nPrompt: fixture\n\n"
            "Rejected alternatives:\n- none\n"
        )
        deferred_entry = (
            "## selftest-deferred\n\nAdded: fixture\n\nOrigins:\n"
            f"- docs/history/backlog/{deferred}\n\n"
            "Urgency: fixture\n\nPrompt: fixture\n\n"
            "Rejected alternatives:\n- none\n"
        )
        log = root / "PLAN-PROMPTS.md"
        log.write_text(template + stale_entry + mixed_entry, encoding="utf-8")
        buffer = io.StringIO()
        code = check_log(log, buffer)
        report = buffer.getvalue()
        # The deferred fixture arm runs against its own log whose only
        # entry holds a single deferred origin, so the arm's exit code is
        # that entry's alone (a deferral must never read stale).
        deferred_log = root / "PLAN-PROMPTS-DEFERRED-ONLY.md"
        deferred_log.write_text(template + deferred_entry, encoding="utf-8")
        deferred_buffer = io.StringIO()
        deferred_code = check_log(deferred_log, deferred_buffer)
        deferred_report = deferred_buffer.getvalue()
    problems = []
    if code != 1:
        problems.append(f"fixture exited {code}, expected 1 (the stale entry)")
    if f"SERVED: selftest-stale -> {done} [done (fixture witness)]" not in report:
        problems.append("served-by-status line missing")
    if f"SERVED: selftest-stale -> {archived} [completed/{archived}]" not in report:
        problems.append("served-by-archive line with the resolved path missing")
    if "STALE: selftest-stale" not in report:
        problems.append("STALE verdict line missing")
    if "STALE: selftest-mixed" in report:
        problems.append("mixed entry was flagged stale")
    if f"LIVE: selftest-mixed -> {live}" not in report:
        problems.append("live origin line missing")
    if "<short-slug>" in report:
        problems.append("entry-template fence leaked into the report")
    if deferred_code != 0:
        problems.append(
            f"deferred-only fixture exited {deferred_code}, expected 0 "
            "(a deferral is still actionable, never stale)"
        )
    if f"DEFERRED: selftest-deferred -> {deferred}" not in deferred_report:
        problems.append("deferred origin line missing")
    if f"deferred/{deferred}" not in deferred_report:
        problems.append("deferred archive path missing from the deferred detail")
    if "still actionable" not in deferred_report:
        problems.append("still-actionable note missing from the deferred detail")
    if "STALE" in deferred_report:
        problems.append("deferred-only entry was flagged stale")
    if "SERVED" in deferred_report:
        problems.append("deferred origin was reported served")
    if problems:
        for problem in problems:
            print(f"selftest FAIL: {problem}", file=sys.stderr)
        return 1
    discovery_problems = _collateral_discovery_selftest()
    if discovery_problems:
        for problem in discovery_problems:
            print(f"selftest FAIL: {problem}", file=sys.stderr)
        return 1
    print(
        "selftest ok: all-served entry STALE (exit 1), mixed entry stays,"
        " deferred-only entry open (exit 0), collateral discovery shapes"
        " list and fence as specified"
    )
    return 0


def _collateral_discovery_selftest() -> list[str]:
    """Exercise the --collateral-served discovery shapes against a scratch
    git repository: the four listed shapes (status flip, archive move,
    covered-row deletion, deferred-at-base-turned-served) and each fenced
    shape (the re-opened covered row, the no-coverage deletion, the
    deferred-at-HEAD cell, and the foreign all-served-at-base entry)."""
    prefix = "2026-10-01-collateral-selftest-"
    origins_base: dict[str, str] = {
        f"{prefix}flip.md": "# fixture\n\n- **Status:** open\n",
        f"{prefix}move.md": "# fixture\n\n- **Status:** open\n",
        f"{prefix}del.md": "# fixture\n\nStatus: covered\n",
        f"{prefix}defserved.md": "# fixture base deferred\n",
        f"{prefix}reopen.md": "# fixture\n\nStatus: done\n",
        f"{prefix}nodel.md": "# fixture\n\n- **Status:** open\n",
        f"{prefix}defstay.md": "# fixture\n\n- **Status:** open\n",
        f"{prefix}foreign.md": "# fixture\n\nStatus: done\n",
    }
    head_moves = {
        f"{prefix}flip.md": ("top", "# fixture\n\nStatus: done\n"),
        f"{prefix}move.md": ("completed", "# fixture moved\n"),
        f"{prefix}defserved.md": ("top", "# fixture\n\nStatus: done\n"),
        f"{prefix}reopen.md": ("top", "# fixture\n\n- **Status:** open\n"),
        f"{prefix}defstay.md": ("deferred", "# fixture deferred\n"),
    }
    entry_order = [
        ("flip-entry", f"{prefix}flip.md"),
        ("move-entry", f"{prefix}move.md"),
        ("del-entry", f"{prefix}del.md"),
        ("defserved-entry", f"{prefix}defserved.md"),
        ("reopen-entry", f"{prefix}reopen.md"),
        ("nodel-entry", f"{prefix}nodel.md"),
        ("defstay-entry", f"{prefix}defstay.md"),
        ("foreign-entry", f"{prefix}foreign.md"),
    ]
    template = (
        "Entry template (one section per entry):\n\n"
        "```\n## <short-slug>\n\nOrigins:\n"
        "- docs/history/backlog/<origin>.md\n```\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        backlog = repo / "docs/history/backlog"
        backlog.mkdir(parents=True)

        def git(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                ["git", *args], cwd=repo, capture_output=True, text=True, timeout=60
            )

        assert git("-c", "init.defaultBranch=main", "init").returncode == 0
        for name, text in origins_base.items():
            (backlog / name).write_text(text, encoding="utf-8")
        (backlog / f"deferred/{prefix}defserved.md").parent.mkdir()
        (backlog / f"deferred/{prefix}defserved.md").write_text(
            "# fixture base deferred\n", encoding="utf-8"
        )
        log_sections = "".join(
            (
                f"## {slug}\n\nAdded: fixture\n\nOrigins:\n"
                f"- docs/history/backlog/{name}\n\n"
                "Urgency: fixture\n\nPrompt: fixture\n\n"
                "Rejected alternatives:\n- none\n\n"
            )
            for slug, name in entry_order
        )
        (backlog / "PLAN-PROMPTS.md").write_text(
            template + log_sections, encoding="utf-8"
        )
        assert git("add", "-A").returncode == 0
        assert (
            git(
                "-c",
                "user.name=Collateral Selftest",
                "-c",
                "user.email=collateral-selftest@example.test",
                "commit",
                "-m",
                "seed",
            ).returncode
            == 0
        )
        base = git("rev-parse", "HEAD").stdout.strip()
        for name, (state, text) in head_moves.items():
            if state == "top":
                (backlog / name).write_text(text, encoding="utf-8")
            else:
                (backlog / name).unlink()
                target = backlog / state
                target.mkdir(exist_ok=True)
                (target / name).write_text(text, encoding="utf-8")
        (backlog / f"{prefix}del.md").unlink()
        (backlog / f"{prefix}nodel.md").unlink()
        assert git("add", "-A").returncode == 0
        assert (
            git(
                "-c",
                "user.name=Collateral Selftest",
                "-c",
                "user.email=collateral-selftest@example.test",
                "commit",
                "-m",
                "head moves",
            ).returncode
            == 0
        )
        buffer = io.StringIO()
        code = collateral_served(
            backlog / "PLAN-PROMPTS.md", repo, base, buffer
        )
        report = buffer.getvalue()
    problems: list[str] = []
    if code != 0:
        problems.append(f"discovery fixture exited {code}, expected 0")
    listed = [
        line
        for line in report.splitlines()
        if line.startswith("COLLATERAL-SERVED:")
    ]
    expected = [
        f"COLLATERAL-SERVED: flip-entry -> {prefix}flip.md",
        f"COLLATERAL-SERVED: move-entry -> {prefix}move.md",
        f"COLLATERAL-SERVED: del-entry -> {prefix}del.md",
        f"COLLATERAL-SERVED: defserved-entry -> {prefix}defserved.md",
    ]
    if sorted(listed) != sorted(expected):
        problems.append(
            f"discovery listing mismatch: {listed!r} != {expected!r}"
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Flag PLAN-PROMPTS.md entries whose every origin is served "
            "(a done/covered status, the file resolved into a served "
            "archive state directory, or a covered-row deletion reachable "
            "from HEAD with the file absent from the HEAD tree; a deferred "
            "origin is still "
            "actionable and never serves); exit 1 for a stale entry, "
            "0 otherwise. "
            "With --prune-audit, classify every base..HEAD removal from the "
            "log against its plan-file witness at the removal commit instead"
        )
    )
    parser.add_argument(
        "log",
        nargs="?",
        default=None,
        help=(
            "prompt log path (default: "
            f"{DEFAULT_LOG_REL}, resolved against this script's repo root)"
        ),
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="exercise the verdicts against fixtures instead of checking a log",
    )
    parser.add_argument(
        "--prune-audit",
        action="store_true",
        help=(
            "audit every removal from the log (and its sibling rolling "
            "log) in --base..HEAD against its plan-file witness at the "
            "removal commit, against an EXEC-PROMPTS-PRUNE receipt "
            "naming the removed slug with a resolvable landing commit, "
            "or against the touched log's own receipt ledger line naming "
            "the removed slug with a resolvable digest or in-tree path "
            "token, and the in-commit receipt: a ledger line with the "
            "literal landing token newly added by the same commit "
            "(PRUNE-OK, SUPERSEDED-IN-COMMIT, "
            "REMOVED-WITHOUT-WITNESS); exit 1 when a removal lacks its "
            "witness, 3 for a tool error"
        ),
    )
    parser.add_argument(
        "--collateral-served",
        action="store_true",
        help=(
            "read-only discovery of collateral served entries across both "
            "rolling logs: list every "
            "log entry (other than entries already pruned) whose every "
            "origin is served at HEAD or was served at the --base commit "
            "and deleted inside --base..HEAD, when at least one origin's "
            "served state was produced inside that range; one "
            "COLLATERAL-SERVED line per listed entry naming only the "
            "range-produced origins; the mode lists, it never prunes"
        ),
    )
    parser.add_argument(
        "--base",
        default=None,
        help="base ref for --prune-audit and --collateral-served",
    )
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.prune_audit:
        return prune_audit_cli(args.log, args.base, sys.stdout)
    if args.collateral_served:
        return collateral_served_cli(args.log, args.base, sys.stdout)
    if args.log:
        log_path = Path(args.log).expanduser()
    else:
        log_path = REPO_ROOT / DEFAULT_LOG_REL
    if not log_path.is_file():
        parser.error(f"prompt log not found: {log_path}")
    return check_log(log_path, sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
