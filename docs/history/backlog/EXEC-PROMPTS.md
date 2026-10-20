Tracked rolling log of ready-to-dispatch ad-hoc work entries, most urgent first, fed by investigate's work-type verdict and consumed by exec-mode sessions. This log is the exec-mode sibling of `docs/history/backlog/PLAN-PROMPTS.md`: its entries follow that file's Entry template unchanged, and its standing rules apply here by their established labels, with only the deltas stated below.

Standing rules (by their labels in `docs/history/backlog/PLAN-PROMPTS.md`, each applied as written there):

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written (the `Order` rule in `docs/history/backlog/PLAN-PROMPTS.md`).
- Prune rule: as the `Prune rule` in `docs/history/backlog/PLAN-PROMPTS.md`, with this log's delta: the prune witness is the ad-hoc landing commit, printed as one `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt line per removed entry (no plans-root file exists for an ad-hoc landing, so the landing commit substitutes for the plans-root witness; the extended prune audit accepts this witness class).
- Freeze rule: as the `Freeze rule` in `docs/history/backlog/PLAN-PROMPTS.md`, with this log's delta: the freeze trigger is an ad-hoc run claim (an exec-mode session claiming the entry for an ad-hoc run marks it `Frozen:` before the run starts, conditional on the entry still reading unfrozen at write time); the mark clears when the run's landing is stood down with a recorded reason or the run aborts without a landing commit (the entry reopens for dispatch).
- Not a backlog item: never cite this file as a plan's `Backlog origin` (the `Not a backlog item` rule in `docs/history/backlog/PLAN-PROMPTS.md`).
- Entries dispatch to exec-mode sessions: the top ready entry is an ad-hoc run's context source per `agents/skills/maintenance/SKILL.md` (the Exec-mode selection rule and the Rolling prompt log duties' EXEC-PROMPTS dispatch leg); the write turn never executes or dispatches its payload.
- Writes follow the targeted-edit drift-retry rules and the same-turn commit duty per `agents/skills/maintenance/SKILL.md` (re-read and compare before every write; targeted section edits; commit in the same turn; repo-relative-only entries carrying no personal or machine-specific data).

EXEC-PROMPTS-PRUNE: learn-commit-own-edit-check-mechanical-shape -> landing in this commit (ad-hoc reviewed landing; focused contract-docs + correctness-completeness panel over the branch delta, one blocking fold (absolute worktree path in the freeze mark) plus three minor folds, verdict ready=yes after folds; residual F2/F6 captured as docs/history/backlog/2026-10-21-own-edit-check-pure-deletion-carve-out.md; origin row deleted per the covered-row rule)

## learn-lesson-number-allocation-fresh-read

Added: 2026-10-21, investigate pass anchored on the lesson-number collision row filed by the learn pass over the certification-seal-landing-survival execution session

