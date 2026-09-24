# Plan: execute-plan fresh-review coverage and boundary-witness enforcement

Backlog origin: `docs/history/backlog/2026-09-08-execute-plan-fresh-review-coverage-gaps.md` (scope of record)
Folded backlog item: `docs/history/backlog/2026-09-08-plans-trunk-branch-confirmation.md` (Task 8; joined by user direction in the authoring task prompt, 2026-09-08: same execute-plan Phase 0 surface, no conflicts with Tasks 1-7)

## Terms

- **fresh-adversarial review**: a review round launched after any accepted fix that independently re-traverses the complete current diff from first principles; prior findings are context, never a filter.
- **risk signal**: a code-mutation signal: a change touching a public API, cross-service call, generated or nullable model, serializer or message converter, or security or rollout boundary. A changed normative documentation example escalates `contract-docs` plus `correctness-completeness` coverage but alone does not trigger the floor (Task 2).
- **Witness ledger**: the staging-doc record of, per changed public mutator and directly affected downstream boundary, the discriminating observation that would fail for the most likely implementation mistake.
- **Release-gate ledger**: the staging-doc handoff record for a boundary explicitly owned by later work: what is missing, who owns it, what is unsafe today, what deployment the current state permits, and what makes it shippable.
- **Skill-gate marker**: consent marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`; recipe in `agents/hooks/skill-gate/README.md`; constants (`SKILL_GATE_WINDOW` default 4h) live there and in `skill_gate.py`.
- **Session key**: the agent-session id supplied to the marker; empty-after-strip becomes the literal `no-session`; otherwise `sha1(value)[:16]` hex; resolved via the shared `session_channel.py` subprocess.

## Assumptions

- assume the product surface is this repo's skills and validator scripts; the "generic workflow regression fixtures" and "harness evaluations" of the backlog item are implemented as `scripts/validate_review_staging.py` selftest canaries plus staged-contract gates; basis: the repo is a skill library and the validator already carries a selftest suite (selftest functions verified on disk).
- assume `review-panel and review-staging guidance` in the backlog scope line resolves to `agents/skills/review-agents/review-panel-selection.md`, `agents/skills/review-agents/documentation.md`, and `agents/skills/review-staging/SKILL.md`; basis: on-disk skill inventory (no `review-panel` directory exists; the contract-docs lens loads the `documentation` lens per `review-panel-selection.md`).
- assume `develop` and every other non-`master`/`main` base keeps its existing confirmation ask in Task 8; basis: the folded backlog item names exactly `master` or `main` for the automatic path.
- assume validator enforcement covers only mechanically decidable properties (metadata presence, enum values, contradiction, section completeness); witness semantic quality (rule 4 below) is an execute-plan orchestrator quality-bar obligation, not a parseable check; basis: the validator parses staging structure, not intent.
- assume the authoring and execution sessions refresh the plans-class skill-gate marker per `agents/hooks/skill-gate/README.md` before every plan-file write, deriving `project` and `session` per the Terms entries above (that recipe is the consumer of both Terms entries).
- assume the new sidecar fields are added to every version-1 producer surface in the same plan: the review-plan inlined required-set copy, the plans SKILL.md prompt-template enumeration, the review-staging minimum-schema example, and the sidecar-writing guidance locations in doing-code-review/review-loop (which today point at the review-staging gold source; update the pointers' surrounding guidance where field semantics are described, and keep them pointers rather than creating new inlined copies); basis: review r1 F2, r4 F1, and r7 F3 folds.

Decision points requiring a grill: none remain.

## Gist & Examples

A post-execution independent review found blocking defects on the same digest execute-plan had already declared clean. The loop treated a post-fix verification pass as closure, its failure-mode matrix accepted test names as evidence, an out-of-scope security boundary vanished from the report, and a normative documentation example was never replayed against the runtime contract.

**Before (today):** after fixes land, the next Step 3.1 may be framed as "verify the fixes"; the staging doc proves workers ran but not that the round re-scanned the whole current diff; a matrix row may cite a test name; a boundary deferred to another task leaves no trace; a strict-mode example with a protected-classified value passes doc review.

**After (this plan):** every post-fix round is labeled `fresh-adversarial` in staging metadata with `Prior findings supplied as filter: no`; the clean round must postdate the last accepted-fix commit; each changed mutator and affected boundary needs a Witness ledger row whose discriminating assertion is named; a deferred boundary stays visible as a Release-gate ledger row carried into the exit report; normative examples are replayed or inventoried against their declared mode; and the staging validator plus selftest canaries refuse the mechanical subset of these failures.

**Example (filtered batch):** a compaction path drops rejected items and must return each surviving item's original input index. Today a row citing `assert items[0].payload == X` counts as covered. After this plan the row must name the discriminating assertion on the returned index, and the staging quality bar (Task 4's prose gate, enforced by the execute-plan orchestrator) rejects the matrix shape that cites only list position for an index invariant.

**Example (deferred boundary):** a plan leaves a downstream protection boundary to a later task. Today the finding is dropped as out of scope. After this plan the staging doc records the missing capability, its owner, the unsafe path, the permitted deployment mode, the shippability condition, and the classification (here: release blocker owned elsewhere), and the exit report carries the ledger.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a round with `Review mode: verification-only`, `Prior findings supplied as filter: yes`, a post-fix round missing the Witness ledger, or an incomplete Release-gate ledger cannot satisfy the Step 3.4 clear-round quality bar; the validator's mechanical subset fails loudly (non-zero exit, named check).
- testing: `scripts/validate_review_staging.py --selftest` covers every new check with both a failing and a passing canary; each new Validation Command obligation is exercised at authoring time and shown to fire on a stripped obligation.
- consistency: each obligation is stated once at its single source (review-staging for staging shape, execute-plan for loop wiring, review-panel-selection for selection, documentation lens for example replay); other skills point at the source instead of restating it.
- hygiene: the changed Markdown must-fix files pass the repo hygiene scan and the no-em-dash scan (the Validation Commands gate exactly those eight files); `scripts/validate_review_staging.py` is excluded from the em-dash scan (23 pre-existing em-dash lines in frozen regions predate this plan) and is instead covered by its selftest suite and the repo hygiene scan; the backlog items remain free of ticket IDs, repository names, service names, internal URLs, and machine-specific paths.

**Done when:**
- All tasks checked; `python3 scripts/validate_review_staging.py --selftest` exits 0; every Validation Command exits 0 on the post-implementation tree.
- The two promoted backlog items still under `docs/history/backlog/` are moved to `docs/history/backlog/completed/` with `Status: done` in the same completion pass as the plan archive (execute-plan Phase 4 lifecycle).

**Ship when:**
- Downstream skill consumers (other repositories running these skills from their registries) pick up the re-synced skill files; not verifiable in this repository, prose only.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-plan/SKILL.md` *(Task 3: inlined version-1 sidecar required-set copy only; all other sections frozen)*
- `agents/skills/doing-code-review/SKILL.md` *(Task 3: sidecar-writing guidance only; all other sections frozen)*
- `agents/skills/review-loop/SKILL.md` *(Task 3: sidecar-writing guidance only; all other sections frozen)*
- `agents/skills/plans/SKILL.md` *(Task 8: Phase 0 Step 0.1 region; Task 3: the inlined sidecar required-set enumeration inside the review-plan sub-agent prompt template; all other sections frozen)*
- `scripts/validate_review_staging.py`

