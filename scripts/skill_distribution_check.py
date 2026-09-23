#!/usr/bin/env python3
"""Skill distribution integrity check.

Enumerates configured platform destinations for an installed skill, resolves
symlinks and deduplicates to physical copies, compares each copy against the
source, and reports the classification per destination:

MISSING, CURRENT, STALE, OLDER, NEWER, SKIP (destination resolves to the
source tree itself; reported, never written).

With ``--refresh`` only MISSING and provably OLDER destinations are
overwritten; a STALE (unknown drift direction, including stampless drift or
equal stamps) or NEWER destination requires the explicit ``--downgrade``
consent flag. Refresh replaces the destination with the source tree including
removal of extraneous destination files, re-verifies after copying, and never
touches the network.

Exit codes: 0 when every destination is CURRENT or SKIP, 1 when any is not,
2 on usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_DEST_ROOTS = ("~/.agents/skills", "~/.claude/skills", "~/.cursor/skills")


def fail_usage(message: str) -> int:
    print(f"usage error: {message}", file=sys.stderr)
    return 2


def repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def parse_version_stamp(skill_dir: Path) -> str | None:
    """Read a version stamp from SKILL.md frontmatter: nested
    ``metadata.version`` or a top-level ``version:``."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None
    lines: list[str]
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    in_metadata = False
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        indented = line.startswith((" ", "\t"))
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if not indented:
            in_metadata = False
        if not indented and key == "metadata" and not value:
            in_metadata = True
            continue
        if key == "version" and value and (in_metadata == indented):
            return value.strip("'\"")
    return None


def version_orders_below(a: str | None, b: str | None) -> bool | None:
    """True when stamp a orders below b, False when above, None when
    unordered (either absent or equal). Numeric-aware dot-segment order."""
    if a is None or b is None or a == b:
        return None
    try:
        segs_a = [int(s) for s in a.split(".")]
        segs_b = [int(s) for s in b.split(".")]
    except ValueError:
        return None
    width = max(len(segs_a), len(segs_b))
    segs_a += [0] * (width - len(segs_a))
    segs_b += [0] * (width - len(segs_b))
    if segs_a == segs_b:
        return None
    return segs_a < segs_b


def digest_tree(skill_dir: Path) -> frozenset[tuple[str, str]]:
    entries: set[tuple[str, str]] = set()
    for path in sorted(skill_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(skill_dir).as_posix()
            entries.add((rel, hashlib.sha256(path.read_bytes()).hexdigest()))
    return frozenset(entries)


def classify(
    source: Path, dest_root: Path
) -> tuple[str, Path, Path, list[Path], list[str]]:
    """Return (classification, platform_root, resolved_path, alias_paths, notes)."""
    resolved_root = dest_root.expanduser().resolve()
    dest = resolved_root / source.name
    notes: list[str] = []
    resolved_source = source.resolve()
    if dest == resolved_source:
        return "SKIP", dest_root, dest, [], notes
    if not dest.is_dir():
        return "MISSING", dest_root, dest, [], notes
    if resolved_root == resolved_source.parent:
        return "SKIP", dest_root, dest, [], notes
    if digest_tree(dest) == digest_tree(source):
        return "CURRENT", dest_root, dest, [], notes
    stamp_order = version_orders_below(
        parse_version_stamp(dest), parse_version_stamp(source)
    )
    if stamp_order is True:
        return "OLDER", dest_root, dest, [], notes
    if stamp_order is False:
        return "NEWER", dest_root, dest, [], notes
    if parse_version_stamp(dest) == parse_version_stamp(source) and parse_version_stamp(
        source
    ) is not None:
        notes.append("equal version stamps with differing content")
    else:
        notes.append("stampless drift: drift direction unknown")
    return "STALE", dest_root, dest, [], notes


def refresh_destination(
    source: Path, resolved_dest: Path, classification: str, downgrade: bool
) -> tuple[bool, str]:
    if classification in ("CURRENT", "SKIP"):
        return True, ""
    if classification not in ("MISSING", "OLDER") and not downgrade:
        return False, (
            f"refresh refused for {resolved_dest}: classification {classification} "
            "requires --downgrade consent (drift direction unknown or destination newer)"
        )
    try:
        if resolved_dest.exists():
            shutil.rmtree(resolved_dest)
        resolved_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, resolved_dest)
    except OSError as exc:
        return False, f"refresh failed for {resolved_dest}: {exc}"
    if digest_tree(resolved_dest) != digest_tree(source):
        return False, f"post-refresh verification failed for {resolved_dest}"
    return True, ""


def build_rows(source: Path, dest_roots: list[Path]) -> list[dict]:
    by_physical: dict[Path, dict] = {}
    order: list[Path] = []
    for root in dest_roots:
        resolved_root = root.expanduser().resolve()
        row = by_physical.get(resolved_root)
        if row is None:
            classification, _, resolved, _, notes = classify(source, root)
            row = {
                "platform_root": str(root),
                "resolved_path": str(resolved),
                "alias_paths": [str(root)],
                "classification": classification,
                "notes": notes,
            }
            by_physical[resolved_root] = row
            order.append(resolved_root)
        else:
            row["alias_paths"].append(str(root))
    return [by_physical[key] for key in order]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check installed copies of a skill against the repository source."
    )
    parser.add_argument("--skill", required=True, help="Skill name under agents/skills/.")
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source skill directory (default: <repo-root>/agents/skills/<skill>).",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        action="append",
        default=[],
        help="Platform skills root (repeatable; default: ~/.agents/skills ~/.claude/skills ~/.cursor/skills).",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Overwrite MISSING and OLDER destinations with the source tree.",
    )
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="Consent to overwrite STALE and NEWER destinations during --refresh.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    args = parser.parse_args(argv)

    if args.skill is None or args.skill == "":
        return fail_usage("--skill is required")

    source = args.source
    if source is None:
        source = repo_root(Path.cwd()) / "agents" / "skills" / args.skill
    source = source.expanduser()
    if not source.is_dir():
        return fail_usage(f"source skill directory not found: {source}")

    dest_roots = args.dest or [Path(d) for d in DEFAULT_DEST_ROOTS]
    rows = build_rows(source, dest_roots)

    if args.refresh:
        refresh_errors: dict[str, list[str]] = {}
        for row in rows:
            if row["classification"] == "SKIP":
                continue
            ok, message = refresh_destination(
                source, Path(row["resolved_path"]), row["classification"], args.downgrade
            )
            if not ok:
                refresh_errors.setdefault(row["resolved_path"], []).append(message)
        rows = build_rows(source, dest_roots)
        for row in rows:
            if row["resolved_path"] in refresh_errors:
                row["errors"] = refresh_errors[row["resolved_path"]]

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            aliases = ", ".join(row["alias_paths"])
            line = (
                f"{row['classification']}: {row['resolved_path']} "
                f"(root: {row['platform_root']}"
                + (f"; aliases: {aliases}" if len(row["alias_paths"]) > 1 else "")
                + ")"
            )
            print(line)
            for note in row.get("notes", []):
                print(f"  note: {note}")
            if row["classification"] in ("STALE", "NEWER"):
                print("  note: --refresh requires --downgrade consent for this destination")
            for error in row.get("errors", []):
                print(f"  {error}")
            if row["classification"] == "MISSING":
                print(f"  refresh with --refresh installs the source skill here")

    bad = [row for row in rows if row["classification"] not in ("CURRENT", "SKIP")]
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
