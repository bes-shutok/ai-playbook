#!/usr/bin/env python3
"""Consult-path profiling harness for the skill-gate (plan
2026-11-09-hook-timeout-recurrence-diagnostic, Task 1).

``ConsultProfiler`` drives and times ONE gated consult (the consult path:
the real Claude adapter's subprocess chain plus the core's internal stages)
inside a populated sandbox: an isolated temporary HOME per worker whose
``.ai-playbook/scripts`` symlinks resolve into the worktree's own scripts,
and a temp git fixture repo holding the gated target file. The core's
internal stages come from its opt-in timing emission (``SKILL_GATE_TIMING_PATH``
/ ``SKILL_GATE_TIMING_NONCE``); the adapter's outer subprocess stages are
timed by VERBATIM ARGV REPLICATION (each argv re-derived from the adapter
source at harness start and re-run as a separate timed probe), and a timed
bare ``python3 -c pass`` (the interpreter probe) runs alongside each consult.

Degraded-path classification follows the plan's Terms "degraded-path sample"
rule (positive core-execution witness); clean-path statistics aggregate
clean samples only. Analyze mode reads retained sample sets from an output
directory and writes the analysis record (``analysis.json``) beside them,
merging every worker's samples per (kind, repeat, class). A completed run
removes its sandbox trees under ``<out>/sandboxes/`` (``--keep-sandboxes``
retains them; an aborted run keeps its sandboxes for inspection); the
retained sample files always stay.

CLI:
    python3 scripts/profile_skill_gate_consult.py load  --out DIR [options]
    python3 scripts/profile_skill_gate_consult.py analyze --out DIR

Stdlib only. The harness is measurement tooling: it changes no decision
byte, refusal class, or pin of the guard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths  # noqa: E402  (live read of the frozen resolver pin)
import skill_gate  # noqa: E402  (BLOCK_MESSAGE single source)

REPO_ROOT = Path(__file__).resolve().parent.parent
ADAPTER_PATH = REPO_ROOT / "agents" / "hooks" / "skill-gate" / "claude.sh"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "tmp" / "profile-skill-gate-consult-samples"

BLOCK_MESSAGE = skill_gate.BLOCK_MESSAGE

#: The host per-hook timeout (README recipe; hand-synced pin, at least 10s)
#: and the per-consult bound the harness enforces (killing the consult's own
#: process group).
HOST_HOOK_TIMEOUT_S = 10.0
PER_CONSULT_TIMEOUT_S = 10.0
#: Incident regime threshold: half the host timeout (Terms "incident regime").
REGIME_FRACTION = 0.5
#: Clean-sample floor per decision-path class per loaded repeat (Terms).
CLEAN_SAMPLE_FLOOR = 20
#: A floor-missing repeat is re-run at most twice (Terms).
MAX_REPEAT_RERUNS = 2
#: Dominance rule bounds (Terms "dominant stage").
DOMINANCE_FLOOR = 0.40
DOMINANCE_RATIO = 2.0
#: The frozen resolver pin, read live from facts_paths.
RESOLVER_BOUND_S = float(facts_paths.RESOLVER_GIT_TIMEOUT_S)
RESOLVER_BOUND_EPSILON_S = 0.05

SESSION_ENV_VARS = (
    "CLAUDE_CODE_SESSION_ID",
    "CURSOR_SESSION_ID",
    "CURSOR_CONVERSATION_ID",
    "CODEX_SESSION_ID",
)
GIT_ISOLATION_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")
TIMING_PATH_ENV = skill_gate.TIMING_PATH_ENV
TIMING_NONCE_ENV = skill_gate.TIMING_NONCE_ENV

CLEAN_KEYING_VALUES = frozenset({"env-var", "project-only"})

#: Core-internal stage names as emitted by the core's timing record, with
#: their provenance surface (stage vocabulary, Terms).
CORE_TIMING_STAGES = (
    "keying_log_append",    # facts_paths.py
    "plans_dir_resolve",    # facts_paths.py
    "classify_target",      # skill_gate.py
    "project_key_resolve",  # facts_paths.py (includes the git resolver)
    "session_derive",       # skill_gate.py
    "marker_check",         # skill_gate.py
)
#: Replicated-probe stage names (verbatim argv replication).
PROBE_STAGES = (
    "payload_extract",
    "session_channel",
    "core_invocation",
    "decision_parse",
    "git_resolver",
)
#: Per-consult interpreter probe (timed bare ``python3 -c pass``).
INTERPRETER_PROBE_STAGE = "interpreter_probe"
#: Derived stage: end-to-end minus the measured component stages.
RESIDUAL_STAGE = "residual"

#: Component stages that partition the end-to-end (dominance inputs). The
#: reference probes (``core_invocation`` = the whole core subprocess,
#: ``interpreter_probe`` = bare startup) are NOT components: the core's
#: subprocess cost is decomposed by the timing-record stages, and the
#: interpreter probe is the correction term for the session-channel stage.
COMPONENT_STAGES = CORE_TIMING_STAGES + (
    "payload_extract",
    "session_channel",
    "decision_parse",
    RESIDUAL_STAGE,
)

STAGE_PROVENANCE = {}
for _name in CORE_TIMING_STAGES:
    STAGE_PROVENANCE[_name] = "timing-record"
for _name in ("payload_extract", "session_channel", "core_invocation",
              "decision_parse", "git_resolver", INTERPRETER_PROBE_STAGE):
    STAGE_PROVENANCE[_name] = "replicated-probe"
STAGE_PROVENANCE[RESIDUAL_STAGE] = "derived"

#: Stage-to-candidate mapping (Terms "stage vocabulary"). ``session_channel``
#: is resolved conditionally at analysis time (see ``stage_candidate``).
STAGE_CANDIDATE = {
    "keying_log_append": "no-candidate",
    "plans_dir_resolve": "no-candidate",
    "project_key_resolve": "no-candidate",
    "git_resolver": "no-candidate",
    "classify_target": "(c)",
    "session_derive": "(c)",
    "marker_check": "(c)",
    "payload_extract": "(a)",
    "decision_parse": "(a)",
    "residual": "(a)",
    "interpreter_probe": "reference-probe",
    "core_invocation": "reference-probe",
}

#: The pinned adapter replica: each literal snippet must appear EXACTLY once
#: in the adapter source, and exactly six code ``python3`` invocations must
#: exist (comments excluded). The replica's four ``-c`` bodies are extracted
#: in source order: payload extraction, decision parse, allow branch, deny
#: branch.
ADAPTER_PINNED_SNIPPETS = (
    ("payload_extract", '"$payload" | python3 -c \'import json,sys'),
    ("session_channel", 'SID="$(python3 "$SESSION_CHANNEL")"'),
    (
        "core_invocation",
        'core_out="$(python3 "$CORE" --target "$target" '
        '${cwd_args[@]+"${cwd_args[@]}"} '
        '${session_args[@]+"${session_args[@]}"} 2>/dev/null)"',
    ),
    ("decision_parse", "decision=\"$(printf '%s' \"$core_out\" | python3 -c 'import json,sys"),
    ("allow_branch", "allow=\"$(printf '%s' \"$decision\" | python3 -c 'import json,sys"),
    ("deny_branch", "deny_reason=\"$(printf '%s' \"$decision\" | python3 -c 'import json,sys"),
)
EXPECTED_PYTHON3_INVOCATIONS = 6
EXPECTED_C_BODIES = 4

SAMPLE_FILE_RE = re.compile(
    r"^samples-(?P<kind>idle|loaded|emissionoff)-r(?P<repeat>\d+)"
    r"-rr(?P<rerun>\d+)-c(?P<cls>allow|block)-w(?P<worker>\d+)\.json$"
)


class SelfCheckError(RuntimeError):
    """Loud harness abort: a startup self-check failed."""


# --------------------------------------------------------------------------- #
# Percentiles and aggregation (pure; no environment access).
# --------------------------------------------------------------------------- #
def percentile(values, q: float) -> float:
    """Linear-interpolated percentile of a non-empty list of floats."""
    if not values:
        raise ValueError("percentile of an empty list")
    vs = sorted(float(v) for v in values)
    if len(vs) == 1 or q <= 0.0:
        return vs[0]
    if q >= 1.0:
        return vs[-1]
    pos = (len(vs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vs[lo]
    return vs[lo] + (vs[hi] - vs[lo]) * (pos - lo)


def sample_stage_value(sample: dict, stage: str):
    """One sample's duration for ``stage`` (None when unmeasured).

    ``residual`` is derived per sample: end-to-end minus the measured
    component stages, floored at 0 (the probes are separate runs, so small
    negative drift is measurement noise, not a real negative stage).
    """
    if stage == RESIDUAL_STAGE:
        stages = sample.get("stages") or {}
        probes = sample.get("probe_stages") or {}
        measured = sum(
            v for v in list(stages.values())
            + [probes.get(n) for n in ("payload_extract", "session_channel", "decision_parse")]
            if isinstance(v, (int, float))
        )
        e2e = sample.get("e2e_s")
        if not isinstance(e2e, (int, float)):
            return None
        return max(0.0, e2e - measured)
    for source in ("stages", "probe_stages"):
        value = (sample.get(source) or {}).get(stage)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def aggregate_clean(samples: dict) -> dict:
    """Aggregate over CLEAN samples only, per decision-path class.

    Returns ``{"by_class": {class: {count, p50, p95, max, stage_shares,
    interpreter_probe_share}}, "degraded_counts": {label: n}, "total",
    "clean_total"}``. Stage shares are each component stage's clean p95 over
    the class's clean end-to-end p95 (the dominance rule's input). The
    interpreter probe's share is computed beside them but kept OUT of
    ``stage_shares`` (it is not a dominance component); it feeds the
    session-channel correction only (Terms "stage vocabulary").
    """
    clean = [s for s in samples if s.get("status") == "clean"]
    degraded = [s for s in samples if s.get("status") != "clean"]
    by_class = {}
    for class_name in ("allow", "block"):
        cls = [s for s in clean if s.get("class") == class_name]
        e2e = [s["e2e_s"] for s in cls if isinstance(s.get("e2e_s"), (int, float))]
        stats = {
            "count": len(cls),
            "p50": percentile(e2e, 0.50) if e2e else None,
            "p95": percentile(e2e, 0.95) if e2e else None,
            "max": max(e2e) if e2e else None,
            "stage_shares": {},
            "all_sample_max": max(
                (s["e2e_s"] for s in samples
                 if s.get("class") == class_name
                 and isinstance(s.get("e2e_s"), (int, float))),
                default=None,
            ),
        }
        if e2e and stats["p95"]:
            for stage in COMPONENT_STAGES:
                values = [
                    v for v in (sample_stage_value(s, stage) for s in cls)
                    if v is not None
                ]
                if values:
                    stats["stage_shares"][stage] = (
                        percentile(values, 0.95) / stats["p95"]
                    )
            probe_values = [
                v for v in (sample_stage_value(s, INTERPRETER_PROBE_STAGE)
                            for s in cls)
                if v is not None
            ]
            if probe_values:
                stats["interpreter_probe_share"] = (
                    percentile(probe_values, 0.95) / stats["p95"]
                )
        by_class[class_name] = stats
    return {
        "by_class": by_class,
        "degraded_counts": dict(
            Counter(s.get("degraded_label") or "unlabeled" for s in degraded)
        ),
        "total": len(samples),
        "clean_total": len(clean),
    }


# --------------------------------------------------------------------------- #
# Degraded-path classification (Terms "degraded-path sample"; pure).
# --------------------------------------------------------------------------- #
def adapter_decision_readable(class_name: str, exit_code, stderr_text: str) -> bool:
    """Whether the consult's decision is readable at the adapter boundary.

    Allow: exit 0 (no stdout by contract). Block: exit 2 with the deny text
    on stderr. An adapter-level fail-open (core never ran) is exit 0 with no
    keying line - readable at the boundary, caught by the keying witness.
    """
    if class_name == "block":
        return exit_code == 2 and BLOCK_MESSAGE in (stderr_text or "")
    return exit_code == 0


def classify_sample(sample: dict, *, resolver_bound_s: float = RESOLVER_BOUND_S):
    """Classify one sample. Returns ``(status, label, detail)``.

    Clean requires the full positive core-execution witness (Terms): a
    timing record with the expected nonce (emission-on only), a keying line
    in the sandbox hooks log whose value is env-var or project-only, a
    readable non-empty decision, and no per-consult timeout. Labels:
    resolver-failed / resolver-timeout (5s bound) / timed-out / fail-open /
    unreadable. Degraded samples never enter clean-path statistics.
    """
    if sample.get("timed_out"):
        return "degraded", "timed-out", {"reason": "per-consult timeout exceeded"}
    keying_values = [
        v for v in (sample.get("keying_values") or [])
        if isinstance(v, str) and v.strip()
    ]
    special = next(
        (v for v in keying_values if v not in CLEAN_KEYING_VALUES), None
    )
    if special == "no-anchor":
        rs = sample.get("resolver_stage_s")
        at_bound = (
            isinstance(rs, (int, float))
            and rs >= resolver_bound_s - RESOLVER_BOUND_EPSILON_S
        ) or bool(sample.get("resolver_probe_timed_out"))
        label = "resolver-timeout" if at_bound else "resolver-failed"
        return "degraded", label, {
            "reason": "keying=no-anchor (git resolver failed)",
            "resolver_stage_s": rs,
        }
    if special is not None:
        return "degraded", "fail-open", {"reason": f"keying={special}"}
    if not sample.get("decision_readable"):
        return "degraded", "unreadable", {"reason": "decision unreadable or empty"}
    if not keying_values:
        return "degraded", "unreadable", {
            "reason": "no keying line in the sandbox hooks log",
        }
    if sample.get("emission") and not sample.get("timing_nonce_ok"):
        return "degraded", "unreadable", {
            "reason": "timing witness missing (no record with the expected nonce)",
        }
    return "clean", "", {"reason": "full positive core-execution witness"}


# --------------------------------------------------------------------------- #
# Dominance helpers (Terms "dominant stage"; pure).
# --------------------------------------------------------------------------- #
def stage_dominant_in_class(shares: dict, floor: float = DOMINANCE_FLOOR,
                            ratio: float = DOMINANCE_RATIO):
    """Apply the Terms rule to ONE class's component-stage shares.

    Returns ``(stage_or_None, fields)``; a stage is dominant when its share
    is >= floor (0.40) AND >= ratio (2x) the runner-up's share. Negative
    cases return None with ``failing_bound`` = "floor" | "ratio".
    """
    if not shares:
        return None, {"failing_bound": "empty", "floor": floor, "ratio": ratio}
    ranked = sorted(
        ((k, float(v)) for k, v in shares.items() if isinstance(v, (int, float))),
        key=lambda kv: kv[1], reverse=True,
    )
    top_name, top = ranked[0]
    runner_name, runner_up = (ranked[1] if len(ranked) > 1 else (None, 0.0))
    fields = {
        "stage": top_name,
        "share": top,
        "runner_up_stage": runner_name,
        "runner_up": runner_up,
        "floor": floor,
        "ratio": ratio,
    }
    if top < floor:
        fields["failing_bound"] = "floor"
        return None, fields
    if runner_up > 0 and top < ratio * runner_up:
        fields["failing_bound"] = "ratio"
        return None, fields
    fields["failing_bound"] = None
    return top_name, fields


#: The decision-path classes the dominant stage is defined over (Terms: a
#: stage is dominant only when it dominates in BOTH measured classes).
DOMINANCE_EXPECTED_CLASSES = ("allow", "block")


def dominance_verdict(per_class_shares: dict, floor: float = DOMINANCE_FLOOR,
                      ratio: float = DOMINANCE_RATIO,
                      expected_classes=DOMINANCE_EXPECTED_CLASSES) -> dict:
    """Combine per-class results: dominant iff the SAME stage dominates in
    BOTH expected classes. A degenerate input (an expected class missing or
    contributing no per-class result) can never yield ``dominant``:
    otherwise ``no-dominant`` with the per-class fields and a ``reason``
    ("degenerate-input-missing-class", "dominant-in-one-class-only", or
    "no-stage-meets-both-bounds").
    """
    per_class = {}
    winners = {}
    for class_name, shares in per_class_shares.items():
        stage, fields = stage_dominant_in_class(shares, floor, ratio)
        per_class[class_name] = {"dominant": stage, **fields}
        if stage:
            winners[class_name] = stage
    missing = [c for c in expected_classes if not per_class_shares.get(c)]
    if missing:
        return {
            "verdict": "no-dominant",
            "reason": "degenerate-input-missing-class",
            "missing_classes": missing,
            "per_class": per_class,
        }
    if len(winners) == len(expected_classes) \
            and len(set(winners.values())) == 1:
        stage = next(iter(winners.values()))
        return {"verdict": "dominant", "stage": stage, "per_class": per_class}
    reason = (
        "dominant-in-one-class-only" if winners else "no-stage-meets-both-bounds"
    )
    return {
        "verdict": "no-dominant",
        "reason": reason,
        "per_class": per_class,
    }


def worse_run_select(candidates: list) -> dict:
    """The worse run among one class's counted repeats: highest loaded
    end-to-end p95 (ties: later repeat/rerun). It governs that class."""
    return max(
        candidates,
        key=lambda c: (
            float(c.get("e2e_p95_s") or 0.0),
            int(c.get("repeat", 0)),
            int(c.get("rerun", 0)),
        ),
    )


def session_channel_corrected_shares(shares: dict) -> dict:
    """Shares with the session-channel stage corrected by the interpreter
    probe's share (Terms: session-channel maps to (b) only when its share
    MINUS the interpreter probe's share still dominates)."""
    corrected = dict(shares)
    sc = float(corrected.get("session_channel") or 0.0)
    ip = float(corrected.get(INTERPRETER_PROBE_STAGE) or 0.0)
    corrected["session_channel"] = max(0.0, sc - ip)
    return corrected


