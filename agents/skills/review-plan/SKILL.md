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

## Plan-review boundary

This skill establishes implementation readiness, not implementation completeness. Block only when the plan leaves public behavior contradictory, an invariant without an owner or state path, duplicated security-sensitive ownership, an observable behavior without an acceptance witness, or an unsafe fallback or unbounded resource path. Record fixture and report mechanics, generated-source details after schema behavior is fixed, CI-helper hardening, and rollout evidence as implementation or activation follow-ups unless they reveal one of those blockers. Use three stages: plan review, implementation/code review, and activation review. Stop plan iterations once the current plan satisfies these blocker criteria and hand off to implementation.

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
7. **Unresolved decision-point audit**: flag for the correctness-completeness worker: (a) plan tasks that implement one of multiple plausible designs where the plan records neither a decision-point receipt nor a `none remain` grill result; (b) a cleanup plan lacking a scope ledger or a grill result while material ownership, preservation, or history-strategy choices remain open; (c) a material candidate appearing in the branch diff or task scope with no keep/remove/defer disposition and no evidence or explicit-confirmation basis; a generic `user confirmed` or `behavior unchanged` phrase is not a basis. Each hit is a correctness-completeness finding.

## Step 2: Launch Workers in Parallel

Read `review-agents/review-panel-selection.md` for the recommended five-worker plan panel. `contract-docs` loads consistency; `risk` conditionally loads concurrency and premortem. Record selection rationale and Domains in staging metadata.

Launch all selected workers in parallel and wait for completion.

Each worker receives:
1. The full plan content
2. Relevant source file excerpts (signatures, data structure definitions, pipeline structure)
3. Its assigned lens catalogs from `review-panel-selection.md`
4. The project's CLAUDE.md content (for repository conventions)
5. **Repo-specific overrides take precedence**: if `CLAUDE.md`, `{guidelines_path}` (from `.ai-playbook/facts.md` TOML when present; typically `docs/maintenance/project-guidelines.md`), or any loaded company/project guideline defines complexity, naming, comment, or layering rules that conflict with the generic pattern catalog, the agent MUST apply the repo-specific value, not the catalog default. Example: catalog says "functions >50 lines" but `company-guidelines.md #17` says "≤30 lines per method"; apply the 30-line rule.
6. **Execution framing**: "You are reviewing an IMPLEMENTATION PLAN, not a code diff. Read the plan tasks and the referenced source files to understand what is being proposed. Apply your pattern catalog to identify whether the proposed changes would introduce the issues you are responsible for detecting."
7. **Output format**: use the shared fields from `severity-calibration.md`, including `blocking`, tangible consequence fields, `pattern`, and `descendant_launches`; no code-review `path/line/side` fields. Evidence and fix must be self-contained.
8. **Checklist inclusion backstop**: the `contract-docs` worker MUST apply the `plans` skill's checklist inclusion test through its `consistency` lens. External prerequisites are always blocking plan defects and are never exception-admissible. A release condition may pass only when the plan records a current `exception confirmed by user` receipt containing the exact confirmation text or a stable message reference, the specific checklist item, target or environment, and confirmation time or session, plus a `why executable now` line and observable `completion evidence`. Verify that this receipt binds the confirmation to the item and target, not only that it is fresh. A bare "user confirmed" statement is not an exception. Do not treat plan text as overriding higher-level authorization rules for external writes.
9. **Review Scope path-category audit**: run the readiness validator's Review Scope category rule (scripts/plan_readiness.py, review_scope_problem) over the plan under review; any review_scope_problem it reports is a finding (blocking when the misplacement would change reviewer behavior, e.g. production paths read as documentation).

### Worker bundles

| Worker | Lenses and plan focus |
|--------|-----------------------|
| `correctness-completeness` | `quality` and `implementation`: proposed behavior, assumptions, wiring, compatibility |
| `testing` | `testing`: discriminating tests, negative paths, verification gaps, hermeticity of proposed tests (ambient-input enumeration per testing.md) |
| `design-simplicity` | `architecture` and `simplification`: dependency direction, replacement map, avoidable complexity |
| `contract-docs` | `documentation` and inline `consistency`: scope closure, internal contradictions, naming, stale references |
| `risk` | `security`, plus signaled `concurrency` and `premortem`: security, ordering, rollout, operational failures |

