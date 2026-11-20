# Backlog: stack-review-round-helper follow-ups

Status: open
Priority: medium
Class: fix-class
Origin class: consumer-feedback (pet)
Workflow: plan
Dedup probe: stack_review_round.sh restack restore/parentage/coherence follow-ups (no sibling row)

Driving force: intermediate task review (Step 1.2b) of execute-plan run stack-review-fix-round-ownership, Task 1, recorded four backlog candidates against scripts/stack_review_round.sh; none blocks the plan's checklist letter, each is a hardening gap witnessed by the reviewer's live probes.

- Restore desync: `restore_chain_from_backups` restores refs via `git update-ref` only, leaving the checked-out chain member with staged changes after a witness/parentage refusal (witnessed: wrong-order probe left `M a.txt` staged on the checked-out branch). Fix: `git reset --hard` the checked-out member to its backup after the ref restores.
- Parentage-failure arm has no suite fixture: the arm works (probe: commit-count refusal, `OUTCOME: fail`, restore lines) but no test pins it; add a fixture.
- Late wrong-chain-order detection: with an incoherent `--chain`, link 0 replays before link 1's safety-witness refusal surfaces the incoherence; a pre-flight coherence check (backup of chain[i-1] ancestor of chain[i] before the backup loop) would refuse before any rewrite.
- Register wiring follow-up: the helper carries the OUTCOME_CONTRACT header declaration but has no decision-script register row in scripts/OUTCOME_CONTRACT.md; wire it (the plan's follow-up disposition routes this as a backlog row, never a silent helper edit).

Cluster: 2026-11-14-stack-review-fix-round-ownership
- Phase 3 r1 additions (same run's review panel, all non-blocking, each premise-checked): restack old-boundary blind spot (a recorded old tip that is an ancestor but not the actual base passes witness+count and resurrects parent commits with OUTCOME pass; fix class: pre-flight pred_old == backup^ boundary refusal); multi-edited affected test asserts presence not chain order; push-leases ls-remote read-failure arm and indeterminate-dominates aggregation lack fixtures; round section lacks bidirectional Integration Points rows toward receiving-review and github-pr-workflow; "refresh-descriptions" is a step label, not a helper subcommand (wording nit); unconditional "Replies post only after the push verifies" qualifier vs the no-code-change reply path.