**Tests:**
- `scripts/validate_review_staging.py` selftest functions for the new checks *(edited in place; no separate test file; the script's selftest suite is the repo's test harness for the validator, verified on disk)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. README catalog lines count only if a task's skill change alters a documented behavior summary. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially-in-scope files:** in `agents/skills/plans/SKILL.md` only two regions are open: the Phase 0 branch-setup block (Step 0.1 region) for Task 8 and the inlined sidecar required-set enumeration inside the review-plan sub-agent prompt template for Task 3; all other methods/sections are frozen; reject any review finding that touches them. The same freeze applies to every other must-fix file outside the sections a task names.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: readiness gate consumes the sidecar contract but this plan only extends the produced contract; adjust here only if a sidecar change breaks its parser, which would be plan-related and escalated to must-fix.
- `docs/history/backlog/2026-09-08-plans-grill-answer-required-readiness-gate.md` family and the plans/grilling authoring-readiness items; reason: different skill family (plan authoring, not execution review), deliberately not joined.
- Historical review artifacts under `docs/reviews/`; reason: preserve-and-improve-future-runs rule from the backlog item.

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# Task 1 pins (execute-plan freshness contract)
grep -qF 'Review mode: fresh-adversarial' agents/skills/execute-plan/SKILL.md || fail "T1 fresh-adversarial labeling missing"
grep -qF 'context, not a review filter' agents/skills/execute-plan/SKILL.md || fail "T1 no-filter framing missing"
grep -qF 'ancestor-or-self' agents/skills/execute-plan/SKILL.md || fail "T1 last-fix ordering gate missing"

