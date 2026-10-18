#!/usr/bin/env python3
"""Check that the realistic report sample preserves source fields and timing."""

from __future__ import annotations

import re
from pathlib import Path


SAMPLE = Path(
    "scripts/fixtures/authoring-gist-sample.md"
)
PLAN = Path("docs/history/plans/completed/2026-10-10-plan-scope-gist-surface.md")
FIELDS = ("Title", "TLDR", "Before", "After", "Edge cases", "Execution budget")
CHANNELS = (
    "In-session, before first review",
    "Scheduled, before first review",
    "Scheduled Cycle gate readiness",
    "In-session authoring closeout",
    "Scheduled final report",
)


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.index(marker) + len(marker)
    end = text.find("\n## ", start)
    return text[start:] if end < 0 else text[start:end]


def _fields(section: str) -> dict[str, str]:
    found = dict(
        re.findall(
            r"^-? ?(Title|TLDR|Before|After|Edge cases|Execution budget): (.+)$",
            section,
            flags=re.MULTILINE,
        )
    )
    return found


def main() -> None:
    sample = SAMPLE.read_text(encoding="utf-8")
    source = _fields(_section(sample, "Input plan fields"))
    assert set(source) == set(FIELDS), f"sample source fields incomplete: {source.keys()}"
    assert source["Execution budget"] == "1h total, largest task 0.5h"

    plan_text = PLAN.read_text(encoding="utf-8")
    plan_title = re.search(r"^# Plan: (.+?)(?: \(audit |$)", plan_text, flags=re.MULTILINE)
    plan_budget = re.search(r"^Execution budget: (.+)$", plan_text, flags=re.MULTILINE)
    assert plan_title and plan_budget, "source plan title or execution budget is missing"
    plan_fields = {"Title": plan_title.group(1)}
    plan_fields.update(_fields(_section(plan_text, "Gist & Examples")))
    plan_fields["Execution budget"] = plan_budget.group(1)
    assert source == plan_fields, "sample input differs from the source plan"

    for channel in CHANNELS:
        output = _fields(_section(sample, channel))
        assert output == source, f"{channel} differs from its source fields"

    pre_review = sample.index("## In-session, before first review")
    in_session_review = sample.index(
        "Event: the normal first review round starts after this report."
    )
    scheduled_handoff = sample.index("## Scheduled, before first review")
    scheduled_review = sample.index(
        "Event: the scheduled first review round starts after this handoff."
    )
    scheduled_gate = sample.index("## Scheduled Cycle gate readiness")
    assert pre_review < in_session_review < scheduled_handoff
    assert scheduled_handoff < scheduled_review < scheduled_gate

    fallback = _section(sample, "Missing-budget fallback")
    assert "Execution budget: undeclared" in fallback
    assert "ordinary review flow" in fallback and "adds no stop" in fallback


if __name__ == "__main__":
    main()
