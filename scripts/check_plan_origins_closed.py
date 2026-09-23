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
through its first blank line); review, guideline, and script paths quoted
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
DEFAULT_PLANS_DIR = "docs/plans/completed"
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
BACKTICK_SPAN_RE = re.compile(r"`([^`]+)`")
# Tolerates the corpus shapes ``Status: open``, ``- **Status:** open``,
# and ``Status: done; plan created ...``: an optional bullet, optional
# bold, then the ``status:`` label.
STATUS_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\*\*)?\s*status\s*(?:\*\*)?\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)
# closed/done as the status VALUE; a hyphenated continuation such as
# ``done-for-now`` is not a closure declaration.
STATUS_CLOSED_VALUE_RE = re.compile(
    r"^(?:closed|done)(?![A-Za-z0-9_-])", re.IGNORECASE
)

PASS_STATES = ("completed", "closed", "rejected")


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


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
    across prose continuation lines). Every backtick span on those lines
    that ends in ``.md`` and names a backlog location contributes its
    basename; a plan with no such block yields an empty list.
    """
    basenames: list[str] = []
    seen: set[str] = set()
    in_block = False
    for line in plan_text.splitlines():
        if not in_block:
            if ORIGINS_HEADER_RE.match(line):
                in_block = True
            else:
                continue
        elif not line.strip():
            break  # first blank line ends the origins paragraph
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
            if match and STATUS_CLOSED_VALUE_RE.match(match.group(1)):
                return "closed", "closed in place (status closed/done)"
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
    stragglers: list[tuple[str, str]] = []
    for name in basenames:
        state, detail = classify_origin(name, backlog_dir, completed_dir)
        if state in PASS_STATES:
            continue
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
    plans_dir: Path, backlog_dir: Path, completed_dir: Path
) -> int:
    """Corpus warn arm: scan every archived plan, warn per unresolved
    origin, always exit 0 (the maintenance survey owns this surface)."""
    if not plans_dir.is_dir():
        _warn(f"plans directory not found: {plans_dir}")
        print("check_plan_origins_closed: corpus scan: no archived plans; exit 0")
        return 0
    plans = sorted(plans_dir.rglob("*.md"))
    unresolved = 0
    for plan in plans:
        try:
            text = plan.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            _warn(f"cannot read archived plan {plan.name}: {exc}")
            continue
        for name in extract_origin_basenames(text, backlog_dir, completed_dir):
            state, detail = classify_origin(name, backlog_dir, completed_dir)
            if state in PASS_STATES:
                continue
            print(
                f"warning: {plan.name}: origin {name} unresolved ({detail})"
            )
            unresolved += 1
    print(
        f"check_plan_origins_closed: corpus scan: {len(plans)} archived "
        f"plan(s), {unresolved} unresolved origin(s) (warn arm; exit 0)"
    )
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
    return run_corpus_mode(plans_dir, backlog_dir, completed_dir)


if __name__ == "__main__":
    raise SystemExit(main())