# Task 2 pins (risk-signal floor, one dedicated grep per file)
grep -qF 'risk-signal floor' agents/skills/review-agents/review-panel-selection.md || fail "T2 floor definition missing"
grep -qF 'risk-signal floor' agents/skills/execute-plan/SKILL.md || fail "T2 Step 3.1 wiring missing"

# Task 3 pins (staging metadata + sidecar + producers)
grep -qF 'Prior findings supplied as filter' agents/skills/review-staging/SKILL.md || fail "T3 filter metadata missing"
grep -qF 'Changed-risk signals' agents/skills/review-staging/SKILL.md || fail "T3 risk-signal metadata missing"
grep -qF 'Last fix commit' agents/skills/review-staging/SKILL.md || fail "T3 last-fix metadata missing"
grep -qF 'EXTENDED_SIDECAR_MIN_DATE' scripts/validate_review_staging.py || fail "T3 grandfathering constant missing"
grep -qF 'review_mode' scripts/validate_review_staging.py || fail "T3 sidecar field missing"
grep -qF 'review_mode' agents/skills/review-plan/SKILL.md || fail "T3 review-plan producer copy missing"
grep -qF 'review_mode' agents/skills/plans/SKILL.md || fail "T3 plans prompt-template producer copy missing"
grep -qF 'verification-only' agents/skills/review-staging/SKILL.md || fail "T3 mode enum missing"

# Task 4 pin (witness ledger section + matrix obligation)
grep -qF '### Witness ledger' agents/skills/review-staging/SKILL.md || fail "T4 witness ledger section missing"
grep -qF 'discriminating assertion' agents/skills/execute-plan/SKILL.md || fail "T4 matrix witness obligation missing"

# Task 5 pins (release-gate ledger + witness empty shape written by Task 5 bullet 2)
grep -qF '## Release-gate ledger' agents/skills/review-staging/SKILL.md || fail "T5 ledger section missing"
grep -qF 'Witness ledger: <populated | N/A (no public mutators)>' agents/skills/review-staging/SKILL.md || fail "T5 witness ledger empty shape missing"
grep -qF 'release blocker owned elsewhere' agents/skills/review-staging/SKILL.md || fail "T5 classification enum missing"
grep -qF 'Release-gate ledger' agents/skills/execute-plan/SKILL.md || fail "T5 exit-report wiring missing"

# Task 6 pins (example replay in the documentation lens; dedicated grep per obligation)
grep -qF 'normative example' agents/skills/review-agents/documentation.md || fail "T6 replay obligation missing"
grep -qF 'example inventory' agents/skills/review-agents/documentation.md || fail "T6 inventory fallback missing"

# Task 7 (selftest canaries; includes new checks by construction)
python3 scripts/validate_review_staging.py --selftest || fail "T7 selftest failed"

# Task 8 pins (trunk auto-branch; dedicated grep per file)
grep -qF 'exactly `master` or `main`' agents/skills/plans/SKILL.md || fail "T8 plans auto-path missing"
grep -qF 'exactly `master` or `main`' agents/skills/execute-plan/SKILL.md || fail "T8 execute-plan auto-path missing"
grep -qF 'does not skip or satisfy the requirements confirmation' agents/skills/plans/SKILL.md || fail "T8 requirements separation missing"

# Forbidden framing must not return (wrap-tolerant flattened sweep per plans authoring rule 19; the plan file itself is excluded from this sweep: its mentions are checker literals, not stale references)
for f in agents/skills/execute-plan/SKILL.md; do
  if tr '\n' ' ' < "$f" | tr -s ' ' | grep -q 'verification-only framing is acceptable'; then fail "T1 forbidden framing reintroduced in $f"; fi
done

