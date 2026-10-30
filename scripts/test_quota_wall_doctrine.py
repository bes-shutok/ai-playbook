"""Hermetic pytest suite for the quota-wall dispatch doctrine (plan
2026-10-08-quota-wall-dispatch-doctrine).

Task 1 witnesses live here now: the two-class classification witnesses run
through a test-local classifier whose rule literals are read from the
doctrine block in agents/skills/execute-plan/SKILL.md (Sub-Agent Launch
Rules) and the mirror sentences in agents/skills/maintenance/zcode.md (the
Dispatch discipline bullet), so the classification witnesses fail while the
block is absent. The launch ledger line shape witnesses (Task 2) live here
too: their test-local parser reads the Phase 3 tracking list's launch ledger
entry (the RED arm while that entry is absent). The operator directive
supersession witnesses (Task 3) read the directives home
(docs/maintenance/operator-directives.md) and its git history baseline: the
newest committed revision of the file whose blob differs from the working
tree (HEAD while the record is uncommitted, the record-carrying commit's
parent once the record lands). This plan's record is anchored by identity,
its recorded D-id cross-checked by its distinguishing witness literal, so a
later record (a future D-14) cannot false-red the suite; its scope names the
execution and maintenance lanes, its witness names the superseded
conversational restart direction, and every pre-existing record is
textually unchanged against the baseline.

Fixtures are in-memory manifest free-text line lists; no network; the Task 3
witnesses read the directives file's git history baseline bytes.
"""
from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXEC_SKILL = REPO_ROOT / "agents" / "skills" / "execute-plan" / "SKILL.md"
MAINT_SKILL = REPO_ROOT / "agents" / "skills" / "maintenance" / "zcode.md"

# The landed dispatch-failure contract (the doctrine never widens it).
TYPED_LINE = "dispatch_failed: <ISO timestamp> <worker role> <reason code> pre-start"
REASON_CODES = ("model-capacity", "thread-limit", "rate-limit", "other")
BUDGET_SPAN = "three launch attempts per failed worker role per boundary"
LAUNCH_RULES_HEADING = "## Sub-Agent Launch Rules"
MAINT_BULLET_HEAD = "Dispatch discipline and loop stand-down"
LOGS_FILE = REPO_ROOT / "agents" / "skills" / "execute-plan" / "agent-logs.md"
PHASE3_HEADING = "## Phase 3: Review / Fix Loop"
TRACKING_LIST_ANCHOR = "Track in `manifest.md`:"
LEDGER_ENTRY_HEAD = "- `launch-wave`"
LEDGER_LINE_FORMAT = (
    "launch-wave: <n> <launched|transient|usage-wall> died-at <ISO timestamp|active>"
)
LEDGER_CLASSES = ("launched", "transient", "usage-wall")
PASS_NUMBERING_ANCHOR = "The orchestrator sets `<LOG_PASS_NUM>`"
CLOCKED_ORDER_PLAN = (
    "docs/history/plans/completed/2026-10-05-authoring-clocked-resume-order.md"
)
BLOCK_MARKER = "Quota-wall dispatch doctrine"

# The classifier's witness vocabulary for the post-death resume record
# (manifest free-text lines mandated by the doctrine block; no schema fields).
RESUME_LINE_PREFIXES = ("timed_resume:", "clocked_order_parked:")

RESET_TIME_RX = re.compile(
    r"reset(?:s)?\s+at\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", re.IGNORECASE
)
ISO_MINUTE_RX = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")

USAGE_WALL_ERROR = (
    "rolling usage window exhausted; quota resets at 2026-10-07T14:00Z"
)
MINUTES_AWAY_ERROR = "momentary throttling; quota resets at 2026-10-07T09:40Z"
TRANSIENT_ERROR = "momentary capacity throttling, retry shortly"


def _exec_text() -> str:
    return EXEC_SKILL.read_text(encoding="utf-8")


