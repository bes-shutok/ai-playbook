#!/usr/bin/env python3
"""Private review corpus discovery, conservation, and baseline lifecycle.

Phase 2 review-effectiveness telemetry. Task 1 scope (this file): build the
private corpus discovery and conservation layer:

- Allowlisted facts-driven discovery (imports ``facts_paths``; never re-parses).
- SHA-256 inventory of every discovered sidecar into a private baseline.
- Private baseline lifecycle: atomic ``--init-baseline``, ``--strict-audit``
  (read-only over sidecar content; normalizes private-file modes to
  0600/0700, stderr warning if a tighten is refused), explicit
  ``--refresh-baseline``, with a transition table.
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

The ``--metrics`` mode is the review-corpus metrics pass: a read-only
aggregation of the discovered sidecars into per-loop, per-complexity-band
metrics (findings-per-round decay, ready-rate, cap-exhaustion share) with
aggregate-only JSON and Markdown outputs.

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

# Historical (pre-versioning) panel identity namespace: the lens-era agent
# names recorded by the Phase 1 cutover marker. Kept frozen so historical
# sidecar classification is never re-derived from today's contract (Design
# Invariant: versionless sidecars remain legacy compatibility inputs).
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

# The worker-ID namespace, taken from the validator's full-panel contract
# (validate_review_staging.DEFAULT_PANEL_WORKERS). Five-worker growth
# eligibility is expressed by these WORKER IDs; lens telemetry is derived
# separately from each panel row's ``lenses`` array and is never compared to
# worker IDs (worker identity and lens identity are distinct namespaces).
WORKER_PANEL_IDS = frozenset(vrs.DEFAULT_PANEL_WORKERS)

# Growth-eligible panel identities: the version-1 worker IDs plus the frozen
# historical namespace above (legacy history stays eligible; it is never
# re-classified by age).
GROWTH_ELIGIBLE_PANEL_IDS = FIVE_WORKER_PANEL_IDS | set(WORKER_PANEL_IDS)

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


@contextmanager
def _pinned_parent(parent: Path, refusal_text: str) -> Iterator[int]:
    """Pin ``parent`` as a dirfd for the caller's dirfd-relative operations.

    Opens the parent once with ``O_RDONLY | O_DIRECTORY | O_NOFOLLOW |
    O_CLOEXEC``. Symlink-indicating errnos (``ELOOP``/``ENOTDIR``) surface as
    ``PermissionsError(refusal_text)`` (per-caller contract); every other
    errno gets an accurate open-failure message (r2 F2). The fd is closed in
    a ``finally`` so ownership never duplicates at the call sites.

    The no-follow guarantee covers the parent itself: ``O_NOFOLLOW`` binds
    only to the final component of this open (the parent), so a symlink
    swapped onto the immediate parent is refused. Intermediate ancestors
    above the parent are resolved by path and keep the r2 sibling contract
    (accepted residual window, review r1 F1).
    """
    try:
        fd = os.open(
            str(parent),
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise PermissionsError(refusal_text) from exc
        raise PermissionsError(
            f"cannot open parent directory: {parent}: {exc}"
        ) from exc
    try:
        yield fd
    finally:
        os.close(fd)


def tighten_parent_ai_playbook(parent: Path) -> None:
    """Tighten ``~/.ai-playbook/`` (``parent``) to ``0700`` or refuse to run.

    If it is a real directory whose mode differs from ``0700``, reset it to
    ``0700``. If it is a symlink, refuse. Re-assert on every run. Kernel-grade:
    the parent is opened once with ``O_DIRECTORY | O_NOFOLLOW`` and both the
    mode read (``fstat``) and the tighten (``fchmod``) act on that fd, so a
    symlink swapped in after the pre-check cannot redirect the chmod.
    """
    _reject_symlink(parent)
    with _pinned_parent(parent, f"parent is not a directory: {parent}") as fd:
        st = os.fstat(fd)
        if not stat.S_ISDIR(st.st_mode):
            raise PermissionsError(f"parent is not a directory: {parent}")
        if stat.S_IMODE(st.st_mode) != 0o700:
            # Tighten. If the fchmod fails (e.g. read-only filesystem) the
            # OSError is translated to a hard failure (refuse to run).
            try:
                os.fchmod(fd, 0o700)
            except OSError as exc:
                raise PermissionsError(
                    f"cannot tighten parent {parent} to 0700: {exc}"
                ) from exc


def ensure_private_dir(path: Path) -> None:
    """Create ``path`` with ``0o700`` under a cleared umask, rejecting symlinks.

    Idempotent: if the dir exists as a real directory with mode ``0700`` it is
    left alone; if its mode differs from ``0700`` it is reset to ``0700``. Never
    create-then-chmod on the create path: the mode is set atomically by
    ``os.mkdir(..., 0o700, dir_fd=...)`` under a cleared umask. Kernel-grade:
    the parent is pinned with an ``O_DIRECTORY | O_NOFOLLOW`` dirfd and the
    final component is created/re-opened dirfd-relative with ``O_NOFOLLOW``,
    so the mode re-assert (fstat/fchmod) always acts on the pinned directory,
    never on a path string that a raced symlink could redirect.
    """
    _reject_symlink(path)
    _reject_symlink(path.parent)
    prev = os.umask(0o077)
    try:
        final_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        with _pinned_parent(
            path.parent, f"refusing symlinked parent: {path.parent}"
        ) as parent_fd:
            name = path.name
            try:
                os.mkdir(name, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                pass
            try:
                fd = os.open(name, final_flags, dir_fd=parent_fd)
            except OSError as exc:
                # ELOOP joins ENOTDIR/ENOENT: on Linux a raced symlink on
                # the final component fails this O_NOFOLLOW open with
                # ELOOP (darwin returns ENOTDIR); both must surface as the
                # friendly refusal, not a raw OSError traceback.
                if exc.errno in (errno.ENOTDIR, errno.ENOENT, errno.ELOOP):
                    raise PermissionsError(
                        f"private path is not a directory: {path}"
                    ) from exc
                raise
            try:
                st = os.fstat(fd)
                if not stat.S_ISDIR(st.st_mode):
                    raise PermissionsError(
                        f"private path is not a directory: {path}"
                    )
                # Re-assert mode on every run (fd-relative, symlink-proof).
                # A failed tighten is a hard failure (refuse to run),
                # translated like tighten_parent_ai_playbook (r3 F4).
                if stat.S_IMODE(st.st_mode) != 0o700:
                    try:
                        os.fchmod(fd, 0o700)
                    except OSError as exc:
                        raise PermissionsError(
                            f"cannot tighten private dir {path} to 0700: {exc}"
                        ) from exc
            finally:
                os.close(fd)
    finally:
        os.umask(prev)


def create_private_file_exclusive(path: Path, data: bytes) -> None:
    """Atomically create ``path`` with ``0o600`` and write ``data``.

    Uses ``os.open(O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW, 0o600, dir_fd=...)``
    under a parent pinned with ``O_DIRECTORY | O_NOFOLLOW``, then ``fdopen``
    under a cleared umask. Fails if the file already exists
    (``--init-baseline``). Never create-then-chmod. Rejects symlink targets;
    the dirfd-relative open also closes the parent-swap TOCTOU window.
    """
    _reject_symlink(path)
    _reject_symlink(path.parent)
    prev = os.umask(0o077)
    try:
        with _pinned_parent(
            path.parent, f"refusing symlinked parent: {path.parent}"
        ) as parent_fd:
            flags = (
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
                | os.O_NOFOLLOW
                | os.O_CLOEXEC
            )
            try:
                fd = os.open(path.name, flags, 0o600, dir_fd=parent_fd)
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


def _open_pinned_read(path: Path, parent_fd: int, err_what: str) -> int:
    """Open ``path``'s final component dirfd-relative for reading.

    Shared by ``read_private_file`` and ``read_byte_buffer``: opens the
    final component with ``O_RDONLY | O_NOFOLLOW | O_CLOEXEC`` relative
    to ``parent_fd`` and owns the single symlink-refusal errno contract
    (ELOOP/ENOTDIR -> ``PermissionsError``); any other ``OSError`` is
    re-raised as ``type(exc)(f"{err_what}: {path}: {exc}")``. Returns
    the raw fd (close-on-failure semantics stay with the caller).
    """
    try:
        return os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise PermissionsError(
                f"refusing to follow symlink target: {path}"
            ) from exc
        raise type(exc)(f"{err_what}: {path}: {exc}") from exc


def read_private_file(path: Path) -> bytes:
    """Read ``path`` bytes, rejecting symlink targets.

    Kernel-grade: the parent directory is pinned with an
    ``O_DIRECTORY | O_NOFOLLOW`` dirfd (via ``_pinned_parent``) and the
    final component is opened dirfd-relative with ``O_NOFOLLOW``, so a
    symlink swapped onto the parent (which the target-only
    ``_reject_symlink`` pre-check never covered) cannot redirect the
    read, and a symlink swapped onto the file itself fails
    the open (ELOOP/ENOTDIR) instead of being followed; both are
    translated to ``PermissionsError``. The parent-open guarantee and
    its intermediate-ancestor residual are documented on
    ``_pinned_parent``.
    A file whose mode differs from 0600 is reset to 0600 on the read path
    (best-effort fchmod on the fd), mirroring the directory helpers.
    """
    _reject_symlink(path)
    with _pinned_parent(
        path.parent, f"refusing symlinked parent: {path.parent}"
    ) as parent_fd:
        fd = _open_pinned_read(path, parent_fd, "cannot read private file")
    # Re-assert mode on every run (fd-based, mirroring the directory
    # helpers): a legacy or restored file with a non-canonical mode is
    # reset on the read path, never via a path-string chmod. Advisory
    # (r2 F1): a refused fchmod (EROFS/EPERM) must NOT fail the read
    # (stderr note only, never in any report), and the fd is closed on
    # every failure path before fdopen takes ownership.
    try:
        st = os.fstat(fd)
        if stat.S_IMODE(st.st_mode) != 0o600:
            try:
                os.fchmod(fd, 0o600)
            except OSError as exc:
                sys.stderr.write(
                    f"warning: could not re-tighten mode of {path}"
                    f" to 0600: {exc}\n"
                )
        fh = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    with fh:
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
        # The kernel symlink-refusal flag makes open fail with ELOOP on a
        # symlinked final component, closing the pre-check-to-open race
        # window; close-on-exec keeps the lock fd out of child processes.
        # A raced ELOOP is translated to a friendly PermissionsError naming
        # the lock path instead of surfacing a raw OSError traceback.
        try:
            fd = os.open(
                str(lock_path),
                os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
            )
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise PermissionsError(
                    f"telemetry lock path is a symlink "
                    f"(possible tampering): {lock_path}"
                ) from exc
            raise
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
    """Read ``path`` ONCE into an immutable byte buffer (digest+parse source).

    Kernel-grade like ``read_private_file``: the parent directory is
    pinned with an ``O_DIRECTORY | O_NOFOLLOW`` dirfd (via
    ``_pinned_parent``) and the final component is opened dirfd-relative
    with ``O_NOFOLLOW``, so a symlink swapped onto the parent cannot
    redirect the read and a symlink swapped onto the file itself fails
    the open (ELOOP/ENOTDIR) instead of being followed. The read is pure: no mode re-tightening on the
    read path (unlike ``read_private_file``, which resets to 0600);
    sidecar modes are managed at write time. Inherits
    ``_pinned_parent``'s intermediate-ancestor residual contract.
    """
    _reject_symlink(path)
    with _pinned_parent(
        path.parent, f"refusing symlinked parent: {path.parent}"
    ) as parent_fd:
        fd = _open_pinned_read(path, parent_fd, "cannot read byte buffer")
        try:
            fh = os.fdopen(fd, "rb")
        except BaseException:
            os.close(fd)
            raise
        with fh:
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


def satisfies_five_worker_set(payload: dict, eligible: frozenset[str]) -> bool:
    """True iff the sidecar's panel identities satisfy the five-worker set.

    "Satisfy" means the panel identity set is non-empty and is a subset of the
    caller-supplied eligible identity family. The family is REQUIRED (r3 F8:
    a default union was a production-dead widening path; a future caller
    omitting it would silently apply the legacy union to version-1 records).
    ``classify_for_conservation`` passes its label-scoped set — version-1
    records must satisfy ``WORKER_PANEL_IDS`` only; the frozen growth-eligible
    union applies to versionless legacy records. Lens telemetry is never
    consulted here; worker IDs and lens IDs are distinct namespaces.
    """
    names = panel_identity_set(payload)
    if not names:
        return False
    return names.issubset(eligible)


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
    digest: str = "",
) -> tuple[str, list[str]]:
    """Classify one discovered sidecar into exactly one ledger class.

    ``digest`` is the sidecar's content digest computed ONCE by the
    conservation run over the already-read immutable byte buffer (Design
    Invariant 9) and shared with the caller's dedup ledger (r5 F6: one
    derivation site for both classification and dedup, so the two can never
    desynchronize). The file is NEVER read here (r4 F2): re-reading opened a
    mixed-version window where the payload was parsed from the old bytes
    while the digest came from new bytes, misclassifying baseline members as
    same-shape replacements and skewing duplicate detection.

    Returns ``(class, audit_signals)``. The classification order:

    1. ``unreadable`` if the buffer did not parse (collapsed malformed +
       unsupported). An explicit-but-unsupported ``schema_version`` also
       ledgers ``unreadable`` with a named signal; this disposition is
       checked BEFORE duplicate (step 2), so an unsupported-version sidecar
       can never ledger as ``duplicate`` or ``audit-anomaly``.
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
    # r5 F7: the schema label is classified ONCE and held for both the
    # unsupported-version hoist below and the growth-shape derivation in
    # steps 5-7 (pre-fix the classifier ran twice on the unchanged payload).
    # r4 F2: the digest arrives precomputed from the held immutable buffer
    # (single derivation, r5 F6); the file is never re-read here.
    schema_label = vrs.classify_sidecar_schema(payload)

    # 1. unreadable
    if payload is None:
        cls = "unreadable"
        return cls, signals

    # 1.5 unsupported schema_version (F7): an explicit-but-unsupported
    # ``schema_version`` is rejected by the validator outright; it is never
    # legacy compatibility input. This disposition is UNCONDITIONAL, so it
    # runs before the duplicate / same-path-digest / panel / schema mismatch
    # branches: such a sidecar always ledgers ``unreadable`` with the named
    # signal (never ``duplicate`` or ``audit-anomaly``).
    #
    # Documented ledger consequence of the hoist (r3 F9): an unchanged
    # baseline snapshot member that carries an unsupported ``schema_version``
    # migrates from ``baseline`` to ``unreadable`` (the snapshot comparison in
    # steps 3-4 never runs for it), silently shrinking the baseline side of
    # cohorts and potentially flipping an evaluable cohort to inconclusive.
    # This erosion is accepted deliberately: an unsupported version is never
    # compatibility input, and treating it as unreadable surfaces it in the
    # audit signal instead of keeping a contract-violating record in the
    # baseline cohort. Re-pin the baseline after resolving any unsupported
    # sidecar so cohort counts recover.
    if schema_label == "unsupported":
        signals.append(
            f"unsupported schema_version {payload.get('schema_version')!r}; "
            "rejected by the validator contract"
        )
        return "unreadable", signals

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
        # panel identity NOT in the marker's family (the recorded cutover
        # identities plus the validator-contract worker IDs). A growth sidecar
        # launching a strict subset of the family does NOT disagree; only an
        # out-of-family identity is an anomaly.
        declared_panel = panel_identity_set(payload)
        marker_panel = set(marker.get("panel_identities", []))
        extra = declared_panel - (marker_panel | WORKER_PANEL_IDS)
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

    # 5/6/7. not in snapshot: classify by shape. The growth-branch shape comes
    # from the validator's exported CURRENT-shape label FAMILY
    # (``vrs.CURRENT_SHAPE_LABELS``), which deliberately includes
    # ``legacy-worker-shaped`` (r3 F1: deriving it from the aggregation
    # adapter's shape made the growth branch unreachable for versionless
    # worker-shaped sidecars, silently re-classifying them from growth to
    # legacy). The aggregation adapter keeps its own routing carve-out for
    # ``legacy-worker-shaped`` records; the growth ledger's shape authority is
    # the schema label family, so versionless worker-shaped history stays
    # growth-eligible while its aggregation still routes through the
    # compatibility adapter. The label itself is the one hoisted near the top
    # of this function (r5 F7: single classification call).
    # An explicit-but-unsupported schema_version was already ledgered
    # ``unreadable`` with a named signal above (unconditional disposition).
    growth_shaped = schema_label in vrs.CURRENT_SHAPE_LABELS
    # Growth eligibility is scoped by schema label (Design Invariant: current
    # records compare WORKER IDs only). Version-1 records must satisfy the
    # worker-ID set; versionless legacy records keep the frozen union (history
    # stays eligible, never re-derived from today's contract). The scoped rule
    # is evaluated by the SAME exported helper the selftest asserts (no inline
    # duplicate predicate).
    eligible_ids = (
        WORKER_PANEL_IDS
        if schema_label == "current-v1"
        else GROWTH_ELIGIBLE_PANEL_IDS
    )
    if growth_shaped and satisfies_five_worker_set(payload, eligible_ids):
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
        # r5 F6: the content digest is computed ONCE per sidecar and shared
        # with the classifier (classification, duplicate detection, and the
        # seen-digests ledger all use one derivation over the same buffer).
        digest = sha256_hex(buf) if buf else ""
        cls, signals = classify_for_conservation(
            sidecar, payload, reason, baseline, seen_digests, digest=digest
        )
        ledger[cls].append(sidecar)
        if signals:
            audit[str(sidecar)] = signals
        if digest and cls != "duplicate":
            seen_digests[digest] = sidecar

    return ledger, audit


# --------------------------------------------------------------------------- #
# Cost and finding-effectiveness aggregation (Task 2).
# --------------------------------------------------------------------------- #
#
# Token telemetry: token usage IS read when present, still never estimated.
# A sidecar's optional top-level ``usage`` record (adapter + provenance +
# totals + by_agent_kind, produced by scripts/review_usage_capture.py) is
# aggregated into observed-token totals and usage coverage over post-cutover
# sidecars (USAGE_CUTOVER_DATE below). Values are sums of observed provider
# counts only: nothing is invented, imputed, or estimated. A malformed usage
# record (bare string, missing ``totals``) is treated as absent, mirroring the
# validator's tolerance.
#
# KNOWN LIMITATION: the observed-token totals SUM the usage records of all
# post-cutover sidecars, and consecutive rounds' capture windows OVERLAP
# (6-hour look-back over the same sessions), so the same session's lifetime
# counters are counted once per capturing sidecar — the line is a sum of
# sidecar usage records over overlapping windows, NOT unique spend.

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


# Versionless worker-shaped compatibility records keep their worker, lens,
# finding, and triage metrics through the compatibility aggregation adapter.
LEGACY_WORKER_SHAPE_LABEL = "legacy-worker-shaped"

# Schema-classification labels that aggregate through the current (per-worker
# panel) adapter: explicit version-1 records plus the pre-version records that
# already carried the current shape (``legacy-panel-mode``). Derived from the
# validator's exported label set minus the one documented carve-out
# (``legacy-worker-shaped`` routes through the compatibility adapter), so the
# summarizer never hand-copies the label set (F5).
CURRENT_SHAPE_SCHEMA_LABELS = vrs.CURRENT_SHAPE_LABELS - {
    LEGACY_WORKER_SHAPE_LABEL
}


