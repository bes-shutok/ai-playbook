#!/usr/bin/env python3
"""Parent-side address fan-out helpers for the execute-plan Step 3.3 contract.

Pure grouping, scope-token, patch-verification, and attempt-transition
functions plus the production ``run_address_fanout`` entrypoint. The parent
invokes the entrypoint for every eligible fanned round, persists the returned
lifecycle transitions into ``runtime_state.json.address_fanout`` under the
manifest lock, then merges the returned triage and receipt into the staging
doc and sidecar and lands the round's single address commit. This module
never edits the staging doc and never creates commits. A ``main()`` CLI
(r2 F9) exposes the deterministic grouping, scope-token issuance, and the
production patch witness as shell-invocable operations; the full parent
loop stays in-process because its worker and cancellation ports are the
parent's own launch and cancellation machinery.

Scope-token trust model (r1 F17): the worker scope token is an
attempt-correlation nonce, not a scope credential. The parent never
verifies the token itself; it compares the token's digest against the
digest recorded at launch, so the check catches wrong-round or wrong-attempt
confusion only. Scope enforcement rests on the patch witness (git-derived
changed paths against the worker's canonical file set), not on the token.

Reason-code enum (r1 F21): the ``REASON_*`` constants below are the
definition site of the closed address-fan-out enum (``REASON_CODES``). The
review-staging validator declares the identical set as a frozen literal
(it must stay importable in layouts without the runtime scripts) and a
harness test pins both by equality, so drift between them fails the suite
rather than silently diverging.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import hmac
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

MAX_FANOUT_WORKERS = 3
MAX_ATTEMPTS_PER_WORKER = 2

# Closed reason-code enum for attempt and terminal subset outcomes. These are
# the review-staging extensions.address_fanout reason codes (definition site:
# this module, r1 F21); the runtime driver projects them into its own blocked
# outcomes verbatim.
REASON_COMPLETED = "completed"
REASON_WORKER_ERROR = "worker_error"
REASON_WORKER_TIMEOUT = "worker_timeout"
REASON_CANCELLATION_UNVERIFIED = "cancellation_unverified"
REASON_AMBIGUOUS_PATCH = "ambiguous_patch"
REASON_SCOPE_VIOLATION = "scope_violation"
REASON_STALE_ATTEMPT = "stale_attempt"
REASON_PARENT_MERGE_CONFLICT = "parent_merge_conflict"
REASON_SUPERSEDED = "superseded"

REASON_CODES = frozenset(
    {
        REASON_COMPLETED,
        REASON_WORKER_ERROR,
        REASON_WORKER_TIMEOUT,
        REASON_CANCELLATION_UNVERIFIED,
        REASON_AMBIGUOUS_PATCH,
        REASON_SCOPE_VIOLATION,
        REASON_STALE_ATTEMPT,
        REASON_PARENT_MERGE_CONFLICT,
        REASON_SUPERSEDED,
    }
)

_ATTEMPT_EVENTS = {"launched", "completed", "failed", "cancelled-verified", "cancellation-unverified"}
# Reasons that terminate a worker's subset: no retry is allowed after
# cleanup-unverified, an ambiguous patch, or a scope violation.
_TERMINAL_REASONS = {REASON_CANCELLATION_UNVERIFIED, REASON_AMBIGUOUS_PATCH, REASON_SCOPE_VIOLATION}

_COMMIT_MARKER_RE = re.compile(rb"^(?:From|commit) [0-9a-f]{40}\b", re.MULTILINE)
# One tolerant header regex (r3 F18): each of the four quote marks is an
# INDEPENDENT optional group - there is deliberately no backreference, so
# unpaired shapes parse leniently (a mixed-quoted rename header like
# `diff --git "a/cafe.md" b/new.md`, where the old path needs git's
# C-quoting and the new path does not, parses instead of matching neither
# the plain nor the fully-quoted shape and false-quarantining an honest
# rename as ambiguous_patch). The leniency is safe because malformed
# headers are fenced downstream by the numstat agreement gate, not here:
# do not "simplify" this to a real backreference pair.
_DIFF_GIT_RE = re.compile(rb'^diff --git ("?)a/(.+?)("?) ("?)b/(.+?)"?$')


class WorkerFailure(Exception):
    """A worker attempt failed or timed out; carries the closed reason code."""

    def __init__(self, reason_code: str = REASON_WORKER_ERROR) -> None:
        if reason_code not in {REASON_WORKER_ERROR, REASON_WORKER_TIMEOUT}:
            raise ValueError("worker failure reason must be worker_error or worker_timeout")
        super().__init__(reason_code)
        self.reason_code = reason_code


def canonicalize_finding_files(
    finding_files: Mapping[Any, Sequence[str]] | Sequence[Mapping[str, Any]],
) -> tuple[dict[int, tuple[str, ...]], list[dict[str, Any]]]:
    """Normalize the staging doc's canonical finding_files input.

    Accepts a mapping of finding id to a file iterable, or a list of
    ``{"id": ..., "files": [...]}`` rows. Returns ``(canonical, problems)``
    where ``canonical`` maps int ids to sorted tuples of non-empty
    repository-relative paths and ``problems`` lists
    ``{"id": ..., "reason": "missing-file-data"}`` for every finding without
    an unambiguous non-empty file set. The canonical file set is the only
    input to fan-out grouping.
    """

    canonical: dict[int, tuple[str, ...]] = {}
    problems: list[dict[str, Any]] = []
    items: list[tuple[Any, Any]] = []
    if isinstance(finding_files, Mapping):
        items = list(finding_files.items())
    elif isinstance(finding_files, (list, tuple)):
        for row in finding_files:
            if not isinstance(row, Mapping):
                problems.append({"id": None, "reason": "missing-file-data"})
                continue
            items.append((row.get("id"), row.get("files")))
    else:
        raise ValueError("finding_files must be a mapping or a list of id/files rows")
    for finding_id, files in items:
        try:
            normalized = _canonical_file_set(files)
        except ValueError:
            problems.append({"id": finding_id, "reason": "missing-file-data"})
            continue
        if not normalized:
            problems.append({"id": finding_id, "reason": "missing-file-data"})
            continue
        try:
            canonical_id = int(finding_id)
        except (TypeError, ValueError):
            # A non-coercible finding id degrades to a problem row instead of
            # crashing the entry (r1 F33); the caller falls back to single
            # mode with the reason recorded.
            problems.append({"id": finding_id, "reason": "missing-file-data"})
            continue
        canonical[canonical_id] = normalized
    return canonical, problems


def _problem_ids(problems: Sequence[Mapping[str, Any]]) -> list[Any]:
    """The failing finding ids from the canonicalization problems list.

    Tolerates mixed id types (a non-coercible id degrades to a problem row
    with its original id, r1 F33) instead of raising on the sort.
    """

    ids = [problem["id"] for problem in problems if problem["id"] is not None]
    try:
        return sorted(ids)
    except TypeError:
        return sorted(ids, key=str)


def _canonical_file_set(files: Any) -> tuple[str, ...]:
    if isinstance(files, str) or not isinstance(files, (list, tuple, set, frozenset)):
        raise ValueError("file set must be a sequence of paths")
    normalized: set[str] = set()
    for value in files:
        if not isinstance(value, str):
            raise ValueError("file paths must be strings")
        candidate = value.strip()
        if not candidate or candidate.startswith("/") or candidate.endswith("/"):
            raise ValueError("file paths must be non-empty relative paths")
        parts = [part for part in candidate.split("/") if part not in ("", ".")]
        if not parts or any(part == ".." for part in parts):
            raise ValueError("file paths must stay inside the repository")
        normalized.add("/".join(parts))
    return tuple(sorted(normalized))


def file_affinity_components(findings: Mapping[int, Sequence[str]]) -> list[list[int]]:
    """Deterministic connected components over shared files.

    Findings that share any file land in the same component; returns a list
    of ascending finding-id lists, ordered by descending size then first id.
    """

    parent: dict[int, int] = {finding_id: finding_id for finding_id in findings}

    def find(finding_id: int) -> int:
        while parent[finding_id] != finding_id:
            parent[finding_id] = parent[parent[finding_id]]
            finding_id = parent[finding_id]
        return finding_id

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    file_owner: dict[str, int] = {}
    for finding_id in sorted(findings):
        for path in findings[finding_id]:
            if path in file_owner:
                union(file_owner[path], finding_id)
            else:
                file_owner[path] = finding_id
    grouped: dict[int, list[int]] = {}
    for finding_id in sorted(findings):
        grouped.setdefault(find(finding_id), []).append(finding_id)
    components = [members for _, members in sorted(grouped.items())]
    return sorted(components, key=lambda members: (-len(members), members[0]))


def pack_components(components: Sequence[Sequence[int]], cap: int = MAX_FANOUT_WORKERS) -> list[list[int]]:
    """Greedy packing by descending finding count into at most cap workers.

    Components arrive ordered by descending finding count; each component is
    placed into the worker with the smallest current load (ties break to the
    lowest worker index), so the result is deterministic.
    """

    if cap < 1:
        raise ValueError("worker cap must be at least one")
    loads: list[list[int]] = []
    for component in components:
        if len(loads) < cap:
            loads.append(list(component))
            continue
        target = min(range(cap), key=lambda index: (len(loads[index]), index))
        loads[target].extend(component)
    return [sorted(load) for load in loads]


def plan_fanout(
    finding_files: Mapping[Any, Sequence[str]] | Sequence[Mapping[str, Any]],
    cap: int = MAX_FANOUT_WORKERS,
) -> dict[str, Any]:
    """Deterministic fan-out plan over the canonical finding_files input.

    Returns ``{"mode": "single", "reason": ...}`` whenever any finding lacks
    an unambiguous non-empty file set or when no grouping into two or more
    non-empty disjoint subsets exists; otherwise returns a fanout plan with
    at most ``cap`` pairwise-disjoint worker assignments.
    """

    canonical, problems = canonicalize_finding_files(finding_files)
    if problems:
        return {
            "mode": "single",
            "reason": "missing-file-data",
            "findings": _problem_ids(problems),
        }
    components = file_affinity_components(canonical)
    if len(components) < 2:
        return {"mode": "single", "reason": "no-disjoint-grouping"}
    packed = pack_components(components, cap)
    workers: list[dict[str, Any]] = []
    for index, finding_ids in enumerate(packed, start=1):
        files = sorted({path for finding_id in finding_ids for path in canonical[finding_id]})
        workers.append({"worker": f"w{index}", "findings": list(finding_ids), "files": files})
    return {"mode": "fanout", "workers": workers}


def issue_scope_token(round_id: str, worker: str, attempt: str, secret: str) -> str:
    """Issue the opaque worker scope token bound to the round and attempt."""

    if not secret:
        raise ValueError("scope token issuance requires a non-empty secret")
    payload = f"{round_id}:{worker}:{attempt}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def token_digest(token: str) -> str:
    """Machine-state form of a scope token: only the digest is persisted."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def worker_log_path(round_id: str, worker: str) -> str:
    """Per-worker address log path per agent-logs."""

    return f"review-{round_id}-receiving-review-{worker}.log.md"


