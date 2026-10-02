# Plan: Evidence-integrity fences: record re-derivation, resolve-at-use digests, base-branch immutability

Backlog origins (scope of record):
- docs/history/backlog/2026-10-02-stale-read-record-derivation-fence.md
- docs/history/backlog/2026-10-02-sha-resolution-at-use-fence.md
- docs/history/backlog/2026-10-02-base-branch-commit-immutability.md

Driving force: code-quality (closed-taxonomy note: the three origins declare `reliability`, which is outside the taxonomy; the work is defect-prevention fencing over agent-recorded evidence, classified here as code-quality with the one-line justification that all three origins cite same-day 2026-10-02 witnesses of silent evidence corruption, so park-triage would take it as a witnessed fix-class-adjacent fence)

Plan review record: the staging series docs/reviews/2026-10-02-plan-review-evidence-integrity-fences-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Durable records written by agent sessions can no longer rest on a single stale-false tool read, a hand-expanded digest, or a silent history rewrite of a landed commit.

- A record-bearing claim (user-facing report, memory file, backlog row, fact-asserting commit message) is re-derived from disk by two independent commands immediately before the record write; a cross-check mismatch stops the write until resolved.
- Full digests used in state-changing commands or durable records are produced by a resolving command at use time, and landing helpers take refs instead of literal digests wherever the tool accepts them.
- Base-branch commits are immutable once landed: corrections land as additive follow-ups, amend is confined to a session's own unlanded branch, a guard stops the commit path once a base-branch amend is detected with HEAD on the base branch, and the post-landing completion duty reports a foreign amend entry on the base-branch reflog.

Gate delta: three additions, each priced by its paying witness. (1) A new record-write refusal rule (stop on two-command cross-check mismatch) - a fix-class-adjacent refusal-path addition on a fence-class origin whose origin body cites the completed 2026-10-02 silent-corruption incident as the witness; the three class-default alternatives are recorded: adding a sanctioned exit does not exist here (the defect is a silent false read, not a blocked action), removing a false positive does not exist (the tool output itself is the false positive and cannot be edited), simplifying the flow does not exist (the record channels are the workflow's own outputs). (2) A new resolve-at-use rule over landing helper invocations - text-plus-documentation extension of the existing repository precision guideline, priced by the 2026-10-02 fabricated-digest witness; no new refusal class is added (the CAS existence check that refused the witnessed slip already exists). (3) One new refusal class in the landing guard family (refuse an amend attempt when HEAD is the base branch) plus one reflog-scan report arm - priced by the 2026-10-02 18:09 witnessed amend of a peer's landed tip; the class-default alternative of prose-only records was refused because the sibling origin body (docs/history/backlog/2026-10-02-sha-resolution-at-use-fence.md) records that prose alone did not hold at typing time, and the immutability origin body records that the peer-safety lesson (lesson 6) does not cover amend of a landed commit, so no existing guard owns the shape. No removals: no existing gate, refusal class, or protocol layer is deleted or narrowed.

## Terms

- **Record-bearing claim**: a fact statement about repository state written into a durable channel (a user-facing report, a memory file, a backlog row, a commit message, a session note) whose wrongness outlives the session.
- **Two-command disk re-derivation**: immediately before a record write, re-derive the claimed fact with two independent commands: an existence claim via a filesystem probe (`ls`/`stat`) plus a git probe (`git cat-file -e <tip>:<path>` or `git show <tip>:<path>`); an absence claim via a working-tree `grep` plus `git grep` at the tip commit. A cross-check mismatch stops the record write until resolved.
- **Resolve-at-use**: a full digest used in a state-changing command or a durable record is produced by `git rev-parse`, `git log --format=%H`, or `git show -s --format=%H` at the moment of use; landing helper invocations pass refs (branch names, `HEAD`, relative forms) rather than literal digests wherever the tool accepts them.
- **Base-branch immutability**: once a commit is reachable from the base branch it is never amended; corrections land as additive follow-up commits; amend is legal only inside a session's own unlanded branch before the landing critical section.
- **Skill-gate marker**: the per-(project, session) consent marker the plans skill refreshes before every plan-file write (agents/hooks/skill-gate/README.md); this session keys it to the authoring worktree root.

## Assumptions

- The three origins are one plan because PLAN-PROMPTS (docs/history/backlog/PLAN-PROMPTS.md, the 2026-10-02 investigate-anchored entry) groups them as one authoring payload with per-arm scope; basis: the operator-authored prompt names all three arms and their wiring sites verbatim.
- The exec-stale-base-clobber-fence origin (docs/history/backlog/2026-10-02-exec-stale-base-clobber-fence.md) shares the execute-plan landing critical-section surface; this plan edits that surface once and the clobber-fence work sequences after it rather than double-wiring; basis: the PLAN-PROMPTS coordination clause and the vendored-sync single-pass rule.
- The landing guard family invocation sites are the execute-plan landing critical section and the done skill's Step 3 pre-commit region; a repo-local guard copy is probed first, then the deployed `$HOME/.ai-playbook/scripts/` copy, matching the reverse-squash-guard convention; basis: the execute-plan landing paragraph's existing guard deployment text read on disk 2026-10-02.
- The read-freshness helper is a standalone small script with its own test file, not an extension of an existing validator, because its inputs (a path and a claimed state) do not match any existing gate's signature; basis: the origin's suggested-fix item 3 and a probe of scripts/ showing no mtime-vs-tip comparer on disk.
- Each origin's `Class: fence-class` line matches its body (all three cite completed same-day incidents and ask for fences over new exits); no class disagreement to record.
- The guard's refuse condition scopes to HEAD on the base branch with a pending amend, not a blanket amend ban, because the origin's expected-state text makes amend legal inside a session's own unlanded branch; basis: docs/history/backlog/2026-10-02-base-branch-commit-immutability.md Expected section, read 2026-10-02.

Decision points requiring a grill: guard refuse condition scope - resolved by the origin's own expected-state text (amend is legal inside a session's own unlanded branch, so only the base-branch shape is refused); source: docs/history/backlog/2026-10-02-base-branch-commit-immutability.md, read 2026-10-02; affected sections: Task 3 checklist items; remaining points - none remain (the operator-authored PLAN-PROMPTS entry fixes the per-arm wiring sites, the helper-script opt-in, and the authoring-only lane; receipts recorded in docs/history/backlog/PLAN-PROMPTS.md on 2026-10-02)

