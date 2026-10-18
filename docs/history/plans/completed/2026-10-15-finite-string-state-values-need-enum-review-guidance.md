# Plan: one canonical rule for repeated finite string state vocabularies

Authoring claim: docs/tmp/authoring-claims/2026-10-14-finite-string-state-values-need-enum-review-guidance.md (session sess_5c51c846-299a-4dfe-a00c-4238d7883663)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-14-finite-string-state-values-need-enum-review-guidance.md

Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/*-plan-review-finite-string-state-values-need-enum-review-guidance-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h

## Terms

- Finite semantic vocabulary: a small closed set of string values carrying shared semantic meaning, supplied at multiple producer call sites or across an API boundary, where the valid set is not discoverable from the type.
- Candidate test: the rule's conditional admission test: a closed semantic set with one natural owning module, repeated call sites or an API boundary, and explicit mapping where an external string representation must be preserved.
- Compatibility-bound string: a string whose external representation is fixed by an owning contract (persistence schema, wire format, configuration key, SQL literal) and must not change without that owner's authorization.
- Canonical rule: the single numbered rule this plan adds to the JVM guidelines file of the Guideline Pack as rule 27, holding the candidate test, the boundary-mapping requirement, and the counterexamples.
- Guideline Pack: the in-repository projects/.ai-playbook/ directory of shared cross-project guidelines; the user-facts guideline home resolves to this repository's main checkout via symlink, so consumer-visible delivery completes when this branch merges.
- Review overlay: the existing Java/Spring review guidance overlay (agents/skills/doing-code-review/java-spring.md), whose Review-wide Java checks list gains the rule as a group sibling.
- Applied-rules entry: one check line in the overlay's Review-wide Java checks list, in the sibling style of its existing jvm_guidelines.md entries, naming the rule by number and title without restating its text.
- Origin row: the backlog row listed under Backlog origins (scope of record); the plan's source of evidence and its disposition target.
- Source project: the repository where the origin row's producer API and its enum replacement live; re-derived at execution time from the authoring session record named in this plan's Authoring claim header, with an operator-supplied identity as the named fallback, never named inside ai-playbook artifacts.
- Census: the execution-time enumeration of the source project's Java/Spring modules for repeated finite semantic vocabularies that violate the canonical rule, reported per the user-level rule that a new standard must audit its current codebase.

## Why

Reviewers miss finite semantic state values expressed as repeated string literals: the origin records a producer API that accepted arbitrary strings for a small closed outcome set, with the same outcome spelled independently at multiple call sites, so the valid set was undiscoverable from the type and spelling drift went unflagged. The JVM guideline pack covers enum import and mapping style, not recognition, and the review overlay covers enum usage, not when repeated strings represent a closed semantic domain.

## Gist & Examples

TLDR: adds one numbered JVM guideline rule that tells reviewers when repeated strings are a finite semantic vocabulary deserving one owning enum with explicit boundary mapping, and adds it to the Java/Spring review overlay's applied-rules list, so the origin's witnessed recognition gap closes without new machinery; declared force code-quality, motivated by the origin's spelling-drift incident.

Before: the candidate test exists nowhere; a reviewer auditing the origin's producer API had no written boundary between semantic outcome states and compatibility-bound strings, and the same outcome label was re-supplied independently at multiple call sites.
After: the JVM guidelines carry one rule with the candidate test, the explicit-mapping requirement at string boundaries, and counterexample classes (free-form text, one-off labels, persistence, wire, configuration, SQL literals); the review overlay applies the rule on every Java/Spring review beside its existing JVM entries; the source project census runs at execution and reports violations without changing application code.
Edge cases: a repeated string that is a compatibility surface stays a string and is conforming; a closed set with a single call site and no API boundary fails the candidate test; a module that already owns a covering enum makes the finding "use the existing enum", never "add another".

## Outcome

One guidance rule and its review-consumer entry, nothing else.
- The JVM guidelines file carries the canonical rule as its next numbered rule, with the candidate test, the boundary-mapping requirement, and at least three counterexample classes.
- The Java/Spring review overlay applies the rule on every review beside its existing JVM entries, and its count sentence keeps the list honest.
- The execution census reports the source project's violations and conforming counterexamples in the execution report; application code is not altered by this plan.
- The origin row flips covered at this plan's landing and is deleted at execution completion in a closing change conditioned on the census disposition, with the disposition named as the deletion's witness per the commit guideline.

Gate delta: none; no gate, refusal, validator, panel, schema field, or fence is added, removed, or re-aimed; the change is guidance text plus its review-consumer entry, so the Machinery admission protocol is not triggered and no registry row is needed; the Task 3 census is a declared external survey whose disposition gates only the closing change's witness, and its operator-parked-row arm prevents any paused work.

## Assumptions

- assume the canonical home is the JVM guidelines file of the in-repository Guideline Pack rather than a language-specific guideline file; basis: the pack owns the numbered JVM rule family the overlay already applies (its #12, #18, #20 entries), the origin's evidence is JVM-flavored (Java/Spring, enum vocabulary), and the language files keep language-only rules.
- assume one rule, not a family: the candidate test, the mapping requirement, and the counterexamples fit one numbered rule; basis: the origin's "smallest suitable placement" direction and its rejection of widening to all repeated string literals.
- assume the review consumer change is an applied-rules list entry, not a duty: no new review step, panel, or validator; basis: the origin's rejected direction and the Machinery admission protocol's no-incident-no-gate rule.
- assume the census is execution-scoped and report-only: the plan defines the census method and acceptance, execution re-derives the source-project identity from the authoring session record with an operator-supplied fallback, the origin row's related-work context supplies module scope and disambiguating evidence only, and identifiers stay out of ai-playbook artifacts; basis: the entry prompt's keep-identifiers-out clause and the origin row's own generic wording.
- assume existing enum mapping guidance (the guideline files and the overlay's existing entries) stays byte-unchanged except the added rule, the added entry, and the mandated count-sentence update; basis: constraint preservation, the origin's Evidence caution against mechanical conversion, and no origin direction authorizing removal of existing guidance.
- assume a module that already owns an enum covering the vocabulary makes the finding "use the existing enum"; basis: the origin's check-existing-types-before-adding-another requirement.

Decision points requiring a grill: canonical home read as the JVM guidelines file with the overlay entry, not a language guideline file or a new review duty: resolved by the pack's existing numbered-rule family and the admission protocol's no-incident-no-gate rule, 2026-10-15, affected sections: Terms, Task 1, Task 2; census posture read as report-only execution work rather than in-plan code edits: resolved by the entry prompt's do-not-alter-application-code constraint, 2026-10-15, affected sections: Terms, Task 3, Standing constraints.

## Standing constraints

- No application code changes: the plan edits guidance and review references only; the census reports violations and changes nothing in the source project.
- No new machinery: no validator, panel, review duty, gate, or schema; the overlay entry is an applied check, not a new enforcement layer.
- Single-homing: the rule text lives once in the JVM guidelines file; the overlay entry names it and does not restate it.
- Identifier hygiene: no source-project names, module names, or literals from the origin's evidence appear in any ai-playbook artifact.
- Vendored sync discipline: each changed skill file lands its runtime twin in the same run or leaves the tracked vendored-sync landing path naming the changed files.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the candidate test's conditions match the origin's evidence, and its counterexamples cover every compatibility class the origin names.
- single-homing: the rule text exists exactly once; the overlay entry names it without restating it.
- measurability: each deliverable has a grep-able anchor; the census reports counts, not adjectives.
- constraint preservation: existing enum guidance and the overlay's existing entries keep their bytes except the additions this plan makes.

**Done when:**
- The JVM guidelines file carries the canonical rule as its next numbered rule.
- The Java/Spring review overlay applies the rule on every review, with its count sentence updated.
- The census procedure is defined with its report shape, and the origin row's disposition is carried.

**Ship when:**
- none; this plan is repository-internal guidance with no external release surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- none; the plan adds no executable code.

**Documentation:**
- `projects/.ai-playbook/jvm_guidelines.md` (the new numbered rule)
- `agents/skills/doing-code-review/java-spring.md` (the applied-rules entry and count sentence)

**Backlog rows (disposition):**
- `docs/history/backlog/2026-10-14-finite-string-state-values-need-enum-review-guidance.md` *(deleted at execution completion; covered flip at landing)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, or reconciles a cross-reference the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- converting persistence, wire, configuration, SQL, or free-text strings to enums; reason: compatibility contracts are the rule's own counterexamples.
- widening the rule to all repeated string literals; reason: the origin's recorded rejected alternative.
- removing or rewriting existing enum mapping guidance; reason: constraint preservation; no origin direction authorizes removal, and existing guidance stays byte-unchanged.
- extending the applied-rules entry to the kotlin-spring overlay; reason: recorded consumer-scope decision, java-only on the origin's Java/Spring evidence; the kotlin overlay picks the rule up through its own JVM guidance when a consumer needs it.
- any validator, review duty, panel, or gate; reason: no witnessed incident requires machinery, per the Machinery admission protocol.

## Validation Commands

```bash
( cd "$(git rev-parse --show-toplevel)" && bash ~/.ai-playbook/scripts/scan-public-hygiene.sh )
( cd "$(git rev-parse --show-toplevel)" && test "$(grep -c 'jvm_guidelines.md' agents/skills/doing-code-review/java-spring.md)" -eq 6 )
( cd "$(git rev-parse --show-toplevel)" && test "$(grep -c '^## 27\.' projects/.ai-playbook/jvm_guidelines.md)" -eq 1 )
( cd "$(git rev-parse --show-toplevel)" && test "$(grep -c 'These four' agents/skills/doing-code-review/java-spring.md)" -eq 1 )
```

Validation preamble (rule 29 record): the pre-round structural gate runs before round 1; the authoring-time em-dash fixer pass and the public-hygiene scan (exit 0) are recorded at authoring. The command block pins three regression-guard spans per rule 22's regression-guard carve-out, each measured RED-today at authoring and GREEN after the change: the overlay's jvm_guidelines.md reference count is 5 today and must be 6 after the applied-rules entry lands; the guideline file carries zero `## 27.` headings today and exactly one after; the count sentence reads "These three" today and "These four" after. The pins suite's documented baseline failures live outside this plan's surfaces and are unchanged by it.

The hygiene scan is the repository-side witness for repository conventions; the three counted greps are the discriminating change witnesses, and Task 2's Run adds the single-homing negative check and the cross-file citation check.

### Task 1: the canonical rule in the JVM guidelines file

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `projects/.ai-playbook/jvm_guidelines.md`

- [x] The JVM guidelines file carries the canonical rule as rule 27 (the file's numeric maximum is an existing out-of-document-order #26 at its head region, so 27 is the next number; the new rule appends after the #25 heading at file end), titled for recognition (a repeated finite string vocabulary gets one owning enum), with the admission test given the explicit name "candidate test" and stated as the rule's admission shape [class: IMPLEMENTATION_REQUIRED]
- [x] The rule requires one owning enum in the natural owning module, checked against existing types before a new enum is added, and requires explicit mapping at any boundary whose external string representation must be preserved (metric tags, serialization) [class: IMPLEMENTATION_REQUIRED]
- [x] The rule names its counterexample classes: free-form text, one-off labels, and compatibility-bound strings (persistence schema, wire format, configuration key, SQL literal), each conforming as a string unless its owning contract authorizes a type change [class: IMPLEMENTATION_REQUIRED]
- [x] The rule carries one compact code-shaped example contrasting a conforming semantic outcome vocabulary with a conforming compatibility-bound persistence literal, with no source-project identifiers [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect exactly one grep hit for `^## 27\.` in the JVM guidelines file carrying the rule title, and before the change the count was zero (measured at authoring); expect the authored rule body to carry the explicit name "candidate test" and one distinctive span each of the boundary-mapping requirement and the counterexample classes, each exactly once after the change and zero before [class: REPOSITORY_TEST]
- [x] Run → before the commit step, re-read the authored rule and its example against the origin row's related-work context and confirm zero shared identifiers, where the origin's outcome-label literals and its module, project, and domain-specific names count as shared identifiers while Java language keywords and the rule's own subject words do not; invent fresh outcome labels for the example, recording the confirmation line in the execution report [class: REPOSITORY_TEST]
- [x] Commit: `docs: add finite string vocabulary recognition rule to JVM guidelines` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the applied-rules entry in the Java/Spring review overlay

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/doing-code-review/java-spring.md`

- [x] The overlay's Review-wide Java checks list gains one entry for the new rule in its existing jvm_guidelines.md group, in the sibling style of its existing entries, citing the rule by number and title (jvm_guidelines.md rule 27, "candidate test" named as the admission shape) and compressing what to check (repeated string arguments forming a closed semantic vocabulary) to a hint, with no restatement of the rule text [class: IMPLEMENTATION_REQUIRED]
- [x] The list's closing count sentence updates from three applied jvm_guidelines.md rules to four, so the list cannot drift against itself [class: IMPLEMENTATION_REQUIRED]
- [x] Each skill file in this task's Files list carries the same change to its vendored twin in the same run, or the change leaves the tracked vendored-sync landing path naming the changed files [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the overlay's jvm_guidelines.md reference count to rise from 5 (measured at authoring) to 6, the count sentence to name four, and the repository hygiene scan exit 0 over the changed set [class: REPOSITORY_TEST]
- [x] Run → expect exactly one hit for the new rule number in the overlay's checks list, exactly one hit for the candidate test name in the overlay's checks list, and the same rule number 27 resolving in the JVM guidelines file with the rule title [class: REPOSITORY_TEST]
- [x] Run → expect zero overlay matches for a distinctive span of the admission test's condition clauses (the closed-set, repeated-call-site, owning-module, or boundary-mapping conditions, never the shape's own name the entry is required to carry), so the entry cannot silently restate the rule [class: REPOSITORY_TEST]
- [x] Commit: `docs: apply finite string vocabulary rule on Java Spring reviews` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the source-project census arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none for the census itself; the execution-completion closing change deletes docs/history/backlog/2026-10-14-finite-string-state-values-need-enum-review-guidance.md (disposition, see Review Scope).

- [x] Execution re-derives the source-project identity from the authoring session record named in this plan's Authoring claim header as the census's first action, with an existence check and an operator-supplied identity as the named fallback when the record cannot resolve it, and states the identity in the execution report only, never in ai-playbook artifacts [class: IMPLEMENTATION_REQUIRED]
- [x] The census enumerates repeated string-literal parameters and fields in a bounded sweep: any modules identifiable from the authoring session record's related-work detail or the origin row's related-work context, else the stated-depth survey alone, with the report stating its coverage (modules swept versus total) and its enumeration method (scan pattern and module scope) [class: IMPLEMENTATION_REQUIRED]
- [x] Each census cluster is classified by the candidate test with per-cluster verdicts (violation, conforming counterexample, or existing-enum reuse) and counts reported in the execution report [class: IMPLEMENTATION_REQUIRED]
- [x] The census is read-only over the source project: no file writes, no builds, no tool invocations that mutate its working tree, scratch confined to the session workspace; the census changes no source file, and per-cluster reports cite file-and-line anchors with counts and verdicts instead of embedding literal values verbatim, redacting credential-shaped strings by pattern class [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the census report present in the execution report with at least the origin row's witnessed cluster classified, or a named blocker that states what was searched (candidate projects and the disambiguating evidence drawn from the origin row's related-work context) when the source project cannot be located [class: REPOSITORY_TEST]
- [x] Commit: the census itself produces no commit in this repository; at execution completion, a closing change in this repository deletes the origin row, conditioned on the witnessed cluster being classified or on a filed operator-parked follow-up row keeping the audit debt tracked when it cannot be, with the census disposition named as the deletion's witness per the commit guideline [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect at execution completion that either the origin row path is absent with the deletion condition evidenced (the execution report's census section carries the witnessed cluster with a verdict, or the operator-parked follow-up row exists in this repository's backlog) and the disposition named as the witness, or the row is present with the closing change withheld and the execution report names the parked follow-up decision [class: REPOSITORY_TEST]

## Execution completion disposition

Executed 2026-10-15 by the maintenance exec lane (session sess-maint-finitestring-20261015). Tasks 1-3 complete; Phase 2 validation all four commands GREEN; Phase 3 exec review r1 blocking 0 across three lenses (record: .ai-playbook/reviews/2026-10-15-plan-review-finite-string-state-values-need-enum-review-guidance-exec-r1.md). Rule 27 landed in projects/.ai-playbook/jvm_guidelines.md; applied-rules entry landed in agents/skills/doing-code-review/java-spring.md with the count sentence at four. Task 3 census classified the witnessed cluster (typed enum complete, zero remaining arbitrary-String call sites) and reported 1 violation cluster, 6 conforming counterexamples, 2 existing-enum reuse findings for the source project, read-only. Origin row deleted at execution completion per Review Scope, conditioned on the census disposition and witnessed by it.
