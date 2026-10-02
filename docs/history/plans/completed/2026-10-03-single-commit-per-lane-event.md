# Plan: One main commit per lane event: flips, prunes, and closeouts ride their landing commit

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-03-single-commit-per-lane-event.md`

## Gist & Examples

TLDR: every lane event lands exactly one main commit by landing the closeout riders as commits on the landing branch before the critical section, so the squash carries them; fencing the residue with a check-single-commit sweep whose two-ended windows are swept at each next closeout and by a maintenance survey arm; and landing the digest-free witness rule; consistency driving force, because the census counted 66 `done:` and 51 `plans:` commits with the per-plan-slug mode at 3 to 4 commits for one change reason.

Witnessed surplus, this cycle's own landings included: plan bb2d9c67 (outcome-contract-migration-batch-1) was followed by flip f604122b and prune a4736a6e as separate main commits; the worktree-complete-landing-lifecycle plan itself consumed four (87cd4703, 83f9e13f, 65a4eccb, 53982b49). Foldability is proven on both lanes: 875594fe rode archive, coverage, and prune in one authoring commit; 82ce1aac did the same on the execution lane; and the execution lane's archive commit already rides the run branch into the squash today (the blueprint's "commit run inside this run's worktree on the run's branch and ride the final squash merge"), which is the shape this plan extends to every rider.

## Terms

- **Landing tails (the three):** the execute-plan "Land under the lock" critical section (agents/skills/execute-plan/SKILL.md), the plans self-landing closeout paragraph (agents/skills/plans/SKILL.md, "Landing closeout - origin coverage and duplicate-origin refusal"), and the maintenance overlay landing tails (agents/skills/maintenance/prompt-templates.md, the authoring payload paragraph and the execution blueprint's final-merge section).
- **Closeout riders:** the mechanical follow-up artifacts a lane event owes: coverage flip bytes (origin files' `Status:` lines), the PLAN-PROMPTS entry deletion, the archive move, the origin fold or deletion, the ownership-registry row append.
- **Rider commits:** commits on the landing branch that carry closeout riders before the landing critical section runs, exactly like the execution lane's existing archive commit; the squash commit carries them, so the tree-equality gate holds and the landing commit is the one main commit carrying the whole lane event. A rider that lands on main after the landing commit is a follow-up commit, the defect class this plan fences.
- **Prune rule:** a PLAN-PROMPTS entry is removed when its plan file exists in the plans root; evaluated against the tree the landing carries (the branch bytes the temp-index sequence reads), never against the pre-landing main.
- **Landing-claim grammar:** a commit subject starting with `plans: land ` (authoring lane event) or `done: execute ` (execution lane event). These are the two sanctioned lane-event landings; the grammar is defined here once and implemented once in the sweep.
- **Follow-up class:** a commit subject shape that only exists as landing residue, scoped by the anchor's lane kind. After a `plans: land ` anchor: the flip class (`done: mark` subject naming covered origins `by the landed ... plan`) and the prune class (`plans: prune` subject naming a PLAN-PROMPTS entry). After a `done: execute ` anchor: the closeout classes (`done: archive` and `done: fold` subjects) whose message references the same plan's kebab slug. The `done: execute` subject itself is never a follow-up: it is the sanctioned second lane event. Plan linkage (the kebab slug, its space-form phrase, the anchor's sha, or shared hyphen-token fragments) is reported metadata for the flip and prune classes, which are residues by construction, and a filter for the closeout classes.
- **Two-ended window:** a landing's forward residue window: commits reachable from `--until` (default HEAD) excluding the anchor rev and its ancestors, closed early at the first landing-claiming commit other than the anchor, and capped by `--max-window` (default 20).
- **Previous-landing anchor:** the nearest landing-claiming commit strictly below a given tip; the sweep resolves it with `--prev-landing-of <tip>` so a closeout can sweep the inter-landing window (previous lane event through this one) without external state.

## Coordination (binding, not re-litigating)

- Binds to the landed shapes of `docs/history/plans/completed/2026-10-02-worktree-complete-landing-lifecycle.md` (worktree-built landing commit, compare-and-swap ref update, tree-equality gate, reconcile receipt duty) and `docs/history/plans/completed/2026-10-01-execute-plan-squash-closeout-finalization.md` (the `execute-plan-closeout` gate and its terminal-receipt binding): their gate names, refusal classes, and tail shapes are the base; this plan re-keys their tail texts and edits no gate code (see the re-derivation note below), removing no refusal class.
- Re-derivation of the origin's arm 2 (the entry licenses re-derivation at authoring): the landed pipeline has no staging point where uncommitted riders could enter the landing commit (a dirty index blocks the rebase, staging after the squash trips the tree-equality gate, and the done-sweep gate runs after Phase 4 where the riders are already branch commits), so the staged-tree gate re-shape the origin sketch names is unreachable and is dropped; the delivered shape is rider commits on the landing branch, verified by the existing execute-plan-closeout conditions and the reconcile receipt, with the new sweep enforcing the follow-up residue class. The re-derivation and its worker-verified basis (the pinned pipeline mechanics at prompt-templates.md:202, 247 and execute-plan SKILL.md:1066) are recorded here as the arm's disposition.
- The frozen sibling entry `ref-move-integrity-fences` (live authoring claim, peer session) adds a landed-receipt arm beside the same `scripts/reverse_squash_guard.py check-landed` guard family this plan's sweep joins: coordinate pins only, whichever plan lands second re-keys the shared guard-family record lines and pin rows (the overlay record in Task 7 names this).
- The landed outcome-contract plan (`docs/history/plans/2026-10-03-outcome-contract-migration-batch-1.md`, landed bb2d9c67) already re-keyed the three tails' caller-obligation sentences; this plan authors against those post-bb2d9c67 bytes and re-keys the rider sequencing beside them, never over them.
- The execution lane closure (operator directive, 2026-10-02) means authoring only: this plan is never executed.

## Review Scope

Every task's Files path, inventoried:

- agents/skills/plans/SKILL.md
- agents/skills/maintenance/prompt-templates.md
- agents/skills/execute-plan/SKILL.md
- scripts/reverse_squash_guard.py
- scripts/test_reverse_squash_guard.py
- scripts/check_maintenance_pins.sh
- agents/skills/doc-hierarchy/SKILL.md
- agents/skills/done/SKILL.md

Gates re-checked but not edited: scripts/done_sweep_gates_lib.py (the re-derivation leaves the execute-plan-closeout gate's code untouched), scripts/validate_review_staging.py, scripts/check_plan_origins_closed.py (its --mark-covered mode is consumed, not edited). Test suites touched: test_reverse_squash_guard.py. Reviewers verify the rider-commits re-derivation against the pinned pipeline mechanics, the follow-up-class grammar against the witnessed commit subjects, the two-ended window against the vacuous-window witness, and that no gate refusal condition changed.

## Tasks

### Task 1: plans landing tail owns the pre-commit flip and prune rider commits

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- grep probes below; `bash scripts/check_maintenance_pins.sh` stays GREEN after the edit (the edits are additive text in spans no pin asserts; if an edit ever trips a pin, fix the wording or the pin row in the same task, never leave the suite red across tasks)

- [x] RED: `grep -c "before the landing commit" agents/skills/plans/SKILL.md` (expect 0 today) and `grep -c "PLAN-PROMPTS" agents/skills/plans/SKILL.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] In the "Landing closeout - origin coverage and duplicate-origin refusal (hard gate):" paragraph, after the existing `--mark-covered` sentence, pin the rider-commit sequence: the flip runs before the landing critical section and the flipped origin files are committed on the authoring branch as rider commits, so the landing commit carries them; the PLAN-PROMPTS prune rule is evaluated against the tree the landing carries and a matched entry's deletion joins the same rider commit; a flip or prune landing on main after the landing commit is the defect the check-single-commit sweep flags (Task 4) [class: IMPLEMENTATION_REQUIRED]
- [x] Name the committed-bytes precedent in the same paragraph: the covered flip's `Status: covered (<repo-relative plan path>)` witness format is the digest-free shape all closeout riders follow (the rule Task 5 lands) [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: the paragraph contains exactly one occurrence each of the flip-ordering fragment "before the landing critical section" and the prune fragment "PLAN-PROMPTS prune" (`grep -c` on each equals 1 post-edit) [class: REPOSITORY_TEST]
- [x] Commit: `skills: plans landing tail owns rider commits for the flip and prune` [class: IMPLEMENTATION_REQUIRED]

