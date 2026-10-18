# Plan: facts path resolver accepts valid TOML string forms

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-07-facts-path-resolver-valid-toml-quotes.md`

Grouping entry: docs/history/backlog/PLAN-PROMPTS.md, `## facts-path-resolver-valid-toml-strings` (its Prompt, scope arms, and rejected alternatives are this plan's spec of record).

Driving force: efficiency

Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-facts-path-resolver-valid-toml-strings-p5e88a2e8-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 1.5h total, largest task 1h

Authoring claim: docs/tmp/authoring-claims/facts-path-resolver-valid-toml-strings.md (session sess_dbec0621-d67c-458d-9416-9f7a02107f3b; pick 2 of 2 of the 01:20 author-lane mandate, 2026-10-17)

## Terms

- TOML fence: the first ```toml fenced block in the repo facts file; the resolver extracts it line-wise and parses `key = value` lines inside it.
- basic string: a TOML double-quoted string (`"value"`) in which escape sequences (`\"`, `\\`, `\t`, and the rest of the TOML basic-string escape set: `\b \t \n \f \r \" \\ \uXXXX \UXXXXXXXX`) are processed; an escape outside the set, or `\u`/`\U` not followed by valid hex, or a `\u`/`\U` escape denoting a value above U+10FFFF or a surrogate, makes the line unsupported and it resolves as absent (strict posture, matching TOML and the sibling tomllib parser).
- literal string: a TOML single-quoted string (`'value'`) in which no escapes are processed; what is written is what the value contains.
- resolver: `resolve_toml_key_raw` in scripts/facts_paths.py and its `resolve_toml_key` wrapper; the SINGLE parser for the TOML-fence format.
- supported subset: the value forms this plan teaches the resolver to accept: single-line basic strings and single-line literal strings. Everything else (multi-line strings, non-string value types, unclosed quotes) resolves as absent, exactly as today, and the subset is documented in the parser's docstring.
- refusal behavior: the resolver's existing absence semantics; a missing file, a missing key, or a line the supported subset cannot parse returns None, which the callers' gates treat as unconfigured. This plan changes none of it.
- closeout: the consumer-completion workflow that consults resolved facts values and stops on unconfigured keys (the workflow whose stop the incident origin witnessed).
- facts contract: the fence format the module docstring documents (single-line `key = value` path and token strings).

## Why

A consumer closeout stopped because a valid single-quoted facts value resolved as absent, forcing a manual edit to the local facts file. The matcher behind `resolve_toml_key_raw` accepts only double-quoted strings with no escape handling, so one of the two standard TOML string forms is invisible to every consumer of the shared helper.

## Gist & Examples

TLDR: teach the facts resolver's TOML-fence parser both TOML string forms, basic with escapes and literal single-quoted, so every string form the facts contract promises resolves while refusal behavior stays untouched, for efficiency.

Before: `tmp_dir = '/tmp/ai-tmp/'` in a facts file resolves as absent and the closeout gate stops; the operator renames the quotes by hand. After: the same line resolves to `/tmp/ai-tmp/`, identical to its double-quoted form.

