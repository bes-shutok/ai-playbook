#!/usr/bin/env python3
"""Revert-set classifier: read-only by contract classification of a dirty checkout.

Contract (the primary revert-set adjudication plan): the ``classify``
sub-command enumerates the dirty path set from ``git status --porcelain=v1
-z``, computes each path's effective dirty state (index blob when the index
entry differs from HEAD, else worktree bytes; absence for deletions), and
compares it against ancestor vintages (blobs the path carried at any commit
reachable from HEAD). A dirty state equal to an ancestor vintage is reversal
damage; anything else is foreign. Read-only by contract: it classifies and
prints, and never stages, restores, or writes.

Exit codes (scripts/OUTCOME_CONTRACT.md, the answer-vocabulary criterion):
0 pass when no path classified reversal, 1 fail when any path did (the
summary line distinguishes pure from partial), 2 indeterminate when a git
plumbing call answered outside its 0/1 vocabulary over already-resolved
inputs, 3 tool error when an input never resolved (a bad ``--repo``, an
unresolvable ``--head`` ref) or the invocation violates usage (argparse
overridden to exit 3). Every non-metadata run ends with exactly one final
``OUTCOME:`` line on stdout after the row evidence; ``--help`` is a
metadata exit with no ``OUTCOME:`` line. The legacy
``revert-set-classifier tool failure:`` stderr prefix retires with the
vocabulary migration.
"""

import argparse
import subprocess
import sys

# Outcome contract (scripts/OUTCOME_CONTRACT.md): the four outcomes and the
# argparse override. A usage violation exits 3 with a final `OUTCOME:
# tool_error` line on stderr before exit (the usage text and the error
# message share that stream); every other run's final line is on stdout
# after the row evidence.
OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}


class OutcomeArgumentParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit 3 (tool error) with a final
    `OUTCOME: tool_error` line on stderr before exit, overriding argparse's
    default exit 2; `--help` stays a metadata exit without an `OUTCOME:`
    line."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        sys.stderr.write("OUTCOME: %s\n" % OUTCOME_LABELS[3])
        raise SystemExit(3)


def emit_outcome(code):
    print("OUTCOME: %s" % OUTCOME_LABELS[code])


def indeterminate(message):
    """A git plumbing failure over already-resolved inputs: the call
    answered outside its 0/1 vocabulary, so what happened to the tree
    cannot be determined (exit 2, never a reversal finding)."""
    sys.stderr.write("revert-set-classifier: %s\n" % message)
    emit_outcome(2)
    return 2


def tool_error(message):
    """An input that never resolved (repo, ref): the classifier cannot
    even address the question (exit 3, tool error)."""
    sys.stderr.write("revert-set-classifier: %s\n" % message)
    emit_outcome(3)
    return 3


def git(repo, *args, check=True):
    proc = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, check=False,
    )
    if check and proc.returncode != 0:
        return None
    return proc


def resolve_head(repo, ref):
    proc = git(repo, "rev-parse", "--verify", "%s^{commit}" % ref)
    if proc is None or proc.returncode != 0:
        return None
    return proc.stdout.strip()


def parse_porcelain(repo):
    """Every record with a non-space, non-? status, plus untracked records,
    from NUL-separated porcelain v1 (never C-quoted). Returns (paths,
    untracked) where paths is the ordered unique path list (a path printed
    by more than one record appears once) and untracked the "??"-record
    subset."""
    proc = git(repo, "status", "--porcelain=v1", "-z")
    if proc is None:
        return None
    records = proc.stdout.split("\0")
    paths = []
    untracked = set()
    i = 0
    while i < len(records):
        rec = records[i]
        i += 1
        if not rec:
            continue
        status, path = rec[:2], rec[3:]
        if status == "??" or (status[0] != " " and status[0] != "?") or (
            status[1] != " " and status[1] != "?"
        ):
            if status == "??":
                untracked.add(path)
            if path not in paths:
                paths.append(path)
        if status[0] in ("R", "C") and i < len(records):
            # The next NUL record is this rename's old path, consumed here
            # as data; the walk must never re-parse it as a status record.
            old = records[i]
            i += 1
            if old and old not in paths:
                paths.append(old)
    return paths, untracked


def head_state(repo, path):
    """(present, blob) for the path at HEAD (NUL-separated, never C-quoted)."""
    proc = git(repo, "ls-tree", "-z", "HEAD", "--", path)
    if proc is None:
        return None
    for rec in proc.stdout.split("\0"):
        if not rec:
            continue
        meta = rec.split(None, 3)
        if len(meta) >= 3 and meta[1] == "blob":
            return True, meta[2]
    return False, None


