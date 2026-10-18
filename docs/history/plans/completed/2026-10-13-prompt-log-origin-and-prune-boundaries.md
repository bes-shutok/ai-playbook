# Plan: prompt-log origin classification and prune-audit receipt reconciliation

Backlog origins (scope of record):
- docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md (deleted from the backlog top level by commit e0d7d6961; disposition below)
- docs/history/backlog/2026-10-11-prompt-log-prune-audit-unwitnessed-history.md

Driving force: automation (primary) + code-quality (secondary)

Plan review record: the staging series {reviews_dir}/2026-10-13-plan-review-prompt-log-origin-and-prune-boundaries-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 2h total, largest task 1h

## Terms

- `origin checker`: `scripts/check_prompt_log_origins.py` run with no mode flag; it prints one classification line per logged origin and exits 1 only for a stale entry (an entry whose every origin is served).
- `served origin`: an origin the checker treats as work complete: a top-level row with a `done`/`covered` status, or a file found under a served archive state (`completed/`, `rejected/`) via `resolve_archive_path`.
- `deferred origin`: an origin row moved to `docs/history/backlog/deferred/` by an operator deferral order; still-actionable work that is neither completed nor rejected.
- `ARCHIVE_DIR_NAMES`: the checker's tuple of backlog subdirectory names whose hits classify an origin as served (currently `completed`, `rejected`, `deferred`).
- `receipt ledger`: the `PLAN-PROMPTS-PRUNE:` / `EXEC-PROMPTS-PRUNE:` `<slug> -> <witness>` receipt lines recorded inside a rolling log; the log charter declares one such line per removed entry as the removal's receipt.
- `commit-message receipt`: a receipt line inside a pruning commit's own message body; the only receipt form the prune audit accepts today (matched by `RECEIPT_LINE_RE`, which accepts only the `EXEC-PROMPTS-PRUNE:` prefix).
- `prune audit`: `scripts/check_prompt_log_origins.py --prune-audit --base <ref>`; walks `base..HEAD` commits touching either rolling log and classifies every entry removal against witnesses.
- `flagged removal`: `REMOVED-WITHOUT-WITNESS`, the audit's only failing classification; any other removal classification is report-only.

## Why

The origin checker treats a deferred backlog row as served work, so an entry whose work is only deferred reads as stale and fails the pins suite; and the prune audit misses the receipt form the log charter itself declares (the in-log receipt ledger line), reporting receipted historical removals as unwitnessed. Both defects force manual adjudication of gates that should certify mechanically.

## Gist & Examples

TLDR: the checker stops classifying deferred rows as served and the prune audit accepts the log's own ledger receipts, so deferred work keeps its entries open and receipted removals stop being flagged, removing recurring manual adjudication (automation).

Before (today): a frozen entry whose origins all sit in `deferred/` is reported `SERVED` and then `STALE` with exit 1, failing the pins pin `prompt log has no all-served (stale) entry` until a prune witness is manufactured for work that was never done (witnessed 2026-10-11 against the then-frozen `execute-plan-adapter-route-scope-inversion` entry). And commit 04e505e4e's four PLAN-PROMPTS removals report `REMOVED-WITHOUT-WITNESS` because their receipts are `PLAN-PROMPTS-PRUNE:` ledger lines inside the log file - a form the audit never reads, since it scans only the removing commit's message body for an `EXEC-PROMPTS-PRUNE:` line (witnessed 2026-10-11, `--prune-audit --base ba0f517a`, `OUTCOME: fail`).

After (this plan): a deferred origin reports as its own still-actionable class, never `SERVED`, so the entry stays open and the gates pass without a manufactured witness. A removal whose slug a resolving ledger line names in the touched log's post-image classifies `PRUNE-OK (log ledger receipt)` instead of flagged. Removals with no witness anywhere in the audited window still flag: `execute-plan-closeout-digest-and-transfer` (removed by commit 0b8ee8069, no receipt in its message, no ledger line, no plan file) remains the named missing-evidence case, advisory at the consultative survey.

Edge cases: an entry with origins split between `deferred/` and live rows stays open (mixed entries never stale); a ledger line naming a different slug never witnesses; a ledger token that resolves to no commit or no in-tree path never witnesses; a basename present in both `completed/` and `deferred/` keeps the completed hit's served semantics; the landing closeout's bounded range stays the caller's `--base` contract and the survey stays consultative (no exit-semantics change).

## Outcome

The prompt-log origin checker and the prune audit certify log state mechanically against the receipt and deferral semantics the log charter declares.

