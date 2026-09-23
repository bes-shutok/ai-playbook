#!/usr/bin/env python3
"""Dirt regression gate: fail on restored dirt that reverts content HEAD gained.

Classification is per hunk of each restored file's diff against HEAD, with the
run's merge base (``--base <merge-base-sha>``) bound:

- A hunk marks a dirt REGRESSION when it removes at least one line HEAD gained
  since the base (a line present in the HEAD version of the file and absent
  from the merge-base version) AND every line it adds exists verbatim in the
  merge-base version of the file. Such a hunk restores base-era text over
  HEAD-gained content.
- Hunks whose added lines are not all base text are forward-looking rewrites
  and pass. So a modification of a HEAD-gained line (the removed line replaced
  by new text not present at the base) passes, pure additions pass, and
  removals of lines already present at the base pass. A removal-only hunk of
  HEAD-gained lines is a regression (the added-line condition holds vacuously).

Exit codes: 0 when no restored path regresses; 1 when at least one path
regresses (one ``dirt REGRESSION`` line per regressed file on stdout); 2 on
usage or git-environment errors (unresolvable ``--base``, missing HEAD, path
outside the repository).

With ``--stamp``, the gate cites an adjacent ``.source-commit`` stamp file
(written beside the deployed copy by ``deploy_runtime_scripts.sh``) as
provenance: when the stamp is present its recorded commit is cited on stdout;
when absent a report-only note goes to stderr and never changes the verdict.
Stamping is manual-only for now; the helper is the sanctioned manual path.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath

STAMP_FILENAME = ".source-commit"


def _git(*args: str, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def _git_ok(*args: str, cwd: Path) -> bool:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    return proc.returncode == 0


def _content_lines(text: str) -> list[str]:
    """Split blob text into verbatim lines, dropping the trailing-newline artifact."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _blob_lines(rev: str, repo_rel: str, cwd: Path) -> list[str]:
    """Lines of a file at a revision; empty list when the file does not exist there."""
    if not _git_ok("cat-file", "-e", f"{rev}:{repo_rel}", cwd=cwd):
        return []
    return _content_lines(_git("show", f"{rev}:{repo_rel}", cwd=cwd))


def _hunks(diff_text: str) -> list[tuple[list[str], list[str]]]:
    """Parse a unified diff into (removed, added) line pairs, one per hunk."""
    hunks: list[tuple[list[str], list[str]]] = []
    removed: list[str] = []
    added: list[str] = []
    in_hunk = False
    for line in diff_text.split("\n"):
        if line.startswith("@@"):
            if in_hunk:
                hunks.append((removed, added))
            removed, added = [], []
            in_hunk = True
            continue
        if in_hunk:
            if line.startswith("\\"):
                # "\ No newline at end of file" marker, not content.
                continue
            if line.startswith("-"):
                removed.append(line[1:])
            elif line.startswith("+"):
                added.append(line[1:])
    if in_hunk:
        hunks.append((removed, added))
    return hunks


def _hunk_is_regression(
    removed: list[str], added: list[str], gained: set[str], base_set: set[str]
) -> bool:
    if not any(line in gained for line in removed):
        return False
    return all(line in base_set for line in added)


def classify_path(path: str, base: str, cwd: Path) -> tuple[bool, str]:
    """Classify one restored path. Returns (is_regression, detail)."""
    repo_root = Path(_git("rev-parse", "--show-toplevel", cwd=cwd).strip())
    resolved = Path(path).resolve()
    try:
        repo_rel = resolved.relative_to(repo_root)
    except ValueError:
        raise RuntimeError(f"path not inside repository {repo_root}: {path}")
    repo_rel_posix = PurePosixPath(repo_rel).as_posix()
    if not resolved.is_file():
        tracked = _git("ls-files", "--", path, cwd=cwd).strip()
        # A staged whole-file deletion (post-deletion `git add` sweep or
        # `git rm`) removes the path from the index while HEAD still tracks
        # it: an ordinary dirt shape the recipes' file enumeration picks up.
        # Classify it through `git diff HEAD` below like any other deletion
        # instead of misreporting it as a git-environment error; only a path
        # HEAD never tracked fails closed here.
        head_tracks = _git_ok("cat-file", "-e", f"HEAD:{repo_rel_posix}", cwd=cwd)
        if not tracked and not head_tracks:
            raise RuntimeError(f"path does not exist or is not a tracked file: {path}")
        # absent from the worktree: a whole-file deletion in the dirt; git
        # diff HEAD classifies it (removal-only hunk of HEAD-gained lines is
        # a regression, the added-line condition holds vacuously)

    base_set = set(_blob_lines(base, repo_rel_posix, cwd))
    head_lines = _blob_lines("HEAD", repo_rel_posix, cwd)
    gained = set(head_lines) - base_set
    diff_text = _git("diff", "HEAD", "--unified=0", "--", path, cwd=cwd)
    for removed, added in _hunks(diff_text):
        if _hunk_is_regression(removed, added, gained, base_set):
            return True, "restores base-era text over lines HEAD gained"
    return False, ""


def _stamp_path_for(path: str) -> Path:
    return Path(path).resolve().parent / STAMP_FILENAME


def _report_stamp(path: str, stdout, stderr) -> None:
    stamp = _stamp_path_for(path)
    if stamp.is_file():
        try:
            sha = stamp.read_text(encoding="utf-8").strip()
        except (UnicodeDecodeError, OSError):
            print(
                f"stamp: unreadable {STAMP_FILENAME} beside {stamp.parent} "
                "(report-only; treated as unstamped)",
                file=stderr,
            )
            return
        print(
            f"stamp provenance: {path} deployed from commit {sha} "
            f"({STAMP_FILENAME} at {stamp.parent})",
            file=stdout,
        )
    else:
        print(
            f"stamp: no {STAMP_FILENAME} beside {stamp.parent} "
            "(report-only; unstamped provenance)",
            file=stderr,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail on restored dirt hunks that restore merge-base-era text over "
            "content HEAD gained since the given merge base."
        )
    )
    parser.add_argument(
        "--base",
        required=True,
        help="merge-base sha the run's dirt was restored against",
    )
    parser.add_argument(
        "--stamp",
        action="store_true",
        help=(
            "cite an adjacent .source-commit stamp as provenance when present; "
            "report-only when absent"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="restored file paths to classify",
    )
    args = parser.parse_args(argv)

    cwd = Path.cwd()
    try:
        _git("rev-parse", "--verify", "--quiet", f"{args.base}^{{commit}}", cwd=cwd)
    except RuntimeError:
        print(
            f"dirt gate: --base does not resolve to a commit: {args.base}",
            file=sys.stderr,
        )
        return 2
    try:
        _git("rev-parse", "--verify", "--quiet", "HEAD^{commit}", cwd=cwd)
    except RuntimeError:
        print("dirt gate: repository has no HEAD commit", file=sys.stderr)
        return 2

    regressed: list[str] = []
    for path in args.paths:
        try:
            is_regression, detail = classify_path(path, args.base, cwd)
        except RuntimeError as exc:
            print(f"dirt gate: {exc}", file=sys.stderr)
            return 2
        if args.stamp:
            _report_stamp(path, sys.stdout, sys.stderr)
        if is_regression:
            regressed.append(path)
            print(f"dirt REGRESSION: {path} ({detail} since {args.base[:12]})")

    if regressed:
        return 1
    print(f"dirt gate: PASS ({len(args.paths)} file(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