Before: a value written with TOML escapes (`"C:\\tools\\"`) resolves today to the raw undecoded bytes (`C:\\tools\\`), so no correct parse exists. After: the escapes decode per TOML and the value is `C:\tools\`; a line TOML rejects (an unterminated string) resolves as absent instead of resolving to wrong bytes, which is the recorded flip class in Assumptions.

After (unchanged): a missing key, a missing facts file, or an unsupported form (an unclosed quote, a multi-line string) still returns None; no caller gate changes behavior.

## Outcome

The shared resolver accepts every single-line TOML string form the facts contract promises, and the witnessed closeout stop cannot recur for quoting reasons.

- A literal single-quoted value resolves to exactly the value its double-quoted twin resolves to (the incident path, pinned as a regression witness).
- Basic strings process the TOML escape set, so escaped quotes and path-escapes parse correctly instead of stopping at the first quote character.
- Refusal semantics stay None-shaped: absent keys, absent files, and unsupported forms return None as before (the recorded flip class re-classifies previously mis-parsed bytes, not previously valid values), and the Markdown-table parser half of the module is untouched.
- Change note for the landing: presently-inert mistyped values (written single-quoted or otherwise unparseable, resolved as absent until now) become effective the moment this lands, because the deployed home copy symlinks to this file; the affected keys are every fence key a consumer resolves (plans_dir, tmp_dir, reviews_dir, and the rest), and the flip direction is inert-to-effective, which is the fix working but worth naming when a mid-week consumer behavior change is diagnosed.

Gate delta: none added and none removed in the counted classes; the change widens one parser's accepted-value set inside its documented contract (a fix-class repair of a representation mismatch, not a new refusal or gate); no new refusal class, hard gate, fence, protocol layer, validator, or state-schema field; the missing-key and malformed-input refusal behavior is retained, and the one deliberate re-classification (the escape-flip class in Assumptions: previously mis-parsed backslash-bearing values) re-reads previously wrong bytes as either the TOML-correct value or absent, never as a new refusal of a TOML-valid input.

## Assumptions

- assume the fix stays a narrow lexical extension of the existing line parser, not a tomllib rewrite; basis: the observed runtime set for this helper spans the project venv (Python 3.14) and system Python 3.9, tomllib is stdlib only from 3.11, a 3.9-compatible backport would be a third-party dependency against the module's stdlib-only contract, and the facts contract only ever promises single-line path strings, which a line-scoped parser covers completely.
- assume the single-parser invariant holds (the TOML-fence parser and the Markdown-table parser stay separate); basis: the module docstring's format-split note (one parser silently returns None for the other format) and the rejected project-strictness plan's single-parser invariant.
- assume the promised value set is single-line strings; basis: every key the fence carries today (plans_dir, tmp_dir, reviews_dir, session-budget tokens) is a path or token string, and the module docstring documents the fence format as `key = "value"` lines.
- assume no consumer change is needed; basis: all consumers call `resolve_toml_key` / `resolve_toml_key_raw`, whose signatures and None semantics this plan does not change.
- flip class (deliberate, recorded): currently-resolving double-quoted values containing backslash escapes or a trailing backslash-terminated quote are re-classified by TOML-correct parsing; measured on the current matcher, `plans_dir = "C:\tmp\"` resolves today to `C:\tmp\` and `plans_dir = "C:\Users\x"` resolves verbatim, while TOML rejects both, so after this plan the first resolves as absent and the second is written with a doubled backslash when the value is intended; consumers observe the written value where TOML accepts it and absence where TOML rejects it (defaults resume, gates stop), never a new refusal of a TOML-valid input; basis: the lenient matcher measured against tomllib on this class, and the origin's representation-mismatch framing.

Decision points requiring a grill: none remain.

## Standing constraints

- The module stays stdlib-only with no new imports beyond the standard library it already uses.
- The fix is confined to scripts/facts_paths.py: the parser function, its docstrings, and the in-file selftest; consumer scripts and the Markdown-table parser half are read-only for this plan.
- Committed files carry no em-dash and no absolute user paths; the hygiene scan runs green before commit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the witnessed incident path (single-quoted value) resolves exactly as its double-quoted form, and every TOML basic-string escape in the supported set decodes per TOML.
- compatibility: every existing double-quoted resolution of a line without escape sequences behaves byte-identically; escape-bearing lines that today resolve via the lenient matcher are deliberately re-classified per TOML (the recorded flip class in Assumptions); the existing selftest arms stay green unchanged.
- refusal fidelity: absent key, absent file, and unsupported form still return None; no new exception path and no silent default substitution.
- separation: the Markdown-table matcher lines are untouched; one parser per on-disk format.

**Done when:**
- `python3 scripts/facts_paths.py --selftest` exits 0 on the finished tree, including the new incident-regression and escape arms.
- the existing selftest arms pass unchanged (no edits to their labels or expectations).
- the hygiene scan passes over the changed set.

