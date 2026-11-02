#!/usr/bin/env python3
"""Worktree closeout migration: capture a review-tree baseline and migrate new or modified artifacts to the main worktree.

Subcommands:
  capture  Write a JSON baseline (path plus SHA-256) of the configured
           review dirs, relative to the current working directory. The
           dirs resolve from the working directory's facts block
           (reviews_dir, tmp_dir, metrics_dir, review_certs_dir - the
           single source for repo paths); an explicit --dirs overrides,
           and an unresolvable facts block fails loud instead of
           guessing.
           Any path whose digest read raises OSError (a dangling symlink,
           a permission-denied file, ...) is skipped with a named
           warning and recorded under a "skipped" list instead of
           crashing the capture; the exit stays 0.
  migrate  Copy files that are new or modified versus the baseline from a
           source worktree into a target worktree, verifying every copy by
           re-read checksum. Never moves: on any verification failure the
           source file is still present and the exit code is non-zero.
           When the session manifest beside the baseline (manifest.md)
           binds its stable run tuple to the source worktree, terminal
           mirror_status/mirror_receipts tokens on task_boundary rows
           authorize replacing a different-byte primary target whose
           current state still matches the latest valid receipt for that
           exact path; invalid or mismatched receipt history keeps the
           foreign rename, and replacements are recorded under "replaced".
           A byte-identical primary target whose current state matches
           the path's latest valid receipt is likewise receipt-proven:
           it is recorded under "migrated" as verified (instead of
           "skipped") without rewriting the target bytes, so the
           removal gate's verified-destination check sees it; a target
           with no valid receipt keeps the skipped row.
           The migration holds the repository-keyed merge lock across its
           copies through one bounded-wait merge-wait-acquire under label
           worktree-closeout-migrate (wait default 300s, overridable by
           DOCS_SYNC_MERGE_MAX_WAIT), releasing in an always-run finally;
           a contended hold past the wait refuses with the holder evidence
           and copies nothing, and a non-git target (no repository key to
           lock by) is skipped with one named line.
           Dangling symlinks in the source are skipped with a warning and
           recorded as manifest skip entries. The manifest is written even
           when the run aborts mid-loop (an "interrupted": true marker
           flags the run, and an "incomplete" entry names the error), so
           already-copied files stay in the audit record.
           Baseline clobber guards (entry closeout-migrate-baseline-tracked-
           clobber): with a baseline and a git-repository target, the migrate
           refuses before any copy when a would-carry path is tracked at the
           target's HEAD with different committed bytes - a whole-file carry
           would overwrite destination content - naming each offending path
           and the re-capture remediation; after the carry, a staged tracked
           entry whose staged bytes are an older committed vintage of HEAD
           and that this run carried is restored from HEAD and reported as a
           prevented clobber (the between-snapshot rewind window), while
           staged entries this run did not carry are reported only and never
           touched. Non-git targets have no committed bytes to compare, so
           both guards are inert there.
  boundary-mirror  Mirror one task boundary's records from the run worktree
           to the primary checkout and append the boundary's task_boundary
           receipt row in one operation: a try-once merge-acquire of the
           same worktree-closeout-migrate repository lock migrate holds,
           kept through every staged mirror install and the atomic
           manifest-row replacement, released in an always-run finally;
           SIGINT and SIGTERM route through the ordinary rollback (prior
           primary targets and prior manifest bytes restored, temporary
           siblings removed, worktree sources retained) and the token-fenced
           release; a signal delivered between the manifest os.replace and
           the commit flag stays pending until the restore-or-discard
           decision has run, so an already-durable row is never rolled back. A refused acquire copies no primary files, records one
           status=skipped item per planned path with no verified receipt,
           reports the refusal, and exits 0 so the boundary continues. A
           per-path copy error is reported, recorded as a failed item, and
           never blocks the row. Exits 0 when the row is complete or
           skipped, 1 when a path failed or the transaction rolled back,
           2 on usage or identity validation.
  gate-removal  Fail-closed pre-removal gate: verify that every review
           record the executing plan's header cites (Plan review record:/
           Plan review: label lines in the header region only, the block
           before the first post-title line whose first character is
           "#", or end of file when no post-title line starts with "#";
           the boundary is a first-character rule, not a Markdown
           heading parse, and the plan body and its fences are never
           scanned)
           plus any --claims paths exists under the target's
           facts-resolved primary reviews home. Exit 0 pass (printing the
           sanctioned git worktree remove command for --worktree), 1 fail
           (one repo-relative line per missing path, a refusal for each
           citation outside the reviews home, a label-line citation or a
           claims entry alike: containment and presence are judged on the
           filesystem-resolved path, so a ..-threaded citation and a
           record symlink resolving outside the home are refused, never
           verified, with absolute exact citations always
           refused, never basename-verified, because their pathlib join
           would discard the home; an absolute series citation matches
           under the home by basename through the series primitive, which
           is correct because the records land under the home; a
           --worktree operand resolving equal to or nested with the
           --target checkout, and a resolved reviews home anchoring
           inside the --worktree tree (a symlinked home component
           staging the records the removal would destroy), are refused
           on their own lines with the operand remedy, never the migrate
           remedy, which the missing-record and outside-home refusals
           carry), 3 tool error. The reverse shape (a --worktree
           resolving inside the absolute external reviews home) is
           warning-only read-only visibility: it cannot refuse or block
           the removal, and the warning records the machinery-admission
           fields (expected catch frequency low, false-positive cost
           relocation noise, review date 2027-01-19). The gate also
           refuses teardown while a
           claimed record's `.stats.json` sibling exists in the worktree
           staging home (the facts-resolved reviews home under the worktree
           being removed) and is absent from the primary home, naming the
           missing-from-home sibling path beside the shared migrate remedy
           before any removal verdict; a sibling absent from the worktree
           staging home never refuses, series citations derive no siblings,
           and a `.stats.json` claims entry verifies as itself and derives
           nothing. Born-conformant to OUTCOME_CONTRACT.md;
           the other subcommands keep their legacy plain-exit semantics.
           Branch accounting rides the pass (plan
           2026-10-19-gate-removal-closeout-accounting): the gate captures
           one proven branch OID from the migration manifest's branch
           record, accounts content by ancestry or exact full-tree match
           (a tip whose complete tree equals any destination-history
           commit's tree is landed without ancestry or an archive twin,
           while the non-ancestor branch stays retained), reports the
           legacy changed-path scope as evidence only, guards live linked
           worktrees and migrated artifacts, and re-compares the ref
           after the checks, so a moved or unreadable ref refuses with
           the branch and any on-disk worktree retained. One
           branch-disposition: line carries the branch, the disposition,
           the proven OID, and the retention reasons. Branch-only mode
           (--branch with an explicit --migration-manifest, no
           --worktree) adjudicates a ref with no linked worktree under
           the same guard chain; deletion in either mode is operator
           work only. The verified no-charter stand-down arm (plan
           2026-10-28-plan-authoring-stand-down-before-charter): in
           worktree mode, when --authoring-claim names the authoring
           claim file and the expected plan file is absent, the gate
           verifies - each check refusing with preservation - the
           claim's session and origin, the frozen PLAN-PROMPTS entry
           naming the claim and its origin, the done-run manifest
           identity (owned_plan_paths naming the expected plan and
           start_commit), the claim-derived worktree placement (the
           claim-file stem) and authoring branch, the branch's
           start-commit equality, the clean worktree, and the
           zero-owned artifact accounting over every binding done-run
           manifest, then authorizes the
           removal through the shared removal line; the plan header is
           never parsed and the ordinary empty-owned-set refusal never
           runs in this arm, while every ordinary-plan gate-removal
           check stays unchanged.
  sweep    Mechanical ad-hoc worktree residue sweep beside a --target
           primary checkout. Report-only by default: every enumerated
           ad-hoc-shaped candidate (same parent directory as the primary,
           basename starting with the repository directory name plus
           -wt-) walks the six-arm pre-removal chain (shape, on-disk
           presence with the stale-registration re-targeting, clean
           tree, the gitignored staging corpus, plans-completed
           membership, live-session evidence, branch resolution plus
           post-landing activity), then the
           gate-removal verification runs over the completed twin's
           bytes read from the target HEAD tree (the candidate's
           slug-resolved migration manifest passed beside
           --plan-identity), and the run prints one
           verdict line per candidate plus the branch-disposition
           lines (content accounting, proven OID, retention reasons)
           ending with one final OUTCOME: line.
           --apply additionally requires the invoking run's authentic
           hold of the target's done lock (verified before any
           enumeration and again before the first release), holds the
           repository merge lock across its releases through one
           try-once merge-acquire, and removes ONLY stale registrations
           with no on-disk directory through the scoped
           administrative-dir removal gated by the enumeration-excluded
           non-destructive git worktree prune --dry-run -v filter and
           verified by the worktree-list deregistration postcondition.
           On-disk worktrees, their artifacts, and every branch ref stay
           operator-controlled in both modes and are never inferred from
           the gate's OUTCOME: pass (plan
           2026-10-19-gate-removal-closeout-accounting).
           Born-conformant to OUTCOME_CONTRACT.md (exit 0 pass, 1 fail
           on any removal command failure, 3 tool error; --help stays a
           metadata exit).
  verify-records  Verify that every review record a plan cites (series
           and exact path-like tokens) or a --claims file claims exists
           under the target's facts-resolved primary reviews home.
           Plain-exit convention: 0 verified, 1 missing records (named
           on stderr beside one JSON line), 2 named failure.
  owned-files-clean  Refuse a worktree removal while the worktree holds
           uncommitted owned files (the remedy is a wip: checkpoint
           commit or a transfer to the primary checkout) and, with
           --expect-plan, while the named owned plan file's
           byte-identical copy is absent from the target at the same
           repository-relative path. Born-conformant to
           OUTCOME_CONTRACT.md (exit 0 pass, 1 fail, 3 tool error).
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable
import review_plan_identity

sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths

# The capture dirs family, resolved from the facts block at the working
# directory in this order when capture runs without an explicit --dirs.
FACTS_DIR_KEYS = ("reviews_dir", "tmp_dir", "metrics_dir", "review_certs_dir")


def _facts_dirs() -> list[str] | None:
    """Resolve the capture dirs from the facts block at the working
    directory; None when the facts file or any family key is missing (the
    caller fails loud rather than guessing a default)."""
    if not Path(".ai-playbook/facts.md").is_file():
        return None
    values: list[str] = []
    for key in FACTS_DIR_KEYS:
        raw = facts_paths.resolve_toml_key_raw(Path.cwd(), key)
        if raw is None or not raw.strip():
            return None
        expanded = Path(raw).expanduser()
        values.append(expanded.as_posix().rstrip("/"))
    return values


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _configured_dirs(raw: str) -> list[str]:
    return [part for part in raw.split() if part]


def _is_dangling_symlink(path: Path) -> bool:
    """True for exactly the dangling-symlink shape: a symlink whose target is missing.

    Containment-scope guard (r1 F4): only this shape may be contained as a
    skip-and-warn. Every other OSError (unreadable regular file, permission
    denied, ...) propagates loudly and unchanged.
    """
    return path.is_symlink() and not path.exists()


def _iter_configured_files(root: Path, dirs: list[str]) -> list[Path]:
    found: list[Path] = []
    for rel_dir in dirs:
        base = root / rel_dir
        if not base.exists():
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for name in filenames:
                found.append(Path(dirpath) / name)
    return sorted(found, key=lambda item: item.as_posix())


def _same_content(left: Path, right: Path) -> bool:
    if left.is_symlink() or right.is_symlink():
        return (
            left.is_symlink()
            and right.is_symlink()
            and os.readlink(left) == os.readlink(right)
        )
    if not left.is_file():
        return False
    return _sha256(left) == _sha256(right)


def _copy_file(src: Path, dst: Path) -> None:
    """Copy seam: regular files via copy2, symlinks copied as links themselves."""
    if src.is_symlink():
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        os.symlink(os.readlink(src), dst)
        return
    shutil.copy2(src, dst)


def _verify_copy(src: Path, dst: Path) -> bool:
    """Verify seam: re-read the copy and compare against the source."""
    if src.is_symlink():
        return dst.is_symlink() and os.readlink(dst) == os.readlink(src)
    if dst.is_symlink() or not dst.is_file():
        return False
    return _sha256(dst) == _sha256(src)


# Receipt-proven same-run mirror replacement (plan
# 2026-10-24-closeout-migration-same-run-mirror-replace): the session
# manifest beside the baseline binds the stable run tuple (run_session_id,
# exact plan_path, registered run_worktree) and its task_boundary rows carry
# terminal mirror_status/mirror_receipts tokens. Parsing is fail-closed: a
# row carrying either token that cannot be parsed, an unknown row status, or
# an item whose path cannot be recovered invalidates run history (no
# replacement anywhere, never a fallback), while a malformed item with a
# recoverable path invalidates only that path. Rows without the tokens are
# legacy and ignored.

class _MirrorHistoryError(Exception):
    """Run-wide mirror-receipt history invalidation (fail-closed)."""


_MIRROR_ROW_STATUSES = ("complete", "partial", "skipped")
_MIRROR_ITEM_STATUSES = ("verified", "failed", "skipped")
_MIRROR_STATUS_TOKEN = "mirror_status="
_MIRROR_RECEIPTS_TOKEN = "mirror_receipts="


def _recoverable_mirror_path(path: object) -> bool:
    """True for a non-empty repository-relative path with no .. escape."""
    if not isinstance(path, str) or not path:
        return False
    if os.path.isabs(path):
        return False
    normalized = os.path.normpath(path)
    return normalized != ".." and not normalized.startswith("../")


def _parse_mirror_row(row: str) -> tuple[str, list] | None:
    """Split one task_boundary row into (status, receipt items); None for a
    legacy row without the tokens. Raises _MirrorHistoryError when the row
    carries either token but cannot be parsed to the terminal grammar."""
    status_idx = row.find(_MIRROR_STATUS_TOKEN)
    receipts_idx = row.find(_MIRROR_RECEIPTS_TOKEN)
    if status_idx == -1 and receipts_idx == -1:
        return None
    if status_idx == -1 or receipts_idx == -1 or receipts_idx < status_idx:
        raise _MirrorHistoryError("mirror tokens missing or out of order")
    cursor = status_idx + len(_MIRROR_STATUS_TOKEN)
    match = re.match(r"[A-Za-z]+", row[cursor:])
    if match is None:
        raise _MirrorHistoryError("mirror_status value missing")
    status = match.group(0)
    if status not in _MIRROR_ROW_STATUSES:
        raise _MirrorHistoryError(f"unknown mirror_status: {status}")
    rest = row[cursor + match.end():].lstrip()
    if not rest.startswith(_MIRROR_RECEIPTS_TOKEN):
        raise _MirrorHistoryError("terminal mirror_receipts token missing")
    payload = rest[len(_MIRROR_RECEIPTS_TOKEN):].strip()
    try:
        items = json.loads(payload)
    except ValueError as exc:
        raise _MirrorHistoryError(f"invalid mirror_receipts JSON: {exc}") from exc
    if not isinstance(items, list):
        raise _MirrorHistoryError("mirror_receipts is not a JSON array")
    return status, items


def _apply_mirror_items(items: list, proven: dict) -> None:
    """Fold one row's receipt items into the per-path map (a None value
    marks an invalidated path): a verified item updates the path, a
    failed/skipped item invalidates it, an absent path retains its history,
    and a complete row with no items changes no path. Raises
    _MirrorHistoryError for an item whose path cannot be recovered (run-wide
    invalidation)."""
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise _MirrorHistoryError("receipt item is not a JSON object")
        path = item.get("path")
        if not _recoverable_mirror_path(path):
            raise _MirrorHistoryError("receipt item path cannot be recovered")
        if path in seen:
            proven[path] = None
            continue
        seen.add(path)
        status = item.get("status")
        if status not in _MIRROR_ITEM_STATUSES or status in ("failed", "skipped"):
            proven[path] = None
            continue
        kind = item.get("type")
        if kind == "file":
            digest = item.get("sha256")
            proven[path] = (
                {"type": "file", "sha256": digest}
                if isinstance(digest, str) and digest
                else None
            )
        elif kind == "symlink":
            link_target = item.get("target")
            proven[path] = (
                {"type": "symlink", "target": link_target}
                if isinstance(link_target, str)
                else None
            )
        else:
            proven[path] = None


def _session_identity(manifest_text: str) -> dict[str, str]:
    """The manifest identity block's stable run tuple fields (first
    occurrence wins); only present, non-empty fields are returned."""
    identity: dict[str, str] = {}
    for line in manifest_text.splitlines():
        for key in ("run_session_id", "plan_path", "run_worktree"):
            prefix = key + ":"
            if key not in identity and line.startswith(prefix):
                value = line[len(prefix):].strip()
                if value:
                    identity[key] = value
    return identity


def _load_mirror_receipts(baseline_path: Path, source: Path) -> tuple[dict[str, dict], str | None]:
    """Receipt-proven per-path map from the session manifest beside the
    baseline, bound to the stable run tuple. Returns (receipts,
    run_session_id); an empty map authorizes no replacement, so missing or
    mismatched identity and run-wide history invalidation degrade to the
    plain foreign-rename behavior and never fall back to a partial
    authorization."""
    manifest_path = baseline_path.parent / "manifest.md"
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return {}, None
    identity = _session_identity(manifest_text)
    if set(identity) != {"run_session_id", "plan_path", "run_worktree"}:
        return {}, None
    if not _recoverable_mirror_path(identity["plan_path"]):
        return {}, None
    try:
        registered = Path(identity["run_worktree"]).resolve()
    except OSError:
        return {}, None
    if registered != source:
        return {}, None
    proven: dict[str, dict | None] = {}
    for line in manifest_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("task_boundary:"):
            continue
        try:
            parsed = _parse_mirror_row(stripped)
            if parsed is None:
                continue
            _apply_mirror_items(parsed[1], proven)
        except _MirrorHistoryError:
            return {}, None
    return {path: state for path, state in proven.items() if state is not None}, identity["run_session_id"]


def _target_matches_receipt(dst: Path, receipt: dict) -> bool:
    """True while the current target state still matches the receipt's
    recorded type and content (SHA-256 for a regular file, link target for
    a symlink); any read failure is a mismatch."""
    try:
        if receipt.get("type") == "file":
            if dst.is_symlink() or not dst.is_file():
                return False
            return _sha256(dst) == receipt.get("sha256")
        if receipt.get("type") == "symlink":
            return dst.is_symlink() and os.readlink(dst) == receipt.get("target")
    except OSError:
        return False
    return False


def _unique_sibling(dst: Path, marker: str) -> Path:
    candidate = dst.with_name(dst.name + marker)
    bump = 2
    while candidate.exists() or candidate.is_symlink():
        candidate = dst.with_name(dst.name + f"{marker}-{bump}")
        bump += 1
    return candidate


def _remove_quietly(path: Path) -> None:
    try:
        if path.is_symlink() or path.exists():
            path.unlink()
    except OSError:
        pass


def _install_staged(temp: Path, dst: Path) -> None:
    """Install seam: one atomic rename puts the staged sibling at the
    target, so a failed install never half-writes the target."""
    os.replace(temp, dst)


def _state_of(path: Path) -> dict:
    """The recorded content state of a path, in receipt grammar shapes."""
    if path.is_symlink():
        return {"type": "symlink", "target": os.readlink(path)}
    return {"type": "file", "sha256": _sha256(path)}


def _capture_prior_target(dst: Path, prior_tmp: Path) -> None:
    """Retain the prior target beside itself so a migration-manifest
    persistence failure can restore it atomically."""
    if dst.is_symlink():
        os.symlink(os.readlink(dst), prior_tmp)
    else:
        shutil.copy2(dst, prior_tmp)


def _replace_receipt_proven(
    src: Path, dst: Path, rel: str, receipt: dict, suffix: str, run_session_id: str
) -> tuple[str, dict]:
    """Stage, verify, recheck, and install one receipt-proven replacement.

    Returns ("replaced", payload) carrying the manifest entry plus the
    retained prior-target sibling (recoverable until the migration manifest
    holding the replaced disposition is atomically installed), ("foreign",
    {}) when the final recheck finds the target changed (the caller falls
    through to the existing foreign rename), or ("failed", failure_entry)
    when staging, verification, or installation failed; every failure path
    preserves the prior target and the source and removes the temporary
    siblings. Every read sits pre-install inside the guarded span, so no
    post-install abort can strand the retained prior sibling unrecorded."""
    temp = _unique_sibling(dst, f".repl-{suffix}.tmp")
    prior_tmp = _unique_sibling(dst, f".repl-{suffix}.prior-tmp")
    try:
        _copy_file(src, temp)
        if not _verify_copy(src, temp):
            raise ValueError("staged replacement failed checksum verification")
        if not _target_matches_receipt(dst, receipt):
            _remove_quietly(temp)
            return "foreign", {}
        prior_state = _state_of(dst)
        _capture_prior_target(dst, prior_tmp)
        # The incoming state is read from the staged sibling before the
        # install, inside the guarded span: the post-install span carries no
        # fallible read, so an abort after install can no longer strand the
        # retained prior sibling beside a replaced-but-unrecorded target.
        # The verified copy is byte-identical to what the install puts at
        # the target, so the recorded state is unchanged.
        incoming_state = _state_of(temp)
        _install_staged(temp, dst)
    except (OSError, ValueError) as exc:
        _remove_quietly(temp)
        _remove_quietly(prior_tmp)
        return "failed", {
            "source": rel,
            "destination": dst.as_posix(),
            "verified": False,
            "error": f"receipt replacement failed: {exc}",
        }
    except BaseException:
        _remove_quietly(temp)
        _remove_quietly(prior_tmp)
        raise
    entry = {
        "source": rel,
        "destination": dst.as_posix(),
        "verified": True,
        "run_session_id": run_session_id,
        "prior_state": prior_state,
        "incoming_state": incoming_state,
    }
    return "replaced", {"entry": entry, "prior_tmp": prior_tmp}


def _restore_prior_targets(priors: list[tuple[Path, Path]]) -> None:
    """Restore every replaced target from its retained prior sibling; the
    replaced disposition never became durable, so the prior state stands."""
    for dst, prior_tmp in priors:
        try:
            os.replace(prior_tmp, dst)
        except OSError as exc:
            print(f"ERROR: could not restore prior target {dst}: {exc}", file=sys.stderr)


def _discard_prior_targets(priors: list[tuple[Path, Path]]) -> None:
    for _dst, prior_tmp in priors:
        _remove_quietly(prior_tmp)


def _append_manifest(manifest_path: Path, sections: dict[str, list[dict]]) -> None:
    manifest: dict = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Run attribution stamp (plan
    # 2026-11-01-gate-removal-inherited-manifest-rows): when the sections
    # carry a `branch` list, the incoming run's branch record takes (or will
    # take) the position equal to the current length of the manifest's
    # `branch` list, and every appended row of every list section is stamped
    # with that index, so the removal gate can attribute each row to the
    # branch record it belongs to. A caller without a `branch` section (the
    # in-place no-op shape) appends unstamped, exactly as before; stamping
    # copies the row dicts, so the caller's own lists stay untouched and the
    # manifest stays append-only (nothing existing is rewritten or dropped).
    record_index: int | None = None
    if isinstance(sections.get("branch"), list):
        existing_branch = manifest.get("branch")
        record_index = len(existing_branch) if isinstance(existing_branch, list) else 0
    for key, entries in sections.items():
        if isinstance(entries, list):
            if record_index is not None:
                entries = [
                    {**entry, "record_index": record_index}
                    if isinstance(entry, dict)
                    else entry
                    for entry in entries
                ]
            manifest.setdefault(key, []).extend(entries)
        else:
            manifest[key] = entries
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic install: the manifest replaces its prior bytes in one rename,
    # so a failed persistence leaves the prior manifest intact and the
    # caller can restore the replaced targets against it.
    temp = manifest_path.with_name(manifest_path.name + f".tmp-{os.getpid()}")
    bump = 2
    while temp.exists() or temp.is_symlink():
        temp = manifest_path.with_name(manifest_path.name + f".tmp-{os.getpid()}-{bump}")
        bump += 1
    try:
        temp.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temp, manifest_path)
    except BaseException:
        _remove_quietly(temp)
        raise


# Boundary-mirror operation (plan
# 2026-10-24-closeout-migration-same-run-mirror-replace Task 2): the Step
# 1.4 record-mirror duty delegates its mirror and receipt work to this
# operation. One live process holds the worktree-closeout-migrate merge
# lock from its try-once acquire through every staged mirror install and
# the atomic task_boundary manifest-row replacement, so the boundary-mirror
# producer and the closeout-migration consumer serialize on the same
# repository key and the receipts the consumer reads are written by a
# lock-cooperating writer.

_BOUNDARY_TEMP_MARKER_PREFIX = ".bndmirror"


class _BoundaryMirrorInterrupt(BaseException):
    """A handled SIGINT/SIGTERM routed through the ordinary rollback and the
    token-fenced release; SIGKILL and power loss are outside this cleanup
    guarantee."""

    def __init__(self, signum: int) -> None:
        super().__init__(f"signal {signum}")
        self.signum = signum


_boundary_saved_handlers: dict[int, object] = {}


def _boundary_signal_raise(signum: int, _frame: object) -> None:
    raise _BoundaryMirrorInterrupt(signum)


def _install_boundary_signal_handlers() -> bool:
    """Arm the handled-signal bridge for the lock span; False when handlers
    cannot be installed (a non-main-thread caller keeps default handling)."""
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            _boundary_saved_handlers[sig] = signal.signal(sig, _boundary_signal_raise)
    except ValueError:
        _boundary_saved_handlers.clear()
        return False
    return True


def _restore_boundary_signal_handlers() -> None:
    for sig, previous in list(_boundary_saved_handlers.items()):
        try:
            signal.signal(sig, previous)
        except (ValueError, OSError, TypeError):
            pass
    _boundary_saved_handlers.clear()


_COMMIT_WINDOW_SIGNALS = (signal.SIGINT, signal.SIGTERM)


def _block_commit_window_signals() -> bool:
    """Block the handled signals across the manifest os.replace-to-commit
    pair (r2 F2): a signal delivered in that window stays pending until the
    matching unblock, so no handler can raise between the durable receipt
    row and the commit flag and roll back mirrors the row already records as
    verified. False when the platform has no pthread_sigmask (the window
    keeps its previous, unblocked behavior)."""
    try:
        signal.pthread_sigmask(signal.SIG_BLOCK, _COMMIT_WINDOW_SIGNALS)
        return True
    except (AttributeError, OSError, ValueError):
        return False


def _unblock_commit_window_signals() -> _BoundaryMirrorInterrupt | None:
    """Release the commit-window block after the restore-or-discard decision
    has run; a signal that arrived while blocked is delivered here, captured,
    and returned instead of unwinding the already-made decision."""
    try:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, _COMMIT_WINDOW_SIGNALS)
    except _BoundaryMirrorInterrupt as exc:
        return exc
    except (AttributeError, OSError, ValueError):
        pass
    return None


def _mirror_receipts_token(items: list) -> str:
    """Producer-side receipt token: compact JSON with every table pipe
    escaped as the six-character \\u007c sequence, the exact grammar the
    migration consumer parses."""
    text = json.dumps(items, separators=(",", ":"), ensure_ascii=True)
    return text.replace("|", "\\u007c")


def _boundary_row_line(note: str, status: str, items: list) -> str:
    """One task_boundary manifest row: the boundary's note, then the
    terminal mirror_status/mirror_receipts tokens."""
    stripped = note.strip()
    head = f"task_boundary: {stripped}; " if stripped else "task_boundary: "
    return head + f"mirror_status={status} mirror_receipts={_mirror_receipts_token(items)}"


def _manifest_with_row(base_text: str, row_line: str) -> str:
    if base_text and not base_text.endswith("\n"):
        base_text += "\n"
    return base_text + row_line + "\n"


def _replace_file_staged(path: Path, text: str, marker: str) -> None:
    """Build the complete file beside itself and atomically replace the
    prior bytes; a failure leaves the prior bytes intact and removes the
    staged sibling."""
    temp = _unique_sibling(path, marker)
    try:
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
    except BaseException:
        _remove_quietly(temp)
        raise


def _mirror_source_state(src: Path) -> dict:
    """The incoming mirror state in receipt grammar shapes; a symlink keeps
    its link target, anything else digests as a regular file (an unreadable,
    missing, or non-regular source surfaces as the open error its per-path
    handling reports)."""
    if src.is_symlink():
        return {"type": "symlink", "target": os.readlink(src)}
    return {"type": "file", "sha256": _sha256(src)}


def _restore_mirror_targets(priors: list[tuple[Path, Path | None]]) -> None:
    """Restore every installed mirror target: a captured prior replaces the
    target, an absent prior (a fresh install) removes it."""
    for dst, prior_tmp in priors:
        try:
            if prior_tmp is None:
                if dst.is_symlink() or dst.exists():
                    dst.unlink()
            else:
                os.replace(prior_tmp, dst)
        except OSError as exc:
            print(f"ERROR: could not restore prior target {dst}: {exc}", file=sys.stderr)


def _discard_mirror_targets(priors: list[tuple[Path, Path | None]]) -> None:
    for _dst, prior_tmp in priors:
        if prior_tmp is not None:
            _remove_quietly(prior_tmp)


def _boundary_mirror_install(
    worktree: Path, target: Path, paths: list[str], priors: list[tuple[Path, Path | None]]
) -> tuple[list[dict], int]:
    """Stage, verify, and atomically install each planned mirror beside its
    destination, capturing the prior target for the rollback span. A
    per-path copy error is contained the boundary's report-only way: the
    item records one failed status, the path's own prior target and
    temporaries are cleaned, and the loop continues. Every planned install
    appends its rollback-span entry (dst, prior sibling or None) to the
    caller's `priors` list before staging, so a handled-signal unwind
    between the append and the install still leaves the whole span - prior
    targets and fresh installs alike - addressable for the restore; a
    handled per-path failure removes its own entry. Returns (receipt items,
    failed count)."""
    items: list[dict] = []
    failed = 0
    marker = f"{_BOUNDARY_TEMP_MARKER_PREFIX}-{os.getpid()}"
    for rel in paths:
        src = worktree / rel
        dst = target / rel
        temp: Path | None = None
        prior_tmp: Path | None = None
        appended = False
        try:
            incoming = _mirror_source_state(src)
            if dst.is_symlink() or dst.exists():
                try:
                    current = _state_of(dst)
                except OSError:
                    current = None
                if current == incoming:
                    items.append({"path": rel, "status": "verified", **incoming})
                    continue
                prior_tmp = _unique_sibling(dst, f"{marker}.prior-tmp")
                _capture_prior_target(dst, prior_tmp)
            # The rollback-span entry rides `priors` from before the staging
            # onward (r2 F2), for fresh installs too (prior_tmp None, the
            # restore removes them): a handled signal raising anywhere
            # between this append and the install unwinds with the entry
            # addressable, so neither a replaced target nor a fresh install
            # can survive the rollback unaddressed.
            priors.append((dst, prior_tmp))
            appended = True
            dst.parent.mkdir(parents=True, exist_ok=True)
            temp = _unique_sibling(dst, f"{marker}.tmp")
            _copy_file(src, temp)
            if not _verify_copy(src, temp):
                raise ValueError("staged mirror failed verification")
            _install_staged(temp, dst)
        except (OSError, ValueError) as exc:
            if temp is not None:
                _remove_quietly(temp)
            if appended:
                # Handled per-path failure: no install happened for this
                # path, so its entry comes back off the rollback span and
                # the prior sibling is removed. A BaseException (the
                # _BoundaryMirrorInterrupt) keeps piercing this containment
                # unchanged, leaving the entry in place for the caller's
                # restore.
                priors.remove((dst, prior_tmp))
                if prior_tmp is not None:
                    _remove_quietly(prior_tmp)
            items.append({"path": rel, "status": "failed"})
            failed += 1
            print(f"boundary-mirror: copy error: {rel}: {exc}", file=sys.stderr)
            continue
        except BaseException:
            # A handled signal (the _BoundaryMirrorInterrupt BaseException)
            # keeps piercing the per-path containment unchanged; the unwind
            # only removes this path's staged sibling. The rollback-span
            # entry and any captured prior sibling stay: the caller's
            # restore consumes them.
            if temp is not None:
                _remove_quietly(temp)
            raise
        items.append({"path": rel, "status": "verified", **incoming})
    return items, failed


def cmd_boundary_mirror(args: argparse.Namespace) -> int:
    """One boundary's mirror-and-receipt transaction: try-once acquire the
    worktree-closeout-migrate merge lock, install the planned mirrors, then
    atomically replace the session manifest with the complete receipt row,
    all in this one live process, releasing in an always-run finally."""
    worktree = Path(args.worktree).resolve()
    target = Path(args.target).resolve()
    manifest_path = Path(args.manifest)
    paths = list(args.mirror_path)
    note = args.boundary_note.strip()
    if "\n" in note or "\r" in note:
        print("ERROR: --boundary-note must be a single line", file=sys.stderr)
        return 2
    # Producer validation (r2 F1): the note text is embedded verbatim before
    # the terminal tokens, and the consumer's row parser keys on the first
    # mirror_status=/mirror_receipts= occurrence, so a note carrying either
    # substring would forge or corrupt the receipt grammar. Refuse it before
    # any lock or copy work instead of writing an unparsable row.
    for token in (_MIRROR_STATUS_TOKEN, _MIRROR_RECEIPTS_TOKEN):
        if token in note:
            print(
                f"ERROR: --boundary-note must not contain {token!r}; the "
                "operation appends the terminal mirror tokens itself",
                file=sys.stderr,
            )
            return 2
    if len(set(paths)) != len(paths):
        print("ERROR: --mirror-path entries must be unique", file=sys.stderr)
        return 2
    for rel in paths:
        if not _recoverable_mirror_path(rel):
            print(f"ERROR: --mirror-path must be a repository-relative path: {rel!r}", file=sys.stderr)
            return 2
    expected = {
        "run_session_id": args.run_session_id.strip(),
        "plan_path": args.plan_path.strip(),
        "run_worktree": args.run_worktree.strip(),
    }
    for key, value in expected.items():
        if not value:
            print(f"ERROR: --{key.replace('_', '-')} must not be empty", file=sys.stderr)
            return 2
    if not _recoverable_mirror_path(expected["plan_path"]):
        print(f"ERROR: --plan-path must be a repository-relative path: {expected['plan_path']!r}", file=sys.stderr)
        return 2
    try:
        base_text = manifest_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read the session manifest {manifest_path}: {exc}", file=sys.stderr)
        return 2
    identity = _session_identity(base_text)
    if (
        identity.get("run_session_id") != expected["run_session_id"]
        or identity.get("plan_path") != expected["plan_path"]
    ):
        print(
            "ERROR: the session manifest's stable tuple does not match the "
            f"invocation (manifest run_session_id {identity.get('run_session_id')!r} "
            f"/ plan_path {identity.get('plan_path')!r}, invocation "
            f"{expected['run_session_id']!r} / {expected['plan_path']!r})",
            file=sys.stderr,
        )
        return 2
    try:
        registered = Path(identity.get("run_worktree", "")).resolve()
        invoked = Path(expected["run_worktree"]).resolve()
    except OSError as exc:
        print(f"ERROR: cannot resolve the registered run worktree: {exc}", file=sys.stderr)
        return 2
    if registered != invoked:
        print(
            "ERROR: the registered run worktree "
            f"{identity.get('run_worktree')!r} does not resolve to the invoked "
            f"--run-worktree {expected['run_worktree']!r}",
            file=sys.stderr,
        )
        return 2
    manifest_marker = f"{_BOUNDARY_TEMP_MARKER_PREFIX}-{os.getpid()}.manifest-tmp"
    started = time.monotonic()
    exports: dict[str, str] | None = None
    # The guarded-state flags are initialized before the merge-lock acquire
    # so that, once the lock is held, the try whose finally releases it
    # begins immediately: a signal landing in a statement gap between
    # acquire and try would otherwise terminate the run with the lock held
    # until the dead-holder grace.
    commit = False
    interrupted: _BoundaryMirrorInterrupt | None = None
    failure: Exception | None = None
    items: list[dict] = []
    priors: list[tuple[Path, Path | None]] = []
    failed_count = 0
    handlers_armed = False
    commit_window_blocked = False
    if _target_is_git_repository(target):
        exports, refused = _merge_lock_acquire(target, _MIGRATE_MERGE_LABEL)
        if exports is None:
            # Report-only contention: copy no primary files, record one
            # skipped item per planned path with no verified receipt, and
            # let the boundary continue.
            for line in refused:
                print(f"boundary-mirror: merge-lock: {line}", file=sys.stderr)
            row = _boundary_row_line(
                note, "skipped", [{"path": rel, "status": "skipped"} for rel in paths]
            )
            try:
                _replace_file_staged(manifest_path, _manifest_with_row(base_text, row), manifest_marker)
            except OSError as exc:
                print(f"ERROR: boundary-mirror could not record the skipped row: {exc}", file=sys.stderr)
                return 1
            print(
                "boundary-mirror: skipped (merge lock held by another writer); "
                f"no primary files copied; {len(paths)} planned path(s) recorded skipped."
            )
            return 0
    else:
        print(
            "boundary-mirror: merge-lock skipped (the target is not a git "
            "repository; the repository-keyed merge lock has no key here)",
            file=sys.stderr,
        )
    try:
        handlers_armed = _install_boundary_signal_handlers()
        try:
            items, failed_count = _boundary_mirror_install(worktree, target, paths, priors)
            row = _boundary_row_line(note, "complete" if failed_count == 0 else "partial", items)
            # r2 F2: the handled signals stay blocked from the manifest
            # os.replace through the commit flag, so a signal delivered in
            # that window cannot raise between the durable row and
            # `commit = True` and roll back mirrors the durable row already
            # records as verified. The pending signal surfaces at the
            # unblock inside the finally, after the decision.
            commit_window_blocked = _block_commit_window_signals()
            _replace_file_staged(manifest_path, _manifest_with_row(base_text, row), manifest_marker)
            commit = True
        except _BoundaryMirrorInterrupt as exc:
            interrupted = exc
        except Exception as exc:
            failure = exc
        finally:
            # Prior targets stay recoverable until the complete receipt row
            # is durably installed; a receipt-write or handled-signal failure
            # restores them, a durable row discards them. The decision runs
            # while the commit-window block (when taken) still holds; the
            # pending signal, if any, is released and captured afterwards.
            if commit:
                _discard_mirror_targets(priors)
            else:
                _restore_mirror_targets(priors)
            if commit_window_blocked:
                commit_window_blocked = False
                interrupted = _unblock_commit_window_signals() or interrupted
    finally:
        if handlers_armed:
            _restore_boundary_signal_handlers()
        if exports is not None:
            _migrate_merge_lock_release(target, exports, started)
    if interrupted is not None:
        if commit:
            print(
                f"boundary-mirror: interrupted (signal {interrupted.signum}) after the "
                "receipt row was durable; the mirrors and row stand.",
                file=sys.stderr,
            )
            # A durable row stands, but a failed path is still a failed path:
            # the interrupted exit honors the failed count like the ordinary
            # complete exit does.
            return 1 if failed_count else 0
        print(
            f"boundary-mirror: interrupted (signal {interrupted.signum}); prior primary "
            "targets and prior manifest bytes restored, sources retained, lock released.",
            file=sys.stderr,
        )
        return 1
    if failure is not None:
        print(
            f"ERROR: boundary-mirror rolled back: {type(failure).__name__}: {failure}; "
            "prior primary targets and prior manifest bytes restored, sources retained.",
            file=sys.stderr,
        )
        return 1
    verified = sum(1 for item in items if item["status"] == "verified")
    print(
        f"boundary-mirror: {'complete' if failed_count == 0 else 'partial'}; "
        f"verified {verified}, failed {failed_count}; row appended at {manifest_path}."
    )
    return 1 if failed_count else 0


def cmd_capture(args: argparse.Namespace) -> int:
    if args.dirs:
        dirs = _configured_dirs(args.dirs)
    else:
        resolved = _facts_dirs()
        if resolved is None:
            print(
                "ERROR: cannot resolve the capture dirs from "
                ".ai-playbook/facts.md (reviews_dir, tmp_dir, metrics_dir, "
                "review_certs_dir); pass --dirs or complete the facts block",
                file=sys.stderr,
            )
            return 2
        dirs = resolved
    root = Path.cwd()
    files: dict[str, str] = {}
    skipped: list[dict] = []
    # The capture time is recorded before the source walk (plan Terms: the
    # UTC time when the baseline capture starts walking its configured
    # paths), so it describes the baseline operation rather than the later
    # baseline-file write.
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for path in _iter_configured_files(root, dirs):
        rel = path.relative_to(root).as_posix()
        # Every OSError from the per-file digest read is contained the same
        # way: a dangling symlink (open raises FileNotFoundError), a
        # permission-denied regular file, any other unreadable shape. The
        # path is named on stderr, recorded under "skipped", and the
        # capture exit stays 0.
        try:
            files[rel] = _sha256(path)
        except OSError as exc:
            reason = f"{type(exc).__name__}: {exc}"
            print(
                f"WARN: capture: skipping unreadable path {rel}: {reason}",
                file=sys.stderr,
            )
            skipped.append({"path": rel, "reason": reason})
            continue
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"captured_at": captured_at, "dirs": dirs, "files": files, "skipped": skipped},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Captured {len(files)} file(s) under {len(dirs)} dir(s) into {out} "
        f"(checkout: {root})."
    )
    return 0


def _head_blob(repo: Path, rel: str) -> str | None:
    """The committed blob id for one repo-relative path at HEAD; None when
    the path is absent at HEAD or the git probe fails."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"HEAD:{rel}"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _blob_in_head_history(repo: Path, rel: str, blob: str) -> bool:
    """True when the blob id appears in the path's committed history at HEAD
    (an older committed vintage of the file). The probe is name-scoped (no
    --follow): vintages committed under a previous path name before a rename
    onto this path are not seen, a conservative miss."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "log", "--format=%H", "-n", "1",
         "--find-object", blob, "HEAD", "--", rel],
        capture_output=True, text=True,
    )
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _worktree_blob(repo: Path, path: Path) -> str | None:
    """The blob id one worktree file's bytes hash to inside the repository's
    object database; None when the hash probe fails."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "--", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _unchanged_since_baseline(src: Path, rel: str, baseline_files: dict[str, str]) -> bool:
    """The carry loop's baseline-identical skip rule, shared with the clobber
    pre-flight so both surfaces evaluate one path set (entry closeout-
    migrate-baseline-tracked-clobber r1)."""
    return rel in baseline_files and _sha256(src) == baseline_files[rel]


