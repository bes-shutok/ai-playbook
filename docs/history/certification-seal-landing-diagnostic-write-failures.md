# Certification seal landing diagnostic write-failure receipts

Receipt escalation chain (this file is the chain's single home; consumers link here instead of restating it): one diagnostic run appends one serialized receipt to the primary ledger `docs/history/certification-seal-landing-diagnostics.md`; a partial or mismatched primary write routes the same serialized receipt to one append in this file, together with the recorded primary-write error and the warning value kept from the applicable matrix row; a failed fallback append emits the receipt to the running maintenance session transcript, and the next maintenance sunset review owns recovery from that transcript into this ledger before deciding whether no catch occurred. No lock is taken, and a storage failure never blocks plan closeout or promotes the diagnostic.

Append contract: each receipt is written as one append-mode (`O_APPEND`) write with its complete bytes verified after the write.

Retention: both ledgers and their origin and dispatch-entry links are removed only when neither tracked file has a receipt; either file holding any receipt, including confirmed passes, retains both files and links (the dispatching entry's Machinery admission).

Outcome matrix: the single receipt outcome matrix lives in the plans skill's Plan Lifecycle post-squash diagnostic outcome matrix (`agents/skills/plans/SKILL.md`) and is the only source for receipt branch behavior; this ledger receives both records whose primary append failed and direct run-identity-mismatch records, each carrying the matrix row's warning value; the certifying plan's archived Task 2 matrix is a historical snapshot, not a second operative source.
