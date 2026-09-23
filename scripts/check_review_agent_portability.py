#!/usr/bin/env python3
"""Portability regression checker for the shared review-agent catalogs.

Scans Markdown files under `agents/skills/review-agents/` (or the positional
paths given) for stack-specific tokens that do not belong in a shared,
language-agnostic catalog: framework and product names, language-syntax
identifiers, build-tool invocations, test-class suffix names,
repository-absolute paths, and ticket-prefix shapes.

A line carrying the placement marker `<!-- portability: abstract -->`
anywhere in the line is excused: its tokens are an explicitly abstract
illustration. In a GFM table row the marker rides in the final cell after
the cell text.

Exit codes: 0 clean, 1 violations reported, 2 usage error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLACEMENT_MARKER = "<!-- portability: abstract -->"

# category -> list of compiled patterns; each match is reported as one hit.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    *(
        ("framework-product", re.compile(rf"\b{token}\b"))
        for token in (
            "Spring",
            "Hibernate",
            "Mockito",
            "EasyMock",
            "JUnit",
            "TestNG",
            "Kafka",
            "RocketMQ",
            "RabbitMQ",
            "Django",
            "Rails",
            "React",
            "Angular",
            "Vue",
            "Modulith",
            "Javadoc",
            "KDoc",
            "ArgumentCaptor",
            "Redis",
        )
    ),
    *(
        ("language-name", re.compile(rf"\b{token}\b"))
        for token in (
            "Java",
            "Kotlin",
            "Python",
            "Ruby",
            "Scala",
            "JavaScript",
            "TypeScript",
            "PHP",
            "Swift",
        )
    ),
    ("language-name", re.compile(r"\bC#\b")),
    ("language-syntax", re.compile(r"\b(java|kotlin|javax)\.[A-Za-z]")),
    *(
        ("language-syntax", re.compile(rf"\b{token}\b"))
        for token in (
            "UnsupportedOperationException",
            "NotImplementedError",
            "ArgumentNullException",
            "NullPointerException",
            "IllegalArgumentException",
            "RuntimeException",
        )
    ),
    ("build-tool", re.compile(r"\b(mvn|gradle|npm|yarn|pnpm|cargo|dotnet)\b")),
    ("build-tool", re.compile(r"\bpip\s+install\b")),
    ("test-suffix", re.compile(r"\b[A-Z][A-Za-z0-9_]*Test\b")),
    ("repo-path", re.compile(r"(/Users/|/home/|\b[A-Za-z]:[\\/])")),
    ("ticket-prefix", re.compile(r"\b[A-Z]{2,12}-\d+\b")),
]

# Letter-digit hyphen shapes that are technical identifiers, not tickets.
TICKET_ALLOWLIST = {"UTF-8", "UTF-16", "UTF-32", "SHA-1", "SHA-256", "SHA-512", "ISO-8601", "Base-64"}


def iter_catalog_files(paths: list[Path]) -> list[Path]:
    if paths:
        files: list[Path] = []
        for path in paths:
            if path.is_dir():
                files.extend(sorted(path.rglob("*.md")))
            else:
                files.append(path)
        return files
    root = repo_root(Path.cwd())
    catalog_dir = root / "agents" / "skills" / "review-agents"
    if not catalog_dir.is_dir():
        return []
    return sorted(catalog_dir.glob("*.md"))


def repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report stack-specific tokens in shared review-agent catalogs."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Catalog files or directories to scan (default: agents/skills/review-agents/*.md).",
    )
    args = parser.parse_args(argv)

    violations: list[str] = []
    for path in iter_catalog_files(args.paths):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        for lineno, line in enumerate(text.splitlines(), start=1):
            if PLACEMENT_MARKER in line:
                continue
            for category, pattern in PATTERNS:
                for match in pattern.finditer(line):
                    token = match.group(0)
                    if category == "ticket-prefix" and token in TICKET_ALLOWLIST:
                        continue
                    violations.append(
                        f"{path}:{lineno}: {category}: {token}"
                    )

    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
