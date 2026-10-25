#!/usr/bin/env python3
"""Skill description length gate: measure every scanned SKILL.md's
frontmatter description (folded block scalars joined single-spaced) against
the 1024-character cap; over-950 descriptions are warned. Outcome classes
are disjoint: exit 1 names every over-cap file and length and is reserved
for measured over-cap results only (the one class the landing sweep
classifies as a guard catch); exit 2 reports an operational exception (an
unreadable file, or an unexpected scan failure) as a stderr diagnostic and
is never a measured result; exit 0 otherwise. (argparse's own usage
error also exits 2 and is read as a tool error, never a measured
result.) The frontmatter parse
binds to the closing ``---`` fence, so fenced code blocks in the document
body are never swallowed. Inside a git checkout the default scan measures
only repository-tracked ``SKILL.md`` files (tracked files stay in scope
regardless of ignore rules; untracked files are excluded whether ignored
or not); outside a checkout, and for explicit paths, the scan is
recursive. Stdlib only; ``--selftest`` runs embedded fixtures."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CAP = 1024
WARN = 950
DEFAULT_TREE = "agents/skills"


def folded_description(text: str) -> str | None:
    """The frontmatter description value, folded. Returns None when the
    document has no frontmatter description. The parse binds to the
    closing ``---`` fence of the frontmatter block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(
            index
            for index in range(1, len(lines))
            if lines[index].strip() == "---"
        )
    except StopIteration:
        return None
    frontmatter = lines[1:end]
    # One pass: the first ``description`` key decides. A value whose first
    # non-space character is a ``>`` or ``|`` scalar marker (with any
    # inline content after it, or none) is a block scalar: collect its
    # more-indented continuation lines and join them single-spaced. Any
    # other value is a single-line value.
    parts: list[str] = []
    collecting = False
    for line in frontmatter:
        stripped = line.strip()
        if not collecting:
            if not stripped.startswith("description:"):
                continue
            value = stripped[len("description:"):].strip()
            if value[:1] in (">", "|"):
                collecting = True
                tail = value[1:].strip()
                if tail:
                    parts.append(tail)
            elif value:
                return value
            else:
                break  # bare description key with no value and no marker
            continue
        # collecting: more-indented lines continue the scalar; the next
        # non-indented frontmatter key ends it.
        if line.startswith((" ", "\t")):
            parts.append(stripped)
        elif stripped:
            break
    if collecting and parts:
        return " ".join(parts)
    return None


def measure(path: Path) -> tuple[str | None, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    description = folded_description(text)
    return description, (len(description) if description is not None else 0)


def tracked_skill_files(root: Path) -> list[Path] | None:
    """Repository-tracked ``SKILL.md`` files under ``root``, or ``None``
    when ``root`` is not inside a git checkout (or git is unavailable or
    fails, degrading to the caller's recursive fallback). Ignore rules
    never remove a tracked file from scope; untracked files never enter
    it."""
    try:
        probe = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=120,
        )
        if probe.returncode != 0:
            return None
        listing = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--deduplicate", "--", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if listing.returncode != 0:
        return None
    matches: list[Path] = []
    for raw in listing.stdout.split(b"\0"):
        if raw.rsplit(b"/", 1)[-1] != b"SKILL.md":
            continue
        path = root / raw.decode("utf-8", errors="replace")
        if path.is_file():
            matches.append(path)
    return sorted(matches)


def check_tree(
    roots: list[Path], tracked_only: bool = False
) -> tuple[list[str], list[str], list[str]]:
    """Return (failures, warnings, errors): failure rows name the file and
    length over the cap; warning rows name over-warn files; error rows are
    operational-exception diagnostics (a file whose measurement raised) that
    classify the whole run as exit 2, never exit 1. With ``tracked_only``
    (the default scan) a directory root inside a git checkout selects only
    repository-tracked ``SKILL.md`` files, and falls back to the recursive
    selection outside a checkout; explicit roots keep the recursive
    selection."""
    failures: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    for root in roots:
        if root.is_dir():
            skill_files = tracked_skill_files(root) if tracked_only else None
            if skill_files is None:  # no checkout, git failure, or untracked mode
                skill_files = sorted(root.rglob("SKILL.md"))
        else:
            skill_files = [root] if root.is_file() else []
        for path in skill_files:
            try:
                description, length = measure(path)
            except OSError as exc:
                errors.append(f"{path}: unreadable ({exc})")
                continue
            if description is None:
                continue  # no description key: skipped silently
            if length > CAP:
                failures.append(
                    f"{path}: folded description {length} > {CAP}"
                )
            elif length > WARN:
                warnings.append(
                    f"warning: {path}: folded description {length} "
                    f"over the {WARN}-character warning band"
                )
    return failures, warnings, errors


