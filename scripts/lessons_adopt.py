#!/usr/bin/env python3
"""Tag-backfill writer for the user-level lessons corpus (SRP).

Separate script from the read-only gate (``lessons_index.py``) per the
single-responsibility invariant: this is the ONLY writer that backfills family
tags, and it is a MANUAL tool (never invoked automatically by ``learn``).

Contract (plan: Two-Layer Lessons Corpus, 2026-06-29):
- ``--tag-unclassified <lessons_file>``: mark every untagged lesson's first body
  line ``**Principle:** Family unclassified (pre-gate migration)``. Idempotent.
- Safety contract: refuse if ``<lessons_file>`` has uncommitted git changes
  (``git diff --quiet -- <file>`` must succeed; clean pre-edit state means
  ``git checkout -- <file>`` is full recovery, so no ``.bak``).
- Write via the shared ``lessons_corpus.atomic_write_text`` helper
  (``O_EXCL|O_NOFOLLOW`` ``.tmp`` + ``os.replace``; cite #119 - diverging write
  contracts on the same highest-value asset are forbidden).
- Shared collection logic (cite #119): MUST reuse the heading parser,
  fence-aware tag-collection (incl. heading-boundary reset), and ``VALID_FAMILIES``
  from ``lessons_corpus`` (import downward; do NOT ``import lessons_index`` -
  that couples the read-only gate to a mutator, Family F).
- Usage constraint: whole-file rewriter; do NOT run concurrently with a ``learn``
  append. No lock, no ``.bak``; git-clean precondition is the recovery.

Threat model: the git-clean precondition is the sole guard against clobbering
uncommitted edits. ``git checkout -- <file>`` is full recovery precisely because
the file was clean before this tool ran. There is no ``.bak`` and no lock; the
operator ensures no concurrent ``learn`` append (both rewrite the whole file,
last-writer-wins).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Allow ``import lessons_corpus`` whether run as a script or via ``python -m``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lessons_corpus  # noqa: E402  (shared primitive, intentional import)

# Same heading shape the shared parser uses (``lessons_corpus._HEADING_RE``); kept
# here so the adopter can locate the insertion point (heading line index) for each
# lesson without reaching into the parser's private symbol.
_HEADING_RE = re.compile(r"^##\s+(\d+)\.\s+(.*)$")

#: Marker written as the first body line of an untagged lesson by
#: ``--tag-unclassified``. The parenthetical is mandatory free-text (the gate
#: requires it; the gate ignores its content).
UNCLASSIFIED_TAG_LINE = "**Principle:** Family unclassified (pre-gate migration)"


def _git_is_clean(file_path: str) -> bool:
    """Return True iff ``file_path`` has NO uncommitted git changes.

    Uses ``git diff --quiet -- <file>``: exit 0 means clean (no unstaged changes
    to that path). The repo root is resolved from ``file_path`` so the command
    works regardless of the caller's CWD. A non-git directory (exit 128) is
    treated as NOT clean (refuse to run; the recovery recipe assumes git).
    """
    abspath = Path(file_path).resolve()
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", "--", str(abspath)],
            cwd=str(abspath.parent),
            capture_output=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def plan_rewrites(text: str) -> list[int]:
    """Return the list of lesson NUMBERS that are untagged and need a backfill.

    A lesson is "untagged" iff ``lessons_corpus.iter_lessons`` reports zero tags
    for it (tags are collected OUTSIDE fenced code blocks, with heading-boundary
    fence reset). Reusing the shared collector (cite #119) guarantees the adopter
    and the gate agree on what counts as a tag - a fenced pseudo-tag does NOT
    protect a lesson from being rewritten, and a real tag after a dangling-open
    fence DOES protect it.
    """
    return [lesson.number for lesson in lessons_corpus.iter_lessons(text) if not lesson.tags]


def rewrite_text(text: str, tag_line: str = UNCLASSIFIED_TAG_LINE) -> tuple[str, int]:
    """Return ``(new_text, n_rewritten)``: insert ``tag_line`` as the first body
    line of every untagged lesson.

    The rewrite is structural and byte-stable outside the inserted lines: it
    walks the original line list, and immediately after each untagged lesson's
    HEADING line it inserts the tag line. A lesson is "untagged" per the shared
    fence-aware collector. Idempotent: a lesson that already has any tag (valid
    or not, outside fences) is left untouched; re-running on already-backfilled
    text rewrites zero lessons.
    """
    lines = text.splitlines(keepends=True)

    # Map heading line-index -> is-untagged, by replaying the shared parser's
    # lesson segmentation. iter_lessons yields lessons in document order; we need
    # the heading line index for each so we know WHERE to insert.
    heading_indices: list[int] = []
    for idx, line in enumerate(lines):
        if _HEADING_RE.match(line):
            heading_indices.append(idx)

    # Build a set of heading line-indices whose lesson is untagged.
    untagged_heading_indices: set[int] = set()
    # iter_lessons segments the same way; pair its output with heading_indices.
    lessons = list(lessons_corpus.iter_lessons(text))
    if len(lessons) != len(heading_indices):
        # Defensive: the parser and our index list must agree. If they ever
        # diverge, refuse rather than risk inserting at a wrong offset.
        raise RuntimeError(
            "lessons_adopt: parser/heading-index mismatch "
            f"({len(lessons)} lessons vs {len(heading_indices)} headings)"
        )
    for lesson, h_idx in zip(lessons, heading_indices, strict=True):
        if not lesson.tags:
            untagged_heading_indices.add(h_idx)

    # Insert the tag line right after each untagged lesson's heading. Walk in
    # REVERSE so earlier insertions don't shift later indices.
    out = list(lines)
    insert_count = 0
    for h_idx in sorted(untagged_heading_indices, reverse=True):
        # Preserve the line-ending style of the heading line for the inserted tag.
        heading_line = out[h_idx]
        eol = "\n" if heading_line.endswith("\n") else ""
        # If the heading has NO trailing newline (last line of file), the tag
        # line carries its own newline so the structure stays valid.
        inserted = f"{tag_line}\n" if not eol else f"{tag_line}{eol}"
        if not eol:
            # Heading was the final line without newline: add a newline after it
            # before the tag so the heading itself stays well-formed.
            out[h_idx] = heading_line + "\n"
        out.insert(h_idx + 1, inserted)
        insert_count += 1

    new_text = "".join(out)
    return new_text, insert_count


def tag_unclassified(file_path: str) -> int:
    """Backfill ``Family unclassified`` tags into every untagged lesson in
    ``file_path``. Returns the process exit code (0 = success).

    Refuses if the file has uncommitted git changes. Writes atomically via
    ``lessons_corpus.atomic_write_text``. Prints how many lessons were rewritten.
    """
    path = Path(file_path)
    if not path.is_file():
        sys.stderr.write(f"lessons_adopt: not a file: {path}\n")
        return 2

    if not _git_is_clean(str(path)):
        sys.stderr.write(
            f"lessons_adopt: refusing to rewrite {path}: uncommitted git changes "
            f"present. Commit or stash first; 'git checkout -- {path}' is the "
            f"post-run recovery ONLY because the file is clean before this tool "
            f"runs.\n"
        )
        return 1

    text = path.read_text(encoding="utf-8")
    new_text, n = rewrite_text(text)
    if n == 0:
        print(f"lessons_adopt: 0 lessons rewritten (all already tagged)")
        return 0

    lessons_corpus.atomic_write_text(str(path), new_text)
    print(f"lessons_adopt: {n} lesson(s) rewritten with 'Family unclassified'")
    return 0


def _selftest_check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
    return condition


def selftest() -> int:
    """In-memory fixtures only.

    Fixtures:
    - one tagged + one fenced pseudo-tag (with a real tag outside the fence) +
      one untagged -> rewrites EXACTLY the untagged one.
    - unbalanced-fence corpus is NOT over-rewritten: already-tagged lessons
      after a dangling-open fence are left tagged (the fence-aware collector with
      heading-boundary reset sees their real tags).
    - idempotency: re-running on backfilled text rewrites zero lessons.
    """
    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        all_ok = _selftest_check(label, cond, detail) and all_ok

    # --- Fixture: tagged + fenced-pseudo-tag + untagged -> rewrite the untagged only
    corpus = (
        "## 1. Tagged\n"
        "**Principle:** Family A (real)\n"
        "body A\n"
        "## 2. Fenced pseudo-tag (has a real tag too)\n"
        "```\n"
        "**Principle:** Family B (decoy inside fence)\n"
        "```\n"
        "**Principle:** Family B (real outside)\n"
        "## 3. Untagged\n"
        "no tag here\n"
    )
    new_text, n = rewrite_text(corpus)
    check("tagged+fenced+untagged: rewrites exactly 1", n == 1, f"n={n}")
    # The rewritten text should contain the unclassified tag exactly once, and
    # it should appear immediately after the "## 3. Untagged" heading.
    check("tagged+fenced+untagged: one unclassified tag inserted",
          new_text.count(UNCLASSIFIED_TAG_LINE) == 1,
          f"count={new_text.count(UNCLASSIFIED_TAG_LINE)}")
    # The original real tags are preserved verbatim.
    check("tagged+fenced+untagged: Family A preserved",
          "**Principle:** Family A (real)\n" in new_text)
    check("tagged+fenced+untagged: Family B (real outside) preserved",
          "**Principle:** Family B (real outside)\n" in new_text)
    # The fenced decoy is preserved (unchanged) - we did not touch fence bodies.
    check("tagged+fenced+untagged: fenced decoy preserved",
          "**Principle:** Family B (decoy inside fence)\n" in new_text)
    # The untagged lesson's body is preserved.
    check("tagged+fenced+untagged: untagged body preserved",
          "no tag here\n" in new_text)
    # plan_rewrites agrees: only lesson 3 is untagged.
    check("plan_rewrites: only lesson 3 untagged",
          plan_rewrites(corpus) == [3], str(plan_rewrites(corpus)))

    # --- Fixture: unbalanced fence - already-tagged lessons after dangling-open
    #     fence are LEFT TAGGED (not over-rewritten to unclassified).
    corpus = (
        "## 1. Opens fence, has real tag\n"
        "**Principle:** Family A (opener)\n"
        "```python\n"
        "code = 'never closed'\n"
        "## 2. After dangling fence, has real tag\n"
        "**Principle:** Family B (after)\n"
        "## 3. After dangling fence, also tagged\n"
        "**Principle:** Family A (also after)\n"
    )
    new_text, n = rewrite_text(corpus)
    check("unbalanced fence: zero rewrites (all tagged)", n == 0, f"n={n}")
    check("unbalanced fence: no unclassified tag inserted",
          UNCLASSIFIED_TAG_LINE not in new_text)
    check("unbalanced fence: real tags preserved",
          "**Principle:** Family B (after)\n" in new_text
          and "**Principle:** Family A (also after)\n" in new_text)

    # --- Fixture: idempotency - re-running on backfilled text rewrites 0 ---
    corpus = (
        "## 1. Untagged\n"
        "body one\n"
        "## 2. Tagged\n"
        "**Principle:** Family A (real)\n"
    )
    once, n1 = rewrite_text(corpus)
    check("idempotency: first pass rewrites 1", n1 == 1, f"n1={n1}")
    twice, n2 = rewrite_text(once)
    check("idempotency: second pass rewrites 0", n2 == 0, f"n2={n2}")
    check("idempotency: second pass is a no-op (text stable)", once == twice)

    if all_ok:
        print("selftest OK")
        return 0
    print("selftest FAILED")
    return 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    if len(args) == 1 and args[0] == "--selftest":
        return selftest()

    if len(args) == 2 and args[0] == "--tag-unclassified":
        return tag_unclassified(args[1])

    sys.stderr.write(
        "usage: lessons_adopt.py --tag-unclassified <lessons_file> | --selftest\n"
        "  --tag-unclassified <file>  backfill untagged lessons with "
        "'Family unclassified'\n"
        "  --selftest                 run in-memory fixtures\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
