#!/usr/bin/env python3
"""Lessons classification: lesson-shape classifier + prompt-intent classifier.

MOVED here from ``lessons_migrate.py`` (byte-identical) and PROMOTED to PUBLIC
leaf API on the move (the underscore dropped on the phrase-matching primitive
and the lesson-shape entry, because they are now consumed cross-module):

- ``FAMILY_KEYWORDS`` - the per-family generic-shape keyword phrase list (signal
  2 of the migrator's lesson routing).
- ``matches_family_vocab(title, body) -> (letter, matched_phrases) | None`` -
  the LESSON-SHAPE classifier. Classifies a lesson ENTRY's shape against
  ``FAMILY_KEYWORDS`` (lesson-descriptive phrases). First-match-wins over
  ``sorted(VALID_FAMILIES)`` (catalog A-H order). It does NOT classify a user
  prompt's intent: its phrases are not things users write, so it silently
  no-ops on real prompts (verified empirically). Behavior byte-identical to the
  pre-move ``_matches_family_vocab``.
- ``phrase_present(haystack_lower, phrase_lower) -> bool`` - the whole-word
  substring matcher shared by both classifiers.

ADDED here (the NEW prompt-intent classifier, NOT the lesson-shape classifier):

- ``PROMPT_INTENT_VOCAB`` - a user-intent vocabulary (lemmas + common
  inflections + domain shapes; NOT lesson-descriptive phrases).
- ``classify_prompt(prompt) -> tuple[str, list[str]] | None`` - classifies a
  user prompt's INTENT. Same phrase-matching primitive, but iterates an EXPLICIT
  ``PROMPT_FAMILY_ORDER`` (G and H before C) and first-match-wins over THAT
  order (NOT ``sorted(VALID_FAMILIES)``).

Mid-tier node: imports ``lessons_corpus`` for ``VALID_FAMILIES`` / ``Lesson``
(not a stdlib-only leaf).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Allow ``import lessons_corpus`` whether run as a script or via ``python -m``
# (mirrors lessons_adopt.py). The leaf will be symlinked into
# ~/.ai-playbook/scripts/ and imports sibling leaves from the repo scripts dir.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lessons_corpus  # noqa: E402  (mid-tier: imports the stdlib-only leaf)


# --------------------------------------------------------------------------- #
# Per-family generic-shape keyword phrase list (signal 2 vocabulary).
# --------------------------------------------------------------------------- #
#: Authority: ``coding_guidelines.md`` #17-#25 (the catalog). This is a SECONDARY
#: DERIVED VIEW of the catalog, NOT single-sourced: when a future audit revises a
#: family's ``**Shape trigger:**`` wording (#17 says triggers may be revised),
#: this list can drift silently and mis-route. Guard: the migrator's
#: ``--selftest`` asserts each family's list contains at least one
#: DISCRIMINATING TOKEN not in the union of the others' lists (a deterministic
#: check that FAILS when a family's keywords collapse to generic English).
#:
#: Phrases are matched case-insensitively as whole-word substrings against the
#: lesson's title+body. Phrases are deliberately CROSS-PROJECT and stable: they
#: ARE the catalog's engineering vocabulary (type annotations, exception
#: handling, post-aggregation validation, test discipline, matching/dedup,
#: review loops, data-loss logging, atomic writes, sentinel values) - NEVER
#: repo/domain terms.
FAMILY_KEYWORDS: dict[str, list[str]] = {
    # #18 Equivalence-class coverage (A).
    "A": [
        "equivalence class",
        "equivalence-class",
        "parametrized test",
        "partition the input",
        "edge case coverage",
    ],
    # #19 Error-policy propagation (B).
    "B": [
        "catch specific exception",
        "exception handling",
        "error-policy propagation",
        "degrade vs raise",
        "fallback path",
    ],
    # #20 Representation: sentinel vs None vs exception (C).
    "C": [
        "type-safe sentinel",
        "sentinel value",
        "absent value",
        "non-representable sentinel",
        "representation of missing",
    ],
    # #21 Single source of truth (D).
    "D": [
        "single source of truth",
        "derived index",
        "sibling aggregator",
        "byte-identical pattern",
        "silent overwrite",
    ],
    # #22 Temporal / ordering invariants (E).
    "E": [
        "sliding-window matcher",
        "ordered queue",
        "temporal ordering",
        "post-aggregation validation",
        "recompute tolerance",
    ],
    # #23 Layering / dependency direction (F).
    "F": [
        "dependency direction",
        "orchestration layer",
        "layering violation",
        "circular import",
        "read-only gate",
    ],
    # #24 Data-loss observability (G).
    "G": [
        "data-loss observability",
        "silent drop",
        "unmatched items",
        "warning or higher",
        "explicit fallback",
    ],
    # #25 Verify the real thing, not the abstraction (H).
    "H": [
        "verify the real thing",
        "data trace verification",
        "data identity tuple",
        "code inspection alone",
        "authority-cited discriminator",
    ],
}


# --------------------------------------------------------------------------- #
# User-intent vocabulary (PROMPT classifier; NOT the lesson-shape vocabulary).
# --------------------------------------------------------------------------- #
#: Seed with LEMMAS + common inflections + domain shapes, not only multi-word
#: phrases. C does NOT seed bare "missing" (reserved for G). The bare-phrase seed
#: "drop" does NOT match inside "dropping", so present-participle forms are
#: seeded explicitly.
PROMPT_INTENT_VOCAB: dict[str, list[str]] = {
    # A: equivalence-class coverage.
    "A": [
        "test the case",
        "empty string",
        "null input",
        "boundary",
        "edge case",
        "parametrized",
    ],
    # B: error-policy propagation.
    "B": [
        "swallow",
        "swallowed",
        "degrade",
        "raise vs warn",
        "fallback",
        "silent failure",
    ],
    # C: representation (sentinel vs None vs exception). NOT bare "missing".
    "C": [
        "null",
        "none",
        "sentinel",
        "absent",
        "placeholder",
    ],
    # D: single source of truth.
    "D": [
        "two places",
        "disagree",
        "disagrees",
        "disagreed",
        "drift",
        "duplicate",
        "consistent",
    ],
    # E: temporal / ordering invariants.
    "E": [
        "ordering",
        "race",
        "stale",
        "timing",
        "reorder",
    ],
    # F: layering / dependency direction.
    "F": [
        "circular",
        "reach up",
        "dependency direction",
        "refactor the layer",
    ],
    # G: data-loss observability.
    "G": [
        "drop",
        "drops",
        "dropped",
        "dropping",
        "missing",
        "missing row",
        "skipped",
        "unmatched",
        "lost",
        "losing",
        "loses",
    ],
    # H: verify the real thing, not the abstraction.
    "H": [
        "trace",
        "verify",
        "mock",
        "actual data",
        "field name",
    ],
}

#: EXPLICIT order for prompt classification (r5-L1). G (data-loss) and H
#: (verify-the-real-thing) are the plan's flagship families and MUST win over C
#: (representation) on overlap. ``sorted(VALID_FAMILIES)`` consults C before G/H,
#: so "verify the null-handling path" would route to C (C seeds ``null``) instead
#: of H, inverting the flagship direction; C is the catch-all representation
#: family and goes last. The lesson-shape classifier keeps its OWN
#: ``sorted(VALID_FAMILIES)`` first-match-wins - it classifies lesson entries,
#: not prompts, and is unchanged.
PROMPT_FAMILY_ORDER = ("G", "H", "A", "B", "D", "E", "F", "C")

#: Task verbs required near a phrase match for classifier v2 (opt-in precision).
#: Matched as whole-word substrings; must appear in a task-intent position
#: (prompt-leading or after an intent prefix), not as a noun compound
#: (e.g. "typo fix" does NOT count).
TASK_VERBS: tuple[str, ...] = (
    "debug",
    "fix",
    "investigate",
    "trace",
    "verify",
    "explain",
    "check",
    "review",
)

#: Max character distance between a task-verb span and a phrase-match span (v2).
#: FLAGGED threshold; pinned for opt-in v2 selftests.
CLASSIFIER_V2_PROXIMITY_WINDOW = 80

#: Intent prefixes after which a task verb counts (whole-word, trailing space).
_TASK_VERB_INTENT_PREFIXES: tuple[str, ...] = (
    "please ",
    "can you ",
    "could you ",
    "help me ",
    "need to ",
    "want to ",
    "try to ",
    "how to ",
    "why ",
    "to ",
)


# --------------------------------------------------------------------------- #
# Phrase-matching primitive (PUBLIC; shared by both classifiers).
# --------------------------------------------------------------------------- #
def phrase_present(haystack_lower: str, phrase_lower: str) -> bool:
    """True iff ``phrase_lower`` appears in ``haystack_lower`` as a whole-word
    substring (the phrase edges align with non-word characters or string ends)."""
    # Escape regex metacharacters in the phrase, then anchor both ends with
    # word-boundary-ish guards. A phrase token char is ``[A-Za-z0-9_-]``; the
    # edge guard is ``(?:^|[^A-Za-z0-9_])`` on the left and
    # ``(?:$|[^A-Za-z0-9_])`` on the right (underscore/digit/dash are part of
    # the token so a hyphenated phrase like "type-safe" matches "type-safe
    # sentinel").
    escaped = re.escape(phrase_lower)
    # Treat a trailing/leading hyphen as a token char (so "type-safe" works);
    # underscore and alnum are token chars.
    pattern = re.compile(r"(?:^|[^A-Za-z0-9_])" + escaped + r"(?:$|[^A-Za-z0-9_])")
    return bool(pattern.search(haystack_lower))


# --------------------------------------------------------------------------- #
# Lesson-shape classifier (PUBLIC; byte-identical to the pre-move body).
# --------------------------------------------------------------------------- #
def matches_family_vocab(title: str, body: str) -> tuple[str, list[str]] | None:
    """Signal 2: return ``(family_letter, matched_phrases)`` if the title+body
    matches a family's keyword phrase list (case-insensitive whole-word
    substring), else ``None``.

    A "whole-word substring" match for a multi-word phrase is a case-insensitive
    substring search bounded by non-word characters on each phrase edge. For
    single-word phrases we use a word-boundary regex. For multi-word phrases the
    internal structure (spaces, hyphens) already anchors the edges.
    """
    haystack = (title + "\n" + body).lower()
    matched: list[str] = []
    # Pick the FIRST family (catalog A-H order) with a match; first-match-wins
    # keeps the classifier deterministic.
    for letter in sorted(lessons_corpus.VALID_FAMILIES):
        phrases = FAMILY_KEYWORDS.get(letter, [])
        for phrase in phrases:
            p = phrase.lower()
            if phrase_present(haystack, p):
                matched.append(f"{letter}:{phrase}")
                return letter, matched
    return None


# --------------------------------------------------------------------------- #
# Prompt-intent classifier (NEW; NOT the lesson-shape classifier).
# --------------------------------------------------------------------------- #
def classify_prompt(prompt: str) -> tuple[str, list[str]] | None:
    """Classify a user prompt's INTENT. Returns ``(family_letter, matched_phrases)``
    or ``None``.

    Uses the SAME phrase-matching primitive as the lesson-shape classifier, but
    keyed on ``PROMPT_INTENT_VOCAB`` (user-intent lemmas + inflections + domain
    shapes, NOT lesson-descriptive phrases). Iterates the EXPLICIT
    ``PROMPT_FAMILY_ORDER`` (G and H before C), first-match-wins over THIS order
    (NOT ``sorted(VALID_FAMILIES)``): the flagship families G (data-loss) and H
    (verify-the-real-thing) must win over C (representation) on overlap.
    """
    haystack = prompt.lower()
    for letter in PROMPT_FAMILY_ORDER:
        phrases = PROMPT_INTENT_VOCAB.get(letter, [])
        for phrase in phrases:
            p = phrase.lower()
            if phrase_present(haystack, p):
                return letter, [f"{letter}:{phrase}"]
    return None


def _find_phrase_span(haystack_lower: str, phrase_lower: str) -> tuple[int, int] | None:
    """Return ``(start, end)`` of the first whole-word phrase match, else ``None``."""
    escaped = re.escape(phrase_lower)
    pattern = re.compile(r"(?:^|[^A-Za-z0-9_])(" + escaped + r")(?:$|[^A-Za-z0-9_])")
    match = pattern.search(haystack_lower)
    if match is None:
        return None
    return match.start(1), match.end(1)


def _span_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Character gap between two half-open spans (0 if they overlap)."""
    a_start, a_end = a
    b_start, b_end = b
    if a_end <= b_start:
        return b_start - a_end
    if b_end <= a_start:
        return a_start - b_end
    return 0


