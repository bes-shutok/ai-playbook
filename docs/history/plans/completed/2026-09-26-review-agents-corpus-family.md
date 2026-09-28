# Plan: Review-agent corpus boundary and parity miss-family upgrades

Backlog origins (scope of record):
- docs/history/backlog/2026-09-21-review-framework-and-runner-contracts.md
- docs/history/backlog/2026-09-21-review-panel-terminal-path-and-boundary-contract-coverage.md
- docs/history/backlog/2026-09-18-review-agents-miss-dual-surface-parity-conversion-floors-comment-inventories.md

Driving force: external + code-quality (external primary: consumer-project failure feedback captured in the three origin items, where external reviews caught the miss classes after full internal panels approved the same diffs, and the origins carry consumer urgency with never profile-defer; code-quality secondary: the deliverable is review-corpus coverage quality. Justification for a non-principle force: correctness, the origins' own motivator, is not in the closed taxonomy, and park-triage would not defer this work because it closes witnessed, recurring miss classes rather than adding speculative machinery.)

Plan review record: the staging series docs/reviews/2026-09-26-plan-review-review-agents-corpus-family-r*.md (the highest rN is the authoritative record, including the deferred-residual list); the review loop was closed by operator decision on 2026-09-26

## Outcome

Give the review-agent lenses eight new door patterns for miss classes that external reviews kept catching after internal panels approved the same diffs.

- Review lenses catch the witnessed consumer-review miss classes (policy parity across surfaces, truncating conversion floors, relocatable identifier inventories, boundary residuals) instead of waving them through.
- The new doors are wired into overlay, staging metadata, severity rows, and panel selection, so they fire in real reviews rather than living as documentation.
- Consumer projects running the shared review corpus stop re-importing defects that an internal panel already should have caught.


## Terms

- **Miss family / miss class**: an abstract review-gap pattern witnessed on consumer projects, named without product identifiers.
- **Lens (worker)**: one review-agent specialization under `agents/skills/review-agents/` (quality, testing, architecture, concurrency, implementation, documentation, security, consistency).
- **Door pattern**: a fail-closed review rule declared exactly once as `Pattern: `<lens>#<kebab-id>`` in its owning lens file and registered in `scripts/test_review_agent_doors.py`; the `Pattern:` declaration lives in the host file that owns the section while the lens prefix records the conceptual owner; `concurrency` is a legacy-only sidecar owner, so Task 4's security-owned id is the first fully declared security-owned door hosted in concurrency.md (the file's existing security-owned ids are inline stage references, not declared doors).
- **Boundary-contract checklist**: the review-metadata obligation from the Boundary-contract coverage floor in `agents/skills/review-agents/review-panel-selection.md`.
- **Guideline Pack**: the shared guidelines bundle under `projects/.ai-playbook/` (`java_guidelines.md`, `jvm_guidelines.md`, `coding_guidelines.md`) that workers open on demand.
- **Staging sidecar**: the `.stats.json` companion of a review staging record under `docs/reviews/`.

## Assumptions

- One plan covers all three origins as one family on the shared review-agents surface; basis: authoring directive 2026-09-26 (user decision).
- Landed coverage is extended by cross-pointers only; exactly three sanctioned lens-corpus edits are sanctioned: Task 3's replacement of the deferral sentence inside the prose-delivery-slice-meta paragraph (the door's asserted tokens stay untouched), Task 3's one carve-out clause appended to the Severity (phase 2) Default Low paragraph together with the reword of its adjacent 4.9.0-citation sentence and Do-not-assign-Medium+ sentence so both reference the carve-out and the new severity-calibration row, and Task 4's one-phrase floor-family extension; adding new items to landed sections is sanctioned and existing item text stays otherwise untouched; Design Invariant 1 is the single source of this sanction rule and its scope (the section-level enumerations formerly recorded here were non-exhaustive and are deliberately gone); basis: the directive's "extend, never re-implement" plus the coverage map below, each row verified against the lens files on the base commit.
- New pattern ids follow the `<lens>#<kebab-id>` convention with exactly one `Pattern:` declaration each; basis: repo convention enforced by `scripts/test_review_agent_doors.py`.
- `jvm_guidelines.md` #18 (Duration truncation floor), `jvm_guidelines.md` #20 (drop perpetual absent-path asserts after a rename), and `coding_guidelines.md` #35 (relocatable identifiers in comments) are cited by section number, never restated; basis: all three sections verified present in the Guideline Pack files.
- The new staging Metadata line joins the when-applicable Review context list, not the `EXTENDED_SIDECAR_MIN_DATE` mechanically-required freshness set; basis: the review-staging SKILL.md Metadata section structure.
- Corpus insertions stay stack-portable; basis: the AGENTS.md standing gates (portability scan, door registry selftest); the shared-body runtime-neutrality test is an execute-plan suite regression gate whose bodies this plan does not change.

Decision points requiring a grill: dual-surface pattern home (architecture.md vs quality.md): decided architecture.md per the origin's suggested pattern name architecture#dual-surface-policy-parity, source standing pre-authorization 2026-09-26, affects Task 1; optional panel-selection targeted follow-up trigger (origin marks it optional): included, source standing pre-authorization accept-recommended-options 2026-09-26, affects Task 1.

## Gist & Examples

TLDR: review-agent lenses gain eight new door patterns plus overlay, staging, severity, and panel-selection wiring for the witnessed miss classes, because external reviews kept catching them after internal panels approved the same diffs (driving force: external + code-quality).

