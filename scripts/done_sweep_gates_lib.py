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
  sensitive-data-scan, em-dash-scan, instruction-size, description-length,
  foreign-staging, post-landing-staging, archive-ceremony,
  execute-plan-closeout, plans-archive-twin.

Contract:
- outcome contract (scripts/OUTCOME_CONTRACT.md): every phase run ends with
  exactly one final stdout ``OUTCOME:`` line (``pass``, ``fail``,
  ``indeterminate``, ``tool_error``) matching the aggregate exit code
  (``phase_exit``: indeterminate dominates fail, tool error dominates the
  run); a gate helper that raises is captured as an indeterminate gate result
  naming the failed gate, never a traceback abort; usage errors of the phase
  entry are tool errors (exit 3) while ``--help`` and ``list-gates`` stay
  metadata exits with no ``OUTCOME:`` line;
- gate registry == the absorbed steps at gate and named sub-check
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
The ``disposition-manifest`` sub-command stamps a one-time ``dispositioned``
record onto an unadoptable interrupted manifest (a recorded ``repo_root`` no
checkout satisfies, so adoption and finalize refuse it forever) after its
owned deliverables verify as landed; ``list-interrupted-manifests`` prints
the interrupted manifests classified by root liveness, read-only.
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

# Outcome contract (scripts/OUTCOME_CONTRACT.md): a phase run's aggregate
# gate-result rcs are the contract's exit vocabulary (0 pass, 1 fail,
# 2 indeterminate, 3 tool error) and every phase run ends stdout with exactly
# one final `OUTCOME:` line carrying the same outcome. Indeterminate dominates
# fail for the same run (the contract's multi-input rule); a gate helper that
# raises is captured as an indeterminate gate result, never a traceback abort.
OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}
OUTCOME_VOCABULARY = frozenset(OUTCOME_LABELS.values())
OUTCOME_LINE_PREFIX = "OUTCOME:"

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
    "description-length",
    "foreign-staging",
    "post-landing-staging",
    "archive-ceremony",
    "execute-plan-closeout",
    "plans-archive-twin",
]
PHASES = {
    "pre-docs": PRE_DOCS_GATES,
    "pre-commit": PRE_COMMIT_GATES,
}

# done Step 2.7 item 2 diff-content grep patterns. Credential terms are
# intentionally assignment-shaped so domain prose such as "claim token" does
# not become a false positive while credential-like values remain blocked.
# Credential-shaped patterns are active in every repository regardless of
# declared visibility; the public-artifact family is audience hygiene and
# drops out when the repo declares artifact_visibility = "private" in its
# repo facts (absent or unparseable reads as public: today's strictness).
CREDENTIAL_CONTENT_PATTERNS = [
    r"(?i)\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}",
    r"(?i)\b(?:access|auth|claim|policy|refresh|session)?[_-]?token\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}",
    r"(?i)\b(?:password|secret)\s*[:=]\s*\S+",
]
PUBLIC_ARTIFACT_CONTENT_PATTERNS = [
    r"/Users/",
    r"/home/",
    r"\.atlassian\.net",
    r"@[a-z]+\.(com|io|net)",
]
CO_AUTHORED_RE = re.compile(r"co-authored-by", re.IGNORECASE)

MANIFEST_MAX_AGE_H = 24.0
# Closeout-baseline grace window: a baseline-holding execute-plan session
# whose baseline mtime is older than this many hours is a crashed run's
# debris, not an in-flight transfer-out, and the sweep removes it.
STALE_BASELINE_GRACE_H = 48.0


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
    def artifact_visibility(self) -> str:
        """Declared repository audience from the repo facts TOML; "private"
        only on an exact case-insensitive match, anything else (absent,
        malformed, other values) reads as "public" (fail-safe strictness)."""
        raw = facts_paths.resolve_toml_key_raw(self.repo_root, "artifact_visibility")
        if isinstance(raw, str) and raw.strip().lower() == "private":
            return "private"
        return "public"

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
    means unanchorable (conservative gating downstream), except that a
    single-marker run whose manifest and owned-commits ledger both exist
    anchors its own window from that witness pair (``anchor`` stays None, so
    marker pruning keeps its conservative behavior)."""
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
        current = markers[-1] if markers else None
        if current is not None:
            witness = _single_marker_witness_window(
                done_session_dir, repo_root, current, notes
            )
            if witness is not None:
                return witness
        notes.append(
            "session window unanchorable: fewer than two content-confirmed "
            "run-start markers under done-session"
        )
        return SessionWindow(False, None, current, None, notes)
    current = markers[-1]
    anchor = markers[-2]
    return SessionWindow(True, anchor, current, anchor.epoch, notes)


def _single_marker_witness_window(
    done_session_dir: Path,
    repo_root: Path,
    current: RunMarker,
    notes: list[str],
) -> Optional[SessionWindow]:
    """The single-marker fallback anchor: this run's manifest plus its
    owned-commits ledger (the witness pair) anchor the window at the
    manifest's ``created_epoch``.

    The manifest resolves through the existing loader binding first (its
    ``marker`` field equals the current marker's filename, root-matched,
    newest ``created_epoch`` on ties; the loader works on an unanchored
    window) or, failing that, the newest root-matched manifest in the
    done-session dir. The ledger for the resolved manifest's run id must
    exist on disk as a regular file (a dangling symlink or a directory
    cannot witness ownership). ``anchor`` stays None deliberately: every
    anchor-keying consumer (marker pruning) keeps its conservative
    behavior. None when the witness pair is incomplete (no manifest, or a
    manifest whose ledger is absent, which appends a witness-pair-incomplete
    note); never raises.
    """
    if not done_session_dir.is_dir():
        return None
    manifest = load_run_manifest(
        done_session_dir, repo_root, SessionWindow(False, None, current, None, [])
    )
    if manifest is None:
        # Secondary arm, exactly-one-marker case only: the newest
        # root-matched manifest in the dir, regardless of its marker field.
        best: Optional[RunManifest] = None
        for path in sorted(done_session_dir.glob("run-manifest-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            candidate = RunManifest.from_dict(payload)
            if candidate is None:
                continue
            if not _manifest_root_matches(candidate.repo_root, repo_root):
                continue
            if best is None or candidate.created_epoch > best.created_epoch:
                best = candidate
        manifest = best
    if manifest is None:
        return None
    ledger = _owned_commits_ledger_path(done_session_dir, manifest.run_id)
    if not ledger.is_file():
        notes.append(
            "witness pair incomplete: run manifest "
            f"{_manifest_path(done_session_dir, manifest.run_id).name} present "
            f"but owned-commits ledger {ledger.name} absent; window stays "
            "unanchorable"
        )
        return None
    notes.append(
        "single-marker window anchored from the witness pair: run manifest "
        f"{_manifest_path(done_session_dir, manifest.run_id).name} plus "
        f"owned-commits ledger {ledger.name} (anchor unset; marker pruning "
        "keeps its conservative behavior)"
    )
    return SessionWindow(True, None, current, manifest.created_epoch, notes)


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
    loadable through the two-arm root match). ``dispositioned`` carries the
    optional one-time disposition record (an object with ``reason``, ``date``
    and ``note`` keys, or unset/None) stamped by the ``disposition-manifest``
    sub-command; it suppresses the interrupted-run detection."""

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
    dispositioned: Optional[dict] = None

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
            "dispositioned": self.dispositioned,
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
        # The dispositioned record is optional and additive: a non-dict value
        # (corrupt or hand-edited) degrades to unset, never to an exception -
        # the loader's fixed-key reconstruction must not strip a valid record.
        dispositioned = payload.get("dispositioned")
        if not isinstance(dispositioned, dict):
            dispositioned = None
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
            dispositioned=dispositioned,
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


def _repo_root_matches_value(root_raw: object, repo_root: Path) -> bool:
    """Single source for the two-arm root identity shared by the manifest
    matcher and the finalize pre-parse, raw-safe over any JSON value: a
    64-hex string compares against this repo's identity digest; any other
    string (a legacy raw-path record) keeps the realpath comparison, so a
    manifest from another checkout of the same repo is never this run's
    record and pre-digest manifests stay loadable; a non-string value can
    satisfy neither arm and matches nothing."""
    if not isinstance(root_raw, str):
        return False
    if re.fullmatch(r"[0-9a-f]{64}", root_raw):
        return hmac.compare_digest(root_raw, _repo_root_digest(repo_root))
    try:
        return os.path.realpath(root_raw) == os.path.realpath(str(repo_root))
    except OSError:
        return False


def _manifest_root_matches(recorded_root: str, repo_root: Path) -> bool:
    """Content-confirmed root matching, two arms like the run-start markers;
    the arm semantics live in ``_repo_root_matches_value`` (one shared copy
    for the matcher and the finalize pre-parse, so neither can drift)."""
    return _repo_root_matches_value(recorded_root, repo_root)


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


def _sanitize_manifest_error_value(raw: object) -> str:
    """Render a raw manifest field for a finalize abort line: newlines and
    other control characters stripped, truncated at 64 characters, so a
    corrupt manifest cannot forge log lines into the finalize stderr."""
    text = str(raw)
    return "".join(ch for ch in text if ch.isprintable())[:64]


def _finalize_identity_mismatch(
    payload: object, repo_root: Path
) -> Optional[tuple[str, str]]:
    """The finalize-path identity contract over the raw payload, checked
    BEFORE the tolerant from_dict parse: a manifest this finalizer accepts
    must carry this repository's identity at the contract version, reusing
    the record's existing keys (``schema`` == ``MANIFEST_SCHEMA_VERSION``
    is the version, ``repo_root`` is the identity value).

    Returns ``(schema_render, root_state)`` for the named abort when the
    payload fails the contract (a missing, wrong-version, or non-int
    ``schema``, or a ``repo_root`` that is missing or matches neither arm of
    ``_repo_root_matches_value`` - the 64-hex fingerprint equal to this
    repo's identity digest, or a resolvable path equal to this
    repository); None when the payload may proceed to the tolerant read.
    The rendered root state is exactly one of ``fingerprint`` (a 64-hex
    root that is not this repository's), ``path`` (any non-hex root
    value), or ``absent`` (the key is missing). The two-arm root matching
    and the field itself stay shared with the frozen sweep-gate and adopt
    consumers; only the finalize path turns a mismatch into a named
    non-zero abort."""
    if not isinstance(payload, dict):
        return ("absent", "absent")
    if "schema" in payload:
        schema_render = _sanitize_manifest_error_value(payload["schema"])
    else:
        schema_render = "absent"
    if "repo_root" not in payload:
        return (schema_render, "absent")
    root_raw = payload["repo_root"]
    if isinstance(root_raw, str) and re.fullmatch(r"[0-9a-f]{64}", root_raw):
        state = "fingerprint"
    else:
        # Non-hex string values and non-string values classify alike for
        # the abort line: neither is a fingerprint.
        state = "path"
    schema = payload.get("schema")
    schema_ok = (
        isinstance(schema, int)
        and not isinstance(schema, bool)
        and schema == MANIFEST_SCHEMA_VERSION
    )
    if schema_ok and _repo_root_matches_value(root_raw, repo_root):
        return None
    return (schema_render, state)


