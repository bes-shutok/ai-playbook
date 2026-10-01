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

Exit codes: 0 pass, 1 refuse, 2 tool failure (guard-family contract).
"""

import argparse
import os
import subprocess
import sys


class ToolFailure(Exception):
    """A git plumbing failure outside the expected absent-object cases."""


def _git(repo, *args):
    """Run git plumbing in ROOT; returns CompletedProcess."""
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, check=False,
    )


def _tool_failure(message):
    sys.stderr.write("prestage-freshness-gate tool failure: %s\n" % message)
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
        raise ToolFailure("hash-object failed for %s" % rel)
    return proc.stdout.strip()


def _blob_at(repo, sha, rel):
    """Blob sha of REL inside commit SHA; None when the path is absent there
    (the caller decides whether a miss is the expected absent-object case)."""
    proc = _git(repo, "rev-parse", "--verify", "%s:%s" % (sha, rel))
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _ancestor_match(repo, rel, disk_blob):
    """First commit walking `git log --format=%H -- REL` whose blob equals
    DISK_BLOB, skipping commits where the path does not exist; None when no
    ancestor blob matches."""
    proc = _git(repo, "log", "--format=%H", "--", rel)
    if proc.returncode != 0:
        raise ToolFailure("git log failed for %s" % rel)
    for line in proc.stdout.splitlines():
        sha = line.strip()
        if not sha:
            continue
        blob = _blob_at(repo, sha, rel)
        if blob is not None and blob == disk_blob:
            return sha
    return None


def cmd_check(args):
    repo = args.repo
    head_sha = _resolve_head(repo, args.head)
    if head_sha is None:
        return _tool_failure("head unresolvable: %s" % args.head)
    fresh = _load_fresh_list(args.fresh_list)
    if fresh is None:
        return _tool_failure("fresh list unreadable: %s" % args.fresh_list)
    refused = False
    for rel in args.paths:
        try:
            if rel in fresh:
                print("ok: %s" % rel)
                continue
            disk = _disk_blob(repo, rel)
            head_blob = _blob_at(repo, head_sha, rel)
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
        except ToolFailure as exc:
            return _tool_failure(str(exc))
    if refused:
        return 1
    print("ok: all candidate paths fresh against HEAD")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(
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
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
