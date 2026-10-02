# Plan: The interrupted-manifest census drains up to five per turn instead of blocking

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-03-interrupted-manifest-pile-drain.md`

## Gist & Examples

TLDR: the maintenance survey's interrupted-manifest arm stops refusing the pile it counts: every survey turn that finds undisposed dead roots runs the drain-up-to-five bound (oldest first in the census output's printed order, witness-first, never bulked), the cross-turn state lives in a census state file beside the manifests the arm already reads, escalation fires only when the pile grows across turns (current undisposed count above the previous record's post-drain count), and the closeout census receipt pair is the regression guard; reliability driving force, because the witnessed pile made the arm's own ceiling turn a serviceable queue into a recurring `turn_error`.

Authoring re-derivation (recorded per the entry; changes the plan's shape):

- The entry's arm 1 (the drain itself) is witnessed done. Authoring census, 2026-10-03, primary checkout: `list-interrupted-manifests` prints 21 manifests, every line `root=dead dispositioned=yes`, zero `dispositioned=no`, zero `root=live`; each manifest carries its own `dispositioned` record (date, reason) per the done skill's Manifest disposition paragraph, and the known cross-repo witness `20260929T023532Z-3fb1c11bb98b` carries `dispositioned.date 2026-10-01, reason work-verified-landed`.
- The entry's twenty-two count was the `complete=false` census and all twenty-two manifests remain on disk; the census prints twenty-one because `20261001T103119Z-5e8b8c50d695` is suppressed by the lib's adoption keep-filter (it is the adopted-from twin of the completed `run-manifest-20261001T103248Z-707c81c1be2b`). The drain ran operator-directed through the sanctioned paragraph; nothing in this plan re-runs it.
- What stays open is the machinery gap the entry names: the arm's census still blocks above ten undisposed dead roots and escalates through `turn_error:` instead of draining, so the next quota-paused pile reproduces the witnessed failure (the origin's own 44-manifest witness), and no gate proves a drain turn actually drained.

## Terms

- **Undisposed dead root:** a manifest line from `list-interrupted-manifests` with `root=dead dispositioned=no`; the only count the census bounds and the drain services. A dispositioned line proposes nothing and never counts.
- **The drain-up-to-five bound:** every survey turn whose census finds one or more undisposed dead roots executes dispositions for the first five undisposed lines in the census output's printed order (the tool's run-id-timestamp order, oldest first to the second, which already resolves same-day ties), each through the done skill's Manifest disposition paragraph as the procedure of record (the deliverables witness is the tool's own refusal behavior, never forced, never bulked). A witness-refused head is reported, consumes none of the five slots (the bound counts completed dispositions), and stays undisposed for the next turn; persistently refused heads are named through the `turn_error:` channel for operator direction.
- **Census state file:** `docs/tmp/done-session/interrupted-census.json`, beside the manifests the arm already reads: every survey turn that runs the census overwrites it with one record `{date, pre_drain_undisposed, post_drain_undisposed, dispositioned_run_ids}`; a turn whose heads all fail the witness or that found zero undisposed writes the record with an empty id list. This is the only cross-turn channel the escalation reads, so gap turns and refused-head turns leave a well-defined predecessor.
- **Growth escalation:** the `turn_error:` alarm reserved for a pile that still grows across turns: the turn compares its pre-drain undisposed count against the previous census record's `post_drain_undisposed` and, when the current count is greater, executes the drain-up-to-five bound anyway and escalates naming both counts (the alarm never suppresses the drain; the drain bounds the bleed every turn, which restores the entry's forcing property that more than zero undisposed manifests forces drain work in the turn that finds them). A first turn with no previous record proceeds with the bound and no alarm.
- **Closeout census receipt:** the census state file's record is the receipt; because every census-running turn rewrites it, the pre-drain and post-drain pair plus the dispositioned ids are the durable trace of the drain turn, and a post-drain count above zero records the residue as the next turn's input, never as a failure.

## Coordination (binding, not re-litigating)

- The done skill's Manifest disposition paragraph (agents/skills/done/SKILL.md, "Manifest disposition (dead-boundary close)") stays the procedure of record and is not edited; its cross-reference to the arm "per its bounded-census gate" survives because the re-keyed text retains the bounded-census name.
- The completed interrupted-manifest disposition drain plan owns the `disposition-manifest` machinery; this plan edits no lib code (scripts/done_sweep_gates_lib.py is consumed, not edited).
- The landed maintenance survey arm text (agents/skills/maintenance/SKILL.md, the interrupted-manifest classification arm) is the base this plan re-keys: both the bounded-census passage and the same-turn execution clause it bounds are re-keyed together, and the stale-deployment probe sentence and the live-root proposal-only rule are untouched.
- The execution lane closure (operator directive, 2026-10-02) means authoring only; the drain this plan enables runs through the survey arm's own sanctioned bookkeeping lane.

## Review Scope

Every task's Files path, inventoried:

- agents/skills/maintenance/SKILL.md
- scripts/check_maintenance_pins.sh
- docs/history/plans/2026-10-03-interrupted-manifest-pile-drain.md

Gates re-checked but not edited: scripts/done_sweep_gates_lib.py (its `list-interrupted-manifests` output is the census input), agents/skills/done/SKILL.md (the disposition paragraph stays the procedure of record, not edited). Harness touched: the pins suite's row set grows (Task 3); no other test harness changes. Reviewers verify the census counts only undisposed dead roots, the bound and the growth alarm are decidable from the census state file alone, the execute-all clause is re-keyed together with the census passage, and no per-manifest step is weakened.

## Tasks

### Task 1: the arm drains up to five undisposed dead roots per turn, with a durable census state file

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- grep probes below; `bash scripts/check-no-em-dash.sh added-lines --base HEAD` and the hygiene scan stay clean

- [x] RED: `grep -c "drain-up-to-five" agents/skills/maintenance/SKILL.md` (expect 0 today), `grep -c "interrupted-census.json" agents/skills/maintenance/SKILL.md` (expect 0 today), and `grep -c "grows across turns" agents/skills/maintenance/SKILL.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Re-key the arm's bounded-census passage AND its same-turn execution clause together: the census counts undisposed dead roots only (`root=dead dispositioned=no`); the drain-up-to-five bound replaces both the execute-for-each-listed wording and the exceeds-ten ceiling, so the same turn executes dispositions for the first five undisposed lines in the census output's printed order (the run-id-timestamp order, oldest first to the second), each through the done skill's Manifest disposition paragraph (witness-first is the tool's own refusal behavior; a refused head is reported, consumes none of the five slots, stays undisposed, and persistently refused heads are named through the `turn_error:` channel for operator direction); the stale-deployment probe sentence and the live-root proposal-only rule keep their places, and the retained phrase "bounded census" keeps the done skill's cross-reference accurate [class: IMPLEMENTATION_REQUIRED]
- [x] In the same arm, add the census state file and the growth escalation, so the arm's own text names the alarm's trigger as a pile that grows across turns: every survey turn that runs the census overwrites `docs/tmp/done-session/interrupted-census.json` with `{date, pre_drain_undisposed, post_drain_undisposed, dispositioned_run_ids}`; the growth alarm compares the turn's pre-drain count against the previous record's `post_drain_undisposed` and fires `turn_error:` naming both counts only when the current count is greater, while the drain-up-to-five bound runs regardless (the alarm never suppresses the drain); a first turn with no previous record proceeds with the bound and no alarm, and gap turns (zero undisposed, or all heads refused) still write their record so every turn leaves a well-defined predecessor [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: each of "drain-up-to-five", "interrupted-census.json", and "grows across turns" appears exactly once in the file's operative text before the `## Revisions` ledger (the count commands scope to `sed -n '1,/## Revisions/p'` output, the pins doctrine's own split, so a ledger entry quoting a literal verbatim never breaks a gate) [class: REPOSITORY_TEST]
- [x] Commit: `skills: interrupted-manifest arm drains five per turn on a durable census state file` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the closeout census record is the regression guard

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- grep probes below

- [x] RED: `grep -c "closeout census" agents/skills/maintenance/SKILL.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Append the guard to the arm, naming the receipt: the closeout census receipt is the census state file's record every census-running turn writes; a turn that executed dispositions leaves the post-drain count beside the dispositioned run ids as the durable trace, a post-drain count above zero records the residue as the next turn's input and is never reported as a turn failure, and a post-drain zero after a prior non-zero census is the drain's witnessed completion [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: "closeout census" appears exactly once in the file's operative text before the `## Revisions` ledger [class: REPOSITORY_TEST]
- [x] Commit: `skills: the closeout census record is the drain's regression guard` [class: IMPLEMENTATION_REQUIRED]

### Task 3: maintenance pins over the re-keyed arm text

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh` GREEN with the new rows present

- [x] RED: the new pin needles are absent (`grep -c "drain-up-to-five" scripts/check_maintenance_pins.sh` expect 0 today) [class: REPOSITORY_TEST]
- [x] Add pin rows asserting the re-keyed texts after their arms exist, mirroring the existing single-file-probe row shape: the drain-up-to-five fragment, the interrupted-census.json fragment, the grows-across-turns fragment, and the closeout census fragment (one file-probe per row, wrap-safe short needles); pins assert presence only and ride behind the armed behavior per the machinery delta doctrine [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` GREEN, then the whole-plan gate battery (the em-dash and hygiene gates) [class: REPOSITORY_TEST]
- [x] Commit: `test: maintenance pins over the bounded-drain census texts` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```
python3 scripts/done_sweep_gates_lib.py list-interrupted-manifests   # read-only census; PRIMARY-CHECKOUT-ONLY authoring evidence (docs/tmp is gitignored and per-checkout): 21 lines, all dispositioned=yes
bash scripts/check_maintenance_pins.sh
sed -n '1,/## Revisions/p' agents/skills/maintenance/SKILL.md | grep -c "drain-up-to-five"   # exactly 1
sed -n '1,/## Revisions/p' agents/skills/maintenance/SKILL.md | grep -c "closeout census"    # exactly 1
bash scripts/check-no-em-dash.sh added-lines --base HEAD
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Evaluation Criteria

1. The census counts undisposed dead roots only; the drain-up-to-five bound replaces both the ceiling and the execute-each wording; ordering is the census output's printed order; refused heads consume no slots and stay undisposed with an operator-direction channel (count gates, Task 1).
2. The cross-turn state lives in `docs/tmp/done-session/interrupted-census.json`, written by every census-running turn, so the growth alarm (current pre-drain above previous post-drain) is decidable from the file alone and never suppresses the drain (Task 1).
3. The closeout census record is the regression guard with residue-as-input and zero-as-completion semantics (Task 2).
4. Pins assert the re-keyed texts; the pins suite is GREEN (Task 3).
5. No lib code changed and the done skill's disposition paragraph is untouched; the authoring census (21 printed lines all dispositioned, the twenty-second suppressed by the adoption keep-filter, witness included) is recorded accurately in the Gist.

## Done When

- Every checkbox is `[x]`, the Validation Commands are GREEN (the census line evaluated in the primary checkout only), and the review rounds returned ready with zero blocking findings.
- The plan is landed; per the execution lane closure (operator directive, 2026-10-02) this plan is authored and landed, never executed.

## Assumptions

- The authoring census reflects the primary checkout's docs/tmp/done-session state on 2026-10-03; the manifests and the census state file are gitignored session-side, so the census is session evidence recorded here, not a committed artifact, and the Validation Commands' census line is primary-checkout evidence by design.
- The per-turn bound of five is an authoring choice within the entry's drain-up-to-N arm; a future turn may re-derive it from observed drain cadence without re-grilling.
- The census state file holds exactly the last record (overwrite semantics); a lost or first-turn file takes the no-predecessor path, which proceeds with the bound and no alarm, so no pruning or loss can wedge the escalation.

Decision points requiring a grill: none remain.
## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-03-interrupted-manifest-pile-drain.md` (origin class: operator-directed, reliability): the covering plan executed 2026-10-03; the backlog item is deleted in the same completion pass per the fold-then-delete rule; this section is its disposition of record.
