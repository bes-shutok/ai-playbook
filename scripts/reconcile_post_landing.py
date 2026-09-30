#!/usr/bin/env python3
"""Post-landing reconciliation: bring every live checkout of the base branch
current after a ref-level landing, with per-path discriminator-gated restores.

Invocation (run by the landing session after the merge-landing lock release):

    python3 scripts/reconcile_post_landing.py --base <branch> \
        --pre-tip <sha> --post-tip <sha> [--repo ROOT]

The script resolves every checkout from ``git worktree list --porcelain``
whose HEAD symref is the base branch or whose detached HEAD is an ancestor of
the post-landing tip, and skips unrelated checkouts. The tip guard runs first
and again immediately before the restore phase: when ``refs/heads/<base>`` no
longer equals ``--post-tip``, a newer landing owns the checkouts and the run
degrades to one block row per live checkout naming the newer landing, with
zero writes. A checkout mid-merge or mid-rebase is a block row and is never
written; a registered checkout whose directory is missing is a
``missing-worktree`` block row and the run continues. A detached checkout
genuinely behind the post-landing tip is fast-forwarded with
``git merge --ff-only`` in the restore phase, immediately after the tip
re-check; a refusal is a block row, never force. The wholesale index
signature (``git diff --cached <pre-tip>`` empty
while HEAD holds the post-landing tip) is recorded as the wholesale
recognition line; remediation is still per path.

Every landing-changed path is classified from its byte states at the two tips
and in the checkout, per the stale-checkout discriminator's gating rule in the
Worktree-first standard section of agents/skills/execute-plan/SKILL.md: an
ancestor-blob match (the pre-landing tip's blob or any older ancestor, walked
with ``git rev-parse <commit>:<path>`` over ``git log --format=%H -- <path>``
while skipping commits where the path does not exist, a deletion or
rename-source commit, never a tool failure) is restored from the post tip
with the single-path restore, re-reading both byte states immediately before
the restore so a mid-window change re-classifies; a path whose bytes match no
ancestor blob in either state is a genuine modification and a block row,
never restored, and a landing-deleted path whose index carries a blob
matching no ancestor (a peer's staged edit) is a block row naming the staged
state. In the checkout holding the common git dir (the primary), an
ancestor-blob match whose worktree file mtime postdates the pre-landing tip's
commit time is a block row instead of an auto-restore; other resolved live
checkouts auto-restore freely.

Output one line per row: ``restored <checkout> <path>``,
``block <checkout> <path> <witness>``, ``wholesale <checkout>``,
``synced <checkout> <path>``.

Exit codes: 0 when every live checkout is verified complete, 1 when block
rows exist (the caller records them as named blocks), 2 on tool failure. A
``--base``, ``--pre-tip``, or ``--post-tip`` value git cannot resolve is exit
2 with zero writes, never a silent pass.
"""

import argparse
import os
import subprocess
import sys


class ToolFailure(Exception):
    """A git tool failure: exit 2, no further writes."""


class Invocation(object):
    """The resolved reconciliation arguments."""

    def __init__(self, base, pre_tip, post_tip, repo=None):
        self.base = base
        self.pre_tip = pre_tip
        self.post_tip = post_tip
        self.repo = repo or os.getcwd()


class Result(object):
    """The rows the run decided plus its exit code."""

    def __init__(self, rows, exit_code):
        self.rows = rows
        self.exit_code = exit_code


# Actions a landing-changed path can take.
SYNCED = "synced"
RESTORE = "restore"                  # restore index and worktree from the post tip
RESTORE_WORKTREE = "restore-worktree"  # restore the worktree only; index untouched
BLOCK = "block"


def git(cwd, *args, **kwargs):
    """Run git with an argument list (no shell); ToolFailure outside ``ok``.

    The spawned env is merged over ``os.environ`` with global and system git
    config nulled and ``GIT_CONFIG_NOSYSTEM=1``, so in-process use is
    hermetic against host git configuration."""
    ok = kwargs.pop("ok", (0,))
    stdin = kwargs.pop("stdin", None)
    env = kwargs.pop("env", None)
    if kwargs:
        raise TypeError("unexpected git kwargs: %s" % sorted(kwargs))
    if env is None:
        env = dict(os.environ)
        env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        env["GIT_CONFIG_SYSTEM"] = "/dev/null"
        env["GIT_CONFIG_NOSYSTEM"] = "1"
    proc = subprocess.run(
        ["git", "-C", cwd] + list(args),
        capture_output=True,
        text=True,
        input=stdin,
        env=env,
    )
    if proc.returncode not in ok:
        raise ToolFailure(
            "git %s failed (rc %d): %s"
            % (" ".join(args), proc.returncode, proc.stderr.strip())
        )
    return proc


