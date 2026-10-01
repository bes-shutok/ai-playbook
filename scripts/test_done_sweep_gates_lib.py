#!/usr/bin/env python3
"""Hermetic pytest suite for the done sweep gate runner lib (plan Task 1).

Plan: docs/history/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md,
section "Task 1: Done sweep gate runner script". Every test below mirrors one
plan checkbox one-for-one and carries the plan's class tag in its docstring
(`[class: REPOSITORY_TEST]`).

Hermeticity contract:
- every fixture lives under pytest ``tmp_path`` (own git repo, own facts file);
- no network; no real ``~/.ai-playbook`` dependency: the runtime home and the
  user facts document are redirected via ``DONE_SWEEP_RUNTIME_HOME`` and
  ``DONE_SWEEP_USER_FACTS`` so every resolved path lands inside the fixture;
- repo-relative path resolution goes through the fixture repo's
  ``.ai-playbook/facts.md`` via the ``facts_paths.py`` helpers, anchored at the
  fixture repo root (the same anchor rule the lib uses in production);
- validators under test are either the repo's own scripts (copied into the
  fixture, still hermetic) or deliberate stubs exercising the subprocess seam.
"""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import done_sweep_gates_lib as lib
from done_sweep_gates_lib import (
    PRE_COMMIT_GATES,
    PRE_DOCS_GATES,
    GateContext,
    derive_plan_readiness_candidates,
    derive_review_staging_candidates,
    derive_session_window,
    run_gate,
)

# The absorbed gate ids, in done SKILL.md step order (plan Terms + G2);
# order-neutral name since the count is now fifteen.
EXPECTED_GATE_ORDER = [
    "plan-readiness",
    "confluence-hygiene",
    "doc-registry",
    "backlog-inbox",
    "review-staging",
    "vim-swap-sweep",
    "docs-tmp-sweep",
    "plans-archive-twin",
    "sensitive-data-scan",
    "em-dash-scan",
    "instruction-size",
    "description-length",
    "foreign-staging",
    "archive-ceremony",
    "execute-plan-closeout",
]


# --------------------------------------------------------------------------- #
# Fixture plumbing: tiny git repos with their own facts file under tmp_path.
# --------------------------------------------------------------------------- #
def sh(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True, check=False, timeout=120
    )


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return sh(["git", *args], root)


def make_repo(tmp_path: Path, name: str, gitignore_docs: bool = True) -> Path:
    """Create a fixture git repo with one commit and (optionally) docs/ ignored."""
    root = tmp_path / name
    root.mkdir(parents=True)
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "fixture")
    ignores = ["__pycache__/"]
    if gitignore_docs:
        ignores.append("/docs/")
    (root / ".gitignore").write_text("\n".join(ignores) + "\n", encoding="utf-8")
    (root / "README.md").write_text("fixture repo\n", encoding="utf-8")
    git(root, "add", ".gitignore", "README.md")
    git(root, "commit", "-m", "init", "-q")
    return root


def write_facts(root: Path) -> Path:
    """Write the fixture repo facts file (TOML fence, same keys as production)."""
    facts_dir = root / ".ai-playbook"
    facts_dir.mkdir(parents=True, exist_ok=True)
    facts = facts_dir / "facts.md"
    facts.write_text(
        "```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'plans_completed_dir = "docs/history/plans/completed/"\n'
        'backlog_dir = "docs/history/backlog/"\n'
        'reviews_dir = "docs/reviews/"\n'
        'tmp_dir = "docs/tmp/"\n'
        "```\n",
        encoding="utf-8",
    )
    return facts


def marker_name(epoch: float) -> str:
    return "run-start-" + datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )


def make_marker(root: Path, epoch: float, pid: int) -> Path:
    """Write a content-bearing run-start marker exactly like done Step 0."""
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    marker = done_session / marker_name(epoch)
    marker.write_text(f"{int(epoch)} {root} {pid}\n", encoding="utf-8")
    return marker


def fresh_iso(hours_ago: float = 0.0) -> str:
    """ISO8601 manifest ``updated:`` value in the production ``+0000`` shape."""
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return dt.isoformat(timespec="seconds").replace("+00:00", "+0000")


def write_manifest(root: Path, slug: str, updated: str, state: str = "active") -> Path:
    session_dir = root / "docs" / "tmp" / "execute-plan" / slug
    session_dir.mkdir(parents=True, exist_ok=True)
    manifest = session_dir / "manifest.md"
    manifest.write_text(
        f"# Execute-plan session: {slug}\n\n"
        f"workflow_state: {state}\n"
        f"updated: {updated}\n",
        encoding="utf-8",
    )
    return manifest


def write_deliverables(root: Path, rel_paths: list[str]) -> Path:
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    path = done_session / "plan-deliverables.txt"
    path.write_text("\n".join(rel_paths) + "\n", encoding="utf-8")
    return path


