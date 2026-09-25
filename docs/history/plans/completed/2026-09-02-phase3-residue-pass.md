# Plan: Phase-3 residue pass (churn-control certification and execution residuals)

Backlog origins: `docs/history/backlog/2026-09-02-phase3-churn-control-r1-review-residuals.md`, `docs/history/backlog/2026-09-02-phase3-churn-control-certification-residuals.md` (kept in place while this plan is open; they move to `{backlog_completed_dir}` at execution).

Plan review: `docs/reviews/2026-09-02-plan-review-phase3-residue-pass-r5.md` (latest, ready: yes; zero blocking, 5/5 workers) · r1-r4 staged (blocking 4, 1, 1, 0; all findings folded or dispositioned) · r5 non-blocking residuals: `docs/history/backlog/2026-09-02-phase3-residue-pass-r5-residuals.md`.

## Terms

- **Residual entry**: one numbered item in the two backlog origin files (5 certification residuals, 12 r1-review entries).
- **Counting paragraph**: the paragraph at the end of `execute-plan` Step 3.5 beginning "Every launch of a Step 3.1 review panel"; owned by `execute-plan`, summarized in the glossary Review iteration cap entry.
- **Exit-hybrid-once**: the at-most-one exit hybrid rule and its once-only allowance in `review-agents/review-panel-selection.md` "Review-loop follow-ups".
- **Mechanical audit**: the plans Validation Commands authoring rule "Mechanically re-verify exact-text contracts after every fold": extract every pinned span, verify it occurs exactly once in the prescribed target, and `bash -n` the Validation Commands block.
- **Skill-gate marker**: file `plans.<project>.<session>.marker` under `~/.ai-playbook/runtime/skill-invoked/`; `<project>` derives via the shared `facts_paths.resolve_project_key` (the ONE function both cores import) over this repository's `.ai-playbook/facts.md`; refreshed by the plans skill before every plan-file write per `agents/hooks/skill-gate/README.md`.
- **Session key**: output of `python3 ~/.ai-playbook/scripts/session_channel.py` (env-picked agent session id, empty allowed); empty-after-strip becomes the literal `no-session`.

## Assumptions

- assume certification residual cc-F2 (clear-round table mutation note) is already satisfied on disk; basis: the Step 3.4 table row "Yes, via the skip-path pass with accepted fixes | Not clean; the changed digest requires a fresh targeted review" exists and `git log -S` attributes it to the churn-control execution squash 80f8c4a.
- assume F15 (archived plan validation-block hardening) gets a frozen-history disposition with no live edit; basis: documentation-minimalism preference (outdated docs frozen as history, never reworded as current) plus the entry's own "extend the validation block only when it is reused as a template" guidance.
- assume CD-2 (Task-0 checkbox commit-message pin) gets a disposition note only; basis: the referenced plan is archived history; no live text carries the pin.
- assume the origin backlog files stay open with a status update recording this plan; basis: plans skill Backlog origin rule (keep the backlog item in place while the plan is open; the completion step moves it at execution).
- assume resolving the duplicated rule numbering as Witnesses 22->23 and Generate 23->24 (monotonic file order, with the Task-coupling rule already renumbered 24->25 by the r5-residuals plan) in `plans/SKILL.md` is safe; basis: the only numbered cross-references on disk are this plan's own validation pins plus the r5-residuals plan's reconciliation, both re-derived after the Task-coupling 24→25 renumber.
- assume at the cap-row co-hold, review-reconciliation runs before the Fix-risk direction; basis: the certification-residuals item's own suggested fix ("reconciliation detour first then Fix-risk direction"), user-authored backlog guidance.
- assume every edit is wording-only on live skill text; basis: the origin items defer non-blocking findings (r1 entry 9 excepted: an out-of-scope note adopted on its own merits; entry 12 excepted: citation hygiene, closed by Task 5) whose deferral rationale (certified-digest immutability) expired at execution and archive (main 80f8c4a).

## Gist & Examples