- A deferred origin keeps its entry open (never `SERVED`, never `STALE` on deferred origins alone), so the pins suite passes without a manufactured prune witness.
- A removal receipted by a resolving in-log ledger line classifies `PRUNE-OK (log ledger receipt)` with the receipt class named in the report, closing the witnessed false-negative class.
- Genuinely unwitnessed removals still flag; the audit's exit semantics, the bounded landing range, and the consultative survey posture are unchanged.

Gate delta: no new gate, refusal class, fence, protocol layer, or schema field. Two existing classification sets change width in opposite directions, each priced by its origin's witnessed incident: the served-classification set narrows (deferred leaves `ARCHIVE_DIR_NAMES`' served semantics; the witnessed incident is a false STALE that failed the pins suite), and the audit's witness-acceptance set widens (the charter-declared ledger receipt form joins the commit-message form; the witnessed incident is a false `REMOVED-WITHOUT-WITNESS` on four receipted removals). One report-line class is added (`DEFERRED:` where `LIVE:` printed before) and one existing report line gains a parenthetical class suffix (`PRUNE-OK ... (log ledger receipt)`); both are report-shape growth paid for by the same two witnessed misclassification incidents. No refusal, check, or field is removed; the flagged class and its fail exit are preserved byte-for-byte in behavior.

## Assumptions

- assume `deferred/` means actionable: rows the operator moved to `deferred/` stay reopenable work, so a deferred origin can never serve an entry; basis: the origin row's Expected arm ("distinguish a deferred, still-actionable origin from a completed or rejected origin") and the coverage gate's `PASS_STATES` in `scripts/check_plan_origins_closed.py`, which admit only completed/closed/rejected and never a deferred analogue.
- assume each log's receipts live in that log: a PLAN-PROMPTS removal consults PLAN-PROMPTS's post-image and an EXEC-PROMPTS removal consults EXEC-PROMPTS's post-image; basis: the log charter's receipt clause ("printed as one `PLAN-PROMPTS-PRUNE: <slug> -> <witness path>` receipt line per removed entry" in the log itself) and the audit's `SIBLING_LOG_RELS` design comment (one window covers both logs' removals).
- assume a ledger token witnesses only through the existing resolution shapes: the digest shape reuses the existing `commit_resolves` probe; the path shape adds one small tree-membership probe of the removal commit (`git cat-file -e <sha>:<path>`-equivalent) beside the existing witness enumeration, because no generic path-existence helper exists today (plan-file witnesses resolve by ls-tree enumeration of the plans root plus hyphen-segment matching, not by probing an arbitrary token path); basis: `witness_candidates` and `commit_resolves` in the checker, read at review round 1.
- assume the real-log baseline stays green through Task 1: the checker exits 0 at the 2026-10-13 tip with no stale entry (verified at authoring time), and un-serving deferred origins can only reduce staleness, never create it, because staleness requires every origin served; basis: the STALE predicate's all-served definition in `check_log`.
- assume no exit-semantics change: flagged removals still fail the audit, the landing closeout stays bounded by the caller's `--base`, and the survey stays report-only; basis: the log charter's audit posture clause and the origin row's "do not turn a consultative historical audit into a landing blocker" arm.

Decision points requiring a grill: none remain.

## Standing constraints

- Plan scripts and validators run under `python3` (3.14); all commands stay repo-relative with no machine-specific absolute paths.
- The pins suite is load-bearing for this surface: the pin `prompt log has no all-served (stale) entry` runs the checker, and three pins grep the exact `--prune-audit --base <merge-base>` invocation string in the log, the plans skill, and the authoring blueprint; no task may break those strings.
- Git history is immutable: no task rewrites, amends, or re-commits historical commits to repair missing receipts.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each witnessed incident is reproduced by a failing-then-passing test before its fix lands; the missing-evidence case stays flagged in the tests.
- maintainability: the ledger acceptance reuses the existing receipt grammar, `commit_resolves`, and tree-probe helpers; no second parser or duplicated slug matcher appears.
- compatibility: the checker selftest, the pins suite, and the three invocation-string pins stay green; existing ad-hoc receipt tests keep passing with precedence preserved.

**Done when:**
- both tasks' new tests pass and the full `test_check_prompt_log_origins.py` suite passes.
- `check_prompt_log_origins.py --selftest` passes with the deferred fixture arm.
- the bounded real-history audit at the origin row's base shows the four 04e505e4e slugs as `PRUNE-OK (log ledger receipt)` and `execute-plan-closeout-digest-and-transfer` still flagged.

**Ship when:**
- landed on main with its dispatch entry pruned by the landing rider per the log's prune rule and both origin rows flipped covered, with the residual missing-evidence case documented in the record.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_prompt_log_origins.py`