def _baseline_clobber_preflight(
    source: Path, target: Path, dirs: list[str], baseline_files: dict[str, str],
) -> list[str]:
    """Backward-move pre-flight (entry closeout-migrate-baseline-tracked-
    clobber): return the would-carry paths tracked at the target's HEAD whose
    source bytes differ from the committed HEAD bytes - the whole-file carries
    that would overwrite destination content. Byte-identical and HEAD-absent
    paths never offend; the walk mirrors the carry loop's own skip rule."""
    offenders: list[str] = []
    for src in _iter_configured_files(source, dirs):
        rel = src.relative_to(source).as_posix()
        if _is_dangling_symlink(src) or not src.exists():
            continue
        if _unchanged_since_baseline(src, rel, baseline_files):
            continue
        head_blob = _head_blob(target, rel)
        if head_blob is None:
            continue
        src_blob = _worktree_blob(target, src)
        if src_blob is None or src_blob == head_blob:
            continue
        offenders.append(rel)
    return offenders


def _prevent_tracked_clobbers(target: Path, owned: set[str]) -> list[str]:
    """Post-run staged-set ownership check (entry closeout-migrate-baseline-
    tracked-clobber): a staged tracked entry whose staged bytes are an older
    committed vintage of the file and that this run carried is the
    between-snapshot rewind - restore it from HEAD and report it as a
    prevented clobber. Staged entries this run did not carry are foreign
    work: reported, never touched. Returns the prevented paths. Vintage
    detection is its own small probe beside the concept owner
    scripts/revert_set_classifier.py; the report lines borrow that
    classifier's foreign-versus-reversal vocabulary."""
    prevented: list[str] = []
    proc = subprocess.run(
        ["git", "-C", str(target), "diff", "--cached", "--name-only", "-z"],
        capture_output=True,
    )
    if proc.returncode != 0:
        print(
            f"WARN: post-run staged-set read failed: "
            f"{proc.stderr.decode(errors='replace').strip()}",
            file=sys.stderr,
        )
        return prevented
    for raw in proc.stdout.split(b"\0"):
        rel = os.fsdecode(raw)
        if not rel:
            continue
        staged_proc = subprocess.run(
            ["git", "-C", str(target), "rev-parse", f":{rel}"],
            capture_output=True, text=True,
        )
        staged_blob = staged_proc.stdout.strip() if staged_proc.returncode == 0 else None
        if staged_blob is None:
            # A staged deletion (the rewind deleting the entry outright) has
            # no index blob to compare: an owned deletion is the same
            # between-snapshot rewind in its most destructive shape and
            # restores from HEAD; a foreign deletion is reported and never
            # touched.
            if rel in owned:
                restore = subprocess.run(
                    ["git", "-C", str(target), "restore", "--source=HEAD",
                     "--staged", "--worktree", "--", rel],
                    capture_output=True, text=True,
                )
                if restore.returncode == 0:
                    prevented.append(rel)
                    print(
                        f"prevented clobber: {rel} (staged deletion of a "
                        "tracked file this run carried; restored from HEAD)"
                    )
                else:
                    print(
                        f"WARN: prevented-clobber restore failed for {rel}: "
                        f"{restore.stderr.strip()}",
                        file=sys.stderr,
                    )
            else:
                print(
                    f"prevented-clobber check: {rel} is a staged deletion "
                    "this run did not carry (foreign staged work); "
                    "left untouched"
                )
            continue
        head_blob = _head_blob(target, rel)
        if head_blob is None or staged_blob == head_blob:
            continue
        if _blob_in_head_history(target, rel, staged_blob):
            if rel in owned:
                # Compare-then-act: re-read the staged blob immediately
                # before the restore so a peer restaging the path between
                # the classification read and this point downgrades to a
                # report-only pass instead of dropping their bytes.
                recheck = subprocess.run(
                    ["git", "-C", str(target), "rev-parse", f":{rel}"],
                    capture_output=True, text=True,
                )
                if recheck.returncode != 0 or recheck.stdout.strip() != staged_blob:
                    print(
                        f"prevented-clobber check: {rel} changed under the "
                        "guard between classification and restore; left "
                        "untouched"
                    )
                    continue
                restore = subprocess.run(
                    ["git", "-C", str(target), "restore", "--source=HEAD",
                     "--staged", "--worktree", "--", rel],
                    capture_output=True, text=True,
                )
                if restore.returncode == 0:
                    prevented.append(rel)
                    print(
                        f"prevented clobber: {rel} (staged bytes are an older "
                        "committed vintage of a tracked file this run carried; "
                        "restored from HEAD)"
                    )
                else:
                    print(
                        f"WARN: prevented-clobber restore failed for {rel}: "
                        f"{restore.stderr.strip()}",
                        file=sys.stderr,
                    )
            else:
                print(
                    f"prevented-clobber check: {rel} holds a rewound staged "
                    "vintage this run did not carry (foreign staged work); "
                    "left untouched for the operator's revert-set machinery"
                )
        elif rel not in owned:
            print(
                f"prevented-clobber check: {rel} is staged outside this run's "
                "carried outputs (foreign staged work); left untouched"
            )
    return prevented


def cmd_migrate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    if manifest_path.exists():
        try:
            json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            print(
                f"closeout manifest exists and is not JSON: {manifest_path}",
                file=sys.stderr,
            )
            return 2
    # The baseline-less scoped arm (plan 2026-10-29-done-gate-report-retention
    # Task 3): the explicitly captured scoped inventory replaces the baseline
    # operand. The inventory is validated before the lock span (nothing is
    # copied on an invalid operand, the same posture as the baseline
    # refusals), and no baseline is read or fabricated.
    scoped_files: list[str] | None = None
    baseline: dict = {}
    if args.inventory is not None:
        inventory_path = Path(args.inventory)
        try:
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(
                f"ERROR: scoped inventory unreadable: {inventory_path} ({exc})",
                file=sys.stderr,
            )
            return 2
        raw_files = inventory.get("files") if isinstance(inventory, dict) else None
        if not isinstance(raw_files, list) or not all(
            _recoverable_mirror_path(item) for item in raw_files
        ):
            print(
                "ERROR: scoped inventory must be a JSON object whose 'files' "
                "is a list of worktree-relative paths without '..' escapes: "
                f"{inventory_path}",
                file=sys.stderr,
            )
            return 2
        scoped_files = list(raw_files)
    else:
        baseline_path = Path(args.baseline)
        if not baseline_path.is_file():
            print(
                f"ERROR: baseline file not found: {baseline_path}",
                file=sys.stderr,
            )
            print(
                "Refusing to continue with an implicit empty baseline; "
                "run capture first, otherwise pre-existing artifacts would be silently skipped.",
                file=sys.stderr,
            )
            print(
                "remedy: check the primary checkout's session dir of the same "
                "slug for closeout-baseline.json (a Phase 0 capture can land "
                "there after a shell cwd reset) and copy it in before "
                "recapturing; a recapture here is a late baseline and is "
                "recorded as a capture-failure deviation",
                file=sys.stderr,
            )
            return 2
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        dirs = baseline.get("dirs")
        if not dirs:
            print(
                "ERROR: baseline lacks dirs; re-capture with a facts-resolved "
                "capture (or an explicit --dirs) instead of migrating against "
                "a guessed dir set",
                file=sys.stderr,
            )
            return 2
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    # Baseline clobber pre-flight (entry closeout-migrate-baseline-tracked-
    # clobber): a whole-file baseline carry must never overwrite a
    # destination-tracked file whose committed HEAD bytes differ from the
    # carried bytes - that overwrite is the witnessed rewind mechanism. The
    # refusal runs before the merge-lock span, names every offending path,
    # and copies nothing. The scoped-inventory route has no baseline and a
    # non-git target has no committed bytes to compare against, so the guard
    # is inert on both.
    if scoped_files is None and _target_is_git_repository(target):
        offenders = _baseline_clobber_preflight(
            source, target, dirs, baseline.get("files", {})
        )
        if offenders:
            for rel in offenders:
                print(
                    "ERROR: baseline clobber pre-flight: "
                    f"{rel} is tracked at the target HEAD with different "
                    "bytes; carrying it would overwrite destination content",
                    file=sys.stderr,
                )
            print(
                "ERROR: refusing the baseline-relative migrate: narrow the "
                "capture dirs to untracked session surfaces and re-capture "
                "the baseline before migrating (a plain re-capture over the "
                "current dir set re-freezes this checkout's bytes and the "
                "retry would carry nothing)",
                file=sys.stderr,
            )
            return 2
    # The runner-owned merge-lock span (plan 2026-10-10-done-closeout-lock-span
    # Task 1): the migration holds the repository-keyed merge lock inside this
    # process for its own runtime, with a bounded wait under its own label; the
    # exports are parsed in-process and the release runs in the always-run
    # finally below. A target that is not a git repository has no
    # repository-keyed lock to take (the merge family refuses non-repo hosts),
    # so the span is skipped there with one named line.
    merge_exports: dict[str, str] | None = None
    merge_started = time.monotonic()
    if _target_is_git_repository(target):
        try:
            max_wait = _migrate_merge_max_wait()
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        merge_exports, refused = _merge_lock_wait_acquire(target, _MIGRATE_MERGE_LABEL, max_wait)
        if merge_exports is None:
            for line in refused:
                print(f"merge-lock: {line}", file=sys.stderr)
            print(
                "ERROR: merge lock acquire refused after the bounded wait; "
                "the migration copied nothing and the source files remain in place",
                file=sys.stderr,
            )
            return 2
    else:
        print(
            "merge-lock: skipped (the migration target is not a git "
            "repository; the repository-keyed merge lock has no key here)",
            file=sys.stderr,
        )
    try:
        return _cmd_migrate_transfer(args, source, target, baseline, scoped_files)
    finally:
        if merge_exports is not None:
            _migrate_merge_lock_release(target, merge_exports, merge_started)


