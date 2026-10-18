#!/usr/bin/env python3
"""Plans-root liveness probe (the authoring-round-liveness-gap plan, 2026-10-05).

Enumerates untracked non-ignored ``.md`` entries at the plans root and
classifies each one live or stranded against the repository's authoring
claims, so a routine turn settles an untracked plan file's status in one
read instead of a forensic pass:

- live: at least one fresh authoring claim names it (the claim's ``updated:``
  within one cadence period, default 120 minutes, and the claim's raw text
  contains the plan's slug, the basename stem with its leading
  ``YYYY-MM-DD-`` prefix stripped, or the full basename).
- stranded: no fresh claim names it. A stranded classification is the
  modeled fail class; a live one is left alone.

Resolution rules: the plans directory and tmp directory come from the repo
facts document's TOML ``plans_dir`` / ``tmp_dir`` keys (the shared
``facts_paths.py`` parser) with the conventional fallbacks
``docs/history/plans`` and ``docs/tmp``; the claims directory is
``<tmp_dir>/authoring-claims``. The G1a discovery arm's facts ``tmp_dir``
override caveat extends to this reader of the surface. Root-level
``.md`` files are candidates beside the plan-directory shape (the
plan-directory-shape plan): an untracked ``<slug>/PLAN.md`` charter path
under the plans root is a directory candidate, reported at its charter
path and classified by claim match on the directory slug, and an
untracked ``<slug>/`` directory whose charter is absent reports stranded
naming the charterless reason (a tracked charter means the plan landed
and is never a candidate). The ``completed/``, ``deferred/``, and
``rejected/`` state subdirectories are never enumerated.

Outcome contract (scripts/OUTCOME_CONTRACT.md, born-conformant): the run
ends with exactly one final ``OUTCOME:`` line after human-readable evidence
lines. Exit 0 (``OUTCOME: pass``) when zero candidates are stranded; exit 1
(``OUTCOME: fail``) naming the stranded paths; exit 3 (``OUTCOME:
tool_error``) on a non-repository ``--repo``, a usage violation, an
unreadable resolved claims directory while candidates exist, or any other
unheld environment assumption. A claim whose ``updated:`` cannot be parsed
as an ISO timestamp with offset is skipped with a warning line, never
classified. No indeterminate class exists. The probe mutates nothing.
"""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from facts_paths import resolve_toml_key_raw
except ImportError:  # deployment gap: handled as tool error in main()
    resolve_toml_key_raw = None  # type: ignore[assignment]
try:
    # The charter filename is the shared resolver's grammar constant (the
    # one grammar derivation every consumer imports); this probe only ever
    # detects the charter path, never re-derives the plan grammar.
    from plan_shape import CHARTER_FILENAME
except ImportError:  # deployment gap: fails closed only when a directory hint needs it
    CHARTER_FILENAME = None  # type: ignore[assignment]

OUTCOME_PASS = "OUTCOME: pass"
OUTCOME_FAIL = "OUTCOME: fail"
OUTCOME_TOOL_ERROR = "OUTCOME: tool_error"

DEFAULT_PLANS_DIR = "docs/history/plans"
DEFAULT_TMP_DIR = "docs/tmp"
CLAIMS_DIRNAME = "authoring-claims"
DEFAULT_CADENCE_MINUTES = 120

DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
UPDATED_LINE_RE = re.compile(r"^updated:\s*(.+)\s*$", re.MULTILINE)

# The plans root's archive state subdirectories: never enumerated, as file
# candidates or as directory hints.
STATE_DIR_NAMES = ("completed", "deferred", "rejected")


class ProbeToolError(Exception):
    """An unheld operating-context assumption; the caller re-derives."""


class Candidate:
    """One untracked plans-root candidate.

    Attributes:
        path: the repo-relative report path: the file path for the
            single-file shape, the charter path for a plan directory,
            the directory path (trailing slash) when charterless.
        slug: the date-prefix-stripped slug the claim match reads.
        identity: the full name the claim match also reads (the file's
            basename, or the plan directory's name).
        directory: True for a plan-directory candidate.
        charterless: True when the plan directory carries no charter
            (always stranded, naming that reason).
    """

    def __init__(self, path: str, slug: str, identity: str, directory: bool, charterless: bool):
        self.path = path
        self.slug = slug
        self.identity = identity
        self.directory = directory
        self.charterless = charterless


class OutcomeArgumentParser(argparse.ArgumentParser):
    """argparse override per the outcome contract's usage rule: a usage
    violation is a tool error, so ``error()`` prints the usage message plus
    a final ``OUTCOME: tool_error`` row on stderr and exits 3; ``--help``
    stays a metadata exit (usage text only, no OUTCOME row)."""

    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        print(OUTCOME_TOOL_ERROR, file=sys.stderr)
        raise SystemExit(3)