def read_deliverables(root: Path) -> list[str]:
    path = root / "docs" / "tmp" / "done-session" / "plan-deliverables.txt"
    if not path.is_file():
        return []
    return [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def write_stub_readiness_validator(root: Path) -> Path:
    """Repo-local stub validator: exit 0 for plan names containing 'good', else 1."""
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    stub = scripts / "plan_readiness.py"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "plan = sys.argv[1] if len(sys.argv) > 1 else ''\n"
        "if 'good' in plan:\n"
        "    print('ready=yes')\n"
        "    sys.exit(0)\n"
        "print('readiness FAILED: stub rejection')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    return stub


def write_stub_doc_registry_validator(root: Path) -> Path:
    """Repo-local stub doc-registry validator (subprocess seam).

    ``validate`` exits 0. Any other subcommand (``check-writes``) parses each
    stdin line with the real validator's change-line grammar (name-status
    ``L<TAB>path`` rows must carry a valid git letter, porcelain ``XY PATH``
    rows, i.e. ``line[2] == ' '`` with valid XY letters, are typed, anything
    else is a bare row), records the raw bytes to ``DOC_REGISTRY_STUB_STDIN_LOG``,
    then exits: 1 with a type-strip finding when bare rows exist and
    ``DOC_REGISTRY_STUB_REJECT_BARE`` is ``1`` (so a future change-type
    stripping regression fails here), 1 with one flagged row when
    ``DOC_REGISTRY_STUB_FLAG`` is ``1``, else 0.
    """
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    stub = scripts / "doc_registry_validator.py"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import sys\n"
        "if sys.argv[1] == 'validate':\n"
        "    sys.exit(0)\n"
        "data = sys.stdin.read()\n"
        "log = os.environ.get('DOC_REGISTRY_STUB_STDIN_LOG', '')\n"
        "if log:\n"
        "    with open(log, 'w', encoding='utf-8') as fh:\n"
        "        fh.write(data)\n"
        "PORCELAIN_CHARS = set('ADMRUTCX?!.')\n"
        "bare = []\n"
        "for line in data.splitlines():\n"
        "    if not line.strip():\n"
        "        continue\n"
        "    if '\\t' in line:\n"
        "        letter = line.split('\\t', 1)[0].strip()\n"
        "        if letter[:1] == '' or letter.rstrip('0123456789') not in (\n"
        "            'A', 'M', 'D', 'R', 'T', 'C'\n"
        "        ):\n"
        "            print('HARD: unparsable name-status stdin row: %r' % line)\n"
        "            sys.exit(1)\n"
        "    elif (\n"
        "        len(line) >= 3\n"
        "        and line[2] == ' '\n"
        "        and (line[0] in PORCELAIN_CHARS or line[0] == ' ')\n"
        "        and (line[1] in PORCELAIN_CHARS or line[1] == ' ')\n"
        "        and not (line[0] == ' ' and line[1] == ' ')\n"
        "    ):\n"
        "        pass  # typed porcelain row\n"
        "    else:\n"
        "        bare.append(line)\n"
        "if os.environ.get('DOC_REGISTRY_STUB_REJECT_BARE', '') == '1' and bare:\n"
        "    print('HARD: type-stripped stdin rows (change-type letters missing): '\n"
        "          + ', '.join(bare))\n"
        "    sys.exit(1)\n"
        "if os.environ.get('DOC_REGISTRY_STUB_FLAG', '') == '1':\n"
        "    print('HARD: protected write blocked by stub')\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    return stub


def copy_hygiene_script(root: Path) -> Path:
    """Copy the repo's real confluence-mirror-hygiene.sh into the fixture."""
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    target = scripts / "confluence-mirror-hygiene.sh"
    target.write_text(
        (SCRIPTS_DIR / "confluence-mirror-hygiene.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


@pytest.fixture
def sweep_env(tmp_path, monkeypatch):
    """Redirect the runtime home and user facts into tmp_path (hermeticity)."""
    runtime_home = tmp_path / "runtime-home"
    runtime_home.mkdir()
    user_facts = tmp_path / "user-facts.md"
    user_facts.write_text("# fixture user facts\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_RUNTIME_HOME", str(runtime_home))
    monkeypatch.setenv("DONE_SWEEP_USER_FACTS", str(user_facts))
    for var in (
        "PLAN_READINESS_VALIDATOR",
        "CONFLUENCE_MIRROR_HYGIENE_SCRIPT",
        "DOC_REGISTRY_VALIDATOR_SCRIPT",
        "BACKLOG_LOCATION_GATE",
        "REVIEW_STAGING_VALIDATOR",
        "CHECK_NO_EM_DASH_SCRIPT",
        "INSTRUCTION_SIZE_CHECK_SCRIPT",
        "DONE_SWEEP_REPO_ROOT",
    ):
        monkeypatch.delenv(var, raising=False)
    return runtime_home


def ctx_for(root: Path) -> GateContext:
    return GateContext.discover(root)


@pytest.fixture
def mktemp_repo(tmp_path):
    """mktemp -d style repo factory with explicit rm -rf teardown: each repo
    lives in its own mkdtemp parent so a crashed test never leaks fixture
    state (fixture placement-plus-teardown discipline)."""
    parents: list[Path] = []

    def _make(name: str, **kwargs) -> Path:
        parent = Path(tempfile.mkdtemp(prefix="done-manifest-"))
        parents.append(parent)
        return make_repo(parent, name, **kwargs)

    yield _make
    for parent in parents:
        shutil.rmtree(parent, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Plan checkbox: test_gate_registry_matches_absorbed_steps
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_gate_registry_matches_absorbed_steps(capsys):
    """[class: REPOSITORY_TEST] Given the lib gate registry, expects exactly fifteen
    gate ids in the two phase slices, in done SKILL.md order, matching
    plan-readiness, confluence-hygiene, doc-registry, backlog-inbox,
    review-staging, vim-swap-sweep, docs-tmp-sweep, sensitive-data-scan,
    em-dash-scan, instruction-size, description-length, archive-ceremony,
    execute-plan-closeout."""
    assert PRE_DOCS_GATES == EXPECTED_GATE_ORDER[:8]
    assert PRE_COMMIT_GATES[:4] == EXPECTED_GATE_ORDER[8:12]
    assert PRE_COMMIT_GATES[4] == "foreign-staging"
    assert PRE_COMMIT_GATES[5] == "archive-ceremony"
    assert PRE_COMMIT_GATES[6] == "execute-plan-closeout"
    assert PRE_COMMIT_GATES[7] == "plans-archive-twin"
    assert lib.PHASES["pre-docs"] == PRE_DOCS_GATES
    assert lib.PHASES["pre-commit"] == PRE_COMMIT_GATES
    assert list(lib.PHASES.keys()) == ["pre-docs", "pre-commit"]
    # Every registry entry has an implementation and a phase slice.
    assert set(lib.GATES.keys()) == set(EXPECTED_GATE_ORDER)
    # The dead READ_ONLY_GATES set stays deleted (sequential execution).
    assert not hasattr(lib, "READ_ONLY_GATES")
    # list-gates prints the gate ids, deduped at first phase (the twin
    # runs in both phases; printed once at pre-docs).
    assert lib.main(["list-gates"]) == 0
    assert capsys.readouterr().out.splitlines() == EXPECTED_GATE_ORDER
    assert len(EXPECTED_GATE_ORDER) == 15
    assert len(set(EXPECTED_GATE_ORDER)) == 15


# --------------------------------------------------------------------------- #
# Plan checkbox: test_plan_readiness_candidates  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_plan_readiness_candidates(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Deliverables-listed plan, untracked in-window
    plan, fresh-active-manifest plan (exempted), completed-dir entry (excluded):
    candidates are the first two only."""
    root = make_repo(tmp_path, "cand", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    prev = make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())  # current run

    alpha = "docs/history/plans/2026-09-20-alpha.md"
    beta = "docs/history/plans/2026-09-20-beta.md"
    gamma = "docs/history/plans/2026-09-20-gamma.md"
    delta_completed = "docs/history/plans/completed/2026-09-19-delta.md"
    (root / "docs/history/plans").mkdir(parents=True)
    (root / "docs/history/plans/completed").mkdir(parents=True)
    (root / alpha).write_text("alpha\n", encoding="utf-8")
    git(root, "add", "-f", alpha)
    git(root, "commit", "-m", "alpha", "-q")  # tracked, unmodified: deliverables arm only
    (root / beta).write_text("beta\n", encoding="utf-8")  # untracked, fresh mtime
    (root / gamma).write_text("gamma\n", encoding="utf-8")
    (root / delta_completed).write_text("delta\n", encoding="utf-8")
    write_deliverables(root, [alpha, gamma, delta_completed])
    write_manifest(root, "2026-09-20-gamma", fresh_iso())

    derivation = derive_plan_readiness_candidates(ctx_for(root))
    names = [str(p) for p in derivation.candidates]
    assert names == [alpha, beta]
    assert [str(p) for p in derivation.exempted] == [gamma]
    # The completed-dir entry is excluded from gating entirely.
    assert all("completed" not in str(p) for p in derivation.candidates)
    # The window anchored on the previous-run marker.
    assert derivation.window.anchored
    assert derivation.window.anchor.path == prev


# --------------------------------------------------------------------------- #
# Plan checkbox: test_plan_readiness_conservative_gating
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_plan_readiness_conservative_gating(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] No previous-run marker under done-session: the
    window is unanchorable and every gitignored-arm (`!!`) plan is treated as a
    session deliverable; each gated plan is named."""
    root = make_repo(tmp_path, "conservative", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    make_marker(root, now, os.getpid())  # current run only; no previous run
    (root / "docs/history/plans").mkdir(parents=True)
    ignored_plans = [
        "docs/history/plans/2026-09-20-conv-a.md",
        "docs/history/plans/2026-09-20-conv-b.md",
    ]
    for rel in ignored_plans:
        (root / rel).write_text(rel + "\n", encoding="utf-8")

    ctx = ctx_for(root)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    assert not window.anchored

    derivation = derive_plan_readiness_candidates(ctx)
    names = sorted(str(p) for p in derivation.candidates)
    assert names == ignored_plans  # conservative: every `!!` plan named


# --------------------------------------------------------------------------- #
# Plan checkbox: test_plan_readiness_stale_manifest_no_exemption
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_plan_readiness_stale_manifest_no_exemption(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An active manifest whose updated: line is 30
    hours old grants no exemption: the plan stays gated."""
    root = make_repo(tmp_path, "stale", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    plan = "docs/history/plans/2026-09-20-stale-exempt-attempt.md"
    (root / "docs/history/plans").mkdir(parents=True)
    (root / plan).write_text("stale\n", encoding="utf-8")
    write_deliverables(root, [plan])
    write_manifest(root, "2026-09-20-stale-exempt-attempt", fresh_iso(hours_ago=30))

    derivation = derive_plan_readiness_candidates(ctx_for(root))
    assert [str(p) for p in derivation.candidates] == [plan]
    assert derivation.exempted == []


# --------------------------------------------------------------------------- #
# Plan checkbox: test_deliverables_removal_rule  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_deliverables_removal_rule(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Passing, exempted, and archived plans listed in
    plan-deliverables.txt: exactly those lines are removed, no others."""
    root = make_repo(tmp_path, "removal", gitignore_docs=True)
    write_facts(root)
    write_stub_readiness_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())

    plans_dir = root / "docs/history/plans"
    completed_dir = root / "docs/history/plans/completed"
    plans_dir.mkdir(parents=True)
    completed_dir.mkdir(parents=True)
    good = "docs/history/plans/2026-09-20-good-one.md"
    exempt = "docs/history/plans/2026-09-20-exempt-one.md"
    gone = "docs/history/plans/2026-09-20-gone-one.md"
    bad = "docs/history/plans/2026-09-20-bad-one.md"
    (plans_dir / "2026-09-20-good-one.md").write_text("g\n", encoding="utf-8")
    (plans_dir / "2026-09-20-exempt-one.md").write_text("e\n", encoding="utf-8")
    (completed_dir / "2026-09-20-gone-one.md").write_text("gone\n", encoding="utf-8")
    (plans_dir / "2026-09-20-bad-one.md").write_text("b\n", encoding="utf-8")
    write_deliverables(root, [good, exempt, gone, bad])
    write_manifest(root, "2026-09-20-exempt-one", fresh_iso())

    result = run_gate("plan-readiness", ctx_for(root))
    # The failing plan is gated and fails the gate (stub rejection).
    assert result.rc == 1
    assert bad in result.message
    # Removal rule: good (passed), exempt (manifest), gone (archived) removed.
    assert read_deliverables(root) == [bad]


# --------------------------------------------------------------------------- #
# Plan checkbox: test_report_shape_and_order  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_report_shape_and_order(tmp_path, sweep_env, monkeypatch, capsys):
    """[class: REPOSITORY_TEST] An early gate failure still yields one JSON line
    per gate in registry order (gate, rc, message), a human summary block, and a
    phase-level non-zero exit."""
    root = make_repo(tmp_path, "report", gitignore_docs=True)
    write_facts(root)
    write_stub_readiness_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    plan = "docs/history/plans/2026-09-20-bad-report-plan.md"
    (root / "docs/history/plans").mkdir(parents=True)
    (root / plan).write_text("bad\n", encoding="utf-8")
    write_deliverables(root, [plan])
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["pre-docs"])
    out = capsys.readouterr().out
    assert rc != 0
    json_lines = [ln for ln in out.splitlines() if ln.startswith("{")]
    assert len(json_lines) == 8  # one per pre-docs gate, in registry order
    gates = []
    for ln in json_lines:
        payload = json.loads(ln)
        assert set(payload) >= {"gate", "rc", "message"}
        gates.append(payload["gate"])
    assert gates == PRE_DOCS_GATES
    first = json.loads(json_lines[0])
    assert first["gate"] == "plan-readiness" and first["rc"] != 0
    # Human summary block after the JSON lines.
    summary_lines = [ln for ln in out.splitlines() if not ln.startswith("{")]
    assert any("summary" in ln.lower() for ln in summary_lines)
    assert any("plan-readiness" in ln for ln in summary_lines)


# --------------------------------------------------------------------------- #
# Plan checkbox: test_fail_open_gates_preserved  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_fail_open_gates_preserved(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] With the backlog-inbox, review-staging, and
    doc-registry validators absent from every resolved path: backlog-inbox
    warns and continues (rc 0, warning recorded), review-staging no-ops when no
    session-touched staging path exists, doc-registry reports once and
    continues (rc 0)."""
    root = make_repo(tmp_path, "failopen", gitignore_docs=True)
    write_facts(root)
    ctx = ctx_for(root)

    backlog = run_gate("backlog-inbox", ctx)
    assert backlog.rc == 0
    assert any("check_backlog_inbox_location" in w for w in backlog.warnings)

    staging = run_gate("review-staging", ctx)
    assert staging.rc == 0
    assert "no session-touched" in staging.message

    registry = run_gate("doc-registry", ctx)
    assert registry.rc == 0
    assert "doc_registry_validator" in registry.message
    assert any("doc_registry_validator" in w for w in registry.warnings) or (
        "absent" in registry.message
    )


# --------------------------------------------------------------------------- #
# Phase 3 panel fix: absent gate scripts fail closed as deployment gaps.
# --------------------------------------------------------------------------- #
def test_absent_scripts_fail_closed_as_deployment_gaps(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] When a gate's script is absent from every
    resolved path, em-dash-scan and instruction-size fail rc 1 with a
    deployment-gap message naming the script, and confluence-hygiene does the
    same once a run-when trigger is live (before any trigger it no-ops);
    none of them warn-and-continues any more."""
    root = make_repo(tmp_path, "deploy-gap", gitignore_docs=True)
    write_facts(root)
    ctx = ctx_for(root)

    em = run_gate("em-dash-scan", ctx)
    assert em.rc == 1
    assert "deployment gap" in em.message
    assert "check-no-em-dash.sh" in em.message

    size = run_gate("instruction-size", ctx)
    assert size.rc == 1
    assert "deployment gap" in size.message
    assert "check-instruction-size.sh" in size.message

    # confluence-hygiene only arms when a run-when trigger fires.
    noop = run_gate("confluence-hygiene", ctx)
    assert noop.rc == 0
    assert "no-op" in noop.message
    tmp = root / "docs" / "tmp"
    tmp.mkdir(parents=True)
    (tmp / "scratch-cf-out.md").write_text("# Snap\n", encoding="utf-8")
    triggered = run_gate("confluence-hygiene", ctx)
    assert triggered.rc == 1
    assert "deployment gap" in triggered.message
    assert "confluence-mirror-hygiene.sh" in triggered.message
    assert "ephemeral" in triggered.message  # names the live run-when trigger


# --------------------------------------------------------------------------- #
# Phase 3 panel fix: a crashed readiness validator reports its stderr line,
# never the bare "Traceback (most recent call last):" header.
# --------------------------------------------------------------------------- #
def test_plan_readiness_reports_stderr_on_validator_crash(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A readiness validator that crashes (traceback
    on stdout, message on stderr) fails the gate with the stderr message as
    the failure reason; the traceback header never reaches the report."""
    root = make_repo(tmp_path, "crash", gitignore_docs=True)
    write_facts(root)
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "plan_readiness.py").write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "sys.stdout.write(\n"
        "    'Traceback (most recent call last):\\n'\n"
        "    '  File \"plan_readiness.py\", line 1\\n'\n"
        "    'ValueError: stub exploded\\n'\n"
        ")\n"
        "sys.stderr.write('readiness error: plan_readiness.py cannot import facts\\n')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    plan = "docs/history/plans/2026-09-20-crashing-plan.md"
    (root / "docs" / "history" / "plans").mkdir(parents=True)
    (root / plan).write_text("p\n", encoding="utf-8")
    write_deliverables(root, [plan])

    result = run_gate("plan-readiness", ctx_for(root))

    assert result.rc == 1
    assert "Traceback (most recent call last)" not in result.message
    assert "readiness error: plan_readiness.py cannot import facts" in result.message


# --------------------------------------------------------------------------- #
# Defect fix (Task 2 blocking defect): doc-registry check-writes --stdin arm.
# --------------------------------------------------------------------------- #
def test_doc_registry_check_writes_stdin_dirty_repo(tmp_path, sweep_env, monkeypatch):
    """[class: REPOSITORY_TEST] Given a dirty fixture repo (one modified
    tracked file, untracked files, and a staged rename) and a stub doc-registry
    validator in strict typed-row mode: the gate's check-writes arm feeds the
    sorted changed-row union VERBATIM on stdin: porcelain rows keep their
    ``XY PATH`` status letters and the rename keeps its ``R  old -> new``
    shape (both sides gated by parse_change_line); a type-strip regression
    (bare rows) fails the stub. With the stub flagging, the gate fails naming
    the flagged row."""
    # Arm 1: validator accepts the changed rows; stdin content is asserted.
    root = make_repo(tmp_path, "docreg-dirty", gitignore_docs=True)
    write_facts(root)
    (root / "README.md").write_text("modified tracked file\n", encoding="utf-8")
    (root / "note.txt").write_text("untracked file\n", encoding="utf-8")
    (root / "old-name.txt").write_text("rename source\n", encoding="utf-8")
    git(root, "add", "old-name.txt")
    git(root, "commit", "-m", "rename source", "-q")
    git(root, "mv", "old-name.txt", "renamed-file.txt")
    write_stub_doc_registry_validator(root)
    stdin_log = tmp_path / "docreg-dirty-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.setenv("DOC_REGISTRY_STUB_REJECT_BARE", "1")
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)

    registry = run_gate("doc-registry", ctx_for(root))

    assert registry.rc == 0
    # Typed rows reach stdin verbatim, sorted by code point: the unstaged
    # edit keeps its worktree status letter, untracked rows keep `??`, and
    # the staged rename keeps the porcelain `R  old -> new` shape (the union
    # is line-based, so the rename row counts once). Ignored rows would be
    # bare; this fixture has none, and the stub rejects bare rows.
    expected_union = [
        " M README.md",
        "?? .ai-playbook/facts.md",
        "?? note.txt",
        "?? scripts/doc_registry_validator.py",
        "R  old-name.txt -> renamed-file.txt",
    ]
    assert stdin_log.read_text(encoding="utf-8").splitlines() == expected_union
    assert "check-writes ok over 5 changed paths" in registry.message
    assert "validate ok" in registry.message

    # Arm 2: validator flags a protected write; the gate fails with the rows.
    root2 = make_repo(tmp_path, "docreg-flag", gitignore_docs=True)
    write_facts(root2)
    (root2 / "README.md").write_text("modified tracked file\n", encoding="utf-8")
    write_stub_doc_registry_validator(root2)
    stdin_log2 = tmp_path / "docreg-flag-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log2))
    monkeypatch.setenv("DOC_REGISTRY_STUB_REJECT_BARE", "1")
    monkeypatch.setenv("DOC_REGISTRY_STUB_FLAG", "1")

    flagged = run_gate("doc-registry", ctx_for(root2))

    assert flagged.rc == 1
    assert "check-writes flagged protected writes" in flagged.message
    assert "protected write blocked by stub" in flagged.message
    # The failing arm received the typed row list on stdin too.
    assert stdin_log2.read_text(encoding="utf-8").splitlines() == [
        " M README.md",
        "?? .ai-playbook/facts.md",
        "?? scripts/doc_registry_validator.py",
    ]


def test_doc_registry_name_status_committed_in_session(tmp_path, sweep_env, monkeypatch):
    """[class: REPOSITORY_TEST] With ORIG_HEAD as the no-manifest committed-
    changes base and a commit landed after it: the committed-in-session file
    reaches check-writes stdin as a typed name-status row (``A<TAB>path``)
    alongside the typed porcelain rows; a bare downgrade of the same path
    never appears. The retired shared baseline file is neither consulted (its
    content names HEAD, so reading it would suppress the committed row) nor
    rewritten by the gate pass."""
    root = make_repo(tmp_path, "docreg-committed", gitignore_docs=True)
    write_facts(root)
    write_stub_doc_registry_validator(root)
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True)
    prior_head = git(root, "rev-parse", "HEAD").stdout.strip()
    # Committed after the ORIG_HEAD boundary: name-status `A` row.
    (root / "committed-in-session.md").write_text("new\n", encoding="utf-8")
    git(root, "add", "committed-in-session.md")
    git(root, "commit", "-m", "land in session", "-q")
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "update-ref", "ORIG_HEAD", prior_head)
    # The retired baseline names HEAD: if any branch still read it, the
    # committed row below would vanish; it must also never be rewritten.
    retired = done_session / "session-start-head.txt"
    retired.write_text(head + "\n", encoding="utf-8")
    # Uncommitted edit: porcelain ` M` row.
    (root / "README.md").write_text("modified tracked file\n", encoding="utf-8")

    stdin_log = tmp_path / "docreg-committed-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    # Bare rows ARE tolerated here: the ignored-matching arm contributes the
    # gitignored retired baseline file as a bare row (it has no change type).
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    # The committed-in-session file arrives with its change type, never bare.
    assert "A\tcommitted-in-session.md" in rows
    assert " M README.md" in rows
    assert "?? scripts/doc_registry_validator.py" in rows
    assert "committed-in-session.md" not in rows
    assert "check-writes ok over 5 changed paths" in result.message
    # Retirement: neither read (the committed row above only appears because
    # the gate used ORIG_HEAD) nor written (byte-identical after the run).
    assert retired.read_text(encoding="utf-8") == head + "\n"


def test_doc_registry_ignores_unchanged_ignored_history(tmp_path, sweep_env, monkeypatch):
    """[class: REPOSITORY_TEST] An ignored completed-history file whose
    modification time predates the anchored done session is not fed to the
    write gate, while the current ignored artifacts remain eligible."""
    root = make_repo(tmp_path, "docreg-ignored-history", gitignore_docs=True)
    write_facts(root)
    write_stub_doc_registry_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())

    completed = root / "docs" / "history" / "plans" / "completed"
    completed.mkdir(parents=True)
    frozen = completed / "unchanged.md"
    frozen.write_text("completed history\n", encoding="utf-8")
    old = now - 7200
    os.utime(frozen, (old, old))

    stdin_log = tmp_path / "docreg-ignored-history-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    assert "docs/history/plans/completed/unchanged.md" not in rows


# --------------------------------------------------------------------------- #
# Plan checkbox: test_sensitive_data_scan_push_range_audit
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def _repo_with_upstream(tmp_path: Path, name: str) -> Path:
    origin = tmp_path / (name + "-origin.git")
    origin.mkdir()
    git(origin, "init", "--bare", "-b", "main")
    root = make_repo(tmp_path, name, gitignore_docs=True)
    git(root, "remote", "add", "origin", str(origin))
    git(root, "push", "-u", "origin", "main", "-q")
    return root


def test_sensitive_data_scan_push_range_audit(tmp_path, sweep_env, monkeypatch):
    """[class: REPOSITORY_TEST] A commit in the push range carrying a
    Co-authored-by: trailer fails the gate naming the offending commit and
    pattern; a second fixture with an employer-brand pattern from facts fails
    the same way."""
    # Fixture 1: trailer in the push range.
    root = _repo_with_upstream(tmp_path, "trailer", )
    write_facts(root)
    (root / "note.txt").write_text("harmless\n", encoding="utf-8")
    git(root, "add", "note.txt")
    git(root, "commit", "-m", "add note", "-m", "Co-authored-by: someone <s@e.st>", "-q")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "Co-authored-by" in result.message
    head = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    assert head in result.message

    # Fixture 2: employer-brand pattern from facts in the pushed subject.
    monkeypatch.setenv(
        "DONE_SWEEP_USER_FACTS",
        str(_user_facts_with_brand(tmp_path)),
    )
    root2 = _repo_with_upstream(tmp_path, "brand")
    write_facts(root2)
    (root2 / "doc.txt").write_text("fine\n", encoding="utf-8")
    git(root2, "add", "doc.txt")
    git(root2, "commit", "-m", "AcmeCorp internal tooling update", "-q")
    result2 = run_gate("sensitive-data-scan", ctx_for(root2))
    assert result2.rc == 1
    assert "AcmeCorp" in result2.message
    head2 = git(root2, "rev-parse", "--short", "HEAD").stdout.strip()
    assert head2 in result2.message


def _user_facts_with_brand(tmp_path: Path) -> Path:
    facts = tmp_path / "user-facts-brand.md"
    facts.write_text(
        "| `employer_brand_patterns` | `AcmeCorp` |\n", encoding="utf-8"
    )
    return facts


# --------------------------------------------------------------------------- #
# Plan checkbox: test_sensitive_data_pattern_hits  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_sensitive_data_pattern_hits(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Staged or untracked content holding a personal
    absolute path pattern fails the gate via the diff-content grep arm; clean
    content passes."""
    # Staged arm.
    root = make_repo(tmp_path, "staged-hit", gitignore_docs=True)
    write_facts(root)
    leak = root / "leak.md"
    leak.write_text("see /Users/alice/notes/todo.txt\n", encoding="utf-8")
    git(root, "add", "leak.md")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "leak.md" in result.message
    assert "/Users/" in result.message

    # Untracked arm.
    root2 = make_repo(tmp_path, "untracked-hit", gitignore_docs=True)
    write_facts(root2)
    leak2 = root2 / "leak2.md"
    leak2.write_text("path is /Users/bob/work/file.py\n", encoding="utf-8")
    result2 = run_gate("sensitive-data-scan", ctx_for(root2))
    assert result2.rc == 1
    assert "leak2.md" in result2.message

    # Clean content passes (no upstream, not the skills repo); the skipped
    # push-range audit is named in a warning line.
    root3 = make_repo(tmp_path, "clean", gitignore_docs=True)
    write_facts(root3)
    ok = root3 / "clean.md"
    ok.write_text("nothing sensitive here\n", encoding="utf-8")
    git(root3, "add", "clean.md")
    result3 = run_gate("sensitive-data-scan", ctx_for(root3))
    assert result3.rc == 0
    assert any(
        "no upstream configured" in w and "push-range" in w
        for w in result3.warnings
    )

    # Domain terms such as claim-token prose are not credentials and must not
    # block a public plan or backlog document.
    root4 = make_repo(tmp_path, "domain-terms", gitignore_docs=True)
    write_facts(root4)
    domain_terms = root4 / "plan.md"
    domain_terms.write_text(
        "Rotate the claim token and owner during handoff.\n",
        encoding="utf-8",
    )
    result4 = run_gate("sensitive-data-scan", ctx_for(root4))
    assert result4.rc == 0

    # Credential-shaped assignments remain blocked.
    root5 = make_repo(tmp_path, "credential-shaped", gitignore_docs=True)
    write_facts(root5)
    credential = root5 / "credential.md"
    credential.write_text(
        "access_" + "token: " + "abcdefghijkl\n", encoding="utf-8"
    )
    git(root5, "add", "credential.md")
    result5 = run_gate("sensitive-data-scan", ctx_for(root5))
    assert result5.rc == 1
    assert "credential.md" in result5.message


# --------------------------------------------------------------------------- #
# Plan checkbox: test_vim_swap_liveness_refusal  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def _write_swap(path: Path, pid: int) -> None:
    buf = bytearray(4096)
    buf[0:11] = b"b0VIM 9.0.1"
    struct.pack_into("<i", buf, 24, pid)
    buf[32:38] = b"tester" + b"\x00"
    buf[40:48] = b"localhost" + b"\x00"
    path.write_bytes(bytes(buf))


def test_vim_swap_liveness_refusal(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A dead-owner swap file is removed; a live-owner
    swap file is preserved and reported active (both file(1)-verified)."""
    root = make_repo(tmp_path, "swaps", gitignore_docs=True)
    write_facts(root)
    editor_dir = root / "editor"
    editor_dir.mkdir()
    doc = editor_dir / "report.md"
    doc.write_text("body\n", encoding="utf-8")

    sleeper = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)", str(doc)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    dead_proc = subprocess.Popen([sys.executable, "-c", "pass"])
    dead_proc.wait()
    try:
        live_swap = editor_dir / ".report.md.swp"
        dead_swap = editor_dir / ".gone.md.swp"
        _write_swap(live_swap, sleeper.pid)
        _write_swap(dead_swap, dead_proc.pid)

        result = run_gate("vim-swap-sweep", ctx_for(root))
        assert result.rc == 0
        assert not dead_swap.exists(), "dead-owner swap must be removed"
        assert live_swap.exists(), "live-owner swap must be preserved"
        assert "active" in result.message
        assert ".report.md.swp" in result.message
        assert "removed" in result.message
        assert ".gone.md.swp" in result.message
    finally:
        sleeper.kill()
        sleeper.wait()


# --------------------------------------------------------------------------- #
# Plan checkbox: test_docs_tmp_sweep_classification_and_marker_immunity
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_docs_tmp_sweep_classification_and_marker_immunity(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Archived-owner entries removed; protected
    review-loop scratch left in place; never-synced one-off script skipped and
    reported; exactly the markers strictly older than the previous-run anchor
    pruned (anchor and current-run markers immune)."""
    root = make_repo(tmp_path, "sweep", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    m_oldest = make_marker(root, now - 7200, os.getpid())
    m_anchor = make_marker(root, now - 3600, os.getpid())
    m_current = make_marker(root, now, os.getpid())

    plans_dir = root / "docs/history/plans"
    completed_dir = root / "docs/history/plans/completed"
    plans_dir.mkdir(parents=True)
    completed_dir.mkdir(parents=True)

    live_plan = "2026-09-20-live-plan.md"
    arch_plan = "2026-09-20-archived-plan.md"
    (plans_dir / live_plan).write_text("live\n", encoding="utf-8")
    (completed_dir / arch_plan).write_text("archived\n", encoding="utf-8")

    tmp_dir = root / "docs/tmp"
    # Active execute-plan session (plan still under plans_dir): kept.
    write_manifest(root, live_plan[:-3], fresh_iso())
    # Archived execute-plan session (plan only under completed): removed.
    arch_session = tmp_dir / "execute-plan" / arch_plan[:-3]
    arch_session.mkdir(parents=True)
    (arch_session / "manifest.md").write_text("stale\n", encoding="utf-8")
    # plan-requirements for the completed plan: removed.
    (tmp_dir / f"plan-requirements-{arch_plan[:-3]}.md").write_text(
        "req\n", encoding="utf-8"
    )
    # Protected review-loop scratch: left in place.
    loop_dir = tmp_dir / "review-loop-r1"
    loop_dir.mkdir()
    (loop_dir / "staging.md").write_text("active loop\n", encoding="utf-8")
    # Never-synced one-off script: skipped and reported.
    one_off = tmp_dir / "notes-2026-09-20.py"
    one_off.write_text("print('scratch')\n", encoding="utf-8")
    # plan-requirements for a still-live plan: kept.
    live_req = tmp_dir / f"plan-requirements-{live_plan[:-3]}.md"
    live_req.write_text("live req\n", encoding="utf-8")

    result = run_gate("docs-tmp-sweep", ctx_for(root))
    assert result.rc == 0
    assert not arch_session.exists(), "archived-owner execute-plan session removed"
    assert not (tmp_dir / f"plan-requirements-{arch_plan[:-3]}.md").exists()
    assert (tmp_dir / "execute-plan" / live_plan[:-3] / "manifest.md").exists()
    assert loop_dir.exists() and (loop_dir / "staging.md").exists()
    assert one_off.exists(), "never-synced one-off must be skipped, not deleted"
    assert "notes-2026-09-20.py" in result.message
    assert not m_oldest.exists(), "marker strictly older than the anchor pruned"
    assert m_anchor.exists(), "anchor marker immune"
    assert m_current.exists(), "current-run marker immune"
    assert live_req.exists(), "plan-requirements for a live plan must be kept"


# --------------------------------------------------------------------------- #
# Phase 3 panel fix: docs-tmp-sweep live-session arm must look under nested
# plans_dir subdirectories, not only at the direct child.
# --------------------------------------------------------------------------- #
def test_docs_tmp_sweep_live_session_nested_plan_preserved(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An execute-plan session whose plan lives in a
    subdirectory of plans_dir (docs/history/plans/deferred/<slug>.md) is a LIVE
    session: the sweep preserves it instead of treating the plan as archived
    and rmtree-ing the session."""
    root = make_repo(tmp_path, "nested-session", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    deferred_dir = root / "docs" / "history" / "plans" / "deferred"
    deferred_dir.mkdir(parents=True)
    plan_slug = "2026-09-20-nested-plan"
    (deferred_dir / (plan_slug + ".md")).write_text(
        "nested live plan\n", encoding="utf-8"
    )
    write_manifest(root, plan_slug, fresh_iso())

    result = run_gate("docs-tmp-sweep", ctx_for(root))

    assert result.rc == 0
    session = root / "docs" / "tmp" / "execute-plan" / plan_slug
    assert session.exists(), "session with a nested live plan must be preserved"
    assert (session / "manifest.md").exists()


# --------------------------------------------------------------------------- #
# Phase 3 panel fix: a synced one-off must also be OUTSIDE the session window
# before removal (conservative when the window is unanchorable).
# --------------------------------------------------------------------------- #
def _add_docs_branch_files(root: Path, files: dict[str, str]) -> None:
    """Create ``refs/heads/docs`` whose root tree contains exactly the given
    rel->body files in ONE commit (plumbing only; the worktree and the index
    stay untouched)."""
    def run(args: list[str], text: str = "") -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            input=text,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        return proc.stdout.strip()

    tree_spec: dict = {}
    for rel, body in files.items():
        parts = rel.split("/")
        node = tree_spec
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = ("blob", run(["hash-object", "-w", "--stdin"], body))

    def build(spec: dict) -> str:
        lines = []
        for name, value in spec.items():
            if isinstance(value, tuple):
                lines.append(f"100644 blob {value[1]}\t{name}\n")
            else:
                lines.append(f"040000 tree {build(value)}\t{name}\n")
        return run(["mktree"], "".join(lines))

    root_tree = build(tree_spec)
    commit = run(["commit-tree", root_tree, "-m", "docs sync"])
    run(["update-ref", "refs/heads/docs", commit])


def test_docs_tmp_sweep_synced_one_off_session_window_guard(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A one-off scratch file already synced to the
    docs branch but modified inside the session window is skipped and reported
    (never removed this session); the same shape last touched before the
    window is removed."""
    root = make_repo(tmp_path, "oneoff-window", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    _add_docs_branch_files(
        root,
        {
            "docs/tmp/stale-synced-2026-09-19.py": "print('stale')\n",
            "docs/tmp/fresh-synced-2026-09-19.py": "print('fresh')\n",
        },
    )
    tmp_dir = root / "docs" / "tmp"
    stale = tmp_dir / "stale-synced-2026-09-19.py"
    fresh = tmp_dir / "fresh-synced-2026-09-19.py"
    stale.write_text("print('stale')\n", encoding="utf-8")
    fresh.write_text("print('fresh')\n", encoding="utf-8")
    old_t = now - 7200  # strictly before the window anchor (now - 3600)
    os.utime(stale, (old_t, old_t))

    result = run_gate("docs-tmp-sweep", ctx_for(root))

    assert result.rc == 0
    assert not stale.exists(), (
        "synced one-off untouched since before the window is removed"
    )
    assert fresh.exists(), (
        "synced one-off modified inside the session window must be skipped"
    )
    assert "fresh-synced-2026-09-19.py" in result.message
    assert "session window" in result.message


# --------------------------------------------------------------------------- #
# Plan checkbox: test_confluence_run_when_gating  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_confluence_run_when_gating(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] No manifest, no confluence-path touches, no
    ephemeral snapshots: the gate no-ops rc 0. Given an ephemeral
    *-cf-out.md, audit-cf-out runs and a NEEDS_UPGRADE classification fails
    the gate."""
    root = make_repo(tmp_path, "cf-noop", gitignore_docs=True)
    write_facts(root)
    result = run_gate("confluence-hygiene", ctx_for(root))
    assert result.rc == 0
    assert "no-op" in result.message

    # Trigger arm: ephemeral snapshot whose content is not in the mirror.
    root2 = make_repo(tmp_path, "cf-needs-upgrade", gitignore_docs=True)
    write_facts(root2)
    copy_hygiene_script(root2)
    maint = root2 / "docs/maintenance"
    maint.mkdir(parents=True)
    manifest = maint / "confluence-sync-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "111",
                        "slug": "foo",
                        "local_path": "docs/history/context/confluence/111-foo.md",
                        "layer2_targets": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    mirror = root2 / "docs/history/context/confluence/111-foo.md"
    mirror.parent.mkdir(parents=True)
    mirror.write_text("mirror body\n", encoding="utf-8")
    snap = root2 / "docs/tmp/foo-cf-out.md"
    snap.parent.mkdir(parents=True)
    snap.write_text("# Snap\n\n## Unmerged Section\n\nsnapshot only\n", encoding="utf-8")

    result2 = run_gate("confluence-hygiene", ctx_for(root2))
    assert result2.rc == 1
    assert "audit-cf-out" in result2.message
    assert "NEEDS_UPGRADE" in result2.message


# --------------------------------------------------------------------------- #
# Plan checkbox: test_session_window_and_staging_candidate_derivations
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_session_window_digest_markers(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] done Step 0's current marker format records a
    64-hex sha256 digest of the trailing-slash-stripped resolved repo root in
    the middle field; digest-format markers anchor the session window exactly
    like legacy raw-path markers, and a foreign digest marker is classified
    cross-repo rather than malformed."""
    root = make_repo(tmp_path, "window-digest", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(str(root).rstrip("/").encode("utf-8")).hexdigest()
    prev = done_session / marker_name(now - 3600)
    current = done_session / marker_name(now)
    prev.write_text(f"{int(now - 3600)} {digest} {os.getpid()}\n", encoding="utf-8")
    current.write_text(f"{int(now)} {digest} {os.getpid()}\n", encoding="utf-8")
    foreign = done_session / marker_name(now - 7200)
    foreign_digest = hashlib.sha256(b"/elsewhere/repo").hexdigest()
    foreign.write_text(f"{int(now - 7200)} {foreign_digest} 1\n", encoding="utf-8")

    ctx = ctx_for(root)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    assert window.anchored
    assert window.anchor.path == prev
    assert window.current.path == current
    assert window.start_epoch == pytest.approx(now - 3600, abs=2)

    # Foreign digest marker plus one own marker: unanchorable, and the
    # foreign marker is classified cross-repo (not malformed) via its digest.
    os.remove(current)
    window2 = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    assert not window2.anchored
    assert any("cross-repo" in note for note in window2.notes)
    assert not any("unparseable" in note for note in window2.notes)


def test_session_window_and_staging_candidate_derivations(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] The session window anchors on the previous-run
    marker (content-confirmed repo root), the current-run marker is immune; a
    gitignored staging doc inside the window is a review-staging candidate and
    one outside it is not, via the porcelain plus ignored-matching arms filtered
    by the validator's staging-path predicate."""
    root = make_repo(tmp_path, "window", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    prev = make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())

    ctx = ctx_for(root)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    assert window.anchored
    assert window.anchor.path == prev
    assert window.current.path == current
    assert window.anchor.repo_root == str(root)
    assert window.start_epoch == pytest.approx(now - 3600, abs=2)

    reviews = root / "docs/reviews"
    reviews.mkdir(parents=True)
    in_window = reviews / "2026-09-21-branch-review-r1.md"
    out_window = reviews / "2026-09-19-branch-review-r1.md"
    in_window.write_text("staging\n", encoding="utf-8")
    out_window.write_text("staging\n", encoding="utf-8")
    old_t = now - 86400
    os.utime(out_window, (old_t, old_t))
    # Tracked (force-added) staging doc, modified now: porcelain arm.
    tracked = reviews / "2026-09-21-plan-review-r1.md"
    tracked.write_text("staging\n", encoding="utf-8")
    git(root, "add", "-f", str(tracked))
    git(root, "commit", "-m", "staging", "-q")
    tracked.write_text("staging edited\n", encoding="utf-8")

    candidates = derive_review_staging_candidates(ctx)
    names = sorted(str(p) for p in candidates)
    assert str(in_window) in names
    assert str(tracked) in names
    assert str(out_window) not in names
    assert len(names) == 2


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
# Task 1: run manifest model, loader, and writer CLI.
# --------------------------------------------------------------------------- #
def _seed_run_manifest(
    root: Path,
    run_id: str,
    marker_name_str: str,
    repo_root: str,
    created_epoch: float,
    start_commit: str | None = None,
    start_porcelain: list[str] | None = None,
    owned_paths: list[str] | None = None,
    owned_plan_paths: list[str] | None = None,
    owned_review_paths: list[str] | None = None,
    foreign_review_paths: list[str] | None = None,
    adopted_from: str | None = None,
    complete: bool = False,
    dispositioned: dict | None = None,
) -> Path:
    """Seed one run-manifest JSON through the lib's own model so loader tests
    exercise the real serialization shape. ``start_commit`` defaults to the
    current HEAD; ``start_porcelain`` defaults to an empty snapshot; the
    owned/foreign lists (including ``owned_paths``) default to empty; ``adopted_from`` defaults to null
    and ``complete`` to false (an interrupted run); ``dispositioned`` defaults
    to unset (no disposition record)."""
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    manifest = lib.RunManifest(
        schema=1,
        run_id=run_id,
        marker=marker_name_str,
        created_epoch=created_epoch,
        repo_root=repo_root,
        pid=os.getpid(),
        start_commit=start_commit if start_commit is not None else head,
        start_porcelain=list(start_porcelain or []),
        owned_paths=list(owned_paths or []),
        owned_plan_paths=list(owned_plan_paths or []),
        owned_review_paths=list(owned_review_paths or []),
        foreign_review_paths=list(foreign_review_paths or []),
        adopted_from=adopted_from,
        complete=complete,
        dispositioned=dispositioned,
    )
    return lib.write_run_manifest(
        manifest, root / "docs" / "tmp" / "done-session"
    )


def test_write_manifest_creates_atomic_v1_record(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a temp repo with two commits, an existing
    run-start marker, pre-seeded dirty paths, and owned plan/review paths,
    expects the writer to succeed and to leave a manifest JSON at
    ``{tmp_dir}/done-session/run-manifest-<run_id>.json`` with schema 1, the
    run_id echoed on stdout, marker equal to the newest marker filename,
    start_commit equal to HEAD, start_porcelain listing exactly the pre-seeded
    dirty paths with their status letters, the owned paths verbatim,
    adopted_from null, and complete false; the write goes through a temp file
    plus atomic replace in the done-session directory, with no partial file
    observable and no temp residue."""
    root = mktemp_repo("atomic")
    (root / "second.txt").write_text("second commit\n", encoding="utf-8")
    git(root, "add", "second.txt")
    git(root, "commit", "-m", "second", "-q")
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    marker = make_marker(root, time.time(), os.getpid())
    # Pre-seeded dirt: one modified tracked file, one untracked file.
    (root / "README.md").write_text("modified tracked file\n", encoding="utf-8")
    (root / "note.txt").write_text("untracked scratch\n", encoding="utf-8")
    plan = "docs/history/plans/2026-09-22-owned-plan.md"
    review_rel = "docs/reviews/2026-09-22-atomic-review-r1.md"
    (root / "docs/history/plans").mkdir(parents=True)
    (root / plan).write_text("plan body\n", encoding="utf-8")
    (root / "docs/reviews").mkdir(parents=True)
    (root / review_rel).write_text("staging review body\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    # The atomic replace is observable: exactly one same-directory rename of
    # a temp file onto the final manifest name.
    replaces: list[tuple[str, str]] = []
    real_replace = os.replace

    def spy_replace(src, dst, *call_args, **call_kwargs):
        replaces.append((str(src), str(dst)))
        return real_replace(src, dst, *call_args, **call_kwargs)

    monkeypatch.setattr(os, "replace", spy_replace)

    rc = lib.main(
        ["write-manifest", "--owned-plan", plan, "--owned-review", review_rel]
    )

    assert rc == 0
    done_session = root / "docs" / "tmp" / "done-session"
    manifests = sorted(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    manifest_path = manifests[0]
    run_id = manifest_path.name[len("run-manifest-") : -len(".json")]
    assert run_id
    out = capsys.readouterr().out
    assert str(manifest_path.resolve()) in out
    assert run_id in out
    assert len(replaces) == 1
    src, dst = replaces[0]
    assert os.path.dirname(src) == str(done_session.resolve())
    assert os.path.dirname(dst) == str(done_session.resolve())
    assert os.path.basename(dst) == manifest_path.name
    assert os.path.basename(src).endswith(".tmp")
    assert list(done_session.glob("*.tmp*")) == []

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema"] == 1
    assert payload["run_id"] == run_id
    assert payload["marker"] == marker.name
    assert payload["start_commit"] == head
    assert payload["start_porcelain"] == [" M README.md", "?? note.txt"]
    assert payload["owned_plan_paths"] == [plan]
    assert payload["owned_review_paths"] == [review_rel]
    assert payload["foreign_review_paths"] == []
    assert payload["adopted_from"] is None
    assert payload["complete"] is False
    assert payload["pid"] == os.getpid()
    assert payload["repo_root"] == root_digest(root)
    assert str(root) not in manifests[0].read_text(encoding="utf-8")
    assert isinstance(payload["created_epoch"], (int, float))


def test_write_manifest_enforces_claim_or_foreign(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a staging candidate present on disk at
    write time (predicate-matched under the reviews dir, not window-filtered:
    Step 0 is the enumeration universe) that is neither passed via
    --owned-review nor via --foreign-review, expects the writer to exit
    non-zero with a named claim-or-foreign error listing the uncovered
    candidate and to write no manifest; given the same candidate passed via
    --foreign-review, expects the writer to succeed and the manifest to record
    it under the foreign-review list."""
    root = mktemp_repo("claim")
    now = time.time()
    make_marker(root, now, os.getpid())
    review_rel = "docs/reviews/2026-09-22-peer-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    (root / review_rel).write_text("peer staging review\n", encoding="utf-8")
    # Not window-filtered: the candidate predates any window, so a windowed
    # enumeration would miss it entirely; Step 0 must still see it.
    old_t = now - 86400
    os.utime(root / review_rel, (old_t, old_t))
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    rc = lib.main(
        ["write-manifest", "--owned-plan", "docs/history/plans/2026-09-22-x.md"]
    )
    assert rc != 0
    err = capsys.readouterr().err
    assert "claim-or-foreign" in err
    assert review_rel in err
    assert list(done_session.glob("run-manifest-*.json")) == []
    assert list(done_session.glob("*.tmp*")) == []

    rc2 = lib.main(["write-manifest", "--foreign-review", review_rel])
    assert rc2 == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert payload["foreign_review_paths"] == [review_rel]


def test_write_manifest_run_ids_unique(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given two successive writer invocations in the
    same repo (the first run's boundary finalized in between, since an
    undisposed interrupted boundary refuses a new write-manifest), expects two
    distinct run_id values and two distinct manifest files, each file's
    payload run_id matching its filename."""
    root = mktemp_repo("unique")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest"]) == 0
    first = sorted(done_session.glob("run-manifest-*.json"))
    assert len(first) == 1
    id0 = first[0].name[len("run-manifest-") : -len(".json")]
    # Close the first run's boundary (the Step 6 finalize) so the second
    # write is not refused over an undisposed interrupted boundary.
    assert lib.main(["finalize-manifest", "--run-id", id0]) == 0
    assert lib.main(["write-manifest"]) == 0
    both = sorted(done_session.glob("run-manifest-*.json"))
    assert len(both) == 2
    second = [p for p in both if p != first[0]]
    assert len(second) == 1
    id1 = first[0].name[len("run-manifest-") : -len(".json")]
    id2 = second[0].name[len("run-manifest-") : -len(".json")]
    assert id1 and id2 and id1 != id2
    for path, run_id in ((first[0], id1), (second[0], id2)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["run_id"] == run_id


def test_load_run_manifest_matches_newest_marker(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given two manifests whose marker fields name
    the two run-start markers, expects the loader to return only the manifest
    naming the newest content-confirmed marker."""
    root = mktemp_repo("loader-newest")
    now = time.time()
    old_marker = make_marker(root, now - 3600, os.getpid())
    new_marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, "run-old", old_marker.name, str(root), now - 10)
    _seed_run_manifest(root, "run-new", new_marker.name, str(root), now)

    ctx = ctx_for(root)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    assert window.anchored
    loaded = lib.load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    assert loaded is not None
    assert loaded.run_id == "run-new"
    assert loaded.marker == new_marker.name


def test_load_run_manifest_rejects_foreign_repo_root(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a manifest whose repo_root records a
    different path, expects the loader to return None and never raise."""
    root = mktemp_repo("loader-foreign")
    marker = make_marker(root, time.time(), os.getpid())
    _seed_run_manifest(
        root, "run-foreign", marker.name, str(tmp_path / "other-repo"), time.time()
    )

    ctx = ctx_for(root)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    loaded = lib.load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    assert loaded is None


def test_load_run_manifest_returns_none_when_absent(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a done-session dir with markers but no
    manifest, expects the loader to return None."""
    root = mktemp_repo("loader-absent")
    make_marker(root, time.time(), os.getpid())

    ctx = ctx_for(root)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    assert lib.load_run_manifest(ctx.done_session_dir, ctx.repo_root, window) is None


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
# Task 3: doc-registry gate consumes the manifest; shared baseline retired.
# --------------------------------------------------------------------------- #
def test_doc_registry_baseline_is_manifest_start_commit(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a repo where HEAD advanced twice after
    the manifest was written and a stale shared baseline file naming an older
    commit, expects the gate's committed-since set to cover exactly
    ``manifest.start_commit..HEAD``, to stay green when those commits touch no
    registered path, and to carry a pre-existing-dirt report line naming each
    ``start_porcelain`` path (the snapshot's one consumer: pre-session dirt is
    reported, never attributed to this run), so the stale baseline can no
    longer widen the checked set."""
    root = mktemp_repo("baseline")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    # The commit the boundary sits on: its file resurfaces in the union only
    # if the stale baseline widens the checked range.
    (root / "pre-boundary.md").write_text("before the manifest\n", encoding="utf-8")
    git(root, "add", "pre-boundary.md")
    git(root, "commit", "-m", "pre boundary", "-q")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    init = git(root, "rev-parse", "HEAD~1").stdout.strip()
    # Pre-existing dirt at Step 0: one modified tracked file, one untracked.
    (root / "README.md").write_text("modified tracked file\n", encoding="utf-8")
    (root / "scratch.txt").write_text("pre-existing untracked\n", encoding="utf-8")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root,
        "run-baseline",
        current.name,
        str(root),
        now,
        start_commit=start,
        start_porcelain=[" M README.md", "?? scratch.txt"],
    )
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / "session-start-head.txt").write_text(init + "\n", encoding="utf-8")
    # HEAD advances twice after the manifest; both commits are ledger-owned.
    (root / "owned-one.md").write_text("one\n", encoding="utf-8")
    git(root, "add", "owned-one.md")
    git(root, "commit", "-m", "owned one", "-q")
    owned_one = git(root, "rev-parse", "HEAD").stdout.strip()
    (root / "owned-two.md").write_text("two\n", encoding="utf-8")
    git(root, "add", "owned-two.md")
    git(root, "commit", "-m", "owned two", "-q")
    owned_two = git(root, "rev-parse", "HEAD").stdout.strip()
    (done_session / "owned-commits-run-baseline.txt").write_text(
        owned_one + "\n" + owned_two + "\n", encoding="utf-8"
    )

    stdin_log = tmp_path / "baseline-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    committed = [row for row in rows if "\t" in row]
    assert committed == ["A\towned-one.md", "A\towned-two.md"]
    assert "A\tpre-boundary.md" not in rows
    assert any(
        "pre-existing dirt" in warning
        and " M README.md" in warning
        and "?? scratch.txt" in warning
        for warning in result.warnings
    )


def test_doc_registry_foreign_commit_excluded_and_reported(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given ``start_commit..HEAD`` containing one
    ledger-listed commit touching a registered path and one unlisted commit
    touching a registered path, expects the check-writes union to contain only
    the owned commit's path and the report to carry a foreign line naming the
    unlisted sha (foreign artifacts are preserved and reported, never gate
    failures)."""
    root = mktemp_repo("foreign-commit")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    (root / "boundary.md").write_text("boundary\n", encoding="utf-8")
    git(root, "add", "boundary.md")
    git(root, "commit", "-m", "boundary", "-q")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root, "run-foreign", current.name, str(root), now, start_commit=start
    )
    (root / "owned-doc.md").write_text("owned\n", encoding="utf-8")
    git(root, "add", "owned-doc.md")
    git(root, "commit", "-m", "owned doc", "-q")
    owned_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    (root / "foreign-doc.md").write_text("foreign\n", encoding="utf-8")
    git(root, "add", "foreign-doc.md")
    git(root, "commit", "-m", "foreign doc", "-q")
    foreign_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / "owned-commits-run-foreign.txt").write_text(
        owned_sha + "\n", encoding="utf-8"
    )

    stdin_log = tmp_path / "foreign-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    assert [row for row in rows if "\t" in row] == ["A\towned-doc.md"]
    assert "A\tforeign-doc.md" not in rows
    reported = result.message + "\n".join(result.warnings)
    assert "foreign" in reported
    assert foreign_sha in reported
    assert owned_sha not in reported


def test_doc_registry_stale_ledger_entry_skipped(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a ledger sha not reachable from HEAD
    (committed once, then reset away), expects a stale-entry report line
    naming the sha and no gate failure, while the reachable ledger commit
    stays owned and its committed row reaches the validator."""
    root = mktemp_repo("stale-ledger")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    (root / "boundary.md").write_text("boundary\n", encoding="utf-8")
    git(root, "add", "boundary.md")
    git(root, "commit", "-m", "boundary", "-q")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root, "run-stale", current.name, str(root), now, start_commit=start
    )
    # A commit the ledger records before it is reset away: unreachable.
    (root / "gone.md").write_text("gone\n", encoding="utf-8")
    git(root, "add", "gone.md")
    git(root, "commit", "-m", "later reset away", "-q")
    stale_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "reset", "--hard", "HEAD~1")
    (root / "kept.md").write_text("kept\n", encoding="utf-8")
    git(root, "add", "kept.md")
    git(root, "commit", "-m", "kept", "-q")
    kept_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / "owned-commits-run-stale.txt").write_text(
        stale_sha + "\n" + kept_sha + "\n", encoding="utf-8"
    )

    stdin_log = tmp_path / "stale-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    assert [row for row in rows if "\t" in row] == ["A\tkept.md"]
    assert "A\tgone.md" not in rows
    assert any(
        "stale" in warning and stale_sha in warning for warning in result.warnings
    )
    assert not any("foreign" in warning for warning in result.warnings)


def test_doc_registry_merge_commit_rows_reach_validator(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a real merge commit reachable inside the
    window whose ledger records the merge sha only (the branch tip commits
    stay unlisted), expects the merge's changed paths to appear in the
    check-writes rows: the per-owned-commit probe must not emit zero rows for
    a merge and silently narrow the validation surface."""
    root = mktemp_repo("merge-rows")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    (root / "boundary.md").write_text("boundary\n", encoding="utf-8")
    git(root, "add", "boundary.md")
    git(root, "commit", "-m", "boundary", "-q")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root, "run-merge", current.name, str(root), now, start_commit=start
    )
    # Branch off, commit a merge-side path, advance mainline, then merge back
    # with a real merge commit: without -m the owned-commit probe emits
    # nothing for the merge and both rows drop out of the check.
    git(root, "checkout", "-b", "side")
    (root / "merge-side.md").write_text("side\n", encoding="utf-8")
    git(root, "add", "merge-side.md")
    git(root, "commit", "-m", "side", "-q")
    git(root, "checkout", "-")
    (root / "mainline.md").write_text("mainline\n", encoding="utf-8")
    git(root, "add", "mainline.md")
    git(root, "commit", "-m", "mainline", "-q")
    git(root, "merge", "--no-ff", "--no-edit", "side")
    assert git(root, "rev-parse", "HEAD^2").returncode == 0  # a real merge
    merge_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / "owned-commits-run-merge.txt").write_text(
        merge_sha + "\n", encoding="utf-8"
    )

    stdin_log = tmp_path / "merge-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    committed = {row for row in rows if "\t" in row}
    assert committed == {"A\tmerge-side.md", "A\tmainline.md"}


def test_doc_registry_rev_list_failure_falls_back_conservatively(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a manifest whose ``start_commit`` is a
    corrupt (unresolvable) sha so ``rev-list base..HEAD`` fails, expects the
    committed arm to keep the conservative inclusion instead of being
    silently dropped: the post-manifest committed row still reaches the
    validator, the conservative over-inclusion keeps the pre-boundary
    committed row too (no owned/foreign narrowing ran, so no foreign report
    line appears), and the warnings carry the rev-list-failure fallback
    report line naming the base."""
    root = mktemp_repo("revlist-fallback")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    (root / "boundary.md").write_text("boundary\n", encoding="utf-8")
    git(root, "add", "boundary.md")
    git(root, "commit", "-m", "boundary", "-q")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    # Corrupt the recorded start_commit: same shape, no such object.
    corrupt = start[:-1] + ("0" if start[-1] != "0" else "1")
    assert corrupt != start
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root, "run-revlist", current.name, str(root), now, start_commit=corrupt
    )
    # HEAD advances after the manifest; the commit is ledger-owned.
    (root / "owned-doc.md").write_text("owned\n", encoding="utf-8")
    git(root, "add", "owned-doc.md")
    git(root, "commit", "-m", "owned doc", "-q")
    owned_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / "owned-commits-run-revlist.txt").write_text(
        owned_sha + "\n", encoding="utf-8"
    )

    stdin_log = tmp_path / "revlist-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    # Never an empty committed arm: the owned commit's row is checked even
    # though the window itself was unreadable.
    assert "A\towned-doc.md" in rows
    # Conservative over-inclusion, not classification: the pre-boundary row
    # is checked too (the fallback never narrows to owned rows).
    assert "A\tboundary.md" in rows
    # The fallback is reported, never silent.
    assert any(
        "rev-list failed" in warning and corrupt in warning
        for warning in result.warnings
    )
    # No owned/foreign classification ran on the git failure.
    assert not any("foreign" in warning for warning in result.warnings)


def test_doc_registry_unreadable_ledger_falls_back_conservatively(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given the active run's ledger file exists but
    is unreadable at gate time (chmod 000, so the read raises OSError),
    expects the conservative inclusion instead of a classification against a
    partial ownership record: the run's own ledger-claimed committed row and
    the unlisted window commit's row both still reach the validator (never a
    foreign exclusion of claimed paths), and the warnings carry an
    unreadable-ledger line naming the ledger path."""
    root = mktemp_repo("unreadable-ledger")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    (root / "boundary.md").write_text("boundary\n", encoding="utf-8")
    git(root, "add", "boundary.md")
    git(root, "commit", "-m", "boundary", "-q")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root, "run-unreadable", current.name, str(root), now, start_commit=start
    )
    # HEAD advances after the manifest; the commit is ledger-owned.
    (root / "owned-doc.md").write_text("owned\n", encoding="utf-8")
    git(root, "add", "owned-doc.md")
    git(root, "commit", "-m", "owned doc", "-q")
    owned_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    # An unlisted window commit: with a readable ledger it would classify as
    # foreign and be excluded, so its presence pins that no classification
    # ran against the partial ownership record.
    (root / "unlisted-doc.md").write_text("unlisted\n", encoding="utf-8")
    git(root, "add", "unlisted-doc.md")
    git(root, "commit", "-m", "unlisted doc", "-q")
    done_session = root / "docs" / "tmp" / "done-session"
    ledger = done_session / "owned-commits-run-unreadable.txt"
    ledger.write_text(owned_sha + "\n", encoding="utf-8")
    # The run's own ledger becomes unreadable at gate time (the plan's
    # conservative-inclusion edge case): an unreadable record must never be
    # treated as an empty one, which would reclassify the run's own commits
    # as foreign and exclude their paths from the check-write union.
    ledger.chmod(0o000)

    stdin_log = tmp_path / "unreadable-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    try:
        result = run_gate("doc-registry", ctx_for(root))
    finally:
        ledger.chmod(0o644)

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    # Conservative inclusion, never foreign narrowing: the ledger-claimed
    # commit stays checked even though its ownership record is unreadable,
    # and the unlisted commit is over-included instead of classified.
    assert "A\towned-doc.md" in rows
    assert "A\tunlisted-doc.md" in rows
    # The fallback is reported, never silent, naming the unreadable ledger.
    assert any(
        "unreadable" in warning and str(ledger) in warning
        for warning in result.warnings
    )
    # No owned/foreign classification ran on the unreadable ledger.
    assert not any(
        "foreign commit excluded" in warning for warning in result.warnings
    )


def test_doc_registry_no_manifest_keeps_legacy_behavior(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given no manifest, expects the gate to use
    ``ORIG_HEAD`` as the committed-changes base and the window-anchored
    ignored arm, matching today's characterization; the retired shared
    baseline file is neither consulted (its stale content cannot suppress the
    committed row) nor rewritten, and an unanchorable window keeps the
    conservative all-ignored inclusion."""
    # Arm 1: anchored window, ORIG_HEAD base, retired file present but inert.
    root = mktemp_repo("legacy")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    prior_head = git(root, "rev-parse", "HEAD").stdout.strip()
    (root / "legacy-committed.md").write_text("committed\n", encoding="utf-8")
    git(root, "add", "legacy-committed.md")
    git(root, "commit", "-m", "legacy commit", "-q")
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "update-ref", "ORIG_HEAD", prior_head)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    completed = root / "docs" / "history" / "plans" / "completed"
    completed.mkdir(parents=True)
    frozen = completed / "pre-window.md"
    frozen.write_text("old ignored history\n", encoding="utf-8")
    old_t = now - 7200
    os.utime(frozen, (old_t, old_t))
    done_session = root / "docs" / "tmp" / "done-session"
    retired = done_session / "session-start-head.txt"
    retired.write_text(head + "\n", encoding="utf-8")

    stdin_log = tmp_path / "legacy-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    # ORIG_HEAD is the base: the committed row reaches the validator even
    # though the retired file names HEAD (if any branch still read it, the
    # row would vanish).
    assert "A\tlegacy-committed.md" in rows
    # Window-anchored ignored arm: the pre-window ignored file stays out.
    assert "docs/history/plans/completed/pre-window.md" not in rows
    # Retirement: the file is never rewritten (byte-identical after the run).
    assert retired.read_text(encoding="utf-8") == head + "\n"

    # Arm 2: unanchorable window (one marker) keeps the conservative
    # all-ignored inclusion.
    root2 = mktemp_repo("legacy-conservative")
    write_facts(root2)
    write_stub_doc_registry_validator(root2)
    make_marker(root2, time.time(), os.getpid())
    completed2 = root2 / "docs" / "history" / "plans" / "completed"
    completed2.mkdir(parents=True)
    old2 = completed2 / "old-ignored.md"
    old2.write_text("old ignored\n", encoding="utf-8")
    os.utime(old2, (now - 86400, now - 86400))
    stdin_log2 = tmp_path / "legacy-conservative-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log2))

    result2 = run_gate("doc-registry", ctx_for(root2))

    assert result2.rc == 0
    rows2 = stdin_log2.read_text(encoding="utf-8").splitlines()
    assert "docs/history/plans/completed/old-ignored.md" in rows2


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
# Task 4: review-staging and ignored-path ownership scoping.
# --------------------------------------------------------------------------- #
def write_stub_review_staging_validator(root: Path) -> Path:
    """Repo-local stub review-staging validator (subprocess seam).

    Appends each validated target to ``REVIEW_STAGING_STUB_LOG`` (one path per
    line, invocation record) then exits 1 with a named finding when the
    target's basename contains ``invalid``, else 0.
    """
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    stub = scripts / "validate_review_staging.py"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "import sys\n"
        "target = sys.argv[-1]\n"
        "log = os.environ.get('REVIEW_STAGING_STUB_LOG', '')\n"
        "if log:\n"
        "    with open(log, 'a', encoding='utf-8') as fh:\n"
        "        fh.write(target + '\\n')\n"
        "if 'invalid' in os.path.basename(target):\n"
        "    print('HARD: staging metadata invalid (stub finding): ' + target)\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    return stub


def test_review_staging_unseen_candidate_reported_foreign(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a manifest and a staging candidate
    created after Step 0 that the manifest neither claims nor lists as
    foreign, expects the gate to report the path as foreign with an
    unseen-since-Step-0 note, to preserve the file byte-identical, and to keep
    the run's outcome driven only by its own claimed artifacts (the unclaimed
    doc carries invalid staging metadata yet the gate stays green because it
    is never validated as this run's own)."""
    root = mktemp_repo("unseen")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    owned_rel = "docs/reviews/2026-09-22-own-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    (root / owned_rel).write_text("owned staging review\n", encoding="utf-8")
    _seed_run_manifest(
        root,
        "run-unseen",
        current.name,
        str(root),
        now,
        owned_review_paths=[owned_rel],
    )
    # The peer's doc appears after Step 0: unseen by the manifest, invalid
    # staging metadata, inside the window (so the legacy window arm would
    # have validated it as this run's own and failed the run).
    unseen_rel = "docs/reviews/2026-09-22-peer-invalid-review-r1.md"
    unseen_payload = "peer staging review with deliberately invalid metadata\n"
    (root / unseen_rel).write_text(unseen_payload, encoding="utf-8")
    stub_log = tmp_path / "unseen-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0
    reported = result.message + "\n".join(result.warnings)
    assert "foreign" in reported
    assert unseen_rel in reported
    assert "unseen since Step 0" in reported
    assert (root / unseen_rel).read_text(encoding="utf-8") == unseen_payload
    invocations = stub_log.read_text(encoding="utf-8")
    assert owned_rel in invocations
    assert unseen_rel not in invocations


def test_review_staging_vanished_owned_review_reported(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a manifest claiming a review path that
    no longer exists on disk at gate time, expects a named vanish report line
    for that path and a green gate (a deleted review is reported, never
    silently skipped and never a failure)."""
    root = mktemp_repo("vanished")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    (root / "docs/reviews").mkdir(parents=True)
    gone_rel = "docs/reviews/2026-09-21-gone-review-r1.md"
    (root / gone_rel).write_text("deleted after Step 0\n", encoding="utf-8")
    (root / gone_rel).unlink()
    _seed_run_manifest(
        root,
        "run-vanished",
        current.name,
        str(root),
        now,
        owned_review_paths=[gone_rel],
    )

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0
    reported = result.message + "\n".join(result.warnings)
    assert "vanished" in reported
    assert gone_rel in reported


def test_review_staging_validates_owned_and_reports_foreign(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a manifest claiming one valid staging
    review and a foreign-marked ignored staging doc with deliberately invalid
    staging metadata, expects the gate result green for the run's own review,
    a foreign report line naming the unclaimed path with the peer-artifact
    owner class, and the unclaimed file preserved byte-identical on disk (and
    never handed to the validator)."""
    root = mktemp_repo("foreign-doc")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    owned_rel = "docs/reviews/2026-09-22-own-review-r1.md"
    foreign_rel = "docs/reviews/2026-09-19-invalid-peer-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    (root / owned_rel).write_text("owned staging review\n", encoding="utf-8")
    foreign_payload = "peer staging review with deliberately invalid metadata\n"
    (root / foreign_rel).write_text(foreign_payload, encoding="utf-8")
    # Current mtime: the legacy window arm would validate it as this run's
    # own; only the manifest's foreign marking keeps it excluded.
    _seed_run_manifest(
        root,
        "run-foreign-doc",
        current.name,
        str(root),
        now,
        owned_review_paths=[owned_rel],
        foreign_review_paths=[foreign_rel],
    )
    stub_log = tmp_path / "foreign-doc-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0
    reported = result.message + "\n".join(result.warnings)
    assert "foreign" in reported
    assert foreign_rel in reported
    assert "peer artifact" in reported
    assert (root / foreign_rel).read_text(encoding="utf-8") == foreign_payload
    invocations = stub_log.read_text(encoding="utf-8")
    assert owned_rel in invocations
    assert foreign_rel not in invocations


def test_review_staging_fail_closed_for_claimed_invalid_review(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a manifest claiming a staging review
    that fails the staging validator (and predates the session window, so
    only the manifest claim brings it into scope), expects the gate to fail
    with the validator findings, proving foreign classification never shields
    a claimed artifact."""
    root = mktemp_repo("claimed-invalid")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    claimed_rel = "docs/reviews/2026-09-18-invalid-own-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    (root / claimed_rel).write_text("own review, invalid staging metadata\n", encoding="utf-8")
    old_t = now - 86400
    os.utime(root / claimed_rel, (old_t, old_t))
    _seed_run_manifest(
        root,
        "run-claimed-invalid",
        current.name,
        str(root),
        now,
        owned_review_paths=[claimed_rel],
    )

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 1
    assert claimed_rel in result.message
    assert "failed" in result.message


def test_session_ignored_paths_stay_window_anchored_under_manifest(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a manifest plus ignored paths inside and
    outside the window, expects ``_session_ignored_paths`` to keep today's
    mtime-window behavior byte-for-byte (characterization: the doc-registry
    ignored arm is a protection surface and is never narrowed to manifest
    claims; the manifest does not touch this arm at all)."""
    root = mktemp_repo("ignored-manifest")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, "run-ignored", current.name, str(root), now)
    completed = root / "docs" / "history" / "plans" / "completed"
    completed.mkdir(parents=True)
    inside_rel = "docs/history/plans/completed/in-window.md"
    outside_rel = "docs/history/plans/completed/out-window.md"
    (root / inside_rel).write_text("touched this session\n", encoding="utf-8")
    (root / outside_rel).write_text("old ignored history\n", encoding="utf-8")
    old_t = now - 86400
    os.utime(root / outside_rel, (old_t, old_t))

    ctx = ctx_for(root)
    kept = lib._session_ignored_paths(ctx, [inside_rel, outside_rel])

    assert kept == [inside_rel]


def test_no_manifest_keeps_window_conservative_filter(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given no manifest, expects
    ``_session_ignored_paths`` to keep today's mtime-window behavior
    byte-for-byte (characterization): an anchored window filters by mtime and
    an unanchorable window retains the conservative all-ignored set."""
    # Arm 1: anchored window, no manifest anywhere.
    root = mktemp_repo("ignored-legacy")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    completed = root / "docs" / "history" / "plans" / "completed"
    completed.mkdir(parents=True)
    inside_rel = "docs/history/plans/completed/in-window.md"
    outside_rel = "docs/history/plans/completed/out-window.md"
    (root / inside_rel).write_text("touched this session\n", encoding="utf-8")
    (root / outside_rel).write_text("old ignored history\n", encoding="utf-8")
    old_t = now - 86400
    os.utime(root / outside_rel, (old_t, old_t))

    ctx = ctx_for(root)
    kept = lib._session_ignored_paths(ctx, [inside_rel, outside_rel])

    assert kept == [inside_rel]

    # Arm 2: unanchorable window (one marker) keeps everything, conservatively.
    root2 = mktemp_repo("ignored-conservative")
    make_marker(root2, time.time(), os.getpid())
    completed2 = root2 / "docs" / "history" / "plans" / "completed"
    completed2.mkdir(parents=True)
    old_rel = "docs/history/plans/completed/old-ignored.md"
    (root2 / old_rel).write_text("old ignored\n", encoding="utf-8")
    os.utime(root2 / old_rel, (now - 86400, now - 86400))

    ctx2 = ctx_for(root2)
    kept2 = lib._session_ignored_paths(ctx2, [old_rel])

    assert kept2 == [old_rel]


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
# Task 5: interrupted-run recovery and explicit adoption.
# --------------------------------------------------------------------------- #
def _newest_manifest_payload(root: Path, exclude_run_id: str | None = None) -> dict:
    """The payload of the run manifest just written (newest created_epoch,
    optionally excluding a known prior run_id)."""
    done_session = root / "docs" / "tmp" / "done-session"
    best: tuple[float, dict] | None = None
    for path in sorted(done_session.glob("run-manifest-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if exclude_run_id is not None and payload["run_id"] == exclude_run_id:
            continue
        if best is None or payload["created_epoch"] > best[0]:
            best = (payload["created_epoch"], payload)
    assert best is not None
    return best[1]


def test_write_manifest_reports_orphaned_manifests(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a done-session dir holding a prior
    manifest with ``complete`` false (never finalized), expects the next
    ``write-manifest`` invocation to print an interrupted-run report line
    naming the orphan run_id and to refuse the write with the named
    ``write-manifest: undisposed-interrupted:`` error (no manifest written
    past the refusal); a prior manifest with ``complete`` true is never
    reported as an orphan (this is what keeps a completed commit-less run
    from misfiring the detection) and never refuses."""
    # Arm 1: an unfinalized prior manifest is reported AND refuses; the
    # boundary decision stays explicit.
    root = mktemp_repo("orphan")
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-orphan-reported"
    _seed_run_manifest(root, orphan_id, prev.name, str(root), time.time() - 10)
    # HEAD advances after the orphan died: the refusal is independent of it.
    (root / "post-orphan.md").write_text("committed after the orphan died\n", encoding="utf-8")
    git(root, "add", "post-orphan.md")
    git(root, "commit", "-m", "post orphan", "-q")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest"])

    assert rc == 1
    captured = capsys.readouterr()
    assert "interrupted run" in captured.out
    assert orphan_id in captured.out
    assert "write-manifest: undisposed-interrupted:" in captured.err
    assert orphan_id in captured.err
    done_session = root / "docs" / "tmp" / "done-session"
    assert [p.name for p in done_session.glob("run-manifest-*.json")] == [
        f"run-manifest-{orphan_id}.json"
    ]

    # Arm 2: a finalized (complete=true) prior manifest is never an orphan.
    root2 = mktemp_repo("finalized")
    prev2 = make_marker(root2, time.time() - 3600, os.getpid())
    done_id = "run-already-complete"
    _seed_run_manifest(
        root2, done_id, prev2.name, str(root2), time.time() - 10, complete=True
    )
    make_marker(root2, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root2))

    rc2 = lib.main(["write-manifest"])

    assert rc2 == 0
    out2 = capsys.readouterr().out
    assert "interrupted run" not in out2
    assert done_id not in out2


def test_adopt_copies_prior_boundary(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given ``--adopt <orphan_run_id>``, expects the
    new manifest to carry the orphan's ``start_commit`` and owned paths
    verbatim and ``adopted_from`` set to the orphan run_id, and expects a third
    ``write-manifest`` invocation to no longer report the adopted run as an
    orphan (adoption is itself the suppression record)."""
    root = mktemp_repo("adopt")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-orphan-adopt"
    plan_rel = "docs/history/plans/2026-09-22-adopted-plan.md"
    review_rel = "docs/reviews/2026-09-22-adopt-review-r1.md"
    (root / review_rel).parent.mkdir(parents=True)
    (root / review_rel).write_text("orphan's staging review\n", encoding="utf-8")
    _seed_run_manifest(
        root,
        orphan_id,
        prev.name,
        str(root),
        time.time() - 10,
        start_commit=start,
        owned_plan_paths=[plan_rel],
        owned_review_paths=[review_rel],
    )
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    # No --owned-review/--foreign-review flags: the adoption itself must cover
    # the orphan's on-disk claimed review through the inherited owned set.
    rc = lib.main(["write-manifest", "--adopt", orphan_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "adopt" in out
    assert orphan_id in out
    payload = _newest_manifest_payload(root, exclude_run_id=orphan_id)
    assert payload["start_commit"] == start
    assert payload["owned_plan_paths"] == [plan_rel]
    assert payload["owned_review_paths"] == [review_rel]
    assert payload["adopted_from"] == orphan_id
    adopter_id = payload["run_id"]

    # A third invocation no longer reports the adopted run as an orphan: the
    # adopted_from link is the suppression record. The adopter's own boundary
    # closes first (the Step 6 finalize, one of the refusal's named exits),
    # since an undisposed interrupted boundary refuses a new write-manifest.
    # The unrelated third run must still cover the on-disk candidate itself
    # (peer artifact: foreign).
    assert lib.main(["finalize-manifest", "--run-id", adopter_id]) == 0
    capsys.readouterr()
    rc3 = lib.main(["write-manifest", "--foreign-review", review_rel])

    assert rc3 == 0
    out3 = capsys.readouterr().out
    assert orphan_id not in out3
    third = _newest_manifest_payload(root, exclude_run_id=orphan_id)
    assert third["run_id"] not in (orphan_id, adopter_id)
    assert third["adopted_from"] is None


def test_adoption_is_explicit_only(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given an orphan manifest and no ``--adopt``,
    expects the write-manifest invocation to be refused with the named
    ``write-manifest: undisposed-interrupted:`` error while the report line
    still surfaces the orphan (adoption stays explicit only, and the refusal
    makes the decision bounded instead of passive); with no new manifest
    written, the doc-registry gate over the same tree keeps the orphan's
    committed file out of its check-writes set (no manifest binds to the
    current marker, so nothing classifies the orphan's commit as this
    run's write)."""
    root = mktemp_repo("explicit")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-orphan-explicit"
    _seed_run_manifest(root, orphan_id, prev.name, str(root), time.time() - 10)
    # The orphan committed once, ledgered it, then died before finalizing.
    (root / "orphan-owned.md").write_text("orphan's commit\n", encoding="utf-8")
    git(root, "add", "orphan-owned.md")
    git(root, "commit", "-m", "orphan commit", "-q")
    orphan_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    assert orphan_sha != start
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / f"owned-commits-{orphan_id}.txt").write_text(
        orphan_sha + "\n", encoding="utf-8"
    )
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest"])

    assert rc == 1
    captured = capsys.readouterr()
    # Surfaced, never silently adopted: the report line names the orphan and
    # the refusal carries the bounded decision.
    assert "interrupted run" in captured.out
    assert orphan_id in captured.out
    assert "write-manifest: undisposed-interrupted:" in captured.err
    assert orphan_id in captured.err
    assert f"--adopt {orphan_id}" in captured.err
    # No manifest was written past the refusal: only the orphan remains.
    done_session_files = sorted(
        (root / "docs" / "tmp" / "done-session").glob("run-manifest-*.json")
    )
    assert [p.name for p in done_session_files] == [
        f"run-manifest-{orphan_id}.json"
    ]

    stdin_log = tmp_path / "explicit-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    committed = [row for row in rows if "\t" in row]
    assert committed == []
    assert not any(
        "foreign" in warning and orphan_sha in warning
        for warning in result.warnings
    )


def test_adopted_chain_commits_ledger_owned(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given an orphan run that committed once (its
    ledger records the sha) and died before finalizing, and an adopter that
    makes no new commits, expects the adopted retry's doc-registry
    classification to treat the orphan's commit as owned (the classification
    reads the ledgers of every run in the ``adopted_from`` chain, not only the
    adopter's)."""
    root = mktemp_repo("chain")
    write_facts(root)
    write_stub_doc_registry_validator(root)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-orphan-chain"
    adopter_id = "run-adopter-chain"
    _seed_run_manifest(root, orphan_id, prev.name, str(root), time.time() - 10)
    (root / "chain-owned.md").write_text("orphan's committed file\n", encoding="utf-8")
    git(root, "add", "chain-owned.md")
    git(root, "commit", "-m", "orphan chain commit", "-q")
    orphan_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / f"owned-commits-{orphan_id}.txt").write_text(
        orphan_sha + "\n", encoding="utf-8"
    )
    # The adopter: boundary adopted from the orphan, no new commits, and no
    # ledger of its own (it never commits).
    current = make_marker(root, time.time(), os.getpid())
    _seed_run_manifest(
        root,
        adopter_id,
        current.name,
        str(root),
        time.time(),
        start_commit=start,
        adopted_from=orphan_id,
    )

    stdin_log = tmp_path / "chain-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    rows = stdin_log.read_text(encoding="utf-8").splitlines()
    assert [row for row in rows if "\t" in row] == ["A\tchain-owned.md"]
    reported = result.message + "\n".join(result.warnings)
    assert not any(
        "foreign" in warning and orphan_sha in warning
        for warning in result.warnings
    )
    assert orphan_id in reported


def test_finalize_manifest_sets_complete(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a manifest with ``complete`` false,
    expects ``finalize-manifest --run-id <id>`` to flip it to true in place
    and to tolerate a missing manifest with an explicit not-found report,
    per the Step 6 recipe's tolerance clause (a run without a manifest skips
    finalization without failing)."""
    root = mktemp_repo("finalize")
    make_marker(root, time.time(), os.getpid())
    run_id = "run-finalize-me"
    _seed_run_manifest(root, run_id, marker_name(time.time()), str(root), time.time())
    done_session = root / "docs" / "tmp" / "done-session"
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    before = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert before["complete"] is False
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["finalize-manifest", "--run-id", run_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert run_id in out
    after = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert after["complete"] is True
    assert after["run_id"] == run_id
    assert after["start_commit"] == before["start_commit"]

    # Idempotent: finalizing a complete run is a named no-op.
    rc_again = lib.main(["finalize-manifest", "--run-id", run_id])
    assert rc_again == 0
    assert "already complete" in capsys.readouterr().out

    # Missing manifest: an explicit not-found report, zero exit (tolerance).
    rc_missing = lib.main(["finalize-manifest", "--run-id", "run-never-written"])
    assert rc_missing == 0
    out_missing = capsys.readouterr().out
    assert "run-never-written" in out_missing
    assert "no run manifest" in out_missing


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md
# Task 1: RED discrimination and behavior tests for r1 findings F1-F13.
# --------------------------------------------------------------------------- #
def test_load_run_manifest_marker_binding_beats_epoch_decoy(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] F1 decoy (regression pin, GREEN on arrival):
    given two manifests where the one naming the OLDER marker carries the
    HIGHER created_epoch, expects the loader to return only the manifest
    naming the newest content-confirmed marker (marker binding filters before
    any epoch comparison, so a high-epoch record bound to a stale marker can
    never win)."""
    root = mktemp_repo("f1-decoy")
    now = time.time()
    old_marker = make_marker(root, now - 3600, os.getpid())
    new_marker = make_marker(root, now, os.getpid())
    # The decoy: bound to the OLD marker but stamped with a far-future epoch.
    _seed_run_manifest(root, "run-decoy", old_marker.name, str(root), now + 9999)
    _seed_run_manifest(root, "run-newest", new_marker.name, str(root), now)

    ctx = ctx_for(root)
    window = derive_session_window(ctx.done_session_dir, ctx.repo_root)
    loaded = lib.load_run_manifest(ctx.done_session_dir, ctx.repo_root, window)
    assert loaded is not None
    assert loaded.run_id == "run-newest"
    assert loaded.marker == new_marker.name


def test_run_manifest_from_dict_rejects_bool_created_epoch(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] F3: a run-manifest payload whose created_epoch
    is the corrupt value ``true`` degrades to None (the documented tolerant
    parse), not to the float 1.0 (bool is an int subtype and must not coerce)."""
    root = mktemp_repo("f3-bool")
    marker = make_marker(root, time.time(), os.getpid())
    done_session = root / "docs" / "tmp" / "done-session"
    corrupt = done_session / "run-manifest-run-corrupt.json"
    payload = {
        "schema": 1,
        "run_id": "run-corrupt",
        "marker": marker.name,
        "created_epoch": True,
        "repo_root": str(root),
        "pid": os.getpid(),
        "start_commit": git(root, "rev-parse", "HEAD").stdout.strip(),
        "start_porcelain": [],
        "owned_plan_paths": [],
        "owned_review_paths": [],
        "foreign_review_paths": [],
        "adopted_from": None,
        "complete": False,
    }
    corrupt.write_text(json.dumps(payload), encoding="utf-8")
    assert lib.RunManifest.from_dict(payload) is None
    window = derive_session_window(done_session, root)
    assert lib.load_run_manifest(done_session, root, window) is None


def test_run_manifest_created_epoch_float_accepted_bool_never_coerces(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] The p79 r1-fix residual pinned at suite level:
    a float ``created_epoch`` stays accepted (the writer itself stamps
    ``time.time()``, so a float-refusing schema would reject every manifest
    the tool writes), while a bool never coerces through the int-or-float
    arm (``True`` and ``False`` both degrade to None, the F3 guard)."""
    root = mktemp_repo("epoch-float-bool")
    marker = make_marker(root, time.time(), os.getpid())
    done_session = root / "docs" / "tmp" / "done-session"

    def payload_with(created_epoch: object) -> dict:
        return {
            "schema": 1,
            "run_id": "run-epoch",
            "marker": marker.name,
            "created_epoch": created_epoch,
            "repo_root": str(root),
            "pid": os.getpid(),
            "start_commit": git(root, "rev-parse", "HEAD").stdout.strip(),
            "start_porcelain": [],
            "owned_plan_paths": [],
            "owned_review_paths": [],
            "foreign_review_paths": [],
            "adopted_from": None,
            "complete": False,
        }

    stamp = time.time()
    parsed = lib.RunManifest.from_dict(payload_with(stamp))
    assert parsed is not None
    assert parsed.created_epoch == pytest.approx(stamp)
    lib.write_run_manifest(parsed, done_session)
    window = derive_session_window(done_session, root)
    loaded = lib.load_run_manifest(done_session, root, window)
    assert loaded is not None
    assert loaded.run_id == "run-epoch"
    assert lib.RunManifest.from_dict(payload_with(True)) is None
    assert lib.RunManifest.from_dict(payload_with(False)) is None


def test_sanitize_manifest_error_value_strips_control_characters():
    """[class: REPOSITORY_TEST] Direct unit over ``_sanitize_manifest_error_value``:
    control characters are stripped and the render truncates at 64 characters,
    so newline/CR line forgery is inert in finalize stderr output; printable
    characters, including quotes, survive by contract."""
    forged = "safe\nFORGED LINE\rtab\there"
    assert lib._sanitize_manifest_error_value(forged) == "safeFORGED LINEtabhere"
    long_value = "x" * 100
    assert lib._sanitize_manifest_error_value(long_value) == "x" * 64
    printable = 'schema "9" <v1>'
    assert lib._sanitize_manifest_error_value(printable) == printable


def test_repo_root_matches_value_digest_and_path_arms(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Both arms route through
    ``_repo_root_matches_value``: a 64-hex root digest equal to this repo's
    identity digest matches, a legacy raw resolved path matches, a wrong
    digest and a wrong path refuse."""
    root = mktemp_repo("root-arms")
    digest = lib._repo_root_digest(root)
    assert len(digest) == 64
    assert all(ch in "0123456789abcdef" for ch in digest)
    assert lib._repo_root_matches_value(digest, root) is True
    assert lib._repo_root_matches_value(str(root), root) is True
    wrong_digest = "b" * 64
    assert wrong_digest != digest
    assert lib._repo_root_matches_value(wrong_digest, root) is False
    assert (
        lib._repo_root_matches_value(str(tmp_path / "other-checkout"), root) is False
    )


def test_adopted_chain_stops_at_foreign_root_ancestor(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] F5: an ancestor manifest recorded against a
    different repo root ends the adoption-chain walk with a named warning; a
    foreign-root ancestor can only ever over-include into the OWNED set, never
    suppress a check."""
    root = mktemp_repo("f5-foreign-ancestor")
    marker = make_marker(root, time.time(), os.getpid())
    child = _seed_run_manifest(
        root,
        "run-child",
        marker.name,
        str(root),
        time.time(),
        adopted_from="run-foreign",
    )
    _seed_run_manifest(
        root,
        "run-foreign",
        marker.name,
        str(tmp_path / "other-repo"),
        time.time() - 60,
    )

    chain, warnings = lib._adopted_chain_run_ids(
        root / "docs" / "tmp" / "done-session",
        lib.RunManifest.from_dict(json.loads(child.read_text(encoding="utf-8"))),
        repo_root=root,
    )
    assert chain == ["run-child"]
    assert warnings and any("run-foreign" in w for w in warnings)
    assert any("repo root" in w for w in warnings)


def test_porcelain_paths_unquote_rename_destination(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] F9: a staged rename of a staging doc whose
    names trigger git's C-style quoting keeps the quote-stripped DESTINATION
    in the claim-or-foreign universe (a rename row keeps only its new side,
    so the source side is never a member)."""
    root = mktemp_repo("f9-quoted-rename", gitignore_docs=False)
    reviews = root / "docs" / "reviews"
    reviews.mkdir(parents=True)
    src = reviews / 'weird "quoted" name.md'
    dst = reviews / 'weird "quoted" new.md'
    src.write_text("staging body\n", encoding="utf-8")
    git(root, "add", str(src.relative_to(root)))
    git(root, "commit", "-m", "stage", "-q")
    git(root, "mv", str(src.relative_to(root)), str(dst.relative_to(root)))

    ctx = ctx_for(root)
    ordinary, _ignored = lib._porcelain_paths(ctx, ".")
    assert str(dst.relative_to(root)) in ordinary
    # No quoting residue: git's escaped form (\" inside a quoted row) must
    # not survive unquoting - the real filename's own quotes are fine.
    assert not any('\\\"' in p for p in ordinary)


def test_load_run_manifest_and_orphans_report_corrupt_records(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] F10: a corrupt run-manifest-*.json in the
    done-session directory is named by the loader's report channel and by the
    orphan detection output instead of being silently skipped."""
    root = mktemp_repo("f10-corrupt")
    make_marker(root, time.time(), os.getpid())
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / "run-manifest-run-broken.json").write_text(
        "{not json at all", encoding="utf-8"
    )
    warnings: list[str] = []
    window = derive_session_window(done_session, root)
    lib.load_run_manifest(done_session, root, window, warnings=warnings)
    assert any("run-broken" in w for w in warnings)

    orphan_warnings: list[str] = []
    lib._detect_interrupted_runs(
        done_session, root, warnings=orphan_warnings
    )
    assert any("run-broken" in w for w in orphan_warnings)


def test_classify_committed_range_dangling_symlink_ledger_unreadable(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] F11: an owned-commits ledger whose stat fails
    (a dangling symlink in its place) is reported as unreadable, never
    classified as absent/empty - the run's own commits must not classify
    foreign, so the conservative cumulative range rows are kept."""
    root = mktemp_repo("f11-dangling-ledger")
    (root / "second.txt").write_text("second commit\n", encoding="utf-8")
    git(root, "add", "second.txt")
    git(root, "commit", "-m", "second", "-q")
    base = git(root, "rev-parse", "HEAD~1").stdout.strip()
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    ledger = lib._owned_commits_ledger_path(done_session, "run-dangling")
    os.symlink(str(done_session / "no-such-ledger-target"), str(ledger))

    ctx = ctx_for(root)
    rows, report = lib._classify_committed_range(ctx, base, [ledger])
    assert any("unreadable" in line for line in report)
    assert any("run-dangling" in line for line in report)
    assert rows  # conservative cumulative range rows kept, nothing narrowed


def test_write_manifest_claim_none_marks_all_candidates_foreign(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] F13: ``--claim-none`` answers the
    claim-or-foreign abort for a run owning no staging doc - every unclaimed
    candidate is marked foreign and recorded in the manifest's
    foreign_review_paths for audit."""
    root = mktemp_repo("f13-claim-none")
    make_marker(root, time.time(), os.getpid())
    peer_a = "docs/reviews/2026-09-25-peer-review-a-r1.md"
    peer_b = "docs/reviews/2026-09-25-peer-review-b-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    for rel in (peer_a, peer_b):
        (root / rel).write_text("peer staging review\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest", "--claim-none"]) == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert sorted(payload["foreign_review_paths"]) == sorted([peer_a, peer_b])
    assert payload["owned_review_paths"] == []


def test_write_manifest_claim_none_conflicts_with_adopted_owner(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] F13 composition rule: ``--claim-none`` with an
    adopted manifest that itself owns staging docs aborts with a named
    ownership-conflict error rather than silently flipping the adopted owned
    paths to foreign."""
    root = mktemp_repo("f13-conflict")
    marker = make_marker(root, time.time(), os.getpid())
    owned = "docs/reviews/2026-09-25-adopted-owned-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    (root / owned).write_text("adopted run's own staging doc\n", encoding="utf-8")
    _seed_run_manifest(
        root,
        "run-adopter",
        marker.name,
        str(root),
        time.time() - 60,
        owned_review_paths=[owned],
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest", "--claim-none", "--adopt", "run-adopter"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "ownership-conflict" in err
    assert owned in err


def test_write_manifest_foreign_review_from_file_bulk_loads(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] F13: ``--foreign-review-from <file>`` bulk-loads
    foreign paths one per line, merged into foreign_review_paths with the same
    dedup as ``--foreign-review``."""
    root = mktemp_repo("f13-from-file")
    make_marker(root, time.time(), os.getpid())
    (root / "docs/reviews").mkdir(parents=True)
    peer_a = "docs/reviews/2026-09-25-peer-review-a-r1.md"
    peer_b = "docs/reviews/2026-09-25-peer-review-b-r1.md"
    for rel in (peer_a, peer_b):
        (root / rel).write_text("peer staging review\n", encoding="utf-8")
    list_file = root / "docs" / "tmp" / "foreign-list.txt"
    list_file.parent.mkdir(parents=True, exist_ok=True)
    list_file.write_text(f"{peer_a}\n\n{peer_a}\n{peer_b}\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest", "--foreign-review-from", str(list_file)]) == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert sorted(payload["foreign_review_paths"]) == sorted([peer_a, peer_b])


# --------------------------------------------------------------------------- #
# Done-gate manifest root truth: digest root + repo-relative paths.
# --------------------------------------------------------------------------- #
def root_digest(root: Path) -> str:
    """The done Step 0 identity digest: sha256 of the trailing-slash-stripped
    resolved repo root (the spelling GateContext.discover records)."""
    return hashlib.sha256(str(root.resolve()).rstrip("/").encode()).hexdigest()


def test_write_manifest_records_repo_root_digest(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a fixture repo with a content-bearing
    run-start marker, expects write-manifest to record the 64-hex digest of
    the resolved root as ``repo_root`` and to leave the raw root spelling out
    of the manifest bytes entirely."""
    root = mktemp_repo("digest-root")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest"]) == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    text = manifests[0].read_text(encoding="utf-8")
    payload = json.loads(text)
    assert payload["repo_root"] == root_digest(root)
    assert str(root) not in text


def test_write_manifest_relativizes_absolute_foreign_input(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given ``--foreign-review`` answered with an
    absolute path under the fixture root (the claim-or-foreign error prints
    absolute candidate paths), expects the manifest to store the repo-relative
    form and no raw root spelling in the bytes."""
    root = mktemp_repo("abs-foreign")
    make_marker(root, time.time(), os.getpid())
    review_rel = "docs/reviews/2026-09-27-peer-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    (root / review_rel).write_text("peer staging review\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest", "--foreign-review", str(root / review_rel)]) == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    text = manifests[0].read_text(encoding="utf-8")
    payload = json.loads(text)
    assert payload["foreign_review_paths"] == [review_rel]
    assert str(root) not in text


def test_write_manifest_relativizes_symlink_aliased_foreign_input(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a symlink alias directory pointing at
    the fixture repo root and a ``--foreign-review`` input spelled through the
    alias, expects the stored path to be the repo-relative form; this
    discriminates the resolve-first helper from a lexical containment check."""
    root = mktemp_repo("alias-foreign")
    make_marker(root, time.time(), os.getpid())
    review_rel = "docs/reviews/2026-09-27-aliased-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True)
    (root / review_rel).write_text("peer staging review\n", encoding="utf-8")
    alias = tmp_path / "alias-link"
    alias.symlink_to(root, target_is_directory=True)
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(
        [
            "write-manifest",
            "--foreign-review",
            str(alias / "docs" / "reviews" / "2026-09-27-aliased-review-r1.md"),
        ]
    ) == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert payload["foreign_review_paths"] == [review_rel]


def test_write_manifest_relativizes_inherited_paths_on_adopt(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a seeded legacy manifest recording the
    absolute root plus an absolute owned review path and an absolute foreign
    path, when the new run adopts it and also passes ``--foreign-review``
    naming the relative form of that same foreign path, expects the new
    manifest to record the digest root and repo-relative owned and foreign
    paths with the shared path recorded exactly once and no raw root spelling."""
    root = mktemp_repo("adopt-rel")
    now = time.time()
    make_marker(root, now - 60, os.getpid())
    (root / "docs/reviews").mkdir(parents=True)
    owned_rel = "docs/reviews/2026-09-27-owned-review-r1.md"
    foreign_rel = "docs/reviews/2026-09-27-peer-review-r1.md"
    for rel in (owned_rel, foreign_rel):
        (root / rel).write_text("staging review body\n", encoding="utf-8")
    old_run_id = "20260926T000000Z-adoptseed01"
    _seed_run_manifest(
        root,
        old_run_id,
        marker_name(now - 60),
        str(root.resolve()),
        now - 60,
        owned_review_paths=[str(root / owned_rel)],
        foreign_review_paths=[str(root / foreign_rel)],
    )
    make_marker(root, now, os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(
        ["write-manifest", "--adopt", old_run_id, "--foreign-review", foreign_rel]
    ) == 0
    manifests = sorted(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 2
    text = manifests[-1].read_text(encoding="utf-8")
    payload = json.loads(text)
    assert payload["adopted_from"] == old_run_id
    assert payload["repo_root"] == root_digest(root)
    assert payload["owned_review_paths"] == [owned_rel]
    assert payload["foreign_review_paths"] == [foreign_rel]
    assert str(root) not in text


def test_manifest_root_matches_digest_and_legacy_arms(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given ``_manifest_root_matches`` called with
    this repo's digest, a legacy absolute path spelling, a foreign repo's
    digest, and a foreign absolute path, expects True, True, False, False."""
    root = mktemp_repo("root-arms")
    other = mktemp_repo("other-root")
    # The production compare side is the resolved root (GateContext.discover
    # resolves DONE_SWEEP_REPO_ROOT), so the direct calls pass root.resolve().
    assert lib._manifest_root_matches(root_digest(root), root.resolve()) is True
    assert lib._manifest_root_matches(str(root.resolve()), root.resolve()) is True
    assert lib._manifest_root_matches(root_digest(other), root.resolve()) is False
    assert lib._manifest_root_matches(str(other.resolve()), root.resolve()) is False


def test_load_run_manifest_accepts_digest_root_and_rejects_foreign_digest(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a seeded manifest whose ``repo_root`` is
    the digest of the resolved root, expects the loader to return it; given
    one seeded with a foreign repo's digest, expects None."""
    root = mktemp_repo("load-digest")
    other = mktemp_repo("load-foreign")
    now = time.time()
    make_marker(root, now, os.getpid())
    window = lib.derive_session_window(
        root / "docs" / "tmp" / "done-session", root
    )
    assert window.current is not None

    _seed_run_manifest(
        root,
        "20260926T000000Z-digestok01",
        window.current.path.name,
        root_digest(root),
        now,
    )
    loaded = lib.load_run_manifest(
        root / "docs" / "tmp" / "done-session", root.resolve(), window
    )
    assert loaded is not None
    assert loaded.run_id == "20260926T000000Z-digestok01"

    foreign_window_root = mktemp_repo("load-foreign-root")
    make_marker(foreign_window_root, now, os.getpid())
    foreign_window = lib.derive_session_window(
        foreign_window_root / "docs" / "tmp" / "done-session", foreign_window_root
    )
    _seed_run_manifest(
        foreign_window_root,
        "20260926T000000Z-digestfg01",
        foreign_window.current.path.name,
        root_digest(other),
        now,
    )
    assert (
        lib.load_run_manifest(
            foreign_window_root / "docs" / "tmp" / "done-session",
            foreign_window_root.resolve(),
            foreign_window,
        )
        is None
    )


# --------------------------------------------------------------------------- #
# Marker parser hex-token hardening and mixed-format window.
# --------------------------------------------------------------------------- #
def test_parse_marker_hex_mismatch_returns_none_without_realpath(
    tmp_path, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a 3-field marker whose middle field is a
    64-hex token that is not this repo's digest, with ``os.path.realpath``
    monkeypatched to raise, expects ``_parse_marker`` to return None and
    ``_marker_records_other_repo`` to return True with neither calling
    realpath; and given a digest-match marker, expects ``_parse_marker`` to
    succeed under the same raising monkeypatch."""
    root = mktemp_repo("hex-mismatch").resolve()
    foreign_digest = hashlib.sha256(b"some-other-repo-root").hexdigest()
    marker_path = tmp_path / "run-start-foreign"
    marker_path.write_text(
        f"1000 {foreign_digest} 4242\n", encoding="utf-8"
    )

    def explode(path, *args, **kwargs):
        raise AssertionError("realpath must not be called for hex tokens")

    monkey = __import__("pytest").MonkeyPatch()
    monkey.setattr(lib.os.path, "realpath", explode)
    try:
        assert lib._parse_marker(marker_path, root) is None
        assert lib._marker_records_other_repo(marker_path, root) is True
    finally:
        monkey.undo()

    digest_marker = tmp_path / "run-start-digest"
    digest_marker.write_text(
        f"2000 {lib._repo_root_digest(root)} 4242\n", encoding="utf-8"
    )
    monkey2 = __import__("pytest").MonkeyPatch()
    monkey2.setattr(lib.os.path, "realpath", explode)
    try:
        parsed = lib._parse_marker(digest_marker, root)
    finally:
        monkey2.undo()
    assert parsed is not None
    assert parsed.repo_root == lib._repo_root_digest(root)


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-30-interrupted-run-disposition-and-survey-arm.md
# Task 1: disposition operation, listing operation, detection filter.
# --------------------------------------------------------------------------- #
def test_disposition_manifest_refusal_set(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm (a): given a fixture per refusal
    class, expects ``disposition-manifest`` to refuse with a named one-line
    error and a non-zero exit, leaving the manifest bytes byte-identical,
    for an absent manifest, a complete run, an adopted boundary (another
    manifest's adopted_from link names the run), a live root recorded as a
    legacy raw path equal to the fixture root (so a digest-equality bypass
    fails and the refusal names the resume path), and a missing deliverable;
    an already-dispositioned manifest instead reprints its existing record
    with a zero exit."""
    root = mktemp_repo("disposition-refusals")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    # Arm: absent manifest refuses, non-zero, named.
    assert lib.main(["disposition-manifest", "--run-id", "run-absent"]) == 1
    assert "no run manifest" in capsys.readouterr().err

    # Arm: complete run refuses (a finalized run is never an interrupted run).
    complete_id = "run-complete"
    _seed_run_manifest(
        root, complete_id, marker_name(now), str(root.resolve()), now, complete=True
    )
    before = (done_session / f"run-manifest-{complete_id}.json").read_bytes()
    assert lib.main(["disposition-manifest", "--run-id", complete_id]) == 1
    assert "already finalized" in capsys.readouterr().err
    assert (done_session / f"run-manifest-{complete_id}.json").read_bytes() == before

    # Arm: adopted boundary refuses (an adopted_from link names the run).
    victim_id = "run-adopted-victim"
    _seed_run_manifest(
        root, victim_id, marker_name(now), str(tmp_path / "deleted-wt"), now
    )
    _seed_run_manifest(
        root,
        "run-adopter",
        marker_name(now),
        str(root.resolve()),
        now,
        adopted_from=victim_id,
    )
    before = (done_session / f"run-manifest-{victim_id}.json").read_bytes()
    assert lib.main(["disposition-manifest", "--run-id", victim_id]) == 1
    assert "adopts this boundary" in capsys.readouterr().err
    assert (done_session / f"run-manifest-{victim_id}.json").read_bytes() == before

    # Arm: live root refuses. The recorded root is the LEGACY RAW PATH equal
    # to the fixture root, so a digest-equality bypass would misclassify it
    # as dead and (wrongly) proceed to the stamp; the two-arm matcher catches
    # it and the refusal names the resume path (the adoption boundary).
    live_id = "run-live-root"
    _seed_run_manifest(root, live_id, marker_name(now), str(root), now)
    before = (done_session / f"run-manifest-{live_id}.json").read_bytes()
    assert lib.main(["disposition-manifest", "--run-id", live_id]) == 1
    err = capsys.readouterr().err
    assert "live root" in err
    assert "--adopt" in err  # the named resume path
    assert (done_session / f"run-manifest-{live_id}.json").read_bytes() == before

    # Arm: already-dispositioned reprints the existing record, exit 0.
    stamped_id = "run-already-dispositioned"
    stamp = {
        "reason": "work-verified-landed",
        "date": "2026-09-29",
        "note": "witnessed closure",
    }
    _seed_run_manifest(
        root,
        stamped_id,
        marker_name(now),
        str(tmp_path / "deleted-wt-2"),
        now,
        dispositioned=stamp,
    )
    before = (done_session / f"run-manifest-{stamped_id}.json").read_bytes()
    assert lib.main(["disposition-manifest", "--run-id", stamped_id]) == 0
    out = capsys.readouterr().out
    assert f"dispositioned: {stamped_id} (2026-09-29)" in out
    assert "work-verified-landed" in out
    assert (done_session / f"run-manifest-{stamped_id}.json").read_bytes() == before

    # Arm: missing deliverable refuses naming the first missing path.
    missing_id = "run-missing-deliverable"
    missing_review = "docs/reviews/2026-09-30-never-landed-r1.md"
    _seed_run_manifest(
        root,
        missing_id,
        marker_name(now),
        str(tmp_path / "deleted-wt-3"),
        now,
        owned_review_paths=[missing_review],
    )
    before = (done_session / f"run-manifest-{missing_id}.json").read_bytes()
    assert lib.main(["disposition-manifest", "--run-id", missing_id]) == 1
    err = capsys.readouterr().err
    assert "deliverables witness failed" in err
    assert missing_review in err
    assert (done_session / f"run-manifest-{missing_id}.json").read_bytes() == before


def test_disposition_stamp_round_trip_dead_root(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm (b): given a fixture dead-root
    manifest (a recorded root naming a checkout that no longer exists, so
    both matcher arms fail) whose owned deliverable resolves at HEAD, expects
    ``disposition-manifest`` to stamp
    ``{reason: "work-verified-landed", date, note}`` and to print the
    ``dispositioned: <run_id> (<date>)`` line; the record survives a reload
    through the root-agnostic reader and through ``from_dict`` on the raw
    payload (the root-filtered loader would refuse the dead-root record),
    and a non-dict ``dispositioned`` payload degrades to unset."""
    root = mktemp_repo("disposition-roundtrip")
    now = time.time()
    run_id = "run-disposition-roundtrip"
    _seed_run_manifest(
        root,
        run_id,
        marker_name(now),
        str(tmp_path / "deleted-worktree"),
        now,
        owned_paths=["README.md"],  # committed by the fixture's init commit
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    manifest_path = (
        root / "docs" / "tmp" / "done-session" / f"run-manifest-{run_id}.json"
    )

    rc = lib.main(
        [
            "disposition-manifest",
            "--run-id",
            run_id,
            "--note",
            "witnessed incident closure",
        ]
    )

    assert rc == 0
    today = datetime.now(timezone.utc).date().isoformat()
    assert f"dispositioned: {run_id} ({today})" in capsys.readouterr().out
    expected = {
        "reason": "work-verified-landed",
        "date": today,
        "note": "witnessed incident closure",
    }
    # Root-agnostic reader reload (the root-filtered loader refuses the
    # dead-root record this operation exists to close).
    reloaded = lib._read_manifest_by_run_id(
        root / "docs" / "tmp" / "done-session", run_id
    )
    assert reloaded is not None
    assert reloaded.dispositioned == expected
    assert reloaded.complete is False  # the stamp closes without finalizing
    # The tolerant from_dict mapping reads the record back from raw bytes.
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["dispositioned"] == expected
    assert lib.RunManifest.from_dict(payload).dispositioned == expected
    # A non-dict dispositioned value degrades to unset, never an exception.
    corrupt = dict(payload)
    corrupt["dispositioned"] = "bogus"
    assert lib.RunManifest.from_dict(corrupt).dispositioned is None
    # as_dict emits the field so a write-through keeps it first-class.
    assert lib.RunManifest.from_dict(payload).as_dict()["dispositioned"] == expected


def test_disposition_rerun_reprints_after_deliverable_vanishes(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm (c): given a stamped manifest whose
    owned deliverable has since vanished from the checkout, expects a
    ``disposition-manifest`` re-run to print the existing record and exit 0
    instead of refusing: the closure is one-time and a vanished deliverable
    cannot un-close it."""
    root = mktemp_repo("disposition-rerun")
    now = time.time()
    run_id = "run-disposition-rerun"
    plan_rel = "docs/history/plans/2026-09-30-vanishing-plan.md"
    plan = root / plan_rel
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("plan body\n", encoding="utf-8")  # on-disk arm, unstaged
    _seed_run_manifest(
        root,
        run_id,
        marker_name(now),
        str(tmp_path / "deleted-worktree"),
        now,
        owned_plan_paths=[plan_rel],
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    assert lib.main(["disposition-manifest", "--run-id", run_id]) == 0
    capsys.readouterr()
    plan.unlink()
    assert not plan.exists()

    rc = lib.main(["disposition-manifest", "--run-id", run_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "already dispositioned" in out
    assert "work-verified-landed" in out


def test_disposition_owned_paths_archive_twin_resolves(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a dead-root manifest whose ``owned_paths``
    entry records a plans-tree path that exists only as its ``plans_completed``
    archive twin at HEAD (schema-1 manifests that recorded plan edits under
    ``owned_paths`` survive their plan's archive), expects
    ``disposition-manifest`` to stamp the ``work-verified-landed`` record with
    the resolution visible in the reloaded record."""
    root = mktemp_repo("disposition-owned-twin", gitignore_docs=False)
    now = time.time()
    run_id = "run-owned-twin"
    twin_rel = "docs/history/plans/completed/2026-09-30-archived-plan.md"
    twin = root / twin_rel
    twin.parent.mkdir(parents=True, exist_ok=True)
    twin.write_text("archived plan bytes\n", encoding="utf-8")
    git(root, "add", twin_rel)
    git(root, "commit", "-m", "archive plan", "-q")
    _seed_run_manifest(
        root,
        run_id,
        marker_name(now),
        str(tmp_path / "deleted-worktree"),
        now,
        owned_paths=["docs/history/plans/2026-09-30-archived-plan.md"],
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    assert lib.main(["disposition-manifest", "--run-id", run_id]) == 0

    out = capsys.readouterr().out
    today = datetime.now(timezone.utc).date().isoformat()
    assert f"dispositioned: {run_id} ({today})" in out
    reloaded = lib._read_manifest_by_run_id(
        root / "docs" / "tmp" / "done-session", run_id
    )
    assert reloaded is not None
    assert reloaded.dispositioned is not None
    assert reloaded.dispositioned["reason"] == "work-verified-landed"


def test_disposition_owned_paths_landed_deletion_witness_resolves(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a dead-root manifest whose ``owned_paths``
    entry names a file a landed commit deleted after the run (a deletion in
    HEAD's history landed through the repo's own gates, so it is the
    sanctioned outcome, not a loss), expects ``disposition-manifest`` to
    stamp the record; a never-tracked path with no deletion in history still
    refuses naming the path."""
    root = mktemp_repo("disposition-owned-deletion", gitignore_docs=False)
    now = time.time()
    run_id = "run-owned-deletion"
    path_rel = "docs/history/plans/2026-09-30-transient-plan.md"
    target = root / path_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("plan bytes\n", encoding="utf-8")
    git(root, "add", path_rel)
    git(root, "commit", "-m", "record plan", "-q")
    git(root, "rm", "-q", path_rel)
    git(root, "commit", "-m", "landed deletion", "-q")
    _seed_run_manifest(
        root, run_id, marker_name(now), str(tmp_path / "deleted-worktree"), now,
        owned_paths=[path_rel],
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    assert lib.main(["disposition-manifest", "--run-id", run_id]) == 0
    capsys.readouterr()
    reloaded = lib._read_manifest_by_run_id(
        root / "docs" / "tmp" / "done-session", run_id
    )
    assert reloaded is not None
    assert reloaded.dispositioned is not None

    never_id = "run-never-tracked"
    _seed_run_manifest(
        root, never_id, marker_name(now), str(tmp_path / "deleted-wt-2"), now,
        owned_paths=["docs/reviews/2026-09-30-never-tracked.md"],
    )
    assert lib.main(["disposition-manifest", "--run-id", never_id]) == 1
    err = capsys.readouterr().err
    assert "deliverables witness failed" in err
    assert "docs/reviews/2026-09-30-never-tracked.md" in err


def test_disposition_note_backed_resolution_closes_cross_checkout(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a dead-root manifest whose
    ``owned_plan_paths`` entry resolves in no arm of this checkout and an
    operator ``--note`` naming that path with its home checkout and verifying
    commit, expects ``disposition-manifest`` to stamp the record with the
    operator's note carried verbatim; an entry neither armed nor note-named
    still refuses naming the path, and an empty note changes nothing."""
    root = mktemp_repo("disposition-note-backed")
    now = time.time()
    run_id = "run-note-backed"
    orphan_plan = "docs/history/plans/2026-09-30-foreign-checkout-plan.md"
    _seed_run_manifest(
        root, run_id, marker_name(now), str(tmp_path / "deleted-worktree"), now,
        owned_plan_paths=[orphan_plan],
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    note = (
        "deliverable docs/history/plans/2026-09-30-foreign-checkout-plan.md "
        "resolved in home checkout /srv/other-checkout at commit 0f1e2d3c "
        "(verified there)"
    )

    assert (
        lib.main(["disposition-manifest", "--run-id", run_id, "--note", note])
        == 0
    )
    capsys.readouterr()
    reloaded = lib._read_manifest_by_run_id(
        root / "docs" / "tmp" / "done-session", run_id
    )
    assert reloaded is not None
    assert reloaded.dispositioned is not None
    assert reloaded.dispositioned["note"] == note

    # An unresolvable entry neither armed nor note-named still refuses.
    refuse_id = "run-note-miss"
    _seed_run_manifest(
        root, refuse_id, marker_name(now), str(tmp_path / "deleted-wt-2"), now,
        owned_plan_paths=["docs/history/plans/2026-09-30-unnamed-plan.md"],
    )
    assert lib.main(["disposition-manifest", "--run-id", refuse_id]) == 1
    err = capsys.readouterr().err
    assert "docs/history/plans/2026-09-30-unnamed-plan.md" in err

    # An empty note changes nothing for the refusing shape.
    empty_id = "run-note-empty"
    _seed_run_manifest(
        root, empty_id, marker_name(now), str(tmp_path / "deleted-wt-3"), now,
        owned_plan_paths=["docs/history/plans/2026-09-30-unnamed-plan.md"],
    )
    assert (
        lib.main(["disposition-manifest", "--run-id", empty_id, "--note", ""])
        == 1
    )
    assert "deliverables witness failed" in capsys.readouterr().err


def test_disposition_zero_owned_sets_prints_and_stamps_note(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm (d): given a dead-root manifest
    whose three owned sets are all empty, expects ``disposition-manifest``
    to print the named no-deliverables note on stdout and to stamp it inside
    the dispositioned record (the witness is vacuously true and the note
    keeps the closure honest), with the work-verified-landed reason and the
    canonical dispositioned line still present."""
    root = mktemp_repo("disposition-zero")
    now = time.time()
    run_id = "run-zero-deliverables"
    _seed_run_manifest(
        root, run_id, marker_name(now), str(tmp_path / "deleted-worktree"), now
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["disposition-manifest", "--run-id", run_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "no-deliverables" in out
    assert "vacuously true" in out
    assert f"dispositioned: {run_id}" in out
    record = lib._read_manifest_by_run_id(
        root / "docs" / "tmp" / "done-session", run_id
    )
    assert record is not None
    assert record.dispositioned["reason"] == "work-verified-landed"
    assert "no-deliverables" in record.dispositioned["note"]
    assert "vacuously true" in record.dispositioned["note"]


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-01-disposition-machinery-followups.md
# Task 3: the stamp CAS race arm and the skill anchor phrases.
# --------------------------------------------------------------------------- #
def test_disposition_stamp_cas_refuses_post_check_finalize(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm: given a dead-root manifest whose
    witness is vacuously true and a finalize landing between the
    disposition's initial read and the stamp (``complete`` flips true on
    disk), expects ``disposition-manifest`` to refuse with the post-check
    finalize named and to leave no ``dispositioned`` record in the on-disk
    payload: the stamp CAS re-read closes the check-then-write window. The
    racer's flip fires when the initial read returns, inside the window the
    CAS guards (``write_run_manifest`` is reached only after the CAS has
    passed, so a flip hooked there would be clobbered by the original write
    and never seen by the re-read)."""
    root = mktemp_repo("disposition-cas-finalize")
    now = time.time()
    run_id = "run-cas-finalize-race"
    done_session = root / "docs" / "tmp" / "done-session"
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    _seed_run_manifest(
        root, run_id, marker_name(now), str(tmp_path / "deleted-worktree"), now
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    original_read = lib._read_manifest_by_run_id

    def racing_read(done_session_dir, rid):
        manifest = original_read(done_session_dir, rid)
        if manifest is not None and manifest.run_id == rid:
            # The racer: a finalize writes its payload right after the
            # disposition's initial read, before the stamp.
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["complete"] = True
            manifest_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return manifest

    monkeypatch.setattr(lib, "_read_manifest_by_run_id", racing_read)

    rc = lib.main(["disposition-manifest", "--run-id", run_id])

    assert rc == 1
    err = capsys.readouterr().err
    assert "post-check finalize" in err
    assert run_id in err
    # No dispositioned record landed: the payload holds the racer's
    # finalize shape, never this call's stamp.
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["complete"] is True
    assert payload["dispositioned"] is None
    reloaded = original_read(done_session, run_id)
    assert reloaded is not None
    assert reloaded.complete is True
    assert reloaded.dispositioned is None


def test_disposition_stamp_cas_refuses_post_check_adoption(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm: given a dead-root manifest whose
    witness is vacuously true and a competing manifest whose ``adopted_from``
    link names the run landing between the disposition's initial read and
    the stamp, expects ``disposition-manifest`` to refuse with the post-check
    adoption named and to leave no ``dispositioned`` record in the on-disk
    payload: the stamp CAS directory re-scan closes the window a payload-only
    re-read cannot see (adoption writes ``adopted_from`` on the ADOPTER's
    manifest). The adopter seeds on the scan helper's SECOND invocation:
    the first invocation is the disposition pre-check and must pass through
    unchanged, otherwise the pre-check refusal fires before the stamp and
    the post-check shape is never reached."""
    root = mktemp_repo("disposition-cas-adoption")
    now = time.time()
    run_id = "run-cas-adoption-race"
    done_session = root / "docs" / "tmp" / "done-session"
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    _seed_run_manifest(
        root, run_id, marker_name(now), str(tmp_path / "deleted-worktree"), now
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    original_adopted = lib._manifest_adopted_by_another

    def racing_adopted_scan(done_session_dir, rid):
        calls = getattr(racing_adopted_scan, "calls", 0) + 1
        racing_adopted_scan.calls = calls
        if calls == 2 and rid == run_id:
            # The racer: a competing run adopts this boundary right after
            # the pre-checks, before the stamp-time re-scan. Seeding through
            # the real writer keeps the production scan (no stub) honest.
            _seed_run_manifest(
                root,
                "run-cas-adopter",
                marker_name(now),
                str(root),
                now + 1,
                adopted_from=rid,
            )
        return original_adopted(done_session_dir, rid)

    monkeypatch.setattr(lib, "_manifest_adopted_by_another", racing_adopted_scan)

    rc = lib.main(["disposition-manifest", "--run-id", run_id])

    assert rc == 1
    err = capsys.readouterr().err
    assert "post-check adoption" in err
    assert run_id in err
    # No dispositioned record landed on the dead-root manifest: the payload
    # keeps its pre-stamp shape, never this call's stamp.
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["dispositioned"] is None
    assert payload["complete"] is False
    reloaded = lib._read_manifest_by_run_id(done_session, run_id)
    assert reloaded is not None
    assert reloaded.dispositioned is None
    # The adopter is on disk with the link naming the run (the real scan
    # saw it, the refusal names the post-check shape).
    adopter = lib._read_manifest_by_run_id(done_session, "run-cas-adopter")
    assert adopter is not None
    assert adopter.adopted_from == run_id


def test_disposition_stamp_cas_dispositioned_race_reprints_idempotent(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm: given a dead-root manifest and a
    concurrent disposition landing between the disposition's initial read
    and the stamp, expects ``disposition-manifest`` to exit 0 and reprint
    the RACER's record (the racer's date and record JSON echoed, not this
    call's): the stamp CAS fresh re-read degrades to the idempotent path.
    No new write lands: the on-disk payload keeps the racer's record
    unchanged. The racer fires on the reader helper's SECOND call, the
    CAS's fresh re-read, which only reaches the hook through the rerouted
    parse path (a raw-json fresh read never makes the second call)."""
    root = mktemp_repo("disposition-cas-dispositioned")
    now = time.time()
    run_id = "run-cas-dispositioned-race"
    done_session = root / "docs" / "tmp" / "done-session"
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    _seed_run_manifest(
        root, run_id, marker_name(now), str(tmp_path / "deleted-worktree"), now
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    racer_record = {
        "reason": "work-verified-landed",
        "date": "2026-09-29",
        "note": "racer note",
    }

    original_read = lib._read_manifest_by_run_id

    def racing_read(done_session_dir, rid):
        calls = getattr(racing_read, "calls", 0) + 1
        racing_read.calls = calls
        manifest = original_read(done_session_dir, rid)
        if calls == 2 and manifest is not None and manifest.run_id == rid:
            # The racer: a concurrent disposition stamps its record after
            # the pre-checks; the CAS's fresh re-read must see it. The
            # returned manifest is the honest parse of the flipped disk.
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["dispositioned"] = dict(racer_record)
            manifest_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            manifest = original_read(done_session_dir, rid)
        return manifest

    monkeypatch.setattr(lib, "_read_manifest_by_run_id", racing_read)

    rc = lib.main(["disposition-manifest", "--run-id", run_id])

    assert rc == 0
    out = capsys.readouterr().out
    assert "concurrent disposition won the race" in out
    assert "2026-09-29" in out  # the racer's date, not this call's
    assert "racer note" in out
    assert json.dumps(racer_record, sort_keys=True) in out
    # No new write: the on-disk payload carries the racer's record exactly
    # (this call's stamp would carry an empty note and today's date).
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["dispositioned"] == racer_record
    assert payload["complete"] is False


def test_disposition_skill_anchor_phrases_present():
    """[class: REPOSITORY_TEST] Plan arm: the two skill anchors from the
    plan's Validation Commands hold - the done skill's witness sentence
    names the third plan arm (``HEAD:<recorded path>``) and the maintenance
    skill's interrupted-manifest classification arm pins the proactive
    stale-deployment probe."""
    repo_root = Path(__file__).resolve().parents[1]
    done_text = (repo_root / "agents/skills/done/SKILL.md").read_text(
        encoding="utf-8"
    )
    maintenance_text = (
        repo_root / "agents/skills/maintenance/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "HEAD:<recorded path>" in done_text
    assert "stale-deployment" in maintenance_text


def test_list_interrupted_manifests_columns_and_non_mutation(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan arm (e): a dead-root fixture prints its
    ``root=dead`` line with ``dispositioned=no`` flipping to ``yes`` after a
    stamp; the ``adopted`` column reports the record's own ``adopted_from``
    link while a complete record never lists; a clean fixture prints the
    empty-set line; and the listing never mutates (byte-identical manifest
    set before and after)."""
    # Empty set on a clean fixture.
    empty_root = mktemp_repo("listing-empty")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(empty_root))
    assert lib.main(["list-interrupted-manifests"]) == 0
    assert capsys.readouterr().out.strip() == "no interrupted manifests"

    root = mktemp_repo("listing-dead")
    now = time.time()
    created_iso = datetime.fromtimestamp(now, tz=timezone.utc).date().isoformat()
    dead_id = "run-dead-root"
    _seed_run_manifest(
        root, dead_id, marker_name(now), str(tmp_path / "deleted-wt"), now
    )
    # A live-root record that itself adopted an older boundary: root=live,
    # adopted=yes (its own adopted_from link), still an interrupted run.
    _seed_run_manifest(
        root,
        "run-live-adopter",
        marker_name(now),
        str(root.resolve()),
        now,
        adopted_from="run-older-parent",
    )
    # A finalized record never lists.
    _seed_run_manifest(
        root,
        "run-live-complete",
        marker_name(now),
        str(root.resolve()),
        now,
        complete=True,
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"
    before = {p.name: p.read_bytes() for p in done_session.glob("run-manifest-*.json")}

    assert lib.main(["list-interrupted-manifests"]) == 0
    out = capsys.readouterr().out
    assert (
        f"{dead_id} root=dead dispositioned=no adopted=no created={created_iso}"
        in out
    )
    assert (
        f"run-live-adopter root=live dispositioned=no adopted=yes "
        f"created={created_iso}" in out
    )
    assert "run-live-complete" not in out
    # Non-mutation: the listing is read-only over the manifest set.
    after = {p.name: p.read_bytes() for p in done_session.glob("run-manifest-*.json")}
    assert after == before

    # A stamp flips the dispositioned column on the dead-root line.
    assert lib.main(["disposition-manifest", "--run-id", dead_id]) == 0
    capsys.readouterr()
    assert lib.main(["list-interrupted-manifests"]) == 0
    out2 = capsys.readouterr().out
    assert (
        f"{dead_id} root=dead dispositioned=yes adopted=no created={created_iso}"
        in out2
    )


def test_detect_interrupted_runs_dispositioned_and_dead_root_arms(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Plan arm (f): the widened orphan detection
    includes a dead-root unadopted fixture (its recorded root fails both
    matcher arms, yet it stays an orphan when complete is false and nothing
    adopts it - the class the old root filter silently skipped) and excludes
    a dispositioned fixture (the second suppression shape); an adopted
    dead-root record and a live-root orphan line up on the adoption side of
    the contract."""
    root = mktemp_repo("detection-arms")
    now = time.time()
    dead_id = "run-dead-unadopted"
    _seed_run_manifest(
        root, dead_id, marker_name(now), str(tmp_path / "deleted-wt"), now
    )
    disp_id = "run-dispositioned"
    _seed_run_manifest(
        root,
        disp_id,
        marker_name(now),
        str(tmp_path / "deleted-wt-2"),
        now,
        dispositioned={
            "reason": "work-verified-landed",
            "date": "2026-09-29",
            "note": "closed",
        },
    )
    adopted_dead_id = "run-dead-adopted"
    _seed_run_manifest(
        root,
        adopted_dead_id,
        marker_name(now),
        str(tmp_path / "deleted-wt-3"),
        now,
    )
    _seed_run_manifest(
        root,
        "run-adopter-final",
        marker_name(now),
        str(root.resolve()),
        now,
        adopted_from=adopted_dead_id,
        complete=True,
    )
    live_id = "run-live-orphan"
    _seed_run_manifest(root, live_id, marker_name(now), str(root.resolve()), now)

    orphans = lib._detect_interrupted_runs(
        root / "docs" / "tmp" / "done-session", root
    )
    orphan_ids = [m.run_id for m in orphans]

    assert dead_id in orphan_ids  # dead-root unadopted surfaces
    assert disp_id not in orphan_ids  # dispositioned suppresses
    assert adopted_dead_id not in orphan_ids  # adoption suppresses (dead root)
    assert live_id in orphan_ids  # the live-root orphan contract is unchanged


def test_write_manifest_dead_root_orphan_names_disposition_path(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] The write-manifest orphan-report loop's
    dead-root line names the disposition path (the done skill's Manifest
    disposition (dead-boundary close) paragraph) instead of the adoption
    advice, since adoption refuses a dead root; the dead-root orphan itself
    still surfaces through the widened detection, and the undisposed-
    interrupted refusal that follows the report names the disposition exit
    only."""
    root = mktemp_repo("dead-orphan-line")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    dead_id = "run-dead-orphan"
    _seed_run_manifest(
        root,
        dead_id,
        marker_name(now - 3600),
        str(tmp_path / "deleted-worktree"),
        now - 10,
    )
    make_marker(root, now, os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest", "--claim-none"])

    assert rc == 1
    captured = capsys.readouterr()
    assert "interrupted run" in captured.out
    assert dead_id in captured.out
    assert "disposition-manifest" in captured.out
    assert "write-manifest: undisposed-interrupted:" in captured.err
    assert f"disposition-manifest --run-id {dead_id}" in captured.err
    assert "--adopt" not in captured.out + captured.err  # disposition only


def test_write_manifest_refuses_undisposed_interrupted_boundary(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] A complete:false manifest in the window fails
    the write with the named ``write-manifest: undisposed-interrupted:``
    error listing the manifest filename with both live-root remedies
    (``--adopt <run_id>`` to continue it, ``finalize-manifest --run-id`` to
    close it) while the interrupted-run report lines are kept and no manifest
    is written; after ``--adopt`` the write succeeds; on a dead-root fixture
    the refusal names the disposition exit only (adoption refuses a dead
    root), and after ``disposition-manifest`` the write succeeds."""
    # Live-root arm: the refusal, then the adopt exit.
    root = mktemp_repo("undisposed-live")
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-undisposed-live"
    _seed_run_manifest(root, orphan_id, prev.name, str(root), time.time() - 10)
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest"])

    assert rc == 1
    captured = capsys.readouterr()
    assert "write-manifest: undisposed-interrupted:" in captured.err
    assert f"run-manifest-{orphan_id}.json" in captured.err
    assert f"--adopt {orphan_id}" in captured.err
    assert f"finalize-manifest --run-id {orphan_id}" in captured.err
    assert "disposition-manifest refuses live roots" in captured.err
    assert "interrupted run" in captured.out  # the report lines are kept
    assert orphan_id in captured.out
    done_session = root / "docs" / "tmp" / "done-session"
    assert [p.name for p in done_session.glob("run-manifest-*.json")] == [
        f"run-manifest-{orphan_id}.json"
    ]  # the refusal leaves no new manifest behind

    rc2 = lib.main(["write-manifest", "--adopt", orphan_id])
    assert rc2 == 0, capsys.readouterr().err
    payload = _newest_manifest_payload(root, exclude_run_id=orphan_id)
    assert payload["adopted_from"] == orphan_id

    # Dead-root arm: the refusal names the disposition exit only; after
    # disposition-manifest the write succeeds.
    root2 = mktemp_repo("undisposed-dead")
    prev2 = make_marker(root2, time.time() - 3600, os.getpid())
    dead_id = "run-undisposed-dead"
    _seed_run_manifest(
        root2,
        dead_id,
        prev2.name,
        str(tmp_path / "deleted-checkout"),
        time.time() - 10,
    )
    make_marker(root2, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root2))

    rc3 = lib.main(["write-manifest"])

    assert rc3 == 1
    captured3 = capsys.readouterr()
    assert "write-manifest: undisposed-interrupted:" in captured3.err
    assert f"run-manifest-{dead_id}.json" in captured3.err
    assert f"disposition-manifest --run-id {dead_id}" in captured3.err
    assert "--adopt" not in captured3.err  # dead root: disposition only

    assert lib.main(["disposition-manifest", "--run-id", dead_id]) == 0
    capsys.readouterr()
    rc4 = lib.main(["write-manifest"])
    assert rc4 == 0, capsys.readouterr().err


def test_session_window_mixed_format_legacy_prev_digest_current(
    tmp_path, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a legacy raw-path previous marker and a
    digest-format current marker for the same repo (the digest derived from
    the resolved root spelling and the legacy marker recording that same
    resolved spelling verbatim), expects ``derive_session_window`` invoked
    with the ``ctx_for(root)`` context root to anchor with anchor equal to the
    legacy marker, current equal to the digest marker, and ``start_epoch``
    equal to the legacy marker's epoch."""
    root = mktemp_repo("mixed-window")
    old_epoch = time.time() - 3600
    new_epoch = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    legacy = done_session / marker_name(old_epoch)
    legacy.write_text(
        f"{int(old_epoch)} {root.resolve()} {os.getpid()}\n", encoding="utf-8"
    )
    current = done_session / marker_name(new_epoch)
    current.write_text(
        f"{int(new_epoch)} {lib._repo_root_digest(root.resolve())} {os.getpid()}\n",
        encoding="utf-8",
    )

    window = lib.derive_session_window(done_session, ctx_for(root).repo_root)
    assert window.anchored is True
    assert window.anchor is not None
    assert window.anchor.path.name == legacy.name
    assert window.current is not None
    assert window.current.path.name == current.name
    assert window.start_epoch == int(old_epoch)


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-01-docs-branch-single-marker-window.md
# Task 1: the manifest-plus-ledger fallback anchor in derive_session_window.
# --------------------------------------------------------------------------- #
def test_session_window_single_marker_falls_back_to_manifest_witness(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given exactly one content-confirmable marker
    whose bound manifest carries a ``created_epoch`` and whose run's
    owned-commits ledger exists on disk (the witness pair), expects the
    session window to anchor from that pair instead of staying unanchorable:
    ``anchored`` True, ``anchor`` None (marker pruning keeps its conservative
    behavior), ``current`` the single marker, ``start_epoch`` the manifest's
    ``created_epoch``, and a note naming the witness pair."""
    root = mktemp_repo("witness-fallback")
    created = time.time() - 120
    marker = make_marker(root, time.time(), os.getpid())
    _seed_run_manifest(root, "run-witness", marker.name, str(root), created)
    done_session = root / "docs" / "tmp" / "done-session"
    lib._owned_commits_ledger_path(done_session, "run-witness").write_text(
        "", encoding="utf-8"
    )

    window = lib.derive_session_window(done_session, root)

    assert window.anchored is True
    assert window.anchor is None
    assert window.current is not None
    assert window.current.path == marker
    assert window.start_epoch == pytest.approx(created, abs=2)
    assert any("witness pair" in note for note in window.notes)


def test_session_window_manifest_without_ledger_stays_unanchorable(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given exactly one content-confirmable marker
    with its bound manifest but no owned-commits ledger on disk (the witness
    pair incomplete), expects the window to stay unanchorable exactly as
    today (``anchored`` False, ``anchor`` None, ``start_epoch`` None) with a
    witness-pair-incomplete note beside the generic unanchorable note."""
    root = mktemp_repo("witness-missing-ledger")
    created = time.time() - 120
    marker = make_marker(root, time.time(), os.getpid())
    _seed_run_manifest(root, "run-noledger", marker.name, str(root), created)
    done_session = root / "docs" / "tmp" / "done-session"

    window = lib.derive_session_window(done_session, root)

    assert window.anchored is False
    assert window.anchor is None
    assert window.start_epoch is None
    assert window.current is not None
    assert window.current.path == marker
    assert any("witness pair incomplete" in note for note in window.notes)
    assert any("unanchorable" in note for note in window.notes)


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-27-concurrent-landing-archive-routing-gates.md
# Task 1: foreign-staging and plans-archive-twin gates.
# --------------------------------------------------------------------------- #
def _foreign_fixture(tmp_path, sweep_env, name: str):
    """Hermetic repo with a run-start marker, a seeded run manifest whose
    start_porcelain carries the plan's verbatim dirt rows, and the matching
    foreign files staged bare (git add -f; the fixture gitignores /docs/)."""
    root = make_repo(tmp_path, name, gitignore_docs=True)
    write_facts(root)
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    (root / "docs/tmp").mkdir(parents=True, exist_ok=True)
    (root / "docs/tmp/foreign-note.md").write_text("rename old side\n", encoding="utf-8")
    (root / "docs/tmp/foreign note.md").write_text("quoted spaced\n", encoding="utf-8")
    (root / "docs/tmp/tab\tname.md").write_text("control tab\n", encoding="utf-8")
    (root / "docs/tmp/old-note.md").write_text("delete+add old side\n", encoding="utf-8")
    (root / "docs/tmp/new-note.md").write_text("delete+add new side\n", encoding="utf-8")
    (root / "docs/tmp/own-mid-session.md").write_text("own staging\n", encoding="utf-8")
    start_porcelain = [
        "R  docs/tmp/foreign-note.md -> docs/tmp/renamed-note.md",
        '?? "docs/tmp/foreign note.md"',
        '?? "docs/tmp/tab\\tname.md"',
        "R  docs/tmp/old-note.md -> docs/tmp/new-note.md",
    ]
    _seed_run_manifest(
        root,
        "foreign-run-1",
        marker.name,
        str(root),
        now,
        start_porcelain=start_porcelain,
    )
    monkey_ok = root
    git(root, "add", "-f",
        "docs/tmp/foreign-note.md",
        "docs/tmp/foreign note.md",
        "docs/tmp/tab\tname.md",
        "docs/tmp/old-note.md",
        "docs/tmp/new-note.md",
        "docs/tmp/own-mid-session.md")
    return monkey_ok, start_porcelain


def test_foreign_staging_fails_on_foreign_start_dirt(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a hermetic repo whose run manifest is
    seeded with verbatim porcelain rows (rename row, quoted spaced row,
    control-character row, rename exposing a delete+add staged pair), where
    the staged foreign path is the rename's OLD side, expects
    gate_foreign_staging to fail naming the paths, unquoted."""
    root, _ = _foreign_fixture(tmp_path, sweep_env, "foreign-fail")
    result = run_gate("foreign-staging", ctx_for(root))
    assert result.rc == 1, result.message
    for path in (
        "docs/tmp/foreign-note.md",
        "docs/tmp/foreign note.md",
        "docs/tmp/tab\tname.md",
        "docs/tmp/old-note.md",
    ):
        assert path in result.message, (path, result.message)
    # Own mid-session staging outside the start-dirt record is not foreign.
    assert "own-mid-session" not in result.message


def test_foreign_staging_owned_exemption_passes_and_names_path(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given the same start-dirt rows with the
    foreign path present in the manifest's owned_paths, expects the gate to
    pass and the pass result to name the exempted owned path."""
    root, _ = _foreign_fixture(tmp_path, sweep_env, "foreign-owned")
    now = time.time()
    marker = make_marker(root, now + 1, os.getpid())
    _seed_run_manifest(
        root,
        "foreign-owned-run",
        marker.name,
        str(root),
        now + 1,
        start_porcelain=[
            "R  docs/tmp/foreign-note.md -> docs/tmp/renamed-note.md",
        ],
        owned_paths=["docs/tmp/foreign-note.md"],
    )
    result = run_gate("foreign-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert "docs/tmp/foreign-note.md" in result.message
    assert result.warnings and "docs/tmp/foreign-note.md" in result.warnings[0]


def test_foreign_staging_union_exemption_via_plan_paths(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a start-dirt path exempted only via
    owned_plan_paths, expects the gate to pass (the owned set is the union
    of all three lists)."""
    root, _ = _foreign_fixture(tmp_path, sweep_env, "foreign-union")
    now = time.time()
    marker = make_marker(root, now + 1, os.getpid())
    _seed_run_manifest(
        root,
        "foreign-union-run",
        marker.name,
        str(root),
        now + 1,
        start_porcelain=[
            "R  docs/tmp/foreign-note.md -> docs/tmp/renamed-note.md",
        ],
        owned_plan_paths=["docs/tmp/foreign-note.md"],
    )
    result = run_gate("foreign-staging", ctx_for(root))
    assert result.rc == 0, result.message


def test_foreign_staging_rerun_own_staging_passes(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given own mid-session staged paths that appear
    in no start-dirt row, expects the gate to pass."""
    root, _ = _foreign_fixture(tmp_path, sweep_env, "foreign-rerun")
    now = time.time()
    marker = make_marker(root, now + 1, os.getpid())
    _seed_run_manifest(
        root,
        "foreign-rerun-run",
        marker.name,
        str(root),
        now + 1,
        start_porcelain=["?? docs/tmp/unrelated-dirt.md"],
    )
    result = run_gate("foreign-staging", ctx_for(root))
    assert result.rc == 0, result.message


def test_foreign_staging_adopted_run_claimed_and_unclaimed(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Adopted-run shapes: an adopted manifest whose
    start_porcelain records the predecessor's created file (the unioned
    start-dirt record) passes when the adopting Step 0 claimed it via
    owned_paths and fails when the same shape is unclaimed."""
    root, _ = _foreign_fixture(tmp_path, sweep_env, "foreign-adopt")
    now = time.time()
    # Claimed arm.
    marker = make_marker(root, now + 1, os.getpid())
    _seed_run_manifest(
        root,
        "adopt-claimed",
        marker.name,
        str(root),
        now + 1,
        start_porcelain=["?? docs/tmp/predecessor-output.md"],
        adopted_from="foreign-run-1",
        owned_paths=["docs/tmp/predecessor-output.md"],
    )
    (root / "docs/tmp/predecessor-output.md").write_text("x\n", encoding="utf-8")
    git(root, "add", "-f", "docs/tmp/predecessor-output.md")
    claimed = run_gate("foreign-staging", ctx_for(root))
    assert claimed.rc == 0, claimed.message
    # Unclaimed arm: identical shape, no owned_paths claim.
    marker2 = make_marker(root, now + 2, os.getpid())
    _seed_run_manifest(
        root,
        "adopt-unclaimed",
        marker2.name,
        str(root),
        now + 2,
        start_porcelain=["?? docs/tmp/predecessor-output.md"],
        adopted_from="foreign-run-1",
    )
    unclaimed = run_gate("foreign-staging", ctx_for(root))
    assert unclaimed.rc == 1, unclaimed.message
    assert "docs/tmp/predecessor-output.md" in unclaimed.message


def test_foreign_staging_writer_owned_path_flag(tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys):
    """[class: REPOSITORY_TEST] Writer-side wiring: run the write-manifest
    command with --owned-path and assert the written payload's owned_paths
    equals that list."""
    root = mktemp_repo("owned-flag")
    marker = make_marker(root, time.time(), os.getpid())
    (root / "docs/tmp").mkdir(parents=True, exist_ok=True)
    (root / "docs/tmp/foreign-note.md").write_text("dirt\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    rc = lib.main(["write-manifest", "--claim-none", "--owned-path", "docs/tmp/foreign-note.md"])
    assert rc == 0, capsys.readouterr().err
    done_session = root / "docs/tmp/done-session"
    manifest_path = sorted(done_session.glob("run-manifest-*.json"))[-1]
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["owned_paths"] == ["docs/tmp/foreign-note.md"]


def test_foreign_staging_writer_warns_on_unmatched_claim(tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys):
    """[class: REPOSITORY_TEST] Writer-side warning: given an --owned-path
    claim matching no normalized start-dirt row, expects the writer to emit
    its named warning."""
    root = mktemp_repo("unmatched-claim")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    rc = lib.main(["write-manifest", "--claim-none", "--owned-path", "docs/tmp/never-dirty.md"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "--owned-path claim(s) matching no normalized start-dirt row" in out
    assert "docs/tmp/never-dirty.md" in out


def test_foreign_staging_writer_adopt_composes_owned_paths(tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys):
    """[class: REPOSITORY_TEST] Writer-side adoption composition: a
    write-manifest --adopt invocation with fresh claims over an adopted
    manifest carrying owned_paths writes fresh claims plus adopted claims,
    deduped."""
    root = mktemp_repo("adopt-compose")
    make_marker(root, time.time(), os.getpid())
    (root / "dirt-a.md").write_text("a\n", encoding="utf-8")
    (root / "dirt-b.md").write_text("b\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    assert lib.main(["write-manifest", "--claim-none", "--owned-path", "dirt-a.md"]) == 0
    out = capsys.readouterr().out
    first_id = sorted(
        p.name[len("run-manifest-"):-len(".json")]
        for p in (root / "docs/tmp/done-session").glob("run-manifest-*.json")
    )[0]
    assert first_id in out
    marker2 = make_marker(root, time.time() + 1, os.getpid())
    assert lib.main([
        "write-manifest", "--adopt", first_id,
        "--owned-path", "dirt-b.md",
        "--owned-path", "dirt-a.md",
    ]) == 0
    capsys.readouterr()
    done_session = root / "docs/tmp/done-session"
    second = [
        path
        for path in done_session.glob("run-manifest-*.json")
        if path.name != f"run-manifest-{first_id}.json"
    ]
    assert len(second) == 1
    payload = json.loads(second[0].read_text(encoding="utf-8"))
    assert payload["owned_paths"] == [
        "dirt-b.md",
        "dirt-a.md",
    ]
    # The adopted start-dirt record is unioned with the fresh snapshot.
    assert "?? dirt-a.md" in payload["start_porcelain"]


def test_foreign_staging_degrades_to_warning_skip_without_manifest(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Degradation: given no resolvable run
    manifest, expects a warning-skip result, never a crash and never a
    failure."""
    root = make_repo(tmp_path, "no-manifest")
    write_facts(root)
    now = time.time()
    make_marker(root, now - 1, os.getpid())
    make_marker(root, now, os.getpid())
    result = run_gate("foreign-staging", ctx_for(root))
    assert result.rc == 0
    assert "warning skip" in result.message
    assert result.warnings


# --- plans-archive-twin gate fixtures ------------------------------------- #
def _twin_repo(tmp_path, sweep_env, name: str, facts_text: str | None = None):
    root = make_repo(tmp_path, name, gitignore_docs=True)
    if facts_text is None:
        write_facts(root)
    else:
        facts_dir = root / ".ai-playbook"
        facts_dir.mkdir(parents=True, exist_ok=True)
        (facts_dir / "facts.md").write_text(facts_text, encoding="utf-8")
    return root


def test_plans_archive_twin_fails_on_root_archive_pairs(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a dated plan basename at the plans root
    paired into each state directory (byte-identical, byte-different,
    deferred, rejected), expects gate_plans_archive_twin to fail naming both
    paths; a basename in exactly one location and non-dated root files
    never trigger the gate."""
    root = _twin_repo(tmp_path, sweep_env, "twin-fail")
    plans = root / "docs/history/plans"
    for sub in ("completed", "deferred", "rejected"):
        (plans / sub).mkdir(parents=True)
    (plans / "2026-09-27-twin-a.md").write_text("same\n", encoding="utf-8")
    (plans / "completed/2026-09-27-twin-a.md").write_text("same\n", encoding="utf-8")
    result = run_gate("plans-archive-twin", ctx_for(root))
    assert result.rc == 1, result.message
    assert "docs/history/plans/2026-09-27-twin-a.md" in result.message
    assert "completed" in result.message

    (plans / "2026-09-27-twin-b.md").write_text("root newer bytes\n", encoding="utf-8")
    (plans / "completed/2026-09-27-twin-b.md").write_text("archive older bytes\n", encoding="utf-8")
    (plans / "2026-09-27-twin-c.md").write_text("c\n", encoding="utf-8")
    (plans / "deferred/2026-09-27-twin-c.md").write_text("c\n", encoding="utf-8")
    (plans / "2026-09-27-twin-d.md").write_text("d\n", encoding="utf-8")
    (plans / "rejected/2026-09-27-twin-d.md").write_text("d\n", encoding="utf-8")
    result = run_gate("plans-archive-twin", ctx_for(root))
    assert result.rc == 1, result.message
    for name in ("twin-b", "twin-c", "twin-d"):
        assert f"2026-09-27-{name}.md" in result.message

    # Single-location basenames and non-dated files pass.
    for path in ("completed/2026-09-27-solo.md", "2026-09-27-root-only.md"):
        (plans / path).write_text("solo\n", encoding="utf-8")
    (plans / "README.md").write_text("not dated\n", encoding="utf-8")
    result = run_gate("plans-archive-twin", ctx_for(root))
    assert result.rc == 1  # twins a-d still present


def test_plans_archive_twin_passes_on_clean_tree(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given the current-tree shape (no
    root-plus-archive basename pair), expects a pass."""
    root = _twin_repo(tmp_path, sweep_env, "twin-clean")
    plans = root / "docs/history/plans"
    for sub in ("completed", "deferred", "rejected"):
        (plans / sub).mkdir(parents=True)
    (plans / "2026-09-27-live.md").write_text("live\n", encoding="utf-8")
    (plans / "completed/2026-09-26-archived.md").write_text("archived\n", encoding="utf-8")
    (plans / "README.md").write_text("non-dated\n", encoding="utf-8")
    result = run_gate("plans-archive-twin", ctx_for(root))
    assert result.rc == 0, result.message
    # Non-dated root file never triggers, even with the same basename in an
    # archive state.
    (plans / "completed/README.md").write_text("non-dated twin\n", encoding="utf-8")
    assert run_gate("plans-archive-twin", ctx_for(root)).rc == 0


def test_plans_archive_twin_reads_non_default_completed_dir(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a non-default plans_completed_dir facts
    key, expects the scan to read the configured home."""
    root = _twin_repo(
        tmp_path, sweep_env, "twin-nondefault",
        "```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'plans_completed_dir = "docs/custom-archive/"\n'
        'backlog_dir = "docs/history/backlog/"\n'
        'reviews_dir = "docs/reviews/"\n'
        'tmp_dir = "docs/tmp/"\n'
        "```\n",
    )
    plans = root / "docs/history/plans"
    plans.mkdir(parents=True, exist_ok=True)
    (root / "docs/custom-archive").mkdir(parents=True)
    (plans / "2026-09-27-twin.md").write_text("root\n", encoding="utf-8")
    (root / "docs/custom-archive/2026-09-27-twin.md").write_text("custom\n", encoding="utf-8")
    result = run_gate("plans-archive-twin", ctx_for(root))
    assert result.rc == 1, result.message
    assert "docs/custom-archive/2026-09-27-twin.md" in result.message


def test_plans_archive_twin_warns_on_fallback_and_absent_dirs(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given the completed-dir key unresolvable,
    expects the named fallback warning and a scan of the default home (never
    a failure); given a resolved state directory absent on disk, expects a
    named warning line and a pass, never a silent green."""
    root = _twin_repo(
        tmp_path, sweep_env, "twin-warn",
        "```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'backlog_dir = "docs/history/backlog/"\n'
        'reviews_dir = "docs/reviews/"\n'
        'tmp_dir = "docs/tmp/"\n'
        "```\n",
    )
    (root / "docs/history/plans").mkdir(parents=True, exist_ok=True)
    result = run_gate("plans-archive-twin", ctx_for(root))
    assert result.rc == 0, result.message
    assert any("plans_completed_dir" in w for w in result.warnings)
    assert any("does not exist on disk" in w for w in result.warnings)


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-28-p79-done-closeout-manifest-attribution-
# and-marker-contracts.md, Task 6: mechanical selftest. The six named tests
# below pin the landed closeout contracts (identity round trip, named legacy
# mismatch, marker self-check both polarities, fused ledger interleaving,
# deterministic foreign-candidate emission); every existing test above is
# frozen. The recipe-side tests execute the plan's prescribed snippets
# verbatim in scratch trees, per the plan's assumption that attribution and
# marker placement are recipe-side bash, not lib functions.
# --------------------------------------------------------------------------- #
PRESCRIBED_MARKER_CHECK_BLOCK = r'''# Post-write location self-check: independent fresh parse, resolved-path compare.
TMP_DIR_FRESH="$(sed -n 's/^tmp_dir = ["'\'']\(.*\)["'\'']$/\1/p' "$REPO_TOP/.ai-playbook/facts.md" 2>/dev/null | head -n 1)"
TMP_DIR_FRESH="${TMP_DIR_FRESH:-$REPO_TOP/docs/tmp/}"
case "$TMP_DIR_FRESH" in /*) ;; *) TMP_DIR_FRESH="$REPO_TOP/$TMP_DIR_FRESH";; esac
EXPECTED_ROOT="${TMP_DIR_FRESH%/}/done-session"
EXPECTED_ROOT="$(cd "$EXPECTED_ROOT" 2>/dev/null && pwd)" || EXPECTED_ROOT=""
MARKER_DIR="$(cd "$(dirname "$MARKER")" 2>/dev/null && pwd)" || MARKER_DIR=""
if [ -z "$EXPECTED_ROOT" ] || [ "$MARKER_DIR" != "$EXPECTED_ROOT" ]; then
  rm -f "$MARKER"
  echo "run-start marker: resolved path ${MARKER_DIR:-unresolvable} is not the expected done-session root ${EXPECTED_ROOT:-unresolvable}; stray marker removed" >&2
  exit 1
fi'''

PRESCRIBED_LEDGER_APPEND_LINE = 'git rev-parse HEAD >> "$LEDGER"'


def _plan_prescribed_fence(lead: str) -> str | None:
    """Best-effort provenance cross-check: extract the verbatim fence that
    follows ``lead`` in this plan's markdown record (the plans dir, or the
    completed archive once the plan lands there); None when the record cannot
    be located, so the embedded constants stay the hermetic source of truth."""
    plan_name = (
        "2026-09-28-p79-done-closeout-manifest-attribution-"
        "and-marker-contracts.md"
    )
    for path in sorted(SCRIPTS_DIR.parent.glob(f"docs/history/**/{plan_name}")):
        text = path.read_text(encoding="utf-8")
        start = text.find(lead)
        if start == -1:
            continue
        fence_open = text.find("```\n", start)
        fence_close = text.find("\n```\n", fence_open + 4)
        if fence_open == -1 or fence_close == -1:
            return None
        return text[fence_open + 4 : fence_close]
    return None


def _run_bash_snippet(
    script: str, env_overrides: dict[str, str]
) -> subprocess.CompletedProcess:
    """Run one bash snippet with variables handed over through the
    environment, so the snippet body itself stays byte-verbatim."""
    return subprocess.run(
        ["bash", "-c", script],
        env={**os.environ, **env_overrides},
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_round_trip_writer_to_finalizer(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a fixture repo with a content-bearing
    run-start marker, expects the production writer to emit the 64-hex
    fingerprint root and the finalize path to resolve that same fingerprint
    and mark the run complete in place (one versioned identity contract on
    both sides; the raw root spelling never enters the record)."""
    root = mktemp_repo("roundtrip")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest"]) == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    run_id = manifests[0].name[len("run-manifest-") : -len(".json")]
    assert run_id
    before = json.loads(manifests[0].read_text(encoding="utf-8"))
    fingerprint = before["repo_root"]
    assert fingerprint == root_digest(root)
    assert len(fingerprint) == 64

    assert lib.main(["finalize-manifest", "--run-id", run_id]) == 0
    assert run_id in capsys.readouterr().out
    after = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert after["complete"] is True
    assert after["run_id"] == run_id
    assert after["repo_root"] == fingerprint
    assert after["start_commit"] == before["start_commit"]


def test_legacy_manifest_rejected_with_named_mismatch(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a wrong-version manifest and a
    schema-valid manifest carrying a foreign 64-hex root, expects
    finalize-manifest to abort non-zero on both with the exact
    ``run-manifest identity mismatch`` sentence and to leave each file
    byte-identical (the root arm cannot regress to silent acceptance)."""
    root = mktemp_repo("legacy-mismatch")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    def payload_for(run_id: str, schema: int, repo_root: str) -> dict:
        return {
            "schema": schema,
            "run_id": run_id,
            "marker": marker_name(time.time()),
            "created_epoch": time.time(),
            "repo_root": repo_root,
            "pid": os.getpid(),
            "start_commit": git(root, "rev-parse", "HEAD").stdout.strip(),
            "start_porcelain": [],
            "owned_plan_paths": [],
            "owned_review_paths": [],
            "foreign_review_paths": [],
            "adopted_from": None,
            "complete": False,
        }

    arms = [
        (
            "run-legacy-v2",
            payload_for("run-legacy-v2", 2, root_digest(root)),
            "manifest schema_version 2 repo_root fingerprint",
        ),
        (
            "run-foreign-root",
            payload_for(
                "run-foreign-root",
                1,
                hashlib.sha256(b"/elsewhere/repo").hexdigest(),
            ),
            "manifest schema_version 1 repo_root fingerprint",
        ),
    ]
    for run_id, payload, rendered in arms:
        done_session.mkdir(parents=True, exist_ok=True)
        manifest_path = done_session / f"run-manifest-{run_id}.json"
        manifest_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        before = manifest_path.read_bytes()

        rc = lib.main(["finalize-manifest", "--run-id", run_id])

        assert rc != 0, f"arm {run_id} must abort non-zero"
        err = capsys.readouterr().err
        assert "run-manifest identity mismatch" in err
        assert (
            "run-manifest identity mismatch: " + rendered
            in err
        )
        assert "is not supported by this finalizer" in err
        assert "manifest left unchanged" in err
        assert manifest_path.read_bytes() == before


def test_marker_check_passes_on_correct_derivation(tmp_path):
    """[class: REPOSITORY_TEST] The prescribed Step 0 marker post-write check
    executed verbatim in a scratch tree: with a facts ``tmp_dir`` key the
    block passes and the marker stays under the resolved done-session root,
    and with the facts key absent the documented fallback derivation passes
    the same way (exit 0, no stray removal)."""
    planned = _plan_prescribed_fence("Prescribed marker check block (verbatim):")
    if planned is not None:
        assert planned == PRESCRIBED_MARKER_CHECK_BLOCK

    # Correct derivation: the facts document carries tmp_dir.
    repo_top = tmp_path / "scratch-pass-keyed"
    (repo_top / ".ai-playbook").mkdir(parents=True)
    (repo_top / ".ai-playbook" / "facts.md").write_text(
        "```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'tmp_dir = "docs/tmp/"\n'
        "```\n",
        encoding="utf-8",
    )
    done_session = repo_top / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True)
    marker = done_session / marker_name(time.time())
    marker.write_text(f"{int(time.time())} {repo_top} {os.getpid()}\n", encoding="utf-8")

    proc = _run_bash_snippet(
        PRESCRIBED_MARKER_CHECK_BLOCK,
        {"REPO_TOP": str(repo_top), "MARKER": str(marker)},
    )
    assert proc.returncode == 0, proc.stderr
    assert marker.exists(), "correct derivation must not remove the marker"
    assert "stray marker removed" not in proc.stderr

    # No-facts-key fallback polarity: the key is absent, the documented
    # default derivation applies.
    repo_top_fb = tmp_path / "scratch-pass-fallback"
    (repo_top_fb / ".ai-playbook").mkdir(parents=True)
    (repo_top_fb / ".ai-playbook" / "facts.md").write_text(
        "```toml\n" 'plans_dir = "docs/history/plans/"\n' "```\n",
        encoding="utf-8",
    )
    done_session_fb = repo_top_fb / "docs" / "tmp" / "done-session"
    done_session_fb.mkdir(parents=True)
    marker_fb = done_session_fb / marker_name(time.time())
    marker_fb.write_text(
        f"{int(time.time())} {repo_top_fb} {os.getpid()}\n", encoding="utf-8"
    )

    proc_fb = _run_bash_snippet(
        PRESCRIBED_MARKER_CHECK_BLOCK,
        {"REPO_TOP": str(repo_top_fb), "MARKER": str(marker_fb)},
    )
    assert proc_fb.returncode == 0, proc_fb.stderr
    assert marker_fb.exists(), "fallback polarity must not remove the marker"
    assert "stray marker removed" not in proc_fb.stderr


def test_marker_check_fails_loud_on_corrupted_derivation(tmp_path):
    """[class: REPOSITORY_TEST] The prescribed Step 0 marker post-write check
    executed verbatim in a scratch tree: a marker stray-landed under a
    system-temp anchor and one stray-landed inside the repository both exit
    non-zero naming the resolved stray path against the expected done-session
    root, and no stray marker survives (the check removes it)."""
    def corrupted_arm(repo_top: Path, marker: Path) -> subprocess.CompletedProcess:
        (repo_top / ".ai-playbook").mkdir(parents=True)
        (repo_top / ".ai-playbook" / "facts.md").write_text(
            "```toml\n" 'tmp_dir = "docs/tmp/"\n' "```\n",
            encoding="utf-8",
        )
        (repo_top / "docs" / "tmp" / "done-session").mkdir(parents=True)
        return _run_bash_snippet(
            PRESCRIBED_MARKER_CHECK_BLOCK,
            {"REPO_TOP": str(repo_top), "MARKER": str(marker)},
        )

    # Stray anchored in system temp (a misderived absolute path).
    stray_dir = Path(tempfile.mkdtemp(prefix="stray-marker-"))
    try:
        stray = stray_dir / marker_name(time.time())
        stray.write_text("stray marker body\n", encoding="utf-8")
        proc = corrupted_arm(tmp_path / "scratch-temp-stray", stray)
        assert proc.returncode != 0, proc.stderr
        assert "run-start marker" in proc.stderr
        assert "is not the expected done-session root" in proc.stderr
        assert str(stray_dir) in proc.stderr
        assert "stray marker removed" in proc.stderr
        assert not stray.exists(), "the stray marker must be removed"
    finally:
        shutil.rmtree(stray_dir, ignore_errors=True)

    # Stray anchored inside the repository but outside the done-session root
    # (a misderived relative path).
    repo_top = tmp_path / "scratch-repo-stray"
    notes_dir = repo_top / "docs" / "notes"
    notes_dir.mkdir(parents=True)
    stray_internal = notes_dir / marker_name(time.time())
    stray_internal.write_text("stray marker body\n", encoding="utf-8")
    proc_internal = corrupted_arm(repo_top, stray_internal)
    assert proc_internal.returncode != 0, proc_internal.stderr
    assert "is not the expected done-session root" in proc_internal.stderr
    assert "stray marker removed" in proc_internal.stderr
    assert not stray_internal.exists(), "the stray marker must be removed"


def test_ledger_interleaving_simulation(tmp_path, sweep_env, mktemp_repo):
    """[class: REPOSITORY_TEST] The prescribed fused ledger line executed in a
    scratch git repository: two owned commits each append at their own return
    while a peer worktree's commit lands in between; the ledger holds exactly
    the two owned SHAs in order and the peer sha (which the retired range
    enumeration would have swept from the same branch range) never enters it."""
    planned = _plan_prescribed_fence("Prescribed ledger append line (verbatim")
    if planned is not None:
        assert planned == PRESCRIBED_LEDGER_APPEND_LINE

    root = mktemp_repo("interleaving")
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True)
    ledger = done_session / "owned-commits-run-itl.txt"

    def fused_commit(fname: str, message: str) -> subprocess.CompletedProcess:
        script = (
            "set -e\n"
            'cd "$REPO_TOP"\n'
            f"git add -- {fname}\n"
            f'git commit -m "{message}" -- {fname} && '
            f"{PRESCRIBED_LEDGER_APPEND_LINE}\n"
        )
        return _run_bash_snippet(
            script, {"REPO_TOP": str(root), "LEDGER": str(ledger)}
        )

    # Owned commit one, fused with its append (one shell invocation).
    (root / "owned-one.txt").write_text("owned one\n", encoding="utf-8")
    assert fused_commit("owned-one.txt", "owned one").returncode == 0
    owned_one = git(root, "rev-parse", "HEAD").stdout.strip()
    assert ledger.read_text(encoding="utf-8") == owned_one + "\n"

    # A peer worktree's commit interleaves into the same branch history.
    peer_wt = tmp_path / "peer-wt"
    assert git(root, "worktree", "add", str(peer_wt), "-b", "peer-branch").returncode == 0
    (peer_wt / "peer-note.txt").write_text("peer work\n", encoding="utf-8")
    assert sh(["git", "-C", str(peer_wt), "add", "peer-note.txt"], peer_wt).returncode == 0
    assert sh(
        [
            "git", "-C", str(peer_wt),
            "-c", "user.name=peer-worktree",
            "-c", "user.email=peer@example.invalid",
            "commit", "-m", "peer commit lands mid-run", "-q",
        ],
        peer_wt,
    ).returncode == 0
    assert git(root, "merge", "--ff-only", "peer-branch").returncode == 0
    peer_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    assert peer_sha != owned_one

    # Owned commit two, fused with its append, after the peer landed.
    (root / "owned-two.txt").write_text("owned two\n", encoding="utf-8")
    assert fused_commit("owned-two.txt", "owned two").returncode == 0
    owned_two = git(root, "rev-parse", "HEAD").stdout.strip()

    try:
        assert ledger.read_text(encoding="utf-8").splitlines() == [
            owned_one,
            owned_two,
        ]
        ledger_lines = ledger.read_text(encoding="utf-8").splitlines()
        assert peer_sha not in ledger_lines
        # The interleaving is real: the retired range enumeration over the
        # same branch range would have swept the peer commit in.
        swept = git(root, "rev-list", f"{owned_one}..HEAD").stdout.split()
        assert swept == [owned_two, peer_sha]
    finally:
        git(root, "worktree", "remove", "--force", str(peer_wt))


def test_emit_foreign_candidates_deterministic(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Two ``--emit-foreign-candidates`` invocations
    over the same tree emit byte-identical files, one sorted repo-relative
    path per line; the ``--owned-review`` claimed artifact never appears and
    no manifest is written."""
    root = mktemp_repo("emit-det")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    (root / "docs/reviews").mkdir(parents=True)
    owned_rel = "docs/reviews/2026-09-28-owned-review-r1.md"
    unowned = [
        "docs/reviews/2026-09-28-peer-review-b-r1.md",
        "docs/reviews/2026-09-28-peer-review-a-r1.md",
    ]
    for rel in [owned_rel] + unowned:
        (root / rel).write_text("staging review body\n", encoding="utf-8")
    done_session = root / "docs" / "tmp" / "done-session"
    out1 = tmp_path / "candidates-first.txt"
    out2 = tmp_path / "candidates-second.txt"

    assert lib.main(
        ["write-manifest", "--emit-foreign-candidates", str(out1),
         "--owned-review", owned_rel]
    ) == 0
    assert lib.main(
        ["write-manifest", "--emit-foreign-candidates", str(out2),
         "--owned-review", owned_rel]
    ) == 0

    assert out1.read_bytes() == out2.read_bytes()
    lines = out1.read_text(encoding="utf-8").splitlines()
    assert lines == sorted(lines)
    assert lines == sorted(unowned)
    assert owned_rel not in lines
    assert list(done_session.glob("run-manifest-*.json")) == []


def test_emit_roundtrip_rejects_vertical_tab_ignored_candidate(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] The emit roundtrip abort's ``[\\\\v\\\\f]\\\\.md$``
    term becomes reachable: an ignored reviews-home candidate whose name
    carries a vertical tab immediately before the extension (git emits the
    C-style ``v`` short escape for it in the ignored enumeration, not octal)
    aborts the emit invocation with the named roundtrip error listing it,
    while a control-free ignored candidate still emits."""
    root = mktemp_repo("vt-ignored-roundtrip")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    (root / "docs/reviews").mkdir(parents=True)
    vt_rel = "docs/reviews/2026-09-29-vt-peer-plan-review\x0b.md"
    plain_rel = "docs/reviews/2026-09-29-plain-peer-review-r1.md"
    (root / vt_rel).write_text("peer staging review\n", encoding="utf-8")
    (root / plain_rel).write_text("peer staging review\n", encoding="utf-8")
    done_session = root / "docs" / "tmp" / "done-session"
    out = tmp_path / "candidates.txt"

    rc = lib.main(["write-manifest", "--emit-foreign-candidates", str(out)])
    assert rc != 0
    err = capsys.readouterr().err
    assert "foreign-candidate-roundtrip" in err
    # The abort renders the candidate through the control-stripping
    # sanitizer, so the listed name carries the vertical tab stripped out.
    assert "docs/reviews/2026-09-29-vt-peer-plan-review.md" in err
    assert not out.exists()
    assert list(done_session.glob("run-manifest-*.json")) == []

    # A control-free ignored candidate still emits.
    (root / vt_rel).unlink()
    assert lib.main(["write-manifest", "--emit-foreign-candidates", str(out)]) == 0
    assert out.read_text(encoding="utf-8").splitlines() == [plain_rel]


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-09-28-em-dash-whole-file-gate-added-lines-selection.md
# Task 2: done gate falls back to added-lines on pre-existing violations.
# Fixture em-dash bytes are constructed at run time via the Python source
# escape "\u2014"; a literal U+2014 byte never appears in this source.
# --------------------------------------------------------------------------- #
def copy_em_dash_script(root: Path) -> Path:
    """Copy the repo's real check-no-em-dash.sh into the fixture scripts dir."""
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    target = scripts / "check-no-em-dash.sh"
    target.write_text(
        (SCRIPTS_DIR / "check-no-em-dash.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


def test_em_dash_fallback_preexisting_tracked_passes(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a fixture repo whose tracked prose file
    carries one committed em dash on an unchanged line while the working tree
    adds one clean line to that file, expects the em-dash-scan gate to return
    rc 0 with a message carrying the full baseline row shape
    ``pre-existing (known-violation baseline): <path>:<line>`` for the fixture
    path and line."""
    root = make_repo(tmp_path, "emdash-preexisting", gitignore_docs=True)
    write_facts(root)
    copy_em_dash_script(root)
    prose = root / "notes.md"
    prose.write_text(
        "committed intro\n" + "kept line with \u2014 dash\n", encoding="utf-8"
    )
    git(root, "add", "notes.md")
    git(root, "commit", "-m", "prose with known violation", "-q")
    prose.write_text(
        "committed intro\n"
        + "kept line with \u2014 dash\n"
        + "clean added line\n",
        encoding="utf-8",
    )

    result = run_gate("em-dash-scan", ctx_for(root))

    assert result.rc == 0
    assert "pre-existing (known-violation baseline): notes.md:2" in result.message


def test_em_dash_fallback_untracked_still_fails(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given the same fixture shape but the dirty
    prose path untracked, expects rc 1 naming that path with the reason marker
    ``new prose must be whole-file clean``."""
    root = make_repo(tmp_path, "emdash-untracked", gitignore_docs=True)
    write_facts(root)
    copy_em_dash_script(root)
    (root / "draft.md").write_text(
        "fresh prose with \u2014 dash\n", encoding="utf-8"
    )

    result = run_gate("em-dash-scan", ctx_for(root))

    assert result.rc == 1
    assert "draft.md" in result.message
    assert "new prose must be whole-file clean" in result.message


def test_em_dash_fallback_dirty_added_lines_still_fails(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a tracked file whose working tree adds a
    line carrying an em dash, expects rc 1 naming that path with the reason
    marker ``added-lines`` (the fallback never launders dirty insertions)."""
    root = make_repo(tmp_path, "emdash-dirty", gitignore_docs=True)
    write_facts(root)
    copy_em_dash_script(root)
    prose = root / "prose.md"
    prose.write_text("clean committed line\n", encoding="utf-8")
    git(root, "add", "prose.md")
    git(root, "commit", "-m", "clean prose", "-q")
    prose.write_text(
        "clean committed line\n" + "dirty insertion with \u2014 dash\n",
        encoding="utf-8",
    )

    result = run_gate("em-dash-scan", ctx_for(root))

    assert result.rc == 1
    assert "prose.md" in result.message
    assert "added-lines" in result.message


def test_em_dash_fallback_mixed_hits_fail_untracked(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a fixture repo holding one tracked file
    with a committed dash on an unchanged line (clean added lines) plus one
    untracked prose file carrying a dash, expects rc 1 naming the untracked
    path with the reason marker ``new prose must be whole-file clean``; the
    tracked pre-existing file must not short-circuit the untracked failure."""
    root = make_repo(tmp_path, "emdash-mixed", gitignore_docs=True)
    write_facts(root)
    copy_em_dash_script(root)
    tracked = root / "kept.md"
    tracked.write_text(
        "kept intro\n" + "kept line with \u2014 dash\n", encoding="utf-8"
    )
    git(root, "add", "kept.md")
    git(root, "commit", "-m", "kept prose with known violation", "-q")
    tracked.write_text(
        "kept intro\n" + "kept line with \u2014 dash\n" + "kept clean tail\n",
        encoding="utf-8",
    )
    (root / "fresh.md").write_text(
        "fresh prose with \u2014 dash\n", encoding="utf-8"
    )

    result = run_gate("em-dash-scan", ctx_for(root))

    assert result.rc == 1
    assert "fresh.md" in result.message
    assert "new prose must be whole-file clean" in result.message


def test_em_dash_fallback_many_hits_full_enumeration(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given eleven tracked prose files each carrying
    one committed em dash on an unchanged line while the working tree adds
    only clean lines, expects rc 0 and one baseline row per hitting file in
    the gate message, proving fallback enumeration is not limited to ten hits."""
    root = make_repo(tmp_path, "emdash-many", gitignore_docs=True)
    write_facts(root)
    copy_em_dash_script(root)
    paths = [f"notes-{index:02d}.md" for index in range(11)]
    for rel_path in paths:
        prose = root / rel_path
        prose.write_text(
            "committed intro\n" + "kept line with \u2014 dash\n", encoding="utf-8"
        )
    git(root, "add", *paths)
    git(root, "commit", "-m", "prose with known violations", "-q")
    for rel_path in paths:
        prose = root / rel_path
        prose.write_text(
            "committed intro\n"
            + "kept line with \u2014 dash\n"
            + "clean added line\n",
            encoding="utf-8",
        )

    result = run_gate("em-dash-scan", ctx_for(root))

    expected_rows = [
        f"pre-existing (known-violation baseline): {rel_path}:2"
        for rel_path in paths
    ]
    assert result.rc == 0
    assert [row for row in expected_rows if row in result.message] == expected_rows
    assert result.message.count("pre-existing (known-violation baseline):") == 11


def test_em_dash_partition_property_full_stdout(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Standing canary for the partition property:
    a touched probe whose stdout carries more than ten hits across the
    tracked/untracked split is partitioned completely, never to the
    last-ten tail; every untracked hit is named by the whole-file failure
    and, with the untracked side removed, every tracked hit is classified
    into its own pre-existing baseline row."""
    root = make_repo(tmp_path, "emdash-partition", gitignore_docs=True)
    write_facts(root)
    copy_em_dash_script(root)
    untracked_names = [f"a-fresh-{index:02d}.md" for index in range(12)]
    tracked_names = [f"z-kept-{index:02d}.md" for index in range(4)]
    for name in untracked_names:
        (root / name).write_text(
            "fresh prose with \u2014 dash\n", encoding="utf-8"
        )
    for name in tracked_names:
        prose = root / name
        prose.write_text(
            "committed intro\n" + "kept line with \u2014 dash\n", encoding="utf-8"
        )
    git(root, "add", *tracked_names)
    git(root, "commit", "-m", "kept prose with known violations", "-q")
    for name in tracked_names:
        prose = root / name
        prose.write_text(
            "committed intro\n"
            + "kept line with \u2014 dash\n"
            + "clean added line\n",
            encoding="utf-8",
        )

    result = run_gate("em-dash-scan", ctx_for(root))

    assert result.rc == 1
    assert "new prose must be whole-file clean" in result.message
    for name in untracked_names:
        assert name in result.message

    # The tracked side of the split classifies completely too: with the
    # untracked hits gone, every tracked hit lands its own baseline row.
    for name in untracked_names:
        (root / name).unlink()
    tracked_result = run_gate("em-dash-scan", ctx_for(root))
    assert tracked_result.rc == 0
    assert (
        tracked_result.message.count("pre-existing (known-violation baseline):")
        == 4
    )
    for name in tracked_names:
        assert (
            f"pre-existing (known-violation baseline): {name}:2"
            in tracked_result.message
        )


def test_em_dash_ls_files_failure_treats_hits_untracked(
    tmp_path, sweep_env, monkeypatch
):
    """[class: REPOSITORY_TEST] Fail-closed polarity: when the
    ``ls-files --others --exclude-standard`` untracked probe fails, every hit
    is treated as untracked and fails whole-file with the untracked marker,
    and none is adjudicated into a pre-existing baseline row (a tracking
    outage must never launder hits through the tracked arm)."""
    root = make_repo(tmp_path, "emdash-lsfiles-failure", gitignore_docs=True)
    write_facts(root)
    copy_em_dash_script(root)
    prose = root / "kept.md"
    prose.write_text(
        "committed intro\n" + "kept line with \u2014 dash\n", encoding="utf-8"
    )
    git(root, "add", "kept.md")
    git(root, "commit", "-m", "kept prose with known violation", "-q")
    prose.write_text(
        "committed intro\n" + "kept line with \u2014 dash\n" + "clean added line\n",
        encoding="utf-8",
    )
    ctx = ctx_for(root)
    real_git = ctx.git

    def failing_untracked_probe(*args, **kwargs):
        if args and args[0] == "ls-files":
            return subprocess.CompletedProcess(
                list(args), 1, stdout="", stderr="fatal: stub ls-files failure"
            )
        return real_git(*args, **kwargs)

    monkeypatch.setattr(ctx, "git", failing_untracked_probe)

    result = run_gate("em-dash-scan", ctx)

    assert result.rc == 1
    assert "new prose must be whole-file clean" in result.message
    assert "kept.md" in result.message
    assert "pre-existing (known-violation baseline)" not in result.message


def test_docs_tmp_sweep_keeps_baseline_holding_archived_session(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An archived-plan execute-plan session still
    holding its captured closeout-baseline.json (regular file) survives the
    sweep with the kept witness rendered in the gate message; a baseline-less
    archived session is still removed; a pending-plan session holding a
    baseline keeps the active: reason (the two exemptions never collide)."""
    root = make_repo(tmp_path, "sweep-baseline", gitignore_docs=True)
    write_facts(root)
    plans_dir = root / "docs/history/plans"
    completed_dir = root / "docs/history/plans/completed"
    plans_dir.mkdir(parents=True)
    completed_dir.mkdir(parents=True)
    arch_plan = "2026-09-30-archived-baseline-plan.md"
    live_plan = "2026-09-30-live-baseline-plan.md"
    (completed_dir / arch_plan).write_text("archived\n", encoding="utf-8")
    (plans_dir / live_plan).write_text("live\n", encoding="utf-8")
    tmp_dir = root / "docs/tmp"
    holder = tmp_dir / "execute-plan" / arch_plan[:-3]
    holder.mkdir(parents=True)
    (holder / "closeout-baseline.json").write_text("{}\n", encoding="utf-8")
    (holder / "task-1-implement.log.md").write_text("log\n", encoding="utf-8")
    bare = tmp_dir / "execute-plan" / "2026-09-30-archived-bare-plan.md"
    bare.mkdir(parents=True)
    (bare / "manifest.md").write_text("stale\n", encoding="utf-8")
    (completed_dir / "2026-09-30-archived-bare-plan.md").write_text("archived\n", encoding="utf-8")
    pending_holder = tmp_dir / "execute-plan" / live_plan[:-3]
    pending_holder.mkdir(parents=True)
    (pending_holder / "closeout-baseline.json").write_text("{}\n", encoding="utf-8")
    write_manifest(root, live_plan[:-3], fresh_iso())

    result = run_gate("docs-tmp-sweep", ctx_for(root))
    assert result.rc == 0
    assert holder.exists() and (holder / "closeout-baseline.json").is_file()
    assert (holder / "task-1-implement.log.md").exists(), "baseline-holding session survives whole"
    assert not bare.exists(), "baseline-less archived session still removed"
    assert pending_holder.exists()
    assert "closeout baseline present" in result.message, result.message
    assert "transfer-out may be pending" in result.message, result.message
    assert "(active: plan still pending)" in result.message, result.message


def test_docs_tmp_sweep_stale_baseline_archived_session_removed(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An archived-plan execute-plan session whose
    closeout-baseline.json is backdated beyond the grace window (os.utime to
    three days ago, 72h > 48h) no longer lingers: the sweep removes the
    whole directory, including the session manifest the interrupted-run
    report would otherwise keep surfacing, and the gate message names the
    stale closeout baseline as the removal reason."""
    root = make_repo(tmp_path, "sweep-stale-baseline", gitignore_docs=True)
    write_facts(root)
    plans_dir = root / "docs/history/plans"
    completed_dir = root / "docs/history/plans/completed"
    plans_dir.mkdir(parents=True)
    completed_dir.mkdir(parents=True)
    arch_plan = "2026-09-30-archived-stale-baseline-plan.md"
    (completed_dir / arch_plan).write_text("archived\n", encoding="utf-8")
    tmp_dir = root / "docs/tmp"
    stale = tmp_dir / "execute-plan" / arch_plan[:-3]
    stale.mkdir(parents=True)
    (stale / "closeout-baseline.json").write_text("{}\n", encoding="utf-8")
    (stale / "manifest.md").write_text("stale run manifest\n", encoding="utf-8")
    stale_epoch = time.time() - 72 * 3600
    os.utime(stale / "closeout-baseline.json", (stale_epoch, stale_epoch))

    result = run_gate("docs-tmp-sweep", ctx_for(root))
    assert result.rc == 0
    assert not stale.exists(), "stale closeout baseline no longer keeps the directory"
    assert "(stale closeout baseline)" in result.message, result.message


@unittest.skipIf(os.getuid() == 0, "root ignores chmod")
def test_docs_tmp_sweep_stale_baseline_removal_failure_reported(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An archived-plan execute-plan session whose
    closeout-baseline.json is backdated 72h (beyond the 48h grace) but whose
    session directory is undeletable (chmod 0o500) exercises the stale
    branch's OSError path: the gate message carries the dedicated
    ``(stale closeout baseline removal-failed)`` row in the removed section
    (not a kept row) and the directory survives for a retry."""
    root = make_repo(tmp_path, "sweep-stale-removal-failed", gitignore_docs=True)
    write_facts(root)
    plans_dir = root / "docs/history/plans"
    completed_dir = root / "docs/history/plans/completed"
    plans_dir.mkdir(parents=True)
    completed_dir.mkdir(parents=True)
    arch_plan = "2026-09-30-archived-stale-baseline-undeleter-plan.md"
    (completed_dir / arch_plan).write_text("archived\n", encoding="utf-8")
    tmp_dir = root / "docs/tmp"
    stale = tmp_dir / "execute-plan" / arch_plan[:-3]
    stale.mkdir(parents=True)
    (stale / "closeout-baseline.json").write_text("{}\n", encoding="utf-8")
    stale_epoch = time.time() - 72 * 3600
    os.utime(stale / "closeout-baseline.json", (stale_epoch, stale_epoch))
    os.chmod(stale, 0o500)
    try:
        result = run_gate("docs-tmp-sweep", ctx_for(root))
        assert result.rc == 0
        assert stale.exists(), "removal-failed directory survives the failed rmtree"
        assert "(stale closeout baseline removal-failed)" in result.message, (
            result.message
        )
        assert "(removal failed)" not in result.message, (
            "failing stale removal must not degrade to a kept row"
        )
    finally:
        os.chmod(stale, 0o755)


def test_docs_tmp_sweep_fresh_baseline_archived_session_kept(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An archived-plan execute-plan session whose
    closeout-baseline.json is only one hour old (1h <= 48h grace) keeps the
    transfer-out-pending exemption: the directory survives whole and the
    gate message carries the unchanged kept wording."""
    root = make_repo(tmp_path, "sweep-fresh-baseline", gitignore_docs=True)
    write_facts(root)
    plans_dir = root / "docs/history/plans"
    completed_dir = root / "docs/history/plans/completed"
    plans_dir.mkdir(parents=True)
    completed_dir.mkdir(parents=True)
    arch_plan = "2026-09-30-archived-fresh-baseline-plan.md"
    (completed_dir / arch_plan).write_text("archived\n", encoding="utf-8")
    tmp_dir = root / "docs/tmp"
    fresh = tmp_dir / "execute-plan" / arch_plan[:-3]
    fresh.mkdir(parents=True)
    (fresh / "closeout-baseline.json").write_text("{}\n", encoding="utf-8")
    fresh_epoch = time.time() - 3600
    os.utime(fresh / "closeout-baseline.json", (fresh_epoch, fresh_epoch))

    result = run_gate("docs-tmp-sweep", ctx_for(root))
    assert result.rc == 0
    assert fresh.exists() and (fresh / "closeout-baseline.json").is_file()
    assert "(kept: closeout baseline present; transfer-out may be pending)" in result.message, result.message


# --------------------------------------------------------------------------- #
# Plan checkbox: visibility-scoped sensitive-data scan contract
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def _write_facts_with_visibility(root: Path, declaration: str | None) -> Path:
    """Repo facts file in the production TOML-fence form, optionally carrying
    the artifact_visibility declaration inside the fence (the only block
    facts_paths.resolve_toml_key_raw parses)."""
    facts_dir = root / ".ai-playbook"
    facts_dir.mkdir(parents=True, exist_ok=True)
    facts = facts_dir / "facts.md"
    lines = [
        "```toml\n",
        'plans_dir = "docs/history/plans/"\n',
        'plans_completed_dir = "docs/history/plans/completed/"\n',
        'backlog_dir = "docs/history/backlog/"\n',
        'reviews_dir = "docs/reviews/"\n',
        'tmp_dir = "docs/tmp/"\n',
    ]
    if declaration is not None:
        lines.append(declaration + "\n")
    lines.append("```\n")
    facts.write_text("".join(lines), encoding="utf-8")
    return facts


def _visibility_fixture(tmp_path: Path, name: str, declaration: str | None):
    """Scratch repo with a committed Jira-link file, an untracked Jira-link
    file, and a separate credential-bearing control file."""
    root = make_repo(tmp_path, name, gitignore_docs=True)
    _write_facts_with_visibility(root, declaration)
    link = root / "service-link.md"
    link.write_text(
        "see https://company.atlassian.net/browse/TEAM-123\n",
        encoding="utf-8",
    )
    git(root, "add", "service-link.md")
    git(root, "commit", "-m", "add service link", "-q")
    (root / "untracked-link.md").write_text(
        "also https://company.atlassian.net/browse/TEAM-456\n",
        encoding="utf-8",
    )
    (root / "credential-control.txt").write_text(
        'api_key = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8"
    )
    return root


def test_visibility_scoped_private_repo_passes_valid_service_link(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A repository declaring
    artifact_visibility = "private" passes valid internal service links
    through both the staged and the untracked content arms; the credential
    control is absent, so the gate returns rc 0."""
    root = _visibility_fixture(
        tmp_path, "private-link", 'artifact_visibility = "private"'
    )
    (root / "credential-control.txt").unlink()
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 0, result.message


def test_visibility_scoped_undeclared_repo_keeps_strict_default(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Without the declaration the Jira-link file
    fails rc 1 exactly as today, naming the atlassian pattern."""
    root = _visibility_fixture(tmp_path, "undeclared-link", None)
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "\\.atlassian\\.net" in result.message


def test_visibility_scoped_public_declaration_keeps_strict_default(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] An explicit artifact_visibility = "public"
    keeps today's strict behavior for the same link."""
    root = _visibility_fixture(
        tmp_path, "public-link", 'artifact_visibility = "public"'
    )
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "\\.atlassian\\.net" in result.message


def test_visibility_scoped_private_repo_still_fails_credentials(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] With the private declaration, credential
    material alone still fails rc 1."""
    root = _visibility_fixture(
        tmp_path, "private-cred", 'artifact_visibility = "private"'
    )
    (root / "untracked-link.md").unlink()
    git(root, "add", "credential-control.txt")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "credential-control.txt" in result.message


def test_visibility_scoped_families_partition_the_old_constant():
    """[class: REPOSITORY_TEST] The two family constants exist, are disjoint,
    and their union equals the seven patterns of today's DIFF_CONTENT_PATTERNS."""
    old = [
        r"/Users/",
        r"/home/",
        r"\.atlassian\.net",
        r"@[a-z]+\.(com|io|net)",
        r"(?i)\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}",
        r"(?i)\b(?:access|auth|claim|policy|refresh|session)?[_-]?token\s*[:=]\s*['\"]?[A-Za-z0-9._+/=-]{8,}",
        r"(?i)\b(?:password|secret)\s*[:=]\s*\S+",
    ]
    cred = set(lib.CREDENTIAL_CONTENT_PATTERNS)
    pub = set(lib.PUBLIC_ARTIFACT_CONTENT_PATTERNS)
    assert not (cred & pub), "families overlap"
    assert cred | pub == set(old), "old set not fully partitioned"


# --------------------------------------------------------------------------- #
# Plan checkbox: review-staging sidecar-kind validation contract
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_review_staging_sidecar_candidate_validates_markdown_twin(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] A manifest-owned .stats.json sidecar candidate
    is validated through its markdown twin: the stub invocation log names the
    .md twin and never the .stats.json path, and the gate passes."""
    root = mktemp_repo("sidecar-twin")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    sidecar_rel = "docs/reviews/2026-09-30-own-review-r1.stats.json"
    twin_rel = "docs/reviews/2026-09-30-own-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True, exist_ok=True)
    (root / sidecar_rel).write_text("{}\n", encoding="utf-8")
    (root / twin_rel).write_text("owned staging review\n", encoding="utf-8")
    _seed_run_manifest(
        root, "run-sidecar", current.name, str(root), now,
        owned_review_paths=[sidecar_rel],
    )
    stub_log = tmp_path / "sidecar-twin-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    invocations = stub_log.read_text(encoding="utf-8")
    assert twin_rel in invocations
    assert sidecar_rel not in invocations


def test_review_staging_sidecar_candidate_missing_twin_fails_closed(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A manifest-owned .stats.json sidecar whose
    markdown twin is absent fails the gate naming the sidecar."""
    root = mktemp_repo("sidecar-orphan")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    sidecar_rel = "docs/reviews/2026-09-30-own-review-r1.stats.json"
    (root / "docs/reviews").mkdir(parents=True, exist_ok=True)
    (root / sidecar_rel).write_text("{}\n", encoding="utf-8")
    _seed_run_manifest(
        root, "run-sidecar-orphan", current.name, str(root), now,
        owned_review_paths=[sidecar_rel],
    )

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 1
    assert sidecar_rel in result.message


def test_review_staging_markdown_candidate_validated_directly(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] A manifest-owned plain .md staging doc is
    validated directly (the branch must not misroute markdown)."""
    root = mktemp_repo("markdown-direct")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    owned_rel = "docs/reviews/2026-09-30-own-review-r1.md"
    (root / "docs/reviews").mkdir(parents=True, exist_ok=True)
    (root / owned_rel).write_text("owned staging review\n", encoding="utf-8")
    _seed_run_manifest(
        root, "run-md", current.name, str(root), now,
        owned_review_paths=[owned_rel],
    )
    stub_log = tmp_path / "markdown-direct-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    invocations = stub_log.read_text(encoding="utf-8")
    assert owned_rel in invocations


# --------------------------------------------------------------------------- #
# Plan checkbox: test_description_length_gate  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_description_length_gate(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] The description-length gate fails rc 1
    naming an over-cap fixture skill and passes rc 0 on an under-cap tree
    (the checker is copied repo-local into each fixture so the deployment
    -gap path is not exercised here)."""
    # Over-cap fixture skill.
    root = make_repo(tmp_path, "desc-over", gitignore_docs=True)
    write_facts(root)
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy(SCRIPTS_DIR / "check_skill_description_length.py", scripts / "check_skill_description_length.py")
    skill_dir = root / "agents" / "skills" / "overcap"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: overcap\ndescription: " + "x" * 1025 + "\n---\n\nbody\n",
        encoding="utf-8",
    )
    result = run_gate("description-length", ctx_for(root))
    assert result.rc == 1
    assert "overcap" in result.message
    assert "1025" in result.message

    # Under-cap tree.
    root2 = make_repo(tmp_path, "desc-under", gitignore_docs=True)
    write_facts(root2)
    scripts2 = root2 / "scripts"
    scripts2.mkdir(parents=True, exist_ok=True)
    shutil.copy(SCRIPTS_DIR / "check_skill_description_length.py", scripts2 / "check_skill_description_length.py")
    under = root2 / "agents" / "skills" / "fine"
    under.mkdir(parents=True)
    (under / "SKILL.md").write_text(
        "---\nname: fine\ndescription: short\n---\n\nbody\n",
        encoding="utf-8",
    )
    result2 = run_gate("description-length", ctx_for(root2))
    assert result2.rc == 0, result2.message


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-
# gate-sweep.md, Task 1: archive-ceremony gate (checkbox check) in the
# pre-commit phase.
# --------------------------------------------------------------------------- #
def _staged_plan_archive(root: Path, plan_name: str, body: str) -> str:
    """Commit a tracked plan under the plans home (the fixture gitignores
    /docs/, hence the forced add), then stage its rename into the completed
    archive directory; returns the archive path (repo-relative). This is the
    same-run staged-rename archive shape the gate's derivation reads."""
    plans = root / "docs" / "history" / "plans"
    (plans / "completed").mkdir(parents=True, exist_ok=True)
    plan_rel = f"docs/history/plans/{plan_name}"
    (root / plan_rel).write_text(body, encoding="utf-8")
    git(root, "add", "-f", plan_rel)
    git(root, "commit", "-m", "plan", "-q")
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    assert git(root, "mv", plan_rel, archive_rel).returncode == 0
    return archive_rel


def _committed_plan_archive(root: Path, plan_name: str, body: str) -> str:
    """Commit a tracked plan, then commit its rename into the completed
    archive directory (a committed archive rename); returns the archive path.
    The caller seeds the active run manifest first so the rename sits inside
    the manifest's start_commit..HEAD window."""
    (root / "docs" / "history" / "plans" / "completed").mkdir(
        parents=True, exist_ok=True
    )
    plan_rel = f"docs/history/plans/{plan_name}"
    (root / plan_rel).write_text(body, encoding="utf-8")
    git(root, "add", "-f", plan_rel)
    git(root, "commit", "-m", "plan", "-q")
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    assert git(root, "mv", plan_rel, archive_rel).returncode == 0
    assert git(root, "commit", "-m", "archive the plan", "-q").returncode == 0
    return archive_rel


def _write_exec_review_record(root: Path, plan_name: str) -> Path:
    """A minimal exec-review staging doc for a fixture plan, named per the
    slug convention the archive-ceremony coverage arm requires (the plan's
    stem minus its leading date prefix inside a ``-plan-review-`` series
    name ending ``-exec-r<N>``)."""
    stem = plan_name[: -len(".md")] if plan_name.endswith(".md") else plan_name
    slug = stem.split("-", 3)[3] if stem[:4].isdigit() else stem
    reviews = root / "docs" / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    record = reviews / f"2026-10-01-plan-review-{slug}-exec-r1.md"
    record.write_text(
        "# Exec review r1\n\nVerdict: ready=yes, zero blocking.\n",
        encoding="utf-8",
    )
    return record


def test_archive_checkbox_gate_refuses_unchecked_archive(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a staged-rename plan archive whose bytes
    still carry unchecked task boxes, expects the archive-ceremony gate to
    fail rc 1 naming the archive path, the unchecked count, and both sanctioned
    exits (check the boxes after verified work, or a marked backfill
    completion record per the archive-correction exception)."""
    root = make_repo(tmp_path, "ceremony-unchecked", gitignore_docs=True)
    write_facts(root)
    body = "# Plan: demo\n\n## Tasks\n\n- [ ] one\n- [ ] two\n"
    archive_rel = _staged_plan_archive(
        root, "2026-09-30-ceremony-demo.md", body
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert archive_rel in result.message
    assert "2 unchecked task box(es)" in result.message
    assert "check the boxes" in result.message
    assert "backfill completion record" in result.message


def test_archive_checkbox_gate_passes_checked_or_backfilled(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Sanctioned-exit arms: a fully checked staged
    archive passes; a backfill-marked archive (boxes checked with per-checkbox
    backfill markings plus a marked backfill completion record) passes; a
    committed rename archive whose HEAD bytes are fully checked passes; and a
    stale plan-deliverables line whose archive twin at HEAD is fully checked
    passes."""
    # Arm 1: fully checked staged-rename archive (its exec-review record of
    # record present, so the coverage arm stays green too).
    root = make_repo(tmp_path, "ceremony-checked", gitignore_docs=True)
    write_facts(root)
    _write_exec_review_record(root, "2026-09-30-ceremony-ok.md")
    _staged_plan_archive(
        root, "2026-09-30-ceremony-ok.md", "# Plan: ok\n\n- [x] done\n"
    )
    result = run_gate("archive-ceremony", ctx_for(root))
    assert result.rc == 0, result.message

    # Arm 2: backfill-marked archive (no unchecked box remains; the record
    # documents the evidence and the markings license the body edit).
    root2 = make_repo(tmp_path, "ceremony-backfilled", gitignore_docs=True)
    write_facts(root2)
    _write_exec_review_record(root2, "2026-09-30-ceremony-backfill.md")
    body2 = (
        "# Plan: backfilled\n\n"
        "- [x] done (backfilled 2026-10-01)\n\n"
        "## Completion record (backfill 2026-10-01)\n\n"
        "The contemporaneous record was lost with the executing worktree; "
        "re-verification evidence: every validation command re-run green.\n"
    )
    _staged_plan_archive(root2, "2026-09-30-ceremony-backfill.md", body2)
    result2 = run_gate("archive-ceremony", ctx_for(root2))
    assert result2.rc == 0, result2.message

    # Arm 3: committed rename since the active run manifest's start_commit
    # (the rename-detecting name-status arm), HEAD bytes fully checked; plus
    # the stale deliverables line whose archive twin at HEAD is checked (the
    # plan path itself no longer exists on disk).
    root3 = make_repo(tmp_path, "ceremony-committed", gitignore_docs=True)
    write_facts(root3)
    now = time.time()
    marker = make_marker(root3, now, os.getpid())
    _seed_run_manifest(root3, "ceremony-run", marker.name, str(root3), now)
    _write_exec_review_record(root3, "2026-09-30-ceremony-committed.md")
    archive_rel3 = _committed_plan_archive(
        root3,
        "2026-09-30-ceremony-committed.md",
        "# Plan: committed\n\n- [x] done\n",
    )
    result3 = run_gate("archive-ceremony", ctx_for(root3))
    assert result3.rc == 0, result3.message
    stale_rel = "docs/history/plans/2026-09-30-ceremony-committed.md"
    assert not (root3 / stale_rel).exists()
    write_deliverables(root3, [stale_rel])
    result4 = run_gate("archive-ceremony", ctx_for(root3))
    assert result4.rc == 0, result4.message
    assert archive_rel3 in result4.message


def test_committed_archive_refuses_unchecked_box(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a committed-rename plan archive (clean
    tree, so no staged or worktree rename exists; the rename sits inside the
    active run manifest's start_commit..HEAD window) whose HEAD bytes carry
    one unchecked task box, expects the archive-ceremony gate to fail rc 1
    naming the archive path, the unchecked count, and both sanctioned exits
    (check the boxes after verified work, or a marked backfill completion
    record per the archive-correction exception). The fixture pins
    single-shape reachability: with the shape's input removed (the manifest
    reseeded with start_commit
    at HEAD, so the committed-rename window covers nothing) the refusal
    disappears (rc 0), and with the manifest restored and the box flipped to
    checked the gate returns rc 0 with the archive still surfaced (the pass
    arm pins the checked-archives path for this shape alone)."""
    root = make_repo(
        tmp_path, "ceremony-committed-unchecked", gitignore_docs=True
    )
    write_facts(root)
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, "ceremony-run", marker.name, str(root), now)
    _write_exec_review_record(root, "2026-09-30-ceremony-committed.md")
    body = "# Plan: committed\n\n## Tasks\n\n- [ ] one\n"
    archive_rel = _committed_plan_archive(
        root, "2026-09-30-ceremony-committed.md", body
    )
    # The committed-rename window must hold exactly the archive rename: a
    # start_commit older than the plan commit turns the base..HEAD tree diff
    # into a plain add row (rename detection pairs deletions with additions,
    # and the plan path does not exist on the old side), so the boundary is
    # reseeded at the post-plan, pre-rename commit (HEAD~1) through the same
    # run-manifest seeding machinery.
    boundary = git(root, "rev-parse", "HEAD~1").stdout.strip()
    manifest_path = _seed_run_manifest(
        root, "ceremony-run", marker.name, str(root), now,
        start_commit=boundary,
    )
    manifest_bytes = manifest_path.read_bytes()

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert archive_rel in result.message
    assert "1 unchecked task box(es)" in result.message
    assert "check the boxes" in result.message
    assert "backfill completion record" in result.message

    # Single-shape reachability witness: reseed the SAME run id (the write
    # overwrites the manifest file, sidestepping the loader's
    # newest-created_epoch selection) with start_commit at HEAD, so the
    # committed-rename window covers nothing and the refusal disappears.
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    _seed_run_manifest(
        root, "ceremony-run", marker.name, str(root), now, start_commit=head
    )
    result2 = run_gate("archive-ceremony", ctx_for(root))
    assert result2.rc == 0, result2.message

    # Pass arm: restore the snapshotted manifest bytes (the rename sits back
    # inside the window) and flip the archived body's box to checked; the
    # gate returns rc 0 with the committed-rename shape fully present.
    manifest_path.write_bytes(manifest_bytes)
    (root / archive_rel).write_text(
        body.replace("- [ ]", "- [x]"), encoding="utf-8"
    )
    git(root, "add", "-f", archive_rel)
    assert git(root, "commit", "-m", "check the box", "-q").returncode == 0
    result3 = run_gate("archive-ceremony", ctx_for(root))
    assert result3.rc == 0, result3.message
    assert archive_rel in result3.message


def test_stale_deliverables_archive_refuses_unchecked_twin(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a stale plan-deliverables line whose
    recorded top-level plan path no longer exists because the plan now sits
    archived (the rename committed BEFORE the active run manifest's
    start_commit, so it sits outside the committed-rename window) and whose
    archive twin at HEAD carries one unchecked task box, expects the
    archive-ceremony gate to fail rc 1 naming the archive twin path and the
    unchecked count. The fixture pins single-shape reachability: with the
    shape's input removed (the deliverables file rewritten without the
    stale line) the
    refusal disappears (rc 0), and with the line restored and the twin's box
    flipped to checked at HEAD the gate returns rc 0 with the twin still
    surfaced (the pass arm pins the checked-archives path for this shape
    alone)."""
    root = make_repo(
        tmp_path, "ceremony-stale-unchecked", gitignore_docs=True
    )
    write_facts(root)
    plan_name = "2026-09-30-ceremony-stale.md"
    stale_rel = f"docs/history/plans/{plan_name}"
    body = "# Plan: stale\n\n## Tasks\n\n- [ ] one\n"
    twin_rel = _committed_plan_archive(root, plan_name, body)
    # One later commit, then the run manifest seeded at it: the rename sits
    # outside the committed-rename window (start..HEAD covers nothing), so
    # only the stale-deliverables shape can derive the archive.
    assert git(root, "commit", "--allow-empty", "-m", "session work", "-q").returncode == 0
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root, "ceremony-run", marker.name, str(root), now,
        start_commit=git(root, "rev-parse", "HEAD").stdout.strip(),
    )
    assert not (root / stale_rel).exists()
    write_deliverables(root, [stale_rel])
    _write_exec_review_record(root, plan_name)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert twin_rel in result.message
    assert "1 unchecked task box(es)" in result.message

    # Single-shape reachability witness: rewrite the deliverables file
    # without the stale line; no shape derives the archive and the refusal
    # disappears.
    write_deliverables(root, [])
    result2 = run_gate("archive-ceremony", ctx_for(root))
    assert result2.rc == 0, result2.message

    # Pass arm: restore the stale line and flip the archived twin's box to
    # checked (amending the twin at HEAD); the gate returns rc 0 with the
    # stale-deliverables shape fully present.
    write_deliverables(root, [stale_rel])
    (root / twin_rel).write_text(
        body.replace("- [ ]", "- [x]"), encoding="utf-8"
    )
    git(root, "add", "-f", twin_rel)
    assert git(root, "commit", "--amend", "-m", "session work", "-q").returncode == 0
    result3 = run_gate("archive-ceremony", ctx_for(root))
    assert result3.rc == 0, result3.message
    assert twin_rel in result3.message


def test_archive_ceremony_gate_requires_exec_review(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given a derived archive whose boxes are fully
    checked and no exec-review record under the reviews home, expects the
    archive-ceremony gate to fail rc 1 naming the plan, the missing
    ``-plan-review-<slug>-exec-r<N>`` series, and the reconstruction remedy;
    adding a minimal ``-exec-r1`` staging doc whose name follows the slug
    convention turns the gate green."""
    root = make_repo(tmp_path, "ceremony-review", gitignore_docs=True)
    write_facts(root)
    archive_rel = _staged_plan_archive(
        root, "2026-09-30-ceremony-reviewed.md", "# Plan: reviewed\n\n- [x] done\n"
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert archive_rel in result.message
    assert "ceremony-reviewed" in result.message  # the plan's slug
    assert "-plan-review-" in result.message
    assert "-exec-r" in result.message
    assert "reconstruction" in result.message

    reviews = root / "docs" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "2026-10-01-plan-review-ceremony-reviewed-exec-r1.md").write_text(
        "# Exec review r1\n\nVerdict: ready=yes, zero blocking.\n",
        encoding="utf-8",
    )

    result2 = run_gate("archive-ceremony", ctx_for(root))

    assert result2.rc == 0, result2.message
    assert archive_rel in result2.message


# --------------------------------------------------------------------------- #
# execute-plan-closeout gate fixtures and witnesses
# (plan docs/history/plans/2026-10-01-execute-plan-squash-closeout-
# finalization.md, Tasks 1 and 2). The shared builder seeds a landed-
# complete run: an archived plan with one closed promoted origin, the
# ownership registry row, a done-run manifest owning the plan, and the
# execute-plan session state carrying a receipt whose digest binds the
# archived bytes.
# --------------------------------------------------------------------------- #
CLOSEOUT_SLUG = "2026-10-01-closeout-demo"
CLOSEOUT_ACTIVE_REL = f"docs/history/plans/{CLOSEOUT_SLUG}.md"
CLOSEOUT_ARCHIVED_REL = f"docs/history/plans/completed/{CLOSEOUT_SLUG}.md"
CLOSEOUT_ORIGIN_NAME = "2026-10-01-closeout-origin.md"
CLOSEOUT_ORIGIN_OPEN_REL = f"docs/history/backlog/{CLOSEOUT_ORIGIN_NAME}"
CLOSEOUT_ORIGIN_CLOSED_REL = (
    f"docs/history/backlog/completed/{CLOSEOUT_ORIGIN_NAME}"
)
CLOSEOUT_REGISTRY_REL = "docs/maintenance/document-registry.md"

CLOSEOUT_PLAN_TEXT = (
    "# Execute-plan closeout demo plan\n\n"
    "Backlog origin: `docs/history/backlog/2026-10-01-closeout-origin.md`\n\n"
    "### Task 1: land the gate\n\n"
    "- [x] task one\n"
)


@pytest.fixture
def closeout_origins_script(monkeypatch):
    """Point the gate's origins-checker seam at the repo's real script
    (the hermetic convention: repo-owned validators, fixture facts)."""
    monkeypatch.setenv(
        "CHECK_PLAN_ORIGINS_CLOSED_SCRIPT",
        str(SCRIPTS_DIR / "check_plan_origins_closed.py"),
    )


def _closeout_repo(tmp_path, name: str) -> Path:
    """The landed-complete fixture repo: archived plan, closed origin under
    the backlog completed archive, and the ownership registry row."""
    root = make_repo(tmp_path, name, gitignore_docs=True)
    write_facts(root)
    archived = root / CLOSEOUT_ARCHIVED_REL
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text(CLOSEOUT_PLAN_TEXT, encoding="utf-8")
    closed_origin = root / CLOSEOUT_ORIGIN_CLOSED_REL
    closed_origin.parent.mkdir(parents=True, exist_ok=True)
    closed_origin.write_text(
        "origin disposition: folded into the archived plan\n",
        encoding="utf-8",
    )
    registry = root / CLOSEOUT_REGISTRY_REL
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        "<!-- Document ownership registry fixture -->\n\n"
        "| identity | sot | state | archived | reason | src | successor"
        " | aliases | audit |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        f"| closeout-demo | no | completed | 2026-10-01 | executed |"
        f" {CLOSEOUT_ARCHIVED_REL} |  |  | user-approved |\n",
        encoding="utf-8",
    )
    return root


def _closeout_receipt(root: Path) -> dict:
    archived = root / CLOSEOUT_ARCHIVED_REL
    return {
        "workflow_state": "complete",
        "archived_plan_path": CLOSEOUT_ARCHIVED_REL,
        "last_commit_sha": "0" * 40,
        "plan_digest": hashlib.sha256(archived.read_bytes()).hexdigest(),
    }


def _closeout_state_payload(
    root: Path,
    *,
    receipt: bool = True,
    workflow_state: str = "complete",
    tasks: dict | None = None,
) -> dict:
    """The execute-plan session state shape the gate reads (the fields it
    consumes mirror the runtime's writer: plan_slug, workflow_state,
    tasks, archive_gate, terminal_receipt)."""
    payload = {
        "schema_version": 1,
        "plan_slug": CLOSEOUT_SLUG,
        "workflow_state": workflow_state,
        "tasks": (
            tasks
            if tasks is not None
            else {
                "task-1": {
                    "id": "task-1",
                    "status": "complete",
                    "checkbox": True,
                }
            }
        ),
        "archive_gate": {
            "plan_path": CLOSEOUT_ACTIVE_REL,
            "declared_destination": CLOSEOUT_ARCHIVED_REL,
            "plan_digest": _closeout_receipt(root)["plan_digest"],
        },
    }
    if receipt:
        payload["terminal_receipt"] = _closeout_receipt(root)
    return payload


def _write_closeout_state(root: Path, slug: str, payload: dict) -> Path:
    session = root / "docs" / "tmp" / "execute-plan" / slug
    session.mkdir(parents=True, exist_ok=True)
    path = session / "runtime_state.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _closeout_done_run(root: Path, *, owned_plan_paths: list[str] | None = None) -> None:
    """Two confirmable run-start markers plus the active run manifest whose
    owned plan claim is the closeout plan (newest marker binds)."""
    now = time.time()
    make_marker(root, now - 1, os.getpid())
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root,
        "closeout-run",
        marker.name,
        str(root),
        now,
        owned_plan_paths=(
            owned_plan_paths
            if owned_plan_paths is not None
            else [CLOSEOUT_ACTIVE_REL]
        ),
    )


# --------------------------------------------------------------------------- #
# Plan checkbox: test_closeout_gate_accepts_landed_complete_run
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_closeout_gate_accepts_landed_complete_run(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given an owned execute-plan session manifest
    with a valid terminal receipt whose archived bytes hash to the receipt
    digest, the active path gone, the promoted origin closed, and the
    registry row resolving, expects rc 0 with a pass message."""
    root = _closeout_repo(tmp_path, "closeout-ok")
    _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "passed" in result.message
    assert CLOSEOUT_SLUG in result.message


def test_closeout_gate_refuses_landed_without_terminal_evidence(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given the origin's witnessed shape (all
    tasks done, no terminal receipt, the plan still active on the landing
    target after its implementation landed), expects rc 1 naming the
    condition and the resume remedy, with the manifest bytes untouched
    (recovery evidence preserved)."""
    root = _closeout_repo(tmp_path, "closeout-no-receipt")
    active = root / CLOSEOUT_ACTIVE_REL
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(CLOSEOUT_PLAN_TEXT, encoding="utf-8")
    state_path = _write_closeout_state(
        root,
        CLOSEOUT_SLUG,
        _closeout_state_payload(root, receipt=False, workflow_state="active"),
    )
    _closeout_done_run(root)
    before = state_path.read_bytes()
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert "landed without terminal evidence" in result.message
    assert "resume" in result.message
    assert state_path.read_bytes() == before


def test_closeout_gate_refuses_stale_receipt_digest(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a receipt whose plan_digest differs
    from the archived bytes' recomputed sha256, expects rc 1 naming the
    digest mismatch."""
    root = _closeout_repo(tmp_path, "closeout-stale-digest")
    payload = _closeout_state_payload(root)
    payload["terminal_receipt"]["plan_digest"] = "0" * 64
    _write_closeout_state(root, CLOSEOUT_SLUG, payload)
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert "digest mismatch" in result.message


def test_closeout_gate_refuses_active_twin_surviving(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a landed-complete run whose archived
    bytes, origin closure, and registry row all resolve but the active plan
    path survives, expects rc 1 naming the surviving active path, from the
    working tree arm and from the index arm (the copy-plus-delete residue
    detector from the origin's repair incident)."""
    root = _closeout_repo(tmp_path, "closeout-active-twin")
    plans = root / "docs/history/plans"
    plans.mkdir(parents=True, exist_ok=True)
    active = plans / f"{CLOSEOUT_SLUG}.md"
    active.write_text("copied, never moved\n", encoding="utf-8")
    _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert CLOSEOUT_ACTIVE_REL in result.message
    # Index arm: the same surviving path tracked in the index (worktree
    # copy removed) refuses identically.
    git(root, "add", "-f", CLOSEOUT_ACTIVE_REL)
    active.unlink()
    result2 = run_gate("execute-plan-closeout", ctx_for(root))
    assert result2.rc == 1, result2.message
    assert CLOSEOUT_ACTIVE_REL in result2.message
    git(root, "rm", "--cached", "-f", "-q", CLOSEOUT_ACTIVE_REL)


# --------------------------------------------------------------------------- #
# Task 2 witnesses: the origin's remaining shapes (open promoted origin,
# unpromoted residual backlog, missing execute-plan home, malformed window
# manifest, unowned peer session, unanchored window).
# --------------------------------------------------------------------------- #
def test_closeout_gate_refuses_open_promoted_origin(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a landed-complete run whose promoted
    origin still sits open in the backlog top level, or whose origin is
    dispositioned but the ownership registry row is missing, expects rc 1
    naming the origin file (arm 1) and the registry gap (arm 2)."""
    root = _closeout_repo(tmp_path, "closeout-open-origin")
    open_origin = root / CLOSEOUT_ORIGIN_OPEN_REL
    open_origin.parent.mkdir(parents=True, exist_ok=True)
    open_origin.write_text("status: open\n", encoding="utf-8")
    (root / CLOSEOUT_ORIGIN_CLOSED_REL).unlink()
    _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert CLOSEOUT_ORIGIN_NAME in result.message
    # Arm 2: origin dispositioned, registry row missing.
    open_origin.unlink()
    closed = root / CLOSEOUT_ORIGIN_CLOSED_REL
    closed.write_text(
        "origin disposition: folded into the archived plan\n",
        encoding="utf-8",
    )
    registry = root / CLOSEOUT_REGISTRY_REL
    registry.write_text(
        "<!-- Document ownership registry fixture without the row -->\n",
        encoding="utf-8",
    )
    result2 = run_gate("execute-plan-closeout", ctx_for(root))
    assert result2.rc == 1, result2.message
    assert "registry" in result2.message
    assert CLOSEOUT_SLUG in result2.message


def test_closeout_gate_keeps_unpromoted_backlog_open(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a landed-complete run plus a residual
    backlog item the plan never promoted, expects rc 0 and the gate message
    does not name the residual item (the false-positive arm of the origin's
    sixth witness)."""
    root = _closeout_repo(tmp_path, "closeout-residual")
    backlog = root / "docs/history/backlog"
    backlog.mkdir(parents=True, exist_ok=True)
    residual = backlog / "2026-10-01-unrelated-residual.md"
    residual.write_text("status: open\n", encoding="utf-8")
    _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "unrelated-residual" not in result.message


def test_closeout_gate_warning_skips_without_execute_plan_home(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a repo fixture whose tmp home has no
    execute-plan directory, expects rc 0 and a warning-skip message naming
    the home (the vacuous-pass guard: absence is reported, never silent)."""
    root = _closeout_repo(tmp_path, "closeout-no-home")
    _closeout_done_run(root)
    assert not (root / "docs/tmp/execute-plan").exists()
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "warning skip" in result.message
    assert "docs/tmp/execute-plan" in result.message


def test_closeout_gate_refuses_malformed_window_manifest(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given an owned manifest whose JSON cannot
    be parsed, expects rc 1 naming the file (fail-closed over
    subprocess-shaped silent passes)."""
    root = _closeout_repo(tmp_path, "closeout-malformed")
    session = root / "docs" / "tmp" / "execute-plan" / CLOSEOUT_SLUG
    session.mkdir(parents=True, exist_ok=True)
    state_path = session / "runtime_state.json"
    state_path.write_text("{not json at all\n", encoding="utf-8")
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert "runtime_state.json" in result.message
    assert "unreadable or malformed" in result.message


def test_closeout_gate_skips_unowned_window_manifests(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given an in-window execute-plan manifest
    whose plan slug matches none of the run manifest's owned plan claims (a
    peer's interrupted run sharing the tmp home), expects rc 0 and a pass
    note that does not demand the peer run's receipt (the
    never-blocks-unrelated-closeout arm)."""
    root = _closeout_repo(tmp_path, "closeout-unowned")
    _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
    peer_slug = "2026-10-01-peer-plan"
    _write_closeout_state(
        root,
        peer_slug,
        {
            "schema_version": 1,
            "plan_slug": peer_slug,
            "workflow_state": "active",
            "tasks": {
                "task-1": {"id": "task-1", "status": "complete", "checkbox": True}
            },
        },
    )
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "passed" in result.message
    assert peer_slug in result.message
    assert "skipped" in result.message
    assert "landed without terminal evidence" not in result.message


def test_closeout_gate_warning_skips_unanchored_window(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a done-session dir whose window cannot
    anchor (a single marker and no manifest-plus-ledger witness pair),
    expects rc 0 and a warning-skip message naming the unanchored window
    (the fold-added discovery arm's witness)."""
    root = _closeout_repo(tmp_path, "closeout-unanchored")
    _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
    make_marker(root, time.time(), os.getpid())
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "warning skip" in result.message
    assert "anchor" in result.message
