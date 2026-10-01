#!/usr/bin/env python3
"""Certified-plan digest guard for the docs-branch sync.

Two subcommands with two distinct postures (never swapped):

- ``guard`` (fail-closed): before the sync's shadow overlay, compare each
  top-level plan file present in BOTH the incoming snapshot root and the
  branch worktree root against the plan's latest certified review sidecar
  digest. When the write would replace branch bytes that match the
  certification digest with bytes that do not (a certified downgrade),
  collect every such row, print them, and exit 1 so the sync aborts before
  staging. One acceptance arm narrows the refusal: when the branch bytes
  match the certified digest and the incoming plan differs ONLY in
  unchecked-to-checked checkbox marker flips (every differing line pair an
  unchecked branch line paired with a checked incoming line on two
  otherwise byte-identical lines of equal line count), the guard prints a
  named acceptance line and counts the plan as accepted; any other byte
  difference still refuses. Upgrades and neither-side matches print
  info/warn lines and exit 0.
- ``check-restored`` (warn-and-continue): after the sync's restore-fill
  leg, witness each restored plan file; a file whose bytes do not match the
  certification digest prints a warn line and the command always exits 0.
  A restored path under an archive subdirectory (``completed/``,
  ``deferred/``, ``rejected/``) is classified as archived and skipped
  with an info line: frozen history is never a certified-plan witness.

The two postures also diverge on an unreadable plan file (an OSError from
the per-file digest read): ``guard`` prints a named warn and exits
non-zero -- the certified-downgrade boundary stays closed on inputs it
cannot verify -- while ``check-restored`` prints the same named warn,
continues, and returns 0. Neither posture ever surfaces a traceback.

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

# Archive subdirectories of the plans dir. A plan under any of them is
# archived surface: the guard's shared-name intersection is top-level
# only, so archived copies are never compared, and the check-restored
# witness skips them (``rejected/`` is the explicit decision-against
# archive; see docs/history/plans/rejected/README.md).
ARCHIVED_PLAN_DIR_NAMES = ("completed", "deferred", "rejected")


def is_archived_plan(path: Path) -> bool:
    """True when the plan path sits under a named archive subdirectory."""
    return any(part in ARCHIVED_PLAN_DIR_NAMES for part in path.parts[:-1])


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


def warn_unreadable_plan(subcommand: str, path: Path, exc: OSError) -> None:
    """Named skip-and-warn for a plan file whose digest read raised OSError."""
    reason = f"{type(exc).__name__}: {exc}"
    print(
        f"WARN: {subcommand}: skipping unreadable plan pair for {path}: {reason}",
        file=sys.stderr,
    )


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
    """Top-level ``.md`` filenames only; the archive subdirectories
    (``completed/``, ``deferred/``, ``rejected/``) and every other
    subdirectory are excluded, so archived plans are never compared."""
    if not plans_dir.is_dir():
        return set()
    return {
        entry.name
        for entry in plans_dir.iterdir()
        if entry.is_file() and entry.suffix == ".md"
    }


# Local pairing predicate for the progress-only overlay arm. The unchecked-
# marker half mirrors ``execute_plan_runtime._unchecked_checkbox_pairs`` as
# the shape of record (line-anchored GFM task-list markers, ``-``/``*``/``+``
# bullets); no import edge into ``execute_plan_runtime`` is added (the
# runtime module is very large and its helper recognizes unchecked markers
# only, while the pairing rule needs checked markers too).
_CHECKBOX_LINE_RE = re.compile(r"^(\s*[-*+] )(\[[ xX]])(.*)$")


def _split_checkbox_line(line: str) -> tuple[str, str, str] | None:
    """``(before-marker, marker token, after-marker)`` for a checkbox line.

    A line counts only when its first non-whitespace token is a GFM
    task-list marker, one of ``- [ ]``, ``- [x]``, ``- [X]`` with any of the
    ``-``, ``*``, ``+`` bullets. The split keeps the bullet, the spacing,
    and the post-marker text in the byte-exact prefix and suffix, so
    normalization in the pairing predicate can touch only the bracketed
    token. None for every non-checkbox line.
    """

    match = _CHECKBOX_LINE_RE.match(line)
    if match is None:
        return None
    return match.group(1), match.group(2), match.group(3)


def progress_only_overlay_flips(branch_text: str, incoming_text: str) -> int | None:
    """Flip count when the incoming text is a progress-only overlay.

    The two plans are compared line by line; the line counts must be equal;
    each line pair must be byte-identical except that the bracketed marker
    token may differ, and a differing pair is accepted only when the branch
    side carries the unchecked marker ``[ ]`` and the incoming side a checked
    marker ``[x]`` or ``[X]``. Any other byte difference (text, structure, a
    checked-to-unchecked regression, bullet or spacing changes) returns
    None, which keeps the certified-downgrade refusal.
    """

    branch_lines = branch_text.splitlines()
    incoming_lines = incoming_text.splitlines()
    if len(branch_lines) != len(incoming_lines):
        return None
    flips = 0
    for branch_line, incoming_line in zip(branch_lines, incoming_lines):
        if branch_line == incoming_line:
            continue
        branch_parts = _split_checkbox_line(branch_line)
        incoming_parts = _split_checkbox_line(incoming_line)
        if branch_parts is None or incoming_parts is None:
            return None
        if branch_parts[0] != incoming_parts[0] or branch_parts[2] != incoming_parts[2]:
            return None
        if branch_parts[1] != "[ ]":
            return None
        if incoming_parts[1] not in ("[x]", "[X]"):
            return None
        flips += 1
    return flips


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
    unreadable = 0
    for name in shared:
        branch_plan = branch_plans_dir / name
        incoming_plan = incoming_plans_dir / name
        try:
            branch_digest = sha256_file(branch_plan)
        except OSError as exc:
            warn_unreadable_plan("guard", branch_plan, exc)
            unreadable += 1
            continue
        try:
            incoming_digest = sha256_file(incoming_plan)
        except OSError as exc:
            warn_unreadable_plan("guard", incoming_plan, exc)
            unreadable += 1
            continue
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
            # Progress-only overlay arm: the branch bytes match the certified
            # digest and the incoming bytes differ only in unchecked-to-checked
            # marker flips (pairing rule per the plan's Terms). The overlay is
            # accepted with a named line instead of refused; any other byte
            # difference keeps the refusal. A plan text that cannot be decoded
            # or read fails closed into the refusal.
            try:
                overlay_flips = progress_only_overlay_flips(
                    branch_plan.read_text(encoding="utf-8"),
                    incoming_plan.read_text(encoding="utf-8"),
                )
            except (OSError, ValueError):
                overlay_flips = None
            if overlay_flips is not None:
                print(
                    f"progress-only overlay accepted for {incoming_plan} "
                    f"({overlay_flips} unchecked-to-checked flip(s); "
                    f"branch matches certified digest {cert_digest})"
                )
            else:
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
    if refusals or unreadable:
        if refusals:
            print(
                f"certified-plan guard: {refusals} certified downgrade(s) refused; "
                f"sync aborted before staging"
            )
        if unreadable:
            print(
                f"certified-plan guard: {unreadable} unreadable plan file(s); "
                f"the certified-downgrade boundary stays closed on inputs it cannot verify"
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
        if is_archived_plan(path):
            # An archived copy (completed/, deferred/, rejected/) is frozen
            # history, not an active certified plan: classify it and skip
            # the certified-digest witness instead of warning.
            print(f"INFO: archived plan copy, certified-digest witness skipped: {path}")
            continue
        certified = latest_certified_sidecar(sidecars, feature_slug(path.name))
        if certified is None:
            continue
        sidecar_path, sidecar_data = certified
        cert_digest = str(sidecar_data.get("source_digest") or "")
        try:
            file_digest = sha256_file(path)
        except OSError as exc:
            warn_unreadable_plan("check-restored", path, exc)
            continue
        if not digest_matches(file_digest, cert_digest):
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
    restored_parser.add_argument("files", nargs="+")
    restored_parser.set_defaults(func=cmd_check_restored)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
