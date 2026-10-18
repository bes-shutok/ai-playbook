# Plan: plans-quality-gate truncated load

Backlog origin: docs/history/backlog/2026-10-04-plans-quality-gate-truncated-skill-load.md
Driving force: code-quality (primary), automation (secondary)
Plan review record: the staging series {reviews_dir}/2026-10-04-plan-review-plans-quality-gate-truncated-load-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Skill-load truncation: a tool-level skill delivery that returns a SKILL.md body ending before the file ends, carrying an explicit truncation marker.
- Load-completeness clause: the using-skills principle stating a truncated skill load is incomplete by construction, with read-the-full-file recovery named before any workflow step of that skill executes.
- Loud-finish gate: the plans-skill finalization duty that runs the readiness validator's full-gate mode before the session describes a plan as ready or delivered, reporting the no-review-artifact failure class by name when it fires.
- Feature slug: the plan filename stem with its leading YYYY-MM-DD- prefix stripped; the readiness gate derives its review-artifact discovery glob from it.
- Readiness validator: scripts/plan_readiness.py, the fail-closed plan gate; full-gate mode is the plain invocation `python3 scripts/plan_readiness.py <plan-path>`.
- Full-gate mode: the validator invocation without `--pre-round`; it consults the review record and reports the no-review-artifact and missing-sidecar failure classes.
- Plan Quality Gate: the plans skill's review loop (review-plan panels) that certifies a plan before delivery.
- Budget gate probes: the quota-window checks the plans skill runs at review-round and handoff boundaries.
- Disk-truth record: the fixed-name notes file a long authoring session keeps as its only trusted session state.
- Done handoff: the plans workflow's final step invoking the done skill to commit the plan and its review artifact.
- Skill-gate marker: the fresh per-(project, session) marker file the plans skill writes before every plan-file write, making the did-the-skill-run question loud at authoring start.

## Why

A witnessed authoring session received the plans skill load truncated mid-file, treated the partial body as the whole contract, completed the gates the visible text described, and then skipped the Plan Quality Gate review loop, the budget probes, the disk-truth record, and the done handoff; the operator had to ask why reviews never ran. The repo's loudness machinery covers the start of authoring (the skill-gate marker) but nothing is loud when an authoring session reports a plan delivered without a review record.

## Outcome

An authoring session can no longer silently deliver an unreviewed plan after a truncated skill load.

- A truncated skill load is recorded as incomplete by construction in the skill-loading discipline, with the read-the-full-file recovery named before any workflow step of that skill executes.
- An authoring session reaching plan delivery runs the readiness validator's full-gate mode; a missing review record for the plan's feature slug is reported by name in the session's own final report instead of surfacing only at a later execution or done boundary.
- No new gate script or validator mode exists; both arms state or route signals that already exist (the validator's failure classes and the skill listing's base-directory pointer).

Gate delta: one review-layer duty addition whose violation blocks (the loud-finish gate paragraph in agents/skills/plans/SKILL.md) and one guidance-clause addition (the skill-load completeness principle in agents/skills/using-skills/SKILL.md); each addition is priced by the witnessed completed integrity failure recorded in the origin row (the 2026-10-04 truncated-load incident); no refusal classes, hard gates, fences, protocol layers, or schema state fields are added or removed, and no script is created.

## Assumptions

