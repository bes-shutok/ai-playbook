#!/usr/bin/env python3
"""Fixture suite for the prompt-log origin checker.

Every test drives the real script through subprocess against a fixture
log written into a temporary directory, never by importing the script's
helpers, so the CLI contract (report lines and exit codes) is the tested
surface. Fixtures mirror the tracked log's section shape: an entry-
template fence in the header, then one ``## <slug>`` section per entry
with its ``Origins:`` list. Origins are cited in the corpus style
(``docs/history/backlog/<name>.md``) while the fixture files sit beside
the fixture log, exercising the checker's basename resolution.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_prompt_log_origins.py"

TEMPLATE_FENCE = """\
Entry template (one section per entry):

```
## <short-slug>

Added: <date and provenance>

Origins:
- docs/history/backlog/<origin>.md

Urgency: <judgment>

Prompt: <full ready-to-dispatch authoring prompt payload>

Rejected alternatives:
- <one line per rejected alternative, with the reason>
```
"""


def write_origin(tmp_path: Path, name: str, status_line: str | None) -> None:
    """A fixture origin file beside the fixture log; the status line is
    the file's first ``Status:`` line verbatim when given."""
    text = "# fixture origin\n"
    if status_line is not None:
        text += f"\n{status_line}\n"
    (tmp_path / name).write_text(text, encoding="utf-8")


def write_log(tmp_path: Path, sections: list[str]) -> Path:
    log = tmp_path / "PLAN-PROMPTS.md"
    log.write_text(
        "Tracked rolling log fixture.\n\n" + TEMPLATE_FENCE + "\n".join(sections),
        encoding="utf-8",
    )
    return log


def entry(slug: str, origins: list[str], frozen_line: str | None = None) -> str:
    lines = [f"## {slug}", ""]
    if frozen_line is not None:
        lines += [frozen_line, ""]
    lines += [
        "Added: fixture provenance",
        "",
        "Origins:",
    ]
    lines += [f"- docs/history/backlog/{name}" for name in origins]
    lines += [
        "",
        "Urgency: fixture",
        "",
        "Prompt: fixture payload",
        "",
        "Rejected alternatives:",
        "- none",
        "",
    ]
    return "\n".join(lines)


def run_checker(log: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(log)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_prompt_log_origins_flags_done_origin(tmp_path):
    write_origin(tmp_path, "2026-10-01-done-origin.md", "Status: done")
    log = write_log(tmp_path, [entry("solo-entry", ["2026-10-01-done-origin.md"])])
    proc = run_checker(log)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "SERVED: solo-entry -> 2026-10-01-done-origin.md [done]" in proc.stdout
    assert "STALE: solo-entry" in proc.stdout
    assert "LIVE" not in proc.stdout


def test_prompt_log_origins_flags_covered_origin(tmp_path):
    write_origin(
        tmp_path,
        "2026-10-01-covered-origin.md",
        "- **Status:** covered (docs/history/plans/fixture-plan.md)",
    )
    log = write_log(
        tmp_path, [entry("solo-entry", ["2026-10-01-covered-origin.md"])]
    )
    proc = run_checker(log)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert (
        "SERVED: solo-entry -> 2026-10-01-covered-origin.md "
        "[covered (docs/history/plans/fixture-plan.md)]"
    ) in proc.stdout
    assert "STALE: solo-entry" in proc.stdout


def test_prompt_log_origins_flags_missing_origin(tmp_path):
    log = write_log(tmp_path, [entry("solo-entry", ["2026-10-01-nowhere.md"])])
    proc = run_checker(log)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LIVE: solo-entry -> 2026-10-01-nowhere.md" in proc.stdout
    assert "SERVED" not in proc.stdout
    assert "STALE" not in proc.stdout


def test_prompt_log_origins_skips_template_block(tmp_path):
    write_origin(tmp_path, "2026-10-01-live-origin.md", "Status: open")
    log = write_log(tmp_path, [entry("real-entry", ["2026-10-01-live-origin.md"])])
    proc = run_checker(log)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # The fenced template placeholders never parse as an entry.
    assert "<short-slug>" not in proc.stdout
    assert "<origin>.md" not in proc.stdout
    assert "LIVE: real-entry -> 2026-10-01-live-origin.md" in proc.stdout


def test_prompt_log_origins_clean_log_exits_zero(tmp_path):
    write_origin(tmp_path, "2026-10-01-live-origin.md", "Status: open")
    log = write_log(
        tmp_path,
        [
            entry("first-entry", ["2026-10-01-live-origin.md"]),
            entry("second-entry", ["2026-10-01-other-live.md"]),
        ],
    )
    write_origin(tmp_path, "2026-10-01-other-live.md", "Status: in review")
    proc = run_checker(log)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "STALE" not in proc.stdout
    assert "LIVE: first-entry -> 2026-10-01-live-origin.md" in proc.stdout
    assert "LIVE: second-entry -> 2026-10-01-other-live.md" in proc.stdout


def test_prompt_log_origins_frozen_entry_still_checked(tmp_path):
    write_origin(tmp_path, "2026-10-01-served-origin.md", "Status: done")
    log = write_log(
        tmp_path,
        [
            entry(
                "frozen-entry",
                ["2026-10-01-served-origin.md"],
                frozen_line=(
                    "- Frozen: fixture witness, 2026-10-01, authoring claim fixture"
                ),
            )
        ],
    )
    proc = run_checker(log)
    # A frozen entry whose origins are all served is exactly the wedge:
    # the freeze rule itself already orders its prune.
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "STALE: frozen-entry" in proc.stdout


def test_prompt_log_origins_mixed_entry_stays(tmp_path):
    write_origin(tmp_path, "2026-10-01-done-origin.md", "Status: done")
    archive = tmp_path / "completed"
    archive.mkdir()
    (archive / "2026-10-01-archived-origin.md").write_text(
        "# fixture origin moved to the archive\n", encoding="utf-8"
    )
    write_origin(tmp_path, "2026-10-01-live-origin.md", "Status: open")
    log = write_log(
        tmp_path,
        [
            entry(
                "mixed-entry",
                [
                    "2026-10-01-done-origin.md",
                    "2026-10-01-archived-origin.md",
                    "2026-10-01-live-origin.md",
                ],
            )
        ],
    )
    proc = run_checker(log)
    # A mixed entry is dispatchable and stays: exit 0, no STALE verdict.
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SERVED: mixed-entry -> 2026-10-01-done-origin.md [done]" in proc.stdout
    assert (
        "SERVED: mixed-entry -> 2026-10-01-archived-origin.md "
        "[completed/2026-10-01-archived-origin.md]"
    ) in proc.stdout
    assert "LIVE: mixed-entry -> 2026-10-01-live-origin.md" in proc.stdout
    assert "STALE" not in proc.stdout
