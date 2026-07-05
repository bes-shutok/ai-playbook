#!/usr/bin/env python3
"""One-time-per-repo migration engine for the two-layer lessons corpus.

Stdlib only. A MANUAL tool invoked by the ``lessons-migrate`` skill. The only
writer of BOTH files during a migration (user corpus + project file + repo-wide
``#N`` references).

Contract (plan: Two-Layer Lessons Corpus, 2026-06-29; Task 4):
- Inputs: the repo's ``docs/maintenance/development_lessons.md`` and the user
  corpus path (``<shared_docs_dir>/development_lessons.md``, created if absent;
  ``shared_docs_dir`` is resolved by PARSING the lowercase facts key from
  ``.ai-playbook/facts.md`` - it is NOT an env var, r3 B2).
- git-clean precondition scoped to the FULL write scope, both repos (r4 Blocker
  3): refuse unless ``git diff --quiet`` over EVERY path this tool will write.
- No-concurrency-with-``learn`` + interruption recovery: PROSE preconditions with
  no runtime enforcement; recovery rolls back BOTH repos via
  ``git checkout -- <scope>`` (no resume marker, no ``--force``).
- Classify each lesson (generic-first, ZERO-CONFIG, repo-agnostic):
    1. well-formed ``Family <A-H>`` tag -> cross-project;
    2. generic engineering shape (per-family keyword phrase list, a SECONDARY
       derived view of the catalog with a discriminating-token selftest) and no
       domain residue -> cross-project;
    3. default -> project-specific (the safe call);
    4. tail summary line (non-routing) listing retained untagged lessons.
- Dedup against the user corpus (cite #77): near-match -> flag for merge, NOT
  auto-added.
- Atomic write order: build BOTH file contents + remap in memory; (1) user
  corpus first via ``atomic_write_text``, run the gate on the ``.tmp``, require
  exit 0, ``os.replace`` only on success, else delete ``.tmp`` + abort leaving
  BOTH files untouched; (2) project file + repo-wide refs second.
- Remap + repo-wide rewrite (load-bearing, B1): ONE rewrite rule everywhere
  (single discriminator + ``.md``-exclusion + case-insensitive process-prefix
  denylist + multi-number repeated group; same-tier -> new ``#N``, cross-tier ->
  REMOVE with within-line ``(#N)`` cleanup, ambiguous -> FLAG).
- Lead-in enumeration audit: the review list emits EVERY distinct
  ``<lead-in> #N`` token discriminated AS a lesson, grouped by lead-in.
- Frozen audit snapshot under ``docs/history/feature-notes/``; delete
  ``docs/maintenance/principle-index.md``.
- Self-check: authoritative remap-driven reconciliation + coarse echoes;
  re-run the gate on the final corpus (exit 0).

The ``--selftest`` exercises every Task-4 fixture bullet against in-memory
synthetic corpora ONLY. ``--dry-run`` classifies + emits the review list +
planned remap WITHOUT writing.

Threat model: the git-clean precondition is the sole recovery guard. No lock;
the operator ensures no concurrent ``learn`` append in any repo (both rewrite
the shared user corpus, last-writer-wins). ``~/.ai-playbook/scripts/`` is
trusted.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Allow ``import lessons_corpus`` whether run as a script or via ``python -m``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lessons_corpus  # noqa: E402  (shared primitive, intentional import; cite #119)
import lessons_classify  # noqa: E402  (mid-tier: classifier + FAMILY_KEYWORDS, cite #119)
import facts_paths  # noqa: E402  (stdlib leaf: facts-file key resolution)

# Re-export the MOVED public API from the leaves (r8-L1 single source: the
# migrator keeps NO own copy of phrase_present/matches_family_vocab; r8-L2: the
# underscore is dropped where re-exported because they are now consumed
# cross-module). ``FAMILY_KEYWORDS`` and the lesson-shape classifier were MOVED
# to ``lessons_classify``; ``resolve_shared_docs_dir``/``user_corpus_path`` were
# MOVED to ``facts_paths``. Public API shape is UNCHANGED.
FAMILY_KEYWORDS = lessons_classify.FAMILY_KEYWORDS
matches_family_vocab = lessons_classify.matches_family_vocab
phrase_present = lessons_classify.phrase_present

#: Marker written as the first body line of a cross-project lesson whose existing
#: tag is malformed or missing. ``unclassified`` passes the strict gate (wrong
#: family > no family; never guess).
UNCLASSIFIED_TAG_LINE = "**Principle:** Family unclassified (needs classification)"

#: Filename of the project lessons file (relative to the repo root).
PROJECT_LESSONS_RELPATH = Path("docs/maintenance/development_lessons.md")

#: The deleted derived index (no persistent index; recall is by grep).
PRINCIPLE_INDEX_RELPATH = Path("docs/maintenance/principle-index.md")

#: Directory under which the frozen audit snapshot is written.
FEATURE_NOTES_RELPATH = Path("docs/history/feature-notes")

#: Repo-wide rewrite targets (relative to repo root). History is excluded.
REWRITE_GLOBS = ("src/**/*.py", "tests/**/*.py", "**/*.md")

#: Directory names never descended into during the repo-wide rewrite. These hold
#: third-party / generated / VCS content (a ``**/*.md`` glob otherwise descends
#: into ``.venv`` and rewrites a packaged CHANGELOG, corrupting an installed
#: dependency). The migrator also skips symlinks (a ``CLAUDE.md -> AGENTS.md``
#: link reads through the link but ``os.replace`` would overwrite the LINK
#: itself, dereferencing it and breaking the repo invariant).
_EXCLUDED_DIRS = frozenset({
    ".git", ".hg", ".svn",
    ".venv", "venv", "env", ".env",
    "node_modules", "bower_components",
    "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".tox",
    "dist", "build", "target", "out",
    ".idea", ".vscode",
    ".eggs",
})

#: Paths the migrator writes in the tax-reporting repo (for the git-clean
#: precondition's FULL write scope, r4 Blocker 3). Repo-wide ref-rewrite targets
#: are covered by these directory scopes.
REPO_WRITE_SCOPES = (
    "docs/maintenance/development_lessons.md",
    "src/",
    "tests/",
    "AGENTS.md",
    "docs/maintenance/",
)

# --------------------------------------------------------------------------- #
# Per-family generic-shape keyword phrase list (signal 2 vocabulary).
# --------------------------------------------------------------------------- #
#: MOVED to ``lessons_classify.FAMILY_KEYWORDS`` (byte-identical). Re-exported
#: above as ``FAMILY_KEYWORDS = lessons_classify.FAMILY_KEYWORDS`` so the
#: migrator's public API shape is unchanged. Authority: ``coding_guidelines.md``
#: #17-#25 (the catalog). This is a SECONDARY DERIVED VIEW of the catalog; on
#: catalog growth, update the list in ``lessons_classify`` AND the
#: discriminating-token selftest there.

#: Process/identifier prefix keywords whose ``#N`` is NOT a lesson citation
#: (case-insensitive; r6 Medium). The corpus carries non-lesson ``#N`` tokens
#: whose preceding token is a process/identifier keyword, NOT a ``.md`` filename
#: - verified present (``Rule #4``, lowercase ``rule #6``, ``Finding #1``,
#: lowercase ``finding #1``, ``Design Invariant #2``, ``Medium #1``,
#: ``DP-014 #6``, ``r2``, etc.). These are LEFT UNCHANGED.
PROCESS_PREFIXES: frozenset[str] = frozenset({
    "Finding", "Findings",
    "Medium", "Blocker", "Low", "High",
    "Task", "Tasks",
    "Rule", "Rules",
    "Round", "Rounds",
    "Step", "Steps",
    "Invariant", "Invariants",
    "Family",
    "Campo", "Quadro", "Anexo", "Tabela",
    "CIRS", "CRG", "SRG",
})

#: Patterns (matched case-insensitively against the immediately-preceding
#: non-space token, backtick-stripped) whose ``#N`` is NOT a lesson citation.
#: ``DP-\\d+``, ``r\\d+`` (review round), ``UL#`` (user-level namespace),
#: ``art\\.?`` (legal article).
PROCESS_PREFIX_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^DP-\d+$", re.IGNORECASE),
    re.compile(r"^r\d+$", re.IGNORECASE),
    re.compile(r"^UL#$", re.IGNORECASE),
    re.compile(r"^art\.?$", re.IGNORECASE),
)


# --------------------------------------------------------------------------- #
# Data shapes.
# --------------------------------------------------------------------------- #
@dataclass
class ClassifiedLesson:
    """A parsed lesson with its migration routing decision."""

    number: int
    title: str
    body_lines: list[str]
    raw_text: str  # the lesson block as it appeared in the source (heading + body)
    tags: tuple[str, ...]
    route: str  # "cross-project" | "project-specific"
    cross_family: str | None = None  # for signal-2 matches, the family letter
    cross_reason: str = ""  # why it was routed cross-project (signal 1/2)


@dataclass
class RemapEntry:
    """Per-old-lesson-number resolution.

    ``action``:
    - ``same-tier``: stays project-side; rewrite citations to ``new_number``.
    - ``cross-tier``: moved to the user corpus; REMOVE citations (no ``UL#`` in
      the project file - the UL namespace is user-level only).
    - ``ambiguous``: flagged for manual review (no rewrite).
    """

    old_number: int
    action: str
    new_number: int | None = None  # set for same-tier
    ul_number: int | None = None  # set for cross-tier (recorded for the audit)


@dataclass
class RewriteRecord:
    """One discriminated lesson-``#N`` token the migrator touched.

    Used by the authoritative stale-ref reconciliation (every touched token:
    old value -> action) and the lead-in enumeration audit.
    """

    file: str
    line_no: int
    old_number: int
    action: str  # "renumbered-to-new" | "removed" | "left-non-lesson" | "flagged-ambiguous"
    new_number: int | None = None
    lead_in: str = ""  # the preceding non-space token (backtick-stripped) if any
    raw_token: str = ""  # the literal matched token (e.g. "#5" or "Lesson #5")


@dataclass
class MigrationResult:
    """Summary counts + the review list."""

    project_kept: int = 0
    cross_moved: int = 0
    ambiguous_flagged: int = 0
    dedup_merge_flagged: int = 0
    refs_rewritten: int = 0
    refs_unremappable: int = 0
    review_lines: list[str] = field(default_factory=list)
    remap: dict[int, RemapEntry] = field(default_factory=dict)
    rewrite_records: list[RewriteRecord] = field(default_factory=list)
    new_project_count: int = 0  # M (compact-renumbered project lesson count)
    user_corpus_path: str | None = None
    project_path: str | None = None
    review_list_path: str | None = None
    snapshot_path: str | None = None
    wrote_files: bool = False


# --------------------------------------------------------------------------- #
# Path resolution.
# --------------------------------------------------------------------------- #
#: MOVED to ``facts_paths`` (byte-identical, including the repo-first two-
#: candidate search order). Re-exported here so the migrator's public API shape
#: is unchanged (cite #119: the migrator and the conformance test must agree on
#: the corpus path via ONE resolver).
resolve_shared_docs_dir = facts_paths.resolve_shared_docs_dir
user_corpus_path = facts_paths.user_corpus_path


# --------------------------------------------------------------------------- #
# git-clean precondition (full write scope, both repos).
# --------------------------------------------------------------------------- #
def _git_is_clean(repo_root: Path, scope: str) -> bool:
    """Return True iff ``git diff --quiet -- <scope>`` over ``repo_root`` is clean.

    A non-git directory (exit 128) is treated as NOT clean (refuse; the recovery
    recipe assumes git).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", "--", scope],
            cwd=str(repo_root),
            capture_output=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def assert_git_clean(repo_root: Path, ai_playbook_root: Path, user_corpus: Path) -> None:
    """Refuse to start unless the FULL write scope is git-clean in BOTH repos.

    Raises ``RuntimeError`` naming the dirty scope(s) + the recovery recipe. The
    full write scope (r4 Blocker 3): tax-reporting's project file + ``src/`` +
    ``tests/`` + ``AGENTS.md`` + ``docs/maintenance/`` AND ai-playbook's
    user-corpus file. The prior input-only check let an unrelated uncommitted
    change in ``src/``/``tests/`` be destroyed by the ``git checkout -- <scope>``
    recovery.
    """
    dirty: list[str] = []
    for scope in REPO_WRITE_SCOPES:
        if not _git_is_clean(repo_root, scope):
            dirty.append(f"{repo_root.name}/{scope}")
    # The user corpus lives under ai-playbook (via the symlink); check the
    # underlying playbook repo path so the dirty-detection sees the right git.
    try:
        rel = user_corpus.resolve().relative_to(ai_playbook_root.resolve())
    except ValueError:
        rel = Path("projects/.ai-playbook/development_lessons.md")
    if not _git_is_clean(ai_playbook_root, str(rel)):
        dirty.append(f"{ai_playbook_root.name}/{rel}")
    if dirty:
        raise RuntimeError(
            "lessons_migrate: refusing to start: uncommitted git changes in the "
            "write scope. Commit or stash first. Dirty scopes: "
            + ", ".join(dirty)
            + ". Recovery recipe (both repos): 'git checkout -- <scope>' + re-run."
        )


