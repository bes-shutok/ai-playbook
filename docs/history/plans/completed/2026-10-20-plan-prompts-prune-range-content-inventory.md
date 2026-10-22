# Plan: Inventory prompt-log prune ranges before deletion
Backlog origin: docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-20-plan-review-plan-prompts-prune-range-content-inventory-r*.md (the highest identity-bearing round for this source-plan path is authoritative)
Execution budget: 1.5h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-15-plan-prompts-prune-end-anchor-overreach.md (session 20261020T145428Z-5bba0180b2a7)

## Terms

- **Prune range:** the complete log text from a selected entry heading up to, but not including, the next heading, inventoried before any edit.
- **Authorized entry set:** the own entry uniquely bound by its `Frozen:`, `Origins:`, and canonical-slug witnesses; collateral entries found by read-only origin discovery; ordinary monitor targets under current eligibility; or ad-hoc targets naming a completed origin, frozen before landing. Determine coverage per origin from the existing selector's witness: the own PLAN origin from this plan's landing; collateral PLAN origins from the read-only discovery result; ordinary PLAN origins from their plan file in the plans root or completed twin; and ad-hoc origins from the frozen entry plus its recorded landing commit. Remove only covered origin bullets and their explicitly paired scope arms. For a partial entry, keep the prompt scoped to the remaining origins, and clear `Frozen:` only after landing and only when the existing claim/worktree check finds no live claim or worktree for any retained origin. If the remaining scope cannot be derived unambiguously from the entry's existing origin-to-scope pairing, leave that entry unchanged and report the specific ambiguity. Prune the entry and add a receipt only when no origins remain.
- **Canonical feature slug:** the plan filename without its leading date prefix; it identifies the plan's own prompt-log entry.
- **Plan-backed removal receipt:** `PLAN-PROMPTS-PRUNE: <slug> -> <plan-file-path>`; own and collateral removals cite the plan whose landing caused that removal, while ordinary monitor removals cite the plan whose `Backlog origin:` exactly matches the removed origin. The plan is in the plans root or its completed twin.
- **Ad-hoc removal receipt:** `EXEC-PROMPTS-PRUNE: <slug> -> <landing-commit>`; use for an ad-hoc-superseded origin even when its entry is in PLAN-PROMPTS, with the recorded ad-hoc landing commit as witness.
- **Write boundary:** an overlapping primary commit acquires or reuses the primary done lock, then the repo-wide merge lock before staging/index writes or final log read, and holds both through commit and failure recovery. Before staging, verify no prior staged delta exists on operation-owned paths; stage and commit only those paths. On commit failure, unstage only those paths and verify their staged state is restored before release; if recovery cannot be verified, block later primary writes and report through the existing recovery path. If done acquisition fails, do no work; if merge acquisition fails, release done token-fenced and do no work. After successful recovery, release merge then done on every exit, attempting done release even if merge release fails. This covers monitor commits, Phase 0 freeze commits, and primary-placement checkpoints. A worktree authoring session targets the primary done-lock key from primary-checkout context for Phase 0. Worktree branch commits stay isolated and use the existing merge-lock guard.
- **Receipt selection:** in one operation, remove every independently eligible origin and paired scope arm from a target heading. If origins remain, add no receipt. If the heading becomes empty, write one receipt using the class and witness of the last removed origin in the original `Origins:` order.
- **Origin discovery:** the existing read-only search that establishes which backlog origins an entry served at the current or base commit and whether the landing range removed one.
- **Scope arm:** the part of a prompt entry that describes work for one origin.
- **Guard-liveness stack ratio:** the guard-liveness ledger’s count of recorded catches compared with recorded incidents.
- **Pending-change audit:** the separate warning-only check for prompt-log changes that have not yet been recorded by a landing.

## Why

A next-heading anchor can still include receipt lines owned by neighboring landings. The 2026-10-19 review caught a neighboring receipt at the tail of a correctly bounded range; the audit stayed green because the existing closeout receipt step was not committed. Receipts are standalone ledger lines with their own slug and witness, and one slug may have receipts from multiple removal events. Preserve every pre-existing ledger line; the existing closeout receipt step records the current operation. The source backlog separates two remedies. This plan covers the procedural range inventory; detection of unrecorded pending prompt-log changes is separately tracked and must begin warning-only under the machinery admission protocol.