def rev_parse_verify(cwd, rev):
    """Resolve rev to a full sha; None when git cannot resolve it (rc 1)."""
    proc = git(cwd, "rev-parse", "--verify", "--quiet", rev, ok=(0, 1))
    if proc.returncode == 0:
        return proc.stdout.strip()
    return None


def commit_time(repo, sha):
    return int(git(repo, "show", "-s", "--format=%ct", sha).stdout.strip())


def is_ancestor(repo, maybe_ancestor, descendant):
    proc = git(repo, "merge-base", "--is-ancestor", maybe_ancestor, descendant, ok=(0, 1))
    return proc.returncode == 0


def parse_worktrees(repo):
    """Parse ``git worktree list --porcelain``; the primary is the first block."""
    out = git(repo, "worktree", "list", "--porcelain").stdout
    blocks = []
    current = None
    for line in out.splitlines():
        if not line.strip():
            if current is not None:
                blocks.append(current)
                current = None
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current = {"worktree": value, "head": None, "branch": None, "detached": False}
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value
        elif key == "detached":
            current["detached"] = True
    if current is not None:
        blocks.append(current)
    return blocks


def is_live(block, inv):
    """A checkout of the base branch, or a detached HEAD that is an ancestor of
    the post-landing tip; anything else is unrelated and skipped."""
    if block["branch"] == "refs/heads/%s" % inv.base:
        return True
    if block["detached"] and block["head"]:
        return is_ancestor(inv.repo, block["head"], inv.post_tip)
    return False


def changed_paths(repo, pre_tip, post_tip):
    # --no-renames pins the enumeration: host diff.renames config cannot
    # collapse a delete+add pair into a rename and skew the path set.
    out = git(repo, "diff", "--name-only", "--no-renames", pre_tip, post_tip).stdout
    return [line for line in out.splitlines() if line]


def blob_at(repo, tip, path):
    """Blob of path in tip's tree; None when absent (a deletion or rename-source
    state), skipped rather than treated as a match or a tool failure."""
    return rev_parse_verify(repo, "%s:%s" % (tip, path))


def index_blob(checkout, path):
    out = git(checkout, "ls-files", "--stage", "--", path).stdout
    for line in out.splitlines():
        meta, _, entry_path = line.partition("\t")
        if entry_path == path:
            return meta.split()[1]
    return None


def worktree_blob(checkout, path):
    if not os.path.isfile(os.path.join(checkout, path)):
        return None
    return git(checkout, "hash-object", "--", path).stdout.strip()


def ancestor_blobs(repo, pre_tip, path, pre_blob):
    """Blobs the path carried at ancestor commits: the pre-landing tip's blob or
    any older ancestor. Walks ``git log --format=%H <pre_tip> -- <path>`` and
    rev-parses ``<commit>:<path>``, skipping commits where the path does not
    exist (a deletion or rename-source commit); such failures are skips, never
    a match and never a tool failure."""
    blobs = set()
    if pre_blob:
        blobs.add(pre_blob)
    out = git(repo, "log", "--format=%H", pre_tip, "--", path).stdout
    for line in out.splitlines():
        commit = line.strip()
        if not commit:
            continue
        found = blob_at(repo, commit, path)
        if found:
            blobs.add(found)
    return blobs


def classify(pre_blob, post_blob, idx_blob, wt_blob, ancestors):
    """The canonical gating rule: synced, a restore arm, or a genuine block."""
    if idx_blob == post_blob and wt_blob == post_blob:
        return (SYNCED, None)
    in_checkout = idx_blob is not None or wt_blob is not None
    if pre_blob is None and not in_checkout:
        # The landing added the path and the checkout never saw it: materialize.
        return (RESTORE, "added")
    if post_blob is None and wt_blob == pre_blob:
        # The landing deleted the path and the checkout still carries the
        # pre-landing bytes: the same restore removes it, but only when the
        # index agrees, i.e. the index blob is an ancestor blob or the path
        # is absent from the index (nothing staged). A staged non-ancestor
        # blob is a peer's edit: block, never restore.
        if idx_blob is None or idx_blob in ancestors:
            return (RESTORE, "deleted")
        return (BLOCK, "staged-peer-edit")
    if pre_blob is not None and post_blob is not None:
        if idx_blob in ancestors and wt_blob in ancestors:
            return (RESTORE, "stale")
        if wt_blob == post_blob and idx_blob in ancestors:
            return (RESTORE, "half-synced")
        if wt_blob in ancestors and idx_blob == post_blob:
            return (RESTORE_WORKTREE, "wholesale-residue")
    return (BLOCK, "genuine-modification")


