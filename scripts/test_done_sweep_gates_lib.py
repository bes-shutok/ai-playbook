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
import struct
import subprocess
import sys
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
    """[class: REPOSITORY_TEST] With a recorded session-start head (repo with
    2+ commits) and a commit landed after it: the committed-in-session file
    reaches check-writes stdin as a typed name-status row (``A<TAB>path``)
    alongside the typed porcelain rows; a bare downgrade of the same path
    never appears."""
    root = make_repo(tmp_path, "docreg-committed", gitignore_docs=True)
    write_facts(root)
    write_stub_doc_registry_validator(root)
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True)
    base_head = git(root, "rev-parse", "HEAD").stdout.strip()
    (done_session / "session-start-head.txt").write_text(
        base_head + "\n", encoding="utf-8"
    )
    # Committed after the recorded session start: name-status `A` row.
    (root / "committed-in-session.md").write_text("new\n", encoding="utf-8")
    git(root, "add", "committed-in-session.md")
    git(root, "commit", "-m", "land in session", "-q")
    # Uncommitted edit: porcelain ` M` row.
    (root / "README.md").write_text("modified tracked file\n", encoding="utf-8")

    stdin_log = tmp_path / "docreg-committed-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    # Bare rows ARE tolerated here: the ignored-matching arm contributes the
    # gitignored session-start head as a bare row (it has no change type).
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