## Gist & Examples

TLDR: inventory the full prompt-log prune range, remove only covered prompt scope, and preserve every receipt line, driven by the neighboring-receipt loss.

**Before (today):** A landing finds the next heading and deletes the range. A neighboring receipt line sits at the range tail and is removed even though the start and end headings are correct.

**After (this plan):** Before editing, the landing or monitor reads the full range and lists every receipt. It removes covered origins with their paired scope arms, narrows partial entries to unresolved origins, and preserves old receipts; closeout records only full-entry removals using each log's existing witness format.

**Edge cases:** A receipt may sit at the end of a correctly anchored range; live claims keep retained entries frozen; mixed receipt classes still produce one deterministic full-removal receipt; ambiguous targets remain unchanged; only the separate audit is report-only.

## Outcome

The operative procedures inventory each prune range, remove only covered prompt scope, keep unresolved origins available for dispatch when their freeze conditions clear, and preserve all pre-existing receipts. Phase 0 must complete its locked freeze before plan work; an unavailable lock stands the authoring session down and removes only its own claim through the ownership-checked rule. This plan adds procedural coverage and warning-only text pins; it does not claim that the separate pending-change audit detects staged or worktree edits, which remains scoped to the linked pending-audit backlog row.

- The procedure reads the actual next heading rather than assuming adjacent entries.
- A landing's own entry slug is the exact canonical feature slug derived by stripping the plan filename's leading date prefix; other discovered entries and targeted entries follow existing discovery and selection rules.
- Coverage is established per origin by the selected entry's existing evidence: this plan's landing covers its PLAN-PROMPTS origin; collateral discovery covers only origins it reports removed in the landing range; an ordinary PLAN-PROMPTS monitor origin is covered only when a plan in the plans root or completed twin has a `Backlog origin:` value exactly equal to that origin path. Entry-slug plan discovery alone covers only the origin named by that plan and never any other `Origins:` bullet. An EXEC-PROMPTS target is covered only by its frozen pre-landing origin and recorded landing commit.
- A partial removal deletes only covered origin bullets and scope arms explicitly paired with those origins. The remaining prompt and scope arms must name only retained origins. If pairing is ambiguous, that entry is unchanged and the ambiguity is reported; other independently authorized entries remain eligible.
- Clear `Frozen:` after landing only when a fresh check finds no live claim or worktree for any retained origin; otherwise preserve it. Apply the check to retained origins, not the landing plan's own authoring claim.
- Every pre-existing receipt line stays byte-for-byte and in order regardless of slug. Remove every eligible origin and paired scope arm in one pass. Partial removal adds no receipt; full removal uses the last removed origin's class and witness. Own/collateral PLAN uses the covering landing plan; ordinary PLAN uses the exact-origin plan; EXEC/ad-hoc uses the recorded landing commit. Monitor writes stay targeted and only the separate audit stays report-only. Before an overlapping primary commit, acquire or reuse primary done then repo merge before staging/final read. Reject staged changes on owned paths, stage/commit only those paths, and recover/verify their staged delta on commit failure before release. This covers monitor, Phase 0, and primary-placement commits; Phase 0 targets the primary done key from primary-checkout context. Worktree branch commits stay isolated under existing landing guards.

Gate delta: extends the registered maintenance-pin checker with warning-only range, slug, coverage, refusal, partial-scope, freeze, receipt, and lock-lifecycle assertions. Receipt pins answer the 2026-10-19 neighboring-receipt catch (`docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md`); lock pins cover the R19 primary-placement race and release-failure findings (`.ai-playbook/reviews/2026-10-20-plan-review-plan-prompts-prune-range-content-inventory-pa284eb99-r19.md`). Guard-liveness stack ratio 28:39. Expected catches are uncommon; a false positive is one non-blocking warning. Review is due 2027-01-20. Missing pins warn and keep exit 0. Ambiguous targets stay unchanged while independent targets remain eligible. Monitor, Phase 0, and primary-placement commits use primary done then repo merge through commit and failure recovery; acquisition refusal writes nothing. Phase 0 stands down and monitor defers. Full removal uses the last removed origin; partial completion narrows scope and retains `Frozen:` while a retained origin has a live claim or worktree. No lane, state field, or lock is added. Promotion requires a production true catch and a pre-registered removal row naming sunset and criteria.

