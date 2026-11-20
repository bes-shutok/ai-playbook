# Plan: Collaborator-wiring review pattern and the sibling-alignment precedent receipt

Backlog origins (scope of record):
- docs/history/backlog/2026-11-10-review-lenses-miss-collaborator-wiring-idiom.md
- docs/history/backlog/2026-11-10-repo-alignment-directive-not-a-checkable-duty.md

Driving force: reliability (primary), simplicity (secondary)
Force justification: reliability is not a taxonomy principle; it is implemented anyway because the witnessed cost is external review rounds on every stacked run in a repository with an alignment directive (seven threads, three fix rounds in the origin run), and park-triage would not take it because the fix is four bounded text edits with no new machinery.
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-collaborator-wiring-idiom-and-alignment-receipt-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 0.5h
Executed: yes (8df23921517665c3fd5b1d25cca3ceda7cb09925)
Authoring claim: collaborator-wiring-idiom-and-alignment-receipt.md (session sess_8a54444d-f7d8-464c-b71b-c7cd24140e8e)

## Terms

- collaborator wiring: how a class gets its helper objects (converters, mappers, assemblers, client wrappers) in a container-managed layer: injected beans versus hand construction.
- container-managed layer: code whose objects the dependency-injection container builds and wires, as opposed to plain data types or test fixtures.
- sibling precedent: the corresponding pattern in a sibling service of the same repository, cited as the evidence a finding or a receipt leans on.
- alignment directive: a repository instruction that says to inspect sibling services first and align naming, technology choices, and patterns with them by default.
- precedent receipt: one optional line in the implementation worker return naming, per new pattern, the sibling file consulted and whether it matches, or `none found`.
- build-wide default: a framework setting the build declares once for the whole project, which a per-file annotation value can silently override.
- static-helper-as-bean trap: with the mapper-generation library's declared reference mechanism, a referenced helper is injected as a bean, so a utility-annotated helper whose methods are not explicitly static makes generated code call an instance that is not managed.
- architecture lens: `agents/skills/review-agents/architecture.md`, the catalog the design-simplicity worker loads.
- per-task selection note: the per-task intermediate review selection mapping in `agents/skills/review-agents/review-panel-selection.md`.
- portability gate: `scripts/check_review_agent_portability.py`, which keeps the review-agent catalogs free of stack-specific tokens.
- byte-budget gate: `scripts/skill_text_budget.py --check`, the blocking per-file byte ceiling over skill text.

## Why

Seven external review threads in one stack were all collaborator wiring, and every internal panel passed them: the lenses carry interface and concrete-dependency rules only in domain-to-infrastructure phrasing, and the repository's align-with-siblings directive reached every worker as prose with nothing asking for discharge evidence. Text is the missing piece: one named lens pattern and one receipt line give workers and reviewers something to apply, at the cost the origins already witnessed.

## Gist & Examples

TLDR: adds the collaborator-wiring pattern to the architecture lens and a one-line precedent receipt to the implementation worker return, so sibling-alignment divergence is named at task time instead of by the external reviewer; motive: reliability.

Before: a stateless converter ships as a concrete class its callers import directly, mappers are built with the generation library's factory method while each file restates a component-model value the build already sets, and a helper reaches generated code by inheritance. Task panels return clean; the external reviewer opens seven threads in the first round.

After: the same diff hits the `architecture#collaborator-wiring` checks at the per-task tier, the implement return carries `converter: ../sibling/XConverter.java: match` style receipt lines, and a divergence without a recorded reason is a finding backed by the cited sibling file.

## Outcome

A repository's sibling-alignment directive becomes a checked duty and container-managed wiring defects surface at task time.

- Review panels see wiring checks for every diff that adds or edits a container-managed collaborator, before an external reviewer does.
- Workers discharge the alignment directive with one receipt line per new pattern instead of unread prose.
- No gate, refusal class, worker role, or ledger is added; the paying deletion keeps the worker prompt byte-honest.

