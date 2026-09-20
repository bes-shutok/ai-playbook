#!/usr/bin/env python3
"""Review record selection helper (review records contract plan, Task 3).

The helper makes the round decision mechanical before any review worker
launches. It enumerates the matching record pairs (Markdown plus
``.stats.json`` sidecar) for a slug, ignoring backup-shaped names
(``<basename>.backup-<timestamp>.md/.stats.json`` are counted
informationally only, never enumerated), and then:

- ``select``: with an empty directory it emits the ``-r1`` pair paths
  (decision ``new-record``); with an existing pair whose sidecar
  ``source_digest`` equals the caller-supplied digest of the bytes about
  to be reviewed it returns that pair (decision ``reuse``); with
  ``--explicit-new-round`` it allocates the next free ``-r<N>`` suffix
  (decision ``new-round``). Anything else is refused: a differing digest
  without an explicit decision is the overwrite guard (exit 1, naming the
  existing record and exactly the two supported actions,
  ``--explicit-new-round`` or ``backup``); an orphan half (a sidecar
  without its Markdown twin or vice versa) is refused for both reuse and
  allocation until repaired. The digest is the only comparison input; the
  helper invents no second state store.
- ``mark-superseded``: appends exactly one ``Superseded by: <successor>``
  Metadata line to the prior record with every other byte unchanged (the
  successor is recorded relative to the prior record's parent, bare name
  when co-located); the marker and Metadata scans are fence-aware (r2 F5)
  and refuse an unclosed fence with exit 2 naming the fence line (r3 F1);
  a symlinked prior is refused with exit 2 (r2 F7); a second
  invocation with a different successor exits 1;
  a matching-successor re-invocation is idempotent.
- ``backup``: writes timestamped byte-identical copies
  (``<basename>.backup-<timestamp>.md`` and ``.stats.json``) under the
  record's directory and prints both paths; the Markdown path feeds the
  new record's ``Backup of prior record:`` Metadata line.

Standard library only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

BACKUP_INFIX = ".backup-"

SUPERSEDED_LABEL = "Superseded by:"

BACKUP_METADATA_LABEL = "Backup of prior record:"

# A slug is embedded in emitted filenames; it may never carry separators or
# traversal segments (r1 F13). The gate uses fullmatch (r2 F10): a bare $ end
# anchor matches before a trailing newline, so a newline-terminated slug
# would slip through and emit a filename with an embedded newline.
SLUG_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*")

# Length bound on the slug (r3 overflow risk F3): the emitted pair embeds
# the slug between the date prefix and the -r<N> suffix, so an over-long
# slug can never be created as a file and would only fail late with a raw
# OSError. 100 characters keeps every emitted name far below common
# filename-length limits.
MAX_SLUG_LENGTH = 100

# The overwrite guard's only comparison input must already be in the
# sidecar grammar (r3 overflow risk F3): a lowercase 64-character hex
# SHA-256. Anything else is a usage error before any record is read.
SOURCE_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")

# Bound on the _unique_path collision suffix search (r1 F11); exhausting it
# is a usage error, never an unbounded loop.
_UNIQUE_PATH_LIMIT = 1000

# Module-level date source for the emitted round names. The test suite
# overrides this so fixture names and the helper's decision share one date
# and cannot straddle local midnight (r1 F20).
DATE_SOURCE = datetime.date.today

# Module-level timestamp source for backup names; the test suite overrides
# it to freeze backup timestamps without swapping the datetime module
# (r2 overflow D3), mirroring the DATE_SOURCE seam above.
BACKUP_TIMESTAMP_SOURCE = lambda: datetime.datetime.now().strftime(
    "%Y%m%dT%H%M%S"
)


class SelectionRefused(Exception):
    """The guard refuses an operation; the message is actionable."""


class SelectionUsageError(Exception):
    """An invalid invocation, or an unusable target/state that is the
    caller's to repair (exit 2).

    Beyond plainly invalid arguments (the slug grammar, the slug length
    bound, the backup-infix slug, the source-digest grammar), this class
    also covers the environmental raise sites about the invocation
    target: a symlinked prior record, a prior record with an unclosed
    code fence, a backup name that appeared while the pair was being
    placed, and an exhausted backup collision-suffix search.

    The exit taxonomy, stated once: usage errors (this class) exit 2;
    environmental refusals (``SelectionRefused``) exit 1, covering a
    missing or damaged record target, an orphaned half, and a differing
    digest without a decision.
    """


@dataclass
class RecordPair:
    round: int
    base: str
    markdown: Path
    sidecar: Path


@dataclass
class Selection:
    decision: str  # new-record | reuse | new-round
    markdown: Path
    sidecar: Path
    prior: Path | None
    backups_ignored: int
    # Ready-to-paste forward link (r2 F1): the prior record named relative
    # to the emitted successor's own directory (bare name when co-located),
    # so an orchestrator can paste it into the new record's
    # ``Supersedes:`` Metadata line and the validator's back-reference
    # grammar resolves it on a relative --dir invocation.
    supersedes: str | None = None


# The literal review-kind infixes the live corpus uses between the date
# stamp and the slug (r1 F1 of the scheduler ops contract plan). The bare
# "review-" kind is not in this tuple: its names are inherently ambiguous
# with another slug's bare family, so it joins the alternation only for
# slugs that already begin with it (see _pair_pattern).
REVIEW_KIND_INFIXES = (
    "plan-review-",
    "branch-review-",
    "code-review-",
    "exec-review-",
)

# The guarded review-kind infix, offered only to slugs that begin with it.
REVIEW_KIND_BARE_INFIX = "review-"


def _pair_pattern(slug: str) -> re.Pattern[str]:
    """A record pair base is ``<date>[-<review-kind-infix>]<slug>-r<N>``.

    The supported prefix is the emitted date stamp plus one optional
    review-kind infix drawn from the live corpus's literal kinds
    (``plan-review-``, ``branch-review-``, ``code-review-``,
    ``exec-review-``). Anchoring the prefix to these literal shapes keeps
    suffix-shadowing slugs (``plan`` vs ``review-plan``) from enumerating
    a foreign family's records, and enumerates every family shape the
    live corpus carries (``main`` reuses ``branch-review-main`` rounds;
    the code-review and exec-review kinds enumerate the same way).

    The bare ``review-`` kind is the one inherently ambiguous shape: a
    ``<date>-review-<slug>-r<N>`` name parses both as the review-kind
    record of the inner slug and as the bare record of the full-rest
    slug. The pinned shadowing semantics decide it: the bare reading
    owns the name (slug ``review-plan`` owns ``2026-09-19-review-plan-r1``
    and slug ``plan`` stays blind to it), so the ``review-`` infix joins
    the alternation only when the slug itself begins with ``review-``,
    reopening names like ``2026-09-15-review-review-coverage-pass-2-r1``
    to their natural owner ``review-coverage-pass-2`` (where the bare
    reading would need a doubled ``review-review-`` slug nobody passes).

    Accepted residual alias, documented and tested but not guarded: a
    slug that itself begins with an offered infix string (form
    ``<infix>Y``, e.g. ``plan-review-Y`` or ``branch-review-Y``)
    enumerates the same legacy-shaped ``<date>-<infix>Y-r<N>`` records
    as the bare ``Y`` slug, because the infix alternative and the slug
    spelling reach the same names; bare ``Y`` additionally owns the
    bare-shaped ``<date>-Y-r<N>`` records the infixed spelling never
    matches. Symmetrically, the bare ``Y`` slug enumerates that
    family's records (so ``plan`` reuses ``branch-review-plan``
    rounds). Every such overlap is shared ownership of the same files,
    never a silent loss.

    The pattern is assembled with plain string concatenation, not an
    f-string: the quantifier braces (``{4}``, ``{2}``) in the date regex
    would be parsed as f-string replacement fields.
    """
    infixes = list(REVIEW_KIND_INFIXES)
    if slug.startswith(REVIEW_KIND_BARE_INFIX):
        infixes.append(REVIEW_KIND_BARE_INFIX)
    return re.compile(
        r"^(?:\d{4}-\d{2}-\d{2}-(?:" + "|".join(infixes) + r")?)"
        + re.escape(slug)
        + r"-r(\d+)$"
    )


def _sidecar_twin(markdown: Path) -> Path:
    return markdown.with_suffix(".stats.json")


def _read_sidecar_digest(sidecar: Path) -> str:
    """Read ``source_digest`` from a sidecar, failing closed.

    A malformed sidecar or a digest-less sidecar can never authorize a
    replacement: the guard compares digests and nothing else, so a record
    without a comparable digest is refused until repaired.
    """
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SelectionRefused(
            f"cannot read the sidecar {sidecar.name} ({exc}); refusing to "
            "compare its digest; repair the sidecar first"
        ) from exc
    if not isinstance(payload, dict) or not isinstance(
        payload.get("source_digest"), str
    ):
        raise SelectionRefused(
            f"the sidecar {sidecar.name} carries no source_digest string; "
            "the overwrite guard compares digests only, so the record must "
            "be repaired (or migrated) before it can be reused or replaced"
        )
    return payload["source_digest"]


def _enumerate(
    reviews_dir: Path, slug: str
) -> tuple[list[RecordPair], list[Path], int]:
    """Enumerate matching record pairs, orphan halves, and backup pairs.

    Backup-shaped names (``.backup-<timestamp>`` infix) never inflate the
    enumeration; complete backup pairs are counted informationally only.
    """
    pattern = _pair_pattern(slug)
    pairs: list[RecordPair] = []
    orphans: list[Path] = []
    backups_ignored = 0
    markdown_files = sorted(reviews_dir.glob("*.md")) if reviews_dir.is_dir() else []
    seen_bases: set[str] = set()
    for markdown in markdown_files:
        base = markdown.name[: -len(".md")]
        if BACKUP_INFIX in base:
            if _sidecar_twin(markdown).is_file():
                backups_ignored += 1
            continue
        match = pattern.match(base)
        if match is None:
            continue
        seen_bases.add(base)
        sidecar = _sidecar_twin(markdown)
        if sidecar.is_file():
            pairs.append(RecordPair(int(match.group(1)), base, markdown, sidecar))
        else:
            orphans.append(markdown)
    for sidecar in sorted(reviews_dir.glob("*.stats.json")):
        base = sidecar.name[: -len(".stats.json")]
        if BACKUP_INFIX in base:
            continue
        if pattern.match(base) is None:
            continue
        if base not in seen_bases:
            orphans.append(sidecar)
    pairs.sort(key=lambda pair: pair.round)
    return pairs, orphans, backups_ignored


def select_record(
    reviews_dir: Path, slug: str, source_digest: str, explicit_new_round: bool = False
) -> Selection:
    """Decide reuse vs the next round, or refuse (the overwrite guard)."""
    reviews_dir = Path(reviews_dir)
    if not SLUG_PATTERN.fullmatch(slug):
        raise SelectionUsageError(
            f"invalid --slug {slug!r}: a slug must match "
            "^[a-z0-9][a-z0-9._-]*$ (no path separators, no trailing "
            "newline) because it is embedded in the emitted "
            "record filenames"
        )
    if len(slug) > MAX_SLUG_LENGTH:
        raise SelectionUsageError(
            f"invalid --slug {slug!r}: a slug is bounded at "
            f"{MAX_SLUG_LENGTH} characters because the emitted record "
            "filenames embed it and an over-long name could never be "
            "created (the failure would surface as a raw OSError instead "
            "of this usage error)"
        )
    if BACKUP_INFIX in slug:
        raise SelectionUsageError(
            f"invalid --slug {slug!r}: a slug must not contain the backup "
            f"infix {BACKUP_INFIX!r}; the emitted pair would be classified "
            "as a backup and counted informationally only, silently "
            "blinding the overwrite guard on a later select"
        )
    pairs, orphans, backups_ignored = _enumerate(reviews_dir, slug)
    if orphans:
        named = ", ".join(sorted(path.name for path in orphans))
        raise SelectionRefused(
            "orphaned record half in "
            f"{reviews_dir}: {named} has no matching Markdown/sidecar twin; "
            "refusing both reuse and allocation until the orphan half is "
            "repaired (restore the missing twin or remove the orphan)"
        )
    if not source_digest.strip():
        # A caller-supplied invocation error, not a record-corpus state:
        # an empty digest would silently disable the overwrite guard, so
        # it is refused in the usage-error taxonomy (exit 2) before any
        # comparison.
        raise SelectionUsageError(
            "--source-digest is empty; an empty digest would silently "
            "disable the overwrite guard"
        )
    if SOURCE_DIGEST_PATTERN.fullmatch(source_digest) is None:
        raise SelectionUsageError(
            f"invalid --source-digest {source_digest!r}: a source digest "
            "must match ^[0-9a-f]{64}$ (a lowercase 64-character hex "
            "SHA-256, the sidecar source_digest grammar); refusing the "
            "comparison input before any record is read"
        )

    def emit(round_number: int) -> tuple[Path, Path]:
        base = f"{DATE_SOURCE().isoformat()}-{slug}-r{round_number}"
        return reviews_dir / f"{base}.md", reviews_dir / f"{base}.stats.json"

    if not pairs:
        markdown, sidecar = emit(1)
        return Selection("new-record", markdown, sidecar, None, backups_ignored)

    latest = pairs[-1]
    if explicit_new_round:
        markdown, sidecar = emit(latest.round + 1)
        supersedes = os.path.relpath(latest.markdown, markdown.parent)
        return Selection(
            "new-round",
            markdown,
            sidecar,
            latest.markdown,
            backups_ignored,
            supersedes=supersedes,
        )

    latest_digest = _read_sidecar_digest(latest.sidecar)
    if latest_digest == source_digest:
        return Selection(
            "reuse", latest.markdown, latest.sidecar, latest.markdown, backups_ignored
        )
    raise SelectionRefused(
        f"refusing to replace the existing record {latest.markdown.name}: its "
        f"sidecar source_digest {latest_digest!r} differs from the supplied "
        f"--source-digest {source_digest!r}; exactly two actions are "
        "supported: rerun with --explicit-new-round to allocate the next "
        "round, or run the backup subcommand for the explicit archival "
        "operation"
    )


def _names_same_path(base: Path, recorded: str, successor: Path) -> bool:
    """True when a recorded back-reference and the successor argument name
    the same file after resolution. A relative recorded value resolves
    against ``base`` (the prior record's parent), mirroring the validator's
    resolution rule, so bare-name, relative, and absolute spellings of one
    successor are all recognized."""
    candidate = Path(recorded)
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve() == successor.resolve()


def _recorded_supersession_value(prior: Path, successor: Path) -> str:
    """The successor named relative to the prior record's parent (bare name
    when co-located), mirroring the validator's back-reference resolution
    grammar, so a relative ``--dir`` invocation round-trips through the
    supersession gate (r1 F2)."""
    return os.path.relpath(successor.resolve(), prior.parent.resolve())


_FENCE_LINE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def _fence_mask(lines: list[str]) -> tuple[list[bool], int | None]:
    """True per line that is fenced content (r2 F5).

    The close rule mirrors the validator's shared fence classifier: a
    fence closes ONLY on a bare, equal-or-longer run of the same delimiter
    character as the opener, so a fenced template copy can never
    contribute a marker line or a Metadata heading. The opener spelling is
    this helper's own byte-scan regex and is NOT claimed to mirror the
    classifier; single-sourcing the remaining grammar belongs to the
    deferred parameterization refactor (see docs/history/backlog/
    2026-09-19-validator-fence-classifier-parameterization.md).

    Returns ``(mask, unclosed_opener_index)`` where the second element is
    the index of a fence opener that never closed, or None when every
    fence closed. An unclosed fence would mask the whole file tail, so the
    caller refuses the operation instead of scanning a truncated record
    (r3 F1).
    """
    mask = [False] * len(lines)
    in_fence = False
    fence_len = 0
    fence_char = ""
    opener_index: int | None = None
    for index, line in enumerate(lines):
        fence_match = _FENCE_LINE_RE.match(line)
        if fence_match:
            if in_fence:
                stripped = line.strip()
                if (
                    stripped == fence_char * len(stripped)
                    and len(stripped) >= fence_len
                ):
                    in_fence = False
                    fence_len = 0
                    fence_char = ""
                    opener_index = None
                    mask[index] = False
                else:
                    mask[index] = True
            else:
                in_fence = True
                fence_len = len(fence_match.group(1))
                fence_char = fence_match.group(1)[0]
                opener_index = index
                mask[index] = False
            continue
        mask[index] = in_fence
    return mask, (opener_index if in_fence else None)


def mark_superseded(prior_path: Path, successor_path: Path) -> tuple[str, str]:
    """Append exactly one ``Superseded by:`` Metadata line to the prior record.

    Every other byte stays unchanged, and the write is atomic (temp file
    plus ``os.replace``), so a crash can never leave a torn prior record.
    The recorded value names the successor relative to the prior record's
    parent (bare name when co-located), mirroring the validator's
    back-reference resolution grammar, so a relative ``--dir`` invocation
    round-trips through the supersession gate (r1 F2). The marker parse is
    case-insensitive anchored (r1 F6) and fence-aware (r2 F5), and existing
    markers are compared by resolved path: an equivalent spelling of the
    same successor is idempotent, a different successor is a refusal
    (exit 1). A symlinked prior is refused (exit 2): replacing the link
    with a regular file would leave the real target unmarked (r2 F7). An
    unclosed fence is refused (exit 2, naming the fence line) because the
    mask would hide every line after the opener, so a marker appended
    "after" the record would be invisible and retries would accumulate
    duplicates (r3 F1).
    Returns ``(status, recorded_value)`` where the recorded value is what
    the record carries after the operation.
    """
    prior = Path(prior_path)
    successor = Path(successor_path)
    if prior.is_symlink():
        raise SelectionUsageError(
            f"the prior record {prior.name} is a symlink; refusing to "
            "replace the link with a regular file (the real target would "
            "stay unmarked); run mark-superseded on the real path instead"
        )
    recorded_value = _recorded_supersession_value(prior, successor)
    content = prior.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in content else "\n"
    lines = content.split(newline)
    mask, unclosed_opener = _fence_mask(lines)
    if unclosed_opener is not None:
        raise SelectionUsageError(
            f"the prior record {prior.name} opens a code fence on line "
            f"{unclosed_opener + 1} ({lines[unclosed_opener].strip()!r}) "
            "that never closes; every line after the opener would be "
            "invisible to the marker and Metadata scans, so the record "
            "must be repaired (close the fence) before supersession is "
            "marked"
        )
    marker_re = re.compile(r"^-[ \t]*Superseded by[ \t]*:[ \t]*(.*)$", re.IGNORECASE)
    existing = [
        (index, marker_re.match(line).group(1).strip())  # type: ignore[union-attr]
        for index, line in enumerate(lines)
        if not mask[index] and marker_re.match(line) is not None
    ]
    if len(existing) > 1:
        raise SelectionRefused(
            f"the prior record {prior.name} carries {len(existing)} "
            f"'{SUPERSEDED_LABEL}' lines; keep exactly one; repair the "
            "record before marking supersession"
        )
    if existing:
        recorded = existing[0][1]
        if not _names_same_path(prior.parent, recorded, successor):
            raise SelectionRefused(
                f"the prior record {prior.name} is already marked "
                f"'{SUPERSEDED_LABEL} {recorded}'; refusing to re-mark it "
                f"for a different successor {successor.name!r}"
            )
        return "already-marked", recorded
    meta_index = next(
        (
            index
            for index, line in enumerate(lines)
            if not mask[index] and line.strip() == "## Metadata"
        ),
        None,
    )
    if meta_index is None:
        raise SelectionRefused(
            f"the prior record {prior.name} has no '## Metadata' section; "
            f"the '{SUPERSEDED_LABEL}' line must live there; repair the "
            "record first"
        )
    insert_at = len(lines)
    for index in range(meta_index + 1, len(lines)):
        if not mask[index] and lines[index].startswith("## "):
            insert_at = index
            break
    while insert_at > meta_index + 1 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, f"- {SUPERSEDED_LABEL} {recorded_value}")
    _atomic_write_text(prior, newline.join(lines))
    return "marked", recorded_value


def _atomic_write_text(path: Path, text: str) -> None:
    """Replace ``path`` with ``text`` atomically (temp file, os.replace).

    The temp file is chmodded to the destination's existing mode before the
    replace, falling back to 0644 masked by the process umask when the
    destination does not exist yet, so a marked record keeps the mode its
    author gave it instead of inheriting NamedTemporaryFile's 0600 (r2 F7).
    """
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with tmp:
            tmp.write(text)
        try:
            mode = path.stat().st_mode & 0o777
        except OSError:
            umask = os.umask(0o077)
            os.umask(umask)
            mode = 0o644 & ~umask
        os.chmod(tmp.name, mode)
        os.replace(tmp.name, path)
    except BaseException:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise


def create_backup(record_path: Path) -> tuple[Path, Path]:
    """Copy a record pair to timestamped byte-identical backup paths."""
    markdown = Path(record_path)
    if not markdown.is_file():
        raise SelectionRefused(
            f"cannot back up {markdown.name}: the record does not exist"
        )
    sidecar = _sidecar_twin(markdown)
    if not sidecar.is_file():
        raise SelectionRefused(
            f"cannot back up {markdown.name}: the sidecar twin "
            f"{sidecar.name} is missing; a record is backed up and replaced "
            "as a pair only"
        )
    timestamp = BACKUP_TIMESTAMP_SOURCE()
    stem = markdown.name[: -len(".md")]
    markdown_backup = _unique_path(markdown.parent, stem, ".md", timestamp)
    sidecar_backup = _unique_path(markdown.parent, stem, ".stats.json", timestamp)
    _write_backup_exclusive(markdown_backup, markdown.read_bytes())
    _write_backup_exclusive(sidecar_backup, sidecar.read_bytes())
    return markdown_backup, sidecar_backup


def _write_backup_exclusive(destination: Path, data: bytes) -> None:
    """Create ``destination`` exclusively and write ``data`` byte-identically.

    ``O_EXCL`` refuses to overwrite anything that appeared after the
    uniqueness check, and ``O_NOFOLLOW`` (where the platform offers it)
    refuses to follow a planted symlink at the destination name, so a
    collision can never redirect record bytes outside the tree (r1 F12).
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(destination, flags, 0o644)
    except FileExistsError as exc:
        raise SelectionUsageError(
            f"the backup name {destination.name} appeared while the pair "
            "was being placed; refusing to overwrite it"
        ) from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
    except BaseException:
        try:
            os.unlink(destination)
        except OSError:
            pass
        raise


