# Backlog: make corpus-level investigation resumable without stopping before emission

- **Filed:** 2026-10-15, corpus-level investigate session
- **Status:** covered (docs/history/plans/2026-10-15-investigate-corpus-pass-resumability.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** observed execution interruption
- **Class:** fix-class
- **Driving force:** reliability + operator time
- **Skill/step:** `agents/skills/investigate/SKILL.md`, Corpus-level invocation; Stages 0 and 4
- **Incident:** The first corpus survey identified 51 uncovered groups and stopped before issue archaeology, work-type routing, prompt-log emission, validation, or commit. The first follow-up created this row and a recovery-plan prompt, then stopped after checking a previously surveyed pin group. The second follow-up amended the incident and investigated one group, but again ended while the user's corpus request remained incomplete. A third follow-up again required the user to restate the same recovery request. On the fourth follow-up, the bounded-group workaround resumed successfully: the next uncovered high-priority origin was investigated, its plan prompt validated, and commit `8205fab1` recorded it. The corpus remains partial, so continuation is still required.
- **Catch frequency:** observed across four consecutive follow-ups; longer-term recurrence rate is unknown
- **False-positive cost:** a whole-corpus request can leave annotations or other preparation without the required ready-to-dispatch entries and same-turn commit, while requiring the operator to reissue the task
- **Review date:** 2026-11-15

## Problem

The corpus-level contract requires one investigated prompt entry per discovered group, but the pass was started as one large undivided task. After the 51-group census and cluster annotations, the session stopped before archaeology and Stage 4 writes. Later turns recorded the interruption, proposed a workaround, and investigated one group, but still yielded while the explicit corpus request remained incomplete. This shows that merely dividing work into bounded groups is insufficient unless continuation remains active and each turn takes the next group until the requested scope is complete or a real hard gate intervenes. The primary checkout was clean on the first follow-up, so the annotations had not persisted; progress accounting initially relied on conversational memory rather than a verified durable checkpoint.

## Expected

Every started investigation unit reaches a validated, committed prompt-log entry or a recorded skip disposition before the session yields. When a follow-up explicitly asks to resume, keep working through bounded groups in the same turn until the authorized scope is complete or a concrete limit requires yielding; do not treat filing a backlog row, planning the repair, or finishing only one convenient group as completion. Preserve a repo-local group roster and completed-unit receipts, then resume only remaining groups without redoing or silently dropping work. Each emitted prompt still follows the investigation skill's archaeology, evidence, routing, ordering, hygiene, and same-turn commit requirements.

## Suggested direction

Trace why the corpus-level invocation was treated as an all-at-once emission obligation despite the skill's one-entry artifact and same-turn commit contract. Prefer a bounded continuation form that records the surveyed roster, per-group verdict, and completed log-entry receipt in the rolling logs or a canonical tracked survey artifact, with a deterministic next-group rule and a final completeness check. Reuse the existing logs and current `Cluster:` graph where possible. If a durable cursor or new artifact is not necessary, define a session-level batching method that commits each investigated group independently while keeping Stage 0 idempotent. Ensure partial progress cannot be mistaken for corpus completion. Do not add a new gate, validator, ledger, or required ceremony without identifying the concrete incident it prevents, catch frequency, false-positive cost, and review date.

## Recovery observed

Resume from repository truth: count uncovered origins by checking the committed PLAN and EXEC prompt logs, inspect the next highest-priority origin and its current implementation, emit only a justified prompt (or skip disposition), run the entry and hygiene checks, commit, then repeat. This has produced durable entries across multiple turns, including commit `8205fab1` for receiving-review checkout preflight. Do not claim corpus completion from these partial commits; finish only after a fresh coverage scan shows every eligible open origin represented or explicitly dispositioned.

## Alternatives

- Leave corpus-level investigations as one unbounded session and rely on context capacity: rejected because this session stopped after census work with zero entries emitted (`agents/skills/investigate/SKILL.md`, Corpus-level invocation; this incident).
- Discard the survey edits and ask the operator to restart from scratch: rejected because the Stage 0 cluster roster is intended as reusable advisory input and a bounded resume can preserve completed work (`agents/skills/investigate/SKILL.md`, Stage 0).
- Weaken Stage 4's same-turn commit or entry validation to fit larger passes: rejected because these are explicit durability and structural checks, and no evidence shows they caused the stop (`agents/skills/investigate/SKILL.md`, Stage 4; `scripts/check_investigate_entries.py`).
- Add a mandatory cursor file, validator, or continuation gate immediately: rejected because the incident shows the need for bounded recovery but has not established that new machinery is the smallest fix; no witnessed recurring catch frequency exists beyond this occurrence (this incident; repository Machinery admission protocol in `AGENTS.md`).
