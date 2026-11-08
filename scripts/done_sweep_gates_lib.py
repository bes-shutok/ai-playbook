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
  description-length (blocking: a measured over-cap rc=1 refuses the
  landing, and the commit path records its guard catch before refusing),
  foreign-staging,
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
(the staging-path predicate is imported, never re-implemented),
``review_record_selection`` (the preservation-backup grammar constant
``BACKUP_INFIX`` is imported, never redefined), and
``dispatch_admission`` (the admission record's seeder imports the
consult's ``owned_paths_from_plan`` derivation, never a copied one).

The ``write-manifest`` sub-command writes the done Step 0 run manifest record
(``run-manifest-<run_id>.json`` next to the run-start marker); it owns no
gate and does not touch the gate registry. It also reports interrupted runs
(root-matched manifests whose ``complete`` flag is still false and which no
other manifest adopts): a retry continues an interrupted run's boundary only
through an explicit ``--adopt <run_id>`` boundary copy, never implicitly.
The ``finalize-manifest`` sub-command sets a run manifest's ``complete`` flag
to true in place (done Step 6, immediately before the done-lock release) and
propagates the finalized bytes into the primary checkout's surviving shadow
record for the same run-id (its success path and already-complete early
return only; misses report on the failure channel without failing the
finalize).
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
import ctypes
import errno
import json
import hashlib
import hmac
import math
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

import dispatch_admission
import facts_paths
import plan_shape
import plan_readiness
import validate_review_staging as vrs
from dispatch_admission import owned_paths_from_plan
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
# The hygiene scanner's non-blocking report-only scope row prefix (plan
# 2026-10-26-hygiene-scanner-default-scope-parity): the sensitive-data gate
# forwards only these child rows into its warnings, verbatim.
PUBLIC_HYGIENE_REPORT_LINE_PREFIX = "PUBLIC_HYGIENE_REPORT:"

# Registry: the landing phase, the closeout's one sweep run (the retained
# roster from the done target-state classification, the plan's Outcome
# table). plan-readiness and instruction-size ride in warning posture: they
# report, never block. description-length left the warning roster with the
# catch-promotion plan (docs/history/plans/2026-10-24-description-length-
# gate-catch-promotion.md): a measured over-cap result keeps rc=1 through the
# structured phase report and refuses the landing, and the commit path
# records its guard catch in scripts/gate_liveness_ledger.json before
# refusing. backlog-inbox and vim-swap-sweep
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
LANDING_WARNING_GATES = frozenset({"plan-readiness", "instruction-size"})

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
# Visibility exemption (2026-10-23 plan:
# docs/history/plans/completed/2026-10-23-done-sensitive-scan-private-repository-scope.md;
# supersedes the 2026-10-12 company/private-pet profile direction): the
# exemption skips both content arms exactly when the repo facts resolve
# artifact_visibility = "private" (case-insensitive), with no dependency on
# project_type: neither the credential family nor the public-artifact family
# is matched over staged or untracked content. The exemption is
# declaration-trusted: the untracked working-tree facts are read fresh per
# gate run, so the visibility is flippable within the same landing and a
# well-formed but false declaration is honored. Every non-exempt visibility
# (public; absent, malformed, or unrecognized values) keeps the strict scan
# with both families for every project type.
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
# The execute-plan plan-slug proof family: closeout evidence retained
# cross-session by design (Phase 0 baseline capture, the skip sibling's
# capture-failure record a retry must re-read, and the migration manifest a
# later plan closeout's gate-removal reads through its explicit operand).
PLAN_SLUG_PROOF_FILES = (
    "closeout-baseline.json",
    "closeout-baseline-skip.json",
    "closeout-migration.json",
)


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
    # The archive-ceremony post-landing arm's pinned span boundary (the
    # entry point's resolved base). Only that entry point sets it; every
    # other consumer leaves the default None and the archive derivation
    # re-reads the session dir exactly as before.
    archive_ceremony_pinned_span_base: Optional[str] = None

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
        The sensitive-data gate skips its two content arms exactly when this
        resolves to "private", regardless of project_type (see
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
        env: Optional[dict] = None,
    ):
        return subprocess.run(
            args,
            cwd=str(cwd or self.repo_root),
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_S,
            input=input_text,
            env=env,
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
            "complete the facts block before running the gates; the file is "
            "machine-local by design and never rides the branch, so copy the "
            "primary checkout's facts block into this checkout (creating the "
            ".ai-playbook parent first) and re-run)"
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
    """Parse one run-start marker; content must record this repo's root."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return _parse_marker_content(path, content, repo_root)


def _parse_marker_content(
    path: Path, content: str, repo_root: Path
) -> Optional[RunMarker]:
    """Parse marker text read from a verified path or opened descriptor."""
    struct = _marker_struct(content)
    if struct is None:
        return None
    epoch, pid, recorded_root = struct
    if len(content.strip().split()) == 3 and re.fullmatch(r"[0-9a-f]{64}", recorded_root):
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


def _read_regular_text_at(directory_fd: int, name: str) -> Optional[str]:
    """Read one regular file through a no-follow directory descriptor."""
    fd: Optional[int] = None
    try:
        before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if not stat_module.S_ISREG(before.st_mode):
            return None
        fd = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
            dir_fd=directory_fd,
        )
        opened = os.fstat(fd)
        if not stat_module.S_ISREG(opened.st_mode) or (
            opened.st_dev, opened.st_ino, opened.st_mode
        ) != (before.st_dev, before.st_ino, before.st_mode):
            return None
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = None
            return stream.read()
    except (OSError, UnicodeError):
        return None
    finally:
        if fd is not None:
            os.close(fd)


def derive_session_window(
    done_session_dir: Path,
    repo_root: Path,
    directory_fd: Optional[int] = None,
) -> SessionWindow:
    """Derive the marker window, optionally reading every witness via one
    already-opened ``done-session`` directory descriptor."""
    notes: list[str] = []
    markers: list[RunMarker] = []
    cross_repo = 0
    malformed = 0
    if directory_fd is not None:
        marker_names = sorted(
            name for name in os.listdir(directory_fd) if name.startswith("run-start-")
        )
        for name in marker_names:
            path = done_session_dir / name
            content = _read_regular_text_at(directory_fd, name)
            if content is None:
                malformed += 1
                continue
            parsed = _parse_marker_content(path, content, repo_root)
            if parsed is not None:
                markers.append(parsed)
            elif _marker_records_other_repo_content(content, repo_root):
                cross_repo += 1
            else:
                malformed += 1
    elif done_session_dir.is_dir():
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
                done_session_dir, repo_root, current, notes, directory_fd
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
    directory_fd: Optional[int] = None,
) -> Optional[SessionWindow]:
    """Use the marker-bound manifest and ledger as a single-marker window.

    When ``directory_fd`` is supplied, all manifest and ledger reads remain
    relative to that same opened directory; inability to verify a witness
    leaves the window unanchorable.
    """
    if directory_fd is None:
        if not done_session_dir.is_dir():
            return None
        manifest = load_run_manifest(
            done_session_dir, repo_root, SessionWindow(False, None, current, None, [])
        )
        if manifest is None:
            best: Optional[RunManifest] = None
            for path in sorted(done_session_dir.glob("run-manifest-*.json")):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                candidate = RunManifest.from_dict(payload)
                if candidate is None or not _manifest_root_matches(candidate.repo_root, repo_root):
                    continue
                if best is None or candidate.created_epoch > best.created_epoch:
                    best = candidate
            manifest = best
        if manifest is None:
            return None
        ledger_name = _owned_commits_ledger_path(done_session_dir, manifest.run_id).name
        if not (done_session_dir / ledger_name).is_file():
            notes.append(
                "witness pair incomplete: run manifest "
                f"{_manifest_path(done_session_dir, manifest.run_id).name} present "
                f"but owned-commits ledger {ledger_name} absent; window stays unanchorable"
            )
            return None
    else:
        manifest: Optional[RunManifest] = None
        best: Optional[RunManifest] = None
        for name in sorted(os.listdir(directory_fd)):
            if not (name.startswith("run-manifest-") and name.endswith(".json")):
                continue
            text = _read_regular_text_at(directory_fd, name)
            if text is None:
                continue
            try:
                payload = json.loads(text)
            except ValueError:
                continue
            candidate = RunManifest.from_dict(payload)
            if candidate is None or not _manifest_root_matches(candidate.repo_root, repo_root):
                continue
            if candidate.marker == current.path.name and (
                manifest is None or candidate.created_epoch > manifest.created_epoch
            ):
                manifest = candidate
            if best is None or candidate.created_epoch > best.created_epoch:
                best = candidate
        if manifest is None:
            manifest = best
        if manifest is None:
            return None
        ledger_name = _owned_commits_ledger_path(done_session_dir, manifest.run_id).name
        try:
            ledger_stat = os.stat(
                ledger_name, dir_fd=directory_fd, follow_symlinks=False
            )
        except OSError:
            ledger_stat = None
        if ledger_stat is None or not stat_module.S_ISREG(ledger_stat.st_mode):
            notes.append(
                "witness pair incomplete: run manifest "
                f"{_manifest_path(done_session_dir, manifest.run_id).name} present "
                f"but owned-commits ledger {ledger_name} absent; window stays unanchorable"
            )
            return None
    notes.append(
        "single-marker window anchored from the witness pair: run manifest "
        f"{_manifest_path(done_session_dir, manifest.run_id).name} plus "
        f"owned-commits ledger {ledger_name} (anchor unset; marker pruning "
        "keeps its conservative behavior)"
    )
    return SessionWindow(True, None, current, manifest.created_epoch, notes)


def _marker_records_other_repo(path: Path, repo_root: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return _marker_records_other_repo_content(content, repo_root)


def _marker_records_other_repo_content(content: str, repo_root: Path) -> bool:
    fields = content.strip().split()
    if len(fields) < 3:
        return False
    recorded_root = " ".join(fields[1:-1])
    if len(fields) == 3 and re.fullmatch(r"[0-9a-f]{64}", recorded_root):
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


def _tracked_ignored_paths(ctx: GateContext) -> list[str]:
    """Index-tracked paths an ignore rule matches, repo-wide: ``git ls-files
    -i -c --exclude-standard`` with no pathspec, deliberately NOT passed
    through ``_session_ignored_paths`` (no session-window/mtime filter), so a
    tracked-ignored path inherited from a polluted base is still reported.
    The rows surface as warning-only report lines beside the untracked
    ignored arm in ``gate_doc_registry``; they never join the check-writes
    union and never change a gate verdict or exit code.

    Admission (recording destination for a true catch): incident, the
    witnessed double landing of force-tracked seals f5a8142ed and 4399aee99;
    catch frequency, about two per 138 seals in the audit home's history
    plus the three live tracked review records the first closeout reports;
    false-positive cost, zero on a clean index once those records are
    untracked; review 2027-01-20, promotion only after a true catch and a
    pre-registered registry-removal row.
    """
    proc = ctx.git("ls-files", "-i", "-c", "--exclude-standard")
    if proc.returncode != 0:
        return []
    return [
        _unquote_porcelain_path(ln)
        for ln in proc.stdout.splitlines()
        if ln.strip()
    ]


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


def _escape_control_chars(path: str) -> str:
    """Backslash-escape the control characters an unquoted porcelain row can
    carry, so a path never breaks the line structure of the human-facing
    warning block it is formatted into."""
    return (
        path.replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\v", "\\v")
        .replace("\f", "\\f")
    )


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


CRASH_EVIDENCE_MAX_CHARS = 200


def _traceback_detail(rows: list[str]) -> Optional[str]:
    """The final non-empty row of a traceback stream: the exception detail
    when one exists, never a later informative row lost to the header (a
    degenerate header-only stream returns the header, there being no
    better evidence available)."""
    if not rows or not rows[0].startswith("Traceback (most recent call last):"):
        return None
    for row in reversed(rows):
        if row.strip():
            return row
    return None


def _manifest_exempts(ctx: GateContext, plan_rel: Path) -> bool:
    """execute-plan mechanical exemption: active manifest with a fresh
    ``updated:`` line (no older than 24h), resolved at the canonical feature
    slug and owned only when its recorded ``plan_path`` exactly matches the
    candidate. Stale or absent updated: never exempts."""
    slug = plan_readiness.feature_slug(plan_rel)
    manifest = ctx.execute_plan_dir / slug / "manifest.md"
    if not manifest.is_file():
        return False
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return False
    state = None
    updated: Optional[datetime] = None
    recorded_plan_path: Optional[str] = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("workflow_state:"):
            state = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("updated:"):
            updated = _parse_marker_time(stripped.split(":", 1)[1])
        elif stripped.startswith("plan_path:"):
            recorded_plan_path = stripped.split(":", 1)[1].strip()
    if state != "active" or updated is None:
        return False
    if recorded_plan_path != str(plan_rel):
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
            # traceback header. A traceback wholly on stderr reports its
            # final exception detail, never the header row.
            stderr_detail = _traceback_detail(stderr_rows)
            first_failure = (
                stderr_detail if stderr_detail is not None else stderr_rows[0]
            )
        elif stdout_rows:
            first_failure = stdout_rows[-1]
        else:
            first_failure = "no output"
        label = _child_final_outcome(proc)
        if label is None:
            # The contract's no-line rule wins over the exit code: a child
            # run with no final OUTCOME line (a crash or a legacy shape) is
            # never a silent pass. The diagnostic excerpt is capped, the
            # useful end retained.
            evidence = first_failure
            if len(evidence) > CRASH_EVIDENCE_MAX_CHARS:
                evidence = evidence[-CRASH_EVIDENCE_MAX_CHARS:]
            tool_errors.append(
                f"{plan_rel} (no final OUTCOME line, child exit "
                f"{proc.returncode}; evidence: {evidence})"
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
    # The tracked sibling's rows stay on the warnings channel only: they
    # never join ``union`` below, which is what keeps the report from ever
    # moving a verdict (admission in _tracked_ignored_paths). Unquoted
    # porcelain rows can carry control characters and the warning goes to
    # the human summary block, so each row is escaped before formatting.
    warnings.extend(
        f"warning: tracked-ignored path in the index: {_escape_control_chars(rel)}"
        for rel in _tracked_ignored_paths(ctx)
    )
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


def _run_marker_epoch(path: Path) -> tuple[Optional[float], Optional[str]]:
    """The bound run-start marker's recorded epoch: the leading timestamp
    token of the marker's first content line, read for the linked-worktree
    foreign-by-arrival arm. Returns ``(epoch, None)`` on a usable finite
    epoch and ``(None, reason)`` fail-closed otherwise - an unreadable
    marker file, a marker with no content line, or a first token that is
    either unparseable or non-finite: the marker parse's plain ``float()``
    accepts ``nan``/``inf`` tokens over an otherwise confirming root
    record, and a non-finite boundary classifies nothing, so the arrival
    arm refuses closed on them. Reporting/refusal channel only: never
    mutates state."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, (
            f"the bound run-start marker {path.name} is unreadable: {exc}"
        )
    for line in content.splitlines():
        fields = line.split()
        if not fields:
            continue
        token = fields[0]
        try:
            epoch = float(token)
        except ValueError:
            return None, (
                f"the bound run-start marker {path.name} records no "
                f"parseable epoch (first content-line token {token!r})"
            )
        if not math.isfinite(epoch):
            return None, (
                f"the bound run-start marker {path.name} records a "
                f"non-finite epoch (first content-line token {token!r})"
            )
        return epoch, None
    return None, f"the bound run-start marker {path.name} has no content line"


def _foreign_by_default_split(
    ctx: GateContext,
    uncovered: list[str],
    owned_review_paths: list[str],
    *,
    arrival_marker: Optional[Path] = None,
) -> tuple[list[str], list[str], Optional[str], bool]:
    """Split the write-manifest claim-or-foreign uncovered set into
    (auto-foreign, still-refused) plus the arrival-arm report pair: the
    refusal reason when the worktree arm's marker epoch is unusable, and
    whether the classification ran in the linked-worktree arrival arm
    (report-line channel selection only).

    The gitignored primary reviews home is by design the shared run-artifact
    surface every run migrates records INTO, so its historical contents are
    structurally foreign to any single run; refusing on them is a false
    positive (witnessed 2026-10-23, the parked done setup in the primary
    checkout; landing commit b3025de59).
    A candidate qualifies for the foreign-by-default arm only when ALL hold:

    - the gate context's repo root IS the primary checkout (first
      ``git worktree list --porcelain`` entry), or - the linked-worktree
      foreign-by-arrival arm (plan
      docs/history/plans/2026-11-01-done-setup-staging-doc-foreign-arrival-default.md)
      - a linked worktree with a fresh boundary (``arrival_marker``
      bound by the caller; an adopted manifest never passes one, so a
      resume's fresh marker never re-classifies the adopted run's staging
      docs) whose reviews home the provisioning transfer carried in;
    - the candidate is gitignored (``!!``-class under the reviews pathspec),
      the shared-home marker;
    - the candidate sits under the resolved reviews dir;
    - the run staged NONE of its own review records there (a run that did
      keeps the owned arm exactly as before);
    - in the linked-worktree arm only: the candidate's mtime is STRICTLY
      older than the bound run-start marker's recorded epoch (a present-
      before-the-run candidate is not this run's write, so it classifies
      foreign-by-arrival; an equal or newer mtime stays in the refuse set,
      keeping the mid-run silent-claiming protection), and the marker
      epoch itself is readable and finite - a missing, unreadable, or
      unparseable epoch fails closed and refuses the whole uncovered set.

    Everything else - candidates outside the reviews home, tracked-but-
    unclaimed, or any candidate at all when the run staged in the home -
    stays in the refuse set unchanged, so the witnessed 2026-10-16
    silent-claiming catch keeps its coverage. An unresolvable worktree
    list still fails closed to refuse in both shapes.
    """
    primary, _primary_err = _resolve_primary_checkout(ctx)
    if primary is None:
        return [], list(uncovered), None, False
    is_primary = os.path.realpath(str(primary)) == os.path.realpath(
        str(ctx.repo_root)
    )
    if not is_primary and arrival_marker is None:
        # A linked worktree without a fresh boundary (an adopted
        # manifest): the refuse arm stays exactly as before.
        return [], list(uncovered), None, False
    if not _is_relative_to(ctx.reviews_dir, ctx.repo_root):
        return [], list(uncovered), None, False
    reviews_rel = ctx.reviews_dir.relative_to(ctx.repo_root).as_posix()
    if any(
        _is_relative_to(ctx.reviews_dir / p, ctx.reviews_dir)
        for p in owned_review_paths
    ):
        return [], list(uncovered), None, False
    ignored = set(_ignored_paths(ctx, reviews_rel))
    auto: list[str] = []
    refused: list[str] = []
    if not is_primary:
        # Linked-worktree foreign-by-arrival arm: the transferred reviews
        # home's pre-marker staging docs predate the run's first owned
        # record, so they are structurally not this run's writes.
        epoch, epoch_refusal = _run_marker_epoch(arrival_marker)
        if epoch_refusal is not None:
            return [], list(uncovered), epoch_refusal, False
        for path in uncovered:
            rel = (
                Path(path)
                .resolve()
                .relative_to(ctx.repo_root.resolve())
                .as_posix()
                if _is_relative_to(ctx.repo_root / path, ctx.repo_root)
                else path
            )
            candidate = ctx.repo_root / rel
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                refused.append(path)
                continue
            if (
                rel in ignored
                and _is_relative_to(candidate, ctx.reviews_dir)
                and mtime < epoch
            ):
                auto.append(rel)
            else:
                refused.append(path)
        return auto, refused, None, True
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
    return auto, refused, None, False


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

# The docs/tmp drain arms' policy knobs (plan
# docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md Task 1): the
# deletion horizon is a named constant re-priced at the next docs/tmp census,
# with the repo-facts knob beside it; the posture gates whether the arms
# unlink or only report, defaulting to report-only until a census cycle
# witnesses zero mispriced would-drain rows.
DOCS_TMP_DELETION_HORIZON_DAYS = 30
DOCS_TMP_DRAIN_ARMS_DEFAULT = "report-only"
DOCS_TMP_NEVER_SYNCED_DRAIN_REASON = (
    "expired never-synced scratch (age > horizon, outside window, uncited)"
)


def _docs_tmp_drain_posture(ctx: GateContext) -> str:
    """The drain-arms posture from repo facts: report-only | on | off."""
    raw = facts_paths.resolve_toml_key_raw(ctx.repo_root, "docs_tmp_drain_arms")
    value = (raw or "").strip().strip('"').strip("'")
    if value in ("report-only", "on", "off"):
        return value
    return DOCS_TMP_DRAIN_ARMS_DEFAULT


def _docs_tmp_deletion_horizon_days(ctx: GateContext) -> float:
    """The deletion horizon in days: the facts knob over the constant."""
    raw = facts_paths.resolve_toml_key_raw(
        ctx.repo_root, "docs_tmp_deletion_horizon_days"
    )
    try:
        value = float((raw or "").strip().strip('"').strip("'"))
    except ValueError:
        return float(DOCS_TMP_DELETION_HORIZON_DAYS)
    return value if value > 0 else float(DOCS_TMP_DELETION_HORIZON_DAYS)


def _entry_birth_epoch(entry_stat: os.stat_result) -> Optional[float]:
    """The entry's birth time where the platform records one; None keeps."""
    birth = getattr(entry_stat, "st_birthtime", None)
    if birth is None or birth <= 0:
        return None
    return float(birth)


def _classify_never_synced_candidate(
    entry_stat: os.stat_result,
    window: SessionWindow,
    horizon_days: float,
    now_epoch: float,
) -> tuple[str, Optional[str]]:
    """The cheap pure guards of the never-synced scratch arm; the returned
    arm is 'keep' (with its named reason) or 'candidate' (the sync state
    and citation checks resolve later, batched). The boundary keeps:
    strictly older than the horizon, never equal."""
    if not window.anchored or window.start_epoch is None:
        return "keep", (
            "never-synced scratch, but the session window is unanchorable; "
            "never guessing"
        )
    mtime = entry_stat.st_mtime
    if mtime >= window.start_epoch:
        return "keep", (
            "never-synced scratch but modified inside the session window"
        )
    birth = _entry_birth_epoch(entry_stat)
    if birth is None:
        return "keep", (
            "never-synced scratch with an unreadable birth time; never guessing"
        )
    horizon_epoch = now_epoch - horizon_days * 86400.0
    if not (mtime < horizon_epoch and birth < horizon_epoch):
        return "keep", (
            "never-synced scratch inside the deletion horizon "
            f"({horizon_days:g} days)"
        )
    return "candidate", None


def _batched_docs_branch_hits(
    ctx: GateContext, rels: list[str]
) -> Optional[set[str]]:
    """One batched docs-branch listing over the candidate rels; None means
    the listing failed (uncertain) and every candidate keeps."""
    proc = ctx.git("ls-tree", "-r", "--name-only", "refs/heads/docs", "--", *rels)
    if proc.returncode != 0:
        return None
    return {line for line in proc.stdout.splitlines() if line.strip()}


def _synced_shape_class(name: str) -> bool:
    """The single-homed synced shape-class predicate (`.py`, `.log.md`,
    dated one-off `.md`): the synced arm keeps these to sync, the
    never-synced scratch arm excludes them, and one copy owns both."""
    return (
        name.endswith(".py")
        or name.endswith(".log.md")
        or (name.endswith(".md") and bool(DATED_ONE_OFF_RE.match(name)))
    )


def _marker_struct(content: str) -> Optional[tuple[float, int, str]]:
    """The single-homed structural marker parse shared by the strict parser
    and the dead-root arm's lenient foreign parse: (epoch, pid,
    recorded_root), or None for malformed content."""
    fields = content.strip().split()
    if len(fields) < 3:
        return None
    try:
        epoch = float(fields[0])
        pid = int(fields[-1])
    except ValueError:
        return None
    return epoch, pid, " ".join(fields[1:-1])


@dataclass(frozen=True)
class PinnedTmpRoot:
    path: Path
    fd: int
    identity: tuple[tuple[str, int, int, int], ...]


@dataclass
class QuarantinedCandidate:
    directory_name: str
    directory_fd: int
    expected_identity: tuple[int, int, int]
    entry_name: str = "candidate"


def _candidate_identity(info: os.stat_result) -> tuple[int, int, int]:
    return info.st_dev, info.st_ino, stat_module.S_IFMT(info.st_mode)


def _rename_noreplace_at(
    source_fd: int, source_name: str, target_fd: int, target_name: str
) -> None:
    """Rename one entry without ever replacing an existing destination."""
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source_name)
    target_bytes = os.fsencode(target_name)
    if hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
            ctypes.c_uint,
        ]
        result = rename(source_fd, source_bytes, target_fd, target_bytes, 1)  # RENAME_NOREPLACE
    elif hasattr(libc, "renameatx_np"):
        rename = libc.renameatx_np
        rename.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
            ctypes.c_uint,
        ]
        result = rename(source_fd, source_bytes, target_fd, target_bytes, 4)  # RENAME_EXCL
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), target_name)


