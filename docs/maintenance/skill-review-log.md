# Weekly skill-review aggregates

## Run 1 (2026-11-01, cold start, rotation_cursor 0 -> 46)

- Combined corpus: 50 skill directories + 19 maintenance Markdown files + 205 open backlog rows = 274 units; batch size ceil(274/6) = 46; cursor range 0-45; the batch is the 46 skill directories agents-best-practices through tdd-guide (lexicographic, vendored `synced/` excluded from the rotation).
- Reviewers: 2 read-only sub-agents (cap respected); token budget recorded at the state record (350000); findings advisory.

### Diagnostic summaries (read-only, data, never failures)

- Em dash scan (364 corpus files via `scripts/check-no-em-dash.sh stdin`, exit 1 carrying findings): 12 hit lines total, split 1 known + 11 new. Known: `agents/skills/agterm/reference.md:868` (the documented quoted app refusal literal, owned by docs/history/backlog/2026-10-27-emdash-residuals-open-rows-and-literal.md). New (path:line): `docs/maintenance/development_lessons.md:5225`; `docs/history/backlog/2026-10-23-dead-run-conversion-coverage-residuals.md:14`; `docs/history/backlog/2026-10-23-machinery-inventory-baseline-red-obscures-regrowth.md:11`; `docs/history/backlog/2026-10-27-self-heal-done-push-reply-authorization-separation.md:4`; `docs/history/backlog/2026-10-28-message-class-description-trim.md:6`; `docs/history/backlog/2026-10-31-doc-registry-row-edit-validator-timing.md:13`; `docs/history/backlog/2026-10-31-gate-removal-stranded-drained-migration-destination.md:1`; `docs/history/backlog/2026-10-31-machinery-witness-stem-substring-false-pass.md:7`; `docs/history/backlog/2026-10-31-review-record-producer-clean-round-constraints.md:1`; `docs/history/backlog/2026-11-01-skill-text-caps-key-ordering.md:5`; `docs/history/backlog/2026-11-01-worktree-first-reaim-residual-sites.md:7`.
- Duplication report (`scripts/skill_text_duplication.py agents/skills/ docs/maintenance/`): OUTCOME: pass; headline: cross-file repeated-span intersections concentrated in agents-best-practices (SKILL.md vs references/source-links.md 147, provider-api-patterns.md 62, security-observability.md 43, skills-and-connectors.md 38, mvp-agent-blueprint.md 24, coding-agents.md 7; references agentic-loop.md vs mvp-agent-blueprint.md 22); data for the class-2 cluster below.
- Byte-budget report (`scripts/skill_text_budget.py --check`, warning-only): 1 breach (`agents/skills/maintenance/template-authoring.md` 44270 bytes > cap 42066), 8 caps gaps (incl. `agents/skills/self-heal/SKILL.md`, `agents/skills/unit-test-runner/maven.md`), 6 pilot-over modules (all under `agents/skills/maintenance/`: decisions.md, failure-cap.md, guards.md, scheduling.md, state-file.md, survey-arms.md), 0 pilot-pending; OUTCOME: pass.

### Semantic findings (49 total; advisory, never applied by this run)

Half 1 (agents-best-practices through investigate), 27 findings:

1. overcomplication | agents/skills/bootstrap-ai-playbook/SKILL.md:44 | recovery-rerun exception guards a hypothetical composition into an unbounded-rerun branch; compress to the plain re-ask-once rule.
2. repetition | agents/skills/bootstrap-ai-playbook/SKILL.md:129,191 | worktree_root arm sentence stated verbatim in optional-keys table and interview; keep interview, point the table.
3. repetition | agents/skills/bootstrap-ai-playbook/SKILL.md:152,182 | company_projects_root resolves-under rule stated twice; single-home in the interview.
4. repetition | agents/skills/bootstrap-ai-playbook/SKILL.md:40,42 | missing-profile-surface routing stated in two adjacent paragraphs; delete the duplicate.
5. repetition | agents/skills/bootstrap-ai-playbook/SKILL.md:153 + doc-hierarchy/SKILL.md:140 + doc-hierarchy-migrate/SKILL.md:152 | greenfield compose rationale restated in three files; keep in bootstrap, link from the others.
6. repetition | agents/skills/doc-hierarchy/SKILL.md:121,123 | audit-note override lifecycle fully stated twice in one file; keep one home.
7. repetition | agents/skills/doc-hierarchy/SKILL.md:146 | integration row spells out done's standing-note duty semantics; compress to a pointer.
8. repetition | agents/skills/doc-hierarchy-upkeep/SKILL.md:27,30 | laptop-vs-ops rule restated against its canonical home; keep one pointer.
9. repetition | agents/skills/doing-code-review/SKILL.md:219,400,537,541 | actionable-fix snippet contract stated four times; keep 4.9.0, reference the rest.
10. repetition | agents/skills/doing-code-review/SKILL.md:424,444 | private-style-preferences rule nearly verbatim twice; single-home.
11. repetition | agents/skills/doing-code-review/SKILL.md:19,54,193,220 | diff-capture rule stated four times, all citing canonical 50.3.2; keep Diff access.
12. repetition | agents/skills/doing-code-review/SKILL.md:809 | integration row restates graded comment-only re-bind mechanics execute-plan says to point at; reduce to pointer.
13. repetition | agents/skills/doing-code-review/SKILL.md:406 + github-pr-workflow/SKILL.md:329 | never-cite-gitignored-docs rule in two unreferenced homes; cross-link.
14. repetition | agents/skills/execute-plan/SKILL.md:587,885,887 | dispatch_failed format, pre_restart pair, reason-code set stated three times; single-home in Launch Rules.
15. repetition | agents/skills/execute-plan/SKILL.md:274,866 | execution-claim protocol summary restated in Queue-drain continuation; replace with pointer.
16. repetition | agents/skills/execute-plan/SKILL.md:866 + done/SKILL.md:169 | sanctioned inter-plan turn-end list duplicated verbatim across skills with no owner; pick one home.
17. repetition | agents/skills/execute-plan/SKILL.md:401 + runtime-contract.md:96 | stack-task entry-point contract stated in both with no ownership marker; declare runtime-contract normative.
18. repetition | agents/skills/execute-plan/SKILL.md:717 | clear-round quality bar re-enumerates the canonical evidence surfaces doing-code-review declares single; point to it.
19. repetition | agents/skills/execute-plan/SKILL.md:224,226 | primary-placement arm restates Worktree-first semantics consumers must reference not restate; compress.
20. repetition | agents/skills/execute-plan/SKILL.md:344,373,375 | telemetry destination and add-only preservation stated three times; drop the paragraph copy.
21. controversy | agents/skills/confluence-page-sync/SKILL.md:89,96,103,105 | cross-references name publication rules 4/5 one item off the actual list (stale numbering after an insertion); renumber.
22. repetition | agents/skills/confluence-page-sync/SKILL.md:21,43,44,45,46 | one-rendering-per-Mermaid-diagram rule stated five times; keep two, point the rest.
23. repetition | agents/skills/docs-branch/SKILL.md:17,26,46,99 | restore-only-after-successful-sync rule stated four times; keep the invariant, point the rest.
24. repetition | agents/skills/docs-branch/SKILL.md:17,24,46,98,108 | never-touch-local-tmp rule stated five times; keep one line plus the Integration Point.
25. repetition | agents/skills/grill-with-docs/SKILL.md:17 | workflow restates grilling clauses as a third unmanaged copy outside the sync-note protection; compress to per-the-clauses.
26. controversy | agents/skills/how-to-write-skills/SKILL.md:339,720 | instructs a vendor-specific skill-list command while the file's own rules forbid vendor tool names; reword to the runtime's command.
27. repetition | agents/skills/done/SKILL.md:170 + investigate/SKILL.md:66 | two-command re-derivation contract duplicated verbatim with no owner link; name done the owner.

Half 2 (jira-workflow through tdd-design, `synced` excluded), 22 findings:

