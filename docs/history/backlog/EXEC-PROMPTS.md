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
EXEC-PROMPTS-PRUNE: parked-done-target-state-v9-polish-landing -> supersession cleanup (this commit): the v9 fold (tip 1ef081c27, plan-text readiness byte-limit splits only) is superseded by the executed r7-certified landing 2f8e017d5 whose archived plan the fold's readiness purpose no longer serves; parked branch wt-done-target-state-closeout-authoring deleted in the same run

EXEC-PROMPTS-PRUNE: review-selector-refusal-naming-and-family-scoping -> landing in this commit (panel over the branch delta, verdict PASS with two folds landed; both origin rows deleted per the covered-row rule; residuals noted: legacy prefix-form corpora strand silently by design, and agents/skills/review-staging/SKILL.md line 736 still documents the prefix glob shape)
EXEC-PROMPTS-PRUNE: closeout-citation-template-form-empty-stem -> landing in this commit (panel over the branch delta, verdict PASS with six non-blocking findings, two folded: assertion pins the named citation span, dead test scaffolding removed; residuals: tokenizer widening can merge no-whitespace bracket-abutting exact tokens fail-closed, gate-side bare-fragment refusal lacks a dedicated test, module docstring nuance)
EXEC-PROMPTS-PRUNE: plans-authoring-checklist-byte-measure-at-draft -> landing in this commit (panel over the branch delta, verdict PASS zero blocking; one duty sentence in the plans skill Writing paragraph, cap derivation pinned to scripts/plan_readiness.py)
EXEC-PROMPTS-PRUNE: review-staging-branch-review-path-glob-drift -> landing in this commit (panel over the branch delta, verdict PASS zero blocking; doing-code-review record-path row synced to the family-scoped suffix form with the legacy prefix glob named as no longer matching new allocations)

EXEC-PROMPTS-PRUNE: fold-commit-staged-record-precondition -> landing in this commit (ad-hoc reviewed landing; panel over the branch delta PASS zero blocking; fold-time staged-record duty line in the review-loop fix-and-fold batch step + Integration Points reconciliation; origin row deleted per the covered-row rule, the landing the witness)

EXEC-PROMPTS-PRUNE: reviews-home-migration-collision-loudness -> landing in this commit (ad-hoc reviewed landing; panel over the branch delta, verdict PASS after one blocking fold - dangling-destination-symlink digest read made OSError-tolerant; origin row deleted per the covered-row rule; standing residual: a collision rename that fails copy verification reports via stderr ERROR, not a COLLISION line)

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

EXEC-PROMPTS-PRUNE: placement-authoring-gloss-residual-sync -> landing in this commit (panel over the branch delta, verdict PASS; sweep found the remaining literals confined to already-conditioned sentences per the origin row's own acceptance arm; both origin rows deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: outcome-contract-fused-row-split -> 41c061b93 (landing in this commit; panel over the branch delta, verdict PASS zero blocking; fused line split at the cell boundary, concatenated cells byte-identical, one-line delta; origin row deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: doc-registry-row-outside-parsed-table-refusal -> c861ee3fc (landing in this commit; panel over the branch delta, verdict PASS zero blocking; additive present-but-unparsed diagnostic in validate and check-writes, parse/pass/refuse unchanged; selftest 154 checks green; origin row deleted per the covered-row rule; residual noted: three real registry rows currently sit outside the parsed first table, pre-existing at HEAD, out of the entry's scope)

EXEC-PROMPTS-PRUNE: acrem-witness-suite-redundant-panel-residuals -> e523e1532 (landing in this commit; panel over the branch delta, verdict PASS zero blocking; residuals O3-O5 appended with all measurements intact, Driving force count adjusted, O1/O2 and the routing sentence unchanged; the origin row stays open by design, the append is its capture)

## series-gate-completed-path-identity

Added: 2026-10-19, learn-capture investigate over the fifth max-4 exec-run reviewer observation

Work-type verdict: ad-hoc-able because the action is a bounded single-function derivation correction on an existing read-only surface (derive the identity from the pre-archive plans-root path when the plan sits under the completed archive), with no gate, no behavior change for plans-root paths, and no new surface (agents/skills/maintenance/decisions.md, Ad-hoc backlog arm single-surface path).

Origins:
- docs/history/backlog/2026-10-19-series-gate-completed-path-identity.md

Urgency: low - the defect is warning noise on one invocation shape (a direct gate or verify run against an archived plan path); the operative closeout flow is the twin runner, which already passes the correct identity and is test-pinned.