# Repo format gates over changed files (em-dash scan scoped to the Markdown must-fix files; scripts/validate_review_staging.py is excluded because 23 pre-existing em-dash lines in frozen regions, first at line ~325, predate this plan and no task touches that region)
bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md agents/skills/review-staging/SKILL.md agents/skills/review-agents/review-panel-selection.md agents/skills/review-agents/documentation.md agents/skills/review-plan/SKILL.md agents/skills/doing-code-review/SKILL.md agents/skills/review-loop/SKILL.md agents/skills/plans/SKILL.md || fail "em-dash scan"
bash scripts/scan-public-hygiene.sh || fail "public hygiene scan"
```

### Task 1: execute-plan fresh-adversarial review contract (backlog A1, A2, A5)

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] In `### Verify-fix vs fresh review (do not conflate)`, add after the pass-type table: every Step 3.1 launched after an accepted fix is labeled in the staging Metadata with the exact line `Review mode: fresh-adversarial`, and its worker prompt must contain the sentence `Prior findings are context, not a review filter; re-derive findings from a first-principles traversal of the complete current diff.`
- [x] In the same section, extend the forbidden-framing paragraph: a verify-fix pass, a unit-only pass, or a verification-only pass never substitutes for the fresh-adversarial round and never satisfies Step 3.4's clean condition.
- [x] In `### Step 3.4: Evaluate the current digest and launch done`, add clear-round quality bar item: the clean round's reviewed head includes the last accepted-fix commit as ancestor-or-self (`git merge-base --is-ancestor <last_fix_commit> <clean-round-head>`; in the canonical loop the post-fix review runs at HEAD equal to the fix commit, which satisfies ancestor-or-self); the manifest records `last_fix_commit` when any address pass accepted fixes, and the orchestrator runs that check before treating the round as clean.
- [x] In the manifest tracking list (Phase 3 preamble), add the `last_fix_commit` counter line.
- [x] Run each Task 1 grep from Validation Commands; expect RED before the edit, GREEN after.
- [x] Commit: `skills: execute-plan fresh-adversarial review contract`

### Task 2: risk-signal-driven worker selection (backlog A3)

Files:
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] In `review-panel-selection.md`, add a `Risk-signal floor` subsection titled with the literal `Risk-signal floor` and referred to in its body as the `risk-signal floor`: signals are the five code-mutation classes from this plan's Terms (public API, cross-service call, generated or nullable model, serializer or message converter, security or rollout boundary); one or more signals require the worker set to include `correctness-completeness`, `testing`, `contract-docs`, and `risk`; two or more signals require the full five-worker panel. Precedence, stated explicitly: when triggered, the floor overrides both the focused-round preference in the late-loop paragraph and the `Focused panels` section. A changed normative documentation example alone (docs-only or docs-plus-scripts diffs with no code-mutation signal) escalates `contract-docs` plus `correctness-completeness` but does not trigger the floor, so docs-only focused panels stay valid; within execute-plan Step 3.1 item 5, doc/skill-only plans keep grep/hygiene commands as the `testing` worker's primary evidence.
- [x] In `execute-plan/SKILL.md` Step 3.1 worker-set resolution, add: derive risk signals from the plan's explicit must-fix paths and the current diff, then apply the `risk-signal floor` from `review-panel-selection.md`; record the detected signals in the staging Metadata `Changed-risk signals` field.
- [x] Run the Task 2 greps; RED before, GREEN after.
- [x] Commit: `skills: risk-signal floor drives Phase 3 worker selection`