## Assumptions

- Derive authorization from existing evidence before resolving a target: bind a landing's own entry to exactly one heading whose `Frozen:` witness names the plan's authoring claim, whose `Origins:` includes the source backlog origin, and whose slug matches the canonical feature slug; accept collateral PLAN-PROMPTS entries only when read-only discovery identifies covered origins; accept an ordinary PLAN-PROMPTS monitor origin only when a plan in the plans root or completed twin has a `Backlog origin:` value exactly equal to that origin path. Entry-slug discovery covers only the origin named in that plan's header. Accept EXEC-PROMPTS origins only when the entry was frozen before its recorded ad-hoc landing commit. Remove only covered origin bullets and paired scope arms. For partial entries, retain only unresolved origins; if pairing is ambiguous, leave that target unchanged and report why. Clear `Frozen:` only after landing and a fresh check finds no live claim or worktree for any retained origin. Remove a section only when no origins remain; choose its single receipt from the class and witness of the last removed origin in original list order. Ambiguous, missing, duplicate, or shared evidence leaves that specific target byte-identical; other independently authorized targets remain eligible, and the whole log stays byte-identical only when none are authorized. Monitor, Phase 0, and primary-placement commits use primary done then repo merge before writes/final read through commit; they reject pre-staged changes on owned paths and recover only their staged delta after commit failure before releasing locks. Phase 0 refusal stands down; monitor refusal defers. Worktree branch commits remain isolated and use existing landing guards. Preserve every receipt line. PLAN-PROMPTS owns shared prune/freeze rules; consumers state only operation-specific deltas. Basis: `scripts/plan_readiness.py::feature_slug`, `docs/history/backlog/PLAN-PROMPTS.md` Prune and Freeze rules, and `agents/skills/maintenance/decisions.md` ad-hoc completion rule.
- Pending-change audit remains in the separate warning-only backlog row and is not implemented by this plan. Basis: the origin backlog's separate-arm instruction and the repository Machinery admission protocol.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep both receipt grammars and ownership classes unchanged; remove all independently eligible origins in one operation, and use the last removed origin's class and witness for the single receipt when the heading empties. After partial completion retain only unresolved scope and preserve `Frozen:` while any retained origin has a live claim or worktree. PLAN-PROMPTS owns shared prune and freeze behavior.
- Preserve every pre-existing receipt line. Primary monitor, Phase 0, and primary-placement commits use primary done then repo merge through commit; on commit failure recover only their staged delta before release. Phase 0 stands down and monitor defers on lock refusal. Keep only the separate audit report-only.
- Do not add a second gate, persistent state, or a lock.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: a receipt at the tail of a correctly anchored range is inventoried before deletion; slug discovery covers only an origin whose exact path appears in its `Backlog origin:` header; full removal emits one receipt from the last removed origin in list order.
- Safety: only covered origins are removed; ambiguous targets stay unchanged while independent targets remain eligible; primary writes hold done then repo merge through commit, recover owned staged paths before release on failure, and preserve other staged paths; unresolved origins remain scoped until freeze conditions clear, and only the separate audit remains report-only.
- Maintainability: the existing procedures describe one repeatable full-range check without new machinery.

**Done when:** both log rules and all operative procedures cover full-range inventory, per-origin coverage, target-specific no-edit behavior, partial-scope narrowing, live-claim freeze retention, one receipt witness on full removal, complete monitor lock lifecycle, and receipt preservation; warning-only pins cover success and refusal outcomes; the two backlog rows retain distinct scopes.

**Ship when:** none; repository-only behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Documentation:**
- `docs/history/backlog/PLAN-PROMPTS.md` *(edited)* - standing prune ownership rule and this entry's dispatch scope.
- `docs/history/backlog/EXEC-PROMPTS.md` *(edited)* - reference to shared PLAN-PROMPTS prune/freeze policy plus ad-hoc-specific eligibility, landing-commit witness, and receipt details.
- `agents/skills/plans/SKILL.md` *(edited)* - landing closeout procedure.
- `agents/skills/maintenance/template-authoring.md` *(edited)* - authoring landing closeout step procedure.
- `agents/skills/maintenance/decisions.md` *(edited)* - monitor prune duties.
- `agents/skills/maintenance/zcode.md` *(edited)* - runtime monitor lock acquisition and token-fenced release sequence.
- `agents/skills/execute-plan/worktree-first.md` *(edited)* - execution landing closeout step procedure.