def adapter_is_current(payload: dict) -> bool:
    """Classify a sidecar payload as current-shaped vs legacy for AGGREGATION
    routing, delegating to the validator's exported schema classifier
    (``validate_review_staging.classify_sidecar_schema``). The summarizer
    never re-derives the predicate; structural agreement with the validator's
    exported label family is pinned by the legacy_adapters selftest (one
    fixture per schema label plus a set-derivation assertion)."""
    return vrs.classify_sidecar_schema(payload) in CURRENT_SHAPE_SCHEMA_LABELS


def _len_container(value) -> int:
    """len() for the len-derived container counts (discard / calibration /
    overflow). Absent, explicit JSON null, and mistyped values (including
    strings — a string is a mistyped container here, not a countable one) all
    yield 0 instead of a TypeError crash (r4 F1): one bad historical sidecar
    must never abort the whole strict-audit report (partial-failure design).
    The validator's type gates reject mistyped containers on current shapes;
    this helper keeps aggregation crash-safe for whatever still reaches it."""
    return len(value) if isinstance(value, (list, dict)) else 0


# Usage-coverage cutover: sidecars whose ``date`` is on/after this day are
# post-cutover; a sidecar missing ``date`` counts as post-cutover
# (conservative: a date-less sidecar without usage can only suppress coverage
# downward, never inflate it). Pre-cutover sidecars are excluded from the
# coverage denominator entirely and their token data is never read.
USAGE_CUTOVER_DATE = "2026-09-06"

# Observed-token keys read from a usage record's ``totals`` block (sums of
# observed provider counts; never estimated).
_USAGE_TOTAL_KEYS = (
    "input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "computed_total_tokens",
)

# Token cost stays labeled supplementary until observed-token coverage over
# post-cutover sidecars reaches this fraction; at/above it the label drops.
USAGE_COVERAGE_DECISION_THRESHOLD = 0.70


def _usage_totals_from_payload(payload: dict) -> dict | None:
    """Return observed token totals from a usage record, or None when absent.

    Tolerance mirrors the validator's: a malformed record (bare string,
    missing or mistyped ``totals``) is treated as absent rather than an error.
    """
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    totals = usage.get("totals")
    if not isinstance(totals, dict):
        return None
    return {key: _coerce_int(totals.get(key)) for key in _USAGE_TOTAL_KEYS}


def _is_post_cutover(payload: dict) -> bool:
    """Classify a sidecar as post-cutover for usage coverage.

    ``payload["date"] >= USAGE_CUTOVER_DATE`` (ISO dates compare
    lexicographically); a missing or non-string ``date`` counts as
    post-cutover (conservative; see USAGE_CUTOVER_DATE above).
    """
    date = payload.get("date")
    if not isinstance(date, str):
        return True
    return date >= USAGE_CUTOVER_DATE


def aggregate_current(payload: dict) -> dict:
    """Normalize a current (five-worker) sidecar payload to aggregation totals.

    Reads worker and lens launches, dedup, discard, calibration, overflow, and
    triage totals. Observed token totals are NOT attached here: usage-record
    extraction lives solely in ``build_effectiveness_report`` via
    ``_usage_totals_from_payload`` (single path; the adapter seam has no
    production usage consumer). ``raw_findings`` is
    read from ``counts.raw_findings`` (falling back to ``counts.raw_total``
    for the minority of current sidecars that carry it; both are read by
    trying each key, matching the plan's artifact-size-bucket derivation
    rule).
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
        "discard_count": _len_container(payload.get("discarded")),
        "calibration_count": _len_container(payload.get("severity_calibration")),
        "overflow_count": _len_container(payload.get("overflow")),
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
        "discard_count": _len_container(payload.get("discarded")),
        "calibration_count": _len_container(payload.get("severity_calibration")),
        "overflow_count": _len_container(payload.get("overflow")),
        "triage": _triage_from_findings(findings),
        "severity": _severity_from_findings(findings),
    }


def aggregate_legacy_worker_compat(payload: dict) -> dict:
    """Compatibility adapter for versionless worker-shaped legacy records.

    These records predate ``schema_version`` but still carry per-worker panel
    rows with lens arrays. They classify legacy (the version-1 contract never
    applies), yet their worker, lens, finding, and triage metrics are
    preserved by reusing the current adapter's panel-aware aggregation while
    reporting the legacy contract in ``schema``.
    """
    norm = aggregate_current(payload)
    norm["schema"] = "legacy"
    return norm


def record_kind_of(payload: dict) -> str | None:
    """Return the payload's ``record_kind`` value for a POST-FENCE record, else
    None. The kind fence is the validator's two-surface classifier
    (``record_kind_fence``, the public alias, imported from
    ``validate_review_staging``; the fence constant is never re-pinned here,
    r1 F8, and the summarizer never imports a private symbol, r2 overflow
    D5): a record whose sidecar ``date`` classifies post-fence must declare
    a kind; pre-fence or undated records are accepted-legacy and exempt.
    The staging filename surface is unavailable at aggregation time, so it
    passes as ``None`` and classifies ``undated`` (which never grants an
    exemption by itself).
    """
    fence = vrs.record_kind_fence(None, payload.get("date"))
    if fence["sidecar_class"] != "post-fence":
        return None
    kind = payload.get("record_kind")
    return kind if isinstance(kind, str) else None


def is_non_canonical_record(payload: dict) -> bool:
    """True iff a POST-FENCE record declares a non-canonical ``record_kind``
    (reconciliation, worker-evidence, legacy-import; the enum is owned by
    ``review-staging`` via the validator). Such a record never folds its
    findings into the panel-tuning aggregate and is counted separately in the
    report output. A pre-fence record or a record without ``record_kind``
    aggregates as today (grandfathered)."""
    kind = record_kind_of(payload)
    return kind is not None and kind != "canonical"


def aggregate_sidecar(payload: dict) -> dict:
    """Classify and normalize a sidecar payload via the validator's exported
    schema classifier (the single classification authority; classified ONCE)
    and choose the aggregation adapter from the returned label:

    - ``current-v1`` / ``legacy-panel-mode`` -> ``aggregate_current``
    - ``legacy-worker-shaped`` -> compatibility adapter (worker/lens metrics
      preserved, legacy contract reported)
    - any other legacy label -> generic legacy normalization

    Canonical-only aggregation: a post-fence record declaring a non-canonical
    ``record_kind`` contributes zero finding-bearing totals (raw, staged,
    dedup, discard, calibration, overflow, triage, severity) and launch
    telemetry stays observed; the report counts the record separately from
    ``is_non_canonical_record`` at report-build time (r1 F17: the normalized
    dict itself carries no record_kind/non_canonical keys because no consumer
    reads them). Pre-fence or kindless records aggregate as today.
    """
    label = vrs.classify_sidecar_schema(payload)
    if label == LEGACY_WORKER_SHAPE_LABEL:
        norm = aggregate_legacy_worker_compat(payload)
    elif label in CURRENT_SHAPE_SCHEMA_LABELS:
        norm = aggregate_current(payload)
    else:
        norm = aggregate_legacy(payload)
    if is_non_canonical_record(payload):
        norm["raw_findings"] = 0
        norm["staged_findings"] = 0
        norm["dedup_count"] = 0
        norm["discard_count"] = 0
        norm["calibration_count"] = 0
        norm["overflow_count"] = 0
        norm["triage"] = {key: 0 for key in norm["triage"]}
        norm["severity"] = {key: 0 for key in norm["severity"]}
    return norm


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
    # r4 F5: a ZERO baseline accepted yield (the typical raw-only legacy
    # baseline whose findings carry no triage values) is an unmeasurable
    # floor, not a failed guardrail: growth-positive vs zero-baseline is an
    # improvement, and auto-failing it systematically verdict-ed every
    # improved cohort over a legacy baseline as "review needed". The guardrail
    # passes with an explicit unmeasurable note instead; both-zero stays
    # no-change.
    accepted_unmeasurable_reason: str | None = None
    if baseline_accepted is not None and growth_accepted is not None:
        if baseline_accepted > 0:
            accepted_change = (growth_accepted - baseline_accepted) / baseline_accepted
        elif growth_accepted == 0:
            accepted_change = 0.0
        else:
            accepted_change = None
            accepted_unmeasurable_reason = (
                "baseline accepted yield is zero (raw-only baseline); "
                "accepted-change guardrail not measurable"
            )
    else:
        accepted_change = None
    checks["accepted_change"] = accepted_change
    accepted_ok = (
        True
        if accepted_unmeasurable_reason is not None
        else accepted_change is not None
        and accepted_change >= -ACCEPTED_CHANGE_GUARDRAIL
    )

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
            # None except when the accepted-change guardrail was unmeasurable
            # (zero-baseline raw-only history, r4 F5): carries the explicit
            # reason so the pass-with-note cannot be mistaken for a measured
            # pass.
            "accepted_change_unmeasurable_reason": accepted_unmeasurable_reason,
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

    A post-fence record declaring a non-canonical ``record_kind`` never enters a
    cohort bucket (its payload-derived metrics must not feed panel tuning); the
    report counts it separately in availability instead.
    """
    cohorts: dict[tuple[str, str, str, str], dict[str, list[tuple[dict, dict]]]] = {}
    for period, payload in classified_sidecars:
        if is_non_canonical_record(payload):
            continue
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
        # Post-fence records declaring a non-canonical record_kind: excluded
        # from the canonical-only aggregate, counted on this separate line.
        "non_canonical_records": sum(
            1 for _period, payload in clean if is_non_canonical_record(payload)
        ),
    }

    # Observed token usage aggregation (never estimated): sum the observed
    # ``totals`` blocks of POST-CUTOVER sidecars carrying a well-formed usage
    # record, and compute coverage as the fraction of post-cutover sidecars
    # carrying one. Pre-cutover sidecars are excluded from BOTH the numerator
    # and the denominator (their token data is never read); a post-cutover
    # sidecar without usage stays in the denominator (the denominator is NOT
    # "sidecars with usage").
    observed_token_totals = {key: 0 for key in _USAGE_TOTAL_KEYS}
    sidecars_with_usage = 0
    post_cutover_sidecars = 0
    for _period, payload in clean:
        if not _is_post_cutover(payload):
            continue
        post_cutover_sidecars += 1
        observed = _usage_totals_from_payload(payload)
        if observed is None:
            continue
        sidecars_with_usage += 1
        for key in _USAGE_TOTAL_KEYS:
            observed_token_totals[key] += observed[key]
    coverage = (
        sidecars_with_usage / post_cutover_sidecars
        if post_cutover_sidecars
        else None
    )
    usage_coverage = {
        "sidecars_with_usage": sidecars_with_usage,
        "post_cutover_sidecars": post_cutover_sidecars,
        "coverage": coverage,
        # Supplementary until observed-token coverage over post-cutover
        # sidecars reaches the threshold (unknown coverage stays
        # supplementary); no branch reads pre-cutover token data.
        "token_cost_supplementary": coverage is None
        or coverage < USAGE_COVERAGE_DECISION_THRESHOLD,
    }
    return {
        "overall_verdict": overall_verdict(verdicts),
        "availability": availability_counts,
        "observed_token_totals": observed_token_totals,
        "usage_coverage": usage_coverage,
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
    # Separate non-canonical count line, only when non-zero so the normal
    # (all-canonical) markdown stays byte-identical (determinism selftest).
    if avail.get("non_canonical_records"):
        lines.append(
            "Non-canonical records excluded from aggregation: "
            f"{avail['non_canonical_records']}"
        )
    lines.append("")
    # Observed token usage (never estimated): totals are sums of observed
    # usage records on post-cutover sidecars; coverage is the fraction of
    # post-cutover sidecars carrying one. KNOWN LIMITATION: capture windows
    # overlap across a round's sidecars, so the same sessions' records are
    # summed repeatedly — this is NOT unique spend. Token cost stays labeled
    # supplementary until coverage reaches the decision threshold.
    tok = report["observed_token_totals"]
    lines.append(
        "Observed token totals (sum of sidecar usage records over "
        "overlapping capture windows; not unique spend): "
        f"input={tok['input_tokens']}, output={tok['output_tokens']}, "
        f"reasoning={tok['reasoning_tokens']}, "
        f"cache_creation={tok['cache_creation_input_tokens']}, "
        f"cache_read={tok['cache_read_input_tokens']}, "
        f"computed_total={tok['computed_total_tokens']}"
    )
    cov = report["usage_coverage"]
    if cov["post_cutover_sidecars"] == 0:
        coverage_text = (
            "Usage coverage: no post-cutover sidecars yet "
            "(coverage unknown); token cost: supplementary"
        )
    else:
        coverage_text = (
            f"Usage coverage: {cov['sidecars_with_usage']}/"
            f"{cov['post_cutover_sidecars']} post-cutover sidecars carry usage "
            f"({cov['coverage']:.0%})"
        )
        if cov["token_cost_supplementary"]:
            coverage_text += "; token cost: supplementary"
    lines.append(coverage_text)
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
    attempt_observer: Callable[[dict[Path, bytes]], None] | None = None,
) -> int:
    """Recheck each input's on-disk generation against the buffer before publish.

    On the success path every published digest matches the byte buffer used for
    parsing. If an input changed between the buffer read and the recheck, retry
    up to ``retries`` times (re-reading the buffer); after that fail publication
    rather than publish a mixed-version snapshot. The caller's ``publish_fn``
    is invoked once per attempt after the recheck passes.

    Load-bearing contract: on retry the ``buffers`` dict is refreshed IN PLACE
    (existing keys re-read from disk) before ``publish_fn`` is invoked. A
    ``publish_fn`` that writes bytes serialized before the recheck, ignoring
    the refreshed ``buffers``, publishes a stale snapshot that still passes
    this gate. Every caller MUST derive its published payload content from
    the current ``buffers`` contents at invocation time (see the cohort
    paragraph below for the one exception).

    Cohort membership is the caller's concern and may be pinned to a
    pre-publish ledger or snapshot (as ``cmd_strict_audit`` does): only
    payload content must follow the refreshed buffers. Consequently a
    caller that ignores the returned attempt count keeps its ledger-derived
    summary and exit code pinned to the pre-publish ledger, which may lag
    a retry-absorbed mutation, while the published report is rebuilt from
    the refreshed buffers; callers that consume the attempt count (as
    ``cmd_strict_audit`` does for its summary and exit code) recompute
    ledger-derived state over the refreshed buffers. Cohort membership
    itself stays ledger-pinned. New callers must pin the freshness
    contract with a
    selftest fixture modeled on the ``strict_audit_stale_snapshot`` family;
    this gate cannot observe what ``publish_fn`` serialized.

    ``attempt_observer`` is informational only: invoked after each in-place
    buffer refresh with a snapshot (shallow copy) of the refreshed buffers,
    it lets a caller track per-attempt parse state that the single final
    ``publish_fn`` invocation cannot observe (as ``cmd_strict_audit`` does
    for window-aware chronicity). Residual: transient parse states that
    keep the byte size equal and are visible only to a recheck digest read
    (repair and re-break of equal-size content between two refreshes) are
    unobservable at the refresh site; this accepted residual is analogous
    to ``_pinned_parent``'s documented intermediate-ancestor residual.

    Returns the attempt count: ``1`` when the first recheck passed (no
    retry), ``N+1`` after ``N`` absorbed retries. Callers use this signal
    to detect a retry-absorbed mutation and recompute ledger-derived state
    over the refreshed buffers (as ``cmd_strict_audit`` does for its
    ``replaced`` set); the ``classes=`` ledger summary stays ledger-pinned.
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
            return attempt
        if attempt > retries:
            raise PublishRace(
                f"input changed between read and publish after {retries} retries"
            )
        # Re-read buffers and retry.
        for path in list(buffers.keys()):
            buffers[path] = read_byte_buffer(path)
        if attempt_observer is not None:
            # Shallow copy: the observer must not mutate the live buffers
            # the recheck loop depends on.
            attempt_observer(dict(buffers))


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
    """Atomically overwrite ``path`` (0o600) via temp file + rename.

    Kernel-grade: the parent is pinned with an ``O_DIRECTORY | O_NOFOLLOW``
    dirfd; the temp file is created dirfd-relative with
    ``O_CREAT | O_EXCL | O_NOFOLLOW`` at ``0600`` (never create-then-chmod)
    and replaced into place with dirfd-relative ``os.replace``, so neither the
    write nor the cleanup can be redirected by a symlink swapped into the
    parent path after the pre-check. Rename-over-symlink at the target is
    accepted-by-design (r2 F10): the write lands in the pinned parent and the
    symlink is replaced, never followed.
    """
    _reject_symlink(path)
    _reject_symlink(path.parent)
    prev = os.umask(0o077)
    try:
        with _pinned_parent(
            path.parent, f"refusing symlinked parent: {path.parent}"
        ) as parent_fd:
            target_name = path.name
            create_flags = (
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
                | os.O_NOFOLLOW
                | os.O_CLOEXEC
            )
            # mkstemp cannot create dirfd-relative, so the temp name is minted
            # here: pid + urandom keeps it unguessable; the bounded retry
            # below guards a name clash.
            tmp_base = f".baseline-{os.getpid()}-{os.urandom(4).hex()}"
            tmp_name = tmp_base
            counter = 0
            while True:
                try:
                    tmp_fd = os.open(
                        tmp_name, create_flags, 0o600, dir_fd=parent_fd
                    )
                    break
                except FileExistsError:
                    counter += 1
                    if counter > 100:
                        raise
                    tmp_name = f"{tmp_base}-{counter}"
            try:
                with os.fdopen(tmp_fd, "wb") as fh:
                    fh.write(data)
                os.replace(
                    tmp_name,
                    target_name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                )
            except BaseException:
                try:
                    os.unlink(tmp_name, dir_fd=parent_fd)
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
    """``--strict-audit``: read-only over sidecar content; normalizes
    private-file modes to 0600/0700 (stderr warning if a tighten is refused);
    fail when baseline missing/unreadable/replaced/mismatched. Runs
    conservation classification and reports."""
    tighten_parent_ai_playbook(telemetry_dir.parent)
    with telemetry_lock(telemetry_dir):
        if not baseline_path.is_file():
            raise BaselineMissing(f"baseline missing: {baseline_path}")
        baseline = load_baseline(baseline_path)  # raises BaselineMissing if unreadable
        repo_roots = _roots_from_facts(user_facts)
        sidecars = discover_sidecars(repo_roots)
        buffers = {s: read_byte_buffer(s) for s in sidecars}
        ledger, audit = run_conservation(sidecars, buffers, baseline)

        # Strict audit: detect replacement/mismatch. One local helper drives
        # both the pre-race and the post-refresh computations (a verbatim
        # second copy would drift after a one-sided edit).
        snapshot_by_path = {
            e["path"]: e for e in baseline.get("sidecars", [])
        }

        def _replaced_of(bufs: dict) -> list[str]:
            replaced_paths: list[str] = []
            for sidecar in sidecars:
                snap = snapshot_by_path.get(str(sidecar))
                if snap is not None and snap.get("sha256") != sha256_hex(
                    bufs[sidecar]
                ):
                    replaced_paths.append(str(sidecar))
            return replaced_paths

        def _audit_of(bufs: dict) -> dict[str, list[str]]:
            # Same conservation pass as the pre-race run at the top of the
            # command, over caller-supplied buffers (r2 F3): the retry path
            # re-derives the audit signals from the refreshed bytes.
            _, audit_signals = run_conservation(sidecars, bufs, baseline)
            return audit_signals

        replaced = _replaced_of(buffers)

        # Build the effectiveness report over the classified corpus. Period
        # assignment: snapshot members (ledger baseline) are ``baseline``; growth
        # sidecars are ``growth``. Legacy/audit-anomaly/unreadable/duplicate are
        # excluded from cohort comparison (no period assigned). Panel mode is not
        # a cohort key, so a baseline review and a growth review that differ only
        # in panel mode land in the same comparable cohort.
        # Cohort membership contract: see the ``publish_with_recheck`` docstring.
        snapshot_paths = {
            entry["path"] for entry in baseline.get("sidecars", [])
        }
        def _classify_current() -> tuple[list[tuple[str, dict]], set[Path]]:
            classified: list[tuple[str, dict]] = []
            unparseable: set[Path] = set()
            for sidecar in sidecars:
                payload, _ = parse_payload(buffers[sidecar])
                if payload is None:
                    unparseable.add(sidecar)
                    continue
                if str(sidecar) in snapshot_paths:
                    classified.append(("baseline", payload))
                elif "growth" in ledger and sidecar in ledger["growth"]:
                    classified.append(("growth", payload))
            return classified, unparseable

        # Window-aware chronicity: a sidecar is chronic only when both
        # conditions hold: it is ledger-unreadable AND it was never
        # parseable at any observed point of the retry window (each
        # refresh snapshot plus the final-attempt state unioned inside
        # ``_publish``). A chronic sidecar repaired and re-broken inside
        # the window is retry-induced. Exit code, published report, and
        # ledger stay unaffected (plan 2026-09-06 item 3 design
        # invariant).
        ever_parseable: set[Path] = set()

        def _parseable(bufs: dict) -> set:
            # Single definition of "parseable at an observed point" (review
            # r1 F4): both the attempt observer and the publish gate's
            # final-attempt union compute the predicate here, so the
            # chronicity rule cannot drift between two idioms.
            return {
                p
                for p, buf in bufs.items()
                if parse_payload(buf)[0] is not None
            }

        def _observe_attempt(refreshed: dict[Path, bytes]) -> None:
            ever_parseable.update(_parseable(refreshed))

        def _publish() -> None:
            classified, unparseable_now = _classify_current()
            report = build_effectiveness_report(classified)
            # Operability pointer: surface the malformed-skip count from the
            # rebuilt report and the retry-induced unparseable drop delta on
            # stderr; paths stay private (not emitted). Set semantics: a
            # sidecar unparseable at publish is excluded from the
            # retry-delta only when it is ledger-unreadable AND never
            # parseable at any observed point of the window
            # (``ever_parseable``, which unions every refresh snapshot
            # the ``attempt_observer`` saw plus this final-attempt
            # parseable subset); a ledger-parseable sidecar broken
            # during the window counts as a fresh drop regardless of
            # ``ever_parseable`` membership. The earlier count
            # subtraction masked the repaired-chronic-plus-fresh-drop
            # window (backlog origin item 3): a repaired chronic sidecar
            # and a fresh drop cancel out numerically while the set
            # difference still catches the fresh drop. Chronic sidecars
            # stay visible via the ledger-pinned classes= summary.
            skipped = report.get("availability", {}).get("skipped_malformed", 0)
            ever_parseable.update(_parseable(buffers))
            chronic = set(ledger["unreadable"]) - ever_parseable
            retry_drops = unparseable_now - chronic
            delta = len(retry_drops)
            if skipped or retry_drops:
                notes = []
                if skipped:
                    notes.append(f"skipped {skipped} malformed sidecar(s)")
                if retry_drops:
                    notes.append(
                        f"dropped {delta} unparseable sidecar(s) (retry-induced)"
                    )
                # The report pointer names the malformed-skip counter only;
                # parse-drops never reach the report, so a drop-only note
                # stands alone.
                pointer = (
                    "; see availability.skipped_malformed in the report"
                    if skipped
                    else ""
                )
                sys.stderr.write(
                    "strict audit: " + "; ".join(notes) + pointer + "\n"
                )
            report_bytes = serialize_effectiveness_json(report)
            markdown_bytes = serialize_effectiveness_markdown(report)
            if json_report is not None:
                _atomic_write_private(json_report, report_bytes)
            if markdown_report is not None:
                _atomic_write_private(markdown_report, markdown_bytes)

        attempts = publish_with_recheck(
            buffers, _publish, attempt_observer=_observe_attempt
        )

        # Retry-absorbed mutation: ``replaced`` and ``audit`` above were
        # computed from the pre-race buffers while the published report was
        # rebuilt from the refreshed ones. Recompute BOTH over the refreshed
        # buffers so the exit code reflects what was actually published
        # (r2 F3: a mutated growth sidecar has no snapshot entry, so only the
        # audit signals can see it). Stay silent when the recompute changed
        # nothing (a rewrite to digest-identical content leaves the summary
        # unchanged and a note would be noise). The ``classes=`` ledger
        # summary stays ledger-pinned (cohort membership contract, see the
        # ``publish_with_recheck`` docstring).
        if attempts > 1:
            refreshed_replaced = _replaced_of(buffers)
            refreshed_audit = _audit_of(buffers)
            if refreshed_replaced != replaced or refreshed_audit != audit:
                replaced = refreshed_replaced
                audit = refreshed_audit
                sys.stderr.write(
                    "strict audit: retry-absorbed mutation; summary recomputed"
                    " from refreshed buffers\n"
                )

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
# Review-corpus metrics pass (review-loop exit-condition metrics, Task 3).
# Read-only aggregation over the discovered sidecar corpus: loops grouped by
# artifact_slug, per-round decay, ready-rate, cap exhaustion, segmented by the
# plan-complexity band derived from the plan file's task-checkbox count.
# Aggregate-only output in both forms: no per-file path rows, no slugs, no
# repository identifiers (privacy invariant).
# --------------------------------------------------------------------------- #


# Report schema marker for the metrics documents.
METRICS_SCHEMA = "review-metrics-v1"

# Complexity bands (plan Terms): small (5 or fewer task checkboxes), medium
# (6 to 15), large (16 or more), unknown (plan file absent or the slug match
# is ambiguous). Fixed key order keeps the report shape stable.
COMPLEXITY_BANDS = ("small", "medium", "large", "unknown")


def _repo_plans_dirs(repo: Path) -> list[Path]:
    """Resolve a repo's plans directories for band derivation.

    ``plans_dir`` plus its completed subdirectory (the ``plans_completed_dir``
    facts key, falling back to ``plans_dir`` / ``completed``). Resolution
    mirrors ``_repo_reviews_dir``: the RAW facts value is read through
    ``facts_paths`` (single parser; Design Invariant 11) and a relative value
    is anchored at the repo root. Defaults keep repos without the facts keys
    working.
    """
    raw = facts_paths.resolve_toml_key_raw(repo, "plans_dir")
    plans = Path(raw).expanduser() if raw else repo / "docs" / "history" / "plans"
    if not plans.is_absolute():
        plans = repo / plans
    raw_completed = facts_paths.resolve_toml_key_raw(repo, "plans_completed_dir")
    completed = (
        Path(raw_completed).expanduser() if raw_completed else plans / "completed"
    )
    if not completed.is_absolute():
        completed = repo / completed
    return [plans, completed]


def _plan_task_checkboxes(path: Path) -> int | None:
    """Count the plan file's task checkboxes (checked or unchecked).

    Both checkbox states count: the band measures plan size, and an archived
    plan is as large as it was when active. Returns None when the file cannot
    be read (the band then stays unknown instead of failing the pass).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return text.count("- [ ]") + text.count("- [x]")


