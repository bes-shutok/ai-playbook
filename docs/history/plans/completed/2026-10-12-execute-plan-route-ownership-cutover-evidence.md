# Plan: Execute-plan route-ownership cutover evidence

Backlog origin: docs/history/backlog/2026-10-12-cutover-survey-route-ownership.md
Driving force: code-quality + efficiency
Plan review record: the staging series docs/history/reviews/2026-10-12-plan-review-execute-plan-route-ownership-cutover-evidence-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h

## Terms

- Affected consumer: a session, launcher, automation, or runtime record whose route-ownership evidence, per the ownership rule this plan lands, shows its owning session or launcher can invoke the route being removed; a known-existing record whose ownership cannot be established because its source is uninspectable stays in the set under the retain fail-safe per the landed rule.
- Route ownership: the evidence relationship in the definition above; record existence, repository co-location, or a shared configured root alone never establishes it.
- Dated operator disposition: an operator-provided classification of a specific record (for example stale, route-independent, invalid, or out-of-scope, or an equivalent operator classification), recorded with its operator-utterance attribution, where the recorded utterance itself identifies the record and route (or was given in the cutover's session in direct response to the survey question about that record), the route and cutover it was given for, the record identity, and the recording session and date.
- No-launch hold: the amended section's rule that a verified live or resumable affected run's route or recovery is retained until terminal or completed disposition (the runtime-contract.md "Hold and cutover evidence" sentences beginning "If a relevant source is unavailable...", "If evidence verifies a live/resumable affected run...", and "If terminal/completed evidence is absent, retain...").

## Why

The adapter-removal cutover repeatedly treated stale records from unrelated runtimes and projects as unresolved affected consumers and reopened the survey after the operator had already disposed of them, because the removal-safety text never defined when a record owns a route. Defining ownership evidence and carrying dispositions forward keeps the existing per-surface hold while ending the reopen loop.

## Gist & Examples

TLDR: execute-plan's cutover checks classify consumer records by route-ownership evidence instead of record existence, ending survey reopen loops on operator-dispositioned records, for code-quality and efficiency.

Before: a route-removal survey reads `runtime_state.json` from an unrelated project's runtime and treats it as an unresolved live consumer; execution re-verifies the same record at every check and reopens the survey question even after the operator states the record is stale, unused, and invalid.

After: a record that fails to evidence route ownership is outside the affected-consumer set for that cutover, and one carrying ownership evidence is classified out by the operator's attributed dated disposition; later checks carry dispositions forward, a known-existing uninspectable-source record stays held under the retain fail-safe, and a record re-enters verification when fresh dated ownership evidence valid under the evidence standard appears from any party (including a re-fired dispositioned record's own verified launch), when the operator supersedes the disposition, or when a new record's own evidence appears.

## Outcome

Route removals verify only records with evidenced route ownership and hold uninspectable-source records under the retain fail-safe absent a covering operator disposition, while every fail-safe of the existing section keeps its trigger.

- Operator dispositions (stale, route-independent, invalid, out-of-scope, or an equivalent operator classification) survive the whole cutover that recorded them, absent fresh dated ownership evidence valid under the evidence standard or an operator supersession, without being reopened as unresolved consumers.
- The warning-only survey posture and the no-launch hold (per Terms) are unchanged, including the unavailable-source retain trigger.

Gate delta: no new refusal class, gate, fence, protocol layer, or schema field; no refusal surface is added. The affected-consumer checked set narrows (existence and co-location no longer qualify; every surfaced record now gets one ownership classification or, for uninspectable sources, the retain hold, and later checks consult recorded dispositions before classifying - new per-check consultation work, priced by deleting the ladder paraphrase this draft first proposed, leaving a pure pointer); the retain and stale-exclusion sentences keep their bytes and their triggers; nothing removed.

## Assumptions

- assume the completed adapter-removal plan and its Task 1 evidence log remain the cutover procedure of record; basis: docs/history/plans/completed/2026-10-11-execute-plan-sequential-only-adapter-removal.md Tasks 1-3 and the origin row's Expected section.
- assume the amendment is text-only with no runtime script change; basis: the origin row names execution policy, and the cutover registry entry is a warning-only protocol no script consumes.
- assume operator dispositions arrive in-session (operator chat or run log) during a run and are recorded by the executing session in the durable implement log; basis: the witnessed friction was resolved by operator chat statements, and the completed plan homes survey evidence in the Task 1 implement log.
- assume the origin row's own driving-force wording ("correctness + operator time") maps to this plan's closed-taxonomy tags code-quality + efficiency; basis: the plans skill taxonomy has no correctness tag, and the row's Problem is a classification correctness defect costing operator time.

Decision points requiring a grill: none remain.

## Standing constraints

- Preserve the existing removal-safety semantics: the no-launch hold (per Terms), the unavailable-source retain trigger, the stale-record exclusion sentence, and the warning-only survey posture stay byte-unchanged.
- The completed adapter-removal plan stays closed; this plan never rewrites its bytes and never claims its local landing verified external route activation.
- No new registry entry, validator, ledger, approval gate, or cross-repository inventory.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every consumer-scope statement in the amended section names its evidence class (ownership, disposition, or hold), states the ownership-before-disposition precedence, and contradicts neither the completed plan's Task 2-3 wording nor the origin row's rejected alternatives.
- simplicity: the amendment touches one existing section, reduces the ladder change to a pure pointer, and introduces no enumerated inventory or new state surface.