def _doctrine_block() -> str:
    """The doctrine block paragraph beside the bounded-retry budget sentence.

    The block opens its own paragraph with BLOCK_MARKER inside the Sub-Agent
    Launch Rules area and runs to the next blank line. Its absence is the
    RED arm: the classifier refuses to classify without the rule's home.
    """
    text = _exec_text()
    heading = text.find(LAUNCH_RULES_HEADING)
    marker = text.find(BLOCK_MARKER, heading)
    if heading == -1 or marker == -1:
        pytest.fail(
            "doctrine block absent from the Sub-Agent Launch Rules in "
            "agents/skills/execute-plan/SKILL.md"
        )
    start = text.rfind("\n", 0, marker) + 1
    end = text.find("\n\n", start)
    block = text[start:] if end == -1 else text[start:end]
    assert BLOCK_MARKER in block
    return block


def _dispatch_bullet() -> str:
    text = MAINT_SKILL.read_text(encoding="utf-8")
    # The line-initial bullet form: another bullet quotes the heading
    # mid-line, so a bare heading find would span the wrong bullet.
    marker = "\n- " + MAINT_BULLET_HEAD
    marker_at = text.find(marker)
    if marker_at == -1:
        pytest.fail(
            "Dispatch discipline bullet absent from "
            "agents/skills/maintenance/zcode.md"
        )
    start = marker_at + len("\n- ")
    end = text.find("\n- ", start)
    return text[start:] if end == -1 else text[start:end]


def _parse_iso_minute(value: str) -> datetime:
    found = ISO_MINUTE_RX.search(value)
    assert found is not None, value
    return datetime.fromisoformat(found.group(0))


def classify_refusal(error_text: str, failed_at: str) -> str:
    """Test-local two-class boundary; its vocabulary is read from the block.

    usage-wall iff the quoted error names a reset time one hour or more
    away; otherwise transient, the class the landed bounded-retry budget
    governs. The block gate keeps the classification witnesses RED while
    the doctrine block is absent from the skill text.
    """
    block = _doctrine_block()
    assert "reset time an hour or more away" in block
    assert "transient" in block and "usage-wall" in block
    match = RESET_TIME_RX.search(error_text)
    if match is None:
        return "transient"
    reset_at = _parse_iso_minute(match.group(0))
    hours = (reset_at - _parse_iso_minute(failed_at)).total_seconds() / 3600
    return "usage-wall" if hours >= 1 else "transient"


class Episode:
    """Test-local doctrine audit over manifest free-text lines.

    Reads only what the Task 1 witnesses need: the per-wave ledger line's
    class token (the full ledger shape suite is Task 2), the pre_restart
    pair ordering, and the timed-resume or parked-order record.
    """

    def __init__(self, lines: list[str]) -> None:
        block = _doctrine_block()
        assert "one hardened probe" in block
        assert "timed resume" in block and "the recorded reset" in block
        assert CLOCKED_ORDER_PLAN in block
        # the arm or the park lands the manifest free-text line the block
        # mandates (`timed_resume:` / `clocked_order_parked:`)
        assert "timed_resume:" in block and "clocked_order_parked:" in block
        self.pairs: list[int] = []
        self.wave_lines: list[tuple[int, tuple[int, str]]] = []
        self.resumes: list[str] = []
        for index, line in enumerate(lines):
            if line.startswith("launch-wave:"):
                parts = line.split()
                self.wave_lines.append((index, (int(parts[1]), parts[2])))
            elif line.startswith("pre_restart:"):
                self.pairs.append(index)
            elif line.startswith(RESUME_LINE_PREFIXES):
                self.resumes.append(line)

    @property
    def waves(self) -> list[tuple[int, str]]:
        return [wave for _, wave in self.wave_lines]

    @property
    def pair_precedes_first_wave(self) -> bool:
        if not self.wave_lines:
            return False
        first = self.wave_lines[0][0]
        return any(pair < first for pair in self.pairs)

    @property
    def verdict(self) -> tuple[str, str]:
        usage_deaths = [wave for _, wave in self.waves if wave == "usage-wall"]
        if len(usage_deaths) >= 2 and not self.resumes:
            return (
                "deviation",
                "second usage-wall death with neither a timed resume nor a "
                "parked order: the lane consumed the remaining bounded-retry "
                "budget instead of arming the timed resume at the recorded "
                "reset",
            )
        if usage_deaths and not self.resumes:
            return (
                "deviation",
                "usage-wall probe death with neither a timed resume nor a "
                "parked clocked order",
            )
        return (
            "conformant",
            "one hardened probe, ledger line classed usage-wall, timed "
            "resume armed at the recorded reset",
        )


