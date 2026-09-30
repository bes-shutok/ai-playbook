# Plan: Backlog capture destination ownership

Backlog origins (scope of record): `docs/history/backlog/2026-10-01-backlog-destination-project-ownership.md`, `docs/history/backlog/2026-10-01-public-backlog-capture-hygiene.md`
Driving force: reliability (privacy integrity)
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-backlog-capture-destination-ownership-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Backlog capture and pre-authoring investigation resolve the finding's owning repository before choosing where to record, and a passing hygiene scan no longer doubles as a publication-suitability decision.

- A review follow-up about a foreign repository's code, tickets, or module paths is captured to that repository's backlog (or the capture stops and asks), never filed into this repository as an accessibility fallback.
- An open backlog item owned by another repository is skipped, with the reason recorded, by the investigate survey and the maintenance monitor, so a misrouted item can never be grouped, investigated, or dispatched from the wrong backlog.
- The capture hygiene check states plainly that a scan verdict is scan evidence only, and prescribes the identifier scrub (or the keep-in-owning-repo alternative) for the rare cross-repository lesson that is genuinely reusable.

Gate delta: one checked condition (owning-repository resolution) added ahead of the existing destination-1 resolution in Backlog capture, one checklist step (suitability review) added to the existing capture hygiene check, one skip class plus one early-end refusal added to investigate Stage 0 and Stage 1, two Integration Points skip enumerations folded (investigate's maintenance row, maintenance's investigate duty leg), and the skill's three end-of-skill framing lines (Boundary, run-order sentence, hard gate) scoped to the same skip exception. Fix-class origins price these additions: the sanctioned exit (resolve ownership, then ask on failure) is the origin bodies' own expected behavior; there is no false positive to remove because today's flow has no ownership check at all, so the witnessed misroute is the missing check, not an over-refusal; the remaining class-default alternatives are unavailable because accessibility-based fallback to a shared repository is exactly the witnessed defect, and no refusal surface is removed anywhere.

## Terms

- Owning repository: the repository whose subject code, documentation, ticket context, or module paths a finding is about; the home of its backlog record, wherever the capturing session happens to run.
- Foreign-origin item: an open backlog item whose owning repository is not the repository holding the item file; the witnessed misroute shape this plan fences.
- Capture hygiene check: the scan-public-hygiene pass run over a composed backlog draft before it counts as captured (receiving-review, Backlog capture).
- Stage 0 ownership skip: the investigate survey's skip class for foreign-origin items, recorded like the survey's other skip reasons.

## Assumptions

- learn Step 1.8 needs no edit: its classifier already bounds skills-repo capture to skills-corpus faults and puts consumer-project defects out of scope, so the ownership gate lands in the shape provider, not in each consumer. (Basis: learn SKILL.md Step 1.8 first paragraph, read this session.)
- No data migration task: the two witnessed misrouted items were already moved to the owning repository's backlog by the correction commit this cycle builds on. (Basis: git show d911b015, file deletions.)
- No scanner change of any kind: the medium origin's own scope constraint, coordinated with the standing hygiene-scan policy; the suitability review is capture-workflow wording only. (Basis: origin body, "Coordinate its scope with the existing hygiene-scan policy rather than broadening scan behavior implicitly".)
- done, doing-code-review, execute-plan, and doc-hierarchy consume Backlog capture by reference ("per receiving-review Backlog capture") and inherit the ownership gate without edits. (Basis: their deferral wording, read this session.)

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Backlog capture and investigation resolve the finding's owning repository before choosing a destination, and a hygiene-scan pass stops counting as publication approval; force: reliability (privacy integrity).

A session running in a service repository captures a review follow-up about that service. Today the capture flow can file it in this shared skills repository's backlog because that home is accessible and the item mentions reusable workflow concerns; the correction then requires manually moving company-specific records out of a public repository's history. After this plan, the ownership resolution sends the item to the owning repository's backlog, or stops and asks when ownership cannot be resolved. On the validation side, a scan pass over a draft that still names the service no longer reads as permission to publish: the scrub step names what to neutralize and when to keep the item in the owning repository instead. And on the investigation side, a foreign-origin item sitting in this backlog is a recorded skip, never a plan-creation target.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the ownership resolution precedes destination-1 resolution and fails closed (stop and ask; return-for-ask in non-interactive runs); a failed ownership resolution can never fall through to a later destination.
- Consistency: receiving-review (the shape provider), investigate (sweep, anchored search, emission), and the maintenance monitor enumerate the same ownership semantics; both Integration Points rows name the Stage 0 ownership skip.
- Simplicity: wording-only contract changes; no new scripts, no scanner surface change, no new required item fields.