Scope arms:
- In scripts/worktree_closeout_migrate.py, when the resolved plan path sits under the completed archive and no `--plan-identity` override is present, derive the identity from `docs/history/plans/<basename>` (the pre-archive path the records were tokened from), mirroring what `_run_gate_on_twin` passes.
- Pin both shapes in tests: a direct run on a completed-archive plan path with a plans-root-tokened record emits no warning; the override flag still wins over the derivation.
- No change to plans-root derivations, the diagnostic sink semantics, or the twin runner.

Orientation: `_plan_identity_for` (scripts/worktree_closeout_migrate.py:597, re-derived at HEAD 4fa60506c) resolves the plan path verbatim, so an archived plan's identity names the completed-archive path while its records carry tokens and sidecar identities derived from the original plans-root path; every series member then reports a spurious foreign warning on a direct run. The twin runner is the sanctioned flow and is unaffected; the reviewer of the series-token execution recorded the direct-run noise as an accepted observation (finding 6, 2026-10-19).

Prompt: Cover the origin row above. Correct the identity derivation for completed-archive plan paths in scripts/worktree_closeout_migrate.py per the scope arms, pin both shapes with tests, run python3 scripts/test_worktree_closeout_migrate.py (expect OK), the em-dash and public hygiene scans (exit 0), and land through the Ad-hoc backlog arm's reviewed path. Do not touch plans-root derivation behavior, the diagnostic wording, or the twin runner.

Rejected alternatives:
- Leave it and document the twin runner as the only sanctioned flow: rejected because the direct-run shape is reachable and the fix is a two-line derivation correction; documentation does not stop the noise (docs/history/backlog/2026-10-19-series-gate-completed-path-identity.md, Expected)
- Add a blocking refusal on the direct-completed-path run: rejected as machinery without admission - the shape produces read-only noise, never a wrong result, and no landing or lane was ever blocked by it (no witnessed incident)
- Re-token archived records to the completed path: rejected because record tokens and sidecar identities are keyed to the original source-plan path by the review-staging contract, and rewriting evidence bytes to silence a warning inverts the ownership (agents/skills/review-staging/SKILL.md, Metadata block; scripts/review_plan_identity.py identity_token)

Machinery admission: not required - the recommendation corrects an existing read-only derivation and adds no gate, validator, lock, ledger, or ceremony; the blocking-refusal arm is explicitly rejected with no witnessed incident.

## doc-registry-stranded-rows-relocation

