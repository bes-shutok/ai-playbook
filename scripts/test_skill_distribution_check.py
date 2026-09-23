"""Fixture tests for the skill distribution integrity check."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "skill_distribution_check.py"


def run_check(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(CHECKER), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


SOURCE_FILES = {
    "SKILL.md": "---\nname: demo\nmetadata:\n  version: 1.0.0\n---\n\n# Demo\n",
    "guide.md": "# Guide\n\nAbstract guidance only.\n",
}


def make_skill(root: Path, files: dict[str, str]) -> Path:
    skill = root / "demo"
    skill.mkdir(parents=True)
    for name, body in files.items():
        (skill / name).write_text(body, encoding="utf-8")
    return skill


def make_source(tmp_path, files=None, version="1.0.0"):
    src_root = tmp_path / "src"
    src_root.mkdir()
    body = dict(files or SOURCE_FILES)
    if version:
        body["SKILL.md"] = (
            f"---\nname: demo\nmetadata:\n  version: {version}\n---\n\n# Demo\n"
        )
    make_skill(src_root, body)
    return src_root / "demo"


def copy_skill(src: Path, dest_root: Path) -> Path:
    dest_root.mkdir(parents=True, exist_ok=True)
    dest = dest_root / src.name
    shutil.copytree(src, dest)
    return dest


def test_default_source_resolves_from_repo_root(tmp_path):
    repo = tmp_path / "repo"
    (repo / "agents" / "skills").mkdir(parents=True)
    (repo / ".git").mkdir()
    make_skill(repo / "agents" / "skills", SOURCE_FILES)
    subdir = repo / "agents" / "skills" / "sub"
    subdir.mkdir()
    dest_root = tmp_path / "dest"
    dest_root.mkdir()
    proc = run_check(
        "--skill", "demo", "--dest", dest_root, cwd=subdir
    )
    assert proc.returncode == 1, proc.stdout
    assert "MISSING" in proc.stdout
    # exit 1 (destination scanned) rather than 2 proves the default source
    # resolved from the repo root, not from the cwd subdirectory


def test_stale_sibling_detected(tmp_path):
    src = make_source(tmp_path)
    dest_root = tmp_path / "dest"
    dest = copy_skill(src, dest_root)
    (dest / "guide.md").write_text("# Guide\n\ndrifted\n", encoding="utf-8")
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert proc.returncode == 1
    assert "STALE" in proc.stdout
    assert str(dest) in proc.stdout


def test_missing_destination_reported(tmp_path):
    src = make_source(tmp_path)
    dest_root = tmp_path / "dest"
    dest_root.mkdir()
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert proc.returncode == 1
    assert "MISSING" in proc.stdout


def test_stampless_drift_requires_consent(tmp_path):
    src = make_source(tmp_path, version=None)
    dest_root = tmp_path / "dest"
    dest = copy_skill(src, dest_root)
    (dest / "guide.md").write_text("# Guide\n\ndrifted\n", encoding="utf-8")
    plain = run_check("--skill", "demo", "--source", src, "--dest", dest_root, "--refresh")
    assert plain.returncode == 1
    assert str(dest) in plain.stdout
    assert (dest / "guide.md").read_text(encoding="utf-8").endswith("drifted\n")
    assert "downgrade" in plain.stdout.lower()
    consented = run_check(
        "--skill", "demo", "--source", src, "--dest", dest_root, "--refresh", "--downgrade"
    )
    assert consented.returncode == 0
    assert (dest / "guide.md").read_text(encoding="utf-8").endswith("Abstract guidance only.\n")


def test_equal_stamp_differing_digest_requires_consent(tmp_path):
    src = make_source(tmp_path)
    dest_root = tmp_path / "dest"
    dest = copy_skill(src, dest_root)
    (dest / "guide.md").write_text("# Guide\n\ndrifted\n", encoding="utf-8")
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert proc.returncode == 1
    assert "STALE" in proc.stdout
    before = (dest / "guide.md").read_text(encoding="utf-8")
    refresh = run_check("--skill", "demo", "--source", src, "--dest", dest_root, "--refresh")
    assert refresh.returncode == 1
    assert (dest / "guide.md").read_text(encoding="utf-8") == before


def test_version_ordering_numeric(tmp_path):
    src = make_source(tmp_path, version="9.0.0")
    dest_root = tmp_path / "dest"
    copy_skill(src, dest_root)
    dest = dest_root / "demo"
    (dest / "SKILL.md").write_text(
        "---\nname: demo\nmetadata:\n  version: 10.0.0\n---\n\n# Demo\n",
        encoding="utf-8",
    )
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert proc.returncode == 1
    assert "NEWER" in proc.stdout


def test_older_destination_refreshes_by_default(tmp_path):
    src = make_source(tmp_path, version="2.0.0")
    dest_root = tmp_path / "dest"
    dest_root.mkdir(parents=True)
    dest = dest_root / "demo"
    make_skill(
        dest_root,
        {
            "SKILL.md": "---\nname: demo\nmetadata:\n  version: 1.0.0\n---\n\n# Demo\n",
            "guide.md": "# Guide\n\nolder copy\n",
        },
    )
    assert dest.exists()
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root, "--refresh")
    assert proc.returncode == 0, proc.stdout
    assert (dest / "guide.md").read_text(encoding="utf-8").endswith("Abstract guidance only.\n")
    follow = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert follow.returncode == 0


def test_newer_destination_preserved(tmp_path):
    src = make_source(tmp_path, version="1.0.0")
    dest_root = tmp_path / "dest"
    dest_root.mkdir(parents=True)
    make_skill(
        dest_root,
        {
            "SKILL.md": "---\nname: demo\nmetadata:\n  version: 2.0.0\n---\n\n# Demo\n",
            "guide.md": "# Guide\n\nnewer drifted copy\n",
        },
    )
    dest = dest_root / "demo"
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert proc.returncode == 1
    assert "NEWER" in proc.stdout
    assert (dest / "guide.md").read_text(encoding="utf-8").endswith("newer drifted copy\n")


def test_downgrade_requires_flag(tmp_path):
    src = make_source(tmp_path, version="1.0.0")
    dest_root = tmp_path / "dest"
    dest_root.mkdir(parents=True)
    make_skill(
        dest_root,
        {
            "SKILL.md": "---\nname: demo\nmetadata:\n  version: 2.0.0\n---\n\n# Demo\n",
            "guide.md": "# Guide\n\nnewer drifted copy\n",
        },
    )
    dest = dest_root / "demo"
    proc = run_check(
        "--skill", "demo", "--source", src, "--dest", dest_root, "--refresh", "--downgrade"
    )
    assert proc.returncode == 0, proc.stdout
    assert (dest / "guide.md").read_text(encoding="utf-8").endswith("Abstract guidance only.\n")


def test_refresh_removes_extraneous_files(tmp_path):
    src = make_source(tmp_path, version=None)
    dest_root = tmp_path / "dest"
    dest = copy_skill(src, dest_root)
    (dest / "extra.md").write_text("# Extra\n", encoding="utf-8")
    proc = run_check(
        "--skill", "demo", "--source", src, "--dest", dest_root, "--refresh", "--downgrade"
    )
    assert proc.returncode == 0, proc.stdout
    assert not (dest / "extra.md").exists()
    follow = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert follow.returncode == 0
    assert "CURRENT" in follow.stdout


def test_refresh_is_idempotent(tmp_path):
    src = make_source(tmp_path)
    dest_root = tmp_path / "dest"
    dest = copy_skill(src, dest_root)
    (dest / "guide.md").write_text("# Guide\n\ndrifted\n", encoding="utf-8")
    first = run_check(
        "--skill", "demo", "--source", src, "--dest", dest_root, "--refresh", "--downgrade"
    )
    assert first.returncode == 0
    second = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert second.returncode == 0
    assert "CURRENT" in second.stdout


def test_symlink_alias_reported_once(tmp_path):
    src = make_source(tmp_path)
    phys = tmp_path / "dest-physical"
    copy_skill(src, phys)
    (phys / "demo" / "guide.md").write_text("# Guide\n\ndrifted\n", encoding="utf-8")
    alias = tmp_path / "dest-alias"
    alias.symlink_to(phys)
    proc = run_check("--skill", "demo", "--source", src, "--dest", phys, "--dest", alias)
    assert proc.returncode == 1
    stale_rows = [line for line in proc.stdout.splitlines() if "STALE" in line]
    assert len(stale_rows) == 1, proc.stdout
    assert str(phys) in stale_rows[0] and str(alias) in stale_rows[0]


def test_destination_resolving_to_source_skipped(tmp_path):
    src = make_source(tmp_path)
    link = tmp_path / "dest-link"
    link.symlink_to(src.parent, target_is_directory=True)
    proc = run_check("--skill", "demo", "--source", src, "--dest", link)
    assert proc.returncode == 0, proc.stdout
    assert "SKIP" in proc.stdout


def test_current_destination_exit_zero(tmp_path):
    src = make_source(tmp_path)
    dest_root = tmp_path / "dest"
    copy_skill(src, dest_root)
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root)
    assert proc.returncode == 0
    assert "CURRENT" in proc.stdout


def test_usage_error_exit_two(tmp_path):
    proc = run_check()
    assert proc.returncode == 2
    assert "usage" in (proc.stdout + proc.stderr).lower()


def test_json_report_shape(tmp_path):
    src = make_source(tmp_path)
    dest_root = tmp_path / "dest"
    copy_skill(src, dest_root)
    proc = run_check("--skill", "demo", "--source", src, "--dest", dest_root, "--json")
    payload = json.loads(proc.stdout)
    assert isinstance(payload, list) and len(payload) == 1
    row = payload[0]
    assert row["classification"] == "CURRENT"
    assert "resolved_path" in row and "platform_root" in row