Gate delta: adds four prose-only requirements (the optional Evidence-envelope precedent receipt line; one alignment-directive sentence extending the review-plan repo-override clause; the lens receipt spot-check sentence; the selection-note mapping sentence), priced by the same-change deletion of the implement template's duplicated placeholder row (paying sibling) and by the origin row's witnessed external-review cost (docs/history/backlog/2026-11-10-review-lenses-miss-collaborator-wiring-idiom.md); no refusal class, hard gate, fence, protocol layer, or schema field added, none removed.

Follow-up disposition: none anticipated; reviewer or panel backlog candidates route through the standing receiving-review Backlog capture contract, and the 2027-01-10 admission review date is recorded in the origins, not re-registered here.

## Assumptions

- assume `~/Projects/.ai-playbook` resolves to this repository's `projects/.ai-playbook` through a symlink, so the guideline edit is an in-repo edit; basis: `readlink` probe 2026-11-15 and the 2026-10-20 java-construction plan's identical placement.
- assume `projects/.ai-playbook/jvm_guidelines.md`'s next section number is 29; basis: heading grep 2026-11-15 (max existing 28).
- assume the review-agent catalogs cannot name frameworks, products, or languages; basis: the term list in `scripts/check_review_agent_portability.py` (framework-product, language-name, language-syntax classes), so Task 1's pattern text stays abstract and Task 2's rule carries the framework specifics.
- assume the receipt is optional and evidence-bearing only: a diff with no new pattern carries no receipt, and no check refuses an absent receipt; basis: both origins ("optional receipt line", "no new refusal class").
- assume the origin rows' named generic "follow repository conventions" sentence no longer exists verbatim in the worker prompts (the prompts evolved since the 2026-11-10 capture); basis: grep over `agents/skills/execute-plan/subagent-prompts.md` 2026-11-15; the paying deletion re-derives its target from current bytes (the duplicated placeholder row).
Decision points requiring a grill: precedent citation format: `<pattern>: <sibling path>: match | diverges (<one-line reason>) | none found`, one line per new pattern, riding the existing Evidence envelope (decision receipt: origin 2026-11-10-repo-alignment-directive-not-a-checkable-duty.md fix item 1 plus the fold-not-add economy, 2026-11-15; affected sections: Task 3); paying-deletion target: the implement template's duplicated `<PLAN_SLUG>` placeholder row (two rows with different descriptions, one deleted) rather than the origin's named no-longer-present generic sentence (decision receipt: current-bytes grep 2026-11-15 under the maintenance-selected arm; affected sections: Task 4).

## Standing constraints

- Catalog abstraction: every byte added under `agents/skills/review-agents/` stays language- and project-agnostic (abstract patterns and pattern ids only); framework-specific vocabulary lives in `projects/.ai-playbook/jvm_guidelines.md`. The portability gate must exit 0 after every task.
- Byte balance: if any skill file this plan touches exceeds its budget cap after an edit, equivalent bytes are deleted in the same change per the repo's skill-text anti-growth rules; `scripts/skill_text_budget.py --check` must exit 0 at closeout.
- No machinery: the plan adds no gate, validator, lock, ledger, or refusal class, and no new worker role; the machinery admission recorded in both origins (review date 2027-01-10) binds these tasks.
- Repository instructions of consumer projects are never edited by this plan; skills stay project-agnostic.

## Evaluation Criteria