- assume the loud-finish home is the plans skill's finalization boundary routing the validator's existing full-gate failure class, not a done-closeout arm, not a new validator mode, and not drafting-mode prose alone; basis: the origin row's fix shape routes existing signals to the authoring report path and rejects new gate scripts, and the witnessed session never reached done, so a done-closeout arm could not have fired (origin row, What happened step 3 and Suggested fix shape items 2 to 3).
- assume the truncation clause lands as one numbered principle in the using-skills Proactive Usage Principles list, the file that owns skill-usage discipline for every session; basis: that file carries the principles list today and contains no truncation text (grep verified 2026-10-04).
- assume the validator itself needs no code change; its full-gate failure text already names the missing record; basis: origin fix shape item 3 plus the Task 1 probe receipt.
- assume the delivery path for both arms is the skill catalog listing plus session-side discipline: no host mechanism injects these files' content into sessions (review r1 finding F1 verified no session-start hook on this host), so the arms' reach is bounded by the same load path they guard, and the sibling cluster row docs/history/backlog/2026-10-04-investigate-workflow-skill-lookup-miss.md owns the workspace-level routing half; basis: review r1 finding F1 (verified) and the origin row's Cluster line.
- Decision receipt for the origin entry's Phase 1 home adjudication (done-skill closeout versus validator authoring-mode surface versus plans drafting-mode paragraph): resolved as the validator-routed plans-skill finalization duty; source: origin row evidence plus standing operator directives (continuous authoring cycles recorded in loop_mode 2026-09-30, live operator direction to proceed 2026-10-04); date: 2026-10-04; affected sections: Outcome, Tasks 2 and 3.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: skill-load truncation gets an explicit incompleteness rule and plan delivery gets a loud full-gate check, so an unreviewed plan can no longer ship silently (code-quality: an authoring session must surface its own skipped gate; automation: the surface is the session's own report, not operator discovery).

Before (today): a session invokes the plans skill, the tool returns the body truncated mid-file, and the session runs the visible half as if it were whole. It writes the plan, passes the gates the visible text describes, reports the plan as delivered, and ends; the review loop, budget probes, and done handoff living below the truncation point never run. Nothing in the repo makes that skip loud; the operator discovers it by asking.

After (this plan): the same truncated load now has a recorded rule: truncation means incomplete, so the session reads the full SKILL.md from the skill's base directory before executing any of that skill's steps. If a session still reaches plan delivery with no review record, the loud-finish gate makes it run the full readiness validator and report the validator's own failure, no review artifact for feature slug, in its final output. The operator sees the skip in the session's report instead of having to detect it.