The churn-control machinery shipped in main 80f8c4a left 17 non-blocking residuals across two backlog files. Fifteen were deferred to avoid mutating the certified plan digest; that rationale expired when the plan was executed and archived, so this plan applies them as ordinary live-text polish in one pass, file by file. (The two exceptions: r1 entry 9 was an out-of-scope note rather than a digest-frozen deferral, adopted into Task 1 on its own merits now that the file is live-editable; r1 entry 12 was deferred for citation hygiene, which Task 5 closes.) Three honest dispositions, plus one record that the previously flagged re-entry counting debt was closed by the Task 2f rewrite:

- cc-F2 is already fixed on disk by the execution itself (the Step 3.4 skip-path digest-mutation table row) and needs no edit.
- F15's target is now an archived plan; frozen history. Its two hardenings (an absence probe for the superseded short-form clean-review row, and deny-list extension beyond the two known runtime names) are recorded as guidance for the next time that validation block is reused as a template.
- CD-2's wrong commit-message citation lives only in archived plan text; recorded, nothing to fix.
- The Task 2f rewrite closed the previously recorded re-entry counting gap: a verification-gate or timeout re-entry that re-checks or re-synthesizes without re-running workers now advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`, and `re_entry_count` reaching 3 in one round stops the loop for a user ask. Any remaining budget re-tuning (cap sizes, thresholds) stays owned by a future budget-change plan.

Example of the change class: the counting paragraph currently opens "Every launch of a Step 3.1 review panel increments `review_round`; ..." and contradicts its own re-entry exception later in the same sentence chain (F-7), scopes the ambiguous-means-absent rule to Step 3.5 only (F-9), and uses "a second re-entry" ambiguously (F14a). The plan replaces the paragraph with a split, exception-carved version whose sentences state each rule once.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every applied fix matches its finding's review analysis; every quoted span was verified against current on-disk text before pinning (authoring-time probe recorded below).
- minimality: wording-only edits; no budget, gate, or exit semantics change beyond what the findings prescribe.
- disposition honesty: every one of the 17 entries ends the pass as fixed, verified no-op, or frozen-history disposition; none silently dropped.

**Done when:**
- The full Validation Commands block exits 0 on the post-implementation tree; every absence probe that pins pre-existing text was recorded RED at authoring time on 2026-09-02, while the fold-added regression guards (2d no-ask, 2e close-clause, cap-row "then also" and "ask below" guards) are green-today by design and must remain green, and the any-exit close-rule pin is a keep-guard (green before and after Task 2f).
- `grep -c "^22\. "`, `"^23\. "`, and `"^24\. "` over `agents/skills/plans/SKILL.md` are each 1, in monotonic file order (22 Mechanical, 23 Witnesses, 24 Generate, 25 Task-coupling). The pre-state on disk carries the duplicated 22s and Witnesses/Generate at 22/23 until residue-pass Task 1 executes.
- Both backlog origin files carry a status line naming this plan and per-entry dispositions, with stale line-number anchors dropped (CD-1).
- The mechanical audit passes: each pinned span occurs exactly once in its target; `bash -n` over the Validation Commands block is clean.

**Ship when:**
- None; no deploy or external dependency (all checks are repository-verifiable).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill contract text):**
- `agents/skills/plans/SKILL.md` (rule renumber only; all other content frozen)
- `agents/skills/execute-plan/SKILL.md` (Step 3.3 gate items 4-5, Step 3.4 clear-round table row 1, Step 3.5 cap row, exit row, and counting paragraph; the routing paragraph beginning `Class membership in the two backlog-by-default classes`; all other content frozen)
- `agents/skills/review-agents/review-panel-selection.md` (Focused panels fan-out paragraph, Review-loop follow-ups bullets; all other content frozen)

**Documentation:**
- `docs/history/backlog/2026-09-02-phase3-churn-control-r1-review-residuals.md` (status + dispositions)
- `docs/history/backlog/2026-09-02-phase3-churn-control-certification-residuals.md` (status + dispositions)
- `docs/maintenance/glossary.md` (Review iteration cap entry only; all other entries frozen)

**Out of scope; reject unless plan-related:**
- `docs/plans/completed/2026-09-01-phase3-review-churn-control.md`; archived plan is frozen history (F15/CD-2 dispositions recorded in the backlog files instead).
- `scripts/validate_review_staging.py`, `scripts/summarize_review_stats.py`; no script behavior changes in this pass.
- Any other skill file; the 17 entries name only the paths above.

## Design Invariants (CR Guard)

- Preserve each residual finding's prescribed semantics exactly; these are review-validated fixes, not re-derivations. Where this plan's prescribed text differs in wording from a finding's suggestion, the finding's normative content (condition, ordering, owner, scope) must survive verbatim in meaning.
- Budgets do not weaken: the five-review total cap, full-panel budget, escalation budget, fix-risk stops, and the one-fresh-clean-review exit condition are untouched by every edit in this plan. The one deliberate stop-semantics change is the Task 2e exit-row edit (residual F14d, review-validated as an internal-contradiction fix): it removes the old text's accidental early close of standing_continue before a reconciliation detour; closure still happens at any loop exit.
- Single canonical home: the F7 relocation must move the fan-out rule, not copy it; no restated duplicate may remain under Focused panels. Tool-agnostic wording: no runtime or agent names in any edited sentence.
- Frozen history untouched: the archived churn-control plan, the docs branch history, and completed backlog items are never edited.
- Pinned spans (the expect_once/expect_absent probe strings) must not contain possessive apostrophes (plans mechanical-audit rule); every probe string below satisfies this.

## Validation Commands

Authoring-time proof (rule 19, recorded 2026-09-02 on branch `2026-09-02-phase3-residue-pass` at 93723a3): every `expect_once` pin was verified ABSENT today, and every `expect_absent` string that pins pre-existing text was verified PRESENT today (the `:638` anchor appears twice; both occurrences are dropped by Task 5), so the block is RED now and flips GREEN exactly when the tasks land. Three named exception classes, each verified at introduction: keep-guards (the any-exit close-rule pin is green before and after Task 2f because that sentence already exists on disk); count guards (the rule 23 count is a green-today invariant guarding against a left-behind duplicate, the Task 2g routing-anchor count is likewise a green-today count guard because the anchor already occurs exactly once on disk so its guard never flips, and the rule 25 Task-coupling count is a green-today regression guard because the r5-residuals plan's Task 1 already renumbered Task-coupling to 25; the rule 22 count and the rule 24 count are RED-today probes that flip green at residue-pass Task 1, when the duplicated 22s resolve and Generate takes the 24 slot, as do the Task 3a fan-out position anchors). The 2d stop-and-ask pin added by the r5-residuals plan is likewise a RED-today probe that flips green when residue-pass Task 2d executes, and the 2f re-entry-cap pins added by the r5-residuals plan are likewise RED-today probes that flip green when residue-pass Task 2f executes. The regression guards added during folds, green-today by design, must remain green (the 2d no-ask guard, the 2e close-clause guard, and the cap-row wording guards). The r1 fold replaced or added probes (Task 1 target, Task 2a item-5 opener, Task 2d reconciliation clause, Task 2f close-rule and cap-row-ask pins, Task 5 anchor probes); the r2 fold added the B1 `:639` and disposition-family pins and the 2d/2e guards; the r3 fold added the cap-row guards, the any-exit keep-guard, the Generate pin, and the disposition-family pins; the r4 fold re-worded the cap-row cell and the re-entry sentence with their pins, and each fold's probes were re-proved against the tree state at that fold (see the round staging docs).

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
EP=agents/skills/execute-plan/SKILL.md
RPS=agents/skills/review-agents/review-panel-selection.md
PL=agents/skills/plans/SKILL.md
GL=docs/maintenance/glossary.md
B1=docs/history/backlog/2026-09-02-phase3-churn-control-r1-review-residuals.md
B2=docs/history/backlog/2026-09-02-phase3-churn-control-certification-residuals.md

expect_once() {
  _f="$1"; _s="$2"
  [ -f "$_f" ] || { echo "MISSING FILE: $_f"; exit 1; }
  _n=$(grep -cF -- "$_s" "$_f")
  if [ "$_n" -eq 1 ]; then :; else echo "expect_once ($_n) in $_f: $_s"; exit 1; fi
}
expect_absent() {
  _f="$1"; _s="$2"
  [ -f "$_f" ] || { echo "MISSING FILE: $_f"; exit 1; }
  if grep -qF -- "$_s" "$_f"; then echo "expect_absent fired in $_f: $_s"; exit 1; fi
}

# Task 1: resolve the duplicated rule numbering (plans)
expect_once "$PL" '23. **Witnesses for bounded tolerances'
expect_once "$PL" '24. **Generate exact-string expectations'
expect_once "$PL" '25. **Task-coupling sweep'
test "$(grep -c "^25\. " "$PL")" -eq 1 || { echo "rule 25 count wrong"; exit 1; }
test "$(grep -c "^22\. " "$PL")" -eq 1 || { echo "rule 22 count wrong"; exit 1; }
test "$(grep -c "^23\. " "$PL")" -eq 1 || { echo "rule 23 count wrong"; exit 1; }
test "$(grep -c "^24\. " "$PL")" -eq 1 || { echo "rule 24 count wrong"; exit 1; }
expect_absent "$PL" '22. **Witnesses for bounded tolerances'
expect_absent "$PL" '23. **Generate exact-string expectations'

# Task 2a: skip-path gate item conditioned on residuals (execute-plan)
expect_once "$EP" 'when Step 3.2 left non-blocking residuals, the skip-path receiving-review pass ran'
expect_once "$EP" 'with no residuals, no pass is required and this item passes'
expect_absent "$EP" '5. On the Step 3.3-skip path, the skip-path receiving-review pass ran'

# Task 2b: gate item 4 skip-path record location
expect_once "$EP" 'in the address log when Step 3.3 launched, or in the skip-path disposition note'
expect_absent "$EP" 'path recorded on the finding or in the address log'

# Task 2c: clear-round table row 1 qualifier
expect_once "$EP" 'the pass neither accepted fixes nor mutated the digest'
expect_absent "$EP" 'or the pass fixed nothing'

# Task 2d: cap-row co-hold order (reconciliation first, then Fix-risk)
expect_once "$EP" 'but any such reconciliation still runs first), take the Fix-risk direction per Hard Gate 23'
expect_once "$EP" 'Fix-risk direction per Hard Gate 23 (a stop-and-ask)'
expect_absent "$EP" 'whether or not a reconciliation trigger holds), take'
expect_absent "$EP" 'the loop returns to Step 3.1 without the ask'
expect_absent "$EP" 'where fix-risk stop conditions then also hold'
expect_absent "$EP" 'and the ask below still happens'
expect_absent "$EP" 'take the Fix-risk direction instead, still writing the session note; where a reconciliation trigger also holds, review-reconciliation runs first, then the session note and ask'

# Task 2e: exit row closes standing_continue only on actual Phase 4 entry
expect_once "$EP" 'with the standing_continue line left open'
expect_absent "$EP" 'on actual Phase 4 entry, close any standing_continue line'
expect_absent "$EP" 'first close any standing_continue line as ended with the exit reason; where a reconciliation trigger'

# Task 2f: counting paragraph rewrite (split; exception carved out; Phase 3 scope; re-entry kind)
expect_once "$EP" 'increments `review_round`, except a verification-gate or timeout re-entry'
expect_once "$EP" 'A re-entry that re-runs workers within the same round counts as a launch too'
expect_once "$EP" 'advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`'
expect_once "$EP" 'reaches 3 within the same round, stop the loop and ask the user before any further re-entry'
expect_absent "$EP" 'A re-entry of the second kind'
expect_once "$EP" 'Phase 3 treats a standing_continue line whose session key'
expect_absent "$EP" 'increments `review_round`; `review_round` starts at 0'
expect_absent "$EP" 'Step 3.5 treats a standing_continue line'
expect_absent "$EP" 'a second re-entry that re-runs workers within the same round'
expect_absent "$EP" 'At loop exit, overwrite it as'
expect_once "$EP" 'the Step 3.5 manifest update records the round just completed'
expect_once "$EP" 'cap row then asks rather than honoring it'
expect_once "$EP" 'Any loop exit, including a user-directed stop from a stop row, closes any standing_continue line'

