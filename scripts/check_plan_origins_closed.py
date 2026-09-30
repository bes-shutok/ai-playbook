#!/usr/bin/env python3
"""Origins-closure gate for plan backlog origins (two arms, one script).

A plan header opens its scope with "Backlog origins (scope of record)"
lines listing promoted backlog item paths. This gate verifies those
origins actually left the backlog top level:

- Archive gate (``--plan <path>``): extract THAT plan's origins-block
  basenames and exit 1 listing the stragglers of that plan only. An
  origin passes when the file sits under the completed directory, under
  the backlog directory's ``rejected/`` archive (an explicit decision
  against the work), or the top-level item's header carries
  ``Status: closed`` or ``Status: done``.
  A plan with no origins block passes trivially (nothing to verify).
  ``--warn`` downgrades the arm to warn-and-exit-0.
- Corpus scan (no ``--plan``): walk every archived plan under the plans
  directory, emit one warning per unresolved origin, and always exit 0.
  This is the maintenance survey's warn arm; only the archive-step arm
  gates behavior, and only on its own stragglers.

Paths resolve from arguments and the repo facts file
(``.ai-playbook/facts.md``, TOML keys ``backlog_dir``,
``backlog_completed_dir``, ``plans_completed_dir``) anchored at the repo
root; conventional repo-relative defaults back a missing key, and no
machine-specific absolute path is hardcoded. Origins are the backtick
quoted backlog paths inside the origins paragraph (the header line
through its first blank line); a plan may also open its scope with a single `Backlog origin:` line, which this gate parses the same way. Review, guideline, and script paths quoted
in the same paragraph are ignored. Stdlib only; no network.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import facts_paths
except ImportError:  # pragma: no cover
    facts_paths = None  # type: ignore

DEFAULT_BACKLOG_DIR = "docs/history/backlog"
DEFAULT_COMPLETED_DIR = "docs/history/backlog/completed"
DEFAULT_PLANS_DIR = "docs/history/plans/completed"
DEFAULT_ACTIVE_PLANS_DIR = "docs/history/plans"
# Rejected archive: a top-level backlog item moved here after an explicit
# decision against the work counts as closed (never a live straggler).
REJECTED_DIR_NAME = "rejected"

# A backlog item's closure declaration lives in its header region: the
# first STATUS_HEADER_LINES lines of the top-level item file. The region
# is bounded so body prose that merely quotes ``Status: done`` (a known
# corpus shape: the no-gate witness item itself does) can never close a
# still-open item.
STATUS_HEADER_LINES = 15

ORIGINS_HEADER_RE = re.compile(
    r"^\s*Backlog origins \(scope of record\)\s*:?", re.IGNORECASE
)
# Canonized single-origin template form: one `Backlog origin:` line opens
# the scope instead of the plural block.
ORIGIN_SINGULAR_RE = re.compile(r"^\s*Backlog origin\s*:\s*(\S+)")
BACKTICK_SPAN_RE = re.compile(r"`([^`]+)`")
# Tolerates the corpus shapes ``Status: open``, ``- **Status:** open``,
# and ``Status: done; plan created ...``: an optional bullet, optional
# bold, then the ``status:`` label.
STATUS_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\*\*)?\s*status\s*(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.+?)\s*$",
    re.IGNORECASE,
)
# closed/done as the status VALUE; a hyphenated continuation such as
# ``done-for-now`` is not a closure declaration.
STATUS_CLOSED_VALUE_RE = re.compile(
    r"^(?:closed|done)(?![A-Za-z0-9_-])", re.IGNORECASE
)

# covered as the status VALUE with the covering-plan witness:
# ``covered (docs/history/plans/<plan>.md)``. A new classification,
# never a closed one: a covered-not-yet-executed origin still owes the
# execution-time fold, so it stays outside PASS_STATES.
STATUS_COVERED_VALUE_RE = re.compile(
    r"^covered\s*\(([^)]+)\)", re.IGNORECASE
)

PASS_STATES = ("completed", "closed", "rejected")

# The plan-side "## Origins dispositions" section (case-insensitive
# heading) lists one disposition line per origin; its backtick backlog
# paths are the undercount warning's comparison set.
_DISPOSITIONS_HEADING_RE = re.compile(
    r"^\s*#{0,6}\s*origins\s+dispositions\s*:?\s*$", re.IGNORECASE
)

# The plan-side "## Disposition of migrated backlog items" section
# (case-insensitive heading) is the fold-then-delete consult anchor: a
# deleted origin whose basename appears there as a boundary-anchored
# `.md` path token was deliberately folded and its per-item file
# deleted, so the migrated-origin warn does not fire for it.
_MIGRATED_DISPOSITIONS_HEADING_RE = re.compile(
    r"^\s*#{0,6}\s*disposition\s+of\s+migrated\s+backlog\s+items\s*:?\s*$",
    re.IGNORECASE,
)

# A `.md` path token in prose or a backtick span; the boundary guards
# below reject a `prefix-<basename>` near miss.
_MD_TOKEN_RE = re.compile(r"[\w./-]*\.md")

# The document registry's migration-audit anchor: a ROW whose notes cell
# carries the `user-approved` token AND the `migration audit` marker, and
# whose row text boundary-anchors the origin's basename.
_REGISTRY_MIGRATION_TOKEN = "user-approved"
_REGISTRY_MIGRATION_MARKER = "migration audit"
DEFAULT_DOC_REGISTRY_REL = "docs/maintenance/document-registry.md"


def _dispositions_basenames(
    plan_text: str, backlog_dir: Path, completed_dir: Path
) -> list[str]:
    """Backlog basenames listed in the plan's origins-dispositions section."""
    names: list[str] = []
    seen: set[str] = set()
    in_section = False
    for line in plan_text.splitlines():
        if _DISPOSITIONS_HEADING_RE.match(line):
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("#") and not _DISPOSITIONS_HEADING_RE.match(line):
                break  # next heading ends the section
            for span in BACKTICK_SPAN_RE.findall(line):
                text = span.strip()
                if not text.endswith(".md"):
                    continue
                if not _is_backlog_ref(text, backlog_dir, completed_dir):
                    continue
                name = Path(text.replace(os.sep, "/")).name
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
    return names


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _boundary_anchored(haystack: str, basename: str) -> bool:
    """True iff ``basename`` appears in ``haystack`` with a non-name
    character (or an edge) on both sides: ``prefix-<basename>`` does not
    resolve."""
    pattern = re.compile(
        r"(?<![\w.-])" + re.escape(basename) + r"(?![\w.-])"
    )
    return pattern.search(haystack) is not None


