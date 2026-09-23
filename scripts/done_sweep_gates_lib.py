#!/usr/bin/env python3
"""Done sweep gate runner lib: the done skill's deterministic gates as code.

Plan: ``docs/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md``,
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
- gate registry == the ten absorbed steps at gate and named sub-check
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
  conservative gating applies;
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
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
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
]
PRE_COMMIT_GATES = [
    "sensitive-data-scan",
    "em-dash-scan",
    "instruction-size",
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
            plans_dir=_resolve_dir(root, "plans_dir", "docs/plans"),
            plans_completed_dir=_resolve_dir(
                root, "plans_completed_dir", "docs/plans/completed"
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
def _parse_marker(path: Path, repo_root: Path) -> Optional[RunMarker]:
    """Parse one run-start marker; content must record this repo's root.

    Field order (done Step 0): first field epoch, last field PID, everything
    between is the repo root (spaces unambiguous).
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
    try:
        return os.path.realpath(recorded_root) != os.path.realpath(str(repo_root))
    except OSError:
        return False


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


def _porcelain_paths(ctx: GateContext, pathspec: str) -> tuple[list[str], list[str]]:
    """Porcelain plus ignored-matching arms over a pathspec; returns
    (tracked_or_untracked_paths, ignored_paths).

    Name-only convenience over ``_porcelain_lines``: status letters are
    stripped and a rename row keeps only its new side. Gates whose
    contract needs the change types (doc-registry check-writes stdin)
    must use ``_porcelain_lines`` + ``_ignored_paths`` instead.
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
            ordinary.append(rest)
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
    # Rejected archive: docs/plans/rejected/ holds plans rejected by
    # explicit decision. It is archive surface like the completed dir:
    # never a readiness candidate, and only its OWN deliverable lines are
    # pruned (see docs/plans/rejected/README.md).
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

    session_head_file = ctx.done_session_dir / "session-start-head.txt"
    base = "ORIG_HEAD"
    if session_head_file.is_file():
        try:
            base = session_head_file.read_text(encoding="utf-8").strip() or base
        except OSError:
            base = "ORIG_HEAD"
    verify = ctx.git("rev-parse", "-q", "--verify", f"{base}^{{commit}}")
    if verify.returncode != 0:
        base = ctx.git("rev-parse", "HEAD").stdout.strip()

    # Change-typed union, never a name-only downgrade (base Step 2.648):
    # porcelain rows carry their XY status letters verbatim (a rename row
    # is ``R  old -> new`` so the validator's parse_change_line gates both
    # sides), the committed-since-session-start rows keep their
    # ``A/M/D<TAB>path`` name-status form, and ignored files (which have
    # no change type) stay bare rows.
    porcelain_rows = _porcelain_lines(ctx, ".")
    ignored = _session_ignored_paths(ctx, _ignored_paths(ctx, "."))
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
                warnings=[],
            )
        arm_note = f"check-writes ok over {len(union)} changed paths"

    # Re-anchor the session base for the next run (fail-closed by design).
    head = ctx.git("rev-parse", "HEAD").stdout.strip()
    if head:
        try:
            ctx.done_session_dir.mkdir(parents=True, exist_ok=True)
            session_head_file.write_text(head + "\n", encoding="utf-8")
        except OSError:
            pass
    return GateResult(
        gate, 0, f"doc registry: validate ok; {arm_note}", warnings=[]
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
def derive_review_staging_candidates(ctx: GateContext) -> list[Path]:
    """Porcelain plus ignored-matching paths under reviews_dir, filtered by the
    validator's own staging-path predicate and restricted to the session
    window. Never a bare glob, never chat recall."""
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    if not window.anchored or window.start_epoch is None:
        return []
    start = window.start_epoch
    end = time.time() + 1.0
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
        try:
            mtime = absolute.stat().st_mtime
        except OSError:
            continue
        if start <= mtime <= end:
            candidates.append(absolute)
    return sorted(candidates)


def gate_review_staging(ctx: GateContext) -> GateResult:
    gate = "review-staging"
    candidates = derive_review_staging_candidates(ctx)
    if not candidates:
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
            warnings=[],
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
            warnings=[],
        )
    return GateResult(
        gate,
        0,
        f"review-staging validation passed for {len(candidates)} session-touched "
        "staging doc(s)",
        warnings=[],
    )


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
    plans_dir (e.g. ``docs/plans/deferred/<slug>.md``), so the pending
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
        "usage: done_sweep_gates.sh <pre-docs|pre-commit|list-gates>\n"
        "phases: pre-docs (done Steps 1.5..2.62 gates), pre-commit (done "
        "Steps 2.7/2.76/2.8 mechanical gates)\n"
        "list-gates prints the ten absorbed gate ids in phase order"
    )


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(_usage(), file=sys.stderr)
        return 0 if args else 2
    command = args[0]
    if command == "list-gates":
        for gate_id in PRE_DOCS_GATES + PRE_COMMIT_GATES:
            print(gate_id)
        return 0
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