def _is_task_verb_at_intent_position(haystack_lower: str, verb_start: int) -> bool:
    """True when ``verb_start`` is a task-intent position (not e.g. noun ``fix``)."""
    left = haystack_lower[:verb_start]
    if left.strip() == "":
        return True
    for prefix in _TASK_VERB_INTENT_PREFIXES:
        if left.endswith(prefix):
            return True
    first = re.match(r"\s*(\S+)", haystack_lower)
    if first is not None and first.start(1) == verb_start:
        return True
    return False


def _find_task_verb_spans(haystack_lower: str) -> list[tuple[int, int]]:
    """Whole-word task-verb spans that pass the intent-position gate."""
    spans: list[tuple[int, int]] = []
    for verb in TASK_VERBS:
        escaped = re.escape(verb.lower())
        pattern = re.compile(r"(?:^|[^A-Za-z0-9_])(" + escaped + r")(?:$|[^A-Za-z0-9_])")
        for match in pattern.finditer(haystack_lower):
            start = match.start(1)
            if _is_task_verb_at_intent_position(haystack_lower, start):
                spans.append((start, match.end(1)))
    return spans


def classify_prompt_v2(prompt: str) -> tuple[str, list[str]] | None:
    """Classify prompt intent (v2): phrase match AND task verb within proximity.

    Same ``PROMPT_FAMILY_ORDER`` / ``PROMPT_INTENT_VOCAB`` as v1, but requires a
    ``TASK_VERBS`` whole-word match in a task-intent position within
    ``CLASSIFIER_V2_PROXIMITY_WINDOW`` chars of the matched phrase.
    """
    haystack = prompt.lower()
    verb_spans = _find_task_verb_spans(haystack)
    if not verb_spans:
        return None
    for letter in PROMPT_FAMILY_ORDER:
        phrases = PROMPT_INTENT_VOCAB.get(letter, [])
        for phrase in phrases:
            p = phrase.lower()
            if not phrase_present(haystack, p):
                continue
            phrase_span = _find_phrase_span(haystack, p)
            if phrase_span is None:
                continue
            for verb_span in verb_spans:
                if _span_distance(phrase_span, verb_span) <= CLASSIFIER_V2_PROXIMITY_WINDOW:
                    return letter, [f"{letter}:{phrase}"]
    return None