def usage_wall_episode(
    extra_wave: bool = False, resume_record: bool = True
) -> list[str]:
    lines = [
        (
            "dispatch_failed: 2026-10-07T09:12Z reviewer rate-limit pre-start "
            f"({USAGE_WALL_ERROR})"
        ),
        "pre_restart: 2026-10-07T09:13Z branch 9d1c0fe",
        "pre_restart_paths: docs/tmp/execute-plan/demo/review-log.md",
        "launch-wave: 1 usage-wall died-at 2026-10-07T09:47Z",
    ]
    if extra_wave:
        lines += [
            "pre_restart: 2026-10-07T09:50Z branch 9d1c0fe",
            "pre_restart_paths: docs/tmp/execute-plan/demo/review-log.md",
            "launch-wave: 2 usage-wall died-at 2026-10-07T10:20Z",
        ]
    if resume_record:
        lines.append(
            "timed_resume: 2026-10-07T09:48Z reviewer armed at the recorded "
            "reset 2026-10-07T14:00Z"
        )
    return lines


def test_doctrine_block_sits_beside_the_bounded_retry_budget_sentence():
    text = _exec_text()
    block = _doctrine_block()
    block_start = text.find(block)
    assert block_start > text.find(LAUNCH_RULES_HEADING)
    preceding = text[:block_start].rstrip()
    prev_paragraph = preceding[preceding.rfind("\n\n") + 2 :]
    assert BUDGET_SPAN in prev_paragraph


def test_doctrine_block_carries_the_two_class_rule():
    block = _doctrine_block()
    for literal in (
        "transient rate-limit refusal",
        "retries within the landed bounded-retry budget",
        "no reset time an hour or more away",
        "reset time an hour or more away",
        "one hardened probe",
        "pre_restart:",
        "pre_restart_paths:",
        # re-aimed 2026-10-30 (review round: the undefined "throttle-window
        # hold" term was dropped; the block now reads "throttle window")
        "throttle window",
        "on the probe's death",
        "timed resume",
        "the recorded reset",
        CLOCKED_ORDER_PLAN,
        "instead of consuming the remaining budget",
        "timed_resume:",
        "clocked_order_parked:",
        "goes straight to the named escalation",
        "never a second probe",
        "rate_limited",
        "`rate_limited:` stop line",
        "structured `rate_limited` end",
        "budget numbers are unchanged",
    ):
        assert literal in block, literal


def test_doctrine_block_keeps_the_landed_contract_byte_identical():
    text = _exec_text()
    assert TYPED_LINE in text
    assert BUDGET_SPAN in text
    for code in REASON_CODES:
        assert code in text
    block = _doctrine_block()
    for code in REASON_CODES:
        assert code in block


def test_mid_run_death_recognition_is_named_in_the_block():
    block = _doctrine_block()
    assert "mid-run usage-wall death" in block
    # the duty scoped to mid-run worker deaths: the parent records the
    # line-initial `rate_limited:` stop line (or the structured end)
    assert "the parent records that death" in block
    assert "`rate_limited:` stop line" in block
    assert "structured `rate_limited` end" in block
    assert "classes it usage-wall" in block


def test_maintenance_bullet_mirrors_the_two_class_rule():
    bullet = _dispatch_bullet()
    for literal in (
        "no reset time an hour or more away",
        "reset time an hour or more away",
        "one hardened probe",
        "on that probe's death",
        "timed resume",
        "the recorded reset",
        "never the remaining budget's probes",
        "bounded-retry budget",
        BLOCK_MARKER,
        "agents/skills/execute-plan/SKILL.md",
    ):
        assert literal in bullet, literal