def _unique_path(directory: Path, stem: str, extension: str, timestamp: str) -> Path:
    """First non-existing backup candidate, with a bounded collision search.

    ``os.path.lexists`` (not a following ``Path.exists``) decides occupancy,
    so a planted dangling symlink at a candidate name counts as taken
    instead of being followed (r1 F12). The collision counter is bounded
    (r1 F11): exhausting it raises a usage error (exit 2) rather than
    looping.
    """
    candidate = directory / f"{stem}{BACKUP_INFIX}{timestamp}{extension}"
    counter = 1
    while os.path.lexists(candidate):
        if counter >= _UNIQUE_PATH_LIMIT:
            raise SelectionUsageError(
                f"no free backup name for {stem}{BACKUP_INFIX}{timestamp}"
                f"{extension} after {_UNIQUE_PATH_LIMIT} collision "
                "suffixes; refusing to loop unbounded"
            )
        candidate = directory / f"{stem}{BACKUP_INFIX}{timestamp}-{counter}{extension}"
        counter += 1
    return candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="review_record_selection",
        description=(
            "Select review record paths (reuse or next -r<N> round) with an "
            "overwrite guard, mark supersession links, and write immutable "
            "backups"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    select_parser = subparsers.add_parser(
        "select", help="emit the record pair paths to use before workers launch"
    )
    select_parser.add_argument("--dir", required=True, help="reviews directory")
    select_parser.add_argument(
        "--slug", required=True, help="artifact slug embedded in the record names"
    )
    select_parser.add_argument(
        "--source-digest",
        required=True,
        help="digest of the bytes about to be reviewed (compared against the "
        "sidecar source_digest; the only comparison input)",
    )
    select_parser.add_argument(
        "--explicit-new-round",
        action="store_true",
        help="allocate the next free -r<N> round instead of refusing on a "
        "differing digest",
    )

    mark_parser = subparsers.add_parser(
        "mark-superseded",
        help="append exactly one 'Superseded by:' Metadata line to the prior record",
    )
    mark_parser.add_argument("--prior", required=True, help="prior record Markdown")
    mark_parser.add_argument(
        "--successor", required=True, help="successor record path the prior yields to"
    )

    backup_parser = subparsers.add_parser(
        "backup",
        help="write timestamped byte-identical copies of a record pair",
    )
    backup_parser.add_argument(
        "--record", required=True, help="the prior record Markdown path"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "select":
            selection = select_record(
                Path(args.dir),
                args.slug,
                args.source_digest,
                explicit_new_round=args.explicit_new_round,
            )
            print(
                json.dumps(
                    {
                        "decision": selection.decision,
                        "markdown": str(selection.markdown),
                        "sidecar": str(selection.sidecar),
                        "prior": (
                            str(selection.prior) if selection.prior else None
                        ),
                        "supersedes": selection.supersedes,
                        "backups_ignored": selection.backups_ignored,
                    }
                )
            )
            return 0
        if args.command == "mark-superseded":
            status, recorded = mark_superseded(
                Path(args.prior), Path(args.successor)
            )
            print(
                json.dumps(
                    {
                        "status": status,
                        "prior": str(args.prior),
                        # Echo the value the record now carries (r2
                        # overflow T6), not the verbatim --successor
                        # argument spelling.
                        "superseded_by": recorded,
                    }
                )
            )
            return 0
        if args.command == "backup":
            markdown_backup, sidecar_backup = create_backup(Path(args.record))
            print(
                json.dumps(
                    {
                        "markdown": str(markdown_backup),
                        "sidecar": str(sidecar_backup),
                    }
                )
            )
            print(
                f"Metadata line for the new record: "
                f"{BACKUP_METADATA_LABEL} {markdown_backup}",
                file=sys.stderr,
            )
            return 0
        parser.error(f"unknown command {args.command!r}")  # pragma: no cover
    except SelectionRefused as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except SelectionUsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