def _detect_interrupted_runs(
    done_session_dir: Path, repo_root: Path, warnings: Optional[list[str]] = None
) -> list[RunManifest]:
    """Every manifest whose ``complete`` flag is still false and which no
    other manifest adopts (an ``adopted_from`` link names it): the
    interrupted runs this Step 0 reports. A finalized (``complete`` true)
    manifest is never an orphan - that is what keeps a completed commit-less
    run from misfiring the detection - and adoption is itself the suppression
    record. Two widenings shape the set: a dead-root record (its recorded
    ``repo_root`` value fails the two-arm match - the manifest of a checkout
    that no longer exists) stays in the orphan set when ``complete`` is false
    and nothing adopts it, instead of being silently skipped by the root
    filter, so a dead-boundary incident surfaces until it closes; and a
    manifest carrying a ``dispositioned`` record is
    no longer detected as an orphan
    (the disposition is the sanctioned one-time closure: the adoption
    link is the first suppression shape, the disposition record the second).
    Unreadable records are skipped, never raised; a corrupt record is named
    through ``warnings`` when provided (F10)."""
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
        manifests.append(manifest)
    adopted = {m.adopted_from for m in manifests if m.adopted_from}
    return [
        m
        for m in manifests
        if not m.complete
        and m.run_id not in adopted
        and m.dispositioned is None
    ]


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
    # Unquote each row so the ignored arm matches the ordinary arm's quoting
    # discipline (a C-quoted row keeps literal quote characters no filesystem
    # path carries); the emit roundtrip abort's [\v\f]\.md$ term is reachable
    # only through this unquoting.
    return [
        _unquote_porcelain_path(ln)
        for ln in proc.stdout.splitlines()
        if ln.strip()
    ]


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
    tab newline CR vertical tab form feed inside, so the verbatim row keeps
    literal quote characters that no filesystem path carries."""
    if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
        body = path[1:-1]
        return (
            body.replace("\\\\", "\x00")
            .replace('\\"', '"')
            .replace("\\t", "\t")
            .replace("\\n", "\n")
            .replace("\\r", "\r")
            .replace("\\v", "\v")
            .replace("\\f", "\f")
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
    """Pre-docs gate: validate the run's gated plan candidates through the
    migrated readiness validator as a CLI subprocess child.

    The child arm branches on the migrated validator's four-outcome contract
    (scripts/OUTCOME_CONTRACT.md) instead of routing every child exit above 1
    into an indeterminate bucket: a child exit 0 passes; exit 1 (a modeled
    readiness fail, `OUTCOME: fail`) lands in the failed bucket with the
    child's first-failure line; exit 2 (which the migrated child never
    models; a crash or legacy shape, `OUTCOME: indeterminate`) keeps an
    indeterminate bucket naming the child; exit 3 (`OUTCOME: tool_error`,
    the sibling-compat mismatch and the argparse usage override included)
    lands in a tool-error bucket reported as the gate's tool-error evidence,
    since a child that could not run reliably is never a readiness fail; and
    a child run with no final OUTCOME line classifies tool error per the
    contract's no-line rule winning over the exit code. A label/exit
    contradiction is an indeterminate gate result naming the child. The
    aggregate exit carries the dominant bucket (tool error dominates
    indeterminate dominates fail, matching ``phase_exit``) while the message
    names every non-passing bucket (the contract's multi-input rule). The
    candidate derivation, the exemption arms, and the missing-validator
    deployment-gap refuse keep their pre-migration shape.
    """
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
    indeterminate: list[str] = []
    tool_errors: list[str] = []
    for plan_rel in derivation.candidates:
        proc = ctx.run(
            [sys.executable, str(validator), str(ctx.repo_root / plan_rel)],
            cwd=ctx.repo_root,
        )
        stdout_rows = [
            row.strip()
            for row in (proc.stdout or "").splitlines()
            if row.strip() and not row.strip().startswith(OUTCOME_LINE_PREFIX)
        ]
        stderr_rows = [
            row.strip()
            for row in (proc.stderr or "").splitlines()
            if row.strip()
        ]
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
        label = _child_final_outcome(proc)
        if label is None:
            # The contract's no-line rule wins over the exit code: a child
            # run with no final OUTCOME line (a crash or a legacy shape) is
            # never a silent pass.
            tool_errors.append(
                f"{plan_rel} (no final OUTCOME line, child exit "
                f"{proc.returncode}; evidence: {first_failure})"
            )
        elif label == "pass" and proc.returncode == 0:
            passed.append(str(plan_rel))
        elif label == "fail" and proc.returncode == 1:
            failed.append((str(plan_rel), first_failure))
        elif label == "indeterminate" and proc.returncode == 2:
            indeterminate.append(
                f"{plan_rel} (child exit {proc.returncode}; evidence: "
                f"{first_failure})"
            )
        elif label == "tool_error" and proc.returncode == 3:
            tool_errors.append(f"{plan_rel} (evidence: {first_failure})")
        else:
            indeterminate.append(
                f"{plan_rel} (child exit {proc.returncode} contradicts its "
                f"OUTCOME: {label} line)"
            )

    remove.update(passed)
    _prune_deliverables(ctx, remove)

    parts = [
        f"passed={len(passed)}",
        f"exempted={len(derivation.exempted)}",
        f"archived={len(derivation.archived)}",
        f"failed={len(failed)}",
        f"indeterminate={len(indeterminate)}",
        f"tool_error={len(tool_errors)}",
    ]
    message = "plan readiness: " + ", ".join(parts)
    if failed:
        message += "; first failures: " + "; ".join(
            f"{plan}: {reason}" for plan, reason in failed[:3]
        )
    if indeterminate:
        message += "; indeterminate: " + "; ".join(indeterminate[:3])
    if tool_errors:
        message += "; tool error: " + "; ".join(tool_errors[:3])
    if tool_errors:
        # Tool error dominates indeterminate dominates fail for the same
        # run (the contract's multi-input rule); every bucket stays named
        # in the message either way. A child that could not run reliably
        # is never a readiness fail.
        return GateResult(gate, 3, message, warnings=[])
    if indeterminate:
        return GateResult(gate, 2, message, warnings=[])
    if failed:
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
    """Pre-docs gate: validate the run's owned staging docs through the
    migrated review-staging validator as a CLI subprocess child.

    The child arm branches on the migrated validator's four-outcome contract
    (scripts/OUTCOME_CONTRACT.md) instead of collapsing every nonzero child
    exit into the failed bucket: a child exit 0 passes; exit 1 (a modeled
    invalid record, `OUTCOME: fail`) lands in the failed bucket with the
    validator's finding tail; exit 2 (`OUTCOME: indeterminate`) lands in an
    indeterminate bucket naming the target; exit 3 (`OUTCOME: tool_error`)
    lands in a tool-error bucket naming the target; and a child run with no
    final OUTCOME line classifies tool error per the contract's no-line rule
    winning over the exit code (a legacy or crashed child is never a silent
    pass). A label/exit contradiction is an indeterminate gate result naming
    the target. The aggregate exit carries the dominant bucket (tool error
    dominates indeterminate dominates fail, matching ``phase_exit``) while
    the message names every non-passing bucket (the contract's multi-input
    rule). The sidecar twin routing and the missing-twin fail-closed arm
    keep their pre-migration shape."""
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
    finding_tails: list[str] = []
    indeterminate: list[str] = []
    tool_errors: list[str] = []
    for candidate in candidates:
        target = candidate
        if candidate.name.endswith(".stats.json"):
            # A sidecar candidate is validated through its markdown twin:
            # the validator's --hard markdown path already covers sidecar
            # schema, agreement, and digest, while the markdown shape checks
            # produce only wrong-shape failures against JSON. String slicing
            # (not Path.with_suffix, which would replace only the final
            # .json and yield .stats.md). A missing twin is an owned
            # half-pair: fail closed naming the sidecar.
            twin = candidate.with_name(candidate.name[: -len(".stats.json")] + ".md")
            if not twin.is_file():
                failed.append(str(candidate) + " (sidecar without markdown twin)")
                continue
            target = twin
        proc = ctx.run(
            [sys.executable, str(validator), "--hard", str(target)],
            cwd=ctx.repo_root,
        )
        evidence = [
            row.strip()
            for row in ((proc.stdout or "") + "\n" + (proc.stderr or "")).splitlines()
            if row.strip() and not row.strip().startswith(OUTCOME_LINE_PREFIX)
        ]
        tail = evidence[-1] if evidence else "no evidence rows"
        label = _child_final_outcome(proc)
        if label is None:
            tool_errors.append(
                f"{target} (no final OUTCOME line, child exit "
                f"{proc.returncode}; the contract's no-line rule classifies "
                "tool error, never a pass)"
            )
        elif label == "pass" and proc.returncode == 0:
            pass
        elif label == "fail" and proc.returncode == 1:
            failed.append(str(target))
            finding_tails.append(f"{target.name}: {tail}")
        elif label == "indeterminate" and proc.returncode == 2:
            indeterminate.append(str(target))
        elif label == "tool_error" and proc.returncode == 3:
            tool_errors.append(str(target))
        else:
            indeterminate.append(
                f"{target} (child exit {proc.returncode} contradicts its "
                f"OUTCOME: {label} line)"
            )
    if failed or indeterminate or tool_errors:
        rc = 3 if tool_errors else (2 if indeterminate else 1)
        if rc == 1:
            message = "review-staging validation failed for: " + ", ".join(failed)
            if finding_tails:
                message += "; validator finding tail: " + " | ".join(finding_tails)
        elif rc == 2:
            message = (
                "review-staging validation indeterminate for: "
                + ", ".join(indeterminate)
            )
        else:
            message = (
                "review-staging validation tool error for: "
                + ", ".join(tool_errors)
            )
        if rc != 1 and failed:
            message += "; also failed: " + ", ".join(failed)
        if rc != 2 and indeterminate:
            message += "; also indeterminate: " + ", ".join(indeterminate)
        if rc != 3 and tool_errors:
            message += "; also tool error: " + ", ".join(tool_errors)
        return GateResult(gate, rc, message, warnings=warnings)
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
    if kept:
        message += "; kept: " + ", ".join(kept)
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
    candidate derivation accepts nested plan paths. An archived-plan session
    that still holds its captured ``closeout-baseline.json`` as a regular
    file is exempt from removal only while the baseline is fresh: the
    baseline is the mechanical witness that a run owns the directory and its
    transfer-out (execute-plan lifecycle step 5) may still be pending. The
    exemption is age-bounded by ``STALE_BASELINE_GRACE_H``: a baseline whose
    mtime age is within the grace window keeps the transfer-out-pending
    exemption unchanged; the boundary comparison keeps via ``<=``, so a
    baseline whose age is exactly 48h is within the window. The pending-plan
    arm's ``continue`` precedes the baseline branch, so an active session's
    stale baseline is kept by precedence, not by the exemption. A crashed
    run's directory lingers by the same
    witness only up to that window: once the baseline's age exceeds it,
    nothing has consumed the baseline for two days and the directory IS
    removed here as a stale closeout baseline (destruction for the stale
    class moves from the interrupted-run report to this arm), and the
    removal deletes the session manifest, ending the interrupted-run
    report's surfacing of that run. A stale removal whose rmtree raises
    OSError appends ``str(session) + " (stale closeout baseline
    removal-failed)"`` to removed instead of a kept row: the row lands in
    removed while the directory survives (removed is report-visible, not
    existential), so a repeatedly failing stale sweep is visible as a
    distinct class instead of retrying silently. An unreadable baseline
    mtime keeps the
    exemption (fail-open to keep, the safe direction for a witness file)."""
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
        if (session / "closeout-baseline.json").is_file():
            baseline_path = session / "closeout-baseline.json"
            try:
                age_hours = (time.time() - os.path.getmtime(baseline_path)) / 3600
            except OSError:
                # Unreadable baseline mtime keeps the exemption: fail-open to
                # keep, the safe direction for a witness file.
                age_hours = 0.0
            if age_hours <= STALE_BASELINE_GRACE_H:
                kept.append(str(session) + " (kept: closeout baseline present; transfer-out may be pending)")
                continue
            try:
                shutil.rmtree(session)
                removed.append(str(session) + " (stale closeout baseline)")
            except OSError:
                # The directory survives the failed rmtree; the report still
                # names the sweep's failed attempt (not a kept row), so a
                # repeatedly failing stale removal stays visible per retry.
                removed.append(
                    str(session) + " (stale closeout baseline removal-failed)"
                )
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
    content_patterns = list(CREDENTIAL_CONTENT_PATTERNS)
    if ctx.artifact_visibility != "private":
        content_patterns.extend(PUBLIC_ARTIFACT_CONTENT_PATTERNS)
        families = "content families: credential+public-artifact"
    else:
        families = "content families: credential (repo declares private visibility)"

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
                for pattern in content_patterns:
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
                for pattern in content_patterns:
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
    #
    # Outcome-contract migration batch 2, Task 5: the arm branches on the
    # migrated scan child's four outcomes (scripts/OUTCOME_CONTRACT.md)
    # instead of collapsing every nonzero exit into a finding: a child exit
    # 1 (`OUTCOME: fail`) keeps landing in findings with the child's tail
    # rows; a child exit 2 (`OUTCOME: indeterminate`) is an indeterminate
    # gate result naming the child; a child exit 3 (`OUTCOME: tool_error`)
    # is a tool-error gate result naming the child; and a child run with no
    # final OUTCOME line classifies tool error per the contract's no-line
    # rule winning over the exit code (a scan that cannot report its outcome
    # is never a silent pass). A label/exit contradiction is an
    # indeterminate gate result naming the child.
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
                evidence_rows = [
                    row.strip()
                    for row in (proc.stdout or "").splitlines()
                    if row.strip()
                    and not row.strip().startswith(OUTCOME_LINE_PREFIX)
                ] + [
                    row.strip()
                    for row in (proc.stderr or "").splitlines()
                    if row.strip()
                ]
                evidence = evidence_rows[-1] if evidence_rows else "no output"
                label = _child_final_outcome(proc)
                if label is None:
                    # The contract's no-line rule wins over the exit code.
                    return GateResult(
                        gate,
                        3,
                        f"public-hygiene scan child tool error: {scan.name} "
                        f"emitted no final OUTCOME line (child exit "
                        f"{proc.returncode}; evidence: {evidence})",
                        warnings=warnings,
                    )
                if label == "fail" and proc.returncode == 1:
                    tail_rows = [
                        row
                        for row in (proc.stdout or "").strip().splitlines()
                        if row.strip()
                        and not row.strip().startswith(OUTCOME_LINE_PREFIX)
                    ][-10:]
                    findings.append(
                        "public-hygiene scan failed: " + " | ".join(tail_rows)
                    )
                elif label == "indeterminate" and proc.returncode == 2:
                    return GateResult(
                        gate,
                        2,
                        f"public-hygiene scan child indeterminate: {scan.name} "
                        f"could not complete its scan (child exit 2; evidence: "
                        f"{evidence})",
                        warnings=warnings,
                    )
                elif label == "tool_error" and proc.returncode == 3:
                    return GateResult(
                        gate,
                        3,
                        f"public-hygiene scan child tool error: {scan.name} "
                        f"could not run reliably (child exit 3; evidence: "
                        f"{evidence})",
                        warnings=warnings,
                    )
                elif label != "pass" or proc.returncode != 0:
                    return GateResult(
                        gate,
                        2,
                        f"public-hygiene scan child exit {proc.returncode} "
                        f"contradicts its OUTCOME: {label} line ({scan.name})",
                        warnings=warnings,
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
        + "); " + families,
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
        # Fallback (plan 2026-09-28-em-dash-whole-file-gate-added-lines-
        # selection Task 2): a non-zero touched probe may carry pre-existing
        # committed violations on unchanged lines. Partition the probe's
        # COMPLETE stdout (every reported row of this same invocation,
        # captured before any failure rendering; never the failure message's
        # last-10-rows tail, so a run with more than ten hitting files cannot
        # silently pass a dirty added line) into untracked and tracked hit
        # paths. Untracked hits still fail whole-file; each tracked hit is
        # adjudicated by added-lines --base HEAD: clean means the hit is
        # pre-existing committed bytes and passes with a baseline row; dirty
        # means this run's insertion and still fails.
        hit_rows = [
            row for row in (proc.stdout or "").strip().splitlines() if row.strip()
        ]
        hit_paths = _dedup_preserving_order(
            [row.split(":", 1)[0] for row in hit_rows if ":" in row]
        )
        first_hit_line: dict[str, str] = {}
        for row in hit_rows:
            parts = row.split(":", 2)
            if len(parts) >= 2 and parts[0] not in first_hit_line:
                # The touched probe reports the first violating line per file.
                first_hit_line[parts[0]] = parts[1]
        others = ctx.git("ls-files", "--others", "--exclude-standard")
        if others.returncode == 0:
            untracked = set(others.stdout.splitlines())
        else:
            # Fail-closed polarity (the em-dash origin's candidate 1): when
            # the untracked enumeration fails, every hit is treated as
            # untracked and fails whole-file, so a tracking outage can never
            # launder hits through the tracked pre-existing baseline arm;
            # candidate 4's residual-harm note is the reason this arm stays
            # small rather than load-bearing.
            untracked = set(hit_paths)
        untracked_hits = [p for p in hit_paths if p in untracked]
        if untracked_hits:
            return GateResult(
                gate,
                1,
                "em dash scan failed: new prose must be whole-file clean: "
                + ", ".join(untracked_hits),
                warnings=[],
            )
        baseline_rows: list[str] = []
        for path in [p for p in hit_paths if p not in untracked]:
            check = ctx.run(
                ["bash", str(script), "added-lines", "--base", "HEAD", "--", path],
                cwd=ctx.repo_root,
            )
            if check.returncode != 0:
                dirty_rows = [
                    row
                    for row in (check.stdout or "").strip().splitlines()
                    if row.strip()
                ][-10:]
                return GateResult(
                    gate,
                    1,
                    "em dash scan failed: added-lines --base HEAD flagged "
                    f"working-tree insertions in {path}: "
                    + " | ".join(dirty_rows),
                    warnings=[],
                )
            baseline_rows.append(
                "pre-existing (known-violation baseline): "
                f"{path}:{first_hit_line.get(path, '?')}"
            )
        if baseline_rows:
            return GateResult(
                gate,
                0,
                "em dash scan clean (pre-existing known-violation baseline): "
                + " | ".join(baseline_rows),
                warnings=[],
            )
        # No parsable hit path (unexpected probe output shape): keep the
        # legacy touched-tail failure rather than inventing a pass.
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


def gate_description_length(ctx: GateContext) -> GateResult:
    gate = "description-length"
    script = ctx.resolve_script(
        "DESCRIPTION_LENGTH_CHECK_SCRIPT", "check_skill_description_length.py"
    )
    if script is None:
        message = (
            "deployment gap: check_skill_description_length.py absent at "
            "every resolved path (env override, repo-local scripts/, runtime "
            "home copy); remedy: deploy the script to the runtime home "
            "scripts/ directory; never use the recorded-stop exception for a "
            "deployment gap"
        )
        return GateResult(gate, 1, message, warnings=[])
    proc = ctx.run([sys.executable, str(script)], cwd=ctx.repo_root)
    if proc.returncode != 0:
        # The checker names over-cap files on stderr and warns on stderr;
        # tail both so the failure message carries the named files.
        tail_rows = [
            row
            for row in (
                (proc.stdout or "") + "\n" + (proc.stderr or "")
            ).strip().splitlines()
            if row.strip()
        ][-10:]
        return GateResult(
            gate,
            1,
            "description length gate failed: " + " | ".join(tail_rows),
            warnings=[],
        )
    warn_rows = [
        row for row in (proc.stderr or "").strip().splitlines() if row.strip()
    ]
    return GateResult(
        gate,
        0,
        "description length gate passed",
        warnings=warn_rows,
    )


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


# --------------------------------------------------------------------------- #
# Gate: post-landing-staging (done sweep pre-commit phase).
# --------------------------------------------------------------------------- #
# Record-only allowlist (plan Terms, "Record-only allowlist"): the standing
# peer edit to the development lessons document is the dirty-path class that
# must never be committed or reverted by any landing or closeout step (the
# witnessed survivor of the selective 2026-10-03 recovery). Owned HERE once,
# with this provenance comment; scripts/land_squash.sh deliberately carries no
# copy - its dirty-intersection pre-refusal is allowlist-agnostic and is the
# record-only protection on the landing side.
RECORD_ONLY_ALLOWLIST = frozenset({
    "projects/.ai-playbook/development_lessons.md",
})


def _resolve_primary_checkout(ctx: GateContext) -> tuple[Optional[Path], str]:
    """The first ``git worktree list --porcelain`` worktree entry (the
    execute-plan worktree bootstrap recipe's PRIMARY resolution): execution
    lanes run closeouts in linked worktrees whose own index is not the
    primary index. Returns (path, error); error is empty on success."""
    proc = ctx.git("worktree", "list", "--porcelain")
    if proc.returncode != 0:
        return None, (
            "git worktree list --porcelain failed: "
            + (proc.stderr or "").strip()
        )
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            return Path(line[len("worktree "):]).expanduser(), ""
    return None, "git worktree list --porcelain printed no worktree entry"


def _classify_primary_status(rows: list[str]) -> tuple[set, set, set]:
    """Split primary-checkout porcelain rows into (staged, unstaged_dirty,
    untracked) path sets: the index column (X) drives the staged set, the
    worktree column (Y) the unstaged tracked set (an ``MM`` row feeds both),
    ``??`` rows the untracked set. Rename rows keep only their new side,
    C-quoted rows are unquoted, mirroring ``_porcelain_paths``."""
    staged: set = set()
    unstaged: set = set()
    untracked: set = set()
    for row in rows:
        if len(row) < 4:
            continue
        xy = row[:2]
        rest = row[3:]
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        rest = _unquote_porcelain_path(rest)
        if xy == "??":
            untracked.add(rest)
            continue
        if xy[0] != " ":
            staged.add(rest)
        if xy[1] != " ":
            unstaged.add(rest)
    return staged, unstaged, untracked


def _merge_lock_held(ctx: GateContext) -> tuple[Optional[bool], str]:
    """``done-lock.sh merge-status`` re-consult, read-only. Returns
    (held, evidence): held is True (a holder is reported), False (free), or
    None (the consult itself could not run or could not be parsed - the
    residue attribution then stays undecided, never a residue refusal)."""
    script = ctx.resolve_script("DONE_LOCK_SCRIPT", "done-lock.sh")
    if script is None:
        return None, (
            "done-lock.sh not resolvable (env override, repo-local scripts/, "
            "runtime home scripts/ copy)"
        )
    proc = ctx.run(["bash", str(script), "merge-status"], cwd=ctx.repo_root)
    text = (proc.stdout or "").strip()
    if proc.returncode != 0 or not text:
        return None, (
            f"merge-status run failed (exit {proc.returncode}); "
            f"evidence: {((proc.stderr or '') or text).strip()[:200]}"
        )
    lines = text.splitlines()
    first = lines[0]
    if ": held" in first:
        label = ""
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("label:"):
                label = stripped.split(":", 1)[1].strip()
                break
        evidence = first.strip()
        if label:
            evidence += f" (holder label: {label})"
        return True, evidence
    if ": free" in first:
        return False, first.strip()
    return None, f"unparseable merge-status output: {first.strip()[:200]}"


def gate_post_landing_staging(ctx: GateContext) -> GateResult:
    """Pre-commit gate: the post-landing staging invariant over the primary
    checkout (plan: squash-landing-failure-path-guard, Task 3).

    The primary checkout's index must match HEAD except for staged paths
    owned by the resolvable current-session manifest (the foreign-staging
    ownership pattern: the union of ``owned_paths``, ``owned_plan_paths``,
    ``owned_review_paths``, named as owned); unstaged tracked modifications
    are permitted only for the record-only allowlist. Residue is inspected
    FIRST and only then is ``done-lock.sh merge-status`` re-consulted, so
    residue observed while the lock is now held reports indeterminate (a
    landing is in flight, never a violation) instead of a refusal - closing
    the consult-then-inspect race. Any other residue fails the closeout
    naming the residue paths, the sanctioned cleanup recipe (the helper's
    probe-then-reland path), and the operator escape for dead residue;
    record-only allowlist paths are never escapable. Untracked paths are
    reported-not-failing (warning lines): the witnessed hazard is index and
    tracked-modification residue. The gate inspects the primary checkout
    read-only (``git -C <primary>``); an unresolvable worktree list or an
    unreadable primary checkout is a tool error.
    """
    gate = "post-landing-staging"
    primary, error = _resolve_primary_checkout(ctx)
    if primary is None:
        return GateResult(
            gate,
            3,
            "post-landing-staging gate could not resolve the primary "
            f"checkout: {error}",
            warnings=[],
        )
    status = ctx.run(
        ["git", "-C", str(primary), "status", "--porcelain=v1", "-uall"],
        cwd=ctx.repo_root,
    )
    if status.returncode != 0:
        return GateResult(
            gate,
            3,
            "post-landing-staging gate could not read the primary checkout "
            f"at {primary}: {(status.stderr or '').strip()[:200]}",
            warnings=[],
        )
    staged, unstaged, untracked = _classify_primary_status(
        status.stdout.splitlines()
    )
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    warnings: list[str] = []
    owned: Optional[set] = None
    if manifest is None:
        # The ownership narrowing is skipped, never the check: the strict
        # staged-empty comparison stays, with the unresolvable record named.
        warnings.append(
            "post-landing-staging: no resolvable run manifest for the "
            "current session window (Step 0 record absent, foreign-rooted, "
            "or schema-invalid); the ownership narrowing is skipped and the "
            "strict staged-empty check kept"
        )
    else:
        owned = {
            _manifest_review_rel(ctx, recorded)
            for recorded in (
                list(manifest.owned_paths)
                + list(manifest.owned_plan_paths)
                + list(manifest.owned_review_paths)
            )
        }
    staged_residue = sorted(staged - owned) if owned is not None else sorted(staged)
    owned_staged = sorted(staged & owned) if owned is not None else []
    dirty_residue = sorted(unstaged - RECORD_ONLY_ALLOWLIST)
    allowed_dirty = sorted(unstaged & RECORD_ONLY_ALLOWLIST)
    residue = staged_residue + dirty_residue
    if residue:
        held, evidence = _merge_lock_held(ctx)
        residue_render = (
            "staged path(s): " + (", ".join(staged_residue) or "none")
            + "; unstaged path(s): " + (", ".join(dirty_residue) or "none")
            + ("; record-only allowlist path(s) present and permitted: "
               + ", ".join(allowed_dirty) if allowed_dirty else "")
        )
        if held is None:
            return GateResult(
                gate,
                2,
                "post-landing-staging gate reported indeterminate: primary "
                f"checkout residue observed ({residue_render}) but the merge "
                "lock state could not be consulted; evidence: "
                + evidence,
                warnings=warnings,
            )
        if held:
            return GateResult(
                gate,
                2,
                "post-landing-staging gate reported indeterminate: primary "
                f"checkout residue observed ({residue_render}) while the "
                "merge lock is held (a landing is in flight, not a "
                f"violation); holder: {evidence}",
                warnings=warnings,
            )
        return GateResult(
            gate,
            1,
            "post-landing-staging gate failed: primary checkout residue "
            f"after landing ({residue_render}); sanctioned cleanup: the "
            "land_squash.sh probe-then-reland path (run scripts/land_squash.sh "
            "probe, resolve or compose, then scripts/land_squash.sh land "
            "under the merge lock); operator escape for dead residue only "
            "(done-lock.sh merge-status free AND the path is not peer-live "
            "dirt): git restore --staged --worktree -- <path> per residue "
            "path; record-only allowlist path(s) are never escapable",
            warnings=warnings,
        )
    message = (
        "post-landing-staging gate passed: primary index matches HEAD (no "
        "unowned staging, no unallowlisted tracked modification)"
    )
    if allowed_dirty:
        message += (
            "; record-only allowlist path(s) permitted: "
            + ", ".join(allowed_dirty)
        )
    if owned_staged:
        message += (
            "; staged path(s) owned by the current session manifest: "
            + ", ".join(owned_staged)
        )
    if untracked:
        warnings.append(
            "post-landing-staging: untracked path(s) in the primary checkout "
            "(reported, not failing): " + ", ".join(sorted(untracked))
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


# --------------------------------------------------------------------------- #
# Gate: archive-ceremony (done Step 2.8 pre-commit; plan 2026-10-01-done-
# boundary-receipt-and-closeout-gate-sweep Tasks 1 and 2): for every plan
# archive the derivation surfaces, checkbox completeness plus the exec-review
# record of the run that executed it.
# --------------------------------------------------------------------------- #
ARCHIVE_SLUG_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
# The series token sits at the end of the record's stem, right before the
# ``.md`` extension real staging docs carry.
EXEC_REVIEW_SERIES_RE = re.compile(r"-exec-r\d+\.md$")


def _archive_state_dirs(ctx: GateContext) -> list[tuple[str, Path]]:
    """The archive state directories (the same three the plans-archive-twin
    gate scans), state name first for report lines."""
    return [
        ("completed", ctx.plans_completed_dir),
        ("deferred", ctx.plans_dir / "deferred"),
        ("rejected", ctx.plans_dir / "rejected"),
    ]


def _archive_state_of(ctx: GateContext, rel: str) -> Optional[str]:
    """The state name when a repo-relative path sits inside an archive state
    directory; None when it sits at the plans root (or anywhere else)."""
    for state, directory in _archive_state_dirs(ctx):
        try:
            prefix = str(
                directory.resolve().relative_to(ctx.repo_root.resolve())
            )
        except ValueError:
            continue
        if rel.startswith(prefix + "/"):
            return state
    return None


def _plans_pathspec(ctx: GateContext) -> str:
    """The plans home as a repo-relative pathspec (absolute fallback when the
    resolved home sits outside the repo root), same derivation shape as the
    plan-readiness candidate enumeration."""
    if _is_relative_to(ctx.plans_dir, ctx.repo_root):
        return str(ctx.plans_dir.resolve().relative_to(ctx.repo_root.resolve()))
    return str(ctx.plans_dir)


def _archive_twin_at_head(ctx: GateContext, plan_rel: str) -> Optional[str]:
    """The repo-relative archive twin of a vanished plan path when one exists
    at HEAD (same basename in the first archive state directory carrying it);
    None when no archive twin is committed."""
    name = Path(plan_rel).name
    for _state, directory in _archive_state_dirs(ctx):
        try:
            prefix = str(
                directory.resolve().relative_to(ctx.repo_root.resolve())
            )
        except ValueError:
            continue
        twin_rel = f"{prefix}/{name}"
        if ctx.git("cat-file", "-e", f"HEAD:{twin_rel}").returncode == 0:
            return twin_rel
    return None


def _derive_archived_plans(
    ctx: GateContext,
) -> tuple[list[tuple[str, str]], list[str]]:
    """archive-ceremony derivation: every plan archive this run's boundary
    surfaces, as ``(repo-relative archive path, plan bytes)`` pairs, plus
    non-failing note lines.

    Three shapes, each with its own byte source:

    (a) staged or worktree rename rows over the plans pathspec (the
        ``R old -> new`` rows ``_porcelain_lines`` returns) whose new side
        sits in an archive state directory; bytes read from the file at the
        new path, which exists at both pre-commit invocations;
    (b) committed renames into ``plans_completed_dir`` since this run's
        manifest boundary: a ``git diff --find-renames <base>..HEAD
        --name-status`` over the plans pathspec where ``<base>`` is the
        active run manifest's ``start_commit`` with the gate_doc_registry
        precedent's ``ORIG_HEAD`` fallback when absent; when neither
        resolves, this shape surfaces nothing this run and the skip is
        noted; bytes from the HEAD blob at the archived path. This is the
        lib's first rename-detecting name-status diff on purpose: every
        existing name-status diff uses ``--no-renames`` because its
        consumers need per-side change-type rows, while this gate needs the
        rename pairing itself;
    (c) stale plan-deliverables lines whose recorded plan path no longer
        exists because it now sits archived; bytes from the archive twin at
        HEAD.
    """
    archives: list[tuple[str, str]] = []
    notes: list[str] = []
    seen: set[str] = set()
    plans_rel = _plans_pathspec(ctx)

    # Shape (a): staged/worktree renames into an archive state directory.
    for row in _porcelain_lines(ctx, plans_rel):
        xy = row[:2]
        rest = row[3:]
        if " -> " not in rest or not (xy[0] in ("R", "C") or xy[1] == "R"):
            continue
        _old, new = rest.split(" -> ", 1)
        new = _unquote_porcelain_path(new)
        if _archive_state_of(ctx, new) is None:
            # A rename inside the plans home is not an archive: the gate
            # checks archives only, never an ordinary in-root rename.
            continue
        try:
            text = (ctx.repo_root / new).read_text(encoding="utf-8")
        except OSError:
            notes.append(
                f"archive-ceremony: staged archive unreadable, skipped: {new}"
            )
            continue
        if new not in seen:
            seen.add(new)
            archives.append((new, text))

    # Shape (b): committed renames into the completed archive since the run
    # manifest boundary (ORIG_HEAD fallback; neither resolves: skip, noted).
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    base = manifest.start_commit if manifest is not None else "ORIG_HEAD"
    verify = ctx.git("rev-parse", "-q", "--verify", f"{base}^{{commit}}")
    if verify.returncode != 0:
        notes.append(
            "archive-ceremony: committed-rename arm skipped this run (no "
            "resolvable boundary commit: neither the active run manifest's "
            f"start_commit nor ORIG_HEAD resolves, tried {base})"
        )
    else:
        diff = ctx.git(
            "diff",
            "--find-renames",
            "--name-status",
            f"{base}..HEAD",
            "--",
            plans_rel,
        )
        try:
            completed_prefix = str(
                ctx.plans_completed_dir.resolve().relative_to(
                    ctx.repo_root.resolve()
                )
            )
        except ValueError:
            completed_prefix = None
        if diff.returncode != 0:
            notes.append(
                "archive-ceremony: committed-rename diff failed, arm "
                f"skipped: {diff.stderr.strip() or 'git diff failed'}"
            )
        elif completed_prefix is not None:
            for line in diff.stdout.splitlines():
                fields = line.split("\t")
                if len(fields) < 3 or not fields[0].startswith("R"):
                    continue
                new = _unquote_porcelain_path(fields[-1])
                if not new.startswith(completed_prefix + "/"):
                    continue
                show = ctx.git("show", f"HEAD:{new}")
                if show.returncode != 0:
                    notes.append(
                        "archive-ceremony: committed archive unreadable at "
                        f"HEAD, skipped: {new}"
                    )
                    continue
                if new not in seen:
                    seen.add(new)
                    archives.append((new, show.stdout))

    # Shape (c): stale plan-deliverables lines whose recorded plan path no
    # longer exists because it now sits archived (twin bytes from HEAD).
    deliverables_path = ctx.done_session_dir / "plan-deliverables.txt"
    if deliverables_path.is_file():
        try:
            deliverables = [
                ln.strip()
                for ln in deliverables_path.read_text(
                    encoding="utf-8"
                ).splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
        except OSError:
            deliverables = []
        for rel in deliverables:
            if (ctx.repo_root / rel).exists():
                continue
            if _archive_state_of(ctx, rel) is not None:
                continue
            twin_rel = _archive_twin_at_head(ctx, rel)
            if twin_rel is None:
                continue
            show = ctx.git("show", f"HEAD:{twin_rel}")
            if show.returncode != 0:
                continue
            if twin_rel not in seen:
                seen.add(twin_rel)
                archives.append((twin_rel, show.stdout))

    return archives, notes


def _plan_slug(archive_rel: str) -> str:
    """The archived plan's slug: the file stem minus its leading date prefix
    (the slug form real review-record names use)."""
    return ARCHIVE_SLUG_DATE_PREFIX_RE.sub(
        "", Path(archive_rel).stem, count=1
    )


def _has_exec_review_record(ctx: GateContext, slug: str) -> bool:
    """True when any file under the resolved reviews home carries the plan's
    exec-review record: its name contains ``-plan-review-``, contains the
    archived plan's slug (the slug form is what real records use), and ends
    ``-exec-r<N>`` (the series token at the end of the stem, before the
    ``.md`` extension)."""
    if not ctx.reviews_dir.is_dir():
        return False
    for path in ctx.reviews_dir.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if "-plan-review-" not in name or slug not in name:
            continue
        if EXEC_REVIEW_SERIES_RE.search(name):
            return True
    return False


def gate_archive_ceremony(ctx: GateContext) -> GateResult:
    """Pre-commit gate over the plan archives this run's boundary surfaces.

    For every archive the derivation (``_derive_archived_plans``) surfaces,
    the gate checks checkbox completeness: plan bytes still carrying a
    ``- [ ]`` unchecked task box fail with the two sanctioned exits (check
    the boxes after verified work, or land a marked backfill completion
    record per the plans skill's archive-correction exception). A derived
    archive whose boxes are complete must further carry an exec-review
    record (the ``archived-plan review-coverage`` check)."""
    gate = "archive-ceremony"
    archives, notes = _derive_archived_plans(ctx)
    if not archives:
        message = "archive-ceremony gate passed: no plan archive surfaced this run"
        if notes:
            message += " (" + "; ".join(notes) + ")"
        return GateResult(gate, 0, message, warnings=notes)
    findings: list[str] = []
    for archive_rel, text in archives:
        unchecked = text.count("- [ ]")
        if unchecked:
            findings.append(
                f"archived plan {archive_rel} carries {unchecked} unchecked "
                "task box(es); sanctioned exits: check the boxes after the "
                "work is verified, or land a marked backfill completion "
                "record per the plans skill's archive-correction exception "
                "(per-checkbox (backfilled ...) markings on an explicitly "
                "marked backfill record)"
            )
            continue
        # archived-plan review-coverage: a box-complete archive must still
        # carry the execution run's review of record; its absence fails with
        # the reconstruction remedy (the cited-review-receipt-integrity
        # precedent: a marked reconstruction is valid, a silent one is not).
        slug = _plan_slug(archive_rel)
        if not _has_exec_review_record(ctx, slug):
            findings.append(
                f"archived plan {archive_rel} has no exec-review record "
                f"(no *-plan-review-{slug}-exec-r<N> file under the reviews "
                "home names the missing series); remedy: produce the "
                "exec-review record for the plan's final bytes, or land a "
                "marked reconstruction per the cited-review-receipt-"
                "integrity precedent"
            )
    if findings:
        return GateResult(
            gate,
            1,
            "archive-ceremony gate failed: " + "; ".join(findings),
            warnings=[],
        )
    return GateResult(
        gate,
        0,
        "archive-ceremony gate passed: "
        + f"{len(archives)} plan archive(s) checked, boxes complete: "
        + ", ".join(rel for rel, _text in archives),
        warnings=notes,
    )


# --------------------------------------------------------------------------- #
# Gate: execute-plan-closeout (pre-commit; plan 2026-10-01-execute-plan-
# squash-closeout-finalization Task 1): for every execute-plan session
# manifest the active done run owns, the terminal lifecycle evidence at the
# landing closeout boundary.
# --------------------------------------------------------------------------- #
EXECUTE_PLAN_STATE_FILENAME = "runtime_state.json"
# The runtime's own done statuses plus its checkbox seeding shape, mirrored
# from the runtime's ``_task_complete`` predicate (deliberately not an
# import: the runtime module is not a lib dependency), so this gate refuses
# exactly when the runtime would call the run machine-complete.
EXECUTE_PLAN_DONE_STATUSES = {"complete", "checkpointed", "deferred"}
CLOSEOUT_RESUME_REMEDY = (
    "remedy: re-enter the execute-plan continuation and finish Phase 4; "
    "the resumable-closeout checkpoint carries the resume"
)


def _closeout_task_done(task: object) -> bool:
    """One task through the runtime's done predicate: a done status
    (``complete``, ``checkpointed``, or the recovery ``deferred``) or a
    truthy plan checkbox."""
    if not isinstance(task, dict):
        return False
    return (
        task.get("status") in EXECUTE_PLAN_DONE_STATUSES
        or bool(task.get("checkbox"))
    )


def _closeout_all_tasks_done(payload: dict) -> bool:
    """True when every entry of the manifest's ``tasks`` map is done under
    the runtime's done predicate (an empty map is vacuously all-done: a
    taskless owned session is a broken run, and the closeout must not
    report it complete without the receipt)."""
    tasks = payload.get("tasks")
    if not isinstance(tasks, dict):
        return False
    return all(_closeout_task_done(task) for task in tasks.values())


def _closeout_owned_plan_slugs(manifest: RunManifest) -> list[str]:
    """The plan claims the done run owns: each ``owned_plan_paths`` entry's
    basename minus its ``.md`` suffix (the runtime binds ``plan_slug`` to
    the plan filename's full stem)."""
    slugs: list[str] = []
    for recorded in manifest.owned_plan_paths:
        name = Path(recorded).name
        if name.endswith(".md"):
            name = name[: -len(".md")]
        if name and name not in slugs:
            slugs.append(name)
    return slugs


def _closeout_boundary_anchor(text: str, basename: str) -> bool:
    """True when ``basename`` appears in ``text`` with a non-name character
    (or an edge) on both sides (the origins checker's boundary rule)."""
    pattern = re.compile(
        r"(?<![\w.-])" + re.escape(basename) + r"(?![\w.-])"
    )
    return pattern.search(text) is not None


def _closeout_registry_path(ctx: GateContext) -> Path:
    """The ownership registry home: the facts TOML key ``doc_registry_rel``
    when it resolves, else the conventional document-registry default."""
    raw = facts_paths.resolve_toml_key_raw(ctx.repo_root, "doc_registry_rel")
    rel = (
        raw.strip()
        if isinstance(raw, str) and raw.strip()
        else "docs/maintenance/document-registry.md"
    )
    path = Path(rel).expanduser()
    if not path.is_absolute():
        path = ctx.repo_root / path
    return path


def _closeout_registry_names(ctx: GateContext, archived_rel: str) -> bool:
    """True when some table row of the ownership registry boundary-anchors
    the archived plan's basename; a missing or unreadable registry names
    nothing (the caller refuses)."""
    try:
        text = _closeout_registry_path(ctx).read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError:
        return False
    basename = Path(archived_rel).name
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if _closeout_boundary_anchor(stripped, basename):
            return True
    return False


def _closeout_session_states(ctx: GateContext) -> list[Path]:
    """Every execute-plan session state file on disk, sorted by path."""
    if not ctx.execute_plan_dir.is_dir():
        return []
    return sorted(ctx.execute_plan_dir.glob(f"*/{EXECUTE_PLAN_STATE_FILENAME}"))


def _child_final_outcome(proc) -> Optional[str]:
    """A migrated child run's final ``OUTCOME:`` label per the outcome
    contract (scripts/OUTCOME_CONTRACT.md), or None when the run emitted no
    final OUTCOME line: the line counts only when it is the single
    ``OUTCOME:``-prefixed stdout row, is the final non-empty stdout row, and
    carries a label from the four-outcome vocabulary. Callers treat None as
    tool error (the contract's no-line rule: a run with no final OUTCOME line
    is not a pass)."""
    rows = [
        line.strip()
        for line in (proc.stdout or "").splitlines()
        if line.strip()
    ]
    outcome_rows = [
        line for line in rows if line.startswith(OUTCOME_LINE_PREFIX)
    ]
    if len(outcome_rows) != 1 or not rows or rows[-1] != outcome_rows[0]:
        return None
    label = outcome_rows[0][len(OUTCOME_LINE_PREFIX):].strip()
    return label if label in OUTCOME_VOCABULARY else None


def _closeout_verify_landed_complete(
    ctx: GateContext, slug: str, payload: dict, receipt: dict
) -> Optional[tuple[int, str]]:
    """The landed-complete verification arm over one ``terminal_receipt``:
    the FIRST unmet condition as a named ``(rc, message)`` pair whose rc is
    the outcome-contract code (1 refuse, 2 indeterminate, 3 tool error),
    None when (a) the archived bytes re-hash to the receipt digest, (b) the
    active plan path (the ``archive_gate.plan_path`` record when present,
    else ``plans_dir/<plan_slug>.md``) is absent from the index and the
    working tree, (c) the archived plan's promoted origins are closed per the
    origins checker invoked with ``--plan`` (no second origins parser), and
    (d) the ownership registry names the archived path. Arm (c) branches on
    the migrated child's four-outcome contract: a modeled straggler failure
    (exit 1) is a refuse; an indeterminate child (exit 2) is an indeterminate
    gate result, never a refuse; a tool-error child (exit 3), an exit its
    OUTCOME line contradicts, or a run with no final OUTCOME line (the
    contract's no-line rule) is a tool error. Review-receipt existence is
    deliberately NOT a condition here: the receipt path is not persisted in
    the manifest, and the run-side Phase 5 exec-review receipt check owns
    that condition fail-closed before this boundary (defense in depth)."""
    def refuse(condition: str) -> str:
        return (
            "execute-plan-closeout gate failed: execute-plan session "
            f"{slug}: {condition}; {CLOSEOUT_RESUME_REMEDY}"
        )

    archived_raw = receipt.get("archived_plan_path")
    digest = receipt.get("plan_digest")
    if (
        not isinstance(archived_raw, str)
        or not archived_raw.strip()
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        return (
            1,
            refuse(
                "the terminal receipt is malformed (a non-empty "
                "archived_plan_path and a 64-hex plan_digest are required)"
            ),
        )
    archived_path = Path(archived_raw)
    if not archived_path.is_absolute():
        archived_path = ctx.repo_root / archived_path
    try:
        archived_bytes = archived_path.read_bytes()
    except OSError:
        return (
            1,
            refuse(
                "the terminal receipt's archived plan is unreadable at "
                f"{archived_raw}"
            ),
        )
    computed = hashlib.sha256(archived_bytes).hexdigest()
    if computed != digest:
        return (
            1,
            refuse(
                "terminal receipt digest mismatch: archived plan bytes at "
                f"{archived_raw} re-hash to {computed} but the receipt "
                f"records {digest}"
            ),
        )
    # (b) The active plan path must be gone from the index and the working
    # tree: the archive is a move, never an add-plus-keep (the witnessed
    # copy-plus-delete repair residue).
    archive_gate = payload.get("archive_gate")
    if (
        isinstance(archive_gate, dict)
        and isinstance(archive_gate.get("plan_path"), str)
        and archive_gate["plan_path"].strip()
    ):
        active_display = archive_gate["plan_path"].strip()
        active_path = Path(active_display)
        if not active_path.is_absolute():
            active_path = ctx.repo_root / active_path
    elif _is_relative_to(ctx.plans_dir, ctx.repo_root):
        plans_rel = str(
            ctx.plans_dir.resolve().relative_to(ctx.repo_root.resolve())
        )
        active_display = f"{plans_rel}/{slug}.md"
        active_path = ctx.repo_root / plans_rel / f"{slug}.md"
    else:
        active_path = ctx.plans_dir / f"{slug}.md"
        active_display = str(active_path)
    if active_path.exists():
        return (
            1,
            refuse(
                f"the active plan path {active_display} still survives the "
                "landed-complete run (present in the working tree); the "
                "archive is a move, never an add-plus-keep"
            ),
        )
    active_rel = _repo_relative(str(active_path), ctx.repo_root)
    indexed = ctx.git("ls-files", "--", active_rel)
    if indexed.returncode == 0 and indexed.stdout.strip():
        return (
            1,
            refuse(
                f"the active plan path {active_rel} still survives the "
                "landed-complete run (tracked in the index); the archive is "
                "a move, never an add-plus-keep"
            ),
        )
    # (c) Promoted-origin closure through the origins checker itself (no
    # second origins parser in the lib, per the plan).
    validator = ctx.resolve_script(
        "CHECK_PLAN_ORIGINS_CLOSED_SCRIPT", "check_plan_origins_closed.py"
    )
    if validator is None:
        return (
            1,
            "execute-plan-closeout gate failed: execute-plan session "
            f"{slug}: deployment gap: check_plan_origins_closed.py absent "
            "at every resolved path (env override, repo-local scripts/, "
            "runtime home copy), so the promoted-origin closure could not "
            "be checked; remedy: deploy the script to the runtime home "
            "scripts/ directory and re-run; never use the recorded-stop "
            "exception for a deployment gap",
        )
    proc = ctx.run(
        [sys.executable, str(validator), "--plan", str(archived_path)],
        cwd=ctx.repo_root,
    )
    stragglers = [
        row.strip()
        for row in (proc.stdout or "").splitlines()
        if row.strip().startswith("straggler:")
    ]
    evidence_rows = [
        row.strip()
        for row in (proc.stdout or proc.stderr or "").splitlines()
        if row.strip() and not row.strip().startswith(OUTCOME_LINE_PREFIX)
    ]
    detail = "; ".join(stragglers[:4]) or (
        evidence_rows[-1] if evidence_rows else "origins check failed"
    )

    def origins_indeterminate(condition: str) -> tuple[int, str]:
        return (
            2,
            "execute-plan-closeout gate indeterminate: execute-plan session "
            f"{slug}: {condition}; the promoted-origin closure of the "
            f"archived plan {archived_raw} could not be determined; "
            f"{CLOSEOUT_RESUME_REMEDY}",
        )

    def origins_tool_error(condition: str) -> tuple[int, str]:
        return (
            3,
            "execute-plan-closeout gate tool error: execute-plan session "
            f"{slug}: {condition}; the promoted-origin closure check could "
            f"not run reliably for the archived plan {archived_raw}",
        )

    label = _child_final_outcome(proc)
    if label is None:
        return origins_tool_error(
            "the origins checker emitted no final OUTCOME line (exit "
            f"{proc.returncode}); per the outcome contract's no-line rule "
            f"this is tool error, never a pass; observed: {detail}"
        )
    if label == "fail" and proc.returncode == 1:
        return (
            1,
            refuse(
                "promoted-origin closure failed for the archived plan "
                f"{archived_raw}: {detail}"
            ),
        )
    if label == "pass" and proc.returncode == 0:
        pass  # origins verified; fall through to the registry arm (d)
    elif label == "indeterminate" and proc.returncode == 2:
        return origins_indeterminate(
            f"the origins checker reported indeterminate (exit 2): {detail}"
        )
    elif label == "tool_error" and proc.returncode == 3:
        return origins_tool_error(
            f"the origins checker reported tool error (exit 3): {detail}"
        )
    else:
        return origins_indeterminate(
            f"the origins checker's exit {proc.returncode} contradicts its "
            f"OUTCOME: {label} line; observed: {detail}"
        )
    # (d) The ownership registry names the archived path.
    if not _closeout_registry_names(ctx, archived_raw):
        return (
            1,
            refuse(
                "the ownership registry does not name the archived plan "
                f"{Path(archived_raw).name} (no row of "
                f"{_closeout_registry_path(ctx)} boundary-anchors it)"
            ),
        )
    return None


def gate_execute_plan_closeout(ctx: GateContext) -> GateResult:
    """Pre-commit gate: the execute-plan lifecycle net at the landing
    closeout boundary.

    Discovery is ownership-scoped: the gate derives the session window
    (``derive_session_window``) and the active done-run manifest
    (``load_run_manifest``) the way the doc-registry and foreign-staging
    gates pair them, then scans ``{tmp_dir}/execute-plan/`` for
    ``*/runtime_state.json`` whose ``plan_slug`` matches one of that
    manifest's owned plan claims (an ``owned_plan_paths`` basename minus
    its ``.md`` suffix; a state file whose JSON cannot be parsed counts as
    owned when its session directory is named for an owned claim) and
    whose ``workflow_state`` is not ``aborted``. A missing execute-plan
    home, an unanchorable window, no resolvable run manifest, and a run
    manifest that owns no plans are warning skips naming the reason, never
    silent vacuous passes, and the scan never widens past the owned claims
    when the window does not anchor.

    Arms per owned session manifest, in this order:

    - landed-complete verification (``terminal_receipt`` present):
      ``_closeout_verify_landed_complete``; the first unmet condition fails
      the gate with that condition and the resume remedy, and the promoted-
      origins arm maps the migrated origins checker's outcome contract
      (refuse on its modeled failure, indeterminate and tool error carried
      through as the gate's own outcome, a missing final OUTCOME line as
      tool error).
    - landed-without-evidence refusal (the witnessed shape): no
      ``terminal_receipt`` while every task is done under the runtime's own
      done predicate refuses unconditionally, wherever the plan bytes sit
      (still active, archived twin, or already gone); a run paused between
      the last task and Phase 4 refuses the same way on purpose, because
      the closeout must not report completion before the receipt exists.
    - mid-run false-positive guard: tasks not all done pass with a note;
      the gate never blocks a run that is still executing.

    An unreadable or malformed owned state file fails the gate naming the
    file (fail-closed over subprocess-shaped silent passes). The gate is
    read-only: recovery evidence stays byte-identical.
    """
    gate = "execute-plan-closeout"
    if not ctx.execute_plan_dir.is_dir():
        message = (
            "execute-plan-closeout: warning skip: execute-plan home does "
            f"not exist on disk: {ctx.execute_plan_dir}; no execute-plan "
            "lifecycle evidence was checked"
        )
        return GateResult(gate, 0, message, warnings=[message])
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    if not window.anchored:
        detail = "; ".join(window.notes) or "unanchorable window"
        message = (
            "execute-plan-closeout: warning skip: the session window "
            f"cannot anchor ({detail}); the owned-plan scan never widens "
            "past unowned sessions, so no execute-plan lifecycle evidence "
            "was checked"
        )
        return GateResult(gate, 0, message, warnings=[message])
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    if manifest is None:
        message = (
            "execute-plan-closeout: warning skip: no resolvable active run "
            "manifest (Step 0 record absent, foreign-rooted, or "
            "schema-invalid); no owned plan claims to scope the scan with"
        )
        return GateResult(gate, 0, message, warnings=[message])
    claimed = _closeout_owned_plan_slugs(manifest)
    if not claimed:
        message = (
            "execute-plan-closeout: warning skip: the active run manifest "
            f"({manifest.run_id}) owns no plan claims (owned_plan_paths "
            "empty); no execute-plan session is in scope"
        )
        return GateResult(gate, 0, message, warnings=[message])

    passes: list[str] = []
    unowned: list[str] = []
    for state_path in _closeout_session_states(ctx):
        slug_dir = state_path.parent.name
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            if slug_dir in claimed:
                return GateResult(
                    gate,
                    1,
                    "execute-plan-closeout gate failed: owned execute-plan "
                    "session manifest is unreadable or malformed: "
                    f"{state_path} (unparseable: {exc})",
                    warnings=[],
                )
            unowned.append(slug_dir)
            continue
        if not isinstance(payload, dict):
            if slug_dir in claimed:
                return GateResult(
                    gate,
                    1,
                    "execute-plan-closeout gate failed: owned execute-plan "
                    "session manifest is unreadable or malformed: "
                    f"{state_path} (the payload is not a JSON object)",
                    warnings=[],
                )
            unowned.append(slug_dir)
            continue
        payload_slug = payload.get("plan_slug")
        owned = (
            payload_slug in claimed
            if isinstance(payload_slug, str)
            else slug_dir in claimed
        )
        if not owned:
            unowned.append(slug_dir)
            continue
        if payload.get("workflow_state") == "aborted":
            passes.append(f"{slug_dir} aborted; out of scope")
            continue
        slug = payload_slug if isinstance(payload_slug, str) else slug_dir
        if not isinstance(payload.get("tasks"), dict):
            return GateResult(
                gate,
                1,
                "execute-plan-closeout gate failed: owned execute-plan "
                "session manifest is unreadable or malformed: "
                f"{state_path} (the tasks record is not a JSON object)",
                warnings=[],
            )
        receipt = payload.get("terminal_receipt")
        if isinstance(receipt, dict):
            finding = _closeout_verify_landed_complete(
                ctx, slug, payload, receipt
            )
            if finding is not None:
                finding_rc, finding_message = finding
                return GateResult(gate, finding_rc, finding_message, warnings=[])
            passes.append(
                f"{slug} landed complete; receipt digest, active-path "
                "absence, promoted-origin closure, and registry row "
                "verified"
            )
        elif _closeout_all_tasks_done(payload):
            return GateResult(
                gate,
                1,
                "execute-plan-closeout gate failed: execute-plan session "
                f"{slug} ({state_path}) landed without terminal evidence: "
                "every task is done under the runtime done predicate but "
                "the manifest carries no terminal_receipt (workflow_state "
                f"{payload.get('workflow_state')!r}); "
                + CLOSEOUT_RESUME_REMEDY,
                warnings=[],
            )
        else:
            passes.append(
                f"{slug} still mid-run (tasks not all done under the "
                "runtime done predicate); the gate never blocks an "
                "executing run"
            )
    message = "execute-plan-closeout gate passed"
    if passes:
        message += ": " + "; ".join(passes)
    else:
        message += ": no owned execute-plan session manifest in scope"
    if unowned:
        message += (
            "; unowned session manifest(s) skipped (plan slug matches no "
            "owned plan claim): " + ", ".join(sorted(set(unowned)))
        )
    return GateResult(gate, 0, message, warnings=[])


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
    "description-length": gate_description_length,
    "foreign-staging": gate_foreign_staging,
    "post-landing-staging": gate_post_landing_staging,
    "archive-ceremony": gate_archive_ceremony,
    "execute-plan-closeout": gate_execute_plan_closeout,
    "plans-archive-twin": gate_plans_archive_twin,
}


def run_gate(gate_id: str, ctx: GateContext) -> GateResult:
    if gate_id not in GATES:
        raise ValueError(f"unknown gate id: {gate_id}")
    return GATES[gate_id](ctx)


def run_phase(phase: str, ctx: GateContext) -> list[GateResult]:
    """Run one phase's gates strictly sequentially in registry order (see the
    module docstring's execution contract). A gate helper that raises is
    captured as an indeterminate gate result naming the failed gate (outcome
    contract exit 2: the gate could not answer, so its evidence is neither a
    pass nor a modeled violation); the run continues so every gate still
    reports."""
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase}")
    results: list[GateResult] = []
    for gate_id in PHASES[phase]:
        try:
            results.append(run_gate(gate_id, ctx))
        except Exception as exc:
            results.append(
                GateResult(
                    gate_id,
                    2,
                    f"gate helper raised {type(exc).__name__}: {exc}; the "
                    "gate could not complete its check, so its result is "
                    "indeterminate",
                    warnings=[],
                )
            )
    return results


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
    """The run's contract exit: the dominant gate outcome, where tool error
    (3) dominates the run, indeterminate (2) dominates fail (1) (the
    contract's multi-input rule), and a clean run is 0."""
    return max((result.rc for result in results), default=0)


def _usage() -> str:
    return (
        "usage: done_sweep_gates.sh "
        "<pre-docs|pre-commit|list-gates|write-manifest|finalize-manifest|"
        "disposition-manifest|list-interrupted-manifests>\n"
        "phases: pre-docs (done Steps 1.5..2.62 gates), pre-commit (done "
        "Steps 2.7/2.76/2.8 mechanical gates)\n"
        "list-gates prints the absorbed gate ids in phase order, "
        "deduped at first phase (the twin runs in both phases)\n"
        "write-manifest writes the done Step 0 run manifest record "
        "(run-manifest-<run_id>.json under the done-session directory), "
        "reporting interrupted runs (complete=false, never finalized; "
        "continued only via an explicit --adopt boundary copy); "
        "--emit-foreign-candidates <file> writes the staging candidates "
        "this run does not own one per line, sorted, for the first-finalize "
        "bulk load and exits 0 without writing a manifest\n"
        "finalize-manifest sets a run manifest's complete flag to true in "
        "place (done Step 6; --run-id required; an absent manifest file is "
        "a named not-found note with a zero exit, while a present manifest "
        "carrying a wrong schema version or another repository's repo_root "
        "is a named non-zero abort that leaves the record unchanged)\n"
        "disposition-manifest stamps the one-time dispositioned record "
        "(work-verified-landed) onto an unadoptable interrupted run manifest "
        "(--run-id required, --note optional; a live root or an adopted "
        "boundary refuses; the deliverables witness refuses naming the "
        "first missing owned deliverable; an already-dispositioned manifest "
        "reprints its record with a zero exit)\n"
        "list-interrupted-manifests prints one line per interrupted run "
        "manifest (root=<live|dead>, dispositioned, adopted, created); "
        "read-only, never mutates\n"
        "phase runs report the outcome contract "
        "(scripts/OUTCOME_CONTRACT.md): exit 0 pass, 1 fail, 2 "
        "indeterminate, 3 tool error, ending stdout with exactly one final "
        "`OUTCOME:` line; a raising gate helper is an indeterminate gate "
        "result, and a usage error is tool error while --help and "
        "list-gates are metadata exits with no OUTCOME line"
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
    orphan report for later runs. The report doubles as a refusal: when an
    orphan remains that this invocation neither adopted nor recognized as
    closed, the write aborts with ``write-manifest: undisposed-interrupted:``
    listing each remaining manifest filename with the remedies its root state
    supports (a live root: ``--adopt`` or ``finalize-manifest``; a dead root:
    ``disposition-manifest`` only), so an interrupted boundary is classified
    before any new manifest (the emit-only arm included).

    First-finalize bulk load: ``--emit-foreign-candidates <file>`` runs the
    same staging-candidate enumeration as the claim-or-foreign gate,
    subtracts the invocation's owned review claims (plus the adopted run's
    inherited owned claims), writes the remaining candidate paths one per
    line in sorted order to the file, and exits 0 without writing a
    manifest, so the operator reviews the list and re-runs the real write
    with ``--foreign-review-from``; a candidate path that cannot round-trip
    through a one-per-line file (a newline, or leading/trailing whitespace,
    including a trailing space before the ``.md`` extension the staging
    predicate requires) aborts the emission with a named error before
    anything is written.
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
        "--emit-foreign-candidates", default=None, metavar="FILE",
        help="write the staging candidates this run does not own, one "
        "repo-relative path per line in sorted order, to FILE and exit 0 "
        "without writing a manifest (first-finalize bulk load: review the "
        "list, then re-run the real write with --foreign-review-from FILE)",
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
    orphans = _detect_interrupted_runs(
        ctx.done_session_dir, ctx.repo_root, warnings=corrupt_warnings
    )
    for orphan in orphans:
        if adopted is not None and orphan.run_id == adopted.run_id:
            print(
                "interrupted run: adopting the boundary of "
                f"{orphan.run_id} (start_commit and owned paths carried "
                "verbatim from its manifest)"
            )
            continue
        if not _manifest_root_matches(orphan.repo_root, ctx.repo_root):
            # Dead-root orphan (the widened detection surfaces the class):
            # adoption refuses a dead root, so the line names the disposition
            # path instead of the adoption advice.
            print(
                "interrupted run: "
                f"{_manifest_path(ctx.done_session_dir, orphan.run_id).name} "
                "(complete=false, never finalized; the recorded repo_root "
                "matches no checkout here, so adoption refuses this "
                "boundary); close it once with disposition-manifest --run-id "
                f"{orphan.run_id} (the done skill's Manifest disposition "
                "(dead-boundary close) paragraph is the procedure of record)"
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

    # Undisposed-interrupted refusal (plan 2026-10-01-done-boundary-receipt-
    # and-closeout-gate-sweep Task 3): the report above stays advisory; the
    # refusal adds the bounded decision, it does not replace the report. A
    # complete:false manifest under this checkout's done-session directory is
    # a past interrupted run of THIS checkout, never a live sibling writing
    # concurrently: the done lock is exclusive per checkout, which is why no
    # liveness probe is needed before demanding the classification. An
    # orphan this invocation neither adopted nor recognized as closed
    # (dispositioned records never reach the orphan set) refuses the write,
    # and the refusal sits before the emit-foreign-candidates arm on
    # purpose: an emit-only invocation also requires the classification
    # first, deliberately.
    remaining = [
        orphan
        for orphan in orphans
        if adopted is None or orphan.run_id != adopted.run_id
    ]
    if remaining:
        entries: list[str] = []
        for orphan in remaining:
            filename = _manifest_path(ctx.done_session_dir, orphan.run_id).name
            if not _manifest_root_matches(orphan.repo_root, ctx.repo_root):
                entries.append(
                    f"{filename}: disposition-manifest --run-id "
                    f"{orphan.run_id} only (the recorded repo_root matches "
                    "no checkout here, so adoption refuses this boundary)"
                )
            else:
                entries.append(
                    f"{filename}: --adopt {orphan.run_id} to continue it, "
                    f"or finalize-manifest --run-id {orphan.run_id} to "
                    "close it (disposition-manifest refuses live roots)"
                )
        return _cli_fail(
            "write-manifest: undisposed-interrupted: " + "; ".join(entries)
        )

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

    # First-finalize bulk load (the F13 companion affordance): emit the
    # staging candidates this run does not own, one repo-relative path per
    # line in sorted order, then exit 0 WITHOUT writing a manifest, so the
    # operator reviews the list and re-runs the real write with
    # --foreign-review-from. This runs before the claim-or-foreign gate on
    # purpose: the emission is the answer to the very violation that gate
    # raises on a first finalize, so the emit invocation must reach it.
    if args.emit_foreign_candidates:
        remaining = [
            _repo_relative(str(candidate), ctx.repo_root)
            for candidate in _all_staging_review_paths(ctx)
            if os.path.realpath(str(candidate)) not in owned_real
        ]
        # The --foreign-review-from loader strips each line and splits on
        # newlines, so a candidate path carrying a newline or CR, leading or
        # trailing whitespace, or a vertical tab / form feed immediately
        # before the final ".md" extension (the two whitespace kinds
        # splitlines also breaks lines on and strip() cannot restore) cannot
        # round-trip through the emitted file; space or tab immediately
        # before the extension is internal whitespace and round-trips
        # untouched. Abort named before anything is written.
        unroundtrippable = [
            path
            for path in remaining
            if "\n" in path
            or "\r" in path
            or path != path.strip()
            or re.search(r"[\v\f]\.md$", path)
        ]
        if unroundtrippable:
            return _cli_fail(
                "write-manifest: foreign-candidate-roundtrip: staging review "
                "candidate path(s) cannot be emitted one per line (a newline "
                "or leading/trailing whitespace cannot round-trip through "
                "--foreign-review-from): "
                + ", ".join(
                    # Control characters are stripped so a hostile filename
                    # cannot forge extra stderr lines (same rendering class
                    # as the finalize mismatch error).
                    f"<{_sanitize_manifest_error_value(path)}>"
                    for path in unroundtrippable
                )
            )
        try:
            Path(args.emit_foreign_candidates).write_text(
                "".join(f"{path}\n" for path in sorted(remaining)),
                encoding="utf-8",
            )
        except OSError as exc:
            return _cli_fail(
                "write-manifest: cannot write --emit-foreign-candidates file "
                f"{args.emit_foreign_candidates}: {exc}"
            )
        print(
            f"foreign-candidates: {args.emit_foreign_candidates} "
            f"({len(remaining)} path(s), sorted); no manifest written; "
            "review the list, then re-run the real write with "
            "--foreign-review-from"
        )
        return 0

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
    is never an interrupted run for a later Step 0. Two-way identity
    contract: an absent manifest file keeps the explicit not-found note with
    a zero exit (the Step 6 recipe's tolerance clause; a run without a
    manifest skips finalization without failing), while a present manifest
    that fails the pre-parse identity check - a wrong ``schema`` version, or
    a ``repo_root`` matching neither arm of the root matcher - is a named
    non-zero abort and the file is left byte-identical. The tolerant
    from_dict read and its silent None degradation stay below this check for
    the frozen non-finalize consumers (interrupted-run detection, adopt);
    they never see this path's named abort."""
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

    def not_found() -> int:
        print(
            "finalize-manifest: no run manifest found for run_id "
            f"{args.run_id} under {ctx.done_session_dir} (nothing to "
            "finalize; a run without a manifest skips finalization)"
        )
        return 0

    if not args.run_id or Path(args.run_id).name != args.run_id or not _manifest_path(
        ctx.done_session_dir, args.run_id
    ).is_file():
        return not_found()
    # Identity contract pre-parse over the raw payload, BEFORE the tolerant
    # read: a present manifest from another repository or at a wrong schema
    # version aborts named and non-zero, writing nothing.
    try:
        payload = json.loads(
            _manifest_path(ctx.done_session_dir, args.run_id).read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValueError):
        payload = None
    mismatch = _finalize_identity_mismatch(payload, ctx.repo_root)
    if mismatch is not None:
        schema_render, root_state = mismatch
        return _cli_fail(
            "run-manifest identity mismatch: manifest schema_version "
            f"{schema_render} repo_root {root_state} is not supported by "
            "this finalizer (expected schema_version 1 and a 64-hex "
            "fingerprint root matching this repository); manifest left "
            "unchanged"
        )
    manifest = _read_manifest_by_run_id(ctx.done_session_dir, args.run_id)
    if manifest is None or not _manifest_root_matches(
        manifest.repo_root, ctx.repo_root
    ):
        return not_found()
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


def _disposition_repo_rel_dir(directory: Path, repo_root: Path) -> str:
    """Repo-relative form of one of the ctx directories (an absolute resolved
    path relative to the repo root when containment holds, else the verbatim
    string), for prefix-matching recorded entry paths against a plans tree."""
    try:
        return str(
            directory.resolve().relative_to(Path(repo_root).resolve())
        )
    except (OSError, ValueError):
        return _repo_relative(str(directory), repo_root)


def _disposition_first_missing_deliverable(
    manifest: RunManifest, ctx: GateContext, note: Optional[str] = None
) -> Optional[str]:
    """The disposition operation's deliverables witness, resolved set by set:
    an ``owned_plan_paths`` entry passes at its recorded path in the current
    checkout, at its ``plans_completed`` archive twin at HEAD, or note-backed
    (the operator's note names the path, recording its home checkout and
    verifying commit); an ``owned_review_paths`` entry passes against the
    docs branch (``git cat-file -e docs:<path>``; review staging docs are
    gitignored on the default branch); an ``owned_paths`` entry passes at
    ``HEAD:<path>``, at its ``plans_completed`` archive twin at HEAD when the
    recorded path sits under ``plans_dir``/``plans_completed_dir``
    (repo-relative prefix; schema-1 manifests that recorded plan edits under
    ``owned_paths``), through its landed deletion (a commit reachable from
    HEAD that deleted the path: exit 0 AND non-empty %H output, since a
    never-tracked path exits 0 with empty output), or note-backed.
    Returns None when every owned deliverable resolves, else a one-line
    message naming the first missing one."""
    for plan_path in manifest.owned_plan_paths:
        on_disk = (ctx.repo_root / plan_path).is_file()
        at_head = ctx.git("cat-file", "-e", f"HEAD:{plan_path}").returncode == 0
        if on_disk or at_head:
            continue
        twin = ctx.plans_completed_dir / Path(plan_path).name
        twin_rel = _repo_relative(str(twin), ctx.repo_root)
        if ctx.git("cat-file", "-e", f"HEAD:{twin_rel}").returncode == 0:
            continue
        if note and plan_path in note:
            continue
        return (
            f"owned_plan_paths entry {plan_path} resolves neither at its "
            "recorded path nor at its plans_completed archive twin at HEAD"
        )
    for review_path in manifest.owned_review_paths:
        if ctx.git("cat-file", "-e", f"docs:{review_path}").returncode == 0:
            continue
        return (
            f"owned_review_paths entry {review_path} does not resolve on the "
            "docs branch"
        )
    for owned_path in manifest.owned_paths:
        if ctx.git("cat-file", "-e", f"HEAD:{owned_path}").returncode == 0:
            continue
        plans_rel = _disposition_repo_rel_dir(ctx.plans_dir, ctx.repo_root)
        completed_rel = _disposition_repo_rel_dir(
            ctx.plans_completed_dir, ctx.repo_root
        )
        under_plans_tree = owned_path == plans_rel or owned_path.startswith(
            plans_rel + "/"
        )
        under_completed_tree = (
            owned_path == completed_rel or owned_path.startswith(completed_rel + "/")
        )
        if under_plans_tree or under_completed_tree:
            twin = ctx.plans_completed_dir / Path(owned_path).name
            twin_rel = _repo_relative(str(twin), ctx.repo_root)
            if ctx.git("cat-file", "-e", f"HEAD:{twin_rel}").returncode == 0:
                continue
        # Landed-deletion arm: a commit reachable from HEAD that deleted the
        # path landed through the repo's own gates. A never-tracked path
        # exits 0 with EMPTY %H output, so resolve only when BOTH the exit
        # is 0 and the commit hash is non-empty.
        deletion = ctx.git(
            "log", "--diff-filter=D", "--format=%H", "-n", "1", "--", owned_path
        )
        if deletion.returncode == 0 and deletion.stdout.strip():
            continue
        if note and owned_path in note:
            continue
        return f"owned_paths entry {owned_path} does not resolve at HEAD"
    return None


def _manifest_adopted_by_another(done_session_dir: Path, run_id: str) -> bool:
    """True when any run manifest in the directory carries an ``adopted_from``
    link naming ``run_id`` (the boundary was continued by another run; the
    scan is over the raw payloads, so an adopter is never missed by a root or
    schema filter)."""
    if not done_session_dir.is_dir():
        return False
    for path in sorted(done_session_dir.glob("run-manifest-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        link = payload.get("adopted_from")
        if isinstance(link, str) and link == run_id:
            return True
    return False


def _cmd_disposition_manifest(argv: list[str]) -> int:
    """Stamp the one-time ``dispositioned`` record onto an unadoptable
    interrupted run manifest (an interrupted run whose recorded ``repo_root``
    names a checkout that no longer exists, so the adoption boundary and the
    finalize identity check refuse it forever). Refusals, each a named
    one-line error with no mutation: an absent manifest; ``complete`` already
    true; an ``adopted_from`` link naming the run (another manifest adopted
    this boundary); a recorded root matching the current repository through
    either arm of ``_repo_root_matches_value`` (a live root is
    adoption/resume territory; the refusal names the resume path). A
    ``dispositioned`` record already present is the idempotent arm: the
    existing record is printed and the exit is 0, never a refusal, so a
    re-run after the deliverable vanished cannot un-close the run. On
    success the deliverables witness resolves every owned deliverable by set
    (naming the first missing one on refusal; three empty owned sets print
    and stamp a named no-deliverables note - the witness is vacuously true).
    Immediately before the write a stamp CAS re-checks with two fresh reads:
    (a) this manifest's payload re-read from disk through the reader's parse
    contract (``_read_manifest_by_run_id``), refusing fail-closed when the
    re-read returns None (absent, unreadable, or schema-mismatched; post-check
    state loss), refusing when
    ``complete`` is now true (post-check finalize), and degrading to the
    idempotent reprint of the racer's record when a ``dispositioned`` record
    landed after the pre-checks (other field drift does not block the
    stamp); (b) a fresh ``_manifest_adopted_by_another`` directory re-scan,
    refusing on post-check adoption (adoption writes ``adopted_from`` on the
    ADOPTER's manifest, invisible to a payload-only re-read). Only then is
    ``dispositioned: {reason: "work-verified-landed", date, note}`` stamped
    through the writer's atomic manifest-update path."""
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py disposition-manifest",
        description=(
            "Stamp the one-time disposition record onto an unadoptable "
            "interrupted run manifest."
        ),
    )
    parser.add_argument(
        "--run-id", required=True, metavar="RUN_ID",
        help="the run_id recorded when Step 0 wrote the manifest",
    )
    parser.add_argument(
        "--note", default=None, metavar="TEXT",
        help="optional closure note recorded inside the dispositioned record",
    )
    args = parser.parse_args(argv)

    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    ctx = GateContext.discover(Path(root) if root else None)

    if not args.run_id or Path(args.run_id).name != args.run_id:
        return _cli_fail(
            f"disposition-manifest: refusing {args.run_id!r}: not a bare "
            "run_id filename"
        )
    # The root-agnostic reader (the root-filtered loader would refuse the
    # dead-root record this operation exists to close).
    manifest = _read_manifest_by_run_id(ctx.done_session_dir, args.run_id)
    if manifest is None:
        return _cli_fail(
            "disposition-manifest: no run manifest found for run_id "
            f"{args.run_id} under {ctx.done_session_dir}"
        )
    if manifest.dispositioned is not None:
        # Idempotent re-run: print the existing record, exit 0, never refuse.
        record = manifest.dispositioned
        date = record.get("date") if isinstance(record.get("date"), str) else ""
        print(f"dispositioned: {manifest.run_id} ({date}) (already dispositioned)")
        print(json.dumps(record, sort_keys=True))
        return 0
    if manifest.complete:
        return _cli_fail(
            f"disposition-manifest: refusing {manifest.run_id}: the run "
            "already finalized (complete=true); a finalized run is never an "
            "interrupted run"
        )
    if _manifest_adopted_by_another(ctx.done_session_dir, manifest.run_id):
        return _cli_fail(
            f"disposition-manifest: refusing {manifest.run_id}: another "
            "manifest adopts this boundary (an adopted_from link names it); "
            "adoption owns the continuation"
        )
    if _repo_root_matches_value(manifest.repo_root, ctx.repo_root):
        return _cli_fail(
            f"disposition-manifest: refusing {manifest.run_id}: the recorded "
            "repo_root matches this repository (a live root); resume the run "
            "in its checkout and close it through the adoption boundary "
            f"(write-manifest --adopt {manifest.run_id}) or with "
            f"finalize-manifest --run-id {manifest.run_id}, never disposition"
        )
    date_str = datetime.now(timezone.utc).date().isoformat()
    if (
        not manifest.owned_plan_paths
        and not manifest.owned_review_paths
        and not manifest.owned_paths
    ):
        note = (
            "no-deliverables: the manifest owns no deliverables "
            "(owned_plan_paths, owned_review_paths, owned_paths all empty); "
            "the deliverables witness is vacuously true"
        )
        if args.note:
            note = f"{note}; operator note: {args.note}"
        print(f"disposition-manifest: {note}")
    else:
        missing = _disposition_first_missing_deliverable(
            manifest, ctx, note=args.note
        )
        if missing is not None:
            return _cli_fail(
                f"disposition-manifest: refusing {manifest.run_id}: "
                f"deliverables witness failed: {missing}"
            )
        note = args.note or ""
    manifest.dispositioned = {
        "reason": "work-verified-landed",
        "date": date_str,
        "note": note,
    }
    # Stamp CAS: two fresh reads close the check-then-write window so a
    # finalize, a competing disposition, or an adoption landing between the
    # pre-checks and the stamp cannot blur the record. (a) This manifest's
    # payload re-read fresh from disk through the reader's parse contract
    # (the same helper the initial read used), so absent, unreadable, and
    # schema-mismatched fresh payloads all refuse identically to
    # _read_manifest_by_run_id's semantics. A None return conflates those
    # three shapes (an accepted narrowing: each refuses fail-closed here)
    # and never covers a complete-but-valid manifest, which the helper
    # parses through to the dataclass, so the post-check finalize shape
    # stays reachable. Any other field drift between the two reads does
    # not block the stamp.
    fresh = _read_manifest_by_run_id(ctx.done_session_dir, manifest.run_id)
    if fresh is None:
        return _cli_fail(
            f"disposition-manifest: refusing {manifest.run_id}: the manifest "
            "payload is absent, unreadable, or schema-mismatched at the "
            "stamp (post-check state loss); refusing to stamp over an "
            "unknown state"
        )
    if fresh.complete:
        return _cli_fail(
            f"disposition-manifest: refusing {manifest.run_id}: the run "
            "finalized between the pre-checks and the stamp (post-check "
            "finalize); a finalized run is never an interrupted run"
        )
    racer = fresh.dispositioned
    if racer is not None:
        # A concurrent disposition won the race: print the EXISTING record
        # (the racer's date/note, not this call's) and exit 0, the same
        # idempotent path as a pre-existing stamp.
        racer_date = (
            racer.get("date") if isinstance(racer.get("date"), str) else ""
        )
        print(
            "disposition-manifest: a dispositioned record landed after the "
            "pre-checks (a concurrent disposition won the race); printing "
            "the existing record"
        )
        print(
            f"dispositioned: {manifest.run_id} ({racer_date}) "
            "(already dispositioned)"
        )
        print(json.dumps(racer, sort_keys=True))
        return 0
    # (b) A fresh directory re-scan: adoption writes adopted_from on the
    # ADOPTER's manifest, invisible to a payload-only re-read.
    if _manifest_adopted_by_another(ctx.done_session_dir, manifest.run_id):
        return _cli_fail(
            f"disposition-manifest: refusing {manifest.run_id}: another "
            "manifest adopted this boundary between the pre-checks and the "
            "stamp (post-check adoption); adoption owns the continuation"
        )
    try:
        path = write_run_manifest(manifest, ctx.done_session_dir)
    except OSError as exc:
        return _cli_fail(
            f"disposition-manifest: cannot rewrite the run manifest: {exc}"
        )
    print(f"dispositioned: {manifest.run_id} ({date_str}) written to {path}")
    return 0


def _cmd_list_interrupted_manifests(argv: list[str]) -> int:
    """Print one line per detected interrupted manifest (read-only, never
    mutates): ``<run_id> root=<live|dead> dispositioned=<yes|no>
    adopted=<yes|no> created=<iso date>``. The enumeration walks every
    ``run-manifest-*.json`` payload itself - never the root-filtered
    ``load_run_manifest`` and never ``_detect_interrupted_runs``, whose
    suppression shapes (dispositioned records) must stay visible as columns
    here. The keep-filter holds ``complete`` false and nothing adopting the
    record (no other manifest's ``adopted_from`` link names it); the
    ``adopted`` column reports the record's own ``adopted_from`` link, so an
    adopted boundary stays distinguishable in the output; root liveness goes
    through both arms of ``_repo_root_matches_value`` (a 64-hex digest
    compares against the current digest, any other value by realpath). An
    empty set prints ``no interrupted manifests`` and exits 0."""
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py list-interrupted-manifests",
        description=(
            "List the interrupted run manifests classified by root liveness "
            "(read-only)."
        ),
    )
    parser.parse_args(argv)

    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    ctx = GateContext.discover(Path(root) if root else None)
    parsed: list[RunManifest] = []
    if ctx.done_session_dir.is_dir():
        for path in sorted(ctx.done_session_dir.glob("run-manifest-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            manifest = RunManifest.from_dict(payload)
            if manifest is None:
                continue
            parsed.append(manifest)
    adopted_ids = {m.adopted_from for m in parsed if m.adopted_from}
    lines: list[str] = []
    for manifest in parsed:
        if manifest.complete or manifest.run_id in adopted_ids:
            continue
        root_state = (
            "live"
            if _repo_root_matches_value(manifest.repo_root, ctx.repo_root)
            else "dead"
        )
        created = datetime.fromtimestamp(
            manifest.created_epoch, tz=timezone.utc
        ).date().isoformat()
        lines.append(
            f"{manifest.run_id} root={root_state} "
            f"dispositioned={'yes' if manifest.dispositioned else 'no'} "
            f"adopted={'yes' if manifest.adopted_from else 'no'} "
            f"created={created}"
        )
    if not lines:
        print("no interrupted manifests")
        return 0
    for line in lines:
        print(line)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        # --help is a metadata exit (no OUTCOME line); a bare invocation is
        # a usage error, which the outcome contract classifies tool error.
        print(_usage(), file=sys.stderr)
        if args:
            return 0
        print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
        return 3
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
    if command == "disposition-manifest":
        return _cmd_disposition_manifest(args[1:])
    if command == "list-interrupted-manifests":
        return _cmd_list_interrupted_manifests(args[1:])
    if command in PHASES:
        root = os.environ.get("DONE_SWEEP_REPO_ROOT")
        ctx = GateContext.discover(Path(root) if root else None)
        results = run_phase(command, ctx)
        print(render_report(results))
        code = phase_exit(results)
        print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS.get(code, 'indeterminate')}")
        return code
    print(_usage(), file=sys.stderr)
    print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
