# RFC Design Harness: Regression Eval Cases

Use these cases to regression-test the `rfc-design` orchestrator harness (gates, Step 2 sub-agents, staging file, fold-in). Grade **traces** (steps taken, agents launched, artifacts written), not only final RFC prose.

Each case uses this shape:

```text
case_id
trigger / fixture
expected_trace
forbidden_trace
pass_criteria
```

---

## RFC-EVAL-001: Skill activation (create)

**Trigger:** User says "draft a design RFC for feature X" with PRD attached.

**Expected trace:**
- Announce `rfc-design` in **Create** mode
- Step 0 input inventory or fast-path checklist (Step 0.1)
- No RFC sections before user proceed (unless fast path applies)

**Forbidden trace:**
- Jump to Step 1 without coverage checklist
- Invoke `review-confluence-doc` or `plans` instead

**Pass:** Correct mode; gates respected.

---

## RFC-EVAL-002: Skill activation (review-local)

**Trigger:** User points at an existing `*-rfc.md` and says "review this RFC only."

**Expected trace:**
- Announce **Review-local** mode
- Step 2 only; no Step 0 intake or Step 1 regeneration

**Forbidden trace:**
- Full create workflow from scratch
- Saving a new RFC under `{rfcs_dir}` without user request

**Pass:** Review-local path; staging file written.

---

## RFC-EVAL-003: Confluence redirect

**Trigger:** User provides a Confluence URL for an RFC review.

**Expected trace:**
- Redirect to `review-confluence-doc`; do not fetch page inside `rfc-design`

**Forbidden trace:**
- Step 2 sub-agents on unparsed Confluence content via this skill

**Pass:** Correct skill handoff.

---

## RFC-EVAL-004: Step 2 not skipped

**Trigger:** Create mode; Step 1 draft complete; draft looks polished.

**Expected trace:**
- Launch the selected Light focused workers in parallel
- Write staging file under `{reviews_dir}/YYYY-MM-DD-rfc-review-<slug>-<mode>.md` before Step 3 fold-in

**Forbidden trace:**
- Orchestrator inline review replacing sub-agents
- Present final RFC with no staging file

**Pass:** Workers launched; staging path recorded.

---

## RFC-EVAL-005: Light focused panel (default)

**Trigger:** MVP RFC create; user did not request full review; no async/queue content.

**Expected trace:**
- Workers: `correctness-completeness`, `design-simplicity`, `contract-docs`, `risk`
- `contract-docs` loads `documentation` and `consistency`; `risk` loads `security`
- Staging records `panel_mode: focused` and the selection reason for omitting `testing`

**Forbidden trace:**
- Separate lens workers launched
- Missing any default Light agent

**Pass:** Agent status table matches Light set.

---

## RFC-EVAL-006: Concurrency when matched (Light depth)

**Fixture:** RFC draft §4 describes message queues, `@Transactional`, or multi-threaded workers.

**Trigger:** Create or Review-local at Light depth (no "full review" request).

**Expected trace:**
- `concurrency.md` launched in addition to Light set
- Listed in staging **Agents launched** and Agent status

**Forbidden trace:**
- Omit `concurrency` because depth is Light

**Pass:** Concurrency agent runs at Light when condition matches.

---

## RFC-EVAL-007: Telegraphic §4 finding folded

**Fixture:** Draft §4 edge case: `- Retry on failure` (no Condition / Behavior / Outcome).

**Expected trace:**
- `contract-docs` or `correctness-completeness` returns a shared-severity finding with quoted excerpt
- After fold-in: §4 uses `##### Edge case: ...` with Condition / Behavior / Outcome

**Forbidden trace:**
- Finding only in chat; RFC left telegraphic

**Pass:** RFC section revised per severity map.

---

## RFC-EVAL-008: Terminology writer meta rejected

**Fixture:** Terminology contains `#### Filters and bitmaps` subsection or writer policy table.

**Expected trace:**
- Worker flags a blocking or materially actionable finding
- Fold-in: flat A–Z glossary only; matrices moved to Addendum if needed

**Forbidden trace:**
- Final RFC ships with topic subsections in Terminology

