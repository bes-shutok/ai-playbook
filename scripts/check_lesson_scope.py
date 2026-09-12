#!/usr/bin/env python3
"""Lesson scope duplicate validator.

Mechanical-only scope: flags a full rule body that appears in both the
project lessons corpus and the company guidelines master. Semantic scope
judgment stays with the learn workflow; this script never moves, rewrites,
or classifies lessons.

Block model note: content before the first heading (preamble) is not
turned into a block and is therefore excluded from comparison. Heading
detection is fence-aware: a `#`-prefixed line inside an open ``` or ~~~
code fence is body text, not a heading boundary. A fence still open at
EOF is a loud failure (exit 2).

Blocks under MIN_RULE_WORDS (25) normalized words are skipped as
presumed witness pointers and never match.

Consumer contract note: WARNING on stderr with exit 0 is the designed
cold start for direct personal-repo runs (a missing corpus or master).
Gate consumers that pre-resolve both paths (like the done pre-commit
audit) must treat any WARNING line as a placement-path resolution
failure and stop.

Matching runs difflib.SequenceMatcher with autojunk=False so
popular-character discounting does not suppress near-verbatim
long-rule matches.

Exit codes: 0 = no duplicate full rule or cold start; 1 = duplicate full
rule; 2 = usage, IO error, or unclosed code fence.
"""

from __future__ import annotations

import os
import re
import sys
import difflib
from dataclasses import dataclass

DUPLICATE_RATIO = 0.90
MIN_RULE_WORDS = 25

_HEADING_RE = re.compile(r"^#{1,3} ")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_ENUM_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
_WS_RE = re.compile(r"\s+")

USAGE = (
    "usage: check_lesson_scope.py <project_corpus> <company_master> "
    "(exit 0 clean or cold start, WARNING on stderr when a file is missing "
    "or parses to zero blocks (designed cold start for direct runs; "
    "pre-resolving gates must stop on any WARNING); "
    "exit 1 duplicate, DUPLICATE: lines on stdout; exit 2 usage, IO error, "
    "or unclosed code fence)"
)


@dataclass(frozen=True)
class Block:
    line: int  # 1-based heading line number
    heading: str  # display heading text without leading hashes
    text: str  # normalized heading + body


def _normalize(text: str) -> str:
    stripped = text.strip().lstrip("#").strip()
    stripped = _ENUM_RE.sub("", stripped, count=1)
    return _WS_RE.sub(" ", stripped.lower()).strip()


def _make_block(lines: list[str], start_line: int) -> Block:
    heading_line = lines[0].lstrip("#").strip()
    body = _normalize("\n".join(lines))
    return Block(line=start_line, heading=heading_line, text=body)


class UnclosedFenceError(ValueError):
    """A code fence was still open at EOF; args[0] is the 1-based opening line."""


def parse_blocks(text: str) -> list[Block]:
    lines = text.splitlines()
    # Fence-aware heading scan: a `#`-prefixed line inside an open ``` or
    # ~~~ fence is body text, not a block boundary. CommonMark closing
    # rule: a fence line closes the open fence only when it uses the SAME
    # fence character, its run is at least as long as the opener's, and
    # nothing but optional whitespace follows the run (an info string is
    # legal only on the opening line).
    fence_char: str | None = None
    fence_len = 0
    fence_line = 0
    heading_indexes: list[int] = []
    for i, line in enumerate(lines):
        fence_match = _FENCE_RE.match(line)
        if fence_char is None:
            if fence_match:
                fence_char = fence_match.group(1)[0]
                fence_len = len(fence_match.group(1))
                fence_line = i + 1
            elif _HEADING_RE.match(line):
                heading_indexes.append(i)
        elif fence_match:
            run = fence_match.group(1)
            rest = line[fence_match.end():]
            if run[0] == fence_char and len(run) >= fence_len and not rest.strip():
                fence_char = None
    if fence_char is not None:
        raise UnclosedFenceError(fence_line)
    if not heading_indexes:
        return [_make_block(lines, 1)] if lines else []
    blocks: list[Block] = []
    for pos, idx in enumerate(heading_indexes):
        end = heading_indexes[pos + 1] if pos + 1 < len(heading_indexes) else len(lines)
        blocks.append(_make_block(lines[idx:end], idx + 1))
    return blocks


def _read(path: str) -> str | None:
    if not os.path.exists(path):
        print(f"WARNING: file not found (cold start), skipping: {path}", file=sys.stderr)
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _load_blocks(path: str, text: str) -> list[Block]:
    try:
        blocks = parse_blocks(text)
    except UnclosedFenceError as exc:
        print(f"ERROR: unclosed code fence in {path} (opened near line {exc.args[0]})", file=sys.stderr)
        raise SystemExit(2) from exc
    if not blocks:
        print(f"WARNING: existing file parses to zero blocks (empty or whitespace-only): {path}", file=sys.stderr)
    return blocks


def find_duplicates(corpus_path: str, corpus_blocks: list[Block], master_path: str, master_blocks: list[Block]) -> list[str]:
    corpus_sized = [(block, len(block.text.split()), len(block.text)) for block in corpus_blocks]
    master_sized = [(block, len(block.text.split()), len(block.text)) for block in master_blocks]
    reports: list[str] = []
    for corpus_block, corpus_words, len_a in corpus_sized:
        for master_block, master_words, len_b in master_sized:
            # Cheap bounds first: word floor, then the ratio upper bound
            # 2*min_len/(len_a+len_b); only then pay for SequenceMatcher.
            if min(corpus_words, master_words) < MIN_RULE_WORDS:
                continue
            if 2 * min(len_a, len_b) / (len_a + len_b) < DUPLICATE_RATIO:
                continue
            ratio = difflib.SequenceMatcher(None, corpus_block.text, master_block.text, autojunk=False).ratio()
            if ratio >= DUPLICATE_RATIO:
                reports.append(
                    f"DUPLICATE: {corpus_path}:{corpus_block.line} {corpus_block.heading}"
                    f" <-> {master_path}:{master_block.line} {master_block.heading}"
                )
    return reports


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(USAGE, file=sys.stderr)
        return 2
    corpus_path, master_path = argv[1], argv[2]
    if not corpus_path.strip() or not master_path.strip():
        print(USAGE, file=sys.stderr)
        return 2
    corpus_text = _read(corpus_path)
    if corpus_text is None:
        return 0
    master_text = _read(master_path)
    if master_text is None:
        return 0
    corpus_blocks = _load_blocks(corpus_path, corpus_text)
    master_blocks = _load_blocks(master_path, master_text)
    reports = find_duplicates(corpus_path, corpus_blocks, master_path, master_blocks)
    for report in reports:
        print(report)
    return 1 if reports else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
