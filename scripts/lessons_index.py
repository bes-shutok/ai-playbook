#!/usr/bin/env python3
"""Read-only single-file validator (gate) for the user-level lessons corpus.

Stdlib only. **Read-only**: this script NEVER opens any file for write. The only
writers are ``lessons_adopt.py`` (tag backfill) and ``lessons_migrate.py``.

Contract (plan: Two-Layer Lessons Corpus, 2026-06-29):
- A single path arg is the USER-LEVEL corpus (strict). Project files are NOT
  gated (convention layer).
- Parses ``## N. <Title>`` headings; for each lesson collects
  ``**Principle:** Family <X>`` lines from its body OUTSIDE fenced code blocks.
- Fence tracking is robust to UNBALANCED fences (resets ``in_fence=False`` at the
  start of each lesson heading). See ``lessons_corpus.iter_lessons``.
- Hard violations (exit 1):
    * duplicate ``UL#N`` (silent-overwrite hazard, lesson #77)
    * a lesson with zero or >1 family tag (counted outside fences)
    * a tag whose ``<X>`` is not in ``VALID_FAMILIES`` / ``excluded`` /
      ``unclassified`` (the gate surfaces catalog growth as ``invalid-family``).
- On success (exit 0): one OK line + per-family counts + total + ``unclassified``
  count.
- On failure (exit 1): ``UL#N: <category>`` lines
  (``duplicate`` | ``untagged`` | ``multiple-tags`` | ``invalid-family``); never
  echo raw tag free-text.
- ``--selftest``: in-memory fixtures ONLY. Does NOT parse the catalog (a
  pre-emptive catalog-vs-``VALID_FAMILIES`` check was routed to Monitor).

Threat model (documented in learn Step 6.6): ``~/.ai-playbook/scripts/`` is
trusted; stdout is never ``eval``'d (unlike a lock script). This script is
read-only and surfaces violations as plain text.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow ``import lessons_corpus`` whether run as a script or via ``python -m``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lessons_corpus  # noqa: E402

#: Program name used in violation output. The user corpus uses the ``UL#N``
#: namespace; the gate reports violations keyed by that namespace so an operator
#: reading the message maps it to the corpus, not a project file.
NAMESPACE = "UL"

#: The four hard-violation categories. Emitted exactly as these tokens (never raw
#: tag free-text) so callers can grep failure output deterministically.
DUPLICATE = "duplicate"
UNTAGGED = "untagged"
MULTIPLE_TAGS = "multiple-tags"
INVALID_FAMILY = "invalid-family"


def validate(text: str) -> tuple[list[str], dict[str, int], int]:
    """Validate corpus ``text``. Returns ``(violations, counts, total)``.

    ``violations``: a list of ``f"{NAMESPACE}#{n}: <category>"`` lines (empty on
    success). Categories are the four constants above; raw tag free-text is never
    echoed (lesson #157/#158-style information-leak avoidance).

    ``counts``: family-letter -> number of validly-tagged lessons (only lessons
    that PASS all checks are counted; a lesson with an ``unclassified`` tag counts
    under the ``unclassified`` key, not a family letter).

    ``total``: number of validated lessons (excludes duplicates and any lesson
    that produced a violation).

    Validation order (the FIRST matching category wins; later checks are skipped
    for that lesson): duplicate -> untagged -> multiple-tags -> invalid-family.
    """
    seen: set[int] = set()
    violations: list[str] = []
    counts: dict[str, int] = {}
    total = 0

    for lesson in lessons_corpus.iter_lessons(text):
        if lesson.number in seen:
            violations.append(f"{NAMESPACE}#{lesson.number}: {DUPLICATE}")
            continue
        seen.add(lesson.number)

        if not lesson.tags:
            violations.append(f"{NAMESPACE}#{lesson.number}: {UNTAGGED}")
            continue
        if len(lesson.tags) > 1:
            violations.append(f"{NAMESPACE}#{lesson.number}: {MULTIPLE_TAGS}")
            continue

        token = lesson.tags[0]
        if not lessons_corpus.parse_tag_token(token).valid:
            violations.append(f"{NAMESPACE}#{lesson.number}: {INVALID_FAMILY}")
            continue

        # Valid single tag. Count it under the token (a family letter A-H or one
        # of the extra values ``excluded`` / ``unclassified``).
        counts[token] = counts.get(token, 0) + 1
        total += 1

    return violations, counts, total


def run(corpus_path: str) -> int:
    """Validate the user-level corpus at ``corpus_path`` (read-only).

    Returns the process exit code (0 = clean, 1 = violations).
    """
    path = Path(corpus_path)
    text = path.read_text(encoding="utf-8")
    violations, counts, total = validate(text)

    if violations:
        for line in violations:
            print(line)
        return 1

    # Success: one OK line + per-family counts + total + unclassified count.
    # Family letters are emitted in canonical A-H order for deterministic output;
    # ``excluded`` and ``unclassified`` follow (any that are zero are omitted).
    print(f"OK: {total} lessons validated")
    for letter in sorted(lessons_corpus.VALID_FAMILIES):
        n = counts.get(letter, 0)
        if n:
            print(f"Family {letter}: {n}")
    if counts.get("excluded"):
        print(f"excluded: {counts['excluded']}")
    unclassified = counts.get("unclassified", 0)
    print(f"unclassified: {unclassified}")
    return 0


def _selftest_check(label: str, condition: bool, detail: str = "") -> bool:
    """Print PASS/FAIL for one selftest assertion. Returns ``condition``."""
    if condition:
        print(f"PASS: {label}")
    else:
        msg = f"FAIL: {label}" + (f" - {detail}" if detail else "")
        print(msg)
    return condition


def selftest() -> int:
    """In-memory fixtures only.

    No filesystem fallback chain, no ``~/`` expansion, no catalog parse. Each
    fixture builds a synthetic corpus string and runs ``validate`` directly.
    """
    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        all_ok = _selftest_check(label, cond, detail) and all_ok

    # --- Fixture: contiguous 3-lesson corpus (Family A, B, excluded) -> exit 0 ---
    corpus = (
        "## 1. First\n"
        "**Principle:** Family A (reason A)\n"
        "body A\n"
        "## 2. Second\n"
        "**Principle:** Family B (reason B)\n"
        "body B\n"
        "## 3. Third\n"
        "**Principle:** Family excluded (process-only)\n"
        "body C\n"
    )
    violations, counts, total = validate(corpus)
    check("3-lesson corpus: no violations", not violations,
          "; ".join(violations))
    check("3-lesson corpus: total==3", total == 3, f"total={total}")
    check("3-lesson corpus: Family A==1", counts.get("A") == 1, str(counts))
    check("3-lesson corpus: Family B==1", counts.get("B") == 1, str(counts))
    check("3-lesson corpus: excluded==1", counts.get("excluded") == 1, str(counts))

    # --- Fixture: duplicate ## 2. -> exit 1, duplicate ---
    corpus = (
        "## 1. First\n"
        "**Principle:** Family A (r)\n"
        "## 2. Second\n"
        "**Principle:** Family B (r)\n"
        "## 2. Duplicate\n"
        "**Principle:** Family C (r)\n"
    )
    violations, _, _ = validate(corpus)
    check("duplicate ## 2.: one violation", len(violations) == 1,
          "; ".join(violations))
    check("duplicate ## 2.: category duplicate",
          violations == ["UL#2: duplicate"] if violations else False,
          "; ".join(violations))

    # --- Fixture: untagged lesson -> exit 1, untagged naming UL#N ---
    corpus = (
        "## 1. Tagged\n"
        "**Principle:** Family A (r)\n"
        "## 2. Untagged\n"
        "no tag here\n"
    )
    violations, _, _ = validate(corpus)
    check("untagged: one violation", len(violations) == 1,
          "; ".join(violations))
    check("untagged: UL#2: untagged",
          violations == ["UL#2: untagged"] if violations else False,
          "; ".join(violations))

    # --- Fixture: parametrized taxonomy table ---
    def one_lesson(tag_token: str) -> str:
        """Build a one-lesson corpus whose single tag uses ``tag_token``.

        ``tag_token`` is the literal text after ``Family`` (may be empty, contain
        trailing characters, etc.). A single space separates the token from the
        mandatory ``(reason)`` parenthetical; the end-of-line (no-parenthetical)
        variant is exercised separately.
        """
        return f"## 1. T\n**Principle:** Family {tag_token} (reason)\nbody\n"

    ok_tokens = {
        "A": "Family A ok",
        "H": "Family H ok",
        "excluded": "Family excluded ok",
        "unclassified": "Family unclassified ok",
    }
    for token, label in ok_tokens.items():
        violations, counts, total = validate(one_lesson(token))
        check(f"taxonomy OK [{label}]", not violations and total == 1,
              "; ".join(violations) + " | " + str(counts))

    invalid_tokens = {
        "-": "Family - invalid (hyphen)",
        "Q": "Family Q invalid",
        "a": "Family a invalid (lowercase)",
        "AB": "Family AB invalid (two-letter)",
        "": "Family invalid (empty token)",
    }
    for token, label in invalid_tokens.items():
        violations, _, _ = validate(one_lesson(token))
        check(f"taxonomy INVALID [{label}]",
              violations == ["UL#1: invalid-family"] if violations else False,
              "; ".join(violations))

    # End-of-line variant: tag at the very end of the line with no parenthetical.
    corpus = "## 1. T\n**Principle:** Family A\nbody\n"
    violations, counts, total = validate(corpus)
    check("taxonomy OK [Family A at end-of-line]",
          not violations and counts.get("A") == 1 and total == 1,
          "; ".join(violations) + " | " + str(counts))

    # --- Fixture: fenced block with a literal tag line + one real tag -> exit 0,
    #     OK-line reports Family A: 1 (the fenced pseudo-tag is NOT counted) ---
    corpus = (
        "## 1. Fenced\n"
        "```\n"
        "**Principle:** Family A (example)\n"
        "```\n"
        "**Principle:** Family A (real)\n"
    )
    violations, counts, total = validate(corpus)
    check("fenced pseudo-tag: no violations", not violations,
          "; ".join(violations))
    check("fenced pseudo-tag: Family A==1 (not 2)",
          counts.get("A") == 1 and total == 1, str(counts))

    # --- Fixture: UNBALANCED fence (r2 Blocker) - ODD fence count ---
    # A ```python opened and never closed (in lesson 1, which is itself validly
    # tagged so the corpus can exit 0), followed by THREE later lessons each
    # carrying a real Family A tag after the dangling-open fence. A naive
    # whole-file toggle would invert in/out state and report 0 (or wrong count).
    corpus = (
        "## 1. Opens fence\n"
        "**Principle:** Family B (opener)\n"
        "```python\n"
        "code = 'fence never closed'\n"
        "## 2. After dangling fence\n"
        "**Principle:** Family A (r2)\n"
        "## 3. Still after\n"
        "**Principle:** Family A (r2)\n"
        "## 4. Third\n"
        "**Principle:** Family A (r2)\n"
    )
    violations, counts, total = validate(corpus)
    check("unbalanced fence: no violations", not violations,
          "; ".join(violations))
    check("unbalanced fence: Family A==3 (heading-boundary reset)",
          counts.get("A") == 3, str(counts))
    check("unbalanced fence: all 4 lessons validated", total == 4,
          f"total={total}")

    # Second unbalanced-fence fixture: a fence RE-OPENED AND CLOSED in a later
    # lesson, with a tagged lesson AFTER it -> counted. Pins heading-boundary
    # RE-SYNC across sections (not just first-section reset). Lesson 1 carries a
    # valid tag and the dangling-open fence so the corpus can exit 0.
    corpus = (
        "## 1. Dangling open\n"
        "**Principle:** Family B (opener)\n"
        "```python\n"
        "## 2. Re-open and close in body\n"
        "**Principle:** Family B (in lesson 2 body, before re-opened fence)\n"
        "```\n"
        "still inside lesson-2 fence\n"
        "```\n"
        "## 3. Tagged after closed fence\n"
        "**Principle:** Family A (r2 re-sync)\n"
    )
    violations, counts, total = validate(corpus)
    check("re-sync fence: no violations", not violations,
          "; ".join(violations))
    check("re-sync fence: lesson-3 Family A==1 counted",
          counts.get("A") == 1, str(counts))
    check("re-sync fence: Family B==2 (lessons 1 and 2)",
          counts.get("B") == 2, str(counts))
    check("re-sync fence: total==3", total == 3, f"total={total}")

    # --- Fixture: two real tags outside fences -> exit 1, multiple-tags ---
    corpus = (
        "## 1. Two tags\n"
        "**Principle:** Family A (r)\n"
        "**Principle:** Family B (r)\n"
    )
    violations, _, _ = validate(corpus)
    check("two tags: one violation", len(violations) == 1,
          "; ".join(violations))
    check("two tags: UL#1: multiple-tags",
          violations == ["UL#1: multiple-tags"] if violations else False,
          "; ".join(violations))

    # --- Fixture: violation output format - matches the documented regex ---
    import re
    pattern = re.compile(r"^#?\d+: (duplicate|untagged|multiple-tags|invalid-family)$")
    sample_violations = [
        "UL#1: duplicate",
        "UL#2: untagged",
        "UL#3: multiple-tags",
        "UL#4: invalid-family",
        "1: duplicate",  # bare-numeric form also tolerated
    ]
    for v in sample_violations:
        # Strip the "UL#" prefix to test the documented regex (which allows an
        # optional leading # but not the "UL" letters). The category suffix is
        # what the regex is really about; the namespace prefix is a stable
        # convention the operator reads.
        stripped = v.split(": ", 1)[1]
        candidate_num = v.split(":", 1)[0].replace("UL#", "")
        normalized = f"{candidate_num}: {stripped}"
        check(f"violation format [{v}]",
              bool(pattern.match(normalized)),
              f"normalized={normalized!r}")

    # Confirm raw tag free-text is NEVER echoed in violation output.
    corpus = (
        "## 1. Leaks\n"
        "**Principle:** Family Q (SECRET-reason-never-echo)\n"
    )
    violations, _, _ = validate(corpus)
    leaked = any("SECRET" in v for v in violations)
    check("violation never echoes raw tag free-text",
          violations == ["UL#1: invalid-family"] and not leaked,
          "; ".join(violations))

    # --- Summary line ---
    if all_ok:
        print("selftest OK")
        return 0
    print("selftest FAILED")
    return 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    if len(args) == 1 and args[0] == "--selftest":
        return selftest()

    if len(args) == 1 and not args[0].startswith("-"):
        # Single path arg = user corpus (read-only). Project files are NOT gated.
        return run(args[0])

    sys.stderr.write(
        "usage: lessons_index.py <user_corpus> | --selftest\n"
        "  <user_corpus>  validate the user-level lessons corpus (read-only)\n"
        "  --selftest     run in-memory fixtures\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
