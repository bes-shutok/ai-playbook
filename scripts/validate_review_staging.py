#!/usr/bin/env python3
"""Validate review staging markdown per review-staging skill.

Exit 0 when valid (soft mode may print warnings). Exit 1 when invalid in --hard mode.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import facts_paths
except ImportError:  # pragma: no cover
    facts_paths = None  # type: ignore

STAGING_NAME_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}-)?"
    r"(?:"
    r"branch-review|.+?-branch-review|"
    r"plan-review|.+?-plan-review|"
    r"rfc-review|.+?-rfc-review|"
    r"confluence-review|.+?-confluence-review|"
    r"PR-\d+"
    r").+"
    r"(?:-r\d+|-(?:light|full|review-local))?\.md$",
    re.IGNORECASE,
)
ROUND_SUFFIX_RE = re.compile(r"-r(\d+)\.md$", re.IGNORECASE)
MEDIUM_PLUS_VERDICT_RE = re.compile(
    r"(\d+)\s+Medium\+?\s+findings(?:\s+accepted\s+for\s+fix)?",
    re.IGNORECASE,
)
CLEAR_ROUND_RE = re.compile(r"0\s+Medium\+?\s+findings;\s*clear\s+round", re.IGNORECASE)
FINDING_HEADER_RE = re.compile(r"^(?:F(\d+)|(\d+)\.)\s", re.MULTILINE)
STUB_BYTE_THRESHOLD = 2000
LEGACY_MIN_BLOCK_CHARS = 120
# The 7 default review-panel agents per review-panel-selection.md. A full code
# review must show each as `complete` (ran). "folded into Solo" / Raw=0-skipped
# for all of them indicates the panel never launched (Solo-collapse). See UL#190.
DEFAULT_PANEL_AGENTS = (
    "quality",
    "implementation",
    "testing",
    "simplification",
    "documentation",
    "architecture",
    "security",
)
VALID_DISCARD_REASONS = frozenset({
    "duplicate",
    "already-mitigated",
    "false-positive",
    "out-of-scope",
    "prior-review",
    "insufficient-evidence",
    "severity-merged",
    "noise",
    "assumption-invalid",
    "downstream-pr",
    "agent-failed",
    "agent-skipped",
    "invalid-anchor",
    "excerpt-mismatch",
    "wrong-owner",
})


def finding_has_comment_and_analysis(block: str) -> tuple[bool, bool]:
    has_comment = "#### Comment" in block
    has_analysis = "#### Analysis" in block
    return has_comment, has_analysis


def is_legacy_finding_block(block: str) -> bool:
    """Pre-gold-format rounds: ### F<N> with Status/triage bullets, no Comment/Analysis."""
    if "#### Comment" in block or "#### Analysis" in block:
        return False
    if "**Status:**" not in block and "**Triage:**" not in block:
        return False
    return len(block.strip()) >= LEGACY_MIN_BLOCK_CHARS


@dataclass
class ValidationResult:
    path: Path
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    medium_plus_expected: int = 0
    finding_sections: int = 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "path": str(self.path),
            "errors": self.errors,
            "warnings": self.warnings,
            "medium_plus_expected": self.medium_plus_expected,
            "finding_sections": self.finding_sections,
        }


def resolve_reviews_dir(start_dir: Path) -> Path:
    if facts_paths is not None:
        resolved = facts_paths.resolve_toml_key(start_dir, "reviews_dir")
        if resolved is not None:
            return resolved
    return start_dir / "docs" / "history" / "reviews"


def is_staging_review_path(path: Path) -> bool:
    name = path.name
    if not name.endswith(".md"):
        return False
    if STAGING_NAME_RE.match(name):
        return True
    if ROUND_SUFFIX_RE.search(name) and "review" in name.lower():
        return True
    return False


