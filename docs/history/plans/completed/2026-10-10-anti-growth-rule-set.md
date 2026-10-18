# Plan: Land the anti-growth rule set as durable guidelines text with the duplication report substrate

Backlog origin: docs/history/backlog/2026-10-10-anti-growth-rule-set.md (the PLAN-PROMPTS entry `anti-growth-rule-set` carries the operator-confirmed prompt; sanctioning directive D-12 in docs/maintenance/operator-directives.md; design inputs docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md Part 5 and Part 2, and the machinery admission protocol, docs/maintenance/machinery-blocker-audit-2026-10-09.md Part 5 item 2 with its 2026-10-10 Reconciliation section)
Driving force: token-usage
Plan review record: the staging series docs/history/reviews/2026-10-10-plan-review-anti-growth-rule-set-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-10-anti-growth-rule-set.md (session sess_72b1f155-dee1-439a-916f-fcc26d801c74)

## Terms

- Anti-growth rule set: the four standing rules of directive D-12 (witness budget, admission, append-tax, review lens), landed durable by this plan; the D-12 record is the wording of record.
- Witness budget: a fix lands the rule; the incident dossier (witness narrative, rejected alternatives, dates) lives in the backlog row, the analysis document, or a changelog file; operative skill text cites it in at most one line.
- Admission: a new top-level arm, section, or field names the existing section it extends and why that section's predicate cannot absorb the case; when no such section exists, that absence, named, is the design input.
- Append-tax: once the repo-wide byte-budget gate lands, a change that grows a skill file past its cap deletes equivalent bytes in the same change, the gate's own breach report being the record; no separate growth-debt note surface is added; until that landing, the same discipline applies at review time only.
- Review lens: plan-review panels treat operative text that grew without a deletion as a finding class, recorded as one line in the review panels' existing finding-class documentation, never a new panel duty.
- Duplication report: scripts/skill_text_duplication.py, the read-only quantified substrate implementing the analysis Part 2 method; its consumers are the doc-hygiene row's standing review arm and the byte-budget gate's growth-telemetry consumer (that consumer's wiring is owned by the maintenance-skill-size-refactor plan's own text, not by this plan).
- Repeated-span percentage: per file, the share of words lying in a normalized 10-word shingle that occurs at least twice in that file (normalization: lowercased, punctuation stripped, whitespace collapsed).
- Duplicated sentence: an exact sentence repetition of 60 or more normalized characters.
- Cross-file intersection: the count of distinct normalized 10-word shingles shared by two files.
- Machinery admission protocol: docs/maintenance/machinery-blocker-audit-2026-10-09.md Part 5 item 2 as bound by its 2026-10-10 Reconciliation section and D-12's admission subordination clause: read-only or warning-only at landing, promotion to blocking only after the first true catch, a stated sunset and review date, and a pre-registered machinery-registry removals commitment.
- Pre-registered removals commitment: the machinery-registry entry's note carrying the sunset trigger and the commitment to move the row to the registry's removals record with the sunset witness at removal time; the removals record cannot hold the row while the path exists, because a removals row whose path still exists is a named failure mutation of scripts/machinery_inventory.py --check.
- Standing review arm: the doc-hygiene row's standing maintenance arm (docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md, Expected section), the consumer home this plan points at the duplication report.

## Why

Skill text growth is unbounded and its counter-signals are policy today, not text: fixes still land incident dossiers inline in operative skill text (the analysis records 64 witness clauses and 81 dated parentheticals in the maintenance SKILL.md alone, about 40KB of operative text), new arms are added without naming the section they specialize, and the plan-review panels have no finding class for unbalanced operative growth (docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md Part 5). The measured ratchet is the budget gate's own incident: 35 commits with exactly one 64-byte shrink, and a roughly 89K-token per-turn doctrine load. Directive D-12 binds all four rules meanwhile, but a directive binds only sessions that read the directives home; the durable forms are the repository guidelines and the panels' finding-class documentation, which every lane and every runtime reads. The duplication report is the quantified substrate both consumers name (the Part 2 method measured the maintenance prompt-templates.md at 30 percent of words in repeated spans with 57 duplicated sentences, and cross-file shared 10-gram counts of 266, 219, and 178 across the corpus), and the operator's 2026-10-10 direction extends the mechanism to every skill, not one corpus.