# --------------------------------------------------------------------------- #
# Self-test.
# --------------------------------------------------------------------------- #
def _selftest_check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" - {detail}" if detail else ""))
    return condition


def selftest() -> int:
    all_ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal all_ok
        all_ok = _selftest_check(label, cond, detail) and all_ok

    # ---- prompt_realistic: "the report dropped a row" -> family G ----
    got = classify_prompt("the report dropped a row")
    check(
        "prompt_realistic: non-None tuple",
        got is not None,
        str(got),
    )
    check(
        "prompt_realistic: first element is family G",
        got is not None and got[0] == "G",
        str(got),
    )

    # ---- prompt_realistic_inflected: lemma + inflection seeding ----
    for prompt, why in [
        ("the report is missing a row", "missing + missing row"),
        ("the report drops a sell", "drops"),
        ("the report is dropping rows", "dropping (present participle)"),
        ("the total disagrees between the two tabs", "disagrees"),
    ]:
        got = classify_prompt(prompt)
        check(
            f"prompt_realistic_inflected: {prompt!r} matches ({why})",
            got is not None,
            str(got),
        )

    # ---- overlap_missing: "missing data" -> G (NOT C) ----
    got = classify_prompt("missing data")
    check(
        "overlap_missing: 'missing data' -> family G (data-loss), NOT C",
        got is not None and got[0] == "G",
        str(got),
    )

    # ---- overlap_verify_vs_representation: "verify the null-handling path" -> H (NOT C) ----
    got = classify_prompt("verify the null-handling path")
    check(
        "overlap_verify_vs_representation: 'verify the null-handling path' -> H (NOT C)",
        got is not None and got[0] == "H",
        str(got),
    )

    # ---- prompt_no_match: "fix the typo" -> None ----
    got = classify_prompt("fix the typo")
    check(
        "prompt_no_match: 'fix the typo' -> None",
        got is None,
        str(got),
    )

    # ---- lesson_shape_unchanged: matches_family_vocab returns the SAME family ----
    # The lesson-shape classifier's FAMILY_KEYWORDS include "silent drop" /
    # "unmatched items" / "data-loss observability" (G). A lesson body containing
    # one of these must classify to G, byte-identical to the pre-move behavior.
    title = "Silent drop in the matcher"
    body = (
        "A silent drop in the unmatched items causes data-loss observability "
        "gaps; the warning or higher path was missing."
    )
    got = matches_family_vocab(title, body)
    check(
        "lesson_shape_unchanged: lesson body -> family G (byte-identical)",
        got is not None and got[0] == "G",
        str(got),
    )

    # ---- depends_on_lessons_corpus: this is a mid-tier node ----
    check(
        "depends_on_lessons_corpus: imports lessons_corpus (mid-tier node)",
        lessons_corpus is not None and hasattr(lessons_corpus, "VALID_FAMILIES"),
        "",
    )

    # ---- phrase_present_single_source: asserted in lessons_migrate selftest ----
    # (IDENTITY, not equality). The assertion lives in the migrator's selftest
    # because it requires importing both modules. Here we only assert the leaf
    # exposes the primitive at all.
    check(
        "phrase_present: leaf exposes the primitive as a public callable",
        callable(phrase_present),
        "",
    )

    # ---- v2_false_positive_comment: incidental "dropped" + noun "fix" -> None ----
    got = classify_prompt_v2("the typo fix dropped a word in the comment")
    check(
        "v2_false_positive_comment: incidental match -> None under v2",
        got is None,
        str(got),
    )

    # ---- v2_flagship_no_verb: flagship v1 prompt has no task verb -> None ----
    got = classify_prompt_v2("the report dropped a row")
    check(
        "v2_flagship_no_verb: 'the report dropped a row' -> None under v2",
        got is None,
        str(got),
    )

    # ---- v2_true_positive: task verb + phrase within window -> family G ----
    got = classify_prompt_v2("debug why the report dropped a row")
    check(
        "v2_true_positive: 'debug why the report dropped a row' -> family G",
        got is not None and got[0] == "G",
        str(got),
    )

    # ---- v1_default_unchanged: all existing v1 #prompt_* arms still pass ----
    v1_prompt_cases: list[tuple[str, str, object]] = [
        ("the report dropped a row", "prompt_realistic", "G"),
        ("missing data", "overlap_missing", "G"),
        ("verify the null-handling path", "overlap_verify_vs_representation", "H"),
        ("fix the typo", "prompt_no_match", None),
    ]
    for prompt, label, expected in v1_prompt_cases:
        got = classify_prompt(prompt)
        if expected is None:
            ok = got is None
        else:
            ok = got is not None and got[0] == expected
        check(
            f"v1_default_unchanged: {label} ({prompt!r})",
            ok,
            str(got),
        )
    for prompt, why in [
        ("the report is missing a row", "missing + missing row"),
        ("the report drops a sell", "drops"),
        ("the report is dropping rows", "dropping (present participle)"),
        ("the total disagrees between the two tabs", "disagrees"),
    ]:
        got = classify_prompt(prompt)
        check(
            f"v1_default_unchanged: prompt_realistic_inflected {prompt!r} ({why})",
            got is not None,
            str(got),
        )

    print()
    print("ALL PASS" if all_ok else "SOME FAIL")
    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "--selftest":
        return selftest()
    sys.stderr.write("usage: lessons_classify.py --selftest\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