def stage_candidate(stage: str, dominant_stage, shares: dict,
                    floor: float = DOMINANCE_FLOOR,
                    ratio: float = DOMINANCE_RATIO) -> str:
    """Map one stage through the stage vocabulary to at most one candidate."""
    if stage == "session_channel":
        if dominant_stage != "session_channel":
            return "no-candidate"
        corrected = session_channel_corrected_shares(shares)
        still, _ = stage_dominant_in_class(corrected, floor, ratio)
        return "(b)" if still == "session_channel" else "no-candidate"
    return STAGE_CANDIDATE.get(stage, "no-candidate")


# --------------------------------------------------------------------------- #
# Floor status (Terms "clean-sample floor").
# --------------------------------------------------------------------------- #
def floor_status(samples: list, classes=("allow", "block")) -> dict:
    """Clean-sample floor per class + the degraded-label breakdown + the
    incident-regime flag (timed-out/resolver-timeout dominating the
    degraded share)."""
    per_class = {}
    degraded = [s for s in samples if s.get("status") != "clean"]
    for class_name in classes:
        clean_n = sum(
            1 for s in samples
            if s.get("status") == "clean" and s.get("class") == class_name
        )
        per_class[class_name] = {
            "clean": clean_n,
            "floor": CLEAN_SAMPLE_FLOOR,
            "met": clean_n >= CLEAN_SAMPLE_FLOOR,
        }
    breakdown = Counter(
        s.get("degraded_label") or "unlabeled" for s in degraded
    )
    budget_labels = breakdown.get("timed-out", 0) + breakdown.get("resolver-timeout", 0)
    incident = bool(degraded) and budget_labels * 2 >= len(degraded)
    return {
        "met": all(v["met"] for v in per_class.values()),
        "per_class": per_class,
        "degraded_label_breakdown": dict(breakdown),
        "incident_regime_reached": incident,
    }


