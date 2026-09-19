# Backlog: maintenance-skill documentation-consistency residuals from the r5 review

Status: open
Origin: 2026-09-16-maintenance-scheduler-liveness r5 review (29 staged findings, zero blocking; all Lows below are documentation-consistency/hygiene on heavily amended spans)

Each entry is independently foldable; anchors are file:approx-line at head c6e2bcdd.

## Functional-adjacent (do first)

1. SKILL.md:151,:116 - the touch-session rearm_note clear on an armed-again listing (mandated unconditionally by the r4 Step 0 check) is missing from the canonical clearer list and the touch-session writer class; add both.
2. prompt-templates.md:90 - terminal-dark wording cites a "touch session's read-back of the memory index"; no touch surface reads the memory index. Reword to the operative mechanism (touch sessions classify darkness and re-arm; the next turn's Step 1 read-back surfaces the note).
3. zcode.md:45-48 - verification recipe omits the completed-record enabled-re-enable reshape shape (recurring false, enabled true); add a third verdict line.
4. prompt-templates.md:58 - the armed-child guard matches only plan-execution payloads; armed clocked authoring payloads are invisible (currently policy-unreachable; note for a future policy change).
5. zcode.md:36 - "or one naming no record the listing shows" reads listing-first inside the zero-listing primary path; drop "the listing shows".
6. plan:42 - witness row 3's "decision_reason records the release" is not an explicit landed record duty; add the duty or re-scope the probe.

## Enumeration/ledger precision

7. SKILL.md:113-114 - child and watchdog writer-class bullets omit their sanctioned parent_automation_id writes; also SKILL.md:151 rearm_note definition narrower than usage (dispatch-direction refusals).
8. SKILL.md:112,:151 - "hand-off" term used only in SKILL.md; rename after its ladder leg or define at first use.
9. SKILL.md:118 + plan:96 - carry-forward tail misdescribes pending_dispatch ownership ("written by non-Step-6 actors" though turn-owned); plan:96 also missing the hand-off refusal write mode.
10. SKILL.md:14 - configuration completeness claim omits tmp_dir.
11. SKILL.md:174-185 - no dated Revisions entry for the r3 fix round of this plan (2026-09-15 r3 entry belongs to the previous plan).
12. prompt-templates.md:3-19 - deviation ledger missing dated entries for the r4 paragraph amendments (armed-child guard, chain-nothing parenthetical, truthful dark-path wording); header counts the closed punctuation entry; the tail-fix entry's "ends with the stranding note" claim is superseded by the compaction final line.
13. SKILL.md:79 - Step 5 floor rule carries an unanchored "the same day" provenance (ledger already records it).
14. zcode.md:36,:40; prompt-templates.md:13 - provenance pointers "(r4 item N)" cite gitignored review logs; "plan Task 2" names no plan.
15. Three backlog items (darkness-race, step0-wording, preservation-pins) cite "r1 review" findings that resolve nowhere in-repo; restate the finding text inline or point at the archived r1 summary.

## Recognition/semantics wording

16. SKILL.md:32 vs :41 vs :56 - recognition rule restated in three shapes with no in-file canonical definition; single-source it.
17. zcode.md:26 - hygiene bullet's "governs the re-arm decision of the turn's Step 0" conflicts with the listing-first Step 0 trigger; extend the scope of backlog 2026-09-17-step0-rearm-trigger-state-first-wording.md to this surface.

## Pins/plan hygiene

18. check_maintenance_pins.sh:86 - schema block regex bounded at start only; bound the end at the next section heading.
19. check_maintenance_pins.sh:2 - stale header comment ("review r1/r2 fix rounds").
20. plan:215,:217,:235,:278,:96 - five plan checkbox/invariant quotes stale vs landed r3/r4 fixes (parent_absent_since clearer list, idle join marker, idle occupancy OR-clause, Task 4 sentence, writer-mode list). Sync or annotate as historical when the plan is next touched; it archives to completed/ as-is.
