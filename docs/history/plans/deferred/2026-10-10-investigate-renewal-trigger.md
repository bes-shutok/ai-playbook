# Plan: Investigate renewal trigger on origin-row rescope (the unowned lifecycle stage)

Backlog origin: docs/history/backlog/2026-10-08-investigate-renewal-trigger-on-row-rescope.md (the PLAN-PROMPTS entry `investigate-renewal-trigger` carries the operator-confirmed prompt)
Driving force: automation
Design input: the witnessed sequence (the memory-index row rescoped at commit 2a5962888, the entry amended by targeted edit only, the fresh anchored pass at 5251042ca materially reshaping the prompt - an outcome the amendment could not have produced, caught only by the operator's compliance ask); the freeze and prune rules that own the other two lifecycle stages
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-investigate-renewal-trigger-r*.md (created by this plan's review loop, r1 onward; the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-investigate-renewal-trigger.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

## Terms

- The `Renewal trigger` (the clause's capitalized heading span): when an origin row's recorded scope materially changes after an entry exists for it, a `## Rescope` section whose commit postdates the entry's authoring commit makes the entry a renewal candidate. A scope-changing operator decision qualifies only when recorded in that section; other decision headings and equivalent witness forms are outside this trigger until the row convention supports them. The monitor routes the candidate to the next investigate slot; if that slot is spent, it waits for the next one. A frozen entry stays frozen and is reconsidered after the existing freeze clears.
- The read-side mirror: the maintenance monitor's rolling-log read treats a noticed row-scope/entry divergence backed by a post-entry `## Rescope` section as a renewal candidate per the `Renewal trigger` clause and routes it to the next investigate slot. A frozen entry remains non-dispatchable under the existing freeze rule; after the freeze clears, the ordinary read detects the same origin witness again.
- The renewal-skip reason: the reason recorded in the entry's `Added:` line when an unfrozen entry reaches its investigate slot and no material change requires a refresh.

## Why

The rolling-log entry lifecycle owns two stages - the prune rule (a landing removes the entry) and the freeze rule (authoring-start blocks rewrites) - and leaves the third unowned: an origin row whose scope changes after its entry exists. The witnessed cost is a stale dispatch payload: an amended entry that a later archaeology pass materially reshaped, caught only because the operator asked whether the pass had been re-run. The fix reads the row's existing `## Rescope` section, with scope-changing operator decisions included only when recorded there, and defines the trigger in the investigate skill that owns the anchored pass plus a read-side mirror in the maintenance monitor's log duties. Other witness formats are deferred until a row convention exists. The trigger reads the origin row, never a new digest store or ledger.

## Gist & Examples

TLDR: one clause in the investigate skill defines the `Renewal trigger`; the monitor consultatively routes noticed divergences to the next investigate slot, and the existing freeze rule continues to prevent dispatch while authoring is active.

Before: the memory-index row was rescoped (2a5962888); the entry was amended by targeted edit only; the dispatch payload was stale until a later pass (5251042ca) reshaped it, and nothing would have noticed without the operator's ask.

After: the monitor's read (or the rescoping session, when the rescope is its own same-turn write) sees a `## Rescope` section committed after the entry's authoring commit and routes it - the re-run executes at the next investigate slot, or a renewal-skip reason is recorded in the `Added:` line - so a stale payload backed by that row witness is surfaced.

Edge cases: a frozen entry is not rewritten or given an extra state mark; the existing `Frozen:` state prevents dispatch, and the monitor redetects the origin-row witness after the freeze clears. The re-run never fires as an unplanned same-turn second pass; when the slot is spent, the candidate waits for the next slot. An unchanged entry records a skip in its `Added:` line when it reaches that slot. An ad-hoc (EXEC-PROMPTS) entry follows the same rule. The monitor flags and routes candidates but never rewrites entries.

## Outcome

The unowned lifecycle stage is partly owned: a material rescope recorded in a `## Rescope` section committed after entry creation is noticed from the row and the entry's existing provenance; the monitor routes the candidate to the next investigate slot, while the existing freeze rule remains unchanged. Other witness formats remain outside this trigger.

Gate delta: adds one renewal clause in agents/skills/investigate/SKILL.md and one consultative read-side arm in agents/skills/maintenance/decisions.md. The candidate is derived from the existing Rescope section and entry provenance; frozen entries rely on the existing `Frozen:` dispatch behavior and are reconsidered after it clears. No new pin, mark, dispatch refusal, state field, script, ledger, digest store, or required ceremony is added; the existing pins suite remains a regression check.

## Assumptions

- The definition home is the investigate skill's Stage 4 region, with the relocation named in the clause's provenance: the entry's prompt cites "the amendment-capable targeted-edit rules" beside which the trigger was to land, but the current investigate SKILL.md (79 lines at the v5 fold, Stages 0-4) carries no section by that name (the log's targeted-edit discipline lives in the log's own standing rules and the monitor's duty (h)). The architecturally consistent alternative - a third standing-rule bullet beside the log's Prune and Freeze rules - was evaluated and rejected: the operator-confirmed prompt names the investigate skill as the definition home, PLAN-PROMPTS.md is read-only under this plan, and the EXEC-PROMPTS log applies the standing rules by label, so a log-rule bullet would need a third file the prompt never scoped; the rejection is recorded here and in the clause's provenance comment rather than adopted silently. Basis: the entry's named home, the file survey, and the review panel's home-pattern finding.
- Freeze remains unchanged: no prompt rewrite or additive status mark is made while an entry is frozen. The monitor can derive the renewal candidate again from the origin row and the entry's authoring provenance after the existing freeze clears. A renewal-skip reason is recorded in `Added:` only when the entry is unfrozen and reaches its investigate slot. Basis: the standing freeze rule and the witnessed rescope sequence.
- The monitor arm is consultative (flag and route), not a rewrite duty. It routes candidates to the next investigate slot and does not attempt cross-turn session attribution; the existing freeze state already prevents dispatch while authoring is active. The arm is witnessed by the existing history-based dry run and prose review; no pin is added. Basis: the entry's candidate-routing wording and the one-investigation-per-turn bound.
- The witnessed-sequence dry run reads git history, not the working tree: the memory-index row was deleted at its landing (90b848575), so the row's Rescope section survives only as `git show 2a5962888:docs/history/backlog/2026-10-08-memory-index-consolidation.md`, and the entry's pre-rescope `Added:` line survives at `2a5962888^` (the line at `5251042ca^` already carries the rescope amendment). The dry run's firing argument is commit-order, not date-vs-date: the entry was authored at 02d08bc9f (2026-10-08 13:16:21; the row itself was authored minutes earlier at 3e3e1802d, 13:12:09), the rescope landed at 2a5962888 (2026-10-08 13:35:34) - a witness the entry's provenance does not cover, so the trigger fires - and the renewal pass followed at 5251042ca (15:04). The `Added:` line's date-only granularity is why the comparison rides commit order. Basis: the entry's validation demand, both commits' history, and the review panel's granularity finding.
- Residual accepted: a rescope without a post-entry `## Rescope` section stays invisible to the trigger, including a scope-changing decision recorded only under another heading or outside the row; the monitor's archaeology passes remain the backstop. Basis: the entry's "reads the origin row itself" constraint and the witnessed row format.

Decision points requiring a grill: none remain (the operator-confirmed entry names the trigger, both homes, the existing freeze behavior, the validation, and the four rejected alternatives).

## Standing constraints

- The trigger reads the origin row itself: no digest store, no ledger, no new state-schema field, no dispatch-time hashing (the smallest-arm rule).
- The freeze rule is never bypassed or extended: a frozen entry takes no prompt rewrite or added state mark. Once it clears, the monitor re-reads the origin witness and routes any still-uncovered rescope to the next investigate slot.
- Both skills are pinned surfaces: the pins suite stays green at every task landing, and every span the edits touch is kept intact or re-aimed beside its provenance in the same task.
- The full battery stays green at every task landing: the pins suite, the entries checker over both logs, em-dash over the touched paths, the hygiene scan.
- Deploy truth: both skill edits reach their runtime home at this plan's merge-locked landing (the vendored twin carries them in the same run).
- No machine-specific absolute paths; nothing pushed to origin; the branch rebases onto current main at each fold with the task-start currency check and the stop-and-report arm.
- Rollback arm: revert the offending task's commit; the change is prose-only, so a revert restores today's text exactly.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the trigger fires exactly on an in-row witness the entry's provenance does not cover (commit order decides), and an unchanged entry records a skip only when unfrozen.
- regression safety: the pins suite and the entries checker green; every pinned span intact or re-aimed beside provenance.
- scope discipline: the changes touch one renewal clause in each skill file plus the sanctioned one-line Stage 3 em-dash remediation; the pins script is edited only if an existing span must be re-aimed. No new script, ledger, pin, or state field.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- The battery is green, including the witnessed-sequence dry run.

**Ship when:**
- The implementation, pins regression suite, entries checkers, em-dash checks, hygiene scan, and witnessed historical Rescope dry run pass. No future rescope is a shipping prerequisite. Record the first later post-entry `## Rescope` observation through the ordinary maintenance record as activation evidence, not as a new gate.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/investigate/SKILL.md` (the renewal-trigger clause in the Stage 4 region, plus the one-line Stage 3 em-dash remediation Task 1 sanctions; nothing else in the file)
- `agents/skills/maintenance/decisions.md` (the read-side renewal arm inside the Rolling prompt log duties bullet; nothing else in the file)

**Tests:**
- `scripts/check_maintenance_pins.sh` (read-only validation unless an existing span is invalidated by the prose edits; no new witness pins)

**Docs:**
- `docs/history/backlog/2026-10-08-investigate-renewal-trigger-on-row-rescope.md` (read-only this plan; flipped covered by the landing rider)

**Read-only (referenced, never edited):**
- `docs/history/backlog/PLAN-PROMPTS.md` (the standing freeze/prune rules and the existing prune receipt; no prompt-log edit is planned)
- the witnessed row in git history: `git show 2a5962888:docs/history/backlog/2026-10-08-memory-index-consolidation.md` (the working-tree row was deleted at its landing 90b848575; its Rescope section is the dry run's witness and survives only in history; the completed twin `docs/history/plans/completed/2026-10-08-memory-index-consolidation.md` carries the outcome prose but no Rescope section)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-08-investigate-renewal-trigger-on-row-rescope.md (Status: open; the landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## investigate-renewal-trigger` (historically frozen under docs/tmp/authoring-claims/2026-10-10-investigate-renewal-trigger.md and pruned with the receipt at line 26; no landing prune remains)

## Validation Commands

**Production:**
```bash
grep -c "Renewal trigger" agents/skills/investigate/SKILL.md   # expect 1 (the capitalized clause heading; 0 pre-edit)
grep -c "renewal candidate" agents/skills/maintenance/decisions.md   # expect 1 (the read-side arm; 0 pre-edit)
```

**Tests:**
```bash
bash scripts/check_maintenance_pins.sh   # exit 0
python3 scripts/check_investigate_entries.py --log docs/history/backlog/PLAN-PROMPTS.md   # exit 0
python3 scripts/check_investigate_entries.py --log docs/history/backlog/EXEC-PROMPTS.md   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/investigate/SKILL.md   # exit 0
bash scripts/check-no-em-dash.sh file agents/skills/maintenance/decisions.md   # exit 0
bash scripts/scan-public-hygiene.sh   # exit 0 from the repo root (the in-repo copy)
```

**Witnessed-sequence dry run (Task 3; the firing argument rides commit order, never date-vs-date):**
```bash
git log --format='%h %ci' -1 02d08bc9f   # the entry's authoring commit: 2026-10-08 13:16:21 +0100
git log --format='%h %ci' -1 2a5962888   # the rescope commit: 2026-10-08 13:35:34 +0100 (postdates the authoring commit - a witness the entry's provenance does not cover)
git show 2a5962888:docs/history/backlog/2026-10-08-memory-index-consolidation.md | grep -c "## Rescope"   # expect 1 (the row's Rescope-class section, read from history: the working-tree row was deleted at landing 90b848575)
git show 2a5962888^:docs/history/backlog/PLAN-PROMPTS.md | sed -n '/^## memory-index-consolidation$/,/^## quota-wall-dispatch-doctrine$/p'   # full pre-rescope prompt: two implementation passes (compress/index, then reviewed prune) plus the permanence convention
git show 2a5962888:docs/history/backlog/2026-10-08-memory-index-consolidation.md | sed -n '/^## Rescope/,$p'   # post-entry scope decision: one-time cleanup runs ad hoc with safeguards; only the audit duty and append-first convention remain
git show 2a5962888^:docs/history/backlog/PLAN-PROMPTS.md | grep -A2 '^## memory-index-consolidation'   # pre-rescope Added: provenance, date-only 2026-10-08 (anchored to the entry heading; a bare Added:-date grep matches the first entry's line)
git log --format='%h %ci' -1 5251042ca   # the renewal pass that followed: 2026-10-08 15:04 +0100
```

### Task 1: the renewal-trigger clause in the investigate skill

Files:
- agents/skills/investigate/SKILL.md
- scripts/check_maintenance_pins.sh (edit only to re-aim an existing pin invalidated by these prose changes; add no pin)

- [ ] Add the `Renewal trigger` clause to the Stage 4 region (beside the emission contract), with a provenance comment naming the relocated home: when an origin row's recorded scope materially changes after an entry exists, a `## Rescope` section whose commit postdates the entry's authoring commit makes it a renewal candidate; a scope-changing operator decision counts only when recorded in that section, and other witness formats are deferred. Route it to the next investigate slot, never an unplanned same-turn second pass; if that slot is spent, leave it for the next one. The re-run refreshes the entry or records a skip in `Added:` when the entry is unfrozen. Read the origin row itself; add no digest store or ledger. A frozen entry remains frozen and is reconsidered by the ordinary monitor read after the existing freeze clears; do not add a mark, frozen-entry write exception, or dispatch hold. Re-aim an existing pin only if the prose edit invalidates its current span; add no pin. [class: IMPLEMENTATION_REQUIRED]
- [ ] Remediate the file's one pre-existing em-dash red so the battery's exit-0 expectation is honest: line 52 (the Stage 3 admission-step bullet, landed 98e1a1c76) carries two em-dashes; rewrite them as plain prose with the wording preserved, sanctioning no other out-of-region line. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run this task's span checks from `## Validation Commands`; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]

### Task 2: the read-side mirror in the monitor's rolling-log duties

Files:
- agents/skills/maintenance/decisions.md
- scripts/check_maintenance_pins.sh

- [ ] Add the read-side renewal arm to the Rolling prompt log duties bullet in agents/skills/maintenance/decisions.md: treat a noticed row-scope/entry divergence backed by a post-entry `## Rescope` section as a renewal candidate per the investigate skill's `Renewal trigger` clause, routing it to the next investigate slot. The monitor is consultative and does not rewrite entries. A frozen entry remains non-dispatchable under the existing freeze rule; after it clears, the ordinary read can detect the same origin witness. Do not add a mark, frozen-entry write exception, or new dispatch hold. Re-aim an existing pin only if the prose edit invalidates its current span; add no pin. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the pins suite, the entries checker over both logs, both em-dash checks, and the hygiene scan; record each exit code in the session log and fix any red span before reporting the task done. [class: REPOSITORY_TEST]

### Task 3: the witnessed-sequence dry run

- [ ] Run the witnessed-sequence dry run exactly as `## Validation Commands` specifies it (all seven commands, in order) and record in the session log: the pre-rescope prompt's two-pass scope (compress/index, then reviewed prune); the post-entry `## Rescope` decision that makes those one-time cleanup passes ad hoc and leaves only the permanence mechanism (periodic audit plus append-first convention); and the conclusion that this is a material scope change, not a wording edit. Also record the three commit timestamps (entry authored 2026-10-08 13:16:21 at 02d08bc9f; rescope 13:35:34 at 2a5962888; renewal pass 15:04 at 5251042ca), the row's Rescope-section count, and the pre-rescope `Added:` provenance. State the firing argument as commit order: the rescope commit postdates the entry's authoring commit 02d08bc9f, so the row witness is outside the entry's provenance and the trigger fires; never infer ordering from date-only `Added:` text. If a history read fails as missing (a shallow clone), deepen the clone (`git fetch --unshallow` or `--deepen`) and retry once; a still-failing read aborts the task with the recorded reason, never a substituted witness. Run the full battery after. [class: REPOSITORY_TEST]
