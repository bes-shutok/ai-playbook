# Plan: Semantic naming and analogous types in reviews

Backlog origin: docs/history/backlog/2026-10-15-semantic-naming-and-analogous-class-review.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-21-plan-review-semantic-naming-and-analogous-class-review-r*.md
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-15-semantic-naming-and-analogous-class-review.md (session 01a15484-176a-70a1-814d-785fd68e1975)

## Terms

- **Semantic naming:** names that accurately describe a type's current responsibility and distinguish it from types with different responsibilities.
- **Analogous types:** interfaces, implementations, or related types that serve a meaningfully similar role, supported by their declarations, callers, and contracts.

## Why

The quality catalog asks reviewers to check naming conventions, but a conventional name can still describe an old responsibility or obscure a real counterpart. Focused reviews can also omit the quality lens, so these issues may go unexamined.

## Gist & Examples

TLDR: Extend quality's naming check and the existing focused-panel recommendation for code quality.

**Before:** Two domain-specific services perform the same role but use names that hide their relationship, or a refactored type keeps a name for work it no longer owns; the existing local-convention check may miss both.

**After:** Reviewers compare changed type names with their responsibilities and evidenced counterparts, and a focused panel receives a warning-only recommendation to retain the existing quality lens when the diff changes a type's responsibility in a way that conflicts with its name, or changes, introduces, or renames a type in an evidenced analogous pair when the changed scope exposes inconsistent names for the shared role.

**Edge cases:** Similar names do not justify symmetry when ownership, lifecycle, or contracts differ. Names that have not shipped can be aligned without compatibility baggage; deployed names require evidence and compatibility review before a rename is suggested.

## Outcome

Review guidance identifies stale or misleading type names and meaningful role parallels while keeping naming ownership in the quality lens.

- The quality lens checks current responsibilities and evidence-backed analogous roles.
- Focused panels receive a narrow, warning-only recommendation when the diff changes a type's responsibility in a way that conflicts with its name, or changes, introduces, or renames a type in an evidenced analogous pair when the changed scope exposes inconsistent names for the shared role.
- Distinct responsibilities remain distinct, and no new reviewer or review round is added.

Gate delta: No runtime refusal class, hard gate, fence, protocol layer, schema field, or blocking review-layer duty is added or removed; the existing focused-panel advisory remains warning-only, and no machinery is added.

## Assumptions

- Semantic naming belongs in the quality catalog's existing Naming and Structural Clarity section because that section already owns naming consistency; simplification remains scoped to avoidable structure. Basis: `agents/skills/review-agents/quality.md` and `agents/skills/review-agents/simplification.md`.
- The existing focused-panel recommendation is the home for conditional quality-lens retention. It stays advisory and does not create a new worker or round. Basis: `agents/skills/review-agents/review-panel-selection.md`.
- The callback readability trigger remains intact and separate; semantic naming is an additional changed-code signal for that same advisory. Basis: completed plan `docs/history/plans/completed/2026-10-15-framework-callback-readability-and-review-scope.md`.
- The backlog's sanitized examples are sufficient witnesses; no personal, company, ticket, or class identifiers belong in the plan or guidance.
- Quality and panel-selection edits will pay for any byte growth by condensing or replacing existing prose in the same files. Basis: repository Guidelines, Skill text anti-growth rules.
- The plan's fix-class origin is consistent with its body: it repairs existing review guidance without introducing a new refusal or gate.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Semantic accuracy: names are compared with current declarations, callers, and relevant contracts before a rename is proposed.
- Useful consistency: reviewers identify real role parallels and preserve names where responsibilities differ.
- Review scope: only focused panels with a relevant changed-type signal receive the existing warning-only recommendation.

**Done when:**
- The quality naming guidance covers stale responsibility, analogous roles, evidence needed before a rename, and false symmetry.
- The focused-panel policy extends its existing recommendation to semantic-naming signals without broadening unrelated focused reviews or changing the callback signal.
- The simplification catalog retains its existing structural scope; no duplicate naming duty, new worker, review round, validator, or gate appears.
- Changes are byte-balanced within each edited skill file and the portability, door, and public-hygiene checks pass.

**Ship when:** None. This is repository guidance with local validation.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:** None.

**Documentation:**
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/review-panel-selection.md`

**Tests:** None; this changes review guidance only.

**Plan-related extension:** `agents/skills/review-agents/simplification.md` may change only if a concise ownership pointer is necessary to prevent duplicate semantic-naming findings; preserve its structural checklist.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-agents/review-plan/SKILL.md`; its Growth balance finding class already covers unbalanced operative-text growth.
- The completed callback plan and its artifacts; preserve its existing callback and local-type scope.

## Validation Commands

```bash
python3 scripts/check_review_agent_portability.py
python3 scripts/test_review_agent_doors.py
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh
```

### Task 1: Extend the quality naming check and focused-panel signal

Context surface: the plan's Terms, this task, and the existing warning-only focused-panel recommendation.

Files:
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/review-panel-selection.md`

- [x] Given a changed type whose name reflects a responsibility it no longer has, the quality guidance expects a finding candidate supported by declarations, callers, and relevant contracts before recommending a rename. [class: IMPLEMENTATION_REQUIRED]
- [x] Given analogous interfaces or implementations with the same intended role but divergent names, the quality guidance expects reviewers to identify the meaningful parallel and suggest alignment when evidence supports it. [class: IMPLEMENTATION_REQUIRED]
- [x] Given similarly named types with different ownership, lifecycle, or contracts, the quality guidance expects reviewers to preserve the distinction and avoid symmetry-only renames. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a focused review whose diff changes a type's responsibility in a way that conflicts with its name, or changes, introduces, or renames a type in an evidenced analogous pair when the changed scope exposes inconsistent names for the shared role, the existing panel-selection rule expects a warning-only recommendation to include correctness-completeness, which owns quality; unrelated focused reviews and the existing callback trigger remain unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep semantic naming in the existing quality naming section, leave simplification focused on structural complexity, and balance added bytes by condensing existing prose within each edited file; add no worker, round, validator, gate, or automated naming check. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands and confirm sanitized positive, negative, and pre-deployment examples are represented without external identifiers. [class: REPOSITORY_TEST]
- [x] Commit: `docs: review semantic naming across analogous types` [class: IMPLEMENTATION_REQUIRED]
