# Plan: Self-Heal Recovery Direction and Evidence

Backlog origins (scope of record):
- docs/history/backlog/2026-11-20-self-heal-explicit-workaround-not-carried-through.md
- docs/history/backlog/2026-11-20-self-heal-premature-stop-without-workaround-evidence.md
- docs/history/backlog/2026-11-16-self-heal-fallback-searches-project-prompt-log.md
- docs/history/backlog/2026-11-16-self-heal-later-gate-without-disposition.md

Driving force: efficiency + code-quality
Plan review record: .ai-playbook/reviews/2026-11-20-plan-review-self-heal-explicit-workaround-not-carried-through-pe5ba9a82-r*.md
Execution budget: 0.5h total, largest task 0.5h
Executed: yes (a4796b229e12ec49635d0fa25182b14be5c82b0f)

## Terms

- **Explicit workaround direction:** a user instruction that asks self-heal to find or apply another authorized route to the stated outcome.
- **Recovery result:** self-heal's terminal report of the blocker, checks performed, next owner or action, and evidence needed to proceed.
- **Caller disposition:** an existing caller-owned place where a later-stage requirement can remain visible until its source-defined activation point.

## Why

The operator reports that recovery did not proceed until they repeated the request as a workaround search. The current skill already directs agents to search and apply authorized workarounds, and the earlier override plan added bounded user-direction precedence; the unavailable original run log prevents a precise claim about why that contract was not followed. The related findings concern how the existing search, report, and disposition surfaces are named and used, so this plan clarifies those surfaces without adding another gate or recovery mechanism.

## Gist & Examples

TLDR: make self-heal turn explicit recovery directions into evidence-backed action and stop reports, reducing repeated user direction while improving recovery quality.

Before (today): a user directs self-heal to find a workaround after a refusal. The skill already says to search and apply an authorized route and to report checks performed, but it does not connect those existing directions into one explicit recovery path. The generic project-backlog wording does not name the prompt logs stored at that same backlog location, and the later-stage rule names only a caller disposition even though the existing recovery result can carry it.

After (this plan): self-heal states how its existing search and apply steps follow the user's direction. The existing project-backlog recall explicitly includes prompt logs already stored there. If recovery stops, the existing checks-performed and recovery-result fields make the search and concrete blocker visible; the same recovery result carries later-stage work only when no caller disposition exists.

## Outcome

Self-heal follows explicit recovery directions within existing authority and leaves evidence-backed recovery results that preserve related work.

- A user who asks for a workaround gets an authorized search and action without needing to repeat the direction.
- A terminal stop explains what was checked and what concrete condition prevents continuation.
- Fallback recall includes the project prompt log, and later-stage requirements remain visible when the caller has no disposition.

Gate delta: adds no refusal class, hard gate, fence, protocol layer, separate survey, report field, pause condition, validator, lock, ledger, schema field, or blocking review duty; names the prompt logs within the existing project-backlog recall, the workaround within the existing checks-performed report, and the later-stage fallback within the existing recovery result; removes none.

Follow-up disposition: any additional gap discovered while verifying these four origins is either fixed only when required by their acceptance criteria, or recorded as a new durable backlog item with its evidence and ready-to-dispatch prompt; reject an out-of-scope candidate only with its ruling evidence.

## Assumptions

- assume the exact internal cause of the reported delay is unknown; basis: the first-pass task log is unavailable, and the current skill and completed override plan already direct workaround search, action, and bounded user-direction precedence.
- assume `agents/skills/self-heal/SKILL.md` is the owning change surface; basis: the four origin rows identify its Recovery section and source inspection confirms the described procedures are there.
- assume a backlog row may be closed as already covered only when its expected behavior is demonstrated from the current source and a realistic scenario; basis: the user's direction and the plan lifecycle require an evidence-backed disposition.
- assume the project prompt logs are part of the existing project-backlog search location; basis: both logs are stored under the repository's resolved `backlog_dir`.
- assume the change adds no recovery machinery or search location; basis: the origins ask for clearer use of existing skill surfaces, and no separate validator, gate, or log incident is recorded.
Decision points requiring a grill: all-four scope accepted by the user on 2026-11-20, source: conversation; affected sections: Scope and Tasks

## Standing constraints

- Keep higher-priority requirements, action-specific safety, user authority, existing gates, retry budgets, ownership, and completion boundaries binding.
- Do not infer that a workaround is safe or authorized from the user's broad request alone.
- Balance any operative text growth in the self-heal skill with equivalent deletion in that same file; run its existing byte-budget check.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: an explicit workaround direction leads to a bounded search and authorized action; a real authority, safety, ownership, or evidence blocker still stops recovery.
- Completeness: the existing checks-performed report names the checks already made; project-backlog recall includes prompt logs at that location; the existing recovery result carries later-stage work when no caller disposition exists.
- Evidence integrity: each backlog origin closes only after a realistic scenario demonstrates the expected behavior or the implementation supplies the missing behavior; lack of a reproduction alone never marks an origin obsolete.
- Minimality: edits clarify existing self-heal surfaces without a new survey, report field, pause, or mechanism, and pay any byte growth within that file.

**Done when:**
- Each of the four backlog origins has an evidence-backed implementation or already-covered disposition.
- Realistic self-heal scenarios show the existing search, report, recall, and disposition surfaces handle explicit workaround direction, a blocked stop, prompt-log recall, and later-stage retention with no caller disposition.
- The skill-text budget and public-hygiene checks pass, and the plan completion lifecycle folds the origin dispositions and removes the covered origin rows.

**Ship when:** none.

## Documentation Impact Assessment

