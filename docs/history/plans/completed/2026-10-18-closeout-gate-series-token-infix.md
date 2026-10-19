# Plan: closeout-gate series-token infix support

Backlog origin: docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md
Driving force: code-quality
Authoring claim: docs/tmp/authoring-claims/2026-10-16-review-series-token-citation-gate-gap.md (session 01a1501c-2267-70b3-9423-7dd6ba3e4dd8)
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-closeout-gate-series-token-infix-p1abf2828-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.0h total, largest task 1.5h

## Terms

- identity token: the canonical `-p` followed by eight lowercase hexadecimal characters derived from a repository-relative source-plan path and included in plan-review record basenames.
- source-plan identity: the repository-relative path of the plan whose review records the closeout gate checks; a temporary copy of completed plan bytes keeps the identity of the original plan path.
- series citation: the path pattern in a plan's `Plan review record:` header that closeout migration expands to review records.
- token infix: the optional identity-token segment between the artifact slug and the `-r<N>` round segment in a plan-review record basename.
- tokenless citation: a series citation without a token infix; selection follows the existing slug and date rules, while a read-only diagnostic reports whether each record identity resolves to the source plan.

## Why

The selector emits plan-review files with a path-derived token infix, but the closeout parser treats a tokenless citation prefix literally and misses those files. Matching every same-slug token can let another plan's reviews satisfy the citation. Repair the parser and report identity mismatches without adding a new blocking refusal before the machinery policy admits promotion.

## Gist & Examples

TLDR: recognize tokened review-series names and report identity mismatches without filtering - code-quality, the closeout gate should expose which plan each record names.

Before: given a plan cites `...-example-r*.md` and its review is named `...-example-p1a2b3c4-r1.md`, expects the closeout parser to miss the record; accepting every token with that slug can count another plan's record.

After: given a tokenless citation and a same-slug foreign record, expects the parser to recognize the tokened filename and warn that the record names another plan, while current selection and closeout results remain unchanged, including through the completed-plan twin's temporary file.

Edge cases: explicit tokens match the citation token exactly; body or fenced `URL or Artifact` text is not identity; malformed token-like text stays literal; concrete dates stay exact; placeholders, wildcard prefixes, suffixes, round ordering, containment, legacy Metadata diagnostics, and zero-member refusal keep their stated behavior. A foreign-only tokenless series may still satisfy current closeout selection; preventing that requires a later blocking filter admitted under the machinery promotion rule.

## Outcome

The closeout matcher recognizes tokened review records and emits a read-only warning when their recorded identity does not resolve to the source plan. A foreign record can still satisfy the current closeout or verification selection; identity filtering is deferred until the machinery promotion rule is met.

- `gate-removal`, `verify-records`, and the completed-plan twin recognize tokened records; identity diagnostics report foreign or unresolved records without filtering members or changing results.
- Tokenless citations retain current selection behavior; actual Metadata identity is reported, and identity text in body or fenced content never binds a record.
- The plans template and matcher docstring describe the optional token infix and warning-only identity diagnostic.

Gate delta: repair the existing matcher false zero-member refusal for canonical tokened records and add one read-only source-identity diagnostic; the diagnostic cannot filter selected members, change exit status, or pause dispatch. Incident: r5 staged same-slug collision finding ([review record](.ai-playbook/reviews/2026-10-18-plan-review-closeout-gate-series-token-infix-p1abf2828-r5.md)) and the origin's four valid-series refusals. Expected diagnostic frequency: only when a selected tokenless same-slug record has foreign or unresolved identity (current corpus measurement: 3 mixed legacy/token groups among 642 slug/date groups, all same identity, 0 foreign collisions). False-positive cost: one warning line for an intentional slug reuse or unresolved legacy record; no behavior or lane effect. Review date: 2027-01-18. Gate-liveness ratio: 27:38 per `scripts/gate_liveness_ledger.py show`. No blocking machinery is added or removed; any future identity filter requires a re-derivable runtime true catch and a pre-registered machinery-removal row naming sunset and promotion criteria. The origin records why the proposed `--claims`, per-run symlink, and mandatory-token alternatives do not repair the parser false refusal or preserve current compatibility.

## Assumptions

- `_series_members` remains the shared expansion point for `gate-removal` and `verify-records`; basis: its current call sites in `scripts/worktree_closeout_migrate.py`.
- The selector derives the canonical token from the source-plan path and records that identity in `extensions.plan_identity`; basis: `scripts/review_record_selection.py`.
- Legacy Markdown identity is the `URL or Artifact` entry in the actual Metadata section; basis: `agents/skills/review-staging/SKILL.md` and the current record shape.
- The completed-twin sweep passes the original path separately from its temporary `--plan` file and the source plan record remains accepted; basis: `_run_gate_on_twin` in `scripts/worktree_closeout_migrate.py`.
- The r5 cross-binding finding and the diagnostic-only decision are recorded in `.ai-playbook/reviews/2026-10-18-reconciliation-closeout-gate-series-token-infix.md`, `.ai-playbook/reviews/2026-10-18-reconciliation-closeout-gate-series-token-infix-r6.md`, and `.ai-playbook/reviews/2026-10-18-reconciliation-closeout-gate-series-token-infix-r7.md`.

Decision points requiring a grill: none remain; machinery admission requires warning-only behavior until a true catch and pre-registered removal row exist.

## Standing constraints

