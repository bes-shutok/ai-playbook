# Plan: authoring round liveness (heartbeat, classifier, marker, reconciliation)

Backlog origin: docs/history/backlog/2026-10-04-authoring-round-liveness-gap.md
Driving force: reliability (not one of the five driving principles; implemented because three witnessed instances, the latest on 2026-10-05, cost an operator flare, a multi-command forensic pass, and a peer harvest adjudicating a live round dead, and the origin's recurrence makes the harm standing rather than incidental)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-authoring-round-liveness-gap-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- authoring round: one plan-creation cycle from the first plan-file write to the certification commit, untracked at the plans root for its whole duration.
- claim heartbeat: refreshing the authoring claim's `updated:` field at named round milestones so the existing freshness test reflects real activity.
- cadence period: the two-hour freshness bound the maintenance G1a stale-claim arm and the foreign-claim gate already use.
- live: an untracked plans-root file a fresh authoring claim names (its `updated:` within one cadence period).
- stranded: an untracked plans-root file no fresh authoring claim names.
- plans-root liveness probe: the new standalone script that enumerates untracked non-ignored plans-root entries and classifies each live or stranded with the evidence named.
- ownership marker: the in-file header line the plan carries between the first write and the certification commit, naming the claim path and owning session.
- fold landing: a landing the authoring session performs mid-round (witnessed: eae2cbfe) while review rounds continue.
- certification commit: the commit whose bytes the review record's digest binds; the digest binding starts here.
- session-level conditional gate: a done-sweep gate the runner does not execute; the applying session runs it in-session per its bullet (the review-thread closure pattern).

## Why

An in-flight authoring round is externally indistinguishable from stranded debris, and its claim ages takeover-eligible mid-round. Three witnessed instances: the 2026-10-04 operator flare cost a multi-command forensic pass to classify one untracked plan file as live, the same day's primary-checkout round went stale in the field while its review rounds ran to about 22:00, and on 2026-10-05 a peer harvest commit adjudicated that live round dead from the stale field and lifted a freeze line mid-round, firing the row's predicted concurrency harm exactly as written. Every authoring round re-opens the window.

## Outcome

The authoring lifecycle keeps its claim fresh at every round milestone, a standing probe classifies any untracked plans-root file as live or stranded with the evidence named in one read, and the plan file self-identifies until certification.

- A mid-round claim survives the freshness test while the round actually progresses, so takeover eligibility tracks reality instead of a frozen timestamp.
- A routine turn classifies an untracked plans-root file as live or stranded in one probe run, ending the forensic-pass class.
- The G1a lane text names mid-round fold landings beside the round's final self-landing, closing the contract reconciliation the origin arm 4 demands.
- Gate delta: grows the authoring lifecycle's checked-condition set (the heartbeat milestones, the ownership marker duty, the liveness probe and its two session-level integrations); adds one standalone probe script with its selftest; no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing is removed. Priced by the cited completed-integrity-failure witnesses in the origin row: the 2026-10-05 harvest adjudicating a live round dead from the stale field (the concurrency harm firing), and the 2026-10-04 operator flare's forensic pass (the visibility harm).

## Assumptions

- assume all four origin arms are included as pairwise-combinable mechanisms per the origin's own reading, with arm 4 landing as the G1a parenthetical plus the recorded reconciliation that the worktree-first standard (the plans Phase 0 hard gate against primary-checkout authoring) is the operative contract today, so no further side moves.
- assume the heartbeat binds through the AUTHORING CLAIM paragraph in agents/skills/maintenance/prompt-templates.md because the plans skill's Phase 0 names that paragraph the procedure of record for every authoring session, dispatched or in-session; the plans skill gains no duplicate milestone list.
- assume the classifier is a standalone probe with two session-level integrations (the maintenance survey and a done in-session gate), not a `done_sweep_gates` runner gate; basis: the done skill already carries the session-level-conditional-gate pattern (review-thread closure) for prose-owned gates, and a runner edit would grow code machinery the origin does not price.
- assume the probe's freshness rule reuses the existing cadence period (120 minutes) and claim-matching is text containment of the plan's slug or basename in the claim file, the same keyed shape the AUTHORING CLAIM duty uses for its filename; basis: the witnessed claims all key their slugs this way.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: Authoring rounds become self-identifying and freshness-honest, so a live round is never again adjudicated dead or classed as debris; closes three witnessed instances (reliability).

**Before (today):** An authoring session writes its plan file, which sits untracked at the plans root for the whole round. Its claim file under the gitignored scratch carries `updated:` equal to `created:` through review rounds, a fold landing, and record writes, because nothing refreshes it. A peer harvest turn reads the stale field, adjudicates the round dead, and lifts the queue freeze mid-round; a human seeing the untracked file spends a multi-command forensic pass to learn what one marker could have said. A round exceeding two hours turns takeover-eligible while its author still works.

**After (this plan):** The same round refreshes its claim at every milestone (plan write, round launch, round return, research boundary, review-record write, fold landing, and gate pass), so the freshness test tracks real activity. A routine turn runs one probe: it lists every untracked non-ignored plans-root entry and classifies each live or stranded with the claim path and timestamp named. The plan file itself carries one header line naming its claim and session until the certification commit drops it. A stranded file fails loud; a live one is left alone.

Edge cases: a plan whose claim was deleted after closeout reads stranded, which is correct (nothing live names it); a file under `completed/`, `deferred/`, or `rejected/` is never enumerated; a stale claim that names a file keeps it unclassified-live only while within the cadence bound, after which the probe reports stranded and the takeover arms may act.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the declaration fixture passes, including the probe's behavioral selftest (fresh claim names it live, no claim or stale claim is stranded, state subdirectories are never enumerated).
- regression safety: the pins suite and the shared-skill-body runtime-neutrality gate stay green; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: the heartbeat binds at exactly the seven named milestones (four pre-existing, three new); the probe touches only the plans root surface; the marker exists only between the first write and the certification commit.

**Done when:**
- `( cd "$REPO" && python3 scripts/test_authoring_plans_liveness.py )` exits 0.
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- A routine turn classifies any untracked plans-root file as live or stranded with the evidence named in one read; a mid-round claim survives the freshness test only while the round actually progresses; both 2026-10-04 instances classify correctly under the shipped mechanism (the origin row's Ship-when triple, carried verbatim as the deployed-behavior bar; no further human action is required in this repository).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/prompt-templates.md` (the AUTHORING CLAIM paragraph's refresh sentence only; all other paragraphs are frozen)
- `agents/skills/maintenance/SKILL.md` (the survey's authoring-claim consult bullet region for the new probe bullet, and the authoring-lane paragraph's self-landing sentence for the parenthetical; all other sections are frozen)
- `agents/skills/done/SKILL.md` (the pre-docs gate enumeration line and the guidance region beside the review-thread closure bullet; all other sections are frozen)
- `agents/skills/plans/SKILL.md` (Phase 0 Step 0.2 for the marker paragraph; all other sections are frozen)
- `scripts/check_authoring_plans_liveness.py` *(new)*
- `scripts/OUTCOME_CONTRACT.md` (the per-script assumptions table's new row only; the rest is frozen)

**Tests:**
- `scripts/test_authoring_plans_liveness.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates.sh` and `scripts/done_sweep_gates_lib.py`; reason: the runner is untouched; the gate rides the session-level-conditional pattern.
- `scripts/check_maintenance_pins.sh`; reason: consumed as a gate and audited beside its provenance, not edited unless a pin row's literal collides with a prescribed insertion (then the row updates in the same edit per the pins rule).
- the sibling debris row's repo-root surface; reason: this plan's probe enumerates only the plans directory.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed `python3 scripts/plan_readiness.py --pre-round` with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against the four skill files (the new-duty spans returned no match; the three preserved spans matched); the rule 22 mechanical audit verified every new-duty span occurs exactly twice in the plan bytes (once in its Task 1 declaration, once in its Task 2 prescription) and `bash -n` accepted the Validation Commands block. Round-start state for r1: authoring worktree ai-playbook-wt-alg, branch 2026-10-05-authoring-round-liveness-gap, plan bytes at the draft commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && python3 scripts/test_authoring_plans_liveness.py -v )
( cd "$REPO" && python3 scripts/check_authoring_plans_liveness.py --repo "$REPO" )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Pin the liveness contract (RED fixture suite)

Files:
- `scripts/test_authoring_plans_liveness.py` *(new)*

Evidence:
- `( cd "$REPO" && python3 scripts/test_authoring_plans_liveness.py )`; covers the RED-today criterion: the probe selftest fails on the missing script while the preserved-span test passes

- [x] Create `scripts/test_authoring_plans_liveness.py` as a unittest module that resolves the repository root from its own file location and contains two test groups: the probe behavior group builds each fixture inside a temp directory (`mktemp -d`) with an explicit teardown, never inside the repository; the declaration group asserts fixed-string spans against the four skill files (the probe script is exercised by the behavior group, not span-asserted) [class: REPOSITORY_TEST]
- [x] `PlansLivenessProbeTest#test_fresh_claim_classifies_live`; given a temp git repository whose plans directory holds one untracked plan file and whose authoring-claims directory holds one claim with an `updated:` minutes old containing the file's slug, expects `check_authoring_plans_liveness.py` to exit 0 and print a `live:` line naming the path and the claim [class: REPOSITORY_TEST]
- [x] `PlansLivenessProbeTest#test_no_claim_classifies_stranded`; given a temp git repository whose plans directory holds one untracked plan file and no claims directory, expects the probe to exit 1 and print a `stranded:` line naming the path [class: REPOSITORY_TEST]
- [x] `PlansLivenessProbeTest#test_stale_claim_classifies_stranded`; given a temp git repository whose only claim's `updated:` is three hours old and names the file, expects the probe to exit 1 with a `stranded:` line [class: REPOSITORY_TEST]
- [x] `PlansLivenessProbeTest#test_state_subdirectories_never_enumerated`; given untracked files under the plans directory's `completed/` subdirectory, expects the probe to report zero candidates and exit 0 [class: REPOSITORY_TEST]
- [x] `PlansLivenessProbeTest#test_witnessed_shapes_classify_live`; given fixtures replicating the two 2026-10-04 instances (a claim created minutes before its plan file appears, in each case), expects both to classify live [class: REPOSITORY_TEST]
- [x] `LivenessDeclarationTest#test_heartbeat_milestones_declared`; given agents/skills/maintenance/prompt-templates.md, expects the file to contain `at every review-record write while a round is in flight` and `at every mechanical gate pass (the pre-round gates, the certification commit, the readiness gate)` [class: REPOSITORY_TEST]
- [x] `LivenessDeclarationTest#test_marker_and_reconciliation_declared`; given agents/skills/plans/SKILL.md and agents/skills/maintenance/SKILL.md, expects plans to contain `Authoring claim: <claim path> (session <session id>)` and `dropped at the certification commit`, and maintenance to contain `(mid-round fold landings included, each through the same lock)` and `Plans-root liveness probe` [class: REPOSITORY_TEST]
- [x] `LivenessDeclarationTest#test_done_gate_declared`; given agents/skills/done/SKILL.md, expects the file to contain `plans-root liveness (a session-level conditional gate the runner does not execute; apply it in-session per its bullet below before continuing)` and `check_authoring_plans_liveness.py` [class: REPOSITORY_TEST]
- [x] `LivenessDeclarationTest#test_preserved_anchors_stay_pinned`; given the four skill files, expects the preserved spans `immediately when a review round returns` (prompt-templates.md), `plans-archive-twin` (done/SKILL.md gate list), and `lands via its own merge-lock-serialized self-landing onto the default branch from its ad-hoc worktree` (maintenance/SKILL.md) to remain present [class: REPOSITORY_TEST]
- [x] Run → expect RED: `( cd "$REPO" && python3 scripts/test_authoring_plans_liveness.py )` fails with the probe group erroring on the missing script and the declaration group failing on the absent spans, while `test_preserved_anchors_stay_pinned` passes [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the authoring round liveness contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Heartbeat, marker, probe, and integrations (GREEN)

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/done/SKILL.md`
- `scripts/check_authoring_plans_liveness.py` *(new)*
- `scripts/OUTCOME_CONTRACT.md`

Evidence:
- `( cd "$REPO" && python3 scripts/test_authoring_plans_liveness.py )`; covers the GREEN criterion: all fixture tests pass
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: no pin row's literal broke
- `( cd "$REPO" && python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies )`; covers the shared-body criterion: the plans skill insertion stays runtime-neutral

- [x] In `agents/skills/maintenance/prompt-templates.md`, replace the span `, and at every phase boundary of the pre-plan research, so no active phase can outlast one cadence period (2 hours) without a refresh; delete that primary-checkout claim file at closeout` inside the operative AUTHORING CLAIM paragraph (the paragraph opening `AUTHORING CLAIM, the claim file this session writes before any plan work`, the one the plans skill names Procedure of record; the same-shaped sentence in the 2026-09-21 changelog bullet is frozen history and is not touched) with `, at every phase boundary of the pre-plan research, at every review-record write while a round is in flight, at every fold landing (including one this same session performs mid-round, the eae2cbfe witness), and at every mechanical gate pass (the pre-round gates, the certification commit, the readiness gate), so no active phase can outlast one cadence period (2 hours) without a refresh; delete that primary-checkout claim file at closeout` (the tail clause is quoted in both sides so its survival is pinned; the milestone list is the plan-write, round-launch, round-return, research-boundary, review-record-write, fold-landing, and gate-pass set) [class: IMPLEMENTATION_REQUIRED]
- [x] Insert the following paragraph into `agents/skills/plans/SKILL.md` at the end of Phase 0 Step 0.2, after the hard-gate paragraph ending `never fall back to working in the primary checkout.` (that sentence is the unique anchor) [class: IMPLEMENTATION_REQUIRED]

```markdown
**Authoring ownership marker:** from the first plan-file write until the certification commit, the plan header carries one line under the metadata block, `Authoring claim: <claim path> (session <session id>)`, naming the Phase 0 claim file and the owning session so an untracked plan file self-identifies in one read. The line is dropped at the certification commit, and the digest binding starts at certification, so pre-certification header churn costs no recertification round; the maintenance liveness probe reads the marker as the in-file witness beside the claim file's freshness.
```

- [x] Insert the following bullet into `agents/skills/maintenance/SKILL.md` immediately after the Authoring-claim consult bullet (the bullet beginning `- Authoring-claim consult (added 2026-09-30` is the unique anchor; the new bullet sits beside it as a sibling survey arm) [class: IMPLEMENTATION_REQUIRED]

```markdown
- Plans-root liveness probe (added 2026-10-05, the authoring-round-liveness-gap plan): run `python3 scripts/check_authoring_plans_liveness.py --repo <repo-root>` (repo-local copy first, then the deployed home copy) once per survey; the probe enumerates untracked non-ignored `.md` entries under the resolved plans directory and classifies each live (a fresh authoring claim names it, its `updated:` within one cadence period) or stranded (none does), reporting live or stranded by path with the claim path and `updated:` timestamp as the named evidence; a stranded classification fails loud in the survey output as a reported finding, never a silent pass, and the probe's outcome contract (scripts/OUTCOME_CONTRACT.md) governs its exits; the G1a discovery arm's facts `tmp_dir`-override caveat extends to this reader of the surface.
```

- [x] In `agents/skills/maintenance/SKILL.md`, replace the span `from its ad-hoc worktree, carrying the plan-document commits` in the authoring-lane paragraph with `from its ad-hoc worktree (mid-round fold landings included, each through the same lock), carrying the plan-document commits` (the tail clause `carrying the plan-document commits` is quoted in both sides so its survival is pinned) [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/done/SKILL.md`, replace the span `review-thread closure (a session-level conditional gate the runner does not execute; apply it in-session per its bullet below before continuing), review-staging` in the pre-docs gate enumeration with `review-thread closure (a session-level conditional gate the runner does not execute; apply it in-session per its bullet below before continuing), plans-root liveness (a session-level conditional gate the runner does not execute; apply it in-session per its bullet below before continuing), review-staging` (the surrounding list items are quoted so their survival is pinned) [class: IMPLEMENTATION_REQUIRED]
- [x] Insert the following bullet into `agents/skills/done/SKILL.md` immediately after the review-thread closure guidance bullet (the bullet beginning `- **review-thread closure:**` is the unique anchor) [class: IMPLEMENTATION_REQUIRED]

```markdown
- **plans-root liveness:** run `python3 scripts/check_authoring_plans_liveness.py --repo <repo-root>` (repo-local copy first, then the deployed home copy). The probe enumerates untracked non-ignored `.md` entries under the resolved plans directory and classifies each live or stranded against the authoring-claims directory by the existing freshness rule (a fresh claim, `updated:` within one cadence period, whose text names the file's slug or basename). The gate answers in the outcome contract: exit 0 with the final `OUTCOME: pass` line reports the classification and continues; exit 1 (`OUTCOME: fail`) names a stranded untracked plan file: report blocked, resolve it through the authoring-claims registry (a live peer's claim refreshes by its own heartbeat; a truly stranded file is adopted or removed by its owner, never deleted by this run), and do not report completion; exit 2 (`OUTCOME: indeterminate`, a crash shape the probe does not model today) and exit 3 (`OUTCOME: tool_error`) are tool outcomes: fix the invocation and re-run; and a run that ends with no final `OUTCOME:` line is tool error per the contract's no-line rule: stop and re-derive the probe's state from disk. A repository with no untracked plans-root entries passes trivially; the G1a discovery arm's facts `tmp_dir`-override caveat extends to this reader of the surface.
```

- [x] Create `scripts/check_authoring_plans_liveness.py` implementing the probe contract: `--repo <root>` (default the working directory) and `--cadence-minutes` (default 120); resolve the claims directory as `<repo>/<tmp_dir>/authoring-claims/` where `<tmp_dir>` is read from the repository facts document's TOML `tmp_dir` key with the conventional fallback `docs/tmp/` (the G1a discovery arm's facts `tmp_dir`-override caveat extends to this reader); enumerate with `git ls-files --others --exclude-standard -- <plans_dir>` filtered to `.md` files at the plans root only (never the `completed/`, `deferred/`, or `rejected/` subdirectories); parse every claim for its `updated:` timestamp (ISO with offset; an unparseable claim is skipped with a warning line) and read its raw text; a claim names a plan when the plan's slug (the basename stem with its leading `YYYY-MM-DD-` prefix stripped) or the full basename occurs in the claim text; a plan is live when at least one fresh claim names it and stranded otherwise; print one `live: <path> (claim <name> updated <timestamp>)` or `stranded: <path> (no fresh claim names it)` line per candidate with a summary line, answer in the outcome contract (exit 0 `OUTCOME: pass` when zero stranded, exit 1 `OUTCOME: fail` naming the stranded paths, exit 3 `OUTCOME: tool_error` on a non-repository root or a usage violation, and never end without a final `OUTCOME:` line), and mutate nothing [class: IMPLEMENTATION_REQUIRED]
- [x] Append one row to the per-script assumptions table in `scripts/OUTCOME_CONTRACT.md` so the probe is born-conformant (the register's own rule holds a decision script outside the contract until its row lands) [class: IMPLEMENTATION_REQUIRED]

```markdown
| `check_authoring_plans_liveness.py` | invocation inside a git repository with a resolvable `--repo` (a non-repository root is tool error); a readable plans directory and, when untracked candidates exist, a readable resolved claims directory (an unreadable claims directory with live candidates is tool error; no candidates passes trivially); claim files whose `updated:` cannot be parsed are skipped with a warning line, never classified; a run over readable inputs otherwise always reaches a verdict (no indeterminate class exists) | born-conformant (the authoring-round-liveness-gap plan, 2026-10-05) |
```
- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/test_authoring_plans_liveness.py )` passes all nine probe and declaration tests; the pins suite and the shared-body gate exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: authoring round liveness (heartbeat milestones, plans-root probe, ownership marker, G1a reconciliation)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Full validation and witnessed-instance sweep

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each new-duty span pinned in Task 1, `grep -cF` over its owning file returns exactly 1 after the edits, and for the three preserved spans it returns at least 1 (their current counts, two and five, are legitimate prose and must not be deduplicated) [class: REPOSITORY_TEST]
- [x] Ship-when evidence sweep: run the probe against a scratch repository replicating the two 2026-10-04 witnessed states (each a claim created minutes before its untracked plan file appears) and record that both classify live, plus the stranded state (a plan with no claim at all, the shape the selftest fixture already covers) classifying stranded, each with the evidence named in the output lines [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-authoring-round-liveness-gap.md`; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-alg2 (branch plan-authoring-round-liveness-gap-exec) by the standing maintenance execution lane. Tasks 1-3 completed as prescribed: the RED fixture suite (81a2be43) pins the nine probe and declaration tests with the witnessed RED shape, and the GREEN commit (daa1a924) lands the heartbeat milestone replacement in prompt-templates.md, the Authoring ownership marker paragraph in plans/SKILL.md, the Plans-root liveness probe bullet and G1a mid-round-fold parenthetical in maintenance/SKILL.md, the plans-root liveness session-level gate bullet and gate-enumeration insertion in done/SKILL.md, the probe script check_authoring_plans_liveness.py, and the born-conformant OUTCOME_CONTRACT row.

Validation: the full Validation Commands block exits 0 on the executed tree (selftest 9/9 OK, probe OUTCOME: pass with zero candidates, pins suite pass, shared-skill-bodies gate OK, em-dash added-lines scan clean, hygiene scan exit 0). Ship-when evidence sweep recorded: the witnessed live shape (claim minutes old naming the file) classifies live with the claim path and timestamp named; the three-hour-stale shape and the no-claim shape both classify stranded with the path named, exits 1. Exec review r4 (fresh-adversarial, one worker) found zero blocking findings with three Low residuals: two accepted (the plan-origin marker-reader over-claim in the plans skill paragraph; the 3.11+-only Z-suffix parser behavior, fail-visible per the contract row) and one overflowed (the unmodeled --cadence-minutes semantic range, recorded for the simplifier census); records at docs/reviews/2026-10-05-plan-review-authoring-round-liveness-gap-r4.{md,stats.json}.

Deferred residuals: the three r4 Low dispositions above; no blocking or High/Medium items remain. Origin row docs/history/backlog/2026-10-04-authoring-round-liveness-gap.md is covered by this execution and folded in the landing.
