Tracked rolling log of ready-to-dispatch ad-hoc work entries, most urgent first, fed by investigate's work-type verdict and consumed by exec-mode sessions. This log is the exec-mode sibling of `docs/history/backlog/PLAN-PROMPTS.md`: its entries follow that file's Entry template unchanged, and its standing rules apply here by their established labels, with only the deltas stated below.

Standing rules (by their labels in `docs/history/backlog/PLAN-PROMPTS.md`, each applied as written there):

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written (the `Order` rule in `docs/history/backlog/PLAN-PROMPTS.md`).
- Prune rule: as the `Prune rule` in `docs/history/backlog/PLAN-PROMPTS.md`, with this log's delta: the prune witness is the ad-hoc landing commit, printed as one `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt line per removed entry (no plans-root file exists for an ad-hoc landing, so the landing commit substitutes for the plans-root witness; the extended prune audit accepts this witness class).
- Freeze rule: as the `Freeze rule` in `docs/history/backlog/PLAN-PROMPTS.md`, with this log's delta: the freeze trigger is an ad-hoc run claim (an exec-mode session claiming the entry for an ad-hoc run marks it `Frozen:` before the run starts, conditional on the entry still reading unfrozen at write time); the mark clears when the run's landing is stood down with a recorded reason or the run aborts without a landing commit (the entry reopens for dispatch).
- Not a backlog item: never cite this file as a plan's `Backlog origin` (the `Not a backlog item` rule in `docs/history/backlog/PLAN-PROMPTS.md`).
- Entries dispatch to exec-mode sessions: the top ready entry is an ad-hoc run's context source per `agents/skills/maintenance/SKILL.md` (the Exec-mode selection rule and the Rolling prompt log duties' EXEC-PROMPTS dispatch leg); the write turn never executes or dispatches its payload.
- Writes follow the targeted-edit drift-retry rules and the same-turn commit duty per `agents/skills/maintenance/SKILL.md` (re-read and compare before every write; targeted section edits; commit in the same turn; repo-relative-only entries carrying no personal or machine-specific data).

## learn-commit-own-edit-check-mechanical-shape

Added: 2026-10-20, investigate pass anchored on the learn-commit clobber row filed from the 06:35 scheduled exec run; re-witnessed and widened 2026-10-20 by the 11:00 scheduler turn session's learn pass (the row's second witness, investigate entry commit 563d2e2e)

Work-type verdict: ad-hoc-able because every arm is a sentence in a tracked skill-text surface named in the origin row (`agents/skills/learn/step-1-extract.md`, the Step 1.8 commit rule, and `agents/skills/investigate/SKILL.md`, the Stage 4 write bullet), the fix is body-named with no open design choice, no guard-bearing path, state schema, dependency, or machinery is touched, and the pins suite script itself stays unchanged (the report-only arm only tells the run when to execute it and report).

Origins:
- docs/history/backlog/2026-10-20-learn-commit-foreign-reversal-hunk-pins-latency.md

Urgency: high - every learn, investigate, and backlog commit on the base branch runs the same explicit-path staging while peers land; the witnessed clobber reverted operative maintenance text on main and the pin stood red for about a day, the same day's second witness resurrected a just-pruned dispatch entry for about twenty hours, and the same shape recurs whenever a run holds a file read from before a peer landing.

Scope arms:
- Mechanical shape for the own-edit check: in the Step 1.8 commit rule, replace the judgment sentence's bare "verify the working-tree delta for that path is this session's own edit" with the probe it means: word-diff each staged non-backlog path against HEAD; a hunk that only removes text, a pure-addition hunk the session did not write, or a path whose last landing (`git log -1 --format=%cd -- <path>`) is newer than the session's read of it, is foreign and the path is skipped and reported; cite lesson 134 in at most one line.
- The same sentence in the investigate Stage 4 write bullet: the same-turn entry commit runs the identical own-edit check before `git commit` (the bullet today carries the write-time re-read rule only, so a stale-read resurrection reaches the commit unexamined); one sentence inside the existing bullet, no new field.
- Report-only pins run on pinned surfaces: in the same rule, when a staged path sits under `agents/skills/maintenance/`, run `bash scripts/check_maintenance_pins.sh` before the commit and print its result in the run output; a failure is reported, never a block, and the commit still proceeds only with the session's own hunks.
- Anti-growth: every arm is a sentence inside the existing Commit rule paragraph or Stage 4 bullet, no new section or field; pay with equivalent deletion in the same paragraph if a file grows past its cap once the byte-budget gate lands, otherwise apply the discipline at review.