## Gist & Examples

TLDR: three same-day silent-corruption witnesses get fenced - record writes re-derive from disk twice, digests resolve at use time, and landed base-branch commits become immutable - named force: code-quality (witnessed defect prevention).

Example of the record-derivation arm: before writing "plan X is unexecuted" into a report, the session runs `ls docs/history/plans/completed/ | grep X` and `git cat-file -e HEAD:docs/history/plans/completed/2026-10-02-x.md`; today a stale-false `ls` (witnessed 2026-10-02 ~17:17) wrote the wrong conclusion to a user-facing report and a memory file; with the fence the git probe contradicts the filesystem probe and the write stops until resolved. Example of resolve-at-use: a landing tail needs the CAS old value; instead of expanding a 7-character display prefix by hand (witnessed 2026-10-02, refused by the CAS existence check), the tail runs `git rev-parse refs/heads/main` and passes the ref itself where the helper accepts one. Example of immutability: a peer wants one extra .gitignore line on a commit landed four minutes ago (witnessed 2026-10-02 18:09); instead of amending the base-branch tip, the change lands as its own commit naming the commit it extends; the guard refuses the amend shape at the landing tail, and the reflog scan reports any `commit (amend)` entry on the base reflog that the landing critical section did not author.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each rule's wiring site is named with a verbatim anchor verified on disk; the guard script's refuse and report conditions match the origin's expected-state text exactly.
- Traceability: each of the three arms cites its origin path and its witness inside the plan and inside the landed skill text, so a future reader re-derives rather than inherits.
- Restraint: no new protocol layer, no scheduler state field, no new reconcile row class; the guard is one small script with two subcommands and its own tests.

**Done when:**
- The two-command re-derivation rule with the mismatch stop is present in the done skill's Step 7 region, the investigate skill's record-write rules, and the maintenance skill's record arms, each citing the stale-read origin.
- The resolve-at-use rule is present in the execute-plan landing critical section, the done skill's landing/verification arms, and `scripts/landing_parentage_gate.py`'s argument documentation.
- The immutability rule is present in the execute-plan landing section, the done skill, and lesson 6 of `docs/maintenance/development_lessons.md`; `scripts/base_branch_amend_guard.py` exists with `check-head` and `reflog-scan` subcommands, both tested.
- `scripts/read_freshness_probe.py` exists and is tested.
- The public hygiene scan and the em-dash added-lines gate exit 0 on the changed bytes.