- Preserve date-prefix normalization, round ordering, suffix handling, `resolved_only` containment, and zero-member refusal.
- Keep `gate-removal` and `verify-records` on the shared `_series_members` implementation.
- Do not infer identity from body/fenced text. The warning-only diagnostic never changes the accepted set; a future blocking filter requires the machinery promotion evidence.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both citation forms recognize tokened records, the diagnostic reports foreign or unresolved identity, and the completed-twin sweep preserves the source plan record while current selection remains unchanged.
- compatibility: tokenless legacy records continue to work when their actual Metadata identity resolves to the plan.
- safety: identity diagnostics do not alter selection or consumer outcomes; foreign-only series may still satisfy current consumers and are an explicit deferred risk; explicit-token grammar remains exact; body/fenced identity text is ignored.
- simplicity: one shared matcher uses the existing identity helper without a second claims-file gate.

**Done when:** regression coverage proves token-infix recognition and read-only identity diagnostics for direct `gate-removal`, `verify-records`, and the completed-twin sweep; the completed twin accepts its own matching record and reports a foreign-only series without changing the existing result; explicit tokens are exact; legacy Metadata resolves while body/fenced text does not; existing date, suffix, containment, malformed-token, ordering, and zero-member controls remain intact. The plans template and matcher docstring state the same grammar and diagnostic limits. The origin rationale is updated, then its completed row is deleted with surviving Cluster pointers tidied in the landing change.

**Ship when:** the existing matcher, its regression coverage, the template update, the origin disposition, and this plan's prompt-prune receipt land together; no external release condition remains.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- `scripts/worktree_closeout_migrate.py`
- `scripts/review_plan_identity.py`

**Tests:**
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/test_review_record_selection.py`

**Documentation:**
- `agents/skills/plans/SKILL.md`
**Backlog disposition:**
- `docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md` *(admission alternatives are part of this origin's fix-class record; deleted in the landing change)*
- `docs/history/backlog/PLAN-PROMPTS.md` *(landing prune rider, its own entry only)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it implements a task, fixes a regression caused by plan work, closes wiring or docs implied by a must-fix change, or contradicts a contract this plan changes. If the link to the plan is weak or speculative, drop it as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: its review-record discovery is a separate consumer and is not required to expand citations during closeout or verify-records.

## Validation Commands

Run from the repository root:

- `python3 scripts/test_worktree_closeout_migrate.py`
- `python3 scripts/test_review_record_selection.py`
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-18-closeout-gate-series-token-infix.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `bash scripts/check-no-em-dash.sh touched`

### Task 1: recognize series tokens and diagnose source-plan identity

- [x] `_series_members` emits a read-only identity diagnostic: given same-slug tokened or legacy records for the source plan, another plan, or no plan, expects foreign or unresolved identity to be reported from `extensions.plan_identity` or actual Metadata `URL or Artifact`; the diagnostic does not filter members, alter consumer results, or affect exit status. [class: IMPLEMENTATION_REQUIRED]
- [x] `_series_members` preserves explicit-token grammar and diagnoses identity separately: given a citation with token `T`, expects the token to match exactly; a different valid token does not match and malformed token-like text remains literal; identity mismatch only emits a warning and never filters a member or changes a result. [class: IMPLEMENTATION_REQUIRED]
- [x] The completed-twin sweep preserves diagnostic identity: given completed plan bytes cited through `_run_gate_on_twin`'s temporary file, expects it to pass the original repository-relative path under `{plans_dir}` separately from the temporary `--plan` path, accept the plan's own matching record, and warn for foreign or unresolved records without changing selection. [class: IMPLEMENTATION_REQUIRED]
- [x] Consumer outcomes prove diagnostic-only behavior: given a foreign-only same-slug series, expects both consumers to emit the identity warning while retaining their pre-change selection and result, including the existing possibility of acceptance; given a source record and a higher-round foreign record, expects the diagnostic to identify the foreign member without changing `verify-records` selection. [class: IMPLEMENTATION_REQUIRED]
- [x] Legacy identity parsing is section-scoped: given a matching `URL or Artifact` line in the actual Metadata section, expects it to resolve; given the same line only in body or fenced content, expects no identity. Date-prefix normalization, round ordering, suffix handling, resolved-only containment, and zero-member refusal remain unchanged. [class: IMPLEMENTATION_REQUIRED]

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/review_plan_identity.py`
- `scripts/test_worktree_closeout_migrate.py`
- `scripts/test_review_record_selection.py`

Primary class anchors:
- `_series_members` in `scripts/worktree_closeout_migrate.py`
- `markdown_identity` in `scripts/review_plan_identity.py`

### Task 2: align the plans template and matcher description

- [x] The Plan review record template describes the optional canonical identity-token infix, explains that identity is reported by a read-only diagnostic and does not filter either citation form, and preserves tokenless legacy compatibility. [class: IMPLEMENTATION_REQUIRED]
- [x] The `_series_members` docstring describes the optional token infix, actual Metadata identity diagnostics, and the diagnostic's no-filter behavior as the template. [class: IMPLEMENTATION_REQUIRED]

Files:
- `agents/skills/plans/SKILL.md`
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `_series_members` in `scripts/worktree_closeout_migrate.py`


### Task 3: update and dispose the backlog origin

- [x] Update the origin rationale to record that identity filtering is deferred until machinery promotion evidence exists; retain the parser false-refusal witnesses and summarize why `--claims`, a per-run symlink, and a mandatory-token gate do not repair the parser defect compatibly. Delete the completed backlog row in the same landing change and tidy every surviving `Cluster:` pointer to it. [class: IMPLEMENTATION_REQUIRED]
- [x] At landing, prune only this plan's frozen dispatch entry from `docs/history/backlog/PLAN-PROMPTS.md` and print one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt; leave peer entries untouched. [class: IMPLEMENTATION_REQUIRED]

Files:
- `docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md`
- `docs/history/backlog/PLAN-PROMPTS.md`

Primary class anchors:
- `## Fix shape` in `docs/history/backlog/2026-10-16-review-series-token-citation-gate-gap.md`