def _selftest() -> int:
    import tempfile

    failures: list[str] = []

    def expect(condition: bool, label: str) -> None:
        if not condition:
            failures.append(label)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def make(name: str, description: str) -> Path:
            directory = root / name
            directory.mkdir(parents=True)
            path = directory / "SKILL.md"
            path.write_text(
                f"---\nname: {name}\ndescription: {description}\n---\n\nbody\n",
                encoding="utf-8",
            )
            return path

        make("over", "x" * 1025)
        make("edge", "x" * 1024)
        make("near", "x" * 951)
        make("short", "fine")
        folded_dir = root / "folded"
        folded_dir.mkdir()
        folded = ">" + "".join("\n  " + "x" * 100 for _ in range(11))
        (folded_dir / "SKILL.md").write_text(
            f"---\nname: folded\ndescription: {folded}\n---\n",
            encoding="utf-8",
        )
        fenced_dir = root / "fenced"
        fenced_dir.mkdir()
        (fenced_dir / "SKILL.md").write_text(
            "---\nname: fenced\ndescription: short\n---\n\n```yaml\n  description: yyyy\n```\n",
            encoding="utf-8",
        )
        no_desc_dir = root / "nodesc"
        no_desc_dir.mkdir()
        (no_desc_dir / "SKILL.md").write_text(
            "---\nname: nodesc\n---\n", encoding="utf-8"
        )
        fails, warns, errs = check_tree([root])
        labels = {
            Path(row.split(":", 1)[0]).parent.name for row in fails
        }
        expect(labels == {"over", "folded"}, f"over-cap set: {labels}")
        expect(any("1110" in row for row in fails), "folded measured folded")
        expect(
            any("edge" in row or "near" in row for row in warns)
            and not any("edge" in row for row in fails),
            "at-cap not failed, warn band reported",
        )
        expect(not any("nodesc" in row for row in fails + warns), "no-desc skipped")
        expect(
            not any("fenced" in row for row in fails + warns),
            "body fence not swallowed",
        )
        expect(not errs, f"clean scan raises no operational errors: {errs}")
        fails_tracked, warns_tracked, errs_tracked = check_tree(
            [root], tracked_only=True
        )
        # Precondition: the temp root sits outside any git checkout (the
        # default TMPDIR); inside one, tracked-only selection returns []
        # and this equality assertion fails visibly.
        expect(
            (fails_tracked, warns_tracked, errs_tracked) == (fails, warns, errs),
            "tracked-only scan outside a checkout keeps recursive selection",
        )
    if failures:
        for row in failures:
            print(f"selftest FAIL: {row}", file=sys.stderr)
        return 1
    print("check_skill_description_length: selftest OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog=(
            "outcome classes: 0 pass; 1 measured over-cap descriptions only "
            "(the modeled failure class the landing sweep refuses and "
            "records as a guard catch); 2 operational exception (a stderr "
            "diagnostic; never a measured result, never a catch; "
            "argparse usage errors also exit 2 and read as tool errors)"
        ),
    )
    parser.add_argument("paths", nargs="*", default=None)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    roots = [Path(p) for p in args.paths] if args.paths else [Path(DEFAULT_TREE)]
    try:
        failures, warnings, errors = check_tree(roots, tracked_only=not args.paths)
    except Exception as exc:  # noqa: BLE001 - a scan crash must never
        # masquerade as exit 1 (the measured over-cap class); it is an
        # operational exception and answers exit 2 with a diagnostic.
        print(
            f"description-length: operational exception: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    for row in errors:
        print(f"description-length: operational exception: {row}", file=sys.stderr)
    for row in warnings:
        print(row, file=sys.stderr)
    for row in failures:
        print(f"description-length: {row}", file=sys.stderr)
    if errors:
        return 2  # an operational exception dominates: never report exit 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