Work-type verdict: ad-hoc-able - two body-named sentence edits inside one skill (`agents/skills/learn/SKILL.md` re-read rule and `agents/skills/learn/step-6-instruction-updates.md` commit discipline), tracked skill text with no guard change, no new dependency, no state-schema change (the Ad-hoc backlog arm's eligibility test, `agents/skills/maintenance/decisions.md`); the blocking-promotion arm is deliberately excluded (see the rejected alternatives).

Origins:
- docs/history/backlog/2026-10-21-learn-lesson-number-collision-parallel-sessions.md

Urgency: high - four colliding heading pairs landed in one day from three sessions and the repair raced a live peer twice; every `See also #N` citation to a collided number is ambiguous until repaired, and the maintenance loop now runs several learn-bearing sessions per day.

Scope arms:
- Allocation by fresh read: extend the SKILL.md re-read sentence ("Before each corpus write, re-read the destination file and re-apply the placement against its fresh state") so the project-corpus `#N` is derived as the maximum existing heading number plus one from that same fresh read, inside the write step, never from a number read earlier in the session.
- Own-edit hunk check on the corpus commit: state in Step 6.6 (or the commit rule it points at) that the project corpus is staged by hunk after the Step 1.8 word-diff own-edit check, never whole-file, so a peer's uncommitted lesson is skipped and reported rather than swept into the committer's commit (lesson 134 is the class).
- Pay growth with deletion: fold the number derivation into the existing re-read sentence and drop the "(warn-only, no script)" parenthetical's dangling claim that no script exists (the user-corpus `lessons.py index` already has the `duplicate` category).

Orientation: the warn-only `grep | uniq -d` dates to the single-session era (380b46fc8, 2026-07-05) and was restated unchanged in the 2026-10-18 module split (867f8ed7e); the SKILL.md re-read rule already anticipates a parallel learn run but names only placement, not the number; the user corpus got a blocking `duplicate` category through `lessons.py index` while the project corpus kept the optional grep, so the two tiers diverged exactly on the invariant that failed.

Prompt: In an ad-hoc worktree, edit `agents/skills/learn/SKILL.md` so the per-write re-read sentence also derives the project-corpus lesson number as max existing `## N.` plus one from that fresh read, and edit `agents/skills/learn/step-6-instruction-updates.md` so the corpus commit is staged by own-edit hunk per the Step 1.8 word-diff check (never whole-file), replacing the "(warn-only, no script)" parenthetical with a pointer at the user-corpus validator's `duplicate` category as the shape a later promotion would reuse; keep both edits to the existing sentences; run the doing-code-review panel over the branch delta, the public-hygiene scan, and the pins suite; land per the Ad-hoc backlog arm with the origin row deleted in the same commit.

Rejected alternatives:
- Promote the project-tier duplicate check to a blocking gate now: rejected for this entry because a warn-only check promoting to blocking is a guard change the Ad-hoc arm excludes and the Machinery admission protocol requires a retired or demoted blocker in the same change or explicit operator approval of net growth; the true catch is now ledgered for that decision in the origin row (the repository guidelines' Machinery admission protocol section; `docs/history/backlog/2026-10-21-learn-lesson-number-collision-parallel-sessions.md`)
- Serialize learn corpus writes under the done lock: rejected because learn runs at every intermediate boundary outside done and the lock's span is the closeout, not the boundary (`agents/skills/learn/SKILL.md`, Integration Points with `done`)
- Switch the project corpus to date-keyed or hash-keyed lesson identifiers: rejected because every existing `See also #N` citation and the `generalize` audit key on the numeric form, so the migration cost exceeds the collision cost the fresh-read allocation removes (`docs/maintenance/development_lessons.md`)

Standing pre-authorization: the two sentence edits.

Machinery admission: no gate, validator, lock, ledger, or ceremony is added or promoted; the fresh-read allocation and the hunk-staging discipline are text within existing steps, and the promotion arm is recorded as rejected pending the operator's net-growth decision.

## closeout-baseline-capture-facts-resolved-dirs

Added: 2026-10-21, investigate pass anchored on the closeout-baseline row filed after the certification-seal-landing-survival execution closeout

Work-type verdict: ad-hoc-able - a body-named single-surface skill-text fix in `agents/skills/execute-plan/SKILL.md` (the Step 0.4 session-bootstrap capture block), a tracked skill surface with no guard change, no new dependency, no state-schema change (the Ad-hoc backlog arm's eligibility test, `agents/skills/maintenance/decisions.md`); the migration script is not edited.

Origins:
- docs/history/backlog/2026-10-21-closeout-baseline-dirs-omit-review-certs.md

Urgency: high - every execution run that closes a code-family round writes its seal under the run worktree's review-certs home, and the Phase 5 transfer-out silently drops it before the worktree deletion; the 2026-10-21 witness kept its seal only because the operator session copied it by hand, and the plans skill's authoring bootstrap already describes the capture as "over the facts-resolved dirs", so the execute-plan block is the one site that disagrees with its own script.

Scope arms:
- Drop the explicit `--dirs "{reviews_dir} {tmp_dir} {metrics_dir}"` override from the Step 0.4 capture invocation so `worktree_closeout_migrate.py capture` resolves its four-key family (`reviews_dir`, `tmp_dir`, `metrics_dir`, `review_certs_dir`) from the facts block, matching the plans skill's wording and the script's `FACTS_DIR_KEYS`.
- Name the seal file in the transfer-out artifact list sentence of `agents/skills/execute-plan/worktree-first.md` lifecycle step 5 ("review staging documents, stats sidecars, telemetry, ...") so the verify step reads it as a durable artifact.
- Pay growth with deletion: the removed `--dirs` operand line pays for the added artifact noun.

Orientation: the capture block's `--dirs` operand predates the script's facts-resolved family; 867f8ed7e (2026-10-18) widened it from two dirs to three on the same day f3894756d (2026-10-18) gave the script its four-key `FACTS_DIR_KEYS` resolution, so the skill lagged the script by exactly the review-certs key; the plans skill's Closeout-evidence establishment duty (Step 0) already delegates the invocation shape to this block while describing it as facts-resolved, so removing the override reconciles both texts with the script.

Prompt: In an ad-hoc worktree, edit the Step 0.4 session-bootstrap capture block in `agents/skills/execute-plan/SKILL.md` so the `worktree_closeout_migrate.py capture` invocation passes no `--dirs` operand (the script resolves `reviews_dir`, `tmp_dir`, `metrics_dir`, and `review_certs_dir` from `.ai-playbook/facts.md`; a missing key already fails loud through the existing skip-note arm), and add the certification seal file to the artifact noun list of lifecycle step 5 in `agents/skills/execute-plan/worktree-first.md` (one noun, no new sentence). Verify by running `python3 scripts/worktree_closeout_migrate.py capture --out /tmp/baseline.json` from the primary checkout and confirming the written `dirs` list carries four entries including the review-certs home; run the doing-code-review panel over the branch delta, the public-hygiene scan, and the pins suite; land per the Ad-hoc backlog arm with the origin row deleted in the same commit.

Rejected alternatives:
- Add `{review_certs_dir}` as a fourth explicit `--dirs` operand: rejected because it keeps a hand-maintained twin of the script's `FACTS_DIR_KEYS` tuple that already drifted once (867f8ed7e versus f3894756d, both 2026-10-18); dropping the override removes the twin (`scripts/worktree_closeout_migrate.py`, `_facts_dirs`)
- Make the migration script copy the review-certs home unconditionally regardless of the baseline: rejected because the baseline is the only thing that distinguishes run-created seals from pre-existing ones, and an unconditional copy re-opens the collision class the closeout migration already prices (`docs/history/backlog/2026-10-19-reviews-home-migration-collision-twins.md`)
- Track the seal file so it rides the branch commits instead of the migration: rejected because the 2026-10-11 plan deliberately re-homed seals as untracked (`docs/history/plans/completed/2026-10-11-review-certs-seal-home-untracked.md`)

Standing pre-authorization: the operand removal and the one-noun artifact-list edit.

Machinery admission: no gate, validator, lock, ledger, or ceremony is added or changed; the edit lets an existing capture resolve one more existing facts key.

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

## guard-signal-gates-authorized-action-lesson

Added: 2026-10-21, investigate pass anchored on the lesson-candidate row filed after the gate-removal-closeout-accounting execution's Phase 3 risk-lens blocking fix

Work-type verdict: ad-hoc-able - a body-named single-surface docs fix (one new lesson in `docs/maintenance/development_lessons.md`), a tracked docs surface with no guard change, no new dependency, no state-schema change (the Ad-hoc backlog arm's eligibility test, `agents/skills/maintenance/decisions.md`).

Origins:
- docs/history/backlog/2026-10-21-guard-signal-gates-authorized-action-lesson.md

Urgency: medium - the defect class (a guard's failure signal computed but only reported, so the gated action prints as authorized) is fixed at the witness site (1af769c59) but stays uncaptured for the next guard author; every session writing a new guard or disposition flag re-risks the same shape.

Scope arms:
- Capture one lesson stating the rule: an authorization decision (exit code, action line, verdict label) must consume the guard's failure signal as an input, never print beside a report that merely carries it; a guard whose evidence reaches only the report is inert.
- Witness the rule with the 2026-10-21 shape: worktree-mode gate-removal computed a retained disposition whose reasons carried failed guards yet printed the force-removal authorization line with `OUTCOME: pass`; the fix 1af769c59 propagates a `removal_blocked` flag into the removal decision and the sweep verdict.
- Land the lesson in the family the learn skill's placement rules select, linked to the fix commit and the origin row.

Orientation: the plan gate-removal-closeout-accounting's Phase 3 risk lens found the guard-report/authorization split; the lessons the same plan already landed (151-156, and the task-boundary pair) cover family-blind definitions, claim-gateway atomicity, stdlib probes, mutation matrices, readiness staleness, refusal remedies, agreement-test cross-references, and log count discipline - none states the guard-signal-to-decision rule, so the class stays uncaptured (`docs/history/backlog/2026-10-21-gate-removal-task2-review-deferred.md` holds the plan's deferred non-blocking residues, a different defect class on the same surface).

Prompt: Run the learn capture flow anchored on `docs/history/backlog/2026-10-21-guard-signal-gates-authorized-action-lesson.md`: re-derive the witness from disk (fix 1af769c59 in `scripts/worktree_closeout_migrate.py` and its tests), place one lesson in `docs/maintenance/development_lessons.md` under the family the learn placement rules select, write Principle/Trigger/Rule/Why/See-also in the house shape, cite the fix commit and the origin row, and re-check neighboring lessons' numbering and See-also links after insertion. Run the public-hygiene scan before the commit; land the lesson and the origin-row resolution in one commit on the primary checkout.

Rejected alternatives:
- Treat the fix as complete with no lesson: rejected because the class is generic to any guard/disposition split and the next guard author re-risks it; fix 1af769c59 is site-specific (`scripts/worktree_closeout_migrate.py`)
- Add a mechanical gate requiring every guard to set a blocking flag: rejected under the machinery admission protocol - one witnessed incident, no catch-frequency estimate, and an unpriced false-positive cost for guards that legitimately report only (`docs/history/backlog/2026-10-21-guard-signal-gates-authorized-action-lesson.md`)
- Route the rule to the review-agents checklist instead: rejected because the review side already caught the defect (the risk lens surfaced it as the plan's one blocking finding); the missing arm is the authoring-side rule, not reviewer vigilance (agents/skills/review-agents/SKILL.md)

Standing pre-authorization: the single-lesson capture and its origin-row resolution.

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the capture is advisory lesson text.

## execute-plan-phase2-staleness-class-and-exec-r-producer-step

Added: 2026-10-21, investigate pass anchored on the two execute-plan skill-text rows filed by the session analysis of the plan-validation-command-undefined-repo execution run (landed 28127e322)

Work-type verdict: ad-hoc-able - two body-named sentence-scale edits inside one tracked skill surface (`agents/skills/execute-plan/SKILL.md`: the Phase 2 failure arm and one Phase 4 producer step beside the archive commit), no guard change (the consuming gates in `scripts/reverse_squash_guard.py` and `scripts/done_sweep_gates_lib.py` are not edited), no new dependency, no state-schema change (the Ad-hoc backlog arm's eligibility test, `agents/skills/maintenance/decisions.md`); both origins classify uniformly (same surface, same defect class: the skill omits a duty its own landing gates enforce), so the Stage 1 group routes as one entry.

Origins:
- docs/history/backlog/2026-10-21-execute-plan-phase2-staleness-remedy-pointer.md
- docs/history/backlog/2026-10-21-execute-plan-exec-r-record-production-duty.md

Urgency: medium - every multi-task execution run reaches Phase 2 with ticked checkboxes, so the full-mode readiness exit fires on every such run while the text's only remedy names an implementation task that does not exist (the 2026-10-21 run paid a pause-and-investigate cycle to derive the re-bind round from corpus history); every archived plan's landing runs the plans-egress gate, and both 2026-10-21 runs (this one and the readiness-files-coverage-quote-prefix sibling) learned the exec-r record duty from the guard's refusal text or a sibling's backfill record, never from the skill.

Scope arms:
- Phase 2 remedy class: extend item 2 of Phase 2 ("treat as a new fix iteration (implement sub-agent on the failing scope)") with the progress-tick staleness class: a full-mode `plan_readiness.py` exit whose only delta since the latest review round is task-checkbox ticks is not a failing scope; its exit is a fresh focused plan-review round over the current plan bytes whose record re-binds the digest (lesson 165 in `docs/maintenance/development_lessons.md`; the review-plan round-close seal duty), the implement arm staying for a genuinely failing validation command.
- Phase 4 producer step: one step beside the archive commit naming the exec-r pointer record the landing's plans-egress gate demands (`<date>-plan-review-<slug>-exec-r<N>.md` under the resolved reviews home, carrying the egress bytes' sha256 and pointing at the exec-review record and its sidecar), and naming which gate each evidence shape satisfies: the reverse-squash guard's `check-archive` leg wants the series record for a plans-root egress, while `gate_archive_ceremony` also accepts a live plan-review receipt whose sidecar binds the plan identity, raw-byte digest, and yes verdict.
- Pay growth with deletion: both edits are sentence-scale and the file sits under its warning-only cap (`scripts/skill_text_budget_caps.json`); any breach line the byte-budget gate reports is paid in the same change.

Orientation: the Phase 2 failure arm's wording dates to the repository's initial commit (6f228dec0, 2026-06-05), before the executed-plan readiness gate existed (2242b2b3b, 2026-09-06) and before lesson 165 named the progress-tick class; the exec-r filename-series leg entered `scripts/done_sweep_gates_lib.py` at 44eec2a73 (2026-10-01) and `scripts/reverse_squash_guard.py` at 10a221758 (2026-10-02), while `agents/skills/execute-plan/SKILL.md` carries no `-exec-r<N>` record shape, no `egress`, and no guard name (working-tree grep and `git grep` at the tip agree); the skill's Phase 5 exec-review receipt existence check consumes the record but nothing produces it, and the sibling run's backfill record under the reviews home names the gate in its own "Why this record exists" text.

Prompt: In an ad-hoc worktree, edit `agents/skills/execute-plan/SKILL.md` twice. (1) In Phase 2 (Plan Completion), extend item 2 so the progress-tick staleness class is named and routed: when the full-mode readiness exit's only delta since the latest review round is checkbox ticks, the remedy is a fresh focused plan-review round over the current plan bytes whose record re-binds the digest (lesson 165; the review-plan round-close seal duty), never an implement sub-agent; keep the implement arm for a genuinely failing validation command. (2) In Phase 4 (Archive Plan), add one producer step beside the archive commit: before landing, write the `<date>-plan-review-<slug>-exec-r<N>.md` pointer record into the resolved reviews home carrying the pre-archive plan bytes' sha256 and pointers to the exec-review record and its sidecar, and name which landing gate each evidence shape satisfies (the reverse-squash guard's series record for a plans-root egress; the bound plan-review receipt alternative for `gate_archive_ceremony`). Keep both edits to one or two sentences each inside the existing items; pay any byte-budget breach in the same change. Validation: `python3 scripts/skill_text_budget.py --check` prints no breach for the file, `bash scripts/check-no-em-dash.sh touched` and the public-hygiene scan exit 0, the pins suite exits 0; run the doing-code-review panel over the branch delta and land per the Ad-hoc backlog arm with both origin rows deleted in the same commit.

Rejected alternatives:
- Leave the plans-egress gate's refusal text as the only producer guidance: rejected because the refusal fires after the landing attempt, inside the lock's span, and both 2026-10-21 runs paid a read of the guard script to learn the record shape (`scripts/reverse_squash_guard.py`)
- Have the reverse-squash guard or the archive ceremony generate the exec-r record itself: rejected because a gate writing its own evidence certifies nothing, and it adds landing-side machinery with no witnessed incident beyond the discoverability gap (`scripts/done_sweep_gates_lib.py`)
- Drop the Phase 2 implement-sub-agent arm in favor of the re-bind round: rejected because a genuinely failing validation command still needs implementation work, and lesson 165 scopes the re-bind to the progress-tick class only (`docs/maintenance/development_lessons.md`)
- Fix the Phase 2 class in the readiness script instead (recognize a ticks-only delta and pass): rejected because the digest binding is the review-plan seal's contract, so a readiness pass over un-rebound bytes would certify a digest no round produced (`agents/skills/review-plan/SKILL.md`)

Standing pre-authorization: both sentence-scale edits (uncontested on evidence).

Machinery admission: no gate, validator, lock, ledger, or ceremony is added or changed; both edits name, inside existing steps, a remedy and a producer duty that existing gates already enforce.

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

## requested-test-verification-scope

Added: 2026-10-21, investigate pass over the requested-test-scope-incomplete filing

Work-type verdict: ad-hoc-able because the fix is localized to the existing Maven test runner contract, with explicit focused and broad request forms and no open design choice about the owner (`agents/skills/unit-test-runner/SKILL.md`); the Ad-hoc backlog arm's single-surface test is met.

Origins:
- docs/history/backlog/2026-10-21-requested-test-scope-incomplete.md

Urgency: medium - a user-reported verification escaped affected test failures after a hand-selected subset ran green; the existing runner's mandatory one-class shape can repeat that omission whenever the request is broader.

Scope arms:
- Preserve the one-class command for explicitly focused requests.
- Add a broad-request path that derives all relevant classes from the changed behavior and test inventory, supports both Surefire and Failsafe selectors, and uses the repository's documented full command when the user asks to confirm no tests fail.
- Keep the result report tied to the exact command, test count, and any excluded suite; do not describe a selected subset as all tests.
- Validate both paths with realistic sample contexts per `AGENTS.md` Testing Guidelines.

Orientation: `agents/skills/unit-test-runner/SKILL.md` entered the repository in the initial skill-library commit and its current instructions still require `-Dtest=<TestClassName>`, say to execute only that class, and tell the runner to ignore caller instructions. Its description also triggers on integration tests and broad test requests, but the body has no alternate selection path. `AGENTS.md` Testing Guidelines cover skill validation and do not define implementation-test scope. The shared workflow guidance's full-suite requirement is limited to extraction, and execute-plan's full validation applies to plan execution rather than ad-hoc work.

Prompt: Update `agents/skills/unit-test-runner/SKILL.md` so caller intent selects between its focused and broad modes: keep the one-class Surefire path for a focused request; for a broader request derive affected test classes from the changed behavior and test coverage, include the correct Failsafe command when integration tests are relevant, and use the repository's documented full test command when the user asks to confirm no tests fail. Report the exact command, test count, and excluded suites. Add realistic sample-context validation showing a focused request remains narrow and a broad request does not collapse to one class; run the public hygiene scan required for skill edits.

Rejected alternatives:
- Always run the full suite: rejected because it adds unnecessary cost when a user asks for one class, while the witnessed omission shows the value of retaining a focused path (`agents/skills/unit-test-runner/SKILL.md`).
- Keep the one-class mandate and tell callers to name every class: rejected because the runner is instructed to ignore caller intent and has no broad path, the witnessed gap recorded by the origin row (`docs/history/backlog/2026-10-21-requested-test-scope-incomplete.md`).
- Add only a general rule to `AGENTS.md`: rejected because it would not repair the runner's local instruction to ignore caller instructions and execute only `-Dtest=<TestClassName>`; the witnessed behavior is in the runner itself (`agents/skills/unit-test-runner/SKILL.md`).
- Add a persisted test-scope ledger or validator: rejected because one caller-sensitive branch in the existing runner addresses the witnessed omission without another stateful check (`AGENTS.md`, Testing Guidelines; origin row above).

Machinery admission: no new gate, validator, lock, ledger, or ceremony is recommended; the witnessed scope omission is addressed by the runner's existing selection contract.

## execution-claim-release-operand-after-archive

Added: 2026-10-21, investigate pass anchored on the claim-release row filed after the certification-seal-landing-survival execution closeout

Work-type verdict: ad-hoc-able - a body-named single-surface skill-text fix in `agents/skills/execute-plan/SKILL.md` (Phase 5, the claim-removal sentence), a tracked skill surface with no guard change (the Ad-hoc backlog arm's eligibility test, `agents/skills/maintenance/decisions.md`); the claim gateway script is deliberately not edited here (see the rejected script arm).

Origins:
- docs/history/backlog/2026-10-21-execution-claim-release-archived-plan-operand.md

Urgency: low - one failed invocation per execution closeout, self-explaining (`plan operand not readable`), recovered by re-invoking with the completed path.

Scope arms:
- In the Phase 5 closeout text that names the run-level execution claim removal by its owner, state the release operand: the plan's resolved archived path (`{plans_completed_dir}/<basename>`), because Phase 4's archive rider has already moved the plan when the release runs.
- Pay growth with deletion: fold the operand clause into the existing sentence rather than adding one.

Orientation: `resolve_context` in `scripts/execution_claim.sh` (f3894756d, 2026-10-18) requires a readable plan operand before resolving the claim file, which is correct for `take`, `claim`, and `refresh` (the plan is live) and only wrong for `release` after the archive move; the claim file itself records the active path, so a caller following the recorded `plan:` line hits the refusal.

Prompt: In an ad-hoc worktree, edit the Phase 5 sentence in `agents/skills/execute-plan/SKILL.md` that names the run-level execution claim removal so it states the release invocation's operand as the archived plan path (the Phase 4 destination), with no new sentence or step; run the doing-code-review panel over the branch delta, the public-hygiene scan, and the pins suite; land per the Ad-hoc backlog arm with the origin row deleted in the same commit.

Rejected alternatives:
- Teach `release` to resolve the claim by slug or by the completed twin when the operand is absent: rejected for this entry because `scripts/execution_claim.sh` is the execution-claim gateway and the open `dead-run-resume-arm3-manifest-key-drift` entry in `docs/history/backlog/PLAN-PROMPTS.md` already opens that script for authoring; the release-operand arm folds into that plan when it authors rather than landing as a separate gateway edit (`docs/history/backlog/PLAN-PROMPTS.md`, dead-run-resume-arm3-manifest-key-drift)
- Record the completed path in the claim file at archive time: rejected because the claim file is deleted at the same closeout and no reader needs the second path (`agents/skills/execute-plan/SKILL.md`, Phase 5 claim removal)
- Release the claim before the archive rider: rejected because the claim must stand through the landing critical section so a fresh foreign claim is a guard-fire stop (`agents/skills/execute-plan/SKILL.md`, Queue-drain continuation)

Standing pre-authorization: the operand clause.

Machinery admission: no gate, validator, lock, ledger, or ceremony is added or changed; the edit names an operand for an existing step.
