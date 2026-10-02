#!/usr/bin/env python3
"""Read-freshness probe: the two-command disk re-derivation helper.

Given a repository root, a repo-relative path, and a claimed state (present,
absent, or stale), runs the filesystem probe and the git probe at the tip
commit and prints exactly one verdict line on stdout:

- ``match``                      exit 0
- ``mismatch: <which command>``  exit 1 (the command that contradicted the claim)
- ``unresolvable: <path>``       exit 2 (also the tool-failure exit; the detail
  goes to stderr)

Probe definitions (docs/history/plans/2026-10-02-evidence-integrity-fences.md,
Task 1; origin docs/history/backlog/2026-10-02-stale-read-record-derivation-fence.md):

- ``present``: the filesystem probe is ``ls``/``stat`` on the path; the git
  probe is ``git cat-file -e <tip>:<path>``.
- ``absent``: the filesystem probe is the path being absent on disk; the git
  probe is ``git cat-file -e <tip>:<path>`` failing.
- ``stale``: the filesystem probe is the path's mtime compared against the
  tip commit's timestamp (mtime predating the tip supports staleness); the
  git probe is the worktree bytes equalling the tip blob (``git show
  <tip>:<path>`` byte-compare), so the verdict flips only on the byte
  comparison.

A path known to neither probe is unresolvable: with both probes answering the
same way there is no cross-check, so the claim stays unverified.
"""

import argparse
import os
import subprocess
import sys


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _unresolvable(rel, detail):
    print("unresolvable: %s" % rel)
    print(detail, file=sys.stderr)
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Two-command disk re-derivation for one claimed path state.")
    parser.add_argument("--repo", required=True,
                        help="repository root; the tip is that repository's HEAD")
    parser.add_argument("--path", required=True,
                        help="repo-relative path the claim is about")
    parser.add_argument("--claim", required=True,
                        choices=("present", "absent", "stale"),
                        help="claimed state of the path")
    args = parser.parse_args(argv)

    rel = args.path
    disk_path = rel if os.path.isabs(rel) else os.path.join(args.repo, rel)

    tip = _git(args.repo, "rev-parse", "--verify", "HEAD")
    if tip.returncode != 0:
        return _unresolvable(rel, "git rev-parse --verify HEAD failed: "
                             + tip.stderr.decode(errors="replace").strip())
    tip = tip.stdout.decode().strip()
    tip_path = "%s:%s" % (tip, rel)

    fs_present = os.path.exists(disk_path)
    in_tip = _git(args.repo, "cat-file", "-e", tip_path)
    git_present = in_tip.returncode == 0

    if args.claim == "present":
        if fs_present and git_present:
            print("match")
            return 0
        if git_present and not fs_present:
            print("mismatch: filesystem probe")
            return 1
        if fs_present and not git_present:
            print("mismatch: git probe")
            return 1
        return _unresolvable(rel, "path known to neither the filesystem "
                             "nor the tip commit")

    if args.claim == "absent":
        if not fs_present and not git_present:
            return _unresolvable(rel, "path known to neither the filesystem "
                                 "nor the tip commit")
        if fs_present:
            # Present on disk: the filesystem probe contradicts the absence
            # claim whether or not the tip still carries the path.
            print("mismatch: filesystem probe")
            return 1
        print("mismatch: git probe")
        return 1

    # claim == "stale": the verdict flips only on the byte comparison.
    if not fs_present or not git_present:
        return _unresolvable(rel, "the stale claim needs the path on disk "
                             "and at the tip commit")
    try:
        st_mtime = os.stat(disk_path).st_mtime
        worktree_bytes = open(disk_path, "rb").read()
    except OSError as exc:
        return _unresolvable(rel, "filesystem probe failed: %s" % exc)
    tip_time = _git(args.repo, "show", "-s", "--format=%ct", tip)
    if tip_time.returncode != 0:
        return _unresolvable(rel, "git show -s --format=%ct failed: "
                             + tip_time.stderr.decode(errors="replace").strip())
    mtime_predates_tip = st_mtime < int(tip_time.stdout.decode().strip())
    blob = _git(args.repo, "show", tip_path)
    if blob.returncode != 0:
        return _unresolvable(rel, "git show %s failed: %s"
                             % (tip_path, blob.stderr.decode(errors="replace").strip()))
    if worktree_bytes != blob.stdout:
        print("mismatch: git probe")
        return 1
    if not mtime_predates_tip:
        print("note: mtime does not predate the tip timestamp; "
              "the byte comparison carried the verdict", file=sys.stderr)
    print("match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