## Gist & Examples

TLDR: the four anti-growth rules land as a dedicated repository guidelines section with the review lens as one prescribed sentence in review-plan's finding-class documentation, the read-only duplication report script lands with its admission test, sunset, and pre-registered removals commitment, and directive D-12 is superseded beside the anchors it pointed at.

Before: a fix appends a six-sentence incident dossier to a skill guard paragraph, a new arm appears under no named parent section, growth past a byte cap lands with no offsetting deletion and no reviewer finding class to price it, and the only repetition signal is an ad hoc analysis run once on 2026-10-09.

After: the same dossier lives in the backlog row with one citing line in the skill text; the new arm names its parent section and the predicate that could not absorb it; a change growing a file past its cap deletes equivalent bytes or takes the review-time growth finding; and the standing review arm and the budget gate's telemetry consumer read the landed script's report instead of ad hoc runs.

Edge cases: the append-tax rule binds in full only once the byte-budget gate is live (the maintenance-skill-size-refactor plan's Task 2); until then it is review-time discipline through the review lens, exactly as D-12 clause (c) stages it. The duplication script's findings are data, never failures: no lane can wire its exit as a gate, and `OUTCOME: fail` is reserved for usage and unreadable-input errors. The rules bind go-forward: existing inline dossiers are not retro-stripped by this plan (the extraction and folding cycles own that residue); the origin row's ship-when line dates the bound to text landing after this rule set.

## Outcome

The anti-growth rules are checkable text in the homes every lane already reads, D-12 is superseded beside them, and the repetition substrate both consumers name exists as read-only telemetry.

- The repository guidelines carry the four rules in one dedicated section whose opening names, per the admission rule's own terms, why no existing section absorbs them; each rule is imperative, one binding sentence plus its citation shape, and the section is the one home.
- The review lens lands as one prescribed sentence in agents/skills/review-plan/SKILL.md's finding-class documentation beside the Declaration findings paragraph, priced ordinary, composing with the existing lenses, creating no new panel or duty.
- scripts/skill_text_duplication.py lands read-only with outcome-contract exits; its header carries the machinery admission test (incident, expected catch frequency, false-positive cost, sunset), its machinery-registry entry carries the pre-registered removals commitment, and the doc-hygiene row's standing review arm gains its consumer line by name.
- Directive D-12's record moves to superseded with superseded_by naming the guidelines section and the lens-line home, dated, the record body kept as history; the admission-subordination clause's own routing (the machinery-admission-protocol row generalizes it) is untouched.

Gate delta: no refusal class, hard gate, fence, protocol layer, or schema state field is added or removed; the plan adds one read-only analysis tool whose witness is stated (the 35-commit one-shrink ratchet and the roughly 89K-token per-turn doctrine load, docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md; it never blocks, findings are data), one machinery-registry entry for it, guidelines prose, one review-plan sentence, one backlog-row consumer line, and one directives-home supersession edit; the review lens is an ordinary finding class in existing documentation, not a review-layer counted addition (its violation never blocks); the guard liveness ledger's current catch-to-incident ratio at authoring time is 19 catches to 24 incidents (`python3 scripts/gate_liveness_ledger.py show`, TOTAL: catches=19 incidents=24 ratio=19:24 overrides=7, re-derived 2026-10-10), cited per the ledger-citation duty.

## Assumptions

- Execution order against the maintenance-skill-size-refactor plan is free for the script surfaces, and each side references the other by name only; the doc-hygiene row is the one shared consumer surface, so this plan's Task 2 consumer line is scoped to the repetition measure (the duplication report) whenever the budget gate script is not yet tracked at task start (that branch carries the reconciliation note that the budget gate's growth-telemetry leg joins the same line at whichever landing is second, neither landing deleting the other's measure), and lands carrying both measures with the join recorded as taken when the gate script is already tracked. This plan lands the duplication report as the repetition measure of the doc-hygiene row's standing review arm, the consumer home the landed sibling plan names (docs/history/plans/2026-10-10-maintenance-skill-size-refactor.md: the growth-telemetry rider wiring stays out of that plan's scope, the doc-hygiene row owns the standing review arm, and the budget gate's sunset waits on the consumer's landing); the budget gate does not exist yet, so no wiring into it happens here, and the append-tax guidelines text carries the timing clause instead of assuming the gate. The machinery-admission-protocol entry targets two further shared surfaces (the guidelines insertion neighborhood and the D-12 admission-subordination clause): Task 1's insertion point and Task 3's byte-identical freeze are relative to the tree found at task start after the currency rebase, so a peer landing in the same neighborhood re-anchors rather than reverts, and the currency check's stop-and-report precedence is unchanged (the found-tree reading is never license to proceed on a stale branch). The growth-telemetry join is owned at execution, not announced: when the budget gate script is already tracked at task start, the consumer line lands carrying both measures; otherwise the doc-hygiene standing arm is the named join owner, triggered by the budget gate's landing, and the execution manifest records which branch was taken. Basis: the landed sibling plan's Task 2 telemetry and sunset wording (docs/history/plans/2026-10-10-maintenance-skill-size-refactor.md), the machinery-admission-protocol PLAN-PROMPTS entry Tasks 1 and 4, D-12 clause (c), and the origin row's Cluster pointers.
- The guidelines section is a new top-level section, and its own opening performs the admission rule's self-application with the true predicates: no existing section absorbs it (the Skill Design Guidelines merge rule prices cross-skill duplication and its other bullets govern authoring and structuring skills, not the growth balance of existing operative text; the Coding Style single-homing bullets fix documentation-mapping cases, not incident-dossier citation caps or per-file byte budgets; the Vendored Asset Sync Rules and Testing Guidelines govern sync mechanics and test practice), so the absence of a section whose predicate absorbs the case, named with those reasons, is the design input the admission rule itself prescribes. Basis: the admission rule's second sentence and the repository guidelines' current section text.
- The lens line's home is agents/skills/review-plan/SKILL.md's finding-class documentation beside the Declaration findings paragraph: that paragraph is the finding-class precedent (the machinery-without-witness class names it the one home), the lens prices ordinary (its violation never blocks, so it is not a review-layer counted addition), and D-12 clause (d) says one line in the existing finding-class documentation, never a new panel duty. Basis: review-plan's Declaration findings paragraph, D-12 clause (d), and the origin row's Expected (d).
- The pre-registered removals commitment lives on the machinery-registry entry's note, not as a removals-record row at landing: scripts/machinery_inventory.py --check fails on a removals row whose path still exists (a named mutation in the registry test), and the two-mode loop policy plan moved its row into the removals record at removal time with its landing as witness, which is the mechanical precedent. Basis: scripts/test_machinery_inventory.py's mutation list and docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md Task 2.
- The supersession is field-level, not record deletion: D-12's status moves to superseded and superseded_by names the two durable homes with this plan as witness, the record body and its witnesses stay as history, and the admission-subordination clause keeps its own routing note (the machinery-admission-protocol row generalizes that clause; that row's landing supersedes it, not this plan). Basis: D-12's expiry line (the durable forms route through the anti-growth-rule-set plan prompt; the record binds the policy meanwhile) and the machinery-admission-protocol entry's Cluster pointer.
- The rules bind go-forward and this plan strips no existing dossier: the origin row's ship-when line dates the bound (text landing after this rule set), the size-refactor extraction and later folding cycles own the existing 64-clause residue, and adding a retro-strip here would widen a rules-and-telemetry plan into the corpus migration that plan already routes. Basis: the origin row's Ship when section and the landed sibling plan's scoping text (its out-of-scope constraint line and Task 1 changelog-extraction routing).
- The Part 2 numbers cited in Why are the analysis doc's recorded measurements (run ad hoc 2026-10-09), not re-derived by this plan; the landed script re-derives them on every run and its test pins the method on a synthetic fixture, so no number in this plan is load-bearing at execution. Basis: the analysis Part 2 method statement and this plan's Task 2 test.

Decision points requiring a grill: none remain (the operator confirmed the mechanism and its fleet-wide scope on 2026-10-10; the PLAN-PROMPTS entry records the rejected alternatives, and D-12's admission subordination reconciles the rule set with the machinery audit's own protocol).

## Standing constraints

- Guidelines and lens edits are prose only: no skill semantics change, no new panel, no new validator flag, no change to any skill's workflow steps; scripts/validate_review_staging.py and scripts/plan_readiness.py bytes are unchanged.
- Nothing this plan lands blocks before its first true catch: the duplication script never exits non-zero on findings, and no wiring introduced here gates on it.
- The machinery registry gains its entry in the same landing as the script, and this plan owns no pre-existing registry failures: scripts/machinery_inventory.py --check reports at every landing the failures present at task start plus none new from this plan's change (the check exits 1 on main today over pre-existing regrowth rows, none this plan's), and the new entry itself validates clean.
- The pins suite, the hygiene scan, the boundary-fixture regression over review-plan, and the parallel-work regressions suite stay green at every landing (bash scripts/check_maintenance_pins.sh; bash ~/.ai-playbook/scripts/scan-public-hygiene.sh; python3 scripts/test_plan_review_boundary_examples.py; python3 scripts/test_parallel_work_regressions.py).
- The runtime twin deploys at the landing: the home skills symlinks resolve to the primary checkout's agents/skills, so the branch's review-plan edit reaches the runtime when the merge-locked landing touches that checkout, and until then the live loop keeps loading the pre-edit file; the execution manifest records the symlink-resolution assertion (the chain resolves to the primary checkout; no separate copy of the file exists in the repository tree).
- No machine-specific absolute paths in any edited file; the em-dash scan passes with its per-surface modes: file mode with CHECK_NO_EM_DASH_ALL=1 over the prose and Python touched paths, and added-lines mode over docs/maintenance/operator-directives.md (whose committed em-dash lines in frozen records are pre-existing history the plan does not touch).
- Execution runs on a branch kept rebased onto current main at each fold. At each task start the executor re-verifies currency (pins suite exit 0 and no commit in git log HEAD..main touching this plan's anchor files) and on a red baseline, a vanished anchor, or a stale rebase stops and reports instead of proceeding; hand-reconciling PLAN-PROMPTS.md is never the repair.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each of the four rules is stated exactly once in the guidelines section using the verbatim bullet text Task 1 prescribes (the D-12 wording of record modulo the imperative conversion prescribed there); the lens sentence is the class's single home in review-plan with the rule-of-record trigger; the supersession fields name both durable homes; the script implements the Part 2 method on the pinned normalization and reports all three measures.
- regression safety: the pins suite, the boundary-fixture regression over review-plan, and the hygiene scan all pass, the machinery inventory check reports no failure naming the new entry (its pre-existing baseline failures are recorded, not fixed, by this plan), and the em-dash scan passes in its per-surface modes; the script is proven read-only by its test.
- scope discipline: the change set touches only the repository guidelines, agents/skills/review-plan/SKILL.md, the two new script files, scripts/machinery_registry.json, the doc-hygiene row, and docs/maintenance/operator-directives.md.

**Done when:**
- Every span check in `## Validation Commands` holds on the executed tree.
- `( cd "$REPO" && bash scripts/check_maintenance_pins.sh )` exits 0.

**Ship when:**
- The four rules resolve from the repository guidelines by name for any lane or runtime, the review panels price unbalanced operative growth as an ordinary finding class, the standing review arm and the budget gate's telemetry consumer can read the landed report, and a fix landing after this rule set carries no incident dossier longer than one line in operative skill text.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `AGENTS.md` (the new `## Skill text anti-growth rules` section directly after `## Skill Design Guidelines`; all other sections frozen)
- `agents/skills/review-plan/SKILL.md` (one prescribed sentence appended as the last paragraph of the Plan-review boundary section; the boundary declaration prose and the two BOUNDARY fixture blocks stay byte-identical, the finding-class documentation being the sanctioned edit region, all other spans frozen)
- `scripts/skill_text_duplication.py` (new, Task 2)
- `scripts/machinery_registry.json` (one entry, Task 2)
- `docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md` (one consumer line in Expected, Task 2)
- `docs/maintenance/operator-directives.md` (the D-12 status and superseded_by fields and the record-format superseded_by field-spec line only, Task 3; the record body and all other directives frozen)

**Tests:**
- `scripts/test_skill_text_duplication.py` (new, Task 2)

**Read-only (referenced, never edited):**
- `docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md` (Part 5 rules, Part 2 method and numbers)
- `docs/maintenance/machinery-blocker-audit-2026-10-09.md` (Part 5 item 2 and the 2026-10-10 Reconciliation section)
- `scripts/machinery_inventory.py` and `scripts/test_machinery_inventory.py` (consumed as they exist; the removals-row mutation is the pre-registration constraint)
- `docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md` (the removal-time registry move precedent)
- `scripts/gate_liveness_ledger.json` (the cited ratio)
- `docs/history/backlog/2026-10-10-anti-growth-rule-set.md` (the origin row; flipped covered by the execution landing rider, not by a task)
- `docs/history/plans/2026-10-10-maintenance-skill-size-refactor.md` (the landed sibling plan's telemetry-consumer and sunset wording; referenced, never edited here)
- `docs/history/backlog/PLAN-PROMPTS.md` (the dispatch entry; pruned by the authoring landing with its receipt, not by a task)

**Receipts:**
- Origin row: docs/history/backlog/2026-10-10-anti-growth-rule-set.md (Status: open; the execution landing rider flips it covered naming this plan)
- Prompt entry: docs/history/backlog/PLAN-PROMPTS.md `## anti-growth-rule-set` (frozen under docs/tmp/authoring-claims/2026-10-10-anti-growth-rule-set.md; the authoring landing prunes it with the plans-root witness and the PLAN-PROMPTS-PRUNE receipt)

## Validation Commands

**Production:**
```bash
grep -c "## Skill text anti-growth rules" AGENTS.md   # expect 1
grep -c "cites it in at most one line" AGENTS.md   # expect 1
grep -c "why that section's predicate cannot absorb the case" AGENTS.md   # expect 1
grep -c "deletes equivalent bytes in the same change" AGENTS.md   # expect 1
grep -c "grew without a deletion" AGENTS.md   # expect 1
grep -c "grew without a deletion" agents/skills/review-plan/SKILL.md   # expect 1 (the lens line, the class's one home outside the guidelines)
awk '/^## Plan-review boundary/{f=1;next} f&&/^## /{exit} f&&/^Declaration findings:/{d=1} f&&/^Growth balance:/{if(d==1){print 1}else{print 0}; exit}' agents/skills/review-plan/SKILL.md   # prints 1 (the lens line sits after the Declaration findings paragraph inside the boundary section)
awk '/^## Plan-review boundary/{f=1;next} f&&/^## /{exit} f&&NF{l=$0} f&&/^Growth balance:/{g=1} END{if(g&&l~/^Growth balance:/){print 1}else{print 0}}' agents/skills/review-plan/SKILL.md   # prints 1 (the Growth balance paragraph is the boundary section's last non-empty line)
grep -c "^- status: superseded" docs/maintenance/operator-directives.md   # expect 1 (the D-12 record)
grep -c "superseded_by: the repository guidelines" docs/maintenance/operator-directives.md   # expect 1
grep -c "^- superseded_by:" docs/maintenance/operator-directives.md   # expect 12 (one per record; the D-12 value replaced, none duplicated)
grep -c "^- superseded_by: none" docs/maintenance/operator-directives.md   # expect 11 (every record except D-12)
grep -c "skill_text_duplication" docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md   # expect 1
python3 -c "import json,sys; d=json.load(open('scripts/machinery_registry.json')); e=[r for r in d['entries'] if r.get('id')=='skill-text-duplication-report']; sys.exit(0 if len(e)==1 and 'removal' in e[0].get('note','') else 1)"   # the registry entry with its pre-registered removals commitment
grep -c "Machinery admission test" scripts/skill_text_duplication.py   # expect >=1 (the verbatim header label Task 2 prescribes)
```

**Tests:**
```bash
python3 scripts/skill_text_duplication.py   # OUTCOME: pass, exit 0; the report names per-file repeated-span percentages, top duplicated sentences, and cross-file intersections over the skills tree
python3 scripts/skill_text_duplication.py --json | python3 -m json.tool >/dev/null   # exit 0, parseable JSON consumed
python3 scripts/skill_text_duplication.py /path/does/not/exist >/dev/null 2>&1; test $? -eq 1   # OUTCOME: fail on unreadable input only
python3 scripts/skill_text_duplication.py --top notanumber agents/skills/ >/dev/null 2>&1; test $? -eq 1   # OUTCOME: fail on the usage-error arm
python3 scripts/test_skill_text_duplication.py   # exit 0 (method fixtures, read-only proof, exit-contract checks)
python3 scripts/machinery_inventory.py --check   # no failure line names the new entry id (skill-text-duplication-report) or its path (the check exits 1 on the pre-existing regrowth baseline this plan does not own; record the output)
( cd "$REPO" && bash scripts/check_maintenance_pins.sh )   # exit 0
python3 scripts/test_plan_review_boundary_examples.py   # exit 0 (the boundary fixture regression; it reads the BOUNDARY fixture blocks, not the lens sentence)
python3 scripts/test_parallel_work_regressions.py   # exit 0
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file AGENTS.md agents/skills/review-plan/SKILL.md scripts/skill_text_duplication.py scripts/test_skill_text_duplication.py docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md scripts/machinery_registry.json   # exit 0 (operator-directives.md is gated by the added-lines line below)
bash scripts/check-no-em-dash.sh added-lines --base <merge-base> -- docs/maintenance/operator-directives.md   # exit 0 on new lines only (the file's committed em-dash lines in frozen records are pre-existing history)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh   # exit 0 from the repo root
```

### Task 1: guidelines rule set and the review lens line

Files:
- `AGENTS.md`
- `agents/skills/review-plan/SKILL.md`

Primary class anchors:
- `Skill Design Guidelines` in `AGENTS.md`, the section the new rules section directly follows; its position fixes the insertion point.
- `Declaration findings` in `agents/skills/review-plan/SKILL.md`, the finding-class home the lens line joins.

- [x] In `AGENTS.md`, insert the new section `## Skill text anti-growth rules` directly after the `## Skill Design Guidelines` section relative to the tree found at task start after the currency rebase (a peer landing that positioned a section there first re-anchors the insertion beside that peer section; the parenthetical never licenses proceeding on a stale branch: the standing constraint's currency check runs first and its stop-and-report precedence is unchanged), opening with the scope sentence (these rules bind every session editing skill text, guidelines, or plans in this repository, and every review panel over such edits; they supersede directive D-12's meanwhile bind, docs/maintenance/operator-directives.md) followed by the admission self-application sentence with the true predicates (no existing section absorbs them: the Skill Design Guidelines merge rule prices cross-skill duplication and its other bullets govern authoring and structuring skills, not the growth balance of existing operative text, and the Coding Style single-homing bullets fix documentation-mapping cases, not incident-dossier citation caps or per-file byte budgets, so the absence of a section whose predicate absorbs the case, named with those reasons, is the design input per the admission rule's own second sentence). [class: IMPLEMENTATION_REQUIRED]
- [x] In the same section, land the four rules as imperative bullets using this task's verbatim bullet text (the D-12 wording of record modulo the imperative conversion prescribed here): (a) Land the rule, not the story: the incident dossier, with its witness narrative, rejected alternatives, and dates, lives in the backlog row, the analysis document, or a changelog file; operative skill text cites it in at most one line. (b) Name the home or the absence: a new top-level arm, section, or field names the existing section it extends and why that section's predicate cannot absorb the case; when no such section exists, that absence, named, is the design input. (c) Pay for growth: once the repo-wide byte-budget gate lands, a change that grows a skill file past its cap deletes equivalent bytes in the same change, the gate's own breach report being the record, and no separate growth-debt note surface is added; until that landing, the same discipline applies at review time only. (d) Price unbalanced growth: treat operative text that grew without a deletion as a finding class, recorded as one line in the review panels' existing finding-class documentation, never a new panel duty. [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/review-plan/SKILL.md`, append exactly one sentence as a new last paragraph of the Plan-review boundary section, directly after the Declaration findings paragraph: Growth balance: operative skill or guidelines text that a change grew without a deletion is a distinct finding class beside, not a second home for, the machinery-without-witness class, priced ordinary by this sentence itself, per the repository guidelines' skill text anti-growth rules; this sentence is the class's one home and creates no new panel duty. The boundary declaration prose and the two BOUNDARY fixture blocks stay byte-identical; the finding-class documentation is the sanctioned edit region, and no other span of the file changes. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the runtime twin topology per the merge-locked deploy model: the home skills symlinks resolve to the primary checkout's agents/skills (the runtime keeps loading the pre-edit file until the landing) and no separate copy of review-plan/SKILL.md exists in the repository tree; record the symlink-resolution assertion in the execution manifest; run the pins suite, the em-dash scan per the standing constraint's modes, and the hygiene scan green before the landing. [class: REPOSITORY_TEST]

### Task 2: duplication report script, registry entry, and consumer pointing

Files:
- `scripts/skill_text_duplication.py` *(new)*
- `scripts/test_skill_text_duplication.py` *(new)*
- `scripts/machinery_registry.json`
- `docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md`

Primary class anchors:
- `Part 2` in `docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md`, the method of record the script implements.
- `entries` in `scripts/machinery_registry.json`, the inventory array the new tool row joins.

- [x] Land `scripts/skill_text_duplication.py`: inputs are file or directory paths (default `agents/skills/`), Markdown files only, with `docs/history/` and `synced/` subtrees excluded; per file the normalized 10-word shingle method (lowercased, punctuation stripped, whitespace collapsed) reports the repeated-span percentage (the share of words in shingles occurring at least twice), the exact duplicated sentences of 60 or more normalized characters with counts, and per file pair the distinct shared 10-gram count, with `--top N` (default 10) bounding the reported sentences and pairs; output is a human report plus `--json` for consumers, the `--json` shape pinned as one top-level object with `files` (per file: path, words, repeated_span_pct, duplicated_sentences as text-count pairs) and `pairs` (path_a, path_b, shared_shingles), every list sorted by path with the text as tie-break, deterministic and byte-identical across runs on the same tree, and a file with fewer than 10 words or zero shingles reporting repeated_span_pct 0.0; arguments are parsed explicitly so a usage error prints `OUTCOME: fail` and exits 1 (stock argparse's exit 2 is never surfaced); the exit contract: `OUTCOME: pass` and exit 0 on any completed analysis (findings are data, never failures), `OUTCOME: fail` and exit 1 only on usage or unreadable-input errors; the script writes nothing but stdout. [class: IMPLEMENTATION_REQUIRED]
- [x] Open the script header comment with the verbatim label line `Machinery admission test (read-only; never gates):` and state beside its provenance: the concrete incident (the 35-commit one-shrink ratchet and the roughly 89K-token per-turn doctrine load, docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md), the expected catch frequency (a weekly rider read plus per-cycle consolidation reads; docs/maintenance/recurring-tasks/weekly-measurement-rider.md is the cadence home), the false-positive cost (zero blocking; the script never gates), and the sunset (if no consumer reads the report across six consecutive weekly rider windows, the script and its registry row are removed). [class: IMPLEMENTATION_REQUIRED]
- [x] Add one machinery-registry entry (id `skill-text-duplication-report`) for the script with the registry's existing schema fields pinned as: kind `script`, disposition keep, witness class `incident` with ref docs/maintenance/maintenance-skill-refactor-analysis-2026-10-09.md, its note carrying the admission summary and the pre-registered removals commitment: at removal time the row moves to the registry's removals record with the sunset witness (a removals-record row while the path exists fails scripts/machinery_inventory.py --check, so the commitment is pre-registered on the entry, per the two-mode registry-move precedent); the --check validation runs after the same-landing commit (the check reads the tracked tree) and reports no failure naming the new entry or its path; the baseline's pre-existing regrowth failures are recorded in the execution manifest as the found-tree baseline and are out of this plan's scope. [class: IMPLEMENTATION_REQUIRED]
- [x] Append one consumer line to the doc-hygiene row's Expected section naming scripts/skill_text_duplication.py as the repetition check's measure (the Part 2 method: per-file repeated-span percentage, top duplicated sentences, cross-file intersections), the arm consuming the report on its standing cadence with its exclusions (archives, `synced/`) unchanged, and the script never gating; absent the budget gate the line is scoped to the repetition measure and carries the reconciliation note that the budget gate's growth-telemetry leg joins the same consumer line at whichever sibling landing is second, neither landing deleting the other's measure; the join is owned, not announced: when scripts/skill_text_budget.py is already tracked at task start, the line lands carrying both measures (repetition and growth telemetry) with the note recording the join as taken rather than pending, and otherwise the line is scoped to the repetition measure and names the doc-hygiene standing arm as the owner of the join, triggered by the budget gate's landing, and the execution manifest records which branch was taken. [class: IMPLEMENTATION_REQUIRED]
- [x] Land `scripts/test_skill_text_duplication.py` (the repository's unittest pattern): a temporary fixture tree exercising the repeated-span percentage math, the 60-or-more-character duplicated-sentence detection, the cross-file intersection count, the degenerate fixtures (a file with fewer than 10 words and an empty file report repeated_span_pct 0.0), the `OUTCOME: pass` and `OUTCOME: fail` exit contract including the usage-error arm, a read-only proof (the full sorted relative-path inventory plus per-file bytes and modification times identical before and after the run, and `git status --porcelain` empty immediately before and after the repo-scoped run), a determinism assertion (two runs over the same fixture produce byte-identical stdout and JSON), a JSON parse check on the `--json` payload, a shape assertion on that payload (the top-level keys files and pairs, the per-entry key sets the contract pins, and both lists ordered by path with the text as tie-break), and the unreadable-input failure path; ends with explicit temp-directory teardown. [class: REPOSITORY_TEST]

### Task 3: D-12 supersession record and final verification

Files:
- `docs/maintenance/operator-directives.md`

Primary class anchors:
- `D-12` in `docs/maintenance/operator-directives.md`, the directive record this task supersedes beside its anchors.

- [x] In the D-12 record, set the status line to `- status: superseded` and replace the existing `- superseded_by: none` line with `- superseded_by: the repository guidelines' Skill text anti-growth rules section and the Growth balance sentence in agents/skills/review-plan/SKILL.md (landed by docs/history/plans/2026-10-10-anti-growth-rule-set.md)`, dated with the execution date; amend the record-format field-spec line for `superseded_by` to admit the second shape (the superseding record's id, or, when the superseder is durable text and not a directive record, that text's homes with the landing plan as witness); the record body, its witnesses, and the admission-subordination clause stay byte-identical relative to the tree found at task start after the currency rebase (the standing constraint's currency check runs first; the found-tree reading never licenses proceeding while a peer commit sits in HEAD..main touching the anchor files), and the clause's durable generalization remains routed to the machinery-admission-protocol row per that row's own Cluster pointer. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full `## Validation Commands` block green on the executed tree and record the outputs in the execution manifest. [class: REPOSITORY_TEST]
