#!/usr/bin/env python3
"""Selftest for dispatch_admission.py: the target-disjointness dispatch
admission check (plan 2026-11-04-parallel-execution-landing-serialization-
blockers Task 1). Covers the four verdict classes through the CLI (exit
codes and the final `OUTCOME:` line per scripts/OUTCOME_CONTRACT.md) plus
the input-source arms (explicit owned paths, done-setup manifest, plan
Files: lists), the interleaved outstanding-run argv order the first-
blocker rule reads, usage-violation routing through the tool-error
outcome, and the check_admission core function directly. The dispatch-
admission outstanding-manifest recovery plan (docs/history/plans/
2026-11-06-dispatch-admission-outstanding-manifest-recovery, Task 2) adds
the lagging-record two-operand witness and the hermetic gateway-take
end-to-end retrieval pin."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "dispatch_admission.py"
GATEWAY = Path(__file__).resolve().parent / "execution_claim.sh"

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
    # consult-semantics witness (outstanding-manifest recovery plan Task 3):
    # the missing-source arm stays byte-identical when the evidence-strict
    # arms land, so the exact reason line is pinned
    assert ("reason: outstanding run run-m carries no done-setup manifest "
            "from which to derive owned paths; treated as intersecting "
            "(conservative verdict)") in out, out


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


# -- dispatch-admission outstanding-manifest recovery (docs/history/plans/
#    2026-11-06-dispatch-admission-outstanding-manifest-recovery, Task 2) -- #

GATEWAY_SLUG = "gateway-retrieval-fixture"


def _gateway_scratch_repo(scratch):
    """A scratch `git init` repository that is its own primary checkout,
    with the trusted lock-root seam pinned into the scratch tree (the
    test_execution_claim.py setUp pattern); the real checkout is never
    touched. Returns (repo, plan, env, claims_dir)."""
    repo = scratch / "primary"
    repo.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    home = scratch / "home"
    (home / "config").mkdir(parents=True)
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / "config")
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["LC_ALL"] = "C"
    env["TZ"] = "UTC"

    def git(*args):
        subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            timeout=60,
            env=env,
        )

    git("init", "-q")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    git("commit", "--allow-empty", "-q", "-m", "init")
    lock_home = scratch / "lock-home"
    lock_home.mkdir()
    env["EXECUTION_CLAIM_LOCK_HOME"] = str(lock_home)
    plan = scratch / "2026-11-06-gateway-retrieval-fixture.md"
    plan.write_text(
        "# Plan: gateway retrieval fixture\n"
        "\n"
        "Files:\n"
        "- `src/owned_one.py`\n"
        "- `src/owned_two.py`\n",
        encoding="utf-8",
    )
    claims_dir = repo / "docs" / "tmp" / "execution-claims"
    return repo, plan, env, claims_dir


def test_lagging_record_and_done_manifest_operands_decide_together(tmp_path):
    """[class: REPOSITORY_TEST] Safety witness (lagging record): a seed-only
    admission record and a done-session manifest holding extra paths, passed
    as two `--outstanding-with-manifest` operands under the same label, refuse
    a candidate intersecting only the manifest's extra paths, naming them."""
    record = write_manifest(
        tmp_path / "admission-slug-admission.json",
        "admission-slug",
        ["src/seeded.md"],
    )
    done_manifest = write_manifest(
        tmp_path / "run-manifest-live-run.json",
        "live-run",
        ["src/seeded.md", "src/merged-later.md"],
    )
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/merged-later.md",
        "--outstanding-with-manifest", "admission-slug", str(record),
        "--outstanding-with-manifest", "admission-slug", str(done_manifest),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    assert "src/merged-later.md" in proc.stdout, proc.stdout


def test_gateway_take_record_end_to_end_retrieval(tmp_path):
    """[class: REPOSITORY_TEST] End-to-end retrieval: a hermetic gateway take
    over a fixture plan with a `Files:` list seeds the record beside the
    claim; a consult passing the record via `--outstanding-with-manifest`
    admits a disjoint candidate and refuses an intersecting one naming the
    paths."""
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    repo, plan, env, claims_dir = _gateway_scratch_repo(scratch)
    take = subprocess.run(
        [
            "bash", str(GATEWAY), "take", str(plan),
            "--session", "sess-live",
            "--branch", "live/branch",
            "--worktree-parent", str(scratch / "wt"),
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert take.returncode == 0, take.stdout + take.stderr
    record = claims_dir / f"{GATEWAY_SLUG}-admission.json"
    assert record.is_file(), f"the take wrote no admission record: {take.stderr}"
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["owned_paths"] == ["src/owned_one.py", "src/owned_two.py"]

    disjoint = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/disjoint.md",
        "--outstanding-with-manifest", GATEWAY_SLUG, str(record),
    ])
    assert disjoint.returncode == 0, disjoint.stdout + disjoint.stderr
    assert final_outcome(disjoint) == "OUTCOME: pass"

    intersecting = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/owned_one.py",
        "--outstanding-with-manifest", GATEWAY_SLUG, str(record),
    ])
    assert intersecting.returncode == 1, intersecting.stdout + intersecting.stderr
    assert final_outcome(intersecting) == "OUTCOME: fail"
    assert "src/owned_one.py" in intersecting.stdout, intersecting.stdout


