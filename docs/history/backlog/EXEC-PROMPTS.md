Tracked rolling log of ready-to-dispatch ad-hoc work entries, most urgent first, fed by investigate's work-type verdict and consumed by exec-mode sessions. This log is the exec-mode sibling of `docs/history/backlog/PLAN-PROMPTS.md`: its entries follow that file's Entry template unchanged, and its standing rules apply here by their established labels, with only the deltas stated below.

Standing rules (by their labels in `docs/history/backlog/PLAN-PROMPTS.md`, each applied as written there):

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written (the `Order` rule in `docs/history/backlog/PLAN-PROMPTS.md`).
- Prune rule: as the `Prune rule` in `docs/history/backlog/PLAN-PROMPTS.md`, with this log's delta: the prune witness is the ad-hoc landing commit, printed as one `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt line per removed entry (no plans-root file exists for an ad-hoc landing, so the landing commit substitutes for the plans-root witness; the extended prune audit accepts this witness class).
- Freeze rule: as the `Freeze rule` in `docs/history/backlog/PLAN-PROMPTS.md`, with this log's delta: the freeze trigger is an ad-hoc run claim (an exec-mode session claiming the entry for an ad-hoc run marks it `Frozen:` before the run starts, conditional on the entry still reading unfrozen at write time); the mark clears when the run's landing is stood down with a recorded reason or the run aborts without a landing commit (the entry reopens for dispatch).
- Not a backlog item: never cite this file as a plan's `Backlog origin` (the `Not a backlog item` rule in `docs/history/backlog/PLAN-PROMPTS.md`).
- Entries dispatch to exec-mode sessions: the top ready entry is an ad-hoc run's context source per `agents/skills/maintenance/SKILL.md` (the Exec-mode selection rule and the Rolling prompt log duties' EXEC-PROMPTS dispatch leg); the write turn never executes or dispatches its payload.
- Writes follow the targeted-edit drift-retry rules and the same-turn commit duty per `agents/skills/maintenance/SKILL.md` (re-read and compare before every write; targeted section edits; commit in the same turn; repo-relative-only entries carrying no personal or machine-specific data).

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
## parked-done-target-state-v9-polish-landing

Added: 2026-10-17, investigate pass over the 2026-10-17 worktree/branch sweep witness (a parked certified landing whose unblock condition passed days ago)

