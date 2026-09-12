# Plan: review-coverage pass 2 (JVM residuals + guideline widening)

Backlog (scope of record): `docs/history/backlog/2026-09-10-jvm-review-coverage-plan-residual-probe-friction.md`, `docs/history/backlog/2026-09-10-jvm-review-coverage-r1-residuals.md`, `docs/history/backlog/2026-09-10-widen-guideline-review-coverage-beyond-jvm.md` (revived 2026-09-12 with this plan when code quality became the fourth driving principle; the items and the plan were parked by the 2026-09-11 efficiency triage)
Guideline SOT: `projects/.ai-playbook/java_guidelines.md` (rules #16-#25 landed by the certified JVM plan, squash 7b26dfe; normative bodies stay frozen), `projects/.ai-playbook/kotlin_guidelines.md` (rules #1-#22), `projects/.ai-playbook/python_guidelines.md` (rules #1-#25)
Predecessor plan (completed): `docs/plans/completed/2026-09-10-strengthen-jvm-review-coverage.md`
Plan review: `docs/reviews/2026-09-11-plan-review-review-coverage-pass-2-r<N>.md` (prefix glob; the latest round is the verdict of record)

## Terms

- **Guideline Pack**: the per-review bundle of shared language guideline paths plus section and rule hints that `doing-code-review` Step 2.5 attaches to worker prompts.
- **Shared trigger surfaces**: the cross-language changed-scope signals (shared helpers, flag and configuration wiring, timeout boundaries, living-documentation claims) that decide when guideline evidence is required; this plan makes `doing-code-review` Step 2.5 their single enumeration home.
- **Trigger table**: the per-overlay section mapping language-specific diff signals to numbered rules of the overlay's shared guideline corpus.
- **Risk-signal floor**: the `review-panel-selection` rule that escalates the worker set when the diff touches listed code-mutation surfaces.
- **Clear-round quality bar**: the `execute-plan` Step 3.4 checklist a review round must satisfy before the Phase 3 loop may exit clean.
- **Language overlay**: a stack-specific trigger file inside `doing-code-review` (`java-spring.md`, `kotlin-spring.md`, `python.md`) appended to worker prompts; the `review-agents` catalogs stay language-agnostic.

## Assumptions

- assume the three deferred backlog items are the scope of record despite their `Priority: deferred` header; basis: the authoring instruction dated 2026-09-11 schedules this plan after the efficiency triage and names all three files.
- assume the widening wires Kotlin and Python through per-language mandatory-evidence paragraphs and overlay trigger tables, and adds no new numbered rules to `kotlin_guidelines.md` or `python_guidelines.md`; basis: the widen item requires deciding per corpus with prior review-cycle evidence as arbiter and forbids precommitting to numbered rules without it, and the repo holds no prior Kotlin or Python review-cycle coverage evidence classes.
- assume `doing-code-review` Step 2.5 is the single owner of the shared trigger-surface enumeration; basis: it is the Guideline Pack section of record, `execute-plan` already runs Phase 3 reviews through `doing-code-review`, and the r1 residuals item names owner-plus-references as a remedy for the trigger-list duplication.
- assume the compatibility-witness routing fix lands as a new tiered-ownership table row in `review-panel-selection.md` rather than rewording the overlay sentence alone; basis: r1 item 1 offers either remedy and wrong-owner discard decisions are recorded against that table.
- assume the Release-gate ledger fix adds an accepted-residual rationale field to `execute-plan` Step 3.4 item 6 rather than rewording `java_guidelines` rules #23/#24; basis: r1 item 6 offers either remedy and the certified rule bodies stay frozen.
- assume the java-spring trigger section folds into the Review-wide Java checks bullets and the section is deleted; basis: r1 item 3 offers folding or a one-line pointer, and folding removes the fifth trigger-list restatement site outright.
- assume doc/skill-only plan conventions apply (the testing worker uses Validation Commands as primary evidence; no runtime scripts are introduced); basis: `doing-code-review` Doc/skill-only diffs boundary, `execute-plan` Step 3.1 item 5, and the certified predecessor plan's identical assumption.
- assume trigger tables cite only rule numbers resolvable from each corpus's own numbered index, with an explicit not-applicable note where a signal has no numbered rule; basis: widen item acceptance bullet 2.
- assume reviews land at `docs/reviews/2026-09-11-plan-review-review-coverage-pass-2-r<N>.md`; basis: plans skill review-artifact naming.

Decision points requiring a grill: none remain.

## Gist & Examples

What changes: the review-cycle evidence wiring that the certified JVM plan built for Java becomes language-wide and single-homed. `doing-code-review` Step 2.5 enumerates the shared trigger surfaces exactly once and gains Kotlin/Spring and Python mandatory-evidence paragraphs mirroring the Java one; the Kotlin and Python overlays gain trigger tables mapping their own diff signals to existing numbered rules of their corpora; the `execute-plan` clear-round gate accepts Kotlin and Python evidence records and references Step 2.5 instead of restating trigger lists; the risk-signal floor stops re-enumerating the shared guideline-coverage surfaces (it keeps its own code-mutation signals inline) and stops reading as Java-only; the near-universal floor qualifiers are narrowed; a missing compatibility witness gets its own tiered-ownership row; the java-spring trigger section folds into the Review-wide bullets; the rule #25 example loses its backlog-ticket mock; and the Release-gate ledger field list gains the residual rationale that rules #23/#24 already direct into it. Shared surfaces are edited once: every file that previously restated the four-surface list now references Step 2.5.

**Before (today):** a Kotlin/Spring branch changes a shared coroutine-scoped repository helper reused by a new caller and touches a `@ConfigurationProperties` binding. The panel clears: the staging record lists `kotlin_guidelines.md` as a path with no applied hints, which is exactly the path-only record a Java branch cannot clear with. The risk floor ignores the branch because its surface wording and guideline-check clause speak only of Java/Spring. A reviewer spots the missing coroutine-cancellation coverage but discards the finding as wrong-owner, because the overlay routes compatibility-style witness work to implementation while the tiered table routes missing tests to testing. The four trigger surfaces that decide all of this are worded independently in five places, and the Release-gate ledger accepts a deferral row with no rationale even though rules #23/#24 direct one into the durable record.

**After (this plan):** the same branch cannot clear a round. The Kotlin mandatory-evidence paragraph makes the pack incomplete without its three shared paths plus applied hints from the overlay trigger table, which maps coroutine boundaries to `kotlin_guidelines.md` #4/#16/#11 and configuration binding to #7/#10/#14/#15; staging metadata records `Kotlin guideline checks: #<rules>` and the quality bar rejects the path-only record. The floor treats the shared trigger surfaces as risk signals for any language via its Step 2.5 reference and pulls the changed files' own overlay guideline checks. The tiered table routes a missing compatibility witness to `correctness-completeness` with the `implementation` lens. The trigger surfaces are enumerated once in Step 2.5 with narrowed qualifiers, and every other site references that list. The ledger row for a deferred boundary records its accepted-residual rationale.

Worked example of the single-homing, showing a surface rename under the plan: changing the shared list in Step 2.5 from "timeout or scheduled-executor boundaries" to new wording updates one file; `review-panel-selection` and `execute-plan` still resolve because they reference the list instead of copying it, and the Validation Commands probes pin each reference so a silently severed pointer fails the block.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every finding in the two residual items and every acceptance bullet in the widen item maps to a task below; every rule number a trigger table cites resolves to a numbered heading in its corpus (resolvability loops in Validation Commands).
- consistency: the shared trigger-surface apply-when conditions are enumerated exactly once (`doing-code-review` Step 2.5); `review-panel-selection` and `execute-plan` Step 3.1 reference that list, while the Step 3.4 quality bar keeps its evidence-surface phrasing and gains the overlay-generic clause; the widened Kotlin/Python gates mirror the Java gate's shape (paths mandatory, hints applied, metadata records them, path-only listings rejected).
- hygiene: no em dashes in new content; no real service names, credentials, customer data, ticket identifiers, or internal URLs; the public hygiene scan exits 0.
- maintainability: each edit is the minimal diff that closes its finding; frozen regions (rule bodies #16-#25, overlay sections outside the edited spans, the five-worker panel) stay untouched.

**Done when:**

- All task checkboxes are checked and the Validation Commands block exits 0 on the changed tree.
- `scripts/check-no-em-dash.sh` (scoped to the changed files) and `scripts/scan-public-hygiene.sh` pass.

**Ship when:**

- The next Kotlin/Spring or Python `execute-plan` Phase 3 or `doing-code-review` run consumes the widened overlays and records per-language applied rule hints in its staging Metadata; this is human-owned evidence from a future review run, tracked as prose here only.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `projects/.ai-playbook/java_guidelines.md` (rule #25 worked example trim only; all rule bodies and other examples frozen)
- `agents/skills/doing-code-review/SKILL.md` (Step 2.5 mandatory-evidence block only; rest frozen)
- `agents/skills/doing-code-review/kotlin-spring.md` (new trigger table section at end of file; rest frozen)
- `agents/skills/doing-code-review/python.md` (new trigger table section at end of file; rest frozen)
- `agents/skills/doing-code-review/java-spring.md` (Review-wide Java checks bullets #21-#25 extension and trigger-section deletion only; rest frozen)
- `agents/skills/review-agents/review-panel-selection.md` (tiered-ownership table row addition and risk-signal floor paragraph replacement only; rest frozen)
- `agents/skills/execute-plan/SKILL.md` (Step 3.1 item 2 bullet, Step 3.4 quality bar item 4 addition and item 6 field list only; rest frozen)

**Tests:**

- None; this is a doc/skill-only change and the Validation Commands block is the testing evidence.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `projects/.ai-playbook/kotlin_guidelines.md` and `projects/.ai-playbook/python_guidelines.md`; reason: the widening decides per corpus with review-cycle evidence as arbiter and this repo holds no evidence classes establishing a Kotlin or Python coverage rule family; this plan ships the wiring only, so the corpora stay untouched.
- `agents/skills/review-agents/documentation.md` and the other lens catalogs; reason: they stay language-agnostic and none of the findings names them.
- `agents/skills/review-agents/simplification.md`; reason: the census evidence requirement landed with the predecessor plan and no residual names it.
- `README.md`; reason: skill names, paths, and usage do not change.
- `docs/maintenance/document-registry.md`; reason: no documents are added, removed, or re-homed.

## Validation Commands

Task 8 executes this block in full after all edits land; no earlier task runs it. Pins are matched against newline-flattened, space-squeezed text so a line-wrapped insert cannot fail the probe (probe-friction residual: wrap-tolerance is load-bearing here). Forbidden-text probes marked RED-today were executed against the 2026-09-11 tree at authoring time and all fired; each flips GREEN exactly when its task lands. The resolvability loops make a trigger table that cites a nonexistent corpus rule number fail the block.

```bash
#!/usr/bin/env bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
flat() { tr '\n' ' ' < "$1" | tr -s ' '; }
has() { # has '<fixed-string>' <file> <label>
  flat "$2" | grep -qF -- "$1" || fail "$3 (missing in $2)"
}
lacks() { # lacks '<fixed-string>' <file> <label>
  if flat "$2" | grep -qF -- "$1"; then fail "$3 (forbidden text present in $2)"; fi
}

JG=projects/.ai-playbook/java_guidelines.md
DCR=agents/skills/doing-code-review/SKILL.md
KOV=agents/skills/doing-code-review/kotlin-spring.md
POV=agents/skills/doing-code-review/python.md
JOV=agents/skills/doing-code-review/java-spring.md
RPS=agents/skills/review-agents/review-panel-selection.md
EP=agents/skills/execute-plan/SKILL.md
KG=projects/.ai-playbook/kotlin_guidelines.md
PG=projects/.ai-playbook/python_guidelines.md

for f in "$JG" "$DCR" "$KOV" "$POV" "$JOV" "$RPS" "$EP"; do
  test -f "$f" || fail "missing expected file $f"
done

# Task 1: rule 25 example trimmed to reconciliation evidence (RED-today: rule25-mock, rule25-title)
has 'no listener annotation, no scheduler, no inbound adapter' "$JG" 'rule 25 reconciliation evidence'
lacks 'Owner: feature team lead' "$JG" 'rule25-mock'
lacks 'Restore notification stream consumer' "$JG" 'rule25-title'
# Frozen neighbors stay in place
has 'Compilation is not compatibility' "$JG" 'rule 24 normative body'
has 'durable backlog item with an explicit owner and handoff' "$JG" 'rule 25 normative body'

# Task 2: Step 2.5 owns the shared trigger surfaces; Kotlin and Python packs mandatory
has 'single canonical' "$DCR" 'shared-surface owner declaration'
has 'when the reuse adds a caller' "$DCR" 'shared surface: narrowed helper qualifier'
has 'when the change alters readiness gating' "$DCR" 'shared surface: narrowed flag qualifier'
has 'timeout or scheduled-executor boundaries' "$DCR" 'shared surface: timeout boundary'
has 'living-documentation status claims' "$DCR" 'shared surface: living docs'
has 'the shared `kotlin_guidelines.md`, `jvm_guidelines.md`, and' "$DCR" 'Kotlin pack paths'
has 'the Kotlin rules the `kotlin-spring.md` trigger table' "$DCR" 'Kotlin mandatory-evidence paragraph'
has 'python_guidelines.md` and `coding_guidelines.md` paths' "$DCR" 'Python pack paths'
has 'the Python rules the `python.md` trigger table' "$DCR" 'Python mandatory-evidence paragraph'
has 'applied rule hints for each' "$DCR" 'company/project applied-hint metadata'
has '#16 through #25' "$DCR" 'Java hint range retained'
# RED-today: java-paragraph-restatement (fires once, inside the replaced Java paragraph span)
lacks 'shared helpers reused across callers' "$DCR" 'java paragraph shared-surface restatement'

# Tasks 3-4: overlay trigger tables exist and cite resolvable corpus rule numbers
has '## Guideline trigger table (Kotlin)' "$KOV" 'kotlin trigger table heading'
KSEC="$(sed -n '/^## Guideline trigger table (Kotlin)/,$p' "$KOV")"
test -n "$KSEC" || fail 'kotlin trigger table extraction empty'
for n in $(printf '%s\n' "$KSEC" | grep -oE '#[0-9]+' | tr -d '#' | sort -un); do
  grep -qE "^## ${n}\." "$KG" || fail "kotlin trigger table cites missing kotlin_guidelines rule #${n}"
done
has 'kotlin_guidelines.md #7, #10, #14, #15' "$KOV" 'kotlin configuration mapping'
has '## Guideline trigger table (Python)' "$POV" 'python trigger table heading'
PSEC="$(sed -n '/^## Guideline trigger table (Python)/,$p' "$POV")"
test -n "$PSEC" || fail 'python trigger table extraction empty'
for n in $(printf '%s\n' "$PSEC" | grep -oE '#[0-9]+' | tr -d '#' | sort -un); do
  grep -qE "^## ${n}\." "$PG" || fail "python trigger table cites missing python_guidelines rule #${n}"
done
has 'python_guidelines.md #4, #12, #15, #16, #22' "$POV" 'python monkeypatch mapping'
has 'no numbered rule exists' "$POV" 'python not-applicable notes'

# Task 5: java-spring trigger section folded into Review-wide bullets (RED-today: trigger-section, old-trigger-line)
has '(Spring `@Component` converters, mappers, or persistence helpers' "$JOV" 'folded rule 21 bullet'
has 'especially after a dependency coordinate change (alongside #19)' "$JOV" 'folded rule 24 bullet'
lacks '## Rollout, timeout, and shared-helper trigger' "$JOV" 'trigger-section heading removed'
lacks 'apply #21 to every caller' "$JOV" 'old trigger-section line removed'
lacks 'apply #24 alongside #19' "$JOV" 'old trigger-section witness line removed'

# Task 6: witness routing row and language-neutral narrowed floor (RED-today: floor-helpers, floor-flags, floor-timeout)
has 'Missing compatibility witness for changed direct dependency API usage' "$RPS" 'tiered witness row'
has 'enumerated in the `doing-code-review` Step 2.5' "$RPS" 'floor references the owner list'
has 'language overlay (Java/Spring, Kotlin/Spring, or Python)' "$RPS" 'floor per-language checks clause'
lacks 'shared conversion or persistence helpers reused across callers' "$RPS" 'floor-helpers'
lacks 'feature-flag and configuration wiring that gates capability readiness' "$RPS" 'floor-flags'
lacks 'time-budget or timeout boundaries' "$RPS" 'floor-timeout'
lacks 'Java/Spring guideline checks' "$RPS" 'floor Java-only clause'

# Task 7: execute-plan references the owner list; Kotlin/Python gates; ledger rationale (RED-today: ep-trigger)
has 'the rules the overlay trigger tables map' "$EP" 'item 2 overlay-generic requirement'
has 'not restated here' "$EP" 'item 2 single-homing reference'
has 'or `Kotlin guideline checks: #<rules>`' "$EP" 'Kotlin staging metadata field'
has 'likewise records the' "$EP" 'item 4 Kotlin/Python clause'
has 'accepted-residual rationale' "$EP" 'item 6 ledger rationale field'
has '#16 through #25' "$EP" 'Java hint range retained'
lacks 'shared helpers reused across callers' "$EP" 'ep-trigger'
lacks 'timeout or scheduled-executor boundaries' "$EP" 'ep trigger surface restatement'
lacks 'living-documentation status claims' "$EP" 'ep living-docs restatement'

# Repository scans (scoped hygiene; the block anchors itself to the repo root)
bash scripts/check-no-em-dash.sh file "$JG" "$DCR" "$KOV" "$POV" "$JOV" "$RPS" "$EP" || fail 'em dash found in changed files'
bash scripts/scan-public-hygiene.sh || fail 'public hygiene scan failed'

echo 'VALIDATION PASS: review coverage pass 2 wiring complete'
```

### Task 1: Trim the java_guidelines rule #25 worked example to its reconciliation evidence

Files:
- `projects/.ai-playbook/java_guidelines.md`

- [ ] In the rule #25 example block, replace the closing backlog-ticket mock together with its `record a durable backlog item:` lead-in line (the span from that lead-in line at the end of the Review finding sentence through `revisit before the next release note.`) so the Review finding sentence ends: `record a durable backlog item with an explicit owner and handoff instead of leaving the deferral in review notes.` The reconciliation evidence above it (consumer class, configuration, test witness bullets) stays byte-identical.
- [ ] Commit: `docs: trim java guidelines rule 25 example to reconciliation evidence`

### Task 2: Make Step 2.5 the single owner of the shared trigger surfaces and add Kotlin/Python mandatory-evidence paragraphs

Files:
- `agents/skills/doing-code-review/SKILL.md`

- [ ] In Step 2.5, immediately before the `For Java/Spring reviews` paragraph, insert this paragraph: `The shared changed-scope trigger surfaces for every language overlay are enumerated once, here: shared conversion or persistence helpers reused across callers when the reuse adds a caller or changes an existing caller outcome, feature-flag and configuration wiring when the change alters readiness gating, timeout or scheduled-executor boundaries, and living-documentation status claims. This list is the single canonical enumeration for the review cycle; review-panel-selection.md and execute-plan reference it instead of restating it.`
- [ ] In the `For Java/Spring reviews` paragraph, change the trigger enumeration to: `when the diff contains Java, Maven, Spring configuration, generated request models, outbound HTTP clients, downstream error mapping, or changed dependency coordinates, or when a shared trigger surface from the paragraph above is present.` Keep the rest of the paragraph, including the `#16 through #25` range and the path-only-listing disclaimer, unchanged.
- [ ] After the Java paragraph, insert: `For Kotlin/Spring reviews, the Guideline Pack is incomplete unless it includes the shared `kotlin_guidelines.md`, `jvm_guidelines.md`, and `coding_guidelines.md` paths. Add rule hints for the Kotlin rules the `kotlin-spring.md` trigger table maps to the changed scope: the shared trigger surfaces from the paragraph above plus the Kotlin-specific signals the table names. Workers must open the relevant hinted sections during their lens pass, and staging metadata must record the applied Kotlin rule hints. Do not treat a path-only listing as evidence that the guidance was applied.`
- [ ] After the Kotlin paragraph, insert: `For Python reviews, the Guideline Pack is incomplete unless it includes the shared `python_guidelines.md` and `coding_guidelines.md` paths. Add rule hints for the Python rules the `python.md` trigger table maps to the changed scope: the shared trigger surfaces from the paragraph above plus the Python-specific signals the table names. Workers must open the relevant hinted sections during their lens pass, and staging metadata must record the applied Python rule hints. Do not treat a path-only listing as evidence that the guidance was applied.`
- [ ] Extend the staging-Metadata paragraph to read, after `including whether company and project were both present`: `and the applied rule hints for each attached file that carries its own numbered index (shared language, company, and project files alike)`.
- [ ] Commit: `skills: single-home guideline trigger surfaces and mandate kotlin python pack evidence`

### Task 3: Add the Kotlin trigger table to the kotlin-spring overlay

Files:
- `agents/skills/doing-code-review/kotlin-spring.md`

- [ ] Append this section at the end of the file (every cited rule number must exist as a numbered heading in `projects/.ai-playbook/kotlin_guidelines.md`):

````markdown
## Guideline trigger table (Kotlin)

The orchestrator records applied hints from this table as `Kotlin guideline
checks: #<rules>` in staging Metadata; a path-only `kotlin_guidelines.md`
listing without applied hints is not evidence of application. Rule numbers
resolve from the `kotlin_guidelines.md` numbered index:

- Coroutine boundaries and cancellation (`suspend` functions, `GlobalScope`,
  structured-concurrency violations, swallowed `CancellationException`):
  kotlin_guidelines.md #4, #16; async fire-and-forget assertions: #11.
- MockK test surfaces (relaxed mocks, `clearAllMocks`, vararg matchers, stubbed
  Reactor/R2DBC error flows): kotlin_guidelines.md #2, #6, #9.
- Configuration binding (`@ConfigurationProperties` init validation, Duration
  fields, Spring Cloud Config identity keys, swallowed config failures):
  kotlin_guidelines.md #7, #10, #14, #15.
- Data-class and collection boundaries (null-safe chains, `forEach` misuse,
  numbered enum slots): kotlin_guidelines.md #5, #8, #12.
- Logging and metrics (exception object not `e.message`, boolean metric tags):
  kotlin_guidelines.md #13, #17.
- Batch read paths and terminal handlers (slim projections, hoisted invariant
  checks, throwing terminal handlers): kotlin_guidelines.md #19, #20, #21.
````

- [ ] Commit: `skills: add kotlin guideline trigger table to overlay`

### Task 4: Add the Python trigger table to the python overlay

Files:
- `agents/skills/doing-code-review/python.md`

- [ ] Append this section at the end of the file (every cited rule number must exist as a numbered heading in `projects/.ai-playbook/python_guidelines.md`; signals with no numbered rule carry an explicit not-applicable note):

````markdown
## Guideline trigger table (Python)

The orchestrator records applied hints from this table as `Python guideline
checks: #<rules>` in staging Metadata; a path-only `python_guidelines.md`
listing without applied hints is not evidence of application. Rule numbers
resolve from the `python_guidelines.md` numbered index:

- Pytest structure and assertions (test names, tabular rows, `pytest.raises`
  match): python_guidelines.md #1, #10, #11, #14.
- Monkeypatching (module-level constants, spy-not-mock ordering, short-circuit
  lookups, selftest module patching, from-import invisibility):
  python_guidelines.md #4, #12, #15, #16, #22.
- Logging and error output (per-call `getLogger`, hand-rolled stderr capture):
  python_guidelines.md #6, #24.
- Configuration and data shapes (typed value objects, dict key shape,
  dataclass field ordering): python_guidelines.md #8, #13, #17.
- Scripts and selftests (explicit guard raises, loop and test-timeout ceilings,
  whitespace-only rejection): python_guidelines.md #21, #25.
- Resource and mutation contracts (release flags, in-place mutation names):
  python_guidelines.md #5, #7.
- Dependency pins and packaging: no numbered rule exists in the corpus; apply
  the Packaging and Dependencies checks of this overlay directly.
- asyncio: no numbered rule exists in the corpus; apply #21 plus the Async
  Python section of this overlay.
````

- [ ] Commit: `skills: add python guideline trigger table to overlay`

### Task 5: Fold the java-spring trigger section into the Review-wide Java checks bullets

Files:
- `agents/skills/doing-code-review/java-spring.md`

- [ ] Replace the `#21` through `#25` bullets of the Review-wide Java checks list with:
  `- \`java_guidelines.md\` #21: raise-versus-degrade policy of every caller at shared conversion and persistence helpers (Spring \`@Component\` converters, mappers, or persistence helpers reused by a new caller: apply to every caller).`
  `- \`java_guidelines.md\` #22: flag and configuration matrix coverage for independent capability readiness (rollout flags, \`@ConditionalOnProperty\` wiring, profile-specific configuration).`
  `- \`java_guidelines.md\` #23: time budgets at the last serialization and transport boundary and scheduled timeout resource lifecycles (per-request budgets, resilience timeout annotations, \`@Scheduled\` cleanup).`
  `- \`java_guidelines.md\` #24: executable compatibility witness for changed direct API usage, especially after a dependency coordinate change (alongside #19).`
  `- \`java_guidelines.md\` #25: living-documentation status claims reconciled with implementation evidence (executable consumer, producer, or witness).`
- [ ] Delete the entire `## Rollout, timeout, and shared-helper triggers (Spring)` section (heading plus its five bullets); the Spring vocabulary now lives in the folded bullets above. The ownership sentence at the end of the Review-wide section stays unchanged.
- [ ] Commit: `skills: fold spring trigger vocabulary into review-wide java checks`

### Task 6: Route the compatibility witness and neutralize the risk-signal floor

Files:
- `agents/skills/review-agents/review-panel-selection.md`

- [ ] In the tiered ownership table, insert this row directly after the `Missing or weak test` row: `| Missing compatibility witness for changed direct dependency API usage (\`java_guidelines\` #24) | \`correctness-completeness\` | \`implementation\` |`
- [ ] Replace the two-sentence risk-signal floor tail (from `Treat changed dependency coordinates,` through `changed files are Java or Spring configuration.`) with: `Treat changed dependency coordinates, outbound service URL configuration, and downstream error-response mapping as risk signals even when the diff is small. The shared changed-scope trigger surfaces enumerated in the \`doing-code-review\` Step 2.5 mandatory-evidence rules are risk signals as well. These signals require the \`risk\` worker and the guideline checks of the changed files' language overlay (Java/Spring, Kotlin/Spring, or Python) per those mandatory-evidence rules.`
- [ ] Commit: `skills: route compatibility witness ownership and neutralize risk floor surfaces`

### Task 7: Wire the widened evidence rules into the execute-plan Phase 3 gates

Files:
- `agents/skills/execute-plan/SKILL.md`

- [ ] Replace the Step 3.1 item 2 Java/Spring bullet with: `For plans whose changed scope is covered by a language overlay, require the Guideline Pack paths and applied rule hints that the \`doing-code-review\` Step 2.5 mandatory-evidence rules require for that overlay: Java rules #16 through #25 for Java/Spring plans; for Kotlin/Spring and Python plans, the rules the overlay trigger tables map to the changed scope. The shared changed-scope trigger surfaces are enumerated once in Step 2.5 and are not restated here. Record \`Java guideline checks: #<rules>\` (or \`Kotlin guideline checks: #<rules>\` / \`Python guideline checks: #<rules>\`) in staging Metadata; a path-only listing without applied rule hints is not sufficient for a clear round.`
- [ ] At the end of Step 3.4 quality bar item 4 (after the Java evidence-list sentence ending `when those surfaces are present.`), append: `For Kotlin/Spring or Python plans, the staging Metadata likewise records the overlay guideline paths and applied rule hints per Step 2.5, and the review evidence covers the evidence surfaces of the applied hints.`
- [ ] In Step 3.4 quality bar item 6, extend the ledger field list so it reads: `(missing capability and owner, unsafe current path and configuration, permitted deployment mode, shippability condition, classification, accepted-residual rationale)`.
- [ ] Commit: `skills: wire overlay guideline evidence into phase 3 gates and ledger rationale`

### Task 8: Final validation sweep

Files: none (verification only).

- [ ] Run the Validation Commands block from the repo root; expect exit 0 with `VALIDATION PASS: review coverage pass 2 wiring complete`.
- [ ] No commit; verification only.
