#!/usr/bin/env python3
"""Base-branch amend guard: immutability of landed base-branch commits.

Rule (docs/history/plans/2026-10-02-evidence-integrity-fences.md, Terms):
once a commit is reachable from the base branch it is never amended;
corrections land as additive follow-up commits; amend is legal only inside
a session's own unlanded branch before the landing critical section.

Origin: docs/history/backlog/2026-10-02-base-branch-commit-immutability.md.
Witness: the 2026-10-02 18:09 amend of a peer's landed tip (a peer session
amended the base-branch tip another session had landed four minutes earlier).

Two read-only subcommands:

check-head --base-branch <name>
    Run in the repository whose commit path is being gated (no --repo; the
    current working directory is the repository). Exit 1 (refuse) when HEAD
    is the named base branch AND the last reflog entry on HEAD
    (`git reflog -1 --format=%gs`) reads `commit (amend)`. Exit 0 otherwise:
    ordinary additive commits are unaffected, and so is an amend inside a
    session's own unlanded branch (HEAD is not the base branch there).

reflog-scan --repo <root> --base-branch <name> --since <pre-tip-sha>
            [--allow-sha <sha>]...
    Walk the base branch's reflog from newest down to (but excluding) the
    entry whose new commit is the since sha, and print one report row per
    `commit (amend)` entry whose new commit is not among the repeatable
    --allow-sha values. The landing critical section passes the shas it
    authored, so an amend of a base-branch tip the landing did not author
    is always reported. Exit 1 when any row is found, 0 when none.

Exit 2 on tool failure for both subcommands; the evidence line goes to
stderr. Report rows and verdict lines go to stdout.
"""

import argparse
import subprocess
import sys

AMEND_SUBJECT = "commit (amend)"
AMEND_PREFIX = AMEND_SUBJECT + ":"


def _is_amend_subject(subject):
    """True when the reflog subject is an amend action: git writes the
    action token followed by the commit message ("commit (amend): <msg>"),
    so the bare token and the colon-suffixed form are both amend entries."""
    return subject == AMEND_SUBJECT or subject.startswith(AMEND_PREFIX)


def _run_git(repo, *cmd):
    argv = ["git"]
    if repo is not None:
        argv += ["-C", repo]
    argv += list(cmd)
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _tool_failure(detail):
    print("TOOL_FAILURE: base-branch amend guard could not run: %s" % detail,
          file=sys.stderr)
    return 2


def cmd_check_head(args):
    head = _run_git(None, "rev-parse", "--abbrev-ref", "HEAD")
    if head.returncode != 0:
        return _tool_failure("git rev-parse --abbrev-ref HEAD failed: "
                             + head.stderr.decode(errors="replace").strip())
    branch = head.stdout.decode(errors="replace").strip()
    if branch != args.base_branch:
        print("ok: HEAD is on '%s', not the base branch '%s'; the "
              "base-branch amend fence does not apply here"
              % (branch, args.base_branch))
        return 0
    reflog = _run_git(None, "reflog", "-1", "--format=%gs")
    if reflog.returncode != 0:
        return _tool_failure("git reflog -1 --format=%gs failed: "
                             + reflog.stderr.decode(errors="replace").strip())
    subject = reflog.stdout.decode(errors="replace").strip()
    if _is_amend_subject(subject):
        print("REFUSE: HEAD is the base branch '%s' and the last reflog "
              "entry is an amend ('%s'); the base-branch tip is immutable, "
              "land the correction as an additive follow-up commit instead"
              % (args.base_branch, subject))
        return 1
    print("ok: last reflog entry on HEAD reads '%s'; no base-branch amend "
          "detected" % subject)
    return 0


def cmd_reflog_scan(args):
    since = _run_git(args.repo, "rev-parse", "--verify",
                     args.since + "^{commit}")
    if since.returncode != 0:
        return _tool_failure("since sha '%s' does not resolve to a commit: %s"
                             % (args.since,
                                since.stderr.decode(errors="replace").strip()))
    since_sha = since.stdout.decode(errors="replace").strip()

    allowed = []
    for value in args.allow_sha:
        resolved = _run_git(args.repo, "rev-parse", "--verify",
                            value + "^{commit}")
        if resolved.returncode != 0:
            return _tool_failure("allow sha '%s' does not resolve to a "
                                 "commit: %s"
                                 % (value,
                                    resolved.stderr.decode(
                                        errors="replace").strip()))
        allowed.append(resolved.stdout.decode(errors="replace").strip())

    reflog = _run_git(args.repo, "reflog", "--format=%H %gs",
                      args.base_branch)
    if reflog.returncode != 0:
        return _tool_failure("git reflog --format='%%H %%gs' %s failed: %s"
                             % (args.base_branch,
                                reflog.stderr.decode(
                                    errors="replace").strip()))

    rows = []
    window_closed = False
    for line in reflog.stdout.decode(errors="replace").splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition(" ")
        if sha == since_sha:
            window_closed = True
            break
        if _is_amend_subject(subject) and sha not in allowed:
            rows.append(sha)
    if not window_closed:
        return _tool_failure("since sha %s never appears as a reflog entry "
                             "of base branch '%s'; the scan window is "
                             "undeterminable, reporting nothing would be a "
                             "silent pass" % (since_sha, args.base_branch))

    for sha in rows:
        print("amend-entry %s %s" % (sha, AMEND_SUBJECT))
    if rows:
        print("%d foreign amend row(s) on the '%s' reflog newer than %s"
              % (len(rows), args.base_branch, since_sha), file=sys.stderr)
        return 1
    print("ok: no unallowed '%s' entry on the '%s' reflog newer than %s"
          % (AMEND_SUBJECT, args.base_branch, since_sha))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Base-branch amend guard: refuse an amend with HEAD on "
                    "the base branch and report foreign amend entries on "
                    "the base branch's reflog.")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser(
        "check-head",
        help="refuse (exit 1) when HEAD is the base branch and the last "
             "reflog entry on HEAD reads 'commit (amend)'; exit 0 otherwise")
    check.add_argument("--base-branch", required=True,
                       help="the base branch name HEAD is compared against")
    check.set_defaults(func=cmd_check_head)

    scan = sub.add_parser(
        "reflog-scan",
        help="report every 'commit (amend)' entry on the base branch's "
             "reflog newer than the since sha whose new commit is not among "
             "the --allow-sha values; exit 1 when any is found, 0 when none")
    scan.add_argument("--repo", required=True,
                      help="repository root the base branch lives in")
    scan.add_argument("--base-branch", required=True,
                      help="the base branch whose reflog is scanned")
    scan.add_argument("--since", required=True,
                      help="the pre-tip sha; the scan window is every "
                           "reflog entry newer than this commit (values "
                           "resolve via git rev-parse)")
    scan.add_argument("--allow-sha", action="append", default=[],
                      help="commit sha an authored amend is allowed to "
                           "carry (repeatable; values resolve via git "
                           "rev-parse)")
    scan.set_defaults(func=cmd_reflog_scan)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
