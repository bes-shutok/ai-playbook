#!/usr/bin/env python3
"""Worktree closeout migration: capture a review-tree baseline and migrate new or modified artifacts to the main worktree.

Subcommands:
  capture  Write a JSON baseline (path plus SHA-256) of the configured
           review dirs, relative to the current working directory.
           Any path whose digest read raises OSError (a dangling symlink,
           a permission-denied file, ...) is skipped with a named
           warning and recorded under a "skipped" list instead of
           crashing the capture; the exit stays 0.
  migrate  Copy files that are new or modified versus the baseline from a
           source worktree into a target worktree, verifying every copy by
           re-read checksum. Never moves: on any verification failure the
           source file is still present and the exit code is non-zero.
           Dangling symlinks in the source are skipped with a warning and
           recorded as manifest skip entries. The manifest is written even
           when the run aborts mid-loop (an "interrupted": true marker
           flags the run, and an "incomplete" entry names the error), so
           already-copied files stay in the audit record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

DEFAULT_DIRS = "docs/reviews docs/tmp"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _configured_dirs(raw: str) -> list[str]:
    return [part for part in raw.split() if part]


def _is_dangling_symlink(path: Path) -> bool:
    """True for exactly the dangling-symlink shape: a symlink whose target is missing.

    Containment-scope guard (r1 F4): only this shape may be contained as a
    skip-and-warn. Every other OSError (unreadable regular file, permission
    denied, ...) propagates loudly and unchanged.
    """
    return path.is_symlink() and not path.exists()


def _iter_configured_files(root: Path, dirs: list[str]) -> list[Path]:
    found: list[Path] = []
    for rel_dir in dirs:
        base = root / rel_dir
        if not base.exists():
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for name in filenames:
                found.append(Path(dirpath) / name)
    return sorted(found, key=lambda item: item.as_posix())


def _same_content(left: Path, right: Path) -> bool:
    if left.is_symlink() or right.is_symlink():
        return (
            left.is_symlink()
            and right.is_symlink()
            and os.readlink(left) == os.readlink(right)
        )
    if not left.is_file():
        return False
    return _sha256(left) == _sha256(right)


def _copy_file(src: Path, dst: Path) -> None:
    """Copy seam: regular files via copy2, symlinks copied as links themselves."""
    if src.is_symlink():
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        os.symlink(os.readlink(src), dst)
        return
    shutil.copy2(src, dst)


def _verify_copy(src: Path, dst: Path) -> bool:
    """Verify seam: re-read the copy and compare against the source."""
    if src.is_symlink():
        return dst.is_symlink() and os.readlink(dst) == os.readlink(src)
    if dst.is_symlink() or not dst.is_file():
        return False
    return _sha256(dst) == _sha256(src)


def _append_manifest(manifest_path: Path, sections: dict[str, list[dict]]) -> None:
    manifest: dict = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key, entries in sections.items():
        if isinstance(entries, list):
            manifest.setdefault(key, []).extend(entries)
        else:
            manifest[key] = entries
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def cmd_capture(args: argparse.Namespace) -> int:
    dirs = _configured_dirs(args.dirs)
    root = Path.cwd()
    files: dict[str, str] = {}
    skipped: list[dict] = []
    for path in _iter_configured_files(root, dirs):
        rel = path.relative_to(root).as_posix()
        # Every OSError from the per-file digest read is contained the same
        # way: a dangling symlink (open raises FileNotFoundError), a
        # permission-denied regular file, any other unreadable shape. The
        # path is named on stderr, recorded under "skipped", and the
        # capture exit stays 0.
        try:
            files[rel] = _sha256(path)
        except OSError as exc:
            reason = f"{type(exc).__name__}: {exc}"
            print(
                f"WARN: capture: skipping unreadable path {rel}: {reason}",
                file=sys.stderr,
            )
            skipped.append({"path": rel, "reason": reason})
            continue
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"dirs": dirs, "files": files, "skipped": skipped},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Captured {len(files)} file(s) under {len(dirs)} dir(s) into {out}.")
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    if manifest_path.exists():
        try:
            json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            print(
                f"closeout manifest exists and is not JSON: {manifest_path}",
                file=sys.stderr,
            )
            return 2
    baseline_path = Path(args.baseline)
    if not baseline_path.is_file():
        print(
            f"ERROR: baseline file not found: {baseline_path}",
            file=sys.stderr,
        )
        print(
            "Refusing to continue with an implicit empty baseline; "
            "run capture first, otherwise pre-existing artifacts would be silently skipped.",
            file=sys.stderr,
        )
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    dirs = baseline.get("dirs") or _configured_dirs(DEFAULT_DIRS)
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    if source == target:
        print(
            "No-op: source and target are the same worktree; nothing copied (in-place closeout).",
            file=sys.stderr,
        )
        _append_manifest(
            manifest_path,
            {"noop": [{"note": "source equals target; in-place no-op, nothing copied"}]},
        )
        return 0

    baseline_files: dict[str, str] = baseline.get("files", {})
    migrated: list[dict] = []
    renamed: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    # Manifest durability: the four sections accumulate in memory and the
    # manifest is written in a finally block, so a mid-loop abort still
    # records every entry earned so far, plus an "interrupted": true marker
    # and an incomplete entry naming the error, before the failure
    # propagates unchanged.
    aborted: BaseException | None = None
    try:
        for src in _iter_configured_files(source, dirs):
            rel = src.relative_to(source).as_posix()
            if _is_dangling_symlink(src):
                print(f"WARN: skipping dangling symlink: {src}", file=sys.stderr)
                skipped.append(
                    {
                        "source": rel,
                        "reason": "dangling symlink; target missing; skipped without copying",
                    }
                )
                continue
            if rel in baseline_files and _sha256(src) == baseline_files[rel]:
                continue
            dst = target / rel
            if dst.exists() or dst.is_symlink():
                if _same_content(dst, src):
                    skipped.append(
                        {
                            "source": rel,
                            "destination": dst.as_posix(),
                            "reason": "target byte-identical; skipped without rename or rewrite",
                            "verified": True,
                        }
                    )
                    continue
                candidate = dst.with_name(dst.stem + f".wt-{args.suffix}" + dst.suffix)
                bump = 2
                while candidate.exists() or candidate.is_symlink():
                    candidate = dst.with_name(
                        dst.stem + f".wt-{args.suffix}-{bump}" + dst.suffix
                    )
                    bump += 1
                dst = candidate
            dst.parent.mkdir(parents=True, exist_ok=True)
            _copy_file(src, dst)
            if _verify_copy(src, dst):
                entry = {
                    "source": rel,
                    "destination": dst.as_posix(),
                    "verified": True,
                }
                if dst.name != Path(rel).name:
                    entry["collision_renamed"] = True
                    renamed.append(entry)
                else:
                    migrated.append(entry)
            else:
                failed.append(
                    {
                        "source": rel,
                        "destination": dst.as_posix(),
                        "verified": False,
                        "error": "checksum mismatch after copy",
                    }
                )
    except BaseException as exc:
        aborted = exc
        raise
    finally:
        sections: dict[str, list[dict]] = {
            "migrated": migrated,
            "renamed": renamed,
            "skipped": skipped,
            "failed": failed,
        }
        if aborted is not None:
            sections["interrupted"] = True
            sections["incomplete"] = [
                {
                    "error": f"{type(aborted).__name__}: {aborted}",
                    "note": "migration aborted mid-loop; entries recorded above are durable",
                }
            ]
        _append_manifest(manifest_path, sections)
    for entry in failed:
        print(
            f"ERROR: verification failed for {entry['source']} -> {entry['destination']}: {entry['error']}",
            file=sys.stderr,
        )
    if failed:
        print(
            f"ERROR: {len(failed)} file(s) failed copy verification; "
            "source files were copied, never moved, and remain in place.",
            file=sys.stderr,
        )
        return 1
    print(
        f"Migrated {len(migrated)} file(s), renamed {len(renamed)} on collision, "
        f"skipped {len(skipped)} identical; manifest at {manifest_path}."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture a review-tree baseline and migrate closeout artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser(
        "capture", help="Write a path-plus-SHA-256 baseline of the configured dirs."
    )
    capture.add_argument("--out", required=True, help="Baseline JSON output path.")
    capture.add_argument(
        "--dirs",
        default=DEFAULT_DIRS,
        help="Space-separated dirs to capture, relative to the working directory.",
    )
    capture.set_defaults(func=cmd_capture)

    migrate = subparsers.add_parser(
        "migrate", help="Copy new and modified files into the target worktree."
    )
    migrate.add_argument("--baseline", required=True, help="Baseline JSON from capture.")
    migrate.add_argument("--source", required=True, help="Source worktree root.")
    migrate.add_argument("--target", required=True, help="Target worktree root.")
    migrate.add_argument("--manifest", required=True, help="Manifest JSON to append to.")
    migrate.add_argument(
        "--suffix", default="1", help="Suffix for collision-renamed copies (<stem>.wt-<suffix><ext>)."
    )
    migrate.set_defaults(func=cmd_migrate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
