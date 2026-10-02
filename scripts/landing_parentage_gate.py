#!/usr/bin/env python3
"""Landing parentage gate: refuse landings that sever the default branch's history.

Witnessed defect (2026-09-27): a squash landing moved main to a parentless
commit carrying the full repository tree, severing 391 commits from main.

Two subcommands over one parentage/ancestry core:

  pre-swap --repo ROOT --pre-tip SHA --new-commit SHA
      [--source-branch BRANCH] [--expected-base SHA]
      Before a ref swap or as the commit-time check: the landing commit must
      have exactly one parent, that parent must equal PRE-TIP, and the
      commit's tree must differ from its parent's tree (a tree-identical
      landing commit is an empty-diff landing tip and is refused). The two
      optional legs are additive opt-ins. With --source-branch: the branch
      tip must contain PRE-TIP (swap-time containment; a refusal names the
      fork-point merge base and the fork-point delta paths, the paths the
      pre-landing tip gained since the fork that the branch lacks). With
      --expected-base (which requires --source-branch): the value must equal
      the computed merge base of PRE-TIP and the branch tip (the base pin; a
      mismatch names both values). A provided --source-branch or
      --expected-base value that does not resolve is a tool error.
  post-landing --repo ROOT --pre-tip SHA --default-ref NAME [--origin-ref REF]
      After a landing: the default branch must still descend from PRE-TIP
      (evaluated and reported first) and, when --origin-ref resolves, from
      that ref too; a non-resolving origin ref is a named skip, not a refusal.

Exit codes (outcome contract): 0 pass, 1 fail (a modeled refusal), 2
indeterminate (the git plumbing answered outside its 0/1 answer vocabulary
over resolved revs, so parentage could not be determined), 3 tool error (an
unresolvable input, a usage error, or an unheld environment assumption).
Every non-metadata run ends with exactly one final `OUTCOME:` line after the
human-readable evidence; `--help` and usage metadata exits emit no `OUTCOME:`
line.
"""

import argparse
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
    """Git plumbing answered outside its 0/1 answer vocabulary over
    resolved revs (the indeterminate class, never a modeled refusal)."""

    def __init__(self, operation, returncode, stderr_text=""):
        super().__init__(operation)
        self.operation = operation
        self.returncode = returncode
        self.stderr_text = (stderr_text or "").strip()


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
    """Parent list of COMMIT via rev-list --parents; raises PlumbingFailure
    when the plumbing exits outside the 0/1 answer vocabulary."""
    proc = _git(repo, "rev-list", "--parents", "-n", "1", commit)
    if proc.returncode != 0:
        raise PlumbingFailure(
            "rev-list --parents", proc.returncode, proc.stderr)
    fields = proc.stdout.split()
    return fields[1:]


def _is_ancestor(repo, ancestor, descendant):
    """True/False ancestry verdict; raises PlumbingFailure when the plumbing
    exits outside the 0/1 answer vocabulary."""
    proc = _git(repo, "merge-base", "--is-ancestor", ancestor, descendant)
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    raise PlumbingFailure(
        "merge-base --is-ancestor", proc.returncode, proc.stderr)


def _merge_base(repo, left, right):
    """Merge base sha of two resolved commits; raises PlumbingFailure when
    the plumbing exits outside its answer vocabulary (including the
    unrelated-histories answer, which leaves no fork point to name)."""
    proc = _git(repo, "merge-base", left, right)
    if proc.returncode != 0:
        raise PlumbingFailure("merge-base", proc.returncode, proc.stderr)
    sha = proc.stdout.strip()
    if not sha:
        raise PlumbingFailure(
            "merge-base", proc.returncode, "empty merge-base output")
    return sha


def _diff_paths(repo, left, right):
    """Path list changed between two resolved commits; raises
    PlumbingFailure when the diff plumbing fails over them."""
    proc = _git(repo, "diff", "--name-only", left, right)
    if proc.returncode != 0:
        raise PlumbingFailure(
            "git diff --name-only", proc.returncode, proc.stderr)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _plumbing_detail(exc, observed, undetermined):
    """Observed/could-not-determine evidence line for a plumbing failure."""
    stderr_note = ""
    if exc.stderr_text:
        stderr_note = "; git stderr: %s" % exc.stderr_text.splitlines()[0]
    return (
        "%s failed (exit %d) over resolved %s; observed: the plumbing "
        "answered outside the 0/1 answer vocabulary%s; %s could not be "
        "determined" % (exc.operation, exc.returncode, observed,
                        stderr_note, undetermined))


def _tool_error(message):
    sys.stderr.write("landing-parentage-gate tool error: %s\n" % message)
    return 3


def _indeterminate(message):
    sys.stderr.write("landing-parentage-gate indeterminate: %s\n" % message)
    return 2


