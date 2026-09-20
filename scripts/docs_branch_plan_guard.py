#!/usr/bin/env python3
"""Certified-plan digest guard for the docs-branch sync.

Two subcommands with two distinct postures (never swapped):

- ``guard`` (fail-closed): before the sync's shadow overlay, compare each
  top-level plan file present in BOTH the incoming snapshot root and the
  branch worktree root against the plan's latest certified review sidecar
  digest. When the write would replace branch bytes that match the
  certification digest with bytes that do not (a certified downgrade),
  collect every such row, print them, and exit 1 so the sync aborts before
  staging. Upgrades and neither-side matches print info/warn lines and
  exit 0.
- ``check-restored`` (warn-and-continue): after the sync's restore-fill
  leg, witness each restored plan file; a file whose bytes do not match the
  certification digest prints a warn line and the command always exits 0.

The certification digest is the ``source_digest`` of the latest sidecar
under the reviews dir whose ``source_kind`` is ``plan`` and whose
``artifact_slug`` equals the plan's feature slug (the basename sans
``.md`` with the leading ``YYYY-MM-DD-`` prefix stripped, mirroring
``feature_slug()`` in ``scripts/plan_readiness.py``). Digest match is
prefix-tolerant in one direction: the byte digest equals the sidecar
digest or starts with it (sidecars in the wild may store a 16-hex prefix).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROUND_RE = re.compile(r"^[rR](\d+)$")
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def feature_slug(plan_name: str) -> str:
    """Plan filename stem minus its leading ``YYYY-MM-DD-`` prefix."""
    stem = Path(plan_name).stem
    return DATE_PREFIX_RE.sub("", stem, count=1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_matches(byte_digest: str, sidecar_digest: str) -> bool:
    """Prefix-tolerant match, one direction only.

    The byte digest must equal the sidecar digest or start with it; the
    reverse direction (a sidecar digest that merely starts with the byte
    digest) never matches, because the prefix test is one-directional.
    """
    if not sidecar_digest:
        return False
    return byte_digest == sidecar_digest or byte_digest.startswith(sidecar_digest)


def round_sort_key(sidecar: dict) -> tuple[int, str]:
    """Latest-round sort key: numeric round (non-numeric oldest), then date.

    Normalizes ``"r9"``, ``"R9"`` and ``9`` to the same integer space so
    string and integer round forms compare correctly and never raise.
    """
    raw = sidecar.get("round")
    number = -1
    if isinstance(raw, int) and not isinstance(raw, bool):
        number = raw
    elif isinstance(raw, str):
        stripped = raw.strip()
        match = ROUND_RE.match(stripped)
        if match:
            number = int(match.group(1))
        else:
            try:
                number = int(stripped)
            except ValueError:
                number = -1
    return (number, str(sidecar.get("date") or ""))


def load_sidecars(reviews_dir: Path) -> list[tuple[Path, dict]]:
    """Parse every ``.stats.json`` under the reviews dir; skip unreadable."""
    sidecars: list[tuple[Path, dict]] = []
    if not reviews_dir.is_dir():
        return sidecars
    for path in sorted(reviews_dir.rglob("*.stats.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            sidecars.append((path, data))
    return sidecars


def latest_certified_sidecar(
    sidecars: list[tuple[Path, dict]], slug: str
) -> tuple[Path, dict] | None:
    """Latest ``source_kind: "plan"`` sidecar for the slug, by round then date."""
    candidates = [
        (path, data)
        for path, data in sidecars
        if data.get("source_kind") == "plan" and data.get("artifact_slug") == slug
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda entry: round_sort_key(entry[1]))


def top_level_plan_names(plans_dir: Path) -> set[str]:
    """Top-level ``.md`` filenames only; subdirectories (completed/) excluded."""
    if not plans_dir.is_dir():
        return set()
    return {
        entry.name
        for entry in plans_dir.iterdir()
        if entry.is_file() and entry.suffix == ".md"
    }


def cmd_guard(args: argparse.Namespace) -> int:
    incoming_root = Path(args.incoming_root)
    branch_root = Path(args.branch_root)
    plans_rel = Path(args.plans_dir)
    incoming_plans_dir = incoming_root / plans_rel
    branch_plans_dir = branch_root / plans_rel

    shared = sorted(
        top_level_plan_names(incoming_plans_dir) & top_level_plan_names(branch_plans_dir)
    )
    if not shared:
        return 0

    sidecars = load_sidecars(Path(args.reviews_dir))
    refusals = 0
    for name in shared:
        branch_plan = branch_plans_dir / name
        incoming_plan = incoming_plans_dir / name
        branch_digest = sha256_file(branch_plan)
        incoming_digest = sha256_file(incoming_plan)
        if branch_digest == incoming_digest:
            continue
        certified = latest_certified_sidecar(sidecars, feature_slug(name))
        if certified is None:
            continue
        sidecar_path, sidecar_data = certified
        cert_digest = str(sidecar_data.get("source_digest") or "")
        branch_ok = digest_matches(branch_digest, cert_digest)
        incoming_ok = digest_matches(incoming_digest, cert_digest)
        if branch_ok and not incoming_ok:
            refusals += 1
            print(f"REFUSE: certified downgrade for {branch_plan}")
            print(f"  incoming {incoming_plan} does not match the certified digest {cert_digest}")
            print(f"  sidecar: {sidecar_path.name}")
        elif incoming_ok and not branch_ok:
            print(
                f"UPGRADE: {branch_plan} incoming bytes match the certified digest "
                f"{cert_digest} (sidecar {sidecar_path.name}); overlay proceeds"
            )
        elif not branch_ok and not incoming_ok:
            print(
                f"WARN: neither branch nor incoming bytes of {branch_plan} match the "
                f"certified digest {cert_digest} (sidecar {sidecar_path.name}); sync proceeds"
            )
    if refusals:
        print(
            f"certified-plan guard: {refusals} certified downgrade(s) refused; "
            f"sync aborted before staging"
        )
        return 1
    return 0


def cmd_check_restored(args: argparse.Namespace) -> int:
    sidecars = load_sidecars(Path(args.reviews_dir))
    for file_arg in args.files:
        path = Path(file_arg)
        if not path.is_file():
            print(f"WARN: check-restored: restored plan file missing: {path}", file=sys.stderr)
            continue
        certified = latest_certified_sidecar(sidecars, feature_slug(path.name))
        if certified is None:
            continue
        sidecar_path, sidecar_data = certified
        cert_digest = str(sidecar_data.get("source_digest") or "")
        if not digest_matches(sha256_file(path), cert_digest):
            print(
                f"WARN: restored plan {path} does not match the certified digest "
                f"{cert_digest} (sidecar {sidecar_path.name})"
            )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Certified-plan digest guard for the docs-branch sync."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    guard_parser = sub.add_parser(
        "guard", help="fail-closed certified-downgrade check before the shadow overlay"
    )
    guard_parser.add_argument("--incoming-root", required=True)
    guard_parser.add_argument("--branch-root", required=True)
    guard_parser.add_argument("--plans-dir", required=True)
    guard_parser.add_argument("--reviews-dir", required=True)
    guard_parser.set_defaults(func=cmd_guard)

    restored_parser = sub.add_parser(
        "check-restored", help="warn-only witness for restored plan files"
    )
    restored_parser.add_argument("--reviews-dir", required=True)
    restored_parser.add_argument("--plans-dir", required=True)
    restored_parser.add_argument("files", nargs="+")
    restored_parser.set_defaults(func=cmd_check_restored)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