- `agents/skills/self-heal/SKILL.md` owns the recovery behavior changed by this plan.
- The four listed backlog origins receive their execution and completion dispositions through the existing plan lifecycle.
- No other documentation source owns or mirrors these Recovery instructions.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production and operative documentation:**
- `agents/skills/self-heal/SKILL.md` (Task 1)

**Backlog origins and completion disposition:**
- `docs/history/backlog/2026-11-20-self-heal-explicit-workaround-not-carried-through.md` (Task 1)
- `docs/history/backlog/2026-11-20-self-heal-premature-stop-without-workaround-evidence.md` (Task 1)
- `docs/history/backlog/2026-11-16-self-heal-fallback-searches-project-prompt-log.md` (Task 1)
- `docs/history/backlog/2026-11-16-self-heal-later-gate-without-disposition.md` (Task 1)

**Read-only recall sources and validation tools:**
- `docs/history/backlog/PLAN-PROMPTS.md` (review-only)
- `docs/history/backlog/EXEC-PROMPTS.md` (review-only)
- `scripts/skill_text_budget.py` (review-only)
- `scripts/scan-public-hygiene.sh` (review-only)

**Tests:** none; this plan changes operative guidance, validated with realistic sample contexts.

**Plan-related extension:** implementation and review may change files not listed above when causally required by a task or to correct a regression introduced by the plan.

**Out of scope; reject unless plan-related:**
- Validators, gates, locks, ledgers, and new logging machinery; reason: the origins call for clearer use of existing recovery steps and the repo's machinery admission protocol requires a separate witnessed failure.
- General instruction-precedence policy outside self-heal; reason: the completed override plan already owns the cross-cutting direction precedence contract.

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
bash scripts/scan-public-hygiene.sh
```

### Task 1: Clarify recovery direction and dispositions

Context surface: the plan's Terms, this task, and Standing constraints; referenced, never restated.

Files:
- `agents/skills/self-heal/SKILL.md`
- `docs/history/backlog/2026-11-20-self-heal-explicit-workaround-not-carried-through.md`
- `docs/history/backlog/2026-11-20-self-heal-premature-stop-without-workaround-evidence.md`
- `docs/history/backlog/2026-11-16-self-heal-fallback-searches-project-prompt-log.md`
- `docs/history/backlog/2026-11-16-self-heal-later-gate-without-disposition.md`
- `docs/history/backlog/PLAN-PROMPTS.md` (read-only source)
- `docs/history/backlog/EXEC-PROMPTS.md` (read-only source)
- `scripts/skill_text_budget.py` (read-only validation)
- `scripts/scan-public-hygiene.sh` (read-only validation)

Primary class anchors:
- `Self-heal` in `agents/skills/self-heal/SKILL.md`

- [x] `Self-heal` carries an explicit workaround direction into its next authorized action: given a user asks for a workaround and repository or tool documentation exposes a safe route, expects self-heal to inspect and apply that route within the existing retry and landing rules without asking the user to repeat the direction. [class: IMPLEMENTATION_REQUIRED]
- [x] `Self-heal` uses its existing stop report accurately: given no safe or authorized route exists, expects the existing checks-performed and evidence-needed report content to identify the search already completed, workaround considered, concrete blocker, next owner or action, without adding a report field or a new check. [class: IMPLEMENTATION_REQUIRED]
- [x] `Self-heal` names the existing project prompt logs within fallback recall: given no caller-named recall procedure and a relevant prior disposition exists in `docs/history/backlog/PLAN-PROMPTS.md` or `docs/history/backlog/EXEC-PROMPTS.md`, expects the existing backlog search to find it before creating a duplicate or asking for direction. [class: IMPLEMENTATION_REQUIRED]
- [x] `Self-heal` reuses its existing recovery result for later-stage work: given the source places a requirement at a later boundary and no caller disposition can hold it, expects the recovery result to preserve the requirement without completing or weakening it and without creating a new state surface. [class: IMPLEMENTATION_REQUIRED]
- [x] Each origin's current behavior is checked with a realistic sample context; an origin already fully covered is closed only with the scenario and source evidence recorded, while a missing behavior receives the smallest text change that satisfies its acceptance criteria. [class: REPOSITORY_TEST]
- [x] Any text added to `agents/skills/self-heal/SKILL.md` is balanced by equivalent deletion in that same file, preserves its authority, safety, gate, retry, and ownership rules, and passes `python3 scripts/skill_text_budget.py --check` and `bash scripts/scan-public-hygiene.sh`. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: clarify self-heal recovery evidence and recall` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-20-self-heal-explicit-workaround-not-carried-through.md`, implemented in `agents/skills/self-heal/SKILL.md` Recovery step 3. Scenario: a user names an outcome and asks for a workaround; self-heal carries that direction into its next authorized action and searches supporting repository or tool documentation without asking the user to repeat it. Existing authority, safety, retry, and landing rules still govern the action.
- `docs/history/backlog/2026-11-20-self-heal-premature-stop-without-workaround-evidence.md`, implemented in Recovery step 5. Scenario: no safe or authorized route is found; the existing stop report states the search already completed, the workaround considered, the concrete blocker, next owner or action, and needed evidence. No report field or check was added.
- `docs/history/backlog/2026-11-16-self-heal-fallback-searches-project-prompt-log.md`, implemented in Recovery step 2. Scenario: with no caller-named recall procedure, the existing backlog fallback can find the relevant `PLAN-PROMPTS.md` and `EXEC-PROMPTS.md` entries before creating a duplicate or asking for direction. The existing unavailable-surface rule remains in force.
- `docs/history/backlog/2026-11-16-self-heal-later-gate-without-disposition.md`, implemented in Recovery step 1. Scenario: when the caller has no disposition surface and a source places a requirement at a later boundary, the existing recovery result carries it forward while authorized work continues, without completing or weakening the later requirement.