The three origins describe the same failure mode at three surfaces: an internal panel approves a diff, a later external review finds a defect class the panel never staged, and the fix lands downstream. This plan wires each witnessed class into the review-agent corpus so the panel itself stages it next time. The coverage map pins what already landed (extend-only; never restate): the new tasks add only the missing classes and the wiring between them.

Coverage map (landed on the base commit; extend-only):

| Witnessed shape (abstract) | Landed home |
|---|---|
| Framework API against resolved dependency, compile evidence, selector-to-verifier parity, effective source trace | `implementation.md` Framework and effective-configuration contract audit (`implementation#framework-contract-unverified`) |
| Disabled or empty safety tests, migration shared consumers, targeted-vs-full runner populations | `testing.md` Safety-boundary and runner witness requirements (`testing#runner-contract-unverified`) |
| Boundary checklist, explicit not-applicable disposition, risk-signal recording | `review-panel-selection.md` Boundary-contract coverage floor + review-staging Metadata `Changed-risk signals` |
| Logging render surfaces: cause chains, unknown objects, arbitrary strings, source plus value policy | `security.md` Fail-closed logging and configuration boundaries (`security#logging-render-surface-unchecked`) |
| Terminal, fallback, rejection, batch path matrix; completion witness; task-vs-decision completion | `concurrency.md` Ownership and decision matrix |
| Closed transition table, first-write-wins, complete-tuple re-read after races, CLAIMED merge | `concurrency.md` Persistent state-machine race matrix |
| Paired-record self-source normalization, multi-fact fan-out enumeration, duration-zero binding | `quality.md` Representation precision and fan-out completeness |
| Changed-code family inventory with explicit not-applicable | `testing.md` Changed-code family inventory |
| Typed catalog enumeration door | `quality#typed-catalog-enumeration-door` (landed in 8e3872e6) |

New in this plan, with abstract examples:

1. **Dual-surface policy parity** (`architecture#dual-surface-policy-parity` + `testing#cross-surface-policy-witness`): the same deny policy lives at two entry points, one matching exact tokens, the other a substring marker; direct callers of the weaker surface bypass the strict gate. Workers enumerate every entry point claiming the policy, diff predicate shapes, prefer one shared helper, and stage a finding when duplication remains without per-surface failing witnesses.
2. **Truncating conversion floor** (`implementation#truncating-conversion-floor`): a validated positive sub-second duration truncates to zero whole units before a sink where zero means unlimited; validation saw positive, the sink saw zero. Workers trace validation to conversion to sink and reject converted values below the sink's minimum meaningful unit.
3. **Relocatable identifier inventories** (`documentation#prose-relocatable-identifier-inventory`): a header comment restates versioned filenames the same diff also lists as mounts; a renumber updates the path and leaves the comment stale. The gate prefers delete plus pointer to the owning artifact, and severity calibration promotes a same-diff contradiction to Medium operability drift.
4. **Boundary residuals**: nullable mapper parameter without an explicit JDBC type (`quality#nullable-jdbc-type`); first-write-wins claim predicates using SQL equality against a NULL-initialized audit tuple (`security#null-tuple-claim-predicates`); packaged local artifact carrying an older schema or seed ordering than the canonical migration set (`implementation#packaged-schema-parity`); an auto-detected test extension discovering containers before deciding the class needs none (`testing#container-discovery-fast-path`).

## Evaluation Criteria

**Quality dimensions:**

- Extend-not-duplicate: no lens insertion restates or contradicts a landed rule named in Design Invariants; reviewer diffs each insertion against that list.
- Registry integrity: every new pattern id declared exactly once in its host lens file, registered in `scripts/test_review_agent_doors.py` with its required actions; the selftest exits 0.
- Portability and neutrality: `check_review_agent_portability.py` exits 0 over the changed lens files; the shared-body runtime-neutrality test exits 0 as an execute-plan regression guard.
- Abstract-only corpus text: no product, service, ticket, PR, hostname, or environment identifiers in lens or overlay insertions (origin non-goals).
- Schema consistency: the staging validator selftest exits 0 with the new Metadata line documented.

**Done when:**

- All eight new pattern ids are present in their owning lens files and the door registry selftest passes with the new declaration tests.
- Both Spring overlays carry the `jvm_guidelines.md` #18 hint; the documentation lens carries the `coding_guidelines.md` #35 pointer; the deferral sentence that reserved the relocatable-inventory class is replaced by the live-gate pointer.
- severity-calibration.md carries the same-diff inventory row as the explicit override of the Documentation Low default, with the matching carve-out in documentation.md; review-staging SKILL.md documents the `Boundary-contract checklist` Metadata line and template line; the floor family list names packaged deployment artifact parity and the Java overlays carry the transaction-manager begin-hook rule.
- The full Validation Commands block exits 0 from the repository root, including the hygiene and em-dash scans over the changed set.

**Ship when:**

- Consumer-project reviews run the upgraded lenses on real diffs; effectiveness is witnessed by future corpus feedback (external findings in these families stop recurring), not by this repo's checks. This is prose, not a checklist item.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (review-agent corpus and wiring):**

