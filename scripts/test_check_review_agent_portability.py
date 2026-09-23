"""Fixture tests for the review-agents portability regression checker."""

import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_review_agent_portability.py"


def run_checker(*paths):
    return subprocess.run(
        [sys.executable, str(CHECKER), *[str(p) for p in paths]],
        capture_output=True,
        text=True,
    )


def make_catalog(tmp_path, body):
    catalog = tmp_path / "catalog.md"
    catalog.write_text(body + "\n", encoding="utf-8")
    return catalog


def test_unmarked_framework_token_fails(tmp_path):
    catalog = make_catalog(tmp_path, "Check Spring bean wiring before approval.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "catalog.md:1:" in proc.stdout
    assert "Spring" in proc.stdout
    assert "framework" in proc.stdout.lower()


def test_placement_marker_excuses_line(tmp_path):
    catalog = make_catalog(
        tmp_path,
        "Check Spring bean wiring before approval. <!-- portability: abstract -->",
    )
    proc = run_checker(catalog)
    assert proc.returncode == 0, proc.stdout


def test_placement_marker_excuses_table_row(tmp_path):
    body = (
        "| Risk | Signals |\n"
        "|---|---|\n"
        "| Messaging | Kafka consumer lag, RocketMQ backlog <!-- portability: abstract --> |\n"
    )
    catalog = make_catalog(tmp_path, body)
    proc = run_checker(catalog)
    assert proc.returncode == 0, proc.stdout


def test_repo_path_token_detected(tmp_path):
    catalog = make_catalog(tmp_path, "Config lives at /Users/dev/repo/config.yaml.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "repo-path" in proc.stdout


def test_build_tool_token_detected(tmp_path):
    catalog = make_catalog(tmp_path, "Run `mvn verify` before the panel.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "build-tool" in proc.stdout


def test_test_suffix_token_detected(tmp_path):
    catalog = make_catalog(tmp_path, "Flag the missing `OrderServiceTest` naming convention.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "test-suffix" in proc.stdout


def test_ticket_prefix_detected(tmp_path):
    catalog = make_catalog(tmp_path, "Cite PROJ-1234 in the finding header.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "ticket-prefix" in proc.stdout


def test_language_syntax_token_detected(tmp_path):
    catalog = make_catalog(tmp_path, "Expect UnsupportedOperationException on the stub.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "language-syntax" in proc.stdout


def test_language_name_token_detected(tmp_path):
    catalog = make_catalog(tmp_path, "Compilers enforce this for Java and Kotlin.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "language-name" in proc.stdout


def test_qualified_identifier_detected(tmp_path):
    catalog = make_catalog(tmp_path, "Prefer `java.time` for date formatting.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "language-syntax" in proc.stdout


def test_windows_single_backslash_path_detected(tmp_path):
    catalog = make_catalog(tmp_path, r"Config lives at C:\Users\dev\config.yaml.")
    proc = run_checker(catalog)
    assert proc.returncode == 1
    assert "repo-path" in proc.stdout


def test_clean_catalog_passes(tmp_path):
    catalog = make_catalog(
        tmp_path,
        "Verify the claim against the module's declared API surface and its tests.",
    )
    proc = run_checker(catalog)
    assert proc.returncode == 0, proc.stdout
