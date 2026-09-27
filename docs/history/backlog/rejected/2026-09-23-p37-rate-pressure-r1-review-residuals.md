# Backlog: P37 rate-pressure plan r1 review residuals (accepted, non-blocking)

Driving force: the P37 rate-pressure execution's r1 correctness review landed one blocking finding (fixed in fcc97c54) and five Low residuals accepted under the backlog-deferral default; they are recorded so the deferral is durable and each has a trigger to revisit.

- **Step 6 carry-forward double-entry** (`agents/skills/maintenance/SKILL.md` ~159): the plan-prescribed extension names `rate_limited_events` twice in the carry list. Revisit next time the Step 6 carry-forward sentence is edited.
- **D1 threshold sentence retains a 24-hours phrase** (`agents/skills/maintenance/SKILL.md` ~85): boundary-exactness language, deliberately out of Task 5's trim scope. Revisit if a fourth define-once trim pass opens.
- **Serialized-cap pin matches any one of four sites** (`scripts/check_maintenance_pins.sh` ~966): partial removal from three of four timeout sites stays GREEN. Revisit if a per-site pin pattern is introduced.
- **Doubled panel bound covers ~2 serialized workers** (execute-plan SKILL.md timeout paragraphs): the plan-prescribed 40-minute value can trip on a healthy five-worker serialized panel; bounded escalation paths mitigate. Revisit with panel-size data.
- **`rate_limited_dedup_ledger` lacks a state-change changelog entry** (`agents/skills/maintenance/SKILL.md` changelog block): the plan freeze made the executor compliant; add the dated entry on the next maintenance SKILL.md touch.

- Status: rejected (2026-09-27; non-blocking wording/pin residuals, each with only a hypothetical revisit trigger)
- Origin: docs/plans/completed/2026-09-22-p37-rate-pressure-ingestion-and-quota-scheduling.md (post-landing archival) r1 review
