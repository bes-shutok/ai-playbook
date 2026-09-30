#!/usr/bin/env python3
"""Focused landing-receipt checker for PR review posting staging records.

Classifies a staging document by its exact ``Status:`` header value:

- ``POSTED`` (the bare posting value): requires a ``## Landing receipt``
  section whose census matches the posted-finding blocks and whose
  per-finding landing lines carry identity evidence (file, line, a
  non-empty fragment substring of the finding's Comment block, a non-empty
  live comment id, ``landed=yes``).
- a value starting with ``INCOMPLETE (posting incomplete``: requires the
  receipt section with at least one ``landed=no`` line.
- any other value (absent, ``STAGED ...``, suffixed ``POSTED (...)``
  record families): a no-op, exit 0.

Offline by design: the recorded receipt is the output of the posting
workflow's live fetch-and-compare; this checker validates only the
recorded surface. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

INCOMPLETE_PREFIX = "INCOMPLETE (posting incomplete"
POSTED_VALUE = "POSTED"


def _parse_header_value(text: str) -> str | None:
    match = re.search(r"^Status:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def _finding_blocks(text: str) -> list[dict[str, str]]:
    """Split the Findings region into per-finding blocks carrying File,
    Line, Status, and Comment text."""
    region = text
    start = region.find("## Findings")
    receipt = region.find("## Landing receipt")
    if start != -1:
        end = receipt if receipt != -1 else len(region)
        region = region[start:end]
    blocks: list[dict[str, str]] = []
    parts = re.split(r"^### ", region, flags=re.MULTILINE)[1:]
    for part in parts:
        block: dict[str, str] = {}
        file_match = re.search(r"- \*\*File\*\*:\s*`?([^`\n]+)`?", part)
        line_match = re.search(r"- \*\*Line\*\*:\s*(\S+)", part)
        status_match = re.search(r"- \*\*Status\*\*:\s*(\S+)", part)
        comment_match = re.search(r"#### Comment\n(.*?)(?=\n#### |\n### |\Z)", part, re.DOTALL)
        if file_match:
            block["file"] = file_match.group(1).strip()
        if line_match:
            block["line"] = line_match.group(1).strip()
        if status_match:
            block["status"] = status_match.group(1).strip()
        if comment_match:
            block["comment"] = comment_match.group(1).strip()
        blocks.append(block)
    return blocks


def _receipt_section(text: str) -> str | None:
    start = text.find("## Landing receipt")
    if start == -1:
        return None
    rest = text[start + len("## Landing receipt"):]
    next_header = re.search(r"^## ", rest, re.MULTILINE)
    body = rest[: next_header.start()] if next_header else rest
    return body


def _landing_lines(section: str) -> list[dict[str, str]]:
    lines: list[dict[str, str]] = []
    for raw in section.splitlines():
        match = re.match(
            r'landing:\s*file=(\S+)\s+line=(\S+)\s+fragment="([^"]*)"\s+'
            r"comment=(\S*)\s+landed=(yes|no)\s*$",
            raw.strip(),
        )
        if match:
            lines.append(
                {
                    "file": match.group(1),
                    "line": match.group(2),
                    "fragment": match.group(3),
                    "comment": match.group(4),
                    "landed": match.group(5),
                }
            )
    return lines


def _summary_line(section: str) -> tuple[str, str] | None:
    match = re.search(r"^intended=(\d+)\s+landed=(\d+)\s*$", section, re.MULTILINE)
    return (match.group(1), match.group(2)) if match else None


def check(text: str) -> list[str]:
    """Return one named error string per receipt defect (empty when clean)."""
    header = _parse_header_value(text)
    if header is None:
        return []
    if header == POSTED_VALUE:
        mode = "posted"
    elif header.startswith(INCOMPLETE_PREFIX):
        mode = "incomplete"
    else:
        return []
    errors: list[str] = []
    section = _receipt_section(text)
    if section is None:
        return [f"missing landing receipt section: header {header!r} requires one"]
    all_blocks = _finding_blocks(text)
    blocks = [b for b in all_blocks if b.get("status") == "posted"]
    posted_indices = {
        index for index, block in enumerate(all_blocks) if block.get("status") == "posted"
    }
    lines = _landing_lines(section)
    summary = _summary_line(section)
    if summary is None:
        errors.append("receipt census: missing intended=<n> landed=<m> summary line")
        summary = ("0", "0")
    intended, landed_count = summary
    posted_count = len(blocks)
    yes_lines = [entry for entry in lines if entry["landed"] == "yes"]
    no_lines = [entry for entry in lines if entry["landed"] == "no"]
    if mode == "posted":
        if intended != str(posted_count):
            errors.append(
                f"receipt census mismatch: intended={intended} but the record "
                f"carries {posted_count} posted finding block(s)"
            )
        if landed_count != str(posted_count):
            errors.append(
                f"receipt census mismatch: landed={landed_count} but the record "
                f"carries {posted_count} posted finding(s); a POSTED record "
                f"requires every posted finding landed"
            )
        if landed_count != str(len(yes_lines)):
            errors.append(
                f"receipt census mismatch: landed={landed_count} but the receipt "
                f"carries {len(yes_lines)} landed=yes line(s)"
            )
        if len(lines) < posted_count:
            errors.append(
                f"receipt incomplete: {posted_count} posted finding(s) but only "
                f"{len(lines)} landing line(s)"
            )
    if mode == "incomplete" and not no_lines:
        errors.append(
            "incomplete record without unlanded evidence: at least one "
            "landed=no line is required while findings remain pending"
        )
    matched: set[int] = set()
    for entry in lines:
        candidates = [
            index
            for index, block in enumerate(all_blocks)
            if block.get("file") == entry["file"] and block.get("line") == entry["line"]
            and index not in matched
            # Pairing polarity: a landed=yes line claims LANDED evidence, so
            # it must pair with a posted block; on a POSTED record a
            # landed=no line admits the finding did not land and may only
            # pair with a pending block (a posted block absorbing a
            # landed=no line would let an unlanded finding pass as POSTED);
            # on an INCOMPLETE record a landed=no line may pair with any
            # block (the unlanded-set record).
            and (
                entry["landed"] == "yes"
                or mode != "posted"
                or index not in posted_indices
            )
        ]
        if not candidates:
            kind = "posted finding block" if entry["landed"] == "yes" else "finding block"
            errors.append(
                f"receipt identity mismatch: no {kind} matches "
                f"file={entry['file']} line={entry['line']} "
                f"(landed={entry['landed']})"
            )
            continue
        index = candidates[0]
        matched.add(index)
        block = all_blocks[index]
        if not entry["fragment"]:
            errors.append(f"receipt fragment empty: file={entry['file']} line={entry['line']}")
        elif entry["fragment"] not in block.get("comment", ""):
            errors.append(
                f"receipt fragment not in comment: file={entry['file']} "
                f"line={entry['line']} fragment={entry['fragment']!r}"
            )
        if entry["landed"] == "yes" and not entry["comment"]:
            errors.append(
                f"receipt comment id empty: file={entry['file']} line={entry['line']}"
            )
    if mode == "posted":
        uncovered = [
            all_blocks[index]
            for index in sorted(posted_indices - matched)
        ]
        for block in uncovered:
            errors.append(
                f"receipt coverage gap: posted finding "
                f"file={block.get('file')} line={block.get('line')} has no "
                f"landing line"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("staging_doc", type=Path)
    args = parser.parse_args()
    try:
        text = args.staging_doc.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"unreadable staging document: {exc}", file=sys.stderr)
        return 1
    errors = check(text)
    for error in errors:
        print(f"landing receipt error: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
