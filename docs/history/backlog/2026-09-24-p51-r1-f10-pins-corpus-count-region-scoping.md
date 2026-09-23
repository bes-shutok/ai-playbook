# Backlog: maintenance pins count gates are corpus-level (body/payload membership blind spot) with narrower claim semantics than enforcement

Status: open
Priority: low
Workflow: backlog
Date: 2026-09-24
Class: non-blocking review Low, conservative direction (documented assumption, not a defect fix)
Source: P51 plans/authoring surface hygiene code review r1 F10
Driving force: code-quality

## Observed

The P51-origin count gates in `scripts/check_maintenance_pins.sh` (the authoring/execution checkpoint-duty pins, the payload re-arm set count, and the FINAL STEP compaction count) assert corpus-level totals over `prompt-templates.md` and cannot tell where an occurrence sits: a span deleted from the payload paragraph while a stray duplicate appears anywhere else in the file (a body paragraph, the deviation ledger's prose, a future paragraph) keeps the corpus count satisfied, so a body/payload membership regression can pass. Independently, the survey gate bullet's claim sentence describes the claim surface narrowly ("a top-level plan's origin list or validation-gate literal naming the item is the claim") while the checker enforces any hyphen-bounded mention anywhere in a top-level plan, so the documented claim semantics are narrower than the mechanical enforcement (conservative direction: over-enforcement only annotates, it never misses a claim).

## Expected

The gap is either closed or recorded as an accepted, documented assumption. Candidate directions, any one suffices:

- Region-scoped counting in the pins suite python blocks: assert each counted span's occurrences per region (the payload paragraph line, the fenced bodies, outside the fences) instead of file-wide totals, mirroring the existing body-scoped precedents in the same script.
- A comment at the count-gate block recording the corpus-level assumption and the blind spot, so a future editor reconciles the pin knowing the limitation.
- The survey gate bullet's claim sentence widened (or annotated) to match the checker's any-mention enforcement, removing the documentation-vs-enforcement gap.

## Direction

Conservative by design: the enforcement direction that matters (a missed claim is the witnessed failure) is unaffected, and the checker's over-broad match only annotates. Prefer the region-scoped counting variant when touched, since the suite already carries the region-scoping idiom; reconcile pins and text in the same edit and record the superseding origin per the pins suite's freeze-literal convention.

## Evidence

- Code review r1 F10 (docs/reviews/2026-09-24-p51-plans-authoring-surface-hygiene-code-review-r1.md), lens: risk; triaged valid non-blocking, routed to backlog per the r1 triage.
- `scripts/check_maintenance_pins.sh` P51 origin 2 block: `grep -oF ... | wc -l` count gates over the whole file (observed 2026-09-24).
- Maintenance SKILL.md survey gate bullet's claim parenthetical vs `scripts/check_backlog_claimed.py` hyphen-bounded segment matching (observed 2026-09-24).
