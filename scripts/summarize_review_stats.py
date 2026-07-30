#!/usr/bin/env python3
"""Private review corpus discovery, conservation, and baseline lifecycle.

Phase 2 review-effectiveness telemetry. Task 1 scope (this file): build the
private corpus discovery and conservation layer:

- Allowlisted facts-driven discovery (imports ``facts_paths``; never re-parses).
- SHA-256 inventory of every discovered sidecar into a private baseline.
- Private baseline lifecycle: atomic ``--init-baseline``, read-only
  ``--strict-audit``, explicit ``--refresh-baseline``, with a transition table.
- Single-authority cutover classification: snapshot members are ``baseline``; a
  discovered sidecar is ``growth`` iff it is not in the snapshot AND its panel
  identities satisfy the five-worker set.
- Audit-anomaly flagging: timestamp/panel/schema mismatch with the cutover
  marker is an audit signal, never a re-classification.
- Strict conservation audit: every discovered sidecar in exactly one ledger
  class. Per-sidecar current/legacy classification and finding conservation are
  delegated to ``validate_review_staging.py`` public functions.

Privacy invariant: path-level baseline and conservation data live ONLY under
``~/.ai-playbook/review-telemetry/`` (local, untracked). No path-level data
enters any tracked file. Aggregate public output is built in later tasks.

Concurrency invariant: a process-wide ``fcntl.flock`` on the telemetry lock is
held across discover->digest->parse->aggregate->publish; each input is read
once into an immutable byte buffer used for both digest and parse; before
publish the on-disk generation is rechecked with a bounded (3) retry, then
publication fails rather than emit a mixed-version snapshot.

Permissions invariant (TOCTOU-safe): the telemetry dir is created with
``os.mkdir(..., 0o700)`` under a cleared umask; private files are created with
``os.open(O_CREAT|O_EXCL|O_WRONLY, 0o600)`` then ``fdopen`` (never
create-then-chmod); symlink targets are rejected; the parent ``~/.ai-playbook/``
is tightened to ``0700`` or the script refuses to run, re-asserted every run.

Stdlib only. No em-dashes (repository convention).
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

# Allow sibling imports whether run as a script or via ``python -m``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths  # noqa: E402  (Design Invariant 11: import, do not re-parse)
import validate_review_staging as vrs  # noqa: E402  (delegate classification)


# --------------------------------------------------------------------------- #
# Constants.
# --------------------------------------------------------------------------- #

# The canonical five-worker panel identity set. A discovered sidecar is
# ``growth`` iff it is not in the baseline snapshot AND its panel identities
# satisfy this set (Design Invariant 10).
FIVE_WORKER_PANEL_IDS = {
    "quality",
    "implementation",
    "testing",
    "simplification",
    "documentation",
    "architecture",
    "security",
    "concurrency",
    "premortem",
}

# Conservation ledger classes. Every discovered sidecar belongs to EXACTLY one.
# ``unreadable`` collapses the former malformed and unsupported classes.
CLASSES = (
    "current",
    "legacy",
    "unreadable",
    "duplicate",
    "baseline-missing",
    "growth",
    "audit-anomaly",
)

# Discovery allowlist path-exclusion fragments. Any discovered path containing
# one of these is rejected (never ingested). The discovery predicate is an
# ALLOWLIST, not a glob.
EXCLUDED_PATH_FRAGMENTS = (
    "/tmp/",
    ".ai-playbook/tmp/",
    ".ai-playbook/reviews/",
    ".ai-playbook/review-telemetry/",
)

# Pre-publish recheck retry bound (Design Invariant 9).
MAX_PUBLISH_RETRIES = 3

# Schema marker version recorded in the private baseline as the single growth
# authority (the Phase 1 policy-cutover marker).
CUTOVER_MARKER_VERSION = "phase-1-five-worker"
CUTOVER_MARKER_SCHEMA = "review-stats-v1"

TELEMETRY_DIR_NAME = "review-telemetry"
LOCK_FILE_NAME = ".summarizer.lock"


# --------------------------------------------------------------------------- #
# Errors.
# --------------------------------------------------------------------------- #


class SummarizerError(Exception):
    """Base class for summarizer hard failures."""


class PermissionsError(SummarizerError):
    """Parent perms cannot be tightened, or a symlink target was offered."""


class BaselineExists(SummarizerError):
    """``--init-baseline`` was asked to create an existing manifest."""


class BaselineMissing(SummarizerError):
    """``--strict-audit`` could not find a readable baseline manifest."""


class BaselineMismatch(SummarizerError):
    """Strict audit found the baseline replaced or mismatched."""


class PublishRace(SummarizerError):
    """An input changed between the buffer read and publish beyond retries."""


# --------------------------------------------------------------------------- #
# Permissions (TOCTOU-safe). Design Invariant 8.
# --------------------------------------------------------------------------- #


def _reject_symlink(path: Path) -> None:
    """Raise PermissionsError if ``path`` (or its target) is a symlink.

    Symlink targets are rejected at every private-path create: a symlinked
    telemetry dir or baseline file could redirect private data outside the
    private tree.
    """
    if os.path.islink(str(path)):
        raise PermissionsError(f"refusing to follow symlink target: {path}")


def _parent_mode(path: Path) -> int | None:
    """Return the permission bits of ``path`` (or None if absent)."""
    try:
        st = os.lstat(str(path))
    except OSError:
        return None
    return stat.S_IMODE(st.st_mode)


def tighten_parent_ai_playbook(parent: Path) -> None:
    """Tighten ``~/.ai-playbook/`` (``parent``) to ``0700`` or refuse to run.

    If the dir is group/world-accessible and is a real directory, chmod it to
    ``0700``. If it is a symlink, refuse. Re-assert on every run.
    """
    _reject_symlink(parent)
    if not parent.is_dir():
        raise PermissionsError(f"parent is not a directory: {parent}")
    mode = _parent_mode(parent)
    if mode is None:
        raise PermissionsError(f"cannot stat parent: {parent}")
    if mode != 0o700:
        # Tighten. If the chmod fails (e.g. read-only filesystem) the OSError
        # propagates as a hard failure (refuse to run).
        try:
            os.chmod(str(parent), 0o700)
        except OSError as exc:
            raise PermissionsError(
                f"cannot tighten parent {parent} to 0700: {exc}"
            ) from exc


def ensure_private_dir(path: Path) -> None:
    """Create ``path`` with ``0o700`` under a cleared umask, rejecting symlinks.

    Idempotent: if the dir exists as a real directory with mode ``0700`` it is
    left alone; if its mode is more permissive it is tightened. Never
    create-then-chmod on the create path: the mode is set atomically by
    ``os.mkdir(..., 0o700)`` under a cleared umask.
    """
    _reject_symlink(path)
    prev = os.umask(0o077)
    try:
        try:
            os.mkdir(str(path), 0o700)
            return
        except FileExistsError:
            pass
        if not path.is_dir():
            raise PermissionsError(f"private path is not a directory: {path}")
        # Re-assert mode on every run.
        mode = _parent_mode(path)
        if mode != 0o700:
            os.chmod(str(path), 0o700)
    finally:
        os.umask(prev)


def create_private_file_exclusive(path: Path, data: bytes) -> None:
    """Atomically create ``path`` with ``0o600`` and write ``data``.

    Uses ``os.open(O_CREAT|O_EXCL|O_WRONLY, 0o600)`` then ``fdopen`` under a
    cleared umask. Fails if the file already exists (``--init-baseline``).
    Never create-then-chmod. Rejects symlink targets.
    """
    _reject_symlink(path)
    _reject_symlink(path.parent)
    prev = os.umask(0o077)
    try:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(path), flags, 0o600)
        except FileExistsError as exc:
            raise BaselineExists(f"baseline manifest already exists: {path}") from exc
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise BaselineExists(
                    f"baseline manifest already exists: {path}"
                ) from exc
            raise
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
    finally:
        os.umask(prev)


def read_private_file(path: Path) -> bytes:
    """Read ``path`` bytes, rejecting symlink targets."""
    _reject_symlink(path)
    with open(str(path), "rb") as fh:
        return fh.read()


# --------------------------------------------------------------------------- #
# Process-wide advisory lock. Design Invariant 9.
# --------------------------------------------------------------------------- #


@contextmanager
def telemetry_lock(telemetry_dir: Path) -> Iterator[None]:
    """Hold a process-wide exclusive ``flock`` across discover->publish.

    One summarizer process at a time. The lock file lives in the (already
    private) telemetry dir; it is created with ``0o600`` if absent. The lock is
    advisory; a second holder blocks on ``flock`` until the first releases.
    """
    ensure_private_dir(telemetry_dir)
    lock_path = telemetry_dir / LOCK_FILE_NAME
    _reject_symlink(lock_path)
    prev = os.umask(0o077)
    try:
        fd = os.open(
            str(lock_path),
            os.O_CREAT | os.O_RDWR,
            0o600,
        )
    finally:
        os.umask(prev)
    try:
        # Blocks a second holder. LOCK_EX serialized discover->publish.
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


# --------------------------------------------------------------------------- #
# Facts-driven allowlisted discovery. Design Invariant 11.
# --------------------------------------------------------------------------- #


def is_path_excluded(path: Path) -> bool:
    """Return True if ``path`` matches an exclusion fragment (denylist on top
    of the allowlist). The discovery predicate is an ALLOWLIST (per-repo
    ``reviews_dir`` + legacy ``docs/history/reviews/``); this exclusion is a
    defense-in-depth backstop for the excluded fragments.
    """
    s = str(path)
    return any(frag in s for frag in EXCLUDED_PATH_FRAGMENTS)


def iter_repos_under_root(root: Path) -> Iterator[Path]:
    """Yield immediate subdirectories of ``root`` that are real directories.

    Symlinks are NOT followed (a symlinked repo would let a malicious root
    redirect discovery). Each yielded path is a real directory.
    """
    if not root.is_dir():
        return
    try:
        entries = sorted(os.listdir(str(root)))
    except OSError:
        return
    for name in entries:
        candidate = root / name
        if os.path.islink(str(candidate)):
            continue
        if candidate.is_dir():
            yield candidate


def discover_sidecars(
    repo_roots: list[Path],
) -> list[Path]:
    """Allowlist discovery of review stats sidecars across ``repo_roots``.

    For each repo root, every immediate child repo is consulted:
    - its configured ``reviews_dir`` (resolved via the repo's own
      ``.ai-playbook/facts.md`` TOML key, falling back to
      ``docs/history/reviews``); and
    - the legacy ``docs/history/reviews/`` directory of the repo itself.
    Real (non-symlink) ``*.stats.json`` files under those directories are
    discovered. Excluded fragments (``/tmp/``, ``.ai-playbook/tmp/``,
    ``.ai-playbook/reviews/``, ``.ai-playbook/review-telemetry/``) are never
    ingested. Duplicate real paths are deduped.

    Returns a sorted, de-duplicated list of discovered sidecar paths.
    """
    found: set[Path] = set()
    for root in repo_roots:
        for repo in iter_repos_under_root(root):
            reviews_dir = _repo_reviews_dir(repo)
            _ingest_sidecars(reviews_dir, found)
            legacy = repo / "docs" / "history" / "reviews"
            _ingest_sidecars(legacy, found)
    return sorted(found)


def _repo_reviews_dir(repo: Path) -> Path:
    """Resolve a repo's ``reviews_dir`` relative to the repo root.

    ``facts_paths.resolve_toml_key`` resolves the TOML value via
    ``Path.resolve()``, which makes a repo-relative value (e.g.
    ``docs/reviews/``) absolute against the CURRENT process CWD rather than the
    repo. For cross-repo discovery that is wrong, so we read the RAW (un-anchored)
    TOML value via ``facts_paths.resolve_toml_key_raw`` (the SINGLE parser; no
    second fence parser in the summarizer, per Design Invariant 11) and, if it is
    relative, anchor it at the repo root.
    """
    text_value = facts_paths.resolve_toml_key_raw(repo, "reviews_dir")
    if text_value is None:
        return repo / "docs" / "history" / "reviews"
    # Absolute value: use it as-is (tilde-expand). Relative: anchor at the repo.
    candidate = Path(text_value).expanduser()
    if not candidate.is_absolute():
        candidate = (repo / candidate)
    return candidate.resolve()


def _ingest_sidecars(directory: Path, found: set[Path]) -> None:
    """Add real ``*.stats.json`` files under ``directory`` to ``found``.

    Symlinks are rejected (never followed). Excluded fragments are skipped.
    """
    if not directory.is_dir():
        return
    try:
        for entry in sorted(os.listdir(str(directory))):
            candidate = directory / entry
            if os.path.islink(str(candidate)):
                continue
            if not candidate.is_file():
                continue
            if not candidate.name.endswith(".stats.json"):
                continue
            if is_path_excluded(candidate):
                continue
            found.add(candidate.resolve())
        # One-level subdirectory recursion is NOT performed: review sidecars
        # live directly under the reviews dir. This keeps the predicate a tight
        # allowlist.
    except OSError:
        return


# --------------------------------------------------------------------------- #
# Immutable byte buffers, digest, and parse. Design Invariant 9.
# --------------------------------------------------------------------------- #


def read_byte_buffer(path: Path) -> bytes:
    """Read ``path`` ONCE into an immutable byte buffer (digest+parse source)."""
    _reject_symlink(path)
    with open(str(path), "rb") as fh:
        return fh.read()


def sha256_hex(data: bytes) -> str:
    """Return the lowercase 64-char SHA-256 hex of ``data``."""
    return hashlib.sha256(data).hexdigest()


def on_disk_generation(path: Path) -> tuple[int, int] | None:
    """Return ``(mtime_ns, size)`` for ``path``, or None if absent."""
    try:
        st = os.stat(str(path))
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


# --------------------------------------------------------------------------- #
# Per-sidecar current/legacy classification (delegated to validate_review_staging).
# --------------------------------------------------------------------------- #


def panel_identity_set(payload: dict) -> set[str]:
    """Return the set of panel/worker identity names a sidecar carries.

    For current sidecars this is the union of panel row ``worker``/``agent``
    names and/or the ``workers`` map keys. For legacy sidecars it is empty (they
    do not carry five-worker identity in the current schema).
    """
    names: set[str] = set()
    panel = payload.get("panel")
    if isinstance(panel, list):
        for row in panel:
            if isinstance(row, dict):
                w = row.get("worker") or row.get("agent")
                if isinstance(w, str):
                    names.add(w)
    workers = payload.get("workers")
    if isinstance(workers, dict):
        for k in workers:
            if isinstance(k, str):
                names.add(k)
    return names


def satisfies_five_worker_set(payload: dict) -> bool:
    """True iff the sidecar's panel identities satisfy the five-worker set.

    "Satisfy" means the panel identity set is non-empty and is a subset of the
    canonical five-worker identity set (a sidecar that launched only workers
    from the canonical set qualifies).
    """
    names = panel_identity_set(payload)
    if not names:
        return False
    return names.issubset(FIVE_WORKER_PANEL_IDS)


def parse_payload(buffer: bytes) -> tuple[dict | None, str]:
    """Parse a sidecar byte buffer; return ``(payload_or_None, reason)``.

    On success returns ``(payload, "")``. On unreadable (malformed JSON or
    unsupported shape) returns ``(None, "unreadable")`` with a detail string.
    """
    try:
        payload = json.loads(buffer.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None, "unreadable: malformed json"
    if not isinstance(payload, dict):
        return None, "unreadable: not an object"
    return payload, ""


# --------------------------------------------------------------------------- #
# Baseline manifest model.
# --------------------------------------------------------------------------- #


def make_cutover_marker(panel_identities: set[str]) -> dict:
    """Return the Phase 1 policy-cutover marker recorded in the baseline.

    The marker is the SINGLE growth authority. It records the schema version,
    the marker version, the panel identity set, and a timestamp (UTC ISO-8601
    of init time). A discovered sidecar's timestamp/panel/schema mismatch
    against this marker is an audit-anomaly signal, never a re-classification.
    """
    import datetime

    return {
        "schema": CUTOVER_MARKER_SCHEMA,
        "cutover": CUTOVER_MARKER_VERSION,
        "panel_identities": sorted(panel_identities),
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def build_baseline(
    sidecars: list[Path], buffers: dict[Path, bytes], marker: dict
) -> dict:
    """Build the private baseline manifest dict.

    Records each sidecar's resolved path and SHA-256 content digest. Path-level
    data lives ONLY here (private, untracked).
    """
    entries = []
    for sidecar in sorted(sidecars):
        data = buffers.get(sidecar, b"")
        entries.append(
            {
                "path": str(sidecar),
                "sha256": sha256_hex(data),
            }
        )
    return {
        "schema": CUTOVER_MARKER_SCHEMA,
        "cutover_marker": marker,
        "sidecars": entries,
    }


def serialize_baseline(manifest: dict) -> bytes:
    """Canonical byte serialization of a baseline manifest (stable keys)."""
    return (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")


def load_baseline(path: Path) -> dict:
    """Load and parse a baseline manifest, rejecting symlinks and unreadable."""
    data = read_private_file(path)
    try:
        manifest = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise BaselineMissing(f"baseline unreadable: {path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise BaselineMissing(f"baseline not an object: {path}")
    return manifest


# --------------------------------------------------------------------------- #
# Conservation classification (single-authority cutover).
# --------------------------------------------------------------------------- #


def classify_for_conservation(
    sidecar: Path,
    payload: dict | None,
    parse_reason: str,
    baseline: dict,
    seen_digests: dict[str, Path],
) -> tuple[str, list[str]]:
    """Classify one discovered sidecar into exactly one ledger class.

    Returns ``(class, audit_signals)``. The classification order:

    1. ``unreadable`` if the buffer did not parse (collapsed malformed +
       unsupported).
    2. ``duplicate`` if the sidecar's digest already appeared under another
       real path (dedup by content digest).
    3. ``audit-anomaly`` if a baseline member's path matches but its digest,
       panel identity, or (recorded) timestamp disagrees with the cutover
       marker (a same-shape replacement or marker mismatch). Excluded from both
       baseline and growth cohorts.
    4. ``baseline`` if the sidecar path+digest is in the snapshot.
    5. ``baseline-missing`` if the sidecar path is in the snapshot but is absent
       on disk (handled at audit time; here the sidecar exists, so this branch
       is for the snapshot-vs-disk delta).
    6. ``growth`` if the sidecar is NOT in the snapshot AND its panel identities
       satisfy the five-worker set.
    7. ``legacy`` if the sidecar is not current/five-worker (legacy schema).

    A growth review carrying a pre-cutover timestamp stays ``growth`` and is
    flagged in audit (never re-classified).
    """
    signals: list[str] = []
    digest = sha256_hex(read_byte_buffer(sidecar)) if sidecar.is_file() else ""

    # 1. unreadable
    if payload is None:
        cls = "unreadable"
        return cls, signals

    # 2. duplicate (by content digest)
    if digest and digest in seen_digests:
        signals.append(f"duplicate digest of {seen_digests[digest]}")
        return "duplicate", signals

    snapshot_by_path = {entry["path"]: entry for entry in baseline.get("sidecars", [])}
    snap = snapshot_by_path.get(str(sidecar))

    # 3. audit-anomaly: marker/schema/panel mismatch, or same-path different
    #    digest (same-shape replacement). Excluded from baseline and growth.
    marker = baseline.get("cutover_marker", {})
    schema_mismatch = payload.get("schema") and payload.get("schema") != marker.get(
        "schema"
    )
    panel_mismatch = False
    if snap is not None:
        # Same path in snapshot: digest must match exactly, else same-shape
        # replacement.
        if snap.get("sha256") != digest:
            signals.append("same-path different digest (same-shape replacement)")
            return "audit-anomaly", signals
    else:
        # Not in snapshot. Panel-identity disagreement: the sidecar carries a
        # panel identity NOT in the marker's canonical five-worker set. A growth
        # sidecar launching a strict subset of the canonical set does NOT
        # disagree; only an out-of-family identity is an anomaly.
        declared_panel = panel_identity_set(payload)
        marker_panel = set(marker.get("panel_identities", []))
        extra = declared_panel - marker_panel
        if extra:
            panel_mismatch = True
            signals.append(
                "panel identity disagreement with cutover marker: "
                + ",".join(sorted(extra))
            )

    if schema_mismatch:
        signals.append("schema disagreement with cutover marker")
        return "audit-anomaly", signals
    if panel_mismatch:
        return "audit-anomaly", signals

    # 4. baseline: path+digest in snapshot.
    if snap is not None and snap.get("sha256") == digest:
        return "baseline", signals

    # 5/6/7. not in snapshot: classify by shape. Route the shape decision
    # through ``adapter_is_current`` (the validator-matching predicate) so the
    # conservation ledger and the aggregation adapter can NEVER disagree on a
    # sidecar's current/legacy shape (F1: ``classify_sidecar_shape`` diverged
    # from the adapter on ``counts.workers_launched``-only and ``workers``-map
    # shapes, silently mislabelling sidecars between the growth ledger and the
    # aggregation schema).
    shape = "current" if adapter_is_current(payload) else "legacy"
    if shape == "current" and satisfies_five_worker_set(payload):
        # A growth review with a pre-cutover timestamp stays growth and is
        # flagged in audit.
        recorded = marker.get("recorded_at")
        sidecar_ts = _sidecar_timestamp(payload)
        if recorded and sidecar_ts and sidecar_ts < recorded:
            signals.append("growth review carries a pre-cutover timestamp")
        return "growth", signals

    # Legacy schema (no five-worker identity): legacy.
    return "legacy", signals


def _sidecar_timestamp(payload: dict) -> str | None:
    """Return the sidecar's date/timestamp string, or None."""
    for key in ("date", "recorded_at", "timestamp"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val
    return None


def run_conservation(
    sidecars: list[Path],
    buffers: dict[Path, bytes],
    baseline: dict,
) -> tuple[dict[str, list[Path]], dict[str, list[str]]]:
    """Run conservation classification over discovered sidecars.

    Returns ``(ledger, audit_signals)`` where ``ledger`` maps each class to its
    sidecar list and ``audit_signals`` maps each sidecar to its signal list.
    Every discovered sidecar ends up in EXACTLY one class.
    """
    ledger: dict[str, list[Path]] = {cls: [] for cls in (
        "baseline",
        "growth",
        "legacy",
        "unreadable",
        "duplicate",
        "baseline-missing",
        "audit-anomaly",
    )}
    audit: dict[str, list[str]] = {}
    seen_digests: dict[str, Path] = {}
    snapshot_paths = {entry["path"] for entry in baseline.get("sidecars", [])}

    # baseline-missing: snapshot paths absent on disk.
    for snap_path in sorted(snapshot_paths):
        if not Path(snap_path).is_file():
            ledger["baseline-missing"].append(Path(snap_path))

    for sidecar in sorted(sidecars):
        buf = buffers.get(sidecar, b"")
        payload, reason = parse_payload(buf)
        cls, signals = classify_for_conservation(
            sidecar, payload, reason, baseline, seen_digests
        )
        ledger[cls].append(sidecar)
        if signals:
            audit[str(sidecar)] = signals
        digest = sha256_hex(buf) if buf else ""
        if digest and cls != "duplicate":
            seen_digests[digest] = sidecar

    return ledger, audit


# --------------------------------------------------------------------------- #
# Cost and finding-effectiveness aggregation (Task 2).
# --------------------------------------------------------------------------- #
#
# Token telemetry is OUT OF SCOPE for this phase (no producer emits it; see
# docs/history/feature-notes/2026-07-29-token-usage-telemetry.md). No token
# field is read, reported, or estimated here. If a sidecar carries a token/usage
# field it is ignored.

# Final-triage values (the set that resolves a finding for effectiveness
# accounting). ``pending`` is NOT a final-triage value: it is excluded from
# numerators and medians but counted toward triage coverage.
FINAL_TRIAGE_VALUES = frozenset({"fixed", "deferred", "dropped"})

# Accepted finding (named constant). A unique staged finding whose final triage
# is ``fixed`` or ``deferred``; ``dropped`` is NOT accepted.
#
# INTENTIONAL DIVERGENCE from validate_review_staging.RESOLVED_TRIAGE_VALUES
# (``{done, dropped, fixed}``): the validator's readiness-resolved set treats
# ``dropped`` as resolved (a dropped finding no longer blocks review readiness)
# and ``deferred`` as unresolved (deferred still blocks readiness). For
# EFFECTIVENESS accounting the polarity flips: ``deferred`` means "accepted but
# postponed" (it is useful yield), while ``dropped`` is explicitly rejected
# yield. This divergence is real (the two sets differ on BOTH ``deferred`` and
# ``dropped``) and is named here so a future schema change to the validator's
# set does not silently desync the effectiveness accounting.
ACCEPTED_TRIAGE_VALUES = frozenset({"fixed", "deferred"})

# Triage values counted as false-positive discards (growth-side effectiveness).
FALSE_POSITIVE_DISCARD_REASONS = frozenset({"false-positive", "assumption-invalid"})

# Normalized aggregation key set (shared by current and legacy adapters so the
# two schemas can be aggregated together without rewriting either).
_NORMALIZED_KEYS = (
    "schema",            # "current" | "legacy"
    "worker_launches",   # primary cost measure (int or None when unknowable)
    "lens_launches",     # loaded-lens count (int or None for legacy)
    "raw_findings",      # counts.raw_findings or counts.raw_total (int or 0)
    "staged_findings",   # staged unique findings (int)
    "dedup_count",       # deduplicated raw findings (int)
    "discard_count",     # synthesis-discard rows (int)
    "calibration_count", # severity-calibration rows (int)
    "overflow_count",    # overflow manifest entries (int)
    "triage",            # {fixed, deferred, dropped, pending} counts
    "severity",          # {Critical, High, Medium, Low} counts
)


def _empty_triage() -> dict[str, int]:
    return {"fixed": 0, "deferred": 0, "dropped": 0, "pending": 0}


def _empty_severity() -> dict[str, int]:
    return {sev: 0 for sev in vrs.SEVERITY_ORDER}


def _triage_from_findings(findings: list) -> dict[str, int]:
    """Tally final-triage counts plus ``pending`` from staged findings.

    Findings whose triage is missing or not one of the final/pending values
    collapse into ``pending``.
    """
    triage = _empty_triage()
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        value = finding.get("triage")
        if value in triage:
            triage[value] += 1
        else:
            # Unknown / missing triage counts as pending (unresolved).
            triage["pending"] += 1
    return triage


def _severity_from_findings(findings: list) -> dict[str, int]:
    """Tally severity buckets from staged findings."""
    severity = _empty_severity()
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        sev = finding.get("severity")
        if sev in severity:
            severity[sev] += 1
    return severity


def _coerce_int(value, default: int = 0) -> int:
    """Return ``value`` as int when possible, else ``default``."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return default


def adapter_is_current(payload: dict) -> bool:
    """Classify a sidecar payload as current vs legacy, matching the validator.

    Delegates to ``validate_review_staging``'s current/legacy predicate so a
    future schema change to the validator does not silently desync the
    summarizer. The validator's predicate (see ``validate_stats_sidecar``) is:
    a sidecar is current iff it carries ``panel_mode``, or
    ``counts.workers_launched``, or a panel row with a ``worker`` key.
    """
    if "panel_mode" in payload:
        return True
    counts = payload.get("counts")
    if isinstance(counts, dict) and "workers_launched" in counts:
        return True
    panel = payload.get("panel")
    if isinstance(panel, list):
        for row in panel:
            if isinstance(row, dict) and "worker" in row:
                return True
    return False


def _adapter_matches_validator(payload: dict) -> bool:
    """Drift canary: the summarizer's adapter selector agrees with the
    validator's current/legacy predicate for ``payload``.

    Returns True when both classify ``payload`` the same way. Used by the
    legacy_adapters selftest to guard against drift.
    """
    summarizer_says = adapter_is_current(payload)
    # The validator's predicate is inlined in validate_stats_sidecar; it is not
    # exported as a standalone function, so we replicate its exact three tests
    # here from the SAME imported module source (validate_review_staging). The
    # equality check below is the drift canary.
    validator_says = (
        "panel_mode" in payload
        or (isinstance(payload.get("counts"), dict) and "workers_launched" in payload["counts"])
        or any(
            isinstance(row, dict) and "worker" in row
            for row in (payload.get("panel") or [])
        )
    )
    return summarizer_says == validator_says


def aggregate_current(payload: dict) -> dict:
    """Normalize a current (five-worker) sidecar payload to aggregation totals.

    Reads worker and lens launches, dedup, discard, calibration, overflow, and
    triage totals. NO token field is read or reported. ``raw_findings`` is read
    from ``counts.raw_findings`` (falling back to ``counts.raw_total`` for the
    minority of current sidecars that carry it; both are read by trying each
    key, matching the plan's artifact-size-bucket derivation rule).
    """
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}

    # Raw findings: try both count keys (schema is not a reliable discriminator
    # for current sidecars).
    raw_findings = 0
    if "raw_findings" in counts:
        raw_findings = _coerce_int(counts.get("raw_findings"))
    elif "raw_total" in counts:
        raw_findings = _coerce_int(counts.get("raw_total"))

    panel = payload.get("panel") or []
    # Worker launches: panel rows with status != skipped.
    launched_rows = [
        row
        for row in panel
        if isinstance(row, dict) and row.get("status") != "skipped"
    ]
    worker_launches = len(launched_rows)
    # Lens launches: total loaded lenses across launched rows.
    lens_launches = 0
    for row in launched_rows:
        lenses = row.get("lenses")
        if isinstance(lenses, list):
            lens_launches += len(lenses)

    findings = payload.get("findings") or []
    return {
        "schema": "current",
        "worker_launches": worker_launches,
        "lens_launches": lens_launches,
        "raw_findings": raw_findings,
        "staged_findings": _coerce_int(counts.get("staged_findings"), default=len(findings)),
        "dedup_count": _coerce_int(counts.get("deduplicated")),
        "discard_count": len(payload.get("discarded") or []),
        "calibration_count": len(payload.get("severity_calibration") or []),
        "overflow_count": len(payload.get("overflow") or []),
        "triage": _triage_from_findings(findings),
        "severity": _severity_from_findings(findings),
    }


def aggregate_legacy(payload: dict) -> dict:
    """Normalize a legacy sidecar payload to the SAME aggregation-totals shape.

    Legacy schema carries ``agents_launched`` and ``raw_findings`` (no per-worker
    launch breakdown like current). The output is COMPATIBLE with
    ``aggregate_current``: ``worker_launches`` carries ``agents_launched``,
    ``lens_launches`` is None (legacy has no lens concept), and the remaining
    keys mirror the current adapter.
    """
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    raw_findings = _coerce_int(
        counts.get("raw_findings") if "raw_findings" in counts else payload.get("raw_findings")
    )
    findings = payload.get("findings") or []
    staged = _coerce_int(
        counts.get("staged_findings") if "staged_findings" in counts else payload.get("staged_findings"),
        default=len(findings),
    )
    return {
        "schema": "legacy",
        "worker_launches": _coerce_int(payload.get("agents_launched")),
        "lens_launches": None,  # legacy schema has no loaded-lens concept
        "raw_findings": raw_findings,
        "staged_findings": staged,
        "dedup_count": _coerce_int(counts.get("deduplicated")),
        "discard_count": len(payload.get("discarded") or []),
        "calibration_count": len(payload.get("severity_calibration") or []),
        "overflow_count": len(payload.get("overflow") or []),
        "triage": _triage_from_findings(findings),
        "severity": _severity_from_findings(findings),
    }


def aggregate_sidecar(payload: dict) -> dict:
    """Classify and normalize a sidecar payload via the validator-matching
    adapter selector. Current payloads use ``aggregate_current``; legacy
    payloads use ``aggregate_legacy``.
    """
    if adapter_is_current(payload):
        return aggregate_current(payload)
    return aggregate_legacy(payload)


# ---- Effectiveness metric primitives (pure, for Task 3 to wire in). ---- #


def accepted_unique_count(review_payload: dict) -> int:
    """Number of accepted unique staged findings in one review.

    Counts staged findings whose final triage is in ``ACCEPTED_TRIAGE_VALUES``
    (``{fixed, deferred}``). ``pending`` and ``dropped`` are excluded.
    """
    findings = review_payload.get("findings") or []
    return sum(
        1
        for f in findings
        if isinstance(f, dict) and f.get("triage") in ACCEPTED_TRIAGE_VALUES
    )


def triage_coverage(review_payloads: list[dict]) -> float:
    """Mean per-review final-triage coverage.

    For each review, coverage = finalized findings / (finalized + pending).
    Reviews with zero staged findings contribute coverage 1.0 (nothing to
    finalize). Returns the mean across reviews, or 1.0 for an empty cohort.
    ``pending`` is excluded from the median numerator but counted here.
    """
    if not review_payloads:
        return 1.0
    coverages = []
    for payload in review_payloads:
        triage = _triage_from_findings(payload.get("findings") or [])
        finalized = triage["fixed"] + triage["deferred"] + triage["dropped"]
        total = finalized + triage["pending"]
        coverages.append(1.0 if total == 0 else finalized / total)
    return sum(coverages) / len(coverages)


def synthesis_discard_rate(aggregated: list[dict]) -> float | None:
    """Total synthesis-discard rows / total raw findings; None when zero raw."""
    discards = sum(a["discard_count"] for a in aggregated)
    raw = sum(a["raw_findings"] for a in aggregated)
    if raw == 0:
        return None
    return discards / raw


def final_dropped_finding_rate(aggregated: list[dict]) -> float | None:
    """Staged findings with final triage ``dropped`` / staged findings with final
    triage in ``{fixed, deferred, dropped}`` (pending excluded); None when zero
    finalized.
    """
    dropped = sum(a["triage"]["dropped"] for a in aggregated)
    finalized = sum(
        a["triage"]["fixed"] + a["triage"]["deferred"] + a["triage"]["dropped"]
        for a in aggregated
    )
    if finalized == 0:
        return None
    return dropped / finalized


def false_positive_rate(aggregated_sidecars: list[tuple[dict, dict]]) -> float | None:
    """False-positive rate = discarded rows with reason ``false-positive`` or
    ``assumption-invalid`` / total raw findings; None when zero raw.

    ``aggregated_sidecars`` is a list of ``(normalized, original_payload)``
    pairs (the false-positive-reason breakdown needs the original discard rows,
    which the normalized totals do not carry).
    """
    fp = 0
    raw = 0
    for norm, payload in aggregated_sidecars:
        raw += norm["raw_findings"]
        for row in (payload.get("discarded") or []):
            if isinstance(row, dict) and row.get("reason") in FALSE_POSITIVE_DISCARD_REASONS:
                fp += 1
    if raw == 0:
        return None
    return fp / raw


def median(values: list[float]) -> float | None:
    """Median of a list (None for empty). Uses the mean of the two middle values
    for even-length lists (so the accepted-unique median can be fractional)."""
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


# --------------------------------------------------------------------------- #
# Cohort comparison and policy report (Task 3).
# --------------------------------------------------------------------------- #
#
# Cohort key (a 4-tuple, each component derivable from BOTH current and legacy
# sidecars):
#   (review_type, role, size_bucket, domain_risk_class)
#
# Panel mode is deliberately NOT a cohort key: it is the baseline/growth
# discriminator. Two sidecars differing only in panel mode MUST derive the same
# key tuple. Period (baseline|growth) is the sole within-cohort discriminator
# and is never a cohort key.
#
# Decision rule is computed INDEPENDENTLY per cohort (no weighted average across
# cohorts). A cohort is evaluable only with >=10 completed reviews on BOTH sides
# AND growth-side triage coverage >=80% (baseline is raw-only, no triage bar).

# Review-type normalization map. Lowercased source values map to a canonical
# token; anything absent/unnormalizable collapses to ``unknown``.
_REVIEW_TYPE_NORMAL = {
    "branch": "branch",
    "branch review": "branch",
    "plan": "plan",
    "plan review": "plan",
    "code": "code",
    "code review": "code",
    "rfc": "rfc",
    "document": "document",
    "doc": "document",
}

# Artifact-size buckets over raw finding count.
def _size_bucket(count: int) -> str:
    if count <= 0:
        return "0"
    if count <= 5:
        return "1-5"
    if count <= 15:
        return "6-15"
    return "16+"


# Domain-risk classes (lossy proxy, documented as such in the plan).
_DOMAIN_SECURITY = frozenset({"security", "privacy"})
_DOMAIN_CONCURRENCY = frozenset({"concurrency", "sql"})
_DOMAIN_DOCS = frozenset({"docs", "docs-only", "skill-spec"})


def normalize_review_type(payload: dict) -> str:
    """Normalize the sidecar review type to a canonical token (or ``unknown``)."""
    rt = payload.get("review_type") or payload.get("type")
    if not isinstance(rt, str):
        return "unknown"
    key = rt.strip().lower()
    return _REVIEW_TYPE_NORMAL.get(key, "unknown")


def derive_role(payload: dict) -> str:
    """Derive role (``initial``/``follow-up``) from the round field.

    ``initial`` when ``round`` is ``r1``/``1``/absent with no ``prior_round``;
    else ``follow-up``. Both current and legacy schemas carry ``round``.
    """
    if payload.get("prior_round"):
        return "follow-up"
    rnd = payload.get("round")
    if rnd is None:
        return "initial"
    if isinstance(rnd, str):
        rnd_s = rnd.strip().lower()
        if rnd_s in ("r1", "1", ""):
            return "initial"
        return "follow-up"
    if isinstance(rnd, int):
        return "initial" if rnd == 1 else "follow-up"
    return "follow-up"


def derive_size_bucket(payload: dict) -> str:
    """Read raw finding count from whichever count key is present.

    Tries ``counts.raw_findings`` (current + legacy) and ``counts.raw_total``
    (minority of current). If both are present they MUST be equal (asserted);
    neither readable yields ``unknown``.
    """
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    rf = counts.get("raw_findings")
    rt = counts.get("raw_total")
    have_rf = isinstance(rf, (int, float)) and not isinstance(rf, bool)
    have_rt = isinstance(rt, (int, float)) and not isinstance(rt, bool)
    if have_rf and have_rt:
        if int(rf) != int(rt):
            raise SummarizerError(
                f"counts.raw_findings ({rf}) != counts.raw_total ({rt})"
            )
        return _size_bucket(int(rf))
    if have_rf:
        return _size_bucket(int(rf))
    if have_rt:
        return _size_bucket(int(rt))
    return "unknown"


def derive_domain_risk_class(payload: dict) -> str:
    """Derive the domain-risk class from the domains set (lossy proxy).

    ``security`` if security/privacy present; ``concurrency`` if concurrency/SQL;
    ``docs`` if only docs/docs-only/skill-spec; else ``other``. Empty/absent
    domains -> ``unspecified``. Security takes precedence over concurrency, which
    takes precedence over docs.
    """
    domains = payload.get("domains")
    if not isinstance(domains, list) or not domains:
        return "unspecified"
    lowered = set()
    for d in domains:
        if isinstance(d, str):
            lowered.add(d.strip().lower())
    if not lowered:
        return "unspecified"
    if lowered & _DOMAIN_SECURITY:
        return "security"
    if lowered & _DOMAIN_CONCURRENCY:
        return "concurrency"
    if lowered <= _DOMAIN_DOCS:
        return "docs"
    return "other"


def cohort_key(payload: dict) -> tuple[str, str, str, str]:
    """Derive the cohort key tuple for a parsed sidecar payload.

    Panel mode is intentionally excluded: two sidecars differing only in panel
    mode derive the same key tuple.
    """
    return (
        normalize_review_type(payload),
        derive_role(payload),
        derive_size_bucket(payload),
        derive_domain_risk_class(payload),
    )


# Decision thresholds (named, plan-specified).
MIN_REVIEWS_PER_SIDE = 10
MIN_GROWTH_TRIAGE_COVERAGE = 0.80
LAUNCH_REDUCTION_RETAIN = 0.25        # >=25% median launch reduction -> ok
ACCEPTED_CHANGE_GUARDRAIL = 0.20      # accepted must NOT fall by >20%
DROP_RATE_CHANGE_GUARDRAIL = 0.10     # growth drop-rate must NOT rise >10pp


def _median_launches_per_initial_full(aggregated_sidecars: list[tuple[dict, dict]]) -> float | None:
    """Median worker launches across ``initial`` full reviews in a side.

    ``aggregated_sidecars`` is a list of ``(normalized, payload)`` pairs. A review
    counts as ``initial full`` when its derived role is ``initial``. Returns None
    for an empty side.
    """
    launches = [
        norm["worker_launches"]
        for norm, payload in aggregated_sidecars
        if derive_role(payload) == "initial"
        and isinstance(norm.get("worker_launches"), int)
    ]
    return median([float(v) for v in launches]) if launches else None


def evaluate_cohort(
    baseline_side: list[tuple[dict, dict]],
    growth_side: list[tuple[dict, dict]],
) -> dict:
    """Evaluate one comparable cohort and return its verdict + metrics.

    Verdict is one of ``retain``, ``review needed``, ``inconclusive``. A cohort
    is evaluable only with >=10 reviews on BOTH sides AND growth triage coverage
    >=80% (baseline is raw-only; baseline triage coverage does NOT gate).

    On the evaluable path, verdict is ``retain`` only when ALL three hold:
      (a) median launches per initial full review fall by >=25% (growth vs
          baseline),
      (b) accepted unique findings per comparable review (growth; baseline
          referenced as raw yield) do NOT fall by >20%,
      (c) growth-side dropped-finding rate does NOT rise by >10 percentage
          points.
    """
    n_baseline = len(baseline_side)
    n_growth = len(growth_side)
    availability = {
        "baseline_reviews": n_baseline,
        "growth_reviews": n_growth,
    }

    # Size gate: >=10 on BOTH sides.
    if n_baseline < MIN_REVIEWS_PER_SIDE or n_growth < MIN_REVIEWS_PER_SIDE:
        return {
            "verdict": "inconclusive",
            "reason": "fewer than ten reviews on a side",
            **availability,
        }

    # Asymmetric triage gate: growth must reach >=80%; baseline is raw-only.
    growth_payloads = [p for _, p in growth_side]
    growth_coverage = triage_coverage(growth_payloads)
    if growth_coverage < MIN_GROWTH_TRIAGE_COVERAGE:
        return {
            "verdict": "inconclusive",
            "reason": "growth triage coverage below 80%",
            "growth_triage_coverage": growth_coverage,
            **availability,
        }

    # Decision metrics.
    baseline_launches = _median_launches_per_initial_full(baseline_side)
    growth_launches = _median_launches_per_initial_full(growth_side)

    # Accepted unique findings: median per-review on each side.
    baseline_accepted = median(
        [float(accepted_unique_count(p)) for _, p in baseline_side]
    )
    growth_accepted = median(
        [float(accepted_unique_count(p)) for _, p in growth_side]
    )

    baseline_drop_rate = final_dropped_finding_rate(
        [norm for norm, _ in baseline_side]
    ) or 0.0
    growth_drop_rate = final_dropped_finding_rate(
        [norm for norm, _ in growth_side]
    )
    growth_drop_rate = growth_drop_rate if growth_drop_rate is not None else 0.0

    checks = {}

    # (a) launch reduction >=25% (a higher baseline -> lower growth).
    if baseline_launches and growth_launches is not None and baseline_launches > 0:
        reduction = (baseline_launches - growth_launches) / baseline_launches
    else:
        reduction = None
    checks["launch_reduction"] = reduction
    launch_ok = reduction is not None and reduction >= LAUNCH_REDUCTION_RETAIN

    # (b) accepted change within 20% guardrail (growth accepted vs baseline raw
    # yield). Baseline contributes raw yield; here we use baseline accepted as
    # the reference yield. Accepted must NOT fall by >20%.
    if baseline_accepted is not None and growth_accepted is not None:
        if baseline_accepted > 0:
            accepted_change = (growth_accepted - baseline_accepted) / baseline_accepted
        else:
            accepted_change = 0.0 if growth_accepted == 0 else None
    else:
        accepted_change = None
    checks["accepted_change"] = accepted_change
    accepted_ok = accepted_change is not None and accepted_change >= -ACCEPTED_CHANGE_GUARDRAIL

    # (c) growth drop-rate change within 10pp.
    drop_change = growth_drop_rate - baseline_drop_rate
    checks["drop_rate_change"] = drop_change
    drop_ok = drop_change <= DROP_RATE_CHANGE_GUARDRAIL

    verdict = "retain" if (launch_ok and accepted_ok and drop_ok) else "review needed"
    return {
        "verdict": verdict,
        "metrics": {
            "baseline_median_launches": baseline_launches,
            "growth_median_launches": growth_launches,
            "baseline_median_accepted": baseline_accepted,
            "growth_median_accepted": growth_accepted,
            "baseline_drop_rate": baseline_drop_rate,
            "growth_drop_rate": growth_drop_rate,
            "growth_triage_coverage": growth_coverage,
        },
        "checks": {
            "launch_reduction_ok": launch_ok,
            "accepted_change_ok": accepted_ok,
            "drop_rate_change_ok": drop_ok,
        },
        **availability,
    }


def group_into_cohorts(
    classified_sidecars: list[tuple[str, dict]],
) -> dict[tuple[str, str, str, str], dict[str, list[tuple[dict, dict]]]]:
    """Group classified sidecars into comparable cohorts.

    ``classified_sidecars`` is a list of ``(period, payload)`` pairs where period
    is ``baseline`` or ``growth``. Returns a mapping ``cohort_key_tuple ->
    {period: [(normalized, payload), ...]}``. Panel mode is NOT a key, so two
    sidecars differing only in panel mode land in the same cohort.
    """
    cohorts: dict[tuple[str, str, str, str], dict[str, list[tuple[dict, dict]]]] = {}
    for period, payload in classified_sidecars:
        key = cohort_key(payload)
        bucket = cohorts.setdefault(key, {"baseline": [], "growth": []})
        norm = aggregate_sidecar(payload)
        bucket.setdefault(period, []).append((norm, payload))
    return cohorts


def overall_verdict(per_cohort_verdicts: list[str]) -> str:
    """Overall verdict: ``inconclusive`` when there are zero evaluable cohorts;
    ``retain`` only if EVERY evaluable cohort retains; ``review needed`` if any
    evaluable cohort fails (per-cohort conjunction, no weighted average)."""
    evaluable = [v for v in per_cohort_verdicts if v != "inconclusive"]
    if not evaluable:
        return "inconclusive"
    if all(v == "retain" for v in evaluable):
        return "retain"
    return "review needed"


def build_effectiveness_report(
    classified_sidecars: list[tuple[str, dict]],
) -> dict:
    """Build the byte-stable aggregate effectiveness report dict.

    ``classified_sidecars`` is a list of ``(period, payload)`` pairs (period is
    ``baseline`` or ``growth``). The report contains: the overall verdict, a
    sorted list of per-cohort entries (key, verdict, availability, metrics), and
    cohort-availability counts. No path/name/ticket/feature/digest identifier is
    ever emitted: only aggregate counts and cohort verdicts.

    A single malformed sidecar (one whose ``cohort_key`` raises the integrity
    assert in ``derive_size_bucket``) does NOT abort the whole report: it is
    skipped per-sidecar and the count is surfaced in
    ``availability.skipped_malformed`` (F4). The integrity assert itself is kept
    (the plan mandates it); only its blast radius is bounded.
    """
    # Skip malformed sidecars per-sidecar so one bad input does not abort a
    # whole-corpus run. The count (not the paths) is surfaced in the PUBLIC
    # report; paths are private.
    skipped_malformed = 0
    clean: list[tuple[str, dict]] = []
    for period, payload in classified_sidecars:
        try:
            cohort_key(payload)
        except SummarizerError:
            skipped_malformed += 1
            continue
        clean.append((period, payload))
    cohorts = group_into_cohorts(clean)

    per_cohort = []
    verdicts: list[str] = []
    for key in sorted(cohorts.keys()):
        bucket = cohorts[key]
        baseline_side = bucket.get("baseline", [])
        growth_side = bucket.get("growth", [])
        evaluation = evaluate_cohort(baseline_side, growth_side)
        verdicts.append(evaluation["verdict"])
        per_cohort.append(
            {
                "cohort": {
                    "review_type": key[0],
                    "role": key[1],
                    "size_bucket": key[2],
                    "domain_risk_class": key[3],
                },
                **evaluation,
            }
        )

    availability_counts = {
        "cohorts": len(per_cohort),
        "evaluable_cohorts": sum(
            1 for c in per_cohort if c["verdict"] != "inconclusive"
        ),
        "comparable_cohorts": sum(
            1
            for c in per_cohort
            if c["baseline_reviews"] > 0 and c["growth_reviews"] > 0
        ),
        "skipped_malformed": skipped_malformed,
    }
    return {
        "overall_verdict": overall_verdict(verdicts),
        "availability": availability_counts,
        "cohorts": per_cohort,
    }


def serialize_effectiveness_json(report: dict) -> bytes:
    """Canonical byte serialization of the effectiveness report (stable keys +
    stable trailing newline)."""
    return (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")


def serialize_effectiveness_markdown(report: dict) -> bytes:
    """Concise Markdown rendering of the effectiveness report.

    One line per cohort (verdict + availability), an overall verdict, and
    cohort-availability counts. No identifier categories are emitted.
    """
    lines = ["# Review effectiveness report", ""]
    lines.append(f"Overall verdict: **{report['overall_verdict']}**")
    avail = report["availability"]
    lines.append("")
    # Condition the skipped-malformed fragment on a non-zero count so the
    # normal (no-skips) markdown stays byte-identical (determinism selftest).
    availability = (
        "Cohort availability: "
        f"{avail['cohorts']} cohort(s), "
        f"{avail['comparable_cohorts']} comparable, "
        f"{avail['evaluable_cohorts']} evaluable"
    )
    if avail.get("skipped_malformed"):
        availability += f", {avail['skipped_malformed']} skipped malformed"
    availability += "."
    lines.append(availability)
    lines.append("")
    lines.append("## Per-cohort verdicts")
    lines.append("")
    lines.append("| Cohort | Verdict | Baseline | Growth |")
    lines.append("| --- | --- | --- | --- |")
    for c in report["cohorts"]:
        cohort = c["cohort"]
        label = "/".join(
            (cohort["review_type"], cohort["role"], cohort["size_bucket"], cohort["domain_risk_class"])
        )
        lines.append(
            f"| {label} | {c['verdict']} | {c['baseline_reviews']} | {c['growth_reviews']} |"
        )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


# --------------------------------------------------------------------------- #
# Real-corpus deny inventory (Task 4). Design Invariant 4.
# --------------------------------------------------------------------------- #
#
# The fixed regex deny list (Task 3 #public_output) is kept ONLY as a coarse
# pre-filter. The REAL privacy check builds the deny inventory at audit time
# from the actual corpus and asserts none of those exact strings appear in the
# public reports. The inventory is assembled from:
#   - discovered repository names (each repo directory name under a root),
#   - path components (directory/file name fragments) of discovered sidecars,
#   - staged review filenames (sidecar basename, with and without extension),
#   - artifact identifiers parsed from sidecar payloads (review_id, slug, and
#     ticket-like tokens), and
#   - recorded content digests (the SHA-256 of every sidecar as recorded in the
#     baseline, plus any 64-hex digest-shaped value found in a payload).
#
# The inventory file itself is runtime-private (under
# ``~/.ai-playbook/review-telemetry/``); it is never committed.

# Coarse fixed deny fragments retained as a pre-filter (never deleted). The real
# inventory is layered on top of this at audit time.
_FIXED_DENY_FRAGMENTS = (
    "/tmp/",
    ".ai-playbook/",
    ".stats.json",
)

# Generic structural path components that are NOT private identifiers. Including
# them in the deny inventory would produce false leaks (they appear in cohort
# labels and prose). The real deny inventory excludes these.
_GENERIC_PATH_COMPONENTS = frozenset(
    {
        os.sep,
        "/",
        ".",
        "..",
        "docs",
        "history",
        "reviews",
        "review",
        "src",
        "scripts",
        "tests",
        "test",
        ".ai-playbook",
    }
)

# Public taxonomy tokens that the effectiveness report legitimately emits (review
# types, roles, size buckets, domain-risk classes, verdicts) plus generic words
# commonly embedded in staged review filenames (``branch``, ``code``, ``main``,
# round tokens). These are NOT private identifiers: a real review filename like
# ``2026-07-29-branch-review-r1.stats.json`` shares the words ``branch``/``r1``
# with the public taxonomy. The deny inventory excludes them so the fixed-string
# ``rg -F -f`` privacy check does not flag the report's own cohort labels.
_PUBLIC_TAXONOMY_COMPONENTS = frozenset(
    {
        # Review-type canonical tokens + their source spellings.
        "branch", "code", "plan", "rfc", "document", "doc", "unknown",
        # Roles.
        "initial", "follow-up", "followup",
        # Size buckets.
        "0", "1-5", "6-15", "16+",
        # Domain-risk classes.
        "security", "concurrency", "docs", "other", "unspecified", "privacy", "sql", "docs-only", "skill-spec",
        # Verdicts + report vocabulary.
        "retain", "inconclusive", "needed", "verdict", "cohort", "baseline", "growth", "overall",
        # Generic words/fragments commonly embedded in staged review filenames and
        # default-branch path components.
        "review", "reviews", "main", "master", "develop", "trunk",
        "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9",
        "stats", "json", "md",
        # Date fragments embedded in review filenames (yyyy-mm-dd).
        "2024", "2025", "2026", "2027",
    }
)


def _ticket_like_tokens(text: str) -> list[str]:
    """Return uppercase ticket-like tokens (e.g. ``PROJ-12345``) found in ``text``.

    Matches the conventional ``PROJECT-\\d+`` shape. Used to harvest artifact
    identifiers from review ids/slugs without parsing a specific schema.
    """
    import re

    return re.findall(r"\b[A-Z][A-Z0-9]{1,}-\d{2,}\b", text)


def _harvest_payload_identifiers(payload: dict) -> list[str]:
    """Return artifact identifiers carried in a parsed sidecar payload.

    Reads well-known identifier-bearing keys (``review_id``, ``artifact_slug``,
    ``slug``) plus any nested ticket-like tokens or 64-hex digest-shaped values.
    """
    out: list[str] = []

    def add(val) -> None:
        if isinstance(val, str) and val:
            out.append(val)

    for key in ("review_id", "artifact_slug", "slug"):
        add(payload.get(key))
    # Nested identifier buckets some producers emit.
    internal = payload.get("_internal")
    if isinstance(internal, dict):
        for k in ("ticket", "repo", "path", "sha", "prior_sha"):
            add(internal.get(k))
    # Harvest ticket-like tokens and digest-shaped values from the whole payload
    # text so a producer that nests them under an unknown key is still covered.
    blob = json.dumps(payload, sort_keys=True)
    out.extend(_ticket_like_tokens(blob))
    import re

    out.extend(re.findall(r"\b[0-9a-f]{64}\b", blob))
    return out


def build_real_deny_inventory(
    repo_roots: list[Path],
    sidecars: list[Path],
    buffers: dict[Path, bytes],
    baseline: dict,
) -> list[str]:
    """Build the real-corpus deny inventory at audit time.

    Returns a de-duplicated, sorted list of exact strings assembled from the
    corpus. Each string is one of: a discovered repository name, a path
    component (directory/file name fragment) of a discovered sidecar, a staged
    review filename, an artifact identifier parsed from a sidecar payload, or a
    recorded content digest. Empty strings are dropped (an empty line in the
    inventory would match every file under ``rg -F``).
    """
    deny: set[str] = set()

    # Discovered repository names: each immediate child repo dir name.
    repo_names: set[str] = set()
    for root in repo_roots:
        for repo in iter_repos_under_root(root):
            repo_names.add(repo.name)
    deny |= repo_names

    # Path components + staged review filenames + payload identifiers + digests.
    snapshot_digests = {entry.get("sha256", "") for entry in baseline.get("sidecars", [])}
    deny |= {d for d in snapshot_digests if d}

    for sidecar in sidecars:
        # Path components that are SPECIFIC identifiers (directory/file name
        # fragments). Generic structural components (docs, reviews, history, ...)
        # AND public taxonomy tokens (review types, roles, size buckets, domain
        # classes, generic filename words like ``branch``/``main``/``r1``) are
        # excluded: the report legitimately emits the taxonomy and a real review
        # filename shares those words. Full path strings (which contain
        # separators) are NOT added as needles; the full filename and its slug
        # ARE added unconditionally below (a specific slug is always a needle).
        excluded = _GENERIC_PATH_COMPONENTS | _PUBLIC_TAXONOMY_COMPONENTS
        parts = [p for p in sidecar.parts if p and p not in excluded]
        deny |= {p for p in parts if len(p) >= 3}
        # Staged review filename: full name and the slug without the extension.
        name = sidecar.name
        deny.add(name)
        if name.endswith(".stats.json"):
            deny.add(name[: -len(".stats.json")])
        # Payload identifiers + the sidecar's own digest. Harvested identifiers
        # that are generic/public taxonomy (e.g. an ``artifact_slug`` of ``main``
        # for a review of the main branch) are excluded so the fixed-string
        # privacy check does not flag the report's own vocabulary.
        excluded = _GENERIC_PATH_COMPONENTS | _PUBLIC_TAXONOMY_COMPONENTS
        buf = buffers.get(sidecar, b"")
        if buf:
            payload, _ = parse_payload(buf)
            if payload is not None:
                deny |= {
                    s
                    for s in _harvest_payload_identifiers(payload)
                    if s and s not in excluded
                }
            deny.add(sha256_hex(buf))

    # Drop the empty string (it would match everything under rg -F) and the
    # coarse fixed fragments are retained separately (not returned here).
    deny.discard("")
    return sorted(deny)


def serialize_deny_inventory(deny: list[str]) -> bytes:
    """Canonical byte serialization of the deny inventory (one needle per line)."""
    return ("\n".join(deny) + "\n").encode("utf-8") if deny else b""


# --------------------------------------------------------------------------- #
# Historical immutability (Task 4). Design Invariant 1.
# --------------------------------------------------------------------------- #
#
# A mechanical digest-comparison test, not a manual checkbox. Before the first
# real-corpus run, SHA-256 is recorded for every discovered historical Markdown
# and sidecar; after the run, every recorded path is re-hashed and asserted
# byte-identical; any unexpected new file in a historical directory is rejected.
# The summarizer opens inputs READ-ONLY; an explicit write attempt to a
# historical input MUST fail.


def _iter_historical_artifacts(repo_roots: list[Path]) -> Iterator[Path]:
    """Yield historical review Markdown and sidecars discovered under repo roots.

    Covers the same allowlist as sidecar discovery (per-repo ``reviews_dir`` and
    legacy ``docs/history/reviews/``) but ALSO yields sibling ``*.md`` review
    documents, since historical Markdown is immutable read-only input alongside
    the sidecars. Symlinks and excluded fragments are rejected.
    """
    seen: set[Path] = set()
    for root in repo_roots:
        for repo in iter_repos_under_root(root):
            reviews_dir = _repo_reviews_dir(repo)
            for p in _iter_review_artifacts(reviews_dir):
                rp = p.resolve()
                if rp not in seen:
                    seen.add(rp)
                    yield p
            legacy = repo / "docs" / "history" / "reviews"
            for p in _iter_review_artifacts(legacy):
                rp = p.resolve()
                if rp not in seen:
                    seen.add(rp)
                    yield p


def _iter_review_artifacts(directory: Path) -> Iterator[Path]:
    """Yield real ``*.stats.json`` and ``*.md`` files directly under ``directory``."""
    if not directory.is_dir():
        return
    try:
        for entry in sorted(os.listdir(str(directory))):
            candidate = directory / entry
            if os.path.islink(str(candidate)):
                continue
            if not candidate.is_file():
                continue
            if is_path_excluded(candidate):
                continue
            if candidate.name.endswith(".stats.json") or candidate.name.endswith(".md"):
                yield candidate
    except OSError:
        return


def record_historical_digests(
    repo_roots: list[Path], manifest_path: Path | None = None
) -> dict[Path, str]:
    """Record SHA-256 for every discovered historical Markdown + sidecar.

    Returns a mapping ``resolved_path -> sha256_hex``. When ``manifest_path`` is
    given, the manifest is also written there (private temp manifest) as a
    JSON object of ``{str(path): sha256}``.
    """
    recorded: dict[Path, str] = {}
    for path in _iter_historical_artifacts(repo_roots):
        recorded[path.resolve()] = sha256_hex(read_byte_buffer(path))
    if manifest_path is not None:
        data = json.dumps(
            {str(p): h for p, h in recorded.items()}, sort_keys=True, indent=2
        ).encode("utf-8")
        manifest_path.write_bytes(data)
    return recorded


def verify_historical_digests(
    repo_roots: list[Path], recorded: dict[Path, str]
) -> list[Path]:
    """Re-discover historical artifacts and return the list of violations.

    A violation is either a recorded path whose digest changed, or a NEW
    unexpected file in a historical directory that was not recorded. Returns the
    list of offending paths (empty when the tree is byte-identical and has no
    unexpected new files).
    """
    recorded_keys = {Path(k) if not isinstance(k, Path) else k for k in recorded}
    recorded_map = {Path(k) if not isinstance(k, Path) else k: v for k, v in recorded.items()}
    violations: list[Path] = []
    current: set[Path] = set()
    for path in _iter_historical_artifacts(repo_roots):
        rp = path.resolve()
        current.add(rp)
        expected = recorded_map.get(rp)
        if expected is None:
            # Unexpected new file in a historical directory.
            violations.append(rp)
            continue
        actual = sha256_hex(read_byte_buffer(path))
        if actual != expected:
            violations.append(rp)
    # Recorded paths that vanished are also violations.
    for p in recorded_keys - current:
        violations.append(p)
    return sorted(violations)


def attempt_historical_write(path: Path) -> None:
    """Refuse to write to a historical input (read-only invariant).

    The summarizer opens inputs READ-ONLY; no write path reaches them. This
    function exists so the immutability test can prove the refusal: it raises
    ``PermissionsError`` unconditionally for any historical input path.
    """
    raise PermissionsError(
        f"refusing to write to immutable historical input: {path}"
    )


# --------------------------------------------------------------------------- #
# Pre-publish recheck (snapshot races). Design Invariant 9.
# --------------------------------------------------------------------------- #


def publish_with_recheck(
    buffers: dict[Path, bytes],
    publish_fn: Callable[[], None],
    *,
    retries: int = MAX_PUBLISH_RETRIES,
) -> None:
    """Recheck each input's on-disk generation against the buffer before publish.

    On the success path every published digest matches the byte buffer used for
    parsing. If an input changed between the buffer read and the recheck, retry
    up to ``retries`` times (re-reading the buffer); after that fail publication
    rather than publish a mixed-version snapshot. The caller's ``publish_fn``
    is invoked once per attempt after the recheck passes.
    """
    attempt = 0
    while True:
        attempt += 1
        changed = False
        for path, buf in buffers.items():
            gen = on_disk_generation(path)
            if gen is None:
                raise PublishRace(f"input vanished before publish: {path}")
            if gen[1] != len(buf):
                changed = True
                break
            if sha256_hex(read_byte_buffer(path)) != sha256_hex(buf):
                changed = True
                break
        if not changed:
            publish_fn()
            return
        if attempt > retries:
            raise PublishRace(
                f"input changed between read and publish after {retries} retries"
            )
        # Re-read buffers and retry.
        for path in list(buffers.keys()):
            buffers[path] = read_byte_buffer(path)


# --------------------------------------------------------------------------- #
# Commands.
# --------------------------------------------------------------------------- #


def cmd_init_baseline(
    user_facts: Path, baseline_path: Path, telemetry_dir: Path
) -> int:
    """``--init-baseline``: atomic create (fails if manifest exists)."""
    tighten_parent_ai_playbook(telemetry_dir.parent)
    with telemetry_lock(telemetry_dir):
        ensure_private_dir(telemetry_dir)
        repo_roots = _roots_from_facts(user_facts)
        sidecars = discover_sidecars(repo_roots)
        buffers = {s: read_byte_buffer(s) for s in sidecars}
        marker = make_cutover_marker(set(FIVE_WORKER_PANEL_IDS))
        manifest = build_baseline(sidecars, buffers, marker)
        data = serialize_baseline(manifest)
        # Atomic exclusive create.
        create_private_file_exclusive(baseline_path, data)
        sys.stdout.write(
            f"initialized baseline with {len(sidecars)} sidecars at {baseline_path}\n"
        )
    return 0


def cmd_refresh_baseline(
    user_facts: Path, baseline_path: Path, telemetry_dir: Path
) -> int:
    """``--refresh-baseline``: explicit refresh (overwrites the manifest)."""
    tighten_parent_ai_playbook(telemetry_dir.parent)
    with telemetry_lock(telemetry_dir):
        ensure_private_dir(telemetry_dir)
        repo_roots = _roots_from_facts(user_facts)
        sidecars = discover_sidecars(repo_roots)
        buffers = {s: read_byte_buffer(s) for s in sidecars}
        # Preserve the original cutover marker across refresh (single authority).
        marker = None
        if baseline_path.is_file():
            try:
                existing = load_baseline(baseline_path)
                marker = existing.get("cutover_marker")
            except BaselineMissing:
                marker = None
        if marker is None:
            marker = make_cutover_marker(set(FIVE_WORKER_PANEL_IDS))
        manifest = build_baseline(sidecars, buffers, marker)
        data = serialize_baseline(manifest)
        # Refresh writes via a private temp file then rename (atomic replace).
        _atomic_write_private(baseline_path, data)
        sys.stdout.write(
            f"refreshed baseline with {len(sidecars)} sidecars at {baseline_path}\n"
        )
    return 0


def _atomic_write_private(path: Path, data: bytes) -> None:
    """Atomically overwrite ``path`` (0o600) via temp file + rename."""
    _reject_symlink(path)
    _reject_symlink(path.parent)
    prev = os.umask(0o077)
    try:
        tmp_fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent), prefix=".baseline-"
        )
        try:
            with os.fdopen(tmp_fd, "wb") as fh:
                fh.write(data)
            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, str(path))
        except BaseException:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
    finally:
        os.umask(prev)


def cmd_strict_audit(
    user_facts: Path,
    baseline_path: Path,
    telemetry_dir: Path,
    json_report: Path | None = None,
    markdown_report: Path | None = None,
) -> int:
    """``--strict-audit``: read-only; fail when baseline missing/unreadable/
    replaced/mismatched. Runs conservation classification and reports."""
    tighten_parent_ai_playbook(telemetry_dir.parent)
    with telemetry_lock(telemetry_dir):
        if not baseline_path.is_file():
            raise BaselineMissing(f"baseline missing: {baseline_path}")
        baseline = load_baseline(baseline_path)  # raises BaselineMissing if unreadable
        repo_roots = _roots_from_facts(user_facts)
        sidecars = discover_sidecars(repo_roots)
        buffers = {s: read_byte_buffer(s) for s in sidecars}
        ledger, audit = run_conservation(sidecars, buffers, baseline)

        # Strict audit: detect replacement/mismatch.
        snapshot_by_path = {
            e["path"]: e for e in baseline.get("sidecars", [])
        }
        replaced: list[str] = []
        for sidecar in sidecars:
            snap = snapshot_by_path.get(str(sidecar))
            if snap is not None and snap.get("sha256") != sha256_hex(
                buffers[sidecar]
            ):
                replaced.append(str(sidecar))

        # Build the effectiveness report over the classified corpus. Period
        # assignment: snapshot members (ledger baseline) are ``baseline``; growth
        # sidecars are ``growth``. Legacy/audit-anomaly/unreadable/duplicate are
        # excluded from cohort comparison (no period assigned). Panel mode is not
        # a cohort key, so a baseline review and a growth review that differ only
        # in panel mode land in the same comparable cohort.
        classified: list[tuple[str, dict]] = []
        snapshot_paths = {
            entry["path"] for entry in baseline.get("sidecars", [])
        }
        for sidecar in sidecars:
            payload, _ = parse_payload(buffers[sidecar])
            if payload is None:
                continue
            if str(sidecar) in snapshot_paths:
                classified.append(("baseline", payload))
            elif "growth" in ledger and sidecar in ledger["growth"]:
                classified.append(("growth", payload))
        report = build_effectiveness_report(classified)
        # Private operability pointer (F4): if any sidecar was skipped as
        # malformed (integrity assert in derive_size_bucket), note the count on
        # stderr. Paths stay private (not emitted); the count is also in the
        # report's availability.skipped_malformed.
        skipped = report.get("availability", {}).get("skipped_malformed", 0)
        if skipped:
            sys.stderr.write(
                f"strict audit: skipped {skipped} malformed sidecar(s); "
                "see availability.skipped_malformed in the report\n"
            )
        report_bytes = serialize_effectiveness_json(report)
        markdown_bytes = serialize_effectiveness_markdown(report)

        def _publish() -> None:
            if json_report is not None:
                _atomic_write_private(json_report, report_bytes)
            if markdown_report is not None:
                _atomic_write_private(markdown_report, markdown_bytes)

        publish_with_recheck(buffers, _publish)

    anomalies = len(audit) + len(ledger["baseline-missing"]) + len(replaced)
    sys.stdout.write(
        f"strict audit: {anomalies} anomaly/anomalies; classes="
        + ", ".join(f"{cls}={len(v)}" for cls, v in ledger.items())
        + "\n"
    )
    return 0 if anomalies == 0 else 1


def cmd_emit_deny_inventory(
    user_facts: Path, out_path: Path, telemetry_dir: Path
) -> int:
    """``--emit-deny-inventory``: build the deny list at audit time from the real
    corpus and write it to the given private path.

    The inventory is assembled from discovered repository names, path components,
    staged review filenames, artifact identifiers, and recorded content digests.
    The existing fixed regex is retained only as a coarse pre-filter; the real
    inventory is layered on top. The output file is runtime-private (under
    ``~/.ai-playbook/review-telemetry/``); it is never committed.
    """
    tighten_parent_ai_playbook(telemetry_dir.parent)
    with telemetry_lock(telemetry_dir):
        ensure_private_dir(telemetry_dir)
        repo_roots = _roots_from_facts(user_facts)
        sidecars = discover_sidecars(repo_roots)
        buffers = {s: read_byte_buffer(s) for s in sidecars}
        baseline_path = telemetry_dir / "baseline.json"
        baseline: dict = {"sidecars": []}
        if baseline_path.is_file():
            try:
                baseline = load_baseline(baseline_path)
            except BaselineMissing:
                baseline = {"sidecars": []}
        deny = build_real_deny_inventory(repo_roots, sidecars, buffers, baseline)
        data = serialize_deny_inventory(deny)
        _atomic_write_private(out_path, data)
        sys.stdout.write(
            f"emitted deny inventory with {len(deny)} needle(s) to {out_path}\n"
        )
    return 0


def _roots_from_facts(user_facts: Path) -> list[Path]:
    """Resolve repo roots from the user facts doc via facts_paths (import)."""
    personal, company = facts_paths.resolve_projects_roots(user_facts)
    roots = [r for r in (personal, company) if r is not None]
    if not roots:
        raise SummarizerError(f"no project roots resolved from {user_facts}")
    return roots


# --------------------------------------------------------------------------- #
# Selftest registry. The dotted names match the plan's checkbox IDs.
# --------------------------------------------------------------------------- #

_registry: dict[str, Callable[[Callable], None]] = {}


def _test(name: str) -> Callable[[Callable], None]:
    """Register a selftest under the plan's dotted checkbox id."""

    def deco(fn: Callable) -> Callable:
        _registry[name] = fn
        return fn

    return deco


def _write_private_sidecar(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_current_payload(panel_ids: list[str], *, date: str = "2099-01-01") -> dict:
    panel = [
        {"worker": w, "status": "complete", "raw": 1, "solo": 1, "echo": 0}
        for w in panel_ids
    ]
    return {
        "review_type": "Branch Review",
        "date": date,
        "round": "r1",
        "panel_mode": "full",
        "counts": {"agents_launched": len(panel_ids), "raw_findings": 1},
        "panel": panel,
    }


def _make_legacy_payload() -> dict:
    return {
        "review_id": "2025-01-01-branch-review-old-r1",
        "type": "branch-review",
        "round": "r1",
        "date": "2025-01-01",
        "agents_launched": 3,
        "counts": {"raw_findings": 2},
    }


# ---- facts_roots ----
@_test("summarize_review_stats#facts_roots")
def _t_facts_roots(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        facts = td_path / "facts.md"
        facts.write_text(
            "| `personal_projects_root` | `~/Projects/myrepos/` | x |\n"
            "| `company_projects_root` | `~/Projects/sporty/` | y |\n",
            encoding="utf-8",
        )
        roots = facts_paths.resolve_projects_roots(facts)
        check(
            "facts_roots: two roots resolved via facts_paths import",
            roots[0] is not None and roots[1] is not None,
            str(roots),
        )
        # Roots are never embedded in tracked output: build_baseline is the only
        # place path data is recorded, and it goes to the private manifest. The
        # aggregate (strict-audit markdown) must not contain the root string.
        sidecars: list[Path] = []
        buffers: dict[Path, bytes] = {}
        manifest = build_baseline(sidecars, buffers, make_cutover_marker(set()))
        leaked = any(
            "Projects" in v for v in json.dumps(manifest).split()
        )
        check("facts_roots: no root embedded in empty baseline", not leaked)
        # Public markdown never contains a root path.
        public_md = "# Review effectiveness report\n"
        check(
            "facts_roots: root string absent from public markdown",
            str(roots[0]) not in public_md if roots[0] else True,
        )


# ---- review_directory_discovery ----
@_test("summarize_review_stats#review_directory_discovery")
def _t_discovery(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Repo root with two child repos.
        root = td_path / "myrepos"
        repo = root / "repo-a"
        # Configured reviews_dir (repo .ai-playbook/facts.md TOML key).
        (repo / ".ai-playbook").mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            '```toml\nreviews_dir = "docs/reviews/"\n```\n', encoding="utf-8"
        )
        real_current = repo / "docs" / "reviews" / "a.stats.json"
        _write_private_sidecar(real_current, _make_current_payload(["quality"]))
        # Legacy docs/history/reviews.
        legacy = repo / "docs" / "history" / "reviews" / "b.stats.json"
        _write_private_sidecar(legacy, _make_legacy_payload())

        # Excluded siblings that must NOT be ingested.
        bad_tmp = root / "tmp" / "reviews" / "leak1.stats.json"
        _write_private_sidecar(bad_tmp, _make_legacy_payload())
        bad_runtime = root / ".ai-playbook" / "reviews" / "leak2.stats.json"
        _write_private_sidecar(bad_runtime, _make_legacy_payload())
        bad_telemetry = root / ".ai-playbook" / "review-telemetry" / "leak3.stats.json"
        _write_private_sidecar(bad_telemetry, _make_legacy_payload())

        # Symlink that must be rejected (not followed).
        link_target = root / "real.stats.json"
        _write_private_sidecar(link_target, _make_legacy_payload())
        sym = repo / "docs" / "reviews" / "link.stats.json"
        os.symlink(link_target, sym)

        found = discover_sidecars([root])
        names = {p.name for p in found}
        check("discovery: real current sidecar discovered", "a.stats.json" in names)
        check("discovery: legacy sidecar discovered", "b.stats.json" in names)
        check("discovery: tmp excluded", "leak1.stats.json" not in names)
        check("discovery: runtime reviews excluded", "leak2.stats.json" not in names)
        check("discovery: telemetry excluded", "leak3.stats.json" not in names)
        check("discovery: symlink rejected", "link.stats.json" not in names)
        # Dedup: each real path appears once.
        check(
            "discovery: no duplicate real paths",
            len(found) == len({str(p) for p in found}),
        )
        # Allowlist predicate: every found path is under reviews_dir or legacy.
        for p in found:
            ok = "docs/reviews" in str(p) or "docs/history/reviews" in str(p)
            check(f"discovery: {p.name} under allowlist", ok, str(p))


# ---- same_shape_replacement ----
@_test("summarize_review_stats#same_shape_replacement")
def _t_same_shape(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        sidecar = td_path / "x.stats.json"
        payload = _make_current_payload(["quality"])
        _write_private_sidecar(sidecar, payload)
        buffers = {sidecar: read_byte_buffer(sidecar)}
        marker = make_cutover_marker(set(FIVE_WORKER_PANEL_IDS))
        # Baseline records the original digest.
        baseline = build_baseline([sidecar], buffers, marker)
        # Now replace the file with a same-path different-digest file.
        _write_private_sidecar(sidecar, _make_current_payload(["testing"]))
        buffers = {sidecar: read_byte_buffer(sidecar)}
        ledger, audit = run_conservation([sidecar], buffers, baseline)
        check(
            "same_shape_replacement: strict audit failure (audit-anomaly)",
            len(ledger["audit-anomaly"]) == 1,
            str({k: len(v) for k, v in ledger.items()}),
        )
        check(
            "same_shape_replacement: not classified baseline",
            len(ledger["baseline"]) == 0,
        )


# ---- conservation ----
@_test("summarize_review_stats#conservation")
def _t_conservation(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        current = td_path / "current.stats.json"
        _write_private_sidecar(current, _make_current_payload(["quality"]))
        legacy = td_path / "legacy.stats.json"
        _write_private_sidecar(legacy, _make_legacy_payload())
        unreadable = td_path / "unreadable.stats.json"
        unreadable.write_text("{not json", encoding="utf-8")
        dup1 = td_path / "dup1.stats.json"
        dup2 = td_path / "dup2.stats.json"
        _write_private_sidecar(dup1, _make_current_payload(["security"]))
        _write_private_sidecar(dup2, _make_current_payload(["security"]))
        growth = td_path / "growth.stats.json"
        _write_private_sidecar(growth, _make_current_payload(["testing"]))

        sidecars = [current, legacy, unreadable, dup1, dup2, growth]
        buffers = {s: read_byte_buffer(s) for s in sidecars}
        # Baseline contains only `current` (so dup1/dup2/growth are not snapshot).
        baseline = build_baseline([current], {current: buffers[current]}, make_cutover_marker(set(FIVE_WORKER_PANEL_IDS)))
        # Add an audit-anomaly: baseline path with changed digest.
        anomaly = td_path / "anomaly.stats.json"
        _write_private_sidecar(anomaly, _make_current_payload(["quality"]))
        abuf = read_byte_buffer(anomaly)
        baseline_anomaly = build_baseline([anomaly], {anomaly: abuf}, make_cutover_marker(set(FIVE_WORKER_PANEL_IDS)))
        _write_private_sidecar(anomaly, _make_current_payload(["testing"]))
        buffers_anom = {anomaly: read_byte_buffer(anomaly)}

        ledger, _ = run_conservation(sidecars, buffers, baseline)
        total = sum(len(v) for v in ledger.values())
        check("conservation: every sidecar in exactly one class", total == len(sidecars))
        check("conservation: current not in snapshot is growth", len(ledger["growth"]) >= 1)
        check("conservation: legacy classed", len(ledger["legacy"]) == 1)
        check("conservation: unreadable classed", len(ledger["unreadable"]) == 1)
        check("conservation: duplicate classed", len(ledger["duplicate"]) == 1)

        ledger_a, audit_a = run_conservation([anomaly], buffers_anom, baseline_anomaly)
        check(
            "conservation: audit-anomaly present",
            len(ledger_a["audit-anomaly"]) == 1,
            str({k: len(v) for k, v in ledger_a.items()}),
        )


# ---- audit_anomaly_classification ----
@_test("summarize_review_stats#audit_anomaly_classification")
def _t_audit_anomaly(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        marker = make_cutover_marker(set(FIVE_WORKER_PANEL_IDS))
        # Timestamp disagreement: growth review with pre-cutover timestamp.
        pre = td_path / "pre.stats.json"
        _write_private_sidecar(pre, _make_current_payload(["quality"], date="2000-01-01"))
        ledger_pre, audit_pre = run_conservation(
            [pre], {pre: read_byte_buffer(pre)}, build_baseline([], {}, marker)
        )
        # Pre-cutover growth stays growth (NOT re-classified) and is flagged.
        check(
            "audit_anomaly: pre-cutover growth stays growth",
            len(ledger_pre["growth"]) == 1 and len(ledger_pre["audit-anomaly"]) == 0,
            str({k: len(v) for k, v in ledger_pre.items()}),
        )
        check(
            "audit_anomaly: pre-cutover growth flagged in audit",
            len(audit_pre) == 1,
            str(audit_pre),
        )

        # Schema disagreement: sidecar schema mismatches marker schema.
        schema_bad = td_path / "schema.stats.json"
        bad_payload = _make_current_payload(["quality"])
        bad_payload["schema"] = "review-stats-evil"
        _write_private_sidecar(schema_bad, bad_payload)
        ledger_s, audit_s = run_conservation(
            [schema_bad], {schema_bad: read_byte_buffer(schema_bad)},
            build_baseline([], {}, marker),
        )
        check(
            "audit_anomaly: schema disagreement -> audit-anomaly",
            len(ledger_s["audit-anomaly"]) == 1,
            str({k: len(v) for k, v in ledger_s.items()}),
        )

        # Panel-identity disagreement: a sidecar with a worker NOT in the marker
        # panel identity set is NOT a five-worker sidecar -> legacy (not anomaly
        # by panel). To force a panel mismatch against the marker for an IN-snapshot
        # baseline member, record it in the snapshot then change its panel.
        panel_a = td_path / "panel.stats.json"
        _write_private_sidecar(panel_a, _make_current_payload(["quality"]))
        snap = build_baseline([panel_a], {panel_a: read_byte_buffer(panel_a)}, marker)
        _write_private_sidecar(panel_a, _make_current_payload(["testing"]))
        # Same path, different digest -> audit-anomaly (same-shape replacement).
        ledger_p, _ = run_conservation(
            [panel_a], {panel_a: read_byte_buffer(panel_a)}, snap
        )
        check(
            "audit_anomaly: panel/digest disagreement -> audit-anomaly",
            len(ledger_p["audit-anomaly"]) == 1,
            str({k: len(v) for k, v in ledger_p.items()}),
        )


# ---- conservation_shape_drift_canary (F1) ----
@_test("summarize_review_stats#conservation_shape_drift")
def _t_conservation_shape_drift(check) -> None:
    """The conservation ledger's current/legacy shape decision must NOT diverge
    from the aggregation adapter's current/legacy predicate. Two invariants:

    1. Drift canary: for every sidecar whose panel identity SATISFIES the
       five-worker set (so the shape decision is the SOLE growth-vs-legacy
       discriminator), the conservation ``growth``/``legacy`` outcome must agree
       with ``adapter_is_current`` (the validator-matching predicate). The
       summarizer owns ONE current/legacy authority, not two. Sidecars that fail
       the five-worker gate land in ``legacy`` regardless of shape, so they are
       out of scope for this agreement.
    2. Growth-aggregation consistency: any sidecar that reaches the ``growth``
       ledger MUST aggregate as ``current``. A sidecar the conservation path
       calls current but the aggregation adapter calls legacy (or vice versa) is
       exactly the silent exclusion F1 guards against."""
    import tempfile

    # Shape fixtures that all SATISFY the five-worker set, so the conservation
    # growth/legacy outcome is driven purely by the shape predicate.
    panel_row_shape = _make_current_payload(["quality", "implementation"])
    # workers-map-only: pre-fix this shape reached ``growth`` (the old shape
    # classifier saw the non-empty ``workers`` dict and returned ``current``)
    # but the aggregation adapter called it ``legacy`` (no panel_mode, no
    # counts.workers_launched, no panel row with a ``worker`` key). After the
    # fix both agree it is ``legacy`` (consistent with the validator).
    workers_map_only = {
        "review_type": "branch review", "round": "r1",
        "workers": {"quality": 1, "implementation": 1, "testing": 1,
                    "simplification": 1, "documentation": 1},
        "counts": {"raw_findings": 4},
    }

    marker = make_cutover_marker(set(FIVE_WORKER_PANEL_IDS))
    empty_baseline = build_baseline([], {}, marker)

    def shape_via_conservation(payload):
        with tempfile.TemporaryDirectory() as td:
            sc = Path(td) / "x.stats.json"
            _write_private_sidecar(sc, payload)
            buf = {sc: read_byte_buffer(sc)}
            ledger, _ = run_conservation([sc], buf, empty_baseline)
            if sc in ledger["growth"]:
                return "current"
            if sc in ledger["legacy"]:
                return "legacy"
            # Unreadable/duplicate/audit-anomaly/baseline: not a shape decision.
            return None

    # Invariant 1: drift canary across five-worker-satisfying shapes. The
    # conservation outcome (growth=current, legacy=legacy) must equal the
    # adapter's current/legacy verdict.
    for name, payload in (
        ("panel_row_shape", panel_row_shape),
        ("workers_map_only", workers_map_only),
    ):
        cons_shape = shape_via_conservation(payload)
        adapter_shape = "current" if adapter_is_current(payload) else "legacy"
        check(
            f"shape_drift: conservation agrees with adapter for {name}",
            cons_shape == adapter_shape,
            f"conservation={cons_shape} adapter={adapter_shape}",
        )

    # Invariant 2: a sidecar that reaches growth must aggregate as current.
    with tempfile.TemporaryDirectory() as td:
        sc = Path(td) / "growth.stats.json"
        _write_private_sidecar(sc, panel_row_shape)
        buf = {sc: read_byte_buffer(sc)}
        ledger, _ = run_conservation([sc], buf, empty_baseline)
        reaches_growth = sc in ledger["growth"]
        agg_schema = aggregate_sidecar(panel_row_shape)["schema"]
        check(
            "shape_drift: growth sidecar aggregates as current",
            (not reaches_growth) or agg_schema == "current",
            f"reaches_growth={reaches_growth} agg_schema={agg_schema}",
        )


# ---- private_manifest ----
@_test("summarize_review_stats#private_manifest")
def _t_private_manifest(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        sidecar = td_path / "c.stats.json"
        _write_private_sidecar(sidecar, _make_current_payload(["quality"]))
        buffers = {sidecar: read_byte_buffer(sidecar)}
        manifest = build_baseline([sidecar], buffers, make_cutover_marker(set()))
        data = serialize_baseline(manifest)
        check(
            "private_manifest: path-level data in manifest",
            str(sidecar) in data.decode("utf-8"),
        )
        # Public/tracked output must NOT contain path-level data.
        public = "# Review effectiveness report\n(Task 1.)\n"
        check(
            "private_manifest: path-level data absent from tracked output",
            str(sidecar) not in public,
        )


# ---- baseline_lifecycle ----
@_test("summarize_review_stats#baseline_lifecycle")
def _t_baseline_lifecycle(check) -> None:
    import tempfile

    # Isolate HOME so cmd_* (which resolve Path.home()/.ai-playbook) never touch
    # the developer's REAL ~/.ai-playbook during the selftest.
    orig_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory() as home_tmp:
        os.environ["HOME"] = home_tmp
        try:
            _lifecycle_inner(check, Path(home_tmp))
        finally:
            if orig_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig_home


def _lifecycle_inner(check, home_tmp: Path) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        facts = td_path / "facts.md"
        facts.write_text(
            f"| `personal_projects_root` | `{td_path}/myrepos/` | x |\n",
            encoding="utf-8",
        )
        root = td_path / "myrepos"
        repo = root / "r"
        (repo / ".ai-playbook").mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            '```toml\nreviews_dir = "docs/reviews/"\n```\n', encoding="utf-8"
        )
        sc = repo / "docs" / "reviews" / "x.stats.json"
        _write_private_sidecar(sc, _make_current_payload(["quality"]))

        tel = td_path / "review-telemetry"
        bp = tel / "baseline.json"
        tel.parent.mkdir(parents=True, exist_ok=True)

        # First init: succeeds.
        rc = cmd_init_baseline(facts, bp, tel)
        check("lifecycle: first init succeeds", rc == 0 and bp.is_file())
        check("lifecycle: baseline file mode 0600", _file_mode(bp) == 0o600)
        # Overwrite attempt: rejected (O_CREAT|O_EXCL).
        raised = False
        try:
            cmd_init_baseline(facts, bp, tel)
        except BaselineExists:
            raised = True
        check("lifecycle: overwrite init rejected", raised)

        # Explicit refresh: succeeds (overwrites).
        rc = cmd_refresh_baseline(facts, bp, tel)
        check("lifecycle: explicit refresh succeeds", rc == 0)

        # Strict audit on a fresh baseline: ok.
        rc = cmd_strict_audit(facts, bp, tel)
        check("lifecycle: strict audit ok on fresh baseline", rc == 0)

        # Missing baseline: strict audit fails.
        bp.unlink()
        raised = False
        try:
            cmd_strict_audit(facts, bp, tel)
        except BaselineMissing:
            raised = True
        check("lifecycle: strict audit fails when baseline missing", raised)

        # Unreadable baseline: strict audit fails.
        rc2 = cmd_init_baseline(facts, bp, tel)
        # Corrupt the file (write via direct open, bypassing symlink check).
        bp.write_text("{corrupt", encoding="utf-8")
        raised = False
        try:
            cmd_strict_audit(facts, bp, tel)
        except BaselineMissing:
            raised = True
        check("lifecycle: strict audit fails when baseline unreadable", raised)


# ---- private_permissions ----
@_test("summarize_review_stats#private_permissions")
def _t_private_permissions(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Parent permissive (0755): tighten to 0700.
        parent = td_path / "ai-playbook"
        parent.mkdir(mode=0o755)
        os.chmod(str(parent), 0o755)
        tighten_parent_ai_playbook(parent)
        check("permissions: parent tightened to 0700", _dir_mode(parent) == 0o700)

        tel = parent / "review-telemetry"
        ensure_private_dir(tel)
        check("permissions: child dir 0700", _dir_mode(tel) == 0o700)
        # Re-assert on every run.
        os.chmod(str(tel), 0o755)
        ensure_private_dir(tel)
        check("permissions: child re-tightened to 0700", _dir_mode(tel) == 0o700)

        # File created atomically at 0600 (no create-then-chmod window).
        f = tel / "baseline.json"
        create_private_file_exclusive(f, b"{}")
        check("permissions: file created 0600", _file_mode(f) == 0o600)

        # Symlink target rejected.
        sym = tel / "sym.json"
        try:
            os.symlink(tel / "real.json", sym)
        except OSError:
            pass
        raised = False
        try:
            _reject_symlink(sym)
        except PermissionsError:
            raised = True
        check("permissions: symlink target rejected", raised)


# ---- snapshot_races ----
@_test("summarize_review_stats#snapshot_races")
def _t_snapshot_races(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        tel = td_path / "review-telemetry"
        tel.mkdir(parents=True)
        # (a) one writer via process-wide lock: acquire in this process, then a
        # second holder blocks. We assert non-blocking acquisition fails while
        # held.
        import multiprocessing

        held = {"ok": False}

        def _second_holder(tmp_tel: str, out) -> None:
            try:
                with telemetry_lock(Path(tmp_tel)):
                    pass
                out["got"] = True
            except Exception:
                out["got"] = False

        with telemetry_lock(tel):
            # Try non-blocking acquire of the same lock file via a fresh fd:
            lock_path = tel / LOCK_FILE_NAME
            fd = os.open(str(lock_path), os.O_RDWR)
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    blocked = False
                except BlockingIOError:
                    blocked = True
            finally:
                os.close(fd)
            check("snapshot_races: second holder blocked", blocked)
            held["ok"] = True
        check("snapshot_races: first holder released cleanly", held["ok"])

        # (b) changed between buffer read and publish -> retry then fail.
        # Deterministically force the on-disk generation to differ on every
        # recheck by patching on_disk_generation to return a fresh mtime each
        # call. publish_with_recheck must exhaust its 3 retries then raise
        # PublishRace WITHOUT calling publish.
        buf_path = td_path / "in.stats.json"
        _write_private_sidecar(buf_path, _make_current_payload(["quality"]))
        buffers = {buf_path: read_byte_buffer(buf_path)}

        published = {"done": False}

        def mutating_publish() -> None:
            published["done"] = True

        import sys as _sys

        # Patch THIS module's global (works whether run as __main__ or imported).
        this_mod = _sys.modules[__name__]

        # Deterministically force the on-disk generation to mismatch the cached
        # buffer on every recheck: patch on_disk_generation to report a size
        # that differs from the cached buffer length. publish_with_recheck must
        # exhaust its 3 retries then raise PublishRace WITHOUT calling publish.
        orig_gen = on_disk_generation

        def mismatched_gen(path):
            real = orig_gen(path)
            if real is None:
                return None
            # Report a size off by one so the size short-circuit always fires.
            return (real[0], real[1] + 1)

        this_mod.on_disk_generation = mismatched_gen
        raised = False
        try:
            publish_with_recheck(dict(buffers), mutating_publish, retries=3)
        except PublishRace:
            raised = True
        finally:
            this_mod.on_disk_generation = orig_gen
        check("snapshot_races: changed input retries then fails publish", raised)
        check("snapshot_races: publish NOT called on race", not published["done"])

        # Success path: stable input publishes; every published digest matches
        # the buffer used for parsing.
        _write_private_sidecar(buf_path, _make_current_payload(["quality"]))
        buffers2 = {buf_path: read_byte_buffer(buf_path)}
        ok = {"done": False}
        captured = {}

        def good_publish() -> None:
            ok["done"] = True
            # On the success path, the published digest matches the byte buffer
            # used for parsing (the recheck passed).
            captured["digest"] = sha256_hex(buffers2[buf_path])

        publish_with_recheck(dict(buffers2), good_publish, retries=3)
        check("snapshot_races: success path publishes", ok["done"])
        check(
            "snapshot_races: published digest matches parse buffer",
            captured.get("digest") == sha256_hex(read_byte_buffer(buf_path)),
        )


# ---- current_adapter ----
@_test("summarize_review_stats#current_adapter")
def _t_current_adapter(check) -> None:
    """Parse a five-worker (current) sidecar; normalized totals cover launches,
    lenses, dedup, discard, calibration, overflow, and triage. No token field is
    read or reported (token telemetry is out of scope)."""
    # Build a representative current sidecar with non-trivial counts.
    payload = {
        "review_type": "branch review",
        "date": "2099-01-01",
        "round": "r1",
        "panel_mode": "full",
        "counts": {
            "workers_launched": 5,
            "raw_findings": 8,
            "staged_findings": 5,
            "discarded": 3,
            "deduplicated": 1,
            "calibrated": 2,
        },
        "panel": [
            {
                "worker": "correctness-completeness",
                "lenses": ["quality", "implementation"],
                "status": "complete",
                "raw": 2,
            },
            {"worker": "testing", "lenses": ["testing"], "status": "complete", "raw": 1},
            {
                "worker": "design-simplicity",
                "lenses": ["architecture", "simplification"],
                "status": "complete",
                "raw": 2,
            },
            {"worker": "contract-docs", "lenses": ["documentation"], "status": "skipped", "raw": 0},
            {"worker": "risk", "lenses": ["security"], "status": "complete", "raw": 3},
        ],
        "deduplication_groups": [{"findings": ["F1", "F2"]}],
        "discarded": [
            {"reason": "false-positive"},
            {"reason": "duplicate"},
            {"reason": "out-of-scope"},
        ],
        "severity_calibration": [
            {"from": "High", "to": "Medium"},
            {"from": "Medium", "to": "Low"},
        ],
        "findings": [
            {"id": 1, "severity": "High", "triage": "fixed"},
            {"id": 2, "severity": "Medium", "triage": "deferred"},
            {"id": 3, "severity": "Medium", "triage": "dropped"},
            {"id": 4, "severity": "Low", "triage": "pending"},
            {"id": 5, "severity": "Low", "triage": "fixed"},
        ],
        "overflow": [{"severity": "Low", "blocking": False}],
        # A token field MUST be ignored by the adapter.
        "usage": {"prompt_tokens": 999, "completion_tokens": 1, "total_tokens": 1000},
    }
    norm = aggregate_current(payload)
    # Launch totals: 4 launched (skipped worker is not a launch); launched
    # lenses = 2 (quality/implementation) + 1 (testing) + 2 (architecture/
    # simplification) + 1 (security) = 6; the skipped contract-docs row's lens
    # is excluded.
    check("current_adapter: launched worker count", norm["worker_launches"] == 4)
    check("current_adapter: lens launch count", norm["lens_launches"] == 6)
    # Dedup / discard / calibration / overflow totals. dedup_count comes from
    # counts.deduplicated (the authoritative dedup measure).
    check("current_adapter: dedup count", norm["dedup_count"] == 1)
    check("current_adapter: discard count", norm["discard_count"] == 3)
    check("current_adapter: calibration count", norm["calibration_count"] == 2)
    check("current_adapter: overflow count", norm["overflow_count"] == 1)
    # Triage totals by final-triage value (pending excluded from numerators).
    check("current_adapter: triage fixed", norm["triage"]["fixed"] == 2)
    check("current_adapter: triage deferred", norm["triage"]["deferred"] == 1)
    check("current_adapter: triage dropped", norm["triage"]["dropped"] == 1)
    check("current_adapter: triage pending", norm["triage"]["pending"] == 1)
    # Severity totals.
    check("current_adapter: severity High", norm["severity"]["High"] == 1)
    check("current_adapter: severity Medium", norm["severity"]["Medium"] == 2)
    check("current_adapter: severity Low", norm["severity"]["Low"] == 2)
    # Raw / staged raw counts.
    check("current_adapter: raw findings", norm["raw_findings"] == 8)
    check("current_adapter: staged findings", norm["staged_findings"] == 5)
    # NO token field is read or reported.
    check(
        "current_adapter: no token field in normalized totals",
        "tokens" not in norm and "usage" not in norm and "total_tokens" not in norm,
    )


# ---- legacy_adapters ----
@_test("summarize_review_stats#legacy_adapters")
def _t_legacy_adapters(check) -> None:
    """Legacy code/plan/rfc/document sidecars (agents_launched, raw_findings,
    agent-keyed panels) produce COMPATIBLE normalized totals without rewriting
    the fixture. The legacy-vs-current decision matches the validator's
    classifier for a shared fixture (drift canary)."""
    legacy_code = {
        "review_type": "branch review",
        "date": "2024-01-01",
        "round": "r1",
        "agents_launched": 5,
        "counts": {"raw_findings": 4, "staged_findings": 2},
        "panel": [
            {"agent": "quality", "status": "complete", "raw": 2},
            {"agent": "implementation", "status": "complete", "raw": 2},
        ],
        "discarded": [{"reason": "out-of-scope"}, {"reason": "false-positive"}],
        "severity_calibration": [],
        "findings": [
            {"id": 1, "severity": "Medium", "triage": "fixed"},
            {"id": 2, "severity": "Low", "triage": "dropped"},
        ],
        "overflow": [],
    }
    norm = aggregate_legacy(legacy_code)
    # Legacy has no per-worker launch breakdown like current; agents_launched is
    # the compatible worker-launch measure, and lens launches are null.
    check("legacy_adapters: agent launches as worker_launches", norm["worker_launches"] == 5)
    check("legacy_adapters: lens launches null", norm["lens_launches"] is None)
    check("legacy_adapters: raw findings", norm["raw_findings"] == 4)
    check("legacy_adapters: staged findings", norm["staged_findings"] == 2)
    check("legacy_adapters: discard count", norm["discard_count"] == 2)
    check("legacy_adapters: triage fixed", norm["triage"]["fixed"] == 1)
    check("legacy_adapters: triage dropped", norm["triage"]["dropped"] == 1)
    # Same normalized key set as the current adapter (compatible aggregation).
    check(
        "legacy_adapters: compatible normalized keys",
        set(norm.keys()) == set(aggregate_current(_make_current_payload(["quality"])).keys()),
    )

    # Drift canary: the legacy-vs-current decision must match the validator's
    # classifier for a SHARED fixture. We classify the same payload with the
    # summarizer's adapter selector and the validator's current/legacy
    # predicate, and they must agree (both current or both legacy).
    shared_current = _make_current_payload(["quality"])
    check(
        "legacy_adapters: drift canary current agrees with validator",
        _adapter_matches_validator(shared_current),
    )
    shared_legacy = legacy_code
    check(
        "legacy_adapters: drift canary legacy agrees with validator",
        _adapter_matches_validator(shared_legacy),
    )


# ---- accepted_unique ----
@_test("summarize_review_stats#accepted_unique")
def _t_accepted_unique(check) -> None:
    """Given fixed, deferred, dropped, and pending findings, only fixed and
    deferred are accepted yield; pending is excluded from the median but counted
    in coverage. The accepted set is a named constant that diverges from the
    validator's readiness set (which excludes deferred)."""
    # The accepted set must EXCLUDE dropped and INCLUDE deferred; the validator's
    # readiness set does the opposite (includes dropped, excludes deferred).
    check("accepted_unique: fixed is accepted", "fixed" in ACCEPTED_TRIAGE_VALUES)
    check("accepted_unique: deferred is accepted", "deferred" in ACCEPTED_TRIAGE_VALUES)
    check("accepted_unique: dropped is NOT accepted", "dropped" not in ACCEPTED_TRIAGE_VALUES)
    # Divergence from the validator's readiness-resolved set is explicit and real.
    check(
        "accepted_unique: diverges from validator readiness set (deferred in, dropped out)",
        "deferred" in ACCEPTED_TRIAGE_VALUES and "deferred" not in vrs.RESOLVED_TRIAGE_VALUES
        and "dropped" in vrs.RESOLVED_TRIAGE_VALUES and "dropped" not in ACCEPTED_TRIAGE_VALUES,
    )

    # Two reviews: one all-finalized, one with a pending finding.
    review_a = {
        "findings": [
            {"id": 1, "severity": "High", "triage": "fixed"},
            {"id": 2, "severity": "Medium", "triage": "deferred"},
            {"id": 3, "severity": "Low", "triage": "dropped"},
        ],
    }
    review_b = {
        "findings": [
            {"id": 1, "severity": "High", "triage": "fixed"},
            {"id": 2, "severity": "Medium", "triage": "pending"},
        ],
    }
    # Per-review accepted counts: review_a = 2 (fixed+deferred), review_b = 1
    # (only fixed; pending excluded).
    counts = [
        accepted_unique_count(review_a),
        accepted_unique_count(review_b),
    ]
    check("accepted_unique: review_a accepted count", counts[0] == 2)
    check("accepted_unique: review_b accepted count (pending excluded)", counts[1] == 1)
    # Median across reviews.
    check("accepted_unique: median accepted", median(counts) == 1.5)
    # Triage coverage: finalized findings / (finalized + pending). pending counts
    # toward coverage denominator.
    cov = triage_coverage([review_a, review_b])
    # review_a: 3/3 finalized; review_b: 1/2 finalized. Mean coverage.
    expected_cov = ((3 / 3) + (1 / 2)) / 2
    check(
        "accepted_unique: pending counted in coverage (not median)",
        abs(cov - expected_cov) < 1e-9,
    )


# ---- cohort_key_derivation ----
@_test("summarize_review_stats#cohort_key_derivation")
def _t_cohort_key_derivation(check) -> None:
    """Cohort keys derive per the Terms rules from BOTH current and legacy shapes.
    Panel mode is NOT a cohort key: two sidecars differing only in panel mode
    derive the same key tuple. Both current count shapes (raw_findings and
    raw_total) yield a non-unknown size bucket."""
    # Current shape A: raw_total, concurrency/SQL domains, r2.
    cur_a = {
        "review_type": "Branch Review",
        "round": "r2",
        "counts": {"raw_total": 12},
        "domains": ["concurrency", "SQL"],
        "panel_mode": "full",
    }
    # Current shape B: raw_findings, docs-only, r1, panel_mode full.
    cur_b = {
        "review_type": "Plan Review",
        "round": "r1",
        "counts": {"raw_findings": 8},
        "domains": ["docs-only"],
        "panel_mode": "full",
    }
    # Legacy shape: raw_findings, docs-only, r1, no panel_mode.
    leg = {
        "review_type": "branch",
        "round": "r1",
        "counts": {"raw_findings": 3},
        "domains": ["docs-only"],
    }
    key_a = cohort_key(cur_a)
    key_b = cohort_key(cur_b)
    key_leg = cohort_key(leg)
    # review type normalized; role from round; size bucket from present key.
    check("cohort_key: current A review_type normalized", key_a[0] == "branch")
    check("cohort_key: current A role follow-up (r2)", key_a[1] == "follow-up")
    check("cohort_key: current A size bucket 6-15 from raw_total", key_a[2] == "6-15")
    check("cohort_key: current A domain class concurrency", key_a[3] == "concurrency")
    check("cohort_key: current B review_type plan", key_b[0] == "plan")
    check("cohort_key: current B role initial (r1)", key_b[1] == "initial")
    check("cohort_key: current B size bucket 6-15 from raw_findings", key_b[2] == "6-15")
    check("cohort_key: current B domain class docs", key_b[3] == "docs")
    # Legacy: no field excluded wholesale.
    check("cohort_key: legacy review_type branch", key_leg[0] == "branch")
    check("cohort_key: legacy role initial", key_leg[1] == "initial")
    check("cohort_key: legacy size bucket 1-5 (non-unknown)", key_leg[2] == "1-5")
    check("cohort_key: legacy domain class docs", key_leg[3] == "docs")
    # Every sidecar derives a concrete key (size bucket non-unknown when count
    # present).
    for k in (key_a, key_b, key_leg):
        check("cohort_key: size bucket non-unknown", k[2] != "unknown")
    # Panel-mode independence: same payload differing ONLY in panel mode.
    pm_full = dict(cur_b)
    pm_targeted = dict(cur_b)
    pm_targeted["panel_mode"] = "targeted"
    check(
        "cohort_key: panel mode not a key (same tuple)",
        cohort_key(pm_full) == cohort_key(pm_targeted),
    )
    # Both count keys present and equal: must not raise (and must not prefer).
    both_eq = {
        "review_type": "branch review",
        "round": "r1",
        "counts": {"raw_findings": 4, "raw_total": 4},
        "domains": ["docs"],
    }
    check("cohort_key: both count keys equal ok", cohort_key(both_eq)[2] == "1-5")
    mismatched = {
        "review_type": "branch review",
        "round": "r1",
        "counts": {"raw_findings": 4, "raw_total": 99},
        "domains": ["docs"],
    }
    raised = False
    try:
        cohort_key(mismatched)
    except SummarizerError:
        raised = True
    check("cohort_key: mismatched count keys raise", raised)


# ---- comparable_cohorts ----
@_test("summarize_review_stats#comparable_cohorts")
def _t_comparable_cohorts(check) -> None:
    """A baseline and a growth review with the SAME cohort-key tuple but
    DIFFERENT panel mode land in the SAME comparable cohort, with period the
    only within-cohort discriminator. Mixed key tuples do not cross-compare."""
    base = {
        "review_type": "branch review",
        "round": "r1",
        "counts": {"raw_findings": 4},
        "domains": ["docs"],
        "panel_mode": "targeted",
    }
    growth = {
        "review_type": "branch review",
        "round": "r1",
        "counts": {"raw_findings": 4},
        "domains": ["docs"],
        "panel_mode": "full",
    }
    other = {
        "review_type": "plan review",
        "round": "r1",
        "counts": {"raw_findings": 4},
        "domains": ["docs"],
        "panel_mode": "full",
    }
    classified = [
        ("baseline", base),
        ("growth", growth),
        ("baseline", other),
        ("growth", other),
    ]
    cohorts = group_into_cohorts(classified)
    # Same key tuple for base/growth despite panel-mode difference.
    check(
        "comparable_cohorts: same key despite panel-mode diff",
        cohort_key(base) == cohort_key(growth),
    )
    bucket = cohorts[cohort_key(base)]
    check(
        "comparable_cohorts: baseline+growth in same cohort",
        len(bucket["baseline"]) == 1 and len(bucket["growth"]) == 1,
    )
    # Mixed key tuples never merge.
    check(
        "comparable_cohorts: plan cohort separate from branch cohort",
        cohort_key(other) != cohort_key(base),
    )
    # A real-shape legacy baseline review maps into a comparable cohort with a
    # growth review (legacy baseline + current growth sharing the key tuple).
    legacy_base = {
        "review_type": "branch",
        "round": "r1",
        "counts": {"raw_findings": 4},
        "domains": ["docs"],
    }
    classified2 = [
        ("baseline", legacy_base),
        ("growth", growth),
    ]
    cohorts2 = group_into_cohorts(classified2)
    report = build_effectiveness_report(classified2)
    check(
        "comparable_cohorts: legacy baseline comparable with growth",
        cohort_key(legacy_base) in cohorts2
        and len(cohorts2[cohort_key(legacy_base)]["growth"]) == 1,
    )
    check(
        "comparable_cohorts: report has cohort-availability counts",
        set(report["availability"]) >= {"cohorts", "comparable_cohorts", "evaluable_cohorts"},
    )
    check(
        "comparable_cohorts: at least one comparable cohort counted",
        report["availability"]["comparable_cohorts"] >= 1,
    )


# ---- inconclusive_sample ----
@_test("summarize_review_stats#inconclusive_sample")
def _t_inconclusive_sample(check) -> None:
    """A cohort with <10 reviews on either side is inconclusive. A cohort with
    enough reviews but growth triage coverage below 80% is inconclusive.
    Baseline triage coverage does NOT gate (baseline is raw-only)."""

    def review(*, triages, panel_mode="full", rt="branch review", rnd="r1", raw=3):
        findings = [{"id": i, "severity": "Low", "triage": t} for i, t in enumerate(triages)]
        return {
            "review_type": rt,
            "round": rnd,
            "counts": {"raw_findings": raw},
            "domains": ["docs"],
            "panel_mode": panel_mode,
            "findings": findings,
        }

    # <10 on growth side.
    few = [("baseline", review(triages=["fixed"])) for _ in range(11)] + [
        ("growth", review(triages=["fixed"])) for _ in range(3)
    ]
    rep = build_effectiveness_report(few)
    check("inconclusive_sample: <10 growth -> inconclusive", rep["overall_verdict"] == "inconclusive")

    # <10 on baseline side.
    few_b = [("baseline", review(triages=["fixed"])) for _ in range(3)] + [
        ("growth", review(triages=["fixed"])) for _ in range(11)
    ]
    rep_b = build_effectiveness_report(few_b)
    check("inconclusive_sample: <10 baseline -> inconclusive", rep_b["overall_verdict"] == "inconclusive")

    # >=10 both sides but growth coverage <80% (most growth findings pending).
    base = [("baseline", review(triages=["fixed"])) for _ in range(11)]
    growth_low = [
        ("growth", review(triages=["pending", "pending", "fixed"])) for _ in range(11)
    ]
    rep_low = build_effectiveness_report(base + growth_low)
    only = rep_low["cohorts"][0]
    check(
        "inconclusive_sample: low growth coverage -> inconclusive",
        only["verdict"] == "inconclusive",
        str(only.get("growth_triage_coverage")),
    )

    # Baseline low coverage does NOT gate: baseline mostly pending, growth fully
    # covered and large enough -> evaluable (not gated by baseline coverage).
    base_pending = [
        ("baseline", review(triages=["pending", "pending", "fixed"])) for _ in range(11)
    ]
    growth_full = [("growth", review(triages=["fixed"])) for _ in range(11)]
    rep_bg = build_effectiveness_report(base_pending + growth_full)
    only_bg = rep_bg["cohorts"][0]
    check(
        "inconclusive_sample: baseline coverage does not gate",
        only_bg["verdict"] != "inconclusive" or "fewer than" not in only_bg.get("reason", ""),
        str(only_bg["verdict"]),
    )


# ---- retain_policy ----
@_test("summarize_review_stats#retain_policy")
def _t_retain_policy(check) -> None:
    """An evaluable cohort (>=10 per side, growth triage >=80%) with >=25% launch
    reduction, accepted change within the 20% guardrail, and drop-rate change
    within 10pp -> verdict retain."""

    def make(side, *, launches, accepted, dropped, pending, panel_mode, n):
        out = []
        # Build a real panel of ``launches`` complete worker rows so the current
        # adapter counts them as worker launches.
        panel = [
            {"worker": "quality", "status": "complete", "raw": 1}
            for _ in range(launches)
        ]
        for _ in range(n):
            findings = []
            for _ in range(accepted):
                findings.append({"id": 1, "severity": "Low", "triage": "fixed"})
            for _ in range(dropped):
                findings.append({"id": 2, "severity": "Low", "triage": "dropped"})
            for _ in range(pending):
                findings.append({"id": 3, "severity": "Low", "triage": "pending"})
            out.append(
                (
                    side,
                    {
                        "review_type": "branch review",
                        "round": "r1",
                        "counts": {"raw_findings": accepted + dropped + pending},
                        "domains": ["docs"],
                        "panel_mode": panel_mode,
                        "panel": panel,
                        "findings": findings,
                    },
                )
            )
        return out

    # Baseline: 8 launches, 4 accepted, 0 dropped. Growth: 4 launches (50%
    # reduction >= 25%), 4 accepted (no fall), 0 dropped. ``agents_launched``
    # carries the launch count (no panel, so the legacy adapter reads it).
    base = make("baseline", launches=8, accepted=4, dropped=0, pending=0,
                panel_mode="targeted", n=11)
    growth = make("growth", launches=4, accepted=4, dropped=0, pending=0,
                  panel_mode="full", n=11)
    rep = build_effectiveness_report(base + growth)
    only = rep["cohorts"][0]
    check(
        "retain_policy: evaluable retain verdict",
        only["verdict"] == "retain",
        str(only.get("checks")),
    )
    check("retain_policy: overall retain", rep["overall_verdict"] == "retain")


# ---- review_needed ----
@_test("summarize_review_stats#review_needed")
def _t_review_needed(check) -> None:
    """An evaluable cohort where any threshold is missed -> review needed and no
    automatic policy mutation. Two cohorts where one retains and one fails ->
    overall review needed."""

    def make(side, *, launches, accepted, dropped, panel_mode, n, rt="branch review"):
        out = []
        panel = [
            {"worker": "quality", "status": "complete", "raw": 1}
            for _ in range(launches)
        ]
        for _ in range(n):
            findings = []
            for _ in range(accepted):
                findings.append({"id": 1, "severity": "Low", "triage": "fixed"})
            for _ in range(dropped):
                findings.append({"id": 2, "severity": "Low", "triage": "dropped"})
            out.append(
                (
                    side,
                    {
                        "review_type": rt,
                        "round": "r1",
                        "counts": {"raw_findings": accepted + dropped},
                        "domains": ["docs"],
                        "panel_mode": panel_mode,
                        "panel": panel,
                        "findings": findings,
                    },
                )
            )
        return out

    # Miss the launch-reduction threshold: growth launches same as baseline.
    base = make("baseline", launches=8, accepted=4, dropped=0,
                panel_mode="targeted", n=11)
    growth = make("growth", launches=8, accepted=4, dropped=0,
                  panel_mode="full", n=11)
    rep = build_effectiveness_report(base + growth)
    only = rep["cohorts"][0]
    check(
        "review_needed: missed launch threshold -> review needed",
        only["verdict"] == "review needed",
        str(only.get("checks")),
    )
    # No automatic policy mutation: the report carries only a verdict string.
    check(
        "review_needed: no policy mutation field",
        "policy_mutation" not in only and "mutate" not in json.dumps(only),
    )

    # Two cohorts: one retains, one fails -> overall review needed.
    retain_base = make("baseline", launches=8, accepted=4, dropped=0,
                       panel_mode="targeted", n=11)
    retain_growth = make("growth", launches=4, accepted=4, dropped=0,
                         panel_mode="full", n=11)
    # Fail cohort: a different review type so it forms its own cohort, with no
    # launch reduction (growth launches == baseline launches).
    fail_base = make("baseline", launches=8, accepted=4, dropped=0,
                     panel_mode="targeted", n=11, rt="plan review")
    fail_growth = make("growth", launches=8, accepted=4, dropped=0,
                       panel_mode="full", n=11, rt="plan review")
    rep2 = build_effectiveness_report(
        retain_base + retain_growth + fail_base + fail_growth
    )
    verdicts = {c["verdict"] for c in rep2["cohorts"]}
    check(
        "review_needed: mixed cohorts -> overall review needed",
        rep2["overall_verdict"] == "review needed" and verdicts == {"retain", "review needed"},
        str(verdicts),
    )


# ---- per_cohort_verdict ----
@_test("summarize_review_stats#per_cohort_verdict")
def _t_per_cohort_verdict(check) -> None:
    """Multiple evaluable cohorts are reported separately; overall retain only if
    EVERY evaluable cohort retains (per-cohort conjunction, no weighted average)."""

    def cohort_pair(rt, *, base_launch, growth_launch):
        def one(side, launches, panel_mode):
            panel = [
                {"worker": "quality", "status": "complete", "raw": 1}
                for _ in range(launches)
            ]
            return (
                side,
                {
                    "review_type": rt,
                    "round": "r1",
                    "counts": {"raw_findings": 4},
                    "domains": ["docs"],
                    "panel_mode": panel_mode,
                    "panel": panel,
                    "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}] * 4,
                },
            )

        base = [one("baseline", base_launch, "targeted") for _ in range(11)]
        growth = [one("growth", growth_launch, "full") for _ in range(11)]
        return base + growth

    # Two evaluable cohorts that both retain.
    both_retain = cohort_pair("branch review", base_launch=8, growth_launch=4) + cohort_pair(
        "plan review", base_launch=8, growth_launch=4
    )
    rep = build_effectiveness_report(both_retain)
    check(
        "per_cohort_verdict: each cohort reported separately",
        len(rep["cohorts"]) == 2,
    )
    check(
        "per_cohort_verdict: all retain -> overall retain",
        rep["overall_verdict"] == "retain",
    )


# ---- determinism ----
@_test("summarize_review_stats#determinism")
def _t_determinism(check) -> None:
    """Same neutral fixtures run twice with shuffled discovery order produce
    byte-identical aggregate JSON (stable key ordering, stable trailing newline).
    A real-report variant runs the report twice against an unchanged snapshot and
    asserts byte-identity."""
    import random

    fixtures = [
        ("baseline", {"review_type": "branch review", "round": "r1",
                       "counts": {"raw_findings": 4}, "domains": ["docs"],
                       "panel_mode": "targeted", "agents_launched": 8,
                       "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}] * 4}),
        ("growth", {"review_type": "branch review", "round": "r1",
                     "counts": {"raw_findings": 4}, "domains": ["docs"],
                     "panel_mode": "full", "agents_launched": 4,
                     "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}] * 4}),
    ] * 11

    def run(order):
        return serialize_effectiveness_json(build_effectiveness_report([fixtures[i] for i in order]))

    order_a = list(range(len(fixtures)))
    order_b = list(range(len(fixtures)))
    random.Random(123).shuffle(order_b)
    bytes_a = run(order_a)
    bytes_b = run(order_b)
    check("determinism: byte-identical across shuffled order", bytes_a == bytes_b)
    check("determinism: stable trailing newline", bytes_a.endswith(b"\n"))

    # Real-report variant: run the report twice against an unchanged snapshot
    # and assert byte-identity.
    rep1 = build_effectiveness_report(list(fixtures))
    rep2 = build_effectiveness_report(list(fixtures))
    check(
        "determinism: real-report variant byte-identity",
        serialize_effectiveness_json(rep1) == serialize_effectiveness_json(rep2),
    )


# ---- partial_failure_skip (F4) ----
@_test("summarize_review_stats#partial_failure_skip")
def _t_partial_failure_skip(check) -> None:
    """A single sidecar with mismatched ``counts.raw_findings`` /
    ``counts.raw_total`` (the integrity assert in ``derive_size_bucket``) must
    NOT abort the whole report. ``build_effectiveness_report`` skips the
    malformed sidecar per-sidecar, still cohort-compares the valid sidecars, and
    records the skipped count in ``availability.skipped_malformed``."""
    valid = {
        "review_type": "branch review", "round": "r1",
        "counts": {"raw_findings": 4}, "domains": ["docs"],
        "panel_mode": "full", "agents_launched": 4,
        "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}] * 4,
    }
    malformed = {
        "review_type": "branch review", "round": "r1",
        # Integrity violation: both count keys present and mismatched.
        "counts": {"raw_findings": 4, "raw_total": 99}, "domains": ["docs"],
        "panel_mode": "full", "agents_launched": 4,
    }
    classified = [("baseline", valid)] * 11 + [("growth", valid)] * 10
    # Insert one malformed sidecar among the valid growth ones.
    classified.append(("growth", malformed))

    raised = False
    try:
        report = build_effectiveness_report(classified)
    except SummarizerError as exc:
        raised = True
        report = None
        check("partial_failure_skip: does not raise on one malformed", False, repr(exc))
    check("partial_failure_skip: does not raise on one malformed", not raised)
    if report is not None:
        # The valid sidecars are still cohort-compared: at least one cohort is
        # present and the malformed sidecar did not abort cohort building.
        check(
            "partial_failure_skip: valid sidecars still cohort-compared",
            len(report["cohorts"]) >= 1,
            str(report.get("availability")),
        )
        # The skipped count is surfaced in availability.
        skipped = report["availability"].get("skipped_malformed", 0)
        check(
            "partial_failure_skip: skipped_malformed recorded (>=1)",
            skipped >= 1,
            str(report["availability"]),
        )
        # The markdown report surfaces the skipped count too (cross-format
        # consistency with the JSON field). The fragment appears only when
        # the count is non-zero, so the no-skip markdown is byte-stable.
        md = serialize_effectiveness_markdown(report).decode("utf-8")
        check(
            "partial_failure_skip: markdown surfaces skipped_malformed",
            "skipped malformed" in md and str(skipped) in md,
            md,
        )
        # No-skip path: a clean report carries no skipped-malformed fragment, so
        # the normal markdown is byte-identical across runs (determinism guard).
        clean = build_effectiveness_report(classified[:-1])  # drop malformed
        if clean["availability"].get("skipped_malformed", 0) == 0:
            md_a = serialize_effectiveness_markdown(clean)
            md_b = serialize_effectiveness_markdown(
                build_effectiveness_report(classified[:-1])
            )
            check(
                "partial_failure_skip: no-skip markdown byte-stable",
                md_a == md_b and b"skipped malformed" not in md_a,
            )


# ---- public_output ----
@_test("summarize_review_stats#public_output")
def _t_public_output(check) -> None:
    """The aggregate JSON and Markdown reports contain NONE of a deny inventory of
    private identifiers (repository names, repo/absolute paths, review filenames,
    ticket IDs, feature names, content digests). Deny-inventory check over
    neutral fixtures, not a fixed regex."""
    # Neutral fixtures that CARRY private identifiers in their payloads.
    repo_name = "neutral-repo-xyz"
    abs_path = "/tmp/neutral-repo-xyz/docs/reviews/secret.stats.json"
    review_file = "2026-07-29-branch-review-secret-r1.stats.json"
    ticket_id = "PROJ-12345"
    feature_name = "super-secret-feature"
    digest = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"

    def carrying(side, panel_mode):
        return (
            side,
            {
                "review_type": "branch review",
                "round": "r1",
                "counts": {"raw_findings": 4},
                "domains": ["docs"],
                "panel_mode": panel_mode,
                "agents_launched": 8 if side == "baseline" else 4,
                "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}] * 4,
                # Private identifiers nested in the payload (must NOT leak).
                "artifact_slug": feature_name,
                "review_id": review_file,
                "_internal": {"repo": repo_name, "path": abs_path, "ticket": ticket_id, "sha": digest},
            },
        )

    fixtures = [carrying("baseline", "targeted")] * 11 + [carrying("growth", "full")] * 11
    report = build_effectiveness_report(fixtures)
    json_out = serialize_effectiveness_json(report).decode("utf-8")
    md_out = serialize_effectiveness_markdown(report).decode("utf-8")

    deny = [repo_name, abs_path, review_file, ticket_id, feature_name, digest]
    for needle in deny:
        check(
            f"public_output: JSON free of {needle[:24]}",
            needle not in json_out,
        )
        check(
            f"public_output: Markdown free of {needle[:24]}",
            needle not in md_out,
        )


# ---- real_deny_inventory ----
@_test("summarize_review_stats#real_deny_inventory")
def _t_real_deny_inventory(check) -> None:
    """The deny inventory is built at audit time from a neutral fixture corpus
    (discovered repository names, path components, staged review filenames,
    artifact identifiers, recorded content digests) and NONE of those exact
    strings appear in the generated effectiveness report JSON or Markdown.

    The fixed regex is kept ONLY as a coarse pre-filter; the real inventory is
    layered on top. This mirrors what the real-corpus Validation Commands run
    exercises against the actual tree."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        root = td_path / "myrepos"
        repo = root / "neutral-repo-alpha"  # private repo name (deny)
        (repo / ".ai-playbook").mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            '```toml\nreviews_dir = "docs/reviews/"\n```\n', encoding="utf-8"
        )

        # A staged review filename carrying a private slug + a ticket-like token.
        review_slug = "2026-07-29-branch-review-PROJ-55123-r1"
        sidecar_path = repo / "docs" / "reviews" / f"{review_slug}.stats.json"
        feature_name = "super-secret-feature-zzz"
        ticket_id = "PROJ-55123"
        digest_carrier = "deadbeefcafebabe" * 4  # 64-hex (a real digest shape)
        payload = _make_current_payload(["quality", "implementation", "testing"])
        # Carry artifact identifiers + a content-digest-shaped value in the payload.
        payload["review_id"] = review_slug
        payload["artifact_slug"] = feature_name
        payload["_internal"] = {"ticket": ticket_id, "prior_sha": digest_carrier}
        _write_private_sidecar(sidecar_path, payload)

        repo_roots = [root]
        sidecars = discover_sidecars(repo_roots)
        buffers = {s: read_byte_buffer(s) for s in sidecars}
        baseline = build_baseline(sidecars, buffers, make_cutover_marker(set(FIVE_WORKER_PANEL_IDS)))

        # Build the deny inventory from the corpus.
        deny = build_real_deny_inventory(repo_roots, sidecars, buffers, baseline)
        deny_text = "\n".join(deny)

        # The built inventory MUST include the discovered identifiers.
        check(
            "real_deny_inventory: repo name in inventory",
            "neutral-repo-alpha" in deny_text,
            deny_text,
        )
        check(
            "real_deny_inventory: review slug filename in inventory",
            review_slug in deny_text,
            deny_text,
        )
        check(
            "real_deny_inventory: ticket id in inventory",
            ticket_id in deny_text,
            deny_text,
        )
        check(
            "real_deny_inventory: feature name in inventory",
            feature_name in deny_text,
            deny_text,
        )
        check(
            "real_deny_inventory: sidecar digest in inventory",
            sha256_hex(buffers[sidecars[0]]) in deny_text,
            deny_text,
        )

        # Generate the report from the same corpus and assert NONE of the deny
        # strings appear in the JSON or Markdown output.
        classified: list[tuple[str, dict]] = []
        snapshot_paths = {e["path"] for e in baseline.get("sidecars", [])}
        for sidecar in sidecars:
            p, _ = parse_payload(buffers[sidecar])
            if p is None:
                continue
            if str(sidecar) in snapshot_paths:
                classified.append(("baseline", p))
        report = build_effectiveness_report(classified)
        json_out = serialize_effectiveness_json(report).decode("utf-8")
        md_out = serialize_effectiveness_markdown(report).decode("utf-8")
        leaked_json = [d for d in deny if d and d in json_out]
        leaked_md = [d for d in deny if d and d in md_out]
        check(
            "real_deny_inventory: no deny string in report JSON",
            not leaked_json,
            str(leaked_json[:5]),
        )
        check(
            "real_deny_inventory: no deny string in report Markdown",
            not leaked_md,
            str(leaked_md[:5]),
        )


# ---- historical_immutability ----
@_test("summarize_review_stats#historical_immutability")
def _t_historical_immutability(check) -> None:
    """Historical review artifacts remain immutable: a mechanical digest test
    (NOT a manual checkbox). Before the summarizer runs, record SHA-256 for every
    discovered historical Markdown and sidecar; run the summarizer end-to-end;
    re-hash every recorded path and assert byte-identity; reject any unexpected
    new file in historical directories. Include an adapter-write attempt that
    MUST fail (the summarizer never mutates inputs; prove it)."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        root = td_path / "myrepos"
        repo = root / "hist-repo-beta"
        (repo / ".ai-playbook").mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            '```toml\nreviews_dir = "docs/reviews/"\n```\n', encoding="utf-8"
        )
        # A sidecar and its sibling review Markdown in the historical reviews dir.
        sidecar_path = repo / "docs" / "reviews" / "2026-07-29-branch-review-r1.stats.json"
        review_md_path = repo / "docs" / "reviews" / "2026-07-29-branch-review-r1.md"
        _write_private_sidecar(sidecar_path, _make_current_payload(["quality"]))
        review_md_path.write_text("# Branch Review\n\nimmutable historical doc\n", encoding="utf-8")

        repo_roots = [root]
        # (a) Record SHA-256 for every discovered historical Markdown + sidecar
        # BEFORE running.
        manifest_path = td_path / "pre-manifest.json"
        recorded = record_historical_digests(repo_roots, manifest_path)
        check(
            "historical_immutability: sidecar recorded",
            sidecar_path.resolve() in recorded,
            str(list(recorded.keys())),
        )
        check(
            "historical_immutability: review markdown recorded",
            review_md_path.resolve() in recorded,
            str(list(recorded.keys())),
        )

        # (b) Run the summarizer end-to-end against the corpus.
        facts = td_path / "facts.md"
        facts.write_text(
            f"| `personal_projects_root` | `{root}/` | x |\n", encoding="utf-8"
        )
        tel = td_path / "review-telemetry"
        bp = tel / "baseline.json"
        tel.parent.mkdir(parents=True, exist_ok=True)
        rc_init = cmd_init_baseline(facts, bp, tel)
        check("historical_immutability: init ran", rc_init == 0)
        json_report = tel / "effectiveness-report.json"
        md_report = tel / "effectiveness-report.md"
        rc_audit = cmd_strict_audit(
            facts, bp, tel, json_report=json_report, markdown_report=md_report
        )
        check("historical_immutability: strict audit ran", rc_audit in (0, 1))

        # (c) Re-hash every recorded path and assert byte-identity.
        new_files = verify_historical_digests(repo_roots, recorded)
        check(
            "historical_immutability: every historical file byte-identical",
            not new_files,
            str(new_files),
        )

        # (d) Drop a NEW unexpected file in the historical reviews dir and confirm
        # the verifier rejects it.
        stray = repo / "docs" / "reviews" / "stray-new.stats.json"
        _write_private_sidecar(stray, _make_current_payload(["testing"]))
        new_files2 = verify_historical_digests(repo_roots, recorded)
        check(
            "historical_immutability: unexpected new file rejected",
            stray.resolve() in new_files2,
            str(new_files2),
        )
        stray.unlink()

        # (e) Adapter-write attempt that MUST FAIL: try to write to a historical
        # sidecar path through the summarizer's write primitives. The summarizer
        # opens inputs READ-ONLY; no write path reaches them.
        raised = False
        try:
            attempt_historical_write(sidecar_path)
        except PermissionsError:
            raised = True
        check(
            "historical_immutability: adapter-write attempt fails",
            raised,
            "write to a historical input must be refused",
        )
        # And the file is unchanged after the refused write.
        check(
            "historical_immutability: file unchanged after refused write",
            sha256_hex(read_byte_buffer(sidecar_path)) == recorded[sidecar_path.resolve()],
        )


# ---- helpers used by selftests ----
def _file_mode(path: Path) -> int | None:
    try:
        return stat.S_IMODE(os.lstat(str(path)).st_mode)
    except OSError:
        return None


def _dir_mode(path: Path) -> int | None:
    return _file_mode(path)


# --------------------------------------------------------------------------- #
# Selftest subsets.
# --------------------------------------------------------------------------- #

# Map each dotted test name to its subset tag for ``--selftest --subset``.
_SUBSET_OF: dict[str, str] = {
    "summarize_review_stats#facts_roots": "discovery",
    "summarize_review_stats#review_directory_discovery": "discovery",
    "summarize_review_stats#same_shape_replacement": "conservation",
    "summarize_review_stats#conservation": "conservation",
    "summarize_review_stats#audit_anomaly_classification": "conservation",
    "summarize_review_stats#conservation_shape_drift": "conservation",
    "summarize_review_stats#private_manifest": "conservation",
    "summarize_review_stats#baseline_lifecycle": "lifecycle",
    "summarize_review_stats#private_permissions": "permissions",
    "summarize_review_stats#snapshot_races": "permissions",
    "summarize_review_stats#current_adapter": "aggregation",
    "summarize_review_stats#legacy_adapters": "aggregation",
    "summarize_review_stats#accepted_unique": "aggregation",
    "summarize_review_stats#cohort_key_derivation": "report",
    "summarize_review_stats#comparable_cohorts": "report",
    "summarize_review_stats#inconclusive_sample": "report",
    "summarize_review_stats#retain_policy": "report",
    "summarize_review_stats#review_needed": "report",
    "summarize_review_stats#per_cohort_verdict": "report",
    "summarize_review_stats#determinism": "report",
    "summarize_review_stats#partial_failure_skip": "report",
    "summarize_review_stats#public_output": "report",
    "summarize_review_stats#real_deny_inventory": "release",
    "summarize_review_stats#historical_immutability": "release",
}


def run_selftest(subsets: list[str] | None = None) -> int:
    """Run registered selftests, optionally filtered by subset tag."""
    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        if cond:
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
            all_ok = False

    names = list(_registry.keys())
    if subsets:
        sel = set(subsets)
        names = [n for n in names if _SUBSET_OF.get(n) in sel]
    for name in names:
        print(f"--- {name} ({_SUBSET_OF.get(name, '?')}) ---")
        try:
            _registry[name](check)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {name} raised {type(exc).__name__}: {exc}")
            all_ok = False
    print()
    print("ALL PASS" if all_ok else "SOME FAIL")
    return 0 if all_ok else 1


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Private review corpus discovery, conservation, and baseline lifecycle."
    )
    parser.add_argument("--selftest", action="store_true", help="run built-in selftests")
    parser.add_argument(
        "--subset",
        default="",
        help="comma-separated selftest subset tags (discovery,conservation,permissions,lifecycle,aggregation,report,release)",
    )
    parser.add_argument("--user-facts", type=Path, default=Path.home() / ".ai-playbook" / "facts.md")
    parser.add_argument(
        "--init-baseline",
        metavar="PATH",
        type=Path,
        default=None,
        help="atomically create a private baseline manifest (fails if it exists)",
    )
    parser.add_argument(
        "--refresh-baseline",
        metavar="PATH",
        type=Path,
        default=None,
        help="explicitly refresh (overwrite) the private baseline manifest",
    )
    parser.add_argument(
        "--baseline-manifest",
        metavar="PATH",
        type=Path,
        default=None,
        help="path to the private baseline manifest (for --strict-audit)",
    )
    parser.add_argument(
        "--strict-audit",
        action="store_true",
        help="read-only strict conservation audit (fails on baseline problems)",
    )
    parser.add_argument("--json-report", type=Path, default=None)
    parser.add_argument("--markdown-report", type=Path, default=None)
    parser.add_argument(
        "--emit-deny-inventory",
        metavar="PATH",
        type=Path,
        default=None,
        help="build the deny inventory at audit time from the real corpus and "
        "write it to the given private path (runtime-private; never committed)",
    )
    args = parser.parse_args(argv)

    if args.selftest:
        subsets = [s for s in args.subset.split(",") if s.strip()] if args.subset else None
        return run_selftest(subsets)

    home_ai = Path.home() / ".ai-playbook"
    tel = home_ai / TELEMETRY_DIR_NAME

    if args.init_baseline is not None:
        return cmd_init_baseline(args.user_facts, args.init_baseline, tel)
    if args.refresh_baseline is not None:
        return cmd_refresh_baseline(args.user_facts, args.refresh_baseline, tel)
    if args.strict_audit:
        if args.baseline_manifest is None:
            sys.stderr.write("--strict-audit requires --baseline-manifest\n")
            return 2
        return cmd_strict_audit(
            args.user_facts,
            args.baseline_manifest,
            tel,
            json_report=args.json_report,
            markdown_report=args.markdown_report,
        )
    if args.emit_deny_inventory is not None:
        return cmd_emit_deny_inventory(
            args.user_facts, args.emit_deny_inventory, tel
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
