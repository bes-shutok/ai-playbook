# Backlog: an EXEC entry's Prompt field shadows the Ad-hoc arm's landing machinery, and a plans-worded exec mandate does not prefer the plans segment

- **Filed:** 2026-10-26 (operator correction over the 2026-10-26 interactive exec mandate)
- **Status:** open
- **Priority:** high (the arm's blocking review panel - the one gate standing between ad-hoc work and the default branch - was skipped in a witnessed landing)
- **Workflow:** backlog
- **Origin class:** operator correction (in-session witness, this repository's own lane)
- **Class:** investigate-then-fix (prompt-authoring contract gap plus a mandate-interpretation gap)
- **Driving force:** reliability
- **Skill/step:** the investigate skill's Stage 4 entry-emission contract (`agents/skills/investigate/SKILL.md`); the EXEC-PROMPTS entry template's `Prompt:` field semantics; the Ad-hoc backlog arm bullet (`agents/skills/maintenance/decisions.md`); the Exec-mode selection rule's ordering contract (`agents/skills/maintenance/decisions.md`)
- **Environment:** playbook repo, interactive exec mandate, primary checkout, 2026-10-26
- **Suspected root area:** the Ad-hoc backlog arm carries the full ad-hoc run contract (ad-hoc worktree, doing-code-review focused panel before any landing with blocking findings folded, `Ad-hoc-panel-pass:` receipt, `land_squash`-class squash landing), but the dispatching session's operative instruction is the EXEC entry's own `Prompt:` field; when an entry's prompt names a shorter gate list (the 2026-10-26 `adhoc-run-pick-time-freeze-mark` entry named only the pins suite, the em-dash gate, and the hygiene scan), the session follows the prompt and the arm's panel/worktree/landing machinery silently drops out. A second, independent gap: an operator mandate worded "exec N plan(s)" was satisfied from the EXEC-PROMPTS segment, and the Exec-mode selection rule's merged urgency ordering gives the operator no way to see that the plans segment was skipped.

Cluster: EXEC-PROMPTS entry adhoc-arm-squash-helper-route (covered 2026-10-27; same surface: the Ad-hoc arm's landing sentence and the sessions that skip it; the covered row's fix - naming the helper - and this row's fix - stopping entry prompts from shadowing the arm - compose)

## Observed vs expected

Observed, 2026-10-26 interactive exec mandate ("exec 1 plan in order of importance, stop when completed"): the session picked the top EXEC-PROMPTS entry (`adhoc-run-pick-time-freeze-mark`), skipped the doing-code-review focused review panel and the `Ad-hoc-panel-pass:` receipt entirely, worked at the primary checkout instead of an ad-hoc worktree, and landed with a hand-composed direct commit (cb0e439c) - following the entry prompt's own three-gate list verbatim. The operator corrected the run in-session. Expected: the entry prompt cannot de-scope the arm - an ad-hoc entry's prompt payload either inherits the arm's machinery by reference or is rejected at emission time by the investigate contract that writes it; and a plans-worded operator mandate resolves its selection to the plans segment first (EXEC-PROMPTS entries only in the plans segment's absence), the resolution recorded in `decision_reason`.

## Evidence and archaeology (2026-10-26)

- The panel mandate's introduction: 867f8ed7e (2026-10-18, "skills: clarify planning and execution workflows") landed the `Ad-hoc-panel-pass:` receipt wording into the Ad-hoc backlog arm; the arm's text at HEAD mandates the panel "before any landing with blocking findings folded first".
- The witnessed landing: cb0e439c carries no review record reference, no `Ad-hoc-panel-pass:` line, and no worktree evidence; its entry prompt (pruned in the same commit) named exactly "the pins suite, the em-dash added-lines gate, and the public hygiene scan".
- Covered sibling, EXEC-PROMPTS entry adhoc-arm-squash-helper-route: three exec runs in 2026-10-22 alone hand-composed ad-hoc landings skipping helper gates - the same class of the arm's machinery dropping out between text and run.
- The Exec-mode selection rule orders plans, then ready EXEC-PROMPTS entries, then ad-hoc items by merged urgency with no operator-wording override, so a "plans"-worded mandate has no textual hook to restrict selection (working-tree grep at the tip agrees).

## Scope to resolve

1. Emission-side constraint: the investigate skill's Stage 4 and/or the EXEC-PROMPTS log's standing rules gain the rule that an ad-hoc entry's `Prompt:` payload never restates a gate list that shadows the Ad-hoc arm's machinery - it inherits the arm by reference (one clause) - and the emission checks it.
2. Mandate-wording resolution: the Exec-mode selection rule (or the maintenance skill's mode binding) gains the clause that an operator mandate worded "plan(s)" resolves the candidate set to the plans segment first, the resolution recorded in `decision_reason`.
3. Retroactive receipt repair is not in scope: the witnessed landing's change is one sentence verified by the pins suite; re-running the panel post-hoc prices more than the risk it retires (recorded here so a later session does not improvise it).

## Alternatives to assess

- A blocking gate that refuses an ad-hoc landing lacking the panel receipt: rejected under the machinery admission protocol - the arm already mandates the panel; the witnessed failure is prompt shadowing, a text-authoring defect, and a gate would duplicate the receipt three-way equality the landing already fails closed on when the arm is followed.
- Restricting entry prompts to a bare target pointer (no prompt payload at all): prices away the entry's real value (scope arms, orientation, urgency evidence); the narrower constraint is on gate restatements only.
- Resolving the mandate gap by asking the operator per run: contradicts the loop's never-block-on-questions invariant; the wording-resolution clause is the text hook.

## Source

- Operator message, 2026-10-26, verbatim: "I asked you to execute plans and you instead did line from EXEC-PROMPTS.md and didn't even run focused review panel."
