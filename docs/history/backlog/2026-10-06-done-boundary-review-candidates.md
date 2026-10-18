# Backlog: done-boundary-evidence-gates Step 1.2b review candidates

- **Filed:** 2026-10-06, from the plan's Task 1 intermediate review
- **Status:** open
- **Cluster:** docs/history/backlog/2026-10-16-worktree-done-boundary-primary-gate-block.md, docs/history/backlog/2026-10-16-done-setup-after-task-edits-foreign-staging-trap.md, docs/history/backlog/2026-10-10-done-lock-live-owner-blocks-plan-closeout.md, docs/history/backlog/2026-10-13-done-landing-commit-lock-span.md, docs/history/backlog/2026-10-12-done-interrupted-manifest-state-classification-certification-residuals.md
- **Workflow:** backlog
- **Priority:** low

Driving force: reliability (the gate's new remedy arm and the audit-note lifecycle ship correct but with under-discriminated tests and unstated rationale; silent drift would reopen the misdirected-staging class the plan closes).

- F1/T-F1: strengthen the held-lock fixture to resolve a run manifest (marker + write_run_manifest_record owned_paths + staged foreign file + held lock) so the arm discriminates the shared-render mutant M3.
- F2/T-F2: fixture for a resolved-but-empty-claims manifest (owned == set(), not None) pinning the None-vs-truthiness key.
- T-F3: assertion for the mixed-arm render (owned-unstaged + unowned-staged: misdirected-write text with the remedy appended); also covers the pre-existing unconsultable-lock rc-2 arm gap.
- F1 correctness: state the note-clearing rationale (the disarm-prevention why) somewhere in the doc-hierarchy lifecycle prose.
- F2 correctness: bring the gate docstring's rc-1 description to parity with the appended adoption remedy.

Task 3 captures (Step 1.2b):
- extend the Step 3.3 verification gate (items 1/7) with the terminal-status check so heartbeat-only address logs refuse one boundary earlier than the Step 3.4 launch validation.
- anchor the informal "review-round contract" phrase to the Step 3.5 counting paragraph (or name it).
- Step 1.4b consumes the Heartbeat final-Pass rule whose new trigger is scoped to Step 3.1; give the rule a boundary-neutral statement or a 1.4b-local restatement.
- add a terminal-status validation at the Step 1.4 per-task done boundary (the same heartbeat-only defect shape is unguarded there).
- add a third Evidence grep pin on a launch-validation fragment (e.g. "worker output is never synthesized") or a ContractContentParityTest probe, so the Step 3.4 rewrite and gate item 2 are pinned.

Phase 3 r1 panel captures (all non-blocking, five lenses, zero blocking):
- testing#task2-obligations-unpinned (medium): the Task 2 gate delta (Step 1.4 item 5, envelope arms, subagent-prompts sentence) carries no durable pin beyond file-level greps; add spans-level pins or a parity probe.
- testing#step31-round-shape-duties-unpinned (low): the Step 3.1 fan-out merge-pass / single-worker verification-duty sentences are pinned by neither grep nor test.
- testing#envelope-completeness-divergence-unchecked (low): agent-logs envelope now exceeds runtime-contract principle 3's acceptance-criteria-only completeness; reconcile principle 3 or narrow the citation.
- docs#batch-launch-obliged-set-contradiction (medium): the batch path lags the obliged-set duty three ways (singular task-local slot; rule 3 forbids the full block; singular envelope field); carve-out needed.
- docs#gate-order-paragraph-omits-adoption-remedy (low): done's gates-run-in-this-order paragraph under-describes the rendered adoption remedy.
- docs#launch-validation-no-pass-block-vacuous (low): "not in_progress" reads vacuously on a Pass-block-less log; tighten to gate item 2's allowlist form.
- docs#adoption-remedy-render-divergence (low, informational): three dictated deltas between the gate's rendered remedy and the Step 0 clause; the "created after Step 0" definite description over-claims for baseline-dirt shapes.
- risk#plain-fresh-boundary-claim-bypasses-adoption-authorization (low): a fresh non-adopting boundary's --owned-path claim is a mechanical route around the adoption authorization; durable invariant holds, the authorization does not bind on that route.
- risk#step34-denylist-admits-malformed-final-status (low): 3.4's "not in_progress" denylist vs 3.1's allowlist on address logs.
- risk#step31-item2-failure-action-unnamed (low): gate item 2 names no failure action.
- correctness#missing-run-deferral-arm-undetermined-at-terms (low): Terms' deferral arm keys only on the exits-non-zero shape.
- design#ip-rows-restating-consumer-duty-text (low), design#plan-terms-vocabulary-dangling-reference (low), design#redundant-restatement-in-changed-spans (low), design#parity-test-name-encodes-superseded-contract (low): duplication/vocabulary/naming slivers.

## Triage verdicts (2026-10-16, plan 2026-10-16-done-emit-prelock-classification execution; one dated verdict per residual, superseded-by witness or kept)

- F1/T-F1 (held-lock fixture resolves a run manifest): KEPT - no held-lock fixture composing marker plus `write_run_manifest_record` plus staged foreign file exists in either suite (probed 2026-10-16).
- F2/T-F2 (resolved-but-empty-claims manifest fixture): KEPT - no empty-claims (`owned == set()` vs None) fixture found (probed 2026-10-16).
- T-F3 (mixed-arm render assertion): SUPERSEDED - the owned-class misdirected-write refusal arm was removed by the closeout-gate demotion program change 7 (`scripts/done_sweep_gates_lib.py` docstring, the rc-1 refusal is staged-residue-only); the surviving warn-order coverage is `test_post_landing_staging_owned_unstaged_warns`.
- F1 correctness (note-clearing rationale in doc-hierarchy prose): KEPT - no note-clearing/disarm rationale found under `agents/skills/doc-hierarchy/` (probed 2026-10-16).
- F2 correctness (gate docstring rc-1 parity with the adoption remedy): SUPERSEDED - program change 7 rewrote the rc-1 docstring description (staged-residue-only after change 7, `scripts/done_sweep_gates_lib.py`), and the mid-session-creation remedy render is commented at its render site (rc-1 message names the adopting-boundary recovery when owned is not None).
- Task 3: extend Step 3.3 gate items 1/7 with terminal-status: KEPT.
- Task 3: anchor the "review-round contract" phrase: KEPT - the phrase still reads unanchored in the Step 3.4 launch-validation sentence (probed 2026-10-16).
- Task 3: 1.4b heartbeat rule boundary-neutral statement: SUPERSEDED - Step 1.4b's paragraph states its own consumption of the Heartbeat final-Pass Status rule in place (agents/skills/execute-plan/SKILL.md, the design-review log append sentence).
- Task 3: terminal-status validation at the Step 1.4 per-task boundary: KEPT.
- Task 3: third Evidence grep pin on a launch-validation fragment: SUPERSEDED - the fragment "worker output is never synthesized" now lives verbatim in the Step 3.4 launch-validation sentence and the launch-validation text carries the reconstruction/refusal arms in full (agents/skills/execute-plan/SKILL.md).
- testing#task2-obligations-unpinned: KEPT.
- testing#step31-round-shape-duties-unpinned: KEPT.
- testing#envelope-completeness-divergence-unchecked: KEPT.
- docs#batch-launch-obliged-set-contradiction: KEPT.
- docs#gate-order-paragraph-omits-adoption-remedy: KEPT.
- docs#launch-validation-no-pass-block-vacuous: KEPT.
- docs#adoption-remedy-render-divergence: KEPT.
- risk#plain-fresh-boundary-claim-bypasses-adoption-authorization: KEPT.
- risk#step34-denylist-admits-malformed-final-status: KEPT.
- risk#step31-item2-failure-action-unnamed: KEPT.
- correctness#missing-run-deferral-arm-undetermined-at-terms: KEPT.
- design#ip-rows-restating-consumer-duty-text: KEPT.
- design#plan-terms-vocabulary-dangling-reference: KEPT.
- design#redundant-restatement-in-changed-spans: KEPT.
- design#parity-test-name-encodes-superseded-contract: KEPT.

Not every residual adjudicates superseded, so the row stays open as the narrow-groups record per the disposition arm; the three done-boundary cluster siblings it points at (worktree-done-boundary-primary-gate-block, done-setup-after-task-edits-foreign-staging-trap, done-landing-commit-lock-span) carry the live facets forward.