Orientation: the clobber mechanism is established in lesson 134 (`docs/maintenance/development_lessons.md`) and the origin row: the learn commit's direct parent was the exec landing that added the sentence, the hunk was a pure deletion, and the commit subject never named the file. Lesson 6 already names the same signature for squash landings, and the ad-hoc arm's suite-failure clause (`agents/skills/maintenance/decisions.md`) is what eventually reconciled the red pin; this entry closes the direct-commit side so the detection does not depend on an unrelated later run. Second witness (the row's Second witness line): the investigate entry commit 563d2e2e re-added a dispatch entry that a peer's direct commit 0c6a66f3f had pruned seventeen seconds earlier, as a pure-addition hunk inside the commit's own declared rolling log; neither the pure-deletion signature nor the declared-path test fires on that shape, only the path-age test does, and the investigate skill's commit carries no own-edit check at all (lesson 134's addition-direction arm).

Prompt: Edit the Step 1.8 Commit rule paragraph in agents/skills/learn/step-1-extract.md: (1) give the own-edit check its mechanical shape (word-diff each staged non-backlog path against HEAD; a pure-deletion hunk, a pure-addition hunk the session did not write, or a path whose last landing date is newer than the session's read of it, is foreign: skip the path and report it; one-line lesson 134 citation); (2) add the report-only pins run for staged paths under agents/skills/maintenance/ (run bash scripts/check_maintenance_pins.sh before the commit, print the result, never block). (3) Add the same one-sentence own-edit check to the Stage 4 write bullet in agents/skills/investigate/SKILL.md, placed before its same-turn entry commit and citing lesson 134 in the same line. Keep every arm inside the existing paragraph or bullet with no new heading or field. Verify the learn router (agents/skills/learn/SKILL.md) still describes the module correctly, run the hygiene scan and the em-dash check, and run the doing-code-review panel over the branch delta per the ad-hoc arm; delete the origin row per the covered-row rule in the landing commit.

Rejected alternatives:
- Repository-wide git pre-commit hook running the pins suite: rejected because the squash landing path composes `commit-tree` plus `update-ref` and never runs hooks, and hooks install per agent rather than per repository (see scripts/land_squash.sh and docs/history/backlog/2026-10-20-ignored-audit-home-paths-force-tracked.md, Rejected)
- A blocking pins gate on learn commits: rejected because one witnessed incident does not admit a new blocking gate under the repository guidelines' Machinery admission protocol (see AGENTS.md, Machinery admission protocol; the report-only arm is the sanctioned first landing)
- Run the pins suite on every learn commit regardless of staged paths: rejected because the suite pins maintenance surfaces only, so commits outside `agents/skills/maintenance/` cannot break a pin and would pay the suite's cost for nothing (see scripts/check_maintenance_pins.sh)
- Leave lesson 134 as the only fix: rejected because the lesson is recall material while the Step 1.8 Commit rule is the text that drives the staging decision, and the witnessed run passed that rule's judgment sentence by assumption (see agents/skills/learn/step-1-extract.md, Step 1.8 Commit rule, and docs/maintenance/development_lessons.md lesson 134)
- A separate entry for the investigate skill's commit: rejected because the mechanism, the fix sentence, and the lesson are identical across both skills, so one landing covers both and a second entry would only split the same dispatch (see docs/history/backlog/2026-10-20-learn-commit-foreign-reversal-hunk-pins-latency.md, Second witness, and docs/maintenance/development_lessons.md lesson 134)

Standing pre-authorization: every arm, uncontested on evidence (the origin row and lesson 134 record both witnesses from disk; no operator or peer correction argues against any arm).

Machinery admission (report-only pins run): incident ce3a984b8 clobbering the Verify-successor sentence 19866b067 added, repaired by a42e0e1d4 (see docs/history/backlog/2026-10-20-learn-commit-foreign-reversal-hunk-pins-latency.md); expected catch frequency low (one witnessed in the corpus's history); false-positive cost a few seconds of suite runtime per learn or investigate commit that stages a maintenance path; review date 2027-01-20, retire if no second catch. The own-edit sentences add no machinery.

## memory-index-compress-and-index-pass

Added: 2026-10-17, investigate pass over the memory-index-audit lane's first filing

Work-type verdict: ad-hoc-able because the parent machinery plan pre-scoped this exact remediation as a one-time operator-rescoped ad-hoc pass over a single untracked surface (the memory store), with no gate, validator, or repo-tracked path touched (the parent plan's Terms define the compress-and-index remediation as outside any plan, the audit only filing the request).

Origins:
- docs/history/backlog/2026-10-17-memory-index-over-budget-compress-and-index.md

Urgency: high - the over-budget index truncates in every session of this project (the load warning is witnessed at each session start), so do-not-redo markers are absent from context and the redo risk is live on every lane until the pass runs.

Scope arms:
- Re-measure before acting: the pass re-derives the index's current line and byte count and the topic-store census at run time (the investigator's fresh re-derivation already moved the row's snapshot: 2891 lines / 97085 bytes at the 2026-10-17 investigation versus the row's 2877/93294 filing numbers), never trusting the row's or the lane state's stale values.
- Compress-and-index per the parent plan's named remediation: fold or retire conversation-scoped lane-state records (landing receipts, fire schedules, checkpoint notes whose outcomes are recorded in the repository's scheduler state file and git history) after a reviewed per-record disposition; index the durable remainder in the one-line append-first shape; classification in doubt resolves to index, never delete.
- Repair dangling pointers beside their provenance: the row names six dangling targets; re-derive each at run time (targets move as peers land), repairing or clearing each beside the record that cites it.
- Run only in a lane-quiet window: no live authoring or execution claims and no in-flight worktree closeouts, because peer closeouts write the index concurrently (three same-day write conflicts witnessed at the parent plan's authoring).

Orientation: the 2026-10-08 parent machinery plan (docs/history/plans/completed/2026-10-08-memory-index-consolidation.md) landed the audit lane, the append-first convention, and the load-budget vocabulary, and deliberately left the one-time consolidation outside itself for the operator to rescope; this row is that designed discharge, not a duplicate of the parent work. The lane state record the row cites at the maintenance home was absent from disk at investigation time, so the entry's numbers come from fresh filesystem re-derivation, and the pass must not depend on that record existing.

Prompt: Run the memory-index compress-and-index consolidation per the origin row and the parent plan's Terms: read the origin row and docs/history/plans/completed/2026-10-08-memory-index-consolidation.md first; verify the lane-quiet window (no live authoring or execution claims, no in-flight worktree closeouts) before any write; re-measure the index and store fresh; classify records into durable (keep and index one-line) versus conversation-scoped lane-state (fold or retire after a reviewed per-record disposition), with the index-rather-than-prune tie-break; repair the dangling pointers beside their provenance; respect the maintenance-side append-first memory-write convention for every entry you add; never bulk-delete by age. Report the before/after line and byte counts, the per-class record counts, and every retired record's disposition witness. The pass never touches repository-tracked files except possibly a closing note on the origin row.

Rejected alternatives:
- Keep everything and only repair the dangling pointers: rejected by the audit's own arithmetic - the index stays roughly fourteen times over the load budget and the truncation and its redo risk persist (see docs/history/backlog/2026-10-17-memory-index-over-budget-compress-and-index.md, Suggested fix option 2)
- Mechanical auto-prune by age: rejected because bulk deletion risks live do-not-redo markers the lanes still depend on and the audit procedure forbids it (see docs/history/backlog/2026-10-17-memory-index-over-budget-compress-and-index.md, Suggested fix option 3)
- Author a plan for the consolidation instead of the ad-hoc pass: rejected because the parent machinery plan deliberately scoped this remediation as a one-time operator-rescoped ad-hoc pass and left it outside any plan (see docs/history/plans/completed/2026-10-08-memory-index-consolidation.md, Terms, compress-and-index remediation)
- Widen the load budget or split the index so truncation stops: rejected because the budget is the host runtime's bound with no repository-side control, and splitting multiplies the write-conflict surface the parent plan already witnessed (see agents/skills/maintenance/SKILL.md, maintenance-side memory-write convention and the parent plan's lane-quiet-window term)

Standing pre-authorization: none - the row explicitly requires the operator's recorded rescope before the pass runs.

Machinery admission: not required - the recommendation consolidates and shrinks an untracked store and adds no gate, validator, lock, ledger, ledger row, or required ceremony.

EXEC-PROMPTS-PRUNE: stranded-execution-claims-release-enforcement -> 5865a50a5 (ad-hoc reviewed landing; the sweep arm landed in scripts/execution_claim.sh with the landing-tail wiring; one blocking review fold, focused re-review clean; Ad-hoc-panel-pass digest 1e58c434e5c29fda)
EXEC-PROMPTS-PRUNE: parked-done-target-state-v9-polish-landing -> supersession cleanup (this commit): the v9 fold (tip 1ef081c27, plan-text readiness byte-limit splits only) is superseded by the executed r7-certified landing 2f8e017d5 whose archived plan the fold's readiness purpose no longer serves; parked branch wt-done-target-state-closeout-authoring deleted in the same run

EXEC-PROMPTS-PRUNE: review-selector-refusal-naming-and-family-scoping -> landing in this commit (panel over the branch delta, verdict PASS with two folds landed; both origin rows deleted per the covered-row rule; residuals noted: legacy prefix-form corpora strand silently by design, and agents/skills/review-staging/SKILL.md line 736 still documents the prefix glob shape)
EXEC-PROMPTS-PRUNE: closeout-citation-template-form-empty-stem -> landing in this commit (panel over the branch delta, verdict PASS with six non-blocking findings, two folded: assertion pins the named citation span, dead test scaffolding removed; residuals: tokenizer widening can merge no-whitespace bracket-abutting exact tokens fail-closed, gate-side bare-fragment refusal lacks a dedicated test, module docstring nuance)
EXEC-PROMPTS-PRUNE: plans-authoring-checklist-byte-measure-at-draft -> landing in this commit (panel over the branch delta, verdict PASS zero blocking; one duty sentence in the plans skill Writing paragraph, cap derivation pinned to scripts/plan_readiness.py)
EXEC-PROMPTS-PRUNE: review-staging-branch-review-path-glob-drift -> landing in this commit (panel over the branch delta, verdict PASS zero blocking; doing-code-review record-path row synced to the family-scoped suffix form with the legacy prefix glob named as no longer matching new allocations)

EXEC-PROMPTS-PRUNE: fold-commit-staged-record-precondition -> landing in this commit (ad-hoc reviewed landing; panel over the branch delta PASS zero blocking; fold-time staged-record duty line in the review-loop fix-and-fold batch step + Integration Points reconciliation; origin row deleted per the covered-row rule, the landing the witness)

EXEC-PROMPTS-PRUNE: reviews-home-migration-collision-loudness -> landing in this commit (ad-hoc reviewed landing; panel over the branch delta, verdict PASS after one blocking fold - dangling-destination-symlink digest read made OSError-tolerant; origin row deleted per the covered-row rule; standing residual: a collision rename that fails copy verification reports via stderr ERROR, not a COLLISION line)

## execute-plan-phase3-initial-pass-panel-selection-reference

Added: 2026-10-20, investigate pass anchored on the Phase 3 cost row filed after the done-immediate-commit-single-homing closeout

Work-type verdict: ad-hoc-able - a body-named single-surface skill-text fix in `agents/skills/execute-plan/SKILL.md` (Step 3.1 item 2), a tracked skill surface with no guard change, no new dependency, no state-schema change (the Ad-hoc backlog arm's eligibility test, `agents/skills/maintenance/decisions.md`); the panel-selection document is not edited, only referenced.

Origins:
- docs/history/backlog/2026-10-20-execute-plan-phase3-initial-pass-ignores-focused-panel.md

Urgency: medium - every execution run pays the cost on its Phase 3 initial pass; the 2026-10-20 witness spent about 2.6 million sub-agent tokens on five lenses over a 12-line delta whose intermediate review was Tier L, while the same-day sibling run read the same text as permitting four lenses.

Scope arms:
- Replace the inline composition sentence in Step 3.1 item 2 ("Initial pass: fresh adversarial five-worker review ...") with a reference: the initial pass composes per `agents/skills/review-agents/review-panel-selection.md` (the default five-worker panel unless its Focused panels arm applies; a run whose every task resolved to Tier L with no cumulative risk signal is the focused docs-only or test-only case, recorded with `panel_mode: focused` and a selection reason); the fresh-adversarial framing and the gate's item 7 stay unchanged.
- Pay growth with deletion: the reference is shorter than the sentence it replaces.

Orientation: the five-worker sentence and the Focused panels allowance were born in the same commit (760e5d812, 2026-07-27) as default and exception; the per-task tier table was added later for Step 1.2b only, so the Tier L signal a run derives never carries into Phase 3, and the execute-plan sentence is the only panel-composition prose outside the document that declares itself the single source.

Prompt: In an ad-hoc worktree, edit `agents/skills/execute-plan/SKILL.md` Step 3.1 item 2 so the initial pass's composition defers to `agents/skills/review-agents/review-panel-selection.md` (default five-worker panel; the Focused panels arm when every task resolved to Tier L and the cumulative diff adds no risk signal; `panel_mode: focused` plus selection reason recorded), keeping `Review mode: fresh-adversarial` and verification-gate item 7 unchanged. Delete at least as many bytes as added. Run the doing-code-review panel over the delta, `bash scripts/check_maintenance_pins.sh`, the hygiene scan, and `bash scripts/check-no-em-dash.sh touched`; land with the `Ad-hoc-panel-pass:` receipt and delete the origin row in the same landing.

Rejected alternatives:
- Add a Phase 3 tier table to execute-plan mirroring the per-task table: rejected because the panel-selection document declares itself the single source and forbids inline duplication (`agents/skills/review-agents/review-panel-selection.md`, Shared scope and complexity policy)
- Make the five-worker panel unconditional and accept the cost: rejected because the Focused panels arm already exists and the risk-signal floor, not worker count, is the protection (`agents/skills/review-agents/review-panel-selection.md`, Focused panels and Risk-signal floor)
- Lower the cost by having lens workers skip re-running validators: rejected because it changes worker return rules across every orchestrator for a cost the panel-size fix removes first (`agents/skills/execute-plan/subagent-prompts.md`, Review lens worker)

Standing pre-authorization: the single sentence swap.

Machinery admission: no gate, validator, lock, ledger, or ceremony is added or changed; the edit references an existing arm.

## registry-audit-cell-empty-on-routine-completion

Added: 2026-10-20, investigate pass anchored on the token-drift row filed from the operator-directed stranded-rows relocation

Work-type verdict: ad-hoc-able because both arms are one sentence each in tracked skill-text surfaces the origin row names (`agents/skills/plans/SKILL.md` completion transition sentence, `agents/skills/doc-hierarchy/SKILL.md` audit column row), body-named with no open design choice (the only choice, scrubbing the existing notes, is deferred out of scope by the row itself), and no validator, guard, state schema, dependency, or machinery is touched (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-20-registry-audit-note-token-drift.md

Urgency: medium - every completion pass appends a row and, absent a writer rule, keeps minting a `user-approved` token on narration (579 rows today, 5 more failed the validator when parsed this week); nothing is blocked, but the token ADR-0001 relies on loses its meaning with every landing until the writer rule exists.

Scope arms:
- Plans completion transition (`agents/skills/plans/SKILL.md`, the "append exactly one ownership-registry row" sentence): add that the `audit` cell stays empty on a routine completion and the execution summary belongs in the landing commit message, never in the registry row.
- Doc-hierarchy audit column row (`agents/skills/doc-hierarchy/SKILL.md`): add that the cell is empty on every row except an ADR-0001 override the user confirmed, and narration is never an audit note.
- Leave the 579 existing token notes untouched; the row records that scrub as a separate operator decision.
- Anti-growth: one sentence inside each existing paragraph or table cell, no new section or field; pay with equivalent deletion if a file sits at its cap.

Orientation: the registry and its validator landed together on 2026-09-10 (`docs/history/plans/completed/2026-09-08-doc-ownership-lifecycle.md`; `scripts/doc_registry_validator.py` `audit_note_valid`); the validator checks only the token's shape, so writers that wanted an execution note in the row learned to prefix it, and the plans completion transition names the minimum cells without saying the audit cell stays empty. The 2026-10-20 relocation pass (registry commit landing the five stranded rows with cleared audit cells) is the witness that narration without the token fails and narration with the token is self-minting.

Prompt: Cover the origin row above. In `agents/skills/plans/SKILL.md`, extend the completion transition's "append exactly one ownership-registry row" sentence with one clause: the `audit` cell stays empty on a routine completion (the execution summary belongs in the landing commit message and the archived plan's disposition section, never in the row). In `agents/skills/doc-hierarchy/SKILL.md`, extend the `audit` column row with one clause: empty on every row except an ADR-0001 override the user confirmed; narration is never an audit note. Do not touch `scripts/doc_registry_validator.py`, the existing registry notes, or any other row. Run `python3 scripts/doc_registry_validator.py --selftest` (exit 0), the em-dash and public hygiene scans (exit 0), and land through the Ad-hoc backlog arm's reviewed path (panel over the branch delta, receipt line in the landing commit); delete the origin row per the covered-row rule.

Rejected alternatives:
- A validator arm refusing token notes that lack confirmation vocabulary: rejected as machinery over a wording heuristic with no witnessed incident of a false override and a high false-positive cost across 579 existing rows; no witnessed incident supports adding machinery (`docs/history/backlog/2026-10-20-registry-audit-note-token-drift.md`, Rejected)
- Widen the contract so execution narration is a sanctioned audit-note class: rejected because it legitimizes the drift and leaves ADR-0001 with no distinguishable confirmation token (`agents/skills/doc-hierarchy/SKILL.md`, Corruption override paragraph; `docs/history/plans/completed/2026-09-08-doc-ownership-lifecycle.md`)
- Scrub the 579 existing notes in the same change: rejected because committed registry rows sit beside the immutability contract and a bulk rewrite is an operator decision the row defers, not a writer-rule fix (`docs/maintenance/document-registry.md`; `docs/history/backlog/2026-10-20-registry-audit-note-token-drift.md`, Suggested fix 3)
- Fix only the doc-hierarchy contract and not the plans writer sentence: rejected because the plans completion transition is the text that drives the row append and today names the minimum cells without the audit rule, so a contract-only edit leaves the writer silent (`agents/skills/plans/SKILL.md`, completion transition)

Standing pre-authorization: both skill-text arms, uncontested on evidence (the registry count and the relocation witness are re-derived from disk; no operator or peer correction argues against them); the scrub is explicitly out of scope.

Machinery admission: not required - two sentences of skill text, no gate, validator, lock, ledger, or ceremony; the validator arm is rejected above with the missing-incident absence named.

EXEC-PROMPTS-PRUNE: placement-authoring-gloss-residual-sync -> landing in this commit (panel over the branch delta, verdict PASS; sweep found the remaining literals confined to already-conditioned sentences per the origin row's own acceptance arm; both origin rows deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: outcome-contract-fused-row-split -> 41c061b93 (landing in this commit; panel over the branch delta, verdict PASS zero blocking; fused line split at the cell boundary, concatenated cells byte-identical, one-line delta; origin row deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: doc-registry-row-outside-parsed-table-refusal -> c861ee3fc (landing in this commit; panel over the branch delta, verdict PASS zero blocking; additive present-but-unparsed diagnostic in validate and check-writes, parse/pass/refuse unchanged; selftest 154 checks green; origin row deleted per the covered-row rule; residual noted: three real registry rows currently sit outside the parsed first table, pre-existing at HEAD, out of the entry's scope)

EXEC-PROMPTS-PRUNE: acrem-witness-suite-redundant-panel-residuals -> e523e1532 (landing in this commit; panel over the branch delta, verdict PASS zero blocking; residuals O3-O5 appended with all measurements intact, Driving force count adjusted, O1/O2 and the routing sentence unchanged; the origin row stays open by design, the append is its capture)

EXEC-PROMPTS-PRUNE: series-gate-completed-path-identity -> landing in this commit (ad-hoc reviewed landing; _plan_identity_for derives the plans-root identity for a plan directly under the completed archive, the override still winning; two witnesses plus a foreign-identity negative control, RED-sanity confirmed, suite 152 OK; origin row deleted per the covered-row rule; cluster pointer tidied in 2026-10-19-machinery-registry-witness-ref-rot.md)

EXEC-PROMPTS-PRUNE: clocked-orders-stale-armed-flags-sweep -> landing in this commit (ad-hoc data pass over the gitignored clocked-order ledger, run lock-held with the ledger's own flock and atomic replace: before 20 orders / 20 terminal / 20 terminal-armed, after 20 / 20 / 0, 20 carriers disarmed, 0 jobs still loaded; each disarmed order gained one history event naming its launchd not-loaded probe as teardown evidence; no order state changed, keys unchanged, JSON parses; origin row deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: doc-registry-stranded-rows-relocation -> landing in this commit (operator-rescoped direct-commit data repair 2026-10-20: the five stranded completed rows moved into the parsed first table with their audit cells cleared instead of byte-preserved, because all five notes were untokened execution narration that the audit-note contract refuses and minting user-approved tokens on narration would be self-minting under ADR-0001; validate 0 hard, selftest exit 0; origin row deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: done-valid-document-removal-row-coverage -> 887d890b8 (served out of band: the plan landing "fix: prevent false dirt-regression refusals" narrowed the dirt-regression classifier so a within-file removal-only hunk that leaves base-era content passes, and deleted the origin row 2026-10-14-done-dirt-gate-valid-doc-removal.md per the covered-row rule; the entry stayed live two days because the stale check reads a deleted origin as LIVE, see docs/history/backlog/2026-10-20-served-origin-deletion-leaves-prompt-entries-live.md)

## i-have-adhd-portable-slash-only-gate

Added: 2026-10-20, investigate pass anchored on the skills-review row filed after the all-skills loader review

Work-type verdict: ad-hoc-able because every arm is skill or docs text on tracked surfaces the origin row names (`agents/skills/i-have-adhd/SKILL.md` frontmatter and body, `agents/skills/how-to-write-skills/SKILL.md` frontmatter requirements, the repository guidelines' Vendored Asset Sync Rules fork paragraph), with no guard, no script, and no open design choice after this investigation.

Origins:
- docs/history/backlog/2026-10-20-i-have-adhd-slash-only-gate-runtime-specific-key.md

Urgency: medium - no harm witnessed this session, but the divergence is live in every session of a runtime that ignores the key (the skill is model-invocable there against the README row's opt-in promise), and the fix is three sentences.

Scope arms:
- `agents/skills/i-have-adhd/SKILL.md`: add a top-level `when_to_use` line stating the skill is used only when the user explicitly invokes it by name and is never invoked on the model's own judgment; keep `disable-model-invocation: true` for the runtime that honors it; leave the description unchanged.
- Fork record: one short Local fork notice in the skill body (the `grilling` shape) naming the added line and why, and one line in the repository guidelines' Vendored Asset Sync Rules fork paragraph so an upstream sync re-applies it instead of overwriting it.
- `agents/skills/how-to-write-skills/SKILL.md` frontmatter requirements: one sentence that a runtime-specific gating key is paired with portable `when_to_use` wording because other loaders ignore unknown top-level keys.
- Anti-growth: three sentences in existing paragraphs, no new section; pay with deletion where a file sits at its cap.

Orientation: the skill was vendored on 2026-07-25 (c91e34db8) with the key already present; one runtime honors `disable-model-invocation`, another recognizes only `name`, `description`, `when_to_use`, `license`, and `metadata` and ignores the rest (its skill-diagnostics guide), presenting `when_to_use` to the model beside the description, which makes it the strongest portable signal available; the repository's tool-agnostic design bullet covers body text, and this is its frontmatter form.

Prompt: Cover the origin row. In `agents/skills/i-have-adhd/SKILL.md`, add the `when_to_use` frontmatter line described in the scope arms and a short Local fork notice in the body modeled on `agents/skills/grilling/SKILL.md`; add one line naming the fork to the Vendored Asset Sync Rules fork paragraph of the repository guidelines; add one sentence to the frontmatter requirements of `agents/skills/how-to-write-skills/SKILL.md` pairing runtime-specific gating keys with portable `when_to_use` wording. Run the public hygiene scan, the em-dash scan, and `python3 scripts/check_skill_description_length.py`; confirm the skill still loads by its frontmatter (`name` and `description` intact, folded description unchanged). Delete the origin row in the same change per the covered-row rule.

Rejected alternatives:
- Remove `disable-model-invocation`: rejected because it drops the hard gate on the runtime that honors it, while the fix adds a portable signal beside it (`docs/history/backlog/2026-10-20-i-have-adhd-slash-only-gate-runtime-specific-key.md`)
- A runtime-side hook hiding the skill from the model: rejected as tool-specific machinery with no witnessed incident (`agents/skills/i-have-adhd/SKILL.md`)
- Edit the frontmatter without a fork record: rejected because the skill is vendored and an upstream sync would silently overwrite the line, which the sync rules forbid for a deliberate fork (`agents/skills/grilling/SKILL.md`)
- Rewrite the description to carry the gate: rejected because a description is a trigger hint the model matches on rather than a gate, and the current description already names the slash invocation (`agents/skills/how-to-write-skills/SKILL.md`)

Standing pre-authorization: all three arms, uncontested on evidence (the recognized-key list and the README row's opt-in promise are re-derived from disk; no operator or peer correction argues against them).

Machinery admission: not required - skill and docs text only, no gate, validator, lock, ledger, or ceremony; the hook arm is rejected above with the missing-incident absence named.