class Claim:
    """One parsed claim file; ``updated`` is None when unparseable."""

    def __init__(self, name: str, text: str, updated: datetime | None, iso_raw: str | None):
        self.name = name
        self.text = text
        self.updated = updated
        self.iso_raw = iso_raw


def git_toplevel(repo_arg: str) -> Path:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_arg), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise ProbeToolError(f"git toplevel probe failed for --repo {repo_arg!r}: {exc!r}") from exc
    if proc.returncode != 0 or not proc.stdout.strip():
        raise ProbeToolError(
            f"--repo does not resolve inside a git repository: {repo_arg!r} ({proc.stderr.strip()})"
        )
    return Path(proc.stdout.strip())


def facts_rel_value(repo_root: Path, key: str, fallback: str) -> str:
    """Read one TOML facts key (raw string), anchored to a clean relative posix form.

    A relative value keeps its repo-relative shape; an absolute value is
    re-expressed relative to the repo root (the probe only enumerates inside
    the repository). The conventional fallback backs a missing key, and the
    G1a discovery arm's facts ``tmp_dir``-override caveat extends here.
    """
    if resolve_toml_key_raw is None:
        raise ProbeToolError(
            "sibling facts_paths.py missing next to the probe copy: deploy it beside "
            "this script (the home copy keeps it as a symlink; cp -P preserves that)"
        )
    raw = resolve_toml_key_raw(repo_root, key)
    value = (raw if raw is not None else fallback).strip() or fallback
    value = value.rstrip("/")
    candidate = Path(value)
    if candidate.is_absolute():
        value = posixpath.relpath(candidate.as_posix(), repo_root.resolve().as_posix())
    return posixpath.normpath(value)


