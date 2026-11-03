# Plan: Memory index load-budget consolidation

Authoring claim: memory-index-load-budget-consolidation.md (session sess_fa4273f5-30c1-454b-afee-5683f68c33f4)

Backlog origin: docs/history/backlog/2026-10-31-memory-index-load-budget-consolidation.md
Driving force: efficiency + token-usage
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-memory-index-load-budget-consolidation-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1h total, largest task 0.5h

## Terms

- Memory store: the per-project memory directory under the user-level store (`~/.zcode/cli/memories/projects/<project-key>/memory/`, recorded tilde-form only), holding `MEMORY.md` beside its topic files; operator-owned session context outside this repository's tracked trees.
- Memory index (`MEMORY.md`): the store's index file the runtime loads into session context each session.
- Load budget: the byte-bounded budget of index content the runtime loads per session, measured at roughly 25 KB: witnessed line cuts are 111 of 450 lines (2026-10-31 audit, truncation at line 112, no byte figure recorded), 94 of 543 (2026-11-02 scheduler witness, truncation at line 95), and 95 of 570 (the authoring session's own 2026-11-02 load); the authoring session measured 25,166 of 140,055 bytes over its loaded 95 lines, and 28,971 bytes over the first 112 lines of the then-current 570-line file at the 2026-10-31 cut position (that witness loaded 111 lines, so the probe spans one line past its cut); both byte figures are that session's live measurements, proxies rather than witnessed records; the load budget is a runtime property, not a line count, and line figures are proxies only.
- Topic file: any `.md` memory file in the store beside `MEMORY.md`.
- Do-not-redo marker: a durable index or topic-file record telling later sessions not to re-execute landed work.
- Index-rather-than-prune: the store convention that a doubtful record gets an index pointer, never deletion; in doubt stays.
- Time-supersession: a record whose current state is already carried by a newer index entry or the repository's durable home set of git-tracked surfaces (archived plans, git history); the scheduler state file is corroborating evidence only and never the sole carrier.
- Per-mandate summary line: one index line summarizing the durable outcome of a completed maintenance mandate, replacing the several per-run outcome lines it supersedes.
- Retirement rule: the standing write-discipline complement to the append-first convention defining when and how a superseded index line retires.
- Whole-load witness: a fresh session's runtime context carrying the index's final line with no truncation notice; the binding verification that the load budget holds.
- Lane-quiet window: a period in which the run's observable claim surfaces (the run claim file and the scheduler state file's fresh missing-outcome entries) show no active writer; writers outside these observable surfaces are handled by the index-write drift check.
- Append-first convention: the maintenance-side memory-write discipline (one-line entries added at the end of the index) whose home is the memory-write convention paragraph in the maintenance overlay; the retirement rule is its complement.
- Lane state record: the audit lane's state record (`.ai-playbook/maintenance/memory-index-audit.json`), the required record surface for the consolidation run's verification outcomes (the run claim file lives beside it).
- Consolidation run: the operator-approved one-time ad hoc run this plan's charter defines, executing the fold, prune, and verification battery.
- Maintenance overlay: the maintenance skill's runtime overlay in this repository (`agents/skills/maintenance/`), home of the memory-write convention.
- Origin row: the backlog row this plan was authored from, the Backlog origin path in the header.
- Pointer integrity: the lane's check that every index pointer (a line carrying a Markdown link to a topic file) resolves; zero dangling means every pointer resolves.
- Fold: the consolidation pass that retires superseded index lines into per-mandate summary lines.
- Durable signal: the store's durable classification, content that outlives its writing conversation; the property a prune row's captured-signal citation must name.
- Do-not-redo survival audit: the battery member verifying the reachable home of every do-not-redo marker whose index line the fold retired or rewrote, every prune-deleted file's marker, and every newly unindexed file.

## Why

The per-project memory index measures 570 lines / 140,055 bytes, while the runtime loads only about 25 KB of it: the 2026-11-02 witness carried 94 of 543 lines, and this session's own load carried 95 of 570. Everything past the cut is silently absent from context, including do-not-redo markers and standing preferences, which is a redo risk for the fleet this repository runs. The store grows roughly 46 index lines per day (the origin row's recorded witness: 450 lines at the 2026-10-31 audit to 543 at the 2026-11-02 re-witness) because the append-first write convention has no retirement half: superseded per-run outcome entries accumulate forever. The operator approved the one-time consolidation on 2026-11-02.