def patch_changed_paths(patch: bytes) -> set[str]:
    """Parse the changed path set from a git (binary) patch. Pure."""

    return _patch_changed_path_sides(patch)[0]


def _patch_changed_path_sides(patch: bytes) -> tuple[set[str], set[str]]:
    """Parse ``(all_paths, post_image_paths)`` from one git patch. Pure.

    A rename header (``diff --git a/old b/new``) names both sides: the
    union feeds the scope check, while the post-image side alone is the
    like-with-like comparison partner for git's numstat witness, which
    prints only the post-image path of a rename (r2 F3; verified against
    ``git apply --numstat`` and its ``-z`` form, both of which emit only
    the new path for a rename record). Each side's quote rendering is
    decoded independently (r3 F18): a side git C-quoted keeps its escape
    decoding, an unquoted side stays literal.
    """

    all_paths: set[str] = set()
    post_image: set[str] = set()
    for line in patch.splitlines():
        match = _DIFF_GIT_RE.match(line)
        if not match:
            continue
        sides = [
            _decode_patch_path(match.group(2), quoted=match.group(1) == b'"'),
            _decode_patch_path(match.group(5), quoted=match.group(4) == b'"'),
        ]
        all_paths.update(sides)
        post_image.add(sides[-1])
    return all_paths, post_image


_C_ESCAPES_RE = re.compile(rb"\\(?:([0-7]{3})|(.))", re.DOTALL)
_C_SIMPLE_UNESCAPES = {
    b"a": b"\a",
    b"b": b"\b",
    b"t": b"\t",
    b"n": b"\n",
    b"v": b"\v",
    b"f": b"\f",
    b"r": b"\r",
    b'"': b'"',
    b"\\": b"\\",
}


def _decode_patch_path(raw: bytes, quoted: bool = False) -> str:
    """Decode one patch header path, unescaping git's C-style quoting.

    A quoted rendering (non-ASCII or control bytes) escapes the raw bytes
    as backslash-octal; decoding restores the literal path so the header
    parse and git's ``core.quotePath=false`` numstat output compare like
    with like (r2 F3). Unquoted renderings are literal bytes: their
    backslashes are never escape sequences.
    """

    text = raw.decode("utf-8", "replace")
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
        quoted = True
    if not quoted:
        return text

    def unescape(match: "re.Match[bytes]") -> bytes:
        octal, simple = match.group(1), match.group(2)
        if octal:
            return bytes([int(octal, 8)])
        return _C_SIMPLE_UNESCAPES.get(simple, simple)

    return _C_ESCAPES_RE.sub(unescape, text.encode("utf-8")).decode("utf-8", "replace")


