#!/usr/bin/env python3
"""Done sweep gate runner lib: the done skill's deterministic gates as code.

Plan: ``docs/history/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md``,
Task 1. Invoked by ``scripts/done_sweep_gates.sh`` (one call per phase) and
exercised hermetically by ``scripts/test_done_sweep_gates_lib.py``.

Gate phases (contiguous slices of the done step order; judgment steps between
them stay in the skill):

- ``pre-docs``   (done Steps 1.5, 2.65, 2.648, 2.645, 2.64, 2.63, 2.62):
  plan-readiness, confluence-hygiene, doc-registry, backlog-inbox,
  review-staging, vim-swap-sweep, docs-tmp-sweep.
- ``pre-commit`` (done Step 2.7 mechanical half, 2.76, 2.8):
  sensitive-data-scan, em-dash-scan, instruction-size.

Contract:
- gate registry == the twelve absorbed steps at gate and named sub-check
  granularity (Design Invariant: gate preservation); report order is registry
  order, every gate reports even after an earlier failure, and the
  implementation runs every phase strictly sequentially in registry order (a
  permitted specialization of the concurrency contract) so reports stay
  deterministic;
- session-scoped inputs are derived mechanically (the runner cannot read chat
  context): the session window anchors on the run-start markers under
  ``{tmp_dir}/done-session/`` where the newest content-confirmed marker is the
  current run and the newest strictly older one is the previous-run anchor;
  fewer than two confirmable markers means an unanchorable window and
  conservative gating applies; the doc-registry committed-changes baseline
  anchors on the active run manifest's ``start_commit`` when a manifest is
  present (``ORIG_HEAD`` fallback otherwise), classifies
  ``start_commit..HEAD`` through the owned-commits ledgers of the run and
  every ``adopted_from`` ancestor, and keeps the ignored arm window-anchored
  in every branch (never narrowed to manifest claims);
- paths resolve via the ``facts_paths.py`` helpers with the repo root as
  anchor; validator scripts resolve env override first, then the repo-local
  ``scripts/`` copy, then the deployed runtime home copy;
- sync nothing: this runner never touches the docs branch.

Hermeticity knobs (used by the tests; harmless in production):
``DONE_SWEEP_REPO_ROOT`` (default: cwd git toplevel as given),
``DONE_SWEEP_RUNTIME_HOME`` (default: ``~/.ai-playbook``),
``DONE_SWEEP_USER_FACTS`` (default: ``<runtime_home>/facts.md``).

Stdlib only plus the repo-local ``facts_paths`` and ``validate_review_staging``
(the staging-path predicate is imported, never re-implemented).

The ``write-manifest`` sub-command writes the done Step 0 run manifest record
(``run-manifest-<run_id>.json`` next to the run-start marker); it owns no
gate and does not touch the gate registry. It also reports interrupted runs
(root-matched manifests whose ``complete`` flag is still false and which no
other manifest adopts): a retry continues an interrupted run's boundary only
through an explicit ``--adopt <run_id>`` boundary copy, never implicitly.
The ``finalize-manifest`` sub-command sets a run manifest's ``complete`` flag
to true in place (done Step 6, immediately before the done-lock release).
"""

from __future__ import annotations

import argparse
import json
import hashlib
import hmac
import os
import re
import shutil
import stat as stat_module
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths
import validate_review_staging as vrs

GIT_TIMEOUT_S = 60
SCRIPT_TIMEOUT_S = 300

# Registry: phase slices in done SKILL.md order.
PRE_DOCS_GATES = [
    "plan-readiness",
    "confluence-hygiene",
    "doc-registry",
    "backlog-inbox",
    "review-staging",
    "vim-swap-sweep",
    "docs-tmp-sweep",
    "plans-archive-twin",
]
PRE_COMMIT_GATES = [
    "sensitive-data-scan",
    "em-dash-scan",
    "instruction-size",
    "foreign-staging",
    "plans-archive-twin",
]
PHASES = {
    "pre-docs": PRE_DOCS_GATES,
    "pre-commit": PRE_COMMIT_GATES,
}

# done Step 2.7 item 2 diff-content grep patterns. Credential terms are
# intentionally assignment-shaped so domain prose such as "claim token" does
# not become a false positive while credential-like values remain blocked.
DIFF_CONTENT_PATTERNS = [
    r"/Users/",
    r"/home/",
    r"\.atlassian\.net",
    r"@[a-z]+\.(com|io|net)",
    r"(?i)\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}",
    r"(?i)\b(?:access|auth|claim|policy|refresh|session)?[_-]?token\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}",
    r"(?i)\b(?:password|secret)\s*[:=]\s*\S+",
]
CO_AUTHORED_RE = re.compile(r"co-authored-by", re.IGNORECASE)

MANIFEST_MAX_AGE_H = 24.0


# --------------------------------------------------------------------------- #
# Context and results.
# --------------------------------------------------------------------------- #
@dataclass
class GateContext:
    repo_root: Path
    plans_dir: Path
    plans_completed_dir: Path
    backlog_dir: Path
    reviews_dir: Path
    tmp_dir: Path
    runtime_home: Path
    user_facts: Path

    @classmethod
    def discover(cls, repo_root: Optional[Path] = None) -> "GateContext":
        root = Path(
            os.environ.get("DONE_SWEEP_REPO_ROOT")
            or (str(repo_root) if repo_root else os.getcwd())
        ).resolve()
        runtime_home = Path(
            os.environ.get("DONE_SWEEP_RUNTIME_HOME")
            or (Path.home() / ".ai-playbook")
        )
        user_facts = Path(
            os.environ.get("DONE_SWEEP_USER_FACTS") or (runtime_home / "facts.md")
        )
        return cls(
            repo_root=root,
            plans_dir=_resolve_dir(root, "plans_dir", "docs/history/plans"),
            plans_completed_dir=_resolve_dir(
                root, "plans_completed_dir", "docs/history/plans/completed"
            ),
            backlog_dir=_resolve_dir(root, "backlog_dir", "docs/history/backlog"),
            reviews_dir=_resolve_dir(root, "reviews_dir", "docs/reviews"),
            tmp_dir=_resolve_dir(root, "tmp_dir", "docs/tmp"),
            runtime_home=runtime_home,
            user_facts=user_facts,
        )

    @property
    def done_session_dir(self) -> Path:
        return self.tmp_dir / "done-session"

    @property
    def execute_plan_dir(self) -> Path:
        return self.tmp_dir / "execute-plan"

    @property
    def confluence_manifest_path(self) -> Path:
        # Same fixed repo-relative home the hygiene script itself uses.
        return self.repo_root / "docs" / "maintenance" / "confluence-sync-manifest.json"

    @property
    def confluence_mirror_dir(self) -> Path:
        return self.repo_root / "docs" / "history" / "context" / "confluence"

    # ---- subprocess helpers (cwd anchored at the repo root) ----
    def git(self, *args: str, input_text: Optional[str] = None):
        return subprocess.run(
            ["git", "-c", "core.quotePath=false", *args],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
            input=input_text,
        )

    def run(
        self,
        args: list[str],
        cwd: Optional[Path] = None,
        input_text: Optional[str] = None,
    ):
        return subprocess.run(
            args,
            cwd=str(cwd or self.repo_root),
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_S,
            input=input_text,
        )

    def resolve_script(self, env_var: str, name: str) -> Optional[Path]:
        """env override, then repo-local scripts/, then runtime home scripts/."""
        candidates: list[Path] = []
        env_value = os.environ.get(env_var)
        if env_value:
            candidates.append(Path(env_value))
        candidates.append(self.repo_root / "scripts" / name)
        candidates.append(self.runtime_home / "scripts" / name)
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def read_user_facts_table_key(self, key: str) -> Optional[str]:
        """Markdown table row ``| `key` | `value` |`` from the user facts doc.

        Mirrors the ``facts_paths.py`` table grammar without touching the
        module-private helper; the user facts file is home-scoped, so the
        repo-anchored public resolvers do not apply.
        """
        if not self.user_facts.is_file():
            return None
        try:
            text = self.user_facts.read_text(encoding="utf-8")
        except OSError:
            return None
        pattern = re.compile(
            r"^\|\s*`" + re.escape(key) + r"`\s*\|\s*`?([^|`]+?)`?\s*\|",
            re.MULTILINE,
        )
        match = pattern.search(text)
        return match.group(1).strip() if match else None


def _resolve_dir(root: Path, key: str, default_rel: str) -> Path:
    """Resolve a repo facts TOML key anchored at the repo root (facts_paths)."""
    raw = facts_paths.resolve_toml_key_raw(root, key)
    if raw is None:
        return (root / default_rel).resolve()
    expanded = Path(raw).expanduser()
    if not expanded.is_absolute():
        expanded = root / expanded
    return expanded.resolve()


@dataclass
class GateResult:
    gate: str
    rc: int
    message: str
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "gate": self.gate,
            "rc": self.rc,
            "message": self.message,
            "warnings": list(self.warnings),
        }


@dataclass
class RunMarker:
    path: Path
    epoch: float
    pid: int
    repo_root: str


@dataclass
class SessionWindow:
    anchored: bool
    anchor: Optional[RunMarker]
    current: Optional[RunMarker]
    start_epoch: Optional[float]
    notes: list[str] = field(default_factory=list)


@dataclass
class PlanReadinessDerivation:
    candidates: list[Path]  # repo-relative plan paths that will be gated
    exempted: list[Path]
    archived: list[Path]
    window: SessionWindow
    notes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Session window (mechanical run-start-marker identity).
# --------------------------------------------------------------------------- #
def _marker_digest_matches(recorded: str, repo_root: Path) -> bool:
    """True when ``recorded`` is a 64-hex digest of ``repo_root``'s root.

    done Step 0 records sha256 of the trailing-slash-stripped resolved repo
    root; legacy markers recorded the raw path instead (accepted for
    compatibility with pre-digest writers and vendored copies).
    """
    if not re.fullmatch(r"[0-9a-f]{64}", recorded):
        return False
    return hmac.compare_digest(recorded, _repo_root_digest(repo_root))


def _repo_root_digest(repo_root: Path) -> str:
    """The done Step 0 identity digest: sha256 of the trailing-slash-stripped
    repo root string (the same derivation the run-start marker records)."""
    return hashlib.sha256(
        str(repo_root).rstrip("/").encode("utf-8")
    ).hexdigest()


def _repo_relative(path: str, repo_root: Path) -> str:
    """Repo-relative form of ``path`` when it sits under ``repo_root``.

    The input resolves through realpath first, so a symlink-aliased spelling
    of an in-repo staging doc still relativizes; when resolution or the
    containment comparison fails (including out-of-root foreign inputs) the
    input is returned verbatim, by prescription.
    """
    try:
        resolved = os.path.realpath(path)
        root = os.path.realpath(str(repo_root))
        if resolved.startswith(root + os.sep):
            return os.path.relpath(resolved, root)
    except OSError:
        pass
    return path


def _parse_marker(path: Path, repo_root: Path) -> Optional[RunMarker]:
    """Parse one run-start marker; content must record this repo's root.

    Field order (done Step 0): first field epoch, last field PID, everything
    between is the identity token. Current writers record a 64-hex SHA-256
    digest of the trailing-slash-stripped resolved repo root; legacy markers
    recorded the raw repo-root path (spaces unambiguous), still accepted.
    """
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    fields = content.split()
    if len(fields) < 3:
        return None
    try:
        epoch = float(fields[0])
        pid = int(fields[-1])
    except ValueError:
        return None
    recorded_root = " ".join(fields[1:-1])
    if len(fields) == 3 and re.fullmatch(r"[0-9a-f]{64}", recorded_root):
        # Hex identity tokens resolve by digest comparison only, never
        # through the CWD-dependent legacy realpath arm.
        if _marker_digest_matches(recorded_root, repo_root):
            return RunMarker(
                path=path, epoch=epoch, pid=pid, repo_root=recorded_root
            )
        return None  # foreign digest: cannot anchor this repo's window
    if os.path.realpath(recorded_root) != os.path.realpath(str(repo_root)):
        return None  # cross-repo marker: cannot anchor this repo's window
    return RunMarker(path=path, epoch=epoch, pid=pid, repo_root=recorded_root)