def effective_state(repo, path):
    """(present, blob, from_index) for the path's effective dirty state."""
    proc = git(repo, "status", "--porcelain=v1", "-z", "--", path)
    if proc is None:
        return None
    rec = proc.stdout.split("\0")[0]
    if not rec:
        return False, None, False
    status = rec[:2]
    if status[0] not in (" ", "?"):
        ls = git(repo, "ls-files", "-s", "-z", "--", path)
        if ls is None:
            return None
        # NUL-separated ls-files records: <mode> <blob> <stage>\0<path>;
        # never C-quoted, so non-ASCII and special-character paths match.
        for rec in ls.stdout.split("\0"):
            if not rec:
                continue
            meta = rec.split()
            if meta:
                return True, meta[1], True
        return False, None, True
    if status[1] == "D":
        return False, None, False
    ho = git(repo, "hash-object", path)
    if ho is None or ho.returncode != 0:
        return None
    return True, ho.stdout.strip(), False


def addition_commit(repo, path):
    """The path's addition commit, or the empty string when no reachable
    commit adds the path."""
    proc = git(repo, "log", "--diff-filter=A", "--format=%H", "--", path)
    if proc is None:
        return None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def vintage_match(repo, path, blob):
    """First commit reachable from HEAD whose blob for path equals blob
    (the freshness gate's walk, skipping commits where the path is absent).
    Returns the commit id, or the empty string when no vintage matches."""
    proc = git(repo, "log", "--format=%H", "--", path)
    if proc is None:
        return None
    for line in proc.stdout.splitlines():
        c = line.strip()
        if not c:
            continue
        lt = git(repo, "ls-tree", c, "--", path)
        if lt is None:
            return None
        for entry in lt.stdout.splitlines():
            meta = entry.split(None, 3)
            if len(meta) >= 3 and meta[1] == "blob" and meta[2] == blob:
                return c
    return ""


def classify(repo, head, restrict=None):
    parsed = parse_porcelain(repo)
    if parsed is None:
        return indeterminate("status porcelain unresolvable")
    paths, untracked = parsed
    dirty = set(paths)
    if restrict:
        paths = [p for p in paths if p in restrict]
        for p in sorted(restrict):
            if p not in paths:
                paths.append(p)
    rows = []
    reversal = 0
    foreign = 0
    for path in paths:
        if path not in dirty:
            h = head_state(repo, path)
            if h is None:
                return indeterminate("ls-tree failed for %s" % path)
            if h[0] is False:
                # A restricted named path absent from both HEAD and disk:
                # the queried deletion matches no reachable addition.
                rows.append("foreign: %s deletion matches no reachable "
                            "addition" % path)
                foreign += 1
            else:
                rows.append("clean: %s" % path)
            continue
        h = head_state(repo, path)
        if h is None:
            return indeterminate("ls-tree failed for %s" % path)
        e = effective_state(repo, path)
        if e is None:
            return indeterminate("effective state failed for %s" % path)
        present, blob, _ = e
        if present == h[0] and blob == h[1]:
            rows.append("clean: %s" % path)
            continue
        if not present:
            add = addition_commit(repo, path)
            if add is None:
                return indeterminate("addition lookup failed for %s" % path)
            if add:
                rows.append("reversal: %s deletion reverts the addition at %s"
                            % (path, add))
                reversal += 1
            else:
                rows.append("foreign: %s deletion matches no reachable addition"
                            % path)
                foreign += 1
            continue
        if h[0] is False:
            if path in untracked:
                rows.append("foreign: %s untracked (never reversal damage)"
                            % path)
                foreign += 1
                continue
            v = vintage_match(repo, path, blob)
            if v is None:
                return indeterminate("vintage walk failed for %s" % path)
            rows.append("foreign: %s dirty state matches no ancestor vintage"
                        % path)
            foreign += 1
            continue
        v = vintage_match(repo, path, blob)
        if v is None:
            return indeterminate("vintage walk failed for %s" % path)
        if v:
            rows.append("reversal: %s dirty state equals ancestor %s vintage "
                        "(HEAD: %s)" % (path, v, head))
            reversal += 1
        else:
            rows.append("foreign: %s dirty state matches no ancestor vintage"
                        % path)
            foreign += 1
    # The summary scopes to the actual dirty set: restricted named paths
    # that are clean, or queried foreign rows for absent-everywhere paths,
    # never flip the summary away from the dirty set's own classification.
    if not dirty:
        rows.append("revert-set: none")
    elif reversal and not foreign:
        rows.append("revert-set: pure")
    elif foreign:
        rows.append("revert-set: partial")
    for row in rows:
        print(row)
    return 1 if reversal else 0


def main(argv):
    parser = OutcomeArgumentParser(prog="revert_set_classifier.py")
    sub = parser.add_subparsers(dest="command")
    cl = sub.add_parser("classify")
    cl.add_argument("--repo", required=True)
    cl.add_argument("--head", default="HEAD")
    cl.add_argument("--path", action="append", default=[])
    args = parser.parse_args(argv)
    if args.command != "classify":
        parser.error("the classify sub-command is the only one")
    head = resolve_head(args.repo, args.head)
    if head is None:
        return tool_error("head unresolvable: %s" % args.head)
    rc = classify(args.repo, head, set(args.path) or None)
    if rc in (0, 1):
        # The verdict arms: the final OUTCOME line follows the row evidence
        # on stdout; the indeterminate and tool-error arms emit their own
        # line at their raise site.
        emit_outcome(rc)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