### Task 2: maintenance overlay landing tails re-key to the same sequence

Files:
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh` GREEN (audit first: `grep -n '\$P' scripts/check_maintenance_pins.sh` lists the rows asserting prompt-templates.md literals; check each row's literal against the edited spans before writing, then re-run the suite)

- [x] RED: `grep -c "PLAN-PROMPTS" agents/skills/maintenance/prompt-templates.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Re-key the payload paragraph's self-landing section: the mark-covered invocation and the PLAN-PROMPTS prune evaluation run before the critical section and their bytes land as rider commits on the authoring branch (the same branch the temp-index landing reads), and the gate re-run before the compare-and-swap keeps its existing position; append the dated overlay record line naming this plan per the overlay's record discipline (a paraphrased record, never quoting the pinned literals) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-key the execution blueprint's final-merge section (the `execution-final-merge` landing): its rider sentence names the existing branch-riding shape as the only rider surface (the archive commit's "commit ... on the run's branch and ride the final squash merge" precedent) and extends it to the origin fold or deletion and the registry row, never a main follow-up commit [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` GREEN [class: REPOSITORY_TEST]
- [x] Commit: `skills: maintenance overlay landing tails own the rider-commit sequence` [class: IMPLEMENTATION_REQUIRED]

### Task 3: execute-plan final-merge tail pins the rider-commit surface

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- grep probes below; `bash scripts/check_maintenance_pins.sh` GREEN

- [x] RED: `grep -c "rider commits" agents/skills/execute-plan/SKILL.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] In the "Land under the lock" step, before the worktree-complete critical section text, pin the rider-commit duty: where the landed result is a plan landing or a plan execution landing, the closeout riders (coverage flip bytes, PLAN-PROMPTS entry deletion, archive move, origin fold or deletion, ownership-registry row) land as rider commits on the landing branch before the critical section, exactly like the existing archive commit, so the squash commit carries them and the tree-equality gate holds; the duty sentence names them "rider commits" [class: IMPLEMENTATION_REQUIRED]
- [x] In the Post-landing reconciliation implementation paragraph, beside the existing check-landed sweep sentence, pin the residue sweep: the closeout invokes `check-single-commit --prev-landing-of <new landing tip> --until <new landing tip> --repo .` and records its receipt beside the reconcile receipt; the sentence names "rider commits" once (the sweep flags rider commits left on main after a landing) and flagged follow-ups are residue rows naming the commit, the class, and the remedy (fold into the next lane event's rider commits), never a landing refusal (the landing already happened) [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: `grep -c "rider commits" agents/skills/execute-plan/SKILL.md` equals exactly 2 (the duty sentence and the residue-sweep sentence's class reference) [class: REPOSITORY_TEST]
- [x] Commit: `skills: execute-plan final-merge pins the rider-commit surface` [class: IMPLEMENTATION_REQUIRED]