# -- dispatch-admission outstanding-manifest recovery (docs/history/plans/
#    2026-11-06-dispatch-admission-outstanding-manifest-recovery, Task 3):
#    evidence-strict admission reads. Fixed precedence (plan Assumption):
#    an unreadable, unparseable, or non-object input on either operand is
#    the exit-3 tool error first; then the candidate's malformed evidence
#    refuses, then an empty candidate set refuses, both exit 1 before the
#    outstanding-run loop; then each outstanding run's malformed evidence
#    is that run's conservative verdict at its loop position under the
#    first-blocker order. -- #


def run_manifest_payload(run_id, owned_paths, **overrides):
    """A done-setup manifest payload shaped like the done skill's
    RunManifest record, with per-field overrides for malformed-evidence
    fixtures."""
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
        "owned_plan_paths": [],
        "owned_review_paths": [],
        "foreign_review_paths": [],
        "adopted_from": None,
        "complete": False,
    }
    payload.update(overrides)
    return payload


def write_payload(path, payload):
    path.write_text(json.dumps(payload))
    return path


def test_empty_candidate_set_refuses_with_zero_outstanding_runs(tmp_path):
    """[class: IMPLEMENTATION_REQUIRED] Empty-set refusal: a candidate
    manifest whose owned-path fields all derive empty lists refuses with
    the candidate's empty-set reason even with no outstanding runs (today
    it passes vacuously)."""
    candidate = write_manifest(
        tmp_path / "run-manifest-run-a.json", "run-a", [])
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert ("reason: candidate owned-path set is empty; refusing") in out, out


def test_empty_candidate_set_refuses_before_missing_source_reason(tmp_path):
    """[class: IMPLEMENTATION_REQUIRED] Empty-set refusal: with one
    --outstanding-without-manifest run present, the candidate's empty-set
    refusal decides before the outstanding-run loop, so the missing-source
    reason is absent."""
    candidate = write_manifest(
        tmp_path / "run-manifest-run-a.json", "run-a", [])
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
        "--outstanding-without-manifest", "run-m",
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert ("reason: candidate owned-path set is empty; refusing") in out, out
    assert "carries no done-setup manifest" not in out, out
    assert "blocking outstanding run: run-m" not in out, out


def test_candidate_non_string_list_item_refuses_naming_dropped_evidence(
        tmp_path):
    """[class: IMPLEMENTATION_REQUIRED] Partial-parse refusal, candidate
    side: a non-string item beside a valid entry refuses naming the
    dropped evidence instead of passing on the silent subset."""
    candidate = write_payload(tmp_path / "run-manifest-run-a.json",
                              run_manifest_payload("run-a",
                                                   ["src/a.md", 42]))
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert "owned_paths[1] is not a string (int)" in out, out
    assert "malformed" in out, out


def test_candidate_non_list_owned_path_field_refuses_naming_dropped_evidence(
        tmp_path):
    """[class: IMPLEMENTATION_REQUIRED] Partial-parse refusal, candidate
    side: a non-list owned-path field beside valid entries refuses naming
    the dropped field instead of passing on the silent subset."""
    candidate = write_payload(
        tmp_path / "run-manifest-run-a.json",
        run_manifest_payload("run-a", ["src/a.md"],
                             owned_review_paths="src/leaked.md"))
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert "owned_review_paths is not a list (str)" in out, out
    assert "malformed" in out, out


def test_outstanding_non_string_list_item_takes_conservative_verdict(
        tmp_path):
    """[class: IMPLEMENTATION_REQUIRED] Partial-parse refusal, outstanding
    side: a non-string item beside valid entries takes that run's
    conservative verdict naming the dropped evidence, never a verdict on
    the dropped subset and never the tool error."""
    outstanding = write_payload(
        tmp_path / "run-manifest-run-b.json",
        run_manifest_payload("run-b", ["src/valid.md", 7]))
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "run-b", str(outstanding),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert ("reason: outstanding run run-b carries malformed owned-path "
            "evidence (owned_paths[1] is not a string (int)); treated as "
            "intersecting (conservative verdict)") in out, out