def _migrated_disposition_basenames(plan_text: str) -> list[str]:
    """.md path tokens named in the plan's disposition-of-migrated-items
    section (basename view), regardless of backtick quoting."""
    names: list[str] = []
    seen: set[str] = set()
    in_section = False
    for line in plan_text.splitlines():
        if _MIGRATED_DISPOSITIONS_HEADING_RE.match(line):
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith("#") and not _MIGRATED_DISPOSITIONS_HEADING_RE.match(line):
                break  # next heading ends the section
            for token in _MD_TOKEN_RE.findall(line):
                name = Path(token.replace(os.sep, "/")).name
                if name.endswith(".md") and name not in seen:
                    seen.add(name)
                    names.append(name)
    return names


def _disposition_consult(plan_text: str, basename: str) -> bool:
    """Fold-then-delete consult: the plan's own migrated-dispositions
    section names the deleted origin."""
    return _boundary_anchored("\n".join(
        _migrated_disposition_basenames(plan_text)
    ), basename)


def _registry_migration_audit_row(
    repo_root: Path, basename: str, registry: Path | None
) -> bool:
    """Registry consult: one ROW jointly carries the anchor. Row-scoped,
    never registry-scoped; inert (warn retained, no exception) when the
    registry is missing or unreadable. ``registry`` is the once-per-run
    resolved path (or None when facts resolution already failed), so the
    per-origin loop neither re-resolves facts nor re-warns."""
    if registry is None:
        return False
    try:
        text = registry.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        notes_hits = [
            c
            for c in cells
            if _REGISTRY_MIGRATION_TOKEN in c
            and _REGISTRY_MIGRATION_MARKER in c
        ]
        if not notes_hits:
            continue
        if _boundary_anchored(stripped, basename):
            return True
    return False


