#!/usr/bin/env python3
"""Done sweep gate runner lib: the done skill's deterministic gates as code.

Plan: ``docs/history/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md``,
Task 1. Invoked by ``scripts/done_sweep_gates.sh`` (one call per phase) and
exercised hermetically by ``scripts/test_done_sweep_gates_lib.py``.

Gate phases (the closeout's one sweep run after the done target-state flip;
judgment steps around it stay in the skill):

- ``landing``    (the closeout's one landing sweep run):
  plan-readiness, confluence-hygiene, doc-registry, review-staging,
  docs-tmp-sweep, plans-archive-twin (deduped to one run slot),
  sensitive-data-scan, em-dash-scan, instruction-size (warning posture),
  description-length (warning posture), foreign-staging,
  post-landing-staging, plans-root-claim-fence, archive-ceremony,
  execute-plan-closeout. backlog-inbox and vim-swap-sweep are not on the
  roster (receiving-review capture step and the periodic survey advisory own
  their duties; see docs/maintenance/demoted-sweep-arms.md).

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

Stdlib only plus the repo-local ``facts_paths``, ``plan_shape`` (the
shared plan-shape resolver; the archive-ceremony twin's directory-grammar
constants are imported, never re-derived), ``validate_review_staging``
(the staging-path predicate is imported, never re-implemented), and
``review_record_selection`` (the preservation-backup grammar constant
``BACKUP_INFIX`` is imported, never redefined).

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
owned deliverables verify as landed; ``--manifest-file`` closes a worktree
shadow copy through its own file (the stamp binds to that copy, the
canonical record untouched). ``list-interrupted-manifests`` prints
the interrupted manifests with their repository identity column and lock
column, read-only, binding shadow copies to their runs as ``shadow-of``
lines and rendering a run closed through another file as closed-run
history. The
``recover-manifest`` sub-command is the live-root sibling: for an
interrupted manifest whose recorded root matches this repository it
verifies the owned deliverables and the owned-commits ledger's reachability
BEFORE any write, then stamps the same ``dispositioned`` record with reason
``work-verified-landed-live-recovery`` (a dead root refuses, naming the
dead-root command).
The ``classify-run-boundary`` sub-command is the read-only canonical boundary
classifier behind the done setup shell classifier: it prints the verdict and
run id for one manifest file read at run identity (terminal
``finalized``/``adopted``/``dispositioned``, ``shadow-closed``, ``orphan``,
``unreadable``).
The ``checkpoint-manifest`` sub-command owns the done skill's
resumable-closeout checkpoint, the sibling JSON
``run-checkpoint-<run_id>.json`` beside the manifest: ``create`` writes it
when the run enters the finalizer span, ``refresh`` updates the recorded
manifest sha256 and green-gate set in place at the Step 6 finalize preamble,
``verify`` re-checks the recorded identity (run_id, manifest path, session)
and the recomputed manifest sha256 (the mechanical gate the resume
continuation reads), and ``remove`` deletes the sibling only after a
successful finalize set the manifest's ``complete`` flag true. Every refusal
is a named one-line non-zero error that mutates nothing; the checkpoint
filename derives from the run_id, so one run's orphaned checkpoint cannot
collide with a later run's create.
"""

from __future__ import annotations

import argparse
import json
import hashlib
import hmac
import os
import posixpath
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
import plan_shape
import plan_readiness
import validate_review_staging as vrs
from review_record_selection import BACKUP_INFIX, ORPHAN_INFIX

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

# Registry: the landing phase, the closeout's one sweep run (the retained
# roster from the done target-state classification, the plan's Outcome
# table). plan-readiness, instruction-size and description-length ride in
# warning posture: they report, never block (no ledger catches; the demotion
# program's landing-dated rows own the evidence). backlog-inbox and vim-swap-sweep
# left the per-run roster entirely: the filing duty stays with
# receiving-review's capture step, the sweep became a periodic survey
# advisory (docs/maintenance/demoted-sweep-arms.md).
LANDING_GATES = [
    "plan-readiness",
    "confluence-hygiene",
    "doc-registry",
    "review-staging",
    "docs-tmp-sweep",
    "plans-archive-twin",
    "sensitive-data-scan",
    "em-dash-scan",
    "instruction-size",
    "description-length",
    "foreign-staging",
    "post-landing-staging",
    "plans-root-claim-fence",
    "archive-ceremony",
    "execute-plan-closeout",
]
LANDING_WARNING_GATES = frozenset(
    {"plan-readiness", "instruction-size", "description-length"}
)

# The per-task boundary roster: LANDING_GATES minus post-landing-staging
# alone (plan: worktree-done-boundary-gate-roster-split, Task 1). Subtraction
# basis: gate_post_landing_staging is the only landing-roster gate whose
# check reads the primary checkout (verified at authoring 2026-10-17 against
# the gate helpers below), so a per-task done boundary inside a live run
# worktree runs exactly this list while the final closeout keeps the full
# LANDING_GATES set. Machinery admission for the narrowed
# gate_post_landing_staging reach: incident, the 2026-10-16 witnessed
# per-task stall (docs/history/plans/completed/2026-10-16-worktree-done-boundary-gate-roster-split.md);
# catch frequency unchanged at the final closeout, where the gate still runs;
# false-positive cost, a per-task boundary forfeits early warning of primary
# residue; sunset, review at first misuse or beside the placement-awareness
# lineage. A gate whose check later grows repo-keyed reach re-enters the
# final-closeout-only class by removal from this list.
PER_TASK_LANDING_GATES = [
    gate for gate in LANDING_GATES if gate != "post-landing-staging"
]

BOUNDARY_CLASSES = ("per-task", "final-closeout")

PHASES = {
    "landing": LANDING_GATES,
}