# Task 2g: routing paragraph split and evidence-pointer trim
expect_once "$EP" 'classify-and-record only, with evidence per `receiving-review`'
expect_absent "$EP" 'with pin and mutation evidence produced at backlog-acceptance time'
test "$(grep -c "Class membership in the two backlog-by-default classes" "$EP")" -eq 1 || { echo "routing anchor count wrong"; exit 1; }

# Task 3a: fan-out paragraph lives in Tiered ownership, not Focused panels
_ln_fanout=$(grep -n "Before staging multiple findings that one rule" "$RPS" | head -1 | cut -d: -f1)
_ln_tier=$(grep -n "^## Tiered ownership" "$RPS" | head -1 | cut -d: -f1)
_ln_consistency=$(grep -n "^### Plan and RFC" "$RPS" | head -1 | cut -d: -f1)
[ -n "$_ln_fanout" ] && [ -n "$_ln_tier" ] && [ -n "$_ln_consistency" ] || { echo "anchor missing"; exit 1; }
test "$_ln_fanout" -gt "$_ln_tier" && test "$_ln_fanout" -lt "$_ln_consistency" || { echo "fan-out not in Tiered ownership"; exit 1; }
test "$(grep -c "Before staging multiple findings that one rule" "$RPS")" -eq 1 || { echo "fan-out duplicated"; exit 1; }