**Ship when:**
- Nothing beyond Done when: the plan has no deployed, cross-team, or human-owned surface.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md` *(modified; record-derivation and resolve-at-use and immutability rule insertions)*
- `agents/skills/investigate/SKILL.md` *(modified; record-derivation rule insertion)*
- `agents/skills/maintenance/SKILL.md` *(modified; record-derivation rule insertion)*
- `agents/skills/execute-plan/SKILL.md` *(modified; resolve-at-use and immutability insertions in the landing critical section)*
- `scripts/landing_parentage_gate.py` *(modified; argument documentation only)*
- `scripts/read_freshness_probe.py` *(new)*
- `scripts/base_branch_amend_guard.py` *(new)*
- `docs/maintenance/development_lessons.md` *(modified; lesson 6 extension)*

**Tests:**
- `scripts/test_read_freshness_probe.py` *(new)*
- `scripts/test_base_branch_amend_guard.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/reconcile_post_landing.py`; reason: the amend report arm is invoked at the landing completion duty as a guard-script subcommand, not a new row class in the reconcile script (Gate delta restraint); changing it is out of scope.
- `docs/history/backlog/2026-10-02-exec-stale-base-clobber-fence.md`; reason: the clobber fence sequences after this plan and is not edited here.

## Validation Commands

Authoring-time record (plans rules 19, 22, 29): the structural pre-round gate passed clean on 2026-10-02 (`python3 scripts/plan_readiness.py --pre-round`, exit 0, no review record consulted); the em-dash touched scan and the public hygiene scan both exited 0 over the plan bytes; rule 19 RED-today probes were executed against the current tree: the `--help` resolve pin currently FAILS (no resolve sentence exists in `scripts/landing_parentage_gate.py` help yet - the gate is RED-today and flips GREEN at Task 2), the per-skill record-rule greps currently FAIL in all three skills (the rule does not exist yet), and the lesson-6 amend grep FAILS today (`grep -c amend` over `docs/maintenance/development_lessons.md` returns 0); the task-level test commands are RED-today by construction (both test files are new). Path verification: `scripts/check-no-em-dash.sh`, `scripts/plan_readiness.py`, and `scripts/validate_review_staging.py` all exist on disk (verified 2026-10-02).

```bash
python3 scripts/test_read_freshness_probe.py
python3 scripts/test_base_branch_amend_guard.py
python3 scripts/landing_parentage_gate.py pre-swap --help 2>&1 | grep -q "resolve.*rev-parse" || { echo "resolve-at-use doc missing in pre-swap help"; exit 1; }
python3 scripts/landing_parentage_gate.py post-landing --help 2>&1 | grep -q "resolve.*rev-parse" || { echo "resolve-at-use doc missing in post-landing help"; exit 1; }
for f in agents/skills/done/SKILL.md agents/skills/investigate/SKILL.md agents/skills/maintenance/SKILL.md; do grep -qi "two-command disk re-derivation" "$f" || { echo "record rule missing in $f"; exit 1; }; grep -q "2026-10-02-stale-read-record-derivation-fence" "$f" || { echo "origin citation missing in $f"; exit 1; }; done
grep -qi "resolve-at-use" agents/skills/execute-plan/SKILL.md || { echo "resolve rule missing"; exit 1; }
grep -qi "base-branch immutability" agents/skills/execute-plan/SKILL.md || { echo "immutability rule missing"; exit 1; }
grep -qi "amend" docs/maintenance/development_lessons.md || { echo "lesson 6 extension missing"; exit 1; }
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

(The term-anchor greps are case-insensitive on purpose: the tasks insert the Terms definitions verbatim, and the definitions carry the head forms `Two-command disk re-derivation`, `Resolve-at-use`, and `Base-branch immutability`; the `--help` pins target the two SUBCOMMAND help outputs because top-level argparse help does not render subparser argument help - verified at authoring time.)