def resolve_repo_root(explicit: str | None) -> Path:
    """Anchor resolution: the explicit argument, else the git toplevel,
    else the current directory (with a warning on the last fallback)."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if out:
            return Path(out).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    _warn("git toplevel unavailable; anchoring at the current directory")
    return Path.cwd().resolve()


def resolve_dir(
    arg_value: str | None, repo_root: Path, facts_key: str, default: str
) -> Path:
    """Resolve one directory: explicit argument, then the facts TOML key,
    then the conventional default. Relative values anchor at the repo
    root, never the process CWD, so a subdirectory invocation resolves
    the same tree. A missing key warns on stderr (exit code unaffected)."""
    raw = arg_value if arg_value else None
    source = "argument"
    if raw is None:
        raw = _facts_raw(repo_root, facts_key)
        source = "facts"
    if raw is None or not raw.strip():
        if source == "facts":
            _warn(f"{facts_key} missing from facts; falling back to {default}")
        raw = default
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path


def _facts_raw(repo_root: Path, key: str) -> str | None:
    if facts_paths is None:
        _warn("facts parser unavailable; using conventional defaults")
        return None
    return facts_paths.resolve_toml_key_raw(repo_root, key)


def _is_backlog_ref(
    text: str, backlog_dir: Path, completed_dir: Path
) -> bool:
    """Decide whether a quoted ``.md`` span inside the origins paragraph
    is a backlog origin (not a review, guideline, or script path)."""
    parts = Path(text.replace(os.sep, "/")).parts
    if any(part == "backlog" for part in parts):
        return True
    # Facts-renamed backlog homes: a basename that exists in the resolved
    # top-level backlog or completed directory is a backlog reference too
    # (the rejected archive counts as well: an origin quoted after the
    # item was already rejected still names a backlog location).
    name = parts[-1] if parts else ""
    return bool(name) and (
        (backlog_dir / name).is_file()
        or (completed_dir / name).is_file()
        or (backlog_dir / REJECTED_DIR_NAME / name).is_file()
    )


def extract_origin_basenames(
    plan_text: str, backlog_dir: Path, completed_dir: Path
) -> list[str]:
    """Extract the plan's own origins-block basenames, in order, deduped.

    The block starts at the "Backlog origins (scope of record)" header
    line and runs through its first blank line (real plans wrap the block
    across prose continuation lines); a single `Backlog origin:` line is
    the other accepted opener, and the singular line ends the origins paragraph. Every backtick span on those lines
    that ends in ``.md`` and names a backlog location contributes its
    basename; a plan with no such block yields an empty list.
    """
    basenames: list[str] = []
    seen: set[str] = set()
    in_block = False
    items_seen = False
    blanks_before_items = 0
    for line in plan_text.splitlines():
        header_just_matched = False
        if not in_block:
            if ORIGINS_HEADER_RE.match(line):
                in_block = True
                header_just_matched = True
            elif ORIGIN_SINGULAR_RE.match(line):
                # The singular line ends the origins paragraph.
                text = (
                    ORIGIN_SINGULAR_RE.match(line)
                    .group(1)
                    .strip()
                    .strip("`")
                    .rstrip(".,;:")
                )
                if text.endswith(".md") and _is_backlog_ref(
                    text, backlog_dir, completed_dir
                ):
                    name = Path(text.replace(os.sep, "/")).name
                    if name not in seen:
                        seen.add(name)
                        basenames.append(name)
                    break
                continue
            else:
                continue
        elif not line.strip():
            # Blank-line grammar: exactly ONE blank line is tolerated
            # between the header line and the first list item (the
            # witnessed frozen archived plan carries that shape); any
            # blank line after list items begin ends the block.
            if items_seen or blanks_before_items >= 1:
                break
            blanks_before_items += 1
            continue
        if not header_just_matched:
            items_seen = True
        for span in BACKTICK_SPAN_RE.findall(line):
            text = span.strip()
            if not text.endswith(".md"):
                continue
            if not _is_backlog_ref(text, backlog_dir, completed_dir):
                continue
            name = Path(text.replace(os.sep, "/")).name
            if name and name not in seen:
                seen.add(name)
                basenames.append(name)
    return basenames


BARE_ORIGIN_LINE_RE = re.compile(
    r"^\s*(?:\[[^\]]*\]\s*)?(?:Backlog\s+)?[Oo]rigin\s*:\s*`?([^`\s]+\.md)`?\s*$",
    re.IGNORECASE,
)


def extract_coverage_origin_basenames(
    plan_text: str, backlog_dir: Path, completed_dir: Path
) -> list[str]:
    """Coverage-scoped superset of ``extract_origin_basenames``: the
    origins block and singular line, PLUS bare ``Origin:`` header lines
    (including a ``[github: ...]`` prefix). Bare lines count only in the
    plan's header region (title line through the first ``## `` heading)
    so body prose never matches, and only when the ``.md`` path is a
    backlog reference."""
    basenames = list(extract_origin_basenames(plan_text, backlog_dir, completed_dir))
    seen = set(basenames)
    header_region = plan_text
    heading = re.search(r"^## ", plan_text, re.MULTILINE)
    if heading:
        header_region = plan_text[: heading.start()]
    for line in header_region.splitlines():
        match = BARE_ORIGIN_LINE_RE.match(line)
        if not match:
            continue
        text = match.group(1)
        if not _is_backlog_ref(text, backlog_dir, completed_dir):
            continue
        name = Path(text.replace(os.sep, "/")).name
        if name not in seen:
            seen.add(name)
            basenames.append(name)
    return basenames


def classify_origin(
    basename: str, backlog_dir: Path, completed_dir: Path
) -> tuple[str, str]:
    """Return (state, detail) for one origin basename.

    States: ``completed`` (file sits under the completed directory),
    ``rejected`` (file sits under the backlog directory's ``rejected/``
    archive: an explicit decision against the work, closed like any
    other disposition),
    ``closed`` (top-level item header carries Status: closed/done),
    ``open`` (top-level item without a closure declaration), and
    ``missing`` (neither archived nor present at the top level; something
    other than the documented dispositions happened to it, so it fails
    closed like an open straggler)."""
    if completed_dir.is_dir():
        found = next(
            (p for p in sorted(completed_dir.rglob(basename)) if p.is_file()),
            None,
        )
        if found is not None:
            return "completed", "archived under the completed directory"
    rejected_dir = backlog_dir / REJECTED_DIR_NAME
    if rejected_dir.is_dir():
        found = next(
            (p for p in sorted(rejected_dir.rglob(basename)) if p.is_file()),
            None,
        )
        if found is not None:
            return "rejected", "archived under the rejected directory"
    top = backlog_dir / basename
    if top.is_file():
        try:
            lines = top.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()[:STATUS_HEADER_LINES]
        except OSError as exc:
            return "open", f"unreadable at the backlog top level: {exc}"
        for line in lines:
            match = STATUS_LINE_RE.match(line)
            if match:
                value = match.group(1)
                if STATUS_CLOSED_VALUE_RE.match(value):
                    return "closed", "closed in place (status closed/done)"
                covered = STATUS_COVERED_VALUE_RE.match(value)
                if covered:
                    return (
                        "covered",
                        f"covered by {covered.group(1).strip()}",
                    )
        return "open", "open at the backlog top level"
    return "missing", "not found under the backlog directory"


def run_plan_mode(
    plan_path: Path, backlog_dir: Path, completed_dir: Path, warn_only: bool
) -> int:
    """Archive gate: only THIS plan's origins can block, and only without
    ``--warn``. No origins block passes trivially."""
    try:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"error: cannot read plan {plan_path}: {exc}", file=sys.stderr)
        return 2
    basenames = extract_origin_basenames(text, backlog_dir, completed_dir)
    if not basenames:
        print("check_plan_origins_closed: no origins block; nothing to verify")
        return 0
    # Dispositions undercount warning (never exit-affecting): when the
    # plan's origins-dispositions section lists more basenames than the
    # origins block parsed, the block was likely misread (witnessed
    # blank-line trap), so say so loudly.
    listed = _dispositions_basenames(text, backlog_dir, completed_dir)
    if len(listed) > len(basenames):
        _warn(
            f"{plan_path.name}: origins dispositions list {len(listed)} "
            f"basenames but the origins block parsed {len(basenames)}; "
            f"check the origins block for a parser undercount"
        )
    stragglers: list[tuple[str, str]] = []
    for name in basenames:
        state, detail = classify_origin(name, backlog_dir, completed_dir)
        if state in PASS_STATES:
            continue
        if state == "missing" and _disposition_consult(text, name):
            continue  # fold-then-delete: the plan's own disposition section anchors it
        stragglers.append((name, detail))
    if not stragglers:
        print(
            f"check_plan_origins_closed: ok "
            f"({len(basenames)}/{len(basenames)} origins closed)"
        )
        return 0
    for name, detail in stragglers:
        if warn_only:
            print(
                f"warning: {plan_path.name}: origin {name} unresolved "
                f"({detail})"
            )
        else:
            print(f"straggler: {name} ({detail})")
    if warn_only:
        print(
            "check_plan_origins_closed: warn arm: "
            f"{len(stragglers)} unresolved origin(s); exit 0"
        )
        return 0
    print(
        f"check_plan_origins_closed: {len(stragglers)} straggler(s) of "
        f"{len(basenames)} origin(s); disposition or record why open",
        file=sys.stderr,
    )
    return 1


def run_corpus_mode(
    plans_dir: Path,
    backlog_dir: Path,
    completed_dir: Path,
    repo_root: Path | None = None,
    active_plans_dir: Path | None = None,
) -> int:
    """Corpus warn arm: scan every archived plan, warn per unresolved
    origin, always exit 0 (the maintenance survey owns this surface)."""
    if not plans_dir.is_dir():
        _warn(f"plans directory not found: {plans_dir}")
        print("check_plan_origins_closed: corpus scan: no archived plans; exit 0")
        return 0
    plans = sorted(plans_dir.rglob("*.md"))
    registry: Path | None = None
    if repo_root is not None:
        registry = resolve_dir(
            None, repo_root, "doc_registry_rel", DEFAULT_DOC_REGISTRY_REL
        )
    unresolved = 0
    for plan in plans:
        try:
            text = plan.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            _warn(f"cannot read archived plan {plan.name}: {exc}")
            continue
        for name in extract_origin_basenames(text, backlog_dir, completed_dir):
            state, detail = classify_origin(name, backlog_dir, completed_dir)
            if state == "covered":
                # Covered items classify as covered, never closed; the
                # corpus warn fires only when the covering plan is no
                # longer top-level under the active plans directory.
                witness = detail[len("covered by "):].strip()
                witness_path = Path(witness)
                if not witness_path.is_absolute() and repo_root is not None:
                    witness_path = repo_root / witness
                witness_live = (
                    witness_path.is_absolute()
                    and witness_path.is_file()
                    and active_plans_dir is not None
                    and witness_path.parent == active_plans_dir
                )
                if not witness_live:
                    print(
                        f"warning: {plan.name}: origin {name} covered by "
                        f"{witness}, which is no longer top-level under "
                        f"the active plans directory"
                    )
                    unresolved += 1
                continue
            if state in PASS_STATES:
                continue
            if state == "missing" and repo_root is not None:
                if _disposition_consult(text, name):
                    continue  # disposition-anchored migrated origin
                if _registry_migration_audit_row(
                    repo_root, name, registry
                ):
                    continue  # registry migration-audit-anchored migrated origin
            print(
                f"warning: {plan.name}: origin {name} unresolved ({detail})"
            )
            unresolved += 1
    print(
        f"check_plan_origins_closed: corpus scan: {len(plans)} archived "
        f"plan(s), {unresolved} unresolved origin(s) (warn arm; exit 0)"
    )
    return 0


REMEDY_BY_STATE = {
    "completed": (
        "supersede-or-explicit-revival: the covering plan already executed; "
        "reject the later plan as superseded or explicitly revive the origin "
        "with the decision recorded"
    ),
    "rejected": (
        "revival-is-a-new-decision: the origin was rejected; using it again "
        "requires a recorded revival decision, not a silent new plan"
    ),
    "deferred": (
        "revive-or-explicitly-supersede: the covering plan is parked under "
        "deferred; revive it or record the later plan as its supersession"
    ),
}


def _find_covering_citers(
    origin_name: str,
    scan_dirs: list[tuple[Path, str]],
    declaring: Path,
    backlog_dir: Path,
    completed_dir: Path,
) -> list[tuple[Path, str]]:
    """Every OTHER plan citing ``origin_name`` across the scan surfaces,
    as (plan path, citer state) pairs."""
    citers: list[tuple[Path, str]] = []
    for directory, state in scan_dirs:
        if not directory.is_dir():
            continue
        for plan in sorted(directory.rglob("*.md")):
            if plan.resolve() == declaring.resolve():
                continue
            try:
                text = plan.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            names = extract_coverage_origin_basenames(
                text, backlog_dir, completed_dir
            )
            if origin_name in names:
                citers.append((plan, state))
    return citers


def run_check_coverage_mode(
    plan_path: Path,
    backlog_dir: Path,
    completed_dir: Path,
    active_plans_dir: Path,
    completed_plans_dir: Path,
) -> int:
    """Duplicate-origin coverage gate: exit 0 clean, 1 conflict naming the
    covering plan and the state-specific remedy, 2 tool error."""
    try:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"error: cannot read plan {plan_path}: {exc}", file=sys.stderr)
        return 2
    names = extract_coverage_origin_basenames(text, backlog_dir, completed_dir)
    if not names:
        print("check_plan_origins_closed: no origins; coverage gate trivially clean")
        return 0
    scan_dirs = [
        (active_plans_dir, "active"),
        (active_plans_dir / "deferred", "deferred"),
        (completed_plans_dir, "completed"),
        (active_plans_dir / "rejected", "rejected"),
    ]
    conflicts = 0
    for name in names:
        for citer, citer_state in _find_covering_citers(
            name, scan_dirs, plan_path, backlog_dir, completed_dir
        ):
            conflicts += 1
            remedy = REMEDY_BY_STATE.get(
                citer_state,
                "first-landed wins - fold the later plan into the covering "
                "plan as an amendment, or reject the later plan as superseded",
            )
            print(
                f"origin coverage conflict: {name} is already cited by "
                f"{citer} ({citer_state}); {remedy}"
            )
    if conflicts:
        return 1
    print("check_plan_origins_closed: coverage gate clean; no covering citer")
    return 0


def _flip_status_line(text: str, witness: str) -> tuple[str, bool]:
    """Rewrite the first header ``Status:`` line's value to the covered
    witness, preserving the line's non-status prefix. Returns
    (new text, flipped)."""
    for line in text.splitlines()[:STATUS_HEADER_LINES]:
        match = STATUS_LINE_RE.match(line)
        if not match:
            continue
        value = match.group(1)
        covered = STATUS_COVERED_VALUE_RE.match(value)
        if covered and covered.group(1).strip() == witness:
            return text, False  # idempotent: same-plan witness already present
        if covered:
            return text, False  # caller reports the conflict
        new_line = line[: match.start(1)] + f"covered ({witness})"
        return text.replace(line, new_line, 1), True
    return text, False


def run_mark_covered_mode(
    plan_path: Path,
    backlog_dir: Path,
    completed_dir: Path,
    repo_root: Path,
) -> int:
    """Landing-closeout covered flip: each named open top-level origin's
    header Status becomes ``covered (<repo-relative plan path>)``. Exit 0
    on success/no-op-with-skips, 1 on a different-plan-witness conflict
    (bytes unchanged), 2 on tool error."""
    try:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"error: cannot read plan {plan_path}: {exc}", file=sys.stderr)
        return 2
    names = extract_coverage_origin_basenames(text, backlog_dir, completed_dir)
    if not names:
        print("check_plan_origins_closed: no origins; nothing to mark covered")
        return 0
    try:
        witness = plan_path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        witness = plan_path.as_posix()
    flipped = 0
    for name in names:
        state, detail = classify_origin(name, backlog_dir, completed_dir)
        if state == "covered":
            covering = detail[len("covered by "):].strip()
            if covering == witness:
                print(f"already covered by this plan: {name}")
                continue
            print(
                f"refusing to mark covered: {name} is already covered by "
                f"{covering} (a different plan); first-landed wins"
            )
            return 1
        if state == "open":
            top = backlog_dir / name
            try:
                item_text = top.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                print(f"skip: {name}: unreadable ({exc})")
                continue
            new_text, did = _flip_status_line(item_text, witness)
            if did:
                top.write_text(new_text, encoding="utf-8")
                flipped += 1
                print(f"covered: {name} (by {witness})")
            else:
                print(f"skip: {name}: no open status header line found")
        else:
            print(f"skip: {name}: {state} ({detail})")
    print(f"check_plan_origins_closed: marked {flipped} origin(s) covered")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify plan backlog origins left the top level: archive gate "
            "on one plan's own origins, corpus-wide warn arm otherwise"
        )
    )
    parser.add_argument(
        "--plan",
        help="plan file to gate in archive mode (its own origins only)",
    )
    parser.add_argument(
        "--warn",
        action="store_true",
        help="plan mode: report stragglers as warnings and exit 0",
    )
    parser.add_argument(
        "--repo-root",
        help=(
            "repository root anchoring facts and relative paths "
            "(default: git toplevel of the current directory)"
        ),
    )
    parser.add_argument(
        "--backlog-dir",
        help="backlog top-level directory (overrides the facts key backlog_dir)",
    )
    parser.add_argument(
        "--completed-dir",
        help=(
            "completed directory "
            "(overrides the facts key backlog_completed_dir)"
        ),
    )
    parser.add_argument(
        "--plans-dir",
        help=(
            "archived plans directory for the corpus scan "
            "(overrides the facts key plans_completed_dir)"
        ),
    )
    parser.add_argument(
        "--active-plans-dir",
        help=(
            "active plans directory for the coverage modes "
            "(overrides the facts key plans_dir)"
        ),
    )
    parser.add_argument(
        "--check-coverage",
        dest="check_coverage",
        help="plan file to gate in duplicate-origin coverage mode",
    )
    parser.add_argument(
        "--mark-covered",
        dest="mark_covered",
        help="plan file whose named open origins flip to covered",
    )
    args = parser.parse_args(argv)

    repo_root = resolve_repo_root(args.repo_root)
    backlog_dir = resolve_dir(
        args.backlog_dir, repo_root, "backlog_dir", DEFAULT_BACKLOG_DIR
    )
    completed_dir = resolve_dir(
        args.completed_dir,
        repo_root,
        "backlog_completed_dir",
        DEFAULT_COMPLETED_DIR,
    )

    if args.check_coverage or args.mark_covered:
        target = args.check_coverage or args.mark_covered
        plan_path = Path(target).expanduser()
        if not plan_path.is_absolute():
            plan_path = repo_root / plan_path
        if not plan_path.is_file():
            parser.error(f"plan file not found: {plan_path}")
        if args.mark_covered:
            return run_mark_covered_mode(
                plan_path, backlog_dir, completed_dir, repo_root
            )
        active_plans_dir = resolve_dir(
            args.active_plans_dir, repo_root, "plans_dir", DEFAULT_ACTIVE_PLANS_DIR
        )
        completed_plans_dir = resolve_dir(
            args.plans_dir, repo_root, "plans_completed_dir", DEFAULT_PLANS_DIR
        )
        return run_check_coverage_mode(
            plan_path,
            backlog_dir,
            completed_dir,
            active_plans_dir,
            completed_plans_dir,
        )

    if args.plan:
        plan_path = Path(args.plan).expanduser()
        if not plan_path.is_absolute():
            plan_path = repo_root / plan_path
        if not plan_path.is_file():
            parser.error(f"--plan file not found: {plan_path}")
        return run_plan_mode(plan_path, backlog_dir, completed_dir, args.warn)

    plans_dir = resolve_dir(
        args.plans_dir, repo_root, "plans_completed_dir", DEFAULT_PLANS_DIR
    )
    active_plans_dir = resolve_dir(
        args.active_plans_dir, repo_root, "plans_dir", DEFAULT_ACTIVE_PLANS_DIR
    )
    return run_corpus_mode(
        plans_dir, backlog_dir, completed_dir, repo_root, active_plans_dir
    )


if __name__ == "__main__":
    raise SystemExit(main())