# Task 3b: exit-rule clause name-based, not positional
expect_once "$RPS" 'once-only allowance of the at-most-one exit hybrid rule'
expect_absent "$RPS" 'exit-hybrid-once rule below'

# Task 3c: clear-candidate hybrid bound
expect_once "$RPS" 'the same single exit hybrid the once-only allowance permits, never an additional pass'

# Task 3d: exit-hybrid lens list and full-panel exemption both branches
expect_once "$RPS" 'in both branches the exit hybrid is still required'
expect_absent "$RPS" 'typically design-simplicity and risk'

# Task 3e: once-only reset trigger widened to any digest-mutating address pass
expect_once "$RPS" 'resets when any address pass after the hybrid mutates the digest'
expect_absent "$RPS" 'resets when a hybrid finding re-enters the address path'

# Task 4: glossary entry trimmed to definition plus owner cite
expect_once "$GL" 'Counting, stop, and standing-instruction semantics are owned by execute-plan Step 3.5'
expect_absent "$GL" 'this lift does not extend to any other stop row'
expect_absent "$GL" 'is closed out (marked ended with the exit reason) when the loop exits'

# Task 5: backlog statuses name this plan and record dispositions
expect_once "$B1" 'plan created 2026-09-02'
expect_once "$B2" 'plan created 2026-09-02'
expect_once "$B1" 'frozen-history disposition'
expect_once "$B2" 'already satisfied on disk'
expect_absent "$B1" 'execute-plan/SKILL.md:502'
expect_absent "$B1" ':638'
expect_absent "$B1" 'Status: open'
expect_absent "$B2" 'Status: open'
expect_absent "$B1" ':639'
expect_once "$B1" 'prescribed into Task 4'
expect_once "$B2" 'prescribed into the plan tasks'
expect_once "$B1" 'F14, F6, F7, CC-1'
expect_once "$B2" 'the other four residuals as prescribed into the plan tasks'
```

### Task 1: Resolve the duplicated rule numbering in plans

Files:
- `agents/skills/plans/SKILL.md`

The Validation Commands authoring rules list contains two rules numbered "22." ("Mechanically re-verify exact-text contracts after every fold" and "Witnesses for bounded tolerances overstep the bound dimension alone"). A repo-wide grep shows zero numbered cross-references, so renumber the second occurrence.

- [x] In `agents/skills/plans/SKILL.md`, resolve the duplicate rule numbering monotonically: change the rule opening `22. **Witnesses for bounded tolerances overstep the bound dimension alone:**` to `23. **Witnesses for bounded tolerances overstep the bound dimension alone:**`, and change the rule opening `23. **Generate exact-string expectations by running the prescribed transform:**` to `24. **Generate exact-string expectations by running the prescribed transform:**`. The file's rule order stays monotonic (22, 23, 24) and no rule content changes. No other byte changes in this file.
- [x] Run → expect RED before the edit, GREEN after: `test "$(grep -c '^22\. ' agents/skills/plans/SKILL.md)" -eq 1 && grep -q '^23\. \*\*Witnesses' agents/skills/plans/SKILL.md && grep -q '^24\. \*\*Generate' agents/skills/plans/SKILL.md`
- [x] Commit: `skills: renumber duplicated plans rule 22 (Witnesses to 23, Generate to 24)`

### Task 2: execute-plan residue fixes

Files:
- `agents/skills/execute-plan/SKILL.md`

Apply the seven sub-edits in one pass over the current file. Each OLD string below was verified present exactly once at authoring time.

- [x] **2a (R-2, gate item 5)** in the Step 3.3 verification gate, replace item 5:

    OLD: `5. On the Step 3.3-skip path, the skip-path receiving-review pass ran and every valid unfixed finding carries a durable backlog item, recorded in a short disposition note appended to `manifest.md` (finding, fixed or deferred, backlog item path); items 1-3 apply only when Step 3.3 launched, and on the skip path this item governs.`

    NEW: `5. On the Step 3.3-skip path, when Step 3.2 left non-blocking residuals, the skip-path receiving-review pass ran and every valid unfixed finding carries a durable backlog item, recorded in a short disposition note appended to `manifest.md` (finding, fixed or deferred, backlog item path); with no residuals, no pass is required and this item passes; items 1-3 apply only when Step 3.3 launched, and on the skip path this item governs.`

- [x] **2b (cc-F1, gate item 4)** replace `(path recorded on the finding or in the address log)` with `(path recorded on the finding, in the address log when Step 3.3 launched, or in the skip-path disposition note)`.
- [x] **2c (r5 R-1, Step 3.4 row 1)** replace `| No (no address pass ran, or the pass fixed nothing) |` with `| No (no address pass ran, or the pass neither accepted fixes nor mutated the digest) |`.
- [x] **2d (ds-F1, cap row)** in the Step 3.5 table row beginning `` | `review_round` has reached `max_review_rounds` ``, replace the action cell after the leading `Stop; ` with:

    `where a reconciliation trigger also holds, review-reconciliation runs first, then a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) is written and the user ask happens (reconciliation changes which digest the next round reviews, not whether the user is asked); where fix-risk stop conditions also hold (their direction is taken whether or not a reconciliation trigger holds, but any such reconciliation still runs first), take the Fix-risk direction per Hard Gate 23 (a stop-and-ask) and fold the budget question (continue, backlog non-blocking residuals, standing continue, or stop) into that single ask rather than issuing both, still writing the short session note; otherwise write a short session note under `{tmp_dir}/` (rounds run, unresolved residuals by class, backlog items written, whether exit coverage per `review-panel-selection` has run) and ask the user whether to continue, backlog non-blocking residuals, give a standing continue instruction, or stop; archiving with unresolved blocking findings additionally requires the user's explicit documented acceptance`

