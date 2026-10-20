# Plan: Strip the interpreter word in the FILES-COVERAGE matcher

Backlog origin: docs/history/backlog/2026-10-19-readiness-files-coverage-quote-prefix.md
Driving force: reliability (readiness warnings must mean what they say; this plan removes a false positive, so simplicity is not its force)
Authoring claim: docs/tmp/authoring-claims/2026-10-19-readiness-files-coverage-quote-prefix.md (session zcode-maintenance-auth-20261020-0300)
Execution budget: 1.0h total, largest task 0.75h

## Terms

- FILES-COVERAGE arm: the warning-only matcher `plan_files_coverage_warnings` in `scripts/plan_readiness.py` (machinery row `script:plan-files-coverage-arm`) that compares backticked acceptance-item spans against the tasks' Files: lists.
- Composite collector: `_plan_item_path_tokens` in the same module, the checklist-item token collector whose plain-prose exclusion and direct `_review_scope_path_token` normalization stay untouched by this plan.
- Interpreter word: a leading shell or interpreter token in a quoted command span; the pinned vocabulary is `bash`, `sh`, `zsh`, `python3`, `python` (the module constant the fix adds).
- Span: the content of one backticked span in an acceptance checkbox item, the matcher's only token source.
- Declared set: the Files: items the module already collects per task, unchanged by this plan.

## Why

An acceptance item quoting `bash scripts/foo.sh` warns as undeclared even when the task's Files list declares `scripts/foo.sh`: the matcher normalizes the whole span and never strips the leading interpreter word. Witnessed on the smme plan at every pre-round and the final readiness gate (warning-only, exit 0), training authors to dismiss readiness warnings. The fix is matcher-side; no rule tells authors to stop quoting the interpreter word.

## Gist & Examples

TLDR: the FILES-COVERAGE matcher strips a leading interpreter word from quoted command spans before matching the declared set, for reliability.

Before (today): `bash scripts/check_maintenance_pins.sh > /tmp/capture.txt 2>&1` in an acceptance item warns even though the task declares `scripts/check_maintenance_pins.sh`; the matcher compares the whole span, so the interpreter prefix and any command suffix after the path both break the match.

After (this plan): the matcher treats the span as a command line and compares its leading path token (the remainder after a pinned interpreter word, first whitespace-delimited token, path-shaped and scheme-free), so the witnessed bash-prefixed, redirection-suffixed quote of a declared script is silent; a genuinely undeclared leading path still warns.

Edge cases: an unprefixed command suffix (`scripts/foo.sh > /tmp/x 2>&1`) goes silent by the same leading-token match; a flag before the path (`bash -c scripts/foo.sh`) has a non-path-shaped leading token and keeps today's whole-span behavior; an interpreter word outside the pinned vocabulary (`timeout`, `env`) is not stripped; an interior interpreter word is never stripped; a remote script behind a pinned word stays silent through the scheme exclusion (design-consistent narrowing, boundary-tested).

## Outcome