def test_maintenance_bullet_defers_the_mechanics_to_the_execution_skill():
    bullet = _dispatch_bullet()
    assert TYPED_LINE not in bullet
    assert "pre_restart_paths:" not in bullet


def test_witness_usage_wall_refusal_gets_one_probe_then_the_timed_resume():
    lines = usage_wall_episode()
    failed_at = lines[0].split()[1]
    assert classify_refusal(USAGE_WALL_ERROR, failed_at) == "usage-wall"
    episode = Episode(lines)
    assert episode.pair_precedes_first_wave
    assert episode.waves == [(1, "usage-wall")]
    assert len(episode.resumes) == 1
    assert "2026-10-07T14:00Z" in episode.resumes[0]
    verdict, _ = episode.verdict
    assert verdict == "conformant"


def test_witness_second_usage_wall_death_without_resume_is_named_deviation():
    lines = usage_wall_episode(extra_wave=True, resume_record=False)
    episode = Episode(lines)
    assert episode.waves == [(1, "usage-wall"), (2, "usage-wall")]
    assert not episode.resumes
    verdict, detail = episode.verdict
    assert verdict == "deviation"
    assert "second usage-wall death" in detail
    assert "timed resume" in detail


def test_witness_error_without_a_reset_time_is_transient():
    failed_at = "2026-10-07T09:12Z"
    assert classify_refusal(TRANSIENT_ERROR, failed_at) == "transient"
    # A reset minutes away is not "hours away": the momentary class again.
    assert classify_refusal(MINUTES_AWAY_ERROR, failed_at) == "transient"


# --- Task 2: the launch ledger line shape (visibility receipt) ---

# The dispatch_failed tracking-list pin (2026-10-30, the receipt-witness
# follow-up): the failure receipt's tracking-list entry gets the same reader
# pin the launch-wave entry carries, so deleting the pinned line is a suite
# failure instead of a silent doctrine erosion.
DISPATCH_FAILED_ENTRY_HEAD = "- `dispatch_failed`"


def _dispatch_failed_entry() -> str:
    """The Phase 3 tracking list's dispatch_failed bullet (one line).

    Its absence is the RED arm, mirroring _ledger_entry: the failure-receipt
    witnesses refuse to parse fixtures without the line contract's home.
    """
    text = _exec_text()
    phase3 = text.find(PHASE3_HEADING)
    if phase3 == -1:
        pytest.fail(
            "Phase 3 heading absent from agents/skills/execute-plan/SKILL.md"
        )
    anchor = text.find(TRACKING_LIST_ANCHOR, phase3)
    head = text.find(DISPATCH_FAILED_ENTRY_HEAD, anchor) if anchor != -1 else -1
    if head == -1:
        pytest.fail(
            "dispatch_failed line contract absent from the Phase 3 tracking "
            "list in agents/skills/execute-plan/SKILL.md"
        )
    end = text.find("\n", head)
    return text[head:] if end == -1 else text[head:end]


# The tracking-list entry's contract literals, single-homed: the parser
# gate and the dedicated contract test assert the same tuple, so the two
# lists cannot drift independently.
DISPATCH_FAILED_CONTRACT_LITERALS = (
    "`dispatch_failed: <ISO timestamp> <worker role> <reason code> pre-start`",
    "closed reason-code set",
    "the two-line `pre_restart:`/`pre_restart_paths:` state pair",
    "the bounded-retry budget owned by the Sub-Agent Launch Rules paragraph",
    "never restated here",
)

# The typed line's timestamp token form: ISO minute precision, the form the
# doctrine's own fixture vocabulary writes (2026-10-07T09:47Z).
DISPATCH_FAILED_TS_RX = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z")