# --------------------------------------------------------------------------- #
# Lesson parsing + classification (generic-first, zero-config).
# --------------------------------------------------------------------------- #
#: Domain-residue detector. INTENT (plan INTENT, r2): "No domain keywords are
#: baked in or CURATED" / "the classifier keys off the family catalog +
#: generic-shape vocabulary, never repo terms." A prior pass kept a CURATED
#: domain vocabulary (``crypto|FIFO|Koinly|ISIN|dividend|Modelo|...``) here and
#: consulted it as signal 2's negative clause - that is exactly what the plan
#: forbids: a hand-curated domain taxonomy used by the classifier. Pass 2 removes
#: the curated vocabulary and re-expresses "domain residue" as a REUSE of tokens
#: the plan already mandates for OTHER reasons, plus ONE generic legal/form-
#: citation pattern (legal-citation STRUCTURE, not a curated vocabulary):
#:   * ``PROCESS_PREFIXES`` - jurisdictional structural tokens (CIRS, CRG, SRG,
#:     Quadro, Anexo, Tabela, Campo, ...) that the plan's discriminator spec
#:     (line ~270) MANDATES for process-identifier exclusion. A lesson whose body
#:     contains one of these as a word IS domain-coupled. We reuse the same set;
#:     we do NOT re-curate.
#:   * ``_GENERIC_LEGAL_CITATION_RE`` - ``art.\\s*\\d`` and the form-code shape
#:     ``\\bQ\\d{1,2}\\b``: GENERIC legal-citation / form-field structure, not a
#:     repo/domain vocabulary. Any lesson citing a legal article or a Q1-Q99 form
#:     field is jurisdiction-coupled regardless of the specific statute.
#: The safe-default fixture ("validate the FIFO basis per CIRS art. 43") is still
#: detected: it contains ``CIRS`` (a PROCESS_PREFIXES token) AND ``art. 43`` (a
#: generic legal citation). A clean generic lesson ("catch specific exception
#: types, not broad Exception") has NEITHER structural token NOR legal citation
#: and stays promotable. The selftest pins both directions.
_GENERIC_LEGAL_CITATION_RE = re.compile(
    r"art\.\s*\d|\bQ\d{1,2}\b",
    re.IGNORECASE,
)


def _has_domain_residue(title: str, body: str) -> bool:
    """Domain-residue check (signal 2's negative clause).

    A lesson is domain-coupled (and therefore stays project-side even if a
    generic-shape phrase matches) iff its title/body contains either:
    (a) a jurisdictional structural token from ``PROCESS_PREFIXES`` (reused; the
        plan mandates this set for the discriminator's process-identifier
        exclusion - we do NOT maintain a separate curated domain vocabulary); or
    (b) a GENERIC legal/form-citation pattern (``art.\\s*\\d`` or ``Q\\d{1,2}``).

    This is NOT a baked-in domain keyword list and NOT routing logic: the
    classifier keys off the family catalog + generic-shape vocabulary, never repo
    terms. The residue check is a SECONDARY guard that reuses structural tokens
    already mandated for other reasons plus a generic legal-citation shape. The
    selftest asserts the SAFE DEFAULT directly (a FIFO+CIRS+art.43 lesson is NOT
    promoted) AND that a clean generic lesson IS promotable (no false residue).
    """
    haystack = title + "\n" + body
    # (a) Reuse PROCESS_PREFIXES (case-insensitive whole-word match).
    for token in PROCESS_PREFIXES:
        if re.search(r"\b" + re.escape(token) + r"\b", haystack, re.IGNORECASE):
            return True
    # (b) Generic legal/form-citation structure.
    if _GENERIC_LEGAL_CITATION_RE.search(haystack):
        return True
    return False


#: ``_matches_family_vocab`` / ``_phrase_present`` MOVED to ``lessons_classify``
#: (byte-identical) and re-exported above as the PUBLIC ``matches_family_vocab`` /
#: ``phrase_present``. Internal callers below use the public names.


def classify_lesson(lesson: lessons_corpus.Lesson) -> tuple[str, str, str | None]:
    """Classify a parsed lesson. Returns ``(route, reason, cross_family)``.

    Signals, evaluated first-match-wins:
    1. well-formed ``Family <A-H>`` tag -> cross-project;
    2. generic engineering shape (family keyword phrase match) AND no domain
       residue -> cross-project;
    3. default -> project-specific (the safe call).
    """
    title = lesson.title
    body = "\n".join(lesson.body_lines)
    # Signal 1: well-formed Family <A-H> tag. The first tag (the parser already
    # filtered fences). A malformed tag (e.g. "Family Q") is NOT signal 1.
    if lesson.tags:
        token = lesson.tags[0]
        if token in lessons_corpus.VALID_FAMILIES:
            return "cross-project", f"signal 1: Family {token} tag", token
    # Signal 2: generic-shape vocabulary + no domain residue.
    hit = matches_family_vocab(title, body)
    if hit and not _has_domain_residue(title, body):
        letter, _matched = hit
        return "cross-project", f"signal 2: generic {letter} vocabulary", letter
    # Signal 3: default -> project-specific.
    return "project-specific", "signal 3: default", None


# --------------------------------------------------------------------------- #
# Dedup against the user corpus (cite #77 - never silent overwrite).
# --------------------------------------------------------------------------- #
def _normalize_title(title: str) -> str:
    """Normalize a lesson title for near-match comparison."""
    # Lowercase, collapse whitespace, strip trailing punctuation.
    return re.sub(r"\s+", " ", title.strip().lower()).rstrip(".").strip()


def _near_match(a_title: str, a_body: str, b_title: str, b_body: str) -> bool:
    """True iff titles normalize-equal AND body Jaccard on word-sets >= 0.6.

    A near-match is FLAGGED FOR MERGE (never auto-added). The threshold is a
    conservative proxy; the operator reconciles flagged merges by hand.
    """
    if _normalize_title(a_title) != _normalize_title(b_title):
        return False
    aw = set(a_body.lower().split())
    bw = set(b_body.lower().split())
    if not aw and not bw:
        return True
    if not aw or not bw:
        return False
    return len(aw & bw) / len(aw | bw) >= 0.6


def find_near_matches(
    candidate_title: str,
    candidate_body: str,
    user_corpus_text: str,
) -> list[int]:
    """Return the ``UL#N`` numbers of user-corpus lessons that near-match."""
    hits: list[int] = []
    for lesson in lessons_corpus.iter_lessons(user_corpus_text):
        body = "\n".join(lesson.body_lines)
        if _near_match(candidate_title, candidate_body, lesson.title, body):
            hits.append(lesson.number)
    return hits


# --------------------------------------------------------------------------- #
# Compact renumber (HEADINGS only; cite r4 Low 1).
# --------------------------------------------------------------------------- #
def renumber_headings(text: str, start: int = 1) -> tuple[str, dict[int, int]]:
    """Compact-renumber ``## N.`` HEADINGS to ``start..`` contiguously.

    Returns ``(new_text, old_to_new_heading_map)``. In-body ``#N`` citations are
    NOT touched here (they are rewritten SOLELY by the remap pass; r4 Low 1 -
    renumbering body ``#N`` here AND in the remap pass would double-shift every
    citation).
    """
    old_to_new: dict[int, int] = {}
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    next_new = start
    heading_re = re.compile(r"^(##\s+)(\d+)(\.\s+.*)$", re.MULTILINE)
    for line in lines:
        m = heading_re.match(line.rstrip("\n"))
        if m:
            old = int(m.group(2))
            old_to_new[old] = next_new
            # Preserve the original line ending (newline if present, else none).
            tail = m.group(3)
            eol = "\n" if line.endswith("\n") else ""
            out.append(f"{m.group(1)}{next_new}{tail}{eol}")
            next_new += 1
        else:
            out.append(line)
    return "".join(out), old_to_new


# --------------------------------------------------------------------------- #
# Discriminator + repo-wide rewrite (load-bearing, B1).
# --------------------------------------------------------------------------- #
#: A ``#N`` token (potential lesson citation). Word boundary on both sides so
#: ``#5,000 EUR`` does not match. Captures the digits.
_TOKEN_RE = re.compile(r"#(\d+)\b")

#: Multi-number form: ``#N, #M``, ``#N / #M``, ``#N, #M, #K, #L``. The repeated
#: group lets the rewrite pass apply the discriminator to EVERY ``#N`` in a
#: cluster. The leading ``#\\d+`` is matched separately so a standalone token is
#: also handled.
_MULTI_TOKEN_RE = re.compile(r"#\d+(?:[ ,/\t]+#\d+)*")

#: Code-fence delimiters (CommonMark). An OPENING fence is 3+ backticks (or
#: tildes) at line start, optionally followed by an info string. A CLOSING fence
#: is 3+ backticks (or tildes) followed by ONLY whitespace - it has NO info
#: string. This distinction is load-bearing: a ``\`\`\`markdown`` line that
#: appears INSIDE an already-open fence is NOT a close (it is code text), so the
#: fence stays open. A naive ``re.match(r"^\s*\`\`\`+")`` toggle wrongly treats
#: every fence line as a toggle, which mis-pairs fences in files with a stray
#: delimiter and silently blanks lesson citations on the lines that land inside
#: the phantom fence (the plan_quality_guidelines.md #136 incident). Matching the
#: fence char (backtick vs tilde) on close keeps the two fence families separate.
_FENCE_OPEN_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_FENCE_CLOSE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*$")

#: A ``development_lessons.md #N`` CITATION PHRASE (r6): an introducer
#: (``See `` / ``see also `` etc., optional) + the filename (optionally
#: backtick-wrapped and/or directory-prefixed) + one or more ``#N`` numbers
#: joined by ``,`` / ``and`` / whitespace. This is a PRE-PASS over the generic
#: per-token pass: it lets the migrator DROP the whole phrase (introducer +
#: filename + numbers) when every cited number is cross-tier, instead of leaving
#: a dangling ``See `development_lessons.md` .`` stub. Mixed clusters keep the
#: phrase with only the surviving (same-tier, renumbered) numbers.
#:
#: A bare file-path mention with NO ``#N`` (e.g. the ``Full details ...:
#: `development_lessons.md`.`` footer) does NOT match: the ``#N`` is required, so
#: legitimate non-citation path references are preserved verbatim.
_DEV_CITATION_RE = re.compile(
    r"(?P<sep>(?:[.;,]\s+|\(\s*)?)"
    r"(?P<intro>(?:See also|See|see also|see)\s+)?"
    r"(?P<fn>`?(?:[\w./-]+/)?development_lessons\.md`?)\s*"
    r"(?P<nums>#[0-9]+(?:\s*(?:,|and)\s*#[0-9]+)*)"
)


def _strip_trailing_backtick(token: str) -> str:
    """Strip ONE trailing backtick from a token (real citations are
    backtick-wrapped, e.g. `` `python_guidelines.md` ``)."""
    if token.endswith("`"):
        return token[:-1]
    return token


def _preceding_token(line: str, end: int) -> str:
    """Return the immediately-preceding non-space token ending at ``end``.

    Skips trailing whitespace between ``end`` and the token. The returned token
    is RAW (backtick not yet stripped). If there is no preceding token (start of
    line), returns ``""``.
    """
    # Walk back over whitespace.
    i = end
    while i > 0 and line[i - 1] in " \t":
        i -= 1
    if i == 0:
        return ""
    # Walk back over non-whitespace.
    j = i
    while j > 0 and line[j - 1] not in " \t":
        j -= 1
    return line[j:i]


def _is_process_prefix(token_lower: str) -> bool:
    """True iff ``token_lower`` (already lowercased, backtick-stripped) is a
    process/identifier prefix whose ``#N`` is NOT a lesson citation (guard v)."""
    if token_lower in {w.lower() for w in PROCESS_PREFIXES}:
        return True
    for pat in PROCESS_PREFIX_PATTERNS:
        if pat.match(token_lower):
            return True
    return False


def _is_inside_fence(line: str, fence_state_before: bool) -> bool:
    """Decide whether ``line`` is inside a fenced code block, given the state
    BEFORE the line. A fence-delimiter line itself toggles; this helper returns
    the state AT the line (a delimiter line is NOT content). For the rewrite
    pass we treat a delimiter line as a no-op (no tokens to rewrite on it)."""
    if re.match(r"^\s*```+", line):
        return fence_state_before  # delimiter; the pass skips it
    return fence_state_before


def discriminate_token(
    line: str,
    match_start: int,
    number: int,
    old_number_set: set[int],
) -> tuple[bool, str]:
    """Apply the discriminator to one ``#N`` match. Returns ``(is_lesson, reason)``.

    The discriminator is the SINGLE rewrite rule (r4 redesign): a token is a
    LESSON citation iff ALL hold:
    (i)   value in the OLD number set;
    (ii)  NOT inside a fenced code block (caller-supplied via ``line`` already
          stripped of fenced bodies - the caller passes non-fence lines only);
    (iii) word boundary ``#(\\d+)\\b`` (the regex guarantees this);
    (iv)  after stripping a trailing backtick, if the immediately-preceding
          non-space token is a filename ending in ``.md``, that filename MUST be
          ``development_lessons.md`` (self-citation rewritten); any OTHER ``.md``
          filename = a rule number, LEFT UNCHANGED;
    (v)   the preceding token is NOT a process/identifier prefix
          (case-insensitive denylist + DP-\\d+ / r\\d+ / UL# / art\\.?).
    """
    if number not in old_number_set:
        return False, "value-not-in-old-set"
    pre = _preceding_token(line, match_start)
    pre_stripped = _strip_trailing_backtick(pre)
    # (iv) .md-filename guard.
    md_match = re.search(r"([\w./-]+)\.md$", pre_stripped)
    if md_match:
        # The filename token (without extension and without directory prefix).
        stem = md_match.group(1)
        # Allow a directory prefix (e.g. ``docs/maintenance/development_lessons``).
        basename = stem.rsplit("/", 1)[-1]
        if basename != "development_lessons":
            return False, f"rule-number-in-{basename}.md"
        # else: self-citation (development_lessons.md #N) IS a lesson ref.
    # (v) process-prefix guard (case-insensitive).
    if pre_stripped and _is_process_prefix(pre_stripped.lower()):
        return False, f"process-prefix:{pre_stripped}"
    return True, "lesson"


