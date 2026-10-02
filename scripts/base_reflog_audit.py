#!/usr/bin/env python3
"""Base-branch reflog audit: name backward ref moves and empty landing receipts.

Witnessed shape (the 2026-10-03 overnight landing window on this
repository's main): the base branch moved forward and then BACKWARD between
two landing sessions of one plan, and the rollback-then-re-land left a
message-bearing landing tip carrying an empty first-parent diff. A backward
move that happens outside any sanctioned landing tail is visible only in
the reflog, and a landing commit that carries nothing is visible only in a
first-parent receipt sweep.

Two subcommands over one base branch:

  reflog-window --repo ROOT --base-branch NAME --since-sha SHA
                [--max-entries N]
      Read the branch's reflog values newest first (v0..vk) via
      `git reflog show refs/heads/<NAME> --format=%H` and audit the
      consecutive pairs (v(i+1) -> v(i)) with
      `git merge-base --is-ancestor v(i+1) v(i)`; each failing pair is one
      `backward-move: <v(i+1)> -> <v(i)>` row. The walk stops after
      auditing the first pair whose newer value v(i) equals the anchor
      (the move that created the anchor is itself audited); when no pair's
      newer value equals the anchor, the anchor is reached at the window's
      oldest entry, whose (last audited) pair carries it as the older
      value. If neither form is met within --max-entries, the walked depth
      is named and the run is indeterminate.
  landed-receipt --repo ROOT --base-branch NAME [--max-commits N]
      Walk `git log --first-parent --format=%H%x00%s -n <N>
      refs/heads/<NAME>`; a commit whose subject matches the
      landing-phrased family `^[A-Za-z0-9-]+: (land|archive) ` is checked
      with `git diff --quiet <sha>^ <sha>`, and an empty diff is one row
      `empty-receipt: <sha> <subject> (repair: a corrective commit naming
      the content-bearing sha, never an amend)`. A landing-phrased ROOT
      commit inside the window has no parent to diff against; it is named
      and the run is indeterminate (a plain non-landing root at the end of
      the walked history is just the end of the walk, not a finding).

Exit codes (outcome contract; conformant at birth): 0 pass, 1 fail (one or
more modeled rows), 2 indeterminate (the anchor was not reached within the
window, a landing-phrased root commit inside the window, or the git
plumbing answered outside its answer vocabulary over resolved values; when
rows and uncertainty occur in one run, every row stays named and
uncertainty dominates), 3 tool error (an unresolvable input, a usage
error, or an unheld operating-context assumption). Evidence rows print
first; every non-metadata run ends with exactly one final `OUTCOME:` line;
`--help` and usage metadata exits emit no `OUTCOME:` line.
"""

import argparse
import re
import subprocess
import sys

OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}

LANDING_PHRASED = re.compile(r"^[A-Za-z0-9-]+: (land|archive) ")


class OutcomeArgumentParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit 3 (tool error) with a final
    `OUTCOME: tool_error` line on stdout, overriding argparse's default
    exit 2; `--help` stays a metadata exit without an `OUTCOME:` line."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        print("OUTCOME: %s" % OUTCOME_LABELS[3])
        raise SystemExit(3)


def _git(repo, *args):
    """Run git plumbing in ROOT; returns a CompletedProcess with bytes
    output (decoding is per call site, so a non-decodable subject is a
    classified tool error rather than a crash)."""
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def _stderr_note(stderr_bytes):
    """First stderr line as an evidence suffix, or the empty string."""
    text = stderr_bytes.decode("utf-8", "replace").strip()
    if not text:
        return ""
    return "; git stderr: %s" % text.splitlines()[0]


def _resolve_commit(repo, value):
    """Resolve VALUE as a commit; returns the full sha or None."""
    proc = _git(repo, "rev-parse", "--verify", value + "^{commit}")
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("ascii", "replace").strip()


def _tool_error(message):
    sys.stderr.write("base-reflog-audit tool error: %s\n" % message)
    return 3