# The ancestor-blob restore arms: the only verdicts the primary fresh-mtime
# bound gates.
FRESH_MTIME_WITNESSES = ("stale", "deleted", "wholesale-residue")


def mtime_gated(action, witness):
    """True when the verdict restores worktree bytes that are an ancestor
    blob, the only shape the primary fresh-mtime bound gates."""
    return action in (RESTORE, RESTORE_WORKTREE) and witness in FRESH_MTIME_WITNESSES


def worktree_mtime_postdates(checkout, path, epoch):
    try:
        return os.stat(os.path.join(checkout, path)).st_mtime > epoch
    except OSError:
        return False


def git_path_in(checkout, marker):
    out = git(checkout, "rev-parse", "--git-path", marker).stdout.strip()
    if not os.path.isabs(out):
        out = os.path.join(checkout, out)
    return out


def midflight_witness(checkout):
    """MERGE_HEAD, rebase-merge, rebase-apply, CHERRY_PICK_HEAD, or the
    sequencer head in the checkout's git dir. Cherry-pick markers
    (CHERRY_PICK_HEAD and sequencer/head) map to the mid-cherry-pick
    witness; rebase markers keep mid-rebase."""
    for marker, witness in (
        ("MERGE_HEAD", "mid-merge"),
        ("rebase-merge", "mid-rebase"),
        ("rebase-apply", "mid-rebase"),
        ("CHERRY_PICK_HEAD", "mid-cherry-pick"),
        ("sequencer/head", "mid-cherry-pick"),
    ):
        if os.path.exists(git_path_in(checkout, marker)):
            return witness
    return None


def base_tip(repo, base):
    tip = rev_parse_verify(repo, "refs/heads/%s" % base)
    if tip is None:
        raise ToolFailure("refs/heads/%s is unresolvable" % base)
    return tip


def newer_landing_rows(live_paths, newer_tip):
    return ["block %s - newer-landing %s" % (path, newer_tip) for path in live_paths]


def classify_checkout(inv, block, primary, paths, pre_time):
    """One live checkout: the missing-directory and midflight guards, the
    wholesale recognition line, and the per-path classification. The detached
    fast-forward itself belongs to the restore phase, after the tip re-check."""
    checkout = {
        "path": block["worktree"],
        "blocked_row": None,
        "wholesale": False,
        "ff_needed": bool(
            block["detached"] and block["head"] and block["head"] != inv.post_tip
        ),
        "entries": [],
    }
    wt = checkout["path"]
    if not os.path.isdir(wt):
        # A registered worktree whose directory is gone: a block row naming
        # the missing checkout, never a tool failure; the run continues.
        checkout["blocked_row"] = "block %s - missing-worktree" % wt
        return checkout
    witness = midflight_witness(wt)
    if witness:
        checkout["blocked_row"] = "block %s - %s" % (wt, witness)
        return checkout
    head_sha = rev_parse_verify(wt, "HEAD")
    if head_sha == inv.post_tip:
        proc = git(wt, "diff", "--cached", "--quiet", inv.pre_tip, ok=(0, 1))
        if proc.returncode == 0:
            checkout["wholesale"] = True
    for path in paths:
        pre_blob = blob_at(inv.repo, inv.pre_tip, path)
        post_blob = blob_at(inv.repo, inv.post_tip, path)
        idx_blob = index_blob(wt, path)
        wt_blob = worktree_blob(wt, path)
        ancestors = ancestor_blobs(inv.repo, inv.pre_tip, path, pre_blob)
        action, witness = classify(pre_blob, post_blob, idx_blob, wt_blob, ancestors)
        entry = {
            "path": path,
            "action": action,
            "witness": witness,
            "expected": (idx_blob, wt_blob),
            "ancestors": ancestors,
            "pre_blob": pre_blob,
            "post_blob": post_blob,
            "mtime_bound": False,
        }
        if mtime_gated(action, witness):
            # The worktree bytes equal an ancestor blob: at the primary, a
            # fresh mtime means a peer touched the path after the landing.
            if wt == primary and worktree_mtime_postdates(wt, path, pre_time):
                entry["action"] = BLOCK
                entry["witness"] = "fresh-mtime"
            else:
                entry["mtime_bound"] = True
        checkout["entries"].append(entry)
    return checkout


