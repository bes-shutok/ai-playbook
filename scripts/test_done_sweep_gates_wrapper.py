#!/usr/bin/env python3
"""Wrapper-dispatch suite for done_sweep_gates.sh (plan Task 1, finding F2).

Plan: docs/history/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md.
Every test exercises the real wrapper script (bash) against a hermetic fixture
repo under pytest ``tmp_path``: the wrapper resolves its lib next to itself,
so these tests run the repo's own scripts/done_sweep_gates.sh.

Hermeticity: DONE_SWEEP_REPO_ROOT points at the fixture repo; the runtime
home and user facts are redirected like the lib suite's ``sweep_env``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
WRAPPER = SCRIPTS_DIR / "done_sweep_gates.sh"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import done_sweep_gates_lib as lib


def sh(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True, check=False, timeout=120
    )


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return sh(["git", *args], root)


@pytest.fixture
def wrapper_repo(tmp_path, monkeypatch):
    """Fixture git repo with its own facts file and a run-start marker; env
    redirected so every runtime path lands inside the fixture."""
    root = tmp_path / "wrapper-repo"
    root.mkdir(parents=True)
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "fixture")
    (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (root / "README.md").write_text("fixture repo\n", encoding="utf-8")
    git(root, "add", ".gitignore", "README.md")
    git(root, "commit", "-m", "init", "-q")
    facts_dir = root / ".ai-playbook"
    facts_dir.mkdir()
    (facts_dir / "facts.md").write_text(
        "```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'plans_completed_dir = "docs/history/plans/completed/"\n'
        'backlog_dir = "docs/history/backlog/"\n'
        'reviews_dir = "docs/reviews/"\n'
        'tmp_dir = "docs/tmp/"\n'
        "```\n",
        encoding="utf-8",
    )
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True)
    stamp = datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    (done_session / f"run-start-{stamp}").write_text(
        f"{int(time.time())} {root} {os.getpid()}\n", encoding="utf-8"
    )
    runtime_home = tmp_path / "runtime-home"
    runtime_home.mkdir()
    monkeypatch.setenv("DONE_SWEEP_RUNTIME_HOME", str(runtime_home))
    monkeypatch.setenv("DONE_SWEEP_USER_FACTS", str(tmp_path / "user-facts.md"))
    (tmp_path / "user-facts.md").write_text("# fixture user facts\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    return root


def test_wrapper_accepts_write_manifest_and_forwards_full_argv(wrapper_repo):
    """[class: REPOSITORY_TEST] F2: invoking the wrapper with ``write-manifest``
    forwards the FULL argument vector to the lib - the flag-forwarding probe
    is ``write-manifest --help`` reaching the lib's own parser (exit 0, lib
    usage text) - and the wrapper usage lists the phase."""
    proc = sh([str(WRAPPER), "write-manifest", "--help"], wrapper_repo)
    assert proc.returncode == 0, proc.stderr
    assert "--owned-plan" in proc.stdout
    assert "--foreign-review" in proc.stdout

    usage = sh([str(WRAPPER)], wrapper_repo)
    assert "write-manifest" in usage.stdout + usage.stderr


def test_wrapper_bare_write_manifest_writes_manifest(wrapper_repo):
    """[class: REPOSITORY_TEST] F2: a bare ``write-manifest`` invocation through
    the wrapper produces a run manifest in the fixture repo's done-session
    directory (the exact flow the done Step 0 recipe's field witness broke)."""
    proc = sh([str(WRAPPER), "write-manifest"], wrapper_repo)
    assert proc.returncode == 0, proc.stderr
    manifests = list(
        (wrapper_repo / "docs" / "tmp" / "done-session").glob("run-manifest-*.json")
    )
    assert len(manifests) == 1
    assert manifests[0].name[len("run-manifest-") : -len(".json")] in proc.stdout


# --------------------------------------------------------------------------- #
# Outcome-contract arms (plan docs/history/plans/2026-10-03-outcome-contract-
# migration-batch-1.md, Task 3). The wrapper's phase runs report the
# four-outcome contract of scripts/OUTCOME_CONTRACT.md (exit 0 pass, 1 fail,
# 2 indeterminate, 3 tool error) with exactly one final stdout `OUTCOME:` line.
# Gates are in-process helpers returning gate results, so the aggregation arms
# stub lib.GATES through the in-process helper seam; the environment, usage,
# and child-vocabulary arms run the real bash wrapper end to end.
# --------------------------------------------------------------------------- #
def _outcome_rows(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.startswith("OUTCOME:")]


STUB_VALIDATOR_FAIL = (
    "#!/usr/bin/env python3\n"
    "import sys\n"
    "print('readiness FAILED: stub rejection')\n"
    "print('OUTCOME: fail')\n"
    "sys.exit(1)\n"
)
STUB_VALIDATOR_CRASH = (
    "#!/usr/bin/env python3\n"
    "import sys\n"
    "print('Traceback (most recent call last):')\n"
    "print('RuntimeError: stub validator exploded')\n"
    "sys.exit(2)\n"
)
STUB_VALIDATOR_INDETERMINATE = (
    "#!/usr/bin/env python3\n"
    "import sys\n"
    "print('readiness could not run (stub)')\n"
    "print('OUTCOME: indeterminate')\n"
    "sys.exit(2)\n"
)


def _write_deliverable_plan(wrapper_repo, plan_rel: str) -> None:
    plan = wrapper_repo / plan_rel
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("fixture plan body\n", encoding="utf-8")
    deliverables = (
        wrapper_repo / "docs" / "tmp" / "done-session" / "plan-deliverables.txt"
    )
    deliverables.write_text(plan_rel + "\n", encoding="utf-8")


def _write_readiness_validator(wrapper_repo, body: str) -> None:
    validator = wrapper_repo / "scripts" / "plan_readiness.py"
    validator.parent.mkdir(parents=True, exist_ok=True)
    validator.write_text(body, encoding="utf-8")


def _stub_gates(monkeypatch, gate_overrides: dict) -> None:
    """Replace every gate helper with a passing stub; the named gates run the
    given override callable instead (raise to model a crashed helper, return
    a GateResult to model any verdict). The in-process helper seam: gates are
    plain callables returning gate results, run sequentially by run_phase."""

    def make(gate_id: str):
        def _gate(ctx):
            override = gate_overrides.get(gate_id)
            if override is not None:
                return override(ctx)
            return lib.GateResult(gate_id, 0, "stub pass", warnings=[])

        return _gate

    monkeypatch.setattr(lib, "GATES", {gid: make(gid) for gid in lib.GATES})


def test_clean_run_emits_outcome_pass(wrapper_repo):
    """[class: REPOSITORY_TEST] A clean pre-docs run through the real wrapper
    exits 0 and ends stdout with exactly one final `OUTCOME: pass` line, the
    evidence lines (JSON report plus summary) preceding it."""
    proc = sh([str(WRAPPER), "pre-docs"], wrapper_repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _outcome_rows(proc.stdout) == ["OUTCOME: pass"]
    assert proc.stdout.rstrip().endswith("OUTCOME: pass")


def test_modeled_violation_emits_outcome_fail(wrapper_repo):
    """[class: REPOSITORY_TEST] A gate reporting a modeled violation (the
    plan-readiness stub validator reporting `OUTCOME: fail` for a
    deliverable plan) makes the run exit 1 and end stdout with exactly one
    final `OUTCOME: fail` line naming the offending plan."""
    _write_readiness_validator(wrapper_repo, STUB_VALIDATOR_FAIL)
    plan_rel = "docs/history/plans/2026-10-03-rejected-plan.md"
    _write_deliverable_plan(wrapper_repo, plan_rel)
    proc = sh([str(WRAPPER), "pre-docs"], wrapper_repo)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert _outcome_rows(proc.stdout) == ["OUTCOME: fail"]
    assert proc.stdout.rstrip().endswith("OUTCOME: fail")
    assert "rejected-plan" in proc.stdout


def test_raising_gate_helper_is_indeterminate(wrapper_repo, monkeypatch, capsys):
    """[class: REPOSITORY_TEST] A gate helper that raises is captured as an
    indeterminate gate result naming the failed gate; the run still reports
    every gate, exits 2 and ends stdout with exactly one final `OUTCOME:
    indeterminate` line. Today a raising helper aborts the whole run with a
    traceback and exit 1."""

    def raising(ctx):
        raise RuntimeError("stub gate exploded")

    _stub_gates(monkeypatch, {"doc-registry": raising})
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(wrapper_repo))
    code = lib.main(["pre-docs"])
    out = capsys.readouterr().out
    assert code == 2, out
    assert _outcome_rows(out) == ["OUTCOME: indeterminate"]
    assert out.rstrip().endswith("OUTCOME: indeterminate")
    assert "doc-registry" in out
    assert "RuntimeError" in out


def test_environment_failure_is_tool_error(wrapper_repo, tmp_path):
    """[class: REPOSITORY_TEST] An environment failure (the lib missing next
    to the copied runner) exits 3 and emits exactly one final stdout
    `OUTCOME: tool_error` line; a usage error exits 3 the same way (the
    argparse-override rule) while `--help` stays a metadata exit with no
    OUTCOME line."""
    lone = tmp_path / "lone-runner"
    lone.mkdir()
    (lone / "done_sweep_gates.sh").write_text(
        WRAPPER.read_text(encoding="utf-8"), encoding="utf-8"
    )
    proc = sh(["bash", str(lone / "done_sweep_gates.sh"), "pre-docs"], wrapper_repo)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert _outcome_rows(proc.stdout) == ["OUTCOME: tool_error"]

    usage = sh([str(WRAPPER), "bogus-phase"], wrapper_repo)
    assert usage.returncode == 3, usage.stdout + usage.stderr
    assert _outcome_rows(usage.stdout) == ["OUTCOME: tool_error"]

    help_proc = sh([str(WRAPPER), "--help"], wrapper_repo)
    assert help_proc.returncode == 0, help_proc.stderr
    assert _outcome_rows(help_proc.stdout) == []


def test_crashing_child_without_outcome_line_is_tool_error(wrapper_repo):
    """[class: REPOSITORY_TEST] A crashed readiness child (a traceback-shaped
    exit 2 emitting no final `OUTCOME:` line) classifies tool error per the
    contract's no-line rule winning over the exit code: the run exits 3 and
    ends stdout with exactly one final `OUTCOME: tool_error` line naming the
    plan. Today the child's exit 2 collapses into the run's fail."""
    _write_readiness_validator(wrapper_repo, STUB_VALIDATOR_CRASH)
    plan_rel = "docs/history/plans/2026-10-03-crashy-plan.md"
    _write_deliverable_plan(wrapper_repo, plan_rel)
    proc = sh([str(WRAPPER), "pre-docs"], wrapper_repo)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert _outcome_rows(proc.stdout) == ["OUTCOME: tool_error"]
    assert proc.stdout.rstrip().endswith("OUTCOME: tool_error")
    assert "crashy-plan" in proc.stdout


def test_child_reporting_indeterminate_is_indeterminate(wrapper_repo):
    """[class: REPOSITORY_TEST] A readiness child reporting indeterminate
    (exit 2 with a final `OUTCOME: indeterminate` line; a legacy shape the
    migrated validator never models) keeps the indeterminate bucket: the run
    exits 2 and ends stdout with exactly one final `OUTCOME: indeterminate`
    line naming the plan."""
    _write_readiness_validator(wrapper_repo, STUB_VALIDATOR_INDETERMINATE)
    plan_rel = "docs/history/plans/2026-10-03-uncertain-plan.md"
    _write_deliverable_plan(wrapper_repo, plan_rel)
    proc = sh([str(WRAPPER), "pre-docs"], wrapper_repo)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert _outcome_rows(proc.stdout) == ["OUTCOME: indeterminate"]
    assert proc.stdout.rstrip().endswith("OUTCOME: indeterminate")
    assert "uncertain-plan" in proc.stdout


def test_indeterminate_dominates_fail_in_aggregation(
    wrapper_repo, monkeypatch, capsys
):
    """[class: REPOSITORY_TEST] One failing gate and one crashed gate in the
    same run aggregate to indeterminate (exit 2, exactly one final `OUTCOME:
    indeterminate` line): uncertainty dominates the definitive subset per the
    contract's multi-input rule, and both gates stay named in the report."""

    def failing(ctx):
        return lib.GateResult("plan-readiness", 1, "stub refusal", warnings=[])

    def raising(ctx):
        raise RuntimeError("stub gate exploded")

    _stub_gates(monkeypatch, {"plan-readiness": failing, "doc-registry": raising})
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(wrapper_repo))
    code = lib.main(["pre-docs"])
    out = capsys.readouterr().out
    assert code == 2, out
    assert _outcome_rows(out) == ["OUTCOME: indeterminate"]
    assert out.rstrip().endswith("OUTCOME: indeterminate")
    assert "plan-readiness" in out
    assert "doc-registry" in out
    assert "stub refusal" in out