def _print_zero_delta_report(source: Path, dirs: list[str], baseline: dict, baseline_path: Path) -> None:
    """Zero-delta distinguishability report (warning-only; entry
    closeout-migrate-zero-delta-silence): a zero-result migrate is ambiguous
    between a correctly empty delta and a baseline that postdates the run
    edits (the late-capture shape that strands run-era records); naming the
    baseline's recorded captured_at against the newest configured-dir file
    mtime lets the closeout reader adjudicate the two readings in the
    tool's own output. The baseline file itself is excluded from the mtime
    walk (capture writes it after walking the source paths), a legacy
    baseline whose captured_at is absent or unreadable reports its capture
    time as unknown rather than borrowing the baseline file's mtime, and
    the report never changes the exit code."""
    try:
        excluded = baseline_path.resolve()
    except OSError:
        excluded = None
    newest: tuple[float, str] | None = None
    for path in _iter_configured_files(source, dirs):
        if excluded is not None:
            try:
                is_baseline = path.resolve() == excluded
            except OSError:
                is_baseline = False
            if is_baseline:
                continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if newest is None or mtime > newest[0]:
            newest = (mtime, path.relative_to(source).as_posix())
    if newest is None:
        print(
            "WARNING: zero-delta report: no readable files found under the configured "
            f"dirs ({', '.join(dirs)}); a correctly empty delta and a mis-resolved dir "
            "set are indistinguishable here; re-derive the run's owned paths before "
            "teardown",
            file=sys.stderr,
        )
        return
    newest_iso = datetime.fromtimestamp(newest[0], timezone.utc).isoformat(
        timespec="seconds"
    )
    captured_at = baseline.get("captured_at")
    captured: datetime | None = None
    if isinstance(captured_at, str):
        try:
            captured = datetime.fromisoformat(captured_at)
        except ValueError:
            captured = None
    if captured is None:
        print(
            "WARNING: zero-delta report: baseline capture time unknown (a legacy "
            "baseline without a readable captured_at); newest file mtime "
            f"{newest_iso} ({newest[1]}); the postdates/predates comparison cannot "
            "run; re-derive the run's owned paths before teardown (manual-delta-carry "
            "remedy per the Worktree-first standard's closeout migration paragraph)",
            file=sys.stderr,
        )
        return
    # A naive captured_at (never written by capture) reads as UTC, and both
    # sides compare at the whole-second granularity the report prints, so
    # the verdict always matches the printed timestamps.
    if captured.tzinfo is None:
        captured = captured.replace(tzinfo=timezone.utc)
    newest_dt = datetime.fromtimestamp(newest[0], timezone.utc).replace(microsecond=0)
    if newest_dt > captured:
        print(
            f"WARNING: zero-delta report: newest file mtime {newest_iso} ({newest[1]}) "
            f"postdates the baseline capture {captured_at}; the empty delta reflects "
            "content the baseline never saw being touched without a digest change; "
            "re-derive the run's owned paths before teardown (manual-delta-carry remedy "
            "per the Worktree-first standard's closeout migration paragraph)",
            file=sys.stderr,
        )
    else:
        print(
            f"WARNING: zero-delta report: newest file mtime {newest_iso} ({newest[1]}) predates "
            f"the baseline capture {captured_at}; this signature fits both a correctly "
            "empty delta and a baseline that postdates the run edits (a late capture "
            "absorbs run-era records and migrates nothing); adjudicate against the "
            "run's owned paths before teardown, the manual-delta-carry remedy applying "
            "when the baseline postdates the edits",
            file=sys.stderr,
        )


def _cmd_migrate_transfer(
    args: argparse.Namespace,
    source: Path,
    target: Path,
    baseline: dict,
    scoped_files: list[str] | None = None,
) -> int:
    manifest_path = Path(args.manifest)
    if source == target:
        print(
            "No-op: source and target are the same worktree; nothing copied (in-place closeout).",
            file=sys.stderr,
        )
        _append_manifest(
            manifest_path,
            {"noop": [{"note": "source equals target; in-place no-op, nothing copied"}]},
        )
        return 0

    # The scoped arm (plan 2026-10-29-done-gate-report-retention Task 3)
    # carries no baseline: no dirs enumeration, no baseline-skip comparison,
    # and no mirror receipts (no baseline sibling exists, so a collision
    # takes the plain foreign-rename disposition).
    dirs = None if scoped_files is not None else baseline.get("dirs")
    baseline_files: dict[str, str] = {} if scoped_files is not None else baseline.get("files", {})
    # Exact-branch binding (plan done-closeout-ceremony-friction Task 3):
    # the manifest records the source worktree's branch at transfer time, so
    # the removal gate can verify the identity at removal time (the
    # gate-removal pass reuses this record; a detached or non-git source
    # records an unresolved branch and the gate's legacy skip applies).
    branch_head = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    )
    branch_name = branch_head.stdout.strip() if branch_head.returncode == 0 else ""
    if branch_name and branch_name != "HEAD":
        branch_record: dict = {"branch": branch_name, "source": str(source)}
    else:
        branch_record = {
            "branch": None,
            "source": str(source),
            "note": "branch unresolved (non-git source or detached HEAD)",
        }
    migrated: list[dict] = []
    renamed: list[dict] = []
    replaced: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    # Staged tracked entries the post-run guard restored from HEAD (entry
    # closeout-migrate-baseline-tracked-clobber); recorded in the manifest.
    prevented: list[dict] = []
    # Prior-target siblings retained by replacements until the migration
    # manifest carrying their replaced disposition is atomically installed.
    priors: list[tuple[Path, Path]] = []
    # Receipt-proven same-run mirrors (plan
    # 2026-10-24-closeout-migration-same-run-mirror-replace): loaded inside
    # the lock span, consulted at a different-byte collision (the
    # replacement, rechecked immediately before the atomic install) and at a
    # byte-identical target (the verified migrated row the receipt backs,
    # plan 2026-10-30-execute-plan-teardown-staging-record-mirror Task 2).
    if scoped_files is not None:
        receipts: dict[str, dict] = {}
        run_session_id = None
    else:
        receipts, run_session_id = _load_mirror_receipts(Path(args.baseline), source)
    # Manifest durability: the sections accumulate in memory and the
    # manifest is written in a finally block, so a mid-loop abort still
    # records every entry earned so far, plus an "interrupted": true marker
    # and an incomplete entry naming the error, before the failure
    # propagates unchanged.
    aborted: BaseException | None = None
    persist_failure: BaseException | None = None
    try:
        if scoped_files is not None:
            # One-for-one expectation: every inventory item names exactly one
            # expected transfer, in the captured order.
            candidates: list[tuple[Path, str]] = [
                (source / rel, rel) for rel in scoped_files
            ]
        else:
            candidates = [
                (src, src.relative_to(source).as_posix())
                for src in _iter_configured_files(source, dirs)
            ]
        for src, rel in candidates:
            if scoped_files is not None:
                # A missing expected source fails the item (and the
                # transaction): never a silent omission, never a verified row.
                if not src.is_file():
                    failed.append(
                        {
                            "source": rel,
                            "destination": (target / rel).as_posix(),
                            "verified": False,
                            "error": "missing source",
                        }
                    )
                    continue
            elif _is_dangling_symlink(src):
                print(f"WARN: skipping dangling symlink: {src}", file=sys.stderr)
                skipped.append(
                    {
                        "source": rel,
                        "reason": "dangling symlink; target missing; skipped without copying",
                    }
                )
                continue
            if _unchanged_since_baseline(src, rel, baseline_files):
                continue
            dst = target / rel
            collision_dst_digest = None
            if dst.exists() or dst.is_symlink():
                if _same_content(dst, src):
                    if scoped_files is not None:
                        # The expected transfer already stands at the target
                        # with identical bytes: record the verified migrated
                        # destination (the skipped disposition would leave the
                        # gate's presence check and the sweep's retention with
                        # no reference) without rewriting identical bytes.
                        migrated.append(
                            {
                                "source": rel,
                                "destination": dst.as_posix(),
                                "verified": True,
                            }
                        )
                        continue
                    receipt = receipts.get(rel)
                    if receipt is not None and _target_matches_receipt(dst, receipt):
                        # A byte-identical target covered by the exact path's
                        # valid same-run mirror receipt is a verified transfer:
                        # the receipt (verified against the target's current
                        # digest, the same check the replacement path uses)
                        # proves the primary copy carries the mirrored state,
                        # so the verified migrated row - the skipped row would
                        # leave the removal gate's presence check with no
                        # reference - records it without rewriting identical
                        # bytes. A path with no valid receipt keeps the
                        # skipped row unchanged.
                        migrated.append(
                            {
                                "source": rel,
                                "destination": dst.as_posix(),
                                "verified": True,
                            }
                        )
                        continue
                    skipped.append(
                        {
                            "source": rel,
                            "destination": dst.as_posix(),
                            "reason": "target byte-identical; skipped without rename or rewrite",
                            "verified": True,
                        }
                    )
                    continue
                receipt = receipts.get(rel)
                if receipt is not None and _target_matches_receipt(dst, receipt):
                    status, payload = _replace_receipt_proven(
                        src, dst, rel, receipt, args.suffix, run_session_id
                    )
                    if status == "replaced":
                        replaced.append(payload["entry"])
                        priors.append((dst, payload["prior_tmp"]))
                        print(f"REPLACED: {rel} (receipt-proven same-run mirror)")
                        continue
                    if status == "failed":
                        failed.append(payload)
                        continue
                try:
                    collision_dst_digest = _sha256(dst)
                except OSError:
                    collision_dst_digest = "unreadable"
                candidate = dst.with_name(dst.stem + f".wt-{args.suffix}" + dst.suffix)
                bump = 2
                while candidate.exists() or candidate.is_symlink():
                    candidate = dst.with_name(
                        dst.stem + f".wt-{args.suffix}-{bump}" + dst.suffix
                    )
                    bump += 1
                dst = candidate
            dst.parent.mkdir(parents=True, exist_ok=True)
            _copy_file(src, dst)
            if _verify_copy(src, dst):
                entry = {
                    "source": rel,
                    "destination": dst.as_posix(),
                    "verified": True,
                }
                if dst.name != Path(rel).name:
                    entry["collision_renamed"] = True
                    renamed.append(entry)
                    print(
                        f"COLLISION: {rel} -> {dst.as_posix()} "
                        f"(incoming {_sha256(src)[:12]} / existing {collision_dst_digest[:12]})"
                    )
                else:
                    migrated.append(entry)
            else:
                failed.append(
                    {
                        "source": rel,
                        "destination": dst.as_posix(),
                        "verified": False,
                        "error": "checksum mismatch after copy",
                    }
                )
    except BaseException as exc:
        aborted = exc
        raise
    finally:
        # Post-run staged-set ownership check (entry closeout-migrate-
        # baseline-tracked-clobber): a between-snapshot rewind - HEAD moving
        # after the pre-flight read - lands as a staged older vintage of a
        # tracked path this run carried; restore it before the closeout's own
        # staging can seal it in. Skipped on an aborted loop and on non-git
        # targets (no index to read).
        if aborted is None and _target_is_git_repository(target):
            # The guard walks repo-relative staged names while the manifest
            # destinations are absolute: normalize the carried set into the
            # target-relative names the staged-set read produces, so the
            # ownership comparison compares like with like.
            prefix = target.as_posix() + "/"
            owned_rels = {
                dest[len(prefix):]
                for dest in {entry["destination"] for entry in migrated}
                | {entry["destination"] for entry in replaced}
                if dest.startswith(prefix)
            }
            for rel in _prevent_tracked_clobbers(target, owned_rels):
                prevented.append(
                    {
                        "destination": (target / rel).as_posix(),
                        "action": "restored-from-HEAD",
                    }
                )
        sections: dict[str, list[dict]] = {
            "migrated": migrated,
            "renamed": renamed,
            "replaced": replaced,
            "skipped": skipped,
            "failed": failed,
            "branch": [branch_record],
            "prevented_clobbers": prevented,
        }
        if aborted is not None:
            sections["interrupted"] = True
            sections["incomplete"] = [
                {
                    "error": f"{type(aborted).__name__}: {aborted}",
                    "note": "migration aborted mid-loop; entries recorded above are durable",
                }
            ]
        try:
            _append_manifest(manifest_path, sections)
        except BaseException as exc:
            persist_failure = exc
            # The replaced disposition never became durable: restore every
            # prior target against the intact prior manifest and fail.
            _restore_prior_targets(priors)
        else:
            _discard_prior_targets(priors)
    if persist_failure is not None:
        print(
            f"ERROR: migration manifest persistence failed ({persist_failure}); "
            "replaced targets restored, prior manifest intact, sources retained",
            file=sys.stderr,
        )
        return 1
    for entry in failed:
        print(
            f"ERROR: verification failed for {entry['source']} -> {entry['destination']}: {entry['error']}",
            file=sys.stderr,
        )
    if failed:
        print(
            f"ERROR: {len(failed)} file(s) failed copy verification; "
            "source files were copied, never moved, and remain in place.",
            file=sys.stderr,
        )
        return 1
    print(
        f"Migrated {len(migrated)} file(s), renamed {len(renamed)} on collision, "
        f"replaced {len(replaced)}, skipped {len(skipped)} identical; manifest at {manifest_path}."
    )
    # Trigger scope (plan Terms): zero-delta means no copied, no
    # collision-renamed, AND no receipt-proven replaced files, so a
    # rename-only or replaced-only migration never reaches the adjudication
    # line: only the truly empty shape is ambiguous enough to warrant it.
    if not migrated and not renamed and not replaced and args.baseline:
        # The scoped-inventory route has no baseline file; its emptiness is
        # inventory-scoped and already refuses on a missing source, so the
        # baseline-adjudication report does not apply there.
        _print_zero_delta_report(source, dirs, baseline, Path(args.baseline))
    return 0


def _facts_resolved_home(target: Path, facts_key: str) -> Path | None:
    """Resolve one facts-block directory key under the target root; None
    when the facts file or the key is unresolvable (fail-closed, never a
    guessed default)."""
    raw = facts_paths.resolve_toml_key_raw(target, facts_key)
    if raw is None or not raw.strip():
        return None
    expanded = Path(raw).expanduser()
    if expanded.is_absolute():
        return expanded
    return (target / expanded).resolve()


def _reviews_home(target: Path) -> Path | None:
    """Resolve the target's reviews home from its facts block; None when the
    facts file or the reviews_dir key is unresolvable (fail-closed, never a
    guessed default)."""
    return _facts_resolved_home(target, "reviews_dir")


# A path-like token: slash/word/dot characters ending in a review-record
# suffix, taken from backtick spans and bare text alike. The bracket and
# angle brackets are included so the plans template's citation form with
# the optional-token segment left literal
# (``...[-p<identity-token>]-r*.md``) is captured as one series token
# instead of shredding into a bare ``-r*.md`` fragment.
_PATH_TOKEN_RE = re.compile(r"[\w./~*\[\]<>-]+\.(?:md|json)")


def _extract_citations(plan_bytes: str) -> tuple[list[str], list[str]]:
    """Split plan-byte citations into (series patterns, exact paths).

    Series patterns are the literal glob form whose basename carries
    ``-r*.md``; a basename with a concrete round number is an exact path.
    Every other path token is returned as an exact candidate (the caller
    keeps only the ones resolving under the reviews home).
    """
    series: list[str] = []
    exact: list[str] = []
    for token in _PATH_TOKEN_RE.findall(plan_bytes):
        base = token.rsplit("/", 1)[-1]
        if "-r*.md" in base:
            series.append(token)
        else:
            exact.append(token)
    return series, exact


# The two witnessed non-concrete date prefixes for a series token (plan
# 2026-10-15-closeout-gate-review-series-expansion): the plans template's
# literal placeholder and the date-agnostic wildcard segment. Both stand
# for any date-shaped prefix; a concrete date stays an exact literal.
_SERIES_DATE_HEADS = ("YYYY-MM-DD", "*")
_SERIES_DATE_FRAGMENT = r"\d{4}-\d{2}-\d{2}"
_SERIES_PLACEHOLDER_FRAGMENT = r"[A-Za-z0-9._-]+"


def _series_prefix_fragment(prefix: str) -> str:
    """Translate one series-token prefix (the text before ``-r*.md``) into
    its match fragment: a leading literal ``YYYY-MM-DD`` placeholder or a
    leading ``*`` wildcard segment matches any date-shaped prefix, a
    template form's ``<placeholder>`` segment matches one slug-shaped run
    and a bracketed ``[...]`` segment is optional, while every other
    prefix is escaped verbatim, so a concrete-date citation keeps matching
    only its own date and never a cross-date member."""
    for head in _SERIES_DATE_HEADS:
        if prefix.startswith(head):
            rest = prefix[len(head):]
            return _SERIES_DATE_FRAGMENT + _series_template_fragment(rest)
    return _series_template_fragment(prefix)


def _series_template_fragment(prefix: str) -> str:
    if "[" not in prefix and "<" not in prefix:
        return re.escape(prefix)
    out: list[str] = []
    i = 0
    while i < len(prefix):
        ch = prefix[i]
        if ch == "<":
            end = prefix.find(">", i)
            if end == -1:
                out.append(re.escape(ch))
                i += 1
                continue
            out.append(_SERIES_PLACEHOLDER_FRAGMENT)
            i = end + 1
        elif ch == "[":
            end = prefix.find("]", i)
            if end == -1:
                out.append(re.escape(ch))
                i += 1
                continue
            out.append("(?:" + _series_template_fragment(prefix[i + 1:end]) + ")?")
            i = end + 1
        else:
            out.append(re.escape(ch))
            i += 1
    return "".join(out)


_CITATION_TOKEN_RE = re.compile(r"-p([0-9a-f]{8})$")


def _plan_identity_for(plan_path: Path) -> str | None:
    """The plan file's repository-relative identity, or None when it cannot
    be derived (a gitless target never fails on identity grounds). A plan
    sitting directly under the completed archive derives the plans-root
    path its records were tokened from, the same identity the completed-twin
    runner passes through ``--plan-identity``."""
    root = review_plan_identity.repository_root(plan_path.parent)
    if root is None:
        return None
    identity = review_plan_identity.normalize_plan_path(plan_path, root)
    if identity is None:
        return None
    parent, _, basename = identity.rpartition("/")
    if parent == _COMPLETED_DIR:
        return f"{_PLANS_DIR}/{basename}"
    return identity


def _member_identity_diagnostic(member: Path, plan_identity: str) -> str | None:
    """One read-only diagnostic line for a series member whose recorded
    identity (stats-sidecar extensions.plan_identity, else the actual
    Metadata section's URL or Artifact) does not resolve to the source
    plan; None when the member names the source plan."""
    sidecar = member.with_suffix(".stats.json")
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    identity = review_plan_identity.record_identity(member, payload)
    if identity == plan_identity:
        return None
    return (
        f"series-identity: {member.name} names "
        f"{identity if identity else 'unresolved'}, expected {plan_identity}"
    )


def _series_members(
    reviews_home: Path,
    token: str,
    resolved_only: bool = False,
    plan_identity: str | None = None,
    sink: Callable[[str], None] | None = None,
) -> list[Path]:
    """Expand one ``-r*.md`` series token to its present members under the
    reviews home, ordered by round number. The token's date prefix may be
    concrete (exact), the plans template's literal ``YYYY-MM-DD``
    placeholder, or the ``*`` wildcard segment; both non-concrete forms
    match any date-shaped prefix, so landed plans citing them verify
    present series instead of false-refusing them. With resolved_only (the
    gate-removal presence seam), a member counts only when its
    filesystem-resolved path is a regular file still under the home, so a
    record symlinked into the worktree the removal would destroy is never
    a member; verify-records keeps its legacy link-following behavior.
    A citation prefix ending in ``-p<8 lowercase hex>`` is an explicit
    canonical identity token: the member's infix must equal it exactly.
    A tokenless citation matches members carrying the optional canonical
    infix ``-p<8 hex>`` too (the tokened-recognition repair), never a
    different or malformed token-like segment, which stays literal. When
    ``plan_identity`` is set, each member whose recorded identity does not
    resolve to that source-plan path emits one read-only ``series-identity``
    warning line through ``sink`` (stderr by default, so verify-records
    keeps its JSON stdout contract; gate-removal passes stdout); the
    diagnostics never filter members or change a result."""
    base = token.rsplit("/", 1)[-1]
    prefix, suffix = base.split("-r*.md", 1)
    citation_token = None
    token_match = _CITATION_TOKEN_RE.search(prefix)
    if token_match is not None:
        citation_token = token_match.group(1)
        prefix = prefix[: token_match.start()]
    infix_fragment = (
        re.escape(f"-p{citation_token}")
        if citation_token is not None
        else r"(?:-p[0-9a-f]{8})?"
    )
    pattern = re.compile(
        _series_prefix_fragment(prefix) + infix_fragment + r"-r(\d+)\.md" + re.escape(suffix) + r"$"
    )
    members: list[tuple[int, Path]] = []
    parent = reviews_home
    if not parent.is_dir():
        return []
    for entry in parent.iterdir():
        match = pattern.match(entry.name)
        if not match:
            continue
        if resolved_only:
            resolved = entry.resolve()
            if not (_is_under(resolved, reviews_home) and resolved.is_file()):
                continue
        elif not entry.is_file():
            continue
        members.append((int(match.group(1)), entry))
    ordered = [path for _round, path in sorted(members)]
    if plan_identity is not None:
        if sink is None:
            def emit(line: str) -> None:
                print(line, file=sys.stderr)
        else:
            emit = sink
        for member in ordered:
            line = _member_identity_diagnostic(member, plan_identity)
            if line is not None:
                emit(line)
    return ordered


def _is_under(path: Path, home: Path) -> bool:
    try:
        path.relative_to(home)
    except ValueError:
        return False
    return True


def cmd_check_stranded_pointers(args: argparse.Namespace) -> int:
    """Warning-only stranded doc-pointer check (entry stranded-doc-pointer-
    edit-orphan): when the audited landing touches a markdown file under
    projects/.ai-playbook/, report the primary checkout's uncommitted
    docs/AGENTS.md edits beside it at file granularity (the check cannot
    attribute which index row the dirt touches), and the reverse direction
    (index rows landed in the same change while index edits remain
    uncommitted). Machinery admission: warning-only first per the protocol
    (entry stranded-doc-pointer-edit-orphan; family record: the
    EXEC-PROMPTS-PRUNE receipt at the top of
    docs/history/backlog/EXEC-PROMPTS.md; witness landing 44f9499a5);
    exits 0 on every audited outcome - usage
    errors still exit 2 per the legacy argparse convention - and never
    blocks a closeout gate or commits. Pairing map: the docs/AGENTS.md
    index rows reference the bodies by bare file name, so a body pairs
    when its file name appears in the index text; the audited window is
    the caller's <base>..<landing> diff, so pass the landing's parent for
    a single squash landing."""
    repo = Path(args.repo).resolve()
    landing = args.landing or "HEAD"
    changed: list[str] = list(args.changed or [])
    if not changed:
        if not args.base:
            print(
                "stranded-pointer-check: nothing to audit (pass --base with "
                "--landing, or explicit --changed paths)",
                file=sys.stderr,
            )
            return 0
        diff_proc = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-only",
             f"{args.base}..{landing}"],
            capture_output=True, text=True,
        )
        if diff_proc.returncode != 0:
            print(
                f"WARN: stranded-pointer-check: changed-set probe failed: "
                f"{diff_proc.stderr.strip()}",
                file=sys.stderr,
            )
            return 0
        changed = [line for line in diff_proc.stdout.splitlines() if line]
    bodies = [
        p for p in changed
        if p.startswith("projects/.ai-playbook/") and p.endswith(".md")
    ]
    index_rel = "docs/AGENTS.md"
    index_touched = index_rel in changed
    dirt_proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--", index_rel],
        capture_output=True, text=True,
    )
    index_dirty = dirt_proc.returncode == 0 and bool(dirt_proc.stdout.strip())
    index_text = ""
    index_path = repo / index_rel
    if index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8", errors="replace")
    if landing == "HEAD":
        head_proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
        )
        short = head_proc.stdout.strip() if head_proc.returncode == 0 else "HEAD"
    else:
        short = landing
    would_strand = 0
    informational = 0
    for body in bodies:
        bare = body.rsplit("/", 1)[-1]
        if bare not in index_text:
            informational += 1
            print(
                f"stranded-pointer-check: {body} landed in {short}; no "
                "docs/AGENTS.md index row references it (no pairing to "
                "strand)"
            )
        elif index_dirty:
            would_strand += 1
            print(
                f"WARN: stranded-pointer-check: {body} landed in {short} "
                "while docs/AGENTS.md holds uncommitted edits in the "
                "primary checkout (would-strand row at file granularity; "
                "the check cannot attribute the row; the 44f9499a5 "
                "witness shape)"
            )
    if index_touched and index_dirty:
        would_strand += 1
        print(
            "WARN: stranded-pointer-check: docs/AGENTS.md landed in "
            f"{short} while the primary checkout still holds uncommitted "
            "docs/AGENTS.md edits (row edits must ride their own landing "
            "change; would-strand row)"
        )
    print(
        f"stranded-pointer-check: {would_strand} would-strand row(s), "
        f"{informational} informational line(s)"
    )
    return 0


def cmd_verify_records(args: argparse.Namespace) -> int:
    """Verify that every cited or claimed review record has bytes under the
    target's primary reviews home. Plain-exit convention: 0 verified, 1
    missing records (named on stderr beside the JSON), 2 named failure."""
    plan_path = Path(args.plan)
    if not plan_path.is_file():
        print(f"verify-records: plan file not found: {plan_path}", file=sys.stderr)
        print(
            json.dumps({"checked": [], "missing": [], "skipped": [], "series_witness": {}})
        )
        return 2
    target = Path(args.target).resolve()
    home = _reviews_home(target)
    if home is None:
        print(
            f"verify-records: cannot resolve reviews_dir from {target / '.ai-playbook' / 'facts.md'}",
            file=sys.stderr,
        )
        print(
            json.dumps({"checked": [], "missing": [], "skipped": [], "series_witness": {}})
        )
        return 2

    plan_bytes = plan_path.read_text(encoding="utf-8")
    series_tokens, exact_tokens = _extract_citations(plan_bytes)

    checked: list[str] = []
    missing: list[str] = []
    skipped: list[str] = []
    series_witness: dict[str, str] = {}

    for token in series_tokens:
        if not token.rsplit("/", 1)[-1].split("-r*.md", 1)[0]:
            # A bare ``-r*.md`` fragment carries no slug: it can never
            # name a series, so it is skipped with a named warning
            # instead of surfacing as a zero-members refusal.
            note = f"empty-prefix series token skipped (no slug in citation): {token}"
            skipped.append(note)
            print(f"verify-records: {note}", file=sys.stderr)
            continue
        members = _series_members(home, token, plan_identity=_plan_identity_for(plan_path))
        if not members:
            missing.append(f"series pattern (zero members): {token}")
            continue
        witness = members[-1]
        series_witness[token] = witness.name
        checked.append(str(witness))

    home_resolved = home.resolve()
    for token in exact_tokens:
        candidate = Path(token) if token.startswith("/") else (target / token)
        candidate_resolved = candidate.resolve()
        if _is_under(candidate_resolved, home_resolved):
            # a citation resolving under the reviews home (containment
            # judged on filesystem-resolved paths on both sides): checked
            # when the record is present, missing and named at its exact
            # candidate path when absent
            if candidate.is_file():
                checked.append(token)
            else:
                missing.append(str(candidate))
        elif not token.startswith("/") and (
            home / token.rsplit("/", 1)[-1]
        ).is_file():
            # a relative token whose basename matches an existing review
            # file at the home is identified and checked; this arm can
            # never change an exit code or stderr line
            checked.append(token)
        # any other token is not a reviews-home citation at all; ignore it
        # without manufacturing a candidate (the plan body cites many
        # non-review paths)

    if args.claims:
        claims_path = Path(args.claims)
        if not claims_path.is_file():
            print(f"verify-records: claims file not found: {claims_path}", file=sys.stderr)
            print(
                json.dumps({"checked": checked, "missing": missing, "skipped": skipped, "series_witness": series_witness})
            )
            return 2
        for line in claims_path.read_text(encoding="utf-8").splitlines():
            entry = line.strip()
            if not entry:
                continue
            candidate = Path(entry) if Path(entry).is_absolute() else (target / entry)
            if not _is_under(candidate, home):
                skipped.append(f"outside reviews home: {entry}")
                print(
                    f"verify-records: skipped claims entry outside the reviews home: {entry}",
                    file=sys.stderr,
                )
                continue
            if candidate.is_file():
                checked.append(entry)
            else:
                missing.append(str(candidate))

    print(
        json.dumps(
            {
                "checked": checked,
                "missing": missing,
                "skipped": skipped,
                "series_witness": series_witness,
            }
        )
    )
    if missing:
        for path in missing:
            print(f"missing under {home}: {path}", file=sys.stderr)
        return 1
    return 0


