# Backlog: the pre-round executability gate names one failing task per run and never prints per-task totals

- **Filed:** 2026-11-15, closeout capture (learn Step 1.8, skills-corpus)
- **Status:** open
- **Priority:** high
- **Origin class:** session-witnessed producer friction (one plan fold needed several consecutive gate runs)
- **Workflow:** backlog
- **Class:** fix-class (diagnostic output hides the information a producer needs to fix every violation in one pass)
- **Skill and step:** `scripts/plan_readiness.py` pre-round mode (the executability contract: 512-byte item cap, 4096-byte per-task aggregate); the plans skill task-authoring text that cites the caps

## Observed vs expected

Observed: after one fold added acceptance criteria to several tasks, the pre-round gate failed on the first task over a limit and named only that task and that limit class. Fixing it moved the failure to the next task (aggregate), then to a criterion over the item cap, then to another task: about six consecutive runs for one fold. Per-task totals appeared only inside the failure text and only for the first failing task; the measure also differs from raw line bytes by roughly 14 bytes per criterion, which no text states, so local pre-measurement under-estimated the totals.

Expected: one run lists every task over a limit with its measured total and the limit, and every criterion over the item cap, so a producer repairs all of them in one pass. The skill text states what the measure counts.

## Reproduction evidence (trimmed)

1. Add four to six criteria across three tasks of a plan already near the aggregate cap.
2. Run `plan_readiness.py --pre-round <plan>`: one task is named.
3. Repair it and re-run: a different task or limit class is named; repeat.

## Environment

- Playbook skills repo scripts, deployed copy, 2026-11-15; a five-task plan with all tasks near the cap.

## Suspected root area

The executability check returns on its first failing task instead of accumulating. A fail-many accumulation with per-task `total/limit` lines (and an explicit statement of the measure) would remove the iteration.