- [x] **2e (F14d, exit row)** in the Step 3.5 clean-exit table row, replace `Proceed to Phase 4; first close any standing_continue line as ended with the exit reason; where a reconciliation trigger also holds, review-reconciliation runs first, and if it changes the digest or staged artifacts, the clean review is no longer fresh and the loop returns to Step 3.1` with `Proceed to Phase 4; where a reconciliation trigger also holds, review-reconciliation runs first, and if it changes the digest or staged artifacts, the clean review is no longer fresh and the loop returns to Step 3.1 with the standing_continue line left open` (the any-exit close rule in the counting paragraphs owns closure on actual Phase 4 entry; this row does not restate it).
- [x] **2f (F-7 + F-9 + F14a + ds-F2, counting paragraph)** replace the entire paragraph beginning `Every launch of a Step 3.1 review panel increments` with these three paragraphs:

    `Every launch of a Step 3.1 review panel increments `review_round`, except a verification-gate or timeout re-entry that re-checks or re-synthesizes the same round's staging doc without re-running workers. `review_round` starts at 0, so the initial review is round 1. A relaunch that starts a new review round (a next `-r<N>` staging doc) counts as a launch. A re-entry that re-runs workers within the same round counts as a launch too; it is tracked as `re_entry_count` in the manifest (reset each round) and continues the same round's `-r<N>` staging doc as an appended pass, so staging-doc numbering and `review_round` may diverge after a counted re-entry. Such an uncounted re-entry advances neither `review_round` nor the `-r<N>` staging doc but still increments `re_entry_count`. When `re_entry_count` reaches 3 within the same round, stop the loop and ask the user before any further re-entry (a mid-round stop: no session note is required, and a standing continue instruction does not lift this stop). A counted re-entry advances `review_round` while continuing the same round's `-r<N>` staging doc; it does not start a new round and does not reset `re_entry_count`. The `max_review_rounds` cap compares `review_round` only, which each counted launch advances; the re-entry stop above is a separate guard and is not a `max_review_rounds` cap stop.`

    `A standing instruction from the user for this loop (for example, continue until clean) lifts only the `max_review_rounds` cap stops until the loop exits. Record it in `manifest.md` as a `standing_continue` line with its scope, the granting run's session key, and a loop-instance id (branch plus loop start timestamp) when first applied. Phase 3 treats a standing_continue line whose session key or loop-instance id differs from the current run as absent; the Step 3.5 cap row then asks rather than honoring it (ambiguous means absent; a loop resumed in a new session therefore re-asks, which is the intended recovery).`

    `The full-panel and escalation budgets are unchanged and continue to apply alongside this cap; the Step 3.5 manifest update records the round just completed and never advances the counter. Any loop exit, including a user-directed stop from a stop row, closes any standing_continue line as `standing_continue: ended` with the exit reason.`