def git_numstat_paths(repo_root: Path | str, patch: bytes) -> tuple[bool, set[str]]:
    """git's own changed-path witness for one patch (r1 F6).

    Runs ``git apply --numstat --binary -`` so the changed-path set comes
    from git's patch parser, not from this module's ``diff --git`` header
    regex. Returns ``(ok, paths)``; ``ok`` is False when git refuses the
    patch (the caller must treat the submission as ambiguous, never as an
    empty-path pass). A traditional unified diff has no ``diff --git``
    headers, so an honest parse of it agrees with git here only when git
    also derives no paths; any disagreement fails closed in
    :func:`verify_patch_submission`.
    """

    completed = subprocess.run(
        ["git", "-c", "core.quotePath=false", "apply", "--numstat", "--binary", "-"],
        cwd=str(repo_root),
        input=patch,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        return False, set()
    paths: set[str] = set()
    for line in completed.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[2].strip():
            paths.add(parts[2].strip())
    return True, paths


def verify_patch_submission(
    submission: Mapping[str, Any],
    worker_files: Sequence[str],
    expected_token_digest: str,
    expected_attempt: str,
    numstat_port: Callable[[bytes], tuple[bool, set[str]]] | None = None,
) -> list[str]:
    """Pure parent patch witness for one worker submission.

    Verifies the attempt echo, the worker token digest, that the patch
    contains no commit object, that git's own numstat parse of the patch
    exists and agrees with the header's post-image paths like with like
    (a rename's numstat names only the new path, r2 F3; a traditional
    unified diff parses to no header paths and is refused, r1 F6), that
    the changed-path receipt matches the parsed patch paths, and that the
    union of both parses (a rename's pre-image included) changes only the
    worker's canonical file set, so an out-of-scope rename source can
    never ride a rename into scope. Returns the deduplicated violation
    reason codes; an empty list means the submission may be accepted and
    applied.
    """

    violations: list[str] = []
    if str(submission.get("attempt", "")) != str(expected_attempt):
        violations.append(REASON_STALE_ATTEMPT)
    digest = submission.get("token_digest")
    if not isinstance(digest, str) or not hmac.compare_digest(digest, expected_token_digest):
        violations.append(REASON_STALE_ATTEMPT)
    patch = submission.get("patch")
    if not isinstance(patch, (bytes, bytearray)):
        violations.append(REASON_AMBIGUOUS_PATCH)
        return _dedupe(violations)
    payload = bytes(patch)
    if not payload.strip():
        # An empty patch is an honest drop-only submission when its
        # changed-path receipt is empty (r1 F9): nothing changed, so the
        # accept records zero changed paths and the worker's counts carry
        # the drop. Any other empty-patch shape is ambiguous, and an empty
        # patch whose counts claim fixes, deferrals, or pending findings is
        # ambiguous too (r3 F17, pending arm r5 F9): zero bytes changed can
        # never reconcile with fixed>0, deferred>0, or pending>0, and the
        # bridge refuses a patch-less return carrying any of them, so a
        # witness pass would admit a shape no documented return produces.
        receipt = submission.get("changed_paths")
        if isinstance(receipt, (list, tuple, set, frozenset)) and len(receipt) == 0:
            counts = submission.get("counts")
            if isinstance(counts, Mapping) and (
                _safe_count(counts.get("fixed")) > 0
                or _safe_count(counts.get("deferred")) > 0
                or _safe_count(counts.get("pending")) > 0
            ):
                violations.append(REASON_AMBIGUOUS_PATCH)
            return _dedupe(violations)
        violations.append(REASON_AMBIGUOUS_PATCH)
        return _dedupe(violations)
    if _COMMIT_MARKER_RE.search(payload):
        violations.append(REASON_SCOPE_VIOLATION)
    parsed, post_image = _patch_changed_path_sides(payload)
    numstat_ok, derived = numstat_port(payload) if numstat_port is not None else (True, set(post_image))
    if not numstat_ok or derived != post_image:
        # git's own parse is the authority (r1 F6), compared like with
        # like (r2 F3): numstat prints only the post-image path of a
        # rename, so the header side matched against it is the post-image
        # side. A patch whose paths the header parser misses, or that
        # numstat refuses, can never pass with an empty or partial
        # changed-path set.
        violations.append(REASON_AMBIGUOUS_PATCH)
        return _dedupe(violations)
    receipt = submission.get("changed_paths")
    if isinstance(receipt, str) or not isinstance(receipt, (list, tuple, set, frozenset)):
        violations.append(REASON_AMBIGUOUS_PATCH)
    elif sorted(str(path) for path in receipt) != sorted(parsed):
        violations.append(REASON_AMBIGUOUS_PATCH)
    outside = sorted((derived | parsed) - set(worker_files))
    if outside:
        violations.append(REASON_SCOPE_VIOLATION)
    return _dedupe(violations)


def _dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def check_active_attempt(
    record: Mapping[str, Any] | None,
    round_id: str,
    worker: str,
    attempt: str,
    token_digest: str,
    generation: int,
    allow_cancelled: bool = False,
    allow_accepted: bool = False,
) -> str | None:
    """Active-attempt compare-and-swap witness. Pure.

    Returns None when the worker, round, attempt id, token digest, and parent
    generation identify the still-active attempt; otherwise returns the
    quarantine reason code for the receipt. Parent-owned bookkeeping
    transitions pass ``allow_cancelled`` to target an attempt whose
    termination was already verified, and ``allow_accepted`` to target an
    accepted attempt (the parent's own post-accept merge bookkeeping, r1 F8);
    worker results never may.
    """

    if not isinstance(record, Mapping) or record.get("round") != str(round_id):
        return REASON_STALE_ATTEMPT
    if record.get("status") != "active":
        return REASON_SUPERSEDED
    if generation != record.get("generation"):
        return REASON_SUPERSEDED
    worker_record = (record.get("workers") or {}).get(worker)
    if not isinstance(worker_record, Mapping):
        return REASON_STALE_ATTEMPT
    status = worker_record.get("status")
    if status in {"completed", "blocked"}:
        return REASON_STALE_ATTEMPT
    if status == "accepted" and not allow_accepted:
        return REASON_STALE_ATTEMPT
    if worker_record.get("active_attempt") != str(attempt):
        return REASON_STALE_ATTEMPT
    registered = next(
        (entry for entry in worker_record.get("attempts", []) if entry.get("id") == str(attempt)),
        None,
    )
    if not isinstance(registered, Mapping):
        return REASON_STALE_ATTEMPT
    allowed_events = {"launched"}
    if allow_cancelled:
        allowed_events.add("cancelled-verified")
    if allow_accepted:
        allowed_events.add("completed")
    if registered.get("event") not in allowed_events:
        return REASON_STALE_ATTEMPT
    digest = token_digest if isinstance(token_digest, str) else ""
    if not hmac.compare_digest(digest, str(registered.get("token_digest", ""))):
        return REASON_STALE_ATTEMPT
    return None


def apply_transition(
    record: Mapping[str, Any] | None,
    transition: Mapping[str, Any],
    clock: Callable[[], float] = time.time,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Pure reducer for one address fan-out lifecycle transition.

    Returns ``(next_record, outcome)``. ``next_record`` is None when the
    transition is invalid or quarantined; ``outcome`` carries status,
    reason_code, evidence, ``mutated`` (persist the next_record), and
    ``quarantined`` (the receipt was refused and never mutates state).
    """

    if not isinstance(transition, Mapping):
        return None, _outcome("blocked", "malformed-result", ["transition must be a mapping"], False, False, "address-fanout:malformed")
    kind = transition.get("kind")
    if kind == "start":
        return _apply_start(record, transition, clock)
    if kind == "attempt":
        return _apply_attempt(record, transition, clock)
    if kind == "accept":
        return _apply_accept(record, transition, clock)
    if kind == "quarantine":
        return _apply_quarantine(record, transition, clock)
    if kind == "block":
        return _apply_block(record, transition, clock)
    return None, _outcome("blocked", "malformed-result", [f"unknown transition kind: {kind}"], False, False, "address-fanout:malformed")


def _outcome(
    status: str,
    reason_code: str,
    evidence: Sequence[str],
    mutated: bool,
    quarantined: bool,
    checkpoint_identity: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "reason_code": reason_code,
        "evidence": list(evidence),
        "mutated": mutated,
        "quarantined": quarantined,
        "checkpoint_identity": checkpoint_identity,
    }


def _stale_outcome(reason: str, worker: str, attempt: str) -> tuple[None, dict[str, Any]]:
    return None, _outcome(
        "blocked",
        reason,
        [f"quarantined receipt for {worker} attempt {attempt}; machine state unchanged"],
        False,
        True,
        f"address-fanout:{worker}:{attempt}",
    )


def _apply_start(
    record: Mapping[str, Any] | None,
    transition: Mapping[str, Any],
    clock: Callable[[], float],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    round_id = transition.get("round")
    baseline = transition.get("baseline")
    grouping = transition.get("grouping")
    workers = transition.get("workers")
    if not isinstance(round_id, str) or not round_id.strip():
        return None, _outcome("blocked", "malformed-result", ["start requires a round"], False, False, "address-fanout:start")
    if not isinstance(baseline, str) or not baseline.strip():
        return None, _outcome("blocked", "malformed-result", ["start requires the pre-round baseline revision"], False, False, f"address-fanout:{round_id}:start")
    if not isinstance(grouping, list) or not isinstance(workers, list) or not workers:
        return None, _outcome("blocked", "malformed-result", ["start requires grouping and worker rows"], False, False, f"address-fanout:{round_id}:start")
    worker_records: dict[str, dict[str, Any]] = {}
    for row in workers:
        if not isinstance(row, Mapping):
            return None, _outcome("blocked", "malformed-result", ["worker rows must be mappings"], False, False, f"address-fanout:{round_id}:start")
        name = row.get("worker")
        digest = row.get("token_digest")
        files = row.get("files")
        if not isinstance(name, str) or not name or name in worker_records:
            return None, _outcome("blocked", "malformed-result", ["worker rows need unique ids"], False, False, f"address-fanout:{round_id}:start")
        if not isinstance(digest, str) or not digest.strip():
            return None, _outcome("blocked", "malformed-result", [f"worker {name} needs a token digest"], False, False, f"address-fanout:{round_id}:start")
        normalized_files = sorted(str(path) for path in (files or ()))
        attempt = str(row.get("attempt", "a1"))
        worker_records[name] = {
            "findings": list(row.get("findings", ())),
            "files": normalized_files,
            "expected_paths": normalized_files,
            "log": str(row.get("log", worker_log_path(round_id, name))),
            "workspace": str(row.get("workspace", "")),
            "attempts": [
                {
                    "id": attempt,
                    "token_digest": digest,
                    "event": "registered",
                    "at": clock(),
                    "reason_code": None,
                }
            ],
            "active_attempt": None,
            "status": "pending",
            "counts": {"fixed": 0, "dropped": 0, "deferred": 0, "pending": 0},
            "accepted": None,
        }
    superseded = isinstance(record, Mapping) and record.get("status") == "active"
    previous_generation = record.get("generation", 0) if isinstance(record, Mapping) else 0
    finding_files_projection: list[dict[str, Any]] = []
    if isinstance(transition.get("finding_files"), list):
        for row in transition["finding_files"]:
            if isinstance(row, Mapping) and row.get("id") is not None:
                finding_files_projection.append({"id": row.get("id"), "files": [str(path) for path in row.get("files", ())]})
    next_record = {
        "round": round_id,
        "status": "active",
        "generation": int(previous_generation) + 1,
        "predecessor_generation": previous_generation if isinstance(record, Mapping) else None,
        "superseded": bool(superseded),
        "baseline": baseline,
        "grouping": grouping,
        "finding_files": finding_files_projection,
        "workers": worker_records,
        "quarantined": [],
        "terminal": {},
        "finalized": None,
        "started_at": clock(),
    }
    reason = REASON_SUPERSEDED if superseded else "started"
    return next_record, _outcome(
        "success",
        reason,
        [f"address fan-out round {round_id} generation {next_record['generation']}"],
        True,
        False,
        f"address-fanout:{round_id}:start",
    )


def _worker_of(record: Mapping[str, Any] | None, transition: Mapping[str, Any]) -> tuple[str, dict[str, Any] | None]:
    round_id = str(transition.get("round", ""))
    worker = str(transition.get("worker", ""))
    if not isinstance(record, Mapping) or record.get("round") != round_id:
        return worker, None
    workers = record.get("workers") or {}
    if not isinstance(workers, Mapping):
        return worker, None
    worker_record = workers.get(worker)
    if not isinstance(worker_record, Mapping):
        return worker, None
    return worker, worker_record


def _active_attempt(worker_record: Mapping[str, Any]) -> dict[str, Any] | None:
    active = worker_record.get("active_attempt")
    for entry in worker_record.get("attempts", []):
        if entry.get("id") == active:
            return entry
    return None


def _apply_attempt(
    record: Mapping[str, Any] | None,
    transition: Mapping[str, Any],
    clock: Callable[[], float],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    worker, worker_record = _worker_of(record, transition)
    attempt = str(transition.get("attempt", ""))
    event = transition.get("event")
    if worker_record is None or event not in _ATTEMPT_EVENTS:
        return _stale_outcome(REASON_STALE_ATTEMPT, worker, attempt)
    if record.get("status") != "active":
        return _stale_outcome(REASON_SUPERSEDED, worker, attempt)
    stale = check_active_attempt(
        record,
        str(transition.get("round", "")),
        worker,
        attempt,
        transition.get("token_digest") if isinstance(transition.get("token_digest"), str) else "",
        transition.get("generation"),
        allow_cancelled=True,
    )
    if event != "launched" and stale is not None:
        return _stale_outcome(stale, worker, attempt)
    next_record = _clone_record(record)
    target = next_record["workers"][worker]
    if event == "launched":
        attempts = target["attempts"]
        if target["status"] == "blocked":
            return None, _outcome("blocked", "terminal-blocked", [f"worker {worker} subset is terminal; no retry"], False, False, f"address-fanout:{worker}:{attempt}")
        if len(attempts) >= MAX_ATTEMPTS_PER_WORKER:
            return None, _outcome("blocked", "attempt-budget-exhausted", [f"worker {worker} already used {MAX_ATTEMPTS_PER_WORKER} attempts"], False, False, f"address-fanout:{worker}:{attempt}")
        if attempts and attempts[-1]["event"] == "registered":
            # First launch: the digest must match the registered start token.
            if str(transition.get("token_digest", "")) != str(attempts[-1]["token_digest"]):
                return _stale_outcome(REASON_STALE_ATTEMPT, worker, attempt)
            attempts[-1]["event"] = "launched"
            attempts[-1]["at"] = clock()
        else:
            previous = attempts[-1] if attempts else None
            if previous is None or previous["event"] != "cancelled-verified":
                return None, _outcome(
                    "blocked",
                    "termination-unverified",
                    [f"worker {worker} retry requires verified cancellation of attempt {previous['id'] if previous else '-'}"],
                    False,
                    False,
                    f"address-fanout:{worker}:{attempt}",
                )
            if not isinstance(transition.get("token_digest"), str) or not transition["token_digest"].strip():
                return None, _outcome("blocked", "malformed-result", [f"retry for {worker} needs the fresh token digest"], False, False, f"address-fanout:{worker}:{attempt}")
            target["attempts"].append({"id": attempt, "token_digest": transition["token_digest"], "event": "launched", "at": clock(), "reason_code": None})
        target["active_attempt"] = attempt
        target["status"] = "active"
        return next_record, _outcome("success", "launched", [f"worker {worker} attempt {attempt} launched"], True, False, f"address-fanout:{worker}:{attempt}")
    entry = _active_attempt(target)
    reason_code = transition.get("reason_code")
    if event == "completed":
        entry["event"] = "completed"
        entry["reason_code"] = REASON_COMPLETED
        target["status"] = "completed"
        return next_record, _outcome("success", "completed", [f"worker {worker} attempt {attempt} completed"], True, False, f"address-fanout:{worker}:{attempt}")
    if event == "cancelled-verified":
        entry["event"] = "cancelled-verified"
        entry["reason_code"] = str(reason_code) if isinstance(reason_code, str) else REASON_WORKER_ERROR
        target["status"] = "cancelled-verified"
        return next_record, _outcome("success", "cancelled-verified", [f"worker {worker} attempt {attempt} termination verified"], True, False, f"address-fanout:{worker}:{attempt}")
    if event == "cancellation-unverified":
        entry["event"] = "cancellation-unverified"
        entry["reason_code"] = str(reason_code) if isinstance(reason_code, str) else REASON_WORKER_ERROR
        target["status"] = "blocked"
        target["active_attempt"] = None
        next_record["terminal"][worker] = REASON_CANCELLATION_UNVERIFIED
        return next_record, _outcome(
            "success",
            REASON_CANCELLATION_UNVERIFIED,
            [f"worker {worker} subset terminally blocked: cleanup-unverified"],
            True,
            False,
            f"address-fanout:{worker}:{attempt}",
        )
    # event == "failed": the second failure blocks the subset terminally.
    entry["event"] = "failed"
    entry["reason_code"] = str(reason_code) if isinstance(reason_code, str) else REASON_WORKER_ERROR
    if len(target["attempts"]) >= MAX_ATTEMPTS_PER_WORKER:
        target["status"] = "blocked"
        target["active_attempt"] = None
        next_record["terminal"][worker] = REASON_WORKER_ERROR
        return next_record, _outcome(
            "success",
            REASON_WORKER_ERROR,
            [f"worker {worker} subset terminally blocked after the second failure"],
            True,
            False,
            f"address-fanout:{worker}:{attempt}",
        )
    target["status"] = "failed"
    return next_record, _outcome("success", "failed", [f"worker {worker} attempt {attempt} failed"], True, False, f"address-fanout:{worker}:{attempt}")


def _apply_accept(
    record: Mapping[str, Any] | None,
    transition: Mapping[str, Any],
    clock: Callable[[], float],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    worker, worker_record = _worker_of(record, transition)
    attempt = str(transition.get("attempt", ""))
    if worker_record is None:
        return _stale_outcome(REASON_STALE_ATTEMPT, worker, attempt)
    if record.get("status") != "active":
        return _stale_outcome(REASON_SUPERSEDED, worker, attempt)
    stale = check_active_attempt(
        record,
        str(transition.get("round", "")),
        worker,
        attempt,
        transition.get("token_digest") if isinstance(transition.get("token_digest"), str) else "",
        transition.get("generation"),
    )
    if stale is not None:
        return _stale_outcome(stale, worker, attempt)
    changed_paths = transition.get("changed_paths")
    changed = sorted(str(path) for path in changed_paths) if isinstance(changed_paths, (list, tuple, set, frozenset)) else []
    outside = sorted(set(changed) - set(worker_record["files"]))
    if outside:
        return None, _outcome(
            "blocked",
            REASON_SCOPE_VIOLATION,
            [f"accepted paths outside the worker scope: {', '.join(outside)}"],
            False,
            False,
            f"address-fanout:{worker}:{attempt}",
        )
    next_record = _clone_record(record)
    target = next_record["workers"][worker]
    entry = _active_attempt(target)
    if entry is not None:
        entry["event"] = "completed"
        entry["reason_code"] = REASON_COMPLETED
    counts = transition.get("counts") if isinstance(transition.get("counts"), Mapping) else {}
    safe_counts = {
        "fixed": _safe_count(counts.get("fixed")),
        "dropped": _safe_count(counts.get("dropped")),
        "deferred": _safe_count(counts.get("deferred")),
        "pending": _safe_count(counts.get("pending")),
    }
    # Conservation (r1 O12): the four counts must account for exactly the
    # worker's finding subset; anything else fails closed with no mutation.
    findings = worker_record.get("findings", ())
    if sum(safe_counts.values()) != len(findings):
        return None, _outcome(
            "blocked",
            "malformed-result",
            [
                f"worker {worker} counts {safe_counts} sum to {sum(safe_counts.values())}, "
                f"expected {len(findings)} findings; accept refused"
            ],
            False,
            False,
            f"address-fanout:{worker}:{attempt}",
        )
    target["counts"] = safe_counts
    target["accepted"] = {
        "attempt": attempt,
        "changed_paths": changed,
        "patch_digest": str(transition.get("patch_digest", "")),
        "generation": transition.get("generation"),
        "at": clock(),
    }
    target["status"] = "accepted"
    return next_record, _outcome("success", "accepted", [f"worker {worker} attempt {attempt} accepted"], True, False, f"address-fanout:{worker}:{attempt}")


def _apply_quarantine(
    record: Mapping[str, Any] | None,
    transition: Mapping[str, Any],
    clock: Callable[[], float],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    worker, worker_record = _worker_of(record, transition)
    attempt = str(transition.get("attempt", ""))
    reason = str(transition.get("reason_code", REASON_STALE_ATTEMPT))
    if worker_record is None:
        return _stale_outcome(REASON_STALE_ATTEMPT, worker, attempt)
    if record.get("status") != "active":
        return _stale_outcome(REASON_SUPERSEDED, worker, attempt)
    stale = check_active_attempt(
        record,
        str(transition.get("round", "")),
        worker,
        attempt,
        transition.get("token_digest") if isinstance(transition.get("token_digest"), str) else "",
        transition.get("generation"),
    )
    if stale is not None:
        return _stale_outcome(stale, worker, attempt)
    next_record = _clone_record(record)
    next_record["quarantined"].append(
        {
            "worker": worker,
            "attempt": attempt,
            "reason_code": reason,
            "detail": str(transition.get("detail", "")),
            "at": clock(),
        }
    )
    if reason in _TERMINAL_REASONS:
        target = next_record["workers"][worker]
        target["status"] = "blocked"
        target["active_attempt"] = None
        entry = _active_attempt(target)
        if entry is not None:
            entry["event"] = "cancelled-verified"
            entry["reason_code"] = reason
        next_record["terminal"][worker] = reason
        return next_record, _outcome(
            "success",
            reason,
            [f"worker {worker} receipt quarantined; subset terminally blocked: {reason}"],
            True,
            True,
            f"address-fanout:{worker}:{attempt}",
        )
    return next_record, _outcome(
        "success",
        reason,
        [f"worker {worker} receipt quarantined: {reason}"],
        True,
        True,
        f"address-fanout:{worker}:{attempt}",
    )


def _apply_block(
    record: Mapping[str, Any] | None,
    transition: Mapping[str, Any],
    clock: Callable[[], float],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    worker, worker_record = _worker_of(record, transition)
    attempt = str(transition.get("attempt", ""))
    reason = str(transition.get("reason_code", REASON_WORKER_ERROR))
    if worker_record is None:
        return _stale_outcome(REASON_STALE_ATTEMPT, worker, attempt)
    if record.get("status") != "active":
        return _stale_outcome(REASON_SUPERSEDED, worker, attempt)
    # Parent-owned terminal bookkeeping: after an accept the attempt is
    # completed and the worker accepted, so the merge-conflict block targets
    # the accepted attempt (r1 F8) and the failure lands in the machine
    # record instead of vanishing.
    stale = check_active_attempt(
        record,
        str(transition.get("round", "")),
        worker,
        attempt,
        transition.get("token_digest") if isinstance(transition.get("token_digest"), str) else "",
        transition.get("generation"),
        allow_accepted=True,
    )
    if stale is not None:
        return _stale_outcome(stale, worker, attempt)
    next_record = _clone_record(record)
    target = next_record["workers"][worker]
    target["status"] = "blocked"
    target["active_attempt"] = None
    next_record["terminal"][worker] = reason
    return next_record, _outcome(
        "success",
        reason,
        [f"worker {worker} subset terminally blocked: {reason}"],
        True,
        False,
        f"address-fanout:{worker}:{attempt}",
    )


def _safe_count(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _clone_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(record))


_TERMINAL_ATTEMPT_EVENTS = {"completed", "cancelled-verified", "cancellation-unverified", "failed"}
_ATTEMPT_STATUS_BY_EVENT = {
    "completed": "success",
    "cancelled-verified": "cancelled",
    "cancellation-unverified": "cancelled",
    "failed": "blocked",
}


def render_sidecar_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    """extensions.address_fanout projection rendered from one snapshot.

    Conforms to the closed three-key sidecar spec (r1 F4): ``round``,
    ``finding_files``, and ``workers`` only. The fan-out generation and the
    terminal-subset map stay in ``runtime_state.json.address_fanout`` (the
    authority); the sidecar is a generated projection. Only attempts with a
    terminal event carry a row, each with its closed-enum reason code: an
    in-flight attempt has no reason code to project, and projecting one
    would fail the --hard gate (r1 F4). Production
    ``run_address_fanout`` terminalizes every attempt before finalize.
    """

    workers: list[dict[str, Any]] = []
    for name in sorted((record.get("workers") or {})):
        worker_record = record["workers"][name]
        attempts: list[dict[str, Any]] = []
        for entry in worker_record.get("attempts", []):
            if entry.get("event") not in _TERMINAL_ATTEMPT_EVENTS:
                continue
            status = _attempt_status(entry)
            attempts.append(
                {
                    "id": entry["id"],
                    "status": status,
                    "reason_code": _attempt_reason_code(entry, status),
                    "log": worker_record.get("log", ""),
                }
            )
        workers.append(
            {
                "id": name,
                "findings": list(worker_record.get("findings", ())),
                "files": list(worker_record.get("files", ())),
                "attempts": attempts,
                "status": _worker_status(worker_record),
                "fixed": worker_record["counts"]["fixed"],
                "dropped": worker_record["counts"]["dropped"],
                "deferred": worker_record["counts"]["deferred"],
                "pending": worker_record["counts"]["pending"],
                "log": worker_record.get("log", ""),
            }
        )
    finding_files: list[dict[str, Any]] = []
    if isinstance(record.get("finding_files"), list) and record.get("finding_files"):
        for row in record["finding_files"]:
            if isinstance(row, Mapping):
                finding_files.append({"id": row.get("id"), "files": list(row.get("files", ()))})
    else:
        for row in record.get("grouping", []) or []:
            if isinstance(row, Mapping):
                for finding_id in row.get("findings", ()):
                    finding_files.append({"id": finding_id, "files": list(row.get("files", ()))})
    return {
        "round": record.get("round"),
        "finding_files": finding_files,
        "workers": workers,
    }


def _attempt_status(entry: Mapping[str, Any]) -> str:
    """The closed-enum attempt status for one terminal attempt row (r1 F32):
    completed projects success, the cancelled pair projects cancelled, and a
    failed (attempt-budget-exhausted) attempt projects blocked."""

    return _ATTEMPT_STATUS_BY_EVENT.get(entry.get("event"), "blocked")


def _attempt_reason_code(entry: Mapping[str, Any], status: str) -> str:
    """The closed-enum reason code for one terminal attempt row.

    Terminal events always record a reason code; the fallbacks keep the
    projection inside the closed enum even for a hand-built record.
    """

    reason = entry.get("reason_code")
    if isinstance(reason, str) and reason in REASON_CODES:
        return reason
    if status == "success":
        return REASON_COMPLETED
    return REASON_WORKER_ERROR


def _worker_status(worker_record: Mapping[str, Any]) -> str:
    if worker_record.get("status") in {"accepted", "completed"}:
        return "complete"
    return "blocked"


def render_manifest_projection(record: Mapping[str, Any]) -> str:
    """manifest.md fan-out projection rendered from the same snapshot."""

    lines = [
        "## Address fan-out",
        f"- round: {record.get('round')}",
        f"- generation: {record.get('generation')}",
        f"- baseline: {record.get('baseline')}",
        f"- status: {record.get('status')}",
    ]
    for name in sorted(record.get("workers") or {}):
        worker_record = record["workers"][name]
        attempts = ", ".join(f"{entry['id']}:{entry['event']}" for entry in worker_record.get("attempts", []))
        lines.append(
            f"- worker {name}: findings {list(worker_record.get('findings', ()))}, files {list(worker_record.get('files', ()))}, attempts {attempts}, status {worker_record.get('status')}"
        )
    terminal = record.get("terminal") or {}
    for worker in sorted(terminal):
        lines.append(f"- terminal blocked subset: {worker} ({terminal[worker]})")
    for entry in record.get("quarantined", []) or []:
        lines.append(f"- quarantined receipt: {entry.get('worker')} {entry.get('attempt')} ({entry.get('reason_code')})")
    return "\n".join(lines) + "\n"


def head_revision(repo_root: Path | str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def build_workspace(
    repo_root: Path | str,
    workspace_root: Path | str,
    baseline: str,
    round_id: str,
    worker: str,
    attempt: str,
) -> Path:
    """Create the ephemeral patch workspace from the pre-round baseline."""

    path = Path(workspace_root) / f"address-{round_id}-{worker}-{attempt}"
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(path), baseline],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return path


def patch_applies_to_baseline(repo_root: Path | str, patch: bytes) -> tuple[bool, str]:
    """git apply --check witness against the recorded baseline.

    The parent worktree starts the round at the recorded baseline and
    accepted patches touch pairwise-disjoint file sets, so checking the
    patch there proves it applies cleanly to the baseline before any
    accepted patch is applied.
    """

    completed = subprocess.run(
        ["git", "apply", "--check", "--binary", "-"],
        cwd=str(repo_root),
        input=patch,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    detail = completed.stderr.decode("utf-8", "replace").strip()
    return completed.returncode == 0, detail


def apply_patch(repo_root: Path | str, patch: bytes) -> None:
    """Apply one verified patch to the parent worktree. Never commits."""

    subprocess.run(
        ["git", "apply", "--binary", "-"],
        cwd=str(repo_root),
        input=patch,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def run_address_fanout(
    round_id: str,
    finding_files: Mapping[Any, Sequence[str]] | Sequence[Mapping[str, Any]],
    repo_root: Path | str,
    workspace_root: Path | str,
    secret: str,
    worker_port: Callable[[dict[str, Any]], Any],
    cancellation_port: Callable[[dict[str, Any]], bool],
    baseline: str | None = None,
    workspace_port: Callable[[Path | str, Path | str, str, str, str, str], Path] | None = None,
    patch_checker: Callable[[Path | str, bytes], tuple[bool, str]] | None = None,
    patch_application_port: Callable[[Path | str, bytes], None] | None = None,
    state_recorder: Callable[[Mapping[str, Any]], Mapping[str, Any] | None] | None = None,
    clock: Callable[[], float] = time.time,
    cap: int = MAX_FANOUT_WORKERS,
) -> dict[str, Any]:
    """Production parent entrypoint for one eligible fanned address round.

    Owns workspace creation, worker launch and collection, termination
    verification before retry, serial application of accepted patches, and
    the merge receipt. Never edits the staging doc and never creates a
    commit: the parent merges the returned triage and lands the round's
    single address commit. ``state_recorder`` persists each lifecycle
    transition into the authoritative machine state and returns the current
    record (a mapping with ``workers`` and ``generation``; the runtime
    driver's outcome carries it under ``address_fanout``); without one,
    transitions apply to a local in-memory record.
    """

    if not isinstance(round_id, str) or not round_id.strip():
        raise ValueError("run_address_fanout requires a round id")
    plan = plan_fanout(finding_files, cap)
    if plan["mode"] != "fanout":
        return {
            "mode": "single",
            "reason": plan.get("reason"),
            "findings": plan.get("findings", []),
            "transitions": [],
            "record": None,
            "merge_receipt": None,
        }
    if not secret:
        raise ValueError("run_address_fanout requires a non-empty scope-token secret")
    repo_root = Path(repo_root)
    workspace_root = Path(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    baseline = baseline or head_revision(repo_root)
    workspace_port = workspace_port or build_workspace
    patch_checker = patch_checker or patch_applies_to_baseline
    patch_application_port = patch_application_port or apply_patch

    def numstat_witness(patch: bytes) -> tuple[bool, set[str]]:
        # git's own changed-path parse (r1 F6 scope witness).
        return git_numstat_paths(repo_root, patch)

    state: dict[str, Any] = {"record": None}

    def record(transition: dict[str, Any]) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None, bool]:
        """Apply one transition; return ``(record, outcome, mutated)``.

        ``mutated`` answers exactly one question: did the authority accept
        THIS transition? The in-memory reducer outcome carries ``mutated``
        directly; a state recorder's outcome either carries it too or
        mirrors it as a non-quarantined success (the runtime driver's
        outcome shape). The value gates the submission take (r2 F1): a
        refused transition must never be read as an acceptance through a
        worker snapshot that still shows an earlier attempt's accepted
        status.
        """

        outcome: Mapping[str, Any] | None = None
        mutated = False
        if state_recorder is not None:
            returned = state_recorder(transition)
            # A recorder returns the authoritative record after persisting;
            # a quarantined or refused transition returns no record and the
            # previously persisted snapshot stays current. The runtime
            # driver's outcome carries the record under ``address_fanout``
            # (r1 F2 seam): unwrap it before the shape check so the only
            # producible production wiring actually advances the live
            # generation and terminal map.
            candidate = returned.get("address_fanout", returned) if isinstance(returned, Mapping) else None
            if isinstance(returned, Mapping):
                outcome = returned
                if "mutated" in returned:
                    mutated = bool(returned.get("mutated"))
                else:
                    mutated = returned.get("status") == "success" and not returned.get("quarantined")
            if isinstance(candidate, Mapping) and isinstance(candidate.get("workers"), Mapping):
                state["record"] = candidate
        else:
            next_record, reducer_outcome = apply_transition(state["record"], transition, clock)
            outcome = reducer_outcome
            mutated = bool(outcome.get("mutated")) if isinstance(outcome, Mapping) else False
            if mutated and next_record is not None:
                state["record"] = next_record
        return state["record"], outcome, mutated

    def current_generation() -> int:
        rec = state["record"]
        return int(rec["generation"]) if isinstance(rec, Mapping) and rec.get("generation") is not None else 0

    def terminal_reason(worker: str) -> str | None:
        rec = state["record"]
        if isinstance(rec, Mapping):
            return (rec.get("terminal") or {}).get(worker)
        return None

    worker_rows: list[dict[str, Any]] = []
    for assignment in plan["workers"]:
        name = assignment["worker"]
        token = issue_scope_token(round_id, name, "a1", secret)
        worker_rows.append(
            {
                "plan": assignment,
                "name": name,
                "attempt_no": 0,
                "token": token,
                "digest": token_digest(token),
                "status": "pending",
                "terminal_reason": None,
                "submission": None,
                "workspace": None,
            }
        )
    canonical, _ = canonicalize_finding_files(finding_files)
    start_transition = {
        "kind": "start",
        "round": round_id,
        "baseline": baseline,
        "grouping": [
            {"worker": row["name"], "findings": list(row["plan"]["findings"]), "files": list(row["plan"]["files"])}
            for row in worker_rows
        ],
        "finding_files": [{"id": finding_id, "files": list(canonical[finding_id])} for finding_id in sorted(canonical)],
        "workers": [
            {
                "worker": row["name"],
                "attempt": "a1",
                "token_digest": row["digest"],
                "findings": list(row["plan"]["findings"]),
                "files": list(row["plan"]["files"]),
                "expected_paths": list(row["plan"]["files"]),
                "log": worker_log_path(round_id, row["name"]),
            }
            for row in worker_rows
        ],
    }
    transitions: list[dict[str, Any]] = [start_transition]
    record(start_transition)

    def fail_attempt(row: dict[str, Any], reason_code: str) -> bool:
        """Cancel the row's current attempt; return True when retry is allowed."""

        attempt = f"a{row['attempt_no']}"
        directive = _directive_for(row, attempt, baseline, round_id, workspace_root)
        if row["workspace"] is not None:
            directive["workspace"] = str(row["workspace"])
        verified = bool(cancellation_port(directive))
        event = "cancelled-verified" if verified else "cancellation-unverified"
        transition = {
            "kind": "attempt",
            "round": round_id,
            "worker": row["name"],
            "attempt": attempt,
            "token_digest": row["digest"],
            "generation": current_generation(),
            "event": event,
            "reason_code": reason_code,
            "at": clock(),
        }
        transitions.append(transition)
        record(transition)
        if not verified:
            row["status"] = "blocked"
            row["terminal_reason"] = terminal_reason(row["name"]) or REASON_CANCELLATION_UNVERIFIED
            return False
        if row["attempt_no"] >= MAX_ATTEMPTS_PER_WORKER:
            failed = {
                "kind": "attempt",
                "round": round_id,
                "worker": row["name"],
                "attempt": attempt,
                "token_digest": row["digest"],
                "generation": current_generation(),
                "event": "failed",
                "reason_code": reason_code,
                "at": clock(),
            }
            transitions.append(failed)
            record(failed)
            row["status"] = "blocked"
            row["terminal_reason"] = terminal_reason(row["name"]) or REASON_WORKER_ERROR
            return False
        next_no = row["attempt_no"] + 1
        token = issue_scope_token(round_id, row["name"], f"a{next_no}", secret)
        row["token"] = token
        row["digest"] = token_digest(token)
        return True

    for row in worker_rows:
        while True:
            row["attempt_no"] += 1
            attempt = f"a{row['attempt_no']}"
            launched = {
                "kind": "attempt",
                "round": round_id,
                "worker": row["name"],
                "attempt": attempt,
                "token_digest": row["digest"],
                "generation": current_generation(),
                "event": "launched",
                "at": clock(),
            }
            transitions.append(launched)
            record(launched)
            workspace = workspace_port(repo_root, workspace_root, baseline, round_id, row["name"], attempt)
            row["workspace"] = workspace
            directive = _directive_for(row, attempt, baseline, round_id, workspace_root)
            directive["workspace"] = str(workspace)
            try:
                collected = worker_port(directive)
            except WorkerFailure as failure:
                if not fail_attempt(row, failure.reason_code):
                    break
                continue
            submissions = [collected] if isinstance(collected, Mapping) else list(collected or ())
            accepted = False
            hard_stop = False
            blocked_report = False
            for submission in submissions:
                if not isinstance(submission, Mapping):
                    continue
                if submission.get("status") == "blocked":
                    # The documented honest blocked report (r1 F9): the
                    # attempt failed through the worker-error path with
                    # cancellation verification, never a terminal
                    # ambiguous_patch quarantine.
                    blocked_report = True
                    break
                violations = verify_patch_submission(submission, row["plan"]["files"], row["digest"], attempt, numstat_port=numstat_witness)
                if not violations:
                    patch = bytes(submission["patch"])
                    if patch.strip():
                        clean, detail = patch_checker(repo_root, patch)
                        if not clean:
                            violations = [REASON_AMBIGUOUS_PATCH]
                            detail = detail or "patch does not apply cleanly to the recorded baseline"
                    else:
                        # An accepted empty patch (r1 F9 drop-only) has
                        # nothing to apply-check: git refuses empty input,
                        # and no bytes means nothing can conflict.
                        clean, detail = True, ""
                    if clean:
                        accept = {
                            "kind": "accept",
                            "round": round_id,
                            "worker": row["name"],
                            "attempt": attempt,
                            "token_digest": row["digest"],
                            "generation": current_generation(),
                            "changed_paths": sorted(str(path) for path in submission.get("changed_paths", ())),
                            "patch_digest": hashlib.sha256(patch).hexdigest(),
                            "counts": submission.get("counts") if isinstance(submission.get("counts"), Mapping) else {},
                            "at": clock(),
                        }
                        transitions.append(accept)
                        recorded, accept_outcome, accept_mutated = record(accept)
                        recorded_worker = (
                            (recorded or {}).get("workers", {}).get(row["name"])
                            if isinstance(recorded, Mapping)
                            else None
                        )
                        accepted_digest = (
                            recorded_worker.get("accepted", {}).get("patch_digest")
                            if isinstance(recorded_worker, Mapping) and isinstance(recorded_worker.get("accepted"), Mapping)
                            else None
                        )
                        if (
                            accept_mutated
                            and isinstance(recorded_worker, Mapping)
                            and recorded_worker.get("status") == "accepted"
                            and accepted_digest == accept["patch_digest"]
                        ):
                            row["submission"] = submission
                            row["status"] = "accepted"
                            accepted = True
                            continue
                        # The accept was refused by machine state (count
                        # conservation, r1 O12, or a lost CAS race or a
                        # stale second accept after an earlier one landed,
                        # r2 F1): fail closed through the quarantine below
                        # instead of applying a patch the authority never
                        # accepted. The gate reads the accept outcome itself
                        # (mutated plus this accept's patch digest), never
                        # the worker snapshot: after a refused second accept
                        # the snapshot still shows the FIRST accept's
                        # accepted status, and taking the submission on it
                        # swapped the audited patch bytes under the round.
                        violations = [REASON_AMBIGUOUS_PATCH]
                        detail = "accept refused by machine state"
                reason = violations[0]
                quarantine = {
                    "kind": "quarantine",
                    "round": round_id,
                    "worker": row["name"],
                    "attempt": str(submission.get("attempt", attempt)),
                    "token_digest": submission.get("token_digest") if isinstance(submission.get("token_digest"), str) else "",
                    "generation": current_generation(),
                    "reason_code": reason,
                    "detail": "; ".join(violations),
                    "at": clock(),
                }
                transitions.append(quarantine)
                record(quarantine)
                if all(violation == REASON_STALE_ATTEMPT for violation in violations):
                    # Late or unauthenticated receipt: quarantined, the
                    # worker's active attempt continues.
                    continue
                if terminal_reason(row["name"]) is not None:
                    row["status"] = "blocked"
                    row["terminal_reason"] = terminal_reason(row["name"])
                    hard_stop = True
                    break
            if accepted or hard_stop:
                break
            if blocked_report:
                if not fail_attempt(row, REASON_WORKER_ERROR):
                    break
                continue
            if not fail_attempt(row, REASON_AMBIGUOUS_PATCH if submissions else REASON_WORKER_ERROR):
                break

    applied: list[str] = []
    for row in worker_rows:
        if row["status"] != "accepted" or row["submission"] is None:
            continue
        patch = bytes(row["submission"]["patch"])
        if not patch.strip():
            # Accepted drop-only submission (r1 F9): nothing to apply.
            applied.append(row["name"])
            continue
        try:
            patch_application_port(repo_root, patch)
        except Exception as exc:  # git apply failure: parent merge conflict
            blocked = {
                "kind": "block",
                "round": round_id,
                "worker": row["name"],
                "attempt": f"a{row['attempt_no']}",
                "token_digest": row["digest"],
                "generation": current_generation(),
                "reason_code": REASON_PARENT_MERGE_CONFLICT,
                "detail": str(exc),
                "at": clock(),
            }
            transitions.append(blocked)
            record(blocked)
            row["status"] = "blocked"
            row["terminal_reason"] = REASON_PARENT_MERGE_CONFLICT
            continue
        applied.append(row["name"])

    final_record = state["record"]
    counts = {"fixed": 0, "dropped": 0, "deferred": 0, "pending": 0}
    for row in worker_rows:
        if row["status"] == "accepted" and isinstance(final_record, Mapping):
            worker_counts = final_record["workers"][row["name"]]["counts"]
            for key in counts:
                counts[key] += int(worker_counts.get(key, 0))
    merge_receipt = {
        "round": round_id,
        "baseline": baseline,
        "workers": [
            {
                "worker": row["name"],
                "findings": list(row["plan"]["findings"]),
                "files": list(row["plan"]["files"]),
                "status": row["status"],
                "terminal_reason": row["terminal_reason"],
                "attempts": [f"a{index}" for index in range(1, row["attempt_no"] + 1)],
            }
            for row in worker_rows
        ],
        "applied": applied,
        "blocked_subsets": dict(final_record.get("terminal") or {}) if isinstance(final_record, Mapping) else {},
        "counts": counts,
    }
    return {
        "mode": "fanout",
        "round": round_id,
        "baseline": baseline,
        "record": final_record,
        "transitions": transitions,
        "merge_receipt": merge_receipt,
    }


def _directive_for(
    row: dict[str, Any],
    attempt: str,
    baseline: str,
    round_id: str,
    workspace_root: Path,
) -> dict[str, Any]:
    workspace = workspace_root / f"address-{round_id}-{row['name']}-{attempt}"
    return {
        "worker": row["name"],
        "round": round_id,
        "attempt": attempt,
        "token": row["token"],
        "token_digest": row["digest"],
        "findings": list(row["plan"]["findings"]),
        "files": list(row["plan"]["files"]),
        "baseline": baseline,
        "workspace": str(workspace),
        "log": worker_log_path(round_id, row["name"]),
    }


_SECTION_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")


def _parse_return_sections(return_text: str) -> dict[str, list[str]]:
    """Split a documented worker return into heading -> raw stripped lines."""

    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in str(return_text).splitlines():
        heading = _SECTION_HEADING_RE.match(line.strip())
        if heading:
            current = heading.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        text = line.strip()
        if text:
            sections[current].append(text)
    return sections


def _strip_bullet(line: str) -> str:
    """Drop a leading Markdown bullet marker from one section line."""

    return line[1:].strip() if line.startswith("-") else line


def _triage_verdict(line: str) -> str:
    """The positional done/drop/pending verdict of one triage line (r3 O10).

    One spelling shared by both parse arms: the verdict is the first word
    of the segment after the finding id, so a colon-bearing reason later
    in the line ("1: done; see docs/x.md:12 for the call site") can never
    redirect the parse the way the old last-colon take did; an unmatched
    verdict is the caller's explicit per-line error instead of a silent
    under-count that failed count conservation terminally.
    """

    segments = line.split(":", 2)
    verdict_source = segments[1] if len(segments) >= 2 else segments[0]
    match = re.match(r"\s*([A-Za-z]+)", verdict_source)
    return match.group(1).lower() if match else ""


def parse_worker_submission(return_text: str, workspace: Path | str) -> dict[str, Any]:
    """Translate one documented Address Fan-out Worker return into a
    verifiable submission mapping (r1 F10).

    The worker prompt (subagent-prompts.md, Address Fan-out Worker) returns
    a workspace-relative patch path and the raw scope token; the parent
    verifier needs the inline patch bytes and the token digest. This helper
    is the shipped bridge: it parses the documented prose shape, reads the
    patch file from the worker's isolated workspace, derives both digests,
    and returns the ``status``/``attempt``/``token_digest``/``patch``/
    ``changed_paths``/``counts`` submission shape
    :func:`verify_patch_submission` and :func:`run_address_fanout` consume.
    A blocked return parses without patch keys (the run loop's blocked-status
    path takes over). Digest disagreements and missing sections fail closed
    with ``ValueError``.

    Counts derive from the per-finding triage lines (``done`` counts fixed,
    ``drop`` counts dropped, ``pending`` counts pending, ``deferred`` is
    always zero for a worker), so the accept conservation check has the
    worker's own accounting.
    """

    sections = _parse_return_sections(return_text)

    def section(heading: str) -> list[str]:
        return sections.get(heading.lower(), [])

    status_lines = section("Status")
    status = status_lines[0].strip().lower() if status_lines else ""
    if status not in {"success", "blocked"}:
        raise ValueError("worker return is missing a 'success' or 'blocked' Status section")

    token = ""
    attempt = ""
    for raw_line in section("Token and attempt echo"):
        line = _strip_bullet(raw_line)
        lowered = line.lower()
        if lowered.startswith("scope token:"):
            token = line.partition(":")[2].strip()
        elif lowered.startswith("attempt id:"):
            attempt = line.partition(":")[2].strip()
    if not token or not attempt:
        raise ValueError("worker return must echo the scope token and attempt id")

    submission: dict[str, Any] = {
        "status": status,
        "attempt": attempt,
        "token": token,
        "token_digest": token_digest(token),
    }
    if status == "blocked":
        return submission

    patch_rel = ""
    for raw_line in section("Binary patch"):
        patch_rel = _strip_bullet(raw_line)
        break
    if not patch_rel:
        raise ValueError("worker return is missing the Binary patch path")
    if patch_rel.strip().lower() == "none":
        # The documented drop-only return (r2 F9): every subset finding is
        # triaged without a code change, so the worker names no patch file.
        # The bridge maps it to the accepted empty submission the parent
        # witness already takes (empty patch plus empty changed-path
        # receipt); any changed-path line here is a malformed drop-only
        # return, never a silent pass.
        leftover = [_strip_bullet(line) for line in section("Changed-path receipt") if _strip_bullet(line)]
        if leftover:
            raise ValueError("a drop-only return (Binary patch: none) must carry an empty Changed-path receipt")
        submission["patch"] = b""
        submission["changed_paths"] = []
        counts = {"fixed": 0, "dropped": 0, "deferred": 0, "pending": 0}
        for raw_line in section("Per-finding triage"):
            line = _strip_bullet(raw_line)
            if not line:
                continue
            verdict = _triage_verdict(line)
            if verdict in {"drop", "dropped"}:
                counts["dropped"] += 1
            elif verdict in {"done", "pending"}:
                # A drop-only return that claims a fix or leaves findings
                # pending contradicts the patch-less shape; fail the bridge
                # so the attempt is retried or blocked, never miscounted.
                raise ValueError(f"a drop-only return (Binary patch: none) cannot carry a {verdict} triage: {line}")
            else:
                raise ValueError(f"per-finding triage line carries no done/drop/pending verdict: {line}")
        submission["counts"] = counts
        return submission
    patch_path = Path(workspace) / patch_rel
    try:
        patch = patch_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"worker patch file is unreadable: {patch_path}: {exc}") from exc
    if not patch.strip():
        raise ValueError("worker patch file is empty")
    submission["patch"] = patch
    submission["patch_digest"] = hashlib.sha256(patch).hexdigest()

    echoed_digest = ""
    for raw_line in section("Patch digest"):
        echoed_digest = _strip_bullet(raw_line)
        break
    if echoed_digest and echoed_digest != submission["patch_digest"]:
        raise ValueError("worker patch digest echo does not match the patch bytes")

    changed_paths = [_strip_bullet(line) for line in section("Changed-path receipt") if _strip_bullet(line)]
    submission["changed_paths"] = changed_paths

    counts = {"fixed": 0, "dropped": 0, "deferred": 0, "pending": 0}
    for raw_line in section("Per-finding triage"):
        line = _strip_bullet(raw_line)
        if not line:
            continue
        verdict = _triage_verdict(line)
        if verdict == "done":
            counts["fixed"] += 1
        elif verdict in {"drop", "dropped"}:
            counts["dropped"] += 1
        elif verdict == "pending":
            counts["pending"] += 1
        else:
            raise ValueError(f"per-finding triage line carries no done/drop/pending verdict: {line}")
    submission["counts"] = counts
    return submission


# ---------------------------------------------------------------------------
# CLI: the parent-side pure operations as a documented invocation surface
# (r2 F9). The full parent loop (``run_address_fanout``) stays the in-process
# entrypoint whose worker and cancellation ports are the parent's own launch
# and cancellation machinery; these operations expose the deterministic
# grouping, scope-token issuance, and the production patch witness so an
# orchestrator can drive and audit them from a shell.
# ---------------------------------------------------------------------------


def _operation_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    finding_files = payload.get("finding_files")
    if not isinstance(finding_files, (Mapping, list)):
        raise ValueError("plan requires a finding_files mapping or row list")
    cap = payload.get("cap")
    # The shell surface cannot project cap-violating groupings (r3 F11):
    # the Step 3.3 contract pins at most three workers, so an override is
    # clamped to the module maximum instead of passed through verbatim.
    plan = plan_fanout(finding_files, min(int(cap), MAX_FANOUT_WORKERS) if cap is not None else MAX_FANOUT_WORKERS)
    return {"operation": "plan", "plan": plan}


def _operation_issue_token(payload: Mapping[str, Any]) -> dict[str, Any]:
    round_id = str(payload.get("round") or "")
    worker = str(payload.get("worker") or "")
    attempt = str(payload.get("attempt") or "")
    secret = str(payload.get("secret") or "")
    token = issue_scope_token(round_id, worker, attempt, secret)
    return {"operation": "issue-token", "token": token, "token_digest": token_digest(token)}


def _operation_verify_submission(payload: Mapping[str, Any], repo_root: Path | str) -> dict[str, Any]:
    submission_path = str(payload.get("submission_path") or "")
    if not submission_path.strip():
        raise ValueError("verify-submission requires a submission_path")
    document = json.loads(Path(submission_path).read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("the submission document must be a JSON object")
    submission = dict(document)
    patch_field = submission.get("patch")
    # JSON cannot carry bytes: the document form encodes the patch as
    # base64 text in ``patch`` (or as a list of byte values).
    if isinstance(patch_field, str):
        submission["patch"] = base64.b64decode(patch_field)
    elif isinstance(patch_field, list) and all(isinstance(item, int) for item in patch_field):
        submission["patch"] = bytes(patch_field)
    worker_files = payload.get("worker_files")
    if not isinstance(worker_files, list):
        raise ValueError("verify-submission requires a worker_files list")
    violations = verify_patch_submission(
        submission,
        [str(path) for path in worker_files],
        str(payload.get("expected_token_digest") or ""),
        str(payload.get("expected_attempt") or ""),
        numstat_port=lambda patch: git_numstat_paths(repo_root, patch),
    )
    return {"operation": "verify-submission", "violations": violations, "accepted": not violations}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=("plan", "issue-token", "verify-submission"), required=True)
    parser.add_argument("--input", help="JSON object payload for the operation")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="repository root for the verify-submission numstat witness")
    args = parser.parse_args(argv)
    try:
        if args.input is None:
            raise ValueError("--input is required for every fan-out operation")
        payload = json.loads(args.input)
        if not isinstance(payload, dict):
            raise ValueError("--input must be a JSON object")
        if args.operation == "plan":
            result = _operation_plan(payload)
        elif args.operation == "issue-token":
            result = _operation_issue_token(payload)
        else:
            result = _operation_verify_submission(payload, args.repo_root)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
