"""Contract tests for the review posting landing receipt checker.

Each test builds a minimal staging document in tmp_path and invokes
scripts/check_review_landing_receipt.py as a subprocess, asserting the
exit code and (on failure) the named error class on stderr.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts" / "check_review_landing_receipt.py"


def run_checker(doc: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(doc)],
        capture_output=True,
        text=True,
    )


def finding_block(file: str, line: int, comment: str, status: str = "posted") -> str:
    return (
        f"### F1\n"
        f"- **File**: `{file}`\n"
        f"- **Line**: {line}\n"
        f"- **Status**: {status}\n"
        f"#### Comment\n"
        f"{comment}\n"
    )


def receipt_doc(
    header: str,
    findings: str,
    summary: str | None = None,
    lines: list[str] | None = None,
) -> str:
    parts = [f"Status: {header}\n\n## Findings\n\n", findings]
    if lines is not None or summary is not None:
        parts.append("## Landing receipt\n")
        if summary is not None:
            parts.append(summary + "\n")
        for line in lines or []:
            parts.append(line + "\n")
    return "".join(parts)


def landing_line(file: str, line: int, fragment: str, comment: str, landed: str) -> str:
    return (
        f'landing: file={file} line={line} fragment="{fragment}" '
        f"comment={comment} landed={landed}"
    )


def test_posted_record_with_complete_receipt_passes(tmp_path):
    doc = tmp_path / "staging.md"
    findings = (
        finding_block("src/service.py", 42, "Retry once after a short pause.")
        + finding_block("src/queue.py", 108, "Dead-letter after three failures.")
    )
    doc.write_text(
        receipt_doc(
            "POSTED",
            findings,
            summary="intended=2 landed=2",
            lines=[
                landing_line("src/service.py", 42, "Retry once after a short pause", "2210456123", "yes"),
                landing_line("src/queue.py", 108, "Dead-letter after three failures", "2210456124", "yes"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 0, result.stderr


def test_posted_record_missing_receipt_section_fails(tmp_path):
    doc = tmp_path / "staging.md"
    doc.write_text(
        receipt_doc("POSTED", finding_block("src/service.py", 42, "Retry once.")),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1
    assert "missing landing receipt section" in result.stderr


def test_posted_record_missing_one_finding_line_fails(tmp_path):
    doc = tmp_path / "staging.md"
    findings = (
        finding_block("src/service.py", 42, "Retry once after a short pause.")
        + finding_block("src/queue.py", 108, "Dead-letter after three failures.")
    )
    doc.write_text(
        receipt_doc(
            "POSTED",
            findings,
            summary="intended=2 landed=2",
            lines=[
                landing_line("src/service.py", 42, "Retry once after a short pause", "2210456123", "yes"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1
    assert "landing line" in result.stderr or "census" in result.stderr


def test_posted_finding_covered_by_pending_pair_fails(tmp_path):
    doc = tmp_path / "staging.md"
    findings = (
        finding_block("src/posted.py", 42, "Retry once after a short pause.")
        + finding_block("src/pending.py", 7, "Dead-letter after three failures.", status="pending")
    )
    doc.write_text(
        receipt_doc(
            "POSTED",
            findings,
            summary="intended=1 landed=1",
            lines=[
                landing_line("src/pending.py", 7, "Dead-letter after three failures", "2210456124", "yes"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1
    assert "coverage gap" in result.stderr


def test_posted_record_with_unlanded_line_fails(tmp_path):
    doc = tmp_path / "staging.md"
    doc.write_text(
        receipt_doc(
            "POSTED",
            finding_block("src/a.py", 42, "Retry once after a short pause."),
            summary="intended=1 landed=0",
            lines=[
                landing_line("src/a.py", 42, "Retry once after a short pause", "", "no"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1
    assert "census" in result.stderr


def test_receipt_identity_mismatch_fails(tmp_path):
    doc = tmp_path / "staging.md"
    doc.write_text(
        receipt_doc(
            "POSTED",
            finding_block("src/service.py", 42, "Retry once after a short pause."),
            summary="intended=1 landed=1",
            lines=[
                landing_line("src/other.py", 42, "Retry once after a short pause", "2210456123", "yes"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1
    assert "file" in result.stderr or "line" in result.stderr


def test_receipt_fragment_not_in_comment_fails(tmp_path):
    doc = tmp_path / "staging.md"
    doc.write_text(
        receipt_doc(
            "POSTED",
            finding_block("src/service.py", 42, "Retry once after a short pause."),
            summary="intended=1 landed=1",
            lines=[
                landing_line("src/service.py", 42, "fragment absent from comment", "2210456123", "yes"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1
    assert "fragment" in result.stderr


def test_receipt_census_mismatch_fails(tmp_path):
    doc = tmp_path / "staging.md"
    doc.write_text(
        receipt_doc(
            "POSTED",
            finding_block("src/service.py", 42, "Retry once after a short pause."),
            summary="intended=1 landed=0",
            lines=[
                landing_line("src/service.py", 42, "Retry once after a short pause", "2210456123", "yes"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1
    assert "intended" in result.stderr or "census" in result.stderr


def test_incomplete_record_with_unlanded_lines_passes(tmp_path):
    doc = tmp_path / "staging.md"
    findings = (
        finding_block("src/service.py", 42, "Retry once after a short pause.", status="posted")
        + finding_block("src/queue.py", 108, "Dead-letter after three failures.", status="pending")
    )
    doc.write_text(
        receipt_doc(
            "INCOMPLETE (posting incomplete; unlanded findings remain pending)",
            findings,
            summary="intended=2 landed=1",
            lines=[
                landing_line("src/service.py", 42, "Retry once after a short pause", "2210456123", "yes"),
                landing_line("src/queue.py", 108, "Dead-letter after three failures", "", "no"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 0, result.stderr


def test_incomplete_record_missing_unlanded_lines_fails(tmp_path):
    doc = tmp_path / "staging.md"
    findings = (
        finding_block("src/service.py", 42, "Retry once after a short pause.", status="posted")
        + finding_block("src/queue.py", 108, "Dead-letter after three failures.", status="pending")
    )
    doc.write_text(
        receipt_doc(
            "INCOMPLETE (posting incomplete; unlanded findings remain pending)",
            findings,
            summary="intended=2 landed=1",
            lines=[
                landing_line("src/service.py", 42, "Retry once after a short pause", "2210456123", "yes"),
            ],
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 1


def test_unposted_and_plan_records_are_noops(tmp_path):
    findings = finding_block("src/service.py", 42, "Retry once after a short pause.")
    for header in ("STAGED (not yet posted)", "STAGED"):
        doc = tmp_path / "staging.md"
        doc.write_text(receipt_doc(header, findings), encoding="utf-8")
        result = run_checker(doc)
        assert result.returncode == 0, (header, result.stderr)


def test_phase3_style_suffixed_posted_record_is_noop(tmp_path):
    doc = tmp_path / "staging.md"
    doc.write_text(
        receipt_doc(
            "POSTED (review record posted)",
            finding_block("docs/x.md", 1, "Some plan-review style comment."),
        ),
        encoding="utf-8",
    )
    result = run_checker(doc)
    assert result.returncode == 0, result.stderr