# --------------------------------------------------------------------------- #
# Sample-set files (retained raw samples) and the manifest.
# --------------------------------------------------------------------------- #
def sample_filename(kind: str, repeat: int, rerun: int, class_name: str,
                    worker: int) -> str:
    return f"samples-{kind}-r{repeat}-rr{rerun}-c{class_name}-w{worker}.json"


def write_samples_file(out_dir: Path, *, kind: str, repeat: int, rerun: int,
                       class_name: str, worker: int, samples: list,
                       failure_counts: dict, probe_reference: dict | None = None) -> Path:
    path = out_dir / sample_filename(kind, repeat, rerun, class_name, worker)
    path.write_text(json.dumps({
        "kind": kind,
        "repeat": repeat,
        "rerun": rerun,
        "class": class_name,
        "worker": worker,
        "failure_counts": failure_counts,
        "probe_reference": probe_reference or {},
        "samples": samples,
    }, indent=1), encoding="utf-8")
    return path


def update_manifest(out_dir: Path, invocation_id: str, summary: dict) -> None:
    path = out_dir / "manifest.json"
    data = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
    data[invocation_id] = summary
    path.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")


def load_sample_sets(out_dir: Path) -> dict:
    """Load retained sample files for analysis.

    Per (kind, repeat, class, WORKER), the HIGHEST rerun replaces the reruns
    it redoes; the per-worker sample lists are then MERGED across workers
    within each (kind, repeat, class) so a multi-worker run keeps every
    worker's samples (failure counts summed, per-worker probe references
    retained under ``probe_reference`` keyed by worker id)."""
    grouped = {}
    for path in sorted(out_dir.glob("samples-*.json")):
        m = SAMPLE_FILE_RE.match(path.name)
        if not m:
            continue
        key = (
            m.group("kind"), int(m.group("repeat")), m.group("cls"),
            int(m.group("worker")),
        )
        rr = int(m.group("rerun"))
        if key not in grouped or rr >= grouped[key][0]:
            grouped[key] = (rr, path)
    sets: dict = {"idle": {}, "loaded": {}, "emissionoff": {}}
    per_class_workers: dict = {}
    for (kind, repeat, class_name, worker), (rerun, path) in grouped.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        slot = per_class_workers.setdefault((kind, repeat, class_name), {})
        slot[worker] = (rerun, data)
    for (kind, repeat, class_name), workers in per_class_workers.items():
        worker_ids = sorted(workers)
        samples: list = []
        failure_counts: Counter = Counter()
        for worker in worker_ids:
            _rerun, data = workers[worker]
            samples.extend(data.get("samples") or [])
            failure_counts.update(data.get("failure_counts") or {})
        sets.setdefault(kind, {}).setdefault(repeat, {})[class_name] = {
            "kind": kind,
            "repeat": repeat,
            "rerun": max(workers[w][0] for w in worker_ids),
            "class": class_name,
            "workers": worker_ids,
            "samples": samples,
            "failure_counts": dict(failure_counts),
            "probe_reference": {
                str(w): workers[w][1].get("probe_reference") or {}
                for w in worker_ids
            },
        }
    return sets


