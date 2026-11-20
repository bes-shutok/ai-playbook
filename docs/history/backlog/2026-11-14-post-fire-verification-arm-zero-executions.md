# Backlog: the post-fire verification arm has zero executions since landing while one window carried ten failed-outcome ledger rows

- **Filed:** 2026-11-14, 24h session-pattern harvest learn run (learn Step 1.9 project-issue capture; second harvest pass)
- **Status:** covered (docs/history/plans/2026-11-14-post-fire-verification-arm-zero-executions.md)
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** witnessed defect (a landed warning-only arm never exercised; runtime fire ledger cross-checked against corpus traces)
- **Skill/step:** `agents/skills/maintenance/survey-arms.md` Step 1 (Post-fire verification arm; the read adapter `scripts/maintenance_fire_outcomes.py`)
- **Driving force:** automation
- **Cluster:** docs/history/backlog/2026-11-06-fire-outcomes-pin-and-guard-accuracy.md (same script family: that row owns the adapter's pin/guard accuracy residuals, this row owns the arm's trigger wiring and zero-execution evidence)

## Observed versus expected

**Observed** (measured 2026-11-14 ~02:10 WET): the post-fire verification arm (landed 2026-11-06, warning-only, machinery review 2026-12-05) shows zero corpus traces of any execution: the persistent memory index holds no keyed `fire-outcome-correction|` entries, and the scheduler state file's notes array (42 entries) holds no outcome notes. The same 24h window carried ten terminal failed-outcome rows in the runtime fire ledger; eight are false failures over landed work (sessions with task status completed/interrupted and commits attributed to them by digest in the rolling logs; failure marks lagged scheduled fires by 12 seconds to 2.5 hours, five rewritten inside one 18-second span, attempts 0 and error empty throughout - a reconciliation-sweep signature, not per-run failure detection). The 11:00 survey turn wrote notes for other survey arms the same minute, so the arm loads into surveys but its enumeration never runs.

**Expected:** a survey turn's execution of the arm leaves its designed traces (one outcome note per verified terminal run, one keyed correction per verified fire), and a window with eligible terminal runs but zero traces is visible as an arm-health signal, not silence. The arm's 2026-12-05 promotion review must be able to distinguish "wired and catching" from "never ran".

## Reproduction evidence (trimmed)

- Runtime fire ledger (read conventions in `agents/skills/maintenance/zcode-primitive-verification.md`): ten terminal failed rows in the window; eight linked task rows read completed/interrupted with landings attributed by commit digests in the rolling logs.
- Corpus traces: zero correction entries in the persistent memory index; the state file's notes array carries 42 entries, none keyed by the arm's note prefix; the machinery-inventory survey notes at 2026-11-13 11:06 show other arms writing the same minute.
- The arm text `agents/skills/maintenance/survey-arms.md` Step 1 orders the per-member read and writes but states no enumeration completeness duty (no census over armed one-shot records whose fire time passed).

## Environment context

- zcode runtime carrier ledger; the corpus-side surfaces are the persistent memory index and the scheduler state file, both outside this repository (referenced by role, never by path).

## Suspected root area

The arm text orders per-member actions but no duty to enumerate the member set each survey, so the arm silently no-ops; the promotion-window design (warning-only, true-catch promotion) cannot accrue evidence while unexercised, and the false-failed ledger rows it exists to correct keep standing uncorrected.

## Accept when

A survey turn's run of the arm leaves the designed note/correction traces for the window's terminal runs (the eight false failures get corrections superseding their armed lines' pending wording), the enumeration is a census duty bound to a named source surface, and the 2026-12-05 review can read an exercised-catch record. The removal arm (retire the unexercised arm at its review with a registry-removal row) is the priced alternative if the operator declines the wiring.