The witnessed false positive stops firing (the origin row's exact shape: interpreter prefix plus redirection suffix), and a genuinely undeclared leading path still warns.

Gate delta: no new gate, validator, lock, or ledger; the change removes a false positive inside an existing warning arm. Machinery admission: the change modifies the existing arm and records no new admission; the machinery registry row `script:plan-files-coverage-arm` (incident 2026-10-11-plan-task3, review date 2027-01-12) continues to govern the arm; this plan's incident witness is the smme false positive (the origin row), its expected catch is every pre-round quoting a declared script behind an interpreter word or command suffix, and its false-positive cost is near zero (leading-token, prefix-scoped).

## Assumptions

- The pinned vocabulary is closed at those five words; extending it is a later machinery touch with its own row. Basis: the witnessed word (`bash`) plus the origin row's enumeration (`python3`, `sh`) and its "or equivalent" clause (`zsh`, `python`), closed at five.
- The leading-token match happens inside `_plan_acceptance_path_token`, the arm-private acceptance-span seam whose sole caller is the FILES-COVERAGE arm; the composite collector normalizes through `_review_scope_path_token` directly and deliberately keeps raw spans, so ownership-side checks are unchanged by this plan (a boundary test pins that). Basis: the call graph on disk (sole caller of `_plan_acceptance_path_token`; the collector's direct `_review_scope_path_token` call).
- The warning template and every unprefixed-shape wording stay byte-identical; a stripped span's warning names the stripped token (no existing test pins a prefixed span). Basis: the warning templates on disk and the existing test set.

Decision points requiring a grill: none (unattended authoring; the origin row fixes the design).

## Standing constraints

- Warning-only posture unchanged: the arm never changes an exit code and adds no schema field.
- The pinned vocabulary is the module constant; no call-site literal grows.
- No author-facing rule tells authors to stop quoting the interpreter word.
- Existing test assertions on FILES-COVERAGE wording stay byte-identical.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the witnessed shape (pinned prefix plus redirection suffix over a declared script) does not warn; the bare and suffixed unprefixed quotes of a declared script do not warn; a genuinely undeclared leading path (prefixed, suffixed, or bare) still warns.
- Safety: the warning template and unprefixed-shape wording are byte-identical; ownership-side consumers keep raw spans (no exit-code or schema change).
- Maintainability: one constant, one strip point in the shared tokenizer, tests pinning both the regression and the preserved warning.

**Done when:** the regression arm (the witnessed shape and its bare and suffixed variants over a declared script do not warn), the preserved-warning arm (an undeclared leading path still warns with the existing template), and the boundary arms (`timeout`/`env`/`bash -c`/interior-word/URL-scheme shapes behave as the Edge cases state) all pass in the suite; the full suite passes.

**Ship when:** none; repository-only behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production code:**
- `scripts/plan_readiness.py` - the interpreter-word strip in the shared acceptance tokenizer.

**Tests:**
- `scripts/test_plan_readiness.py` *(edited)*

**Docs:**
- `docs/history/backlog/2026-10-19-readiness-files-coverage-quote-prefix.md` - the origin row; edited only by the covered flip (plan-related extension).

**Plan-related extension:** only the covered flip of the origin row rides the landing; record the reason in the review report.

**Out of scope; reject unless plan-related:**
- Any matcher widening beyond the command's leading path token (interior tokens; flag-prefixed spans keep today's whole-span behavior).
- The composite collector's plain-prose token exclusion and its raw-span normalization.
- Any rule, template, or skill text change.

## Validation Commands

```bash
python3 scripts/test_plan_readiness.py   # expect: OK (exit 0)
```

A command's expected outcome on its comment line is the pass bar: the checkbox owning the command fails unless it exits 0.

### Task 1: Strip the pinned interpreter word in the shared tokenizer

Context surface: this task, `## Terms`, `## Standing constraints`, and the `_plan_acceptance_path_token` docstring's normalization contract.

Files:
- `scripts/plan_readiness.py` *(edited)*
- `scripts/test_plan_readiness.py` *(edited)*

Primary class anchors:
- `_plan_acceptance_path_token` in `scripts/plan_readiness.py`
- `plan_files_coverage_warnings` in `scripts/plan_readiness.py`

- [x] [class: IMPLEMENTATION_REQUIRED] Add the module constant `_INTERPRETER_WORDS = {"bash", "sh", "zsh", "python3", "python"}` beside the tokenizer.
- [x] [class: IMPLEMENTATION_REQUIRED] In `_plan_acceptance_path_token`, replace the whole-span token with the leading-token match: strip a leading `_INTERPRETER_WORDS` member when one is present, then take the remainder's first whitespace-delimited token as the compared token when that token is path-shaped and scheme-free; when no pinned prefix is present the same leading-token read applies to the span.
- [x] [class: IMPLEMENTATION_REQUIRED] In the same tokenizer: a scheme-bearing extracted token is out of scope and returns None through the existing scheme exclusion (no fall-through).
- [x] [class: IMPLEMENTATION_REQUIRED] In the same tokenizer: only a non-path-shaped extracted token (the `bash -c` shape) falls through to today's whole-span handling.
- [x] [class: IMPLEMENTATION_REQUIRED] Add tests in `scripts/test_plan_readiness.py`, the regression arm: the witnessed shape `bash scripts/foo.sh > /tmp/capture.txt 2>&1`, the bare prefixed shapes `bash`/`sh`/`zsh`/`python3`/`python scripts/foo.sh`, and the unprefixed suffixed shape `scripts/foo.sh > /tmp/capture.txt 2>&1` over a task declaring `scripts/foo.sh` emit no FILES-COVERAGE warning.
- [x] [class: IMPLEMENTATION_REQUIRED] Add tests in `scripts/test_plan_readiness.py`, the preserved-warning arm: an undeclared leading path in bare, prefixed, and suffixed shapes still warns through the existing template, the warning naming the stripped leading token.
- [x] [class: IMPLEMENTATION_REQUIRED] Add tests in `scripts/test_plan_readiness.py`, the boundary arms: `timeout scripts/foo.sh` and `env scripts/foo.sh` still warn; `bash -c scripts/foo.sh` keeps today's whole-span warning; an interior interpreter word is not stripped; `bash https://host/x.sh` stays silent through the scheme exclusion.
- [x] [class: IMPLEMENTATION_REQUIRED] Run the Validation Command from the repository root and record the output in the run record; a non-zero exit fails this checkbox.

### Task 2: Covered flip

Files:
- `docs/history/backlog/2026-10-19-readiness-files-coverage-quote-prefix.md` *(edited, plan-related extension)*

- [x] [class: IMPLEMENTATION_REQUIRED] Flip the origin row's Status to covered with this plan as witness (the flip rides the landing commit).
