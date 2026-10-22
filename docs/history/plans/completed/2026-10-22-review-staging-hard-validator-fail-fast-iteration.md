# Plan: Review Staging Hard Validator Fail-Fast Iteration

Backlog origin: docs/history/backlog/2026-10-21-review-staging-hard-validator-fail-fast-iteration.md
Driving force: efficiency + code-quality
Plan review record: .ai-playbook/reviews/2026-10-22-plan-review-review-staging-hard-validator-fail-fast-iteration-r*.md
Execution budget: 2.5h total, largest task 1.25h
Authoring claim: docs/tmp/authoring-claims/2026-10-21-review-staging-hard-validator-fail-fast-iteration.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Hard mode:** The validator CLI posture that returns exit 1 for an invalid record.
- **Independent diagnostic:** An error whose predicate can be evaluated without a failed prerequisite.
- **Cascade diagnostic:** A downstream error caused only by malformed or absent prerequisite data.
- **Clause pointer:** A concise reference to the owning section or recording rule in the review-staging skill.
- **First-error routing:** The existing consumer contract where plan readiness classifies `ValidationResult.errors[0]` into a specific failure family.

## Why

The origin records eight fix-validate rounds for one canonical review record. The current hard-mode fixture already reports ten errors, but sorts them and does not cover several failure families in the origin or test clause pointers. Pin the remaining independently applicable diagnostics before changing behavior, then preserve the existing readiness routing while making each reported failure actionable.

## Gist & Examples

TLDR: Pin the missing hard-mode diagnostics and add clause pointers, improving repair efficiency without changing readiness routing.

Before: The hard-mode characterization covers ten errors, but sorts the output and misses several failure families named by the incident. Authors can also see a failure without its owning skill clause.

After: A regression fixture covers the origin's failure families and distinguishes independent failures from cascades. Hard output points to each existing clause, keeps its first error for readiness routing, and remains stable. The existing clause documentation stays in place.

## Outcome

Hard-mode diagnostics identify the origin's independently applicable review-record failures in a single actionable report while preserving readiness classification and validation verdicts.

- A fixture proves which reported failure families are currently missing or lack clause pointers.
- Hard-mode error lines identify their owning review-staging clause and retain stable order.
- Readiness keeps the same first-error classification; passing, soft, and preflight outcomes stay unchanged.

Gate delta: none; this improves diagnostics in an existing validator and adds no gate, refusal class, ledger, field, or ceremony.

## Assumptions

- The origin row is the available witness for the eight-round incident; its listed failure families define the regression fixture.
- The current ten-error fixture must remain covered; new assertions target the origin-listed families and error order it does not pin.
- Keep the skill's existing clause locations and add a concise behavior statement under its synthesis-time hard-gates rule.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- A fixture with valid prerequisites exercises every applicable failure family from the origin; missing diagnostics and pointers fail before implementation and pass after it.
- The existing hard-mode first error and the resulting `plan_readiness` failure family remain unchanged when routed errors coexist.
- Invalid-record exit and text/JSON verdicts, passing-record verdicts, and soft/preflight behavior remain unchanged.
- The skill note documents the behavior in its existing section without growing operative text overall.

**Quality dimensions:**
- Correctness: report independent defects and exclude prerequisite-caused cascades.
- Compatibility: preserve readiness routing and all existing outcome behavior.
- Usability: point each reported failure to its existing governing clause.

**Done when:** the validator self-test, plan-readiness regression, maintenance pins, and CLI fixture rehearsal pass.

**Ship when:** the plan is implemented, reviewed, and its origin row is dispositioned at landing.

## Review Scope

**Must-fix paths:**
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`
- `scripts/check_maintenance_pins.sh`

**Plan-related extension:** Other findings are in scope only when needed to preserve hard-mode outcomes, first-error routing, or the documented diagnostic order.

**Out of scope:** Moving or restating the skill's existing clause documentation; changing preflight or soft-mode posture; adding a gate, ledger, ceremony, or schema field.

## Validation Commands

```bash
python3 scripts/validate_review_staging.py --selftest
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_plan_readiness.py'
bash scripts/check_maintenance_pins.sh
```

Also run the hard-mode CLI on the regression fixture with multiple origin-listed defects. Confirm each independently applicable diagnostic and clause pointer appears once, cascades stay suppressed, the emitted order keeps the established first error, and exit/text/JSON outcomes match the existing contract. Check one valid record and one report-only invocation.

## Tasks

### Task 1: Make independent hard errors actionable

Files:
- `scripts/validate_review_staging.py`
- `agents/skills/review-staging/SKILL.md`

Primary class anchors:
- `ValidationResult` in `scripts/validate_review_staging.py`
- `validate_staging_file` in `scripts/validate_review_staging.py`

- [x] Given a fixture with valid prerequisites and the origin's listed failure families, expects every applicable diagnostic missing today, with a pointer to its existing review-staging clause. [class: IMPLEMENTATION_REQUIRED]
- [x] Given malformed prerequisite data, expects independent diagnostics to remain visible while dependent cascade messages stay suppressed. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a multiply-invalid sidecar, expects the existing first error used by readiness routing to stay unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the existing synthesis-time hard-gates rule with the output contract; keep clause locations and avoid net operative text growth. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a passing record, soft run, or preflight run, expects the current verdict and output behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `scripts: report actionable review staging failures`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin diagnostics and shared routing

Files:
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `ValidationResult` in `scripts/validate_review_staging.py`
- `_first_gate_error_reason()` in `scripts/plan_readiness.py`

- [x] Embedded self-tests pin the origin-listed diagnostics, clause pointers, stable emission order, and cascade suppression; preserve the existing ten-error case. [class: IMPLEMENTATION_REQUIRED]
- [x] A plan-readiness regression pins the same first-error reason when multiple routed diagnostics coexist. [class: IMPLEMENTATION_REQUIRED]
- [x] Re-derive hard-mode pins; update any one-error assertion with its rationale, and add none when no such assertion exists. [class: IMPLEMENTATION_REQUIRED]
- [x] The CLI fixture rehearsal preserves exit, text/JSON, passing, soft, and preflight outcomes. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `scripts: pin review staging diagnostics and routing`. [class: IMPLEMENTATION_REQUIRED]
