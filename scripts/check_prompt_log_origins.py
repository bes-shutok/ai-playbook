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
post-image. Beside the removal-commit-side classes, the audit
recognizes the audited tip's committed log image (never working-tree
bytes; the uncommitted reconcile budget stays responsible for pending
restores): an otherwise-unwitnessed removal classifies ``PRUNE-OK``
through the tip receipt when the tip image carries a ledger line
naming the removed slug with a token resolvable at the tip (any
commit-ish the resolution probe accepts, or a path in the tip
commit's tree; the in-commit ``landing`` literal is excluded by the
token-equality guard before the probes run, and stays owned by the
in-commit class), and an otherwise-flagged receipt-line deletion
classifies ``PRUNE-OK`` through the tip restoration when the tip
image carries that line's exact committed bytes, consumed one draw
per occurrence by full-line identity across the walk. The slug-token
disjunct never clears an eaten-line flag, and a fresh
non-byte-identical line never restores one. The audit classifies
mechanically; the
consultative leg adjudicates: ranges are expected to start after the
pNNN-to-dispatch-log transition, and the landing leg never spans the
pre-plan-era wave commits. An optional ``--head <commit>`` pins the
audited range's upper endpoint (default ``HEAD``): the audit enumerates
``base..head`` at the pinned commit and reports that tip identity, so a
caller can audit an exact verified tip even after the working tree's
``HEAD`` has moved; the summary line reports the actual audited range.
Exit 1 when any removal lacks its witness,
0 otherwise, 3 for a tool error (a missing log at the audit path, an
unresolvable base or head ref, or a git plumbing failure), each with the
final ``OUTCOME:`` line per scripts/OUTCOME_CONTRACT.md.

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
# The exact receipt-ledger line identity used by the repair
# reconciliation: the whole ledger line (both prefixes, trailing prose
# tolerated), so one pending exact re-add matches one committed deletion
# byte-for-byte rather than by (slug, token) pair alone.
RECEIPT_FULL_LINE_RE = re.compile(
    r"^(?:PLAN-PROMPTS-PRUNE|EXEC-PROMPTS-PRUNE):[ \t]+.*$", re.MULTILINE
)

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
# The pending token joins the served class (plan docs/history/plans/
# 2026-11-04-execution-lane-authored-plans-misread-as-landed.md Task 3):
# an all-pending entry goes stale at the authoring flip and owes its
# prune; the execution flip is staleness-preserving (both tokens
# served), unstaling only via prune or the completion fold-and-delete.
SERVED_STATUS_RE = re.compile(
    r"^(?:done|covered-pending-execution|covered)(?![A-Za-z0-9_-])",
    re.IGNORECASE,
)

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


def receipt_compare_slug(slug: str) -> str:
    """The heading slug's first whitespace-delimited token, the compare
    form for receipt slugs: every receipt grammar captures a single
    token (``(\\S+)``), while legacy headings carry an origins suffix
    (``<slug> (origins: ...)``), so a receipt naming the leading slug
    witnesses the removal and the fail-closed no-receipt arm is
    unchanged."""
    return slug.split(None, 1)[0]


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


def missing_ledger_pairs(old_text: str, new_text: str) -> list[tuple[str, str]]:
    """(slug, token) receipt-ledger pairs present in ``old_text`` but
    missing from ``new_text``: the per-log ``(slug, token)`` count delta
    walked in old-image order, so only a genuinely deleted line counts
    and a pre-existing identical line never does. The mirror of
    ``newly_added_receipt_pairs`` for the pending-removal warning."""
    new = Counter(LEDGER_RECEIPT_LINE_RE.findall(new_text))
    removed: list[tuple[str, str]] = []
    for pair in LEDGER_RECEIPT_LINE_RE.findall(old_text):
        if new.get(pair, 0):
            new[pair] -= 1
        else:
            removed.append(pair)
    return removed


def _line_slug(line: str) -> str | None:
    """The receipt slug a ledger line carries, or None when the line is
    not a parseable ledger line."""
    match = LEDGER_RECEIPT_LINE_RE.match(line + "\n")
    return match.group(1) if match else None


def _line_removals(old_text: str, new_text: str) -> list[str]:
    """Exact receipt-ledger lines present in ``old_text`` but missing
    from ``new_text``, walked in old-image order with multiplicity: the
    full-line mirror of ``missing_ledger_pairs``, so a genuinely deleted
    line counts and a pre-existing identical line never does."""
    new = Counter(RECEIPT_FULL_LINE_RE.findall(new_text))
    removed: list[str] = []
    for line in RECEIPT_FULL_LINE_RE.findall(old_text):
        if new.get(line, 0):
            new[line] -= 1
        else:
            removed.append(line)
    return removed


