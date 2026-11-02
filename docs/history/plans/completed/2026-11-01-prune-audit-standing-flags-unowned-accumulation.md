# Plan: Prune-audit standing flags: receipt backfill to green

Backlog origin: docs/history/backlog/2026-11-01-prune-audit-standing-flags-unowned-accumulation.md
Driving force: code-quality (primary), token-usage (secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-prune-audit-standing-flags-unowned-accumulation-pab5166cc-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.0h total, largest task 1.0h
Authoring claim: prune-audit-standing-flags-unowned-accumulation.md (session zcode-interactive-20261101T1503-current-pick)

## Terms

- prune-audit: the consultative `scripts/check_prompt_log_origins.py --prune-audit` classification of every rolling-log removal inside a base..HEAD range; it classifies each removal against that removal commit's own post-image, so a receipt written only at a later commit needs the tip-recognition class below to witness it.
- receipt ledger line: a `PLAN-PROMPTS-PRUNE:` or `EXEC-PROMPTS-PRUNE: <slug> -> <token> (prose)` line inside a rolling log; the token is a commit digest, an in-tree path, or the checker's in-commit literal `landing` (all three are well-formed ledger tokens; only the first two are probed for resolvability, and only on newly written or retokened lines).
- REMOVED-WITHOUT-WITNESS and RECEIPT-LINE-REMOVED-WITHOUT-WITNESS: the audit's two flag classes - respectively, a log removal with no resolvable witness, and a committed receipt-line deletion whose lines the tip does not carry back.
- subclass A/B/C: the origin row's three flag classes, corrected by review r1: A is four covered-row deletion landings, of which two wrote no receipt at all (self-heal-caller-map at c5c31e9d6, hygiene-scanner at 830119aff) and two wrote receipts whose prose token `landed ad-hoc` resolves to nothing (done-closeout-gates-trio at eebc930c0, untrack-operand-residual-trio at 66255a68d); B is the eighteen receipt lines eaten by the ledger rewrites 30fc2342b and a5024b396; C is the plan-prompts-stub-rewrite-origin receipt written by 312c53122 with the same prose-token defect (`landed`).
- tip recognition: the audit classification arm this plan adds, reading the audited tip's committed log image (never working-tree bytes; the existing uncommitted reconcile budget stays responsible for pending restores): an entry removal flagged REMOVED-WITHOUT-WITNESS is re-classified PRUNE-OK when the tip image carries a ledger line naming that slug with a resolvable token; an eaten line flagged RECEIPT-LINE-REMOVED-WITHOUT-WITNESS is re-classified PRUNE-OK when the tip image carries that line's exact committed bytes, consumed one draw per occurrence by full-line identity (multiplicity mirroring the existing pending budget). The slug-token disjunct never clears an eaten-line flag, and a fresh non-byte-identical line never restores one.
- retoken (same-commit): the sanctioned way to replace a ledger line: one commit removes the broken line and adds the corrected line for the same slug, so the removal is a retoken, never a bare receipt-line deletion.
- resolve-at-use: a full digest is produced by git (`git rev-parse` or `git log --format=%H`) in the command that uses it, never retyped from a display prefix.
- covered-row deletion landing: a landing commit that deleted its covered backlog origin row per the covered-row rule (the removals subclass A flags).
- receipt convention: the 2026-10-28 receipt convention (landing 3c7917dad) requiring a receipt per rolling-log removal.
- rolling log: one of the two rolling prompt logs, `docs/history/backlog/EXEC-PROMPTS.md` and `docs/history/backlog/PLAN-PROMPTS.md`.

## Why

The consultative prune-audit has carried 23 standing flags since the receipt convention landed (2026-10-28), and every scheduler turn re-derives a subset report-only. The standing flags erode the audit's signal for real findings and re-pay the derivation cost each turn. Review r1 additionally established that no log edit alone can clear them: the checker classifies each removal against its own commit's post-image, so backfilled lines witness nothing, and committed restorations are invisible to the repair reconciliation. The origin row's triage question anticipated this: its option (2) is a checker recognition class, and its machinery admission pre-authorized that arm's admission test.

## Gist & Examples

TLDR: add tip recognition to the prune-audit and repair the rolling logs' receipts, so the consultative audit runs green again, ending the per-turn flag re-derivation, for code-quality with a token-usage payoff.

Before (today): `python3 scripts/check_prompt_log_origins.py --prune-audit --base 3c7917dad` exits 1 with 23 standing flags. Four covered-row deletion landings lack a usable receipt (two receipt-less, two with the unresolvable `landed ad-hoc` token); the stub-rewrite receipt's token is the prose word `landed`; eighteen receipt lines eaten by 30fc2342b and a5024b396 leave their removals unwitnessed. Every scheduler turn re-records subsets report-only because no route repairs the flags.

After (this plan): the same command exits 0 with final `OUTCOME: pass`. The checker recognizes a tip receipt (a resolvable-token ledger line at the audited tip) and a tip restoration (an eaten line's exact bytes back at the tip), so the repaired ledger witnesses the historical removals: the two receipt-less landings carry backfilled lines; the three broken-token lines are retokened in the same commits that re-issue them; the eighteen eaten lines are restored byte-exact. Example: the flag `REMOVED-WITHOUT-WITNESS: untrack-operand-residual-trio (commit 66255a68d ...)` becomes a PRUNE-OK classification through its corrected tip line `EXEC-PROMPTS-PRUNE: untrack-operand-residual-trio -> <full sha of 66255a68d> (...)`.

Edge cases: a retoken that removes a ledger line without re-adding a line for the same slug in the same commit would create a new RECEIPT-LINE-REMOVED-WITHOUT-WITNESS flag, so the retoken constraint is absolute; a restored line must byte-match its committed original, because the recognition consumes exact full lines (`RECEIPT_FULL_LINE_RE` identity); a backfilled token must resolve through the checker's own probes at write time, because a display-prefix or prose token re-creates the subclass C defect; and the audit window base stays 3c7917dad, the convention's landing commit, so pre-convention removals are never judged by the post-convention grammar; a restored historical line is never retokened afterward, because a later retoken removes the exact bytes from the tip image and re-flags the committed deletion; and the receipt grammar's retoken constraint stays absolute because the recognition's byte-identity disjunct does not match a retoken's own removal, so the removal and the re-add must share one commit.

## Outcome

The consultative prune-audit is a reliable green signal again: every log removal since the receipt convention carries a resolvable receipt or witness, so the audit's exit code means what it says.

- The 23 standing flags classify PRUNE-OK at the convention-era base 3c7917dad, and the audit exits 0.
- The ledger block carries a worked receipt example for each flag class, so the next covered-row deletion has an in-place shape to copy.
- Future ledger rewrites stay policed by the existing eaten-line flag class, now extended to committed restorations through tip recognition.

Gate delta: adds one classification class to the consultative prune-audit (tip recognition: a tip-side resolvable-token receipt, or an eaten line's exact committed bytes present at the tip, re-classifies a flagged removal PRUNE-OK). Pricing per the machinery admission test the origin entry pre-authorized: incident links are this plan's origin row (23 standing flags with no repair route; review r1's three worker simulations verified no log edit, committed or pending, clears the subclass A/C flags) and 30fc2342b's sixteen-line receipt eat; expected catch: every receipt backfill, retoken, and restoration repair pass, and every later ledger rewrite whose lines are restored; false-positive cost: a fabricated tip line could witness a removal it does not belong to, bounded by resolve-at-use and the line naming its own landing; review at the next prune-audit maintenance pass. No refusal, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition is added or removed; the landing prune-audit leg stays procedural; the origin row's covered flip carries these dispositions.

## Assumptions

- assume the convention-era audit base stays 3c7917dad; basis: the origin row's triage question and the audit's documented range semantics.
- assume every eaten receipt line is recoverable from git history at its exact committed bytes; basis: the repair reconciliation's full-line identity in `scripts/check_prompt_log_origins.py` and the surviving pre-rewrite blobs of 30fc2342b and a5024b396.
- Decision receipt: the initially authored repair-only doctrine (checker unchanged) was falsified in review r1 - three workers independently simulated the plan's task sequence and measured the audit still red with 23 flags after all repairs, because removal classification reads the removal commit's post-image and the repair reconciliation consumes only uncommitted working-tree additions; the origin row's triage option (2), a checker recognition arm, was selected instead; source: review r1 findings (staged record 2026-11-01-plan-review-prune-audit-standing-flags-unowned-accumulation-pab5166cc-r1), 2026-11-01; affected sections: Outcome, Gate delta, Task 1.
Decision points requiring a grill: none remain.

## Standing constraints

- Hermeticity (lesson 43): every log edit, commit, and verification command re-enters the ad-hoc worktree and verifies the toplevel (`git rev-parse --show-toplevel`) in the same command, so a shell cwd reset never writes or verifies against the primary checkout.
- Resolve-at-use: every digest written into a receipt line is produced by git in the same command that writes the line; never retype a display prefix.
- Receipt grammar: a newly written or retokened ledger line reads `<slug> -> <token> (prose)` where the token is a resolvable commit digest, an in-tree path, or the checker's in-commit literal `landing`, never prose such as `landed <abbrev>`; replacing a ledger line is always a same-commit retoken.
- Log write discipline: re-read and compare before every write, targeted edits only, commit in the same change, run the public-hygiene scan over the touched log after the write.

## Evaluation Criteria

Quality dimensions:
- correctness: after the tasks, `python3 scripts/check_prompt_log_origins.py --prune-audit --base 3c7917dad` exits 0 with final `OUTCOME: pass`, zero `REMOVED-WITHOUT-WITNESS` lines, zero `RECEIPT-LINE-REMOVED-WITHOUT-WITNESS` lines, and zero pending receipt flags.
- minimality: the branch diff touches only the checker, its test file, and the two rolling logs; no skill text, registry, or machinery-registry byte changes.
- durability: every new or retokened token resolves through the checker's own probes at HEAD, and each restored line byte-matches its committed original (verified per line by fixed-string count, and by the audit's exact-line recognition post-commit).

Done when:
- the audit runs green at base 3c7917dad with the recognition arm landed and the repaired receipts present at HEAD.

Ship when:
- nothing external; this work is repository-verifiable only.

## Review Scope

**Explicit must-fix (review and fix if valid):**

**Production code:**
- `scripts/check_prompt_log_origins.py` (Task 1) *(edited: the tip-recognition classification class)*

**Tests:**
- `scripts/test_check_prompt_log_origins.py` (Task 1) *(new tests appended)*

**Logs:**
- `docs/history/backlog/EXEC-PROMPTS.md` (Task 2) *(receipt lines only)*
- `docs/history/backlog/EXEC-PROMPTS.md` (Task 3)
- `docs/history/backlog/EXEC-PROMPTS.md` (Task 4)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 4) *(only where history places an eaten line in this log)*

**Plan-related extension:** implementation and review may change files not listed above only when causally related to this plan; a weak or speculative link drops as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/development_lessons.md`; reason: lesson 44 already records the receipt grammar; no text change is picked.
- the landing procedure texts; reason: the landing prune-audit leg stays procedural per the Gate delta disposition.

## Validation Commands

```bash
python3 scripts/check_prompt_log_origins.py --prune-audit --base 3c7917dad
```

Expect exit 0 with the final line `OUTCOME: pass`, zero lines of either flag class, and zero pending receipt flags in the summary.

### Task 1: Add tip recognition to the prune-audit classification

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py` *(tests appended)*

Primary class anchors:
- `walk_audit_commits` in `scripts/check_prompt_log_origins.py`, which owns the per-removal classification walk

- [x] Record the run's start tip once for the Task 5 minimality check: `git rev-parse HEAD` at the placement, before any task commit; Task 5 reads the recorded value and never retypes it [class: REPOSITORY_TEST]
- [x] `walk_audit_commits` recognizes a tip receipt: given a removal commit whose slug carries a resolvable-token ledger line at the audited tip (absent at the removal commit), expects the removal classifies PRUNE-OK naming the tip receipt witness, not REMOVED-WITHOUT-WITNESS [class: IMPLEMENTATION_REQUIRED]
- [x] `walk_audit_commits` recognizes a committed restoration: given a removal commit that removed receipt lines whose exact bytes are present in the audited tip's committed log image, expects the eaten-line removal classifies PRUNE-OK naming the restoration witness, and the recognition survives committing the restore [class: IMPLEMENTATION_REQUIRED]
- [x] Negative: given a tip line whose token does not resolve (prose such as `landed 5fd2cd482`) or a drifted restoration line that is not a byte match, expects the recognition class does not fire and the flag stands [class: REPOSITORY_TEST]
- [x] `walk_audit_commits` keeps eaten-line policing narrow: given a ledger rewrite that re-adds fresh, non-byte-identical lines for the eaten slugs, expects the eaten-line flags stand; and given two committed removals of the same line, expects one restored byte-exact copy reconciles exactly one of them [class: REPOSITORY_TEST]
- [x] `walk_audit_commits` reads the committed tip image: given a committed byte-exact restore whose working-tree copy is subsequently mutated (uncommitted drift), expects the recognition still classifies PRUNE-OK from the committed image [class: REPOSITORY_TEST]
- [x] Run → expect RED: the appended recognition tests fail against the current classifier [class: REPOSITORY_TEST]
- [x] Write minimal implementation in the classification walk [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the appended tests pass and the checker's existing test suite passes [class: REPOSITORY_TEST]
- [x] Commit: `fix: recognize tip-restored and backfilled receipts in the prune-audit` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Re-issue the subclass C receipt with a same-commit retoken

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/EXEC-PROMPTS.md`

- [x] Verify the toplevel, then remove the broken line `EXEC-PROMPTS-PRUNE: plan-prompts-stub-rewrite-origin -> landed 5fd2cd482 (...)` and add the corrected line with the full digest of 5fd2cd482 resolved at write time, in one commit (the retoken shape) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `git rev-parse --verify <token>^{commit}` resolves before the write, the written token's identity equals the named landing's full digest (both sides resolved by git in the verifying command, never quoted from context), and the audit at base 3c7917dad no longer flags plan-prompts-stub-rewrite-origin and reports no retoken flag for this commit [class: REPOSITORY_TEST]
- [x] Commit: `fix: re-issue stub-rewrite receipt with a resolvable ledger token` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Repair the four subclass A receipts

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/EXEC-PROMPTS.md`

- [x] For the two broken-token landings (done-closeout-gates-trio at eebc930c0, untrack-operand-residual-trio at 66255a68d): retoken each `landed ad-hoc` line to the landing's full digest resolved at write time, same-commit per line [class: IMPLEMENTATION_REQUIRED]
- [x] For the two receipt-less landings (self-heal-caller-map-recoverability-drift-and-review-question-scope at c5c31e9d6, hygiene-scanner-frozen-arm-and-report-residuals at 830119aff): append one backfilled ledger line per slug with the landing's full digest resolved at write time [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: those four flags classify PRUNE-OK at base 3c7917dad through the tip-recognition class, with no retoken flags, and each written token's identity equals its named landing's full digest (both sides resolved by git at verification time) [class: REPOSITORY_TEST]
- [x] Commit: `fix: repair covered-row-deletion receipts for the four flagged landings` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Restore the eaten receipt lines byte-exact

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/EXEC-PROMPTS.md`
- `docs/history/backlog/PLAN-PROMPTS.md` *(only where history places an eaten line in this log)*

- [x] Enumerate the eaten lines from the audit's subclass B flags and the two rewrite commits (30fc2342b, a5024b396); extract each exact committed full line from the pre-rewrite blob (`git show <pre-rewrite-commit>:<log-path>`), the same exact-byte sourcing the checker's landing-only `--repair` mode automates (`prune_audit_repair`), which cannot be used here because its contract restores into pending images only [class: REPOSITORY_TEST]
- [x] Re-add every enumerated line to its original log's ledger block, byte-identical, with no token-resolvability condition: restoration is byte identity, and historical tokens (including the fourteen literal `landing` tokens and the two path tokens the eating commit itself archived) are recorded report-only when they no longer resolve, never withheld [class: IMPLEMENTATION_REQUIRED]
- [x] Verify per line by fixed-string count: `grep -Fxc '<line>' <log>` equals the expected count for every restored line, then commit; a restored line is never retokened afterward [class: REPOSITORY_TEST]
- [x] Commit: `fix: restore eaten receipt-ledger lines from their committed bytes` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Terminal verification

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none (verification only)

- [x] Re-enter the ad-hoc worktree and verify `git rev-parse --show-toplevel` resolves to the placement before running either command [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/check_prompt_log_origins.py --prune-audit --base 3c7917dad` exits 0 with final `OUTCOME: pass`, zero lines of either flag class, zero pending receipt flags [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-01-prune-audit-standing-flags-unowned-accumulation.md` exits 0 [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `git diff --name-only <recorded start tip>..HEAD -- scripts/ docs/history/backlog/` lists exactly `scripts/check_prompt_log_origins.py`, `scripts/test_check_prompt_log_origins.py`, `docs/history/backlog/EXEC-PROMPTS.md`, and `docs/history/backlog/PLAN-PROMPTS.md`; every path the unscoped diff adds beyond those four is this plan file itself (the run's own per-task checkbox ticks land in the task commits per execute-plan Step 1.3) [class: REPOSITORY_TEST]

## Residual findings (cap closure)

- consistency#unsatisfiable-minimality-diff-base (r5 F1): folded - the minimality check now scopes its diff to scripts/ and docs/history/backlog/ and names the plan file's own checkbox-tick commits as the expected beyond-set, per the round's fix.

## Disposition of migrated backlog items

The covered origin row docs/history/backlog/2026-11-01-prune-audit-standing-flags-unowned-accumulation.md is deleted at this archive per the covered-row rule; its disposition is folded here. All three subclasses repaired on this lineage: subclass A receipts retokened/backfilled (1397d672c, 3be796661 — the plan's fourth slug has no in-range removal here, derivation in the commit body); subclass C's stub-rewrite line retokened to a resolvable digest (1397d672c); subclass B's 56 eaten lines restored byte-exact from their committed pre-rewrite blobs (663965c51). The checker gained the tip-recognition classes (b4099443) so tip receipts and committed restorations witness without per-turn re-derivation. Terminal audit at base 3c7917dad exits 0 with zero flag lines; the covering landing commit is the witness. Review record: .ai-playbook/reviews/2026-11-02-prune-audit-standing-flags-unowned-accumulation-code-review-r1.md (0 blocking; deferred Mediums F4/F5/F6 carry recorded rationale).