# --------------------------------------------------------------------------- #
# Analyze mode (Terms "analysis record").
# --------------------------------------------------------------------------- #
def analyze_sets(out_dir: Path) -> dict:
    """Write the analysis record beside the sample sets and return it."""
    out_dir = Path(out_dir)
    sets = load_sample_sets(out_dir)
    manifest = {}
    manifest_path = out_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {}

    loaded = sets.get("loaded", {})
    repeats = sorted(loaded.keys())
    per_class_stage_shares = {}
    per_class_probe_share = {}
    worse_run = {}
    loaded_max = {}
    counted_samples = []
    candidates_by_class = {}
    floor_missed = {}

    for class_name in ("allow", "block"):
        candidates = []
        for repeat in repeats:
            data = loaded[repeat].get(class_name)
            if not data:
                continue
            samples = data.get("samples") or []
            counted_samples.extend(samples)
            agg = aggregate_clean(samples)
            stats = agg["by_class"].get(class_name) or {}
            p95 = stats.get("p95")
            if p95 is None:
                continue
            candidates.append({
                "class": class_name,
                "repeat": repeat,
                "rerun": data.get("rerun", 0),
                "e2e_p95_s": p95,
                "clean": stats.get("count", 0),
                "stage_shares": stats.get("stage_shares") or {},
                "interpreter_probe_share": stats.get("interpreter_probe_share"),
                "all_sample_max": stats.get("all_sample_max"),
                "aggregate": agg,
            })
        if not candidates:
            continue
        meeting = [c for c in candidates
                   if c["clean"] >= CLEAN_SAMPLE_FLOOR]
        floor_missed[class_name] = not bool(meeting)
        pool = meeting or candidates
        worse = worse_run_select(pool)
        worse_run[class_name] = {
            "repeat": worse["repeat"],
            "rerun": worse["rerun"],
            "e2e_p95_s": worse["e2e_p95_s"],
            "clean": worse["clean"],
        }
        per_class_stage_shares[class_name] = worse["stage_shares"]
        per_class_probe_share[class_name] = worse.get("interpreter_probe_share")
        loaded_max[class_name] = {
            "all_samples_s": worse.get("all_sample_max"),
            "clean_only_s": worse["aggregate"]["by_class"][class_name].get("max"),
        }
        candidates_by_class[class_name] = candidates

    regime_threshold_s = HOST_HOOK_TIMEOUT_S * REGIME_FRACTION
    regime_max_s = None
    regime_class = None
    for class_name, mx in loaded_max.items():
        all_max = mx.get("all_samples_s")
        if all_max is not None and (regime_max_s is None or all_max > regime_max_s):
            regime_max_s = all_max
            regime_class = class_name
    regime = {
        "reached": bool(regime_max_s is not None
                        and regime_max_s >= regime_threshold_s),
        "threshold_s": regime_threshold_s,
        "worse_run_all_sample_max_s": regime_max_s,
        "worse_run_class": regime_class,
    }

    # Terms: no stage verdict is drawn outside the incident regime, and a
    # repeat still under the clean-sample floor draws no stage verdict
    # either. The suppression is recorded explicitly on the dominance
    # record; per-class shares stay available beside it.
    suppression_reasons = []
    if any(floor_missed.values()):
        suppression_reasons.append("floor-missed")
    if not regime["reached"]:
        suppression_reasons.append("regime-not-reached")
    if suppression_reasons:
        dominance = {
            "verdict": None,
            "reason": "+".join(suppression_reasons),
            "per_class": {},
        }
    else:
        dominance = dominance_verdict(per_class_stage_shares)

    resolver_counts = {
        "resolver-failed": sum(
            1 for s in counted_samples
            if s.get("degraded_label") == "resolver-failed"
        ),
        "resolver-timeout": sum(
            1 for s in counted_samples
            if s.get("degraded_label") == "resolver-timeout"
        ),
    }

    emission_on_block_p95 = None
    if "block" in per_class_stage_shares and worse_run.get("block"):
        emission_on_block_p95 = worse_run["block"]["e2e_p95_s"]
    emission_off_p95 = None
    for repeat in sorted(sets.get("emissionoff", {}).keys()):
        data = sets["emissionoff"][repeat].get("block")
        if not data:
            continue
        agg = aggregate_clean(data.get("samples") or [])
        p95 = agg["by_class"]["block"].get("p95")
        if p95 is not None:
            emission_off_p95 = p95

    stage_candidates = {}
    for class_name, shares in per_class_stage_shares.items():
        dominant = dominance["per_class"].get(class_name, {}).get("dominant")
        # The interpreter probe enters the share inputs for the session-
        # channel correction ONLY (Terms "stage vocabulary"); it is never a
        # dominance component, so it stays out of ``shares`` itself.
        correction_shares = dict(shares)
        probe_share = per_class_probe_share.get(class_name)
        if probe_share is not None:
            correction_shares[INTERPRETER_PROBE_STAGE] = probe_share
        for stage in shares:
            mapped = stage_candidate(stage, dominant, correction_shares)
            if stage not in stage_candidates or stage_candidates[stage] == mapped:
                stage_candidates[stage] = mapped
            else:
                # Same stage mapped differently per class: keep the
                # no-candidate (more conservative) reading.
                stage_candidates[stage] = (
                    mapped if mapped == "no-candidate"
                    else stage_candidates[stage]
                )
    for stage in COMPONENT_STAGES:
        stage_candidates.setdefault(stage, STAGE_CANDIDATE.get(stage, "no-candidate"))

    # Session-channel conditional mapping is finalized per class where it
    # could dominate; the conservative fold above only ever narrows to
    # no-candidate, never widens to (b).

    record = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": host_summary(),
        "run_context": {
            "repeats": repeats,
            "manifest": manifest,
            "worker_ceiling": host_worker_ceiling(),
        },
        "worse_run": worse_run,
        "per_class_stage_shares": per_class_stage_shares,
        "interpreter_probe_shares": {
            class_name: per_class_probe_share[class_name]
            for class_name in sorted(per_class_probe_share)
        },
        "regime": regime,
        "resolver_counts": resolver_counts,
        "loaded_max": loaded_max,
        "emission_on_block_p95_s": emission_on_block_p95,
        "emission_off_p95_s": emission_off_p95,
        "dominance": dominance,
        "stage_provenance": {
            stage: STAGE_PROVENANCE.get(stage, "unknown")
            for stage in sorted(
                set(stage_candidates) | set(COMPONENT_STAGES)
                | set(PROBE_STAGES) | {INTERPRETER_PROBE_STAGE}
            )
        },
        "stage_candidates": stage_candidates,
        "clean_sample_floor": CLEAN_SAMPLE_FLOOR,
        "floor_missed": floor_missed,
        "idle": {
            str(repeat): {
                class_name: {
                    "count": (aggregate_clean(
                        (sets["idle"][repeat].get(class_name) or {}).get("samples")
                        or []
                    )["by_class"][class_name]["count"]),
                    "p50": (aggregate_clean(
                        (sets["idle"][repeat].get(class_name) or {}).get("samples")
                        or []
                    )["by_class"][class_name]["p50"]),
                    "p95": (aggregate_clean(
                        (sets["idle"][repeat].get(class_name) or {}).get("samples")
                        or []
                    )["by_class"][class_name]["p95"]),
                }
                for class_name in sorted(sets["idle"][repeat].keys())
            }
            for repeat in sorted(sets.get("idle", {}).keys())
        },
    }
    analysis_path = out_dir / "analysis.json"
    analysis_path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


