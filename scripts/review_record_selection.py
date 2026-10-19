#!/usr/bin/env python3
"""Review record selection helper (review records contract plan, Task 3).

The helper makes the round decision mechanical before any review worker
launches. It enumerates the matching record pairs (Markdown plus
``.stats.json`` sidecar) for a slug, ignoring backup-shaped names
(``<basename>.backup-<timestamp>.md/.stats.json`` are counted
informationally only, never enumerated), and then:

- ``select``: plan reviews are allocated by repository-relative source-plan
  identity and receive a path-token-qualified filename; a bare slug with an
  explicit other kind enumerates only that family's suffix-shaped records and
  emits the suffix-form name. With an empty directory it emits the ``-r1`` pair paths
  (decision ``new-record``); with an existing pair whose sidecar
  ``source_digest`` equals the caller-supplied digest of the bytes about
  to be reviewed it returns that pair (decision ``reuse``); with
  ``--explicit-new-round`` it allocates the next free ``-r<N>`` suffix
  (decision ``new-round``), preserving the matched predecessor filename stem
  when the caller slug is an alias. Anything else is refused: a differing digest
  without an explicit decision is the overwrite guard (exit 1, naming the
  existing record and exactly the two supported actions,
  ``--explicit-new-round`` or ``backup``); an orphan half (a sidecar
  without its Markdown twin or vice versa) is refused for both reuse and
  allocation until repaired. The digest remains the freshness comparison;
  the source-plan path identifies the plan review series.
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
- ``recover-orphan``: the auditable recovery for an orphan half (a
  canonical Markdown whose sidecar twin is missing, left by an
  interrupted synthesis; review round record lifecycle gaps plan,
  Task 3). The orphan-state refusals fire before any mutation (a record
  whose sidecar exists is not an orphan, an absent record refuses, and
  a name already carrying the ``.orphan-`` infix is already preserved),
  then the orphan is renamed (never copied) byte-identical to
  ``<original stem>.orphan-<UTCtimestamp>.md`` (a name no canonical
  discovery or validation glob matches), and the fresh canonical pair
  for the explicitly passed slug and optional kind is allocated through
  the same allocation logic ``select`` uses (the slug and kind are
  never inverse-parsed from the preserved stem, whose alias analysis is
  documented ambiguous). The receipt names the preserved path, the
  allocated pair, and the exact ``Orphan recovery: <repo-relative
  path>`` Metadata line to add to the fresh record; the preserved path
  is spelled repo-relative so the printed line passes the staging
  validator's orphan-recovery link gate verbatim. The selector refuses
  outside a git repository: the evidence link is repo-relative by
  contract, so a receipt cannot be printed there.
- ``verify-digest``: the mechanical digest freshness check at a
  record-reading boundary (a continuation resumption, a boundary after a
  closeout or address commit, or terminal evaluation). Every input is an
  explicit caller input, never derived: the record path, its reviews
  directory, the recorded base commit, and the latest recorded verified
  head. The recomputation uses the canonical derivation (the
  ``git diff <base>...<head>`` bytes hashed with SHA-256, imported from
  ``corrections_record.py`` so no second freshness notion exists),
  compares against the sidecar's ``source_digest`` through the same read
  helper the overwrite guard uses, and refuses stale with both digests
  named. A HEAD move past the recorded verified head refuses even when
  the reviewed-scope bytes are unchanged, unless the sidecar records a
  corrections chain whose terminal binds the current bytes and HEAD (the
  chain the staging validator grades), which yields the named
  accepted-stale pass instead. The subcommand mutates nothing.

Standard library only.
"""

from __future__ import annotations

import argparse
from collections import Counter
import datetime
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from review_plan_identity import (
    identity_token as _identity_token,
    normalize_plan_path as _normalize_plan_path,
    record_identity as _shared_record_identity,
    repository_root as _repository_root,
)

BACKUP_INFIX = ".backup-"

# The preserved-orphan infix (review round record lifecycle gaps plan,
# Task 3): a name carrying it is a preserved orphan, never a canonical
# record. Selection and validation refuse it structurally: the canonical
# pair grammar requires the ``-r<N>`` suffix at the end of the base, so
# ``<stem>.orphan-<timestamp>.md`` never matches the selector's
# enumeration shapes. Discovery excludes it explicitly instead: the
# staging-path predicate (``is_staging_review_path`` in
# validate_review_staging.py, which mirrors this constant) refuses any
# name carrying the infix, because the staging grammar's optional
# ``-r<N>`` tail would otherwise match a preserved name on the
# plan-review, branch-review, rfc-review, confluence-review, PR-N, and
# bare-family shapes.
ORPHAN_INFIX = ".orphan-"

ORPHAN_RECOVERY_METADATA_LABEL = "Orphan recovery:"

SUPERSEDED_LABEL = "Superseded by:"

