#!/usr/bin/env python3
"""Hermetic pytest suite for the done sweep gate runner lib (plan Task 1).

Plan: docs/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md,
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
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
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

# The ten absorbed gate ids, in done SKILL.md step order (plan Terms + G2).
EXPECTED_TEN_GATES = [
    "plan-readiness",
    "confluence-hygiene",
    "doc-registry",
    "backlog-inbox",
    "review-staging",
    "vim-swap-sweep",
    "docs-tmp-sweep",
    "sensitive-data-scan",
    "em-dash-scan",
    "instruction-size",
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
        'plans_dir = "docs/plans/"\n'
        'plans_completed_dir = "docs/plans/completed/"\n'
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
    """[class: REPOSITORY_TEST] Given the lib gate registry, expects exactly ten
    gate ids in the two phase slices, in done SKILL.md order, matching
    plan-readiness, confluence-hygiene, doc-registry, backlog-inbox,
    review-staging, vim-swap-sweep, docs-tmp-sweep, sensitive-data-scan,
    em-dash-scan, instruction-size."""
    assert PRE_DOCS_GATES == EXPECTED_TEN_GATES[:7]
    assert PRE_COMMIT_GATES == EXPECTED_TEN_GATES[7:]
    assert lib.PHASES["pre-docs"] == PRE_DOCS_GATES
    assert lib.PHASES["pre-commit"] == PRE_COMMIT_GATES
    assert list(lib.PHASES.keys()) == ["pre-docs", "pre-commit"]
    # Every registry entry has an implementation and a phase slice.
    assert set(lib.GATES.keys()) == set(EXPECTED_TEN_GATES)
    # The dead READ_ONLY_GATES set stays deleted (sequential execution).
    assert not hasattr(lib, "READ_ONLY_GATES")
    # list-gates prints the ten ids in phase order, one per line.
    assert lib.main(["list-gates"]) == 0
    assert capsys.readouterr().out.splitlines() == EXPECTED_TEN_GATES


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

    alpha = "docs/plans/2026-09-20-alpha.md"
    beta = "docs/plans/2026-09-20-beta.md"
    gamma = "docs/plans/2026-09-20-gamma.md"
    delta_completed = "docs/plans/completed/2026-09-19-delta.md"
    (root / "docs/plans").mkdir(parents=True)
    (root / "docs/plans/completed").mkdir(parents=True)
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
    (root / "docs/plans").mkdir(parents=True)
    ignored_plans = [
        "docs/plans/2026-09-20-conv-a.md",
        "docs/plans/2026-09-20-conv-b.md",
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
    plan = "docs/plans/2026-09-20-stale-exempt-attempt.md"
    (root / "docs/plans").mkdir(parents=True)
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

    plans_dir = root / "docs/plans"
    completed_dir = root / "docs/plans/completed"
    plans_dir.mkdir(parents=True)
    completed_dir.mkdir(parents=True)
    good = "docs/plans/2026-09-20-good-one.md"
    exempt = "docs/plans/2026-09-20-exempt-one.md"
    gone = "docs/plans/2026-09-20-gone-one.md"
    bad = "docs/plans/2026-09-20-bad-one.md"
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
    plan = "docs/plans/2026-09-20-bad-report-plan.md"
    (root / "docs/plans").mkdir(parents=True)
    (root / plan).write_text("bad\n", encoding="utf-8")
    write_deliverables(root, [plan])
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["pre-docs"])
    out = capsys.readouterr().out
    assert rc != 0
    json_lines = [ln for ln in out.splitlines() if ln.startswith("{")]
    assert len(json_lines) == 7  # one per pre-docs gate, in registry order
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
    plan = "docs/plans/2026-09-20-crashing-plan.md"
    (root / "docs" / "plans").mkdir(parents=True)
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

    completed = root / "docs" / "plans" / "completed"
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
    assert "docs/plans/completed/unchanged.md" not in rows


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

    plans_dir = root / "docs/plans"
    completed_dir = root / "docs/plans/completed"
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
    subdirectory of plans_dir (docs/plans/deferred/<slug>.md) is a LIVE
    session: the sweep preserves it instead of treating the plan as archived
    and rmtree-ing the session."""
    root = make_repo(tmp_path, "nested-session", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    deferred_dir = root / "docs" / "plans" / "deferred"
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
# Plan: docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
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
    owned_plan_paths: list[str] | None = None,
    owned_review_paths: list[str] | None = None,
    foreign_review_paths: list[str] | None = None,
    adopted_from: str | None = None,
    complete: bool = False,
) -> Path:
    """Seed one run-manifest JSON through the lib's own model so loader tests
    exercise the real serialization shape. ``start_commit`` defaults to the
    current HEAD; ``start_porcelain`` defaults to an empty snapshot; the
    owned/foreign lists default to empty; ``adopted_from`` defaults to null
    and ``complete`` to false (an interrupted run)."""
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
        owned_plan_paths=list(owned_plan_paths or []),
        owned_review_paths=list(owned_review_paths or []),
        foreign_review_paths=list(foreign_review_paths or []),
        adopted_from=adopted_from,
        complete=complete,
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
    plan = "docs/plans/2026-09-22-owned-plan.md"
    review_rel = "docs/reviews/2026-09-22-atomic-review-r1.md"
    (root / "docs/plans").mkdir(parents=True)
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
    assert payload["repo_root"] == str(root.resolve())
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
        ["write-manifest", "--owned-plan", "docs/plans/2026-09-22-x.md"]
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
    same repo, expects two distinct run_id values and two distinct manifest
    files, each file's payload run_id matching its filename."""
    root = mktemp_repo("unique")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest"]) == 0
    first = sorted(done_session.glob("run-manifest-*.json"))
    assert len(first) == 1
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
# Plan: docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
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
    completed = root / "docs" / "plans" / "completed"
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
    assert "docs/plans/completed/pre-window.md" not in rows
    # Retirement: the file is never rewritten (byte-identical after the run).
    assert retired.read_text(encoding="utf-8") == head + "\n"

    # Arm 2: unanchorable window (one marker) keeps the conservative
    # all-ignored inclusion.
    root2 = mktemp_repo("legacy-conservative")
    write_facts(root2)
    write_stub_doc_registry_validator(root2)
    make_marker(root2, time.time(), os.getpid())
    completed2 = root2 / "docs" / "plans" / "completed"
    completed2.mkdir(parents=True)
    old2 = completed2 / "old-ignored.md"
    old2.write_text("old ignored\n", encoding="utf-8")
    os.utime(old2, (now - 86400, now - 86400))
    stdin_log2 = tmp_path / "legacy-conservative-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log2))

    result2 = run_gate("doc-registry", ctx_for(root2))

    assert result2.rc == 0
    rows2 = stdin_log2.read_text(encoding="utf-8").splitlines()
    assert "docs/plans/completed/old-ignored.md" in rows2


