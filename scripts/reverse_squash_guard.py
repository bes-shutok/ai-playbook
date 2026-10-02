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
  check-landing --source-branch BRANCH --target-ref REV [--repo ROOT]
      Judge a landing before its ref move: the source branch must contain
      the target tip (the tip is an ancestor of the branch). Refuses the
      witnessed stale-base squash clobber (2026-10-02: commit 3fd4be09
      deleted a 20-minute-old peer landing from a pre-landing base), naming
      the merge base and every path the landing would delete from the
      target; a source branch already an ancestor of the target is refused
      as already integrated (nothing to land).
  check-landed --rev REV --source-branch BRANCH --pre-tip REV [--repo ROOT]
      [--ack-deleted PATH]... [--ack-file FILE]
      Judge a landed commit after its ref move: deletions in the commit's
      first-parent diff (REV^ -> REV) whose content was last touched after
      the merge base of BRANCH and the pre-landing tip are the witnessed
      foreign-deletion clobber signature (2026-10-02: commit 3fd4be09),
      each finding naming the deleted path and the commit that last touched
      its content. Fold-and-delete deletions the run's manifest owns are
      acknowledged by exact path identity via repeatable --ack-deleted or
      an --ack-file newline list (blank lines skipped); acks are bounded to
      FOLD_ACK_TREES (docs/history/plans/, docs/history/backlog/) - an
      entry outside them is a tool failure, and a prefix or directory entry
      suppresses nothing and warns as unused.
  check-archive --rev SHA | --staged [--repo ROOT] [--ack-egress PATH]...
      Judge a plans-root egress (the archive-ceremony family).
      --rev inspects the commit's first-parent diff (REV^ -> REV);
      --staged judges index-versus-HEAD. An egress is a rename or
      deletion moving a plan file from a plans root (docs/history/plans/,
      docs/history/backlog/, excluding their completed/, deferred/, and
      rejected/ subdirectories) into an archive state directory
      (completed/ or deferred/ of either root), deleting it from a
      plans root, or leaving that plans root entirely (the sideways
      rename: docs/tmp/, the repo root, the other plans root); it must
      carry execution evidence: zero unchecked `- [ ]` boxes in the
      egress bytes (parent-side bytes for deletions) AND, for
      docs/history/plans/ sources, an exec-review record under
      docs/reviews/ or docs/history/reviews/ (read at check time; the
      homes are per-checkout state) whose filename matches the anchored
      record-name shape ^<...>-plan-review-<slug>-exec-r<N>.md$ (the
      whole name must match, anchored at both name ends, the slug
      occupying the whole hyphen-bounded segment, never a bare
      substring; the slug is the dated basename minus its leading date)
      and whose content carries the egress bytes' sha256. A backlog-root
      egress needs only the zero-unchecked-boxes leg (a backlog item
      never carries an exec-review record; its sanctioned ticket is the
      sweep's own gate receipt context). A missing or digest-mismatching
      record refuses; a rename into a rejected/ subdirectory of the
      source root is the sanctioned non-execution exit. --ack-egress
      suppresses exactly one egress path; more than one ack per
      invocation refuses and an ack naming a non-egress path refuses
      as unused; in --rev mode an acked path must be verified by a
      matching Archive-egress-ack: <path> trailer in the commit message
      (an ack whose message lacks the trailer, or whose trailer names a
      different path, refuses), and a --staged ack is warning-level only
      (it cannot be trailer-verified pre-commit).

Refusal classes: archive-dir egress (a deletion or rename out of
ARCHIVE_DIRS; judged by the staged and diff modes over the index and the
piped diff), the never-suppressible reviews-home egress (any A, M, R,
or C record whose post-side path falls under REVIEWS_HOME_PREFIXES -
docs/reviews/ or docs/history/reviews/; addition-side, no deletion arm),
and the diffstat mirror of a landed commit (suppressible per commit with
--ack); the landing mode additionally refuses a reviews-home egress in
the landing diff with its dedicated refuse line before the fresh-base
verdict, and the landed mode's foreign-deletion sweep walks the commit's
first-parent diff (REV^ -> REV). The plans-egress archive-ceremony
family (check-archive) shares its evidence schema with the
archive-ceremony section of scripts/done_sweep_gates_lib.py - the
contract twin; a contract edit updates both named sites. Named
divergences of record: this guard binds the record leg to the egress
bytes' sha256 digest, matches the record name with the anchored
record-name grammar above (the done lib's live series match is a bare
substring match, a hole this grammar deliberately does not share: plan
slug `foo` never matches `bar-foo`'s record here), reads both reviews
homes (the done lib reads its single resolved home), and covers both
plans roots (the done lib scans its own plans root only, with
rejected/ among its states where this guard keeps rejected/ the
sanctioned non-egress exit).

Exit codes: 0 clean, 1 refusal with named evidence, 2 tool failure.
  Stale-checkout adjudication: a refused or suspect entry whose blob equals the path's blob at an ancestor commit is a stale witness per the stale-checkout discriminator in the Worktree-first standard section of agents/skills/execute-plan/SKILL.md; restore-and-record, never commit.
"""

import hashlib
import os
import re
import subprocess
import sys

ARCHIVE_DIRS = ("docs/history/plans/completed/", "docs/history/backlog/completed/")
# Addition-side deny set for the reviews-home egress class: any tracked
# record (A, M, R, or C) whose post-side path lands under these homes is
# refused, in the staged set, a piped diff, and the landing diff.
REVIEWS_HOME_PREFIXES = ("docs/reviews/", "docs/history/reviews/")
# Fold-and-delete ack bound for the check-landed sweep: deliberately wider
# than ARCHIVE_DIRS (which carries the /completed/ component) because
# fold-and-delete targets sit flat in the two archive trees.
FOLD_ACK_TREES = ("docs/history/plans/", "docs/history/backlog/")
# check-archive: the plans roots whose open files are egress sources, the
# non-open state subdirectories under them, the archive state destinations
# (the done lib's _archive_state_dirs set minus rejected/, which is the
# sanctioned non-execution exit), and the reviews homes scanned at check
# time for the digest-bound record leg.
PLANS_ROOTS = ("docs/history/plans/", "docs/history/backlog/")
PLANS_STATE_SUBDIRS = ("completed", "deferred", "rejected")
ARCHIVE_STATE_SUBDIRS = ("completed", "deferred")
REVIEWS_HOMES = ("docs/reviews/", "docs/history/reviews/")
PLAN_SLUG_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
# The record stem grammar: <...>-plan-review-<slug>-exec-r<N>; the slug
# segment is matched hyphen-bounded (whole segment equality, never a bare
# substring: plan `foo` does not match `bar-foo`'s record).
EXEC_REVIEW_RECORD_RE = re.compile(r"^.+?-plan-review-(?P<slug>.+)-exec-r\d+$")
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


def is_reviews_home(path):
    return any(path.startswith(prefix) for prefix in REVIEWS_HOME_PREFIXES)


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


def reviews_home_findings(numstat_records, diff_text):
    """Signature: reviews-home egress. Addition-side, never suppressible.

    Flags every record whose post-side path falls under the deny set
    regardless of status letter (A, M, R, and C: a modified tracked record
    under the home is the same witnessed harm), via the numstat records and
    the extended-header rename pairs. No deletion arm: a reviews-home
    deletion is never a finding under this addition-side class (a D
    record's numstat path is the deleted pre-side path, so records whose
    path is a `deleted file mode` header path are skipped)."""
    findings = []
    seen = set()

    def add(path):
        if path not in seen:
            seen.add(path)
            findings.append("reviews-home egress: %s" % path)

    renames, deletions = parse_extended_headers(diff_text)
    preside = set(deletions)
    for pair in renames:
        if pair["to"] is not None and is_reviews_home(pair["to"]):
            add(pair["to"])
    for rec in numstat_records:
        if rec["path"] in preside:
            # D record: parse_numstat_z stores the deleted (pre-side) path
            # in `path`; the addition-side class must not refuse it.
            continue
        if is_reviews_home(rec["path"]):
            add(rec["path"])
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


def name_status_records(root, a, b=None):
    """One `--name-status -z` scan over the a -> b diff, parsed into records.

    Each record is {status (letter), old (first path), path (post-side
    path: the new side of R and C records, the single path otherwise)}.
    With b omitted the scan is `--cached a`: the index judged against a
    (the check-archive --staged arm's index-versus-HEAD shape). Consumed
    by deleted_paths (the shared deletion enumerator), by the
    cmd_check_landing reviews-home partition, and by cmd_check_archive,
    so the landing and archive modes each perform a single diff
    invocation."""
    args = ["git", "-C", root, "diff", "--name-status", "-z", "-M"]
    if b is None:
        args.append("--cached")
    args.append(a)
    if b is not None:
        args.append(b)
    ns_raw = run_git(args, "deletion scan")
    records = []
    tokens = ns_raw.split(b"\0")
    i = 0
    while i < len(tokens):
        status = tokens[i].decode("utf-8", "replace")
        i += 1
        if status == "" or i >= len(tokens):
            continue
        path = unquote_path(tokens[i].decode("utf-8", "replace"))
        i += 1
        letter = status[0]
        rec = {"status": letter, "old": path, "path": path}
        if letter in ("R", "C"):
            if i >= len(tokens):
                raise ToolError("truncated two-path name-status record")
            rec["path"] = unquote_path(tokens[i].decode("utf-8", "replace"))
            i += 1  # two-path record: the second token is the post-side path
        records.append(rec)
    return records


def deleted_paths(root, a, b):
    """Shared deletion enumerator over the a -> b name-status diff.

    Unquoted deleted paths; the old-side path of R and C records counts as
    a deletion (a rename or copy away deletes the old path). Consumed by
    cmd_check_landing (via the shared name_status_records scan) and the
    check-landed sweep so the deletion enumeration lives once."""
    return [rec["old"] for rec in name_status_records(root, a, b)
            if rec["status"] in ("D", "R", "C")]


def last_content_touch(root, path, a, b):
    """The newest commit in the range a..b that touched path's content,
    its sha, or empty when no commit in the range touched it. The
    check-landed mode's foreign-content predicate."""
    return run_git(["git", "-C", root, "log", "-n", "1", "--format=%H",
                    "%s..%s" % (a, b), "--", path],
                   "content-touch scan for %s" % path).decode().strip()


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
    findings.extend(reviews_home_findings(records, diff_text))
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
    findings.extend(reviews_home_findings(records, diff_text))
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


def cmd_check_landing(args):
    root = args.repo
    try:
        run_git(["git", "-C", root, "rev-parse", "--git-dir"], "repository probe")
        source = run_git(["git", "-C", root, "rev-parse", "--verify",
                          "%s^{commit}" % args.source_branch],
                         "source branch resolve").decode().strip()
        target = run_git(["git", "-C", root, "rev-parse", "--verify",
                          "%s^{commit}" % args.target_ref],
                         "target ref resolve").decode().strip()
    except ToolError as exc:
        return fail2(str(exc))

    def try_git(git_args):
        proc = subprocess.run(git_args, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        return (proc.returncode, proc.stdout.decode("utf-8", "replace").strip())

    # Reviews-home egress partition: the single target-to-source
    # name-status scan (the same scan the stale arm's deleted-path
    # partition consumes below, so no second diff invocation), taken
    # before the fresh-base early return so a fresh base cannot launder an
    # addition into the reviews home. A, M, R, and C records all count via
    # the post-side path, so renames into the set are caught; D does not
    # (this class is addition-side and carries no deletion arm).
    try:
        ns_records = name_status_records(root, target, source)
    except ToolError as exc:
        return fail2(str(exc))
    egress = []
    for rec in ns_records:
        if rec["status"] in ("A", "M", "R", "C") and is_reviews_home(rec["path"]):
            if rec["path"] not in egress:
                egress.append(rec["path"])
    if egress:
        for path in egress:
            print("reviews-home egress: %s" % path)
        print("refuse: reviews-home egress in the landing")
        return 1

    rc, _ = try_git(["git", "-C", root, "merge-base", "--is-ancestor",
                     target, source])
    if rc == 0:
        print("ok: landing base fresh (%s contains %s)"
              % (args.source_branch, target))
        return 0
    if rc > 1:
        return fail2("merge-base ancestry probe failed")

    rc_int, _ = try_git(["git", "-C", root, "merge-base", "--is-ancestor",
                         source, target])
    if rc_int == 0:
        print("refuse: source branch %s is already an ancestor of target tip "
              "%s: nothing to land" % (args.source_branch, target))
        return 1

    rc_mb, mb = try_git(["git", "-C", root, "merge-base", target, source])
    mb_text = mb if rc_mb == 0 and mb else "unrelated histories (no merge base)"
    findings = ["stale base: %s does not contain target tip %s "
                "(merge base: %s); rebase onto %s before landing"
                % (args.source_branch, target, mb_text, target)]

    # Name the content the landing would delete from the target: paths
    # present at the target tip and absent from the source branch's tree
    # (partitioned from the same name-status scan the reviews-home egress
    # check consumed; the old side of a rename-away counts).
    deleted = [rec["old"] for rec in ns_records
               if rec["status"] in ("D", "R", "C")]
    for path in deleted:
        try:
            added = run_git(["git", "-C", root, "log", "-n", "1",
                             "--format=%H", "--diff-filter=A", target,
                             "--", path],
                            "addition scan for %s" % path).decode().strip()
        except ToolError as exc:
            return fail2(str(exc))
        if added:
            findings.append("would delete from target: %s (content added at %s)"
                            % (path, added))

    for line in findings:
        print(line)
    print("refuse: landing base stale")
    return 1


def cmd_check_landed(args):
    root = args.repo
    try:
        run_git(["git", "-C", root, "rev-parse", "--git-dir"], "repository probe")
        rev = run_git(["git", "-C", root, "rev-parse", "--verify",
                       "%s^{commit}" % args.rev],
                      "landed commit resolve").decode().strip()
        source = run_git(["git", "-C", root, "rev-parse", "--verify",
                          "%s^{commit}" % args.source_branch],
                         "source branch resolve").decode().strip()
        pre_tip = run_git(["git", "-C", root, "rev-parse", "--verify",
                           "%s^{commit}" % args.pre_tip],
                          "pre-landing tip resolve").decode().strip()
    except ToolError as exc:
        return fail2(str(exc))

    def try_git(git_args):
        proc = subprocess.run(git_args, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        return (proc.returncode, proc.stdout.decode("utf-8", "replace").strip())

    rc_mb, mb = try_git(["git", "-C", root, "merge-base", source, pre_tip])
    if rc_mb != 0 or not mb:
        return fail2("unrelated histories: no merge base between %s and %s; "
                     "refusing to guess" % (args.source_branch, args.pre_tip))

    acks = list(args.ack_deleted or [])
    if args.ack_file:
        try:
            with open(args.ack_file, "rb") as fh:
                ack_raw = fh.read()
        except OSError as exc:
            return fail2("ack file: %s" % exc)
        for line in ack_raw.decode("utf-8", "replace").splitlines():
            entry = line.strip()
            if entry:
                acks.append(entry)
    # Set-difference semantics on entries: a repeated entry is one ack, so
    # consuming it must not strand a duplicate copy as an unused warning.
    # Suppression itself stays exact path identity (first-seen order kept
    # for deterministic output).
    acks = list(dict.fromkeys(acks))
    for entry in acks:
        if not any(entry.startswith(prefix) for prefix in FOLD_ACK_TREES):
            return fail2("ack entry outside the fold-ack trees (%s): %s"
                         % (", ".join(FOLD_ACK_TREES), entry))

    try:
        deleted = deleted_paths(root, rev + "^", rev)
    except ToolError as exc:
        return fail2(str(exc))

    findings = []
    acked = []
    unused = list(acks)
    for path in deleted:
        if path in acks:
            acked.append(path)
            unused.remove(path)
            continue
        touched = last_content_touch(root, path, mb, pre_tip)
        if touched:
            findings.append("landed foreign deletion: %s (content last touched "
                            "at %s after merge base %s)" % (path, touched, mb))
    for entry in unused:
        print("warning: ack entry matched no deleted path: %s" % entry)
    for path in acked:
        print("ok: acknowledged fold-and-delete deletion: %s" % path)
    if findings:
        for line in findings:
            print(line)
        print("refuse: landed commit deletes foreign content")
        return 1
    print("ok: no foreign deletion in the landed commit")
    return 0


# --- check-archive: the plans-egress archive-ceremony family ----------------
#
# The evidence schema is shared with the archive-ceremony section of
# scripts/done_sweep_gates_lib.py (the contract twin; one schema, two
# named implementations, so a contract edit updates both named sites;
# the named divergences of record live in the module docstring's
# contract-twin paragraph).


def plans_location(path):
    """Where a repo-relative path sits relative to the plans roots
    (PLANS_ROOTS): "root" for a file open at a plans root (outside the
    completed/, deferred/, and rejected/ state subdirectories), the state
    name for a file inside one of those states, "subdir" for any other
    nested directory, and None for a path outside both roots."""
    for root in PLANS_ROOTS:
        if path.startswith(root):
            rest = path[len(root):]
            top, sep, _rest = rest.partition("/")
            if sep and top in PLANS_STATE_SUBDIRS:
                return top
            if sep:
                return "subdir"
            return "root"
    return None


def egress_source_root(path):
    """The plans root (a PLANS_ROOTS member) an egress-source path sits
    under, or None when the path is outside both roots."""
    for root in PLANS_ROOTS:
        if path.startswith(root):
            return root
    return None


def archive_egress_pairs(records):
    """The plan-egress changes in a name-status record set, as
    (old_path, new_path_or_None) pairs. A deletion from an open plans
    root is egress; a rename from an open plans root into an archive
    state directory (completed/ or deferred/ of either root) is egress;
    so is a sideways rename whose destination leaves the source plans
    root entirely (docs/tmp/, the repo root, the other plans root); a
    rename into a rejected/ subdirectory of the source root is the
    sanctioned non-execution exit and is not egress; root-internal
    renames are not egress."""
    pairs = []
    for rec in records:
        if rec["status"] == "D":
            if plans_location(rec["path"]) == "root":
                pairs.append((rec["path"], None))
        elif rec["status"] == "R":
            if plans_location(rec["old"]) != "root":
                continue
            if plans_location(rec["path"]) in ARCHIVE_STATE_SUBDIRS:
                pairs.append((rec["old"], rec["path"]))
                continue
            source_root = egress_source_root(rec["old"])
            if source_root is not None \
                    and not rec["path"].startswith(source_root):
                pairs.append((rec["old"], rec["path"]))
    return pairs


def plan_slug(path):
    """The done lib's slug rule: the dated basename's stem minus its
    leading date prefix."""
    base = path.rsplit("/", 1)[-1]
    stem = base[:-3] if base.endswith(".md") else base
    return PLAN_SLUG_DATE_RE.sub("", stem, count=1)


def exec_review_record_matches(name, slug):
    """Anchored record-name match: the whole name must carry the
    <...>-plan-review-<slug>-exec-r<N> shape, anchored at both name
    ends, with the slug occupying the whole segment between the
    -plan-review- anchor and the -exec-r<N> series token. A
    bare-substring match (plan slug `foo` against `bar-foo`'s record,
    the done lib's live substring hole) never passes."""
    if not name.endswith(".md") or "-plan-review-" not in name:
        return False
    m = EXEC_REVIEW_RECORD_RE.match(name[:-3])
    return bool(m) and m.group("slug") == slug


def find_evidence_record(root, slug, digest_hex):
    """The digest-bound record leg, evaluated at check time: walk the
    reviews homes under root (the homes are per-checkout state) for a
    record whose name matches the slug hyphen-bounded and whose content
    carries the egress bytes' sha256. A name-only match without the
    digest does not satisfy the leg."""
    for home in REVIEWS_HOMES:
        home_dir = os.path.join(root, home)
        if not os.path.isdir(home_dir):
            continue
        for dirpath, _dirnames, filenames in os.walk(home_dir):
            for name in sorted(filenames):
                if not exec_review_record_matches(name, slug):
                    continue
                try:
                    with open(os.path.join(dirpath, name), "rb") as fh:
                        text = fh.read().decode("utf-8", "replace")
                except OSError:
                    continue
                if digest_hex in text:
                    return os.path.join(home, name)
    return None


def record_leg_required(old):
    """The exec-review record leg is scoped to plans-root FILES
    (docs/history/plans/): a backlog-root egress never carries an
    exec-review record (its sanctioned ticket is the sweep's own gate
    receipt context), so only the unchecked-boxes leg applies there."""
    return old.startswith("docs/history/plans/")


def plan_egress_finding(root, old, new, read_egress_bytes):
    """The named-evidence refusal block for one egress, or an empty list
    when both evidence legs pass. The egress bytes are the new-side bytes
    for a rename and the parent-side bytes for a deletion."""
    blob = read_egress_bytes(old, new)
    digest = hashlib.sha256(blob).hexdigest()
    unchecked = blob.count(b"- [ ]")
    header = "plan-egress: %s%s" % (old, "" if new is None else " -> %s" % new)
    legs = []
    if unchecked:
        legs.append("missing evidence leg: %d unchecked `- [ ]` task boxes "
                    "in the egress bytes (verify the work and check the "
                    "boxes)" % unchecked)
    if record_leg_required(old) \
            and find_evidence_record(root, plan_slug(old), digest) is None:
        legs.append("missing evidence leg: exec-review record for slug %s "
                    "(*-plan-review-<slug>-exec-r<N>.md, hyphen-bounded) "
                    "under %s whose content carries the egress bytes' "
                    "sha256 %s (backfill the completion record)"
                    % (plan_slug(old), " or ".join(REVIEWS_HOMES), digest))
    if not legs:
        return []
    return [header] + ["  %s" % leg for leg in legs]


ACK_TRAILER_RE = re.compile(r"^Archive-egress-ack:[ \t]*(.+?)[ \t]*$")


def ack_trailer_verified(commit_message, path):
    """True when the commit message carries an Archive-egress-ack:
    trailer naming exactly path (the whole trailer value is compared, so
    a trailer naming a different path never verifies another path's
    ack)."""
    for line in commit_message.splitlines():
        m = ACK_TRAILER_RE.match(line)
        if m and m.group(1) == path:
            return True
    return False


def cmd_check_archive(args):
    if args.staged == bool(args.rev):
        # Exactly one input arm: neither flag, or both, is a tool failure.
        return fail2("check-archive requires exactly one of --rev SHA "
                     "or --staged")
    root = args.repo
    commit_message = None
    try:
        run_git(["git", "-C", root, "rev-parse", "--git-dir"], "repository probe")
        if args.rev:
            rev = run_git(["git", "-C", root, "rev-parse", "--verify",
                           "%s^{commit}" % args.rev],
                          "commit resolve").decode().strip()
            records = name_status_records(root, rev + "^", rev)
            commit_message = run_git(
                ["git", "-C", root, "log", "-1", "--format=%B", rev],
                "commit message").decode("utf-8", "replace")

            def read_egress_bytes(old, new):
                spec = ("%s:%s" % (rev, new) if new
                        else "%s^:%s" % (rev, old))
                return run_git(["git", "-C", root, "show", spec],
                               "egress bytes %s" % spec)
        else:
            records = name_status_records(root, "HEAD")

            def read_egress_bytes(old, new):
                spec = ":%s" % new if new else "HEAD:%s" % old
                return run_git(["git", "-C", root, "show", spec],
                               "egress bytes %s" % spec)
    except ToolError as exc:
        return fail2(str(exc))
    acks = list(args.ack_egress or [])
    if len(acks) > 1:
        print("refuse: at most one --ack-egress per invocation (got %d)"
              % len(acks))
        return 1
    findings = []
    acked = []
    unused = list(acks)
    for old, new in archive_egress_pairs(records):
        if old in unused:
            unused.remove(old)
            acked.append(old)
            continue
        findings.extend(plan_egress_finding(root, old, new, read_egress_bytes))
    for entry in unused:
        print("warning: --ack-egress matched no detected egress: %s" % entry)
    trailer_missing = []
    if args.rev:
        for path in acked:
            if not ack_trailer_verified(commit_message, path):
                trailer_missing.append(path)
    else:
        for path in acked:
            print("warning: --ack-egress %s cannot be trailer-verified "
                  "pre-commit (restate an Archive-egress-ack: %s trailer "
                  "in the archive commit's message)" % (path, path))
    for path in acked:
        if path in trailer_missing:
            continue
        print("ok: acknowledged plan egress (operator ack): %s" % path)
    if findings or unused or trailer_missing:
        for line in findings:
            print(line)
        if findings:
            print("sanctioned exits: verify the work and check the boxes, "
                  "land the backfill completion record, take the rejected "
                  "path (rename under a rejected/ directory), or the "
                  "operator ack (--ack-egress PATH, restated in the commit "
                  "message as an Archive-egress-ack: <path> trailer)")
            print("refuse: plan egress without execution evidence")
        if unused:
            print("refuse: unused --ack-egress (an ack must name a "
                  "detected plan egress)")
        for path in trailer_missing:
            print("refuse: --ack-egress %s is not verified by a matching "
                  "Archive-egress-ack: %s trailer in the commit message"
                  % (path, path))
        return 1
    print("ok: no unevidenced plan egress")
    return 0


# --- check-single-commit: the landing-residue sweep -------------------------
#
# Landing-claim grammar (single definition; the plan document
# docs/history/plans/2026-10-03-single-commit-per-lane-event.md "Terms" is its
# prose home): a commit subject starting with "plans: land " is an authoring
# lane event and one starting with "done: execute " is an execution lane
# event. Every lane event lands exactly one main commit; closeout riders land
# as commits on the landing branch before the critical section, so any
# follow-up commit on main after a landing is residue this sweep flags.

LANDING_CLAIM_PREFIXES = ("plans: land ", "done: execute ")
FLIP_CLASS_PREFIX = "done: mark"
PRUNE_CLASS_PREFIX = "plans: prune"
CLOSEOUT_CLASS_PREFIXES = ("done: archive", "done: fold")
# Hyphen-token fragments shorter than this are too generic for linkage.
LINKAGE_TOKEN_MIN = 5
# Previous-landing walk bound (a linear walk below the tip; far past any
# observed inter-landing distance).
PREV_LANDING_MAX = 5000


def is_landing_claim(subject):
    return any(subject.startswith(p) for p in LANDING_CLAIM_PREFIXES)


def landing_claim_slug(subject):
    """The anchor plan's kebab slug: the first hyphenated token after the
    grammar prefix; fallback to the first token when none is hyphenated."""
    for prefix in LANDING_CLAIM_PREFIXES:
        if subject.startswith(prefix):
            tokens = subject[len(prefix):].split()
            for token in tokens:
                stripped = token.strip("()[]:,.")
                if "-" in stripped and stripped == stripped.lower():
                    return stripped
            return tokens[0].strip("()[]:,.") if tokens else ""
    return ""


def anchor_kind(subject):
    if subject.startswith("plans: land "):
        return "authoring"
    if subject.startswith("done: execute "):
        return "execution"
    return None


def linkage_signals(message, anchor_subject, anchor_sha):
    """Plan-linkage metadata reported on each finding line: the kebab slug,
    its space-form phrase, the anchor sha, or shared hyphen-token fragments
    present in the finding's message."""
    slug = landing_claim_slug(anchor_subject)
    signals = []
    if slug and slug in message:
        signals.append("slug:%s" % slug)
    if slug and " " in slug.replace("-", " ") and slug.replace("-", " ") in message:
        signals.append("space-form")
    if anchor_sha and anchor_sha in message:
        signals.append("anchor-sha:%s" % anchor_sha[:12])
    if slug:
        shared = [t for t in slug.split("-")
                  if len(t) >= LINKAGE_TOKEN_MIN and t in message]
        if shared and "slug:%s" % slug not in signals:
            signals.append("fragments:%s" % ",".join(shared[:3]))
    return signals


def load_subjects(root, rev_range, what):
    """Full-message records over a rev range, newest first: a leading-NUL
    record format (%x00%H%x00%s%x00%b); a commit body never contains NUL,
    so the split re-groups deterministically."""
    out = run_git(["git", "-C", root, "log",
                   "--format=%x00%H%x00%s%x00%b"] + rev_range.split() + ["--"],
                  what).decode("utf-8", "replace")
    fields = out.split("\x00")
    records = []
    i = 1
    while i + 2 <= len(fields):
        sha, subject, body = fields[i], fields[i + 1], fields[i + 2]
        if sha:
            records.append((sha, subject, body))
        i += 3
    return records


def resolve_anchor(root, args):
    """The anchor commit: --rev directly, or the nearest landing-claiming
    commit strictly below --prev-landing-of's tip."""
    if args.rev:
        rev = run_git(["git", "-C", root, "rev-parse", "--verify",
                       "%s^{commit}" % args.rev],
                      "anchor commit resolve").decode().strip()
        record = load_subjects(root, "-1 %s" % rev, "anchor subject read")
        if not record:
            raise ToolError("anchor subject read failed for %s" % rev)
        return (record[0][0], record[0][1])
    tip = run_git(["git", "-C", root, "rev-parse", "--verify",
                   "%s^{commit}" % args.prev_landing_of],
                  "prev-landing tip resolve").decode().strip()
    records = load_subjects(root, "-%d %s" % (PREV_LANDING_MAX, tip),
                            "previous-landing walk")
    for sha, subject, _body in records:
        if sha == tip:
            continue
        if is_landing_claim(subject):
            return (sha, subject)
    raise ToolError("no landing-claiming commit found below tip %s" % tip)


def sweep_window(root, anchor_sha, anchor_subject, until, max_window):
    """The two-ended window: commits reachable from --until excluding the
    anchor and its ancestors, walked oldest-first, closed early at the first
    landing-claiming commit other than the anchor, capped at max_window.
    Returns (scanned records, closed_early bool, window bounds shas)."""
    range_spec = "%s ^%s" % (until, anchor_sha)
    records = load_subjects(root, range_spec, "residue window read")
    records = list(reversed(records))  # oldest first
    scanned = []
    closed_early = False
    for sha, subject, body in records:
        if len(scanned) >= max_window:
            break
        if is_landing_claim(subject):
            closed_early = True
            break
        scanned.append((sha, subject, body))
    bounds = (anchor_sha, until)
    return scanned, closed_early, bounds


def classify_followups(anchor_kind_value, anchor_subject, anchor_sha, records):
    findings = []
    kind = anchor_kind_value
    slug = landing_claim_slug(anchor_subject)
    for sha, subject, body in records:
        message = subject + "\n" + body
        full = subject + " " + body
        if is_landing_claim(subject):
            continue  # the sanctioned next lane event never flags
        cls = None
        if kind == "authoring":
            if subject.startswith(FLIP_CLASS_PREFIX):
                cls = "flip"
            elif subject.startswith(PRUNE_CLASS_PREFIX):
                cls = "prune"
        elif kind == "execution":
            if subject.startswith(CLOSEOUT_CLASS_PREFIXES[0]):
                cls = "archive"
            elif subject.startswith(CLOSEOUT_CLASS_PREFIXES[1]):
                cls = "fold"
            if cls and slug and slug not in full:
                cls = None  # closeout classes flag only on slug linkage
        if cls:
            signals = linkage_signals(message, anchor_subject, anchor_sha)
            findings.append((sha, subject, cls, signals))
    return findings


def cmd_check_single_commit(args):
    root = args.repo
    try:
        run_git(["git", "-C", root, "rev-parse", "--git-dir"], "repository probe")
        if args.scan_window is not None:
            return cmd_check_single_commit_batch(args, root)
        if not args.rev and not args.prev_landing_of:
            print("fail: check-single-commit requires --rev or "
                  "--prev-landing-of")
            return 2
        resolved = resolve_anchor(root, args)
        anchor_sha, anchor_subject = resolved
        kind = anchor_kind(anchor_subject)
        if kind is None:
            print("fail: anchor %s is not a landing-claiming commit "
                  "(subject: %s)" % (anchor_sha[:12], anchor_subject))
            return 2
        until = args.until or "HEAD"
        until_sha = run_git(["git", "-C", root, "rev-parse", "--verify",
                             "%s^{commit}" % until],
                            "until commit resolve").decode().strip()
        scanned, closed_early, bounds = sweep_window(
            root, anchor_sha, anchor_subject, until_sha, args.max_window)
        findings = classify_followups(kind, anchor_subject, anchor_sha, scanned)
        acked_shas = load_ack_file(args.ack_file) if args.ack_file else set()
        return emit_single_commit_receipt(
            findings, acked_shas, len(scanned), bounds, closed_early)
    except ToolError as exc:
        return fail2(str(exc))


def cmd_check_single_commit_batch(args, root):
    """Batch mode: walk the last N landing-claiming commits on the base
    branch and sweep each one's two-ended window (until HEAD)."""
    until_sha = run_git(["git", "-C", root, "rev-parse", "--verify",
                         "%s^{commit}" % (args.until or "HEAD")],
                        "until commit resolve").decode().strip()
    walk = load_subjects(root, "-%d %s" % (PREV_LANDING_MAX, until_sha),
                         "batch landing walk")
    anchors = [(sha, subject) for sha, subject, _b in walk
               if is_landing_claim(subject)][:args.scan_window]
    if not anchors:
        print("ok: no landing-claiming commits found (batch scan)")
        return 0
    acked_shas = load_ack_file(args.ack_file) if args.ack_file else set()
    total_findings = []
    total_acked = []
    for anchor_sha, anchor_subject in anchors:
        scanned, closed_early, bounds = sweep_window(
            root, anchor_sha, anchor_subject, until_sha, args.max_window)
        findings = classify_followups(
            anchor_kind(anchor_subject), anchor_subject, anchor_sha, scanned)
        print("anchor %s %s" % (anchor_sha[:12], anchor_subject))
        for sha, subject, cls, signals in findings:
            line = "finding %s %s [%s] linkage: %s" % (
                sha, subject, cls, ", ".join(signals) or "none")
            if sha in acked_shas:
                print("acknowledged %s %s [%s]" % (sha, subject, cls))
                total_acked.append(sha)
            else:
                print(line)
                total_findings.append(sha)
        print("receipt: anchor=%s findings=%d window_scanned=%d "
              "window=[%s..%s]%s" % (
                  anchor_sha[:12],
                  sum(1 for s, _su, _c, _sig in findings if s not in acked_shas),
                  len(scanned), bounds[0][:12], bounds[1][:12],
                  " closed-early" if closed_early else ""))
    if total_findings:
        print("refuse: follow-up residue detected (%d finding(s) across "
              "%d anchor(s))" % (len(total_findings), len(anchors)))
        return 1
    print("ok: no follow-up residue (%d anchor(s) scanned)" % len(anchors))
    return 0


def load_ack_file(path):
    """One commit sha per line (blank lines skipped) - a different grammar
    from check-landed's path ack file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return {line.strip() for line in handle if line.strip()}
    except OSError as exc:
        raise ToolError("ack file unreadable: %s" % exc)


def emit_single_commit_receipt(findings, acked_shas, scanned, bounds,
                               closed_early):
    unacked = [f for f in findings if f[0] not in acked_shas]
    acked_rows = [f for f in findings if f[0] in acked_shas]
    for sha, subject, cls, signals in acked_rows:
        print("acknowledged %s %s [%s]" % (sha, subject, cls))
    for sha, subject, cls, signals in unacked:
        print("finding %s %s [%s] linkage: %s" % (
            sha, subject, cls, ", ".join(signals) or "none"))
    print("receipt: findings=%d acknowledged=%d window_scanned=%d "
          "window=[%s..%s]%s" % (
              len(unacked), len(acked_rows), scanned,
              bounds[0][:12], bounds[1][:12],
              " closed-early" if closed_early else ""))
    if unacked:
        print("refuse: follow-up residue detected")
        return 1
    print("ok: no unacknowledged follow-up residue")
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

    landing = sub.add_parser("check-landing")
    landing.add_argument("--source-branch", required=True)
    landing.add_argument("--target-ref", required=True)
    landing.add_argument("--repo", default=".")

    single = sub.add_parser(
        "check-single-commit",
        epilog=("Exit codes: 0 clean or every finding acknowledged; "
                "1 residue findings named (sha, subject, class, linkage); "
                "2 tool failure. The --ack-file grammar here is one commit "
                "sha per line, NOT check-landed's path ack file."))
    single.add_argument("--rev", default=None,
                        help="anchor commit (required unless --prev-landing-of)")
    single.add_argument("--until", default=None,
                        help="window head (default HEAD)")
    single.add_argument("--repo", default=".")
    single.add_argument("--max-window", type=int, default=20)
    single.add_argument("--prev-landing-of", default=None,
                        help="resolve the anchor as the nearest landing-claiming "
                             "commit strictly below this tip")
    single.add_argument("--ack-file", default=None,
                        help="newline-delimited commit shas to acknowledge")
    single.add_argument("--scan-window", type=int, default=None,
                        help="batch mode: sweep the last N landing-claiming "
                             "commits on the base branch")

    landed = sub.add_parser("check-landed")
    landed.add_argument("--rev", required=True)
    landed.add_argument("--source-branch", required=True)
    landed.add_argument("--pre-tip", required=True)
    landed.add_argument("--repo", default=".")
    landed.add_argument("--ack-deleted", action="append", default=None)
    landed.add_argument("--ack-file", default=None)

    archive = sub.add_parser("check-archive")
    archive.add_argument("--rev", default=None,
                         help="inspect one commit's first-parent diff "
                              "(REV^ -> REV); exactly one of --rev/--staged")
    archive.add_argument("--staged", action="store_true",
                         help="judge the index against HEAD; exactly one "
                              "of --rev/--staged")
    archive.add_argument("--repo", default=".")
    archive.add_argument("--ack-egress", action="append", default=None,
                         dest="ack_egress",
                         help="suppress exactly one egress path; at most "
                              "one per invocation, an unused ack refuses")

    args = parser.parse_args(argv)
    try:
        if args.mode == "check-staged":
            return cmd_check_staged(args)
        if args.mode == "check-commit":
            return cmd_check_commit(args)
        if args.mode == "check-landing":
            return cmd_check_landing(args)
        if args.mode == "check-single-commit":
            return cmd_check_single_commit(args)
        if args.mode == "check-landed":
            return cmd_check_landed(args)
        if args.mode == "check-archive":
            return cmd_check_archive(args)
        return cmd_check_diff(args)
    except ToolError as exc:
        return fail2(str(exc))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