**Done when:**
- The "Hold and cutover evidence" section defines route-ownership evidence with its evidence standard, the disposition carry-forward with its attribution and binding fields, the ownership-before-disposition precedence, and the unavailable-source fail-safe boundary; the Live-session discovery ladder carries the pure pointer.
- The pins suite, hygiene scan, em-dash scan, skill-text budget advisory output (zero breach lines), and machinery inventory baseline all pass on the branch.
- These gates are structural only: the amendment's semantics (ownership exclusions, carry-forward boundaries, byte-preservation, precedence) are discriminated by the Review Scope checklist at review time; no automated check is added per the Gate delta.

**Ship when:**
- The next witnessed route-removal cutover runs its consumer checks without reopening an attributed operator disposition. Evidence owner: the parent session of that cutover run; closure evidence: the cutover's implement log entry recording that each dispositioned record stayed closed (any reopen event routes back to this plan's review record); review date: 2026-10-18 (the machinery registry cutover entry's review date, recorded here as a literal so the anchor survives that entry's pre-registered removal).

## Review Scope

**Explicit must-fix:** the folded r1 findings below; **Production code:**
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

**Documentation:** none (both files are operative skill text; the .md suffix does not make them documentation). Findings on paths outside this list are in scope when causally related to this plan (a floor, not a ceiling).

Focus: (1) the ownership definition excludes exactly what the origin row excludes and no more, states that the parenthetical evidence components are illustrative rather than independent prerequisites, and carries the evidence standard (read artifacts, cutover-window freshness, operator confirmation on conflicting signals); (2) the carry-forward rule cannot silence a record re-evidenced within the same cutover or a new record with genuine ownership evidence, and every landed disposition entry carries its attribution and binding fields; (3) the ownership-before-disposition precedence is stated, subject to the unavailable-source fail-safe boundary, and the byte-preservation checkbox names the stale-exclusion and retain sentences explicitly; (4) the existing hold, recovery, unavailable-source, stale-exclusion, and warning-only sentences named by Task 1 are byte-unchanged.

## Validation Commands

- `bash scripts/check_maintenance_pins.sh` (exit 0)
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` (exit 0)
- `bash scripts/check-no-em-dash.sh touched` (exit 0), or `file` mode over the two changed paths
- `python3 scripts/skill_text_budget.py --check` (exit 0; the gate is warning-only and exits 0 even on breach, so the evidence is the recorded advisory output with zero printed breach lines)
- `python3 scripts/machinery_inventory.py --check` (no new failure beyond the recorded standing baseline)

### Task 1: define route-ownership evidence and disposition carry-forward in the cutover checks

Context surface: the plan's Terms and Standing constraints.

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] Add the ownership rule to "Hold and cutover evidence": a session, launcher, automation, or runtime record is an affected consumer of the removed route only when dated evidence shows its owning session or launcher can invoke that route; record existence, repository co-location, or a shared configured root alone never qualifies [class: IMPLEMENTATION_REQUIRED]
- [x] Add the evidence-shape clauses: the components (record route identity, owning runtime or project identity, launcher or automation reachability) are illustrative, not prerequisites, and directly verified invocation of the removed route is by itself sufficient [class: IMPLEMENTATION_REQUIRED]
- [x] Add the evidence standard: each component cites a read artifact captured or re-validated within the cutover window (window = cutover start to the check being performed) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the conflicting-signals arm: signals conflict when any in-window read artifact indicates invocability and anything points otherwise; exclusion then requires operator confirmation, forced by any invocability artifact regardless of weighing, recorded as a dated disposition with the entry fields per Terms [class: IMPLEMENTATION_REQUIRED]
- [x] Add the uninspectable-source boundary: a read that fails, is partial, or yields no citable artifact counts as uninspectable, including a complete read silent on ownership and an ownership component with no attempted in-window read; only a complete read artifact affirmatively identifying the owner as unable to invoke supports default exclusion [class: IMPLEMENTATION_REQUIRED]
- [x] Add the hold: a known-existing uninspectable-source record stays in the affected-consumer set under the existing retain rule unless an operator disposition covers it; the reclassification does not alter that retain trigger [class: IMPLEMENTATION_REQUIRED]
- [x] Add the precedence rule: ownership is the membership precondition; the preserved stale-record sentence governs records carrying ownership evidence; a record without ownership evidence, not covered by the boundary, is outside the set and needs no disposition [class: IMPLEMENTATION_REQUIRED]
- [x] Add the carry-forward rule: an attributed dated operator disposition (entry fields per Terms) is recorded once in the cutover's durable implement log, applies for the rest of that cutover only, and binds to the route and record [class: IMPLEMENTATION_REQUIRED]
- [x] Add the application arm: later checks apply the disposition after re-running the lift scan over the record's sources within the window (re-validation per the standard) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the lift arm: it lifts when fresh dated ownership evidence valid under the standard exists regardless of surfacing party (own verified launch or newly active launcher, newly readable source artifact, operator-provided evidence) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the re-entry arms: operator supersession re-enters the record and re-applies the hold; a different record with its own evidence always re-enters; a later cutover re-runs the ownership check regardless of prior-log dispositions [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the existing hold, recovery, unavailable-source, stale-record exclusion, and warning-only sentences byte-unchanged; the amendment only reclassifies affected-consumer membership and never rewrites preserved triggers [class: IMPLEMENTATION_REQUIRED]
- [x] Add one pointer sentence to the Live-session discovery ladder: during a route removal, consumer classification (including records other than this run's own worker-session records) follows the "Hold and cutover evidence" section of agents/skills/execute-plan/runtime-contract.md; the pointer does not relax the ladder's re-observe-before-edit rule for this run's own workers [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands and record all exits plus the budget advisory output in the run log [class: REPOSITORY_TEST]
- [x] Commit: `skills: classify cutover consumers by route ownership` [class: IMPLEMENTATION_REQUIRED]