### Task 3: staging freshness metadata and sidecar contract (backlog A4)

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-plan/SKILL.md` *(inlined version-1 sidecar required-set copy only)*
- `agents/skills/doing-code-review/SKILL.md` *(sidecar-writing guidance only)*
- `agents/skills/review-loop/SKILL.md` *(sidecar-writing guidance only)*
- `scripts/validate_review_staging.py`

- [x] RED: extend the selftest with failing canaries: (a) staging doc with `Review mode: verification-only` and a clean verdict fails; (b) staging doc with `Prior findings supplied as filter: yes` and a clean verdict fails; (c) sidecar without the new fields fails the version-1 schema.
- [x] In the staged Metadata template, add lines: `Review mode: fresh-adversarial | targeted | verification-only`, `Changed-risk signals: <comma list or none>`, `Prior findings supplied as filter: no`, `Last fix commit: <sha or none>`; state that a clean verdict contradicts `verification-only` mode or filter `yes`.
- [x] In the `### Version-1 sidecar contract`, add the fields `review_mode` (enum), `risk_signals` (list), `prior_findings_filter` (boolean, must be false for a clean verdict), `last_fix_commit` (string or null), and the cross-field rule: a clean verdict with a non-null `last_fix_commit` requires `review_mode: fresh-adversarial` (a `targeted` label on a post-fix clean round bypasses the fresh-adversarial mandate), plus the grandfathering rule: a version-1 record whose `date` field is earlier than the validator constant `EXTENDED_SIDECAR_MIN_DATE` is accepted-legacy and exempt from the four new fields; set the constant to the DAY AFTER the implementing commit's date, so same-day records (this repo lands plans same-day; of the sidecars dated the implementation day on disk at authoring time, none carry the fields) stay exempt and only post-landing records require the fields.
- [x] RED canaries for the grandfathering rule: a record dated before `EXTENDED_SIDECAR_MIN_DATE` without the new fields passes; a record dated ON the implementing date (same-day shape) without the new fields also passes; the same shape dated after `EXTENDED_SIDECAR_MIN_DATE` fails.
- [x] Update the producer copies in the same task so no version-1 producer emits sidecars that fail the extended schema: the inlined required-set copy in `review-plan/SKILL.md` Step 3, the inlined sidecar required-set enumeration in the `plans/SKILL.md` review-plan sub-agent prompt template, the minimum-schema JSON example in `review-staging/SKILL.md`, and any sidecar-writing guidance in `doing-code-review/SKILL.md` and `review-loop/SKILL.md` (grep all four skills for sidecar schema references and update every inlined copy).
- [x] In `scripts/validate_review_staging.py`, implement the checks behind the canaries (mode enum membership, filter-must-not-be-yes on clean verdicts, sidecar field presence with the `EXTENDED_SIDECAR_MIN_DATE` grandfathering exemption) and keep the existing checks green.
- [x] GREEN: all new selftest canaries pass; full selftest exits 0.
- [x] Run the Task 3 greps; RED before, GREEN after.
- [x] Commit: `skills: staging freshness metadata and sidecar v1 fields`

### Task 4: mutator and boundary witness ledger (backlog B)

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] In the staged hierarchy under `## Review Statistics`, add a `### Witness ledger` subsection after `### Triage outcomes`: one row per changed public mutator and each directly affected downstream boundary, each row naming input partitions (absent, explicit-null, valid, invalid, protected, filtered where applicable), any index, identity, or ordering transformation, the actual downstream wire boundary and serializer configuration, downstream success, partial-failure, malformed-response, and no-call behavior, the rollout or compatibility mode and deployed default, normative documentation examples describing the path, and the exact discriminating assertion or structural guard for each claim.
- [x] State in the same subsection: a row citing only a test name, a list position, a status code, or a manually configured fixture fails the quality bar when the invariant at risk is index preservation, wire serialization, downstream response, or mode preservation.
- [x] In `execute-plan/SKILL.md`, extend the `Mutator failure-mode matrix` paragraph to require the matrix rows and the Witness ledger rows to carry the discriminating assertion obligation, and add a Step 3.1 verification gate item: post-fix rounds missing a populated Witness ledger fail the gate.
- [x] Run the Task 4 greps; RED before, GREEN after.
- [x] Commit: `skills: witness ledger with discriminating-assertion requirement`