- [x] **2g (F6, routing paragraph)** replace the paragraph beginning `Class membership in the two backlog-by-default classes` with two paragraphs:

    `Class membership in the two backlog-by-default classes defined by `receiving-review` (sibling-doc restatement, duplicate unit witness) is decided by the receiving-review pass (sub-agent or inline) during Step 3.3 triage, never by the orchestrator here; a blocking candidate still takes the Fix-risk blocking re-evaluation and is never silently backlogged.`

    `When Step 3.2 shows no unresolved blocking findings and Step 3.3 is skipped, the orchestrator still routes non-blocking residuals through a receiving-review pass (which may run inline) applying the owner rules per `receiving-review`; the pass fixes findings it does not defer (mutating the digest and restarting the fresh-review rule), and deferred findings (the two classes, user-deferred, scope-dropped) become durable backlog items per `receiving-review` **Backlog capture** (for the two classes, pointer-cleanup and family-completeness items) before the clean row may exit. Deferrals of the two classes are classify-and-record only, with evidence per `receiving-review`.`

- [x] Run → expect GREEN for the Task 1-2 probes in the Validation Commands block (Task 1 probes are GREEN at this point; Tasks 3-5 probes are still RED; scope the interim run to the Task 1-2 sections).
- [x] Commit: `skills: execute-plan residue fixes (skip-path gate scope, cap-row order, counting paragraph, routing trim)`

