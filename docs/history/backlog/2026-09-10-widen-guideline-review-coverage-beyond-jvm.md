# Backlog: widen guideline-driven review coverage beyond the JVM overlay

Status: open
Priority: deferred (efficiency/token/simplicity triage 2026-09-11: process-cosmetic or archived-record value only; revisit only if it starts costing real review rounds or tokens)

Workflow: backlog
Source: author follow-up to the strengthen-jvm-review-coverage backlog item (2026-09-10): review coverage symmetry for non-Java overlays and the wider guideline corpus
Severity: Medium overall; individual gaps range from Low to Medium by reachability
Class: review-cycle coverage hardening

## Problem

The strengthen-jvm-review-coverage change hardens Java/Spring reviews with
mandatory shared guideline paths, trigger-based numbered rule hints, and
applied-rule-hint staging evidence. The same evidence wiring does not exist
for the other overlays or for the rest of the guideline corpus:

1. Kotlin/Spring and Python reviews load their shared guideline files through
   the existing overlay map (`kotlin_guidelines.md`, `python_guidelines.md`,
   plus `jvm_guidelines.md` / `coding_guidelines.md`), but nothing makes
   application mandatory or provable. A Kotlin or Python staging record can
   pass with a path-only listing, while a Java record cannot.
2. The mandatory-evidence paragraph in the doing-code-review Guideline Pack
   section ("incomplete unless... rule hints... staging metadata must record
   the applied hints") is written for Java only. There is no Kotlin or Python
   equivalent naming numbered rules per diff trigger.
3. The Kotlin and Python corpora (`kotlin_guidelines.md` rules 1-22,
   `python_guidelines.md` rules 1-25) contain code rules but no review-cycle
   coverage rule family analogous to `java_guidelines.md` rules 16-25
   (changed-source declaration census, boundary-state enumeration, untrusted
   downstream payloads, dependency audits, transport-boundary enforcement,
   and the five rules the certified JVM plan adds).
4. Company and project guideline files are attached as a pair for
   company-scoped workspaces, but only their attachment is recorded. No
   applied-rule-hint evidence is required for them, so a staging record
   cannot prove the company or project rules were consulted.
5. The review-panel-selection risk-signal floor cross-references the
   Java/Spring guideline checks by name; Kotlin and Python have no
   equivalents (for example coroutine-cancellation and pytest-fixture signals
   that should pull the testing worker's corpus hints).
6. execute-plan Phase 3 hint ranges and the clear-round quality bar item 4
   name Java evidence classes; Kotlin/Python equivalents are absent.

## Location

- `agents/skills/doing-code-review/SKILL.md`, Guideline Pack mandatory-evidence paragraph and overlay map
- `agents/skills/doing-code-review/kotlin-spring.md`, rule-hint triggers into `kotlin_guidelines.md`
- `agents/skills/doing-code-review/python.md`, rule-hint triggers into `python_guidelines.md`
- `agents/skills/review-agents/review-panel-selection.md`, risk-signal floor
- `agents/skills/execute-plan/SKILL.md`, Phase 3 hint ranges and clear-round quality bar
- `projects/.ai-playbook/kotlin_guidelines.md`, `projects/.ai-playbook/python_guidelines.md`, potential review-coverage rule families

## Suggested fix

Keep the five-worker panel and the existing overlay map, and mirror the JVM
treatment for the remaining surfaces:

- Add a per-language mandatory-evidence paragraph: a Kotlin/Spring pack is
  incomplete without `kotlin_guidelines.md`, `jvm_guidelines.md`, and
  `coding_guidelines.md` paths plus trigger-based rule hints; a Python pack
  without `python_guidelines.md` and `coding_guidelines.md` paths plus hints.
  Staging metadata must record the applied rule hints per overlay; a
  path-only listing is not evidence of application.
- Define trigger tables per language from diff signals, resolvable from each
  corpus's own numbered index (examples, not exhaustive: Kotlin coroutines,
  MockK tests, `@ConfigurationProperties`, data-class boundaries; Python
  pytest fixtures and monkeypatching, asyncio, dependency pins, logging).
- Decide per corpus whether a review-cycle coverage rule family is needed
  beyond the wiring, using evidence classes from prior Kotlin and Python
  review cycles as the arbiter; do not precommit to new numbered rules
  without that evidence.
- Extend the applied-rule-hint evidence requirement to attached
  `company_guidelines_master` and `project_guidelines_rel` files, with hints
  selected from their own indexes when present.
- Make the risk-signal floor and clear-round quality-bar wording
  language-neutral where the underlying check is language-neutral, and name
  per-language equivalents where it is not.

## Acceptance

- A Kotlin/Spring or Python Phase 3 staging record with a path-only guideline
  listing is rejected by the clear-round gate, exactly as Java records are.
- Trigger tables exist for the kotlin-spring and python overlays and name
  numbered rules resolvable from each corpus's own index.
- Staging metadata records applied rule hints for every attached guideline
  file (language, JVM-shared, coding, company, project), not only Java.
- The risk-signal floor and the quality-bar evidence list no longer read as
  Java-only; each non-Java overlay has named equivalents or an explicit
  not-applicable note.
- A generic fixture or self-test demonstrates each new check without real
  service names, credentials, customer data, ticket identifiers, or internal
  URLs.
- The widening change builds on the post-execution state of
  strengthen-jvm-review-coverage; no file is edited by both changes in
  flight.

## Why not fixed now

The certified strengthen-jvm-review-coverage plan (authored 2026-09-10,
execution pending) owns the same files: the doing-code-review Guideline Pack
section, review-panel-selection risk signals, and execute-plan Phase 3
wording. Editing those surfaces before that plan executes would collide with
an in-flight certified change. This item records the symmetry gap so the
widening can be authored as its own skills-repo change once the JVM plan
lands, folded with it if execution has not started.
