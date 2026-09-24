#!/usr/bin/env python3
"""Wrapper-dispatch suite for done_sweep_gates.sh (plan Task 1, finding F2).

Plan: docs/plans/2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md.
Every test exercises the real wrapper script (bash) against a hermetic fixture
repo under pytest ``tmp_path``: the wrapper resolves its lib next to itself,
so these tests run the repo's own scripts/done_sweep_gates.sh.

Hermeticity: DONE_SWEEP_REPO_ROOT points at the fixture repo; the runtime
home and user facts are redirected like the lib suite's ``sweep_env``.
"""

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
WRAPPER = SCRIPTS_DIR / "done_sweep_gates.sh"


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
        'plans_dir = "docs/plans/"\n'
        'plans_completed_dir = "docs/plans/completed/"\n'
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
