---
name: review-plan
description: >
  Review implementation plans for correctness, completeness, and risks. Orchestrates parallel
  sub-agents that analyze different quality dimensions of a plan document. Use when a plan is
  written or updated and needs validation before execution. Trigger phrases: "review the plan",
  "review plan", "check the plan", "validate the plan", "plan review".
---

# Plan Review

## Boundary

Use this skill for **reviewing implementation plan documents** under resolved `{plans_dir}/` (read path keys from `.ai-playbook/facts.md` per `using-skills` Step 0).

Do not use for:
- Reviewing actual code diffs (use `doing-code-review`)
- Creating or editing plans (use `plans`)
- General premortem stress-testing of ideas (use `premortem`)

## When to Run

- After creating or significantly updating a plan
- Before starting execution of a plan
- When asked to "review the plan" or "validate the plan"

## Step 1: Load Plan and Context

1. Read the plan file in full
2. Identify all source files referenced in the plan (from Review Scope, Task file lists)
3. Read key referenced source files to understand current code shape (function signatures,
   data structure definitions, pipeline order, return types)
4. **Existing-method modification audit**: for every existing method the plan modifies, compute
   pre-change line count and the new line count implied by the planned edits. Flag any
   post-modification method that would exceed repo complexity limits (cyclomatic, nesting depth,
   line length; see repo-specific overrides in Step 2 item 5). New methods get audited by the
   relevant agent; modifications to existing methods are easy to miss otherwise.
5. **Replacement / supersession map**: list any new class, enum, method, or table the plan
   introduces that overlaps in purpose with existing code (e.g. a new policy enum that supersedes
   a static-constants class). For each, check whether the plan also deletes the original or
   justifies retention. Unaddressed supersession is a finding for the simplification agent.
6. **Plan-closure matrix**: for every changed or new production file, migration resource, test,
   documentation artifact, and validation command named in a task, verify the same work is present
   in the task's Files list, the global Review Scope, the implementation step, and that each named
   test runs in its owning task gate. Report any mismatch as implementation, testing, documentation,
   or consistency finding according to the missing element.

## Step 2: Launch Sub-Agents in Parallel

Read `review-agents/review-panel-selection.md` for the default 8-agent plan panel (7 shared plus inline consistency) and conditional `concurrency` / `premortem` launch. Record `Domains:` in staging metadata.

Launch ALL selected review agents simultaneously using your agent's parallel execution capability
(e.g., background execution mode, parallel sub-agent launch, or equivalent mechanism).
Wait for all agents to complete before proceeding.

Each agent receives:
1. The full plan content
2. Relevant source file excerpts (signatures, data structure definitions, pipeline structure)
3. Its specific review lens from `~/.agents/skills/review-agents/<agent>.md` (or the repo-vendored copy under `agents/skills/review-agents/<agent>.md` when present)
4. The project's CLAUDE.md content (for repository conventions)
5. **Repo-specific overrides take precedence**: if `CLAUDE.md`, `{guidelines_path}` (from `.ai-playbook/facts.md` TOML when present; typically `docs/maintenance/project-guidelines.md`), or any loaded company/project guideline defines complexity, naming, comment, or layering rules that conflict with the generic pattern catalog, the agent MUST apply the repo-specific value, not the catalog default. Example: catalog says "functions >50 lines" but `company-guidelines.md #17` says "≤30 lines per method"; apply the 30-line rule.
6. **Execution framing**: "You are reviewing an IMPLEMENTATION PLAN, not a code diff. Read the plan tasks and the referenced source files to understand what is being proposed. Apply your pattern catalog to identify whether the proposed changes would introduce the issues you are responsible for detecting."
7. **Output format**: for each finding provide `{location_in_plan, issue, severity: Critical/Suggestion/Advisory, fix, evidence}`; no `path/line/side` fields (those are for code review). **`issue` and `evidence` must be self-contained**: name the plan task, quote or paraphrase the contradicting plan text, cite what the referenced source file shows, and state the concrete fix. Do not return stubs the orchestrator must research.

