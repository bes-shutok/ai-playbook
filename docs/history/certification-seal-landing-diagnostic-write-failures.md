# Certification seal landing diagnostic write-failure receipts

One-shot fallback ledger for diagnostic receipts whose primary append into `docs/history/certification-seal-landing-diagnostics.md` failed: the same serialized receipt is appended here once, together with the recorded primary-write error and the warning value kept from the applicable matrix row.

Append contract: each receipt is written as one append-mode (`O_APPEND`) write with its complete bytes verified after the write; a partial or mismatched write here, after a failed primary append, sends the receipt to the running maintenance session transcript, and the next maintenance sunset review owns recovery from that transcript into this ledger before deciding whether no catch occurred. No lock is taken, and a storage failure never blocks plan closeout or promotes the diagnostic.

Retention: both ledgers and their origin and dispatch-entry links are removed only when neither tracked file has a receipt; either file holding any receipt, including confirmed passes, retains both files and links (the dispatching entry's Machinery admission).

Outcome matrix: the single receipt outcome matrix lives in Task 2 of the certifying plan `docs/history/plans/2026-10-20-certification-seal-landing-survival.md` (after archive, `docs/history/plans/completed/` under the same basename) and is the only source for receipt branch behavior.
