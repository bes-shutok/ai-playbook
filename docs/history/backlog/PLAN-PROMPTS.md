Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.

Standing rules:

- Order: entries sit most-urgent-first; a new entry inserts at the urgency position it merits, judged when it is written.
- Prune rule: an entry is removed when its plan file exists in the plans root.
- Freeze rule: when authoring for an entry has started (a live authoring claim file keyed to the entry slug or one of its origins under the tmp authoring-claims directory, live meaning its `updated:` fresher than one cadence period per the `G1a` discovery arm's bound (a stale claim taking the takeover path instead of freezing), or a live authoring worktree or branch for its plan), the entry is marked frozen before any further log processing: a `Frozen:` line naming the witness and date goes directly under the entry's heading. A frozen entry accepts no origin additions, no prompt rewrites, no repositioning, and is never a dispatch candidate; the mark is removed when the authoring aborts without a plan file in the plans root (the entry reopens), and the entry is pruned outright per the prune rule when its plan file lands.
- Not a backlog item: never cite this file as a plan's Backlog origin.
- Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.
- Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.
- Every log write is committed in the same turn that performs it.
- Entries carry repo-relative paths only and no personal or machine-specific data.
- An entry is a prompt for a later authoring turn; the write turn never executes or dispatches its payload.

Entry template (one section per entry):

```
## <short-slug>

Added: <date and provenance>

Origins:
- docs/history/backlog/<origin>.md

Urgency: <judgment: class, witness, relative queue position>

Prompt: <full ready-to-dispatch authoring prompt payload>

Rejected alternatives:
- <one line per rejected alternative, with the reason>
```

## script-outcome-contract

Added: 2026-10-02, anchored investigate pass on the operator-filed origin (user-request class, filed 2026-10-02 minutes after the same-day dirt-gate known-case fix landed); same-day operator direction widened the scope to operating-context assumptions for all decision-making scripts, recorded in the origin's Expected section.

Origins:
- docs/history/backlog/2026-10-02-script-indeterminate-results-and-agent-escalation.md

Urgency: high, fix-class user-request riding a fresh witnessed incident: an agent followed the dirt gate's REGRESSION result and stopped closeout on moved imports and lines before the known-case fix 46a91c91 landed, and the structural residual stands: unmodeled classifier shapes still exit 0 PASS silently (in scripts/dirt_regression_gate.py a partial or malformed diff yields no hunks and is indistinguishable from a clean tree), so the next unmodeled shape can pass unsafe work with no signal.

Prompt: Author a plan that defines a shared outcome contract for ai-playbook scripts that classify or gate agent work (pass; fail with the offending evidence identified; indeterminate, reporting what was observed and what could not be determined; tool error, never represented as a pass or a domain finding), and migrates the highest-risk scripts first. Scope arms: (1) inventory the decision scripts (scripts/dirt_regression_gate.py, scripts/done-lock.sh, scripts/done_sweep_gates.sh and scripts/done_sweep_gates_lib.py, scripts/landing_parentage_gate.py, scripts/check_plan_origins_closed.py, scripts/plan_readiness.py, scripts/validate_review_staging.py, scripts/check_maintenance_pins.sh, the public-hygiene scan, and their siblings) and rank them by the consequence of a wrong classification and by how easily their operating-context assumptions are violated in use; (2) define the machine-readable outcome shape (an exit-code and output convention or a shared result type, with a documented compatibility adapter that preserves old behavior only for explicitly classified known cases), keeping each script's domain criteria explicit, and require each script to declare the operating-context assumptions its result depends on (repository root and checkout context, branch or lock state, input presence and freshness, invocation outside the modeled context) so an unheld assumption surfaces as tool error or indeterminate, never as a domain pass or fail; (3) migrate scripts/dirt_regression_gate.py first: its known-case behavior from 46a91c91 stays deterministic, the unmodeled-shape arm becomes an explicit indeterminate outcome instead of a silent PASS, and its agent-facing callers (the closeout Validation block in agents/skills/done/SKILL.md and the recipes in agents/skills/maintenance/prompt-templates.md) branch explicitly on every outcome and hand the evidence back to the agent when a decision is required; (4) per updated script add fixtures for established pass/fail cases, boundary cases, malformed or unsupported input, mixed evidence, and at least one previously unmodeled shape; (5) record the caller-obligation rule where the skills own it (an agent must not treat indeterminate or tool error as pass/fail, nor continue a dependent destructive or landing action on that result) without silently widening any classifier's pass or fail rules to make an unexpected case fit. Authoring constraints: fix-class machinery growth, so the plan's Gate delta line prices the outcome-contract addition on the witnessed incident as its recorded-failure witness per the machinery delta doctrine (docs/history/plans/completed/2026-09-29-plans-machinery-delta-doctrine.md); known cases keep deterministic behavior and escalation is for uncertainty, never a substitute for implementing expected cases; the sibling origin docs/history/backlog/2026-10-02-project-configurable-worktree-policy.md (dispatch checkout selection) is out of scope here.

Rejected alternatives:
- Remove the gate and rely on agent judgment: rejected, the gate is landed load-bearing machinery with a machinery-registry entry, pins, and done-skill integration, and it caught the squash-clobber family (witnessed 2026-09-30 repair 455ed9ec).
- Keep the binary contract and keep patching known cases per incident: rejected as the whole answer, every unmodeled shape would need its own incident first, and the post-fix residual still silently passes malformed or partial diffs (witnessed 2026-10-02, fixed same-day by 46a91c91 for its two known shapes only).
- Skill-text-only fix teaching agents to distrust gate results and re-derive from disk: rejected, prose cannot tell a modeled certainty from an unmodeled guess per script, and the incident agent followed the documented closeout discipline and still failed when the gate's own result was the wrong part (witnessed 2026-10-02, origin Problem section).
- Pins-suite change as the primary mechanism, requiring an indeterminate arm through gate needles: rejected as primary because pins assert text presence rather than semantics, a pins row may ride along only after the contract exists (witnessed pins role in scripts/check_maintenance_pins.sh).
- Big-bang rewrite of every decision script in one pass: rejected on the origin's own scope warning, different result formats and risk levels need a ranked staged migration so no consumer keeps interpreting uncertainty as pass/fail (witnessed origin Why-not-fixed-now section, docs/history/backlog/2026-10-02-script-indeterminate-results-and-agent-escalation.md).
