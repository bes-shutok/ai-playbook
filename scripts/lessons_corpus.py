"""Shared primitives for the lessons-index gate, adopter, and migrator.

Single source of truth (cite development_lessons.md #119 - diverging collection
contracts on the same asset silently drop data; sibling collectors MUST use
byte-identical patterns or a shared helper).

Contains:
- ``VALID_FAMILIES`` - the family-letter set (authority: ``coding_guidelines.md``
  #17-#25). The catalog is the authority; this constant is a documented secondary
  view. On catalog growth, update this constant AND the catalog together as an
  explicit cross-project change; the gate surfaces the need by rejecting the
  first tag of a new family letter with ``invalid-family``.
- heading parser + fence-aware collector (robust to UNBALANCED fences; resets
  ``in_fence=False`` at each lesson heading).
- ``atomic_write_text`` - hardened ``.tmp`` + ``os.replace`` writer
  (``O_EXCL|O_NOFOLLOW`` kills the TOCTOU; cite #119).

Stdlib only. No third-party imports.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from dataclasses import dataclass

# Authority is coding_guidelines.md #17-#25. On catalog growth, update this
# constant and the catalog together as an explicit cross-project change; the
# gate surfaces the need by rejecting the first tag of a new family letter with
# ``invalid-family``.
VALID_FAMILIES: frozenset[str] = frozenset("ABCDEFGH")

# Legal non-letter tag values (always accepted regardless of catalog).
EXTRA_TAG_VALUES: frozenset[str] = frozenset({"excluded", "unclassified"})

# A tag line: ``**Principle:** Family <X> (<free-text reason>)``. The parenthetical
# is mandatory free text, ignored by the gate. ``<X>`` is a single token (one of
# A-H, ``excluded``, ``unclassified``). Match the token after ``Family`` up to the
# first whitespace; the rest is the parenthetical/reason.
_TAG_RE = re.compile(r"^\*\*Principle:\*\*\s+Family\s+(\S*)", re.MULTILINE)

# A lesson heading: ``## N. <Title>``. Numbering is per-layer (UL#N at user level,
# #N at project level); the parser is layer-agnostic.
_HEADING_RE = re.compile(r"^##\s+(\d+)\.\s+(.*)$")

# A fenced code block delimiter line: a line whose first non-space characters are
# three or more backticks (info string allowed after the opening fence).
_FENCE_RE = re.compile(r"^\s*```+")


@dataclass(frozen=True)
class Lesson:
    """A parsed lesson: its number, title, body lines, and the family tags found
    in its body OUTSIDE fenced code blocks."""

    number: int
    title: str
    body_lines: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class TagValue:
    """Validated tag value: either a family letter (in ``VALID_FAMILIES``), one of
    the extra values (``excluded``/``unclassified``), or invalid.

    ``raw`` is the exact token captured from the source line; the gate never echoes
    the free-text parenthetical, only the category (``invalid-family`` etc.).
    """

    raw: str
    valid: bool


def parse_tag_token(token: str) -> TagValue:
    """Classify a single tag token captured from a ``**Principle:** Family <X>``
    line. The token is the maximal non-space run after ``Family`` (the parenthetical
    follows a space and is not part of the token). Empty string (``Family`` with no
    token) is invalid.
    """
    if token in VALID_FAMILIES or token in EXTRA_TAG_VALUES:
        return TagValue(raw=token, valid=True)
    return TagValue(raw=token, valid=False)


def iter_lessons(text: str) -> Iterator[Lesson]:
    """Parse lessons from a corpus.

    A lesson is introduced by a ``## N. <Title>`` heading and its body runs until
    the next ``## N.`` heading or end-of-text. ``#``/``###`` headings do NOT start
    a lesson.

    Fence tracking is robust to UNBALANCED fences (r2 Blocker): ``in_fence`` is
    reset to ``False`` at the start of each lesson (a fenced block cannot legally
    span a ``## N.`` heading). A fence opened and never closed in a lesson body is
    treated as closed at end-of-section (defensive). Do NOT use a naive whole-file
    ```` ``` ```` toggle: the real corpus has an ODD fence count (verified), so a
    naive toggle inverts in/out state and silently drops real tags.

    The family tags collected for each lesson are the ``**Principle:** Family <X>``
    lines found in its body OUTSIDE fenced code blocks.
    """
    lines = text.splitlines()
    # Pre-split into (heading_index, body_start, body_end) runs so the fence state
    # resets cleanly per lesson. A lesson body is [its line+1, next heading line).
    starts: list[tuple[int, int, str]] = []  # (line_idx, number, title)
    for idx, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m:
            starts.append((idx, int(m.group(1)), m.group(2).strip()))

    for i, (idx, number, title) in enumerate(starts):
        body_start = idx + 1
        body_end = starts[i + 1][0] if i + 1 < len(starts) else len(lines)
        body = tuple(lines[body_start:body_end])

        tags: list[str] = []
        in_fence = False  # reset at each lesson (heading-boundary reset; r2 Blocker)
        for bline in body:
            if _FENCE_RE.match(bline):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = _TAG_RE.match(bline)
            if m:
                tags.append(m.group(1))

        yield Lesson(number=number, title=title, body_lines=body, tags=tuple(tags))


def atomic_write_text(path: str, text: str) -> None:
    """Atomically write ``text`` to ``path`` via a hardened ``.tmp`` + ``os.replace``.

    Contract (cite development_lessons.md #119 - diverging write contracts on the
    same highest-value asset are forbidden):
    - ``os.open(path, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0o600)`` on the ``.tmp``:
      ``O_EXCL`` refuses if ``.tmp`` already exists; ``O_NOFOLLOW`` refuses if
      ``.tmp`` is a symlink. Together they kill the TOCTOU (a planted ``.tmp``
      symlink cannot redirect the write).
    - ``os.replace(tmp, path)``: atomic inode swap on POSIX (rename(2)).
    - ``try/finally`` deletes ``.tmp`` on any error; the original file is untouched
      (never opened for write until the atomic replace).

    The caller is responsible for the git-clean precondition (whole-file rewriter;
    ``git checkout -- <file>`` is full recovery, so no ``.bak``).
    """
    tmp = f"{path}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        # Best-effort cleanup; never raise over the cleanup error.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


__all__ = [
    "EXTRA_TAG_VALUES",
    "VALID_FAMILIES",
    "Lesson",
    "TagValue",
    "atomic_write_text",
    "iter_lessons",
    "parse_tag_token",
]