def _quarantine_candidate(
    root_fd: int,
    source_fd: int,
    name: str,
    expected: os.stat_result,
) -> tuple[Optional[QuarantinedCandidate], Optional[str]]:
    """Atomically move a candidate beneath a private directory under root_fd.

    The caller supplies the identity observed during initial classification.
    A different object moved into quarantine is restored without replacing a
    concurrent source entry and is never deleted.
    """
    directory_name = ".tmp-sweep-quarantine-" + uuid.uuid4().hex
    directory_fd: Optional[int] = None
    moved = False
    try:
        os.mkdir(directory_name, 0o700, dir_fd=root_fd)
        directory_fd = os.open(
            directory_name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
            dir_fd=root_fd,
        )
        opened_dir = os.fstat(directory_fd)
        if not stat_module.S_ISDIR(opened_dir.st_mode) or opened_dir.st_mode & 0o077:
            os.close(directory_fd)
            os.rmdir(directory_name, dir_fd=root_fd)
            return None, "quarantine directory is not private"
        _rename_noreplace_at(source_fd, name, directory_fd, "candidate")
        moved = True
        quarantined = os.stat(
            "candidate", dir_fd=directory_fd, follow_symlinks=False
        )
        if _candidate_identity(quarantined) != _candidate_identity(expected):
            reason = "candidate identity changed; replacement preserved"
            try:
                os.stat(name, dir_fd=source_fd, follow_symlinks=False)
            except FileNotFoundError:
                try:
                    _rename_noreplace_at(
                        directory_fd,
                        "candidate",
                        source_fd,
                        name,
                    )
                except OSError:
                    return QuarantinedCandidate(
                        directory_name, directory_fd, _candidate_identity(expected)
                    ), reason
                try:
                    os.rmdir(directory_name, dir_fd=root_fd)
                except OSError:
                    pass
                os.close(directory_fd)
                return None, reason
            return QuarantinedCandidate(
                directory_name, directory_fd, _candidate_identity(expected)
            ), reason
        return QuarantinedCandidate(
            directory_name, directory_fd, _candidate_identity(expected)
        ), None
    except OSError as exc:
        if moved and directory_fd is not None:
            quarantined = QuarantinedCandidate(
                directory_name, directory_fd, _candidate_identity(expected)
            )
            try:
                os.stat(name, dir_fd=source_fd, follow_symlinks=False)
            except FileNotFoundError:
                try:
                    _rename_noreplace_at(
                        directory_fd,
                        "candidate",
                        source_fd,
                        name,
                    )
                    try:
                        os.rmdir(directory_name, dir_fd=root_fd)
                    except OSError:
                        pass
                    os.close(directory_fd)
                    return None, f"candidate quarantine check failed; restored ({exc})"
                except OSError:
                    pass
            return quarantined, f"candidate quarantine check failed; retained at {directory_name}/candidate ({exc})"
        try:
            if directory_fd is not None:
                os.close(directory_fd)
        except OSError:
            pass
        try:
            os.rmdir(directory_name, dir_fd=root_fd)
        except OSError:
            pass
        if isinstance(exc, FileExistsError):
            return (
                None,
                "quarantine destination occupied; source preserved; "
                f"collision retained at {directory_name}/candidate",
            )
        return None, f"candidate quarantine failed; preserved ({exc})"


def _restore_quarantined_candidate(
    root_fd: int,
    source_fd: int,
    source_name: str,
    quarantined: QuarantinedCandidate,
) -> Optional[str]:
    """Restore a quarantined candidate or return its retained quarantine path."""
    try:
        _rename_noreplace_at(
            quarantined.directory_fd,
            quarantined.entry_name,
            source_fd,
            source_name,
        )
        try:
            os.rmdir(quarantined.directory_name, dir_fd=root_fd)
        except OSError:
            pass
        os.close(quarantined.directory_fd)
        return None
    except OSError:
        pass
    location = quarantined.directory_name + "/" + quarantined.entry_name
    os.close(quarantined.directory_fd)
    return location


def _discard_quarantined_candidate(
    root_fd: int,
    quarantined: QuarantinedCandidate,
    revalidate: Optional[Callable[[], bool]] = None,
) -> None:
    """Remove only the identity-checked candidate that still passes policy."""
    info = os.stat(
        quarantined.entry_name,
        dir_fd=quarantined.directory_fd,
        follow_symlinks=False,
    )
    if _candidate_identity(info) != quarantined.expected_identity:
        raise OSError(errno.ESTALE, "candidate identity changed before discard")
    if revalidate is not None and not revalidate():
        raise OSError(errno.ESTALE, "candidate eligibility changed before discard")
    if stat_module.S_ISDIR(info.st_mode):
        _remove_tree_at(quarantined.directory_fd, quarantined.entry_name)
    else:
        os.unlink(quarantined.entry_name, dir_fd=quarantined.directory_fd)
    try:
        os.rmdir(quarantined.directory_name, dir_fd=root_fd)
    except OSError:
        # The candidate is already removed; an empty private container may be
        # retried by a later sweep without misreporting candidate survival.
        pass
    finally:
        os.close(quarantined.directory_fd)


def _quarantine_location(quarantined: QuarantinedCandidate) -> str:
    os.close(quarantined.directory_fd)
    return quarantined.directory_name + "/" + quarantined.entry_name


def _open_pinned_tmp_root(
    ctx: GateContext,
) -> tuple[Optional[PinnedTmpRoot], Optional[str]]:
    """Open the facts-configured tmp root from the repository descriptor.

    The raw facts value defines the lexical walk. Require the resolved
    ``GateContext`` path to name that same path, then open every component
    without following symlinks and compare each opened directory with its
    no-follow stat before carrying the final descriptor forward.
    """
    raw = facts_paths.resolve_toml_key_raw(ctx.repo_root, "tmp_dir")
    if not isinstance(raw, str) or not raw.strip():
        return None, "tmp_dir is missing or unreadable in repo facts"
    raw_path = Path(os.path.expanduser(raw.strip()))
    if ".." in raw_path.parts:
        return None, "raw tmp_dir contains a parent traversal"
    root = ctx.repo_root.resolve()
    candidate = raw_path if raw_path.is_absolute() else root / raw_path
    candidate = Path(os.path.abspath(os.path.normpath(str(candidate))))
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return None, "raw tmp_dir resolves outside the repository"
    if not relative.parts or relative.parts[-1] not in {"tmp", ".tmp"}:
        return None, "tmp_dir must be a dedicated repository tmp or .tmp root"
    if Path(ctx.tmp_dir) != candidate:
        return None, "raw tmp_dir and facts-resolved tmp_dir disagree"

    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow:
        return None, "platform does not support no-follow directory opens"
    repo_fd: Optional[int] = None
    current_fd: Optional[int] = None
    try:
        repo_fd = os.open(root, directory_flags | nofollow)
        repo_stat = os.fstat(repo_fd)
        if not stat_module.S_ISDIR(repo_stat.st_mode):
            return None, "repository anchor is not a directory"
        identity: list[tuple[str, int, int, int]] = [
            (".", repo_stat.st_dev, repo_stat.st_ino, stat_module.S_IFMT(repo_stat.st_mode))
        ]
        current_fd = repo_fd
        for component in relative.parts:
            before = os.stat(
                component, dir_fd=current_fd, follow_symlinks=False
            )
            if not stat_module.S_ISDIR(before.st_mode):
                return None, f"tmp_dir component {component!r} is not a directory"
            child_fd = os.open(
                component, directory_flags | nofollow, dir_fd=current_fd
            )
            after = os.fstat(child_fd)
            if (
                not stat_module.S_ISDIR(after.st_mode)
                or (before.st_dev, before.st_ino, before.st_mode)
                != (after.st_dev, after.st_ino, after.st_mode)
            ):
                os.close(child_fd)
                return None, f"tmp_dir component {component!r} changed while opening"
            identity.append(
                (
                    component,
                    after.st_dev,
                    after.st_ino,
                    stat_module.S_IFMT(after.st_mode),
                )
            )
            if current_fd != repo_fd:
                os.close(current_fd)
            current_fd = child_fd
        if current_fd == repo_fd:
            return None, "tmp_dir cannot be the repository root"
        os.close(repo_fd)
        repo_fd = None
        pinned_fd = current_fd
        current_fd = None
        return PinnedTmpRoot(candidate, pinned_fd, tuple(identity)), None
    except OSError as exc:
        return None, f"tmp_dir cannot be pinned without following links ({exc})"
    finally:
        if current_fd is not None and current_fd != repo_fd:
            os.close(current_fd)
        if repo_fd is not None:
            os.close(repo_fd)


def _pinned_tmp_root_is_current(
    ctx: GateContext, pinned: PinnedTmpRoot
) -> bool:
    current, _reason = _open_pinned_tmp_root(ctx)
    if current is None:
        return False
    try:
        return current.identity == pinned.identity
    finally:
        os.close(current.fd)


def _docs_sync_state(ctx: GateContext, rel: str) -> str:
    """synced | never-synced | uncertain, via the docs orphan branch."""
    proc = ctx.git("ls-tree", "-r", "--name-only", "refs/heads/docs", "--", rel)
    if proc.returncode != 0:
        return "uncertain"
    return "synced" if proc.stdout.strip() else "never-synced"


def gate_docs_tmp_sweep(ctx: GateContext) -> GateResult:
    gate = "docs-tmp-sweep"
    pinned, root_error = _open_pinned_tmp_root(ctx)
    if pinned is None:
        return GateResult(
            gate,
            0,
            "docs/tmp sweep: removed=0, skipped=1, kept=0; skipped: "
            f"unsafe tmp root ({root_error}); cleanup skipped",
            warnings=[],
        )
    try:
        return _gate_docs_tmp_sweep_pinned(ctx, pinned)
    finally:
        os.close(pinned.fd)


def _gate_docs_tmp_sweep_pinned(
    ctx: GateContext, pinned: PinnedTmpRoot
) -> GateResult:
    done_session_fd: Optional[int] = None
    try:
        try:
            info = os.stat("done-session", dir_fd=pinned.fd, follow_symlinks=False)
            if stat_module.S_ISDIR(info.st_mode):
                done_session_fd = os.open(
                    "done-session",
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
                    dir_fd=pinned.fd,
                )
                opened = os.fstat(done_session_fd)
                if (opened.st_dev, opened.st_ino, opened.st_mode) != (
                    info.st_dev, info.st_ino, info.st_mode
                ):
                    os.close(done_session_fd)
                    done_session_fd = None
        except OSError:
            done_session_fd = None
        if done_session_fd is None:
            window = SessionWindow(False, None, None, None, [
                "done-session directory unavailable through pinned tmp root"
            ])
        else:
            window = derive_session_window(
                ctx.done_session_dir, ctx.repo_root, directory_fd=done_session_fd
            )
        return _gate_docs_tmp_sweep_with_window(
            ctx, pinned, done_session_fd, window
        )
    finally:
        if done_session_fd is not None:
            os.close(done_session_fd)