def _band_of_count(count: int) -> str:
    """Map a task-checkbox count to its complexity band (plan Terms)."""
    if count <= 5:
        return "small"
    if count <= 15:
        return "medium"
    return "large"


def _resolve_band(slug: str, plans_dirs: list[Path]) -> str:
    """Derive a loop's complexity band from its plan file.

    The artifact slug globs both plans directories; exactly one match derives
    the band from the file's task-checkbox count. Zero matches (plan absent)
    or more than one (ambiguous: the slug matches plan files under both the
    plans directory and its completed subdirectory) resolve ``unknown``.
    """
    matches: set[Path] = set()
    for directory in plans_dirs:
        if not directory.is_dir():
            continue
        try:
            for candidate in directory.glob(f"*{slug}*.md"):
                if candidate.is_file() and not candidate.is_symlink():
                    matches.add(candidate.resolve())
        except (OSError, ValueError):
            continue
    if len(matches) != 1:
        return "unknown"
    count = _plan_task_checkboxes(next(iter(matches)))
    if count is None:
        return "unknown"
    return _band_of_count(count)


def _round_index_of(value) -> int | None:
    """Coerce a sidecar ``round`` value to an integer index, or None.

    Accepts the contracted shapes (integer, or a string like ``"r3"`` or
    ``"3"``); anything else, including bool, is unusable.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text.startswith("r"):
            text = text[1:]
        if text.isdigit():
            return int(text)
    return None


def _metrics_round_record(payload: dict) -> dict | None:
    """One loop round's metrics record from a sidecar payload, or None.

    Records the round number, verdict, staged findings total, blocking count,
    and whether ``extensions.cap_closure`` is present. Mistyped containers
    yield zeros (partial-failure design: one bad sidecar never aborts the
    pass); a record without a usable round index is not a record.
    """
    rnd = _round_index_of(payload.get("round"))
    if rnd is None:
        return None
    findings = payload.get("findings")
    if isinstance(findings, list):
        staged = len(findings)
        blocking = sum(
            1
            for finding in findings
            if isinstance(finding, dict) and finding.get("blocking") is True
        )
    else:
        counts = payload.get("counts")
        staged = (
            _coerce_int(counts.get("staged_findings"))
            if isinstance(counts, dict)
            else 0
        )
        blocking = 0
    verdict = payload.get("verdict")
    if verdict not in ("yes", "no"):
        verdict = None
    extensions = payload.get("extensions")
    cap = isinstance(extensions, dict) and "cap_closure" in extensions
    return {
        "round": rnd,
        "verdict": verdict,
        "staged": staged,
        "blocking": blocking,
        "cap_closure": cap,
    }


def _sidecar_fails_validation(payload: dict) -> bool:
    """Delegated validation gate for the metrics pass.

    Unparsable buffers are caught by the caller (payload None). A version-1
    record must pass the validator's exported version-1 contract (the single
    validation authority, ``validate_review_staging.validate_version1_payload``);
    versionless records keep their legacy compatibility treatment and are
    never re-judged against today's contract. The Markdown content argument
    is empty: the pass is sidecar-only, and with no verdict heading the
    clean-verdict cross-checks inside the validator stay quiet.
    """
    label = vrs.classify_sidecar_schema(payload)
    if label == "unsupported":
        return True
    if label != "current-v1":
        return False
    result = vrs.ValidationResult(path=Path("metrics-sidecar"))
    vrs.validate_version1_payload(payload, "", result)
    return bool(result.errors)


def _loops_from_sidecars(
    sidecars: list[Path], buffers: dict[Path, bytes]
) -> tuple[dict[str, list[dict]], int]:
    """Group discovered sidecars into per-slug loop round records.

    Returns ``(loops, legacy_count)``: ``loops`` maps each artifact slug to
    its round records sorted by round index; ``legacy_count`` counts sidecars
    that failed validation or carry no usable loop identity (the unknown-band
    legacy bucket; the pass never fails on them). A duplicate slug+round pair
    keeps the first record in sorted-path order (deterministic; no
    double-counting).
    """
    slots: dict[str, dict[int, dict]] = {}
    legacy = 0
    for sidecar in sidecars:  # caller passes sorted paths
        payload, _ = parse_payload(buffers.get(sidecar, b""))
        if payload is None or _sidecar_fails_validation(payload):
            legacy += 1
            continue
        record = _metrics_round_record(payload)
        slug = payload.get("artifact_slug")
        if record is None or not isinstance(slug, str) or not slug:
            legacy += 1
            continue
        slot = slots.setdefault(slug, {})
        if record["round"] in slot:
            continue
        slot[record["round"]] = record
    loops = {
        slug: [slot[rnd] for rnd in sorted(slot)] for slug, slot in slots.items()
    }
    return loops, legacy


def _empty_band_stats() -> dict:
    """Empty stats shape for one cohort of loops (stable key set)."""
    return {
        "loops": 0,
        "cap_closures": 0,
        "cap_exhaustion_share": 0.0,
        "findings_by_round": {},
        "blocking_by_round": {},
        "ready_by_round": {},
        "ready_rate_by_round": {},
        "latest_round_distribution": {},
    }


def _band_stats(loops: list[list[dict]]) -> dict:
    """Aggregate one cohort of loops (a band, or all bands) into stats.

    ``loops`` is a list of per-loop round-record lists, each sorted by round
    index. Findings totals per round index form the decay series; ready-rate
    divides by ALL the cohort's loops (a loop without a round at an index is
    not ready there), so the final-index rate reads as the share of loops
    whose round at that depth was clean. Cap exhaustion counts each loop once
    (any round carrying ``extensions.cap_closure`` closes the loop through
    the cap). Round-index keys are ints in memory; JSON stringifies them.
    """
    stats = _empty_band_stats()
    stats["loops"] = len(loops)
    cap_loops = 0
    by_round_findings: dict[int, int] = {}
    by_round_blocking: dict[int, int] = {}
    by_round_ready: dict[int, int] = {}
    latest: dict[int, int] = {}
    for records in loops:
        if not records:
            continue
        if any(rec.get("cap_closure") for rec in records):
            cap_loops += 1
        last = records[-1]["round"]
        latest[last] = latest.get(last, 0) + 1
        for rec in records:
            idx = rec["round"]
            by_round_findings[idx] = by_round_findings.get(idx, 0) + rec["staged"]
            by_round_blocking[idx] = (
                by_round_blocking.get(idx, 0) + rec["blocking"]
            )
            if rec.get("verdict") == "yes":
                by_round_ready[idx] = by_round_ready.get(idx, 0) + 1
    total = len(loops)
    stats["cap_closures"] = cap_loops
    stats["cap_exhaustion_share"] = (cap_loops / total) if total else 0.0
    stats["findings_by_round"] = dict(sorted(by_round_findings.items()))
    stats["blocking_by_round"] = dict(sorted(by_round_blocking.items()))
    stats["ready_by_round"] = dict(sorted(by_round_ready.items()))
    stats["ready_rate_by_round"] = {
        idx: ((ready / total) if total else 0.0)
        for idx, ready in sorted(by_round_ready.items())
    }
    stats["latest_round_distribution"] = dict(sorted(latest.items()))
    return stats


def build_metrics_report(
    band_loops: dict[str, list[list[dict]]], legacy_count: int
) -> dict:
    """Build the aggregate-only metrics report.

    Every band key is always present (stable shape for consumers); the
    unknown band carries the legacy-bucket sidecar count next to its loops.
    Output holds aggregates only: no sidecar paths, no slugs, no repository
    identifiers.
    """
    bands = {}
    for band in COMPLEXITY_BANDS:
        bands[band] = _band_stats(band_loops.get(band, []))
    bands["unknown"]["legacy_bucket_sidecars"] = legacy_count
    overall = _band_stats(
        [
            loops
            for band in COMPLEXITY_BANDS
            for loops in band_loops.get(band, [])
        ]
    )
    return {
        "schema": METRICS_SCHEMA,
        "loops": overall["loops"],
        "sidecars_legacy_bucket": legacy_count,
        "bands": bands,
        "overall": overall,
    }


def serialize_metrics_json(report: dict) -> bytes:
    """Canonical JSON bytes for the metrics report (deterministic)."""
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _fmt_rate(value: float) -> str:
    """Format a share/rate with two decimals for the Markdown tables."""
    return f"{value:.2f}"


def _rounds_suffix(stats: dict, key: str) -> str:
    """Format a per-round stats map as a compact ``rN=value`` list."""
    return ", ".join(
        f"r{idx}={stats[key][idx]}" for idx in sorted(stats[key])
    )


def serialize_metrics_markdown(report: dict) -> bytes:
    """Aggregate-only Markdown for the metrics report.

    Tables carry per-round and per-band aggregates only; no per-file rows,
    paths, slugs, or repository identifiers (privacy invariant).
    """
    overall = report["overall"]
    lines: list[str] = []
    lines.append("# Review corpus metrics")
    lines.append("")
    lines.append(
        f"Loops: {report['loops']}; sidecars in legacy bucket: "
        f"{report['sidecars_legacy_bucket']}"
    )
    lines.append("")
    lines.append("## Overall")
    lines.append("")
    lines.append("| round | findings | blocking | ready | ready rate |")
    lines.append("|---|---|---|---|---|")
    for idx in sorted(overall["findings_by_round"]):
        lines.append(
            f"| r{idx} | {overall['findings_by_round'][idx]} "
            f"| {overall['blocking_by_round'].get(idx, 0)} "
            f"| {overall['ready_by_round'].get(idx, 0)} "
            f"| {_fmt_rate(overall['ready_rate_by_round'].get(idx, 0.0))} |"
        )
    lines.append("")
    lines.append(
        f"Cap closures: {overall['cap_closures']} of {overall['loops']} loops "
        f"(share {_fmt_rate(overall['cap_exhaustion_share'])})"
    )
    lines.append(
        "Latest-round distribution: "
        + _rounds_suffix(overall, "latest_round_distribution")
    )
    lines.append("")
    lines.append("## Complexity bands")
    lines.append("")
    lines.append(
        "| band | loops | cap closures | cap share | findings by round "
        "| ready rate by round | latest rounds |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for band in COMPLEXITY_BANDS:
        stats = report["bands"][band]
        lines.append(
            f"| {band} | {stats['loops']} | {stats['cap_closures']} "
            f"| {_fmt_rate(stats['cap_exhaustion_share'])} "
            f"| {_rounds_suffix(stats, 'findings_by_round')} "
            f"| {_rounds_suffix(stats, 'ready_rate_by_round')} "
            f"| {_rounds_suffix(stats, 'latest_round_distribution')} |"
        )
    lines.append("")
    lines.append(
        "Legacy bucket (sidecars that failed validation or carry no usable "
        "loop identity, counted in the unknown band): "
        f"{report['sidecars_legacy_bucket']}"
    )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def run_metrics_pass(repo_roots: list[Path]) -> dict:
    """Run the read-only metrics pass over the discovered corpus.

    Reuses the facts-driven discovery primitives (repo walk, reviews-dir
    resolution, sidecar ingestion, pinned single reads, delegated
    validation) and never fails on a legacy or unparseable sidecar (legacy
    bucket). Returns the aggregate-only report (see
    ``build_metrics_report``).
    """
    band_loops: dict[str, list[list[dict]]] = {
        band: [] for band in COMPLEXITY_BANDS
    }
    legacy = 0
    for root in repo_roots:
        for repo in iter_repos_under_root(root):
            found: set[Path] = set()
            _ingest_sidecars(_repo_reviews_dir(repo), found)
            _ingest_sidecars(repo / "docs" / "history" / "reviews", found)
            sidecars = sorted(found)
            buffers = {s: read_byte_buffer(s) for s in sidecars}
            loops, legacy_count = _loops_from_sidecars(sidecars, buffers)
            legacy += legacy_count
            plans_dirs = _repo_plans_dirs(repo)
            for slug in sorted(loops):
                band_loops[_resolve_band(slug, plans_dirs)].append(loops[slug])
    return build_metrics_report(band_loops, legacy)


def cmd_metrics(
    user_facts: Path,
    json_path: Path | None,
    markdown_path: Path | None,
) -> int:
    """``--metrics``: read-only corpus aggregation into per-band loop metrics.

    Aggregate-only outputs (no per-file path rows) are written atomically to
    the caller-supplied paths. Never fails on a legacy or unparseable
    sidecar: failing sidecars land in the unknown-band legacy bucket.
    """
    repo_roots = _roots_from_facts(user_facts)
    report = run_metrics_pass(repo_roots)
    if json_path is not None:
        _atomic_write_private(json_path, serialize_metrics_json(report))
    if markdown_path is not None:
        _atomic_write_private(markdown_path, serialize_metrics_markdown(report))
    sys.stdout.write(
        f"metrics: {report['loops']} loop(s); legacy bucket "
        f"{report['sidecars_legacy_bucket']}\n"
    )
    return 0


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


def _metrics_v1_payload(
    slug: str,
    round_no: int,
    verdict: str,
    blocking_flags: list[bool],
    *,
    cap_closure: bool = False,
) -> dict:
    """Build a valid version-1 sidecar payload for the metrics selftests.

    Reuses the validator's ``_version1_payload`` builder (ONE canonical
    five-worker shape; its pre-fence date keeps the extended-field, coverage,
    and record-kind fences exempt) and overrides the loop-identity fields the
    metrics pass reads: artifact_slug, round, verdict, findings (with
    blocking flags), and the cap-closure extension.
    """
    payload = vrs._version1_payload()
    payload["artifact_slug"] = slug
    payload["round"] = round_no
    payload["verdict"] = verdict
    payload["findings"] = [
        vrs._current_finding(id=i + 1, blocking=flag)
        for i, flag in enumerate(blocking_flags)
    ]
    payload["counts"]["staged_findings"] = len(blocking_flags)
    payload["extensions"] = (
        {"cap_closure": {"round": round_no}} if cap_closure else {}
    )
    return payload


# ---- facts_roots ----
@_test("summarize_review_stats#facts_roots")
def _t_facts_roots(check) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        facts = td_path / "facts.md"
        facts.write_text(
            "| `personal_projects_root` | `~/Projects/myrepos/` | x |\n"
            "| `company_projects_root` | `~/Projects/example-company/` | y |\n",
            encoding="utf-8",
        )
        roots = facts_paths.resolve_projects_roots(facts)
        check(
            "facts_roots: two roots resolved via facts_paths import",
            roots[0] is not None and roots[1] is not None,
            str(roots),
        )
        # Roots are never embedded in tracked output. Build a REAL report from
        # a current-shaped fixture and assert the production output (public
        # markdown + canonical JSON) contains no resolved root string. The
        # markdown-content check proves the fixture actually produced report
        # output, so the privacy assertion cannot pass vacuously.
        fixture = _make_current_payload(["quality"])
        report = build_effectiveness_report([("growth", fixture)])
        md_out = serialize_effectiveness_markdown(report).decode("utf-8")
        json_out = serialize_effectiveness_json(report).decode("utf-8")
        check(
            "facts_roots: report markdown produced from the fixture",
            "# Review effectiveness report" in md_out
            and report["availability"]["cohorts"] >= 1,
            md_out[:120],
        )
        root_strings = [str(r) for r in roots if r is not None]
        check(
            "facts_roots: no resolved root embedded in public report output",
            all(r not in md_out and r not in json_out for r in root_strings),
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
    """The conservation ledger's growth/legacy shape decision must NOT diverge
    from the validator's exported current-shape label family. Two invariants:

    1. Shape agreement: for every sidecar whose panel identity SATISFIES the
       five-worker set (so the shape decision is the SOLE growth-vs-legacy
       discriminator), the conservation ``growth``/``legacy`` outcome must
       agree with ``vrs.is_current_shape`` (the validator's exported label
       family). Sidecars that fail the five-worker gate land in ``legacy``
       regardless of shape, so they are out of scope for this agreement.
       (r3 F1: the growth-branch shape now comes from the label family, which
       includes ``legacy-worker-shaped``, NOT from the aggregation adapter's
       carved-out routing set.)
    2. Growth-aggregation consistency: any sidecar that reaches the ``growth``
       ledger MUST aggregate through a panel-aware adapter (the current
       adapter, or the worker-shaped compatibility adapter that preserves
       worker/lens launch totals). A growth sidecar routed to the generic
       legacy adapter (no per-worker metrics) is exactly the silent exclusion
       this test guards against."""
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

    # Invariant 1: shape agreement across five-worker-satisfying shapes. The
    # conservation outcome (growth=current family, legacy=legacy) must equal
    # the validator's exported current-shape predicate.
    for name, payload in (
        ("panel_row_shape", panel_row_shape),
        ("workers_map_only", workers_map_only),
        ("worker_shaped", {
            "date": "2026-08-28",
            "panel": [
                {"worker": w, "lenses": [w], "status": "complete", "raw": 0}
                for w in ("quality", "implementation", "testing")
            ],
        }),
    ):
        cons_shape = shape_via_conservation(payload)
        validator_shape = "current" if vrs.is_current_shape(payload) else "legacy"
        check(
            f"shape_drift: conservation agrees with validator family for {name}",
            cons_shape == validator_shape,
            f"conservation={cons_shape} validator={validator_shape}",
        )

    # Invariant 2: a sidecar that reaches growth must aggregate through a
    # panel-aware adapter (current schema, or the worker-shaped compat adapter
    # with per-worker launch metrics preserved).
    with tempfile.TemporaryDirectory() as td:
        sc = Path(td) / "growth.stats.json"
        _write_private_sidecar(sc, panel_row_shape)
        buf = {sc: read_byte_buffer(sc)}
        ledger, _ = run_conservation([sc], buf, empty_baseline)
        reaches_growth = sc in ledger["growth"]
        norm = aggregate_sidecar(panel_row_shape)
        check(
            "shape_drift: growth sidecar aggregates as current",
            (not reaches_growth) or norm["schema"] == "current",
            f"reaches_growth={reaches_growth} schema={norm['schema']}",
        )
    with tempfile.TemporaryDirectory() as td:
        worker_shaped_growth = {
            "date": "2026-08-28",
            "panel": [
                {"worker": w, "lenses": [w], "status": "complete", "raw": 0}
                for w in ("quality", "implementation", "testing")
            ],
        }
        sc = Path(td) / "growth-ws.stats.json"
        _write_private_sidecar(sc, worker_shaped_growth)
        buf = {sc: read_byte_buffer(sc)}
        ledger, _ = run_conservation([sc], buf, empty_baseline)
        reaches_growth = sc in ledger["growth"]
        norm = aggregate_sidecar(worker_shaped_growth)
        check(
            "shape_drift: worker-shaped growth sidecar aggregates panel-aware",
            (not reaches_growth)
            or (norm["schema"] == "legacy" and norm["worker_launches"] == 3),
            f"reaches_growth={reaches_growth} schema={norm['schema']} "
            f"worker_launches={norm['worker_launches']}",
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

        # Family-local refusal-expectation closure (review r2 F6): True iff
        # fn raised PermissionsError with EXACTLY the expected message.
        def _expect_refusal(fn, msg) -> bool:
            try:
                fn()
            except PermissionsError as exc:
                return str(exc) == msg
            return False

        # Characterization anchors (GREEN today via the _reject_symlink
        # pre-check): the kernel-grade dirfd rewrite must keep refusing
        # statically symlinked paths with the same message.
        real_parent = td_path / "real-parent"
        real_parent.mkdir()
        parent_link = td_path / "parent-link"
        os.symlink(real_parent, parent_link)
        check(
            "permissions: tighten_parent_ai_playbook refuses symlinked parent",
            _expect_refusal(
                lambda: tighten_parent_ai_playbook(parent_link),
                f"refusing to follow symlink target: {parent_link}",
            ),
        )

        real_dir = td_path / "real-dir"
        real_dir.mkdir()
        dir_link = td_path / "dir-link"
        os.symlink(real_dir, dir_link)
        check(
            "permissions: ensure_private_dir refuses symlinked private dir",
            _expect_refusal(
                lambda: ensure_private_dir(dir_link),
                f"refusing to follow symlink target: {dir_link}",
            ),
        )

        real_target = tel / "real-target.json"
        real_target.write_text("{}", encoding="utf-8")
        target_link = tel / "target-link.json"
        os.symlink(real_target, target_link)
        check(
            "permissions: _atomic_write_private refuses symlinked target",
            _expect_refusal(
                lambda: _atomic_write_private(target_link, b"{}"),
                f"refusing to follow symlink target: {target_link}",
            ),
        )

        real_parent2 = td_path / "real-parent2"
        real_parent2.mkdir()
        parent_link2 = td_path / "parent-link2"
        os.symlink(real_parent2, parent_link2)
        check(
            "permissions: _atomic_write_private refuses symlinked parent",
            _expect_refusal(
                lambda: _atomic_write_private(parent_link2 / "baseline.json", b"{}"),
                f"refusing to follow symlink target: {parent_link2}",
            ),
        )
        read_target = tel / "read-target.json"
        read_target.write_text("{}", encoding="utf-8")
        os.chmod(str(read_target), 0o600)
        read_link = tel / "read-link.json"
        os.symlink(read_target, read_link)
        check(
            "permissions: read_private_file refuses symlinked file",
            _expect_refusal(
                lambda: read_private_file(read_link),
                f"refusing to follow symlink target: {read_link}",
            ),
        )

        # Static symlinked PARENT of the private dir (review r1 F1): the
        # parent pre-check must refuse with the same contract even without
        # a race (previously a raw NotADirectoryError escaped the parent
        # dirfd open).
        real_dir_p = td_path / "real-dir-parent"
        real_dir_p.mkdir()
        parent_link_dir = td_path / "parent-link-dir"
        os.symlink(real_dir_p, parent_link_dir)
        check(
            "permissions: ensure_private_dir refuses symlinked parent",
            _expect_refusal(
                lambda: ensure_private_dir(parent_link_dir / "priv"),
                f"refusing to follow symlink target: {parent_link_dir}",
            ),
        )

        # Legacy loose-mode file re-tightened on the read path (review r1
        # F3): a 0644 file read via read_private_file ends up 0600 (fd-based
        # fstat/fchmod, mirroring the directory helpers' per-run re-assert).
        legacy = tel / "legacy.json"
        legacy.write_bytes(b"{}")
        os.chmod(str(legacy), 0o644)
        check(
            "permissions: loose-mode legacy fixture starts 0644",
            _file_mode(legacy) == 0o644,
        )
        read_private_file(legacy)
        check(
            "permissions: read_private_file re-tightens loose mode to 0600",
            _file_mode(legacy) == 0o600,
        )

        # Advisory-refusal arm (review r4 F2): a refused re-tighten must NOT
        # fail the read; the warning branch (stderr note naming the path) is
        # the only production line of its kind and had no witness. Reached
        # portably by monkeypatching os.fchmod to raise OSError for one call
        # (family no-op-patch idiom; restored in finally), so the read
        # proceeds with the mode still loose.
        import contextlib
        import io

        refusal = tel / "refusal.json"
        refusal.write_bytes(b'{"k": 1}')
        os.chmod(str(refusal), 0o644)
        orig_fchmod = os.fchmod
        fchmod_calls = {"n": 0}

        def _fail_first_fchmod(fd, mode):
            if fchmod_calls["n"] == 0:
                fchmod_calls["n"] += 1
                raise OSError(errno.EPERM, "mode change refused")
            return orig_fchmod(fd, mode)

        os.fchmod = _fail_first_fchmod
        try:
            with contextlib.redirect_stderr(io.StringIO()) as refusal_err:
                refusal_bytes = read_private_file(refusal)
        finally:
            os.fchmod = orig_fchmod
        check(
            "permissions: refused re-tighten still returns the file bytes",
            refusal_bytes == b'{"k": 1}',
        )
        check(
            "permissions: refused re-tighten warns on stderr naming the path",
            "warning: could not re-tighten mode of" in refusal_err.getvalue()
            and str(refusal) in refusal_err.getvalue(),
        )

        # Post-temp-creation failure arm (review r2 F5): a DIRECTORY at the
        # target's final component lets the temp file be created but makes
        # the dirfd-relative os.replace fail (rename onto a directory), so
        # the except-cleanup is the only thing standing between the failure
        # and a leaked temp file.
        real_parent3 = td_path / "real-parent3"
        real_parent3.mkdir()
        (real_parent3 / "baseline.json").mkdir()
        raised_oserror = False
        try:
            _atomic_write_private(real_parent3 / "baseline.json", b"{}")
        except OSError:
            raised_oserror = True
        check(
            "permissions: _atomic_write_private post-temp failure raises OSError",
            raised_oserror,
        )
        residue_post_temp = [
            p.name
            for p in real_parent3.iterdir()
            if p.name.startswith(".baseline-")
        ]
        check(
            "permissions: post-temp failure leaves no temp residue",
            residue_post_temp == [],
        )

        # Missing-parent arm (review r5 F3): the non-symlink errno branch of
        # the parent dirfd open (r2 F2) had no witness. A missing parent
        # (ENOENT) must surface as a fail-closed PermissionsError whose
        # message is the accurate open-failure text naming the parent, not
        # the symlink refusal text and not a raw OSError. tighten_parent_
        # ai_playbook takes the parent itself; the other three take a child
        # inside it. Message-predicate idiom (r4 advisory-refusal pattern).
        missing_parent = td_path / "nope"

        def _names_parent_only(msg) -> bool:
            # Shared four-conjunct predicate (plan round 3, item 5; r1 F2
            # hoist): the message must be the accurate open-failure text
            # naming the PARENT, and a message naming the full child path
            # (of which the parent string is a substring) fails. Trivially
            # true for tighten_parent_ai_playbook, which takes no child.
            return (
                msg is not None
                and "cannot open parent directory" in msg
                and str(missing_parent) in msg
                and str(missing_parent / "child") not in msg
            )

        for helper_name, helper_call in (
            (
                "tighten_parent_ai_playbook",
                lambda: tighten_parent_ai_playbook(missing_parent),
            ),
            (
                "ensure_private_dir",
                lambda: ensure_private_dir(missing_parent / "child"),
            ),
            (
                "create_private_file_exclusive",
                lambda: create_private_file_exclusive(
                    missing_parent / "child", b"{}"
                ),
            ),
            (
                "_atomic_write_private",
                lambda: _atomic_write_private(
                    missing_parent / "child", b"{}"
                ),
            ),
        ):
            msg = None
            try:
                helper_call()
            except PermissionsError as exc:
                msg = str(exc)
            check(
                f"permissions: {helper_name} missing parent fails closed "
                "naming the parent",
                _names_parent_only(msg),
            )

        # read_private_file missing-parent arm (plan round 3, item 5): its
        # own check beside the shared loop, NOT a loop entry: before the
        # round-3 manager rewrite a missing parent surfaced as a raw
        # FileNotFoundError that would ESCAPE the loop's ``except
        # PermissionsError`` and abort the whole family at run_selftest
        # (RED, contained, at authoring time). Capturing
        # (PermissionsError, OSError) keeps any failure contained; since
        # the rewrite the parent-open refusal is the
        # PermissionsError("cannot open parent directory: ...") message
        # and the check passes.
        msg = None
        try:
            read_private_file(missing_parent / "child")
        except (PermissionsError, OSError) as exc:
            msg = str(exc)
        check(
            "permissions: read_private_file missing parent fails closed "
            "naming the parent",
            _names_parent_only(msg),
        )

        # Non-symlink final-component open-failure arm (plan 2026-09-06,
        # item 1): the dirfd-relative final-component open surfaces only the
        # bare file name in the OSError message, losing the directory
        # context. Given an existing real directory (tel) and a missing
        # child, the captured message must contain the full path string.
        # RED before Task 2: the message used to read "[Errno 2] No such
        # file or directory: 'absent.json'" with no directory context;
        # the re-raise now names the full path. Same msg-capture idiom as
        # the missing-parent arm above; capturing (PermissionsError,
        # OSError) keeps any failure contained. The exception object is
        # kept (review r1 F2): the plan's diagnostics criterion promises
        # both the full path AND chaining via ``from exc``, so the arm
        # also pins the OSError subclass name and the original OSError as
        # ``__cause__``; the reconstructed exception does not carry
        # errno/filename attributes (plan Task 2 note).
        caught = None
        try:
            read_private_file(tel / "absent.json")
        except (PermissionsError, OSError) as exc:
            caught = exc
        msg = None if caught is None else str(caught)
        check(
            "permissions: read_private_file non-symlink open failure names "
            "the full path",
            msg is not None and str(tel / "absent.json") in msg,
        )
        check(
            "permissions: read_private_file open failure preserves the "
            "OSError subclass and chains the original OSError",
            caught is not None
            and type(caught) is type(caught.__cause__),
        )

        # read_byte_buffer non-symlink open-failure arm (review r1 F1):
        # sibling of the read_private_file arm above for the strict
        # audit's sidecar reader. Given the same existing real directory
        # (tel) and a missing child, the translated message must name the
        # full path ("cannot read byte buffer: <path>: ..."). Same
        # msg-capture idiom; capturing (PermissionsError, OSError) keeps
        # any failure contained. The exception object is kept (review r2
        # F2): like the read_private_file sibling above, the arm also
        # pins the OSError subclass name and the original OSError as
        # ``__cause__`` via the exact type relationship (review r2
        # F1 idiom); the reconstructed exception does not carry
        # errno/filename attributes (plan Task 2 note).
        caught_b = None
        try:
            read_byte_buffer(tel / "absent-buffer.json")
        except (PermissionsError, OSError) as exc:
            caught_b = exc
        buf_msg = None if caught_b is None else str(caught_b)
        check(
            "permissions: read_byte_buffer non-symlink open failure names "
            "the full path",
            buf_msg is not None
            and str(tel / "absent-buffer.json") in buf_msg,
        )
        check(
            "permissions: read_byte_buffer open failure preserves the "
            "OSError subclass and chains the original OSError",
            caught_b is not None
            and type(caught_b) is type(caught_b.__cause__),
        )

        # Pre-check-bypass arms (review r1 F2): with _reject_symlink patched
        # to a no-op, the kernel flags (O_NOFOLLOW / O_DIRECTORY dirfd) are
        # the only guard left, so these arms pin the kernel mechanism the
        # characterization anchors above cannot see. Idiom mirrors the
        # snapshot_races arm (d) for telemetry_lock; restore in finally.
        import sys as _sys

        this_mod = _sys.modules[__name__]
        orig_reject = _reject_symlink
        this_mod._reject_symlink = lambda p: None  # noqa: ARG001
        try:
            # read_private_file: symlinked final component -> the
            # O_NOFOLLOW open fails (ELOOP) and the translation names it.
            check(
                "permissions: read_private_file kernel-refuses symlink "
                "with pre-check disabled",
                _expect_refusal(
                    lambda: read_private_file(read_link),
                    f"refusing to follow symlink target: {read_link}",
                ),
            )

            # ensure_private_dir: symlinked final component under a real
            # parent -> the dirfd-relative O_DIRECTORY|O_NOFOLLOW open
            # fails (ENOTDIR on darwin, ELOOP on Linux) inside the
            # translated errno tuple.
            check(
                "permissions: ensure_private_dir kernel-refuses symlink "
                "with pre-check disabled",
                _expect_refusal(
                    lambda: ensure_private_dir(dir_link),
                    f"private path is not a directory: {dir_link}",
                ),
            )

            # create_private_file_exclusive / _atomic_write_private: with a
            # symlinked FINAL component the kernel refuses via O_EXCL
            # (EEXIST -> BaselineExists), so the discriminating bypass arm
            # uses a symlinked PARENT: the parent dirfd open itself must
            # fail closed with the r1 F1 translation naming the parent.
            check(
                "permissions: create_private_file_exclusive kernel-refuses "
                "symlink with pre-check disabled",
                _expect_refusal(
                    lambda: create_private_file_exclusive(
                        parent_link2 / "bl.json", b"{}"
                    ),
                    f"refusing symlinked parent: {parent_link2}",
                ),
            )

            check(
                "permissions: _atomic_write_private kernel-refuses symlink "
                "with pre-check disabled",
                _expect_refusal(
                    lambda: _atomic_write_private(
                        parent_link2 / "baseline.json", b"{}"
                    ),
                    f"refusing symlinked parent: {parent_link2}",
                ),
            )

            # Pre-check-bypass arms (review r2 F4): the two matrix cells the
            # r1 F2 arms left empty. (a) tighten_parent_ai_playbook has no
            # other bypass arm: the O_NOFOLLOW parent open must fail closed
            # on a symlinked parent with the ENOTDIR-family message.
            check(
                "permissions: tighten_parent_ai_playbook kernel-refuses "
                "symlink with pre-check disabled",
                _expect_refusal(
                    lambda: tighten_parent_ai_playbook(parent_link),
                    f"parent is not a directory: {parent_link}",
                ),
            )

            # (b) ensure_private_dir's symlinked PARENT (final component
            # real): the parent dirfd open must fail closed naming the
            # parent.
            check(
                "permissions: ensure_private_dir kernel-refuses symlinked "
                "parent with pre-check disabled",
                _expect_refusal(
                    lambda: ensure_private_dir(parent_link_dir / "priv"),
                    f"refusing symlinked parent: {parent_link_dir}",
                ),
            )

            # read_private_file symlinked ANCESTOR (plan round 3, item 2):
            # the full-path O_NOFOLLOW open guarded only the final
            # component, so with the pre-check disabled it FOLLOWED a
            # symlinked ancestor directory and returned the bytes; RED
            # until the pinned-parent manager landed (plan 2026-09-05,
            # item 2). The arm exercises a depth-1 (immediate-parent)
            # swap, refused by the O_NOFOLLOW on the parent open itself;
            # deeper ancestors follow the r2 sibling contract (r1 F1).
            anc_real = td_path / "real-anc"
            anc_real.mkdir()
            (anc_real / "target.json").write_text("{}", encoding="utf-8")
            anc_link = td_path / "anc-link"
            os.symlink(anc_real, anc_link)
            check(
                "permissions: read_private_file "
                "kernel-refuses symlinked ancestor with pre-check disabled",
                _expect_refusal(
                    lambda: read_private_file(anc_link / "target.json"),
                    f"refusing symlinked parent: {anc_link}",
                ),
            )

            # read_byte_buffer symlinked ANCESTOR (plan 2026-09-06, item 2):
            # RED before Task 2: the reader the strict audit uses for
            # sidecar content used to open the full path string with only
            # the target pre-check, so with the pre-check disabled it
            # FOLLOWED a symlinked ancestor directory and returned the
            # bytes; the pinned-parent rerouting now kernel-refuses it.
            # Reuses the anc_real / anc_link fixtures of the sibling arm
            # above (anc_link -> real ancestor dir containing target.json);
            # refusal message mirrors the read_private_file ancestor
            # contract exactly.
            check(
                "permissions: read_byte_buffer kernel-refuses symlinked "
                "ancestor with pre-check disabled",
                _expect_refusal(
                    lambda: read_byte_buffer(anc_link / "target.json"),
                    f"refusing symlinked parent: {anc_link}",
                ),
            )

            # read_byte_buffer symlinked FINAL component (review r1 F1):
            # sibling of the read_private_file final-component bypass arm
            # above, reusing its read_link fixture (symlink under the real
            # tel directory pointing at the real read_target file); with
            # the pre-check disabled the O_NOFOLLOW open fails
            # (ELOOP/ENOTDIR) and the translation names the link with the
            # target-refusal message.
            check(
                "permissions: read_byte_buffer kernel-refuses symlinked "
                "target with pre-check disabled",
                _expect_refusal(
                    lambda: read_byte_buffer(read_link),
                    f"refusing to follow symlink target: {read_link}",
                ),
            )

            # Rename-over-symlink arm (review r2 F10): a symlinked FINAL
            # target with the pre-check disabled is clobbered
            # accepted-by-design: the write lands at the pinned path, the
            # symlink is replaced (not followed), content is correct, and
            # no temp residue remains.
            clobber_payload = b'{"clobbered": true}'
            _atomic_write_private(target_link, clobber_payload)
            check(
                "permissions: bypassed _atomic_write_private clobbers "
                "target symlink at the pinned path",
                not os.path.islink(str(target_link))
                and target_link.read_bytes() == clobber_payload,
            )
            residue_clobber = [
                p.name
                for p in tel.iterdir()
                if p.name.startswith(".baseline-")
            ]
            check(
                "permissions: bypassed clobber leaves no temp residue",
                residue_clobber == [],
            )

            # create_private_file_exclusive symlinked FINAL component (review
            # r3 F1, retitled r4 F6): with the pre-check disabled, this arm
            # is a characterization anchor, not a kernel discriminator: POSIX
            # makes open(..., O_CREAT | O_EXCL, ...) fail with EEXIST on an
            # existing symlink final component regardless of O_NOFOLLOW, so
            # the refusal (-> BaselineExists) holds with or without the
            # dirfd-relative open; the discriminating kernel cells for this
            # helper are the symlinked-PARENT arms above. Pinned as-is: no
            # creation through the link, symlink and target undisturbed.
            attacker = td_path / "attacker"
            attacker.mkdir()
            steal = tel / "steal.json"
            os.symlink(attacker / "stolen.json", steal)
            baseline_refused = False
            try:
                create_private_file_exclusive(steal, b"{}")
            except BaselineExists:
                baseline_refused = True
            check(
                "permissions: create_private_file_exclusive "
                "O_EXCL characterization: existing symlink final component "
                "fails closed as BaselineExists",
                baseline_refused
                and not (attacker / "stolen.json").exists()
                and os.path.islink(str(steal)),
            )
        finally:
            this_mod._reject_symlink = orig_reject


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

        # (c) static symlink at lock path rejected (characterization; GREEN
        # today). Remove arm (a)'s leftover regular lock file first so the
        # symlink create is not blocked by an occupied path.
        lock_path = tel / LOCK_FILE_NAME
        lock_path.unlink(missing_ok=True)
        t2 = td_path / "t2"
        t2.mkdir()
        # Unguarded create on purpose: a guarded create would silently skip
        # when the path is occupied, which is exactly the fixture hazard the
        # unlink above removes.
        os.symlink(t2 / "target", lock_path)
        check("snapshot_races: static symlink occupies lock path", lock_path.is_symlink())
        raised_c = False
        try:
            with telemetry_lock(tel):
                pass
        except PermissionsError:
            raised_c = True
        check(
            "snapshot_races: static symlink at lock path rejected",
            raised_c and not (t2 / "target").exists(),
        )
        lock_path.unlink()
        check("snapshot_races: static symlink removed after rejection", not lock_path.exists())

        # (d) symlink swap in race window fails closed with a friendly error
        # (RED until the open's ELOOP is translated). Patch _reject_symlink
        # to a no-op: this simulates the pre-check passing before the swap -
        # the exact TOCTOU race window this arm pins. No sleeps or threads.
        # The kernel ELOOP detail is intentionally replaced by the
        # operator-facing message (PermissionsError extends Exception, not
        # OSError, so the raw errno is lost by design).
        evil = td_path / "evil"
        evil.mkdir()
        os.symlink(evil / "outside.lock", lock_path)
        check("snapshot_races: swapped symlink occupies lock path", lock_path.is_symlink())
        orig_reject = _reject_symlink

        def _noop_reject(path: Path) -> None:  # noqa: ARG001
            pass

        this_mod._reject_symlink = _noop_reject
        raised_d: PermissionsError | None = None
        try:
            with telemetry_lock(tel):
                pass
        except PermissionsError as exc:
            raised_d = exc
        finally:
            this_mod._reject_symlink = orig_reject
        check(
            "snapshot_races: telemetry_lock translates a race-window symlink "
            "swap into a friendly error",
            raised_d is not None
            and str(raised_d)
            == f"telemetry lock path is a symlink (possible tampering): {lock_path}",
        )
        check(
            "snapshot_races: symlink swap attack target not created",
            not (evil / "outside.lock").exists(),
        )
        lock_path.unlink()
        check("snapshot_races: lock path clean at family exit", not lock_path.exists())


# ---- strict_audit_stale_snapshot ----
@_test("summarize_review_stats#strict_audit_stale_snapshot")
def _t_strict_audit_stale_snapshot(check) -> None:
    import tempfile

    # Isolate HOME so cmd_* (which resolve Path.home()/.ai-playbook) never
    # touch the developer's REAL ~/.ai-playbook during the selftest.
    orig_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory() as home_tmp:
        os.environ["HOME"] = home_tmp
        try:
            _stale_snapshot_inner(check)
        finally:
            if orig_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = orig_home


def _stale_snapshot_inner(check) -> None:
    import contextlib
    import io
    import sys as _sys
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
        # Bound once at the top of the family (r1 F3): the lag,
        # both-counters, and no-report arms below re-use this path.
        sc2 = repo / "docs" / "reviews" / "y.stats.json"
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        # Snapshot the original gen-1 bytes for the stale derivation below.
        gen1_bytes = read_byte_buffer(sc)

        tel = td_path / "review-telemetry"
        bp = tel / "baseline.json"
        tel.parent.mkdir(parents=True, exist_ok=True)
        rc = cmd_init_baseline(facts, bp, tel)
        check("strict_audit_stale_snapshot: init succeeds", rc == 0 and bp.is_file())

        # First-call mutation hook: the FIRST publish_with_recheck invocation
        # (which happens after the initial buffer read but before the first
        # recheck) rewrites the on-disk sidecar; every invocation delegates
        # to the real function.
        p2 = _make_current_payload(["quality"])
        p2["counts"]["raw_findings"] = 8  # size bucket 1-5 -> 6-15
        this_mod = _sys.modules[__name__]
        orig_pwr = publish_with_recheck

        def _rewrite_on_first_call(rewrites: dict) -> Callable:
            calls = {"n": 0}

            def hooked(buffers, publish_fn, **kwargs):
                if calls["n"] == 0:
                    for path, new_payload in rewrites.items():
                        if isinstance(new_payload, bytes):
                            path.write_bytes(new_payload)
                        else:
                            _write_private_sidecar(path, new_payload)
                calls["n"] += 1
                return orig_pwr(buffers, publish_fn, **kwargs)

            return hooked

        def _audit_with_hook(rewrites: dict, out=None, md_out=None) -> tuple[int, str]:
            """Run ``cmd_strict_audit`` with a first-call sidecar rewrite
            hooked into ``publish_with_recheck``; return ``(rc, stderr)``.
            Owns the module patch, stderr capture, and restore."""
            this_mod.publish_with_recheck = _rewrite_on_first_call(rewrites)
            try:
                with contextlib.redirect_stderr(io.StringIO()) as err:
                    rc_audit = cmd_strict_audit(
                        facts, bp, tel, json_report=out, markdown_report=md_out
                    )
            finally:
                this_mod.publish_with_recheck = orig_pwr
            return rc_audit, err.getvalue()

        def _read_or_empty(path):
            return path.read_bytes() if path.is_file() else b""

        def _skipped_malformed_of(path) -> object:
            # Guarded parse of a published report's availability counter:
            # a missing/invalid report or a non-dict availability block
            # yields None instead of aborting the family.
            availability: object = None
            raw = _read_or_empty(path)
            if raw:
                try:
                    availability = json.loads(raw.decode("utf-8")).get(
                        "availability", {}
                    )
                except ValueError:
                    availability = None
            return (
                availability.get("skipped_malformed")
                if isinstance(availability, dict)
                else None
            )

        out = td_path / "out-effectiveness.json"
        md_out = td_path / "out-effectiveness.md"
        audit_rc, first_err = _audit_with_hook({sc: p2}, out=out, md_out=md_out)
        # The one-time change is absorbed by the bounded retry: no PublishRace.
        # The recomputed summary now counts the mutated sidecar as replaced
        # (plan round 2, Task 2): rc 1 plus the recomputed-summary note.
        check(
            "strict_audit_stale_snapshot: audit returns 1 after retry-absorbed mutation",
            audit_rc == 1,
        )
        check(
            "strict_audit_stale_snapshot: stderr names the recomputed summary",
            "retry-absorbed mutation; summary recomputed" in first_err,
        )

        # Fresh expectation derived AFTER the call from the current on-disk
        # sidecar (never by hand-editing observed output). One report, both
        # serializations.
        payload_now, _ = parse_payload(read_byte_buffer(sc))
        fresh_report = build_effectiveness_report([("baseline", payload_now)])
        fresh = serialize_effectiveness_json(fresh_report)
        fresh_md = serialize_effectiveness_markdown(fresh_report)
        payload_gen1, _ = parse_payload(gen1_bytes)
        stale = serialize_effectiveness_json(
            build_effectiveness_report([("baseline", payload_gen1)])
        )
        # Guarded read: a regression that fails the audit without writing the
        # report must fail the check below, not abort the family with
        # FileNotFoundError.
        published = _read_or_empty(out)
        # One combined predicate: the published bytes equal the fresh
        # derivation AND differ from the gen-1 derivation. Pre-fix the stale
        # bytes equal the gen-1 derivation (serializer is deterministic), so
        # both halves are false.
        check(
            "strict_audit_stale_snapshot: published report matches recheck-verified input",
            published == fresh and published != stale,
        )
        # Markdown half of the rebuild contract: both formats are serialized
        # inside _publish from the rebuilt report, so the published markdown
        # must equal the fresh derivation too (guarded like the JSON read).
        published_md = _read_or_empty(md_out)
        check(
            "strict_audit_stale_snapshot: published markdown matches recheck-verified input",
            published_md == fresh_md,
        )

        # Summary-lag arm (plan round 2, Task 1; repurposed r4 F3 to a
        # distinct discriminator): re-baseline the sidecar (payload A on
        # disk), then a fresh first-call hook rewrites it at the publish
        # gate to a DIFFERENT valid payload B (raw_findings moved to the
        # 16+ size bucket). Unlike the first arm (which pins the rc and
        # stderr note alone), this arm pins the report-vs-ledger split: the
        # PUBLISHED report is rebuilt from B (its cohort carries B's 16+
        # size bucket, not A's), while the stdout ``classes=`` ledger
        # summary line stays byte-identical to a hook-free baseline audit
        # run over the same ledger (cohort membership is ledger-pinned).
        # The recompute note check is kept: rc 1 plus the stderr note.
        # Round 3, item 4 strengthening: a second valid sidecar (sc2,
        # bound at the top of the family) joins the corpus before this
        # re-init; see the discrimination comment at the classes= check
        # below for why the rewrite moves it into would-be-unreadable.
        _write_private_sidecar(sc2, _make_current_payload(["risk"]))
        bp.unlink()
        rc_init_lag = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init before summary-lag audit succeeds",
            rc_init_lag == 0 and bp.is_file(),
        )

        def _classes_of(stdout_text: str) -> str:
            # The ledger-derived ``classes=`` tail of the stdout summary
            # line; empty string when the line is missing (fails both
            # identity checks below rather than aborting the family).
            for line in stdout_text.splitlines():
                if "classes=" in line:
                    return line.split("classes=", 1)[1]
            return ""

        with contextlib.redirect_stdout(io.StringIO()) as base_out:
            _audit_with_hook({})
        base_classes = _classes_of(base_out.getvalue())
        p_b = _make_current_payload(["quality"])
        p_b["counts"]["raw_findings"] = 25  # size bucket 6-15 -> 16+
        out_lag = td_path / "out-lag-effectiveness.json"
        with contextlib.redirect_stdout(io.StringIO()) as lag_out:
            lag_rc, lag_err = _audit_with_hook(
                {sc: p_b, sc2: b"{ not json"}, out=out_lag
            )
        check(
            "strict_audit_stale_snapshot: summary-lag arm recomputes anomalies",
            lag_rc == 1
            and "retry-absorbed mutation; summary recomputed" in lag_err,
        )
        # Discrimination strengthened (plan round 3, item 4): the hook also
        # moved sc2 (valid at init) into would-be-unreadable at the publish
        # gate, so a refreshed-ledger regression now changes the tail via
        # sc2; only the ledger-pinned implementation keeps it identical.
        check(
            "strict_audit_stale_snapshot: lag run classes= summary stays "
            "ledger-pinned (identical to hook-free baseline run)",
            base_classes != "" and _classes_of(lag_out.getvalue()) == base_classes,
        )
        # Report half of the split: the published report reflects payload
        # B's bucket (16+), never payload A's (6-15, the on-disk sidecar at
        # re-init time), because _publish serializes from the refreshed
        # buffers. Guarded read; missing report fails the check.
        lag_report = _read_or_empty(out_lag).decode("utf-8", "replace")
        check(
            "strict_audit_stale_snapshot: lag run published report reflects "
            "payload B's size bucket, not the ledger-pinned payload A",
            '"size_bucket": "16+"' in lag_report
            and '"size_bucket": "6-15"' not in lag_report,
        )
        # Restore the single-sidecar corpus for the downstream arms
        # (plan round 3, item 4): sc2 served the classes= discrimination
        # above and is removed so every later arm's pinned expectations
        # stay byte-identical to the single-sidecar corpus they were
        # written against.
        sc2.unlink()

        # Malformed-at-retry arm: re-baseline the (now gen-2) sidecar, then a
        # fresh first-call hook rewrites it at the publish gate to a payload
        # that PARSES but violates the counts integrity assert
        # (derive_size_bucket), so the refreshed buffer is skipped in the
        # rebuilt report (availability.skipped_malformed) instead of silently
        # crashing _publish or dropping the cohort without a signal.
        p3 = _make_current_payload(["quality"])
        p3["counts"]["raw_total"] = 99  # != raw_findings (1): integrity skip
        bp.unlink()
        rc_init2 = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init after gen-2 mutation succeeds",
            rc_init2 == 0 and bp.is_file(),
        )

        out2 = td_path / "out2-effectiveness.json"
        audit_rc2, malformed_err = _audit_with_hook({sc: p3}, out=out2)
        check("strict_audit_stale_snapshot: malformed-at-retry audit returns 1", audit_rc2 == 1)
        check(
            "strict_audit_stale_snapshot: malformed-at-retry stderr note carries count",
            "skipped 1 malformed sidecar(s)" in malformed_err,
        )
        check(
            "strict_audit_stale_snapshot: malformed-at-retry note carries report pointer",
            "see availability.skipped_malformed in the report" in malformed_err,
        )
        skipped2 = _skipped_malformed_of(out2)
        check(
            "strict_audit_stale_snapshot: malformed-at-retry skipped in published report",
            skipped2 == 1,
        )

        # Unparseable-at-retry arm: re-baseline the (now p3) sidecar back to
        # a valid payload, then a fresh first-call hook rewrites it at the
        # publish gate to bytes that do NOT parse. The sidecar must be
        # dropped from the rebuilt report with a stderr note carrying the
        # parse-drop count (the sole sidecar), not vanish silently.
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        bp.unlink()
        rc_init3 = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init after integrity mutation succeeds",
            rc_init3 == 0 and bp.is_file(),
        )
        out3 = td_path / "out3-effectiveness.json"
        audit_rc3, unparseable_err = _audit_with_hook(
            {sc: b"{ not json"}, out=out3
        )
        check(
            "strict_audit_stale_snapshot: unparseable-at-retry audit returns 1",
            audit_rc3 == 1,
        )
        check(
            "strict_audit_stale_snapshot: unparseable-at-retry stderr note carries count",
            "dropped 1 unparseable sidecar(s) (retry-induced)" in unparseable_err,
        )
        # Drop-only case: the note stands alone; the report pointer names
        # the malformed-skip counter, which stays 0 for parse-drops.
        check(
            "strict_audit_stale_snapshot: unparseable-at-retry note has no report pointer",
            "see availability.skipped_malformed" not in unparseable_err,
        )
        empty_report = serialize_effectiveness_json(build_effectiveness_report([]))
        check(
            "strict_audit_stale_snapshot: unparseable-at-retry report has no cohort",
            _read_or_empty(out3) == empty_report,
        )

        # Both-counters arm: the hook rewrites one sidecar to the
        # integrity-violating payload shape (skipped in the rebuilt report)
        # and the other to unparseable bytes (dropped before
        # classification), pinning the composed note and the disjointness
        # of the two counters. The second sidecar re-uses the sc2 path
        # (bound at the top of the family, unlinked after the lag arm);
        # the write below is the re-assertion.
        _write_private_sidecar(sc2, _make_current_payload(["risk"]))
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        bp.unlink()
        rc_init4 = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init with second sidecar succeeds",
            rc_init4 == 0 and bp.is_file(),
        )
        p4 = _make_current_payload(["quality"])
        p4["counts"]["raw_total"] = 99  # != raw_findings (1): integrity skip
        out4 = td_path / "out4-effectiveness.json"
        audit_rc4, both_err = _audit_with_hook(
            {sc: p4, sc2: b"{ not json"}, out=out4
        )
        check(
            "strict_audit_stale_snapshot: both-counters audit returns 1",
            audit_rc4 == 1,
        )
        check(
            "strict_audit_stale_snapshot: both-counters note carries both fragments",
            "skipped 1 malformed sidecar(s)" in both_err
            and "dropped 1 unparseable sidecar(s) (retry-induced)" in both_err,
        )
        # Expected derivation: the integrity-violating sidecar is skipped
        # inside the report builder; the unparseable one is absent entirely.
        fresh4 = serialize_effectiveness_json(
            build_effectiveness_report([("baseline", p4)])
        )
        raw4 = _read_or_empty(out4)
        skipped4 = _skipped_malformed_of(out4)
        check(
            "strict_audit_stale_snapshot: both-counters skipped 1, unparseable absent",
            skipped4 == 1 and raw4 == fresh4,
        )

        # Report-path independence arm (plan Task 2): the note's emission
        # stays independent of whether the report output paths are None.
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        _write_private_sidecar(sc2, _make_current_payload(["risk"]))
        bp.unlink()
        rc_init5 = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init before no-report audit succeeds",
            rc_init5 == 0 and bp.is_file(),
        )
        audit_rc5, no_report_err = _audit_with_hook({sc: b"{ not json"})
        check(
            "strict_audit_stale_snapshot: no-report audit returns 1",
            audit_rc5 == 1,
        )
        check(
            "strict_audit_stale_snapshot: note fires without report paths",
            "dropped 1 unparseable sidecar(s) (retry-induced)" in no_report_err,
        )

        # Chronic-unreadable arm (plan round 2, Task 3): a sidecar
        # unparseable at the initial read (written BEFORE cmd_init_baseline,
        # no hook mutation anywhere in the run) is a chronic condition, not
        # retry-induced. The parse-drop note must NOT fire for it; the
        # sidecar stays visible via the ledger-pinned classes= summary
        # (unreadable=1) instead.
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        sc_b = repo / "docs" / "reviews" / "b.stats.json"
        sc_b.write_bytes(b"{ not json")
        bp.unlink()
        rc_init6 = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init with chronic-unreadable sidecar succeeds",
            rc_init6 == 0 and bp.is_file(),
        )
        with contextlib.redirect_stdout(io.StringIO()) as chronic_out_cap, \
                contextlib.redirect_stderr(io.StringIO()) as chronic_err_cap:
            chronic_rc = cmd_strict_audit(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: chronic-unreadable sidecar does not fire the parse-drop note",
            chronic_rc == 0
            and "unparseable sidecar(s)" not in chronic_err_cap.getvalue()
            and "unreadable=1" in chronic_out_cap.getvalue(),
        )

        # Mask arm (plan round 3, item 3): the hook REPAIRS the chronic
        # sidecar (sc_b -> valid) and simultaneously BREAKS the healthy
        # one (sc -> unparseable) at the publish gate. Both refreshed
        # buffers differ from their build_baseline snapshot digests (which
        # cover every discovered sidecar, including the unparseable one),
        # so the audit still exits 1. The pre-round-3 count subtraction
        # (dropped 1 - chronic 1 == 0) masked this window and left the
        # note silent (RED until the set-based retry-delta landed, plan
        # 2026-09-05, item 3); the set-based retry-delta must fire with
        # count 1.
        # Re-assert sc2 parseable (both-counters idiom): the mask arm's
        # exact dropped-1 count depends on it, not on earlier-arm state.
        _write_private_sidecar(sc2, _make_current_payload(["risk"]))
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        sc_b.write_bytes(b"{ not json")  # chronic: unparseable before init
        bp.unlink()
        rc_init_mask = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init before mask arm succeeds",
            rc_init_mask == 0 and bp.is_file(),
        )
        mask_repair = _make_current_payload(["risk"])
        out_mask = td_path / "out-mask-effectiveness.json"
        mask_rc, mask_err = _audit_with_hook(
            {sc_b: mask_repair, sc: b"{ not json"}, out=out_mask
        )
        # Line-scoped guard (review r3 F3): the "skipped" exclusion must
        # apply to the drop-notes line only, not the whole stderr, so an
        # unrelated stderr line containing "skipped" cannot fail the arm.
        notes_line = next(
            (
                line
                for line in mask_err.splitlines()
                if line.startswith("strict audit: dropped")
            ),
            "",
        )
        check(
            "strict_audit_stale_snapshot: mask arm fires on repaired-chronic plus fresh drop",
            mask_rc == 1
            and "dropped 1 unparseable sidecar(s) (retry-induced)" in notes_line
            and "skipped" not in notes_line,
        )

        # Double-flip arm (plan 2026-09-06, item 3): a chronic sidecar
        # repaired and then re-broken INSIDE one retry window ends
        # unparseable (retry-induced final state) yet stays in the chronic
        # snapshot set; before Task 3 the bare-snapshot chronic set kept
        # the note silent, and Task 3's window-aware chronicity
        # reclassifies it as retry-induced. This
        # fixture shape is exactly the executed probe
        # (docs/tmp/probe-chronic-reabsorption.py, run 2026-09-06: rc 0,
        # five sc_b reads, stderr empty). sc_b is written unparseable
        # BEFORE cmd_init_baseline (chronic); inside ONE cmd_strict_audit
        # run a first-call publish_with_recheck hook repairs sc_b to a
        # distinct valid payload, and a read_byte_buffer patch with a read
        # counter (realpath-matched to sc_b: the macOS tempdir /var ->
        # /private/var symlink would break a plain Path equality) re-breaks
        # sc_b just before its THIRD read (read 1: initial buffer; read 2:
        # re-read after the repair-triggered retry; read 3: the next
        # attempt's recheck digest read). Final bytes equal the baseline
        # snapshot, so rc stays 0 (exit-code invariant pinned); the read
        # counter pins the observed five-read retry sequence (reads 4-5:
        # the closing refresh + recheck) so a future recheck-loop refactor
        # fails diagnosably instead of silently.
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        sc_b.write_bytes(b"{ not json")  # chronic: unparseable before init
        bp.unlink()
        rc_init_double_flip = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init before double-flip arm succeeds",
            rc_init_double_flip == 0 and bp.is_file(),
        )
        double_flip_repair = _make_current_payload(["risk"])
        double_flip_repair["counts"]["raw_findings"] = 8  # distinct payload
        orig_rbb = read_byte_buffer
        sc_b_reads = {"n": 0}
        sc_b_real = Path(os.path.realpath(sc_b))

        def _rebreak_sc_b_before_third_read(path, *rbb_args, **rbb_kwargs):
            if Path(os.path.realpath(path)) == sc_b_real:
                sc_b_reads["n"] += 1
                if sc_b_reads["n"] == 3:
                    sc_b.write_bytes(b"{ not json")
            return orig_rbb(path, *rbb_args, **rbb_kwargs)

        this_mod.read_byte_buffer = _rebreak_sc_b_before_third_read
        try:
            double_flip_rc, double_flip_err = _audit_with_hook(
                {sc_b: double_flip_repair}
            )
        finally:
            this_mod.read_byte_buffer = orig_rbb
        check(
            "strict_audit_stale_snapshot: re-broken chronic sidecar counts "
            "as retry-induced",
            double_flip_rc == 0
            and sc_b_reads["n"] == 5
            and "dropped 1 unparseable sidecar(s) (retry-induced)"
            in double_flip_err,
        )

        # Silent-suppression arm (review r1 F6): the sidecar is mutated on
        # disk BEFORE the audit (so the pre-race ``replaced`` already counts
        # it), and the hook then rewrites it to yet another digest at the
        # publish gate. The refreshed ``replaced`` set is unchanged, so the
        # recomputed-summary note must stay silent (r3 F1 noise guard) even
        # though the audit still exits 1 on the real replacement.
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        bp.unlink()
        rc_init7 = cmd_init_baseline(facts, bp, tel)
        check(
            "strict_audit_stale_snapshot: re-init before silent-suppression audit succeeds",
            rc_init7 == 0 and bp.is_file(),
        )
        p_pre = _make_current_payload(["quality"])
        p_pre["counts"]["raw_findings"] = 8  # size bucket 1-5 -> 6-15
        _write_private_sidecar(sc, p_pre)
        p_post = _make_current_payload(["quality"])
        p_post["counts"]["raw_findings"] = 25  # 6-15 -> 16-30: still replaced
        silent_rc, silent_err = _audit_with_hook({sc: p_post})
        check(
            "strict_audit_stale_snapshot: pre-replaced sidecar still fails the audit",
            silent_rc == 1,
        )
        check(
            "strict_audit_stale_snapshot: unchanged replaced set stays note-silent",
            "summary recomputed" not in silent_err,
        )

        # Growth-sidecar arm (review r2 F3): a sidecar created AFTER the
        # last init (no baseline snapshot entry) is rewritten by the
        # first-call hook to a payload carrying an out-of-family panel
        # identity. ``_replaced_of`` cannot see it (snap is None), so only
        # the recomputed AUDIT signals over the refreshed buffers can:
        # pre-fix the exit code stays 0 while the report already reflects
        # the mutated content.
        sc_g = repo / "docs" / "reviews" / "g.stats.json"
        _write_private_sidecar(sc_g, _make_current_payload(["quality"]))
        p_g = _make_current_payload(["quality"])
        p_g["panel"].append(
            {
                "worker": "bogus-out-of-family",
                "status": "complete",
                "raw": 0,
                "solo": 0,
                "echo": 0,
            }
        )
        growth_rc, growth_err = _audit_with_hook({sc_g: p_g})
        check(
            "strict_audit_stale_snapshot: growth-sidecar mutation recomputes audit signals",
            growth_rc == 1
            and "retry-absorbed mutation; summary recomputed" in growth_err,
        )

        # Attempts signal (plan round 2, Task 1): publish_with_recheck must
        # return the attempt count so callers can detect retry-absorbed
        # mutations. Clean publish (no mutation) reports one attempt; a
        # first-call sidecar rewrite absorbed by the bounded retry reports
        # two attempts.
        _write_private_sidecar(sc, _make_current_payload(["quality"]))
        clean_buffers = {sc: read_byte_buffer(sc)}
        clean_attempts = orig_pwr(clean_buffers, lambda: None)
        check(
            "strict_audit_stale_snapshot: clean publish reports one attempt",
            clean_attempts == 1,
        )
        p_other = _make_current_payload(["quality"])
        p_other["counts"]["raw_findings"] = 40  # size bucket 1-5 -> 31-50
        retry_buffers = {sc: read_byte_buffer(sc)}
        this_mod.publish_with_recheck = _rewrite_on_first_call({sc: p_other})
        try:
            retry_attempts = this_mod.publish_with_recheck(
                retry_buffers, lambda: None
            )
        finally:
            this_mod.publish_with_recheck = orig_pwr
        check(
            "strict_audit_stale_snapshot: retry-absorbed publish reports two attempts",
            retry_attempts == 2,
        )


# ---- current_adapter ----
@_test("summarize_review_stats#current_adapter")
def _t_current_adapter(check) -> None:
    """Parse a five-worker (current) sidecar; normalized totals cover launches,
    lenses, dedup, discard, calibration, overflow, and triage, plus the observed
    token totals from the sidecar's ``usage`` record when present (never
    estimated)."""
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
        # Observed token usage record (collect-and-report contract): the
        # seam's previous fixture values (input 999 / output 1 / total 1000)
        # in the usage-record shape produced by review_usage_capture.
        "usage": {
            "adapter": "zcode-sqlite",
            "provenance": {
                "db": "~/.zcode/cli/db/db.sqlite",
                "session_ids": ["sess_89a0cb7"],
                "ambiguous": False,
                "window_started_at_ms": 1788698397679,
                "window_ended_at_ms": 1788719997679,
                "captured_at_ms": 1788719997680,
                "estimated": False,
            },
            "totals": {
                "input_tokens": 999,
                "output_tokens": 1,
                "reasoning_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "computed_total_tokens": 1000,
            },
            "by_agent_kind": {
                "main": {"input_tokens": 999, "output_tokens": 1},
                "subagent": {"input_tokens": 0, "output_tokens": 0},
                "other": {"input_tokens": 0, "output_tokens": 0},
            },
        },
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
    # Observed token totals: the adapter no longer attaches them (single
    # extraction path is build_effectiveness_report); the shared helper
    # still reads the observed ``totals`` block (never estimated).
    check(
        "current_adapter: usage_totals not attached (single report path)",
        "usage_totals" not in norm,
        str(sorted(norm)),
    )
    check(
        "current_adapter: observed usage totals extracted by helper",
        _usage_totals_from_payload(payload) == {
            "input_tokens": 999,
            "output_tokens": 1,
            "reasoning_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "computed_total_tokens": 1000,
        },
        str(_usage_totals_from_payload(payload)),
    )
    # The normalized totals are unchanged by the usage record.
    no_usage = aggregate_current(
        {k: v for k, v in payload.items() if k != "usage"}
    )
    check(
        "current_adapter: non-token totals unchanged by usage record",
        norm == no_usage,
    )

    # r4 F1: a truthy mistyped container (e.g. severity_calibration=5) must
    # aggregate to 0 instead of raising TypeError and aborting the whole
    # strict-audit report (partial-failure design).
    bad = json.loads(json.dumps(payload))
    bad["severity_calibration"] = 5
    bad["discarded"] = "not-a-list"
    bad["overflow"] = 7
    try:
        bad_norm = aggregate_current(bad)
        crash = False
    except TypeError:
        bad_norm = None
        crash = True
    check(
        "current_adapter: mistyped containers do not crash len-derived counts (r4 F1)",
        not crash
        and bad_norm["calibration_count"] == 0
        and bad_norm["discard_count"] == 0
        and bad_norm["overflow_count"] == 0,
    )


# ---- current_adapter_usage_collected ----
@_test("summarize_review_stats#current_adapter_usage_collected")
def _t_current_adapter_usage_collected(check) -> None:
    """Given a current-schema payload whose ``usage`` record carries the seam
    test's previous fixture values, the shared extraction helper returns the
    observed input/output/total token counts while the adapter attaches no
    ``usage_totals`` (single extraction path: the effectiveness report)."""
    payload = {
        "review_type": "branch review",
        "date": "2026-09-07",
        "round": "r1",
        "panel_mode": "full",
        "counts": {"raw_findings": 2, "staged_findings": 1},
        "panel": [
            {"worker": "quality", "lenses": ["quality"], "status": "complete", "raw": 2}
        ],
        "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}],
        "usage": {
            "adapter": "zcode-sqlite",
            "provenance": {"session_ids": ["sess_89a0cb7"], "estimated": False},
            "totals": {
                "input_tokens": 999,
                "output_tokens": 1,
                "reasoning_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "computed_total_tokens": 1000,
            },
            "by_agent_kind": {
                "main": {"input_tokens": 999, "output_tokens": 1},
                "subagent": {"input_tokens": 0, "output_tokens": 0},
                "other": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    }
    norm = aggregate_current(payload)
    observed = _usage_totals_from_payload(payload)
    check(
        "current_adapter_usage_collected: observed token totals extracted",
        observed is not None,
        str(observed),
    )
    if observed is not None:
        check(
            "current_adapter_usage_collected: input tokens",
            observed["input_tokens"] == 999,
        )
        check(
            "current_adapter_usage_collected: output tokens",
            observed["output_tokens"] == 1,
        )
        check(
            "current_adapter_usage_collected: total tokens",
            observed["computed_total_tokens"] == 1000,
        )
    check(
        "current_adapter_usage_collected: adapter attaches no usage_totals",
        "usage_totals" not in norm,
        str(sorted(norm)),
    )
    check(
        "current_adapter_usage_collected: launch totals still aggregated",
        norm["worker_launches"] == 1 and norm["lens_launches"] == 1,
    )


# ---- current_adapter_no_usage_unchanged ----
@_test("summarize_review_stats#current_adapter_no_usage_unchanged")
def _t_current_adapter_no_usage_unchanged(check) -> None:
    """Given the same payload WITHOUT ``usage``, normalized totals are
    byte-identical to the pre-telemetry output (launch/dedup/triage numbers
    unchanged, no token fields added)."""
    payload = {
        "review_type": "branch review",
        "date": "2026-09-07",
        "round": "r1",
        "panel_mode": "full",
        "counts": {"raw_findings": 2, "staged_findings": 1, "deduplicated": 1},
        "panel": [
            {"worker": "quality", "lenses": ["quality"], "status": "complete", "raw": 2}
        ],
        "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}],
    }
    norm = aggregate_current(payload)
    expected = {
        "schema": "current",
        "worker_launches": 1,
        "lens_launches": 1,
        "raw_findings": 2,
        "staged_findings": 1,
        "dedup_count": 1,
        "discard_count": 0,
        "calibration_count": 0,
        "overflow_count": 0,
        "triage": {"fixed": 1, "deferred": 0, "dropped": 0, "pending": 0},
        "severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 1},
    }
    check(
        "current_adapter_no_usage_unchanged: normalized totals byte-identical",
        json.dumps(norm, sort_keys=True) == json.dumps(expected, sort_keys=True),
        json.dumps(norm, sort_keys=True),
    )


# ---- current_adapter_malformed_usage_treated_absent ----
@_test("summarize_review_stats#current_adapter_malformed_usage_treated_absent")
def _t_current_adapter_malformed_usage_treated_absent(check) -> None:
    """A ``usage`` that is a bare string or lacks ``totals`` is treated as
    absent (no crash, no token fields), mirroring the validator's tolerance."""
    base = {
        "review_type": "branch review",
        "date": "2026-09-07",
        "round": "r1",
        "panel_mode": "full",
        "counts": {"raw_findings": 1},
        "panel": [{"worker": "quality", "status": "complete", "raw": 1}],
        "findings": [],
    }
    for label, bad_usage in (
        ("bare string", "usage-as-a-string"),
        ("missing totals", {"adapter": "zcode-sqlite", "provenance": {}}),
        ("mistyped totals", {"adapter": "zcode-sqlite", "totals": "not-a-dict"}),
    ):
        payload = dict(base)
        payload["usage"] = bad_usage
        try:
            norm = aggregate_current(payload)
            crashed = False
        except Exception:
            norm = None
            crashed = True
        check(
            f"current_adapter_malformed_usage_treated_absent: {label} no crash",
            not crashed,
        )
        check(
            f"current_adapter_malformed_usage_treated_absent: {label} treated absent",
            norm is not None
            and "usage_totals" not in norm
            and _usage_totals_from_payload(payload) is None,
            str(sorted(norm or {})),
        )


