# Plan: Preserve a safe continuation path after done-lock context compaction

Backlog origin: `docs/history/backlog/2026-10-26-done-lock-context-recovery-after-compaction.md`
Driving force: efficiency
Plan review record: `.ai-playbook/reviews/2026-10-26-plan-review-done-lock-context-compaction-recovery-r*.md` (highest rN for this source path is authoritative)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: `docs/tmp/authoring-claims/2026-10-26-done-lock-context-recovery-after-compaction.md` (session `01a178b1-5677-70c1-ac05-effe8f0f5a76`)

## Terms

- **Step 0 witness**: the lock path and SHA-256 fingerprint of the original setup token retained in session context; the raw token is never durable.
- **Context compaction**: loss of working conversation context that can remove the original token and witness from the active session.
- **Separate-checkout continuation**: continuing unrelated authorized work from another checkout with its own done lock while leaving the original worktree and lock untouched.

## Why

Context compaction can erase the original Step 0 witness, and the done skill correctly stops rather than infer ownership from a manifest or current lock metadata. That safe stop can also halt unrelated authorized work. The skill should state the separate-checkout continuation clearly while preserving the original lock and stop condition.

## Gist & Examples

TLDR: Document separate-checkout continuation, improving efficiency while preserving the done skill's ownership stop.

Before: when compaction removes the original token or witness, the done skill stops safely, but its instructions do not clearly route unrelated authorized work to a separate checkout. After: the skill says to leave the original worktree and lock untouched, start a distinct new run for independent work from a separate checkout under that checkout's own lock and manifest, and return to the original recovery only when its original witness is available. The new run never reuses the original manifest or lock witness. No token is reconstructed or persisted.

## Outcome

The done skill directs operators to a distinct run in another checkout for unrelated authorized work after context compaction, without weakening lock ownership checks.

- Missing original witness continues to stop recovery before release.
- Unrelated authorized work can continue in a distinct run from a separate checkout with that checkout's own done lock and manifest.
- The original worktree and lock remain untouched until the original witness is available for its token-checked recovery.

Gate delta: zero added or removed runtime gates, refusals, fences, protocol layers, schema fields, or blocking review duties; this plan changes only workflow documentation.

## Assumptions

- The done skill's current token-checked recovery remains authoritative; basis: `agents/skills/done/SKILL.md`, Step 6.
- Separate-checkout continuation is limited to unrelated authorized work and does not release the original lock; basis: the backlog origin and current per-checkout done-lock behavior.
- The from-holder generation-binding origin remains open and outside this plan pending a safe policy resolution; basis: its separate runtime scope and the user-approved split.

Decision points requiring a grill: none remain.
Scope extensions (maintenance-selected arm): durable token or witness handoff across compaction: omit-extension.

## Standing constraints

- Never persist the raw lock token or infer ownership from a manifest or current metadata.
- Do not release, stale-clean, or otherwise alter the original live worktree's lock as part of this continuation.
- Preserve the existing stop when the original token or witness is missing.

## Evaluation Criteria

- Correctness: the instructions distinguish original-worktree recovery from separate-checkout continuation.
- Safety: the missing-witness stop remains explicit, and the workaround never releases or alters the original lock.
- Clarity: an operator can identify the next checkout action without reconstructing or transferring the original token.

**Done when:** the done skill documents the separate-checkout workaround and preserves the existing recovery stop; plan readiness and review-plan certify the final bytes.

**Ship when:** documentation is landed with the plan under the repository's existing worktree closeout.

## Review Scope

**Explicit must-fix:**

**Documentation:**
- `agents/skills/done/SKILL.md` (Task 1)

**Plan-related extension:** files causally required to complete the documentation task.

**Out of scope; reject unless plan-related:** `scripts/done_run.sh` and `scripts/done-lock.sh`; reason: this plan does not change runtime lock behavior.

## Validation Commands

- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-26-done-lock-context-compaction-recovery.md`
- `bash scripts/scan-public-hygiene.sh --files docs/history/plans/2026-10-26-done-lock-context-compaction-recovery.md agents/skills/done/SKILL.md`

## Tasks

### Task 1: Document the separate-checkout continuation

Files:
- `agents/skills/done/SKILL.md`

- [ ] Given context compaction removed the original Step 0 token or witness, expect the done skill to stop before release and forbid inferring ownership from current metadata or the manifest. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given unrelated authorized work remains after that stop, expect the skill to direct it to a distinct new run in a separate checkout using that checkout's own lock and manifest, never reusing the original manifest or lock witness; the original worktree and lock remain untouched. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the original checkout is resumed, expect the skill to permit token-checked recovery only when the original witness and token are available. [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the change adds no lock, gate, validator, ledger, or recovery ceremony. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: clarify done-lock continuation after compaction` [class: IMPLEMENTATION_REQUIRED]

## Plan invariants

- The original worktree lock is never altered by the separate-checkout workaround.
- Missing ownership evidence never becomes permission to release.
- The raw token remains out of durable records.