**Pass:** Terminology conforms to reader-facing glossary rules.

---

## RFC-EVAL-009: Partial review gate (>2 agent failures)

**Fixture:** Simulate or inject 3 failed sub-agent returns (timeout/empty).

**Expected trace:**
- Staging file written with Agent status `failed` rows and **Partial review: yes**
- Step 3 fold-in **not** performed
- Console reports partial review status

**Forbidden trace:**
- Silent skip of failed agents
- Fold-in despite partial review gate

**Pass:** Partial gate enforced; user informed.

---

## RFC-EVAL-010: Relaunch budget (thin agent output)

**Fixture:** One agent returns a single vague finding with no quoted excerpt.

**Expected trace:**
- One relaunch with focused prompt
- Agent status shows `relaunch-complete` and Relaunch: yes
- No second relaunch for same agent

**Forbidden trace:**
- Orchestrator expands finding inline instead of relaunch
- More than 1 relaunch per agent

**Pass:** Relaunch recorded; budget respected.

---

## RFC-EVAL-011: Full depth on explicit request

**Trigger:** User says "full review" on an existing draft.

**Expected trace:**
- All five recommended workers
- `testing` is present; `risk` records `premortem` or `concurrency` as loaded lenses only when matched

**Forbidden trace:**
- Focused panel only when user explicitly requested Full

**Pass:** Full agent set launched.

---

## RFC-EVAL-012: Post-fold verification round (Step 2.5)

**Fixture:** A draft where the r1 panel returns at least one `blocking: true` finding whose fix must rewrite a §4 flow. Seed the fold so the new flow text contradicts an untouched section (for example a new §8 test assertion against a metric §7 defers to a later ticket).

**Expected trace:**
- r1 staging written, blocking finding folded
- A second round launches over the **post-fold** RFC bytes, including `correctness-completeness` and the workers owning the rewritten sections
- r2 staging written as `...-r2.md` with `Round: r2`, `Prior:` set, and a `source_digest` matching the RFC on disk
- The seeded fold-induced contradiction is reported in r2
- Step 3 runs only after a round returns zero unresolved blocking findings and required no fold

**Forbidden trace:**
- Step 3 finalize directly after the r1 fold
- r2 sidecar carrying the pre-fold r1 digest
- Exit declared on a round that itself produced fixes
- More than three verification rounds without handing residuals to the user

**Pass:** The fold is reviewed, not assumed; readiness is claimed only against post-fold bytes.

---

## RFC-EVAL-013: Formatting-only fold skips Step 2.5

**Fixture:** r1 returns only Low non-blocking findings on Terminology ordering and heading shape.

**Expected trace:**
- Fold applied, Step 2.5 skipped with the formatting-only reason recorded
- Step 3 finalize proceeds

**Forbidden trace:**
- A full verification round for a formatting-only fold
- Skipping Step 2.5 when the same fold also changed normative content

**Pass:** The verification gate is scoped to normative folds.

---

## RFC-EVAL-014: Undefined kept jargon flagged by documentation phase 2

**Fixture:** RFC draft §4 flow uses "protected egress" and "blast radius" as normative wording with no `# Terminology` / `## Terms` entry and no inline first-use spelling-out.

**Trigger:** Create or Review-local at Light depth.

**Expected trace:**
- `contract-docs` (`documentation` phase 2) returns a finding tagged `documentation#prose-undefined-jargon`
- Severity `Low` (wording-only), with both fix options in the body: reword to plain English **or** add a one-line A–Z glossary bullet
- Finding quotes the undefined term and names the missing glossary section

**Forbidden trace:**
- Finding omitted because "concision is acceptable"
- Finding tagged only with the legacy alias `prose-clarity#…`
- Single fix option presented as mandatory when either reword or glossary-entry would resolve it

**Pass:** Correct pattern tag; both fix options present; severity respects the documentation default-Low rule.

---

## Adding new cases

After any production or review incident (skipped Step 2, wrong depth, bad fold-in, gate bypass):

1. Capture trigger, fixture RFC excerpt, and actual trace.
2. Add the smallest replayable case here.
3. Update the orchestrating rule in `SKILL.md` if the harness gap is structural.