# --------------------------------------------------------------------------- #
# Host helpers.
# --------------------------------------------------------------------------- #
def host_summary() -> dict:
    summary = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "logical_cpu": os.cpu_count(),
    }
    try:
        summary["loadavg"] = round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        pass
    return summary


def host_worker_ceiling() -> tuple:
    """(ceiling, derivation): physical cores minus one, floor 1."""
    physical = None
    source = None
    try:
        out = subprocess.run(
            ["sysctl", "-n", "hw.physicalcpu"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip().isdigit():
            physical = int(out.stdout.strip())
            source = "sysctl hw.physicalcpu"
    except (OSError, subprocess.SubprocessError):
        pass
    if physical is None:
        physical = os.cpu_count() or 1
        source = "os.cpu_count() (physical count unavailable)"
    ceiling = max(1, physical - 1)
    derivation = f"physical cores {physical} ({source}) minus one -> ceiling {ceiling}"
    return ceiling, derivation


def _kill_process_group(proc: subprocess.Popen) -> None:
    """Kill the consult's own process group (it runs in its own session)."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _read_keying_lines_since(hooks_log: Path, offset: int) -> list:
    """Keying values appended to the worker's own sandbox hooks log in the
    window (a line belongs to the consult whose start and end bracket its
    append; consults within one worker run sequentially)."""
    values = []
    if not hooks_log.is_file():
        return values
    try:
        with open(hooks_log, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(offset)
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except ValueError:
                    continue
                value = payload.get("keying")
                if isinstance(value, str) and value:
                    values.append(value)
    except OSError:
        return values
    return values


def _extract_python_c_bodies(text: str) -> list:
    """Extract the single-quoted ``python3 -c '<body>'`` bodies in source
    order (shell quoting: ``'\\''`` is a literal quote)."""
    bodies = []
    idx = 0
    marker = "python3 -c '"
    while True:
        start = text.find(marker, idx)
        if start < 0:
            break
        i = start + len(marker)
        chunks = []
        while i < len(text):
            ch = text[i]
            if ch == "'":
                if text[i:i + 4] == "'\\''":
                    chunks.append("'")
                    i += 4
                    continue
                i += 1
                break
            chunks.append(ch)
            i += 1
        bodies.append("".join(chunks))
        idx = i
    return bodies


# --------------------------------------------------------------------------- #
# The profiler.
# --------------------------------------------------------------------------- #
class ConsultProfiler:
    """Drive and time gated consults through the REAL adapter chain.

    One instance per measurement invocation. Sandbox recipe mirrors the core
    selftest: an isolated temporary HOME per worker (``.ai-playbook/scripts``
    symlinks resolving into the worktree's own scripts) and a temp git
    fixture repo holding the gated target.
    """

    def __init__(self, *, worktree_root: Path | None = None,
                 adapter_path: Path | None = None, output_dir: Path | None = None,
                 workers: int | None = None, iterations: int | None = None,
                 kind: str = "loaded", repeat: int = 0, rerun: int = 0,
                 classes=("allow", "block"), emission: bool = True,
                 verbose: bool = False, keep_sandboxes: bool = False):
        self.worktree_root = Path(worktree_root) if worktree_root else REPO_ROOT
        self.adapter_path = Path(adapter_path) if adapter_path else (
            self.worktree_root / "agents" / "hooks" / "skill-gate" / "claude.sh"
        )
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.workers = workers
        self.iterations = iterations if iterations is not None else 10
        self.kind = kind
        self.repeat = repeat
        self.rerun = rerun
        self.classes = tuple(classes)
        self.emission = emission
        self.verbose = verbose
        self.keep_sandboxes = keep_sandboxes
        self.samples: list = []
        self._replica: dict | None = None
        self._sandbox_roots: list = []

    def _log(self, message: str) -> None:
        if self.verbose:
            sys.stderr.write(f"[profile-skill-gate] {message}\n")

    # --------------------------- self checks --------------------------- #
    def derive_adapter_stage_replica(self, adapter_path: Path | None = None) -> dict:
        """Re-derive the adapter's subprocess argvs from its SOURCE and pin
        them against the harness's replica. Loud failure on any mismatch."""
        path = Path(adapter_path) if adapter_path else self.adapter_path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            raise SelfCheckError(
                f"self-check failed: adapter unreadable at {path}: {e}"
            ) from e
        failures = []
        for name, snippet in ADAPTER_PINNED_SNIPPETS:
            count = text.count(snippet)
            if count != 1:
                failures.append(
                    f"pinned replica {name!r} matched {count} times (expected 1)"
                )
        code_lines = [
            ln for ln in text.splitlines()
            if "python3" in ln and not ln.lstrip().startswith("#")
        ]
        if len(code_lines) != EXPECTED_PYTHON3_INVOCATIONS:
            failures.append(
                f"adapter carries {len(code_lines)} code python3 invocations "
                f"(pinned replica expects {EXPECTED_PYTHON3_INVOCATIONS})"
            )
        bodies = _extract_python_c_bodies(text)
        if len(bodies) != EXPECTED_C_BODIES:
            failures.append(
                f"adapter carries {len(bodies)} python3 -c bodies "
                f"(pinned replica expects {EXPECTED_C_BODIES})"
            )
        if failures:
            raise SelfCheckError(
                "self-check failed: adapter stage argv no longer matches the "
                "pinned replica: " + "; ".join(failures)
            )
        self._replica = {
            "adapter": str(path),
            "snippets": {name: snippet for name, snippet in ADAPTER_PINNED_SNIPPETS},
            "bodies": bodies,
        }
        return self._replica

    def run_self_checks(self, sandbox: dict) -> None:
        """Sandbox startup self-check: core path is a symlink INTO the
        worktree; the fixture repo holds the gated target and passes
        ``git rev-parse``."""
        core = sandbox["scripts_core"]
        if not core.is_symlink():
            raise SelfCheckError(
                f"self-check failed: sandbox core {core} is not a symlink"
            )
        resolved = Path(os.path.realpath(str(core)))
        worktree_scripts = Path(
            os.path.realpath(str(self.worktree_root / "scripts"))
        )
        if worktree_scripts not in resolved.parents:
            raise SelfCheckError(
                f"self-check failed: sandbox core {core} resolves to {resolved}, "
                f"outside the worktree scripts dir {worktree_scripts}"
            )
        target = sandbox["target"]
        if not target.is_file():
            raise SelfCheckError(
                f"self-check failed: fixture repo lacks the gated target {target}"
            )
        try:
            proc = subprocess.run(
                ["git", "-C", str(sandbox["fixture"]), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True,
                timeout=RESOLVER_BOUND_S,
            )
            rc = proc.returncode
        except (OSError, subprocess.SubprocessError) as e:
            raise SelfCheckError(
                f"self-check failed: fixture repo git rev-parse error: {e}"
            ) from e
        if rc != 0:
            raise SelfCheckError(
                "self-check failed: fixture repo git rev-parse exited "
                f"{rc}: {proc.stderr.strip()[:200]}"
            )

    # --------------------------- sandbox --------------------------- #
    def build_sandbox(self, class_name: str, worker_id: int = 0) -> dict:
        """Isolated temp HOME + git fixture repo (the core selftest recipe).

        The sandbox lives under the declared output root so no consult write
        escapes the declared roots. Marker keying: session vars are cleared,
        so the seeded marker uses the ``no-session`` component.
        """
        root = Path(tempfile.mkdtemp(
            prefix=f"sgprof-{self.kind}-r{self.repeat}-w{worker_id}-{class_name}-",
            dir=str(self._sandbox_root()),
        ))
        self._sandbox_roots.append(root)
        home = root / "home"
        scripts = home / ".ai-playbook" / "scripts"
        scripts.mkdir(parents=True, mode=0o700)
        for basename in ("skill_gate.py", "session_channel.py"):
            os.symlink(
                str(self.worktree_root / "scripts" / basename),
                str(scripts / basename),
            )
        fixture = root / "fixture"
        (fixture / "docs" / "history" / "plans").mkdir(parents=True)
        target = fixture / "docs" / "history" / "plans" / "target.md"
        target.write_text("gated fixture target\n", encoding="utf-8")
        env = dict(os.environ)
        env["GIT_AUTHOR_NAME"] = "sgprof"
        env["GIT_AUTHOR_EMAIL"] = "sgprof@example.com"
        env["GIT_COMMITTER_NAME"] = "sgprof"
        env["GIT_COMMITTER_EMAIL"] = "sgprof@example.com"
        subprocess.run(["git", "init", "-q", str(fixture)],
                       check=True, capture_output=True, env=env)
        subprocess.run(["git", "-C", str(fixture), "add", "-A"],
                       check=True, capture_output=True, env=env)
        subprocess.run(["git", "-C", str(fixture), "commit", "-q", "-m", "init"],
                       check=True, capture_output=True, env=env)
        return {
            "root": root,
            "home": home,
            "fixture": fixture,
            "target": target,
            "timing_dir": self._ensure_timing_dir(root),
            "hooks_log": home / ".ai-playbook" / "logs" / "hooks.log",
            "runtime_dir": home / ".ai-playbook" / "runtime" / "skill-invoked",
            "scripts_core": scripts / "skill_gate.py",
            "scripts_session_channel": scripts / "session_channel.py",
            "class": class_name,
            "worker": worker_id,
        }

    @staticmethod
    def _ensure_timing_dir(root: Path) -> Path:
        timing_dir = root / "timing"
        timing_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        return timing_dir

    def _sandbox_root(self) -> Path:
        root = self.output_dir / "sandboxes"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _cleanup_sandboxes(self) -> int:
        """Remove THIS run's sandbox trees (isolated HOMEs + fixture repos +
        timing dirs) under ``<out>/sandboxes/``; the retained sample files
        stay. An ABORTED run (a loud self-check raise mid-run) keeps its
        sandboxes for post-mortem inspection; a completed run leaves no
        sandbox bytes behind unless ``keep_sandboxes`` is set."""
        removed = 0
        for root in self._sandbox_roots:
            shutil.rmtree(root, ignore_errors=True)
            removed += 1
        self._sandbox_roots = []
        sandbox_root = self.output_dir / "sandboxes"
        try:
            next(sandbox_root.iterdir())
        except StopIteration:
            shutil.rmtree(sandbox_root, ignore_errors=True)
        except OSError:
            pass
        return removed

    def seed_allow_marker(self, sandbox: dict) -> Path:
        """Allow-class seeding through the SANDBOX core's ``--write-marker``
        (the core's actual CLI), keyed to the fixture repo with the session
        vars cleared (``no-session``)."""
        env = self.worker_env(sandbox, emission=False)
        proc = subprocess.run(
            [
                "python3", str(sandbox["scripts_core"]),
                "--write-marker",
                "--cwd", str(sandbox["fixture"]),
            ],
            capture_output=True, text=True, env=env,
            cwd=str(sandbox["fixture"]), timeout=30,
        )
        if proc.returncode != 0:
            raise SelfCheckError(
                "self-check failed: --write-marker seeding exited "
                f"{proc.returncode}: {proc.stderr.strip()[:200]}"
            )
        runtime = sandbox["runtime_dir"]
        markers = sorted(runtime.glob("plans.*.no-session.marker")) \
            if runtime.is_dir() else []
        if not markers:
            raise SelfCheckError(
                "self-check failed: --write-marker wrote no plans.*.no-session"
                f".marker under {runtime}"
            )
        return markers[0]

    def worker_env(self, sandbox: dict, *, emission: bool = True,
                   timing_path=None, nonce: str | None = None) -> dict:
        """The consult subprocess env: HOME pinned to the sandbox, session
        and GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR cleared,
        PYTHONDONTWRITEBYTECODE=1, timing vars present only when emission."""
        env = dict(os.environ)
        for var in SESSION_ENV_VARS + GIT_ISOLATION_VARS + (
            TIMING_PATH_ENV, TIMING_NONCE_ENV,
        ):
            env.pop(var, None)
        env["HOME"] = str(sandbox["home"])
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if emission:
            env[TIMING_PATH_ENV] = str(timing_path)
            env[TIMING_NONCE_ENV] = str(nonce or "")
        return env

    # --------------------------- stage probes --------------------------- #
    def run_stage_probes(self, sandbox: dict) -> dict:
        """Verbatim argv replication: re-run each adapter subprocess argv as
        a separate timed probe (argvs re-derived from the adapter source)."""
        replica = self._replica or self.derive_adapter_stage_replica()
        fixture = sandbox["fixture"]
        target = sandbox["target"]
        payload = json.dumps({
            "tool_input": {"file_path": str(target)},
            "cwd": str(fixture),
        })
        block_decision = json.dumps({
            "allow_tool": False,
            "deny_reason": BLOCK_MESSAGE,
        })
        env = self.worker_env(sandbox, emission=False)
        probe_specs = [
            ("payload_extract",
             ["python3", "-c", replica["bodies"][0]], payload),
            ("session_channel",
             ["python3", str(sandbox["scripts_session_channel"])], None),
            ("core_invocation",
             ["python3", str(sandbox["scripts_core"]),
              "--target", str(target), "--cwd", str(fixture)], None),
            ("decision_parse",
             ["python3", "-c", replica["bodies"][1]], block_decision),
            ("git_resolver",
             ["git", "-C", str(fixture), "rev-parse", "--show-toplevel"], None),
        ]
        stages = {}
        resolver_probe_timed_out = False
        for name, argv, stdin_text in probe_specs:
            t0 = time.perf_counter()
            timed_out = False
            try:
                subprocess.run(
                    argv,
                    input=stdin_text if stdin_text is not None else "",
                    capture_output=True, text=True, env=env,
                    cwd=str(fixture),
                    timeout=RESOLVER_BOUND_S if name == "git_resolver"
                    else PER_CONSULT_TIMEOUT_S,
                )
            except subprocess.TimeoutExpired:
                timed_out = True
            stages[name] = time.perf_counter() - t0
            if name == "git_resolver":
                resolver_probe_timed_out = timed_out
        return {
            "stages": stages,
            "resolver_probe_timed_out": resolver_probe_timed_out,
        }

    def _run_interpreter_probe(self, env: dict, sandbox: dict) -> float:
        """Timed bare ``python3 -c pass`` inside the worker sandbox."""
        t0 = time.perf_counter()
        subprocess.run(
            ["python3", "-c", "pass"],
            capture_output=True, env=env, cwd=str(sandbox["fixture"]),
            timeout=PER_CONSULT_TIMEOUT_S,
        )
        return time.perf_counter() - t0

    # --------------------------- one consult --------------------------- #
    def measure_consult(self, sandbox: dict, *, class_name: str,
                        worker_id: int, iteration: int, probes: dict | None,
                        emission: bool, kind: str | None = None,
                        repeat: int | None = None, rerun: int | None = None) -> dict:
        """Drive ONE gated consult through the real adapter chain and return
        the retained sample record."""
        kind = kind if kind is not None else self.kind
        repeat = self.repeat if repeat is None else repeat
        rerun = self.rerun if rerun is None else rerun
        probes = probes or {}
        fixture = sandbox["fixture"]
        target = sandbox["target"]
        payload = json.dumps({
            "tool_input": {"file_path": str(target)},
            "cwd": str(fixture),
        })
        nonce = (
            f"{kind}-r{repeat}-rr{rerun}-c{class_name}"
            f"-w{worker_id}-i{iteration}-{os.getpid()}"
        )
        timing_path = sandbox["timing_dir"] / f"it{iteration}.json"
        if timing_path.exists():
            timing_path.unlink()
        env = self.worker_env(
            sandbox, emission=emission, timing_path=timing_path, nonce=nonce
        )
        hooks_log = sandbox["hooks_log"]
        offset = hooks_log.stat().st_size if hooks_log.is_file() else 0

        ip_before = self._run_interpreter_probe(env, sandbox)
        t0 = time.perf_counter()
        timed_out = False
        exit_code = None
        stdout_text = ""
        stderr_text = ""
        proc = subprocess.Popen(
            ["bash", str(self.adapter_path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=env,
            cwd=str(fixture), start_new_session=True,
        )
        try:
            stdout_text, stderr_text = proc.communicate(
                input=payload, timeout=PER_CONSULT_TIMEOUT_S
            )
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_process_group(proc)
            try:
                stdout_text, stderr_text = proc.communicate(timeout=5)
            except (subprocess.TimeoutExpired, ValueError):
                pass
        e2e_s = time.perf_counter() - t0
        ip_after = self._run_interpreter_probe(env, sandbox)

        keying_values = _read_keying_lines_since(hooks_log, offset)

        timing_nonce_ok = None
        timing_record = None
        resolver_stage_s = None
        if emission:
            timing_nonce_ok = False
            if timing_path.is_file():
                try:
                    timing_record = json.loads(
                        timing_path.read_text(encoding="utf-8")
                    )
                except (OSError, ValueError):
                    timing_record = None
            if isinstance(timing_record, dict) \
                    and timing_record.get("nonce") == nonce:
                timing_nonce_ok = True
                stages = timing_record.get("stages") or {}
                value = stages.get("project_key_resolve")
                if isinstance(value, (int, float)):
                    resolver_stage_s = float(value)

        sample = {
            "kind": kind,
            "repeat": repeat,
            "rerun": rerun,
            "worker": worker_id,
            "iteration": iteration,
            "class": class_name,
            "e2e_s": e2e_s,
            "timed_out": timed_out,
            "exit_code": exit_code,
            "stdout": stdout_text or "",
            "stderr": stderr_text or "",
            "outcome": (
                "allow" if exit_code == 0
                else "block" if exit_code == 2
                else "unknown"
            ),
            "emission": bool(emission),
            "timing_nonce_ok": timing_nonce_ok,
            "timing_path": str(timing_path) if emission else None,
            "nonce": nonce,
            "keying_values": keying_values,
            "keying_branch": (
                "environment-derived"
                if keying_values and keying_values[0] == "env-var"
                else "empty" if keying_values and keying_values[0] == "project-only"
                else None
            ),
            "decision_readable": adapter_decision_readable(
                class_name, exit_code, stderr_text
            ),
            "resolver_stage_s": resolver_stage_s,
            "resolver_probe_timed_out": bool(
                probes.get("resolver_probe_timed_out")
            ),
            "stages": (timing_record or {}).get("stages") or {},
            "probe_stages": dict(probes.get("stages") or {}),
            "interpreter_probe_s": max(ip_before, ip_after),
            "project_key": hashlib.sha1(
                os.path.realpath(str(fixture)).encode()
            ).hexdigest()[:16],
            "target": str(target),
            "cwd": str(fixture),
        }
        status, label, detail = classify_sample(sample)
        sample["status"] = status
        sample["degraded_label"] = label
        sample["degraded_detail"] = detail
        if sample["probe_stages"].get(INTERPRETER_PROBE_STAGE) is None:
            sample["probe_stages"][INTERPRETER_PROBE_STAGE] = \
                sample["interpreter_probe_s"]
        return sample

    def pre_run_class_check(self, sandbox: dict) -> dict:
        """Pre-run consult: the sample must match its decision-path class
        (allow allows; block blocks with the exact deny text). Loud abort
        otherwise."""
        class_name = sandbox["class"]
        sample = self.measure_consult(
            sandbox, class_name=class_name, worker_id=sandbox["worker"],
            iteration=-1, probes={}, emission=self.emission,
        )
        if sample["outcome"] != class_name:
            raise SelfCheckError(
                "self-check failed: pre-run consult contradicted its class "
                f"({class_name}): exit={sample['exit_code']} "
                f"stderr={sample['stderr'][:200]!r}"
            )
        return sample

    # --------------------------- load mode --------------------------- #
    def resolve_workers(self) -> int:
        ceiling, derivation = host_worker_ceiling()
        workers = self.workers if self.workers is not None \
            else min(ceiling, 4)
        if workers > ceiling:
            raise SelfCheckError(
                f"self-check failed: requested workers {workers} above the "
                f"declared ceiling {ceiling} ({derivation})"
            )
        if workers < 1:
            raise SelfCheckError(
                f"self-check failed: worker count {workers} below 1"
            )
        return workers

    def _run_worker(self, class_name: str, worker_id: int, iterations: int,
                    rerun: int, results: list, errors: list) -> None:
        try:
            sandbox = self.build_sandbox(class_name, worker_id)
            self.run_self_checks(sandbox)
            if class_name == "allow":
                self.seed_allow_marker(sandbox)
            self.derive_adapter_stage_replica()
            probes = self.run_stage_probes(sandbox)
            self.pre_run_class_check(sandbox)
            samples = []
            failure_counts = Counter()
            for iteration in range(iterations):
                sample = self.measure_consult(
                    sandbox, class_name=class_name, worker_id=worker_id,
                    iteration=iteration, probes=probes, emission=self.emission,
                    rerun=rerun,
                )
                samples.append(sample)
                if sample["status"] != "clean":
                    failure_counts[sample["degraded_label"] or "unlabeled"] += 1
                self._log(
                    f"w{worker_id} c{class_name} i{iteration} "
                    f"{sample['status']} {sample['e2e_s']:.3f}s"
                )
            path = write_samples_file(
                self.output_dir, kind=self.kind, repeat=self.repeat,
                rerun=rerun, class_name=class_name, worker=worker_id,
                samples=samples, failure_counts=dict(failure_counts),
                probe_reference={
                    "stages": dict(probes.get("stages") or {}),
                    "resolver_probe_timed_out":
                        bool(probes.get("resolver_probe_timed_out")),
                },
            )
            results.append({"samples": samples, "path": str(path)})
        except Exception as e:  # noqa: BLE001 - re-raised in the join phase
            errors.append((class_name, worker_id, e))

    def _enforce_floor_after_reruns(self, status: dict, attempts: int) -> dict:
        """The clean-sample floor's loud arms after the re-run budget (Terms
        "clean-sample floor"). A repeat still under the floor with
        timed-out/resolver-timeout labels dominating the degraded share
        RECORDS the incident regime reached (loud stderr note; the summary
        and manifest carry the degraded-label breakdown) and no stage
        verdict may be drawn from that repeat. Otherwise it is a HARNESS
        INCIDENT: fail loud for the operator to fix and re-run."""
        if status.get("met"):
            return status
        detail = (
            "clean per class="
            f"{ {c: v['clean'] for c, v in status['per_class'].items()} } "
            f"degraded_labels={status['degraded_label_breakdown']}"
        )
        if status.get("incident_regime_reached"):
            sys.stderr.write(
                "[profile-skill-gate] INCIDENT REGIME REACHED: the "
                f"clean-sample floor is still unmet after {attempts} "
                f"re-run(s) ({detail}); this repeat records the incident "
                "regime reached and no stage verdict may be drawn from it\n"
            )
            recorded = dict(status)
            recorded["incident_regime_recorded"] = True
            recorded["reruns_used"] = attempts
            return recorded
        raise SelfCheckError(
            "harness incident: the clean-sample floor is still unmet after "
            f"{attempts} re-run(s) ({detail}); fix the harness and re-run"
        )

    def run(self) -> dict:
        """Matched-control load run: N workers x M matched consults per
        class, each worker under its own isolated HOME; the clean-sample
        floor is enforced with at most two re-runs; samples, failure counts,
        and the run context are retained under the output dir. On success the
        run's sandbox trees are removed (``keep_sandboxes`` retains them;
        the retained sample files always stay)."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ceiling, derivation = host_worker_ceiling()
        workers = self.resolve_workers()
        self.derive_adapter_stage_replica()
        ambient_before = None
        try:
            ambient_before = round(os.getloadavg()[0], 2)
        except (AttributeError, OSError):
            pass

        attempt = 0
        all_samples: list = []
        status = None
        while True:
            results: list = []
            errors: list = []
            threads = [
                threading.Thread(
                    target=self._run_worker,
                    args=(class_name, worker_id, self.iterations, attempt,
                          results, errors),
                    name=f"sgprof-{class_name}-w{worker_id}",
                )
                for class_name in self.classes
                for worker_id in range(workers)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if errors:
                class_name, worker_id, e = errors[0]
                raise SelfCheckError(
                    f"self-check failed: worker c{class_name} w{worker_id}: {e}"
                ) from e
            all_samples = [s for r in results for s in r["samples"]]
            status = floor_status(all_samples, self.classes)
            self._log(
                f"attempt {attempt}: floor met={status['met']} "
                f"per_class={status['per_class']}"
            )
            if status["met"] or attempt >= MAX_REPEAT_RERUNS:
                break
            attempt += 1
        # Loud floor arms after the re-run budget (Terms): record the
        # incident regime when timeout labels dominate, else harness incident.
        status = self._enforce_floor_after_reruns(status, attempt)

        try:
            ambient_after = round(os.getloadavg()[0], 2)
        except (AttributeError, OSError):
            ambient_after = None

        branches = sorted(
            {s["keying_branch"] for s in all_samples if s.get("keying_branch")}
        )
        aggregate = aggregate_clean(all_samples)
        invocation_id = f"{self.kind}-r{self.repeat}-rr{attempt}"
        sandbox_cleanup = {"kept": bool(self.keep_sandboxes), "removed": 0}
        if not self.keep_sandboxes:
            sandbox_cleanup["removed"] = self._cleanup_sandboxes()
        summary = {
            "kind": self.kind,
            "repeat": self.repeat,
            "rerun": attempt,
            "rerun_attempts_used": attempt,
            "max_reruns": MAX_REPEAT_RERUNS,
            "workers": workers,
            "worker_ceiling": ceiling,
            "ceiling_derivation": derivation,
            "iterations": self.iterations,
            "classes": list(self.classes),
            "emission": self.emission,
            "host": host_summary(),
            "ambient_load_before": ambient_before,
            "ambient_load_after": ambient_after,
            "keying_branches": branches,
            "floor_status": status,
            "aggregate": {
                "by_class": {
                    c: {
                        "count": v["count"],
                        "p50": v["p50"],
                        "p95": v["p95"],
                        "max": v["max"],
                    }
                    for c, v in aggregate["by_class"].items()
                },
                "degraded_counts": aggregate["degraded_counts"],
                "clean_total": aggregate["clean_total"],
                "total": aggregate["total"],
            },
            "total_samples": len(all_samples),
            "sandbox_cleanup": sandbox_cleanup,
        }
        update_manifest(self.output_dir, invocation_id, summary)
        self.samples = all_samples
        return summary


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="profile_skill_gate_consult.py",
        description=(
            "Consult-path profiling harness for the skill-gate (measurement "
            "tooling; changes no decision byte, refusal class, or pin)."
        ),
    )
    sub = p.add_subparsers(dest="mode", required=True)

    load = sub.add_parser("load", help="Run one matched-control repeat.")
    load.add_argument("--out", default=str(DEFAULT_OUTPUT_DIR),
                      help="Output dir for retained samples (defaults under docs/tmp).")
    load.add_argument("--workers", type=int, default=None,
                      help="Worker count (at or under the declared ceiling).")
    load.add_argument("--iterations", type=int, default=10,
                      help="Matched consults per worker per class.")
    load.add_argument("--kind", choices=("idle", "loaded", "emissionoff"),
                      default="loaded")
    load.add_argument("--repeat", type=int, default=0)
    load.add_argument("--classes", default="allow,block",
                      help="Comma-separated decision-path classes.")
    load.add_argument("--emission", choices=("on", "off"), default="on",
                      help="Core timing emission on/off (emission-off spot-check).")
    load.add_argument("--keep-sandboxes", action="store_true",
                      help="Keep the run's sandbox trees under <out>/sandboxes/ "
                           "after completion (default: removed; samples kept).")
    load.add_argument("-v", "--verbose", action="store_true")

    analyze = sub.add_parser("analyze", help="Write the analysis record.")
    analyze.add_argument("--out", default=str(DEFAULT_OUTPUT_DIR))

    return p


def main(argv: list | None = None) -> int:
    ns = _build_parser().parse_args(
        list(sys.argv[1:]) if argv is None else list(argv)
    )
    if ns.mode == "load":
        profiler = ConsultProfiler(
            output_dir=Path(ns.out),
            workers=ns.workers,
            iterations=ns.iterations,
            kind=ns.kind,
            repeat=ns.repeat,
            classes=tuple(c.strip() for c in ns.classes.split(",") if c.strip()),
            emission=(ns.emission == "on"),
            verbose=ns.verbose,
            keep_sandboxes=ns.keep_sandboxes,
        )
        summary = profiler.run()
        print(json.dumps({
            "invocation": f"{summary['kind']}-r{summary['repeat']}-rr{summary['rerun']}",
            "total_samples": summary["total_samples"],
            "floor_met": summary["floor_status"]["met"],
            "aggregate": summary["aggregate"],
            "out": str(profiler.output_dir),
        }, indent=1))
        return 0
    if ns.mode == "analyze":
        record = analyze_sets(Path(ns.out))
        print(json.dumps({
            "analysis": str(Path(ns.out) / "analysis.json"),
            "regime_reached": record["regime"]["reached"],
            "dominance": record["dominance"]["verdict"],
            "dominant_stage": record["dominance"].get("stage"),
            "worse_run": record["worse_run"],
        }, indent=1))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