## Gist & Examples

TLDR: the memory index gains a standing retirement rule and a one-time operator-approved consolidation run, so the whole index fits the runtime's byte-bounded load budget and durable markers stop being truncated away, for efficiency and token-usage.

Before (today): a maintenance session that landed a plan appends its one-line outcome entry to the index and moves on. Its predecessor's line for the same mandate stays. After months of this the index is 570 lines and 140 KB; the runtime loads the first 25 KB and cuts the rest; a session whose tail never loads can re-execute a landed plan or re-file a filed row because its do-not-redo marker sat past the truncation cut. A reviewed prune deletes a topic file while its index line survives, leaving a dangling pointer (witnessed today: the `exec-praudit-completion-pass-landed-e5d1c93e48-20261031.md` line resolves to no file).

After (this plan): every maintenance-side memory write carries the retirement discipline, so a line superseded by a newer record folds into it in the same targeted edit, and a topic-file deletion removes the lines pointing at it in the same change. The store's accumulated supersession is cleared once by an operator-approved consolidation run: per-run outcome lines retire into per-mandate summary lines, durable still-current records gain one-line pointers, and reviewed topic-file prunes run only where the compressed index plus the repository's own durable records already capture every byte of durable signal. Post-run a fresh session's whole-load witness carries the index's final line, pointer integrity reads zero dangling except recorded exceptions, and every touched do-not-redo marker (lines the fold retired or rewrote, prune-deleted files, newly unindexed files) has a verified reachable home.

Edge cases:
- A line in doubt (not provably time-superseded) stays: index-rather-than-prune holds inside the consolidation too.
- A topic file whose live do-not-redo marker a lane still depends on is never deleted unless the marker's durable signal is captured by the compressed index or the repository's durable records.
- A run-completion record whose state is carried by archived plans and git history (git-tracked surfaces) is time-superseded even though its own file is durable by classification; the scheduler state file corroborates but never alone carries a retirement; the fold retires its index line, the prune may then delete the file.
- A concurrent maintenance session appending to the index mid-fold: the run runs only in a lane-quiet window, and the charter's index-write drift check re-reads the index before each of the run's index writes, so an append observable at write-preparation time is detected and reported; the residual replace-window race (an append landing after the re-read, before the replace) is not claim-fenced, and the charter's post-run reconciliation arm re-appends any line it dropped and reports the reconciliation in the lane state record.

## Outcome

Every maintenance session loads the whole memory index within the runtime's byte-bounded load budget, so every do-not-redo marker and standing preference the store holds is present in context, and the store stops regrowing past the budget.

- The append-first write convention gains its retirement half, so superseded entries stop accumulating.
- A one-time operator-approved consolidation run brings the live index within the load budget with zero dangling pointers and a verified do-not-redo survival audit.
- The next memory-index-audit lane run (next due 2026-11-07) re-measures with a whole-load witness instead of filing the same over-budget finding.

Gate delta: none (all three tasks amend convention and procedure text only; no gate, validator, lock, ledger, refusal class, or dispatch-pausing condition is added or removed).

## Assumptions