### Task 3: review-panel-selection residue fixes

Files:
- `agents/skills/review-agents/review-panel-selection.md`

- [x] **3a (F7 relocation)** cut the paragraph `Before staging multiple findings that one rule's restatement explains, list the living restatements of the rule; ...` (currently the last paragraph before the `### Review-loop follow-ups` subsection under `## Focused panels`) and paste it unchanged, as its own paragraph, immediately before the `### Plan and RFC `consistency` ownership` heading (the last paragraph of `## Tiered ownership (dedup, not discard)` preceding that subsection). Move, do not copy; no duplicate may remain.
- [x] **3b (testing-F1)** replace `exit coverage additionally follows the exit-hybrid-once rule below.` with `exit coverage additionally follows the once-only allowance of the at-most-one exit hybrid rule in this section.`
- [x] **3c (CC-1)** in the bullet beginning `- Before loop **exit**, if the clear-candidate round would omit`, change `include it in a hybrid pass (see `review-loop` exit criteria).` to `include it in a hybrid pass (see `review-loop` exit criteria); this coverage is the same single exit hybrid the once-only allowance permits, never an additional pass.`
- [x] **3d (F14b)** in the exit-hybrid bullet, replace `(the missing quality-bar lenses, typically design-simplicity and risk)` with `(the missing quality-bar lenses, typically design-simplicity)` and replace `when the plan has no production paths, any blocking-clean round satisfies that precondition and the exit hybrid is still required before` with `when the plan has no production paths, any blocking-clean round satisfies that precondition; in both branches the exit hybrid is still required before`.
- [x] **3e (F14c)** replace `The exit-hybrid once-only allowance resets when a hybrid finding re-enters the address path, so the post-fix exit attempt again requires coverage.` with `The exit-hybrid once-only allowance resets when any address pass after the hybrid mutates the digest, so the post-fix exit attempt again requires coverage.`
- [x] Run → expect GREEN for the Task 1-3 probes (fan-out position check inclusive); Task 4-5 probes are still RED; scope the interim run to the Task 1-3 sections.
- [x] Commit: `skills: review-panel-selection residue fixes (fan-out home, exit-hybrid bounds and placement)`