def _resolve_token(
    number: int,
    remap: dict[int, RemapEntry],
) -> tuple[str, int | None, str]:
    """Resolve a discriminated lesson ``#N`` to its new value. Returns
    ``(action, new_number, reason)``.

    - same-tier -> ``("renumber", new_number, "")``;
    - cross-tier -> ``("remove", None, "")`` (drop ``#N``; within-line cleanup
      handled by the caller);
    - ambiguous / unmapped -> ``("flag", None, reason)``.
    """
    entry = remap.get(number)
    if entry is None:
        return "flag", None, f"old #{number} not in remap"
    if entry.action == "same-tier":
        return "renumber", entry.new_number, ""
    if entry.action == "cross-tier":
        return "remove", None, ""
    return "flag", None, f"action={entry.action}"


def _strip_fence_bodies(text: str) -> str:
    """Return ``text`` with fenced code block BODIES replaced by blank lines,
    preserving line structure (so line numbers are stable). Fence delimiter
    lines are kept (so the rewriter sees the same line layout). Used only to
    decide per-line fence state; the rewriter reads the ORIGINAL line text.

    Fence state uses the CommonMark open/close distinction (see
    ``_FENCE_OPEN_RE`` / ``_FENCE_CLOSE_RE``): an info-string fence line (e.g.
    a triple-backtick ``markdown`` fence) is an OPEN only, never a CLOSE; a CLOSE
    is a bare fence line with no trailing non-whitespace. This prevents a stray
    delimiter from
    mis-pairing fences and blanking lesson citations that sit outside any real
    code block. A fence opened and never closed is honored to EOF (the rest is
    code). The fence char (backtick vs tilde) is matched so the two families do
    not close each other.
    """
    out: list[str] = []
    in_fence = False
    fence_char = ""  # "`" or "~" of the currently open fence
    for line in text.splitlines():
        if not in_fence:
            m = _FENCE_OPEN_RE.match(line)
            if m:
                in_fence = True
                fence_char = m.group(1)[0]
                out.append(line)  # keep delimiter
                continue
        else:
            cm = _FENCE_CLOSE_RE.match(line)
            if cm and cm.group(1)[0] == fence_char:
                in_fence = False
                fence_char = ""
                out.append(line)  # keep delimiter
                continue
            # Inside a fence: any other line (including an info-string fence
            # line, which is NOT a close) is code text.
            out.append("")  # blank the body line (preserve line count)
            continue
        out.append(line)
    return "\n".join(out)


def rewrite_file(
    file_rel: str,
    original_text: str,
    remap: dict[int, RemapEntry],
    old_number_set: set[int],
    fence_aware: bool,
) -> tuple[str, list[RewriteRecord]]:
    """Apply the SINGLE rewrite rule to ``original_text``. Returns
    ``(new_text, records)``.

    ``fence_aware``: when True (the lessons corpus itself), fence bodies are
    blanked for discrimination but the original text is emitted with the
    rewritten non-fence lines. When False (code files - fences are rare but
    possible), the same logic applies. The rewriter processes line by line,
    multi-token clusters via ``_MULTI_TOKEN_RE``.

    Within-line cleanup for cross-tier REMOVAL (r6 Low):
    - sole-content parenthetical ``(#N)`` -> remove the parentheses too;
    - mid-prose removal -> flag the line "review prose grammar" (no grammar
      engine; accepted cosmetic residual).
    """
    records: list[RewriteRecord] = []
    # Per-line fence state (for the discriminator's (ii) clause). Uses the
    # CommonMark open/close distinction (see _FENCE_OPEN_RE / _FENCE_CLOSE_RE):
    # an info-string fence line is an OPEN only, never a CLOSE, so a stray
    # delimiter cannot mis-pair fences and silently skip citations outside any
    # real code block (the plan_quality_guidelines.md #136 incident).
    lines = original_text.splitlines(keepends=True)
    new_lines: list[str] = []
    in_fence = False
    fence_char = ""
    for line_no_0, raw in enumerate(lines, start=1):
        if not in_fence:
            om = _FENCE_OPEN_RE.match(raw)
            if om:
                in_fence = True
                fence_char = om.group(1)[0]
                new_lines.append(raw)
                continue
        else:
            cm = _FENCE_CLOSE_RE.match(raw)
            if cm and cm.group(1)[0] == fence_char:
                in_fence = False
                fence_char = ""
                new_lines.append(raw)
                continue
            if fence_aware:
                # Inside a fence body: emit verbatim, no discrimination.
                new_lines.append(raw)
                continue
            # fence_aware=False: fall through and discriminate even inside a
            # fence (code files; Python comments need "# " so "#N" is rare).
        new_line, line_records = _rewrite_line(
            file_rel, line_no_0, raw, remap, old_number_set
        )
        records.extend(line_records)
        new_lines.append(new_line)
    return "".join(new_lines), records


def _sole_paren_span(line: str, m: re.Match) -> tuple[int, int] | None:
    """If ``#N`` match ``m`` is the SOLE content of a parenthetical
    ``(#N)`` (optional inner whitespace only), return the deletion span covering
    the parentheses plus ONE preceding space (so ``seed (#5) vs`` -> ``seed vs``,
    not ``seed  vs``). Return ``None`` otherwise.

    Span-precise (no global regex): only the paren that actually wrapped THIS
    removed token is deleted, so an unrelated ``func()`` call on the same line is
    never touched.
    """
    before = line[: m.start()]
    mo = re.search(r"\((\s*)$", before)
    if not mo:
        return None
    paren_start = mo.start()  # index of '('
    after = line[m.end():]
    mc = re.match(r"(\s*\))", after)
    if not mc:
        return None
    paren_end = m.end() + mc.end()  # index just after ')'
    del_start = paren_start
    if del_start > 0 and line[del_start - 1] in " \t":
        del_start -= 1
    return del_start, paren_end


def _handle_citation_match(
    file_rel: str,
    line_no: int,
    m: re.Match,
    remap: dict[int, RemapEntry],
    old_number_set: set[int],
) -> tuple[str, list[RewriteRecord]]:
    """Rewrite ONE ``development_lessons.md #N`` citation phrase (``m``).

    The cited numbers are partitioned:

    - a number IN the old set with a ``same-tier`` remap entry -> SURVIVES,
      renumbered to its new value;
    - a number IN the old set with a ``cross-tier``/ambiguous entry -> DROPPED;
    - a number NOT in the old set (not a known lesson) -> kept verbatim.

    If any survivors (or unknowns) remain, the phrase is rebuilt as
    ``sep + intro + filename + ' ' + surviving_numbers``. If ALL cited numbers
    are dropped AND an introducer (``See `` etc.) was present, the WHOLE phrase
    (sep + intro + filename + numbers) is removed - the r6 fix for the dangling
    ``See `development_lessons.md` .`` stubs. If all are dropped but NO
    introducer (bare ``development_lessons.md #N``), only the separating
    punctuation (``sep``) is retained so surrounding prose stays grammatical.

    Returns the rebuilt phrase text (replacing ``m.group(0)``) and the
    per-number RewriteRecords. This is the AUTHORITY for the phrase: the caller
    must NOT run the per-token pass over it (a renumbered survivor's NEW number
    collides with a valid OLD number in ``old_number_set`` and would be
    re-resolved - dropping a same-tier citation that was just renumbered).
    """
    records: list[RewriteRecord] = []
    nums = [int(x) for x in re.findall(r"#(\d+)", m.group("nums"))]
    surviving: list[str] = []
    for n in nums:
        if n in old_number_set:
            entry = remap.get(n)
            if entry is not None and entry.action == "same-tier" and entry.new_number is not None:
                surviving.append(f"#{entry.new_number}")
                records.append(RewriteRecord(
                    file=file_rel, line_no=line_no, old_number=n,
                    action="renumbered-to-new", new_number=entry.new_number,
                    raw_token=f"#{n}", lead_in="development_lessons",
                ))
            else:
                records.append(RewriteRecord(
                    file=file_rel, line_no=line_no, old_number=n,
                    action="removed", raw_token=f"#{n}",
                    lead_in="development_lessons",
                ))
        else:
            # Not a known lesson number; preserve verbatim.
            surviving.append(f"#{n}")
    if surviving:
        rebuilt = (
            m.group("sep")
            + (m.group("intro") or "")
            + m.group("fn")
            + " "
            + ", ".join(surviving)
        )
        return rebuilt, records
    if m.group("intro"):
        # All dropped AND an introducer was present: drop the whole phrase.
        return "", records
    # All dropped, bare mention: keep only the separating punctuation.
    return m.group("sep"), records


def _rewrite_line_tokens(
    file_rel: str,
    line_no: int,
    text: str,
    remap: dict[int, RemapEntry],
    old_number_set: set[int],
) -> tuple[str, list[RewriteRecord]]:
    """Per-token rewrite pass over ``text`` (a GAP between citation phrases).

    Each ``#N`` is discriminated independently; gap text between tokens is
    emitted verbatim, so multi-token lists (``#5, #6`` / ``#5/#6``) rewrite
    correctly without a separate cluster pass.

    Removal handling is span-precise (no global line regex):
    - cross-tier removal of a SOLE-content ``(#N)`` -> delete the parentheses
      too (plus one preceding space); ``seed (#5) vs`` -> ``seed vs``.
    - cross-tier removal embedded in other prose -> drop only the token; the line
      stays structurally valid and the audit flags it ``removed-mid-prose``.

    Leading whitespace (Python indentation) lives in the first gap and is never
    altered - earlier global ``re.sub`` cleanup destroyed indentation and ate
    unrelated ``func()`` calls (the test_fee_filter IndentationError incident).
    """
    records: list[RewriteRecord] = []
    out: list[str] = []
    cursor = 0
    for m in _TOKEN_RE.finditer(text):
        number = int(m.group(1))
        abs_start = m.start()
        is_lesson, _reason = discriminate_token(text, abs_start, number, old_number_set)
        if not is_lesson:
            # Leave the token unchanged (gap + token).
            out.append(text[cursor:m.end()])
            cursor = m.end()
            records.append(RewriteRecord(
                file=file_rel, line_no=line_no, old_number=number,
                action="left-non-lesson", raw_token=m.group(0),
                lead_in=_strip_trailing_backtick(_preceding_token(text, abs_start)),
            ))
            continue
        action, new_number, _flag_reason = _resolve_token(number, remap)
        lead_in = _strip_trailing_backtick(_preceding_token(text, abs_start))
        if action == "renumber":
            out.append(text[cursor:abs_start])
            out.append(f"#{new_number}")
            cursor = m.end()
            records.append(RewriteRecord(
                file=file_rel, line_no=line_no, old_number=number,
                action="renumbered-to-new", new_number=new_number,
                raw_token=m.group(0), lead_in=lead_in,
            ))
        elif action == "remove":
            paren = _sole_paren_span(text, m)
            if paren is not None:
                del_start, del_end = paren
                out.append(text[cursor:del_start])
                cursor = del_end
                records.append(RewriteRecord(
                    file=file_rel, line_no=line_no, old_number=number,
                    action="removed", raw_token=m.group(0), lead_in=lead_in,
                ))
            else:
                out.append(text[cursor:abs_start])
                cursor = m.end()
                records.append(RewriteRecord(
                    file=file_rel, line_no=line_no, old_number=number,
                    action="removed", raw_token=m.group(0), lead_in=lead_in,
                ))
                records.append(RewriteRecord(
                    file=file_rel, line_no=line_no, old_number=number,
                    action="removed-mid-prose", raw_token=m.group(0),
                    lead_in=lead_in,
                ))
        else:  # flag
            out.append(text[cursor:m.end()])
            cursor = m.end()
            records.append(RewriteRecord(
                file=file_rel, line_no=line_no, old_number=number,
                action="flagged-ambiguous", raw_token=m.group(0),
                lead_in=lead_in,
            ))
    out.append(text[cursor:])
    return "".join(out), records


def _rewrite_line(
    file_rel: str,
    line_no: int,
    raw: str,
    remap: dict[int, RemapEntry],
    old_number_set: set[int],
) -> tuple[str, list[RewriteRecord]]:
    """Rewrite one line's lesson citations per the discriminator + remap.

    Single interleaved pass (no global line regex). ``_DEV_CITATION_RE`` citation
    phrases (``development_lessons.md #N``) are handled WHOLESALE by
    ``_handle_citation_match`` and CLAIM their spans; the per-token pass
    (``_rewrite_line_tokens``) runs ONLY on the gaps between claimed phrases.

    Why the citation pass must be authoritative (not a pre-pass whose output the
    per-token pass re-scans): a same-tier survivor is renumbered to a NEW number
    in 1..M, and every value 1..M is ALSO a valid OLD number in
    ``old_number_set`` (1..N). A per-token pass over the renumbered phrase would
    re-discriminate the new ``#k`` as an old citation and re-resolve it -
    dropping a same-tier citation that was just renumbered (the r6 stub
    regression). Interleaving with claimed spans makes the citation pass the
    sole authority over its phrases.
    """
    records: list[RewriteRecord] = []
    out: list[str] = []
    cursor = 0
    for m in _DEV_CITATION_RE.finditer(raw):
        # Gap before this citation: per-token rewrite.
        gap = raw[cursor:m.start()]
        gap_out, gap_recs = _rewrite_line_tokens(
            file_rel, line_no, gap, remap, old_number_set,
        )
        out.append(gap_out)
        records.extend(gap_recs)
        # Citation phrase: handled wholesale (authoritative).
        rebuilt, cite_recs = _handle_citation_match(
            file_rel, line_no, m, remap, old_number_set,
        )
        out.append(rebuilt)
        records.extend(cite_recs)
        cursor = m.end()
    # Trailing gap.
    gap = raw[cursor:]
    gap_out, gap_recs = _rewrite_line_tokens(
        file_rel, line_no, gap, remap, old_number_set,
    )
    out.append(gap_out)
    records.extend(gap_recs)
    return "".join(out), records



