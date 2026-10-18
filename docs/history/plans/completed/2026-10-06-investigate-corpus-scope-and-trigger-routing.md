# Plan: investigate corpus-scope arm and workflow-verb routing

Backlog origin: docs/history/backlog/2026-10-04-investigate-workflow-skill-lookup-miss.md
Driving force: consistency (outside the closed taxonomy and not one of the five driving principles; justification: the corpus ask must resolve to the owning skill's contract exactly as a single-item ask does, witnessed by the three-correction miss and the gate's 17-violation bypass; park-triage would take it on wording alone, and the routing lands now because the miss is witnessed rather than hypothetical)
Plan review record: the staging series docs/reviews/2026-10-06-plan-review-investigate-corpus-scope-and-trigger-routing-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- corpus-level ask: an operator investigate ask whose object is the whole backlog corpus ("investigate the backlogs", "investigate all backlog items") rather than one item or a small related set.
- corpus roster: the Stage 0 cluster survey's group roster, which for a corpus-level ask doubles as the enumeration of what the pass investigates (an ungrouped open item counting as its own single-origin group).
- workflow verb: an operator verb that names a first-party workflow (investigate, author, execute, review, triage, release); the routing duty is resolution to its owning skill where the catalog carries one.
- owning skill: the skill whose stages, gates, and artifact contract own the named workflow; resolution is one catalog read.
- entry-count rule: one pass over a corpus-level ask emits one entry per investigated group, the entry count being the group count, not one per pass.

## Why

Three operator corrections were spent on a corpus-level investigate ask before the skill's contract ran: the session never opened the skill, improvised an ad-hoc pass, crossed the never-execute hard gate, and only a third message produced log entries that bypassed the pipeline (17 gate violations, repaired same-pass). Two repo-side gaps make recurrence real for any agent: the skill's stated scope is one item or a small related set with no corpus-scope arm, and its trigger phrases live only inside the skill's frontmatter with no workspace-instruction surface routing a bare corpus investigate ask to it.

## Outcome

A corpus-level investigate ask resolves to the skill and executes its contract as written: the skill states the corpus-level invocation, and the workspace instructions route every workflow verb to its owning skill before any improvised pass.

- `agents/skills/investigate/SKILL.md` states the corpus-level invocation: the Stage 0 cluster survey doubles as the corpus roster, the pass emits one entry per investigated group, and the per-turn single-investigation bound stays the maintenance scheduler's binding and never a skill bound; the description's trigger phrases gain the corpus form.
- The repository `AGENTS.md` gains the workflow-verb routing section, and the tracked `CLAUDE.md` twin carries the same section to the sessions that load it: an operator verb that names a workflow resolves to its owning skill under `agents/skills/` before any improvised pass, the catalog check being one file read.
- Gate delta: grows the investigate skill's checked-condition set (the corpus-level invocation) and the workspace instructions' routing surface (the workflow-verb line); no refusal class, hard gate, fence, protocol layer, or schema state field is added, and nothing is removed. Priced by the witnessed three-correction miss recorded in the origin row, re-derived from the row's three-message narrative and the gate's witnessed 17-violation bypass.

## Assumptions