def _usage_sidecar(date: str, totals: dict | None) -> dict:
    """Minimal cohort-valid sidecar fixture with an optional usage record."""
    payload = {
        "review_type": "branch review",
        "round": "r1",
        "date": date,
        "counts": {"raw_findings": 4},
        "domains": ["docs"],
        "panel_mode": "full",
        "agents_launched": 4,
        "findings": [{"id": 1, "severity": "Low", "triage": "fixed"}] * 4,
    }
    if totals is not None:
        payload["usage"] = {
            "adapter": "zcode-sqlite",
            "provenance": {"session_ids": ["sess_89a0cb7"], "estimated": False},
            "totals": totals,
            "by_agent_kind": {},
        }
    return payload


_USAGE_TOTALS_A = {
    "input_tokens": 100,
    "output_tokens": 10,
    "reasoning_tokens": 0,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "computed_total_tokens": 110,
}
_USAGE_TOTALS_B = {
    "input_tokens": 50,
    "output_tokens": 5,
    "reasoning_tokens": 0,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "computed_total_tokens": 55,
}


# ---- coverage_post_cutover_denominator ----
@_test("summarize_review_stats#coverage_post_cutover_denominator")
def _t_coverage_post_cutover_denominator(check) -> None:
    """Coverage is computed over POST-CUTOVER sidecars only: a legacy
    pre-cutover sidecar is excluded from the denominator by the
    ``date >= USAGE_CUTOVER_DATE`` classification, and a post-cutover sidecar
    without ``usage`` is in the denominator but not the numerator (the
    denominator is NOT "sidecars with usage")."""
    corpus = [
        ("growth", _usage_sidecar("2026-09-07", _USAGE_TOTALS_A)),
        ("baseline", _usage_sidecar("2026-01-01", None)),  # pre-cutover, no usage
        ("growth", _usage_sidecar("2026-09-06", None)),  # post-cutover, no usage
    ]
    report = build_effectiveness_report(corpus)
    cov = report.get("usage_coverage") or {}
    check(
        "coverage_post_cutover_denominator: numerator is sidecars with usage",
        cov.get("sidecars_with_usage") == 1,
        str(cov),
    )
    check(
        "coverage_post_cutover_denominator: denominator is post-cutover sidecars",
        cov.get("post_cutover_sidecars") == 2,
        str(cov),
    )
    check(
        "coverage_post_cutover_denominator: coverage is 1 of 2",
        cov.get("coverage") == 0.5,
        str(cov),
    )
    totals = report.get("observed_token_totals") or {}
    check(
        "coverage_post_cutover_denominator: observed totals sum observed records",
        totals.get("input_tokens") == 100 and totals.get("computed_total_tokens") == 110,
        str(totals),
    )
    # The classification itself: date >= cutover, missing date conservative.
    check(
        "coverage_post_cutover_denominator: cutoff constant",
        USAGE_CUTOVER_DATE == "2026-09-06",
    )
    check(
        "coverage_post_cutover_denominator: cutover day itself is post-cutover",
        _is_post_cutover({"date": "2026-09-06"}),
    )
    check(
        "coverage_post_cutover_denominator: day before cutover is pre-cutover",
        not _is_post_cutover({"date": "2026-09-05"}),
    )
    check(
        "coverage_post_cutover_denominator: missing date counts as post-cutover",
        _is_post_cutover({}),
    )