**Tests:**
- `scripts/test_check_prompt_log_origins.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The landing's own riders (the frozen entry's prune line, origin-row status flips, the PLAN-PROMPTS-PRUNE receipt) ride the landing branch per the log charter and are in scope as landing mechanics. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/deferred/` row contents; reason: this plan fixes their classification, not their dispositions (they stay deferred work).
- `scripts/done_run.sh` and the sibling frozen entry `done-finalized-manifest-classification`; reason: a disjoint defect and owner (manifest completion-state classification).
- `scripts/check_maintenance_pins.sh` pin expectations; reason: the pins are the compatibility surface this plan must keep green, not a surface to retune.
- Any history rewrite or retroactive receipt for commit 0b8ee8069; reason: immutable history doctrine; the missing-evidence flag is the honest class.

## Validation Commands

```bash
python3 -m pytest scripts/test_check_prompt_log_origins.py -q
python3 scripts/check_prompt_log_origins.py --selftest
python3 scripts/check_prompt_log_origins.py
python3 scripts/check_prompt_log_origins.py --prune-audit --base 04e505e4e^
bash scripts/check_maintenance_pins.sh
```

The suite is pytest-collected: run it under an interpreter whose environment provides pytest (the repository validator venv). A bare `unittest discover` collects zero tests from this pytest-style suite and exits 5 (witnessed at review round 3 under python3.14; it reads vacuously green only on interpreters of 3.11 or older).

The real-history audit at the origin row's base is expected to exit 1 while `execute-plan-closeout-digest-and-transfer` remains the single `REMOVED-WITHOUT-WITNESS` line; the four 04e505e4e slugs must read `PRUNE-OK (log ledger receipt)`. That exit 1 is the specified missing-evidence behavior, not a task failure.

### Task 1: Deferred origins are actionable, not served

Files:
- scripts/check_prompt_log_origins.py
- scripts/test_check_prompt_log_origins.py

- [x] Split the archive-state tuple by meaning: the served pair (the completed and rejected archive states) keeps driving `resolve_archive_path`; the deferred state gets its own named constant and lookup so a deferred hit resolves for reporting without ever serving. [class: IMPLEMENTATION_REQUIRED]
- [x] `classify_origin` returns not-served for a deferred-only hit with detail naming the deferred archive path plus the still-actionable note, and a top-level, completed-archive, or rejected-archive classification always wins over the deferred lookup when the same basename exists in several states (keep the existing sorted-first-match determinism for the served pair). [class: IMPLEMENTATION_REQUIRED]
- [x] `check_log` prints a deferred origin as its own line class `DEFERRED: <slug> -> <origin>` with the detail deferred/<basename> plus the still-actionable note, never `SERVED`, never counted toward the all-served staleness predicate. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `selftest()` with a deferred fixture arm: an entry whose only origin sits in the deferred archive state exits 0 with the `DEFERRED:` line and no `STALE` verdict. [class: REPOSITORY_TEST]
- [x] Tests (write failing first): deferred-only entry is not stale (exit 0, `DEFERRED:` line, no `STALE`); mixed entry with one deferred and one live origin stays open with both lines; a basename present in both the completed and deferred archive states still classifies served via the completed hit; existing served-arm tests (completed twin, top-level done/covered statuses) stay green unchanged. [class: REPOSITORY_TEST]

Evidence: `python3 -m pytest scripts/test_check_prompt_log_origins.py -q` green (21 passed, pytest-collected suite); `--selftest` green; the real-log checker run stays exit 0 with no `DEFERRED:` line expected on today's log (no entry currently holds a deferred origin) and no newly stale entry.

### Task 2: The prune audit accepts the log's ledger receipts and names the evidence class

Files:
- scripts/check_prompt_log_origins.py
- scripts/test_check_prompt_log_origins.py