def _line_additions(old_text: str, new_text: str) -> list[str]:
    """Exact receipt-ledger lines newly present in ``new_text`` relative
    to ``old_text``, walked in new-image order with multiplicity."""
    old = Counter(RECEIPT_FULL_LINE_RE.findall(old_text))
    added: list[str] = []
    for line in RECEIPT_FULL_LINE_RE.findall(new_text):
        if old.get(line, 0):
            old[line] -= 1
        else:
            added.append(line)
    return added


def _pending_layer_text(
    repo_root: Path, log_rel: str, layer: str
) -> str:
    """One pending layer's newer image of the log: the index blob for
    the ``index`` layer (``git show :<path>``) and the working-tree file
    for the ``worktree`` layer. An image with no log (never created, or
    the whole file pending-deleted at that layer) reads as the empty
    string, so a whole-file pending deletion compares against an empty
    image and its receipt removals still warn at that layer; a read
    failure other than plain absence raises."""
    if layer == "index":
        proc = run_git(repo_root, "show", f":{log_rel}")
        if proc.returncode != 0:
            # Both absence shapes read as an empty image: a path git
            # never knew ("does not exist") and a path staged as deleted
            # ("exists on disk, but not in the index").
            if "does not exist" in proc.stderr or "not in the index" in proc.stderr:
                return ""
            raise AuditToolError(
                f"git show :{log_rel} failed: {proc.stderr.strip()}"
            )
        return proc.stdout
    path = repo_root / log_rel
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def pending_receipt_removal_warnings(
    repo_root: Path,
    log_rel: str,
    head_short: str,
    out: TextIO,
    head_commit: str = "HEAD",
) -> tuple[int, Counter]:
    """Warning-only pending-receipt-removal scan for one rolling log:
    compare the log's audited-tip image against the index (the ``index``
    layer) and the index against the working tree (the ``worktree``
    layer), and report each deleted receipt-ledger line with its slug,
    log path, layer, and the audited tip identity. A log absent from an
    image reads as empty there (a whole-file pending deletion still warns;
    a log absent at the audited tip has no older image and cannot lose
    receipts). Read failures emit one ``PENDING-SCAN-WARNING`` line and
    never change the committed audit's exit or outcome — the tip image's
    own NON-ABSENCE failure follows the same fail-open-with-a-warning
    shape (a log absent at the tip is the benign no-older-image case and
    stays silent). The absence probes match the git stderr shapes
    "does not exist" / "not in the index" / "does not exist in"; an
    unmatched localized message degrades to the same explicit warning.
    Returns the warnings emitted."""
    warnings = 0
    missing_index: Counter = Counter()
    missing_worktree: Counter = Counter()
    try:
        index_text = _pending_layer_text(repo_root, log_rel, "index")
        worktree_text = _pending_layer_text(repo_root, log_rel, "worktree")
        head_proc = run_git(repo_root, "show", f"{head_commit}:{log_rel}")
    except (AuditToolError, subprocess.TimeoutExpired, OSError, UnicodeDecodeError) as exc:
        out.write(f"PENDING-SCAN-WARNING: {log_rel}: {exc}\n")
        return 1, missing_index, missing_worktree
    head_text = head_proc.stdout
    if head_proc.returncode != 0:
        if "does not exist" in head_proc.stderr:
            # Benign absence: the log was never committed (a brand-new
            # sibling), so no older image exists and no receipts can be
            # pending-deleted against it.
            head_text = ""
        else:
            out.write(
                f"PENDING-SCAN-WARNING: {log_rel}: "
                f"git show {head_commit} failed: {head_proc.stderr.strip()}\n"
            )
            warnings += 1
            head_text = ""
    for layer, old_text, new_text in (
        ("index", head_text, index_text),
        ("worktree", index_text, worktree_text),
    ):
        for slug, token in missing_ledger_pairs(old_text, new_text):
            warnings += 1
            out.write(
                f"PENDING-RECEIPT-REMOVAL: {slug} -> {token} "
                f"{log_rel} {layer} (HEAD {head_short})\n"
            )
    # The net missing lines (HEAD image minus the working-tree image,
    # full-line identity with multiplicity): the repair path's restore
    # worklist for this log. Read failures above leave it empty, so an
    # unavailable image can never be guessed at.
    missing_index = Counter(_line_removals(head_text, index_text))
    missing_worktree = Counter(_line_removals(index_text, worktree_text))
    return warnings, missing_index, missing_worktree


