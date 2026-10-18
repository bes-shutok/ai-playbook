#!/usr/bin/env python3
"""Staged-scope guard: refuse an explicitly path-scoped commit whose staged
set carries unrelated entries.

The witnessed failure (backlog row docs/history/backlog/2026-10-05-explicit-add-commit-includes-prestaged-deletion.md,
commit 7b8d1bff): a commit made for one declared path silently committed the
whole staged set, including a pre-staged deletion of an unrelated tracked
file. This guard runs BEFORE an explicitly path-scoped commit, compares the
declared set against the staged set, and refuses naming every unrelated
staged entry with its state. It mutates nothing (read-only over the index
and HEAD) and offers no bypass: the remedy for a flagged entry is to unstage
it, or to widen the declared set deliberately, or to make the commit an
explicit pathspec commit covering exactly the declared set.

Parse grammar: `git diff --cached --name-status -z HEAD` reports a state
token then path records, NUL-delimited; a rename/copy state (R/C) consumes
TWO path records in origin-first order (`state\\0origin\\0destination\\0`).
Membership is symmetric: an entry is related when ANY of its consumed path
records is in the declared set, so a rename with the origin inside the
declared set passes even when the destination is not; the refusal names one
line per unrelated staged entry (path plus state), the unrelated sides
only, with the origin before the destination.

Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 with the final
`OUTCOME: pass` line (the pass receipt names the compared staged-entry
count); exit 1 with `OUTCOME: fail` names the unrelated entries; exit 2 with
`OUTCOME: indeterminate` is a git plumbing failure over already-resolved
inputs or a partially parsed name-status stream; exit 3 with `OUTCOME:
tool_error` is a usage violation (a missing `--include` among them), an
unresolvable repository, or an unresolvable HEAD (an input never resolved
is never a plumbing failure). Usage errors exit through the overridden
argparse error hook, so every run ends with exactly one final `OUTCOME:`
line; `--help` stays a metadata exit.
"""

import argparse
import subprocess
import sys

MULTI_PATH_STATES = ("R", "C")

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


class MalformedStagedSet(Exception):
    """A truncated or otherwise unparseable name-status stream (the
    indeterminate class: partially parsed evidence, never a refusal)."""


class ContractParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"staged-scope-guard: usage violation: {message}")
        print("OUTCOME: tool_error")
        raise SystemExit(3)


def _run_git(repo, args):
    return subprocess.run(
        ["git", "-C", repo] + args, capture_output=True, text=True
    )


def parse_staged_set(raw):
    """Parse the NUL-delimited name-status stream into entries.

    Returns a list of (state, [paths...]) tuples in report order; a rename
    or copy state consumes two path records, origin first. A truncated
    stream raises MalformedStagedSet: partially parsed evidence is the
    indeterminate class, never a refusal.
    """
    tokens = raw.split("\0")
    entries = []
    i = 0
    while i < len(tokens):
        state = tokens[i]
        if not state:
            break
        i += 1
        paths = []
        for _ in range(2 if state[0] in MULTI_PATH_STATES else 1):
            # An empty token where a path record belongs is a truncated
            # stream: git never reports an empty path.
            if i >= len(tokens) or not tokens[i]:
                raise MalformedStagedSet(
                    "truncated name-status record for state %r" % state)
            paths.append(tokens[i])
            i += 1
        entries.append((state, paths))
    return entries


def run_guard(args):
    if not args.include:
        print("staged-scope-guard: no --include declared: a scope check without a declared set is a usage violation")
        print("OUTCOME: tool_error")
        return 3

    probe = _run_git(args.repo, ["rev-parse", "--show-toplevel"])
    if probe.returncode != 0:
        print(f"staged-scope-guard: cannot resolve a git repository at {args.repo!r}: {probe.stderr.strip()}")
        print("OUTCOME: tool_error")
        return 3

    head = _run_git(args.repo, ["rev-parse", "--verify", "HEAD^{commit}"])
    if head.returncode != 0:
        print(f"staged-scope-guard: HEAD unresolvable in {args.repo!r}: {head.stderr.strip()}")
        print("OUTCOME: tool_error")
        return 3

    diff = _run_git(args.repo, ["diff", "--cached", "--name-status", "-z", "HEAD"])
    if diff.returncode != 0:
        print(f"staged-scope-guard: git plumbing failure reading the staged set: {diff.stderr.strip()}")
        print("OUTCOME: indeterminate")
        return 2

    try:
        entries = parse_staged_set(diff.stdout)
    except MalformedStagedSet as exc:
        print(f"staged-scope-guard: partially parsed staged set: {exc}")
        print("OUTCOME: indeterminate")
        return 2

    declared = set(args.include)
    unrelated = [
        (state, [p for p in paths if p not in declared])
        for state, paths in entries
        if not any(p in declared for p in paths)
    ]

    if unrelated:
        print("staged-scope-guard: refusal: the staged set carries entries outside the declared set:")
        for state, paths in unrelated:
            print(f"  refuse: {state} {' -> '.join(paths)}")
        print(
            "staged-scope-guard: unstage the unrelated entries, widen the declared set deliberately, "
            "or make the commit an explicit pathspec commit covering exactly the declared set; "
            "record the disposition in the session notes"
        )
        print("OUTCOME: fail")
        return 1

    print(f"staged-scope-guard: pass: compared {len(entries)} staged entries against {len(declared)} declared paths, no unrelated entries")
    print("OUTCOME: pass")
    return 0


def main(argv=None):
    parser = OutcomeArgumentParser(
        description="Refuse a path-scoped commit whose staged set carries unrelated entries."
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="a declared path of the commit; repeat for each declared path",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="repository to inspect (default: the current directory's repo)",
    )
    args = parser.parse_args(argv)
    try:
        return run_guard(args)
    except Exception as exc:  # safety net: every run ends with one OUTCOME line
        print(f"staged-scope-guard: unexpected failure: {exc}")
        print("OUTCOME: %s" % OUTCOME_LABELS[3])
        return 3


if __name__ == "__main__":
    sys.exit(main())