def dispatch_failed_fields(line: str) -> dict:
    """Test-local dispatch-failure record parser; its shape vocabulary is
    read from the tracking-list entry the same way ledger_lines reads the
    launch-wave entry.

    Returns the typed line's timestamp, role, and closed-set reason code;
    refuses any line outside the `dispatch_failed: <ISO timestamp> <worker
    role> <reason code> pre-start` shape (the timestamp token must match the
    ISO minute form; a single-token role per the doctrine's fixture
    vocabulary). The `other` reason code carries the provider error text
    quoted on the line (the closed set's clause in the Sub-Agent Launch
    Rules paragraph), so trailing tokens after `other` are that quote and
    are accepted, carried back as `error_text`.
    """
    entry = _dispatch_failed_entry()
    for literal in DISPATCH_FAILED_CONTRACT_LITERALS:
        assert literal in entry, literal
    assert line.startswith("dispatch_failed:"), line
    parts = line.split()
    assert len(parts) >= 5, f"missing pre-start token: {line}"
    assert parts[4] == "pre-start", line
    assert parts[3] in REASON_CODES, (
        f"reason code {parts[3]!r} outside the closed set: {line}"
    )
    assert DISPATCH_FAILED_TS_RX.fullmatch(parts[1]), line
    fields = {"timestamp": parts[1], "role": parts[2], "reason_code": parts[3]}
    if parts[3] == "other":
        assert len(parts) > 5, (
            f"other reason code carries no quoted provider error text: {line}"
        )
        fields["error_text"] = " ".join(parts[5:])
    else:
        assert len(parts) == 5, (
            f"trailing tokens outside the other code's quoted-error shape: {line}"
        )
    return fields


def test_dispatch_failed_tracking_entry_carries_the_line_contract():
    entry = _dispatch_failed_entry()
    # The typed line, its closed reason-code set, the pre-restart state pair,
    # the budget pointer, and the delegation clause are the entry's contract;
    # deleting any of them (the witnessed erosion class) fails here. The
    # literal tuple is shared with the parser gate, so the two lists cannot
    # drift apart.
    for literal in DISPATCH_FAILED_CONTRACT_LITERALS:
        assert literal in entry, literal


def test_witness_dispatch_failed_line_parses_against_the_entry_contract():
    fields = dispatch_failed_fields(
        "dispatch_failed: 2026-10-29T23:41Z reviewer rate-limit pre-start"
    )
    assert fields == {
        "timestamp": "2026-10-29T23:41Z",
        "role": "reviewer",
        "reason_code": "rate-limit",
    }


def test_witness_dispatch_failed_parser_refuses_out_of_set_reason_code():
    with pytest.raises(AssertionError, match="outside the closed set"):
        dispatch_failed_fields(
            "dispatch_failed: 2026-10-29T23:41Z reviewer quota-wall pre-start"
        )
    with pytest.raises(AssertionError, match="pre-start"):
        dispatch_failed_fields(
            "dispatch_failed: 2026-10-29T23:41Z reviewer rate-limit"
        )


def test_witness_dispatch_failed_parser_refuses_malformed_timestamp():
    with pytest.raises(AssertionError, match="notatime"):
        dispatch_failed_fields(
            "dispatch_failed: notatime reviewer rate-limit pre-start"
        )


def test_witness_dispatch_failed_other_code_carries_the_quoted_error_text():
    fields = dispatch_failed_fields(
        "dispatch_failed: 2026-10-29T23:41Z reviewer other pre-start "
        "provider returned 529 origin-wall"
    )
    assert fields["reason_code"] == "other"
    assert fields["error_text"] == "provider returned 529 origin-wall"
    with pytest.raises(AssertionError, match="quoted provider error text"):
        dispatch_failed_fields(
            "dispatch_failed: 2026-10-29T23:41Z reviewer other pre-start"
        )


def _ledger_entry() -> str:
    """The Phase 3 tracking list's launch ledger bullet (one line).

    Its absence is the Task 2 RED arm: the ledger witnesses refuse to parse
    fixtures without the line contract's home.
    """
    text = _exec_text()
    phase3 = text.find(PHASE3_HEADING)
    if phase3 == -1:
        pytest.fail(
            "Phase 3 heading absent from agents/skills/execute-plan/SKILL.md"
        )
    anchor = text.find(TRACKING_LIST_ANCHOR, phase3)
    head = text.find(LEDGER_ENTRY_HEAD, anchor) if anchor != -1 else -1
    if head == -1:
        pytest.fail(
            "launch ledger line contract absent from the Phase 3 tracking "
            "list in agents/skills/execute-plan/SKILL.md"
        )
    end = text.find("\n", head)
    return text[head:] if end == -1 else text[head:end]


