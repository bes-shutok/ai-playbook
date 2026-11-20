# Certification seal landing diagnostic write-failure receipts

Receipt escalation chain (this file is the chain's single home; consumers link here instead of restating it): one diagnostic run appends one serialized receipt to the primary ledger `docs/history/certification-seal-landing-diagnostics.md`; a partial or mismatched primary write routes the same serialized receipt to one append in this file, together with the recorded primary-write error and the warning value kept from the applicable matrix row; a failed fallback append emits the receipt to the running maintenance session transcript, and the next maintenance sunset review owns recovery from that transcript into this ledger before deciding whether no catch occurred. No lock is taken, and a storage failure never blocks plan closeout or promotes the diagnostic.

Content contract: the primary ledger's Receipt content contract governs every record appended here, including direct run-identity-mismatch records - the mask-before-append duty and the pre-append probe apply before any append, the same remediation and terminal arm routing.

Append contract: each receipt is written as one append-mode (`O_APPEND`) write with its complete bytes verified after the write.

Retention: both ledgers and their origin and dispatch-entry links are removed only when neither tracked file has a receipt; either file holding any receipt, including confirmed passes, retains both files and links (the dispatching entry's Machinery admission).

Outcome matrix: the single receipt outcome matrix lives in the plans skill's Plan Lifecycle post-squash diagnostic outcome matrix (`agents/skills/plans/SKILL.md`) and is the only source for receipt branch behavior; this ledger receives both records whose primary append failed and direct run-identity-mismatch records, each carrying the matrix row's warning value; the certifying plan's archived Task 2 matrix is a historical snapshot, not a second operative source.

## 2026-11-15 collaborator-wiring-idiom-and-alignment-receipt (authoring landing 997f9e637224f634c50fbfadefbe18d91bb47dab; run sess_8a54444d-f7d8-464c-b71b-c7cd24140e8e)

- outcome: run-identity row per the outcome matrix - run identity missing (neither validator ran); warning not_observed
- expected identities: plan docs/history/plans/2026-11-15-collaborator-wiring-idiom-and-alignment-receipt.md certified at digest fb82496fcfb7c687a0aa1047680608782d27059002c64708f9558e43c10d4cb6 (r2 ready=yes zero blocking); source worktree ai-playbook-worktrees/collaborator-wiring-idiom-and-alignment-receipt (canonical digest 616b0c11270c28365ddd1253bd371bcdbe6c84a94665936ba134481003e48a61); certification-time branch tip 4e76798a1, replayed post-rebase as bcd8ed63da34bce902c4dd03d1890b03e7a4c256 (same blob, seal re-pinned)
- observed identities: no DONE_RUN_ID / DONE_RUN_MANIFEST captured; no done-run setup manifest under docs/tmp/done-session/ names this plan (the run's closeout used the worktree-first baseline-capture arm, manifests 20261115T045506Z-2fffbd4f5c37, none carrying owned_plan_paths for this plan)
- landing context: landed tip 997f9e637224f634c50fbfadefbe18d91bb47dab; landed plan bytes through refs/heads/main digest fb82496fcfb7c687a0aa1047680608782d27059002c64708f9558e43c10d4cb6, equal to the certified r2 digest (landed-bytes verification succeeded through the branch ref); the landing's own gates all passed (tree equality, source-branch containment, parentage, default-branch ancestry, swap-lock, reconcile rows restored=3 removed=0)
- actionability: needs-recert remains available through the standing re-verification path; warning-only, no closeout stop