BACKUP_METADATA_LABEL = "Backup of prior record:"

# A slug is embedded in emitted filenames; it may never carry separators or
# traversal segments (r1 F13). The gate uses fullmatch (r2 F10): a bare $ end
# anchor matches before a trailing newline, so a newline-terminated slug
# would slip through and emit a filename with an embedded newline.
SLUG_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

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

# Module-level timestamp source for preserved-orphan names; the plan pins
# the UTC spelling, so this seam reads the timezone-aware UTC clock. The
# test suite overrides it to freeze the preservation timestamp, mirroring
# the BACKUP_TIMESTAMP_SOURCE seam above.
ORPHAN_TIMESTAMP_SOURCE = lambda: datetime.datetime.now(
    datetime.timezone.utc
).strftime("%Y%m%dT%H%M%S")


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
    missing or damaged record target, an orphaned half, a differing
    digest without a decision, and the mark-superseded-side refusals
    on the supersession marking path (a prior record already marked
    with a different recorded successor, a prior record carrying
    duplicate supersession markers, or a prior record with no Metadata
    section to host the marker line).
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


def _pair_pattern(slug: str, *, plan_identity: bool = False) -> re.Pattern[str]:
    """A record pair base is ``<date>[-<review-kind-infix>]<slug>[-r<N>]``;
    an unnumbered legacy singleton is round 1.

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
    slug that itself begins with one of the four literal review-kind infixes
    (form ``<infix>Y``, e.g. ``plan-review-Y`` or
    ``branch-review-Y``) enumerates the same legacy-shaped
    ``<date>-<infix>Y-r<N>`` records as the bare ``Y`` slug, because
    the infix alternative and the slug spelling reach the same names;
    the guarded bare ``review-`` kind is the carve-out: it is offered
    only to slugs that already begin with it, and a ``review-``-prefixed
    full slug's inner spelling never enumerates its bare-shaped records
    (pinned by ``test_pair_pattern_review_shape_stays_bare_owned``);
    bare ``Y`` additionally owns the bare-shaped ``<date>-Y-r<N>``
    records the infixed spelling never matches. Symmetrically, the bare ``Y`` slug enumerates that
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
        + (r"(?:-p[0-9a-f]{8})?" if plan_identity else "")
        + r"(?:-r(\d+))?$"
    )


def _family_scope(slug: str, review_kind: str | None) -> str | None:
    """The family suffix scope for a bare slug with an explicit kind.

    A bare slug with an explicit non-plan-review kind selects that
    family's suffix-shaped records only (the documented caller shape); a
    slug already carrying the kind infix keeps the legacy spelling, and
    plan-review keeps its identity-filtered legacy behavior.
    """
    if (
        review_kind not in (None, "plan-review")
        and not slug.startswith(review_kind + "-")
    ):
        return review_kind
    return None


def _suffix_family_pattern(slug: str, kind: str) -> re.Pattern[str]:
    """A record pair base for a bare artifact slug scoped to one review
    family: ``<date>[-<kind>-]<slug>-<kind>[-r<N>]``.

    When a caller passes a bare slug with an explicit ``--kind`` (the
    documented execute-plan branch-review invocation), the candidate set
    is the requested family's suffix-shaped records only: the optional
    same-kind prefix is the legacy spelling of the same family, and no
    other kind's infix may appear on either side of the slug. This keeps
    mixed families sharing an artifact slug from advancing or superseding
    one another's rounds (the 2026-10-10 family-scope row's acceptance).
    """
    prefix = kind + "-"
    suffix = "-" + kind
    return re.compile(
        r"^\d{4}-\d{2}-\d{2}-(?:" + re.escape(prefix) + r")?"
        + re.escape(slug)
        + re.escape(suffix)
        + r"(?:-r(\d+))?$"
    )


def _plan_identity(source_plan: Path, reviews_dir: Path) -> str:
    """Return a repository-relative plan path for stable series identity."""
    if not source_plan.expanduser().exists():
        raise SelectionUsageError(f"--source-plan does not exist: {source_plan}")
    root = _repository_root(reviews_dir)
    if root is None:
        if not reviews_dir.expanduser().exists():
            raise SelectionUsageError(
                f"reviews directory {reviews_dir} does not exist; create "
                "or transfer it in before selection (the worktree "
                "standard's transfer-in step provisions the reviews home)"
            )
        raise SelectionUsageError("--source-plan requires a path inside a git repository")
    identity = _normalize_plan_path(source_plan, root)
    if identity is None:
        raise SelectionUsageError(
            f"--source-plan must resolve inside repository {root}"
        )
    return identity


def _record_plan_identity(markdown: Path, sidecar: Path) -> str | None:
    """Read identity from the additive sidecar field or legacy artifact line."""
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    return _shared_record_identity(markdown, payload)


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
    reviews_dir: Path, slug: str, *, review_kind: str | None = None,
    source_plan_identity: str | None = None,
    family_kind: str | None = None,
    advisories: list[str] | None = None
) -> tuple[list[RecordPair], list[Path], int]:
    """Enumerate matching record pairs, orphan halves, and backup pairs.

    Backup-shaped names (``.backup-<timestamp>`` infix) never inflate the
    enumeration; complete backup pairs are counted informationally only.

    With ``source_plan_identity`` set, a complete pair whose record resolves
    no plan identity no longer refuses the whole enumeration: at or below
    the resolved identity-bearing latest round it is excluded from the pair
    set and named in the ``advisories`` out-parameter (the caller owns the
    list and any printing), while an unresolvable pair OUTRANKING the
    resolved round still refuses with the outranking record named, before
    any allocation or reuse decision. A series with zero identity-bearing
    pairs of any plan resolves the latest round lexically (highest ``r<N>``,
    ties by filename, duplicate rounds included) with the advisory naming
    the lexical resolution, so allocation continues from the highest
    existing round instead of minting a parallel chain; a series whose only
    identity-bearing pairs belong to other plans never lexical-resolves.
    Mismatched identity-bearing pairs keep the silent skip without an
    advisory, identity-bearing duplicates keep the duplicate-round refusal,
    and the orphan boundary is unchanged: an identity-unresolvable half
    keeps the orphan-completeness refusal and a half carrying a foreign
    plan identity keeps the silent skip.
    """
    if family_kind is not None:
        pattern = _suffix_family_pattern(slug, family_kind)
    else:
        pattern = _pair_pattern(slug, plan_identity=review_kind == "plan-review")
    pairs: list[RecordPair] = []
    unresolvable: list[RecordPair] = []
    identity_bearing = False
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
            if source_plan_identity is not None:
                identity = _record_plan_identity(markdown, sidecar)
                if identity is None:
                    unresolvable.append(
                        RecordPair(int(match.group(1) or "1"), base, markdown, sidecar)
                    )
                    continue
                identity_bearing = True
                if identity != source_plan_identity:
                    continue
            pairs.append(RecordPair(int(match.group(1) or "1"), base, markdown, sidecar))
        else:
            if source_plan_identity is not None:
                legacy_identity = _shared_record_identity(markdown, {})
                if legacy_identity is not None and legacy_identity != source_plan_identity:
                    continue
            orphans.append(markdown)
    for sidecar in sorted(reviews_dir.glob("*.stats.json")):
        base = sidecar.name[: -len(".stats.json")]
        if BACKUP_INFIX in base:
            continue
        if pattern.match(base) is None:
            continue
        if base not in seen_bases:
            if source_plan_identity is not None:
                candidate_identity = _record_plan_identity(
                    reviews_dir / f"{base}.md", sidecar
                )
                if (
                    candidate_identity is not None
                    and candidate_identity != source_plan_identity
                ):
                    continue
            orphans.append(sidecar)
    if source_plan_identity is not None and unresolvable:
        unresolvable.sort(key=lambda pair: (pair.round, pair.base))
        if pairs:
            resolved_round = max(pair.round for pair in pairs)
            for pair in unresolvable:
                if pair.round > resolved_round:
                    raise SelectionRefused(
                        f"cannot identify legacy plan-review record "
                        f"{pair.markdown.name}: this identity-unresolvable "
                        f"round r{pair.round} outranks the resolved "
                        f"identity-bearing latest round r{resolved_round}; "
                        "repair the record's identity before selecting"
                    )
                if advisories is not None:
                    advisories.append(
                        "excluded identity-unresolvable review record "
                        f"{pair.markdown.name} (round r{pair.round} at or "
                        f"below the resolved round r{resolved_round})"
                    )
        elif identity_bearing:
            # Foreign-bearing series: the consulting plan owns nothing, so
            # the strays never lexical-resolve the series; the empty pair
            # set below stands.
            if advisories is not None:
                for pair in unresolvable:
                    advisories.append(
                        "excluded identity-unresolvable review record "
                        f"{pair.markdown.name} (no identity-bearing record "
                        "of this plan in the series)"
                    )
        else:
            # Pure-legacy series: the pre-convention lexical selection
            # (highest rN, ties by filename, duplicate rounds included).
            resolved = max(unresolvable, key=lambda pair: (pair.round, pair.base))
            if advisories is not None:
                advisories.append(
                    "no identity-bearing record in the series; resolved the "
                    f"latest round lexically: {resolved.markdown.name}"
                )
            pairs = [resolved]
    pairs.sort(key=lambda pair: (pair.round, pair.base))
    rounds = [pair.round for pair in pairs]
    if len(rounds) != len(set(rounds)):
        duplicates = sorted(round_number for round_number, count in Counter(rounds).items() if count > 1)
        raise SelectionRefused(
            "matching records contain ambiguous duplicate round number(s) "
            + ", ".join(f"r{number}" for number in duplicates)
            + "; repair the duplicate pair before selecting"
        )
    return pairs, orphans, backups_ignored


def _validate_slug_and_kind(slug: str, review_kind: str | None) -> None:
    """The shared slug and kind usage gates (invalid invocation, exit 2).

    Decided before any record-corpus state is consulted, so the same
    invalid input exits 2 with the same message on every subcommand
    (the pinned usage-error-precedes-orphan-refusal precedence).
    """
    if not SLUG_PATTERN.fullmatch(slug):
        raise SelectionUsageError(
            f"invalid --slug {slug!r}: a slug must match "
            "^[A-Za-z0-9][A-Za-z0-9._-]*$ (no path separators, no trailing "
            "newline) because it is embedded in the emitted "
            "record filenames"
        )
    if review_kind is not None and review_kind not in {
        "plan-review",
        "branch-review",
        "code-review",
        "exec-review",
    }:
        raise SelectionUsageError(
            f"invalid --kind {review_kind!r}: use plan-review, branch-review, code-review, or exec-review"
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


def select_record(
    reviews_dir: Path,
    slug: str,
    source_digest: str,
    explicit_new_round: bool = False,
    review_kind: str | None = None,
    source_plan: Path | None = None,
    advisories: list[str] | None = None,
) -> Selection:
    """Decide reuse vs the next round, or refuse (the overwrite guard).

    ``advisories`` is the optional out-parameter threaded down to
    ``_enumerate``: the caller owns the list and any printing (this function
    neither prints nor keeps module state).
    """
    reviews_dir = Path(reviews_dir)
    _validate_slug_and_kind(slug, review_kind)
    if not source_digest.strip():
        # A caller-supplied invocation error, not a record-corpus state:
        # an empty digest would silently disable the overwrite guard, so
        # this usage error (exit 2) is decided before any record-corpus
        # state is consulted.
        raise SelectionUsageError(
            "--source-digest is empty; an empty digest would silently "
            "disable the overwrite guard"
        )
    if SOURCE_DIGEST_PATTERN.fullmatch(source_digest) is None:
        # The digest-grammar usage error (exit 2) is likewise decided
        # before any record-corpus state is consulted: an orphan half in
        # the corpus must never mask this invocation-level refusal with
        # the exit-1 taxonomy.
        raise SelectionUsageError(
            f"invalid --source-digest {source_digest!r}: a source digest "
            "must match ^[0-9a-f]{64}$ (a lowercase 64-character hex "
            "SHA-256, the sidecar source_digest grammar); refusing the "
            "comparison input before any record is read"
        )
    identity = None
    if review_kind == "plan-review":
        if source_plan is None:
            raise SelectionUsageError("--kind plan-review requires --source-plan")
        identity = _plan_identity(Path(source_plan), reviews_dir)
    # A bare slug with an explicit non-plan-review kind selects that
    # family's suffix-shaped records only (the documented caller shape);
    # a slug already carrying the kind infix keeps the legacy spelling.
    family_kind = _family_scope(slug, review_kind)
    pairs, orphans, backups_ignored = _enumerate(
        reviews_dir, slug, review_kind=review_kind,
        source_plan_identity=identity,
        family_kind=family_kind, advisories=advisories
    )
    if orphans:
        named = ", ".join(sorted(path.name for path in orphans))
        raise SelectionRefused(
            "orphaned record half in "
            f"{reviews_dir}: {named} has no matching Markdown/sidecar twin; "
            "refusing both reuse and allocation until the orphan half is "
            "repaired (restore the missing twin or remove the orphan)"
        )

    def emit(round_number: int, *, selected_stem: str | None = None) -> tuple[Path, Path]:
        if selected_stem is None:
            if family_kind is not None:
                selected_stem = f"{slug}-{family_kind}"
            else:
                kind_prefix = f"{review_kind}-" if review_kind else ""
                selected_stem = f"{kind_prefix}{slug}"
            if identity is not None:
                selected_stem += "-p" + _identity_token(identity)
        elif identity is not None:
            selected_stem = re.sub(r"-p[0-9a-f]{8}$", "", selected_stem)
            selected_stem += "-p" + _identity_token(identity)
        base = f"{DATE_SOURCE().isoformat()}-{selected_stem}-r{round_number}"
        return reviews_dir / f"{base}.md", reviews_dir / f"{base}.stats.json"

    if not pairs:
        markdown, sidecar = emit(1)
        return Selection("new-record", markdown, sidecar, None, backups_ignored)

    latest = pairs[-1]
    if explicit_new_round:
        prior_stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", latest.base)
        prior_stem = re.sub(r"-r\d+$", "", prior_stem)
        markdown, sidecar = emit(latest.round + 1, selected_stem=prior_stem)
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

try:
    from validate_review_staging import (
        classify_fence_lines as _classify_fence_lines,
    )
except ImportError:  # direct-script invocation where scripts/ is not sys.path[0]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validate_review_staging import (
        classify_fence_lines as _classify_fence_lines,
    )

# The canonical reviewed-scope digest derivation and the commit resolver,
# imported (not copied) from the corrections machinery so verify-digest
# grades against exactly the diff-bytes-plus-sha256 shape the seal
# validator grades and the classifiers consume: one freshness notion.
try:
    from corrections_record import (
        diff_bytes as _diff_bytes,
        git_text as _git_text,
        resolve_commit as _resolve_commit,
        sha256_hex as _sha256_hex,
    )
except ImportError:  # direct-script invocation where scripts/ is not sys.path[0]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from corrections_record import (
        diff_bytes as _diff_bytes,
        git_text as _git_text,
        resolve_commit as _resolve_commit,
        sha256_hex as _sha256_hex,
    )


def _fence_mask(lines: list[str]) -> tuple[list[bool], int | None]:
    """True per line that is fenced content (r2 F5).

    Adapter over the validator's shared fence classifier (the single fence
    state machine): the mask marks exactly the lines whose classifier event
    is ``in_fence_content``, and the unclosed index is the classifier's.
    The helper's own opener regex travels through the classifier's declared
    ``fence_line_re`` seam parameter; it is deliberately narrower than the
    classifier's default (no form-feed-prefixed openers), and that
    divergence is carried as the named parameter, not as a copied grammar.
    A fenced template copy can therefore never contribute a marker line or
    a Metadata heading.

    Returns ``(mask, unclosed_opener_index)`` where the second element is
    the index of a fence opener that never closed, or None when every
    fence closed. An unclosed fence would mask the whole file tail, so the
    caller refuses the operation instead of scanning a truncated record
    (r3 F1).
    """
    events, unclosed_opener_index = _classify_fence_lines(
        lines, fence_line_re=_FENCE_LINE_RE
    )
    mask = [event == "in_fence_content" for event, _payload in events]
    return mask, unclosed_opener_index


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


# The orphan record's recorded digest line (the staging template's
# ``- Source digest: <sha256>`` Metadata bullet): the fresh pair's
# overwrite guard compares digests, so the recovery reads the digest from
# the orphan record itself instead of inventing a second source.
_ORPHAN_SOURCE_DIGEST_RE = re.compile(
    r"^-[ \t]*Source digest[ \t]*:[ \t]*([0-9a-f]{64})[ \t]*$",
    re.MULTILINE,
)


def recover_orphan(
    record_path: Path, slug: str, review_kind: str | None = None,
    source_plan: Path | None = None
) -> dict:
    """Preserve an orphan half and allocate the fresh canonical pair.

    The refusal arms (review round record lifecycle gaps plan, Task 3)
    fire before any mutation, each a named one-line error leaving the
    reviews directory byte-identical: a record whose sidecar twin exists
    is not an orphan, an absent record refuses, and a name already
    carrying the ``.orphan-`` infix is already preserved (so a second
    recovery can never double-suffix). The slug and kind gates run first
    (the shared usage-error precedence); the slug and kind are explicit
    caller inputs and are never inverse-parsed from the preserved stem.
    The orphan's own recorded ``Source digest`` feeds the existing
    allocation logic (``select`` with ``--explicit-new-round``), which
    runs after the rename so the preserved name is discovery-invisible
    and the canonical path is vacated. Every mutation is the single
    rename to ``<original stem>.orphan-<UTCtimestamp>.md``; the fresh
    pair is emitted, never written. The receipt names the preserved
    path, the allocated pair, and the exact ``Orphan recovery:``
    Metadata line to add, the preserved path spelled repo-relative so
    the printed line passes the validator's orphan-recovery link gate
    verbatim; the repo root is resolved before the rename, so a
    non-repository reviews directory refuses without any mutation.
    """
    _validate_slug_and_kind(slug, review_kind)
    record = Path(record_path)
    if ORPHAN_INFIX in record.name:
        raise SelectionRefused(
            f"cannot recover {record.name}: the name already carries the "
            f"{ORPHAN_INFIX!r} infix (already preserved); a preserved "
            "orphan is never recovered again"
        )
    if not record.is_file():
        raise SelectionRefused(
            f"cannot recover the absent record {record}: no record exists "
            "at that path; recover-orphan preserves an existing canonical "
            "Markdown only"
        )
    sidecar = _sidecar_twin(record)
    if sidecar.is_file():
        raise SelectionRefused(
            f"cannot recover {record.name}: it is not an orphan (its "
            f"sidecar twin {sidecar.name} exists); recover-orphan "
            "preserves a canonical Markdown whose sidecar is missing"
        )
    try:
        content = record.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SelectionRefused(
            f"cannot read the orphan record {record.name} ({exc}); "
            "repair the record before recovering it"
        ) from exc
    digest_match = _ORPHAN_SOURCE_DIGEST_RE.search(content)
    if digest_match is None:
        raise SelectionRefused(
            f"the orphan record {record.name} carries no '- Source digest: "
            "<64-char lowercase hex>' Metadata line; the fresh pair's "
            "allocation compares digests, so repair the record's digest "
            "line before recovering it"
        )
    toplevel = _git_text(record.parent, "rev-parse", "--show-toplevel")
    if not toplevel:
        raise SelectionRefused(
            f"cannot recover {record.name}: the reviews directory "
            f"{record.parent} is not inside a git repository; the "
            "evidence link is repo-relative by contract, so run the "
            "recovery inside the repository"
        )
    repo_root = Path(toplevel.strip())
    reviews_dir = record.parent
    identity = (
        _plan_identity(source_plan, reviews_dir)
        if review_kind == "plan-review" and source_plan is not None
        else None
    )
    if review_kind == "plan-review" and identity is None:
        raise SelectionUsageError("--kind plan-review requires --source-plan")
    # The other-orphan pre-check enumerates the same family pattern the
    # post-rename select_record allocation will use, so a blocking orphan
    # half is always refused before the record is renamed, never after.
    family_kind = _family_scope(slug, review_kind)
    pairs, orphans, _backups = _enumerate(
        reviews_dir, slug, review_kind=review_kind,
        source_plan_identity=identity,
        family_kind=family_kind
    )
    other_orphans = [
        orphan for orphan in orphans if orphan.resolve() != record.resolve()
    ]
    if other_orphans:
        named = ", ".join(sorted(path.name for path in other_orphans))
        raise SelectionRefused(
            f"cannot recover {record.name}: another orphaned record half "
            f"blocks the fresh allocation in {reviews_dir}: {named}; "
            "recover or repair the other orphan half first"
        )
    stem = record.name[: -len(".md")]
    preserved = _unique_path(
        reviews_dir,
        stem,
        ".md",
        ORPHAN_TIMESTAMP_SOURCE(),
        infix=ORPHAN_INFIX,
        noun="preserved-orphan",
    )
    if os.path.lexists(preserved):
        raise SelectionUsageError(
            f"the preserved-orphan name {preserved.name} appeared while "
            "the recovery was being placed; refusing to overwrite it"
        )
    rel_preserved = Path(
        os.path.relpath(preserved.resolve(), repo_root.resolve())
    ).as_posix()
    os.rename(record, preserved)
    selection = select_record(
        reviews_dir,
        slug,
        digest_match.group(1),
        explicit_new_round=True,
        review_kind=review_kind,
        source_plan=source_plan,
    )
    return {
        "status": "recovered",
        "orphan": str(record),
        "preserved": str(preserved),
        "markdown": str(selection.markdown),
        "sidecar": str(selection.sidecar),
        "decision": selection.decision,
        "plan_identity": identity,
        "metadata_line": (
            f"{ORPHAN_RECOVERY_METADATA_LABEL} {rel_preserved}"
        ),
    }


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


def _unique_path(
    directory: Path,
    stem: str,
    extension: str,
    timestamp: str,
    infix: str = BACKUP_INFIX,
    noun: str = "backup",
) -> Path:
    """First non-existing candidate name, with a bounded collision search.

    ``os.path.lexists`` (not a following ``Path.exists``) decides occupancy,
    so a planted dangling symlink at a candidate name counts as taken
    instead of being followed (r1 F12). The collision counter is bounded
    (r1 F11): exhausting it raises a usage error (exit 2) rather than
    looping. The ``infix`` parameter carries the name family: ``.backup-``
    for archival copies, ``.orphan-`` for preserved orphans.
    """
    candidate = directory / f"{stem}{infix}{timestamp}{extension}"
    counter = 1
    while os.path.lexists(candidate):
        if counter >= _UNIQUE_PATH_LIMIT:
            raise SelectionUsageError(
                f"no free {noun} name for {stem}{infix}{timestamp}"
                f"{extension} after {_UNIQUE_PATH_LIMIT} collision "
                "suffixes; refusing to loop unbounded"
            )
        candidate = directory / f"{stem}{infix}{timestamp}-{counter}{extension}"
        counter += 1
    return candidate


def _corrections_chain_terminal(sidecar: Path) -> tuple[str | None, str | None]:
    """The recorded corrections chain's terminal ``(after_digest, after_head)``.

    The sidecar's ``extensions.corrections`` array is the receipt the
    graded corrections flow records: the staging validator owns verifying
    the chain (its graded stale arm runs the anchor, binding, linkage,
    and terminal legs over the seal), and rows are written only through
    that graded surface. verify-digest consults that recorded ownership
    rather than re-grading it: the terminal row's ``after_digest`` and
    ``after_head`` are what "terminates at the current bytes" means
    mechanically here. Anything absent or malformed reads as no chain, so
    the plain exact-match and refusal arms stand unchanged.
    """
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    if not isinstance(payload, dict):
        return None, None
    extensions = payload.get("extensions")
    if not isinstance(extensions, dict):
        return None, None
    rows = extensions.get("corrections")
    if not isinstance(rows, list) or not rows:
        return None, None
    terminal = rows[-1]
    if not isinstance(terminal, dict):
        return None, None
    after_digest = terminal.get("after_digest")
    after_head = terminal.get("after_head")
    if not isinstance(after_digest, str) or not isinstance(after_head, str):
        return None, None
    return after_digest, after_head


def verify_digest(
    record_path: Path, reviews_dir: Path, base: str, expect_head: str
) -> dict:
    """Recompute the reviewed-scope digest and refuse a stale record.

    Every operand is an explicit caller input and is never derived: the
    record path (the latest round's staging Markdown), its reviews
    directory (the record must resolve inside it, so a stray path can
    never pass as the corpus's record), the recorded base commit, and the
    latest recorded verified head (from the session manifest, or the
    corrections chain's after-head when a chain carries the record). The
    digest is recomputed over the invoking process's repository with the
    canonical derivation (``git diff <base>...<head>`` bytes through
    ``corrections_record.diff_bytes``, hashed with
    ``corrections_record.sha256_hex``) and compared against the sidecar's
    ``source_digest`` through the existing read helper.

    Decision order: record-state refusals first (an absent record, a
    backup-shaped name, a record outside --dir, an orphan half without
    its sidecar twin, a sidecar without a readable ``source_digest``
    string), then the git operands, then the comparison with the
    corrections precedence pinned: a chain whose terminal binds the
    current bytes and HEAD yields the named accepted-stale pass ahead of
    any refusal, so corrections-carried records never verify permanently
    stale; without such a chain a digest mismatch is the named stale
    refusal (both digests and the record named) and a HEAD move past the
    recorded verified head refuses even when the reviewed-scope bytes are
    unchanged. The pass receipts name the verified HEAD beside the digest
    comparison; the accepted-stale pass names both heads, the chain's
    after-head being the movement. The subcommand mutates nothing: every
    path here only reads.
    """
    record = Path(record_path)
    if not record.is_file():
        raise SelectionRefused(
            f"cannot verify the absent record {record}: no record exists "
            "at that path; verify-digest checks the explicit --record and "
            "never derives one"
        )
    if BACKUP_INFIX in record.name:
        raise SelectionRefused(
            f"cannot verify the backup pair {record.name}: backup-shaped "
            "names are archived copies, never the live record; pass the "
            "live round record"
        )
    resolved_dir = Path(reviews_dir).resolve()
    try:
        record.resolve().relative_to(resolved_dir)
    except ValueError:
        raise SelectionUsageError(
            f"invalid --record {record}: it resolves outside the reviews "
            f"directory {resolved_dir} named by --dir; verify-digest "
            "checks a record inside the corpus the caller names"
        ) from None
    sidecar = _sidecar_twin(record)
    if not sidecar.is_file():
        raise SelectionRefused(
            f"cannot verify the orphaned record half {record.name}: its "
            f"sidecar twin {sidecar.name} is missing; a record verifies "
            "as a Markdown/sidecar pair only, so restore the missing twin "
            "or remove the orphan"
        )
    recorded_digest = _read_sidecar_digest(sidecar)
    repo = Path.cwd()
    base_commit = _resolve_commit(repo, base)
    if base_commit is None:
        raise SelectionUsageError(
            f"invalid --base {base!r}: git cannot resolve it to a commit "
            "in the invoking repository; the base is an explicit caller "
            "input and is never guessed"
        )
    expected_commit = _resolve_commit(repo, expect_head)
    if expected_commit is None:
        raise SelectionUsageError(
            f"invalid --expect-head {expect_head!r}: git cannot resolve it "
            "to a commit in the invoking repository; the recorded verified "
            "head is an explicit caller input and is never guessed"
        )
    head_commit = _resolve_commit(repo, "HEAD")
    if head_commit is None:
        raise SelectionRefused(
            "cannot resolve the invoking repository's HEAD; the freshness "
            "comparison refuses rather than verify against an unknown HEAD"
        )
    diff = _diff_bytes(repo, base_commit, head_commit)
    if diff is None:
        raise SelectionRefused(
            f"cannot recompute the reviewed-scope digest: the diff "
            f"{base_commit}...{head_commit} is unresolvable in the "
            "invoking repository; refusing the freshness comparison"
        )
    recomputed = _sha256_hex(diff)
    chain_after_digest, chain_after_head = _corrections_chain_terminal(sidecar)
    chain_binds_current = (
        chain_after_digest == recomputed and chain_after_head == head_commit
    )
    if recomputed == recorded_digest and head_commit == expected_commit:
        return {
            "outcome": "fresh",
            "record": str(record),
            "reviewed_base": base_commit,
            "recorded_digest": recorded_digest,
            "recomputed_digest": recomputed,
            "verified_head": head_commit,
        }
    if chain_binds_current:
        return {
            "outcome": "accepted-stale",
            "record": str(record),
            "reviewed_base": base_commit,
            "recorded_digest": recorded_digest,
            "recomputed_digest": recomputed,
            "verified_head": head_commit,
            "expected_head": expected_commit,
            "corrections_after_head": chain_after_head,
        }
    if recomputed != recorded_digest:
        raise SelectionRefused(
            f"stale review record {record}: sidecar source_digest "
            f"{recorded_digest} differs from the recomputed reviewed-scope "
            f"digest {recomputed} over {base_commit}...{head_commit}; the "
            "record is not current evidence; run a fresh round on the "
            "recomputed digest or re-bind it through the staging "
            "validator's corrections arm"
        )
    raise SelectionRefused(
        f"refusing the moved HEAD for {record.name}: HEAD {head_commit} is "
        f"past the recorded verified head {expected_commit} while the "
        f"reviewed-scope digest {recomputed} is unchanged; a HEAD move "
        "past the recorded verified head refuses without a verified "
        "corrections chain terminating at the current bytes"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="review_record_selection",
        description=(
            "Select review record paths (reuse or next -r<N> round) with an "
            "overwrite guard, mark supersession links, write immutable "
            "backups, and recover stranded orphan halves"
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
        "--source-plan", help="source plan path; required for plan-review identity"
    )
    select_parser.add_argument(
        "--kind",
        choices=("plan-review", "branch-review", "code-review", "exec-review"),
        help="review family scoping: plan-review prefixes the emitted name, "
        "other kinds scope a bare slug to that family's suffix-form records",
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

    recover_parser = subparsers.add_parser(
        "recover-orphan",
        help="preserve an orphan half and allocate the fresh canonical pair",
    )
    recover_parser.add_argument(
        "--record",
        required=True,
        help="the orphan canonical Markdown (no sidecar twin)",
    )
    recover_parser.add_argument(
        "--source-plan", help="source plan path; required for plan-review identity"
    )
    recover_parser.add_argument(
        "--slug",
        required=True,
        help="artifact slug embedded in the fresh record names (never "
        "inverse-parsed from the preserved stem)",
    )
    recover_parser.add_argument(
        "--kind",
        choices=("plan-review", "branch-review", "code-review", "exec-review"),
        help="review family scoping: plan-review prefixes the emitted name, "
        "other kinds scope a bare slug to that family's suffix-form records",
    )

    verify_parser = subparsers.add_parser(
        "verify-digest",
        help="recompute the reviewed-scope digest at a record-reading "
        "boundary and refuse a stale record",
    )
    verify_parser.add_argument(
        "--record",
        required=True,
        help="the record Markdown to verify (the latest round's record)",
    )
    verify_parser.add_argument(
        "--dir",
        required=True,
        help="reviews directory the record belongs to",
    )
    verify_parser.add_argument(
        "--base",
        required=True,
        help="the recorded base commit the reviewed-scope diff is "
        "computed over",
    )
    verify_parser.add_argument(
        "--expect-head",
        required=True,
        help="the latest recorded verified head (from the session "
        "manifest, or the corrections chain's after-head)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "select":
            # Advisory out-parameter (review-record legacy identity plan,
            # Task 1): main owns the list; select_record threads it down to
            # the enumeration, and the advisories ride the JSON envelope as
            # a non-blocking array. The advisories never change the decision.
            advisories: list[str] = []
            selection = select_record(
                Path(args.dir),
                args.slug,
                args.source_digest,
                explicit_new_round=args.explicit_new_round,
                review_kind=args.kind,
                source_plan=Path(args.source_plan) if args.source_plan else None,
                advisories=advisories,
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
                        "plan_identity": (
                            _plan_identity(Path(args.source_plan), Path(args.dir))
                            if args.kind == "plan-review" and args.source_plan
                            else None
                        ),
                        "advisories": advisories,
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
        if args.command == "recover-orphan":
            receipt = recover_orphan(
                Path(args.record), args.slug, review_kind=args.kind,
                source_plan=Path(args.source_plan) if args.source_plan else None,
            )
            print(json.dumps(receipt))
            print(
                f"Metadata line for the fresh record: {receipt['metadata_line']}",
                file=sys.stderr,
            )
            return 0
        if args.command == "verify-digest":
            outcome = verify_digest(
                Path(args.record), Path(args.dir), args.base, args.expect_head
            )
            print(json.dumps(outcome))
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