def build_plan(inv):
    """Classification phase: tip guard, live checkouts, per-path verdicts."""
    plan = {"live": [], "checkouts": [], "newer_landing": None}
    tip = base_tip(inv.repo, inv.base)
    blocks = parse_worktrees(inv.repo)
    primary = blocks[0]["worktree"] if blocks else None
    live_blocks = [block for block in blocks if is_live(block, inv)]
    plan["live"] = [block["worktree"] for block in live_blocks]
    if tip != inv.post_tip:
        plan["newer_landing"] = tip
        plan["checkouts"] = [
            {
                "path": block["worktree"],
                "blocked_row": None,
                "wholesale": False,
                "entries": [],
                "newer_row": "block %s - newer-landing %s"
                % (block["worktree"], tip),
            }
            for block in live_blocks
        ]
        return plan
    paths = changed_paths(inv.repo, inv.pre_tip, inv.post_tip)
    pre_time = commit_time(inv.repo, inv.pre_tip)
    for block in live_blocks:
        plan["checkouts"].append(
            classify_checkout(inv, block, primary, paths, pre_time)
        )
    return plan


def restore_path(inv, wt, path, worktree_only):
    """The single-path restore from the post tip; subprocess argument list,
    no shell."""
    if worktree_only:
        git(wt, "restore", "--source=" + inv.post_tip, "--worktree", "--", path)
    else:
        git(
            wt,
            "restore",
            "--source=" + inv.post_tip,
            "--staged",
            "--worktree",
            "--",
            path,
        )


def apply_entry(inv, wt, entry, primary, pre_time):
    """Re-read both byte states immediately before the restore so a mid-window
    change re-classifies; then execute the single verdict. A re-classified
    verdict re-derives the primary fresh-mtime bound from the fresh verdict
    instead of reusing the plan-time bound."""
    idx_blob = index_blob(wt, entry["path"])
    wt_blob = worktree_blob(wt, entry["path"])
    action = entry["action"]
    witness = entry["witness"]
    mtime_bound = entry["mtime_bound"]
    if (idx_blob, wt_blob) != entry["expected"]:
        action, witness = classify(
            entry["pre_blob"],
            entry["post_blob"],
            idx_blob,
            wt_blob,
            entry["ancestors"],
        )
        mtime_bound = mtime_gated(action, witness)
    if action == BLOCK:
        return "block %s %s %s" % (wt, entry["path"], witness)
    if action == SYNCED:
        return "synced %s %s" % (wt, entry["path"])
    if (
        mtime_bound
        and wt == primary
        and worktree_mtime_postdates(wt, entry["path"], pre_time)
    ):
        return "block %s %s fresh-mtime" % (wt, entry["path"])
    try:
        restore_path(inv, wt, entry["path"], action == RESTORE_WORKTREE)
    except ToolFailure:
        # The witnessed untracked-debris refusal shape: one path the
        # restore cannot take degrades to its block row (the recorded,
        # resumable outcome) instead of aborting the run as a tool
        # failure; classification and other tool failures inside the
        # entry keep their exit-2 ToolFailure semantics.
        return "block %s %s restore-refused" % (wt, entry["path"])
    return "restored %s %s" % (wt, entry["path"])


def status_paths(wt):
    """Paths carrying a status entry (``git status --porcelain -z``)."""
    out = git(wt, "status", "--porcelain", "-z").stdout
    fields = out.split("\0")
    paths = set()
    skip_next = False
    for field in fields:
        if skip_next:
            skip_next = False
            continue
        if len(field) >= 4 and field[2] == " ":
            paths.add(field[3:])
            if field[0] in ("R", "C"):
                skip_next = True
    return paths