Work-type verdict: ad-hoc-able because the action is a bounded evidence check plus a landing or a recorded supersession of one certified branch, with the design already certified (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-parked-done-target-state-v9-polish-unlanded.md

Urgency: medium - r8-certified work exists only on one branch and is one sweep away from destruction; the park's unblock condition (the peer staged index clearing) is long satisfied.

Scope arms:
- Re-derive the v9 delta (`1ef081c27` vs its merge base) against current main; where the done/closeout surfaces moved since 2026-10-11, re-apply the intent on current bytes; land through the normal critical section.
- Verify the polish is superseded by a later landing and record the supersession, then delete the parked branch.
- Delete the parked branch without recording a disposition.

Orientation: the park record is the rider commit `a5a7656f7` ("the r8-certified v9 polish landing parks on branch tip 1ef081c27 behind the peer's staged index entry and lands as the follow-up when the index clears"). The branch `wt-done-target-state-closeout-authoring` carries the r7 landing's v9 fold (readiness byte-limit splits of four over-limit criteria, two r7-deferred prose residues). The parent plan is archived at `docs/history/plans/completed/2026-10-11-done-target-state-learn-commit-closeout.md` (r7-certified landing `04bd9c80a`), so the polish's review lineage and seal are on disk.

Prompt: Ad-hoc run covering the origin row. Read the row, the park record in rider commit `a5a7656f7`, and the parked branch's v9 tip. Diff the v9 fold against current main's touched surfaces; if the polish still applies, re-apply it on current bytes, certify nothing new (the r8 certification is the park record's own), land through the merge landing lock's critical section, and delete the branch in the same run; if a later landing already delivers the same splits or the surfaces moved such that the fold no longer applies cleanly, record the supersession in one cleanup commit (naming both the parked tip and the delivering landing) and delete the branch. Either exit leaves zero parked-landing state. Do not re-open the review series or touch the archived plan.

Rejected alternatives:
- Leave the branch parked until a future sweep: rejected because the park's unblock condition is satisfied and an ownerless parked landing is exactly what the 2026-10-17 sweep nearly destroyed (`docs/history/backlog/2026-10-17-parked-done-target-state-v9-polish-unlanded.md`)
- Re-run the review series on the v9 fold: rejected because the r8 certification is already recorded in the park record; a re-review re-pays rounds for work already certified (`docs/history/plans/completed/2026-10-11-done-target-state-learn-commit-closeout.md`)
- Delete the branch as sweep residue without a disposition: rejected because the tip is the only copy of certified work (`docs/history/backlog/2026-10-17-parked-done-target-state-v9-polish-unlanded.md`)

Machinery admission: no new machinery; both live arms end in an existing landing path or a recorded cleanup commit (`AGENTS.md`).

## review-selector-refusal-naming-and-family-scoping

Added: 2026-10-17, investigate pass over the 2026-10-17 authoring session's misattributed selector refusal and the clustered 2026-10-10 family-scoping row (one group by shared script surface; both members classify uniformly)

Work-type verdict: ad-hoc-able because both members carry body-named single-surface fixes with no open design choice on a tracked script surface, never a guard-bearing path (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-review-selector-root-derivation-refusal.md
- docs/history/backlog/2026-10-10-review-selector-kind-suffix-alias.md

Urgency: low - two live witnessed refusals this week (a fresh-worktree selection refused with a wrong precondition, and a cross-family predecessor emitted another family's r13 as the match), but each recovery is a minutes-scale detour, not a lane blocker.

Scope arms:
- Name the missing reviews directory in the `select` usage refusal: `_repository_root` returns None on a nonexistent `reviews_dir` and the usage error reports "requires a path inside a git repository"; the refusal names the directory it could not resolve and the transfer-in remedy, keeping the fail-closed refusal.
- Scope selection to the requested review family per the 2026-10-10 row's Expected: a suffix-free slug with `--kind code-review` selects only the code-review family and emits the documented suffix-form path; mixed families sharing an artifact slug never advance or supersede one another, with tests over mixed-family records.
- Derive the repository root from the source plan's git directory when the reviews directory anchor fails (silently re-anchoring past a provisioning failure).
- Keep the helper and only document the suffix-form workaround at the caller.

Orientation: read both origin rows, `scripts/review_record_selection.py` (`_repository_root` and the `select` usage path carrying the "inside a git repository" refusal, plus the family-matching predecessor logic from the review policy scope landing 90a36850e), and the Orphan recovery section of `agents/skills/review-staging/SKILL.md`. The root check's protective value is the repo-relative evidence-link contract (landed 4f86ee71a with the recover-orphan subcommand): the fix names the unresolvable directory, it does not remove the anchor. The worktree standard's transfer-in already creates the reviews home (`agents/skills/execute-plan/SKILL.md` transfer-in block runs `mkdir -p` on the facts-resolved reviews directory), so the corrected message names the provisioning remedy, not a git problem.

Prompt: Ad-hoc run covering both origins above. Read the origins, the selector script's `_repository_root`/`select` usage path and family matching, and the review-staging Orphan recovery contract. Fix 1: when the facts-resolved reviews directory does not exist, refuse with a message naming that directory and the transfer-in remedy instead of "requires a path inside a git repository"; every existing refusal behavior for genuine non-repo paths stays byte-identical. Fix 2: scope `select` candidate matching to the requested review family so a suffix-free slug with `--kind` never treats another family's records as predecessors, and emit the documented suffix-form path, per the 2026-10-10 row's Acceptance. Add tests covering mixed review families sharing an artifact slug and the missing-reviews-directory refusal wording. Run the selector's existing test suite (green required), the public hygiene scan, and the em-dash scan; land through the Ad-hoc backlog arm's reviewed path (panel over the branch delta, receipt line in the landing commit). Do not touch the pins suite, the machinery registry, or any gate or validator refusal logic.

Rejected alternatives:
- Derive the repository root from the source plan's git directory when the reviews directory is missing: rejected because the missing reviews home is a provisioning failure the worktree standard's transfer-in step owns, and silently re-anchoring hides it while changing a fail-closed helper's refusal semantics (`agents/skills/execute-plan/SKILL.md` transfer-in block)
- Remove the reviews-directory root derivation and refuse only on genuinely non-repo paths: rejected because the repo-relative evidence-link contract is the check's protective value (recover-orphan receipt; `agents/skills/review-staging/SKILL.md` Orphan recovery section, landed 4f86ee71a)
- Keep the helper and document the suffix-form slug workaround at the caller: rejected because mis-scoped predecessors let another review family's records advance the round count, which a doc note leaves live (`docs/history/backlog/2026-10-10-review-selector-kind-suffix-alias.md`)
- Fix only at the caller side (pre-create the reviews home in execute-plan Phase 3 before selection): rejected because every other caller keeps the misleading refusal; the smallest arm is at the refusal site (`scripts/review_record_selection.py`)

Machinery admission: no new machinery; both fixes are refusal-message wording and behavior-to-contract alignment in an existing helper with tests, no new gate, ledger, or ceremony (`AGENTS.md`).

## done-valid-document-removal-row-coverage

Stand-down record 2026-10-16 (run sess_67ac1556-2efe-4e92-b319-32ba30a0b40c; the entry's stop-before-deletion condition fired): the origin's witnessed shape is NOT a worktree-absent declared path. The origin's workaround ("a concise, useful boundary statement was added inside the same rewritten section") places the removal inside a file that stays present, and the disk probes split exactly on that line: a removal-only rewrite of HEAD-gained lines in a base-present worktree-existing declared path still refuses (`dirt REGRESSION`, rc 1, re-probed 2026-10-16 against scripts/dirt_regression_gate.py), while the same rewrite plus the boundary statement passes (rc 0) and a whole-file removal of a base-absent declared path passes the classifier's newly-introduced arm (rc 0, 790e02af2). The landed declared-deletion plan covers only the worktree-absent arm, so the row is NOT stale queue state and stays open; the precise uncovered case is the intentional, declared, within-file removal of HEAD-gained documentation lines, whose sanctioned exit is a machinery decision (an approval flag or classifier narrowing) that belongs to the operator under the machinery admission protocol, not to an ad-hoc pass. The row's status is untouched per the entry's own no-disposition scope arm.

Work-type verdict: ad-hoc-able because current code and its completed plan already cover the reported removal case; the remaining action is a bounded evidence check and removal of the stale open backlog row.

Origins:
- docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md

Urgency: low - the closeout gate skips a declared path that is absent from the worktree, and the completed declared-deletion plan pins that behavior; only stale queue state remains to reconcile.

Scope arms: verify the landed declared-deletion behavior and remove the now-covered origin row; retain the row and author a second guard for the same absent-path case; remove the dirt-regression gate entirely; add a new removal-only approval flag.

Orientation: the user-visible defect was that an intentional declared documentation removal was classified as a dirt regression. The completed declared-deletion landing changed the runner's input set so worktree-absent declared paths are excluded from the dirt-regression gate, while preserving the classifier for existing paths. Verify that the existing implementation and completed-plan evidence cover this exact origin. If confirmed, delete the backlog row and cite the landing commit in the cleanup commit message. Do not change the gate, add a new approval channel, or modify any other backlog item.

Prompt: Reconcile `docs/history/backlog/2026-10-14-done-dirt-gate-valid-doc-removal.md` against the completed declared-deletion fix. Read the origin, `docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md`, the current `scripts/done_run.sh` dirt-regression input construction, and its wrapper-suite evidence. Confirm that the exact removal shape in the origin is a declared path absent from the worktree and that the runner excludes it before invoking `scripts/dirt_regression_gate.py`; confirm the existing-path gate remains unchanged. If the completed plan and current code cover the origin, delete the backlog row in the same cleanup commit and name landing commit `1a9108808` as the witness. If the origin's shape differs from the landed deletion arm, stop before deletion and report the precise uncovered case. Do not run a new test suite or modify production code for a covered row.

Rejected alternatives:
- Keep the origin open and author a second removal exception: rejected because the completed plan already excludes declared worktree-absent paths from the existing dirt-regression gate (`docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md`)
- Remove the dirt-regression classifier: rejected because the landing preserves it for present declared paths and only narrows the input set for declared removals (`scripts/done_run.sh`)
- Add a new approval flag or gate for the same removal: rejected because the existing declared-path contract already carries the authorization and the fix adds no new mechanism (`docs/history/plans/completed/2026-10-15-done-run-declared-deletion-path.md`)

## placement-authoring-gloss-residual-sync

Added: 2026-10-17, investigate pass over the placement-closing-doctrine-enforcement run's exit rows (one group by shared defect class: stale worktree-keyed text left beside the landed placement consolidation; both members classify uniformly)

Work-type verdict: ad-hoc-able because both members carry body-named single-surface text fixes with no open design choice on tracked skill and template surfaces, never a guard-bearing path, with no new dependency, state-schema, or guard change (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-plans-primary-placement-authoring-residuals.md
- docs/history/backlog/2026-10-17-template-authoring-placement-gloss.md

Urgency: low - both are gloss-accuracy residuals whose anchors still resolve today; the cost is a reader resolving the plans Phase 0 to its retired worktree shape, not a blocked lane.

Scope arms:
- Sweep the plans authoring region sentence by sentence (the Phase 0 region and the Plan Lifecycle completion side): generalize worktree-keyed nouns to the placement root or add the short primary arm inline, per the origin row's stated rule; keep every pinned span byte-intact.
- Sync the maintenance authoring template's gloss lines to the renamed heading "Phase 0 (authoring placement setup)" and condition the satisfaction claim on the placement resolution the same way the plans skill's intro does; the same sentence's "worktree-first Phase 0 run setup" gloss takes the same hedge.
- Text-only change; no machinery; the placement pins own the load-bearing spans and stay green.

Orientation: the consolidation landed in 1e86f42b3 (conditioning commits afc8802c2, 9025721c9, 0e8815007); the rename and the stale glosses witness on disk today (`agents/skills/plans/SKILL.md` line 14; `agents/skills/maintenance/template-authoring.md` lines 6 and 15). This is the consumer-sweep family of `docs/maintenance/development_lessons.md` #67: retired operative text surviving in consumer text. The pins suite is a read-only probe in this pass: run it, and any red means a pinned span was touched, which stops the pass and parks for a plan route (the ad-hoc denylist bans editing `scripts/check_maintenance_pins.sh`).

Prompt: Ad-hoc run covering both origins above. Read both rows, the plans Phase 0 region and Plan Lifecycle completion side, and the maintenance authoring template. Sweep the plans region sentence by sentence per the origin row's rule and sync both template gloss lines. Keep every pinned span byte-intact; run the pins suite as a read-only probe and treat any red as stop-and-park for a plan route. Run the public hygiene scan and the em-dash scan (green required) and land through the Ad-hoc backlog arm's reviewed path (panel over the branch delta, receipt line in the landing commit). Do not touch the pins suite, the machinery registry, or any gate or validator.

Rejected alternatives:
- Treat the phase-intro scoping clause as sufficient and skip the sentence sweep: rejected as a completeness gap for step-level readers, acceptable only if the sweep finds the literals confined to already-conditioned sentences (`agents/skills/plans/SKILL.md` Phase 0)
- Fold the template gloss into the plans row's surface: rejected because the template is a separate maintenance-side consumer with its own owner-named row (`agents/skills/maintenance/template-authoring.md`)
- Add a validator pinning placement-neutral phrasing: rejected because a text sweep needs no new gate and the existing pins already cover the doctrine spans (`scripts/check_maintenance_pins.sh`; no witnessed incident)
- Leave the template as-is because the "Phase 0" anchor still resolves: rejected as the exact stale-gloss class the r4 round recorded; the cost is a reader resolving the phase to a removed shape (`docs/history/backlog/2026-10-17-template-authoring-placement-gloss.md`)

Machinery admission: no new machinery; both fixes are operative-text syncs beside an existing pin family, no new gate, ledger, or ceremony (`AGENTS.md`, Machinery admission protocol).

## plans-authoring-checklist-byte-measure-at-draft

Added: 2026-10-17, investigate pass over the third gate-time split recurrence (learn Step 1.8 dedupe into the 2026-10-10 origin row)

Work-type verdict: ad-hoc-able because the fix is one composition-time duty sentence in a single tracked skill file with no open design choice, never a guard-bearing path (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-10-execute-plan-checklist-size-preflight.md

Urgency: normal - three authoring cycles (2026-10-10, 2026-10-13/14, 2026-10-17) spent thirteen gate-time checklist-item splits in total; each split reworks complete, already-reviewed items and burns a fresh readiness pass, and the corpus rule alone has failed to prevent it twice.

Scope arms:
- Add the composition-time duty to the plans skill's authoring guidance: measure each drafted checklist item against the readiness gate's per-item byte cap while drafting (probe the drafted item's byte length; derive the cap from its owning validator, never from memory), splitting or tightening at composition time.
- Add an authoring-time preflight script the plans skill invokes before each readiness consult.
- Teach only the corpus lesson (no skill-text change).
- Extend the readiness gate's refusal message to name the cap and the offending item's length.

Orientation: the cap is enforced at execution admission (the execute-plan runtime manifest, 512 bytes per item, the origin row's witnessed 558-byte refusal) and at plan readiness, both after authoring and review have treated the checklist as final; the authoring guidance in `agents/skills/plans/SKILL.md` (Writing section) carries no measurement duty. The project corpus rule (`docs/maintenance/development_lessons.md` #49, measure while drafting) predates both later cycles and neither complied, so operative text is the fix, per the same recurrence logic as lesson #81. Derive the current cap value and its owner from `scripts/plan_readiness.py` at execution time.

Prompt: Add one duty sentence to the plans skill's authoring guidance (`agents/skills/plans/SKILL.md`, Writing section, beside the existing write-time duties): when drafting task acceptance checklist items, measure each item against the readiness gate's per-item byte cap while drafting (derive the cap from its owning validator at execution time, never from memory) and split or tighten at composition time rather than at gate time. Keep the sentence under the skill's style rules, run the public hygiene scan and the em-dash scan over the changed file (exit 0 required), and land through the Ad-hoc backlog arm's reviewed path (panel over the branch delta, receipt line in the landing commit).

Rejected alternatives:
- Authoring-time preflight script invoked before readiness consults: rejected as machinery ahead of need - the duty sentence is the smallest arm, and a script is the promotion if the sentence alone misses again (`AGENTS.md`, Machinery admission protocol; no witnessed catch for the script)
- Rely on the corpus lesson alone: rejected by witness - the rule existed for both later cycles and neither complied (`docs/maintenance/development_lessons.md` #49, recurrences 2026-10-13/14 and 2026-10-17)
- Better gate refusal message naming cap and length: rejected because gate-time diagnosis still lands after reviewed items are complete, the rework the origin row prices (`docs/history/backlog/2026-10-10-execute-plan-checklist-size-preflight.md`)

Machinery admission: no new machinery; one operative-text duty beside existing write-time duties, no gate, ledger, or ceremony (`AGENTS.md`, Machinery admission protocol).

## outcome-contract-fused-row-split

Added: 2026-10-17, investigate pass over the placement-closing-doctrine-enforcement closeout's formatting exit row

Work-type verdict: ad-hoc-able because the row carries a body-named single-surface fix with no open design choice on a tracked docs surface, never a guard-bearing path (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-outcome-contract-row-jam.md

Urgency: low - markdown still renders the cells; the cost is line-oriented parsing and human scans reading one oversized row; witnessed once, no recurrence since the 2026-10-04 introduction.

Scope arms:
- Split the fused physical line at the cell boundary so the done-lock row starts on its own table line, preserving every cell's text byte-for-byte; the jam sits mid-cell, so a naive newline insertion can swallow content.
- Prove the split with a one-line count delta and byte-identical concatenated content on both sides of the inserted newline; no other table edits.

Orientation: the fusion predates the current placement landing: introduced 10a221758 (2026-10-04, the outcome-contract migration) and carried through the contract's re-landing cf53ec22f. The physical line has drifted from the origin row's line 58 to 68, so locate it by content anchor (the one physical line carrying both the done_sweep_gates row text and the done-lock.sh invocation text), never by line number.

Prompt: Ad-hoc run covering the origin above. Read the row, locate the fused line in `scripts/OUTCOME_CONTRACT.md` by its content anchor, split it at the cell boundary into two table rows, and prove no cell text changed (concatenated-byte equality plus the one-line delta). Run the public hygiene scan and the em-dash scan (green required) and land through the Ad-hoc backlog arm's reviewed path (panel over the branch delta, receipt line in the landing commit). Do not reflow the table or touch any other row.

Rejected alternatives:
- Reflow or reformat the whole table while splitting the row: rejected as overreach beyond the witnessed one-line defect (`docs/history/backlog/2026-10-17-outcome-contract-row-jam.md`)
- Leave as-is because markdown renders the cells: rejected because line-oriented tooling and human scans lose the row boundary, the row's witnessed cost (`scripts/OUTCOME_CONTRACT.md` table)
- Add a table-lint gate to catch future fusions: rejected because one formatting defect with no recurrence is no incident for blocking machinery (`AGENTS.md`, Machinery admission protocol; no witnessed recurrence)

Machinery admission: no new machinery; a one-line formatting split in a doc file, no gate, ledger, or ceremony.

## doc-registry-row-outside-parsed-table-refusal

Added: 2026-10-17, learn Step 1.8 capture from an exec-run session, investigated same day

Work-type verdict: ad-hoc-able because the fix is one bounded refusal-message narrowing in a single validator with no open design choice; it satisfies the Ad-hoc backlog arm's single-surface text-fix path (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm).

Origins:
- docs/history/backlog/2026-10-17-doc-registry-row-outside-parsed-table-refusal.md

Urgency: low - the cost lands only inside a landing's critical section (two extra refusal cycles to re-derive the parser's first-table boundary empirically), and the row shape is now pinned in the project lessons corpus (`docs/maintenance/development_lessons.md`, #80)

Scope arms:
- Narrow the failing-identity refusal: when the identity's row text exists in the registry file but outside the parsed first table, the refusal names the row as present-but-unparsed in one line.
- Widen the parser to read every table in the file.
- Remove the first-table contract and the row-count cross-check.
- Add a pre-write lint or hook that validates row placement before the gate runs.

Orientation: the validator parses only the FIRST Markdown table and ignores rows after any non-table line (`scripts/doc_registry_validator.py`, module docstring), a contract unchanged since introduction (7dcdf6c5b). When a check fails for an identity whose row text is present in the file but unparsed, the refusal reports only an aggregate row-count delta on both sides, so the remedy is re-derived under landing pressure rather than named. Keep the parse behavior and all existing refusals unchanged; add only the diagnostic line. Update the validator's wrapper-suite fixtures for the new message and keep the row-count cross-check intact.

Prompt: In `scripts/doc_registry_validator.py`, when a registry check fails for an identity whose row text appears in the registry file outside the parsed first-table region, emit one additional refusal line naming the row as present but unparsed (rows after the first non-table line are ignored). Do not change what parses, what passes, or what refuses. Extend the validator's test suite with a fixture whose row sits after a bullet list and assert the new diagnostic line fires alongside the existing row-count refusal. Run the suite; exit 0 required.

Rejected alternatives:
- Widen the parser to every table: rejected because first-table-only parsing is the documented contract since the validator's introduction and widening changes gate semantics beyond the witnessed cost (`scripts/doc_registry_validator.py` module docstring; 7dcdf6c5b)
- Remove the first-table contract and row-count cross-check: rejected because the cross-check caught the misplacement at all; without it the unparsed row would land silently (`docs/history/backlog/2026-10-17-doc-registry-row-outside-parsed-table-refusal.md`)
- Add a pre-write lint or hook for row placement: rejected as machinery without admission - no witnessed incident beyond the two refusal cycles the diagnostic itself removes, and the row shape is already pinned as a lesson (`docs/maintenance/development_lessons.md`, #80)
- Teach the shape in skill text instead: rejected because the witnessed repeat shows session-carried notes do not bind under landing pressure, and the anti-growth rules price operative text growth over a bounded validator message (`agents/skills/maintenance/zcode.md`)

## acrem-witness-suite-redundant-panel-residuals

Added: 2026-10-18, investigate pass over the 2026-10-18 acrem certification double-delivery's uncaptured panel findings

Work-type verdict: ad-hoc-able because the action is one bounded append to an existing durable row (the certification-residual routing's capture shape, `agents/skills/review-staging/SKILL.md`, certification-residual routing note), with no design choice, no gate, and no tracked surface beyond the row file.

Origins:
- docs/history/backlog/2026-10-18-acrem-certification-residuals.md

Urgency: low - the cost lands when the landed plan is executed (the executor builds the mis-sized degenerate fixture and ships the unwitnessed index branch), and the origin row's own priority is low.

Scope arms:
- Append the three redundant-panel residuals below to the landed row as items 3 through 5 of its Residuals list, keeping its per-residual shape, and adjust the row's count-bearing header wording (the Driving force line names "two Low residuals") to match the appended set; leave its two existing residuals and closing routing sentence unchanged.
- Fold the residuals into the landed plan text instead, re-opening certification.

The three residuals, measured by the redundant session's r11 panel (both panels independently converged on the row's existing screening-length residual, which strengthens it):

1. Degenerate-rename fixture sizing (testing#needle-unreachable-from-prescribed-text, Medium): the Task 1 recipe "the plan bytes amended between the boundary and the archive add by a small edit above the rename-detection threshold" is not self-executing and reads inverted (similarity must stay above the threshold, so the edit must be small). Measured in scratch repositories at the test suite's house fixture scale: two-line plan bodies emit D+A for any amendment; pairing holds from about four content lines up (R081 at 4 lines, R086 at 6, R089 at 8, R074 at 10 with one edited line). Fix: pin a sizing rule (the fixture plan carries at least four checked task lines; the amendment appends or edits one short line so the pair stays above git's rename-detection threshold) and the base-blob-distinct property the refuse arm needs.
2. CRLF fixture git-attributes hermeticity (testing#hermeticity-gap, Medium): the Task 3 pin "core.autocrlf=false with no text or eol attributes" covers only repo-local configuration; a global core.attributesFile declaring text normalization for the fixture's file kind normalizes the committed blob to LF and the expected-GREEN arms refuse (measured end-to-end; this host's global core.autocrlf=input is defeated by the repo pin, so the attributes path is the gap). Fix: pin the mechanism - repo-local core.attributesFile set to an empty fixture file, or GIT_CONFIG_GLOBAL/GIT_ATTR_NOSYSTEM in the sweep env.
3. Staged-addition witness arm (testing#missing-test, Medium): Task 1 threads the staged-addition shape but no witness covers it: the Task 3 else-form witness pins only untracked and committed additions, and the existing staged fixture is a rename (git mv), so the index branch ships unwitnessed. Fix: extend the else-form witness (or Task 4) with a staged-addition arm: a staged-addition archive whose record carries the archive-state identity with the staged bytes' digest and a yes verdict expects the pass.

Orientation: the plan landed r11-certified (landing 6570005ad; certified plan digest fb1f3efcd258cd7f19e2e6bf696228a08508a62e1868a6380364fc75d28383fd, re-derived from the tip at investigation time). The winning session's panel captured the row's two residuals while a redundant parallel session - spawned by stacked same-window carriers, the development-lessons #86 incident - stood down before any staging write, and its panel's three residuals survived only in its stand-down report (development-lessons #87). This entry is that report's durable routing: the append turns conversation-held evidence into the row's capture. The certification-residual routing forbids re-rounds for non-blocking residuals, so the row, not the plan bytes, is the capture surface of record.

Prompt: Read docs/history/backlog/2026-10-18-acrem-certification-residuals.md first. Append the three residuals above as items 3 through 5 of its Residuals list, preserving the row's per-residual shape (worker, pattern id, severity, the stated fix), adjusting the count-bearing header wording to match the appended set, and leaving the two existing residuals and the closing routing sentence unchanged. Keep every addition free of em dashes and absolute paths; run the em-dash scan over the row (exit 0 required) and commit the row edit by explicit path.

Rejected alternatives:
- Fold the three residuals into the landed plan text and re-certify: rejected because the certification-residual routing forbids re-rounds for non-blocking residuals and any plan-byte change stales the certified sidecar digest against the readiness gates (`agents/skills/review-staging/SKILL.md` certification-residual routing note; `agents/skills/review-plan/SKILL.md` readiness-gate integration paragraph)
- File a second row for the redundant panel's findings: rejected because one plan's residuals belong in one durable home and the winner's row already exists (`docs/history/backlog/2026-10-18-acrem-certification-residuals.md`; the fold-not-write discipline, `docs/maintenance/development_lessons.md` #66)
- Add a mechanical gate requiring stand-down sessions to file their findings: rejected as machinery without admission - one witnessed collision and low expected catch frequency against a blocking gate on every stand-down, with the behavioral rule just landed (`docs/maintenance/development_lessons.md` #86, #87)
- Drop the three findings as non-blocking noise: rejected because two are Medium measurements that bite the executor directly (the mis-sized fixture, the hermeticity gap) and the third is a coverage gap in the planned witness suite (`docs/history/plans/2026-10-17-archive-ceremony-review-evidence-mismatch.md`, Tasks 1 and 3 witness prescriptions)

Standing pre-authorization: ordinary backlog capture under the certification-residual routing; no operator rescope required.

Machinery admission: not required - the recommendation is one row append and adds no gate, validator, lock, ledger, or ceremony.