### Task 4: check-single-commit sweep beside the check-landed guard family

Files:
- `scripts/reverse_squash_guard.py`
- `scripts/test_reverse_squash_guard.py`

Evidence:
- `$PY scripts/test_reverse_squash_guard.py`; covers the landing-claim grammar, the anchor-scoped classes, the two-ended window, the previous-landing finder, the ack-file escape, and every pre-existing arm

- [x] RED (live): `python3 scripts/reverse_squash_guard.py check-single-commit --rev bb2d9c67 --repo .` exits 2 today (argparse: invalid choice), while the witnessed follow-ups exist on main: f604122b (`done: mark six outcome-contract-migration origins covered by the landed batch-1 plan`) and a4736a6e (`plans: prune outcome-contract-migration-queue entry (batch 1 landed bb2d9c67, ...)`); the invocation must exit 1 flagging both once implemented [class: REPOSITORY_TEST]
- [x] Implement the `check-single-commit` subcommand: `--rev <anchor commit>` (required unless `--prev-landing-of` is given), `--until <commit>` (default HEAD), `--repo`, `--max-window <N>` (default 20), `--prev-landing-of <tip>` (resolve the anchor as the nearest landing-claiming commit strictly below the tip), `--ack-file <path>`; implement the landing-claim grammar and the follow-up classes exactly as the Terms define them (this plan's Terms are the single grammar definition; the repo has no existing landing-message parser to reuse, the check-landed flow reads diffs only, so the grammar is authored here once and never duplicated); window: commits reachable from `--until` excluding the anchor and its ancestors, closed early at the first landing-claiming commit other than the anchor, capped at `--max-window`; flag flip-class and prune-class subjects unconditionally (residues by construction), and closeout-class subjects (`done: archive`, `done: fold`) only when the message references the anchor plan's kebab slug; report the plan linkage (kebab slug, space-form phrase, anchor sha, or shared hyphen-token fragments) in each finding line; exit 0 when clean or every finding is acknowledged, exit 1 naming each finding (sha, subject, class, linkage), exit 2 on tool failure; an `--ack-file` entry (one commit sha per line, a different grammar from check-landed's path ack file, a difference the usage text states) flips its finding to an acknowledged row in the output receipt, never a silent drop (the recorded-stop escape) [class: IMPLEMENTATION_REQUIRED]
- [x] The output receipt carries the counts (findings, acknowledged, window scanned, window bounds) so the closeout can record it beside the reconcile receipt; the usage text documents the exit vocabulary and the ack-file grammar split [class: IMPLEMENTATION_REQUIRED]
- [x] Run `$PY scripts/test_reverse_squash_guard.py` GREEN, then the live probe: `python3 scripts/reverse_squash_guard.py check-single-commit --rev bb2d9c67 --repo .` exits 1 flagging f604122b and a4736a6e, and `--prev-landing-of bb2d9c67 --until bb2d9c67` resolves the previous landing-claiming anchor below bb2d9c67 without counting bb2d9c67 itself [class: REPOSITORY_TEST]
- [x] Commit: `feat: check-single-commit sweep flags same-slug follow-up commits` [class: IMPLEMENTATION_REQUIRED]

### Task 5: digest-free committed witness rule

Files:
- `agents/skills/doc-hierarchy/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- grep probes below; census recorded in this plan (below), no historical-row rewrite

- [x] Authoring census (recorded here, not repaired): the ownership registry's audit notes embed landing digests as witnesses (`docs/maintenance/document-registry.md` rows citing "the concurrent landing 11e63b63", "completion commit 68b53910 followed by the pure archive rename 1c0fe236", "completed-path add df664ad5"), and execute-plan Step 4.1 mandates a committed `Phase <N> landed at commit \`<SHA>\`` line in a parent artifact's Status block; the coverage flip's `Status: covered (<path>)` format is the digest-free precedent; this plan lands the forward rule and never bulk-rewrites historical rows (the registry is append-oriented and the audit notes record history as written) [class: IMPLEMENTATION_REQUIRED]
- [x] RED: `grep -c "never a landing digest" agents/skills/doc-hierarchy/SKILL.md agents/skills/done/SKILL.md agents/skills/plans/SKILL.md agents/skills/execute-plan/SKILL.md` (expect 0 in all four today) [class: REPOSITORY_TEST]
- [x] In the doc-hierarchy ownership-registry row-shape section, the completion-transition guidance gains the witness rule: committed witness lines (registry audit notes on new rows, disposition sections, `Status:` lines) name repo-relative paths and dates, never a landing digest; the digest belongs to the commit message and the session-side receipts [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the same sentence in the done skill's staging step (the registry-row append guidance), the plans skill's completion bullet (the "append exactly one ownership-registry row" paragraph), and re-key the execute-plan Step 4.1 line to the digest-free shape (the phase Status line names the phase's repo-relative artifact paths and the landing's subject, never the sha); count gate: the sentence appears exactly once per file, 4 total across the four files [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `skills: committed witness lines are digest-free, paths over digests` [class: IMPLEMENTATION_REQUIRED]

### Task 6: maintenance survey batch arm for the historical residue

Files:
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh` GREEN; the live batch probe below

- [x] RED: `grep -c "check-single-commit" agents/skills/maintenance/prompt-templates.md` (expect 0 today) [class: REPOSITORY_TEST]
- [x] The overlay's survey paragraph gains the batch arm: the maintenance survey runs `python3 scripts/reverse_squash_guard.py check-single-commit --scan-window <N>` (the subcommand's batch mode: walk the last N landing-claiming commits on the base branch and sweep each one's two-ended window), reporting flagged follow-ups as the census row class with the same ack-file escape; the overlay record from Task 2 is extended to name this arm [class: IMPLEMENTATION_REQUIRED]
- [x] Live probe: the batch mode flags the witnessed pair inside bb2d9c67's window when scanned (`--scan-window` covering bb2d9c67 exits 1 listing f604122b and a4736a6e under that anchor) [class: REPOSITORY_TEST]
- [x] Commit: `skills: maintenance survey sweeps landing windows for follow-up residue` [class: IMPLEMENTATION_REQUIRED]

### Task 7: maintenance pins and coordination record

Files:
- `scripts/check_maintenance_pins.sh`
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh` GREEN with the new rows present

- [x] RED: the new pin needles are absent from the pins suite (`grep -c "check-single-commit" scripts/check_maintenance_pins.sh` expect 0 today) [class: REPOSITORY_TEST]
- [x] Add pin rows asserting the re-keyed texts after their arms exist: the plans-tail rider-commit fragment, the overlay payload's pre-critical-section ordering fragment, the execute-plan rider-commit duty sentence, the digest-free rule sentence (one file-probe per row), and the check-single-commit usage literal in the execute-plan tail; pins assert presence only and ride behind the armed behaviors per the entry's refused-alternative ruling [class: IMPLEMENTATION_REQUIRED]
- [x] Append the dated overlay record naming this plan, recording the coordination: the `ref-move-integrity-fences` sibling adds a landed-receipt arm beside the same guard family, and whichever plan lands second re-keys the shared guard-family record lines and pin rows [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh` GREEN, then the whole-plan gate battery: the two suites under `$PY`, the hygiene scan, the em-dash gate [class: REPOSITORY_TEST]
- [x] Commit: `test: maintenance pins over the single-commit tail texts` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```
PY=$HOME/.agents/venvs/ai-playbook-test/bin/python3
$PY scripts/test_reverse_squash_guard.py
bash scripts/check_maintenance_pins.sh
python3 scripts/reverse_squash_guard.py check-single-commit --rev bb2d9c67 --repo .   # exit 1 flagging f604122b and a4736a6e (both stay ackable via --ack-file once the residue is dispositioned)
python3 scripts/reverse_squash_guard.py check-single-commit --prev-landing-of bb2d9c67 --until bb2d9c67 --repo .   # exit 0 or exit 1 naming the previous inter-landing window's residue, never a tool failure
bash scripts/check-no-em-dash.sh added-lines --base HEAD
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Evaluation Criteria

1. All three landing tails own the rider-commit sequence: flips, prunes, archive moves, origin folds, and registry rows land as commits on the landing branch before the critical section, never as main follow-ups (count gates in Tasks 1-3).
2. The execute-plan-closeout gate's code, conditions, and refusal texts are untouched; the re-derivation note records why the staged-tree re-shape is dropped (no staging point in the landed pipeline) with the pinned mechanics cited.
3. The digest-free witness rule appears exactly once per owning file, 4 total, with the census and the Step 4.1 re-key recorded and no historical rewrite (Task 5).
4. The check-single-commit subcommand exists with the Terms as the single grammar definition, anchor-kind-scoped classes (the sanctioned `done: execute` lane event never flags), a two-ended window with the previous-landing finder, the ack-file recorded-stop escape, the three-valued exit vocabulary, and a GREEN suite; the live probes reproduce the witnessed pair (Task 4).
5. The maintenance survey batch arm and the pins assert the re-keyed texts; the pins suite is GREEN; the overlay record names the plan and the ref-move coordination (Tasks 6-7).

## Done When

- Every checkbox is `[x]`, the Validation Commands are GREEN, and the review rounds returned ready with zero blocking findings.
- The plan is landed; per the execution lane closure (operator directive, 2026-10-02) this plan is authored and landed, never executed.

## Assumptions

- The three tails' current bytes are the post-bb2d9c67 shapes this plan re-keys; a peer landing that moves the pinned paragraphs before execution re-keys this plan's fragments per the coordination section.
- The four execute-plan-closeout conditions' refusal texts stay untouched because the gate's code is untouched; basis: the re-derivation note above, priced by the closeout-finalization plan's gate-delta record (additions only, never removals).
- The witnessed follow-up pair (f604122b, a4736a6e) stays on main as the sweep's live fixture; if a later landing rewrites that history, the plan's probes re-derive against the then-current census per the machinery delta doctrine.

Decision points requiring a grill: none remain.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-03-single-commit-per-lane-event.md` (origin class: operator-directed, fence-class): the covering plan executed 2026-10-03; the backlog item is deleted in the same completion pass per the fold-then-delete rule; this section is its disposition of record.
