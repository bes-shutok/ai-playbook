#!/usr/bin/env python3
"""Cleanup scope baseline checker.

Classifies a repository's dirty and deleted paths against a cleanup scope
ledger (base ref + allow-list) so a cleanup or restoration commit cannot
silently sweep unaccounted work.

Classification:
- dirty paths: every path in ``git status --porcelain -z
  --untracked-files=all`` (staged, unstaged, and untracked alike), minus
  paths classified as deletions below;
- deletions: ``git diff --name-only -z --diff-filter=D <base>`` (paths
  deleted relative to the base ref).

Both git invocations pass ``-c diff.renames=false`` so rename detection is
disabled: a staged rename (``git mv old new``) cannot hide its source
deletion (the source path is classified as a deletion and must be
allow-listed), and classification is independent of the user's
``diff.renames`` config.

Both listings are parsed as NUL-delimited records (``-z``), which lists
untracked files individually (no directory collapse) and emits paths
verbatim (no C-quoting), so an allow-list entry written as a real file path
always matches.

Every path outside the allow-list fails with exactly one of the two error
classes on stderr (sorted, one per path):
- ``cleanup-scope: unaccounted dirty path <path>``
- ``cleanup-scope: unauthorized deletion <path>``

A deleted path that IS allow-listed passes: that is what a cleanup ledger
authorizes. Allow-list entries are matched byte-exact, repo-root-relative:
no ``./`` normalization and no directory-prefix semantics; list each file
path verbatim.

Known limitation: gitignored files are invisible to both listings, so
cleanup or deletion of gitignored content is not covered by this checker.
Known limitation: paths that are not valid UTF-8 are decoded with
replacement characters, so the decoded string cannot match an allow-list
entry; such a path fails closed with exit 1 (never silently passes).

Run before the first commit of the session, or with the session-start
base ref from the ledger; ``--base HEAD`` after commits exist cannot see
committed modifications (committed non-deletion sweeps are invisible to
it).

Stdlib only; no network.

Outcome contract (scripts/OUTCOME_CONTRACT.md): every non-metadata run ends
with exactly one final ``OUTCOME:`` line on stdout (``--help`` and the
``--selftest`` diagnostic run are metadata modes and emit none). Exit codes
follow the four-outcome vocabulary: 0 when every dirty/deleted path is
accounted for (``OUTCOME: pass``); 1 for the two baseline violation classes
above, whose lines stay on stderr (``OUTCOME: fail``); 2 indeterminate, a
git plumbing failure over already-resolved inputs, reported with the
observed/could-not-determine evidence on stderr (``OUTCOME: indeterminate``);
3 tool error: usage (argparse overridden), an unresolvable base ref, or a
non-repo root (``OUTCOME: tool_error``; the legacy ``cleanup-scope:
internal error`` prefix is retired into these split arms). ``--selftest``
builds twelve fixture repos in a temp dir and asserts every arm's positive
and negative checker outcomes across twelve fixture repos, including
negative arms that pin byte-exact allow-list matching (each fixture repo
sets a local git identity so identity-less machines stay green).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ERR_DIRTY = "cleanup-scope: unaccounted dirty path"
ERR_DELETION = "cleanup-scope: unauthorized deletion"
OUTCOME_LABELS = ("pass", "fail", "indeterminate", "tool_error")


class OutcomeArgumentParser(argparse.ArgumentParser):
    """argparse override per the outcome contract's usage rule: a usage
    violation is a tool error, so ``error()`` prints the usage message plus
    a final ``OUTCOME: tool_error`` row on stderr and exits 3; ``--help``
    stays a metadata exit (usage text only, no OUTCOME row)."""

    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        print("OUTCOME: tool_error", file=sys.stderr)
        raise SystemExit(3)


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        first_line = stderr.splitlines()[0] if stderr else "no stderr"
        raise RuntimeError(
            f"git {' '.join(args)} failed in {repo_root}: {first_line}"
        )
    return proc.stdout


def classify(repo_root: Path, base: str) -> tuple[list[str], list[str]]:
    """Return (dirty_paths, deleted_paths), each sorted and deduplicated.

    Both listings use NUL-delimited parsing: ``-z`` emits paths verbatim
    (no C-quoting to undo) and ``--untracked-files=all`` lists each untracked
    file individually instead of collapsing a wholly-untracked directory to
    ``dir/``.
    """
    deleted: set[str] = set(
        path
        for path in _git(
            repo_root,
            "-c",
            "diff.renames=false",
            "diff",
            "--name-only",
            "-z",
            "--diff-filter=D",
            base,
        ).split("\0")
        if path
    )
    dirty: set[str] = set()
    records = _git(
        repo_root,
        "-c",
        "diff.renames=false",
        "status",
        "--porcelain",
        "-z",
        "--untracked-files=all",
    ).split("\0")
    records_iter = iter(records)
    for record in records_iter:
        if len(record) < 4:
            continue
        status, path = record[:2], record[3:]
        if "R" in status[:2] or "C" in status[:2]:
            # Defensive only: this branch is unreachable in practice because
            # both git invocations above pass ``-c diff.renames=false`` and
            # ``status.renames`` follows ``diff.renames``, so renames/copies
            # are never collapsed into R/C records here (no selftest arm can
            # exercise it directly; selftest arm 9 guards this configuration
            # by asserting a staged rename surfaces as a plain deletion-plus-
            # dirty pair instead). Should an R/C record ever appear (either
            # status position), porcelain -z format emits the original path
            # as a second NUL record; the destination path is already in this
            # record, so skip the next one.
            next(records_iter, None)
        if path and path not in deleted:
            dirty.add(path)
    return sorted(dirty), sorted(deleted)


def check(repo_root: Path, base: str, allow: list[str]) -> list[str]:
    """Return the sorted list of error lines (empty when the baseline holds)."""
    allowed = set(allow)
    dirty, deleted = classify(repo_root, base)
    errors = [
        f"{ERR_DIRTY} {path}" for path in dirty if path not in allowed
    ] + [
        f"{ERR_DELETION} {path}" for path in deleted if path not in allowed
    ]
    return sorted(errors)


def _make_fixture_repo(root: Path, name: str) -> Path:
    repo = root / name
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Selftest Fixture")
    _git(repo, "config", "user.email", "selftest.fixture@invalid")
    (repo / "base.txt").write_text("base\n")
    (repo / "owned.txt").write_text("task-owned v1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture base")
    return repo


def _run_checker(repo: Path, base: str, allow: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--repo-root",
            str(repo),
            "--base",
            base,
            *sum([["--allow", a] for a in allow], []),
        ],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_selftest() -> int:
    failures: list[str] = []
    outcome_labels = ("pass", "fail", "indeterminate", "tool_error")

    def final_outcome(out: str) -> str:
        """The single final ``OUTCOME:`` label on a checker run's stdout, or
        the empty string when the shape is wrong (missing, duplicated, not
        the last non-empty row, or outside the four-outcome vocabulary)."""
        rows = [row for row in out.splitlines() if row.strip()]
        outcome_rows = [row for row in rows if row.startswith("OUTCOME: ")]
        if len(outcome_rows) != 1 or not rows or not rows[-1].startswith(
            "OUTCOME: "
        ):
            return ""
        label = rows[-1][len("OUTCOME: "):].strip()
        return label if label in outcome_labels else ""

    with tempfile.TemporaryDirectory(prefix="cleanup-scope-selftest-") as tmp:
        root = Path(tmp)

        # Shared dirty tree: unrelated modified tracked file + untracked file;
        # allow-list covers only the task-owned file.
        def make_dirty_tree(name: str) -> Path:
            repo = _make_fixture_repo(root, name)
            (repo / "tracked-extra.txt").write_text("tracked-extra modified\n")
            _git(repo, "add", "tracked-extra.txt")
            _git(repo, "commit", "-q", "-m", "add tracked-extra")
            (repo / "tracked-extra.txt").write_text("tracked-extra dirty\n")
            (repo / "untracked-extra.txt").write_text("untracked\n")
            return repo

        # Arm 1: unaccounted_dirty_fails
        repo = make_dirty_tree("unaccounted-dirty")
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt"])
        if code != 1:
            failures.append(
                f"unaccounted_dirty_fails: want exit 1, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "fail":
            failures.append(
                f"unaccounted_dirty_fails: stdout must end with exactly one final "
                f"OUTCOME: fail row, got {out!r}"
            )
        for span, path in [
            (ERR_DIRTY, "tracked-extra.txt"),
            (ERR_DIRTY, "untracked-extra.txt"),
        ]:
            if f"{span} {path}" not in err:
                failures.append(
                    f"unaccounted_dirty_fails: stderr missing {span} {path!r}: {err!r}"
                )
        # Ordering: error lines are sorted, one per path, so the
        # tracked-extra line precedes the untracked-extra line.
        lines = [line for line in err.splitlines() if line.startswith("cleanup-scope:")]
        if lines != sorted(lines):
            failures.append(
                f"unaccounted_dirty_fails: stderr lines not sorted: {lines!r}"
            )

        # Arm 2: allowed_dirty_passes (same tree, both paths allow-listed)
        repo = make_dirty_tree("allowed-dirty")
        code, out, err = _run_checker(
            repo, "HEAD", ["owned.txt", "tracked-extra.txt", "untracked-extra.txt"]
        )
        if code != 0:
            failures.append(
                f"allowed_dirty_passes: want exit 0, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "pass":
            failures.append(
                f"allowed_dirty_passes: stdout must end with exactly one final "
                f"OUTCOME: pass row, got {out!r}"
            )

        # Arm 3: unauthorized_deletion_fails (base file deleted, not allowed;
        # an untracked extra file makes stderr mix both error classes, and the
        # full stderr must equal the expected sorted two-line sequence with
        # the unaccounted dirty line before the unauthorized deletion line)
        repo = _make_fixture_repo(root, "unauthorized-deletion")
        (repo / "base.txt").unlink()
        (repo / "untracked-extra.txt").write_text("untracked\n")
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt"])
        if code != 1:
            failures.append(
                f"unauthorized_deletion_fails: want exit 1, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "fail":
            failures.append(
                f"unauthorized_deletion_fails: stdout must end with exactly one final "
                f"OUTCOME: fail row, got {out!r}"
            )
        expected_lines = sorted(
            [f"{ERR_DIRTY} untracked-extra.txt", f"{ERR_DELETION} base.txt"]
        )
        if err.splitlines() != expected_lines:
            failures.append(
                f"unauthorized_deletion_fails: stderr {err.splitlines()!r} "
                f"!= expected {expected_lines!r}"
            )
        if f"{ERR_DIRTY} base.txt" in err:
            failures.append(
                f"unauthorized_deletion_fails: deleted path misclassified as dirty: {err!r}"
            )

        # Arm 4: clean_tree_passes (only the allow-listed task-owned file is dirty)
        repo = _make_fixture_repo(root, "clean-tree")
        (repo / "owned.txt").write_text("task-owned v2\n")
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt"])
        if code != 0:
            failures.append(
                f"clean_tree_passes: want exit 0, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "pass":
            failures.append(
                f"clean_tree_passes: stdout must end with exactly one final "
                f"OUTCOME: pass row, got {out!r}"
            )

        # Arm 5: staged_modification_fails (staged but uncommitted change,
        # not allow-listed, must fail as unaccounted dirty)
        repo = _make_fixture_repo(root, "staged-modification")
        (repo / "owned.txt").write_text("task-owned staged\n")
        _git(repo, "add", "owned.txt")
        code, out, err = _run_checker(repo, "HEAD", ["other.txt"])
        if code != 1:
            failures.append(
                f"staged_modification_fails: want exit 1, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "fail":
            failures.append(
                f"staged_modification_fails: stdout must end with exactly one final "
                f"OUTCOME: fail row, got {out!r}"
            )
        if f"{ERR_DIRTY} owned.txt" not in err:
            failures.append(
                f"staged_modification_fails: stderr missing dirty line: {err!r}"
            )

        # Arm 6: allowed_deletion_passes (ledger authorizes the deletion)
        repo = _make_fixture_repo(root, "allowed-deletion")
        (repo / "base.txt").unlink()
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt", "base.txt"])
        if code != 0:
            failures.append(
                f"allowed_deletion_passes: want exit 0, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "pass":
            failures.append(
                f"allowed_deletion_passes: stdout must end with exactly one final "
                f"OUTCOME: pass row, got {out!r}"
            )

        # Arm 7: untracked_dir_file_allows (untracked file inside a wholly
        # untracked directory, allow-listed by file path, must pass)
        repo = _make_fixture_repo(root, "untracked-dir")
        nested = repo / "nested" / "deep"
        nested.mkdir(parents=True)
        (nested / "scratch-notes.md").write_text("peer session scratch\n")
        code, out, err = _run_checker(
            repo, "HEAD", ["owned.txt", "nested/deep/scratch-notes.md"]
        )
        if code != 0:
            failures.append(
                f"untracked_dir_file_allows: want exit 0, got {code}; stderr={err!r}"
            )
        # Fail side (negative arm): allow-listing only the directory string
        # ``nested/`` must NOT cover ``nested/deep/scratch-notes.md``:
        # matching is byte-exact with no directory-prefix semantics, so the
        # run fails exit 1 with the full nested filename verbatim on stderr.
        # Pins against a regression to prefix matching.
        code, out, err = _run_checker(repo, "HEAD", ["nested/"])
        if code != 1:
            failures.append(
                f"untracked_dir_prefix_not_allowed: want exit 1, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "fail":
            failures.append(
                f"untracked_dir_prefix_not_allowed: stdout must end with exactly "
                f"one final OUTCOME: fail row, got {out!r}"
            )
        if f"{ERR_DIRTY} nested/deep/scratch-notes.md" not in err:
            failures.append(
                f"untracked_dir_prefix_not_allowed: stderr missing byte-exact "
                f"nested path line: {err!r}"
            )
        # Fail side (negative arm): a ``./``-prefixed allow entry must NOT
        # match the verbatim repo-root-relative path: matching is byte-exact
        # with no ``./`` normalization, so the run fails exit 1 with the
        # path named as unaccounted dirty. Pins the no-``./``-normalization
        # claim in the module docstring.
        code, out, err = _run_checker(
            repo, "HEAD", ["./nested/deep/scratch-notes.md"]
        )
        if code != 1:
            failures.append(
                f"untracked_dir_dot_prefix_not_normalized: want exit 1, "
                f"got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "fail":
            failures.append(
                f"untracked_dir_dot_prefix_not_normalized: stdout must end with "
                f"exactly one final OUTCOME: fail row, got {out!r}"
            )
        if f"{ERR_DIRTY} nested/deep/scratch-notes.md" not in err:
            failures.append(
                f"untracked_dir_dot_prefix_not_normalized: stderr missing "
                f"unaccounted-dirty line for nested path: {err!r}"
            )

        # Arm 8: unicode_dirty_allow_passes (non-ASCII dirty path,
        # allow-listed by its real name, must pass)
        repo = _make_fixture_repo(root, "unicode-dirty")
        unicode_name = "notes-café-ünïcode.md"
        (repo / unicode_name).write_text("unicode scratch\n")
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt", unicode_name])
        if code != 0:
            failures.append(
                f"unicode_dirty_allow_passes: want exit 0, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "pass":
            failures.append(
                f"unicode_dirty_allow_passes: stdout must end with exactly one final "
                f"OUTCOME: pass row, got {out!r}"
            )
        # Fail side: same fixture with the unicode path NOT allow-listed; the
        # error line must carry the real name verbatim (no C-quoting).
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt"])
        if code != 1:
            failures.append(
                f"unicode_dirty_allow_fails: want exit 1, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "fail":
            failures.append(
                f"unicode_dirty_allow_fails: stdout must end with exactly one final "
                f"OUTCOME: fail row, got {out!r}"
            )
        if f"{ERR_DIRTY} {unicode_name}" not in err:
            failures.append(
                f"unicode_dirty_allow_fails: stderr missing verbatim unicode path: {err!r}"
            )

        # Arm 9: rename_deletion_source_requires_allow (staged rename with
        # only the destination allow-listed; the rename source is a
        # deletion and must fail as unauthorized, not pass silently)
        repo = _make_fixture_repo(root, "rename-source")
        (repo / "a.txt").write_text("committed v1\n")
        _git(repo, "add", "a.txt")
        _git(repo, "commit", "-q", "-m", "add a.txt")
        _git(repo, "mv", "a.txt", "z.txt")
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt", "z.txt"])
        if code != 1:
            failures.append(
                f"rename_deletion_source_requires_allow: want exit 1, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "fail":
            failures.append(
                f"rename_deletion_source_requires_allow: stdout must end with exactly one final "
                f"OUTCOME: fail row, got {out!r}"
            )
        if f"{ERR_DELETION} a.txt" not in err:
            failures.append(
                f"rename_deletion_source_requires_allow: stderr missing unauthorized deletion of a.txt: {err!r}"
            )
        if f"{ERR_DIRTY} a.txt" in err:
            failures.append(
                f"rename_deletion_source_requires_allow: rename source misclassified as dirty: {err!r}"
            )

        # Arm 10: unresolvable_inputs_tool_error (renewed from the legacy
        # internal-error exit-2 shape per the answer-vocabulary criterion: an
        # input that never resolved is a tool error, exit 3). Three legs:
        # (a) a nonexistent base ref, (b) a missing --base operand (usage,
        # argparse override), (c) a --repo-root outside any repository. Each
        # leg pins exit 3 with exactly one final `OUTCOME: tool_error` row on
        # stdout and the retired ``cleanup-scope: internal error`` prefix
        # absent from stderr.
        repo = _make_fixture_repo(root, "internal-error")
        code, out, err = _run_checker(repo, "refs/heads/nonexistent", ["owned.txt"])
        if code != 3:
            failures.append(
                f"unresolvable_inputs_tool_error: nonexistent base ref: want "
                f"exit 3, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "tool_error":
            failures.append(
                f"unresolvable_inputs_tool_error: nonexistent base ref: stdout "
                f"must end with exactly one final OUTCOME: tool_error row, "
                f"got {out!r}"
            )
        if "cleanup-scope: internal error" in err:
            failures.append(
                f"unresolvable_inputs_tool_error: nonexistent base ref: "
                f"retired internal-error prefix still on stderr: {err!r}"
            )
        # T4(a): without --selftest and without --base, argparse must refuse
        # with exit 3 (the usage override; a usage violation is a tool error,
        # never the legacy argparse exit 2).
        proc = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--repo-root",
                str(repo),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 3:
            failures.append(
                f"unresolvable_inputs_tool_error: missing --base: want exit 3, "
                f"got {proc.returncode}; stderr={proc.stderr!r}"
            )
        if "OUTCOME: tool_error" not in proc.stderr:
            failures.append(
                f"unresolvable_inputs_tool_error: missing --base: stderr "
                f"missing OUTCOME: tool_error row: {proc.stderr!r}"
            )
        # T4(b): --repo-root at an empty non-repo temp dir -> exit 3 (tool
        # error) with the retired internal-error prefix absent.
        non_repo = root / "non-repo"
        non_repo.mkdir()
        proc = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--repo-root",
                str(non_repo),
                "--base",
                "HEAD",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 3:
            failures.append(
                f"unresolvable_inputs_tool_error: non-repo root: want exit 3, "
                f"got {proc.returncode}; stderr={proc.stderr!r}"
            )
        if final_outcome(proc.stdout) != "tool_error":
            failures.append(
                f"unresolvable_inputs_tool_error: non-repo root: stdout must "
                f"end with exactly one final OUTCOME: tool_error row, "
                f"got {proc.stdout!r}"
            )
        if "cleanup-scope: internal error" in proc.stderr:
            failures.append(
                f"unresolvable_inputs_tool_error: non-repo root: retired "
                f"internal-error prefix still on stderr: {proc.stderr!r}"
            )

        # Arm 11: gitignored_dirty_invisible (documents the known limitation
        # as observable behavior: a .gitignore'd dirty file is invisible, so
        # the checker passes and the ignored path never appears on stderr)
        repo = _make_fixture_repo(root, "gitignored-invisible")
        (repo / ".gitignore").write_text("ignored-dirty.txt\n")
        _git(repo, "add", ".gitignore")
        _git(repo, "commit", "-q", "-m", "add gitignore")
        (repo / "ignored-dirty.txt").write_text("ignored dirty content\n")
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt"])
        if code != 0:
            failures.append(
                f"gitignored_dirty_invisible: want exit 0, got {code}; stderr={err!r}"
            )
        if final_outcome(out) != "pass":
            failures.append(
                f"gitignored_dirty_invisible: stdout must end with exactly one final "
                f"OUTCOME: pass row, got {out!r}"
            )
        if "ignored-dirty.txt" in err:
            failures.append(
                f"gitignored_dirty_invisible: ignored path leaked to stderr: {err!r}"
            )

        # Arm 12: plumbing_failure_indeterminate (a corrupted loose tree
        # object makes the checker's git plumbing fail over already-resolved
        # inputs: the base ref resolves and the root is a repository, so the
        # answer-vocabulary criterion places the failure at indeterminate,
        # exit 2, naming what could not be determined; the legacy shape
        # lumped this with usage and unresolvable inputs at the internal-
        # error exit 2).
        repo = _make_fixture_repo(root, "plumbing-failure")
        tree_sha = _git(repo, "rev-parse", "HEAD^{tree}").strip()
        tree_obj = repo / ".git" / "objects" / tree_sha[:2] / tree_sha[2:]
        tree_obj.chmod(0o644)  # git writes loose objects read-only
        tree_obj.write_bytes(b"corrupted loose object")
        code, out, err = _run_checker(repo, "HEAD", ["owned.txt"])
        if code != 2:
            failures.append(
                f"plumbing_failure_indeterminate: want exit 2, got {code}; "
                f"stderr={err!r}"
            )
        if final_outcome(out) != "indeterminate":
            failures.append(
                f"plumbing_failure_indeterminate: stdout must end with exactly "
                f"one final OUTCOME: indeterminate row, got {out!r}"
            )
        if "could not determine" not in err:
            failures.append(
                f"plumbing_failure_indeterminate: stderr missing the "
                f"could-not-determine evidence: {err!r}"
            )

    if failures:
        for failure in failures:
            print(f"SELFTEST FAILED: {failure}", file=sys.stderr)
        return 1
    print("SELFTEST OK: 12/12 arms passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = OutcomeArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=".", help="repository root (default: .)")
    parser.add_argument("--base", help="base ref for the deletion diff")
    parser.add_argument("--allow", action="append", default=[], help=(
        "repo-root-relative allow-listed path (repeatable)"
    ))
    parser.add_argument("--selftest", action="store_true", help=(
        "run the built-in twelve-arm selftest"
    ))
    args = parser.parse_args(argv)

    # --base is required for classification but not for --selftest, which
    # must run standalone; the override parser turns the refusal into a tool
    # error (usage row plus final `OUTCOME: tool_error` on stderr, exit 3).
    if not args.selftest and not args.base:
        parser.error("--base is required unless --selftest is given")

    if args.selftest:
        return run_selftest()

    repo_root = Path(args.repo_root).resolve()

    # Resolution arms: an input that never resolved is a tool error (the
    # answer-vocabulary criterion), never indeterminacy about a verdict.
    probe = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        print(
            f"cleanup-scope: tool error: {repo_root} is not inside a git "
            f"repository",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    verify = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "rev-parse",
            "--verify",
            "--quiet",
            f"{args.base}^{{commit}}",
        ],
        capture_output=True,
        text=True,
    )
    if verify.returncode != 0:
        print(
            f"cleanup-scope: tool error: base ref {args.base!r} does not "
            f"resolve to a commit in {repo_root}",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3

    try:
        errors = check(repo_root, args.base, args.allow)
    except Exception as exc:  # git plumbing failure over resolved inputs
        print(f"cleanup-scope: observed: {exc}", file=sys.stderr)
        print(
            "cleanup-scope: could not determine the dirty/deleted path "
            "classification",
            file=sys.stderr,
        )
        print("OUTCOME: indeterminate")
        return 2
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print("OUTCOME: fail")
        return 1
    print("cleanup-scope: baseline OK")
    print("OUTCOME: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