def derive_session_window(done_session_dir: Path, repo_root: Path) -> SessionWindow:
    """Newest content-confirmed marker is the current run; the newest strictly
    older one is the previous-run anchor; fewer than two confirmable markers
    means unanchorable (conservative gating downstream)."""
    notes: list[str] = []
    markers: list[RunMarker] = []
    cross_repo = 0
    malformed = 0
    if done_session_dir.is_dir():
        for path in sorted(done_session_dir.glob("run-start-*")):
            parsed = _parse_marker(path, repo_root)
            if parsed is not None:
                markers.append(parsed)
            elif _marker_records_other_repo(path, repo_root):
                cross_repo += 1
            else:
                malformed += 1
    markers.sort(key=lambda marker: (marker.epoch, marker.path.name))
    if len(markers) < 2:
        if cross_repo:
            notes.append(
                f"{cross_repo} marker(s) record a different repository root "
                "(cross-repo done run); they cannot anchor this window"
            )
        if malformed:
            notes.append(f"{malformed} marker(s) unparseable; never guessed")
        notes.append(
            "session window unanchorable: fewer than two content-confirmed "
            "run-start markers under done-session"
        )
        current = markers[-1] if markers else None
        return SessionWindow(False, None, current, None, notes)
    current = markers[-1]
    anchor = markers[-2]
    return SessionWindow(True, anchor, current, anchor.epoch, notes)


