#!/usr/bin/env python3
"""Landing parentage gate: refuse landings that sever the default branch's history.

Witnessed defect (2026-09-27): a squash landing moved main to a parentless
commit carrying the full repository tree, severing 391 commits from main.

Two subcommands over one parentage/ancestry core:

  pre-swap --repo ROOT --pre-tip SHA --new-commit SHA
      Before a ref swap or as the commit-time check: the landing commit must
      have exactly one parent and that parent must equal PRE-TIP.
  post-landing --repo ROOT --pre-tip SHA --default-ref NAME [--origin-ref REF]
      After a landing: the default branch must still descend from PRE-TIP
      (evaluated and reported first) and, when --origin-ref resolves, from
      that ref too; a non-resolving origin ref is a named skip, not a refusal.

Exit codes: 0 pass, 1 refuse, 2 tool failure (guard-family contract).
"""

import argparse
import subprocess
import sys


def _git(repo, *args):
    """Run git plumbing in ROOT; returns CompletedProcess."""
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, check=False,
    )


def _resolve_commit(repo, value):
    """Resolve VALUE as a commit; returns sha or None (unresolvable)."""
    proc = _git(repo, "rev-parse", "--verify", value + "^{commit}")
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _parents(repo, commit):
    """Parent list of COMMIT via rev-list --parents; None on plumbing failure."""
    proc = _git(repo, "rev-list", "--parents", "-n", "1", commit)
    if proc.returncode != 0:
        return None
    fields = proc.stdout.split()
    return fields[1:]


def _is_ancestor(repo, ancestor, descendant):
    """True/False ancestry verdict; None when the plumbing exits otherwise."""
    proc = _git(repo, "merge-base", "--is-ancestor", ancestor, descendant)
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def cmd_pre_swap(args):
    repo = args.repo
    new = _resolve_commit(repo, args.new_commit)
    if new is None:
        print("refuse: landing commit unresolvable: %s" % args.new_commit)
        return 1
    pre_tip = _resolve_commit(repo, args.pre_tip)
    if pre_tip is None:
        sys.stderr.write(
            "landing-parentage-gate tool failure: pre-landing tip unresolvable: %s\n"
            % args.pre_tip)
        return 2
    parents = _parents(repo, new)
    if parents is None:
        sys.stderr.write(
            "landing-parentage-gate tool failure: rev-list failed\n")
        return 2
    if not parents:
        print("refuse: landing commit is parentless")
        return 1
    if len(parents) > 1:
        print("refuse: landing commit has %d parents" % len(parents))
        return 1
    if parents[0] != pre_tip:
        print("refuse: landing commit parent %s does not equal pre-landing tip %s"
              % (parents[0], pre_tip))
        return 1
    print("ok: landing commit parentage verified")
    return 0


def cmd_post_landing(args):
    repo = args.repo
    pre_tip = _resolve_commit(repo, args.pre_tip)
    if pre_tip is None:
        sys.stderr.write(
            "landing-parentage-gate tool failure: pre-landing tip unresolvable: %s\n"
            % args.pre_tip)
        return 2
    default_ref = "refs/heads/" + args.default_ref
    proc = _git(repo, "rev-parse", "--verify", default_ref)
    if proc.returncode != 0:
        sys.stderr.write(
            "landing-parentage-gate tool failure: default ref unresolvable: %s\n"
            % default_ref)
        return 2
    refused = False
    tip_leg = _is_ancestor(repo, pre_tip, default_ref)
    if tip_leg is None:
        sys.stderr.write(
            "landing-parentage-gate tool failure: merge-base plumbing failed\n")
        return 2
    if not tip_leg:
        print("refuse: default branch no longer descends from pre-landing tip")
        refused = True
    origin_note = None
    origin_refusal = False
    if args.origin_ref:
        origin = _resolve_commit(repo, args.origin_ref)
        if origin is None:
            origin_note = (
                "note: origin ref %s absent; ancestry leg skipped" % args.origin_ref)
        else:
            origin_leg = _is_ancestor(repo, origin, default_ref)
            if origin_leg is None:
                sys.stderr.write(
                    "landing-parentage-gate tool failure: merge-base plumbing failed\n")
                return 2
            if not origin_leg:
                print("refuse: default branch no longer descends from %s"
                      % args.origin_ref)
                origin_refusal = True
    if origin_note:
        print(origin_note)
    if refused or origin_refusal:
        return 1
    print("ok: default branch ancestry verified")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(
        prog="landing_parentage_gate.py",
        description="Refuse landings that sever the default branch history.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("pre-swap")
    pre.add_argument("--repo", required=True)
    pre.add_argument("--pre-tip", required=True)
    pre.add_argument("--new-commit", required=True)
    pre.set_defaults(func=cmd_pre_swap)

    post = sub.add_parser("post-landing")
    post.add_argument("--repo", required=True)
    post.add_argument("--pre-tip", required=True)
    post.add_argument("--default-ref", required=True)
    post.add_argument("--origin-ref", default=None)
    post.set_defaults(func=cmd_post_landing)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