### Task 1: two-command record re-derivation rule and freshness helper

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/investigate/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/read_freshness_probe.py` *(new)*
- `scripts/test_read_freshness_probe.py` *(new)*

Evidence:
- `python3 scripts/test_read_freshness_probe.py`; covers the helper's probe verdicts
- `grep -qi "two-command disk re-derivation" agents/skills/done/SKILL.md`; covers the rule wiring in the done skill

- [x] Insert the two-command disk re-derivation rule (Terms definition, verbatim) into the done skill's Step 7 outcome-reporting region (`## Step 7: Report outcome to the user`), the investigate skill's record-write standing rules (the bullet owning the fresh-read drift rule, investigate/SKILL.md:58 family), and the maintenance skill's record arms (the turn-output and decision-reason channels), each insertion citing docs/history/backlog/2026-10-02-stale-read-record-derivation-fence.md and the 2026-10-02 ~17:17 witness [class: IMPLEMENTATION_REQUIRED]
- [x] Create `scripts/read_freshness_probe.py`: given `--repo`, `--path`, and `--claim {present,absent,stale}`, run the filesystem probe and the git probe at the tip commit and print one verdict line (`match`, `mismatch: <which command>`, or `unresolvable: <path>`), exit 0 on match, 1 on mismatch, 2 on tool failure or unresolvable. Probe definition per claim: `present` - filesystem probe is `ls`/`stat` on the path, git probe is `git cat-file -e <tip>:<path>`; `absent` - filesystem probe is the path being absent on disk, git probe is `git cat-file -e <tip>:<path>` failing; `stale` - filesystem probe is the path's mtime compared against the tip commit's timestamp (mtime predating the tip supports staleness), git probe is the worktree bytes equalling the tip blob (`git show <tip>:<path>` byte-compare), so the verdict flips only on the byte comparison [class: IMPLEMENTATION_REQUIRED]
- [x] `ReadFreshnessProbeTest#test_present_match`; given a tracked file present in the worktree and at HEAD, expects verdict `match` and exit 0 [class: REPOSITORY_TEST]
- [x] `ReadFreshnessProbeTest#test_absent_mismatch`; given a file present on disk but deleted at HEAD (claim `absent`), expects verdict `mismatch` naming the filesystem probe and exit 1 [class: REPOSITORY_TEST]
- [x] `ReadFreshnessProbeTest#test_stale_mismatch`; given a file whose worktree mtime predates the tip commit's timestamp while its bytes equal the tip blob (claim `stale`), expects verdict `match`; and with bytes differing from the tip blob, expects `mismatch` naming the git probe [class: REPOSITORY_TEST]
- [x] `ReadFreshnessProbeTest#test_unresolvable_path`; given a path unknown to both the filesystem and the tip commit, expects verdict `unresolvable` and exit 2 [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `python3 scripts/test_read_freshness_probe.py` [class: REPOSITORY_TEST]

### Task 2: resolve-at-use digest rule

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- `scripts/landing_parentage_gate.py`

Evidence:
- `grep -qi "resolve-at-use" agents/skills/execute-plan/SKILL.md`; covers the rule wiring
- `python3 scripts/landing_parentage_gate.py pre-swap --help 2>&1 | grep -q "resolve.*rev-parse" && python3 scripts/landing_parentage_gate.py post-landing --help 2>&1 | grep -q "resolve.*rev-parse"`; covers the argument documentation pin

- [x] Insert the resolve-at-use rule (Terms definition, verbatim) into the execute-plan landing critical section paragraph 4 (Land under the lock), citing docs/history/backlog/2026-10-02-sha-resolution-at-use-fence.md and the 2026-10-02 fabricated-digest witness; the rule states refs are preferred over literal digests in helper invocations and any digest argument is produced by `git rev-parse` at the moment of use [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the same rule into the done skill's Step 3 pre-commit region (`## Step 3: Commit Uncommitted Changes`) and its landing receipt verification guidance (the docs-branch verification block region) with the same citation [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `scripts/landing_parentage_gate.py` subparser argument help for `--pre-tip` and `--new-commit` (pre-swap subparser) and `--pre-tip` and `--default-ref` (post-landing subparser) with the sentence that values are resolved via `git rev-parse` and refs are accepted and preferred over literal digests; top-level help does not render subparser argument help, so the pinned probes target `pre-swap --help` and `post-landing --help` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect exit 0: `python3 scripts/landing_parentage_gate.py pre-swap --help 2>&1 | grep -q "resolve.*rev-parse" && python3 scripts/landing_parentage_gate.py post-landing --help 2>&1 | grep -q "resolve.*rev-parse"` [class: REPOSITORY_TEST]

### Task 3: base-branch immutability rule and amend guard

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/done/SKILL.md`
- `docs/maintenance/development_lessons.md`
- `scripts/base_branch_amend_guard.py` *(new)*
- `scripts/test_base_branch_amend_guard.py` *(new)*

Evidence:
- `python3 scripts/test_base_branch_amend_guard.py`; covers the guard's refuse and report conditions
- `grep -qi "base-branch immutability" agents/skills/execute-plan/SKILL.md`; covers the rule wiring

- [x] Insert the base-branch immutability rule (Terms definition, verbatim) into the execute-plan landing critical section beside the landing-op uniqueness rule, citing docs/history/backlog/2026-10-02-base-branch-commit-immutability.md and the 2026-10-02 18:09 witnessed amend of a peer's landed tip; mirror into the done skill's Step 3 pre-commit region (`## Step 3: Commit Uncommitted Changes`) and Step 7 reporting guidance [class: IMPLEMENTATION_REQUIRED]
- [x] Extend lesson 6 of `docs/maintenance/development_lessons.md` (the ref-move peer-safety lesson) with the immutability rule and the pointer that a cited sha is expected to stay reachable and immutable, so an amend surfaces as a cross-check mismatch [class: IMPLEMENTATION_REQUIRED]
- [x] Create `scripts/base_branch_amend_guard.py` with two subcommands: `check-head --base-branch <name>` exits 1 (refuse) when HEAD is the named base branch and the last reflog entry on HEAD (`git reflog -1 --format=%gs`) reads `commit (amend)`, exits 0 otherwise; `reflog-scan --repo <root> --base-branch <name> --since <pre-tip-sha> [--allow-sha <sha>]...` reports every `commit (amend)` entry on the base branch's reflog newer than the given sha whose new commit is not listed among the repeatable `--allow-sha` values (the current landing critical section passes the shas it authored; an amend of a base-branch tip the landing did not author is therefore always reported), printing one report row per entry and exiting 1 when any is found, 0 when none, 2 on tool failure [class: IMPLEMENTATION_REQUIRED]
- [x] `BaseBranchAmendGuardTest#test_check_head_refuses_base_amend`; given a scratch repo whose HEAD is the base branch and whose last reflog entry is `commit (amend)`, expects exit 1 [class: REPOSITORY_TEST]
- [x] `BaseBranchAmendGuardTest#test_check_head_allows_branch_amend`; given a scratch repo whose HEAD is a feature branch with an amend reflog entry, expects exit 0 [class: REPOSITORY_TEST]
- [x] `BaseBranchAmendGuardTest#test_reflog_scan_reports_foreign_amend`; given a scratch repo with an amend entry on the base branch reflog after the since-sha and no matching `--allow-sha`, expects exit 1 and one report row naming the entry [class: REPOSITORY_TEST]
- [x] `BaseBranchAmendGuardTest#test_reflog_scan_allows_landing_authored_amend`; given the same amend entry with its new commit passed via `--allow-sha`, expects exit 0 [class: REPOSITORY_TEST]
- [x] `BaseBranchAmendGuardTest#test_reflog_scan_clean`; given a scratch repo with only ordinary commits after the since-sha, expects exit 0 and no rows [class: REPOSITORY_TEST]
- [x] Wire the guard at the two live sites: in the execute-plan landing critical section `check-head` runs before the CAS ref move (a refusal takes the deferred-landing path) and `reflog-scan` runs inside the post-landing completion duty beside the reconcile receipt with the landing's own commit shas passed as `--allow-sha` and its exit code and rows recorded; in the done skill's Step 3 pre-commit region (`## Step 3: Commit Uncommitted Changes`), before each commit operation, `check-head` runs and a refusal stops the commit path once a base-branch amend is detected (ordinary additive commits are unaffected), because the witnessed actor - a session amending the base tip outside any landing critical section - executes the done skill's commit region with HEAD on the base branch, the only live invocation site for the refuse condition [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_base_branch_amend_guard.py` [class: REPOSITORY_TEST]

### Task 4: validation

Files: none (verification only)

- [x] Run → expect exit 0: the full Validation Commands block above [class: REPOSITORY_TEST]
- [x] Run → expect exit 0: `bash scripts/check-no-em-dash.sh touched` [class: REPOSITORY_TEST]
- [x] Run → expect exit 0: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` [class: REPOSITORY_TEST]
- [x] Run → expect exit 0 per round record: `python3 scripts/validate_review_staging.py --hard <round-md-path> --source-plan <round-bytes-file>` for each authored round record [class: REPOSITORY_TEST]
- [x] Run → expect exit 0: `python3 scripts/plan_readiness.py` on the final bytes [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-02-base-branch-commit-immutability.md`: the base-branch immutability rule landed in the execute-plan landing section and the amend-shape fence arm (scripts/base_branch_amend_guard.py `check-head`), both citing this origin; execution evidence docs/reviews/2026-10-03-exec-review-evidence-integrity-fences-r1.md.
- `docs/history/backlog/2026-10-02-sha-resolution-at-use-fence.md`: the resolve-at-use digest rule landed in the execute-plan landing section citing this origin (full digests produced by a resolving command at use time; refs preferred over literal digests in helper invocations).
- `docs/history/backlog/2026-10-02-stale-read-record-derivation-fence.md`: the record-bearing claim re-derivation rule landed in the done skill's Step 7 (done/SKILL.md) citing this origin (two-command disk re-derivation before any durable record write; mismatch stops the write); all three origins fold-deleted 2026-10-04 in the backlog-root fold pass.