def cmd_copy_cited_records(args: argparse.Namespace) -> int:
    """Copy the review records a plan cites from the source (primary)
    reviews home into the target's (run's) reviews home, so the closeout's
    verify-records leg - whose containment resolves the home from the closeout
    target - finds records written per the no-mirror remedy (lesson 270: a
    record written to the primary home is foreign by construction until it is
    copied run-side; the copy is the bridge, never a containment change).
    Plain-exit convention: 0 copied or already present, 2 named failure."""
    plan_path = Path(args.plan)
    if not plan_path.is_file():
        print(f"copy-cited-records: plan file not found: {plan_path}", file=sys.stderr)
        return 2
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    source_home = _reviews_home(source)
    target_home = _reviews_home(target)
    if source_home is None:
        print(
            f"copy-cited-records: cannot resolve reviews_dir from {source / '.ai-playbook' / 'facts.md'}",
            file=sys.stderr,
        )
        return 2
    if target_home is None:
        print(
            f"copy-cited-records: cannot resolve reviews_dir from {target / '.ai-playbook' / 'facts.md'}",
            file=sys.stderr,
        )
        return 2

    plan_bytes = plan_path.read_text(encoding="utf-8")
    series_tokens, exact_tokens = _extract_citations(plan_bytes)
    source_home_resolved = source_home.resolve()
    target_home_resolved = target_home.resolve()
    transferred: list[str] = []
    present: list[str] = []
    failures: list[str] = []

    def copy_member(candidate: Path) -> None:
        resolved = candidate.resolve()
        if not _is_under(resolved, source_home_resolved) or not candidate.is_file():
            return
        # Destination keyed to the cited path's own home-relative location
        # when that path already sits under the source home: an in-home
        # symlink member keeps the cited name the verify leg's scans read,
        # while containment stays judged on the resolved path (a link
        # escaping the home is never copied through).
        try:
            rel = candidate.relative_to(source_home_resolved)
        except ValueError:
            rel = resolved.relative_to(source_home_resolved)
        dest = target_home_resolved / rel
        if dest.is_file():
            present.append(str(dest))
            return
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, dest)
        except OSError as exc:
            failures.append(f"copy-cited-records: cannot copy {candidate}: {exc}")
            return
        transferred.append(str(dest))

    for token in series_tokens:
        for member in _series_members(
            source_home, token, plan_identity=_plan_identity_for(plan_path)
        ):
            copy_member(member)
    for token in exact_tokens:
        candidate = Path(token) if token.startswith("/") else (source / token)
        copy_member(candidate)

    for path in transferred:
        print(f"copy-cited-records: transferred {path}")
    for path in present:
        print(f"copy-cited-records: already present {path}")
    print(
        f"copy-cited-records: transferred={len(transferred)} "
        f"already-present={len(present)}"
    )
    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        return 2
    return 0


# The gate's header-line extraction: a plan line citing the session's owned
# review records carries one of these labels; ONLY label lines contribute
# owned citations (the plan body is never scanned).
_REVIEW_LABEL_RE = re.compile(r"^(?:Plan review record|Plan review):\s*(.*)$")

# The single remedy line of the refuse arm: names the helper's migrate
# invocation the session runs before the removal may proceed.
_GATE_REMEDY_LINE = (
    "remedy: run worktree_closeout_migrate.py capture then "
    "worktree_closeout_migrate.py migrate to land the staging records in "
    "the primary reviews home, then re-run gate-removal"
)

# The operand refusals' remedy line (r2): no migrate run can clear an
# operand nesting (a --worktree equal to or nested with the target, or a
# resolved reviews home anchored inside the worktree tree), so the line
# names the operand fix instead of the migrate loop.
_GATE_OPERAND_REMEDY_LINE = (
    "remedy: no migration fixes operand nesting; use a worktree outside "
    "the primary checkout, then re-run gate-removal"
)

# The never-verifiable citations' remedy line (plan
# 2026-10-19-gate-removal-closeout-accounting Task 1): a citation outside
# the primary reviews home (an absolute citation always, a relative one
# whose resolved home join escapes the home) is never satisfiable by
# migrating staging records, so the attainable repair is correcting the
# cited path in the plan header, never the migrate loop.
_GATE_CITATION_REMEDY_LINE = (
    "remedy: no migrate run can satisfy a citation outside the primary "
    "reviews home; correct the cited path where it lives (the plan header "
    "for header citations, re-pointed reviews-home-relative; the claims "
    "file for claims entries; absolute citations are never verifiable), "
    "then re-run gate-removal"
)

# The empty-owned-set refusal's remedy line (plan
# 2026-10-27-gate-removal-empty-owned-set-remedy Task 1): no migrate run
# can create the missing inputs (the plan header carries no citation and
# the claims file names no record path), so the attainable repair is
# adding a Plan review record:/Plan review: citation to the plan's header
# or passing a --claims file listing review-record paths, then re-running
# gate-removal.
_GATE_EMPTY_SET_REMEDY_LINE = (
    "remedy: no migrate run can create the missing inputs; add a "
    "Plan review record:/Plan review: citation to the plan's header, or "
    "pass a --claims file listing review-record paths, then re-run "
    "gate-removal"
)

# The no-charter stand-down refusals' remedy line (plan
# 2026-10-28-plan-authoring-stand-down-before-charter Task 1): a refused
# pre-plan cleanup preserves the worktree and branch, names the exact
# missing or ambiguous evidence above, and the attainable repair is
# resolving that evidence or removing the resources deliberately as
# operator work; no migrate run applies (no plan file exists to migrate
# records for).
_GATE_NO_CHARTER_REMEDY_LINE = (
    "remedy: the authoring worktree and branch stay preserved; resolve "
    "the named evidence, or remove the resources deliberately as operator "
    "work, then re-run gate-removal"
)


def _review_label_rest(plan_text: str) -> str:
    """The gate's own extraction: the joined post-label text of every
    Plan review record:/Plan review: label line in the plan's header
    region, the block bounded below by the first post-title line whose
    first character is ``#`` (the exact implemented boundary: a plain
    first-character rule, not a general Markdown heading parse, so a
    setext underline, an indented ATX line, or any other heading-shaped
    line not starting with ``#`` stays inside the region while a bare
    ``#hashtag`` line ends it), or extending to end of file when no
    post-title line starts with ``#``. Feeding only this text through the
    citation classifier keeps the plan body and its fenced blocks
    unscanned: a body or fenced label-shaped line never seeds the owned
    set."""
    rest: list[str] = []
    for index, line in enumerate(plan_text.splitlines()):
        if index and line.startswith("#"):
            # The header region ends at the first post-title line whose
            # first character is "#": index 0 is the title itself and
            # cannot be a label line (the label regex requires the label
            # at the start), and the boundary is a first-character rule,
            # not a Markdown heading parse.
            break
        match = _REVIEW_LABEL_RE.match(line.strip())
        if match:
            rest.append(match.group(1))
    return "\n".join(rest)


def _gate_repo_rel(path: Path, target: Path, fallback: str) -> str:
    """Render a missing or refused path repo-relative (never absolute):
    relative to the target root when it lives under it, else the caller's
    original repo-relative citation text."""
    try:
        return path.resolve().relative_to(target).as_posix()
    except ValueError:
        return fallback


def _gate_refusal_text(token: str, candidate: Path, target: Path) -> str:
    """Render a refused citation, or a missing series token, never as an
    absolute path: repo-relative when the resolved path lives under the
    target (its suffix after the target is then the repo-relative,
    home-relative form of the citation), else the citation's own token
    when that token is already repo-relative, else the citation's
    basename. Delegates the repo-relative step to _gate_repo_rel."""
    if token.startswith("/"):
        fallback = Path(token).name or token
    else:
        fallback = token
    return _gate_repo_rel(candidate, target, fallback)


# The canonical <PLAN_SLUG> date prefix (the execute-plan session-slug rule,
# agents/skills/execute-plan/SKILL.md Step 0.4): a leading YYYY-MM-DD- is
# stripped from a dated plan file's stem, or from a dated charter
# directory's name, so every producer and consumer keys the session
# directory by the same slug.
_PLAN_SLUG_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")

_PLAN_CHARTER_BASENAME = "PLAN.md"


def _plan_session_slug(plan_path: Path) -> str:
    """The execute-plan session directory name (<PLAN_SLUG>, the canonical
    rule in agents/skills/execute-plan/SKILL.md Step 0.4): a date-prefixed
    plan file contributes the filename after removing the leading date and
    the extension; the charter operand of a dated plan directory (PLAN.md
    inside YYYY-MM-DD-<slug>/) contributes the directory name after
    removing the leading date; undated forms keep the stem or directory
    name. A bare PLAN stem is never the slug: the dated-directory charter
    resolves to the date-stripped directory, the directory the execute-plan
    transfer-out writes closeout-migration.json under."""
    if plan_path.name == _PLAN_CHARTER_BASENAME:
        parent = plan_path.parent.name
        match = _PLAN_SLUG_DATE_PREFIX_RE.match(parent)
        return parent[match.end():] if match else parent
    stem = plan_path.stem
    match = _PLAN_SLUG_DATE_PREFIX_RE.match(stem)
    return stem[match.end():] if match else stem


