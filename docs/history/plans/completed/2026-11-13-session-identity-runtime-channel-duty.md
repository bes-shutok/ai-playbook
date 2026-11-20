# Plan: session-identity runtime-channel duty and claim provenance guard

Backlog origins (scope of record):
- docs/history/backlog/2026-11-12-session-identity-runtime-channel-duty.md

Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-session-identity-runtime-channel-duty[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 0.75h
Executed: yes (4a71bf347f443bcc97f8981ae0194616081493e4)
Authoring claim: 2026-11-12-session-identity-runtime-channel-duty.md (session sess_7b19dc51-0e25-403f-a413-65c4fce59330)

## Terms

- identity resolver: the two allowed sources of an authoring session's session id: the runtime-provided session identity, or the session channel script's runtime derivation (the form the skill-gate marker recipe already prescribes); the resolver requirement fires at the foreign-claim fire-time gate's entry, before any identity-keyed classification, takeover, or write.
- store-based inference: deriving a session id from any store the runtime does not own; the witnessed instances are task-index rows, rowid ordering, and title matching, and the ban covers automation listings, state files, and every other non-runtime-owned source; banned for identity resolution.
- provenance rule: a matching session line in a claim file proves the file claims that id, never that the writer of the check owned it.
- second witness: none exists, and the duty says so. For a deletion of a claim whose session line matches the checking session's id but which that session did not write in its own current run, the duty refuses the deletion out of band and preserves the claim, reporting the matched file; the sanctioned clearance paths are the stale-foreign-claim takeover (the claim's updated: stale past one cadence period) and the operator. The frozen entry's named witness surfaces (a live worktree, an authoring branch, a live listing entry) cannot bind identity: guards.md pins that listing records carry no session ids and the worktree and authoring-branch surfaces are slug-keyed, so no corroboration form exists and the gate refuses rather than self-approves. A claim the session wrote in its own current run keeps deleting at the duty's placement-owned boundaries: on the run manifest's triple-match (the claim's session, plan, and branch matching the manifest's session id, plan path, and run branch) at the manifest-bearing boundaries, and on the ownership re-read plus this run's create at the worktree-creation-failure stand-down, where no manifest exists.

## Why

A carrier-fired authoring session without its runtime session id in context resolved its identity by querying the task-index store for the newest author-mode row and took a parallel session's id (rowid ordering decided among three rows created seconds apart). The forged id propagated into the claim file, the entry freeze witness, the review-certification seal, and the run's memory records; then the id-owning session found a claim naming its own id that it never wrote and deleted it through the ownership-checked removal arm, because the identity check matched the forged line and self-approved. The failure ran unattended end to end; nothing in the duty text or the guards' matching carried the provenance input that would have stopped it.

## Gist & Examples

TLDR: pin the identity resolver to its two allowed sources with a loud refusal when neither resolves, and give the claim duty's identity checks the provenance rule with a matched-line deletion refusal (the frozen entry's witness surfaces cannot bind identity, so an out-of-band matched-line deletion refuses and preserves), while every sanctioned self-written-claim boundary keeps deleting exactly as today.

Before: a session missing its id invented one from store rows; the forged id authored a claim, froze an entry, certified a review, and armed an ownership deletion against the real owner.
After: the same session refuses the claim write loudly (no claim, no freeze, no seal, no memory records carry a forged id), and a matched-but-unowned line can no longer be deleted on the match alone: the out-of-band deletion refuses and the claim is preserved until the stale-foreign-claim takeover or the operator clears it.

## Outcome

Authoring attribution stays truthful under unattended operation, and the ownership guard's deletion path requires evidence of ownership, not merely a matching string.