- assume the corpus-arm semantics are one-pass-many-entries (the entry count is the group count), not iterate-per-group across turns: basis: the origin row records both readings and dispatches the adjudication to this authoring pass, the Stage 0 survey already enumerates the groups in one sweep so the roster exists before any entry is written, and the scheduler's per-turn bound is explicitly a scheduler binding the skill text does not own.
- assume the routing line lands in the repository `AGENTS.md` as its own short section rather than inside the scheduling verb-contract section: basis: the scheduling section's topic is automation asks specifically, while the routing rule covers every workflow verb, and a sibling heading keeps both verb contracts discoverable; the same section appends to the tracked `CLAUDE.md` twin so the routing reaches the sessions that load it.
- assume `scripts/check_investigate_entries.py` is never edited: basis: the origin's suggested fix shape keeps the gate as the standing verification (it witnessed the bypass live), and the plan adds no log entries, so the gate's contract is untouched; it runs green over the whole log as a whole-plan gate.
- assume the trigger-phrase addition is frontmatter description text only: basis: the phrases live only in the description (the origin's receipt), and the corpus-scope semantics live in the body, so the two surfaces keep their existing division; the origin's second corpus phrase (investigate all backlog items) is covered by the routing line and deliberately not added to the description.
- assume the description's and Purpose line's singular-entry phrasings stay under the freeze although the corpus clause supersedes them for corpus asks: basis: the inserted clause sits immediately after the Purpose paragraph and restates the entry-count rule, so a full read resolves the contract, and widening the frozen sentences would churn pinned frontmatter for wording alone.
- assume the README and agent-runtime-layout catalog rows stay untouched by this plan: basis: the rows describe the artifact shape (a tracked rolling-log entry), which the corpus arm does not change, while the rows' singular per-pass count wording ages the same way the skill's own singular phrasings do, deferred with them through the standing catalog workflow at its next touch.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: A corpus-level investigate ask runs the skill's own contract, and every workflow verb routes to its owning skill before improvisation (consistency).

**Before (today):** "Investigate the backlogs" pattern-matches the noun to the backlog corpus: the stated scope covers one item or a small set, so the ask sits outside the letter of the skill, no surface routes the verb, and the session improvises past the skill's gates until corrected three times.

**After (this plan):** The skill states the corpus-level invocation (Stage 0 doubles as the roster, one entry per group, the per-turn bound stays the scheduler's), the description carries the corpus trigger phrase, and `AGENTS.md` and the tracked `CLAUDE.md` twin route every workflow verb to its owning skill in one catalog read.

Edge cases: a corpus ask still skips foreign-origin and already-investigated items per the Stage 0 ownership and skip rules; an open item the survey leaves ungrouped is its own single-origin group under a corpus ask; the scheduler turn keeps dispatching at most one investigation per turn regardless of the skill's own entry-count rule; a verb with no owning skill falls through to ordinary context gathering (the routing line carries the fall-through in its shipped text).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the gate script exits 0 over the whole log on the executed tree; the added trigger phrase appears in the description and the corpus-level invocation in the body.
- regression safety: the pins suite stays green; the em-dash added-lines scan and the hygiene scan report no findings.
- scope discipline: the gate script is untouched; the routing line adds resolution duty without a hard refusal arm.

**Done when:**
- `( cd "$REPO" && python3 scripts/check_investigate_entries.py )` exits 0.
- The full Validation Commands block exits 0 on the executed tree.

**Ship when:**
- The next corpus-level investigate ask opens the skill and runs its contract as written, and the next workflow verb resolves through the routing line; both are routine-turn behaviors requiring no further human action in this repository beyond the executed tree.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/investigate/SKILL.md` (the corpus-level invocation clause in the body and the corpus trigger phrase in the description; all other sections are frozen)
- `AGENTS.md` (the workflow-verb routing section; all other sections are frozen)
- `CLAUDE.md` (the appended workflow-verb routing section; the file is a known-stale twin of the Repository Guidelines and its other sections are frozen)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/check_investigate_entries.py`; reason: the gate is the standing verification and the origin's fix shape keeps it untouched.
- `README.md` and `projects/.ai-playbook/agent-runtime-layout.md` catalog rows; reason: the rows describe the artifact shape (a tracked rolling-log entry), which the corpus arm does not change; the catalog wording updates through the standing catalog workflow at its next touch (recorded in the assumptions).
- `docs/history/backlog/PLAN-PROMPTS.md`; reason: the plan adds no log entries; the queue entry's own lifecycle is the landing rider.
- the agent-conduct half of the origin (session-side skill-lookup discipline); reason: the origin records it as standing session discipline needing no repo text.

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the plan bytes passed the pre-round gate with exit 0 and `OUTCOME: pass` in the authoring worktree; the rule 19 RED-today probe ran each pinned span with grep against its owning target (the new-duty spans returned no match; the preserved spans matched); the rule 22 mechanical audit verified every pinned span occurs exactly once in its owning prescribed snippet (rule 36 mirrors included; the preserved spans matched against the current target bytes) and `bash -n` accepted the Validation Commands block. Round-start state for r3: authoring worktree ai-playbook-wt-icsc, branch 2026-10-06-investigate-corpus-scope-and-trigger-routing, plan bytes at the r2 fold commit.

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && python3 scripts/check_investigate_entries.py )
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base main )
( cd "$REPO" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
```

### Task 1: Corpus-level invocation and workflow-verb routing (GREEN)

Files:
- `agents/skills/investigate/SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`

Evidence:
- `( cd "$REPO" && python3 scripts/check_investigate_entries.py )`; covers the untouched-gate criterion: the validator exits 0 over the whole log after the skill-text edits
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )`; covers the pins-reconciliation criterion: no pin row's literal broke

- [x] In `agents/skills/investigate/SKILL.md`, extend the description's trigger phrases with the corpus form: after the existing phrase `\"prepare a plan-creation prompt\"` inside the frontmatter description, insert `, \"investigate the backlogs\"` so the quoted trigger list ends with the corpus form [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/investigate/SKILL.md`, insert the corpus-level invocation paragraph into the body immediately after the Purpose line's paragraph (the paragraph beginning the unique span `**Purpose:** pre-authoring investigation for one open backlog item or a small set of related items`), as a new paragraph separated by blank lines on both sides, reading exactly: [class: IMPLEMENTATION_REQUIRED]

```markdown
**Corpus-level invocation:** an ask whose object is the whole backlog corpus runs this skill's contract over the corpus: the Stage 0 cluster survey doubles as the corpus roster, the pass emits one entry per investigated group (the entry count is the group count, not one per pass), an open item the survey leaves ungrouped is its own single-origin group under the same contract, and the per-turn single-investigation bound stays the maintenance scheduler's binding and never a skill bound; the Stage 0 ownership and skip rules apply to every group exactly as they do to the anchored pass.
```

- [x] In `AGENTS.md`, insert the following section immediately before the `## Scheduling asks (verb contract)` heading (the heading is the unique anchor; the new section sits directly above it, separated by blank lines on both sides): [class: IMPLEMENTATION_REQUIRED]

```markdown
## Workflow verb routing

An operator verb that names a workflow (investigate, author, execute, review, triage, release) resolves to its owning skill under `agents/skills/` before any improvised pass: consult the skill's own `SKILL.md` for the verb, and run its stages, gates, and artifact contract as written; a verb with no single owning skill proceeds by ordinary context gathering; the resolution check is one file read.
```

- [x] In `CLAUDE.md`, append the same `## Workflow verb routing` section (the identical markdown block as the AGENTS.md insertion above) at the end of the file, separated from the final line by a blank line; `CLAUDE.md` is a tracked stale twin of the Repository Guidelines (last synced at c64ce112, missing the Scheduling section and later bullets), and this append carries the routing rule to the sessions that load it; future edits to the routing section edit both files in the same change (the two copies are hand-synced by duty) [class: IMPLEMENTATION_REQUIRED]

- [x] Run → expect GREEN: `( cd "$REPO" && python3 scripts/check_investigate_entries.py )` exits 0; the pins suite exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `feat: investigate corpus-level invocation and workflow-verb routing line` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Full validation

Evidence:
- The full `## Validation Commands` block; covers every Done-when criterion on the executed tree

- [x] Run → expect GREEN: the full Validation Commands block exits 0 line by line; the em-dash added-lines scan and the hygiene scan report no findings on the changed files [class: REPOSITORY_TEST]
- [x] Verify span uniqueness: for each new-duty span introduced by this plan, `grep -cF` over its owning file returns exactly 1 after the edits (`investigate the backlogs` in `agents/skills/investigate/SKILL.md`; `one entry per investigated group` in `agents/skills/investigate/SKILL.md`; `Workflow verb routing` in `AGENTS.md`; `Workflow verb routing` in `CLAUDE.md`), and for the preserved spans it returns at least 1 (`**Purpose:** pre-authoring investigation for one open backlog item or a small set of related items` in `agents/skills/investigate/SKILL.md`; `\"prepare a plan-creation prompt\"` in `agents/skills/investigate/SKILL.md`; `## Scheduling asks (verb contract)` in `AGENTS.md`) [class: REPOSITORY_TEST]
- [x] Run the readiness gate over this plan; expect exit 0 with `OUTCOME: pass` at the certification boundary [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-06 in worktree ai-playbook-wt-ics (branch plan-investigate-corpus-scope-exec) by the standing maintenance execution lane. Task 1 (fec506cc): the investigate skill's frontmatter description ends with the corpus trigger phrase, the verbatim Corpus-level invocation paragraph lands between the Purpose paragraph and Boundary naming Stage 0's survey as the corpus roster with one entry per investigated group and ungrouped open items as their own single-origin groups; the workflow-verb routing section lands verbatim in AGENTS.md directly above the Scheduling asks section and as a byte-identical twin appended to the tracked CLAUDE.md.

Validation: check_investigate_entries.py exit 0 (5 entries, 0 violations); pins suite exit 0; em-dash added-lines scan and hygiene scan exit 0; span uniqueness holds including the TOML-escaped quoting form (the plan's Task 2 span-check line omitted the escapes; the escaped on-disk bytes exist exactly once). Exec review r4 (fresh-adversarial, one worker) found zero findings with one informational plan-priced note (the triage verb rides the fall-through arm as the plan's edge case prescribes); records at docs/reviews/2026-10-06-plan-review-investigate-corpus-scope-and-trigger-routing-r4.{md,stats.json} plus the r5 certification probe.

Deferred residuals: none. Origin row docs/history/backlog/2026-10-04-investigate-workflow-skill-lookup-miss.md is covered by this execution and folded in the landing.