# ---- decision_rule_supplementary ----
@_test("summarize_review_stats#decision_rule_supplementary")
def _t_decision_rule_supplementary(check) -> None:
    """Token cost stays labeled supplementary while observed-token coverage
    over post-cutover sidecars is below 70 percent; at or above 70 percent the
    supplementary label is dropped. No branch of the rule reads or requires
    pre-cutover token data (a pre-cutover sidecar carrying usage is ignored)."""
    # Low coverage: 1 of 2 post-cutover sidecars carry usage (50% < 70%), and
    # a pre-cutover sidecar WITH usage must not lift the numerator or totals.
    low = build_effectiveness_report(
        [
            ("growth", _usage_sidecar("2026-09-07", _USAGE_TOTALS_A)),
            ("growth", _usage_sidecar("2026-09-08", None)),
            ("baseline", _usage_sidecar("2026-01-01", _USAGE_TOTALS_B)),
        ]
    )
    cov_low = low.get("usage_coverage") or {}
    check(
        "decision_rule_supplementary: pre-cutover usage not counted in numerator",
        cov_low.get("sidecars_with_usage") == 1,
        str(cov_low),
    )
    check(
        "decision_rule_supplementary: below threshold labeled supplementary",
        cov_low.get("token_cost_supplementary") is True,
        str(cov_low),
    )
    md_low = serialize_effectiveness_markdown(low).decode("utf-8")
    check(
        "decision_rule_supplementary: markdown labels token cost supplementary",
        "token cost: supplementary" in md_low,
        md_low,
    )
    totals_low = low.get("observed_token_totals") or {}
    check(
        "decision_rule_supplementary: pre-cutover tokens not read into totals",
        totals_low.get("input_tokens") == 100,
        str(totals_low),
    )

    # High coverage: 2 of 2 post-cutover sidecars carry usage (100% >= 70%).
    high = build_effectiveness_report(
        [
            ("growth", _usage_sidecar("2026-09-07", _USAGE_TOTALS_A)),
            ("growth", _usage_sidecar("2026-09-08", _USAGE_TOTALS_B)),
        ]
    )
    cov_high = high.get("usage_coverage") or {}
    check(
        "decision_rule_supplementary: coverage at/above 70 percent",
        cov_high.get("coverage") == 1.0,
        str(cov_high),
    )
    check(
        "decision_rule_supplementary: supplementary label dropped at threshold",
        cov_high.get("token_cost_supplementary") is False,
        str(cov_high),
    )
    md_high = serialize_effectiveness_markdown(high).decode("utf-8")
    check(
        "decision_rule_supplementary: markdown drops supplementary label",
        "supplementary" not in md_high,
        md_high,
    )

    # N7 boundary witness: coverage of EXACTLY 0.70 (7 of 10 post-cutover
    # sidecars carry usage) drops the supplementary label (< vs <= pinned).
    exact = build_effectiveness_report(
        [("growth", _usage_sidecar(f"2026-09-{10 + i:02d}",
                                   _USAGE_TOTALS_A if i < 7 else None))
         for i in range(10)]
    )
    cov_exact = exact.get("usage_coverage") or {}
    check(
        "decision_rule_supplementary: exact 0.70 coverage",
        cov_exact.get("coverage") == 0.70,
        str(cov_exact),
    )
    check(
        "decision_rule_supplementary: exact 0.70 not supplementary",
        cov_exact.get("token_cost_supplementary") is False,
        str(cov_exact),
    )
    totals_high = high.get("observed_token_totals") or {}
    check(
        "decision_rule_supplementary: totals sum both post-cutover records",
        totals_high.get("input_tokens") == 150
        and totals_high.get("computed_total_tokens") == 165,
        str(totals_high),
    )