**Ship when:**
- none stated.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/facts_paths.py` (both halves this plan touches live in this one file: the TOML-fence parser around `resolve_toml_key_raw`, and the in-file `selftest()` fixtures that are the plan's only test surface)

**Tests:**
- none listed separately; the in-file selftest lives in `scripts/facts_paths.py`, listed above (no separate test files exist for the resolver).

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- every consumer script calling the resolver (seventeen Python scripts, plus one hook wrapper embedding a Python import); reason: the public API and None semantics are unchanged, so consumers need no edits; a consumer that misuses the API is a separate finding.
- the Markdown-table half of scripts/facts_paths.py (`resolve_table_key` and its matchers); reason: single-parser separation is a standing constraint, and its parsing is untouched.

## Validation Commands

```bash
# Run from the repository root. The selftest leg is RED-today for the new
# arms (the incident path returns None before Task 1) and GREEN after.
cd "$(git rev-parse --show-toplevel)" || exit 1

fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

PATH="${HOME}/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/facts_paths.py --selftest || fail "selftest"
bash scripts/check-no-em-dash.sh touched || fail "em-dash"
if bash "${HOME}/.ai-playbook/scripts/scan-public-hygiene.sh"; then :; else fail "hygiene"; fi

# Count-exact span pins, one dedicated grep per obligation.
expect1() { n=$(grep -oF -- "$2" "$1" | wc -l | tr -d ' '); [ "$n" -eq 1 ] || fail "expect 1 hit in $1 for: $2 (got $n)"; }
expect1 scripts/facts_paths.py "literal string (single-quoted) support"
expect1 scripts/facts_paths.py "resolve_toml_key_raw: single-quoted value equals its double-quoted form"
expect1 scripts/facts_paths.py "resolve_toml_key_raw: escaped quote inside a basic string"
expect1 scripts/facts_paths.py "resolve_toml_key_raw: literal string keeps backslashes verbatim"
expect1 scripts/facts_paths.py "resolve_toml_key_raw: backslash-terminated quote resolves as absent"
expect1 scripts/facts_paths.py "resolve_toml_key_raw: unclosed quote resolves as absent"
expect1 scripts/facts_paths.py "resolve_toml_key_raw: absent key returns None"
expect1 scripts/facts_paths.py "lines (basic or literal strings)"

echo "VALIDATION OK"
```

### Task 1: teach the TOML-fence parser both string forms

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Primary class anchors:
- `resolve_toml_key_raw` in `scripts/facts_paths.py`

Files:
- `scripts/facts_paths.py`

- [x] Replace the double-quote-only line matcher in `resolve_toml_key_raw` (the `re.match` at its loop tail, currently `m = re.match(r'^\s*(' + re.escape(key) + r')\s*=\s*"([^"]*)"\s*$', line)`) with a small value parser that recognizes a basic string (double quotes, TOML escape set processed) and a literal string (single quotes, no escapes processed) and returns the decoded value, leaving the fence extraction, the key match, and the None-on-no-match semantics untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] Retain the existing trailing `.strip()` on the decoded value (today's matcher strips the captured group; keep that so escape-free padded values resolve byte-identically). [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the end-of-line anchor: the decoded value is returned only when the closing quote is followed by nothing but whitespace to end of line (the current regex anchor guarantees this; trailing content, a TOML comment included, keeps the line unsupported). [class: IMPLEMENTATION_REQUIRED]
- [x] Document the supported subset in `resolve_toml_key_raw`'s docstring with this exact sentence: "Supported subset: single-line basic strings (escapes processed; an escape outside the TOML set, or a `\u`/`\U` escape that is invalid or not a Unicode scalar, makes the line unsupported) and literal string (single-quoted) support; multi-line strings, non-string values, unclosed quotes, and lines with trailing content are unsupported and resolve as absent." [class: IMPLEMENTATION_REQUIRED]
- [x] Update the module header's fence description from ``key = "value"`` lines to ``key = "value"`` lines (basic or literal strings), and update `resolve_toml_key`'s docstring fence sentence to name both string forms in different words (not the pinned sentence verbatim, so the count-exact pin stays at 1). [class: IMPLEMENTATION_REQUIRED]
- [x] Behavior witness (the incident): given a facts fence line `tmp_dir = '/tmp/ai-tmp/'`, expects `resolve_toml_key_raw` to return `/tmp/ai-tmp/`, identical to the double-quoted form of the same value. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (refusal fidelity): given a line with an unclosed quote (`tmp_dir = "/tmp/ai-tmp/`), given a multi-line string opener, given a non-string value (`plans_dir = 3`), given an invalid escape (`tmp_dir = "C:\Users\x"`), given a scalar-invalid escape (`tmp_dir = "\U00110000"`), and given a trailing-comment line (`plans_dir = "v" # note`), expects None returned and no exception raised for every one of them. [class: IMPLEMENTATION_REQUIRED]
- [x] Flip carve-out in the same witness: four of the six inputs match today's absence semantics; the invalid-escape and scalar-invalid inputs resolve to values today and their None is the recorded flip class in Assumptions, not preserved refusal. [class: IMPLEMENTATION_REQUIRED]