class _GateRemovalUsageParser(argparse.ArgumentParser):
    """Usage-error override scoped to the gate-removal subcommand: a usage
    violation is a tool error (exit 3) with the contract's final OUTCOME
    line on stdout, never the argparse legacy exit 2 the helper's other
    subcommands keep."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"gate-removal: error: {message}", file=sys.stderr)
        print("OUTCOME: tool_error", flush=True)
        raise SystemExit(3)


def _add_gate_removal_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--plan",
        required=True,
        help="The executing plan's file; owned citations come from its "
        "Plan review record:/Plan review: label lines only.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Primary checkout root whose facts-resolved reviews home must "
        "hold every owned record.",
    )
    parser.add_argument(
        "--worktree",
        default=None,
        help="The worktree the sanctioned removal command removes; "
        "omit in branch-only mode (an explicit --branch with "
        "--migration-manifest adjudicates a ref with no linked worktree).",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Branch-only mode: the ref to account for, with an explicit "
        "--migration-manifest and no --worktree; binds the manifest "
        "identity, checks artifacts, ancestry/exact-tree proof and no "
        "linked worktree, and captures and rechecks one proven OID.",
    )
    parser.add_argument(
        "--claims",
        default=None,
        help="Newline-delimited file of extra record paths the session owns.",
    )
    parser.add_argument(
        "--plan-identity",
        default=None,
        help="Repository-relative source-plan identity overriding the "
        "derivation from --plan (the completed-twin runner passes the "
        "original plans-root path beside its temporary plan copy); "
        "diagnostics stay read-only either way.",
    )
    parser.add_argument(
        "--migration-manifest",
        default=None,
        help="Explicit migration-manifest path holding the branch record; "
        "derived from the target's facts tmp_dir plus the plan stem when "
        "omitted.",
    )
    parser.add_argument(
        "--authoring-claim",
        default=None,
        help="The authoring claim file enabling the no-charter stand-down "
        "arm: in worktree mode, when the expected plan file is absent, "
        "the gate verifies the claim's session and origin, the frozen "
        "PLAN-PROMPTS entry, the done-run manifest identity (owned plan "
        "and start_commit), the claim-derived worktree placement and "
        "authoring branch, the clean worktree, and the zero-owned-review "
        "artifact accounting before authorizing the removal; ignored "
        "when the plan file exists.",
    )
    parser.set_defaults(func=cmd_gate_removal)



def _owned_files_report(worktree: Path) -> list[str]:
    """The worktree's uncommitted owned files: the porcelain reader over the
    run worktree (staged, unstaged, and untracked entries alike)."""
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(worktree), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return [f"tool_error: git status --porcelain failed in {worktree}: {proc.stderr.strip()}"]
    return [line for line in proc.stderr.splitlines()] + [
        line for line in proc.stdout.splitlines() if line.strip()
    ]


def cmd_owned_files_clean(args: argparse.Namespace) -> int:
    """The D-10 removal preflight (plan 2026-10-10-wip-auto-checkpoint.md
    Task 2): a worktree holding uncommitted owned files is never removed.
    The check refuses when the porcelain reader reports any uncommitted
    state in the worktree (the remedy is a `wip:` checkpoint commit or a
    transfer to the primary checkout) and, when --expect-plan names an
    owned plan file, when that file's byte-identical copy is absent from
    the target checkout at the same repository-relative path. OUTCOME
    vocabulary: 0 pass, 1 fail, 3 tool error; one final OUTCOME line."""
    worktree = Path(args.worktree)
    if not worktree.is_dir():
        print(f"owned-files-clean: worktree not found: {worktree}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
    worktree = worktree.resolve()
    dirty = _owned_files_report(worktree)
    if any(line.startswith("tool_error:") for line in dirty):
        for line in dirty:
            print(line)
        print("OUTCOME: tool_error")
        return 3
    failed = False
    for line in dirty:
        failed = True
        path = line[3:].strip().strip('"')
        print(
            f"refused: uncommitted owned file in {worktree}: {line} "
            f"(remedy: commit it on the worktree branch under the wip: "
            f"checkpoint marker, or transfer the file to the primary checkout)"
        )
    if args.expect_plan:
        plan_path = Path(args.expect_plan)
        wt_plan = worktree / plan_path
        if not wt_plan.is_file():
            print(f"refused: owned plan file absent from the worktree: {plan_path}")
            failed = True
        else:
            target = Path(args.target) if args.target else None
            if target is None:
                print(
                    "owned-files-clean: --expect-plan requires --target "
                    "(the primary checkout the byte-identical copy is checked against)",
                    file=sys.stderr,
                )
                print("OUTCOME: tool_error")
                return 3
            target = target.resolve()
            primary_plan = target / plan_path
            if not primary_plan.is_file():
                print(
                    f"refused: owned plan file not transferred to the primary "
                    f"checkout: {plan_path} (remedy: copy the worktree file to "
                    f"{primary_plan} before removal)"
                )
                failed = True
            elif hashlib.sha256(primary_plan.read_bytes()).hexdigest() != hashlib.sha256(wt_plan.read_bytes()).hexdigest():
                print(
                    f"refused: owned plan file at the primary checkout is not "
                    f"byte-identical to the worktree copy: {plan_path} "
                    f"(remedy: re-copy the worktree file over the primary copy)"
                )
                failed = True
            else:
                print(f"owned {plan_path}: transferred byte-identical to the primary checkout")
    if failed:
        print("OUTCOME: fail")
        return 1
    if not dirty:
        print(f"owned-files-clean: {worktree} holds no uncommitted owned files")
    print("OUTCOME: pass")
    return 0


def build_owned_files_clean_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="worktree_closeout_migrate.py owned-files-clean",
        description=(
            "D-10 removal preflight: refuse a worktree removal while it "
            "holds uncommitted owned files; verify an owned plan file's "
            "byte-identical transfer when named."
        ),
    )
    parser.add_argument("--worktree", required=True, help="The worktree about to be removed.")
    parser.add_argument("--target", default=None, help="Primary checkout root for the byte-identical plan check.")
    parser.add_argument("--expect-plan", default=None, help="Repository-relative owned plan path (enables the transfer check).")
    parser.set_defaults(func=cmd_owned_files_clean)
    return parser


def build_gate_removal_parser() -> argparse.ArgumentParser:
    """The gate-removal parser, built standalone so the legacy parser
    (build_parser) stays byte-unchanged and the usage-override class
    applies to gate-removal runs only. Flat by construction (plan
    2026-10-19-gate-removal-closeout-accounting Task 4): main consumes the
    dispatch token before parsing, the parser carries only the gate's own
    options, and the standalone help presents gate-removal exactly once
    (the earlier nested shape printed the token twice in the usage line)."""
    parser = _GateRemovalUsageParser(
        prog="worktree_closeout_migrate.py gate-removal",
        description=(
            "Gate a worktree removal on the plan's owned review records "
            "being present under the primary reviews home."
        ),
    )
    _add_gate_removal_arguments(parser)
    return parser


# The no-charter stand-down arm's fixed surfaces (plan
# 2026-10-28-plan-authoring-stand-down-before-charter Task 1): the prompt
# log the frozen binding reads, and the Worktree-first pre-plan authoring
# arm's branch placement (agents/skills/execute-plan/worktree-first.md:
# branch `authoring/<claim-file-stem>` for a worktree at
# <worktree-root>/<claim-file-stem>).
_NO_CHARTER_PROMPTS_LOG_REL = "docs/history/backlog/PLAN-PROMPTS.md"
_NO_CHARTER_BRANCH_PREFIX = "authoring/"


def _no_charter_claim_fields(claim_path: Path) -> tuple[str | None, str | None]:
    """The authoring claim's `session:` and `item:` values (r3 F2: the
    first occurrence of each key, scanned line-by-line over the whole
    file; no frontmatter block is parsed or bounded); (None, None) when
    the file is unreadable. An absent or empty field stays None: the
    caller refuses, never guesses."""
    try:
        text = claim_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    session: str | None = None
    item: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if session is None and stripped.startswith("session:"):
            session = stripped[len("session:"):].strip() or None
        elif item is None and stripped.startswith("item:"):
            item = stripped[len("item:"):].strip() or None
    return session, item


def _no_charter_frozen_entry(
    log_path: Path, slug: str, claim_name: str, item: str
) -> tuple[dict | None, str | None]:
    """The prompt-log entry binding this pre-plan claim: (entry, None) when
    exactly one entry whose heading slug is the session slug carries a
    ``Frozen:`` line naming the claim file and an ``Origins:`` list holding
    the claim's origin; (None, reason) for every other shape (missing log,
    zero or duplicate slug headings, absent freeze mark, a foreign witness,
    a missing origin), so the caller refuses with the specific reason."""
    try:
        text = log_path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"the prompt log {_NO_CHARTER_PROMPTS_LOG_REL} is unreadable ({exc})"
    entries: list[dict] = []
    current: dict | None = None
    in_origins = False
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                entries.append(current)
            current = {"slug": line[3:].strip(), "frozen": None, "origins": []}
            in_origins = False
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("Frozen:") and current["frozen"] is None:
            current["frozen"] = stripped[len("Frozen:"):].strip()
        elif stripped == "Origins:":
            in_origins = True
        elif stripped.startswith("- ") and in_origins:
            current["origins"].append(stripped[2:].strip())
        elif stripped:
            in_origins = False
    if current is not None:
        entries.append(current)
    shape = [entry for entry in entries if entry["slug"] == slug]
    if not shape:
        return None, (
            f"no prompt-log entry names the session slug {slug} "
            f"({_NO_CHARTER_PROMPTS_LOG_REL})"
        )
    if len(shape) > 1:
        return None, (
            f"{len(shape)} prompt-log entries name the session slug {slug} "
            "(ambiguous own-entry binding)"
        )
    entry = shape[0]
    if not entry["frozen"]:
        return None, (
            f"the prompt-log entry {slug} carries no Frozen: mark, so the "
            "authoring claim has no frozen prompt binding"
        )
    if claim_name not in entry["frozen"]:
        return None, (
            f"the prompt-log entry {slug} is frozen for a different witness: "
            f"its Frozen: line does not name the claim file {claim_name}"
        )
    if item not in entry["origins"]:
        return None, (
            f"the prompt-log entry {slug} does not list the claim's origin "
            f"{item} under Origins:"
        )
    return entry, None


def _no_charter_run_manifests(
    target: Path,
    worktree_resolved: Path,
    expected_plan_rel: str,
    root_matches: Callable[[object, Path], bool],
) -> list[tuple[str, dict]]:
    """The done-run manifests binding the expected plan: every parseable
    ``run-manifest-*.json`` under the target's AND the run worktree's
    facts-resolved ``done-session`` directories (r1 F1: the producer's
    ``session_dir`` resolves from the dispatching checkout's toplevel, so a
    worktree-dispatched run records under the worktree side while a
    primary-dispatched run records under the target side; a shared
    ``tmp_dir`` collapses to one scanned directory) whose recorded
    ``repo_root`` binds the target or the run worktree through the
    producer's shared two-arm matcher (``root_matches``: a 64-hex identity
    digest, or a legacy raw-path record kept loadable), and whose
    ``owned_plan_paths`` name the expected plan exactly. Manifest identity
    is the producer's ``run-manifest-<run_id>.json`` filename: the same
    record visible through both sides dedupes to one binding, and the
    first scanned side (the target side) is authoritative for a filename
    whose twins disagree. Unparseable or foreign records match nothing
    (the conservative fallback), so a run whose only record is corrupt
    refuses through the zero-match arm."""
    done_dirs: list[Path] = []
    for root in (target, worktree_resolved):
        done_dir = _facts_tmp_root(root) / "done-session"
        if done_dir not in done_dirs:
            done_dirs.append(done_dir)
    matches: list[tuple[str, dict]] = []
    seen_names: set[str] = set()
    for done_dir in done_dirs:
        if not done_dir.is_dir():
            continue
        for path in sorted(done_dir.glob("run-manifest-*.json")):
            if path.name in seen_names:
                continue
            seen_names.add(path.name)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(payload, dict):
                continue
            plans = payload.get("owned_plan_paths")
            if not isinstance(plans, list):
                continue
            root_raw = payload.get("repo_root")
            if not root_matches(root_raw, target) and not root_matches(
                root_raw, worktree_resolved
            ):
                continue
            if not any(isinstance(plan, str) and plan == expected_plan_rel for plan in plans):
                continue
            matches.append((path.name, payload))
    return matches


def _gate_no_charter_refusal(*lines: str) -> int:
    """Print one no-charter refusal (the named refused: lines plus the
    shared preservation remedy and the fail outcome) and return the gate's
    refusal exit. The worktree and branch stay untouched on every path
    through here."""
    for line in lines:
        print(f"refused: {line}")
    print(_GATE_NO_CHARTER_REMEDY_LINE)
    print("OUTCOME: fail")
    return 1


def _manifest_created_epoch(payload: dict) -> float:
    """The done-run manifest's creation epoch, 0.0 when absent or
    non-numeric: the newest-binding tiebreaker over agreeing done-run
    manifest generations."""
    epoch = payload.get("created_epoch")
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)):
        return 0.0
    return float(epoch)


def _no_charter_manifest_owned_entries(
    matches: list[tuple[str, dict]], key: str, label: str
) -> tuple[list[tuple[str, str]], str | None]:
    """One manifest owned-set field aggregated across EVERY binding
    done-run manifest (r3 F1): the newest binding alone fixes the plan and
    start commit, but zero-owned must hold for every binding generation,
    so an older manifest declaring owned records refuses even when the
    newest declares none. Returns the non-empty string entries as
    (declaring manifest filename, entry) pairs, or ([], refusal) when some
    binding manifest lacks the key or carries a non-list value: that
    manifest proves nothing about ownership, so zero-owned is not proven."""
    pairs: list[tuple[str, str]] = []
    for name, payload in matches:
        if key not in payload:
            return [], (
                f"the done-run manifest {name} carries no {key} key, so "
                f"zero-owned {label} is not proven"
            )
        raw = payload.get(key)
        if not isinstance(raw, list):
            return [], (
                f"the done-run manifest {name} carries a non-list {key} "
                f"value ({type(raw).__name__}), so zero-owned {label} is "
                "not proven"
            )
        pairs.extend(
            (name, entry) for entry in raw if isinstance(entry, str) and entry
        )
    return pairs, None


def _no_charter_owned_entries_refusal(
    pairs: list[tuple[str, str]], claim: str, tail: str
) -> str:
    """One aggregated owned-set refusal line (r3 F1): names every declaring
    manifest filename and up to three declared entries."""
    names = ", ".join(sorted({name for name, _entry in pairs}))
    named = ", ".join(entry for _name, entry in pairs[:3])
    more = f" and {len(pairs) - 3} more" if len(pairs) > 3 else ""
    return f"the done-run manifest(s) {names} {claim} ({named}{more}) {tail}"


# The gitignored homes the Worktree-first transfer-in copies from the
# primary checkout into a fresh worktree (agents/skills/execute-plan/
# worktree-first.md Transfer-in implementation; agents/skills/maintenance/
# template-authoring.md WORKTREE DUTY): each entry is (label, facts key).
# A pre-plan authoring stand-down's staging homes therefore hold
# provisioned mirrors of primary records, not run-created artifacts.
_NO_CHARTER_TRANSFERRED_HOMES = (
    ("reviews", "reviews_dir"),
    ("review-certs", "review_certs_dir"),
)


def _unmirrored_staging_files(staging_home: Path, primary_home: Path) -> list[Path]:
    """The staging-home files that are NOT provisioned transfer-in mirrors:
    a file is a mirror only when the same relative path under the primary
    home exists and matches byte-for-byte (symlinks compare by link target,
    per _same_content). Everything else - no twin, a missing twin file, or
    differing bytes - is run-created or drifted state the removal would
    destroy unaccounted."""
    unmirrored: list[Path] = []
    for child in sorted(path for path in staging_home.rglob("*") if path.is_file()):
        twin = primary_home / child.relative_to(staging_home)
        if not (twin.is_symlink() or twin.is_file()):
            unmirrored.append(child)
            continue
        if not _same_content(child, twin):
            unmirrored.append(child)
    return unmirrored


def _no_charter_staging_refusal(target: Path, worktree_resolved: Path) -> list[str]:
    """The transferred-homes scan behind the no-charter zero-owned verdict
    (r2 F1). The Worktree-first transfer-in copies the primary reviews and
    review-certs homes into the worktree at provisioning, so a staging
    record whose byte-identical twin survives under the target's
    primary-side home is a provisioned mirror: harmless to destroy, the
    primary original survives. A staging record with no primary twin, or
    with bytes differing from its twin, is not a mirror and the run owns
    none: the removal would destroy it unaccounted. Returns the refusal
    lines (empty when every scanned home holds only mirrors or nothing).
    An unresolvable staging home refuses (r1 F3: never a silently skipped
    scan), as does an unresolvable primary twin home while staging records
    exist (the twin semantics are unprovable there)."""
    lines: list[str] = []
    for label, facts_key in _NO_CHARTER_TRANSFERRED_HOMES:
        staging_home = _facts_resolved_home(worktree_resolved, facts_key)
        if staging_home is None:
            lines.append(
                f"the worktree's facts cannot resolve {facts_key}, so the "
                f"staging {label} home cannot be scanned for unaccounted "
                "run-owned records"
            )
            continue
        if not staging_home.is_dir():
            continue
        staged = sorted(
            child for child in staging_home.rglob("*") if child.is_file()
        )
        if not staged:
            continue
        primary_home = _facts_resolved_home(target, facts_key)
        if primary_home is None:
            lines.append(
                f"the target's facts cannot resolve {facts_key}, so the "
                f"{len(staged)} staging {label} record(s) cannot be proven "
                "provisioned transfer-in mirrors"
            )
            continue
        unmirrored = _unmirrored_staging_files(staging_home, primary_home)
        if not unmirrored:
            continue
        try:
            named = [
                child.resolve().relative_to(worktree_resolved).as_posix()
                for child in unmirrored[:3]
            ]
        except ValueError:
            named = [child.name for child in unmirrored[:3]]
        more = f" and {len(unmirrored) - 3} more" if len(unmirrored) > 3 else ""
        lines.append(
            f"the worktree staging {label} home holds record(s) the "
            f"removal would destroy ({', '.join(named)}{more}): a "
            "provisioned transfer-in copy is safe to destroy only because "
            "its byte-identical twin survives under the primary home, and "
            "these records carry no such twin or differ from it, and the "
            "run owns none"
        )
    return lines


def _gate_removal_no_charter(
    args: argparse.Namespace,
    plan_path: Path,
    target: Path,
    worktree_resolved: Path,
) -> int:
    """The verified no-charter authoring stand-down arm (plan
    2026-10-28-plan-authoring-stand-down-before-charter Task 1): cleanup of
    an authoring worktree provisioned before its first plan-file write,
    entered only in worktree mode when --authoring-claim is explicit and
    the expected plan file is absent. The evidence chain, each refusing
    with preservation before the next runs:

    1. the authoring claim parses its session and origin;
    2. the expected plan operand is a dated plan file at the plans root
       whose date-stripped stem is the claim's slug;
    3. the prompt log holds exactly one entry with that slug, frozen for
       this claim file, listing the claim's origin;
    4. exactly one binding done-run manifest (or several agreeing on the
       start commit; the newest binds) names the expected plan in its
       ``owned_plan_paths`` and records a non-empty ``start_commit``;
    5. the worktree is the claim's placement (the claim-file stem) and a
       registered, unlocked worktree of the target bound to the
       claim-derived branch ``authoring/<claim-file-stem>``;
    6. the branch ref still sits at the recorded start commit (zero run
       commits);
    7. the worktree is clean, every binding done-run manifest carries its
       owned_review_paths and owned_paths keys as lists whose entries,
       aggregated across all bindings (r3 F1: not only the newest), are
       empty, and the transferred reviews/review-certs
       staging homes hold only provisioned transfer-in mirrors
       (byte-identical primary twins) or nothing.

    On a full pass the arm prints its evidence lines, the zero-owned
    records verdict, and rides the shared branch-closeout and removal tail:
    no plan-header citation is parsed and the ordinary empty-owned-set
    refusal never runs. Every ordinary-plan gate-removal check is unchanged."""
    claim_path = Path(args.authoring_claim)
    if not claim_path.is_file():
        return _gate_no_charter_refusal(
            f"the authoring claim file was not found: "
            f"{_gate_refusal_text(str(claim_path), claim_path, target)}"
        )
    session, item = _no_charter_claim_fields(claim_path)
    if not session or not item:
        missing = []
        if not session:
            missing.append("session:")
        if not item:
            missing.append("item:")
        return _gate_no_charter_refusal(
            "the authoring claim "
            f"{_gate_refusal_text(str(claim_path), claim_path, target)} "
            f"carries no parseable {' and '.join(missing)} line(s); the "
            "claim must bind this stand-down to a session id and a backlog "
            "origin"
        )

    # The expected plan operand: a dated plan file directly under the plans
    # root whose date-stripped stem is the claim's slug (the canonical
    # feature slug the coverage rule keys).
    slug = _plan_session_slug(claim_path)
    try:
        plan_rel = plan_path.resolve().relative_to(target).as_posix()
    except (OSError, ValueError):
        plan_rel = None
    if plan_rel is None:
        return _gate_no_charter_refusal(
            "the --plan operand does not resolve under the target checkout: "
            "pass the expected plan's absolute (or target-relative) path"
        )
    plan_base = plan_rel.rsplit("/", 1)[-1]
    plans_prefix = _PLANS_DIR + "/"
    under_plans_root = plan_rel.startswith(plans_prefix) and "/" not in plan_rel[len(plans_prefix):]
    if not under_plans_root or not _DATED_PLAN_RE.match(plan_base):
        return _gate_no_charter_refusal(
            f"the --plan operand is not a dated plan file at the plans root "
            f"({_PLANS_DIR}/): {plan_rel}"
        )
    if _plan_session_slug(plan_path) != slug:
        return _gate_no_charter_refusal(
            f"the --plan operand's session slug "
            f"{_plan_session_slug(plan_path)} does not match the claim's "
            f"slug {slug}"
        )

    entry, binding_refusal = _no_charter_frozen_entry(
        target / _NO_CHARTER_PROMPTS_LOG_REL, slug, claim_path.name, item
    )
    if binding_refusal is not None:
        return _gate_no_charter_refusal(binding_refusal)

    # The root identity borrows the done producer's shared two-arm matcher
    # (r1 F1): the producer records ``repo_root`` as the same 64-hex
    # identity digest the run-start marker records, so only the producer's
    # own matcher can bind current-producer manifests; a local raw-path
    # comparison would match nothing and silently refuse every clean
    # stand-down. The lazy import keeps the heavy sweep lib off the other
    # subcommands; an unimportable producer is a tool error, never a
    # zero-match refusal.
    try:
        from done_sweep_gates_lib import (
            _repo_root_matches_value as shared_repo_root_matcher,
        )
    except ImportError as exc:
        print(
            f"gate-removal: the done producer's shared repo-root matcher is "
            f"unimportable ({exc}); the no-charter arm cannot bind "
            "done-run manifests",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3

    matches = _no_charter_run_manifests(
        target, worktree_resolved, plan_rel, shared_repo_root_matcher
    )
    if not matches:
        return _gate_no_charter_refusal(
            f"no done-run manifest under the target's or the worktree's "
            f"done-session records names the expected plan {plan_rel} in "
            "its owned_plan_paths"
        )
    start_commits = {
        payload.get("start_commit")
        for _name, payload in matches
        if isinstance(payload.get("start_commit"), str) and payload.get("start_commit")
    }
    if len(start_commits) != 1:
        return _gate_no_charter_refusal(
            f"{len(matches)} done-run manifests name the expected plan "
            f"{plan_rel} with disagreeing or missing start commits "
            "(ambiguous run identity: "
            + ", ".join(sorted(name for name, _payload in matches))
            + ")"
        )
    manifest_name, manifest = max(
        matches, key=lambda match: _manifest_created_epoch(match[1])
    )
    start_commit = manifest.get("start_commit")

    # The placement identity: the Worktree-first pre-plan authoring arm
    # names the worktree after the claim file stem and the branch after the
    # stem under authoring/.
    claim_stem = claim_path.stem
    expected_branch = _NO_CHARTER_BRANCH_PREFIX + claim_stem
    if worktree_resolved.name != claim_stem:
        return _gate_no_charter_refusal(
            f"the --worktree operand is not the claim's placement worktree "
            f"(expected the worktree directory named after the claim file "
            f"stem {claim_stem}, found {worktree_resolved.name})"
        )
    probe = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--git-dir"],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        print(
            "gate-removal: the target is not a git checkout; the no-charter "
            "arm cannot verify the branch identity",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    try:
        entries = _parse_worktree_entries(target)
    except _SweepToolError as exc:
        print(
            f"gate-removal: the target's worktree list is unreadable ({exc})",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    mine = None
    for candidate in entries:
        try:
            if Path(candidate["path"]).resolve() == worktree_resolved:
                mine = candidate
                break
        except OSError:
            continue
    if mine is None:
        return _gate_no_charter_refusal(
            f"the worktree {worktree_resolved.name} is not a registered "
            f"worktree of the target, so the placement identity "
            f"{expected_branch} cannot be verified"
        )
    if mine.get("locked"):
        return _gate_no_charter_refusal(
            f"the worktree registration is locked ({mine.get('locked')}); "
            "an operator hold keeps the resources in place"
        )
    actual_branch = mine.get("branch")
    if mine.get("detached") or not actual_branch:
        return _gate_no_charter_refusal(
            f"the worktree is on a detached HEAD, not the claim-derived "
            f"authoring branch {expected_branch}"
        )
    if actual_branch != expected_branch:
        return _gate_no_charter_refusal(
            f"exact-branch identity mismatch: the worktree is bound to "
            f"branch '{actual_branch}', not the claim-derived authoring "
            f"branch '{expected_branch}'"
        )
    ref = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--verify", expected_branch],
        capture_output=True, text=True,
    )
    if ref.returncode != 0:
        return _gate_no_charter_refusal(
            f"the authoring branch {expected_branch} does not resolve in "
            f"the target repository ({ref.stderr.strip()})"
        )
    branch_oid = ref.stdout.strip()
    if branch_oid != start_commit:
        return _gate_no_charter_refusal(
            f"the authoring branch {expected_branch} moved past the "
            f"recorded start commit (branch {branch_oid} != start commit "
            f"{start_commit}); the run's content is not provably empty"
        )

    # Clean worktree and zero-owned artifact accounting.
    dirty = _owned_files_report(worktree_resolved)
    if any(line.startswith("tool_error:") for line in dirty):
        for line in dirty:
            print(line)
        print("OUTCOME: tool_error")
        return 3
    if dirty:
        lines = [
            f"the no-charter worktree holds uncommitted owned files: {line}"
            for line in dirty[:5]
        ]
        if len(dirty) > 5:
            lines.append(
                f"the no-charter worktree holds uncommitted owned files: "
                f"and {len(dirty) - 5} more"
            )
        return _gate_no_charter_refusal(*lines)
    # The zero-owned proof (r1 F2, r3 F1): every binding done-run manifest
    # must carry each owned-set key as a list, and the entries aggregated
    # across ALL binding manifests must be empty. The newest binding alone
    # fixes the plan and start commit, so an older generation declaring
    # owned records while the newest declares none would otherwise remove
    # the worktree while the older generation's declared records are
    # destroyed unaccounted.
    review_pairs, owned_shape_refusal = _no_charter_manifest_owned_entries(
        matches, "owned_review_paths", "review records"
    )
    if owned_shape_refusal is not None:
        return _gate_no_charter_refusal(owned_shape_refusal)
    if review_pairs:
        return _gate_no_charter_refusal(
            _no_charter_owned_entries_refusal(
                review_pairs,
                "own review record(s)",
                ", so zero-owned review records is not proven",
            )
        )
    # The general run-owned artifact set (r2 F2): the producer's
    # --owned-path accumulation lands in owned_paths; a non-empty aggregate
    # names run-owned artifacts outside the reviews home - ignored-path
    # artifacts the porcelain check cannot see and the staging scan does
    # not cover - so zero-owned is not proven. The key checks mirror the
    # owned_review_paths enforcement above: a missing or non-list key on
    # any binding manifest proves nothing about artifact ownership.
    artifact_pairs, owned_shape_refusal = _no_charter_manifest_owned_entries(
        matches, "owned_paths", "run artifacts"
    )
    if owned_shape_refusal is not None:
        return _gate_no_charter_refusal(owned_shape_refusal)
    if artifact_pairs:
        return _gate_no_charter_refusal(
            _no_charter_owned_entries_refusal(
                artifact_pairs,
                "carry a non-empty owned_paths set",
                ": unaccounted run-owned artifact(s) outside the reviews "
                "home, so zero-owned is not proven",
            )
        )
    # The transferred-homes staging scan (r1 F3, r2 F1): the Worktree-first
    # transfer-in copies the primary reviews and review-certs homes into
    # the worktree at provisioning, so a staging record whose byte-identical
    # twin survives under the target's primary-side home is a provisioned
    # mirror (harmless to destroy; the primary original survives), while a
    # record with no twin or differing bytes is run-created or drifted
    # state the removal would destroy unaccounted. An unresolvable staging
    # home is a refusal with preservation, never a silently skipped scan.
    staging_refusal = _no_charter_staging_refusal(target, worktree_resolved)
    if staging_refusal:
        return _gate_no_charter_refusal(*staging_refusal)

    # Full pass: the evidence lines, then the shared tail.
    print(
        f"no-charter: authoring claim {claim_path.name} verified "
        f"(session {session}; origin {item})"
    )
    print(f"no-charter: frozen PLAN-PROMPTS entry {slug} binds this claim")
    print(
        f"no-charter: done-run manifest {manifest.get('run_id')} "
        f"({manifest_name}) owns plan {plan_rel} "
        f"at start commit {start_commit}"
    )
    print(
        f"no-charter: branch {expected_branch} remains at the recorded "
        "start commit; the worktree is clean and owns no review record"
    )
    print(
        "verified 0 owned record(s): every binding done-run manifest owns "
        "no review record or run artifact, and the worktree staging reviews "
        "and review-certs homes hold no record without a byte-identical "
        "primary twin"
    )
    identity = getattr(args, "plan_identity", None)
    accounting_basename = Path(identity).name if identity else plan_path.name
    refusal, branch_lines, disposition = _gate_branch_closeout(
        target,
        worktree_resolved,
        plan_path,
        getattr(args, "migration_manifest", None),
        branch_only=False,
        expected_branch=None,
        plan_basename=accounting_basename,
    )
    if disposition is not None:
        print(_branch_disposition_line(disposition))
    if refusal is not None:
        print(f"refused: {refusal}")
        print(_GATE_REMEDY_LINE)
        print("OUTCOME: fail")
        return 1
    for line in branch_lines:
        print(line)
    if disposition is not None and disposition.get("removal_blocked"):
        print(
            "held: the branch disposition above names a failed guard; the "
            "on-disk worktree stays retained with the ref for operator "
            "resolution (cleanup is authorized only when the accounting and "
            "identity/artifact checks pass)"
        )
        print("OUTCOME: fail")
        return 1
    _print_gate_removal_line(args.worktree)
    print("OUTCOME: pass")
    return 0


def _print_gate_removal_line(worktree_operand: str) -> None:
    """The sanctioned removal line shared by both gate arms: the exact
    git command for an on-disk worktree, the stale-registration note
    otherwise (the operand is echoed exactly as given, the cleanup line
    staying truthful about what exists on disk)."""
    if Path(worktree_operand).exists():
        print(f"removal: git worktree remove --force {shlex.quote(worktree_operand)}")
    else:
        print(
            f"removal: no on-disk worktree at {worktree_operand} (stale "
            "registration; only the sweep's scoped administrative drain "
            "applies)"
        )


def cmd_gate_removal(args: argparse.Namespace) -> int:
    """Fail-closed pre-removal gate: the records the executing plan's
    header cites (label lines only) plus any --claims paths must exist
    under the target's facts-resolved primary reviews home before the
    worktree removal may run. Branch accounting rides the pass: the gate
    captures one proven branch OID, accounts content by ancestry or exact
    tree, and reports the branch disposition beside the worktree cleanup
    status. Branch-only mode (--branch with an explicit --migration-manifest,
    no --worktree) adjudicates a ref with no linked worktree. OUTCOME_CONTRACT
    vocabulary: 0 pass, 1 fail, 3 tool error, one final OUTCOME: line per
    classified run."""
    branch_only = bool(getattr(args, "branch", None))
    explicit_manifest = getattr(args, "migration_manifest", None)
    authoring_claim = getattr(args, "authoring_claim", None)
    if branch_only and args.worktree:
        print(
            "gate-removal: --branch and --worktree are mutually exclusive: "
            "branch-only accounting adjudicates a ref with no linked "
            "worktree",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    if branch_only and not explicit_manifest:
        print(
            "gate-removal: branch-only accounting requires an explicit "
            "--migration-manifest holding the branch record",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    if not branch_only and not args.worktree:
        print(
            "gate-removal: one of --worktree or --branch is required",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    if branch_only and authoring_claim:
        print(
            "gate-removal: --authoring-claim applies only in worktree mode: "
            "the no-charter stand-down arm removes a linked authoring "
            "worktree, never an unlinked ref",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    plan_path = Path(args.plan)
    # The no-charter stand-down arm (plan
    # 2026-10-28-plan-authoring-stand-down-before-charter Task 1): entered
    # only when an explicit authoring-claim operand is supplied in worktree
    # mode and the expected plan file is absent; every other absent-plan
    # run keeps the legacy tool error. The common operand and home guards
    # below run for both arms before the dispatch.
    no_charter = bool(authoring_claim) and not branch_only and not plan_path.is_file()
    if not no_charter and not plan_path.is_file():
        print(f"gate-removal: plan file not found: {plan_path}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
    target = Path(args.target)
    if not target.is_dir():
        print(f"gate-removal: target directory not found: {target}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
    target = target.resolve()
    # The home resolves gate-local and before the operand guards (r2): the
    # guards must judge the resolved home, and the gate-local resolution
    # closes the unresolved-absolute-facts mismatch (a facts reviews_dir
    # recorded through an unresolved symlink prefix, a macOS /tmp-style
    # path, no longer false-refuses present records).
    home = _reviews_home(target)
    if home is None:
        print(
            "gate-removal: cannot resolve reviews_dir from "
            ".ai-playbook/facts.md under the target",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
    home = home.resolve()
    # Operand-confusion refusals (r1, extended r2): a --worktree equal to
    # or nesting with the --target checkout resolves the records' home
    # from the very worktree the sanctioned command removes, and a
    # resolved reviews home anchoring inside the --worktree tree (a
    # symlinked home component pointing into the worktree's staging tree)
    # leaves the only copy of every record inside the removed subtree; in
    # both shapes the gate would pass while the removal destroys the
    # records it just verified. Both refuse with the operand remedy,
    # never the migrate remedy. Branch-only mode has no --worktree
    # operand, so the worktree-shaped guards do not apply.
    worktree_resolved = Path(args.worktree).resolve() if args.worktree else None
    if worktree_resolved is not None and (
        worktree_resolved == target
        or _is_under(worktree_resolved, target)
        or _is_under(target, worktree_resolved)
    ):
        operand = _gate_refusal_text(args.worktree, worktree_resolved, target)
        print(
            "refused: --worktree resolves equal to or nested with the "
            f"--target checkout: {operand}"
        )
        print(_GATE_OPERAND_REMEDY_LINE)
        print("OUTCOME: fail")
        return 1
    if worktree_resolved is not None and (
        home == worktree_resolved or _is_under(home, worktree_resolved)
    ):
        try:
            home_shape = home.relative_to(worktree_resolved).as_posix()
        except ValueError:
            home_shape = home.name
        if not home_shape or home_shape == ".":
            home_shape = home.name
        print(
            "refused: the resolved reviews home anchors inside the "
            f"--worktree tree: {home_shape}"
        )
        print(_GATE_OPERAND_REMEDY_LINE)
        print("OUTCOME: fail")
        return 1
    # Reverse containment (plan 2026-10-19-gate-removal-closeout-accounting
    # Task 3): the worktree being removed resolves INSIDE the absolute
    # external reviews home (with the two guards above passed, a worktree
    # under the home cannot also sit under the target, so the home here is
    # genuinely external). No harmful occurrence of this shape was ever
    # witnessed, so the admission is warning-only: the lines below are
    # read-only visibility and cannot refuse, change the outcome, or block
    # the removal in any arm below; only the blocking guard above (the home
    # anchoring inside the worktree, which would destroy the records' only
    # copy) stays a refusal. Machinery-admission fields recorded in the
    # output: expected catch frequency low (no witnessed catch),
    # false-positive cost is relocation noise, review date 2027-01-19.
    if worktree_resolved is not None and _is_under(worktree_resolved, home):
        warn_shape = _gate_refusal_text(args.worktree, worktree_resolved, target)
        print(
            "warning: reverse containment: the --worktree resolves inside "
            f"the reviews home: {warn_shape}"
        )
        print(
            "warning: advisory only, removal proceeds: expected catch "
            "frequency low (no witnessed harmful occurrence), "
            "false-positive cost is relocation noise, review date "
            "2027-01-19"
        )

    if no_charter:
        # The verified no-charter stand-down: claim, frozen prompt entry,
        # done-run manifest identity, placement, start commit, clean
        # worktree, and zero-owned artifact accounting all bind before any
        # plan-specific check is skipped (the plan header is never parsed
        # and the ordinary empty-owned-set refusal never runs in this arm).
        return _gate_removal_no_charter(args, plan_path, target, worktree_resolved)

    claims_entries: list[str] = []
    if args.claims:
        claims_path = Path(args.claims)
        if not claims_path.is_file():
            print(
                f"gate-removal: claims file not found: {claims_path}",
                file=sys.stderr,
            )
            print("OUTCOME: tool_error")
            return 3
        claims_entries = [
            entry.strip()
            for entry in claims_path.read_text(encoding="utf-8").splitlines()
            if entry.strip()
        ]

    # The gate's own extraction: only label lines contribute owned
    # citations; the classification reuses the verify-records citation
    # classifier over the extracted label text alone.
    plan_text = plan_path.read_text(encoding="utf-8")
    series_tokens, exact_tokens = _extract_citations(_review_label_rest(plan_text))

    if not series_tokens and not exact_tokens and not claims_entries:
        print(
            "refused: empty owned set: the plan carries no Plan review record:/"
            "Plan review: header citation and --claims names no record path"
        )
        # The remedy follows its class (plan
        # 2026-10-27-gate-removal-empty-owned-set-remedy Task 1): no migrate
        # run can create a plan-header citation or a claims-file entry, so
        # the empty set carries its own attainable-input remedy, never the
        # migrate remedy.
        print(_GATE_EMPTY_SET_REMEDY_LINE)
        print("OUTCOME: fail")
        return 1

    missing: list[str] = []
    verified = 0
    # Verified record paths with their citation texts: the
    # sibling-destruction arm's derivation input (claims entries and
    # exact-token citations only; the series arm contributes no entries and
    # keeps its witness-presence semantics).
    verified_records: list[tuple[Path, str]] = []

    for token in series_tokens:
        # The verify-records series primitive: the series is present when
        # it has at least one member under the home (the highest round is
        # the witness). A zero-member series is missing, rendered through
        # the same never-absolute rendering as the exact-token arm
        # (repo-relative when derivable, else basename, else token): the
        # raw token would leak an absolute path for an absolute citation.
        # The gate expands members with the resolved-only filter, so a
        # home record symlinked into the worktree is never a member.
        if _series_members(
            home,
            token,
            resolved_only=True,
            plan_identity=getattr(args, "plan_identity", None)
            or _plan_identity_for(plan_path),
            sink=print,
        ):
            verified += 1
        else:
            missing.append(_gate_refusal_text(token, target / token, target))

    refused_citations: list[str] = []
    for token in exact_tokens:
        candidate = Path(token) if token.startswith("/") else (target / token)
        candidate = candidate.resolve() if candidate.exists() else (target / token)
        if token.startswith("/"):
            # an absolute citation is ALWAYS refused (never
            # basename-verified), because its pathlib join would discard
            # the home, so its file could exist anywhere (the worktree's
            # own staging copy included) and a basename twin in the home
            # proves nothing
            refused_citations.append(_gate_refusal_text(token, candidate, target))
            continue
        # Filesystem-resolved containment (r3 correction): a lexical prefix
        # match reads a `..` component as an ordinary one, so the
        # `home / token` join never escaped the home lexically, the
        # basename arm below stayed dead code, and a `..` citation verified
        # fail-open against whatever file the normalized join landed on
        # outside the home; resolving the join first routes the escape to
        # the refusal arm.
        home_join = (home / token).resolve()
        if _is_under(candidate, home):
            home_path: Path = candidate
        elif not _is_under(home_join, home) and (
            home / token.rsplit("/", 1)[-1]
        ).exists():
            # a genuine basename-form citation from a RELATIVE token only:
            # the resolved home join escapes the home (a `..` citation)
            # while the basename record exists on disk under the home; the
            # presence check below still requires the record's resolved
            # path to stay under the home, so a basename twin that is a
            # symlink into the worktree is refused, never verified
            home_path = home / token.rsplit("/", 1)[-1]
        elif _is_under(home_join, home):
            home_path = home / token
        else:
            # a label-line citation outside the reviews home is refused,
            # never skipped: a label line owns only review records
            refused_citations.append(_gate_refusal_text(token, candidate, target))
            continue
        # Presence is judged on the filesystem-resolved path (r1):
        # is_file() follows symlinks, so a staging record symlinked into
        # the worktree would verify here and the sanctioned removal would
        # destroy the bytes; a resolution leaving the home is a refusal,
        # never a verification.
        home_resolved = home_path.resolve()
        if not _is_under(home_resolved, home):
            refused_citations.append(_gate_refusal_text(token, home_resolved, target))
        elif home_resolved.is_file():
            verified += 1
            verified_records.append((home_resolved, token))
        else:
            missing.append(_gate_repo_rel(home_path, target, token))

    refused_claims: list[str] = []
    for entry in claims_entries:
        candidate = Path(entry) if Path(entry).is_absolute() else (target / entry)
        # Filesystem-resolved containment and presence (r1 B1 and the
        # symlink guard), the same resolution pattern as the exact-token
        # arm: the lexical prefix check read a `..`-threaded claims entry
        # as inside the home while its is_file() followed the dots to the
        # outside file, and a record symlinked into the worktree verified
        # through the link; only the resolved path's containment and
        # regular-file presence decide refused versus verified.
        resolved = candidate.resolve()
        if not _is_under(resolved, home):
            refused_claims.append(_gate_refusal_text(entry, resolved, target))
            continue
        if resolved.is_file():
            verified += 1
            verified_records.append((resolved, entry))
        else:
            missing.append(_gate_repo_rel(resolved, target, entry))

    # Sibling-destruction arm (plan
    # 2026-10-16-worktree-closeout-claim-sibling-completeness): every
    # verified claims entry or exact-token citation ending .md requires its
    # .stats.json sidecar (the staging validator's twin contract) to
    # survive the removal. When that sibling exists in the worktree staging
    # home (the facts-resolved reviews home under the worktree being
    # removed) and is absent from the primary home, the removal would
    # destroy the only worktree-side copy, so the refusal joins the
    # aggregate below naming the missing-from-home sibling path with the
    # shared migrate remedy, before any removal verdict. A sibling absent
    # from the worktree staging home never refuses (never existed, already
    # transferred, or the record carries none), a worktree with no
    # resolvable staging home takes no worktree-side probe, and a
    # .stats.json-suffixed entry verifies as itself and derives nothing.
    destroyed_siblings: list[str] = []
    staging_home = _reviews_home(worktree_resolved) if worktree_resolved else None
    if staging_home is not None:
        staging_home = staging_home.resolve()
        for verified_path, record_token in verified_records:
            if verified_path.suffix != ".md":
                continue
            home_sibling = verified_path.with_suffix(".stats.json")
            try:
                staging_sibling = staging_home / home_sibling.relative_to(home)
            except ValueError:
                continue
            if staging_sibling.is_file() and not home_sibling.is_file():
                fallback = (
                    record_token[:-3] + ".stats.json"
                    if record_token.endswith(".md")
                    else home_sibling.name
                )
                destroyed_siblings.append(
                    _gate_repo_rel(home_sibling, target, fallback)
                )

    if missing or refused_citations or refused_claims or destroyed_siblings:
        for path in missing:
            print(f"missing: {path}")
        for entry in refused_citations:
            print(f"refused: label citation outside the reviews home: {entry}")
        for entry in refused_claims:
            print(f"refused: claims entry outside the reviews home: {entry}")
        for entry in destroyed_siblings:
            print(
                "refused: claimed record's required stats sibling exists only "
                f"in the worktree staging home: {entry}"
            )
        # The remedy follows its class: missing records and destroyed
        # siblings are closed by a migrate re-run (the migrate remedy);
        # refused citations are never-verifiable and carry only the
        # citation-correction remedy.
        if missing or destroyed_siblings:
            print(_GATE_REMEDY_LINE)
        if refused_citations or refused_claims:
            print(_GATE_CITATION_REMEDY_LINE)
        print("OUTCOME: fail")
        return 1

    print(f"verified {verified} owned record(s) present under the primary reviews home")
    # The accounting basename: the completed-twin runner's --plan-identity
    # names the original plans-root path, so the legacy changed-path scope
    # probes the real plan basename instead of the temporary twin's.
    identity = getattr(args, "plan_identity", None)
    accounting_basename = Path(identity).name if identity else plan_path.name
    refusal, branch_lines, disposition = _gate_branch_closeout(
        target,
        worktree_resolved,
        plan_path,
        explicit_manifest,
        branch_only=branch_only,
        expected_branch=getattr(args, "branch", None),
        plan_basename=accounting_basename,
    )
    if disposition is not None:
        print(_branch_disposition_line(disposition))
    if refusal is not None:
        print(f"refused: {refusal}")
        print(_GATE_REMEDY_LINE)
        print("OUTCOME: fail")
        return 1
    for line in branch_lines:
        print(line)
    if branch_only:
        # Nothing is removed in branch-only mode: a pass authorizes the
        # operator closeout the branch lines above spell out, and a
        # retained disposition (missing proof or any failed guard) fails
        # the run so the ref stays retained for operator resolution. A
        # skip shape (no manifest at the explicit path, no manifest at
        # all, a manifest without a branch record, an unresolved recorded
        # branch, a non-git target) returns no disposition at all: the
        # branch went unadjudicated, so branch-only mode fails instead of
        # passing without branch accounting (plan
        # 2026-10-19-gate-removal-closeout-accounting Task 2: a pass
        # requires an actual disposition binding the manifest identity
        # and carrying the proof); the skip line above names the shape.
        if disposition is None:
            print(
                "refused: branch-only closeout produced no branch "
                "disposition; the skip line above names the legacy shape "
                "and the branch ref stays retained for operator resolution"
            )
            print("OUTCOME: fail")
            return 1
        if disposition.get("status") == "retained":
            print("OUTCOME: fail")
            return 1
        print("OUTCOME: pass")
        return 0
    if disposition is not None and disposition.get("removal_blocked"):
        print(
            "held: the branch disposition above names a failed guard; the "
            "on-disk worktree stays retained with the ref for operator "
            "resolution (cleanup is authorized only when the accounting and "
            "identity/artifact checks pass)"
        )
        print("OUTCOME: fail")
        return 1
    _print_gate_removal_line(args.worktree)
    print("OUTCOME: pass")
    return 0


def _branch_landing_content_scope(
    target: Path, branch: str, plan_basename: str
) -> tuple[str, str]:
    """The legacy changed-path content-scope proof for a branch whose
    commits are not merge-reachable from HEAD (the squash-landing shape):
    the landing's introduction commit is the archive twin's earliest add under
    the completed directory, every branch commit must predate it (no
    post-landing activity), and every changed path since the merge base must
    sit inside that introduction commit's touched set (a squash landing
    touches every file its branch touched; --no-renames keeps an archival
    move's plans-root vintage in the set). ``branch`` may be the captured
    proven OID, so the proof judges one immutable commit. Returns (verdict,
    evidence): verdict "accounted" reports landed content as ACCOUNTING
    EVIDENCE only (plan 2026-10-19-gate-removal-closeout-accounting Task 2:
    it never permits deleting a non-ancestor branch); anything else is a
    preserve reason, never a gate failure - an unaccounted branch is retained
    and reported, exactly like Arm 6's pairing in the sweep chain."""
    adds: list[tuple[int, str]] = []
    intro = subprocess.run(
        [
            "git", "-C", str(target), "log", "--diff-filter=A",
            "--format=%H %ct", "--", f"{_COMPLETED_DIR}/{plan_basename}",
        ],
        capture_output=True, text=True,
    )
    if intro.returncode != 0:
        return "unaccounted", f"archive twin probe failed ({intro.stderr.strip()})"
    for line in intro.stdout.strip().splitlines():
        sha, _sep, ct = line.strip().partition(" ")
        if sha and ct.strip().isdigit():
            adds.append((int(ct.strip()), sha))
    if not adds:
        return (
            "unaccounted",
            f"no completed archive twin {_COMPLETED_DIR}/{plan_basename} names the landing",
        )
    intro_ct, intro_sha = min(adds, key=lambda item: item[0])
    rev = subprocess.run(
        ["git", "-C", str(target), "rev-list", branch, "--not", "HEAD"],
        capture_output=True, text=True,
    )
    if rev.returncode != 0:
        return "unaccounted", f"branch commits unresolvable ({rev.stderr.strip()})"
    for sha in rev.stdout.split():
        show = subprocess.run(
            ["git", "-C", str(target), "show", "-s", "--format=%ct", sha],
            capture_output=True, text=True,
        )
        ct_text = show.stdout.strip().splitlines()[-1] if show.stdout.strip() else ""
        if not ct_text.isdigit():
            return "unaccounted", f"cannot resolve the committer date of {sha}"
        if int(ct_text) > intro_ct:
            return "unaccounted", f"post-landing commits on branch ({sha})"
    merge = subprocess.run(
        ["git", "-C", str(target), "merge-base", branch, "HEAD"],
        capture_output=True, text=True,
    )
    if merge.returncode != 0:
        return "unaccounted", "no merge base between the branch and HEAD"
    changed = subprocess.run(
        ["git", "-C", str(target), "diff", "--name-only", f"{merge.stdout.strip()}..{branch}"],
        capture_output=True, text=True,
    )
    if changed.returncode != 0:
        return "unaccounted", f"branch diff failed ({changed.stderr.strip()})"
    touched = {
        line
        for line in subprocess.run(
            ["git", "-C", str(target), "show", "--name-only", "--no-renames", "--format=", intro_sha],
            capture_output=True, text=True,
        ).stdout.splitlines()
        if line.strip()
    }
    for changed_path in changed.stdout.splitlines():
        if changed_path.strip() and changed_path not in touched:
            return "unaccounted", f"branch content outside the landing's file set: {changed_path}"
    return "accounted", ""


