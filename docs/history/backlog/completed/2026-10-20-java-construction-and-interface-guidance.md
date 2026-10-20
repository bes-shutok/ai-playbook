# Backlog: make Java construction and interface placement conventions explicit

Status: done (covered by docs/history/plans/completed/2026-10-20-java-construction-and-interface-conventions.md, executed and landed 2026-10-20)
Priority: high
Class: fix-class (missing reusable convention and review coverage; no new blocking gate)
Origin class: consumer-feedback (company)
Consumer urgency: consumer projects that run the Java review skill need this guidance; the skills-repo personal priority profile must not park or defer it as formal-hardening for the skills repo alone.
Driving force: maintainability + simplicity

## Skill and step

`projects/.ai-playbook/java_guidelines.md` (shared Java convention source); `agents/skills/doing-code-review/java-spring.md` (Java review overlay); `agents/skills/review-agents/architecture.md` and `agents/skills/review-agents/simplification.md` (review lenses).

## Observed versus expected

Observed: in a consumer Java pull request, the operator requested that constructors with more than three parameters use builders to make object creation readable, and that interfaces be declared as separate top-level types rather than nested inside another type. The implementation review needed a manual sweep of every created or changed class and record to apply the construction convention. Existing shared Java guidance does not define the parameter threshold or interface placement rule, and the Java review overlay does not ask reviewers to check either. The simplification lens currently lists builder patterns for simple constructions as unnecessary chaining without a boundary for larger constructions, so it can conflict with the requested rule. A sibling project's Lombok examples provided useful precedent for builder-based creation of data and model objects, while also exposing the need to state how the rule applies to framework-injected constructors.

Expected: establish one shared Java source of truth that requires readable builder-based construction when a constructor has more than three parameters, including a clear Lombok pattern where available; clarify the treatment of Spring-managed dependency-injection constructors so the implementation preserves framework construction; and require interfaces to be top-level types. Add review checks that inspect every added or changed Java class, record, interface, constructor, and relevant call site. Reconcile the simplification lens so it continues to flag unnecessary builders for small/simple constructions without contradicting the larger-constructor rule. Keep `agents-best-practices` provider-neutral: it supplies the feedback-loop principle, while the Java convention belongs in the language guide and review overlay.

## Evidence

Session evidence: a consumer-project PR task required a pass over all created or changed Java classes and records for constructors with more than three parameters, with builder-based construction requested for readability; the operator also identified top-level interface placement as a convention worth codifying. Inspection of the current Java guideline, Java review overlay, architecture lens, and simplification lens found no matching rule or review check, and found the unqualified simple-builder heuristic described above. A sibling project was consulted for Lombok builder usage. Environment: repo copy of the skills and guidelines, interactive session, 2026-10-20. Source reference: user/operator direction in the current session and the preceding consumer PR review; project and PR identifiers intentionally omitted.

Severity and source reference: maintainability / review consistency; operator-requested convention surfaced during a consumer code-change session (2026-10-20).

## Suggested fix

Add the normative rules to `projects/.ai-playbook/java_guidelines.md`, with a decision on Spring constructor-injection handling and examples for multi-parameter records/classes. Add concise review checks to the Java overlay and architecture/simplification lenses, and point them to the shared guideline rather than duplicating its full wording. Review the applicable guideline pack / staging rule hints so Java reviews actually receive the new checks. Keep the instruction concise and judgment-based; do not add a blocking validator unless a later implementation demonstrates a reliable low-noise mechanical check.

## Why not fixed now

This session was asked to analyze instruction-corpus coverage and file backlog work, not to change and validate the shared coding and review guidance. The conventions need a coordinated update across the canonical Java guide and its consumers, including a precise resolution for dependency-injection constructors.

## Dedup probe

Searched open backlog filenames and problem text for builder/constructor parameter thresholds, nested or top-level interfaces, and Java review convention coverage. No open item owns these conventions. The nearest Java backlog mentions builder-shaped helper code only as an implementation detail of a review-record producer; it does not concern Java construction readability or interface placement. Keep this as one item because the same consumer session exposed missing Java guidance and corresponding review coverage, and the guide and its reviewer checks should land together.

Capture hygiene: scan-public-hygiene --files pass.