### Shared agents (from `~/.agents/skills/review-agents/`)

| Agent file | Focus in plan context |
|---|---|
| `quality.md` | Will the proposed algorithm produce correct results? Data type/API assumption errors? |
| `implementation.md` | Missing wiring, return value propagation gaps, backward compatibility holes |
| `architecture.md` | Would the proposed design introduce SOLID violations, layer crossings, god classes? |
| `testing.md` | Are the described tests sufficient? Could a test pass even if the implementation is wrong? |
| `simplification.md` | Is the planned approach over-engineered for the problem? |
| `documentation.md` | Missing docs for user-visible changes; redundant or verbose plan prose (two-phase agent) |
| `security.md` | Would the proposed changes introduce security vulnerabilities? |
| `concurrency.md` | Would the proposed changes introduce race conditions or transactional scope issues? |
| `premortem.md` | Design-level failure modes; "it shipped and failed; why?" |

### Plan-specific agent (inline; no shared file)

#### Consistency Agent

```
Review this implementation plan for internal contradictions and alignment issues.

Check:
1. Design invariants vs task descriptions: Does any task step violate a stated
   design invariant? Are invariants complete (missing guards)?
2. Test expectations vs implementation: Do tests expect behavior X while the
   implementation description says Y?
3. Cross-task coherence: Does Task N produce output that Task M expects in the
   right format? Are intermediate states valid?
4. Naming consistency: Are the same concepts named identically across tasks?
   (e.g., function names, field names, parameter names)
5. Commit boundaries: Can each commit compile independently? Does splitting
   across commits create broken intermediate states?
6. Stale references after restructuring: After any renumber, file-move, package-change,
   or path change in the plan, scan ALL file paths AND all task cross-references
   (e.g. "Tasks 1–N", "see Task M") for staleness. A path that still says `domain/`
   after the file moved to `application/`, or a "Tasks 1–7" reference after the plan
   grew to 10 tasks, must be flagged.
7. Evaluation Criteria substance: Does the plan's Evaluation Criteria section contain
   specific, verifiable criteria (e.g. "API returns 404 for unknown IDs", "batch completes
   within 5s at 10k records")? Vague criteria like "it should work" or "tests pass" must
   be flagged as a Suggestion finding.

For each finding, provide:
- The two contradicting statements (with task numbers)
- Which one is correct (based on source code and domain rules)
- Severity: Critical / Suggestion / Advisory
- Evidence: what was read in source files or plan text that supports the finding
- Suggested resolution

**Ownership (tiered):** report Design Invariants / Glossary vs Task contradictions and cross-task alignment only. Do not report source-code algorithm bugs (quality), missing tests (testing), or wiring gaps (implementation). Invariant-vs-task contradictions stay here even when they sound like quality bugs. See `review-panel-selection.md`.
```

## Step 3: Synthesize Findings

After all sub-agents complete, **synthesize from agent returns only**; do not re-read source files or re-analyze the plan in the orchestrator context. The orchestrator dedups, ranks, formats, and **records Review Statistics** per `review-staging`; sub-agents already did the reading and reasoning.

1. **Deduplicate**: Merge findings that describe the same root issue from different angles. Apply tiered ownership from `review-panel-selection.md` to pick the lead agent; do not discard a different fix at the same site. Record each merge in **Deduplication groups** (all contributing agents, staged finding number).
2. **Rank by severity**:
   - **Critical**; blocks execution
   - **Suggestion**; should add safeguard, test, or step to plan
   - **Advisory**; monitor-level note or optional improvement
3. **Cross-reference with plan**: For each finding, note whether the plan already
   addresses it (and mark as "Already mitigated" if so). Discarded mitigated items go in **Discarded findings** with reason `already-mitigated`.
