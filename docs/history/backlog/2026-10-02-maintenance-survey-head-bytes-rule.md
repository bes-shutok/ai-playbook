# Maintenance survey reads status-bearing files from the stale primary working tree

- **Filed:** 2026-10-02
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Class:** fix-class
- **Driving force:** reliability

## Problem

Witnessed 2026-10-02 (twice in one survey, and recurring every session): the maintenance survey read backlog items from the primary checkout's working tree and reported items as open that were already done or covered at HEAD — the primary working-tree bytes are stale whenever a peer lands between the checkout's last refresh and the survey. The correction (read status-bearing corpus files via `git show HEAD:<path>`, never working-tree bytes) lives only in session memory; the maintenance skill's survey step does not pin it (verified 2026-10-02: zero matches for the HEAD-read discipline in the skill at HEAD). Every fresh maintenance session can re-introduce the phantom-open-item class: acting on items that no longer exist, or standing down believing the queue is empty when HEAD says otherwise.

## Expected

The maintenance skill's survey step pins the freshness discipline for status-bearing corpus files (backlog items, plan-prompts log, claims): status is read from the committed tree at the survey's base ref, not from the working tree — or an equivalent freshness verification (status-vs-HEAD comparison) is spelled in the step. A pins-suite pin witnesses the rule's presence so it cannot silently regress.

## Suggested fix

Add one sentence to the maintenance SKILL.md survey step naming the class (working-tree bytes vs the base ref) and the required read shape, then add a pin to the pins suite (fixed-string grep on the skill file, next to the existing survey-step pins), and run the suite plus the hygiene scan before landing.

## Dedup probe

Searched open backlog items and top-level plans for `HEAD bytes`, `git show HEAD`, and `stale` on 2026-10-02: no open item or plan covers the survey-read discipline. The machinery-inventory-upkeep item covers inventory registration drift, not the survey freshness rule; this item does not duplicate it.
