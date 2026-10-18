#!/usr/bin/env python3
"""Fail-closed readiness validator for reviewed plans.

Given a plan path, answers: does the latest review of these exact plan bytes
report ready=yes with zero unresolved blocking findings and a valid sidecar --
or, when that final round declares a cap closure (``extensions.cap_closure``),
does the plan carry the conforming terminal ``## Residual findings (cap
closure)`` section that stands in for the yes verdict? A plan under the plans
dir's ``rejected/`` archive is never active-ready: it is excluded with its own
named reason before any review checks run.

Exit 0 only when every readiness condition passes; otherwise prints the FIRST
failed condition and exits 1. Digest, schema, sidecar-path, and review-parsing
rules are IMPORTED from ``validate_review_staging.py`` (same directory); the
digest recipe is never re-implemented here. ``{plans_dir}`` and ``{reviews_dir}``
resolve from the ``.ai-playbook/facts.md`` TOML block via ``facts_paths.py``.

Outcome contract (scripts/OUTCOME_CONTRACT.md): exit 0 pass (every readiness
condition holds), exit 1 fail (the FIRST failed condition is named on
stderr), exit 2 indeterminate (not modeled: a readiness run over readable
inputs always reaches a verdict), exit 3 tool error (argparse usage and
mutual-exclusion violations overridden from argparse's exit 2, and a
sibling-compatibility mismatch: compatibility evidence is about the
environment pairing, never a readiness fail). Every non-metadata run ends
with exactly one final ``OUTCOME:`` line on stdout after the human-readable
evidence; ``--help`` is a metadata exit with no ``OUTCOME:`` line. The
``--sweep`` drift mode rides the same vocabulary. The importable probe
functions (``evaluate_readiness``, the structural probes behind
``run_pre_round``, ``check_review_name``, ``run_sweep``'s helpers) are
library surfaces outside this CLI contract and keep their function-level
behavior.

Condition ordering inside ``evaluate_readiness`` is deliberate: local
readability checks (plan path, review artifact, sidecar file, sidecar JSON,
review UTF-8, plan bytes) run first so each gets its own named reason, then
the shared sidecar gate (schema, source_kind, digest), then the verdict line,
then ``is_review_ready``. Several of those readability steps re-state checks
the shared gate would also make; they exist for reason classification, not
duplication.
"""

from __future__ import annotations

import argparse
import contextlib
import glob as globmod
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import facts_paths
import plan_shape
import runtime_capabilities
import validate_review_staging as vrs
from review_plan_identity import (
    identity_token as plan_identity_token,
    normalize_plan_path,
    record_identity,
    repository_root,
)

# Invocation telemetry (the fail-open wall-time writer, plan
# 2026-10-14-script-runtime-cost-telemetry): a deployed copy without the
# sibling keeps the full contract byte-identical, appending no line and
# printing nothing on either channel.
try:
    import invocation_telemetry
except Exception:  # pragma: no cover - a corrupt sibling must fail open too
    invocation_telemetry = None  # type: ignore

# The corrections-record sibling (review-cert-graded-binding plan): the
# marker-prefix constant owner for the caller dispatch, the hermetic
# scratch-repo builder for the in-file selftest, and the module whose
# verifier legs the shared gate's graded stale arm runs. A deployment
# missing the module keeps the legacy exact-match digest rule: the graded
# stale arm never arms without it (the shared validator degrades the same
# way), so the fallback is the named degradation, never a crash.
try:
    import corrections_record
except ImportError:  # deployment gap: legacy digest rule, per its own row
    corrections_record = None

# Sibling compat handshake: the COMPAT_VERSION value of the sibling shared-rule
# module (vrs) that THIS validator shipped against. Checked at every launch
# (gate, sweep, selftest) before any other work; a missing or mismatched
# sibling value means a partially updated deployment. Bumped 2 to 3 with
# the cap-closure terminal shape (certification machinery
# contract-collisions plan, Task 1): this verdict arm consumes the vrs
# CAP_CLOSURE_SECTION_HEADING constant and the malformed-declaration
# rejection lives in the new vrs wiring, so the shared-rule semantics are
# pair-coupled.
EXPECTED_SIBLING_COMPAT_VERSION = 3

# Outcome contract (scripts/OUTCOME_CONTRACT.md): the four outcomes and the
# argparse override. A usage violation exits 3 with a final `OUTCOME:
# tool_error` line on stderr before exit (the usage text and the error
# message share that stream); every non-metadata run's final line is on
# stdout after the human-readable evidence.
OUTCOME_LABELS = {0: "pass", 1: "fail", 2: "indeterminate", 3: "tool_error"}


class OutcomeArgumentParser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit 3 (tool error) with a final
    `OUTCOME: tool_error` line on stderr before exit, overriding argparse's
    default exit 2; `--help` stays a metadata exit without an `OUTCOME:`
    line."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        sys.stderr.write("OUTCOME: %s\n" % OUTCOME_LABELS[3])
        raise SystemExit(3)

# Round suffix of a review artifact filename: ``-r<N>.md`` (N >= 1).
# Case-sensitive on purpose: the discovery glob below is lowercase-only, so
# an uppercase ``-R1.md`` artifact is invisible to both (consistent pair).
ROUND_RE = re.compile(r"-r(\d+)\.md$")
# Verdict token inside the review's ``## Summary`` section. TOTAL rule
# (r4 reconciliation directive): a verdict line is ANY line in the section
# containing a word-bounded ``ready=yes`` / ``ready=no`` token — bare,
# bulleted, bolded, behind a ``Verdict:`` / ``Ready for execution:`` label,
# or as a prose tail (``… — ready=yes.``, ``- Blocking findings: 0 —
# ready=yes``, ``Counts: … **ready=yes** — …``). A prose mention IS the
# verdict under the total rule; the fail-open concern that motivated the old
# prefix/label shape-chasing is covered by the OTHER readiness conditions
# (sidecar schema, digest match, ``is_review_ready`` zero-blocking), so the
# grammar no longer tries to distinguish prose from verdict lines. Matching
# stays PER LINE (a token split across two lines never matches) and the LAST
# occurrence in the section wins.
# PRECEDENCE (2026-09-05 plan-readiness-migration): the sidecar ``verdict``
# field ("yes"/"no", written by review-plan) is the PREFERRED verdict source;
# this per-line total rule is the LEGACY fallback for pre-adoption artifacts
# whose sidecar lacks a conforming field. Deleting the legacy grammar is
# TIME-GATED and tracked in the spin-off backlog item
# ``docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md``
# (eligible only once ``--sweep`` coverage reports a positive total with covered equal to total).
VERDICT_TOKEN_RE = re.compile(r"\bready\s*=\s*(yes|no)\b", re.IGNORECASE)

# Plans reviewed on or after this date must carry the decision-points trailer
# (plans skill Step 1.4 confirmation, carried into ## Assumptions). Plans with
# an earlier latest-round date are legacy and stay exempt: the rule is
# forward-looking and does not retrofit already-certified plans (origin
# backlog exclusion).
DECISION_MARKER_MIN_DATE = "2026-09-08"

# The trailer line in plan bytes: "Decision points requiring a grill: <value>".
# The bolded "**Decision points requiring a grill:**" form is the Step 1.4
# chat template and never matches; the plan-file trailer is plain.
DECISION_MARKER_RE = re.compile(
    r"^Decision points requiring a grill:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE
)

# Plans reviewed on or after this date must have a well-formed ##
# Review Scope section (path categories consistent with path kind, no
# path in two categories, every task Files: path inventoried). Earlier
# rounds are legacy and exempt (no retrofit of already-certified plans).
REVIEW_SCOPE_MIN_DATE = "2026-09-09"

# Plans reviewed on or after this date must satisfy the plan-ownership
# static checks (plan_ownership_problem: at most one creating task per
# new file, consumer-before-owner ordering for file paths, Files: paths
# existing on disk or carrying the planned-new marker, at most one
# transition-table section) and the scope-classification probe
# (scope_classification_problem: every task checklist item carries a
# classification tag from the four-name vocabulary, and the Ship-when-only
# classes stay off task items). Earlier rounds are legacy and exempt (no
# retrofit of already-certified plans).
PLAN_STRUCTURE_MIN_DATE = "2026-09-19"

# Generic default path-kind suffix tables for the Review Scope category
# gate. These are LANGUAGE/FORMAT defaults (implementation vs
# documentation file extensions) and must NOT be narrowed or widened to
# encode one consumer repository's layout; repo-specific classification
# belongs in the plan text, not in these constants. Pure-config
# extensions (.yaml .yml .json .toml .xml .gradle) are deliberately
# ABSENT from the implementation table (r1 F3): docs pipelines carry
# real config (mkdocs.yaml, docs/_data/refs.json) under Documentation,
# and flagging them taught authors to misclassify; a doc-suffix path
# under Documentation is additionally authoritative via the doc table
# below (r1 F4/F7 consumer).
REVIEW_SCOPE_IMPLEMENTATION_SUFFIXES = (
    ".py", ".java", ".kt", ".kts", ".ts", ".tsx", ".js", ".jsx", ".go",
    ".rb", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".php",
    ".sh", ".bash", ".sql",
)
REVIEW_SCOPE_DOC_SUFFIXES = (".md", ".rst", ".adoc", ".txt")


def sidecar_verdict(payload: dict) -> str | None:
    """Conforming sidecar ``verdict`` value (``"yes"``/``"no"``), else ``None``.

    Single owner of the conforming-verdict predicate: the readiness verdict
    step and the sweep coverage counter both route through this helper, so
    the yes/no membership test exists exactly once. Any other value (absent,
    dict-valued legacy key, non-yes/no string) yields ``None`` and callers
    fall back to the legacy Summary rule; version-1 records never reach a
    caller with a non-conforming value because the schema gate rejects them
    earlier.
    """
    value = payload.get("verdict")
    return value if value in vrs.VERDICT_VALUES else None


def verdict_tokens(summary: str) -> list[str]:
    """Verdict tokens (``yes``/``no``) per matching line, in document order."""
    tokens: list[str] = []
    for line in summary.splitlines():
        for match in VERDICT_TOKEN_RE.finditer(line):
            tokens.append(match.group(1).lower())
    return tokens


def repo_root(start: Path) -> Path:
    """Return the git toplevel for ``start``, or ``start`` itself on failure."""
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).resolve()
    except (subprocess.SubprocessError, OSError):
        pass
    return start.resolve()


def feature_slug(plan_path: Path) -> str:
    """Plan filename stem minus its leading ``YYYY-MM-DD-`` prefix."""
    stem = plan_path.stem
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem, count=1)


# The canonical artifact-slug shape: the lowercase kebab shape the
# corrections and seal path enforces (corrections_record's SEAL_SLUG_RE
# shape). ``artifact_slug`` reports a named refusal for a lowercased
# feature slug outside it and never sanitizes by any other transform.
_KEBAB_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ArtifactSlugRefusal(ValueError):
    """The one pinned derivation refusal for the canonical artifact slug.

    Raised by ``artifact_slug`` when the plan's lowercased feature slug is
    not already a safe kebab token. Every consumer surface catches it in
    place and converts it to its own named failure shape (a readiness
    ``(False, reason)`` path, a validator ``None`` slug, a runtime
    refusal), so no seam ever surfaces it as a traceback; it subclasses
    ``ValueError`` so existing narrow ``except ValueError`` postures keep
    degrading exactly as before.
    """


def artifact_slug(plan_path: Path) -> str:
    """The one machine identity for plan-review artifacts: the feature
    slug lowercased.

    The plan filename's story key (its uppercase ticket prefix) stays
    preserved in prose, titles, and links; only machine surfaces (the
    discovery glob, per-round name binding, sidecar equality, the
    evidence payload's seal-context slug, seal paths) resolve through
    this lowercase canonical form. A lowercased feature slug that does
    not fullmatch the kebab shape raises ``ArtifactSlugRefusal`` naming
    the plan filename and the kebab rule; nothing else is transformed.
    """
    feature = feature_slug(plan_path)
    slug = feature.lower()
    if not _KEBAB_SLUG_RE.fullmatch(slug):
        raise ArtifactSlugRefusal(
            f"cannot derive a canonical artifact slug: plan filename "
            f"{plan_path.name!r} carries feature slug {feature!r}, whose "
            f"lowercase form {slug!r} is not a safe kebab token (only "
            "lowercase letters and digits, joined by single hyphens; no "
            "underscores, dots, or leading/trailing hyphens)"
        )
    return slug


# ONE encoding of the review-round discovery shape
# ``*-plan-review-<feature-slug>[-p<8-hex-token>]-r<N>.md`` (N >= 1): a glob skeleton
# ``latest_review_round`` iterates under the reviews directory and a regex
# skeleton the ``--check-review-name`` probe fullmatches a round filename
# against. Both are instantiated by ``review_round_shape`` below, which also
# owns the slug escaping per pattern language, so the two matchers cannot
# drift into disagreeing about what a discoverable round is.
_REVIEW_ROUND_GLOB_SKELETON = "*-plan-review-{slug}*-r*.md"
_REVIEW_ROUND_NAME_SKELETON = r".*-plan-review-{slug}(?:-p[0-9a-f]{{8}})?-r([1-9]\d*)\.md"


class AmbiguousReviewSeries(ValueError):
    """Two canonical pairs claim the same round for one source plan."""


def review_round_shape(slug: str) -> tuple[str, re.Pattern[str]]:
    """Both pattern-language forms of the discovery shape for ``slug``.

    Returns ``(glob_pattern, name_re)``: the glob string for ``Path.glob``
    in ``latest_review_round`` and the compiled regex the
    ``--check-review-name`` probe fullmatches a round filename against.
    The slug is escaped inside this helper (glob metacharacters for the
    glob form, regex metacharacters for the fullmatch form); no caller
    re-derives either the shape or the escaping.
    """
    return (
        _REVIEW_ROUND_GLOB_SKELETON.format(slug=globmod.escape(slug)),
        re.compile(_REVIEW_ROUND_NAME_SKELETON.format(slug=re.escape(slug))),
    )