Workers load the named catalogs. The `contract-docs` consistency section checks invariants against tasks, tests against implementation, cross-task formats, naming, commit boundaries, stale references, and measurable Evaluation Criteria. It owns contradictions, not source-code bugs, test gaps, or wiring defects.

Workers must not launch children. The `risk` worker applies premortem personas as reasoning sections and returns `descendant_launches: []`.

## Step 3: Synthesize Findings

After all workers complete, synthesize from their returns. The orchestrator deduplicates, orders, formats, and records statistics.

1. **Deduplicate**: merge the same root issue, preserve distinct fixes, and record contributing workers and lead lens.
2. **Calibrate, group, and order** with `severity-calibration.md`. Keep `blocking` independent.
3. **Cross-reference with plan**: For each finding, note whether the plan already
   addresses it (and mark as "Already mitigated" if so). Discarded mitigated items go in **Discarded findings** with reason `already-mitigated`.
4. **Incomplete agent output**: if a finding lacks `evidence` or a concrete `fix`, relaunch that agent focused on the gap; do not fill it inline. Failed relaunches: Panel Status `failed` or `timeout`, discards use `agent-failed` or `insufficient-evidence`.
5. **Record statistics**: populate full `## Review Statistics` per `review-staging` (Panel with Solo/Echo, Counts, Deduplication groups, Discarded with Pattern, Severity calibration, Triage placeholder) before writing `## Findings`. Write the matching `.stats.json` sidecar in the same pass.

