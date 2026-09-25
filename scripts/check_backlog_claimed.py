#!/usr/bin/env python3
"""Claimed-origin mechanical checker (P51 origin 1).

Answers one question mechanically: is this backlog item CLAIMED by a
top-level plan? A plan claims an item when the item's filename stem (or
that stem with its leading ``YYYY-MM-DD-`` prefix stripped) occurs as a
hyphen-bounded segment of any line of a TOP-LEVEL plan file. The plans
directory's ``completed/``, ``deferred/``, and other subdirectories are
never scanned, because only a top-level plan's origin list or
validation-gate literal naming the item is a claim. The bulk disposition
sweep gate (agents/skills/maintenance/SKILL.md) treats a claimed report
as skip-and-annotate: the claimed item is never moved; ownership beats
the triage verdict, and exit 1 is the gate's stop signal.

Contract (plan docs/history/plans/2026-09-23-p51-plans-authoring-surface-hygiene.md,
Task 1; origin docs/history/backlog/2026-09-22-deferral-sweeps-must-cross-check-claimed-origins.md):

- Repeatable ``--slug`` accepting kebab-case stems or ``.md`` paths
  (normalized to filename stems).
- ``--plans-dir`` override; without it the directory resolves from the
  repo facts file (``.ai-playbook/facts.md``, TOML ``plans_dir`` key)
  with conventional default ``docs/history/plans/``. Relative values anchor at
  the repo root, never the process CWD, and no machine-specific
  absolute path is hardcoded.
- Hyphen-bounded matching: an occurrence counts when the characters
  immediately before and after it (when present) are not alphanumeric:
  a path separator, a dot, a backtick, a space, or a hyphen bounds the
  segment, while a longer word's continuation letter does not
  (``example-origin-itemx`` never matches ``example-origin-item``).
- One finding line per hit: ``CLAIMED <stem> -> <plan-path>:<line>``
  (both match forms hitting the same line report once).
- Exit 0 when no candidate is claimed, 1 when any is, 2 on usage or
  path errors.

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import facts_paths
except ImportError:  # pragma: no cover
    facts_paths = None  # type: ignore

DEFAULT_PLANS_DIR = "docs/history/plans/"
FACTS_PLANS_DIR_KEY = "plans_dir"

# A stem's second match form: the leading calendar-date prefix, stripped.
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")

# Hyphen-bounded occurrence: not preceded and not followed by an
# alphanumeric character (string edges count as boundaries).
SEGMENT_RE = r"(?<![A-Za-z0-9]){needle}(?![A-Za-z0-9])"


def repo_root() -> Path:
    """The repo root anchoring facts-key and default-dir resolution.

    Derived from this script's own location (``scripts/`` parent), so a
    subdirectory or cross-tree invocation resolves the same tree without
    any machine-specific path.
    """
    return Path(__file__).resolve().parent.parent


def normalize_slug(raw: str) -> str | None:
    """Normalize one ``--slug`` value to a filename stem.

    Accepts a kebab-case stem (``2026-09-20-example-origin-item``) or a
    ``.md`` path (``docs/history/backlog/2026-09-20-example-origin-item.md``);
    both normalize to the filename stem. Returns ``None`` for a value
    with no stem (empty or slash-only).
    """
    value = raw.strip()
    if not value:
        return None
    stem = Path(value).stem
    return stem or None


def match_forms(stem: str) -> list[str]:
    """The stem's match forms: itself, plus its date-stripped form when a
    leading ``YYYY-MM-DD-`` prefix is present."""
    forms = [stem]
    stripped = DATE_PREFIX_RE.sub("", stem, count=1)
    if stripped != stem and stripped:
        forms.append(stripped)
    return forms


def line_hits(line: str, forms: list[str]) -> bool:
    """Whether any match form occurs in the line as a hyphen-bounded
    segment."""
    for form in forms:
        if re.search(SEGMENT_RE.format(needle=re.escape(form)), line):
            return True
    return False


def resolve_plans_dir(explicit: str | None) -> Path:
    """Resolve the plans directory: the explicit ``--plans-dir`` argument,
    then the repo facts file's ``plans_dir`` TOML key, then the
    conventional default. Relative values anchor at the repo root, never
    the process CWD, so a subdirectory invocation resolves the same
    tree. A missing facts key warns on stderr (exit code unaffected)."""
    if explicit:
        raw = explicit
    else:
        raw = None
        if facts_paths is not None:
            raw = facts_paths.resolve_toml_key_raw(repo_root(), FACTS_PLANS_DIR_KEY)
        else:  # pragma: no cover
            print(
                "warning: facts parser unavailable; using conventional default",
                file=sys.stderr,
            )
        if not raw or not raw.strip():
            if raw is not None:
                print(
                    f"warning: {FACTS_PLANS_DIR_KEY} missing from facts; "
                    f"falling back to {DEFAULT_PLANS_DIR}",
                    file=sys.stderr,
                )
            raw = DEFAULT_PLANS_DIR
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = repo_root() / path
    return path


def scan(plans_dir: Path, slugs: list[str]) -> list[str]:
    """Scan top-level plan files and return the finding lines.

    Only the directory's direct ``.md`` file children are scanned
    (``completed/``, ``deferred/``, and other subdirectories are never
    claims). Files are walked in sorted order and lines in ascending
    order for deterministic output; both match forms hitting the same
    line report once per candidate.
    """
    candidates = [(slug, match_forms(slug)) for slug in slugs]
    reported: set[tuple[str, str, int]] = set()
    findings: list[str] = []
    for plan in sorted(plans_dir.iterdir()):
        if not plan.is_file() or plan.suffix != ".md":
            continue
        try:
            text = plan.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            print(f"warning: unreadable plan file skipped: {plan}", file=sys.stderr)
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for slug, forms in candidates:
                key = (slug, plan.name, lineno)
                if key in reported:
                    continue
                if line_hits(line, forms):
                    reported.add(key)
                    findings.append(f"CLAIMED {slug} -> {plan}:{lineno}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report backlog items claimed by a top-level plan "
            "(claimed-origin mechanical checker; exit 1 is the "
            "bulk disposition sweep gate's stop signal)."
        )
    )
    parser.add_argument(
        "--slug",
        action="append",
        required=True,
        metavar="STEM_OR_MD_PATH",
        help="candidate backlog item, as a filename stem or a .md path; "
        "repeat for every candidate in one invocation",
    )
    parser.add_argument(
        "--plans-dir",
        default=None,
        metavar="DIR",
        help="plans directory override (default: the repo facts file's "
        f"{FACTS_PLANS_DIR_KEY} key, else {DEFAULT_PLANS_DIR})",
    )
    args = parser.parse_args(argv)

    slugs: list[str] = []
    for raw in args.slug:
        slug = normalize_slug(raw)
        if slug is None:
            parser.error(f"--slug has no filename stem: {raw!r}")
        slugs.append(slug)

    plans_dir = resolve_plans_dir(args.plans_dir)
    if not plans_dir.is_dir():
        print(f"error: plans directory not found: {plans_dir}", file=sys.stderr)
        return 2

    try:
        findings = scan(plans_dir, slugs)
    except OSError as exc:
        # An existing-but-unreadable plans directory is a path error, not a
        # crash: exit 2 with an error line, preserving the exit contract.
        print(
            f"error: plans directory not scannable: {plans_dir}: {exc}",
            file=sys.stderr,
        )
        return 2
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
