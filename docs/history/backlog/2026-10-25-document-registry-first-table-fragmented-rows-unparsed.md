# Backlog: blank lines and a concatenated row fragment the document registry's first table, so the validator parses 8 of ~850 rows

- **Filed:** 2026-10-25, learn Step 1.9 over the 2026-10-24 22:00 exec takeover session (registry rows inserted for the prompt-log-stale-check landing)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** session-witnessed data drift in a machine-parsed table (writer appends outside the parsed region)
- **Class:** fix-class
- **Driving force:** correctness (the registry validator's coverage check runs over a near-empty table, so its 530+ "unregistered completed-history file" warnings are noise that hides any real gap, and every closeout that appends a row at end-of-file adds to the unparsed tail)
- **Skill/step:** `docs/maintenance/document-registry.md` (the table body: blank separator lines at the table's head region since `6b094a247`, 2026-10-22, and one line carrying two rows joined by `||` from the landing `d72ca0084`, 2026-10-24); `scripts/doc_registry_validator.py` `parse_registry` (by design parses the first table only and, since `c861ee3fc`, names present-but-unparsed rows beside the refusal); the plans skill's completion-transition registry-row duty (the writers that append rows)
- **Cluster:** docs/history/backlog/2026-10-25-landing-staged-set-foreign-dirt.md (same registry file as the surface; a different mechanism, the squash landing committing a peer's staged registry edit)
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog filenames and text for `document-registry`, `doc_registry_validator`, `first table`, `unparsed`; nearest is the Cluster sibling above (landing staged-set, not table shape) and the rejected rows under `docs/history/backlog/rejected/` about registry backfill and facts paths (different defects). No open row owns the fragmented-table shape.

## Problem

`parse_registry` stops at the first non-table line after the header, and the file now has blank lines inside the table's head region plus one physical line holding two rows (`... retargeted to the completed path || prune-audit-incommit-receipt-witness-arm | ...`). `python3 scripts/doc_registry_validator.py validate` reports `0 hard finding(s), 537 warn(s), 8 registry row(s)` on a file with 847 table lines: the coverage check sees almost nothing, so its warnings are uninformative, and sessions appending closeout rows at end-of-file (the common shape of recent landings) add rows the validator never reads. The 2026-10-24 22:00 session worked around it by inserting its two rows directly under the header separator, which is a per-session convention nobody else follows.

## Expected

One contiguous table: the validator parses every row (`N registry row(s)` equals the row count), the concatenated line is two rows, and the coverage warnings fall to the real gaps. New rows land inside the parsed table whichever position the writer picks.

## Suggested fix

Data repair first, no machinery: delete the blank lines inside the table region, split the `||` line at the join into two rows, and re-run `validate` to confirm the parsed-row count equals the table-line count and the warning count drops to the genuine unregistered files (triage those separately). Rejected: widening the parser to read every table or to skip blank lines (the first-table rule is deliberate and `c861ee3fc` chose a diagnostic over widening); a new blocking gate on table shape (the validator already names unparsed rows; one witnessed drift class, no incident beyond noise).
