#!/usr/bin/env python3
"""Reverse-squash guard: refuse staged or diffed change sets that invert landed content.

Two thin modes over one detection core, plus one commit-inspection mode:

  check-staged [--repo ROOT] [--ack SHA]
      Judge the index of ROOT (default: process cwd) against ROOT HEAD.
  check-diff --against REV --repo ROOT [--ack SHA] [FILE]
      Judge a git-format unified diff (FILE or stdin) against REV.
  check-commit --rev SHA --repo ROOT
      Inspect one commit: a parentless commit whose tree carries at least
      SNAPSHOT_RATIO of the repository's tracked files is the witnessed
      orphan-squash defect (2026-09-27: commit 351f704f) and is refused.

Exit codes: 0 clean, 1 refusal with named evidence, 2 tool failure.
  Stale-checkout adjudication: a refused or suspect entry whose blob equals the path's blob at an ancestor commit is a stale witness per the stale-checkout discriminator in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md; restore-and-record, never commit.
"""

import re
import subprocess
import sys

ARCHIVE_DIRS = ("docs/history/plans/completed/", "docs/history/backlog/completed/")
SNAPSHOT_RATIO = 0.5
MIRROR_SCAN_SINCE = "30.days"
MIRROR_SCAN_MAX_COMMITS = 2000
MIRROR_FLOOR = 2

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def fail2(message):
    sys.stderr.write("reverse-squash-guard tool failure: %s\n" % message)
    return 2


def unquote_path(path):
    """Undo git C-quoting for extended-header / numstat paths.

    Octal escapes are raw UTF-8 bytes, so the unquoted body is assembled as
    a byte string and decoded once at the end."""
    if not path.startswith('"'):
        return path
    body = path[1:-1] if path.endswith('"') else path[1:]
    out = bytearray()
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            simple = {"a": 7, "b": 8, "f": 12, "n": 10, "r": 13, "t": 9,
                      "v": 11, "\\": 92, '"': 34}
            if nxt in simple:
                out.append(simple[nxt])
                i += 2
                continue
            if nxt.isdigit():
                out.append(int(body[i + 1:i + 4], 8))
                i += 4
                continue
        out.extend(ch.encode("utf-8"))
        i += 1
    return out.decode("utf-8", "replace")