def test_outstanding_non_list_field_in_admission_record_takes_conservative_verdict(
        tmp_path):
    """[class: IMPLEMENTATION_REQUIRED] Partial-parse refusal, outstanding
    side: the admission record reads through the same
    --outstanding-with-manifest input path, so a non-list owned-path field
    in a record takes the same conservative verdict naming the dropped
    field."""
    record = write_payload(
        tmp_path / "admission-slug-admission.json",
        {
            "owned_paths": ["src/valid.md"],
            "owned_plan_paths": 42,
            "owned_review_paths": [],
        })
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "admission-slug", str(record),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert ("reason: outstanding run admission-slug carries malformed "
            "owned-path evidence (owned_plan_paths is not a list (int)); "
            "treated as intersecting (conservative verdict)") in out, out


def test_malformed_outstanding_run_ahead_of_intersecting_one_decides(
        tmp_path):
    """[class: IMPLEMENTATION_REQUIRED] Partial-parse refusal, outstanding
    side: under the first-blocker order a malformed run ahead of an
    intersecting one decides with its conservative verdict and no
    intersecting-paths line."""
    malformed = write_payload(
        tmp_path / "run-manifest-run-bad.json",
        run_manifest_payload("run-bad", ["src/disjoint.md", None]))
    intersecting = write_manifest(
        tmp_path / "run-manifest-run-i.json", "run-i", ["src/a.md"])
    proc = run([
        "--candidate-run", "plan-a",
        "--owned-path", "src/a.md",
        "--outstanding-with-manifest", "run-bad", str(malformed),
        "--outstanding-with-manifest", "run-i", str(intersecting),
    ])
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: fail"
    out = proc.stdout
    assert "blocking outstanding run: run-bad" in out, out
    assert "owned_paths[1] is not a string (NoneType)" in out, out
    assert "blocking outstanding run: run-i" not in out, out
    assert "intersecting paths" not in out, out


def test_non_object_candidate_manifest_is_tool_error(tmp_path):
    """[class: REPOSITORY_TEST] Tool-error boundary unchanged: a non-object
    candidate manifest stays the exit-3 tool error (the arm is checked
    before the malformed-evidence and empty-set arms)."""
    candidate = tmp_path / "candidate.json"
    candidate.write_text("[1, 2]")
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
    ])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"


def test_malformed_candidate_beside_unreadable_outstanding_is_tool_error(
        tmp_path):
    """[class: REPOSITORY_TEST] Tool-error boundary unchanged: a malformed
    candidate beside an unreadable outstanding input decides as the tool
    error, not as the candidate's malformed-evidence refusal."""
    candidate = write_payload(tmp_path / "run-manifest-run-a.json",
                              run_manifest_payload("run-a",
                                                   ["src/a.md", 42]))
    missing = tmp_path / "no-such-manifest.json"
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
        "--outstanding-with-manifest", "run-b", str(missing),
    ])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"


def test_empty_candidate_beside_unreadable_outstanding_is_tool_error(
        tmp_path):
    """[class: REPOSITORY_TEST] Tool-error boundary unchanged: an empty
    candidate beside an unreadable outstanding input decides as the tool
    error, not as the empty-set refusal."""
    candidate = write_manifest(
        tmp_path / "run-manifest-run-a.json", "run-a", [])
    missing = tmp_path / "no-such-manifest.json"
    proc = run([
        "--candidate-run", "run-a", "--candidate-manifest", str(candidate),
        "--outstanding-with-manifest", "run-b", str(missing),
    ])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"


def test_plan_with_no_owned_paths_stays_fail_closed_tool_error(tmp_path):
    """[class: REPOSITORY_TEST] Safety witness (plan-arm fail-closed
    preserved): a --plan derivation that finds no owned paths keeps the
    existing fail-closed tool error."""
    plan = tmp_path / "plan-a.md"
    plan.write_text(
        "# Plan: sample\n\n## Why\n\nSome prose.\n\n### Task 1\n\n"
        "Primary class anchors:\n"
        "- `check_admission` in `scripts/dispatch_admission.py`\n")
    proc = run([
        "--candidate-run", "plan-a", "--plan", str(plan),
    ])
    assert proc.returncode == 3, (proc.stdout, proc.stderr)
    assert final_outcome(proc) == "OUTCOME: tool_error"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