- After execution, an authoring turn with neither allowed identity source refuses the claim write loudly: no claim, no freeze, no seal, no memory record carries a forged id.
- After execution, a claim line that merely matches the checking session's id no longer self-approves a deletion: the out-of-band deletion refuses and the claim is preserved until the stale-foreign-claim takeover or the operator clears it, and each of the duty's own sanctioned boundaries keeps deleting self-written claims exactly as today.
- Follow-up disposition: writer-code, harness, and store changes stay rejected (the runtime already provides the id; the frozen entry's Verdict line and the Machinery admission protocol rule out new machinery); the Ship-when observation is human-owned on the live loop and dispatches no carrier.

Gate delta: adds no gate, validator, lock, ledger, or automation primitive; adds two prose-only refusal classes by name (the loud resolver refusal firing at the foreign-claim gate's entry and the claim write; the matched-line deletion refusal that preserves a fresh matched-but-unwritten claim), duty text only. Machinery admission: single 2026-11-10 incident; expected catch every carrier-fired authoring run lacking its runtime id in context, plus every out-of-band matched-line deletion attempt; false-positive cost a loud refusal the session resolves by recovering its runtime id, and a refused out-of-band deletion whose claim is preserved until the stale-foreign-claim takeover clears it one cadence period later; review date 2027-01-12 aligned with the loop-liveness family rows. Removes nothing.

## Assumptions

- the runtime already provides the session id and the marker recipe's resolver resolves it today; basis: agents/hooks/skill-gate/README.md's marker write recipe.
- the 2026-11-10 event is the single incident; no validator is warranted; basis: the frozen entry's Verdict line (guard-bearing exclusion; the duty-text arm alone would be ad-hoc-able) and the repository guidelines' Machinery admission protocol.
- the witnessed deletion self-approval ran through the claim matching this plan amends; basis: the origin row's observed section.

Decision points requiring a grill: fail-loud versus a silent fallback identity: fail loud, basis the forged id propagated silently through four record classes (the silent fallback is the witnessed failure mode), affects Task 1; second-witness form: none exists, the gate refuses and preserves (basis the frozen entry's named surfaces cannot bind identity: guards.md pins that listing records carry no session ids and the worktree and authoring-branch surfaces are slug-keyed), affects Task 2; no new gate: duty text plus matching-rule clause only, basis single incident and the machinery admission protocol, affects both tasks.

## Standing constraints

- Skill-text anti-growth rules (repository guidelines): each amendment lands in its named home; the incident story stays in the origin row; operative text cites an incident in at most one line.
- The pins suite (`scripts/check_maintenance_pins.sh`) pins literals in the guarded maintenance modules this plan edits; run it after each task's edit.
- The byte-budget gate (`python3 scripts/skill_text_budget.py --check`) runs at authoring time over the touched operative files; the ceiling class blocks.
- No new top-level section in any edited module: each insertion extends the section the origin row names.
- Pay for growth (repository guidelines' skill-text anti-growth rules): both target files already sit on advisory budget rows (template-authoring.md on a ratchet breach line, 51,559 bytes over its 42,066 advisory cap; guards.md on a pilot-target row, 24,897 bytes over its 20,480 target), so each task's insertion pairs with an equivalent compression deletion in the same module, recorded in the task evidence; where no faithful compression exists, the residual ratchet delta is accepted and the gate's advisory breach line is the record.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the pinned resolver names both allowed sources, the loud refusal, and the store-inference ban; the provenance rule carries the degenerate second-witness resolution the Terms pin (no witness form exists; the out-of-band matched-line deletion refuses and preserves the claim, cleared by the stale-foreign-claim takeover or the operator); both verified by reading the amended text against the witnessed scenario.
- compatibility: pins suite, public hygiene scan, and the byte-budget ceiling all exit 0.
- maintainability: one-line incident citations only; no new top-level section; no second wording home.

**Done when:**
- pins, hygiene, and the byte-budget ceiling exit 0 over the changed files.
- the full readiness gate passes on the certified plan bytes.

**Ship when:** the next carrier-fired authoring session lacking a resolvable runtime id refuses the claim write loudly instead of writing a forged id (human-owned observation on the live loop).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 2)
- `agents/skills/maintenance/guards.md` (Task 2)
- `agents/skills/maintenance/CHANGELOG.md` with one line from Task 1 (Task 1)
- `agents/skills/maintenance/CHANGELOG.md` with one line from Task 2 (Task 2)

**Plan-related extension:** implementation and review may change files not listed above when causally related to a task (for example sibling references to the claim duty's resolver wording). Otherwise out of scope.

**Out of scope; reject unless plan-related:**
- any harness, store, or writer-code change; reason: the runtime already provides the id and the writer guards stay unchanged (the entry's rejected alternatives).
- new validators or machinery; reason: single incident, the Machinery admission protocol.

## Validation Commands

```bash
python3 scripts/plan_readiness.py docs/history/plans/2026-11-13-session-identity-runtime-channel-duty.md
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/skill_text_budget.py --check
rg -c "AUTHORING CLAIM" agents/skills/maintenance/template-authoring.md
```

Authoring preflight record (rule 29, 2026-11-13, placement root = the authoring worktree):
- pre-round structural gate: OUTCOME pass (advisory warnings recorded at authoring, if any).
- no-em-dash: `touched` and `added-lines` scans OUTCOME pass at authoring.
- public hygiene scan: OUTCOME pass; maintenance pins suite: OUTCOME pass; byte-budget ceiling: OUTCOME pass (0 blocking breaches; 3 advisory ratchet breach lines pre-existing, one of them on a touched module: template-authoring.md 51,559 bytes over its 42,066 advisory cap; guards.md sits separately among the pilot-target advisory rows at 24,897 bytes over its 20,480 target).
- rule 22 mechanical audit: bash -n over this block OK; no literal pinned-span contracts in this plan.
- execution-time commands (pytest suites): not applicable to this plan's skill-text scope; the pins and byte-budget gates are the executable battery.

Round-start state for r1: branch authoring/session-identity-runtime-channel-duty; base main.

### Task 1: pin the identity resolver in the AUTHORING CLAIM duty

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `AUTHORING CLAIM` in `agents/skills/maintenance/template-authoring.md`

- [x] `AUTHORING CLAIM` duty delivers `identity resolver pin`: given an authoring session about to write its claim file, expects the duty text to name the two allowed id sources (the runtime-provided session identity; the session channel script's runtime derivation, the marker recipe's form) and to require the claim's `session:` line id from one of them [class: IMPLEMENTATION_REQUIRED]
- [x] `AUTHORING CLAIM` duty keeps the resolver `firing point`: given the foreign-claim fire-time gate's identity-keyed classification consuming the session id before any write exists, expects the duty text to fire the resolver requirement at the gate's entry, before the classification and any takeover arm, and before the first identity-keyed write, the probe scratch included [class: IMPLEMENTATION_REQUIRED]
- [x] `AUTHORING CLAIM` duty keeps `fail-loud refusal`: given neither allowed source resolves in context, expects the duty text to refuse the claim write and the identity-keyed writes that follow it (the probe scratch, the freeze witness, the seal, the memory records), loudly, with no fallback value written [class: IMPLEMENTATION_REQUIRED]
- [x] `AUTHORING CLAIM` duty carries the `store-inference ban`: given any temptation to derive the id from a store, expects the duty text to ban deriving the id from any store the runtime does not own for identity resolution, naming the witnessed instances (task-index rows, rowid ordering, title matching) [class: IMPLEMENTATION_REQUIRED]
- [x] The five-line frontmatter shape and the noclobber create recipe read byte-unchanged after the edit (diff check recorded in task evidence) [class: REPOSITORY_TEST]
- [x] Pins + hygiene + byte-budget ceiling exit 0 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: pin the authoring claim identity resolver to its two allowed sources` [class: IMPLEMENTATION_REQUIRED]

### Task 2: provenance rule and second-witness deletion gate in the claim duty's identity checks

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/guards.md`
- `agents/skills/maintenance/CHANGELOG.md`

Primary class anchors:
- `AUTHORING CLAIM` in `agents/skills/maintenance/template-authoring.md`
- `G1a (authoring lane)` in `agents/skills/maintenance/guards.md`

- [x] The claim duty's identity checks deliver the `provenance rule` at every match site: given the re-read-before-mutate check and the ownership re-check's scope sentence, expects the amended text to state at each site that a match proves the file claims that id, never ownership [class: IMPLEMENTATION_REQUIRED]
- [x] The create gate's own-id arm keeps `foreign-class matched files`: given a fresh claim whose session line matches but which this session did not write in its own current run, expects the create decision to refuse or route it through the foreign arms, never refresh-and-continue on the match alone [class: IMPLEMENTATION_REQUIRED]
- [x] The claim duty's deletion boundaries keep the `matched-line deletion gate`: given an out-of-band deletion of a fresh claim whose session line matches but which this session did not write in its own current run, expects the duty text to refuse the deletion and preserve the claim, reporting the matched file, with the stale-foreign-claim takeover and the operator as the sanctioned clearance paths [class: IMPLEMENTATION_REQUIRED]
- [x] The claim duty keeps `legitimate-owner deletions` at manifest-bearing boundaries: given a claim this session wrote in its own current run, expects the duty text to keep deleting it on the manifest triple-match at the closeout-success boundary after the authoring-branch removal and at the post-provision stand-down arm whose setup leg creates the manifest, exactly as today [class: IMPLEMENTATION_REQUIRED]
- [x] The claim duty keeps the `creation-failure stand-down delete`: given the worktree-creation-failure stand-down where no run manifest exists, expects the duty text to keep deleting this session's own claim on the ownership re-read plus this run's create, exactly as today [class: IMPLEMENTATION_REQUIRED]
- [x] `G1a` discovery arm carries the origin's `one-line provenance note`: given the arm's target-keyed claim matching, expects the matching rule to state the provenance rule in one line without extending the arm's matching inputs [class: IMPLEMENTATION_REQUIRED]
- [x] The runtime-scope filter and the same-target collision rule read byte-unchanged after the edit (diff check recorded in task evidence) [class: REPOSITORY_TEST]
- [x] Pins + hygiene + byte-budget ceiling exit 0 after the edits [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: claim mutation carries provenance and a second-witness deletion gate` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Origin row docs/history/backlog/2026-11-12-session-identity-runtime-channel-duty.md deleted in this completion pass: the plan executed (Tasks 1-2 landed on the run branch, Phase 3 focused three-lens panel zero blocking, r5 digest re-bind ready=yes), the executed flip recorded tip 4a71bf347f443bcc97f8981ae0194616081493e4, and the two non-blocking residual findings carry the durable row docs/history/backlog/2026-11-19-matched-line-claim-clearance-reachability.md.
