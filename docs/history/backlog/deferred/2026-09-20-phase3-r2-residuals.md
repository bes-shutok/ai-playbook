# Backlog: phase 3 r2 residuals (probe coverage, vocabulary, hygiene)

- **Status:** open
Priority: deferred (formal-hardening triage 2026-09-22 full sweep per the project-priority-profiles directive: on this personal/pet repo formal fixes defer, no witnessed failure; probe coverage + envelope vocabulary + field hygiene. Revive on the contract is next reworked under a live plan, or a project-priority-profile change.)
- **Origin:** execute-plan phase 3 code review r2 (correctness + contract-docs lenses, 2026-09-20)

## Findings

1. Probe coverage beyond the pinned set: several changed contract sentences still lack deletion-failing probes (the plan's global bar): the manifest-lock-fences-manifest-only sentence (runtime-contract.md:164-166); reclaim-refuses-parked-claim (:180-181) and the queue-head preserve-and-reconcile sentence (:181-184); both terminal-refused evidence-write obligations (:888-891, :964-968); the done-boundary and archived-plan whitespace-only/three-marker restatements (:906-909, :958-963); partially the empty-manifest clause (:779-781); the diagnose selection rule and none→success/blocked→preserve-and-reconcile mapping (:977-1013, only enum + read-only rule pinned); the reclaim paragraph's quoted evidence literals (:216-218, only the paraphrase is pinned).
2. Diagnose CLI-envelope vocabulary: `_operation_diagnose` prints the envelope verbatim with `reason_code` equal to the classification (worker-failure, stale-evidence, inclusion, terminal-gate, user-interruption, none), but the contract's closed-set/CLI-envelope carve-out names only created/reclaimed/readiness decision codes; add one sentence to the Diagnose subsection.
3. In-place capacity resume leaves stale fields on the relaunched task: `_park_waiting_capacity_locked` writes `task["resume_allowed"] = false` and `task["blocked_receipt"]`, and `_mark_claim_launched` (unlike the reclaim reset) never strips them, so a live launched task durably carries a stale capacity blocked receipt. All current readers are gated on task status blocked, so behavior is unchanged; hygiene fix: strip the fields in the parked-relaunch path like the reclaim reset does.
4. Em-dash hygiene rider: commit 053791cf's rewritten line in agents/skills/execute-plan/SKILL.md:505 carried over two pre-existing U+2014s; the added-lines gate scopes committed insertions out by design, so fix on the next touch of that paragraph.

## Driving force

The durable-probe criterion is only as strong as its coverage; these spans can drift silently today, and the stale receipt fields are exactly the kind of misleading durable evidence the diagnose operation downstream consumes.
