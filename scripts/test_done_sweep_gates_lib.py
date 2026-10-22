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
import re
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
    LANDING_GATES,
    GateContext,
    derive_plan_readiness_candidates,
    derive_review_staging_candidates,
    derive_review_staging_scope,
    derive_session_window,
    run_gate,
)

# The implemented gate ids (the GATES registry); the landing roster is the
# retained subset (EXPECTED_LANDING_ROSTER) after the done target-state flip
# removed backlog-inbox and vim-swap-sweep from the per-run roster.
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
    "post-landing-staging",
    "plans-root-claim-fence",
    "archive-ceremony",
    "execute-plan-closeout",
]

# The landing roster, in registry order (the closeout's one sweep run;
# plans-archive-twin deduped to one slot).
EXPECTED_LANDING_ROSTER = [
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


def write_landing_validator_stubs(root: Path) -> None:
    """Stub the landing roster's script-backed hygiene gates in the fixture
    repo's repo-local scripts/ arm, so an end-to-end landing run is
    deterministic (the deployment-gap refusals have their own arm)."""
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "check-no-em-dash.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8"
    )
    (scripts_dir / "check-instruction-size.sh").write_text(
        "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8"
    )
    (scripts_dir / "check_skill_description_length.py").write_text(
        "#!/usr/bin/env python3\nprint('stub ok')\n", encoding="utf-8"
    )


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
        'reviews_dir = ".ai-playbook/reviews/"\n'
        'tmp_dir = "docs/tmp/"\n'
        'base_branch = "main"\n'
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
    """Repo-local stub validator answering in the migrated four-outcome
    shape: 'good' plans pass (exit 0, `OUTCOME: pass`), others fail
    (exit 1 with the rejection line and `OUTCOME: fail`)."""
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    stub = scripts / "plan_readiness.py"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "plan = sys.argv[1] if len(sys.argv) > 1 else ''\n"
        "if 'good' in plan:\n"
        "    print('ready=yes')\n"
        "    print('OUTCOME: pass')\n"
        "    sys.exit(0)\n"
        "print('readiness FAILED: stub rejection')\n"
        "print('OUTCOME: fail')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    return stub


def write_stub_readiness_validator_body(root: Path, body: str) -> Path:
    """Repo-local stub readiness validator with a custom exit body (the
    subprocess seam for the child-outcome fixtures)."""
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    stub = scripts / "plan_readiness.py"
    stub.write_text(
        "#!/usr/bin/env python3\nimport sys\n" + body, encoding="utf-8"
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
    git_home = tmp_path / "git-home"
    git_home.mkdir()
    xdg_config_home = tmp_path / "xdg-config-home"
    xdg_config_home.mkdir()
    user_facts = tmp_path / "user-facts.md"
    user_facts.write_text("# fixture user facts\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_RUNTIME_HOME", str(runtime_home))
    monkeypatch.setenv("DONE_SWEEP_USER_FACTS", str(user_facts))
    monkeypatch.setenv("HOME", str(git_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config_home))
    for var in (
        "PLAN_READINESS_VALIDATOR",
        "CONFLUENCE_MIRROR_HYGIENE_SCRIPT",
        "DOC_REGISTRY_VALIDATOR_SCRIPT",
        "BACKLOG_LOCATION_GATE",
        "REVIEW_STAGING_VALIDATOR",
        "CHECK_NO_EM_DASH_SCRIPT",
        "INSTRUCTION_SIZE_CHECK_SCRIPT",
        "DONE_SWEEP_REPO_ROOT",
        "DONE_SWEEP_DECLARED_STAGE_PATHS",
    ):
        monkeypatch.delenv(var, raising=False)
    for var in tuple(os.environ):
        if var.startswith("GIT_"):
            monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    return runtime_home


def test_sweep_env_keeps_system_git_config_disabled(sweep_env):
    """The shared fixture environment leaves the system-config opt-out set
    after clearing inherited Git variables, so child Git processes stay isolated."""
    assert os.environ.get("GIT_CONFIG_NOSYSTEM") == "1"
    assert Path.home().name == "git-home"
    assert Path(os.environ["XDG_CONFIG_HOME"]).name == "xdg-config-home"
    assert not (Path(os.environ["XDG_CONFIG_HOME"]) / "git" / "config").exists()


def ctx_for(root: Path) -> GateContext:
    # Facts-first resolution is fail-closed now: a fixture repo without a
    # facts block provisions the standard five keys at discovery time, the
    # same production ordering (facts exists before any gate runs). Tests
    # that write their own facts keep their bytes (the write is skipped).
    if not (root / ".ai-playbook" / "facts.md").is_file():
        write_facts(root)
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
        root = make_repo(parent, name, **kwargs)
        # Facts-first resolution is fail-closed: every fixture repo carries
        # the standard facts block unless the test writes its own (the
        # write is skipped when one exists), mirroring production where a
        # bootstrapped repo always has facts before any gate runs.
        if not (root / ".ai-playbook" / "facts.md").is_file():
            write_facts(root)
        return root

    yield _make
    for parent in parents:
        shutil.rmtree(parent, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Plan checkbox: test_gate_registry_matches_absorbed_steps
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_gate_registry_matches_absorbed_steps(capsys):
    """[class: REPOSITORY_TEST] Given the lib gate registry, expects exactly
    seventeen implemented gate ids, and the landing phase carries the retained
    fifteen-gate roster (the done target-state flip): backlog-inbox and
    vim-swap-sweep are off the roster, plan-readiness, instruction-size and
    description-length ride in warning posture, and plans-archive-twin is
    deduped to one slot."""
    # The flip: the deleted phases are gone from the registry.
    assert not hasattr(lib, "PRE_DOCS_GATES")
    assert not hasattr(lib, "PRE_COMMIT_GATES")
    assert list(lib.PHASES.keys()) == ["landing"]
    assert lib.PHASES["landing"] == EXPECTED_LANDING_ROSTER
    assert lib.LANDING_GATES == EXPECTED_LANDING_ROSTER
    for demoted in ("backlog-inbox", "vim-swap-sweep"):
        assert demoted not in lib.LANDING_GATES
    assert lib.LANDING_WARNING_GATES == frozenset(
        {"plan-readiness", "instruction-size", "description-length"}
    )
    # Every registry entry has an implementation.
    assert set(lib.GATES.keys()) == set(EXPECTED_GATE_ORDER)
    # The dead READ_ONLY_GATES set stays deleted (sequential execution).
    assert not hasattr(lib, "READ_ONLY_GATES")
    # list-gates prints the landing roster (bare and with the phase argument
    # alike), warning-posture gates suffixed.
    assert lib.main(["list-gates"]) == 0
    assert capsys.readouterr().out.splitlines() == EXPECTED_LANDING_ROSTER
    assert lib.main(["list-gates", "landing"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        f"{gate} (warning)" if gate in lib.LANDING_WARNING_GATES else gate
        for gate in EXPECTED_LANDING_ROSTER
    ]
    # An unknown phase argument is a tool error.
    assert lib.main(["list-gates", "no-such-phase"]) == 3
    capsys.readouterr()
    assert len(EXPECTED_GATE_ORDER) == 17
    assert len(set(EXPECTED_GATE_ORDER)) == 17
    assert len(EXPECTED_LANDING_ROSTER) == 15
    assert len(set(EXPECTED_LANDING_ROSTER)) == 15


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
    """[class: REPOSITORY_TEST] Passing, exempted, archived, and modeled-fail
    plans listed in plan-deliverables.txt: exactly those lines are removed, no
    others; the modeled ready=no is advisory (the gate exits 0 naming the
    failure) and its candidate retires from the queue."""
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
    # The failing plan is gated; its modeled ready=no is advisory: the gate
    # reports failed=1 with the stub's first failure line and exits 0.
    assert result.rc == 0
    assert "failed=1" in result.message
    assert bad in result.message
    assert "readiness FAILED: stub rejection" in result.message
    # Removal rule: good (passed), exempt (manifest), gone (archived), and
    # bad (the retired modeled-fail candidate) all removed.
    assert read_deliverables(root) == []


# --------------------------------------------------------------------------- #
# Plan checkbox: test_report_shape_and_order  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_report_shape_and_order(tmp_path, sweep_env, monkeypatch, capsys):
    """[class: REPOSITORY_TEST] A landing run whose only non-passing input
    is an advisory modeled ready=no (the plan-readiness row exits 0 with the
    finding named) still yields one JSON line per gate in roster order (gate,
    rc, message), a human summary block, and a phase-level zero exit."""
    root = make_repo(tmp_path, "report", gitignore_docs=True)
    write_facts(root)
    write_landing_validator_stubs(root)
    write_stub_readiness_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    plan = "docs/history/plans/2026-09-20-bad-report-plan.md"
    (root / "docs/history/plans").mkdir(parents=True)
    (root / plan).write_text("bad\n", encoding="utf-8")
    write_deliverables(root, [plan])
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["landing"])
    out = capsys.readouterr().out
    assert rc == 0
    json_lines = [ln for ln in out.splitlines() if ln.startswith("{")]
    assert len(json_lines) == 15  # one per landing gate, in roster order
    gates = []
    for ln in json_lines:
        payload = json.loads(ln)
        assert set(payload) >= {"gate", "rc", "message"}
        gates.append(payload["gate"])
    assert gates == EXPECTED_LANDING_ROSTER
    first = json.loads(json_lines[0])
    assert first["gate"] == "plan-readiness" and first["rc"] == 0
    assert "failed=1" in first["message"]
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
# Plan checkbox: test_backlog_inbox_violation_warns  [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def test_backlog_inbox_violation_warns(tmp_path, sweep_env, monkeypatch):
    """[class: REPOSITORY_TEST] With a stub backlog-location validator that
    exits 1 with a violation line, expects the backlog-inbox gate to report
    and continue (rc 0) with the violation carried in a ``reported, not
    failing`` warning - the demotion program change 4 posture (ledger entry
    backlog-inbox: 0 catches / 1 incident, the temporary-filename
    relocation incident); a validator that exits 0 still passes with no
    warning."""
    root = make_repo(tmp_path, "backlog-warns", gitignore_docs=True)
    write_facts(root)
    stub = root / "stub-backlog-gate.py"
    stub.write_text(
        "import sys\n"
        "print('HARD: docs/maintenance/untracked-backlog-inbox.md: rule 1')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BACKLOG_LOCATION_GATE", str(stub))
    ctx = ctx_for(root)

    violated = run_gate("backlog-inbox", ctx)

    assert violated.rc == 0
    assert any(
        "backlog-inbox: location violation (reported, not failing):" in w
        for w in violated.warnings
    )
    assert any("rule 1" in w for w in violated.warnings)

    stub.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    ctx2 = ctx_for(root)

    passed = run_gate("backlog-inbox", ctx2)

    assert passed.rc == 0
    assert passed.warnings == []
    assert passed.message == "backlog inbox location gate passed"


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
# Outcome-contract child arms (plan docs/history/plans/2026-10-03-outcome-
# contract-migration-batch-2.md, Task 2): the plan-readiness child arm
# branches on the migrated validator's four outcomes and the no-line rule
# instead of routing every child exit above 1 into an indeterminate bucket.
# A crashed readiness validator (traceback on stdout, message on stderr, no
# final OUTCOME line) reports its stderr line as the tool-error evidence,
# never the bare "Traceback (most recent call last):" header.
# --------------------------------------------------------------------------- #
def _gate_one_deliverable_plan(root: Path, plan_rel: str) -> object:
    """Marker pair plus one deliverable plan: the minimal gated candidate."""
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    (root / "docs" / "history" / "plans").mkdir(parents=True, exist_ok=True)
    (root / plan_rel).write_text("plan bytes\n", encoding="utf-8")
    write_deliverables(root, [plan_rel])
    return run_gate("plan-readiness", ctx_for(root))


def test_plan_readiness_reports_stderr_on_validator_crash(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A readiness validator that crashes (traceback
    on stdout, message on stderr, no final OUTCOME line) classifies tool
    error per the contract's no-line rule winning over the exit code: the
    gate exits 3 with the stderr message as the tool-error evidence, and the
    traceback header never reaches the report."""
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

    result = _gate_one_deliverable_plan(
        root, "docs/history/plans/2026-09-20-crashing-plan.md"
    )

    assert result.rc == 3, result.message
    assert "Traceback (most recent call last)" not in result.message
    assert "readiness error: plan_readiness.py cannot import facts" in result.message


def test_plan_readiness_modeled_fail_is_advisory(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A readiness child reporting the modeled ready=no
    (exit 1 with a final `OUTCOME: fail` line) is advisory: the gate exits 0,
    reports `failed=1` naming the child and its first-failure line, and retires
    the candidate by pruning its deliverable line so a later closeout does not
    reconsider it."""
    root = mktemp_repo("readiness-child-modeled-fail")
    write_facts(root)
    write_stub_readiness_validator_body(
        root,
        "print('readiness FAILED: stub review record is stale (stub)')\n"
        "print('OUTCOME: fail')\n"
        "sys.exit(1)\n",
    )
    plan_rel = "docs/history/plans/2026-09-20-modeled-fail-plan.md"

    result = _gate_one_deliverable_plan(root, plan_rel)

    assert result.rc == 0, result.message
    assert "failed=1" in result.message
    assert plan_rel in result.message
    assert "readiness FAILED: stub review record is stale (stub)" in result.message
    assert read_deliverables(root) == []


def test_plan_readiness_child_indeterminate_lands_indeterminate(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A readiness child reporting indeterminate
    (exit 2 with a final `OUTCOME: indeterminate` line; a legacy shape the
    migrated validator never models) lands the gate in the indeterminate
    bucket naming the child: the gate exits 2 and never collapses the
    child's uncertainty into a fail."""
    root = mktemp_repo("readiness-child-indeterminate")
    write_facts(root)
    write_stub_readiness_validator_body(
        root,
        "print('validator could not read the review record (stub)')\n"
        "print('OUTCOME: indeterminate')\n"
        "sys.exit(2)\n",
    )

    result = _gate_one_deliverable_plan(
        root, "docs/history/plans/2026-09-20-indeterminate-plan.md"
    )

    assert result.rc == 2, result.message
    assert "2026-09-20-indeterminate-plan.md" in result.message
    assert "indeterminate" in result.message


def test_plan_readiness_child_tool_error_lands_tool_error(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A readiness child reporting tool error
    (exit 3 with a final `OUTCOME: tool_error` line, the sibling-compat and
    usage arms included) lands the gate in the tool-error bucket reported as
    the gate's tool-error evidence: a child that could not run reliably is
    never a readiness fail."""
    root = mktemp_repo("readiness-child-tool-error")
    write_facts(root)
    write_stub_readiness_validator_body(
        root,
        "print('compatibility FAILED: stub sibling drifted (stub)')\n"
        "print('OUTCOME: tool_error')\n"
        "sys.exit(3)\n",
    )

    result = _gate_one_deliverable_plan(
        root, "docs/history/plans/2026-09-20-tool-error-plan.md"
    )

    assert result.rc == 3, result.message
    assert "2026-09-20-tool-error-plan.md" in result.message
    assert "tool error" in result.message
    assert "compatibility FAILED: stub sibling drifted (stub)" in result.message


def test_plan_readiness_child_without_outcome_line_is_tool_error(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A legacy readiness child that exits 0
    emitting no final `OUTCOME:` line classifies tool error per the
    contract's no-line rule winning over the exit code: the gate exits 3
    naming the child, never a silent pass."""
    root = mktemp_repo("readiness-child-no-line")
    write_facts(root)
    write_stub_readiness_validator_body(
        root,
        "print('ready=yes (legacy validator without outcome reporting)')\n"
        "sys.exit(0)\n",
    )

    result = _gate_one_deliverable_plan(
        root, "docs/history/plans/2026-09-20-no-line-plan.md"
    )

    assert result.rc == 3, result.message
    assert "2026-09-20-no-line-plan.md" in result.message
    assert "no final OUTCOME line" in result.message


# --------------------------------------------------------------------------- #
# Operator-acked readiness through the done plan-readiness gate
# (corrections-chain-operator-ack plan, Task 2): the gate's readiness child
# resolves the primary checkout's correction_authorizations entry, so the
# gate accepts (or refuses) the same witness object the staging validator
# and direct readiness resolve. These arms run the REAL readiness validator
# through the env seam; every other gate test stubs it.
# --------------------------------------------------------------------------- #

_ACK_PLAN_HEAD = (
    "# P\n\n"
    "## Assumptions\n\n"
    "Decision points requiring a grill: none remain.\n\n"
)
_ACK_PLAN_TAIL = (
    "\n## Tasks\n\n"
    "### Task 1: Do the thing\n\n"
    "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n"
)
_ACK_D1 = (_ACK_PLAN_HEAD + "alpha bravo." + _ACK_PLAN_TAIL).encode("utf-8")
_ACK_D3 = (_ACK_PLAN_HEAD + "alpha omega." + _ACK_PLAN_TAIL).encode("utf-8")
_ACK_DATE = "2026-09-22"
_ACK_SLUG = "acme-plan"
_ACK_PLAN_NAME = "2026-09-22-acme-plan.md"
_ACK_PLAN_REL = "docs/history/plans/" + _ACK_PLAN_NAME
_ACK_AUTHOR = "sess-author-done-gate"
_ACK_WRITER = "sess-writer-operator"
_ACK_DIRECTIVE = "accept the unclassified done-gate re-bind"
_ACK_GAP_REL = "docs/history/backlog/2026-10-18-done-gate-ack-gap.md"


def _seed_operator_ack_repo(root: Path) -> dict:
    """The graded fixture recipe over a done-sweep fixture repo (docs
    tracked so the plan history commits): D1 seed, round-close commit, the
    committed round-1 seal entry, the unclassified D3 hop, and the
    committed classifier-gap row. Returns the operator-acked row."""
    import corrections_record as cr

    def head_sha() -> str:
        return git(root, "rev-parse", "HEAD").stdout.strip()

    def commit_all(message: str, allow_empty: bool = False) -> str:
        proc = git(root, "add", "-A")
        assert proc.returncode == 0, proc.stderr
        args = ["commit", "-m", message, "-q"]
        if allow_empty:
            args.append("--allow-empty")
        proc = git(root, *args)
        assert proc.returncode == 0, proc.stderr
        return head_sha()

    (root / "docs" / "history" / "plans").mkdir(parents=True, exist_ok=True)
    (root / _ACK_PLAN_REL).write_text(
        _ACK_D1.decode("utf-8"), encoding="utf-8")
    start = commit_all("seed plan")
    commit_all("round 1 close", allow_empty=True)
    close = head_sha()
    seal_rel = ".ai-playbook/review-certs/%s.md" % _ACK_SLUG
    seal_path = root / seal_rel
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(
        "## round 1\n"
        "artifact: %s\n"
        "round_start_commit: %s\n"
        "round_start_digest: %s\n"
        "round_close_commit: %s\n" % (
            _ACK_PLAN_REL, start, hashlib.sha256(_ACK_D1).hexdigest(), close,
        ),
        encoding="utf-8",
    )
    commit_all("seal: round 1")
    (root / _ACK_PLAN_REL).write_text(
        _ACK_D3.decode("utf-8"), encoding="utf-8")
    hop = commit_all("unclassified fix")
    row = {
        "kind": cr.KIND_OPERATOR_ACKED,
        "before_digest": hashlib.sha256(_ACK_D1).hexdigest(),
        "after_digest": hashlib.sha256(_ACK_D3).hexdigest(),
        "evidence_commit": hop,
        "hunks": [{"header": "@@ -4 +4 @@",
                   "digest": cr.sha256_hex(b"ack-hunk-bytes")}],
        "recorded_at": "2026-10-18T00:00:00Z",
        "recorded_by": "plan_delta_classifier",
        "receipt": {
            "directive": _ACK_DIRECTIVE,
            "authorization_witness": cr.ACK_STATE_SELECTOR,
            "classifier_gap_row": _ACK_GAP_REL,
        },
        "author_session_id": _ACK_AUTHOR,
    }
    gap = root / _ACK_GAP_REL
    gap.parent.mkdir(parents=True, exist_ok=True)
    gap.write_text(
        "# classifier gap\n\nhunk digest %s\n" % row["hunks"][0]["digest"],
        encoding="utf-8",
    )
    commit_all("file the ack gap row")
    return {"row": row, "start": start, "hop": hop}


def _ack_entry_for(row: dict) -> dict:
    """The correction_authorizations entry binding the row digest and the
    exact row subject, written by a distinct operator-ack session."""
    import corrections_record as cr

    return {
        "row_digest": cr.correction_row_digest(row),
        "writer_session_id": _ACK_WRITER,
        "operator_direction": row["receipt"]["directive"],
        "recorded_at": row["recorded_at"],
        "author_session_id": row["author_session_id"],
        "artifact_path": _ACK_PLAN_REL,
        "before_digest": row["before_digest"],
        "after_digest": row["after_digest"],
        "evidence_commit": row["evidence_commit"],
        "hunk_digests": [h["digest"] for h in row["hunks"]],
    }


def _write_ack_state(root: Path, entries: list) -> None:
    state_dir = root / ".ai-playbook"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "scheduler-state.json").write_text(
        json.dumps({"correction_authorizations": entries}), encoding="utf-8"
    )


def _write_ack_review(root: Path, row: dict) -> None:
    """The review markdown plus the graded v1 sidecar (the proven graded
    fixture shape from the readiness tests) declaring the operator-acked
    row, at the round-start digest so the verified corrections chain
    re-binds it."""
    import validate_review_staging as vrs

    payload = vrs._post_window_fixture_payload("plan")
    payload["schema_version"] = 1
    payload["review_type"] = "Branch Review"
    payload["artifact_slug"] = _ACK_SLUG
    payload["round"] = "r1"
    payload["source_kind"] = "plan"
    payload["source_digest"] = hashlib.sha256(_ACK_D1).hexdigest()
    payload["verdict"] = "yes"
    payload["deduplication_groups"] = []
    payload["discarded"] = []
    payload["severity_calibration"] = []
    payload["triage_outcomes"] = []
    payload["soften_watchlist"] = []
    payload["extensions"] = {"corrections": [row]}
    reviews_dir = root / ".ai-playbook" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    markdown = vrs._post_window_fixture_markdown("plan")
    if "- URL or Artifact:" not in markdown:
        markdown = markdown.replace(
            "## Metadata\n",
            "## Metadata\n- URL or Artifact: %s\n" % _ACK_PLAN_REL, 1,
        )
    review = reviews_dir / (
        "%s-plan-review-%s-r1.md" % (_ACK_DATE, _ACK_SLUG)
    )
    review.write_text(markdown, encoding="utf-8")
    review.with_suffix(".stats.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _ack_gate_run(root: Path, monkeypatch) -> object:
    monkeypatch.setenv(
        "PLAN_READINESS_VALIDATOR", str(SCRIPTS_DIR / "plan_readiness.py")
    )
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    write_deliverables(root, [_ACK_PLAN_REL])
    return run_gate("plan-readiness", ctx_for(root))


def test_plan_readiness_gate_accepts_operator_acked_witness(
    tmp_path, sweep_env, mktemp_repo, monkeypatch
):
    """[class: REPOSITORY_TEST] The done plan-readiness gate runs the real
    readiness child over a fixture whose primary checkout carries the
    unique matching correction_authorizations entry: the child resolves
    that same object and accepts the same terminal digest, so the gate
    reports passed=1 and prunes the deliverable line."""
    root = mktemp_repo("ack-gate-pass", gitignore_docs=False)
    seeded = _seed_operator_ack_repo(root)
    _write_ack_state(root, [_ack_entry_for(seeded["row"])])
    _write_ack_review(root, seeded["row"])

    result = _ack_gate_run(root, monkeypatch)

    assert result.rc == 0, result.message
    assert "passed=1" in result.message, result.message
    assert read_deliverables(root) == []


def test_plan_readiness_gate_refuses_without_authorization(
    tmp_path, sweep_env, mktemp_repo, monkeypatch
):
    """[class: REPOSITORY_TEST] With no authorization recorded (the
    scheduled shape: no writer invocation, an empty array), the real
    readiness child refuses through the missing-witness leg; the gate
    reports the advisory modeled fail naming the receipt-leg reason."""
    root = mktemp_repo("ack-gate-refuses", gitignore_docs=False)
    seeded = _seed_operator_ack_repo(root)
    _write_ack_state(root, [])
    _write_ack_review(root, seeded["row"])

    result = _ack_gate_run(root, monkeypatch)

    assert result.rc == 0, result.message
    assert "failed=1" in result.message, result.message
    assert "no correction_authorizations entry" in result.message, (
        result.message
    )


def test_primary_checkout_resolver_parity(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] The two first-entry primary-checkout
    resolver bodies (the staging validator's and the done lib's
    dirty-state owner) behave identically: the same first entry wins on a
    real two-worktree fixture, and on a fabricated two-entry porcelain
    list whose primary path is written in ``~`` form both resolvers
    select and expand it to the same path (the tilde form exists so a
    resolver that forgets expanduser cannot pass this arm)."""
    import corrections_record
    import validate_review_staging as vrs

    root = make_repo(tmp_path, "resolver-parity", gitignore_docs=False)
    secondary_parent = tmp_path / "parity-wt"
    secondary_parent.mkdir()
    secondary = secondary_parent / "linked"
    proc = git(root, "worktree", "add", str(secondary), "-b", "parity-side")
    assert proc.returncode == 0, proc.stderr

    # Real fixture: the primary (first) entry wins in both resolvers.
    lib_primary, lib_error = lib._resolve_primary_checkout(ctx_for(root))
    vrs_primary, vrs_error = vrs._resolve_primary_checkout(root)
    assert lib_error == "" and vrs_error is None
    assert lib_primary.resolve() == root.resolve()
    assert vrs_primary.resolve() == root.resolve()

    # Fabricated two-entry list with the tilde path as the primary (the
    # first entry a resolver must select): both resolvers expand it to
    # the same path.
    porcelain = (
        "worktree ~/elsewhere/primary\nHEAD %s\nbranch refs/heads/main\n\n"
        "worktree %s\nHEAD %s\nbranch refs/heads/parity-side\n\n"
        % ("0" * 40, root, "0" * 40)
    )

    class _FakeCtx:
        def git(self, *args, input_text=None):
            return subprocess.CompletedProcess(
                args, 0, stdout=porcelain, stderr=""
            )

    lib_fake_primary, lib_fake_error = lib._resolve_primary_checkout(
        _FakeCtx()
    )
    assert lib_fake_error == ""
    assert lib_fake_primary == Path("~/elsewhere/primary").expanduser()

    original_git_text = corrections_record.git_text
    corrections_record.git_text = lambda repo, *args: porcelain
    try:
        vrs_fake_primary, vrs_fake_error = vrs._resolve_primary_checkout(
            root
        )
    finally:
        corrections_record.git_text = original_git_text
    assert vrs_fake_error is None
    assert vrs_fake_primary == Path("~/elsewhere/primary").expanduser()
    assert lib_fake_primary == vrs_fake_primary


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
# Outcome-contract migration batch 2, Task 5: the skills-repo hygiene arm
# branches on the migrated scan child's four outcomes (scripts/
# OUTCOME_CONTRACT.md) instead of collapsing every nonzero exit into a
# finding, and the contract's no-line rule wins over the exit code.
# --------------------------------------------------------------------------- #
def write_stub_hygiene_scanner(root: Path, mode: str) -> Path:
    """Repo-local stub scan-public-hygiene.sh (subprocess seam) answering in
    the migrated child outcome contract per its baked-in mode: pass (exit 0
    `OUTCOME: pass`), fail (exit 1 with hit rows plus `OUTCOME: fail`),
    indeterminate (exit 2), tool-error (exit 3), or no-line (a legacy shape
    that exits 0 emitting no OUTCOME row)."""
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    stub = scripts / "scan-public-hygiene.sh"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f"mode='{mode}'\n"
        "case \"$mode\" in\n"
        "  pass)\n"
        "    echo '=== PASS (public hygiene) ==='\n"
        "    echo 'OUTCOME: pass'\n"
        "    exit 0\n"
        "    ;;\n"
        "  fail)\n"
        "    echo 'FAIL: stub-hit'\n"
        "    echo 'leak-row: line-two-of-stub'\n"
        "    echo '=== 1 public-hygiene failure(s) ==='\n"
        "    echo 'OUTCOME: fail'\n"
        "    exit 1\n"
        "    ;;\n"
        "  indeterminate)\n"
        "    echo 'stub scan could not complete (no verdict)'\n"
        "    echo 'OUTCOME: indeterminate'\n"
        "    exit 2\n"
        "    ;;\n"
        "  tool-error)\n"
        "    echo 'FATAL: stub scanner cannot read its patterns file' >&2\n"
        "    echo 'OUTCOME: tool_error'\n"
        "    exit 3\n"
        "    ;;\n"
        "  no-line)\n"
        "    echo 'legacy scanner without outcome reporting'\n"
        "    exit 0\n"
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    return stub


def _seed_skills_repo_user_facts(tmp_path, monkeypatch, root: Path) -> None:
    """Point the user facts' skills_repo_path row at the fixture repo so the
    sensitive-data gate's skills-repo hygiene arm triggers for it."""
    facts = tmp_path / "user-facts-skills-repo.md"
    facts.write_text(f"| `skills_repo_path` | `{root}` |\n", encoding="utf-8")
    monkeypatch.setenv("DONE_SWEEP_USER_FACTS", str(facts))


def test_hygiene_child_pass_keeps_gate_green(
    tmp_path, sweep_env, mktemp_repo, monkeypatch
):
    """[class: REPOSITORY_TEST] A scan child reporting pass (exit 0 with a
    final `OUTCOME: pass` row) keeps the gate green."""
    root = mktemp_repo("hygiene-pass")
    write_facts(root)
    write_stub_hygiene_scanner(root, "pass")
    _seed_skills_repo_user_facts(tmp_path, monkeypatch, root)

    result = run_gate("sensitive-data-scan", ctx_for(root))

    assert result.rc == 0, result.message


def test_hygiene_child_findings_lands_finding(
    tmp_path, sweep_env, mktemp_repo, monkeypatch
):
    """[class: REPOSITORY_TEST] A scan child reporting findings (exit 1 with
    a final `OUTCOME: fail` row) keeps landing in the findings bucket with
    the child's tail rows, and the OUTCOME row itself never leaks into the
    finding text."""
    root = mktemp_repo("hygiene-findings")
    write_facts(root)
    write_stub_hygiene_scanner(root, "fail")
    _seed_skills_repo_user_facts(tmp_path, monkeypatch, root)

    result = run_gate("sensitive-data-scan", ctx_for(root))

    assert result.rc == 1, result.message
    assert "public-hygiene scan failed" in result.message
    assert "FAIL: stub-hit" in result.message
    assert "OUTCOME:" not in result.message


def test_hygiene_child_indeterminate_lands_indeterminate(
    tmp_path, sweep_env, mktemp_repo, monkeypatch
):
    """[class: REPOSITORY_TEST] A scan child reporting indeterminate (exit 2
    with a final `OUTCOME: indeterminate` row) lands the gate in the
    indeterminate bucket naming the child: the gate exits 2 and never
    collapses the child's uncertainty into a finding."""
    root = mktemp_repo("hygiene-indeterminate")
    write_facts(root)
    write_stub_hygiene_scanner(root, "indeterminate")
    _seed_skills_repo_user_facts(tmp_path, monkeypatch, root)

    result = run_gate("sensitive-data-scan", ctx_for(root))

    assert result.rc == 2, result.message
    assert "scan-public-hygiene.sh" in result.message
    assert "indeterminate" in result.message


def test_hygiene_child_tool_error_lands_tool_error(
    tmp_path, sweep_env, mktemp_repo, monkeypatch
):
    """[class: REPOSITORY_TEST] A scan child reporting tool error (exit 3
    with a final `OUTCOME: tool_error` row) lands the gate in the tool-error
    bucket naming the child: a scan that could not run reliably is never a
    finding."""
    root = mktemp_repo("hygiene-tool-error")
    write_facts(root)
    write_stub_hygiene_scanner(root, "tool-error")
    _seed_skills_repo_user_facts(tmp_path, monkeypatch, root)

    result = run_gate("sensitive-data-scan", ctx_for(root))

    assert result.rc == 3, result.message
    assert "scan-public-hygiene.sh" in result.message
    assert "tool error" in result.message


def test_hygiene_child_without_outcome_line_is_tool_error(
    tmp_path, sweep_env, mktemp_repo, monkeypatch
):
    """[class: REPOSITORY_TEST] A legacy scan child that exits 0 emitting no
    final `OUTCOME:` row classifies tool error per the contract's no-line
    rule winning over the exit code: the gate exits 3 naming the child,
    never a silent pass."""
    root = mktemp_repo("hygiene-no-line")
    write_facts(root)
    write_stub_hygiene_scanner(root, "no-line")
    _seed_skills_repo_user_facts(tmp_path, monkeypatch, root)

    result = run_gate("sensitive-data-scan", ctx_for(root))

    assert result.rc == 3, result.message
    assert "scan-public-hygiene.sh" in result.message
    assert "no final OUTCOME line" in result.message


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

    reviews = root / ".ai-playbook/reviews"
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
    review_rel = ".ai-playbook/reviews/2026-09-22-atomic-review-r1.md"
    (root / "docs/history/plans").mkdir(parents=True)
    (root / plan).write_text("plan body\n", encoding="utf-8")
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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
    assert payload["start_porcelain"] == [
        " M README.md",
        "?? .ai-playbook/facts.md",
        "?? .ai-playbook/reviews/2026-09-22-atomic-review-r1.md",
        "?? note.txt",
    ]
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
    review_rel = ".ai-playbook/reviews/2026-09-22-peer-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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
    same repo (the first run's boundary finalized in between, keeping the
    boundary clean the documented way), expects two
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
    # write starts from a clean boundary the documented way.
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
def write_stub_review_staging_validator(root: Path, stub_body: str | None = None) -> Path:
    """Repo-local stub review-staging validator (subprocess seam).

    Appends each validated target to ``REVIEW_STAGING_STUB_LOG`` (one path per
    line, invocation record) then answers in the migrated child outcome
    contract: a target whose basename contains ``invalid`` gets a named
    finding plus a final ``OUTCOME: fail`` row and exit 1; every other target
    gets ``OUTCOME: pass`` and exit 0. A custom ``stub_body`` replaces only
    the verdict logic (the outcome-arm fixtures use it to model the
    indeterminate and tool-error children and the no-line legacy shape); the
    invocation-log prologue stays wired either way.
    """
    if stub_body is None:
        stub_body = (
            "if 'invalid' in os.path.basename(target):\n"
            "    print('HARD: staging metadata invalid (stub finding): ' + target)\n"
            "    print('OUTCOME: fail')\n"
            "    sys.exit(1)\n"
            "print('OUTCOME: pass')\n"
            "sys.exit(0)\n"
        )
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
        + stub_body,
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
    owned_rel = ".ai-playbook/reviews/2026-09-22-own-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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
    unseen_rel = ".ai-playbook/reviews/2026-09-22-peer-invalid-review-r1.md"
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
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    gone_rel = ".ai-playbook/reviews/2026-09-21-gone-review-r1.md"
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
    owned_rel = ".ai-playbook/reviews/2026-09-22-own-review-r1.md"
    foreign_rel = ".ai-playbook/reviews/2026-09-19-invalid-peer-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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
    claimed_rel = ".ai-playbook/reviews/2026-09-18-invalid-own-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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


# --------------------------------------------------------------------------- #
# Outcome-contract migration batch 2, Task 1: the review-staging child arm
# branches on the migrated validator child's four outcomes (scripts/
# OUTCOME_CONTRACT.md) instead of collapsing every nonzero exit into the
# failed bucket, and the contract's no-line rule wins over the exit code.
# --------------------------------------------------------------------------- #
def _seed_single_owned_review(root: Path, owned_rel: str, run_name: str) -> None:
    """One manifest-owned staging review in the session window (the minimal
    fixture behind the child-outcome arms)."""
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    (root / owned_rel).write_text("own staging review\n", encoding="utf-8")
    _seed_run_manifest(
        root, run_name, current.name, str(root), now,
        owned_review_paths=[owned_rel],
    )


def test_review_staging_child_indeterminate_lands_indeterminate(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A validator child reporting indeterminate
    (exit 2 with a final `OUTCOME: indeterminate` line) lands the gate in the
    indeterminate bucket naming the target: the gate exits 2 and never
    collapses the child's uncertainty into a fail."""
    root = mktemp_repo("child-indeterminate")
    write_stub_review_staging_validator(
        root,
        "print('validator could not determine the verdict (stub)')\n"
        "print('OUTCOME: indeterminate')\n"
        "sys.exit(2)\n",
    )
    owned_rel = ".ai-playbook/reviews/2026-09-18-own-review-r1.md"
    _seed_single_owned_review(root, owned_rel, "run-child-indet")

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 2, result.message
    assert owned_rel in result.message
    assert "indeterminate" in result.message


def test_review_staging_child_tool_error_lands_tool_error(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A validator child reporting tool error
    (exit 3 with a final `OUTCOME: tool_error` line) lands the gate in the
    tool-error bucket naming the target: a child that could not run reliably
    is never a staging fail."""
    root = mktemp_repo("child-tool-error")
    write_stub_review_staging_validator(
        root,
        "print('validator cannot open the input (stub)')\n"
        "print('OUTCOME: tool_error')\n"
        "sys.exit(3)\n",
    )
    owned_rel = ".ai-playbook/reviews/2026-09-18-own-review-r1.md"
    _seed_single_owned_review(root, owned_rel, "run-child-tool-error")

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 3, result.message
    assert owned_rel in result.message
    assert "tool error" in result.message


def test_review_staging_child_without_outcome_line_is_tool_error(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A legacy child that exits 0 emitting no final
    `OUTCOME:` line classifies tool error per the contract's no-line rule
    winning over the exit code: the gate exits 3 naming the target, never a
    silent pass."""
    root = mktemp_repo("child-no-line")
    write_stub_review_staging_validator(
        root,
        "print('legacy validator without outcome reporting')\n"
        "sys.exit(0)\n",
    )
    owned_rel = ".ai-playbook/reviews/2026-09-18-own-review-r1.md"
    _seed_single_owned_review(root, owned_rel, "run-child-no-line")

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 3, result.message
    assert owned_rel in result.message
    assert "no final OUTCOME line" in result.message


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-05-review-record-noncanonical-fences.md
# Task 1: backup-exclusion filter in the review-staging gate's candidate
# derivation. Preservation backups (the record-selection helper's timestamped
# byte-identical copy pairs, named by its single BACKUP_INFIX grammar) are
# audit state, never live review records: a backup's stale Supersedes link can
# never satisfy the validator's name-based back-reference check, so validating
# one is an unsound false-block that refused a witnessed closeout.
# --------------------------------------------------------------------------- #
def _seed_reviews_record_pair(reviews: Path, stem: str) -> None:
    """One live record pair (markdown plus sidecar twin) under reviews_dir,
    the shape the helper's backup operation requires."""
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / f"{stem}.md").write_text(f"stale record {stem}\n", encoding="utf-8")
    (reviews / f"{stem}.stats.json").write_text("{}\n", encoding="utf-8")


def _emit_helper_backup_pair(reviews: Path, stem: str) -> tuple[Path, Path]:
    """Emit the preservation backup pair through the helper's own ``backup``
    operation (the single grammar source), then remove the live pair the way
    the witnessed incident left the directory (backups only, record replaced
    by the successor round)."""
    import review_record_selection as rrs

    backup_md, backup_sidecar = rrs.create_backup(reviews / f"{stem}.md")
    assert lib.BACKUP_INFIX in backup_md.name
    assert lib.BACKUP_INFIX in backup_sidecar.name
    (reviews / f"{stem}.md").unlink()
    (reviews / f"{stem}.stats.json").unlink()
    return backup_md, backup_sidecar


def test_review_staging_manifest_owned_backup_pair_excluded(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a run manifest owning a canonical
    staging review plus a preservation backup pair emitted by the
    record-selection helper's own backup operation, expects both pair members
    excluded from validation with one informational report line each
    (relative path plus reason, never a failure) while the canonical owned
    record is still validated; the backup files stay byte-identical on
    disk (audit state, never touched)."""
    root = mktemp_repo("owned-backup-pair")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    reviews = root / ".ai-playbook/reviews"
    _seed_reviews_record_pair(reviews, "2026-10-05-plan-review-r1")
    backup_md, backup_sidecar = _emit_helper_backup_pair(
        reviews, "2026-10-05-plan-review-r1"
    )
    backup_md_bytes = backup_md.read_bytes()
    backup_sidecar_bytes = backup_sidecar.read_bytes()
    canonical_rel = ".ai-playbook/reviews/2026-10-05-plan-review-r2.md"
    (reviews / "2026-10-05-plan-review-r2.md").write_text(
        "owned canonical staging review\n", encoding="utf-8"
    )
    _seed_run_manifest(
        root,
        "run-owned-backup",
        current.name,
        str(root),
        now,
        owned_review_paths=[
            canonical_rel,
            ".ai-playbook/reviews/" + backup_md.name,
            ".ai-playbook/reviews/" + backup_sidecar.name,
        ],
    )
    stub_log = tmp_path / "owned-backup-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    backup_lines = [
        row
        for row in result.warnings
        if "excluded preservation backup" in row
    ]
    assert len(backup_lines) == 2, result.warnings
    assert any(".ai-playbook/reviews/" + backup_md.name in row for row in backup_lines)
    assert any(
        ".ai-playbook/reviews/" + backup_sidecar.name in row for row in backup_lines
    )
    assert all("never a live review record" in row for row in backup_lines)
    invocations = stub_log.read_text(encoding="utf-8")
    assert canonical_rel in invocations
    assert backup_md.name not in invocations
    assert backup_sidecar.name not in invocations
    assert backup_md.read_bytes() == backup_md_bytes
    assert backup_sidecar.read_bytes() == backup_sidecar_bytes


def test_review_staging_canonical_supersedes_chain_survives_backup_exclusion(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] The witnessed false-block regression shape: a
    validator whose name-based back-reference check refuses any target
    carrying the backup infix (a byte-identical backup can never match its
    successor's Supersedes link) plus a manifest owning a canonical successor
    record with an intact round chain and the stale-linked backup pair.
    Expects the gate green with the canonical record validated in full while
    both backup members are excluded informationally and never reach the
    validator (before the filter this exact fixture failed the closeout on
    the backup's stale link)."""
    root = mktemp_repo("supersedes-chain")
    write_stub_review_staging_validator(
        root,
        f"if '{lib.BACKUP_INFIX}' in os.path.basename(target):\n"
        "    print('HARD: Supersedes back-reference mismatched (stub: a "
        "byte-identical backup never name-matches its successor link): '\n"
        "          + target)\n"
        "    print('OUTCOME: fail')\n"
        "    sys.exit(1)\n"
        "print('OUTCOME: pass')\n"
        "sys.exit(0)\n",
    )
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    reviews = root / ".ai-playbook/reviews"
    _seed_reviews_record_pair(reviews, "2026-10-05-plan-review-r1")
    backup_md, backup_sidecar = _emit_helper_backup_pair(
        reviews, "2026-10-05-plan-review-r1"
    )
    canonical_rel = ".ai-playbook/reviews/2026-10-05-plan-review-r2.md"
    (reviews / "2026-10-05-plan-review-r2.md").write_text(
        "canonical successor record (r2 of the backed-up r1)\n",
        encoding="utf-8",
    )
    _seed_run_manifest(
        root,
        "run-supersedes-chain",
        current.name,
        str(root),
        now,
        owned_review_paths=[
            canonical_rel,
            ".ai-playbook/reviews/" + backup_md.name,
            ".ai-playbook/reviews/" + backup_sidecar.name,
        ],
    )
    stub_log = tmp_path / "supersedes-chain-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    assert any("excluded preservation backup" in row for row in result.warnings)
    invocations = stub_log.read_text(encoding="utf-8")
    assert canonical_rel in invocations
    assert backup_md.name not in invocations
    assert backup_sidecar.name not in invocations


def test_review_staging_window_arm_real_backup_pair_byte_identical(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] A window-fallback reviews directory (no run
    manifest) holding a real helper-emitted backup pair plus a canonical
    record expects byte-identical scope output: the staging-path predicate
    already refused the pair upstream (BACKUP_NAME_RE for the markdown, the
    .md gate for the sidecar twin), so the filter adds zero report lines and
    the canonical record stays the sole validated candidate (characterization
    of the pre-existing exclusion; defense-in-depth only on this arm)."""
    root = mktemp_repo("window-backup-pair")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    reviews = root / ".ai-playbook/reviews"
    _seed_reviews_record_pair(reviews, "2026-09-21-branch-review-r1")
    backup_md, backup_sidecar = _emit_helper_backup_pair(
        reviews, "2026-09-21-branch-review-r1"
    )
    canonical = reviews / "2026-09-21-branch-review-r2.md"
    canonical.write_text("canonical staging review\n", encoding="utf-8")
    stub_log = tmp_path / "window-backup-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    scope = derive_review_staging_scope(ctx_for(root))

    assert scope.manifest_scoped is False
    assert [p.name for p in scope.candidates] == [canonical.name]
    assert scope.report_lines == []

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    assert result.warnings == []
    invocations = stub_log.read_text(encoding="utf-8")
    assert canonical.name in invocations
    assert backup_md.name not in invocations
    assert backup_sidecar.name not in invocations


def test_review_staging_window_arm_handmade_backup_name_excluded(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] A window-arm candidate whose name matches the
    helper's BACKUP_INFIX grammar but not the validator's timestamp-shaped
    BACKUP_NAME_RE slips past the staging-path predicate and is excluded by
    the filter with its informational report line (the defense-in-depth arm:
    never validated, never a failure)."""
    root = mktemp_repo("window-handmade-backup")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    reviews = root / ".ai-playbook/reviews"
    reviews.mkdir(parents=True)
    handmade_rel = ".ai-playbook/reviews/2026-09-21-plan-review.backup-handmade.md"
    (root / handmade_rel).write_text(
        "helper-grammar name without the timestamp shape\n", encoding="utf-8"
    )
    stub_log = tmp_path / "handmade-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    scope = derive_review_staging_scope(ctx_for(root))

    assert scope.candidates == []
    assert len(scope.report_lines) == 1
    assert "excluded preservation backup" in scope.report_lines[0]
    assert handmade_rel in scope.report_lines[0]

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    assert scope.report_lines[0] in result.warnings
    assert not stub_log.exists() or not stub_log.read_text(encoding="utf-8")


def test_review_staging_backup_free_directory_byte_identical(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] A backup-free manifest-owned reviews
    directory expects byte-identical scope output: exactly the owned
    canonical candidate, an empty report-lines channel, and a green gate
    with zero warnings (the filter is a no-op when no name carries the
    infix)."""
    root = mktemp_repo("backup-free")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    canonical_rel = ".ai-playbook/reviews/2026-09-22-own-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    (root / canonical_rel).write_text(
        "owned staging review\n", encoding="utf-8"
    )
    _seed_run_manifest(
        root, "run-backup-free", current.name, str(root), now,
        owned_review_paths=[canonical_rel],
    )

    scope = derive_review_staging_scope(ctx_for(root))

    assert scope.manifest_scoped is True
    assert [p.name for p in scope.candidates] == ["2026-09-22-own-review-r1.md"]
    assert scope.report_lines == []

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    assert result.warnings == []


def test_review_staging_receipt_namespace_excluded_universe_and_validation(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given an execution-completion receipt under
    the reviews home (the ``*-plan-review-<slug>-exec-r<N>.md`` grammar whose
    optional ``-r<N>`` tail the staging predicate used to pull into the
    staging universe), expects the receipt absent from the Step 0
    claim-or-foreign enumeration universe while a genuine staging doc stays
    enumerated; and, when a run manifest claims the receipt anyway, expects
    it excluded from validation with one informational line, the validator
    stub never invoked on it, and the bytes preserved on disk, while the
    archive gate's independent discovery (``_has_exec_review_record``) still
    finds it as execution evidence."""
    root = mktemp_repo("receipt-exclusion")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    reviews = root / ".ai-playbook/reviews"
    reviews.mkdir(parents=True)
    receipt_rel = ".ai-playbook/reviews/2026-10-08-plan-review-demo-plan-exec-r2.md"
    receipt = root / receipt_rel
    receipt.write_text(
        "# Exec review r2\n\nVerdict: ready=yes, zero blocking.\n",
        encoding="utf-8",
    )
    receipt_bytes = receipt.read_bytes()
    genuine_rel = ".ai-playbook/reviews/2026-10-08-plan-review-demo-plan-r2.md"
    (root / genuine_rel).write_text("genuine staged review\n", encoding="utf-8")

    universe = {p.name for p in lib._all_staging_review_paths(ctx_for(root))}
    assert receipt.name not in universe, sorted(universe)
    assert Path(genuine_rel).name in universe

    _seed_run_manifest(
        root,
        "run-receipt",
        current.name,
        str(root),
        now,
        owned_review_paths=[receipt_rel],
    )
    stub_log = tmp_path / "receipt-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    excluded_lines = [
        row
        for row in result.warnings
        if "excluded execution-completion receipt" in row
    ]
    assert len(excluded_lines) == 1, result.warnings
    assert receipt_rel in excluded_lines[0]
    assert "archive certification discovers it independently" in excluded_lines[0]
    invocations = (
        stub_log.read_text(encoding="utf-8") if stub_log.exists() else ""
    )
    assert receipt.name not in invocations
    assert receipt.read_bytes() == receipt_bytes
    assert lib._has_exec_review_record(ctx_for(root), "demo-plan") is True


def test_review_staging_lone_backup_members_and_infix_embedded_names_excluded(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] The same BACKUP_INFIX name test excludes a
    manifest-owned backup markdown alone without its sidecar, a sidecar twin
    alone without its markdown, and a record-shaped name that embeds the
    infix as part of a longer segment (the helper's select path refuses to
    emit such slugs, so no live record collides): each gets its own
    informational line and none reaches the validator."""
    root = mktemp_repo("lone-backup-members")
    write_stub_review_staging_validator(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    reviews = root / ".ai-playbook/reviews"
    reviews.mkdir(parents=True)
    lone_md_rel = (
        ".ai-playbook/reviews/2026-10-05-doc-review-r1.md.backup-20261005T120000.md"
    )
    lone_sidecar_rel = (
        ".ai-playbook/reviews/2026-10-05-rfc-review-r1.md.backup-20261005T120000"
        ".stats.json"
    )
    infix_embedded_rel = ".ai-playbook/reviews/2026-10-05-plan.backup-notes-review-r1.md"
    (root / lone_md_rel).write_text("lone backup markdown\n", encoding="utf-8")
    (root / lone_sidecar_rel).write_text("{}\n", encoding="utf-8")
    (root / infix_embedded_rel).write_text(
        "record-shaped name embedding the infix\n", encoding="utf-8"
    )
    _seed_run_manifest(
        root,
        "run-lone-members",
        current.name,
        str(root),
        now,
        owned_review_paths=[lone_md_rel, lone_sidecar_rel, infix_embedded_rel],
    )
    stub_log = tmp_path / "lone-members-invocations.txt"
    monkeypatch.setenv("REVIEW_STAGING_STUB_LOG", str(stub_log))

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    backup_lines = [
        row
        for row in result.warnings
        if "excluded preservation backup" in row
    ]
    assert len(backup_lines) == 3, result.warnings
    for rel in (lone_md_rel, lone_sidecar_rel, infix_embedded_rel):
        assert any(rel in row for row in backup_lines), result.warnings
    assert not stub_log.exists() or not stub_log.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-10-done-closeout-lock-span-and-output-cost.md
# Task 2: bounded sweep-gate reports with run-scoped, file-backed full lists.
# --------------------------------------------------------------------------- #
def _seed_foreign_review_docs(root: Path, count: int) -> list[str]:
    """Seed ``count`` foreign-marked staging docs (each one report line) and
    return their repo-relative paths in seeding order."""
    reviews = root / ".ai-playbook/reviews"
    reviews.mkdir(parents=True)
    rels = []
    for i in range(count):
        rel = f".ai-playbook/reviews/2026-09-19-peer-review-r{i:02d}.md"
        (root / rel).write_text("peer staging review\n", encoding="utf-8")
        rels.append(rel)
    return rels


def _gate_reports_dir(root: Path) -> Path:
    return root / "docs" / "tmp" / "done-session" / "gate-reports"


def _header_count(text: str) -> int:
    """Parse the leading integer of the bounded header line (the one line
    carrying the total count)."""
    for row in text.splitlines():
        if "total (showing the first" in row:
            return int(row.split(" ", 1)[0])
    raise AssertionError(f"no bounded count header line in: {text}")


def test_review_staging_bounded_report_shape_and_verdict_parity(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a staging tree whose reportable entries
    exceed the sample bound, expects the gate verdict to stay green (parity
    with the frozen classification: foreign artifacts are warnings, never
    failures) and the emitted report to carry a count header, at most 10
    sample lines, and the full-list file name under the done-session
    gate-reports home (this shape assertion is the RED target against
    today's unbounded emission)."""
    root = mktemp_repo("bounded-shape")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    rels = _seed_foreign_review_docs(root, 12)
    _seed_run_manifest(
        root,
        "bounded-shape-r1",
        current.name,
        str(root),
        now,
        foreign_review_paths=rels,
    )

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    warnings_text = "\n".join(result.warnings)
    assert _header_count(warnings_text) == 12, result.warnings
    # 10: the pinned sample bound (lib SAMPLE_LIMIT).
    named = [rel for rel in rels if rel in warnings_text]
    assert 1 <= len(named) <= 10, result.warnings
    assert "full list: " in warnings_text, result.warnings
    listed = warnings_text.split("full list: ", 1)[1].splitlines()[0]
    assert "gate-reports" in listed, result.warnings
    assert any(path.name in listed for path in _gate_reports_dir(root).glob("*")), (
        result.warnings
    )


def test_review_staging_full_list_fidelity_and_distinct_second_run(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a candidate set larger than the sample
    bound, expects the written full-list file to contain every entry the old
    inline emission would have printed, one per line; given a second run in
    the same checkout (its own marker and manifest), expects its report file
    name to be distinct from the first run's."""
    root = mktemp_repo("bounded-fidelity")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    marker_two = make_marker(root, now, os.getpid())
    rels = _seed_foreign_review_docs(root, 12)
    _seed_run_manifest(
        root,
        "bounded-r1",
        marker_two.name,
        str(root),
        now,
        foreign_review_paths=rels,
    )

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    reports = sorted(_gate_reports_dir(root).glob("*"))
    assert len(reports) == 1, [str(p) for p in reports]
    first = reports[0]
    assert first.name == "run-bounded-r1-review-staging-full.txt", first.name
    lines = first.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 12, lines
    for rel in rels:
        matches = [row for row in lines if rel in row]
        assert len(matches) == 1, (rel, lines)
        assert matches[0].startswith(
            "foreign staging doc excluded from validation"
        ), matches[0]

    # Second run in the same checkout: a newer marker plus its own manifest.
    now_two = time.time() + 60
    marker_three = make_marker(root, now_two, os.getpid())
    _seed_run_manifest(
        root,
        "bounded-r2",
        marker_three.name,
        str(root),
        now_two,
        foreign_review_paths=rels,
    )

    result_two = run_gate("review-staging", ctx_for(root))

    assert result_two.rc == 0, result_two.message
    reports = sorted(_gate_reports_dir(root).glob("*"))
    names = [path.name for path in reports]
    assert len(names) == 2, names
    assert len(set(names)) == 2, "second run's report file name must differ"
    second = reports[1]
    assert second.name == "run-bounded-r2-review-staging-full.txt", second.name
    second_lines = second.read_text(encoding="utf-8").splitlines()
    assert len(second_lines) == 12, second_lines
    for rel in rels:
        assert any(rel in row for row in second_lines), (rel, second_lines)


def test_review_staging_small_report_set_passes_through_unbounded(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given 10 or fewer reportable entries, expects
    the warnings to pass through inline exactly as today (one line per entry,
    no count header, no full-list file, no gate-reports directory)."""
    root = mktemp_repo("bounded-small")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    rels = _seed_foreign_review_docs(root, 3)
    _seed_run_manifest(
        root,
        "bounded-small-r1",
        current.name,
        str(root),
        now,
        foreign_review_paths=rels,
    )

    result = run_gate("review-staging", ctx_for(root))

    assert result.rc == 0, result.message
    assert len(result.warnings) == 3, result.warnings
    for rel in rels:
        assert sum(1 for row in result.warnings if rel in row) == 1, (
            rel,
            result.warnings,
        )
    assert not any("total (showing the first" in row for row in result.warnings)
    assert not _gate_reports_dir(root).exists()


@pytest.mark.skipif(os.getuid() == 0, reason="root ignores chmod")
def test_review_staging_write_failure_degrades_to_unbounded_inline(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a staging tree with more than 10
    reportable entries and the gate-reports directory made unwritable,
    expects the gate verdict to equal the writable run's verdict, the
    message to carry the full inline enumeration plus one warning line
    naming the failed write path, and the exit status to stay pass (the
    write-failure arm is never a gate failure)."""
    root = mktemp_repo("bounded-writefail")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    rels = _seed_foreign_review_docs(root, 12)
    _seed_run_manifest(
        root,
        "bounded-writefail-r1",
        current.name,
        str(root),
        now,
        foreign_review_paths=rels,
    )

    writable = run_gate("review-staging", ctx_for(root))
    assert writable.rc == 0, writable.message
    reports_dir = _gate_reports_dir(root)
    # The writable run owns the directory (the helper creates it on demand);
    # pre-creating it here keeps the arm's setup faithful when the gate does
    # not yet write full lists at all.
    reports_dir.mkdir(parents=True, exist_ok=True)
    # Drop the first run's report file: writing over an existing file needs
    # only file permission, and the arm under test is the unwritable parent.
    for stale_report in reports_dir.glob("*"):
        stale_report.unlink()
    os.chmod(reports_dir, 0o500)
    try:
        degraded = run_gate("review-staging", ctx_for(root))

        assert degraded.rc == 0, degraded.message
        assert degraded.rc == writable.rc, "verdict parity under write failure"
        warnings_text = "\n".join(degraded.warnings)
        for rel in rels:
            assert rel in warnings_text, (rel, degraded.warnings)
        failed_path = (
            reports_dir / "run-bounded-writefail-r1-review-staging-full.txt"
        ).resolve()
        failure_lines = [
            row for row in degraded.warnings if "full list write failed" in row
        ]
        assert len(failure_lines) == 1, degraded.warnings
        assert str(failed_path) in failure_lines[0], degraded.warnings
    finally:
        os.chmod(reports_dir, 0o755)


def test_docs_tmp_sweep_bounded_kept_shape(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given more than 10 kept entries, expects the
    docs-tmp sweep message to carry the count, at most 10 sample rows, and
    the full-list file name (no run manifest in this tree, so the phase-gate
    name scopes the file), with the full enumeration written one entry per
    line under the done-session gate-reports home (RED target against
    today's unbounded kept join)."""
    root = make_repo(tmp_path, "bounded-kept", gitignore_docs=True)
    write_facts(root)
    tmp_dir = root / "docs/tmp"
    tmp_dir.mkdir(parents=True)
    names = [f"scratch-kept-{i:02d}" for i in range(12)]
    for name in names:
        (tmp_dir / name).mkdir()
        (tmp_dir / name / "work.txt").write_text("scratch\n", encoding="utf-8")

    result = run_gate("docs-tmp-sweep", ctx_for(root))

    assert result.rc == 0, result.message
    assert "kept=12" in result.message, result.message
    assert "12 entries total (showing the first 10)" in result.message, (
        result.message
    )
    named = [name for name in names if name in result.message]
    assert named == names[:10], result.message
    assert "full list: " in result.message, result.message
    listed = result.message.split("full list: ", 1)[1]
    assert "gate-reports" in listed, result.message
    full_list = _gate_reports_dir(root) / "docs-tmp-sweep-full.txt"
    assert full_list.is_file(), listed
    lines = full_list.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 12, lines
    for name in names:
        matches = [row for row in lines if name in row]
        assert len(matches) == 1, (name, lines)
        assert matches[0] == f"docs/tmp/{name} (unclear ownership or active work)", (
            matches[0]
        )


def test_docs_tmp_sweep_small_kept_set_lists_inline_exactly(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Given 10 or fewer kept entries, expects the
    message to list them inline exactly as today (the same kept join), with
    no warnings, no count header, and no gate-reports directory."""
    root = make_repo(tmp_path, "bounded-kept-small", gitignore_docs=True)
    write_facts(root)
    tmp_dir = root / "docs/tmp"
    tmp_dir.mkdir(parents=True)
    for name in ("scratch-a", "scratch-b"):
        (tmp_dir / name).mkdir()
        (tmp_dir / name / "work.txt").write_text("scratch\n", encoding="utf-8")
    expected_join = (
        "docs/tmp/scratch-a (unclear ownership or active work), "
        "docs/tmp/scratch-b (unclear ownership or active work)"
    )

    result = run_gate("docs-tmp-sweep", ctx_for(root))

    assert result.rc == 0, result.message
    assert result.message.endswith("; kept: " + expected_join), result.message
    assert "total (showing the first" not in result.message, result.message
    assert result.warnings == [], result.warnings
    assert not _gate_reports_dir(root).exists()


def test_docs_tmp_sweep_prunes_gate_reports_outside_session_window(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] The done-session sweep's prune arm removes
    gate-reports files whose mtime sits strictly older than the previous-run
    anchor (outside the current session window), mirroring the run-start
    marker rule; files inside the window stay."""
    root = make_repo(tmp_path, "bounded-prune", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    make_marker(root, now, os.getpid())
    reports_dir = _gate_reports_dir(root)
    reports_dir.mkdir(parents=True)
    stale = reports_dir / "run-stale-review-staging-full.txt"
    inside = reports_dir / "run-prev-docs-tmp-sweep-full.txt"
    current = reports_dir / "run-cur-review-staging-full.txt"
    for path in (stale, inside, current):
        path.write_text("rows\n", encoding="utf-8")
    os.utime(stale, (now - 7200, now - 7200))
    os.utime(inside, (now - 1800, now - 1800))

    result = run_gate("docs-tmp-sweep", ctx_for(root))

    assert result.rc == 0, result.message
    assert not stale.exists(), "gate-reports file outside the window pruned"
    assert str(stale.resolve()) in result.message, result.message
    assert inside.exists(), "file inside the session window immune"
    assert current.exists(), "current-run file immune"


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
    naming the orphan run_id and to warn with the named
    ``write-manifest: undisposed-interrupted (reported, not failing):``
    line while the write continues (the new manifest lands past the
    warning); a prior manifest with ``complete`` true is never
    reported as an orphan (this is what keeps a completed commit-less run
    from misfiring the detection) and never warns."""
    # Arm 1: an unfinalized prior manifest is reported AND warned; the
    # boundary decision stays visible, the write proceeds.
    root = mktemp_repo("orphan")
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-orphan-reported"
    _seed_run_manifest(root, orphan_id, prev.name, str(root), time.time() - 10)
    # HEAD advances after the orphan died: the warning is independent of it.
    (root / "post-orphan.md").write_text("committed after the orphan died\n", encoding="utf-8")
    git(root, "add", "post-orphan.md")
    git(root, "commit", "-m", "post orphan", "-q")
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest"])

    assert rc == 0
    captured = capsys.readouterr()
    assert "interrupted run" in captured.out
    assert orphan_id in captured.out
    assert "write-manifest: undisposed-interrupted (reported, not failing):" in captured.err
    assert orphan_id in captured.err
    done_session = root / "docs" / "tmp" / "done-session"
    manifests = sorted(p.name for p in done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 2  # the orphan plus the new run's manifest

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
    review_rel = ".ai-playbook/reviews/2026-09-22-adopt-review-r1.md"
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
    # closes first (the Step 6 finalize, one of the warning's named exits),
    # keeping the boundary clean the documented way before the next write.
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
    expects the write-manifest invocation to succeed while the report line
    surfaces the orphan and the demoted warning names the remedies
    (demotion program change 3: adoption stays explicit only, and the
    warning keeps the decision visible instead of passive); the doc-registry
    gate over the same tree still runs clean after the new manifest binds
    the current marker."""
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
    captured = capsys.readouterr()
    # Surfaced, never silently adopted: the report line names the orphan and
    # the demoted warning carries the bounded decision; adoption stays an
    # explicit flag.
    assert "interrupted run" in captured.out
    assert orphan_id in captured.out
    assert "write-manifest: undisposed-interrupted (reported, not failing):" in captured.err
    assert orphan_id in captured.err
    assert f"--adopt {orphan_id}" in captured.err
    # The new run's manifest was written past the warning, with no
    # implicit adoption (the test's namesake: adoption is explicit only).
    done_session_files = sorted(
        (root / "docs" / "tmp" / "done-session").glob("run-manifest-*.json")
    )
    assert len(done_session_files) == 2
    assert _newest_manifest_payload(
        root, exclude_run_id=orphan_id
    )["adopted_from"] is None

    stdin_log = tmp_path / "explicit-stdin.txt"
    monkeypatch.setenv("DOC_REGISTRY_STUB_STDIN_LOG", str(stdin_log))
    monkeypatch.delenv("DOC_REGISTRY_STUB_FLAG", raising=False)
    monkeypatch.delenv("DOC_REGISTRY_STUB_REJECT_BARE", raising=False)

    result = run_gate("doc-registry", ctx_for(root))

    assert result.rc == 0
    # Post-demotion the new manifest binds the current marker while the
    # orphan's commit stays unclassified: the new run made no commits and
    # adopted nothing, so the gate's check-writes set carries no committed
    # row and no foreign warning names the orphan's commit.
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
    reviews = root / ".ai-playbook" / "reviews"
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
    peer_a = ".ai-playbook/reviews/2026-09-25-peer-review-a-r1.md"
    peer_b = ".ai-playbook/reviews/2026-09-25-peer-review-b-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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
    owned = ".ai-playbook/reviews/2026-09-25-adopted-owned-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    peer_a = ".ai-playbook/reviews/2026-09-25-peer-review-a-r1.md"
    peer_b = ".ai-playbook/reviews/2026-09-25-peer-review-b-r1.md"
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
# Plan: docs/history/plans/2026-10-05-done-lifecycle-recovery-gaps.md
# Task 1: --run-marker explicit binding in _cmd_write_manifest.
# --------------------------------------------------------------------------- #
def make_digest_marker(root: Path, epoch: float, pid: int) -> Path:
    """Write a digest-form run-start marker (the current done Step 0 shape:
    the middle field is the 64-hex repo-root digest, not the raw path)."""
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    marker = done_session / marker_name(epoch)
    digest = hashlib.sha256(
        str(root.resolve()).rstrip("/").encode()
    ).hexdigest()
    marker.write_text(f"{int(epoch)} {digest} {pid}\n", encoding="utf-8")
    return marker


def done_session_snapshot(done_session: Path) -> dict:
    """Byte snapshot of every file under the done-session directory, keyed by
    filename (the byte-identical witness the refusal arms require)."""
    return {
        p.name: p.read_bytes()
        for p in sorted(done_session.iterdir())
        if p.is_file()
    }


def test_write_manifest_run_marker_binds_newest_confirmed(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a done-session directory holding two
    content-confirmed run-start markers, ``write-manifest --run-marker``
    pointed at the older marker refuses with a named one-line error and
    writes no manifest; pointed at the newest marker it creates the manifest
    and the record's ``marker`` field names that marker."""
    root = mktemp_repo("run-marker-bind")
    now = time.time()
    old_marker = make_marker(root, now - 3600, os.getpid())
    new_marker = make_digest_marker(root, now, os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    # Older marker: named refusal (not the newest), no manifest written.
    rc = lib.main(["write-manifest", "--run-marker", str(old_marker)])
    assert rc != 0
    err = capsys.readouterr().err
    assert "write-manifest: run-marker-not-newest:" in err
    assert old_marker.name in err
    assert list(done_session.glob("run-manifest-*.json")) == []
    assert list(done_session.glob("*.tmp*")) == []

    # Newest marker: the manifest is created and binds to that marker.
    rc2 = lib.main(["write-manifest", "--run-marker", str(new_marker)])
    assert rc2 == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert payload["marker"] == new_marker.name


def test_write_manifest_run_marker_refusals(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Three refusal arms for
    ``write-manifest --run-marker``: an absent marker path, a marker whose
    content does not confirm under the two-form confirmation, and a marker
    path pointing at a file outside the done-session directory; each expects
    a named one-line refusal, a non-zero exit, and the done-session directory
    byte-identical before and after."""
    root = mktemp_repo("run-marker-refusals")
    marker = make_digest_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    # Arm 1: absent marker path under the done-session directory.
    before = done_session_snapshot(done_session)
    absent = done_session / "run-start-20200101T000000Z"
    rc = lib.main(["write-manifest", "--run-marker", str(absent)])
    assert rc != 0
    err = capsys.readouterr().err
    assert "write-manifest: run-marker-absent:" in err
    assert done_session_snapshot(done_session) == before

    # Arm 2: content that does not confirm (foreign root path record).
    foreign_marker = done_session / "run-start-unconfirmed"
    foreign_marker.write_text(
        f"{int(time.time())} {tmp_path / 'some-other-repo'} 999\n",
        encoding="utf-8",
    )
    before = done_session_snapshot(done_session)
    rc = lib.main(["write-manifest", "--run-marker", str(foreign_marker)])
    assert rc != 0
    err = capsys.readouterr().err
    assert "write-manifest: run-marker-unconfirmed:" in err
    assert done_session_snapshot(done_session) == before

    # Arm 3: confirming content, but the path sits outside the
    # done-session directory.
    outside = root / "outside-done-session.marker"
    digest = hashlib.sha256(
        str(root.resolve()).rstrip("/").encode()
    ).hexdigest()
    outside.write_text(
        f"{int(time.time())} {digest} {os.getpid()}\n", encoding="utf-8"
    )
    before = done_session_snapshot(done_session)
    rc = lib.main(["write-manifest", "--run-marker", str(outside)])
    assert rc != 0
    err = capsys.readouterr().err
    assert "write-manifest: run-marker-outside-done-session:" in err
    assert done_session_snapshot(done_session) == before

    # No arm ever wrote a manifest or left temp residue.
    assert list(done_session.glob("run-manifest-*.json")) == []
    assert list(done_session.glob("*.tmp*")) == []


def test_write_manifest_without_flag_keeps_newest_anchor(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given two content-confirmed markers and the
    ``--run-marker`` flag absent, expects today's behavior: the manifest
    binds to the newest content-confirmed marker."""
    root = mktemp_repo("run-marker-absent-flag")
    now = time.time()
    old_marker = make_marker(root, now - 3600, os.getpid())
    new_marker = make_digest_marker(root, now, os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(["write-manifest"]) == 0
    manifests = list(done_session.glob("run-manifest-*.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert payload["marker"] == new_marker.name
    assert payload["marker"] != old_marker.name


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
    review_rel = ".ai-playbook/reviews/2026-09-27-peer-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
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
    review_rel = ".ai-playbook/reviews/2026-09-27-aliased-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    (root / review_rel).write_text("peer staging review\n", encoding="utf-8")
    alias = tmp_path / "alias-link"
    alias.symlink_to(root, target_is_directory=True)
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"

    assert lib.main(
        [
            "write-manifest",
            "--foreign-review",
            str(alias / ".ai-playbook" / "reviews" / "2026-09-27-aliased-review-r1.md"),
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
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    owned_rel = ".ai-playbook/reviews/2026-09-27-owned-review-r1.md"
    foreign_rel = ".ai-playbook/reviews/2026-09-27-peer-review-r1.md"
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
    missing_review = ".ai-playbook/reviews/2026-09-30-never-landed-r1.md"
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


def test_recover_manifest_refuses_unresolved_peer_boundary(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Witnessed misclassification class: a live
    peer session's undisposed boundary is never closed implicitly by a
    foreign session. Given an undisposed manifest recorded at a live root
    (the fixture checkout itself) whose owned review record resolves nowhere
    (no docs branch carries it), expects ``recover-manifest`` to refuse
    non-zero naming the deliverables-witness reason, leaving the manifest
    byte-identical (complete stays false, no disposition stamp), so the
    boundary stays the peer's own resume surface."""
    root = mktemp_repo("recover-live-peer")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    review_rel = ".ai-playbook/reviews/2026-10-08-plan-review-peer-work-r1.md"
    _seed_run_manifest(
        root,
        "run-peer-live",
        marker_name(now),
        str(root),
        now,
        owned_review_paths=[review_rel],
    )
    manifest_path = done_session / "run-manifest-run-peer-live.json"
    before = manifest_path.read_bytes()

    assert lib.main(["recover-manifest", "--run-id", "run-peer-live"]) == 1

    err = capsys.readouterr().err
    assert "does not resolve on the docs branch" in err
    assert review_rel in err
    assert manifest_path.read_bytes() == before
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload.get("complete") is False
    assert not payload.get("dispositioned")


def test_sync_deferral_availability_check_gates_local_commit(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] The sync-deferral arm's availability check
    decision shape: an explicit docs-branch sync deferral does not block the
    requested local commit when every manifest owned-review claim is present
    under the primary reviews home (the same presence verification the
    migration/removal gates perform). Given a manifest claiming a review
    record, expects the availability check to fail while the record is
    absent, pass once the record exists, and the local commit to complete
    with the docs sync deferred (no docs branch exists in this fixture) with
    the claimed review bytes preserved unchanged on disk."""
    root = mktemp_repo("sync-deferral")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    reviews = root / ".ai-playbook" / "reviews"
    reviews.mkdir(parents=True)
    review_rel = ".ai-playbook/reviews/2026-10-08-plan-review-demo-sync-r1.md"
    _seed_run_manifest(
        root,
        "run-defer",
        current.name,
        str(root),
        now,
        owned_review_paths=[review_rel],
    )
    done_session = root / "docs" / "tmp" / "done-session"
    window = lib.derive_session_window(done_session, root)
    manifest = lib.load_run_manifest(done_session, root, window)
    assert manifest is not None

    def availability_check() -> list[str]:
        return [
            path
            for path in manifest.owned_review_paths
            if not (root / path).is_file()
        ]

    assert availability_check() == [review_rel]

    review_path = root / review_rel
    review_path.write_text("owned review bytes\n", encoding="utf-8")
    review_bytes = review_path.read_bytes()
    assert availability_check() == []

    (root / "notes.md").write_text("local non-lane work\n", encoding="utf-8")
    assert git(root, "add", "notes.md").returncode == 0
    assert git(root, "commit", "-q", "-m", "local work with sync deferred").returncode == 0
    assert git(root, "cat-file", "-e", "HEAD:notes.md").returncode == 0
    assert review_path.read_bytes() == review_bytes


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
        owned_paths=[".ai-playbook/reviews/2026-09-30-never-tracked.md"],
    )
    assert lib.main(["disposition-manifest", "--run-id", never_id]) == 1
    err = capsys.readouterr().err
    assert "deliverables witness failed" in err
    assert ".ai-playbook/reviews/2026-09-30-never-tracked.md" in err


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
    maintenance skill's interrupted-manifest classification arm in its
    canonical survey-arms module pins the proactive
    stale-deployment probe.

    Re-aimed 2026-10-11 (the done target-state flip): the deliverables-
    witness arm phrase is owned by the sweep-gates lib itself (the
    disposition-manifest implementation is the procedure of record; the
    dissolved skill module carried it only as prose)."""
    repo_root = Path(__file__).resolve().parents[1]
    done_text = (
        repo_root / "scripts/done_sweep_gates_lib.py"
    ).read_text(encoding="utf-8")
    maintenance_text = (
        repo_root / "agents/skills/maintenance/survey-arms.md"
    ).read_text(encoding="utf-8")
    assert "HEAD:<recorded path>" in done_text
    assert "stale-deployment" in maintenance_text


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-05-done-lifecycle-recovery-gaps.md Task 2:
# live-root interrupted-manifest recovery command (recover-manifest).
# --------------------------------------------------------------------------- #
def test_recover_manifest_stamps_when_work_verified(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given an interrupted manifest with a live
    recorded root (the 64-hex digest arm, then the legacy raw-path arm), an
    owned plan resolving at its recorded path, and every owned-commits
    ledger entry reachable from HEAD, expects ``recover-manifest`` to exit
    0, to stamp the shared closing record with the reason
    ``work-verified-landed-live-recovery`` and today's date (the operator
    ``--note`` recorded inside it), and to print the ``recovered:`` receipt
    line; the stamped manifest leaves the interrupted-run detection, and a
    second identical invocation reprints the existing record and exits 0
    with the manifest bytes unchanged."""
    root = mktemp_repo("recover-stamps")
    now = time.time()
    run_id = "run-recover-stamps"
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    plan_rel = "docs/history/plans/2026-10-05-recovered-plan.md"
    plan = root / plan_rel
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("plan body\n", encoding="utf-8")  # on-disk arm, unstaged
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    (done_session / f"owned-commits-{run_id}.txt").write_text(
        f"{head}\n", encoding="utf-8"
    )
    _seed_run_manifest(
        root,
        run_id,
        marker_name(now),
        root_digest(root),  # the digest arm of the two-arm matcher
        now,
        owned_plan_paths=[plan_rel],
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    assert [
        m.run_id for m in lib._detect_interrupted_runs(done_session, root)
    ] == [run_id]

    rc = lib.main(
        [
            "recover-manifest",
            "--run-id",
            run_id,
            "--note",
            "operator witnessed recovery",
        ]
    )

    assert rc == 0
    today = datetime.now(timezone.utc).date().isoformat()
    out = capsys.readouterr().out
    assert f"recovered: {run_id} ({today})" in out
    expected = {
        "reason": "work-verified-landed-live-recovery",
        "date": today,
        "note": "operator witnessed recovery",
    }
    reloaded = lib._read_manifest_by_run_id(done_session, run_id)
    assert reloaded is not None
    assert reloaded.dispositioned == expected
    assert reloaded.complete is False  # the recovery closes without finalizing
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["dispositioned"] == expected
    # The stamped record suppresses the interrupted-run detection.
    assert lib._detect_interrupted_runs(done_session, root) == []

    # Second identical invocation: idempotent reprint, exit 0, no rewrite.
    before = manifest_path.read_bytes()
    rc2 = lib.main(
        [
            "recover-manifest",
            "--run-id",
            run_id,
            "--note",
            "operator witnessed recovery",
        ]
    )
    assert rc2 == 0
    out2 = capsys.readouterr().out
    assert "already dispositioned" in out2
    assert "work-verified-landed-live-recovery" in out2
    assert manifest_path.read_bytes() == before

    # The legacy raw-path root record recovers through the other matcher arm.
    legacy_id = "run-recover-legacy-root"
    legacy_plan_rel = "docs/history/plans/2026-10-05-legacy-plan.md"
    legacy_plan = root / legacy_plan_rel
    legacy_plan.parent.mkdir(parents=True, exist_ok=True)
    legacy_plan.write_text("legacy plan\n", encoding="utf-8")
    (done_session / f"owned-commits-{legacy_id}.txt").write_text(
        f"{head}\n", encoding="utf-8"
    )
    _seed_run_manifest(
        root,
        legacy_id,
        marker_name(now + 1),
        str(root.resolve()),  # the legacy raw-path arm
        now + 1,
        owned_plan_paths=[legacy_plan_rel],
    )
    assert lib.main(["recover-manifest", "--run-id", legacy_id]) == 0
    capsys.readouterr()
    reloaded2 = lib._read_manifest_by_run_id(done_session, legacy_id)
    assert reloaded2 is not None
    assert reloaded2.dispositioned is not None
    assert (
        reloaded2.dispositioned["reason"] == "work-verified-landed-live-recovery"
    )


def test_recover_manifest_dead_root_refusal(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given a manifest whose recorded root digest
    names a nonexistent checkout (both matcher arms fail), expects
    ``recover-manifest`` to refuse with a named one-line error directing to
    ``disposition-manifest``, with no record stamped, the manifest bytes
    byte-identical, and the manifest still surfacing as interrupted."""
    root = mktemp_repo("recover-dead-root")
    now = time.time()
    run_id = "run-recover-dead"
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    dead_root = str(tmp_path / "deleted-checkout")
    dead_digest = hashlib.sha256(dead_root.rstrip("/").encode()).hexdigest()
    _seed_run_manifest(root, run_id, marker_name(now), dead_digest, now)
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    before = manifest_path.read_bytes()

    rc = lib.main(["recover-manifest", "--run-id", run_id])

    assert rc == 1
    err = capsys.readouterr().err
    assert "dead root" in err
    assert f"disposition-manifest --run-id {run_id}" in err
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["dispositioned"] is None
    assert manifest_path.read_bytes() == before
    assert [
        m.run_id for m in lib._detect_interrupted_runs(done_session, root)
    ] == [run_id]


def test_recover_manifest_unverified_evidence_refusals(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Two refusal arms on live-root manifests: an
    owned deliverable that resolves through none of the witness arms refuses
    naming the deliverable and the arms attempted; an owned-commits ledger
    entry that exists but is not reachable from HEAD refuses naming the
    commit. Both refusals leave the manifest byte-identical and still
    interrupted."""
    root = mktemp_repo("recover-unverified")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    # Arm A: an owned review path resolving on no docs branch.
    missing_review = ".ai-playbook/reviews/2026-10-05-never-landed-r1.md"
    arm_a = "run-recover-missing-review"
    _seed_run_manifest(
        root,
        arm_a,
        marker_name(now),
        root_digest(root),
        now,
        owned_review_paths=[missing_review],
    )
    manifest_a = done_session / f"run-manifest-{arm_a}.json"
    before_a = manifest_a.read_bytes()

    rc = lib.main(["recover-manifest", "--run-id", arm_a])

    assert rc == 1
    err = capsys.readouterr().err
    assert "deliverables witness failed" in err
    assert missing_review in err  # the deliverable is named
    assert "docs branch" in err  # the arm attempted is named
    assert manifest_a.read_bytes() == before_a
    assert [
        m.run_id for m in lib._detect_interrupted_runs(done_session, root)
    ] == [arm_a]

    # Arm B: a ledger entry that exists but is not reachable from HEAD
    # (a stray commit object, resolvable as a commit, never an ancestor).
    stray = git(root, "commit-tree", "-m", "stray owned commit", "HEAD^{tree}")
    assert stray.returncode == 0
    stray_sha = stray.stdout.strip()
    arm_b = "run-recover-unreachable"
    done_session.mkdir(parents=True, exist_ok=True)
    (done_session / f"owned-commits-{arm_b}.txt").write_text(
        f"{stray_sha}\n", encoding="utf-8"
    )
    _seed_run_manifest(
        root, arm_b, marker_name(now), root_digest(root), now
    )
    manifest_b = done_session / f"run-manifest-{arm_b}.json"
    before_b = manifest_b.read_bytes()

    rc2 = lib.main(["recover-manifest", "--run-id", arm_b])

    assert rc2 == 1
    err2 = capsys.readouterr().err
    assert "owned-commits reachability failed" in err2
    assert stray_sha in err2  # the commit is named
    assert "not reachable from HEAD" in err2
    assert manifest_b.read_bytes() == before_b
    orphan_ids = [
        m.run_id for m in lib._detect_interrupted_runs(done_session, root)
    ]
    assert sorted(orphan_ids) == sorted([arm_a, arm_b])


def test_recover_manifest_state_refusals(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] State refusal arms: an already-``complete``
    manifest refuses (a finalized run is never an interrupted run); a
    manifest adopted by another manifest refuses (an adopted_from link
    names it; adoption owns the continuation); and the unowned-tree
    preservation arm: a verified recovery mutates nothing outside the
    manifest record, witnessed by byte-comparing the worktree and the git
    index before and after (only the manifest JSON's bytes differ)."""
    root = mktemp_repo("recover-state")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    # Arm: already complete refuses.
    complete_id = "run-recover-complete"
    _seed_run_manifest(
        root,
        complete_id,
        marker_name(now),
        root_digest(root),
        now,
        complete=True,
    )
    before = (done_session / f"run-manifest-{complete_id}.json").read_bytes()
    assert lib.main(["recover-manifest", "--run-id", complete_id]) == 1
    assert "already finalized" in capsys.readouterr().err
    assert (
        done_session / f"run-manifest-{complete_id}.json"
    ).read_bytes() == before

    # Arm: already adopted by another manifest refuses.
    victim_id = "run-recover-adopted"
    _seed_run_manifest(
        root, victim_id, marker_name(now), root_digest(root), now
    )
    _seed_run_manifest(
        root,
        "run-recover-adopter",
        marker_name(now),
        str(root.resolve()),
        now + 1,
        adopted_from=victim_id,
    )
    before2 = (done_session / f"run-manifest-{victim_id}.json").read_bytes()
    assert lib.main(["recover-manifest", "--run-id", victim_id]) == 1
    assert "adopts this boundary" in capsys.readouterr().err
    assert (
        done_session / f"run-manifest-{victim_id}.json"
    ).read_bytes() == before2

    # Arm: unowned-tree preservation. The verified recovery's ONLY mutation
    # is the manifest record itself: byte-compare every worktree file
    # (tracked, untracked, and ignored alike) and the index across the run.
    clean_id = "run-recover-tree-clean"
    _seed_run_manifest(
        root, clean_id, marker_name(now), root_digest(root), now
    )
    manifest_path = done_session / f"run-manifest-{clean_id}.json"

    def worktree_snapshot(repo: Path) -> dict:
        return {
            str(p.relative_to(repo)): p.read_bytes()
            for p in sorted(repo.rglob("*"))
            if ".git" not in p.relative_to(repo).parts and p.is_file()
        }

    porcelain_before = git(root, "status", "--porcelain").stdout
    index_before = (root / ".git" / "index").read_bytes()
    worktree_before = worktree_snapshot(root)

    assert lib.main(["recover-manifest", "--run-id", clean_id]) == 0
    capsys.readouterr()

    worktree_after = worktree_snapshot(root)
    index_after = (root / ".git" / "index").read_bytes()
    porcelain_after = git(root, "status", "--porcelain").stdout
    changed = {
        name
        for name in set(worktree_before) | set(worktree_after)
        if worktree_before.get(name) != worktree_after.get(name)
    }
    assert changed == {
        f"docs/tmp/done-session/run-manifest-{clean_id}.json"
    }
    assert index_after == index_before
    assert porcelain_after == porcelain_before


def test_recover_manifest_unlanded_deliverable_refusals_and_note_escape(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] The recovery-side landing discrimination
    over an owned plan resolving only through the on-disk recorded path (an
    uncommitted worktree file, no HEAD arm, no completed-archive twin) with
    the run's owned-commits ledger absent (the reachability witness's
    vacuous-pass shape): the plain invocation refuses with a named one-line
    error listing the unlanded deliverable and the remedy (land the work
    first, or the operator-attested note-backed escape), the manifest stays
    byte-identical and still interrupted; a record-keeping note that merely
    mentions the path (no literal ``note-backed`` marker) still refuses; the
    explicit ``--note`` carrying the literal marker ``note-backed`` plus the
    path stamps the closing record with the recovery reason and the note
    verbatim, suppressing the interrupted-run detection."""
    root = mktemp_repo("recover-unlanded")
    now = time.time()
    run_id = "run-recover-unlanded"
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    plan_rel = "docs/history/plans/2026-10-05-unlanded-plan.md"
    plan = root / plan_rel
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("unlanded plan body\n", encoding="utf-8")  # on-disk only
    # No owned-commits ledger file: the reachability witness passes
    # vacuously, which is exactly the shape the conjunct discriminates.
    _seed_run_manifest(
        root,
        run_id,
        marker_name(now),
        root_digest(root),
        now,
        owned_plan_paths=[plan_rel],
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    before = manifest_path.read_bytes()

    # Arm (a): disk-only plan plus absent ledger refuses.
    rc = lib.main(["recover-manifest", "--run-id", run_id])

    assert rc == 1
    err = capsys.readouterr().err
    assert "unlanded deliverables with no owned-commits ledger" in err
    assert plan_rel in err  # the unlanded deliverable is named
    assert "land the work first" in err
    assert "note-backed" in err  # the remedy names the escape marker
    assert "\n" not in err.strip()  # one line
    assert manifest_path.read_bytes() == before
    assert [
        m.run_id for m in lib._detect_interrupted_runs(done_session, root)
    ] == [run_id]

    # Arm (c): a record-keeping note mentioning the path without the literal
    # marker still refuses (mentioning a path never flips the refusal).
    rc2 = lib.main(
        [
            "recover-manifest",
            "--run-id",
            run_id,
            "--note",
            f"record keeping: {plan_rel} was reviewed in the session notes",
        ]
    )
    assert rc2 == 1
    err2 = capsys.readouterr().err
    assert "unlanded deliverables with no owned-commits ledger" in err2
    assert manifest_path.read_bytes() == before

    # Arm (b): the operator-explicit note-backed escape stamps.
    escape_note = f"note-backed: {plan_rel} - operator attested"
    rc3 = lib.main(
        ["recover-manifest", "--run-id", run_id, "--note", escape_note]
    )
    assert rc3 == 0
    today = datetime.now(timezone.utc).date().isoformat()
    out3 = capsys.readouterr().out
    assert f"recovered: {run_id} ({today})" in out3
    reloaded = lib._read_manifest_by_run_id(done_session, run_id)
    assert reloaded is not None
    assert reloaded.dispositioned == {
        "reason": "work-verified-landed-live-recovery",
        "date": today,
        "note": escape_note,
    }
    assert reloaded.complete is False  # the recovery closes without finalizing
    # The stamped record suppresses the interrupted-run detection.
    assert lib._detect_interrupted_runs(done_session, root) == []


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-05-done-lifecycle-recovery-gaps.md Task 3:
# resumable-closeout checkpoint writer (checkpoint-manifest).
# --------------------------------------------------------------------------- #
def _seed_checkpoint(
    root: Path,
    run_id: str,
    session: str,
    manifest_sha256: str,
    gates: list[str],
) -> Path:
    """Seed one checkpoint sibling JSON through the lib's own writer so
    refusal arms start from the real record shape."""
    return lib._write_checkpoint_payload(
        root / "docs" / "tmp" / "done-session",
        {
            "schema": lib.CHECKPOINT_SCHEMA_VERSION,
            "kind": lib.CHECKPOINT_KIND,
            "run_id": run_id,
            "manifest_path": f"run-manifest-{run_id}.json",
            "session": session,
            "manifest_sha256": manifest_sha256,
            "gates_green": list(gates),
            "created_epoch": time.time(),
        },
    )


def test_checkpoint_create_refresh_verify_remove_lifecycle(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given an interrupted run manifest, expects
    ``checkpoint-manifest`` to: create the sibling checkpoint JSON naming
    the run_id, the manifest path, the session identity, the manifest's
    sha256, the green-gate list, and a created epoch; refresh the recorded
    sha and gate set in place (same filename) after the manifest's bytes
    change; verify with a matching session and with the session omitted
    (exit 0, verified receipt); refuse the remove while ``complete`` is
    false; and succeed after finalize set ``complete`` true, deleting the
    sibling."""
    root = mktemp_repo("checkpoint-lifecycle")
    now = time.time()
    run_id = "run-checkpoint-lifecycle"
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    _seed_run_manifest(root, run_id, marker_name(now), root_digest(root), now)
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    checkpoint_path = done_session / f"run-checkpoint-{run_id}.json"

    # Create: the sibling JSON records the full contract field set.
    rc = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            run_id,
            "--mode",
            "create",
            "--session",
            "session-alpha",
            "--gates",
            "plan-readiness,doc-registry",
        ]
    )
    assert rc == 0
    assert checkpoint_path.is_file()
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert payload["schema"] == lib.CHECKPOINT_SCHEMA_VERSION
    assert payload["kind"] == lib.CHECKPOINT_KIND
    assert payload["run_id"] == run_id
    assert payload["manifest_path"] == manifest_path.name
    assert payload["session"] == "session-alpha"  # recorded verbatim
    assert (
        payload["manifest_sha256"]
        == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    )
    assert payload["gates_green"] == ["plan-readiness", "doc-registry"]
    assert isinstance(payload["created_epoch"], (int, float))

    # Refresh: after the manifest's bytes change, the recorded sha and gate
    # set update in place (same filename, still one checkpoint sibling).
    _seed_run_manifest(
        root,
        run_id,
        marker_name(now),
        root_digest(root),
        now,
        owned_paths=["README.md"],
    )
    manifest_before_refresh = manifest_path.read_bytes()
    rc2 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            run_id,
            "--mode",
            "refresh",
            "--session",
            "session-alpha",
            "--gates",
            "plan-readiness,doc-registry,sensitive-data-scan",
        ]
    )
    assert rc2 == 0
    assert checkpoint_path.is_file()
    refreshed = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert (
        refreshed["manifest_sha256"]
        == hashlib.sha256(manifest_before_refresh).hexdigest()
    )
    assert refreshed["gates_green"] == [
        "plan-readiness",
        "doc-registry",
        "sensitive-data-scan",
    ]
    assert refreshed["created_epoch"] == payload["created_epoch"]
    assert sorted(p.name for p in done_session.glob("run-checkpoint-*.json")) == [
        checkpoint_path.name
    ]

    # Verify: the mechanical gate reads identity plus the recomputed sha.
    rc3 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            run_id,
            "--mode",
            "verify",
            "--session",
            "session-alpha",
        ]
    )
    assert rc3 == 0
    out3 = capsys.readouterr().out
    assert f"verified: checkpoint-manifest run {run_id}" in out3
    assert "manifest sha256" in out3
    # An omitted session skips the session-identity comparison.
    assert (
        lib.main(["checkpoint-manifest", "--run-id", run_id, "--mode", "verify"])
        == 0
    )
    out4 = capsys.readouterr().out
    assert "session comparison skipped" in out4

    # Remove refuses while complete is false.
    checkpoint_bytes = checkpoint_path.read_bytes()
    rc5 = lib.main(
        ["checkpoint-manifest", "--run-id", run_id, "--mode", "remove"]
    )
    assert rc5 == 1
    err5 = capsys.readouterr().err
    assert "not complete" in err5
    assert f"finalize-manifest --run-id {run_id}" in err5
    assert checkpoint_path.read_bytes() == checkpoint_bytes

    # A successful finalize sets complete true; then the remove deletes
    # the sibling.
    assert lib.main(["finalize-manifest", "--run-id", run_id]) == 0
    capsys.readouterr()
    rc6 = lib.main(
        ["checkpoint-manifest", "--run-id", run_id, "--mode", "remove"]
    )
    assert rc6 == 0
    out6 = capsys.readouterr().out
    assert f"removed: checkpoint-manifest run {run_id}" in out6
    assert not checkpoint_path.exists()


def test_checkpoint_refusals(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Every named refusal arm, each a one-line
    non-zero error that mutates nothing: create on an existing checkpoint
    names refresh; refresh with no checkpoint present names create; create
    and refresh on an absent manifest refuse; verify on an absent manifest
    refuses as unverifiable and remove names finalize as the prerequisite;
    refresh after the manifest is already complete refuses, and create on an
    already-complete manifest refuses symmetrically (the message names
    finalize and remove as the exits); verify after a
    manifest byte change refuses as stale naming the recomputed digest;
    verify with a mismatched session identity or run_id refuses; every
    refusal leaves the checkpoint and the manifest byte-identical."""
    root = mktemp_repo("checkpoint-refusals")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    def checkpoint_bytes(run: str) -> bytes:
        path = done_session / f"run-checkpoint-{run}.json"
        return path.read_bytes() if path.is_file() else b""

    # Arm: create on an existing checkpoint refuses, naming refresh.
    live_id = "run-checkpoint-live"
    done_session.mkdir(parents=True, exist_ok=True)
    _seed_run_manifest(root, live_id, marker_name(now), root_digest(root), now)
    manifest_path = done_session / f"run-manifest-{live_id}.json"
    _seed_checkpoint(
        root, live_id, "session-live",
        hashlib.sha256(manifest_path.read_bytes()).hexdigest(), [],
    )
    manifest_before = manifest_path.read_bytes()
    checkpoint_before = checkpoint_bytes(live_id)
    rc = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            live_id,
            "--mode",
            "create",
            "--session",
            "session-live",
        ]
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "already exists" in err
    assert "--mode refresh" in err
    assert checkpoint_bytes(live_id) == checkpoint_before
    assert manifest_path.read_bytes() == manifest_before

    # Arm: refresh with no checkpoint present refuses, naming create.
    bare_id = "run-checkpoint-bare"
    _seed_run_manifest(root, bare_id, marker_name(now), root_digest(root), now)
    bare_manifest = done_session / f"run-manifest-{bare_id}.json"
    bare_before = bare_manifest.read_bytes()
    rc2 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            bare_id,
            "--mode",
            "refresh",
            "--session",
            "session-bare",
        ]
    )
    assert rc2 == 1
    err2 = capsys.readouterr().err
    assert "no checkpoint present" in err2
    assert "--mode create" in err2
    assert not (done_session / f"run-checkpoint-{bare_id}.json").exists()
    assert bare_manifest.read_bytes() == bare_before

    # Arm: create and refresh on an absent manifest refuse.
    ghost_id = "run-checkpoint-ghost"
    rc3 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            ghost_id,
            "--mode",
            "create",
            "--session",
            "session-ghost",
        ]
    )
    assert rc3 == 1
    assert "no run manifest found" in capsys.readouterr().err
    rc4 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            ghost_id,
            "--mode",
            "refresh",
            "--session",
            "session-ghost",
        ]
    )
    assert rc4 == 1
    assert "no run manifest found" in capsys.readouterr().err
    assert not (done_session / f"run-checkpoint-{ghost_id}.json").exists()

    # Arm: verify on an absent manifest refuses as unverifiable; remove
    # refuses naming finalize as the prerequisite. Both sit beside a live
    # checkpoint so only the manifest is missing (it is deleted below).
    orphan_id = "run-checkpoint-orphan"
    _seed_run_manifest(root, orphan_id, marker_name(now), root_digest(root), now)
    orphan_manifest = done_session / f"run-manifest-{orphan_id}.json"
    _seed_checkpoint(
        root, orphan_id, "session-orphan",
        hashlib.sha256(orphan_manifest.read_bytes()).hexdigest(), [],
    )
    orphan_checkpoint_before = checkpoint_bytes(orphan_id)
    orphan_manifest.unlink()
    rc5 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            orphan_id,
            "--mode",
            "verify",
            "--session",
            "session-orphan",
        ]
    )
    assert rc5 == 1
    assert "unverifiable" in capsys.readouterr().err
    rc6 = lib.main(
        ["checkpoint-manifest", "--run-id", orphan_id, "--mode", "remove"]
    )
    assert rc6 == 1
    err6 = capsys.readouterr().err
    assert f"finalize-manifest --run-id {orphan_id}" in err6
    assert checkpoint_bytes(orphan_id) == orphan_checkpoint_before

    # Arm: refresh after the manifest is already complete refuses.
    complete_id = "run-checkpoint-complete"
    _seed_run_manifest(
        root, complete_id, marker_name(now), root_digest(root), now,
        complete=True,
    )
    complete_manifest = done_session / f"run-manifest-{complete_id}.json"
    complete_before = complete_manifest.read_bytes()
    _seed_checkpoint(
        root, complete_id, "session-complete",
        hashlib.sha256(complete_before).hexdigest(), [],
    )
    complete_checkpoint_before = checkpoint_bytes(complete_id)
    rc7 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            complete_id,
            "--mode",
            "refresh",
            "--session",
            "session-complete",
        ]
    )
    assert rc7 == 1
    assert "already finalized" in capsys.readouterr().err
    assert checkpoint_bytes(complete_id) == complete_checkpoint_before
    assert complete_manifest.read_bytes() == complete_before

    # Arm: create on an already-complete manifest refuses, symmetric with
    # refresh; the message names finalize-manifest and --mode remove as the
    # exits.
    rc7b = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            complete_id,
            "--mode",
            "create",
            "--session",
            "session-complete",
        ]
    )
    assert rc7b == 1
    err7b = capsys.readouterr().err
    assert "already finalized" in err7b
    assert "finalize-manifest" in err7b
    assert f"--mode remove --run-id {complete_id}" in err7b
    assert checkpoint_bytes(complete_id) == complete_checkpoint_before
    assert complete_manifest.read_bytes() == complete_before

    # Arm: verify after any manifest byte change refuses as stale, naming
    # the recomputed digest.
    stale_id = "run-checkpoint-stale"
    _seed_run_manifest(root, stale_id, marker_name(now), root_digest(root), now)
    stale_manifest = done_session / f"run-manifest-{stale_id}.json"
    _seed_checkpoint(
        root, stale_id, "session-stale",
        hashlib.sha256(stale_manifest.read_bytes()).hexdigest(), [],
    )
    stale_checkpoint_before = checkpoint_bytes(stale_id)
    _seed_run_manifest(
        root,
        stale_id,
        marker_name(now),
        root_digest(root),
        now,
        owned_paths=["README.md"],
    )
    stale_manifest_after = stale_manifest.read_bytes()
    recomputed = hashlib.sha256(stale_manifest_after).hexdigest()
    rc8 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            stale_id,
            "--mode",
            "verify",
            "--session",
            "session-stale",
        ]
    )
    assert rc8 == 1
    err8 = capsys.readouterr().err
    assert "stale" in err8
    assert recomputed in err8  # the recomputed digest is named
    assert checkpoint_bytes(stale_id) == stale_checkpoint_before
    assert stale_manifest.read_bytes() == stale_manifest_after

    # Arm: verify with a mismatched session identity refuses.
    rc9 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            stale_id,
            "--mode",
            "verify",
            "--session",
            "session-other",
        ]
    )
    assert rc9 == 1
    err9 = capsys.readouterr().err
    assert "session identity mismatch" in err9
    assert "session-other" in err9
    assert checkpoint_bytes(stale_id) == stale_checkpoint_before

    # Arm: verify with a mismatched run_id refuses. A foreign checkpoint
    # payload under this run's filename (renamed or hand-edited; manual
    # checkpoint editing is unsupported) names the run_id mismatch.
    foreign_id = "run-checkpoint-foreign"
    _seed_run_manifest(
        root, foreign_id, marker_name(now), root_digest(root), now
    )
    foreign_manifest = done_session / f"run-manifest-{foreign_id}.json"
    foreign_before = foreign_manifest.read_bytes()
    _seed_checkpoint(
        root, foreign_id, "session-foreign",
        hashlib.sha256(foreign_before).hexdigest(), [],
    )
    foreign_checkpoint = done_session / f"run-checkpoint-{foreign_id}.json"
    forged = json.loads(foreign_checkpoint.read_text(encoding="utf-8"))
    forged["run_id"] = "run-somebody-else"
    foreign_checkpoint.write_text(
        json.dumps(forged, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    foreign_checkpoint_before = foreign_checkpoint.read_bytes()
    rc10 = lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            foreign_id,
            "--mode",
            "verify",
            "--session",
            "session-foreign",
        ]
    )
    assert rc10 == 1
    err10 = capsys.readouterr().err
    assert "run_id" in err10
    assert "run-somebody-else" in err10
    assert foreign_checkpoint.read_bytes() == foreign_checkpoint_before
    assert foreign_manifest.read_bytes() == foreign_before


def test_failed_finalize_leaves_checkpoint(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Given the refreshed Step 6 sequence (create,
    refresh, finalize that aborts on the identity check, remove), expects
    the finalize to abort non-zero with the manifest byte-identical and
    ``complete`` still false, and the remove to refuse because ``complete``
    stayed false, with the checkpoint sibling still present."""
    root = mktemp_repo("checkpoint-failed-finalize")
    now = time.time()
    run_id = "run-checkpoint-aborted"
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    # A recorded root matching neither matcher arm makes the finalize's
    # identity pre-parse abort (the frozen two-way identity contract).
    foreign_root = str(tmp_path / "another-checkout")
    _seed_run_manifest(
        root, run_id, marker_name(now), foreign_root, now
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    manifest_path = done_session / f"run-manifest-{run_id}.json"
    checkpoint_path = done_session / f"run-checkpoint-{run_id}.json"

    assert lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            run_id,
            "--mode",
            "create",
            "--session",
            "session-aborted",
            "--gates",
            "plan-readiness",
        ]
    ) == 0
    assert lib.main(
        [
            "checkpoint-manifest",
            "--run-id",
            run_id,
            "--mode",
            "refresh",
            "--session",
            "session-aborted",
            "--gates",
            "plan-readiness,doc-registry",
        ]
    ) == 0
    manifest_before = manifest_path.read_bytes()
    checkpoint_before = checkpoint_path.read_bytes()

    finalize_rc = lib.main(["finalize-manifest", "--run-id", run_id])
    assert finalize_rc == 1
    assert "identity mismatch" in capsys.readouterr().err
    assert manifest_path.read_bytes() == manifest_before
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["complete"] is False

    rc = lib.main(
        ["checkpoint-manifest", "--run-id", run_id, "--mode", "remove"]
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "not complete" in err
    assert checkpoint_path.is_file()
    assert checkpoint_path.read_bytes() == checkpoint_before


def test_list_interrupted_manifests_columns_and_non_mutation(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan Task 2: a dead-root fixture prints its
    ``root_matches_current_repo=no`` line with ``dispositioned=no`` flipping
    to ``yes`` after a stamp; the ``adopted`` column reports the record's own
    ``adopted_from`` link while a complete record never lists; the identity
    value ``live`` never renders (the old ``root=`` prefix is gone from the
    output entirely); one guidance line names a matching root a repository
    identity fact and the lock status command the liveness check, and no
    guidance line prints when no record matches; a clean fixture prints the
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
    # A root-matching record that itself adopted an older boundary:
    # root_matches_current_repo=yes, adopted=yes (its own adopted_from
    # link), still an interrupted run.
    _seed_run_manifest(
        root,
        "run-adopter-match",
        marker_name(now),
        root_digest(root),
        now,
        adopted_from="run-older-parent",
    )
    # A finalized record never lists.
    _seed_run_manifest(
        root,
        "run-match-complete",
        marker_name(now),
        root_digest(root),
        now,
        complete=True,
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    done_session = root / "docs" / "tmp" / "done-session"
    before = {p.name: p.read_bytes() for p in done_session.glob("run-manifest-*.json")}

    assert lib.main(["list-interrupted-manifests"]) == 0
    out = capsys.readouterr().out
    assert (
        f"{dead_id} root_matches_current_repo=no lock=unknown "
        f"dispositioned=no adopted=no created={created_iso}" in out
    )
    assert (
        f"run-adopter-match root_matches_current_repo=yes lock=free "
        f"dispositioned=no adopted=yes created={created_iso}" in out
    )
    assert "run-match-complete" not in out
    # The identity value ``live`` is never rendered for a root match: the
    # retired ``root=<live|dead>`` prefix is gone from the rendering.
    assert "root=live" not in out
    assert "root=dead" not in out
    # One guidance line, present because at least one listed record matches
    # this checkout's root; it names the lock status command as the liveness
    # check.
    assert out.count("repository identity fact") == 1
    assert "done-lock.sh status" in out
    # Non-mutation: the listing is read-only over the manifest set.
    after = {p.name: p.read_bytes() for p in done_session.glob("run-manifest-*.json")}
    assert after == before

    # A stamp flips the dispositioned column on the dead-root line.
    assert lib.main(["disposition-manifest", "--run-id", dead_id]) == 0
    capsys.readouterr()
    assert lib.main(["list-interrupted-manifests"]) == 0
    out2 = capsys.readouterr().out
    assert (
        f"{dead_id} root_matches_current_repo=no lock=unknown "
        f"dispositioned=yes adopted=no created={created_iso}" in out2
    )

    # A listing whose records match no checkout's root prints no guidance
    # line (the guidance keys on a root match, never on the listing itself).
    foreign_root = mktemp_repo("listing-foreign-only")
    _seed_run_manifest(
        foreign_root,
        "run-foreign-only",
        marker_name(now),
        str(tmp_path / "another-deleted-wt"),
        now,
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(foreign_root))
    assert lib.main(["list-interrupted-manifests"]) == 0
    out3 = capsys.readouterr().out
    assert "run-foreign-only root_matches_current_repo=no" in out3
    assert "repository identity fact" not in out3


def test_list_interrupted_manifests_lock_column_semantics(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan Task 2 lock-column witnesses, read-only
    over the checkout-keyed done-lock directory honored through
    ``DONE_LOCK_ROOT``: a fingerprint root maps to its lock directory under
    the lock root (held with live holder metadata, free when the directory
    is absent); a meta-less leftover directory past the crash-leftover rule
    reports free under the column's own incomplete-age arm (the lock
    script's raw held line for the same directory is the documented
    divergence, never an agreement claim); a meta-less directory younger
    than the incomplete age reports held; a present-meta hold whose
    recorded holder is verified dead reports free; and removing the
    ``DONE_LOCK_ROOT`` override hides the fixture directories, so the same
    fingerprint records fall back to the default lock root."""
    root = mktemp_repo("lock-arms")
    now = time.time()
    match_fp = root_digest(root)
    held_id = "run-lock-holder-alive"
    _seed_run_manifest(root, held_id, marker_name(now), match_fp, now)
    leftover_id = "run-lock-metaless-leftover"
    _seed_run_manifest(root, leftover_id, marker_name(now), "b" * 64, now)
    young_id = "run-lock-metaless-young"
    _seed_run_manifest(root, young_id, marker_name(now), "c" * 64, now)
    dead_holder_id = "run-lock-holder-dead"
    _seed_run_manifest(root, dead_holder_id, marker_name(now), "d" * 64, now)
    absent_id = "run-lock-dir-absent"
    _seed_run_manifest(root, absent_id, marker_name(now), "e" * 64, now)

    lock_root = tmp_path / "fixture-locks"
    monkeypatch.setenv("DONE_LOCK_ROOT", str(lock_root))

    def write_meta(lock_dir: Path, holder_pid: int) -> None:
        lock_dir.mkdir(parents=True)
        (lock_dir / "meta.env").write_text(
            f"lock_token=fixture-token\n"
            f"repo_root={root}\n"
            f"label=fixture\n"
            f"started_epoch={int(now)}\n"
            f"started_at=fixture\n"
            f"hostname=fixture\n"
            f"holder_pid={holder_pid}\n"
            f"holder_identity=fixture holder identity\n"
            f"holder_pinned=0\n",
            encoding="utf-8",
        )

    # Live holder metadata (this test process is alive): held.
    write_meta(lock_root / match_fp[:16], os.getpid())
    # Meta-less leftover past the crash-leftover rule (aged mtime): free.
    leftover_dir = lock_root / ("b" * 16)
    leftover_dir.mkdir(parents=True)
    aged = now - 3600
    os.utime(leftover_dir, (aged, aged))
    # Meta-less directory younger than the incomplete age: held.
    (lock_root / ("c" * 16)).mkdir(parents=True)
    # Present-meta hold whose recorded holder is verified dead: free.
    victim = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    victim.kill()
    victim.wait()
    write_meta(lock_root / ("d" * 16), victim.pid)

    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    assert lib.main(["list-interrupted-manifests"]) == 0
    out = capsys.readouterr().out
    assert f"{held_id} root_matches_current_repo=yes lock=held" in out
    assert f"{absent_id} root_matches_current_repo=no lock=free" in out
    assert f"{leftover_id} root_matches_current_repo=no lock=free" in out
    assert f"{young_id} root_matches_current_repo=no lock=held" in out
    assert f"{dead_holder_id} root_matches_current_repo=no lock=free" in out

    # The override is honored: without DONE_LOCK_ROOT the fixture lock root
    # is invisible, so every fingerprint record falls back to the default
    # lock root and no held value survives.
    monkeypatch.delenv("DONE_LOCK_ROOT")
    assert lib.main(["list-interrupted-manifests"]) == 0
    out2 = capsys.readouterr().out
    assert "lock=held" not in out2
    assert f"{held_id} root_matches_current_repo=yes lock=free" in out2


def test_list_interrupted_manifests_unreadable_lock_root_is_unknown(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan Task 2: an unreadable done-lock root
    lands the lock column on ``unknown`` (never free, never held), while the
    identity column still renders from the manifest record."""
    root = mktemp_repo("lock-unreadable")
    now = time.time()
    rec_id = "run-lock-sealed-root"
    _seed_run_manifest(root, rec_id, marker_name(now), "f" * 64, now)
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    lock_root = tmp_path / "sealed-locks"
    lock_root.mkdir()
    monkeypatch.setenv("DONE_LOCK_ROOT", str(lock_root))

    real_stat = os.stat

    def sealed_stat(path, *args, **kwargs):
        if os.fspath(path).startswith(str(lock_root)):
            raise PermissionError(13, "sealed fixture lock root", os.fspath(path))
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(lib.os, "stat", sealed_stat)
    assert lib.main(["list-interrupted-manifests"]) == 0
    out = capsys.readouterr().out
    assert f"{rec_id} root_matches_current_repo=no lock=unknown" in out


def test_list_interrupted_manifests_usage_and_docstring_describe_columns():
    """[class: REPOSITORY_TEST] Plan Task 2: the command usage text and the
    command docstring describe the identity column, the lock column, and the
    guidance line, and neither documents the retired liveness rendering."""
    usage = lib._usage()
    assert "root_matches_current_repo=yes|no" in usage
    assert "lock=held|free|unknown" in usage
    assert "done-lock.sh status" in usage
    assert "identity fact" in usage
    assert "root=<live|dead>" not in usage
    doc = lib._cmd_list_interrupted_manifests.__doc__ or ""
    assert "root_matches_current_repo" in doc
    assert "held|free|unknown" in doc
    assert "done-lock.sh status" in doc
    assert "identity fact" in doc
    assert "incomplete-age" in doc
    assert "root=<live|dead>" not in doc


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


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-12-done-interrupted-manifest-state-
# classification.md Task 1: the canonical run-boundary classifier
# (classify_run_boundary), derived only through the existing RunManifest parse
# and the directory's adopted set (the _detect_interrupted_runs semantics).
# --------------------------------------------------------------------------- #
def _write_shadow_copy(
    done_session: Path, manifest_path: Path, suffix: str, mutate=None
) -> Path:
    """Copy one manifest record to a non-canonical, glob-matching name whose
    payload keeps the run id (the worktree-copy shape the plan's Terms
    describe); the suffix lands before the ``.json`` extension so the copy
    can be made to sort after the canonical name, and ``mutate`` may adjust
    the copied payload."""
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(payload)
    shadow = done_session / (manifest_path.name[: -len(".json")] + suffix + ".json")
    shadow.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return shadow


def test_classify_run_boundary_names_each_terminal_state(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given the newest record for each canonical
    shape, expects the verdict to name finalized, adopted, and dispositioned
    (a dead-root disposition included, root matching playing no role),
    derived only through the RunManifest parse and the directory-wide adopted
    set; an unresolved record (complete false, unadopted, undispositioned) is
    the orphan verdict, and an unparseable or schema-invalid record is the
    unreadable verdict with no run id."""
    root = mktemp_repo("classify-arms")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    # finalized: the given canonical record itself carries complete true
    finalized = _seed_run_manifest(
        root, "run-fin", marker_name(now), root_digest(root), now, complete=True
    )
    assert lib.classify_run_boundary(done_session, finalized) == (
        "finalized",
        "run-fin",
    )
    # adopted: complete false, but another record's adopted_from names the
    # run id (the directory's adopted set)
    adopted = _seed_run_manifest(
        root, "run-adopted", marker_name(now), root_digest(root), now
    )
    _seed_run_manifest(
        root,
        "run-adopter",
        marker_name(now),
        root_digest(root),
        now,
        adopted_from="run-adopted",
    )
    assert lib.classify_run_boundary(done_session, adopted) == (
        "adopted",
        "run-adopted",
    )
    # dispositioned: the disposition record is the second suppression shape
    dispositioned = _seed_run_manifest(
        root,
        "run-disp",
        marker_name(now),
        root_digest(root),
        now,
        dispositioned={
            "reason": "work-verified-landed",
            "date": "2026-10-13",
            "note": "closed",
        },
    )
    assert lib.classify_run_boundary(done_session, dispositioned) == (
        "dispositioned",
        "run-disp",
    )
    # a dead-root disposition classifies the same way: the verdict is read
    # from the record states, never from root matching
    dead = _seed_run_manifest(
        root,
        "run-dead-disp",
        marker_name(now),
        str(tmp_path / "deleted-wt"),
        now,
        dispositioned={
            "reason": "work-verified-landed",
            "date": "2026-10-13",
            "note": "dead root",
        },
    )
    assert lib.classify_run_boundary(done_session, dead) == (
        "dispositioned",
        "run-dead-disp",
    )
    # orphan: complete false, unadopted, undispositioned
    orphan = _seed_run_manifest(
        root, "run-orphan", marker_name(now), root_digest(root), now
    )
    assert lib.classify_run_boundary(done_session, orphan) == (
        "orphan",
        "run-orphan",
    )
    # unreadable: unparseable JSON, and a parseable payload failing the
    # schema validation, both degrade to the fail-closed verdict
    corrupt = done_session / "run-manifest-run-corrupt.json"
    corrupt.write_text("{ not json\n", encoding="utf-8")
    assert lib.classify_run_boundary(done_session, corrupt) == (
        "unreadable",
        None,
    )
    schema_bad = done_session / "run-manifest-run-schemabad.json"
    schema_bad.write_text(
        json.dumps({"schema": 99, "run_id": "run-schemabad"}) + "\n",
        encoding="utf-8",
    )
    assert lib.classify_run_boundary(done_session, schema_bad) == (
        "unreadable",
        None,
    )


def test_classify_run_boundary_groups_over_run_identity(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a session directory holding several
    records of one run, expects the verdict grouped over every
    run-manifest-*.json record sharing the given file's payload run id, so a
    terminal record on any of the run's files closes the boundary whichever
    file sorts newest: the canonical twin carrying the terminal record names
    shadow-closed through a newest unresolved copy, and a disposition living
    only on the copy closes the run whose canonical record sorts before it
    and stays unresolved; grouping never leaks across runs."""
    root = mktemp_repo("classify-group")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    # canonical twin finalized, unresolved copy sorts newest (the copy's
    # suffix keeps it non-canonical and lexicographically after the
    # canonical name)
    canon = _seed_run_manifest(
        root, "run-grp-fin", marker_name(now), root_digest(root), now, complete=True
    )
    shadow = _write_shadow_copy(done_session, canon, ".worktree")
    assert shadow.name > canon.name  # the copy is the newest file
    assert lib.classify_run_boundary(done_session, shadow) == (
        "shadow-closed",
        "run-grp-fin",
    )
    # whichever file sorts newest: passing the canonical file names the state
    assert lib.classify_run_boundary(done_session, canon) == (
        "finalized",
        "run-grp-fin",
    )
    # mirrored flow: the disposition lives only on the copy; the canonical
    # record sorts before it and stays unresolved; run identity still closes
    dcanon = _seed_run_manifest(
        root, "run-grp-disp", marker_name(now), root_digest(root), now - 60
    )
    dcopy = _write_shadow_copy(
        done_session,
        dcanon,
        ".worktree",
        mutate=lambda p: p.update(
            dispositioned={
                "reason": "work-verified-landed",
                "date": "2026-10-13",
                "note": "copy closed",
            }
        ),
    )
    assert dcopy.name > dcanon.name
    assert lib.classify_run_boundary(done_session, dcopy) == (
        "shadow-closed",
        "run-grp-disp",
    )
    assert lib.classify_run_boundary(done_session, dcanon) == (
        "dispositioned",
        "run-grp-disp",
    )
    # grouping never leaks across runs: an unrelated orphan stays unresolved
    other = _seed_run_manifest(
        root, "run-other-orphan", marker_name(now), root_digest(root), now - 120
    )
    assert lib.classify_run_boundary(done_session, other) == (
        "orphan",
        "run-other-orphan",
    )


def test_classify_run_boundary_cli_prints_verdict_and_run_id(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] The read-only CLI subcommand behind the shell
    classifier prints the ``verdict:`` and ``run_id:`` lines for the named
    manifest file and exits 0; a missing manifest file is the outcome
    contract's tool error."""
    root = mktemp_repo("classify-cli")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    manifest = _seed_run_manifest(
        root, "run-cli", marker_name(now), root_digest(root), now, complete=True
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    rc = lib.main(
        [
            "classify-run-boundary",
            "--session-dir",
            str(done_session),
            "--manifest",
            str(manifest),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "verdict: finalized\n" in out
    assert "run_id: run-cli\n" in out
    missing = lib.main(
        [
            "classify-run-boundary",
            "--session-dir",
            str(done_session),
            "--manifest",
            str(done_session / "run-manifest-absent.json"),
        ]
    )
    assert missing == 3
    captured = capsys.readouterr()
    assert "OUTCOME: tool_error" in captured.out + captured.err


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-12-done-interrupted-manifest-state-
# classification.md Task 3: shadow copies bind to their run and close through
# their own evidence (disposition-manifest --manifest-file, and the
# interrupted-run reports rendering copies as shadow-of, never boundaries).
# --------------------------------------------------------------------------- #
def test_disposition_manifest_file_closes_copy_through_own_evidence(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan Task 3: given a worktree-suffixed copy
    whose payload run id matches --run-id, ``--manifest-file`` verifies the
    deliverables witness against THAT copy's owned paths (a missing
    deliverable on the copy refuses even though the canonical record owns
    nothing) and stamps the dispositioned record on that copy only, through
    the shared compare-and-swap stamp re-reading that file, leaving the
    canonical record byte-identical."""
    root = mktemp_repo("disposition-copy")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"
    run_id = "run-shadow-disposition"
    canonical = _seed_run_manifest(
        root, run_id, marker_name(now), str(tmp_path / "deleted-wt"), now
    )
    # The copy owns a deliverable the canonical record does not: the witness
    # must run against the copy's own payload, so this attempt refuses naming
    # the copy's missing review and mutates nothing.
    missing_review = ".ai-playbook/reviews/2026-10-12-never-landed-r1.md"
    copy = _write_shadow_copy(
        done_session,
        canonical,
        ".worktree",
        mutate=lambda p: p.update({"owned_review_paths": [missing_review]}),
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    before_canonical = canonical.read_bytes()
    before_copy = copy.read_bytes()

    rc = lib.main(
        [
            "disposition-manifest",
            "--run-id",
            run_id,
            "--manifest-file",
            copy.name,
        ]
    )

    assert rc == 1
    err = capsys.readouterr().err
    assert "deliverables witness failed" in err
    assert missing_review in err
    assert canonical.read_bytes() == before_canonical
    assert copy.read_bytes() == before_copy

    # A copy whose own evidence resolves (an owned path committed at HEAD):
    # the stamp lands on that copy only.
    copy2 = _write_shadow_copy(
        done_session,
        canonical,
        ".worktree2",
        mutate=lambda p: p.update({"owned_paths": ["README.md"]}),
    )
    rc2 = lib.main(
        [
            "disposition-manifest",
            "--run-id",
            run_id,
            "--manifest-file",
            copy2.name,
            "--note",
            "copy closure",
        ]
    )
    assert rc2 == 0
    today = datetime.now(timezone.utc).date().isoformat()
    out = capsys.readouterr().out
    assert f"dispositioned: {run_id} ({today})" in out
    assert f"written to" in out and copy2.name in out
    copy2_payload = json.loads(copy2.read_text(encoding="utf-8"))
    assert copy2_payload["dispositioned"] == {
        "reason": "work-verified-landed",
        "date": today,
        "note": "copy closure",
    }
    assert copy2_payload["complete"] is False
    # The canonical record stays byte-identical and unstamped.
    assert canonical.read_bytes() == before_canonical
    assert (
        json.loads(canonical.read_text(encoding="utf-8"))["dispositioned"]
        is None
    )


def test_disposition_manifest_file_refusal_arms(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan Task 3 safety: a ``--manifest-file``
    whose payload run id differs from ``--run-id`` refuses named with no
    mutation (a copy can never be closed through a mismatched canonical
    record); the copy arm applies the canonical refusals - a complete copy, a
    copy adopted by another manifest, a live-rooted copy, a non-bare or
    traversing name, and a name outside the ``run-manifest-*.json`` glob -
    and an already-stamped copy is the idempotent reprint arm."""
    root = mktemp_repo("disposition-copy-refusals")
    now = time.time()
    done_session = root / "docs" / "tmp" / "done-session"

    # Arm: mismatched payload run id refuses named, no mutation.
    canonical = _seed_run_manifest(
        root, "run-mismatch", marker_name(now), str(tmp_path / "deleted-wt"), now
    )
    foreign_copy = _write_shadow_copy(
        done_session,
        canonical,
        ".worktree",
        mutate=lambda p: p.update({"run_id": "run-other"}),
    )
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    before_canonical = canonical.read_bytes()
    before_foreign = foreign_copy.read_bytes()
    assert (
        lib.main(
            [
                "disposition-manifest",
                "--run-id",
                "run-mismatch",
                "--manifest-file",
                foreign_copy.name,
            ]
        )
        == 1
    )
    err = capsys.readouterr().err
    assert "differs from --run-id" in err
    assert "run-other" in err
    assert canonical.read_bytes() == before_canonical
    assert foreign_copy.read_bytes() == before_foreign

    # Arm: non-bare, traversing, and non-glob names refuse with no mutation.
    for bad_name in (
        "../run-mismatch.json",
        "a/b.json",
        "run-manifest-notes.txt",
        "notes.json",
    ):
        rc = lib.main(
            [
                "disposition-manifest",
                "--run-id",
                "run-mismatch",
                "--manifest-file",
                bad_name,
            ]
        )
        assert rc == 1, bad_name
        err = capsys.readouterr().err
        assert "refusing" in err, bad_name
        if bad_name.endswith(".txt") or bad_name == "notes.json":
            assert "run-manifest-*.json" in err, bad_name
        else:
            assert "bare" in err, bad_name
    assert canonical.read_bytes() == before_canonical

    # Arm: a complete copy refuses (a finalized run is never interrupted).
    complete_id = "run-copy-complete"
    complete = _seed_run_manifest(
        root,
        complete_id,
        marker_name(now),
        str(tmp_path / "deleted-wt-2"),
        now,
        complete=True,
    )
    complete_copy = _write_shadow_copy(done_session, complete, ".worktree")
    before = complete_copy.read_bytes()
    assert (
        lib.main(
            [
                "disposition-manifest",
                "--run-id",
                complete_id,
                "--manifest-file",
                complete_copy.name,
            ]
        )
        == 1
    )
    assert "already finalized" in capsys.readouterr().err
    assert complete_copy.read_bytes() == before

    # Arm: a copy of an adopted boundary refuses (an adopter names the run).
    victim_id = "run-copy-adopted"
    victim = _seed_run_manifest(
        root, victim_id, marker_name(now), str(tmp_path / "deleted-wt-3"), now
    )
    victim_copy = _write_shadow_copy(done_session, victim, ".worktree")
    _seed_run_manifest(
        root,
        "run-copy-adopter",
        marker_name(now),
        str(root.resolve()),
        now,
        adopted_from=victim_id,
    )
    before = victim_copy.read_bytes()
    assert (
        lib.main(
            [
                "disposition-manifest",
                "--run-id",
                victim_id,
                "--manifest-file",
                victim_copy.name,
            ]
        )
        == 1
    )
    assert "adopts this boundary" in capsys.readouterr().err
    assert victim_copy.read_bytes() == before

    # Arm: a live-rooted copy refuses naming the resume path (--adopt).
    live_id = "run-copy-live"
    live = _seed_run_manifest(root, live_id, marker_name(now), str(root), now)
    live_copy = _write_shadow_copy(done_session, live, ".worktree")
    before = live_copy.read_bytes()
    assert (
        lib.main(
            [
                "disposition-manifest",
                "--run-id",
                live_id,
                "--manifest-file",
                live_copy.name,
            ]
        )
        == 1
    )
    err = capsys.readouterr().err
    assert "live root" in err
    assert "--adopt" in err
    assert live_copy.read_bytes() == before

    # Arm: an already-stamped copy is the idempotent reprint arm (exit 0).
    stamped_id = "run-copy-stamped"
    stamp = {
        "reason": "work-verified-landed",
        "date": "2026-09-29",
        "note": "earlier closure",
    }
    stamped = _seed_run_manifest(
        root,
        stamped_id,
        marker_name(now),
        str(tmp_path / "deleted-wt-4"),
        now,
        dispositioned=stamp,
    )
    stamped_copy = _write_shadow_copy(done_session, stamped, ".worktree")
    before = stamped_copy.read_bytes()
    assert (
        lib.main(
            [
                "disposition-manifest",
                "--run-id",
                stamped_id,
                "--manifest-file",
                stamped_copy.name,
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert f"dispositioned: {stamped_id} (2026-09-29)" in out
    assert "already dispositioned" in out
    assert stamped_copy.read_bytes() == before


def test_reports_bind_shadow_copies_never_independent_boundaries(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan Task 3: given a shadow copy sharing a
    canonical record's run id, the write-manifest interrupted-run report AND
    ``list-interrupted-manifests`` render that file as a ``shadow-of
    <run_id>`` line naming the filename, never as an independent boundary:
    the canonical boundary line and the undisposed-interrupted warning entry
    render once for the run, not once per file."""
    root = mktemp_repo("shadow-binding")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    run_id = "run-shadow-boundary"
    canonical = _seed_run_manifest(
        root,
        run_id,
        marker_name(now - 3600),
        str(tmp_path / "deleted-wt"),
        now - 10,
    )
    copy = _write_shadow_copy(
        root / "docs" / "tmp" / "done-session", canonical, ".worktree"
    )
    make_marker(root, now, os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest", "--claim-none"])
    assert rc == 0
    captured = capsys.readouterr()
    out = captured.out
    assert f"interrupted run: shadow-of {run_id} {copy.name}" in out
    # The canonical boundary line renders once for the run, never per file.
    assert out.count(f"interrupted run: {canonical.name}") == 1
    assert out.count(f"disposition-manifest --run-id {run_id}") == 1
    # The undisposed-interrupted warning carries one entry for the run.
    assert captured.err.count(f"disposition-manifest --run-id {run_id}") == 1

    assert lib.main(["list-interrupted-manifests"]) == 0
    out2 = capsys.readouterr().out
    assert f"shadow-of {run_id} {copy.name}" in out2
    # The copy never renders as its own boundary column line.
    assert out2.count(f"{run_id} root_matches_current_repo=") == 1


def test_reports_render_copy_closed_run_as_history(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan Task 3: given a copy closed through
    ``--manifest-file``, the reports render the run's remaining records as
    the closed run's history with no open-boundary line, matching the Terms'
    run-identity closure: the interrupted-run detection returns no record of
    the closed run, the write-manifest report carries no interrupted-run line
    and no undisposed-interrupted warning for it, and
    ``list-interrupted-manifests`` renders the stamped copy as ``shadow-of``
    and the canonical record as a closed-run history line naming the closing
    file."""
    root = mktemp_repo("shadow-closed-run")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    run_id = "run-copy-closed"
    canonical = _seed_run_manifest(
        root,
        run_id,
        marker_name(now - 3600),
        str(tmp_path / "deleted-wt"),
        now - 10,
        owned_paths=["README.md"],
    )
    done_session = root / "docs" / "tmp" / "done-session"
    copy = _write_shadow_copy(done_session, canonical, ".worktree")
    make_marker(root, now, os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    assert (
        lib.main(
            [
                "disposition-manifest",
                "--run-id",
                run_id,
                "--manifest-file",
                copy.name,
            ]
        )
        == 0
    )
    capsys.readouterr()
    # Run-identity closure: the detection returns no record of the closed run.
    orphans = lib._detect_interrupted_runs(done_session, root)
    assert all(o.run_id != run_id for o in orphans)

    rc = lib.main(["write-manifest", "--claim-none"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "interrupted run" not in captured.out
    assert "undisposed-interrupted" not in captured.err
    assert run_id not in captured.err

    assert lib.main(["list-interrupted-manifests"]) == 0
    out = capsys.readouterr().out
    assert f"shadow-of {run_id} {copy.name}" in out
    closed_lines = [
        line for line in out.splitlines() if line.startswith(f"closed-run {run_id} ")
    ]
    assert len(closed_lines) == 1
    assert canonical.name in closed_lines[0]
    assert copy.name in closed_lines[0]
    assert "dispositioned" in closed_lines[0]
    # Never an open-boundary line for the closed run.
    assert f"{run_id} root_matches_current_repo=" not in out


def test_disposition_manifest_usage_and_docstring_describe_manifest_file():
    """[class: REPOSITORY_TEST] Plan Task 3: the disposition-manifest usage
    text and the command docstring describe ``--manifest-file``, its
    payload-run-id match requirement, and the copy arm's refusals."""
    usage = lib._usage()
    assert "--manifest-file" in usage
    assert "run-manifest-*.json" in usage
    assert "payload run_id" in usage
    doc = lib._cmd_disposition_manifest.__doc__ or ""
    assert "--manifest-file" in doc
    assert "run-manifest-*.json" in doc
    assert "byte-identical" in doc
    assert "idempotent" in doc


def test_write_manifest_dead_root_orphan_names_disposition_path(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] The write-manifest orphan-report loop's
    dead-root line names the disposition path (the done skill's Manifest
    disposition (dead-boundary close) paragraph) instead of the adoption
    advice, since adoption refuses a dead root; the dead-root orphan itself
    still surfaces through the widened detection, and the undisposed-
    interrupted warning that follows the report names the disposition exit
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

    assert rc == 0
    captured = capsys.readouterr()
    assert "interrupted run" in captured.out
    assert dead_id in captured.out
    assert "disposition-manifest" in captured.out
    assert "write-manifest: undisposed-interrupted (reported, not failing):" in captured.err
    assert f"disposition-manifest --run-id {dead_id}" in captured.err
    assert "--adopt" not in captured.out + captured.err  # disposition only
    # The write continues past the warning: the orphan plus the new manifest.
    assert len(list((root / "docs" / "tmp" / "done-session").glob(
        "run-manifest-*.json"))) == 2


def test_write_manifest_warns_on_undisposed_interrupted_boundary(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] A complete:false manifest in the window draws
    the named ``write-manifest: undisposed-interrupted (reported, not
    failing):`` warning listing the manifest filename with the live-root
    remedies (``recover-manifest --run-id`` to verify and close it,
    ``--adopt <run_id>`` to continue it, ``finalize-manifest --run-id`` to
    close it) while the interrupted-run report lines are kept and the new
    manifest IS written past the warning (demotion program change 3); with
    ``--adopt`` the write carries the adopted boundary; on a dead-root
    fixture the warning names the disposition exit only (adoption refuses a
    dead root), and after ``disposition-manifest`` the write succeeds."""
    # Live-root arm: the warning, then the adopt exit.
    root = mktemp_repo("undisposed-live")
    prev = make_marker(root, time.time() - 3600, os.getpid())
    orphan_id = "run-undisposed-live"
    _seed_run_manifest(root, orphan_id, prev.name, str(root), time.time() - 10)
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    rc = lib.main(["write-manifest"])

    assert rc == 0
    captured = capsys.readouterr()
    assert "write-manifest: undisposed-interrupted (reported, not failing):" in captured.err
    assert f"run-manifest-{orphan_id}.json" in captured.err
    assert f"--adopt {orphan_id}" in captured.err
    assert f"finalize-manifest --run-id {orphan_id}" in captured.err
    assert "disposition-manifest refuses live roots" in captured.err
    assert "interrupted run" in captured.out  # the report lines are kept
    assert orphan_id in captured.out
    done_session = root / "docs" / "tmp" / "done-session"
    assert len(list(done_session.glob("run-manifest-*.json"))) == 2
    # the write continues past the warning: the orphan plus the new manifest

    rc2 = lib.main(["write-manifest", "--adopt", orphan_id])
    assert rc2 == 0, capsys.readouterr().err
    payload = _newest_manifest_payload(root, exclude_run_id=orphan_id)
    assert payload["adopted_from"] == orphan_id
    # Flush the adopt run's capture: post-demotion the live arm's own write
    # is itself an incomplete manifest, so the adopt run correctly warns
    # about it (a live-root remedy line carrying --adopt); that warning
    # belongs to root's window and must not leak into the dead-root arm.
    capsys.readouterr()

    # Dead-root arm: the warning names the disposition exit only; after
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

    assert rc3 == 0
    captured3 = capsys.readouterr()
    assert "write-manifest: undisposed-interrupted (reported, not failing):" in captured3.err
    assert f"run-manifest-{dead_id}.json" in captured3.err
    assert f"disposition-manifest --run-id {dead_id}" in captured3.err
    assert "--adopt" not in captured3.err  # dead root: disposition only
    # The write continues past the warning here too.
    root2_session = root2 / "docs" / "tmp" / "done-session"
    assert len(list(root2_session.glob("run-manifest-*.json"))) == 2

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
        'reviews_dir = ".ai-playbook/reviews/"\n'
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
        'reviews_dir = ".ai-playbook/reviews/"\n'
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
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    owned_rel = ".ai-playbook/reviews/2026-09-28-owned-review-r1.md"
    unowned = [
        ".ai-playbook/reviews/2026-09-28-peer-review-b-r1.md",
        ".ai-playbook/reviews/2026-09-28-peer-review-a-r1.md",
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


def test_emit_foreign_candidates_fresh_directory_no_marker(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan 2026-10-16-done-emit-prelock-
    classification: in a fresh done-session directory holding zero
    confirmable run-start markers, the emit-only invocation still completes
    (rc 0), writes the sorted one-per-line file, names the repo root the
    enumeration ran against in its summary, and creates no done-session
    state (no marker, no manifest)."""
    root = mktemp_repo("emit-fresh-dir")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    unowned = [
        ".ai-playbook/reviews/2026-09-28-peer-review-b-r1.md",
        ".ai-playbook/reviews/2026-09-28-peer-review-a-r1.md",
    ]
    for rel in unowned:
        (root / rel).write_text("staging review body\n", encoding="utf-8")
    done_session = root / "docs" / "tmp" / "done-session"
    out = tmp_path / "candidates.txt"

    assert lib.main(
        ["write-manifest", "--emit-foreign-candidates", str(out)]
    ) == 0

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines == sorted(unowned)
    captured = capsys.readouterr().out
    assert "foreign-candidates:" in captured
    assert f"repo root {os.path.realpath(root)}" in captured
    # The zero-marker emit creates and mutates no done-session state.
    assert done_session.exists() is False or (
        list(done_session.glob("*")) == []
    )


def test_zero_marker_writer_refusal_unchanged(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan 2026-10-16-done-emit-prelock-
    classification: a manifest-writing invocation in the same fresh
    zero-marker shape keeps the no-marker refusal byte-identical and writes
    no manifest - only the read-only emit shape relaxes."""
    root = mktemp_repo("zero-marker-writer")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    rel = ".ai-playbook/reviews/2026-09-28-peer-review-a-r1.md"
    (root / rel).write_text("staging review body\n", encoding="utf-8")
    done_session = root / "docs" / "tmp" / "done-session"
    out = tmp_path / "candidates.txt"

    rc = lib.main(["write-manifest", "--owned-review", rel])
    assert rc != 0
    err = capsys.readouterr().err
    assert (
        "write-manifest: no content-confirmed run-start marker under "
        f"{os.path.realpath(done_session)}; write the marker before the manifest" in err
    )
    assert list(done_session.glob("run-manifest-*.json")) == []

    # The emit arm on the identical state still completes.
    assert lib.main(
        ["write-manifest", "--emit-foreign-candidates", str(out)]
    ) == 0
    assert out.read_text(encoding="utf-8").splitlines() == [rel]


def test_emit_matches_gate_candidate_set_on_zero_marker_corpus(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Plan 2026-10-16-done-emit-prelock-
    classification: emit-versus-gate exact-set parity over one corpus - the
    zero-marker emit's candidate set equals the set the claim-or-foreign
    gate (marker present, no ownership flags) names as uncovered."""
    root = mktemp_repo("emit-gate-parity")
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    candidates = [
        ".ai-playbook/reviews/2026-09-28-peer-review-b-r1.md",
        ".ai-playbook/reviews/2026-09-28-peer-review-a-r1.md",
        ".ai-playbook/reviews/2026-09-28-peer-review-c-r1.md",
    ]
    for rel in candidates:
        (root / rel).write_text("staging review body\n", encoding="utf-8")
    out = tmp_path / "candidates.txt"

    assert lib.main(
        ["write-manifest", "--emit-foreign-candidates", str(out)]
    ) == 0
    emitted = set(out.read_text(encoding="utf-8").splitlines())

    # Same corpus, marker present, writer arm with no ownership flags: the
    # claim-or-foreign gate refuses naming the uncovered set.
    make_marker(root, time.time(), os.getpid())
    rc = lib.main(["write-manifest"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "claim-or-foreign violation" in err
    # The refusal names every uncovered candidate on one comma-joined line;
    # recover them by scanning for the repo-relative candidate paths.
    uncovered = {c for c in candidates if c in err}
    assert uncovered == emitted


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
    (root / ".ai-playbook/reviews").mkdir(parents=True)
    vt_rel = ".ai-playbook/reviews/2026-09-29-vt-peer-plan-review\x0b.md"
    plain_rel = ".ai-playbook/reviews/2026-09-29-plain-peer-review-r1.md"
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
    assert ".ai-playbook/reviews/2026-09-29-vt-peer-plan-review.md" in err
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
def _write_facts_with_visibility(
    root: Path, declaration: str | None, project_type: str | None = None
) -> Path:
    """Repo facts file in the production TOML-fence form, optionally carrying
    the project_type and artifact_visibility declarations inside the fence
    (the only block facts_paths.resolve_toml_key_raw parses)."""
    facts_dir = root / ".ai-playbook"
    facts_dir.mkdir(parents=True, exist_ok=True)
    facts = facts_dir / "facts.md"
    lines = [
        "```toml\n",
        'plans_dir = "docs/history/plans/"\n',
        'plans_completed_dir = "docs/history/plans/completed/"\n',
        'backlog_dir = "docs/history/backlog/"\n',
        'reviews_dir = ".ai-playbook/reviews/"\n',
        'tmp_dir = "docs/tmp/"\n',
    ]
    if project_type is not None:
        lines.append('project_type = "' + project_type + '"\n')
    if declaration is not None:
        lines.append(declaration + "\n")
    lines.append("```\n")
    facts.write_text("".join(lines), encoding="utf-8")
    return facts


def _visibility_fixture(
    tmp_path: Path,
    name: str,
    declaration: str | None,
    project_type: str | None = None,
):
    """Scratch repo with a committed Jira-link file, an untracked Jira-link
    file, and a separate credential-bearing control file."""
    root = make_repo(tmp_path, name, gitignore_docs=True)
    _write_facts_with_visibility(root, declaration, project_type)
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
    """[class: REPOSITORY_TEST] A pet repository (project_type = "pet")
    declaring artifact_visibility = "private" returns rc 0 under the profile
    exemption: both content arms are skipped, so the valid internal service
    links pass regardless of the credential control."""
    root = _visibility_fixture(
        tmp_path, "private-link", 'artifact_visibility = "private"', "pet"
    )
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


def test_visibility_scoped_private_repo_credentials_exempt_by_profile_direction(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Per the 2026-10-12 operator direction in
    docs/history/backlog/2026-10-12-done-private-repository-visibility-scan.md,
    a pet project (project_type = "pet") declaring
    artifact_visibility = "private" is exempt from both content arms:
    staged credential material alone no longer fails the gate, and the
    result message names the profile-scoped exemption."""
    root = _visibility_fixture(
        tmp_path, "private-cred", 'artifact_visibility = "private"', "pet"
    )
    (root / "untracked-link.md").unlink()
    git(root, "add", "credential-control.txt")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 0, result.message
    assert "profile exemption" in result.message


def test_visibility_scoped_private_pet_allows_public_patterns(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Given project_type = "pet" and
    artifact_visibility = "private", a service-link pattern with no
    credentials keeps the public-artifact family skipped and the gate
    returns rc 0."""
    root = _visibility_fixture(
        tmp_path, "private-pet-link", 'artifact_visibility = "private"', "pet"
    )
    (root / "credential-control.txt").unlink()
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 0, result.message


def test_visibility_scoped_public_pet_scans_public_patterns(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Given project_type = "pet" and
    artifact_visibility = "public", the strict scan stays active: the gate
    failure names hits from both content families (credential and
    public-artifact), unchanged from today."""
    root = _visibility_fixture(
        tmp_path, "public-pet-link", 'artifact_visibility = "public"', "pet"
    )
    (root / "staged-link.md").write_text(
        "see https://company.atlassian.net/browse/TEAM-789\n",
        encoding="utf-8",
    )
    git(root, "add", "staged-link.md")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "\\.atlassian\\.net" in result.message
    assert "credential-control.txt" in result.message
    assert "staged-link.md" in result.message


def test_visibility_scoped_strict_pet_clean_names_both_families(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A pet project declaring
    artifact_visibility = "public" keeps the strict branch: with no
    violation content the clean result names both active content families,
    credential+public-artifact."""
    root = _visibility_fixture(
        tmp_path, "public-pet-clean", 'artifact_visibility = "public"', "pet"
    )
    (root / "untracked-link.md").unlink()
    (root / "credential-control.txt").unlink()
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 0, result.message
    assert "content families: credential+public-artifact" in result.message


def test_visibility_scoped_company_exempt_with_malformed_visibility(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Per the 2026-10-12 operator direction in
    docs/history/backlog/2026-10-12-done-private-repository-visibility-scan.md,
    a company project (project_type = "company") is exempt from both content
    arms regardless of the visibility value: even a malformed
    artifact_visibility value beside the company declaration keeps the gate
    at rc 0 with the result message naming the profile-scoped exemption."""
    root = _visibility_fixture(
        tmp_path,
        "company-malformed-visibility",
        'artifact_visibility = "semi-private"',
        "company",
    )
    (root / "staged-cred.txt").write_text(
        'password = "hunter2-staged-company"\n', encoding="utf-8"
    )
    git(root, "add", "staged-cred.txt")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 0, result.message
    assert "profile exemption" in result.message
    assert "content families" not in result.message


def test_visibility_scoped_company_profile_skips_content_arms(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Per the 2026-10-12 operator direction in
    docs/history/backlog/2026-10-12-done-private-repository-visibility-scan.md,
    a company project with a staged public-artifact line passes the gate:
    both content arms are skipped, the matched pattern appears nowhere in
    the result, and the message names the profile-scoped exemption."""
    root = _visibility_fixture(tmp_path, "company-staged-link", None, "company")
    (root / "untracked-link.md").unlink()
    (root / "credential-control.txt").unlink()
    staged = root / "staged-link.md"
    staged.write_text(
        "see https://company.atlassian.net/browse/TEAM-789\n",
        encoding="utf-8",
    )
    git(root, "add", "staged-link.md")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 0, result.message
    assert "atlassian" not in result.message
    assert "profile exemption" in result.message


def test_visibility_scoped_missing_project_type_ignores_private_visibility(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] With no project_type recorded, a legacy
    artifact_visibility = "private" does not exempt: a staged public-artifact
    line still fails the gate rc 1."""
    root = _visibility_fixture(
        tmp_path, "typeless-private-link", 'artifact_visibility = "private"'
    )
    staged = root / "staged-fallback-link.md"
    staged.write_text(
        "notes under /Users/carol/notes/plan.md\n", encoding="utf-8"
    )
    git(root, "add", "staged-fallback-link.md")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "staged-fallback-link.md" in result.message


def test_visibility_scoped_invalid_project_type_ignores_private_visibility(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] An invalid project_type (neither pet nor
    company) with artifact_visibility = "private" does not exempt: a staged
    public-artifact line still fails the gate rc 1."""
    root = _visibility_fixture(
        tmp_path,
        "invalid-type-private-link",
        'artifact_visibility = "private"',
        "personal",
    )
    staged = root / "staged-fallback-link.md"
    staged.write_text(
        "notes under /Users/dave/notes/plan.md\n", encoding="utf-8"
    )
    git(root, "add", "staged-fallback-link.md")
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "staged-fallback-link.md" in result.message


def test_visibility_scoped_pet_without_private_visibility_keeps_strict(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A pet project whose artifact_visibility is
    absent or malformed does not resolve to private, so the strict scan
    stays active: a staged public-artifact line fails the gate rc 1 in both
    rows."""
    for name, declaration in (
        ("pet-absent-visibility", None),
        ("pet-malformed-visibility", 'artifact_visibility = "semi-private"'),
    ):
        root = _visibility_fixture(tmp_path, name, declaration, "pet")
        staged = root / "staged-fallback-link.md"
        staged.write_text(
            "notes under /Users/erin/notes/plan.md\n", encoding="utf-8"
        )
        git(root, "add", "staged-fallback-link.md")
        result = run_gate("sensitive-data-scan", ctx_for(root))
        assert result.rc == 1, result.message
        assert "staged-fallback-link.md" in result.message


def test_visibility_scoped_company_push_range_attribution_still_fails(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] The profile exemption covers the content arms
    only: a company project whose push-range commit message carries a
    Co-authored-by trailer still fails the gate on the attribution finding,
    and the failure result never claims the profile exemption."""
    root = _repo_with_upstream(tmp_path, "company-trailer")
    _write_facts_with_visibility(root, None, "company")
    (root / "note.txt").write_text("harmless\n", encoding="utf-8")
    git(root, "add", "note.txt")
    git(
        root,
        "commit",
        "-m",
        "add note",
        "-m",
        "Co-authored-by: someone <s@e.st>",
        "-q",
    )
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 1
    assert "Co-authored-by" in result.message
    assert "push-range commit" in result.message
    assert "profile exemption" not in result.message


def test_visibility_scoped_private_pet_credentials_exempt_by_profile_direction(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Per the 2026-10-12 operator direction in
    docs/history/backlog/2026-10-12-done-private-repository-visibility-scan.md,
    a private pet (project_type = "pet", artifact_visibility = "private")
    with an untracked credential-shaped line is exempt from both content
    arms: the untracked-content arm skips the family, the gate returns rc 0,
    and the result message names the profile-scoped exemption."""
    root = _visibility_fixture(
        tmp_path, "private-pet-cred", 'artifact_visibility = "private"', "pet"
    )
    (root / "untracked-link.md").unlink()
    result = run_gate("sensitive-data-scan", ctx_for(root))
    assert result.rc == 0, result.message
    assert "profile exemption" in result.message


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
    sidecar_rel = ".ai-playbook/reviews/2026-09-30-own-review-r1.stats.json"
    twin_rel = ".ai-playbook/reviews/2026-09-30-own-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
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
    sidecar_rel = ".ai-playbook/reviews/2026-09-30-own-review-r1.stats.json"
    (root / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
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
    owned_rel = ".ai-playbook/reviews/2026-09-30-own-review-r1.md"
    (root / ".ai-playbook/reviews").mkdir(parents=True, exist_ok=True)
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
    naming an over-cap tracked fixture skill and passes rc 0 on an
    under-cap tree (the checker is copied repo-local into each fixture so
    the deployment-gap path is not exercised here; the fixture skill is
    committed because the default scan inside a checkout selects tracked
    skills)."""
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
    git(root, "add", "agents")
    git(root, "commit", "-m", "skill", "-q")
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
    # Track the under-cap fixture so the rc 0 leg proves measurement of a
    # tracked under-cap skill, not vacuous selection silence.
    git(root2, "add", "agents")
    git(root2, "commit", "-m", "skill", "-q")
    result2 = run_gate("description-length", ctx_for(root2))
    assert result2.rc == 0, result2.message


# --------------------------------------------------------------------------- #
# Plan checkbox: description-length default-scan scope  [class: REPOSITORY_TEST]
# (plan docs/history/plans/2026-10-21-description-length-checker-scope-and-
# admission.md, Task 1). These drive the checker directly (default scan vs
# explicit paths) because the gate only ever invokes the default scan.
# --------------------------------------------------------------------------- #
def _write_overcap_skill(root: Path, rel_dir: str) -> str:
    """Write an over-cap SKILL.md under ``rel_dir`` in the fixture repo;
    returns the repo-relative SKILL.md path."""
    skill_dir = root / rel_dir
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: skill\ndescription: " + "x" * 1025 + "\n---\n\nbody\n",
        encoding="utf-8",
    )
    return f"{rel_dir}/SKILL.md"


def _run_description_checker(root: Path, *args: str) -> subprocess.CompletedProcess:
    """Run the repo-local checker with cwd at the fixture root."""
    return sh(
        [sys.executable, str(SCRIPTS_DIR / "check_skill_description_length.py"), *args],
        root,
    )


def test_description_length_default_scan_selects_tracked_only(tmp_path):
    """[class: REPOSITORY_TEST] Inside a checkout the default scan reports
    tracked over-cap descriptions - including a tracked path that matches
    an ignore rule - and excludes untracked descriptions whether ignored
    or not."""
    root = make_repo(tmp_path, "desc-tracked-scope", gitignore_docs=True)
    tracked_rel = _write_overcap_skill(root, "agents/skills/overcap")
    tracked_ignored_rel = _write_overcap_skill(root, "agents/skills/ignored-but-tracked")
    untracked_ignored_rel = _write_overcap_skill(root, "agents/skills/synced/cached")
    untracked_rel = _write_overcap_skill(root, "agents/skills/draft")
    git(root, "add", "agents/skills/overcap", "agents/skills/ignored-but-tracked")
    git(root, "commit", "-m", "skills", "-q")
    gitignore = root / ".gitignore"
    gitignore.write_text(
        gitignore.read_text(encoding="utf-8")
        + "agents/skills/ignored-but-tracked/\nagents/skills/synced/\n",
        encoding="utf-8",
    )
    # Fixture honesty: the tracked one still matches an ignore rule (the
    # --no-index probe evaluates the rule for a tracked path) and the
    # synced one is untracked-ignored.
    assert (
        git(root, "check-ignore", "-q", "--no-index", tracked_ignored_rel).returncode == 0
    )
    assert git(root, "check-ignore", "-q", untracked_ignored_rel).returncode == 0
    tracked_set = {tracked_rel, tracked_ignored_rel}
    untracked_set = {untracked_ignored_rel, untracked_rel}

    result = _run_description_checker(root)

    assert result.returncode == 1, result.stderr
    out = result.stdout + result.stderr
    for rel in tracked_set:
        assert rel in out, rel
    for rel in untracked_set:
        assert rel not in out, rel
    assert "1025" in out


def test_description_length_explicit_directory_reports_untracked(tmp_path):
    """[class: REPOSITORY_TEST] Explicit-directory selection is unchanged:
    inside a checkout the named directory is scanned recursively and an
    untracked over-cap skill is still reported, while the default scan on
    the same tree stays silent."""
    root = make_repo(tmp_path, "desc-explicit-untracked", gitignore_docs=True)
    untracked_rel = _write_overcap_skill(root, "agents/skills/draft")

    default = _run_description_checker(root)
    assert default.returncode == 0, default.stderr

    explicit = _run_description_checker(root, "agents/skills")
    assert explicit.returncode == 1, explicit.stderr
    out = explicit.stdout + explicit.stderr
    assert untracked_rel in out
    assert "1025" in out


def test_description_length_default_scan_outside_checkout_recursive(tmp_path):
    """[class: REPOSITORY_TEST] Outside a checkout the default scan keeps
    its recursive selection and reports an over-cap skill description."""
    root = tmp_path / "desc-no-checkout"
    _write_overcap_skill(root, "agents/skills/orphan")
    assert not (root / ".git").exists()

    result = _run_description_checker(root)

    assert result.returncode == 1, result.stderr
    out = result.stdout + result.stderr
    assert "agents/skills/orphan/SKILL.md" in out
    assert "1025" in out


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-
# gate-sweep.md, Task 1: archive-ceremony gate (checkbox check) in the
# landing sweep.
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


def test_archive_ceremony_fails_closed_on_staged_non_utf8_archive(
    tmp_path, sweep_env
):
    """Invalid UTF-8 in a staged archive returns a gate refusal, not an exception."""
    root = make_repo(tmp_path, "ceremony-staged-non-utf8", gitignore_docs=True)
    write_facts(root)
    archive_rel = _staged_plan_archive(
        root, "2026-10-18-staged-non-utf8.md", "# Plan\n\n- [x] done\n"
    )
    archive = root / archive_rel
    archive.write_bytes(b"# Plan\n\n- [x] done\n\xff")
    assert git(root, "add", "-f", archive_rel).returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "not UTF-8" in result.message
    assert "archive-ceremony gate failed" in result.message


def test_archive_ceremony_fails_closed_on_committed_non_utf8_archive(
    tmp_path, sweep_env
):
    """Invalid UTF-8 in a committed archive returns a gate refusal, not an exception."""
    root = make_repo(tmp_path, "ceremony-committed-non-utf8", gitignore_docs=True)
    write_facts(root)
    source_rel = "docs/history/plans/2026-10-18-committed-non-utf8.md"
    source = root / source_rel
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Plan\n\n- [x] done\n", encoding="utf-8")
    assert git(root, "add", "-f", source_rel).returncode == 0
    assert git(root, "commit", "-m", "create plan", "-q").returncode == 0
    _seed_archive_boundary(root, "ceremony-committed-non-utf8")
    archive_rel = "docs/history/plans/completed/2026-10-18-committed-non-utf8.md"
    (root / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    assert git(root, "mv", source_rel, archive_rel).returncode == 0
    (root / archive_rel).write_bytes(b"# Plan\n\n- [x] done\n\xff")
    assert git(root, "add", "-f", archive_rel).returncode == 0
    assert git(root, "commit", "-m", "archive non-utf8 plan", "-q").returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "not UTF-8" in result.message
    assert "archive-ceremony gate failed" in result.message


def _write_exec_review_record(root: Path, plan_name: str) -> Path:
    """A minimal exec-review staging doc for a fixture plan, named per the
    slug convention the archive-ceremony coverage arm requires (the plan's
    stem minus its leading date prefix inside a ``-plan-review-`` series
    name ending ``-exec-r<N>``)."""
    stem = plan_name[: -len(".md")] if plan_name.endswith(".md") else plan_name
    slug = stem.split("-", 3)[3] if stem[:4].isdigit() else stem
    reviews = root / ".ai-playbook" / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    record = reviews / f"2026-10-01-plan-review-{slug}-exec-r1.md"
    record.write_text(
        "# Exec review r1\n\nVerdict: ready=yes, zero blocking.\n",
        encoding="utf-8",
    )
    return record


def _write_bound_plan_review_candidate(
    root: Path,
    *,
    name: str,
    markdown_artifact: str,
    source_digest: str,
    identity: str | None,
    verdict: str | None = "yes",
    include_markdown: bool = True,
    include_sidecar: bool = True,
) -> tuple[Path, Path]:
    """Write a review pair with independently selectable binding fields."""
    reviews = root / ".ai-playbook" / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    markdown = reviews / name
    sidecar = markdown.with_suffix(".stats.json")
    if include_markdown:
        markdown.write_text(
            f"# Plan review candidate\n\nURL or Artifact: {markdown_artifact}\n",
            encoding="utf-8",
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "record_kind": "canonical",
        "source_kind": "plan",
        "source_digest": source_digest,
    }
    if verdict is not None:
        payload["verdict"] = verdict
    extensions: dict[str, object] = {}
    if identity is not None:
        extensions["plan_identity"] = identity
    payload["extensions"] = extensions
    if include_sidecar:
        sidecar.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return markdown, sidecar


def _checked_staged_archive_fixture(
    tmp_path: Path, fixture_name: str, plan_name: str
) -> tuple[Path, str, str, bytes]:
    root = make_repo(tmp_path, fixture_name, gitignore_docs=True)
    write_facts(root)
    source_rel = f"docs/history/plans/{plan_name}"
    body = f"# Plan: {plan_name}\n\n- [x] done\n".encode("utf-8")
    archive_rel = _staged_plan_archive(root, plan_name, body.decode("utf-8"))
    return root, source_rel, archive_rel, body


def _assert_missing_exec_review_refusal(result, archive_rel: str) -> None:
    assert result.rc == 1, result.message
    assert archive_rel in result.message
    assert "no exec-review record" in result.message
    assert "produce the exec-review record" in result.message
    assert "marked reconstruction" in result.message


def _assert_bound_receipt_acceptance(
    result, archive_rel: str, record: Path, digest: str, digest_form: str
) -> None:
    """Pin the future counted acceptance warning to its record and digest."""
    assert result.rc == 0, result.message
    assert archive_rel in result.message
    warnings = "\n".join(result.warnings)
    acceptance = "\n".join(
        row for row in warnings.splitlines()
        if "bound" in row.lower() and "receipt" in row.lower()
    )
    assert acceptance
    counted_clause = r"bound-receipt acceptance\s*[:=]\s*1\b"
    assert re.search(counted_clause, result.message, re.IGNORECASE), result.message
    assert re.search(counted_clause, acceptance, re.IGNORECASE), acceptance
    assert record.name in acceptance
    assert digest in acceptance
    assert digest_form in acceptance.lower()


def _seed_archive_boundary(root: Path, run_id: str) -> str:
    boundary = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, run_id, marker.name, str(root), now,
                       start_commit=boundary)
    return boundary


def _write_committed_archive_addition(
    root: Path, plan_name: str, body: bytes, run_id: str
) -> str:
    _seed_archive_boundary(root, run_id)
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    archive = root / archive_rel
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(body)
    assert git(root, "add", "-f", archive_rel).returncode == 0
    assert git(root, "commit", "-m", "add archived plan", "-q").returncode == 0
    return archive_rel


def test_archive_ceremony_accepts_prearchive_identity_bound_to_reviewed_blob(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A staged rename binds its reviewed source."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-binding-prearchive", "2026-10-18-prearchive.md"
    )
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-prearchive-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=lib.vrs.compute_source_digest("plan", body),
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, hashlib.sha256(body).hexdigest(),
        "reviewed-revision",
    )


def test_archive_ceremony_accepts_crlf_committed_addition_raw_bytes(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Committed additions bind certified raw bytes."""
    root = make_repo(tmp_path, "ceremony-crlf-committed-addition", gitignore_docs=False)
    git(root, "config", "core.autocrlf", "false")
    write_facts(root)
    plan_name = "2026-10-18-crlf-addition.md"
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    body = b"# CRLF plan\r\n\r\n- [x] raw bytes\r\n"
    _write_committed_archive_addition(root, plan_name, body, "ceremony-crlf-add")
    archive = root / archive_rel
    assert archive.read_bytes() == body
    assert git(root, "config", "--get", "core.autocrlf").stdout.strip() == "false"
    attr = git(root, "check-attr", "text", "eol", "--", archive_rel)
    assert attr.returncode == 0
    assert "text: unspecified" in attr.stdout
    assert "eol: unspecified" in attr.stdout
    assert not (root / ".gitattributes").exists()
    digest = lib.vrs.compute_source_digest("plan", body)
    assert digest == hashlib.sha256(body).hexdigest()
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[2] == body
    assert row[3] is None
    assert row[4] == body
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-crlf-addition-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=digest,
        identity=archive_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, digest, "archived-bytes"
    )


def test_archive_ceremony_committed_addition_uses_head_blob_after_worktree_drift(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A committed addition ignores drifted worktree bytes."""
    root = make_repo(tmp_path, "ceremony-addition-worktree-drift", gitignore_docs=False)
    write_facts(root)
    plan_name = "2026-10-18-addition-drift.md"
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    body = b"# Addition\n\n- [x] committed bytes\n"
    _write_committed_archive_addition(root, plan_name, body, "ceremony-add-drift")
    (root / archive_rel).write_bytes(body + b"worktree-only drift\n")
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[2] == body
    assert row[4] == body
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-addition-drift-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=lib.vrs.compute_source_digest("plan", body),
        identity=archive_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, hashlib.sha256(body).hexdigest(),
        "archived-bytes",
    )


def test_archive_ceremony_accepts_binding_latest_review_round(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A stale prior round does not shadow the binding round."""
    root = make_repo(tmp_path, "ceremony-binding-latest-round", gitignore_docs=False)
    write_facts(root)
    plan_name = "2026-10-18-latest-round.md"
    source_rel = f"docs/history/plans/{plan_name}"
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    initial = b"# Plan: latest round\n\n- [x] done\n"
    (root / source_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / source_rel).write_bytes(initial)
    assert git(root, "add", "-f", source_rel).returncode == 0
    assert git(root, "commit", "-m", "initial reviewed plan", "-q").returncode == 0
    amended = initial + b"post-review amendment\n"
    (root / source_rel).write_bytes(amended)
    assert git(root, "add", "-f", source_rel).returncode == 0
    assert git(root, "commit", "-m", "amend reviewed plan", "-q").returncode == 0
    (root / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    assert git(root, "mv", source_rel, archive_rel).returncode == 0
    stale, _ = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-latest-round-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(initial).hexdigest(),
        identity=source_rel,
    )
    binding, _ = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-latest-round-r2.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(amended).hexdigest(),
        identity=source_rel,
    )
    assert stale.name < binding.name

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, binding, hashlib.sha256(amended).hexdigest(),
        "reviewed-revision",
    )


def test_archive_ceremony_accepts_binding_round_after_malformed_candidate(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A malformed candidate does not shadow a later binding record."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-binding-malformed-neighbor", "2026-10-18-malformed-neighbor.md"
    )
    malformed, malformed_sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-malformed-neighbor-r1.md",
        markdown_artifact=archive_rel,
        source_digest="not-a-digest",
        identity=None,
    )
    malformed_sidecar.write_text("{ malformed json", encoding="utf-8")
    binding, _ = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-malformed-neighbor-r2.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )
    assert malformed.name < binding.name

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, binding, hashlib.sha256(body).hexdigest(),
        "reviewed-revision",
    )


def test_stale_deliverables_twin_accepts_deliverables_identity_archived_digest(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Stale twins bind deliverables identity and archive bytes."""
    root = make_repo(tmp_path, "ceremony-stale-deliverables-binding", gitignore_docs=False)
    write_facts(root)
    plan_name = "2026-10-18-stale-deliverables.md"
    source_rel = f"docs/history/plans/{plan_name}"
    body = b"# Stale twin\n\n- [x] archived\n"
    archive_rel = _committed_plan_archive(root, plan_name, body.decode())
    _seed_archive_boundary(root, "ceremony-stale-twin")
    write_deliverables(root, [source_rel])
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-stale-deliverables-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[3] == source_rel
    assert row[4] is None

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, hashlib.sha256(body).hexdigest(),
        "archived-bytes",
    )


def _committed_rename_binding_fixture(
    root: Path, plan_name: str, initial: bytes, run_id: str
) -> tuple[str, str, bytes, bytes]:
    write_facts(root)
    source_rel = f"docs/history/plans/{plan_name}"
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    (root / source_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / source_rel).write_bytes(initial)
    assert git(root, "add", "-f", source_rel).returncode == 0
    assert git(root, "commit", "-m", "add reviewed plan", "-q").returncode == 0
    _seed_archive_boundary(root, run_id)
    return source_rel, archive_rel, initial, initial


def test_committed_rename_base_blob_digest_refuses_wrong_revision(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A base blob cannot approximate the rename parent."""
    root = make_repo(tmp_path, "ceremony-wrong-revision", gitignore_docs=False)
    plan_name = "2026-10-18-wrong-revision.md"
    initial = (b"# Wrong revision\n\n- [x] reviewed\n" + b"stable line\n" * 50)
    source_rel, archive_rel, base_bytes, _ = _committed_rename_binding_fixture(
        root, plan_name, initial, "ceremony-wrong-revision"
    )
    amended = initial.replace(b"reviewed", b"amended", 1)
    (root / source_rel).write_bytes(amended)
    assert git(root, "add", "-f", source_rel).returncode == 0
    assert git(root, "commit", "-m", "post-review amendment", "-q").returncode == 0
    assert git(root, "mv", source_rel, archive_rel).returncode == 0
    assert git(root, "commit", "-m", "archive amended plan", "-q").returncode == 0
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-wrong-revision-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(base_bytes).hexdigest(),
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_committed_rename_archive_digest_with_prearchive_identity_refuses(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Matching archive bytes cannot replace reviewed bytes."""
    root = make_repo(tmp_path, "ceremony-form-quantifier", gitignore_docs=False)
    plan_name = "2026-10-18-form-quantifier.md"
    initial = (b"# Form quantifier\n\n- [x] reviewed\n" + b"stable line\n" * 50)
    source_rel, archive_rel, reviewed, _ = _committed_rename_binding_fixture(
        root, plan_name, initial, "ceremony-form-quantifier"
    )
    assert git(root, "mv", source_rel, archive_rel).returncode == 0
    archived = initial.replace(b"reviewed", b"archive edit", 1)
    (root / archive_rel).write_bytes(archived)
    assert git(root, "add", "-f", archive_rel).returncode == 0
    assert git(root, "commit", "-m", "archive with edit", "-q").returncode == 0
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-form-quantifier-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(archived).hexdigest(),
        identity=source_rel,
    )
    assert hashlib.sha256(reviewed).hexdigest() != hashlib.sha256(archived).hexdigest()

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_untracked_addition_former_plans_identity_refuses(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An addition has no recovered old-path identity."""
    root = make_repo(tmp_path, "ceremony-addition-former-identity", gitignore_docs=False)
    write_facts(root)
    plan_name = "2026-10-18-former-plans-identity.md"
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    source_rel = f"docs/history/plans/{plan_name}"
    body = b"# Addition\n\n- [x] no old path\n"
    archive = root / archive_rel
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(body)
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-former-identity-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_committed_rename_archive_identity_refuses_even_matching_digest(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A rename requires its recovered source identity."""
    root = make_repo(tmp_path, "ceremony-rename-archive-identity", gitignore_docs=False)
    plan_name = "2026-10-18-rename-archive-identity.md"
    body = b"# Rename identity\n\n- [x] checked\n"
    source_rel, archive_rel, _, _ = _committed_rename_binding_fixture(
        root, plan_name, body, "ceremony-rename-archive-identity"
    )
    assert git(root, "mv", source_rel, archive_rel).returncode == 0
    assert git(root, "commit", "-m", "archive plan", "-q").returncode == 0
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-rename-archive-identity-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=archive_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_untracked_addition_archive_identity_accepts(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Untracked additions bind the archive-state identity."""
    root = make_repo(tmp_path, "ceremony-untracked-addition-binding", gitignore_docs=False)
    write_facts(root)
    plan_name = "2026-10-18-untracked-addition.md"
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    body = b"# Untracked addition\n\n- [x] checked\n"
    archive = root / archive_rel
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(body)
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-untracked-addition-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=archive_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, hashlib.sha256(body).hexdigest(),
        "archived-bytes",
    )


def test_archive_ceremony_refuses_bound_sidecar_without_markdown_record(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A sidecar alone is not a live review record."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-sidecar-only", "2026-10-18-sidecar-only.md"
    )
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-sidecar-only-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )
    record.unlink()

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


@pytest.mark.parametrize("retired_infix", [".backup-20261018T120000", ".orphan-20261018T120000"])
def test_archive_ceremony_refuses_retired_review_pair(
    tmp_path, sweep_env, retired_infix
):
    """[class: REPOSITORY_TEST] Backup and orphan pairs are retired evidence."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, f"ceremony-retired-{retired_infix.split('-')[0]}",
        "2026-10-18-retired-pair.md",
    )
    _write_bound_plan_review_candidate(
        root,
        name=f"2026-10-18-plan-review-retired-pair-exec-r1{retired_infix}.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_archive_ceremony_refuses_bound_record_with_wrong_digest(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Matching identity cannot rescue a bad digest."""
    root, source_rel, archive_rel, _body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-wrong-digest", "2026-10-18-wrong-digest.md"
    )
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-wrong-digest-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest="0" * 64,
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)
    assert "bound-receipt acceptance" in result.message


def test_archive_ceremony_refuses_matching_digest_with_foreign_identity(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A reviewed digest cannot bind another plan."""
    root, _source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-foreign-identity", "2026-10-18-foreign-id.md"
    )
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-foreign-id-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity="docs/history/plans/2026-10-18-some-other-plan.md",
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_archive_ceremony_refuses_missing_sidecar_identity(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Markdown artifact text cannot supply identity."""
    root, _source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-no-identity", "2026-10-18-no-identity.md"
    )
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-no-identity-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=None,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_archive_ceremony_refuses_basename_only_sidecar_identity(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A basename does not bind the archived plan."""
    plan_name = "2026-10-18-basename-only.md"
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-basename", plan_name
    )
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-basename-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=Path(source_rel).name,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_archive_ceremony_refuses_live_review_without_stats_sidecar(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A markdown candidate without its sidecar declines."""
    root, _source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-no-sidecar", "2026-10-18-no-sidecar.md"
    )
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-no-sidecar-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=None,
        include_sidecar=False,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_archive_ceremony_refuses_rejected_twin_sidecar_identity(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Same basename in rejected is a foreign plan."""
    plan_name = "2026-10-18-rejected-twin.md"
    root, _source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-rejected-twin", plan_name
    )
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-rejected-twin-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=f"docs/history/plans/rejected/{plan_name}",
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


@pytest.mark.parametrize("verdict", ["no", None])
def test_archive_ceremony_refuses_nonpassing_sidecar_verdict(
    tmp_path, sweep_env, verdict
):
    """[class: REPOSITORY_TEST] Only an explicit yes verdict can bind."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, f"ceremony-bound-verdict-{verdict or 'absent'}",
        "2026-10-18-nonpassing-verdict.md",
    )
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-nonpassing-verdict-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
        verdict=verdict,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_archive_ceremony_declines_unreadable_candidate_sidecar(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] An unreadable sidecar declines, then refuses."""
    root, _source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-bound-unreadable-sidecar", "2026-10-18-unreadable.md"
    )
    _record, sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-unreadable-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity="docs/history/plans/2026-10-18-unreadable.md",
    )
    sidecar.write_text("{ malformed json", encoding="utf-8")

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_archive_ceremony_filename_receipt_tolerates_malformed_neighbor(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A malformed candidate cannot block a valid receipt."""
    root2, _source2, archive2, _body2 = _checked_staged_archive_fixture(
        tmp_path, "ceremony-filename-review-bad-neighbor",
        "2026-10-18-filename-review.md",
    )
    _write_exec_review_record(root2, "2026-10-18-filename-review.md")
    _record2, malformed_sidecar = _write_bound_plan_review_candidate(
        root2,
        name="2026-10-18-plan-review-filename-review-r2.md",
        markdown_artifact=archive2,
        source_digest="invalid",
        identity=None,
    )
    malformed_sidecar.write_text("{ malformed json", encoding="utf-8")

    result2 = run_gate("archive-ceremony", ctx_for(root2))

    assert result2.rc == 0, result2.message
    assert archive2 in result2.message


def test_archive_ceremony_keeps_filename_receipt_unchanged(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Existing filename receipt acceptance is unchanged."""
    root, _source_rel, archive_rel, _body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-filename-receipt-unchanged",
        "2026-10-18-filename-receipt.md",
    )
    _write_exec_review_record(root, "2026-10-18-filename-receipt.md")
    result = run_gate("archive-ceremony", ctx_for(root))
    assert result.rc == 0, result.message
    assert archive_rel in result.message


def test_archive_ceremony_keeps_rejected_state_exemption_unchanged(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Rejected-state archives remain exempt."""
    rejected_root = make_repo(tmp_path, "ceremony-rejected-exemption-unchanged", gitignore_docs=True)
    write_facts(rejected_root)
    plan_name = "2026-10-18-rejected-exempt.md"
    plan_rel = f"docs/history/plans/{plan_name}"
    rejected_rel = f"docs/history/plans/rejected/{plan_name}"
    (rejected_root / plan_rel).parent.mkdir(parents=True, exist_ok=True)
    (rejected_root / plan_rel).write_text(
        "# Plan: rejected\n\n- [ ] intentionally declined\n", encoding="utf-8"
    )
    git(rejected_root, "add", "-f", plan_rel)
    git(rejected_root, "commit", "-m", "add rejected plan", "-q")
    (rejected_root / rejected_rel).parent.mkdir(parents=True, exist_ok=True)
    assert git(rejected_root, "mv", plan_rel, rejected_rel).returncode == 0
    result2 = run_gate("archive-ceremony", ctx_for(rejected_root))
    assert result2.rc == 0, result2.message
    assert rejected_rel in result2.message
    assert any("rejected-state archive exempt" in row for row in result2.warnings)


def test_task4_committed_rename_drift_accepts_parent_blob_with_divergence(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Parent-blob evidence names exact archive drift."""
    root = make_repo(tmp_path, "ceremony-task4-committed-drift", gitignore_docs=False)
    plan_name = "2026-10-18-committed-drift.md"
    original = b"# Committed drift\n\n- [x] reviewed bytes\n" + b"stable\n" * 60
    source_rel, archive_rel, _base, _ = _committed_rename_binding_fixture(
        root, plan_name, original, "ceremony-task4-committed-drift"
    )
    archived = original.replace(b"reviewed bytes", b"amended bytes", 1)
    assert git(root, "mv", source_rel, archive_rel).returncode == 0
    (root / archive_rel).write_bytes(archived)
    assert git(root, "add", "-f", archive_rel).returncode == 0
    assert git(root, "commit", "-m", "archive with amendment", "-q").returncode == 0
    parent_digest = hashlib.sha256(original).hexdigest()
    archived_digest = hashlib.sha256(archived).hexdigest()
    assert parent_digest != archived_digest
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-committed-drift-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=parent_digest,
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, parent_digest, "reviewed-revision"
    )
    assert any(
        parent_digest in warning
        and archived_digest in warning
        and "unreviewed" in warning.lower()
        for warning in result.warnings
    )


def _task4_degenerate_rename_fixture(root: Path, suffix: str):
    write_facts(root)
    old_rel = f"docs/history/plans/2026-10-18-degenerate-{suffix}.md"
    archive_rel = f"docs/history/plans/completed/2026-10-18-degenerate-{suffix}.md"
    base = b"# Degenerate\n\n" + b"stable line\n" * 80 + b"- [x] done\n"
    (root / old_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / old_rel).write_bytes(base)
    assert git(root, "add", "-f", old_rel).returncode == 0
    assert git(root, "commit", "-m", "reviewed plan", "-q").returncode == 0
    _seed_archive_boundary(root, f"ceremony-task4-degenerate-{suffix}")
    intermediate = base.replace(b"stable line\n", b"amended line\n", 1)
    (root / old_rel).write_bytes(intermediate)
    assert git(root, "add", "-f", old_rel).returncode == 0
    assert git(root, "commit", "-m", "intermediate edit", "-q").returncode == 0
    assert git(root, "rm", old_rel, "-q").returncode == 0
    assert git(root, "commit", "-m", "delete before archive", "-q").returncode == 0
    archived = intermediate.replace(b"done", b"finished", 1)
    (root / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / archive_rel).write_bytes(archived)
    assert git(root, "add", "-f", archive_rel).returncode == 0
    assert git(root, "commit", "-m", "add archived plan", "-q").returncode == 0
    return old_rel, archive_rel, base, archived


def test_task4_degenerate_rename_accepts_archived_bytes_digest(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A degenerate rename binds its archived bytes."""
    root = make_repo(tmp_path, "ceremony-task4-degenerate-archive-bytes", gitignore_docs=False)
    old_rel, archive_rel, _base, archived = _task4_degenerate_rename_fixture(
        root, "accepted"
    )
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[3] == old_rel and row[4] is None
    digest = hashlib.sha256(archived).hexdigest()
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-degenerate-archive-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=digest,
        identity=old_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(result, archive_rel, record, digest, "archived-bytes")


def test_task4_degenerate_rename_refuses_base_blob_digest(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A degenerate rename cannot approximate a base blob."""
    root = make_repo(tmp_path, "ceremony-task4-degenerate-base-bytes", gitignore_docs=False)
    old_rel, archive_rel, base, _archived = _task4_degenerate_rename_fixture(root, "base")
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-degenerate-base-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(base).hexdigest(),
        identity=old_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, archive_rel)


def test_task4_bound_receipt_does_not_preempt_unchecked_box_refusal(
    tmp_path, sweep_env, monkeypatch
):
    """[class: REPOSITORY_TEST] Checkbox refusal precedes receipt evaluation."""
    root = make_repo(tmp_path, "ceremony-task4-precedence", gitignore_docs=True)
    plan_name = "2026-10-18-precedence.md"
    body = b"# Plan\n\n- [ ] unchecked\n"
    archive_rel = _staged_plan_archive(root, plan_name, body.decode())
    source_rel = f"docs/history/plans/{plan_name}"
    _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-precedence-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )
    calls = []
    helper = lib._find_bound_review_receipt

    def recording_helper(*args, **kwargs):
        calls.append((args, kwargs))
        return helper(*args, **kwargs)

    monkeypatch.setattr(lib, "_find_bound_review_receipt", recording_helper)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "1 unchecked task box(es)" in result.message
    assert archive_rel in result.message
    assert "no exec-review record" not in result.message
    assert calls == []


def test_task4_staged_rename_drift_names_both_raw_digests(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Staged drift reports both exact raw digests."""
    root = make_repo(tmp_path, "ceremony-task4-staged-drift", gitignore_docs=True)
    plan_name = "2026-10-18-staged-drift.md"
    original = b"# Staged drift\n\n- [x] reviewed\n" + b"stable\n" * 20
    archive_rel = _staged_plan_archive(root, plan_name, original.decode())
    source_rel = f"docs/history/plans/{plan_name}"
    archived = original.replace(b"reviewed", b"amended", 1)
    (root / archive_rel).write_bytes(archived)
    assert git(root, "add", "-f", archive_rel).returncode == 0
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-staged-drift-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(original).hexdigest(),
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    original_digest = hashlib.sha256(original).hexdigest()
    archived_digest = hashlib.sha256(archived).hexdigest()
    _assert_bound_receipt_acceptance(
        result, archive_rel, record, original_digest, "reviewed-revision"
    )
    assert any(
        original_digest in warning
        and archived_digest in warning
        and "unreviewed" in warning.lower()
        for warning in result.warnings
    )


def test_task4_staged_rename_without_drift_has_no_divergence_clause(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Equal staged and reviewed bytes need no divergence."""
    original = b"# Staged drift\n\n- [x] reviewed\n" + b"stable\n" * 20
    original_digest = hashlib.sha256(original).hexdigest()
    clean_root = make_repo(tmp_path, "ceremony-task4-staged-no-drift", gitignore_docs=True)
    clean_archive_rel = _staged_plan_archive(
        clean_root, "2026-10-18-staged-no-drift.md", original.decode()
    )
    clean_source_rel = "docs/history/plans/2026-10-18-staged-no-drift.md"
    clean_record, _ = _write_bound_plan_review_candidate(
        clean_root,
        name="2026-10-18-plan-review-staged-no-drift-binding-r1.md",
        markdown_artifact=clean_archive_rel,
        source_digest=original_digest,
        identity=clean_source_rel,
    )
    clean = run_gate("archive-ceremony", ctx_for(clean_root))
    _assert_bound_receipt_acceptance(
        clean, clean_archive_rel, clean_record, original_digest, "reviewed-revision"
    )
    assert "divergence" not in "\n".join(clean.warnings).lower()
    assert "unreviewed" not in "\n".join(clean.warnings).lower()


def test_task4_screens_full_long_control_character_basename(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Receipt warnings screen without truncating names."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-task4-screening", "2026-10-18-screening.md"
    )
    basename = "2026-10-18-plan-review-" + ("long-name-" * 9) + "\x01-r1.md"
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name=basename,
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    screened = record.name.replace("\x01", "")
    assert len(screened) > 64
    assert result.rc == 0, result.message
    assert archive_rel in result.message
    warnings = "\n".join(result.warnings)
    acceptance = "\n".join(
        row for row in warnings.splitlines()
        if "bound" in row.lower() and "receipt" in row.lower()
    )
    assert acceptance
    counted_clause = r"bound-receipt acceptance\s*[:=]\s*1\b"
    assert re.search(counted_clause, result.message, re.IGNORECASE), result.message
    assert re.search(counted_clause, acceptance, re.IGNORECASE), acceptance
    assert screened in acceptance
    assert "\x01" not in acceptance
    digest = hashlib.sha256(body).hexdigest()
    assert digest in acceptance
    assert "reviewed-revision" in acceptance.lower()


def test_task4_nested_reviews_home_record_is_accepted(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Candidate search recurses through reviews home."""
    nested_root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-task4-nested-reviews", "2026-10-18-nested-reviews.md"
    )
    nested_record, nested_sidecar = _write_bound_plan_review_candidate(
        nested_root,
        name="2026-10-18-plan-review-nested-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )
    nested_dir = nested_record.parent / "archive" / "nested"
    nested_dir.mkdir(parents=True)
    nested_record.rename(nested_dir / nested_record.name)
    nested_sidecar.rename(nested_dir / nested_sidecar.name)
    nested_record = nested_dir / nested_record.name
    nested = run_gate("archive-ceremony", ctx_for(nested_root))
    _assert_bound_receipt_acceptance(
        nested, archive_rel, nested_record, hashlib.sha256(body).hexdigest(),
        "reviewed-revision",
    )


def test_task4_deferred_archive_with_bound_record_is_accepted(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Deferred state accepts its fully bound record."""
    deferred_root = make_repo(tmp_path, "ceremony-task4-deferred-archive", gitignore_docs=False)
    write_facts(deferred_root)
    plan_name = "2026-10-18-deferred-archive.md"
    deferred_source = f"docs/history/plans/{plan_name}"
    deferred_rel = f"docs/history/plans/deferred/{plan_name}"
    deferred_body = b"# Deferred\n\n- [x] complete\n"
    (deferred_root / deferred_source).parent.mkdir(parents=True, exist_ok=True)
    (deferred_root / deferred_source).write_bytes(deferred_body)
    assert git(deferred_root, "add", "-f", deferred_source).returncode == 0
    assert git(deferred_root, "commit", "-m", "add deferred plan", "-q").returncode == 0
    _seed_archive_boundary(deferred_root, "ceremony-task4-deferred")
    (deferred_root / deferred_rel).parent.mkdir(parents=True, exist_ok=True)
    assert git(deferred_root, "mv", deferred_source, deferred_rel).returncode == 0
    assert git(deferred_root, "commit", "-m", "defer plan", "-q").returncode == 0
    deferred_record, _ = _write_bound_plan_review_candidate(
        deferred_root,
        name="2026-10-18-plan-review-deferred-binding-r1.md",
        markdown_artifact=deferred_rel,
        source_digest=hashlib.sha256(deferred_body).hexdigest(),
        identity=deferred_source,
    )
    deferred = run_gate("archive-ceremony", ctx_for(deferred_root))
    _assert_bound_receipt_acceptance(
        deferred, deferred_rel, deferred_record,
        hashlib.sha256(deferred_body).hexdigest(), "reviewed-revision",
    )


def test_task4_normalizes_posix_equivalent_prearchive_identity(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Posix-equivalent identity paths bind equally."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-task4-normalized-identity", "2026-10-18-normalized-identity.md"
    )
    identity = source_rel.replace("docs/history/plans/", "docs/history/plans/./", 1)
    assert identity != source_rel
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-normalized-identity-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=identity,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, hashlib.sha256(body).hexdigest(),
        "reviewed-revision",
    )


def test_task5_bound_receipt_ignores_unconsumed_sidecar_fields(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] The arm reads only its three binding fields."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-task5-minimal-sidecar", "2026-10-18-minimal-sidecar.md"
    )
    digest = hashlib.sha256(body).hexdigest()
    record, sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-minimal-sidecar-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=digest,
        identity=source_rel,
    )
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["schema_version"] = "not revalidated by the archive arm"
    payload["record_kind"] = None
    payload["source_kind"] = {"unexpected": "shape"}
    sidecar.write_text(json.dumps(payload), encoding="utf-8")

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, digest, "reviewed-revision"
    )


def test_task5_single_file_named_plan_md_accepts_bound_receipt(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A bare PLAN.md archive remains a single file."""
    root, source_rel, archive_rel, body = _checked_staged_archive_fixture(
        tmp_path, "ceremony-task5-bare-plan-md", "PLAN.md"
    )
    digest = hashlib.sha256(body).hexdigest()
    record, _sidecar = _write_bound_plan_review_candidate(
        root,
        name="2026-10-18-plan-review-bare-charter-name-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=digest,
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_bound_receipt_acceptance(
        result, archive_rel, record, digest, "reviewed-revision"
    )


def test_archive_ceremony_refuses_bound_directory_charter_candidate(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Directory archives stay outside bound receipts."""
    root = make_repo(tmp_path, "ceremony-bound-directory-charter", gitignore_docs=True)
    write_facts(root)
    slug = "2026-10-18-bound-directory"
    source_dir = root / "docs/history/plans" / slug
    (source_dir / "tasks").mkdir(parents=True)
    source_rel = f"docs/history/plans/{slug}/PLAN.md"
    archive_rel = f"docs/history/plans/completed/{slug}/PLAN.md"
    body = b"# Plan: directory\n\n- [x] charter done\n"
    (source_dir / "PLAN.md").write_bytes(body)
    (source_dir / "tasks/01-task.md").write_text(
        "### Task 1\n\n- [x] task done\n", encoding="utf-8"
    )
    git(root, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01-task.md")
    git(root, "commit", "-m", "add directory plan", "-q")
    archive_dir = root / "docs/history/plans/completed" / slug
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    git(root, "mv", f"docs/history/plans/{slug}",
        f"docs/history/plans/completed/{slug}")
    _write_bound_plan_review_candidate(
        root,
        name=f"2026-10-18-plan-review-{slug}-binding-r1.md",
        markdown_artifact=archive_rel,
        source_digest=hashlib.sha256(body).hexdigest(),
        identity=source_rel,
    )

    result = run_gate("archive-ceremony", ctx_for(root))

    _assert_missing_exec_review_refusal(result, f"docs/history/plans/completed/{slug}")


def test_archive_derivation_carries_staged_source_and_archive_bytes(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Staged rename and untracked addition rows
    retain exact byte evidence and identify whether a source revision exists."""
    root = make_repo(tmp_path, "archive-byte-derivation-staged", gitignore_docs=False)
    git(root, "config", "core.autocrlf", "false")
    write_facts(root)
    plan_name = "2026-10-03-staged-evidence.md"
    body = b"# Plan\r\n\r\n- [x] staged\r\n"
    archive_rel = _staged_plan_archive(root, plan_name, body.decode())
    source_rel = f"docs/history/plans/{plan_name}"

    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))

    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[1] == body.decode()
    assert row[2] == body
    assert row[3] == source_rel
    assert row[4] == body

    addition_rel = "docs/history/plans/completed/2026-10-04-untracked.md"
    addition = b"# Addition\r\n\r\n- [x] untracked\r\n"
    (root / addition_rel).write_bytes(addition)
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    addition_row = next(row for row in rows if row[0] == addition_rel)
    assert addition_row[2] == addition
    assert addition_row[3] is None
    assert addition_row[4] == addition

    git(root, "add", "-f", addition_rel)
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    staged_row = next(row for row in rows if row[0] == addition_rel)
    assert staged_row[2] == addition
    assert staged_row[3] is None
    assert staged_row[4] == addition
    drifted = addition + b"worktree-only"
    (root / addition_rel).write_bytes(drifted)
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert any("staged archive differs from worktree bytes" in blocker
               for blocker in blockers)
    staged_drift_row = next(row for row in rows if row[0] == addition_rel)
    assert staged_drift_row[2] == drifted
    assert staged_drift_row[4] == drifted
    (root / addition_rel).write_bytes(addition)

    boundary = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, "archive-addition", marker.name, str(root), now,
                       start_commit=boundary)
    committed_rel = "docs/history/plans/completed/2026-10-08-committed-add.md"
    committed_bytes = b"# Committed addition\r\n\r\n- [x] exact\r\n"
    (root / committed_rel).write_bytes(committed_bytes)
    git(root, "add", "-f", committed_rel)
    git(root, "commit", "-m", "add archived plan", "-q")
    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    committed_row = next(row for row in rows if row[0] == committed_rel)
    assert committed_row[2] == committed_bytes
    assert committed_row[3] is None
    assert committed_row[4] == committed_bytes


def test_archive_derivation_uses_committed_rename_parent_blob(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] A committed rename recovers its immediate
    parent blob even when a post-boundary commit changed the plan first."""
    root = make_repo(tmp_path, "archive-byte-derivation-committed", gitignore_docs=False)
    git(root, "config", "core.autocrlf", "false")
    write_facts(root)
    plan_name = "2026-10-05-committed-evidence.md"
    source_rel = f"docs/history/plans/{plan_name}"
    initial = b"# Plan\r\n\r\n- [x] reviewed\r\n" + b"stable content\r\n" * 30
    (root / source_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / source_rel).write_bytes(initial)
    git(root, "add", "-f", source_rel)
    git(root, "commit", "-m", "add reviewed plan", "-q")
    boundary = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, "archive-parent", marker.name, str(root), now,
                       start_commit=boundary)
    parent_bytes = initial.replace(b"reviewed", b"parented")
    (root / source_rel).write_bytes(parent_bytes)
    git(root, "add", "-f", source_rel)
    git(root, "commit", "-m", "post-review amendment", "-q")
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    (root / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    git(root, "mv", source_rel, archive_rel)
    git(root, "commit", "-m", "archive plan", "-q")

    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))

    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[2] == parent_bytes
    assert row[3] == source_rel
    assert row[4] == parent_bytes
    assert row[4] != initial

    ctx = ctx_for(root)
    real_git_bytes = ctx.git_bytes
    rename_parent = git(root, "rev-parse", "HEAD^").stdout.strip()

    def fail_reviewed_blob(*args):
        if args == ("show", f"{rename_parent}:{source_rel}"):
            return subprocess.CompletedProcess(
                list(args), 1, stdout=b"", stderr=b"simulated reviewed blob failure"
            )
        return real_git_bytes(*args)

    ctx.git_bytes = fail_reviewed_blob
    _rows, _, failed_blockers = lib._derive_archived_plans(ctx)
    assert any("simulated reviewed blob failure" in item for item in failed_blockers)

    real_git = ctx.git

    def fail_parent_lookup(*args, **kwargs):
        if (args and args[0] == "rev-parse" and args[-1].endswith("^{commit}^")):
            return subprocess.CompletedProcess(
                list(args), 1, stdout="", stderr="simulated parent lookup failure"
            )
        return real_git(*args, **kwargs)

    ctx.git = fail_parent_lookup
    _rows, _, failed_blockers = lib._derive_archived_plans(ctx)
    assert any("simulated parent lookup failure" in item for item in failed_blockers)


def test_archive_derivation_uses_latest_matching_rename_parent(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] Repeated archive cycles recover the parent
    of the final matching rename, not an earlier archive cycle."""
    root = make_repo(tmp_path, "archive-byte-derivation-repeated", gitignore_docs=False)
    write_facts(root)
    plan_name = "2026-10-09-repeated-evidence.md"
    source_rel = f"docs/history/plans/{plan_name}"
    archive_rel = f"docs/history/plans/completed/{plan_name}"
    initial = ("# Repeated\n\n" + "stable\n" * 30 + "- [x] done\n").encode()
    (root / source_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / source_rel).write_bytes(initial)
    git(root, "add", "-f", source_rel)
    git(root, "commit", "-m", "reviewed plan", "-q")
    boundary = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, "archive-repeated", marker.name, str(root), now,
                       start_commit=boundary)

    (root / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    git(root, "mv", source_rel, archive_rel)
    git(root, "commit", "-m", "first archive", "-q")
    (root / source_rel).parent.mkdir(parents=True, exist_ok=True)
    git(root, "mv", archive_rel, source_rel)
    git(root, "commit", "-m", "restore source", "-q")
    latest_parent = initial.replace(b"stable\n", b"stable!\n", 1)
    (root / source_rel).write_bytes(latest_parent)
    git(root, "add", "-f", source_rel)
    git(root, "commit", "-m", "amend before final archive", "-q")
    (root / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    git(root, "mv", source_rel, archive_rel)
    git(root, "commit", "-m", "final archive", "-q")

    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))

    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[3] == source_rel
    assert row[4] == latest_parent
    assert row[4] != initial


def test_archive_derivation_marks_stale_and_degenerate_rename_evidence(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Stale twins use their deliverables path
    without a reviewed blob; delete/add histories never guess a base blob."""
    root = make_repo(tmp_path, "archive-byte-derivation-stale", gitignore_docs=False)
    write_facts(root)
    plan_name = "2026-10-06-stale-evidence.md"
    source_rel = f"docs/history/plans/{plan_name}"
    body = "# Stale\n\n- [x] archived\n"
    archive_rel = _committed_plan_archive(root, plan_name, body)
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    _seed_run_manifest(root, "archive-stale", marker.name, str(root), now)
    write_deliverables(root, [source_rel])

    rows, _, blockers = lib._derive_archived_plans(ctx_for(root))
    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[2] == body.encode()
    assert row[3] == source_rel
    assert row[4] is None

    # A delete and a later add can appear as a rename in the aggregate
    # boundary diff. There is no rename commit from which to recover a parent
    # blob, so the base revision must not be substituted.
    degenerate = make_repo(tmp_path, "archive-byte-derivation-degenerate", gitignore_docs=False)
    write_facts(degenerate)
    old_rel = "docs/history/plans/2026-10-07-degenerate-evidence.md"
    archive_rel = f"docs/history/plans/completed/2026-10-07-degenerate-evidence.md"
    old = ("# Degenerate\n\n" + "line\n" * 80 + "- [x] done\n").encode()
    (degenerate / old_rel).parent.mkdir(parents=True, exist_ok=True)
    (degenerate / old_rel).write_bytes(old)
    git(degenerate, "add", "-f", old_rel)
    git(degenerate, "commit", "-m", "reviewed plan", "-q")
    boundary = git(degenerate, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(degenerate, now, os.getpid())
    _seed_run_manifest(degenerate, "archive-degenerate", marker.name,
                       str(degenerate), now, start_commit=boundary)
    intermediate = old.replace(b"line\n", b"line!\n", 1)
    (degenerate / old_rel).write_bytes(intermediate)
    git(degenerate, "add", "-f", old_rel)
    git(degenerate, "commit", "-m", "intermediate edit", "-q")
    git(degenerate, "rm", old_rel, "-q")
    git(degenerate, "commit", "-m", "delete before archive", "-q")
    archived = intermediate.replace(b"done", b"finished")
    (degenerate / archive_rel).parent.mkdir(parents=True, exist_ok=True)
    (degenerate / archive_rel).write_bytes(archived)
    git(degenerate, "add", "-f", archive_rel)
    git(degenerate, "commit", "-m", "add archived plan", "-q")

    rows, _, blockers = lib._derive_archived_plans(ctx_for(degenerate))
    assert not blockers, blockers
    row = next(row for row in rows if row[0] == archive_rel)
    assert row[2] == archived
    assert row[3] == old_rel
    assert row[4] is None


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


def test_archive_ceremony_rejected_state_exempt_completed_still_refuses(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Given a same-run staged rename into the
    ``plans/rejected/`` archive state whose bytes carry unchecked task boxes
    and no exec-review record, expects the archive-ceremony gate to pass
    rc 0 with one exempt informational line naming the archive (the
    rejected disposition stands; never certified as executed), while the
    identical unchecked shape renamed into ``completed/`` still fails rc 1
    with the unchecked-box finding."""
    root = make_repo(tmp_path, "ceremony-rejected", gitignore_docs=True)
    write_facts(root)
    body = "# Plan: demo\n\n## Tasks\n\n- [ ] one\n- [ ] two\n"
    plans = root / "docs" / "history" / "plans"
    (plans / "rejected").mkdir(parents=True, exist_ok=True)
    plan_rel = "docs/history/plans/2026-09-30-rejected-demo.md"
    (root / plan_rel).write_text(body, encoding="utf-8")
    git(root, "add", "-f", plan_rel)
    git(root, "commit", "-m", "plan", "-q")
    rejected_rel = "docs/history/plans/rejected/2026-09-30-rejected-demo.md"
    assert git(root, "mv", plan_rel, rejected_rel).returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 0, result.message
    assert rejected_rel in result.message
    assert any(
        "rejected-state archive exempt" in row for row in result.warnings
    ), result.warnings

    root2 = make_repo(
        tmp_path, "ceremony-completed-contrast", gitignore_docs=True
    )
    write_facts(root2)
    (root2 / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    plan_rel2 = "docs/history/plans/2026-09-30-completed-contrast.md"
    (root2 / plan_rel2).write_text(body, encoding="utf-8")
    git(root2, "add", "-f", plan_rel2)
    git(root2, "commit", "-m", "plan", "-q")
    assert git(
        root2,
        "mv",
        plan_rel2,
        "docs/history/plans/completed/2026-09-30-completed-contrast.md",
    ).returncode == 0

    result2 = run_gate("archive-ceremony", ctx_for(root2))

    assert result2.rc == 1, result2.message
    assert "2 unchecked task box(es)" in result2.message


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

def test_archive_ceremony_checks_untracked_addition_in_completed_archive(
    tmp_path, sweep_env
):
    """An untracked completed archive is still visible to the landing gate."""
    root = make_repo(tmp_path, "ceremony-untracked-archive-add", gitignore_docs=False)
    write_facts(root)
    archive_rel = "docs/history/plans/completed/2026-10-03-untracked.md"
    archive = root / archive_rel
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text("# Plan: untracked\n\n- [ ] task\n", encoding="utf-8")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert archive_rel in result.message
    assert "1 unchecked task box(es)" in result.message

    assert "check the boxes" in result.message
    assert "backfill completion record" in result.message


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


def test_archive_ceremony_uses_rebased_worktree_base_boundary(tmp_path, sweep_env):
    """A worktree rebased onto main must not inherit archive obligations
    from commits already present at that base, while its own archive remains
    in the run range."""
    root = make_repo(tmp_path, "ceremony-rebased-base", gitignore_docs=True)
    write_facts(root)
    current_plan = "docs/history/plans/2026-10-02-ceremony-current.md"
    (root / "docs/history/plans").mkdir(parents=True, exist_ok=True)
    (root / current_plan).write_text(
        "# Plan: current\n\n- [x] done\n", encoding="utf-8"
    )
    assert git(root, "add", "-f", current_plan).returncode == 0
    assert git(root, "commit", "-m", "create current plan", "-q").returncode == 0
    original_start = git(root, "rev-parse", "HEAD").stdout.strip()
    old_archive = _committed_plan_archive(
        root,
        "2026-10-01-ceremony-upstream.md",
        "# Plan: upstream\n\n- [x] done\n",
    )
    upstream_base = git(root, "rev-parse", "HEAD").stdout.strip()
    assert git(root, "checkout", "-b", "feature").returncode == 0
    current_archive = "docs/history/plans/completed/2026-10-02-ceremony-current.md"
    assert git(root, "mv", current_plan, current_archive).returncode == 0
    assert git(root, "commit", "-m", "archive current plan", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-02-ceremony-current.md")
    assert git(root, "add", "-f", ".ai-playbook/reviews").returncode == 0
    assert git(root, "commit", "-m", "record current execution review", "-q").returncode == 0

    marker = make_marker(root, time.time(), os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = original_start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 0, result.message
    assert current_archive in result.message
    assert old_archive not in result.message
    boundary_note = " ".join(result.warnings)
    assert upstream_base in boundary_note
    assert "instead of older run marker" in boundary_note


def test_archive_ceremony_keeps_feature_run_boundary_before_rebase(tmp_path, sweep_env):
    """An ordinary feature branch keeps pre-run archives outside the run."""
    root = make_repo(tmp_path, "ceremony-feature-no-rebase", gitignore_docs=True)
    write_facts(root)
    assert git(root, "checkout", "-b", "feature").returncode == 0
    upstream_archive = _committed_plan_archive(
        root,
        "2026-10-01-feature-prior.md",
        "# Plan: prior\n\n- [x] task\n",
    )
    plan = "docs/history/plans/2026-10-03-feature-plan.md"
    (root / plan).write_text("# Plan: feature\n\n- [ ] task\n", encoding="utf-8")
    assert git(root, "add", "-f", plan).returncode == 0
    assert git(root, "commit", "-m", "start feature run", "-q").returncode == 0
    feature_start = git(root, "rev-parse", "HEAD").stdout.strip()

    current_archive = "docs/history/plans/completed/2026-10-03-feature-plan.md"
    (root / current_archive).parent.mkdir(parents=True, exist_ok=True)
    (root / plan).write_text("# Plan: feature\n\n- [x] task\n", encoding="utf-8")
    assert git(root, "add", "-f", plan).returncode == 0
    assert git(root, "mv", plan, current_archive).returncode == 0
    assert git(root, "commit", "-m", "archive feature plan", "-q").returncode == 0

    marker = make_marker(root, time.time(), os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = feature_start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_exec_review_record(root, "2026-10-03-feature-plan.md")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 0, result.message
    assert current_archive in result.message
    assert upstream_archive not in result.message
    assert "using worktree base-branch merge base" not in " ".join(result.warnings)


# --------------------------------------------------------------------------- #
# Plan checkbox: feature-only rebase archive attribution
# [class: REPOSITORY_TEST]
# --------------------------------------------------------------------------- #
def _seed_start_commit_manifest(root: Path, start_commit: str) -> Path:
    """Seed the active run manifest with an explicit start_commit."""
    marker = make_marker(root, time.time(), os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start_commit
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _feature_start_commit(root: Path, note: str = "feature run start") -> str:
    """Commit a tracked non-docs marker file on the current branch and
    return the new HEAD sha (the run's feature-only start commit)."""
    (root / "RUNNOTES.md").write_text(note + "\n", encoding="utf-8")
    git(root, "add", "RUNNOTES.md")
    assert git(root, "commit", "-m", note, "-q").returncode == 0
    return git(root, "rev-parse", "HEAD").stdout.strip()


def _fail_git_calls(ctx, needles):
    """Return the ctx with a git method reporting rc 128 for matching
    leading-argument tuples, delegating everything else."""
    real_git = ctx.git

    def flaky(*args, **kwargs):
        for needle in needles:
            if tuple(args[: len(needle)]) == tuple(needle):
                return subprocess.CompletedProcess(args, 128, "", "injected failure")
        return real_git(*args, **kwargs)

    ctx.git = flaky
    return ctx


def test_archive_ceremony_feature_only_rebase_filters_upstream_archives(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A feature-only rebased start keeps the
    manifest boundary and filters raw paths against the configured-base
    snapshot: an upstream archive identical at snapshot and HEAD is
    excluded while the run's own archive stays checked (the upstream plan
    carries no exec-review record, so a filtering regression would flip
    the finding to it)."""
    root = make_repo(tmp_path, "ceremony-feature-only-rebase", gitignore_docs=True)
    write_facts(root)
    live_plan = "docs/history/plans/2026-10-05-feature-only.md"
    (root / "docs/history/plans").mkdir(parents=True, exist_ok=True)
    (root / live_plan).write_text(
        "# Plan: feature only\n\n- [ ] run task\n", encoding="utf-8"
    )
    git(root, "add", "-f", live_plan)
    assert git(root, "commit", "-m", "create live plan", "-q").returncode == 0
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "main")
    upstream_archive = _committed_plan_archive(
        root,
        "2026-10-04-feature-only-upstream.md",
        "# Plan: upstream\n\n- [x] done\n",
    )
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    run_archive = "docs/history/plans/completed/2026-10-05-feature-only.md"
    assert git(root, "mv", live_plan, run_archive).returncode == 0
    assert git(root, "commit", "-m", "archive feature plan", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-05-feature-only.md")
    _seed_start_commit_manifest(root, feature_start)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert run_archive in result.message
    assert "1 unchecked task box(es)" in result.message
    assert upstream_archive not in result.message

    (root / run_archive).write_text(
        "# Plan: feature only\n\n- [x] run task\n", encoding="utf-8"
    )
    git(root, "add", "-f", run_archive)
    assert git(root, "commit", "--amend", "-m", "archive feature plan", "-q").returncode == 0

    passed = run_gate("archive-ceremony", ctx_for(root))

    assert passed.rc == 0, passed.message
    assert run_archive in passed.message
    assert upstream_archive not in passed.message
    warnings = " ".join(passed.warnings)
    assert "feature-only run start" in warnings
    assert "configured-base snapshot" in warnings


def test_archive_ceremony_feature_only_collision_content_and_mode_retained(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Changed-content and mode-only collisions
    with the configured-base snapshot stay checked; only the matching
    presence-content-mode triple is excluded."""
    root = make_repo(tmp_path, "ceremony-feature-only-collide", gitignore_docs=True)
    write_facts(root)
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "main")
    archive_rel = _committed_plan_archive(
        root, "2026-10-04-collide.md", "# Plan: collide\n\n- [x] done\n"
    )
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    # Changed content in the run range: the M row must survive filtering.
    (root / archive_rel).write_text(
        "# Plan: collide\n\n- [x] done\n\n## Amended by the run\n",
        encoding="utf-8",
    )
    git(root, "add", "-f", archive_rel)
    assert git(root, "commit", "-m", "amend archive content", "-q").returncode == 0
    _seed_start_commit_manifest(root, feature_start)

    changed = run_gate("archive-ceremony", ctx_for(root))

    assert changed.rc == 1, changed.message
    assert archive_rel in changed.message

    # Mode-only collision on a fresh geometry: same blob, mode differs.
    root2 = make_repo(tmp_path, "ceremony-feature-only-mode", gitignore_docs=True)
    write_facts(root2)
    git(root2, "checkout", "-b", "feature")
    feature_start2 = _feature_start_commit(root2)
    git(root2, "checkout", "main")
    archive2 = _committed_plan_archive(
        root2, "2026-10-04-mode-only.md", "# Plan: mode only\n\n- [x] done\n"
    )
    git(root2, "checkout", "feature")
    assert git(root2, "rebase", "main").returncode == 0
    os.chmod(root2 / archive2, 0o755)
    git(root2, "add", "-f", archive2)
    assert git(root2, "commit", "-m", "flip archive mode", "-q").returncode == 0
    _seed_start_commit_manifest(root2, feature_start2)

    mode_only = run_gate("archive-ceremony", ctx_for(root2))

    assert mode_only.rc == 1, mode_only.message
    assert archive2 in mode_only.message

    # Identical collision: the upstream archive is added after the fork, so
    # the two-dot A row matches the snapshot on presence, content, and mode
    # and is excluded without any run-side commit.
    root3 = make_repo(tmp_path, "ceremony-feature-only-identical", gitignore_docs=True)
    write_facts(root3)
    git(root3, "checkout", "-b", "feature")
    feature_start3 = _feature_start_commit(root3)
    git(root3, "checkout", "main")
    body3 = "# Plan: identical\n\n- [x] done\n"
    archive3 = _committed_plan_archive(root3, "2026-10-04-identical.md", body3)
    git(root3, "checkout", "feature")
    assert git(root3, "rebase", "main").returncode == 0
    _seed_start_commit_manifest(root3, feature_start3)

    identical = run_gate("archive-ceremony", ctx_for(root3))

    assert identical.rc == 0, identical.message
    assert archive3 not in identical.message


def test_archive_ceremony_feature_only_member_rows_map_through_parent_charter(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Added and changed member rows under an
    unchanged charter map to the parent charter at HEAD and keep it
    checked."""
    root = make_repo(tmp_path, "ceremony-feature-only-members", gitignore_docs=True)
    write_facts(root)
    slug = "2026-10-04-feature-members"
    plan_dir = root / "docs/history/plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: members\n\n- [x] charter\n", encoding="utf-8"
    )
    (plan_dir / "tasks/01-a.md").write_text(
        "### Task 1\n\n- [x] a\n", encoding="utf-8"
    )
    git(root, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01-a.md")
    assert git(root, "commit", "-m", "create directory plan", "-q").returncode == 0
    (root / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    archive_dir = root / "docs/history/plans/completed" / slug
    git(root, "mv", f"docs/history/plans/{slug}",
        str(archive_dir.relative_to(root)))
    assert git(root, "commit", "-m", "archive directory plan", "-q").returncode == 0
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    # Add a member with an unchecked box and change an existing member's
    # content: both raw rows map to the unchanged charter at HEAD.
    charter_rel = f"docs/history/plans/completed/{slug}/PLAN.md"
    (archive_dir / "tasks/02-added.md").write_text(
        "### Task 2\n\n- [ ] added\n", encoding="utf-8"
    )
    (archive_dir / "tasks/01-a.md").write_text(
        "### Task 1\n\n- [x] a amended\n", encoding="utf-8"
    )
    git(root, "add", "-f", f"docs/history/plans/completed/{slug}/tasks/02-added.md",
        f"docs/history/plans/completed/{slug}/tasks/01-a.md")
    assert git(root, "commit", "-m", "run member work", "-q").returncode == 0
    _seed_start_commit_manifest(root, feature_start)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert charter_rel in result.message
    assert "1 unchecked task box(es)" in result.message

    # Mode-only member change also keeps the charter checked.
    root2 = make_repo(tmp_path, "ceremony-feature-only-member-mode", gitignore_docs=True)
    write_facts(root2)
    slug2 = "2026-10-04-member-mode"
    plan_dir2 = root2 / "docs/history/plans" / slug2
    (plan_dir2 / "tasks").mkdir(parents=True)
    (plan_dir2 / "PLAN.md").write_text(
        "# Plan: member mode\n\n- [x] charter\n", encoding="utf-8"
    )
    (plan_dir2 / "tasks/01.md").write_text("### Task 1\n\n- [x] one\n", encoding="utf-8")
    git(root2, "add", "-f", f"docs/history/plans/{slug2}/PLAN.md",
        f"docs/history/plans/{slug2}/tasks/01.md")
    assert git(root2, "commit", "-m", "create directory plan", "-q").returncode == 0
    (root2 / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    archive_dir2 = root2 / "docs/history/plans/completed" / slug2
    git(root2, "mv", f"docs/history/plans/{slug2}",
        str(archive_dir2.relative_to(root2)))
    assert git(root2, "commit", "-m", "archive directory plan", "-q").returncode == 0
    git(root2, "checkout", "-b", "feature")
    feature_start2 = _feature_start_commit(root2)
    git(root2, "checkout", "feature")
    assert git(root2, "rebase", "main").returncode == 0
    os.chmod(archive_dir2 / "tasks/01.md", 0o755)
    git(root2, "add", "-f", f"docs/history/plans/completed/{slug2}/tasks/01.md")
    assert git(root2, "commit", "-m", "flip member mode", "-q").returncode == 0
    _write_exec_review_record(root2, slug2)
    _seed_start_commit_manifest(root2, feature_start2)

    mode_only = run_gate("archive-ceremony", ctx_for(root2))

    charter_rel2 = f"docs/history/plans/completed/{slug2}/PLAN.md"
    assert mode_only.rc == 0, mode_only.message
    assert charter_rel2 in mode_only.message


def test_archive_ceremony_feature_only_source_only_member_deletion(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Base A+B, start A, HEAD B: the D(A) row
    checks the surviving shared charter and the unchanged B addition is
    excluded, so exactly the charter unit surfaces."""
    root = make_repo(tmp_path, "ceremony-feature-only-src-del", gitignore_docs=True)
    write_facts(root)
    slug = "2026-10-04-src-del"
    plan_dir = root / "docs/history/plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: src del\n\n- [x] charter\n", encoding="utf-8"
    )
    (plan_dir / "tasks/01-a.md").write_text("### Task 1\n\n- [x] a\n", encoding="utf-8")
    git(root, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01-a.md")
    assert git(root, "commit", "-m", "create directory plan", "-q").returncode == 0
    (root / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    archive_dir = root / "docs/history/plans/completed" / slug
    git(root, "mv", f"docs/history/plans/{slug}",
        str(archive_dir.relative_to(root)))
    assert git(root, "commit", "-m", "archive directory plan", "-q").returncode == 0
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    # Upstream adds member B under the archived charter after the fork.
    git(root, "checkout", "main")
    (archive_dir / "tasks/02-b.md").write_text(
        "### Task 2\n\n- [x] b\n", encoding="utf-8"
    )
    git(root, "add", "-f", f"docs/history/plans/completed/{slug}/tasks/02-b.md")
    assert git(root, "commit", "-m", "upstream adds member b", "-q").returncode == 0
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    # The run deletes member A only; the charter and B survive at HEAD.
    git(root, "rm", "-q", f"docs/history/plans/completed/{slug}/tasks/01-a.md")
    assert git(root, "commit", "-m", "run deletes member a", "-q").returncode == 0
    _write_exec_review_record(root, slug)
    _seed_start_commit_manifest(root, feature_start)

    archives, notes, blockers = lib._derive_archived_plans(ctx_for(root))

    charter_rel = f"docs/history/plans/completed/{slug}/PLAN.md"
    assert blockers == [], blockers
    assert [row[0] for row in archives] == [charter_rel]

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 0, result.message
    assert charter_rel in result.message


def test_archive_ceremony_feature_only_move_rows_reach_base_comparison(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Same-charter and heavily rewritten
    cross-charter moves surface their D and A rows independently of Git
    similarity pairing and map both endpoints to their checked charters."""
    root = make_repo(tmp_path, "ceremony-feature-only-same-move", gitignore_docs=True)
    write_facts(root)
    slug = "2026-10-04-same-move"
    plan_dir = root / "docs/history/plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: same move\n\n- [x] charter\n", encoding="utf-8"
    )
    (plan_dir / "tasks/01.md").write_text("### Task 1\n\n- [x] one\n", encoding="utf-8")
    git(root, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01.md")
    assert git(root, "commit", "-m", "create directory plan", "-q").returncode == 0
    (root / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    archive_dir = root / "docs/history/plans/completed" / slug
    git(root, "mv", f"docs/history/plans/{slug}",
        str(archive_dir.relative_to(root)))
    assert git(root, "commit", "-m", "archive directory plan", "-q").returncode == 0
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    git(root, "mv", f"docs/history/plans/completed/{slug}/tasks/01.md",
        f"docs/history/plans/completed/{slug}/tasks/01-renamed.md")
    assert git(root, "commit", "-m", "same-charter member move", "-q").returncode == 0
    _write_exec_review_record(root, slug)
    _seed_start_commit_manifest(root, feature_start)

    archives, notes, blockers = lib._derive_archived_plans(ctx_for(root))

    charter_rel = f"docs/history/plans/completed/{slug}/PLAN.md"
    assert blockers == [], blockers
    assert [row[0] for row in archives] == [charter_rel]

    # Cross-charter move with a heavy rewrite: both charters stay checked.
    root2 = make_repo(tmp_path, "ceremony-feature-only-cross-move", gitignore_docs=True)
    write_facts(root2)
    slug_a = "2026-10-04-cross-a"
    slug_b = "2026-10-04-cross-b"
    for cross_slug, body in (
        (slug_a, "# Plan: cross a\n\n- [x] charter\n"),
        (slug_b, "# Plan: cross b\n\n- [x] charter\n"),
    ):
        cross_dir = root2 / "docs/history/plans" / cross_slug
        (cross_dir / "tasks").mkdir(parents=True)
        (cross_dir / "PLAN.md").write_text(body, encoding="utf-8")
        (cross_dir / "tasks/01.md").write_text(
            "### Task 1\n\n- [x] one\n", encoding="utf-8"
        )
        git(root2, "add", "-f", f"docs/history/plans/{cross_slug}/PLAN.md",
            f"docs/history/plans/{cross_slug}/tasks/01.md")
    assert git(root2, "commit", "-m", "create cross plans", "-q").returncode == 0
    (root2 / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    for cross_slug in (slug_a, slug_b):
        cross_archive = root2 / "docs/history/plans/completed" / cross_slug
        git(root2, "mv", f"docs/history/plans/{cross_slug}",
            str(cross_archive.relative_to(root2)))
    assert git(root2, "commit", "-m", "archive cross plans", "-q").returncode == 0
    git(root2, "checkout", "-b", "feature")
    feature_start2 = _feature_start_commit(root2)
    git(root2, "checkout", "feature")
    assert git(root2, "rebase", "main").returncode == 0
    git(root2, "mv",
        f"docs/history/plans/completed/{slug_a}/tasks/01.md",
        f"docs/history/plans/completed/{slug_b}/tasks/01-moved.md")
    moved = root2 / "docs/history/plans/completed" / slug_b / "tasks/01-moved.md"
    moved.write_text(
        "### Task 1 (fully rewritten by the run)\n\n"
        "- [x] one; the body now carries an entirely different shape,\n"
        "so similarity pairing could never pair these endpoints.\n",
        encoding="utf-8",
    )
    git(root2, "add", "-f",
        f"docs/history/plans/completed/{slug_b}/tasks/01-moved.md")
    assert git(root2, "commit", "-m", "cross-charter member move", "-q").returncode == 0
    _write_exec_review_record(root2, slug_a)
    _write_exec_review_record(root2, slug_b)
    _seed_start_commit_manifest(root2, feature_start2)

    archives2, _notes2, blockers2 = lib._derive_archived_plans(ctx_for(root2))

    assert blockers2 == [], blockers2
    assert sorted(row[0] for row in archives2) == [
        f"docs/history/plans/completed/{slug_a}/PLAN.md",
        f"docs/history/plans/completed/{slug_b}/PLAN.md",
    ]


def test_archive_ceremony_feature_only_state_transitions_and_skips(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Whole-charter deferred-to-completed and
    completed-to-rejected moves skip the vanished source and classify the
    destination by HEAD state (the rejected exemption intact); whole-charter
    deletion skips member D rows only after HEAD confirms the parent
    absent."""
    root = make_repo(tmp_path, "ceremony-feature-only-transitions", gitignore_docs=True)
    write_facts(root)
    # Upstream archives foo under deferred/ and bar under completed/.
    deferred_dir = root / "docs/history/plans/deferred"
    deferred_dir.mkdir(parents=True, exist_ok=True)
    foo_rel = "docs/history/plans/deferred/2026-10-04-foo.md"
    (deferred_dir / "2026-10-04-foo.md").write_text(
        "# Plan: foo\n\n- [x] done\n", encoding="utf-8"
    )
    git(root, "add", "-f", foo_rel)
    assert git(root, "commit", "-m", "seed deferred plan", "-q").returncode == 0
    bar_archive = _committed_plan_archive(
        root, "2026-10-04-bar.md", "# Plan: bar\n\n- [x] done\n"
    )
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "main")
    assert git(root, "commit", "--allow-empty", "-m", "main advances", "-q").returncode == 0
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    completed_rel = "docs/history/plans/completed/2026-10-04-foo.md"
    rejected_rel = "docs/history/plans/rejected/2026-10-04-bar.md"
    (root / "docs/history/plans/rejected").mkdir(parents=True, exist_ok=True)
    git(root, "mv", foo_rel, completed_rel)
    git(root, "mv", bar_archive, rejected_rel)
    assert git(root, "commit", "-m", "transition archived plans", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-04-foo.md")
    _seed_start_commit_manifest(root, feature_start)

    archives, notes, blockers = lib._derive_archived_plans(ctx_for(root))

    assert blockers == [], blockers
    assert sorted(row[0] for row in archives) == [
        completed_rel,
        "docs/history/plans/rejected/2026-10-04-bar.md",
    ]

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 0, result.message
    assert completed_rel in result.message
    assert foo_rel not in result.message
    assert bar_archive not in result.message
    assert "rejected-state archive(s) exempt" in result.message

    # Whole-charter deletion: the D member row is skipped only after HEAD
    # confirms the parent charter absent.
    root2 = make_repo(tmp_path, "ceremony-feature-only-charter-del", gitignore_docs=True)
    write_facts(root2)
    slug = "2026-10-04-charter-del"
    plan_dir = root2 / "docs/history/plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: charter del\n\n- [x] charter\n", encoding="utf-8"
    )
    (plan_dir / "tasks/01.md").write_text("### Task 1\n\n- [x] one\n", encoding="utf-8")
    git(root2, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01.md")
    assert git(root2, "commit", "-m", "create directory plan", "-q").returncode == 0
    (root2 / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    archive_dir = root2 / "docs/history/plans/completed" / slug
    git(root2, "mv", f"docs/history/plans/{slug}",
        str(archive_dir.relative_to(root2)))
    assert git(root2, "commit", "-m", "archive directory plan", "-q").returncode == 0
    git(root2, "checkout", "-b", "feature")
    feature_start2 = _feature_start_commit(root2)
    git(root2, "checkout", "feature")
    assert git(root2, "rebase", "main").returncode == 0
    git(root2, "rm", "-rq", f"docs/history/plans/completed/{slug}")
    assert git(root2, "commit", "-m", "run removes whole archive", "-q").returncode == 0
    _seed_start_commit_manifest(root2, feature_start2)

    archives2, notes2, blockers2 = lib._derive_archived_plans(ctx_for(root2))

    assert archives2 == [], archives2
    assert blockers2 == [], blockers2


def test_archive_ceremony_feature_only_bare_file_rows(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Bare-file A/M/D rows map directly: changed
    and added files stay checked, and an absent D is skipped only after a
    successful HEAD lookup."""
    root = make_repo(tmp_path, "ceremony-feature-only-bare", gitignore_docs=True)
    write_facts(root)
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "main")
    archive_m = _committed_plan_archive(
        root, "2026-10-04-bare-m.md", "# Plan: bare m\n\n- [x] done\n"
    )
    archive_d = _committed_plan_archive(
        root, "2026-10-04-bare-d.md", "# Plan: bare d\n\n- [x] done\n"
    )
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    (root / archive_m).write_text(
        "# Plan: bare m\n\n- [ ] run-amended box\n", encoding="utf-8"
    )
    git(root, "add", "-f", archive_m)
    added = "docs/history/plans/completed/2026-10-04-bare-added.md"
    (root / added).write_text("# Plan: bare added\n\n- [x] done\n", encoding="utf-8")
    git(root, "add", "-f", added)
    git(root, "rm", "-q", archive_d)
    assert git(root, "commit", "-m", "run bare-file work", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-04-bare-added.md")
    _seed_start_commit_manifest(root, feature_start)

    archives, notes, blockers = lib._derive_archived_plans(ctx_for(root))

    assert blockers == [], blockers
    assert sorted(row[0] for row in archives) == sorted([added, archive_m])

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert archive_m in result.message
    assert archive_d not in result.message


def test_archive_ceremony_feature_only_missing_or_nonregular_charter_blocks(
    tmp_path, sweep_env, monkeypatch
):
    """[class: REPOSITORY_TEST] A member row whose parent charter is absent
    or non-regular at HEAD stays checked as an explicit blocker, and an
    injected parent HEAD lookup error retains the failure explicitly."""
    root = make_repo(tmp_path, "ceremony-feature-only-orphan", gitignore_docs=True)
    write_facts(root)
    slug = "2026-10-04-orphan"
    plan_dir = root / "docs/history/plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: orphan\n\n- [x] charter\n", encoding="utf-8"
    )
    (plan_dir / "tasks/01.md").write_text("### Task 1\n\n- [x] one\n", encoding="utf-8")
    git(root, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01.md")
    assert git(root, "commit", "-m", "create directory plan", "-q").returncode == 0
    (root / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    archive_dir = root / "docs/history/plans/completed" / slug
    git(root, "mv", f"docs/history/plans/{slug}",
        str(archive_dir.relative_to(root)))
    assert git(root, "commit", "-m", "archive directory plan", "-q").returncode == 0
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    # The run adds a member and deletes the parent charter: the member's A
    # row finds no charter at HEAD and must block explicitly.
    charter_rel = f"docs/history/plans/completed/{slug}/PLAN.md"
    (archive_dir / "tasks/02-orphan.md").write_text(
        "### Task 2\n\n- [x] orphan\n", encoding="utf-8"
    )
    git(root, "add", "-f", f"docs/history/plans/completed/{slug}/tasks/02-orphan.md")
    git(root, "rm", "-q", charter_rel)
    assert git(root, "commit", "-m", "orphan the member", "-q").returncode == 0
    _seed_start_commit_manifest(root, feature_start)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert charter_rel in result.message
    assert "not a regular file at HEAD" in result.message or (
        "missing or ambiguous at HEAD" in result.message
    ), result.message

    # Injected parent HEAD lookup error: the blocker carries the failure.
    real_probe = lib._head_regular_archive_file

    def failing_probe(ctx, rel):
        if rel == charter_rel:
            return f"injected HEAD lookup failure: {rel}"
        return real_probe(ctx, rel)

    monkeypatch.setattr(lib, "_head_regular_archive_file", failing_probe)
    injected = run_gate("archive-ceremony", ctx_for(root))

    assert injected.rc == 1, injected.message
    assert "injected HEAD lookup failure" in injected.message

    # Non-regular direct-file and charter A rows block the same way.
    root2 = make_repo(tmp_path, "ceremony-feature-only-symlink", gitignore_docs=True)
    write_facts(root2)
    git(root2, "checkout", "-b", "feature")
    feature_start2 = _feature_start_commit(root2)
    git(root2, "checkout", "main")
    file_archive = _committed_plan_archive(
        root2, "2026-10-04-link.md", "# Plan: link\n\n- [x] done\n"
    )
    slug_c = "2026-10-04-link-charter"
    plan_dir_c = root2 / "docs/history/plans" / slug_c
    (plan_dir_c / "tasks").mkdir(parents=True)
    (plan_dir_c / "PLAN.md").write_text(
        "# Plan: link charter\n\n- [x] charter\n", encoding="utf-8"
    )
    (plan_dir_c / "tasks/01.md").write_text(
        "### Task 1\n\n- [x] one\n", encoding="utf-8"
    )
    git(root2, "add", "-f", f"docs/history/plans/{slug_c}/PLAN.md",
        f"docs/history/plans/{slug_c}/tasks/01.md")
    assert git(root2, "commit", "-m", "create link charter plan", "-q").returncode == 0
    (root2 / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    archive_dir_c = root2 / "docs/history/plans/completed" / slug_c
    git(root2, "mv", f"docs/history/plans/{slug_c}",
        str(archive_dir_c.relative_to(root2)))
    assert git(root2, "commit", "-m", "archive link charter plan", "-q").returncode == 0
    git(root2, "checkout", "feature")
    assert git(root2, "rebase", "main").returncode == 0
    charter_c = f"docs/history/plans/completed/{slug_c}/PLAN.md"
    git(root2, "rm", "-q", file_archive)
    os.symlink("../elsewhere.md", root2 / file_archive)
    git(root2, "add", "-f", file_archive)
    git(root2, "rm", "-q", charter_c)
    os.symlink("../elsewhere.md", root2 / charter_c)
    git(root2, "add", "-f", charter_c)
    assert git(root2, "commit", "-m", "replace archives with symlinks", "-q").returncode == 0
    _seed_start_commit_manifest(root2, feature_start2)

    symlinked = run_gate("archive-ceremony", ctx_for(root2))

    assert symlinked.rc == 1, symlinked.message
    assert file_archive in symlinked.message
    assert charter_c in symlinked.message
    assert "not a regular file at HEAD" in symlinked.message


def test_archive_ceremony_feature_only_error_arms_keep_candidates(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] Configured-base branch lookup, merge-base
    lookup, and ancestry-check failures never activate snapshot filtering:
    the upstream archive candidate stays checked."""

    def build(name):
        root = make_repo(tmp_path, name, gitignore_docs=True)
        write_facts(root)
        live_plan = "docs/history/plans/2026-10-05-err.md"
        (root / "docs/history/plans").mkdir(parents=True, exist_ok=True)
        (root / live_plan).write_text(
            "# Plan: err\n\n- [x] done\n", encoding="utf-8"
        )
        git(root, "add", "-f", live_plan)
        assert git(root, "commit", "-m", "create live plan", "-q").returncode == 0
        git(root, "checkout", "-b", "feature")
        feature_start = _feature_start_commit(root)
        git(root, "checkout", "main")
        upstream = _committed_plan_archive(
            root, "2026-10-04-err-upstream.md", "# Plan: err upstream\n\n- [ ] open\n"
        )
        git(root, "checkout", "feature")
        assert git(root, "rebase", "main").returncode == 0
        _seed_start_commit_manifest(root, feature_start)
        return root, upstream

    # Configured-base branch lookup fails: no filtering, candidate checked.
    root, upstream = build("ceremony-err-branch-lookup")
    ctx = ctx_for(root)
    _fail_git_calls(ctx, [("branch", "--show-current")])
    branch_err = run_gate("archive-ceremony", ctx)
    branch_notes = lib._derive_archived_plans(ctx)[1]

    assert branch_err.rc == 1, branch_err.message
    assert upstream in branch_err.message
    assert all("feature-only run start" not in n for n in branch_notes)

    # Merge-base lookup fails: same conservative outcome.
    root2, upstream2 = build("ceremony-err-merge-base")
    ctx2 = ctx_for(root2)
    _fail_git_calls(ctx2, [("merge-base", "HEAD")])
    merge_err = run_gate("archive-ceremony", ctx2)
    merge_notes = lib._derive_archived_plans(ctx2)[1]

    assert merge_err.rc == 1, merge_err.message
    assert upstream2 in merge_err.message
    assert all("feature-only run start" not in n for n in merge_notes)

    # Ancestry command error (not the successful result 1): no filtering,
    # and the failure is noted.
    root3, upstream3 = build("ceremony-err-ancestry")
    ctx3 = ctx_for(root3)
    _fail_git_calls(ctx3, [("merge-base", "--is-ancestor")])
    ancestry_err = run_gate("archive-ceremony", ctx3)
    ancestry_notes = lib._derive_archived_plans(ctx3)[1]

    assert ancestry_err.rc == 1, ancestry_err.message
    assert upstream3 in ancestry_err.message
    assert any("ancestry check failed" in n for n in ancestry_notes)
    assert all("feature-only run start" not in n for n in ancestry_notes)


def test_archive_ceremony_feature_only_snapshot_lookup_errors_retain(
    tmp_path, sweep_env, monkeypatch
):
    """[class: REPOSITORY_TEST] A configured-base snapshot lookup failure on
    the feature-only path retains the candidate as an explicit blocker and
    never silently skips it."""
    root = make_repo(tmp_path, "ceremony-feature-only-snap-err", gitignore_docs=True)
    write_facts(root)
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "main")
    archive_rel = _committed_plan_archive(
        root, "2026-10-04-snap-err.md", "# Plan: snap err\n\n- [x] done\n"
    )
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    (root / archive_rel).write_text(
        "# Plan: snap err\n\n- [x] done\n\n## amended\n", encoding="utf-8"
    )
    git(root, "add", "-f", archive_rel)
    assert git(root, "commit", "-m", "amend archive", "-q").returncode == 0
    _seed_start_commit_manifest(root, feature_start)

    real_state = lib._commit_path_state

    def failing_state(ctx, commit, rel):
        if commit != "HEAD" and rel == archive_rel:
            return None, None, None, "injected snapshot lookup failure"
        return real_state(ctx, commit, rel)

    monkeypatch.setattr(lib, "_commit_path_state", failing_state)
    archives, notes, blockers = lib._derive_archived_plans(ctx_for(root))

    assert any("injected snapshot lookup failure" in b for b in blockers), blockers
    assert [row[0] for row in archives] == [archive_rel]


def test_archive_ceremony_configured_base_branch_keeps_start_boundary(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] A run on the configured base branch keeps
    the manifest start boundary: an archive created after the manifest
    start remains checked."""
    root = make_repo(tmp_path, "ceremony-configured-base", gitignore_docs=True)
    write_facts(root)
    live_plan = "docs/history/plans/2026-10-05-onbase.md"
    (root / "docs/history/plans").mkdir(parents=True, exist_ok=True)
    (root / live_plan).write_text("# Plan: onbase\n\n- [ ] task\n", encoding="utf-8")
    git(root, "add", "-f", live_plan)
    assert git(root, "commit", "-m", "create live plan", "-q").returncode == 0
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    run_archive = "docs/history/plans/completed/2026-10-05-onbase.md"
    (root / "docs/history/plans/completed").mkdir(parents=True, exist_ok=True)
    (root / live_plan).write_text("# Plan: onbase\n\n- [x] task\n", encoding="utf-8")
    git(root, "add", "-f", live_plan)
    git(root, "mv", live_plan, run_archive)
    assert git(root, "commit", "-m", "archive onbase plan", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-05-onbase.md")
    _seed_start_commit_manifest(root, start)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 0, result.message
    assert run_archive in result.message
    assert "feature-only run start" not in " ".join(result.warnings)
    assert "using worktree base-branch merge base" not in " ".join(result.warnings)


def test_archive_ceremony_feature_only_preserves_stale_deliverables_and_staged(
    tmp_path, sweep_env
):
    """[class: REPOSITORY_TEST] The feature-only derivation leaves the
    stale plan-deliverables shape untouched: a stale deliverables entry for
    a plan now archived still surfaces its twin."""
    root = make_repo(tmp_path, "ceremony-feature-only-shapes", gitignore_docs=True)
    write_facts(root)
    plan_name = "2026-10-04-stale-shapes.md"
    stale_rel = f"docs/history/plans/{plan_name}"
    body = "# Plan: stale shapes\n\n- [ ] one\n"
    twin_rel = _committed_plan_archive(root, plan_name, body)
    git(root, "checkout", "-b", "feature")
    feature_start = _feature_start_commit(root)
    git(root, "checkout", "main")
    assert git(root, "commit", "--allow-empty", "-m", "main advances", "-q").returncode == 0
    git(root, "checkout", "feature")
    assert git(root, "rebase", "main").returncode == 0
    assert not (root / stale_rel).exists()
    write_deliverables(root, [stale_rel])
    _seed_start_commit_manifest(root, feature_start)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert twin_rel in result.message
    assert "1 unchecked task box(es)" in result.message


def test_archive_ceremony_checks_added_member_of_existing_directory_archive(
    tmp_path, sweep_env, monkeypatch
):
    """An added task file has no changed charter row to carry its checkboxes."""
    root = make_repo(tmp_path, "ceremony-added-archive-member", gitignore_docs=True)
    write_facts(root)
    slug = "2026-10-03-member-plan"
    plan_dir = root / "docs/history/plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: member\n\n- [x] charter task\n", encoding="utf-8"
    )
    (plan_dir / "tasks/01-existing.md").write_text(
        "### Task 1\n\n- [x] existing task\n", encoding="utf-8"
    )
    git(
        root, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01-existing.md",
    )
    assert git(root, "commit", "-m", "create directory plan", "-q").returncode == 0
    archive_dir = root / "docs/history/plans/completed" / slug
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    assert git(root, "mv", f"docs/history/plans/{slug}", str(archive_dir.relative_to(root))).returncode == 0
    assert git(root, "commit", "-m", "archive directory plan", "-q").returncode == 0
    start = git(root, "rev-parse", "HEAD").stdout.strip()

    new_member = archive_dir / "tasks/02-added.md"
    new_member.write_text("### Task 2\n\n- [ ] added task\n", encoding="utf-8")
    assert git(root, "add", "-f", str(new_member.relative_to(root))).returncode == 0
    assert git(root, "commit", "-m", "add archive member", "-q").returncode == 0
    marker = make_marker(root, time.time(), os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_exec_review_record(root, slug)

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert str((archive_dir / "PLAN.md").relative_to(root)) in result.message
    assert "1 unchecked task box(es)" in result.message

    new_member.write_text("### Task 2\n\n- [x] added task\n", encoding="utf-8")
    assert git(root, "add", "-f", str(new_member.relative_to(root))).returncode == 0
    assert git(root, "commit", "--amend", "-m", "add archive member", "-q").returncode == 0

    checked = run_gate("archive-ceremony", ctx_for(root))

    assert checked.rc == 0, checked.message
    assert str((archive_dir / "PLAN.md").relative_to(root)) in checked.message

    disappearing_member = archive_dir / "tasks/03-disappearing.md"
    disappearing_member.write_text(
        "### Task 3\n\n- [ ] staged but missing from worktree\n", encoding="utf-8"
    )
    assert git(root, "add", "-f", str(disappearing_member.relative_to(root))).returncode == 0
    real_mismatch = lib._worktree_index_mismatch

    def delete_after_comparison(ctx, rel):
        result = real_mismatch(ctx, rel)
        if rel == str(disappearing_member.relative_to(root)):
            disappearing_member.unlink(missing_ok=True)
            return None
        return result

    monkeypatch.setattr(lib, "_worktree_index_mismatch", delete_after_comparison)
    disappeared = run_gate("archive-ceremony", ctx_for(root))
    assert disappeared.rc == 1, disappeared.message
    assert "1 unchecked task box(es)" in disappeared.message
    assert str((archive_dir / "PLAN.md").relative_to(root)) in disappeared.message

    for failure_kind in ("ls-tree", "task-show", "status", "ls-files"):
        ctx = ctx_for(root)
        real_git = ctx.git

        def fail_task_read(*args, input_text=None):
            should_fail = (
                (
                    args[0] == failure_kind
                    if failure_kind in {"ls-tree", "status"}
                    else args[0] == "ls-files"
                    and args[-1].endswith("/tasks")
                )
                if failure_kind in {"ls-tree", "status", "ls-files"}
                else args[0] == "show" and len(args) > 1 and "/tasks/" in args[1]
            )
            if should_fail:
                return subprocess.CompletedProcess(
                    args, 128 if failure_kind == "ls-files" else 1,
                    "", "simulated read failure"
                )
            return real_git(*args, input_text=input_text)

        ctx.git = fail_task_read
        unreadable = run_gate("archive-ceremony", ctx)
        assert unreadable.rc == 1, unreadable.message
        assert "archive-ceremony gate failed" in unreadable.message


def test_archive_ceremony_does_not_skip_added_member_without_charter(
    tmp_path, sweep_env
):
    """An orphaned task member still contributes unchecked boxes to the gate."""
    root = make_repo(tmp_path, "ceremony-orphan-archive-member", gitignore_docs=True)
    write_facts(root)
    assert git(root, "commit", "--allow-empty", "-m", "run start", "-q").returncode == 0
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    member_rel = (
        "docs/history/plans/completed/2026-10-03-orphan-plan/tasks/01-orphan.md"
    )
    member = root / member_rel
    member.parent.mkdir(parents=True)
    member.write_text("### Task 1\n\n- [ ] orphan task\n", encoding="utf-8")
    assert git(root, "add", "-f", member_rel).returncode == 0
    assert git(root, "commit", "-m", "add orphan member", "-q").returncode == 0
    marker = make_marker(root, time.time(), os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "archive evidence missing or ambiguous at HEAD" in result.message

    ctx = ctx_for(root)
    real_git = ctx.git

    def fail_archive_reads(*args, input_text=None):
        if args[0] == "show" and len(args) > 1 and args[1].startswith("HEAD:"):
            return subprocess.CompletedProcess(args, 1, "", "simulated read failure")
        return real_git(*args, input_text=input_text)

    ctx.git = fail_archive_reads
    unreadable = run_gate("archive-ceremony", ctx)
    assert unreadable.rc == 1, unreadable.message
    assert "archive evidence missing or ambiguous at HEAD" in unreadable.message


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

    reviews = root / ".ai-playbook" / "reviews"
    reviews.mkdir(parents=True)
    (reviews / "2026-10-01-plan-review-ceremony-reviewed-exec-r1.md").write_text(
        "# Exec review r1\n\nVerdict: ready=yes, zero blocking.\n",
        encoding="utf-8",
    )

    result2 = run_gate("archive-ceremony", ctx_for(root))

    assert result2.rc == 0, result2.message
    assert archive_rel in result2.message


def test_done_twin_directory_archive(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] plan-directory-shape Task 2: the archive
    twin accepts a directory-shaped archived plan. The derivation surfaces
    the charter as the archive (member task-file rows never surface as
    separate archives), the checkbox leg spans the charter plus every task
    file, and the exec-review record leg keys on the directory slug."""
    root = make_repo(tmp_path, "ceremony-dir-twin", gitignore_docs=True)
    write_facts(root)
    _write_exec_review_record(root, "2026-09-30-ceremony-dir.md")
    slug = "2026-09-30-ceremony-dir"
    plan_dir = root / "docs" / "history" / "plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: dir demo\n\n- [x] charter box\n", encoding="utf-8"
    )
    (plan_dir / "tasks" / "01-a.md").write_text(
        "### Task 1\n\n- [ ] task box one\n", encoding="utf-8"
    )
    git(
        root, "add", "-f",
        f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01-a.md",
    )
    git(root, "commit", "-m", "plan", "-q")
    (root / "docs" / "history" / "plans" / "completed").mkdir(
        parents=True, exist_ok=True
    )
    archive_rel = f"docs/history/plans/completed/{slug}"
    assert git(root, "mv", f"docs/history/plans/{slug}",
               archive_rel).returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    # The unchecked box lives in the TASK file: the refusal naming the
    # charter archive path proves the checkbox leg spans the task files,
    # and exactly one archive (the charter) surfaced.
    assert result.rc == 1, result.message
    assert archive_rel + "/PLAN.md" in result.message
    assert "1 unchecked task box(es)" in result.message
    assert "tasks/01-a.md" not in result.message.split("gate failed:")[0]

    # Flipping the task box (working tree at the archived path) turns the
    # gate green with the directory archive still surfaced.
    (root / archive_rel / "tasks" / "01-a.md").write_text(
        "### Task 1\n\n- [x] task box one\n", encoding="utf-8"
    )
    git(root, "add", "-f", f"{archive_rel}/tasks/01-a.md")

    result2 = run_gate("archive-ceremony", ctx_for(root))

    assert result2.rc == 0, result2.message
    assert archive_rel + "/PLAN.md" in result2.message


def test_archive_ceremony_notes_missing_tasks_dir_on_staged_charter(tmp_path, sweep_env):
    """[class: REPOSITORY_TEST] execution-review r1 fold: a staged charter
    rename whose plan directory carries no tasks/ directory on disk surfaces
    the empty task span as a note on the same channel as the unreadable-file
    arm, never a silent empty task span (a task box left behind at the old
    path must not be skipped without a trace)."""
    root = make_repo(tmp_path, "ceremony-no-tasks-dir", gitignore_docs=True)
    write_facts(root)
    _write_exec_review_record(root, "2026-09-30-no-tasks-dir")
    slug = "2026-09-30-no-tasks-dir"
    plan_dir = root / "docs" / "history" / "plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: no tasks dir\n\n- [x] charter box\n", encoding="utf-8"
    )
    (plan_dir / "tasks" / "01-a.md").write_text(
        "### Task 1\n\n- [ ] task box one\n", encoding="utf-8"
    )
    git(
        root, "add", "-f",
        f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01-a.md",
    )
    git(root, "commit", "-m", "plan", "-q")
    archive_rel = f"docs/history/plans/completed/{slug}"
    (root / archive_rel).mkdir(parents=True)
    assert git(
        root, "mv", f"docs/history/plans/{slug}/PLAN.md", f"{archive_rel}/PLAN.md"
    ).returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    # The charter itself is box-complete and the exec-review record is
    # seeded, so the gate passes; the missing tasks/ directory surfaces as
    # the note (warnings channel when archives are non-empty).
    assert result.rc == 0, result.message
    assert any(
        "no tasks/ directory on disk" in note
        for note in [result.message] + list(result.warnings)
    ), (result.message, result.warnings)


def test_archive_ceremony_checks_staged_addition_in_completed_archive(
    tmp_path, sweep_env
):
    """A newly authored archive file is checked before its first commit."""
    root = make_repo(tmp_path, "ceremony-staged-archive-add", gitignore_docs=True)
    write_facts(root)
    _write_exec_review_record(root, "2026-10-03-staged-add")
    archive_rel = "docs/history/plans/completed/2026-10-03-staged-add.md"
    archive = root / archive_rel
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text("# Plan: staged add\n\n- [ ] task\n", encoding="utf-8")
    assert git(root, "add", "-f", archive_rel).returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert archive_rel in result.message
    assert "1 unchecked task box(es)" in result.message

    archive.write_text("# Plan: staged add\n\n- [x] task\n", encoding="utf-8")
    mismatched = run_gate("archive-ceremony", ctx_for(root))
    assert mismatched.rc == 1, mismatched.message
    assert "staged archive differs from worktree bytes" in mismatched.message


def test_archive_worktree_read_refuses_failed_post_read_index_lookup(
    tmp_path, sweep_env, monkeypatch
):
    """[class: REPOSITORY_TEST] Only exit 1 proves the path stayed untracked."""
    root = make_repo(tmp_path, "archive-post-read-index-error")
    ctx = ctx_for(root)
    rel = "docs/history/plans/completed/2026-10-10-plan.md"
    target = root / rel
    target.parent.mkdir(parents=True)
    target.write_text("# Plan\n", encoding="utf-8")
    real_git = ctx.git
    lookups = 0

    def fail_second_lookup(*args, **kwargs):
        nonlocal lookups
        if args[:2] == ("ls-files", "--error-unmatch"):
            lookups += 1
            if lookups == 1:
                return subprocess.CompletedProcess(list(args), 1, "", "")
            return subprocess.CompletedProcess(
                list(args), 128, "", "simulated index lookup failure"
            )
        return real_git(*args, **kwargs)

    monkeypatch.setattr(ctx, "git", fail_second_lookup)
    text, error = lib._archive_text_at_index_or_worktree(ctx, rel)

    assert text is None
    assert error == (
        "staged archive index lookup failed after worktree read: "
        f"{rel}: simulated index lookup failure"
    )
    assert lookups == 2


@pytest.mark.parametrize("source", ["index", "head"])
def test_archive_ceremony_refuses_directory_task_symlink(tmp_path, sweep_env, source):
    """A task symlink cannot hide unchecked task content from the gate."""
    root = make_repo(tmp_path, f"archive-task-symlink-{source}")
    write_facts(root)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    plan_dir = root / "docs/history/plans/completed/2026-10-10-linked-plan"
    tasks = plan_dir / "tasks"
    tasks.mkdir(parents=True)
    charter = plan_dir / "PLAN.md"
    charter.write_text("# Plan\n\n- [x] charter task\n", encoding="utf-8")
    link = tasks / "01-linked.md"
    hidden_target = root / "unchecked-task-target.md"
    hidden_target.write_text("### Task 1\n\n- [ ] hidden task\n", encoding="utf-8")
    link.symlink_to(hidden_target)
    assert git(root, "add", "-f", str(charter.relative_to(root)),
               str(link.relative_to(root))).returncode == 0
    if source == "head":
        assert git(root, "commit", "-m", "archive linked task", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-10-linked-plan")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "2026-10-10-linked-plan/tasks/01-linked.md" in result.message
    assert "not a regular file" in result.message


@pytest.mark.parametrize("source", ["index", "head"])
def test_archive_ceremony_refuses_symlink_tasks_directory(tmp_path, sweep_env, source):
    """A tasks/ symlink is rejected before enumeration can traverse it."""
    root = make_repo(tmp_path, f"archive-tasks-dir-symlink-{source}", gitignore_docs=True)
    write_facts(root)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    plan_dir = root / "docs/history/plans/completed/2026-10-10-linked-dir-plan"
    plan_dir.mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text("# Plan\n\n- [x] charter task\n", encoding="utf-8")
    external_tasks = root.parent / f"external-tasks-{source}"
    external_tasks.mkdir()
    (external_tasks / "01-hidden.md").write_text(
        "### Task 1\n\n- [ ] external unchecked task\n", encoding="utf-8"
    )
    (plan_dir / "tasks").symlink_to(external_tasks, target_is_directory=True)
    assert git(
        root, "add", "-f", "docs/history/plans/completed/2026-10-10-linked-dir-plan/PLAN.md",
        "docs/history/plans/completed/2026-10-10-linked-dir-plan/tasks",
    ).returncode == 0
    if source == "head":
        assert git(root, "commit", "-m", "archive tasks symlink", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-10-linked-dir-plan")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "tasks path is not" in result.message


def test_archive_ceremony_refuses_committed_regular_file_tasks_path(tmp_path, sweep_env):
    """A blob named tasks cannot stand in for the committed task directory."""
    root = make_repo(tmp_path, "archive-tasks-regular-file-head", gitignore_docs=True)
    write_facts(root)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    plan_dir = root / "docs/history/plans/completed/2026-10-10-file-tasks-plan"
    plan_dir.mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text("# Plan\n\n- [x] charter task\n", encoding="utf-8")
    (plan_dir / "tasks").write_text("no task directory\n", encoding="utf-8")
    assert git(root, "add", "-f", "docs/history/plans/completed/2026-10-10-file-tasks-plan/PLAN.md",
               "docs/history/plans/completed/2026-10-10-file-tasks-plan/tasks").returncode == 0
    assert git(root, "commit", "-m", "archive malformed tasks path", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-10-file-tasks-plan")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "tasks path is not a directory at HEAD" in result.message


def test_archive_ceremony_refuses_index_file_at_tasks_path(tmp_path, sweep_env):
    """Index mode is checked even when the worktree has repaired the path."""
    root = make_repo(tmp_path, "archive-tasks-index-regular-file", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    write_run_manifest_record(root, marker)
    plan_dir = root / "docs/history/plans/completed/2026-10-10-index-file-tasks-plan"
    plan_dir.mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text("# Plan\n\n- [x] charter task\n", encoding="utf-8")
    tasks_path = plan_dir / "tasks"
    tasks_path.write_text("malformed index entry\n", encoding="utf-8")
    assert git(root, "add", "-f", "docs/history/plans/completed/2026-10-10-index-file-tasks-plan/PLAN.md",
               "docs/history/plans/completed/2026-10-10-index-file-tasks-plan/tasks").returncode == 0
    tasks_path.unlink()
    tasks_path.mkdir()
    (tasks_path / "01-task.md").write_text("### Task 1\n\n- [x] task\n", encoding="utf-8")
    _write_exec_review_record(root, "2026-10-10-index-file-tasks-plan")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "tasks path is not a directory in index" in result.message


def test_archive_ceremony_refuses_committed_symlink_archive_file(tmp_path, sweep_env):
    """Committed archive files must be regular Markdown blobs in HEAD."""
    root = make_repo(tmp_path, "archive-file-symlink-head", gitignore_docs=True)
    write_facts(root)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    archive = root / "docs/history/plans/completed/2026-10-10-linked-file.md"
    archive.parent.mkdir(parents=True, exist_ok=True)
    target = root / "hidden-plan-target.md"
    target.write_text("# Plan\n\n- [ ] hidden task\n", encoding="utf-8")
    archive.symlink_to(target)
    assert git(root, "add", "-f", str(archive.relative_to(root))).returncode == 0
    assert git(root, "commit", "-m", "archive symlink", "-q").returncode == 0
    _write_exec_review_record(root, "2026-10-10-linked-file.md")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "not a regular file at HEAD" in result.message


def test_archive_ceremony_checks_committed_rejected_symlink(tmp_path, sweep_env):
    """Rejected archives keep structural checks even without staged status."""
    root = make_repo(tmp_path, "archive-rejected-symlink-head", gitignore_docs=True)
    write_facts(root)
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = start
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    archive = root / "docs/history/plans/rejected/2026-10-10-rejected-linked.md"
    archive.parent.mkdir(parents=True, exist_ok=True)
    target = root / "hidden-rejected-plan.md"
    target.write_text("# Rejected plan\n", encoding="utf-8")
    archive.symlink_to(target)
    rel = str(archive.relative_to(root))
    assert git(root, "add", "-f", rel).returncode == 0
    assert git(root, "commit", "-m", "archive rejected symlink", "-q").returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "not a regular file at HEAD" in result.message


def test_archive_ceremony_blocks_staged_symlink_in_rejected_state(tmp_path, sweep_env):
    """Rejected-state exemption for checkboxes never admits unreadable bytes."""
    root = make_repo(tmp_path, "archive-rejected-symlink", gitignore_docs=True)
    write_facts(root)
    now = time.time()
    marker = make_marker(root, now, os.getpid())
    write_run_manifest_record(root, marker)
    archive = root / "docs/history/plans/rejected/2026-10-10-linked-rejected.md"
    archive.parent.mkdir(parents=True, exist_ok=True)
    target = root / "hidden-rejected-target.md"
    target.write_text("# Plan\n\n- [ ] rejected plan\n", encoding="utf-8")
    archive.symlink_to(target)
    assert git(root, "add", "-f", str(archive.relative_to(root))).returncode == 0

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "not a regular file" in result.message


@pytest.mark.parametrize("failed_part", ["PLAN.md", "tasks/01-a.md"])
def test_archive_ceremony_fails_closed_on_staged_directory_read_error(
    tmp_path, sweep_env, monkeypatch, failed_part
):
    """Unreadable staged charter/task bytes cannot become a passing empty span."""
    root = make_repo(tmp_path, f"ceremony-staged-read-{failed_part.replace('/', '-')}", gitignore_docs=True)
    write_facts(root)
    slug = "2026-10-03-staged-read"
    plan_dir = root / "docs/history/plans" / slug
    (plan_dir / "tasks").mkdir(parents=True)
    (plan_dir / "PLAN.md").write_text(
        "# Plan: staged read\n\n- [x] charter task\n", encoding="utf-8"
    )
    (plan_dir / "tasks/01-a.md").write_text(
        "### Task 1\n\n- [x] task box\n", encoding="utf-8"
    )
    git(
        root, "add", "-f", f"docs/history/plans/{slug}/PLAN.md",
        f"docs/history/plans/{slug}/tasks/01-a.md",
    )
    assert git(root, "commit", "-m", "create plan", "-q").returncode == 0
    archive_dir = root / "docs/history/plans/completed" / slug
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    assert git(root, "mv", f"docs/history/plans/{slug}", str(archive_dir.relative_to(root))).returncode == 0
    _write_exec_review_record(root, slug)

    ctx = ctx_for(root)
    real_git = ctx.git
    real_git_bytes = ctx.git_bytes

    def fail_index_blob(*args, **kwargs):
        if args and args[0] == "show" and len(args) > 1 and str(args[1]).startswith(":"):
            return subprocess.CompletedProcess(
                list(args), 1, stdout="", stderr="simulated staged blob read failure"
            )
        return real_git(*args, **kwargs)

    monkeypatch.setattr(ctx, "git", fail_index_blob)
    def fail_index_blob_bytes(*args):
        if args and args[0] == "show" and len(args) > 1 and str(args[1]).startswith(":"):
            return subprocess.CompletedProcess(
                list(args), 1, stdout=b"", stderr=b"simulated staged blob read failure"
            )
        return real_git_bytes(*args)

    monkeypatch.setattr(ctx, "git_bytes", fail_index_blob_bytes)
    result = run_gate("archive-ceremony", ctx)

    assert result.rc == 1, result.message
    assert "simulated staged blob read failure" in result.message


@pytest.mark.parametrize(
    "failure", ["committed-archive", "deliverables", "archive-twin"]
)
def test_archive_ceremony_fails_closed_on_committed_evidence_read_error(
    tmp_path, sweep_env, monkeypatch, failure
):
    """Committed rename and stale-deliverable evidence reads cannot fail open."""
    root = make_repo(tmp_path, f"ceremony-committed-read-{failure}", gitignore_docs=True)
    write_facts(root)
    plan_name = "2026-10-03-read-error.md"
    plan_rel = f"docs/history/plans/{plan_name}"
    if failure == "committed-archive":
        marker = make_marker(root, time.time(), os.getpid())
        write_run_manifest_record(root, marker)
    archive_rel = _committed_plan_archive(
        root, plan_name, "# Plan: read error\n\n- [x] task\n"
    )
    if failure != "committed-archive":
        marker = make_marker(root, time.time(), os.getpid())
        write_run_manifest_record(root, marker)
        write_deliverables(root, [plan_rel])
    _write_exec_review_record(root, plan_name)

    if failure == "deliverables":
        target = root / "docs/tmp/done-session/plan-deliverables.txt"
        real_read_text = Path.read_text

        def fail_deliverables(self, *args, **kwargs):
            if self == target:
                raise OSError("simulated deliverables read failure")
            return real_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", fail_deliverables)
        ctx = ctx_for(root)
    else:
        ctx = ctx_for(root)
        real_git = ctx.git
        real_git_bytes = ctx.git_bytes

        def fail_archive_show(*args, input_text=None):
            if failure == "archive-twin" and args[0] == "ls-tree":
                return subprocess.CompletedProcess(args, 1, "", "simulated tree read failure")
            if failure == "committed-archive" and (
                args[0] == "show"
                and len(args) > 1
                and args[1] == f"HEAD:{archive_rel}"
            ):
                return subprocess.CompletedProcess(args, 1, "", "simulated blob read failure")
            return real_git(*args, input_text=input_text)

        ctx.git = fail_archive_show
        def fail_archive_show_bytes(*args):
            if failure == "committed-archive" and (
                args[0] == "show" and len(args) > 1
                and args[1] == f"HEAD:{archive_rel}"
            ):
                return subprocess.CompletedProcess(
                    list(args), 1, stdout=b"", stderr=b"simulated blob read failure"
                )
            return real_git_bytes(*args)

        ctx.git_bytes = fail_archive_show_bytes

    result = run_gate("archive-ceremony", ctx)

    assert result.rc == 1, result.message
    assert "archive-ceremony gate failed" in result.message


def test_archive_ceremony_fails_closed_on_unresolvable_manifest_boundary(
    tmp_path, sweep_env
):
    """A present run manifest with an invalid commit cannot skip committed coverage."""
    root = make_repo(tmp_path, "ceremony-invalid-boundary", gitignore_docs=True)
    write_facts(root)
    marker = make_marker(root, time.time(), os.getpid())
    manifest_path = write_run_manifest_record(root, marker)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["start_commit"] = "deadbeef"
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = run_gate("archive-ceremony", ctx_for(root))

    assert result.rc == 1, result.message
    assert "committed archive boundary does not resolve" in result.message


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


def _closeout_repo(tmp_path, name: str, *, commit_archive: bool = True) -> Path:
    """The landed-complete fixture repo: archived plan, closed origin under
    the backlog completed archive, and the ownership registry row. The
    archive is a landed commit by default (the landed-archive verification
    reads the destination from the commit tree); ``commit_archive=False``
    leaves the moved plan as uncommitted working-tree residue."""
    root = make_repo(tmp_path, name, gitignore_docs=True)
    write_facts(root)
    archived = root / CLOSEOUT_ARCHIVED_REL
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text(CLOSEOUT_PLAN_TEXT, encoding="utf-8")
    if commit_archive:
        git(root, "add", "-f", CLOSEOUT_ARCHIVED_REL)
        git(root, "commit", "-m", "archive the closeout demo plan", "-q")
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


def _closeout_pre_archive_receipt(root: Path) -> dict:
    """The Phase 4 pre-archive receipt the bounded pre-archive arm consumes
    (plan docs/history/plans/2026-10-15-execute-plan-closeout-cycle-and-
    filed-records.md): the declared archive pathset (plan source path,
    archived destination, promoted origin disposition, the run's filed-row
    paths), the plan digest at pre-archive, the Phase 2 and Phase 3
    evidence pointers, and a recorded-at timestamp. Reads the ACTIVE plan
    bytes for the digest (the receipt is written before the move)."""
    active = root / CLOSEOUT_ACTIVE_REL
    slug_dir = f"docs/tmp/execute-plan/{CLOSEOUT_SLUG}"
    return {
        "declared_paths": [
            CLOSEOUT_ACTIVE_REL,
            CLOSEOUT_ARCHIVED_REL,
            CLOSEOUT_ORIGIN_CLOSED_REL,
        ],
        "archived_plan_path": CLOSEOUT_ARCHIVED_REL,
        "plan_digest": hashlib.sha256(active.read_bytes()).hexdigest(),
        "evidence": [
            f"phase-2 validation receipt: {slug_dir}/validation.md",
            f"phase-3 exit record: {slug_dir}/exit.md",
        ],
        "recorded_at": "2026-10-15T00:00:00Z",
        "filed_row_paths": [],
    }


def _closeout_state_payload(
    root: Path,
    *,
    receipt: bool = True,
    workflow_state: str = "complete",
    tasks: dict | None = None,
    pre_archive_receipt: dict | None = None,
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
    if pre_archive_receipt is not None:
        payload["pre_archive_receipt"] = pre_archive_receipt
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


# --------------------------------------------------------------------------- #
# Plan docs/history/plans/2026-10-15-execute-plan-closeout-cycle-and-filed-
# records.md, Task 1 witnesses: the byte-identical no-receipt refusal pin,
# the bounded pre-archive arm keyed to a well-formed pre_archive_receipt,
# the malformed-receipt fail-closed arm, and the landed-archive commit-tree
# verification over the recorded destination and digest.
# --------------------------------------------------------------------------- #
CLOSEOUT_RESUME_REMEDY_TEXT = (
    "remedy: re-enter the execute-plan continuation and finish Phase 4; "
    "the resumable-closeout checkpoint carries the resume"
)


def _closeout_pre_archive_boundary_repo(tmp_path: Path, name: str) -> Path:
    """The all-tasks-done pre-archive boundary fixture: the plan still
    active on the landing target, every task done, no terminal receipt."""
    root = _closeout_repo(tmp_path, name)
    active = root / CLOSEOUT_ACTIVE_REL
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(CLOSEOUT_PLAN_TEXT, encoding="utf-8")
    return root


def test_closeout_gate_pins_byte_identical_no_receipt_refusal(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given the origin's witnessed all-tasks-done
    shape with no receipt of any kind, expects the refusal message verbatim
    (the byte-identical pin captured before the bounded pre-archive arm
    landed: a receipt-free state must never see new text or a new
    remedy)."""
    root = _closeout_pre_archive_boundary_repo(tmp_path, "closeout-pin")
    state_path = _write_closeout_state(
        root,
        CLOSEOUT_SLUG,
        _closeout_state_payload(root, receipt=False, workflow_state="active"),
    )
    _closeout_done_run(root)
    before = state_path.read_bytes()
    result = run_gate("execute-plan-closeout", ctx_for(root))
    expected = (
        "execute-plan-closeout gate failed: execute-plan session "
        f"{CLOSEOUT_SLUG} ({state_path}) landed without terminal evidence: "
        "every task is done under the runtime done predicate but the "
        "manifest carries no terminal_receipt (workflow_state 'active'); "
        + CLOSEOUT_RESUME_REMEDY_TEXT
    )
    assert result.rc == 1, result.message
    assert result.message == expected
    assert result.warnings == []
    assert state_path.read_bytes() == before
    assert lib.CLOSEOUT_RESUME_REMEDY == CLOSEOUT_RESUME_REMEDY_TEXT


def test_closeout_gate_admits_bounded_pre_archive_transition(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given an all-tasks-done owned session whose
    state carries a well-formed pre_archive_receipt before the archive
    commit is requested (the plan still active, no terminal_receipt),
    expects rc 0 with one pass note naming the receipt and the declared
    archive destination (the bounded pre-archive arm; declared-set
    equality stays with the staged-scope guard)."""
    root = _closeout_pre_archive_boundary_repo(tmp_path, "closeout-bounded")
    _write_closeout_state(
        root,
        CLOSEOUT_SLUG,
        _closeout_state_payload(
            root,
            receipt=False,
            workflow_state="active",
            pre_archive_receipt=_closeout_pre_archive_receipt(root),
        ),
    )
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "pre_archive_receipt" in result.message
    assert CLOSEOUT_ARCHIVED_REL in result.message
    assert "landed without terminal evidence" not in result.message


@pytest.mark.parametrize(
    ("mutation", "offending_field"),
    [
        ("not-an-object", "pre_archive_receipt"),
        ("missing-declared-paths", "declared_paths"),
        ("empty-declared-paths", "declared_paths"),
        ("declared-paths-entry-not-a-string", "declared_paths"),
        ("plan-digest-not-a-string", "plan_digest"),
        ("missing-evidence", "evidence"),
        ("empty-evidence", "evidence"),
        ("missing-recorded-at", "recorded_at"),
        ("recorded-at-not-a-string", "recorded_at"),
    ],
)
def test_closeout_gate_refuses_malformed_pre_archive_receipt(
    tmp_path, sweep_env, closeout_origins_script, mutation, offending_field
):
    """[class: REPOSITORY_TEST] Given an all-tasks-done owned session whose
    pre_archive_receipt is present but malformed (missing keys, wrong
    types), expects rc 1 naming the offending field with the existing
    re-enter-Phase-4 remedy, never the bounded pass (fail-closed over a
    receipt the run wrote malformed)."""
    root = _closeout_pre_archive_boundary_repo(
        tmp_path, f"closeout-bad-receipt-{mutation}"
    )
    receipt = _closeout_pre_archive_receipt(root)
    if mutation == "not-an-object":
        receipt = "not a JSON object"
    elif mutation == "missing-declared-paths":
        del receipt["declared_paths"]
    elif mutation == "empty-declared-paths":
        receipt["declared_paths"] = []
    elif mutation == "declared-paths-entry-not-a-string":
        receipt["declared_paths"] = [CLOSEOUT_ACTIVE_REL, 7]
    elif mutation == "plan-digest-not-a-string":
        receipt["plan_digest"] = 12345
    elif mutation == "missing-evidence":
        del receipt["evidence"]
    elif mutation == "empty-evidence":
        receipt["evidence"] = []
    elif mutation == "missing-recorded-at":
        del receipt["recorded_at"]
    elif mutation == "recorded-at-not-a-string":
        receipt["recorded_at"] = None
    _write_closeout_state(
        root,
        CLOSEOUT_SLUG,
        _closeout_state_payload(
            root,
            receipt=False,
            workflow_state="active",
            pre_archive_receipt=receipt,
        ),
    )
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert offending_field in result.message, result.message
    assert "malformed" in result.message
    assert CLOSEOUT_RESUME_REMEDY_TEXT in result.message
    assert "passed" not in result.message


def test_closeout_gate_refuses_archive_absent_from_commit_tree(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a landed-complete run whose archived
    plan sits in the working tree with receipt-matching bytes but was never
    committed, expects rc 1 naming the commit-tree condition (the
    destination is absent from HEAD) with the resume remedy: the archive is
    a landed commit, never working-tree residue the receipt claims
    landed."""
    root = _closeout_repo(
        tmp_path, "closeout-uncommitted-archive", commit_archive=False
    )
    _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert CLOSEOUT_ARCHIVED_REL in result.message
    assert "absent from the commit tree" in result.message
    assert CLOSEOUT_RESUME_REMEDY_TEXT in result.message


def test_closeout_gate_refuses_divergent_committed_archive_digest(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given a landed-complete run whose HEAD
    carries archived bytes diverging from the receipt digest while the
    working tree matches it, expects rc 1 naming the commit-tree digest
    mismatch with the resume remedy (the working-tree arm alone would
    silently pass a rewritten landed archive)."""
    root = _closeout_repo(tmp_path, "closeout-divergent-commit")
    payload = _closeout_state_payload(root)
    archived = root / CLOSEOUT_ARCHIVED_REL
    archived.write_text("committed divergent archive bytes\n", encoding="utf-8")
    git(root, "add", "-f", CLOSEOUT_ARCHIVED_REL)
    git(root, "commit", "-m", "rewrite the landed archive", "-q")
    archived.write_text(CLOSEOUT_PLAN_TEXT, encoding="utf-8")
    _write_closeout_state(root, CLOSEOUT_SLUG, payload)
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert CLOSEOUT_ARCHIVED_REL in result.message
    assert "digest mismatch" in result.message
    assert "commit tree" in result.message
    assert CLOSEOUT_RESUME_REMEDY_TEXT in result.message


# --------------------------------------------------------------------------- #
# Plan docs/history/plans/2026-10-15-execute-plan-closeout-cycle-and-filed-
# records.md, Task 4 witnesses: the gate-level end-to-end acceptance
# sequence (pre-archive receipt, declared archive commit, terminal
# landed-complete verification, divergent-digest refusal) and the negative
# arms the Task 1 pins do not carry (an aborted owned run stays out of
# scope; the paused mid-run shape keeps the pass-with-note guard). The
# receipt-free byte-identical refusal and the malformed-receipt fail-closed
# arms stay with the Task 1 pins above (pinned verbatim there; not
# duplicated here).
# --------------------------------------------------------------------------- #
def test_closeout_gate_end_to_end_receipt_backed_archive_transition(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given the origin's acceptance sequence: the
    all-tasks-done state plus a well-formed pre_archive_receipt passes the
    closeout at the archive-commit boundary (the bounded pre-archive arm,
    the refusal the origin witnessed is gone); after the declared archive
    transition commits the moved plan, the follow-up boundary with the
    archived destination and matching digest passes landed-complete
    verification; a divergent recorded digest at that boundary fails naming
    the condition with the resume remedy. One witness for the complete
    pre-archive, archive-commit, final-terminal sequence."""
    root = _closeout_repo(tmp_path, "closeout-e2e", commit_archive=False)
    active = root / CLOSEOUT_ACTIVE_REL
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(CLOSEOUT_PLAN_TEXT, encoding="utf-8")
    pre_receipt = _closeout_pre_archive_receipt(root)
    payload = _closeout_state_payload(
        root,
        receipt=False,
        workflow_state="active",
        pre_archive_receipt=pre_receipt,
    )
    # The destination does not exist yet: the receipt is written before the
    # archive commit is requested.
    (root / CLOSEOUT_ARCHIVED_REL).unlink()
    _write_closeout_state(root, CLOSEOUT_SLUG, payload)
    _closeout_done_run(root)

    # Boundary 1: the archive-commit closeout passes on the receipt.
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "pre_archive_receipt" in result.message
    assert CLOSEOUT_ARCHIVED_REL in result.message
    assert "landed without terminal evidence" not in result.message

    # The declared archive transition: the move lands as a commit.
    archived = root / CLOSEOUT_ARCHIVED_REL
    archived.write_text(CLOSEOUT_PLAN_TEXT, encoding="utf-8")
    git(root, "add", "-f", CLOSEOUT_ARCHIVED_REL)
    active.unlink()
    git(root, "commit", "-m", "archive the closeout demo plan", "-q")
    archive_sha = git(root, "rev-parse", "HEAD").stdout.strip()

    # Boundary 2: the terminal receipt records the destination, the
    # pre-archive digest, and the archive commit sha; landed-complete
    # verification passes against the landed commit.
    payload["workflow_state"] = "complete"
    payload["terminal_receipt"] = {
        "workflow_state": "complete",
        "archived_plan_path": CLOSEOUT_ARCHIVED_REL,
        "last_commit_sha": archive_sha,
        "plan_digest": pre_receipt["plan_digest"],
    }
    _write_closeout_state(root, CLOSEOUT_SLUG, payload)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "landed complete" in result.message

    # Boundary 2 divergent: a recorded digest diverging from the landed
    # archive bytes fails naming the condition with the resume remedy.
    payload["terminal_receipt"]["plan_digest"] = "f" * 64
    _write_closeout_state(root, CLOSEOUT_SLUG, payload)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 1, result.message
    assert "digest mismatch" in result.message
    assert CLOSEOUT_RESUME_REMEDY_TEXT in result.message


def test_closeout_gate_keeps_aborted_run_out_of_scope(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given an owned session whose workflow_state
    is aborted, even in the would-refuse shape (every task done under the
    runtime done predicate, no receipt of any kind), expects rc 0 with the
    out-of-scope pass note and the state file untouched; a malformed
    pre_archive_receipt in the aborted payload cannot surface because the
    closeout arms are not reached (the aborted run stays out of scope, the
    gate unaffected)."""
    root = _closeout_pre_archive_boundary_repo(tmp_path, "closeout-aborted")
    state_path = _write_closeout_state(
        root,
        CLOSEOUT_SLUG,
        _closeout_state_payload(root, receipt=False, workflow_state="aborted"),
    )
    _closeout_done_run(root)
    before = state_path.read_bytes()
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "aborted" in result.message
    assert "out of scope" in result.message
    assert "landed without terminal evidence" not in result.message
    assert state_path.read_bytes() == before

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["pre_archive_receipt"] = {"declared_paths": "not a list"}
    state_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result2 = run_gate("execute-plan-closeout", ctx_for(root))
    assert result2.rc == 0, result2.message
    assert "out of scope" in result2.message
    assert "malformed" not in result2.message


def test_closeout_gate_keeps_paused_mid_run_pass_with_note(
    tmp_path, sweep_env, closeout_origins_script
):
    """[class: REPOSITORY_TEST] Given the paused mid-run shape (tasks not
    all done under the runtime done predicate, no receipt of any kind),
    expects rc 0 with the pass-with-note guard naming an executing run (the
    gate never blocks a run that is still executing); the all-tasks-done
    paused-between-the-last-task-and-Phase-4 refusal stays with the
    byte-identical no-receipt pin above."""
    root = _closeout_pre_archive_boundary_repo(tmp_path, "closeout-mid-run")
    _write_closeout_state(
        root,
        CLOSEOUT_SLUG,
        _closeout_state_payload(
            root,
            receipt=False,
            workflow_state="active",
            tasks={
                "task-1": {
                    "id": "task-1",
                    "status": "complete",
                    "checkbox": True,
                },
                "task-2": {
                    "id": "task-2",
                    "status": "in_progress",
                    "checkbox": False,
                },
            },
        ),
    )
    _closeout_done_run(root)
    result = run_gate("execute-plan-closeout", ctx_for(root))
    assert result.rc == 0, result.message
    assert "mid-run" in result.message
    assert "never blocks an executing run" in result.message
    assert "landed without terminal evidence" not in result.message


# --------------------------------------------------------------------------- #
# Plan docs/history/plans/2026-10-15-execute-plan-closeout-cycle-and-filed-
# records.md, Task 2 presence pins: the receipt keys and the landed-archive
# verification phrase appear in the execute-plan skill text, and the skill
# and its vendored twin stay byte-equal (the Validation Commands' pinned
# diff line exits 0).
# --------------------------------------------------------------------------- #
EXECUTE_PLAN_SKILL_REL = "agents/skills/execute-plan/SKILL.md"
EXECUTE_PLAN_SKILL_PINS = (
    "pre_archive_receipt",
    "filed_row_paths",
    "archived_plan_path",
    "plan_digest",
    "`evidence`",
    "recorded_at",
    "declared_paths",
    "the archive is a landed commit, never working-tree residue "
    "the receipt claims landed",
    "re-enter the execute-plan continuation and finish Phase 4; the "
    "resumable-closeout checkpoint carries the resume",
)


def test_execute_plan_skill_receipt_pins_and_vendored_twin():
    """[class: REPOSITORY_TEST] Plan Task 2 presence pins: the receipt keys
    (``pre_archive_receipt``, ``declared_paths``, ``archived_plan_path``,
    ``plan_digest``, ``recorded_at``, ``filed_row_paths``) and the
    landed-archive verification phrase appear in the execute-plan skill
    text, and the skill is byte-equal with its vendored twin, which carries
    the same pins. Fails before the skill text lands, passes after."""
    repo_root = Path(__file__).resolve().parents[1]
    skill_bytes = (repo_root / EXECUTE_PLAN_SKILL_REL).read_bytes()
    skill_text = skill_bytes.decode("utf-8")
    for pin in EXECUTE_PLAN_SKILL_PINS:
        assert pin in skill_text, f"presence pin absent from the skill: {pin!r}"
    twin_path = Path.home() / ".agents" / "skills" / "execute-plan" / "SKILL.md"
    if not twin_path.exists():
        pytest.skip(
            "vendored twin not deployed on this machine; the same-change "
            "twin sync and the Validation Commands diff line own it"
        )
    twin_bytes = twin_path.read_bytes()
    assert twin_bytes == skill_bytes, (
        "the vendored twin diverges from agents/skills/execute-plan/SKILL.md "
        "(the diff line in the plan's Validation Commands must exit 0)"
    )
    twin_text = twin_bytes.decode("utf-8")
    for pin in EXECUTE_PLAN_SKILL_PINS:
        assert pin in twin_text, f"presence pin absent from the twin: {pin!r}"


REVIEW_PANEL_SELECTION_REL = (
    "agents/skills/review-agents/review-panel-selection.md"
)
REVIEW_PANEL_SECTION_ANCHOR = "## Recommended five-worker panel"
REVIEW_PANEL_FILED_ROWS_PINS = (
    "claiming backlog filings",
    "uncommitted and untracked",
    "never pass-with-notes",
    "a recorded tracked landing path satisfies the check",
)
AGENTS_VENDORED_TWIN_RULE_PIN = "never strand the vendored twin as orphan dirt"
AGENTS_FILED_RECORDS_PIN = (
    "A run that files durable records lands them in the same run or leaves "
    "a tracked landing path; never strand them as untracked residue."
)


def test_review_composition_filed_rows_pins_and_vendored_twin():
    """[class: REPOSITORY_TEST] Plan Task 3 presence pins: the
    execution-review completeness duty (an execute-plan run record claiming
    backlog filings whose tree leaves them uncommitted and untracked is a
    blocking finding, never pass-with-notes; a recorded tracked landing path
    satisfies the check) appears inside the ``## Recommended five-worker
    panel`` section of the review-panel catalog, and the AGENTS.md
    durable-records landing-path line sits beside the vendored-twin
    orphan-dirt rule. The catalog is byte-equal with its vendored twin.
    Fails before the duty lines land, passes after."""
    repo_root = Path(__file__).resolve().parents[1]
    catalog_bytes = (repo_root / REVIEW_PANEL_SELECTION_REL).read_bytes()
    catalog_text = catalog_bytes.decode("utf-8")
    section_start = catalog_text.index(REVIEW_PANEL_SECTION_ANCHOR)
    section_end = catalog_text.index("\n## ", section_start + 1)
    section_text = catalog_text[section_start:section_end]
    for pin in REVIEW_PANEL_FILED_ROWS_PINS:
        assert pin in section_text, (
            "presence pin absent from the five-worker panel section: "
            f"{pin!r}"
        )
    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert AGENTS_VENDORED_TWIN_RULE_PIN in agents_text
    assert AGENTS_FILED_RECORDS_PIN in agents_text
    agents_lines = agents_text.splitlines()
    rule_lines = [
        i
        for i, line in enumerate(agents_lines)
        if AGENTS_VENDORED_TWIN_RULE_PIN in line
    ]
    duty_lines = [
        i
        for i, line in enumerate(agents_lines)
        if "files durable records" in line
    ]
    assert rule_lines and duty_lines, (
        "the vendored-twin rule or the durable-records duty line is absent"
    )
    assert min(
        abs(duty - rule) for rule in rule_lines for duty in duty_lines
    ) == 1, "the durable-records line must sit beside the vendored-twin rule"
    skills_root = Path.home() / ".agents" / "skills"
    twin_path = (
        skills_root / "review-agents" / "review-panel-selection.md"
    )
    if not skills_root.exists() or not twin_path.exists():
        pytest.skip(
            "vendored twin under ~/.agents/skills not deployed on this "
            "machine; the same-change twin sync and the Validation Commands "
            "diff line own it"
        )
    twin_bytes = twin_path.read_bytes()
    assert twin_bytes == catalog_bytes, (
        "the vendored twin diverges from agents/skills/review-agents/"
        "review-panel-selection.md (the diff line in the plan's Validation "
        "Commands must exit 0)"
    )
    twin_text = twin_bytes.decode("utf-8")
    twin_section_start = twin_text.index(REVIEW_PANEL_SECTION_ANCHOR)
    twin_section_end = twin_text.index("\n## ", twin_section_start + 1)
    for pin in REVIEW_PANEL_FILED_ROWS_PINS:
        assert pin in twin_text[twin_section_start:twin_section_end], (
            f"presence pin absent from the twin's panel section: {pin!r}"
        )


# --------------------------------------------------------------------------- #
# Outcome-contract fixtures for the execute-plan-closeout origins consumer
# (plan docs/history/plans/2026-10-03-outcome-contract-migration-batch-1.md,
# Task 3). The migrated origins checker (scripts/check_plan_origins_closed.py)
# reports the four-outcome contract; the consumer branches on every outcome
# and on the missing-OUTCOME-line rule instead of collapsing any non-zero
# child exit into a refuse.
# --------------------------------------------------------------------------- #
class DoneSweepGatesLibOutcomeTest(unittest.TestCase):
    """Outcome-contract fixtures (plan Task 3): a child origins run reporting
    indeterminate (exit 2) yields an indeterminate gate result, never a
    refuse; a tool-error child (exit 3) yields a tool-error result; and a
    migrated child with no final `OUTCOME:` line yields tool error per the
    contract's no-line rule. The child seam is the documented
    ``CHECK_PLAN_ORIGINS_CLOSED_SCRIPT`` env override, stubbed per case."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        runtime_home = self.tmp / "runtime-home"
        runtime_home.mkdir()
        user_facts = self.tmp / "user-facts.md"
        user_facts.write_text("# fixture user facts\n", encoding="utf-8")
        self._saved_env = {}
        for var, value in (
            ("DONE_SWEEP_RUNTIME_HOME", str(runtime_home)),
            ("DONE_SWEEP_USER_FACTS", str(user_facts)),
        ):
            self._saved_env[var] = os.environ.get(var)
            os.environ[var] = value
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        for var, old in self._saved_env.items():
            if old is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = old

    def _run_case(self, name: str, stub_body: str):
        stub = self.tmp / f"origins-child-{name}.py"
        stub.write_text(stub_body, encoding="utf-8")
        saved = os.environ.get("CHECK_PLAN_ORIGINS_CLOSED_SCRIPT")
        os.environ["CHECK_PLAN_ORIGINS_CLOSED_SCRIPT"] = str(stub)
        try:
            root = _closeout_repo(self.tmp, f"closeout-origins-{name}")
            _write_closeout_state(root, CLOSEOUT_SLUG, _closeout_state_payload(root))
            _closeout_done_run(root)
            return run_gate("execute-plan-closeout", ctx_for(root))
        finally:
            if saved is None:
                os.environ.pop("CHECK_PLAN_ORIGINS_CLOSED_SCRIPT", None)
            else:
                os.environ["CHECK_PLAN_ORIGINS_CLOSED_SCRIPT"] = saved

    def test_origins_consumer_branches_on_outcomes(self):
        stub_bodies = {
            "indeterminate": (
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('observed: origin unreadable at classification "
                "time: docs/history/backlog/2026-10-01-closeout-origin.md; "
                "could not determine: the origin disposition state')\n"
                "print('OUTCOME: indeterminate')\n"
                "sys.exit(2)\n"
            ),
            "tool_error": (
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('error: the plans directory is unreadable')\n"
                "print('OUTCOME: tool_error')\n"
                "sys.exit(3)\n"
            ),
            "no-line": (
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('origins all closed')\n"
                "sys.exit(0)\n"
            ),
        }
        expectations = {
            "indeterminate": (2, ["indeterminate", "unreadable"], ["gate failed"]),
            "tool_error": (3, ["tool error"], ["gate failed"]),
            "no-line": (3, ["OUTCOME", "tool error"], ["gate failed"]),
        }
        for name, body in stub_bodies.items():
            with self.subTest(case=name):
                want_rc, want_terms, refuse_terms = expectations[name]
                result = self._run_case(name, body)
                self.assertEqual(
                    result.rc, want_rc, f"{name}: {result.message}"
                )
                for term in want_terms:
                    self.assertIn(term, result.message)
                for term in refuse_terms:
                    # The indeterminate and tool-error arms are never a
                    # refuse: the refuse wording is reserved for the
                    # modeled-violation arm.
                    self.assertNotIn(term, result.message)


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-03-squash-landing-failure-path-guard.md,
# Task 3. The post-landing staging invariant gate: the primary checkout's
# index must match HEAD except for staged paths owned by the resolvable
# current-session manifest, unstaged tracked modifications are permitted only
# for the record-only allowlist, residue under a held merge lock reports
# indeterminate, and untracked paths are reported-not-failing.
# --------------------------------------------------------------------------- #
POST_LANDING_DONE_LOCK = SCRIPTS_DIR / "done-lock.sh"


def post_landing_allowlist_file(root: Path) -> Path:
    """Create and commit the record-only allowlist path as a tracked file."""
    lessons = root / "projects" / ".ai-playbook" / "development_lessons.md"
    lessons.parent.mkdir(parents=True, exist_ok=True)
    lessons.write_text("development lessons\n", encoding="utf-8")
    git(root, "add", "projects")
    git(root, "commit", "-m", "lessons", "-q")
    return lessons


def acquire_merge_lock_for_gate(repo: Path, lock_root: Path):
    """Acquire a live merge lock on repo via done-lock.sh; returns (dir, token)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["MERGE_LOCK_ROOT"] = str(lock_root)
    env["MERGE_LOCK_HOLDER_PID"] = str(os.getpid())
    proc = subprocess.run(
        ["bash", str(POST_LANDING_DONE_LOCK), "merge-acquire", "--label", "fixture"],
        capture_output=True, text=True, check=False, cwd=str(repo), env=env,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    values = {}
    for line in proc.stdout.splitlines():
        if line.startswith("export "):
            key, _, value = line[len("export "):].partition("=")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            values[key] = value
    # The session fence is done-lock's status witness, not fixture state under
    # test: remove it so the primary checkout's porcelain carries only the
    # residue the fixture itself created.
    session = Path(repo) / ".ai-playbook" / "merge-lock.session"
    try:
        session.unlink()
        session.parent.rmdir()
    except OSError:
        pass
    return values["MERGE_LOCK_DIR"], values["MERGE_LOCK_TOKEN"]


def write_run_manifest_record(root: Path, marker, owned_paths=(), owned_plan_paths=()) -> Path:
    """Write a Step 0 run manifest record bound to the given marker."""
    done_session = root / "docs" / "tmp" / "done-session"
    done_session.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "run_id": "post-landing-fixture",
        "marker": marker.name,
        "created_epoch": time.time(),
        "repo_root": root_digest(root),
        "pid": os.getpid(),
        "start_commit": git(root, "rev-parse", "HEAD").stdout.strip(),
        "start_porcelain": [],
        "owned_paths": list(owned_paths),
        "owned_plan_paths": list(owned_plan_paths),
        "owned_review_paths": [],
        "foreign_review_paths": [],
        "adopted_from": None,
        "complete": False,
    }
    path = done_session / "run-manifest-post-landing-fixture.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def test_post_landing_staging_clean_pass(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given a primary checkout whose index matches
    HEAD and whose only unstaged tracked modification is the record-only
    allowlist path, expects the gate to pass (rc 0) and name the allowlisted
    path as permitted."""
    root = mktemp_repo("post-landing-clean")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    lessons = post_landing_allowlist_file(root)
    lessons.write_text("development lessons + peer edit\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert "development_lessons.md" in result.message
    assert "permitted" in result.message


def test_post_landing_staging_staged_refusal(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given one staged path in the primary index
    outside the session's owned set, expects the gate to fail (rc 1) naming
    the residue path, the sanctioned cleanup recipe (the helper's
    probe-then-reland path), and the operator escape (per-path restore after
    merge-status free); given a staged path INSIDE the resolvable session's
    owned set, expects the gate to pass naming it as owned (the own-staged
    exemption)."""
    root = mktemp_repo("post-landing-staged")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "foreign.txt").write_text("foreign residue\n", encoding="utf-8")
    git(root, "add", "foreign.txt")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert "foreign.txt" in result.message
    assert "land_squash.sh" in result.message
    assert "probe-then-reland" in result.message
    assert "restore --staged --worktree" in result.message
    assert "merge-status" in result.message

    owned_root = mktemp_repo("post-landing-owned")
    marker = make_marker(owned_root, time.time(), os.getpid())
    (owned_root / "closeout.md").write_text("closeout work\n", encoding="utf-8")
    git(owned_root, "add", "closeout.md")
    write_run_manifest_record(owned_root, marker, owned_paths=["closeout.md"])
    owned_result = run_gate("post-landing-staging", ctx_for(owned_root))
    assert owned_result.rc == 0, owned_result.message
    assert "closeout.md" in owned_result.message
    assert "owned" in owned_result.message


def test_post_landing_staging_unowned_unstaged_warns(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Demotion program change 1: given an unstaged
    tracked modification outside the allowlist and no resolvable manifest
    (every unstaged path unowned by construction), expects the gate to PASS
    (rc 0) with a warning naming the path, the sanctioned cleanup recipe, and
    the operator escape; given a SECOND modification inside the allowlist
    alongside it, expects the allowlisted one named as permitted in the pass
    message and the other in the warning."""
    root = mktemp_repo("post-landing-dirty")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    lessons = post_landing_allowlist_file(root)
    (root / "README.md").write_text("dirty residue\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert (
        "no unowned staging, no blocking residue" in result.message
    )
    warning = next(w for w in result.warnings if "README.md" in w)
    assert "reported, not failing" in warning
    assert "land_squash.sh" in warning
    assert "probe-then-reland" in warning
    assert "restore --staged --worktree" in warning
    assert "merge-status" in warning
    lessons.write_text("development lessons + peer edit\n", encoding="utf-8")
    both = run_gate("post-landing-staging", ctx_for(root))
    assert both.rc == 0, both.message
    assert "development_lessons.md" in both.message
    assert "permitted" in both.message
    assert any("README.md" in warning for warning in both.warnings)


def test_post_landing_staging_owned_unstaged_warns(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Demotion program change 7: with a resolvable
    manifest that owns a committed-then-modified tracked file left unstaged
    under an unconfigured (non-primary-resident) placement, the
    manifest-owned unstaged class reports and continues (rc 0) - the guard
    entry post-landing-staging-gate reads 0 catches / 1 incident, the
    2026-10-05 owned-plan refusal witnessed three times - and the warning
    carries the misdirected-write check first plus the staging resolution,
    never a destructive remedy."""
    root = mktemp_repo("post-landing-owned-dirty")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "closeout.md").write_text("committed run file\n", encoding="utf-8")
    git(root, "add", "closeout.md")
    git(root, "commit", "-m", "run file", "-q")
    marker = make_marker(root, time.time(), os.getpid())
    (root / "closeout.md").write_text("run work, wrong checkout\n", encoding="utf-8")
    write_run_manifest_record(root, marker, owned_paths=["closeout.md"])
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    warning = next(w for w in result.warnings if "closeout.md" in w)
    assert "manifest-owned unstaged residue" in warning
    assert "reported, not failing" in warning
    assert warning.index("misdirected-write") < warning.index("git add")
    assert "never the bare restore escape or the reland path" in warning


def test_post_landing_staging_untracked_warning(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given untracked paths in the primary checkout,
    expects the gate to pass with warning lines naming them
    (reported-not-failing per the recorded narrowing)."""
    root = mktemp_repo("post-landing-untracked")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "scratch.txt").write_text("untracked scratch\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert any("scratch.txt" in warning for warning in result.warnings)


def test_post_landing_staging_primary_resolution(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] The gate inspects the FIRST
    ``git worktree list --porcelain`` worktree entry, not the cwd checkout:
    the fixture runs the gate from a linked worktree while staging residue in
    the primary checkout and expects the refusal to still fire."""
    root = mktemp_repo("post-landing-primary")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    linked = tmp_path / "post-landing-linked-wt"
    git(root, "worktree", "add", str(linked), "-b", "post-landing-lane")
    (root / "README.md").write_text("staged residue in primary\n", encoding="utf-8")
    git(root, "add", "README.md")
    result = run_gate("post-landing-staging", ctx_for(linked))
    assert result.rc == 1, result.message
    assert "README.md" in result.message


def test_post_landing_staging_unresolvable_manifest_strict(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] With no resolvable run manifest and one staged
    foreign path in the primary index, expects the gate to fail rc 1 naming
    the residue AND to carry the unresolvable-manifest warning line (the
    ownership narrowing is skipped, never the check)."""
    root = mktemp_repo("post-landing-strict")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "foreign.txt").write_text("foreign residue\n", encoding="utf-8")
    git(root, "add", "foreign.txt")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert "foreign.txt" in result.message
    assert any("no resolvable run manifest" in warning for warning in result.warnings)


def test_post_landing_staging_lock_held_indeterminate(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given STAGED residue observed (a blocking
    class after demotion program change 1; unowned unstaged residue now
    warns) and a held merge lock (``done-lock.sh merge-status`` reports a
    holder on re-consult), expects the gate to report indeterminate (rc 2)
    naming the holder, never a residue refusal."""
    root = mktemp_repo("post-landing-lock")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "README.md").write_text("staged residue\n", encoding="utf-8")
    git(root, "add", "README.md")
    lock_root = tmp_path / "post-landing-merge-locks"
    lock_dir, lock_token = acquire_merge_lock_for_gate(root, lock_root)
    assert lock_dir and lock_token
    monkeypatch.setenv("MERGE_LOCK_ROOT", str(lock_root))
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 2, result.message
    assert "held" in result.message
    assert "fixture" in result.message
    assert "probe-then-reland" not in result.message


def test_post_landing_staging_unowned_unstaged_lock_held_warns(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Demotion program change 1 lock arm: given
    only unowned unstaged residue while the merge lock is HELD (a landing in
    flight), expects the gate to pass (rc 0) with the warning line naming the
    path and NO indeterminate report - the demoted class never reaches the
    lock consult, so an in-flight peer landing no longer blocks the
    closeout (witnessed incident 4's quiesce-wait friction)."""
    root = mktemp_repo("post-landing-unowned-lock")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "README.md").write_text("unstaged peer-window residue\n", encoding="utf-8")
    lock_root = tmp_path / "post-landing-unowned-merge-locks"
    lock_dir, lock_token = acquire_merge_lock_for_gate(root, lock_root)
    assert lock_dir and lock_token
    monkeypatch.setenv("MERGE_LOCK_ROOT", str(lock_root))
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert "indeterminate" not in result.message
    assert any("README.md" in warning for warning in result.warnings)


def test_post_landing_staging_mm_row_refused_on_staged_leg_only(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Demotion program change 1 MM arm: a path both
    staged and worktree-modified in the primary (porcelain MM) is refused on
    its STAGED leg (rc 1, named in the refusal render) and is never named in
    an unowned-unstaged warning - the exclusion arm keeps one path from
    carrying contradictory posture text in one gate result."""
    root = mktemp_repo("post-landing-mm-row")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "README.md").write_text("staged side\n", encoding="utf-8")
    git(root, "add", "README.md")
    (root / "README.md").write_text("staged side plus worktree edit\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert "README.md" in result.message
    assert not any(
        "reported, not failing" in warning and "README.md" in warning
        for warning in result.warnings
    )


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-05-execute-plan-lifecycle-recovery-gaps.md,
# Task 1. The done landing sweep's plan-checkbox admission: an unstaged
# plan-path residue whose worktree-vs-HEAD diff classifies checkbox-marker-only
# is admitted in place (the A6 class-1 read; the disposition receipt is only
# required at the done boundary for committed paths), beside the existing
# record-only allowlist behavior.
# --------------------------------------------------------------------------- #
POST_LANDING_PLAN_REL = "docs/history/plans/2026-10-05-fixture-plan.md"


def post_landing_committed_plan(root: Path) -> Path:
    """Create and commit the run's plan document (unchecked task box)."""
    plan = root / POST_LANDING_PLAN_REL
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(
        "# Fixture Plan\n\n### Task 1: fixture\n\n- [ ] step one\n",
        encoding="utf-8",
    )
    git(root, "add", POST_LANDING_PLAN_REL)
    git(root, "commit", "-m", "fixture plan", "-q")
    return plan


def test_post_landing_staging_plan_checkbox_residue_admitted(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given an unstaged tracked modification of the
    run's owned plan path whose worktree-vs-HEAD diff is a pure
    unchecked-to-checked checkbox flip, expects the gate to pass (rc 0) and
    name the admitted residue; given the same plan path carrying substantive
    content drift instead, the admission arm declines but the change-7
    demotion keeps the outcome non-blocking (rc 0 with the manifest-owned
    unstaged warning naming the path)."""
    root = mktemp_repo("post-landing-plan-flip", gitignore_docs=False)
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    plan = post_landing_committed_plan(root)
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_plan_paths=[POST_LANDING_PLAN_REL])
    plan.write_text(
        "# Fixture Plan\n\n### Task 1: fixture\n\n- [x] step one\n",
        encoding="utf-8",
    )
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert "2026-10-05-fixture-plan.md" in result.message

    # Substantive drift on the same path declines the admission arm but
    # warns past it (change 7): an appended prose line has no removed
    # checkbox counterpart, so the paired-line shape never holds and the
    # path lands in the manifest-owned unstaged warning.
    plan.write_text(
        "# Fixture Plan\n\n### Task 1: fixture\n\n- [x] step one\n\nprose appendix\n",
        encoding="utf-8",
    )
    drifted = run_gate("post-landing-staging", ctx_for(root))
    assert drifted.rc == 0, drifted.message
    assert "2026-10-05-fixture-plan.md" not in drifted.message
    warning = next(
        w for w in drifted.warnings if "2026-10-05-fixture-plan.md" in w
    )
    assert "manifest-owned unstaged residue" in warning
    assert "misdirected-write" in warning


def test_post_landing_staging_plan_residue_without_manifest_warns(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] With no resolvable run manifest the ownership
    narrowing is skipped, so an unstaged plan-path flip is never ADMITTED as
    owned; after demotion program change 1 the unowned unstaged class reports
    and continues (rc 0, warning naming the plan path) beside the
    unresolvable-manifest warning - admission stays keyed on the manifest,
    only the posture demoted."""
    root = mktemp_repo("post-landing-plan-strict", gitignore_docs=False)
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    plan = post_landing_committed_plan(root)
    plan.write_text(
        "# Fixture Plan\n\n### Task 1: fixture\n\n- [x] step one\n",
        encoding="utf-8",
    )
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert any("2026-10-05-fixture-plan.md" in warning for warning in result.warnings)
    assert any("no resolvable run manifest" in warning for warning in result.warnings)


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-05-post-landing-staging-placement-awareness.md,
# Task 2. The placement-aware unstaged leg: under a primary-resident facts
# placement (``primary`` or ``primary-execution``) the unstaged leg mirrors
# the staged leg's ownership exemption (owned unstaged paths pass with an
# informational count); every other reading converges on the demoted
# warning arms (program changes 1 and 7), placement-inert. Facts files are written
# manually per fixture practice; the manifest seeding helper and the
# primary-resolution fixture's shape are reused unchanged.
# --------------------------------------------------------------------------- #
def _write_post_landing_facts(root: Path, policy: str) -> Path:
    """Repo facts file carrying the declared worktree placement (the
    production TOML-fence form facts_paths.resolve_toml_key_raw parses)."""
    facts_dir = root / ".ai-playbook"
    facts_dir.mkdir(parents=True, exist_ok=True)
    facts = facts_dir / "facts.md"
    facts.write_text(
        "```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'plans_completed_dir = "docs/history/plans/completed/"\n'
        'backlog_dir = "docs/history/backlog/"\n'
        'reviews_dir = ".ai-playbook/reviews/"\n'
        'tmp_dir = "docs/tmp/"\n'
        'worktree_policy = "' + policy + '"\n'
        "```\n",
        encoding="utf-8",
    )
    return facts


def test_post_landing_staging_primary_owned_unstaged_pass(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given declared-``primary`` facts and a
    manifest-owned unstaged tracked modification, expects the gate to pass
    (rc 0) with the informational count naming the path (the unstaged leg
    mirrors the staged leg's ownership exemption) and the amended base
    parenthetical (no unowned staging, no blocking residue)."""
    root = mktemp_repo("post-landing-primary-owned")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _write_post_landing_facts(root, "primary")
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["README.md"])
    (root / "README.md").write_text("the run's own edits\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert (
        "unstaged path(s) owned by the session manifest or the "
        "invocation's declared-stage channel: README.md"
        in result.message
    )
    assert (
        "no unowned staging, no blocking residue" in result.message
    )
    assert not any(
        "no resolvable run manifest" in warning for warning in result.warnings
    )


def test_post_landing_staging_primary_execution_owned_unstaged_pass(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given declared-``primary-execution`` facts
    (the witnessed placement) and the same manifest-owned unstaged state,
    expects the gate to pass (rc 0) with the same message shape as the
    declared-``primary`` fixture."""
    root = mktemp_repo("post-landing-primary-exec-owned")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _write_post_landing_facts(root, "primary-execution")
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["README.md"])
    (root / "README.md").write_text("the run's own edits\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert (
        "unstaged path(s) owned by the session manifest or the "
        "invocation's declared-stage channel: README.md"
        in result.message
    )
    assert (
        "no unowned staging, no blocking residue" in result.message
    )
    assert not any(
        "no resolvable run manifest" in warning for warning in result.warnings
    )


def test_post_landing_staging_unconfigured_owned_unstaged_warns(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given no facts file (the unconfigured
    reading) and the same manifest-owned unstaged state, the change-7
    demotion is placement-inert: the gate passes (rc 0) with the warning
    carrying the misdirected-write check FIRST, staging the owned path as
    the sanctioned resolution, and neither the bare restore escape nor the
    reland path offered for the owned path."""
    root = mktemp_repo("post-landing-unconfigured-owned")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["README.md"])
    (root / "README.md").write_text("the run's own edits\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    warning = next(w for w in result.warnings if "README.md" in w)
    assert "manifest-owned unstaged residue" in warning
    assert warning.index("misdirected-write") < warning.index("git add")
    assert "never the bare restore escape or the reland path" in warning
    assert not any(
        "no resolvable run manifest" in warning for warning in result.warnings
    )


def test_post_landing_staging_mixed_residue_warns_split(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given one manifest-owned and one unowned
    unstaged path in one closeout under a non-primary reading, expects the
    fully demoted split (program changes 1 and 7): the gate passes (rc 0)
    with two warning lines - the owned path's warning carries the
    owned-class remedies (the misdirected-write check first, staging as the
    sanctioned resolution), while the unowned path's warning carries the
    sanctioned cleanup recipe and the per-path restore escape."""
    root = mktemp_repo("post-landing-mixed-residue")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "notes.md").write_text("unowned tracked file\n", encoding="utf-8")
    git(root, "add", "notes.md")
    git(root, "commit", "-m", "notes", "-q")
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["README.md"])
    (root / "README.md").write_text("the run's own edits\n", encoding="utf-8")
    (root / "notes.md").write_text("unowned residue\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    owned_warning = next(w for w in result.warnings if "README.md" in w)
    assert "manifest-owned unstaged residue" in owned_warning
    assert owned_warning.index("misdirected-write") < owned_warning.index("git add")
    assert "never the bare restore escape or the reland path" in owned_warning
    warning = next(w for w in result.warnings if "notes.md" in w)
    assert "reported, not failing" in warning
    assert "probe-then-reland" in warning
    assert "restore --staged --worktree" in warning


def test_post_landing_staging_malformed_policy_owned_unstaged_warns(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given a facts file declaring an
    out-of-vocabulary ``worktree_policy`` value and a manifest-owned
    unstaged path, the fail-closed declaration reading never widens the
    placement admission (no informational count), but the change-7 demotion
    is placement-inert: the owned path reports and continues (rc 0) with
    the warning carrying the owned-class remedies, never a destructive
    one; the fail-closed reading's residual strictness lives on the staged
    leg."""
    root = mktemp_repo("post-landing-malformed-policy")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _write_post_landing_facts(root, "mostly-worktrees")
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["README.md"])
    (root / "README.md").write_text("the run's own edits\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert (
        "unstaged path(s) owned by the session manifest or the "
        "invocation's declared-stage channel" not in result.message
    )
    warning = next(w for w in result.warnings if "README.md" in w)
    assert "manifest-owned unstaged residue" in warning
    assert warning.index("misdirected-write") < warning.index("git add")
    assert "never the bare restore escape or the reland path" in warning
    assert not any(
        "no resolvable run manifest" in warning for warning in result.warnings
    )


def test_post_landing_staging_primary_unresolvable_manifest_strict(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given declared-``primary`` facts and no
    resolvable run manifest, the placement-inert strictness lives on the
    STAGED leg after demotion program change 1 (unowned unstaged residue
    warns under every placement, so the staged leg carries the test): one
    staged foreign path expects the strict refusal (rc 1) beside the
    unresolvable-manifest warning line."""
    root = mktemp_repo("post-landing-primary-strict")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _write_post_landing_facts(root, "primary")
    (root / "README.md").write_text("staged with no manifest\n", encoding="utf-8")
    git(root, "add", "README.md")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert "README.md" in result.message
    assert "probe-then-reland" in result.message
    assert "misdirected-write" not in result.message
    assert any("no resolvable run manifest" in warning for warning in result.warnings)


def test_post_landing_staging_owned_allowlist_overlap_single_count(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given a manifest-owned unstaged path that
    also sits on the record-only allowlist under declared-``primary`` facts,
    expects the gate to pass (rc 0) with the path named exactly once in the
    allowlist clause and never in the owned-unstaged clause (the
    post-allowlist intersection keeps the count single)."""
    root = mktemp_repo("post-landing-allowlist-overlap")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _write_post_landing_facts(root, "primary")
    lessons = post_landing_allowlist_file(root)
    lessons.write_text("development lessons + peer edit\n", encoding="utf-8")
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(
        root, marker, owned_paths=["projects/.ai-playbook/development_lessons.md"]
    )
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert result.message.count("development_lessons.md") == 1
    assert (
        "record-only allowlist path(s) permitted: "
        "projects/.ai-playbook/development_lessons.md" in result.message
    )
    assert (
        "unstaged path(s) owned by the session manifest or the "
        "invocation's declared-stage channel" not in result.message
    )


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-05-execute-plan-done-boundary-evidence-gates.md,
# Task 1. The mid-session-creation remedy: with a resolvable run manifest, a
# staged path absent from every manifest claim set refuses (rc 1) naming the
# adopting-boundary recovery; the unstaged-only refusal, the held-lock
# indeterminate arm, and the no-manifest refusal keep today's text
# (byte-identical for the no-manifest arm).
# --------------------------------------------------------------------------- #
POST_LANDING_ADOPTION_REMEDY_LITERAL = (
    "whose re-derived owned-path set names only paths that adopting boundary's own session created"
)
# Plan: docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md,
# Task 3: the adopting-boundary sentence pinned verbatim (the whole rendered
# sentence, not the fragment above), so the declared-stage remedy lands beside
# it without ever disturbing its render.
POST_LANDING_ADOPTION_REMEDY_SENTENCE = (
    "; a staged path created after Step 0 (absent from every manifest "
    "claim set) is recovered by closing this done boundary and opening "
    "a fresh adopting boundary, per the Step 0 adopt clause's operator "
    "authorization, whose re-derived owned-path set names only paths "
    "that adopting boundary's own session created (the "
    "operator-authorized cross-session arm keeps the adopted run's own "
    "uncommitted output per the existing adoption re-derivation record), "
    "never by widening the active manifest in place"
)


def test_post_landing_staging_staged_unowned_with_manifest_names_adoption_remedy(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given a resolvable run manifest and one staged
    path absent from every manifest claim set (the mid-session-creation
    shape), expects the rc-1 refusal to name the adopting-boundary remedy:
    close this done boundary and open a fresh adopting boundary per the Step 0
    adopt clause's operator authorization, never widening the active manifest
    in place."""
    root = mktemp_repo("post-landing-mid-session")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["owned.md"])
    (root / "mid-session.txt").write_text("created after Step 0\n", encoding="utf-8")
    git(root, "add", "mid-session.txt")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert "mid-session.txt" in result.message
    assert POST_LANDING_ADOPTION_REMEDY_LITERAL in result.message
    assert "closing this done boundary and opening a fresh adopting boundary" in result.message
    assert "never by widening the active manifest in place" in result.message


def test_post_landing_staging_unowned_unstaged_lacks_adoption_remedy(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Negative direction after demotion program
    change 1: with a resolvable run manifest and only UNOWNED unstaged
    residue (no staged paths, no owned-unstaged paths), expects the gate to
    pass (rc 0) with the path in the warning line, and the adopting-boundary
    remedy literal in neither the message nor any warning (the remedy stays
    keyed on the staged leg)."""
    root = mktemp_repo("post-landing-unstaged-only")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["owned.md"])
    (root / "README.md").write_text("unstaged residue\n", encoding="utf-8")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert any("README.md" in warning for warning in result.warnings)
    assert POST_LANDING_ADOPTION_REMEDY_LITERAL not in result.message
    assert not any(
        POST_LANDING_ADOPTION_REMEDY_LITERAL in warning for warning in result.warnings
    )


def test_post_landing_staging_staged_residue_lock_held_lacks_adoption_remedy(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given staged residue observed while the merge
    lock is held (a landing in flight), expects the indeterminate report
    (rc 2) with the shared render unchanged: the adopting-boundary remedy
    literal stays absent from the indeterminate message."""
    root = mktemp_repo("post-landing-staged-lock")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "foreign.txt").write_text("staged residue\n", encoding="utf-8")
    git(root, "add", "foreign.txt")
    lock_root = tmp_path / "post-landing-staged-merge-locks"
    lock_dir, lock_token = acquire_merge_lock_for_gate(root, lock_root)
    assert lock_dir and lock_token
    monkeypatch.setenv("MERGE_LOCK_ROOT", str(lock_root))
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 2, result.message
    assert "merge lock is held" in result.message
    assert POST_LANDING_ADOPTION_REMEDY_LITERAL not in result.message


# The no-manifest refusal render pinned byte-identical, shared by the
# gate-level pin below and the declared-stage-remedy pins (plan
# docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md,
# Task 3: the remedy sentences stay out of the no-manifest arm).
POST_LANDING_NO_MANIFEST_REFUSAL_PIN = (
    "post-landing-staging gate failed: primary checkout residue after "
    "landing (staged path(s): foreign.txt); "
    "sanctioned cleanup: the land_squash.sh probe-then-reland path (run "
    "scripts/land_squash.sh probe, resolve or compose, then "
    "scripts/land_squash.sh land under the merge lock); operator escape "
    "for dead residue only (done-lock.sh merge-status free AND the path "
    "is not peer-live dirt): git restore --staged --worktree -- <path> "
    "per residue path; record-only allowlist path(s) are never escapable"
)


def test_post_landing_staging_no_manifest_refusal_pinned_text(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] With no resolvable run manifest and one staged
    foreign path, expects the rc-1 refusal with the pinned text (the change-7
    render dropped the always-empty unstaged clause): the ownership narrowing
    is skipped, so the mid-session-creation remedy is never appended to the
    no-manifest arm."""
    root = mktemp_repo("post-landing-no-manifest-pin")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "foreign.txt").write_text("foreign residue\n", encoding="utf-8")
    git(root, "add", "foreign.txt")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert result.message == POST_LANDING_NO_MANIFEST_REFUSAL_PIN, result.message


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md,
# Task 2. The declared-stage channel: DONE_SWEEP_DECLARED_STAGE_PATHS unions
# into the owned computation when a manifest resolved and the checkout-shape
# guard holds (the gate's resolved primary checkout equals the gate context's
# repo root, realpath-resolved on both sides); the record-only allowlist is
# always subtracted; every non-consuming reading contributes nothing, never an
# error, and the no-manifest path keeps today's strict behavior byte-identical.
# --------------------------------------------------------------------------- #
def _post_landing_declared_stage_fixture(root: Path) -> None:
    """The post-setup learn-edit shape: a tracked file committed before the
    manifest was written, modified after it (the documented learn step's
    product) and staged for landing; the manifest owns only an unrelated
    path."""
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["owned.md"])
    (root / "closeout.md").write_text("committed run file\n", encoding="utf-8")
    git(root, "add", "closeout.md")
    git(root, "commit", "-m", "run file", "-q")
    (root / "closeout.md").write_text(
        "learn edit authored after setup\n", encoding="utf-8"
    )
    git(root, "add", "closeout.md")


def test_post_landing_staging_declared_post_setup_staged_path_passes(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given a manifest-resolved primary-resident
    closeout whose staged post-setup learn edit is absent from every manifest
    claim set but named on the declared-stage channel, expects the gate to
    pass (rc 0) with the informational channel line naming the count and the
    normalized path and the reworded staged-ownership clause."""
    root = mktemp_repo("post-landing-declared-stage")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _post_landing_declared_stage_fixture(root)
    monkeypatch.setenv("DONE_SWEEP_DECLARED_STAGE_PATHS", "closeout.md\n")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert (
        "declared-stage channel path(s) owned (1): closeout.md"
        in result.message
    )
    assert (
        "staged path(s) owned by the session manifest or the "
        "invocation's declared-stage channel: closeout.md"
        in result.message
    )
    assert not any(
        "DONE_SWEEP_DECLARED_STAGE_PATHS" in warning
        for warning in result.warnings
    )


def test_post_landing_staging_undeclared_staged_path_refusal_class_identical(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] The strict leg stays refusal-class identical
    for staged paths neither manifest-owned nor declared: a companion run with
    the channel set to a path that is not staged produces the same rc and a
    byte-identical refusal render (same residue paths, same recipes) as the
    run with no channel at all."""
    root_a = mktemp_repo("post-landing-undeclared-a")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _post_landing_declared_stage_fixture(root_a)
    undeclared = run_gate("post-landing-staging", ctx_for(root_a))
    assert undeclared.rc == 1, undeclared.message
    assert "closeout.md" in undeclared.message
    assert "land_squash.sh" in undeclared.message
    assert "probe-then-reland" in undeclared.message
    assert "restore --staged --worktree" in undeclared.message
    assert "merge-status" in undeclared.message

    root_b = mktemp_repo("post-landing-undeclared-b")
    _post_landing_declared_stage_fixture(root_b)
    monkeypatch.setenv("DONE_SWEEP_DECLARED_STAGE_PATHS", "not-staged.md\n")
    declared_elsewhere = run_gate("post-landing-staging", ctx_for(root_b))
    assert declared_elsewhere.rc == undeclared.rc
    assert declared_elsewhere.message == undeclared.message


def test_post_landing_staging_declared_allowlist_path_still_refuses(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] A declared path on the record-only allowlist
    is subtracted from the channel before the union: staging the allowlist
    path and naming it on the channel still refuses (rc 1) with the strict
    render, and the channel contributes no owned clause."""
    root = mktemp_repo("post-landing-declared-allowlist")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    lessons = post_landing_allowlist_file(root)
    marker = make_marker(root, time.time(), os.getpid())
    write_run_manifest_record(root, marker, owned_paths=["owned.md"])
    lessons.write_text("development lessons + run append\n", encoding="utf-8")
    git(root, "add", "projects")
    monkeypatch.setenv(
        "DONE_SWEEP_DECLARED_STAGE_PATHS",
        "projects/.ai-playbook/development_lessons.md\n",
    )
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert "development_lessons.md" in result.message
    assert "record-only allowlist path(s) are never escapable" in result.message
    assert "declared-stage channel path(s) owned" not in result.message


def test_post_landing_staging_declared_absolute_path_normalizes_and_passes(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] An absolute-path channel line normalizes
    through the same repo-relative normalization the manifest claim legs
    receive: the staged post-setup edit declared by its absolute path passes
    (rc 0) with the normalized relative name in the channel line."""
    root = mktemp_repo("post-landing-declared-absolute")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _post_landing_declared_stage_fixture(root)
    monkeypatch.setenv(
        "DONE_SWEEP_DECLARED_STAGE_PATHS", str(root / "closeout.md") + "\n"
    )
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 0, result.message
    assert (
        "declared-stage channel path(s) owned (1): closeout.md"
        in result.message
    )


def test_post_landing_staging_channel_ignored_at_non_primary_checkout(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] The checkout-shape guard: with a resolvable
    manifest in a linked worktree (the gate context's repo root) and the
    declared-stage channel set, the channel is ignored with one named warning
    line (the primary index the gate inspects is not the index this
    invocation staged) and the strict refusal for the primary's staged
    residue stands."""
    root = mktemp_repo("post-landing-channel-linked")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    linked = tmp_path / "post-landing-channel-linked-wt"
    git(root, "worktree", "add", str(linked), "-b", "channel-lane")
    linked_marker = make_marker(linked, time.time(), os.getpid())
    write_run_manifest_record(linked, linked_marker, owned_paths=["owned.md"])
    (root / "README.md").write_text("staged residue in primary\n", encoding="utf-8")
    git(root, "add", "README.md")
    monkeypatch.setenv("DONE_SWEEP_DECLARED_STAGE_PATHS", "README.md\n")
    result = run_gate("post-landing-staging", ctx_for(linked))
    assert result.rc == 1, result.message
    assert "README.md" in result.message
    assert "probe-then-reland" in result.message
    warning = next(
        w
        for w in result.warnings
        if "DONE_SWEEP_DECLARED_STAGE_PATHS" in w
    )
    assert "checkout-shape guard does not hold" in warning
    assert "ignored" in warning
    assert "declared-stage channel path(s) owned" not in result.message


def test_post_landing_staging_channel_without_manifest_keeps_pinned_no_manifest_text(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] With no resolvable run manifest the channel is
    never read: setting DONE_SWEEP_DECLARED_STAGE_PATHS (even naming the
    staged path itself) refuses rc 1 with the byte-identical no-manifest text
    and no channel warning line (today's strict behavior, byte-identical)."""
    root = mktemp_repo("post-landing-channel-no-manifest")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "foreign.txt").write_text("foreign residue\n", encoding="utf-8")
    git(root, "add", "foreign.txt")
    monkeypatch.setenv("DONE_SWEEP_DECLARED_STAGE_PATHS", "foreign.txt\n")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert result.message == POST_LANDING_NO_MANIFEST_REFUSAL_PIN, result.message
    assert not any(
        "DONE_SWEEP_DECLARED_STAGE_PATHS" in warning
        for warning in result.warnings
    )


# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-14-done-ownership-post-setup-learn-edits.md,
# Task 3. The manifest-resolved staged-residue refusal names the post-setup
# remedy (a live edit authored after setup is landed by re-running the commit
# with the path declared via --stage) beside the preserved adopting-boundary
# sentence; the no-manifest arm's text stays byte-identical and carries
# neither remedy sentence.
# --------------------------------------------------------------------------- #
POST_LANDING_DECLARED_STAGE_REMEDY_SENTENCE = (
    "; a live edit authored after setup (the documented learn step's "
    "product) is landed by re-running the commit with the path declared "
    "via --stage"
)


def test_post_landing_staging_refusal_names_declared_stage_remedy(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] Given a manifest-resolved closeout with one
    staged post-setup live edit absent from every manifest claim set and no
    declared-stage channel, expects the rc-1 refusal to carry the byte-pinned
    render: the strict base, the adopting-boundary sentence verbatim, then
    the declared-stage remedy sentence."""
    root = mktemp_repo("post-landing-declared-remedy")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    _post_landing_declared_stage_fixture(root)
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert POST_LANDING_DECLARED_STAGE_REMEDY_SENTENCE in result.message
    assert POST_LANDING_ADOPTION_REMEDY_SENTENCE in result.message
    expected = (
        "post-landing-staging gate failed: primary checkout residue after "
        "landing (staged path(s): closeout.md); "
        "sanctioned cleanup: the land_squash.sh probe-then-reland path (run "
        "scripts/land_squash.sh probe, resolve or compose, then "
        "scripts/land_squash.sh land under the merge lock); operator escape "
        "for dead residue only (done-lock.sh merge-status free AND the path "
        "is not peer-live dirt): git restore --staged --worktree -- <path> "
        "per residue path; record-only allowlist path(s) are never escapable"
        + POST_LANDING_ADOPTION_REMEDY_SENTENCE
        + POST_LANDING_DECLARED_STAGE_REMEDY_SENTENCE
    )
    assert result.message == expected, result.message


def test_post_landing_staging_no_manifest_refusal_lacks_declared_stage_remedy(tmp_path, sweep_env, monkeypatch, mktemp_repo):
    """[class: REPOSITORY_TEST] The remedy sentences stay keyed on the
    manifest-resolved arm: with no resolvable run manifest (the declared-stage
    channel set, even naming the staged path itself), the rc-1 refusal is
    byte-identical to today's no-manifest render and names neither the
    declared-stage remedy nor the adopting-boundary sentence."""
    root = mktemp_repo("post-landing-remedy-no-manifest")
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    (root / "foreign.txt").write_text("foreign residue\n", encoding="utf-8")
    git(root, "add", "foreign.txt")
    monkeypatch.setenv("DONE_SWEEP_DECLARED_STAGE_PATHS", "foreign.txt\n")
    result = run_gate("post-landing-staging", ctx_for(root))
    assert result.rc == 1, result.message
    assert result.message == POST_LANDING_NO_MANIFEST_REFUSAL_PIN, result.message
    assert POST_LANDING_DECLARED_STAGE_REMEDY_SENTENCE not in result.message
    assert POST_LANDING_ADOPTION_REMEDY_SENTENCE not in result.message


def test_discover_fail_closed_on_missing_and_empty_facts_keys(tmp_path):
    """[class: REPOSITORY_TEST] Facts-first resolution is fail-closed: a
    missing facts file, a missing key, and an empty-value key each raise the
    named ValueError (never a guessed default path)."""
    root = tmp_path / "no-facts"
    root.mkdir()
    with pytest.raises(ValueError, match="cannot resolve plans_dir"):
        GateContext.discover(root)
    facts = root / ".ai-playbook" / "facts.md"
    facts.parent.mkdir()
    facts.write_text('```toml\nreviews_dir = ""\ntmp_dir = "docs/tmp/"\n```\n', encoding="utf-8")
    with pytest.raises(ValueError, match="cannot resolve plans_dir"):
        GateContext.discover(root)
    facts.write_text(
        "```toml\n"
        'plans_dir = "docs/history/plans/"\n'
        'plans_completed_dir = "docs/history/plans/completed/"\n'
        'backlog_dir = "docs/history/backlog/"\n'
        'reviews_dir = ""\n'
        'tmp_dir = "docs/tmp/"\n'
        "```\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cannot resolve reviews_dir"):
        GateContext.discover(root)
# --------------------------------------------------------------------------- #
# Plan: docs/history/plans/2026-10-05-live-claim-plan-deletion-fence.md
# Task 2: the plans-root claim fence gate (refusal, foreign report, skip).
# --------------------------------------------------------------------------- #
def _copy_reverse_squash_guard(root: Path) -> Path:
    """Copy the repo's real reverse-squash guard into the fixture repo (the
    gate's repo-local scripts/ resolution arm; still hermetic). The
    guard's sibling ``plan_shape`` import (the shared plan-shape resolver
    it reads the charter grammar from) is copied beside it, mirroring the
    deployment pair in scripts/runtime-scripts.list."""
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    target = scripts / "reverse_squash_guard.py"
    target.write_text(
        (SCRIPTS_DIR / "reverse_squash_guard.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (scripts / "plan_shape.py").write_text(
        (SCRIPTS_DIR / "plan_shape.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


def _seed_claim_fence_boundary(
    root: Path, plan_rel: str, claim_rel: str, claim: bool = True
) -> str:
    """One tracked plans-root plan with (claim=True, the default) a live
    execution claim file under the primary checkout's claims home, plus
    the Step 0 marker pair and run manifest anchored at the plan commit
    (the gate's start_commit); claim=False skips the claim file for the
    unclaimed-deletion warning leg; returns the boundary commit sha."""
    (root / "docs/history/plans").mkdir(parents=True, exist_ok=True)
    (root / plan_rel).write_text("fenced plan\n", encoding="utf-8")
    git(root, "add", "-f", plan_rel)
    git(root, "commit", "-m", "plan", "-q")
    start = git(root, "rev-parse", "HEAD").stdout.strip()
    if claim:
        claim_path = root / claim_rel
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text("execution claim\n", encoding="utf-8")
    now = time.time()
    make_marker(root, now - 3600, os.getpid())
    current = make_marker(root, now, os.getpid())
    _seed_run_manifest(
        root, "run-claim-fence", current.name, str(root), now, start_commit=start
    )
    return start


def test_plans_root_claim_fence_gate_refusal_foreign_report_and_skip(
    tmp_path, sweep_env, mktemp_repo
):
    """[class: REPOSITORY_TEST] Given a scratch run whose own (ledger-owned)
    range deletes a claimed plans-root file, expects the failed bucket naming
    the deleted path and the live claim; given the same deletion inside a
    foreign commit (no owned-commits ledger entry), expects a named report
    line and no failure; given the same deletion with no live claim at all,
    expects a pass whose gate message carries the child's unclaimed-deletion
    warning lines and nothing parsed as a refusal block; given an empty run
    range, expects the warning skip naming the reason."""
    plan_rel = "docs/history/plans/2026-09-20-fenced.md"
    claim_rel = "docs/tmp/execution-claims/fenced.md"

    # Own-commit refusal: the deleting commit sits in the owned-commits ledger.
    root = mktemp_repo("claim-fence-own")
    write_facts(root)
    _copy_reverse_squash_guard(root)
    _seed_claim_fence_boundary(root, plan_rel, claim_rel)
    git(root, "rm", "-q", plan_rel)
    git(root, "commit", "-m", "delete the claimed plan", "-q")
    owned_sha = git(root, "rev-parse", "HEAD").stdout.strip()
    done_session = root / "docs" / "tmp" / "done-session"
    (done_session / "owned-commits-run-claim-fence.txt").write_text(
        owned_sha + "\n", encoding="utf-8"
    )
    result = run_gate("plans-root-claim-fence", ctx_for(root))
    assert result.rc == 1, result.message
    assert plan_rel in result.message
    assert claim_rel in result.message
    assert "Plans-Deletion-Ack" in result.message

    # Foreign-commit report: the same deletion, no ledger entry (the commit
    # is foreign to this run); reported, never a gate failure.
    foreign_root = mktemp_repo("claim-fence-foreign")
    write_facts(foreign_root)
    _copy_reverse_squash_guard(foreign_root)
    _seed_claim_fence_boundary(foreign_root, plan_rel, claim_rel)
    git(foreign_root, "rm", "-q", plan_rel)
    git(foreign_root, "commit", "-m", "peer deletes the claimed plan", "-q")
    foreign = run_gate("plans-root-claim-fence", ctx_for(foreign_root))
    reported = foreign.message + "\n".join(foreign.warnings)
    assert foreign.rc == 0, reported
    assert plan_rel in reported
    assert "foreign" in reported

    # Unclaimed-deletion warning leg: the same deletion with no live claim
    # anywhere is the warning class; the child exits 0 and the gate passes
    # with the warning lines riding the gate message, nothing parsed as a
    # refusal block (plan
    # 2026-10-11-landing-deleted-unclaimed-execution-ready-plan Task 1).
    unclaimed_root = mktemp_repo("claim-fence-unclaimed")
    write_facts(unclaimed_root)
    _copy_reverse_squash_guard(unclaimed_root)
    _seed_claim_fence_boundary(unclaimed_root, plan_rel, claim_rel, claim=False)
    git(unclaimed_root, "rm", "-q", plan_rel)
    git(unclaimed_root, "commit", "-m", "delete the unclaimed plan", "-q")
    unclaimed = run_gate("plans-root-claim-fence", ctx_for(unclaimed_root))
    assert unclaimed.rc == 0, unclaimed.message
    assert "claim-fence-warning:" in unclaimed.message
    assert plan_rel in unclaimed.message
    assert "sanctioned exits" in unclaimed.message
    assert "deleted while its claim is live" not in unclaimed.message
    assert "gate failed" not in unclaimed.message

    # Empty-range warning skip: no commits since the Step 0 boundary.
    empty_root = mktemp_repo("claim-fence-empty")
    write_facts(empty_root)
    _copy_reverse_squash_guard(empty_root)
    _seed_claim_fence_boundary(empty_root, plan_rel, claim_rel)
    skip = run_gate("plans-root-claim-fence", ctx_for(empty_root))
    assert skip.rc == 0, skip.message
    assert "warning skip" in skip.message
    assert "empty" in skip.message


def test_post_checkpoint_tree_classifies_clean(tmp_path):
    """[class: REPOSITORY_TEST] The wip-auto-checkpoint plan Task 2's
    classification fixture: the dirt classification (the porcelain reader)
    sees a post-checkpoint tree - a clean worktree with `wip:` checkpoint
    commits in history - as clean, proving checkpoint commits are
    first-class (the classification reads working-tree state, never
    history, so a mechanical `wip:` safety commit never registers as
    dirt)."""
    root = make_repo(tmp_path, "wip-checkpoint-clean")
    write_facts(root)
    (root / "work.txt").write_text("owned work\n", encoding="utf-8")
    git(root, "add", ".ai-playbook/facts.md", "work.txt")
    git(root, "commit", "-m", "wip: checkpoint before quota pause", "-q")
    ctx = ctx_for(root)
    assert lib._porcelain_lines(ctx, ".") == []
    assert git(root, "status", "--porcelain", "-uall").stdout == ""
    subjects = git(root, "log", "--format=%s").stdout.splitlines()
    assert any(s.startswith("wip:") for s in subjects)


def _landing_repo(tmp_path):
    """Hermetic fixture repo for the landing-roster guard tests."""
    root = tmp_path / "landing-repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.test")
    git(root, "config", "user.name", "t")
    (root / "seed.txt").write_text("seed\n", encoding="utf-8")
    write_facts(root)
    git(root, "add", ".")
    git(root, "commit", "-qm", "seed")
    return root


def test_landing_roster_membership_and_absence():
    import done_sweep_gates_lib as lib

    retained = {
        "docs-tmp-sweep", "confluence-hygiene", "sensitive-data-scan",
        "em-dash-scan", "doc-registry", "review-staging", "plan-readiness",
        "foreign-staging", "post-landing-staging", "plans-root-claim-fence",
        "archive-ceremony", "execute-plan-closeout", "plans-archive-twin",
    }
    assert retained <= set(lib.LANDING_GATES)
    assert "backlog-inbox" not in lib.LANDING_GATES
    assert "vim-swap-sweep" not in lib.LANDING_GATES
    assert lib.PHASES["landing"] == lib.LANDING_GATES
    for gate in ("instruction-size", "description-length"):
        assert gate in lib.LANDING_GATES
        assert gate in lib.LANDING_WARNING_GATES


def test_landing_warning_posture_run_path(tmp_path, monkeypatch):
    import done_sweep_gates_lib as lib

    root = _landing_repo(tmp_path)
    ctx = ctx_for(root)
    warning = ("instruction-size", "description-length")

    def fake_gate(gate, rc):
        def _g(_ctx):
            return lib.GateResult(gate, rc, f"{gate} fixture verdict", warnings=[])
        return _g

    # Landing run: the two warning-posture breaches downgrade to rc 0 with a
    # warning line naming each gate; every other gate deterministic pass.
    for gate in lib.LANDING_GATES:
        monkeypatch.setitem(
            lib.GATES, gate, fake_gate(gate, 1 if gate in warning else 0)
        )
    results = lib.run_phase("landing", ctx)
    by_gate = {r.gate: r for r in results}
    for gate in warning:
        assert by_gate[gate].rc == 0
        assert any("warning posture" in w and gate in w for w in by_gate[gate].warnings)
    assert lib.phase_exit(results) == 0

    # The same breaches at the gate level still refuse: the warning posture
    # is landing-run-scoped, and the retained predicates themselves are
    # unchanged (a direct run_gate call answers the modeled failure).
    for gate in warning:
        monkeypatch.setitem(lib.GATES, gate, fake_gate(gate, 1))
        assert lib.run_gate(gate, ctx).rc == 1


# --------------------------------------------------------------------------- #
# Boundary-class roster split (plan: worktree-done-boundary-gate-roster-split)
# The per-task landing roster is LANDING_GATES minus post-landing-staging
# exactly; the final-closeout class keeps the full roster byte-identically;
# an invalid class value is the usage-error tool error (exit 3).
# --------------------------------------------------------------------------- #
EXPECTED_PER_TASK_ROSTER = [
    gate for gate in EXPECTED_LANDING_ROSTER if gate != "post-landing-staging"
]


def test_per_task_roster_composition(tmp_path, sweep_env, monkeypatch, capsys):
    """[class: REPOSITORY_TEST] Roster composition witness: with the gate
    registry stubbed, the per-task class executes exactly LANDING_GATES minus
    post-landing-staging, and the same stubbed context under the
    final-closeout class executes the full LANDING_GATES set."""
    root = make_repo(tmp_path, "boundary-class-roster", gitignore_docs=True)
    write_facts(root)
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    executed: list[str] = []

    def fake_gate(gate_id, rc=0):
        def _run(ctx):
            executed.append(gate_id)
            return lib.GateResult(gate_id, rc, "stub ok", warnings=[])
        return _run

    real = dict(lib.GATES)
    for gate_id in EXPECTED_LANDING_ROSTER:
        monkeypatch.setitem(lib.GATES, gate_id, fake_gate(gate_id))
    rc = lib.main(["landing", "--boundary-class", "per-task"])
    assert rc == 0
    assert executed == EXPECTED_PER_TASK_ROSTER
    executed.clear()
    rc = lib.main(["landing", "--boundary-class", "final-closeout"])
    assert rc == 0
    assert executed == EXPECTED_LANDING_ROSTER


def test_per_task_warning_posture_kept(tmp_path, sweep_env, monkeypatch, capsys):
    """[class: REPOSITORY_TEST] Warning-posture witness: given the per-task
    class with the warning-class instruction-size gate stubbed to breach, the
    landing phase exits 0 carrying that gate's warning-posture line, proving
    the per-task roster keeps the warning set."""
    root = make_repo(tmp_path, "boundary-class-warning", gitignore_docs=True)
    write_facts(root)
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))

    def fake_gate(gate_id):
        def _run(ctx):
            if gate_id == "instruction-size":
                return lib.GateResult(
                    gate_id, 1, "stub breach", warnings=[]
                )
            return lib.GateResult(gate_id, 0, "stub ok", warnings=[])
        return _run

    for gate_id in EXPECTED_LANDING_ROSTER:
        monkeypatch.setitem(lib.GATES, gate_id, fake_gate(gate_id))
    rc = lib.main(["landing", "--boundary-class", "per-task"])
    out = capsys.readouterr().out
    assert rc == 0
    assert any(
        "warning posture: instruction-size" in ln for ln in out.splitlines()
    )


def test_invalid_boundary_class_tool_error(tmp_path, sweep_env, monkeypatch, capsys):
    """[class: REPOSITORY_TEST] An invalid boundary class value is the
    usage-error tool error (exit 3 with an OUTCOME: tool_error line), never a
    silent default to the full roster."""
    root = make_repo(tmp_path, "boundary-class-invalid", gitignore_docs=True)
    write_facts(root)
    make_marker(root, time.time(), os.getpid())
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    rc = lib.main(["landing", "--boundary-class", "bogus"])
    out = capsys.readouterr().out
    assert rc == 3
    assert out.rstrip().endswith("OUTCOME: tool_error")


def test_per_task_passes_foreign_staged_entry(
    tmp_path, sweep_env, monkeypatch, mktemp_repo
):
    """[class: REPOSITORY_TEST] Safety witness pass arm: given the per-task
    class with a foreign staged entry fabricated inside the fixture repo only
    (git add in the fixture, no resolvable run manifest, never the real
    primary index), the landing phase passes on the scoped roster. Every other
    gate is stubbed green so the arm isolates the post-landing-staging
    subtraction; DONE_LOCK_SCRIPT is pinned to the repo-local done-lock.sh and
    MERGE_LOCK_ROOT to a temp root so the refuse arm is consulted, not the
    indeterminate arm."""
    root = mktemp_repo("boundary-class-safety-pass")
    write_facts(root)
    write_landing_validator_stubs(root)
    make_marker(root, time.time(), os.getpid())
    (root / "foreign_peer.txt").write_text("peer staged byte\n", encoding="utf-8")
    git(root, "add", "foreign_peer.txt")
    lock_root = Path(tempfile.mkdtemp(prefix="boundary-class-lock-"))
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    monkeypatch.setenv("MERGE_LOCK_ROOT", str(lock_root))

    def fake_gate(gate_id):
        def _run(ctx):
            return lib.GateResult(gate_id, 0, "stub ok", warnings=[])
        return _run

    for gate_id in EXPECTED_PER_TASK_ROSTER:
        monkeypatch.setitem(lib.GATES, gate_id, fake_gate(gate_id))
    rc = lib.main(["landing", "--boundary-class", "per-task"])
    assert rc == 0


def test_final_closeout_refuses_foreign_staged_entry(
    tmp_path, sweep_env, monkeypatch, mktemp_repo, capsys
):
    """[class: REPOSITORY_TEST] Safety witness refuse arm: the same fabricated
    foreign staged entry under the final-closeout class refuses with today's
    message shape (the post-landing-staging staged-residue refusal)."""
    root = mktemp_repo("boundary-class-safety-refuse")
    write_facts(root)
    write_landing_validator_stubs(root)
    make_marker(root, time.time(), os.getpid())
    (root / "foreign_peer.txt").write_text("peer staged byte\n", encoding="utf-8")
    git(root, "add", "foreign_peer.txt")
    lock_root = Path(tempfile.mkdtemp(prefix="boundary-class-lock-"))
    monkeypatch.setenv("DONE_SWEEP_REPO_ROOT", str(root))
    monkeypatch.setenv("DONE_LOCK_SCRIPT", str(POST_LANDING_DONE_LOCK))
    monkeypatch.setenv("MERGE_LOCK_ROOT", str(lock_root))

    def fake_gate(gate_id):
        def _run(ctx):
            return lib.GateResult(gate_id, 0, "stub ok", warnings=[])
        return _run

    for gate_id in EXPECTED_PER_TASK_ROSTER:
        monkeypatch.setitem(lib.GATES, gate_id, fake_gate(gate_id))
    rc = lib.main(["landing", "--boundary-class", "final-closeout"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "foreign_peer.txt" in out