Edge cases: a conversational draft under drafting mode states review finalization is pending and does not claim delivery, unchanged; a plan delivered through the validator's cap-closure terminal shape passes the full gate through that shape's own acceptance, so the new duty adds no second exit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both prescribed texts name the exact failure class and the exact recovery (the validator's reason line quoted from live output; the base-directory full-file read), each verified by its own pin.
- completeness: the loud-finish duty sits at the finalization self-check boundary so it cannot be skipped by the report path that witnessed the failure; verified by the anchor and span pins.
- maintainability: no new scripts, validator modes, or duplicated failure text; both arms are prose duties over existing machinery; verified by the out-of-scope list and the absence pins.

**Done when:**
- agents/skills/using-skills/SKILL.md carries the skill-load completeness principle with the base-directory full-file recovery, and no longer claims the nonexistent SessionStart hook mechanism (review r1 finding F1).
- agents/skills/plans/SKILL.md carries the loud-finish gate paragraph at the pre-finalization self-check boundary with the by-name report requirement.
- The Task 1 RED receipts (absence greps over both files; the fixture probe's validator output) are recorded beside their tasks.
- bash scripts/check-no-em-dash.sh touched passes, and the public-hygiene scan exits 0.

**Ship when:**
- none; both arms are repository text with no deployed or cross-team condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- agents/skills/using-skills/SKILL.md
- agents/skills/plans/SKILL.md

**Tests:**
- none; both arms are documentation-duty edits verified by pins and the validator's own output.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- scripts/plan_readiness.py; reason: the validator already owns the failure class; no code change is in scope (Assumptions bullet 3)
- agents/skills/execute-plan/SKILL.md; reason: the execution and done boundaries already bind review records; this plan touches only the authoring report path
- docs/history/backlog/2026-10-04-skill-monolith-module-extraction.md; reason: the monolith split is a sequenced separate effort, explicitly outside this plan's scope (origin entry rejected alternatives)

## Validation Commands

Pre-round record (authoring, 2026-10-04): em-dash scan `touched` over the authoring checkout exit 0; public-hygiene scan exit 0 OUTCOME: pass; readiness pre-round exit 0 OUTCOME: pass; rule 19 RED-today evidence recorded under Task 1 (both pin spans absent from both target files; fixture probe failure text captured); rule 22 mechanical audit pass (each pin span occurs exactly once in the prescribed task text; bash -n clean over this block).

```bash
set -e
# Pin 1: the load-completeness clause exists in using-skills (new text; RED at authoring per Task 1 receipt, GREEN after Task 2)
grep -q "incomplete by construction" agents/skills/using-skills/SKILL.md || { echo "pin1 missing truncation clause"; exit 1; }
grep -q "read the full SKILL.md from the skill's base directory" agents/skills/using-skills/SKILL.md || { echo "pin1 missing full-file recovery"; exit 1; }
# Pin 4: the stale hook-mechanism claims are gone from using-skills (forbidden greps use the three-way exit split)
rc=0; grep -qiE "session[-]?start" agents/skills/using-skills/SKILL.md || rc=$?
if [ "$rc" -eq 0 ]; then echo "pin4 stale hook claim present"; exit 1; elif [ "$rc" -ge 2 ]; then echo "pin4 grep error"; exit 1; fi
grep -q "through their skill listings" agents/skills/using-skills/SKILL.md || { echo "pin4 missing delivery sentence"; exit 1; }
grep -q "## Skill Discovery" agents/skills/using-skills/SKILL.md || { echo "pin4 missing discovery heading"; exit 1; }
# Pin 2: the loud-finish gate exists at the plans finalization boundary (new text; RED at authoring per Task 1 receipt, GREEN after Task 3)
grep -q "Loud-finish gate (mechanical)" agents/skills/plans/SKILL.md || { echo "pin2 missing loud-finish paragraph"; exit 1; }
grep -q "full-gate mode" agents/skills/plans/SKILL.md || { echo "pin2 missing full-gate invocation duty"; exit 1; }
grep -q "reported by name in the authoring session's final report" agents/skills/plans/SKILL.md || { echo "pin2 missing by-name report duty"; exit 1; }
# Pin 3: the duty sits at the pre-finalization self-check boundary (anchor region check)
grep -q "Pre-finalization self-check" agents/skills/plans/SKILL.md || { echo "pin3 missing finalization anchor"; exit 1; }
# Scans (both target files carry no em-dash today; insertions are em-dash-free, so touched scope is safe)
( cd "$(git rev-parse --show-toplevel)" && bash scripts/check-no-em-dash.sh touched )
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: RED receipts (probe both gaps today)

Files:
- none (evidence only; the fixture plan is scratch, created and deleted in the run checkout, never committed)

Evidence:
- `grep -c "incomplete by construction" agents/skills/using-skills/SKILL.md; grep -c "incomplete by construction" agents/skills/plans/SKILL.md; grep -c "loud-finish" agents/skills/plans/SKILL.md; grep -c "full-gate" agents/skills/plans/SKILL.md`; covers "both pin spans are absent today"
- `python3 scripts/plan_readiness.py <scratch fixture plan path>`; covers "the full gate reports the missing-record class by name"

- [x] Absence greps executed 2026-10-04 over the authoring checkout: "incomplete by construction" 0 hits in agents/skills/using-skills/SKILL.md and 0 in agents/skills/plans/SKILL.md; "loud-finish" 0 and "full-gate" 0 in agents/skills/plans/SKILL.md [class: REPOSITORY_TEST]
- [x] Fixture probe executed 2026-10-04: a scratch plan `2026-10-04-fixture-pqgtl-probe.md` under the plans root with no review artifacts; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-04-fixture-pqgtl-probe.md` printed `readiness FAILED: no review artifact for feature slug 'fixture-pqgtl-probe' under <checkout>/docs/reviews`, exit 1, `OUTCOME: fail`; fixture deleted after the probe [class: REPOSITORY_TEST]

### Task 2: load-completeness clause in using-skills

Files:
- `agents/skills/using-skills/SKILL.md`

Evidence:
- `grep -q "incomplete by construction" agents/skills/using-skills/SKILL.md && grep -q "read the full SKILL.md from the skill's base directory" agents/skills/using-skills/SKILL.md`; covers "the clause and its recovery are present"
- `! grep -qiE "session[-]?start" agents/skills/using-skills/SKILL.md`; covers "the stale hook-mechanism claims are gone (run as the three-way split in Validation Commands)"

- [x] Append principle 12 to the Proactive Usage Principles list, text exactly: `12. **Skill-load completeness** - A skill load that reports truncation is incomplete by construction: before executing any workflow step of that skill, read the full SKILL.md from the skill's base directory. A skill whose contract cannot survive a partial load either fits the load window or states which sections are load-bearing.` [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the sentence `This skill is automatically triggered by the SessionStart hook, dynamically scanning all available skills under the` `~/.agents/skills/` `directory.` (the span ends at that period; the next line is the Dynamic Scanning heading) with `This guide catalogs the skills available to sessions; hosts surface them through their skill listings, and a session applies this guide by opening it (see the skill-load completeness principle for truncated loads).` [class: IMPLEMENTATION_REQUIRED]
- [x] Retitle the section heading `## Dynamic Scanning Mechanism` to `## Skill Discovery`, and delete its bullet line `- Hook location:` `~/.agents/hooks/session-start.sh` (the remaining Scan directory and Extracted information bullets stay) [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the sentence `The SessionStart hook injects the following principles into every session:` (the tail it introduces is the numbered principles list, which stays) with `Sessions apply the following principles by reading this guide:` [class: IMPLEMENTATION_REQUIRED]
- [x] Run both pin 1 greps from Validation Commands; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: treat a truncated skill load as incomplete by construction` (58e7a476) [class: IMPLEMENTATION_REQUIRED]

### Task 3: loud-finish gate at the plans finalization boundary

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- `grep -q "Loud-finish gate (mechanical)" agents/skills/plans/SKILL.md && grep -q "full-gate mode" agents/skills/plans/SKILL.md && grep -q "reported by name in the authoring session's final report" agents/skills/plans/SKILL.md`; covers "the duty, its invocation, and its report path are present"

- [x] In the Pre-finalization self-check section, immediately after the six-question list and before the closing validator paragraph, insert the paragraph, text exactly: `**Loud-finish gate (mechanical):** before describing the plan as ready for execution or delivered, run the readiness validator's full-gate mode over the plan (python3 scripts/plan_readiness.py <plan-path>). A failure in the no-review-artifact or missing-sidecar class is reported by name in the authoring session's final report, quoting the validator's reason line; the session does not describe the plan as delivered while that failure stands. The drafting-mode caveat is unchanged: a conversational draft states review finalization is pending instead of claiming delivery.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run all pin 2 and pin 3 greps from Validation Commands; expect GREEN [class: REPOSITORY_TEST]
- [x] Run the Task 1 fixture probe again unchanged; expect the same validator failure text (the signal persists; the duty now routes it to the report path) [class: REPOSITORY_TEST]
- [x] Commit: `plans: make an unreviewed plan delivery loud at the finalization boundary` (b11d4fc7) [class: IMPLEMENTATION_REQUIRED]

## Disposition

Executed 2026-10-04 from worktree ai-playbook-wt-pqgtl (branch plan-pqgtl-exec). Task 1 RED receipts: all four absence greps returned 0 hits; the fixture probe printed `readiness FAILED: no review artifact for feature slug 'fixture-pqgtl-probe'` exit 1. Task 2 landed as 58e7a476 (principle 12 appended, hook-mechanism sentence replaced, heading retitled `## Skill Discovery`, hook-location bullet deleted, injection sentence replaced; pins 1 and 4 GREEN). Task 3 landed as b11d4fc7 (loud-finish paragraph inserted immediately after the six-question list; pins 2 and 3 GREEN; fixture probe re-run unchanged). Receipts commit 7e1f232c. Exec review r1: ready=yes, zero blocking, three Low residuals (digest staleness caused by the receipts commit itself, judged no-action; line 27 detection sentence judged not an F1-class over-claim; three run-verification boxes ticked with corroborated but unannotated claims). Scans: em-dash touched exit 0, public hygiene OUTCOME: pass. Origin row folded with this landing.