def run_git(args, what, input_bytes=None):
    try:
        proc = subprocess.run(args, input=input_bytes,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        raise ToolError("%s: %s" % (what, exc))
    if proc.returncode != 0:
        raise ToolError("%s: %s" % (what, proc.stderr.decode("utf-8", "replace").strip()))
    return proc.stdout


class ToolError(Exception):
    pass


def parse_numstat_z(stream):
    """Parse `--numstat -z` output into records.

    Returns a list of dicts: {path (new side), old (old side or None),
    added, deleted} where added/deleted are ints or None (binary).
    Verified grammars of `--numstat -z` output:
    - ordinary record: ``ins\\tdel\\tpath``
    - rename with edit: two per-side records (deletions on the old path,
      insertions on the new path)
    - pure rename (100% similarity): ``0\\t0\\t`` placeholder followed by the
      old path and the new path as separate NUL-terminated tokens (the
      check-diff producer via `git apply --numstat -z` carries only the new
      path for a pure rename).
    """
    tokens = stream.split(b"\0")
    records = []
    i = 0
    while i < len(tokens):
        token = tokens[i].decode("utf-8", "replace")
        if token.startswith("\n"):
            token = token[1:]
        i += 1
        if token == "":
            continue
        if "\t" not in token:
            raise ToolError("unparseable numstat record: %r" % token[:80])
        fields = token.split("\t")
        if len(fields) != 3:
            raise ToolError("unparseable numstat record: %r" % token[:80])
        added_s, deleted_s, path = fields
        rec = {"path": unquote_path(path), "old": None, "added": None, "deleted": None}
        if added_s != "-" and deleted_s != "-":
            try:
                rec["added"] = int(added_s)
                rec["deleted"] = int(deleted_s)
            except ValueError:
                raise ToolError("unparseable numstat counts: %r" % token[:80])
        if path == "":
            # Pure-rename placeholder: the next two tokens are old, new.
            if i + 1 >= len(tokens):
                raise ToolError("truncated pure-rename numstat record")
            rec["old"] = unquote_path(tokens[i].decode("utf-8", "replace"))
            rec["path"] = unquote_path(tokens[i + 1].decode("utf-8", "replace"))
            rec["added"] = 0
            rec["deleted"] = 0
            i += 2
        records.append(rec)
    return records


def parse_extended_headers(diff_text):
    """Recover rename pairs and whole-file deletions from git-format diff text."""
    renames = []
    deletions = []
    last_old = None
    last_new = None
    for line in diff_text.split("\n"):
        if line.startswith("diff --git "):
            m = re.match(r'^diff --git (?P<a>"(?:[^"\\]|\\.)*"|\S+) (?P<b>"(?:[^"\\]|\\.)*"|\S+)$', line)
            if m:
                last_old = unquote_path(m.group("a"))[2:]
                last_new = unquote_path(m.group("b"))[2:]
            continue
        m = re.match(r'^rename from (?P<p>.+)$', line)
        if m:
            pending = {"from": unquote_path(m.group("p")), "to": None}
            renames.append(pending)
            continue
        m = re.match(r'^rename to (?P<p>.+)$', line)
        if m and renames and renames[-1]["to"] is None:
            renames[-1]["to"] = unquote_path(m.group("p"))
            continue
        if line.startswith("deleted file mode") and last_old is not None:
            deletions.append(last_old)
    return renames, deletions


def is_archive(path):
    return any(path.startswith(prefix) for prefix in ARCHIVE_DIRS)


def egress_findings(numstat_records, diff_text):
    """Signature A: archive-dir egress. Never suppressible."""
    findings = []
    seen = set()

    def add(path):
        if path not in seen:
            seen.add(path)
            findings.append("archive-egress: %s" % path)

    renames, deletions = parse_extended_headers(diff_text)
    for old in deletions:
        if is_archive(old):
            add(old)
    for rec in numstat_records:
        if rec["old"] is not None and is_archive(rec["old"]) and not is_archive(rec["path"]):
            add(rec["old"])
    for pair in renames:
        if pair["to"] is not None and is_archive(pair["from"]) and not is_archive(pair["to"]):
            add(pair["from"])
    return findings


def parse_log_numstat_z(stream):
    """Parse batched `git log --format=%H --numstat -z` output into
    {commit_sha: {path_side: (added, deleted) or None}} keyed on both sides.
    Record grammar per parse_numstat_z; count records carry a leading
    newline in this producer."""
    landed = {}
    current = None
    tokens = stream.split(b"\0")
    i = 0
    while i < len(tokens):
        token = tokens[i].decode("utf-8", "replace")
        if token.startswith("\n"):
            token = token[1:]
        i += 1
        if token == "":
            continue
        if SHA_RE.match(token):
            current = token
            landed.setdefault(current, {})
            continue
        if current is None or "\t" not in token:
            continue
        fields = token.split("\t")
        if len(fields) != 3:
            continue
        added_s, deleted_s, path = fields
        counts = None
        if added_s != "-" and deleted_s != "-":
            try:
                counts = (int(added_s), int(deleted_s))
            except ValueError:
                counts = None
        if path == "" and counts == (0, 0) and i + 1 < len(tokens):
            # Pure-rename placeholder: next two tokens are old, new.
            oldp = unquote_path(tokens[i].decode("utf-8", "replace"))
            newp = unquote_path(tokens[i + 1].decode("utf-8", "replace"))
            landed[current][oldp] = (0, 0)
            landed[current][newp] = (0, 0)
            i += 2
            continue
        landed[current][unquote_path(path)] = counts
    return landed


def mirror_findings(staged_records, landed, ack_sha):
    """Signature B: diffstat mirror. Fires for commit C when at least two
    staged nonzero paths mirror C; padding and non-mirroring overlap
    tolerated; a single mirroring path alone never fires."""
    per_commit = {}
    for rec in staged_records:
        if rec["added"] is None or rec["deleted"] is None:
            continue
        if rec["added"] == 0 and rec["deleted"] == 0:
            continue
        staged_pair = (rec["added"], rec["deleted"])
        for side in (rec["path"], rec["old"]):
            if side is None:
                continue
            for sha, pathmap in landed.items():
                landed_pair = pathmap.get(side)
                if landed_pair is None:
                    continue
                if landed_pair == (staged_pair[1], staged_pair[0]):
                    per_commit.setdefault(sha, set()).add(side)
    findings = []
    acked = []
    for sha in sorted(per_commit):
        if ack_sha and sha == ack_sha:
            acked.append(sha)
            continue
        if len(per_commit[sha]) >= MIRROR_FLOOR:
            findings.append("diffstat mirror of landed commit %s (paths: %s)"
                            % (sha, ", ".join(sorted(per_commit[sha]))))
    return findings, acked


def load_landed(root, rev):
    args = ["git", "-C", root, "log", "--format=%H", "--numstat", "-z", "-M",
            "--diff-merges=first-parent",
            "--since=%s" % MIRROR_SCAN_SINCE,
            "--max-count=%d" % MIRROR_SCAN_MAX_COMMITS, rev]
    return parse_log_numstat_z(run_git(args, "log scan"))


def report(findings, acked):
    for line in findings:
        print(line)
    if findings:
        print("refuse: reverse-squash signature detected")
        return 1
    if acked:
        for sha in acked:
            print("ok: mirror %s acknowledged" % sha)
        return 0
    print("ok: no reverse-squash signature")
    return 0


def cmd_check_staged(args):
    root = args.repo
    probe = ["git", "-C", root, "rev-parse", "--git-dir"]
    try:
        run_git(probe, "repository probe")
        numstat_raw = run_git(["git", "-C", root, "diff", "--cached", "-M", "--numstat", "-z"],
                              "staged numstat")
        diff_text = run_git(["git", "-C", root, "diff", "--cached", "-M"],
                            "staged diff").decode("utf-8", "replace")
        head = run_git(["git", "-C", root, "rev-parse", "HEAD"], "HEAD resolve").decode().strip()
    except ToolError as exc:
        return fail2(str(exc))
    records = parse_numstat_z(numstat_raw)
    landed = load_landed(root, head)
    findings = egress_findings(records, diff_text)
    mirrors, acked = mirror_findings(records, landed, args.ack)
    findings.extend(mirrors)
    return report(findings, acked)


def cmd_check_diff(args):
    root = args.repo
    try:
        run_git(["git", "-C", root, "rev-parse", "--git-dir"], "repository probe")
        run_git(["git", "-C", root, "rev-parse", "--verify", "%s^{commit}" % args.against],
                "against revision resolve")
        if args.diff_file:
            try:
                with open(args.diff_file, "rb") as fh:
                    diff_raw = fh.read()
            except OSError as exc:
                return fail2("diff input: %s" % exc)
        else:
            diff_raw = sys.stdin.buffer.read()
        if diff_raw.strip() == b"":
            # A genuinely empty tracked-dirt set: git apply would reject
            # empty input, but an empty diff is clean by definition.
            print("ok: no reverse-squash signature")
            return 0
        if b"diff --git " not in diff_raw:
            return fail2("input diff is not git-format (no 'diff --git' header)")
        numstat_raw = run_git(["git", "-C", root, "apply", "--numstat", "-z", "--allow-empty", "-"],
                              "apply numstat", input_bytes=diff_raw)
    except ToolError as exc:
        return fail2(str(exc))
    try:
        records = parse_numstat_z(numstat_raw)
    except ToolError as exc:
        return fail2(str(exc))
    diff_text = diff_raw.decode("utf-8", "replace")
    landed = load_landed(root, args.against)
    findings = egress_findings(records, diff_text)
    mirrors, acked = mirror_findings(records, landed, args.ack)
    findings.extend(mirrors)
    return report(findings, acked)


def cmd_check_commit(args):
    root = args.repo
    try:
        run_git(["git", "-C", root, "rev-parse", "--git-dir"], "repository probe")
    except ToolError as exc:
        return fail2(str(exc))
    # An unresolvable rev raises ToolError inside run_git; main() maps that
    # to the guard-family exit 2 (tool failure).
    rev = run_git(["git", "-C", root, "rev-parse", "--verify",
                   args.rev + "^{commit}"], "commit resolve").decode().strip()
    fields = run_git(["git", "-C", root, "rev-list", "--parents", "-n", "1", rev],
                     "parent scan").decode().split()
    if len(fields) > 1:
        print("ok: parented commit")
        return 0
    numerator = run_git(["git", "-C", root, "ls-tree", "-r", "--name-only", rev],
                        "tree listing").decode().splitlines()
    n = len([ln for ln in numerator if ln.strip()])
    denominator = run_git(["git", "-C", root, "ls-files"],
                          "tracked listing").decode().splitlines()
    d = len([ln for ln in denominator if ln.strip()])
    if d == 0:
        ratio = 1.0 if n > 0 else 0.0
    else:
        ratio = float(n) / float(d)
    if ratio >= SNAPSHOT_RATIO:
        print("refuse: parentless near-full-repo squash commit detected "
              "(%d/%d paths >= %s)" % (n, d, SNAPSHOT_RATIO))
        return 1
    print("ok: parentless commit below snapshot ratio (%d/%d)" % (n, d))
    return 0


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(prog="reverse_squash_guard.py")
    sub = parser.add_subparsers(dest="mode", required=True)

    staged = sub.add_parser("check-staged")
    staged.add_argument("--repo", default=".")
    staged.add_argument("--ack", default=None)

    diff = sub.add_parser("check-diff")
    diff.add_argument("--against", required=True)
    diff.add_argument("--repo", required=True)
    diff.add_argument("--ack", default=None)
    diff.add_argument("diff_file", nargs="?", default=None)

    commit = sub.add_parser("check-commit")
    commit.add_argument("--rev", required=True)
    commit.add_argument("--repo", required=True)

    args = parser.parse_args(argv)
    try:
        if args.mode == "check-staged":
            return cmd_check_staged(args)
        if args.mode == "check-commit":
            return cmd_check_commit(args)
        return cmd_check_diff(args)
    except ToolError as exc:
        return fail2(str(exc))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
