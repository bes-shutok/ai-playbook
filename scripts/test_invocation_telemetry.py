#!/usr/bin/env python3
"""Hermetic pytest suite for the fail-open invocation-telemetry library.

Plan: docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md,
sections "Task 1: the telemetry library and the two python self-timing
integrations" and "Task 2: the pins-suite bash integration and its
repo-resolution arms". Every test below mirrors one plan checkbox
one-for-one and carries the plan's class tag in its docstring
(``[class: REPOSITORY_TEST]``).

Hermeticity contract (the test_done_sweep_gates_lib.py pattern):
- every fixture lives under pytest ``tmp_path``; the metrics home resolves
  inside the fixture (a facts file with ``metrics_dir`` under a fixture
  ``.ai-playbook/``), never the developer's real ``.ai-playbook/metrics``;
- the subprocess-level integration tests run the REAL instrumented scripts
  (cheap modes) with the fixture as the working directory, so the library's
  cwd-anchored facts resolution lands every append inside the fixture;
- the contract baseline pins each probed invocation's pre-integration
  literals (exact stdout, exact stderr, exit code), captured at the plan's
  base before any telemetry integration, and asserts them byte-identical
  with telemetry active.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import invocation_telemetry as itel

PR_SCRIPT = SCRIPTS_DIR / "plan_readiness.py"
VRS_SCRIPT = SCRIPTS_DIR / "validate_review_staging.py"
COSTS_NAME = "invocation-costs.jsonl"

# --------------------------------------------------------------------------- #
# Pinned pre-integration contract literals (contract-baseline checkbox).
# Captured at base c2cfc02a9, before any telemetry integration: each probed
# invocation's exact stdout, exact stderr, and exit code. The subprocess
# integration tests assert these stay byte-identical with telemetry active.
# --------------------------------------------------------------------------- #

PR_SUCCESS = {
    "args": ("--print-artifact-slug", "{plan}"),
    "exit": 0,
    "stdout": "ab-123-good-kebab\nOUTCOME: pass\n",
    "stderr": "",
}
PR_REFUSAL = {
    "args": ("--print-artifact-slug", "{plan_bad}"),
    "exit": 1,
    "stdout": "OUTCOME: fail\n",
    "stderr": (
        "artifact slug FAILED: cannot derive a canonical artifact slug: plan "
        "filename 'bad-name_plan.md' carries feature slug 'bad-name_plan', "
        "whose lowercase form 'bad-name_plan' is not a safe kebab token (only "
        "lowercase letters and digits, joined by single hyphens; no "
        "underscores, dots, or leading/trailing hyphens)\n"
    ),
}
PR_USAGE = {
    "args": ("--pre-round", "--selftest"),
    "exit": 3,
    "stdout": "",
    "stderr": (
        "usage: plan_readiness.py [-h] [--selftest] [--sweep] [--pre-round]\n"
        "                         [--check-review-name ROUND_MD]\n"
        "                         [--print-artifact-slug]\n"
        "                         [plan_path]\n"
        "plan_readiness.py: error: --pre-round must not be combined with"
        " --selftest\n"
        "OUTCOME: tool_error\n"
    ),
}

VRS_SUCCESS = {
    "args": ("--newest-for-branch", "no-such-branch", "--cwd", "{root}"),
    "exit": 0,
    "stdout": "OUTCOME: pass\n",
    "stderr": "",
}
# The refusal probe's stderr: one deterministic eight-line block for an
# undated invalid staging record (an undated filename keeps the date-gated
# freshness errors out of the baseline, so the block is content-only).
VRS_REFUSAL_LINES = [
    "WARN: missing ### Counts or Agents launched row",
    "WARN: missing ### Triage outcomes or Pending triage placeholder",
    "ERROR: missing ## Metadata",
    "ERROR: missing ## Review Statistics",
    "ERROR: missing ### Panel under Review Statistics",
    "ERROR: clear round still requires ## Review Statistics",
    "ERROR: missing required stats sidecar: plan-review-fake-slug-r1.stats.json",
    "FAIL: {target}",
]
VRS_REFUSAL = {
    "args": ("--hard", "{target}"),
    "exit": 1,
    "stdout": "OUTCOME: fail\n",
    "stderr": "\n".join(VRS_REFUSAL_LINES) + "\n",
}
VRS_USAGE = {
    "args": (),
    "exit": 3,
    "stdout": "",
    "stderr": (
        "usage: validate_review_staging.py [-h] [--hard] [--json]"
        " [--preflight]\n"
        "                                  [--newest-for-branch BRANCH]"
        " [--cwd CWD]\n"
        "                                  [--selftest] [--source-plan PATH]\n"
        "                                  [--source-rfc PATH]"
        " [--source-doc PATH]\n"
        "                                  [--source-code-repo ROOT]\n"
        "                                  [--source-code-plan SIDECAR-PATH]\n"
        "                                  [--ack-witness PATH]\n"
        "                                  [path]\n"
        "validate_review_staging.py: error: path or --newest-for-branch is"
        " required\n"
        "OUTCOME: tool_error\n"
    ),
}

FACTS_BODY = (
    "# fixture facts\n\n```toml\n"
    'plans_dir = "docs/history/plans/"\n'
    'reviews_dir = ".ai-playbook/reviews/"\n'
    'metrics_dir = ".ai-playbook/metrics/"\n'
    "```\n"
)
FACTS_BODY_NO_METRICS = (
    "# fixture facts\n\n```toml\n"
    'plans_dir = "docs/history/plans/"\n'
    'reviews_dir = ".ai-playbook/reviews/"\n'
    "```\n"
)


# --------------------------------------------------------------------------- #
# Fixture plumbing (tmp-only; nothing outside tmp_path is touched).
# --------------------------------------------------------------------------- #
def make_fixture(tmp_path: Path, *, with_metrics_key: bool = True) -> Path:
    """Fixture working directory whose facts file carries metrics_dir."""
    root = tmp_path / "fixture-repo"
    (root / ".ai-playbook").mkdir(parents=True)
    body = FACTS_BODY if with_metrics_key else FACTS_BODY_NO_METRICS
    (root / ".ai-playbook" / "facts.md").write_text(body, encoding="utf-8")
    return root


def read_cost_lines(home: Path) -> list[dict]:
    """Parsed JSON objects of the home's costs file; empty lines skipped."""
    costs = home / COSTS_NAME
    if not costs.is_file():
        return []
    return [
        json.loads(ln)
        for ln in costs.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


def run_probe(
    script: Path, cwd: Path, args: tuple[str, ...]
) -> subprocess.CompletedProcess:
    """Run one instrumented script as a subprocess inside the fixture."""
    env = dict(os.environ, COLUMNS="80")
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def assert_contract(proc: subprocess.CompletedProcess, spec: dict, root: Path,
                    plan: Path, plan_bad: Path, target: Path) -> None:
    assert proc.returncode == spec["exit"], (
        f"exit {proc.returncode} != {spec['exit']}; stderr={proc.stderr!r}"
    )
    assert proc.stdout == spec["stdout"], f"stdout={proc.stdout!r}"
    assert proc.stderr == spec["stderr"].format(
        root=str(root), plan=str(plan), plan_bad=str(plan_bad),
        target=str(target),
    ), f"stderr={proc.stderr!r}"


def probe_appends_exactly_one_line(
    tmp_path: Path, script: Path, spec: dict, telemetry: dict
) -> None:
    """Shared subprocess invariant: unchanged pinned contract, exactly one
    appended schema-valid line, plausible wall_ms (0 < wall_ms < 60000)."""
    root = make_fixture(tmp_path)
    plan = root / "2026-01-01-AB-123-good-kebab.md"
    plan.write_text("# fixture plan\n", encoding="utf-8")
    plan_bad = root / "bad-name_plan.md"
    plan_bad.write_text("# fixture plan\n", encoding="utf-8")
    target = (root / "plan-review-fake-slug-r1.md").resolve()
    target.write_text("not a valid staging record\n", encoding="utf-8")
    args = tuple(
        part.format(root=str(root), plan=str(plan), plan_bad=str(plan_bad),
                    target=str(target))
        for part in spec["args"]
    )
    proc = run_probe(script, root, args)
    assert_contract(proc, spec, root, plan, plan_bad, target)
    lines = read_cost_lines(root / ".ai-playbook" / "metrics")
    assert len(lines) == 1, f"expected exactly one appended line: {lines!r}"
    line = lines[0]
    assert line["script"] == telemetry["script"]
    assert line["invocation_kind"] == telemetry["invocation_kind"]
    assert isinstance(line["wall_ms"], (int, float))
    assert 0 < line["wall_ms"] < 60000, f"wall_ms={line['wall_ms']!r}"


# --------------------------------------------------------------------------- #
# Library unit tests (one per plan checkbox).
# --------------------------------------------------------------------------- #
def test_record_invocation_appends_line_creating_home(tmp_path):
    """record_invocation appends one line to invocation-costs.jsonl in the
    given home, creating the home on first write; the home parameter
    overrides resolution for tests; returns True on a writable home.
    [class: IMPLEMENTATION_REQUIRED -> REPOSITORY_TEST]"""
    home = tmp_path / "metrics-home"  # absent: the write creates it
    assert itel.record_invocation(
        "plan_readiness.py", "readiness-gate", 12.5, home=home
    ) is True
    assert home.is_dir()
    lines = read_cost_lines(home)
    assert len(lines) == 1
    assert lines[0]["script"] == "plan_readiness.py"


def test_facts_resolved_home_through_facts_paths_and_line_schema(
    tmp_path, monkeypatch
):
    """The metrics home resolves through scripts/facts_paths.py (the repo's
    single TOML-fence parser, start_dir-injected at the repo root) and the
    appended line carries the full schema: script basename, invocation_kind,
    wall_ms (number, at least 0), lane_class, worker, recorded_at (UTC
    ISO-8601). [class: IMPLEMENTATION_REQUIRED -> REPOSITORY_TEST]"""
    root = make_fixture(tmp_path)
    monkeypatch.chdir(root)
    assert itel.record_invocation(
        "plan_readiness.py", "readiness-gate", 1.0,
        lane_class="exec", worker=False,
    ) is True
    costs = root / ".ai-playbook" / "metrics" / COSTS_NAME
    assert costs.is_file(), "home not anchored at the fixture repo root"
    (line,) = read_cost_lines(root / ".ai-playbook" / "metrics")
    assert line["script"] == "plan_readiness.py"  # basename, never a path
    assert line["invocation_kind"] == "readiness-gate"
    assert isinstance(line["wall_ms"], (int, float)) and line["wall_ms"] >= 0
    assert line["lane_class"] == "exec"
    assert line["worker"] is False
    stamp = datetime.fromisoformat(line["recorded_at"])
    assert stamp.tzinfo is not None
    assert stamp.utcoffset().total_seconds() == 0  # UTC


def test_facts_nondefault_metrics_dir_is_parser_resolved(tmp_path, monkeypatch):
    """A facts metrics_dir DIFFERENT from the library default pins the
    parser-mediated resolution arm: the writer anchors at the key's value,
    not the .ai-playbook/metrics fallback, so a neutered TOML parser cannot
    pass this arm on the default key. [class: REPOSITORY_TEST]"""
    root = make_fixture(tmp_path)
    facts = root / ".ai-playbook" / "facts.md"
    facts.write_text(
        "# fixture facts\n\n```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'reviews_dir = ".ai-playbook/reviews/"\n'
        'metrics_dir = ".ai-playbook/custom-metrics/"\n'
        "```\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(root)
    assert itel.record_invocation("a.py", "k", 0.5) is True
    custom = root / ".ai-playbook" / "custom-metrics" / COSTS_NAME
    assert custom.is_file(), "home not anchored at the facts key's value"
    assert not (root / ".ai-playbook" / "metrics").exists() or not (
        root / ".ai-playbook" / "metrics" / COSTS_NAME
    ).exists(), "default fallback home must stay empty under a facts key"


def test_metrics_dir_default_applied_by_library(tmp_path, monkeypatch):
    """Facts without a metrics_dir key: the library applies the
    .ai-playbook/metrics default, anchored at the repo root.
    [class: IMPLEMENTATION_REQUIRED -> REPOSITORY_TEST]"""
    root = make_fixture(tmp_path, with_metrics_key=False)
    monkeypatch.chdir(root)
    assert itel.record_invocation("a.py", "k", 0.5) is True
    assert (root / ".ai-playbook" / "metrics" / COSTS_NAME).is_file()


def test_concurrent_appends_leave_every_line_parseable(tmp_path):
    """O_APPEND plus one write() per line (no read-modify-write, no temp
    rename): N concurrent record_invocation callers leave every appended
    line parseable. [class: IMPLEMENTATION_REQUIRED -> REPOSITORY_TEST]"""
    home = tmp_path / "metrics-home"
    threads_n, per_thread = 8, 5

    def hammer(worker_id: int) -> None:
        for i in range(per_thread):
            assert itel.record_invocation(
                f"s{worker_id}.py", "k", float(i), home=home
            ) is True

    threads = [
        threading.Thread(target=hammer, args=(w,))
        for w in range(threads_n)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    raw = (home / COSTS_NAME).read_text(encoding="utf-8")
    non_empty = [ln for ln in raw.splitlines() if ln.strip()]
    assert len(non_empty) == threads_n * per_thread
    parsed = [json.loads(ln) for ln in non_empty]  # every line parses
    assert len({p["script"] for p in parsed}) == threads_n


def test_null_lane_or_worker_carries_absence_note(tmp_path):
    """A null lane_class or worker carries a note field naming the absence
    reason, mirroring the landing-cost family's absence-note precedent; a
    fully populated line carries no note. [class: IMPLEMENTATION_REQUIRED
    -> REPOSITORY_TEST]"""
    home = tmp_path / "metrics-home"
    itel.record_invocation("a.py", "k", 1.0, home=home)  # both unknown
    itel.record_invocation(
        "a.py", "k", 1.0, lane_class="exec", home=home
    )  # worker unknown
    itel.record_invocation(
        "a.py", "k", 1.0, worker=True, home=home
    )  # lane unknown
    itel.record_invocation(
        "a.py", "k", 1.0, lane_class="authoring", worker=False, home=home
    )  # nothing unknown
    lines = read_cost_lines(home)
    assert len(lines) == 4
    assert lines[0]["lane_class"] is None and lines[0]["worker"] is None
    assert "lane_class" in lines[0]["note"] and "worker" in lines[0]["note"]
    assert lines[1]["worker"] is None
    assert "worker" in lines[1]["note"]
    assert "lane_class" not in lines[1]["note"]
    assert lines[2]["lane_class"] is None
    assert "lane_class" in lines[2]["note"]
    assert "worker" not in lines[2]["note"]
    assert "note" not in lines[3]


def test_unwritable_home_returns_false_without_raising(tmp_path):
    """Safety witness (fail-openness): an unwritable metrics home modeled as
    a target path under a regular file (immune to uid-0 permission-bit
    bypass) returns False without raising.
    [class: REPOSITORY_TEST]"""
    blocker = tmp_path / "blocker"
    blocker.write_text("regular file, not a directory\n", encoding="utf-8")
    assert itel.record_invocation(
        "a.py", "k", 1.0, home=blocker / "metrics"
    ) is False
    # The regular file's bytes are untouched (the writer never rewrites).
    assert blocker.read_text(encoding="utf-8") == (
        "regular file, not a directory\n"
    )


def test_torn_tail_line_separator_prefixed_in_same_write(tmp_path):
    """A truncated or corrupt trailing line lacking the trailing newline:
    the writer prefixes the separating newline into the same single write
    payload (last-byte check, no read-modify-write of the line bytes) and
    the file gains exactly one new schema-valid line after the corrupt
    bytes. [class: REPOSITORY_TEST]"""
    home = tmp_path / "metrics-home"
    home.mkdir()
    costs = home / COSTS_NAME
    corrupt = b'{"script": "torn.py", "wall_ms"'
    costs.write_bytes(corrupt)  # torn tail: no trailing newline
    assert itel.record_invocation("next.py", "k", 2.0, home=home) is True
    data = costs.read_bytes()
    assert data.startswith(corrupt), "corrupt bytes must stay untouched"
    assert data[len(corrupt):len(corrupt) + 1] == b"\n", (
        "the separating newline must be prefixed into the same write payload"
    )
    tail = data[len(corrupt) + 1:]
    assert tail.endswith(b"\n")
    lines = [
        json.loads(ln)
        for ln in tail.decode("utf-8").splitlines()
        if ln.strip()  # parseability witnesses skip empty lines
    ]
    assert len(lines) == 1
    assert lines[0]["script"] == "next.py"
    assert lines[0]["wall_ms"] >= 0


def test_start_stamp_fractional_epoch_two_stamps_differ():
    """The start stamp records sub-second-resolution values (fractional
    epoch) and two consecutive stamps differ.
    [class: REPOSITORY_TEST]"""
    first = itel.start_stamp()
    second = itel.start_stamp()
    assert isinstance(first, float) and isinstance(second, float)
    assert first % 1 != 0 and second % 1 != 0, "stamps must be fractional"
    assert second != first, "two consecutive stamps must differ"
    assert itel.elapsed_ms(first) >= 0.0


# --------------------------------------------------------------------------- #
# Subprocess-level integration tests: one per instrumented script per exit
# path (the test_done_sweep_gates_lib.py pattern; tmp fixture; the pinned
# contract literals must stay byte-identical with telemetry active).
# --------------------------------------------------------------------------- #
def test_plan_readiness_success_appends_one_line(tmp_path):
    """plan_readiness success path: pinned literals unchanged, exactly one
    readiness-gate line. [class: REPOSITORY_TEST]"""
    probe_appends_exactly_one_line(
        tmp_path, PR_SCRIPT, PR_SUCCESS,
        {"script": "plan_readiness.py", "invocation_kind": "readiness-gate"},
    )


def test_plan_readiness_refusal_appends_one_line(tmp_path):
    """plan_readiness refusal path (nonzero exit): pinned literals
    unchanged, exactly one readiness-gate line. [class: REPOSITORY_TEST]"""
    probe_appends_exactly_one_line(
        tmp_path, PR_SCRIPT, PR_REFUSAL,
        {"script": "plan_readiness.py", "invocation_kind": "readiness-gate"},
    )


def test_plan_readiness_usage_error_appends_one_line(tmp_path):
    """plan_readiness usage-error path (SystemExit from the parser): pinned
    literals unchanged, exactly one readiness-gate line.
    [class: REPOSITORY_TEST]"""
    probe_appends_exactly_one_line(
        tmp_path, PR_SCRIPT, PR_USAGE,
        {"script": "plan_readiness.py", "invocation_kind": "readiness-gate"},
    )


def test_vrs_success_appends_one_line(tmp_path):
    """validate_review_staging success path: pinned literals unchanged,
    exactly one review-validation line. [class: REPOSITORY_TEST]"""
    probe_appends_exactly_one_line(
        tmp_path, VRS_SCRIPT, VRS_SUCCESS,
        {
            "script": "validate_review_staging.py",
            "invocation_kind": "review-validation",
        },
    )


def test_vrs_refusal_appends_one_line(tmp_path):
    """validate_review_staging refusal path (--hard invalid record, exit 1):
    pinned literals unchanged, exactly one review-validation line.
    [class: REPOSITORY_TEST]"""
    probe_appends_exactly_one_line(
        tmp_path, VRS_SCRIPT, VRS_REFUSAL,
        {
            "script": "validate_review_staging.py",
            "invocation_kind": "review-validation",
        },
    )


def test_vrs_usage_error_appends_one_line(tmp_path):
    """validate_review_staging usage-error path: pinned literals unchanged,
    exactly one review-validation line. [class: REPOSITORY_TEST]"""
    probe_appends_exactly_one_line(
        tmp_path, VRS_SCRIPT, VRS_USAGE,
        {
            "script": "validate_review_staging.py",
            "invocation_kind": "review-validation",
        },
    )


# --------------------------------------------------------------------------- #
# Task 2: the pins-suite bash integration (subprocess-level, tmp fixture).
# The fixture copies the pins script and its telemetry library beside a
# facts file into a fake checkout (root marker: .ai-playbook/facts.md, no
# .git), and the probe runs it with a NON-REPO working directory, so the
# append can only resolve through the library's location-based repo walk.
# The pins suite's pass arm needs the whole real repository (the suite
# greps dozens of repo files), so the cheap probed arm here is the
# not-inside-a-git-repo tool-error arm; the real-suite OUTCOME: pass
# stdout byte-identity is pinned at the execution run level against the
# pre-integration capture (Task 2 GREEN evidence), not in this hermetic
# suite.
# --------------------------------------------------------------------------- #
PINS_SCRIPT = SCRIPTS_DIR / "check_maintenance_pins.sh"
PINS_LIB_FILES = ("invocation_telemetry.py", "facts_paths.py")
# Pinned pre-integration contract literals for the tool-error arm,
# captured at base 7f49c622e before any telemetry integration.
PINS_TOOL_ERROR = {
    "exit": 3,
    "stdout": "OUTCOME: tool_error\n",
    "stderr": "not inside a git repo\n",
}


def make_pins_fixture(tmp_path: Path) -> Path:
    """A fixture checkout: the pins script plus its telemetry library under
    scripts/ beside a facts file carrying metrics_dir; the .ai-playbook/
    facts.md marker is the repo-root marker the location walk anchors on."""
    root = tmp_path / "fixture-checkout"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / ".ai-playbook").mkdir()
    (root / ".ai-playbook" / "facts.md").write_text(FACTS_BODY, encoding="utf-8")
    shutil.copy2(PINS_SCRIPT, scripts / PINS_SCRIPT.name)
    for name in PINS_LIB_FILES:
        shutil.copy2(SCRIPTS_DIR / name, scripts / name)
    return root


def run_pins_probe(script: Path, cwd: Path) -> subprocess.CompletedProcess:
    """Run the pins script copy as a subprocess from a non-repo cwd."""
    return subprocess.run(
        ["bash", str(script)],
        cwd=str(cwd),
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_pins_suite_location_arm_appends_exactly_one_line(tmp_path):
    """Pins-suite subprocess integration (the tmp fixture copy resolving
    through the location-based arm): the not-inside-a-git-repo arm exits
    through emit_outcome before any cwd-resolvable home exists, still
    appends exactly one invocation_kind pins-suite line anchored at the
    SCRIPT'S location (never at the working directory), and the arm's
    pinned pre-integration contract literals stay byte-identical.
    [class: REPOSITORY_TEST]"""
    root = make_pins_fixture(tmp_path)
    probe_cwd = tmp_path / "non-repo-cwd"
    probe_cwd.mkdir()
    proc = run_pins_probe(root / "scripts" / PINS_SCRIPT.name, probe_cwd)
    assert proc.returncode == PINS_TOOL_ERROR["exit"], (
        f"exit {proc.returncode}; stderr={proc.stderr!r}"
    )
    assert proc.stdout == PINS_TOOL_ERROR["stdout"], f"stdout={proc.stdout!r}"
    assert proc.stderr == PINS_TOOL_ERROR["stderr"], f"stderr={proc.stderr!r}"
    lines = read_cost_lines(root / ".ai-playbook" / "metrics")
    assert len(lines) == 1, f"expected exactly one appended line: {lines!r}"
    line = lines[0]
    assert line["script"] == "check_maintenance_pins.sh"
    assert line["invocation_kind"] == "pins-suite"
    assert isinstance(line["wall_ms"], (int, float))
    assert 0 < line["wall_ms"] < 60000, f"wall_ms={line['wall_ms']!r}"
    assert line["lane_class"] is None and line["worker"] is None
    assert "note" in line, "null lane/worker must carry the absence notes"
    # The home anchored at the script's own installed location (the
    # fixture checkout); the non-repo working directory gained nothing.
    assert not (probe_cwd / ".ai-playbook").exists()


def test_pins_suite_deployed_copy_outside_any_checkout_records_no_line(tmp_path):
    """The named zero-line exception (a script copy whose file lives
    outside any checkout fails open with no line): a non-repo scratch
    probe of a bare deployed copy asserts the unchanged tool-error
    contract and zero appended lines anywhere.
    [class: REPOSITORY_TEST]"""
    bare = tmp_path / "bare-deployed"
    (bare / "scripts").mkdir(parents=True)
    shutil.copy2(PINS_SCRIPT, bare / "scripts" / PINS_SCRIPT.name)
    for name in PINS_LIB_FILES:
        shutil.copy2(SCRIPTS_DIR / name, bare / "scripts" / name)
    probe_cwd = tmp_path / "non-repo-cwd"
    probe_cwd.mkdir()
    proc = run_pins_probe(bare / "scripts" / PINS_SCRIPT.name, probe_cwd)
    assert proc.returncode == PINS_TOOL_ERROR["exit"], (
        f"exit {proc.returncode}; stderr={proc.stderr!r}"
    )
    assert proc.stdout == PINS_TOOL_ERROR["stdout"], f"stdout={proc.stdout!r}"
    assert proc.stderr == PINS_TOOL_ERROR["stderr"], f"stderr={proc.stderr!r}"
    for scope in (bare, probe_cwd):
        assert not (scope / ".ai-playbook" / "metrics" / COSTS_NAME).exists(), (
            f"zero-line exception violated under {scope}"
        )


# --------------------------------------------------------------------------- #
# Task 3: the closeout-battery line spanning the whole finalize (plan
# docs/history/plans/2026-10-14-script-runtime-cost-telemetry.md, Task 3).
# Subprocess-level witnesses against a tmp fixture repo, following the
# test_done_run_wrapper.py DoneRunFinalizeTest pattern: the REAL
# scripts/done_run.sh finalize runs the real release ceremony (checkpoint
# create-then-refresh, manifest finalize, checkpoint remove, lock releases,
# status verification, report-input assembly) with the lock and sweep homes
# pinned under tmp, and the facts-resolved metrics home resolves inside the
# fixture. The contract baseline pins each probed arm's pre-integration
# literals (exit status, stdout lines, stderr text), captured at base
# d88657273 before the Task 3 integration; finalize stdout/stderr embed tmp
# paths, run ids, and content digests, so the pinned literals are the
# captured bytes with exactly those varying tokens masked by
# normalize_done_output on both sides.
# --------------------------------------------------------------------------- #
DONE_RUN_SCRIPT = SCRIPTS_DIR / "done_run.sh"
DONE_LOCK_SCRIPT_FILE = SCRIPTS_DIR / "done-lock.sh"
# The sweep-gates lib's sibling import closure: the safety witness copies the
# script's full helper closure EXCEPT the telemetry library, so the
# closeout-site telemetry import fails while every other step is hermetic.
DONE_RUN_LIB_COPY_FILES = (
    "corrections_record.py",
    "done_sweep_gates_lib.py",
    "facts_paths.py",
    "plan_shape.py",
    "review_record_selection.py",
    "review_staging_calibration.py",
    "validate_review_staging.py",
)
LANDING_COSTS_NAME = "landing-costs.jsonl"

# Pinned pre-integration contract literals for the probed closeout arms,
# captured at base d88657273 (before the Task 3 integration) with
# normalize_done_output applied. The release ceremony's stdout prologue, the
# landing-summary variants, and the checkpoint create-then-refresh fallback
# stderr line are shared; each arm's literal is the captured composition.
_FINALIZE_RELEASE_STDOUT = (
    "finalize-manifest: run <RUN_ID> marked complete in"
    " <TMP>/done-fixture-repo/docs/tmp/done-session/run-manifest-<RUN_ID>.json\n"
    "removed: checkpoint-manifest run <RUN_ID>"
    " (<TMP>/done-fixture-repo/docs/tmp/done-session/"
    "run-checkpoint-<RUN_ID>.json)\n"
    "done-lock: removed released lock at <TMP>/locks/done/<HEX>\n"
    "done-lock: released lock for <TMP>/done-fixture-repo\n"
    "OUTCOME: pass\n"
    "done_run finalize: merge lock free\n"
    "done-lock: free (<TMP>/done-fixture-repo)\n"
    "OUTCOME: pass\n"
    "done_run finalize: done lock status: free\n"
)
_FINALIZE_NO_LEDGER_SUMMARY = (
    "done_run finalize: landing summary: no owned-commits ledger for this"
    " run; nothing landed in the project repo through the commit subcommand\n"
)
_FINALIZE_LANDING_SUMMARY = (
    "done_run finalize: landing summary: run_id=<RUN_ID> ledger="
    "<TMP>/done-fixture-repo/docs/tmp/done-session/"
    "owned-commits-<RUN_ID>.txt commits=1 landing_commit=<HEX>\n"
)
_FINALIZE_SCAN_TAIL = "missing-review-record scan: 0 missing record(s)\n"
_FINALIZE_FALLBACK_CREATE_STDERR = (
    "created: checkpoint-manifest run <RUN_ID> at"
    " <TMP>/done-fixture-repo/docs/tmp/done-session/"
    "run-checkpoint-<RUN_ID>.json (manifest sha256 <HEX>, gates green: 1)\n"
)
PINNED_NO_LEDGER_STDOUT = (
    _FINALIZE_RELEASE_STDOUT + _FINALIZE_NO_LEDGER_SUMMARY + _FINALIZE_SCAN_TAIL
)
PINNED_NO_LEDGER_STDERR = _FINALIZE_FALLBACK_CREATE_STDERR
PINNED_NO_LANDING_COST_STDOUT = (
    _FINALIZE_RELEASE_STDOUT + _FINALIZE_LANDING_SUMMARY + _FINALIZE_SCAN_TAIL
)
PINNED_NO_LANDING_COST_STDERR = _FINALIZE_FALLBACK_CREATE_STDERR
PINNED_LANDING_STDOUT = (
    PINNED_NO_LANDING_COST_STDOUT
    + "landing-cost telemetry appended:"
    " <TMP>/done-fixture-repo/.ai-playbook/metrics//landing-costs.jsonl\n"
)
PINNED_LANDING_STDERR = _FINALIZE_FALLBACK_CREATE_STDERR
PINNED_NO_MANIFEST_STDOUT = (
    "done_run finalize: no run manifest from setup; nothing to finalize or"
    " checkpoint; the release still runs\n"
    "done_run finalize: releasing the done lock via the from-holder arm (the"
    " hold's own acquire-time records gate it)\n"
    "done-lock: lock already released (<TMP>/locks/done/<HEX>)\n"
    "OUTCOME: pass\n"
    "done_run finalize: merge lock free\n"
    "done-lock: free (<TMP>/done-fixture-repo)\n"
    "OUTCOME: pass\n"
    "done_run finalize: done lock status: free\n"
    + _FINALIZE_NO_LEDGER_SUMMARY
    + _FINALIZE_SCAN_TAIL
)
PINNED_NO_MANIFEST_STDERR = ""


def make_done_fixture(tmp_path: Path) -> Path:
    """A tmp fixture repo whose facts file resolves tmp_dir and metrics_dir
    inside the fixture (the wrapper suite's init_fixture_repo shape)."""
    root = tmp_path / "done-fixture-repo"
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)

    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True
        )

    git("config", "user.email", "t@example.test")
    git("config", "user.name", "t")
    (root / "seed.txt").write_text("seed\n", encoding="utf-8")
    (root / ".gitignore").write_text("docs/tmp/\n__pycache__/\n", encoding="utf-8")
    (root / ".ai-playbook").mkdir()
    (root / "docs" / "tmp").mkdir(parents=True)
    (root / ".ai-playbook" / "facts.md").write_text(
        "# fixture facts\n\n```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'backlog_dir = "docs/history/backlog/"\n'
        'reviews_dir = ".ai-playbook/reviews/"\n'
        'tmp_dir = "docs/tmp/"\n'
        'metrics_dir = ".ai-playbook/metrics/"\n'
        "```\n",
        encoding="utf-8",
    )
    git("add", ".")
    git("commit", "-qm", "seed")
    return root


DONE_RUNNER_SCRUB_VARS = (
    "DONE_LOCK_DIR", "DONE_LOCK_TOKEN", "DONE_LOCK_HOLDER_PID",
    "DONE_LOCK_POLL_SECS", "DONE_LOCK_STALE_SECS",
    "DONE_LOCK_INCOMPLETE_SECS", "DONE_LOCK_DEAD_HOLDER_GRACE_SECS",
    "DONE_LOCK_AGENT_MAX_WAIT_SECS", "DONE_LOCK_HOLD_PIN",
    "MERGE_LOCK_DIR", "MERGE_LOCK_TOKEN", "MERGE_LOCK_HOLDER_PID",
    "MERGE_LOCK_POLL_SECS", "MERGE_LOCK_STALE_SECS",
    "MERGE_LOCK_INCOMPLETE_SECS", "MERGE_LOCK_DEAD_HOLDER_GRACE_SECS",
    "DOCS_SYNC_NOW", "DOCS_SYNC_TRACE_FILE", "DOCS_SYNC_MERGE_MAX_WAIT",
    "PLAN_READINESS_VALIDATOR", "BACKLOG_LOCATION_GATE",
    "CHECK_NO_EM_DASH_SCRIPT", "CONFLUENCE_MIRROR_HYGIENE_SCRIPT",
    "DOC_REGISTRY_VALIDATOR_SCRIPT", "REVIEW_STAGING_VALIDATOR",
    "PUBLIC_HYGIENE_SCAN_SCRIPT", "PUBLIC_HYGIENE_PATTERNS_FILE",
    "PUBLIC_HYGIENE_REPO_ROOT",
    "INSTRUCTION_SIZE_CHECK_SCRIPT",
    "DESCRIPTION_LENGTH_CHECK_SCRIPT", "REVERSE_SQUASH_GUARD_SCRIPT",
    "CHECK_PLAN_ORIGINS_CLOSED_SCRIPT",
    "DONE_RUN_TRACE_FILE", "DONE_RUN_LINTER",
    "DONE_RUN_ID", "DONE_RUN_MANIFEST", "DONE_RUN_MARKER",
    "PYTHONPATH",
)


def done_runner_env(tmp_path: Path, root: Path) -> dict:
    """The hermetic finalize environment (the wrapper suite's runner_env
    shape): lock and sweep homes pinned under tmp, the venv's python3 first
    on PATH, no ambient DONE_* / MERGE_* / validator state."""
    env = dict(os.environ)
    for var in DONE_RUNNER_SCRUB_VARS:
        env.pop(var, None)
    env["PATH"] = (
        str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    )
    env["DONE_LOCK_ROOT"] = str(tmp_path / "locks" / "done")
    env["MERGE_LOCK_ROOT"] = str(tmp_path / "locks" / "merge")
    env["MERGE_LOCK_POLL_SECS"] = "1"
    env["DONE_LOCK_SCRIPT"] = str(DONE_LOCK_SCRIPT_FILE)
    env["DONE_SWEEP_REPO_ROOT"] = str(root)
    env["DONE_SWEEP_RUNTIME_HOME"] = str(tmp_path / "runtime-home")
    env["DONE_SWEEP_USER_FACTS"] = str(tmp_path / "user-facts.md")
    return env


def run_done_run(
    script: Path, cwd: Path, env: dict, *args: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def eval_done_exports(output: str) -> dict:
    """Parse the runner's `export K=V` stdout lines into a dict."""
    exports: dict[str, str] = {}
    for line in output.splitlines():
        if line.startswith("export "):
            key, _, raw = line[len("export "):].partition("=")
            exports[key] = shlex.split(raw)[0]
    return exports


def normalize_done_output(text: str, base: Path) -> str:
    """Mask exactly the tokens a fixture run cannot pin (the tmp base holding
    the fixture repo and the lock homes, the run-id stamp and its hex
    suffix, content digests, lock ages) so the captured pre-integration
    bytes stay comparable across fixtures. Longest variant first: the
    resolved /private/var realpath form contains the /var form."""
    variants = sorted(
        {str(base), os.path.realpath(str(base))}, key=len, reverse=True
    )
    for variant in variants:
        text = text.replace(variant, "<TMP>")
    text = re.sub(r"\b\d{8}T\d{6}Z-[0-9a-f]{6,64}\b", "<RUN_ID>", text)
    text = re.sub(r"\b[0-9a-f]{6,64}\b", "<HEX>", text)
    text = re.sub(r"age [0-9]+s", "age <N>s", text)
    return text


def read_landing_lines(root: Path) -> list[dict]:
    """Parsed JSON objects of the fixture's landing-costs.jsonl."""
    costs = root / ".ai-playbook" / "metrics" / LANDING_COSTS_NAME
    if not costs.is_file():
        return []
    return [
        json.loads(ln)
        for ln in costs.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


def seed_done_run(
    tmp_path: Path, root: Path
) -> tuple[dict, dict]:
    """A real setup run (boundary marker, manifest, lock hold); returns the
    hermetic env and the setup exports."""
    env = done_runner_env(tmp_path, root)
    proc = run_done_run(
        DONE_RUN_SCRIPT, root, env, "setup", "--label", "telemetry-fixture"
    )
    assert proc.returncode == 0, proc.stderr
    return env, eval_done_exports(proc.stdout)


def write_landing_ledger(root: Path, run_id: str) -> str:
    """One real landing commit plus the owned-commits ledger tail that
    finalize's landing summary reads; returns the landing commit sha."""
    (root / "landing.txt").write_text("landed work\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(root), "add", "landing.txt"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "fixture landing"],
        check=True, capture_output=True,
    )
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    session = root / "docs" / "tmp" / "done-session"
    (session / f"owned-commits-{run_id}.txt").write_text(
        commit + "\n", encoding="utf-8"
    )
    return commit


def closeout_probe(
    tmp_path: Path, *, landing: bool, finalize_args: tuple[str, ...] = ()
) -> tuple[subprocess.CompletedProcess, Path, str, str]:
    """One real closeout: setup then finalize against the tmp fixture.
    Returns (finalize proc, fixture root, run_id, landing_commit)."""
    root = make_done_fixture(tmp_path)
    env, exports = seed_done_run(tmp_path, root)
    landing_commit = ""
    if landing:
        landing_commit = write_landing_ledger(root, exports["DONE_RUN_ID"])
    finalize_env = dict(env)
    finalize_env.update(exports)
    proc = run_done_run(
        DONE_RUN_SCRIPT, root, finalize_env, "finalize", *finalize_args
    )
    return proc, root, exports["DONE_RUN_ID"], landing_commit


def assert_closeout_line(line: dict) -> None:
    """The one closeout-battery line's schema plus the magnitude witness:
    wall_ms spans the whole finalize ceremony (at least 100 ms), not just
    the writer block."""
    assert line["script"] == "done_run.sh"
    assert line["invocation_kind"] == "closeout-battery"
    assert isinstance(line["wall_ms"], (int, float))
    assert line["wall_ms"] >= 100, f"wall_ms={line['wall_ms']!r}"
    assert line["lane_class"] is None and line["worker"] is None
    assert "note" in line, "null lane/worker must carry the absence notes"


def test_finalize_no_ledger_closeout_appends_one_closeout_line(tmp_path):
    """Placement witness (no-ledger arm): a real no-ledger closeout (the
    landing-cost guard skips on the empty ledger) still records exactly one
    closeout-battery line, the arm's pinned pre-integration stdout and
    stderr literals stay byte-identical, and stdout carries no telemetry
    prose. [class: REPOSITORY_TEST]"""
    proc, root, _run_id, _commit = closeout_probe(tmp_path, landing=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert normalize_done_output(proc.stdout, tmp_path) == PINNED_NO_LEDGER_STDOUT
    assert normalize_done_output(proc.stderr, tmp_path) == PINNED_NO_LEDGER_STDERR
    lines = read_cost_lines(root / ".ai-playbook" / "metrics")
    assert len(lines) == 1, f"expected exactly one appended line: {lines!r}"
    assert_closeout_line(lines[0])
    # The landing-cost guard fired its skip: no landing-cost record exists.
    assert not (root / ".ai-playbook" / "metrics" / LANDING_COSTS_NAME).exists()


def test_finalize_no_landing_cost_closeout_appends_one_closeout_line(tmp_path):
    """Placement witness (--no-landing-cost arm): a landing-bearing closeout
    run with --no-landing-cost records exactly one closeout-battery line and
    zero landing-cost lines; the arm's pinned pre-integration contract
    literals stay byte-identical. [class: REPOSITORY_TEST]"""
    proc, root, _run_id, _commit = closeout_probe(
        tmp_path, landing=True, finalize_args=("--no-landing-cost",)
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert (
        normalize_done_output(proc.stdout, tmp_path)
        == PINNED_NO_LANDING_COST_STDOUT
    )
    assert (
        normalize_done_output(proc.stderr, tmp_path)
        == PINNED_NO_LANDING_COST_STDERR
    )
    lines = read_cost_lines(root / ".ai-playbook" / "metrics")
    assert len(lines) == 1, f"expected exactly one appended line: {lines!r}"
    assert_closeout_line(lines[0])
    assert read_landing_lines(root) == []


def test_finalize_landing_bearing_keeps_landing_cost_line_beside_closeout(tmp_path):
    """Placement witness (landing-bearing arm): a real landing closeout
    keeps the landing-cost record intact beside the closeout-battery line;
    the landing summary and the landing-cost telemetry line stay on stdout
    against the pinned literals. [class: REPOSITORY_TEST]"""
    proc, root, _run_id, landing_commit = closeout_probe(
        tmp_path, landing=True
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert normalize_done_output(proc.stdout, tmp_path) == PINNED_LANDING_STDOUT
    assert normalize_done_output(proc.stderr, tmp_path) == PINNED_LANDING_STDERR
    assert "landing-cost telemetry appended:" in proc.stdout
    landing_lines = read_landing_lines(root)
    assert len(landing_lines) == 1, "the landing-cost record must stay intact"
    assert landing_lines[0]["landing_commit"] == landing_commit
    lines = read_cost_lines(root / ".ai-playbook" / "metrics")
    assert len(lines) == 1, f"expected exactly one appended line: {lines!r}"
    assert_closeout_line(lines[0])


def test_finalize_no_manifest_closeout_appends_one_closeout_line(tmp_path):
    """Guard-scope witness (no-manifest arm): a finalize with no run
    manifest at all (the RUN_MANIFEST arm of the landing-cost guard skips
    the landing-cost writer) still records exactly one closeout-battery
    line against the pinned pre-integration literals.
    [class: REPOSITORY_TEST]"""
    root = make_done_fixture(tmp_path)
    env = done_runner_env(tmp_path, root)
    proc = run_done_run(DONE_RUN_SCRIPT, root, env, "finalize")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert (
        normalize_done_output(proc.stdout, tmp_path) == PINNED_NO_MANIFEST_STDOUT
    )
    assert (
        normalize_done_output(proc.stderr, tmp_path) == PINNED_NO_MANIFEST_STDERR
    )
    lines = read_cost_lines(root / ".ai-playbook" / "metrics")
    assert len(lines) == 1, f"expected exactly one appended line: {lines!r}"
    assert_closeout_line(lines[0])
    assert read_landing_lines(root) == []


def test_finalize_usage_error_records_no_line(tmp_path):
    """Named zero-line exception (usage-error arm): an unknown finalize
    argument exits during argument parsing, before the exit-side append,
    and records no line anywhere. [class: REPOSITORY_TEST]"""
    root = make_done_fixture(tmp_path)
    env = done_runner_env(tmp_path, root)
    proc = run_done_run(DONE_RUN_SCRIPT, root, env, "finalize", "--bogus")
    assert proc.returncode == 3, proc.stderr
    assert proc.stdout == ""
    assert proc.stderr == "done_run finalize: unknown argument: --bogus\n"
    assert not (root / ".ai-playbook" / "metrics" / COSTS_NAME).exists()


def test_finalize_early_refusal_records_no_line(tmp_path):
    """Named zero-line exception (early-refusal arm): a finalize outside any
    git repository takes the not-inside-a-repo stop before the exit-side
    append and records no line anywhere. [class: REPOSITORY_TEST]"""
    root = make_done_fixture(tmp_path)
    env = done_runner_env(tmp_path, root)
    non_repo = tmp_path / "non-repo-cwd"
    non_repo.mkdir()
    proc = run_done_run(DONE_RUN_SCRIPT, non_repo, env, "finalize")
    assert proc.returncode == 3, proc.stderr
    assert proc.stdout == ""
    assert proc.stderr == "done_run finalize: not inside a git repository\n"
    assert not (root / ".ai-playbook" / "metrics" / COSTS_NAME).exists()


def test_finalize_telemetry_failure_leaves_contract_and_landing_cost_intact(tmp_path):
    """Safety witness: a telemetry failure at the closeout site (a deployed
    script copy whose helper closure omits the telemetry library, so the
    exit-side import fails) leaves the closeout flow completing with the
    pinned pre-integration contract literals (exit status, stdout lines,
    stderr text) and the landing-cost record unaffected; no invocation line
    is recorded. [class: REPOSITORY_TEST]"""
    root = make_done_fixture(tmp_path)
    scripts = root / "scripts"
    scripts.mkdir()
    copy = scripts / DONE_RUN_SCRIPT.name
    shutil.copy2(DONE_RUN_SCRIPT, copy)
    shutil.copy2(DONE_LOCK_SCRIPT_FILE, scripts / DONE_LOCK_SCRIPT_FILE.name)
    for name in DONE_RUN_LIB_COPY_FILES:
        shutil.copy2(SCRIPTS_DIR / name, scripts / name)
    assert not (scripts / "invocation_telemetry.py").exists()
    env = done_runner_env(tmp_path, root)
    env["DONE_LOCK_SCRIPT"] = str(scripts / DONE_LOCK_SCRIPT_FILE.name)
    setup = run_done_run(copy, root, env, "setup", "--label", "telemetry-fixture")
    assert setup.returncode == 0, setup.stderr
    exports = eval_done_exports(setup.stdout)
    landing_commit = write_landing_ledger(root, exports["DONE_RUN_ID"])
    finalize_env = dict(env)
    finalize_env.update(exports)
    proc = run_done_run(copy, root, finalize_env, "finalize")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    # Byte-identical with the healthy landing-bearing arm's pinned literals.
    assert normalize_done_output(proc.stdout, tmp_path) == PINNED_LANDING_STDOUT
    assert normalize_done_output(proc.stderr, tmp_path) == PINNED_LANDING_STDERR
    assert "landing-cost telemetry appended:" in proc.stdout
    landing_lines = read_landing_lines(root)
    assert len(landing_lines) == 1, "the landing-cost record must stay intact"
    assert landing_lines[0]["landing_commit"] == landing_commit
    assert not (root / ".ai-playbook" / "metrics" / COSTS_NAME).exists(), (
        "the failed telemetry site must record no line (fail-open, silent)"
    )