**Tests:**
- `scripts/check_maintenance_pins.sh` *(edited)* - pin full-range inventory, canonical plan-to-entry slug binding, and preservation of every existing receipt line across each operative procedure.

**Plan-related extension:**
- `docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md` *(edited)* - scope this origin to the procedural arm, record selective preservation, and point to the separate audit row.
- `docs/history/backlog/2026-10-20-prompt-log-pending-prune-audit-warning.md` *(new)* - preserve the pending-audit arm with warning-only admission and promotion boundary.

**Out of scope; reject unless plan-related:** pending-delta checker behavior, receipt grammar changes, historical log repair, additional gates, persistent state, and any change to monitor report-only posture.

## Validation Commands

```bash
set -e
# PATH selects the local toolchain; HOME resolves the configured public hygiene script and user patterns.
validation_path="${PATH:-/usr/bin:/bin}"
validation_home="${HOME:?HOME is required for the configured public hygiene scan}"
repo_root="$(env -i PATH="$validation_path" git rev-parse --show-toplevel)"
validation_tmp="$(env -i PATH="$validation_path" mktemp -d /tmp/prompt-prune-validation.XXXXXX)"
trap 'rm -rf "$validation_tmp"' EXIT
printf '%s\n' '{"schema":1,"window":{},"guards":{}}' > "$validation_tmp/gate_liveness_ledger.json"
(
  cd "$repo_root"
  env -i PATH="$validation_path" HOME="$validation_home" TMPDIR="$validation_tmp" TZ=UTC LC_ALL=C GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PINS_RECORDED_RED_REGISTER="$validation_tmp/gate_liveness_ledger.json" bash scripts/check_maintenance_pins.sh
  env -i PATH="$validation_path" HOME="$validation_home" TMPDIR="$validation_tmp" TZ=UTC LC_ALL=C GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null python3 -c 'from pathlib import Path; p=Path("scripts/check_maintenance_pins.sh"); assert "\u2014" not in p.read_text(), f"{p}: em dash found"'
  env -i PATH="$validation_path" HOME="$validation_home" TMPDIR="$validation_tmp" TZ=UTC LC_ALL=C GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null bash "$validation_home/.ai-playbook/scripts/scan-public-hygiene.sh"
)
```

A command's expected outcome is exit 0. A failure blocks the task checkbox that owns it.

### Task 1: Inventory the full prune range in operative procedures

Files:
- `docs/history/backlog/PLAN-PROMPTS.md` *(edited)*
- `docs/history/backlog/EXEC-PROMPTS.md` *(edited)*
- `agents/skills/plans/SKILL.md` *(edited)*
- `agents/skills/maintenance/template-authoring.md` *(edited)*
- `agents/skills/maintenance/decisions.md` *(edited)*
- `agents/skills/maintenance/zcode.md` *(edited)*
- `agents/skills/execute-plan/worktree-first.md` *(edited)*