def ledger_lines(lines: list[str]) -> list[dict]:
    """Test-local ledger parser; its shape vocabulary is read from the entry.

    Accepts both contracted forms: the single-role `launch-wave: <n> <class>
    died-at <ts|active>` and the multi-role `launch-wave: <role> <n> ...`
    (a non-numeric second token is the role). Returns one record per ledger
    line with its file position, role token, ordinal, outcome class, and
    died-at value.
    """
    entry = _ledger_entry()
    for literal in (
        LEDGER_LINE_FORMAT,
        "per dispatch wave per worker role",
        "free-text lines",
        "1-based launch sequence",
        "per-path pass number",
        "per-round wave ordinal",
        # the "receipt wave 2 is not ledger ordinal 2" example clause was
        # dropped 2026-10-30 (review round: it leaned on an absent
        # wave_budget_receipts example); the parenthetical it leaned on is
        # pinned by "per-round wave ordinal" above
        "launch-wave: <role> <n>",
        "the lines never collide across roles (the per-role ordinals may repeat)",
        "consumes no ordinal",
        "written beside the `pre_restart:`/`pre_restart_paths:` pair",
        "after the probe's outcome",
        "never a second copy of the wave's line",
        "usage-wall probe",
    ):
        assert literal in entry, literal
    ledger = []
    for position, line in enumerate(lines):
        if not line.startswith("launch-wave:"):
            continue
        parts = line.split()
        if parts[1].isdigit():
            role, ordinal, rest = None, int(parts[1]), parts[2:]
        else:
            role, ordinal, rest = parts[1], int(parts[2]), parts[3:]
        outcome, separator, died_at = rest[0], rest[1], rest[2]
        assert outcome in LEDGER_CLASSES, line
        assert separator == "died-at", line
        ledger.append(
            {
                "position": position,
                "role": role,
                "ordinal": ordinal,
                "outcome": outcome,
                "died_at": died_at,
            }
        )
    return ledger


def three_wave_manifest() -> list[str]:
    """One role, one boundary, three waves: launched, usage-wall death, then
    the wave after the timed-resume arm."""
    return [
        "review_round: 1",
        (
            "wave_budget_receipts: round 1 wave 1 decision: probe-run "
            "digest abc123"
        ),
        "launch-wave: 1 launched died-at active",
        "pre_restart: 2026-10-07T09:50Z branch 9d1c0fe",
        "pre_restart_paths: docs/tmp/execute-plan/demo/review-log.md",
        "launch-wave: 2 usage-wall died-at 2026-10-07T10:20Z",
        (
            "timed_resume: 2026-10-07T10:21Z reviewer armed at the recorded "
            "reset 2026-10-07T14:00Z"
        ),
        "launch-wave: 3 launched died-at active",
    ]


def test_witness_three_wave_manifest_reads_ordinals_and_classes_in_sequence():
    ledger = ledger_lines(three_wave_manifest())
    assert len(ledger) == 3
    assert [line["ordinal"] for line in ledger] == [1, 2, 3]
    assert [line["outcome"] for line in ledger] == [
        "launched",
        "usage-wall",
        "launched",
    ]
    assert [line["died_at"] for line in ledger] == [
        "active",
        "2026-10-07T10:20Z",
        "active",
    ]
    assert [line["position"] for line in ledger] == sorted(
        line["position"] for line in ledger
    )