### Task 5: release-gate ledger for deferred boundaries (backlog C)

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] In the staged hierarchy, add an optional `## Release-gate ledger` section after `## Findings` groups: when a plan explicitly assigns a boundary to later work, record the missing capability and its owner, the current code path and configuration that would be unsafe without it, the deployment mode permitted before completion, the exact condition that makes the future path shippable, and the classification `implementation blocker | release blocker owned elsewhere | non-blocking follow-up`; when no deferred boundary exists, Metadata carries `- Release-gate ledger: none`.
- [x] In the staged Metadata template (Task 3's block), add the empty shape line `Witness ledger: <populated | N/A (no public mutators)>`; a post-fix round fails the gate when it has neither a populated `### Witness ledger` nor the N/A line, mirroring the matrix's `N/A: no mutating APIs in this plan` and the ledger's `none` line. The enforcing validator check and its canaries land in Task 7; this task prescribes only the staged-contract text.
- [x] In `execute-plan/SKILL.md`, wire the ledger into Step 3.4's clear-round quality bar (incomplete ledger is not clean) and require the exit report and any user-facing completion summary to carry every `release blocker owned elsewhere` row verbatim; the ledger is a handoff artifact, never authorization to expand the plan.
- [x] Run the Task 5 greps; RED before, GREEN after.
- [x] Commit: `skills: release-gate ledger keeps deferred boundaries visible`

### Task 6: normative example replay in the documentation lens (backlog D)

Files:
- `agents/skills/review-agents/documentation.md`

- [x] Add a `Normative example replay` subsection to the documentation lens: for every changed normative example in the diff, either validate it against the active schema, classifier, or mode rules it documents, or build a structured `example inventory` recording the declared mode, required headers, protected fields, and expected result class; an example that conflicts with its declared mode or field classification is a finding even when anchors and prose are correct.
- [x] State the boundary: where full execution is impractical in the review context, the inventory satisfies the obligation; a successful documentation review must prove examples are not merely syntactically valid.
- [x] Run the Task 6 greps; RED before, GREEN after.
- [x] Commit: `skills: documentation lens replays normative examples`

### Task 7: incident-shape canaries in the validator selftest (backlog E)

Files:
- `scripts/validate_review_staging.py`

- [x] Add selftest canaries completing the six incident shapes mechanically decidable by the validator: (1) fresh-adversarial round with all ledgers and `filter: no` passes; (2) post-fix round (non-null `last_fix_commit`) with neither a populated Witness ledger nor the `Witness ledger: <populated | N/A (no public mutators)>` empty shape fails; (3) clean verdict with `prior_findings_filter: true` fails; (4) clean verdict with `review_mode: verification-only` fails; (4b) clean verdict with non-null `last_fix_commit` and `review_mode: targeted` fails; (5) `## Release-gate ledger` with a missing classification field fails; (6) sidecar missing `risk_signals` fails the version-1 schema.
- [x] In `scripts/validate_review_staging.py`, implement the checks behind canaries (2)-(6) in this task (witness-ledger presence and empty shape, filter scoping, mode enum, the fresh-adversarial requirement on post-fix clean verdicts, release-gate field completeness, sidecar schema fields); each failing canary asserts the validator's named check id in the failure output, not just a non-zero exit. Canaries (3), (4), and (6) deliberately re-pin Task 3's RED canaries (b), (a), and (c) inside the complete six-shape suite; keep both so the exit suite pins them even if Task 3's interim canaries are later reorganized.
- [x] Shapes that are workflow obligations rather than parseable structure (sibling-defect re-scan, test-name-only matrix row) are enforced by the Task 1 and Task 4 prose gates; record that mapping in a one-line selftest comment so the incident coverage is traceable.
- [x] Run `python3 scripts/validate_review_staging.py --selftest`; expect GREEN with all new canaries.
- [x] Commit: `validator: incident-shape canaries for freshness and ledgers`

### Task 8: trunk auto-branch fail-closed path (folded backlog item)

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] In `plans/SKILL.md` Phase 0 before Step 0.1's ask, insert the automatic path: when the current branch is exactly `master` or `main`, both `git status --porcelain` and `git status --porcelain --ignored` are empty (ignored user content keeps the confirmation, per the folded backlog item), the proposed branch name is derived from the requested task or plan slug, and the destination branch does not already exist, create and verify the local feature branch without asking for branch confirmation; every other case (detached HEAD, dirty tracked content, non-empty ignored content, non-trunk base, ambiguous target, existing destination, any history rewrite) keeps the explicit confirmation; the automatic path does not skip or satisfy the requirements confirmation.
- [x] In `execute-plan/SKILL.md` Step 0.1c, insert the same guard, preserving the literal condition that the current branch is exactly `master` or `main`, so a clean trunk proceeds to branch creation without the redundant ask; `develop` and every other non-`master`/`main` default keeps the existing ask; push authorization is unchanged.
- [x] Add the mechanically testable truth table as a short fenced list beside the auto-path (nine positive/negative rows: clean master, clean main, dirty tracked trunk, untracked content on trunk, non-empty ignored content on trunk, non-trunk base, detached HEAD, existing destination, ambiguous target or history-rewriting operation).
- [x] Run the Task 8 greps; RED before, GREEN after.
- [x] Commit: `skills: fail-closed auto-branch from clean trunk`

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-07-plan-review-scope-path-category-validation.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-08-execute-plan-fresh-review-coverage-gaps.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-10-jvm-review-coverage-plan-residual-probe-friction.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-14-execute-plan-parallel-review-address-workers.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-14-review-runner-coverage-plan-residuals.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-review-staging-coverage-attempt-shadowing.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-review-validator-coverage-attempts-shadowing.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-17-execute-plan-bound-review-loop-and-plan-freeze.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-18-execute-plan-residual-acceptance-exit-for-review-loops.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-01-execute-plan-five-review-cap-vs-focused-churn.md: disposition folded into 2026-09-08-execute-plan-fresh-review-coverage-gaps.md (2026-09-25); per-item file deleted.