# ---- legacy_adapters ----
@_test("summarize_review_stats#legacy_adapters")
def _t_legacy_adapters(check) -> None:
    """Legacy code/plan/rfc/document sidecars (agents_launched, raw_findings,
    agent-keyed panels) produce COMPATIBLE normalized totals without rewriting
    the fixture. Adapter routing is pinned structurally against the
    validator's exported label family (one fixture per schema label)."""
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

    # Drift guard (r3 F6 replaced the old same-source equality canary; r4 F9
    # removed its replacement too because re-deriving the constant's
    # definition inside the test is tautological and cannot fail while the
    # definition stands). The sole drift guard is the fixture-per-label
    # routing loop below: it pins classifier labels AND adapter routing
    # behaviorally, one fixture per schema label.
    worker_shaped = {
        "date": "2026-08-28",
        "counts": {"staged_findings": 1},
        "panel": [
            {"worker": "quality", "lenses": ["quality"], "status": "complete", "raw": 1},
            {
                "worker": "implementation",
                "lenses": ["implementation"],
                "status": "complete",
                "raw": 0,
            },
            {"worker": "testing", "lenses": ["testing"], "status": "complete", "raw": 0},
        ],
        "findings": [{"id": 1, "severity": "Low", "triage": "pending"}],
    }
    label_fixtures = (
        ("current-v1", {"schema_version": 1}),
        ("legacy-panel-mode", {"panel_mode": "full"}),
        ("legacy-worker-shaped", worker_shaped),
        ("legacy", legacy_code),
    )
    for expected_label, fixture in label_fixtures:
        label = vrs.classify_sidecar_schema(fixture)
        check(
            f"legacy_adapters: fixture classifies as {expected_label}",
            label == expected_label,
            f"label={label}",
        )
        expected_route = label in vrs.CURRENT_SHAPE_LABELS and label != LEGACY_WORKER_SHAPE_LABEL
        check(
            f"legacy_adapters: adapter routing agrees with label for {expected_label}",
            adapter_is_current(fixture) == expected_route,
            f"label={label} adapter_is_current={adapter_is_current(fixture)}",
        )


