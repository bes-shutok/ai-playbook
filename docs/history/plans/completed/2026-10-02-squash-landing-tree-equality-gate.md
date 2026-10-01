# Squash-landing tree-equality gate: a squash commit whose tree diverges from the squashed branch fails before the ref swap

Backlog origin: `docs/history/backlog/2026-10-01-squash-landing-tree-equality-gate.md`

Classification: [class: fence-class] landing-recipe invariant with a spelled-command arm, a scratch-repo divergence selftest, mirror registrations, and a receipt-record clause; authoring only (this plan is not self-executing).

## Terminology and core concepts

- **Tree equality at the squash step**: after a squash merge produces the landing commit, the landing commit's tree must equal the squashed branch tip's tree (`git diff --quiet <branch> <squash-commit>` empty). A pure squash is the only sanctioned default; any subset squash must be declared at the call site.
- **The witnessed divergence**: landing `15746cae` shipped both the archived plan copy and the stale pre-execution root copy while the squashed branch tip (`e73cd109`) carried the correct archive state (root absent, completed copy present, same blob); the rename's deletion half was dropped between the branch tree and the squash commit, stranding an orphan duplicate that read as an open plan until the manual repair (`00426305`).
- **Deferred-landing path**: the landing recipes' existing refusal outcome (keep the branch and worktree, report); the tree-equality refusal joins it, never a forced landing.
- **Guard posture**: the check is read-only plumbing (a diff comparison) inside the landing critical section, between the squash commit's existence and `landing_parentage_gate.py pre-swap`; it adds no new record surface, riding the existing reconcile-receipt channel.

## Coordination

- The closeout-time detector is owned downstream by the landed execute-plan squash-closeout-finalization plan (its `test_closeout_gate_refuses_active_twin_surviving` witness catches a surviving active plan path after the fact); this plan owns only the upstream landing-time invariant, per the origin's Near-siblings contract. No terminal-receipt conditions are re-owned.
- The worktree-complete landing lifecycle (landed, archived) owns the primary-checkout staging and reconcile arms and the prestage freshness gate (staged bytes against HEAD); the tree-equality check compares squash output against the branch tree, a different surface, and inserts into the single Worktree arm that lifecycle landed.
- The done-origin-fold-delete-enforcement plan extends `check_plan_origins_closed.py` and the archive-ceremony gate in the machinery neighborhood; a peer execution of it is in flight on worktree `wt-foldel`. This plan adds new sentences and new pins and re-keys nothing; if that execution lands first and touches the same recipe sentences, its executor re-keys shared pins per its own plan, and this plan's executor re-checks the pins suite before its landing (the suite is green at this plan's base `99cc6210`).
- Neighbor pins verified to survive untouched (scanned `scripts/check_maintenance_pins.sh`): the count-gated squash and compare-and-swap pins key on command literals this plan does not remove or duplicate; the additions are new sentences and new pins only. The pins suite exits 0 at this plan's base.

## Tasks

### Task 1: the invariant sentence and the receipt clause in the execute-plan standard

Files:
- `agents/skills/execute-plan/SKILL.md`

Two insertions.

Insertion (a): in step 4 (**Land under the lock**), immediately after the sentence ending "and a refusal naming the paths defers the staging, never stages." and before "Landing-op uniqueness rule:", insert verbatim:

```markdown
Tree equality at the squash step: the landing verifies tree equality between the squashed branch tip and the produced squash commit before the parentage gates (the `landing_parentage_gate.py pre-swap` invocation spelled in the maintenance execution blueprint) and the ref move (`git diff --quiet <branch> <squash-commit>` must be empty; a non-empty diff aborts the landing before the CAS move, naming the divergent paths and taking the deferred-landing path keeping the branch and worktree; a deliberate non-pure squash says so explicitly at the call site, and silence fails closed).
```

Insertion (b): in the closeout receipt sentence beginning "The closeout records the reconcile receipt, the invocation's exit code and its one-line row summary (the restored, removed, block, wholesale, and synced counts) recorded in the run's session notes beside the landing record before the closeout ends", replace "counts) recorded in the run's session notes" with "counts) and the squash-step tree-equality check's pass result, recorded in the run's session notes".

Evidence:
- `grep -c "tree equality between the squashed branch tip and the produced squash commit" agents/skills/execute-plan/SKILL.md` prints 1
- `grep -c "and the squash-step tree-equality check's pass result" agents/skills/execute-plan/SKILL.md` prints 1