def extract_medium_plus_count(content: str) -> int:
    verdict_match = re.search(
        r"## Verdict for this round \(before fixes\)(.*?)(?:\n## |\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    search_blob = verdict_match.group(1) if verdict_match else content
    if CLEAR_ROUND_RE.search(search_blob):
        return 0
    match = MEDIUM_PLUS_VERDICT_RE.search(search_blob)
    if match:
        return int(match.group(1))
    counts_match = re.search(
        r"\|\s*Medium\+\s*staged\s*\|\s*(\d+)\s*\|",
        content,
        re.IGNORECASE,
    )
    if counts_match:
        return int(counts_match.group(1))
    medium_only = re.search(
        r"(\d+)\s+Medium\s+findings\s+accepted\s+for\s+fix",
        search_blob,
        re.IGNORECASE,
    )
    if medium_only:
        return int(medium_only.group(1))
    return 0


def extract_staged_count(content: str) -> int:
    staged_match = re.search(
        r"\|\s*Staged findings\s*\|\s*(\d+)\s*\|",
        content,
        re.IGNORECASE,
    )
    if staged_match:
        return int(staged_match.group(1))
    bullet_match = re.search(
        r"^-\s*Staged findings:\s*(\d+)\s*$",
        content,
        re.IGNORECASE | re.MULTILINE,
    )
    if bullet_match:
        return int(bullet_match.group(1))
    meta_match = re.search(
        r"^-\s*Findings:\s*(\d+)\s*$",
        content,
        re.IGNORECASE | re.MULTILINE,
    )
    if meta_match:
        return int(meta_match.group(1))
    return extract_medium_plus_count(content)


def split_finding_blocks(content: str) -> list[str]:
    findings_match = re.search(r"^## Findings\s*$", content, re.MULTILINE)
    if not findings_match:
        return []
    findings_section = content[findings_match.end() :]
    findings_section = re.split(r"\n## ", findings_section, maxsplit=1)[0]
    parts = re.split(r"\n(?=### )", findings_section)
    blocks: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped.startswith("### "):
            continue
        header = stripped.splitlines()[0][4:].strip()
        if FINDING_HEADER_RE.match(header + " "):
            blocks.append(stripped)
    return blocks




def stats_sidecar_path(staging_path: Path) -> Path:
    return staging_path.with_suffix(".stats.json")


def metadata_allows_stats_skip(content: str) -> bool:
    meta = re.search(r"^## Metadata\s*$", content, re.MULTILINE)
    if not meta:
        return False
    tail = content[meta.end() :]
    tail = re.split(r"\n## ", tail, maxsplit=1)[0]
    return bool(
        re.search(
            r"Stats sidecar:\s*skipped\b",
            tail,
            re.IGNORECASE,
        )
    )


def validate_discarded_findings(content: str, result: ValidationResult) -> None:
    section_match = re.search(
        r"^### Discarded findings\s*$",
        content,
        re.MULTILINE,
    )
    if not section_match:
        return
    tail = content[section_match.end() :]
    tail = re.split(r"\n### ", tail, maxsplit=1)[0]
    if re.search(r"^\s*None\.?\s*$", tail, re.MULTILINE):
        return
    for line in tail.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*Agent\s*\|", line):
            continue
        if re.match(r"^\|[-:| ]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        _agent, _sev, _pattern, _theme, reason, notes = cells[:6]
        if reason not in VALID_DISCARD_REASONS:
            result.add_warning(f"unknown discard reason code: {reason}")
        if reason == "wrong-owner" and not re.search(r"lead:\s*\w+", notes, re.IGNORECASE):
            result.add_error(
                "wrong-owner discard row missing Notes lead: <agent-id>"
            )


def validate_stats_sidecar(staging_path: Path, content: str, result: ValidationResult) -> None:
    staged_count = extract_staged_count(content)
    # Hard gate: never waive the sidecar when the doc claims staged findings.
    if metadata_allows_stats_skip(content) and staged_count == 0:
        return
    if metadata_allows_stats_skip(content) and staged_count > 0:
        result.add_error(
            "Stats sidecar: skipped is not allowed when Staged findings > 0"
        )
    sidecar = stats_sidecar_path(staging_path)
    if not sidecar.is_file():
        result.add_error(f"missing required stats sidecar: {sidecar.name}")
        return
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result.add_error(f"invalid stats sidecar JSON: {exc}")
        return
    for key in ("panel", "counts"):
        if key not in payload:
            result.add_warning(f"stats sidecar missing '{key}'")
    discarded = payload.get("discarded") or []
    for row in discarded:
        if not isinstance(row, dict):
            continue
        reason = row.get("reason")
        if reason == "wrong-owner" and not row.get("lead_agent"):
            result.add_error(
                "stats sidecar wrong-owner row missing lead_agent"
            )


def detect_solo_collapse(staging_path: Path, content: str) -> bool:
    """Detect Solo-collapse: a code review whose 7 default panel agents never ran.

    Returns True when the staging doc is a code review (not a plan/RFC/confluence
    review) AND the Panel table shows the default panel agents as folded into
    Solo / skipped while only an orchestrator-Solo row ran. See UL#190.
    """
    filename = staging_path.name.lower()
    # The filename prefix is the authoritative review-type discriminator:
    #   -code-review-r<N>  -> execute-plan Phase 3 code review (panel expected)
    #   -branch-review-    -> standalone doing-code-review branch review (panel expected)
    #   -plan-review-r<N>  -> pre-execution plan review (NON-panel; Solo OK)
    #   -rfc-review-       -> RFC review (NON-panel)
    #   -confluence-review -> Confluence review (NON-panel)
    # The Type line is NOT used as a discriminator: an execute-plan Phase 3 code
    # review is legitimately "Branch Review (Plan-based, ...)" but still runs
    # the full panel, so "Plan-based" must not exempt it.
    is_panel_review = "-code-review-r" in filename or "-branch-review-" in filename
    if not is_panel_review:
        return False

    # Parse the Panel table rows. A row is "panel-ran" for an agent if the
    # agent name appears and its status is complete (regardless of Raw count;
    # an agent may legitimately return zero findings).
    panel_section = content.split("### Panel", 1)[1] if "### Panel" in content else ""
    # Stop at the next ### subsection.
    panel_section = re.split(r"\n### ", panel_section, maxsplit=1)[0]
    folded_or_skipped = 0
    present_complete = 0
    for agent in DEFAULT_PANEL_AGENTS:
        # Match a table row mentioning this agent. Status is the 2nd column.
        row_re = re.compile(
            rf"\|\s*[^|]*\b{re.escape(agent)}\b[^|]*\s*\|\s*([^||]+)\s*\|",
            re.IGNORECASE,
        )
        match = row_re.search(panel_section)
        if not match:
            continue
        status = match.group(1).strip().lower()
        if "folded into solo" in status or status.startswith("skipped"):
            folded_or_skipped += 1
        elif status.startswith("complete"):
            present_complete += 1
    # Solo-collapse: all of the 7 default agents are folded/skipped, OR none
    # completed while a majority are folded/skipped (an orchestrator-Solo row
    # claimed completion in place of the panel).
    if folded_or_skipped >= 7:
        return True
    if present_complete == 0 and folded_or_skipped >= 4:
        return True
    return False


def validate_staging_file(path: Path, *, hard: bool = False) -> ValidationResult:
    result = ValidationResult(path=path)
    if not path.is_file():
        result.add_error("file does not exist")
        return result

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        result.add_error(f"cannot read file: {exc}")
        return result

    size = path.stat().st_size

    for heading in ("## Metadata", "## Review Statistics"):
        if heading not in content:
            result.add_error(f"missing {heading}")

    if "### Panel" not in content:
        result.add_error("missing ### Panel under Review Statistics")

    # Anti-Solo-collapse check (UL#190): a code review must show the 7 default
    # panel agents as having run, not folded into Solo / skipped. This catches
    # a wrapped doing-code-review sub-agent that had no fan-out capability and
    # silently ran an inline Solo pass.
    if "### Panel" in content and detect_solo_collapse(path, content):
        result.add_error(
            "Solo-collapse detected: the 7 default review-panel agents are "
            "'folded into Solo' or skipped, but only an orchestrator-Solo row "
            "ran. A code review must launch the full review-panel-selection.md "
            "panel (Hard Gate #1); 'Solo' is a dedup label, not a mode. See UL#190."
        )

    if "### Counts" not in content and "Agents launched" not in content:
        result.add_warning("missing ### Counts or Agents launched row")

    if "### Triage outcomes" not in content and "Pending triage" not in content:
        result.add_warning("missing ### Triage outcomes or Pending triage placeholder")

    medium_plus = extract_medium_plus_count(content)
    staged_count = extract_staged_count(content)
    result.medium_plus_expected = max(staged_count, medium_plus)
    finding_blocks = split_finding_blocks(content)
    result.finding_sections = len(finding_blocks)

    # Cross-check: Verdict claiming Medium+ cannot pair with Staged findings: 0.
    if staged_count == 0 and medium_plus > 0:
        result.add_error(
            f"verdict claims {medium_plus} Medium+ but Counts/Metadata staged findings is 0"
        )

    if staged_count > 0 or medium_plus > 0:
        effective_staged = max(staged_count, medium_plus)
        if not re.search(r"^## Findings\s*$", content, re.MULTILINE):
            result.add_error("verdict claims Medium+ but missing ## Findings section")
        for idx, block in enumerate(finding_blocks, start=1):
            has_comment, has_analysis = finding_has_comment_and_analysis(block)
            if has_comment or has_analysis:
                if not has_comment:
                    result.add_error(f"finding {idx} missing #### Comment")
                if not has_analysis:
                    result.add_error(f"finding {idx} missing #### Analysis")
            elif not is_legacy_finding_block(block):
                result.add_error(
                    f"finding {idx} missing #### Comment/Analysis (legacy blocks need "
                    f"Status/Triage and >= {LEGACY_MIN_BLOCK_CHARS} chars)"
                )
        if len(finding_blocks) < effective_staged:
            delta = effective_staged - len(finding_blocks)
            if len(finding_blocks) == 0:
                result.add_error(
                    f"staged count expects {effective_staged} findings but no finding sections"
                )
            else:
                result.add_error(
                    f"staged count expects {effective_staged} findings but only "
                    f"{len(finding_blocks)} finding sections (gap {delta})"
                )
        if size < STUB_BYTE_THRESHOLD and effective_staged > 0:
            result.add_error(
                f"stub suspected: {effective_staged} staged findings claimed but file is only "
                f"{size} bytes (threshold {STUB_BYTE_THRESHOLD})"
            )
    else:
        if "## Review Statistics" not in content:
            result.add_error("clear round still requires ## Review Statistics")

    validate_discarded_findings(content, result)
    validate_stats_sidecar(path, content, result)

    if hard and not result.ok:
        return result
    if not hard and result.errors:
        result.add_warning("soft mode: errors reported but exit code remains 0")
    return result


def newest_staging_for_branch(repo_root: Path, branch: str) -> Path | None:
    reviews_dir = resolve_reviews_dir(repo_root)
    if not reviews_dir.is_dir():
        return None
    slug = branch.lower().replace("/", "-")
    candidates = [
        p
        for p in reviews_dir.glob("*.md")
        if slug in p.name.lower() and is_staging_review_path(p)
    ]
    if not candidates:
        candidates = [p for p in reviews_dir.glob("*.md") if is_staging_review_path(p)]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def run_selftest() -> int:
    import tempfile
    import textwrap

    failures = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failures
        if ok:
            print(f"OK: {name}")
        else:
            print(f"FAIL: {name}", file=sys.stderr)
            failures += 1

    check(
        "PR staging name without 'review'",
        is_staging_review_path(Path("2026-07-17-PR-99-feature-r1.md")),
    )
    check(
        "confluence staging without round suffix",
        is_staging_review_path(Path("2026-07-17-confluence-review-foo.md")),
    )
    check(
        "branch-review round name",
        is_staging_review_path(Path("2026-07-17-branch-review-main-r2.md")),
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stub = root / "2026-07-17-branch-review-x-r1.md"
        stub.write_text(
            textwrap.dedent(
                """\
                # Branch Review: x
                ## Metadata
                - Findings: 2
                - Status: STAGED
                ## Review Statistics
                ### Panel
                | Agent | Status | Raw | Solo | Echo | Relaunch |
                |-------|--------|-----|------|------|----------|
                | quality | complete | 0 | 0 | 0 | no |
                ### Counts
                - Agents launched: 1
                - Agents skipped: 0
                - Raw findings (all agents): 0
                - Staged findings: 2
                - Discarded during synthesis: 0
                - Solo staged (unique agent origin): 0
                - Echo staged (multi-agent dedup): 0
                ### Deduplication groups
                None (each staged finding had a single agent origin).
                ### Discarded findings
                None.
                ### Severity calibration
                None (agent severities matched staged severities).
                ### Triage outcomes
                Pending triage.
                ## Findings
                ### 1. Thin
                - **Severity**: Medium
                - **Triage**: pending
                ### 2. Also thin
                - **Severity**: Low
                - **Triage**: pending
                ## Verdict for this round (before fixes)
                **2 Medium+ findings accepted for fix**
                """
            )
        )
        result = validate_staging_file(stub, hard=True)
        check("stub findings without Comment/Analysis fail hard", not result.ok)
        check(
            "stub fails specifically for missing Comment",
            any("Comment" in e for e in result.errors),
        )
        check(
            "stub fails for missing stats sidecar",
            any("stats sidecar" in e for e in result.errors),
        )
        check(
            "bullet staged count 2 from stub",
            extract_staged_count(stub.read_text()) == 2,
        )

        gap = root / "2026-07-17-branch-review-gap-r1.md"
        gap.write_text(
            textwrap.dedent(
                """\
                # Branch Review: gap
                ## Metadata
                - Findings: 3
                - Stats sidecar: skipped
                - Status: STAGED
                ## Review Statistics
                ### Panel
                | Agent | Status | Raw | Solo | Echo | Relaunch |
                |-------|--------|-----|------|------|----------|
                | quality | complete | 1 | 1 | 0 | no |
                ### Counts
                - Staged findings: 3
                ### Deduplication groups
                None (each staged finding had a single agent origin).
                ### Discarded findings
                None.
                ### Severity calibration
                None (agent severities matched staged severities).
                ### Triage outcomes
                Pending triage.
                ## Findings
                ### 1. Only one
                - **Severity**: Medium
                - **Triage**: pending
                #### Comment
                Contract says X. Code does Y. Why it matters: Z. Fix: pad.
                #### Analysis
                Verified against HEAD.
                ## Verdict for this round (before fixes)
                **3 Medium+ findings accepted for fix**
                """
            )
            + ("x" * 2000)
        )
        gap_result = validate_staging_file(gap, hard=True)
        check(
            "count gap 1-4 fails hard",
            any("gap" in e for e in gap_result.errors),
        )
        check(
            "stats skip with staged findings fails hard",
            any("Stats sidecar: skipped" in e for e in gap_result.errors),
        )

        wrong = root / "2026-07-17-branch-review-wo-r1.md"
        wrong.write_text(
            textwrap.dedent(
                """\
                # Branch Review: wo
                ## Metadata
                - Findings: 0
                - Status: STAGED
                ## Review Statistics
                ### Panel
                | Agent | Status | Raw | Solo | Echo | Relaunch |
                |-------|--------|-----|------|------|----------|
                | quality | complete | 0 | 0 | 0 | no |
                ### Counts
                - Staged findings: 0
                ### Deduplication groups
                None (each staged finding had a single agent origin).
                ### Discarded findings
                | Agent | Agent severity | Pattern | Theme | Reason | Notes |
                |-------|----------------|---------|-------|--------|-------|
                | architecture | Medium | architecture#x | IP drift | wrong-owner | |
                ### Severity calibration
                None (agent severities matched staged severities).
                ### Triage outcomes
                Pending triage.
                ## Verdict for this round (before fixes)
                0 Medium+ findings; clear round
                """
            )
        )
        (root / "2026-07-17-branch-review-wo-r1.stats.json").write_text(
            '{"panel":[],"counts":{}}'
        )
        wo_result = validate_staging_file(wrong, hard=True)
        check(
            "wrong-owner without lead fails hard",
            any("wrong-owner" in e and "lead" in e for e in wo_result.errors),
        )

        clear = root / "2026-07-17-branch-review-clear-r1.md"
        clear.write_text(
            textwrap.dedent(
                """\
                # Branch Review: clear
                ## Metadata
                - Findings: 0
                - Status: STAGED
                ## Review Statistics
                ### Panel
                | Agent | Status | Raw | Solo | Echo | Relaunch |
                |-------|--------|-----|------|------|----------|
                | quality | complete | 0 | 0 | 0 | no |
                ### Counts
                - Agents launched: 1
                - Agents skipped: 0
                - Raw findings (all agents): 0
                - Staged findings: 0
                - Discarded during synthesis: 0
                - Solo staged (unique agent origin): 0
                - Echo staged (multi-agent dedup): 0
                ### Deduplication groups
                None (each staged finding had a single agent origin).
                ### Discarded findings
                None.
                ### Severity calibration
                None (agent severities matched staged severities).
                ### Triage outcomes
                | Agent | Staged | Fixed | Dropped | Deferred | Pending |
                |-------|--------|-------|---------|----------|---------|
                | quality | 0 | 0 | 0 | 0 | 0 |
                ## Verdict for this round (before fixes)
                0 Medium+ findings; clear round
                """
            )
        )
        (root / "2026-07-17-branch-review-clear-r1.stats.json").write_text(
            '{"panel":[{"agent":"quality","status":"complete","raw":0,"solo":0,"echo":0}],'
            '"counts":{"staged_findings":0}}'
        )
        clear_result = validate_staging_file(clear, hard=True)
        check("clear round with sidecar passes hard", clear_result.ok)

        lie = root / "2026-07-17-branch-review-lie-r1.md"
        lie.write_text(
            textwrap.dedent(
                """\
                # Branch Review: lie
                ## Metadata
                - Findings: 0
                - Stats sidecar: skipped
                - Status: STAGED
                ## Review Statistics
                ### Panel
                | Agent | Status | Raw | Solo | Echo | Relaunch |
                |-------|--------|-----|------|------|----------|
                | quality | complete | 0 | 0 | 0 | no |
                ### Counts
                - Staged findings: 0
                ### Deduplication groups
                None (each staged finding had a single agent origin).
                ### Discarded findings
                None.
                ### Severity calibration
                None (agent severities matched staged severities).
                ### Triage outcomes
                Pending triage.
                ## Verdict for this round (before fixes)
                **3 Medium+ findings accepted for fix**
                """
            )
        )
        lie_result = validate_staging_file(lie, hard=True)
        check(
            "clear-round lie (staged 0 + verdict Medium+) fails hard",
            not lie_result.ok
            and any("verdict claims" in e for e in lie_result.errors),
        )

        phrase = root / "2026-07-17-branch-review-phrase-r1.md"
        phrase.write_text(
            textwrap.dedent(
                """\
                # Branch Review: phrase
                ## Metadata
                - Findings: 0
                - Status: STAGED
                ## Review Statistics
                ### Panel
                | Agent | Status | Raw | Solo | Echo | Relaunch |
                |-------|--------|-----|------|------|----------|
                | quality | complete | 0 | 0 | 0 | no |
                ### Counts
                - Staged findings: 0
                ### Deduplication groups
                None (each staged finding had a single agent origin).
                ### Discarded findings
                None.
                ### Severity calibration
                None (agent severities matched staged severities).
                ### Triage outcomes
                | Agent | Staged | Fixed | Dropped | Deferred | Pending |
                |-------|--------|-------|---------|----------|---------|
                | quality | 0 | 0 | 0 | 0 | 0 |
                ## Findings
                ### 1. Mentions skip phrase
                - **Severity**: Low
                - **Triage**: dropped
                #### Comment
                Discussed `Stats sidecar: skipped` as a waived option for clear rounds.
                #### Analysis
                Prose only; staged count remains 0.
                ## Verdict for this round (before fixes)
                0 Medium+ findings; clear round
                """
            )
        )
        (root / "2026-07-17-branch-review-phrase-r1.stats.json").write_text(
            '{"panel":[],"counts":{"staged_findings":0}}'
        )
        phrase_result = validate_staging_file(phrase, hard=True)
        check(
            "Stats sidecar phrase outside Metadata does not waive sidecar",
            phrase_result.ok,
        )

    if failures:
        print(f"validate_review_staging: --selftest FAILED ({failures})", file=sys.stderr)
        return 1
    print("validate_review_staging: --selftest ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate review staging markdown")
    parser.add_argument("path", nargs="?", help="Staging markdown file")
    parser.add_argument(
        "--hard",
        action="store_true",
        help="Exit 1 when validation fails",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result on stdout")
    parser.add_argument(
        "--newest-for-branch",
        metavar="BRANCH",
        help="Validate newest staging doc for branch slug in reviews_dir",
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="Repo cwd when using --newest-for-branch",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run fixture checks and exit",
    )
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    target: Path | None = None
    if args.path:
        target = Path(args.path).expanduser().resolve()
    elif args.newest_for_branch:
        repo_root = Path(args.cwd).expanduser().resolve()
        target = newest_staging_for_branch(repo_root, args.newest_for_branch)
        if target is None:
            payload = {
                "ok": True,
                "skipped": True,
                "reason": "no staging doc found for branch",
            }
            if args.json:
                print(json.dumps(payload))
            return 0
    else:
        parser.error("path or --newest-for-branch is required")

    result = validate_staging_file(target, hard=args.hard)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for warning in result.warnings:
            print(f"WARN: {warning}", file=sys.stderr)
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if result.ok:
            print(f"OK: {target}")
        else:
            print(f"FAIL: {target}", file=sys.stderr)

    if args.hard and not result.ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