def _destination_history_trees(target: Path) -> tuple[set[str] | None, str]:
    """The complete tree OID of every destination-history commit (reachable
    from HEAD). Returns (trees, error): trees is None when the history walk
    fails, carrying the git diagnostic."""
    walk = subprocess.run(
        ["git", "-C", str(target), "log", "--format=%T", "HEAD"],
        capture_output=True, text=True,
    )
    if walk.returncode != 0:
        return None, walk.stderr.strip()
    return {line.strip() for line in walk.stdout.splitlines() if line.strip()}, ""


def _capture_branch_oid(target: Path, branch: str) -> tuple[str | None, str]:
    """One proven-tip capture: resolve the branch ref to its commit OID once.
    Returns (oid, error); oid is None when the ref does not resolve."""
    proc = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--verify", branch],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None, proc.stderr.strip()
    return proc.stdout.strip(), ""


def _branch_disposition_line(disposition: dict) -> str:
    """The machine-parseable branch-disposition line: one per adjudicated
    branch, carrying the branch name, the content-accounting status, the
    proven OID when captured, and the retention reasons. The sweep's twin
    gate run parses this line to carry disposition and proven OID into its
    own verdicts."""
    oid = disposition.get("oid") or "unknown"
    line = (
        f"branch-disposition: branch={disposition['branch']} "
        f"disposition={disposition['status']} oid={oid}"
    )
    reasons = disposition.get("reasons") or []
    if reasons:
        line += " reasons=" + "; ".join(reasons)
    return line


def _closeout_manifest_candidate(
    target: Path,
    plan_path: Path,
    explicit_manifest: str | None,
) -> tuple[Path | None, bool]:
    """The closeout migration manifest a consumer resolves for one plan,
    refactored out of the gate's inline lookup (plan
    2026-10-29-done-gate-report-retention Task 1) so the done-session sweep
    can resolve the same reference. The explicit ``--migration-manifest``
    operand is authoritative: an absent explicit file returns ``(None,
    True)`` so the caller reports its own explicit-path skip and never
    falls back to the derived slug directory behind its back (plan
    2026-10-19-gate-removal-closeout-accounting Task 1). Otherwise the
    canonical Phase 5 ``closeout-migration.json`` name is probed first and
    the legacy ``migration-manifest.json`` twin second under the
    facts-resolved ``execute-plan/<PLAN_SLUG>/`` session directory;
    ``(None, False)`` when neither exists."""
    if explicit_manifest:
        path = Path(explicit_manifest)
        return (path if path.is_file() else None), True
    manifest_dir = (
        _facts_tmp_root(target) / "execute-plan" / _plan_session_slug(plan_path)
    )
    for name in ("closeout-migration.json", "migration-manifest.json"):
        candidate = manifest_dir / name
        if candidate.is_file():
            return candidate, False
    return None, False


def _is_done_session_gate_report(destination: str) -> bool:
    """True when the verified destination is a done-session bounded gate
    report (the ``gate-reports/run-<id>-<gate>-full.txt`` shape the producer
    writes and the sanctioned docs/tmp sweep expires): the swept-artifact
    class both 2026-10-31 witnesses name. The match is anchored: adjacent
    ``gate-reports/run-`` components, the ``-full.txt`` suffix, and a
    target-relative path (an absolute destination would discard the target
    at the join, so it stays fail-closed); the transfer rows record these
    destinations as target-relative POSIX paths."""
    if PurePosixPath(destination).is_absolute():
        return False
    parts = PurePosixPath(destination).parts
    adjacent = any(
        parts[i] == "gate-reports" and parts[i + 1].startswith("run-")
        for i in range(len(parts) - 1)
    )
    return adjacent and destination.endswith("-full.txt")


def _resolve_closeout_reference_state(manifest_path: Path) -> dict:
    """The consumer-usable closeout reference state behind the gate's
    exact-branch adjudication, refactored out of the gate's inline logic
    (plan 2026-10-29-done-gate-report-retention Task 1) so the done-session
    sweep can consume the same resolution. Reads one migration manifest and
    returns a state dict; the resolver NEVER raises, and every unreadable
    or unsupported shape resolves to no references:

    - ``read_error``: the OSError/ValueError when the file is absent or
      unreadable, else None; the remaining fields are then unresolved.
    - ``shape_error``: the AttributeError a parsed non-dictionary root (an
      array root, a JSON scalar) raises at branch-record extraction, else
      None. The gate re-raises it at the same point the inline manifest
      access always raised, so the caught ``OUTCOME: tool_error`` shape is
      preserved byte-identically; the sweep treats the shape as
      reference-less.
    - ``records``: the raw ``branch`` value, ``[]`` when absent or falsy
      (the inline ``manifest.get("branch") or []`` product, unnormalized).
    - ``record``: the latest branch record - repeated migrate runs extend
      the branch list, so the last element is the authoritative binding,
      and it is taken only when it is a dictionary, else ``{}``.
    - ``recorded``: ``record.get("branch")`` verbatim, else None.
    - ``verified_destinations``: every truthy ``destination`` of a
      dictionary row carrying a truthy ``verified`` mark, across
      ``migrated`` then ``renamed`` in manifest order, duplicates
      preserved; non-dictionary rows are ignored and ``skipped`` rows are
      never references.
    - ``verified_rows``: the same verified rows as dictionaries, beside
      their destinations and in the same order (plan
      2026-11-01-gate-removal-inherited-manifest-rows), so the gate can
      read each row's run-attribution stamp; additive only, no consumer
      outside the gate reads it.
    - ``destinations_error``: the TypeError a non-iterable section raises
      at destination extraction, else None, discarding any partial
      collection (both ``verified_destinations`` and ``verified_rows``
      reset together); the gate re-raises it at the guard-check point
      (after identity binding), preserving the inline ordering, and the
      sweep treats the shape as reference-less.

    No shape is normalized and no refusal class is added: malformed parsed
    shapes resolve to no references while the gate's shape-specific skip,
    refusal, and tool-error outcomes stay byte-identical."""
    state: dict = {
        "path": manifest_path,
        "read_error": None,
        "shape_error": None,
        "records": [],
        "record": {},
        "recorded": None,
        "verified_destinations": [],
        "verified_rows": [],
        "destinations_error": None,
    }
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        state["read_error"] = exc
        return state
    try:
        records = manifest.get("branch") or []
    except AttributeError as exc:
        state["shape_error"] = exc
        return state
    state["records"] = records
    if isinstance(records, list) and records:
        last = records[-1]
        if isinstance(last, dict):
            state["record"] = last
    state["recorded"] = state["record"].get("branch")
    try:
        for section in ("migrated", "renamed"):
            for entry in manifest.get(section, []):
                if (
                    isinstance(entry, dict)
                    and entry.get("verified")
                    and entry.get("destination")
                ):
                    state["verified_rows"].append(entry)
                    state["verified_destinations"].append(entry["destination"])
    except TypeError as exc:
        state["destinations_error"] = exc
        state["verified_destinations"] = []
        state["verified_rows"] = []
    return state


def _gate_branch_closeout(
    target: Path,
    worktree_resolved: Path | None,
    plan_path: Path,
    explicit_manifest: str | None,
    branch_only: bool = False,
    expected_branch: str | None = None,
    plan_basename: str | None = None,
) -> tuple[str | None, list[str], dict | None]:
    """The exact-branch closeout adjudication behind the gate-removal pass
    (plan 2026-10-19-gate-removal-closeout-accounting Task 2). The migrate
    manifest's ``branch`` record binds the worktree to its exact source
    branch at transfer time (worktree mode) or the ``--branch`` operand
    (branch-only mode), then the branch itself is adjudicated: capture ONE
    proven tip OID, judge content against that OID (ancestry, then
    exact-tree, then the legacy changed-path scope as evidence only), run
    the guard checks (live linked worktrees, migrated artifacts), and
    re-compare the ref afterward: a ref that moved or turned unreadable
    mid-check voids the accounting and refuses, so the branch and any
    on-disk worktree stay for operator resolution.

    The migrated-artifact hold is scoped by run attribution (plan
    2026-11-01-gate-removal-inherited-manifest-rows): the shared manifest
    is append-only per canonical session slug, so each migrate run stamps
    its rows with its branch record's index and the hold covers only rows
    stamped for the adjudicated record (the manifest's last) plus all rows
    of a single-record legacy manifest, the done-session gate-report
    exception staying report-only inside this population; a prior run's rows and
    unattributable rows in multi-record manifests demote to a report-only
    foreign note naming the missing destinations and the
    attributed/unattributed counts, and the manifest is never rewritten.

    Content accounting: an ancestry-accounted tip (an ancestor of
    destination history) is landed; a tip whose complete tree equals any
    destination-history commit's tree is landed WITHOUT ancestry or an
    archive twin, while the non-ancestor branch itself stays retained; the
    legacy changed-path scope reports evidence only and never permits
    deleting a non-ancestor branch.

    Returns ``(refusal, report_lines, disposition)``: a non-empty refusal is
    an identity mismatch or a ref anomaly (OUTCOME: fail, the removal must
    not run); report lines are informational closeout verdicts that never
    block the records gate's pass; the disposition dict carries
    ``branch``, ``oid`` (or None), ``status`` (ancestry-accounted,
    exact-tree-accounted, retained, unknown-ref, ref-changed, unbound) and
    ``reasons``. Legacy shapes (no manifest, no branch record, a non-git
    target) skip with one named line: the sweep arm owns them."""
    basename = plan_basename or plan_path.name
    manifest_path, explicit_named = _closeout_manifest_candidate(
        target, plan_path, explicit_manifest
    )
    if manifest_path is None:
        if explicit_named:
            # The explicit operand is authoritative: when it names an absent
            # file the gate reports the distinct explicit-path skip and never
            # falls back to the derived slug directory behind the caller's
            # back (plan 2026-10-19-gate-removal-closeout-accounting Task 1).
            return None, [
                "branch-closeout: skipped (no migration manifest at the "
                f"explicit --migration-manifest path {explicit_manifest}; "
                "no fallback to the derived plan-slug directory)"
            ], None
        return None, [
            "branch-closeout: skipped (no migration manifest found; the "
            "sweep arm owns legacy shapes)"
        ], None
    state = _resolve_closeout_reference_state(manifest_path)
    if state["read_error"] is not None:
        exc = state["read_error"]
        return (
            "the migration manifest exists but is unreadable, so the "
            f"exact-branch binding cannot be verified ({exc}); remedy: "
            "repair or re-run the closeout migration to regenerate the "
            "manifest, then re-run gate-removal",
            [],
            None,
        )
    if state["shape_error"] is not None:
        # A parsed non-dictionary manifest root (an array root, a JSON
        # scalar) reaches the caught tool-error class at the same point the
        # inline manifest access always raised: no normalization, no new
        # refusal class (plan 2026-10-29-done-gate-report-retention Task 1).
        raise state["shape_error"]
    records = state["records"]
    if not records or not isinstance(records, list):
        return None, [
            "branch-closeout: skipped (migration manifest carries no branch "
            "record; legacy shape)"
        ], None
    # Append semantics: repeated migrate runs extend the branch list, so the
    # LATEST transfer record is the authoritative binding (resolved by
    # _resolve_closeout_reference_state).
    record = state["record"]
    recorded = state["recorded"]
    if not recorded:
        return None, [
            "branch-closeout: skipped (recorded branch unresolved at "
            "transfer; legacy shape)"
        ], None
    probe = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--git-dir"],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        return None, [
            "branch-closeout: skipped (target is not a git checkout; the "
            "branch record cannot be verified here)"
        ], None

    def _disposition(status: str, oid: str | None, reasons: list[str]) -> dict:
        return {
            "branch": recorded,
            "oid": oid,
            "status": status,
            "reasons": list(reasons),
        }

    # Identity binding. Worktree mode: the worktree being removed must be a
    # registered worktree of the target bound to the recorded branch.
    # Branch-only mode: the explicit --branch operand must equal the
    # recorded branch.
    if branch_only:
        if recorded != expected_branch:
            refusal = (
                f"exact-branch identity mismatch: the migration manifest "
                f"binds branch '{recorded}', not the --branch operand "
                f"'{expected_branch}'"
            )
            return refusal, [], _disposition("unbound", None, [refusal])
    else:
        mine = None
        for entry in _parse_worktree_entries(target):
            try:
                if Path(entry["path"]).resolve() == worktree_resolved:
                    mine = entry
                    break
            except OSError:
                continue
        if mine is None:
            refusal = (
                "exact-branch identity mismatch: the exact-branch record "
                "names this worktree but it is not a registered worktree of "
                f"the target (recorded source: {record.get('source')})"
            )
            return refusal, [], _disposition("unbound", None, [refusal])
        actual = mine.get("branch")
        if actual != recorded:
            refusal = (
                f"exact-branch identity mismatch: the worktree being "
                f"removed is bound to branch '{actual}', not the recorded "
                f"source branch '{recorded}'"
            )
            return refusal, [], _disposition("unbound", None, [refusal])

    # Guard checks: live worktrees linked to the branch, and migrated
    # artifacts verified under the target. A failed guard retains the branch
    # and reports the reason; the records-verified removal decision stays
    # separate from the branch disposition. A failed guard also blocks the
    # worktree-mode removal authorization: cleanup is permitted only when
    # the identity/artifact checks pass, so the on-disk worktree stays
    # retained with the ref (plan 2026-10-19-gate-removal-closeout-
    # accounting: missing proof, failed guard, or uncertainty retains both).
    reasons: list[str] = []
    guard_failed = False
    linked: list[str] = []
    for entry in _parse_worktree_entries(target):
        if entry.get("branch") != recorded:
            continue
        try:
            if branch_only or Path(entry["path"]).resolve() != worktree_resolved:
                linked.append(entry["path"])
        except OSError:
            continue
    if linked:
        guard_failed = True
        reasons.append(
            f"branch shared with {len(linked)} live worktree(s): "
            + ", ".join(linked)
        )
    if state["destinations_error"] is not None:
        # A non-iterable migrated/renamed section reaches the caught
        # tool-error class at the guard-check point, exactly where the
        # inline destination comprehension raised (after identity
        # binding): no normalization, no new refusal class.
        raise state["destinations_error"]
    # Run-attribution scoping of the missing-destination hold (plan
    # 2026-11-01-gate-removal-inherited-manifest-rows): the shared manifest
    # is append-only per canonical session slug, so prior runs' rows ride
    # beside the adjudicated run's own rows forever. The fail-closed hold
    # covers only the missing destinations attributed to the adjudicated
    # branch record (position len(records) - 1, the run this gate
    # adjudicates) and, in a single-record legacy manifest, every stamp-less
    # row (gate-report shapes excepted, report-only as below); a stamp is
    # recognized only when its record_index is an int (bool
    # excluded). The unattributed population - stamped rows at any other
    # index, and stamp-less rows whenever more than one branch record
    # exists - demotes to a report-only foreign note, so a prior run's
    # drained destination can no longer permanently refuse this run's
    # teardown; the refusal text for the attributed population is unchanged.
    adjudicated_index = len(records) - 1
    hold_missing: list[str] = []
    expired_missing: list[str] = []
    unattributed_missing: list[str] = []
    for row in state["verified_rows"]:
        destination = row["destination"]
        if (target / destination).exists():
            continue
        index = row.get("record_index")
        stamped = isinstance(index, int) and not isinstance(index, bool)
        if not stamped:
            attributed = len(records) == 1
        else:
            attributed = index == adjudicated_index
        if attributed and _is_done_session_gate_report(destination):
            # Swept-artifact classification (the 2026-10-31 closeout-gates
            # trio, landed 52750a1fe; shared-slug second witness): inside
            # the attributed scope too, a missing verified destination
            # under the done-session gate-reports home is a bounded gate
            # report the sanctioned docs/tmp sweep legitimately expires -
            # the OWNING run's disposition, report-only, never a hold.
            expired_missing.append(destination)
        elif attributed:
            hold_missing.append(destination)
        else:
            unattributed_missing.append(destination)
    if hold_missing:
        guard_failed = True
        reasons.append(
            "migrated artifact(s) missing under the target: "
            + ", ".join(hold_missing[:5])
        )
    foreign_notes: list[str] = []
    if expired_missing:
        foreign_notes.append(
            "branch-closeout: expired gate-report destination(s) missing "
            "under the target (report-only; each cites its owning run's "
            "disposition - the sanctioned docs/tmp sweep expires bounded "
            "gate reports - never a hold on this branch): "
            + ", ".join(expired_missing[:5])
        )
    if unattributed_missing:
        foreign_notes.append(
            "branch-closeout: unattributed migration destination(s) missing "
            "under the target (report-only; rows the manifest does not "
            "attribute to the adjudicated branch record never hold this "
            "branch): "
            + ", ".join(unattributed_missing[:5])
            + f" (missing attributed to the adjudicated record: "
            f"{len(hold_missing) + len(expired_missing)}; unattributed: "
            f"{len(unattributed_missing)})"
        )

    # Capture ONE proven tip OID for the ancestry/tree checks.
    proven_oid, capture_err = _capture_branch_oid(target, recorded)
    if proven_oid is None:
        refusal = (
            f"branch ref unreadable: {recorded} does not resolve in the "
            f"target repository ({capture_err}); the content accounting is "
            "unknown: resolve the ref, then re-run gate-removal"
        )
        return refusal, [], _disposition(
            "unknown-ref", None, reasons + ["branch ref unreadable at capture"]
        )

    # Content accounting against the CAPTURED OID only.
    accounted: str | None = None
    legacy_evidence: str | None = None
    ancestry = subprocess.run(
        ["git", "-C", str(target), "merge-base", "--is-ancestor", proven_oid, "HEAD"],
        capture_output=True, text=True,
    )
    if ancestry.returncode == 0:
        accounted = "ancestry-accounted"
    else:
        tree_run = subprocess.run(
            ["git", "-C", str(target), "rev-parse", f"{proven_oid}^{{tree}}"],
            capture_output=True, text=True,
        )
        if tree_run.returncode != 0:
            guard_failed = True
            reasons.append(
                f"branch tip tree unresolvable ({tree_run.stderr.strip()})"
            )
        else:
            tip_tree = tree_run.stdout.strip()
            trees, walk_err = _destination_history_trees(target)
            if trees is None:
                guard_failed = True
                reasons.append(
                    f"destination-history tree probe failed ({walk_err})"
                )
            elif tip_tree in trees:
                accounted = "exact-tree-accounted"
        if accounted is None:
            # Legacy changed-path scope: accounting evidence only. It can
            # report landed content but never permits deleting a
            # non-ancestor branch.
            verdict, evidence = _branch_landing_content_scope(
                target, proven_oid, basename
            )
            if verdict == "accounted":
                legacy_evidence = (
                    "changed-path scope: content landed inside the "
                    "landing's file set (legacy evidence only)"
                )
            else:
                reasons.append(
                    "no ancestry or exact-tree proof; " + evidence
                )
    if legacy_evidence is not None:
        reasons.insert(
            0,
            "no ancestry or exact-tree proof; the legacy changed-path scope "
            "is accounting evidence only and never permits deleting a "
            "non-ancestor branch",
        )

    # Re-compare the ref after the content and worktree checks: the proven
    # OID must still be the ref's OID. A mismatch or an unreadable ref
    # voids the accounting and retains the branch and any on-disk worktree
    # for operator resolution.
    recheck_oid, recheck_err = _capture_branch_oid(target, recorded)
    if recheck_oid is None:
        refusal = (
            f"branch ref unreadable at the closeout recheck: {recorded} no "
            f"longer resolves (proven OID {proven_oid}; {recheck_err}); the "
            "accounting is void: resolve the ref state, then re-run "
            "gate-removal"
        )
        return refusal, [], _disposition(
            "unknown-ref",
            proven_oid,
            reasons + ["branch ref unreadable at recheck"],
        )
    if recheck_oid != proven_oid:
        refusal = (
            f"branch ref changed during the closeout checks: {recorded} "
            f"moved from the proven OID {proven_oid} to {recheck_oid}; the "
            "accounting is void: quiesce writers, resolve the ref, then "
            "re-run gate-removal"
        )
        return refusal, [], _disposition(
            "ref-changed",
            proven_oid,
            reasons + [f"ref moved to {recheck_oid} during checks"],
        )

    if reasons:
        at = f" at {proven_oid}" if proven_oid else ""
        lines = [
            "branch-closeout: preserve branch " + recorded + at
            + " (" + "; ".join(reasons) + ")",
        ]
        if legacy_evidence is not None:
            lines.append(
                "branch-closeout: " + recorded + ": " + legacy_evidence
            )
        lines.append(
            "branch: preserve " + recorded
            + " and report it in the closeout record; delete only the worktree"
        )
        disposition = _disposition("retained", proven_oid, reasons)
        disposition["removal_blocked"] = guard_failed
        return None, lines + foreign_notes, disposition
    if accounted == "exact-tree-accounted":
        return None, [
            f"branch-closeout: branch {recorded} exact-tree-accounted at "
            f"{proven_oid} (the tip tree equals a destination-history "
            "commit's tree; the non-ancestor branch is retained)",
            f"branch: {recorded} content is landed by exact tree match; the "
            "branch stays retained for automated paths, and the operator "
            f"closeout may delete it at expected OID {proven_oid} only "
            "after the documented quiesce-and-reconcile sequence while "
            "writers stay stopped",
        ] + foreign_notes, _disposition("exact-tree-accounted", proven_oid, [])
    # The ancestry statement carries only the branch evidence the gate
    # itself proves (branch, proven OID, ancestry result): branch-only mode
    # has no linked worktree, and worktree/artifact facts stay with the
    # guard checks' own lines (plan 2026-10-29-gate-removal-task2-review-
    # residues Task 1).
    return None, [
        f"branch-closeout: branch {recorded} ancestry-accounted at "
        f"{proven_oid} (the branch tip is an ancestor of destination "
        "history)",
        f"branch: operator closeout may delete branch {recorded} at "
        f"expected OID {proven_oid} after the documented quiesce-and-"
        "reconcile sequence (plain git branch -d must print deletable; "
        "never force while a linked worktree remains)",
    ] + foreign_notes, _disposition("ancestry-accounted", proven_oid, [])