def _gate_docs_tmp_sweep_with_window(
    ctx: GateContext,
    pinned: PinnedTmpRoot,
    done_session_fd: Optional[int],
    window: SessionWindow,
) -> GateResult:
    gate = "docs-tmp-sweep"
    # Keep the lexical path for reports and read-only classification. Every
    # destructive operation below is relative to the pinned descriptor.
    tmp_dir = pinned.path
    removed: list[str] = []
    skipped: list[str] = []
    kept: list[str] = []
    prune_warnings: list[str] = []
    dead_root_drained: list[Path] = []
    dead_root_kept: list[Path] = []
    never_synced_survivors: list[tuple[str, Path, os.stat_result, PinnedTmpRoot]] = []
    horizon_days = _docs_tmp_deletion_horizon_days(ctx)
    now_epoch = time.time()

    def rel_of(path: Path) -> str:
        try:
            return str(path.relative_to(ctx.repo_root))
        except ValueError:
            return str(path)

    if stat_module.S_ISDIR(os.fstat(pinned.fd).st_mode):
        for entry in sorted(tmp_dir / name for name in os.listdir(pinned.fd)):
            name = entry.name
            if not _pinned_tmp_root_is_current(ctx, pinned):
                skipped.append(
                    f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                )
                break
            if name == "done-session":
                if not _pinned_tmp_root_is_current(ctx, pinned):
                    skipped.append(
                        f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                    )
                    break
                try:
                    if done_session_fd is None:
                        kept.append(str(entry) + " (directory unavailable; preserved)")
                        continue
                    done_info = os.stat(
                        name, dir_fd=pinned.fd, follow_symlinks=False
                    )
                    opened_done = os.fstat(done_session_fd)
                    if not stat_module.S_ISDIR(done_info.st_mode) or (
                        opened_done.st_dev, opened_done.st_ino, opened_done.st_mode
                    ) != (done_info.st_dev, done_info.st_ino, done_info.st_mode):
                        skipped.append(
                            f"{tmp_dir}/{name} (directory identity changed; cleanup skipped)"
                        )
                        break
                except OSError:
                    skipped.append(
                        f"{tmp_dir}/{name} (changed while opening; cleanup skipped)"
                    )
                    break
                _prune_done_session_markers(
                    ctx, entry, window, removed, kept, prune_warnings,
                    directory_fd=done_session_fd,
                    root_fd=pinned.fd,
                    root_is_current=lambda: _pinned_tmp_root_is_current(ctx, pinned),
                    dead_root_drained=dead_root_drained,
                    dead_root_kept=dead_root_kept,
                )
                if not _pinned_tmp_root_is_current(ctx, pinned):
                    skipped.append(
                        f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                    )
                    break
                continue
            try:
                entry_stat = os.stat(name, dir_fd=pinned.fd, follow_symlinks=False)
            except OSError:
                skipped.append(f"{tmp_dir}/{name} (identity unreadable; preserved)")
                continue
            if stat_module.S_ISDIR(entry_stat.st_mode) and name == "execute-plan":
                if not _pinned_tmp_root_is_current(ctx, pinned):
                    skipped.append(
                        f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                    )
                    break
                execute_fd = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
                    dir_fd=pinned.fd,
                )
                try:
                    opened = os.fstat(execute_fd)
                    if (opened.st_dev, opened.st_ino, opened.st_mode) != (
                        entry_stat.st_dev,
                        entry_stat.st_ino,
                        entry_stat.st_mode,
                    ):
                        skipped.append(
                            f"{tmp_dir}/{name} (directory changed while opening; cleanup skipped)"
                        )
                        break
                    _sweep_execute_plan_sessions(
                        ctx, execute_fd, entry, removed, kept,
                        pinned_fd=pinned.fd,
                        root_is_current=lambda: _pinned_tmp_root_is_current(ctx, pinned),
                        warnings=prune_warnings,
                    )
                finally:
                    os.close(execute_fd)
                if not _pinned_tmp_root_is_current(ctx, pinned):
                    skipped.append(
                        f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                    )
                    break
                continue
            if stat_module.S_ISREG(entry_stat.st_mode) and name.startswith("plan-requirements-") and name.endswith(".md"):
                slug = name[len("plan-requirements-") : -len(".md")]
                if (ctx.plans_completed_dir / (slug + ".md")).is_file():
                    if not _pinned_tmp_root_is_current(ctx, pinned):
                        skipped.append(
                            f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                        )
                        break
                    quarantined, reason = _quarantine_candidate(
                        pinned.fd, pinned.fd, name, entry_stat
                    )
                    if quarantined is None:
                        skipped.append(f"{rel_of(entry)} ({reason})")
                        continue
                    if reason is not None:
                        location = _quarantine_location(quarantined)
                        skipped.append(f"{rel_of(entry)} ({reason}; retained at {location})")
                        continue
                    try:
                        current = os.stat(
                            quarantined.entry_name,
                            dir_fd=quarantined.directory_fd,
                            follow_symlinks=False,
                        )
                        current_pending = _pending_plan_session_names(
                            ctx.plans_dir, ctx.plans_completed_dir
                        )
                        archived = (
                            slug not in current_pending
                            and (ctx.plans_completed_dir / (slug + ".md")).is_file()
                        )
                        if _candidate_identity(current) != _candidate_identity(entry_stat):
                            location = _quarantine_location(quarantined)
                            skipped.append(
                                f"{rel_of(entry)} (identity changed; retained at {location})"
                            )
                        elif not archived:
                            location = _restore_quarantined_candidate(
                                pinned.fd, pinned.fd, name, quarantined
                            )
                            kept.append(
                                f"{rel_of(entry)} (owning plan still pending)"
                                + (f"; retained at {location}" if location else "")
                            )
                        elif not _pinned_tmp_root_is_current(ctx, pinned):
                            location = _restore_quarantined_candidate(
                                pinned.fd, pinned.fd, name, quarantined
                            )
                            skipped.append(
                                f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                                + (f"; retained at {location}" if location else "")
                            )
                            break
                        else:
                            _discard_quarantined_candidate(pinned.fd, quarantined)
                            removed.append(rel_of(entry))
                    except OSError:
                        location = _restore_quarantined_candidate(
                            pinned.fd, pinned.fd, name, quarantined
                        )
                        kept.append(
                            f"{rel_of(entry)} (removal failed; preserved)"
                            + (f" at {location}" if location else "")
                        )
                    if not _pinned_tmp_root_is_current(ctx, pinned):
                        skipped.append(
                            f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                        )
                        break
                else:
                    kept.append(rel_of(entry) + " (owning plan still pending)")
                continue
            if stat_module.S_ISDIR(entry_stat.st_mode) and (
                name.startswith(PROTECTED_SCRATCH_PREFIXES) or name in PROTECTED_SCRATCH_DIRS
            ):
                kept.append(rel_of(entry) + " (protected scratch; owning skill cleans up)")
                continue
            if stat_module.S_ISREG(entry_stat.st_mode) and not (
                name.startswith(PROTECTED_SCRATCH_PREFIXES)
                or name in PROTECTED_SCRATCH_DIRS
            ) and not _synced_shape_class(name):
                # The never-synced scratch arm (plan
                # docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md
                # Task 1): every top-level regular file outside the synced
                # shape classes. Cheap pure guards first; the docs-branch
                # state and the citation hold resolve batched post-loop.
                verdict, keep_reason = _classify_never_synced_candidate(
                    entry_stat, window, horizon_days, now_epoch
                )
                if verdict == "keep":
                    kept.append(f"{rel_of(entry)} ({keep_reason})")
                else:
                    never_synced_survivors.append((name, entry, entry_stat, pinned))
                continue
            if stat_module.S_ISREG(entry_stat.st_mode) and _synced_shape_class(name):
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
                        mtime = os.stat(name, dir_fd=pinned.fd, follow_symlinks=False).st_mtime
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
                    if not _pinned_tmp_root_is_current(ctx, pinned):
                        skipped.append(
                            f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                        )
                        break
                    quarantined, reason = _quarantine_candidate(
                        pinned.fd, pinned.fd, name, entry_stat
                    )
                    if quarantined is None:
                        skipped.append(f"{rel_of(entry)} ({reason})")
                        continue
                    if reason is not None:
                        location = _quarantine_location(quarantined)
                        skipped.append(f"{rel_of(entry)} ({reason}; retained at {location})")
                        continue
                    try:
                        current = os.stat(
                            quarantined.entry_name,
                            dir_fd=quarantined.directory_fd,
                            follow_symlinks=False,
                        )
                        final_sync_state = _docs_sync_state(ctx, rel_of(entry))
                        if _candidate_identity(current) != _candidate_identity(entry_stat):
                            location = _quarantine_location(quarantined)
                            skipped.append(
                                f"{rel_of(entry)} (identity changed; retained at {location})"
                            )
                        elif final_sync_state != "synced":
                            location = _restore_quarantined_candidate(
                                pinned.fd, pinned.fd, name, quarantined
                            )
                            reason = (
                                "docs branch presence uncertain; never guessing"
                                if final_sync_state == "uncertain"
                                else "never synced to the docs branch; removal would be permanent"
                            )
                            skipped.append(
                                f"{rel_of(entry)} ({reason})"
                                + (f"; retained at {location}" if location else "")
                            )
                        elif not window.anchored or window.start_epoch is None:
                            location = _restore_quarantined_candidate(
                                pinned.fd, pinned.fd, name, quarantined
                            )
                            skipped.append(
                                f"{rel_of(entry)} (session window became unanchorable; preserved)"
                                + (f" at {location}" if location else "")
                            )
                        elif current.st_mtime >= window.start_epoch:
                            location = _restore_quarantined_candidate(
                                pinned.fd, pinned.fd, name, quarantined
                            )
                            skipped.append(
                                f"{rel_of(entry)} (same-inode update inside the session window; preserved)"
                                + (f" at {location}" if location else "")
                            )
                        elif not _pinned_tmp_root_is_current(ctx, pinned):
                            location = _restore_quarantined_candidate(
                                pinned.fd, pinned.fd, name, quarantined
                            )
                            skipped.append(
                                f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                                + (f"; retained at {location}" if location else "")
                            )
                            break
                        else:
                            _discard_quarantined_candidate(pinned.fd, quarantined)
                            removed.append(rel_of(entry))
                    except OSError:
                        location = _restore_quarantined_candidate(
                            pinned.fd, pinned.fd, name, quarantined
                        )
                        kept.append(
                            f"{rel_of(entry)} (removal failed; preserved)"
                            + (f" at {location}" if location else "")
                        )
                    if not _pinned_tmp_root_is_current(ctx, pinned):
                        skipped.append(
                            f"{tmp_dir} (pinned root identity changed; cleanup skipped)"
                        )
                        break
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

    # The never-synced scratch arm's post-loop resolution (plan
    # docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md Task 1):
    # the batched docs-branch listing and the closeout-reference hold run
    # once for the whole candidate set, then the posture decides between
    # draining (quarantine flow, mirroring the synced arm's rechecks) and
    # reporting would-drain rows that unlink nothing.
    posture = _docs_tmp_drain_posture(ctx)
    if never_synced_survivors:
        if posture == "off":
            for name, entry, _entry_stat, _pinned in never_synced_survivors:
                kept.append(f"{rel_of(entry)} (drain arms off; never-synced scratch kept)")
        else:
            hits = _batched_docs_branch_hits(
                ctx, [rel_of(entry) for _, entry, _, _ in never_synced_survivors]
            )
            if hits is None:
                for _name, entry, _entry_stat, _pinned in never_synced_survivors:
                    kept.append(
                        f"{rel_of(entry)} (docs-branch listing failed; never guessing)"
                    )
            else:
                drainable: list[tuple[str, Path, os.stat_result, PinnedTmpRoot]] = []
                for name, entry, entry_stat, pinned in never_synced_survivors:
                    if rel_of(entry) in hits:
                        kept.append(
                            f"{rel_of(entry)} (never-synced classification stale; "
                            "now present on the docs branch)"
                        )
                    else:
                        drainable.append((name, entry, entry_stat, pinned))

                def _consume_never_synced(referenced: Optional[set[str]]) -> None:
                    # Runs exactly once on every return path of the hold:
                    # inside the merge-lock span with the verified cited set,
                    # or with None on each unverifiable path. Only the
                    # verified path may unlink, and only in the 'on' posture;
                    # 'report-only' never unlinks.
                    if referenced is None:
                        for _name, entry, _entry_stat, _pinned in drainable:
                            kept.append(
                                f"{rel_of(entry)} (closeout-reference hold "
                                "unverified; never guessing)"
                            )
                        return
                    root_changed = False
                    for name, entry, entry_stat, pinned in drainable:
                        try:
                            cited = str(Path(os.path.realpath(entry))) in referenced
                        except OSError:
                            cited = False
                        if cited:
                            kept.append(
                                f"{rel_of(entry)} (cited by a live closeout "
                                "manifest; kept)"
                            )
                            continue
                        if posture == "report-only":
                            kept.append(
                                f"{rel_of(entry)} (would-drain: "
                                f"{DOCS_TMP_NEVER_SYNCED_DRAIN_REASON}; "
                                f"posture report-only)"
                            )
                            continue
                        if not _pinned_tmp_root_is_current(ctx, pinned):
                            # Report every stranded remainder before breaking,
                            # so the pass never undercounts on the safety path.
                            for rest_name, rest_entry, _rest_stat, _rest_pinned in (
                                drainable[drainable.index((name, entry, entry_stat, pinned)):]
                            ):
                                kept.append(
                                    f"{rel_of(rest_entry)} (pinned root identity "
                                    "changed; cleanup skipped)"
                                )
                            break
                        try:
                            current = os.stat(
                                name, dir_fd=pinned.fd, follow_symlinks=False
                            )
                        except OSError:
                            kept.append(f"{rel_of(entry)} (recheck stat failed; kept)")
                            continue
                        if _candidate_identity(current) != _candidate_identity(entry_stat):
                            kept.append(
                                f"{rel_of(entry)} (identity changed during the "
                                "sweep; kept)"
                            )
                            continue
                        quarantined, quarantine_reason = _quarantine_candidate(
                            pinned.fd, pinned.fd, name, current
                        )
                        if quarantined is None:
                            kept.append(
                                f"{rel_of(entry)} ({quarantine_reason}; kept)"
                            )
                            continue
                        if quarantine_reason is not None:
                            location = _quarantine_location(quarantined)
                            kept.append(
                                f"{rel_of(entry)} ({quarantine_reason}; "
                                f"retained at {location})"
                            )
                            continue
                        try:
                            final_stat = os.stat(
                                quarantined.entry_name,
                                dir_fd=quarantined.directory_fd,
                                follow_symlinks=False,
                            )
                            if _candidate_identity(final_stat) != _candidate_identity(
                                entry_stat
                            ):
                                location = _quarantine_location(quarantined)
                                kept.append(
                                    f"{rel_of(entry)} (identity changed; retained "
                                    f"at {location})"
                                )
                            elif final_stat.st_mtime >= window.start_epoch:
                                location = _restore_quarantined_candidate(
                                    pinned.fd, pinned.fd, name, quarantined
                                )
                                kept.append(
                                    f"{rel_of(entry)} (same-inode update inside "
                                    "the session window; preserved)"
                                    + (f" at {location}" if location else "")
                                )
                            else:
                                _discard_quarantined_candidate(pinned.fd, quarantined)
                                removed.append(
                                    rel_of(entry)
                                    + f" [{DOCS_TMP_NEVER_SYNCED_DRAIN_REASON}]"
                                )
                        except OSError:
                            location = _restore_quarantined_candidate(
                                pinned.fd, pinned.fd, name, quarantined
                            )
                            kept.append(
                                f"{rel_of(entry)} (removal failed; preserved)"
                                + (f" at {location}" if location else "")
                            )

                _hold_referenced, hold_warnings = _closeout_reference_hold(
                    ctx, _consume_never_synced
                )
                prune_warnings.extend(hold_warnings)

    kept_warnings: list[str] = []
    parts = [
        f"removed={len(removed)}",
        f"skipped={len(skipped)}",
        f"kept={len(kept)}",
        f"dead-root-drained={len(dead_root_drained)}",
        f"dead-root-kept={len(dead_root_kept)}",
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
    return GateResult(gate, 0, message, warnings=kept_warnings + prune_warnings)


def _closeout_reference_hold(
    ctx: GateContext,
    consume: Optional[Callable[[Optional[set[str]]], None]] = None,
) -> tuple[Optional[set[str]], list[str]]:
    """The merge-locked closeout-reference hold behind the gate-report prune
    arm (plan 2026-10-29-done-gate-report-retention Task 2).

    ``consume``, when given, runs exactly once with the final ``referenced``
    value on every return path: inside this merge-lock span on the verified
    path, so the gate-report prune arm's unlink loop shares the lock with the
    aged set's lookup (one atomic span: a publisher that acquires the lock
    next can never have a freshly written citation deleted by a sweep that
    scanned before the publisher's manifest landed), and outside the span on
    each unverifiable path, where ``consume`` receives ``None`` and the
    caller's arm prunes nothing. An exception out of ``consume`` on the
    verified path still releases the lock (the release stays in
    ``finally``).

    Returns ``(referenced, warnings)``. ``referenced`` is None exactly when
    the hold could not be verified; the sibling helpers are unavailable
    (this lib deployed beside an older driver copy), the
    ``worktree-closeout-migrate`` merge lock could not be acquired (launch
    failure, refusal, or missing MERGE_LOCK ownership exports), the primary
    checkout could not be resolved, or the worktree registration could not be
    read; the caller must then prune nothing (never prune without a
    verified hold). Otherwise ``referenced`` is the possibly-empty set of
    resolved filesystem paths that a live registered-worktree closeout
    manifest still cites as a verified ``migrated``/``renamed`` destination.

    The manifest set is the supported one (plan Terms): migration-shaped JSON
    under both the run-owner (this checkout's facts-resolved) and the
    resolved primary checkout temporary roots, in their ``execute-plan/`` and
    ``done-session/`` subtrees; canonical and legacy plan-session files,
    run-ID ``worktree-migrate-baseline-<id>-manifest.json`` skeletons, and
    explicitly placed operands under those roots (the subtree scan covers
    every JSON there; ``_closeout_manifest_candidate``'s per-plan canonical-
    then-legacy selection needs a plan operand this cross-session sweep does
    not have, so the enumeration is by location and the per-file rules stay
    single-homed in the resolver). Resolution reuses Task 1's
    ``_resolve_closeout_reference_state``: any read/shape/destinations error
    is reference-less with one warning and stays age-prunable (no
    normalization, no new refusal class), and a manifest without a usable
    branch record is the consumer's named legacy skip shape, silently
    reference-less. A manifest is live for registered-worktree closeout
    exactly while a registered worktree of the repository is bound to its
    latest recorded branch (the consumer's identity rule, independent of the
    manifest's ``source`` field), so an ``unknown-ref`` recovery keeps its
    report (the registration persists while the ref is being resolved) and
    after successful worktree removal no entry matches and the report is
    age-prunable again. Branch-only ``unknown-ref`` retention is explicitly
    deferred to the linked backlog item."""
    warnings: list[str] = []

    def finish(
        referenced: Optional[set[str]],
    ) -> tuple[Optional[set[str]], list[str]]:
        """Hand ``consume`` the final ``referenced`` value exactly once, on
        every return path: inside the merge-lock span on the verified path
        (the return expression evaluates before ``finally`` releases the
        lock), and outside it (pruning nothing) on each unverifiable one."""
        if consume is not None:
            consume(referenced)
        return referenced, warnings

    try:
        from worktree_closeout_migrate import (  # stale deployed siblings degrade to skip, never to a blind prune
            _MIGRATE_MERGE_LABEL,
            _facts_tmp_root,
            _merge_lock_acquire,
            _merge_lock_release,
            _parse_worktree_entries,
            _resolve_closeout_reference_state,
        )
    except Exception as exc:
        warnings.append(
            "docs-tmp-sweep: worktree_closeout_migrate helpers unavailable; "
            f"aged gate-report pruning skipped this run ({exc})"
        )
        return finish(None)
    exports, refused = _merge_lock_acquire(ctx.repo_root, _MIGRATE_MERGE_LABEL)
    if exports is None:
        evidence = (
            "; ".join(line.strip() for line in refused if line.strip())[:200]
            or "merge-acquire refused"
        )
        warnings.append(
            "docs-tmp-sweep: worktree-closeout-migrate merge lock not "
            "acquired; aged gate-report pruning skipped this run "
            f"({evidence})"
        )
        return finish(None)
    try:
        primary, primary_err = _resolve_primary_checkout(ctx)
        if primary is None:
            warnings.append(
                "docs-tmp-sweep: primary checkout unresolved; aged "
                "gate-report pruning skipped this run "
                f"({(primary_err or '').strip()[:200]})"
            )
            return finish(None)
        try:
            entries = _parse_worktree_entries(primary)
        except Exception as exc:
            warnings.append(
                "docs-tmp-sweep: worktree registration unreadable; aged "
                f"gate-report pruning skipped this run ({exc})"
            )
            return finish(None)
        roots: list[Path] = []
        seen_roots: set[Path] = set()
        for root in (ctx.tmp_dir, _facts_tmp_root(primary)):
            resolved = Path(root)
            try:
                resolved = resolved.resolve()
            except OSError:
                pass
            if resolved not in seen_roots:
                seen_roots.add(resolved)
                roots.append(resolved)
        referenced: set[str] = set()
        for root in roots:
            for pattern in (
                "execute-plan/*/*.json",
                "execute-plan/*.json",
                "done-session/*.json",
            ):
                for manifest_path in sorted(root.glob(pattern)):
                    if not manifest_path.is_file():
                        continue
                    state = _resolve_closeout_reference_state(manifest_path)
                    if state["read_error"] is not None:
                        warnings.append(
                            "docs-tmp-sweep: closeout manifest unreadable; "
                            "its verified destinations stay age-prunable: "
                            f"{manifest_path} ({state['read_error']})"
                        )
                        continue
                    if (
                        state["shape_error"] is not None
                        or state["destinations_error"] is not None
                    ):
                        exc = state["shape_error"] or state["destinations_error"]
                        warnings.append(
                            "docs-tmp-sweep: closeout manifest shape "
                            "unsupported; its verified destinations stay "
                            f"age-prunable: {manifest_path} ({exc})"
                        )
                        continue
                    recorded = state["recorded"]
                    if not recorded:
                        # The consumer's legacy skip shape: no branch record,
                        # nothing live to retain for.
                        continue
                    if not any(
                        entry.get("branch") == recorded for entry in entries
                    ):
                        # No registered worktree is bound to the recorded
                        # branch: the worktree closeout has completed (or the
                        # record was branch-only, whose retention is
                        # deferred); age-prunable again.
                        continue
                    for destination in state["verified_destinations"]:
                        try:
                            referenced.add(
                                str((primary / destination).resolve())
                            )
                        except (TypeError, ValueError, OSError) as exc:
                            warnings.append(
                                "docs-tmp-sweep: closeout manifest carries an "
                                "unresolvable verified destination; it stays "
                                f"age-prunable: {manifest_path} ({exc})"
                            )
        return finish(referenced)
    finally:
        _merge_lock_release(ctx.repo_root, exports)


def _snapshot_candidate_checkout_roots(
    ctx: GateContext,
) -> tuple[list[Path], bool, list[str]]:
    """The per-pass candidate-root snapshot (plan
    docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md Task 2): the
    primary checkout root, the registered worktree entries via the existing
    worktree-entry parsing, and the sibling worktree-root families. The
    second element is False exactly when an enumeration leg failed
    (registration unreadable, sibling scan error); the caller's dead-root arm
    then prunes nothing that pass."""
    warnings: list[str] = []
    roots: list[Path] = []
    seen: set[str] = set()

    def add(raw: Path) -> None:
        try:
            resolved = Path(os.path.realpath(str(raw)))
        except OSError:
            resolved = Path(raw)
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            roots.append(resolved)

    primary, _primary_err = _resolve_primary_checkout(ctx)
    if primary is not None:
        add(primary)
        try:
            from worktree_closeout_migrate import _parse_worktree_entries

            for entry in _parse_worktree_entries(primary):
                path = entry.get("path")
                if path:
                    add(Path(path))
        except Exception as exc:
            warnings.append(
                "docs-tmp-sweep: worktree registration unreadable; the "
                f"dead-root snapshot is unverified this pass ({exc})"
            )
            return roots, False, warnings
    else:
        warnings.append(
            "docs-tmp-sweep: primary checkout unresolved; the dead-root "
            "snapshot is unverified this pass"
        )
        return roots, False, warnings
    family = primary.parent / (primary.name + "-worktrees")
    try:
        if family.is_dir():
            for child in sorted(family.iterdir()):
                add(child)
    except OSError as exc:
        warnings.append(
            "docs-tmp-sweep: sibling worktree-root family scan failed; the "
            f"dead-root snapshot is unverified this pass ({exc})"
        )
        return roots, False, warnings
    return roots, True, warnings


def _marker_root_matches_candidates(
    recorded_root: str, candidates: list[Path]
) -> bool:
    """The parser's two-arm root match against the snapshot: a 64-hex token
    compares by identity digest only; a legacy raw path compares by realpath
    (plan Task 2)."""
    if re.fullmatch(r"[0-9a-f]{64}", recorded_root):
        return any(
            _marker_digest_matches(recorded_root, candidate)
            for candidate in candidates
        )
    try:
        recorded_real = os.path.realpath(recorded_root)
    except OSError:
        return False
    return any(
        os.path.realpath(str(candidate)) == recorded_real for candidate in candidates
    )


def _lenient_foreign_marker(content: str) -> Optional[tuple[float, str]]:
    """The (epoch, recorded_root) of a structurally well-formed marker whose
    root does not confirm as this repo; None for malformed content, which the
    dead-root arm never prunes. Shares the strict parser's structural parse
    (``_marker_struct``) so the grammar lives once."""
    struct = _marker_struct(content)
    if struct is None:
        return None
    return struct[0], struct[2]


def _prune_done_session_markers(
    ctx: GateContext,
    done_session: Path,
    window: SessionWindow,
    removed: list[str],
    kept: list[str],
    warnings: list[str],
    directory_fd: int,
    root_fd: int,
    root_is_current: Callable[[], bool],
    dead_root_drained: list[Path],
    dead_root_kept: list[Path],
) -> None:
    """Remove run-start-* markers strictly older than the previous-run anchor;
    the anchor and the current-run marker are immune; an unanchorable window
    or unparseable content prunes nothing (never guess by recency). The same
    window rule governs the bounded reports' gate-reports home: a file whose
    mtime sits strictly older than the anchor (outside the current session
    window) is removed, a file inside the window stays, and an unreadable
    mtime keeps the file (never guessing). An aged report still cited as a
    verified migrated/renamed destination by a live registered-worktree
    closeout manifest is retained for the closeout consumer (plan
    2026-10-29-done-gate-report-retention Task 2): the aged set's lookup and
    unlink share the ``worktree-closeout-migrate`` merge lock, and when the
    hold cannot be verified (lock unavailable, primary unresolved, helpers
    missing) the sweep warns and prunes nothing; never without a verified
    hold. Retention ends with the closeout: after successful worktree removal
    no registration is bound to the recorded branch and the report is
    age-prunable again."""
    if not window.anchored or window.anchor is None:
        kept.append(str(done_session) + " (window unanchorable; markers immune)")
        return
    anchor_epoch = window.anchor.epoch
    # The dead-root arm's per-pass state: the snapshot builds lazily on the
    # first well-formed foreign marker; candidates drain in one
    # citation-hold merge-lock span after the loop (plan Task 2).
    snapshot_roots: Optional[list[Path]] = None
    snapshot_verified: bool = False
    snapshot_warnings: list[str] = []
    dead_candidates: list[tuple[str, Path, Optional[os.stat_result], float]] = []
    marker_names = sorted(
        name for name in os.listdir(directory_fd) if name.startswith("run-start-")
    )
    for marker_name in marker_names:
        marker = done_session / marker_name
        if not root_is_current():
            kept.append(str(done_session) + " (pinned root identity changed; cleanup skipped)")
            return
        marker_identity: Optional[os.stat_result] = None
        marker_fd: Optional[int] = None
        content_text: Optional[str] = None
        try:
            marker_fd = os.open(
                marker_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd
            )
            marker_info = os.fstat(marker_fd)
            if not stat_module.S_ISREG(marker_info.st_mode):
                raise OSError("marker changed type")
            marker_identity = marker_info
            with os.fdopen(marker_fd, "r", encoding="utf-8") as stream:
                marker_fd = None
                content = stream.read()
            content_text = content
            parsed = _parse_marker_content(marker, content, ctx.repo_root)
        except (OSError, UnicodeError):
            parsed = None
        finally:
            if marker_fd is not None:
                os.close(marker_fd)
        if parsed is None:
            # A cross-repo or unparseable marker is never pruned by recency;
            # the dead-root arm (plan
            # docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md
            # Task 2) owns the well-formed foreign pre-anchor subset below.
            foreign = (
                _lenient_foreign_marker(content_text)
                if content_text is not None
                else None
            )
            if foreign is None:
                kept.append(str(marker) + " (content not confirmable as this repo)")
                continue
            foreign_epoch, foreign_root = foreign
            if snapshot_roots is None:
                snapshot_roots, snapshot_verified, snapshot_warnings = (
                    _snapshot_candidate_checkout_roots(ctx)
                )
                warnings.extend(snapshot_warnings)
            if not snapshot_verified:
                kept.append(
                    str(marker)
                    + " (candidate-root snapshot unverified; dead-root drain "
                    "skipped this pass)"
                )
                dead_root_kept.append(marker)
                continue
            if _marker_root_matches_candidates(foreign_root, snapshot_roots):
                kept.append(
                    str(marker)
                    + " (live-root cross-repo marker; fenced by the candidate-root "
                    "snapshot)"
                )
                dead_root_kept.append(marker)
                continue
            if not foreign_epoch < anchor_epoch:
                kept.append(
                    str(marker)
                    + " (cross-repo marker inside the session window; immune)"
                )
                dead_root_kept.append(marker)
                continue
            dead_candidates.append((marker_name, marker, marker_identity, foreign_epoch))
            continue
        if parsed.epoch < anchor_epoch:
            if not root_is_current():
                kept.append(str(done_session) + " (pinned root identity changed; cleanup skipped)")
                return
            if marker_identity is None:
                kept.append(str(marker) + " (quarantine unavailable; preserved)")
                continue
            quarantined, quarantine_error = _quarantine_candidate(
                root_fd, directory_fd, marker_name, marker_identity
            )
            if quarantined is None:
                kept.append(str(marker) + f" ({quarantine_error})")
                continue
            if quarantine_error is not None:
                location = _quarantine_location(quarantined)
                kept.append(str(marker) + f" ({quarantine_error}; retained at {location})")
                continue
            try:
                marker_fd = os.open(
                    quarantined.entry_name,
                    os.O_RDONLY | os.O_NOFOLLOW,
                    dir_fd=quarantined.directory_fd,
                )
                try:
                    current_info = os.fstat(marker_fd)
                    with os.fdopen(marker_fd, "r", encoding="utf-8") as stream:
                        marker_fd = -1
                        current_content = stream.read()
                finally:
                    if marker_fd >= 0:
                        os.close(marker_fd)
                current_marker = _parse_marker_content(
                    marker, current_content, ctx.repo_root
                )
                if (
                    _candidate_identity(current_info) != _candidate_identity(marker_identity)
                    or current_marker is None
                    or current_marker.epoch >= anchor_epoch
                ):
                    location = _restore_quarantined_candidate(
                        root_fd, directory_fd, marker_name, quarantined
                    )
                    kept.append(
                        str(marker) + " (marker changed or entered the protected window)"
                        + (f"; retained at {location}" if location else "")
                    )
                elif not root_is_current():
                    location = _restore_quarantined_candidate(
                        root_fd, directory_fd, marker_name, quarantined
                    )
                    kept.append(
                        str(marker) + " (pinned root identity changed; cleanup skipped)"
                        + (f"; retained at {location}" if location else "")
                    )
                else:
                    _discard_quarantined_candidate(root_fd, quarantined)
                    removed.append(str(marker))
            except OSError:
                location = _restore_quarantined_candidate(
                    root_fd, directory_fd, marker_name, quarantined
                )
                kept.append(
                    str(marker) + " (marker removal failed; preserved)"
                    + (f" at {location}" if location else "")
                )
        else:
            kept.append(str(marker) + " (anchor or current run; immune)")
    if dead_candidates:
        posture = _docs_tmp_drain_posture(ctx)

        def _drain_dead_roots(referenced: Optional[set[str]]) -> None:
            # The unlink arm, invoked by ``_closeout_reference_hold`` exactly
            # once on every return path: inside the merge-lock span on the
            # verified path, with None on each unverifiable one. Only the
            # verified path unlinks, and only in the 'on' posture.
            if referenced is None:
                for _name, marker, _identity, _epoch in dead_candidates:
                    kept.append(
                        str(marker)
                        + " (dead-root marker; prune skipped: closeout reference "
                        "hold unverified)"
                    )
                    dead_root_kept.append(marker)
                return
            for marker_name_d, marker, marker_identity, dead_epoch in dead_candidates:
                if not root_is_current():
                    # Report every stranded remainder before returning, so the
                    # census never undercounts on the safety path.
                    for rest_marker in dead_candidates[dead_candidates.index(
                        (marker_name_d, marker, marker_identity, dead_epoch)
                    ):]:
                        kept.append(
                            str(rest_marker[1])
                            + " (pinned root identity changed; cleanup skipped)"
                        )
                        dead_root_kept.append(rest_marker[1])
                    return
                if posture == "off":
                    kept.append(
                        str(marker) + " (drain arms off; dead-root marker kept)"
                    )
                    dead_root_kept.append(marker)
                    continue
                if posture == "report-only":
                    kept.append(
                        str(marker)
                        + " (would-drain: dead-root marker (root absent, "
                        "pre-window); posture report-only)"
                    )
                    dead_root_kept.append(marker)
                    continue
                if marker_identity is None:
                    kept.append(str(marker) + " (quarantine unavailable; preserved)")
                    dead_root_kept.append(marker)
                    continue
                quarantined, quarantine_error = _quarantine_candidate(
                    root_fd, directory_fd, marker_name_d, marker_identity
                )
                if quarantined is None:
                    kept.append(str(marker) + f" ({quarantine_error})")
                    dead_root_kept.append(marker)
                    continue
                if quarantine_error is not None:
                    location = _quarantine_location(quarantined)
                    kept.append(
                        str(marker) + f" ({quarantine_error}; retained at {location})"
                    )
                    dead_root_kept.append(marker)
                    continue
                try:
                    marker_fd_d = os.open(
                        quarantined.entry_name,
                        os.O_RDONLY | os.O_NOFOLLOW,
                        dir_fd=quarantined.directory_fd,
                    )
                    try:
                        current_info = os.fstat(marker_fd_d)
                        with os.fdopen(marker_fd_d, "r", encoding="utf-8") as stream:
                            marker_fd_d = -1
                            current_content = stream.read()
                    finally:
                        if marker_fd_d >= 0:
                            os.close(marker_fd_d)
                    current_foreign = _lenient_foreign_marker(current_content)
                    if (
                        _candidate_identity(current_info) != _candidate_identity(marker_identity)
                        or current_foreign is None
                        or current_foreign[0] != dead_epoch
                        or current_foreign[0] >= anchor_epoch
                    ):
                        location = _restore_quarantined_candidate(
                            root_fd, directory_fd, marker_name_d, quarantined
                        )
                        kept.append(
                            str(marker)
                            + " (marker changed or entered the protected window)"
                            + (f"; retained at {location}" if location else "")
                        )
                        dead_root_kept.append(marker)
                    elif not root_is_current():
                        location = _restore_quarantined_candidate(
                            root_fd, directory_fd, marker_name_d, quarantined
                        )
                        kept.append(
                            str(marker)
                            + " (pinned root identity changed; cleanup skipped)"
                            + (f"; retained at {location}" if location else "")
                        )
                        dead_root_kept.append(marker)
                    else:
                        _discard_quarantined_candidate(root_fd, quarantined)
                        removed.append(
                            str(marker) + " [dead-root marker (root absent, pre-window)]"
                        )
                        dead_root_drained.append(marker)
                except OSError:
                    location = _restore_quarantined_candidate(
                        root_fd, directory_fd, marker_name_d, quarantined
                    )
                    kept.append(
                        str(marker) + " (marker removal failed; preserved)"
                        + (f" at {location}" if location else "")
                    )
                    dead_root_kept.append(marker)

        _dead_hold, dead_hold_warnings = _closeout_reference_hold(ctx, _drain_dead_roots)
        warnings.extend(dead_hold_warnings)
    gate_reports = done_session / GATE_REPORTS_DIRNAME
    try:
        reports_fd = os.open(
            GATE_REPORTS_DIRNAME,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
            dir_fd=directory_fd,
        )
    except OSError:
        return
    report_names = sorted(os.listdir(reports_fd))
    aged: list[tuple[str, Path, os.stat_result]] = []
    for report_name in report_names:
        report_file = gate_reports / report_name
        try:
            info = os.stat(report_name, dir_fd=reports_fd, follow_symlinks=False)
            if not stat_module.S_ISREG(info.st_mode):
                continue
            mtime = info.st_mtime
        except OSError:
            kept.append(str(report_file) + " (mtime unreadable; never guessing)")
            continue
        if mtime < anchor_epoch:
            aged.append((report_name, report_file, info))
        else:
            kept.append(str(report_file) + " (inside the session window; immune)")
    if not aged:
        os.close(reports_fd)
        return

    def prune_within_hold(referenced: Optional[set[str]]) -> None:
        """The unlink arm, invoked by ``_closeout_reference_hold`` with the
        final ``referenced`` value: on the verified path it runs inside the
        merge-lock span, so the aged set's classification and its unlinks are
        one atomic span under the lock and a publisher's manifest cannot land
        between the scan and the unlink (plan
        2026-10-29-done-gate-report-retention Task 2); on an unverifiable
        hold it prunes nothing (the skip lines below)."""
        if referenced is None:
            # The hold could not be verified: never prune without one.
            for _report_name, report_file, _info in aged:
                kept.append(
                    str(report_file)
                    + " (aged; prune skipped: closeout reference hold unverified)"
                )
            return
        for report_name, report_file, report_identity in aged:
            if not root_is_current():
                kept.append(str(done_session) + " (pinned root identity changed; cleanup skipped)")
                return
            try:
                resolved_report = os.path.abspath(report_file)
            except OSError:
                kept.append(
                    str(report_file) + " (path unresolvable; never guessing)"
                )
                continue
            if not root_is_current():
                kept.append(str(done_session) + " (pinned root identity changed; cleanup skipped)")
                return
            if resolved_report in referenced:
                kept.append(
                    str(report_file)
                    + " (retained: cited by a live registered-worktree closeout "
                    "manifest)"
                )
                continue
            quarantined, quarantine_error = _quarantine_candidate(
                root_fd, reports_fd, report_name, report_identity
            )
            if quarantined is None:
                kept.append(str(report_file) + f" ({quarantine_error})")
                continue
            if quarantine_error is not None:
                location = _quarantine_location(quarantined)
                kept.append(
                    str(report_file) + f" ({quarantine_error}; retained at {location})"
                )
                continue
            try:
                current = os.stat(
                    quarantined.entry_name,
                    dir_fd=quarantined.directory_fd,
                    follow_symlinks=False,
                )
                if (
                    _candidate_identity(current) != _candidate_identity(report_identity)
                    or current.st_mtime >= anchor_epoch
                ):
                    location = _restore_quarantined_candidate(
                        root_fd, reports_fd, report_name, quarantined
                    )
                    kept.append(
                        str(report_file) + " (report changed or entered the session window)"
                        + (f"; retained at {location}" if location else "")
                    )
                elif root_is_current is not None and not root_is_current():
                    location = _restore_quarantined_candidate(
                        root_fd, reports_fd, report_name, quarantined
                    )
                    kept.append(
                        str(report_file) + " (pinned root identity changed; cleanup skipped)"
                        + (f"; retained at {location}" if location else "")
                    )
                else:
                    _discard_quarantined_candidate(root_fd, quarantined)
                    removed.append(str(report_file))
            except OSError:
                location = _restore_quarantined_candidate(
                    root_fd, reports_fd, report_name, quarantined
                )
                kept.append(
                    str(report_file) + " (report removal failed; preserved)"
                    + (f" at {location}" if location else "")
                )

    try:
        _, hold_warnings = _closeout_reference_hold(ctx, prune_within_hold)
        warnings.extend(hold_warnings)
    finally:
        os.close(reports_fd)


def _pending_plan_session_names(
    plans_dir: Path, plans_completed_dir: Path
) -> set[str]:
    """Pending-name set for the execute-plan session sweep: every pending
    plan's full file stem plus, for date-prefixed plans, the date-stripped
    canonical session slug (execute-plan Step 0.4), since live sessions name
    their directories by the no-date slug while the plan file is
    date-prefixed."""
    names: set[str] = set()
    for plan in plans_dir.rglob("*.md"):
        if not plan.is_file() or _is_relative_to(plan, plans_completed_dir):
            continue
        names.add(plan.stem)
        m = re.match(r"\d{4}-\d{2}-\d{2}-(.+)", plan.stem)
        if m:
            names.add(m.group(1))
    return names


def _remove_tree_at(parent_fd: int, name: str) -> None:
    """Remove one entry using only descriptor-relative no-follow operations."""
    before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat_module.S_ISDIR(before.st_mode):
        os.unlink(name, dir_fd=parent_fd)
        return
    child_fd = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
        dir_fd=parent_fd,
    )
    try:
        opened = os.fstat(child_fd)
        if (opened.st_dev, opened.st_ino, opened.st_mode) != (
            before.st_dev,
            before.st_ino,
            before.st_mode,
        ):
            raise OSError("directory changed while opening")
        for child in os.listdir(child_fd):
            _remove_tree_at(child_fd, child)
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino, current.st_mode) != (
            opened.st_dev,
            opened.st_ino,
            opened.st_mode,
        ):
            raise OSError("directory identity changed before removal")
        os.rmdir(name, dir_fd=parent_fd)
    finally:
        os.close(child_fd)