def walk_audit_commits(
    repo_root: Path,
    commits: list[str],
    log_rels: list[str],
    out: TextIO,
    unwitnessed: list[dict] | None = None,
    reconcile: dict[str, Counter] | None = None,
    tip_texts: dict[str, str] | None = None,
    tip_commit: str | None = None,
) -> tuple[int, int, int, int]:
    """Print one classification line per removal, oldest commit first,
    and return (removals, ledger_receipts, flagged, warnings). Raises
    AuditToolError on a git plumbing failure. ``log_rels`` is the
    enumerated rolling logs (the audited log plus its sibling when it
    names one). The log-ledger count includes the in-commit receipt
    class (a newly added same-log ``landing`` line naming the removed
    slug).

    Repair-mode extensions (the pending-receipt-removal-audit-promotion
    plan): ``reconcile`` maps each log to a budget Counter of exact
    pending re-added receipt lines; an otherwise-unwitnessed committed
    removal whose exact removed lines all draw from that budget (one
    draw per occurrence, by full-line identity) classifies
    ``PRUNE-OK: <slug> -> landing (repair reconciliation)`` instead of
    flagging. ``unwitnessed`` collects one record per flagged removal
    (slug, log, exact removed lines, and whether the exact source bytes
    could be established from the removal commit's pre-image) for the
    landing repair's restore worklist.

    Tip-recognition extensions (the prune-audit-standing-flags plan):
    ``tip_texts`` maps each log to the audited tip's committed log image
    (never working-tree bytes) and ``tip_commit`` is that tip's commit
    id. An otherwise-unwitnessed removal classifies
    ``PRUNE-OK: <slug> -> <token> (tip receipt)`` when the tip image
    carries a ledger line naming the slug with a token resolvable at
    the tip (any commit-ish the resolution probe accepts, or a path in
    the tip commit's tree); an
    otherwise-flagged eaten line classifies
    ``PRUNE-OK: <slug> -> landing (tip restoration)`` when the tip
    image carries its exact bytes, one draw per occurrence by full-line
    identity across the walk. The slug-token disjunct never clears an
    eaten-line flag, and a fresh non-byte-identical line never restores
    one."""
    removals = 0
    ledger_receipts = 0
    flagged = 0
    warnings = 0
    # The tip restoration budget (the tip-recognition class): the
    # audited tip's committed image's exact receipt-ledger lines, one
    # draw per occurrence, consumed by the oldest-first walk so two
    # committed removals of one line reconcile one draw per
    # byte-identical tip copy.
    tip_restores: dict[str, Counter] = {
        rel: Counter(
            RECEIPT_FULL_LINE_RE.findall(
                tip_texts.get(rel, "") if tip_texts else ""
            )
        )
        for rel in log_rels
    }
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
        any_removed = any(removed for removed, _, _, _ in per_log)
        candidates = witness_candidates(repo_root, sha) if any_removed else []
        for log_rel, (removed, added, post_text, old_text) in zip(
            log_rels, per_log
        ):
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
                        if rslug == receipt_compare_slug(slug)
                        and commit_resolves(repo_root, token)
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
                        if rslug == receipt_compare_slug(slug)
                        and token == "landing"
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
                        if rslug == receipt_compare_slug(slug)
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
                # Repair reconciliation (one flagged class, the
                # pending-receipt-removal-audit-promotion plan): the
                # exact removed lines draw from the pending re-add
                # budget, one draw per occurrence by full-line identity.
                removed_lines = _line_removals(old_text, post_text)
                budget = reconcile.get(log_rel) if reconcile else None
                if budget is not None and removed_lines:
                    trial = {
                        line: budget.get(line, 0) for line in removed_lines
                    }
                    affordable = True
                    for line in removed_lines:
                        if trial[line] <= 0:
                            affordable = False
                            break
                        trial[line] -= 1
                    if affordable:
                        for line in removed_lines:
                            budget[line] -= 1
                        ledger_receipts += 1
                        out.write(
                            f"PRUNE-OK: {slug} -> landing"
                            " (repair reconciliation)\n"
                        )
                        continue
                # Tip recognition (the tip-recognition class): the
                # audited tip's committed image naming the removed slug
                # with a token resolvable at the tip (a commit digest, or
                # a path in the tip commit's tree). Consulted only after
                # every removal-commit-side class failed, so the removal
                # commit's own images carry no resolvable witness, and
                # each log's removals consult only that log's tip image.
                # The in-commit ``landing`` literal resolves through
                # neither probe and stays owned by the in-commit class.
                tip_receipt = None
                if tip_texts and tip_commit is not None:
                    tip_receipt = next(
                        (
                            token
                            for rslug, token in LEDGER_RECEIPT_LINE_RE.findall(
                                tip_texts.get(log_rel, "")
                            )
                            if rslug == receipt_compare_slug(slug)
                            and token != "landing"
                            and ledger_token_resolves(
                                repo_root, tip_commit, token
                            )
                        ),
                        None,
                    )
                if tip_receipt is not None:
                    ledger_receipts += 1
                    out.write(
                        f"PRUNE-OK: {slug} -> {tip_receipt} (tip receipt)\n"
                    )
                    continue
                flagged += 1
                out.write(
                    f"REMOVED-WITHOUT-WITNESS: {slug} (commit {short} {subject})\n"
                )
                if unwitnessed is not None:
                    sourceable = bool(old_text) and len(set(removed_lines)) <= 1
                    unwitnessed.append(
                        {
                            "slug": slug,
                            "log_rel": log_rel,
                            "lines": removed_lines,
                            "sourceable": sourceable,
                        }
                    )
            # Pure receipt-line deletions (the receipt's entry stays in the
            # log): every receipt-ledger line removed by the commit whose
            # slug matches no entry removed in the same commit is its own
            # flagged audit class, reconciled only by an exact pending
            # re-add one-for-one (the pending-receipt-removal-audit-promotion
            # plan's committed-history detection layer).
            budget = reconcile.get(log_rel) if reconcile else None
            for line in _line_removals(old_text, post_text):
                line_slug = _line_slug(line)
                if line_slug is None:
                    continue
                if any(
                    receipt_compare_slug(removed_slug)
                    == receipt_compare_slug(line_slug)
                    for removed_slug in removed
                ):
                    continue
                # The retoken shape: the same commit re-adds a receipt line
                # for the same slug (a witness token refresh beside a
                # surviving entry), so nothing was lost.
                if any(
                    receipt_compare_slug(added_slug)
                    == receipt_compare_slug(line_slug)
                    for added_slug, _token in newly_added_receipt_pairs(
                        old_text, post_text
                    )
                ):
                    continue
                if budget is not None and budget.get(line, 0) > 0:
                    budget[line] -= 1
                    ledger_receipts += 1
                    out.write(
                        f"PRUNE-OK: {line_slug} -> landing"
                        f" (repair reconciliation, commit {short})\n"
                    )
                    continue
                # Tip restoration (the tip-recognition class): the exact
                # removed bytes present in the audited tip's committed
                # image, one draw per occurrence by full-line identity.
                # Byte identity only: the slug-token disjunct never
                # clears an eaten-line flag, and a fresh
                # non-byte-identical line never restores one.
                if tip_restores[log_rel].get(line, 0) > 0:
                    tip_restores[log_rel][line] -= 1
                    ledger_receipts += 1
                    out.write(
                        f"PRUNE-OK: {line_slug} -> landing (tip restoration)\n"
                    )
                    continue
                flagged += 1
                out.write(
                    f"RECEIPT-LINE-REMOVED-WITHOUT-WITNESS: {line_slug} "
                    f"(commit {short} {subject})\n"
                )
                if unwitnessed is not None:
                    # Ambiguity: the same commit removes more than one
                    # distinct receipt variant of this slug, so no unique
                    # exact source exists and the repair must never
                    # invent either variant.
                    variants = {
                        candidate
                        for candidate in _line_removals(old_text, post_text)
                        if _line_slug(candidate) == line_slug
                    }
                    unwitnessed.append(
                        {
                            "slug": line_slug,
                            "log_rel": log_rel,
                            "lines": [line],
                            "sourceable": bool(old_text)
                            and len(variants) <= 1,
                        }
                    )


    return removals, ledger_receipts, flagged, warnings