### Task 4: glossary trim

Files:
- `docs/maintenance/glossary.md`

- [x] In the `**Review iteration cap**:` entry, replace the entire entry body (everything after the `**Review iteration cap**:` heading line and before the `_Avoid_:` line) with the NEW entry body below. Keep the `_Avoid_:` line unchanged.

    NEW entry body: `The total count of review rounds in one execute-plan Phase 3 loop, counting full-panel and focused rounds alike, stated as the `max_review_rounds` budget (default 5) in the execute-plan Review end condition table. Counting, stop, and standing-instruction semantics are owned by execute-plan Step 3.5.`

- [x] Run → expect GREEN for the Task 1-4 probes; Task 5 probes are still RED; scope the interim run to the Task 1-4 sections.
- [x] Commit: `docs: trim glossary review-iteration-cap entry to definition plus owner cite`

### Task 5: backlog statuses and dispositions

Files:
- `docs/history/backlog/2026-09-02-phase3-churn-control-r1-review-residuals.md`
- `docs/history/backlog/2026-09-02-phase3-churn-control-certification-residuals.md`

- [x] In both files, replace the `Status:` line with: `Status: plan created 2026-09-02 (docs/plans/2026-09-02-phase3-residue-pass.md, branch 2026-09-02-phase3-residue-pass); file moves to backlog/completed/ when that plan executes.`
- [x] In the r1-residuals file: drop the stale line-number anchors in entry 7 (`execute-plan/SKILL.md:502/:638`) and the `:638 ... (now :639)` mentions in entry 12's item (a) (CD-1 citation hygiene), and append a short `## Dispositions (2026-09-02)` section recording: entry 4 (F15) and CD-2 are frozen-history dispositions (archived plan; the two validation-block hardenings apply when the block is reused as a template; the Task-0 commit-message citation is historical); entry 8 (F-10/DS-3) is prescribed into Task 4 (glossary trim); CD-1 is satisfied by this edit (the entry 7 and entry 12 line-number mentions are dropped here); entries 9, R-2, F-7, F-9, F14, F6, F7, CC-1, and r5 R-1 (entry 11, Step 3.4 row 1) are prescribed into the plan tasks above.
- [x] In the certification-residuals file: append the same `## Dispositions (2026-09-02)` section recording cc-F2 as already satisfied on disk by the churn-control execution squash (Step 3.4 skip-path digest-mutation table row) and the other four residuals as prescribed into the plan tasks.
- [x] Run → expect GREEN for the Task 5 probes.
- [x] Commit: `backlog: record residue-pass plan reference and dispositions`

### Task 6: full validation and mechanical audit

- [x] `bash -n` over the plan's Validation Commands block content; fix any syntax defect in the same edit.
- [x] Run the full Validation Commands block → expect GREEN on the post-Task-5 tree (every probe green; no interim scoping).
- [x] Mechanical audit: extract each pinned span from Tasks 1-5 and confirm it occurs exactly once in its target file (the expect_once probes already enforce this; confirm no pin was edited after the last green run).
- [x] Commit via the done workflow (learn, gates, docs-branch) or `plans: certify phase3 residue pass` if nothing new to commit.

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-02-phase3-residue-pass-r5-residuals.md: disposition folded into 2026-09-02-phase3-residue-pass.md (2026-09-25); per-item file deleted.