def test_witness_multi_role_wave_writes_one_line_per_role_with_the_role_token():
    lines = [
        "launch-wave: reviewer 1 launched died-at active",
        "launch-wave: implementer 1 launched died-at active",
    ]
    ledger = ledger_lines(lines)
    assert len(ledger) == 2
    assert [line["role"] for line in ledger] == ["reviewer", "implementer"]
    assert all(line["role"] is not None for line in ledger)
    # One 1-based sequence per role: the shared ordinal 1 never collides.
    assert [line["ordinal"] for line in ledger] == [1, 1]
    assert [line["outcome"] for line in ledger] == ["launched", "launched"]


def test_witness_zero_dispatch_boundary_yields_no_ledger_line():
    lines = [
        "workflow_state: active",
        "review_round: 1",
        "re_entry_count: 0",
        (
            "wave_budget_receipts: round 1 wave 1 decision: probe-run "
            "digest abc123"
        ),
    ]
    assert ledger_lines(lines) == []
    assert not any(line.startswith("launch-wave:") for line in lines)


def test_agent_logs_pass_numbering_rides_the_same_numbering():
    text = LOGS_FILE.read_text(encoding="utf-8")
    anchor = text.find(PASS_NUMBERING_ANCHOR)
    assert anchor != -1
    end = text.find("\n\n", anchor)
    paragraph = text[anchor:] if end == -1 else text[anchor:end]
    assert "launch-wave:" in paragraph
    assert "per-path pass numbering" in paragraph
    assert "from the manifest alone" in paragraph


# --- Task 3: the operator directive record (supersession scope) ---

DIRECTIVES_FILE = REPO_ROOT / "docs" / "maintenance" / "operator-directives.md"
DIRECTIVES_HEAD_PATH = "docs/maintenance/operator-directives.md"
RECORD_HEAD_RX = re.compile(r"^## (D-\d+): .*$", re.MULTILINE)
# This plan's record, anchored by identity: the recorded D-id plus the
# distinguishing witness literal, never a record count against the baseline
# (a future D-14 must not false-red these witnesses).
NEW_RECORD_ID = "D-13"
NEW_RECORD_WITNESS = "superseded conversational restart direction"


def _directive_records(text: str) -> dict[str, str]:
    """id -> section text (the `## D-<n>:` heading through the next heading)."""
    heads = list(RECORD_HEAD_RX.finditer(text))
    if not heads:
        pytest.fail(
            "no D-records found in docs/maintenance/operator-directives.md"
        )
    records: dict[str, str] = {}
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        records[head.group(1)] = text[head.start() : end].rstrip("\n")
    return records


def _git_bytes(args: list[str]) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        check=True,
    )
    return proc.stdout


def _git_line(args: list[str]) -> str:
    return _git_bytes(args).decode("utf-8").strip()


def _baseline_revision() -> str:
    """The pre-record revision of the directives file.

    Commit-aware so the witnesses stay green once the record's own commit
    lands: the newest commit in the file's history whose committed blob
    differs from the working tree's bytes wins. The record-carrying
    commit's blob matches the tree and is skipped, so its parent (the
    pre-record revision) is the baseline once the record is committed,
    even when later commits touch only this test file; an uncommitted
    record makes HEAD the first differing revision. HEAD is the last
    resort when no committed blob differs (nothing landed yet).
    """
    tree_blob = _git_line(["hash-object", str(DIRECTIVES_FILE)])
    touching = _git_line(
        ["rev-list", "HEAD", "--", DIRECTIVES_HEAD_PATH]
    ).split()
    for commit in touching:
        blob = _git_line(["rev-parse", f"{commit}:{DIRECTIVES_HEAD_PATH}"])
        if blob != tree_blob:
            return commit
    return "HEAD"


def _baseline_directives_text() -> str:
    """The directives file's pre-record revision bytes, decoded."""
    revision = _baseline_revision()
    return _git_bytes(["show", f"{revision}:{DIRECTIVES_HEAD_PATH}"]).decode(
        "utf-8"
    )