# ---------------------------------------------------------------------------
# sweep: mechanical ad-hoc worktree residue removal (born-conformant, the
# worktree-residue-sweep plan)
# ---------------------------------------------------------------------------

# The ad-hoc worktree shape (the plan's Terms): a registered worktree whose
# path sits in the same parent directory as the primary checkout and whose
# basename starts with the repository directory name followed by "-wt-".
_ADHOC_MARK = "-wt-"

# The plans home and its archive subtrees: dated plan files at the plans
# root are the membership candidates; the completed/deferred/rejected
# subtrees never are (the ls-tree blob filter excludes them by type).
_PLANS_DIR = "docs/history/plans"
_COMPLETED_DIR = "docs/history/plans/completed"

# A dated plan file at the plans root: YYYY-MM-DD-<slug>.md.
_DATED_PLAN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")

# Live-session evidence freshness (the plan's Terms): one cadence period,
# two hours.
_LIVE_FRESHNESS_SECS = 7200

_SWEEP_LABEL = "worktree-residue-sweep"

# The authentic-hold refusal's named requirement line: --apply can never
# proceed without the invoking run's own hold of the target's done lock.
_SWEEP_HOLD_REQUIREMENT = (
    "sweep: --apply requires the invoking run's authentic hold of the "
    "target checkout's done lock"
)


class _SweepToolError(Exception):
    """A git plumbing or environment failure: the run-level tool-error
    class (exit 3), never a modeled candidate finding."""


class _RemovalFailure(Exception):
    """A removal or release command failure: the candidate is reported
    with the command's output, the enumeration continues for the
    remaining candidates, and the run ends OUTCOME: fail."""


def _sweep_git(target: Path, *args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(cwd if cwd is not None else target), *args],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise _SweepToolError(f"git launch failed: {exc}") from exc


def _sweep_git_out(target: Path, *args: str, cwd: str | None = None) -> str:
    proc = _sweep_git(target, *args, cwd=cwd)
    if proc.returncode != 0:
        raise _SweepToolError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _sweep_toplevel(target: Path) -> str:
    out = _sweep_git_out(target, "rev-parse", "--show-toplevel").strip()
    if not out:
        raise _SweepToolError("git rev-parse --show-toplevel produced no toplevel")
    return out


def _sweep_common_dir(target: Path) -> Path:
    out = _sweep_git_out(target, "rev-parse", "--git-common-dir").strip()
    common = Path(out)
    if not common.is_absolute():
        common = target / common
    return common


def _sweep_lock_root() -> Path:
    """The done-lock script's lock root, resolved through DONE_LOCK_ROOT
    exactly as the script resolves it (env value or the runtime-home
    default)."""
    return Path(os.environ.get("DONE_LOCK_ROOT") or (Path.home() / ".ai-playbook" / "locks" / "done"))


def _done_lock_dir_for(checkout: str) -> Path:
    """The done-lock script's per-worktree key: the first 16 hex characters
    of the SHA-256 of the checkout toplevel, under the lock root (the
    script's toplevel-digest form)."""
    repo_id = hashlib.sha256(checkout.encode("utf-8")).hexdigest()[:16]
    return _sweep_lock_root() / repo_id


def _verify_authentic_hold(target: Path) -> tuple[bool, str]:
    """The --apply precondition (the plan's authentic-hold term): the
    invoking run's own DONE_LOCK_DIR/DONE_LOCK_TOKEN exports must match the
    target checkout's derived done-lock directory and its meta.env recorded
    token plus repo_root equal to the target checkout root. Directory
    presence alone never satisfies; a meta-less or mismatching directory is
    not-held. Returns (held, named deviation)."""
    try:
        toplevel = _sweep_toplevel(target)
    except _SweepToolError as exc:
        return False, f"cannot resolve the target checkout toplevel: {exc}"
    dir_env = os.environ.get("DONE_LOCK_DIR", "")
    token_env = os.environ.get("DONE_LOCK_TOKEN", "")
    if not dir_env or not token_env:
        return False, (
            "DONE_LOCK_DIR and DONE_LOCK_TOKEN are not both set in the "
            "invoking environment (acquire the target's done lock first)"
        )
    derived = _done_lock_dir_for(toplevel)
    if Path(dir_env) != derived:
        return False, (
            f"DONE_LOCK_DIR does not match the target checkout's derived "
            f"done-lock directory {derived}"
        )
    if not derived.is_dir():
        return False, f"the derived done-lock directory {derived} does not exist"
    meta = derived / "meta.env"
    if not meta.is_file():
        return False, f"the lock directory {derived} carries no meta.env record"
    fields: dict[str, str] = {}
    for line in meta.read_text(encoding="utf-8", errors="replace").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields.setdefault(key.strip(), value.strip())
    if fields.get("lock_token") != token_env:
        return False, "the lock record's lock_token does not equal DONE_LOCK_TOKEN"
    if fields.get("repo_root") != toplevel:
        return False, (
            f"the lock record's repo_root does not equal the target checkout "
            f"root {toplevel}"
        )
    return True, ""


def _parse_worktree_entries(target: Path) -> list[dict]:
    out = _sweep_git_out(target, "worktree", "list", "--porcelain")
    entries: list[dict] = []
    entry: dict | None = None
    for line in out.splitlines():
        if not line.strip():
            if entry is not None:
                entries.append(entry)
                entry = None
            continue
        key, _sep, value = line.partition(" ")
        if key == "worktree":
            entry = {"path": value, "branch": None, "detached": False, "locked": None}
        elif entry is None:
            continue
        elif key == "branch":
            entry["branch"] = value[len("refs/heads/"):] if value.startswith("refs/heads/") else value
        elif key == "detached":
            entry["detached"] = True
        elif key == "locked":
            entry["locked"] = value.strip() or "locked"
    if entry is not None:
        entries.append(entry)
    return entries


def _is_adhoc_shape(path_str: str, toplevel: str) -> bool:
    worktree = Path(path_str)
    primary = Path(toplevel)
    return worktree.parent == primary.parent and worktree.name.startswith(primary.name + _ADHOC_MARK)


def _facts_tmp_root(target: Path) -> Path:
    """The target's facts-resolved tmp directory (the claims roots' parent
    and the twin operand's home); the done skill's docs/tmp default applies
    when the facts key is unresolvable."""
    raw = facts_paths.resolve_toml_key_raw(target, "tmp_dir")
    if raw and raw.strip():
        expanded = Path(raw).expanduser()
        if expanded.is_absolute():
            return expanded
        return target / expanded
    return target / "docs/tmp"


def _claim_is_fresh(claim: Path, now: float) -> bool:
    """A claim file is fresh when its `updated:` line (the execution-claim
    frontmatter's UTC stamp) parses and sits within the freshness bound."""
    try:
        text = claim.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    raw = None
    for line in text.splitlines():
        if line.startswith("updated:"):
            raw = line[len("updated:"):].strip()
            break
    if not raw:
        return False
    try:
        stamp = datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return False
    epoch = calendar.timegm(stamp.timetuple())
    return 0 <= now - epoch < _LIVE_FRESHNESS_SECS


def _candidate_toplevels(cand_path: str, stale: bool) -> set[str]:
    """The candidate path spellings the done-lock script could have keyed a
    lock directory by: the registered path, plus git's own toplevel spelling
    when the tree is on disk."""
    keyed = {cand_path}
    if not stale:
        try:
            keyed.add(_sweep_toplevel(Path(cand_path)))
        except _SweepToolError:
            pass
    return keyed


def _live_session_evidence(target: Path, cand_path: str, plan_basename: str, stale: bool) -> str | None:
    """Arm 5's target-side witnesses: a fresh claim under the target's
    execution-claims/ or authoring-claims/ naming the candidate path or its
    plan slug, or a done-lock directory keyed to the candidate path within
    the freshness bound (its lock root resolved through DONE_LOCK_ROOT).
    Returns the named evidence, or None when no witness holds."""
    stem = plan_basename[: -len(".md")]
    hints = {cand_path, Path(cand_path).name, plan_basename, stem}
    keyed = _candidate_toplevels(cand_path, stale)
    hints.update(keyed)
    now = time.time()
    claims_root = _facts_tmp_root(target)
    for sub in ("execution-claims", "authoring-claims"):
        claims_dir = claims_root / sub
        if not claims_dir.is_dir():
            continue
        try:
            children = sorted(claims_dir.iterdir())
        except OSError:
            continue
        for claim in children:
            if not claim.is_file() or not _claim_is_fresh(claim, now):
                continue
            try:
                text = claim.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if any(hint in text for hint in hints):
                return f"{sub} claim {claim.name}"
    for spelling in sorted(keyed):
        lock_dir = _done_lock_dir_for(spelling)
        try:
            age = now - lock_dir.stat().st_mtime
        except OSError:
            continue
        if 0 <= age <= _LIVE_FRESHNESS_SECS:
            return "a done lock keyed to this worktree"
    return None


def _plan_blobs_on_branch(target: Path, branch: str) -> list[str]:
    """Arm 4's branch-tree membership: `git ls-tree <branch>
    docs/history/plans/` filtered on the `100644 blob` columns to
    dated-`.md` entries at that level (the completed/deferred/rejected
    subtree entries are excluded by the same filter)."""
    listing = _sweep_git_out(target, "ls-tree", branch, _PLANS_DIR + "/")
    blobs: list[str] = []
    for line in listing.splitlines():
        meta, _tab, name = line.partition("\t")
        cols = meta.split()
        if len(cols) >= 2 and cols[0] == "100644" and cols[1] == "blob":
            base = name.rsplit("/", 1)[-1]
            if _DATED_PLAN_RE.match(base):
                blobs.append(base)
    return blobs


def _plan_files_in_worktree(cand_path: str) -> list[str]:
    """Arm 4's worktree-side membership: the candidate's own dated `.md`
    files at docs/history/plans/ (maxdepth 1, the three subtrees excluded)."""
    plans_root = Path(cand_path) / _PLANS_DIR
    if not plans_root.is_dir():
        return []
    return sorted(
        child.name
        for child in plans_root.iterdir()
        if child.is_file() and _DATED_PLAN_RE.match(child.name)
    )


def _evaluate_candidate(target: Path, toplevel: str, cand: dict) -> tuple[str | None, dict]:
    """The six-arm pre-removal chain, stopping at the first failing arm.
    Returns (None, info) when every arm passes, or (skip_reason, {}) with
    the named reason."""
    path = cand["path"]
    # Arm 1: the ad-hoc shape (the enumeration invariant, re-checked so the
    # chain is self-contained).
    if not _is_adhoc_shape(path, toplevel):
        return "not the ad-hoc worktree shape", {}
    # Arm 2: on-disk presence. A registered entry whose path is missing on
    # disk is a stale registration; a porcelain `locked` attribute reports
    # and stops the chain here for BOTH kinds (fold r1 F4: an on-disk
    # locked worktree used to walk the whole chain and only die at removal
    # time, degrading the run to fail), never removed while the operator's
    # lock stands. The stale branch resolves from the porcelain entry here,
    # before arm 4.
    stale = not Path(path).exists()
    if cand["locked"] is not None:
        return "locked registration", {}
    if stale:
        if cand["detached"]:
            return "stale detached registration", {}
        if not cand["branch"]:
            raise _SweepToolError(f"stale registration without a branch: {path}")
    # Arm 3: the clean-tree check for an on-disk candidate (untracked
    # non-ignored files fail the arm); a stale registration passes without
    # evaluation because no on-disk tree exists to carry uncommitted state.
    if not stale:
        proc = _sweep_git(target, "status", "--porcelain", cwd=path)
        if proc.returncode != 0:
            raise _SweepToolError(f"git status failed in {path}: {proc.stderr.strip()}")
        if proc.stdout.strip():
            return "dirty worktree", {}
        # Arm 3b (fold r1 F1): the gitignored staging corpus. A clean
        # porcelain tree is blind to ignored records, so a dead-session
        # worktree whose .ai-playbook/reviews or docs/tmp holds
        # untracked-but-ignored artifacts passed every other arm and the
        # removal destroyed them; the staging surfaces are probed directly
        # and ANY output line reports the candidate. Stale registrations
        # skip this arm (no on-disk tree exists to probe).
        proc = _sweep_git(
            target, "status", "--ignored", "--porcelain", "--",
            ".ai-playbook/reviews", "docs/tmp", cwd=path,
        )
        if proc.returncode != 0:
            raise _SweepToolError(
                f"git status --ignored failed in {path}: {proc.stderr.strip()}"
            )
        if proc.stdout.strip():
            return "unmigrated ignored artifacts present", {}
    # Arm 4: plans-completed membership, exactly one dated plan file whose
    # basename has a HEAD twin in the target (stale re-targeted to the
    # branch's tree, on-disk to the candidate's own manifest).
    blobs = _plan_blobs_on_branch(target, cand["branch"]) if stale else _plan_files_in_worktree(path)
    if not blobs:
        return "zero plan files on branch", {}
    if len(blobs) > 1:
        return "multiple plan files on branch", {}
    basename = blobs[0]
    twin = _sweep_git(target, "cat-file", "-e", f"HEAD:{_COMPLETED_DIR}/{basename}")
    if twin.returncode != 0:
        return "no completed twin in the primary HEAD tree", {}
    # Arm 5: live-session evidence with target-side witnesses.
    evidence = _live_session_evidence(target, path, basename, stale)
    if evidence is not None:
        return f"live-session evidence: {evidence}", {}
    # Arm 6: branch resolution plus post-landing activity. A detached on-disk
    # candidate is reported, never removed; a stale detached one already
    # stopped the chain at arm 2.
    if not stale and cand["detached"]:
        return "detached HEAD worktree", {}
    rev_out = _sweep_git_out(target, "rev-list", cand["branch"], "--not", "HEAD")
    if rev_out.strip():
        # Fold r1 F2b: anchor on the EARLIEST introduction commit. A
        # delete-plus-re-add of the twin re-anchored the previous `-1` form
        # on the re-add, widening the window over genuinely post-landing
        # commits; the minimum %ct across every add commit is the landing's
        # true introduction date, and its commit is the content-scope
        # witness below.
        intro_out = _sweep_git_out(
            target, "log", "--diff-filter=A", "--format=%H %ct", "--",
            f"{_COMPLETED_DIR}/{basename}",
        )
        adds: list[tuple[int, str]] = []
        for line in intro_out.strip().splitlines():
            sha, _sep, ct = line.strip().partition(" ")
            if sha and ct.strip().isdigit():
                adds.append((int(ct.strip()), sha))
        if not adds:
            raise _SweepToolError(
                f"cannot resolve the introduction commit of the completed twin "
                f"{_COMPLETED_DIR}/{basename}"
            )
        intro_ct, intro_sha = min(adds, key=lambda item: item[0])
        for sha in rev_out.split():
            ct_out = _sweep_git_out(target, "show", "-s", "--format=%ct", sha).strip()
            if not ct_out:
                raise _SweepToolError(f"cannot resolve the committer date of {sha}")
            if int(ct_out.splitlines()[-1]) > intro_ct:
                return "post-landing commits on branch", {}
        # Fold r1 F2a: the committer date is not a content check. A branch
        # commit whose content never reached the landing but predates the
        # twin's introduction passes the date check and dies with the
        # branch's force delete, so every changed path since the merge base
        # must sit inside the introduction commit's touched set (a squash
        # landing touches every file its branch touched, so the witnessed
        # residue class stays removable).
        merge_base = _sweep_git_out(target, "merge-base", cand["branch"], "HEAD").strip()
        changed = _sweep_git_out(
            target, "diff", "--name-only", f"{merge_base}..{cand['branch']}"
        )
        if changed.strip():
            # --no-renames expands an archival move (the landing carries the
            # plan from the plans root into completed/, witnessed squash-
            # landing shape) to both endpoints; rename detection would list
            # only the new path and false-report the branch's plans-root
            # vintage as outside the landing's file set.
            touched = {
                line
                for line in _sweep_git_out(
                    target, "show", "--name-only", "--no-renames", "--format=", intro_sha
                ).splitlines()
                if line.strip()
            }
            for changed_path in changed.splitlines():
                if changed_path.strip() and changed_path not in touched:
                    return "branch content outside the landing's file set", {}
    return None, {"basename": basename, "branch": cand["branch"], "stale": stale}


def _candidate_migration_manifest(target: Path, basename: str) -> str | None:
    """The candidate's slug-resolved migration manifest path (plan
    2026-10-19-gate-removal-closeout-accounting Task 2): the completed
    twin's temporary filename differs from the candidate's plan slug, so
    the twin gate run cannot rely on the derived lookup; the sweep passes
    the explicit --migration-manifest instead, resolving the candidate's
    own <PLAN_SLUG> session directory and probing the canonical
    closeout-migration.json name first, the legacy migration-manifest.json
    name second. None when neither supported filename exists (the twin run
    then reports the named legacy skip)."""
    slug = _plan_session_slug(Path(basename))
    manifest_dir = _facts_tmp_root(target) / "execute-plan" / slug
    canonical = manifest_dir / "closeout-migration.json"
    if canonical.is_file():
        return str(canonical)
    legacy = manifest_dir / "migration-manifest.json"
    if legacy.is_file():
        return str(legacy)
    return None


def _parse_branch_disposition(lines: list[str]) -> dict | None:
    """Parse the gate child's branch-disposition line into the disposition
    dict the sweep verdicts carry; None when the gate adjudicated no
    branch (the legacy skip shapes)."""
    for line in lines:
        if not line.startswith("branch-disposition: "):
            continue
        body = line[len("branch-disposition: "):]
        fields: dict[str, str] = {}
        reasons: str | None = None
        for chunk in body.split(" "):
            key, sep, value = chunk.partition("=")
            if sep:
                fields[key] = value
        reasons_part = body.split(" reasons=", 1)
        if len(reasons_part) == 2:
            reasons = reasons_part[1]
        branch = fields.get("branch")
        status = fields.get("disposition")
        if not branch or not status:
            return None
        return {
            "branch": branch,
            "oid": None if fields.get("oid") in (None, "unknown") else fields["oid"],
            "status": status,
            "reasons": (
                [part for part in reasons.split("; ") if part]
                if reasons is not None
                else []
            ),
        }
    return None


def _run_gate_on_twin(target: Path, basename: str, cand_path: str) -> tuple[str, list[str], dict | None]:
    """Run the existing gate-removal verification over the completed twin's
    bytes and return (class, evidence lines, branch disposition). The twin
    is read from the target HEAD tree into a temp file under the target's
    facts-resolved tmp directory, removed on every exit path, so membership
    and the gate key the same landed bytes while the candidate's own copy
    stays outside the trust boundary. The candidate's slug-resolved
    migration manifest rides beside --plan-identity (the temp twin's
    filename differs from the candidate's plan slug, so the derived lookup
    would miss the real manifest), and the gate's branch-disposition line
    is parsed out so the sweep verdicts carry the content disposition and
    the proven OID (plan 2026-10-19-gate-removal-closeout-accounting
    Task 2). The class is `pass`, `empty-owned-set`, or the gate's own
    outcome otherwise (a run with no final OUTCOME line is tool_error per
    the contract's no-line rule)."""
    tmp_root = _facts_tmp_root(target)
    tmp_root.mkdir(parents=True, exist_ok=True)
    blob = _sweep_git(target, "cat-file", "blob", f"HEAD:{_COMPLETED_DIR}/{basename}")
    if blob.returncode != 0:
        raise _SweepToolError(
            f"cannot read the completed twin from the target HEAD tree: {blob.stderr.strip()}"
        )
    fd, tmp_name = tempfile.mkstemp(dir=tmp_root, prefix="sweep-twin-", suffix=".md")
    tmp_path = Path(tmp_name)
    manifest = _candidate_migration_manifest(target, basename)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(blob.stdout.encode("utf-8"))
        proc = subprocess.run(
            [
                sys.executable, str(Path(__file__).resolve()), "gate-removal",
                "--plan", str(tmp_path),
                "--plan-identity", f"{_PLANS_DIR}/{basename}",
                "--target", str(target),
                "--worktree", str(cand_path),
                *(["--migration-manifest", manifest] if manifest else []),
            ],
            capture_output=True,
            text=True,
            cwd=str(target),
        )
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
    lines = proc.stdout.splitlines()
    # Fold r1 F5: the gate child prints its tool_error diagnostics on
    # stderr, so the `gate: ` evidence duty captures both streams (stdout
    # evidence first, then stderr's non-empty lines; the final OUTCOME line
    # is still dropped either way).
    err_lines = [line for line in proc.stderr.splitlines() if line.strip()]
    outcome = None
    if lines and lines[-1].startswith("OUTCOME: "):
        outcome = lines[-1][len("OUTCOME: "):].strip()
    evidence = lines[:-1] if outcome is not None else lines
    evidence = evidence + err_lines
    disposition = _parse_branch_disposition(evidence)
    if outcome == "pass":
        return "pass", evidence, disposition
    if outcome == "fail" and "empty owned set" in proc.stdout:
        return "empty-owned-set", evidence, disposition
    return (outcome if outcome in ("fail", "tool_error") else "tool_error"), evidence, disposition


def _admin_dir_for(common_dir: Path, cand_path: str) -> Path | None:
    """Locate the administrative dir `.git/worktrees/<id>` whose gitdir file
    names the candidate worktree path."""
    admin_root = common_dir / "worktrees"
    if not admin_root.is_dir():
        return None
    wanted = Path(cand_path).resolve()
    for entry in sorted(admin_root.iterdir()):
        gitdir = entry / "gitdir"
        if not gitdir.is_file():
            continue
        try:
            named = Path(gitdir.read_text(encoding="utf-8", errors="replace").strip())
            if named.parent.resolve() == wanted:
                return entry
        except (OSError, ValueError):
            continue
    return None


def _describe_admin_entry(common_dir: Path, entry_id: str) -> str:
    admin = common_dir / "worktrees" / entry_id
    gitdir = admin / "gitdir"
    if gitdir.is_file():
        try:
            named = Path(gitdir.read_text(encoding="utf-8", errors="replace").strip())
            if str(named) not in ("", "."):
                return str(named.parent)
        except OSError:
            pass
    return str(admin)


