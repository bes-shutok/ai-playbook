# Plan: Scope the done-lock blocked-acquire stop to its lock-bound write set

Backlog origin: docs/history/backlog/2026-10-30-done-lock-hold-overbroad-commit-stop.md
Driving force: simplicity; secondary: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-04-plan-review-done-lock-hold-overbroad-commit-stop-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: done-lock-hold-overbroad-commit-stop.md (session sess_deb2c527-7de4-4e88-87ac-e99c0f6e76ba)

## Terms

- **Done lock:** the per-checkout closeout lock in `scripts/done-lock.sh`; the done skill's Step 0 acquire takes it for the closeout run.
- **Blocked acquire:** the Step 0 outcome when the done lock cannot be taken within the agent wait; the skill returns `blocked` with the holder evidence.
- **Lock-bound write set:** the writes a done-lock hold actually defers: the closeout run's own staged landing set, plus any primary rolling prompt-log write (the rolling logs' Write boundary rule).
- **Write boundary rule:** the rule in `docs/history/backlog/PLAN-PROMPTS.md` that scopes mandatory primary done-lock serialization to primary rolling prompt-log writes, routed through `scripts/done_run.sh`'s ref-bound transaction.
- **Unrelated path-scoped commit:** a commit whose changed paths touch no lock-bound surface (the witnessed case: a two-line history-record receipt addition).
- **Agent wait:** `DONE_LOCK_AGENT_MAX_WAIT_SECS`, default 90 seconds, the Step 0 bounded wait before returning `blocked`.
- **Dead-holder grace:** `DONE_LOCK_DEAD_HOLDER_GRACE_SECS`, default 5 seconds, the minimum age before a verified dead holder is auto-reclaimable on acquire.
- **stale-clean:** the explicit operator escape that removes a stale or abandoned hold; `DONE_LOCK_STALE_SECS` (default 1800 seconds) governs when it may remove a session-fenced lock.
- **Direct-commit class:** the ordinary ad-hoc work class defined in `agents/skills/execute-plan/worktree-first.md` (its Direct-commit class paragraph); cited as a boundary text that already governs its own commits, not changed by this plan.

## Why

The Step 0 blocked-acquire sentence reads as a blanket commit veto: one session deferred an unrelated two-line history-record receipt because another run held the primary done lock, without checking whether that commit touched a lock-protected surface; the receipt landed only after the hold died and was recovered. The boundary texts themselves (the Write boundary rule, the direct-commit class) already scope their own lock needs correctly; only the stop sentence overreaches.

## Gist & Examples

TLDR: Scope the done blocked-acquire stop to its lock-bound write set, so a hold cannot be read as a blanket commit veto.

Before: `agents/skills/done/SKILL.md` Step 0 says "return `blocked`, and do not commit"; a session holding unrelated ready-to-commit prose defers it on a held lock and waits out the recovery.

After: the same sentence names the lock-bound set the stop covers (the run's staged landing set and primary rolling-log writes) and states that a hold does not classify an unrelated path-scoped commit as lock-bound: the commit's own governing lane, with its commit rules, preconditions, and holds, decides when it can land.

## Outcome

A held done lock, by itself, defers only the writes the lock actually protects; it never classifies an unrelated commit as lock-bound: the commit's own governing lane decides when it can land.

- A blocked acquire stops only the closeout's lock-bound set: the run's staged landing set and primary rolling-log writes under the Write boundary rule.
- An unrelated path-scoped commit is not classified as lock-bound by the hold: its own governing lane's commit rules, preconditions, and holds decide when it can land (for the direct-commit class, that lane's closeout integration and its compatibility preconditions govern unchanged).
- The agent wait, dead-holder grace, and stale-clean threshold keep their distinct recorded jobs with no value change.

Gate delta: none added; removes the unqualified prose commit stop in done Step 0 (narrowed to the lock-bound write set); no gate, fence, refusal class, protocol layer, or schema field changes.

## Assumptions

- assume the misclassification root is the unqualified "do not commit" reading of the Step 0 blocked-acquire sentence; basis: the origin incident narrative plus the sentence wording, and no other skill text mandates a blanket commit veto (checked 2026-11-04 across `agents/skills/done/SKILL.md`, the Write boundary rule, and the direct-commit class); the Step 0 opening serialization sentence ("the done lock precedes learn and every commit step") remains a lane-level constraint that can still defer a closeout-routed unrelated commit while a hold stands, so this clarification removes the blanket-veto reading, not the lane's own hold
- assume the three timeout controls stay unchanged; basis: the origin records no measured hold-state transition establishing a recovery delay ("the earlier holder state and the exact time it died are not established") and instructs leaving values unchanged without such evidence
- assume the Write boundary rule scopes its own writes correctly and the direct-commit class already governs its own commits' rules and preconditions; basis: both texts read at authoring time (`docs/history/backlog/PLAN-PROMPTS.md` Write boundary rule; `agents/skills/execute-plan/worktree-first.md` direct-commit class paragraph, whose closeout integration lands through the done closeout and whose holder consult reads the merge lock); the done-lock classification dimension is the gap this plan's sentence fills

