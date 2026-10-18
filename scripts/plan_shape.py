#!/usr/bin/env python3
"""Shared plan-shape resolver: the one grammar derivation for plan operands.

A plan operand is one of two shapes (plan-directory-shape plan, Terms):

- the single-file shape: one ``<name>.md`` file at the plans root (today's
  storage; behavior-identical, digest payload is the file's raw bytes);
- the directory shape: a plan directory named ``YYYY-MM-DD-<slug>/`` whose
  charter file ``PLAN.md`` carries the shared sections and whose ``tasks/``
  subdirectory carries exactly one Markdown file per task, each holding
  that task's ``### Task N:`` section.

``resolve_plan_operand(path)`` is the one derivation every consumer imports
(mirroring the shared-matcher precedent): it returns a resolved
:class:`PlanShape` (operand kind, charter text, sorted task-file list with
relative paths, digest payload bytes, slug) or raises
:class:`PlanShapeRefusal` naming BOTH the defect and the operand path (no
bare tracebacks, no silent skips). The directory ordinal grammar is part of
this grammar: a task file without a ``### Task N:`` heading refuses, two
task files claiming the same ordinal refuse naming both files, and the
ordinal sequence must be gap-free from 1 (naming the missing ordinals).
The single-file form's position-identity acceptance of repeated ordinals
lives with the document-position consumers and is deliberately NOT
duplicated here.

Manifest digest payload: the directory form's ``source_digest`` payload is
the canonical serialization built by :func:`manifest_digest_payload` --
sha256 over the sorted ``relpath<NUL>sha256(file-bytes)<LF>`` lines of the
charter plus every task file (order-independent, file-boundary-verbose).
Consumers hash it with the SAME digest recipe as the single-file form
(``vrs.compute_source_digest("plan", payload)``), so the source_digest
contract keeps its shape. The single-file payload stays the raw file bytes
so existing sidecars verify unchanged.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

# The charter and tasks grammar: exactly these names, no per-consumer
# re-derivation (the evaluation criteria forbid a second PLAN.md literal
# outside this helper, its tests, and the documented contract text).
CHARTER_FILENAME = "PLAN.md"
TASKS_DIRNAME = "tasks"

# One task file per task, each holding its ``### Task N:`` heading. The
# FIRST heading in a task file is its ordinal declaration (the file IS the
# task section); a file whose text carries no match at all is the missing-
# ordinal refusal below.
_TASK_ORDINAL_RE = re.compile(r"^### Task (\d+):", re.MULTILINE)


class PlanShapeRefusal(ValueError):
    """Named refusal for a malformed plan operand.

    Raised by :func:`resolve_plan_operand` for a nonexistent operand, an
    unreadable or non-UTF-8 file, a charterless directory, a missing or
    empty ``tasks/``, an unexpected entry under ``tasks/``, and the
    directory ordinal grammar arms (missing heading, duplicate ordinal
    across files, gap in the sequence). The message always names the
    defect AND the operand path; consumers convert it to their own named
    failure shape in place, never a bare traceback.
    """


@dataclass(frozen=True)
class PlanShape:
    """One resolved plan operand.

    Attributes:
        kind: ``"file"`` (single-file shape) or ``"directory"`` (charter
            plus ``tasks/`` shape).
        root: the resolved operand path (the file, or the plan directory).
        charter_text: the plan's shared-section text: the whole file text
            for the single-file shape, the charter's text for the
            directory shape.
        task_files: the sorted ``(relpath, path, text)`` triples of the
            task files, lexicographic by relative path; empty for the
            single-file shape.
        digest_payload: the bytes the consumer hashes with the shared
            digest recipe: the file's raw bytes for the single-file
            shape, the canonical manifest serialization
            (:func:`manifest_digest_payload`) for the directory shape.
        slug: the shape's identity token: the file's stem, or the plan
            directory's name (both carry the ``YYYY-MM-DD-<slug>`` prefix
            the consumers' date-strip expects; a directory path's stem is
            its name, so ``feature_slug``-style consumers work unchanged).
    """

    kind: str
    root: Path
    charter_text: str
    task_files: tuple[tuple[str, Path, str], ...]
    digest_payload: bytes
    slug: str

    def fence_units(self) -> tuple[tuple[str, str], ...]:
        """Per-file fence-scan units: ``(label, text)`` pairs.

        The charter first, then the sorted task files; each file must
        balance on its own, so a fence from one file can never pair
        across a file boundary in the assembled text. Labels are the
        operand-relative paths the file-named errors carry.
        """
        return tuple(
            [(CHARTER_FILENAME, self.charter_text)]
            + [(rel, text) for rel, _path, text in self.task_files]
        )

    def charter_plus_tasks_text(self) -> str:
        """The assembled plan text: charter with the task texts appended.

        The document-position consumers (the readiness probes) read this
        one text: the shared sections come from the charter, the
        ``### Task N:`` sections from the sorted task files, so section
        order and task identity are the directory form's assembly.
        """
        return "\n\n".join(
            [self.charter_text] + [text for _rel, _path, text in self.task_files]
        )


def manifest_digest_payload(
    entries: list[tuple[str, bytes]] | tuple[tuple[str, bytes], ...],
) -> bytes:
    """Canonical manifest serialization over ``(relpath, file-bytes)``.

    The sorted ``relpath<NUL>sha256(file-bytes)<LF>`` lines: sorted by the
    UTF-8 bytes of the relative path (order-independent under task-file
    renames that preserve the file set), one NUL between the path and the
    per-file digest, one LF per line (so every file boundary is visible in
    the hashed bytes). This is the ONLY place the serialization is built;
    consumers hash its output with the shared digest recipe.
    """
    lines: list[bytes] = []
    for relpath, data in sorted(entries, key=lambda item: item[0].encode("utf-8")):
        file_digest = hashlib.sha256(data).hexdigest().encode("ascii")
        lines.append(relpath.encode("utf-8") + b"\x00" + file_digest + b"\n")
    return b"".join(lines)


def resolve_plan_operand(path: Path | str) -> PlanShape:
    """Resolve one plan operand to its shape, or refuse by name.

    See the module docstring for the two shapes and the refusal arms.
    """
    resolved = Path(path).expanduser().resolve()
    if resolved.is_dir():
        return _resolve_directory(resolved)
    if not resolved.is_file():
        raise PlanShapeRefusal(f"plan operand does not exist: {resolved}")
    return _resolve_file(resolved)


def _resolve_file(resolved: Path) -> PlanShape:
    """Single-file shape: raw-bytes payload, file text, stem slug."""
    try:
        data = resolved.read_bytes()
    except OSError as exc:
        raise PlanShapeRefusal(
            f"cannot read plan operand: {resolved}: {exc}"
        ) from None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlanShapeRefusal(
            f"plan operand is not valid UTF-8: {resolved}: {exc}"
        ) from None
    return PlanShape(
        kind="file",
        root=resolved,
        charter_text=text,
        task_files=(),
        digest_payload=data,
        slug=resolved.stem,
    )


def _resolve_directory(resolved: Path) -> PlanShape:
    """Directory shape: charter plus sorted task files, manifest payload."""
    charter_path = resolved / CHARTER_FILENAME
    if not charter_path.is_file():
        raise PlanShapeRefusal(
            f"plan path is not a file: {resolved} (a plan directory "
            f"carries a {CHARTER_FILENAME} charter; none found)"
        )
    tasks_dir = resolved / TASKS_DIRNAME
    if not tasks_dir.is_dir():
        raise PlanShapeRefusal(
            f"plan directory carries no {TASKS_DIRNAME}/ directory "
            f"(a plan has tasks): {resolved}"
        )
    try:
        children = sorted(tasks_dir.iterdir(), key=lambda child: child.name)
    except OSError as exc:
        raise PlanShapeRefusal(
            f"cannot read plan tasks directory under {resolved}: {exc}"
        ) from None
    task_paths: list[tuple[str, Path]] = []
    for child in children:
        rel = f"{TASKS_DIRNAME}/{child.name}"
        if child.is_dir():
            raise PlanShapeRefusal(
                f"unexpected directory under {TASKS_DIRNAME}/: {rel} "
                f"(plan directory {resolved})"
            )
        if not child.is_file():
            raise PlanShapeRefusal(
                f"unreadable entry under {TASKS_DIRNAME}/: {rel} "
                f"(plan directory {resolved})"
            )
        if child.suffix != ".md":
            raise PlanShapeRefusal(
                f"non-Markdown file under {TASKS_DIRNAME}/: {rel} "
                f"(plan directory {resolved})"
            )
        task_paths.append((rel, child))
    if not task_paths:
        raise PlanShapeRefusal(
            f"plan directory carries an empty {TASKS_DIRNAME}/ directory "
            f"(a plan has tasks): {resolved}"
        )

    ordinals: dict[int, str] = {}
    task_files: list[tuple[str, Path, str]] = []
    manifest_entries: list[tuple[str, bytes]] = []
    for rel, path in task_paths:
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise PlanShapeRefusal(
                f"cannot read plan task file {rel} in {resolved}: {exc}"
            ) from None
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PlanShapeRefusal(
                f"plan task file is not valid UTF-8: {rel} in {resolved}: "
                f"{exc}"
            ) from None
        match = _TASK_ORDINAL_RE.search(text)
        if match is None:
            raise PlanShapeRefusal(
                f"plan task file carries no '### Task N:' heading: {rel} "
                f"(plan directory {resolved})"
            )
        ordinal = int(match.group(1))
        previous = ordinals.get(ordinal)
        if previous is not None:
            raise PlanShapeRefusal(
                f"directory plan ordinal collision: {previous} and {rel} "
                f"both claim Task {ordinal} (plan directory {resolved})"
            )
        ordinals[ordinal] = rel
        task_files.append((rel, path, text))
        manifest_entries.append((rel, data))

    highest = max(ordinals)
    missing = [str(n) for n in range(1, highest + 1) if n not in ordinals]
    if highest < 1:
        # The sequence must start at 1: ordinals that never reach 1 (for
        # example a directory whose only task file declares '### Task 0:')
        # leave the range above empty, so the missing first ordinal is
        # named explicitly.
        missing.append("1")
    if missing:
        present = ", ".join(str(n) for n in sorted(ordinals))
        raise PlanShapeRefusal(
            f"directory plan is missing task ordinal(s) "
            f"{', '.join(missing)} (present ordinals: {present}; "
            f"plan directory {resolved})"
        )

    try:
        charter_bytes = charter_path.read_bytes()
    except OSError as exc:
        raise PlanShapeRefusal(
            f"cannot read plan charter {CHARTER_FILENAME} in {resolved}: "
            f"{exc}"
        ) from None
    try:
        charter_text = charter_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlanShapeRefusal(
            f"plan charter is not valid UTF-8: {resolved}/"
            f"{CHARTER_FILENAME}: {exc}"
        ) from None

    payload = manifest_digest_payload(
        [(CHARTER_FILENAME, charter_bytes)] + manifest_entries
    )
    return PlanShape(
        kind="directory",
        root=resolved,
        charter_text=charter_text,
        task_files=tuple(task_files),
        digest_payload=payload,
        slug=resolved.name,
    )


# The Primary class anchors grammar (single home, primary-class-anchors-
# grammar-drift plan Task 1): the heading literal, the entry regex, the
# canonical shape string, the task-section extractor, and the block loop
# live only here; both consumers (the execution runtime and the readiness
# pre-round probe) import them and never define a second copy.
PRIMARY_CLASS_ANCHORS_HEADING = "Primary class anchors:"
# One anchor entry binds a class name to its source path:
#   - `ClassName` in `path/to/source.py`, optionally followed by prose.
PRIMARY_CLASS_ANCHOR_ENTRY = re.compile(
    r"^[-*]\s+`([^`]+)`\s+in\s+`([^`]+)`\s*(?:,.*)?$"
)
# The canonical entry form the refusal messages name (the self-remedying
# suffix); message text only, never a second grammar.
PRIMARY_CLASS_ANCHOR_SHAPE = "- `ClassName` in `path`"

_TASK_SECTION_ORDINAL_RE = re.compile(r"task-(\d+)")


def plan_task_section(plan_text: str, task_id: str) -> str | None:
    """Extract the plan section of the task whose id encodes its ordinal.

    Machine task ids are seeded in plan order (``task-N``); the section
    is the ``### Task N`` heading span. A task id without a resolvable
    ordinal returns None and the drift check reports nothing for it.
    Shared so the seeding boundary (``create_manifest``) and the
    readiness probe reuse the one section extractor.
    """
    match = _TASK_SECTION_ORDINAL_RE.fullmatch(str(task_id))
    if match is None:
        return None
    pattern = re.compile(
        rf"(?ms)^### Task {match.group(1)}:.*?(?=^### Task \d+:|^## |\Z)"
    )
    found = pattern.search(plan_text)
    return found.group(0) if found else None


def primary_class_anchors(section: str) -> list[tuple[str, str]]:
    """Parse the plan section's optional ``Primary class anchors:`` block.

    Each entry binds a class name to its source path. A present block whose
    entry fails the entry grammar raises the named ValueError so every
    consumer refuses before any state change; documentation-only tasks
    declare no block and get an empty list.
    """

    anchors: list[tuple[str, str]] = []
    in_block = False
    for line in section.splitlines():
        stripped = line.strip()
        if stripped == PRIMARY_CLASS_ANCHORS_HEADING:
            in_block = True
            continue
        if not in_block:
            continue
        if not stripped:
            # The block ends at its first blank line: the acceptance
            # checkbox bullets that follow the block are criteria, never
            # anchor entries.
            break
        if not stripped.startswith(("-", "*")):
            break
        match = PRIMARY_CLASS_ANCHOR_ENTRY.fullmatch(stripped)
        if match is None:
            raise ValueError(
                f"malformed Primary class anchors entry: {stripped}; "
                f"expected form: {PRIMARY_CLASS_ANCHOR_SHAPE}"
            )
        anchors.append((match.group(1), match.group(2)))
    return anchors