def _prune_dryrun_entries(target: Path) -> list[tuple[str, str]]:
    """The enumeration-excluded non-destructive probe: the dry-run's
    `Removing worktrees/<id>` lines as (id, line). Never destructive. The
    lines are git diagnostics and arrive on stderr; both streams are
    scanned so a git stream change cannot empty the filter."""
    proc = _sweep_git(target, "worktree", "prune", "--dry-run", "-v")
    if proc.returncode != 0:
        raise _SweepToolError(f"git worktree prune --dry-run failed: {proc.stderr.strip()}")
    entries: list[tuple[str, str]] = []
    for line in proc.stdout.splitlines() + proc.stderr.splitlines():
        match = re.match(r"^Removing worktrees/([^:]+):", line)
        if match:
            entries.append((match.group(1), line))
    return entries


def _release_stale_registration(
    target: Path, common_dir: Path, cand: dict, enumerated_paths: list[str]
) -> str | None:
    """The scoped administrative-dir release of the plan's Terms. Returns a
    deferral reason when a foreign prunable registration survives, raises
    _RemovalFailure on a release command failure. Never `git worktree
    remove`, never a destructive prune."""
    path = cand["path"]
    enumerated_ids = set()
    for other in enumerated_paths:
        admin = _admin_dir_for(common_dir, other)
        if admin is not None:
            enumerated_ids.add(admin.name)
    for entry_id, _line in _prune_dryrun_entries(target):
        if entry_id in enumerated_ids:
            continue
        sibling = _describe_admin_entry(common_dir, entry_id)
        return f"foreign prunable registration present: {sibling}"
    admin = _admin_dir_for(common_dir, path)
    if admin is not None:
        try:
            shutil.rmtree(admin)
        except OSError as exc:
            raise _RemovalFailure(
                f"removal failed: administrative-dir removal {admin.name}: {exc}"
            ) from exc
    for entry in _parse_worktree_entries(target):
        if Path(entry["path"]) == Path(path):
            raise _RemovalFailure(
                "removal failed: the deregistration postcondition failed: "
                "the candidate is still registered"
            )
    return None


def _remove_candidate(
    target: Path, common_dir: Path, cand: dict, info: dict, enumerated_paths: list[str]
) -> str | None:
    """Perform one candidate's release under --apply (plan
    2026-10-19-gate-removal-closeout-accounting Task 2): a STALE
    registration releases through the scoped administrative-dir removal,
    and that is all the sweep ever removes. An on-disk worktree, its
    artifacts, and every branch ref stay operator-controlled: existing
    locks do not exclude ordinary writers, so no release infers a worktree
    or branch deletion from the gate's OUTCOME: pass. Returns a deferral
    reason (a stale release deferred on a foreign prunable registration)
    or None on success; raises _RemovalFailure on any release command
    failure."""
    path = cand["path"]
    if not info["stale"]:
        raise _RemovalFailure(
            f"removal refused: {path} holds an on-disk worktree; the sweep "
            "removes stale registrations only"
        )
    deferred = _release_stale_registration(target, common_dir, cand, enumerated_paths)
    if deferred is not None:
        return deferred
    return None


def _done_lock_script(target: Path) -> Path:
    """The done-lock script resolution: the DONE_LOCK_SCRIPT env override,
    the target's repo-local scripts copy, then the runtime-home copy."""
    override = os.environ.get("DONE_LOCK_SCRIPT")
    if override:
        return Path(override)
    local = target / "scripts" / "done-lock.sh"
    if local.is_file():
        return local
    return Path.home() / ".ai-playbook" / "scripts" / "done-lock.sh"


def _parse_merge_lock_exports(stdout: str) -> dict[str, str]:
    """Parse the acquire subcommands' `export NAME=value` stdout lines."""
    exports: dict[str, str] = {}
    for line in stdout.splitlines():
        for name in ("MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN"):
            prefix = f"export {name}="
            if line.startswith(prefix):
                raw = line[len(prefix):]
                try:
                    exports[name] = shlex.split(raw)[0]
                except (ValueError, IndexError):
                    exports[name] = raw
    return exports


def _merge_lock_acquire(target: Path, label: str = _SWEEP_LABEL) -> tuple[dict[str, str] | None, list[str]]:
    """One try-once merge-acquire of the done-lock script before the first
    release, under `label` (the sweep's own label by default; the
    boundary-mirror operation passes the migrate arm's
    worktree-closeout-migrate label so the producer and the consumer
    serialize on the same lock). Returns (exports, refused lines); exports
    is None on any refusal with the acquire's captured stderr re-prefixed
    `merge-lock: ` per line and its final OUTCOME line dropped (the sweep's
    single final line closes the run)."""
    script = _done_lock_script(target)
    try:
        proc = subprocess.run(
            ["bash", str(script), "merge-acquire", "--label", label],
            capture_output=True,
            text=True,
            cwd=str(target),
        )
    except OSError as exc:
        return None, [f"merge lock script launch failed: {exc}"]
    if proc.returncode != 0:
        return None, [
            line for line in proc.stderr.splitlines() if not line.startswith("OUTCOME:")
        ]
    exports = _parse_merge_lock_exports(proc.stdout)
    if "MERGE_LOCK_DIR" not in exports or "MERGE_LOCK_TOKEN" not in exports:
        return None, ["merge-acquire produced no MERGE_LOCK exports to release against"]
    return exports, []


# The migrate arm's runner-owned merge-lock span (plan
# 2026-10-10-done-closeout-lock-span Task 1): a bounded-wait acquire under
# its own label, held only across the migration's own runtime, with the
# exports parsed in-process and the release in an always-run finally. The
# sweep keeps its try-once posture and label unchanged.
_MIGRATE_MERGE_LABEL = "worktree-closeout-migrate"
_MERGE_MAX_WAIT_DEFAULT_SECS = 300


def _migrate_merge_max_wait() -> int:
    """The bounded-wait deadline for the migrate arm's merge-lock acquire;
    the same override knob the docs sync runner reads, defaulting to 300s."""
    raw = os.environ.get("DOCS_SYNC_MERGE_MAX_WAIT", "").strip()
    if not raw:
        return _MERGE_MAX_WAIT_DEFAULT_SECS
    wait = int(raw)
    if wait < 0:
        raise ValueError(f"DOCS_SYNC_MERGE_MAX_WAIT must not be negative: {raw!r}")
    return wait


def _target_is_git_repository(target: Path) -> bool:
    """True when the target resolves as a git repository toplevel: the merge
    lock is repository-keyed, so a non-repository target has no key to take."""
    probe = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    return probe.returncode == 0


def _merge_lock_wait_acquire(target: Path, label: str, max_wait: int) -> tuple[dict[str, str] | None, list[str]]:
    """One bounded-wait merge-acquire of the done-lock script. Same return
    contract as _merge_lock_acquire: exports is None on any refusal with the
    acquire's captured stderr lines (the final OUTCOME line dropped)."""
    script = _done_lock_script(target)
    try:
        proc = subprocess.run(
            ["bash", str(script), "merge-wait-acquire", "--label", label, "--max-wait", str(max_wait)],
            capture_output=True,
            text=True,
            cwd=str(target),
        )
    except OSError as exc:
        return None, [f"merge lock script launch failed: {exc}"]
    if proc.returncode != 0:
        return None, [
            line for line in proc.stderr.splitlines() if not line.startswith("OUTCOME:")
        ]
    exports = _parse_merge_lock_exports(proc.stdout)
    if "MERGE_LOCK_DIR" not in exports or "MERGE_LOCK_TOKEN" not in exports:
        return None, ["merge-wait-acquire produced no MERGE_LOCK exports to release against"]
    return exports, []


def _migrate_merge_lock_release(target: Path, exports: dict[str, str], started: float) -> None:
    """Always-run release for the migrate arm's span: one held-span stderr
    line at release, then best-effort refusal evidence on stderr (a release
    failure never reclassifies the migration outcome; the operator escapes
    stay merge-status and merge-stale-clean)."""
    held = time.monotonic() - started
    script = _done_lock_script(target)
    env = os.environ.copy()
    env.update(exports)
    print(f"merge-lock: held {held:.1f}s", file=sys.stderr)
    try:
        proc = subprocess.run(
            ["bash", str(script), "merge-release"],
            capture_output=True,
            text=True,
            cwd=str(target),
            env=env,
        )
    except OSError as exc:
        print(f"migrate: merge-lock release failed: {exc}", file=sys.stderr)
        return
    if proc.returncode != 0:
        for line in proc.stderr.splitlines():
            if not line.startswith("OUTCOME:"):
                print(f"migrate: merge-lock release evidence: {line}", file=sys.stderr)
        print(
            f"migrate: merge-lock release failed (exit {proc.returncode}); "
            "the copies already performed stand",
            file=sys.stderr,
        )


def _merge_lock_release(target: Path, exports: dict[str, str]) -> None:
    """Token-fenced release after the last removal. Best-effort with the
    refusal evidence on stderr: the release is not itself a removal, so it
    never reclassifies the run's outcome."""
    script = _done_lock_script(target)
    env = os.environ.copy()
    env.update(exports)
    try:
        proc = subprocess.run(
            ["bash", str(script), "merge-release"],
            capture_output=True,
            text=True,
            cwd=str(target),
            env=env,
        )
    except OSError as exc:
        print(f"sweep: merge-lock release failed: {exc}", file=sys.stderr)
        return
    if proc.returncode != 0:
        for line in proc.stderr.splitlines():
            if not line.startswith("OUTCOME:"):
                print(f"sweep: merge-lock release evidence: {line}", file=sys.stderr)
        print(
            f"sweep: merge-lock release failed (exit {proc.returncode}); "
            "the removals already performed stand",
            file=sys.stderr,
        )


def _sweep_branch_report_line(disposition: dict | None) -> str | None:
    """The sweep's branch-disposition verdict line: names the branch, its
    content-accounting disposition, the proven OID, and the retention
    reasons; None when the gate adjudicated no branch (the legacy skip
    shapes)."""
    if disposition is None:
        return None
    oid = disposition.get("oid") or "unknown"
    line = (
        f"branch-report: branch {disposition['branch']}: disposition "
        f"{disposition['status']} at {oid}"
    )
    reasons = disposition.get("reasons") or []
    if reasons:
        line += "; reasons: " + "; ".join(reasons)
    return line


def _sweep_branch_tip_oid(target: Path, branch: str) -> str | None:
    """The candidate branch's tip OID as the sweep resolves it (one
    rev-parse, the gate's capture form); None when the ref does not
    resolve, so the report can name the explicit unknown instead. Never
    raises: an unresolvable ref is an observation, never a tool error,
    because a skip verdict must always render (plan
    2026-10-29-gate-removal-task2-review-residues Task 2)."""
    proc = _sweep_git(target, "rev-parse", "--verify", branch)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _sweep_skip_branch_line(branch: str, oid: str | None, reason: str) -> str:
    """The sweep's branch-report line for a candidate skipped before gate
    adjudication: the branch identity, the resolved tip OID or the
    explicit `unknown`, and the skip reason, on the same prefix the setup
    filter relays. `skipped` is a sweep-side observation word, not a gate
    disposition: the setup wrapper relays it without reclassifying the
    candidate (plan 2026-10-29-gate-removal-task2-review-residues
    Task 2)."""
    return (
        f"branch-report: branch {branch}: skipped at {oid or 'unknown'}; "
        f"reason: {reason}"
    )


def cmd_sweep(args: argparse.Namespace) -> int:
    """Mechanical ad-hoc worktree residue sweep. Report-only by default;
    --apply requires the invoking run's authentic hold of the target's done
    lock before any enumeration and again before the first release. The
    apply mode removes ONLY stale registrations with no on-disk directory:
    on-disk worktrees, their artifacts, and every branch ref stay
    operator-controlled (existing locks do not exclude ordinary writers),
    never inferred from the gate's OUTCOME: pass. One verdict line per
    candidate plus the branch-disposition lines, and one final OUTCOME:
    line: 0 pass, 1 fail on any removal command failure, 3 tool error."""
    target = Path(args.target)
    if not target.is_dir():
        print(f"sweep: target directory not found: {target}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
    if args.apply:
        held, detail = _verify_authentic_hold(target)
        if not held:
            print(_SWEEP_HOLD_REQUIREMENT, file=sys.stderr)
            print(f"sweep: the hold does not verify: {detail}", file=sys.stderr)
            print("OUTCOME: tool_error")
            return 3
    try:
        toplevel = _sweep_toplevel(target)
        entries = _parse_worktree_entries(target)
    except _SweepToolError as exc:
        print(f"sweep: {exc}", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
    candidates = [
        entry
        for entry in entries
        if Path(entry["path"]) != Path(toplevel) and _is_adhoc_shape(entry["path"], toplevel)
    ]
    removals: list[tuple[dict, dict, dict | None]] = []
    removal_failed = False
    for cand in candidates:
        path = cand["path"]
        try:
            skip, info = _evaluate_candidate(target, toplevel, cand)
            gate_class: str | None = None
            evidence: list[str] = []
            disposition: dict | None = None
            if skip is None:
                gate_class, evidence, disposition = _run_gate_on_twin(target, info["basename"], path)
        except _SweepToolError as exc:
            # Fold r1 F3: a poison candidate (a stale registration whose
            # branch ref no longer resolves, a plumbing failure under one
            # candidate's tree) is reported per candidate and the
            # enumeration continues, so later candidates still get verdicts
            # instead of the whole run aborting mid-enumeration and
            # recurring forever; only enumeration-level failures (the
            # porcelain parse, an unresolvable target) stay run-level
            # tool errors.
            message = str(exc).strip()
            first_line = message.splitlines()[0] if message else "unspecified evaluation failure"
            print(f"report {path}: evaluation error: {first_line}")
            continue
        if skip is not None:
            print(f"report {path}: {skip}")
            # Plan 2026-10-29-gate-removal-task2-review-residues Task 2: a
            # branch-backed skip is retained-branch evidence, so it also
            # rides the branch-report prefix the setup filter relays; a
            # candidate with no branch identity invents no branch data.
            branch = cand["branch"]
            if branch:
                print(_sweep_skip_branch_line(
                    branch, _sweep_branch_tip_oid(target, branch), skip
                ))
            continue
        # A gate fail whose branch disposition is retained is the held
        # removal shape in the gate's own worktree mode: for an on-disk
        # candidate the sweep never removes anything in any mode, so the
        # verdict stays the conservative operator-controlled retained
        # report, with the gate's guard evidence prefixed for visibility.
        retained_fail = (
            gate_class == "fail"
            and disposition is not None
            and disposition.get("status") == "retained"
        )
        if gate_class == "pass" or (retained_fail and not info["stale"]):
            branch_line = _sweep_branch_report_line(disposition)
            if info["stale"]:
                if args.apply:
                    removals.append((cand, info, disposition))
                else:
                    print(
                        f"report {path}: stale registration drain eligible "
                        "(report-only mode; re-run with --apply)"
                    )
            else:
                # On-disk candidates are never removed, in either mode:
                # the worktree, its artifacts, and the branch ref stay
                # operator-controlled (existing locks do not exclude
                # ordinary writers), and the branch disposition above
                # carries the content accounting.
                print(
                    f"report {path}: operator-controlled worktree retained "
                    "(on-disk worktree and artifacts preserved; branch refs "
                    "are never removed by the sweep)"
                )
            if retained_fail:
                for line in evidence:
                    print(f"gate: {line}")
            if branch_line:
                print(branch_line)
        elif gate_class == "empty-owned-set":
            print(f"report {path}: no owned review citations")
        else:
            print(f"report {path}: gate-removal {gate_class}")
            for line in evidence:
                print(f"gate: {line}")
    if removals:
        held, detail = _verify_authentic_hold(target)
        if not held:
            print(_SWEEP_HOLD_REQUIREMENT, file=sys.stderr)
            print(f"sweep: the hold does not verify: {detail}", file=sys.stderr)
            print("OUTCOME: tool_error")
            return 3
        common_dir = _sweep_common_dir(target)
        enumerated_paths = [entry["path"] for entry in candidates]
        exports, refused = _merge_lock_acquire(target)
        if exports is None:
            for line in refused:
                print(f"merge-lock: {line}", file=sys.stderr)
            print("OUTCOME: tool_error")
            return 3
        try:
            for cand, info, disposition in removals:
                path = cand["path"]
                try:
                    deferred = _remove_candidate(target, common_dir, cand, info, enumerated_paths)
                except _RemovalFailure as exc:
                    print(f"report {path}: {exc}")
                    removal_failed = True
                    continue
                if deferred is not None:
                    print(f"report {path}: {deferred}")
                    continue
                print(f"remove {path}")
                if disposition is not None:
                    oid = disposition.get("oid") or "unknown"
                    print(
                        f"registration: drained {path} (stale registration "
                        f"only; branch {disposition['branch']} ref preserved, "
                        f"disposition {disposition['status']} at {oid})"
                    )
                else:
                    print(
                        f"registration: drained {path} (stale registration "
                        "only; branch refs are never removed by the sweep)"
                    )
        finally:
            _merge_lock_release(target, exports)
    print("OUTCOME: fail" if removal_failed else "OUTCOME: pass")
    return 1 if removal_failed else 0


class _SweepUsageParser(argparse.ArgumentParser):
    """Usage-error override scoped to the sweep subcommand (the gate-removal
    parser override pattern): a usage violation is a tool error (exit 3)
    with the contract's final OUTCOME line on stdout, never the argparse
    legacy exit 2 the helper's other subcommands keep."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"sweep: error: {message}", file=sys.stderr)
        print("OUTCOME: tool_error", flush=True)
        raise SystemExit(3)


def build_sweep_parser() -> argparse.ArgumentParser:
    """The sweep parser, built standalone so the legacy parser
    (build_parser) stays byte-unchanged and the usage-override class
    applies to sweep runs only."""
    parser = _SweepUsageParser(
        prog="worktree_closeout_migrate.py sweep",
        description=(
            "Sweep ad-hoc worktree residue beside the primary checkout: "
            "report every candidate, remove only on fully verified preconditions."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    sweep = subparsers.add_parser("sweep", help=parser.description)
    sweep.add_argument(
        "--target",
        required=True,
        help="The primary checkout root the sweep keys candidates beside.",
    )
    sweep.add_argument(
        "--apply",
        action="store_true",
        help="Remove verified candidates; the default is report-only.",
    )
    sweep.set_defaults(func=cmd_sweep)
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture a review-tree baseline and migrate closeout artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser(
        "capture", help="Write a path-plus-SHA-256 baseline of the configured dirs."
    )
    capture.add_argument("--out", required=True, help="Baseline JSON output path.")
    capture.add_argument(
        "--dirs",
        default=None,
        help="Space-separated dirs to capture, relative to the working "
        "directory; resolved from the facts block when omitted.",
    )
    capture.set_defaults(func=cmd_capture)

    migrate = subparsers.add_parser(
        "migrate", help="Copy new and modified files into the target worktree."
    )
    # Transfer operands (plan 2026-10-29-done-gate-report-retention Task 3):
    # exactly one of the canonical baseline arm and the baseline-less scoped
    # inventory arm; the scoped arm supplies the explicitly captured transfer
    # set without fabricating a baseline or requiring non-empty dirs.
    transfer_operands = migrate.add_mutually_exclusive_group(required=True)
    transfer_operands.add_argument(
        "--baseline", default=None, help="Baseline JSON from capture."
    )
    transfer_operands.add_argument(
        "--inventory",
        default=None,
        help=(
            'Scoped-transfer inventory JSON ({"files": [worktree-relative '
            "paths]}): every listed path is an expected transfer, copied, "
            "digest-verified, and appended as a verified migrated row inside "
            "the merge-lock transaction; a missing source or digest mismatch "
            "fails the transaction with no verified row for the item."
        ),
    )
    migrate.add_argument("--source", required=True, help="Source worktree root.")
    migrate.add_argument("--target", required=True, help="Target worktree root.")
    migrate.add_argument("--manifest", required=True, help="Manifest JSON to append to.")
    migrate.add_argument(
        "--suffix", default="1", help="Suffix for collision-renamed copies (<stem>.wt-<suffix><ext>)."
    )
    migrate.set_defaults(func=cmd_migrate)

    mirror = subparsers.add_parser(
        "boundary-mirror",
        help="Mirror one boundary's records to the primary and append the receipt row under the merge lock.",
    )
    mirror.add_argument(
        "--worktree", required=True,
        help="Run worktree root the mirror sources resolve under.",
    )
    mirror.add_argument(
        "--target", required=True,
        help="Primary checkout root the mirrors install into.",
    )
    mirror.add_argument(
        "--manifest", required=True,
        help="Session manifest.md the receipt row is appended to.",
    )
    mirror.add_argument(
        "--run-session-id", required=True,
        help="Stable run tuple field: run_session_id.",
    )
    mirror.add_argument(
        "--plan-path", required=True,
        help="Stable run tuple field: exact plan path.",
    )
    mirror.add_argument(
        "--run-worktree", required=True,
        help="Stable run tuple field: registered run worktree.",
    )
    mirror.add_argument(
        "--boundary-note", default="",
        help="Task-boundary text preceding the mirror tokens in the appended row.",
    )
    mirror.add_argument(
        "--mirror-path", action="append", default=[],
        help="Repository-relative path to mirror from the worktree to the primary; repeatable.",
    )
    mirror.set_defaults(func=cmd_boundary_mirror)

    verify = subparsers.add_parser(
        "verify-records",
        help="Verify cited and claimed review records exist under the target's primary reviews home.",
    )
    verify.add_argument(
        "--plan", required=True, help="The executed plan's file, exactly the caller-resolved path."
    )
    verify.add_argument(
        "--target", required=True, help="Primary checkout root whose reviews home is the verification root."
    )
    verify.add_argument(
        "--claims",
        default=None,
        help="Newline-delimited file of record paths the boundary claims.",
    )
    verify.set_defaults(func=cmd_verify_records)

    copy_cited = subparsers.add_parser(
        "copy-cited-records",
        help="Copy the review records a plan cites from the source reviews "
        "home into the target's reviews home (the lesson-270 run-side bridge "
        "before the verify-records leg).",
    )
    copy_cited.add_argument(
        "--plan", required=True, help="The plan whose citations are copied."
    )
    copy_cited.add_argument(
        "--source", required=True, help="Source root whose reviews home is read (the primary checkout)."
    )
    copy_cited.add_argument(
        "--target", required=True, help="Target root whose reviews home receives the copies (the run root)."
    )
    copy_cited.set_defaults(func=cmd_copy_cited_records)

    stranded = subparsers.add_parser(
        "check-stranded-pointers",
        help="Warning-only stranded doc-pointer check: a landing touching "
        "projects/.ai-playbook/ guideline bodies while docs/AGENTS.md "
        "index-row edits sit uncommitted in the primary checkout (or the "
        "reverse) reports would-strand rows; never blocks, never commits.",
    )
    stranded.add_argument(
        "--repo", default=".",
        help="Primary checkout to inspect (default: the working directory).",
    )
    stranded.add_argument(
        "--landing", default="HEAD",
        help="The owning landing (sha or ref; default HEAD).",
    )
    stranded.add_argument(
        "--base", default=None,
        help="Derive the changed set as the <base>..<landing> diff.",
    )
    stranded.add_argument(
        "--changed", action="append", default=None,
        help="Explicit changed path; repeatable (overrides the diff probe).",
    )
    stranded.set_defaults(func=cmd_check_stranded_pointers)

    # Help-only catalog entries (plan
    # 2026-10-24-closeout-helper-command-discovery): the three specialized
    # commands are routed by main() to their own parsers before this parser
    # runs, so these entries carry no arguments and no handler: they exist
    # only so the generic --help lists every routed command; no runtime
    # dispatch or option parsing is added here.
    subparsers.add_parser(
        "gate-removal",
        help="Gate a worktree removal on the plan's owned review records "
        "being present under the primary reviews home.",
    )
    subparsers.add_parser(
        "owned-files-clean",
        help="Refuse a worktree removal while it holds uncommitted owned "
        "files; verify an owned plan file's byte-identical transfer.",
    )
    subparsers.add_parser(
        "sweep",
        help="Sweep ad-hoc worktree residue beside the primary checkout: "
        "report every candidate, remove only on fully verified preconditions.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    tokens = sys.argv[1:] if argv is None else list(argv)
    if tokens and tokens[0] == "gate-removal":
        # Routed before the legacy parser, which consumes the dispatch
        # token itself (plan 2026-10-19-gate-removal-closeout-accounting
        # Task 4): the remaining tokens parse through the flat
        # usage-override parser (usage violations exit 3 with the final
        # OUTCOME line), and an unexpected failure is caught to the same
        # class so every classified run ends with exactly one final
        # OUTCOME: line; the legacy subcommands keep their argparse exits.
        args = build_gate_removal_parser().parse_args(tokens[1:])
        try:
            return args.func(args)
        except Exception as exc:  # unexpected failure: the tool-error class
            print(
                f"gate-removal: unexpected failure: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            print("OUTCOME: tool_error")
            return 3
    if tokens and tokens[0] == "owned-files-clean":
        # Routed before the legacy parser beside gate-removal: the D-10
        # removal preflight parses through its own parser and every
        # classified run ends with exactly one final OUTCOME line.
        args = build_owned_files_clean_parser().parse_args(tokens[1:])
        try:
            return args.func(args)
        except Exception as exc:  # unexpected failure: the tool-error class
            print(
                f"owned-files-clean: unexpected failure: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            print("OUTCOME: tool_error")
            return 3
    if tokens and tokens[0] == "sweep":
        # Routed before the legacy parser beside gate-removal: sweep parses
        # through the usage-override parser (usage violations exit 3 with
        # the final OUTCOME line), and an unexpected failure is caught to
        # the same class so every classified run ends with exactly one
        # final OUTCOME: line; the legacy subcommands keep their argparse
        # exits.
        args = build_sweep_parser().parse_args(tokens)
        try:
            return args.func(args)
        except Exception as exc:  # unexpected failure: the tool-error class
            print(
                f"sweep: unexpected failure: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            print("OUTCOME: tool_error")
            return 3
    parser = build_parser()
    args = parser.parse_args(tokens)
    func = getattr(args, "func", None)
    if func is None:
        # A help-only catalog token reached the generic parser (the `--`
        # separator bypasses main()'s tokens[0] dispatch); answer the legacy
        # argparse invalid-choice exit class instead of a traceback.
        parser.error(
            f"invalid choice: {args.command!r} (a routed closeout command "
            "must be invoked without the '--' separator)"
        )
    return func(args)


if __name__ == "__main__":
    sys.exit(main())