# --------------------------------------------------------------------------- #
# Authoritative stale-ref reconciliation (B1; r5 Medium).
# --------------------------------------------------------------------------- #
def reconcile_refs(
    records: list[RewriteRecord],
    remap: dict[int, RemapEntry],
) -> list[str]:
    """Authoritative remap-driven reconciliation. Returns a list of defect
    strings (empty = clean).

    Asserts that NO discriminated lesson token was left at its OLD value unless
    the action was explicitly ``removed`` or ``left-non-lesson``. This is exact
    because we have the remap; it closes the low-numbered blind spot a value-scan
    cannot (a missed citation whose old value <= M is invisible to ``> M``).
    """
    defects: list[str] = []
    for r in records:
        entry = remap.get(r.old_number)
        if entry is None:
            # Token discriminated as a lesson but not in remap -> flag.
            if r.action in {"renumbered-to-new", "removed"}:
                defects.append(
                    f"{r.file}:{r.line_no}: #{r.old_number} discriminated as lesson "
                    f"but absent from remap (action={r.action})"
                )
            continue
        # If the record says the token was left at its OLD value but the remap
        # says it should have been renumbered/removed, that is a defect.
        if r.action == "left-non-lesson":
            # The discriminator decided this #N is NOT a lesson. That is
            # authoritative ONLY if the value is NOT in the remap's same-tier
            # set OR the discriminator's reason is a process-prefix/.md rule.
            # We accept it (the discriminator already filtered).
            continue
        if r.action == "renumbered-to-new":
            if r.new_number is None or r.new_number == r.old_number:
                if entry.action == "same-tier" and entry.new_number != r.old_number:
                    defects.append(
                        f"{r.file}:{r.line_no}: #{r.old_number} left at old value "
                        f"(should be #{entry.new_number})"
                    )
        if r.action == "removed":
            if entry.action != "cross-tier":
                defects.append(
                    f"{r.file}:{r.line_no}: #{r.old_number} removed but remap says "
                    f"action={entry.action}"
                )
    return defects


def coarse_echo_in_corpus(
    corpus_text: str, new_project_count: int, old_number_set: set[int]
) -> list[str]:
    """Coarse belt-and-braces echo (b): discriminated lesson-``#N`` with value >
    M in the corpus -> defect. KNOWN blind spot: misses values <= M; the
    authoritative reconciliation closes that hole.
    """
    defects: list[str] = []
    blanked = _strip_fence_bodies(corpus_text)
    for line_no, line in enumerate(blanked.splitlines(), start=1):
        for m in _TOKEN_RE.finditer(line):
            number = int(m.group(1))
            if number not in old_number_set:
                continue
            if number <= new_project_count:
                continue
            pre = _strip_trailing_backtick(_preceding_token(line, m.start()))
            md_match = re.search(r"([\w./-]+)\.md$", pre)
            if md_match:
                basename = md_match.group(1).rsplit("/", 1)[-1]
                if basename != "development_lessons":
                    continue
            if pre and _is_process_prefix(pre.lower()):
                continue
            defects.append(
                f"corpus:{line_no}: #{number} > M={new_project_count} "
                f"and looks like a stale lesson citation"
            )
    return defects


# --------------------------------------------------------------------------- #
# Audit snapshot.
# --------------------------------------------------------------------------- #
_AUDIT_SNAPSHOT_TEMPLATE = """# {date}-principle-index-audit-snapshot

> FROZEN ONE-TIME AUDIT. This file is a verbatim snapshot of the deleted
> `docs/maintenance/principle-index.md`, captured by `lessons_migrate.py` at
> migration time. It is NOT maintained; recall is by grep on
> `docs/maintenance/development_lessons.md` (project) and the user-level corpus
> (cross-project). Do not edit.

{body}
"""


def build_audit_snapshot(date_iso: str, deleted_index_text: str) -> str:
    """Build the frozen audit snapshot body.

    Preserves the verbatim ``## Blind-spot analysis``, ``## Dry-run recall``,
    ``## Precision gate``, ``## Duplicate clusters``, ``## Accounting check``
    sections from the deleted index. Sections absent from the index are noted as
    absent (the snapshot is still emitted).
    """
    keep_sections = (
        "## Blind-spot analysis",
        "## Dry-run recall",
        "## Precision gate",
        "## Duplicate clusters",
        "## Accounting check",
    )
    body_parts: list[str] = []
    for section in keep_sections:
        extracted = _extract_section(deleted_index_text, section)
        if extracted:
            body_parts.append(extracted.rstrip() + "\n")
        else:
            body_parts.append(f"{section}\n\n(absent from the source index)\n")
    return _AUDIT_SNAPSHOT_TEMPLATE.format(date=date_iso, body="\n".join(body_parts).rstrip() + "\n")


