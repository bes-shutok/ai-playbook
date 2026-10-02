#!/usr/bin/env python3
"""Pre-stage freshness gate: refuse staging candidate paths whose disk bytes
are stale against HEAD.

A residual landing lane may stage paths in a checkout only when each candidate
path's disk bytes equal the checkout HEAD's blob for that path, or the path is
a session-owned fresh write listed in the fresh-write list. The gate is
read-only by contract: it verifies and refuses, and the calling lane defers on
a refusal. It never stages, restores, or writes.

CLI:
  check --repo ROOT [--head REF] [--fresh-list FILE] -- PATH...

The stale-checkout discriminator reuses the ancestor-blob walk already defined
in the Worktree-first standard: walk `git log --format=%H -- <path>`, skip
commits where the path does not exist, and never treat a plumbing miss as a
tool failure.

Exit codes (outcome contract): 0 pass, 1 fail (a modeled refusal), 2
indeterminate (the git plumbing answered outside its 0/1 answer vocabulary
over resolved inputs, or a candidate path's HEAD tree mode type disagrees
with its disk lstat type, so freshness could not be determined; when one
multi-path run observes both regressed and indeterminate paths,
indeterminate dominates and every regressed path is still named), 3 tool
error (an unresolvable head, an unreadable fresh list, a usage error, or an
unheld environment assumption). Every non-metadata run ends with exactly one
final `OUTCOME:` line after the human-readable evidence; `--help` and usage
metadata exits emit no `OUTCOME:` line.
"""

import argparse
import os
import subprocess
import sys

OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}


class OutcomeArgumentParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit 3 (tool error) with a final
    `OUTCOME: tool_error` line on stdout, overriding argparse's default
    exit 2; `--help` stays a metadata exit without an `OUTCOME:` line."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        print("OUTCOME: %s" % OUTCOME_LABELS[3])
        raise SystemExit(3)


class PlumbingFailure(Exception):
    """A git plumbing failure over resolved inputs (the indeterminate
    class, never a modeled refusal)."""


def _git(repo, *args):
    """Run git plumbing in ROOT; returns CompletedProcess."""
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, check=False,
    )


def _tool_error(message):
    sys.stderr.write("prestage-freshness-gate tool error: %s\n" % message)
    return 3


def _indeterminate(message):
    sys.stderr.write("prestage-freshness-gate indeterminate: %s\n" % message)
    return 2


def _resolve_head(repo, ref):
    """Resolve REF as a commit; None when unresolvable."""
    proc = _git(repo, "rev-parse", "--verify", ref + "^{commit}")
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _load_fresh_list(path):
    """Parse the fresh-write list (one path per line, '#' comments allowed);
    None when the file is unreadable."""
    if path is None:
        return set()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return None
    entries = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.add(stripped)
    return entries


def _disk_blob(repo, rel):
    """Blob sha of the path's on-disk bytes; None when absent from disk."""
    if not os.path.exists(os.path.join(str(repo), rel)):
        return None
    proc = _git(repo, "hash-object", "--", rel)
    if proc.returncode != 0:
        raise PlumbingFailure("hash-object failed for %s" % rel)
    return proc.stdout.strip()


def _blob_at(repo, sha, rel):
    """Blob sha of REL inside commit SHA; None when the path is absent there
    (the caller decides whether a miss is the expected absent-object case)."""
    proc = _git(repo, "rev-parse", "--verify", "%s:%s" % (sha, rel))
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _head_tree_mode(repo, head_sha, rel):
    """Tree mode of REL inside commit SHA; None when the path is absent
    there. Raises PlumbingFailure when ls-tree fails over the resolved
    head."""
    proc = _git(repo, "ls-tree", head_sha, "--", rel)
    if proc.returncode != 0:
        raise PlumbingFailure("ls-tree failed for %s" % rel)
    line = proc.stdout.strip()
    if not line:
        return None
    return line.split()[0]


