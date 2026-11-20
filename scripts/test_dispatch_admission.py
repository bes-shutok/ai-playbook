#!/usr/bin/env python3
"""Selftest for dispatch_admission.py: the target-disjointness dispatch
admission check (plan 2026-11-04-parallel-execution-landing-serialization-
blockers Task 1). Covers the four verdict classes through the CLI (exit
codes and the final `OUTCOME:` line per scripts/OUTCOME_CONTRACT.md) plus
the input-source arms (explicit owned paths, done-setup manifest, plan
Files: lists), the interleaved outstanding-run argv order the first-
blocker rule reads, usage-violation routing through the tool-error
outcome, and the check_admission core function directly."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "dispatch_admission.py"

sys.path.insert(0, str(SCRIPT.parent))


def run(args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, check=False, env=env,
    )


def write_manifest(path, run_id, owned_paths, owned_plan_paths=None,
                   owned_review_paths=None):
    """A done-setup manifest fixture shaped like the done skill's
    run-manifest record (scripts/done_sweep_gates_lib.py RunManifest)."""
    payload = {
        "schema": 1,
        "run_id": run_id,
        "marker": "marker-" + run_id,
        "created_epoch": 1730700000.0,
        "repo_root": "repo-root-digest",
        "pid": 4242,
        "start_commit": "0" * 40,
        "start_porcelain": [],
        "owned_paths": list(owned_paths),
        "owned_plan_paths": list(owned_plan_paths or []),
        "owned_review_paths": list(owned_review_paths or []),
        "foreign_review_paths": [],
        "adopted_from": None,
        "complete": False,
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def final_outcome(proc):
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("OUTCOME:")]
    return lines[-1] if lines else "<no OUTCOME line>"


def test_intersecting_outstanding_run_refuses_naming_both_runs_and_paths(tmp_path):
    manifest = write_manifest(
        tmp_path / "run-manifest-run-b.json", "run-b", ["src/b.md", "src/c.md"])
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md", "--owned-path", "src/b.md",
        "--outstanding-with-manifest", "run-b", str(manifest),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert "plan-a" in out, out
    assert "run-b" in out, out
    assert "src/b.md" in out, out
    assert "src/c.md" not in out, out  # only intersecting paths are named


def test_disjoint_candidate_passes_with_outcome_pass(tmp_path):
    manifest = write_manifest(
        tmp_path / "run-manifest-run-b.json", "run-b", ["src/other.md"])
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "run-b", str(manifest),
    ])
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: pass"
    assert "run-b" in proc.stdout


def test_empty_recorded_owned_set_takes_conservative_verdict(tmp_path):
    manifest = write_manifest(tmp_path / "run-manifest-run-e.json", "run-e", [])
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "run-e", str(manifest),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert "run-e" in out
    assert "empty" in out, out
    assert "intersect" in out, out


def test_missing_manifest_takes_conservative_verdict(tmp_path):
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-without-manifest", "run-m",
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert "run-m" in out
    assert "manifest" in out.lower(), out
    assert "intersect" in out, out


def test_first_blocker_decides_among_several_outstanding_runs(tmp_path):
    disjoint = write_manifest(
        tmp_path / "run-manifest-run-d.json", "run-d", ["src/disjoint.md"])
    intersecting = write_manifest(
        tmp_path / "run-manifest-run-i.json", "run-i", ["src/a.md"])
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "run-d", str(disjoint),
        "--outstanding-without-manifest", "run-m",
        "--outstanding-with-manifest", "run-i", str(intersecting),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    out = proc.stdout
    # the interleaved argv order puts run-m before run-i; per-option
    # collection would let the intersecting run decide instead, so the
    # blocking line must name run-m with the missing-manifest reason and
    # no path-intersection evidence may decide
    assert "blocking outstanding run: run-m" in out, out
    assert ("reason: outstanding run run-m carries no done-setup "
            "manifest") in out, out
    assert "blocking outstanding run: run-i" not in out, out
    assert "intersecting paths" not in out, out


def test_candidate_owned_paths_from_manifest(tmp_path):
    candidate = write_manifest(
        tmp_path / "run-manifest-run-a.json", "run-a", ["src/a.md"],
        owned_plan_paths=["docs/history/plans/plan-a.md"])
    outstanding = write_manifest(
        tmp_path / "run-manifest-run-b.json", "run-b",
        ["docs/history/plans/plan-a.md"])
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
        "--outstanding-with-manifest", "run-b", str(outstanding),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert "docs/history/plans/plan-a.md" in proc.stdout


def test_candidate_owned_paths_from_plan_files_lists(tmp_path):
    plan = tmp_path / "plan-a.md"
    plan.write_text(
        "# Plan: sample\n\n## Why\n\nSome prose.\n\n### Task 1\n\n"
        "Files:\n"
        "- `src/a.md`\n"
        "- `agents/skills/maintenance/SKILL.md` *(new-ish span text)*\n"
        "\n"
        "Primary class anchors:\n"
        "- `check_admission` in `scripts/dispatch_admission.py`\n")
    outstanding = write_manifest(
        tmp_path / "run-manifest-run-b.json", "run-b", ["src/a.md"])
    proc = run([
        "--candidate-run", "plan-a", "--plan", str(plan),
        "--outstanding-with-manifest", "run-b", str(outstanding),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert "src/a.md" in proc.stdout
    # the plan-derived set excludes non-path backticked spans and spans
    # outside Files: blocks
    assert "check_admission" not in proc.stdout


def test_plan_derived_disjoint_candidate_passes(tmp_path):
    plan = tmp_path / "plan-a.md"
    plan.write_text(
        "# Plan: sample\n\nFiles:\n- `src/a.md`\n\nNotes: end of files list\n")
    outstanding = write_manifest(
        tmp_path / "run-manifest-run-b.json", "run-b", ["src/b.md"])
    proc = run([
        "--candidate-run", "plan-a", "--plan", str(plan),
        "--outstanding-with-manifest", "run-b", str(outstanding),
    ])
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: pass"


def test_unreadable_outstanding_manifest_is_tool_error(tmp_path):
    missing = tmp_path / "no-such-manifest.json"
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "run-b", str(missing),
    ])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"


def test_unparseable_outstanding_manifest_is_tool_error(tmp_path):
    bad = tmp_path / "run-manifest-run-b.json"
    bad.write_text("not json at all{")
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "run-b", str(bad),
    ])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"


def test_no_candidate_source_is_tool_error():
    proc = run(["--candidate-run", "plan-a"])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"


def test_missing_required_option_is_usage_tool_error():
    # missing --candidate-run is an argparse usage violation; the
    # parser's error override routes it to exit 3 with the OUTCOME line
    # instead of argparse's bare exit 2
    proc = run([])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"
    assert "--candidate-run" in proc.stdout, proc.stdout
    assert "usage" in proc.stdout, proc.stdout


def test_check_admission_function_verdicts():
    import dispatch_admission as da

    admitted = da.check_admission(
        da.Candidate("plan-a", ["src/a.md"]),
        [da.OutstandingRun("run-b", ["src/b.md"])],
    )
    assert admitted.admitted is True

    colliding = da.check_admission(
        da.Candidate("plan-a", ["src/a.md", "src/b.md"]),
        [da.OutstandingRun("run-b", ["src/b.md", "src/c.md"])],
    )
    assert colliding.admitted is False
    assert colliding.blocking_run_id == "run-b"
    assert colliding.intersecting_paths == ["src/b.md"]

    empty = da.check_admission(
        da.Candidate("plan-a", ["src/a.md"]),
        [da.OutstandingRun("run-e", [])],
    )
    assert empty.admitted is False
    assert "empty" in empty.reason

    missing = da.check_admission(
        da.Candidate("plan-a", ["src/a.md"]),
        [da.OutstandingRun("run-m", None)],
    )
    assert missing.admitted is False
    assert "manifest" in missing.reason.lower()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