- [x] Read each target through its actual next heading; inventory receipts and bind own, collateral, monitor, or ad-hoc targets using Outcome evidence. PLAN-PROMPTS owns shared prune/freeze rules; consumers keep operation-specific deltas. [class: IMPLEMENTATION_REQUIRED]
- [x] Primary monitor, Phase 0, and primary-placement commits use primary done then repo merge before writes/final read; refuse pre-staged changes on owned paths, stage/commit only owned paths, and recover/verify only their staged delta before releasing locks on commit failure. Phase 0 targets the primary done key from primary-checkout context; add no lock. [class: IMPLEMENTATION_REQUIRED]
- [x] On Phase 0 refusal, release acquired locks, remove only this session's claim by the ownership-checked rule, and stand down before plan-file work; monitor refusal leaves logs unchanged and defers its write. [class: IMPLEMENTATION_REQUIRED]
- [x] A uniquely bound own entry may remove its covered origin even when others remain; absent association is a no-op, and independent collateral targets remain eligible. [class: IMPLEMENTATION_REQUIRED]
- [x] For mapped partial entries, remove covered origins and paired scope, retain unresolved origins, and keep `Frozen:` while any retained origin has a live claim/worktree. Ambiguous mapping or missing evidence leaves that target unchanged and reports why. [class: IMPLEMENTATION_REQUIRED]
- [x] PLAN monitor targets require an exact `Backlog origin:` match in a plan or completed twin; slug discovery covers only its plan's named origin. EXEC requires the frozen pre-landing origin and recorded landing commit. [class: IMPLEMENTATION_REQUIRED]
- [x] Remove every eligible origin in one pass. Partial removal adds no receipt; full removal uses the last removed origin's witness: covering landing plan for own/collateral PLAN, exact-origin plan for ordinary PLAN, recorded landing commit for EXEC/ad-hoc. Preserve prior receipts byte-for-byte and in order. [class: IMPLEMENTATION_REQUIRED]
- [x] Duplicate headings or absent/shared own-entry witnesses leave that target byte-identical; the log is unchanged if none qualify. [class: IMPLEMENTATION_REQUIRED]
- [x] Walk isolated PLAN/EXEC copies across refusal, collateral, tail receipts, mixed origins, and live/cleared claims; compare bytes, scope, freeze, and receipt order. Trace lock/no-op and write/commit/recovery/release failures; assert unrelated staged paths and release order; leave no fixture or second implementation. [class: REPOSITORY_TEST]
- [x] Verify exact PLAN-origin matches (including completed twins), own-origin-only slug discovery, and pre-frozen EXEC plus recorded commit. Assert covered targets change, unauthorized ones stay byte-identical, and full-removal receipts use matching witnesses. [class: REPOSITORY_TEST]
- [x] Keep the source backlog on range inventory/receipt preservation and the separate backlog on pending-change audit; only that audit remains report-only. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the procedure and split the audit arm

Files:
- `scripts/check_maintenance_pins.sh` *(edited)*
- `docs/history/backlog/2026-10-15-plan-prompts-prune-end-anchor-overreach.md` *(edited)*
- `docs/history/backlog/2026-10-20-prompt-log-pending-prune-audit-warning.md` *(new)*

- [x] Add warning-only pins for range inventory, slug/origin binding, per-origin coverage, target refusal, partial scope, freeze retention, one final receipt, lock lifecycle, receipt preservation, and audit separation across rules and procedures. [class: REPOSITORY_TEST]
- [x] The normal fixture satisfies every pin without a placement warning. Give each refusal, no-edit, Phase 0 freeze, primary-placement commit, and lock-release branch its own named warning-only pin; a missing-clause probe emits that pin's warning while the suite remains exit 0. [class: REPOSITORY_TEST]
- [x] Keep the pin family warning-only; a future promotion requires a production true catch and a pre-registered registry-removal row naming sunset and promotion criteria. [class: REPOSITORY_TEST]
- [x] Make recorded-red evaluation accept an explicit as-of date in selftests and use the system date in production; with as-of 2026-10-20, expect review-by 2026-10-20 live and 2026-10-19 expired, asserting both. [class: REPOSITORY_TEST]
- [x] Run pin validation from the intended repository root with the controlled environment and empty register fixture in Validation Commands. [class: IMPLEMENTATION_REQUIRED]
- [x] In the pending-audit backlog row, state that the audit inspects staged or worktree prune-range bytes and detects foreign receipt-line removals. [class: IMPLEMENTATION_REQUIRED]
- [x] Include the linked incident, expected catch frequency, false-positive cost, review date, warning-only posture, pre-registered removal-row requirement, first production true-catch boundary, and separate reviewed promotion criteria; prohibit promotion until a later reviewed change supplies and meets those inputs. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the source backlog's incident evidence, narrow its expected outcome and fix shape to preserving all existing receipts in this procedural arm, and point to the new pending-audit backlog row. [class: IMPLEMENTATION_REQUIRED]
- [x] Record in the fix-class origin why a sanctioned exit, false-positive removal, or simpler selection flow cannot safely resolve ambiguous or unauthorized targets. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the complete Validation Commands block and require every command to exit 0. [class: REPOSITORY_TEST]
- [x] Confirm changed paths are limited to Review Scope and that the two backlog rows describe non-overlapping scopes. [class: IMPLEMENTATION_REQUIRED]