# ---- schema_contract_adapters (versioned sidecar contract, RED-first) ----
@_test("summarize_review_stats#legacy_adapter_compat")
def _t_legacy_adapter_compat(check) -> None:
    """Versionless worker-shaped payload: the exported validator schema
    classifier routes it to the legacy contract, and the compatibility
    aggregation adapter preserves its worker, lens, finding, and triage totals
    (equal to the pre-version compatibility shape)."""
    legacy_worker_shaped = {
        "review_type": "branch review",
        "date": "2024-03-01",
        "round": "r1",
        "counts": {"raw_findings": 6, "staged_findings": 3, "deduplicated": 1},
        "panel": [
            {"worker": "quality", "lenses": ["quality"], "status": "complete", "raw": 2},
            {
                "worker": "implementation",
                "lenses": ["implementation"],
                "status": "complete",
                "raw": 2,
            },
            {"worker": "testing", "lenses": ["testing"], "status": "complete", "raw": 2},
        ],
        "discarded": [{"reason": "duplicate"}],
        "findings": [
            {"id": 1, "severity": "High", "triage": "fixed"},
            {"id": 2, "severity": "Medium", "triage": "dropped"},
            {"id": 3, "severity": "Low", "triage": "pending"},
        ],
    }
    check(
        "legacy_adapter_compat: validator schema classifier is exported",
        callable(vrs.classify_sidecar_schema),
        "vrs.classify_sidecar_schema not implemented yet",
    )
    label = str(vrs.classify_sidecar_schema(legacy_worker_shaped))
    check(
        "legacy_adapter_compat: versionless worker-shaped payload classifies legacy",
        "legacy" in label,
        label,
    )
    norm = aggregate_sidecar(legacy_worker_shaped)
    check(
        "legacy_adapter_compat: versionless worker-shaped payload aggregates via the legacy contract",
        norm["schema"] == "legacy",
        f"schema={norm['schema']}",
    )
    # Totals must equal the pre-version compatibility shape.
    check(
        "legacy_adapter_compat: worker launch total preserved",
        norm["worker_launches"] == 3,
        str(norm["worker_launches"]),
    )
    check(
        "legacy_adapter_compat: lens launch total preserved",
        norm["lens_launches"] == 3,
        str(norm["lens_launches"]),
    )
    check(
        "legacy_adapter_compat: staged finding total preserved",
        norm["staged_findings"] == 3,
        str(norm["staged_findings"]),
    )
    check(
        "legacy_adapter_compat: raw finding total preserved",
        norm["raw_findings"] == 6,
        str(norm["raw_findings"]),
    )
    check(
        "legacy_adapter_compat: discard total preserved",
        norm["discard_count"] == 1,
        str(norm["discard_count"]),
    )
    check(
        "legacy_adapter_compat: triage totals preserved",
        norm["triage"]["fixed"] == 1
        and norm["triage"]["dropped"] == 1
        and norm["triage"]["pending"] == 1,
        str(norm["triage"]),
    )


@_test("summarize_review_stats#current_adapter_v1")
def _t_current_adapter_v1(check) -> None:
    """Realistic version-1 five-worker panel with worker IDs and their assigned
    lens arrays: current aggregation, growth-ledger eligibility by worker
    identity, lens telemetry from ``panel[].lenses``, and no conflation of
    worker and lens identity. The fixture reuses the validator's
    ``_version1_payload`` builder so both scripts' selftests share ONE
    canonical five-worker shape."""
    worker_lenses = [
        (worker, sorted(vrs.REQUIRED_PANEL_LENSES[worker]))
        for worker in vrs.DEFAULT_PANEL_WORKERS
    ]
    payload = vrs._version1_payload()
    payload["date"] = "2099-01-01"
    payload["counts"] = {"workers_launched": 5, "raw_findings": 6, "staged_findings": 3}
    payload["findings"] = [
        {"id": 1, "severity": "High", "triage": "fixed"},
        {"id": 2, "severity": "Medium", "triage": "deferred"},
        {"id": 3, "severity": "Low", "triage": "pending"},
    ]
    check(
        "current_adapter_v1: validator schema classifier is exported",
        callable(vrs.classify_sidecar_schema),
        "vrs.classify_sidecar_schema not implemented yet",
    )
    label = str(vrs.classify_sidecar_schema(payload))
    check(
        "current_adapter_v1: version-1 payload classifies current",
        "current" in label,
        label,
    )
    norm = aggregate_sidecar(payload)
    check(
        "current_adapter_v1: aggregates via the current contract",
        norm["schema"] == "current",
        f"schema={norm['schema']}",
    )
    check(
        "current_adapter_v1: five worker launches by worker ID",
        norm["worker_launches"] == 5,
        str(norm["worker_launches"]),
    )
    # 2 + 1 + 2 + 1 + 1 = 7 lens launches, derived only from panel[].lenses.
    check(
        "current_adapter_v1: lens launches derived from panel lenses only",
        norm["lens_launches"] == 7,
        str(norm["lens_launches"]),
    )
    check(
        "current_adapter_v1: staged and raw finding totals",
        norm["staged_findings"] == 3 and norm["raw_findings"] == 6,
        f"staged={norm['staged_findings']} raw={norm['raw_findings']}",
    )
    check(
        "current_adapter_v1: triage totals preserved",
        norm["triage"]["fixed"] == 1
        and norm["triage"]["deferred"] == 1
        and norm["triage"]["pending"] == 1,
        str(norm["triage"]),
    )
    check(
        "current_adapter_v1: growth-ledger eligible by worker identity",
        satisfies_five_worker_set(payload, WORKER_PANEL_IDS),
        "five-worker identity set does not include the version-1 worker IDs",
    )
    check(
        "current_adapter_v1: worker identity is not lens identity",
        panel_identity_set(payload) == {w for w, _ in worker_lenses},
        str(sorted(panel_identity_set(payload))),
    )

    # F3: growth eligibility is scoped by schema label. A version-1 sidecar
    # whose panel rows carry legacy LENS names as worker IDs violates the
    # worker-ID contract and must NOT enter the growth ledger.
    # F7: an explicit-but-unsupported schema_version is never legacy
    # compatibility input; it ledgers as unreadable with a named signal.
    import tempfile

    marker = make_cutover_marker(set(FIVE_WORKER_PANEL_IDS))
    empty_baseline = build_baseline([], {}, marker)

    def ledger_class(p: dict) -> tuple[str, list[str]]:
        with tempfile.TemporaryDirectory() as td:
            sc = Path(td) / "x.stats.json"
            _write_private_sidecar(sc, p)
            ledger, audit = run_conservation(
                [sc], {sc: read_byte_buffer(sc)}, empty_baseline
            )
            for cls, members in ledger.items():
                if sc in members:
                    return cls, audit.get(str(sc), [])
        return "none", []

    lens_named = json.loads(json.dumps(payload))
    lens_named["panel"] = [
        {"worker": w, "lenses": [w], "status": "complete", "raw": 0}
        for w in ("quality", "implementation", "testing", "simplification", "documentation")
    ]
    cls, _ = ledger_class(lens_named)
    check(
        "current_adapter_v1: version-1 sidecar with legacy lens-named worker IDs ledgers legacy, not growth",
        cls == "legacy",
        f"class={cls}",
    )

    # r3 F1: a versionless worker-shaped FIVE-agent payload (the frozen
    # lens-era identity namespace) that is NOT in the baseline must ledger
    # growth. Pre-fix the growth branch derived its shape from the aggregation
    # adapter (which carves out legacy-worker-shaped), making growth
    # unreachable for this compatibility class and silently re-classifying
    # history from growth to legacy.
    worker_shaped_five = {
        "review_type": "Branch Review",
        "date": "2026-08-28",
        "counts": {"raw_findings": 5, "staged_findings": 2},
        "panel": [
            {"worker": w, "lenses": [w], "status": "complete", "raw": 1}
            for w in (
                "quality",
                "implementation",
                "testing",
                "simplification",
                "documentation",
            )
        ],
        "findings": [
            {"id": 1, "severity": "Medium", "triage": "pending"},
            {"id": 2, "severity": "Low", "triage": "pending"},
        ],
    }
    cls, _ = ledger_class(worker_shaped_five)
    check(
        "current_adapter_v1: versionless worker-shaped five-agent payload ledgers growth",
        cls == "growth",
        f"class={cls}",
    )

    # Positive growth path through the production classifier (F4): a valid
    # version-1 sidecar with the canonical five worker IDs ledgers growth.
    cls, _ = ledger_class(json.loads(json.dumps(payload)))
    check(
        "current_adapter_v1: valid version-1 sidecar ledgers growth",
        cls == "growth",
        f"class={cls}",
    )

    unsupported = json.loads(json.dumps(payload))
    unsupported["schema_version"] = 2
    cls, signals = ledger_class(unsupported)
    check(
        "current_adapter_v1: unsupported schema_version ledgers unreadable, not legacy",
        cls == "unreadable"
        and any("unsupported schema_version" in s for s in signals),
        f"class={cls} signals={signals}",
    )