Decision points requiring a grill: single-sentence narrowing chosen over a lock-policy split; source: the entry prompt's instruction that a one-sentence resolution is preferred and timeout values stay unchanged, plus both boundary texts already scoping their own writes; 2026-11-04; done SKILL.md Step 0

## Evaluation Criteria

**Quality dimensions:**
- correctness: the narrowed sentence names exactly the two lock-bound write classes and preserves the serialization posture and the verified-dead recovery rule wording
- simplicity: one sentence region changed; no gate, lock, validator, ledger, or ceremony added (the Gate delta line is the machinery record); operative-text growth priced at review time per the repository anti-growth rules: the replacement is a measured net addition to done Step 0 (152-byte sentence to the 434-byte scoped form, +282 bytes), acknowledged here with no paying deletion available in a one-sentence clarification
- gate compatibility: the pins suite and the public-hygiene scan exit 0 over the changed skill text

**Done when:**
- `agents/skills/done/SKILL.md` Step 0 carries the scoped sentence and the unqualified form is absent
- `bash scripts/check_maintenance_pins.sh` exits 0
- the public-hygiene scan exits 0

**Ship when:**
- none; every acceptance criterion is repository-verifiable

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md` (Task 1)

**Tests:**
- none; acceptance is grep-and-scan based and rides the repository's existing pins and hygiene suites

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes the plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done-lock.sh`; reason: the timeout control values stay unchanged by design
- `scripts/done_run.sh`; reason: the 90-second agent wait stays unchanged by design
- `docs/history/backlog/PLAN-PROMPTS.md`; reason: the Write boundary rule already scopes its own writes correctly
- `agents/skills/maintenance/`; reason: no maintenance-lane surface is touched by this clarification

## Validation Commands

```bash
bash scripts/check_maintenance_pins.sh
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
grep -c "lock-bound set" agents/skills/done/SKILL.md
grep -q 'return `blocked`, and do not commit;' agents/skills/done/SKILL.md && echo "OLD FORM STILL PRESENT" && exit 1 || echo "old form gone"
```

### Task 1: Scope the blocked-acquire stop sentence

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/done/SKILL.md`

Replacement text (apply verbatim; both forms are single sentences inside the Step 0 acquisition paragraph; the landed bytes use plain backticks per the file's existing convention, the code-span backslash escaping below being plan notation only):

- Old form: `On a blocked acquire, run \`status\`, report the holder evidence, return \`blocked\`, and do not commit; \`stale-clean\` is the explicit operator escape only.`
- New form: `On a blocked acquire, run \`status\`, report the holder evidence, return \`blocked\`, and commit nothing in this closeout's lock-bound set (the run's staged landing set and primary rolling-log writes under the Write boundary rule); the hold does not classify an unrelated path-scoped commit as lock-bound: follow the commit's own governing lane's commit rules, preconditions, and holds; \`stale-clean\` is the explicit operator escape only.`

- [x] Apply the replacement text block above verbatim: the old form sentence is replaced by the new form sentence in the Step 0 paragraph [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the unqualified form is gone and the scoped form present: `grep -c "lock-bound set"` over `agents/skills/done/SKILL.md` returns at least 1 and `grep -q 'return \`blocked\`, and do not commit;'` finds nothing [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check_maintenance_pins.sh`, expect exit 0 [class: REPOSITORY_TEST]
- [x] Run the public-hygiene scan over the repository, expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: scope the done blocked-acquire stop to its lock-bound write set` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- Former backlog origin: `docs/history/backlog/2026-10-30-done-lock-hold-overbroad-commit-stop.md` (the blanket done-lock commit-veto witness). Executed 2026-11-04 by the one-shot exec run (landing b8036d031): the Step 0 blocked-acquire stop now scopes "commit nothing" to the closeout's lock-bound write set (the run's staged landing set and primary rolling-log writes under the Write boundary rule) and states a hold never classifies an unrelated path-scoped commit as lock-bound; timeout controls unchanged. Origin flipped covered by the landing rider, deleted in this completion pass; per-item archive not kept.
