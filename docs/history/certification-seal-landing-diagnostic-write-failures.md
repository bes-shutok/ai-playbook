# Certification seal landing diagnostic write-failure receipts

Receipt escalation chain (this file is the chain's single home; consumers link here instead of restating it): one diagnostic run appends one serialized receipt to the primary ledger `docs/history/certification-seal-landing-diagnostics.md`; a partial or mismatched primary write routes the same serialized receipt to one append in this file, together with the recorded primary-write error and the warning value kept from the applicable matrix row; a failed fallback append emits the receipt to the running maintenance session transcript, and the next maintenance sunset review owns recovery from that transcript into this ledger before deciding whether no catch occurred. No lock is taken, and a storage failure never blocks plan closeout or promotes the diagnostic.

Append contract: each receipt is written as one append-mode (`O_APPEND`) write with its complete bytes verified after the write.

Retention: both ledgers and their origin and dispatch-entry links are removed only when neither tracked file has a receipt; either file holding any receipt, including confirmed passes, retains both files and links (the dispatching entry's Machinery admission).

Outcome matrix: the single receipt outcome matrix lives in Task 2 of the certifying plan `docs/history/plans/2026-10-20-certification-seal-landing-survival.md` (after archive, `docs/history/plans/completed/` under the same basename) and is the only source for receipt branch behavior.