# The landing sweep's sensitive-data-scan gate item 2
# diff-content grep patterns. Credential terms are
# intentionally assignment-shaped so domain prose such as "claim token" does
# not become a false positive while credential-like values remain blocked.
#
# Profile exemption (2026-10-12 operator direction, recorded in
# docs/history/backlog/2026-10-12-done-private-repository-visibility-scan.md):
# the exemption skips both content arms for company and private-pet profiles:
# when the repo facts record project_type = "company", or project_type =
# "pet" with artifact_visibility = "private", neither the credential family
# nor the public-artifact family is matched over staged or untracked
# content. The exemption is declaration-trusted: the untracked working-tree
# facts are read fresh per gate run, so the profile is flippable within the
# same landing and a well-formed but false declaration is honored. Every
# non-exempt profile (public pets; absent, malformed, or unrecognized
# project types) keeps the strict scan with both families.
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
            plans_dir=_resolve_dir(root, "plans_dir"),
            plans_completed_dir=_resolve_dir_or(
                root, "plans_completed_dir", "docs/history/plans/completed"
            ),
            backlog_dir=_resolve_dir(root, "backlog_dir"),
            reviews_dir=_resolve_dir(root, "reviews_dir"),
            tmp_dir=_resolve_dir(root, "tmp_dir"),
            runtime_home=runtime_home,
            user_facts=user_facts,
        )

    @property
    def project_type(self) -> Optional[str]:
        """Confirmed project profile from the repo facts TOML; "pet" or
        "company" only on an exact case-insensitive match, anything else
        (absent, malformed, other values) reads as None (fail-safe
        strictness)."""
        raw = facts_paths.resolve_toml_key_raw(self.repo_root, "project_type")
        if isinstance(raw, str):
            value = raw.strip().lower()
            if value in ("pet", "company"):
                return value
        return None

    @property
    def artifact_visibility(self) -> str:
        """Declared repository audience from the repo facts TOML; "private"
        only on an exact case-insensitive match, anything else (absent,
        malformed, other values) reads as "public" (fail-safe strictness).
        The sensitive-data gate honors it only for pet projects (see
        project_type)."""
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

    def git_bytes(self, *args: str):
        """Run git without decoding blob output, preserving exact bytes."""
        return subprocess.run(
            ["git", "-c", "core.quotePath=false", *args],
            cwd=str(self.repo_root),
            capture_output=True,
            text=False,
            timeout=GIT_TIMEOUT_S,
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


def _resolve_dir(root: Path, key: str) -> Path:
    """Resolve a repo facts TOML key anchored at the repo root (facts_paths).

    The facts block is the single source for repo paths: an unresolvable key
    is a loud failure (mirroring plan_readiness), never a guessed default.
    """
    raw = facts_paths.resolve_toml_key_raw(root, key)
    if raw is None or not raw.strip():
        raise ValueError(
            f"cannot resolve {key} from .ai-playbook/facts.md "
            "(the facts block is the single source for repo paths; "
            "complete the facts block before running the gates)"
        )
    expanded = Path(raw).expanduser()
    if not expanded.is_absolute():
        expanded = root / expanded
    return expanded.resolve()


def _resolve_dir_or(root: Path, key: str, default_rel: str) -> Path:
    """Fallback variant reserved for plans_completed_dir: the derived
    completed-dir key is the one landed warn-and-scan-default contract (the
    plans-archive-twin gate names the fallback in a warning and scans the
    default home, never a failure), so discover must not refuse on it."""
    raw = facts_paths.resolve_toml_key_raw(root, key)
    if raw is None or not raw.strip():
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
    # In-memory provenance for the interrupted-run reports: the filename the
    # record was parsed from (set by ``_detect_interrupted_runs`` so a
    # worktree shadow copy can bind to its run by name). Never serialized:
    # ``as_dict`` emits the schema keys only, and every parse leaves it None.
    source_name: Optional[str] = None

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
    return _write_run_manifest_file(
        _manifest_path(done_session_dir, manifest.run_id), manifest
    )


def _write_run_manifest_file(path: Path, manifest: RunManifest) -> Path:
    """The writer's atomic manifest-update shape (temp file plus
    same-directory ``os.replace``) targeted at ``path``: the canonical
    ``run-manifest-<run_id>.json`` name for ``write_run_manifest``, or a
    shadow copy's own filename for the copy disposition's targeted stamp.
    The parent directory must already exist."""
    payload = json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n"
    tmp = path.parent / (path.name + ".tmp")
    try:
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return path


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


def _sanitize_manifest_error_value(raw: object, *, truncate: bool = True) -> str:
    """Render a raw field with controls stripped and, by default, capped at
    64 characters so corrupt input cannot forge log lines. Review-record
    basenames may exceed that cap, so their warning uses ``truncate=False``."""
    text = str(raw)
    screened = "".join(ch for ch in text if ch.isprintable())
    return screened[:64] if truncate else screened


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
    """Every manifest whose ``complete`` flag is still false and which is not
    closed at its run identity: the interrupted runs this Step 0 reports. A
    finalized (``complete`` true) manifest is never an orphan - that is what
    keeps a completed commit-less run from misfiring the detection - and
    adoption is itself the suppression record. Two widenings shape the set: a
    dead-root record (its recorded ``repo_root`` value fails the two-arm match
    - the manifest of a checkout that no longer exists) stays in the orphan
    set when ``complete`` is false and nothing adopts it, instead of being
    silently skipped by the root filter, so a dead-boundary incident surfaces
    until it closes; and a manifest carrying a ``dispositioned`` record is
    no longer detected as an orphan
    (the disposition is the sanctioned one-time closure: the adoption
    link is the first suppression shape, the disposition record the second).
    Closure reads at run identity (the payload ``run_id``, the same grouping
    ``classify_run_boundary`` applies): a terminal record on ANY file of the
    run - a ``complete`` record, an adopter's link naming the run id, or a
    ``dispositioned`` record, shadow copies included - suppresses every
    record of that run, so a worktree copy closed through its own evidence
    closes the whole boundary and no remaining record re-opens it. Each
    returned record carries ``source_name``, the filename it was parsed from,
    so the reports can bind a shadow copy (a non-canonical filename) to its
    run instead of counting it a second boundary. Unreadable records are
    skipped, never raised; a corrupt record is named
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
        manifest.source_name = path.name
        manifests.append(manifest)
    adopted = {m.adopted_from for m in manifests if m.adopted_from}
    by_run: dict[str, list[RunManifest]] = {}
    for manifest in manifests:
        by_run.setdefault(manifest.run_id, []).append(manifest)
    return [
        m
        for m in manifests
        if not m.complete
        and m.run_id not in adopted
        and m.dispositioned is None
        and not any(s.complete for s in by_run[m.run_id])
        and not any(s.dispositioned is not None for s in by_run[m.run_id])
    ]


def classify_run_boundary(
    done_session_dir: Path, manifest_path: Path
) -> tuple[str, Optional[str]]:
    """The canonical boundary verdict for the given manifest file, read at
    run identity (the payload ``run_id``): ``finalized``, ``adopted``, or
    ``dispositioned`` (the terminal states), ``shadow-closed``, ``orphan``,
    or ``unreadable``.

    Derived only through the existing ``RunManifest`` parse and the
    directory-wide adopted set, the same semantics ``_detect_interrupted_runs``
    applies: the run's records are every ``run-manifest-*.json`` payload
    sharing the given file's payload run id, so a terminal record on any of
    the run's files closes the boundary whichever file sorts newest;
    finalized is a ``complete`` record in the group, adopted is the run id
    appearing in the directory's adopted set, dispositioned is a
    ``dispositioned`` record in the group; everything else with ``complete``
    false is the unresolved orphan. A non-canonical given file (its name is
    not ``run-manifest-<run_id>.json``) on a terminal run is the worktree
    ``shadow-closed`` arm. An unparseable or schema-invalid given file is
    ``unreadable`` (fail-closed; the state is never guessed). Returns
    ``(verdict, run_id)``; the run id is the payload value when the record
    parses, else None. Read-only; never raises."""
    try:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unreadable", None
    newest = RunManifest.from_dict(payload)
    if newest is None:
        return "unreadable", None
    run_id = newest.run_id
    records: list[RunManifest] = []
    if done_session_dir.is_dir():
        for path in sorted(done_session_dir.glob("run-manifest-*.json")):
            try:
                record = RunManifest.from_dict(
                    json.loads(path.read_text(encoding="utf-8"))
                )
            except (OSError, ValueError):
                continue
            if record is not None:
                records.append(record)
    adopted = {m.adopted_from for m in records if m.adopted_from}
    group = [m for m in records if m.run_id == run_id]
    if any(m.complete for m in group):
        state: Optional[str] = "finalized"
    elif run_id in adopted:
        state = "adopted"
    elif any(m.dispositioned is not None for m in group):
        state = "dispositioned"
    else:
        state = None
    if state is None:
        return "orphan", run_id
    if manifest_path.name != _manifest_path(done_session_dir, run_id).name:
        return "shadow-closed", run_id
    return state, run_id


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
# Gate: plan-readiness (a landing sweep gate; the done skill links, never restates).
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
    """Mechanical candidate derivation for the landing sweep's plan-readiness gate (see plan Task 1)."""
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
    contract's no-line rule winning over the exit code.
    A modeled ready=no result is advisory: reported with its first
    failure, its candidate retired, the closeout proceeding. A label/exit
    contradiction is an indeterminate gate result naming the child. The
    aggregate exit carries the dominant bucket (tool error dominates
    indeterminate, matching ``phase_exit``; a modeled fail no longer
    carries the aggregate exit, the advisory arm above) while the message
    names every non-passing bucket (the contract's multi-input rule). The
    candidate derivation, the exemption arms, and the missing-validator
    deployment-gap refuse keep their pre-migration shape.
    Consumption note (corrections-chain-operator-ack plan, Task 2): the
    real child consumes the correction-record helper's primary-state
    authorization route, so an operator-acked hop's witness resolves from
    the primary checkout's correction_authorizations array inside the
    child; this gate's own ``_resolve_primary_checkout`` stays the
    dirty-state owner and never selects witness authority.
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
    remove.update(str(plan) for plan, _ in failed)
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
        # Tool error dominates indeterminate for the same run, and a modeled fail is advisory with its candidate retired
        return GateResult(gate, 3, message, warnings=[])
    if indeterminate:
        return GateResult(gate, 2, message, warnings=[])
    return GateResult(gate, 0, message, warnings=[])


# --------------------------------------------------------------------------- #
# Gate: confluence-hygiene (a landing sweep gate; the done skill links, never restates).
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
# Gate: doc-registry (a landing sweep gate; the done skill links, never restates).
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
# Gate: backlog-inbox (off the landing roster; the filing duty stays with receiving-review's capture step; kept as a callable for the survey arm).
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
        # Demotion split (closeout-gate demotion program change 4, D-7;
        # carrier row 2026-10-08-done-closeout-ceremony-friction): the
        # ledger entry reads 0 catches / 1 incident - a temporary
        # candidate-list filename tripped the shape check and a relocation
        # plus rerun passed - so a shape violation reports and the run
        # continues. The line names the flagged path via the validator's
        # tail rows; the remedy itself (move genuine backlog material into
        # the resolved backlog home per the receiving-review Backlog
        # capture) lives in the done skill's backlog-inbox bullet and is
        # still owed before the closeout lands.
        tail_rows = [
            row for row in (proc.stdout or "").strip().splitlines() if row.strip()
        ][-10:]
        warning = (
            "backlog-inbox: location violation (reported, not failing): "
            + " | ".join(tail_rows)
        )
        return GateResult(gate, 0, warning, warnings=[warning])
    return GateResult(gate, 0, "backlog inbox location gate passed", warnings=[])


# --------------------------------------------------------------------------- #
# Gate: review-staging (a landing sweep gate; the done skill links, never restates).
# --------------------------------------------------------------------------- #
def _all_staging_review_paths(ctx: GateContext) -> list[Path]:
    """Every on-disk staging doc under reviews_dir per the porcelain plus
    ignored-matching arms, filtered by the validator's own staging-path
    predicate only (NO session-window mtime filter): this is the Step 0
    claim-or-foreign enumeration universe, and the windowed derivation below
    narrows it. The library's own exec-receipt series grammar
    (``EXEC_REVIEW_SERIES_RE``) drops execution-completion receipts from
    this universe: a receipt is archive-certification evidence discovered
    independently by ``_has_exec_review_record``'s own rglob (which shares
    no list with this derivation), never a staged-review candidate, so the
    staging predicate's optional ``-r<N>`` tail can no longer pull a receipt
    into the universe the claim-or-foreign gate reads. Known grammar overlap,
    reported not silent: a staged review of a plan whose slug itself ends in
    ``-exec`` carries the series tail and is excluded with the receipt line;
    the exclusion can be narrowed to also require the ``-plan-review-``
    infix if that slug shape ever witnesses."""
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
        if EXEC_REVIEW_SERIES_RE.search(absolute.name):
            continue
        candidates.append(absolute)
    return sorted(candidates)


def _foreign_by_default_split(
    ctx: GateContext, uncovered: list[str], owned_review_paths: list[str]
) -> tuple[list[str], list[str]]:
    """Split the write-manifest claim-or-foreign uncovered set into
    (auto-foreign, still-refused).

    The gitignored primary reviews home is by design the shared run-artifact
    surface every run migrates records INTO, so its historical contents are
    structurally foreign to any single run; refusing on them is a false
    positive (witnessed 2026-10-23, the parked done setup in the primary
    checkout; landing commit b3025de59).
    A candidate qualifies for the foreign-by-default arm only when ALL hold:

    - the gate context's repo root IS the primary checkout (first
      ``git worktree list --porcelain`` entry); a run-owned linked worktree
      keeps the refuse arm, and an unresolvable worktree list fails closed
      to refuse;
    - the candidate is gitignored (``!!``-class under the reviews pathspec),
      the shared-home marker;
    - the candidate sits under the resolved reviews dir;
    - the run staged NONE of its own review records there (a run that did
      keeps the owned arm exactly as before).

    Everything else - candidates outside the reviews home, in a non-primary
    checkout, tracked-but-unclaimed, or any candidate at all when the run
    staged in the home - stays in the refuse set unchanged, so the witnessed
    2026-10-16 silent-claiming catch keeps its coverage.
    """
    primary, _primary_err = _resolve_primary_checkout(ctx)
    if primary is None:
        return [], list(uncovered)
    if os.path.realpath(str(primary)) != os.path.realpath(str(ctx.repo_root)):
        return [], list(uncovered)
    if not _is_relative_to(ctx.reviews_dir, ctx.repo_root):
        return [], list(uncovered)
    reviews_rel = ctx.reviews_dir.relative_to(ctx.repo_root).as_posix()
    if any(
        _is_relative_to(ctx.reviews_dir / p, ctx.reviews_dir)
        for p in owned_review_paths
    ):
        return [], list(uncovered)
    ignored = set(_ignored_paths(ctx, reviews_rel))
    auto: list[str] = []
    refused: list[str] = []
    for path in uncovered:
        rel = (
            Path(path)
            .resolve()
            .relative_to(ctx.repo_root.resolve())
            .as_posix()
            if _is_relative_to(ctx.repo_root / path, ctx.repo_root)
            else path
        )
        if rel in ignored and _is_relative_to(
            ctx.repo_root / rel, ctx.reviews_dir
        ):
            auto.append(rel)
        else:
            refused.append(path)
    return auto, refused


# --------------------------------------------------------------------------- #
# Bounded report emission: a gate report listing of more than SAMPLE_LIMIT
# entries reduces to the count plus at most SAMPLE_LIMIT sample entries
# inline, with the full enumeration written under the gate context's
# done-session directory (plan
# docs/history/plans/2026-10-10-done-closeout-lock-span-and-output-cost.md
# Task 2). Reporting channel only: never a gate predicate, a refusal class,
# or a verdict input.
# --------------------------------------------------------------------------- #
SAMPLE_LIMIT = 10
GATE_REPORTS_DIRNAME = "gate-reports"


def _gate_reports_dir(ctx: GateContext) -> Path:
    """The full-list home under the gate context's done-session directory
    (created on demand by the writer)."""
    return ctx.done_session_dir / GATE_REPORTS_DIRNAME


def _gate_report_run_scope(ctx: GateContext) -> str:
    """The report filename's run-identity scope: ``run-<run_id>-`` when the
    current window's run manifest resolves one, else the empty fallback so
    the phase-gate name alone scopes the file."""
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    return f"run-{manifest.run_id}-" if manifest is not None else ""


def _write_gate_report_full_list(
    ctx: GateContext,
    gate: str,
    entries: list[str],
) -> tuple[Optional[Path], Optional[str]]:
    """Write the full enumeration (one entry per line) under the done-session
    gate-reports home and return ``(path, None)``. On a write failure return
    ``(None, warning)`` with one line naming the failed write path: the
    write-failure arm degrades the emission, it never fails a gate and never
    enters a verdict."""
    path = _gate_reports_dir(ctx) / f"{_gate_report_run_scope(ctx)}{gate}-full.txt"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(entries) + "\n", encoding="utf-8")
    except OSError as exc:
        return None, (
            f"gate report full list write failed for {path}: {exc}; "
            "falling back to the unbounded inline emission"
        )
    return path, None


def bounded_report_lines(ctx: GateContext, gate: str, lines: list[str]) -> list[str]:
    """Bounded emission for a gate's report-line channel: at or under
    SAMPLE_LIMIT the lines pass through unchanged and nothing is written (no
    behavior change at small scale); above the bound one header line carrying
    the total count and the full-list file name precedes at most SAMPLE_LIMIT
    sample lines, and the full enumeration is written under the done-session
    gate-reports home. On a full-list write failure the emission degrades to
    the unbounded inline lines plus one warning line naming the failed write
    path."""
    if len(lines) <= SAMPLE_LIMIT:
        return list(lines)
    path, warning = _write_gate_report_full_list(ctx, gate, lines)
    if path is None:
        return list(lines) + [warning]
    header = (
        f"{len(lines)} report lines total (showing the first {SAMPLE_LIMIT}; "
        f"full list: {path})"
    )
    return [header, *lines[:SAMPLE_LIMIT]]


def bounded_inline_listing(
    ctx: GateContext,
    gate: str,
    entries: list[str],
) -> tuple[str, list[str]]:
    """Bounded emission for a gate's inline message listing (the docs-tmp
    sweep's kept join). At or under SAMPLE_LIMIT entries the fragment is the
    full inline join and no warnings are produced (no behavior change at
    small scale); above the bound the fragment carries the count, at most
    SAMPLE_LIMIT sample entries, and the full-list file name, and the full
    enumeration is written under the done-session gate-reports home. On a
    full-list write failure the fragment degrades to the full inline join
    plus one warning line naming the failed write path."""
    if len(entries) <= SAMPLE_LIMIT:
        return ", ".join(entries), []
    path, warning = _write_gate_report_full_list(ctx, gate, entries)
    if path is None:
        return ", ".join(entries), [warning]
    fragment = (
        f"{len(entries)} entries total (showing the first {SAMPLE_LIMIT}); "
        f"samples: {', '.join(entries[:SAMPLE_LIMIT])}; full list: {path}"
    )
    return fragment, []


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

    Both arms compute into local values and converge on one shared
    ``ReviewStagingScope`` construction exit, where preservation backups are
    excluded from the live candidates: a timestamped byte-identical backup
    pair written by the record-selection helper's ``backup`` subcommand is
    audit state, never a live review record (its stale ``Supersedes`` link
    can never satisfy the validator's name-based back-reference check, so
    validating one is an unsound false-block). The name test is the helper's
    single grammar (``BACKUP_INFIX`` in the basename, markdown and sidecar
    twin alike, imported rather than redefined so a grammar rename cannot
    re-create this defect class one rename later); each excluded path gets
    one informational report line (relative path plus reason, printed and
    never fatal, like the vanish and foreign-exclusion lines) and its file
    stays byte-identical on disk. The window arm's real backup pairs are
    already refused upstream by the validator's staging-path predicate
    (``BACKUP_NAME_RE`` inside ``_all_staging_review_paths``), so there the
    filter adds zero report lines and stays armed as defense-in-depth for a
    helper-grammar name lacking the timestamp shape; the live effect is the
    manifest arm, whose owned paths bypass the predicate on ``is_file``
    alone. Canonical records are never filtered: names the helper refuses to
    emit cannot carry the infix.
    """
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    report: list[str] = []
    if manifest is None:
        arm_candidates = _window_review_candidates(ctx, window)
        manifest_scoped = False
    else:
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
        arm_candidates = [unique[key] for key in sorted(unique)]
        manifest_scoped = True
    # One shared construction exit: preservation backups (the record-selection
    # helper's timestamped copy pairs) are audit state, never live candidates,
    # and execution-completion receipts (the library's own
    # ``EXEC_REVIEW_SERIES_RE`` grammar) are archive-certification evidence
    # outside the staged-review schema. The filter only ever removes
    # candidates, so a filtering bug cannot suppress a canonical validation: a
    # canonical record's name never carries the infix the helper refuses to
    # emit, and a genuine staged review never carries the receipt tail the
    # execute-plan completion-evidence namespace owns. The receipt arm keeps
    # a manifest-claimed receipt out of the validator while the archive
    # gate's independent discovery still certifies it; the window arm's real
    # receipts are already refused upstream by the enumeration-universe
    # filter, so there this arm adds zero report lines and stays armed as
    # defense-in-depth.
    candidates: list[Path] = []
    for candidate in arm_candidates:
        if BACKUP_INFIX in candidate.name:
            report.append(
                "excluded preservation backup from validation (record-selection "
                "helper backup grammar: audit state, never a live review "
                "record; file preserved): "
                + _manifest_review_rel(ctx, str(candidate))
            )
            continue
        if EXEC_REVIEW_SERIES_RE.search(candidate.name):
            report.append(
                "excluded execution-completion receipt from validation "
                "(execute-plan completion-evidence namespace: archive "
                "certification discovers it independently; outside the "
                "staged-review schema; file preserved): "
                + _manifest_review_rel(ctx, str(candidate))
            )
            continue
        candidates.append(candidate)
    return ReviewStagingScope(candidates, report, manifest_scoped)


def derive_review_staging_candidates(ctx: GateContext) -> list[Path]:
    """The review-staging gate's candidates: the run manifest's owned review
    paths when a manifest is present, else the legacy porcelain plus
    ignored-matching paths under reviews_dir restricted to the session window
    and filtered by the validator's own staging-path predicate. Never a
    bare glob, never chat recall.

    F4/F8 branch asymmetry, deliberate and fail-closed: in the manifest
    branch, an owned path that exists on disk is validated on existence alone
    (is_file), regardless of the staging-path predicate - over-validation
    can only over-check a claimed artifact - while the fallback window arm
    applies the staging-path predicate to each candidate. The two sanctioned
    suppression arms live at the shared scope exit, each with an
    informational line per excluded path: the backup exclusion (the
    record-selection helper's timestamped byte-identical copy pairs, audit
    state rather than live records, excluded by the helper's single
    ``BACKUP_INFIX`` grammar, because a byte-identical backup can never
    satisfy the validator's name-based ``Supersedes`` back-reference check
    and validating one is an unsound false-block) and the exec-receipt
    exclusion (the library's own ``EXEC_REVIEW_SERIES_RE`` grammar, because
    a receipt is archive-certification evidence outside the staged-review
    schema that the archive gate discovers independently); every other
    claimed artifact is still over-checked, never suppressed."""
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
    keep their pre-migration shape. The candidate derivation excludes
    preservation backups before any validation runs: a timestamped
    byte-identical backup pair written by the record-selection helper's
    ``backup`` subcommand is audit state, never a live candidate (its stale
    ``Supersedes`` link can never name-match), sourced from the helper's
    single ``BACKUP_INFIX`` grammar and reported with one informational line
    per excluded path; canonical records and the validator's link-integrity
    refusals are untouched."""
    gate = "review-staging"
    scope = derive_review_staging_scope(ctx)
    candidates = scope.candidates
    # Bounded report-line emission: the foreign-exclusion, vanish, backup, and
    # receipt lines keep their per-line text; above the sample bound the list
    # reduces to a count header plus samples with the full enumeration on
    # disk. Warnings stay warnings: never a verdict input.
    warnings = bounded_report_lines(ctx, gate, scope.report_lines)
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
# Gate: vim-swap-sweep (off the landing roster; a periodic survey advisory; kept as a callable for that arm).
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
# Gate: docs-tmp-sweep (a landing sweep gate; the sole governor of run-start marker pruning).
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

    kept_warnings: list[str] = []
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
        # Bounded kept join: above the sample bound the listing reduces to a
        # count plus samples inline with the full enumeration on disk; a
        # failed full-list write degrades to the full join plus one warning
        # line. Kept rows stay informational: never a verdict input.
        kept_fragment, kept_warnings = bounded_inline_listing(ctx, gate, kept)
        message += "; kept: " + kept_fragment
    return GateResult(gate, 0, message, warnings=kept_warnings)


def _prune_done_session_markers(
    ctx: GateContext,
    done_session: Path,
    window: SessionWindow,
    removed: list[str],
    kept: list[str],
) -> None:
    """Remove run-start-* markers strictly older than the previous-run anchor;
    the anchor and the current-run marker are immune; an unanchorable window
    or unparseable content prunes nothing (never guess by recency). The same
    window rule governs the bounded reports' gate-reports home: a file whose
    mtime sits strictly older than the anchor (outside the current session
    window) is removed, a file inside the window stays, and an unreadable
    mtime keeps the file (never guessing)."""
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
    gate_reports = done_session / GATE_REPORTS_DIRNAME
    if not gate_reports.is_dir():
        return
    for report_file in sorted(gate_reports.iterdir()):
        if not report_file.is_file():
            continue
        try:
            mtime = report_file.stat().st_mtime
        except OSError:
            kept.append(str(report_file) + " (mtime unreadable; never guessing)")
            continue
        if mtime < anchor_epoch:
            try:
                report_file.unlink()
                removed.append(str(report_file))
            except OSError:
                kept.append(str(report_file))
        else:
            kept.append(str(report_file) + " (inside the session window; immune)")


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
# Gate: sensitive-data-scan (a landing sweep gate; re-run over each staged side-repo set by the commit runner).
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
    profile_exempt = ctx.project_type == "company" or (
        ctx.project_type == "pet" and ctx.artifact_visibility == "private"
    )
    if profile_exempt:
        # The profile exemption skips both content arms entirely: arms 1
        # and 2 below iterate an empty pattern list, while arms 3 and 4
        # still run for every profile.
        content_patterns: list[str] = []
    else:
        content_patterns = list(CREDENTIAL_CONTENT_PATTERNS)
        content_patterns.extend(PUBLIC_ARTIFACT_CONTENT_PATTERNS)
        families = "content families: credential+public-artifact"

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
    if profile_exempt:
        clean = (
            "sensitive-data scan clean (content arms skipped by profile "
            "exemption: company or private-pet"
        )
        if push_range_ran:
            clean += "; push-range commit messages"
        return GateResult(gate, 0, clean + ")", warnings=warnings)
    return GateResult(
        gate,
        0,
        "sensitive-data scan clean (diff content, untracked content"
        + (", push-range commit messages" if push_range_ran else "")
        + "); " + families,
        warnings=warnings,
    )


# --------------------------------------------------------------------------- #
# Gates: em-dash-scan and instruction-size (landing sweep gates; instruction-size in warning posture).
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
    """Landing gate: the commit-boundary re-run over the final staged set.

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
# Gate: post-landing-staging (a landing sweep gate).
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


def _plan_edit_marker_only(worktree_diff: str) -> bool:
    """The A6 class-1 read over a worktree-vs-HEAD plan diff.

    The runtime's own marker-only classifier, imported (never re-implemented
    here, matching the lib's import-don't-duplicate contract). An import
    failure (this lib deployed beside an older driver copy) classifies as
    not-marker-only, so the admission arm degrades to today's refusal and
    never to a silent pass.
    """
    try:
        from execute_plan_runtime import _diff_is_checkbox_marker_only
    except Exception:
        return False
    return _diff_is_checkbox_marker_only(worktree_diff)


def gate_post_landing_staging(ctx: GateContext) -> GateResult:
    """Landing gate: the post-landing staging invariant over the primary
    checkout (plan: squash-landing-failure-path-guard, Task 3).

    The primary checkout's index must match HEAD except for staged paths
    owned by the resolvable current-session manifest plus the invocation's
    declared-stage channel (the foreign-staging ownership pattern: the union
    of ``owned_paths``, ``owned_plan_paths``, ``owned_review_paths``, named
    as owned, plus the ``DONE_SWEEP_DECLARED_STAGE_PATHS`` channel's paths
    when the checkout-shape guard holds, the guard being the consumption
    condition that the gate's resolved primary checkout equals the gate
    context's repo root, the primary-resident shape where the declared set
    is the shape the gate inspects; the manifest stays fixed at write time,
    the channel being an invocation-scoped environment input handed to this
    very sweep, never a manifest edit, so the manifest's claim sets are
    never widened in place); unstaged tracked modifications
    are permitted only for the record-only allowlist and for the run's own
    owned plan paths whose worktree-vs-HEAD diff classifies
    checkbox-marker-only in place (the execute-plan lifecycle recovery plan's
    A6 class-1 read: the sanctioned Step 1.3 plan flip this run still owes its
    task commit; the disposition receipt is required only at the runtime done
    boundary for committed paths, never at this sweep). Residue is inspected
    FIRST and only then is ``done-lock.sh merge-status`` re-consulted, so
    blocking residue (staged residue; the manifest-owned unstaged leg is a
    demoted warning class as of program change 7) observed while the
    lock is now held reports indeterminate (a landing is in flight, never a
    violation) instead of a refusal - closing the consult-then-inspect race
    (the demoted unowned-unstaged and manifest-owned-unstaged classes never
    reach the consult). Unowned
    unstaged residue reports and
    continues (a warning line carrying the sanctioned cleanup recipe and the
    operator escape; the demotion program's incident-heavy leg - every
    ledger incident in this class is peer-window dirt, an advisory append,
    or own-run work a manifest omission left unowned), and manifest-owned
    unstaged residue reports and continues too (the guard entry
    post-landing-staging-gate reads 0 catches / 1 incident, the 2026-10-05
    owned-plan refusal witnessed three times - the run's own unstaged owned
    paths read as landing residue and the refusal named a harmful remedy -
    so the warning carries the misdirected-write check first and staging
    the owned path as the sanctioned resolution, never a destructive one);
    staged residue still fails
    the closeout naming the residue paths, the sanctioned cleanup recipe
    (the helper's probe-then-reland path), and the operator escape for dead
    residue; record-only allowlist paths are never escapable. Untracked
    paths are reported-not-failing (warning lines). The gate inspects the
    primary checkout read-only (``git -C <primary>``); an unresolvable
    worktree list or an unreadable primary checkout is a tool error.

    Placement contract (plan: post-landing-staging-placement-awareness,
    Task 1): the gate reads the project facts' declared ``worktree_policy``
    key once per run through ``facts_paths.resolve_toml_key_raw``. A
    resolution of exactly ``primary`` or ``primary-execution`` (the
    primary-resident placements) widens the unstaged leg's exemption to the
    staged leg's ownership set: in a primary-resident checkout the run's own
    unstaged manifest-owned edits are structural run state, not landing
    residue, so they pass with an informational count. Every other reading
    is fail-closed to unconfigured (an absent key, an unreadable facts file,
    a malformed or out-of-vocabulary value, a resolution failure) and, after
    program change 7, converges on the same warning arm anyway: the
    manifest-owned unstaged class reports-not-failing under every placement
    reading, so the fail-closed reading's residual strictness lives entirely
    on the staged leg; the unresolvable-manifest strict
    path is placement-independent (no manifest means no owned set, so the
    widening is inert under every placement). The indeterminate arms stay
    keyed on the residue composition, not the placement: a residue state
    that survives the widening still reaches them unchanged, while an
    owned-unstaged-only state passes under a primary-resident placement and
    never reaches them. The rc-1 refusal is staged-residue-only after
    program change 7 and keeps the probe-then-reland recipe and the guarded
    operator escape verbatim; no refusing class contains an owned path
    (owned staged paths are exempt with an informational count, and the
    owned-unstaged class warns), so the former owned-class
    misdirected-write refusal arm is removed - the misdirected-write check
    and the staging resolution live in the owned-unstaged warning line.
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
    # The declared worktree placement, read once per run through the facts
    # reader (the plans-archive-twin gate's invocation precedent). Fail-closed:
    # an absent key, an unreadable facts file, a malformed or
    # out-of-vocabulary value, or a resolution failure all read as
    # unconfigured, so only the two spelled primary-resident forms widen the
    # unstaged leg.
    try:
        placement = facts_paths.resolve_toml_key_raw(
            ctx.repo_root, "worktree_policy"
        )
    except Exception:
        placement = None
    placement_primary = placement in ("primary", "primary-execution")
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
    declared_channel: list[str] = []
    if owned is not None:
        # The declared-stage channel (plan
        # 2026-10-14-done-ownership-post-setup-learn-edits, Task 2): the
        # commit invocation's own declared set, read with the lib's
        # DONE_SWEEP_* os.environ house-style and consumed only when a
        # manifest resolved (the no-manifest path keeps today's strict
        # behavior byte-identical) and the checkout-shape guard holds: the
        # gate's resolved primary checkout must equal the gate context's
        # repo root, the primary-resident shape where the declared set is
        # the shape the gate inspects. Any other shape ignores the channel
        # with one named warning line; every non-consuming reading (unset,
        # empty, unresolvable manifest, guard not holding) contributes
        # nothing and never errors. Consumed lines are split on newlines,
        # blank lines skipped, normalized through the same repo-relative
        # normalization the manifest claim legs receive, and the record-only
        # allowlist is subtracted before the union into owned.
        raw_channel = os.environ.get("DONE_SWEEP_DECLARED_STAGE_PATHS")
        if raw_channel:
            # The guard's equality compares realpath-resolved paths on both
            # sides (git's printed primary path is not canonical under
            # symlink aliasing); an unresolvable comparison fails closed to
            # ignoring the channel.
            try:
                primary_is_root = (
                    Path(primary).expanduser().resolve() == ctx.repo_root.resolve()
                )
                guard_note = ""
            except (OSError, RuntimeError, ValueError):
                primary_is_root = False
                guard_note = (
                    "the primary-vs-repo-root realpath comparison could not "
                    "be resolved"
                )
            if not primary_is_root:
                warnings.append(
                    "post-landing-staging: DONE_SWEEP_DECLARED_STAGE_PATHS "
                    "is set but the checkout-shape guard does not hold ("
                    + (guard_note or (
                        "the resolved primary checkout " + str(primary)
                        + " is not this gate context's repo root"
                    ))
                    + "); the declared-stage channel is ignored and the "
                    "strict staged-residue check is kept"
                )
            else:
                channel_owned = {
                    _manifest_review_rel(ctx, line)
                    for line in raw_channel.split("\n")
                    if line.strip()
                } - RECORD_ONLY_ALLOWLIST
                if channel_owned:
                    owned = owned | channel_owned
                    declared_channel = sorted(channel_owned)
    staged_residue = sorted(staged - owned) if owned is not None else sorted(staged)
    owned_staged = sorted(staged & owned) if owned is not None else []
    # The plan-checkbox admission arm: an unstaged (not simultaneously
    # staged) owned plan path whose worktree-vs-HEAD diff classifies
    # checkbox-marker-only is admitted in place. No manifest means no owned
    # plan claims, so nothing admits; after demotion changes 1 and 7 the
    # class lands in the unstaged warning arms either way, never a refusal.
    admitted_plan_residue: list[str] = []
    if manifest is not None:
        owned_plan_paths = {recorded for recorded in manifest.owned_plan_paths}
        for path in sorted((unstaged - staged) & owned_plan_paths):
            diff = ctx.run(
                ["git", "-C", str(primary), "diff", "HEAD", "--", path],
                cwd=ctx.repo_root,
            )
            if diff.returncode == 0 and _plan_edit_marker_only(diff.stdout):
                admitted_plan_residue.append(path)
    owned_unstaged: list[str] = []
    if placement_primary and owned is not None:
        # The placement-aware widening: under a primary-resident placement
        # the primary checkout is an authorized execution surface, so the
        # run's own unstaged manifest-owned edits there are structural run
        # state, not landing residue; the unstaged leg mirrors the staged
        # leg's ownership exemption. The count set is the post-allowlist
        # intersection, so an owned path the record-only allowlist already
        # permits is counted exactly once (in the allowlist clause, never
        # in the owned-unstaged clause). No manifest means no owned set,
        # so the widening stays inert under every placement.
        dirty_residue = sorted(
            unstaged - RECORD_ONLY_ALLOWLIST - owned - set(admitted_plan_residue)
        )
        owned_unstaged = sorted((unstaged - RECORD_ONLY_ALLOWLIST) & owned)
    else:
        dirty_residue = sorted(unstaged - RECORD_ONLY_ALLOWLIST - set(admitted_plan_residue))
    allowed_dirty = sorted(unstaged & RECORD_ONLY_ALLOWLIST)
    # Demotion split (closeout-gate demotion program change 1, D-7; carrier
    # row 2026-10-08-done-closeout-ceremony-friction): the UNOWNED unstaged
    # residue class is the incident-heavy leg - every ledger incident row
    # under this gate is peer-window dirt, an advisory append, or own-run
    # work a manifest omission left unowned, refused at the done boundary
    # (scripts/gate_liveness_ledger.json, guard post-landing-staging) - so
    # it reports and continues
    # like the untracked arm, with the sanctioned cleanup recipe carried in
    # the warning line.
    # The staged leg keeps its refusal under every ownership class (both
    # recorded ledger catches are compatible with the staged leg: the
    # manifest-less strict staged leg names it explicitly, and the live peer
    # corpus-migration boundary presents as staged mid-migration).
    # Demotion split (closeout-gate demotion program change 7, D-7; carrier
    # row 2026-10-08-done-closeout-ceremony-friction): the manifest-owned
    # UNSTAGED class joined the warning arm - the guard entry
    # post-landing-staging-gate reads 0 catches / 1 incident, the
    # 2026-10-05 owned-plan refusal witnessed twice plus a reproduced third
    # case (the run's own unstaged owned paths read as landing residue and
    # the refusal named a harmful remedy) - so it reports and continues
    # under every placement reading, with the misdirected-write check and
    # the staging resolution carried in its warning line; the placement
    # admission arm above stays as the informational count. With no resolvable
    # manifest every unstaged path is unowned by construction, so the
    # unresolvable-manifest warning plus this warning is the whole unstaged
    # story there; the strict staged check is untouched.
    # An MM row (staged and worktree-modified) is refused on its staged leg,
    # so its unstaged leg never claims it reported-not-failing in the warning.
    staged_set = set(staged_residue)
    owned_unstaged_warn = (
        [path for path in dirty_residue if path in owned]
        if owned is not None
        else []
    )
    unowned_dirty = [
        path
        for path in dirty_residue
        if path not in staged_set
        and (owned is None or path not in owned)
    ]
    if owned_unstaged_warn:
        warnings.append(
            "post-landing-staging: manifest-owned unstaged residue in the "
            "primary checkout (reported, not failing): "
            + ", ".join(sorted(owned_unstaged_warn))
            + "; misdirected-write check first: verify the run's worktree "
            "copy is authoritative before any restore; sanctioned "
            "resolution: stage the owned path (git add <path>), which "
            "clears the leg under any placement, never the bare restore "
            "escape or the reland path for an owned path"
        )
    if unowned_dirty:
        warnings.append(
            "post-landing-staging: unowned unstaged residue in the primary "
            "checkout (reported, not failing): " + ", ".join(sorted(unowned_dirty))
            + "; sanctioned cleanup when the residue is dead: the "
            "land_squash.sh probe-then-reland path (run scripts/land_squash.sh "
            "probe, resolve or compose, then scripts/land_squash.sh land "
            "under the merge lock); operator escape for dead residue only "
            "(done-lock.sh merge-status free AND the path is not peer-live "
            "dirt): git restore --staged --worktree -- <path> per residue path"
        )
    residue = staged_residue
    if residue:
        held, evidence = _merge_lock_held(ctx)
        residue_render = (
            "staged path(s): " + (", ".join(staged_residue) or "none")
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
        # The refusal is staged-residue-only after program change 7: the
        # owned-unstaged class warns above, and manifest-owned STAGED paths
        # are exempt with an informational count (staged_residue subtracts
        # owned), so no refusing class contains an owned path and the
        # owned-class misdirected-write refusal arm is gone (the
        # misdirected-write guidance lives in the warning line).
        refusal = (
            "post-landing-staging gate failed: primary checkout residue "
            f"after landing ({residue_render}); sanctioned cleanup: the "
            "land_squash.sh probe-then-reland path (run scripts/land_squash.sh "
            "probe, resolve or compose, then scripts/land_squash.sh land "
            "under the merge lock); operator escape for dead residue only "
            "(done-lock.sh merge-status free AND the path is not peer-live "
            "dirt): git restore --staged --worktree -- <path> per residue "
            "path; record-only allowlist path(s) are never escapable"
        )
        # Plan: 2026-10-05-execute-plan-done-boundary-evidence-gates Task 1.
        # The mid-session-creation remedy: when the residue includes staged
        # paths and the run manifest resolved for the session window
        # (owned is not None), the rc-1 message names the adopting-boundary
        # recovery. The no-manifest arm (owned is None), the indeterminate
        # arms above, and every other gate leg keep today's render verbatim.
        if staged_residue and owned is not None:
            refusal += (
                "; a staged path created after Step 0 (absent from every "
                "manifest claim set) is recovered by closing this done "
                "boundary and opening a fresh adopting boundary, per the "
                "Step 0 adopt clause's operator authorization, "
                "whose re-derived owned-path set names only paths that adopting boundary's own session created "
                "(the operator-authorized cross-session arm keeps the adopted run's own uncommitted "
                "output per the existing adoption re-derivation record), "
                "never by widening the active manifest in place"
            )
            # Plan: 2026-10-14-done-ownership-post-setup-learn-edits Task 3:
            # the post-setup remedy, named beside the preserved
            # adopting-boundary sentence (whose render stays verbatim); the
            # no-manifest arm (owned is None) never reaches either sentence.
            refusal += (
                "; a live edit authored after setup (the documented learn "
                "step's product) is landed by re-running the commit with "
                "the path declared via --stage"
            )
        return GateResult(
            gate,
            1,
            refusal,
            warnings=warnings,
        )
    message = (
        "post-landing-staging gate passed: primary index matches HEAD (no "
        "unowned staging, no blocking residue)"
    )
    if admitted_plan_residue:
        message += (
            "; checkbox-marker-only plan residue admitted in place: "
            + ", ".join(admitted_plan_residue)
        )
    if allowed_dirty:
        message += (
            "; record-only allowlist path(s) permitted: "
            + ", ".join(allowed_dirty)
        )
    if declared_channel:
        message += (
            "; declared-stage channel path(s) owned ("
            + str(len(declared_channel)) + "): "
            + ", ".join(declared_channel)
        )
    if owned_staged:
        message += (
            "; staged path(s) owned by the session manifest or the "
            "invocation's declared-stage channel: "
            + ", ".join(owned_staged)
        )
    if owned_unstaged:
        message += (
            "; unstaged path(s) owned by the session manifest or the "
            "invocation's declared-stage channel: "
            + ", ".join(owned_unstaged)
        )
    if untracked:
        warnings.append(
            "post-landing-staging: untracked path(s) in the primary checkout "
            "(reported, not failing): " + ", ".join(sorted(untracked))
        )
    return GateResult(gate, 0, message, warnings=warnings)


# --------------------------------------------------------------------------- #
# Gate: plans-root-claim-fence (a landing sweep gate; plan
# 2026-10-05-live-claim-plan-deletion-fence.md Task 2). Thin CLI-child gate
# over the reverse-squash guard's check-claim-fence subcommand.
# --------------------------------------------------------------------------- #
# Contract twin: this parser mirrors the guard's refusal-block emission in
# reverse_squash_guard.py cmd_check_claim_fence (the "claim-fence:" block
# header and each block's "live claim:" line); a format edit updates both.
def _claim_fence_refusal_blocks(stdout: str) -> list[tuple[str, str]]:
    """The guard child's refusal blocks as ``(path, claim)`` pairs, parsed
    from the guard's ``claim-fence: <path> deleted while its claim is live``
    block headers and each block's ``live claim:`` line (a header whose claim
    line never arrives carries an empty claim)."""
    header_prefix = "claim-fence: "
    header_suffix = " deleted while its claim is live"
    blocks: list[tuple[str, str]] = []
    in_block = False
    for raw in stdout.splitlines():
        stripped = raw.strip()
        if stripped.startswith(header_prefix) and stripped.endswith(header_suffix):
            blocks.append(
                (stripped[len(header_prefix): -len(header_suffix)], "")
            )
            in_block = True
            continue
        if in_block and stripped.startswith("live claim: "):
            blocks[-1] = (blocks[-1][0], stripped[len("live claim: "):])
    return blocks


def gate_plans_root_claim_fence(ctx: GateContext) -> GateResult:
    """Landing gate: the plans-root deletion claim fence over the run range.

    Thin CLI-child gate in the review-staging gate's pattern: it invokes the
    reverse-squash guard's ``check-claim-fence --base <start_commit> --head
    HEAD`` over the active run manifest's ``start_commit..HEAD`` range (the
    guard resolved per the sweep-gates lib rule: env override, then the
    repo-local ``scripts/`` copy, then the deployed runtime home), and routes
    the child's four-outcome contract exactly: exit 0 passes with the child's
    sanction lines in the message; exit 1 lands in the failed bucket with the
    refusal blocks; exit 2 is indeterminate naming the target; exit 3 or a
    missing final ``OUTCOME:`` line is tool error (the contract's no-line
    rule, never a silent pass); a label/exit contradiction is indeterminate
    naming the target.

    The ``start_commit..HEAD`` range is shared with peer commits, so the
    refusal arm classifies with the done lib's existing foreign-commit
    classification (``_classify_committed_range`` over the run's owned-commits
    ledger and every ``adopted_from`` ancestor): a refused path no owned
    commit deleted (no ``D`` row in the owned name-status rows) is a
    foreign-commit deletion, reported as a named report line and never a gate
    failure (the battery's foreign-artifact treatment; the peer's own closeout
    fences it), while a refused path an owned commit deleted keeps the failed
    bucket. A child refusal naming no parsable block fails closed with the
    child output tail. An empty run range is a warning skip naming the reason;
    so is a plans home that resolves to nothing (absent on disk AND carrying
    no plans tree at the boundary commit or at HEAD: a run whose own commit
    emptied the plans root keeps its scan, because the diff-based child is
    exactly the arm that must judge it), never silent vacuous passes.
    """
    gate = "plans-root-claim-fence"
    warnings: list[str] = []
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(
        ctx.done_session_dir, ctx.repo_root, window, warnings=warnings
    )
    if manifest is None:
        message = (
            "plans-root-claim-fence: warning skip: no resolvable active run "
            "manifest (Step 0 record absent, foreign-rooted, or "
            "schema-invalid); no run range to scan"
        )
        return GateResult(gate, 0, message, warnings=warnings)
    base = manifest.start_commit
    rev_list = ctx.git("rev-list", f"{base}..HEAD")
    if rev_list.returncode == 0 and not rev_list.stdout.strip():
        message = (
            "plans-root-claim-fence: warning skip: the run range "
            f"({base}..HEAD) is empty (no commits since the Step 0 boundary); "
            "no deletion to scan"
        )
        return GateResult(gate, 0, message, warnings=warnings)
    if not ctx.plans_dir.is_dir():
        plans_rel = _plans_pathspec(ctx)
        surface_at = [
            commitish
            for commitish in ("HEAD", base)
            if ctx.git("cat-file", "-e", f"{commitish}:{plans_rel}").returncode == 0
        ]
        if not surface_at:
            message = (
                "plans-root-claim-fence: warning skip: the plans home does "
                f"not exist on disk: {ctx.plans_dir}; no plans-root surface "
                "to scan"
            )
            return GateResult(gate, 0, message, warnings=warnings)
    guard = ctx.resolve_script(
        "REVERSE_SQUASH_GUARD_SCRIPT", "reverse_squash_guard.py"
    )
    if guard is None:
        return GateResult(
            gate,
            3,
            "plans-root-claim-fence gate tool error: reverse_squash_guard.py "
            "is absent from every resolved path (env override, repo-local "
            "scripts/, deployed runtime home); the claim-fence child cannot "
            "run, so the scan is tool error, never a pass",
            warnings=warnings,
        )
    proc = ctx.run(
        [
            sys.executable,
            str(guard),
            "check-claim-fence",
            "--base",
            base,
            "--head",
            "HEAD",
            "--repo",
            str(ctx.repo_root),
        ],
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
        return GateResult(
            gate,
            3,
            "plans-root-claim-fence gate tool error: child run with no final "
            f"OUTCOME line (child exit {proc.returncode}; the contract's "
            f"no-line rule classifies tool error, never a pass): {tail}",
            warnings=warnings,
        )
    if label == "pass" and proc.returncode == 0:
        message = (
            "plans-root-claim-fence gate passed: no live-claim plans-root "
            "deletion in the run range"
        )
        if evidence:
            message += "; sanction lines: " + " | ".join(evidence)
        return GateResult(gate, 0, message, warnings=warnings)
    if label == "fail" and proc.returncode == 1:
        blocks = _claim_fence_refusal_blocks(proc.stdout or "")
        if not blocks:
            return GateResult(
                gate,
                1,
                "plans-root-claim-fence gate failed: the child refused but "
                "named no parsable refusal block (fail closed with the child "
                f"output tail): {tail}",
                warnings=warnings,
            )
        chain, chain_warnings = _adopted_chain_run_ids(
            ctx.done_session_dir, manifest, repo_root=ctx.repo_root
        )
        owned_rows, classification_lines = _classify_committed_range(
            ctx,
            base,
            [
                _owned_commits_ledger_path(ctx.done_session_dir, run_id)
                for run_id in chain
            ],
        )
        owned_deleted = {
            row.split("\t", 1)[1]
            for row in owned_rows
            if row.split("\t", 1)[0] == "D" and "\t" in row
        }
        own: list[tuple[str, str]] = []
        foreign: list[tuple[str, str]] = []
        for refused_path, claim in blocks:
            if refused_path in owned_deleted:
                own.append((refused_path, claim))
            else:
                foreign.append((refused_path, claim))
        warnings.extend(chain_warnings)
        warnings.extend(classification_lines)
        for refused_path, claim in foreign:
            warnings.append(
                "foreign-commit deletion reported (never a gate failure; the "
                "deleting commit is foreign to this run's owned-commits "
                f"ledger, the peer's own closeout fences it): {refused_path}"
                + (f" (live claim: {claim})" if claim else "")
            )
        if own:
            detail = "; ".join(
                refused_path + (f" (live claim: {claim})" if claim else "")
                for refused_path, claim in own
            )
            return GateResult(
                gate,
                1,
                "plans-root-claim-fence gate failed: own-commit plans-root "
                "deletion under a live claim; sanctioned exits: archive the "
                "file in the same commit, stand down and restore the file, "
                "or record a Plans-Deletion-Ack: <path> trailer in the "
                f"deleting commit's message: {detail}",
                warnings=warnings,
            )
        message = (
            "plans-root-claim-fence gate passed: every refused deletion in "
            f"the child's verdict is a foreign-commit deletion ({len(foreign)} "
            "reported as warnings; the peer's own closeout fences it)"
        )
        return GateResult(gate, 0, message, warnings=warnings)
    if label == "indeterminate" and proc.returncode == 2:
        return GateResult(
            gate,
            2,
            "plans-root-claim-fence gate reported indeterminate: the guard "
            f"could not resolve its diff source (target {base}..HEAD): {tail}",
            warnings=warnings,
        )
    if label == "tool_error" and proc.returncode == 3:
        return GateResult(
            gate,
            3,
            "plans-root-claim-fence gate tool error (the guard child's "
            f"outcome): {tail}",
            warnings=warnings,
        )
    return GateResult(
        gate,
        2,
        f"plans-root-claim-fence gate reported indeterminate: child exit "
        f"{proc.returncode} contradicts its OUTCOME: {label} line: {tail}",
        warnings=warnings,
    )


DATED_PLAN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")


def gate_plans_archive_twin(ctx: GateContext) -> GateResult:
    """Landing-time twin gate over the plans home (one deduped landing run slot).

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
# Gate: archive-ceremony (a landing sweep gate; plan 2026-10-01-done-
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


def _head_regular_archive_file(
    ctx: GateContext, rel: str
) -> Optional[str]:
    """Return a diagnostic unless HEAD stores ``rel`` as a regular blob."""
    listing = ctx.git("ls-tree", "HEAD", "--", rel)
    if listing.returncode != 0:
        return (
            f"archive mode lookup failed at HEAD: {rel}: "
            f"{listing.stderr.strip() or 'git ls-tree failed'}"
        )
    rows = [line for line in listing.stdout.splitlines() if line]
    if len(rows) != 1:
        return f"archive evidence missing or ambiguous at HEAD: {rel}"
    entry, separator, found_path = rows[0].partition("\t")
    mode = entry.split(None, 1)[0] if separator else ""
    if found_path != rel or mode not in {"100644", "100755"}:
        return f"archive evidence is not a regular file at HEAD: {rel} (mode {mode or 'unknown'})"
    return None


def _archive_twin_at_head(
    ctx: GateContext, plan_rel: str
) -> tuple[Optional[str], Optional[str]]:
    """The repo-relative archive twin of a vanished plan path when one exists
    at HEAD (same basename in the first archive state directory carrying
    it); no twin plus no error when no archive is committed. The keying accepts the
    directory twin: a vanished path under a plans-root directory
    ``<slug>/`` (or the charter path itself) twins at
    ``<state>/<slug>/<charter>``, keyed on the directory slug; the file
    twin ``<state>/<basename>`` must be a blob (never a tree), so a
    directory archive's tree path never masquerades as a file twin."""
    path = Path(plan_rel)
    name = path.name
    plan_dir = name
    if name == plan_shape.CHARTER_FILENAME:
        plan_dir = path.parent.name
    for _state, directory in _archive_state_dirs(ctx):
        try:
            prefix = str(
                directory.resolve().relative_to(ctx.repo_root.resolve())
            )
        except ValueError:
            continue
        twin_dir_rel = f"{prefix}/{plan_dir}/{plan_shape.CHARTER_FILENAME}"
        listing = ctx.git("ls-tree", "-r", "--name-only", "HEAD", "--", prefix)
        if listing.returncode != 0:
            return None, (
                "archive-state tree listing failed at HEAD: "
                f"{prefix}: {listing.stderr.strip() or 'git ls-tree failed'}"
            )
        paths = set(listing.stdout.splitlines())
        if twin_dir_rel in paths:
            return twin_dir_rel, None
        file_rel = f"{prefix}/{name}"
        if file_rel in paths:
            probe = ctx.git("cat-file", "-t", f"HEAD:{file_rel}")
            if probe.returncode != 0:
                return None, (
                    "archive-file type lookup failed at HEAD: "
                    f"{file_rel}: {probe.stderr.strip() or 'git cat-file failed'}"
                )
            if probe.stdout.strip() == "blob":
                return file_rel, None
    return None, None


def _archive_unit(ctx: GateContext, rel: str) -> tuple[Optional[str], Optional[str]]:
    """The archive unit a repo-relative archive-state path carries, as
    ``(kind, state prefix)``: ``"file"`` for a bare archived file directly
    under the state directory, ``"charter"`` for a directory plan's
    charter at ``<state>/<slug>/<charter>``, ``"member"`` for any deeper
    file of a directory plan (the charter row carries the archive), and
    ``(None, None)`` when the path sits outside the archive states."""
    for _state, directory in _archive_state_dirs(ctx):
        try:
            prefix = str(
                directory.resolve().relative_to(ctx.repo_root.resolve())
            )
        except ValueError:
            continue
        if not rel.startswith(prefix + "/"):
            continue
        parts = rel[len(prefix) + 1:].split("/")
        if len(parts) == 1:
            return "file", prefix
        if len(parts) == 2 and parts[1] == plan_shape.CHARTER_FILENAME:
            return "charter", prefix
        return "member", prefix
    return None, None


def _worktree_index_mismatch(ctx: GateContext, rel: str) -> Optional[str]:
    """Return a blocker note when worktree bytes differ from the staged index."""
    diff = ctx.git("diff", "--quiet", "--", rel)
    if diff.returncode == 1:
        return f"staged archive differs from worktree bytes: {rel}"
    if diff.returncode != 0:
        return (
            f"staged/worktree comparison failed for {rel}: "
            f"{diff.stderr.strip() or 'git diff failed'}"
        )
    return None


def _archive_bytes_at_index_or_worktree(
    ctx: GateContext, rel: str
) -> tuple[Optional[bytes], Optional[str]]:
    """Read exact index or worktree bytes without text-mode conversions."""
    indexed = ctx.git("ls-files", "--error-unmatch", "--", rel)
    if indexed.returncode == 0:
        mode = ctx.git("ls-files", "--stage", "--", rel)
        if mode.returncode != 0:
            return None, (
                f"staged archive mode lookup failed: {rel}: "
                f"{mode.stderr.strip() or 'git ls-files failed'}"
            )
        entries = [line.split(None, 1)[0] for line in mode.stdout.splitlines() if line]
        if not entries or any(entry not in {"100644", "100755"} for entry in entries):
            return None, f"staged archive is not a regular file: {rel}"
        show = ctx.git_bytes("show", f":{rel}")
        if show.returncode != 0:
            return None, (
                f"staged archive unreadable from index: {rel}: "
                f"{show.stderr.strip() or 'git show failed'}"
            )
        return show.stdout, None
    if indexed.returncode != 1:
        return None, (
            f"staged archive index lookup failed: {rel}: "
            f"{indexed.stderr.strip() or 'git ls-files failed'}"
        )
    path = ctx.repo_root / rel
    if path.is_symlink():
        return None, f"staged archive is not a regular file: {rel}"
    try:
        data = path.read_bytes()
    except OSError:
        return None, f"staged archive unreadable from worktree: {rel}"
    # An untracked path may have been staged while its worktree bytes were
    # being read. Prefer the new index blob if that transition occurred.
    indexed_after_read = ctx.git("ls-files", "--error-unmatch", "--", rel)
    if indexed_after_read.returncode == 0:
        mode = ctx.git("ls-files", "--stage", "--", rel)
        if mode.returncode != 0:
            return None, (
                f"staged archive mode lookup failed after worktree read: {rel}: "
                f"{mode.stderr.strip() or 'git ls-files failed'}"
            )
        entries = [line.split(None, 1)[0] for line in mode.stdout.splitlines() if line]
        if not entries or any(entry not in {"100644", "100755"} for entry in entries):
            return None, f"staged archive is not a regular file: {rel}"
        show = ctx.git_bytes("show", f":{rel}")
        if show.returncode != 0:
            return None, (
                f"staged archive unreadable from index: {rel}: "
                f"{show.stderr.strip() or 'git show failed'}"
            )
        return show.stdout, None
    if indexed_after_read.returncode != 1:
        return None, (
            f"staged archive index lookup failed after worktree read: {rel}: "
            f"{indexed_after_read.stderr.strip() or 'git ls-files failed'}"
        )
    return data, None


def _archive_bytes_from_worktree(
    ctx: GateContext, rel: str
) -> tuple[Optional[bytes], Optional[str]]:
    """Read the exact worktree representation for an addition shape."""
    path = ctx.repo_root / rel
    if path.is_symlink() or not path.is_file():
        return None, f"staged archive is not a regular file: {rel}"
    try:
        return path.read_bytes(), None
    except OSError:
        return None, f"staged archive unreadable from worktree: {rel}"


def _archive_text_from_bytes(
    data: bytes, rel: str
) -> tuple[Optional[str], Optional[str]]:
    """Decode archive text without losing the raw-byte evidence source."""
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, f"archive is not UTF-8 text: {rel}"


def _archive_text_for_derivation(
    data: bytes, rel: str, blockers: list[str]
) -> str:
    """Return text or record a bounded blocker and a safe placeholder."""
    text, error = _archive_text_from_bytes(data, rel)
    if error is not None or text is None:
        blockers.append(f"archive-ceremony: {error or f'archive text unavailable: {rel}'}")
        return "\n- [ ] archive evidence is not UTF-8\n"
    return text


def _archive_text_at_index_or_worktree(
    ctx: GateContext, rel: str
) -> tuple[Optional[str], Optional[str]]:
    """Decode archive bytes for checkbox checks, retaining the bytes source."""
    data, error = _archive_bytes_at_index_or_worktree(ctx, rel)
    if error is not None or data is None:
        return None, error
    text, decode_error = _archive_text_from_bytes(data, rel)
    if decode_error is not None:
        return None, f"staged {decode_error}"
    return text, None


def _git_blob_bytes(
    ctx: GateContext, spec: str
) -> tuple[Optional[bytes], Optional[str]]:
    """Read a blob's exact bytes, distinguishing absence from Git failure."""
    result = ctx.git_bytes("show", spec)
    if result.returncode == 0:
        return result.stdout, None
    detail = result.stderr.decode("utf-8", errors="replace").strip()
    return None, f"archive reviewed blob read failed for {spec}: {detail or 'git show failed'}"


def _committed_rename_parent_bytes(
    ctx: GateContext, base: str, old: str, new: str
) -> tuple[Optional[bytes], Optional[str]]:
    """Recover only an actual rename commit's parent blob, never a base guess."""
    commits = ctx.git("rev-list", f"{base}..HEAD")
    if commits.returncode != 0:
        return None, (
            "archive rename history lookup failed: "
            f"{commits.stderr.strip() or 'git rev-list failed'}"
        )
    for commit in commits.stdout.splitlines():
        parent = ctx.git("rev-parse", "-q", "--verify", f"{commit}^{{commit}}^")
        if parent.returncode != 0:
            return None, (
                "archive rename parent lookup failed: "
                f"{parent.stderr.strip() or 'git rev-parse failed'}"
            )
        changes = ctx.git(
            "diff-tree", "--find-renames", "--name-status", "-r",
            parent.stdout.strip(), commit, "--", _plans_pathspec(ctx),
        )
        if changes.returncode != 0:
            return None, (
                "archive rename commit lookup failed: "
                f"{changes.stderr.strip() or 'git diff-tree failed'}"
            )
        for line in changes.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) == 3 and fields[0].startswith("R"):
                if (
                    _unquote_porcelain_path(fields[1]) == old
                    and _unquote_porcelain_path(fields[2]) == new
                ):
                    return _git_blob_bytes(ctx, f"{parent.stdout.strip()}:{old}")
    return None, None


def _directory_task_texts_on_disk(
    ctx: GateContext, charter_rel: str
) -> tuple[list[str], list[str], list[str]]:
    """Read staged/worktree task files as ``(texts, notes, errors)``.

    Read errors are separate from informational notes so callers can block
    without interpreting diagnostic wording.
    """
    texts: list[str] = []
    notes: list[str] = []
    errors: list[str] = []
    tasks_dir = ctx.repo_root / Path(charter_rel).parent / plan_shape.TASKS_DIRNAME
    task_dir_rel = (Path(charter_rel).parent / plan_shape.TASKS_DIRNAME).as_posix()
    indexed = ctx.git("ls-files", "--", task_dir_rel)
    if indexed.returncode != 0:
        errors.append(
            "archive-ceremony: directory task index listing failed: "
            f"{task_dir_rel}: {indexed.stderr.strip() or 'git ls-files failed'}"
        )
    indexed_modes = ctx.git("ls-files", "--stage", "--", task_dir_rel)
    if indexed_modes.returncode != 0:
        errors.append(
            "archive-ceremony: directory task mode listing failed: "
            f"{task_dir_rel}: {indexed_modes.stderr.strip() or 'git ls-files failed'}"
        )
    elif any(
        line.partition("\t")[2] == task_dir_rel
        for line in indexed_modes.stdout.splitlines()
        if line
    ):
        errors.append(
            f"archive-ceremony: tasks path is not a directory in index: {task_dir_rel}"
        )
    if tasks_dir.is_symlink() or (tasks_dir.exists() and not tasks_dir.is_dir()):
        errors.append(
            f"archive-ceremony: tasks path is not a real directory in worktree: {task_dir_rel}"
        )
        return texts, notes, errors

    indexed_paths = {
        line.strip()
        for line in indexed.stdout.splitlines()
        if line.strip().endswith(".md")
    }
    worktree_paths = {
        task_path.relative_to(ctx.repo_root).as_posix()
        for task_path in tasks_dir.glob("*.md")
    } if tasks_dir.is_dir() else set()
    task_paths = sorted(indexed_paths | worktree_paths)
    if not task_paths:
        notes.append(
            "archive-ceremony: directory archive carries no "
            f"{plan_shape.TASKS_DIRNAME}/ directory on disk, task span "
            f"empty: {Path(charter_rel).parent}"
        )
        return texts, notes, errors
    for rel in task_paths:
        mismatch = _worktree_index_mismatch(ctx, rel)
        if mismatch is not None:
            errors.append(mismatch)
        text, error = _archive_text_at_index_or_worktree(ctx, rel)
        if error is not None:
            errors.append(f"archive-ceremony: {error}")
        elif text is not None:
            texts.append(text)
    return texts, notes, errors


def _directory_task_texts_at_head(
    ctx: GateContext, charter_rel: str
) -> tuple[list[str], list[str], list[str]]:
    """Read HEAD task files as ``(texts, notes, errors)``.

    Read errors are separate from informational notes so callers can fail the
    archive gate closed without interpreting diagnostic wording.
    """
    plan_dir = Path(charter_rel).parent.as_posix()
    listing = ctx.git("ls-tree", "-r", "HEAD", "--", plan_dir)
    if listing.returncode != 0:
        return [], [], [
            "archive-ceremony: directory task listing failed at HEAD: "
            f"{plan_dir}"
        ]
    tasks_prefix = f"{plan_dir}/{plan_shape.TASKS_DIRNAME}/"
    task_dir_rel = f"{plan_dir}/{plan_shape.TASKS_DIRNAME}"
    texts: list[str] = []
    notes: list[str] = []
    errors: list[str] = []
    for line in listing.stdout.splitlines():
        entry, separator, rel = line.partition("\t")
        mode = entry.split(None, 1)[0] if separator else ""
        if rel == task_dir_rel:
            errors.append(
                f"archive-ceremony: tasks path is not a directory at HEAD: {task_dir_rel} (mode {mode or 'unknown'})"
            )
            continue
        if not rel.startswith(tasks_prefix) or not rel.endswith(".md"):
            continue
        if mode not in {"100644", "100755"}:
            errors.append(
                "archive-ceremony: directory task file is not a regular file at HEAD: "
                f"{rel} (mode {mode or 'unknown'})"
            )
            continue
        show = ctx.git("show", f"HEAD:{rel}")
        if show.returncode != 0:
            errors.append(
                "archive-ceremony: directory task file unreadable at HEAD: "
                f"{rel}"
            )
            continue
        texts.append(show.stdout)
    return texts, notes, errors

def _commit_path_state(
    ctx: GateContext, commit: str, rel: str
) -> tuple[Optional[bool], Optional[str], Optional[str], Optional[str]]:
    """Presence, blob id, and mode of ``rel`` at ``commit``.

    Returns ``(present, blob, mode, error)``. ``present is None`` marks a
    lookup error, which callers never interpret as presence or absence; a
    confirmed absence is ``(False, None, None, None)``.
    """
    listing = ctx.git("ls-tree", commit, "--", rel)
    if listing.returncode != 0:
        return None, None, None, (
            listing.stderr.strip() or "git ls-tree failed"
        )
    rows = [line for line in listing.stdout.splitlines() if line]
    if not rows:
        return False, None, None, None
    if len(rows) > 1:
        return None, None, None, f"ambiguous path listing at {commit}: {rel}"
    entry, separator, found = rows[0].partition("\t")
    meta = entry.split()
    mode = meta[0] if meta else ""
    blob = meta[2] if len(meta) > 2 else ""
    if found != rel:
        return None, None, None, (
            f"path listing returned {found} for {rel} at {commit}"
        )
    return True, (blob or None), (mode or None), None

def _path_unchanged_since_snapshot(
    ctx: GateContext, snapshot: str, rel: str
) -> tuple[bool, Optional[str]]:
    """Whether ``rel`` carries identical presence, content, and mode at the
    configured-base snapshot and at HEAD.

    Any lookup error returns ``(False, error)`` so the candidate stays
    checked; only a confirmed match on all three excludes a raw diff row.
    """
    head_present, head_blob, head_mode, head_error = _commit_path_state(
        ctx, "HEAD", rel
    )
    if head_error is not None:
        return False, head_error
    base_present, base_blob, base_mode, base_error = _commit_path_state(
        ctx, snapshot, rel
    )
    if base_error is not None:
        return False, base_error
    if head_present != base_present:
        return False, None
    if not head_present:
        return True, None
    if head_blob != base_blob or head_mode != base_mode:
        return False, None
    return True, None

def _emit_head_archive_unit(
    ctx: GateContext,
    unit_rel: str,
    is_charter: bool,
    seen: set,
    archives: list,
    blockers: list,
    notes: list,
) -> None:
    """Surface one mapped archive unit from its HEAD bytes.

    The regular-file probe and the bytes read each fail explicitly into
    ``blockers`` (a mapped unit is never silently dropped); charter units
    carry the HEAD task span beside the charter text.
    """
    mode_error = _head_regular_archive_file(ctx, unit_rel)
    if mode_error is not None:
        blockers.append(mode_error)
        return
    show = ctx.git_bytes("show", f"HEAD:{unit_rel}")
    if show.returncode != 0:
        blockers.append(f"committed archive unreadable at HEAD: {unit_rel}")
        return
    archive_bytes = show.stdout
    text = _archive_text_for_derivation(archive_bytes, unit_rel, blockers)
    if is_charter:
        task_texts, task_notes, task_errors = _directory_task_texts_at_head(
            ctx, unit_rel
        )
        notes.extend(task_notes)
        blockers.extend(task_errors)
        text = text + "".join(task_texts)
    if unit_rel not in seen:
        seen.add(unit_rel)
        archives.append((unit_rel, text, archive_bytes, None, archive_bytes))

def _derive_archived_plans(
    ctx: GateContext,
) -> tuple[list[tuple[str, str, bytes, Optional[str], Optional[bytes]]], list[str], list[str]]:
    """Surface archive rows plus non-failing notes and blocking diagnostics.

    Each row is ``(archive path, decoded checkbox text, exact archive bytes,
    recovered pre-archive path, preferred reviewed raw bytes)``. Unreadable
    evidence and failed source queries are never silently treated as an empty
    archive set.

    Three shapes, each with its own byte source:

    (a) staged/worktree renames and additions over the plans pathspec whose
        new path sits in an archive state directory, including untracked
        additions; staged renames read the index, while additions read the
        worktree;
    (b) committed renames or additions into ``plans_completed_dir`` since this run's
        manifest boundary: a ``git diff --find-renames <base>..HEAD
        --name-status`` over the plans pathspec where ``<base>`` is the
        active run manifest's ``start_commit`` with the gate_doc_registry
        precedent's ``ORIG_HEAD`` fallback when absent; when neither
        resolves, this shape surfaces nothing this run and the skip is
        noted; archive bytes come from the HEAD blob, with a rename's
        preferred reviewed bytes recovered from the parent source blob. On
        the feature-only rebase path (the recorded start commit is not an
        ancestor of the worktree's merge base with the configured base
        branch), the diff runs with ``--no-renames`` so additions,
        modifications, and deletions are independent path candidates, and
        each raw path is compared with the configured-base snapshot
        (presence, content, and mode) before it maps to its archive unit:
        a path matching the snapshot on all three is unchanged base state
        and excluded, every lookup error retains the candidate, and a
        deleted member or whole unit is skipped only after HEAD confirms
        the source unit absent; This
        is the lib's first rename-detecting name-status diff on purpose: every
        existing name-status diff uses ``--no-renames`` because its
        consumers need per-side change-type rows, while this gate needs the
        rename pairing itself;
    (c) stale plan-deliverables lines whose recorded plan path no longer
        exists because it now sits archived; archive bytes come from the twin
        at HEAD, with no separately recoverable reviewed source bytes.
    """
    # Each row is (archive path, decoded checkbox text, exact archive bytes,
    # recovered pre-archive path, preferred raw digest bytes). The last field
    # is the source blob for renames, the archive blob for additions, and None
    # for stale deliverables twins that use the archive form.
    archives: list[tuple[str, str, bytes, Optional[str], Optional[bytes]]] = []
    notes: list[str] = []
    blockers: list[str] = []
    seen: set[str] = set()
    plans_rel = _plans_pathspec(ctx)

    # Shape (a): staged/worktree renames or additions in an archive state.
    porcelain = ctx.git("status", "--porcelain", "-uall", "--", plans_rel)
    if porcelain.returncode != 0:
        blockers.append(
            "staged archive status failed: "
            f"{porcelain.stderr.strip() or 'git status failed'}"
        )
        porcelain_rows: list[str] = []
    else:
        porcelain_rows = [
            line
            for line in porcelain.stdout.splitlines()
            if len(line) >= 4 and line[:2] != "!!"
        ]
    for row in porcelain_rows:
        xy = row[:2]
        rest = row[3:]
        is_rename = " -> " in rest and (
            xy[0] in ("R", "C") or xy[1] == "R"
        )
        is_untracked = xy == "??"
        is_add = ("A" in xy or is_untracked) and " -> " not in rest
        if not is_rename and not is_add:
            continue
        new = rest.split(" -> ", 1)[-1] if is_rename else rest
        new = _unquote_porcelain_path(new)
        kind, _prefix = _archive_unit(ctx, new)
        if kind is None:
            # A rename inside the plans home is not an archive: the gate
            # checks archives only, never an ordinary in-root rename.
            continue
        if kind == "member":
            if not is_add:
                # A renamed directory member is carried by its charter row.
                continue
            charter = (
                Path(new).parents[1] / plan_shape.CHARTER_FILENAME
            ).as_posix()
            if not is_untracked:
                mismatch = _worktree_index_mismatch(ctx, new)
                if mismatch is not None:
                    blockers.append(mismatch)
            archive_bytes, error = _archive_bytes_at_index_or_worktree(ctx, charter)
            if error is not None or archive_bytes is None:
                blockers.append(error or f"staged directory charter unreadable: {charter}")
                text = "\n- [ ] staged charter evidence unreadable\n"
                archive_bytes = text.encode("utf-8")
            else:
                text = _archive_text_for_derivation(archive_bytes, charter, blockers)
            if not is_untracked:
                mismatch = _worktree_index_mismatch(ctx, charter)
                if mismatch is not None:
                    blockers.append(mismatch)
            task_texts, task_notes, task_errors = _directory_task_texts_on_disk(ctx, charter)
            notes.extend(task_notes)
            blockers.extend(task_errors)
            text += "".join(task_texts)
            if charter not in seen:
                seen.add(charter)
                old_rel = _unquote_porcelain_path(rest.split(" -> ", 1)[0]) if is_rename else None
                reviewed = archive_bytes
                if old_rel:
                    reviewed, error = _git_blob_bytes(ctx, f"HEAD:{old_rel}")
                    if error is not None:
                        blockers.append(error)
                archives.append(
                    (charter, text, archive_bytes, old_rel, reviewed)
                )
            continue
        if not is_untracked:
            mismatch = _worktree_index_mismatch(ctx, new)
            if mismatch is not None:
                blockers.append(mismatch)
        archive_bytes, error = (
            _archive_bytes_at_index_or_worktree(ctx, new)
            if is_rename
            else _archive_bytes_from_worktree(ctx, new)
        )
        if error is not None or archive_bytes is None:
            blockers.append(f"archive-ceremony: {error or f'staged archive unreadable: {new}'}")
            text = "\n- [ ] staged archive evidence unreadable\n"
            archive_bytes = text.encode("utf-8")
        else:
            text = _archive_text_for_derivation(archive_bytes, new, blockers)
        old_rel = _unquote_porcelain_path(rest.split(" -> ", 1)[0]) if is_rename else None
        reviewed = archive_bytes
        if old_rel:
            reviewed, error = _git_blob_bytes(ctx, f"HEAD:{old_rel}")
            if error is not None:
                blockers.append(error)
        if kind == "charter":
            task_texts, task_notes, task_errors = _directory_task_texts_on_disk(ctx, new)
            notes.extend(task_notes)
            blockers.extend(task_errors)
            text = text + "".join(task_texts)
        if new not in seen:
            seen.add(new)
            archives.append((new, text, archive_bytes, old_rel, reviewed))

    # Shape (b): committed renames into the completed archive since the run
    # manifest boundary (ORIG_HEAD fallback; neither resolves: skip, noted).
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    base = manifest.start_commit if manifest is not None else "ORIG_HEAD"
    # A worktree can be rebased onto a newer configured base branch after its
    # done marker was written. In that case the manifest boundary predates
    # upstream archive commits and would misclassify them as this run's work.
    # Use the worktree's merge base only when it is a descendant of the
    # manifest boundary; on the base branch itself, keep the run boundary so
    # archives created by this run remain visible. If the manifest start is
    # a feature-only commit rewritten by rebase, ancestry alone cannot map
    # that start into the new history: keep the recorded boundary and filter
    # raw path rows against the configured-base snapshot instead of guessing
    # at provenance; only the successful ancestry result 1 selects that
    # path, and any ancestry command error retains candidates with no
    # snapshot exclusions.
    feature_only_snapshot: Optional[str] = None
    if manifest is not None:
        configured_base = facts_paths.resolve_toml_key_raw(
            ctx.repo_root, "base_branch"
        )
        branch = ctx.git("branch", "--show-current")
        if (
            isinstance(configured_base, str)
            and configured_base.strip()
            and branch.returncode == 0
            and branch.stdout.strip() != configured_base.strip()
        ):
            merge_base = ctx.git("merge-base", "HEAD", configured_base.strip())
            if merge_base.returncode == 0:
                candidate = merge_base.stdout.strip()
                starts_before = ctx.git(
                    "merge-base", "--is-ancestor", base, candidate
                )
                if starts_before.returncode == 0:
                    notes.append(
                        "archive-ceremony: using worktree base-branch merge base "
                        f"{candidate} instead of older run marker {base}"
                    )
                    base = candidate
                elif starts_before.returncode == 1:
                    feature_only_snapshot = candidate
                    notes.append(
                        "archive-ceremony: feature-only run start "
                        f"{base} is not an ancestor of the base-branch merge "
                        f"base {candidate}; filtering committed archive paths "
                        "against the configured-base snapshot"
                    )
                else:
                    notes.append(
                        "archive-ceremony: worktree base-branch ancestry check "
                        f"failed (rc {starts_before.returncode}); keeping run "
                        f"marker {base} with no snapshot filtering"
                    )
    verify = ctx.git("rev-parse", "-q", "--verify", f"{base}^{{commit}}")
    if verify.returncode != 0:
        detail = (
            "committed archive boundary does not resolve: "
            f"neither the active run manifest start_commit nor ORIG_HEAD "
            f"resolves, tried {base}"
        )
        if manifest is not None:
            blockers.append(detail)
        else:
            notes.append("archive-ceremony: " + detail)
    else:
        diff_mode = (
            ["--no-renames"]
            if feature_only_snapshot is not None
            else ["--find-renames"]
        )
        diff = ctx.git(
            "diff",
            *diff_mode,
            "--name-status",
            f"{base}..HEAD",
            "--",
            plans_rel,
        )
        state_prefixes: list[tuple[str, str]] = []
        for state, directory in _archive_state_dirs(ctx):
            try:
                prefix = str(
                    directory.resolve().relative_to(ctx.repo_root.resolve())
                )
            except ValueError:
                continue
            state_prefixes.append((state, prefix))
        if diff.returncode != 0:
            blockers.append(
                "committed archive diff failed: "
                f"{diff.stderr.strip() or 'git diff failed'}"
            )
        elif feature_only_snapshot is not None:
            # Feature-only rebase path: independent A/M/D rows with rename
            # detection disabled; each raw path is snapshot-compared before
            # it maps to its archive unit, so unchanged base state is
            # excluded while every lookup error retains the candidate.
            for line in diff.stdout.splitlines():
                fields = line.split("\t")
                if len(fields) < 2 or not fields[0]:
                    continue
                letter = fields[0]
                raw = _unquote_porcelain_path(fields[-1])
                kind, _prefix = _archive_unit(ctx, raw)
                if kind is None:
                    continue
                unchanged, lookup_error = _path_unchanged_since_snapshot(
                    ctx, feature_only_snapshot, raw
                )
                if lookup_error is not None:
                    blockers.append(
                        "archive-ceremony: configured-base snapshot lookup "
                        f"failed for {raw}: {lookup_error}"
                    )
                elif unchanged:
                    continue
                if kind == "member":
                    unit = (
                        Path(raw).parents[1] / plan_shape.CHARTER_FILENAME
                    ).as_posix()
                    is_charter = True
                else:
                    unit = raw
                    is_charter = kind == "charter"
                if letter == "D":
                    present, _blob, _mode, state_error = _commit_path_state(
                        ctx, "HEAD", unit
                    )
                    if state_error is not None:
                        blockers.append(
                            "archive-ceremony: deleted-path source-unit lookup "
                            f"failed at HEAD: {unit}: {state_error}"
                        )
                        continue
                    if not present:
                        # A deleted row is skipped only after HEAD confirmed
                        # its source unit absent.
                        continue
                _emit_head_archive_unit(
                    ctx, unit, is_charter, seen, archives, blockers, notes
                )
        elif state_prefixes:
            for line in diff.stdout.splitlines():
                fields = line.split("\t")
                if not fields or not (
                    fields[0].startswith("R")
                    or (fields[0] == "A" and len(fields) == 2)
                ):
                    continue
                old = (
                    _unquote_porcelain_path(fields[1])
                    if fields[0].startswith("R") and len(fields) == 3
                    else None
                )
                new = _unquote_porcelain_path(fields[-1])
                archive_state = next(
                    (
                        state
                        for state, prefix in state_prefixes
                        if new.startswith(prefix + "/")
                    ),
                    None,
                )
                if archive_state is None:
                    continue
                kind, _prefix = _archive_unit(ctx, new)
                if kind == "member" and fields[0] != "A":
                    # A directory plan's member row is carried by its
                    # charter row; an added member of an existing charter
                    # has no changed charter row, so surface its parent unit.
                    continue
                if kind == "member":
                    charter = (
                        Path(new).parents[1] / plan_shape.CHARTER_FILENAME
                    ).as_posix()
                    mode_error = _head_regular_archive_file(ctx, charter)
                    if mode_error is not None:
                        blockers.append(mode_error)
                        continue
                    show = ctx.git_bytes("show", f"HEAD:{charter}")
                    if show.returncode != 0:
                        blockers.append(
                            "added directory member charter unreadable at "
                            f"HEAD: {charter}"
                        )
                        member = ctx.git_bytes("show", f"HEAD:{new}")
                        if member.returncode == 0 and new not in seen:
                            seen.add(new)
                            text = _archive_text_for_derivation(member.stdout, new, blockers)
                            reviewed, error = (
                                _committed_rename_parent_bytes(ctx, base, old, new)
                                if old
                                else (member.stdout, None)
                            )
                            if error is not None:
                                blockers.append(error)
                            archives.append((new, text, member.stdout, old,
                                             reviewed))
                        elif member.returncode != 0 and new not in seen:
                            seen.add(new)
                            text = "\n- [ ] unreadable archive member evidence\n"
                            reviewed, error = (
                                _committed_rename_parent_bytes(ctx, base, old, new)
                                if old
                                else (text.encode("utf-8"), None)
                            )
                            if error is not None:
                                blockers.append(error)
                            archives.append(
                                (new, text, text.encode("utf-8"), old,
                                 reviewed)
                            )
                        continue
                    task_texts, task_notes, task_errors = _directory_task_texts_at_head(
                        ctx, charter
                    )
                    notes.extend(task_notes)
                    blockers.extend(task_errors)
                    archive_bytes = show.stdout
                    text = _archive_text_for_derivation(archive_bytes, charter, blockers) + "".join(task_texts)
                    if charter not in seen:
                        seen.add(charter)
                        reviewed, error = (
                            _committed_rename_parent_bytes(ctx, base, old, new)
                            if old
                            else (archive_bytes, None)
                        )
                        if error is not None:
                            blockers.append(error)
                        archives.append((charter, text, archive_bytes, old,
                                         reviewed))
                    continue
                mode_error = _head_regular_archive_file(ctx, new)
                if mode_error is not None:
                    blockers.append(mode_error)
                    continue
                show = ctx.git_bytes("show", f"HEAD:{new}")
                if show.returncode != 0:
                    blockers.append(
                        "committed archive unreadable at HEAD: "
                        f"{new}"
                    )
                    continue
                archive_bytes = show.stdout
                text = _archive_text_for_derivation(archive_bytes, new, blockers)
                if kind == "charter":
                    task_texts, task_notes, task_errors = _directory_task_texts_at_head(
                        ctx, new
                    )
                    notes.extend(task_notes)
                    blockers.extend(task_errors)
                    text = text + "".join(task_texts)
                if new not in seen:
                    seen.add(new)
                reviewed, error = (
                    _committed_rename_parent_bytes(ctx, base, old, new)
                    if old
                    else (archive_bytes, None)
                )
                if error is not None:
                    blockers.append(error)
                archives.append((new, text, archive_bytes, old,
                                 reviewed))

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
            blockers.append(
                "plan-deliverables file unreadable: "
                f"{deliverables_path}"
            )
            deliverables = []
        for rel in deliverables:
            if (ctx.repo_root / rel).exists():
                continue
            if _archive_state_of(ctx, rel) is not None:
                continue
            twin_rel, twin_error = _archive_twin_at_head(ctx, rel)
            if twin_error is not None:
                blockers.append(twin_error)
                continue
            if twin_rel is None:
                continue
            mode_error = _head_regular_archive_file(ctx, twin_rel)
            if mode_error is not None:
                blockers.append(mode_error)
                continue
            show = ctx.git_bytes("show", f"HEAD:{twin_rel}")
            if show.returncode != 0:
                blockers.append(
                    "archive twin unreadable at HEAD: "
                    f"{twin_rel}"
                )
                continue
            archive_bytes = show.stdout
            text = _archive_text_for_derivation(archive_bytes, twin_rel, blockers)
            if Path(twin_rel).name == plan_shape.CHARTER_FILENAME:
                # A directory twin: the checkbox leg spans the task files
                # archived beside the charter.
                task_texts, task_notes, task_errors = _directory_task_texts_at_head(
                    ctx, twin_rel
                )
                notes.extend(task_notes)
                blockers.extend(task_errors)
                text = text + "".join(task_texts)
            if twin_rel not in seen:
                seen.add(twin_rel)
                archives.append((twin_rel, text, archive_bytes, rel, None))

    return archives, notes, blockers


def _plan_slug(archive_rel: str) -> str:
    """The archived plan's slug: the file stem minus its leading date prefix
    (the slug form real review-record names use). A directory archive's
    charter re-derives from the plan directory's name (the directory
    operand's slug), never the charter's own stem."""
    path = Path(archive_rel)
    stem = path.stem
    if path.name == plan_shape.CHARTER_FILENAME:
        stem = path.parent.name
    return ARCHIVE_SLUG_DATE_PREFIX_RE.sub(
        "", stem, count=1
    )


def _find_bound_review_receipt(
    ctx: GateContext,
    archive_rel: str,
    archive_bytes: bytes,
    pre_archive_rel: str | None,
    reviewed_bytes: bytes | None,
) -> tuple[Path, str, str] | None:
    """Find a live plan-review pair bound to this single-file archive.

    Return its markdown path, matching digest, and matched byte form. Sidecar
    parsing is deliberately narrow: this archive arm consumes only the plan
    identity, source digest, and sidecar verdict, and re-validates no other
    version-1 fields. A missing or unreadable candidate declines so a later
    matching pair can still authorize the archive.
    """
    archive_path = ctx.repo_root / archive_rel
    archive_kind, _state_prefix = _archive_unit(ctx, archive_rel)
    if archive_path.is_dir() or archive_kind == "charter":
        return None
    if not isinstance(archive_bytes, bytes):
        return None
    expected_identity = pre_archive_rel or archive_rel
    expected_identity = posixpath.normpath(expected_identity)
    if reviewed_bytes is None or pre_archive_rel is None:
        expected_bytes = archive_bytes
        digest_form = "archived-bytes"
    elif isinstance(reviewed_bytes, bytes):
        expected_bytes = reviewed_bytes
        digest_form = "reviewed-revision"
    else:
        return None
    expected_digest = vrs.compute_source_digest("plan", expected_bytes)

    if not ctx.reviews_dir.is_dir():
        return None
    candidates = sorted(
        ctx.reviews_dir.rglob("*.md"), key=lambda path: path.as_posix()
    )
    for record in candidates:
        if not record.is_file():
            continue
        if "-plan-review-" not in record.name:
            continue
        if not vrs.is_staging_review_path(record):
            continue
        if BACKUP_INFIX in record.name or ORPHAN_INFIX in record.name:
            continue
        sidecar = vrs.stats_sidecar_path(record)
        if not sidecar.is_file():
            continue
        if BACKUP_INFIX in sidecar.name or ORPHAN_INFIX in sidecar.name:
            continue
        try:
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue

        extensions = payload.get("extensions")
        identity = extensions.get("plan_identity") if isinstance(extensions, dict) else None
        if not isinstance(identity, str):
            continue
        if posixpath.normpath(identity) != expected_identity:
            continue
        if payload.get("source_digest") != expected_digest:
            continue
        if plan_readiness.sidecar_verdict(payload) != "yes":
            continue
        return record, expected_digest, digest_form
    return None


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
    """Landing gate over the plan archives this run's boundary surfaces.

    For every archive the derivation (``_derive_archived_plans``) surfaces,
    the gate checks checkbox completeness: plan bytes still carrying a
    ``- [ ]`` unchecked task box fail with the two sanctioned exits (check
    the boxes after verified work, or land a marked backfill completion
    record per the plans skill's archive-correction exception). A box-complete
    archive must carry either an exec-review filename-series record or a live
    plan-review receipt whose sidecar binds the plan identity, raw-byte digest,
    and yes verdict (the ``archived-plan review-coverage`` check). A
    rejected-state archive (the archive-state derivation's ``rejected`` state, the
    ``plans/rejected/`` placement of a plan the operator declined) is exempt
    from both demands: its unchecked boxes and absent execution evidence are
    the disposition, not defects, and the exemption lives in this executable
    owner so a rejected plan is never certified as executed by the ceremony
    that refuses it."""
    gate = "archive-ceremony"
    archives, notes, blockers = _derive_archived_plans(ctx)
    if blockers:
        return GateResult(
            gate,
            1,
            "archive-ceremony gate failed: " + "; ".join(blockers),
            warnings=notes,
        )
    if not archives:
        message = "archive-ceremony gate passed: no plan archive surfaced this run"
        if notes:
            message += " (" + "; ".join(notes) + ")"
        return GateResult(gate, 0, message, warnings=notes)
    findings: list[str] = []
    exempted: list[str] = []
    accepted_receipts: list[tuple[str, Path, str, str, str | None]] = []
    for archive_rel, text, archive_bytes, pre_archive_rel, reviewed_bytes in archives:
        if _archive_state_of(ctx, archive_rel) == "rejected":
            exempted.append(archive_rel)
            continue
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
        # carry either the filename-series execution review or a digest-bound
        # plan-review receipt; absence of both fails with the reconstruction
        # remedy (the cited-review-receipt-integrity
        # precedent: a marked reconstruction is valid, a silent one is not).
        slug = _plan_slug(archive_rel)
        if _has_exec_review_record(ctx, slug):
            continue
        bound = _find_bound_review_receipt(
            ctx,
            archive_rel,
            archive_bytes,
            pre_archive_rel,
            reviewed_bytes,
        )
        if bound is not None:
            record, matched_digest, digest_form = bound
            archive_digest = vrs.compute_source_digest("plan", archive_bytes)
            divergence = None
            if matched_digest != archive_digest:
                divergence = archive_digest
            accepted_receipts.append(
                (archive_rel, record, matched_digest, digest_form, divergence)
            )
            continue
        findings.append(
            f"archived plan {archive_rel} has no exec-review record "
            f"(no *-plan-review-{slug}-exec-r<N> file under the reviews "
            "home names the missing series); remedy: produce the "
            "exec-review record for the plan's final bytes, use the "
            "bound-receipt acceptance with a live identity-, raw-byte-"
            "digest-, and verdict-bound plan-review record, or land a "
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
    for exempt_rel in exempted:
        notes = notes + [
            "rejected-state archive exempt from the unchecked-box and "
            "execution-evidence demands (the plan's rejected disposition "
            "stands; never certified as executed): " + exempt_rel
        ]
    checked = [row[0] for row in archives if row[0] not in exempted]
    message_parts: list[str] = []
    if checked:
        message_parts.append(
            f"{len(checked)} plan archive(s) checked, boxes complete: "
            + ", ".join(checked)
        )
    if exempted:
        message_parts.append(
            f"{len(exempted)} rejected-state archive(s) exempt: "
            + ", ".join(exempted)
        )
    message_parts.append(f"bound-receipt acceptance: {len(accepted_receipts)}")
    warnings = list(notes)
    for archive_rel, record, digest, digest_form, archive_digest in accepted_receipts:
        warning = (
            f"bound-receipt acceptance: {len(accepted_receipts)}; "
            f"{archive_rel} accepted by "
            f"{_sanitize_manifest_error_value(record.name, truncate=False)}; "
            f"matched {digest_form} digest {digest}"
        )
        if archive_digest is not None:
            warning += (
                f"; divergence: archive digest {archive_digest}, matched "
                f"digest {digest}; amendment is unreviewed"
            )
        warnings.append(warning)
    message = "archive-ceremony gate passed: " + "; ".join(message_parts)
    return GateResult(gate, 0, message, warnings=warnings)


# --------------------------------------------------------------------------- #
# Gate: execute-plan-closeout (a landing sweep gate; plan 2026-10-01-execute-plan-
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


def _closeout_pre_receipt_defect(receipt: object) -> Optional[str]:
    """The first well-formedness defect of one ``pre_archive_receipt``
    candidate as a naming of the offending field, or None when it is
    well-formed: the declared archive pathset (``declared_paths``, a
    non-empty list of non-empty path strings), a string plan digest, the
    Phase 2 and Phase 3 evidence pointers (``evidence``, a non-empty list
    of non-empty strings), and a recorded-at timestamp string. The archived
    destination is declared when the run knows it and is deliberately not a
    well-formedness demand: the receipt is written before the archive
    commit, and the landed-complete arm verifies the recorded destination
    and digest against the commit tree."""
    if not isinstance(receipt, dict):
        return "pre_archive_receipt must be a JSON object"
    paths = receipt.get("declared_paths")
    if not isinstance(paths, list) or not paths:
        return (
            "declared_paths (the declared archive pathset) must be a "
            "non-empty list"
        )
    if any(not isinstance(path, str) or not path.strip() for path in paths):
        return "declared_paths entries must be non-empty path strings"
    digest = receipt.get("plan_digest")
    if not isinstance(digest, str) or not digest.strip():
        return "plan_digest must be a non-empty string"
    evidence = receipt.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return (
            "evidence (the Phase 2 and Phase 3 evidence pointers) must be "
            "a non-empty list"
        )
    if any(
        not isinstance(pointer, str) or not pointer.strip()
        for pointer in evidence
    ):
        return "evidence entries must be non-empty pointer strings"
    recorded_at = receipt.get("recorded_at")
    if not isinstance(recorded_at, str) or not recorded_at.strip():
        return "recorded_at must be a timestamp string"
    return None


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
    None when (a) the archived bytes re-hash to the receipt digest in the
    working tree AND in the commit tree (HEAD names the recorded
    destination and its committed bytes re-hash to the digest: the archive
    is a landed commit, never working-tree residue the receipt claims
    landed), (b) the
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
    # (a, commit tree) The recorded destination must be committed and its
    # committed bytes must re-hash to the recorded digest (the blob is read
    # with a binary capture: the bytes must bypass text decoding before
    # hashing).
    archived_rel = _repo_relative(str(archived_path), ctx.repo_root)
    tree = ctx.git("ls-tree", "HEAD", "--", archived_rel)
    if tree.returncode != 0 or not tree.stdout.strip():
        return (
            1,
            refuse(
                "the terminal receipt's archived destination "
                f"{archived_rel} is absent from the commit tree (no HEAD "
                "entry); the archive commit must land before the terminal "
                "receipt"
            ),
        )
    blob = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "cat-file",
            "blob",
            f"HEAD:{archived_rel}",
        ],
        cwd=str(ctx.repo_root),
        capture_output=True,
        timeout=GIT_TIMEOUT_S,
    )
    committed = (
        hashlib.sha256(blob.stdout).hexdigest()
        if blob.returncode == 0
        else None
    )
    if committed != digest:
        detail = (
            f"re-hash to {committed}"
            if committed is not None
            else "could not be read from HEAD"
        )
        return (
            1,
            refuse(
                "terminal receipt digest mismatch in the commit tree: the "
                f"committed bytes of {archived_rel} at HEAD {detail} but "
                f"the receipt records {digest}"
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
    """Landing gate: the execute-plan lifecycle net at the landing
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
    - bounded pre-archive arm (plan docs/history/plans/2026-10-15-execute-
      plan-closeout-cycle-and-filed-records.md): every task done with a
      well-formed ``pre_archive_receipt`` (declared archive pathset, string
      plan digest, evidence pointers, recorded-at timestamp) passes with
      one note naming the receipt and the declared archive destination;
      declared-set equality stays with the staged-scope guard.
    - landed-without-evidence refusal (the witnessed shape): no
      ``terminal_receipt`` and no ``pre_archive_receipt`` while every task
      is done under the runtime's own done predicate refuses
      unconditionally, wherever the plan bytes sit (still active, archived
      twin, or already gone); a run paused between the last task and
      Phase 4 refuses the same way on purpose, because the closeout must
      not report completion before a receipt exists. A present-but-
      malformed ``pre_archive_receipt`` refuses naming the offending field
      with the same remedy (fail-closed over a receipt the run wrote
      malformed).
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
                f"{slug} landed complete; receipt digest in the working "
                "tree and the commit tree, active-path absence, "
                "promoted-origin closure, and registry row verified"
            )
        elif _closeout_all_tasks_done(payload):
            pre_receipt = payload.get("pre_archive_receipt")
            if pre_receipt is None:
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
            defect = _closeout_pre_receipt_defect(pre_receipt)
            if defect is not None:
                return GateResult(
                    gate,
                    1,
                    "execute-plan-closeout gate failed: execute-plan session "
                    f"{slug}: the pre_archive_receipt is malformed "
                    f"({defect}); " + CLOSEOUT_RESUME_REMEDY,
                    warnings=[],
                )
            destination = pre_receipt.get("archived_plan_path")
            destination_text = (
                f"the declared archive destination {destination}"
                if isinstance(destination, str) and destination.strip()
                else "no archived destination recorded"
            )
            passes.append(
                f"{slug} all tasks done; the run's well-formed "
                "pre_archive_receipt (recorded_at "
                f"{pre_receipt.get('recorded_at')!r}) admits the bounded "
                f"pre-archive arm: {destination_text} (declared-set "
                "equality stays with the staged-scope guard)"
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
    "plans-root-claim-fence": gate_plans_root_claim_fence,
    "archive-ceremony": gate_archive_ceremony,
    "execute-plan-closeout": gate_execute_plan_closeout,
    "plans-archive-twin": gate_plans_archive_twin,
}


def run_gate(gate_id: str, ctx: GateContext) -> GateResult:
    if gate_id not in GATES:
        raise ValueError(f"unknown gate id: {gate_id}")
    return GATES[gate_id](ctx)


def run_phase(
    phase: str, ctx: GateContext, boundary_class: str = "final-closeout"
) -> list[GateResult]:
    """Run one phase's gates strictly sequentially in registry order (see the
    module docstring's execution contract). A gate helper that raises is
    captured as an indeterminate gate result naming the failed gate (outcome
    contract exit 2: the gate could not answer, so its evidence is neither a
    pass nor a modeled violation); the run continues so every gate still
    reports."""
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase}")
    if boundary_class not in BOUNDARY_CLASSES:
        raise ValueError(
            f"invalid boundary class: {boundary_class} (expected one of "
            f"{', '.join(BOUNDARY_CLASSES)})"
        )
    roster = PHASES[phase]
    if phase == "landing" and boundary_class == "per-task":
        roster = PER_TASK_LANDING_GATES
    results: list[GateResult] = []
    for gate_id in roster:
        try:
            result = run_gate(gate_id, ctx)
            if phase == "landing" and gate_id in LANDING_WARNING_GATES and result.rc == 1:
                result.rc = 0
                result.warnings.append(
                    f"warning posture: {gate_id} reports but does not "
                    "block (landing roster)"
                )
            results.append(result)
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
        "<landing|list-gates|write-manifest|finalize-manifest|"
        "disposition-manifest|recover-manifest|checkpoint-manifest|"
        "classify-run-boundary|list-interrupted-manifests>\n"
        "phases: landing (the closeout's one landing sweep run: the "
        "retained roster with instruction-size and description-length in "
        "warning posture; backlog-inbox and vim-swap-sweep are not on the "
        "roster - receiving-review capture step and the periodic survey "
        "advisory own their duties)\n"
        "list-gates [phase] prints that phase's roster one gate per line "
        "with warning-posture gates suffixed \" (warning)\"\n"
        "write-manifest writes the done Step 0 run manifest record "
        "(run-manifest-<run_id>.json under the done-session directory), "
        "reporting interrupted runs (complete=false, never finalized; "
        "continued only via an explicit --adopt boundary copy; a worktree "
        "copy of a run's boundary reports as a shadow-of <run_id> line "
        "bound to its run, never a second boundary); "
        "--run-marker <path> binds the manifest to that named run-start "
        "marker (fail-closed refusals when it is absent, outside the "
        "done-session directory, unconfirmable, or no longer the newest "
        "content-confirmed marker; without the flag the newest-anchor "
        "binding applies); "
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
        "reprints its record with a zero exit; --manifest-file FILENAME "
        "dispositions one bare run-manifest-*.json copy under the "
        "done-session directory (a worktree shadow copy) whose payload "
        "run_id must equal --run-id: a mismatching, non-bare, non-glob, "
        "complete, adopted, or live-rooted copy refuses named with no "
        "mutation, the deliverables witness resolves the copy's own owned "
        "paths, and the stamp lands on that copy only, canonical record "
        "untouched)\n"
        "recover-manifest verifies an interrupted run manifest's landed "
        "work against the live repository (the deliverables witness plus "
        "owned-commits reachability from HEAD) and stamps the shared "
        "dispositioned record with reason work-verified-landed-live-"
        "recovery (--run-id required, --note optional; a dead root refuses "
        "naming disposition-manifest, an already-complete or adopted "
        "boundary refuses, the witness and reachability checks refuse "
        "naming the failed evidence; an already-dispositioned manifest "
        "reprints its record with a zero exit)\n"
        "checkpoint-manifest owns the resumable-closeout checkpoint, the "
        "per-run sibling JSON run-checkpoint-<run_id>.json beside the "
        "manifest (--run-id and --mode required; --session required "
        "non-empty for create and refresh and recorded verbatim, optional "
        "for verify where an omitted session skips the session-identity "
        "comparison; --gates is the comma-separated green-gate set recorded "
        "at write time): --mode create writes the checkpoint at the "
        "finalizer-span entry, --mode refresh updates the recorded manifest "
        "sha256 and gate set in place at the Step 6 finalize preamble, "
        "--mode verify re-checks the recorded identity and the recomputed "
        "manifest sha256 (the resume continuation's mechanical gate), and "
        "--mode remove deletes the sibling only after a successful finalize "
        "set complete true; every refusal is a named one-line non-zero "
        "error that mutates nothing\n"
        "classify-run-boundary prints the canonical boundary verdict for a "
        "manifest file at its run identity (--session-dir and --manifest "
        "required; verdict: and run_id: lines naming terminal "
        "(finalized, adopted, dispositioned), shadow-closed, orphan, or "
        "unreadable); read-only, the setup shell classifier's owner\n"
        "list-interrupted-manifests prints one line per interrupted run "
        "manifest (root_matches_current_repo=yes|no, lock=held|free|unknown, "
        "dispositioned, adopted, created) plus one guidance line when a "
        "record matches this checkout's root: a matching root is a "
        "repository identity fact, not liveness, and done-lock.sh status "
        "is the liveness check; a worktree copy of a run's boundary renders "
        "as shadow-of <run_id> naming its filename, never an independent "
        "boundary, and a record whose run closed through another file "
        "renders as closed-run history; read-only, never mutates\n"
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


def _run_marker_binding_refusal(
    done_session_dir: Path,
    repo_root: Path,
    requested: str,
    window: SessionWindow,
) -> Optional[str]:
    """Refusal line when ``write-manifest --run-marker`` cannot bind the
    manifest to the named marker, else None (the named marker binds).

    Check order is fail-closed cheapest-first: an absent path, a path
    outside the done-session directory, content failing the two-form
    confirmation (a 64-hex digest record compares against the freshly
    recomputed repo-root digest, a legacy raw-path record against the
    resolved path - the same arms ``_parse_marker`` applies to the window),
    then the newest-marker binding. Every refusal is one line; the caller
    writes no manifest on any refusal."""
    marker = Path(requested)
    if not marker.exists():
        return (
            "write-manifest: run-marker-absent: "
            f"{requested} does not exist; write the run-start marker "
            "before the manifest"
        )
    session_real = os.path.realpath(str(done_session_dir))
    marker_real = os.path.realpath(requested)
    if marker_real != session_real and not marker_real.startswith(
        session_real + os.sep
    ):
        return (
            "write-manifest: run-marker-outside-done-session: "
            f"{requested} sits outside the done-session directory "
            f"{done_session_dir}; the manifest binds only to a marker "
            "under it"
        )
    if _parse_marker(marker, repo_root) is None:
        return (
            "write-manifest: run-marker-unconfirmed: "
            f"{marker.name} content does not confirm this repository's "
            "root (neither a 64-hex digest record matching the recomputed "
            "repo-root digest nor a legacy raw-path record resolving to "
            "the same path); refusing to bind"
        )
    if (
        window.current is None
        or os.path.realpath(str(window.current.path)) != marker_real
    ):
        newest = window.current.path.name if window.current is not None else "none"
        return (
            "write-manifest: run-marker-not-newest: "
            f"{marker.name} is not the newest content-confirmed run-start "
            f"marker under {done_session_dir} (newest: {newest}); refusing "
            "to bind a stale marker"
        )
    return None


def _cmd_write_manifest(argv: list[str]) -> int:
    """Write the done Step 0 run manifest record.

    Derives run_id, the run-start marker, the HEAD start commit, the
    porcelain dirt snapshot, and the repo root itself, then enforces
    claim-or-foreign over the staging candidates on disk (predicate matched,
    NOT window filtered: Step 0 is the enumeration universe). Any uncovered
    candidate aborts with a named error and no manifest. Prints the manifest
    path plus run_id (the run's audit record).

    Marker binding: without ``--run-marker`` the manifest binds to the newest
    content-confirmed marker under the done-session directory (today's
    newest-anchor binding). With ``--run-marker <path>`` the manifest binds
    to that named marker instead, fail-closed: a named one-line refusal and
    no manifest written when the path is absent, sits outside the
    done-session directory, carries content that does not confirm this
    repository's root under the two-form confirmation, or is no longer the
    newest content-confirmed marker (a cross-shell continuation must never
    silently rebind a fresh manifest to a previous run's marker).

    Interrupted-run reporting: every root-matched manifest whose ``complete``
    flag is still false and which no other manifest adopts is reported as an
    interrupted run (a finalized manifest is never an orphan). The report
    reads at run identity: a terminal record on any file of a run (a shadow
    copy included) closes the whole boundary, and a worktree shadow copy (a
    ``run-manifest-*.json`` file whose payload run id equals the run's but
    whose filename is not the canonical name) renders as a ``shadow-of
    <run_id>`` line naming its own filename, never as an independent
    boundary. Without
    ``--adopt`` the new manifest keeps the new run's own HEAD boundary;
    adoption is explicit only: ``--adopt <run_id>`` copies the interrupted
    run's boundary (start_commit plus owned paths, foreign markings included)
    verbatim and records ``adopted_from``, and the adopted link suppresses the
    orphan report for later runs. The report doubles as a demoted warning
    (closeout-gate demotion program change 3): when an orphan remains that
    this invocation neither adopted nor recognized as closed, the write
    prints ``write-manifest: undisposed-interrupted (reported, not
    failing):`` listing each remaining manifest filename with the remedies
    its root state supports (a live root: ``recover-manifest``,
    ``--adopt``, or ``finalize-manifest``; a dead root:
    ``disposition-manifest`` only) and continues - the witnessed incident
    behind the former refusal was a live linked-worktree peer manifest
    misread as a dead root - so an interrupted boundary is still classified
    in the output before any new manifest (the emit-only arm included),
    never refused.

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
    parser.add_argument(
        "--run-marker", default=None, metavar="PATH",
        help="bind the manifest to this run-start marker PATH explicitly "
        "(the composed Step 0 block passes the marker it just wrote); "
        "named one-line refusals when the path is absent, sits outside "
        "the done-session directory, does not confirm this repo's root "
        "under the two-form confirmation, or is no longer the newest "
        "content-confirmed marker; omitting the flag keeps the "
        "newest-anchor binding",
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
    # Marker binding: --run-marker binds to the named marker fail-closed
    # (refusal classes in _run_marker_binding_refusal); the flag absent keeps
    # today's newest-anchor binding.
    if args.run_marker is not None:
        refusal = _run_marker_binding_refusal(
            ctx.done_session_dir, ctx.repo_root, args.run_marker, window
        )
        if refusal is not None:
            return _cli_fail(refusal)
        marker_name = Path(args.run_marker).name
    else:
        if window.current is None:
            if args.emit_foreign_candidates is None:
                return _cli_fail(
                    "write-manifest: no content-confirmed run-start marker under "
                    f"{ctx.done_session_dir}; write the marker before the manifest"
                )
            # Zero-marker emit-only shape (plan 2026-10-16-done-emit-
            # prelock-classification): the emit arm is read-only over
            # done-session state - it writes only the caller-named file and
            # never a manifest - so the marker's content-confirmation is
            # not engaged here; the classification runs pre-lock instead of
            # through the partial-setup receipt path. Only the zero-marker
            # shape relaxes; any confirmable marker keeps the newest-anchor
            # binding below, and every manifest-writing invocation keeps
            # this refusal byte-identical.
            marker_name = None
        else:
            marker_name = window.current.path.name
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
        canonical_name = _manifest_path(ctx.done_session_dir, orphan.run_id).name
        if orphan.source_name != canonical_name:
            # A worktree shadow copy binds to its run's one boundary: the
            # copy renders as a bound line naming its own filename, never
            # as a second independent boundary.
            print(
                "interrupted run: shadow-of "
                f"{orphan.run_id} {orphan.source_name} (a worktree copy "
                f"of the canonical boundary {canonical_name}, not an "
                "independent boundary)"
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
            "boundary, or recover-manifest --run-id "
            f"{orphan.run_id} to verify the landed work and close it"
        )
    for line in corrupt_warnings:
        # F10: a corrupt record in the done-session dir is reported, never
        # silently skipped (an undead run leaves a trace).
        print(line)

    # Undisposed-interrupted classification (plan 2026-10-01-done-boundary-
    # receipt-and-closeout-gate-sweep Task 3; posture demoted by the
    # closeout-gate demotion program change 3 below): the report above stays
    # advisory and so does the bounded decision - the former refusal's
    # liveness rationale (the done lock exclusive per checkout) is the
    # assumption the witnessed incident falsified, since separate worktrees
    # hold separate checkout locks. An orphan this invocation neither
    # adopted nor recognized as closed (dispositioned records never reach
    # the orphan set) draws the warning, and the warning sits before the
    # emit-foreign-candidates arm, so an emit-only invocation still sees
    # the classification in its output first.
    remaining = [
        orphan
        for orphan in orphans
        if adopted is None or orphan.run_id != adopted.run_id
    ]
    if remaining:
        # One entry per run: a shadow copy binds to its canonical record's
        # entry (or, for a copy-only run, renders as its own shadow-of
        # label), never a second independent boundary entry.
        by_run: dict[str, RunManifest] = {}
        for orphan in remaining:
            canonical_name = _manifest_path(
                ctx.done_session_dir, orphan.run_id
            ).name
            current = by_run.get(orphan.run_id)
            if current is None or (
                current.source_name != canonical_name
                and orphan.source_name == canonical_name
            ):
                by_run[orphan.run_id] = orphan
        entries: list[str] = []
        for run_id in sorted(by_run):
            orphan = by_run[run_id]
            canonical_name = _manifest_path(ctx.done_session_dir, run_id).name
            if orphan.source_name == canonical_name:
                label = canonical_name
            else:
                label = f"shadow-of {run_id} {orphan.source_name}"
            if not _manifest_root_matches(orphan.repo_root, ctx.repo_root):
                entries.append(
                    f"{label}: disposition-manifest --run-id "
                    f"{run_id} only (the recorded repo_root matches "
                    "no checkout here, so adoption refuses this boundary)"
                )
            else:
                entries.append(
                    f"{label}: recover-manifest --run-id "
                    f"{run_id} to verify-and-close it, "
                    f"--adopt {run_id} to continue it, or "
                    f"finalize-manifest --run-id {run_id} to close "
                    "it (disposition-manifest refuses live roots)"
                )
        # Demotion split (closeout-gate demotion program change 3, D-7;
        # carrier row 2026-10-08-done-closeout-ceremony-friction): the
        # ledger entry reads 0 catches / 1 incident - the former refusal
        # misclassified a live linked-worktree peer manifest as a dead
        # root and blocked a valid closeout for 20 witnessed minutes - so
        # the bounded-decision demand prints as a warning and the write
        # continues. The remedies stay in the line; adoption and
        # disposition stay explicit operator choices.
        print(
            "write-manifest: undisposed-interrupted (reported, not "
            "failing): " + "; ".join(entries),
            file=sys.stderr,
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
            f"({len(remaining)} path(s), sorted); enumerated under repo "
            f"root {ctx.repo_root}; no manifest written; "
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
    if uncovered and not args.claim_none:
        auto_foreign, uncovered = _foreign_by_default_split(
            ctx, uncovered, owned_review_paths
        )
        if auto_foreign:
            foreign_review_paths = _dedup_preserving_order(
                foreign_review_paths + auto_foreign
            )
            print(
                "write-manifest: foreign-by-default: "
                f"{len(auto_foreign)} gitignored historical staging "
                "candidate(s) under the primary checkout's reviews home "
                "classified foreign (shared run-artifact home; origin row "
                "landing commit b3025de59)"
            )
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
        marker=marker_name,
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
            f"owned_plan_paths entry {plan_path} resolves through none of "
            "the witness arms (its recorded path on disk, HEAD:<recorded "
            "path>, its plans_completed archive twin at HEAD, note-backed)"
        )
    for review_path in manifest.owned_review_paths:
        if ctx.git("cat-file", "-e", f"docs:{review_path}").returncode == 0:
            continue
        return (
            f"owned_review_paths entry {review_path} does not resolve on "
            "the docs branch (the owned-review set's single witness arm)"
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
        return (
            f"owned_paths entry {owned_path} resolves through none of the "
            "witness arms (HEAD:<path>, its plans_completed archive twin at "
            "HEAD, a landed deletion reachable from HEAD, note-backed)"
        )
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


def _vacuous_deliverables_note(operator_note: Optional[str]) -> str:
    """The named note the deliverables witness records when the manifest
    owns no deliverables at all (all three owned sets empty): the witness
    is vacuously true, and the operator's ``--note`` rides along when
    present. Shared by the disposition and recovery commands so the stamped
    note text cannot drift between them."""
    note = (
        "no-deliverables: the manifest owns no deliverables "
        "(owned_plan_paths, owned_review_paths, owned_paths all empty); "
        "the deliverables witness is vacuously true"
    )
    if operator_note:
        note = f"{note}; operator note: {operator_note}"
    return note


def _recover_first_unreachable_commit(
    done_session_dir: Path, run_id: str, ctx: GateContext
) -> Optional[str]:
    """The recovery operation's owned-commits reachability witness: every
    entry of the run's own ledger (``owned-commits-<run_id>.txt``, the
    per-commit ownership record the done skill appends at Step 1 and Step 3)
    must resolve as a commit and be reachable from HEAD, the landing
    destination this verification closes against. An absent ledger is an
    empty one (the run recorded no commits; the witness passes vacuously,
    the same stance the gate-side ledger reader takes). A ledger that exists
    but cannot be read refuses fail-closed (it is not proof of an empty
    record). Returns None when every entry is reachable, else a one-line
    message naming the first entry that failed."""
    ledger = _owned_commits_ledger_path(done_session_dir, run_id)
    try:
        lines = ledger.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    except OSError as exc:
        return (
            f"owned-commits ledger {ledger.name} unreadable "
            f"({' '.join(str(exc).split())})"
        )
    for entry in (line.strip() for line in lines):
        if not entry:
            continue
        resolved = ctx.git("rev-parse", "-q", "--verify", f"{entry}^{{commit}}")
        if resolved.returncode != 0:
            return (
                f"owned-commits ledger entry {entry} does not resolve as a "
                "commit reachable from HEAD"
            )
        sha = resolved.stdout.strip()
        ancestor = ctx.git("merge-base", "--is-ancestor", sha, "HEAD")
        if ancestor.returncode == 1:
            return (
                f"owned-commits ledger entry {sha} is not reachable from "
                "HEAD (the commit exists but is not an ancestor of the "
                "landing destination)"
            )
        if ancestor.returncode != 0:
            return (
                f"owned-commits ledger entry {sha} reachability "
                "unverifiable (merge-base failed: "
                f"{' '.join(ancestor.stderr.split())[:120]})"
            )
    return None


def _recover_unlanded_deliverables(
    manifest: RunManifest, ctx: GateContext
) -> list[tuple[str, str, str]]:
    """The recovery-side landing discrimination over the owned deliverables
    (``owned_plan_paths`` and ``owned_paths``; an owned review's single arm
    is the docs branch, so it is landed or the witness already refused).
    Every entry is classified by the witness arm actually used, and only a
    HEAD-landed arm counts as landed: ``head`` resolves the entry at
    ``HEAD:<path>``, at its ``plans_completed`` archive twin at HEAD, or -
    for owned paths - through a landed deletion reachable from HEAD;
    ``disk-only`` means only the on-disk recorded path resolves (an
    uncommitted worktree file); ``note-backed only`` means no arm but a
    note would save it. Returns one ``(label, path, kind)`` tuple per
    unlanded entry; an empty list means every owned deliverable resolves
    through a HEAD-landed arm. Mirrors ``_disposition_first_missing_
    deliverable``'s per-set arms exactly, plus the on-disk classification
    the disposition witness applies to plans implicitly (the on-disk arm is
    a saving resolution there; here it is the unlanded shape)."""
    unlanded: list[tuple[str, str, str]] = []
    for plan_path in manifest.owned_plan_paths:
        if ctx.git("cat-file", "-e", f"HEAD:{plan_path}").returncode == 0:
            continue
        twin = ctx.plans_completed_dir / Path(plan_path).name
        twin_rel = _repo_relative(str(twin), ctx.repo_root)
        if ctx.git("cat-file", "-e", f"HEAD:{twin_rel}").returncode == 0:
            continue
        if (ctx.repo_root / plan_path).is_file():
            unlanded.append(
                (f"owned_plan_paths entry {plan_path}", plan_path, "disk-only")
            )
        else:
            unlanded.append(
                (
                    f"owned_plan_paths entry {plan_path}",
                    plan_path,
                    "note-backed only",
                )
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
        landed = False
        if under_plans_tree or under_completed_tree:
            twin = ctx.plans_completed_dir / Path(owned_path).name
            twin_rel = _repo_relative(str(twin), ctx.repo_root)
            if ctx.git("cat-file", "-e", f"HEAD:{twin_rel}").returncode == 0:
                landed = True
        if not landed:
            # The landed-deletion arm, the disposition witness's stance: a
            # never-tracked path exits 0 with EMPTY %H output, so resolve
            # only when BOTH the exit is 0 and the commit hash is non-empty.
            deletion = ctx.git(
                "log", "--diff-filter=D", "--format=%H", "-n", "1", "--", owned_path
            )
            if deletion.returncode == 0 and deletion.stdout.strip():
                landed = True
        if landed:
            continue
        if (ctx.repo_root / owned_path).is_file():
            unlanded.append(
                (f"owned_paths entry {owned_path}", owned_path, "disk-only")
            )
        else:
            unlanded.append(
                (
                    f"owned_paths entry {owned_path}",
                    owned_path,
                    "note-backed only",
                )
            )
    return unlanded


def _stamp_disposition_record_with_cas(
    ctx: GateContext,
    manifest: RunManifest,
    record: dict,
    command_name: str,
    receipt_verb: str,
    stamp_path: Optional[Path] = None,
) -> int:
    """Stamp the prepared ``dispositioned`` record onto ``manifest`` and
    write it through the shared stamp-time compare-and-swap, then print the
    success receipt. ``command_name`` prefixes the refusal lines of the
    calling sub-command; ``receipt_verb`` is the success line's verb
    (``dispositioned`` for the dead-root command, ``recovered`` for the
    live-root command). ``stamp_path`` is the targeted stamp path: None (the
    canonical arm) re-reads and rewrites the canonical
    ``run-manifest-<run_id>.json`` through ``_read_manifest_by_run_id`` and
    ``write_run_manifest`` as before, while a path (the copy disposition
    arm's ``--manifest-file``) re-reads and rewrites THAT file through the
    same tolerant parse contract and the same atomic update shape, so the
    stamp lands on the named copy only and the canonical record stays
    byte-identical.

    Two fresh reads narrow the check-then-write window so a finalize, a
    competing disposition or recovery, or an adoption landing between the
    pre-checks and the stamp cannot blur the record. (a) This manifest's
    payload re-read fresh from disk (through the reader's parse contract:
    ``_read_manifest_by_run_id`` on the canonical arm, the same tolerant
    parse over ``stamp_path`` on the copy arm):
    absent, unreadable, and schema-mismatched fresh payloads refuse
    fail-closed (post-check state loss), ``complete`` true refuses
    (post-check finalize), and a ``dispositioned`` record that landed after
    the pre-checks degrades to the idempotent reprint of the racer's record
    (other field drift does not block the stamp). (b) A fresh
    ``_manifest_adopted_by_another`` directory re-scan refuses on
    post-check adoption (adoption writes ``adopted_from`` on the ADOPTER's
    manifest, invisible to a payload-only re-read)."""
    manifest.dispositioned = record
    if stamp_path is None:
        fresh = _read_manifest_by_run_id(ctx.done_session_dir, manifest.run_id)
    else:
        try:
            fresh = RunManifest.from_dict(
                json.loads(stamp_path.read_text(encoding="utf-8"))
            )
        except (OSError, ValueError):
            fresh = None
    if fresh is None:
        return _cli_fail(
            f"{command_name}: refusing {manifest.run_id}: the manifest "
            "payload is absent, unreadable, or schema-mismatched at the "
            "stamp (post-check state loss); refusing to stamp over an "
            "unknown state"
        )
    if fresh.complete:
        return _cli_fail(
            f"{command_name}: refusing {manifest.run_id}: the run "
            "finalized between the pre-checks and the stamp (post-check "
            "finalize); a finalized run is never an interrupted run"
        )
    racer = fresh.dispositioned
    if racer is not None:
        # A concurrent disposition or recovery won the race: print the
        # EXISTING record (the racer's date/note, not this call's) and
        # exit 0, the same idempotent path as a pre-existing stamp.
        racer_date = (
            racer.get("date") if isinstance(racer.get("date"), str) else ""
        )
        print(
            f"{command_name}: a dispositioned record landed after the "
            "pre-checks (a concurrent disposition won the race); printing "
            "the existing record"
        )
        print(
            f"dispositioned: {manifest.run_id} ({racer_date}) "
            "(already dispositioned)"
        )
        print(json.dumps(racer, sort_keys=True))
        return 0
    if _manifest_adopted_by_another(ctx.done_session_dir, manifest.run_id):
        return _cli_fail(
            f"{command_name}: refusing {manifest.run_id}: another "
            "manifest adopted this boundary between the pre-checks and the "
            "stamp (post-check adoption); adoption owns the continuation"
        )
    try:
        if stamp_path is None:
            path = write_run_manifest(manifest, ctx.done_session_dir)
        else:
            path = _write_run_manifest_file(stamp_path, manifest)
    except OSError as exc:
        return _cli_fail(
            f"{command_name}: cannot rewrite the run manifest: {exc}"
        )
    print(f"{receipt_verb}: {manifest.run_id} ({record['date']}) written to {path}")
    return 0


def _cmd_disposition_manifest(argv: list[str]) -> int:
    """Stamp the one-time ``dispositioned`` record onto an unadoptable
    interrupted run manifest (an interrupted run whose recorded ``repo_root``
    names a checkout that no longer exists, so the adoption boundary and the
    finalize identity check refuse it forever). Refusals, each a named
    one-line error with no mutation: an absent manifest; ``complete`` already
    true; an ``adopted_from`` link naming the run (another manifest adopted
    this boundary); a recorded root matching the current repository through
    either arm of ``_repo_root_matches_value`` (a live root is
    recovery/resume territory; the refusal names the recover, adopt, and
    finalize exits). A
    ``dispositioned`` record already present is the idempotent arm: the
    existing record is printed and the exit is 0, never a refusal, so a
    re-run after the deliverable vanished cannot un-close the run. On
    success the deliverables witness resolves every owned deliverable by set
    (naming the first missing one on refusal; three empty owned sets print
    and stamp a named no-deliverables note - the witness is vacuously true).

    The ``--manifest-file <filename>`` arm binds the whole operation to one
    named file under the done-session directory instead of the canonical
    ``run-manifest-<run_id>.json`` name: a worktree shadow copy (a bare
    ``run-manifest-*.json`` filename whose payload run_id equals
    ``--run-id``) is read, checked, and stamped on that copy only, through
    the same deliverables witness resolved against the copy's own payload and
    the same compare-and-swap stamp with a targeted stamp path, leaving the
    canonical record byte-identical. The name must be bare and inside the
    ``run-manifest-*.json`` session glob (a traversing or nested name, or any
    name outside the glob, refuses with no mutation), and the copy's payload
    run_id must equal ``--run-id`` (a mismatch refuses named, so a copy can
    never be closed through a mismatched canonical record); the copy then
    walks the canonical refusal set unchanged, with the idempotent reprint
    arm for an already-stamped copy.

    Immediately before the write the shared ``_stamp_disposition_record_with_cas``
    compare-and-swap re-checks with two fresh reads: (a) this manifest's
    payload re-read from disk through the reader's parse contract
    (``_read_manifest_by_run_id`` on the canonical arm, the same tolerant
    parse over the named copy file on the copy arm), refusing fail-closed when the
    re-read returns None (absent, unreadable, or schema-mismatched; post-check
    state loss), refusing when
    ``complete`` is now true (post-check finalize), and degrading to the
    idempotent reprint of the racer's record when a ``dispositioned`` record
    landed after the pre-checks (other field drift does not block the
    stamp); (b) a fresh ``_manifest_adopted_by_another`` directory re-scan,
    refusing on post-check adoption (adoption writes ``adopted_from`` on the
    ADOPTER's manifest, invisible to a payload-only re-read). Only then is
    ``dispositioned: {reason: "work-verified-landed", date, note}`` stamped
    through the writer's atomic manifest-update path. The live-root
    ``recover-manifest`` sub-command reuses the same witness helper, record
    shape, and stamp CAS unchanged, with its own reason literal."""
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
        "--manifest-file", default=None, metavar="FILENAME",
        help="disposition one bare run-manifest-*.json copy under the "
        "done-session directory (a worktree shadow copy) instead of the "
        "canonical run-manifest-<run_id>.json name; its payload run_id "
        "must equal --run-id (a mismatch refuses named, no mutation), the "
        "deliverables witness resolves the copy's own owned paths, and the "
        "stamp lands on that copy only, canonical record untouched",
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
    # The --manifest-file arm binds the operation to one named session file
    # (a worktree shadow copy): bare, glob-matching, run-id-matched payload.
    stamp_path: Optional[Path] = None
    if args.manifest_file is not None:
        name = args.manifest_file
        if not name or Path(name).name != name:
            return _cli_fail(
                f"disposition-manifest: refusing {name!r}: not a bare "
                "filename under the done-session directory (a traversing "
                "or nested name is never a manifest copy)"
            )
        if re.fullmatch(r"run-manifest-.*\.json", name) is None:
            return _cli_fail(
                f"disposition-manifest: refusing {name!r}: outside the "
                "run-manifest-*.json session glob (a manifest copy names "
                "a run-manifest-*.json file)"
            )
        stamp_path = ctx.done_session_dir / name
        try:
            copy_payload = json.loads(stamp_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            copy_payload = None
        manifest = RunManifest.from_dict(copy_payload)
        if manifest is None:
            return _cli_fail(
                f"disposition-manifest: no run manifest found at {name} "
                f"under {ctx.done_session_dir}"
            )
        if manifest.run_id != args.run_id:
            return _cli_fail(
                f"disposition-manifest: refusing {name}: its payload "
                f"run_id {manifest.run_id} differs from --run-id "
                f"{args.run_id}; a manifest copy closes only through its "
                "own run's id, never through a mismatched record"
            )
    else:
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
            f"(write-manifest --adopt {manifest.run_id}), with "
            f"finalize-manifest --run-id {manifest.run_id}, or by verifying "
            f"and closing it with recover-manifest --run-id "
            f"{manifest.run_id}, never disposition"
        )
    date_str = datetime.now(timezone.utc).date().isoformat()
    if (
        not manifest.owned_plan_paths
        and not manifest.owned_review_paths
        and not manifest.owned_paths
    ):
        note = _vacuous_deliverables_note(args.note)
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
    return _stamp_disposition_record_with_cas(
        ctx,
        manifest,
        {"reason": "work-verified-landed", "date": date_str, "note": note},
        command_name="disposition-manifest",
        receipt_verb="dispositioned",
        stamp_path=stamp_path,
    )


RECOVERY_REASON = "work-verified-landed-live-recovery"


def _cmd_recover_manifest(argv: list[str]) -> int:
    """Verify an interrupted run manifest's landed work against THIS live
    repository and stamp the one-time ``dispositioned`` record (the
    live-root sibling of ``disposition-manifest``, which owns the dead-root
    arm and refuses a live root by contract). The recorded ``repo_root``
    must match the current repository through either arm of
    ``_repo_root_matches_value`` (a 64-hex digest record compares against
    the recomputed root digest, a legacy raw-path record by resolved path;
    either arm per record); a recorded root matching no checkout is the
    dead-root arm and the refusal directs to ``disposition-manifest``.
    Refusals, each a named one-line error with no mutation (the manifest
    stays byte-identical and still interrupted): an absent manifest;
    ``complete`` already true; an ``adopted_from`` link naming the run
    (another manifest adopted this boundary); a dead root; a deliverables
    witness failure; an owned-commits reachability failure; the
    landing-discrimination conjunct (``_recover_unlanded_deliverables``):
    an owned deliverable that resolves only through the on-disk recorded
    path (an uncommitted worktree file) or only through a note, while the
    run's owned-commits ledger is absent (the reachability witness's
    vacuous-pass shape, so nothing witnesses the work as landed), refuses
    listing the unlanded deliverables - the remedy is landing the work
    first, or an explicit ``--note`` carrying the literal marker
    ``note-backed`` plus each unlanded path (the operator-attested
    note-backed escape; a record-keeping note merely mentioning a path
    never flips the refusal into a stamp). A ``dispositioned`` record
    already present is the idempotent arm: the existing record is printed
    and the exit is 0, never a refusal, so a second identical invocation
    reprints and never re-verifies.
    BEFORE any write the command verifies (a) the deliverables witness,
    reusing ``disposition-manifest``'s set-specific resolution arms per set
    unchanged (an owned plan passes at its recorded path, at
    ``HEAD:<recorded path>``, at its completed-archive twin at HEAD, or
    note-backed; an owned review resolves on the docs branch; an owned path
    passes at ``HEAD:<path>``, its completed twin, through a landed deletion
    reachable from HEAD, or note-backed; all three sets empty passes
    vacuously with the named note), then the landing discrimination over
    the same deliverables (only a HEAD-landed arm counts when the ledger
    cannot corroborate), and (b) owned-commits reachability of
    every entry of the run's own ledger from HEAD, the landing destination
    (``_recover_first_unreachable_commit``). Only then is
    ``dispositioned: {reason: "work-verified-landed-live-recovery", date,
    note}`` stamped through the same ``_stamp_disposition_record_with_cas``
    compare-and-swap ``disposition-manifest`` uses (the payload re-read
    through the reader's parse contract and a fresh adoption re-scan
    immediately before the write, refusing post-check finalize and
    post-check adoption so a concurrent Step 6 finalize or competing
    closure cannot be overwritten) and a ``recovered:`` receipt line is
    printed. ``--note`` records the operator note inside the stamped record
    (the note-backed escape)."""
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py recover-manifest",
        description=(
            "Verify an interrupted run manifest's landed work against the "
            "live repository and stamp the one-time disposition record."
        ),
    )
    parser.add_argument(
        "--run-id", required=True, metavar="RUN_ID",
        help="the run_id recorded when Step 0 wrote the manifest",
    )
    parser.add_argument(
        "--note", default=None, metavar="TEXT",
        help="optional operator note recorded inside the dispositioned "
        "record (the note-backed escape)",
    )
    args = parser.parse_args(argv)

    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    ctx = GateContext.discover(Path(root) if root else None)

    if not args.run_id or Path(args.run_id).name != args.run_id:
        return _cli_fail(
            f"recover-manifest: refusing {args.run_id!r}: not a bare "
            "run_id filename"
        )
    # The root-agnostic reader: the live-root match is this command's own
    # explicit precondition below, not the loader's filter.
    manifest = _read_manifest_by_run_id(ctx.done_session_dir, args.run_id)
    if manifest is None:
        return _cli_fail(
            "recover-manifest: no run manifest found for run_id "
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
            f"recover-manifest: refusing {manifest.run_id}: the run "
            "already finalized (complete=true); a finalized run is never an "
            "interrupted run"
        )
    if _manifest_adopted_by_another(ctx.done_session_dir, manifest.run_id):
        return _cli_fail(
            f"recover-manifest: refusing {manifest.run_id}: another "
            "manifest adopts this boundary (an adopted_from link names it); "
            "adoption owns the continuation"
        )
    if not _repo_root_matches_value(manifest.repo_root, ctx.repo_root):
        return _cli_fail(
            f"recover-manifest: refusing {manifest.run_id}: the recorded "
            "repo_root matches no checkout here (a dead root); this "
            "command verifies against the live repository only, so close "
            f"it with disposition-manifest --run-id {manifest.run_id} "
            "instead"
        )
    date_str = datetime.now(timezone.utc).date().isoformat()
    if (
        not manifest.owned_plan_paths
        and not manifest.owned_review_paths
        and not manifest.owned_paths
    ):
        note = _vacuous_deliverables_note(args.note)
        print(f"recover-manifest: {note}")
    else:
        missing = _disposition_first_missing_deliverable(
            manifest, ctx, note=args.note
        )
        if missing is not None:
            return _cli_fail(
                f"recover-manifest: refusing {manifest.run_id}: "
                f"deliverables witness failed: {missing}"
            )
        note = args.note or ""
        # Landing discrimination: a deliverable the witness saved only
        # through the on-disk recorded path (an uncommitted worktree file)
        # or only through a note is not HEAD-landed, and an absent
        # owned-commits ledger makes the reachability witness below pass
        # vacuously, so together they close an unlanded boundary. The
        # operator-explicit escape is a --note carrying the literal marker
        # "note-backed" plus each unlanded path; a record-keeping note that
        # merely mentions a path never flips this refusal into a stamp.
        unlanded = _recover_unlanded_deliverables(manifest, ctx)
        ledger_path = _owned_commits_ledger_path(
            ctx.done_session_dir, manifest.run_id
        )
        ledger_present = ledger_path.is_file() and ledger_path.read_text(
            encoding="utf-8", errors="replace"
        ).strip() != ""
        if unlanded and not ledger_present:
            note_backed_escape = (
                "note-backed" in note
                and all(path in note for _label, path, _kind in unlanded)
            )
            if not note_backed_escape:
                listing = "; ".join(
                    f"{label} ({kind})" for label, _path, kind in unlanded
                )
                return _cli_fail(
                    f"recover-manifest: refusing {manifest.run_id}: "
                    "unlanded deliverables with no owned-commits ledger: "
                    f"{listing}; the absent ledger makes the reachability "
                    "witness pass vacuously, so nothing witnesses this "
                    "work as landed; land the work first, or close with "
                    "an explicit --note carrying the literal marker "
                    "'note-backed' plus each unlanded path (the "
                    "operator-attested note-backed escape)"
                )
    unreachable = _recover_first_unreachable_commit(
        ctx.done_session_dir, manifest.run_id, ctx
    )
    if unreachable is not None:
        return _cli_fail(
            f"recover-manifest: refusing {manifest.run_id}: "
            f"owned-commits reachability failed: {unreachable}"
        )
    return _stamp_disposition_record_with_cas(
        ctx,
        manifest,
        {"reason": RECOVERY_REASON, "date": date_str, "note": note},
        command_name="recover-manifest",
        receipt_verb="recovered",
    )


CHECKPOINT_KIND = "resumable-closeout-checkpoint"
CHECKPOINT_SCHEMA_VERSION = 1


def _checkpoint_path(done_session_dir: Path, run_id: str) -> Path:
    """The per-run sibling JSON beside the manifest; the filename derives
    from the run_id, so one run's orphaned checkpoint cannot collide with a
    later run's create."""
    return done_session_dir / f"run-checkpoint-{run_id}.json"


def _checkpoint_manifest_sha256(path: Path) -> Optional[str]:
    """The recomputed sha256 hex digest of the manifest file's bytes; None
    when the file cannot be read (fail-closed: an unreadable manifest never
    verifies)."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _read_checkpoint_payload(
    done_session_dir: Path, run_id: str
) -> Optional[dict]:
    """Raw parse of the sibling checkpoint payload: the JSON dict when the
    file exists and parses, else None (absent, unreadable, or not a JSON
    object). Schema, kind, and run_id validation stay with the caller so a
    mismatched record can be refused by name instead of read as absent."""
    if not run_id or Path(run_id).name != run_id:
        return None
    path = _checkpoint_path(done_session_dir, run_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _checkpoint_record_is_wellformed(payload: dict, run_id: str) -> bool:
    """Shape gate over a raw checkpoint payload: the operation's own schema
    version and kind, and this run's run_id. A payload failing it is not a
    checkpoint this operation wrote (manual checkpoint editing is
    unsupported), so consumers refuse instead of trusting it."""
    return (
        payload.get("schema") == CHECKPOINT_SCHEMA_VERSION
        and payload.get("kind") == CHECKPOINT_KIND
        and payload.get("run_id") == run_id
    )


def _write_checkpoint_payload(done_session_dir: Path, payload: dict) -> Path:
    """Serialize the checkpoint record and atomically replace the final file
    (same-directory temp file plus replace, the manifest writer's durability
    shape: a reader observes either the absent or the complete checkpoint,
    never a partial one)."""
    done_session_dir.mkdir(parents=True, exist_ok=True)
    final = _checkpoint_path(done_session_dir, payload["run_id"])
    tmp = done_session_dir / (final.name + ".tmp")
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, final)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return final


def _cmd_checkpoint_manifest(argv: list[str]) -> int:
    """Write, refresh, verify, and remove the resumable-closeout checkpoint
    (the done closeout's finalizer-span record; re-aimed 2026-10-11 to this
    operation's own usage text when the done target-state flip dissolved the
    skill module homes): the
    per-run sibling JSON ``run-checkpoint-<run_id>.json`` beside the run
    manifest, owned by this operation (manual checkpoint editing is
    unsupported). The record names the run_id, the manifest path, the session
    identity (recorded verbatim from ``--session``), the manifest's sha256 at
    write time, the green-gate list from ``--gates`` (a comma list, recorded
    at write time), and the created epoch.

    Modes, each refusal a named one-line non-zero error that mutates nothing
    (the checkpoint and the manifest stay byte-identical after every
    refusal):
    - ``create`` (Step 0 finalizer-span entry): ``--session`` required
      non-empty; refuses when the checkpoint already exists (naming
      ``refresh`` - one run's checkpoint is refreshed, never duplicated),
      when the run manifest is absent (the checkpoint records the manifest's
      sha256, so the manifest must exist), or when the manifest is already
      ``complete`` (symmetric with ``refresh``: a finalized run never
      creates a checkpoint; the message names ``finalize-manifest`` and
      ``--mode remove`` as the exits).
    - ``refresh`` (Step 6 finalize preamble): ``--session`` required
      non-empty; updates the recorded manifest sha256 and gate set in place
      (same filename, never a second copy) and re-records the session
      identity; refuses when no checkpoint is present (naming ``create``),
      when the run manifest is absent, when the manifest is already
      ``complete`` (a finalized run never refreshes a checkpoint), or when
      the present checkpoint is not this operation's well-formed record.
    - ``verify`` (the resume continuation's mechanical gate): the identity
      match plus the recomputed manifest sha256 match; ``--session`` is
      optional - an omitted session skips the session-identity comparison, a
      present one is compared against the recorded identity. Refuses when the
      checkpoint is absent or not well-formed, when the manifest is absent,
      unreadable, or schema-mismatched (unverifiable), when any identity
      field mismatches (run_id, manifest path, session), or when the
      manifest's recomputed sha256 differs from the recorded one (stale;
      the refusal names the recomputed digest).
    - ``remove`` (after the successful finalize): deletes the sibling;
      refuses when the run manifest is absent (naming ``finalize-manifest``
      as the prerequisite) or while ``complete`` is false, so a failed
      finalize leaves the checkpoint present for the resume continuation; a
      ``complete`` manifest with no sibling present is the idempotent arm
      (already removed or never created; a noted zero exit).
    """
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py checkpoint-manifest",
        description=(
            "Create, refresh, verify, or remove the resumable-closeout "
            "checkpoint sibling beside the run manifest."
        ),
    )
    parser.add_argument(
        "--run-id", required=True, metavar="RUN_ID",
        help="the run_id recorded when Step 0 wrote the manifest",
    )
    parser.add_argument(
        "--mode", required=True,
        choices=["create", "refresh", "verify", "remove"],
        help="create at the finalizer-span entry, refresh at the finalize "
        "preamble, verify at resume, remove after the successful finalize",
    )
    parser.add_argument(
        "--session", default=None, metavar="IDENTITY",
        help="the session identity recorded verbatim (required non-empty "
        "for create and refresh; optional for verify, where an omitted "
        "session skips the session-identity comparison)",
    )
    parser.add_argument(
        "--gates", default="", metavar="COMMA_LIST",
        help="comma-separated green-gate set recorded at write time",
    )
    args = parser.parse_args(argv)

    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    ctx = GateContext.discover(Path(root) if root else None)

    if not args.run_id or Path(args.run_id).name != args.run_id:
        return _cli_fail(
            f"checkpoint-manifest: refusing {args.run_id!r}: not a bare "
            "run_id filename"
        )
    if args.mode in ("create", "refresh") and (
        not args.session or not args.session.strip()
    ):
        return _cli_fail(
            f"checkpoint-manifest: refusing {args.run_id}: "
            f"--mode {args.mode} requires a non-empty --session identity "
            "(the checkpoint records it verbatim)"
        )
    gates = _dedup_preserving_order(
        [item.strip() for item in args.gates.split(",") if item.strip()]
    )
    manifest_path = _manifest_path(ctx.done_session_dir, args.run_id)
    checkpoint_path = _checkpoint_path(ctx.done_session_dir, args.run_id)
    # create/refresh record the manifest's sha256, so the manifest must be
    # present and parseable before either writes (a named refusal otherwise,
    # no mutation); verify and remove consult it below.
    manifest = _read_manifest_by_run_id(ctx.done_session_dir, args.run_id)

    if args.mode == "create":
        if manifest is None:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: no run "
                f"manifest found for run_id {args.run_id} under "
                f"{ctx.done_session_dir}; the checkpoint records the "
                "manifest's sha256, so the manifest must exist first"
            )
        if manifest.complete:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the run "
                "already finalized (complete=true); a finalized run never "
                "creates a resumable-closeout checkpoint (finalize-manifest "
                f"already closed this boundary; remove a leftover checkpoint "
                f"with checkpoint-manifest --mode remove --run-id "
                f"{args.run_id})"
            )
        if checkpoint_path.exists():
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the "
                f"checkpoint already exists at {checkpoint_path}; "
                "refresh it instead of creating a second copy "
                f"(checkpoint-manifest --mode refresh --run-id {args.run_id})"
            )
        sha = _checkpoint_manifest_sha256(manifest_path)
        if sha is None:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the run "
                f"manifest at {manifest_path} cannot be read; refusing to "
                "record an unknown sha256"
            )
        payload = {
            "schema": CHECKPOINT_SCHEMA_VERSION,
            "kind": CHECKPOINT_KIND,
            "run_id": args.run_id,
            "manifest_path": manifest_path.name,
            "session": args.session,
            "manifest_sha256": sha,
            "gates_green": gates,
            "created_epoch": time.time(),
        }
        try:
            written = _write_checkpoint_payload(ctx.done_session_dir, payload)
        except OSError as exc:
            return _cli_fail(
                f"checkpoint-manifest: cannot write the checkpoint: {exc}"
            )
        print(
            f"created: checkpoint-manifest run {args.run_id} at {written} "
            f"(manifest sha256 {sha}, gates green: {len(gates)})"
        )
        return 0

    if args.mode == "refresh":
        if manifest is None:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: no run "
                f"manifest found for run_id {args.run_id} under "
                f"{ctx.done_session_dir}; the checkpoint records the "
                "manifest's sha256, so the manifest must exist first"
            )
        if manifest.complete:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the run "
                "already finalized (complete=true); a finalized run never "
                "refreshes a checkpoint"
            )
        existing = _read_checkpoint_payload(ctx.done_session_dir, args.run_id)
        if existing is None:
            unparseable = checkpoint_path.is_file()
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: "
                + (
                    "the file at "
                    f"{checkpoint_path} exists but is unreadable or not a "
                    "JSON object; manual checkpoint editing is unsupported"
                )
                if unparseable
                else (
                    "no "
                    f"checkpoint present at {checkpoint_path}; create it "
                    f"first (checkpoint-manifest --mode create --run-id "
                    f"{args.run_id})"
                )
            )
        if not _checkpoint_record_is_wellformed(existing, args.run_id):
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the file at "
                f"{checkpoint_path} is not this operation's well-formed "
                "checkpoint record (wrong schema, kind, or run_id; manual "
                "checkpoint editing is unsupported)"
            )
        sha = _checkpoint_manifest_sha256(manifest_path)
        if sha is None:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the run "
                f"manifest at {manifest_path} cannot be read; refusing to "
                "record an unknown sha256"
            )
        existing["session"] = args.session
        existing["manifest_sha256"] = sha
        existing["gates_green"] = gates
        existing["refreshed_epoch"] = time.time()
        try:
            written = _write_checkpoint_payload(ctx.done_session_dir, existing)
        except OSError as exc:
            return _cli_fail(
                f"checkpoint-manifest: cannot write the checkpoint: {exc}"
            )
        print(
            f"refreshed: checkpoint-manifest run {args.run_id} at {written} "
            f"(manifest sha256 {sha}, gates green: {len(gates)})"
        )
        return 0

    if args.mode == "verify":
        payload = _read_checkpoint_payload(ctx.done_session_dir, args.run_id)
        if payload is None:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: no readable "
                f"checkpoint present at {checkpoint_path}; nothing to "
                "verify (create it first with checkpoint-manifest --mode "
                f"create --run-id {args.run_id})"
            )
        # Identity first, named per field: a payload whose recorded run_id
        # differs from the requested run_id (a renamed or hand-edited
        # record) is a run_id mismatch, not a generic shape failure.
        payload_run_id = payload.get("run_id")
        if payload_run_id != args.run_id:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: run_id "
                "mismatch: the checkpoint records "
                f"{_sanitize_manifest_error_value(payload_run_id)!r} but "
                f"{args.run_id!r} was requested"
            )
        if not _checkpoint_record_is_wellformed(payload, args.run_id):
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the file at "
                f"{checkpoint_path} is not this operation's well-formed "
                "checkpoint record (wrong schema, kind, or run_id; manual "
                "checkpoint editing is unsupported)"
            )
        if manifest is None:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: the run "
                f"manifest {manifest_path.name} is absent, unreadable, or "
                f"schema-mismatched under {ctx.done_session_dir}; the "
                "checkpoint cannot be verified (unverifiable)"
            )
        recorded_path = payload.get("manifest_path")
        if recorded_path != manifest_path.name:
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: identity "
                "mismatch: the checkpoint records manifest path "
                f"{recorded_path!r} but this run's manifest is "
                f"{manifest_path.name!r}"
            )
        if args.session is not None:
            recorded_session = payload.get("session")
            if not isinstance(recorded_session, str) or not hmac.compare_digest(
                recorded_session.encode("utf-8"), args.session.encode("utf-8")
            ):
                return _cli_fail(
                    f"checkpoint-manifest: refusing {args.run_id}: session "
                    "identity mismatch: the checkpoint records "
                    f"{_sanitize_manifest_error_value(recorded_session)!r} "
                    f"but {_sanitize_manifest_error_value(args.session)!r} "
                    "was presented"
                )
        recomputed = _checkpoint_manifest_sha256(manifest_path)
        recorded_sha = payload.get("manifest_sha256")
        if (
            not isinstance(recorded_sha, str)
            or recomputed is None
            or not hmac.compare_digest(
                recorded_sha.encode("utf-8"), recomputed.encode("utf-8")
            )
        ):
            return _cli_fail(
                f"checkpoint-manifest: refusing {args.run_id}: checkpoint "
                "stale: the manifest's recomputed sha256 "
                f"{recomputed} differs from the recorded "
                f"{_sanitize_manifest_error_value(recorded_sha)} "
                "(the manifest changed after the checkpoint was written; "
                "refresh the checkpoint)"
            )
        session_note = (
            "; session matches"
            if args.session is not None
            else "; session comparison skipped"
        )
        print(
            f"verified: checkpoint-manifest run {args.run_id} at "
            f"{checkpoint_path} (manifest sha256 {recomputed} matches"
            f"{session_note})"
        )
        return 0

    # args.mode == "remove": a successful finalize is the only thing that
    # may remove the checkpoint.
    if manifest is None:
        return _cli_fail(
            f"checkpoint-manifest: refusing {args.run_id}: no run manifest "
            f"found for run_id {args.run_id} under {ctx.done_session_dir}; "
            f"finalize-manifest --run-id {args.run_id} must set "
            "complete=true before the checkpoint can be removed"
        )
    if not manifest.complete:
        return _cli_fail(
            f"checkpoint-manifest: refusing {args.run_id}: the run manifest "
            "is not complete (complete=false); a successful "
            f"finalize-manifest --run-id {args.run_id} must set "
            "complete=true before the checkpoint can be removed"
        )
    if not checkpoint_path.exists():
        print(
            f"checkpoint-manifest: no checkpoint present for run "
            f"{args.run_id} at {checkpoint_path} (already removed or never "
            "created); nothing to remove"
        )
        return 0
    try:
        checkpoint_path.unlink()
    except OSError as exc:
        return _cli_fail(
            f"checkpoint-manifest: cannot remove the checkpoint: {exc}"
        )
    print(
        f"removed: checkpoint-manifest run {args.run_id} ({checkpoint_path})"
    )
    return 0


def _cmd_classify_run_boundary(argv: list[str]) -> int:
    """Print the canonical boundary verdict for one manifest file (read-only,
    never mutates): ``verdict: <verdict>`` plus ``run_id: <run_id>`` lines,
    classified at run identity through ``classify_run_boundary`` (terminal
    ``finalized``/``adopted``/``dispositioned``, ``shadow-closed``,
    ``orphan``, ``unreadable``). This is the subcommand the setup shell
    classifier consumes, so no manifest state predicate is re-implemented in
    bash; exit 0 always carries a verdict, a missing manifest file is the
    outcome contract's tool error."""
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py classify-run-boundary",
        description=(
            "Classify the run boundary at the named manifest file's run "
            "identity (read-only; the verdict names terminal "
            "(finalized, adopted, dispositioned), shadow-closed, orphan, "
            "or unreadable)."
        ),
    )
    parser.add_argument(
        "--session-dir", required=True, help="the done-session directory"
    )
    parser.add_argument(
        "--manifest", required=True, help="the manifest file to classify"
    )
    args = parser.parse_args(argv)
    manifest = Path(args.manifest)
    if not manifest.is_file():
        print(
            f"classify-run-boundary: no manifest file at {manifest}",
            file=sys.stderr,
        )
        print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
        return 3
    verdict, run_id = classify_run_boundary(Path(args.session_dir), manifest)
    print(f"verdict: {verdict}")
    print(f"run_id: {run_id or ''}")
    return 0


_DONE_LOCK_META_FILE = "meta.env"
# The lock script's crash-leftover default: a meta-less lock directory is a
# crash leftover once its age reaches this many seconds
# (DONE_LOCK_INCOMPLETE_SECS in scripts/done-lock.sh, default 5).
_DONE_LOCK_INCOMPLETE_SECS_DEFAULT = 5


def _done_lock_root() -> Path:
    """The done-lock root the lock script derives: ``DONE_LOCK_ROOT`` when
    set, else ``~/.ai-playbook/locks/done``."""
    override = os.environ.get("DONE_LOCK_ROOT")
    return Path(override) if override else Path.home() / ".ai-playbook" / "locks" / "done"


def _done_lock_incomplete_secs() -> float:
    """The crash-leftover incomplete age, honoring the lock script's
    ``DONE_LOCK_INCOMPLETE_SECS`` override with the same default; a blank or
    non-numeric override reads as the default (the lock script would fail
    its own arithmetic on one)."""
    raw = os.environ.get("DONE_LOCK_INCOMPLETE_SECS", "")
    if re.fullmatch(r"[0-9]+", raw.strip()):
        return float(raw)
    return float(_DONE_LOCK_INCOMPLETE_SECS_DEFAULT)


def _process_alive(pid: int) -> bool:
    """The lock script's process-table witness (``ps -p <pid> -o lstart=``):
    a pid with no process-table line is verifiably dead; any failure to
    consult the table keeps the holder not verifiably dead (the caller
    holds, never reporting free on missing evidence)."""
    try:
        proc = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    return bool(proc.stdout.strip())


def _done_lock_meta_holder_pid(lock_dir: Path) -> Optional[int]:
    """The recorded ``holder_pid`` from the lock directory's ``meta.env``
    (the lock script's own meta record, read with its anchored first-match
    rule), or None when the record is unreadable or carries no numeric pid;
    a None return means the hold is never verifiably dead."""
    try:
        text = (lock_dir / _DONE_LOCK_META_FILE).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        if line.startswith("holder_pid="):
            raw = line[len("holder_pid="):].strip()
            return int(raw) if re.fullmatch(r"[0-9]+", raw) else None
    return None


def _done_lock_state(recorded_root: object) -> str:
    """The ``lock=`` column value for one manifest record, derived READ-ONLY
    from the checkout-keyed done-lock directory (no lock script invocation,
    no mutation): ``held`` when the lock directory carries holder metadata
    that is not verifiably dead - a meta-less directory younger than the
    crash-leftover incomplete age is an in-flight acquire (the acquire
    classifier's own held arm), and a present-meta hold whose recorded
    holder is alive, ambiguous, or unreadable stays held; ``free`` when the
    directory is absent, when it is a meta-less crash leftover past the
    lock script's incomplete-age rule, or when the recorded holder pid is
    verified dead in the process table; ``unknown`` for a non-fingerprint
    root (a legacy raw-path record maps to no lock key) or an unreadable
    lock root. A fingerprint root maps to ``<done-lock root>/<first 16
    hex chars>``, the same derivation the lock script keys (sha256 of the
    checkout root truncated to 16 hex), honoring the ``DONE_LOCK_ROOT``
    override.

    Documented divergence: for a meta-less lock directory the lock script's
    status prints its raw held line regardless of age, while this column
    applies the lock script's own crash-leftover incomplete-age rule and
    reports free past it; the column never claims agreement with that raw
    line, and ``done-lock.sh status`` stays the liveness check of record."""
    if not isinstance(recorded_root, str) or not re.fullmatch(
        r"[0-9a-f]{64}", recorded_root
    ):
        return "unknown"
    lock_dir = _done_lock_root() / recorded_root[:16]
    try:
        lock_stat = os.stat(lock_dir)
    except FileNotFoundError:
        return "free"
    except OSError:
        return "unknown"
    if not stat_module.S_ISDIR(lock_stat.st_mode):
        # The lock script's status reads a non-directory at the keyed path
        # as free; the column mirrors that arm.
        return "free"
    try:
        meta_stat = os.stat(lock_dir / _DONE_LOCK_META_FILE)
    except FileNotFoundError:
        meta_present = False
    except OSError:
        return "unknown"
    else:
        meta_present = stat_module.S_ISREG(meta_stat.st_mode)
    if not meta_present:
        # Crash-leftover rule (scripts/done-lock.sh): a meta-less lock
        # directory past the incomplete age is a crash leftover, never a
        # live hold; younger than that it is an in-flight acquire.
        incomplete = _done_lock_incomplete_secs()
        return "free" if (time.time() - lock_stat.st_mtime) >= incomplete else "held"
    holder_pid = _done_lock_meta_holder_pid(lock_dir)
    if holder_pid is not None and not _process_alive(holder_pid):
        # Verified-dead holder: the same predicate that lets the lock
        # script reclaim the hold (release-orphaned) lets this column
        # report free.
        return "free"
    return "held"


def _cmd_list_interrupted_manifests(argv: list[str]) -> int:
    """Print one line per detected interrupted manifest (read-only, never
    mutates): ``<run_id> root_matches_current_repo=<yes|no>
    lock=<held|free|unknown> dispositioned=<yes|no> adopted=<yes|no>
    created=<iso date>``, plus one guidance line when at least one listed
    record matches this checkout's root. The identity column is a
    repository identity fact through both arms of
    ``_repo_root_matches_value`` (a 64-hex digest compares against the
    current digest, any other value by realpath); the retired liveness
    word never renders for a root match. The guidance line states that a
    matching root is a repository identity fact and names
    ``done-lock.sh status`` the liveness check of record. The ``lock``
    column is derived read-only from the checkout-keyed done-lock
    directory through ``_done_lock_state``: held when holder metadata is
    not verifiably dead, free when the directory is absent, a meta-less
    crash leftover past the lock script's incomplete-age rule, or a hold
    whose recorded holder is verified dead, unknown for a non-fingerprint
    root or an unreadable lock root; for a meta-less directory the status
    command's raw held line is the documented divergence this column
    resolves by applying the incomplete-age rule, never an agreement
    claim. The enumeration walks every ``run-manifest-*.json`` payload
    itself - never the root-filtered ``load_run_manifest`` and never
    ``_detect_interrupted_runs``, whose suppression shapes (dispositioned
    records) must stay visible as columns here. The keep-filter holds
    ``complete`` false and nothing adopting the record (no other
    manifest's ``adopted_from`` link names it); the ``adopted`` column
    reports the record's own ``adopted_from`` link, so an adopted boundary
    stays distinguishable in the output. Records bind at run identity (the
    payload ``run_id``): a worktree shadow copy (a non-canonical
    ``run-manifest-*.json`` filename) renders as ``shadow-of <run_id>``
    naming its own filename, never as an independent boundary, and a
    canonical record whose run closed through another file (a terminal
    record on any file of the run: ``complete`` or a ``dispositioned``
    record, shadow copies included) renders as ``closed-run <run_id>``
    history naming the closing file instead of an open boundary, while a
    record carrying its own ``dispositioned`` closure keeps the column
    line with ``dispositioned=yes``. An empty set prints ``no
    interrupted manifests`` and exits 0."""
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py list-interrupted-manifests",
        description=(
            "List the interrupted run manifests by repository identity and "
            "lock state (read-only)."
        ),
    )
    parser.parse_args(argv)

    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    ctx = GateContext.discover(Path(root) if root else None)
    records: list[tuple[str, RunManifest]] = []
    if ctx.done_session_dir.is_dir():
        for path in sorted(ctx.done_session_dir.glob("run-manifest-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            manifest = RunManifest.from_dict(payload)
            if manifest is None:
                continue
            records.append((path.name, manifest))
    adopted_ids = {m.adopted_from for _, m in records if m.adopted_from}
    by_run: dict[str, list[tuple[str, RunManifest]]] = {}
    for filename, manifest in records:
        by_run.setdefault(manifest.run_id, []).append((filename, manifest))
    lines: list[str] = []
    root_match_seen = False
    for filename, manifest in records:
        if manifest.complete or manifest.run_id in adopted_ids:
            continue
        canonical_name = _manifest_path(
            ctx.done_session_dir, manifest.run_id
        ).name
        is_shadow = filename != canonical_name
        terminal: Optional[str] = None
        closer: Optional[str] = None
        for sib_name, sibling in by_run[manifest.run_id]:
            if sibling.complete:
                terminal, closer = "finalized", sib_name
                break
            if sibling.dispositioned is not None:
                terminal, closer = "dispositioned", sib_name
        root_match = _repo_root_matches_value(manifest.repo_root, ctx.repo_root)
        root_match_seen = root_match_seen or root_match
        if is_shadow:
            # A worktree copy binds to its run: a shadow-of line naming the
            # copy's own filename, never an independent boundary line.
            lines.append(f"shadow-of {manifest.run_id} {filename}")
            continue
        if terminal is not None and manifest.dispositioned is None:
            # The run closed through another file (a worktree copy's
            # disposition included): the remaining canonical record renders
            # as the closed run's history, never as an open boundary.
            lines.append(
                f"closed-run {manifest.run_id} {filename} "
                f"(terminal state {terminal} via {closer})"
            )
            continue
        created = datetime.fromtimestamp(
            manifest.created_epoch, tz=timezone.utc
        ).date().isoformat()
        lines.append(
            f"{manifest.run_id} "
            f"root_matches_current_repo={'yes' if root_match else 'no'} "
            f"lock={_done_lock_state(manifest.repo_root)} "
            f"dispositioned={'yes' if manifest.dispositioned else 'no'} "
            f"adopted={'yes' if manifest.adopted_from else 'no'} "
            f"created={created}"
        )
    if not lines:
        print("no interrupted manifests")
        return 0
    for line in lines:
        print(line)
    if root_match_seen:
        # One guidance line: a matching root is a repository identity fact;
        # liveness belongs to the lock column and the lock status command.
        print(
            "note: a root_matches_current_repo=yes record is a repository "
            "identity fact, not process or lock liveness; the lock column "
            "is a read-only derivation and done-lock.sh status is the "
            "liveness check of record"
        )
    return 0


def _dispatch(args: list[str]) -> int:
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
        # With a phase argument: print that phase's roster one gate per
        # line, warning-posture gates suffixed " (warning)". Bare: the
        # landing roster's plain gate ids (the closeout's one sweep run).
        if args[1:]:
            phase = args[1]
            if phase not in PHASES:
                print(f"list-gates: unknown phase '{phase}'", file=sys.stderr)
                print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
                return 3
            for gate_id in PHASES[phase]:
                suffix = " (warning)" if gate_id in LANDING_WARNING_GATES else ""
                print(f"{gate_id}{suffix}")
            return 0
        for gate_id in LANDING_GATES:
            print(gate_id)
        return 0
    if command == "write-manifest":
        return _cmd_write_manifest(args[1:])
    if command == "finalize-manifest":
        return _cmd_finalize_manifest(args[1:])
    if command == "disposition-manifest":
        return _cmd_disposition_manifest(args[1:])
    if command == "recover-manifest":
        return _cmd_recover_manifest(args[1:])
    if command == "checkpoint-manifest":
        return _cmd_checkpoint_manifest(args[1:])
    if command == "classify-run-boundary":
        return _cmd_classify_run_boundary(args[1:])
    if command == "list-interrupted-manifests":
        return _cmd_list_interrupted_manifests(args[1:])
    if command in PHASES:
        boundary_class = "final-closeout"
        trailing = args[1:]
        idx = 0
        while idx < len(trailing):
            if trailing[idx] == "--boundary-class":
                if idx + 1 >= len(trailing):
                    print(
                        "--boundary-class requires a value (one of "
                        f"{', '.join(BOUNDARY_CLASSES)})",
                        file=sys.stderr,
                    )
                    print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
                    return 3
                boundary_class = trailing[idx + 1]
                idx += 2
            else:
                idx += 1
        root = os.environ.get("DONE_SWEEP_REPO_ROOT")
        ctx = GateContext.discover(Path(root) if root else None)
        try:
            results = run_phase(command, ctx, boundary_class)
        except ValueError as exc:
            print(f"config error: {exc}", file=sys.stderr)
            print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
            return 3
        print(render_report(results))
        code = phase_exit(results)
        print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS.get(code, 'indeterminate')}")
        return code
    print(_usage(), file=sys.stderr)
    print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
    return 3


def main(argv: Optional[list[str]] = None) -> int:
    try:
        return _dispatch(list(sys.argv[1:] if argv is None else argv))
    except ValueError as exc:
        # Facts-first resolution is fail-closed: an unresolvable repo path
        # key is a configuration tool error (contract exit 3, named on
        # stderr, OUTCOME line emitted), never a bare exit-1 traceback that
        # the outcome contract would read as a modeled fail.
        print(f"config error: {exc}", file=sys.stderr)
        print(f"{OUTCOME_LINE_PREFIX} {OUTCOME_LABELS[3]}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
