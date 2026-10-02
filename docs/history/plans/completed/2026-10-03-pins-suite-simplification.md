# Plan: Pins-suite simplification: exact-count floor, documented residual direction, named Step 0 sub-bullets

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-21-pins-appendix-floor-redundancy.md`
- `docs/history/backlog/2026-09-21-r3-design-simplification-residuals.md`

## Gist & Examples

TLDR: the pins suite drops one redundant layer, restates a second, and splits the Step 0 density instead of adding checks: the mode-appendix sourcing count floor in prompt-templates.md restates as the exact total 3 (the layered checks already guarantee at least three, and the exact form adds the deviation-list leak direction), the recipe-mode-appendix existence pin on zcode.md stays with its residual failure direction documented (it is the suite's only guard on that file's sourcing span, so folding it would lose a live failure direction), and the Step 0 rearm-on-touch bullet splits into named sub-bullets with every clause byte preserved; simplification driving force, because every reader of the suite reasons about layers without a recorded coverage map and the Step 0 density (1433 words in one bullet) is the documented mechanism behind the witnessed four-homes-in-one-round rule growth.

Re-derivation of the layered guarantee on the current suite (recorded per the entry, driving the drop-or-restate choice):

- The file the floor counts is prompt-templates.md (`p` in the script): the paras[0] state-durability needle check requires `mode appendix sourced from state` in the re-arm duty paragraph; the byte-identity parity requires the twin paragraph byte-identical (two copies); the successor-region membership requires the successor leg's copy. Together: at least three, which is exactly why the floor `< 3` never fires when the layered checks pass - zero independent failure direction over that file.
- The exact total is derivable: three sanctioned copies and the deviation-list entries must not carry the span, so `!= 3` also fails a leaked verbatim copy into the deviation list - a direction the `< 3` floor never had and the suite's exact-count convention (the primitive-precheck pin's exact 5 with its distribution note, the HOST CAVEAT counts of exactly 2 and exactly 1) already prefers.
- The recipe-mode-appendix existence pin greps a DIFFERENT file: it is `grep -qF 'mode appendix sourced from state' "$Z"` over agents/skills/maintenance/zcode.md (the runtime overlay), which carries exactly one copy that no layered check counts. The same-file siblings pin different spans (the directive-wording span, the normalization, the canonical template literal, the recipe-region conjunct), so a surgical deletion or reword of the sourcing span in zcode.md's clause leaves every sibling green - the existence pin is the suite's only guard on that copy, and the entry's fold arm would lose a live failure direction. Its disposition is therefore the entry's other arm: keep the pin and document its residual failure direction the way the r1 F14 comment does.
- The Step 0 bullet (1433 words, one bullet) carries the consultation, bookkeeping, self-heal, and shared-guards contracts; the split is structural.

## Terms

- **Layered guarantee:** the paras[0] membership check, the byte-identity parity over the two re-arm duty paragraphs, and the successor-region membership check, which together bound the whole-file count of `mode appendix sourced from state` in prompt-templates.md from below at three.
- **Exact-count restatement:** the floor becomes `!= 3`, enforcing both the at-least-three layered guarantee and the no-leaked-copy deviation-list rule as one check.
- **Residual-direction documentation:** the zcode.md existence pin stays, and its comment names the failure direction it alone guards: a surgical deletion or reword of the sourcing span in zcode.md's mode-appendix clause that the same-file sibling pins (different spans) do not catch.
- **Structural split:** the Step 0 rearm-on-touch bullet's text is partitioned at its contract boundaries into named sub-bullets under the same check; a contract boundary may fall at a semicolon where the bullet's own sentence chains two contracts, and the clause punctuation bytes stay untouched; every clause's bytes are preserved verbatim and no semantics change.
- **Pin-frozen text:** agents/skills/maintenance/SKILL.md's Step 0 bullet carries suite needles inside its clauses, including the state-first placement pin's contiguous span `rearm-on-touch check: consult the scheduler state file first`, which no inserted marker may sever; any pin that still breaks is updated in the same plan and the same task.

## Coordination (binding, not re-litigating)

- The r1 F14 exact-count precedent (the primitive-precheck pin at exactly 5 with its per-paragraph distribution note) is the convention the restatement follows; the r1 F21 shrink suggestion stays overflowed and is not revived beyond this entry's own arms.
- The r3 row's Item 2 disposes the existence pin (keep-and-document per this plan's re-derivation); the floor's restatement is the sibling appendix-floor row's own disposition (its Candidate fix names the exact-count restatement) - each plan comment names the row that owns it.
- The done skill and prompt-templates.md are not edited; the mode-appendix sourcing span lives in prompt-templates.md's re-arm duty paragraphs and successor leg, whose shapes this plan only counts, never rewrites; zcode.md's clause is never rewritten either (the existence pin keeps guarding it unchanged).
- The maintenance skill's dated revision ledger receives the split's entry (the ledger is newest-first, so the entry is prepended); the pin edits ride this same plan because the Step 0 text is pin-frozen and review-gated.
- The operator execution-lane closure (operator directive, 2026-10-02) means authoring only.

## Review Scope

Every task's Files path, inventoried:

- scripts/check_maintenance_pins.sh
- agents/skills/maintenance/SKILL.md
- docs/history/plans/2026-10-03-pins-suite-simplification.md

Gates re-checked but not edited: agents/skills/maintenance/prompt-templates.md (the counted file), agents/skills/maintenance/zcode.md (the existence pin's file, kept unchanged), scripts/done_sweep_gates_lib.py, agents/skills/done/SKILL.md. Harness touched: the pins suite itself is the edited file (Tasks 1-3) and its row comments grow (Task 2). Reviewers verify the exact-count restatement's layered derivation is scoped to prompt-templates.md, the existence pin's kept status carries a truthful residual-direction comment scoped to zcode.md, and the Step 0 split preserves every clause byte-for-byte without severing the state-first placement pin's contiguous span.

## Tasks

### Task 1: the sourcing count floor restates as the exact total 3

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh` GREEN after the edit; the layered derivation recorded in this plan's Gist is the re-derivation the entry requires