- `agents/skills/review-agents/architecture.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/concurrency.md`
- `agents/skills/review-agents/implementation.md`
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/severity-calibration.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/doing-code-review/java-spring.md`
- `agents/skills/doing-code-review/kotlin-spring.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`

**Tests:**

- `scripts/test_review_agent_doors.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `projects/.ai-playbook/jvm_guidelines.md` and `projects/.ai-playbook/coding_guidelines.md`; reason: the pointed-at rules (#18, #20, #35) already exist; this plan only cites them.
- `README.md`; reason: no skill name, path, or usage change; lens files are internal to the review-agents and doing-code-review skills.
- The three origin backlog files under `docs/history/backlog/`; reason: origins stay in place while the plan is open; disposition folds at completion per the plans lifecycle, not in a task.
- `claude/skills` mirror; reason: it is a symlink to `../agents/skills`, lens edits flow through with no second landing.

## Residual review findings

The review loop was closed by operator decision on 2026-09-26. The staging series under docs/reviews/ for this slug is the authoritative review record; its highest-numbered round carries the full account of every finding and this section carries only the round-free residual list. Deferred residuals carried against this plan's tasks:

- Task 3 Severity (phase 2): the carve-out clause and the 4.9.0-citation reword sub-edits are pinned only partially (the shared operability-drift span is also satisfied by the Do-not-assign-Medium+ reword text); land both sub-edits and verify each by its own distinct span.
- Task 3: the absence-grep on the old Do-not-assign-Medium+ phrasing forces deletion of the landed combined-issue allowance; a future editor may narrow the forbidden span to the old sentence's opening so the allowance can survive beside the carve-out.
- Task 2: the kotlin JVM guideline note carries no staging-recording clause (the trigger table's recording contract does not cover it); a future editor should add a file-qualified recording line.
- Task 4: the packaged-parity boundary sentence partitions documentation phase-1's remit more narrowly than the landed text; a future editor should reword it as a non-absorption boundary and re-point the pinned span.
- Task 5: the new Metadata line's value vocabulary (`populated` | `not applicable (no boundary families)`) is unpinned; a future editor should add the value-span needle.
- Task 4: two declaration-test parentheticals drift comma-wise from their corpus bullets; a future editor should assert token-level spans (matching the landed tests' style).

Executor note: any edit to this plan invalidates the latest review digest and requires a fresh review round before finalization; this section intentionally carries no round state so that requirement stays the only review-coupled constraint in these bytes.

## Design Invariants (CR Guard)

1. **Extend, never re-implement.** Do not restate, edit, or contradict these landed rules (all verified on the base commit): `quality#typed-catalog-enumeration-door`, `testing#helper-path-retarget-after-door`, `documentation#prose-delivery-slice-meta`, the Framework and effective-configuration contract audit (`implementation#framework-contract-unverified`), the Safety-boundary and runner witness requirements (`testing#runner-contract-unverified`), the Boundary-contract coverage floor, the Fail-closed logging and configuration boundaries (`security#logging-render-surface-unchecked`), the Ownership and decision matrix, the Persistent state-machine race matrix, Representation precision and fan-out completeness, and the Changed-code family inventory. New content only adds the missing classes and cross-pointers; adding new items to landed sections is sanctioned and existing item text stays otherwise untouched, except exactly three sanctioned edits: Task 3 replaces the deferral sentence in the prose-delivery-slice-meta paragraph with a pointer to the new subsection (the door's asserted tokens plan-slice identity, ticket key, and behavior-facing stay untouched), Task 3 appends one carve-out clause to the Severity (phase 2) Default Low paragraph and must reword the adjacent 4.9.0-citation sentence and the Do-not-assign-Medium+ sentence so both reference the carve-out and the new severity-calibration row, and Task 4 extends the floor's family list by one phrase; Task 3 additionally amends the doing-code-review section 4.9.0 Documentation bullet (the severity contract the lens corpus points at). The count is exactly three sanctioned lens-corpus edits plus this one sanctioned consumer-doc edit outside the lens-corpus sanction scope.
2. **Exactly one declaration per id.** Each new id carries exactly one `Pattern: `<lens>#<id>`` declaration; the door registry selftest's exactly-once assertion is load-bearing and must keep passing. A pattern id must never be restated anywhere else in its owning lens file, including cross-pointers: `pattern_window` fails on total mentions, not only on duplicate declarations.
3. **Lens portability.** Shared lens files stay stack-agnostic; language-specific mechanics (Duration APIs, transaction-manager hook types) live in the `doing-code-review` overlays, with lens text naming the overlay handoff.
4. **Abstract examples only.** No service names, ticket ids, PR numbers, hostnames, or payload inventories in corpus insertions (origin non-goals); generic marker examples such as identifier-shaped compound tokens are fine.
5. **Additive staging documentation.** The new `Boundary-contract checklist` Metadata line documents an existing panel obligation; it must not join the date-gated mechanically-required freshness set and must not invalidate existing records that lack it.

## Validation Commands

Authoring-time record: the block executed from the repository root on the base tree fails first at the per-file presence grep for `architecture#dual-surface-policy-parity` (exit 1 from the `fail` helper), which is the expected RED-today state; every earlier gate (door registry selftest on the landed patterns, portability, shared-body neutrality, staging validator selftest) passes on the base tree. The block flips green exactly when Tasks 1 through 5 land.

```bash
#!/usr/bin/env bash
# Run from the repository root. Fail closed: any missed obligation aborts non-zero.
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

# Standing review-agents gates (AGENTS.md).
python3 scripts/test_review_agent_doors.py > /dev/null || fail "door registry selftest"
python3 scripts/check_review_agent_portability.py > /dev/null || fail "review-agent portability scan"

# Execute-plan shared bodies: regression guard only (this plan does not change
# them); the portability scan carries neutrality for the changed set.
( cd scripts && python3 -m unittest \
  test_execute_plan_runtime.ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral ) \
  > /dev/null || fail "shared-body runtime neutrality"

# Staging validator stays consistent with the documented Metadata line.
python3 scripts/validate_review_staging.py --selftest > /dev/null || fail "staging validator selftest"

# Each new pattern id present in its owning lens file. The doors selftest owns
# exactly-once declarations and required actions; these per-file greps pin
# per-file presence so one file's success cannot mask a missing sibling.
# The loop reads a herestring (not a pipeline) so a failing check aborts the
# whole block instead of only the loop's subshell.
ID_FILES="
agents/skills/review-agents/architecture.md architecture#dual-surface-policy-parity
agents/skills/review-agents/testing.md testing#cross-surface-policy-witness
agents/skills/review-agents/testing.md testing#container-discovery-fast-path
agents/skills/review-agents/quality.md quality#nullable-jdbc-type
agents/skills/review-agents/concurrency.md security#null-tuple-claim-predicates
agents/skills/review-agents/implementation.md implementation#truncating-conversion-floor
agents/skills/review-agents/implementation.md implementation#packaged-schema-parity
agents/skills/review-agents/documentation.md documentation#prose-relocatable-identifier-inventory
"
while read -r file id; do
  test -n "$file" || continue
  test -f "$file" || fail "missing lens file $file"
  grep -qF "$id" "$file" || fail "$id absent from $file"
done <<< "$ID_FILES"

# The door registry's new declaration tests must exist: the selftest enforces
# their content, but only this count pin ensures they were written at all.
test "$(grep -c 'def test_.*_declared' scripts/test_review_agent_doors.py)" -eq 12 \
  || fail "door registry declaration tests missing (four landed plus eight new)"
grep -qF '### Relocatable identifier inventory gate' agents/skills/review-agents/documentation.md \
  || fail "relocatable inventory gate heading pin missing"
grep -qF 'dual-entry' scripts/test_review_agent_doors.py \
  || fail "panel-signal test extension missing the dual-entry branch"

# Overlay and shared-guideline pointers.
grep -qF 'jvm_guidelines.md` #18' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring overlay lacks the jvm_guidelines #18 hint"
grep -qF 'jvm_guidelines.md` #18' agents/skills/doing-code-review/kotlin-spring.md \
  || fail "kotlin-spring overlay lacks the jvm_guidelines #18 hint"
grep -qF 'coding_guidelines.md` #35' agents/skills/review-agents/documentation.md \
  || fail "documentation lens lacks the coding_guidelines #35 pointer"
grep -qF 'jvm_guidelines.md` #20' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring overlay lacks the jvm_guidelines #20 hint"
grep -qF 'jvm_guidelines.md` #20' agents/skills/doing-code-review/kotlin-spring.md \
  || fail "kotlin-spring overlay lacks the jvm_guidelines #20 hint"
grep -qF 'not only after an incident' agents/skills/doing-code-review/kotlin-spring.md \
  || fail "kotlin JVM note lacks the every-review scope clause"
kotlin_table_line="$(grep -n '## Guideline trigger table' agents/skills/doing-code-review/kotlin-spring.md | head -1 | cut -d: -f1)"
kotlin_jvm_line="$(grep -n 'jvm_guidelines.md` #18' agents/skills/doing-code-review/kotlin-spring.md | head -1 | cut -d: -f1)"
test -n "$kotlin_table_line" && test -n "$kotlin_jvm_line" && [ "$kotlin_jvm_line" -gt "$kotlin_table_line" ] \
  || fail "kotlin JVM guideline note not placed after the trigger table"
grep -qF 'operability drift' agents/skills/review-agents/documentation.md \
  || fail "documentation lens lacks the severity carve-out"
grep -qF 'stages Medium operability drift per the severity-calibration Category defaults row' agents/skills/review-agents/documentation.md \
  || fail "Do-not-assign-Medium+ reword not landed"
grep -qF 'except the same-diff relocatable-inventory contradiction class' agents/skills/doing-code-review/SKILL.md \
  || fail "doing-code-review 4.9.0 lacks the severity deference"
DOC_LENS_SEV=agents/skills/review-agents/documentation.md
grep -qF 'unless combined with a separate correctness or contract issue' "$DOC_LENS_SEV"
sev_rc=$?
if [ "$sev_rc" -eq 0 ]; then fail "Do-not-assign-Medium+ sentence not reworded to reference the carve-out"; fi
if [ "$sev_rc" -ge 2 ]; then fail "grep error scanning documentation.md severity paragraph"; fi
grep -qF 'peer documentation' agents/skills/review-agents/documentation.md \
  || fail "documentation lens lacks the stale-semantics sweep line"
grep -qF 'stay with consistency.md' agents/skills/review-agents/documentation.md \
  || fail "documentation lens lacks the consistency boundary note"
grep -qF 'See the Relocatable identifier inventory gate' agents/skills/review-agents/documentation.md \
  || fail "prose-delivery paragraph lacks the prescribed pointer sentence"
grep -qF 'packaged deployment artifact parity' agents/skills/review-agents/review-panel-selection.md \
  || fail "panel floor family list lacks packaged parity"
grep -qF 'post-begin' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring overlay lacks the begin-hook rule"
grep -qF 'post-begin' agents/skills/doing-code-review/kotlin-spring.md \
  || fail "kotlin-spring overlay lacks the begin-hook mirror"
grep -qF 'applies to any such sink' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring hint lacks the any-such-sink scope clause"
grep -qF 'applies to any such sink' agents/skills/doing-code-review/kotlin-spring.md \
  || fail "kotlin JVM hint lacks the any-such-sink scope clause"
grep -qF 'java_guidelines.md` #18' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring lost the landed java_guidelines #18 hint"
grep -qF 'java_guidelines.md` #20' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring lost the landed java_guidelines #20 hint"
grep -qF 'release or recovery procedure' agents/skills/review-agents/severity-calibration.md \
  || fail "severity row lacks the promote-to-High clause"
grep -qF 'not only after an incident' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring hint lacks the every-review scope clause"
grep -qF 'framework callback' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring begin-hook rule lacks the callback-handle clause"
grep -qF 'superclass' agents/skills/doing-code-review/java-spring.md \
  || fail "java-spring begin-hook rule lacks the superclass-audit clause"
grep -qF 'framework callback' agents/skills/doing-code-review/kotlin-spring.md \
  || fail "kotlin begin-hook mirror lacks the callback-handle clause"
grep -qF 'superclass' agents/skills/doing-code-review/kotlin-spring.md \
  || fail "kotlin begin-hook mirror lacks the superclass-audit clause"
test "$(grep -cF 'Boundary-contract checklist' agents/skills/review-staging/SKILL.md)" -ge 2 \
  || fail "review staging needs both the metadata entry and the template line"

# Severity row, staging Metadata line, panel trigger.
grep -qF 'operability drift' agents/skills/review-agents/severity-calibration.md \
  || fail "severity calibration lacks the same-diff inventory row"
grep -qF 'migration renumber' agents/skills/review-agents/review-panel-selection.md \
  || fail "panel selection lacks the renumber and dual-entry follow-up trigger"
grep -qF 'per tiered ownership' agents/skills/review-agents/implementation.md \
  || fail "conversion floor boundary sentence missing"
conc_permit_line="$(grep -n 'concurrency#permit-finally' agents/skills/review-agents/concurrency.md | head -1 | cut -d: -f1)"
conc_null_line="$(grep -n 'security#null-tuple-claim-predicates' agents/skills/review-agents/concurrency.md | head -1 | cut -d: -f1)"
test -n "$conc_permit_line" && test -n "$conc_null_line" && [ "$conc_null_line" -gt "$conc_permit_line" ] \
  || fail "null-tuple item not appended after the race matrix tail"
grep -qF 'bootstrap-mount updates stay owned by' agents/skills/review-agents/implementation.md \
  || fail "packaged parity boundary sentence missing"

# Positive pin: the replacement pointer exists (subsection heading plus the
# pointer sentence; the pattern id string itself must stay single-mention).
test "$(grep -icF 'relocatable identifier inventory' agents/skills/review-agents/documentation.md)" -ge 2 \
  || fail "prose-delivery-slice-meta paragraph lacks the live-gate pointer"

# The deferral sentence that reserved this class must be gone once the gate
# lands. Zero-match is the pass condition, so the sweep negates explicitly and
# splits grep exit codes (0 forbidden, 1 clean, >=2 tool error).
DOC_LENS=agents/skills/review-agents/documentation.md
test -f "$DOC_LENS" || fail "missing $DOC_LENS"
grep -qF 'deferred relocatable identifier-inventory class' "$DOC_LENS"
grep_rc=$?
if [ "$grep_rc" -eq 0 ]; then fail "stale deferral sentence still present in documentation.md"; fi
if [ "$grep_rc" -ge 2 ]; then fail "grep error scanning documentation.md"; fi

# Corpus insertions stay hygiene-clean and em-dash-free. The em-dash scan runs
# with CHECK_NO_EM_DASH_ALL=1 because the default prose filter silently skips
# the .py target.
bash scripts/scan-public-hygiene.sh || fail "public hygiene scan"
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file \
  agents/skills/review-agents/architecture.md \
  agents/skills/review-agents/testing.md \
  agents/skills/review-agents/quality.md \
  agents/skills/review-agents/concurrency.md \
  agents/skills/review-agents/implementation.md \
  agents/skills/review-agents/documentation.md \
  agents/skills/review-agents/severity-calibration.md \
  agents/skills/review-agents/review-panel-selection.md \
  agents/skills/doing-code-review/java-spring.md \
  agents/skills/doing-code-review/kotlin-spring.md \
  agents/skills/review-staging/SKILL.md \
  agents/skills/doing-code-review/SKILL.md \
  scripts/test_review_agent_doors.py || fail "em-dash scan"

echo "VALIDATION OK"
```

### Task 1: Dual-surface policy parity door, cross-surface witness, panel trigger

Files:
- `agents/skills/review-agents/architecture.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `scripts/test_review_agent_doors.py`

- [x] Add `test_dual_surface_policy_parity_declared` to `scripts/test_review_agent_doors.py`: assert the `architecture#dual-surface-policy-parity` window carries the trigger (a deny or allow policy enforced at more than one public entry point), the predicate-shape compare (exact equality versus contains or prefix; normalization steps; shared versus duplicated constant sets), the shared-helper preference, and the per-surface witnesses alternative (tests prove both surfaces reject the same representative inputs) plus the asymmetry-examples span (passes exact match but fails contains); add `test_cross_surface_policy_witness_declared`: assert the `testing#cross-surface-policy-witness` window requires at least one failing witness per surface when a shared helper enforcing one policy is mutated to the weaker shape; extend the panel-signal test to assert the targeted follow-up trigger names a migration renumber and a dual-entry validation-policy change forcing contract-docs plus correctness-completeness, and additionally design-simplicity plus testing on the dual-entry branch. Run `python3 scripts/test_review_agent_doors.py`; expect RED (declarations absent). [class: REPOSITORY_TEST]
- [x] `architecture.md`: add a `## Dual-surface policy parity` section near the pattern-violation sections with the trigger verbatim (a deny or allow policy enforced at more than one public entry point, such as a parser, validator, filter, gateway, or batch importer), the three-step worker action (enumerate every entry point claiming the policy; compare predicate shapes (exact equality versus contains or prefix; normalization steps; shared versus duplicated constant sets); prefer one shared helper, otherwise stage a finding unless tests prove both surfaces reject the same representative inputs, citing the asymmetry examples: a compound token that passes exact match but fails contains, and the reverse), and the declaration `Pattern: `architecture#dual-surface-policy-parity``. The embedded language-agnostic examples satisfy origin 3's worker self-test acceptance criterion; plan justification, not landing text. [class: IMPLEMENTATION_REQUIRED]
- [x] `testing.md`: add the cross-surface witness obligation to the Test Quality area (at least one failing witness per surface when a shared helper enforcing one policy is mutated to the weaker shape; shared helper preferred over duplicated predicates), with the declaration `Pattern: `testing#cross-surface-policy-witness``. [class: IMPLEMENTATION_REQUIRED]
- [x] `review-panel-selection.md`: add one targeted follow-up bullet with two branches: after a migration renumber, force the contract-docs and correctness-completeness workers on the paired surfaces even in a focused round; after a dual-entry validation-policy change, additionally force the design-simplicity and testing workers so the architecture and testing lenses load the new doors. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/test_review_agent_doors.py`; expect GREEN for the new declarations with the landed ones untouched. [class: REPOSITORY_TEST]
- [x] Run `bash scripts/scan-public-hygiene.sh` and `python3 scripts/check_review_agent_portability.py`; expect exit 0 before committing. [class: REPOSITORY_TEST]
- [x] Commit: `skills: dual-surface policy parity door with cross-surface witness and panel trigger` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Truncating conversion floor wiring (implementation lens plus Spring overlays)

Files:
- `agents/skills/review-agents/implementation.md`
- `agents/skills/doing-code-review/java-spring.md`
- `agents/skills/doing-code-review/kotlin-spring.md`
- `scripts/test_review_agent_doors.py`

- [x] Add `test_truncating_conversion_floor_declared` to `scripts/test_review_agent_doors.py`: assert the `implementation#truncating-conversion-floor` window carries the span trace validation, conversion, sink, the rejection of values whose converted integer is below the sink's minimum meaningful unit even when the source value is positive, and the citation of the shared JVM guideline when present in the Guideline Pack. Run the selftest; expect RED. [class: REPOSITORY_TEST]
- [x] `implementation.md`: add a `## Conversion floor before zero-meaning sinks` section near the framework audit (trigger: validated config or API duration or numeric quantity rendered through a truncating conversion into a sink documented or known to treat zero as unlimited, disabled, or no-limit; required action: trace validation, conversion, sink; reject values whose converted integer is below the sink's minimum meaningful unit even when the source value is positive; cite the shared JVM guideline when present in the Guideline Pack), with the declaration `Pattern: `implementation#truncating-conversion-floor``; include one boundary sentence: quality.md's landed Representation precision rule owns the emitted-representation witness for the duration-zero shape, while this door owns the validation-to-conversion-to-sink trace, the sub-floor rejection, and the guideline citation; merge per tiered ownership; the boundary sentence must carry the exact phrase per tiered ownership so the Validation Commands grep pins it. [class: IMPLEMENTATION_REQUIRED]
- [x] `java-spring.md` Review-wide Java checks: add two hint lines: one citing `jvm_guidelines.md` #18 (floor `Duration.toMillis()` and every other truncating conversion before sinks that treat zero as unlimited or disabled; the rule applies to any such sink, not only the guideline's named timeout sink), and one citing `jvm_guidelines.md` #20 (drop perpetual "old migration path is null" asserts after a rename); both rules are applied on every Java review, not only after an incident. [class: IMPLEMENTATION_REQUIRED]
- [x] `kotlin-spring.md`: add a separate short note outside the Guideline trigger table (a file-qualified JVM guideline checks line after the table, so the table's kotlin_guidelines index resolution is not conflated) carrying the `jvm_guidelines.md` #18 pointer and the `jvm_guidelines.md` #20 pointer, with #18 carrying the same any-such-sink scope clause as the java hint, and the note stating both rules are applied on every Kotlin review, not only after an incident. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/test_review_agent_doors.py`; expect GREEN. [class: REPOSITORY_TEST]
- [x] Run `bash scripts/scan-public-hygiene.sh` and `python3 scripts/check_review_agent_portability.py`; expect exit 0 before committing. [class: REPOSITORY_TEST]
- [x] Commit: `skills: truncating conversion floor door and Spring overlay pointers` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Relocatable identifier inventory gate and severity promotion

Files:
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/severity-calibration.md`
- `agents/skills/doing-code-review/SKILL.md`
- `scripts/test_review_agent_doors.py`

- [x] Add `test_prose_relocatable_identifier_inventory_declared` to `scripts/test_review_agent_doors.py`: assert the `documentation#prose-relocatable-identifier-inventory` window carries identifiers that also appear as real paths, mounts, or resource names in the same diff, the delete-plus-pointer preference, the rewrite-only-when-sole-operator-contract exception, and the `coding_guidelines.md` #35 alignment. Run the selftest; expect RED. [class: REPOSITORY_TEST]
- [x] `documentation.md` phase 2: add the relocatable identifier inventory gate subsection, titled verbatim "Relocatable identifier inventory gate", with the replacement sentence naming that title (trigger: an added or changed comment or operator-doc line lists versioned filenames, migration ids, enum ordinals, or other identifiers that also appear as real paths, mounts, or resource names in the same diff; required action: prefer delete plus pointer to the owning artifact; rewrite only when the comment is the sole operator contract and cannot point elsewhere) with the declaration `Pattern: `documentation#prose-relocatable-identifier-inventory``, citing `coding_guidelines.md` #35 as the shared rule it wires, with that citation landing immediately after the required-action sentence, before the boundary statement, so it stays inside the declaration window; the subsection text also states its boundary to the landed Outdated documentation dispositions: for relocatable-inventory contradictions this gate's delete-plus-pointer disposition replaces the generic same-diff fix-in-place normal path of the Outdated documentation section's current-change disposition, and that section continues to own non-inventory stale prose. In the prose-delivery-slice-meta paragraph, replace the sentence that calls the relocatable identifier-inventory class deferred and not merged with a pointer to the new subsection; the replacement sentence reads "See the Relocatable identifier inventory gate for the live gate." and never restates the pattern id (the registry's window check fails on any second mention of the id in this file). [class: IMPLEMENTATION_REQUIRED]
- [x] `documentation.md` phase 2, section "Outdated documentation: remove or freeze": add one line to that section's duty: when a null, omission, or empty-object contract changes, search canonical and peer documentation for statements of the old semantics and stage stale-semantics findings; note the boundary that contradictions between two normative statements stay with consistency.md; the Validation Commands grep pins this boundary span. [class: IMPLEMENTATION_REQUIRED]
- [x] `severity-calibration.md` Category defaults: add a row for a comment or operator-doc inventory contradicting a path in the same diff: default Medium (operability drift; operators follow the named file), promote to High when the stale inventory gates a release or recovery procedure; phrase the row as the specific override of both the Documentation / inline comment Low default and the Document calibration rule that document inconsistency alone is Low, for this same-diff contradiction class. [class: IMPLEMENTATION_REQUIRED]
- [x] `documentation.md` phase 2 "Severity (phase 2)": add one carve-out clause to the Default Low paragraph naming the same-diff relocatable-inventory contradiction as operability drift staged Medium per the new severity-calibration row; reword the sentence citing doing-code-review section 4.9.0 so the citation reads through the carve-out rather than against it; reword the adjacent Do-not-assign-Medium+ sentence to read that prose findings stage Low except the same-diff relocatable-inventory contradiction class, which stages Medium operability drift per the new severity-calibration row, so the section no longer unconditionally forbids the staged Medium. [class: IMPLEMENTATION_REQUIRED]
- [x] `doing-code-review/SKILL.md` section 4.9.0: amend the Documentation bullet to defer on this class, mirroring the Metrics bullet's deference pattern: documentation and inline-comment asks are Low, except the same-diff relocatable-inventory contradiction class, which defaults Medium per the severity-calibration Category-defaults row. This consumer-doc edit is the fourth sanctioned edit; it sits outside the lens-corpus sanction scope. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/test_review_agent_doors.py`; expect GREEN. [class: REPOSITORY_TEST]
- [x] Run `bash scripts/scan-public-hygiene.sh` and `python3 scripts/check_review_agent_portability.py`; expect exit 0 before committing. [class: REPOSITORY_TEST]
- [x] Commit: `skills: relocatable identifier inventory gate with Medium operability drift severity` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Boundary-contract residual doors (origins one and two)

Files:
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/concurrency.md`
- `agents/skills/review-agents/implementation.md`
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/doing-code-review/java-spring.md`
- `agents/skills/doing-code-review/kotlin-spring.md`
- `scripts/test_review_agent_doors.py`

- [x] Add four declaration tests to `scripts/test_review_agent_doors.py`: `quality#nullable-jdbc-type` (a nullable mapper parameter or bound value requires an explicit JDBC type for the SQL NULL case plus a test exercising the null representation), `security#null-tuple-claim-predicates` (first-write-wins predicates over a NULL-initialized audit tuple use IS NULL per field in the fresh-claim branch because SQL equality never matches NULL, with fresh-claim, identical-retry, and conflicting-retry witnesses), `implementation#packaged-schema-parity` (packaged deployment and local-development manifests compared against the canonical migration and seed inventory including ordering), and `testing#container-discovery-fast-path` (an auto-detected test extension decides the non-container fast path before any container discovery; container probes on classes needing no container are a runner defect). Run the selftest; expect RED. [class: REPOSITORY_TEST]
- [x] `quality.md` Representation precision and fan-out completeness: add the nullable JDBC item (a nullable mapper parameter or bound value requires an explicit JDBC type for the SQL NULL case, plus a test exercising the null representation) with the declaration `Pattern: `quality#nullable-jdbc-type``. [class: IMPLEMENTATION_REQUIRED]
- [x] `concurrency.md` Persistent state-machine race matrix: append to the Persistent state-machine race matrix list, after the first-write-wins item's family and without renumbering existing items, the NULL-tuple claim predicate item (SQL three-valued logic for first-write-wins audit tuples, because SQL equality never matches NULL; IS NULL per field in the fresh-claim branch; fresh-claim, identical-retry, and conflicting-retry witnesses), with the declaration `Pattern: `security#null-tuple-claim-predicates``. [class: IMPLEMENTATION_REQUIRED]
- [x] `implementation.md`: add the packaged-schema parity item near the Same-change-set inventory section (compare packaged deployment and local-development manifests against the canonical migration and seed inventory, including ordering) with the declaration `Pattern: `implementation#packaged-schema-parity``; include one boundary sentence: verify-script expected inventories stay owned by implementation.md's Same-change-set inventory section, and missing ops-doc or bootstrap-mount updates stay owned by documentation.md phase 1's Ops / local bootstrap inventory. [class: IMPLEMENTATION_REQUIRED]
- [x] `testing.md` Safety-boundary and runner witness requirements: add the container-discovery fast-path item (an auto-detected test extension decides the non-container fast path before any container discovery; container probes on classes needing no container are a runner defect) with the declaration `Pattern: `testing#container-discovery-fast-path``. [class: IMPLEMENTATION_REQUIRED]
- [x] `review-panel-selection.md` Boundary-contract coverage floor: extend the family list by one phrase so packaged deployment artifact parity joins migration and runner parity as a named family; change no other sentence. [class: IMPLEMENTATION_REQUIRED]
- [x] `java-spring.md`, section "## Spring-Specific Concerns", as a new bullet after the `@Transactional` propagation item: add the transaction-manager begin-hook rule (treat framework callback arguments as framework-specific handles and verify their runtime type before invoking rollback or cleanup; audit the superclass cleanup contract when extending begin hooks; on post-begin setup failure, roll back and unbind the already-bound resource before propagating). [class: IMPLEMENTATION_REQUIRED]
- [x] `kotlin-spring.md`, section `## Spring + Kotlin Integration`: add a new bullet with the begin-hook mirror (the same Spring mapping as `java-spring.md`, per the harness-fidelity mirror precedent): framework callback handles, superclass cleanup audit, post-begin failure rollback and unbind. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `python3 scripts/test_review_agent_doors.py`; expect GREEN for all four new declarations. [class: REPOSITORY_TEST]
- [x] Run `bash scripts/scan-public-hygiene.sh` and `python3 scripts/check_review_agent_portability.py`; expect exit 0 before committing. [class: REPOSITORY_TEST]
- [x] Commit: `skills: boundary residual doors for jdbc typing, null tuples, packaged parity, container fast path` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Staging audit-result recording

Files:
- `agents/skills/review-staging/SKILL.md`

- [x] Add a `Boundary-contract checklist` entry to the Review context Metadata list: `populated` | `not applicable (no boundary families)`, required when the Boundary-contract coverage floor triggers (changed scope touches one of its boundary families); add the matching line to the Metadata template near the `Changed-risk signals` line. Do not modify the `EXTENDED_SIDECAR_MIN_DATE` freshness set or any sidecar schema key. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `test "$(grep -cF 'Boundary-contract checklist' agents/skills/review-staging/SKILL.md)" -ge 2`; expect RED before the Metadata edit and GREEN after it. [class: REPOSITORY_TEST]
- [x] Run `python3 scripts/validate_review_staging.py --selftest`; expect GREEN (the additive Metadata line must not invalidate records lacking it). [class: REPOSITORY_TEST]
- [x] Run `bash scripts/scan-public-hygiene.sh`; expect exit 0 before committing. [class: REPOSITORY_TEST]
- [x] Commit: `skills: stage boundary-contract checklist audit result in review metadata` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Full gate set

Files: none (verification only)

- [x] Run the complete `## Validation Commands` block from the repository root; expect exit 0, including the hygiene and em-dash scans over the changed set. [class: REPOSITORY_TEST]

## Origins disposition (fold-then-delete, archive commit 2026-09-27)

- docs/history/backlog/2026-09-21-review-framework-and-runner-contracts.md: DONE. Every acceptance criterion is landed: framework-API/resolved-dependency and selector-to-verifier parity were already live (implementation#framework-contract-unverified, testing#runner-contract-unverified, both verified on the base commit per the coverage map); the container-discovery fast path and disabled-safety-test classes landed via Task 4 (testing#container-discovery-fast-path, testing.md Safety-boundary area); the staging-schema audit recording landed via Task 5 (Boundary-contract checklist Metadata line). Origin file deleted in the archive commit.
- docs/history/backlog/2026-09-21-review-panel-terminal-path-and-boundary-contract-coverage.md: DONE. Suggested fixes 4, 9, 14, 19/24, and 27 landed via Tasks 3 and 4 (quality#nullable-jdbc-type, implementation#packaged-schema-parity, the documentation.md stale-semantics sweep with the consistency.md boundary, the Spring overlay begin-hook rules, security#null-tuple-claim-predicates); the remaining shapes (terminal paths, logging render surfaces, provenance, CLAIMED merge, completion witness, changed-code family inventory, multi-fact fan-out) were landed before this plan and are pinned by its coverage map. Boundary-contract recording (acceptance criterion) landed via Task 5. Origin file deleted in the archive commit.
- docs/history/backlog/2026-09-18-review-agents-miss-dual-surface-parity-conversion-floors-comment-inventories.md: DONE. The plan's core miss families landed via Tasks 1-3 (architecture#dual-surface-policy-parity + testing#cross-surface-policy-witness, implementation#truncating-conversion-floor with overlay pointers, documentation#prose-relocatable-identifier-inventory with the Medium operability-drift severity chain). Origin file deleted in the archive commit.

Execution record: executed 2026-09-27 by the scheduled dispatch session (branch 2026-09-27-execute-review-agents-corpus-family, squash-merged to main); plan re-certified post plans-home relocation by review-plan r10 (ready=yes, zero blocking; the only delta vs the r9-reviewed bytes was the Outcome section insertion); Phase 3 code review r1 full panel zero blocking (4 accepted fixes), r2 residual address pass, r3 exit round zero blocking; three deferred-findings backlog items filed under docs/history/backlog/2026-09-27-review-agents-corpus-family-*.