# ---- canonical_only_aggregation (record kinds contract, RED-first) ----
@_test("summarize_review_stats#canonical_only_aggregation")
def _t_canonical_only_aggregation(check) -> None:
    """A post-fence record that declares a non-canonical ``record_kind`` never
    folds its findings into the panel-tuning aggregate: a fixture directory
    holding one canonical sidecar (two findings) and one post-fence
    reconciliation sidecar (one finding) aggregates exactly the two canonical
    findings, and the report output counts the non-canonical record separately.
    A pre-fence record or a post-fence record without ``record_kind`` aggregates
    as today (grandfathered). Fixture dates derive from the fence constant
    imported from the validator (never hardcoded)."""
    import datetime
    import tempfile

    fence = vrs.RECORD_KIND_SIDECAR_MIN_DATE
    check(
        "canonical_only_aggregation: fence constant imported from the validator",
        isinstance(fence, str) and len(fence) == 10 and fence[4] == "-" and fence[7] == "-",
        repr(fence),
    )
    post_fence_date = fence  # on/after the fence is post-fence
    pre_fence_date = (
        datetime.date.fromisoformat(fence) - datetime.timedelta(days=1)
    ).isoformat()

    def payload_of(record_kind: str | None, date: str, findings_count: int) -> dict:
        payload = vrs._version1_payload()
        payload["date"] = date
        payload["counts"] = {
            "workers_launched": 5,
            "raw_findings": findings_count,
            "staged_findings": findings_count,
        }
        payload["findings"] = [
            {"id": i + 1, "severity": "Low", "triage": "fixed"}
            for i in range(findings_count)
        ]
        if record_kind is None:
            payload.pop("record_kind", None)
        else:
            payload["record_kind"] = record_kind
        return payload

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        root = td_path / "myrepos"
        repo = root / "kind-fence-repo"
        (repo / ".ai-playbook").mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            '```toml\nreviews_dir = "docs/reviews/"\n```\n', encoding="utf-8"
        )
        canonical = payload_of("canonical", post_fence_date, 2)
        reconciliation = payload_of("reconciliation", post_fence_date, 1)
        canonical_path = repo / "docs" / "reviews" / f"{post_fence_date}-code-review-r1.stats.json"
        reconciliation_path = (
            repo / "docs" / "reviews" / f"{post_fence_date}-code-review-reconciliation-r1.stats.json"
        )
        _write_private_sidecar(canonical_path, canonical)
        _write_private_sidecar(reconciliation_path, reconciliation)

        sidecars = discover_sidecars([root])
        check(
            "canonical_only_aggregation: both fixture sidecars discovered",
            canonical_path.resolve() in sidecars
            and reconciliation_path.resolve() in sidecars,
            str(sorted(str(s) for s in sidecars)),
        )

        # Canonical-only aggregation: exactly the canonical sidecar's two
        # findings fold into the panel-tuning totals; the reconciliation
        # record's finding does not.
        norms = []
        for sidecar in sidecars:
            parsed, _reason = parse_payload(read_byte_buffer(sidecar))
            if parsed is not None:
                norms.append(aggregate_sidecar(parsed))
        total_raw = sum(n["raw_findings"] for n in norms)
        total_staged = sum(n["staged_findings"] for n in norms)
        total_fixed = sum(n["triage"]["fixed"] for n in norms)
        check(
            "canonical_only_aggregation: only canonical findings aggregate for panel tuning",
            total_raw == 2 and total_staged == 2 and total_fixed == 2,
            f"raw={total_raw} staged={total_staged} fixed={total_fixed}",
        )

        # Report output: the non-canonical record is counted separately.
        classified = [("baseline", canonical), ("baseline", reconciliation)]
        report = build_effectiveness_report(classified)
        excluded = report["availability"].get("non_canonical_records")
        check(
            "canonical_only_aggregation: non-canonical record counted separately in availability",
            excluded == 1,
            str(report["availability"]),
        )
        md = serialize_effectiveness_markdown(report).decode("utf-8")
        check(
            "canonical_only_aggregation: markdown reports the non-canonical record on its own line",
            "Non-canonical records excluded from aggregation: 1" in md,
            md,
        )

    # Grandfathered: a PRE-FENCE record with a non-canonical kind aggregates as
    # today, and so does a post-fence record without any record_kind.
    pre_fence_norm = aggregate_sidecar(payload_of("reconciliation", pre_fence_date, 1))
    check(
        "canonical_only_aggregation: pre-fence reconciliation record aggregates as today (grandfathered)",
        pre_fence_norm["raw_findings"] == 1 and pre_fence_norm["staged_findings"] == 1,
        f"raw={pre_fence_norm['raw_findings']} staged={pre_fence_norm['staged_findings']}",
    )
    kindless_norm = aggregate_sidecar(payload_of(None, post_fence_date, 1))
    check(
        "canonical_only_aggregation: post-fence record without record_kind aggregates as today (grandfathered)",
        kindless_norm["raw_findings"] == 1 and "non_canonical" not in kindless_norm,
        f"raw={kindless_norm['raw_findings']}",
    )
    canonical_norm = aggregate_sidecar(payload_of("canonical", post_fence_date, 2))
    check(
        "canonical_only_aggregation: post-fence canonical record aggregates its own findings",
        canonical_norm["raw_findings"] == 2 and "non_canonical" not in canonical_norm,
        f"raw={canonical_norm['raw_findings']}",
    )

    # r1 F22 (informational uncovered arm): a classified list holding only
    # non-canonical records yields ZERO cohort buckets, so no non-canonical
    # payload-derived metric can reach panel tuning through the grouping.
    only_non_canonical = [
        ("baseline", payload_of("reconciliation", post_fence_date, 1)),
        ("growth", payload_of("worker-evidence", post_fence_date, 1)),
    ]
    check(
        "canonical_only_aggregation: group_into_cohorts yields zero cohorts "
        "for a non-canonical-only classified list",
        group_into_cohorts(only_non_canonical) == {},
        str(group_into_cohorts(only_non_canonical)),
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

    # r4 F5: a ZERO baseline accepted yield (raw-only legacy baseline with no
    # triage data) is an unmeasurable floor, not a failed guardrail. The
    # baseline carries the same RAW volume (4 pending, untriaged findings —
    # raw-only history) so both sides share the cohort size bucket; growth
    # improves (4 accepted vs baseline 0) with the same launch reduction and
    # drop rates as the retain case: the cohort must retain with an explicit
    # unmeasurable note, not verdict "review needed".
    zero_base = make("baseline", launches=8, accepted=0, dropped=0, pending=4,
                     panel_mode="targeted", n=11)
    rep_zero = build_effectiveness_report(zero_base + growth)
    only_zero = rep_zero["cohorts"][0]
    check(
        "retain_policy: zero-baseline accepted yield does not fail the guardrail (r4 F5)",
        only_zero["verdict"] == "retain",
        str(only_zero.get("checks")),
    )
    check(
        "retain_policy: zero-baseline accepted pass carries the unmeasurable note",
        only_zero["checks"]["accepted_change_ok"] is True
        and "not measurable"
        in only_zero["checks"]["accepted_change_unmeasurable_reason"],
    )


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

    # r5 F2: negative coverage for the two guardrail FAILURE arms. Pre-fix no
    # evaluable cohort failed either guardrail, so hardcoding either check to
    # True kept the suite green. Each fixture keeps the OTHER two checks
    # passing so exactly one guard fails per case.

    # Accepted-change fall: baseline accepts 15 per review, growth accepts 6
    # (a 60% fall, far past the 20% guardrail); both sides stay in the same
    # size bucket (6-15), launches still halve (8 -> 4) and nothing is
    # dropped, so only accepted_ok is False.
    fall_base = make("baseline", launches=8, accepted=15, dropped=0,
                     panel_mode="targeted", n=11)
    fall_growth = make("growth", launches=4, accepted=6, dropped=0,
                       panel_mode="full", n=11)
    rep_fall = build_effectiveness_report(fall_base + fall_growth)
    only_fall = rep_fall["cohorts"][0]
    check(
        "review_needed: accepted fall >20% -> review needed with accepted_change_ok False (r5 F2)",
        only_fall["verdict"] == "review needed"
        and only_fall["checks"]["accepted_change_ok"] is False
        and only_fall["checks"]["launch_reduction_ok"] is True
        and only_fall["checks"]["drop_rate_change_ok"] is True,
        str(only_fall.get("checks")),
    )

    # Drop-rate rise: both sides accept 8 per review; baseline drops nothing
    # (8 findings, bucket 6-15), growth drops 7 of its 15 staged findings
    # (same 6-15 bucket, drop rate 0.467 vs 0, far past the 10pp guardrail);
    # launches still halve and accepted counts match, so only drop_ok is
    # False.
    drop_base = make("baseline", launches=8, accepted=8, dropped=0,
                     panel_mode="targeted", n=11, rt="plan review")
    drop_growth = make("growth", launches=4, accepted=8, dropped=7,
                       panel_mode="full", n=11, rt="plan review")
    rep_drop = build_effectiveness_report(drop_base + drop_growth)
    only_drop = rep_drop["cohorts"][0]
    check(
        "review_needed: drop-rate rise >10pp -> review needed with drop_rate_change_ok False (r5 F2)",
        only_drop["verdict"] == "review needed"
        and only_drop["checks"]["drop_rate_change_ok"] is False
        and only_drop["checks"]["launch_reduction_ok"] is True
        and only_drop["checks"]["accepted_change_ok"] is True,
        str(only_drop.get("checks")),
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


# ---- metrics ----
@_test("summarize_review_stats#metrics_bands")
def _t_metrics_bands(check) -> None:
    """Metrics pass over a synthetic five-loop corpus (review-loop
    exit-condition metrics plan, Task 3 Case A).

    Loop A: three rounds, findings totals 6, 4, 2, verdicts no, no, yes.
    Loop B: two rounds, totals 3, 3, cap closure on the last round.
    Loop C: one round, two findings, verdict no. Plans sized into different
    bands (small, medium, large). A fourth loop whose plan file is absent
    (one round, two findings, verdict no) and a fifth loop whose slug matches
    plan files under BOTH the plans dir and its completed subdir (one round,
    one finding, verdict no). Expected: per-round findings series 14, 7, 2;
    ready-rate one of five at the final index; cap-exhaustion share one of
    five; three loops in their derived bands with the plan-less fourth and
    the ambiguous-slug fifth both unknown; zero per-file path rows in the
    JSON. Ends with explicit temp-directory teardown.
    """
    import shutil
    import tempfile

    td = Path(tempfile.mkdtemp(prefix="review-metrics-selftest-"))
    try:
        root = td / "myrepos"
        repo = root / "metrics-repo"  # synthetic; never asserted in outputs
        plans = repo / "docs" / "history" / "plans"
        completed = plans / "completed"
        reviews = repo / "docs" / "reviews"
        for directory in (plans, completed, reviews, repo / ".ai-playbook"):
            directory.mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            "```toml\n"
            'plans_dir = "docs/history/plans/"\n'
            'plans_completed_dir = "docs/history/plans/completed/"\n'
            'reviews_dir = "docs/reviews/"\n'
            "```\n",
            encoding="utf-8",
        )

        def plan_file(directory: Path, slug: str, checkboxes: int) -> None:
            body = "\n".join("- [ ] task item" for _ in range(checkboxes))
            (directory / f"2026-09-01-{slug}.md").write_text(
                f"# {slug} plan\n\n{body}\n", encoding="utf-8"
            )

        def sidecar(
            slug: str,
            round_no: int,
            verdict: str,
            blocking_flags: list[bool],
            *,
            cap_closure: bool = False,
        ) -> None:
            payload = _metrics_v1_payload(
                slug, round_no, verdict, blocking_flags, cap_closure=cap_closure
            )
            _write_private_sidecar(
                reviews / f"2026-09-02-branch-review-{slug}-r{round_no}.stats.json",
                payload,
            )

        plan_file(plans, "alpha-feature", 3)  # small (5 or fewer)
        plan_file(plans, "beta-feature", 10)  # medium (6 to 15)
        plan_file(plans, "gamma-feature", 20)  # large (16 or more)
        # delta-feature: deliberately absent from both plans directories.
        plan_file(plans, "epsilon-feature", 7)
        plan_file(completed, "epsilon-feature", 7)  # ambiguous slug match

        sidecar("alpha-feature", 1, "no", [False] * 6)
        sidecar("alpha-feature", 2, "no", [True, True, False, False])
        sidecar("alpha-feature", 3, "yes", [True, False])
        sidecar("beta-feature", 1, "no", [False] * 3)
        sidecar("beta-feature", 2, "no", [False] * 3, cap_closure=True)
        sidecar("gamma-feature", 1, "no", [False, False])
        sidecar("delta-feature", 1, "no", [True, False])
        sidecar("epsilon-feature", 1, "no", [False])

        report = run_metrics_pass([root])
        overall = report["overall"]
        check(
            "metrics_bands: per-round findings series 14, 7, 2",
            [overall["findings_by_round"].get(i, 0) for i in (1, 2, 3)]
            == [14, 7, 2],
            str(overall["findings_by_round"]),
        )
        check(
            "metrics_bands: ready-rate one of five at the final index",
            abs(overall["ready_rate_by_round"].get(3, -1.0) - 0.2) < 1e-9,
            str(overall["ready_rate_by_round"]),
        )
        check(
            "metrics_bands: cap-exhaustion share one of five",
            report["loops"] == 5
            and overall["cap_closures"] == 1
            and abs(overall["cap_exhaustion_share"] - 0.2) < 1e-9,
            f"loops={report['loops']} cap={overall['cap_closures']}",
        )
        bands = report["bands"]
        check(
            "metrics_bands: three loops in their derived bands",
            bands["small"]["loops"] == 1
            and bands["medium"]["loops"] == 1
            and bands["large"]["loops"] == 1,
            str({b: bands[b]["loops"] for b in ("small", "medium", "large")}),
        )
        check(
            "metrics_bands: plan-less and ambiguous loops both unknown",
            bands["unknown"]["loops"] == 2
            and bands["unknown"].get("legacy_bucket_sidecars", 0) == 0,
            str(bands["unknown"]),
        )
        check(
            "metrics_bands: cap closure lands in the medium band",
            bands["medium"]["cap_closures"] == 1
            and bands["small"]["cap_closures"] == 0,
            str(bands["medium"]),
        )
        check(
            "metrics_bands: no legacy sidecars in the clean corpus",
            report["sidecars_legacy_bucket"] == 0,
            str(report["sidecars_legacy_bucket"]),
        )
        json_text = serialize_metrics_json(report).decode("utf-8")
        md_text = serialize_metrics_markdown(report).decode("utf-8")
        check(
            "metrics_bands: JSON has zero per-file path rows",
            ".stats.json" not in json_text and str(td) not in json_text,
            "per-file path data leaked into metrics JSON",
        )
        check(
            "metrics_bands: Markdown aggregate-only",
            ".stats.json" not in md_text
            and str(td) not in md_text
            and "alpha-feature" not in md_text,
            "slug or path data leaked into metrics Markdown",
        )
    finally:
        shutil.rmtree(td)

    check(
        "metrics_bands: explicit temp-directory teardown",
        not td.exists(),
        f"{td} still exists",
    )


# ---- metrics ----
@_test("summarize_review_stats#metrics_legacy_tolerance")
def _t_metrics_legacy_tolerance(check) -> None:
    """Metrics pass beside a sidecar that fails version-1 validation
    (review-loop exit-condition metrics plan, Task 3 Case B).

    One valid two-round loop sits next to a version-1 sidecar missing a
    required top-level field: the failing sidecar is counted into the
    unknown-band legacy bucket, the loop's series stays intact, and the pass
    (command layer included) still exits 0.
    """
    import shutil
    import tempfile

    td = Path(tempfile.mkdtemp(prefix="review-metrics-legacy-selftest-"))
    try:
        root = td / "myrepos"
        repo = root / "legacy-tolerance-repo"
        # No repo facts file: discovery exercises its legacy default reviews
        # directory (docs/history/reviews/) in this case.
        reviews = repo / "docs" / "history" / "reviews"
        reviews.mkdir(parents=True)
        _write_private_sidecar(
            reviews / "2026-09-02-branch-review-valid-feature-r1.stats.json",
            _metrics_v1_payload("valid-feature", 1, "no", [False] * 3),
        )
        _write_private_sidecar(
            reviews / "2026-09-02-branch-review-valid-feature-r2.stats.json",
            _metrics_v1_payload("valid-feature", 2, "yes", [False]),
        )
        failing = _metrics_v1_payload("broken-feature", 1, "no", [True])
        del failing["panel"]  # version-1 required top-level field
        _write_private_sidecar(
            reviews / "2026-09-02-branch-review-broken-feature-r1.stats.json",
            failing,
        )

        report = run_metrics_pass([root])
        check(
            "metrics_legacy_tolerance: failing sidecar in the legacy bucket",
            report["sidecars_legacy_bucket"] == 1
            and report["bands"]["unknown"].get("legacy_bucket_sidecars", 0) == 1,
            str(report["sidecars_legacy_bucket"]),
        )
        check(
            "metrics_legacy_tolerance: valid loop still aggregates",
            report["loops"] == 1
            and report["overall"]["findings_by_round"] == {1: 3, 2: 1},
            str(report["overall"]["findings_by_round"]),
        )

        # Command layer: exit 0 with both outputs written and aggregate-only.
        user_facts = td / "facts.md"
        user_facts.write_text(
            f"| `personal_projects_root` | `{td / 'myrepos'}` | x |\n",
            encoding="utf-8",
        )
        json_out = td / "metrics.json"
        md_out = td / "metrics.md"
        exit_code = cmd_metrics(user_facts, json_out, md_out)
        check(
            "metrics_legacy_tolerance: pass exits 0",
            exit_code == 0,
            str(exit_code),
        )
        check(
            "metrics_legacy_tolerance: both outputs written non-empty",
            json_out.is_file()
            and json_out.read_text(encoding="utf-8").strip() != ""
            and md_out.is_file()
            and md_out.read_text(encoding="utf-8").strip() != "",
            "metrics output missing or empty",
        )
        json_text = json_out.read_text(encoding="utf-8")
        check(
            "metrics_legacy_tolerance: JSON aggregate-only",
            ".stats.json" not in json_text and str(td) not in json_text,
            "per-file path data leaked into metrics JSON",
        )
    finally:
        shutil.rmtree(td)

    check(
        "metrics_legacy_tolerance: explicit temp-directory teardown",
        not td.exists(),
        f"{td} still exists",
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
    "summarize_review_stats#strict_audit_stale_snapshot": "lifecycle",
    "summarize_review_stats#private_permissions": "permissions",
    "summarize_review_stats#snapshot_races": "permissions",
    "summarize_review_stats#current_adapter": "aggregation",
    "summarize_review_stats#legacy_adapters": "aggregation",
    "summarize_review_stats#legacy_adapter_compat": "aggregation",
    "summarize_review_stats#current_adapter_v1": "aggregation",
    "summarize_review_stats#canonical_only_aggregation": "aggregation",
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
    "summarize_review_stats#metrics_bands": "metrics",
    "summarize_review_stats#metrics_legacy_tolerance": "metrics",
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
        help="comma-separated selftest subset tags (discovery,conservation,permissions,lifecycle,aggregation,report,release,metrics)",
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
        help="read-only strict conservation audit over sidecar content; "
        "normalizes private-file modes to 0600/0700 (stderr warning if a "
        "tighten is refused); fails on baseline problems",
    )
    parser.add_argument("--json-report", type=Path, default=None)
    parser.add_argument("--markdown-report", type=Path, default=None)
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="read-only review-corpus metrics pass: loops grouped by "
        "artifact_slug, findings decay, ready-rate, and cap-exhaustion "
        "share per complexity band; aggregate-only outputs",
    )
    parser.add_argument(
        "--metrics-json",
        metavar="PATH",
        type=Path,
        default=None,
        help="metrics output as canonical JSON (with --metrics; at least "
        "one of --metrics-json / --metrics-markdown is required)",
    )
    parser.add_argument(
        "--metrics-markdown",
        metavar="PATH",
        type=Path,
        default=None,
        help="metrics output as aggregate-only Markdown (with --metrics; "
        "at least one of --metrics-json / --metrics-markdown is required)",
    )
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

    if args.metrics:
        if args.metrics_json is None and args.metrics_markdown is None:
            sys.stderr.write(
                "--metrics requires --metrics-json and/or --metrics-markdown\n"
            )
            return 2
        return cmd_metrics(args.user_facts, args.metrics_json, args.metrics_markdown)

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