def prune_audit(
    log_path: Path,
    repo_root: Path,
    base_ref: str,
    out: TextIO,
    head_ref: str = "HEAD",
    unwitnessed: list[dict] | None = None,
) -> int:
    """Audit base..head removals of the prompt log against plan-file
    witnesses at each removal commit; returns the exit code and writes
    the evidence plus the final OUTCOME line. ``head_ref`` defaults to
    ``HEAD``; an explicit pinned commit audits that exact upper endpoint
    regardless of where the working tree's HEAD sits."""
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
    head_verified = run_git(
        repo_root, "rev-parse", "--verify", "--quiet", f"{head_ref}^{{commit}}"
    )
    if head_verified.returncode != 0:
        return write_tool_error(
            out, f"head ref does not resolve to a commit: {head_ref}"
        )
    head_commit = head_verified.stdout.strip()
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
        f"{base_commit}..{head_commit}",
        "--",
        *log_rels,
    )
    if listing.returncode != 0:
        return write_tool_error(out, f"git rev-list failed: {listing.stderr.strip()}")
    commits = listing.stdout.split()
    # The pending re-add budget (the reconciliation class): exact
    # receipt lines newly present in the working tree over the audited
    # endpoint's image, consumed one draw per occurrence by the
    # committed walk, so one exact pending re-add reconciles exactly one
    # matching committed deletion by line identity and multiplicity and
    # unmatched deletions stay flagged.
    reconcile: dict[str, Counter] = {}
    # The audited tip's committed log image per log (the
    # tip-recognition class): the same endpoint read the pending budget
    # consumes, pinned to ``head_commit`` so an explicit --head audits
    # that exact tip's image and never the working-tree bytes.
    tip_texts: dict[str, str] = {}
    for rel in log_rels:
        try:
            endpoint_proc = run_git(repo_root, "show", f"{head_commit}:{rel}")
            endpoint_text = (
                endpoint_proc.stdout
                if endpoint_proc.returncode == 0
                else ""
            )
        except UnicodeDecodeError:
            # An undecodable endpoint image contributes no budget; the
            # committed walk reports the blob on its own terms.
            endpoint_text = ""
        tip_texts[rel] = endpoint_text
        try:
            worktree_text = (repo_root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            worktree_text = ""
        reconcile[rel] = Counter(
            _line_additions(endpoint_text, worktree_text)
        )
    try:
        removals, ledger_receipts, flagged, warnings = walk_audit_commits(
            repo_root,
            commits,
            log_rels,
            out,
            unwitnessed=unwitnessed,
            reconcile=reconcile,
            tip_texts=tip_texts,
            tip_commit=head_commit,
        )
    except AuditToolError as exc:
        return write_tool_error(out, str(exc))
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        return write_tool_error(out, f"git plumbing failure: {exc}")
    # The pending-removal warning scan (warning-only, the
    # warn-pending-prompt-log-receipt-removals plan): receipt-ledger
    # lines deleted in the index or working tree but not yet committed
    # are invisible to the committed walk above, so each rolling log is
    # scanned per layer after it. Findings ride the existing warning
    # count and never change the committed classifications, exit, or
    # OUTCOME; a pending-scan read failure emits its own warning line
    # and likewise never becomes a stop or tool error.
    try:
        head_ident = run_git(repo_root, "rev-parse", "--short", head_commit)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return write_tool_error(out, f"git plumbing failure: {exc}")
    head_short = head_ident.stdout.strip()
    if head_ident.returncode != 0:
        # The same fail-open-with-a-warning shape the scan's own reads
        # use: the identity degrades to empty and the failure is named.
        out.write(
            "PENDING-SCAN-WARNING: "
            f"{head_commit}: git rev-parse --short failed: "
            f"{head_ident.stderr.strip()}\n"
        )
        warnings += 1
        head_short = ""
    # The pending scan now feeds the flagged audit class (the
    # pending-receipt-removal-audit-promotion plan promoted it from a
    # warning): each net missing receipt line flags, and the repair
    # path is the only way a landing continues past it.
    pending_missing: dict[str, tuple[Counter, Counter]] = {}
    # The pending images are pending relative to the working tree's own
    # HEAD, never the audit's pinned endpoint: an explicit --head audits
    # an exact committed range, while the pending layers describe the
    # uncommitted landing state (the repair path re-derives against the
    # literal HEAD too, so the two never disagree).
    real_head = run_git(repo_root, "rev-parse", "--short", "HEAD")
    real_head_short = real_head.stdout.strip() if real_head.returncode == 0 else ""
    for rel in log_rels:
        layer_warnings, missing_index, missing_worktree = (
            pending_receipt_removal_warnings(
                repo_root, rel, real_head_short, out, "HEAD"
            )
        )
        warnings += layer_warnings
        pending_missing[rel] = (missing_index, missing_worktree)
    pending_flags = sum(
        sum(index_counts.values()) + sum(worktree_counts.values())
        for index_counts, worktree_counts in pending_missing.values()
    )
    out.write(
        f"prune-audit summary: {removals} removals "
        f"({ledger_receipts} by log ledger) across {len(commits)} "
        f"log-touching commit(s) in {base_commit}..{head_commit}, "
        f"{warnings} warning(s), {pending_flags} pending receipt "
        f"flag(s)\n"
    )
    if flagged or pending_flags:
        out.write("OUTCOME: fail\n")
        return 1
    out.write("OUTCOME: pass\n")
    return 0


def _stage_index_blob(repo_root: Path, log_rel: str, blob: str) -> bool:
    """Point the index at ``blob`` for ``log_rel``, keeping the tracked
    mode; False when the path is not tracked or the update refuses."""
    listing = run_git(repo_root, "ls-files", "--stage", "--", log_rel)
    if listing.returncode != 0 or not listing.stdout.strip():
        return False
    mode = listing.stdout.split()[0]
    proc = run_git(
        repo_root, "update-index", "--cacheinfo", f"{mode},{blob},{log_rel}"
    )
    return proc.returncode == 0


def _hash_object_bytes(repo_root: Path, data: str) -> str | None:
    """Write ``data`` into the object database and return its blob SHA,
    or None on a plumbing failure."""
    proc = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=repo_root,
        input=data,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _worktree_text(path: Path) -> str:
    """The log's working-tree image; the seam the repair's compose and
    fresh-read verification both read through."""
    return path.read_text(encoding="utf-8")


def _append_lines(text: str, lines: list[str]) -> str:
    """The image with the receipt lines appended after its current
    content, never reordering or rewriting a byte of what is already
    there."""
    if not text.endswith("\n") and text:
        text += "\n"
    return text + "".join(line + "\n" for line in lines)


def _receipt_repair_apply(
    repo_root: Path,
    log_rels: list[str],
    need: dict[str, Counter],
    out: TextIO,
) -> bool:
    """Restore the needed exact receipt lines into both pending images
    (working tree and index) of each log, preserving every unrelated
    byte of both images: the lines append after each image's current
    content, and the index update stages a hash-object blob of the
    index image plus the inserted lines, never the working-tree file.
    Before writing, both images are re-read and must still match the
    compose input; one mismatch retries the compose once, and a second
    mismatch leaves everything untouched with a named conflict report.
    If the paired write fails partway (the working-tree bytes landed
    but the index update failed), the inserted working-tree bytes roll
    back and both images are verified to retain their pre-repair
    content. Returns True when every needed line is in place in both
    images."""
    for log_rel in log_rels:
        wanted = need.get(log_rel)
        if not wanted:
            continue
        index_lines = list(wanted[0].elements())
        worktree_lines = list(wanted[1].elements())
        path = repo_root / log_rel
        applied = False
        for attempt in (1, 2):
            index_text = _pending_layer_text(repo_root, log_rel, "index")
            try:
                worktree_text = _worktree_text(path)
            except (OSError, UnicodeDecodeError) as exc:
                out.write(
                    f"RECEIPT-REPAIR-CONFLICT: {log_rel}: the working-tree "
                    f"image is unreadable: {exc}\n"
                )
                return False
            # Fresh-read verification: the composed images must still be
            # the images on disk at the write instant; a concurrent edit
            # between the compose and the write retries the compose once.
            try:
                fresh_index = _pending_layer_text(repo_root, log_rel, "index")
                fresh_worktree = _worktree_text(path)
            except (OSError, UnicodeDecodeError) as exc:
                out.write(
                    f"RECEIPT-REPAIR-CONFLICT: {log_rel}: an image turned "
                    f"unreadable under the repair: {exc}\n"
                )
                return False
            if (fresh_index, fresh_worktree) != (index_text, worktree_text):
                continue
            new_worktree = _append_lines(worktree_text, worktree_lines)
            new_index = _append_lines(index_text, index_lines)
            try:
                path.write_text(new_worktree, encoding="utf-8")
            except OSError as exc:
                out.write(
                    f"RECEIPT-REPAIR-CONFLICT: {log_rel}: the working-tree "
                    f"write failed: {exc}\n"
                )
                return False
            blob = _hash_object_bytes(repo_root, new_index)
            if blob is None or not _stage_index_blob(repo_root, log_rel, blob):
                # Partway failure: the working-tree insertion rolls back
                # and both images are verified to hold their pre-repair
                # content, including any concurrent unrelated edits the
                # fresh read captured.
                try:
                    path.write_text(worktree_text, encoding="utf-8")
                except OSError as exc:
                    out.write(
                        f"RECEIPT-REPAIR-CONFLICT: {log_rel}: the index "
                        f"update failed and the worktree rollback failed "
                        f"too: {exc}\n"
                    )
                    return False
                rolled_index = _pending_layer_text(repo_root, log_rel, "index")
                rolled_worktree = path.read_text(encoding="utf-8")
                if (rolled_index, rolled_worktree) != (index_text, worktree_text):
                    out.write(
                        f"RECEIPT-REPAIR-CONFLICT: {log_rel}: the rollback "
                        "did not restore the pre-repair images\n"
                    )
                    return False
                out.write(
                    f"RECEIPT-REPAIR-CONFLICT: {log_rel}: the index update "
                    "failed; the inserted worktree bytes rolled back\n"
                )
                return False
            applied = True
            break
        if not applied:
            out.write(
                f"RECEIPT-REPAIR-CONFLICT: {log_rel}: the log's images kept "
                "changing between the compose and the write; the repair is "
                "unapplied and both images are untouched\n"
            )
            return False
    return True


def _log_head_text(repo_root: Path, log_rel: str) -> str:
    """The log's HEAD image, or the empty string on benign absence (the
    log was never committed); other read failures raise."""
    proc = run_git(repo_root, "show", f"HEAD:{log_rel}")
    if proc.returncode != 0:
        if "does not exist" in proc.stderr:
            return ""
        raise AuditToolError(
            f"git show HEAD:{log_rel} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def prune_audit_repair(
    log_path: Path,
    repo_root: Path,
    base_ref: str,
    out: TextIO,
    head_ref: str = "HEAD",
) -> int:
    """The landing-only repair mode: run the audit, and when it flags
    restorable receipt-line deletions (pending missing lines, committed
    unwitnessed removals with uniquely sourced exact bytes), restore the
    exact bytes into both pending images, reconcile each restoration
    against its exact committed deletion on one rerun, and succeed only
    when the rerun passes. An exact source that cannot be established,
    a repair that cannot be safely applied after one fresh-read retry,
    or a rerun that still fails names its specific condition and
    returns the audit's failure. The default invocation's outcomes are
    unchanged; this mode is only for landing closeout."""
    log_rel = log_path.resolve().relative_to(repo_root.resolve()).as_posix()
    log_rels = [log_rel]
    sibling = SIBLING_LOG_RELS.get(log_rel)
    if sibling is not None and sibling != log_rel:
        log_rels.append(sibling)
    unwitnessed: list[dict] = []
    code = prune_audit(
        log_path, repo_root, base_ref, out, head_ref, unwitnessed=unwitnessed
    )
    if code == 0:
        return 0
    # The same one-for-one budget the audit's own reconciliation used,
    # consumed here while composing the restore need.
    pending_budget: dict[str, Counter] = {}
    for rel in log_rels:
        try:
            endpoint_text = _log_head_text(repo_root, rel)
            worktree_text = (repo_root / rel).read_text(encoding="utf-8")
            pending_budget[rel] = Counter(
                _line_additions(endpoint_text, worktree_text)
            )
        except (AuditToolError, OSError, UnicodeDecodeError):
            pending_budget[rel] = Counter()
    # The need is per image: the index must regain the head image's
    # missing receipt lines, the working tree must regain the index
    # image's missing lines on top of those, and each committed
    # unwitnessed removal's exact lines ride both images so the landing
    # commit carries the restoration.
    need: dict[str, tuple[Counter, Counter]] = {}

    def _need_for(rel: str) -> tuple[Counter, Counter]:
        return need.setdefault(rel, (Counter(), Counter()))

    restorable = False
    for record in unwitnessed:
        if not record["sourceable"]:
            out.write(
                f"RECEIPT-REPAIR-UNRECOVERABLE: {record['slug']} in "
                f"{record['log_rel']}: the exact source bytes cannot be "
                "established from the removal commit's pre-image; the "
                "line is named here, never invented or altered\n"
            )
            continue
        restorable = True
        index_need, worktree_need = _need_for(record["log_rel"])
        for line in record["lines"]:
            # A pending re-add already present for this exact line
            # reconciles one committed deletion one-for-one; the repair
            # restores only the uncovered remainder.
            if pending_budget.get(record["log_rel"], {}).get(line, 0) > 0:
                pending_budget[record["log_rel"]][line] -= 1
                continue
            index_need.update([line])
            worktree_need.update([line])
    for rel in log_rels:
        try:
            head_text = _log_head_text(repo_root, rel)
            index_text = _pending_layer_text(repo_root, rel, "index")
            try:
                worktree_text = (repo_root / rel).read_text(encoding="utf-8")
            except FileNotFoundError:
                if head_text:
                    # A committed log whose whole working-tree file is
                    # gone is a whole-file loss the receipt repair must
                    # never paper over with a receipt-lines-only file.
                    out.write(
                        f"RECEIPT-REPAIR-UNRECOVERABLE: {rel}: the "
                        "working-tree image is absent while the log is "
                        "committed; a whole-file loss is not receipt-"
                        "repairable\n"
                    )
                    continue
                # Benign absence: the log was never committed, so there
                # is no older image and no receipts can be missing.
                worktree_text = ""
        except (AuditToolError, OSError, UnicodeDecodeError) as exc:
            out.write(
                f"RECEIPT-REPAIR-UNRECOVERABLE: {rel}: the pending "
                f"images cannot be read to source the restoration: {exc}\n"
            )
            continue
        missing_index = Counter(_line_removals(head_text, index_text))
        missing_worktree = Counter(_line_removals(index_text, worktree_text))
        if missing_index or missing_worktree:
            restorable = True
            index_need, worktree_need = _need_for(rel)
            index_need.update(missing_index.elements())
            worktree_need.update(missing_index.elements())
            worktree_need.update(missing_worktree.elements())
    if not restorable:
        # Nothing restorable: the flags stand and the report already
        # names every unrecoverable line; the repair invocation ends
        # with its own terminal outcome line.
        out.write("OUTCOME: fail\n")
        return code
    if not _receipt_repair_apply(repo_root, log_rels, need, out):
        out.write("OUTCOME: fail\n")
        return 1
    # The reconciliation budget: the repaired working tree's exact
    # receipt additions over HEAD, consumed one draw per occurrence by
    # the rerun's committed walk.
    return prune_audit(log_path, repo_root, base_ref, out, head_ref)


def prune_audit_cli(
    log_arg: str | None,
    base_ref: str | None,
    out: TextIO,
    head_arg: str | None = None,
    repair: bool = False,
) -> int:
    """Resolve the audited log and its repository, then run the audit.
    The default log is this script's own repo root's tracked log; an
    explicit log path is audited in the repository that contains it (the
    caller's cwd is never consulted). ``head_arg`` optionally pins the
    audited range's upper endpoint; omitted keeps the ``HEAD`` default
    for existing callers."""
    if not base_ref:
        return write_tool_error(out, "--base <ref> is required with --prune-audit")
    head_ref = head_arg or "HEAD"
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
    if repair:
        return prune_audit_repair(
            log_path, repo_root, base_ref, out, head_ref
        )
    return prune_audit(log_path, repo_root, base_ref, out, head_ref)


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
            "literal landing token newly added by the same commit, and "
            "the tip recognition against the audited tip's committed log "
            "image: a tip receipt naming the slug with a tip-resolvable "
            "token, or a tip restoration carrying an eaten line's exact "
            "bytes (PRUNE-OK, SUPERSEDED-IN-COMMIT, "
            "REMOVED-WITHOUT-WITNESS); an optional --head <commit> pins "
            "the audited range's upper endpoint (default HEAD); exit 1 "
            "when a removal lacks its witness, 3 for a tool error"
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
    parser.add_argument(
        "--head",
        default=None,
        help=(
            "optional upper endpoint commit for --prune-audit "
            "(default: HEAD); the audit enumerates base..head at the "
            "pinned commit and the summary reports the audited range"
        ),
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help=(
            "with --prune-audit, the landing-only repair mode: receipt-"
            "line deletions the audit flags are restored from their "
            "exact committed bytes into both pending images, the audit "
            "is rerun, and the landing continues only when the rerun "
            "passes; an exact source that cannot be established, a "
            "repair that cannot be safely applied after one fresh-read "
            "retry, or a rerun that still fails names its specific "
            "condition and fails. Never pass this from a survey: the "
            "default invocation stays read-only"
        ),
    )
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.prune_audit:
        return prune_audit_cli(
            args.log, args.base, sys.stdout, args.head, repair=args.repair
        )
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