def _plan_directive_record() -> str:
    """This plan's directive record, anchored by identity, not by count.

    The recorded D-id (D-13) is the primary anchor and the distinguishing
    witness literal the identity cross-check, so a later record (a future
    D-14) cannot false-red these witnesses. Absence of both anchors is the
    RED arm.
    """
    tree_records = _directive_records(DIRECTIVES_FILE.read_text(encoding="utf-8"))
    if NEW_RECORD_ID in tree_records:
        record = tree_records[NEW_RECORD_ID]
        assert NEW_RECORD_WITNESS in record, (
            f"{NEW_RECORD_ID} no longer carries this plan's witness literal"
        )
        return record
    matching = [
        section
        for section in tree_records.values()
        if NEW_RECORD_WITNESS in section
    ]
    if len(matching) == 1:
        return matching[0]
    pytest.fail(
        "this plan's directive record "
        f"({NEW_RECORD_ID}, witness `{NEW_RECORD_WITNESS}`) absent from "
        f"{DIRECTIVES_HEAD_PATH}"
    )


def _record_field(record: str, field: str) -> str:
    match = re.search(rf"^- {field}: (.*)$", record, re.MULTILINE)
    assert match is not None, f"field `{field}` absent from the record"
    return match.group(1)


def test_witness_plan_record_scope_names_the_lanes_a_dispatch_lift_resolves():
    scope = _record_field(_plan_directive_record(), "scope")
    assert "execution and maintenance lanes" in scope
    assert "in this repository" in scope


def test_witness_plan_record_witness_names_the_superseded_chat_direction():
    witness = _record_field(_plan_directive_record(), "witness")
    assert "superseded conversational restart direction" in witness
    assert "2026-10-07" in witness
    assert "usage-wall" in witness
    assert "operator chat" in witness
    assert "memory notes" in witness
    # the doctrine's home block and the landing plan make it auditable
    assert "agents/skills/execute-plan/SKILL.md" in witness
    assert "Sub-Agent Launch Rules" in witness
    assert "quota-wall dispatch doctrine" in witness
    assert (
        "docs/history/plans/2026-10-08-quota-wall-dispatch-doctrine.md" in witness
    )


def _committed_text() -> str:
    """The directives file's newest committed (HEAD) revision's bytes."""
    return _git_bytes(["show", f"HEAD:{DIRECTIVES_HEAD_PATH}"]).decode("utf-8")


def _committed_records() -> dict[str, str]:
    """The directives file's newest committed (HEAD) revision's records."""
    return _directive_records(_committed_text())


def test_witness_every_preexisting_record_is_textually_unchanged_against_baseline():
    """Byte-level pin of every pre-existing record against the baseline.

    A sanctioned post-record commit may edit a pre-existing record (the
    2026-10-27 em-dash formatting pass over D-3..D-6 landed after this
    plan's record): such a record is held byte-identically to the newest
    committed (HEAD) revision instead, so any uncommitted drift from both
    revisions stays red with the record id named, and a working-tree
    deletion of a committed record is a named red too, never a bare
    KeyError. The preamble carries the same two-revision acceptance: it
    must equal the baseline preamble, or the newest committed (HEAD)
    preamble when a sanctioned commit edited the preamble.
    """
    tree_text = DIRECTIVES_FILE.read_text(encoding="utf-8")
    head_text = _baseline_directives_text()
    committed_text = _committed_text()
    tree_records = _directive_records(tree_text)
    head_records = _directive_records(head_text)
    committed_records = _directive_records(committed_text)
    for record_id, head_section in head_records.items():
        assert record_id in tree_records, (
            f"committed record {record_id} deleted from the working tree"
        )
        if tree_records[record_id] == head_section:
            continue
        committed_section = committed_records.get(record_id)
        assert tree_records[record_id] == committed_section, (
            f"record {record_id} drifted from both the baseline and the "
            "committed (HEAD) revision"
        )
    tree_preamble = tree_text[: RECORD_HEAD_RX.search(tree_text).start()]
    head_preamble = head_text[: RECORD_HEAD_RX.search(head_text).start()]
    if tree_preamble != head_preamble:
        committed_preamble = committed_text[
            : RECORD_HEAD_RX.search(committed_text).start()
        ]
        assert tree_preamble == committed_preamble, (
            "working-tree preamble drifted from both the baseline and the "
            "committed (HEAD) preamble"
        )