4. **Incomplete agent output**: if a finding lacks `evidence` or a concrete `fix`, relaunch that agent focused on the gap; do not fill it inline. Failed relaunches: Panel Status `failed` or `timeout`, discards use `agent-failed` or `insufficient-evidence`.
5. **Record statistics**: populate full `## Review Statistics` per `review-staging` (Panel with Solo/Echo, Counts, Deduplication groups, Discarded with Pattern, Severity calibration, Triage placeholder) before writing `## Findings`. Write the matching `.stats.json` sidecar in the same pass.

## Step 4: Output

Write the review to `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md` and `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.stats.json` (read `{reviews_dir}` from `.ai-playbook/facts.md` TOML; use `-r1`, `-r2`, … per loop iteration). Follow the staged hierarchy and **Review Statistics** section from `review-staging` (gold source).

```markdown
# Plan Review: <Plan Title>

## Metadata
- Type: Plan Review
- Date: YYYY-MM-DD
- URL or Artifact: `{plans_dir}/<filename>.md`
- Depth: light | full *(when applicable)*
- Domains: concurrency, SQL *(when known)*
- Round: r1
- Prior: `{reviews_dir}/<prior-rN>.md` *(omit on r1)*
- Findings: <staged count>
- Status: STAGED

## Review Statistics

### Panel
| Agent | Status | Raw | Solo | Echo | Relaunch |
|-------|--------|-----|------|------|----------|
| quality | complete | 0 | 0 | 0 | no |
| consistency | complete | 1 | 1 | 0 | no |

### Counts
- Agents launched: 12
- Agents skipped: 0
- Raw findings (all agents): 3
- Staged findings: 2
- Discarded during synthesis: 1
- Solo staged (unique agent origin): 1
- Echo staged (multi-agent dedup): 1

### Deduplication groups
| Staged # | Agents | Theme |
|----------|--------|-------|
| 1 | quality, concurrency | Missing guard on concurrent delete |

When none: `None (each staged finding had a single agent origin).`

### Discarded findings
| Agent | Agent severity | Pattern | Theme | Reason | Notes |
|-------|----------------|---------|-------|--------|-------|
| documentation | Advisory | documentation#glossary | Add glossary link | already-mitigated | Plan Review Scope lists glossary |

When none: `None.`

### Severity calibration
| Staged # | Agent | Agent severity | Staged severity | Delta |
|----------|-------|----------------|-----------------|-------|

When none: `None (agent severities matched staged severities).`

### Triage outcomes
Pending triage. *(After Step 5 plan fold: set Fixed for folded Blocker/Medium, Deferred for Monitor-only, Dropped for rejected findings.)*

## Findings

### 1. <short title>
- **Severity**: Critical | Suggestion | Advisory
- **Agent severity**: Suggestion *(omit when equal to Severity)*
- **Pattern**: quality#concurrent-access
- **Agents**: quality, concurrency
- **Triage**: pending
- **Anchor**: Task N, bullet M (plan section heading or nearby prose anchor)
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<Self-contained, suggestion-tone explanation of the issue and the concrete change to the plan.>

#### Analysis (not posted)
<Originating agent (quality | implementation | architecture | testing | simplification | documentation | security | concurrency | premortem | consistency), what the referenced source code shows, and severity rationale.>

---

### 2. <short title>
- **Severity**: Critical | Suggestion | Advisory
- **Pattern**: implementation#wiring-gap
- **Agents**: implementation
- **Triage**: pending
- **Anchor**: <plan section heading or nearby prose anchor>
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<...>

#### Analysis (not posted)
<...>
```

## Step 5: Amend Plan

After writing the review document:

1. For each finding with **Severity: Critical**: fold into the plan as a **Blocker** (update the affected plan task directly; mandatory before next review round)
2. For each finding with **Severity: Suggestion**: fold into the plan as a **Medium** (update tasks, invariants, tests, or Review Scope; mandatory before next review round)
3. For each finding with **Severity: Advisory**: fold into the plan as a **Monitor** (add/update the plan's `## Monitor` section with named owner)
4. Add a reference line to the plan header: `Plan review: {reviews_dir}/<latest-rN>.md (latest, ready) · …`
5. If the plan has a final validation task, add verification commands for each Blocker/Medium finding (Critical/Suggestion only)
6. Update each finding **Triage** and `## Review Statistics` → **Triage outcomes**: `fixed` for folded Critical/Suggestion, `deferred` for Monitor-only Advisory, `dropped` for findings rejected during fold

Note: older plan review artifacts may use the prior Blocker/Medium/Low/Monitor vocabulary. This skill now uses staged severities (Critical/Suggestion/Advisory) plus the Step 5 mapping into plan actions (Blocker/Medium/Monitor).

Report to user:
> "Plan review r<N> complete: B blockers, M medium (fixed in plan), Mon monitor.
> Review saved to `{reviews_dir}/<filename>-r<N>.md`.
> Ready for execution: Yes/No (requires Blocker=0 and Medium=0)."

## Iteration Discipline (plans skill gate)

When the user asks to run reviews until clean (e.g. "no medium problems", "until ready", "keep review loop until gates are met", "don't ask anymore"):

0. **No mid-loop re-prompt:** once the user has directed continuous review until the quality gate, do **not** ask execute-plan / continue / another round between iterations. Fold Critical/Suggestion, write the staging doc, and immediately launch the next round until the exit condition holds (or the five-cycle reconciliation gate fires).
1. **Exit condition and minimum rounds:** see `plans` skill Plan Quality Gate (Blocker=0 AND Medium=0, minimum two rounds).
2. **Severity alignment:** agents emit Critical/Suggestion/Advisory. Step 5 defines how to fold these into plan actions (Blocker/Medium/Monitor).
3. **Treat a clean review as data, not as a terminal verdict.** A 0 Blocker / 0 Medium outcome can mean either (a) the plan is correct, or (b) the agent catalog lacks patterns to detect defects. Run the self-audit below before stopping after only one round.
4. **Run a brief self-audit alongside the agent review.** Before declaring iteration complete, scan the change types introduced by the latest plan revision (new domain types, decomposed methods, replaced classes, modified existing methods, restructured tasks) and verify the catalog has an active pattern for each. If a change type has no corresponding pattern in your review-agent prompts (often under `~/.agents/skills/review-agents/*.md`, and sometimes vendored under `agents/skills/review-agents/`), the agents cannot detect defects of that class. **Also list every "inherited/validated/tested/unchanged" claim in the plan and confirm the panel re-probed each by measurement** (see Signal-to-Noise: Inherited/validated claims are claims, not proof). A clean round that did not re-probe the plan's "settled" mechanisms is not evidence those mechanisms are correct.
5. **Catalog gap discovered → update the skill before re-iterating.** If the self-audit identifies a missing pattern (e.g. "no agent owns 'type-boundary discipline'", "no agent enumerates switches", "no agent checks for superseded code"), add the pattern to the relevant agent file FIRST, then re-run the review. Patching the plan around a catalog gap leaves the gap for future plans.
6. **Stop when both conditions hold**: the latest review reports Blocker=0 AND Medium=0 (minimum two rounds completed) AND a self-audit against the change types in the plan finds no additional concerns the catalog would have missed.
7. **Record self-audit gaps as catalog improvements**, not as one-off plan patches. When the self-audit found something the catalog missed, the fix is two-part: patch the plan AND update the agent file or `SKILL.md`. The catalog improvement is the persistent gain; the plan patch is local.

## Five-Cycle Reconciliation Gate

When a user asks for repeated review-and-amend cycles, count one review-fix cycle only after a complete staged review has been triaged and every valid Critical/Suggestion finding has been amended into the plan. Do not run an unbounded loop.

After five consecutive non-clean cycles since the last reconciliation, stop automatic review launches and run a **plan reconciliation** before a sixth review:

1. Read the five staged review artifacts and their JSON sidecars.
2. Cluster findings by root cause, including findings fixed in earlier cycles, rather than treating each wording variation as a new issue.
3. Distinguish an omitted local safeguard from an intrinsic plan weakness such as an unclear state machine, split source of truth, incomplete ordering protocol, overloaded migration, or boundary ambiguity.
4. Update the plan's Terms, Gist, Design Invariants, task decomposition, and tests when the correction is within the approved architecture. Update the relevant review-agent catalog when the five-cycle record exposes a detection gap.
5. If reconciliation requires a material architectural, scope, or rollout decision, stop and present the concrete options to the user. Do not assume permission to redesign the plan.
6. Record the reconciliation result in the next staged review artifact or a linked review note, reset the five-cycle counter, and then resume the normal two-clean-round readiness gate.

A user may set a smaller cycle cap. When they do, run the same reconciliation at that cap. A clean round still requires the normal minimum two complete clean rounds; it does not reset a non-clean-cycle count by itself.

## Signal-to-Noise Rules

Adapted from `doing-code-review`:

- **Report problems only.** No positive observations or praise.
- **No vague concerns.** Every finding must name specific components, data flows, or functions.
- **Skip findings the plan already addresses.** Read the full plan (including Design Invariants)
  before generating findings. This applies to *specific prior findings that were mitigated* -
  NOT to mechanisms the plan merely *asserts* are proven (see the next rule).
- **Inherited/validated claims are claims, not proof.** When a plan says a mechanism is
  "inherited," "validated by prior rounds," "already tested," "unchanged from a prior phase,"
  or "gate-core inherited," treat that phrasing as a flag to RE-VERIFY the mechanism, not as a
  reason to skip it. The areas a plan declares settled are precisely where latent defects hide
  unchallenged (a prior review declaring "X is tested" discourages the next panel from
  measuring X). Re-probe by exercising the mechanism against the real artifact it operates on,
  not by re-reading the plan's assertion.
- **Measure the real artifact, don't just re-assert the plan's claims about it.** When a plan
  operates on a real file, schema, config, or API (a parser over a corpus, a migration over a
  dataset, a loader over a config), run at least one structural measurement of that artifact
  that the code's correctness depends on - fence-marker parity, key uniqueness, encoding,
  delimiter/count parity, nullability - beyond re-asserting the counts the plan states. Reading
  the source is necessary; measuring the property the code relies on is the verification.
- **Agent empirical assertions are claims, not measurements.** A review agent may state a
  runtime fact (an exception type, a return shape, an encoding or serialization outcome) with
  measured-sounding confidence without having executed it. When a finding turns on such an
  assertion, re-run the one-line reproduction yourself before folding the finding: agents
  regularly invert language semantics, and a false assertion reads identical to a true one.
  Shape witnessed this session: two agents asserted `json.dumps({"k": b"x"}, default=str)`
  raises; an empirical check showed it succeeds (`default=str` degrades `bytes`), and the real
  residual vectors were circular-reference and `__str__`-raising.
- **No markdown formatting nitpicks** on the plan document itself (heading levels, list style). Redundant or verbose plan prose is owned by `documentation.md` phase 2.
- **Evidence-gated findings:** correctness claims must be backed by reading the actual source
  file. Do not assume; verify.
- **2-3 findings max per agent.** Quality over quantity. If an agent finds nothing credible,
  it reports "No findings."

## Integration Points

### With `review-staging` skill
Writes `{reviews_dir}/YYYY-MM-DD-plan-review-<slug>-r<N>.md` and the matching `.stats.json` sidecar. Follow `review-staging` for hierarchy, required `## Review Statistics`, and naming. Read `{reviews_dir}` from `.ai-playbook/facts.md` TOML.