- [x] Run → expect RED: both grep Evidence commands print 0 on current bytes [class: REPOSITORY_TEST]
- [x] Apply insertions (a) and (b) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]

### Task 2: the spelled-command arm and the deviation-list entry in the prompt templates

Files:
- `agents/skills/maintenance/prompt-templates.md`

Edit (a): in the execution blueprint's spelled Worktree arm, immediately after "then squash there with `git merge --squash <branch>` followed by the commit (the landing commit's single parent is the detached tip);" and before "a conflicted squash is cleaned with", insert verbatim (the region is hard-wrapped at roughly 76 characters; insert the sentence wrapped to the region's convention, keeping the command literals unbroken):

```markdown
capture `<new-tip>` immediately after the commit and run `git diff --quiet <branch> <new-tip>` (the tree-equality check: a non-empty diff means the squash commit's tree diverges from the squashed branch tip's tree, the landing aborts before the parentage gates and the ref move, `git diff --name-only <branch> <new-tip>` names the divergent paths, and the deferred-landing path keeps the branch and worktree);
```

Edit (b): prepend one dated bullet to the file's deviation list, immediately before the bullet beginning "- Worktree-first standard consolidation (2026-09-28", verbatim:

```markdown
- Squash-landing tree-equality gate (2026-10-02, plan `docs/history/plans/2026-10-02-squash-landing-tree-equality-gate.md`; not part of the backlog source text): the execution blueprint's spelled Worktree arm captures the landing commit's id immediately after the squash commit and runs the tree-equality diff between the squashed branch tip and that commit before the parentage gates and the ref move; a non-empty diff aborts the landing naming the divergent paths and takes the deferred-landing path, and a deliberate non-pure squash must be declared at the call site (silence fails closed). The command literals are pinned and paraphrased here, never quoted.
```

Evidence:
- `grep -c "git diff --quiet <branch> <new-tip>" agents/skills/maintenance/prompt-templates.md` prints 1
- `grep -c "Squash-landing tree-equality gate (2026-10-02" agents/skills/maintenance/prompt-templates.md` prints 1

- [x] Run → expect RED: both grep Evidence commands print 0 on current bytes [class: REPOSITORY_TEST]
- [x] Apply edits (a) and (b) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]

### Task 3: the zcode mirror clause

Files:
- `agents/skills/maintenance/zcode.md`

In the merge-landing-lock registry entry, immediately after the sentence ending "and a masked rebase or merge failure aborts the landing before any staging.", append verbatim:

```markdown
The landing also verifies tree equality between the squashed branch tip and the produced squash commit before the parentage gates and the ref move (added 2026-10-02, plan `docs/history/plans/2026-10-02-squash-landing-tree-equality-gate.md`; a non-empty diff aborts before the ref move and a deliberate non-pure squash says so at the call site).
```

Evidence:
- `grep -c "added 2026-10-02, plan \`docs/history/plans/2026-10-02-squash-landing-tree-equality-gate.md\`" agents/skills/maintenance/zcode.md` prints 1

- [x] Run → expect RED: the grep Evidence command prints 0 on current bytes [class: REPOSITORY_TEST]
- [x] Append the clause [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]

### Task 4: the scratch-repo divergence selftest

Files:
- `scripts/test_squash_tree_equality.py` *(new)*

Unittest scratch-repo fixtures (the `test_prestage_freshness_gate.py` shape) proving the check's mechanics on the witnessed shape, at minimum:

- clean squash: a base commit adds a plan file; a branch renames it into the archive directory (same bytes); the squash of that branch produces a commit whose tree equals the branch tip: `git diff --quiet <branch> <squash-commit>` exits 0.
- the witnessed divergence: the same squash, then the stale source path re-added into the landing commit before it is created: `git diff --quiet <branch> <squash-commit>` exits 1 and `git diff --name-only <branch> <squash-commit>` names the re-added source path.
- byte-divergence shape: the landing commit carries the same paths as the branch tip but different bytes on one: the diff exits 1 and names that path.
- rename-with-content-change negative control: a branch renames and modifies the file; the clean squash keeps the new bytes and `git diff --quiet <branch> <squash-commit>` exits 0 (the gate is landing-fidelity-only and never false-positives on legitimate branch-side content changes), while a landing that drops the branch's edit exits 1 naming the path.

Evidence:
- `python3 scripts/test_squash_tree_equality.py` exits 0