**Quality dimensions:**
- consistency: lens pattern, selection note, guideline rule, receipt format, and override clause reference one pattern id (`architecture#collaborator-wiring`) and one guideline section (`jvm_guidelines.md` #29) with no contradictory phrasing.
- portability: `scripts/check_review_agent_portability.py` exits 0 over the touched catalogs.
- byte balance: `scripts/skill_text_budget.py --check` exits 0 after all edits; subagent-prompts.md growth is paid by its same-file deletion.
- no-machinery: reading the diff shows no gate, refusal class, or worker role added.

**Done when:**
- all four tasks' edits exist with the classification tags below satisfied.
- `python3 scripts/check_review_agent_portability.py` exits 0.
- `python3 scripts/test_review_agent_doors.py` exits 0 (the catalogs and door-pattern registry keep their required actions).
- `python3 scripts/skill_text_budget.py --check` exits 0.
- `bash scripts/scan-public-hygiene.sh` exits 0.
- the guideline file carries the `## 29.` section and the lens, selection note, worker return, and override clause cite the pattern id or the guideline section.

**Ship when:**
- none (repository-only change; the consumer-repository effect is judged by the next stacked run there, which no repository command can witness).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-agents/architecture.md` (Task 1)
- `agents/skills/review-agents/review-panel-selection.md` (Task 1)
- `projects/.ai-playbook/jvm_guidelines.md` (Task 2)
- `agents/skills/execute-plan/subagent-prompts.md` (Task 3)
- `agents/skills/execute-plan/subagent-prompts.md` (Task 4)
- `agents/skills/review-plan/SKILL.md` (Task 3)

**Tests:**
- none; this plan prescribes no test file (gates and focused suites are the evidence, see Validation Commands).

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** the shared guideline file and the skill catalogs are themselves the documentation surface; no page under `docs/` changes, and `README.md` is untouched because no skill name, path, or usage changes.

**Out of scope; reject unless plan-related:**
- `agents/skills/doing-code-review/` and its overlays; reason: the entry's guard-adjacency names only its context-loading role as routing evidence, and no scope arm edits it.
- `agents/skills/review-agents/` catalogs other than the two named files; reason: single-home the pattern; other catalogs carry different defect classes.
- consumer-repository instruction files (CLAUDE.md and siblings); reason: this repository never edits a consumer's instructions.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_review_agent_doors.py -q
python3 scripts/check_review_agent_portability.py
python3 scripts/skill_text_budget.py --check
bash scripts/scan-public-hygiene.sh
```

### Task 1: Collaborator-wiring pattern in the lens and the per-task selection note

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-agents/architecture.md`
- `agents/skills/review-agents/review-panel-selection.md`

- [x] Add a `## Collaborator Wiring` section to the architecture lens headed by the pattern id `architecture#collaborator-wiring`, abstract phrasing only (no framework, product, or language names) [class: IMPLEMENTATION_REQUIRED]
- [x] Check (a), injection: production-code collaborators are injected, not built with direct construction, a static factory, or a service locator; tests may construct freely [class: IMPLEMENTATION_REQUIRED]
- [x] Check (b), sibling shape: a stateless collaborator's type follows the sibling-service shape (interface plus implementation when siblings do), the finding citing the sibling file as precedent evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Check (c), build default: a per-file framework annotation value that restates or overrides the build-wide default is flagged with its consequence named [class: IMPLEMENTATION_REQUIRED]
- [x] Check (d), composition mechanism: shared helper logic reaches its consumer through the framework's declared composition mechanism, never by inheritance or a duplicated default method [class: IMPLEMENTATION_REQUIRED]
- [x] Add the receipt spot-check sentence to the same section: when the reviewing pass's scope materials carry precedent receipts (the Step 1.2b worker receives them from the implement return; a Phase 3 round only when its scope summary carries them), the lens verifies at most one receipt against its cited sibling file, and a receipt claiming match where the sibling differs is a finding [class: IMPLEMENTATION_REQUIRED]
- [x] Add one sentence to the per-task selection note mapping, in the sibling mappings' grammar (the mapping names the worker it adds): a diff adding or editing a container-managed collaborator or a per-file framework attribute adds design-simplicity (whose architecture lens carries `architecture#collaborator-wiring`) to the per-task tier set when the shape is present and the worker absent [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/check_review_agent_portability.py` exits 0 over the edited catalogs (abstract phrasing, no stack tokens) [class: REPOSITORY_TEST]
- [x] Commit: `review-agents: add collaborator-wiring pattern and per-task mapping` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Mapper-wiring guideline rule with the static-helper-as-bean trap

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `projects/.ai-playbook/jvm_guidelines.md`

- [x] Add section `## 29. Mapper wiring with a mapper-generation library` whose first rule reads: the build sets the component model once; mappers are injected container beans and the generation library's factory method stays out of production code (tests may use it) [class: IMPLEMENTATION_REQUIRED]
- [x] Second rule, build default: a per-file component-model attribute must not restate the build-wide default; an explicit restatement is flagged because it silently overrides the build and un-beans the mappers [class: IMPLEMENTATION_REQUIRED]
- [x] Third rule, the static-helper-as-bean trap: a helper referenced through the library's declared mechanism is an injected bean, so a utility-annotated helper must declare every method explicitly static or generated code calls an unmanaged instance (the trap the origin's first fix hit in a context test) [class: IMPLEMENTATION_REQUIRED]
- [x] Fourth rule, placement: shared conversion logic belongs in a referenced helper or a declarative mapping, not a default method on the mapper [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the section heading `## 29.` exists and the rule text names no repository, ticket, or organization [class: REPOSITORY_TEST]
- [x] Commit: `guidelines: mapper wiring rule with the static-helper-as-bean trap` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Precedent receipt in the worker return and the override-clause extension

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/review-plan/SKILL.md`

- [x] Add one optional bullet to the implement prompt's Evidence envelope: `Precedent receipts (optional; new patterns only): one line per new class kind, library use, or annotation attribute, in the form` `<pattern>: <sibling path>: match | diverges (<one-line reason>) | none found`; the receipt rides the existing envelope, no new Return section and no new refusal class [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the intermediate-review placeholder row for the fresh validation output so the parent quotes the implement return's precedent receipts beside it when present, and the worker spot-checks at most one receipt against its cited sibling file [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `agents/skills/review-plan/SKILL.md` Step 2 item 5 with one sentence: when the instruction file or guidelines carry an alignment directive, the directive takes the same precedence as the numeric-limit example, and a new pattern diverging from the cited sibling precedent is a finding unless the diff or plan records the reason; the implementation worker's precedent receipts are the discharge evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: reading the diff shows the receipt is optional (an absent receipt never blocks a return) and no new refusal class appears [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: precedent receipt in implement return; review-plan: alignment-directive override` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Paying deletion and byte-balance closeout

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/subagent-prompts.md`

- [x] Delete the duplicated `<PLAN_SLUG>` placeholder row from the implement section's placeholder table (two rows carry different descriptions for the same placeholder; verify the exact duplicate from current bytes before deleting, keep the row the log-path entries actually use) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/skill_text_budget.py --check` exits 0 (no ceiling breach on any touched file), and the subagent-prompts.md growth across Tasks 3 and 4 is reported net of the deletion in the run record [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_review_agent_doors.py` and `bash scripts/scan-public-hygiene.sh` exit 0 over the touched set [class: REPOSITORY_TEST]
- [x] Commit: `execute-plan: pay receipt growth with duplicated placeholder row deletion` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-10-review-lenses-miss-collaborator-wiring-idiom.md` — migrated into this plan (Tasks 1 and 2: the collaborator-wiring lens pattern with its per-task selection-note mapping, and the jvm_guidelines.md #29 mapper-wiring rule with the static-helper-as-bean trap); executed and archived at `docs/history/plans/completed/2026-11-15-collaborator-wiring-idiom-and-alignment-receipt.md`; the per-item file is deleted under the fold-then-delete rule.
- `docs/history/backlog/2026-11-10-repo-alignment-directive-not-a-checkable-duty.md` — migrated into this plan (Task 3: the optional Evidence-envelope precedent receipt in the implement return and the review-plan alignment-directive override sentence); executed and archived at `docs/history/plans/completed/2026-11-15-collaborator-wiring-idiom-and-alignment-receipt.md`; the per-item file is deleted under the fold-then-delete rule.