**Sidecar schema (inlined here so it is in context without loading `review-staging`; authoritative copy lives there).** Every `.stats.json` is a version-1 record (`"schema_version": 1`) and must carry, at minimum:
- Top level (version-1 required set): `schema_version` (`1`), `review_type`, `date`, `artifact_slug`, `round`, `panel_mode` (`"full"` | `"focused"`), `selection_reason` (`null` when `panel_mode == "full"`), `source_kind` (`"plan"` for plan reviews), `source_digest` (lowercase 64-hex sha256 of the reviewed plan bytes, via `compute_source_digest("plan", plan_bytes)`), `escalation_reason` (`null` unless a sixth worker was launched), the four freshness fields (`review_mode`, `risk_signals`, `prior_findings_filter`, `last_fix_commit`), required on records dated on or after `EXTENDED_SIDECAR_MIN_DATE`; values and enum live in `review-staging`, `counts`, `panel`, `deduplication_groups`, `discarded`, `severity_calibration`, `triage_outcomes`, `findings`, `overflow`, `soften_watchlist` (`[]` when none). When `last_fix_commit` is non-null, the staging Markdown Metadata carries the `Witness ledger: N/A (no public mutators)` line (plan reviews have no public mutators; the populated-or-N/A witness shape per `review-staging` is required on any code-review round with a non-null `last_fix_commit`). Optional: `depth` (string), `domains` (list), `verdict` (string `yes` or `no`; this skill writes it in the same pass as the `## Summary`, matching the round's final verdict), `extensions` (object; all future extra data belongs inside it; any other top-level field is rejected). The digest must reflect the **post-fold** plan bytes the final round reviewed; recording a pre-fold digest is a stale-review error caught by the mechanical gate below.
- Pattern IDs: canonical `<lens>#<kebab-slug>` (owners: `quality`, `implementation`, `testing`, `architecture`, `simplification`, `documentation`, `security`, `consistency`, `unknown`). Plan-review contradictions and stale cross-references use `consistency#<slug>`. Each Markdown finding carries the same canonical `- **Pattern**:` bullet as its sidecar entry.
- Each `panel[]` row: `descendant_launches` (`[]` for the five base workers, which launch no children).
- Each `findings[]` row: `id` as an **integer** (`1`, not `"F1"`), plus `severity`, `blocking`, `consequence`, `reachability`, `blast_radius`, `confidence`, `pattern`, `workers`, `triage`.
- `discarded[]` rows with `reason: "wrong-owner"` must carry `lead_worker` + `lead_lens` (or `lead_agent`).

Skipping the sidecar is not allowed for plan reviews: the mechanical gate below fails the round if the sidecar is missing or schema-non-compliant.

## Step 4: Output

Write the review to `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md` and `{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.stats.json` (read `{reviews_dir}` from `.ai-playbook/facts.md` TOML; use `-r1`, `-r2`, … per loop iteration). Follow the staged hierarchy and **Review Statistics** section from `review-staging` (gold source).

**Mechanical gate (before reporting round complete):** run the review-staging validator on the staging path and confirm the `.stats.json` sidecar exists; do not report the round complete until both pass. This catches sidecar schema drift (string-vs-integer finding ids, missing consequence fields, missing `panel_mode`/`source_digest`/`descendant_launches`) **and stale-review-on-folded-plan** (sidecar `source_digest` no longer matches the plan on disk) that prose-only "follow `review-staging`" instructions cannot:

```bash
VALIDATOR="${REVIEW_STAGING_VALIDATOR:-$HOME/.ai-playbook/scripts/validate_review_staging.py}"
STAGING_PATH="{reviews_dir}/YYYY-MM-DD-plan-review-<feature-name>-r<N>.md"
PLAN_PATH="<path-to-the-plan-file-under-review>.md"   # whose bytes source_digest must match
python3 "$VALIDATOR" --hard "$STAGING_PATH" --source-plan "$PLAN_PATH"
```

`--source-plan` recomputes the plan's SHA-256 and fails hard if it differs from the sidecar's `source_digest`. Pass the plan path on every round, especially after folds: a `ready=yes` recorded against a pre-fold digest fails the gate and cannot be reported as round-complete.

**Canonical verdict line (readiness-validator output contract):** the `## Summary` of every review round must contain a final canonical line exactly `Verdict: ready=yes` or `Verdict: ready=no` (machine-exact for the readiness validator; this is the post-adoption producer contract). The validator's consumer rule accepts any `## Summary` line carrying a word-bounded `ready=yes`/`ready=no` token (last occurrence wins) for pre-adoption artifacts, but new rounds produced by this skill always end their Summary with the canonical line so downstream gates never depend on legacy verdict shapes. The same verdict is recorded in the sidecar `verdict` field in the same pass; the readiness validator prefers the sidecar field and falls back to Summary parsing only for artifacts whose sidecar lacks it.

Cursor hooks also warn via `postToolUse` after staging writes and may inject a `stop` follow-up if the newest round file is still a stub.

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
- Review mode: fresh-adversarial | targeted | verification-only
- Changed-risk signals: <comma list or none>
- Prior findings supplied as filter: no
- Last fix commit: <sha or none>
- Witness ledger: <populated | N/A (no public mutators)>
- Release-gate ledger: <rows or none>
- Findings: <staged count>
- Status: STAGED

## Review Statistics

### Panel
| Worker | Lenses | Status | Raw | Solo | Echo | Relaunch | Parent worker |
|--------|--------|--------|-----|------|------|----------|--------------|
| correctness-completeness | quality, implementation | complete | 0 | 0 | 0 | no | none |
| contract-docs | documentation, consistency | complete | 1 | 1 | 0 | no | none |

### Counts
- Workers launched: 5
- Workers skipped: 0
- Raw findings (all workers): 3
- Staged findings: 2
- Discarded during synthesis: 1
- Solo staged (unique agent origin): 1
- Echo staged (multi-agent dedup): 1

### Deduplication groups
| Staged # | Workers | Theme |
|----------|---------|-------|
| 1 | correctness-completeness, risk | Missing guard on concurrent delete |

When none: `None (each staged finding had a single agent origin).`

### Discarded findings
| Worker | Worker severity | Pattern | Theme | Reason | Notes |
|--------|------------------|---------|-------|--------|-------|
| contract-docs | Low | documentation#glossary | Add glossary link | already-mitigated | Plan Review Scope lists glossary |

When none: `None.`

### Severity calibration
| Staged # | Worker | Worker severity | Staged severity | Delta |
|----------|--------|-----------------|-----------------|-------|

When none: `None (agent severities matched staged severities).`

### Triage outcomes
Pending triage. *(After Step 5 plan fold: update Fixed, Dropped, Deferred, and Pending from finding triage.)*

## Findings

### Critical

#### F1. <short title>
- **Severity**: Critical | High | Medium | Low
- **Blocking**: true | false
- **Consequence**: <tangible outcome>
- **Reachability**: expected | common | plausible-edge | theoretical
- **Blast radius**: global | multi-service | single-service | local
- **Confidence**: verified | strong-evidence | hypothesis
- **Worker severity**: Medium *(omit when equal to Severity)*
- **Pattern**: quality#concurrent-access
- **Workers**: correctness-completeness, risk
- **Triage**: pending
- **Anchor**: Task N, bullet M (plan section heading or nearby prose anchor)
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<Self-contained, suggestion-tone explanation of the issue and the concrete change to the plan.>

#### Analysis (not posted)
<Originating worker and lens, source evidence, and severity rationale.>

---

### High

None.

### Medium

#### F2. <short title>
- **Severity**: Critical | High | Medium | Low
- **Blocking**: true | false
- **Consequence**: <tangible outcome>
- **Reachability**: expected | common | plausible-edge | theoretical
- **Blast radius**: global | multi-service | single-service | local
- **Confidence**: verified | strong-evidence | hypothesis
- **Pattern**: implementation#wiring-gap
- **Workers**: correctness-completeness
- **Triage**: pending
- **Anchor**: <plan section heading or nearby prose anchor>
- **Source**: [Prose] | [Premortem] | [Code]

#### Comment (posted as-is when approved)
<...>

#### Analysis (not posted)
<...>

---

### Low

None.

### Overflow manifest
| Worker | Pattern | Anchor | Severity | Confidence | Consequence |
|--------|---------|--------|----------|------------|-------------|
```

## Step 5: Amend Plan

After writing the review document:

1. Fold every accepted finding with `blocking: true` into the plan before the next round.
2. Fold non-blocking `Critical`, `High`, and material `Medium` findings when they expose a concrete implementation risk.
3. Treat non-blocking `Low` as optional; do not extend the cycle for document inconsistency without demonstrated behavior impact.
4. Add a reference line to the plan header: `Plan review: {reviews_dir}/<latest-rN>.md (latest, ready) · …`
5. Add verification commands for each folded behavioral finding.
6. Update finding triage and Review Statistics. Historical artifacts with older vocabularies remain valid legacy input.
7. Classify findings located in Completed history artifacts (vocabulary per `doc-hierarchy` "Document states") as immutable context pointing at the current Living SOT: the recommended fix is a pointer, successor, or a successor (`superseded_by`) ownership-registry row recorded from the Living SOT, never an edit to the historical artifact body.

Report to user:
> "Plan review r<N> complete: C critical, H high, M medium, L low.
> Review saved to `{reviews_dir}/<filename>-r<N>.md`.
> Ready for execution: Yes/No (requires zero unresolved blocking findings)."

## Iteration Discipline (plans skill gate)

When the user asks to run reviews until clean (e.g. "no medium problems", "until ready", "keep review loop until gates are met", "don't ask anymore"):

0. **No mid-loop re-prompt:** once the user directs continuous review, fold accepted blocking findings, write staging, and continue until the exit or reconciliation gate.
1. **Exit condition:** one fresh review of the current source digest with zero unresolved blocking findings and no unresolved reconciliation trigger.
2. **Severity alignment:** all workers use the shared four-tier calibration and independent blocking field.
3. **Treat a clean review as data, not proof of catalog completeness.** Run the self-audit before stopping.
4. **Run a brief self-audit alongside the agent review.** Before declaring iteration complete, scan the change types introduced by the latest plan revision (new domain types, decomposed methods, replaced classes, modified existing methods, restructured tasks) and verify the catalog has an active pattern for each. If a change type has no corresponding pattern in your review-agent prompts (often under `~/.agents/skills/review-agents/*.md`, and sometimes vendored under `agents/skills/review-agents/`), the agents cannot detect defects of that class. **Also list every "inherited/validated/tested/unchanged" claim in the plan and confirm the panel re-probed each by measurement** (see Signal-to-Noise: Inherited/validated claims are claims, not proof). A clean round that did not re-probe the plan's "settled" mechanisms is not evidence those mechanisms are correct.
5. **Catalog gap discovered → update the skill before re-iterating.** If the self-audit identifies a missing pattern (e.g. "no agent owns 'type-boundary discipline'", "no agent enumerates switches", "no agent checks for superseded code"), add the pattern to the relevant agent file FIRST, then re-run the review. Patching the plan around a catalog gap leaves the gap for future plans.
6. **Stop when both conditions hold**: the latest fresh review has zero unresolved blocking findings and a self-audit finds no material catalog gap.
7. **Record self-audit gaps as catalog improvements**, not as one-off plan patches. When the self-audit found something the catalog missed, the fix is two-part: patch the plan AND update the agent file or `SKILL.md`. The catalog improvement is the persistent gain; the plan patch is local.

## Reconciliation gate

Count one review-fix cycle only after a complete staged review has been triaged and every accepted blocking finding has been amended into the plan. Do not run an unbounded loop. When the same root issue recurs, fixes regenerate findings, review evidence contradicts itself, or the configured cycle cap is reached, invoke `review-reconciliation` before launching another panel. Pass the chronological staging artifacts and sidecars, plan digest, triage history, cycle counter, and the permitted mutation scope.

The reconciliation result is recorded in the next staging artifact or linked note. If it changes the plan, review catalog, or review rules, `review-plan` remains the original orchestrator and must run a fresh review of the changed plan with its normal worker selection and source-digest gate. It resets the recurrence counter only after that fresh review completes. A material architectural, scope, or rollout decision remains a user decision.

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
- Apply the shared finding budget. If a worker finds nothing credible,
  it reports "No findings."

## Integration Points

### With `review-staging` skill
Writes `{reviews_dir}/YYYY-MM-DD-plan-review-<slug>-r<N>.md` and the matching `.stats.json` sidecar. Follow `review-staging` for hierarchy, required `## Review Statistics`, and naming. Read `{reviews_dir}` from `.ai-playbook/facts.md` TOML. The sidecar JSON schema is inlined in Step 3 so it is in the producer's context without a load step, and the Step 4 mechanical gate runs `validate_review_staging.py --hard` before the round is reported complete.

### With `plans` skill
The `plans` skill provides the Checklist inclusion rule and required exception shape to its consumer, `review-plan`. Plan review uses `consistency` as the mandatory review home for that rule. External prerequisites are always blocking and never exception-admissible. A release condition may pass only with a current bound `exception confirmed by user` receipt plus `why executable now` and observable `completion evidence`.

### With the plan readiness gate (`scripts/plan_readiness.py`)
The review artifacts and sidecars this skill writes feed the readiness validator (`scripts/plan_readiness.py`) that the `execute-plan` and `done` gates call. The validator derives the feature slug from the plan filename stem, selects the latest round under `{reviews_dir}` via the `*-plan-review-<feature-slug>-r<N>.md` glob (highest `r<N>`, never mtime), and passes only when that round's `.stats.json` sidecar exists, passes schema validation, carries `source_kind: "plan"` and a `source_digest` equal to the current plan bytes, and reports zero unresolved blocking findings (`is_review_ready`); the verdict is established from the sidecar `verdict` field first, with the Summary total rule over the review Markdown as the legacy fallback. A missing or malformed sidecar, a `ready=no` verdict, or an unresolved blocking finding therefore fails the downstream gates, not just this skill's own Step 4 mechanical gate. The sidecar digest covers the PLAN bytes only: a post-round plan edit fails the gates as a stale digest, while a post-round edit of the review Markdown is still caught when it breaks the blocking consistency the validator recomputes over the current review text; once the sidecar carries a conforming `verdict` field, the Summary verdict token is no longer consulted, so Summary-only edits no longer flip readiness. The gate additionally requires the plan's decision-points trailer under the sidecar-date rule owned by scripts/plan_readiness.py (the DECISION_MARKER_MIN_DATE constant and the evaluate_readiness step-6 comment in scripts/plan_readiness.py together own the exact date and exemption semantics); treat a missing or unresolved trailer in such a plan as a blocking documentation finding. The gate additionally runs the Review Scope category rule owned by scripts/plan_readiness.py (review_scope_problem) under its own sidecar-date rule.

### With `review-reconciliation` skill
When the reconciliation gate fires, this skill owns the chronological recurrence analysis and closure ledger. `review-plan` owns the follow-up review and cannot accept reconciliation's own refactor as proof of closure.