def cmd_reflog_window(args):
    repo = args.repo
    anchor = _resolve_commit(repo, args.since_sha)
    if anchor is None:
        return _tool_error("since-sha unresolvable: %s" % args.since_sha)
    ref = "refs/heads/" + args.base_branch
    proc = _git(repo, "reflog", "show", ref, "--format=%H",
                "-n", str(args.max_entries))
    if proc.returncode != 0:
        return _tool_error("base branch reflog unresolvable: %s%s"
                           % (ref, _stderr_note(proc.stderr)))
    try:
        values = [line.strip().decode("ascii")
                  for line in proc.stdout.splitlines() if line.strip()]
    except UnicodeDecodeError:
        return _tool_error("reflog output not decodable as text: %s" % ref)
    if not values:
        return _tool_error(
            "reflog for %s carries no entries; the operating-context "
            "assumption requires at least one entry" % ref)
    rows = []
    audited = 0
    stopped = False
    plumbing_failure = None
    for i in range(len(values) - 1):
        newer, older = values[i], values[i + 1]
        verdict = _git(repo, "merge-base", "--is-ancestor", older, newer)
        audited += 1
        if verdict.returncode == 0:
            pass
        elif verdict.returncode == 1:
            rows.append("backward-move: %s -> %s" % (older, newer))
        else:
            plumbing_failure = (older, newer, verdict.returncode,
                                _stderr_note(verdict.stderr))
            break
        if newer == anchor:
            stopped = True
            break
    for row in rows:
        print(row)
    if plumbing_failure is not None:
        older, newer, code, note = plumbing_failure
        print("indeterminate: merge-base --is-ancestor failed (exit %d) "
              "over resolved values %s and %s%s; whether the step is a "
              "backward move could not be determined"
              % (code, older, newer, note))
        return 2
    reached = stopped or values[-1] == anchor
    if not reached:
        print("indeterminate: anchor %s not reached within the walked "
              "reflog window (read %d entries, audited %d pairs, "
              "--max-entries %d); re-derive with a larger window or verify "
              "the anchor value"
              % (anchor, len(values), audited, args.max_entries))
        return 2
    if rows:
        return 1
    print("ok: no backward move in the audited reflog window "
          "(%d pairs audited, anchor %s)" % (audited, anchor))
    return 0


def cmd_landed_receipt(args):
    repo = args.repo
    ref = "refs/heads/" + args.base_branch
    proc = _git(repo, "log", "--first-parent", "--format=%H%x00%s",
                "-n", str(args.max_commits), ref)
    if proc.returncode != 0:
        return _tool_error("base branch log unresolvable: %s%s"
                           % (ref, _stderr_note(proc.stderr)))
    entries = []
    for line in proc.stdout.split(b"\n"):
        if not line:
            continue
        sha_bytes, sep, subject_bytes = line.partition(b"\x00")
        if not sep:
            return _tool_error(
                "unexpected git log output line (missing NUL separator): %s"
                % line.decode("ascii", "replace"))
        try:
            entries.append((sha_bytes.decode("ascii"),
                            subject_bytes.decode("utf-8")))
        except UnicodeDecodeError:
            return _tool_error(
                "commit subject not decodable as text: %s"
                % sha_bytes.decode("ascii", "replace"))
    if not entries:
        return _tool_error("no commits walked for %s; the base branch "
                           "carries no history" % ref)
    rows = []
    root_commit = None
    plumbing_failure = None
    for sha, subject in entries:
        if not LANDING_PHRASED.match(subject):
            continue
        parents = _git(repo, "rev-list", "--parents", "-n", "1", sha)
        if parents.returncode != 0:
            plumbing_failure = ("rev-list --parents", sha,
                                parents.returncode,
                                _stderr_note(parents.stderr))
            break
        if len(parents.stdout.split()) < 2:
            root_commit = (sha, subject)
            continue
        diff = _git(repo, "diff", "--quiet", sha + "^", sha)
        if diff.returncode == 0:
            rows.append(
                "empty-receipt: %s %s (repair: a corrective commit naming "
                "the content-bearing sha, never an amend)" % (sha, subject))
        elif diff.returncode != 1:
            plumbing_failure = ("git diff --quiet", sha, diff.returncode,
                                _stderr_note(diff.stderr))
            break
    for row in rows:
        print(row)
    if plumbing_failure is not None:
        operation, sha, code, note = plumbing_failure
        print("indeterminate: %s failed (exit %d) over resolved commit %s%s; "
              "whether the landing-phrased commit carries an empty receipt "
              "could not be determined" % (operation, code, sha, note))
        return 2
    if root_commit is not None:
        sha, subject = root_commit
        print('indeterminate: landing-phrased root commit %s ("%s") inside '
              "the walked window; a root commit has no parent, so its "
              "receipt could not be determined" % (sha, subject))
        return 2
    if rows:
        return 1
    print("ok: no landing-phrased commit with an empty first-parent diff "
          "in the walked window (%d commits walked)" % len(entries))
    return 0


def main(argv):
    parser = OutcomeArgumentParser(
        prog="base_reflog_audit.py",
        description="Audit the base branch's reflog window and landing "
                    "receipts under the script outcome contract.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    window = sub.add_parser(
        "reflog-window",
        help="audit the base reflog window for backward moves",
    )
    window.add_argument("--repo", required=True)
    window.add_argument("--base-branch", required=True)
    window.add_argument("--since-sha", required=True)
    window.add_argument("--max-entries", type=int, default=200)
    window.set_defaults(func=cmd_reflog_window)

    receipt = sub.add_parser(
        "landed-receipt",
        help="sweep the base branch's first-parent history for empty "
             "landing receipts",
    )
    receipt.add_argument("--repo", required=True)
    receipt.add_argument("--base-branch", required=True)
    receipt.add_argument("--max-commits", type=int, default=100)
    receipt.set_defaults(func=cmd_landed_receipt)

    args = parser.parse_args(argv)
    code = args.func(args)
    print("OUTCOME: %s" % OUTCOME_LABELS[code])
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