- [x] RED: `grep -c 'mode appendix sourcing count %d != 3' scripts/check_maintenance_pins.sh` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Restate the floor: `if p.count("mode appendix sourced from state") != 3:` failing with `PIN FAIL: mode appendix sourcing count %d != 3 in prompt-templates.md (two blueprint paragraphs plus one successor leg; a fourth copy is a deviation-list leak)`, and update the block comment to record the exact-count choice as the appendix-floor backlog row's disposition (the layered guarantee gives at-least-three; the exact form adds the leaked-copy direction; the r1 F21 shrink suggestion stays overflowed) [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` GREEN (the current prompt-templates.md carries exactly the three sanctioned copies; a nonzero exit here is a re-derivation failure, stop and re-derive before proceeding) [class: REPOSITORY_TEST]
- [x] Commit: `test: mode-appendix sourcing floor restated as the exact total 3` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the zcode.md existence pin keeps with its residual direction documented

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh` GREEN after the edit; the pin count is unchanged

- [x] RED: `grep -c "the suite's only guard on zcode.md's sourcing span" scripts/check_maintenance_pins.sh` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Keep `pin "recipe mode appendix clause"` and extend its comment with the residual-direction record in the r1 F14 comment style: the pin is the suite's only guard on zcode.md's copy of the sourcing span (the layered checks and the exact count run on prompt-templates.md; the same-file siblings pin different spans - the directive-wording span, the normalization, the canonical template literal, the recipe-region conjunct), so its alone-guarded direction is a surgical deletion or reword of the sourcing span in zcode.md's mode-appendix clause, and the pin's disposition per the r3 row's Item 2 is keep-and-document, not fold [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` GREEN [class: REPOSITORY_TEST]
- [x] Commit: `test: document the zcode.md existence pin's residual failure direction` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the Step 0 rearm-on-touch bullet splits into named sub-bullets

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh` GREEN after the split; the needle spot-list below all present; the dated ledger entry prepended

- [x] RED: `grep -c '^- rearm-on-touch check: consult' agents/skills/maintenance/SKILL.md` (expect 1 today, 0 after the split, because the parent bullet's opening clause moves under the first named sub-bullet with its pinned contiguous span intact) [class: REPOSITORY_TEST]
- [x] Split the single rearm-on-touch bullet into named sub-bullets under the same check: `Consultation` (the state-first decision, the cannot-decide events, the staleness escape, the live-bound condition and its suppression scope, the recognition rule, and the whole-check listing gate), `Bookkeeping` (the three listing-gated edits, their listing-derived scope, and the staleness bound on the touch surface), `Self-heal` (the divergence and removal legs, the verifiable-echo discipline, the primitive prechecks, the refusal records and their structured first lines, the attempt bound), and `Shared adoption guards and consumer` (the Step 0 adoption guards, the no-listing inertness rule, the child-duty precedence sentence, and the `scripts/rearm_on_touch.py` consumer paragraph); a contract boundary may fall at the semicolon where the bullet's own sentence chains the listing gate and the bookkeeping, and the clause punctuation bytes stay untouched (a sub-bullet may begin lowercase where the semicolon seam leaves it so); the state-first placement pin's contiguous span `rearm-on-touch check: consult the scheduler state file first` is never severed by an inserted marker; no clause text changes, no clause moves between contracts, and every cross-reference inside the bullet keeps its antecedent; a pin that the split still breaks is updated in this task and this task's Files [class: IMPLEMENTATION_REQUIRED]
- [x] Needle spot-list verified present verbatim after the split (one span per contract, byte-exact against the current bullet): "consult the scheduler state file first" (Consultation), "its three bookkeeping edits per the State file semantics" (Bookkeeping), "delete the record and create the parent per the runtime overlay's recipe" (Self-heal), "it mirrors this bullet's state-first classification" (Shared) [class: REPOSITORY_TEST]
- [x] Run `bash scripts/check_maintenance_pins.sh` GREEN; a broken pin row is updated in this task (the pin edits ride this plan), never left red [class: REPOSITORY_TEST]
- [x] Prepend the dated ledger entry (the ledger is newest-first) naming this plan and recording the structural split (no semantic change, no blueprint body change, the companion pins kept green), per the ledger's own convention [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skills: split the Step 0 rearm-on-touch bullet into named sub-bullets` [class: IMPLEMENTATION_REQUIRED]

