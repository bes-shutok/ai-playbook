# Backlog: maintenance completion arm adopts the closeout audit duty explicitly

- **Status:** open
- **Origin:** residual F3 of the ref-move-integrity-fences plan review r3 (docs/reviews/2026-10-03-plan-review-ref-move-integrity-fences-r3.md), deferred Low, re-confirmed by execution review r1 (2026-10-03)
- **Driving force:** consistency - the maintenance skill's landing-completion arm names only the reconcile receipt in its success tail, so a literal actor on the maintenance-completed-landing path could run reconcile-only and skip the two `base_reflog_audit.py` subcommands and the diffstat receipt; both creation-time fences already run in that arm's adopted critical section, so this is backstop-only coverage on a rare deferred-landing-retry path

## Outcome

The maintenance skill's landing-completion arm names the closeout audit duty explicitly (the two `scripts/base_reflog_audit.py` subcommands beside the reconcile receipt and the diffstat receipt) instead of adopting it by region reference, so a literal actor cannot skip the audits.

Ship when: the arm's success tail lists the audit subcommands and diffstat receipt; the pins suite still holds.