def _ancestor_match(repo, rel, disk_blob):
    """First commit walking `git log --format=%H -- REL` whose blob equals
    DISK_BLOB, skipping commits where the path does not exist; None when no
    ancestor blob matches."""
    proc = _git(repo, "log", "--format=%H", "--", rel)
    if proc.returncode != 0:
        raise PlumbingFailure("git log failed for %s" % rel)
    for line in proc.stdout.splitlines():
        sha = line.strip()
        if not sha:
            continue
        blob = _blob_at(repo, sha, rel)
        if blob is not None and blob == disk_blob:
            return sha
    return None


def _type_change_detail(rel, head_mode, disk_is_symlink):
    """Observed/could-not-determine evidence for a HEAD-versus-disk type
    disagreement (the explicit type check ahead of the byte comparison)."""
    disk_type = "symlink" if disk_is_symlink else "regular file"
    return (
        "type change for %s: HEAD tree mode %s disagrees with the disk "
        "lstat type (%s); observed: the tracked entry and the disk entry "
        "are different filesystem types; freshness could not be determined"
        % (rel, head_mode, disk_type))


def cmd_check(args):
    repo = args.repo
    head_sha = _resolve_head(repo, args.head)
    if head_sha is None:
        return _tool_error("head unresolvable: %s" % args.head)
    fresh = _load_fresh_list(args.fresh_list)
    if fresh is None:
        return _tool_error("fresh list unreadable: %s" % args.fresh_list)
    refused = False
    # Collected indeterminate details (typechange disagreements and
    # plumbing failures): the loop always finishes so every remaining
    # path still yields its evidence; indeterminate (exit 2) then
    # dominates a stale refuse (exit 1) per the outcome contract's
    # dominance rule (a multi-input run reports indeterminate AND still
    # names every regressed path, never argument-order-dependent
    # evidence).
    indeterminate_details = []
    for rel in args.paths:
        try:
            if rel in fresh:
                print("ok: %s" % rel)
                continue
            head_blob = _blob_at(repo, head_sha, rel)
            disk_path = os.path.join(str(repo), rel)
            if head_blob is not None and os.path.lexists(disk_path):
                # NEW explicit type check ahead of the byte comparison: a
                # HEAD tree mode type (file versus symlink) that disagrees
                # with the disk lstat type (including a dangling symlink)
                # is indeterminate, never a stale refuse or a bogus
                # byte-equality pass through a symlink's target bytes.
                head_mode = _head_tree_mode(repo, head_sha, rel)
                disk_is_symlink = os.path.islink(disk_path)
                if head_mode is not None and (
                        head_mode.startswith("120") != disk_is_symlink):
                    indeterminate_details.append(_type_change_detail(
                        rel, head_mode, disk_is_symlink))
                    continue
            disk = _disk_blob(repo, rel)
            if disk is not None and head_blob is not None and disk == head_blob:
                print("ok: %s" % rel)
                continue
            refused = True
            ancestor = None
            if disk is not None:
                ancestor = _ancestor_match(repo, rel, disk)
            if ancestor is not None:
                print("refuse: %s disk bytes equal ancestor %s, not HEAD %s"
                      % (rel, ancestor, head_sha))
            else:
                print("refuse: %s disk bytes match neither HEAD nor the "
                      "session-owned fresh list" % rel)
        except PlumbingFailure as exc:
            indeterminate_details.append(
                "%s over resolved head %s; observed: the plumbing answered "
                "outside the 0/1 answer vocabulary; freshness could not be "
                "determined" % (exc, head_sha))
    for detail in indeterminate_details:
        _indeterminate(detail)
    if indeterminate_details:
        return 2
    if refused:
        return 1
    print("ok: all candidate paths fresh against HEAD")
    return 0


def main(argv):
    parser = OutcomeArgumentParser(
        prog="prestage_freshness_gate.py",
        description=("Refuse staging candidate paths whose disk bytes match "
                     "neither HEAD nor the session-owned fresh list."),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check")
    check.add_argument("--repo", required=True)
    check.add_argument("--head", default="HEAD")
    check.add_argument("--fresh-list", dest="fresh_list", default=None)
    check.add_argument("paths", nargs="+")
    check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    code = args.func(args)
    print("OUTCOME: %s" % OUTCOME_LABELS[code])
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