- [x] Write the selftest; run it and record RED (module absent) [class: REPOSITORY_TEST]
- [x] Implement the selftest to the case list [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]

### Task 5: pins

Files:
- `scripts/check_maintenance_pins.sh`

Append two pins immediately after the pin line `pin "override integrity exclusion present in the skill" grep -qF 'Integrity guards are never overridable' "$S"` and before the final `[ "$fail" -eq 1 ] && exit 1` aggregation (adjacent appends from other pending plans in the same region are compatible):

```bash
pin "squash tree-equality invariant present" grep -qF 'tree equality between the squashed branch tip and the produced squash commit' "$E"
pin "squash tree-equality arm wired in the blueprint" grep -qF 'git diff --quiet <branch> <new-tip>' "$P"
```

Evidence:
- `bash scripts/check_maintenance_pins.sh` exits 0
- `grep -c "squash tree-equality" scripts/check_maintenance_pins.sh` prints 2

- [x] Append the two pins [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Evidence commands [class: REPOSITORY_TEST]

### Task 6: full-suite validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Validation Commands

```bash
python3 scripts/test_squash_tree_equality.py
bash scripts/check_maintenance_pins.sh
grep -c "tree equality between the squashed branch tip and the produced squash commit" agents/skills/execute-plan/SKILL.md   # 1
grep -c "git diff --quiet <branch> <new-tip>" agents/skills/maintenance/prompt-templates.md   # 1
grep -c "Squash-landing tree-equality gate (2026-10-02" agents/skills/maintenance/prompt-templates.md   # 1
grep -c "added 2026-10-02, plan \`docs/history/plans/2026-10-02-squash-landing-tree-equality-gate.md\`" agents/skills/maintenance/zcode.md   # 1
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Review scope

Fresh adversarial reviewers verify, on current bytes: (1) the insertion anchors exist uniquely in the three skill files (the step 4 sentence tail, the receipt sentence, and the zcode lock entry's closing sentence verbatim; the spelled-arm squash clause and its before-anchor wrap-tolerant under the region's roughly 76-character hard wrap with command literals unbroken; the deviation-list top bullet verbatim); (2) the dictated insertions carry every Evidence literal character-exactly and the count claims hold post-edit; (3) the Task 4 selftest's four cases mechanically reproduce the witnessed divergence and prove the check refuses it while never false-positiving on legitimate branch-side content changes (the re-add path lands in the diff's name-only output); (4) the tree-equality check's placement (after the squash commit, before `landing_parentage_gate.py pre-swap`) is consistent with the landed Worktree arm's ordering and does not contradict the closeout-gate plan's downstream detector or the prestage freshness gate's different surface; (5) the receipt clause extension keeps the original sentence's grammar and record channel; (6) the pins' greps target literals the insertions actually carry and the pins suite exits 0 post-edit; (7) the Validation Commands all pass on the post-edit tree.

## Assumptions

Decision points requiring a grill: refusal outcome (resolved: the deferred-landing path keeping the branch and worktree, the recipes' existing refusal outcome, never a forced landing); call-site rule for subset squashes (resolved: fail closed, a deliberate non-pure squash must be declared explicitly at the call site); receipt recording (resolved: ride the existing reconcile-receipt sentence as an added recorded item, no new record surface); mirror depth (resolved: invariant sentence in the execute-plan standard, spelled command arm plus deviation-list entry in the prompt templates, one dated clause in the zcode registry, no maintenance SKILL.md body change).

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-01-squash-landing-tree-equality-gate.md`: this plan's own promoted origin, folded here and deleted in the same completion pass per the sharpened archive gate. Execution receipt: worktree branch exec/squash-tree-eq over main 7ec423cb; all six tasks executed (RED/GREEN per task), commit f04acb43; landing squash commit ee9e953d passed the very tree-equality gate this plan spells (diff --quiet empty) before the CAS ref move. Execution review r1: ready=yes, zero blocking. Validation block green: selftest 4 cases OK, pins suite all hold, four grep counts 1/1/1/1, em-dash clean, hygiene PASS. Archive-repair note: the first archive pass (a85aafdf) shipped the pre-archive branch tree because its landing was built from HEAD^{tree} while the archive changes were still only staged, dropping this fold, the registry row, and the origin delete; repaired by exec/sq-archive-fix after the gap was witnessed at main (the root copy re-read as an open plan), and the drop itself is a live demonstration of the tree-equality lesson: the landing tree must be the committed branch tip's tree.