- [x] Add a log-ledger receipt grammar scoped to the in-log ledger lines: it accepts both prefixes (`PLAN-PROMPTS-PRUNE:` and `EXEC-PROMPTS-PRUNE:`) and tolerates trailing rationale prose after the token, because the log's real receipt lines read `PLAN-PROMPTS-PRUNE: <slug> -> <token> (<reason prose>)` (three of the four incident lines carry such prose). [class: IMPLEMENTATION_REQUIRED]
- [x] The commit-message scan keeps its existing strict anchored end-of-line receipt shape unchanged: the ledger grammar is a separate pattern, never a loosening of the commit-message acceptance. [class: IMPLEMENTATION_REQUIRED]
- [x] In `walk_audit_commits`, keep the log post-image text the audit already materializes per touched log, and add the third evidence lookup after the plan-file witness and the commit-message receipt both miss: a ledger line in that log's post-image whose slug equals the removed slug and whose token resolves (digest via the existing `commit_resolves`; path via a tree-membership probe of the removal commit). [class: IMPLEMENTATION_REQUIRED]
- [x] Accepted ledger receipts report `PRUNE-OK: <slug> -> <token> (log ledger receipt)` and are never flagged. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve evidence precedence and determinism: plan-file witness first, commit-message receipt second, log-ledger receipt third; a removal classified by an earlier class never consults later ones, and each log's removals consult only that log's post-image. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the summary line to carry the reconciliation count: `prune-audit summary: <R> removals (<L> by log ledger) across <C> log-touching commit(s) in <base>..HEAD`. [class: IMPLEMENTATION_REQUIRED]
- [x] Tests (write failing first): a removal receipted by a `PLAN-PROMPTS-PRUNE:` ledger line with a resolving digest token is not flagged (exit 0, `(log ledger receipt)` suffix), with the fixture line mirroring the real trailing-prose shape `PLAN-PROMPTS-PRUNE: <slug> -> <token> (ad-hoc-superseded: <prose>)`; a ledger line whose token resolves to nothing still flags; a ledger line naming a different slug never witnesses. [class: REPOSITORY_TEST]
- [x] Tests (continued): a path-form token witnesses when the path exists in the removal commit's tree and flags when it does not; an EXEC-PROMPTS removal is witnessed by its own log's post-image, not the sibling's; the existing ad-hoc commit-message receipt tests stay green with precedence preserved (a commit-message receipt wins over a ledger line). [class: REPOSITORY_TEST]
- [x] Update the two summary-line assertions the extended format breaks (the exact substrings in `test_template_fence_never_parses_as_removal` and `test_untouched_log_audits_clean` around scripts/test_check_prompt_log_origins.py lines 538 and 553) to the extended format in this task, so the suite lands green without an unowned improvised edit. [class: REPOSITORY_TEST]

Evidence: the full pytest suite green; the real-history audit at `--base 04e505e4e^` measured at authoring time reports 26 removals across 51 log-touching commits with 5 flags; after the fix the same command shows the four docs-branch slugs (`docs-branch-overlapping-shadow-candidates`, `docs-branch-sync-persisted-copy`, `done-docs-branch-sync-overhead`, `docs-branch-temporal-sync-retention`) as `PRUNE-OK (log ledger receipt)` and `execute-plan-closeout-digest-and-transfer` still `REMOVED-WITHOUT-WITNESS`, with the summary line naming four removals by log ledger (L=4) and the flag count dropped to the single missing-evidence case; the missing-evidence residual is recorded in the landing's closeout notes rather than repaired by a manufactured receipt.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md` - deleted from the backlog top level by commit e0d7d6961 (the 2026-10-12 peer adapter-removal landing) while the defect it records stayed unfixed; this plan is the covering work for that row; its full text is preserved in git history at `e0d7d6961^:docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md` and its Cluster sibling (`2026-10-11-prompt-log-prune-audit-unwitnessed-history.md`) remains an origin of record here.

## Rejected alternatives

- Delete all prune auditing: rejected because the originating plan records real bulk removal of live entries without witnesses (witnessed: `docs/history/plans/completed/2026-10-05-plan-prompts-prune-eligibility-fence.md`).
- Treat every deferred origin as completed and prune its prompt: rejected because the prune rule requires a plans-root or completed-plan witness (witnessed: `docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md`).
- Make the 20-commit survey audit a blocking landing gate: rejected because it reports historical removals beyond the current landing's responsibility (witnessed: `docs/history/backlog/2026-10-11-prompt-log-prune-audit-unwitnessed-history.md`).
- Accept any in-log line as a receipt without the slug match and the token resolution probes: rejected because it would let an unserved entry's deletion witness itself, weakening the current-landing protection the origin orders preserved (witnessed: `docs/history/backlog/2026-10-11-prompt-log-prune-audit-unwitnessed-history.md`).
- Rewrite history to retrofit a receipt onto commit 0b8ee8069: rejected because recorded history is immutable and the flagged missing-evidence class is the honest disposition (witnessed: the origin row's "do not rewrite old commits" arm).
- Re-serve deferred origins by rewriting the deferred rows' status lines to done: rejected because it manufactures the completion the operator's deferral explicitly withheld (witnessed: `docs/history/backlog/2026-10-11-prompt-log-deferred-origin-stale-pin.md`).