def cmd_pre_swap(args):
    repo = args.repo
    if args.expected_base is not None and args.source_branch is None:
        return _tool_error(
            "--expected-base requires its companion --source-branch "
            "(the missing companion argument)")
    new = _resolve_commit(repo, args.new_commit)
    if new is None:
        print("refuse: landing commit unresolvable: %s" % args.new_commit)
        return 1
    pre_tip = _resolve_commit(repo, args.pre_tip)
    if pre_tip is None:
        return _tool_error("pre-landing tip unresolvable: %s" % args.pre_tip)
    source_tip = None
    expected_base = None
    if args.source_branch is not None:
        source_tip = _resolve_commit(repo, args.source_branch)
        if source_tip is None:
            return _tool_error(
                "source branch unresolvable: %s" % args.source_branch)
    if args.expected_base is not None:
        expected_base = _resolve_commit(repo, args.expected_base)
        if expected_base is None:
            return _tool_error(
                "expected base unresolvable: %s" % args.expected_base)
    try:
        parents = _parents(repo, new)
    except PlumbingFailure as exc:
        return _indeterminate(_plumbing_detail(
            exc,
            "commits %s (landing) and %s (pre-landing tip)" % (new, pre_tip),
            "parentage"))
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
    try:
        diff = _git(repo, "diff", "--quiet", pre_tip, new)
        if diff.returncode not in (0, 1):
            raise PlumbingFailure(
                "git diff --quiet", diff.returncode, diff.stderr)
    except PlumbingFailure as exc:
        return _indeterminate(_plumbing_detail(
            exc,
            "commits %s (landing) and %s (pre-landing tip)" % (new, pre_tip),
            "tree equality"))
    if diff.returncode == 0:
        print("refuse: landing commit %s is tree-identical to its parent %s"
              " (empty-diff landing tip)" % (new, pre_tip))
        return 1
    if source_tip is not None:
        try:
            contained = _is_ancestor(repo, pre_tip, source_tip)
        except PlumbingFailure as exc:
            return _indeterminate(_plumbing_detail(
                exc,
                "commits %s (pre-landing tip) and %s (source branch tip)"
                % (pre_tip, source_tip),
                "source-branch containment"))
        if not contained:
            try:
                fork_base = _merge_base(repo, pre_tip, source_tip)
                delta = _diff_paths(repo, fork_base, pre_tip)
            except PlumbingFailure as exc:
                return _indeterminate(_plumbing_detail(
                    exc,
                    "commits %s (pre-landing tip) and %s (source branch tip)"
                    % (pre_tip, source_tip),
                    "the fork point"))
            print("refuse: source branch %s does not contain the pre-landing"
                  " tip %s (swap-time containment broken)"
                  % (args.source_branch, pre_tip))
            print("  fork-point merge base: %s" % fork_base)
            print("  fork-point delta paths (the paths the pre-landing tip"
                  " gained since the fork that the branch lacks):")
            if delta:
                for path in delta:
                    print("    %s" % path)
            else:
                print("    (none)")
            return 1
        print("ok: source branch containment verified (%s contains %s)"
              % (args.source_branch, pre_tip))
        if expected_base is not None:
            try:
                computed = _merge_base(repo, pre_tip, source_tip)
            except PlumbingFailure as exc:
                return _indeterminate(_plumbing_detail(
                    exc,
                    "commits %s (pre-landing tip) and %s (source branch tip)"
                    % (pre_tip, source_tip),
                    "the merge base"))
            if computed != expected_base:
                print("refuse: base pin mismatch: expected base %s does not"
                      " equal the computed merge base %s (a silent rebase"
                      " under a stale record)" % (expected_base, computed))
                return 1
            print("ok: base pin verified (expected base %s equals the"
                  " computed merge base)" % expected_base)
    print("ok: landing commit parentage verified")
    return 0


def cmd_post_landing(args):
    repo = args.repo
    pre_tip = _resolve_commit(repo, args.pre_tip)
    if pre_tip is None:
        return _tool_error("pre-landing tip unresolvable: %s" % args.pre_tip)
    default_ref = "refs/heads/" + args.default_ref
    proc = _git(repo, "rev-parse", "--verify", default_ref)
    if proc.returncode != 0:
        return _tool_error("default ref unresolvable: %s" % default_ref)
    refused = False
    try:
        tip_leg = _is_ancestor(repo, pre_tip, default_ref)
    except PlumbingFailure as exc:
        return _indeterminate(_plumbing_detail(
            exc,
            "refs %s (pre-landing tip) and %s (default branch)" % (
                pre_tip, default_ref),
            "default-branch ancestry"))
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
            try:
                origin_leg = _is_ancestor(repo, origin, default_ref)
            except PlumbingFailure as exc:
                return _indeterminate(_plumbing_detail(
                    exc,
                    "refs %s (origin) and %s (default branch)" % (
                        origin, default_ref),
                    "origin ancestry"))
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
    parser = OutcomeArgumentParser(
        prog="landing_parentage_gate.py",
        description="Refuse landings that sever the default branch history.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    resolve_note = (
        "values are resolved via `git rev-parse` at the moment of use; "
        "refs (branch names, HEAD, relative forms) are accepted and "
        "preferred over literal digests"
    )

    pre = sub.add_parser("pre-swap")
    pre.add_argument("--repo", required=True)
    pre.add_argument("--pre-tip", required=True, help=resolve_note)
    pre.add_argument("--new-commit", required=True, help=resolve_note)
    pre.add_argument(
        "--source-branch", default=None,
        help="optional swap-time containment leg: the branch tip must"
             " contain the pre-landing tip (an unresolvable ref is a tool"
             " error)")
    pre.add_argument(
        "--expected-base", default=None,
        help="optional base pin: must equal the computed merge base of the"
             " pre-landing tip and the source branch tip; requires"
             " --source-branch (an unresolvable ref is a tool error)")
    pre.set_defaults(func=cmd_pre_swap)

    post = sub.add_parser("post-landing")
    post.add_argument("--repo", required=True)
    post.add_argument("--pre-tip", required=True, help=resolve_note)
    post.add_argument("--default-ref", required=True, help=resolve_note)
    post.add_argument("--origin-ref", default=None)
    post.set_defaults(func=cmd_post_landing)

    args = parser.parse_args(argv)
    code = args.func(args)
    print("OUTCOME: %s" % OUTCOME_LABELS[code])
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