Stand-down record 2026-10-19 (exec-mode ad-hoc run sess exec-2026-10-19-lciu, stood down before any landing; the run's stop-before-completion condition fired): the byte-preserving relocation is incompatible with the validator's audit-token contract. Re-derived on the run branch: two of the five rows' audit cells (plan-authoring-done-closeout, done-final-only-learn-intermediate) carry prose notes written outside the gate, and `scripts/doc_registry_validator.py` `audit_note_defects` HARD-refuses any non-empty completed-row audit note not beginning with `user-approved YYYY-MM-DD:` (ADR-0001: a self-minted token licenses nothing), so the moved rows fail `validate` hard. The entry's byte-preservation arm and its validate-green acceptance cannot both hold; minting the approval token is operator-owned and no gate or validator may be edited mid-lane. The entry stays open; a viable fix shape needs the operator's recorded approval token for the affected rows, or the entry re-scoped to relocate only rows whose notes already carry the token.

Added: 2026-10-19, investigate pass anchored on the learn Step 1.9 row of the same name

Work-type verdict: ad-hoc-able because the action is a one-time bounded data repair of a single tracked file (move already-written table rows into the parsed first table), with no design choice, no behavior change, and no gate touched (`agents/skills/maintenance/decisions.md`, Ad-hoc backlog arm single-surface path).

Origins:
- docs/history/backlog/2026-10-19-doc-registry-stranded-rows-relocation.md

Urgency: low - the cost is five standing unregistered-file warns on every validate run and five completed sources outside the gate's claimed-src set; no landing is currently blocked, and the validator-side diagnostic that names each stray row landed c861ee3fc.

Scope arms:
- Move the five stranded completed-state rows (plan-scope-gist-surface-1010-plan, plan-scope-gist-surface-1010-backlog, plan-authoring-done-closeout, prompt-log-deferred-origin-stale-pin, done-final-only-learn-intermediate) into the first table of docs/maintenance/document-registry.md, byte-preserving each row's cells, and delete the stray copies after the first non-table block.
- Confirm with `python3 scripts/doc_registry_validator.py validate` (zero unregistered warns for the five sources) and `--selftest` exit 0.
- Leave the first-table parse contract, the row-count cross-check, and every other row untouched.

Orientation: the first-table-only parse contract dates to the validator's introduction (7dcdf6c5b, 2026-09-10) and is documented in its module docstring; rows after the first non-table line never parse. The misplacement is recurring: development-lessons #80 witnessed two occurrences 2026-10-17, and one of the five standing rows landed 2026-10-19. The diagnostic that names a present-but-unparsed row beside the refusal landed earlier the same day (c861ee3fc); this entry is its data-repair complement. The five-row standing state was re-derived from disk 2026-10-19 with the validator's own helpers (five unparsed table lines, five matching unregistered-file warns, present at HEAD by git probe).

Prompt: Cover the origin row above. Move the five stranded registry rows into the first table of docs/maintenance/document-registry.md byte-preserving each row's cells, delete the stray copies, run `python3 scripts/doc_registry_validator.py validate` (zero unregistered warns for the five named sources required) and `--selftest` (exit 0), run the em-dash and public hygiene scans (exit 0), and land through the Ad-hoc backlog arm's reviewed path (panel over the branch delta, receipt line in the landing commit). Do not touch any other row, the validator, or its parse contract.

Rejected alternatives:
- Add a pre-write lint or hook enforcing row placement: rejected as machinery without admission - one low-severity recurring warn class, no blocked landing, and the additive diagnostic already names each stray row at refusal time (`docs/history/backlog/2026-10-19-doc-registry-stranded-rows-relocation.md`, Rejected alternatives; the pruned entry `doc-registry-row-outside-parsed-table-refusal`, landing c861ee3fc)
- Widen the parser to read every table: rejected because first-table-only parsing is the documented contract since the validator's introduction and widening changes gate semantics beyond the witnessed cost (`scripts/doc_registry_validator.py` module docstring; introduced 7dcdf6c5b, 2026-09-10)
- Leave the rows where they are: rejected because unregistered completed sources sit outside the immutability gate's claimed-src set and five standing warns train operators to ignore the warn tier (re-derived from disk 2026-10-19: five unparsed lines, five matching warns; docs/maintenance/document-registry.md at HEAD)

Machinery admission: not required - the recommendation is a one-time data repair of an existing tracked file and adds no gate, validator, lock, ledger, or ceremony; the machinery arm (pre-write lint) is explicitly rejected with no witnessed blocking incident.

## clocked-orders-stale-armed-flags-sweep

Added: 2026-10-19, investigate pass over the authoring closeout's launchd liveness repair

Work-type verdict: ad-hoc-able because the fix is one scripted data pass over a gitignored runtime ledger with no gate, validator, or guard-bearing surface touched (the ad-hoc eligibility test's machinery and guard exclusions both miss), and the witnessed cost is one wasted probe, not a wrong action.

Origins:
- docs/history/backlog/2026-10-19-clocked-orders-stale-armed-flags.md

Scope arms:
1. Re-derive from disk at run time: count the ledger's terminal orders (state discharged or cancelled) and the subset whose carrier record reads armed true; when the armed subset is empty, report the sweep as already done and stop.
2. For each terminal order with armed true: set `carrier.armed` to false and append one history event recording that order's teardown evidence (the 2026-10-19 launchd bootouts where the job was among them, otherwise a not-loaded probe of the order's recorded job label).
3. Verify the write is read-only at the order level: no order `state` changes, no schema change, and the ledger parses as JSON after the write.

Orientation: a terminal order's carrier record still reads armed, so a ledger reader cannot distinguish an armed carrier from a consumed one without leaving the ledger; witnessed 2026-10-19 when a closeout's liveness repair had to probe launchd directly and found six jobs for discharged orders still loaded while every ledger flag said armed.

Prompt: Cover the origin row above. Sweep the clocked-order ledger per the three scope arms: re-derive the armed-terminal subset from disk first, disarm each terminal order's carrier record with a history event naming its teardown evidence, and finish with a JSON parse plus a before/after count printed in the run record. Stop and report if the runtime lock for the ledger cannot be acquired; never edit order states.

Rejected alternatives:
- Flip the flag inside the discharge and cancel handlers now: rejected, no second witnessed cost and the certified consult design reads state fields (next_turn_at, parent_automation_id, children[]), never carrier flags (docs/history/plans/2026-10-18-clocked-order-successor-verification.md predicate); the sweep is the smallest arm that removes the witnessed cost.
- Leave the flags and document the reading semantics: rejected, the flags misled a witnessed read the same day they mattered (the closeout probed launchd directly); a docs note does not stop the next mislead.
- A validator gating armed flags on terminal orders: rejected as machinery with no witnessed incident (the flag's mislead cost one probe and no wrong action followed), the missing-incident absence named per the machinery admission protocol.

Machinery admission: not required - the recommendation is a one-time data repair of an existing runtime ledger; the machinery arm is explicitly rejected above with its missing-incident absence named.