- assume the operator approval recorded 2026-11-02 in the authoring session satisfies the origin row's operator gate for authoring this plan and for chartering the consolidation run; basis: the operator's explicit approval answer in this session.
- assume the load budget is the runtime's index-loader property, bounded (consistent with a byte- or token-bounded loader) and not repository-configurable, so the fix is store-side, never a budget raise; basis: the witnessed truncation cuts restated per the Terms convention (25,166 bytes over the loaded 95 lines on 2026-11-02; 28,971 bytes over the first 112 lines at the 2026-10-31 cut position), both authoring-session measurements; the whole-load witness remains the only binding check.
- assume the origin row's roughly 200-line load-budget figure is a line-count proxy contradicted by its own truncation witnesses (a 200-line index of this store's line lengths is about 50 KB, roughly twice the witnessed byte cut), so the plan rewrites the operative target to the whole-load witness with the byte figure as the proxy; basis: this session's byte measurements at both witnessed cut points; recorded as the origin-acceptance rewrite the plans skill requires.
- assume the measured basis for the consolidation is the 2026-11-02 fresh measurement in this authoring session (570 lines, 140055 bytes, 1537 topic files, 569 pointers, 1 dangling pointer) superseding the origin row's 2026-10-31 values; basis: direct measurement of the store this session.
- assume the store path resolves per the audit lane's Store locator clause and is recorded tilde-form only in committed files; basis: docs/maintenance/recurring-tasks/memory-index-audit.md.
Decision points requiring a grill: memory-store consolidation operator gate: approved by operator 2026-11-02 in this authoring session (explicit approval answer; the entry's operator-gated scope); affected: Why, Tasks 2-3.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the retirement rule text covers both decay directions (superseded-line accumulation and index-line-left-behind-after-file-deletion) and names the in-doubt and live-marker refusals; the run charter's verification battery verifies the operative outcome (the whole-load witness), not only a line proxy.
- maintainability: the convention amendment lives in the append-first convention's existing home, not a parallel doc; the run charter lives in the lane's procedure-of-record file.
- safety: the store is never machine-mass-edited; every deletion is individually reviewable, reversible from a pre-run backup, and operator-approved row by row.

**Done when:**
- The retirement rule text is present in the maintenance overlay and the existing pins suite stays green over the pinned maintenance files.
- The lane task file carries the consolidation run charter with the lane-quiet window check, the dry-run approval gate, the index-write drift check, the verification battery (whole-load witness, byte proxy, pointer integrity, do-not-redo survival audit), and the rollback posture.
- Public hygiene scan and em-dash added-lines gate pass over the changed set.

**Ship when:**
- The operator-approved consolidation run executes per the Task 2 charter in a lane-quiet window and records its verification battery outcomes in the lane state record; evidence owner: the operator-approved consolidation session; closure condition: a fresh session's whole-load witness carries the index's final line, pointer integrity reads zero dangling (recorded exceptions excepted), and the do-not-redo survival audit is clean, re-measured by the next audit lane run (class: OPERATIONS_FOLLOW_UP).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/zcode.md` (Task 1)

**Documentation:**
- `docs/maintenance/recurring-tasks/memory-index-audit.md` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The user-level memory store itself; operator-owned session context, touched only by the Ship-when consolidation run, never by this plan's tasks.
- `docs/history/backlog/PLAN-PROMPTS.md`; the rolling log's write discipline is owned by the log's own rules and the monitor duties, not this plan.

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base <branch point this run started from>
```

### Task 1: Standing retirement rule (the append-first convention's missing half)

Context surface: the plan's Terms, this task, and the existing append-first convention text in the maintenance overlay.

Files:
- `agents/skills/maintenance/zcode.md`
- `docs/maintenance/recurring-tasks/memory-index-audit.md`

- [ ] Add the standing retirement rule to the maintenance overlay's memory-write convention home in `agents/skills/maintenance/zcode.md`, as clauses beside the append-first one-line-entry paragraph, extending that paragraph's sanctioned targeted edits enumeration to name the supersession fold, and recording the operator-approved consolidation run as the sanctioned exception to the paragraph's wholesale-rewrite ban [class: IMPLEMENTATION_REQUIRED]
- [ ] Clause (a) supersession fold: a new record that supersedes an existing entry's carried value folds the superseded line's still-durable signal into the successor line, or into a per-mandate summary line, in the same targeted edit that records the successor [class: IMPLEMENTATION_REQUIRED]
- [ ] Clause (b) deletion pairing: a change that deletes a topic file removes every index line pointing at that file in the same change [class: IMPLEMENTATION_REQUIRED]
- [ ] Clause (c) reviewed shape: retirement is reviewed, never bulk, and an entry in doubt stays (index-rather-than-prune) [class: IMPLEMENTATION_REQUIRED]
- [ ] Clause (d) live-marker refusal: a line whose live do-not-redo marker or standing preference a lane still depends on is never retired unless its durable signal is captured by the successor line or the repository's durable records [class: IMPLEMENTATION_REQUIRED]
- [ ] Clause (e) write-time supersession: a new record whose durable signal is already carried by git-tracked surfaces (archived plans, git history) folds into a per-mandate summary line or skips the append in the same targeted edit, rather than adding a new line [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a one-line pointer in `docs/maintenance/recurring-tasks/memory-index-audit.md` (the Filing rule or a neighboring clause) naming the retirement rule as the standing complement the lane's recommendation cites, so the lane's future filings reference one home, and aligning the Filing rule's lane-quiet window parenthetical with the Terms definition [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend the lane task file's Measure-and-check Load budget clause to measure the byte-bounded budget with the whole-load witness as the binding check (byte and line counts as proxies) and record the witness outcome in the state record [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `bash scripts/check_maintenance_pins.sh` and expect exit 0 (the edit touches a pinned maintenance file; the suite's existing pins must stay green); run `bash scripts/scan-public-hygiene.sh` over the changed set and expect exit 0; treat any skill-text-budget breach line in the pins output as a failure to repair, keeping the file under its `scripts/skill_text_budget_caps.json` cap [class: REPOSITORY_TEST]
- [ ] Commit: `docs: add retirement rule complement to the memory-write convention` [class: IMPLEMENTATION_REQUIRED]

Safety witness: given a retirement pass that cannot establish whether a superseded line's durable signal survives in the successor or the repository's durable records, expects the rule text's in-doubt clause to keep the line (index-rather-than-prune), never a deletion.

### Task 2: Consolidation run charter (the operator-approved one-time run)

Context surface: the plan's Terms, this task, and the lane task file's existing Filing rule and State record sections.

Files:
- `docs/maintenance/recurring-tasks/memory-index-audit.md`

- [ ] Add an `Operator-approved consolidation run (ad hoc)` section to `docs/maintenance/recurring-tasks/memory-index-audit.md` specifying the run the operator approved on 2026-11-02 [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, lane-quiet window check: read from the observable claim surfaces (the claim file below and the scheduler state file's fresh missing-outcome entries, parks and retained pendings excepted): none may stand before any mutation; unobservable writers are handled by the drift check and post-write verification [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, run claim: the session acquires its claim by a noclobber create of a dedicated claim file beside the lane state record, failing closed if one stands, recording the owning session id so a dead run's leftover claim is distinguishable; removed when the run ends [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, fold arm: classify current index entries; time-superseded per-run outcome entries retire into per-mandate summary lines; durable still-current records without pointers gain one-line pointers; a dangling pointer on a non-superseded line gets an explicit disposition: repair the target, retire the line when its signal is git-tracked-carried, or record it as a known exception [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, fold target: bring the post-run index at or under 20,000 bytes, headroom below the 25,166-byte witnessed cut; basis: the Task 1 retirement rule collapses the witnessed roughly 46-lines-per-day growth to an append-only residual, the growth assumption this charter records; if the next lane re-measurement still reads over budget, the Filing rule re-files and the operator may approve a second window [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, prune arm: reviewed per file, never bulk; delete a topic file only when its entire durable signal is captured by the compressed index or a git-tracked durable surface; the scheduler state file never alone authorizes a deletion; in doubt stays [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, dry-run gate: a row-by-row presentation naming each retired line, each new pointer, and each proposed deletion with its captured-signal citation, approved by the operator before any store mutation; deletions execute only on explicit per-row approval [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, index-write drift check: before each of the run's index writes, re-read the index and compare against the prepared read; first drift: re-derive and retry once; second drift: abort, record fold not applied with the landed-write count, re-attempt only after fresh operator approval [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, post-write verification: after each index replace, re-read and confirm the written content is exactly present, reporting any unaccounted tail beyond its byte length; on a mismatch abort further mutations, restore lost lines from the pre-write read or record a reconciliation line, and report in the lane state record [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, post-run reconciliation: at run end, re-read the index and diff it against the union of the pre-run read and every per-write prepared content; re-append any concurrent line a replace dropped and report the reconciliation in the lane state record [class: IMPLEMENTATION_REQUIRED]
- [ ] Charter member, deletion freshness re-check: before the deletion batch, re-verify each approved row's file state and captured-signal citation against a fresh index read; skip any row whose premise changed and report the skip [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same section, state the run's execution route: ad hoc per the operator's recorded rescope and never rewriting the index mid-lane, per the Filing rule above; the consolidation session records its verification outcomes in the lane state record for the next audit run to re-measure; the whole-load witness is supplied by a fresh operator-opened session after the final write or recorded pending for the next lane run [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: charter the operator-approved memory index consolidation run` [class: IMPLEMENTATION_REQUIRED]

Gates over Tasks 1-2's changed sets are deferred to Task 3's final-state run, the last edit to the pinned lane file.

Safety witness: given a proposed deletion whose captured-signal citation cannot name a reachable home for the file's do-not-redo marker, expects the charter's prune arm to refuse the row (in doubt stays) and the dry-run presentation to omit it, before any store mutation.

### Task 3: Charter verification battery and rollback posture (the run's acceptance surfaces)

Context surface: the plan's Terms, the Task 2 charter section, and the lane task file's existing State record clause.

Files:
- `docs/maintenance/recurring-tasks/memory-index-audit.md`

- [ ] In the charter section, specify the verification battery: a fresh session's whole-load witness carrying the index's final line with no truncation notice; the index byte count at or under the 20,000-byte proxy target; pointer integrity zero dangling except recorded exceptions [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same section, specify the survival audit: name every do-not-redo marker whose index line the fold retired or rewrote, every topic file the prune deleted, and every topic file newly unindexed, each with its reachable home (compressed index or git-tracked durable surface) [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same section, specify the rollback posture: a pre-run backup of the memory index file and every to-be-deleted topic file into a dated sibling directory outside the loaded memory directory, so every deletion is individually reviewable and reversible; the run verifies the backup copy matches the source by digest before any mutation, and a post-abort restore is never applied blindly over a drifted-forward index [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same section, specify atomic store writes: the fold's index write and every state-record update use the temp-file-plus-atomic-replace shape the lane's existing State record clause prescribes, so a death mid-write leaves either the prior bytes or the complete new ones [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `bash scripts/check-no-em-dash.sh added-lines --base <branch point this run started from>` over the changed set and expect exit 0; run `bash scripts/check_maintenance_pins.sh` and `bash scripts/scan-public-hygiene.sh` and expect exit 0 over the post-edit tree (Task 3 edits a pinned file last; the final state must pass the gates) [class: REPOSITORY_TEST]
- [ ] Commit: `docs: charter verification and rollback surfaces for the consolidation run` [class: IMPLEMENTATION_REQUIRED]

Safety witness: given a run whose backup copy is unreadable, expects the rollback posture to halt before any store mutation.

## Residual findings (cap closure)

Series terminal state at the configured round cap: the loop exits through the cap-closure terminal shape with operator authorization recorded at the 2026-11-03 reflection checkpoint. Every r5 staged finding's outcome is listed below; the r5 record pair in the reviews staging home stays authoritative for verdicts, counts, and triage. The corrections landed in the reconciliation commit a352384c1 on the authoring branch and were not panel-verified, a verification round exceeding the series' configured cap; the execution-time surfaces of Tasks 2-3 (dry-run gate, post-write verification, post-run reconciliation arm, rollback posture) bound the residual risk where it matters.

- F1 security#replace-window-silent-loss (Medium, was blocking): disposition: folded - the run claim's exclusivity attribution is deleted, the post-write tail measure re-scoped beyond the written content's byte length, and the post-run reconciliation arm added (diff against the union of the pre-run read and every per-write prepared content, concurrent lines re-appended).
- F2 security#survival-audit-scope-gap (Medium, was blocking): disposition: folded - the survival audit names the prune-deleted class, and the touched-set scope aligns the Terms and Gist surfaces.
- F3 quality#acceptance-criteria-internal-conflict (Medium): disposition: folded - the fold arm's recorded-exception clause and the battery's "zero dangling except recorded exceptions" acceptance surface now agree.
- F4 security#weak-backup-verification (Medium): disposition: folded - the rollback posture verifies the backup copy against the source by digest before any mutation.
- F5 security#invariant-conflict-unreconciled (Medium): disposition: folded - Task 1's retirement rule carries the consolidation-run exception to the overlay's standing wholesale-rewrite ban.
- F6 architecture#ownership-gap (Low): disposition: folded - the execution route charters a fresh operator-opened session as the whole-load witness supplier, with a recorded-pending fallback for the next lane run.
- F7 consistency#derived-figure-drift (Low): disposition: folded - the Assumptions figure now reads about 50 KB with its derivation recorded.
- F8 testing#gate-deferral-undescribed (Low): disposition: folded - the deferral prose names Tasks 1-2's changed sets as riding to Task 3's final-state gate run.
- F9 documentation#review-scope-annotation (Low): disposition: accepted - declined with reason: the readiness validator's Review Scope vocabulary admits only the singular "(Task N)" annotation form, so the multi-task ownership stays documented in the r5 record's overflow rows.
