#!/usr/bin/env python3
"""Dirt regression gate: fail on restored dirt that reverts content HEAD gained.

Classification is per hunk of each restored file's diff against HEAD, with the
run's merge base (``--base <merge-base-sha>``) bound. Import declarations and
exact lines moved between diff hunks are excluded from the removed-line signal
because they do not by themselves show a behavior reversion:

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

Outcome contract (scripts/OUTCOME_CONTRACT.md): the gate reports exactly one
of four outcomes as the final ``OUTCOME:`` line on stdout and its exit code.
Exit codes: 0 pass (no restored path regresses); 1 fail (at least one path
regresses; one ``dirt REGRESSION`` line per regressed file on stdout);
2 indeterminate (an observed diff shape the classifier does not model; the
observed and could-not-determine lines precede the OUTCOME line); 3 tool
error (usage or git-environment errors: unresolvable ``--base``, missing
HEAD, a path outside the repository, an absent path HEAD never tracked, any
git failure, or an argparse usage error). Operating-context assumptions this gate's result
depends on, declared per the contract: the invocation runs inside the
repository (checkout context); ``--base`` resolves to a commit and HEAD
exists (branch state); the listed paths exist in the worktree, are HEAD-
tracked, or are staged deletions (input presence); ``git diff`` output is
well-formed and blob content decodable as the pinned utf-8 strict codec.
An unheld assumption surfaces as tool error (exit 3), never as a domain
pass or fail; a diff shape outside the modeled cases surfaces as
indeterminate (exit 2), never as pass. Operating-context assumptions are
declared in scripts/OUTCOME_CONTRACT.md (the authoritative surface).

With ``--stamp``, the gate cites an adjacent ``.source-commit`` stamp file
(written beside the deployed copy at deployment time) as
provenance: when the stamp is present its recorded commit is cited on stdout;
when absent a report-only note goes to stderr and never changes the verdict.
Stamping is manual-only for now; the helper is the sanctioned manual path.
"""

from __future__ import annotations

import argparse
from collections import Counter
import subprocess
import sys
from pathlib import Path, PurePosixPath

STAMP_FILENAME = ".source-commit"


def _git(*args: str, cwd: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except UnicodeDecodeError:
        # Unsupported data per the outcome contract: output git produced but
        # the gate cannot decode (a non-UTF-8 tracked blob or diff text) is
        # tool error, never a domain pass or fail.
        raise RuntimeError(
            f"git {' '.join(args)} failed: unsupported data: output not "
            "decodable as utf-8 text"
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def _git_ok(*args: str, cwd: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except UnicodeDecodeError:
        # The gate's other decode boundary; both are guarded so a decode
        # failure is tool error everywhere.
        raise RuntimeError(
            f"git {' '.join(args)} failed: unsupported data: output not "
            "decodable as utf-8 text"
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


def _is_import_declaration(line: str) -> bool:
    """Imports are compile-time names, not evidence that behavior was reverted."""
    stripped = line.strip()
    if not stripped:
        return False
    return (
        stripped.startswith("import ")
        or stripped.startswith("from ") and " import " in stripped
        or stripped.startswith("using ")
        and stripped.endswith(";")
        and not stripped.startswith(("using (", "using var "))
        or stripped.startswith("global using ") and stripped.endswith(";")
        or stripped.startswith("use ") and stripped.endswith(";")
        or stripped.startswith("#include ")
    )


def _hunk_is_regression(
    removed: list[str], added: list[str], gained: set[str], base_set: set[str]
) -> bool:
    behavior_removed = [
        line for line in removed if not _is_import_declaration(line)
    ]
    if not any(line in gained for line in behavior_removed):
        return False
    return all(line in base_set for line in added)


def classify_path(path: str, base: str, cwd: Path) -> tuple[str, str]:
    """Classify one restored path. Returns (status, detail).

    status is "regression", "clean", or "indeterminate" per the outcome
    contract (scripts/OUTCOME_CONTRACT.md); "indeterminate" marks a diff
    shape the classifier does not model, never a pass or a fail.
    """
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
    hunks = _hunks(diff_text)
    if diff_text.strip() and not hunks:
        # Unmodeled diff shape: content the classifier cannot see (a binary
        # restored file is the witnessed class, and a binary payload riding a
        # mode flip or a rename header is the same class). Modeled hunk-less
        # shapes are PURE rename ("similarity index"/"rename from"/"rename
        # to") or PURE mode change ("old mode"/"new mode") with no binary
        # payload line. Uncertainty is indeterminate, never a silent pass.
        modeled = (
            "Binary files" not in diff_text
            and "GIT binary patch" not in diff_text
            and (
                "similarity index" in diff_text
                or "old mode" in diff_text
                or "new mode" in diff_text
            )
        )
        if not modeled:
            return (
                "indeterminate",
                "diff carries no classifiable hunks (binary or unrecognized "
                "shape); observed "
                f"{len(diff_text.splitlines())} diff lines, could not "
                "determine restored-content polarity",
            )
    removed_counts = Counter(line for removed, _ in hunks for line in removed)
    added_counts = Counter(line for _, added in hunks for line in added)
    moved_counts = removed_counts & added_counts
    for removed, added in hunks:
        unmatched_removed: list[str] = []
        for line in removed:
            if moved_counts[line]:
                moved_counts[line] -= 1
            else:
                unmatched_removed.append(line)
        if _hunk_is_regression(unmatched_removed, added, gained, base_set):
            return "regression", "restores base-era text over lines HEAD gained"
    return "clean", ""


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
    class _GateParser(argparse.ArgumentParser):
        # Usage errors are tool error (exit 3) per the outcome contract;
        # argparse's documented extension point is the error() override.
        def error(self, message: str) -> None:
            print(f"dirt gate: {message}", file=sys.stderr)
            print("OUTCOME: tool_error")
            raise SystemExit(3)

    parser = _GateParser(
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
        print("OUTCOME: tool_error")
        return 3
    try:
        _git("rev-parse", "--verify", "--quiet", "HEAD^{commit}", cwd=cwd)
    except RuntimeError:
        print("dirt gate: repository has no HEAD commit", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3

    regressed: list[str] = []
    indeterminate: list[str] = []
    for path in args.paths:
        try:
            status, detail = classify_path(path, args.base, cwd)
        except RuntimeError as exc:
            print(f"dirt gate: {exc}", file=sys.stderr)
            print("OUTCOME: tool_error")
            return 3
        if args.stamp:
            _report_stamp(path, sys.stdout, sys.stderr)
        if status == "regression":
            regressed.append(path)
            print(f"dirt REGRESSION: {path} ({detail} since {args.base[:12]})")
        elif status == "indeterminate":
            indeterminate.append(path)
            print(f"dirt INDETERMINATE: {path} ({detail})")

    if indeterminate:
        # Uncertainty dominates a mixed run (the contract's precedence rule):
        # every regressed path is still named in the evidence lines above, and
        # the caller stops and re-derives instead of acting on the subset.
        print("OUTCOME: indeterminate")
        return 2
    if regressed:
        print("OUTCOME: fail")
        return 1
    print(f"dirt gate: PASS ({len(args.paths)} file(s) checked)")
    print("OUTCOME: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