### Task 2: selftest regression and compatibility arms

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Primary class anchors:
- `selftest` in `scripts/facts_paths.py`

Files:
- `scripts/facts_paths.py`

- [x] Add the incident-regression arm to the `resolve_toml_key_raw` selftest block (in a fresh fixture fence of its own, beside the existing `raw_missing` arm's block: a fixture fence carrying the two quoting forms under two DISTINCT keys with the identical value, expecting equality of the two raw results; label the arm `resolve_toml_key_raw: single-quoted value equals its double-quoted form`. [class: REPOSITORY_TEST]
- [x] Why distinct keys: the resolver returns on the first key match, so the same key written twice exposes only one form and the equality arm would be green even without the fix. [class: REPOSITORY_TEST]
- [x] Add the escape arm: basic strings written with TOML escapes, one exercising backslash decoding (bytes `esc = "C:\\tools\\"` expecting `C:\tools\`) and one exercising escaped quotes (bytes `note = "a \"quoted\" word"` expecting `a "quoted" word`, the only input class where today's matcher truncates); label the arm `resolve_toml_key_raw: escaped quote inside a basic string`. [class: REPOSITORY_TEST]
- [x] Add the literal-fidelity arm: a literal string containing backslashes (`win_dir = 'C:\temp\'`), expecting the backslashes verbatim (no escape processing inside single quotes, which no other planned arm discriminates); label the arm `resolve_toml_key_raw: literal string keeps backslashes verbatim`. [class: REPOSITORY_TEST]
- [x] Add the flip-witness arm: a fixture line `plans_dir = "C:\tmp\"` (a value the lenient matcher resolves today), expecting None after the fix so the recorded flip class is witnessed, not incidental; label the arm `resolve_toml_key_raw: backslash-terminated quote resolves as absent`. [class: REPOSITORY_TEST]
- [x] Add the refusal arms as ONE combined check whose label is used exactly once in the file (a loop over the refusal inputs inside a single check call; the count-exact pin fails on a repeated label): an unclosed double quote, an unclosed literal quote, a non-string value, a multi-line string opener, an invalid escape, and a trailing-comment line in the fixture fence, each expecting None with no exception; label the check `resolve_toml_key_raw: unclosed quote resolves as absent`. [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/facts_paths.py --selftest` and confirm exit 0 with every pre-existing arm passing unchanged and the new arms green (RED before Task 1 for every new arm: the witnessed single-quoted path returns None today, while the escape, flip, and invalid-escape inputs resolve to wrong values). [class: REPOSITORY_TEST]
- [x] The unchanged-arms witness: the pre-existing label `resolve_toml_key_raw: absent key returns None` appears exactly once before and after the change (pinned in Validation Commands), so the existing arms are demonstrably untouched. [class: REPOSITORY_TEST]