### Task 4: whole-plan gates

Files:
- `docs/history/plans/2026-10-03-pins-suite-simplification.md`

Evidence:
- the full Validation Commands block

- [x] Run the full Validation Commands block GREEN (the pins suite, the grep probes, the em-dash and hygiene gates) [class: REPOSITORY_TEST]
- [x] Verify the simplification record is complete: both dispositions landed (the exact-count restatement as the appendix-floor row's disposition, the existence pin kept with its residual direction as the r3 row's Item 2 disposition), the split recorded in the ledger, and the Gist's layered derivation matches the landed suite bytes [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: pins-suite simplification record` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```
bash scripts/check_maintenance_pins.sh
grep -c 'mode appendix sourcing count %d != 3' scripts/check_maintenance_pins.sh   # exactly 1
grep -c "the suite's only guard on zcode.md's sourcing span" scripts/check_maintenance_pins.sh   # exactly 1
grep -c '^- rearm-on-touch check: consult' agents/skills/maintenance/SKILL.md      # exactly 0 after Task 3
bash scripts/check-no-em-dash.sh added-lines --base HEAD
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Evaluation Criteria

1. The sourcing count floor is the exact total 3 scoped to prompt-templates.md with the layered derivation recorded and the suite GREEN (Task 1).
2. The zcode.md existence pin is kept with a truthful residual-direction comment (its alone-guarded direction named, the sibling pins' span distinctness recorded), and the suite's pin count is unchanged (Task 2).
3. The Step 0 bullet is split into the four named sub-bullets with every clause byte preserved, the semicolon seam allowed with punctuation untouched, the state-first placement pin's contiguous span unsevered, the needle spot-list verbatim, the suite GREEN, and the ledger entry prepended (Task 3).
4. No new checks were added; both dispositions are restatement or documentation only, per the entry's authoring constraints, with each disposition attributed to the backlog row that owns it.

## Done When

- Every checkbox is `[x]`, the Validation Commands are GREEN, and the review rounds returned ready with zero blocking findings.
- The plan is landed; per the execution lane closure (operator directive, 2026-10-02) this plan is authored and landed, never executed.

## Assumptions

- The layered derivation reflects the current suite bytes; a peer landing that reshapes the re-arm paragraphs before execution re-derives the exact total before restating, per the Gist's stop-and-re-derive rule.
- The split's sub-bullet boundaries (four groups, the semicolon seam allowed) are an authoring choice within the entry's named contracts; a future pass may regroup without re-grilling as long as clause bytes stay preserved and no pinned contiguous span is severed.
- The pins suite runs GREEN at authoring time; any peer pin landing mid-cycle is reconciled by re-running the suite before each commit.

Decision points requiring a grill: none remain.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-21-pins-appendix-floor-redundancy.md`: covered by this plan's Task 1 (the floor's exact-count restatement is that row's own disposition, its Candidate fix); folded here and deleted.
- `docs/history/backlog/2026-09-21-r3-design-simplification-residuals.md`: covered by this plan's Task 2 (the existence pin's keep-and-document is that row's Item 2 disposition); folded here and deleted.
