# Backlog: Review pointer-wiring polish (fix-risk deferred)

Status: backlog
Workflow: pre-plan (promote via `plans` skill when scheduled)

## Problem

Seven Low/Medium findings from the 2026-08-28 fix-risk-triage-skills review (rounds r3-r6, design-simplicity and contract-docs workers) remain open on the call-site wiring introduced with the Fix-risk triage policy:

1. **Call sites keep a gloss of the pointed-at rule.** `agents/skills/receiving-review/SKILL.md` rule 4, `agents/skills/review-loop/SKILL.md` orchestration rule 4, and `agents/skills/execute-plan/SKILL.md` Hard Gate 23 each say "verify scoped fixes with the focused targeted round composed per `review-panel-selection.md` (Review-loop follow-ups)". The decision rule itself (when preference applies, composition, exit coverage) is single-sourced in the catalog since r2; what remains at call sites is a pointer plus an object noun. A stricter reading wants name-only references ("verify scoped fixes per `review-panel-selection.md` Review-loop follow-ups").
2. **Catalog follow-up bullet is overloaded and the section title is consumer-specific.** `agents/skills/review-agents/review-panel-selection.md` "Review-loop follow-ups" bullet 2 packs the preference, its applicability condition, and per-consumer exit-coverage forks into one bullet, partially overlapping bullet 3 (design-simplicity hybrid); the section title says "Review-loop" while the scope line now also governs `execute-plan` Phase 3 rounds. Candidate fix: rename the section to a consumer-neutral name (e.g. "Targeted follow-ups") and update every call site in the same pass.
3. **Hard Gate 17 restates the fix-risk stop conditions (added r4).** `agents/skills/execute-plan/SKILL.md` Hard Gate 17 spells out "the fix-risk stop for user direction when a must-stay-blocking finding has neither a minimal additive path nor a user in a non-interactive run" — a fourth paraphrase of the provider's conditions (beyond the three call sites above). Candidate fix: shrink to a name-only pointer ("the fix-risk asks sanctioned under Hard Gate 23 / receiving-review Fix-risk triage when fixes regenerate findings").
4. **Blocking re-evaluation mechanic specified in two places (added r3/r4).** The three-part mechanic (rewrite Blocking bullet in place, rationale on Analysis, mirror in sidecar `findings[].blocking`) is fully stated in both `agents/skills/review-staging/SKILL.md` Triage presentation freeze and the `receiving-review` "Staging doc triage outcomes" checklist step. Candidate fix: keep the full mechanic in review-staging (contract owner) and reduce the receiving-review checklist step to a name-only reference.
5. **No owner or ordering for finalizing triage after the fix-risk ask is answered (found r6).** `receiving-review/SKILL.md` Fix-risk closing: the executing agent returns the presentation/stop question to its orchestrator and the finding stays `pending` until answered — but after the answer, no rule instructs anyone to apply the triage-outcomes checklist (Status → deferred, Triage outcomes recompute, sidecar mirror, validator). Candidate fix: one sentence assigning the post-answer checklist application to the orchestrator or a relaunched triage pass before the next round.
6. **Catalog bullet asserts Phase 3 exit governance by absence (added r5).** `agents/skills/review-agents/review-panel-selection.md` Review-loop follow-ups: "Phase 3 has no separate worker-coverage exit rule" is a negative claim about another skill's rule set that the catalog cannot keep true and execute-plan does not reciprocally own. Candidate fix: reduce to "exit coverage for Phase 3 is governed by execute-plan Step 3.4/3.5 (see that skill)".
7. **Template step 7 re-glosses the returned-for-ask exception at a delegating site (added r7, found r8).** `agents/skills/execute-plan/subagent-prompts.md` Address Review step 7 already points at receiving-review **Backlog capture** by name (and the prompted agent runs that skill), then re-derives the exception in a parenthetical — a fourth normative copy. Candidate fix: drop the parenthetical; keep the name-only pointer.
8. **Two more stop-condition paraphrases (added r7, found r8).** The Step 3.5 fix-risk stop row and the review-loop rule 4 stop note are a fifth and sixth restatement of the provider's stop clause (the pattern of item 3), and the Step 3.5 row drops the "non-interactive" and "minimal" qualifiers. Candidate fix: collapse both to name-only pointers ("Stop; ask the user per Hard Gate 23 / receiving-review Fix-risk triage when fixes regenerate findings").

Exact locations: `receiving-review/SKILL.md` rule 4 and Fix-risk closing; `review-loop/SKILL.md` orchestration rule 4; `execute-plan/SKILL.md` Hard Gates 17 and 23 and Integration Points; `review-panel-selection.md` "Review-loop follow-ups" (~line 42-49); `receiving-review/SKILL.md` "Staging doc triage outcomes" step 4 + `review-staging/SKILL.md` Triage presentation freeze.

## Why not fixed now

Fix-risk triage (user policy 2026-08-28, receiving-review **Fix-risk triage when fixes regenerate findings**): this component family — the pointer wiring and the fix-risk closing paragraph — produced new findings in every review round r1-r7 as earlier fixes landed. The residual items are polish-level or single-sentence additions with no live drift hazard today (all copies were written together in this run). Further surgery was refused for this run; the items are recorded here so a future pass can take them as one coherent rename-and-trim edit.

## History

- The r6 review also found that cross-references had coined "non-negotiable 23" for the list titled "Hard Gates"; that rename to "Hard Gate 23" landed in the r6 fixes — no open work.

## Source

- Review staging: `docs/reviews/2026-08-28-fix-risk-triage-skills-code-review-r3.md` (r3, staged 7 + overflow), `docs/reviews/2026-08-28-fix-risk-triage-skills-code-review-r5.md` (r5, staged 5), `docs/reviews/2026-08-28-fix-risk-triage-skills-code-review-r6.md` (r6, staged 4), and `docs/reviews/2026-08-28-fix-risk-triage-skills-code-review-r8.md` (r8, staged 5)
- Severity: Low-Medium (all deferred items); design-simplicity and contract-docs workers