def _branch_ref_resolves(ctx: GateContext, branch: str) -> bool:
    """True when a branch ref still resolves in the repo (a still-resolving
    branch keeps its closeout-migration family, the gate-removal binding
    operand)."""
    proc = ctx.git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}")
    return proc.returncode == 0


def _read_session_json_at(
    directory_fd: int, name: str
) -> tuple[Optional[dict], Optional[str]]:
    """Best-effort (payload, error) for a JSON file read through a no-follow
    descriptor; unreadable and unparseable are distinguished errors."""
    text = _read_regular_text_at(directory_fd, name)
    if text is None:
        return None, "unreadable or missing"
    try:
        payload = json.loads(text)
    except ValueError as exc:
        return None, f"unparseable ({exc})"
    if not isinstance(payload, dict):
        return None, "not a JSON object"
    return payload, None


def _proof_family_state_file_terminal(payload: dict) -> bool:
    """The terminal-state bound (plan
    docs/history/plans/2026-11-01-docs-tmp-retention-redesign.md Task 3): the
    state file parses and carries ``terminal_receipt`` or reads
    ``workflow_state`` complete."""
    return bool(payload.get("terminal_receipt")) or (
        payload.get("workflow_state") == "complete"
    )


def _proof_family_worktree_key(payload: dict) -> Optional[str]:
    """Best-effort recorded worktree from the state file's worktree-family
    keys; None when none is readable (an unresolvable registration keeps)."""
    for key in ("worktree", "worktree_path", "worktree_family", "worktree_root"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _proof_family_session_decision(
    ctx: GateContext,
    session_fd: int,
    snapshot_roots: Optional[list[Path]],
    snapshot_verified: bool,
    primary: Optional[Path],
    proof_names: Optional[list[str]] = None,
) -> tuple[str, str]:
    """The fail-closed classification of one proof-family session directory
    (plan Task 3). Returns ('drain', reason), ('partial', reason), or
    ('keep', reason). The legacy receipt-less arm qualifies when no readable
    state file exists, the migration manifest records a branch ref that no
    longer resolves, and its recorded source worktree is unregistered or the
    primary checkout."""
    state_payload, state_error = _read_session_json_at(
        session_fd, EXECUTE_PLAN_STATE_FILENAME
    )
    branch: Optional[str] = None
    source: Optional[str] = None

    def migration_branch_source() -> None:
        """One single-homed (branch, source) extraction from the session's
        closeout-migration.json, when it carries a branch record."""
        nonlocal branch, source
        migration_payload, _migration_error = _read_session_json_at(
            session_fd, "closeout-migration.json"
        )
        if migration_payload is None:
            return
        records = migration_payload.get("branch")
        if not (isinstance(records, list) and records and isinstance(records[0], dict)):
            return
        raw_branch = records[0].get("branch")
        raw_source = records[0].get("source")
        if isinstance(raw_branch, str) and raw_branch.strip():
            branch = raw_branch.strip()
        if isinstance(raw_source, str) and raw_source.strip():
            source = raw_source.strip()

    if state_payload is not None:
        if not _proof_family_state_file_terminal(state_payload):
            return "keep", "session state file present but not terminal"
        worktree = _proof_family_worktree_key(state_payload)
        if worktree is None:
            return "keep", "state file carries no readable worktree-family key"
        # The state-file arm reads its branch ref from the migration
        # manifest when one exists; without one no branch is recorded and
        # the manifest family has nothing to keep, so the drain is total.
        migration_branch_source()
    elif _is_regular_file_at(session_fd, EXECUTE_PLAN_STATE_FILENAME):
        # The state file exists but could not be read or parsed: fail closed.
        return "keep", f"state file {state_error}; never guessing"
    else:
        migration_payload, _migration_error = _read_session_json_at(
            session_fd, "closeout-migration.json"
        )
        if migration_payload is None:
            if proof_names:
                # The legacy retention shape: no state file and no migration
                # manifest; the family keeps under its plain listing reason.
                return "keep", ", ".join(proof_names)
            return "keep", (
                "neither a readable state file nor a migration manifest; "
                "never guessed from age or directory shape"
            )
        migration_branch_source()
        if branch is None:
            if proof_names:
                return "keep", ", ".join(proof_names)
            return "keep", (
                "receipt-less session whose migration manifest records no "
                "branch; never guessed"
            )
        if source is None:
            return "keep", (
                "receipt-less session whose migration manifest records no "
                "source worktree; never guessed"
            )

    if snapshot_roots is None or not snapshot_verified or primary is None:
        return "keep", "candidate-root snapshot unverified; never guessing"
    still_resolves = (
        _branch_ref_resolves(ctx, branch) if branch is not None else False
    )
    recorded_worktree = (
        _proof_family_worktree_key(state_payload) if state_payload is not None else source
    )
    assert recorded_worktree is not None
    primary_resolved = Path(os.path.realpath(str(primary)))
    # A relative recorded value anchors at the primary checkout, never at
    # the sweep process CWD (the premortem key-shape guard).
    recorded_path = Path(recorded_worktree)
    if not recorded_path.is_absolute():
        recorded_path = primary_resolved / recorded_path
    try:
        resolved_wt = Path(os.path.realpath(recorded_path))
    except OSError:
        return "keep", "recorded worktree path unresolvable; never guessing"
    # A recorded key resolving to a family root (a parent of a candidate
    # checkout) is an unresolvable registration, not an unregistered leaf.
    if any(
        candidate != resolved_wt and resolved_wt in candidate.parents
        for candidate in snapshot_roots
    ):
        return "keep", (
            "recorded worktree key resolves to a family root; never guessing"
        )
    registered_elsewhere = any(
        resolved_wt == candidate and candidate != primary_resolved
        for candidate in snapshot_roots
    )
    if registered_elsewhere:
        return "keep", "session worktree is still registered"
    is_primary = resolved_wt == primary_resolved
    if branch is not None and still_resolves:
        if state_payload is None:
            # The receipt-less arm qualifies only when the branch no longer
            # resolves (plan Task 3); a stalled legacy migration with a live
            # branch keeps whole.
            return "keep", (
                "receipt-less session whose migration branch still resolves; "
                "never guessing"
            )
        return "partial", (
            "branch still resolves; migration manifests retained, baseline "
            "and other artifacts drained"
        )
    if is_primary or not registered_elsewhere:
        return (
            "drain",
            "consuming closeout terminal; proof family drained (retry reads a "
            "fresh setup baseline)",
        )
    return "keep", "session worktree is still registered"


def _sweep_execute_plan_sessions(
    ctx: GateContext,
    execute_fd: int,
    display_path: Path,
    removed: list[str],
    kept: list[str],
    pinned_fd: Optional[int] = None,
    root_is_current: Optional[Callable[[], bool]] = None,
    warnings: Optional[list[str]] = None,
) -> None:
    """Descriptor-relative counterpart used by the pinned-root sweep."""
    pending_stems = _pending_plan_session_names(
        ctx.plans_dir, ctx.plans_completed_dir
    )
    # The proof-family terminal-state drain (plan Task 3): candidates collect
    # here and classify + drain inside one citation-hold merge-lock span
    # after the loop.
    proof_candidates: list[tuple[str, Path, os.stat_result]] = []
    for session_name in sorted(os.listdir(execute_fd)):
        session_path = display_path / session_name
        try:
            session_stat = os.stat(
                session_name, dir_fd=execute_fd, follow_symlinks=False
            )
        except OSError:
            kept.append(str(session_path) + " (identity unreadable; preserved)")
            continue
        if not stat_module.S_ISDIR(session_stat.st_mode):
            kept.append(str(session_path) + " (not a directory; preserved)")
            continue
        if session_name in pending_stems:
            kept.append(str(session_path) + " (active: plan still pending)")
            continue
        try:
            session_fd = os.open(
                session_name,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
                dir_fd=execute_fd,
            )
        except OSError:
            kept.append(str(session_path) + " (changed while opening; preserved)")
            continue
        try:
            opened = os.fstat(session_fd)
            if (opened.st_dev, opened.st_ino, opened.st_mode) != (
                session_stat.st_dev,
                session_stat.st_ino,
                session_stat.st_mode,
            ):
                kept.append(str(session_path) + " (changed while opening; preserved)")
                continue
            proof_present = [
                proof for proof in PLAN_SLUG_PROOF_FILES
                if _is_regular_file_at(session_fd, proof)
            ]
            if proof_present:
                proof_candidates.append(
                    (session_name, session_path, opened)
                )
                continue
            current = os.stat(
                session_name, dir_fd=execute_fd, follow_symlinks=False
            )
            if (current.st_dev, current.st_ino, current.st_mode) != (
                opened.st_dev,
                opened.st_ino,
                opened.st_mode,
            ):
                kept.append(str(session_path) + " (identity changed; preserved)")
                continue
            if pinned_fd is None:
                kept.append(str(session_path) + " (quarantine root unavailable; preserved)")
                continue
            quarantined, quarantine_error = _quarantine_candidate(
                pinned_fd, execute_fd, session_name, opened
            )
            if quarantined is None:
                kept.append(
                    str(session_path)
                    + f" (removal failed) ({quarantine_error})"
                )
                continue
            if quarantine_error is not None:
                location = _quarantine_location(quarantined)
                kept.append(
                    str(session_path)
                    + f" ({quarantine_error}; retained at {location})"
                )
                continue
            try:
                quarantined_stat = os.stat(
                    quarantined.entry_name,
                    dir_fd=quarantined.directory_fd,
                    follow_symlinks=False,
                )
                if _candidate_identity(quarantined_stat) != _candidate_identity(opened):
                    location = _quarantine_location(quarantined)
                    kept.append(
                        str(session_path)
                        + f" (identity changed; retained at {location})"
                    )
                    continue
                current_pending = _pending_plan_session_names(
                    ctx.plans_dir, ctx.plans_completed_dir
                )
                quarantined_session_fd = os.open(
                    quarantined.entry_name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
                    dir_fd=quarantined.directory_fd,
                )
                try:
                    latest_info = os.fstat(quarantined_session_fd)
                    if _candidate_identity(latest_info) != _candidate_identity(opened):
                        location = _quarantine_location(quarantined)
                        kept.append(
                            str(session_path)
                            + f" (identity changed; retained at {location})"
                        )
                        continue
                    latest_proof = [
                        proof for proof in PLAN_SLUG_PROOF_FILES
                        if _is_regular_file_at(quarantined_session_fd, proof)
                    ]
                finally:
                    os.close(quarantined_session_fd)
                if session_name in current_pending:
                    location = _restore_quarantined_candidate(
                        pinned_fd, execute_fd, session_name, quarantined
                    )
                    kept.append(
                        str(session_path) + " (active: plan still pending)"
                        + (f"; retained at {location}" if location else "")
                    )
                    continue
                if latest_proof:
                    location = _restore_quarantined_candidate(
                        pinned_fd, execute_fd, session_name, quarantined
                    )
                    kept.append(
                        str(session_path)
                        + " (retained: closeout proof family: "
                        + ", ".join(latest_proof) + ")"
                        + (f"; retained at {location}" if location else "")
                    )
                    continue
                if root_is_current is not None and not root_is_current():
                    location = _restore_quarantined_candidate(
                        pinned_fd, execute_fd, session_name, quarantined
                    )
                    kept.append(
                        str(session_path) + " (pinned root identity changed; cleanup skipped)"
                        + (f"; retained at {location}" if location else "")
                    )
                    continue

                def session_remains_discardable() -> bool:
                    if session_name in _pending_plan_session_names(
                        ctx.plans_dir, ctx.plans_completed_dir
                    ):
                        return False
                    try:
                        final_session_fd = os.open(
                            quarantined.entry_name,
                            os.O_RDONLY
                            | getattr(os, "O_DIRECTORY", 0)
                            | os.O_NOFOLLOW,
                            dir_fd=quarantined.directory_fd,
                        )
                    except OSError:
                        return False
                    try:
                        opened_final = os.fstat(final_session_fd)
                        if _candidate_identity(opened_final) != quarantined.expected_identity:
                            return False
                        if any(
                            _is_regular_file_at(final_session_fd, proof)
                            for proof in PLAN_SLUG_PROOF_FILES
                        ):
                            return False
                    finally:
                        os.close(final_session_fd)
                    return root_is_current is None or root_is_current()

                _discard_quarantined_candidate(
                    pinned_fd, quarantined, revalidate=session_remains_discardable
                )
                removed.append(str(session_path) + " (plan archived)")
            except OSError as exc:
                location = _restore_quarantined_candidate(
                    pinned_fd, execute_fd, session_name, quarantined
                )
                kept.append(
                    str(session_path) + " (removal failed; preserved)"
                    + (f" at {location}" if location else "")
                    + f"; {exc}"
                )
        except OSError:
            kept.append(str(session_path) + " (removal failed)")
        finally:
            os.close(session_fd)
    if proof_candidates:
        posture = _docs_tmp_drain_posture(ctx)
        snapshot_roots, snapshot_verified, snapshot_warnings = (
            _snapshot_candidate_checkout_roots(ctx)
        )
        if warnings is not None:
            warnings.extend(snapshot_warnings)
        primary, _primary_err = _resolve_primary_checkout(ctx)

        def _drain_terminal_proof_families(referenced: Optional[set[str]]) -> None:
            # Invoked by ``_closeout_reference_hold`` exactly once on every
            # return path: inside the merge-lock span on the verified path,
            # with None on each unverifiable one. Only the verified path
            # unlinks, and only in the 'on' posture; any byte inside the
            # session named by the shared referenced set keeps the whole
            # directory.
            for cand_name, cand_path, cand_identity in proof_candidates:
                if referenced is None:
                    kept.append(
                        str(cand_path)
                        + " (proof family retained: closeout reference hold "
                        "unverified)"
                    )
                    continue
                cited = False
                if referenced:
                    try:
                        for root, _dirs, files in os.walk(cand_path):
                            for fname in files:
                                full = os.path.realpath(os.path.join(root, fname))
                                if full in referenced:
                                    cited = True
                                    break
                            if cited:
                                break
                    except OSError:
                        cited = True  # an unreadable walk keeps, never guessing
                if cited:
                    kept.append(
                        str(cand_path)
                        + " (proof family retained: a byte inside the session "
                        "is cited by a live closeout manifest)"
                    )
                    continue
                try:
                    session_fd_d = os.open(
                        cand_name,
                        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW,
                        dir_fd=execute_fd,
                    )
                except OSError:
                    kept.append(str(cand_path) + " (changed while opening; preserved)")
                    continue
                try:
                    opened_d = os.fstat(session_fd_d)
                    if _candidate_identity(opened_d) != _candidate_identity(cand_identity):
                        kept.append(str(cand_path) + " (identity changed; preserved)")
                        continue
                    verdict, reason = _proof_family_session_decision(
                        ctx, session_fd_d, snapshot_roots, snapshot_verified, primary,
                        proof_names=[
                            proof
                            for proof in PLAN_SLUG_PROOF_FILES
                            if _is_regular_file_at(session_fd_d, proof)
                        ],
                    )
                    if verdict == "keep":
                        kept.append(f"{cand_path} (retained: closeout proof family: {reason})")
                        continue
                    if posture == "off":
                        kept.append(f"{cand_path} (drain arms off; proof family kept)")
                        continue
                    if posture == "report-only":
                        kept.append(
                            f"{cand_path} (would-drain: {reason}; "
                            "posture report-only)"
                        )
                        continue
                    if verdict == "partial":
                        # Drain the baseline and other artifacts through the
                        # quarantine flow (recovery parity with the full
                        # drain); keep the closeout-migration.json family
                        # (the gate-removal binding operand).
                        if pinned_fd is None:
                            kept.append(
                                str(cand_path)
                                + " (quarantine root unavailable; preserved)"
                            )
                            continue
                        drained_any = False
                        members = sorted(os.listdir(session_fd_d))
                        for member in members:
                            try:
                                m_stat = os.stat(
                                    member, dir_fd=session_fd_d, follow_symlinks=False
                                )
                            except OSError:
                                continue
                            if not stat_module.S_ISREG(m_stat.st_mode):
                                continue
                            if member.startswith("closeout-migration"):
                                continue
                            member_quarantined, member_error = _quarantine_candidate(
                                pinned_fd, session_fd_d, member, m_stat
                            )
                            if member_quarantined is None or member_error is not None:
                                continue
                            try:
                                member_current = os.stat(
                                    member_quarantined.entry_name,
                                    dir_fd=member_quarantined.directory_fd,
                                    follow_symlinks=False,
                                )
                                if _candidate_identity(member_current) != (
                                    _candidate_identity(m_stat)
                                ):
                                    _restore_quarantined_candidate(
                                        pinned_fd, session_fd_d, member,
                                        member_quarantined,
                                    )
                                    continue
                                _discard_quarantined_candidate(
                                    pinned_fd, member_quarantined
                                )
                                drained_any = True
                            except OSError:
                                _restore_quarantined_candidate(
                                    pinned_fd, session_fd_d, member,
                                    member_quarantined,
                                )
                        kept.append(f"{cand_path} ({reason})")
                        if drained_any:
                            removed.append(
                                f"{cand_path} [proof-family artifacts drained; "
                                "branch still resolving]"
                            )
                        continue
                    # verdict == 'drain': full-directory removal through the
                    # quarantine flow with the identity and pending-plan
                    # rechecks.
                    if pinned_fd is None:
                        kept.append(
                            str(cand_path) + " (quarantine root unavailable; preserved)"
                        )
                        continue
                    quarantined, quarantine_error = _quarantine_candidate(
                        pinned_fd, execute_fd, cand_name, opened_d
                    )
                    if quarantined is None:
                        kept.append(
                            str(cand_path) + f" (removal failed) ({quarantine_error})"
                        )
                        continue
                    if quarantine_error is not None:
                        location = _quarantine_location(quarantined)
                        kept.append(
                            str(cand_path)
                            + f" ({quarantine_error}; retained at {location})"
                        )
                        continue
                    try:
                        current_pending = _pending_plan_session_names(
                            ctx.plans_dir, ctx.plans_completed_dir
                        )
                        if cand_name in current_pending:
                            location = _restore_quarantined_candidate(
                                pinned_fd, execute_fd, cand_name, quarantined
                            )
                            kept.append(
                                str(cand_path) + " (active: plan still pending)"
                                + (f"; retained at {location}" if location else "")
                            )
                            continue
                        if root_is_current is not None and not root_is_current():
                            location = _restore_quarantined_candidate(
                                pinned_fd, execute_fd, cand_name, quarantined
                            )
                            kept.append(
                                str(cand_path)
                                + " (pinned root identity changed; cleanup skipped)"
                                + (f"; retained at {location}" if location else "")
                            )
                            continue

                        def session_remains_terminal_discardable() -> bool:
                            if cand_name in _pending_plan_session_names(
                                ctx.plans_dir, ctx.plans_completed_dir
                            ):
                                return False
                            try:
                                final_fd = os.open(
                                    quarantined.entry_name,
                                    os.O_RDONLY
                                    | getattr(os, "O_DIRECTORY", 0)
                                    | os.O_NOFOLLOW,
                                    dir_fd=quarantined.directory_fd,
                                )
                            except OSError:
                                return False
                            try:
                                final_stat = os.fstat(final_fd)
                                if _candidate_identity(final_stat) != (
                                    quarantined.expected_identity
                                ):
                                    return False
                            finally:
                                os.close(final_fd)
                            return root_is_current is None or root_is_current()

                        _discard_quarantined_candidate(
                            pinned_fd, quarantined, revalidate=session_remains_terminal_discardable
                        )
                        removed.append(f"{cand_path} ({reason})")
                    except OSError as exc:
                        location = _restore_quarantined_candidate(
                            pinned_fd, execute_fd, cand_name, quarantined
                        )
                        kept.append(
                            str(cand_path) + " (removal failed; preserved)"
                            + (f" at {location}" if location else "")
                            + f"; {exc}"
                        )
                finally:
                    os.close(session_fd_d)

        _proof_hold, proof_hold_warnings = _closeout_reference_hold(
            ctx, _drain_terminal_proof_families
        )
        if warnings is not None:
            warnings.extend(proof_hold_warnings)


def _is_regular_file_at(directory_fd: int, name: str) -> bool:
    try:
        info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except OSError:
        return False
    return stat_module.S_ISREG(info.st_mode)


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
    profile_exempt = ctx.artifact_visibility == "private"
    if profile_exempt:
        # The private-visibility exemption skips both content arms entirely:
        # arms 1 and 2 below iterate an empty pattern list, while arms 3 and
        # 4 still run for every profile, private included.
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
                # r3 F3: pin the scanned root in the child's environment. The
                # child would otherwise inherit the caller's
                # PUBLIC_HYGIENE_REPO_ROOT and scan a foreign repository
                # while this gate records its result against ctx.repo_root.
                # The PUBLIC_HYGIENE_PATTERNS_FILE inheritance is left
                # untouched (choice recorded here): this call site resolves
                # no patterns file of its own, so the child keeps the
                # scanner contract's own resolution (env override, else the
                # default home path).
                proc = ctx.run(
                    ["bash", str(scan)],
                    cwd=ctx.repo_root,
                    env={
                        **os.environ,
                        "PUBLIC_HYGIENE_REPO_ROOT": str(ctx.repo_root),
                    },
                )
                # Report-only tracked scope (plan 2026-10-26-hygiene-
                # scanner-default-scope-parity): the default-mode child's
                # PUBLIC_HYGIENE_REPORT rows ride the warnings channel
                # verbatim whatever the child's verdict is; every other
                # successful-output row stays uninterpreted evidence, and
                # the FAIL tail handling and child result codes below are
                # untouched.
                warnings.extend(
                    row.rstrip("\r\n")
                    for row in (proc.stdout or "").splitlines()
                    if row.strip().startswith(PUBLIC_HYGIENE_REPORT_LINE_PREFIX)
                    # Phase 3 r2 F1: a tracked filename containing a newline
                    # under a blocking root splits its rg -n FAIL row, and the
                    # second physical line can start with the report prefix.
                    # Any `:\d+:` row is treated as split debris and dropped;
                    # accepted collision: a genuine path containing
                    # `:<digits>:` (unescaped by json_quote_path) is textually
                    # indistinguishable from debris and is dropped too, a rare
                    # false negative on an advisory channel (review r3 F1).
                    and not re.search(r":\d+:", row)
                )
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
                    # r3 F2: report rows already ride the warnings channel
                    # verbatim above, so filtering them out of the tail keeps
                    # a report-row flood (report records print after FAIL
                    # blocks) from evicting the real FAIL rows from the
                    # finding message at the last-10 cut.
                    tail_rows = [
                        row
                        for row in (proc.stdout or "").strip().splitlines()
                        if row.strip()
                        and not row.strip().startswith(OUTCOME_LINE_PREFIX)
                        and not row.strip().startswith(
                            PUBLIC_HYGIENE_REPORT_LINE_PREFIX
                        )
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
            "sensitive-data scan clean (content arms skipped: "
            "artifact_visibility is private"
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
    """Blocking landing gate (plan
    docs/history/plans/2026-10-24-description-length-gate-catch-promotion.md):
    the folded skill-description 1024-character cap. The checker's outcome
    classes are classified, never collapsed: exit 1 is a measured over-cap
    result and keeps rc=1 (the one result the commit path records as a
    description-length guard catch before refusing the landing); exit 0
    passes with the checker's warning-band rows; a missing checker
    deployment and every other checker exit (2 = the checker's own
    operational-exception class; anything else unexpected) are tool errors
    (rc=3) and never catches. A raised gate helper stays indeterminate
    (rc=2) through the phase runner's capture."""
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
        # A deployment gap cannot answer the check, so it is a tool error
        # (rc=3), never a modeled over-cap failure (rc=1) and never a catch.
        return GateResult(gate, 3, message, warnings=[])
    proc = ctx.run([sys.executable, str(script)], cwd=ctx.repo_root)
    if proc.returncode == 1:
        # Measured over-cap result: the checker names over-cap files on
        # stderr; tail both streams so the failure message carries the named
        # files. This is the only catch-classified checker outcome.
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
    if proc.returncode != 0:
        # Exit 2 is the checker's own operational-exception class; every
        # other non-zero exit is an unexpected checker failure. Neither is a
        # measured over-cap result, so neither is a catch: tool error rc=3
        # (the commit path refuses rc=2/rc=3 without recording a catch).
        tail_rows = [
            row
            for row in (
                (proc.stdout or "") + "\n" + (proc.stderr or "")
            ).strip().splitlines()
            if row.strip()
        ][-10:]
        return GateResult(
            gate,
            3,
            f"description length checker tool error (exit {proc.returncode}): "
            + " | ".join(tail_rows),
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
            "under the Primary land lock ownership (the primary done lock "
            "acquired before the merge lock, both held through the landing, "
            "released merge then done)); operator escape for dead residue only "
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
            "under the Primary land lock ownership (the primary done lock "
            "acquired before the merge lock, both held through the landing, "
            "released merge then done)); operator escape for dead residue only "
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
    provenance: str,
) -> None:
    """Surface one mapped archive unit from its HEAD bytes.

    The regular-file probe and the bytes read each fail explicitly into
    ``blockers`` (a mapped unit is never silently dropped); charter units
    carry the HEAD task span beside the charter text. ``provenance`` is the
    row's range-provenance class, decided by the caller against the span
    base (a modified row can carry a unit a prior run landed).
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
        archives.append(
            (unit_rel, text, archive_bytes, None, archive_bytes, provenance)
        )

# The Task 4 range-provenance classes (plan
# docs/history/plans/2026-11-07-archive-rider-sweep-ordering.md): whether a
# surfaced archive lies inside this run's manifest span or was landed by a
# prior run. The classes tag the derivation rows internally and surface only
# in the finding message text; no acceptance route or verdict reads them.
ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN = "this run's manifest span"
ARCHIVE_CEREMONY_PROVENANCE_PRIOR_RUN = "a prior run"


def _archive_provenance_at_span_base(
    ctx: GateContext, base: str, archive_rel: str
) -> str:
    """The range-provenance class of a committed archive row: the prior-run
    class only when the archive path is confirmed present at the span base
    the derivation evaluated (the archived-plan surface predates the
    evaluated range, so a prior run landed it); the this-run class otherwise,
    including an unresolvable base or a presence-lookup error, where the
    probe cannot decide and the finding addresses the running run (a wrong
    prior-run class would teach the operator to dismiss an archive this run
    did land, the silent-rider hazard the report arm exists to close)."""
    verify = ctx.git("rev-parse", "-q", "--verify", f"{base}^{{commit}}")
    if verify.returncode != 0:
        return ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN
    present, _blob, _mode, _error = _commit_path_state(ctx, base, archive_rel)
    if present:
        return ARCHIVE_CEREMONY_PROVENANCE_PRIOR_RUN
    return ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN


def _derive_archived_plans(
    ctx: GateContext,
) -> tuple[
    list[tuple[str, str, bytes, Optional[str], Optional[bytes], str]],
    list[str],
    list[str],
]:
    """Surface archive rows plus non-failing notes and blocking diagnostics.

    Each row is ``(archive path, decoded checkbox text, exact archive bytes,
    recovered pre-archive path, preferred reviewed raw bytes,
    range-provenance class)``. Unreadable
    evidence and failed source queries are never silently treated as an empty
    archive set.

    The range-provenance class (plan
    docs/history/plans/2026-11-07-archive-rider-sweep-ordering.md, Task 4)
    states whether the surfaced archive lies inside this run's manifest span
    or was landed by a prior run. Shape (a) rows are this run's own pending
    landing and shape (b) rename/addition rows are new inside the evaluated
    ``base..HEAD`` range by construction, so both carry the this-run class;
    the feature-only rebase rows and the shape (c) stale-deliverables twins
    decide through ``_archive_provenance_at_span_base`` (confirmed presence
    at the evaluated span base names a prior run). The tag is internal: it
    surfaces only in the finding message text, and no acceptance route or
    verdict reads it.

    When the context carries ``archive_ceremony_pinned_span_base`` (set only
    by the archive-ceremony arm's entry point), that pinned boundary replaces
    the session-dir newest-marker re-derivation, so a peer marker that
    flipped post-release cannot move the evaluation span.

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
    # for stale deliverables twins that use the archive form. The final list
    # field is the range-provenance class (this run's manifest span vs a
    # prior run; shape (a) and the committed rename/addition rows are
    # this-run by construction, the rest decide per row).
    archives: list[tuple[str, str, bytes, Optional[str], Optional[bytes], str]] = []
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
                    (
                        charter, text, archive_bytes, old_rel, reviewed,
                        ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN,
                    )
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
            archives.append(
                (
                    new, text, archive_bytes, old_rel, reviewed,
                    ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN,
                )
            )

    # Shape (b): committed renames into the completed archive since the run
    # manifest boundary (ORIG_HEAD fallback; neither resolves: skip, noted).
    pinned_base = ctx.archive_ceremony_pinned_span_base
    manifest: Optional[RunManifest] = None
    manifest_pinned = False
    if pinned_base is not None:
        # The archive-ceremony arm's pinned boundary (the entry point
        # resolved it from the owning bound manifest and verified it): the
        # session-dir newest-marker re-read below is skipped, so a peer
        # setup that flipped the newest marker post-release cannot move
        # this evaluation's span.
        manifest_pinned = True
        base = pinned_base
    else:
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
    if manifest is not None or manifest_pinned:
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
                    ctx, unit, is_charter, seen, archives, blockers, notes,
                    _archive_provenance_at_span_base(ctx, base, unit),
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
                                             reviewed,
                                             ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN))
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
                                 reviewed,
                                 ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN)
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
                                         reviewed,
                                         ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN))
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
                                 reviewed,
                                 ARCHIVE_CEREMONY_PROVENANCE_THIS_RUN))

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
                archives.append(
                    (
                        twin_rel, text, archive_bytes, rel, None,
                        _archive_provenance_at_span_base(ctx, base, twin_rel),
                    )
                )

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
    that refuses it. Each finding also states the surfaced archive's range
    provenance (the derivation row's internal tag, message-visible only):
    whether the archive lies inside this run's manifest span or was landed
    by a prior run; the classes feed no acceptance route and no verdict."""
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
    for (
        archive_rel,
        text,
        archive_bytes,
        pre_archive_rel,
        reviewed_bytes,
        provenance,
    ) in archives:
        if _archive_state_of(ctx, archive_rel) == "rejected":
            exempted.append(archive_rel)
            continue
        unchecked = text.count("- [ ]")
        if unchecked:
            findings.append(
                f"archived plan {archive_rel} carries {unchecked} unchecked "
                f"task box(es); range provenance: {provenance}; "
                "sanctioned exits: check the boxes after the "
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
            "home names the missing series); "
            f"range provenance: {provenance}; remedy: produce the "
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
# Post-landing archive-ceremony report arm (plan
# docs/history/plans/2026-11-07-archive-rider-sweep-ordering.md, Task 2).
# Warning-only and fail-open: the owning closeout re-runs the EXISTING
# gate_archive_ceremony over its landed state and reports the finding
# instead of staying silent. The entry point below is the only new code and
# carries no acceptance logic: the gate's verdict is consumed as returned;
# what the entry point owns is context work - the span-boundary resolution
# (the finalize's pre-release bound manifest as the primary route, the
# checkout-local newest-marker re-derivation fallback-only), the boundary
# and derivation-blocker classification into the distinct could-not-evaluate
# posture, and the pinned hybrid context (ONLY the reviews corpus re-roots
# at the primary reviews home; repo_root, every git surface, and the span
# evidence stay anchored at the running checkout). No bash code classifies
# the boundary or string-matches the gate's note text.
# --------------------------------------------------------------------------- #
ARCHIVE_CEREMONY_REPORT_SUMMARY_PREFIX = "archive-ceremony evaluation:"
ARCHIVE_CEREMONY_REPORT_FINDING_PREFIX = "archive-ceremony finding:"
ARCHIVE_CEREMONY_REPORT_POSTURE_TOKEN = "could-not-evaluate"
# The reconstruction producer the finding lines name (the plan's repair
# pointer; the producer surface itself is outside this plan's scope).
ARCHIVE_CEREMONY_REPORT_PRODUCER = "scripts/produce_exec_review_record.py"


def _primary_checkout_for_reviews(repo_root: Path) -> Path:
    """The primary checkout as the missing-review-record scan derives it:
    the first ``worktree `` line of ``git worktree list --porcelain`` (git
    itself prints the realpath), falling back to the running checkout when
    the listing fails or names none. Byte-frozen twin of the scan's inline
    primary selection; this entry point is the owning home of the
    pinned-context resolution, so a future scan edit re-derives the parity
    here instead of drifting it."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return repo_root
    return next(
        (
            Path(line[len("worktree "):])
            for line in proc.stdout.splitlines()
            if line.startswith("worktree ")
        ),
        repo_root,
    )


def _primary_reviews_home(repo_root: Path, primary: Path) -> tuple[str, Path]:
    """The primary reviews home in its two forms: the report string (the
    literal facts value joined, trailing form preserved for the summary
    line) and the context path. A relative reviews corpus resolves from the
    primary checkout: that shared gitignored reviews home is canonical
    while a worktree transfer-in copy can be partial (development lesson
    74); an absolute value keeps the configured path. Byte-frozen twin of
    the scan's facts-rooted reviews re-root."""
    try:
        value = facts_paths.resolve_toml_key_raw(repo_root, "reviews_dir") or ""
    except OSError:
        value = ""
    if not value:
        joined = os.path.join(str(primary), ".ai-playbook/reviews")
        return joined, Path(joined)
    if os.path.isabs(value):
        return value, Path(value)
    joined = os.path.join(str(primary), value)
    return joined, Path(joined)


def _load_bound_span_manifest(
    path: Path, repo_root: Path
) -> tuple[Optional[RunManifest], str]:
    """Parse the finalize's pre-release bound run manifest as the span
    evidence primary route. Returns ``(manifest, "")`` on success, or
    ``(None, detail)`` when the record is unreadable, schema-invalid, or
    foreign to the running checkout (a manifest from another checkout of
    the same repo is never this run's record; the loader's two-arm root
    match decides)."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return None, f"unreadable ({exc})"
    manifest = RunManifest.from_dict(payload) if isinstance(payload, dict) else None
    if manifest is None:
        return None, "schema or field validation failed"
    if not _manifest_root_matches(manifest.repo_root, repo_root):
        return None, "repo_root does not match the running checkout"
    return manifest, ""


def _archive_ceremony_span_base(
    ctx: GateContext, bound_manifest_path: Optional[Path]
) -> tuple[str, str]:
    """Resolve the span boundary and classify it. Primary route: the owning
    run's bound manifest passed in by the wrapper (the finalize's
    pre-release resolution), never re-derived post-release. Fallback-only,
    when no manifest was bound: the checkout-local newest-marker
    re-derivation with the ORIG_HEAD fallback (the gate_doc_registry
    precedent), which the root-match contract pins to this checkout's own
    records. Returns ``(base, "")`` when the boundary resolves, or
    ``("", detail)`` when it does not: the caller reports could-not-evaluate
    from that detail instead of evaluating, never a pass-shaped line. The
    caller pins the resolved base onto the gate context, so the derivation
    and the gate re-run consume it and never re-read the session dir
    post-release."""
    base = "ORIG_HEAD"
    if bound_manifest_path is not None:
        manifest, error = _load_bound_span_manifest(
            bound_manifest_path, ctx.repo_root
        )
        if error:
            return "", (
                "the finalize's bound run manifest is not usable as the "
                f"span boundary: {bound_manifest_path} {error}"
            )
        base = manifest.start_commit
    else:
        window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
        manifest = load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
        if manifest is not None:
            base = manifest.start_commit
    verify = ctx.git("rev-parse", "-q", "--verify", f"{base}^{{commit}}")
    if verify.returncode != 0 or not verify.stdout.strip():
        return "", (
            "span boundary does not resolve: neither the owning run "
            f"manifest start_commit nor ORIG_HEAD resolves, tried {base}"
        )
    return base, ""


def _segment_archive_findings(message: str) -> list[str]:
    """Split the gate's failure message into per-archive finding texts.
    The message is the gate's verdict output, not an acceptance input:
    segments beginning with ``archived plan `` start a finding and every
    following segment continues the preceding one (the route texts carry
    their own semicolons). Empty when the failure names no surfaced archive
    (a derivation blocker), which the caller classifies as
    could-not-evaluate."""
    prefix = "archive-ceremony gate failed: "
    if not message.startswith(prefix):
        return []
    findings: list[str] = []
    for segment in message[len(prefix):].split("; "):
        if segment.startswith("archived plan "):
            findings.append(segment)
        elif findings:
            findings[-1] += "; " + segment
    return findings


def _archive_ceremony_posture(detail: str) -> str:
    """The distinct could-not-evaluate line: never pass-shaped, never a
    findings=0 summary, carrying the posture token the report consumers
    grep for."""
    return (
        f"{ARCHIVE_CEREMONY_REPORT_SUMMARY_PREFIX} "
        f"{ARCHIVE_CEREMONY_REPORT_POSTURE_TOKEN}: {detail}"
    )


def _archive_ceremony_summary_line(
    findings: int, evaluated_commit: str, evaluated_at: str, reviews_root: str
) -> str:
    """The always-present evaluation summary line (findings count, evaluated
    commit, evaluation time, resolved reviews root)."""
    return (
        f"{ARCHIVE_CEREMONY_REPORT_SUMMARY_PREFIX} findings={findings} "
        f"evaluated_commit={evaluated_commit} evaluated_at={evaluated_at} "
        f"reviews_root={reviews_root}"
    )


def archive_ceremony_post_landing_report(
    repo_root: Path,
    bound_manifest_path: Optional[Path],
) -> tuple[list[str], list[str]]:
    """Evaluate the landed state through the existing archive-ceremony gate
    and return the report lines as ``(stdout_lines, stderr_lines)``.

    Classification ownership (plan
    docs/history/plans/2026-11-07-archive-rider-sweep-ordering.md, Task 2):

    - an unresolvable span boundary (neither the owning run manifest
      start_commit nor ORIG_HEAD resolves) is a distinct could-not-evaluate
      result on stdout, reported like a finding, and the gate never runs;
    - the resolved span boundary is pinned onto the gate context before the
      derivation and the gate re-run run: neither re-reads the session dir's
      newest marker post-release, so a peer setup that flipped the newest
      marker cannot move the evaluated span (the plan's no-post-release
      re-derivation assumption);
    - a derivation blocker (a gate failure whose message carries no surfaced
      archive) classifies into the same could-not-evaluate posture, never
      into the archive-finding line;
    - surfaced archives drive the one gate re-run: rc 0 (or no archive
      surfaces changed in the span, where the gate does not re-run at all)
      produces the findings=0 summary; rc 1 with surfaced findings produces
      the summary plus one ``archive-ceremony finding:`` line per archive
      naming the failing acceptance route, the reconstruction producer, and
      the evaluated commit and evaluation time;
    - any arm failure of its own (facts resolution, gate exception) returns
      the could-not-evaluate posture on the failure channel instead, never
      a pass-shaped or bare-clean line.

    Reader divergence note: the reviews-home resolution here
    (``_primary_reviews_home``, via ``facts_paths.resolve_toml_key_raw``) is
    not byte-identical to the missing-review-record scan twin's inline regex
    reader; on non-canonical facts lines the two twins can resolve different
    corpora, while canonical facts lines resolve identically.

    Always exit-0 semantics live with the caller: this function never
    refuses and never carries an exit code."""
    out: list[str] = []
    err: list[str] = []
    try:
        ctx = GateContext.discover(repo_root)
        primary = _primary_checkout_for_reviews(ctx.repo_root)
        reviews_root_text, reviews_root_path = _primary_reviews_home(
            ctx.repo_root, primary
        )
        # Pinned hybrid context: ONLY the reviews corpus re-roots at the
        # primary reviews home; repo_root, every git surface (the
        # derivation's porcelain and diff reads, the archive-state dirs),
        # and the span evidence stay anchored at the running checkout.
        ctx.reviews_dir = reviews_root_path
        _base, boundary_detail = _archive_ceremony_span_base(
            ctx, bound_manifest_path
        )
        if boundary_detail:
            out.append(_archive_ceremony_posture(boundary_detail))
            return out, err
        # Pin the resolved boundary for both consumers below: the derivation
        # and the gate re-run would otherwise re-read the session dir's
        # newest marker post-release, the peer-flip race the plan's span
        # assumption forbids (a newer same-checkout peer marker would
        # silently move the evaluated span and hide this run's archives).
        ctx.archive_ceremony_pinned_span_base = _base
        evaluated_commit = ctx.git("rev-parse", "HEAD").stdout.strip()
        if not evaluated_commit:
            out.append(_archive_ceremony_posture(
                "HEAD does not resolve at the running checkout"
            ))
            return out, err
        evaluated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows, _notes, blockers = _derive_archived_plans(ctx)
        if blockers:
            out.append(_archive_ceremony_posture(
                "gate derivation blocked: " + "; ".join(blockers)
            ))
            return out, err
        if not rows:
            # No archive surfaces changed in the run's span: the gate does
            # not re-run; the always-present summary reports the clean span.
            out.append(_archive_ceremony_summary_line(
                0, evaluated_commit, evaluated_at, reviews_root_text
            ))
            return out, err
        result = gate_archive_ceremony(ctx)
        if result.rc == 0:
            out.append(_archive_ceremony_summary_line(
                0, evaluated_commit, evaluated_at, reviews_root_text
            ))
            return out, err
        findings = _segment_archive_findings(result.message)
        if not findings:
            out.append(_archive_ceremony_posture(
                "gate reported failure with no surfaced archive finding: "
                + result.message
            ))
            return out, err
        out.append(_archive_ceremony_summary_line(
            len(findings), evaluated_commit, evaluated_at, reviews_root_text
        ))
        for route_text in findings:
            out.append(
                f"{ARCHIVE_CEREMONY_REPORT_FINDING_PREFIX} {route_text}; "
                f"repair producer: {ARCHIVE_CEREMONY_REPORT_PRODUCER} "
                f"(reconstruction path); evaluated_commit="
                f"{evaluated_commit} evaluated_at={evaluated_at}"
            )
        return out, err
    except Exception as exc:  # fail-open: any arm failure warns and continues
        err.append(_archive_ceremony_posture(
            f"arm failure: {type(exc).__name__}: {exc}"
        ))
        return out, err


def _cmd_archive_ceremony_report(argv: list[str]) -> int:
    """CLI entry for the post-landing archive-ceremony report arm: read-only
    reporting only, exit 0 on every answered outcome (the warning-only
    posture; the wrapper's ``||`` guard carries the catastrophic-only
    could-not-evaluate warning)."""
    parser = argparse.ArgumentParser(
        prog="done_sweep_gates.py archive-ceremony-report",
        description=(
            "Post-landing archive-ceremony report arm (warning-only, "
            "fail-open): re-runs the existing archive-ceremony gate over "
            "the landed state under the pinned hybrid context and prints "
            "the always-present evaluation summary line plus per-finding "
            "lines. Read-only; never refuses; exit 0 on every answered "
            "outcome."
        ),
    )
    parser.add_argument(
        "--manifest",
        default="",
        help=(
            "the finalize's pre-release bound run manifest (the span "
            "evidence primary route); empty or omitted selects the "
            "checkout-local newest-marker re-derivation fallback"
        ),
    )
    args = parser.parse_args(argv)
    root = os.environ.get("DONE_SWEEP_REPO_ROOT")
    out_lines, err_lines = archive_ceremony_post_landing_report(
        Path(root) if root else Path.cwd(),
        Path(args.manifest) if args.manifest else None,
    )
    for line in out_lines:
        print(line)
    for line in err_lines:
        print(line, file=sys.stderr)
    return 0


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
    reports. The one demotion (plan
    docs/history/plans/2026-10-24-description-length-gate-catch-promotion.md):
    an unexpected docs-tmp-sweep helper exception is warning-only (rc=0 with
    a warning line, later gates still run, and the phase can still exit 0):
    scratch cleanup is retryable in a later session, though the sweep may
    have been interrupted mid-run: entries it had already classified as
    removable may be gone and its removal report was lost; the gate's
    normal conservative keep behavior is unchanged."""
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
            if gate_id == "docs-tmp-sweep":
                # Demoted class: an unexpected docs-tmp helper exception
                # warns and never blocks; cleanup retries in a later
                # session. The sweep may have been interrupted mid-run, so
                # entries it already classified as removable may be gone
                # and its removal report was lost; re-derive docs/tmp
                # state from disk before trusting the keeps.
                results.append(
                    GateResult(
                        gate_id,
                        0,
                        f"docs-tmp-sweep helper raised {type(exc).__name__}: "
                        f"{exc}; warning-only: the exception does not block "
                        "the landing, and cleanup can retry in a later "
                        "session (the sweep was interrupted mid-run: entries "
                        "it had already classified as removable may be gone "
                        "and its removal report was lost; re-derive docs/tmp "
                        "state from disk before trusting the keeps)",
                        warnings=[
                            f"docs-tmp-sweep helper raised "
                            f"{type(exc).__name__}: {exc}; cleanup retried "
                            "in a later session"
                        ],
                    )
                )
                continue
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
        "classify-run-boundary|list-interrupted-manifests|"
        "archive-ceremony-report>\n"
        "phases: landing (the closeout's one landing sweep run: the "
        "retained roster with instruction-size in warning posture and "
        "description-length blocking - a measured over-cap result refuses "
        "the landing, the commit path records its guard catch before "
        "refusing, and checker deployment gaps plus operational-exception "
        "exits answer tool error, never a catch; backlog-inbox and "
        "vim-swap-sweep are not on the roster - receiving-review capture "
        "step and the periodic survey advisory own their duties)\n"
        "list-gates [phase] prints that phase's roster one gate per line "
        "with warning-posture gates suffixed \" (warning)\"\n"
        "write-manifest writes the done Step 0 run manifest record "
        "(run-manifest-<run_id>.json under the done-session directory), "
        "reporting interrupted runs (complete=false, never finalized; "
        "continued only via an explicit --adopt boundary copy; an adopt "
        "refuses unless DONE_LOCK_DIR/DONE_LOCK_TOKEN prove the caller "
        "holds this checkout's current done lock and the target classifies "
        "as an interrupted orphan, and a path claimed both owned and "
        "foreign in the adopted composition refuses; a worktree "
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
        "archive-ceremony-report prints the post-landing archive-ceremony "
        "evaluation (warning-only, fail-open; plan "
        "docs/history/plans/2026-11-07-archive-rider-sweep-ordering.md): an "
        "always-present summary line (findings count, evaluated commit, "
        "evaluation time, resolved reviews root) plus one archive-ceremony "
        "finding line per surfaced archive naming the failing acceptance "
        "route and the reconstruction producer; an unresolvable span "
        "boundary, a derivation blocker, or an arm failure of its own "
        "prints the distinct could-not-evaluate posture instead, never a "
        "pass-shaped clean line; read-only, never refuses, exit 0 on every "
        "answered outcome\n"
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