def latest_review_round(
    reviews_dir: Path,
    slug: str,
    plan_identity: str | None = None,
) -> tuple[Path, int] | None:
    """Latest review artifact for ``slug``: highest ``r<N>``, ties by filename.

    Never resolves latest by mtime. The candidate glob is instantiated by
    the shared ``review_round_shape``: one encoding of the discovery shape,
    consumed here and by the ``--check-review-name`` probe's fullmatch.
    """
    candidates: list[tuple[int, str, Path]] = []
    glob_pattern, name_re = review_round_shape(slug)
    for path in reviews_dir.glob(glob_pattern):
        match = name_re.fullmatch(path.name)
        if match:
            if plan_identity is not None:
                sidecar = vrs.stats_sidecar_path(path)
                try:
                    payload = json.loads(sidecar.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    # The legacy Markdown path may still assign this pair
                    # to a different source plan; the selected plan's own
                    # sidecar is graded by evaluate_readiness afterward.
                    payload = None
                candidate_identity = record_identity(path, payload)
                if candidate_identity is None:
                    raise AmbiguousReviewSeries(
                        f"cannot resolve plan identity for {path.name}: "
                        "missing or unreadable identity metadata"
                    )
                if candidate_identity != plan_identity:
                    continue
            candidates.append((int(match.group(1)), path.name, path))
    if not candidates:
        return None
    rounds = [candidate[0] for candidate in candidates]
    duplicates = sorted(number for number in set(rounds) if rounds.count(number) > 1)
    if plan_identity is not None and duplicates:
        raise AmbiguousReviewSeries(
            "matching records for one source plan contain duplicate round(s): "
            + ", ".join(f"r{number}" for number in duplicates)
        )
    round_no, _, path = max(candidates)
    return path, round_no


def md_section(text: str, heading: str) -> str:
    """Text of the ``## <heading>`` section, or ``""`` when absent.

    Fail-closed: an absent heading yields an empty string, so a trailer
    gate scoped to one section never falls back to matching a trailer
    line elsewhere in the whole document.
    """
    match = re.search(
        rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE
    )
    if not match:
        return ""
    tail = text[match.end() :]
    return re.split(r"\n## ", tail, maxsplit=1)[0]


def summary_section(content: str) -> str:
    """Text of the ``## Summary`` section (empty when absent)."""
    return md_section(content, "Summary")


# Placeholder vocabulary for trailer values: a receipt segment is
# unresolved when its start is pending, tbd, todo, or open
# (case-insensitive) followed by end of value, whitespace, or more word
# characters. The boundary is a negative lookahead for the HYPHEN
# character only — not ``\b`` and not word characters: a stem followed
# immediately by a hyphen is treated as a resolved receipt, so
# ``todo-list ownership: ...``, ``tbd-for-now``, and ``open-question
# policy: ...`` pass, while ``todos``, ``pending2``, and ``TBD for now``
# fail. The hyphen carve-out is load-bearing for the pinned ``todo-list``
# receipt (r2 F2) and the ``open-question`` receipt; ``\b`` would also
# match at the hyphen boundary and wrongly reject them. Lookalikes with
# trailing word characters fail (r3 F3). Receipt-wording constraints
# shared by every stem: a receipt segment must not BEGIN with a bare
# stem word (reword it or hyphenate, e.g. "open-question"; only the
# hyphen arm escapes the stem), and a receipt must not contain a
# semicolon, because any ``;`` starts a new segment under the
# per-segment split (use commas inside a receipt instead). The ``<``
# template-token check is separate (r2 F2).
_PLACEHOLDER_RE = re.compile(r"^(pending|tbd|todo|open)(?!-)", re.IGNORECASE)


# Fence opener: 3+ backticks or 3+ tildes, optionally followed by an info
# string (CommonMark lets the OPENER carry one, e.g. ```text or ~~~markdown).
_FENCE_OPENER_RE = re.compile(r"^(`{3,}|~{3,})")
# Fence closer: a BARE run of fence characters with only optional trailing
# whitespace — an info string on a closer line means it is fence CONTENT,
# not a closer (CommonMark).
_FENCE_CLOSER_RE = re.compile(r"^(`{3,}|~{3,})[ \t]*$")


def _strip_fences(text: str) -> str:
    """Remove fenced code blocks so quoted template text cannot match.

    Single-active-fence-state parser (r2 F1, r3 F2/F4, r4 F1): honors BOTH
    CommonMark fence syntaxes (backtick ``` and tilde ``~~~``). An OPENER
    is a run of 3+ fence characters (optionally carrying an info string,
    e.g. ```` ```text ````), indented at most 3 spaces — EXCEPT (r5 F8) a
    backtick opener whose info string contains a backtick is paragraph
    content, not an opener (tilde openers keep accepting any info string);
    a line whose leading whitespace contains a tab counts as indent >= 4
    (r5 F8) and can neither open nor close. The opener's
    character and run length are recorded. A CLOSER is a bare run of the
    SAME character, at least as long as the opener, with only optional
    trailing whitespace and at most 3 leading spaces — a closer line
    carrying info text (```` ``` note ````) or a shorter same-character
    run does not close the fence, and a shorter run never closes a longer
    one early in the fail-open direction. While one fence is open, only
    such a closer toggles it, so a stray ``` line inside a tilde block
    cannot desync the parser. An unterminated fence stays open at end of
    input, so everything it swallowed is dropped: fail-closed, never
    fail-open. Applied to the WHOLE document BEFORE section extraction, so
    a fenced ``## `` heading can never truncate a section and a stray
    inline triple backtick can never pair with a later fence opener to
    delete real content.
    """
    stripped, _unclosed = _scan_fences(text)
    return stripped


def _scan_fences(text: str) -> tuple[str, int | None]:
    """Fence scanner core shared by ``_strip_fences`` and the balance probe.

    Returns ``(stripped_text, unclosed_opener_line)``: the stripped text is
    byte-identical to what ``_strip_fences`` has always produced, and
    ``unclosed_opener_line`` is the 1-based source line number of an opener
    that never closed (``None`` when every fence closes). The scanner
    semantics below are the ones ``_strip_fences`` documents; this core
    only adds the opener line bookkeeping.
    """
    out = []
    fence = None  # (fence character, opener run length) when open
    opener_line: int | None = None
    line_no = 0
    # r5 F7: split on "\n" ONLY — splitlines() also splits on CR, VT, FF,
    # and the Unicode separators U+0085/U+2028/U+2029, letting a separator
    # embedded inside a fence-character run fabricate a parser-line closer.
    # Each line is normalized by removing ONE trailing "\r" (CRLF input),
    # and the normalized line is used for BOTH fence matching and emission
    # (a match-only strip would leave the "\r" in the emitted line and
    # falsely reject CRLF plans at ``[ \t]*$`` anchors).
    for raw in text.split("\n"):
        line_no += 1
        line = raw[:-1] if raw.endswith("\r") else raw
        stripped = line.lstrip()
        lead_ws = line[: len(line) - len(stripped)]
        # r5 F8: a leading tab reads as indent >= 4 (CommonMark), so a
        # tab-indented line can never open or close a fence; fail-closed.
        lead = 4 if "\t" in lead_ws else len(lead_ws)
        if fence is None:
            m = _FENCE_OPENER_RE.match(stripped) if lead <= 3 else None
            # r5 F8: a BACKTICK opener whose info string contains a
            # backtick is CommonMark paragraph content, not an opener
            # (tilde openers keep accepting any info string).
            if m and m.group(1)[0] == "`" and "`" in stripped[len(m.group(1)):]:
                m = None
            if m:
                fence = (m.group(1)[0], len(m.group(1)))
                opener_line = line_no
            else:
                out.append(line)
            continue
        m = _FENCE_CLOSER_RE.match(stripped) if lead <= 3 else None
        if (
            m
            and m.group(1)[0] == fence[0]
            and len(m.group(1)) >= fence[1]
        ):
            fence = None
            opener_line = None
        # Any other line is fence content: dropped, not emitted.
    return "\n".join(out), opener_line


def fence_balance_problem(plan_text: str) -> str | None:
    """Reason when the document carries an unclosed fence delimiter line.

    Both readiness entries surface this BEFORE any probe evaluates the
    stripped text: an unterminated fence makes ``_strip_fences`` drop
    everything it swallowed, so probes would silently score only the
    document prefix. The reason names the offending opener's 1-based line
    number (the same scanner the stripper uses, so the two can never
    disagree about balance).
    """
    _stripped, opener_line = _scan_fences(plan_text)
    if opener_line is None:
        return None
    return (
        f"unclosed fence opener at line {opener_line} (no matching "
        f"closer); refusing to evaluate probes over truncated text"
    )


# Residual-section disposition vocabulary (certification machinery
# contract-collisions plan, Task 1): the pinned enum the cap-closure
# matcher parses. A ``disposition: <word>`` label outside the vocabulary,
# or a list entry with no disposition token at all, rejects the entry so
# the matcher is total (never a silent skip).
_CAP_CLOSURE_DISPOSITION_VOCABULARY = frozenset({"folded", "accepted"})
_CAP_CLOSURE_DISPOSITION_LABEL_RE = re.compile(
    r"\bdispositions?\b\s*[:=]?\s*([A-Za-z][A-Za-z_-]*)", re.IGNORECASE
)


def _cap_closure_entry_disposition(entry: str) -> str | None:
    """Parse one residual-section list entry's disposition token.

    Returns ``"accepted"``, ``"folded"``, or ``None`` when the entry
    carries no disposition token or one outside the vocabulary. An
    explicit ``disposition: <word>`` label is authoritative: a word
    outside the vocabulary rejects the entry instead of falling back to a
    bare vocabulary mention elsewhere on the line.
    """
    label = _CAP_CLOSURE_DISPOSITION_LABEL_RE.search(entry)
    if label is not None:
        word = label.group(1).lower()
        return word if word in _CAP_CLOSURE_DISPOSITION_VOCABULARY else None
    for word in ("accepted", "folded"):
        if re.search(rf"\b{word}\b", entry):
            return word
    return None


def cap_closure_terminal_state_problem(
    plan_text: str,
    cap_closure_declaration: object,
    staged_patterns: list[str],
) -> str | None:
    """Reason when the plan's cap-closure terminal state is unsatisfied.

    Consumed by the readiness verdict arm whenever the final sidecar
    declares ``extensions.cap_closure``; ``staged_patterns`` are the
    patterns from that sidecar's ``findings`` array (keeping the
    accounting inside the probe is what lets the verdict arm stay
    ordering-only). Returns ``None`` on a satisfied conjunct, else the
    dedicated named reason.

    Conjuncts, first problem wins:

    (a) the fence-stripped plan text carries the staging validator's
        single-owner section literal (``vrs.CAP_CLOSURE_SECTION_HEADING``,
        the BARE heading; the declaration check compares the
        ``'## ' + `` prefixed form against the same owner) as a
        line-anchored level-2 heading, the Assumptions-trailer precedent
        (``md_section`` composes its matcher from the bare heading): a
        quoted mention, a fenced copy, or a ``###`` heading never
        satisfies it;
    (b) when the declaration's ``residuals`` count is greater than zero,
        the section body (md_section semantics: it stops at the next
        level-2 heading or end of file, and the FIRST conforming heading
        governs, so a non-empty body under any later conforming heading
        never rescues an empty first section) contains at least one
        non-blank line;
    (c) every staged pattern appears in the section body WITH a
        ``folded``/``accepted`` disposition on the same list entry as its
        pattern (never scanned section-wide); under-reporting the round's
        staged findings returns the dedicated named reason;
    (d) the declared ``residuals`` count equals the number of distinct
        section-body entries carrying the ``accepted`` disposition.
    """
    heading = vrs.CAP_CLOSURE_SECTION_HEADING
    stripped = _strip_fences(plan_text)
    heading_present = re.search(
        rf"^## {re.escape(heading)}\s*$", stripped, re.MULTILINE
    )
    if not heading_present:
        return (
            "cap closure terminal state missing: the plan carries no "
            f"line-anchored '## {heading}' section (a quoted mention, a "
            "fenced copy, or a '###' heading never satisfies it)"
        )
    section = md_section(stripped, heading)
    raw_residuals = (
        cap_closure_declaration.get("residuals")
        if isinstance(cap_closure_declaration, dict)
        else 0
    )
    residuals = (
        raw_residuals
        if isinstance(raw_residuals, int) and not isinstance(raw_residuals, bool)
        else 0
    )
    entries = [line.strip() for line in section.splitlines() if line.strip()]
    if residuals > 0 and not entries:
        return (
            "cap closure terminal state missing or empty: the "
            f"'## {heading}' section body is missing or empty while the "
            f"declaration claims {residuals} residual(s)"
        )
    under_reported = [
        pattern
        for pattern in staged_patterns
        if not any(
            pattern in entry
            and _cap_closure_entry_disposition(entry) is not None
            for entry in entries
        )
    ]
    if under_reported:
        return (
            "cap closure terminal state under-reports the round's staged "
            f"findings: no '## {heading}' body entry carries a folded or "
            f"accepted disposition for {under_reported!r}"
        )
    accepted_tally = sum(
        1
        for entry in entries
        if _cap_closure_entry_disposition(entry) == "accepted"
    )
    if accepted_tally != residuals:
        return (
            "cap closure residuals count mismatch: the declaration claims "
            f"{residuals} accepted residual(s) but the '## {heading}' "
            f"section body carries {accepted_tally}"
        )
    return None


def decision_marker_problem(plan_text: str) -> str | None:
    """Reason when the decision-points trailer is missing or unresolved.

    The author-facing statement of trailer acceptance mechanics lives in
    the plans skill plan-template Assumptions line
    (agents/skills/plans/SKILL.md); this probe owns enforcement — link
    there, do not restate the mechanics.

    ``None`` when the single trailer line inside the ``## Assumptions``
    section reads ``none remain.`` (case-insensitive, trailing period
    optional) or carries a non-placeholder receipt; a named reason
    otherwise. Placeholder-prefixed segments (starting with the words
    ``pending``, ``tbd``, ``todo``, or ``open``, or a ``<`` template
    token) are unresolved. The stem and template-token checks apply PER
    RECEIPT SEGMENT: the trailer value is split on ``;`` and each
    stripped segment's start is tested (segment start = value start or
    the start after any ``;``), so a mixed mid-interview trailer — closed
    receipts plus one newly ``open:`` question — fails even though its
    value start is a resolved receipt. Fenced code blocks are stripped
    from the WHOLE document FIRST, then the ``## Assumptions`` section is
    extracted from the stripped text (so a fenced heading cannot truncate
    the section); an unterminated fence fails closed by dropping
    everything it swallowed. More than one trailer line is ambiguous and
    is rejected on its own reason (r4 F1: last-wins would let an
    unresolved line hide under a terminal none-remain line).
    """
    values = DECISION_MARKER_RE.findall(
        md_section(_strip_fences(plan_text), "Assumptions")
    )
    if not values:
        return "missing decision-points trailer"
    if len(values) > 1:
        return f"ambiguous decision-points trailer: {len(values)} lines"
    value = values[0]
    if value.lower() in {"none remain.", "none remain"}:
        return None
    for segment in value.split(";"):
        start = segment.lstrip()
        if start.startswith("<") or _PLACEHOLDER_RE.match(start):
            return f"unresolved decision-points trailer: {value!r}"
    return None


# Category-block label inside the ## Review Scope section: a bolded
# ``**<label>:**`` line opens a block with or without same-line guidance
# prose after the label (the plans skill Review Scope template's own
# Documentation label carries prose); subsequent ``- `` items belong to
# it. A label containing ``Out of scope`` is prose, not a category
# block. Label handling (strip, out-of-scope exclusion) is unchanged and
# uses ``group(1)`` only; the same-line guidance prose after the label
# is matched but not captured (r1 F12a).
_REVIEW_SCOPE_CATEGORY_RE = re.compile(r"^\*\*(.+?):\*\*[ \t]*(?:.*)$")
# A test-detectable path: any path SEGMENT named test/tests/spec.
_REVIEW_SCOPE_TEST_SEGMENTS = ("test", "tests", "spec")


def _review_scope_is_doc_path(path: str) -> bool:
    """True when the path carries a documentation-format suffix.

    A doc-suffix path is never test-detectable (F4: ``docs/spec/
    architecture.md`` is documentation that lives under a spec dir, not a
    test) and is authoritative under a Documentation label (the spec-dir
    arm exercises this branch). Config-suffixed paths such as
    ``site.yaml`` are NOT doc-suffix paths: they pass a Documentation
    label only because config extensions are absent from the
    implementation table (r1 F3), a separate mechanism.
    """
    return path.lower().endswith(REVIEW_SCOPE_DOC_SUFFIXES)


def _review_scope_is_test_path(path: str) -> bool:
    """True when any path segment is test/tests/spec (doc-suffix paths
    are never test-detectable)."""
    if _review_scope_is_doc_path(path):
        return False
    return any(
        segment in _REVIEW_SCOPE_TEST_SEGMENTS
        for segment in re.split(r"[\\/]+", path.lower())
    )


def _review_scope_path_token(item: str) -> str:
    """Leading path token of a list item, dropping trailing annotations.

    List items in Review Scope category blocks and task ``Files:`` lists
    carry trailing annotations (``- ``src/service.py`` *(new; this
    plan)*``); comparisons must see the bare path. The backticked span
    wins ONLY when it is the item's leading content (one anchored match,
    ``re.match(r"\\s*`+([^`]+)`+", item)``, r1 F12d; a backtick-run opener
    of any length is accepted, behaviorally equivalent to the pattern); any backticked span
    that is not leading content is prose, and extraction falls through to
    the first whitespace-delimited token after backtick stripping (F2:
    annotation-blind parsing made the category, duplicate, and inventory
    checks silently inoperative for the template's annotated common
    case; the earlier unconditional first-span rule let a mid-prose span
    such as ``- see `docs/a.md` and also `docs/b.md``` win as a false
    path). Inside the winning leading span, a trailing parenthesized
    annotation is stripped (``re.sub(r"\\s*\\([^()]*\\)\\s*$", "",
    span).strip()``; r3 F2: ``- ``src/service.py (new; this plan)````
    extracts as bare ``src/service.py``). Separators are normalized at a
    single shared exit for BOTH branches (``token.replace("\\\\", "/")``;
    r3 overflow: Windows-style backslash paths must compare equal to
    their slash forms in every downstream check), and a single leading
    ``./`` is stripped (r2 F5: ``./src/a.py`` in scope and ``src/a.py``
    in Files must not fail coverage on notation drift).
    """
    def _strip_dot_slash(token: str) -> str:
        return token[2:] if token.startswith("./") else token

    lead = re.match(r"\s*`+([^`]+)`+", item)
    if lead:
        # Leading-span rule: a backticked span (single or doubled backtick
        # fence, r2 risk follow-up) is the item's leading content and wins;
        # a trailing parenthesized annotation inside the span is stripped
        # (r3 F2). The strip applies ONLY here, to the winning span.
        token = re.sub(r"\s*\([^()]*\)\s*$", "", lead.group(1)).strip()
    else:
        if not item.strip():
            return ""
        token = item.strip().strip("`").strip().split()[0]
    return _strip_dot_slash(token.replace("\\", "/"))


def _review_scope_task_files(stripped: str) -> list[str]:
    """Every ``Files:`` list-item path from ``###``/``####`` Task and
    Step sections.

    Wrapper over ``_plan_task_sections`` plus ``_plan_files_items``, the
    one parser implementation, so review-scope clause (c) and the
    ownership check inventory the same Files lists. The collection
    rules (exact ``Files:`` opener, empty-payload re-open, checkbox
    close, indented entries, path-shaped tokens only, leading-token
    normalization) live in ``_plan_files_items``; this wrapper only
    flattens the per-section items to the path sequence in document
    order.
    """
    return [
        token
        for _, body in _plan_task_sections(stripped)
        for token, _ in _plan_files_items(body)
    ]


def review_scope_problem(plan_text: str) -> str | None:
    """Reason when the ``## Review Scope`` section miscategorizes paths.

    Fences are stripped from the WHOLE document first (same ordering as
    the trailer gate); an absent ``## Review Scope`` section yields
    ``None`` (fail-open on shape absence is deliberate: the section is
    plan-authoring convention, not a hard schema). Checks, first problem
    wins:

    (a) an implementation-suffix or test-detectable path listed under a
        label matching ``documentation`` (case-insensitive) — a
        doc-suffix path (REVIEW_SCOPE_DOC_SUFFIXES) is authoritative
        under Documentation and never flagged here; the reason names the
        path, the declared category, and the expected category
        (``Tests`` for test-detectable, ``Production code`` otherwise);
    (b) a path listed under two different category blocks;
    (c) a ``Files:`` list path from a ``###``/``####`` Task and Step
        section that appears
        nowhere in the Review Scope section text (category list,
        plan-related-extension prose, or out-of-scope list). Items in
        both surfaces are normalized to their leading path token before
        any comparison (trailing annotations are not part of the path).
    """
    stripped = _strip_fences(plan_text)
    scope = md_section(stripped, "Review Scope")
    if not scope:
        return None

    # Parse category blocks in document order.
    blocks: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in scope.splitlines():
        label_match = _REVIEW_SCOPE_CATEGORY_RE.match(line)
        if label_match:
            label = label_match.group(1).strip()
            # The hyphenated spelling "out-of-scope" must match too
            # (r2 F6: normalize hyphens to spaces before the test).
            current = (
                None
                if "out of scope" in label.lower().replace("-", " ")
                else (label, [])
            )
            if current is not None:
                blocks.append(current)
            continue
        item_match = re.match(r"^-\s+(.+?)\s*$", line)
        if item_match and current is not None:
            token = _review_scope_path_token(item_match.group(1))
            if token:
                current[1].append(token)

    # (a) path kind vs declared category. A doc-suffix path (the
    # REVIEW_SCOPE_DOC_SUFFIXES table) is AUTHORITATIVE under a
    # Documentation label (spec-directory docs like
    # docs/spec/architecture.md exercise this branch). Docs-pipeline
    # config (site.yaml) passes a Documentation label only because
    # config extensions are absent from the implementation-suffix table
    # (r1 F3), not because .yaml is a doc suffix.
    for label, items in blocks:
        if "documentation" not in label.lower():
            continue
        for path in items:
            if _review_scope_is_doc_path(path):
                continue
            if _review_scope_is_test_path(path):
                return (
                    f"Review Scope lists {path} under declared category "
                    f"{label!r}; path kind suggests 'Tests'"
                )
            if path.lower().endswith(REVIEW_SCOPE_IMPLEMENTATION_SUFFIXES):
                return (
                    f"Review Scope lists {path} under declared category "
                    f"{label!r}; path kind suggests 'Production code'"
                )

    # (b) one path under two different category blocks.
    label_of: dict[str, str] = {}
    for label, items in blocks:
        for path in items:
            previous = label_of.get(path)
            if previous is not None and previous != label:
                return (
                    f"duplicate path across Review Scope categories: "
                    f"{path} listed under both {previous!r} and {label!r}"
                )
            label_of[path] = label

    # (c) task Files: paths must appear in the inventory: either as an
    # extracted scope-path token (category items, normalized the same
    # way), as a DIRECTORY scope entry covering it (r2 F4: a token that
    # ends with ``/`` with the task path under it, or a token whose
    # ``token + "/"`` form is a component-boundary prefix of the task
    # path — trailing slashes are normalized inside the comparison
    # (r3 F1), and the boundary keeps the F8 superstring case failing:
    # ``scripts/foo.py`` does not cover ``scripts/foo.py.bak``), or as a
    # path-boundary occurrence in any line of the section text
    # (plan-related-extension prose and out-of-scope lists keep
    # counting; F8: a raw substring test let ``scripts/foo.py`` pass on a
    # longer different path like ``scripts/foo.py.bak``).
    scope_paths = {path for _, items in blocks for path in items}

    def _scope_token_covers(token: str, path: str) -> bool:
        # Trailing-slash notation drift (r3 F1): scope ``docs/`` must
        # cover task ``docs`` and scope ``docs`` must cover task
        # ``docs/``; normalize the slash on the token side only, inside
        # this component-boundary comparison. The ``token + "/"``
        # boundary keeps the F8 superstring case failing
        # (``scripts/foo.py`` does not cover ``scripts/foo.py.bak``).
        dir_token = token.rstrip("/")
        if not dir_token:
            return False
        if path == dir_token:
            return True
        return path.startswith(dir_token + "/")

    for path in _review_scope_task_files(stripped):
        if path in scope_paths:
            continue
        if any(_scope_token_covers(token, path) for token in scope_paths):
            continue
        boundary = re.compile(
            rf"(?<![\w./\\-]){re.escape(path)}(?![\w./\\-])"
        )
        if any(boundary.search(line) for line in scope.splitlines()):
            continue
        return (
            f"task Files path {path} is omitted from the Review Scope "
            f"inventory"
        )
    return None


# ``*(new)*`` is the plans template's new-file record, the planned-new marker:
# an annotation (optionally with elaboration, e.g. ``*(new; this plan)*``) on
# a task ``Files:`` item marks the task that CREATES the file. It is the
# single creation record the ownership checks below read; a Files listing
# without it is a shared or sequential edit and never claims creation.
_PLAN_NEW_FILE_ANNOTATION_RE = re.compile(r"\*\(\s*new\b[^()]*\)\*")


def _plan_path_shaped(token: str) -> bool:
    """Path-shaped token, same rule as the task Files collector: a
    separator or a doc/implementation suffix."""
    return (
        "/" in token
        or token.lower().endswith(
            REVIEW_SCOPE_DOC_SUFFIXES + REVIEW_SCOPE_IMPLEMENTATION_SUFFIXES
        )
    )


def _plan_task_sections(stripped: str) -> list[tuple[str, str]]:
    """``(heading title, body)`` for each ``###``/``####`` Task/Step
    section, the one owner of the section-boundary rule (a section ends
    at the next heading of level ## through ####)."""
    sections: list[tuple[str, str]] = []
    for match in re.finditer(
        r"^#{3,4} (?:Task|Step).*$", stripped, re.MULTILINE
    ):
        title = match.group(0).lstrip("#").strip()
        body = re.split(r"\n#{2,4} ", stripped[match.end():], maxsplit=1)[0]
        sections.append((title, body))
    return sections


def _plan_task_ordinal(title: str) -> int | None:
    """Numeric task ordinal from a Task/Step heading title, else None."""
    match = re.search(r"\b(?:Task|Step)\s+(\d+)", title, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _plan_task_label(title: str) -> str:
    """Reason-facing task name: the ordinal when present, else the
    verbatim heading title."""
    ordinal = _plan_task_ordinal(title)
    return f"Task {ordinal}" if ordinal is not None else f"task section {title!r}"


def _plan_files_items(body: str) -> list[tuple[str, bool]]:
    """``(path token, carries the planned-new marker)`` for a task
    section's ``Files:`` block, the one owner of the collection rules
    (``_review_scope_task_files`` is a wrapper over this parser plus
    ``_plan_task_sections``) aligned to the one documented declaration
    grammar:
    only the exact ``Files:`` heading opens collection (case variants are
    named refusals via ``_plan_declaration_shape_problem``), an
    empty-payload ``Files:`` line (re)opens collection, a payload-bearing
    line closes it, the first checkbox item closes it, an indented item is
    an entry like any other (the former nested-annotation skip is
    stopped), and only path-shaped tokens are collected."""
    items: list[tuple[str, bool]] = []
    collecting = False
    for line in body.splitlines():
        opener = re.match(r"Files:(.*)$", line)
        if opener:
            collecting = not opener.group(1).strip()
            continue
        if not collecting:
            continue
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith("- ["):
            collecting = False
            continue
        if stripped_line.startswith("- "):
            token = _review_scope_path_token(stripped_line[2:])
            if token and _plan_path_shaped(token):
                items.append(
                    (
                        token,
                        bool(
                            _PLAN_NEW_FILE_ANNOTATION_RE.search(stripped_line)
                        ),
                    )
                )
        else:
            collecting = False
    return items


# The one declaration contract's named decisions, verbatim the runtime
# parser's problem strings (execute_plan_runtime.py ``_plan_declared_files``
# class constants) so both surfaces emit the same problem family for the
# same shape. Change them together.
_FILES_DUPLICATE_PROBLEM = (
    "duplicate Files: heading in one task section: the documented grammar accepts exactly one exact 'Files:' declaration per task section"
)
_FILES_INDENTED_PROBLEM = (
    "missing Files: declaration: an indented 'Files:' line is not a block opener under the documented grammar"
)
_FILES_CASE_VARIANT_PROBLEM = (
    "declaration opener '{opener}' is a case variant: the documented grammar accepts the exact 'Files:' heading only"
)


def _plan_declaration_shape_problem(body: str) -> str | None:
    """The named declaration-shape refusal for one task section body, the
    authoring-side producer of the same problem family the runtime parser
    emits: a second exact ``Files:`` heading in the section (the duplicate
    declaration, refused instead of union-collected), a section whose only
    opener is an indented ``Files:`` line (never a block opener), or a
    case-variant opener (``files:``/``FILES:``; the documented grammar
    accepts the exact ``Files:`` heading only). A path-shaped bullet above
    the heading is inert prose on both surfaces. ``None`` when the section
    carries no divergent shape."""
    lines = body.splitlines()
    exact_openers = [line for line in lines if line == "Files:"]
    if len(exact_openers) > 1:
        return _FILES_DUPLICATE_PROBLEM
    if not exact_openers:
        for line in lines:
            stripped = line.strip()
            if stripped.lower() != "files:":
                continue
            if line != stripped:
                return _FILES_INDENTED_PROBLEM
            return _FILES_CASE_VARIANT_PROBLEM.format(opener=stripped)
    return None


def _plan_checklist_items(body: str) -> list[str]:
    """Checkbox item lines (``- [ ...``) of a task section, stripped."""
    return [
        line.strip()
        for line in body.splitlines()
        if line.strip().startswith("- [")
    ]


def _plan_item_path_tokens(item: str) -> list[str]:
    """Path-shaped tokens referenced by a checklist item.

    Backticked spans are extracted first (a backticked span is the
    plan's quoting convention for paths); plain tokens from the prose
    outside spans follow. Each candidate is normalized through
    ``_review_scope_path_token`` and must be path-shaped; anything else
    (a test-method token, a commit-message span, a class tag) carries no
    creation marker and is never ordered.
    """
    tokens: list[str] = []

    def _collect(candidate: str) -> None:
        token = _review_scope_path_token(candidate)
        if token and _plan_path_shaped(token) and token not in tokens:
            tokens.append(token)

    for span in re.findall(r"`([^`]+)`", item):
        _collect(f"`{span}`")
    outside = re.sub(r"`[^`]*`", " ", item)
    for raw in outside.split():
        _collect(raw)
    return tokens


# Scheme exclusion for the Files:-coverage arm: a URI-scheme token
# (``https://example.com/a.md``) is a web address, not a repository path,
# even though its slashes make it path-shaped under ``_plan_path_shaped``.
# The comparison below never reports scheme-bearing tokens as ``Files:``
# omissions.
_PLAN_URL_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")


def _plan_acceptance_path_token(span: str) -> str | None:
    """Normalized path token for one backticked acceptance-item span, or
    ``None`` when the span is out of scope.

    The span is normalized through ``_review_scope_path_token`` (the
    module's shared token normalization, applied exactly as
    ``_plan_item_path_tokens`` applies it to a backticked span) and must
    pass ``_plan_path_shaped`` verbatim plus the scheme exclusion: a
    scheme-bearing token is not a repository path.
    """
    token = _review_scope_path_token(f"`{span}`")
    if not token or not _plan_path_shaped(token):
        return None
    if _PLAN_URL_SCHEME_RE.match(token):
        return None
    return token


def plan_files_coverage_warnings(plan_text: str) -> list[str]:
    """Warning-only Files:-coverage arm (machinery registry row
    ``script:plan-files-coverage-arm``): one line per acceptance-item path
    token missing from task ``Files:`` lists.

    The shared check surface both gate paths call: the pre-round gate
    (``run_pre_round``) prints the lines on stderr after all probes pass,
    mirroring the execution-budget warning precedent, and the full gate's
    main path prints them on stderr as human-readable evidence before its
    summary and OUTCOME lines, on its pass path only. The arm never
    changes an exit code, adds no schema field, and refuses nothing;
    every failure path prints zero lines (the callers own that contract;
    here the arm is a pure function of the plan text).

    Token source, pinned so no parallel grammar grows: the acceptance side
    reads backticked spans from the task's acceptance (checkbox) items
    only, with the same span anchoring the module's composite
    checklist-item collector ``_plan_item_path_tokens``; that collector's
    plain-prose tokens are deliberately out of scope here because they
    would exceed the priced false-positive cost (one adjudicated warning
    line per omission). Each span is normalized through
    ``_review_scope_path_token`` and must be path-shaped
    (``_plan_path_shaped``) and scheme-free. The comparison set is the
    ``Files:`` items the module already collects (``_plan_files_items``),
    with per-task attribution: a token present in its own task's
    ``Files:`` list is conforming and silent; a token absent from its own
    task but declared by a sibling task emits the softened sibling
    variant naming the sibling; the loud variant naming the task, the
    path, and the quoting item fires only for tokens declared nowhere.
    A token quoted by several items of one task is reported once, by its
    first quoting item.

    Known limitation: an acceptance item that mentions another task's
    path for context produces a warning the author adjudicates; the
    warning posture keeps that cost at one read.
    """
    warnings: list[str] = []
    stripped = _strip_fences(plan_text)
    sections = _plan_task_sections(stripped)
    if not sections:
        return warnings
    # Per-task Files: sets plus the token -> first-declaring-task map the
    # sibling attribution reads.
    per_task: list[tuple[str, set[str]]] = [
        (
            _plan_task_label(title),
            {token for token, _ in _plan_files_items(body)},
        )
        for title, body in sections
    ]
    declarer_of: dict[str, str] = {}
    for label, tokens in per_task:
        for token in sorted(tokens):
            declarer_of.setdefault(token, label)
    for (label, own_files), (_, body) in zip(per_task, sections):
        reported: set[str] = set()
        for item in _plan_checklist_items(body):
            for span in re.findall(r"`([^`]+)`", item):
                token = _plan_acceptance_path_token(span)
                if token is None or token in reported:
                    continue
                reported.add(token)
                if token in own_files:
                    continue
                declarer = declarer_of.get(token)
                if declarer is not None:
                    warnings.append(
                        f"readiness FILES-COVERAGE WARNING: {label} "
                        f"acceptance item quotes `{token}`, already "
                        f"declared by {declarer}'s Files: list "
                        f"(sibling-declared; adjudicate whether this "
                        f"task must declare it too)"
                    )
                else:
                    warnings.append(
                        f"readiness FILES-COVERAGE WARNING: {label} "
                        f"acceptance item quotes `{token}` but no task's "
                        f"Files: list declares it (Files:-coverage "
                        f"contract; quoting item: {item})"
                    )
    return warnings


def plan_ownership_problem(plan_text: str, repo_root: Path) -> str | None:
    """Reason when the plan's task ownership structure is inconsistent.

    Fences are stripped from the WHOLE document first (same ordering as
    the trailer and Review Scope gates); task sections are the
    ``###``/``####`` headings starting with ``Task`` or ``Step``. Checks,
    first problem wins:

    (0) a task section whose ``Files:`` declaration carries a divergent
        shape under the one documented declaration grammar: a second
        exact ``Files:`` heading (the duplicate declaration, refused
        instead of union-collected), an indented ``Files:`` line as the
        section's only opener (never a block opener), or a case-variant
        opener (the documented exact-``Files:``-only rule). The reason is
        the same named problem family the runtime parser emits, prefixed
        by the task label; ``_plan_declaration_shape_problem`` owns the
        decisions;
    (a) ``duplicate creating task`` - a ``Files:`` path annotated with
        the planned-new marker in more than one task section's
        ``Files:`` list; task identity is the section's document
        position, not the ``Task {ordinal}`` label, so two distinct
        sections sharing an ordinal stay distinct owners; the reason
        names the path and both tasks. Shared listings without the
        annotation are sequential edits of one file and never trip;
    (b) ``consumer-before-owner`` - a task checklist item references a
        file path whose creating task (the task carrying the planned-new
        marker for it in its ``Files:`` list) is a later task; sections
        order by document position, so an ordinal-less section still
        orders; the reason names the referencing task, the path, and the
        creating task. Referencing an already-created witness in a later
        task passes;
        test-method tokens are not ordered by this static check (they
        carry no creation marker): their ownership ordering is an
        authoring-time duty of the ownership ledger and a review-agent
        classification duty, not a static one;
    (c) a ``Files:`` path that does not exist under ``repo_root`` and
        carries no planned-new marker; the reason names the task and the
        path. Checklist-only references to nonexistent paths stay an
        authoring and review duty and are not checked here;
    (d) more than one section heading denoting a transition table
        (``state transition`` or ``transition table`` in the heading);
        the reason names the first two headings and the total count.
    """
    stripped = _strip_fences(plan_text)
    sections = [
        (_plan_task_label(title), body) for title, body in _plan_task_sections(stripped)
    ]

    # (0) declaration-shape parity with the runtime parser: each divergent
    # shape refuses through the same named problem family the runtime
    # emits, in document order, before any ownership evaluation reads the
    # collected items.
    for label, body in sections:
        shape_problem = _plan_declaration_shape_problem(body)
        if shape_problem is not None:
            return f"{label}: {shape_problem}"

    # (a) one creating task per new file: the first annotated listing
    # owns the path; a second annotated listing in a DIFFERENT section
    # is the duplicate-creation contradiction. Section identity is the
    # section's document position, not the Task-ordinal label, so two
    # distinct sections sharing an ordinal stay distinct owners.
    owners: dict[str, tuple[int, str]] = {}
    for index, (label, body) in enumerate(sections):
        for token, is_new in _plan_files_items(body):
            if not is_new:
                continue
            previous = owners.get(token)
            if previous is not None and previous[0] != index:
                return (
                    f"duplicate creating task for {token}: annotated "
                    f"*(new)* in both {previous[1]} and {label}"
                )
            owners.setdefault(token, (index, label))

    # (b) consumer-before-owner: a checklist item referencing a path
    # whose creating section is a LATER section. Sections order by
    # document position (an ordinal-less section still orders), unowned
    # paths never trip (no creation record to order against), and an
    # owner at or before the referencing section is the legitimate
    # reference-after-owner shape.
    for index, (label, body) in enumerate(sections):
        for item in _plan_checklist_items(body):
            for token in _plan_item_path_tokens(item):
                owner = owners.get(token)
                if owner is None or owner[0] <= index:
                    continue
                return (
                    f"consumer-before-owner: {label} checklist references "
                    f"{token} but its creating task is {owner[1]} (the "
                    f"*(new)* record there)"
                )

    # (c) a Files: path must exist under the repo root unless it carries
    # the planned-new marker (a creation record for a file this plan
    # creates).
    for label, body in sections:
        for token, is_new in _plan_files_items(body):
            if is_new or (repo_root / token).exists():
                continue
            return (
                f"Files: path {token} in {label} does not exist under "
                f"{repo_root} and carries no *(new)* annotation"
            )

    # (d) at most one section heading may denote a transition table.
    transition_headings = [
        match.group(1).strip()
        for match in re.finditer(
            r"^#{1,6}\s+(.+?)\s*$", stripped, re.MULTILINE
        )
        if re.search(
            r"state transition|transition table",
            match.group(1),
            re.IGNORECASE,
        )
    ]
    if len(transition_headings) > 1:
        return (
            f"more than one transition-table section: "
            f"{transition_headings[0]!r} and {transition_headings[1]!r} "
            f"({len(transition_headings)} headings denote a transition "
            f"table)"
        )
    return None


# Classification tag on a task checklist item: ``[class: NAME]``. The
# tag prefix is matched case-sensitively (the plans skill authors the
# lowercase literal shape), the captured value is compared exactly.
_CLASSIFICATION_TAG_RE = re.compile(r"\[class:[ \t]*([^\]]*?)[ \t]*\]")

# The four-name classification vocabulary. The first two names ride on
# task checklist items; the last two are the Ship-when-only classes
# below. The plans skill's Checklist inclusion gate owns the authoring
# rule and the taxonomy mapping; this table is the enforcement-side
# single owner of the membership set.
CLASSIFICATION_VOCABULARY = (
    "IMPLEMENTATION_REQUIRED",
    "REPOSITORY_TEST",
    "EXTERNAL_RELEASE_GATE",
    "OPERATIONS_FOLLOW_UP",
)

# Classes that refine the release-condition and external-prerequisite
# classification and are therefore written in the Ship when prose, never
# on an executable task checklist item.
SHIP_WHEN_ONLY_CLASSES = ("EXTERNAL_RELEASE_GATE", "OPERATIONS_FOLLOW_UP")


def scope_classification_problem(plan_text: str) -> str | None:
    """Reason when a task checklist item violates the classification-tag
    rule.

    The author-facing statement of the rule lives in the plans skill's
    Checklist inclusion gate (agents/skills/plans/SKILL.md); this probe
    owns enforcement - link there, do not restate the taxonomy. Fences
    are stripped from the WHOLE document first (same ordering as the
    trailer, Review Scope, and plan-ownership gates); task sections are
    the ``###``/``####`` headings starting with ``Task`` or ``Step``
    (shared parser ``_plan_task_sections``); Ship when prose and every
    non-task section are exempt (only task checklist items are read).
    Checks, first problem in document order wins (the placement check runs
    first within each task section; see the (placement) entry):

    (placement) scanned per task section BEFORE the per-item loop: a
        non-blank line that is not a checkbox item and carries a
        ``[class: ...]`` token outside backtick spans - the tag sits on
        a wrapped item's continuation line, where the per-item parser
        (which reads checkbox-marker lines only) cannot see it. This
        check runs first within each section because it explains why
        the item reads untagged: without it the probe would return the
        misleading untagged reason (a) for the marker line instead of
        naming the placement.
    (a) a checklist item with no ``[class: ...]`` tag at all - every task
        checklist item must carry ``[class: IMPLEMENTATION_REQUIRED]``
        or ``[class: REPOSITORY_TEST]``; the reason names the task and
        quotes the item;
    (b) an item tagged ``[class: EXTERNAL_RELEASE_GATE]`` or
        ``[class: OPERATIONS_FOLLOW_UP]`` - those classes refine the
        release-condition and external-prerequisite classification and
        belong in the Ship when prose with their evidence owner and
        closure condition, never on an executable item;
    (c) a tag value outside the four-name vocabulary
        (``CLASSIFICATION_VOCABULARY``). Every tag on an item is
        checked, so a junk second tag cannot hide behind a valid first
        one; an empty or whitespace-only tag value is a (c) violation,
        not a missing tag.

    Backticked spans are QUOTES, not declarations (the plan corpus
    quotes the tag syntax itself, e.g. `` `[class: ...]` ``, inside
    task-item prose): tags are matched on the text outside backtick
    spans only, the same span-then-prose split
    (``re.sub(r"`` `[^`]*` ``", " ", item)``) as
    ``_plan_item_path_tokens``. An item whose only tag sits inside a
    backticked span stays untagged (a) - fail-closed.
    """
    stripped = _strip_fences(plan_text)
    for title, body in _plan_task_sections(stripped):
        label = _plan_task_label(title)
        # Placement check (runs before the per-item loop): a tag on a
        # non-checkbox line is a wrapped item's continuation line, and
        # it explains why the item reads untagged below.
        for line in body.splitlines():
            if not line.strip() or line.strip().startswith("- ["):
                continue
            if _CLASSIFICATION_TAG_RE.findall(re.sub(r"`[^`]*`", " ", line)):
                return (
                    f"classification tag on a non-checkbox line in "
                    f"{label}; tags must sit on the item's first "
                    f"(checkbox-marker) line: {line!r}"
                )
        for item in _plan_checklist_items(body):
            tags = _CLASSIFICATION_TAG_RE.findall(re.sub(r"`[^`]*`", " ", item))
            if not tags:
                return (
                    f"task checklist item in {label} carries no "
                    f"[class: ...] classification tag: {item!r}"
                )
            for value in tags:
                if value not in CLASSIFICATION_VOCABULARY:
                    return (
                        f"classification tag [class: {value}] in {label} "
                        f"is outside the four-name vocabulary "
                        f"({', '.join(CLASSIFICATION_VOCABULARY)})"
                    )
                if value in SHIP_WHEN_ONLY_CLASSES:
                    return (
                        f"task checklist item in {label} carries "
                        f"[class: {value}]; external-gate and operations "
                        f"requirements belong in the Ship when prose"
                    )
    return None


def digest_failure_reason(first_error: str, round_no: int) -> str:
    """Classify a shared-gate ``source_digest`` error into a distinct reason.

    ``stale`` is reserved for a digest MISMATCH only (the plan bytes changed
    after the review round). A missing digest or a non-hex placeholder is
    ``invalid or missing``. An unrecognized digest error gets a fallback
    wording that embeds the raw error verbatim, so a silent classification
    collapse (unknown shared-validator wording mapping to the wrong family)
    stays detectable from the printed reason.
    """
    if "is stale" in first_error:
        return (
            f"sidecar source_digest is stale (plan bytes changed after "
            f"review r{round_no}): {first_error}"
        )
    if (
        "missing source_digest" in first_error
        or "must be a lowercase" in first_error
    ):
        return (
            f"sidecar source_digest is invalid or missing (round "
            f"r{round_no}): {first_error}"
        )
    return (
        f"sidecar source_digest failed an unrecognized check (round "
        f"r{round_no}); raw error: {first_error}"
    )


# Shared gated-probe date guards (single owners): a round gates a probe only
# when its sidecar date is exactly YYYY-MM-DD (a missing/blank/malformed date
# is exempt, r4 F4) and sorts at or after the gate's minimum date, and all
# gated probes report failures through the one reason format below.
def _gate_fires(round_date: str, min_date: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", round_date)) and round_date >= min_date


def _gated_probe_reason(problem: str, min_date: str, round_no: int, round_date: str) -> str:
    return f"{problem} (required for plans reviewed on or after {min_date}; latest round r{round_no} is dated {round_date})"


# The graded-gate indeterminate prefix (review-cert-graded-binding plan,
# Task 6): the shared gate's indeterminate evidence (an unresolvable seal
# anchor or a git plumbing failure over resolved inputs on the
# corrections-graded arms) is a fail-closed readiness refusal, and this
# prefix marks the reason so main() classifies it as the indeterminate
# outcome (exit 2) instead of a findings-class fail.
_GATE_INDETERMINATE_PREFIX = "readiness indeterminate: "


def _plan_corrections_context(
    plan_path: Path, plan_bytes: bytes
) -> dict | None:
    """The correction context for the shared gate's graded stale arm
    (review-cert-graded-binding plan, Task 6): the plan's repository root
    resolved from the plan's own directory, the plan path relative to that
    root (the artifact identity the certification seal names), and the
    current bytes. ``None`` when the plan does not resolve inside a git
    working tree: the graded arm never arms and the legacy exact-match
    digest rule applies unchanged."""
    try:
        proc = subprocess.run(
            [
                "git", "-C", str(plan_path.parent),
                "rev-parse", "--show-toplevel",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    root = Path(proc.stdout.strip()).resolve()
    try:
        artifact_rel = plan_path.relative_to(root).as_posix()
    except ValueError:
        return None
    return {
        "family": "plan",
        "repo": str(root),
        "artifact_path": artifact_rel,
        "current_bytes": plan_bytes,
        # The seal slug: the artifact filename stem carries the plan's date
        # prefix, so the sidecar's artifact_slug fallback alone would
        # resolve the seal at the wrong name whenever the two differ. The
        # canonical artifact slug (the feature slug lowercased) is the one
        # machine identity; the story key stays preserved in prose.
        "slug": artifact_slug(plan_path),
    }


def _first_gate_error_reason(
    first_error: str, payload: dict, round_no: int
) -> str:
    """Map the shared gate's FIRST error to the readiness reason.

    Routing home (review-cert-graded-binding plan, Task 6): a
    ``corrections verification:``-prefixed error is the corrections family
    and routes DIRECTLY, as the first dispatch test, before the coverage,
    source_kind, and source_digest substring branches and the final schema
    wrap. The marker constant is corrections_record's exported
    ``MARKER_PREFIX``, so a verifier leg can never be misfiled into a
    substring family its wording happens to touch; production verifier
    reasons carry no banned routing literal (pinned in
    corrections_record's MarkerConstantsTest). ``digest_failure_reason``
    keeps its three families unchanged below."""
    if corrections_record is not None and first_error.startswith(
        corrections_record.MARKER_PREFIX
    ):
        return first_error
    if "missing the required 'coverage' object" in first_error:
        # The coverage-presence error names source_kind in its text;
        # map it to its own reason instead of the source_kind family.
        return (
            f"malformed stats sidecar (schema validation failed) for "
            f"round r{round_no}: {first_error}"
        )
    if "source_kind" in first_error:
        declared = payload.get("source_kind")
        return (
            f"sidecar source_kind is {declared!r}, expected 'plan' "
            f"(round r{round_no})"
        )
    if "source_digest" in first_error:
        return digest_failure_reason(first_error, round_no)
    return (
        f"malformed stats sidecar (schema validation failed) for round "
        f"r{round_no}: {first_error}"
    )


def evaluate_readiness(
    plan_path: Path, plans_dir: Path, reviews_dir: Path
) -> tuple[bool, str | None]:
    """Evaluate the readiness conditions in order.

    Returns ``(ok, reason)``; ``reason`` names the FIRST failed condition only
    and is ``None`` on success.
    """
    plans_dir = plans_dir.expanduser().resolve()
    reviews_dir = reviews_dir.expanduser().resolve()
    resolved = plan_path.expanduser().resolve()

    # 1. Plan operand exists (single file or resolvable plan directory) and
    # resolves under {plans_dir}. A directory operand resolves through the
    # shared shape resolver BEFORE the regular-file gate (plan-directory-
    # shape plan, Task 1): a well-formed directory is accepted with its
    # manifest digest, and a malformed one refuses through the resolver's
    # named arms (whose charterless wording keeps the pinned "not a file"
    # family). A file or missing operand keeps the legacy checks and reason
    # strings byte-identically.
    shape: plan_shape.PlanShape | None = None
    if resolved.is_dir():
        try:
            shape = plan_shape.resolve_plan_operand(resolved)
        except plan_shape.PlanShapeRefusal as exc:
            return False, str(exc)
    elif not resolved.is_file():
        return False, f"plan file does not exist: {resolved}"
    try:
        rel_to_plans = resolved.relative_to(plans_dir)
    except ValueError:
        return False, (
            f"plan file resolves outside plans_dir: {resolved} "
            f"is not under {plans_dir}"
        )
    # Rejected archive: a plan under the plans dir's rejected/ subdirectory
    # is a recorded decision against doing the work. It is excluded from
    # active-plan readiness (fail-closed for direct invocations; the done
    # sweep's candidate derivation excludes the archive before this gate
    # runs). See docs/history/plans/rejected/README.md.
    if rel_to_plans.parts and rel_to_plans.parts[0] == "rejected":
        return False, (
            f"plan file sits under the rejected archive directory "
            f"({plans_dir / 'rejected'}): excluded from active-plan readiness"
        )

    # r6 Z5: a configured-but-missing reviews_dir is a wiring failure with
    # its OWN reason (mirroring the sweep's r5 message), never a misleading
    # "no review artifact" that sends the user down the wrong remedy loop.
    if not reviews_dir.is_dir():
        return False, (
            f"configured reviews_dir does not exist on disk: {reviews_dir}"
        )
    story_slug = feature_slug(resolved)
    try:
        slug = artifact_slug(resolved)
    except ArtifactSlugRefusal as exc:
        return False, str(exc)
    plan_root = repository_root(resolved.parent)
    plan_identity = normalize_plan_path(resolved, plan_root) if plan_root else None
    try:
        latest = latest_review_round(reviews_dir, slug, plan_identity)
    except AmbiguousReviewSeries as exc:
        return False, str(exc)

    # Case-variant secondary probe: scan the reviews home's directory
    # entries for round filenames matching the canonical shape regex
    # under case folding but NOT exactly, anchored as a fullmatch (the
    # module's canonical matcher; a search-based matcher would classify
    # every `.backup-<timestamp>` copy of a canonical round as
    # case-variant and permanently collision-refuse any plan with
    # backups). The probe runs for every plan regardless of its own
    # slug's case, so a post-rename legacy state is diagnosed by name.
    _glob_pattern, canonical_name_re = review_round_shape(slug)
    case_fold_re = re.compile(canonical_name_re.pattern, re.IGNORECASE)
    entry_names = {entry.name for entry in reviews_dir.iterdir()}
    case_variants: list[str] = []
    for name in sorted(entry_names):
        if (
            case_fold_re.fullmatch(name) is None
            or canonical_name_re.fullmatch(name) is not None
        ):
            continue
        variant_path = reviews_dir / name
        variant_sidecar = vrs.stats_sidecar_path(variant_path)
        try:
            variant_payload = json.loads(variant_sidecar.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            variant_payload = None
        variant_identity = record_identity(variant_path, variant_payload)
        if variant_identity is None or variant_identity == plan_identity:
            case_variants.append(name)
    if case_variants:
        if latest is not None:
            return False, (
                "case-variant round records exist under both the "
                "story-key and canonical shapes; rename the legacy pair "
                "to the canonical lowercase shape: "
                f"{', '.join(case_variants)}"
            )
        legacy_names: list[str] = []
        for name in case_variants:
            legacy_names.append(name)
            sidecar_name = name[:-3] + ".stats.json"
            if sidecar_name in entry_names:
                legacy_names.append(sidecar_name)
        return False, (
            f"no review artifact for canonical artifact slug {slug!r} "
            f"(plan filename story slug {story_slug!r}) under "
            f"{reviews_dir}; legacy case-variant round records "
            f"{', '.join(legacy_names)} exist; rename the pair to the "
            "canonical lowercase shape"
        )

    # 2. A review artifact for the canonical artifact slug (the feature
    # slug lowercased; the story slug stays in the plan filename) exists.
    if latest is None:
        if story_slug != slug:
            return False, (
                f"no review artifact for canonical artifact slug {slug!r} "
                f"(plan filename story slug {story_slug!r}) "
                f"under {reviews_dir}"
            )
        return False, (
            f"no review artifact for feature slug {slug!r} "
            f"under {reviews_dir}"
        )
    latest_path, round_no = latest

    # The sidecar and review Markdown are each read ONCE here, purely so a
    # local failure (missing file, bad JSON/UTF-8) can be classified with its
    # own reason; the shared gate below re-reads both internally. The plan
    # digest is computed ONCE and threaded into the shared gate.
    sidecar = vrs.stats_sidecar_path(latest_path)
    if not sidecar.is_file():
        return False, (
            f"missing stats sidecar for latest round r{round_no}: {sidecar.name}"
        )
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, (
            f"malformed stats sidecar (unreadable or invalid JSON): {exc}"
        )
    if not isinstance(payload, dict):
        return False, (
            f"malformed stats sidecar (top-level JSON value is not an object): "
            f"{type(payload).__name__} (round r{round_no})"
        )
    # r5 Y1: a legacy/versionless (or explicit-unsupported) sidecar is
    # REJECTED before the shared gate runs. Pure-legacy payloads take the
    # shared validator's compatibility path, which never reaches the digest
    # or source_kind checks — a fail-open hole in this fail-closed gate.
    # ``is_current_shape`` delegates to the shared classifier
    # (``classify_sidecar_schema``) so the current-vs-legacy definition has a
    # single owner; only current-shape payloads (version-1 or the versionless
    # current markers) carry a verifiable ``source_digest`` contract at all.
    if not vrs.is_current_shape(payload):
        return False, (
            f"sidecar schema is legacy/versionless; a current-shape sidecar "
            f"with a verifiable source_digest is required (round r{round_no})"
        )
    # r6 Z1: the shared gate's source_kind check only fires when the key is
    # DECLARED, so a versionless current-shape sidecar with the key deleted
    # or null bypassed it (empirically exit-0). Enforce the kind locally,
    # unconditionally, with its own named reason; the shared gate below stays
    # the authority for everything else.
    # Deliberate ordering deviation from the plan Assumptions (which
    # prescribe schema, then source_kind, then digest): this local
    # kind-before-schema pre-check runs first so a wrong-kind or kindless
    # sidecar is fail-closed classified with its own named reason instead of
    # surfacing as a generic schema failure. Same pattern as the readability
    # pre-checks above: local reason-classification pre-checks ahead of the
    # shared authority.
    declared_kind = payload.get("source_kind")
    if declared_kind != "plan":
        if declared_kind is None:
            return False, (
                f"sidecar source_kind is missing or not 'plan' (round "
                f"r{round_no})"
            )
        return False, (
            f"sidecar source_kind is {declared_kind!r}, expected 'plan' "
            f"(round r{round_no})"
        )
    try:
        content = latest_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return False, (
            f"cannot read review artifact r{round_no} (not valid UTF-8): {exc}"
        )
    if shape is not None:
        # Directory form: the digest payload is the manifest serialization
        # (the SAME compute_source_digest call below hashes it, so the
        # source_digest contract keeps its shape); the charter and task
        # texts were read once by the resolver.
        plan_bytes = shape.digest_payload
    else:
        try:
            plan_bytes = resolved.read_bytes()
        except OSError as exc:
            return False, f"cannot read plan bytes to compute digest: {exc}"
    plan_text: str | None = None
    if shape is not None:
        # Per-file fence scanning with file-named errors (plan-directory-
        # shape plan, Task 1): each file must balance on its own, so a
        # fence from one file can never pair across a file boundary in the
        # assembled text the probes read below.
        for file_label, file_text in shape.fence_units():
            _fence_problem = fence_balance_problem(file_text)
            if _fence_problem is not None:
                return False, f"plan file {file_label}: {_fence_problem}"
        plan_text = shape.charter_plus_tasks_text()
    else:
        # Structural fence-balance gate (unconditional, before ANY probe or
        # the digest gate evaluates the plan): an unterminated fence makes the
        # stripper drop everything it swallowed, so probes would silently score
        # only the document prefix. Decode defensively here: an undecodable plan
        # keeps its own later reason family.
        try:
            _fence_problem = fence_balance_problem(plan_bytes.decode("utf-8"))
        except UnicodeDecodeError:
            _fence_problem = None
        if _fence_problem is not None:
            return False, _fence_problem
    # Cap-closure declaration presence and the plan-text date guards: the
    # trigger set for the single shared defensive decode below (the only
    # gated consumers of the plan text).
    extensions = payload.get("extensions")
    cap_closure_declared = isinstance(extensions, dict) and (
        vrs.CAP_CLOSURE_KEY in extensions
    )
    round_date = str(payload.get("date") or "").strip()
    trailer_gated = _gate_fires(round_date, DECISION_MARKER_MIN_DATE)
    scope_gated = _gate_fires(round_date, REVIEW_SCOPE_MIN_DATE)
    ownership_gated = _gate_fires(round_date, PLAN_STRUCTURE_MIN_DATE)
    # Shared defensive decode for the gated plan-text consumers (the
    # declaration-routed cap-closure probe and the date-gated trailer,
    # Review Scope, and plan-ownership probes): the bytes are decoded at
    # most ONCE per call and ONLY when at least one consumer needs the
    # text, so an undecodable plan whose round is date-exempt and which
    # carries no declaration keeps today's pass and its own later reason
    # family (r2 F2). The existing cannot-read reason family is kept for
    # the shared failure case; step 6 reuses the decoded text. The
    # directory form's assembled text was decoded per file above, so this
    # decode is the single-file form's duty only.
    if plan_text is None and (
        cap_closure_declared or trailer_gated or scope_gated or ownership_gated
    ):
        try:
            plan_text = plan_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            return False, (
                f"cannot read plan bytes for gated checks (trailer, "
                f"Review Scope, and/or plan ownership): {exc}"
            )
    expected_digest = vrs.compute_source_digest("plan", plan_bytes)

    # 3. Shared sidecar gate: the SAME validation the staging validator runs
    # (schema validity, then source_kind, then digest — the sequencing the
    # plan Assumptions prescribe), with the "Stats sidecar: skipped" waiver
    # disabled by passing expected_digest and source_kind explicitly. This is
    # the single schema/kind/digest authority; no local duplicate checks. The
    # FIRST error is mapped to a crisp first-failed reason below, preserving
    # the distinct reason families (malformed sidecar, schema, source_kind,
    # stale digest) by classifying the shared validator's error text.
    # Task 6 pass-through: the correction context (the plan path relative to
    # its resolved repository root, the current bytes, and that root) arms
    # the graded stale arm, so it can verify a declared corrections record
    # and run the round-anchored digest check on EVERY authoritative
    # freshness check; a plan outside any git repository passes no context
    # and keeps the legacy exact-match disposition.
    corrections_context = _plan_corrections_context(resolved, plan_bytes)
    staging_result = vrs.ValidationResult(path=latest_path)
    vrs.validate_stats_sidecar(
        latest_path,
        content,
        staging_result,
        expected_digest=expected_digest,
        source_kind="plan",
        corrections_context=corrections_context,
    )
    if staging_result.errors:
        first_error = staging_result.errors[0]
        return False, _first_gate_error_reason(first_error, payload, round_no)
    graded_indeterminate = getattr(
        staging_result, "indeterminate_reason", None
    )
    if graded_indeterminate is not None:
        # The corrections-graded arm could not re-derive its git evidence
        # (an unresolvable seal anchor or a plumbing failure over resolved
        # inputs): the gate refuses without a verdict instead of passing,
        # and main() classifies the prefixed reason as the indeterminate
        # outcome (exit 2).
        return False, _GATE_INDETERMINATE_PREFIX + graded_indeterminate

    # 4. Verdict: sidecar ``verdict`` field is DECISIVE when conforming
    # ("yes"/"no" via the single-owner ``sidecar_verdict`` predicate); for
    # ANY other value (absent, or a non-conforming legacy value such as a
    # dict or a non-yes/no string) the legacy Summary total rule runs
    # UNCHANGED (any line with a word-bounded ready=yes/no token; last
    # occurrence wins). Version-1 records with non-conforming values never
    # reach this step (the schema gate rejects them earlier); versionless
    # legacy records keep today's tolerance (r2 F1 fold: the live corpus
    # carries legacy ``verdict`` keys, so a rejecting consumer would newly
    # fail artifacts that pass today).
    # Cap-closure exception (certification machinery contract-collisions
    # plan, Task 1): when the final sidecar DECLARES
    # ``extensions.cap_closure``, this step keeps only the ordering
    # decision, mirroring the ``fence_balance_problem`` consumption above.
    # The declaration routes the probe at the plan bytes; a satisfied
    # conjunct passes (whatever the verdict value), and a probe reason
    # returns the dedicated terminal-state reason. Without the
    # declaration, today's verdict behavior is unchanged.
    verdict_field = sidecar_verdict(payload)
    if cap_closure_declared:
        findings = payload.get("findings")
        staged_patterns = [
            row.get("pattern")
            for row in (findings if isinstance(findings, list) else [])
            if isinstance(row, dict) and isinstance(row.get("pattern"), str)
        ]
        problem = cap_closure_terminal_state_problem(
            plan_text,
            extensions.get(vrs.CAP_CLOSURE_KEY),
            staged_patterns,
        )
        if problem is not None:
            return False, problem
    else:
        if verdict_field == "no":
            return False, (
                f"latest review r{round_no} sidecar verdict field reports 'no'"
            )
        if verdict_field != "yes":
            summary = summary_section(content)
            verdicts = verdict_tokens(summary)
            if not verdicts or verdicts[-1].lower() != "yes":
                return False, (
                    f"latest review r{round_no} does not report a ready=yes verdict "
                    f"line in its ## Summary"
                )

    # 5. is_review_ready() over the same Markdown is True.
    if not vrs.is_review_ready(content):
        return False, (
            f"latest review r{round_no} has unresolved blocking findings "
            f"(is_review_ready is False)"
        )

    # 6. Decision-points trailer (forward-looking): plans whose LATEST round
    # is dated on or after DECISION_MARKER_MIN_DATE must carry the trailer
    # in their bytes; legacy rounds stay exempt (no retrofit). A sidecar
    # with a missing, empty, or whitespace-only date, or a date that is
    # not exactly ``YYYY-MM-DD`` (malformed, e.g. ``09/10/2026``), is also
    # exempt: the schema does not hard-require the field on versionless
    # current-shape sidecars, and a malformed value must not reach the
    # lexicographic gate comparison (r4 F4); failing those would retrofit
    # legacy artifacts; the authoring-side prose gate covers newly
    # authored plans regardless (r1 F3). The date guards and the shared
    # decode live beside the fence-balance consumption above (one decode
    # per call, one named failure reason); this block reuses the decoded
    # plan text.
    if trailer_gated:
        problem = decision_marker_problem(plan_text)
        if problem:
            return False, _gated_probe_reason(
                problem, DECISION_MARKER_MIN_DATE, round_no, round_date
            )

    # 7. Review Scope category gate (forward-looking): plans whose LATEST
    # round is dated on or after REVIEW_SCOPE_MIN_DATE must carry a
    # well-formed ## Review Scope section; earlier rounds stay exempt (no
    # retrofit). The same malformed-or-missing-date exemption as the
    # trailer gate applies (a non-YYYY-MM-DD value never reaches the
    # lexicographic comparison).
    if scope_gated:
        problem = review_scope_problem(plan_text)
        if problem:
            return False, _gated_probe_reason(
                problem, REVIEW_SCOPE_MIN_DATE, round_no, round_date
            )

    # 8. Plan-structure gate (forward-looking): plans whose LATEST round
    # is dated on or after PLAN_STRUCTURE_MIN_DATE must satisfy the
    # plan-ownership static checks (plan_ownership_problem: at most one
    # creating task per new file, consumer-before-owner ordering, Files:
    # paths existing on disk or carrying the planned-new marker, at most
    # one transition-table section) and the classification-tag probe
    # (scope_classification_problem); earlier rounds stay exempt (no
    # retrofit). The same malformed-or-missing-date exemption as the
    # other gated probes applies.
    if ownership_gated:
        problem = plan_ownership_problem(
            plan_text, repo_root(plans_dir.parent)
        )
        if problem:
            return False, _gated_probe_reason(
                problem, PLAN_STRUCTURE_MIN_DATE, round_no, round_date
            )
        problem = scope_classification_problem(plan_text)
        if problem:
            return False, _gated_probe_reason(
                problem, PLAN_STRUCTURE_MIN_DATE, round_no, round_date
            )

    # 9. Extraction-rule executability parity (contract single-sourcing):
    # the create boundary's three extraction-rule components (per-task
    # checklist action classification, the checklist-action derivation its
    # checks consume, and the bounded-evidence envelope) run here over the
    # DERIVED plan shape through the single-homed owned module, so a plan
    # Phase 0 would refuse on those grounds fails certification with the
    # same labels - and a certified plan never refuses at Phase 0 on any of
    # them. POSITION: this step runs AFTER the structural conditions
    # (readability, sidecar, digest, verdict, trailer, Review Scope, plan
    # ownership), so a parity fixture mints a conforming review record and
    # sidecar at the matching digest and makes THIS check the failing
    # condition. The clone-signature component's inputs (the
    # discovery-derived verification commands) are a create-boundary
    # internal not derivable from the plan file alone: per the plan's
    # Assumption that arm is the EXPLICIT RESIDUAL recorded here, not a
    # pretended parity; the signature detection still single-homes in the
    # owned module where the create boundary calls it.
    if plan_text is None:
        # The gated consumers above never needed the text (a legacy-exempt
        # round). An undecodable plan KEEPS TODAY'S PASS here (the pinned
        # r2 F2 shape: its own reason family, no extraction-rule refusal) -
        # the create boundary refuses undecodable plans at discovery before
        # seeding anyway, so no false parity is claimed.
        try:
            plan_text = plan_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return True, None
    # The derived-task loops live in the module-level
    # extraction_rule_executability_problem helper, which the pre-round
    # gate's run_pre_round calls too, so both surfaces return byte-identical
    # verdicts and refusal strings by construction.
    problem = extraction_rule_executability_problem(plan_text)
    if problem is not None:
        return False, problem

    return True, None


# Raw "ready=" mention in Summary text (sweep detector; broader than the
# total-rule token on purpose: it must also fire on cross-line or malformed
# shapes the token rule cannot see).
SWEEP_MENTION_RE = re.compile(r"ready\s*=", re.IGNORECASE)


def run_sweep(reviews_dir: Path) -> int:
    """Drift check (r4 X1.4): sweep ``{reviews_dir}`` plan-review artifacts.

    Under the total rule every ``## Summary`` whose text mentions ``ready=``
    must yield at least one verdict token; an anomaly is a file whose Summary
    contains a ``ready=`` mention but whose parse finds no verdict token
    (cross-line split or otherwise malformed). Exit 0 when zero anomalies;
    exit 1 listing them.
    """
    # r5 Y7: a configured-but-missing reviews_dir is a wiring failure with
    # its OWN reason — never a silent zero-artifact pass.
    if not reviews_dir.is_dir():
        print(
            f"sweep FAILED: configured reviews_dir does not exist on disk: "
            f"{reviews_dir}",
            file=sys.stderr,
        )
        print("OUTCOME: %s" % OUTCOME_LABELS[1])
        return 1
    anomalies: list[str] = []
    total = 0
    covered = 0
    for path in sorted(reviews_dir.glob("*-plan-review-*.md")):
        total += 1
        # Coverage counter (Task 4): a covered artifact's sidecar exists,
        # parses as JSON, and carries a conforming ``verdict`` via the SAME
        # ``sidecar_verdict`` helper the readiness verdict step uses (single
        # owner of the yes/no predicate). Unreadable or malformed sidecars
        # count as NOT covered and are NOT anomalies.
        try:
            sidecar_payload = json.loads(
                vrs.stats_sidecar_path(path).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeDecodeError, ValueError):
            sidecar_payload = None
        if isinstance(sidecar_payload, dict) and sidecar_verdict(sidecar_payload):
            covered += 1
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            anomalies.append(f"{path.name}: unreadable ({exc})")
            continue
        summary = summary_section(content)
        if SWEEP_MENTION_RE.search(summary) and not verdict_tokens(summary):
            anomalies.append(
                f"{path.name}: ## Summary mentions ready= but the total "
                f"rule finds no verdict token (cross-line or malformed)"
            )
    # Coverage line built ONCE (r1 F5): both post-glob exits print the same
    # variable, so the two messages cannot diverge on future wording edits.
    coverage_line = (
        f"sweep coverage: {covered}/{total} plan-review artifacts carry a "
        "sidecar verdict field; legacy Summary grammar deletion is "
        "eligible only when total is positive and covered equals total"
    )
    if anomalies:
        print("sweep FAILED: verdict anomalies in plan-review artifacts:")
        for line in anomalies:
            print(f"  - {line}")
        print(coverage_line)
        print("OUTCOME: %s" % OUTCOME_LABELS[1])
        return 1
    print(coverage_line)
    print(
        f"sweep OK: no verdict anomalies across plan-review artifacts under "
        f"{reviews_dir}"
    )
    print("OUTCOME: %s" % OUTCOME_LABELS[0])
    return 0


# Execution budget sizing caps (pre-round warning thresholds). The caps
# are the plans skill's split questions, never refusals: a breach emits a
# non-blocking warning naming the breached threshold, so the split
# decision surfaces at authoring time instead of mid-execution. The
# comparisons are strictly greater (at-threshold values are silent).
PRE_ROUND_BUDGET_TOTAL_CAP_HOURS = 3.0
PRE_ROUND_BUDGET_TASK_CAP_HOURS = 1.5
PRE_ROUND_BUDGET_TASK_COUNT_CAP = 4
# The pinned `Execution budget:` line grammar: two author-computed
# non-negative decimal hours with an optional single fractional part
# (integers valid); a missing number, a negative, or a non-numeric value
# is a malformed line. The gate reads the declared numbers and never
# estimates cost from plan content.
PRE_ROUND_BUDGET_LINE_RE = re.compile(r"^Execution budget:[ \t]+(.+?)[ \t]*$")
PRE_ROUND_BUDGET_VALUE_RE = re.compile(
    r"^(\d+(?:\.\d+)?)h total, largest task (\d+(?:\.\d+)?)h$"
)
PRE_ROUND_TASK_HEADING_RE = re.compile(r"^### Task \d+:")


def anchors_block_problem(plan_text: str) -> str | None:
    """The pre-round anchors-block grammar probe (plans rule 29, added by
    the primary-class-anchors-grammar-drift plan Task 1).

    Enumerates the ``### Task N:`` ordinals over fence-stripped text
    (mirroring the create path's payload-driven ordinals: a fenced
    example section is never an enumerated ordinal) and parses each
    extracted section RAW through the shared parser in
    ``scripts/plan_shape.py`` -- the same parser, by identity, that the
    execution seeding's anchors block runs, so a readiness refusal here
    implies a ``create`` refusal there (the inherited fence-blindness is
    parity with ``create``, not a new restriction). A malformed entry
    returns the named problem line quoting the offending entry and
    interpolating the shared canonical shape; a plan with no task
    sections, blockless sections, or conforming blocks returns None.
    """

    stripped = _strip_fences(plan_text)
    ordinals = sorted(
        {
            int(match.group(1))
            for match in re.finditer(r"^### Task (\d+):", stripped, re.MULTILINE)
        }
    )
    for ordinal in ordinals:
        section = plan_shape.plan_task_section(plan_text, f"task-{ordinal}")
        if section is None:
            continue
        try:
            plan_shape.primary_class_anchors(section)
        except ValueError as exc:
            return (
                f"Primary class anchors block refused in Task {ordinal}: "
                f"{exc}; the canonical entry shape is "
                f"{plan_shape.PRIMARY_CLASS_ANCHOR_SHAPE}"
            )
    return None


def pre_round_budget_warnings(plan_text: str) -> list[str]:
    """Sizing warnings for the optional `Execution budget:` header line.

    The header region is the region between the plan title line (the
    first line starting ``# ``) and the first ``## `` heading, where the
    required metadata block lives. Returns zero warnings when the region
    carries no `Execution budget:` line (silent skip: plans without the
    line behave byte-identically); one malformed-line warning naming the
    pinned grammar when the line's value does not parse; otherwise one
    warning per strictly-greater breach in the declared order (total,
    largest task, task count from the ``### Task N:`` headings). Every
    returned line already carries the ``readiness PRE-ROUND WARNING:``
    prefix. Structural-only: the declared numbers are read as authored
    and no cost is ever estimated from plan content.
    """
    lines = plan_text.splitlines()
    header_lines: list[str] = []
    seen_title = False
    for line in lines:
        if not seen_title:
            if line.startswith("# "):
                seen_title = True
            continue
        if line.startswith("## "):
            break
        header_lines.append(line)
    budget_value: str | None = None
    for line in header_lines:
        match = PRE_ROUND_BUDGET_LINE_RE.match(line)
        if match is not None:
            budget_value = match.group(1)
            break
    if budget_value is None:
        return []
    value_match = PRE_ROUND_BUDGET_VALUE_RE.match(budget_value)
    if value_match is None:
        return [
            "readiness PRE-ROUND WARNING: the Execution budget line "
            "does not match the required grammar "
            "'Execution budget: <total>h total, largest task <max>h' "
            "(non-negative decimal hours with an optional single "
            "fractional part, integers valid; a missing number, a "
            "negative, or a non-numeric value is a malformed line); "
            "the declared budget is ignored"
        ]
    total_hours = float(value_match.group(1))
    largest_task_hours = float(value_match.group(2))
    task_count = sum(
        1 for line in lines if PRE_ROUND_TASK_HEADING_RE.match(line)
    )
    warnings: list[str] = []
    if total_hours > PRE_ROUND_BUDGET_TOTAL_CAP_HOURS:
        warnings.append(
            f"readiness PRE-ROUND WARNING: execution budget total "
            f"{value_match.group(1)}h exceeds the "
            f"{PRE_ROUND_BUDGET_TOTAL_CAP_HOURS}h plan cap; split the plan"
        )
    if largest_task_hours > PRE_ROUND_BUDGET_TASK_CAP_HOURS:
        warnings.append(
            f"readiness PRE-ROUND WARNING: execution budget largest task "
            f"{value_match.group(2)}h exceeds the "
            f"{PRE_ROUND_BUDGET_TASK_CAP_HOURS}h task cap; split the task "
            f"into its own plan"
        )
    if task_count > PRE_ROUND_BUDGET_TASK_COUNT_CAP:
        warnings.append(
            f"readiness PRE-ROUND WARNING: execution budget task count "
            f"{task_count} exceeds the "
            f"{PRE_ROUND_BUDGET_TASK_COUNT_CAP}-task cap; split the plan"
        )
    return warnings


def plan_review_identity_warnings(plan_path: Path, plans_dir: Path) -> list[str]:
    """Report other dated plans sharing this plan's canonical review slug."""
    try:
        slug = artifact_slug(plan_path)
    except ArtifactSlugRefusal:
        return []
    current = plan_path.expanduser().resolve()
    root = plans_dir.expanduser().resolve()
    repository = repository_root(root.parent)
    collisions: set[str] = set()
    dated_name = re.compile(r"^\d{4}-\d{2}-\d{2}-.+")
    for candidate in root.rglob("*.md"):
        if candidate.name == "PLAN.md":
            source = candidate.parent
            if not dated_name.fullmatch(source.name):
                continue
        elif dated_name.fullmatch(candidate.name):
            source = candidate
        else:
            continue
        source = source.resolve()
        if source == current:
            continue
        try:
            candidate_slug = artifact_slug(source)
        except ArtifactSlugRefusal:
            continue
        if candidate_slug != slug:
            continue
        display = (
            source.relative_to(repository).as_posix()
            if repository is not None and source.is_relative_to(repository)
            else source.as_posix()
        )
        collisions.add(display)
    return [
        f"readiness PRE-ROUND WARNING: plan review slug {slug!r} is also used by {path}; source-plan identity keeps review series separate"
        for path in sorted(collisions)
    ]


def extraction_rule_executability_problem(
    plan_text: str | None = None,
    *,
    derived_task_map: dict[str, dict[str, Any]] | None = None,
) -> str | None:
    """The extraction-rule executability parity probes over one plan's
    derived task sections, single-homed here so the full gate's step 9
    and the pre-round gate's plan-private subset return byte-identical
    refusal strings by construction.

    With ``plan_text``, the derived task map is built exactly as step 9
    builds it (the create boundary's task grammar recognizes
    ``### Task <N>:`` headings only; a task section with no acceptance
    criteria stays skipped, the discovery-path residual the create
    boundary refuses first). With ``derived_task_map``, the caller
    supplies pre-derived items directly (the unit-level witness over
    seeding shapes no plan text can express); at least one input must be
    provided, and a supplied derived task map takes precedence over plan
    text. Per task, the three single-homed owned
    checks run in step 9's order (checklist action classification,
    checklist action derivation, evidence criterion ids) and the first
    ``ValueError`` becomes the returned named refusal string, wrapped
    through the SAME ``execute_plan_runtime._named_evidence_limit_error``
    task-attributed shape for the bounded-evidence envelope grounds (the
    import kept inside the except arm so the deployment-degradation shape
    is unchanged); ``None`` when every derived task section is
    executable. The clone-signature component is NOT here: its
    discovery-derived verification-command inputs are the documented
    create-boundary-only residual.
    """
    if derived_task_map is None:
        if plan_text is None:
            raise ValueError(
                "extraction_rule_executability_problem needs plan bytes or "
                "a derived task map"
            )
        derived_task_map = {}
        for section_title, section_body in _plan_task_sections(plan_text):
            ordinal_match = re.match(r"^Task (\d+):", section_title)
            if ordinal_match is None:
                # The create boundary's task grammar recognizes
                # ``### Task <N>:`` headings only; other headings seed no task
                # and so carry no extraction-rule ground.
                continue
            task_id = f"task-{ordinal_match.group(1)}"
            criteria, actions = runtime_capabilities.derive_plan_checklist_actions(section_body)
            if not criteria:
                # A task section with no acceptance criteria (or only Commit:
                # lines) is refused by the create boundary's discovery BEFORE
                # the extraction checks run ("discovery produced no acceptance
                # criteria ..."): the discovery-path class is the documented
                # residual, out of certification parity, so the task is skipped
                # here rather than false-failing with a label discovery never
                # reaches.
                continue
            derived_task_map[task_id] = {
                "task_body": section_body,
                "checklist_actions": actions,
                "required_criteria": criteria,
            }
    for task_id, item in sorted(derived_task_map.items()):
        try:
            runtime_capabilities.check_checklist_action_classification(task_id, item)
            runtime_capabilities.derive_checklist_actions(task_id, item)
            runtime_capabilities.evidence_criterion_ids(list(item["required_criteria"]))
        except ValueError as error:
            named = error
            if any(
                needle in str(error)
                for needle in (
                    "evidence criterion exceeds UTF-8 item byte limit",
                    "evidence criteria exceed UTF-8 aggregate byte limit",
                    "evidence criteria exceed receipt item-count limit",
                )
            ):
                # The create boundary wraps the single-homed limit refusals
                # with the task-attributed named shape; reuse the SAME
                # wrapper so the full label text is byte-identical.
                from execute_plan_runtime import _named_evidence_limit_error

                named = _named_evidence_limit_error(derived_task_map, error)
            return (
                f"plan fails the executability contract the create boundary "
                f"enforces at Phase 0: {named}"
            )
    return None


def run_pre_round(plan_path: Path, plans_dir: Path) -> int:
    """Structural-only pre-round authoring gate (plans rule 29).

    Runs the five structural review-record-independent probes over the
    plan bytes in gate order (``decision_marker_problem``,
    ``review_scope_problem``, ``plan_ownership_problem``,
    ``scope_classification_problem``, ``anchors_block_problem``) and then
    the extraction-rule executability parity probes
    (``extraction_rule_executability_problem``, the plan-private subset of
    the full gate's step 9: the bounded-evidence envelope inside the
    evidence-criterion-ids arm plus the checklist action classification
    and derivation checks over the derived task sections; the
    clone-signature component stays create-boundary-only, its
    discovery-derived verification-command inputs not derivable from plan
    bytes) with NO
    sidecar-date gating and NO review-record consultation: the tolerated
    no-review-artifact/missing-sidecar class is respected by construction
    (this function never opens ``reviews_dir`` or any sidecar). All clean
    prints the OK line and exits 0; the FIRST failing condition prints
    ``readiness PRE-ROUND FAILED: <reason>`` to stderr and exits 1, an
    executability refusal carrying step 9's byte-identical named label.

    After every probe passes, the optional `Execution budget:` header
    line is sized non-blockingly: ``readiness PRE-ROUND WARNING:`` lines
    go to stderr (one per strictly-greater breach in the declared order,
    total, largest task, task count, plus one malformed-line warning
    naming the grammar; silence when the line is absent). The warning-only
    Files:-coverage arm (``plan_files_coverage_warnings``, machinery row
    ``script:plan-files-coverage-arm``) prints on the same channel under
    the same contract: its lines go to stderr after all probes pass and
    the failure paths above emit zero warning lines. Warnings never
    change the OK line, the exit code, or the failure path (a probe
    failure emits zero warning lines).

    The first-step path semantics (directory, missing, outside plans_dir,
    rejected archive) restate ``evaluate_readiness`` step 1 with its exact
    reason strings so both invocations report the same first-step failure
    for the same input; the shared gate itself is untouched (additive
    branch only). Plan bytes must decode as UTF-8; the decode failure
    carries its own reason here because the full gate's wording is tied to
    its date-gated probes. A directory-shaped plan (plan-directory-shape
    plan, Task 1) resolves through the shared helper: per-file fence
    scanning names the file, and the probes read the charter-plus-tasks
    assembly; the single-file path is byte-identical.
    """
    plans_dir = plans_dir.expanduser().resolve()
    resolved = plan_path.expanduser().resolve()

    # Mirror evaluate_readiness step 1 exactly: same checks in the same
    # order, and byte-identical reason strings (a directory operand now
    # resolves through the shared shape resolver, whose named arms keep
    # the pinned reason families; a well-formed directory proceeds).
    reason: str | None = None
    shape: plan_shape.PlanShape | None = None
    if resolved.is_dir():
        try:
            shape = plan_shape.resolve_plan_operand(resolved)
        except plan_shape.PlanShapeRefusal as exc:
            reason = str(exc)
    elif not resolved.is_file():
        reason = f"plan file does not exist: {resolved}"
    if reason is None:
        try:
            rel_to_plans = resolved.relative_to(plans_dir)
        except ValueError:
            reason = (
                f"plan file resolves outside plans_dir: {resolved} "
                f"is not under {plans_dir}"
            )
        else:
            # Rejected archive: same exclusion as the full gate's step 1.
            if rel_to_plans.parts and rel_to_plans.parts[0] == "rejected":
                reason = (
                    f"plan file sits under the rejected archive directory "
                    f"({plans_dir / 'rejected'}): excluded from active-plan "
                    f"readiness"
                )
    if reason is not None:
        print(f"readiness PRE-ROUND FAILED: {reason}", file=sys.stderr)
        return 1

    plan_text: str | None = None
    problem: str | None = None
    if shape is not None:
        # Directory form: per-file fence scanning with file-named errors
        # (same wording as the full gate's directory path), then the
        # charter-plus-tasks assembly the probes read.
        for file_label, file_text in shape.fence_units():
            problem = fence_balance_problem(file_text)
            if problem is not None:
                problem = f"plan file {file_label}: {problem}"
                break
        if problem is None:
            plan_text = shape.charter_plus_tasks_text()
    else:
        try:
            plan_text = resolved.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(
                f"readiness PRE-ROUND FAILED: cannot read plan bytes (not "
                f"valid UTF-8): {exc}",
                file=sys.stderr,
            )
            return 1
        # Gate order, first problem wins; each probe stays the single owner
        # of its check (no logic re-implemented here). The fence-balance probe
        # runs FIRST: an unterminated fence makes the stripper drop everything
        # it swallowed, so no later probe may evaluate the truncated text.
        problem = fence_balance_problem(plan_text)
    if problem is None:
        problem = decision_marker_problem(plan_text)
    if problem is None:
        problem = review_scope_problem(plan_text)
    if problem is None:
        problem = plan_ownership_problem(
            plan_text, repo_root(plans_dir.parent)
        )
    if problem is None:
        problem = scope_classification_problem(plan_text)
    if problem is None:
        problem = anchors_block_problem(plan_text)
    if problem is None:
        # The plan-private subset of step 9 (extraction-rule executability
        # parity): the SAME helper step 9 calls, so the refusal strings are
        # byte-identical; still no review-record consultation.
        problem = extraction_rule_executability_problem(plan_text)
    if problem is not None:
        print(f"readiness PRE-ROUND FAILED: {problem}", file=sys.stderr)
        return 1

    # Non-blocking sizing warnings (report posture per the guard
    # doctrine): emitted only after every structural probe passed, so the
    # failure path above emits zero warning lines. Stderr only; the OK
    # line and the exit contract below are unchanged.
    for warning in pre_round_budget_warnings(plan_text):
        print(warning, file=sys.stderr)
    for warning in plan_files_coverage_warnings(plan_text):
        print(warning, file=sys.stderr)
    for warning in plan_review_identity_warnings(resolved, plans_dir):
        print(warning, file=sys.stderr)

    print(
        "readiness PRE-ROUND OK: structural checks clean "
        "(review record not consulted)"
    )
    return 0


def check_review_name(
    plan_path: Path, round_md: Path, reviews_dir: Path
) -> tuple[bool, str | None]:
    """Name-shape probe: does one written round pair bind to the plan's
    canonical artifact slug?

    The per-round companion of ``latest_review_round``: re-verifies the
    review artifact pair ``round_md`` against the SAME discovery shape the
    done-boundary gate discovers rounds through, so a misnamed round is
    caught in the round that wrote it instead of surfacing at the done
    boundary as the readiness gate's no-artifact reason (which names the
    canonical artifact slug beside the story slug for a story-key plan).
    Returns ``(ok, reason)``; ``reason`` names the FIRST failed condition
    only. A plan whose stem lowercases to an unsafe kebab form converts
    here into the named ``(False, reason)`` refusal, never a traceback.

    Checks, first problem wins: the round file's parent directory must BE
    the configured ``reviews_dir``; the filename must fullmatch the shared
    ``review_round_shape`` for the plan's canonical ``artifact_slug`` (the
    feature slug lowercased); the sidecar
    (``vrs.stats_sidecar_path``) must exist and parse as a JSON object;
    ``artifact_slug`` must equal the slug; and when a ``coverage`` object
    is present, every non-empty link value in ``attempts[]``
    (``artifact``/``sidecar``), ``inherited_coverage[]``
    (``artifact``/``sidecar``), and ``replacement[]``
    (``original_artifact``/``original_sidecar``) must resolve through the
    staging validator's own ``vrs._coverage_artifact_exists`` (a rename
    orphans the old filename inside the sidecar's self-references). The
    probe parses ONLY the fields it checks: staging schema validation
    stays ``validate_review_staging.py --hard``'s duty and is never run
    here.
    """
    reviews_dir = reviews_dir.expanduser().resolve()
    # Identity checks (parent directory + filename) run on the LEXICAL
    # path: a symlinked round path must be validated under the name and
    # location it was CLAIMED at, never its symlink target's identity
    # (a claimed r9 name whose target is a clean r1 pair would otherwise
    # pass). The sidecar and every content check below run against the
    # CLAIMED (lexical) path too, so the claimed PAIR must be complete
    # under the claimed names; a symlink borrowing a clean target's
    # sidecar fails its own missing-sidecar check.
    _lex = Path(os.path.abspath(round_md.expanduser()))
    lexical_round = Path(os.path.realpath(_lex.parent)) / _lex.name
    resolved_plan = plan_path.expanduser().resolve()
    story_slug = feature_slug(resolved_plan)
    try:
        slug = artifact_slug(resolved_plan)
    except ArtifactSlugRefusal as exc:
        return False, str(exc)

    # The round file must live DIRECTLY under the configured reviews
    # directory: the gate's glob only ever looks there, so a pair staged
    # anywhere else is invisible to the done-boundary discovery.
    if lexical_round.parent != reviews_dir:
        return False, (
            f"round file must live directly under the configured reviews "
            f"directory {reviews_dir}: {lexical_round.parent}"
        )

    _glob_pattern, name_re = review_round_shape(slug)
    match = name_re.fullmatch(lexical_round.name)
    if match is None:
        return False, (
            f"round filename does not match the discovery shape "
            f"*-plan-review-{slug}[-p<8-hex-token>]-r<N>.md (N >= 1) for canonical "
            f"artifact slug {slug!r} (plan filename story slug "
            f"{story_slug!r}): {lexical_round.name}"
        )
    round_no = int(match.group(1))

    sidecar = vrs.stats_sidecar_path(lexical_round)
    if not sidecar.is_file():
        return False, (
            f"missing stats sidecar for round r{round_no}: {sidecar.name}"
        )
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, (
            f"malformed stats sidecar (unreadable or invalid JSON): {exc}"
        )
    if not isinstance(payload, dict):
        return False, (
            f"malformed stats sidecar (top-level JSON value is not an "
            f"object): {type(payload).__name__} (round r{round_no})"
        )

    plan_root = repository_root(resolved_plan.parent)
    identity = normalize_plan_path(resolved_plan, plan_root) if plan_root else None
    if identity is not None:
        recorded_identity = record_identity(lexical_round, payload)
        token_match = re.search(r"-p([0-9a-f]{8})-r[1-9]\d*\.md$", lexical_round.name)
        if recorded_identity is not None and recorded_identity != identity:
            return False, (
                f"review record source plan identity is {recorded_identity!r}, "
                f"expected {identity!r}"
            )
        if token_match and token_match.group(1) != plan_identity_token(identity):
            return False, "review filename plan-identity token does not match source-plan path"
        if token_match and recorded_identity is None:
            return False, "identity-qualified review record has no source-plan identity"
        extensions = payload.get("extensions")
        if (
            not token_match
            and isinstance(extensions, dict)
            and extensions.get("plan_identity")
        ):
            return False, "review record with sidecar plan identity must carry its identity token in the filename"

    declared_slug = payload.get("artifact_slug")
    if declared_slug != slug:
        return False, (
            f"sidecar artifact_slug is {declared_slug!r}, expected "
            f"{slug!r} (round r{round_no})"
        )

    coverage = payload.get("coverage")
    if isinstance(coverage, dict):
        for list_key, keys in (
            ("attempts", ("artifact", "sidecar")),
            ("inherited_coverage", ("artifact", "sidecar")),
            ("replacement", ("original_artifact", "original_sidecar")),
        ):
            entries = coverage.get(list_key)
            for index, entry in enumerate(
                entries if isinstance(entries, list) else []
            ):
                if not isinstance(entry, dict):
                    continue
                for key in keys:
                    value = entry.get(key)
                    if (
                        isinstance(value, str)
                        and value.strip()
                        and not vrs._coverage_artifact_exists(value)
                    ):
                        return False, (
                            f"coverage {list_key}[{index}] entry's {key} "
                            f"references a missing file: {value} (round "
                            f"r{round_no})"
                        )
    return True, None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _check_sibling_compat() -> str | None:
    """Named error when the sibling shared-rule module drifted, else ``None``."""
    declared = getattr(vrs, "COMPAT_VERSION", None)
    if declared is None:
        return (
            "sibling validate_review_staging.py does not declare COMPAT_VERSION; "
            "the deployment is a partial update"
        )
    if declared != EXPECTED_SIBLING_COMPAT_VERSION:
        return (
            f"sibling validate_review_staging.py COMPAT_VERSION {declared!r} "
            f"!= expected {EXPECTED_SIBLING_COMPAT_VERSION!r}; "
            "the deployment is a partial update with divergent "
            "shared-rule semantics"
        )
    return None


# In-process selftest suppression (invocation telemetry): the selftest is a
# metadata exit, not a measured lane, and its fixture families manage the
# ``.ai-playbook`` layout of the shared temp root with plain mkdir/rmdir, so
# the in-process ``main()`` calls must leave no telemetry footprint (no
# metrics home created, no line appended). Subprocess invocations of the
# script stay measured as designed.
_selftest_telemetry_suppressed = False


def main(argv: list[str] | None = None) -> int:
    """CLI entry: one self-timed wall span across the full run (the
    invocation-telemetry plan). The body runs under try/finally so the
    fail-open self-timed append fires on the SystemExit paths too (usage
    errors, refusals); the writer's own failure never touches the exit
    status or either contract channel."""
    started = time.time()
    try:
        return _main(argv)
    finally:
        if invocation_telemetry is not None and not _selftest_telemetry_suppressed:
            invocation_telemetry.record_invocation(
                "plan_readiness.py",
                "readiness-gate",
                invocation_telemetry.elapsed_ms(started),
            )


def _main(argv: list[str] | None = None) -> int:
    parser = OutcomeArgumentParser(
        description="Fail-closed reviewed-plan readiness gate"
    )
    parser.add_argument("plan_path", nargs="?", help="Path to the plan file")
    parser.add_argument(
        "--selftest", action="store_true", help="Run fixture checks and exit"
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Sweep {reviews_dir} plan-review artifacts for verdict-parse "
        "anomalies (Summary text contains ready= but the total rule finds "
        "no verdict token); exit 0 when none, exit 1 listing them",
    )
    parser.add_argument(
        "--pre-round",
        action="store_true",
        help="Run the structural-only pre-round gate (plans rule 29) over "
        "the plan: the five structural probes plus the extraction-rule executability parity probes with no "
        "sidecar-date gating and no review-record consultation",
    )
    parser.add_argument(
        "--check-review-name",
        metavar="ROUND_MD",
        help="Name-shape probe: verify that the ROUND_MD review artifact "
        "pair under {reviews_dir} binds to the plan's canonical artifact "
        "slug (the feature slug lowercased; the story key stays in the "
        "plan filename; round filename matches the gate's discovery "
        "shape, stats sidecar present with artifact_slug equal to the "
        "slug, coverage self-references resolve); prints review name "
        "check OK/FAILED and exits 0/1",
    )
    parser.add_argument(
        "--print-artifact-slug",
        action="store_true",
        help="Print the plan's canonical artifact slug (the feature slug "
        "lowercased, through the one artifact_slug derivation) and exit; "
        "read-only: no review record consultation, no facts resolution",
    )
    args = parser.parse_args(argv)

    # Parse-time mutual exclusion (plans rule 29): --pre-round composes
    # with neither --selftest nor --sweep; the combination is a usage
    # error (exit 3, the outcome contract's tool error) decided before
    # any mode runs.
    if args.pre_round and args.selftest:
        parser.error("--pre-round must not be combined with --selftest")
    if args.pre_round and args.sweep:
        parser.error("--pre-round must not be combined with --sweep")

    # Parse-time mutual exclusion (--check-review-name probe): the probe
    # composes with neither --selftest, --sweep, nor --pre-round, and its
    # plan operand is required; every violation is a usage error (exit 3,
    # the outcome contract's tool error) decided before any mode runs.
    if args.check_review_name and args.selftest:
        parser.error(
            "--check-review-name must not be combined with --selftest"
        )
    if args.check_review_name and args.sweep:
        parser.error("--check-review-name must not be combined with --sweep")
    if args.check_review_name and args.pre_round:
        parser.error(
            "--check-review-name must not be combined with --pre-round"
        )
    if args.check_review_name and not args.plan_path:
        parser.error("plan_path is required when --check-review-name is set")

    # Parse-time mutual exclusion (--print-artifact-slug print arm): the
    # slug print composes with neither --selftest, --sweep, --pre-round,
    # nor --check-review-name, and its plan operand is required; every
    # violation is a usage error (exit 3, the outcome contract's tool
    # error) decided before any mode runs.
    if args.print_artifact_slug and args.selftest:
        parser.error(
            "--print-artifact-slug must not be combined with --selftest"
        )
    if args.print_artifact_slug and args.sweep:
        parser.error("--print-artifact-slug must not be combined with --sweep")
    if args.print_artifact_slug and args.pre_round:
        parser.error(
            "--print-artifact-slug must not be combined with --pre-round"
        )
    if args.print_artifact_slug and args.check_review_name:
        parser.error(
            "--print-artifact-slug must not be combined with "
            "--check-review-name"
        )
    if args.print_artifact_slug and not args.plan_path:
        parser.error("plan_path is required when --print-artifact-slug is set")

    compat_error = _check_sibling_compat()
    if compat_error is not None:
        print(f"compatibility FAILED: {compat_error}", file=sys.stderr)
        # Compatibility evidence is about the environment pairing, not the
        # plan: the contract classifies it tool error, never a readiness
        # fail (the final OUTCOME line rides stdout per the convention).
        print("OUTCOME: %s" % OUTCOME_LABELS[3])
        return 3

    if args.selftest:
        return run_selftest()

    if args.print_artifact_slug:
        # Read-only slug print (the execution-claim gateway's derivation
        # seam): the canonical artifact slug through the one ``artifact_slug``
        # SOT function, no review record consultation, no facts resolution.
        # The operand anchors at the process cwd like every mode's plan
        # operand (r4 X5 cwd preference); a missing operand is the
        # missing-input tool error, and a slug outside the kebab shape is
        # the derivation's named refusal (fail), never a traceback.
        _sx = Path(args.plan_path).expanduser()
        if not _sx.is_absolute():
            _sx = Path(os.path.abspath(_sx))
        if not _sx.is_file():
            print(
                f"artifact slug FAILED: plan operand not readable: {_sx}",
                file=sys.stderr,
            )
            print("OUTCOME: %s" % OUTCOME_LABELS[3])
            return 3
        try:
            slug = artifact_slug(_sx)
        except ArtifactSlugRefusal as refusal:
            print(f"artifact slug FAILED: {refusal}", file=sys.stderr)
            print("OUTCOME: %s" % OUTCOME_LABELS[1])
            return 1
        print(slug)
        print("OUTCOME: %s" % OUTCOME_LABELS[0])
        return 0

    root = repo_root(Path.cwd())
    plans_dir_raw = facts_paths.resolve_toml_key_raw(root, "plans_dir")
    reviews_dir_raw = facts_paths.resolve_toml_key_raw(root, "reviews_dir")

    def anchor_at_root(raw: str) -> Path:
        # Tilde-valued facts keys are user-absolute; everything else anchors
        # at the repo ROOT (not the process CWD), so a caller outside the
        # repo root must not false-reject (C1). CWD PREFERENCE (r4 X5): when
        # the raw relative path exists relative to the process cwd, prefer
        # the cwd interpretation BEFORE re-rooting, so a cwd-relative
        # ``..``-containing plan path does not get misleadingly re-rooted at
        # the repo root into a nonexistent path.
        expanded = Path(raw).expanduser() if raw.startswith("~") else Path(raw)
        if expanded.is_absolute():
            return expanded.resolve()
        if expanded.exists():
            return expanded.resolve()
        return (root / expanded).resolve()

    # Single facts resolution (r5 Y5): resolved ONCE here, above the --sweep
    # branch, for both the sweep path (reviews_dir only) and the gate path.
    plans_dir = anchor_at_root(plans_dir_raw) if plans_dir_raw else None
    reviews_dir = anchor_at_root(reviews_dir_raw) if reviews_dir_raw else None

    if args.sweep:
        # --sweep takes no plan operand (r5 Y7): the sweep covers the whole
        # {reviews_dir}; a plan_path alongside it is a caller error.
        if args.plan_path:
            parser.error("plan_path must not be combined with --sweep")
        if reviews_dir is None:
            print(
                "sweep FAILED: cannot resolve reviews_dir from the facts "
                "TOML block",
                file=sys.stderr,
            )
            print("OUTCOME: %s" % OUTCOME_LABELS[1])
            return 1
        return run_sweep(reviews_dir)

    if not args.plan_path:
        parser.error("plan_path is required (or pass --selftest / --sweep)")

    if plans_dir is None or reviews_dir is None:
        print(
            "readiness FAILED: cannot resolve plans_dir/reviews_dir from the "
            "facts TOML block",
            file=sys.stderr,
        )
        print("OUTCOME: %s" % OUTCOME_LABELS[1])
        return 1

    if args.pre_round:
        # Structural-only pre-round gate (plans rule 29): probes over the
        # plan bytes only; the review record is never consulted. The full
        # gate below is untouched (additive branch only). The final OUTCOME
        # line follows the human-readable evidence per the outcome
        # contract.
        rc = run_pre_round(anchor_at_root(args.plan_path), plans_dir)
        print("OUTCOME: %s" % OUTCOME_LABELS[rc])
        return rc

    if args.check_review_name:
        # Name-shape probe: the written round pair must bind to the gate's
        # own discovery shape before the loop folds the round's findings
        # or relaunches. reviews_dir resolves exactly as every other mode
        # resolves it (above); the probe parses only the fields it checks
        # and never runs staging schema validation.
        plan = anchor_at_root(args.plan_path)
        # The round path enters LEXICALLY (anchored like facts values but
        # never symlink-resolved): identity checks must judge the path as
        # claimed, and check_review_name resolves internally for content.
        _rx = Path(args.check_review_name).expanduser()
        if _rx.is_absolute():
            round_path = Path(os.path.abspath(_rx))
        elif _rx.exists():
            round_path = Path(os.path.abspath(_rx))
        else:
            round_path = Path(os.path.abspath(root / _rx))
        ok, reason = check_review_name(plan, round_path, reviews_dir)
        if not ok:
            print(f"review name check FAILED: {reason}", file=sys.stderr)
            print("OUTCOME: %s" % OUTCOME_LABELS[1])
            return 1
        story_slug = feature_slug(plan)
        slug = artifact_slug(plan)
        round_no = (
            review_round_shape(slug)[1].fullmatch(round_path.name).group(1)
        )
        print(
            f"review name check OK: {round_path.name} binds plan slug "
            f"{story_slug} via canonical artifact slug {slug} (r{round_no})"
        )
        print("OUTCOME: %s" % OUTCOME_LABELS[0])
        return 0

    # The plan-path argument anchors like relative facts values: CWD
    # PREFERENCE first (a path that exists relative to the process cwd wins,
    # r4 X5), then re-rooting at the resolved repo ROOT (a caller invoking
    # from a subdirectory or outside the repo must not false-reject a valid
    # relative plan path).
    plan_operand = anchor_at_root(args.plan_path)
    ok, reason = evaluate_readiness(plan_operand, plans_dir, reviews_dir)
    if ok:
        # Warning-only Files:-coverage arm (machinery row
        # script:plan-files-coverage-arm): human-readable stderr evidence
        # printed BEFORE the summary and OUTCOME lines, on this pass path
        # only; any failure path below prints zero coverage lines. A plan
        # whose bytes are undecodable (or unreadable, e.g. a
        # directory-shaped plan operand) skips the arm silently; the arm
        # never changes the exit code and adds no schema field.
        coverage_plan_text: str | None
        try:
            coverage_plan_text = plan_operand.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            coverage_plan_text = None
        if coverage_plan_text is not None:
            for warning in plan_files_coverage_warnings(coverage_plan_text):
                print(warning, file=sys.stderr)
        print("readiness OK: latest review of these plan bytes is ready")
        print("OUTCOME: %s" % OUTCOME_LABELS[0])
        return 0
    if reason is not None and reason.startswith(_GATE_INDETERMINATE_PREFIX):
        # The corrections-graded arm's indeterminate class: the gate ran on
        # repository evidence it could not re-derive, so the run reports
        # the indeterminate outcome and the caller re-derives from disk
        # instead of reading a findings-class fail.
        print(reason, file=sys.stderr)
        print("OUTCOME: %s" % OUTCOME_LABELS[2])
        return 2
    print(f"readiness FAILED: {reason}", file=sys.stderr)
    print("OUTCOME: %s" % OUTCOME_LABELS[1])
    return 1


# --------------------------------------------------------------------------- #
# Selftest: corrections-graded gate (review-cert-graded-binding plan,
# Task 6). Hermetic scratch repos, never the live repo.
# --------------------------------------------------------------------------- #
_CORRECTIONS_SELFTEST_SLUG = "graded-gate-plan"
_CORRECTIONS_SELFTEST_PLAN_NAME = "2026-09-22-graded-gate-plan.md"
_CORRECTIONS_SELFTEST_PLAN_REL = (
    "docs/history/plans/" + _CORRECTIONS_SELFTEST_PLAN_NAME
)
# The em dash is built from an escape at run time: these fixture bytes never
# carry the character itself.
_CORRECTIONS_SELFTEST_D1 = (
    "# P\n\n"
    "## Assumptions\n\n"
    "Decision points requiring a grill: none remain.\n\n"
    "alpha \u2014 bravo.\n"
).encode("utf-8")
_CORRECTIONS_SELFTEST_D2 = (
    "# P\n\n"
    "## Assumptions\n\n"
    "Decision points requiring a grill: none remain.\n\n"
    "alpha, bravo.\n"
).encode("utf-8")


def _corrections_selftest_payload(digest: str) -> dict:
    """A current-v1 clear-review sidecar carrying the graded fields (the
    Task 5 fixture shape): the declared source kind and digest, the round,
    and the artifact slug the certification seal resolves by."""
    payload = vrs._post_window_fixture_payload("plan")
    payload["schema_version"] = 1
    payload["review_type"] = "Branch Review"
    payload["artifact_slug"] = _CORRECTIONS_SELFTEST_SLUG
    payload["round"] = "r1"
    payload["source_kind"] = "plan"
    payload["source_digest"] = digest
    payload["verdict"] = "yes"
    payload["deduplication_groups"] = []
    payload["discarded"] = []
    payload["severity_calibration"] = []
    payload["triage_outcomes"] = []
    payload["soften_watchlist"] = []
    return payload


def _corrections_selftest_row(repo, start: str) -> dict | None:
    """The CLI-produced typography row: the classifier CLI is the only row
    producer, so the selftest mints through the real ``--emit-row``
    subprocess inside the scratch repo and returns None on any failure
    (the caller's check reports the arm, never a traceback)."""
    script = Path(__file__).resolve().parent / "plan_delta_classifier.py"
    try:
        proc = subprocess.run(
            [
                sys.executable, str(script),
                "--plan", str(repo.root / _CORRECTIONS_SELFTEST_PLAN_REL),
                "--since", start,
                "--emit-row",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env=corrections_record.hermetic_git_env(),
        )
    except (subprocess.SubprocessError, OSError):
        return None
    if proc.returncode != 0:
        return None
    rows = [
        line.split(": ", 1)[1]
        for line in proc.stdout.splitlines()
        if line.startswith("corrections-row-json: ")
    ]
    if len(rows) != 1:
        return None
    try:
        row = json.loads(rows[0])
    except json.JSONDecodeError:
        return None
    return row if isinstance(row, dict) else None


def _selftest_corrections_gate(check) -> None:
    """The declared-record path through the shared digest gate
    (review-cert-graded-binding plan, Task 6): a hermetic scratch repo
    carries the committed D1 plan bytes, the round-close commit, the
    on-disk seal entry for the fixture round, and the committed
    typography hop to D2; a CLI-produced row re-binds the stale declared
    digest with no error, and the same repo with the record replaced by a
    declared digest matching the current bytes refuses naming the anchor
    leg (bare rewrite)."""
    cleanup = vrs._GradingCleanup()
    if corrections_record is None:
        check(
            "selftest#corrections_gate/declared_record_passes",
            False,
            "corrections_record.py is not importable next to this copy",
        )
        check(
            "selftest#corrections_gate/bare_rewrite_refuses",
            False,
            "corrections_record.py is not importable next to this copy",
        )
        return
    repo = corrections_record.build_scratch_repo(cleanup)
    plans_dir = repo.root / "docs" / "history" / "plans"
    reviews_dir = repo.root / "docs" / "history" / "reviews"
    plans_dir.mkdir(parents=True)
    reviews_dir.mkdir(parents=True)
    start = repo.commit_file(
        _CORRECTIONS_SELFTEST_PLAN_REL, _CORRECTIONS_SELFTEST_D1, "seed plan"
    )
    close = repo.commit_allow_empty("round 1 close")
    repo.append_seal_entry(
        _CORRECTIONS_SELFTEST_SLUG, 1, _CORRECTIONS_SELFTEST_PLAN_REL,
        start, corrections_record.sha256_hex(_CORRECTIONS_SELFTEST_D1),
        close,
    )
    repo.commit_file(
        _CORRECTIONS_SELFTEST_PLAN_REL, _CORRECTIONS_SELFTEST_D2,
        "fix typography",
    )
    review = reviews_dir / (
        "2026-09-22-plan-review-%s-r1.md" % _CORRECTIONS_SELFTEST_SLUG
    )
    review.write_text(vrs._post_window_fixture_markdown("plan"),
                      encoding="utf-8")
    sidecar = review.with_suffix(".stats.json")

    row = _corrections_selftest_row(repo, start)
    payload = None
    if row is not None:
        payload = _corrections_selftest_payload(
            corrections_record.sha256_hex(_CORRECTIONS_SELFTEST_D1)
        )
        payload["extensions"] = {"corrections": [row]}
        sidecar.write_text(json.dumps(payload), encoding="utf-8")
    plan = plans_dir / _CORRECTIONS_SELFTEST_PLAN_NAME
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#corrections_gate/declared_record_passes",
        row is not None and ok and reason is None,
        f"row={row is not None} ok={ok} reason={reason}",
    )

    # Bare rewrite: the declared digest matches the current bytes while the
    # round-anchored locator resolves the round-start digest.
    if payload is not None:
        del payload["extensions"]
        payload["source_digest"] = corrections_record.sha256_hex(
            _CORRECTIONS_SELFTEST_D2
        )
        sidecar.write_text(json.dumps(payload), encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#corrections_gate/bare_rewrite_refuses",
        payload is not None and not ok and reason is not None
        and reason.startswith(corrections_record.MARKER_PREFIX)
        and "bare rewrite" in reason,
        f"ok={ok} reason={reason}",
    )


# --------------------------------------------------------------------------- #
# Selftest: fixture family through a TEMP tree, never the live repo.
# --------------------------------------------------------------------------- #
def _clear_sidecar(plan_digest: str, source_kind: str = "plan") -> dict:
    """Versionless current-shape clear-review sidecar (schema-passing)."""
    return {
        "panel_mode": "full",
        "selection_reason": None,
        "source_kind": source_kind,
        "source_digest": plan_digest,
        "escalation_reason": None,
        "counts": {"workers_launched": 5, "staged_findings": 0},
        "panel": [
            {
                "worker": worker,
                "lenses": lenses,
                "parent_worker": None,
                "descendant_launches": [],
                "status": "complete",
                "raw": 0,
                "solo": 0,
                "echo": 0,
                "relaunch": False,
            }
            for worker, lenses in (
                ("correctness-completeness", ["quality", "implementation"]),
                ("testing", ["testing"]),
                ("design-simplicity", ["architecture", "simplification"]),
                ("contract-docs", ["documentation"]),
                ("risk", ["security"]),
            )
        ],
        "findings": [],
        "overflow": [],
    }


def _review_markdown(
    verdict: str = "yes",
    blocking_finding: bool = False,
    verdict_line: str | None = None,
) -> str:
    """A realistic plan-review round with a ``## Summary`` verdict.

    ``verdict_line`` overrides the default ``- ready=<verdict>`` bullet to
    exercise other legitimate verdict-line shapes (bare line, trailing
    parenthetical, prose mention).
    """
    findings_body = (
        "### Critical\nNone.\n\n### High\nNone.\n\n"
        "### Medium\nNone.\n\n### Low\nNone.\n"
    )

    if blocking_finding:
        findings_body = (
            "### Critical\nNone.\n\n### High\n\n#### F1. unresolved blocker\n"
            "- **Severity**: High\n"
            "- **Blocking**: true\n"
            "- **Consequence**: plan cannot be executed as written\n"
            "- **Reachability**: expected\n"
            "- **Blast Radius**: single-service\n"
            "- **Confidence**: verified\n"
            "- **Triage**: pending\n\n"
            "#### Comment\n\nThe blocker stands.\n\n"
            "#### Analysis\n\nWorker finding, unrestaged doubt.\n\n"
            "### Medium\nNone.\n\n### Low\nNone.\n"
        )
    summary_verdict = (
        verdict_line if verdict_line is not None else f"- ready={verdict}"
    )
    return (
        "# Plan Review: fixture feature\n\n"
        "## Metadata\n"
        "- Type: Plan Review\n"
        "- Round: r1\n"
        "- Findings: 0\n"
        "- Status: STAGED\n\n"
        "## Summary\n\n"
        "- Counts: Critical 0 | High 0 | Medium 0 | Low 0 | Overflow 0\n"
        "- Blocking findings by id: none\n"
        f"{summary_verdict}\n\n"
        "## Review Statistics\n\n"
        "### Panel\n"
        "| Worker | Lenses | Status | Raw | Solo | Echo | Relaunch | Parent worker |\n"
        "|--------|--------|--------|-----|------|------|----------|--------------|\n"
        "| correctness-completeness | quality, implementation | complete | 0 | 0 | 0 | no | none |\n"
        "| testing | testing | complete | 0 | 0 | 0 | no | none |\n"
        "| design-simplicity | architecture, simplification | complete | 0 | 0 | 0 | no | none |\n"
        "| contract-docs | documentation | complete | 0 | 0 | 0 | no | none |\n"
        "| risk | security | complete | 0 | 0 | 0 | no | none |\n\n"
        "### Counts\n"
        "- Workers launched: 5\n"
        "- Staged findings: 0\n\n"
        "### Triage outcomes\n"
        "Pending triage.\n\n"
        "## Findings\n\n"
        f"{findings_body}\n"
    )


# --------------------------------------------------------------------------- #
# Selftest fixture-runner helpers: one cleanup owner, one fixture writer, and
# per-family fixture runners. run_selftest is only a dispatcher over the
# families; every check name and PASS/FAIL line is byte-identical to the
# pre-extraction monolith.
# --------------------------------------------------------------------------- #
def _clean_reviews_dir(reviews_dir: Path) -> None:
    """Empty the selftest reviews dir between fixtures."""
    for path in reviews_dir.iterdir():
        path.unlink()


def _write_clean_state(
    plans_dir: Path,
    reviews_dir: Path,
    plan_text: str = "# Fixture plan\n\nBody.\n",
    verdict: str = "yes",
    digest_override: str | None = None,
    source_kind: str = "plan",
    blocking: bool = False,
    round_suffix: str = "r1",
    date: str = "2026-09-01",
    slug: str = "fixture-feature",
    verdict_line: str | None = None,
) -> tuple[Path, Path]:
    plan = plans_dir / f"{date}-{slug}.md"
    plan.write_text(plan_text, encoding="utf-8")
    digest = digest_override or vrs.compute_source_digest(
        "plan", plan.read_bytes()
    )
    sidecar = _clear_sidecar(digest, source_kind)
    sidecar["date"] = date
    if blocking:
        sidecar["findings"] = [
            {
                "id": 1,
                "severity": "High",
                "blocking": True,
                "consequence": "plan cannot be executed as written",
                "reachability": "expected",
                "blast_radius": "single-service",
                "confidence": "verified",
            }
        ]
        sidecar["counts"]["staged_findings"] = 1
    review = reviews_dir / (
        f"{date}-plan-review-{slug}-{round_suffix}.md"
    )
    plan_root = repository_root(plan.parent)
    identity = normalize_plan_path(plan, plan_root) if plan_root else None
    identity_line = f"- URL or Artifact: {identity}\n" if identity else ""
    review_markdown = _review_markdown(
        verdict=verdict,
        blocking_finding=blocking,
        verdict_line=verdict_line,
    ).replace("## Metadata\n", "## Metadata\n" + identity_line, 1)
    review.write_text(review_markdown, encoding="utf-8")
    review.with_suffix(".stats.json").write_text(
        json.dumps(sidecar), encoding="utf-8"
    )
    return plan, review


def _selftest_run_cli(plan_arg: Path) -> tuple[int, str, str]:
    return _selftest_run_main([str(plan_arg)])


def _selftest_run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


def _selftest_sidecar_shapes(
    plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Sidecar shape family: missing, malformed, and legacy sidecars."""
    # no_review_files: plan present, no matching review artifact.
    plan = plans_dir / "2026-09-01-fixture-feature.md"
    plan.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#no_review_files",
        not ok and reason is not None and "no review artifact" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # missing_sidecar: latest round Markdown present, no .stats.json.
    plan, review = _write_clean_state(plans_dir, reviews_dir)
    review.with_suffix(".stats.json").unlink()
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#missing_sidecar",
        not ok and reason is not None and "missing stats sidecar" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # malformed_sidecar (invalid JSON arm).
    plan, review = _write_clean_state(plans_dir, reviews_dir)
    review.with_suffix(".stats.json").write_text("{not json", encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#malformed_sidecar/invalid_json",
        not ok and reason is not None and "malformed stats sidecar" in reason,
        f"ok={ok} reason={reason}",
    )
    # legacy_or_unsupported_sidecar (r5 Y1): an explicit-unsupported
    # schema_version never reaches the shared gate's per-field checks;
    # it is rejected by the current-shape requirement with the named
    # legacy/versionless reason.
    review.with_suffix(".stats.json").write_text(
        json.dumps({"schema_version": 99}), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#legacy_or_unsupported_sidecar/schema_version",
        not ok and reason is not None
        and "legacy/versionless" in reason,
        f"ok={ok} reason={reason}",
    )
    # legacy_or_unsupported_sidecar (r5 Y1a): an EMPTY sidecar object
    # classifies pure-legacy (no version, no current markers) — it used
    # to bypass the digest/source_kind checks entirely (fail-open hole);
    # it must now exit 1 with the named reason even beside a clean
    # review and a matching plan.
    review.with_suffix(".stats.json").write_text("{}", encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#legacy_or_unsupported_sidecar/empty_object",
        not ok and reason is not None
        and "legacy/versionless" in reason
        and "source_digest is required" in reason,
        f"ok={ok} reason={reason}",
    )
    # legacy_or_unsupported_sidecar (r5 Y1b): a versionless legacy
    # payload WITHOUT a source_digest (no panel_mode / counts markers)
    # classifies pure-legacy and must be rejected by the shape gate, not
    # silently waved through with no digest to verify.
    review.with_suffix(".stats.json").write_text(
        json.dumps({"source_kind": "plan", "panel": []}), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#legacy_or_unsupported_sidecar/no_source_digest",
        not ok and reason is not None
        and "legacy/versionless" in reason,
        f"ok={ok} reason={reason}",
    )
    # legacy_or_unsupported_sidecar (r5 Y1c, CRITICAL bypass proof):
    # with a legacy sidecar the gate must reject EVEN when the shared
    # gate alone would pass; and after a would-be-ready state, EDITING
    # the plan bytes must STILL exit 1 (the pre-Y1 build exited 0 both
    # times — the bypass is closed).
    review.with_suffix(".stats.json").write_text(
        json.dumps({"legacy": True}), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#legacy_or_unsupported_sidecar/bypass_closed_initial",
        not ok and reason is not None
        and "legacy/versionless" in reason,
        f"ok={ok} reason={reason}",
    )
    plan.write_text("# Fixture plan\n\nBody edited post-review.\n", encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#legacy_or_unsupported_sidecar/bypass_closed_after_edit",
        not ok and reason is not None
        and "legacy/versionless" in reason,
        f"ok={ok} reason={reason}",
    )
    # malformed_sidecar (schema-failing arm: current shape with bad panel).
    # Digest must MATCH the plan bytes so the failure is schema-shaped.
    bad = _clear_sidecar(vrs.compute_source_digest("plan", plan.read_bytes()))
    bad["panel_mode"] = "banana"
    review.with_suffix(".stats.json").write_text(
        json.dumps(bad), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#malformed_sidecar/panel_mode_invalid",
        not ok and reason is not None and "schema validation failed" in reason,
        f"ok={ok} reason={reason}",
    )
    # malformed_sidecar (non-UTF-8 arm): named reason, no traceback.
    review.with_suffix(".stats.json").write_bytes(b"\xff\xfe{not json")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#malformed_sidecar/not_utf8",
        not ok and reason is not None
        and "unreadable or invalid JSON" in reason,
        f"ok={ok} reason={reason}",
    )
    # review artifact itself not valid UTF-8: named reason, no traceback.
    # (Restore a VALID sidecar first so the review read is the failure.)
    review.with_suffix(".stats.json").write_text(
        json.dumps(
            _clear_sidecar(
                vrs.compute_source_digest("plan", plan.read_bytes())
            )
        ),
        encoding="utf-8",
    )
    review.write_bytes(b"# review \xff\xfe binary\n")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_artifact_not_utf8",
        not ok and reason is not None and "not valid UTF-8" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)


def _selftest_source_and_digest(
    plans_dir: Path, reviews_dir: Path, check
) -> None:
    """source_kind and digest classification family."""
    # wrong_source_kind: valid schema, source_kind "code" -> the shared
    # sidecar-gate condition (no ordinal: the shared gate owns the
    # schema/kind/digest sequence; do not renumber against the numbered
    # comments inside evaluate_readiness).
    plan, _ = _write_clean_state(plans_dir, reviews_dir, source_kind="code")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#wrong_source_kind",
        not ok and reason is not None
        and "source_kind is 'code', expected 'plan'" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # r6 Z1: source_kind bypassable by omission/null on versionless
    # current-shape sidecars (the shared gate only checks a DECLARED
    # kind). Both arms must exit 1 with the named reason.
    plan, review = _write_clean_state(plans_dir, reviews_dir)
    missing_kind = _clear_sidecar(
        vrs.compute_source_digest("plan", plan.read_bytes())
    )
    del missing_kind["source_kind"]
    review.with_suffix(".stats.json").write_text(
        json.dumps(missing_kind), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#source_kind_key_deleted",
        not ok and reason is not None
        and "source_kind is missing or not 'plan'" in reason,
        f"ok={ok} reason={reason}",
    )
    null_kind = _clear_sidecar(
        vrs.compute_source_digest("plan", plan.read_bytes())
    )
    null_kind["source_kind"] = None
    review.with_suffix(".stats.json").write_text(
        json.dumps(null_kind), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#source_kind_null",
        not ok and reason is not None
        and "source_kind is missing or not 'plan'" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # valid_schema_wrong_digest: schema passes, digest hashes other bytes.
    plan, review = _write_clean_state(
        plans_dir, reviews_dir, digest_override="a" * 64
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#valid_schema_wrong_digest",
        not ok and reason is not None and "stale" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # Digest reason classification (W4, r3): "stale" is reserved for a
    # MISMATCH; missing or non-hex digests get the distinct
    # "invalid or missing" family; an unrecognized shared-validator digest
    # error gets the fallback wording that embeds the raw error.
    plan, review = _write_clean_state(plans_dir, reviews_dir)
    missing = _clear_sidecar(
        vrs.compute_source_digest("plan", plan.read_bytes())
    )
    del missing["source_digest"]
    review.with_suffix(".stats.json").write_text(
        json.dumps(missing), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#digest_missing_key",
        not ok and reason is not None
        and "invalid or missing" in reason
        and "stale" not in reason,
        f"ok={ok} reason={reason}",
    )

    non_hex = _clear_sidecar("Z" * 64)
    review.with_suffix(".stats.json").write_text(
        json.dumps(non_hex), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#digest_non_hex",
        not ok and reason is not None
        and "invalid or missing" in reason
        and "stale" not in reason,
        f"ok={ok} reason={reason}",
    )

    fallback = digest_failure_reason(
        "current sidecar source_digest failed some future check", 3
    )
    check(
        "selftest#digest_fallback_classification",
        "unrecognized check" in fallback
        and "future check" in fallback,
        f"fallback={fallback!r}",
    )
    _clean_reviews_dir(reviews_dir)

    # stale_digest_after_plan_edit + review edited after validation.
    plan, review = _write_clean_state(plans_dir, reviews_dir)
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#stale_digest_after_plan_edit/initial_pass",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    plan.write_text("# Fixture plan\n\nBody edited.\n", encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#stale_digest_after_plan_edit/plan_edited",
        not ok and reason is not None and "stale" in reason,
        f"ok={ok} reason={reason}",
    )
    # Restore the plan bytes (digest matches again), then edit ONLY the
    # review Markdown after a passing call: the next call must re-read it
    # and fail on the changed verdict.
    plan.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#stale_digest_after_plan_edit/restored_pass",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    review.write_text(
        _review_markdown(verdict="no"), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#stale_digest_after_plan_edit/review_markdown_edited",
        not ok and reason is not None and "ready=yes" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # ready_no_verdict: ready=no with zero blocking findings.
    plan, _ = _write_clean_state(plans_dir, reviews_dir, verdict="no")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#ready_no_verdict",
        not ok and reason is not None and "ready=yes" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)


def _selftest_verdict_grammar(
    plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Verdict precedence and Summary-grammar family."""
    # verdict_field fixtures (Task 3): consumer precedence, sidecar
    # verdict over Summary grammar. Three RED (precedence not
    # implemented yet) + two GREEN characterization (fallback must
    # survive unchanged).
    plan, review = _write_clean_state(plans_dir, reviews_dir)
    sc = _clear_sidecar(vrs.compute_source_digest("plan", plan.read_bytes()))
    sc["verdict"] = "yes"
    review.write_text(
        _review_markdown(
            verdict_line=(
                "Counts confirmed in Review Statistics; the verdict "
                "lives in the sidecar verdict field."
            )
        ),
        encoding="utf-8",
    )
    review.with_suffix(".stats.json").write_text(
        json.dumps(sc), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_field/sidecar_yes_summary_silent_passes",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    plan, review = _write_clean_state(plans_dir, reviews_dir, verdict="yes")
    sc = _clear_sidecar(vrs.compute_source_digest("plan", plan.read_bytes()))
    sc["verdict"] = "no"
    review.with_suffix(".stats.json").write_text(
        json.dumps(sc), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_field/sidecar_no_overrides_summary_yes",
        not ok and reason is not None
        and "sidecar verdict field reports" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    plan, review = _write_clean_state(plans_dir, reviews_dir, verdict="no")
    sc = _clear_sidecar(vrs.compute_source_digest("plan", plan.read_bytes()))
    sc["verdict"] = "yes"
    review.with_suffix(".stats.json").write_text(
        json.dumps(sc), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_field/sidecar_yes_overrides_summary_no",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # legacy_verdict_junk_falls_back (characterization): a
    # non-conforming verdict value neither decides nor fails readiness;
    # the Summary rule runs unchanged.
    plan, review = _write_clean_state(plans_dir, reviews_dir, verdict="yes")
    sc = _clear_sidecar(vrs.compute_source_digest("plan", plan.read_bytes()))
    sc["verdict"] = "maybe"
    review.with_suffix(".stats.json").write_text(
        json.dumps(sc), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_field/legacy_verdict_junk_falls_back/string_arm",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    plan, review = _write_clean_state(plans_dir, reviews_dir, verdict="no")
    sc = _clear_sidecar(vrs.compute_source_digest("plan", plan.read_bytes()))
    sc["verdict"] = {"ready": False}
    review.with_suffix(".stats.json").write_text(
        json.dumps(sc), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_field/legacy_verdict_junk_falls_back/dict_arm",
        not ok and reason is not None
        and "does not report a ready=yes verdict" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # absent_falls_back_to_summary (characterization): no verdict field,
    # Summary decides exactly as today.
    plan, _ = _write_clean_state(plans_dir, reviews_dir, verdict="no")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_field/absent_falls_back_to_summary",
        not ok and reason is not None
        and "does not report a ready=yes verdict" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # verdict_outside_summary_rejects (r5 Y3): a ready=yes token that
    # appears ONLY in ## Findings is not a Summary verdict; the Summary
    # scoping must not silently widen to the whole document.
    plan, review = _write_clean_state(
        plans_dir, reviews_dir, verdict_line="- verdict deferred"
    )
    content = _review_markdown(verdict_line="- verdict deferred")
    content = content.replace(
        "### Low\nNone.\n", "### Low\nNone.\n\nready=yes\n", 1
    )
    review.write_text(content, encoding="utf-8")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_outside_summary_rejects",
        not ok and reason is not None and "ready=yes" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # boundary_violating_mention_rejects (r5 Y4): ``Notready=yes`` is
    # NOT a word-bounded verdict token; as the ONLY Summary mention it
    # must yield no verdict (reject), proving the \b anchors.
    plan, _ = _write_clean_state(
        plans_dir, reviews_dir, verdict_line="- Notready=yes"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#boundary_violating_mention_rejects",
        not ok and reason is not None and "ready=yes" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # verdict_line_shapes (r4 reconciliation, corpus-derived): every
    # shape attested in the LIVE corpus under {reviews_dir} (grounded
    # against real lines before writing fixtures), exercised for
    # ready=yes AND ready=no, under the TOTAL rule: any Summary line
    # with a word-bounded ready=yes/no token is a verdict line, last
    # occurrence wins, and a prose mention IS a verdict.
    corpus_shapes = [
        # bare line (2026-09-04-plan-review-review-doc-digest-scope-fix-r5.md:88)
        "ready=yes",
        # bullet, trailing parenthetical (corpus family default)
        "- ready=yes (clean after r7 folds)",
        # bold verdict, no label (2026-09-02-...-r5-residuals-fixes-r4.md:15)
        "**ready=yes**",
        # bold Verdict label + parenthetical (validator-pass r3:53)
        "**Verdict: ready=yes** (zero unresolved blocking findings).",
        # bullet Verdict label, bold value, dash tail (docs-branch-temp-file-hygiene r3:42)
        "- Verdict: **ready=yes** — zero unresolved blocking findings.",
        # bullet Verdict label, plain value (review-doc-digest-scope-fix r4:17)
        "- Verdict: ready=yes after r3 folds",
        # prose tail sentence (fence-close-rules r5:19)
        "Counts: Critical 0 | High 0 | Medium 0 | Low 0. Blocking findings: none. The plan is ready for execution at this digest. Verdict: ready=yes.",
        # Ready for execution label (corpus family)
        "Ready for execution: ready=yes",
        # bullet label + bold value + parenthetical (review-pointer-wiring-polish r2:7)
        "- Ready for execution: **ready=yes** (zero unresolved blocking findings)",
        # bold ready=yes as prose tail after a period (docs-branch-temp-file-hygiene r3:119)
        "Zero unresolved blocking findings. The plan's diagnosis is accurate and every stated witness reproduces. **ready=yes**.",
        # dash tail after Blocking findings count (fence-scanner-consolidation r2:157)
        "- Blocking findings: 0 — ready=yes",
        # Counts prose with bold verdict and dash tail (docs-branch-temp-file-hygiene r2:17)
        "Counts: **0 Critical | 0 High | 0 Medium | 2 Low**. Blocking findings: **none**. Verdict: **ready=yes** — the plan is ready for execution.",
        # prose mention with no label at all: ACCEPTS under the total rule
        "The panel concludes this plan is ready=yes overall.",
    ]
    for idx, line in enumerate(corpus_shapes):
        plan, _ = _write_clean_state(plans_dir, reviews_dir, verdict_line=line)
        ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
        check(
            f"selftest#verdict_line_shapes/corpus_yes_{idx}",
            ok and reason is None,
            f"line={line!r} ok={ok} reason={reason}",
        )
        _clean_reviews_dir(reviews_dir)

    corpus_no_shapes = [
        # bare ready=no (review-doc-digest-scope-fix r3:91)
        "ready=no",
        # bullet ready=no (phase3-review-churn-control r6:283)
        "- ready=no",
        # bold Verdict label, no (r5-residuals-fixes r2:93)
        "Verdict: **ready=no**",
        # bullet Verdict label + reason (validator-pass r1:17)
        "- Verdict: ready=no (one unresolved blocking finding; fold F1 into the plan and re-run a fresh round).",
        # prose tail ready=no
        "Counts: Critical 0 | High 1. Verdict: ready=no.",
        # dash tail after a nonzero blocking count (fence-scanner-consolidation r3:141)
        "- Blocking findings: 1 (F1) — ready=no",
        # Ready for execution label, no
        "Ready for execution: ready=no",
        # bold ready=no as prose tail after a period
        "One blocker stands unresolved against the current digest. **ready=no**.",
    ]
    for idx, line in enumerate(corpus_no_shapes):
        plan, _ = _write_clean_state(plans_dir, reviews_dir, verdict_line=line)
        ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
        check(
            f"selftest#verdict_line_shapes/corpus_no_{idx}_rejects",
            not ok and reason is not None and "ready=yes" in reason,
            f"line={line!r} ok={ok} reason={reason}",
        )
        _clean_reviews_dir(reviews_dir)

    # last-wins across lines: an earlier ready=yes is overridden by a
    # later ready=no in the same Summary (total rule, per line).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        verdict_line="- ready=yes\n- Verdict: ready=no (one blocker re-confirmed)",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_line_shapes/last_line_wins_no",
        not ok and reason is not None and "ready=yes" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # last-wins in the other direction: an earlier ready=no is rescued
    # by a later canonical ready=yes line.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        verdict_line="- Verdict: ready=no (superseded by the fold below)\nVerdict: ready=yes",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#verdict_line_shapes/last_line_wins_yes",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)


def _selftest_paths_and_blocking(
    root: Path, plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Blocking-finding and plan/reviews path-shape family."""
    # unresolved_blocking_finding: ready=yes, one blocking:true unresolved.
    plan, _ = _write_clean_state(plans_dir, reviews_dir, blocking=True)
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#unresolved_blocking_finding",
        not ok and reason is not None and "is_review_ready" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    outside = root / "outside-plan.md"
    outside.write_text("# outside\n", encoding="utf-8")
    ok, reason = evaluate_readiness(outside, plans_dir, reviews_dir)
    check(
        "selftest#plan_outside_plans_dir",
        not ok and reason is not None and "outside plans_dir" in reason,
        f"ok={ok} reason={reason}",
    )

    ghost = plans_dir / "2026-09-01-ghost.md"
    ok, reason = evaluate_readiness(ghost, plans_dir, reviews_dir)
    check(
        "selftest#missing_plan_path",
        not ok and reason is not None and "does not exist" in reason,
        f"ok={ok} reason={reason}",
    )

    # missing_reviews_dir (r6 Z5): a configured-but-missing reviews_dir
    # on the GATE path gets its own named wiring reason (mirroring the
    # sweep's r5 message), never a misleading "no review artifact".
    wire = plans_dir / "2026-09-01-wire-check.md"
    wire.write_text("# wire check\n", encoding="utf-8")
    ok, reason = evaluate_readiness(
        wire, plans_dir, root / "reviews-gone"
    )
    check(
        "selftest#missing_reviews_dir",
        not ok and reason is not None
        and "configured reviews_dir does not exist on disk" in reason,
        f"ok={ok} reason={reason}",
    )

    # plan_path_is_directory: directory at the plan path gets its own
    # reason, not a misleading "does not exist".
    dir_at_plan = plans_dir / "2026-09-01-not-a-plan.md"
    dir_at_plan.mkdir()
    ok, reason = evaluate_readiness(dir_at_plan, plans_dir, reviews_dir)
    check(
        "selftest#plan_path_is_directory",
        not ok and reason is not None and "not a file" in reason,
        f"ok={ok} reason={reason}",
    )
    dir_at_plan.rmdir()


def _selftest_round_selection(
    plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Round discovery, tie-break, and slug-matching family."""
    # latest_round_selection: r1 clean (newer mtime), r2 not; r2 decides.
    plan, r1 = _write_clean_state(
        plans_dir, reviews_dir, round_suffix="r1", date="2026-09-01"
    )
    digest = vrs.compute_source_digest("plan", plan.read_bytes())
    r2 = reviews_dir / "2026-09-02-plan-review-fixture-feature-r2.md"
    r2.write_text(_review_markdown(verdict="no"), encoding="utf-8")
    r2.with_suffix(".stats.json").write_text(
        json.dumps(_clear_sidecar(digest)), encoding="utf-8"
    )
    # Force r1 to have the NEWER mtime; latest must still be r2.
    future = 4102444800.0  # 2100-01-01
    os.utime(r1, (future, future))
    os.utime(r1.with_suffix(".stats.json"), (future, future))
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#latest_round_selection",
        not ok and reason is not None and "r2" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # case_variant_collision/uppercase_round_suffix (retargeted from
    # uppercase_round_suffix_ignored, W10 r3): the uppercase ``-R2.md``
    # bytes case-fold-match the canonical discovery shape beside the
    # canonical rejecting r1, so the case-variant collision refusal
    # fires by its pinned prefix. The W10 property (an uppercase round
    # suffix cannot rescue a rejecting round) is now carried by this
    # refusal: the run still refuses instead of accepting the uppercase
    # r2's clean verdict.
    plan, _ = _write_clean_state(
        plans_dir, reviews_dir, verdict="no", round_suffix="r1"
    )
    digest = vrs.compute_source_digest("plan", plan.read_bytes())
    upper = reviews_dir / "2026-09-02-plan-review-fixture-feature-R2.md"
    upper.write_text(_review_markdown(verdict="yes"), encoding="utf-8")
    upper.with_suffix(".stats.json").write_text(
        json.dumps(_clear_sidecar(digest)), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#case_variant_collision/uppercase_round_suffix",
        not ok and reason is not None
        and "case-variant round records exist under both" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # latest_round_selection_tie_break (same-N cross-date): two r1
    # artifacts for one slug with different date prefixes; the tie must
    # resolve by (round, filename) order, NEVER by mtime. The
    # earlier-dated artifact and its sidecar are forced to a year-2100
    # mtime so any mtime participation would flip the winner.
    # Arm 1: later-dated ready=no decides -> not-ok mentioning r1.
    plan, _ = _write_clean_state(
        plans_dir, reviews_dir, verdict="yes", round_suffix="r1", date="2026-09-01"
    )
    digest = vrs.compute_source_digest("plan", plan.read_bytes())
    later = reviews_dir / "2026-09-02-plan-review-fixture-feature-r1.md"
    later.write_text(_review_markdown(verdict="no"), encoding="utf-8")
    later.with_suffix(".stats.json").write_text(
        json.dumps(_clear_sidecar(digest)), encoding="utf-8"
    )
    earlier = reviews_dir / "2026-09-01-plan-review-fixture-feature-r1.md"
    future = 4102444800.0  # 2100-01-01
    os.utime(earlier, (future, future))
    os.utime(earlier.with_suffix(".stats.json"), (future, future))
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#latest_round_selection_tie_break/later_dated_decides",
        not ok and reason is not None and "r1" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # Arm 2: inverted polarity — later-dated ready=yes decides -> ok,
    # under the same adversarial mtime on the earlier-dated pair.
    plan, _ = _write_clean_state(
        plans_dir, reviews_dir, verdict="no", round_suffix="r1", date="2026-09-01"
    )
    digest = vrs.compute_source_digest("plan", plan.read_bytes())
    later = reviews_dir / "2026-09-02-plan-review-fixture-feature-r1.md"
    later.write_text(_review_markdown(verdict="yes"), encoding="utf-8")
    later.with_suffix(".stats.json").write_text(
        json.dumps(_clear_sidecar(digest)), encoding="utf-8"
    )
    earlier = reviews_dir / "2026-09-01-plan-review-fixture-feature-r1.md"
    # r1 F4: this arm owns its adversarial mtime constant instead of
    # reusing arm 1's ``future``; removing or reordering arm 1 must
    # fail only this check, not crash the whole selftest with NameError.
    future = 4102444800.0  # 2100-01-01
    os.utime(earlier, (future, future))
    os.utime(earlier.with_suffix(".stats.json"), (future, future))
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#latest_round_selection_tie_break/inverted_polarity_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # glob_metachar_slug (retargeted for the canonical artifact slug): a
    # plan slug containing glob metacharacters (e.g. ``fixture[1]``)
    # lowercases to a non-kebab form, so the gate refuses at the
    # derivation BEFORE any discovery runs; the named refusal carries the
    # plan filename, never a traceback. The escaped-glob property the old
    # arms pinned stays pinned at the discovery helper directly below.
    plan, _ = _write_clean_state(plans_dir, reviews_dir, slug="fixture[1]")
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#glob_metachar_slug/derivation_refusal",
        not ok and reason is not None
        and "cannot derive a canonical artifact slug" in reason
        and plan.name in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # Escaped-glob pin at the helper the gate used to drive: a metachar
    # slug's round is discoverable through the escaped glob, and the
    # escaped pattern never over-matches another plan's rounds.
    _write_clean_state(plans_dir, reviews_dir, slug="fixture[1]")
    found = latest_review_round(reviews_dir, "fixture[1]")
    check(
        "selftest#glob_metachar_slug/escaped_glob_discovers",
        found is not None and found[1] == 1,
        f"found={found}",
    )
    _clean_reviews_dir(reviews_dir)
    _write_clean_state(plans_dir, reviews_dir, slug="fixture-feature")
    found = latest_review_round(reviews_dir, "fixture[1]")
    check(
        "selftest#glob_metachar_slug/escaped_glob_no_overmatch",
        found is None,
        f"found={found}",
    )
    _clean_reviews_dir(reviews_dir)


def _validate_arm(suffix: str, needle: str | None, expect_ok: bool) -> None:
    # r5 F4: the table validates its own needle/polarity pairing, and
    # (r1 F2) a fail-arm needle must have only non-empty "|"-separated
    # parts, else an empty part would satisfy the check vacuously.
    # (r2 F1) both guards are explicit raises so they survive python -O,
    # and needle parts must be non-whitespace, not merely non-empty.
    if (needle is None) != expect_ok:
        raise AssertionError(f"needle/expect_ok polarity mismatch: {suffix}")
    if needle is not None and not all(p.strip() for p in needle.split("|")):
        raise AssertionError(f"empty needle part: {suffix}")


def _selftest_decision_marker(plans_dir: Path, reviews_dir: Path, check) -> None:
    """Decision-points trailer family: gated vs legacy rounds, shapes.

    r4 F6: the standard arms are one tuple-driven table. Each tuple is
    (check-name suffix, plan_text, date, expect_ok, expected reason
    substring or None); the pass/fail assertion distinguishes pass-arms
    (``ok and reason is None``) from fail-arms (``not ok and needle in
    (reason or "")``). Every ``selftest#decision_marker/*`` check name is
    verbatim from the pre-refactor family; the sidecar-mutation arms
    (missing/blank/malformed date) are a second table below (r5 F10: one
    fixture write and one ``mutate(sidecar)`` call per row; r1 F6: the
    decode rows in that family each carry an explicit expect-pass flag
    and the assertion is selected from the row), and the
    fence-boundary comments sit beside their tuples.
    """
    trailer = "Decision points requiring a grill: "

    # Standard arms: (suffix, plan_text, date, expect_ok, needle).
    arms: list[tuple[str, str, str, bool, str | None]] = [
        (
            "gated_none_remain_passes",
            f"# P\n\n## Assumptions\n\n{trailer}none remain.\n",
            "2026-09-08",
            True,
            None,
        ),
        # (r2 F3): the gate accepts
        # the literal none-remain line case-insensitively with an OPTIONAL
        # trailing period.
        (
            "gated_none_remain_lenient_form_passes",
            f"# P\n\n## Assumptions\n\n{trailer}None remain\n",
            "2026-09-08",
            True,
            None,
        ),
        # (r5 F3: multi-needle also pins the
        # 2026-09-08 minimum date behind the gate).
        (
            "gated_missing_trailer_fails",
            "# P\n\nBody.\n",
            "2026-09-08",
            False,
            "missing decision-points trailer"
            "|required for plans reviewed on or after 2026-09-08",
        ),
        (
            "gated_placeholder_trailer_fails",
            f"# P\n\n## Assumptions\n\n{trailer}<point>: <receipt>\n",
            "2026-09-08",
            False,
            "unresolved decision-points trailer",
        ),
        (
            "gated_receipt_passes",
            (
                "# P\n\n## Assumptions\n\n"
                f"{trailer}cleanup scope: ledger-only plan "
                "(user confirmed 2026-09-07)\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r1 F1): all per-point
        # receipts on ONE trailer line (semicolon-separated); one line per
        # point would be ambiguous.
        (
            "gated_multiple_receipts_one_line_passes",
            (
                "# P\n\n## Assumptions\n\n"
                f"{trailer}cleanup scope: ledger-only "
                "(user confirmed 2026-09-07); deployment note: none needed "
                "(sources decide)\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r1 F2): with NO ##
        # Assumptions heading the section extraction is fail-closed
        # (empty), so a trailer line inside ## Notes cannot satisfy the
        # gate.
        (
            "gated_no_assumptions_heading_fails",
            (
                "# P\n\n## Notes\n\n"
                "Decision points requiring a grill: none remain.\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r1 F3): a fenced template quote
        # under ## Assumptions is stripped before matching.
        (
            "trailer_inside_fence_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n```\n"
                "Decision points requiring a grill: none remain.\n"
                "```\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r2 F1): an unterminated fence
        # fails CLOSED. Since the fence-balance gate landed, the FIRST
        # failure is the fence-balance probe naming the opener line (the
        # trailer probe never sees the truncated text anymore); the arm
        # still pins fail-closedness at the same gate entry.
        (
            "trailer_unterminated_fence_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n```\n"
                f"{trailer}none remain.\n"
                "trailer text inside the still-open fence\n"
            ),
            "2026-09-08",
            False,
            "unclosed fence opener at line 7",
        ),
        # (r2 F1): a fenced
        # ``## `` heading line must not truncate the section; a real
        # trailer after the fence still passes.
        (
            "heading_inside_fence_under_assumptions_passes",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n```\n"
                "## Notes\n```\n\n"
                f"{trailer}none remain.\n\n## Gist\n\nBody.\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r1 F6): a value merely
        # STARTING with a placeholder token is unresolved (`TBD for now`
        # used to pass).
        (
            "gated_pending_word_trailer_fails",
            f"# P\n\n## Assumptions\n\n{trailer}TBD for now\n",
            "2026-09-08",
            False,
            "unresolved decision-points trailer",
        ),
        # (r2 F2): a RESOLVED receipt
        # whose first word only STARTS with the placeholder letters
        # (``todo-list ...``) passes.
        (
            "gated_todo_prefixed_receipt_passes",
            (
                "# P\n\n## Assumptions\n\n"
                f"{trailer}todo-list ownership: user takes it "
                "(confirmed 2026-09-07)\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r4 F2, characterization):
        # the hyphen carve-out treats ANY stem-hyphen value as a resolved
        # receipt, so ``tbd-for-now`` passes (the regex cannot tell it
        # from a real receipt without semantics; the boundary is pinned,
        # not perfected).
        (
            "gated_hyphenated_placeholder_passes",
            f"# P\n\n## Assumptions\n\n{trailer}tbd-for-now\n",
            "2026-09-08",
            True,
            None,
        ),
        # a trailer value STARTING with the
        # bare stem ``open:`` is an unresolved open question.
        (
            "gated_open_trailer_fails",
            f"# P\n\n## Assumptions\n\n{trailer}open: phased-rollout decision\n",
            "2026-09-08",
            False,
            "unresolved decision-points trailer",
        ),
        # a mixed mid-interview trailer
        # (a CLOSED receipt plus a semicolon-separated ``open:`` segment)
        # is unresolved; a start-only stem check would miss it.
        (
            "gated_mixed_open_segment_fails",
            (
                "# P\n\n## Assumptions\n\n"
                f"{trailer}rollout: phased (user confirmed 2026-09-08); "
                "open: is the migration coupled\n"
            ),
            "2026-09-08",
            False,
            "unresolved decision-points trailer",
        ),
        # a ``<`` template token is
        # unresolved wherever it sits, including as a later
        # semicolon-separated segment.
        (
            "gated_mixed_template_segment_fails",
            (
                "# P\n\n## Assumptions\n\n"
                f"{trailer}rollout: phased (user confirmed 2026-09-08); "
                "<point>: <receipt>\n"
            ),
            "2026-09-08",
            False,
            "unresolved decision-points trailer",
        ),
        # (characterization): the
        # hyphen carve-out keeps a receipt whose first word is the
        # hyphenated ``open-question`` passing, mirroring the pinned
        # ``todo-list`` receipt.
        (
            "open_question_hyphen_receipt_passes",
            (
                "# P\n\n## Assumptions\n\n"
                f"{trailer}open-question policy: receipts in trailer "
                "(user confirmed 2026-09-08)\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # a round dated before the constant
        # is exempt (no retrofit of already-certified plans).
        (
            "legacy_missing_trailer_passes",
            "# P\n\nBody.\n",
            "2026-09-07",
            True,
            None,
        ),
        # (r3 F1): a later quoted
        # template mention outside ## Assumptions can never satisfy the
        # gate.
        (
            "trailer_outside_assumptions_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n"
                "## Notes\n\nDecision points requiring a grill: none remain.\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r4 F1): an unresolved line
        # above a terminal "none remain." line must not pass on last-wins
        # semantics.
        (
            "ambiguous_two_trailer_lines_fails",
            (
                "# P\n\n## Assumptions\n\n"
                f"{trailer}<point>: <receipt>\n\n{trailer}none remain.\n"
            ),
            "2026-09-08",
            False,
            "ambiguous decision-points trailer",
        ),
        # (r3 F2): a quoted template line inside
        # a TILDE fence (~~~) with an INFO-STRING OPENER (~~~markdown) is
        # stripped like a backtick fence.
        (
            "trailer_tilde_fence_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n~~~markdown\n"
                f"{trailer}none remain.\n"
                "~~~\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r3 F2): a
        # ``` line that is LITERAL TEXT inside a tilde block must not
        # toggle the fence state (single-active-fence-character parser).
        (
            "trailer_after_tilde_block_with_stray_backticks_passes",
            (
                "# P\n\n## Assumptions\n\n~~~\n"
                "quoted template example\n"
                "```\n"
                "~~~\n\n"
                f"{trailer}none remain.\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r5 F6): a stray ```~~~``` line that is LITERAL TEXT inside an open
        # BACKTICK fence must not toggle the fence state
        # (single-active-fence-character parser; cross-character mirror of
        # the stray-backticks-in-tilde-block arm above).
        (
            "trailer_after_backtick_block_with_stray_tildes_passes",
            (
                "# P\n\n## Assumptions\n\n```\n"
                "quoted template\n"
                "~~~\n"
                "more quoted text\n"
                "```\n\n"
                f"{trailer}none remain.\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r3 F3): lookalike
        # tokens with trailing word characters (``todos``) are unresolved.
        (
            "gated_placeholder_lookalike_trailer_fails",
            f"# P\n\n## Assumptions\n\n{trailer}todos\n",
            "2026-09-08",
            False,
            "unresolved decision-points trailer",
        ),
        # (r3 F6): the ``pending``
        # alternative of the placeholder regex has its own witness.
        (
            "gated_pending_placeholder_trailer_fails",
            f"# P\n\n## Assumptions\n\n{trailer}pending user answer\n",
            "2026-09-08",
            False,
            "unresolved decision-points trailer",
        ),
        # (r3 F7):
        # an unterminated fence opening BEFORE ## Assumptions swallows the
        # heading and trailer; pins the strip-before-extract ordering.
        (
            "trailer_swallowed_by_earlier_unterminated_fence_fails",
            (
                "# P\n\n```\nbroken fence\n\n## Assumptions\n\n"
                "Decision points requiring a grill: none remain.\n"
            ),
            "2026-09-08",
            False,
            "unclosed fence opener at line 3",
        ),
        # (r4 F1): a closer line
        # carrying info text (```` ``` note ````) is fence CONTENT, not a
        # closer; CommonMark keeps the fence open, so the REAL trailer
        # after the pseudo-closer stays invisible (r5 F1: the trailer now
        # sits after the pseudo-closer, so a lenient closer regression
        # would expose it and flip this arm red).
        (
            "trailer_inside_close_with_info_text_fails",
            (
                "# P\n\n## Assumptions\n\n```\nquoted template\n``` note\n"
                f"{trailer}none remain.\n"
                "```\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r5 F5): a tilde closer line carrying info text (````` ~~~ end `````)
        # is fence CONTENT, not a closer, so the REAL trailer after the
        # pseudo-closer stays invisible inside the still-open tilde fence
        # (tilde-side twin of the info-text backtick arm above).
        (
            "trailer_inside_tilde_close_with_info_text_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n~~~\nquoted template\n"
                "~~~ end\n"
                f"{trailer}none remain.\n"
                "~~~\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r4 F1): a 3-backtick line does
        # NOT close a 4-backtick opener (closer run must be at least the
        # opener run); the REAL trailer after the pseudo-closer stays
        # inside the open fence (r5 F1: a lenient closer that ignores run
        # length would expose the trailer and flip this arm red).
        (
            "trailer_inside_short_close_fails",
            (
                "# P\n\n## Assumptions\n\n````\nquoted template\n```\n"
                f"{trailer}none remain.\n"
                "````\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r1 overflow F3): a 3-tilde line does NOT close a 4-tilde opener
        # (tilde-side twin of the short-close backtick arm above); it is
        # legal fence content, so the REAL trailer after it stays inside
        # the open fence (a lenient closer that ignores run length would
        # expose the trailer and flip this arm red).
        (
            "trailer_inside_tilde_short_close_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n~~~~\nquoted template\n~~~\n"
                f"{trailer}none remain.\n"
                "~~~~\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r4 F5): a closer
        # line with exactly 4 leading spaces is outside the <=3 indent
        # bound, so the fence stays open and the REAL trailer after the
        # pseudo-closer is invisible; the genuine bare closer later ends
        # the fence (r5 F1: a lenient closer that ignores indent would
        # expose the trailer and flip this arm red).
        (
            "trailer_after_indent_4_closer_stays_fenced",
            (
                "# P\n\n## Assumptions\n\n```\nquoted template\n    ```\n"
                f"{trailer}none remain.\n"
                "```\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r1 overflow F4): a 4-space-indented tilde line is fence CONTENT
        # (indent > 3 can never close; tilde-side twin of the indent-4
        # backtick arm above), so the REAL trailer after it stays inside
        # the open fence (a lenient closer that ignores indent would
        # expose the trailer and flip this arm red). The pseudo-closer
        # carries a FULL-LENGTH (4) tilde run so the run-length rule does
        # not independently block it: the indent gate is the only
        # protection being probed (the plan's Task 3 checkbox was corrected
        # to the full-length run for the same reason — a 3-tilde line is
        # rejected by the run-length rule alone, making the indent-gate
        # mutation probe unable to flip the arm).
        (
            "trailer_after_indent_4_tilde_closer_stays_fenced",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n~~~~\nquoted template\n    ~~~~\n"
                f"{trailer}none remain.\n"
                "~~~~\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r5 F7): a
        # U+2028 embedded after a would-be closer run must not fabricate a
        # parser-line closer (splitlines() used to split on it); the fence
        # stays open and the trailer stays swallowed.
        (
            "trailer_after_unicode_separator_close_stays_fenced",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n```\nquoted template\n"
                "``` \u2028\n"
                f"{trailer}none remain.\n"
                "```\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r5 F8): a backtick
        # opener whose info string contains a backtick is CommonMark
        # paragraph content, not an opener, so the trailer below stays
        # visible.
        (
            "backtick_info_opener_is_paragraph_passes",
            (
                "# P\n\n## Assumptions\n\n```Decision points``` styled text.\n"
                f"{trailer}none remain.\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r1 overflow): a tilde opener keeps accepting ANY info string —
        # the r5 F8 backtick-info rejection must NOT apply to tilde
        # openers (fail-side mirror of the backtick-info paragraph arm
        # above) — so the fence OPENS and the real trailer inside stays
        # swallowed (extending the rejection to tilde openers would close
        # the fence and flip this arm red).
        (
            "trailer_inside_tilde_fence_with_backtick_info_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n~~~x ``` styled\n"
                "quoted template\n"
                f"{trailer}none remain.\n"
                "~~~\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (r5 F8): a leading tab
        # reads as indent >= 4, so the line can never open (or close) a
        # fence and the trailer below stays visible.
        (
            "tab_indented_fence_line_is_content_passes",
            (
                "# P\n\n## Assumptions\n\n\t```\nquoted template\n"
                f"{trailer}none remain.\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
        # (r5 F8): the same tab
        # rule guards the CLOSER direction: the tab-indented line is fence
        # content, the fence stays open, and the real trailer stays
        # swallowed.
        (
            "tab_indented_closer_line_is_content_fails",
            (
                "# P\n\n## Assumptions\n\nNone needed.\n\n```\nquoted template\n"
                "\t```\n"
                f"{trailer}none remain.\n"
                "```\n"
            ),
            "2026-09-08",
            False,
            "missing decision-points trailer",
        ),
        # (characterization, r5 F7): a CRLF plan
        # keeps passing the gate after the split-on-newline line model.
        (
            "crlf_fenced_quote_passes",
            (
                "# P\r\n\r\n## Assumptions\r\n\r\n```\r\nquoted template\r\n"
                "```\r\n\r\n"
                f"{trailer}none remain.\r\n"
            ),
            "2026-09-08",
            True,
            None,
        ),
    ]

    for suffix, plan_text, date, expect_ok, needle in arms:
        _validate_arm(suffix, needle, expect_ok)
        plan, _ = _write_clean_state(
            plans_dir, reviews_dir, plan_text=plan_text, date=date
        )
        ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
        if expect_ok:
            passed = ok and reason is None
        else:
            # Multi-needle convention (r5 F3): a "|"-separated needle must
            # have every part present in the reason.
            passed = not ok and all(n in (reason or "") for n in needle.split("|"))
        check(
            f"selftest#decision_marker/{suffix}",
            passed,
            f"ok={ok} reason={reason}",
        )
        _clean_reviews_dir(reviews_dir)

    # Negative-witness meta-rows (r2-F1 design invariant): each row calls
    # _validate_arm with a malformed arm and asserts its DISTINCT message
    # fires; converting a guard back to a bare ``assert`` loses the
    # message prefix and python -O strips a bare assert entirely, so both
    # regressions flip these rows red.
    meta_arms: list[tuple[str, object, str]] = [
        ("meta_polarity_mismatch_raises", lambda: _validate_arm("meta_probe", None, False), "needle/expect_ok polarity mismatch"),
        ("meta_empty_needle_part_raises", lambda: _validate_arm("meta_probe", "a| |b", False), "empty needle part"),
    ]
    for name, probe, expected in meta_arms:
        message = ""
        try:
            probe()
        except AssertionError as exc:
            message = str(exc)
        check(
            f"selftest#decision_marker/{name}",
            expected in message,
            f"message={message!r}",
        )

    # Sidecar-mutation arms (r5 F10): one (name, mutate) table with
    # a single fixture write and one mutate(sidecar) call per row; every row
    # is an exempt pass-arm (expect_ok=True).
    sidecar_arms: list[tuple[str, object]] = [
        # (characterization, r2 F1): a current-shape sidecar without a
        # date key is exempt from the trailer gate; the schema does not
        # hard-require the field and failing it would retrofit legacy
        # artifacts.
        (
            "sidecar_date_missing_exempt",
            lambda sidecar: sidecar.pop("date"),
        ),
        # (r2 F4): a whitespace-only sidecar date is exempt exactly like
        # a missing one.
        (
            "sidecar_date_blank_exempt",
            lambda sidecar: sidecar.update(date=" "),
        ),
        # (r4 F4): a wrong-shape date (2026-09-08T12:00: valid ISO 8601
        # datetime, not the YYYY-MM-DD shape the guard requires) is exempt
        # like a missing or blank one; a malformed value must not reach the
        # lexicographic gate comparison (r5 F2: the malformed value
        # sorts at/above the 2026-09-08 minimum, so dropping the shape
        # guard would gate the plan and flip this arm).
        (
            "sidecar_date_malformed_exempt",
            lambda sidecar: sidecar.update(date="2026-09-08T12:00"),
        ),
    ]
    for name, mutate in sidecar_arms:
        plan, review = _write_clean_state(
            plans_dir, reviews_dir, plan_text="# P\n\nBody.\n", date="2026-09-08"
        )
        sidecar = json.loads(
            review.with_suffix(".stats.json").read_text(encoding="utf-8")
        )
        mutate(sidecar)
        review.with_suffix(".stats.json").write_text(
            json.dumps(sidecar), encoding="utf-8"
        )
        ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
        check(
            f"selftest#decision_marker/{name}",
            ok and reason is None,
            f"ok={ok} reason={reason}",
        )
        _clean_reviews_dir(reviews_dir)

    # Decode-sharing arms (r2-F2: the plan bytes are decoded ONCE and ONLY
    # when at least one date guard fires): an undecodable plan whose round
    # is date-exempt still passes, while the same undecodable plan under a
    # gated date fails with the decode reason. Both rows overwrite the plan
    # bytes and then refresh source_digest to match, so the stale-digest
    # reason can never mask the decode reason under test. Each row carries
    # an explicit expect-pass flag (r1 F6): the assertion is selected by
    # row identity, not by re-inspecting the mutated sidecar at assertion
    # time.
    decode_arms: list[tuple[str, object, bool]] = [
        ("undecodable_plan_date_exempt_passes", lambda s: s.pop("date"), True),
        ("undecodable_plan_gated_fails", lambda s: None, False),
    ]
    for name, mutate, expect_ok in decode_arms:
        plan, review = _write_clean_state(
            plans_dir, reviews_dir, plan_text="# P\n\nBody.\n", date="2026-09-08"
        )
        sidecar = json.loads(
            review.with_suffix(".stats.json").read_text(encoding="utf-8")
        )
        mutate(sidecar)
        plan.write_bytes(b"\xff\xfe\x00 undecodable")
        sidecar["source_digest"] = vrs.compute_source_digest(
            "plan", plan.read_bytes()
        )
        review.with_suffix(".stats.json").write_text(
            json.dumps(sidecar), encoding="utf-8"
        )
        ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
        # Assertion selected by the row's explicit expect-pass flag
        # (r1 F6): the pass row requires ok with no reason; the fail row
        # requires the decode reason.
        if expect_ok:
            passed = ok and reason is None
        else:
            passed = not ok and "cannot read plan bytes" in (reason or "")
        check(
            f"selftest#decision_marker/{name}",
            passed,
            f"ok={ok} reason={reason}",
        )
        _clean_reviews_dir(reviews_dir)


def _selftest_review_scope(plans_dir: Path, reviews_dir: Path, check) -> None:
    """Review Scope category family: path-kind vs declared category,
    duplicate categories, task-Files inventory coverage, and the
    sidecar-date exemption arms.

    Every fixture plan is dated on or after 2026-09-08, so each carries a
    plain ``Decision points requiring a grill: none remain.`` line inside
    its ``## Assumptions`` section; otherwise the arms would fail on the
    trailer gate instead of exercising the category gate. The gated arms
    use 2026-09-09 (this gate's own minimum), and the below-min exemption
    arm uses 2026-09-08 (above DECISION_MARKER_MIN_DATE but below
    REVIEW_SCOPE_MIN_DATE, so the trailer gate still runs there too).
    """
    trailer = "Decision points requiring a grill: none remain."

    def rs_plan(scope_body: str, tasks_body: str = "") -> str:
        parts = [f"# P\n\n## Assumptions\n\n{trailer}\n"]
        if tasks_body:
            parts.append(f"\n## Tasks\n\n{tasks_body}\n")
        parts.append(f"\n## Review Scope\n\n{scope_body}")
        return "".join(parts)

    # doc_under_documentation_ok: a documentation-suffix path declared
    # under **Documentation:** passes.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan("**Documentation:**\n\n- docs/guide.md\n"),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/doc_under_documentation_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # implementation_under_documentation: an implementation-suffix path
    # declared under **Documentation:** fails; the reason must name the
    # path, the declared category, and the expected category.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan("**Documentation:**\n\n- src/service.py\n"),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/implementation_under_documentation",
        not ok
        and reason is not None
        and "src/service.py" in reason
        and "Documentation" in reason
        and "Production code" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # template_prose_label_implementation_under_documentation: the plans
    # skill Review Scope template's own Documentation label carries
    # same-line guidance prose, so a plan copying the template opens a
    # category block from the label-with-prose line; an
    # implementation-suffix path listed under it must fail check (a)
    # with the category-mismatch reason naming the path and both
    # categories.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:** production code and tests use the"
            " explicit list\n\n- src/service.py\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/"
        "template_prose_label_implementation_under_documentation",
        not ok
        and reason is not None
        and "src/service.py" in reason
        and "Documentation" in reason
        and "Production code" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # template_prose_label_doc_under_documentation_ok: a documentation-
    # suffix path declared under the prose-carrying Documentation label
    # is authoritative and passes (characterization arm; green before
    # and after the grammar fix).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:** production code and tests use the"
            " explicit list\n\n- docs/guide.md\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/template_prose_label_doc_under_documentation_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # duplicate_across_categories: one path under two different category
    # blocks fails with a duplicate-path reason.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- src/service.py\n\n"
            "**Tests:**\n\n- src/service.py\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/duplicate_across_categories",
        not ok
        and reason is not None
        and "duplicate" in reason
        and "src/service.py" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # task_file_missing_from_inventory: a ### Task section whose Files:
    # lists a path the Review Scope section never mentions fails with an
    # omitted-from-inventory reason.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "- [ ] Step one.\n\n"
                "Files:\n\n"
                "- src/missing.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/task_file_missing_from_inventory",
        not ok
        and reason is not None
        and "src/missing.py" in reason
        and "Review Scope" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # extension_only_coverage_ok: a task Files: path that appears only in
    # the plan-related-extension PROSE of the Review Scope section (no
    # category list entry) still counts as inventoried and passes.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n\n"
            "Extensions of this plan in later rounds may also touch "
            "docs/ext/guide.md; those rounds carry their own review.\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "- [ ] Step one.\n\n"
                "Files:\n\n"
                "- docs/ext/guide.md\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/extension_only_coverage_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # sidecar_date_missing_exempt: a VIOLATION plan (implementation path
    # under Documentation) whose sidecar carries no date field is exempt;
    # this arm proves the date guard exists, since the violation-only
    # arms cannot.
    plan, review = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan("**Documentation:**\n\n- src/service.py\n"),
        date="2026-09-09",
    )
    sidecar = json.loads(
        review.with_suffix(".stats.json").read_text(encoding="utf-8")
    )
    del sidecar["date"]
    review.with_suffix(".stats.json").write_text(
        json.dumps(sidecar), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/sidecar_date_missing_exempt",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # sidecar_date_below_min_exempt: the same violation plan with a
    # sidecar dated 2026-09-08 (below REVIEW_SCOPE_MIN_DATE but at the
    # decision-marker minimum) is exempt; no retrofit of
    # already-certified plans.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan("**Documentation:**\n\n- src/service.py\n"),
        date="2026-09-08",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/sidecar_date_below_min_exempt",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # template_files_above_checkboxes_ok (r1 F1): the repo's canonical
    # task layout — Files: block, blank line, then - [x] checkboxes —
    # must NOT bleed the checkboxes into the extracted Files paths.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- docs/guide.md\n"
                "\n"
                "- [x] Record the current HEAD sha before editing.\n"
                "- [ ] Apply the edit.\n"
                "\n"
                "Notes:\n\n- some note\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/template_files_above_checkboxes_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # inline_files_line_ok (r1 F1): an inline "Files: none new (...)"
    # line is prose, not a list opener; the checkboxes after it are
    # never collected.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: Validation only\n\n"
                "- [x] Run the gate.\n"
                "\n"
                "Files: none new (validation only; fixes commit to the "
                "owning file)\n"
                "\n"
                "- [x] Record the current HEAD sha before editing.\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/inline_files_line_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # annotated_implementation_under_documentation (r1 F2): a trailing
    # annotation on the item must not defeat check (a); the reason still
    # names the path, declared category, and expected category.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n"
            "- `src/service.py` *(new; this plan)*\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/annotated_implementation_under_documentation",
        not ok
        and reason is not None
        and "src/service.py" in reason
        and "Documentation" in reason
        and "Production code" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # annotated_task_path_coverage_ok (r1 F2): an annotated task Files
    # entry vs a plain scope entry must count as inventoried.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- `docs/guide.md` *(updated; this plan)*\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/annotated_task_path_coverage_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # doc_config_under_documentation_ok (r1 F3): docs-pipeline config
    # (site.yaml) under a Documentation label passes because config
    # extensions are ABSENT from the implementation table (r1 F3), not
    # because .yaml is a doc suffix (it is not; the doc-suffix authority
    # branch is exercised by the spec-dir arm).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- `site.yaml` *(new; this plan)*\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/doc_config_under_documentation_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # spec_dir_doc_under_documentation_ok (r1 F4): a doc-suffix path
    # under a spec/ directory segment is documentation, not Tests.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- `docs/spec/architecture.md`\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/spec_dir_doc_under_documentation_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # test_path_under_documentation (r1 F6): a test-segment path under a
    # Documentation label fails with a reason naming "Tests".
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- `src/tests/unit.py`\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/test_path_under_documentation",
        not ok
        and reason is not None
        and "src/tests/unit.py" in reason
        and "Tests" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # substring_superstring_not_inventory (r1 F8): a task path that only
    # appears as a substring of a longer different scope path is NOT
    # inventoried (scripts/foo.py vs scripts/foo.py.bak).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- `scripts/foo.py.bak`\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- scripts/foo.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/substring_superstring_not_inventory",
        not ok
        and reason is not None
        and "scripts/foo.py" in reason
        and "omitted from the Review Scope" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # nested_subbullet_not_path_ok (r2 F3): an indented annotation
    # sub-bullet under a Files item is skipped (not collected as a
    # phantom path); sibling top-level items still count.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- docs/guide.md\n"
                "  - updated section anchors only; no new file\n"
                "- [x] done note kept out of Files by the checkbox rule\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/nested_subbullet_not_path_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # directory_scope_entry_covers_ok (r2 F4): a directory entry in a
    # category block covers task Files paths beneath it
    # (component-boundary prefix; the F8 superstring case stays failing).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- docs/guide.md\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/directory_scope_entry_covers_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # directory_slash_polarity_ok (r3 F1): trailing-slash notation drift
    # between the scope entry and the task Files path must not
    # false-reject. Both polarities in one fixture: bare scope token
    # `docs` covers slashed task path `docs/`, and slashed scope token
    # `scripts/` covers bare task path `scripts`.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- docs\n- scripts/\n",
            tasks_body=(
                "### Task 1: Bare scope covers slashed path\n\n"
                "Files:\n\n"
                "- docs/\n\n"
                "### Task 2: Slashed scope covers bare path\n\n"
                "Files:\n\n"
                "- scripts\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/directory_slash_polarity_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # bare_token_boundary_not_covered (r3 F4): a non-slash directory
    # token must NOT cover a longer path that merely shares the token as
    # a string prefix (`scripts` vs `scripts-old/tool.py`); the boundary
    # fails with the omitted-from-inventory reason.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- scripts\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- scripts-old/tool.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/bare_token_boundary_not_covered",
        not ok
        and reason is not None
        and "scripts-old/tool.py" in reason
        and "omitted from the Review Scope" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # uppercase_files_opener_collected (r3 F3, re-keyed per the
    # 2026-10-04 backlog row): the documented grammar opens collection on
    # the exact `Files:` heading only, so an uppercase `FILES:` block is
    # never collected and the review-scope gate passes it vacuously; the
    # refusal comes from the plan-structure gate's declaration-shape
    # check (0) instead. The fixture round is dated on
    # PLAN_STRUCTURE_MIN_DATE so that gate fires; below it the arm
    # passed vacuously (ok=True reason=None), the stale-fixture bug this
    # re-key fixes.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: X\n\n"
                "FILES:\n\n"
                "- src/unlisted.py\n"
            ),
        ),
        date=PLAN_STRUCTURE_MIN_DATE,
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/uppercase_files_opener_collected",
        not ok
        and reason is not None
        and "FILES:" in reason
        and "case variant" in reason
        and PLAN_STRUCTURE_MIN_DATE in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # second_files_block_latched (r3 F3, re-characterized by r1 F1): a
    # later bare `Files:` echo now RE-OPENS collection (r1 F1), but the
    # token it harvests (`word`) is not path-shaped — no slash, no
    # doc/implementation suffix (r4 F2) — so it is dropped and the
    # inventory check still passes; pre-r1-F1 the echo stayed closed.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: X\n\n"
                "Files:\n\n"
                "- docs/guide.md\n\n"
                "Notes: echo\n\n"
                "Files:\n\n"
                "- word\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/second_files_block_latched",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # step_heading_files_collected: a `### Step` section heading carries
    # its own Files: block; pre-fix the `^### Task` scan skips Step
    # headings entirely and the gate passes vacuously.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Step 1: X\n\n"
                "Files:\n\n"
                "- src/unlisted.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/step_heading_files_collected",
        not ok
        and reason is not None
        and "src/unlisted.py" in reason
        and "omitted from the Review Scope" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # task4_heading_files_collected: a `#### Task` section's Files: block
    # is scanned too; pre-fix nothing matches `^### Task` and nothing is
    # collected (the fixture has no `### Task` section anywhere).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "#### Task 1: X\n\n"
                "Files:\n\n"
                "- src/unlisted.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/task4_heading_files_collected",
        not ok
        and reason is not None
        and "src/unlisted.py" in reason
        and "omitted from the Review Scope" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # bare_none_files_item_not_phantom (r4 F2): a bare `- none` item in a
    # Files: list must not tokenize to the phantom path `none` and
    # false-reject check (c).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: X\n\n"
                "Files:\n\n"
                "- docs/guide.md\n"
                "- none\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/bare_none_files_item_not_phantom",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # backticked_space_path_coverage_ok (characterization arm; green
    # before and after): a backticked span carries spaces intact;
    # backticks are the convention for space-bearing paths, so the
    # unbackticked multi-token payload keeps the first-token rule
    # unchanged.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- `my docs/white paper.md`\n",
            tasks_body=(
                "### Task 1: X\n\n"
                "Files:\n\n"
                "- `my docs/white paper.md`\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/backticked_space_path_coverage_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # bare_scope_entry_covers_slashed_task_ok (r3-F1 surviving polarity
    # witness; characterization arm, green before and after): a bare
    # scope entry `scripts` covers a slashed task Files token `scripts/`;
    # the lost mirror direction (slashed scope covering a bare task
    # token) is recorded in the plan's Design Invariants.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- scripts\n",
            tasks_body=(
                "### Task 1: X\n\n"
                "Files:\n\n"
                "- scripts/\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/bare_scope_entry_covers_slashed_task_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # prose_two_spans_not_a_path: a task Files item whose leading content
    # is prose carrying two backticked spans must contribute NO path; the
    # first-span-wins rule made the mid-prose span `docs/a.md` win as a
    # false path and fail the inventory check. The scope text mentions
    # neither docs/a.md nor docs/b.md anywhere, so the raw-text boundary
    # fallback cannot mask the RED.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Documentation:**\n\n- docs/guide.md\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- see `docs/a.md` and also `docs/b.md`\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/prose_two_spans_not_a_path",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # in_tick_annotation_stripped: a parenthesized annotation INSIDE the
    # backticked span must not stay attached to the extracted path; the
    # Production code label is pinned so check (a) stays silent and the
    # arm exercises the inventory check (c).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- src/service.py\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- `src/service.py (new; this plan)`\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/in_tick_annotation_stripped",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # windows_separator_coverage_ok: a backslash-separated task Files
    # path must be covered by a slash-form directory scope entry;
    # separator normalization at extraction makes the downstream
    # comparison see one form.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- scripts/\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- scripts\\service.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/windows_separator_coverage_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # backticked_windows_separator_ok: a backslash path inside a leading
    # backticked span must reach the shared normalization exit (leading-
    # span branch), so a slash-form directory scope entry covers it.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- scripts/\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- `scripts\\service.py`\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/backticked_windows_separator_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # doubled_backtick_span_extracted: a doubled-backtick fence with a
    # trailing annotation extracts as the bare path via the leading-span
    # branch; the annotation never enters the span and the path is
    # covered by its scope entry.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- src/service.py\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- ``src/service.py`` *(new)*\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/doubled_backtick_span_extracted",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # payload_files_line_then_reopen_collects: a payload Files: line
    # closes collection and a later bare Files: line in the same task
    # section re-opens it (r1 F1), so the unlisted path is collected and
    # the inventory check fails naming it. Expects-failure because an
    # ok-arm with an in-scope path cannot detect under-collection.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- src/service.py\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files: none new (validation only)\n\n"
                "Files:\n\n"
                "- src/unlisted.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/payload_files_line_then_reopen_collects",
        not ok
        and reason is not None
        and "src/unlisted.py" in reason
        and "Review Scope" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # second_real_files_block_unlisted_fails: two real Files: blocks in
    # one task section; the second block's unlisted path is collected
    # and must fail the inventory check (no first-block latch).
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- src/service.py\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- src/service.py\n\n"
                "Files:\n\n"
                "- src/unlisted2.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/second_real_files_block_unlisted_fails",
        not ok
        and reason is not None
        and "src/unlisted2.py" in reason
        and "Review Scope" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # heading_boundary_files_after_subheading_ignored: a non-Task
    # subheading inside a task region cuts the region's tail (the
    # #{2,4} boundary), so a Files: block under it is never collected;
    # the arm stays ok. (A `### Step note:` subheading WOULD match the
    # Task|Step scan and open its own collected region.)
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=rs_plan(
            "**Production code:**\n\n- src/service.py\n",
            tasks_body=(
                "### Task 1: Do the thing\n\n"
                "Files:\n\n"
                "- src/service.py\n\n"
                "### Notes: boundary probe\n\n"
                "Files:\n\n"
                "- src/unlisted.py\n"
            ),
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/heading_boundary_files_after_subheading_ignored",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # echo_section_non_path_token_ignored: a second Review Scope echo
    # section's stray Files: line contributes no collected path (the
    # task scan reads only Task|Step heading regions, and the section
    # parser returns only the first block); the arm stays ok.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=(
            f"# P\n\n## Assumptions\n\n{trailer}\n\n"
            "## Tasks\n\n"
            "### Task 1: Do the thing\n\n"
            "Files:\n\n"
            "- src/service.py\n\n"
            "## Review Scope\n\n"
            "**Production code:**\n\n"
            "- src/service.py\n\n"
            "## Review Scope\n\n"
            "Files:\n\n"
            "- src/phantom.md\n"
        ),
        date="2026-09-09",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#review_scope/echo_section_non_path_token_ignored",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)


def _selftest_plan_ownership(
    root: Path, plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Plan-ownership family: duplicate creating task (a),
    consumer-before-owner (b), nonexistent Files path without the
    planned-new marker (c), more than one transition-table heading (d),
    the clean shared-edit and reference-after-owner shapes, test-method
    tokens never ordered, per-check mutation probes, and the two
    sidecar-date gated-wiring arms (before 2026-09-19 exempt, at
    2026-09-19 failing with the gated reason naming the minimum date).

    Direct-call arms pass ``root`` as the repo root and pre-create the
    on-disk witnesses they need under ``root/src``; the gated arms run
    through ``evaluate_readiness`` in the shared temp tree, where the
    wiring's repo-root anchor (``plans_dir.parent``) resolves to ``root``
    because no .git exists above the temp tree.
    """
    trailer = "Decision points requiring a grill: none remain."

    def own_plan(tasks_body: str, extra_sections: str = "") -> str:
        parts = [f"# P\n\n## Tasks\n\n{tasks_body}\n"]
        parts.append(extra_sections)
        return "".join(parts)

    def own_gated_plan(tasks_body: str, scope_body: str) -> str:
        return (
            f"# P\n\n## Assumptions\n\n{trailer}\n\n"
            f"## Tasks\n\n{tasks_body}\n\n## Review Scope\n\n{scope_body}"
        )

    # On-disk witnesses for the direct-call and gated arms: paths listed
    # WITHOUT the planned-new marker must exist under the repo root so
    # the existence check (c) stays silent and each arm trips only its
    # own clause.
    src_dir = root / "src"
    src_dir.mkdir(exist_ok=True)
    for rel in (
        "src/shared.py",
        "src/dup_owner.py",
        "src/gated_new.py",
    ):
        (root / rel).write_text("# witness\n", encoding="utf-8")

    # (a) duplicate creating task: the same path annotated *(new)* in two
    # tasks' Files sections fails, naming the path and both tasks.
    dup_plan = own_plan(
        "### Task 1: Create the module\n\n"
        "- [ ] Write `src/dup_owner.py`.\n\n"
        "Files:\n\n"
        "- src/dup_owner.py *(new)*\n\n"
        "### Task 2: Extend the module\n\n"
        "- [ ] Edit `src/dup_owner.py`.\n\n"
        "Files:\n\n"
        "- src/dup_owner.py *(new)*\n"
    )
    reason = plan_ownership_problem(dup_plan, root)
    check(
        "selftest#plan_ownership/duplicate_creating_task",
        reason is not None
        and "duplicate creating task" in reason
        and "src/dup_owner.py" in reason
        and "Task 1" in reason
        and "Task 2" in reason,
        f"reason={reason}",
    )

    # Mutation (a): removing the second task's *(new)* annotation leaves
    # a sequential shared edit of an existing file; the check stops
    # firing.
    dup_mutated = own_plan(
        "### Task 1: Create the module\n\n"
        "- [ ] Write `src/dup_owner.py`.\n\n"
        "Files:\n\n"
        "- src/dup_owner.py *(new)*\n\n"
        "### Task 2: Extend the module\n\n"
        "- [ ] Edit `src/dup_owner.py`.\n\n"
        "Files:\n\n"
        "- src/dup_owner.py\n"
    )
    reason = plan_ownership_problem(dup_mutated, root)
    check(
        "selftest#plan_ownership/mutation_a_shared_edit_passes",
        reason is None,
        f"reason={reason}",
    )

    # Duplicate ordinals (r1 F6): two DISTINCT sections both numbered
    # "Task 2" annotating the same path are distinct owners (identity is
    # the section position, not the ordinal label), so the
    # duplicate-creation check still fires across the ordinal collision;
    # label-identity mutants would silently pass this shape.
    dup_ordinal_plan = own_plan(
        "### Task 2: Create the module\n\n"
        "- [ ] Write `src/dup_owner.py`.\n\n"
        "Files:\n\n"
        "- src/dup_owner.py *(new)*\n\n"
        "### Task 2: Extend the module\n\n"
        "- [ ] Edit `src/dup_owner.py`.\n\n"
        "Files:\n\n"
        "- src/dup_owner.py *(new)*\n"
    )
    reason = plan_ownership_problem(dup_ordinal_plan, root)
    check(
        "selftest#plan_ownership/duplicate_ordinals_still_distinct_owners",
        reason is not None
        and "duplicate creating task" in reason
        and "src/dup_owner.py" in reason,
        f"reason={reason}",
    )

    # (b) consumer-before-owner: Task 1's checklist references a path
    # whose creating task (the *(new)* record) is a later task.
    cbo_plan = own_plan(
        "### Task 1: Wire the checker\n\n"
        "- [ ] Import `src/later_new.py` and call it.\n\n"
        "Files:\n\n"
        "- src/shared.py\n\n"
        "### Task 2: Create the checker\n\n"
        "- [ ] Write the module.\n\n"
        "Files:\n\n"
        "- src/later_new.py *(new)*\n"
    )
    reason = plan_ownership_problem(cbo_plan, root)
    check(
        "selftest#plan_ownership/consumer_before_owner",
        reason is not None
        and "consumer-before-owner" in reason
        and "src/later_new.py" in reason
        and "Task 1" in reason
        and "Task 2" in reason,
        f"reason={reason}",
    )

    # Mutation (b): removing the later task's creation record (the
    # annotated Files item) leaves the checklist reference unowned;
    # checklist-only references are not existence-checked, so the check
    # stops firing.
    cbo_mutated = own_plan(
        "### Task 1: Wire the checker\n\n"
        "- [ ] Import `src/later_new.py` and call it.\n\n"
        "Files:\n\n"
        "- src/shared.py\n\n"
        "### Task 2: Create the checker\n\n"
        "- [ ] Write the module.\n\n"
        "Files:\n"
    )
    reason = plan_ownership_problem(cbo_mutated, root)
    check(
        "selftest#plan_ownership/mutation_b_unowned_reference_passes",
        reason is None,
        f"reason={reason}",
    )

    # Reference before a later UNANNOTATED listing (r1 F9): a checklist
    # reference in Task 1 to a path that a later task lists WITHOUT the
    # *(new)* marker passes; an unannotated listing is not a creation
    # record, so there is no owner to order against (a marker-ignoring
    # mutant that treats any Files listing as creation would false-trip
    # this legitimate shared-edit shape).
    ref_before_unannotated_plan = own_plan(
        "### Task 1: Wire the checker\n\n"
        "- [ ] Import `src/shared.py` and call it.\n\n"
        "### Task 2: Touch the shared module\n\n"
        "- [ ] Edit the module.\n\n"
        "Files:\n\n"
        "- src/shared.py\n"
    )
    reason = plan_ownership_problem(ref_before_unannotated_plan, root)
    check(
        "selftest#plan_ownership/reference_before_later_unannotated_listing_passes",
        reason is None,
        f"reason={reason}",
    )

    # Ordinal-less sections still order by position (r1 F6): an
    # unnumbered earlier section's checklist reference to a path created
    # in a later unnumbered section trips consumer-before-owner, so the
    # ordering check no longer depends on the Task-ordinal label.
    unnumbered_plan = own_plan(
        "### Task: Wire the checker\n\n"
        "- [ ] Import `src/later_new.py` and call it.\n\n"
        "Files:\n\n"
        "- src/shared.py\n\n"
        "### Task: Create the checker\n\n"
        "- [ ] Write the module.\n\n"
        "Files:\n\n"
        "- src/later_new.py *(new)*\n"
    )
    reason = plan_ownership_problem(unnumbered_plan, root)
    check(
        "selftest#plan_ownership/unnumbered_sections_order_by_position",
        reason is not None
        and "consumer-before-owner" in reason
        and "src/later_new.py" in reason,
        f"reason={reason}",
    )

    # (c) a Files: path that does not exist under the repo root and
    # carries no *(new)* annotation fails, naming the task and path.
    ghost_plan = own_plan(
        "### Task 1: Touch the ghost\n\n"
        "- [ ] Edit `src/ghost.py`.\n\n"
        "Files:\n\n"
        "- src/ghost.py\n"
    )
    reason = plan_ownership_problem(ghost_plan, root)
    check(
        "selftest#plan_ownership/files_path_missing_on_disk",
        reason is not None
        and "does not exist" in reason
        and "src/ghost.py" in reason
        and "Task 1" in reason,
        f"reason={reason}",
    )

    # Mutation (c): adding the planned-new marker to the same item makes
    # it a creation record; the existence check stops firing.
    ghost_mutated = own_plan(
        "### Task 1: Touch the ghost\n\n"
        "- [ ] Edit `src/ghost.py`.\n\n"
        "Files:\n\n"
        "- src/ghost.py *(new)*\n"
    )
    reason = plan_ownership_problem(ghost_mutated, root)
    check(
        "selftest#plan_ownership/mutation_c_annotated_new_passes",
        reason is None,
        f"reason={reason}",
    )

    # (d) more than one heading denoting a transition table fails,
    # naming the headings.
    trans_plan = own_plan(
        "### Task 1: Document the machine\n\n- [ ] Fill the table.\n",
        extra_sections=(
            "## State transition\n\nRows.\n\n"
            "### Transition table for gates\n\nRows.\n"
        ),
    )
    reason = plan_ownership_problem(trans_plan, root)
    check(
        "selftest#plan_ownership/multiple_transition_headings",
        reason is not None
        and "transition" in reason
        and "State transition" in reason
        and "Transition table for gates" in reason,
        f"reason={reason}",
    )

    # Mutation (d): removing the second transition heading leaves one;
    # the check stops firing (this also pins the single-heading pass).
    trans_mutated = own_plan(
        "### Task 1: Document the machine\n\n- [ ] Fill the table.\n",
        extra_sections="## State transition\n\nRows.\n",
    )
    reason = plan_ownership_problem(trans_mutated, root)
    check(
        "selftest#plan_ownership/mutation_d_single_transition_passes",
        reason is None,
        f"reason={reason}",
    )

    # clean_plan_ok: the legitimate shapes all pass together - a shared
    # edit of one existing file listed in two tasks without the marker,
    # a reference-after-owner shape (Task 2 references Task 1's new
    # file), and a test-method token that carries no creation marker and
    # is never ordered.
    clean_plan = own_plan(
        "### Task 1: Create the module\n\n"
        "- [ ] Write `src/new_b.py` and run `test_new_module_passes`.\n\n"
        "Files:\n\n"
        "- src/shared.py\n\n"
        "- src/new_b.py *(new)*\n\n"
        "### Task 2: Verify and extend\n\n"
        "- [ ] Edit `src/shared.py` and re-run `src/new_b.py`.\n\n"
        "Files:\n\n"
        "- src/shared.py\n"
    )
    reason = plan_ownership_problem(clean_plan, root)
    check(
        "selftest#plan_ownership/clean_shared_edit_and_after_owner_ok",
        reason is None,
        f"reason={reason}",
    )

    # method_tokens_not_ordered: checklist references to test-method
    # tokens never trip consumer-before-owner even when a later task
    # creates a witness module (method tokens carry no creation marker;
    # their ordering is an authoring and review duty, not a static one).
    methods_plan = own_plan(
        "### Task 1: Plan the witness\n\n"
        "- [ ] Verify `test_new_checker_passes` and `CheckerTest::new_case`"
        " before the module exists.\n\n"
        "### Task 2: Create the witness module\n\n"
        "- [ ] Write it.\n\n"
        "Files:\n\n"
        "- src/method_witness.py *(new)*\n"
    )
    reason = plan_ownership_problem(methods_plan, root)
    check(
        "selftest#plan_ownership/method_tokens_not_ordered",
        reason is None,
        f"reason={reason}",
    )

    # Gated wiring, before the minimum: the same violating plan (a) with
    # a sidecar dated 2026-09-18 stays exempt.
    gated_scope = "**Production code:**\n\n- src/gated_new.py\n"
    gated_tasks = (
        "### Task 1: Create the module\n\n"
        "- [ ] Write `src/gated_new.py`.\n\n"
        "Files:\n\n"
        "- src/gated_new.py *(new)*\n\n"
        "### Task 2: Extend the module\n\n"
        "- [ ] Edit `src/gated_new.py` again.\n\n"
        "Files:\n\n"
        "- src/gated_new.py *(new)*\n"
    )
    gated_text = own_gated_plan(gated_tasks, gated_scope)
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=gated_text,
        date="2026-09-18",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#plan_ownership/gated_below_min_exempt",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # Gated wiring, at the minimum: the same plan with a sidecar dated
    # 2026-09-19 fails with the gated reason naming the minimum date.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=gated_text,
        date="2026-09-19",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#plan_ownership/gated_at_min_fails",
        not ok
        and reason is not None
        and "duplicate creating task" in reason
        and "required for plans reviewed on or after 2026-09-19" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)


def _selftest_scope_classification(
    plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Scope-classification family: an untagged task checklist item (a),
    a Ship-when-only class tag on a task item (b), a tag value outside
    the four-name vocabulary (c), the first-violation-only ordering, the
    clean both-valid-tags shape with the Ship-when prose exemption, and
    the two sidecar-date gated-wiring arms (before 2026-09-19 exempt, at
    2026-09-19 failing with the gated reason naming the minimum date).

    Direct-call arms call ``scope_classification_problem`` on plan text;
    the gated arms run through ``evaluate_readiness`` in the shared temp
    tree, so their fixtures carry the decision-points trailer and a
    well-formed ## Review Scope section and stay clean under every
    earlier gate (the fixtures carry no ``Files:`` blocks, so the
    plan-ownership probes stay silent and each arm trips only the
    classification clause).
    """
    trailer = "Decision points requiring a grill: none remain."

    def classified_plan(tasks_body: str) -> str:
        return (
            f"# P\n\n## Assumptions\n\n{trailer}\n\n"
            f"## Tasks\n\n{tasks_body}\n\n"
            "## Review Scope\n\n**Production code:**\n\n"
            "- src/classified.py\n"
            "## Ship when\n\n"
            "- Ships only after the vendor export lands "
            "[class: EXTERNAL_RELEASE_GATE].\n"
        )

    # (a) untagged item: the reason names the task and the item text.
    untagged = (
        "### Task 1: Do the thing\n\n"
        "- [ ] Write the module.\n"
    )
    reason = scope_classification_problem(classified_plan(untagged))
    check(
        "selftest#scope_classification/untagged_item",
        reason is not None
        and "no [class:" in reason
        and "Task 1" in reason
        and "Write the module." in reason,
        f"reason={reason}",
    )

    # First-violation-only ordering: the FIRST violating item in document
    # order decides; a later tagged task never surfaces instead.
    partial = (
        "### Task 1: Do the thing\n\n"
        "- [ ] Write the module.\n\n"
        "### Task 2: Verify the thing\n\n"
        "- [ ] Add the test. [class: REPOSITORY_TEST]\n"
    )
    reason = scope_classification_problem(classified_plan(partial))
    check(
        "selftest#scope_classification/first_violation_only",
        reason is not None
        and "Task 1" in reason
        and "Task 2" not in reason,
        f"reason={reason}",
    )

    # (b) Ship-when-only classes on a task checklist item: both names
    # fail; the reason names the tag and the Ship-when prose home.
    for class_name in ("EXTERNAL_RELEASE_GATE", "OPERATIONS_FOLLOW_UP"):
        ship_only = (
            "### Task 1: Wait for the outside world\n\n"
            f"- [ ] Confirm the export landed [class: {class_name}].\n"
        )
        reason = scope_classification_problem(classified_plan(ship_only))
        check(
            "selftest#scope_classification/"
            f"ship_when_only_tag_{class_name.lower()}",
            reason is not None
            and f"[class: {class_name}]" in reason
            and "Ship when" in reason,
            f"reason={reason}",
        )

    # (c) a tag value outside the four-name vocabulary fails and names
    # the offending value.
    unknown = (
        "### Task 1: Do the thing\n\n"
        "- [ ] Write the module. [class: RELEASE_CHECK]\n"
    )
    reason = scope_classification_problem(classified_plan(unknown))
    check(
        "selftest#scope_classification/unknown_tag_value",
        reason is not None
        and "RELEASE_CHECK" in reason
        and "vocabulary" in reason,
        f"reason={reason}",
    )

    # Clean shape: both valid tags across two tasks pass, and the
    # Ship-when prose carrying its class is exempt (a ## section is not
    # a task checklist item).
    clean = (
        "### Task 1: Implement the thing\n\n"
        "- [ ] Write the module. [class: IMPLEMENTATION_REQUIRED]\n\n"
        "### Task 2: Verify the thing\n\n"
        "- [ ] Add the test. [class: REPOSITORY_TEST]\n"
    )
    reason = scope_classification_problem(classified_plan(clean))
    check(
        "selftest#scope_classification/clean_both_valid_tags_ok",
        reason is None,
        f"reason={reason}",
    )

    # Backticked span = quote, not tag: a descriptive `` `[class: ...]` ``
    # mention in an item's prose (the live plan quotes the syntax exactly
    # this way) must not read as a tag; the item's real trailing tag
    # decides.
    quoted_mention = (
        "### Task 1: Describe the convention\n\n"
        "- [ ] Tag every item with `[class: ...]` from the vocabulary."
        " [class: IMPLEMENTATION_REQUIRED]\n"
    )
    reason = scope_classification_problem(classified_plan(quoted_mention))
    check(
        "selftest#scope_classification/backticked_mention_is_quote_ok",
        reason is None,
        f"reason={reason}",
    )

    # Fail-closed mirror: a tag written INSIDE a backticked span is a
    # quote, not a declaration, so the item stays untagged (a).
    quoted_only = (
        "### Task 1: Do the thing\n\n"
        "- [ ] Write the module. `[class: IMPLEMENTATION_REQUIRED]`\n"
    )
    reason = scope_classification_problem(classified_plan(quoted_only))
    check(
        "selftest#scope_classification/backticked_tag_not_a_tag",
        reason is not None
        and "no [class:" in reason
        and "IMPLEMENTATION_REQUIRED" not in reason.split(": ", 1)[0],
        f"reason={reason}",
    )

    # Gated wiring, before the minimum: the same untagged-violation plan
    # with a sidecar dated 2026-09-18 stays exempt.
    violating_text = classified_plan(untagged)
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=violating_text,
        date="2026-09-18",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#scope_classification/gated_below_min_exempt",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # Gated wiring, at the minimum: the same plan with a sidecar dated
    # 2026-09-19 fails with the gated reason naming the minimum date.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=violating_text,
        date="2026-09-19",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#scope_classification/gated_at_min_fails",
        not ok
        and reason is not None
        and "no [class:" in reason
        and "required for plans reviewed on or after 2026-09-19" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # Clean end-to-end: the fully tagged plan passes the gate at the
    # minimum date, so the wiring is not a blanket rejection.
    plan, _ = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=classified_plan(clean),
        date="2026-09-19",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#scope_classification/clean_gated_passes",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)


def _selftest_pre_round(
    root: Path, plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Pre-round family: the structural-only ``--pre-round`` invocation.

    The fixture text mirrors the section order the five structural
    probes read: a ``# Plan:`` title, ``## Assumptions`` closing with
    the plain none-remain trailer line, the ``### Task 1`` section
    (``Files:`` list matching the Review Scope entries, every checklist
    item classified, including the per-task Commit line), and only then
    the ``## Review Scope`` section. The order is load-bearing:
    ``md_section`` ends a ``##`` section only at the next ``## ``
    heading, so a Review Scope section placed before the task section
    swallows it and the path-kind probe misreads the Production-code
    path as Documentation-listed. The composed text is proven clean by
    direct probe calls before any CLI arm runs; the CLI arms pin the
    pre-round exit contract: the five structural probes plus the
    extraction-rule executability parity probes over the derived task
    sections (the tolerated no-review-artifact/missing-sidecar class
    never blocks), a stripped classification tag blocks, and
    ``--pre-round`` composes with neither ``--selftest`` nor ``--sweep``
    (parse-time usage error). The executability fixtures keep the
    reviews dir empty throughout and expect the byte-identical step 9
    labels: the three bounded-evidence envelope grounds over plan files,
    the refusal-path blindness and warning suppression, and the
    unit-level classification and derivation labels over synthetic item
    dicts through the extracted helper.

    Every CLI invocation goes through a local SystemExit-capturing
    wrapper: argparse raises ``SystemExit`` through
    ``_selftest_run_main`` (usage errors, and until the ``--pre-round``
    mode exists its unrecognized-option error too); the wrapper catches
    it and uses ``exc.code`` as the rc. The temp facts block is removed
    on exit so the later CLI family's fresh ``.ai-playbook`` creation
    stays valid.
    """
    trailer = "Decision points requiring a grill: none remain."
    commit_item = (
        "- [ ] Commit: `feat: pre-round structural gate` "
        "[class: IMPLEMENTATION_REQUIRED]"
    )

    def _pre_round_clean_plan_text() -> str:
        return (
            "# Plan: pre-round fixture\n\n"
            f"## Assumptions\n\n{trailer}\n\n"
            "### Task 1: Create the pre-round gate\n\n"
            "Files:\n\n"
            "- scripts/pre_round_gate.py *(new)*\n"
            "- docs/pre-round-gate.md *(new)*\n\n"
            "- [ ] Add the `scripts/pre_round_gate.py` gate behind the "
            "`--pre-round` flag. [class: IMPLEMENTATION_REQUIRED]\n"
            f"{commit_item}\n\n"
            "## Review Scope\n\n"
            "**Production code:**\n\n"
            "- scripts/pre_round_gate.py *(new)*\n\n"
            "**Documentation:**\n\n"
            "- docs/pre-round-gate.md *(new)*\n"
        )

    def run_main(argv: list[str]) -> tuple[int, str, str]:
        # argparse raises SystemExit through _selftest_run_main; the
        # wrapper catches it and uses exc.code as the rc.
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = main(argv)
            except SystemExit as exc:
                rc = exc.code
        return rc, out.getvalue(), err.getvalue()

    plan_text = _pre_round_clean_plan_text()
    plan = plans_dir / "2026-09-01-pre-round-feature.md"
    plan.write_text(plan_text, encoding="utf-8")

    # Fixture proof, direct probe calls (no CLI): the composed text must
    # pass all five structural probes before the CLI arms run.
    probe_reasons = {
        "decision_marker": decision_marker_problem(plan_text),
        "review_scope": review_scope_problem(plan_text),
        "plan_ownership": plan_ownership_problem(
            plan_text, repo_root(plans_dir.parent)
        ),
        "scope_classification": scope_classification_problem(plan_text),
        "anchors_block": anchors_block_problem(plan_text),
    }
    check(
        "selftest#pre_round/fixture_probes_clean",
        not any(probe_reasons.values()),
        f"probe_reasons={probe_reasons}",
    )

    facts_dir = root / ".ai-playbook"
    prev_cwd = os.getcwd()
    os.chdir(root)  # main() anchors facts resolution at the process cwd
    try:
        facts_dir.mkdir(exist_ok=True)
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )

        # structural_only_pass: the clean fixture plan passes the
        # structural-only invocation; the review record is not consulted.
        rc, out, err = run_main(["--pre-round", str(plan)])
        check(
            "selftest#pre_round/structural_only_pass",
            rc == 0 and "readiness PRE-ROUND OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # missing_sidecar_tolerated: with an emptied reviews dir the
        # no-review-artifact class never blocks the pre-round invocation,
        # while the full gate over the same tree fails on it.
        _clean_reviews_dir(reviews_dir)
        pre_round_rc, pre_out, pre_err = run_main(
            ["--pre-round", str(plan)]
        )
        full_rc, full_out, full_err = run_main([str(plan)])
        check(
            "selftest#pre_round/missing_sidecar_tolerated",
            pre_round_rc == 0
            and full_rc == 1
            and "no review artifact" in full_err,
            f"pre_round_rc={pre_round_rc} pre_out={pre_out!r} "
            f"pre_err={pre_err!r} full_rc={full_rc} "
            f"full_err={full_err!r}",
        )

        # structural_failure_blocking: the per-task Commit checklist line
        # stripped of its classification tag blocks with the
        # classification-tag problem named on stderr.
        broken_text = plan_text.replace(
            commit_item,
            "- [ ] Commit: `feat: pre-round structural gate`",
        )
        broken_problem = scope_classification_problem(broken_text)
        plan.write_text(broken_text, encoding="utf-8")
        rc, out, err = run_main(["--pre-round", str(plan)])
        check(
            "selftest#pre_round/structural_failure_blocking",
            broken_problem is not None
            and "no [class:" in broken_problem
            and rc == 1
            and "readiness PRE-ROUND FAILED" in err
            and "classification tag" in err,
            f"rc={rc} probe={broken_problem!r} err={err!r}",
        )

        # mutual_exclusion: --pre-round composes with neither --selftest
        # nor --sweep; both combinations are parse-time usage errors
        # (exit 3, the outcome contract's tool error, naming the invalid
        # combination).
        rc, out, err = run_main(["--pre-round", str(plan), "--selftest"])
        selftest_mix = (rc, err)
        rc, out, err = run_main(["--pre-round", str(plan), "--sweep"])
        sweep_mix = (rc, err)
        check(
            "selftest#pre_round/mutual_exclusion",
            selftest_mix[0] == 3
            and "--pre-round must not be combined with --selftest"
            in selftest_mix[1]
            and sweep_mix[0] == 3
            and "--pre-round must not be combined with --sweep"
            in sweep_mix[1],
            f"selftest_mix={selftest_mix!r} sweep_mix={sweep_mix!r}",
        )

        # budget_warning_nonblocking: an over-budget header line emits one
        # stderr warning naming the breached cap without changing the OK
        # line, the OUTCOME line, or the exit code (the warning class
        # never blocks).
        budget_text = _pre_round_clean_plan_text().replace(
            "# Plan: pre-round fixture\n\n",
            "# Plan: pre-round fixture\n\n"
            "Execution budget: 4.0h total, largest task 1.0h\n\n",
            1,
        )
        plan.write_text(budget_text, encoding="utf-8")
        rc, out, err = run_main(["--pre-round", str(plan)])
        check(
            "selftest#pre_round/budget_warning_nonblocking",
            rc == 0
            and "readiness PRE-ROUND OK" in out
            and "OUTCOME: pass" in out
            and err.count("readiness PRE-ROUND WARNING:") == 1
            and "exceeds the 3.0h plan cap" in err,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # --- Extraction-rule executability parity family (pre-round-gate-
        # dimension-parity plan, Task 1): the full gate's plan-private step
        # 9 probes run at pre-round over the plan bytes alone. Every
        # fixture keeps the reviews dir EMPTY (review-record blindness by
        # construction), and the expected refusal labels are built through
        # the SAME single-homed wrap scripts/test_plan_readiness.py's
        # ExtractionRuleParityTest replicates, so a label here is
        # byte-identical to step 9's by construction.
        _clean_reviews_dir(reviews_dir)

        def _exec_fixture_plan(criteria_lines: str, budget_line: str = "") -> str:
            return (
                "# Plan: pre-round executability fixture\n\n"
                f"{budget_line}"
                f"## Assumptions\n\n{trailer}\n\n"
                "### Task 1: Create the pre-round gate\n\n"
                "Files:\n\n"
                "- scripts/pre_round_gate.py *(new)*\n"
                "- docs/pre-round-gate.md *(new)*\n\n"
                f"{criteria_lines}"
                f"{commit_item}\n\n"
                "## Review Scope\n\n"
                "**Production code:**\n\n"
                "- scripts/pre_round_gate.py *(new)*\n\n"
                "**Documentation:**\n\n"
                "- docs/pre-round-gate.md *(new)*\n"
            )

        def _exec_task_criteria(fixture_text: str) -> list[str]:
            section_body = _plan_task_sections(fixture_text)[0][1]
            criteria, _actions = runtime_capabilities.derive_plan_checklist_actions(
                section_body
            )
            return criteria

        def _exec_named_label(criteria: list[str]) -> str:
            # The create boundary's task-attributed wrap over the bare
            # single-homed refusal (mirrors ExtractionRuleParityTest's
            # _named_evidence_label replica).
            try:
                runtime_capabilities.evidence_criterion_ids(list(criteria))
            except ValueError as error:
                from execute_plan_runtime import _named_evidence_limit_error

                return str(
                    _named_evidence_limit_error(
                        {"task-1": {"required_criteria": list(criteria)}},
                        error,
                    )
                )
            raise AssertionError("fixture criteria must exceed an evidence limit")

        # item_bytes_shared_ground: the shared-module probe refuses the
        # exact criterion the fixture plan derives, and the task-attributed
        # wrap embeds that bare ground (the gap's both halves at unit
        # level; holds before and after the pre-round wiring).
        item_criterion = "x" * 600 + " [class: IMPLEMENTATION_REQUIRED]"
        item_text = _exec_fixture_plan(f"- [ ] {item_criterion}\n")
        item_criteria = _exec_task_criteria(item_text)
        item_label = _exec_named_label(item_criteria)
        try:
            runtime_capabilities.evidence_criterion_ids(list(item_criteria))
            item_bare = None
        except ValueError as error:
            item_bare = str(error)
        check(
            "selftest#pre_round/executability_item_bytes_shared_ground",
            item_criteria == [item_criterion]
            and item_bare is not None
            and "evidence criterion exceeds UTF-8 item byte limit" in item_bare
            and item_label.startswith(f"task 'task-1': {item_bare}"),
            f"criteria_len={len(item_criteria)} bare={item_bare!r} "
            f"label_head={item_label[:120]!r}",
        )

        # executability_item_bytes_refused: the over-cap item fixture must
        # fail --pre-round with the byte-identical named envelope label
        # (today's tree passes it clean: the witnessed gap this family
        # pins).
        exec_plan = plans_dir / "2026-09-01-pre-round-over-cap.md"
        exec_plan.write_text(item_text, encoding="utf-8")
        rc, out, err = run_main(["--pre-round", str(exec_plan)])
        check(
            "selftest#pre_round/executability_item_bytes_refused",
            rc == 1
            and "readiness PRE-ROUND FAILED:" in err
            and item_label in err,
            f"rc={rc} out={out!r} err_head={err[:300]!r}",
        )

        # executability_aggregate_bytes_refused: nine sub-cap criteria
        # (458 y's plus the tag keeps every item under the 512-byte cap)
        # whose aggregate breaches the 4096-byte cap refuse with their own
        # named ground, byte-identical to step 9's.
        aggregate_criteria = [
            f"c{index}-" + "y" * 458 + " [class: IMPLEMENTATION_REQUIRED]"
            for index in range(9)
        ]
        aggregate_text = _exec_fixture_plan(
            "".join(f"- [ ] {criterion}\n" for criterion in aggregate_criteria)
        )
        aggregate_label = _exec_named_label(_exec_task_criteria(aggregate_text))
        exec_plan = plans_dir / "2026-09-01-pre-round-over-aggregate.md"
        exec_plan.write_text(aggregate_text, encoding="utf-8")
        rc, out, err = run_main(["--pre-round", str(exec_plan)])
        check(
            "selftest#pre_round/executability_aggregate_bytes_refused",
            rc == 1
            and "readiness PRE-ROUND FAILED:" in err
            and "evidence criteria exceed UTF-8 aggregate byte limit" in err
            and aggregate_label in err,
            f"rc={rc} out={out!r} err_head={err[:300]!r}",
        )

        # executability_criteria_count_refused: 101 short criteria breach
        # the receipt item-count limit (the count check precedes the
        # aggregate check inside the single-homed probe, so the count
        # ground is the named refusal) and refuse with their own named
        # ground, byte-identical to step 9's.
        count_criteria = [
            f"criterion-{index:03d}" + " [class: IMPLEMENTATION_REQUIRED]"
            for index in range(101)
        ]
        count_text = _exec_fixture_plan(
            "".join(f"- [ ] {criterion}\n" for criterion in count_criteria)
        )
        count_label = _exec_named_label(_exec_task_criteria(count_text))
        exec_plan = plans_dir / "2026-09-01-pre-round-over-count.md"
        exec_plan.write_text(count_text, encoding="utf-8")
        rc, out, err = run_main(["--pre-round", str(exec_plan)])
        check(
            "selftest#pre_round/executability_criteria_count_refused",
            rc == 1
            and "readiness PRE-ROUND FAILED:" in err
            and "evidence criteria exceed receipt item-count limit" in err
            and count_label in err,
            f"rc={rc} out={out!r} err_head={err[:300]!r}",
        )

        # executability_review_blindness: safety witness over the same
        # over-cap plan with an emptied reviews home; the refusal names
        # the envelope label without any review record or sidecar in
        # existence, and the run writes none.
        _clean_reviews_dir(reviews_dir)
        exec_plan = plans_dir / "2026-09-01-pre-round-over-cap.md"
        rc, out, err = run_main(["--pre-round", str(exec_plan)])
        check(
            "selftest#pre_round/executability_review_blindness",
            rc == 1
            and "readiness PRE-ROUND FAILED:" in err
            and item_label in err
            and not any(reviews_dir.iterdir()),
            f"rc={rc} reviews={sorted(p.name for p in reviews_dir.iterdir())} "
            f"err_head={err[:300]!r}",
        )

        # executability_conforming_ok: a conforming plan still prints the
        # OK line with its "(review record not consulted)" suffix.
        conforming_text = _exec_fixture_plan(
            "- [ ] Add the `scripts/pre_round_gate.py` gate behind the "
            "`--pre-round` flag. [class: IMPLEMENTATION_REQUIRED]\n"
        )
        exec_plan = plans_dir / "2026-09-01-pre-round-exec-conforming.md"
        exec_plan.write_text(conforming_text, encoding="utf-8")
        rc, out, err = run_main(["--pre-round", str(exec_plan)])
        check(
            "selftest#pre_round/executability_conforming_ok",
            rc == 0
            and "readiness PRE-ROUND OK: structural checks clean "
            "(review record not consulted)" in out
            and "OUTCOME: pass" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # executability_failure_path_no_warnings: on the refusal path the
        # budget-warning loops never ran; the failing fixture carries an
        # over-budget header line, so an emitted warning would be visible
        # and the count stays zero.
        suppressed_text = _exec_fixture_plan(
            f"- [ ] {item_criterion}\n",
            budget_line="Execution budget: 4.0h total, largest task 1.0h\n\n",
        )
        exec_plan = plans_dir / "2026-09-01-pre-round-exec-suppressed.md"
        exec_plan.write_text(suppressed_text, encoding="utf-8")
        rc, out, err = run_main(["--pre-round", str(exec_plan)])
        check(
            "selftest#pre_round/executability_failure_path_no_warnings",
            rc == 1
            and "readiness PRE-ROUND FAILED:" in err
            and item_label in err
            and err.count("readiness PRE-ROUND WARNING:") == 0,
            f"rc={rc} err_head={err[:300]!r}",
        )

        # executability_unit_parity: the extracted helper over synthetic
        # item dicts (the three classification shapes mirror
        # test_classification_labels_unit_parity; the two derivation shapes
        # are seeding-shape grounds no plan text can express) returns
        # classification and derivation labels byte-identical to step 9's.
        executability_prefix = (
            "plan fails the executability contract the create boundary "
            "enforces at Phase 0: "
        )

        def _step9_label(refuse):
            try:
                refuse()
            except ValueError as error:
                return executability_prefix + str(error)
            raise AssertionError("synthetic item must refuse")

        synthetic_items = []
        for item in (
            {"task_body": "- [ ] do a thing\n", "checklist_actions": None},
            {
                "task_body": "- [ ] do a thing\n",
                "checklist_actions": [{"text": "other", "owner": "worker"}],
            },
            {
                "task_body": "",
                "checklist_actions": [{"text": "", "owner": "worker"}],
            },
        ):
            synthetic_items.append(
                (
                    item,
                    lambda item=item: runtime_capabilities.check_checklist_action_classification(
                        "task-1", item
                    ),
                )
            )
        for item in (
            {
                "task_body": "",
                "checklist_actions": [{"text": "Commit:", "owner": "worker"}],
                "required_criteria": ["do a thing"],
            },
            {
                "task_body": "",
                "checklist_actions": [{"text": "do a thing", "owner": "parent"}],
                "required_criteria": ["do a thing"],
            },
        ):
            synthetic_items.append(
                (
                    item,
                    lambda item=item: runtime_capabilities.derive_checklist_actions(
                        "task-1", item
                    ),
                )
            )
        # RED tolerance: until the helper lands, the sentinel string keeps
        # this check failing (never raising) against today's tree.
        extraction_helper = globals().get(
            "extraction_rule_executability_problem"
        )
        unit_problems = [
            (
                extraction_helper(derived_task_map={"task-1": item})
                if extraction_helper is not None
                else "extraction_rule_executability_problem is not defined"
            )
            for item, _refuse in synthetic_items
        ]
        unit_expected = [_step9_label(refuse) for _item, refuse in synthetic_items]
        check(
            "selftest#pre_round/executability_unit_parity",
            unit_problems == unit_expected,
            f"problems={unit_problems!r} expected={unit_expected!r}",
        )
    finally:
        os.chdir(prev_cwd)
        # Leave no facts block behind: the CLI family below creates
        # .ai-playbook fresh (plain mkdir, no exist_ok).
        facts_md = facts_dir / "facts.md"
        if facts_md.exists():
            facts_md.unlink()
        if facts_dir.is_dir() and not any(facts_dir.iterdir()):
            facts_dir.rmdir()



_PROBE_GATE_PATH = "scripts/pre_round_gate.py"


def _anchors_fixture_plan(task_one_block: str, extra_tasks: str = "") -> str:
    """A structurally clean single-task plan whose Task 1 carries the
    given anchors block text ("" for blockless); extra_tasks appends
    further raw task sections."""
    trailer = "Decision points requiring a grill: none remain."
    return (
        "# Plan: anchors fixture\n\n"
        f"## Assumptions\n\n{trailer}\n\n"
        "### Task 1: Create the pre-round gate\n\n"
        "Files:\n\n"
        f"- {_PROBE_GATE_PATH} *(new)*\n"
        "- docs/pre-round-gate.md *(new)*\n\n"
        f"{task_one_block}"
        "- [ ] Add the `scripts/pre_round_gate.py` gate behind the "
        "`--pre-round` flag. [class: IMPLEMENTATION_REQUIRED]\n"
        "- [ ] Commit: `feat: pre-round structural gate` "
        "[class: IMPLEMENTATION_REQUIRED]\n\n"
        f"{extra_tasks}"
        "## Review Scope\n\n"
        "**Production code:**\n\n"
        f"- {_PROBE_GATE_PATH} *(new)*\n\n"
        "**Documentation:**\n\n"
        "- docs/pre-round-gate.md *(new)*\n"
        "- docs/second-task.md *(new)*\n"
    )


_CONFORMING_BLOCK = (
    "Primary class anchors:\n"
    "- `PreRoundGate` in `scripts/pre_round_gate.py`, the new gate module\n\n"
)
_PROSE_BLOCK = (
    "Primary class anchors:\n"
    "- The pre-round gate dispatch-mode paragraph in "
    "scripts/pre_round_gate.py\n\n"
)


def _selftest_anchors_block(
    root: Path, plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Anchors-block grammar probe family (primary-class-anchors-grammar-
    drift plan Task 1): the pre-round refusal of a prose-form block, the
    conforming/blockless/blank-line-boundary passes, the fenced-example
    and non-task-section ignorals, the second-section enumeration, and
    the full gate's unchanged posture over a prose-form fixture."""
    import contextlib
    import io
    import os

    def run_main(argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = main(argv)
            except SystemExit as exc:
                rc = exc.code
        return rc, out.getvalue(), err.getvalue()

    facts_dir = root / ".ai-playbook"
    prev_cwd = os.getcwd()
    os.chdir(root)
    try:
        facts_dir.mkdir(exist_ok=True)
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )

        def pre_round(text: str, name: str):
            plan = plans_dir / name
            plan.write_text(text, encoding="utf-8")
            return run_main(["--pre-round", str(plan)])

        # prose_form_refused: the pre-round invocation refuses with the
        # canonical shape named.
        rc, out, err = pre_round(
            _anchors_fixture_plan(_PROSE_BLOCK), "2026-09-01-anchors-prose.md"
        )
        check(
            "selftest#anchors_block/prose_form_refused",
            rc == 1
            and "readiness PRE-ROUND FAILED:" in err
            and "The pre-round gate dispatch-mode paragraph" in err
            and plan_shape.PRIMARY_CLASS_ANCHOR_SHAPE in err,
            f"rc={rc} err={err!r}",
        )

        # conforming_accepted: every entry conforming passes clean.
        rc, out, err = pre_round(
            _anchors_fixture_plan(_CONFORMING_BLOCK),
            "2026-09-01-anchors-conforming.md",
        )
        check(
            "selftest#anchors_block/conforming_accepted",
            rc == 0 and "readiness PRE-ROUND OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # blockless_unaffected: no anchors block behaves as before.
        rc, out, err = pre_round(
            _anchors_fixture_plan(""), "2026-09-01-anchors-blockless.md"
        )
        check(
            "selftest#anchors_block/blockless_unaffected",
            rc == 0 and "readiness PRE-ROUND OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # blank_line_boundary: checkboxes after the block's blank line
        # are criteria, never anchor entries.
        boundary_block = (
            "Primary class anchors:\n"
            "- `PreRoundGate` in `scripts/pre_round_gate.py`\n\n"
        )
        rc, out, err = pre_round(
            _anchors_fixture_plan(boundary_block),
            "2026-09-01-anchors-boundary.md",
        )
        check(
            "selftest#anchors_block/blank_line_boundary",
            rc == 0 and "readiness PRE-ROUND OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # fenced_example_section_ignored: a FULL `### Task 2:` example
        # section fenced inside Task 1 is never an enumerated ordinal,
        # exactly as create never requests it.
        fenced_task2 = (
            "```text\n"
            "### Task 2: Example only\n\n"
            "Primary class anchors:\n"
            "- The example paragraph in scripts/elsewhere.py\n\n"
            "- [ ] Not a real task [class: IMPLEMENTATION_REQUIRED]\n"
            "```\n\n"
        )
        rc, out, err = pre_round(
            _anchors_fixture_plan(_CONFORMING_BLOCK, fenced_task2),
            "2026-09-01-anchors-fenced-task2.md",
        )
        check(
            "selftest#anchors_block/fenced_example_section_ignored",
            rc == 0 and "readiness PRE-ROUND OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # fenced_block_inside_task_refused: an anchors block quoted in a
        # fence INSIDE a real task section is read raw (the inherited
        # fence-blindness, parity with create) and refuses. The quoted
        # block is the section's only anchors-shaped content: the shared
        # block loop ends at the first blank line or non-bullet line, so
        # a block quoted after a real block's blank line is never read
        # (on either surface).
        fenced_block = (
            "```text\n"
            "Primary class anchors:\n"
            "- The quoted paragraph in scripts/elsewhere.py\n"
            "```\n\n"
        )
        rc, out, err = pre_round(
            _anchors_fixture_plan(fenced_block),
            "2026-09-01-anchors-fenced-block.md",
        )
        check(
            "selftest#anchors_block/fenced_block_inside_task_refused",
            rc == 1 and "readiness PRE-ROUND FAILED:" in err,
            f"rc={rc} err={err!r}",
        )

        # non_task_section_ignored: an anchors-shaped block under a `## `
        # section is never parsed (create never reads that section).
        stray = (
            "## Notes\n\n"
            "Primary class anchors:\n"
            "- The stray paragraph in scripts/elsewhere.py\n\n"
        )
        rc, out, err = pre_round(
            _anchors_fixture_plan(_CONFORMING_BLOCK).replace(
                "## Review Scope", stray + "## Review Scope"
            ),
            "2026-09-01-anchors-non-task.md",
        )
        check(
            "selftest#anchors_block/non_task_section_ignored",
            rc == 0 and "readiness PRE-ROUND OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # second_section_enumeration: only the second task's block is
        # malformed; the refusal names that section's entry.
        task2_bad = (
            "### Task 2: Second task\n\n"
            "Files:\n\n"
            "- docs/second-task.md *(new)*\n\n"
            "Primary class anchors:\n"
            "- The second-task paragraph in scripts/pre_round_gate.py\n\n"
            "- [ ] Do the second thing [class: IMPLEMENTATION_REQUIRED]\n"
            "- [ ] Commit: `feat: second` [class: IMPLEMENTATION_REQUIRED]\n\n"
        )
        rc, out, err = pre_round(
            _anchors_fixture_plan(_CONFORMING_BLOCK, task2_bad),
            "2026-09-01-anchors-second-section.md",
        )
        check(
            "selftest#anchors_block/second_section_enumeration",
            rc == 1
            and "Task 2" in err
            and "The second-task paragraph" in err,
            f"rc={rc} err={err!r}",
        )

        # subsection_read_through: anchors content under a `#### `
        # subsection heading inside a task section stays inside the
        # section span, so the shared parser still reads (and refuses) it.
        rc, out, err = pre_round(
            _anchors_fixture_plan(_PROSE_BLOCK).replace(
                "Primary class anchors:",
                "#### Notes\n\nPrimary class anchors:",
            ),
            "2026-09-01-anchors-subsection.md",
        )
        check(
            "selftest#anchors_block/subsection_read_through",
            rc == 1
            and "readiness PRE-ROUND FAILED:" in err
            and "Task 1" in err,
            f"rc={rc} err={err!r}",
        )

        # full_gate_posture_unchanged: the full gate over a prose-form
        # fixture keeps its pre-plan verdict (the no-review-artifact
        # condition, never the anchors probe -- the anchors check is
        # wired solely into the pre-round chain).
        plan = plans_dir / "2026-09-01-anchors-full-gate.md"
        plan.write_text(
            _anchors_fixture_plan(_PROSE_BLOCK), encoding="utf-8"
        )
        rc, out, err = run_main([str(plan)])
        check(
            "selftest#anchors_block/full_gate_posture_unchanged",
            rc == 1 and "no review artifact" in err,
            f"rc={rc} err={err!r}",
        )
    finally:
        os.chdir(prev_cwd)
        facts_md = facts_dir / "facts.md"
        if facts_md.exists():
            facts_md.unlink()
        if facts_dir.is_dir() and not any(facts_dir.iterdir()):
            facts_dir.rmdir()


# The protected grammar names and their single home (the shadowing scan's
# contract): a definition is an assignment to the exact protected name
# whose right-hand side is not a `plan_shape.`-qualified reference.
_ANCHORS_HOME_RELPATH = "scripts/plan_shape.py"
_ANCHORS_PROTECTED_NAMES = (
    "PRIMARY_CLASS_ANCHORS_HEADING",
    "PRIMARY_CLASS_ANCHOR_ENTRY",
    "PRIMARY_CLASS_ANCHOR_SHAPE",
)


def _anchors_shadow_definitions(
    files_text: dict[str, str],
) -> list[str]:
    """Shadowing scan over an injectable path-to-text mapping.

    Returns one violation line per assignment to a protected name whose
    right-hand side is not a `plan_shape.`-qualified reference, outside
    the home file. The mapping keys are repo-relative paths; the home
    file is exempt.
    """
    import re as _re

    pattern = _re.compile(
        r"^("
        + "|".join(_ANCHORS_PROTECTED_NAMES)
        + r")\s*=\s*(.*)$"
    )
    violations: list[str] = []
    for relpath in sorted(files_text):
        if relpath == _ANCHORS_HOME_RELPATH:
            continue
        for lineno, line in enumerate(
            files_text[relpath].splitlines(), start=1
        ):
            match = pattern.match(line)
            if match is None:
                continue
            rhs = match.group(2).strip()
            if rhs.startswith("plan_shape."):
                continue
            violations.append(
                f"{relpath}:{lineno}: local definition of protected "
                f"anchors grammar name {match.group(1)} outside the "
                f"single home {_ANCHORS_HOME_RELPATH}"
            )
    return violations


def _selftest_anchors_single_home(check) -> None:
    """Single-home witness family: the tracked repository source carries
    no definition of the anchors grammar names outside
    ``scripts/plan_shape.py``; a shadowing redefinition in a consumer is
    caught by the same scan over an injectable mapping; the runtime's
    ``plan_shape.``-qualified alias assignments and the skills' prose
    mentions are the sanctioned-reference arm."""
    import re as _re
    import subprocess
    from pathlib import Path as _Path

    module_root = _Path(__file__).resolve().parent
    repo_root = module_root.parent
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z", "*.py"],
            cwd=repo_root,
            capture_output=True,
            timeout=30,
            check=True,
        ).stdout.decode("utf-8")
    except (OSError, subprocess.SubprocessError):
        listing = ""
    tracked = [
        rel
        for rel in listing.split("\0")
        if rel.endswith(".py")
    ]
    files_text: dict[str, str] = {}
    for rel in tracked:
        source = (repo_root / rel).read_text(encoding="utf-8")
        files_text[rel] = source
    # The skills' anchors bytes are scanned as real bytes, not only
    # modeled synthetically: the two skills whose prose carries the
    # anchors block and fixture entries join the scanned set (the
    # assignment discriminator accepts prose, so a definition smuggled
    # into a tracked skill is still caught).
    for rel in (
        "agents/skills/plans/SKILL.md",
        "agents/skills/review-plan/SKILL.md",
    ):
        skill = repo_root / rel
        if skill.exists():
            files_text[rel] = skill.read_text(encoding="utf-8")
    # Self-checking enumeration: the scan must have observed the home
    # and at least one consumer file, so a git failure never reads as a
    # vacuous pass.
    check(
        "selftest#anchors_single_home/enumeration_self_check",
        _ANCHORS_HOME_RELPATH in files_text
        and any(
            rel != _ANCHORS_HOME_RELPATH for rel in files_text
        )
        and "agents/skills/plans/SKILL.md" in files_text
        and "agents/skills/review-plan/SKILL.md" in files_text,
        f"scanned={sorted(files_text)[:5]}... n={len(files_text)}",
    )
    violations = _anchors_shadow_definitions(files_text)
    check(
        "selftest#anchors_single_home/tracked_source_clean",
        violations == [],
        f"violations={violations[:3]}",
    )

    # Shadowing arm: one regex-valued and one plain-string literal
    # redefinition in a synthetic consumer fails the scan.
    shadowed = dict(files_text)
    shadowed["scripts/synthetic_consumer.py"] = (
        "PRIMARY_CLASS_ANCHOR_ENTRY = re.compile(r'x')\n"
        "PRIMARY_CLASS_ANCHOR_SHAPE = '- `A` in `b`'\n"
    )
    violations = _anchors_shadow_definitions(shadowed)
    check(
        "selftest#anchors_single_home/shadowing_caught",
        len(violations) == 2
        and all(
            "synthetic_consumer" in violation for violation in violations
        ),
        f"violations={violations}",
    )

    # Sanctioned-reference arm: the runtime's alias assignments (the
    # `plan_shape.`-qualified shape) and a prose mention accept.
    sanctioned = dict(files_text)
    sanctioned["scripts/synthetic_consumer.py"] = (
        "PRIMARY_CLASS_ANCHORS_HEADING = "
        "plan_shape.PRIMARY_CLASS_ANCHORS_HEADING\n"
        "PRIMARY_CLASS_ANCHOR_ENTRY = plan_shape.PRIMARY_CLASS_ANCHOR_ENTRY\n"
        "# prose: the shape named PRIMARY_CLASS_ANCHOR_SHAPE is owned in "
        "scripts/plan_shape.py\n"
    )
    check(
        "selftest#anchors_single_home/sanctioned_references_accepted",
        _anchors_shadow_definitions(sanctioned) == [],
        "sanctioned references must not violate",
    )

    # Owner fingerprint (Task 2): the plans skill's corrected shape
    # sentence names its owner as a backticked symbol; that symbol must
    # be a compiled-regex binding in scripts/plan_shape.py, resolved via
    # the module file path (never the process cwd).
    skill_path = (
        _Path(__file__).resolve().parent.parent
        / "agents/skills/plans/SKILL.md"
    )
    skill_text = skill_path.read_text(encoding="utf-8")
    owner_marker = "**Primary class anchors; required:**"
    sentence = skill_text[
        skill_text.index(owner_marker):
    ].split("\n", 1)[0]
    backticked = _re.findall(r"`([^`]+)`", sentence)
    regex_bindings = [
        token
        for token in backticked
        if token in _ANCHORS_PROTECTED_NAMES
        and isinstance(getattr(plan_shape, token, None), _re.Pattern)
    ]
    check(
        "selftest#anchors_single_home/owner_fingerprint",
        len(regex_bindings) == 1
        and regex_bindings[0] == "PRIMARY_CLASS_ANCHOR_ENTRY",
        f"backticked={backticked} regex_bindings={regex_bindings}",
    )


def _selftest_accepted_state(
    plans_dir: Path, reviews_dir: Path, check
) -> None:
    """accepted_state: exit 0 and no reason output."""
    plan, _ = _write_clean_state(plans_dir, reviews_dir)
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#accepted_state",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )

    # coverage gate: degraded outcome with verdict yes must fail
    # (review-runner bounded-timeout plan, Task 5). Fixtures are dated
    # post-constant (2026-09-17) so the coverage fence arms at its real
    # pinned value with no module-state mutation; the plan text carries
    # the decision-points trailer and the sidecar carries the four
    # extended freshness fields, satisfying the neighboring post-fence
    # gates the 2026-09-16+ round date arms.
    fixture_plan_text = (
        "# Fixture plan\n\n"
        "## Assumptions\n\n"
        "Decision points requiring a grill: none remain.\n\n"
        "Body.\n"
    )

    def _coverage_case(
        name: str,
        coverage: dict | None,
        verdict: str,
        expect_ok: bool,
    ) -> None:
        plan_path, review_path = _write_clean_state(
            plans_dir,
            reviews_dir,
            plan_text=fixture_plan_text,
            date="2026-09-17",
            slug="coverage-gate-fixture",
        )
        sidecar = review_path.with_suffix(".stats.json")
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        # The clean-state sidecar is versionless by design; the coverage
        # contract lives in the version-1 gates, so promote the fixture to
        # current-v1 with minimal required fields.
        payload["schema_version"] = 1
        payload["review_type"] = "plan"
        payload["artifact_slug"] = "coverage-gate-fixture"
        payload["round"] = 1
        payload["review_mode"] = "fresh-adversarial"
        payload["risk_signals"] = []
        payload["prior_findings_filter"] = False
        payload["last_fix_commit"] = None
        payload["findings"] = []
        payload["overflow"] = []
        payload["soften_watchlist"] = []
        payload["deduplication_groups"] = []
        payload["discarded"] = []
        payload["severity_calibration"] = []
        payload["triage_outcomes"] = []
        payload["verdict"] = verdict
        if coverage is not None and isinstance(coverage, dict):
            material = sorted(
                {
                    str(lens)
                    for row in payload.get("panel", [])
                    if isinstance(row, dict)
                    for lens in (
                        row.get("lenses")
                        or vrs.REQUIRED_PANEL_LENSES.get(
                            row.get("worker"), []
                        )
                    )
                }
            )
            if not coverage.get("material_lens_set"):
                coverage["material_lens_set"] = material
            if "completed" not in coverage:
                coverage["completed"] = material
            if "missing" not in coverage:
                coverage["missing"] = []
            payload["coverage"] = coverage
            coverage_outcome = coverage.get("outcome")
            review_md = review_path.read_text(encoding="utf-8")
            if "- Coverage:" not in review_md and isinstance(
                coverage_outcome, str
            ):
                review_md = review_md.replace(
                    "## Metadata",
                    "## Metadata\n" f"- Coverage: {coverage_outcome}",
                    1,
                )
                review_path.write_text(review_md, encoding="utf-8")
        sidecar.write_text(json.dumps(payload, indent=2))
        ok_case, reason_case = evaluate_readiness(
            plan_path, plans_dir, reviews_dir
        )
        if ok_case != expect_ok:
            raw = vrs.ValidationResult(path=review_path)
            vrs.validate_stats_sidecar(
                review_path,
                review_path.read_text(encoding="utf-8"),
                raw,
                expected_digest=vrs.compute_source_digest(
                    "plan", plan_path.read_bytes()
                ),
                source_kind="plan",
            )
            name = f"{name} | raw_errors={raw.errors[:2]}"
        check(
            name,
            ok_case == expect_ok,
            f"ok={ok_case} reason={reason_case}",
        )

    _coverage_case(
        "selftest#coverage degraded outcome with verdict yes must fail",
        {
            "outcome": "degraded",
            "material_lens_set": ["quality"],
            "completed": [],
            "missing": ["quality"],
        },
        "yes",
        False,
    )
    _coverage_case(
        "selftest#coverage clean record with coverage passes",
        {"outcome": "clean"},
        "yes",
        True,
    )
    # replacement-covered with a valid link passes end to end: stage the
    # original as post-constant shown uncovered (timed-out panel row plus
    # its missing list) and link the replacing round to it.
    _orig_plan, _orig_review = _write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=fixture_plan_text,
        date="2026-09-17",
        slug="coverage-gate-fixture-orig",
        verdict="no",
    )
    _orig_payload = json.loads(
        _orig_review.with_suffix(".stats.json").read_text(encoding="utf-8")
    )
    _orig_payload["schema_version"] = 1
    _orig_payload["review_type"] = "plan"
    _orig_payload["artifact_slug"] = "coverage-gate-fixture-orig"
    _orig_payload["round"] = 1
    _orig_payload["date"] = "2026-09-17"
    _orig_payload["verdict"] = "no"
    _orig_payload["coverage"] = {
        "outcome": "degraded",
        "material_lens_set": ["quality"],
        "completed": [],
        "missing": ["quality"],
    }
    _orig_panel = _orig_payload.get("panel", [])
    if _orig_panel and isinstance(_orig_panel[0], dict):
        _orig_panel[0]["status"] = "timed-out"
        _orig_panel[0]["lenses"] = ["quality"]
    _orig_review.with_suffix(".stats.json").write_text(
        json.dumps(_orig_payload, indent=2), encoding="utf-8"
    )
    _coverage_case(
        "selftest#coverage replacement-covered with a valid link passes",
        {
            "outcome": "replacement-covered",
            "material_lens_set": ["quality"],
            "completed": [],
            "missing": [],
            "replacement": [
                {
                    "lens": "quality",
                    "original_artifact": str(_orig_review),
                    "original_sidecar": str(
                        _orig_review.with_suffix(".stats.json")
                    ),
                    "original_failure": "provider-timeout after budget",
                }
            ],
        },
        "yes",
        True,
    )
    # The missing-coverage arm is asserted directly against the shared
    # v1 gates (deterministic; the end-to-end fence behavior is witnessed
    # by the degraded case above).
    missing_cov_payload = json.loads(
        json.dumps(_clear_sidecar("a" * 64, "plan"))
    )
    missing_cov_payload.update(
        {
            "schema_version": 1,
            "review_type": "plan",
            "artifact_slug": "fixture-feature",
            "round": 1,
            "date": "2026-09-17",
            "review_mode": "fresh-adversarial",
            "risk_signals": [],
            "prior_findings_filter": False,
            "last_fix_commit": None,
            "findings": [],
            "overflow": [],
            "soften_watchlist": [],
            "deduplication_groups": [],
            "discarded": [],
            "severity_calibration": [],
            "triage_outcomes": [],
            "verdict": "yes",
        }
    )
    missing_cov_result = vrs.ValidationResult(Path("x"))
    vrs.validate_version1_payload(
        missing_cov_payload,
        "",
        missing_cov_result,
        staging_name="2026-09-17-plan-review-fixture-feature-r1.md",
    )
    check(
        "selftest#coverage post-constant record without coverage fails",
        any(
            "missing the required 'coverage' object" in e
            for e in missing_cov_result.errors
        ),
    )


def _selftest_slug_case(
    root: Path, plans_dir: Path, reviews_dir: Path, check
) -> None:
    """Canonical artifact-slug family (plan-review story-key case plan):
    the story-key pass end to end, the case-variant collision and
    rename-direction refusals, the derivation-refusal conversion, the
    backup-copy no-op pinning the probe's fullmatch anchor, and the
    lowercase identity no-op.

    The story key in the fixture names is a generic uppercase placeholder
    (``AB-12``): the shape under test is the uppercase story filename to
    lowercase round pair to seal resolution, and this repository's
    hygiene scan denies real ticket prefixes in script bytes. The fixture
    date (2026-09-01) sits below the coverage sidecar window, matching
    the ``_write_clean_state`` convention, so the arms trip only the
    slug-case behavior under test.
    """
    story_date = "2026-09-01"
    story_slug = "AB-12-nightly-bitmap-rebuild-lifecycle"
    canonical_slug = story_slug.lower()

    # backup_copy_noop: a `.backup-<timestamp>` copy of the canonical
    # round beside it leaves the readiness outcome unchanged. The
    # case-variant probe is anchored as a fullmatch; a search-based
    # matcher would classify this copy as case-variant and permanently
    # collision-refuse the plan, flipping this arm red.
    plan, review = _write_clean_state(plans_dir, reviews_dir)
    ok_before, reason_before = evaluate_readiness(plan, plans_dir, reviews_dir)
    backup = review.with_name(review.name + ".backup-1735689600")
    backup.write_bytes(review.read_bytes())
    ok_after, reason_after = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#slug_case/backup_copy_noop",
        ok_before and reason_before is None
        and ok_after and reason_after is None,
        f"before={ok_before}/{reason_before} after={ok_after}/{reason_after}",
    )
    _clean_reviews_dir(reviews_dir)

    # case_variant_collision_refusal: canonical-shaped AND case-variant
    # round records both present under the story-key plan; the named
    # collision refusal fires. The case-variant witness is an
    # uppercase-shaped legacy r9 record beside the canonical r1 pair:
    # names that differ by case ONLY cannot coexist on a
    # case-insensitive filesystem (the second write would collapse into
    # the first), so the fixture varies the round ordinal too, which
    # materializes the both-shapes state on every filesystem breed and
    # is exactly a case-variant record per the plan's terms.
    plan = plans_dir / f"{story_date}-{story_slug}.md"
    plan.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")
    digest = vrs.compute_source_digest("plan", plan.read_bytes())
    canonical_round = reviews_dir / (
        f"{story_date}-plan-review-{canonical_slug}-r1.md"
    )
    canonical_round.write_text(_review_markdown(), encoding="utf-8")
    canonical_sidecar = _clear_sidecar(digest)
    canonical_sidecar["date"] = story_date
    canonical_sidecar["artifact_slug"] = canonical_slug
    canonical_round.with_suffix(".stats.json").write_text(
        json.dumps(canonical_sidecar), encoding="utf-8"
    )
    legacy_round = reviews_dir / (
        f"{story_date}-plan-review-{story_slug}-r9.md"
    )
    legacy_round.write_text(_review_markdown(), encoding="utf-8")
    legacy_sidecar = _clear_sidecar(digest)
    legacy_sidecar["date"] = story_date
    legacy_sidecar["artifact_slug"] = story_slug
    legacy_round.with_suffix(".stats.json").write_text(
        json.dumps(legacy_sidecar), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#slug_case/case_variant_collision_refusal",
        not ok and reason is not None
        and (
            "case-variant round records exist under both the story-key "
            "and canonical shapes; rename the legacy pair to the "
            "canonical lowercase shape"
        ) in reason
        and legacy_round.name in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # rename_direction_refusal: the plan renamed to lowercase (canonical
    # identity), legacy uppercase-shaped pairs only; the refusal names
    # each legacy record, both halves of the pair.
    renamed = plans_dir / f"{story_date}-{canonical_slug}.md"
    renamed.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")
    legacy_md_name = f"{story_date}-plan-review-{story_slug}-r1.md"
    legacy = reviews_dir / legacy_md_name
    legacy.write_text(_review_markdown(), encoding="utf-8")
    legacy_stats_name = legacy.with_suffix(".stats.json").name
    legacy_rename_sidecar = _clear_sidecar(
        vrs.compute_source_digest("plan", renamed.read_bytes())
    )
    legacy_rename_sidecar["date"] = story_date
    legacy_rename_sidecar["artifact_slug"] = story_slug
    legacy.with_suffix(".stats.json").write_text(
        json.dumps(legacy_rename_sidecar),
        encoding="utf-8",
    )
    ok, reason = evaluate_readiness(renamed, plans_dir, reviews_dir)
    check(
        "selftest#slug_case/rename_direction_refusal",
        not ok and reason is not None
        and "rename the pair to the canonical lowercase shape" in reason
        and legacy_md_name in reason
        and legacy_stats_name in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # story_key_pass: uppercase plan filename, lowercase round pair and
    # sidecar; readiness OK, the seal-context slug lowercase in the
    # evidence payload, and check_review_name OK through the
    # --check-review-name CLI path with the OK line naming the story slug
    # beside the canonical slug (a missed CLI switch cannot ship green:
    # the asserted span names both only when the print derives through
    # artifact_slug).
    repo = root / "slug-case-repo"
    repo_plans = repo / "plans"
    repo_reviews = repo / "reviews"
    repo_plans.mkdir(parents=True)
    repo_reviews.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=False)
    story_plan = repo_plans / f"{story_date}-{story_slug}.md"
    story_plan.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")
    story_digest = vrs.compute_source_digest("plan", story_plan.read_bytes())
    story_round = repo_reviews / (
        f"{story_date}-plan-review-{canonical_slug}-r1.md"
    )
    story_round.write_text(_review_markdown(), encoding="utf-8")
    story_sidecar = _clear_sidecar(story_digest)
    story_sidecar["date"] = story_date
    story_sidecar["artifact_slug"] = canonical_slug
    story_round.with_suffix(".stats.json").write_text(
        json.dumps(story_sidecar), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(story_plan, repo_plans, repo_reviews)
    check(
        "selftest#slug_case/story_key_readiness_ok",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    # The context probe mirrors production usage: evaluate_readiness passes
    # its RESOLVED plan path, so the fixture resolves too (a raw macOS
    # /var/... path would not be relative to git's /private/var/... toplevel).
    context = _plan_corrections_context(
        story_plan.resolve(), story_plan.read_bytes()
    )
    check(
        "selftest#slug_case/story_key_seal_context_slug_lowercase",
        context is not None and context["slug"] == canonical_slug,
        f"context={context}",
    )
    prev_cwd = os.getcwd()
    os.chdir(repo)  # main() anchors facts resolution at the process cwd
    try:
        (repo / ".ai-playbook").mkdir()
        (repo / ".ai-playbook" / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )
        rc, out, err = _selftest_run_main(
            [str(story_plan), "--check-review-name", str(story_round)]
        )
        check(
            "selftest#slug_case/story_key_check_review_name_ok",
            rc == 0
            and "review name check OK" in out
            and (
                f"binds plan slug {story_slug} via canonical artifact "
                f"slug {canonical_slug}"
            ) in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
    finally:
        os.chdir(prev_cwd)

    # derivation_refusal_converts_to_fail: an unsafe stem lowercasing to
    # a non-kebab form yields OUTCOME: fail with the plan filename named,
    # never a traceback.
    unsafe = plans_dir / "2026-10-06-Foo_bar.md"
    unsafe.write_text("# Fixture plan\n\nBody.\n", encoding="utf-8")
    facts_dir = root / ".ai-playbook"
    prev_cwd = os.getcwd()
    os.chdir(root)
    try:
        facts_dir.mkdir(exist_ok=True)
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )
        rc, out, err = _selftest_run_main([str(unsafe)])
        check(
            "selftest#slug_case/derivation_refusal_converts_to_fail",
            rc == 1
            and "OUTCOME: fail" in out
            and "2026-10-06-Foo_bar.md" in err
            and "Traceback" not in err
            and "Traceback" not in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # check_review_name derivation catch: the per-round probe converts
        # the same refusal into its named (False, reason) failure path.
        ok, reason = check_review_name(
            unsafe,
            reviews_dir / f"{story_date}-plan-review-foo-bar-r1.md",
            reviews_dir,
        )
        check(
            "selftest#slug_case/derivation_refusal_check_review_name",
            not ok and reason is not None
            and "2026-10-06-Foo_bar.md" in reason
            and "Traceback" not in reason,
            f"ok={ok} reason={reason}",
        )
    finally:
        os.chdir(prev_cwd)
        # Leave no facts block behind: the CLI family creates .ai-playbook
        # fresh (plain mkdir, no exist_ok).
        facts_md = facts_dir / "facts.md"
        if facts_md.exists():
            facts_md.unlink()
        if facts_dir.is_dir() and not any(facts_dir.iterdir()):
            facts_dir.rmdir()

    # lowercase_identity_noop: for an all-lowercase plan the canonical
    # artifact slug equals the feature slug byte for byte.
    plain = Path(f"{story_date}-fixture-feature.md")
    check(
        "selftest#slug_case/lowercase_identity_noop",
        artifact_slug(plain) == feature_slug(plain) == "fixture-feature",
        f"artifact={artifact_slug(plain)!r} feature={feature_slug(plain)!r}",
    )


def _selftest_cli(
    root: Path, plans_dir: Path, reviews_dir: Path, check
) -> None:
    """CLI fixtures (main() over a temp tree): exit codes, output format,
    facts resolution, and repo-root anchoring all guarded here."""
    facts_dir = root / ".ai-playbook"
    facts_dir.mkdir()
    (facts_dir / "facts.md").write_text(
        "# facts\n\n```toml\n"
        'plans_dir = "plans"\n'
        'reviews_dir = "reviews"\n'
        "```\n",
        encoding="utf-8",
    )

    plan, _ = _write_clean_state(plans_dir, reviews_dir)

    prev_cwd = os.getcwd()
    os.chdir(root)  # repo_root() anchors at the process cwd
    try:
        # Sibling compat handshake fixtures: the in-process pair must
        # agree on COMPAT_VERSION, and every CLI mode fails loudly on a
        # mismatched or missing sibling constant.
        declared = getattr(vrs, "COMPAT_VERSION", None)
        check(
            "selftest#sibling_compat/real_pair_match",
            declared == EXPECTED_SIBLING_COMPAT_VERSION
            and _check_sibling_compat() is None,
            f"declared={declared!r}",
        )

        _compat_missing = object()
        _compat_saved = getattr(vrs, "COMPAT_VERSION", _compat_missing)
        try:
            vrs.COMPAT_VERSION = 999
            rc, out, err = _selftest_run_main(["--sweep"])
            check(
                "selftest#sibling_compat/mismatch_fails_loud",
                rc == 3
                and "compatibility FAILED" in err
                and "999" in err
                and "sweep" not in out,
                f"rc={rc} out={out!r} err={err!r}",
            )
            # r1 F3: gate mode fails loudly on the same mismatch; pins
            # that the handshake runs ahead of the gate path too, not
            # only the sweep path.
            rc, out, err = _selftest_run_cli(plan)
            check(
                "selftest#sibling_compat/mismatch_fails_loud/gate_mode",
                rc == 3
                and "compatibility FAILED" in err
                and "readiness" not in out,
                f"rc={rc} out={out!r} err={err!r}",
            )
            # r1 F3: --selftest mode fails loudly BEFORE the nested
            # selftest dispatch (returns early, so cost is negligible);
            # a refactor moving the check below the dispatch would fail
            # this arm.
            rc, out, err = _selftest_run_main(["--selftest"])
            check(
                "selftest#sibling_compat/mismatch_fails_loud/"
                "selftest_mode",
                rc == 3
                and "compatibility FAILED" in err
                and "ALL PASS" not in out
                and "PASS:" not in out,
                f"rc={rc} out={out!r} err={err!r}",
            )
            delattr(vrs, "COMPAT_VERSION")
            rc, out, err = _selftest_run_main(["--sweep"])
            _ok = (
                rc == 3
                and "compatibility FAILED" in err
                and "does not declare COMPAT_VERSION" in err
                and "sweep" not in out
            )
            check(
                "selftest#sibling_compat/missing_constant",
                _ok,
                f"rc={rc} out={out!r} err={err!r}",
            )
        finally:
            if _compat_saved is _compat_missing:
                delattr(vrs, "COMPAT_VERSION")
            else:
                vrs.COMPAT_VERSION = _compat_saved

        # accepted: exit 0 with the readiness OK line on stdout.
        rc, out, err = _selftest_run_cli(plan)
        check(
            "selftest#cli/accepted_state",
            rc == 0 and "readiness OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # rejected: exit 1 with the readiness FAILED: prefix on stderr.
        plan2, _ = _write_clean_state(plans_dir, reviews_dir, verdict="no")
        rc, out, err = _selftest_run_cli(plan2)
        check(
            "selftest#cli/rejected_state",
            rc == 1 and "readiness FAILED:" in err,
            f"rc={rc} out={out!r} err={err!r}",
        )
        _clean_reviews_dir(reviews_dir)

        # missing facts: exit 1 with the cannot-resolve reason.
        (facts_dir / "facts.md").unlink()
        rc, out, err = _selftest_run_cli(plan)
        check(
            "selftest#cli/missing_facts",
            rc == 1 and "cannot resolve plans_dir/reviews_dir" in err,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # nested_cwd (W10, r3): a RELATIVE plan path invoked from a
        # subdirectory of a real git repo anchors at the repo ROOT, not
        # the process cwd.
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )
        plan, _ = _write_clean_state(plans_dir, reviews_dir)
        subprocess.run(
            ["git", "-C", str(root), "init", "-q"], check=False
        )
        subdir = root / "sub"
        subdir.mkdir()
        os.chdir(subdir)
        rc, out, err = _selftest_run_cli(Path("plans") / plan.name)
        check(
            "selftest#cli/nested_cwd",
            rc == 0 and "readiness OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # cwd_relative_dotdot (r4 X5): a ``..``-containing relative
        # plan path that EXISTS relative to the process cwd prefers the
        # cwd interpretation over repo-root re-rooting (root/../plans
        # does not exist and would false-reject).
        plan, _ = _write_clean_state(plans_dir, reviews_dir)
        rc, out, err = _selftest_run_cli(Path("..") / "plans" / plan.name)
        check(
            "selftest#cli/cwd_relative_dotdot",
            rc == 0 and "readiness OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )

        # tilde_facts (W10, r3): tilde-valued facts keys expand against
        # HOME (pointed at the temp root here), user-absolute regardless
        # of cwd.
        tilde_plans = root / "tilde-plans"
        tilde_reviews = root / "tilde-reviews"
        tilde_plans.mkdir()
        tilde_reviews.mkdir()
        tplan = tilde_plans / "2026-09-01-tilde-feature.md"
        tplan.write_text("# tilde plan\n\nBody.\n", encoding="utf-8")
        tdigest = vrs.compute_source_digest("plan", tplan.read_bytes())
        treview = tilde_reviews / (
            "2026-09-01-plan-review-tilde-feature-r1.md"
        )
        treview.write_text(_review_markdown(), encoding="utf-8")
        treview.with_suffix(".stats.json").write_text(
            json.dumps(_clear_sidecar(tdigest)), encoding="utf-8"
        )
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "~/tilde-plans"\n'
            'reviews_dir = "~/tilde-reviews"\n'
            "```\n",
            encoding="utf-8",
        )
        prev_home = os.environ.get("HOME")
        os.environ["HOME"] = str(root)
        try:
            rc, out, err = _selftest_run_cli(tplan)
            check(
                "selftest#cli/tilde_facts",
                rc == 0 and "readiness OK" in out,
                f"rc={rc} out={out!r} err={err!r}",
            )
        finally:
            if prev_home is None:
                del os.environ["HOME"]
            else:
                os.environ["HOME"] = prev_home
    finally:
        os.chdir(prev_cwd)


def _selftest_sweep(
    root: Path, plans_dir: Path, reviews_dir: Path, check
) -> None:
    """--sweep fixtures (r5 Y2/Y7): anomaly detection, clean pass,
    CLI plumbing, missing reviews_dir, and plan_path rejection."""
    facts_dir = root / ".ai-playbook"
    prev_cwd = os.getcwd()
    os.chdir(root)
    try:
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )
        _clean_reviews_dir(reviews_dir)
        # (a) anomaly: Summary's ready= is split across two lines — the
        # sweep mention fires, the per-line total rule finds no token.
        _write_clean_state(plans_dir, reviews_dir, verdict_line="- ready=\nyes")
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/anomaly_split_ready_returns_1",
            rc == 1
            and "sweep FAILED" in out
            and "2026-09-01-plan-review-fixture-feature-r1.md" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        _clean_reviews_dir(reviews_dir)
        # (b) clean: a plain ready=yes review sweeps to 0.
        _write_clean_state(plans_dir, reviews_dir)
        rc_sweep = run_sweep(reviews_dir)
        check(
            "selftest#sweep/clean_returns_0",
            rc_sweep == 0,
            f"rc={rc_sweep}",
        )
        # (c) CLI plumbing: main(["--sweep"]) exit 0 with the OK line.
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/main_cli_plumbing",
            rc == 0 and "sweep OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        # (c2) r6 Z3: an anomalous *-code-review-*.md file in the sweep
        # tree is NOT swept (glob scoping is plan-review-only); the
        # clean plan-review state still sweeps to 0.
        code_review = reviews_dir / (
            "2026-09-01-code-review-fixture-feature-r1.md"
        )
        code_review.write_text(
            "## Summary\n\n- ready=\nyes\n", encoding="utf-8"
        )
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/code_review_files_not_flagged",
            rc == 0 and "sweep OK" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        # (c3) r6 Z3: an unreadable (non-UTF-8) plan-review artifact in
        # the sweep tree is an anomaly naming the file, rc 1.
        unreadable = reviews_dir / (
            "2026-09-01-plan-review-unreadable-feature-r1.md"
        )
        unreadable.write_bytes(b"# review \xff\xfe binary\n")
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/unreadable_artifact_returns_1",
            rc == 1
            and "sweep FAILED" in out
            and "2026-09-01-plan-review-unreadable-feature-r1.md" in out
            and "unreadable" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        unreadable.unlink()
        # (c4) r6 Z3: mention-vs-token breadth — a Summary line whose
        # ready= mention is NOT a word-bounded token (``Notready=yes``)
        # or carries no yes/no value (``- Blocking findings: ready=``)
        # is an anomaly: the broad mention fires, the token rule cannot.
        breadth = reviews_dir / (
            "2026-09-01-plan-review-breadth-feature-r1.md"
        )
        breadth.write_text(
            "## Summary\n\nVerdict: Notready=yes\n", encoding="utf-8"
        )
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/mention_vs_token_notready",
            rc == 1
            and "sweep FAILED" in out
            and "2026-09-01-plan-review-breadth-feature-r1.md" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        breadth.write_text(
            "## Summary\n\n- Blocking findings: ready=\n", encoding="utf-8"
        )
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/mention_vs_token_no_value",
            rc == 1
            and "sweep FAILED" in out
            and "2026-09-01-plan-review-breadth-feature-r1.md" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        breadth.unlink()
        code_review.unlink()
        # (c5) r6 Z3: a facts.md WITHOUT a reviews_dir key cannot run
        # the sweep at all; rc 1 with the named resolution reason.
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\nplans_dir = \"plans\"\n```\n",
            encoding="utf-8",
        )
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/facts_without_reviews_dir",
            rc == 1 and "cannot resolve reviews_dir" in err,
            f"rc={rc} out={out!r} err={err!r}",
        )
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )
        # (d) r5 Y7: configured reviews_dir missing on disk → exit 1
        # with its OWN reason (never a silent zero-artifact pass).
        reviews_dir.rename(root / "reviews-gone")
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/missing_reviews_dir_returns_1",
            rc == 1 and "does not exist on disk" in err,
            f"rc={rc} out={out!r} err={err!r}",
        )
        (root / "reviews-gone").rename(reviews_dir)
        # (e) r5 Y7: plan_path combined with --sweep is a usage error.
        plan, _ = _write_clean_state(plans_dir, reviews_dir)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                main(["--sweep", str(plan)])
            except SystemExit as exc:
                usage_rc = exc.code
            else:
                usage_rc = 0
        check(
            "selftest#sweep/plan_path_rejected",
            usage_rc == 3 and "must not be combined" in err.getvalue(),
            f"usage_rc={usage_rc} err={err.getvalue()!r}",
        )
        # (f) Task 4: coverage counter over a mixed corpus — one clean
        # artifact whose sidecar lacks the field, one (at a DISTINCT
        # date-prefixed path) whose sidecar carries "verdict": "yes" —
        # prints 1/2; rc 0.
        _clean_reviews_dir(reviews_dir)
        _write_clean_state(plans_dir, reviews_dir)
        _, review_dated = _write_clean_state(plans_dir, reviews_dir, date="2026-09-02")
        dated_sidecar = review_dated.with_suffix(".stats.json")
        dated_payload = json.loads(
            dated_sidecar.read_text(encoding="utf-8")
        )
        dated_payload["verdict"] = "yes"
        dated_sidecar.write_text(
            json.dumps(dated_payload), encoding="utf-8"
        )
        # r1 F1: third artifact at a distinct date whose sidecar carries a
        # legacy NON-CONFORMING dict verdict; presence is NOT coverage;
        # only the conforming "yes" arm counts, so coverage stays 1/3.
        _, review_legacy = _write_clean_state(plans_dir, reviews_dir, date="2026-09-03")
        legacy_sidecar = review_legacy.with_suffix(".stats.json")
        legacy_payload = json.loads(
            legacy_sidecar.read_text(encoding="utf-8")
        )
        legacy_payload["verdict"] = {"ready": False}
        legacy_sidecar.write_text(
            json.dumps(legacy_payload), encoding="utf-8"
        )
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/coverage_mixed_corpus",
            rc == 0 and "sweep coverage: 1/3" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        _clean_reviews_dir(reviews_dir)
        # (f2) Task 4: a malformed sidecar (not JSON) counts as NOT
        # covered and is NOT an anomaly; 0/2, rc 0, no crash.
        _write_clean_state(plans_dir, reviews_dir)
        malformed_review = reviews_dir / (
            "2026-09-02-plan-review-fixture-feature-r1.md"
        )
        malformed_review.write_text(
            "# Plan Review\n\n## Summary\n\n- ready=yes\n",
            encoding="utf-8",
        )
        malformed_review.with_suffix(".stats.json").write_text(
            "not json", encoding="utf-8"
        )
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/coverage_malformed_sidecar_uncovered",
            rc == 0 and "sweep coverage: 0/2" in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        _clean_reviews_dir(reviews_dir)
        # (f3) Task 4 (r1 F3 fold): a facts file whose reviews_dir points
        # at a missing directory fails with its OWN error and prints NO
        # coverage line (the early return precedes the glob).
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews-absent"\n'
            "```\n",
            encoding="utf-8",
        )
        rc, out, err = _selftest_run_main(["--sweep"])
        check(
            "selftest#sweep/coverage_absent_on_missing_reviews_dir",
            rc == 1
            and "sweep FAILED" in err
            and "sweep coverage:" not in out,
            f"rc={rc} out={out!r} err={err!r}",
        )
        (facts_dir / "facts.md").write_text(
            "# facts\n\n```toml\n"
            'plans_dir = "plans"\n'
            'reviews_dir = "reviews"\n'
            "```\n",
            encoding="utf-8",
        )
        _clean_reviews_dir(reviews_dir)
    finally:
        os.chdir(prev_cwd)


def run_selftest() -> int:
    """Selftest dispatcher: fixture families run in a TEMP tree, never
    the live repo; every family reports through the shared ``check``."""
    global _selftest_telemetry_suppressed

    _prior = _selftest_telemetry_suppressed
    _selftest_telemetry_suppressed = True
    try:
        return _run_selftest_families()
    finally:
        _selftest_telemetry_suppressed = _prior


def _run_selftest_families() -> int:
    """The run_selftest families, with telemetry already suppressed."""
    import tempfile

    failures = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        if ok:
            print(f"PASS: {name}")
        else:
            failures += 1
            print(f"FAIL: {name}" + (f" - {detail}" if detail else ""))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        plans_dir = root / "plans"
        reviews_dir = root / "reviews"
        plans_dir.mkdir()
        reviews_dir.mkdir()

        _selftest_sidecar_shapes(plans_dir, reviews_dir, check)
        _selftest_source_and_digest(plans_dir, reviews_dir, check)
        _selftest_verdict_grammar(plans_dir, reviews_dir, check)
        _selftest_paths_and_blocking(root, plans_dir, reviews_dir, check)
        _selftest_round_selection(plans_dir, reviews_dir, check)
        _selftest_decision_marker(plans_dir, reviews_dir, check)
        _selftest_review_scope(plans_dir, reviews_dir, check)
        _selftest_plan_ownership(root, plans_dir, reviews_dir, check)
        _selftest_scope_classification(plans_dir, reviews_dir, check)
        _selftest_pre_round(root, plans_dir, reviews_dir, check)
        _selftest_anchors_block(root, plans_dir, reviews_dir, check)
        _selftest_anchors_single_home(check)
        _selftest_accepted_state(plans_dir, reviews_dir, check)
        _selftest_slug_case(root, plans_dir, reviews_dir, check)
        _selftest_cli(root, plans_dir, reviews_dir, check)
        _selftest_corrections_gate(check)
        _selftest_sweep(root, plans_dir, reviews_dir, check)

    print()
    if failures:
        print(f"SOME FAIL ({failures})")
        print("OUTCOME: %s" % OUTCOME_LABELS[1])
        return 1
    print("ALL PASS")
    print("OUTCOME: %s" % OUTCOME_LABELS[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
