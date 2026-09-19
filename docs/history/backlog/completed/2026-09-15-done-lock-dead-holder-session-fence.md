# Backlog: done lock must reclaim a verified-dead owner despite a surviving session fence

**Captured:** 2026-09-15 (user-reported blockage while finalizing the review-coverage session)
**Status:** done (2026-09-15; implemented in `scripts/done-lock.sh` and `agents/skills/done/SKILL.md`)
**Priority:** high
**Origin:** done Step 0 blocked on a dead holder PID while the matching `.ai-playbook/done-lock.session` remained

## Finding

The done lock correctly recorded a holder PID and process identity, and the process table verified that the holder was dead. However, `is_dead_holder_lock` rejected recovery whenever the matching session fence remained. This made a dead one-shot shell appear held until the 30-minute stale-clean escape, so a new done workflow could not proceed automatically.

## Required behavior

After `DONE_LOCK_DEAD_HOLDER_GRACE_SECS` has elapsed, a lock whose recorded holder is independently verified dead must be automatically reclaimable on the next `acquire` or `wait-acquire`, even when the matching session fence remains. The replacement generation must still use the existing token and epoch compare-and-swap removal path.

## Safety boundary

The session file remains a protection signal for live or ambiguous holders, but it is not proof that the owner is alive. PID reuse and identity mismatch remain non-stealable. Incomplete metadata and locks inside the dead-holder grace period remain protected.

## Verification

- The built-in lock self-test now proves that a dead fenced holder is reclaimed automatically.
- The self-test still proves that a stale live fenced holder is not auto-stolen and requires `stale-clean`.
- Existing PID-identity and generation compare-and-swap fixtures remain in the same suite.