**Done when:**
- Every Validation Commands grep is green on the changed skills, and the pins baseline, em-dash scan, hygiene scan, and investigate checker all exit 0.

**Ship when:**
- The next cross-project capture run in a consuming repository applies the ownership resolution (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/receiving-review/SKILL.md`
- `agents/skills/investigate/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

**Tests:**
- none; this plan's verification surface is the repository grep canaries and the four command gates in Validation Commands, not a test suite.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/learn/SKILL.md`; reason: Step 1.8's classifier already bounds its capture to skills-corpus faults (Assumptions).
- `scripts/scan-public-hygiene.sh` and the deny-patterns file; reason: the origins' explicit scope constraint, no scanner broadening.
- `agents/skills/doc-hierarchy/SKILL.md`, `agents/skills/done/SKILL.md`, `agents/skills/doing-code-review/SKILL.md`, `agents/skills/execute-plan/SKILL.md`; reason: they consume Backlog capture by reference and inherit the gate.
- `agents/skills/bootstrap-ai-playbook/SKILL.md`; reason: its recovery pass is per-repository and composes unchanged when run in the owning repository; its mirror Integration Points row stays as written.
- `docs/history/backlog/*` records; reason: no data migration (Assumptions).

## Validation Commands

```bash
[ "$(grep -c 'owning repositor' agents/skills/receiving-review/SKILL.md)" -ge 4 ] || { echo FAIL owning-repository wording; exit 1; }
grep -q 'The owning repository.s `{backlog_dir}` pre-plan file' agents/skills/receiving-review/SKILL.md || { echo FAIL destination-1 rehome; exit 1; }
grep -qF 'scan evidence only' agents/skills/receiving-review/SKILL.md || { echo FAIL scan-evidence bound; exit 1; }
grep -q 'owning repository before destination 1' agents/skills/receiving-review/SKILL.md || { echo FAIL ownership gate placement; exit 1; }
[ "$(grep -c 'foreign-origin' agents/skills/investigate/SKILL.md)" -ge 4 ] || { echo FAIL foreign-origin skip; exit 1; }
grep -qF 'Stage 0 ownership skip' agents/skills/investigate/SKILL.md || { echo FAIL investigate IP fold; exit 1; }
grep -qF 'Stage 0 ownership skip' agents/skills/maintenance/SKILL.md || { echo FAIL maintenance leg-e fold; exit 1; }
grep -qF 'no personal, machine-specific, or foreign-project data' agents/skills/investigate/SKILL.md || { echo FAIL stage-4 sanitization; exit 1; }
grep -q 'pass ends before Stage 2' agents/skills/investigate/SKILL.md || { echo FAIL foreign-input early end; exit 1; }
grep -q 'ownership skip ends the pass with no entry' agents/skills/investigate/SKILL.md || { echo FAIL run-order exception; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo FAIL pins baseline; exit 1; }
bash scripts/check-no-em-dash.sh file agents/skills/receiving-review/SKILL.md agents/skills/investigate/SKILL.md agents/skills/maintenance/SKILL.md || { echo FAIL em-dash; exit 1; }
bash scripts/scan-public-hygiene.sh --files agents/skills/receiving-review/SKILL.md || { echo FAIL hygiene receiving-review; exit 1; }
bash scripts/scan-public-hygiene.sh --files agents/skills/investigate/SKILL.md || { echo FAIL hygiene investigate; exit 1; }
bash scripts/scan-public-hygiene.sh --files agents/skills/maintenance/SKILL.md || { echo FAIL hygiene maintenance; exit 1; }
python3 scripts/check_investigate_entries.py || { echo FAIL investigate checker; exit 1; }
```

### Task 1: receiving-review resolves the destination from the owning repository

Files:
- `agents/skills/receiving-review/SKILL.md`

Evidence:
- `grep -c 'owning repositor' agents/skills/receiving-review/SKILL.md`; covers the ownership gate wording landed in all four sites
- `grep -q 'The owning repository.s \`{backlog_dir}\` pre-plan file' agents/skills/receiving-review/SKILL.md`; covers the destination-1 rehome
- `grep -q 'owning repository before destination 1' agents/skills/receiving-review/SKILL.md`; covers the gate's placement ahead of destination resolution

- [ ] Run → expect RED: `grep -c 'owning repositor' agents/skills/receiving-review/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [ ] Scope line (Backlog capture): replace the opening sentence `Scope: review findings in the current project.` with `Scope: review findings, recorded in the repository that owns the finding (ownership resolution below); this section's destinations apply to findings this repository owns, and a foreign-origin finding records in its owning repository, never here by fallback.` keeping the learn sentence that follows unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert one ownership-resolution paragraph between the partner-declined-fixes sentence and `Resolve destination 1 before consulting any later destination`: `Resolve the finding's owning repository before destination 1: the owning repository is the one whose subject code, documentation, ticket context, or module paths the finding is about, wherever the capturing session runs. Destination 1's {backlog_dir} resolves in the owning repository (its own .ai-playbook/facts.md), and the bootstrap recovery pass runs there too. This repository records the item directly only when the finding is genuinely about this repository's own repository-agnostic workflow and carries independent cross-project value, and then only after the capture hygiene check's suitability review below. Never record a foreign-origin finding in this repository as a fallback merely because the shared repository is accessible or because the item mentions reusable workflow concerns; describing a destination as shared, in a user ask, a prompt, or a capture flow, does not transfer a project-specific finding's ownership. When the owning repository or its backlog home cannot be resolved, stop and ask the user where to record, returning the ask to the orchestrator in a non-interactive run; a failed ownership resolution never falls through to a later destination or to an accessible shared repository.` (wrap in the section's prose style, keep the `{backlog_dir}` and `.ai-playbook/facts.md` code spans from the surrounding text) [class: IMPLEMENTATION_REQUIRED]
- [ ] Destination 1 entry: replace `1. \`{backlog_dir}\` pre-plan file (key from \`.ai-playbook/facts.md\`;` with `1. The owning repository's \`{backlog_dir}\` pre-plan file (key from that repository's \`.ai-playbook/facts.md\`;` keeping the rest of the entry unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Integration Points row `With bootstrap-ai-playbook skill`: extend the recovery clause to `the recovery rerun resolves or creates the backlog home when the keys are missing, in the owning repository when the ownership resolution selected a foreign home` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the three Evidence greps above; `grep -c 'owning repositor' agents/skills/receiving-review/SKILL.md` returns 4 or more [class: REPOSITORY_TEST]
- [ ] Commit: `skills: receiving-review resolves backlog destination from the owning repository` [class: IMPLEMENTATION_REQUIRED]

### Task 2: capture hygiene scan pass is evidence, not publication approval

Files:
- `agents/skills/receiving-review/SKILL.md`

Evidence:
- `grep -qF 'scan evidence only' agents/skills/receiving-review/SKILL.md`; covers the suitability step landed
- `bash scripts/check-no-em-dash.sh file agents/skills/receiving-review/SKILL.md`; covers the inserted text staying em-dash clean

- [ ] Run → expect RED: `grep -c 'scan evidence only' agents/skills/receiving-review/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [ ] Append step 5 to the capture hygiene check numbered list: `A passing verdict is scan evidence only: it proves the draft matches the scanner's deny patterns, not that the item belongs in this repository or is suitable to publish there. Before a foreign-origin item is recorded in a shared or public repository, apply the ownership resolution above and scrub the project-specific identifiers the scanner does not own: ticket prefixes, organization, service, and module names, internal document or RFC titles, and project-specific paths, each replaced with neutral phrasing (a ticket prefix becomes the project tracker, a service name the owning service, a module path the owning repository's module). When scrubbing would destroy the item's actionable context, record the item in its owning repository instead; this repository keeps only the sanitized, independently reusable process lesson. This suitability review is capture-workflow policy: it never widens or forks the scanner's deny patterns (step 2's rule).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence greps above [class: REPOSITORY_TEST]
- [ ] Commit: `skills: capture hygiene scan pass is evidence, not publication approval` [class: IMPLEMENTATION_REQUIRED]

### Task 3: investigate skips foreign-origin items; emissions carry no foreign-project data

Files:
- `agents/skills/investigate/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -c 'foreign-origin' agents/skills/investigate/SKILL.md`; covers the skip, the anchored-search rule, the early end, the framing-line exceptions, and the emission bound
- `grep -qF 'Stage 0 ownership skip' agents/skills/investigate/SKILL.md`; covers the Integration Points fold in investigate
- `grep -qF 'Stage 0 ownership skip' agents/skills/maintenance/SKILL.md`; covers the maintenance leg (e) fold
- `grep -qF 'no personal, machine-specific, or foreign-project data' agents/skills/investigate/SKILL.md`; covers the emission bound
- `bash scripts/check-no-em-dash.sh file agents/skills/investigate/SKILL.md agents/skills/maintenance/SKILL.md`; covers the inserted text staying em-dash clean

- [ ] Run → expect RED: `grep -c 'foreign-origin' agents/skills/investigate/SKILL.md` returns 0, and `grep -c 'Stage 0 ownership skip'` returns 0 on both target files [class: REPOSITORY_TEST]
- [ ] Stage 0 sweep bullet: replace `skipping origins that are not ungrouped (the monitor's skip rule: no intersection with an existing log entry's \`Origins:\` line, no plans-root plan file).` with `skipping origins that are not investigable here (the monitor's skip rule: no intersection with an existing log entry's \`Origins:\` line, no plans-root plan file, plus the Stage 0 ownership skip: a foreign-origin item, one whose subject code, documentation, ticket context, or module paths identify a different owning repository, is skipped with that reason recorded in the turn output and is never grouped, investigated, or dispatched from this backlog).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Stage 1: add one bullet after the open-backlog similarity-search bullet: `Apply the Stage 0 ownership skip to the anchored search as well: a foreign-origin sibling is never grouped into this investigation, and when the input item itself is foreign-origin, the pass ends before Stage 2 with the reason recorded in the turn output (no log entry; ownership is a boundary this skill never crosses).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Stage 4 write rules: replace `the entry carries repo-relative paths only and no personal or machine-specific data` with `the entry carries repo-relative paths only and no personal, machine-specific, or foreign-project data (no ticket prefixes, organization, service, or module names, and no internal document titles of a repository this one does not own)` [class: IMPLEMENTATION_REQUIRED]
- [ ] Boundary line: extend `and stops at the log entry` to `and stops at the log entry, or earlier on the Stage 1 ownership skip` keeping the plans Phase 1 clause that follows unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Run-order sentence: replace `Run the four stages in order; the skill ends when Stage 4's write is committed.` with `Run the four stages in order; the skill ends when Stage 4's write is committed, or earlier when Stage 1's ownership skip ends the pass with no entry.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Hard gate bullet: replace `the skill ends at the log entry;` with `the skill ends at the log entry, when one is emitted (the Stage 1 ownership skip ends a foreign-origin pass earlier with no entry);` keeping the prompt-payload clause that follows unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Integration Points row `With maintenance skill`: extend the monitor's skip enumeration `whose origins intersect an existing log entry's \`Origins:\` line or a plans-root plan file` to `whose origins intersect an existing log entry's \`Origins:\` line or a plans-root plan file, or are foreign-origin (the Stage 0 ownership skip)` [class: IMPLEMENTATION_REQUIRED]
- [ ] maintenance SKILL.md investigate duty leg (e): extend `skip any ungrouped open backlog item whose origins intersect an existing log entry's \`Origins:\` line or a plans-root plan file` to `skip any ungrouped open backlog item whose origins intersect an existing log entry's \`Origins:\` line or a plans-root plan file, or are foreign-origin per investigate's Stage 0 ownership skip` keeping the parenthetical about recording the skip reason unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence greps above [class: REPOSITORY_TEST]
- [ ] Commit: `skills: investigate skips foreign-origin backlog items; entries carry no foreign-project data` [class: IMPLEMENTATION_REQUIRED]

### Task 4: cross-skill consistency and regression gates

Files:
- none; verification-only task

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the receiving-review marker pin and every maintenance pin surviving the wording changes
- `bash scripts/check-no-em-dash.sh file` over the three changed skills; covers em-dash cleanliness
- `bash scripts/scan-public-hygiene.sh --files` per changed skill; covers the capture-hygiene discipline this plan prescribes
- `python3 scripts/check_investigate_entries.py`; covers the rolling-log checker staying green beside the edited skill

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
- [ ] Re-run `grep -c 'owning repositor' agents/skills/receiving-review/SKILL.md` and `grep -c 'foreign-origin' agents/skills/investigate/SKILL.md`; counts unchanged from Task 1 and Task 3 GREEN state [class: REPOSITORY_TEST]