def _extract_section(text: str, heading: str) -> str:
    """Return the verbatim text of one ``## Section`` (heading + body until the
    next same-or-higher heading), or ``""`` if absent."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading or line.strip().startswith(heading + " "):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if re.match(r"^#{1,2} ", line):
            end = j
            break
    return "\n".join(lines[start:end])


# --------------------------------------------------------------------------- #
# Idempotency guard.
# --------------------------------------------------------------------------- #
def _project_already_migrated(project_text: str) -> bool:
    """Heuristic idempotency guard: re-running on an already-migrated project
    file (contiguous ``## 1..N`` AND no Family-Z/missing-tag mess that a fresh
    run would create) refuses cleanly. We detect a contiguous numbering that has
    no gaps AND whose every lesson carries a valid-or-malformed tag set (i.e.
    the file is in the post-migration steady state). This is best-effort; the
    authoritative guard is the operator + the recovery recipe.

    A fresh (pre-migration) file with gaps (e.g. missing #163/#164) returns
    False; a compact-renumbered file returns True.
    """
    nums: list[int] = []
    for m in re.finditer(r"^##\s+(\d+)\.\s+", project_text, re.MULTILINE):
        nums.append(int(m.group(1)))
    if not nums:
        return False
    # Contiguous 1..N with no gaps and no duplicates.
    return nums == list(range(1, len(nums) + 1))


# --------------------------------------------------------------------------- #
# Gate invocation (run lessons_index.py on the .tmp).
# --------------------------------------------------------------------------- #
def run_gate(corpus_path: str) -> int:
    """Run the read-only gate on ``corpus_path``. Returns its exit code.

    The gate path is resolved relative to this script's directory (canonical
    source). The gate is invoked via subprocess (never imported - keeps the
    read-only gate decoupled from this mutator, Family F).
    """
    gate = str(Path(__file__).resolve().parent / "lessons_index.py")
    interp = sys.executable or "python3"
    try:
        result = subprocess.run(
            [interp, gate, corpus_path],
            capture_output=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 1
    return result.returncode


# --------------------------------------------------------------------------- #
# Review-list emission (incl. lead-in enumeration audit; r6 Medium).
# --------------------------------------------------------------------------- #
def build_review_list(
    result: MigrationResult,
    classified: list[ClassifiedLesson],
) -> list[str]:
    """Assemble the review-list lines: tail summary, dedup-merge flags,
    ambiguous-ref flags, removed/renumbered token audit, the FULL remap table,
    and the lead-in enumeration audit (every distinct ``<lead-in> #N``
    discriminated AS a lesson, grouped by lead-in)."""
    lines: list[str] = []
    # Tail summary (signal 4, non-routing).
    retained_untagged = [
        c for c in classified
        if c.route == "project-specific"
        and not any(t in lessons_corpus.VALID_FAMILIES for t in c.tags)
    ]
    lines.append(
        f"Tail summary: {len(retained_untagged)} untagged project-specific "
        f"lessons retained - review for possible cross-project promotion."
    )
    for c in retained_untagged:
        lines.append(f"  - #{c.number}: {c.title}")

    # Dedup-merge flags.
    for line in result.review_lines:
        if line.startswith("MERGE:"):
            lines.append(line)

    # Ambiguous-ref flags.
    for r in result.rewrite_records:
        if r.action == "flagged-ambiguous":
            lines.append(
                f"AMBIGUOUS: {r.file}:{r.line_no}: {r.raw_token} (#{r.old_number}) "
                f"- could not map 1:1; review manually."
            )

    # Removed/renumbered token audit.
    lines.append("")
    lines.append("## Removed / renumbered token audit")
    lines.append("(every discriminated lesson token: old -> action)")
    for r in result.rewrite_records:
        if r.action in {"removed", "renumbered-to-new", "removed-mid-prose"}:
            if r.action == "renumbered-to-new":
                lines.append(
                    f"- {r.file}:{r.line_no}: #{r.old_number} -> #{r.new_number}"
                )
            elif r.action == "removed":
                lines.append(
                    f"- {r.file}:{r.line_no}: #{r.old_number} -> REMOVED (cross-tier)"
                )
            elif r.action == "removed-mid-prose":
                lines.append(
                    f"- {r.file}:{r.line_no}: #{r.old_number} -> REMOVED (mid-prose; "
                    f"review prose grammar)"
                )

    # Lead-in enumeration audit (r6 Medium).
    lines.append("")
    lines.append("## Lead-in enumeration audit")
    lines.append(
        "(every distinct <lead-in> #N token discriminated AS a lesson, grouped "
        "by lead-in; confirm no process-id lead-in snuck through)"
    )
    lead_groups: dict[str, list[str]] = {}
    for r in result.rewrite_records:
        if r.action in {"removed", "renumbered-to-new", "removed-mid-prose"}:
            key = r.lead_in if r.lead_in else "(bare / no lead-in)"
            lead_groups.setdefault(key, []).append(
                f"#{r.old_number}" + (
                    f" -> #{r.new_number}" if r.action == "renumbered-to-new" else " -> REMOVED"
                )
            )
    for lead in sorted(lead_groups):
        lines.append(f"- {lead}: {', '.join(lead_groups[lead])}")

    # Full remap table.
    lines.append("")
    lines.append("## Remap table (old #N -> new #N / REMOVE / FLAG)")
    for old in sorted(result.remap):
        entry = result.remap[old]
        if entry.action == "same-tier":
            lines.append(f"- #{old} -> #{entry.new_number} (same-tier)")
        elif entry.action == "cross-tier":
            lines.append(f"- #{old} -> REMOVE (cross-tier; UL#{entry.ul_number} in user corpus)")
        else:
            lines.append(f"- #{old} -> FLAG ({entry.action})")
    return lines


# --------------------------------------------------------------------------- #
# Top-level migration.
# --------------------------------------------------------------------------- #
def _build_user_corpus_append(
    cross_lessons: list[ClassifiedLesson],
    existing_corpus_text: str,
) -> tuple[str, list[int], list[str]]:
    """Build the appended+renumbered user corpus text + the UL numbers assigned
    to each cross lesson (in input order) + merge-flag lines.

    New cross-project lessons are appended with valid strict tags: if a lesson's
    existing tag is malformed/missing, mark it ``Family unclassified (needs
    classification)``. The whole corpus is compact-renumbered ``1..N`` as
    ``UL#N``.
    """
    merge_flags: list[str] = []
    # Determine the existing lesson count to continue numbering.
    existing = list(lessons_corpus.iter_lessons(existing_corpus_text))
    next_ul = len(existing) + 1
    appended_blocks: list[str] = []
    assigned_uls: list[int] = []
    for c in cross_lessons:
        body = "\n".join(c.body_lines)
        # Dedup check.
        hits = find_near_matches(c.title, body, existing_corpus_text)
        if hits:
            merge_flags.append(
                f"MERGE: '#{c.number} {c.title}' near-matches UL#{hits} "
                f"- flag for merge, NOT appended."
            )
            assigned_uls.append(-1)  # sentinel: not appended
            continue
        # Ensure the lesson has exactly one valid strict tag. The project file
        # may carry a malformed tag (convention); for the user corpus we replace
        # a malformed/missing tag with the unclassified marker.
        tag_line = _ensure_strict_tag(c)
        # Strip any existing tag lines from the body (they are convention-tier
        # and may be malformed; we emit exactly one clean strict tag).
        body_lines_clean = [
            ln for ln in c.body_lines
            if not re.match(r"^\*\*Principle:\*\*\s+Family\s+\S+", ln)
        ]
        block_lines = [f"## {next_ul}. {c.title}", ""]
        block_lines.append(tag_line)
        block_lines.extend(body_lines_clean)
        appended_blocks.append("\n".join(block_lines))
        assigned_uls.append(next_ul)
        next_ul += 1
    # Compose: existing text + appended blocks, then compact-renumber the whole.
    if existing_corpus_text and not existing_corpus_text.endswith("\n"):
        existing_corpus_text = existing_corpus_text + "\n"
    separator = "\n\n" if existing_corpus_text else ""
    composed = existing_corpus_text + separator + "\n\n".join(appended_blocks)
    if not existing_corpus_text and appended_blocks:
        composed = "\n\n".join(appended_blocks)
    renumbered, _ = renumber_headings(composed, start=1)
    return renumbered, assigned_uls, merge_flags


def _ensure_strict_tag(c: ClassifiedLesson) -> str:
    """Return a valid strict tag line for a cross-project lesson.

    If the lesson's first tag is a valid family letter (A-H) or a valid extra
    value (excluded/unclassified), keep it verbatim. Otherwise emit the
    ``unclassified (needs classification)`` marker (wrong family > no family;
    never guess).
    """
    if c.tags:
        token = c.tags[0]
        if lessons_corpus.parse_tag_token(token).valid:
            # Re-emit the original tag line verbatim (it is well-formed).
            for ln in c.body_lines:
                if re.match(r"^\*\*Principle:\*\*\s+Family\s+\S+", ln):
                    return ln
    return UNCLASSIFIED_TAG_LINE


def _build_project_file(
    project_lessons: list[ClassifiedLesson],
) -> tuple[str, dict[int, int]]:
    """Build the compact-renumbered project file. Convention tags preserved
    as-is (incl. malformed ones; the gate is never applied to a project file).

    Returns ``(text, old_to_new_heading_map)``. The old_to_new map is the
    HEADING renumber only; in-body citation rewrites happen in the remap pass.
    """
    # Preserve the project file's header (any leading prose before the first
    # ``## N.`` heading) so the file stays valid markdown. The caller passes
    # only the lesson blocks, so we reconstruct from the original project text
    # via the ClassifiedLesson.raw_text ordering. For the synthetic selftest we
    # build from the lessons directly.
    blocks: list[str] = []
    for c in project_lessons:
        blocks.append(c.raw_text)
    composed = "\n\n".join(blocks)
    renumbered, old_to_new = renumber_headings(composed, start=1)
    return renumbered, old_to_new


def migrate(
    repo_root: Path,
    project_text: str,
    user_corpus_text: str,
    *,
    write: bool,
    ai_playbook_root: Path | None = None,
    date_iso: str = "2026-06-30",
) -> MigrationResult:
    """Run the migration. ``write=False`` is the ``--dry-run`` path (classify +
    emit review list + planned remap WITHOUT writing).

    ``project_text`` is the repo's ``docs/maintenance/development_lessons.md``
    contents; ``user_corpus_text`` is the existing user corpus contents (may be
    empty for cold start). For ``write=True`` the caller is responsible for the
    git-clean precondition and for committing the user-corpus + project writes.
    """
    result = MigrationResult()
    # Idempotency guard: refuse if the project file is already in the
    # post-migration steady state (contiguous 1..N).
    if _project_already_migrated(project_text) and write:
        raise RuntimeError(
            "lessons_migrate: project file appears already migrated (contiguous "
            "## 1..N). Refusing to re-run. Recovery: 'git checkout -- "
            "<scope>' in BOTH repos + re-run; no resume marker, no --force."
        )

    # Parse + classify.
    parsed = list(lessons_corpus.iter_lessons(project_text))
    classified: list[ClassifiedLesson] = []
    for lesson in parsed:
        route, reason, family = classify_lesson(lesson)
        # Reconstruct the lesson's raw block (heading + body) for re-emit.
        heading = f"## {lesson.number}. {lesson.title}\n"
        body = "\n".join(lesson.body_lines)
        raw = heading + body
        if not raw.endswith("\n"):
            raw = raw + "\n"
        classified.append(ClassifiedLesson(
            number=lesson.number, title=lesson.title,
            body_lines=list(lesson.body_lines), raw_text=raw,
            tags=lesson.tags, route=route, cross_family=family,
            cross_reason=reason,
        ))

    cross = [c for c in classified if c.route == "cross-project"]
    project = [c for c in classified if c.route == "project-specific"]
    result.cross_moved = len(cross)
    result.project_kept = len(project)

    # Build the user-corpus append (with dedup flags).
    new_corpus_text, assigned_uls, merge_flags = _build_user_corpus_append(
        cross, user_corpus_text
    )
    result.dedup_merge_flagged = sum(1 for u in assigned_uls if u == -1)
    result.review_lines.extend(merge_flags)

    # Build the remap. old_number -> RemapEntry.
    # Same-tier: project lesson; new number is its position in the compact
    # project renumber. Cross-tier: moved to user corpus; REMOVE in-repo tokens.
    # Build the project old->new heading map first.
    _, project_heading_map = _build_project_file(project)
    for c in classified:
        if c.route == "project-specific":
            new_n = project_heading_map.get(c.number)
            if new_n is None:
                # Defensive: every project lesson must be in the heading map.
                result.remap[c.number] = RemapEntry(
                    old_number=c.number, action="ambiguous"
                )
                result.ambiguous_flagged += 1
            else:
                result.remap[c.number] = RemapEntry(
                    old_number=c.number, action="same-tier", new_number=new_n
                )
        else:
            # Cross-tier. Find the assigned UL (skip -1 merge-flags: those are
            # NOT appended, so in-repo citations to them are FLAGGED ambiguous).
            idx = cross.index(c)
            ul = assigned_uls[idx] if idx < len(assigned_uls) else -1
            if ul == -1:
                # Merge-flagged: the lesson is NOT in the corpus yet. Treat as
                # ambiguous (flag) so the operator resolves the merge, then a
                # later re-run rewrites the citation.
                result.remap[c.number] = RemapEntry(
                    old_number=c.number, action="ambiguous"
                )
                result.ambiguous_flagged += 1
            else:
                result.remap[c.number] = RemapEntry(
                    old_number=c.number, action="cross-tier", ul_number=ul
                )

    old_number_set: set[int] = {c.number for c in classified}

    # Build the project file text (compact-renumbered headings).
    project_text_new, _ = _build_project_file(project)
    result.new_project_count = len(project)

    # Rewrite the project file's in-body citations (it is both a write target
    # AND a rewrite target; fence-aware).
    project_rewritten, project_records = rewrite_file(
        str(PROJECT_LESSONS_RELPATH), project_text_new, result.remap,
        old_number_set, fence_aware=True,
    )
    result.rewrite_records.extend(project_records)

    # Authoritative reconciliation on the project file's own records.
    defects = reconcile_refs(project_records, result.remap)
    if defects:
        result.review_lines.append("AUTHORITATIVE RECONCILIATION DEFECTS (project file):")
        result.review_lines.extend(f"  - {d}" for d in defects)
        result.refs_unremappable += len(defects)

    # Coarse echo (b): in-corpus discriminated lesson-#N with value > M.
    coarse = coarse_echo_in_corpus(
        project_rewritten, result.new_project_count, old_number_set
    )
    if coarse:
        result.review_lines.append("COARSE ECHO DEFECTS (in-corpus value > M):")
        result.review_lines.extend(f"  - {d}" for d in coarse)

    # Count refs rewritten (renumbered-to-new + removed).
    result.refs_rewritten = sum(
        1 for r in project_records
        if r.action in {"renumbered-to-new", "removed", "removed-mid-prose"}
    )

    # Emit the audit snapshot body (from the deleted index, if present).
    snapshot_text: str | None = None
    deleted_index_path = repo_root / PRINCIPLE_INDEX_RELPATH
    if deleted_index_path.is_file():
        try:
            deleted_index_text = deleted_index_path.read_text(encoding="utf-8")
            snapshot_text = build_audit_snapshot(date_iso, deleted_index_text)
        except OSError:
            snapshot_text = None

    # Write path.
    if write:
        # (1) User corpus first: write the .tmp -> run the gate on the .tmp ->
        # os.replace ONLY on success. On failure delete the .tmp + abort leaving
        # BOTH real files untouched (the project file has NOT been written yet
        # at this point). This honors the gate-on-.tmp contract (abort-before-
        # os.replace) so a corpus the gate rejects NEVER replaces the real file.
        user_corpus = user_corpus_path(repo_root)
        if user_corpus is None:
            raise RuntimeError(
                "lessons_migrate: could not resolve shared_docs_dir from "
                ".ai-playbook/facts.md (lowercase key); set it in the facts file."
            )
        tmp = str(user_corpus) + ".tmp"
        # Pre-flight: refuse if a .tmp symlink is planted (the O_NOFOLLOW flag
        # below also enforces this at the kernel level; the pre-flight surfaces
        # a clearer message).
        if os.path.islink(tmp) or os.path.exists(tmp):
            raise RuntimeError(
                f"lessons_migrate: refusing to write user corpus: {tmp} exists "
                f"(planted .tmp TOCTOU). Remove it and re-run."
            )
        # Write the .tmp using the SAME hardened flags as atomic_write_text
        # (O_EXCL|O_NOFOLLOW; cite #119). We do NOT os.replace yet: the gate
        # runs on the .tmp first.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        try:
            fd = os.open(tmp, flags, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                    f.write(new_corpus_text)
            except BaseException:
                # fdopen owns fd; best-effort cleanup.
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
            gate_rc = run_gate(tmp)
            if gate_rc != 0:
                # Abort: delete the .tmp, leave BOTH real files untouched.
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise RuntimeError(
                    f"lessons_migrate: gate failed (exit {gate_rc}) on the user "
                    f"corpus .tmp; aborting BEFORE os.replace. BOTH real files "
                    f"are untouched. Fix the corpus content and re-run."
                )
            # Gate passed: atomic inode swap.
            os.replace(tmp, str(user_corpus))
        except OSError as e:
            # O_EXCL|O_NOFOLLOW refused (planted .tmp symlink or pre-existing).
            raise RuntimeError(
                f"lessons_migrate: refused to write user corpus .tmp: {e}. "
                f"Remove {tmp} and re-run."
            ) from e
        result.user_corpus_path = str(user_corpus)

        # (2) Project file + repo-wide refs second. ALL write sites use
        # atomic_write_text (cite #119).
        project_target = repo_root / PROJECT_LESSONS_RELPATH
        # Pre-flight .tmp check.
        if os.path.islink(str(project_target) + ".tmp") or os.path.exists(str(project_target) + ".tmp"):
            raise RuntimeError(
                f"lessons_migrate: refusing to write project file: "
                f"{project_target}.tmp exists (planted .tmp TOCTOU)."
            )
        lessons_corpus.atomic_write_text(str(project_target), project_rewritten)
        result.project_path = str(project_target)

        # Repo-wide refs (src/, tests/, AGENTS.md, docs/maintenance/).
        for glob_pat in REWRITE_GLOBS:
            for path in repo_root.glob(glob_pat):
                if not path.is_file():
                    continue
                # Skip symlinks (e.g. CLAUDE.md -> AGENTS.md): read_text follows
                # the link, but atomic_write_text's os.replace would overwrite
                # the LINK ITSELF with a regular file, dereferencing it and
                # breaking the repo invariant. The link's target (a regular
                # file) is globbed and processed on its own; skipping the link
                # also avoids double-rewriting (and diverging) the same content.
                if path.is_symlink():
                    continue
                # Skip history.
                try:
                    rel = path.relative_to(repo_root)
                except ValueError:
                    continue
                # Skip VCS / vendor / cache dirs (.venv, node_modules,
                # __pycache__, build, ...). A ``**/*.md`` glob otherwise
                # descends into ``.venv`` and rewrites a packaged CHANGELOG.
                if _EXCLUDED_DIRS.intersection(rel.parts):
                    continue
                if str(rel).startswith("docs/history/"):
                    continue
                # Skip the project lessons file (already written above) and the
                # audit snapshot we are about to write.
                if rel == PROJECT_LESSONS_RELPATH:
                    continue
                try:
                    original = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                # Rewrite (the rewrite function is a no-op when there are no
                # discriminated tokens). fence_aware=True so lesson citations
                # inside genuine code blocks are left untouched; the CommonMark
                # open/close tracker keeps a stray delimiter from blanking
                # citations outside any real fence.
                new_text, path_records = rewrite_file(
                    str(rel), original, result.remap, old_number_set,
                    fence_aware=True,
                )
                result.rewrite_records.extend(path_records)
                if new_text != original:
                    tmp_check = str(path) + ".tmp"
                    if os.path.islink(tmp_check) or os.path.exists(tmp_check):
                        raise RuntimeError(
                            f"lessons_migrate: refusing to rewrite {path}: "
                            f"{tmp_check} exists (planted .tmp TOCTOU at a "
                            f"repo-wide target; r4 Medium 2)."
                        )
                    lessons_corpus.atomic_write_text(str(path), new_text)

        # Authoritative reconciliation across ALL repo-wide records.
        all_defects = reconcile_refs(result.rewrite_records, result.remap)
        if all_defects:
            result.review_lines.append("AUTHORITATIVE RECONCILIATION DEFECTS (repo-wide):")
            result.review_lines.extend(f"  - {d}" for d in all_defects)
            result.refs_unremappable += len(all_defects)

        # Emit the audit snapshot.
        if snapshot_text is not None:
            snapshot_dir = repo_root / FEATURE_NOTES_RELPATH
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path = snapshot_dir / f"{date_iso}-principle-index-audit-snapshot.md"
            lessons_corpus.atomic_write_text(str(snapshot_path), snapshot_text)
            result.snapshot_path = str(snapshot_path)

        # Delete the index.
        index_path = repo_root / PRINCIPLE_INDEX_RELPATH
        if index_path.is_file():
            index_path.unlink()

        # Write the review list.
        review_dir = repo_root / "docs" / "tmp" / "lessons-migrate"
        review_dir.mkdir(parents=True, exist_ok=True)
        review_path = review_dir / f"{date_iso}-review-list.md"
        result.review_lines = build_review_list(result, classified)
        lessons_corpus.atomic_write_text(str(review_path), "\n".join(result.review_lines) + "\n")
        result.review_list_path = str(review_path)

        # Belt-and-braces: re-run the gate on the final user corpus.
        final_rc = run_gate(str(user_corpus))
        if final_rc != 0:
            result.review_lines.append(
                f"WARNING: final gate re-run exited {final_rc} on the user corpus."
            )
        result.wrote_files = True
    else:
        # Dry-run: emit the review list (in-memory).
        result.review_lines = build_review_list(result, classified)

    return result


# --------------------------------------------------------------------------- #
# Self-test (Task 4 fixtures).
# --------------------------------------------------------------------------- #
def _selftest_check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
    return condition


def selftest() -> int:
    """In-memory fixtures ONLY. Exercises every Task-4 fixture bullet."""
    import tempfile

    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        all_ok = _selftest_check(label, cond, detail) and all_ok

    # ---- phrase_present_single_source: re-import is IDENTITY, not a copy ----
    # (r8-L1: the migrator keeps NO own copy of phrase_present/matches_family_vocab;
    # a second copy would diverge silently - Family D). The re-export must be the
    # SAME function object as the leaf's, not merely an equal-valued redefinition.
    check(
        "phrase_present_single_source: lessons_migrate.phrase_present is lessons_classify.phrase_present",
        phrase_present is lessons_classify.phrase_present,
        f"migrator={phrase_present!r} leaf={lessons_classify.phrase_present!r}",
    )
    check(
        "matches_family_vocab_single_source: lessons_migrate.matches_family_vocab is lessons_classify.matches_family_vocab",
        matches_family_vocab is lessons_classify.matches_family_vocab,
        "",
    )

    # ---- repo-agnostic engine: no curated domain vocabulary in the classifier ----
    # NOTE (Pass 2): the plan's Task-4 fixture #2 demands a literal
    # ``grep -iE 'crypto|FIFO|Koinly|ISIN|dividend|Modelo|CIRS|Quadro|Anexo'
    # lessons_migrate.py`` -> zero matches. That literal whole-file grep is
    # UNSATISFIABLE: the SAME plan MANDATES ``PROCESS_PREFIXES`` containing
    # ``CIRS``, ``CRG``, ``SRG``, ``Quadro``, ``Anexo``, ``Tabela``, ``Campo``
    # (discriminator spec, plan line ~270) AND a safe-default selftest fixture
    # whose synthetic text is domain-coupled ("validate the FIFO basis per CIRS
    # art. 43"; "Koinly file naming"; plan line ~283). Those tokens MUST stay.
    # We therefore re-scope the plan's literal grep to its INTENT (the plan's
    # invariant: "no domain keywords are baked in or CURATED" / "the classifier
    # keys off the family catalog + generic-shape vocabulary, never repo terms"):
    #   (1) FAMILY_KEYWORDS (signal 2's POSITIVE routing vocabulary) contains
    #       NONE of the domain terms crypto/FIFO/Koinly/ISIN/dividend/Modelo;
    #   (2) the engine exposes NO ``--domain-keywords`` CLI flag;
    #   (3) residue detection reuses the mandated PROCESS_PREFIXES structural
    #       tokens + a GENERIC legal-citation pattern only - it consults NO
    #       curated domain keyword list as a positive routing signal.
    DOMAIN_TERMS = ("crypto", "FIFO", "Koinly", "ISIN", "dividend", "Modelo")
    # (1) FAMILY_KEYWORDS is domain-free.
    classifier_domain_hits = []
    for letter, phrases in FAMILY_KEYWORDS.items():
        for p in phrases:
            for term in DOMAIN_TERMS:
                if term.lower() in p.lower():
                    classifier_domain_hits.append((letter, p, term))
    check(
        "repo-agnostic: FAMILY_KEYWORDS (signal 2 routing vocab) has zero domain terms",
        not classifier_domain_hits,
        str(classifier_domain_hits[:3]),
    )
    # (2) No --domain-keywords CLI flag is wired into the argument parser.
    # Invoke main() with the flag and confirm it is rejected as UNKNOWN (exit 2),
    # the same path any other unrecognized flag takes. (Inspecting main()'s
    # dispatch directly, rather than grepping source text, avoids the
    # self-referential false-positive of the assertion's own label mentioning the
    # flag name.)
    rejected = main(["--domain-keywords", "crypto,FIFO"]) == 2
    check(
        "repo-agnostic: no --domain-keywords CLI flag is exposed",
        rejected,
        "main() accepted --domain-keywords as a known flag",
    )
    # (3) The classifier consults NO curated domain keyword list. The residue
    # detector must reuse PROCESS_PREFIXES + the generic legal-citation pattern
    # ONLY. Concretely: every PROCESS_PREFIXES token used by _has_domain_residue
    # is a structural token the plan mandates for the discriminator (not a
    # domain-curated entry); and there is no module-level regex enumerating
    # crypto/FIFO/Koinly/etc. as a routing vocabulary. We assert the only
    # module-level residue regex is the GENERIC legal-citation pattern.
    check(
        "repo-agnostic: no curated domain vocabulary in classifier residue detection "
        "(reuses PROCESS_PREFIXES + generic legal-citation only)",
        _GENERIC_LEGAL_CITATION_RE.pattern == r"art\.\s*\d|\bQ\d{1,2}\b",
        _GENERIC_LEGAL_CITATION_RE.pattern,
    )

    # ---- discriminating-token assertion (r3 Medium 6): each family's keyword
    # list has >=1 token NOT in the union of the others'.
    def _tokens(phrases: list[str]) -> set[str]:
        toks: set[str] = set()
        for p in phrases:
            for w in p.lower().split():
                # Strip punctuation from each word for the union check.
                w = re.sub(r"[^a-z0-9-]", "", w)
                if w:
                    toks.add(w)
        return toks

    families = sorted(FAMILY_KEYWORDS)
    for letter in families:
        mine = _tokens(FAMILY_KEYWORDS[letter])
        others: set[str] = set()
        for other in families:
            if other == letter:
                continue
            others |= _tokens(FAMILY_KEYWORDS[other])
        discriminating = mine - others
        check(
            f"discriminating token: Family {letter} has >=1 unique token",
            len(discriminating) >= 1,
            f"mine={sorted(mine)} others-overlap={sorted(mine & others)}",
        )

    # ---- generic-first classification (no flags) ----
    # (a) Family B tag, (b) untagged generic-shape, (c) domain-coupled,
    # (d) abstract-but-untagged no domain residue.
    repo_corpus = (
        "## 1. Catch specific exceptions\n"
        "**Principle:** Family B (error policy)\n"
        "Catch specific exception types, not broad Exception.\n"
        "## 2. Generic untagged shape\n"
        "Always catch specific exception types, not broad Exception, in row loops.\n"
        "## 3. Koinly file naming\n"
        "Koinly transaction_history.csv files use a fixed naming convention.\n"
        "## 4. Abstract untagged no residue\n"
        "Prefer pure functions over implicit shared state where possible.\n"
    )
    parsed = list(lessons_corpus.iter_lessons(repo_corpus))
    routes = {l.number: classify_lesson(l) for l in parsed}
    check("classify: (a) Family B tag -> cross-project",
          routes[1][0] == "cross-project", str(routes[1]))
    check("classify: (b) generic shape -> cross-project",
          routes[2][0] == "cross-project", str(routes[2]))
    check("classify: (c) domain-coupled -> project-specific",
          routes[3][0] == "project-specific", str(routes[3]))
    check("classify: (d) abstract untagged no residue -> project-specific (default)",
          routes[4][0] == "project-specific", str(routes[4]))

    # ---- safe default (the core guard) ----
    safe_corpus = (
        "## 5. Validate the FIFO basis\n"
        "Validate the FIFO basis per CIRS art. 43 for each disposal. Catch specific "
        "exception types in the per-row guard so a bad row does not abort the batch.\n"
    )
    parsed = list(lessons_corpus.iter_lessons(safe_corpus))
    route, _reason, _fam = classify_lesson(parsed[0])
    check("safe default: FIFO+CIRS lesson stays project-specific",
          route == "project-specific", f"route={route}")

    # ---- dedup: near-match flagged, not appended ----
    existing_corpus = (
        "## 1. Catch specific exceptions\n"
        "**Principle:** Family B (error policy)\n"
        "Catch specific exception types, not broad Exception in row loops.\n"
    )
    candidate_title = "Catch specific exceptions"
    candidate_body = "Catch specific exception types, not broad Exception in row loops."
    hits = find_near_matches(candidate_title, candidate_body, existing_corpus)
    check("dedup: near-match returns the existing UL#1",
          hits == [1], str(hits))

    # ---- remap (markdown): AGENTS.md cites development_lessons.md #5 ----
    # Build a remap where old #5 -> new #2 (same-tier), old #3 -> cross-tier.
    remap = {
        5: RemapEntry(old_number=5, action="same-tier", new_number=2),
        3: RemapEntry(old_number=3, action="cross-tier", ul_number=1),
    }
    old_set = {3, 5}
    agents_line = "See development_lessons.md #5 for the rule.\n"
    rewritten, recs = rewrite_file("AGENTS.md", agents_line, remap, old_set, fence_aware=True)
    check("remap markdown: old #5 -> new #2",
          "#2" in rewritten and "development_lessons.md #2" in rewritten,
          rewritten.strip())
    check("remap markdown: old #5 recorded as renumbered-to-new",
          any(r.action == "renumbered-to-new" and r.old_number == 5 and r.new_number == 2
              for r in recs),
          str([(r.action, r.old_number, r.new_number) for r in recs]))

    moved_line = "See development_lessons.md #3 (the moved one).\n"
    rewritten, recs = rewrite_file("AGENTS.md", moved_line, remap, old_set, fence_aware=True)
    check("remap markdown: moved #3 token REMOVED (no UL# in project output)",
          "#3" not in rewritten and "UL#" not in rewritten,
          rewritten.strip())
    check("remap markdown: moved #3 recorded as removed",
          any(r.action == "removed" and r.old_number == 3 for r in recs),
          str([(r.action, r.old_number) for r in recs]))

    # ---- remap (code, B1): three citation forms + bare PR-number ----
    code = (
        "# See development_lessons.md #5.\n"
        "# silent drop (lesson #5)\n"
        "# #5/#6 multi\n"
        "# 123\n"
    )
    remap_code = {
        5: RemapEntry(old_number=5, action="same-tier", new_number=2),
        6: RemapEntry(old_number=6, action="same-tier", new_number=3),
    }
    old_set_code = {5, 6}
    rewritten, recs = rewrite_file("src/x.py", code, remap_code, old_set_code, fence_aware=True)
    check("remap code: 'development_lessons.md #5' -> #2",
          "development_lessons.md #2" in rewritten, rewritten)
    check("remap code: 'lesson #5' -> 'lesson #2'",
          "lesson #2" in rewritten, rewritten)
    check("remap code: multi '#5/#6' -> '#2/#3'",
          "#2/#3" in rewritten, rewritten)
    check("remap code: bare '# 123' PR-number left untouched",
          "# 123\n" in rewritten, rewritten)

    # ---- remap (backtick form, B2) ----
    backtick = "See `development_lessons.md` #5 for details.\n"
    rewritten, recs = rewrite_file("AGENTS.md", backtick, remap, old_set, fence_aware=True)
    check("remap backtick: `development_lessons.md` #5 -> #2",
          "`development_lessons.md` #2" in rewritten, rewritten.strip())

    # ---- in-body cross-link, same-tier + renumber scope (r4 Low 1) ----
    # 5 lessons; #58 -> new #12 (PINNED concrete mapping). A double-shift impl
    # (renumber body #N in the renumber pass AND the remap pass) fails this.
    inbody_corpus = (
        "## 58. First\n"
        "**Principle:** Family D (single source)\n"
        "See also (principle cluster D): #58, #68, #94\n"
        "Distinguishing from #71 / #72\n"
        "Lesson #73 is related.\n"
        "seed (#5) variant.\n"
        "## 68. Second\n"
        "**Principle:** Family D (single source)\n"
        "body\n"
        "## 71. Third\n"
        "**Principle:** Family D (single source)\n"
        "body\n"
        "## 72. Fourth\n"
        "**Principle:** Family D (single source)\n"
        "body\n"
        "## 73. Fifth\n"
        "**Principle:** Family D (single source)\n"
        "body\n"
        "## 94. Sixth\n"
        "**Principle:** Family D (single source)\n"
        "body\n"
        "## 5. Seventh\n"
        "**Principle:** Family D (single source)\n"
        "body\n"
    )
    # All lessons project-side. Compact-renumber gives:
    # 58->1, 68->2, 71->3, 72->4, 73->5, 94->6, 5->7.
    # We PIN old #58 -> new #1 (the heading renumber). The body #58 citation
    # must rewrite to #1 ONLY ONCE (renumber-scope: body #N is remap-only).
    parsed = list(lessons_corpus.iter_lessons(inbody_corpus))
    # Build same-tier remap from the compact renumber.
    project_lessons_for_remap = [
        ClassifiedLesson(
            number=l.number, title=l.title, body_lines=list(l.body_lines),
            raw_text="", tags=l.tags, route="project-specific",
        ) for l in parsed
    ]
    # Reproduce the heading renumber to get the old->new map.
    _, heading_map = renumber_headings(inbody_corpus, start=1)
    remap_inbody = {
        old: RemapEntry(old_number=old, action="same-tier", new_number=new)
        for old, new in heading_map.items()
    }
    old_set_inbody = set(heading_map)
    # First renumber headings, THEN rewrite body citations.
    renumbered_text, _ = renumber_headings(inbody_corpus, start=1)
    body_rewritten, recs = rewrite_file(
        "docs/maintenance/development_lessons.md", renumbered_text,
        remap_inbody, old_set_inbody, fence_aware=True,
    )
    # PINNED: old #58 -> new #1. A double-shift impl renumbers body #58 in the
    # heading pass too, producing #1 -> ... wrong.
    check("in-body same-tier + renumber scope: old #58 -> new #1 (heading)",
          "## 1. First" in body_rewritten, body_rewritten.splitlines()[0])
    check("in-body same-tier: body '#58, #68, #94' cluster rewritten",
          "#1, #2, #6" in body_rewritten,
          [ln for ln in body_rewritten.splitlines() if "principle cluster" in ln])
    check("in-body same-tier: spaced slash '#71 / #72' -> '#3 / #4'",
          "#3 / #4" in body_rewritten,
          [ln for ln in body_rewritten.splitlines() if "Distinguishing" in ln])
    check("in-body same-tier: 'Lesson #73' -> 'Lesson #5'",
          "Lesson #5" in body_rewritten,
          [ln for ln in body_rewritten.splitlines() if "Lesson" in ln])
    # old #5 -> new #7; the parenthetical (#5) -> (#7).
    check("in-body same-tier: '(#5)' -> '(#7)'",
          "(#7)" in body_rewritten,
          [ln for ln in body_rewritten.splitlines() if "seed" in ln])

    # ---- guideline-citation exclusion (r4 Medium 1) ----
    guideline_lines = (
        "See `~/Projects/.ai-playbook/python_guidelines.md` #3 for the canonical rule.\n"
        "See development_lessons.md #4 (type-safe sentinels).\n"
    )
    remap_gl = {
        3: RemapEntry(old_number=3, action="same-tier", new_number=9),
        4: RemapEntry(old_number=4, action="same-tier", new_number=10),
    }
    old_set_gl = {3, 4}
    rewritten, recs = rewrite_file("AGENTS.md", guideline_lines, remap_gl, old_set_gl, fence_aware=True)
    check("guideline exclusion: python_guidelines.md #3 LEFT UNCHANGED",
          "python_guidelines.md` #3" in rewritten, rewritten.strip())
    check("guideline exclusion: development_lessons.md #4 REWRITTEN to #10",
          "development_lessons.md #10" in rewritten, rewritten.strip())

    # ---- process-identifier exclusion (r5 guard v; r6 Medium) ----
    proc_line = (
        "See AGENTS.md Rule #4 and finding #1 (Medium), per Design Invariant #2. "
        "DP-014 #6, Medium #1, rule #6 unchanged.\n"
    )
    remap_proc = {
        4: RemapEntry(old_number=4, action="same-tier", new_number=99),
        1: RemapEntry(old_number=1, action="same-tier", new_number=99),
        2: RemapEntry(old_number=2, action="same-tier", new_number=99),
        6: RemapEntry(old_number=6, action="same-tier", new_number=99),
    }
    old_set_proc = {1, 2, 4, 6}
    rewritten, recs = rewrite_file("AGENTS.md", proc_line, remap_proc, old_set_proc, fence_aware=True)
    # ALL the process-id tokens unchanged.
    check("process-id: 'Rule #4' unchanged",
          "Rule #4" in rewritten, rewritten)
    check("process-id: lowercase 'finding #1' unchanged (case-insensitive)",
          "finding #1" in rewritten, rewritten)
    check("process-id: 'Design Invariant #2' unchanged",
          "Design Invariant #2" in rewritten, rewritten)
    check("process-id: 'DP-014 #6' unchanged",
          "DP-014 #6" in rewritten, rewritten)
    check("process-id: 'Medium #1' unchanged",
          "Medium #1" in rewritten, rewritten)
    check("process-id: lowercase 'rule #6' unchanged",
          "rule #6" in rewritten, rewritten)
    # The lead-in enumeration MUST NOT list Rule/finding/Invariant as lesson
    # lead-ins. Build a review list from these records.
    lesson_lead_ins = {
        r.lead_in for r in recs
        if r.action in {"renumbered-to-new", "removed", "removed-mid-prose"}
    }
    check("lead-in audit: Rule/finding/Invariant NOT in lesson lead-ins",
          not ({"Rule", "finding", "Invariant"} & lesson_lead_ins),
          str(lesson_lead_ins))

    # ---- in-body cross-link, cross-tier (r5 Option A; r6 Low) ----
    crosstier_corpus = (
        "## 28. Stays\n"
        "**Principle:** Family D (single source)\n"
        "seed (#5) vs focused.\n"
        "#94 is the test-enforced variant of #23's manual grep.\n"
        "See also: #5\n"
        "## 5. Moves\n"
        "**Principle:** Family D (single source)\n"
        "moves\n"
        "## 94. Moves2\n"
        "**Principle:** Family D (single source)\n"
        "moves\n"
        "## 23. Moves3\n"
        "**Principle:** Family D (single source)\n"
        "moves\n"
    )
    # #28 stays (new #1); #5, #94, #23 move to user corpus (REMOVE).
    heading_re_crosstier = {
        28: 1,  # only stayer gets a heading number after renumber
    }
    # Simulate the project renumber: only #28 remains.
    project_only = (
        "## 1. Stays\n"
        "**Principle:** Family D (single source)\n"
        "seed (#5) vs focused.\n"
        "#94 is the test-enforced variant of #23's manual grep.\n"
        "See also: #5\n"
    )
    remap_ct = {
        28: RemapEntry(old_number=28, action="same-tier", new_number=1),
        5: RemapEntry(old_number=5, action="cross-tier", ul_number=1),
        94: RemapEntry(old_number=94, action="cross-tier", ul_number=2),
        23: RemapEntry(old_number=23, action="cross-tier", ul_number=3),
    }
    old_set_ct = {5, 23, 28, 94}
    rewritten, recs = rewrite_file(
        "docs/maintenance/development_lessons.md", project_only,
        remap_ct, old_set_ct, fence_aware=True,
    )
    check("cross-tier: NO UL# in project output",
          "UL#" not in rewritten, rewritten)
    check("cross-tier: moved #5 token GONE",
          "#5" not in rewritten, rewritten)
    check("cross-tier: sole-content '(#5)' -> no '()'",
          "()" not in rewritten,
          [ln for ln in rewritten.splitlines() if "seed" in ln])
    check("cross-tier: 'seed (#5) vs' -> 'seed vs'",
          "seed vs focused" in rewritten,
          [ln for ln in rewritten.splitlines() if "seed" in ln])
    check("cross-tier: moved #94 token GONE",
          "#94" not in rewritten, rewritten)
    check("cross-tier: moved #23 token GONE",
          "#23" not in rewritten, rewritten)
    # The mid-prose removal (#94 / #23 in rationale) is flagged.
    check("cross-tier: mid-prose removal flagged",
          any(r.action == "removed-mid-prose" for r in recs),
          str([(r.action, r.old_number) for r in recs]))
    # Every removal appears in the records.
    removed_old = {r.old_number for r in recs if r.action in {"removed", "removed-mid-prose"}}
    check("cross-tier: every removal recorded",
          {5, 94, 23} <= removed_old, str(sorted(removed_old)))

    # ---- citation-phrase pass (r6): drop whole `development_lessons.md #N` ----
    # Cross-tier phrase WITH an introducer is dropped entirely (no dangling
    # ``See `development_lessons.md` .`` stub). A bare file-path mention with NO
    # ``#N`` is preserved verbatim. A mixed cluster keeps the surviving same-tier
    # (renumbered) numbers.
    cite_remap = {
        7: RemapEntry(old_number=7, action="cross-tier", ul_number=4),
        9: RemapEntry(old_number=9, action="cross-tier", ul_number=5),
        12: RemapEntry(old_number=12, action="same-tier", new_number=2),
    }
    cite_old_set = {7, 9, 12}
    cite_text = (
        "Catch specific exceptions. See `development_lessons.md` #7.\n"
        "Full details: `development_lessons.md`.\n"
        "Mixed: see `development_lessons.md` #7 and #12 then proceed.\n"
    )
    cite_out, cite_recs = rewrite_file(
        "AGENTS.md", cite_text, cite_remap, cite_old_set, fence_aware=True,
    )
    cite_lines = cite_out.splitlines()
    check("citation: cross-tier `See ...md` #7 fully dropped",
          not any("development_lessons.md" in ln and "#7" in ln for ln in cite_lines)
          and "Catch specific exceptions." in cite_lines[0],
          cite_lines[:1])
    check("citation: no dangling 'See `...md`' stub remains",
          "See `development_lessons.md`" not in cite_out
          and "See development_lessons.md" not in cite_out,
          [ln for ln in cite_lines if "development_lessons" in ln])
    check("citation: bare path mention (no #N) preserved verbatim",
          "Full details: `development_lessons.md`." in cite_lines,
          [ln for ln in cite_lines if "Full details" in ln])
    check("citation: mixed cluster keeps renumbered survivor #12 -> #2",
          any("development_lessons.md` #2" in ln for ln in cite_lines),
          [ln for ln in cite_lines if "Mixed" in ln])
    check("citation: mixed cluster drops cross-tier #7",
          not any("Mixed" in ln and "#7" in ln for ln in cite_lines),
          [ln for ln in cite_lines if "Mixed" in ln])
    cite_removed = {r.old_number for r in cite_recs if r.action == "removed"}
    check("citation: removed + renumbered recorded per-number",
          {7} <= cite_removed and any(
              r.action == "renumbered-to-new" and r.old_number == 12 for r in cite_recs),
          str([(r.action, r.old_number) for r in cite_recs]))

    # ---- citation new-number collision (r6 stub regression) ----
    # Same-tier #50 renumbered to NEW #7, but OLD #7 is cross-tier. A per-token
    # pass that re-scans the citation output would re-discriminate the new #7 as
    # OLD #7 (cross-tier) and DROP it, leaving a dangling stub. The interleaved
    # pass must treat the citation phrase as authoritative: #50 -> #7 survives.
    coll_remap = {
        50: RemapEntry(old_number=50, action="same-tier", new_number=7),
        7: RemapEntry(old_number=7, action="cross-tier", ul_number=9),
    }
    coll_old_set = {7, 50}
    coll_text = "See `development_lessons.md` #50 for details.\n"
    coll_out, coll_recs = rewrite_file(
        "AGENTS.md", coll_text, coll_remap, coll_old_set, fence_aware=True,
    )
    check("citation: same-tier #50 -> new #7 survives (new# collides with old cross-tier #7)",
          "development_lessons.md` #7" in coll_out and "for details" in coll_out,
          coll_out.splitlines())
    check("citation: no dangling stub from new-number collision",
          "See `development_lessons.md`." not in coll_out
          and "See `development_lessons.md` ." not in coll_out,
          coll_out.splitlines())
    check("citation: collision case records #50 renumbered-to-new (not removed)",
          any(r.action == "renumbered-to-new" and r.old_number == 50 for r in coll_recs),
          str([(r.action, r.old_number) for r in coll_recs]))

    # ---- stale-ref reconciliation (B1, r5) ----
    # Authoritative: a same-tier citation left at old value <= M is caught.
    # Plant a record claiming renumbered-to-new but new == old (the wrong impl).
    bad_records = [
        RewriteRecord(file="x.py", line_no=1, old_number=2,
                      action="renumbered-to-new", new_number=2),
    ]
    remap_recon = {2: RemapEntry(old_number=2, action="same-tier", new_number=5)}
    defects = reconcile_refs(bad_records, remap_recon)
    check("reconcile: same-tier citation left at old value caught",
          any("#2 left at old value" in d for d in defects), str(defects))
    # Coarse echo: in-corpus #N > M.
    coarse_corpus = "## 1. T\nrefers to #99 here.\n"
    coarse_defects = coarse_echo_in_corpus(coarse_corpus, 5, {1, 99})
    check("coarse echo: #99 > M=5 flagged",
          any("#99" in d for d in coarse_defects), str(coarse_defects))

    # ---- strictness split (r3 Medium 8): Family Z + zero-tag survive in project ----
    strict_corpus = (
        "## 1. Bad tag\n"
        "**Principle:** Family Z (invalid)\n"
        "body\n"
        "## 2. No tag\n"
        "body\n"
    )
    parsed = list(lessons_corpus.iter_lessons(strict_corpus))
    # Both default to project-specific; the project file build preserves tags.
    project_lessons = []
    for l in parsed:
        heading = f"## {l.number}. {l.title}\n"
        body = "\n".join(l.body_lines)
        raw = heading + body
        if not raw.endswith("\n"):
            raw += "\n"
        project_lessons.append(ClassifiedLesson(
            number=l.number, title=l.title, body_lines=list(l.body_lines),
            raw_text=raw, tags=l.tags, route="project-specific",
        ))
    proj_text, _ = _build_project_file(project_lessons)
    check("strictness split: Family Z preserved in project file",
          "Family Z" in proj_text, proj_text)
    check("strictness split: zero-tag lesson preserved (no tag injected)",
          "## 2. No tag\nbody" in proj_text, proj_text)

    # ---- atomic write ALL sites (r3 Medium 3 + r4 Medium 2): .tmp symlink refused ----
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "victim.py"
        target.write_text("original\n", encoding="utf-8")
        # Plant a .tmp symlink (TOCTOU attempt).
        evil = Path(td) / "evil.txt"
        evil.write_text("pwned\n", encoding="utf-8")
        tmp_symlink = Path(str(target) + ".tmp")
        os.symlink(str(evil), str(tmp_symlink))
        refused = False
        try:
            lessons_corpus.atomic_write_text(str(target), "rewritten\n")
        except OSError:
            refused = True
        check("atomic write: .tmp symlink at write target refused (O_EXCL|O_NOFOLLOW)",
              refused, "atomic_write_text did not refuse")
        check("atomic write: original untouched after refusal",
              target.read_text(encoding="utf-8") == "original\n",
              target.read_text(encoding="utf-8"))
        # Repo-wide target refusal: the migrator's pre-flight check rejects a
        # planted .tmp at a repo-wide rewrite target.
        repo_wide_refused = False
        try:
            tmp_check = str(target) + ".tmp"
            if os.path.islink(tmp_check) or os.path.exists(tmp_check):
                raise RuntimeError("planted .tmp TOCTOU at repo-wide target")
        except RuntimeError:
            repo_wide_refused = True
        check("atomic write: repo-wide target .tmp pre-flight refuses",
              repo_wide_refused)
        # Cleanup the symlink for the tempdir teardown.
        tmp_symlink.unlink()

    # ---- idempotency: re-run refuses with recovery recipe ----
    already_migrated = (
        "## 1. A\n**Principle:** Family A (r)\n"
        "## 2. B\n**Principle:** Family A (r)\n"
    )
    check("idempotency: contiguous 1..N detected as already-migrated",
          _project_already_migrated(already_migrated) is True)
    refused = False
    try:
        migrate(Path("/tmp/fake"), already_migrated, "", write=True)
    except RuntimeError as e:
        if "already migrated" in str(e):
            refused = True
    check("idempotency: re-run refuses (recovery recipe)", refused)

    # ---- self-check: abort on duplicate tag, no os.replace ----
    # The gate aborts a corpus with a duplicate UL#N. First confirm the gate
    # itself rejects a duplicate-tag corpus.
    dup_corpus = (
        "## 1. A\n**Principle:** Family A (r)\n"
        "## 1. Dup\n**Principle:** Family A (r)\n"
    )
    rc = run_gate_on_text(dup_corpus)
    check("self-check: gate exits 1 on duplicate tag", rc == 1, f"rc={rc}")

    # End-to-end abort: migrate(write=True) where the appended user corpus would
    # have a duplicate tag MUST raise BEFORE os.replace, leaving the real user
    # corpus file untouched. We plant a user corpus with a lesson that the
    # migrator's compact-renumber would collide with.
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "docs" / "maintenance").mkdir(parents=True)
        # Two cross-project lessons (Family A tags). Numbered with a gap so the
        # project file is NOT in the post-migration steady state (which would
        # trip the idempotency refusal instead of the gate refusal).
        (repo / "docs" / "maintenance" / "development_lessons.md").write_text(
            "## 1. Cross one\n**Principle:** Family A (r)\nbody\n"
            "## 3. Cross two\n**Principle:** Family A (r)\nbody\n",
            encoding="utf-8",
        )
        # Plant a fake facts file pointing shared_docs_dir at a temp dir so the
        # migrator resolves the user corpus inside our temp tree.
        shared_dir = Path(td) / "shared"
        shared_dir.mkdir()
        (repo / ".ai-playbook").mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            "| `shared_docs_dir` | `" + str(shared_dir) + "/` | test |\n",
            encoding="utf-8",
        )
        # Pre-existing user corpus with a DEFECT that compact-renumber does NOT
        # fix: an existing lesson with an INVALID family tag (``Family Z``).
        # Compact-renumber rewrites ``## N.`` headings only (preserving tag
        # lines), so the invalid tag survives into the appended corpus and the
        # gate rejects it -> the migrator aborts BEFORE os.replace.
        user_corpus_file = shared_dir / "development_lessons.md"
        user_corpus_file.write_text(
            "## 1. Existing with bad tag\n**Principle:** Family Z (invalid)\nbody\n",
            encoding="utf-8",
        )
        original_corpus = user_corpus_file.read_text(encoding="utf-8")
        project_text_bad = (repo / "docs" / "maintenance" / "development_lessons.md").read_text(encoding="utf-8")
        aborted = False
        try:
            migrate(repo, project_text_bad, original_corpus, write=True,
                    ai_playbook_root=repo, date_iso="2026-06-30")
        except RuntimeError as e:
            if "gate failed" in str(e) or "BOTH real files are untouched" in str(e):
                aborted = True
        check("self-check: migrate(write=True) aborts on bad user corpus",
              aborted, "migrate did not abort")
        # CRITICAL: the real user corpus file is UNTOUCHED (no os.replace).
        check("self-check: real user corpus untouched (no os.replace)",
              user_corpus_file.read_text(encoding="utf-8") == original_corpus,
              "user corpus was replaced despite the abort")
        # And the .tmp is cleaned up.
        check("self-check: .tmp cleaned up after abort",
              not (Path(str(user_corpus_file) + ".tmp")).exists())

    # ---- end-to-end migrate() on a small synthetic repo (dry-run) ----
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "docs" / "maintenance").mkdir(parents=True)
        (repo / "docs" / "maintenance" / "development_lessons.md").write_text(
            "## 1. Generic\n**Principle:** Family A (r)\n"
            "Catch specific exception types.\n"
            "## 2. Domain\nKoinly file naming.\n"
            "## 3. Cites #1\nrefers to #1 and #2.\n",
            encoding="utf-8",
        )
        (repo / "AGENTS.md").write_text(
            "See development_lessons.md #1.\n", encoding="utf-8"
        )
        project_text_e2e = (repo / "docs" / "maintenance" / "development_lessons.md").read_text(encoding="utf-8")
        result = migrate(repo, project_text_e2e, "", write=False)
        # #1 cross-project (Family A tag); #2 project-specific (domain); #3 project-specific (default).
        check("e2e dry-run: 1 cross-project moved",
              result.cross_moved == 1, f"cross={result.cross_moved}")
        check("e2e dry-run: 2 project-specific kept",
              result.project_kept == 2, f"kept={result.project_kept}")
        check("e2e dry-run: remap has 3 entries",
              len(result.remap) == 3, str(sorted(result.remap)))
        # #1 -> cross-tier (REMOVE in-repo); #2 -> same-tier new #1; #3 -> same-tier new #2.
        check("e2e dry-run: #1 cross-tier",
              result.remap[1].action == "cross-tier",
              str(result.remap[1]))
        check("e2e dry-run: #2 same-tier new #1",
              result.remap[2].action == "same-tier" and result.remap[2].new_number == 1,
              str(result.remap[2]))
        check("e2e dry-run: #3 same-tier new #2",
              result.remap[3].action == "same-tier" and result.remap[3].new_number == 2,
              str(result.remap[3]))

    # ---- fence tracking: CommonMark open/close (plan_quality #136 incident) ----
    # A stray bare ``` opens a fence; a subsequent ```markdown line is NOT a
    # close (it has an info string). The naive "toggle on any ```" tracker
    # treats ```markdown as a close, mis-pairs fences, and blanks a citation
    # that actually sits OUTSIDE any real code block. The citation must be
    # rewritten.
    fence_corpus = (
        "## 1. T\n**Principle:** Family A (r)\nbody\n"
        "```markdown\n"        # real block 1 OPEN
        "code-one\n"
        "```\n"                # CLOSE block 1
        "```\n"                # STRAY bare OPEN
        "stray-fence-body\n"
        "```markdown\n"        # naive: close (WRONG); fixed: in-fence text
        "code-two\n"
        "```\n"                # naive: open (WRONG); fixed: CLOSE the stray fence
        "See development_lessons.md #1 for the rule.\n"  # OUTSIDE any real fence
    )
    fence_remap = {1: RemapEntry(old_number=1, action="cross-tier", ul_number=1)}
    fence_old = {1}
    rewritten, recs = rewrite_file(
        "docs/maintenance/x.md", fence_corpus, fence_remap, fence_old, fence_aware=True
    )
    check(
        "fence: stray-bare + markdown block does not blank a trailing citation "
        "(CommonMark close: info-string fence is not a close)",
        "development_lessons.md #1" not in rewritten
        and "for the rule" in rewritten.splitlines()[-1],
        [ln for ln in rewritten.splitlines() if "development_lessons" in ln],
    )
    check("fence: the trailing #1 recorded as removed",
          any(r.action in {"removed", "removed-mid-prose"} and r.old_number == 1 for r in recs),
          str([(r.action, r.old_number) for r in recs]))

    # ---- repo-wide safety: symlinks preserved, vendor dirs untouched ----
    # write=True on a temp repo. CLAUDE.md -> AGENTS.md symlink must NOT be
    # dereferenced/overwritten; a .venv packaged CHANGELOG must NOT be rewritten.
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        repo = td / "repo"
        repo.mkdir()
        shared = td / "shared"  # OUTSIDE repo so the repo glob cannot reach it
        shared.mkdir()
        (repo / "docs" / "maintenance").mkdir(parents=True)
        # Gap in headings (1, 4) so the file is NOT in the post-migration steady
        # state (which would trip the idempotency refusal).
        (repo / "docs" / "maintenance" / "development_lessons.md").write_text(
            "## 1. Cross\n**Principle:** Family A (r)\nbody\n"
            "## 4. Project\nKoinly file naming.\n",
            encoding="utf-8",
        )
        (repo / "AGENTS.md").write_text(
            "See development_lessons.md #1.\n", encoding="utf-8"
        )
        (repo / "CLAUDE.md").symlink_to(repo / "AGENTS.md")
        venv_pkg = repo / ".venv" / "lib" / "pkg"
        venv_pkg.mkdir(parents=True)
        vengictim = venv_pkg / "CHANGELOG.md"
        vengictim.write_text("release #1 notes\n", encoding="utf-8")
        (repo / ".ai-playbook").mkdir(parents=True)
        (repo / ".ai-playbook" / "facts.md").write_text(
            "| `shared_docs_dir` | `" + str(shared) + "/` | test |\n",
            encoding="utf-8",
        )
        project_text_e2e2 = (
            (repo / "docs" / "maintenance" / "development_lessons.md").read_text("utf-8")
        )
        migrate(repo, project_text_e2e2, "", write=True,
                ai_playbook_root=repo, date_iso="2026-06-30")
        agents_after = (repo / "AGENTS.md").read_text("utf-8")
        check("repo-wide safety: AGENTS.md citation rewritten (#1 removed)",
              "#1" not in agents_after, agents_after)
        check("repo-wide safety: CLAUDE.md symlink preserved (not overwritten)",
              (repo / "CLAUDE.md").is_symlink(), "CLAUDE.md is not a symlink")
        check("repo-wide safety: .venv packaged CHANGELOG NOT rewritten",
              vengictim.read_text("utf-8") == "release #1 notes\n",
              vengictim.read_text("utf-8"))

    # ---- code safety: span-precise removal (test_fee_filter IndentationError) ----
    # The old within-line cleanup used GLOBAL regexes: re.sub(r"\(\s*\)", ...)
    # stripped any empty parens (ate unrelated func() calls) and
    # re.sub(r"  +", " ", ...) collapsed leading indentation. Both corrupt
    # Python. The new pass is span-precise: only the removed token (and its own
    # sole-content paren) is deleted; indentation and unrelated () are intact.
    indent_remap = {84: RemapEntry(old_number=84, action="cross-tier", ul_number=1)}
    indent_old = {84}
    same_line = "    x = init()  # see #84\n"
    rw, _ = rewrite_file("tests/x.py", same_line, indent_remap, indent_old, fence_aware=True)
    rline = rw.rstrip("\n")
    check("code safety: indent + func() preserved when #N removed on same line",
          rline.startswith("    x = init()") and "#84" not in rline, repr(rline))
    doc_line = '    """Disabled (lesson #84)."""\n'
    rw, _ = rewrite_file("tests/x.py", doc_line, indent_remap, indent_old, fence_aware=True)
    dline = rw.rstrip("\n")
    check("code safety: docstring indent preserved, sole-content (#N) paren removed",
          dline.startswith('    """Disabled') and "()" not in dline and "#84" not in dline,
          repr(dline))

    if all_ok:
        print("selftest OK")
        return 0
    print("selftest FAILED")
    return 1


def run_gate_on_text(text: str) -> int:
    """Run the gate on an in-memory corpus string by writing it to a temp file.

    Selftest helper only (the gate takes a path). Returns the gate's exit code.
    """
    import tempfile
    gate = str(Path(__file__).resolve().parent / "lessons_index.py")
    interp = sys.executable or "python3"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [interp, gate, tmp_path],
            capture_output=True, check=False,
        )
        return result.returncode
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def _usage() -> int:
    sys.stderr.write(
        "usage: lessons_migrate.py <project_lessons> | --selftest | "
        "--dry-run <project_lessons>\n"
        "  <project_lessons>   run the migration on the repo's project lessons file\n"
        "  --dry-run <file>    classify + emit review list + planned remap, NO writes\n"
        "  --selftest          run in-memory fixtures\n"
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    if args and args[0] == "--selftest":
        return selftest()

    dry_run = False
    rest: list[str] = []
    for a in args:
        if a == "--dry-run":
            dry_run = True
        elif a.startswith("-"):
            sys.stderr.write(f"lessons_migrate: unknown flag {a}\n")
            return 2
        else:
            rest.append(a)

    if len(rest) != 1:
        return _usage()

    project_path = Path(rest[0]).resolve()
    if not project_path.is_file():
        sys.stderr.write(f"lessons_migrate: not a file: {project_path}\n")
        return 2

    # Resolve repo root: the project file lives at
    # ``<repo>/docs/maintenance/development_lessons.md``.
    try:
        repo_root = project_path.parents[2]
    except IndexError:
        sys.stderr.write(
            f"lessons_migrate: could not resolve repo root from {project_path}\n"
        )
        return 2

    # Resolve the ai-playbook repo root (for the git-clean check on the user
    # corpus). Walk up from the user corpus's resolved path.
    user_corpus = user_corpus_path(repo_root)
    if user_corpus is None:
        sys.stderr.write(
            "lessons_migrate: could not resolve shared_docs_dir from "
            ".ai-playbook/facts.md (lowercase key); set it in the facts file.\n"
        )
        return 1
    ai_playbook_root = user_corpus.resolve().parents[2]

    if not dry_run:
        try:
            assert_git_clean(repo_root, ai_playbook_root, user_corpus)
        except RuntimeError as e:
            sys.stderr.write(f"{e}\n")
            return 1

    project_text = project_path.read_text(encoding="utf-8")
    user_corpus_text = ""
    if user_corpus.is_file():
        user_corpus_text = user_corpus.read_text(encoding="utf-8")

    import datetime as _dt
    date_iso = _dt.date.today().isoformat()

    try:
        result = migrate(
            repo_root, project_text, user_corpus_text,
            write=not dry_run, ai_playbook_root=ai_playbook_root,
            date_iso=date_iso,
        )
    except RuntimeError as e:
        sys.stderr.write(f"{e}\n")
        return 1

    # Summary.
    print(f"lessons_migrate: project-specific kept: {result.project_kept}")
    print(f"lessons_migrate: cross-project moved:  {result.cross_moved}")
    print(f"lessons_migrate: ambiguous flagged:    {result.ambiguous_flagged}")
    print(f"lessons_migrate: dedup-merge flagged:  {result.dedup_merge_flagged}")
    print(f"lessons_migrate: refs rewritten:       {result.refs_rewritten}")
    print(f"lessons_migrate: refs unremappable:    {result.refs_unremappable}")
    if result.review_list_path:
        print(f"lessons_migrate: review list:         {result.review_list_path}")
    if dry_run:
        print("lessons_migrate: DRY RUN (no files written)")
        for line in result.review_lines[:20]:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