28. controversy | agents/skills/systematic-debugging/SKILL.md:114,280-284 | promises three reference files that do not exist in the directory; restore or delete the references.
29. controversy | agents/skills/systematic-debugging/SKILL.md:179,287 | points to a nonexistent /test-driven-development skill; repoint to tdd-guide/tdd-design.
30. controversy | agents/skills/systematic-debugging/SKILL.md:232 | "see Phase 4.5" names a nonexistent phase; fix the pointer.
31. controversy | agents/skills/review-agents/quality.md:45,130 | MyBatis-specific catalog sections carry no portability marker against the Consumer contract forbidding framework tokens; mark or move.
32. repetition | agents/skills/maintenance/SKILL.md:14,20 | five-line gist plus budget rule stated twice and duplicates the canonical statement at plans/SKILL.md:513; keep one pointer.
33. controversy | agents/skills/maintenance/SKILL.md:106 | sanctioned-overlap closing sentence still says "repo-wide cap of three", stale against the runtime-scoped cap; update the stance wording.
34. repetition | agents/skills/jira-workflow/SKILL.md:216-225 | Notes section restates the Step 4/6/7 branch contract owned by the steps; reduce to pointers.
35. repetition | agents/skills/slack-message/SKILL.md:18,133 | never-direct-send contract stated three times in one file; single-home.
36. overcomplication | agents/skills/slack-message/SKILL.md:79-103 | Wording rules accrete roughly two dozen per-incident one-offs into a generic skill; consolidate to principles, move specifics to overlays.
37. repetition | agents/skills/review-confluence-doc/SKILL.md:189,208 | sidecar write contract spelled out in full in Step 4.7 and Step 5; state once.
38. repetition | agents/skills/review-confluence-doc/SKILL.md:327,367 | em-dash prohibition restated in-file against the canonical home already pointed to; keep one scan line.
39. repetition | agents/skills/review-plan/SKILL.md:163-170 (+ plans/SKILL.md:541-547, review-confluence-doc/SKILL.md:189) | version-1 sidecar field contract re-enumerated in three consumers against the review-staging gold source; replace with pointers.
40. repetition | agents/skills/review-plan/SKILL.md:119,424 | release-gate exception receipt fields restated twice against plans' canonical gate; keep the pointer.
41. repetition | agents/skills/review-plan/SKILL.md:378 | measured churn trigger enumerated identically in review-loop/SKILL.md:177; single-home.
42. repetition | agents/skills/review-loop/SKILL.md:175 | post-fix certification rule stated in full in two skills while review-staging owns it; keep one statement.
43. repetition | agents/skills/review-loop/SKILL.md:139,153,178,198,204 | design-simplicity-before-exit rule in five homes within one file; keep Exit criterion 4.
44. repetition | agents/skills/receiving-review/SKILL.md:356,370 | soften-watchlist write contract stated in full twice; state once.
45. repetition | agents/skills/review-agents/SKILL.md:18-26,28-37 | four-layer boundary stated twice though the file names the contract the single authority; keep the contract.
46. repetition | agents/skills/tdd-design/SKILL.md:239-248,252-266 | Non-Collapse and Density Preservation duplicate the same prohibition; merge.
47. repetition | agents/skills/rfc-design/SKILL.md:162,210,250,362 | Mermaid trigger enumeration spelled out in four places against the named reference home; keep the reference.
48. repetition | agents/skills/plans/SKILL.md:214,539 | plan-review record naming rule defined in template and again at launch; keep the template.
49. repetition | agents/skills/learn/SKILL.md:23,59-60 | done-invocation boundary contract stated in both When to Use and the Integration Point; keep the Integration Point.

Clean units (no findings): pdf, plan-stack, premortem, release, review-reconciliation, review-staging, rootly-retrospective, self-heal, lessons-migrate, and the remaining half-1 units beyond those listed.

## Quarantine batch presentation (proposals only; operator-driven turns own final dispositions)

26 open top-level rows carry a `Quarantine:` header line. Proposed dispositions for one operator batch decision:

| Row | Quarantined | One-line value | Proposal |
|---|---|---|---|
| docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md | 2026-10-27 | claim-deletion fence misses uppercase plan stems | reject (case-sensitive plan stems do not occur in practice; no witness since filing) |
| docs/history/backlog/2026-10-07-iso-to-epoch-python-one-liner.md | 2026-10-27 | iso_to_epoch hand-rolled date arithmetic | keep open (correctness-adjacent; review at next scripts touch) |
| docs/history/backlog/2026-10-07-witnessed-fail-arm-enumeration-stale.md | 2026-10-27 | witnessed-fail-arm enumerations under-count | reject (enumeration snapshots age by design; the pins suite is the live count) |
| docs/history/backlog/2026-10-08-checkout-flow-class-language-lingers.md | 2026-10-16 | checkout-flow class language lingers | reject (pre-dates the current backlog taxonomy; no recent witness) |
| docs/history/backlog/2026-10-08-maintenance-guard-reads-priority-profile-only.md | 2026-10-16 | maintenance guard reads priority profile only | reject (superseded by the current guard set; verify-then-reject at operator turn) |
| docs/history/backlog/2026-10-08-legacy-project-class-key-no-cleanup.md | 2026-10-16 | legacy project-class key not cleaned up | keep open (small bounded fix, still real) |
| docs/history/backlog/2026-10-08-bootstrap-interview-descriptions-stale.md | 2026-10-16 | bootstrap interview descriptions stale | reject (bootstrap-ai-playbook was rewritten 2026-10; the descriptions no longer exist in that form) |
| docs/history/backlog/2026-10-10-review-loop-budget-exec-residuals.md | 2026-10-16 | review-loop budget execution residuals | reject (the budget plan landed; residuals were folded in later rounds) |
| docs/history/backlog/2026-10-11-done-sensitive-scan-neutral-token-assignment.md | 2026-10-27 | sensitive scan rejects neutral token variables | keep open (real false-positive class; small scan-allowlist fix) |
| docs/history/backlog/2026-10-11-lock-span-review-hardening-nits.md | 2026-10-16 | lock-span plan review hardening nits | reject (nits from a landed plan's rounds; the landing's own record owns them) |
| docs/history/backlog/2026-10-11-execute-plan-sequential-workflow-trace.md | 2026-10-27 | observable witnesses for sequential execute-plan | keep open (the runtime-contract normative shift makes the witnesses more valuable, not less) |
| docs/history/backlog/2026-10-13-covered-stub-rows-pending-disposal.md | 2026-10-27 | covered stub rows remain open | keep open (housekeeping row; its own subject is stub disposal, self-owning) |
| docs/history/backlog/2026-10-18-done-lock-from-holder-generation-binding.md | 2026-10-27 | bind from-holder release to lock generation | keep open (machinery hardening with a real race window; needs a plan) |
| docs/history/backlog/2026-10-18-plan-delta-classifier-scope-fold.md | 2026-10-27 | classify plan-scope corrections inside authored boundary | keep open (classifier behavior question, still unresolved) |
| docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md | 2026-10-27 | deployed runtime home carries 25 real files beside symlinks | keep open (real drift; bounded sync fix) |
| docs/history/backlog/2026-10-21-landing-diagnostic-selects-foreign-plan.md | 2026-10-27 | landing diagnostic selects foreign plan/worktree | keep open (witnessed twice; plan-worthy) |
| docs/history/backlog/2026-10-21-plan-review-validation-block-check-pinned-mirror.md | 2026-10-27 | validation-block check needs pinned-mirror note | reject (the pinned-mirror wording landed in the interim; verify-then-reject) |
| docs/history/backlog/2026-10-21-runtime-verifier-naming-and-remedy-gaps.md | 2026-10-27 | runtime verifier naming/remedy gaps | keep open (cluster with the other 2026-10-21 runtime rows) |
| docs/history/backlog/2026-10-21-learn-captures-shared-corpus-promotion.md | 2026-10-27 | promote Task 2 learn captures to canonical homes | keep open (promotion duty still pending) |
| docs/history/backlog/2026-10-21-runtime-deployer-test-pin-gaps.md | 2026-10-27 | runtime deployment test pin gaps | keep open (cluster sibling) |
| docs/history/backlog/2026-10-21-sync-runtime-scripts-prefixed-manifest-lines.md | 2026-10-27 | sync script lacks basename mapping for prefixed lines | keep open (real defect, small fix) |
| docs/history/backlog/2026-10-21-runtime-verifier-design-simplification.md | 2026-10-27 | runtime verifier design simplifications | keep open (cluster sibling) |
| docs/history/backlog/2026-10-24-probe-branch-only-ignore-rule-gap.md | 2026-10-27 | probe tracked-ignored warning reads only base ignore rules | keep open (real gap, small fix) |
| docs/history/backlog/2026-10-24-liveness-pin-plans-archive-twin-span-missing.md | 2026-10-27 | liveness pin names a removed done/SKILL.md span | keep open (stale pin is a real maintenance hazard) |
| docs/history/backlog/2026-10-24-sweep-warning-line-separator-fragmentation.md | 2026-10-27 | warning fragments on Unicode line-separator paths | keep open (edge-case fix, low urgency) |
| docs/history/backlog/2026-10-26-release-sibling-loop-flags-orphan-branch.md | 2026-10-27 | sibling-branch report flags unrelated history, prints git fatal | keep open (real defect with an ugly failure surface) |

Proposal tally: reject 8, keep open 18. No disposition is recorded in any row by this run.

## Filed origins

- docs/history/backlog/2026-11-01-skill-review-systematic-debugging-broken-references.md (findings 28-30)
- docs/history/backlog/2026-11-01-skill-review-maintenance-stance-stale-cap-wording.md (finding 33)
- docs/history/backlog/2026-11-01-skill-review-review-agents-portability-markers.md (finding 31)
- docs/history/backlog/2026-11-01-skill-review-cross-skill-repetition-debt.md (the 40 repetition-class findings as one batched cluster)
