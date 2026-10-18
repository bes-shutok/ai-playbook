# Backlog: a landing's PLAN-PROMPTS closeout discovers collateral served entries only via a red pins suite

- **Filed:** 2026-10-10 (learn Step 1.8 skill-usage issue capture, witnessed during an author-mode maintenance turn's done closeout)
- **Status:** covered (docs/history/plans/2026-10-16-prompt-log-collateral-served-prune.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed defect (log-entry lifecycle discipline)
- **Class:** fix-class
- **Skill/step:** the maintenance authoring payload's self-landing prune evaluation (`agents/skills/maintenance/prompt-templates.md`, the prune-eligibility fence) and `scripts/check_prompt_log_origins.py --prune-audit`

## Observed vs expected

Observed: the wip-auto-checkpoint landing (`bbdc8f999`) fully served the PLAN-PROMPTS entry `execute-plan-restored-manifest-terminal-evidence` - the landing's origin coverage answered the entry's demand - but the landing's prune evaluation, scoped by the prune-eligibility fence to the landing's own dispatch entry only, left the served entry in the log. The pins suite on main then went RED: the origins checker's STALE verdict on that entry blocked the next landing until an out-of-band prune with receipt landed (`PLAN-PROMPTS-PRUNE: execute-plan-restored-manifest-terminal-evidence -> bbdc8f999`, commit `0c09305f6`).

Expected: an entry the landing's content fully serves is pruned with its own receipt in the same closeout (or its deferral is owned by a named duty), so the pins suite never adjudicates a landing's collateral coverage after the fact.

## Evidence

- `git show 0c09305f6` deletes the 17-line `## execute-plan-restored-manifest-terminal-evidence` entry; the commit subject carries the receipt naming the covering landing `bbdc8f999`.
- The fence row (`2026-10-04-plan-prompts-prune-eligibility-fence`, covered) owns the opposite arm: it stops a landing from pruning entries that are NOT served; nothing discovers entries that ARE served.

## Environment

This repository, repo copy, 2026-10-10; author-mode maintenance turn, eight authoring cycles landed in one session.

## Suspected root area and fix shape

The prune-eligibility fence deliberately narrows a landing's prune to its own dispatch entry (anti-over-prune) and has no collateral-discovery counterpart. Candidate arms to adjudicate at authoring: (a) the riders prune evaluation enumerates entries whose demanded origin the landing's coverage now serves (cross-check entry demands against the landed origin rows) and prunes each with its own receipt; (b) a maintenance survey arm flags served-but-unpruned entries before the pins suite runs; (c) write the pins-red adjudication (a STALE verdict on an entry served by the just-landed plan means prune with a receipt naming the covering landing) into the fence text as the standing recovery.