def verify_checkout(inv, wt, paths, rows_with_blocks):
    """Completion is verified, not assumed: each landing-changed path carries no
    diff against the new base tip and no status entry."""
    staged = status_paths(wt)
    for path in paths:
        if path in rows_with_blocks:
            continue
        post_blob = blob_at(inv.repo, inv.post_tip, path)
        if index_blob(wt, path) != post_blob:
            return "block %s %s verification-failed" % (wt, path)
        if worktree_blob(wt, path) != post_blob:
            return "block %s %s verification-failed" % (wt, path)
        if path in staged:
            return "block %s %s verification-failed" % (wt, path)
    return None


def apply_plan(plan, inv):
    """Restore phase: re-check the tip, execute the planned verdicts, verify."""
    pre_time = commit_time(inv.repo, inv.pre_tip)
    blocks = parse_worktrees(inv.repo)
    primary = blocks[0]["worktree"] if blocks else None
    rows = []
    failed = False
    if plan["newer_landing"] is not None:
        return Result(newer_landing_rows(plan["live"], plan["newer_landing"]), 1)
    tip = base_tip(inv.repo, inv.base)
    if tip != inv.post_tip:
        # Re-check the tip immediately before the restore phase: a newer
        # landing owns the checkouts; write nothing anywhere.
        return Result(newer_landing_rows(plan["live"], tip), 1)
    paths = changed_paths(inv.repo, inv.pre_tip, inv.post_tip)
    for checkout in plan["checkouts"]:
        wt = checkout["path"]
        rows_with_blocks = set()
        if checkout["blocked_row"]:
            rows.append(checkout["blocked_row"])
            failed = True
            continue
        if checkout.get("ff_needed"):
            # The detached fast-forward sits after the tip re-check so the
            # re-check covers every write: genuinely behind, fast-forward,
            # never force; a refusal is a block row.
            proc = git(wt, "merge", "--ff-only", inv.post_tip, ok=(0, 1))
            if proc.returncode != 0:
                rows.append("block %s - ff-refused" % wt)
                failed = True
                continue
        if checkout["wholesale"]:
            rows.append("wholesale %s" % wt)
        for entry in checkout["entries"]:
            row = apply_entry(inv, wt, entry, primary, pre_time)
            rows.append(row)
            if row.startswith("block "):
                failed = True
                rows_with_blocks.add(entry["path"])
        failure = verify_checkout(inv, wt, paths, rows_with_blocks)
        if failure:
            rows.append(failure)
            failed = True
    return Result(rows, 1 if failed else 0)


def resolve_invocation_or_exit2(inv):
    """A --base, --pre-tip, or --post-tip value git cannot resolve is exit 2
    with zero writes, never a silent pass. The invocation's tip fields are
    rewritten to the resolved full shas, so the tip guards compare resolved
    identities: an abbreviated argument spelling must not degrade to
    newer-landing blocks."""
    checks = (
        ("--base", None, "refs/heads/%s" % inv.base),
        ("--pre-tip", "pre_tip", "%s^{commit}" % inv.pre_tip),
        ("--post-tip", "post_tip", "%s^{commit}" % inv.post_tip),
    )
    for label, field, rev in checks:
        try:
            sha = rev_parse_verify(inv.repo, rev)
        except ToolFailure as exc:
            sys.stderr.write("tool failure: %s\n" % exc)
            return False
        if sha is None:
            sys.stderr.write("cannot resolve %s value %r\n" % (label, rev))
            return False
        if field is not None:
            setattr(inv, field, sha)
    return True


def run(inv):
    """Build the plan, apply it, print one line per row, return the exit code."""
    plan = build_plan(inv)
    result = apply_plan(plan, inv)
    for row in result.rows:
        sys.stdout.write(row + "\n")
    return result.exit_code


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile every live checkout of the base branch after a "
            "ref-level landing; per-path restores are discriminator-gated."
        )
    )
    parser.add_argument("--base", required=True, help="the base branch the landing moved")
    parser.add_argument("--pre-tip", dest="pre_tip", required=True, help="the pre-landing tip")
    parser.add_argument("--post-tip", dest="post_tip", required=True, help="the post-landing tip")
    parser.add_argument("--repo", default=None, help="repository root (default: cwd)")
    args = parser.parse_args(argv)
    inv = Invocation(args.base, args.pre_tip, args.post_tip, args.repo)
    if not resolve_invocation_or_exit2(inv):
        return 2
    try:
        return run(inv)
    except ToolFailure as exc:
        sys.stderr.write("tool failure: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