def _caller_done_lock_refusal(repo_root: Path) -> Optional[str]:
    """The named reason the caller environment fails to prove done-lock
    ownership of this repository, else None (the exported lock is the
    current hold for this checkout, unlocked by the caller's token).

    The evidence contract behind ``write-manifest --adopt``: DONE_LOCK_DIR
    names a lock directory whose ``meta.env`` records this repository's
    root (both arms of the shared ``_repo_root_matches_value``) and whose
    recorded ``lock_token`` equals DONE_LOCK_TOKEN (the caller holds it).
    Absent, malformed, or mismatched evidence refuses: a meta-less or
    unreadable hold is unknown state, never guessed, and a recorded token
    naming another holder refuses the same way, the target run's owning
    run possibly still live under it. The meta parse keeps the lock
    script's anchored first-match reading (the
    ``_done_lock_meta_holder_pid`` rule)."""
    lock_dir_text = os.environ.get("DONE_LOCK_DIR", "")
    token_text = os.environ.get("DONE_LOCK_TOKEN", "")
    if not lock_dir_text or not token_text:
        return (
            "DONE_LOCK_DIR and DONE_LOCK_TOKEN must name the current lock "
            "for this repository and carry its token"
        )
    lock_dir = Path(lock_dir_text)
    if not lock_dir.is_dir():
        return f"{lock_dir_text} is not a lock directory (the exported DONE_LOCK_DIR path is absent or not a directory)"
    try:
        text = (lock_dir / _DONE_LOCK_META_FILE).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return (
            f"no readable {_DONE_LOCK_META_FILE} under {lock_dir_text} "
            "(unknown holder state; adoption never guesses a hold)"
        )
    recorded_token = ""
    recorded_root = ""
    for line in text.splitlines():
        if line.startswith("lock_token=") and not recorded_token:
            recorded_token = line[len("lock_token="):].strip()
        elif line.startswith("repo_root=") and not recorded_root:
            recorded_root = line[len("repo_root="):].strip()
    if not recorded_token or not recorded_root:
        return (
            f"{_DONE_LOCK_META_FILE} under {lock_dir_text} records no "
            "lock_token or no repo_root (unknown holder state; adoption "
            "never guesses a hold)"
        )
    if not hmac.compare_digest(recorded_token.encode(), token_text.encode()):
        return (
            "the recorded lock_token does not match DONE_LOCK_TOKEN (the "
            "hold is another holder's, the target run's owning run "
            "possibly still live under it)"
        )
    if not _repo_root_matches_value(recorded_root, repo_root):
        return (
            "the recorded repo_root is not this repository (the exported "
            "lock is another checkout's current lock)"
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

    Adoption guard (plan 2026-10-26-done-writer-adoption-guards): an
    ``--adopt`` invocation must prove done-lock ownership of this repository
    before the boundary is touched, and the target boundary must still be an
    open interrupted orphan. The proof is the caller's own held lock:
    DONE_LOCK_DIR and DONE_LOCK_TOKEN name and unlock the current lock whose
    recorded repo_root is this checkout; absent, malformed, or mismatched
    evidence refuses before writing (a meta-less or unreadable hold is
    unknown state, never guessed, and a recorded token naming another holder
    refuses the same way, the target run's owning run possibly still live
    under it). The target then classifies through ``classify_run_boundary``:
    only the ``orphan`` verdict adopts, so a terminal record on any file of
    the run (a shadow copy included) or an unreadable record refuses with no
    new manifest. The adopted composition also keeps ownership separation: a
    review path the caller claims owned while the adopted record marks it
    foreign refuses before any manifest is written (either declaration alone
    can be intentional; their intersection is contradictory input).

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

    # Explicit adoption: the caller must prove done-lock ownership of this
    # repository first, and the target must be a readable, root-matched,
    # orphan-classified manifest; its boundary (start_commit and owned paths,
    # plus its foreign markings) is carried verbatim into the new record.
    adopted: Optional[RunManifest] = None
    if args.adopt:
        lock_refusal = _caller_done_lock_refusal(ctx.repo_root)
        if lock_refusal is not None:
            return _cli_fail(
                f"write-manifest: cannot adopt {args.adopt}: no proven "
                f"done-lock ownership for this repository: {lock_refusal}"
            )
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
        boundary_verdict, _classified_run_id = classify_run_boundary(
            ctx.done_session_dir, _manifest_path(ctx.done_session_dir, args.adopt)
        )
        if boundary_verdict != "orphan":
            return _cli_fail(
                f"write-manifest: cannot adopt {args.adopt}: the run boundary "
                f"is {boundary_verdict}, not an interrupted orphan (only an "
                "orphan-classified boundary can be adopted; closure on any "
                "same-run record, shadow copies included, refuses the same)"
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
                "boundary); close it once with python3 "
                "scripts/done_sweep_gates_lib.py disposition-manifest "
                "--run-id "
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

    # Ownership separation (plan 2026-10-26-done-writer-adoption-guards):
    # either declaration alone can be intentional, but their intersection is
    # contradictory input - a path claimed owned while the adopted record
    # marks it foreign must not pass as owned - so the adopted composition
    # refuses the overlap before any manifest is written.
    if adopted is not None:
        owned_foreign = sorted(set(owned_review_paths) & set(foreign_review_paths))
        if owned_foreign:
            return _cli_fail(
                "write-manifest: ownership-conflict: review path(s) claimed "
                "both owned and foreign in the adopted composition: "
                + ", ".join(owned_foreign)
                + " (the intersection refuses before any manifest is "
                "written; whichever declaration is wrong, the composition "
                f"must not carry the conflict; adopted record {adopted.run_id})"

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
        # The linked-worktree foreign-by-arrival arm engages only on a fresh
        # boundary: an adopted manifest (--adopt; the wrapper's --from-
        # manifest re-entry never rewrites through this writer) never passes
        # an arrival marker, so the resume's fresh marker never silently
        # classifies the adopted run's mid-run staging docs foreign.
        auto_foreign, uncovered, arrival_refusal, arrival_classified = (
            _foreign_by_default_split(
                ctx,
                uncovered,
                owned_review_paths,
                arrival_marker=(
                    ctx.done_session_dir / marker_name
                    if adopted is None and marker_name is not None
                    else None
                ),
            )
        )
        if arrival_refusal is not None:
            return _cli_fail(
                "write-manifest: foreign-by-arrival: "
                + arrival_refusal
                + "; refusing the whole uncovered set fail-closed (no "
                "auto-foreign): "
                + ", ".join(uncovered)
            )
        if auto_foreign:
            foreign_review_paths = _dedup_preserving_order(
                foreign_review_paths + auto_foreign
            )
            if arrival_classified:
                # Bounded per the existing report-emission limit: at most
                # SAMPLE_LIMIT samples inline, the full list under the
                # done-session gate-reports home above the bound.
                arrival_listing, arrival_warnings = bounded_inline_listing(
                    ctx, "foreign-by-arrival", sorted(auto_foreign)
                )
                print(
                    "write-manifest: foreign-by-arrival: "
                    f"{len(auto_foreign)} gitignored staging candidate(s) "
                    "under the run-owned worktree's reviews home classified "
                    "foreign (mtime strictly predates the bound run-start "
                    f"marker's recorded epoch): {arrival_listing}"
                )
                for arrival_warning in arrival_warnings:
                    print(arrival_warning, file=sys.stderr)
            else:
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
    # The done boundary's admission-record merge (warn-only: every failure
    # reports on stderr and this boundary's own outcome stands).
    merge_admission_records_at_done_boundary(
        ctx,
        manifest.owned_paths,
        manifest.owned_plan_paths,
        manifest.owned_review_paths,
    )
    return 0


_SHADOW_PROPAGATION_PREFIX = "finalize-manifest: shadow propagation:"


def _shadow_propagation_report(message: str) -> None:
    """One propagation-arm report line on the operation's failure channel.
    The ``shadow propagation:`` prefix is distinct from every finalize
    outcome string the wrapper's grep-classified advice arms match on (plan
    docs/history/plans/2026-11-05-done-finalized-manifest-shadow.md), so a
    miss report can never re-route the finalize's own FAILED-line arms."""
    print(f"{_SHADOW_PROPAGATION_PREFIX} {message}", file=sys.stderr)


def _propagate_finalized_shadow(ctx: GateContext, manifest: RunManifest) -> None:
    """The finalize leg's terminal-state propagation (plan
    docs/history/plans/2026-11-05-done-finalized-manifest-shadow.md, Task 2):
    write the run's finalized manifest bytes over the surviving primary
    shadow record (``run-manifest-<run-id>.json`` in the primary checkout's
    done-session directory) so a completed worktree run stops
    re-classifying as interrupted after its source copy and worktree are
    gone. This arm is the one authoritative terminal-state writer into the
    primary shadow: only this operation's success path and its
    already-complete early return reach it (idempotent - the same finalized
    bytes), and no standalone command, no closeout-migration write, and no
    classifier write-back participates.

    Every outcome keeps the finalize's own exit semantics unchanged: the arm
    reports on the failure channel under the ``shadow propagation:`` prefix
    and returns; a miss never fails the finalize. Arms, in order:

    - the invocation checkout already is the primary checkout (the resolved
      primary done-session directory equals this checkout's own): a silent
      no-op skip - no rewrite, no miss report;
    - the primary checkout cannot be resolved, the migration helpers are
      unavailable, or the finalized source bytes cannot be read: one miss
      report, nothing written;
    - the shadow payload already carries terminal state (``complete`` true
      or a non-null ``dispositioned`` record): skipped with a report, never
      overwritten, so a sanctioned closure record is never destroyed;
    - the shadow payload disagrees with the finalized source identity
      (``run_id``, ``repo_root``, ``owned_plan_paths``), is unreadable, or
      carries a ``complete`` value that is not the strict pre-finalize
      false: one abort report, both files untouched;
    - the shadow is the strict pre-finalize twin: the finalized source
      bytes replace it atomically (a write refusal reports the miss with no
      partial write);
    - the shadow is absent: the run's closeout-migration record must
      witness the manifest's transfer (a verified ``migrated``/``renamed``/
      ``replaced`` row whose source names this manifest under a
      ``done-session`` directory, located through the migration helpers'
      session-slug and record-path resolution over the run's owned plan
      claims) before the finalized bytes are written as the surviving
      record; with neither the shadow nor a witness, one skip report and
      nothing is invented.
    """
    try:
        finalized_bytes = _manifest_path(
            ctx.done_session_dir, manifest.run_id
        ).read_bytes()
    except OSError as exc:
        _shadow_propagation_report(
            f"cannot read the finalized source bytes ({exc}); nothing propagated"
        )
        return
    try:
        from worktree_closeout_migrate import (  # stale deployed siblings degrade the arm to a report, never to a guess
            _closeout_manifest_candidate,
            _facts_tmp_root,
        )
    except Exception as exc:
        _shadow_propagation_report(
            "worktree_closeout_migrate helpers unavailable "
            f"({exc}); nothing propagated"
        )
        return
    primary, primary_err = _resolve_primary_checkout(ctx)
    if primary is None:
        _shadow_propagation_report(
            "primary checkout unresolved "
            f"({(primary_err or '').strip()[:200]}); nothing propagated"
        )
        return
    try:
        primary_session = _facts_tmp_root(primary) / "done-session"
    except Exception as exc:
        _shadow_propagation_report(
            f"primary facts tmp_dir unresolved ({exc}); nothing propagated"
        )
        return
    try:
        same_checkout = os.path.realpath(str(primary_session)) == os.path.realpath(
            str(ctx.done_session_dir)
        )
    except OSError:
        same_checkout = str(primary_session) == str(ctx.done_session_dir)
    if same_checkout:
        # The primary-dispatched closeout: the resolved primary shadow path
        # is the file the operation itself just finalized - a silent no-op
        # skip with no rewrite and no miss report.
        return
    shadow = primary_session / f"run-manifest-{manifest.run_id}.json"
    created_from_witness = False
    if not shadow.is_file():
        manifest_name = f"run-manifest-{manifest.run_id}.json"
        for plan_rel in manifest.owned_plan_paths:
            record, _explicit = _closeout_manifest_candidate(
                primary, Path(plan_rel), None
            )
            if record is None:
                continue
            try:
                payload = json.loads(record.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(payload, dict):
                continue
            for section in ("migrated", "renamed", "replaced"):
                rows = payload.get(section)
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    source_raw = row.get("source")
                    if (
                        row.get("verified") is True
                        and isinstance(source_raw, str)
                        and posixpath.basename(source_raw) == manifest_name
                        and "done-session" in posixpath.normpath(source_raw).split("/")
                    ):
                        created_from_witness = True
                        break
                if created_from_witness:
                    break
            if created_from_witness:
                break
            # Each owned plan claim contributes its canonical session-slug
            # record home (the migration helpers' own resolution, canonical
            # ``closeout-migration.json`` first, legacy twin second); the
            # first witness anywhere in the run's claim set authorizes the
            # surviving-record write.
        if not created_from_witness:
            _shadow_propagation_report(
                "no primary shadow and no closeout-migration transfer "
                f"witness for {manifest_name}; skipped (nothing invented)"
            )
            return
    else:
        try:
            payload = json.loads(shadow.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _shadow_propagation_report(
                "the primary shadow payload is unreadable "
                f"({exc}); run identity unverifiable; aborted, both files "
                "untouched"
            )
            return
        if not isinstance(payload, dict):
            _shadow_propagation_report(
                "the primary shadow payload is not an object; run identity "
                "unverifiable; aborted, both files untouched"
            )
            return
        if payload.get("complete") is True or payload.get("dispositioned") is not None:
            state = (
                "complete=true"
                if payload.get("complete") is True
                else "a dispositioned record"
            )
            _shadow_propagation_report(
                f"the primary shadow already carries terminal state ({state}); "
                "skipped without overwrite"
            )
            return
        mismatches: list[str] = []
        if payload.get("run_id") != manifest.run_id:
            mismatches.append(
                "run_id "
                + _sanitize_manifest_error_value(payload.get("run_id"))
            )
        if payload.get("repo_root") != manifest.repo_root:
            mismatches.append(
                "repo_root "
                + _sanitize_manifest_error_value(payload.get("repo_root"))
            )
        if payload.get("owned_plan_paths") != list(manifest.owned_plan_paths):
            mismatches.append("owned_plan_paths differs from the finalized source")
        if payload.get("complete") is not False:
            mismatches.append(
                "complete "
                + _sanitize_manifest_error_value(payload.get("complete"))
                + " is not the strict pre-finalize false"
            )
        if mismatches:
            _shadow_propagation_report(
                "identity mismatch between the primary shadow and the "
                f"finalized source ({'; '.join(mismatches)}); aborted, both "
                "files untouched"
            )
            return
    try:
        shadow.parent.mkdir(parents=True, exist_ok=True)
        tmp = shadow.parent / (shadow.name + ".tmp")
        try:
            tmp.write_bytes(finalized_bytes)
            os.replace(tmp, shadow)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise
    except OSError as exc:
        _shadow_propagation_report(
            f"cannot write {shadow} ({exc}); no partial write; the shadow is "
            "untouched"
        )
        return
    if created_from_witness:
        _shadow_propagation_report(
            "no shadow present and the closeout-migration record witnesses "
            f"the transfer; wrote the finalized bytes as the surviving "
            f"record {shadow}"
        )
    else:
        _shadow_propagation_report(
            f"wrote the finalized bytes over the primary shadow {shadow}"
        )


# --------------------------------------------------------------------------- #
# The admission record (plan
# docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-
# recovery, Task 1): the claim-keyed JSON object beside the execution claim
# in the PRIMARY checkout at the gateway's fixed relative path, carrying
# exactly the three owned-list fields so the consult's existing manifest
# reader reads it unchanged. It is never a ``run-manifest-*.json`` file and
# never lives under a done-session directory, so the done-session
# classification surface never sees it. The seeder imports the consult's
# plan derivation; the writer reuses the run manifest's atomic
# temp-plus-replace shape; every record mutation holds the existing repo
# merge lock (a verified inherited hold, else one try-once acquire through
# the closeout migrate's helper) and the merge arm updates an EXISTING
# record only, warn-only at the done boundary.
# --------------------------------------------------------------------------- #

# The execution-claim gateway's fixed relative claims home
# (scripts/execution_claim.sh CLAIMS_REL); the admission record lives
# beside the claim there, never a facts-resolved temp directory.
EXECUTION_CLAIMS_REL = Path("docs") / "tmp" / "execution-claims"

_ADMISSION_RECORD_SUFFIX = "-admission.json"
_ADMISSION_RECORD_FIELDS = (
    "owned_paths",
    "owned_plan_paths",
    "owned_review_paths",
)
_ADMISSION_MERGE_LABEL = "done-sweep-admission-record"


def _admission_warn(message: str) -> None:
    """One admission-record report line on the failure channel. Every
    message names the slug (or, before a slug resolves, the plan path), and
    a report never changes the done boundary's own exit."""
    print(f"admission-record: {message}", file=sys.stderr)


def admission_record_path(primary_root: Path, slug: str) -> Path:
    """The gateway's fixed relative record path for one plan slug: the
    primary checkout's execution-claims directory, the slug plus the
    ``-admission.json`` suffix (the consult reader's manifest shape reads it
    unchanged; the name never matches a ``run-manifest-*.json`` glob)."""
    return Path(primary_root) / EXECUTION_CLAIMS_REL / (
        f"{slug}{_ADMISSION_RECORD_SUFFIX}"
    )


def seed_admission_owned_paths(plan_path) -> list[str]:
    """The admission seed for one covering plan: the owned-path list the
    consult's ``owned_paths_from_plan`` derivation yields for the plan's
    ``Files:`` lists, imported at this module's top (never copied). The
    derivation's no-paths tool error reads as an empty seed: the gateway
    warns and writes no record instead, and the run stays on the consult's
    existing missing-source conservative verdict."""
    try:
        return list(owned_paths_from_plan(str(plan_path)))
    except dispatch_admission.ToolError:
        return []


def admission_record_payload(
    owned_paths: list[str],
    owned_plan_paths: list[str],
    owned_review_paths: list[str],
) -> dict:
    """The record's exact shape: a JSON object carrying exactly the three
    owned-list fields, nothing else."""
    return {
        "owned_paths": list(owned_paths),
        "owned_plan_paths": list(owned_plan_paths),
        "owned_review_paths": list(owned_review_paths),
    }


def write_admission_record(
    path: Path,
    owned_paths: list[str],
    owned_plan_paths: list[str],
    owned_review_paths: list[str],
) -> Path:
    """Atomically replace the record at ``path`` (temp file plus
    same-directory ``os.replace``, the ``write_run_manifest`` shape): a
    reader observes either the absent or the complete record, never a
    partial one."""
    payload = (
        json.dumps(
            admission_record_payload(
                owned_paths, owned_plan_paths, owned_review_paths
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
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


def read_admission_record(path: Path) -> Optional[dict]:
    """Tolerant read: an unreadable, unparseable, or non-object record
    returns None (the caller decides its own conservative arm), never an
    exception."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _admission_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def merge_admission_record_payload(
    existing: dict,
    owned_paths: list[str],
    owned_plan_paths: list[str],
    owned_review_paths: list[str],
) -> dict:
    """The monotone merge: the boundary's owned lists unioned per field with
    what the existing record already holds, deduplicated preserving order
    (existing items first), so a record update only ever adds paths."""
    return admission_record_payload(
        _dedup_preserving_order(
            _admission_str_list(existing.get("owned_paths")) + list(owned_paths)
        ),
        _dedup_preserving_order(
            _admission_str_list(existing.get("owned_plan_paths"))
            + list(owned_plan_paths)
        ),
        _dedup_preserving_order(
            _admission_str_list(existing.get("owned_review_paths"))
            + list(owned_review_paths)
        ),
    )


def _verify_inherited_merge_lock() -> tuple[bool, str]:
    """The gateway's verification shape (scripts/execution_claim.sh
    ``merge_lock_hold_or_reuse``) over an exported hold: the lock's meta
    record must be readable, its ``lock_token`` must equal the exported
    ``MERGE_LOCK_TOKEN``, and the recorded holder must be verifiably this
    boundary's - the recorded ``holder_pid`` is this process itself, or a
    live process whose ``holder_identity`` record matches the process
    table, and an exported ``MERGE_LOCK_HOLDER_PID`` (the gateway's holder
    pin) must equal the recorded ``holder_pid``. Any other state is an
    unverifiable hold, never guessed. Returns (verified, reason)."""
    lock_dir = os.environ.get("MERGE_LOCK_DIR", "")
    token = os.environ.get("MERGE_LOCK_TOKEN", "")
    if not lock_dir or not token:
        return False, "no MERGE_LOCK_DIR/MERGE_LOCK_TOKEN pair exported"
    meta = Path(lock_dir) / "meta.env"
    try:
        meta_text = meta.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"the lock's meta record {meta} is unreadable ({exc})"
    fields: dict[str, str] = {}
    for line in meta_text.splitlines():
        key, sep, value = line.partition("=")
        if sep and key and key not in fields:
            fields[key] = value
    if fields.get("lock_token") != token:
        return False, "the recorded lock_token does not match the exported token"
    holder_pid = fields.get("holder_pid", "")
    if not re.fullmatch(r"[1-9][0-9]*", holder_pid):
        return False, "the recorded holder_pid is not a positive pid"
    exported_holder = os.environ.get("MERGE_LOCK_HOLDER_PID", "")
    if exported_holder and exported_holder != holder_pid:
        return False, (
            f"the exported MERGE_LOCK_HOLDER_PID {exported_holder} does not "
            f"match the recorded holder_pid {holder_pid}"
        )
    if int(holder_pid) != os.getpid():
        try:
            proc = subprocess.run(
                ["ps", "-p", holder_pid, "-o", "lstart="],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, (
                f"the recorded holder_pid {holder_pid} cannot be probed "
                f"({exc})"
            )
        identity = proc.stdout.strip()
        recorded_identity = fields.get("holder_identity", "")
        if not identity or not recorded_identity or identity != recorded_identity:
            return False, (
                f"the recorded holder_pid {holder_pid} does not verify "
                "alive with the recorded holder_identity"
            )
    return True, ""


def _merge_admission_record_locked(
    ctx: GateContext,
    claims_dir: Path,
    slug: str,
    owned_paths: list[str],
    owned_plan_paths: list[str],
    owned_review_paths: list[str],
) -> None:
    """The under-lock record mutation: re-check the ownership evidence, then
    union the boundary's owned lists into the EXISTING record. Every
    refusal warns naming the slug and writes nothing; the done boundary
    keeps its own outcome."""
    claim_path = claims_dir / f"{slug}.md"
    if not claim_path.is_file():
        _admission_warn(
            f"slug {slug}: no execution claim at {claim_path}; the "
            "admission record is not updated"
        )
        return
    try:
        claim_text = claim_path.read_text(encoding="utf-8")
    except OSError as exc:
        _admission_warn(
            f"slug {slug}: the execution claim {claim_path} is unreadable "
            f"({exc}); the admission record is not updated"
        )
        return
    claim_branch = ""
    for line in claim_text.splitlines():
        if line.startswith("branch:"):
            claim_branch = line[len("branch:"):].strip()
            break
    current = ""
    proc = ctx.git("branch", "--show-current")
    if proc.returncode == 0:
        current = proc.stdout.strip()
    if not claim_branch or claim_branch != current:
        _admission_warn(
            f"slug {slug}: the execution claim records branch "
            f"{claim_branch or '<none>'} while this boundary checkout is on "
            f"{current or '<none>'}; the admission record is not updated"
        )
        return
    record_path = claims_dir / f"{slug}{_ADMISSION_RECORD_SUFFIX}"
    if not record_path.is_file():
        # The merge never creates: a boundary over a claim whose seed the
        # gateway never wrote (or retired) records nothing.
        return
    existing = read_admission_record(record_path)
    if existing is None:
        _admission_warn(
            f"slug {slug}: the existing admission record "
            f"{record_path.name} is unreadable or not a JSON object; the "
            "record is left unchanged"
        )
        return
    unexpected = sorted(set(existing) - set(_ADMISSION_RECORD_FIELDS))
    if unexpected:
        _admission_warn(
            f"slug {slug}: the existing admission record carries unexpected "
            f"field(s) {', '.join(unexpected)}; the record is left unchanged"
        )
        return
    merged = merge_admission_record_payload(
        existing, owned_paths, owned_plan_paths, owned_review_paths
    )
    if merged == existing:
        return
    try:
        write_admission_record(
            record_path,
            merged["owned_paths"],
            merged["owned_plan_paths"],
            merged["owned_review_paths"],
        )
    except OSError as exc:
        _admission_warn(
            f"slug {slug}: cannot write the admission record ({exc}); the "
            "boundary continues"
        )


def _merge_admission_record_for_slug(
    ctx: GateContext,
    slug: str,
    owned_paths: list[str],
    owned_plan_paths: list[str],
    owned_review_paths: list[str],
) -> None:
    """One slug's locked merge span: resolve the primary checkout, secure
    the repo merge lock (a verified inherited hold, else one try-once
    acquire through the closeout migrate's helper), merge under it, and
    release only a hold this span acquired itself. Every failure warns
    naming the slug and never fails the done boundary."""
    primary, primary_err = _resolve_primary_checkout(ctx)
    if primary is None:
        _admission_warn(
            f"slug {slug}: primary checkout unresolved "
            f"({(primary_err or '').strip()[:200]}); the admission record "
            "is not updated"
        )
        return
    claims_dir = primary / EXECUTION_CLAIMS_REL
    release = None
    inherited_dir = os.environ.get("MERGE_LOCK_DIR", "")
    inherited_token = os.environ.get("MERGE_LOCK_TOKEN", "")
    hold_verified = False
    if inherited_dir and inherited_token:
        hold_verified, reason = _verify_inherited_merge_lock()
        if not hold_verified:
            _admission_warn(
                f"slug {slug}: the exported merge-lock hold does not verify "
                f"as this boundary's ({reason}); falling back to a try-once "
                "acquire"
            )
    if not hold_verified:
        try:
            from worktree_closeout_migrate import (  # stale deployed siblings degrade the arm to a report, never to a guess
                _merge_lock_acquire,
                _merge_lock_release,
            )
        except Exception as exc:
            _admission_warn(
                f"slug {slug}: merge-lock helpers unavailable ({exc}); the "
                "admission record is not updated"
            )
            return
        exports, refused = _merge_lock_acquire(
            ctx.repo_root, _ADMISSION_MERGE_LABEL
        )
        if exports is None:
            detail = "; ".join(
                part.strip() for part in refused[:2] if part.strip()
            )
            _admission_warn(
                f"slug {slug}: merge-lock acquire refused "
                f"({detail[:200] or 'no refusal evidence'}); the admission "
                "record is not updated"
            )
            return

        def release():
            _merge_lock_release(ctx.repo_root, exports)

    try:
        _merge_admission_record_locked(
            ctx,
            claims_dir,
            slug,
            owned_paths,
            owned_plan_paths,
            owned_review_paths,
        )
    finally:
        if release is not None:
            release()


def merge_admission_records_at_done_boundary(
    ctx: GateContext,
    owned_paths: list[str],
    owned_plan_paths: list[str],
    owned_review_paths: list[str],
) -> None:
    """The done-boundary merge arm: for each owned plan path of the run's
    boundary, derive the artifact slug through the same derivation the
    execution-claim gateway uses (``plan_readiness.artifact_slug``) and
    merge the boundary's owned lists into that slug's admission record under
    the primary checkout's claims home. Warn-only: every failure reports on
    stderr and the boundary's own outcome is unchanged."""
    for plan_rel in _dedup_preserving_order(list(owned_plan_paths)):
        try:
            slug = plan_readiness.artifact_slug(Path(plan_rel))
        except ValueError as exc:
            _admission_warn(
                f"plan {plan_rel}: the artifact slug derivation failed "
                f"({exc}); the admission record is not updated"
            )
            continue
        _merge_admission_record_for_slug(
            ctx, slug, owned_paths, owned_plan_paths, owned_review_paths
        )


def _cmd_finalize_manifest(argv: list[str]) -> int:
    """Set the run manifest's ``complete`` flag to true in place (done Step 6,
    immediately before the done-lock release): the run reached the end, so it
    is never an interrupted run for a later Step 0. The success path and the
    already-complete early return also propagate the finalized bytes into the
    primary checkout's surviving shadow record for the same run-id (the
    terminal-state writer of plan
    docs/history/plans/2026-11-05-done-finalized-manifest-shadow.md; the arm
    reports on the failure channel and never changes the exit). Two-way
    identity
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
            "unchanged; if the run worktree has already been removed, "
            "the failed finalization step must be reported and not rerun "
            "from the primary checkout (let the existing lock-release "
            "steps run); future closeouts must run the done runner's "
            "finalize subcommand before worktree removal "
            "(development_lessons.md #326)"
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
        # Idempotent propagation: a re-run after an earlier skipped or
        # refused propagation still lands the same finalized bytes.
        _propagate_finalized_shadow(ctx, manifest)
        # The finalize boundary's admission-record merge (warn-only; the
        # monotone union makes the re-run idempotent like the shadow above).
        merge_admission_records_at_done_boundary(
            ctx,
            manifest.owned_paths,
            manifest.owned_plan_paths,
            manifest.owned_review_paths,
        )
        return 0
    manifest.complete = True
    try:
        path = write_run_manifest(manifest, ctx.done_session_dir)
    except OSError as exc:
        return _cli_fail(f"finalize-manifest: cannot rewrite the run manifest: {exc}")
    print(f"finalize-manifest: run {manifest.run_id} marked complete in {path}")
    _propagate_finalized_shadow(ctx, manifest)
    # The finalize boundary's admission-record merge (warn-only: every
    # failure reports on stderr and this boundary's own outcome stands).
    merge_admission_records_at_done_boundary(
        ctx,
        manifest.owned_paths,
        manifest.owned_plan_paths,
        manifest.owned_review_paths,
    )
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
    if command == "archive-ceremony-report":
        return _cmd_archive_ceremony_report(args[1:])
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