# --------------------------------------------------------------------------- #
# Plan: docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
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
    completed = root / "docs" / "plans" / "completed"
    completed.mkdir(parents=True)
    inside_rel = "docs/plans/completed/in-window.md"
    outside_rel = "docs/plans/completed/out-window.md"
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
    completed = root / "docs" / "plans" / "completed"
    completed.mkdir(parents=True)
    inside_rel = "docs/plans/completed/in-window.md"
    outside_rel = "docs/plans/completed/out-window.md"
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
    completed2 = root2 / "docs" / "plans" / "completed"
    completed2.mkdir(parents=True)
    old_rel = "docs/plans/completed/old-ignored.md"
    (root2 / old_rel).write_text("old ignored\n", encoding="utf-8")
    os.utime(root2 / old_rel, (now - 86400, now - 86400))

    ctx2 = ctx_for(root2)
    kept2 = lib._session_ignored_paths(ctx2, [old_rel])

    assert kept2 == [old_rel]


# --------------------------------------------------------------------------- #
# Plan: docs/plans/2026-09-22-done-session-isolation-shared-checkout-ownership.md
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
    naming the orphan run_id and, without ``--adopt``, to write a manifest
    whose boundary is the new run's own HEAD; a prior manifest with
    ``complete`` true is never reported as an orphan (this is what keeps a
    completed commit-less run from misfiring the detection)."""
    # Arm 1: an unfinalized prior manifest is reported; the retry keeps its
    # own HEAD boundary.
    root = mktemp_repo("orphan")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-orphan-reported"
    _seed_run_manifest(root, orphan_id, prev.name, str(root), time.time() - 10)
    # HEAD advances after the orphan died: the retry's own boundary is here.
    (root / "post-orphan.md").write_text("committed after the orphan died\n", encoding="utf-8")
    git(root, "add", "post-orphan.md")
    git(root, "commit", "-m", "post orphan", "-q")
    new_head = git(root, "rev-parse", "HEAD").stdout.strip()
    assert new_head != start
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "interrupted run" in out
    assert orphan_id in out
    payload = _newest_manifest_payload(root, exclude_run_id=orphan_id)
    assert payload["start_commit"] == new_head
    assert payload["adopted_from"] is None
    assert payload["complete"] is False
    assert payload["run_id"] != orphan_id

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
    plan_rel = "docs/plans/2026-09-22-adopted-plan.md"
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
    # adopted_from link is the suppression record. The unrelated third run
    # must still cover the on-disk candidate itself (peer artifact: foreign).
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
    expects the retry's gates to stay bounded by the retry's own boundary,
    never by the orphan's (the origin's no-implicit-adoption clause): the
    orphan is reported (surfaced for an explicit decision) but its boundary is
    not inherited, so the orphan's committed file never enters the retry's
    doc-registry check-writes set and is never foreign-reported either (it is
    simply outside the retry's committed window)."""
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

    assert rc == 0
    out = capsys.readouterr().out
    # Surfaced, never silently adopted.
    assert "interrupted run" in out
    assert orphan_id in out
    payload = _newest_manifest_payload(root, exclude_run_id=orphan_id)
    assert payload["adopted_from"] is None
    assert payload["start_commit"] == orphan_sha

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
# Plan: docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md
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