def enumerate_candidates(repo_root: Path, plans_rel: str) -> list[Candidate]:
    """Untracked non-ignored candidates at the plans root, repo-relative.

    Two shapes (the plan-directory-shape plan): root-level ``.md`` files
    (today's candidates, unchanged), and plan directories derived from the
    same untracked enumeration. The ``git ls-files --others`` listing
    reports the nested files of an untracked plan directory individually,
    so an untracked ``<slug>/PLAN.md`` charter path under the plans root
    is a directory candidate reported at its charter path, and an
    untracked ``<slug>/`` directory whose charter is absent (none
    untracked and none on disk; a tracked charter means the plan landed
    and is never a candidate) is a charterless directory candidate
    reported stranded. The ``completed/``, ``deferred/``, and
    ``rejected/`` state subdirectories are never enumerated, and a
    directory hint only fires for the directory shape's date-prefixed
    ``YYYY-MM-DD-`` name.
    """
    try:
        proc = subprocess.run(
            [
                "git", "-C", str(repo_root),
                "ls-files", "--others", "--exclude-standard", "--", plans_rel,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise ProbeToolError(f"git ls-files failed over {plans_rel!r}: {exc!r}") from exc
    if proc.returncode != 0:
        raise ProbeToolError(f"git ls-files failed over {plans_rel!r}: {proc.stderr.strip()}")
    candidates: list[Candidate] = []
    charter_hints: set[str] = set()
    other_hints: set[str] = set()
    prefix = plans_rel + "/"
    for line in proc.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        if posixpath.dirname(path) == plans_rel:
            if path.endswith(".md"):
                basename = posixpath.basename(path)
                candidates.append(
                    Candidate(
                        path=path,
                        slug=plan_slug(basename),
                        identity=basename,
                        directory=False,
                        charterless=False,
                    )
                )
            continue
        if not path.startswith(prefix) or not path.endswith(".md"):
            continue  # deeper paths outside the plans root are not candidates
        tail = path[len(prefix):]
        slug_dir = tail.split("/", 1)[0]
        if slug_dir in STATE_DIR_NAMES or not DATE_PREFIX_RE.match(slug_dir):
            continue
        if tail == f"{slug_dir}/{CHARTER_FILENAME}":
            charter_hints.add(slug_dir)
        else:
            other_hints.add(slug_dir)
    if (charter_hints or other_hints) and CHARTER_FILENAME is None:
        raise ProbeToolError(
            "sibling plan_shape.py missing next to the probe copy: deploy it beside "
            "this script (the home copy keeps it as a symlink; cp -P preserves that)"
        )
    for slug_dir in sorted(charter_hints):
        candidates.append(
            Candidate(
                path=f"{plans_rel}/{slug_dir}/{CHARTER_FILENAME}",
                slug=plan_slug(slug_dir),
                identity=slug_dir,
                directory=True,
                charterless=False,
            )
        )
    for slug_dir in sorted(other_hints - charter_hints):
        if (repo_root / plans_rel / slug_dir / CHARTER_FILENAME).is_file():
            continue  # a tracked charter: the plan landed; residue is not an untracked plan
        candidates.append(
            Candidate(
                path=f"{plans_rel}/{slug_dir}/",
                slug=plan_slug(slug_dir),
                identity=slug_dir,
                directory=True,
                charterless=True,
            )
        )
    return sorted(candidates, key=lambda cand: cand.path)


def load_claims(claims_dir: Path) -> tuple[list[Claim], list[str]]:
    """Parse every ``.md`` claim; unparseable claims are skipped with a warning."""
    claims: list[Claim] = []
    warnings: list[str] = []
    if not claims_dir.exists():
        return claims, warnings  # no claims directory: the empty-claims state
    if not claims_dir.is_dir():
        raise ProbeToolError(f"resolved claims directory is not a directory: {claims_dir}")
    try:
        names = sorted(entry.name for entry in os.scandir(claims_dir))
    except OSError as exc:
        raise ProbeToolError(f"claims directory unreadable: {claims_dir} ({exc!r})") from exc
    for name in names:
        if not name.endswith(".md"):
            continue
        path = claims_dir / name
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ProbeToolError(f"claim file unreadable: {path} ({exc!r})") from exc
        match = UPDATED_LINE_RE.search(text)
        updated: datetime | None = None
        iso_raw: str | None = None
        if match:
            iso_raw = match.group(1).strip()
            try:
                stamp = datetime.fromisoformat(iso_raw)
            except ValueError:
                stamp = None
            if stamp is not None and stamp.tzinfo is not None:
                updated = stamp
        if updated is None:
            warnings.append(
                f"warning: claim {name}: no parseable updated: timestamp; skipped"
            )
            continue
        claims.append(Claim(name, text, updated, iso_raw))
    return claims, warnings


def plan_slug(basename: str) -> str:
    stem = basename[: -len(".md")] if basename.endswith(".md") else basename
    return DATE_PREFIX_RE.sub("", stem, count=1)


def main(argv: list[str] | None = None) -> int:
    parser = OutcomeArgumentParser(
        prog="check_authoring_plans_liveness.py",
        description="Classify untracked plans-root .md entries live or stranded against the authoring claims.",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="repository root (default: the working directory)",
    )
    parser.add_argument(
        "--cadence-minutes",
        type=int,
        default=DEFAULT_CADENCE_MINUTES,
        help="freshness bound for an authoring claim's updated: timestamp (default: 120)",
    )
    args = parser.parse_args(argv)

    try:
        repo_root = git_toplevel(args.repo)
        plans_rel = facts_rel_value(repo_root, "plans_dir", DEFAULT_PLANS_DIR)
        tmp_rel = facts_rel_value(repo_root, "tmp_dir", DEFAULT_TMP_DIR)
        claims_dir = repo_root / tmp_rel / CLAIMS_DIRNAME

        candidates = enumerate_candidates(repo_root, plans_rel)
        if not candidates:
            print("summary: candidates=0 live=0 stranded=0")
            print(OUTCOME_PASS)
            return 0

        claims, warnings = load_claims(claims_dir)
        now = datetime.now(timezone.utc)
        cadence_seconds = args.cadence_minutes * 60
        fresh_claims = [c for c in claims if (now - c.updated).total_seconds() <= cadence_seconds]

        live_count = 0
        stranded_paths: list[str] = []
        for cand in candidates:
            if cand.charterless:
                stranded_paths.append(cand.path)
                print(
                    f"stranded: {cand.path} "
                    f"(charterless: no {CHARTER_FILENAME} charter in the "
                    "untracked plan directory)"
                )
                continue
            namers = [
                c for c in fresh_claims
                if (cand.slug in c.text) or (cand.identity in c.text)
            ]
            if namers:
                live_count += 1
                newest = max(namers, key=lambda c: c.updated)
                print(f"live: {cand.path} (claim {newest.name} updated {newest.iso_raw})")
            else:
                stranded_paths.append(cand.path)
                print(f"stranded: {cand.path} (no fresh claim names it)")

        for warning in warnings:
            print(warning)
        stranded_count = len(stranded_paths)
        summary = (
            f"summary: candidates={len(candidates)} live={live_count} stranded={stranded_count}"
        )
        if warnings:
            summary += f" unparseable_claims={len(warnings)}"
        print(summary)

        if stranded_count:
            print(OUTCOME_FAIL)
            return 1
        print(OUTCOME_PASS)
        return 0
    except ProbeToolError as exc:
        print(f"error: {exc}")
        print(OUTCOME_TOOL_ERROR)
        return 3
    except Exception as exc:  # never end without a final OUTCOME: line
        print(f"error: unexpected probe failure: {exc!r}")
        print(OUTCOME_TOOL_ERROR)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