def _marker_records_other_repo(path: Path, repo_root: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    fields = content.split()
    if len(fields) < 3:
        return False
    recorded_root = " ".join(fields[1:-1])
    if len(fields) == 3 and re.fullmatch(r"[0-9a-f]{64}", recorded_root):
        # Same short-circuit as _parse_marker: a hex token classifies by
        # digest comparison only, never through the legacy realpath arm.
        return not _marker_digest_matches(recorded_root, repo_root)
    try:
        return os.path.realpath(recorded_root) != os.path.realpath(str(repo_root))
    except OSError:
        return False


# --------------------------------------------------------------------------- #
# Run manifest (done Step 0 ownership record).
# --------------------------------------------------------------------------- #
MANIFEST_SCHEMA_VERSION = 1


@dataclass
class RunManifest:
    """The Step 0 record next to the run-start marker: run identity, the
    boundary (start commit plus pre-existing dirt), the run-owned plan and
    review paths (repo-relative), explicitly foreign review artifacts, the
    explicit adoption link, and the completion flag (false until the run
    finalizes). ``repo_root`` carries the same 64-hex identity digest the
    run-start marker records (legacy records keep the raw path and stay
    loadable through the two-arm root match)."""

    schema: int
    run_id: str
    marker: str
    created_epoch: float
    repo_root: str
    pid: int
    start_commit: str
    start_porcelain: list[str]
    owned_paths: list[str]
    owned_plan_paths: list[str]
    owned_review_paths: list[str]
    foreign_review_paths: list[str]
    adopted_from: Optional[str]
    complete: bool

    def as_dict(self) -> dict:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "marker": self.marker,
            "created_epoch": self.created_epoch,
            "repo_root": self.repo_root,
            "pid": self.pid,
            "start_commit": self.start_commit,
            "start_porcelain": list(self.start_porcelain),
            "owned_paths": list(self.owned_paths),
            "owned_plan_paths": list(self.owned_plan_paths),
            "owned_review_paths": list(self.owned_review_paths),
            "foreign_review_paths": list(self.foreign_review_paths),
            "adopted_from": self.adopted_from,
            "complete": self.complete,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> Optional["RunManifest"]:
        """Tolerant parse: a schema mismatch or a missing identity field
        degrades to None (the documented conservative fallback), never an
        exception."""
        if not isinstance(payload, dict):
            return None
        if payload.get("schema") != MANIFEST_SCHEMA_VERSION:
            return None
        run_id = payload.get("run_id")
        marker = payload.get("marker")
        start_commit = payload.get("start_commit")
        repo_root = payload.get("repo_root")
        created_epoch = payload.get("created_epoch")
        if not isinstance(run_id, str) or not run_id:
            return None
        if not isinstance(marker, str) or not marker:
            return None
        if not isinstance(start_commit, str) or not start_commit:
            return None
        if not isinstance(repo_root, str) or not repo_root:
            return None
        # F3: bool is an int subtype; a corrupt `true` must degrade to the
        # None path like any other type error, never coerce to 1.0 / 1.
        if isinstance(created_epoch, bool) or not isinstance(
            created_epoch, (int, float)
        ):
            return None

        def str_list(key: str) -> list[str]:
            value = payload.get(key)
            if not isinstance(value, list):
                return []
            return [item for item in value if isinstance(item, str)]

        adopted = payload.get("adopted_from")
        if not isinstance(adopted, str):
            adopted = None
        return cls(
            schema=MANIFEST_SCHEMA_VERSION,
            run_id=run_id,
            marker=marker,
            created_epoch=float(created_epoch),
            repo_root=repo_root,
            pid=(
                payload.get("pid")
                if isinstance(payload.get("pid"), int)
                and not isinstance(payload.get("pid"), bool)
                else -1
            ),
            start_commit=start_commit,
            start_porcelain=str_list("start_porcelain"),
            owned_paths=str_list("owned_paths"),
            owned_plan_paths=str_list("owned_plan_paths"),
            owned_review_paths=str_list("owned_review_paths"),
            foreign_review_paths=str_list("foreign_review_paths"),
            adopted_from=adopted,
            complete=bool(payload.get("complete", False)),
        )


def _new_run_id(now: Optional[float] = None) -> str:
    """Unique within and across runs: UTC second stamp plus a random suffix."""
    stamp = datetime.fromtimestamp(
        time.time() if now is None else now, tz=timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")
    return stamp + "-" + uuid.uuid4().hex[:12]


def _manifest_path(done_session_dir: Path, run_id: str) -> Path:
    return done_session_dir / f"run-manifest-{run_id}.json"


def write_run_manifest(manifest: RunManifest, done_session_dir: Path) -> Path:
    """Serialize the record and atomically replace the final file: a reader
    observes either the absent or the complete manifest, never a partial one."""
    done_session_dir.mkdir(parents=True, exist_ok=True)
    final = _manifest_path(done_session_dir, manifest.run_id)
    tmp = done_session_dir / (final.name + ".tmp")
    payload = json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n"
    try:
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, final)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return final


def _manifest_root_matches(recorded_root: str, repo_root: Path) -> bool:
    """Content-confirmed root matching, two arms like the run-start markers:
    a 64-hex recorded root compares against this repo's identity digest;
    anything else (a legacy raw-path record) keeps the realpath comparison,
    so a manifest from another checkout of the same repo is never this run's
    record and pre-digest manifests stay loadable."""
    if re.fullmatch(r"[0-9a-f]{64}", recorded_root):
        return hmac.compare_digest(recorded_root, _repo_root_digest(repo_root))
    try:
        return os.path.realpath(recorded_root) == os.path.realpath(str(repo_root))
    except OSError:
        return False


def load_run_manifest(
    done_session_dir: Path,
    repo_root: Path,
    window: SessionWindow,
    warnings: Optional[list[str]] = None,
) -> Optional[RunManifest]:
    """Return the manifest bound to the window's newest content-confirmed
    marker, root-matched content-wise. None when there is no current marker,
    no manifest, a foreign repo_root, a schema mismatch, or an unreadable
    record (conservative fallback downstream); never raises.

    F10: an unparseable or schema-invalid ``run-manifest-*.json`` is never
    silently skipped - when ``warnings`` is a list, each skipped corrupt
    record is named (file plus reason) so an undead run leaves a trace."""
    if window is None or window.current is None:
        return None
    if not done_session_dir.is_dir():
        return None
    marker_name = window.current.path.name
    best: Optional[RunManifest] = None
    for path in sorted(done_session_dir.glob("run-manifest-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            if warnings is not None:
                warnings.append(
                    f"corrupt run manifest skipped: {path.name} "
                    f"(unparseable: {exc})"
                )
            continue
        manifest = RunManifest.from_dict(payload)
        if manifest is None:
            if warnings is not None:
                warnings.append(
                    f"corrupt run manifest skipped: {path.name} "
                    "(schema or field validation failed)"
                )
            continue
        if manifest.marker != marker_name:
            continue
        if not _manifest_root_matches(manifest.repo_root, repo_root):
            continue
        if best is None or manifest.created_epoch > best.created_epoch:
            best = manifest
    return best


def _dedup_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _read_manifest_by_run_id(
    done_session_dir: Path, run_id: str
) -> Optional[RunManifest]:
    """Parse ``run-manifest-<run_id>.json``; None when the run_id is empty or
    not a bare filename, the file is absent, unreadable, or a schema
    mismatch; never raises."""
    if not run_id or Path(run_id).name != run_id:
        return None
    path = _manifest_path(done_session_dir, run_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return RunManifest.from_dict(payload)


def _detect_interrupted_runs(
    done_session_dir: Path, repo_root: Path, warnings: Optional[list[str]] = None
) -> list[RunManifest]:
    """Every root-matched manifest whose ``complete`` flag is still false and
    which no other manifest adopts (an ``adopted_from`` link names it): the
    interrupted runs this Step 0 reports. A finalized (``complete`` true)
    manifest is never an orphan - that is what keeps a completed commit-less
    run from misfiring the detection - and adoption is itself the suppression
    record. Unreadable and foreign-root records are skipped, never raised;
    a corrupt record is named through ``warnings`` when provided (F10)."""
    manifests: list[RunManifest] = []
    if not done_session_dir.is_dir():
        return manifests
    for path in sorted(done_session_dir.glob("run-manifest-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            if warnings is not None:
                warnings.append(
                    f"corrupt run manifest skipped: {path.name} "
                    f"(unparseable: {exc})"
                )
            continue
        manifest = RunManifest.from_dict(payload)
        if manifest is None:
            if warnings is not None:
                warnings.append(
                    f"corrupt run manifest skipped: {path.name} "
                    "(schema or field validation failed)"
                )
            continue
        if not _manifest_root_matches(manifest.repo_root, repo_root):
            continue
        manifests.append(manifest)
    adopted = {m.adopted_from for m in manifests if m.adopted_from}
    return [m for m in manifests if not m.complete and m.run_id not in adopted]


def _adopted_chain_run_ids(
    done_session_dir: Path, manifest: RunManifest, repo_root: Optional[Path] = None
) -> tuple[list[str], list[str]]:
    """The run's run_id followed by every ``adopted_from`` ancestor, oldest
    last: the ownership chain whose owned-commits ledgers the gate-side
    classification consults. A missing ancestor manifest ends the walk (its
    own ledger still counts, named by the link); a cycle is cut, never
    walked forever.

    F5: when ``repo_root`` is given, each ancestor manifest's recorded repo
    root is verified against it; a foreign-root ancestor ends the walk with a
    named warning. Stopping can only narrow the OWNED (checked) set - never
    suppress a check - and the walk stops rather than trusting a record from
    another repository.

    Returns ``(chain, warnings)``."""
    chain = [manifest.run_id]
    warnings: list[str] = []
    seen = {manifest.run_id}
    parent_id = manifest.adopted_from
    while parent_id and parent_id not in seen:
        parent = _read_manifest_by_run_id(done_session_dir, parent_id)
        if parent is not None and repo_root is not None and not _manifest_root_matches(
            parent.repo_root, repo_root
        ):
            warnings.append(
                "adopted-chain ancestor "
                f"{parent_id} records a different repo root ({parent.repo_root}); "
                "ending the walk there (foreign-root records are never trusted; "
                "the narrowed owned set only over-checks, never suppresses)"
            )
            break
        chain.append(parent_id)
        seen.add(parent_id)
        parent_id = parent.adopted_from if parent is not None else None
    return chain, warnings


# --------------------------------------------------------------------------- #
# Git status parsing helpers (porcelain + ignored-matching arms).
# --------------------------------------------------------------------------- #
def _porcelain_lines(ctx: GateContext, pathspec: str) -> list[str]:
    """Verbatim non-ignored porcelain rows over a pathspec (empty on git
    failure): ``XY PATH`` with the status letters intact, renames as
    ``R  old -> new``.

    The doc-registry check-writes stdin union must carry these rows
    verbatim: the change-type letters are what bound the registered-src
    exemption to the archive transition, so that union is never
    downgraded to name-only output. Path-only consumers use
    ``_porcelain_paths``, which strips the letters.
    """
    proc = ctx.git("status", "--porcelain", "-uall", "--", pathspec)
    if proc.returncode != 0:
        return []
    return [
        line
        for line in proc.stdout.splitlines()
        if len(line) >= 4 and line[:2] != "!!"
    ]


def _ignored_paths(ctx: GateContext, pathspec: str) -> list[str]:
    """Per-file ignored set over a pathspec via ``ls-files --others
    --ignored --exclude-standard``; exactly the files the ignored-matching
    arm of ``git status --porcelain --ignored=matching`` marks ``!!`` (that
    arm collapses an entirely-ignored untracked directory to a single
    ``!! dir/`` entry, never descending)."""
    proc = ctx.git(
        "ls-files", "--others", "--ignored", "--exclude-standard", "--", pathspec
    )
    if proc.returncode != 0:
        return []
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def _session_ignored_paths(ctx: GateContext, paths: list[str]) -> list[str]:
    """Keep only ignored files touched during the anchored done session.

    Git cannot report change types for files that remain outside the index, so
    ignored paths need the same session-window fence used by the other gates.
    When the window is unanchorable, retain the conservative all-ignored set.
    """
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    if not window.anchored:
        return paths
    start = window.start_epoch or 0.0
    filtered: list[str] = []
    for rel in paths:
        try:
            if (ctx.repo_root / rel).stat().st_mtime >= start:
                filtered.append(rel)
        except OSError:
            # Keep unreadable paths conservative rather than silently dropping
            # a possible write from the registry gate.
            filtered.append(rel)
    return filtered


def _unquote_porcelain_path(path: str) -> str:
    """Strip git's C-style quoting from a porcelain path (F9): git wraps a
    path with special characters in double quotes and escapes ``"`` ``\\``
    tab newline CR inside, so the verbatim row keeps literal quote characters
    that no filesystem path carries."""
    if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
        body = path[1:-1]
        return (
            body.replace("\\\\", "\x00")
            .replace('\\"', '"')
            .replace("\\t", "\t")
            .replace("\\n", "\n")
            .replace("\\r", "\r")
            .replace("\x00", "\\")
        )
    return path


def _porcelain_paths(ctx: GateContext, pathspec: str) -> tuple[list[str], list[str]]:
    """Porcelain plus ignored-matching arms over a pathspec; returns
    (tracked_or_untracked_paths, ignored_paths).

    Name-only convenience over ``_porcelain_lines``: status letters are
    stripped and a rename row keeps only its new side; a C-style-quoted row
    (git quotes paths with special characters) is unquoted so the real
    filesystem name survives (F9 - a quoted rename destination must stay in
    the claim-or-foreign universe). Gates whose contract needs the change
    types (doc-registry check-writes stdin) must use ``_porcelain_lines`` +
    ``_ignored_paths`` instead, which carry rows verbatim.
    """
    ordinary: list[str] = []
    proc = ctx.git("status", "--porcelain", "-uall", "--", pathspec)
    if proc.returncode != 0:
        return ordinary, []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        rest = line[3:]
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        if xy != "!!":
            ordinary.append(_unquote_porcelain_path(rest))
    return ordinary, _ignored_paths(ctx, pathspec)


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


# --------------------------------------------------------------------------- #
# Gate: plan-readiness (done Step 1.5).
# --------------------------------------------------------------------------- #
def _parse_marker_time(text: str) -> Optional[datetime]:
    raw = text.strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _manifest_exempts(ctx: GateContext, plan_rel: Path) -> bool:
    """execute-plan mechanical exemption: active manifest with a fresh
    ``updated:`` line (no older than 24h). Stale or absent updated: never
    exempts."""
    slug = plan_rel.stem
    manifest = ctx.execute_plan_dir / slug / "manifest.md"
    if not manifest.is_file():
        return False
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return False
    state = None
    updated: Optional[datetime] = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("workflow_state:"):
            state = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("updated:"):
            updated = _parse_marker_time(stripped.split(":", 1)[1])
    if state != "active" or updated is None:
        return False
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - updated).total_seconds() / 3600.0
    return 0.0 <= age_hours <= MANIFEST_MAX_AGE_H


def derive_plan_readiness_candidates(ctx: GateContext) -> PlanReadinessDerivation:
    """Mechanical candidate derivation for done Step 1.5 (see plan Task 1)."""
    notes: list[str] = []
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    plans_rel = ctx.plans_dir.relative_to(ctx.repo_root) if _is_relative_to(
        ctx.plans_dir, ctx.repo_root
    ) else ctx.plans_dir
    completed_prefix = None
    if _is_relative_to(ctx.plans_completed_dir, ctx.repo_root):
        completed_prefix = str(
            ctx.plans_completed_dir.resolve().relative_to(ctx.repo_root.resolve())
        )
    # Rejected archive: docs/history/plans/rejected/ holds plans rejected by
    # explicit decision. It is archive surface like the completed dir:
    # never a readiness candidate, and only its OWN deliverable lines are
    # pruned (see docs/history/plans/rejected/README.md).
    rejected_dir = ctx.plans_dir / "rejected"
    rejected_prefix = None
    if _is_relative_to(rejected_dir, ctx.repo_root):
        rejected_prefix = str(
            rejected_dir.resolve().relative_to(ctx.repo_root.resolve())
        )

    deliverables: list[str] = []
    deliverables_path = ctx.done_session_dir / "plan-deliverables.txt"
    if deliverables_path.is_file():
        try:
            deliverables = [
                ln.strip()
                for ln in deliverables_path.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
        except OSError:
            deliverables = []

    ordinary, ignored = _porcelain_paths(ctx, str(plans_rel))
    under_plans = lambda p: _is_relative_to(ctx.repo_root / p, ctx.plans_dir)
    under_completed = (
        lambda p: completed_prefix is not None and p.startswith(completed_prefix + "/")
    )
    under_rejected = (
        lambda p: rejected_prefix is not None and p.startswith(rejected_prefix + "/")
    )
    under_archive = lambda p: under_completed(p) or under_rejected(p)

    candidates: set[str] = set()
    archived: list[str] = []
    exempted: list[str] = []

    for rel in ordinary:
        if under_archive(rel) or not under_plans(rel):
            continue
        if (ctx.repo_root / rel).exists():
            candidates.add(rel)

    deliverables_set = set(deliverables)
    for rel in ignored:
        if under_archive(rel) or not under_plans(rel):
            continue
        if rel in deliverables_set:
            candidates.add(rel)
            continue
        if not window.anchored:
            # Conservative gating: unanchorable window treats every `!!`
            # plan as this session's deliverable.
            candidates.add(rel)
            notes.append(f"conservative gating: gitignored-arm plan {rel}")
            continue
        try:
            mtime = (ctx.repo_root / rel).stat().st_mtime
        except OSError:
            continue
        if mtime >= (window.start_epoch or 0.0):
            candidates.add(rel)

    for rel in deliverables:
        if under_archive(rel):
            archived.append(rel)
            continue
        if not (ctx.repo_root / rel).exists():
            archived.append(rel)
            continue
        if under_plans(rel):
            candidates.add(rel)

    final: list[Path] = []
    for rel in sorted(candidates):
        plan_rel = Path(rel)
        if _manifest_exempts(ctx, plan_rel):
            exempted.append(rel)
            continue
        final.append(plan_rel)

    return PlanReadinessDerivation(
        candidates=final,
        exempted=[Path(p) for p in sorted(exempted)],
        archived=[Path(p) for p in sorted(set(archived))],
        window=window,
        notes=notes,
    )


def _prune_deliverables(ctx: GateContext, remove: set[str]) -> None:
    """Remove exactly the named lines from plan-deliverables.txt (Step 1.5
    removal rule); other lines are preserved in order."""
    path = ctx.done_session_dir / "plan-deliverables.txt"
    if not path.is_file() or not remove:
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    kept = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and stripped in remove:
            continue
        kept.append(line)
    try:
        path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    except OSError:
        pass


def gate_plan_readiness(ctx: GateContext) -> GateResult:
    gate = "plan-readiness"
    derivation = derive_plan_readiness_candidates(ctx)
    remove: set[str] = {str(p) for p in derivation.exempted}
    remove.update(str(p) for p in derivation.archived)
    if not derivation.candidates:
        _prune_deliverables(ctx, remove)
        detail = ""
        if derivation.archived:
            detail = (
                " (archived deliverable lines pruned: "
                + ", ".join(str(p) for p in derivation.archived)
                + ")"
            )
        return GateResult(
            gate, 0, "no gated plan-deliverable candidates this session" + detail,
            warnings=[],
        )

    validator = ctx.resolve_script("PLAN_READINESS_VALIDATOR", "plan_readiness.py")
    if validator is None:
        return GateResult(
            gate,
            1,
            "deployment gap: plan readiness validator absent at every resolved "
            "path (repo-local scripts/plan_readiness.py and runtime copy); "
            "remedy: cp scripts/plan_readiness.py plus siblings "
            "(validate_review_staging.py, facts_paths.py) to the runtime home; "
            "never use the recorded-stop exception for a deployment gap",
            warnings=[],
        )

    passed: list[str] = []
    failed: list[tuple[str, str]] = []
    for plan_rel in derivation.candidates:
        proc = ctx.run(
            [sys.executable, str(validator), str(ctx.repo_root / plan_rel)],
            cwd=ctx.repo_root,
        )
        if proc.returncode == 0:
            passed.append(str(plan_rel))
        else:
            stdout_rows = (proc.stdout or "").strip().splitlines()
            stderr_rows = (proc.stderr or "").strip().splitlines()
            traceback_header = bool(stdout_rows) and stdout_rows[0].startswith(
                "Traceback (most recent call last):"
            )
            if stdout_rows and not traceback_header:
                first_failure = stdout_rows[0]
            elif stderr_rows:
                # A crashed validator prints its traceback on stdout and its
                # message on stderr: report the message, never the bare
                # traceback header.
                first_failure = stderr_rows[0]
            elif stdout_rows:
                first_failure = stdout_rows[-1]
            else:
                first_failure = "no output"
            failed.append((str(plan_rel), first_failure))

    remove.update(passed)
    _prune_deliverables(ctx, remove)

    parts = [
        f"passed={len(passed)}",
        f"exempted={len(derivation.exempted)}",
        f"archived={len(derivation.archived)}",
        f"failed={len(failed)}",
    ]
    message = "plan readiness: " + ", ".join(parts)
    if failed:
        message += "; first failures: " + "; ".join(
            f"{plan}: {reason}" for plan, reason in failed[:3]
        )
        return GateResult(gate, 1, message, warnings=[])
    return GateResult(gate, 0, message, warnings=[])


# --------------------------------------------------------------------------- #
# Gate: confluence-hygiene (done Step 2.65).
# --------------------------------------------------------------------------- #
def _confluence_triggered(ctx: GateContext) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if ctx.confluence_manifest_path.is_file():
        reasons.append("confluence sync manifest exists")
    ordinary, ignored = _porcelain_paths(ctx, "docs/history/context/confluence")
    if ordinary or ignored:
        reasons.append("porcelain/ignored paths under docs/history/context/confluence")
    if ctx.confluence_mirror_dir.is_dir():
        window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
        for path in ctx.confluence_mirror_dir.rglob("*.md"):
            if not window.anchored:
                break
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if mtime >= (window.start_epoch or 0.0):
                reasons.append("confluence mirror path touched in session window")
                break
    tmp_dir = ctx.repo_root / "docs" / "tmp"
    if tmp_dir.is_dir():
        if list(tmp_dir.glob("*-cf-out.md")):
            reasons.append("ephemeral *-cf-out.md snapshot under docs/tmp")
        if any(tmp_dir.rglob("__pycache__")):
            reasons.append("__pycache__ under docs/tmp")
    return bool(reasons), reasons


def gate_confluence_hygiene(ctx: GateContext) -> GateResult:
    gate = "confluence-hygiene"
    triggered, reasons = _confluence_triggered(ctx)
    if not triggered:
        return GateResult(
            gate,
            0,
            "no-op (no confluence manifest, no mirror touches, no ephemeral "
            "docs/tmp snapshots)",
            warnings=[],
        )
    script = ctx.resolve_script(
        "CONFLUENCE_MIRROR_HYGIENE_SCRIPT", "confluence-mirror-hygiene.sh"
    )
    if script is None:
        # Fail closed (deployment-gap signature semantics, same as
        # plan-readiness): the base inline invocation failed loud when the
        # script was missing, so warn-and-continue would silently disarm the
        # hygiene gate.
        message = (
            "deployment gap: confluence-mirror-hygiene.sh absent at every "
            "resolved path (env override, repo-local scripts/, runtime home "
            "copy) while its run-when triggers are live ("
            + "; ".join(reasons)
            + "); remedy: deploy the script to the runtime home scripts/ "
            "directory; never use the recorded-stop exception for a "
            "deployment gap"
        )
        return GateResult(gate, 1, message, warnings=[])

    def tail(text: str, lines: int = 12) -> str:
        rows = [row for row in (text or "").strip().splitlines() if row.strip()]
        return " | ".join(rows[-lines:])

    audit = ctx.run(["bash", str(script), "audit-cf-out"], cwd=ctx.repo_root)
    if audit.returncode != 0:
        return GateResult(
            gate,
            1,
            "audit-cf-out blocked (NEEDS_UPGRADE/UNMAPPED; judgment stays in "
            f"the done skill): {tail(audit.stdout)} {tail(audit.stderr, 3)}",
            warnings=[],
        )
    arm_results = [f"audit-cf-out ok: {tail(audit.stdout, 2)}"]
    if ctx.confluence_manifest_path.is_file():
        validate = ctx.run(["bash", str(script), "validate"], cwd=ctx.repo_root)
        if validate.returncode != 0:
            return GateResult(
                gate,
                1,
                f"confluence validate failed: {tail(validate.stdout)}",
                warnings=[],
            )
        arm_results.append("validate ok")
    cleanup = ctx.run(["bash", str(script), "cleanup"], cwd=ctx.repo_root)
    if cleanup.returncode != 0:
        return GateResult(
            gate,
            1,
            f"confluence cleanup failed: {tail(cleanup.stdout)}",
            warnings=[],
        )
    arm_results.append("cleanup ok")
    return GateResult(gate, 0, "confluence hygiene: " + "; ".join(arm_results), warnings=[])


# --------------------------------------------------------------------------- #
# Gate: doc-registry (done Step 2.648).
# --------------------------------------------------------------------------- #
def _owned_commits_ledger_path(done_session_dir: Path, run_id: str) -> Path:
    """A run's owned-commits ledger written by the done skill (Step 1 and
    Step 3 commit sites), keyed by that run's run_id."""
    return done_session_dir / f"owned-commits-{run_id}.txt"


def _cumulative_range_rows(ctx: GateContext, base: str) -> Optional[list[str]]:
    """The cumulative ``base..HEAD`` name-status rows, or None when the range
    itself is unreadable (the shared conservative-fallback feeder for the
    committed arm)."""
    proc = ctx.git("diff", "--name-status", "--no-renames", base, "HEAD")
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _full_head_tree_rows(ctx: GateContext) -> list[str]:
    """Every committed file in HEAD as ``A<TAB>path`` rows (HEAD's tree
    diffed against the empty tree): the last conservative tier when neither
    the window nor its base is readable, so the committed arm cannot be
    emptied by a git failure."""
    empty_tree = ctx.git("hash-object", "-t", "tree", os.devnull)
    if empty_tree.returncode != 0:
        return []
    proc = ctx.git(
        "diff", "--name-status", "--no-renames", empty_tree.stdout.strip(), "HEAD"
    )
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _classify_committed_range(
    ctx: GateContext, base: str, ledger_paths: list[Path]
) -> tuple[list[str], list[str]]:
    """Classify ``base..HEAD`` commits through the owned-commits ledgers.

    ``ledger_paths`` carries the active run's ledger plus every ``adopted_from``
    ancestor's ledger (the adoption chain), so commits an adopted interrupted
    run already made stay owned for the adopting retry.

    Returns ``(owned_rows, report_lines)``: the owned commits' own name-status
    rows (the same ``A/M/D<TAB>path`` form the cumulative range diff uses)
    plus non-failing report lines. A reachable ledger entry is owned; a
    ledger entry not reachable from HEAD is stale-reported and skipped; a
    window commit absent from every ledger is foreign: excluded from the write
    set with a named report line (foreign artifacts are preserved and
    reported, never gate failures). A git failure keeps the conservative
    inclusion (the cumulative range rows, then the full HEAD tree when the
    base itself is unreadable) rather than silently narrowing the protection
    surface: on any window-level git failure no owned/foreign classification
    runs at all. The same stance applies to an unreadable ledger: a ledger
    that exists but cannot be read (permissions, a non-regular file in its
    place) is not proof of an empty record, so its name is reported and the
    conservative cumulative range rows are kept instead of classifying
    against a partial ownership record; only an absent ledger counts as an
    empty one.
    """
    report: list[str] = []
    rev_list = ctx.git("rev-list", f"{base}..HEAD")
    if rev_list.returncode != 0:
        # Conservative fallback (the window-level twin of the per-commit
        # diff-tree fallback below): the window itself is unreadable, so
        # classification must not run; the cumulative range rows over-include
        # instead of silently dropping the entire committed arm.
        report.append(
            "committed window unreadable (rev-list failed); keeping the "
            f"conservative cumulative range rows ({base}..HEAD)"
        )
        rows = _cumulative_range_rows(ctx, base)
        if rows is not None:
            return rows, report
        # The base itself is unreadable (for example a corrupt manifest
        # start_commit): fall through to the full HEAD tree.
        report.append(
            "cumulative range diff failed too; keeping the conservative "
            "full-HEAD-tree rows so the committed arm stays checked"
        )
        return _full_head_tree_rows(ctx), report
    window_commits = [
        line.strip() for line in rev_list.stdout.splitlines() if line.strip()
    ]
    raw_entries: list[str] = []
    seen_entries: set[str] = set()
    unreadable_ledgers: list[Path] = []
    for ledger_path in ledger_paths:
        # F11: lstat instead of exists() - a dangling symlink (or a stat
        # denial) must read as present-but-unreadable, never as an absent
        # (empty) ledger folding the run's own commits into the foreign set.
        try:
            ledger_stat = ledger_path.lstat()
        except FileNotFoundError:
            # An absent ledger is an empty one (the run recorded no commits
            # yet), not an unreadable one.
            continue
        except OSError:
            unreadable_ledgers.append(ledger_path)
            continue
        if not stat_module.S_ISREG(ledger_stat.st_mode):
            unreadable_ledgers.append(ledger_path)
            continue
        try:
            ledger_lines = [
                line.strip()
                for line in ledger_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except OSError:
            unreadable_ledgers.append(ledger_path)
            continue
        for entry in ledger_lines:
            if entry not in seen_entries:
                seen_entries.add(entry)
                raw_entries.append(entry)
    if unreadable_ledgers:
        # A ledger is the ownership record: when one in the chain exists but
        # cannot be read, every window commit is potentially owned, so
        # classifying against the remaining readable ledgers could misreport
        # the run's own ledger-claimed commits as foreign and narrow the
        # check-write surface. Keep the conservative inclusion instead (the
        # ledger-read twin of the window-level fallback above): the
        # cumulative range rows over-include rather than silently dropping
        # owned writes.
        for ledger_path in unreadable_ledgers:
            report.append(
                "owned-commits ledger unreadable; keeping the conservative "
                f"cumulative range rows ({base}..HEAD) instead of classifying "
                f"against a partial ownership record: {ledger_path}"
            )
        rows = _cumulative_range_rows(ctx, base)
        if rows is not None:
            return rows, report
        report.append(
            "cumulative range diff failed too; keeping the conservative "
            "full-HEAD-tree rows so the committed arm stays checked"
        )
        return _full_head_tree_rows(ctx), report
    ledger: set[str] = set()
    for entry in raw_entries:
        resolved = ctx.git("rev-parse", "-q", "--verify", f"{entry}^{{commit}}")
        if resolved.returncode != 0:
            report.append(
                "stale owned-commits ledger entry skipped (sha not "
                f"resolvable as a commit): {entry}"
            )
            continue
        ledger.add(resolved.stdout.strip())
    owned_rows: list[str] = []
    for commit in window_commits:
        if commit not in ledger:
            report.append(
                "foreign commit excluded from the registry write set (owner "
                f"class: foreign or peer run): {commit}"
            )
            continue
        # ``-m`` makes merge commits contribute their rows too (the diff vs
        # each parent); without it diff-tree emits nothing for a merge and an
        # owned merge's writes silently leave the check surface. Combined
        # with ``--root`` the flag is inert for normal and root commits.
        show = ctx.git(
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-status",
            "--no-renames",
            "-m",
            "-r",
            commit,
        )
        if show.returncode != 0:
            # Conservative fallback: over-include the whole range rather than
            # silently dropping an owned commit's writes from the check.
            cumulative = _cumulative_range_rows(ctx, base)
            if cumulative is not None:
                owned_rows.extend(cumulative)
            continue
        owned_rows.extend(line for line in show.stdout.splitlines() if line.strip())
    for entry in sorted(ledger):
        ancestor = ctx.git("merge-base", "--is-ancestor", entry, "HEAD")
        if ancestor.returncode == 1:
            report.append(
                "stale owned-commits ledger entry skipped (not reachable from "
                f"HEAD): {entry}"
            )
        elif ancestor.returncode != 0:
            # A git failure is not a staleness answer: exit 1 is the only
            # clean ``is not an ancestor`` verdict, so any other failure
            # keeps the entry reachable and reports unknown reachability
            # instead of claiming stale.
            report.append(
                "owned-commits ledger reachability unknown (merge-base "
                f"failed; the entry stays checked as reachable): {entry}"
            )
    return owned_rows, report


def gate_doc_registry(ctx: GateContext) -> GateResult:
    gate = "doc-registry"
    validator = ctx.resolve_script(
        "DOC_REGISTRY_VALIDATOR_SCRIPT", "doc_registry_validator.py"
    )
    if validator is None:
        message = (
            "doc_registry_validator.py absent at every resolved path; "
            "report-once-and-continue (Step 2.648 fail-open)"
        )
        return GateResult(gate, 0, message, warnings=[message])

    validate = ctx.run([sys.executable, str(validator), "validate"], cwd=ctx.repo_root)
    if validate.returncode != 0:
        tail_rows = [
            row
            for row in (validate.stdout or "").strip().splitlines()
            if row.strip()
        ][-10:]
        return GateResult(
            gate,
            1,
            "doc registry validate failed (hard findings): "
            + " | ".join(tail_rows),
            warnings=[],
        )

    # Committed-changes baseline: the active run manifest's start_commit when
    # a manifest is present (per-run boundary, so a failed earlier run can
    # never widen this run's checked set), else the conservative ORIG_HEAD
    # fallback (legacy tree, foreign repo, interrupted write). The committed
    # window is classified through the owned-commits ledgers of the run and
    # every adopted_from ancestor (an adopted interrupted run's commits stay
    # owned for the adopting retry); the ignored arm stays window-anchored in
    # every branch (never narrowed to manifest claims).
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    warnings: list[str] = []
    manifest = load_run_manifest(
        ctx.done_session_dir, ctx.repo_root, window, warnings=warnings
    )
    owned_rows: Optional[list[str]] = None
    base = "ORIG_HEAD"
    if manifest is not None:
        base = manifest.start_commit
        if manifest.start_porcelain:
            warnings.append(
                "pre-existing dirt recorded at Step 0 (reported, never "
                "attributed to this run): "
                + " | ".join(manifest.start_porcelain)
            )
        chain, chain_warnings = _adopted_chain_run_ids(
            ctx.done_session_dir, manifest, repo_root=ctx.repo_root
        )
        warnings.extend(chain_warnings)
        if manifest.adopted_from:
            warnings.append(
                "adopted boundary: this run continues interrupted run "
                f"{manifest.adopted_from}; owned-commits ledgers consulted "
                "for the full adoption chain: " + ", ".join(chain)
            )
        rows, ledger_lines = _classify_committed_range(
            ctx,
            base,
            [
                _owned_commits_ledger_path(ctx.done_session_dir, run_id)
                for run_id in chain
            ],
        )
        owned_rows = rows
        warnings.extend(ledger_lines)
    verify = ctx.git("rev-parse", "-q", "--verify", f"{base}^{{commit}}")
    if verify.returncode != 0:
        base = ctx.git("rev-parse", "HEAD").stdout.strip()

    # Change-typed union, never a name-only downgrade (base Step 2.648):
    # porcelain rows carry their XY status letters verbatim (a rename row
    # is ``R  old -> new`` so the validator's parse_change_line gates both
    # sides), committed rows keep their ``A/M/D<TAB>path`` name-status form
    # (the manifest branch contributes the owned commits' own rows, with the
    # conservative cumulative/full-tree fallback when git cannot classify;
    # the no-manifest branch keeps the cumulative ``base..HEAD`` diff), and
    # ignored files (which have no change type) stay bare rows.
    porcelain_rows = _porcelain_lines(ctx, ".")
    ignored = _session_ignored_paths(ctx, _ignored_paths(ctx, "."))
    if owned_rows is not None:
        name_status = owned_rows
    else:
        name_status_proc = ctx.git("diff", "--name-status", "--no-renames", base, "HEAD")
        name_status = [
            row for row in name_status_proc.stdout.splitlines() if row.strip()
        ]
    union = sorted(set(porcelain_rows) | set(ignored) | set(name_status))
    arm_note = "check-writes skipped (no changed files)"
    if union:
        check = ctx.run(
            [sys.executable, str(validator), "check-writes", "--stdin"],
            cwd=ctx.repo_root,
            input_text="\n".join(union) + "\n",
        )
        if check.returncode != 0:
            tail_rows = [
                row
                for row in (check.stdout or "").strip().splitlines()
                if row.strip()
            ][-10:]
            return GateResult(
                gate,
                1,
                "doc registry check-writes flagged protected writes: "
                + " | ".join(tail_rows),
                warnings=warnings,
            )
        arm_note = f"check-writes ok over {len(union)} changed paths"

    return GateResult(
        gate, 0, f"doc registry: validate ok; {arm_note}", warnings=warnings
    )


# --------------------------------------------------------------------------- #
# Gate: backlog-inbox (done Step 2.645).
# --------------------------------------------------------------------------- #
def gate_backlog_inbox(ctx: GateContext) -> GateResult:
    gate = "backlog-inbox"
    validator = ctx.resolve_script("BACKLOG_LOCATION_GATE", "check_backlog_inbox_location.py")
    if validator is None:
        warning = (
            "warning: check_backlog_inbox_location.py not found; skipping "
            "backlog inbox location gate"
        )
        return GateResult(gate, 0, warning, warnings=[warning])
    proc = ctx.run([sys.executable, str(validator)], cwd=ctx.repo_root)
    if proc.returncode != 0:
        tail_rows = [
            row for row in (proc.stdout or "").strip().splitlines() if row.strip()
        ][-10:]
        return GateResult(
            gate,
            1,
            "backlog inbox location gate failed: " + " | ".join(tail_rows),
            warnings=[],
        )
    return GateResult(gate, 0, "backlog inbox location gate passed", warnings=[])


# --------------------------------------------------------------------------- #
# Gate: review-staging (done Step 2.64).
# --------------------------------------------------------------------------- #
def _all_staging_review_paths(ctx: GateContext) -> list[Path]:
    """Every on-disk staging doc under reviews_dir per the porcelain plus
    ignored-matching arms, filtered by the validator's own staging-path
    predicate only (NO session-window mtime filter): this is the Step 0
    claim-or-foreign enumeration universe, and the windowed derivation below
    narrows it."""
    reviews_rel = (
        ctx.reviews_dir.relative_to(ctx.repo_root)
        if _is_relative_to(ctx.reviews_dir, ctx.repo_root)
        else ctx.reviews_dir
    )
    ordinary, ignored = _porcelain_paths(ctx, str(reviews_rel))
    seen: set[str] = set()
    candidates: list[Path] = []
    for rel in ordinary + ignored:
        if rel in seen:
            continue
        seen.add(rel)
        absolute = ctx.repo_root / rel
        if not absolute.is_file():
            continue
        if not _is_relative_to(absolute, ctx.reviews_dir):
            continue
        if not vrs.is_staging_review_path(absolute):
            continue
        candidates.append(absolute)
    return sorted(candidates)


@dataclass
class ReviewStagingScope:
    """The review-staging gate's scoped inputs: the candidates this run
    validates plus report lines for everything excluded (foreign artifacts
    and vanished owned reviews). Report lines become gate warnings: foreign
    artifacts are preserved and reported, never gate failures, and a deleted
    review is reported, never silently skipped."""

    candidates: list[Path]
    report_lines: list[str]
    manifest_scoped: bool


def _window_review_candidates(
    ctx: GateContext, window: SessionWindow
) -> list[Path]:
    """The no-manifest fallback arm (legacy behavior, byte-for-byte):
    porcelain plus ignored-matching paths under reviews_dir, filtered by the
    validator's own staging-path predicate and restricted to the session
    window mtime fence. Demoted to the fallback once a run manifest is
    present; unchanged when no manifest exists."""
    if not window.anchored or window.start_epoch is None:
        return []
    start = window.start_epoch
    end = time.time() + 1.0
    candidates: list[Path] = []
    for absolute in _all_staging_review_paths(ctx):
        try:
            mtime = absolute.stat().st_mtime
        except OSError:
            continue
        if start <= mtime <= end:
            candidates.append(absolute)
    return candidates


def _manifest_review_rel(ctx: GateContext, recorded: str) -> str:
    """Normalize a manifest review path entry (repo-relative or absolute) to
    a repo-relative posix string, so gate-time comparisons match the writer's
    verbatim records."""
    path = Path(recorded)
    if not path.is_absolute():
        path = ctx.repo_root / path
    try:
        return path.resolve().relative_to(ctx.repo_root).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


def derive_review_staging_scope(ctx: GateContext) -> ReviewStagingScope:
    """Scope the review-staging gate through the run manifest.

    Manifest branch: the run's owned review paths that exist on disk are the
    candidates (fail-closed for claimed artifacts: a manifest-owned review is
    validated regardless of its mtime, so the session window never shields
    it); an owned path no longer on disk gets a vanish report line; the
    manifest's foreign-review list and every staging candidate unseen since
    Step 0 (predicate-matched on disk, neither owned nor foreign-marked: it
    appeared after Step 0's claim-or-foreign enumeration) go to the
    foreign-excluded side list with named report lines, and their files stay
    byte-identical on disk. No manifest (legacy tree, foreign repo,
    interrupted write): the conservative window-mtime fallback arm.
    """
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    if manifest is None:
        return ReviewStagingScope(
            _window_review_candidates(ctx, window), [], False
        )
    report: list[str] = []
    unique: dict[str, Path] = {}
    for recorded in manifest.owned_review_paths:
        normalized = _manifest_review_rel(ctx, recorded)
        if normalized in unique:
            continue
        absolute = ctx.repo_root / normalized
        if absolute.is_file():
            unique[normalized] = absolute
        else:
            report.append(
                "manifest-owned review no longer on disk (vanished since "
                "Step 0; reported, never silently skipped): " + normalized
            )
    foreign_norm = {
        _manifest_review_rel(ctx, recorded)
        for recorded in manifest.foreign_review_paths
    }
    for absolute in _all_staging_review_paths(ctx):
        normalized = _manifest_review_rel(ctx, str(absolute))
        if normalized in unique:
            continue
        if normalized in foreign_norm:
            report.append(
                "foreign staging doc excluded from validation (owner class: "
                "peer artifact, marked foreign at Step 0; file preserved): "
                + normalized
            )
        else:
            report.append(
                "foreign staging doc excluded from validation (owner class: "
                "peer artifact, unseen since Step 0; file preserved): "
                + normalized
            )
    candidates = [unique[key] for key in sorted(unique)]
    return ReviewStagingScope(candidates, report, True)


def derive_review_staging_candidates(ctx: GateContext) -> list[Path]:
    """The review-staging gate's candidates: the run manifest's owned review
    paths when a manifest is present, else the legacy porcelain plus
    ignored-matching paths under reviews_dir restricted to the session window
    and filtered by the validator's own staging-path predicate. Never a
    bare glob, never chat recall.

    F4/F8 branch asymmetry, deliberate and fail-closed: in the manifest
    branch, an owned path that exists on disk is validated on existence alone
    (is_file), regardless of the staging-path predicate - over-validation
    can only over-check a claimed artifact, never suppress a check - while
    the fallback window arm applies the staging-path predicate to each
    candidate."""
    return derive_review_staging_scope(ctx).candidates


def gate_review_staging(ctx: GateContext) -> GateResult:
    gate = "review-staging"
    scope = derive_review_staging_scope(ctx)
    candidates = scope.candidates
    warnings = list(scope.report_lines)
    if not candidates:
        if warnings:
            # Foreign-excluded and vanished lines still report on an
            # otherwise empty run: never silently dropped, never a failure.
            return GateResult(
                gate,
                0,
                "review-staging: no owned staging candidates to validate; "
                "excluded artifacts preserved and reported as warnings",
                warnings=warnings,
            )
        return GateResult(
            gate,
            0,
            "no-op: no session-touched staging docs under reviews_dir in the "
            "session window",
            warnings=[],
        )
    validator = ctx.resolve_script(
        "REVIEW_STAGING_VALIDATOR", "validate_review_staging.py"
    )
    if validator is None:
        return GateResult(
            gate,
            1,
            "review-staging validator absent but session-touched staging "
            "candidates exist (fail-closed, matching the skill's "
            "|| exit 1): " + ", ".join(str(p) for p in candidates),
            warnings=warnings,
        )
    failed: list[str] = []
    for candidate in candidates:
        proc = ctx.run(
            [sys.executable, str(validator), "--hard", str(candidate)],
            cwd=ctx.repo_root,
        )
        if proc.returncode != 0:
            failed.append(str(candidate))
    if failed:
        return GateResult(
            gate,
            1,
            "review-staging validation failed for: " + ", ".join(failed),
            warnings=warnings,
        )
    if scope.manifest_scoped:
        message = (
            f"review-staging validation passed for {len(candidates)} "
            "manifest-owned staging doc(s)"
        )
    else:
        message = (
            f"review-staging validation passed for {len(candidates)} "
            "session-touched staging doc(s)"
        )
    return GateResult(gate, 0, message, warnings=warnings)


# --------------------------------------------------------------------------- #
# Gate: vim-swap-sweep (done Step 2.63).
# --------------------------------------------------------------------------- #
SWAP_SUFFIXES = (".swp", ".swo", ".swn")
FILE_PID_RE = re.compile(r"pid (\d+)")


def _iter_swap_candidates(ctx: GateContext) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ctx.repo_root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            if name.startswith(".") and name.endswith(SWAP_SUFFIXES):
                found.append(Path(dirpath) / name)
    return sorted(found)


def _edited_document(swap_path: Path) -> Path:
    name = swap_path.name
    stem = name[1:-4]  # strip leading dot and 4-char suffix
    return swap_path.parent / stem


def gate_vim_swap_sweep(ctx: GateContext) -> GateResult:
    gate = "vim-swap-sweep"
    candidates = _iter_swap_candidates(ctx)
    if not candidates:
        return GateResult(gate, 0, "no vim swap files found", warnings=[])
    removed: list[str] = []
    active: list[str] = []
    needs_manual: list[str] = []
    for swap in candidates:
        probe = subprocess.run(
            ["file", "--", str(swap)],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
        )
        output = probe.stdout or ""
        if "Vim swap file" not in output:
            needs_manual.append(f"{swap} (file(1) did not verify a Vim swap)")
            continue
        pid_match = FILE_PID_RE.search(output)
        if not pid_match:
            needs_manual.append(f"{swap} (no usable PID in swap header)")
            continue
        pid = int(pid_match.group(1))
        ps = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
        )
        document = _edited_document(swap)
        if ps.returncode == 0:
            command = (ps.stdout or "").strip()
            if document.name in command or str(document) in command:
                active.append(f"{swap} (live editor pid {pid})")
            else:
                needs_manual.append(
                    f"{swap} (live pid {pid} does not name the edited document)"
                )
        else:
            try:
                swap.unlink()
                removed.append(str(swap))
            except OSError as exc:
                needs_manual.append(f"{swap} (removal failed: {exc})")
    parts = [
        f"removed={len(removed)}",
        f"active={len(active)}",
        f"needs-manual={len(needs_manual)}",
    ]
    message = "vim swap sweep: " + ", ".join(parts)
    if removed:
        message += "; removed: " + ", ".join(removed)
    if active:
        message += "; active (preserved): " + ", ".join(active)
    if needs_manual:
        message += "; needs manual confirmation: " + ", ".join(needs_manual)
    return GateResult(gate, 0, message, warnings=[])


# --------------------------------------------------------------------------- #
# Gate: docs-tmp-sweep (done Step 2.62).
# --------------------------------------------------------------------------- #
DATED_ONE_OFF_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
PROTECTED_SCRATCH_PREFIXES = ("review-loop",)
PROTECTED_SCRATCH_DIRS = ("code-review", "handoff")


def _docs_sync_state(ctx: GateContext, rel: str) -> str:
    """synced | never-synced | uncertain, via the docs orphan branch."""
    proc = ctx.git("ls-tree", "-r", "--name-only", "refs/heads/docs", "--", rel)
    if proc.returncode != 0:
        return "uncertain"
    return "synced" if proc.stdout.strip() else "never-synced"


def gate_docs_tmp_sweep(ctx: GateContext) -> GateResult:
    gate = "docs-tmp-sweep"
    tmp_dir = ctx.tmp_dir
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    removed: list[str] = []
    skipped: list[str] = []
    kept: list[str] = []

    def rel_of(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(ctx.repo_root.resolve()))
        except ValueError:
            return str(path)

    if tmp_dir.is_dir():
        for entry in sorted(tmp_dir.iterdir()):
            name = entry.name
            if name == "done-session":
                _prune_done_session_markers(
                    ctx, entry, window, removed, kept
                )
                continue
            if entry.is_dir() and name == "execute-plan":
                _sweep_execute_plan_sessions(ctx, entry, removed, kept)
                continue
            if entry.is_file() and name.startswith("plan-requirements-") and name.endswith(".md"):
                slug = name[len("plan-requirements-") : -len(".md")]
                if (ctx.plans_completed_dir / (slug + ".md")).is_file():
                    try:
                        entry.unlink()
                        removed.append(rel_of(entry))
                    except OSError:
                        kept.append(rel_of(entry))
                else:
                    kept.append(rel_of(entry) + " (owning plan still pending)")
                continue
            if entry.is_dir() and (
                name.startswith(PROTECTED_SCRATCH_PREFIXES) or name in PROTECTED_SCRATCH_DIRS
            ):
                kept.append(rel_of(entry) + " (protected scratch; owning skill cleans up)")
                continue
            if entry.is_file() and (
                name.endswith(".py")
                or name.endswith(".log.md")
                or (name.endswith(".md") and DATED_ONE_OFF_RE.match(name))
            ):
                state = _docs_sync_state(ctx, rel_of(entry))
                if state == "synced":
                    # Base guard: synced removal also requires the entry to be
                    # OUTSIDE the session window. An unanchorable window or an
                    # unreadable mtime is conservative and removes nothing.
                    if not window.anchored or window.start_epoch is None:
                        skipped.append(
                            f"{rel_of(entry)} (synced, but the session window "
                            "is unanchorable; never guessing)"
                        )
                        continue
                    try:
                        mtime = entry.stat().st_mtime
                    except OSError:
                        skipped.append(
                            f"{rel_of(entry)} (synced, but mtime unreadable; "
                            "never guessing)"
                        )
                        continue
                    if mtime >= window.start_epoch:
                        skipped.append(
                            f"{rel_of(entry)} (synced but modified inside the "
                            "session window; removal deferred to a later "
                            "session)"
                        )
                        continue
                    try:
                        entry.unlink()
                        removed.append(rel_of(entry))
                    except OSError:
                        kept.append(rel_of(entry))
                else:
                    reason = (
                        "never synced to the docs branch; removal would be "
                        "permanent"
                        if state == "never-synced"
                        else "docs branch presence uncertain; never guessing"
                    )
                    skipped.append(f"{rel_of(entry)} ({reason})")
                continue
            kept.append(rel_of(entry) + " (unclear ownership or active work)")

    parts = [
        f"removed={len(removed)}",
        f"skipped={len(skipped)}",
        f"kept={len(kept)}",
    ]
    message = "docs/tmp sweep: " + ", ".join(parts)
    if not window.anchored:
        message += "; no anchor: no run-start-* marker pruned this run"
    if removed:
        message += "; removed: " + ", ".join(removed)
    if skipped:
        message += "; skipped: " + ", ".join(skipped)
    return GateResult(gate, 0, message, warnings=[])


def _prune_done_session_markers(
    ctx: GateContext,
    done_session: Path,
    window: SessionWindow,
    removed: list[str],
    kept: list[str],
) -> None:
    """Remove run-start-* markers strictly older than the previous-run anchor;
    the anchor and the current-run marker are immune; an unanchorable window
    or unparseable content prunes nothing (never guess by recency)."""
    if not done_session.is_dir():
        return
    if not window.anchored or window.anchor is None:
        kept.append(str(done_session) + " (window unanchorable; markers immune)")
        return
    anchor_epoch = window.anchor.epoch
    for marker in sorted(done_session.glob("run-start-*")):
        parsed = _parse_marker(marker, ctx.repo_root)
        if parsed is None:
            # A cross-repo or unparseable marker is never pruned by recency.
            kept.append(str(marker) + " (content not confirmable as this repo)")
            continue
        if parsed.epoch < anchor_epoch:
            try:
                marker.unlink()
                removed.append(str(marker))
            except OSError:
                kept.append(str(marker))
        else:
            kept.append(str(marker) + " (anchor or current run; immune)")


def _sweep_execute_plan_sessions(
    ctx: GateContext,
    execute_dir: Path,
    removed: list[str],
    kept: list[str],
) -> None:
    """Remove execute-plan/<slug>/ sessions whose plan archived to
    plans_completed_dir; never remove an active session (manifest present and
    plan still under plans_dir). A live plan may sit anywhere under
    plans_dir (e.g. ``docs/history/plans/deferred/<slug>.md``), so the pending
    check is recursive over plans_dir, mirroring how the readiness
    candidate derivation accepts nested plan paths."""
    if not execute_dir.is_dir():
        return
    pending_stems = {
        plan.stem
        for plan in ctx.plans_dir.rglob("*.md")
        if plan.is_file() and not _is_relative_to(plan, ctx.plans_completed_dir)
    }
    for session in sorted(execute_dir.iterdir()):
        if not session.is_dir():
            continue
        if session.name in pending_stems:
            kept.append(str(session) + " (active: plan still pending)")
            continue
        try:
            shutil.rmtree(session)
            removed.append(str(session) + " (plan archived)")
        except OSError:
            kept.append(str(session) + " (removal failed)")


# --------------------------------------------------------------------------- #
# Gate: sensitive-data-scan (done Step 2.7 mechanical half).
# --------------------------------------------------------------------------- #
def _employer_brand_patterns(ctx: GateContext) -> list[str]:
    """Employer-brand patterns resolved from the user facts document; never
    hardcoded. Explicit ``employer_brand_patterns`` rows (comma-separated)
    first, then the org Atlassian domain row when present."""
    patterns: list[str] = []
    explicit = ctx.read_user_facts_table_key("employer_brand_patterns")
    if explicit:
        patterns.extend(part.strip() for part in explicit.split(",") if part.strip())
    domain = ctx.read_user_facts_table_key("atlassian_domain")
    if domain:
        value = domain.strip()
        host = value.split("://", 1)[-1].strip("/")
        if host and host not in patterns:
            patterns.append(re.escape(host))
    return patterns


def gate_sensitive_data_scan(ctx: GateContext) -> GateResult:
    gate = "sensitive-data-scan"
    findings: list[str] = []
    warnings: list[str] = []

    # Arm 1: diff-content grep over staged content (git diff --cached -U0).
    staged = ctx.git("diff", "--cached", "--name-only")
    if staged.returncode == 0:
        for rel in [ln for ln in staged.stdout.splitlines() if ln.strip()]:
            if not (ctx.repo_root / rel).is_file():
                continue
            diff = ctx.git("diff", "--cached", "-U0", "--", rel)
            if diff.returncode != 0:
                continue
            for line in diff.stdout.splitlines():
                if not line.startswith("+") or line.startswith("+++"):
                    continue
                for pattern in DIFF_CONTENT_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(
                            f"staged {rel}: diff content matches pattern "
                            f"/{pattern}/ in added line"
                        )
                        break

    # Arm 2: full-content grep over untracked files being staged.
    others = ctx.git("ls-files", "--others", "--exclude-standard")
    if others.returncode == 0:
        for rel in [ln for ln in others.stdout.splitlines() if ln.strip()]:
            path = ctx.repo_root / rel
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(content.splitlines(), start=1):
                for pattern in DIFF_CONTENT_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(
                            f"untracked {rel}:{lineno}: content matches pattern "
                            f"/{pattern}/"
                        )
                        break

    # Arm 3: push-range commit-message audit when an upstream is configured.
    upstream = ctx.git(
        "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"
    )
    push_range_ran = upstream.returncode == 0 and bool(upstream.stdout.strip())
    if push_range_ran:
        remote_ref = upstream.stdout.strip()
        brand_patterns = _employer_brand_patterns(ctx)
        log = ctx.git(
            "log", f"{remote_ref}..HEAD", "--format=%H%x00%s%x00%B%x1e"
        )
        if log.returncode == 0:
            for record in log.stdout.split("\x1e"):
                pieces = record.strip().split("\x00")
                if len(pieces) < 3:
                    continue
                sha, subject, body = pieces[0], pieces[1], pieces[2]
                short = sha[:12]
                if CO_AUTHORED_RE.search(body):
                    findings.append(
                        f"push-range commit {short}: message matches pattern "
                        "/Co-authored-by/ (attribution trailers must not be "
                        "pushed)"
                    )
                for brand in brand_patterns:
                    if re.search(brand, body, re.IGNORECASE) or re.search(
                        brand, subject, re.IGNORECASE
                    ):
                        findings.append(
                            f"push-range commit {short}: message matches "
                            f"employer-brand pattern /{brand}/ from facts"
                        )
    else:
        warnings.append(
            "warning: no upstream configured; push-range commit-message "
            "audit skipped"
        )

    # Arm 4: the public-hygiene scan when this repo IS the skills repo. Its
    # deny-patterns file carries the employer-brand patterns, so it absorbs
    # the skills-tree employer-brand grep (LICENSE.txt excluded).
    skills_repo_raw = ctx.read_user_facts_table_key("skills_repo_path")
    if skills_repo_raw:
        try:
            same_repo = os.path.realpath(skills_repo_raw) == os.path.realpath(
                str(ctx.repo_root)
            )
        except OSError:
            same_repo = False
        if same_repo:
            scan = ctx.resolve_script(
                "PUBLIC_HYGIENE_SCAN_SCRIPT", "scan-public-hygiene.sh"
            )
            if scan is None:
                warnings.append(
                    "warning: scan-public-hygiene.sh not found at any resolved "
                    "path; skills-repo hygiene arm skipped"
                )
            else:
                proc = ctx.run(["bash", str(scan)], cwd=ctx.repo_root)
                if proc.returncode != 0:
                    tail_rows = [
                        row
                        for row in (proc.stdout or "").strip().splitlines()
                        if row.strip()
                    ][-10:]
                    findings.append(
                        "public-hygiene scan failed: " + " | ".join(tail_rows)
                    )

    if findings:
        return GateResult(
            gate,
            1,
            "sensitive-data scan failed: " + "; ".join(findings[:10]),
            warnings=warnings,
        )
    return GateResult(
        gate,
        0,
        "sensitive-data scan clean (diff content, untracked content"
        + (", push-range commit messages" if push_range_ran else "")
        + ")",
        warnings=warnings,
    )


# --------------------------------------------------------------------------- #
# Gates: em-dash-scan (done Step 2.76) and instruction-size (done Step 2.8).
# --------------------------------------------------------------------------- #
def gate_em_dash_scan(ctx: GateContext) -> GateResult:
    gate = "em-dash-scan"
    script = ctx.resolve_script("CHECK_NO_EM_DASH_SCRIPT", "check-no-em-dash.sh")
    if script is None:
        # Fail closed (deployment-gap signature semantics, same as
        # plan-readiness): the base inline invocation failed loud when the
        # script was missing.
        message = (
            "deployment gap: check-no-em-dash.sh absent at every resolved "
            "path (env override, repo-local scripts/, runtime home copy); "
            "remedy: deploy the script to the runtime home scripts/ "
            "directory; never use the recorded-stop exception for a "
            "deployment gap"
        )
        return GateResult(gate, 1, message, warnings=[])
    proc = ctx.run(["bash", str(script), "touched"], cwd=ctx.repo_root)
    if proc.returncode != 0:
        tail_rows = [
            row for row in (proc.stdout or "").strip().splitlines() if row.strip()
        ][-10:]
        return GateResult(
            gate, 1, "em dash scan failed: " + " | ".join(tail_rows), warnings=[]
        )
    return GateResult(gate, 0, "em dash scan clean (touched prose)", warnings=[])


def gate_instruction_size(ctx: GateContext) -> GateResult:
    gate = "instruction-size"
    script = ctx.resolve_script(
        "INSTRUCTION_SIZE_CHECK_SCRIPT", "check-instruction-size.sh"
    )
    if script is None:
        # Fail closed (deployment-gap signature semantics, same as
        # plan-readiness): the base inline invocation failed loud when the
        # script was missing.
        message = (
            "deployment gap: check-instruction-size.sh absent at every "
            "resolved path (env override, repo-local scripts/, runtime home "
            "copy); remedy: deploy the script to the runtime home scripts/ "
            "directory; never use the recorded-stop exception for a "
            "deployment gap"
        )
        return GateResult(gate, 1, message, warnings=[])
    proc = ctx.run(["bash", str(script), "gate"], cwd=ctx.repo_root)
    if proc.returncode != 0:
        tail_rows = [
            row for row in (proc.stdout or "").strip().splitlines() if row.strip()
        ][-10:]
        return GateResult(
            gate,
            1,
            "instruction size gate failed: " + " | ".join(tail_rows),
            warnings=[],
        )
    return GateResult(gate, 0, "instruction size gate passed", warnings=[])


# --------------------------------------------------------------------------- #
# Registry, phase runner, report, CLI.
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# foreign-staging + plans-archive-twin gates (done sweep landing-time nets).
# --------------------------------------------------------------------------- #
def normalized_start_dirt_paths(start_porcelain: list[str]) -> set[str]:
    """Dedicated row normalizer for the start-dirt record, keyed on the
    status letters: a row whose FIRST status letter (the index column) is
    ``R`` or ``C``, or whose second (worktree) letter is ``R`` on runtimes
    that emit worktree-column rename rows, registers BOTH sides of the
    `` -> `` separator (each C-unquoted); any other row registers its body
    verbatim, C-unquoted. A path containing the literal separator is parsed
    by letters, never by substring. Deliberately NOT ``_porcelain_paths``,
    which keeps only the new side of a rename and detects renames by
    substring."""
    paths: set[str] = set()
    for row in start_porcelain:
        if len(row) < 4:
            continue
        xy = row[:2]
        rest = row[3:]
        rename_like = xy[0] in ("R", "C") or xy[1] == "R"
        if rename_like and " -> " in rest:
            old, new = rest.split(" -> ", 1)
            paths.add(_unquote_porcelain_path(old))
            paths.add(_unquote_porcelain_path(new))
        else:
            paths.add(_unquote_porcelain_path(rest))
    return paths


def gate_foreign_staging(ctx: GateContext) -> GateResult:
    """Pre-commit gate: the commit-boundary re-run over the final staged set.

    Fails any staged path that is recorded as start-dirt at Step 0 and is
    outside the run's owned paths (the union of ``owned_paths``,
    ``owned_plan_paths``, and ``owned_review_paths``). With no resolvable
    run manifest the gate reports a warning skip, never a silent pass and
    never a crash. Content-level co-editing inside a session-owned path
    stays a recorded residual (the judgment gate in the done skill owns it;
    pathspec-only landing commits are the commit-time net)."""
    gate = "foreign-staging"
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    if manifest is None:
        return GateResult(
            gate,
            0,
            "foreign-staging: warning skip: no resolvable run manifest "
            "(Step 0 record absent, foreign-rooted, or schema-invalid); "
            "the staged set could not be ownership-checked",
            warnings=[
                "foreign-staging skipped: no resolvable run manifest for "
                "the current session window"
            ],
        )
    start_dirt = normalized_start_dirt_paths(manifest.start_porcelain)
    owned = {
        _manifest_review_rel(ctx, recorded)
        for recorded in (
            list(manifest.owned_paths)
            + list(manifest.owned_plan_paths)
            + list(manifest.owned_review_paths)
        )
    }
    proc = ctx.git("diff", "--cached", "--name-only", "--no-renames")
    staged = {
        _unquote_porcelain_path(line)
        for line in proc.stdout.splitlines()
        if line.strip()
    }
    foreign = sorted(staged & start_dirt - owned)
    if foreign:
        return GateResult(
            gate,
            1,
            "foreign-staging gate failed: landing must never stage foreign "
            "start-dirt; staged path(s) recorded as start-dirt but not "
            "owned: " + ", ".join(foreign),
            warnings=[],
        )
    exempted = sorted(staged & start_dirt & owned)
    message = "foreign-staging gate passed: no foreign start-dirt staged"
    warnings: list[str] = []
    if exempted:
        message += (
            "; owned start-dirt path(s) deliberately staged (claimed at "
            "Step 0): " + ", ".join(exempted)
        )
        warnings.append(
            "foreign-staging exempted owned path(s) named for audit: "
            + ", ".join(exempted)
        )
    return GateResult(gate, 0, message, warnings=warnings)


DATED_PLAN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")


def gate_plans_archive_twin(ctx: GateContext) -> GateResult:
    """Landing-time twin gate over the plans home (pre-docs AND pre-commit).

    Fails any landing while a dated plan basename sits both at the plans
    root and inside an archive state directory (completed, deferred,
    rejected), byte-identical or not. Ownership split (recorded at the code
    home per the plan): ``scripts/check_maintenance_pins.sh``
    ``check_live_vs_archive_duplicates`` stays the corpus-wide scheduled
    owner of the basename-collision class (plans AND backlog roots,
    non-dated names included); this gate is the landing-time net over the
    plans home only, facts-key-driven, dated plan shape. Deliberate scope
    edge owned by neither scanner today: a basename in two state
    directories with no root copy (completed plus rejected, say) is the
    corpus-wide owner's designated absorber."""
    gate = "plans-archive-twin"
    warnings: list[str] = []
    import facts_paths as _facts_paths

    for key in ("plans_dir", "plans_completed_dir"):
        if _facts_paths.resolve_toml_key_raw(ctx.repo_root, key) is None:
            warnings.append(
                f"plans-archive-twin: facts key {key!r} does not resolve; "
                "the default home fell back"
            )
    state_dirs = {
        "completed": ctx.plans_completed_dir,
        "deferred": ctx.plans_dir / "deferred",
        "rejected": ctx.plans_dir / "rejected",
    }
    for name, directory in state_dirs.items():
        if not directory.is_dir():
            warnings.append(
                f"plans-archive-twin: resolved {name} state directory does "
                f"not exist on disk: {directory}"
            )
    if not ctx.plans_dir.is_dir():
        return GateResult(
            gate,
            0,
            "plans-archive-twin: warning skip: plans home does not exist "
            f"on disk: {ctx.plans_dir}",
            warnings=warnings,
        )
    root_dated = {
        entry.name
        for entry in ctx.plans_dir.iterdir()
        if entry.is_file() and DATED_PLAN_RE.match(entry.name)
    }
    findings: list[str] = []
    for name in sorted(root_dated):
        for state_name, directory in state_dirs.items():
            twin = directory / name
            if twin.is_file():
                findings.append(
                    f"{ctx.plans_dir / name} <-> {twin} ({state_name})"
                )
    if findings:
        return GateResult(
            gate,
            1,
            "plans-archive-twin gate failed: a dated plan basename sits "
            "both at the plans root and in an archive state directory "
            "(a move, never an add-plus-keep): " + "; ".join(findings),
            warnings=warnings,
        )
    return GateResult(
        gate,
        0,
        "plans-archive-twin gate passed: no root-plus-archive plan twin",
        warnings=warnings,
    )


GATES: dict[str, Callable[[GateContext], GateResult]] = {
    "plan-readiness": gate_plan_readiness,
    "confluence-hygiene": gate_confluence_hygiene,
    "doc-registry": gate_doc_registry,
    "backlog-inbox": gate_backlog_inbox,
    "review-staging": gate_review_staging,
    "vim-swap-sweep": gate_vim_swap_sweep,
    "docs-tmp-sweep": gate_docs_tmp_sweep,
    "sensitive-data-scan": gate_sensitive_data_scan,
    "em-dash-scan": gate_em_dash_scan,
    "instruction-size": gate_instruction_size,
    "foreign-staging": gate_foreign_staging,
    "plans-archive-twin": gate_plans_archive_twin,
}


def run_gate(gate_id: str, ctx: GateContext) -> GateResult:
    if gate_id not in GATES:
        raise ValueError(f"unknown gate id: {gate_id}")
    return GATES[gate_id](ctx)


def run_phase(phase: str, ctx: GateContext) -> list[GateResult]:
    """Run one phase's gates strictly sequentially in registry order (see the
    module docstring's execution contract)."""
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase}")
    return [run_gate(gate_id, ctx) for gate_id in PHASES[phase]]


def render_report(results: list[GateResult]) -> str:
    """One JSON line per gate (registry order) plus a human summary block."""
    lines = [json.dumps(result.as_dict()) for result in results]
    lines.append("")
    lines.append("==== done sweep summary ====")
    for result in results:
        lines.append(f"[{result.gate}] rc={result.rc} {result.message}")
        for warning in result.warnings:
            lines.append(f"  {warning}")
    return "\n".join(lines)


def phase_exit(results: list[GateResult]) -> int:
    return max((result.rc for result in results), default=0)


def _usage() -> str:
    return (
        "usage: done_sweep_gates.sh "
        "<pre-docs|pre-commit|list-gates|write-manifest|finalize-manifest>\n"
        "phases: pre-docs (done Steps 1.5..2.62 gates), pre-commit (done "
        "Steps 2.7/2.76/2.8 mechanical gates)\n"
        "list-gates prints the twelve absorbed gate ids in phase order, "
        "deduped at first phase (the twin runs in both phases)\n"
        "write-manifest writes the done Step 0 run manifest record "
        "(run-manifest-<run_id>.json under the done-session directory), "
        "reporting interrupted runs (complete=false, never finalized; "
        "continued only via an explicit --adopt boundary copy)\n"
        "finalize-manifest sets a run manifest's complete flag to true in "
        "place (done Step 6; --run-id required; a missing manifest is a "
        "named not-found note, not a failure)"
    )


def _cli_fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _cmd_write_manifest(argv: list[str]) -> int:
    """Write the done Step 0 run manifest record.

    Derives run_id, the newest content-confirmed run-start marker, the HEAD
    start commit, the porcelain dirt snapshot, and the repo root itself, then
    enforces claim-or-foreign over the staging candidates on disk (predicate
    matched, NOT window filtered: Step 0 is the enumeration universe). Any
    uncovered candidate aborts with a named error and no manifest. Prints the
    manifest path plus run_id (the run's audit record).

    Interrupted-run reporting: every root-matched manifest whose ``complete``
    flag is still false and which no other manifest adopts is reported as an
    interrupted run (a finalized manifest is never an orphan). Without
    ``--adopt`` the new manifest keeps the new run's own HEAD boundary;
    adoption is explicit only: ``--adopt <run_id>`` copies the interrupted
    run's boundary (start_commit plus owned paths, foreign markings included)
    verbatim and records ``adopted_from``, and the adopted link suppresses the
    orphan report for later runs.
    """
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py write-manifest",
        description="Write the done Step 0 run manifest record.",
    )
    parser.add_argument(
        "--owned-plan", action="append", default=[], metavar="PATH",
        help="plan path this run finalizes (repeatable)",
    )
    parser.add_argument(
        "--owned-review", action="append", default=[], metavar="PATH",
        help="review staging doc this run finalizes (repeatable)",
    )
    parser.add_argument(
        "--owned-path", action="append", default=[], metavar="PATH",
        help="start-dirt path this run may stage (repeatable; recorded in "
        "owned_paths and audited by the foreign-staging gate)",
    )
    parser.add_argument(
        "--foreign-review", action="append", default=[], metavar="PATH",
        help="staging candidate recognized as a peer's artifact (repeatable)",
    )
    parser.add_argument(
        "--foreign-review-from", default=None, metavar="FILE",
        help="bulk-load foreign paths one per line from FILE (F13; merged "
        "into --foreign-review with the same dedup)",
    )
    parser.add_argument(
        "--claim-none", action="store_true",
        help="this run owns no staging doc: mark every unclaimed candidate "
        "foreign (F13; conflicts with an adopted manifest that owns staging "
        "docs or with --owned-review)",
    )
    parser.add_argument(
        "--adopt", default=None, metavar="RUN_ID",
        help="explicitly adopt a prior interrupted run's boundary",
    )
    args = parser.parse_args(argv)

    # F13 bulk load: one path per line, blank lines skipped, merged into the
    # repeatable --foreign-review list with the same dedup downstream.
    if args.foreign_review_from:
        try:
            bulk_lines = Path(args.foreign_review_from).read_text(
                encoding="utf-8"
            ).splitlines()
        except OSError as exc:
            return _cli_fail(
                "write-manifest: cannot read --foreign-review-from file "
                f"{args.foreign_review_from}: {exc}"
            )
        args.foreign_review.extend(
            line.strip() for line in bulk_lines if line.strip()
        )
    if args.claim_none and args.owned_review:
        return _cli_fail(
            "write-manifest: ownership-conflict: --claim-none asserts this "
            "run owns no staging doc, but --owned-review names "
            + ", ".join(args.owned_review)
        )

    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    ctx = GateContext.discover(Path(root) if root else None)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    if window.current is None:
        return _cli_fail(
            "write-manifest: no content-confirmed run-start marker under "
            f"{ctx.done_session_dir}; write the marker before the manifest"
        )
    head = ctx.git("rev-parse", "HEAD")
    start_commit = head.stdout.strip()
    if head.returncode != 0 or not start_commit:
        return _cli_fail(
            "write-manifest: cannot resolve the HEAD start commit: "
            + (head.stderr.strip() or "git rev-parse failed")
        )

    # Explicit adoption: the target must be a readable, root-matched,
    # not-yet-finalized manifest; its boundary (start_commit and owned paths,
    # plus its foreign markings) is carried verbatim into the new record.
    adopted: Optional[RunManifest] = None
    if args.adopt:
        candidate = _read_manifest_by_run_id(ctx.done_session_dir, args.adopt)
        if candidate is None or not _manifest_root_matches(
            candidate.repo_root, ctx.repo_root
        ):
            return _cli_fail(
                f"write-manifest: cannot adopt {args.adopt}: no readable, "
                "root-matched run manifest for that run_id under "
                f"{ctx.done_session_dir}"
            )
        if candidate.complete:
            return _cli_fail(
                f"write-manifest: cannot adopt {args.adopt}: that run already "
                "finalized (complete=true); only an interrupted (complete="
                "false) run can be adopted"
            )
        verify = ctx.git(
            "rev-parse", "-q", "--verify", candidate.start_commit + "^{commit}"
        )
        if verify.returncode != 0:
            return _cli_fail(
                f"write-manifest: cannot adopt {args.adopt}: the recorded "
                f"start_commit {candidate.start_commit} does not resolve in "
                "this repository"
            )
        adopted = candidate

    # F13 composition rule: --claim-none with an adopted manifest that itself
    # owns staging docs is a named ownership conflict, never a silent flip of
    # the adopted owned paths to foreign.
    if args.claim_none and adopted is not None and adopted.owned_review_paths:
        return _cli_fail(
            "write-manifest: ownership-conflict: --claim-none asserts this "
            "run owns no staging doc, but the adopted run "
            f"{adopted.run_id} owns: " + ", ".join(adopted.owned_review_paths)
        )

    # Interrupted-run report: surfaced for an explicit decision, never
    # implicitly adopted. The adopted target prints its own line.
    corrupt_warnings: list[str] = []
    for orphan in _detect_interrupted_runs(
        ctx.done_session_dir, ctx.repo_root, warnings=corrupt_warnings
    ):
        if adopted is not None and orphan.run_id == adopted.run_id:
            print(
                "interrupted run: adopting the boundary of "
                f"{orphan.run_id} (start_commit and owned paths carried "
                "verbatim from its manifest)"
            )
            continue
        print(
            "interrupted run: "
            f"{_manifest_path(ctx.done_session_dir, orphan.run_id).name} "
            "(complete=false, never finalized); this run keeps its own HEAD "
            f"boundary; pass --adopt {orphan.run_id} to continue that run's "
            "boundary"
        )
    for line in corrupt_warnings:
        # F10: a corrupt record in the done-session dir is reported, never
        # silently skipped (an undead run leaves a trace).
        print(line)

    if adopted is not None:
        start_commit = adopted.start_commit
        owned_paths = _dedup_preserving_order(
            [
                _repo_relative(p, ctx.repo_root)
                for p in list(args.owned_path) + list(adopted.owned_paths)
            ]
        )
        owned_plan_paths = _dedup_preserving_order(
            [
                _repo_relative(p, ctx.repo_root)
                for p in list(args.owned_plan) + list(adopted.owned_plan_paths)
            ]
        )
        owned_review_paths = _dedup_preserving_order(
            [
                _repo_relative(p, ctx.repo_root)
                for p in list(args.owned_review) + list(adopted.owned_review_paths)
            ]
        )
        foreign_review_paths = _dedup_preserving_order(
            [
                _repo_relative(p, ctx.repo_root)
                for p in list(args.foreign_review) + list(adopted.foreign_review_paths)
            ]
        )
    else:
        owned_paths = _dedup_preserving_order(
            [_repo_relative(p, ctx.repo_root) for p in args.owned_path]
        )
        owned_plan_paths = _dedup_preserving_order(
            [_repo_relative(p, ctx.repo_root) for p in args.owned_plan]
        )
        owned_review_paths = _dedup_preserving_order(
            [_repo_relative(p, ctx.repo_root) for p in args.owned_review]
        )
        foreign_review_paths = _dedup_preserving_order(
            [_repo_relative(p, ctx.repo_root) for p in args.foreign_review]
        )

    start_porcelain = _porcelain_lines(ctx, ".")

    # Adoption composition: the predecessor's uncommitted output stays
    # gate-visible, so the adopted start-dirt record is the adopted
    # manifest's start_porcelain unioned with the fresh snapshot.
    if adopted is not None:
        start_porcelain = _dedup_preserving_order(
            list(adopted.start_porcelain) + list(start_porcelain)
        )

    # Writer-side cross-check: an --owned-path claim matching no normalized
    # start-dirt row warns by name (a wrong claim is auditable, never
    # silent).
    unclaimed = [
        path
        for path in owned_paths
        if path not in normalized_start_dirt_paths(start_porcelain)
    ]
    if unclaimed:
        print(
            "write-manifest: warning: --owned-path claim(s) matching no "
            "normalized start-dirt row: " + ", ".join(unclaimed)
        )

    # Claim-or-foreign over the Step 0 enumeration universe: every staging
    # candidate on disk must be either claimed (the run's own --owned-review
    # plus the adopted run's inherited claims) or explicitly marked a peer's
    # artifact (--foreign-review plus inherited foreign markings); fail loud
    # otherwise, and never write a partial ownership record.
    def real(path: str) -> str:
        return os.path.realpath(str(ctx.repo_root / path))

    owned_real = {real(p) for p in owned_review_paths}
    foreign_real = {real(p) for p in foreign_review_paths}
    uncovered = [
        str(candidate)
        for candidate in _all_staging_review_paths(ctx)
        if real(str(candidate)) not in owned_real
        and real(str(candidate)) not in foreign_real
    ]
    if uncovered:
        if args.claim_none:
            # F13: the run owns no staging doc, so every unclaimed candidate
            # is marked foreign (each recorded in foreign_review_paths for
            # audit, repo-relative like the --foreign-review inputs) instead
            # of aborting one flag per path.
            foreign_review_paths = _dedup_preserving_order(
                foreign_review_paths
                + [_repo_relative(c, ctx.repo_root) for c in uncovered]
            )
        else:
            return _cli_fail(
                "write-manifest: claim-or-foreign violation: staging review "
                "candidate(s) on disk are neither owned nor foreign: "
                + ", ".join(uncovered)
                + " (bulk answers: --claim-none when this run owns no "
                "staging doc, or --foreign-review-from <file> with one path "
                "per line)"
            )

    manifest = RunManifest(
        schema=MANIFEST_SCHEMA_VERSION,
        run_id=_new_run_id(),
        marker=window.current.path.name,
        created_epoch=time.time(),
        repo_root=_repo_root_digest(ctx.repo_root),
        pid=os.getpid(),
        start_commit=start_commit,
        start_porcelain=start_porcelain,
        owned_paths=owned_paths,
        owned_plan_paths=owned_plan_paths,
        owned_review_paths=owned_review_paths,
        foreign_review_paths=foreign_review_paths,
        adopted_from=args.adopt,
        complete=False,
    )
    try:
        path = write_run_manifest(manifest, ctx.done_session_dir)
    except OSError as exc:
        return _cli_fail(f"write-manifest: cannot write the run manifest: {exc}")
    print(f"manifest: {path}")
    print(f"run_id: {manifest.run_id}")
    return 0


def _cmd_finalize_manifest(argv: list[str]) -> int:
    """Set the run manifest's ``complete`` flag to true in place (done Step 6,
    immediately before the done-lock release): the run reached the end, so it
    is never an interrupted run for a later Step 0. A missing (or foreign-
    rooted) manifest gets an explicit not-found note with a zero exit: the
    Step 6 recipe's tolerance clause, a run without a manifest skips
    finalization without failing."""
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py finalize-manifest",
        description="Set the run manifest's complete flag to true in place.",
    )
    parser.add_argument(
        "--run-id", required=True, metavar="RUN_ID",
        help="the run_id recorded when Step 0 wrote the manifest",
    )
    args = parser.parse_args(argv)

    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    ctx = GateContext.discover(Path(root) if root else None)
    manifest = _read_manifest_by_run_id(ctx.done_session_dir, args.run_id)
    if manifest is None or not _manifest_root_matches(
        manifest.repo_root, ctx.repo_root
    ):
        print(
            "finalize-manifest: no run manifest found for run_id "
            f"{args.run_id} under {ctx.done_session_dir} (nothing to "
            "finalize; a run without a manifest skips finalization)"
        )
        return 0
    if manifest.complete:
        print(
            f"finalize-manifest: run {manifest.run_id} is already complete; "
            "nothing to do"
        )
        return 0
    manifest.complete = True
    try:
        path = write_run_manifest(manifest, ctx.done_session_dir)
    except OSError as exc:
        return _cli_fail(f"finalize-manifest: cannot rewrite the run manifest: {exc}")
    print(f"finalize-manifest: run {manifest.run_id} marked complete in {path}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(_usage(), file=sys.stderr)
        return 0 if args else 2
    command = args[0]
    if command == "list-gates":
        # Each gate id printed once, deduped at its first phase (the twin
        # runs in both phases; printing it twice invites count drift).
        for gate_id in dict.fromkeys(PRE_DOCS_GATES + PRE_COMMIT_GATES):
            print(gate_id)
        return 0
    if command == "write-manifest":
        return _cmd_write_manifest(args[1:])
    if command == "finalize-manifest":
        return _cmd_finalize_manifest(args[1:])
    if command in PHASES:
        root = os.environ.get("DONE_SWEEP_REPO_ROOT")
        ctx = GateContext.discover(Path(root) if root else None)
        results = run_phase(command, ctx)
        print(render_report(results))
        return phase_exit(results)
    print(_usage(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
