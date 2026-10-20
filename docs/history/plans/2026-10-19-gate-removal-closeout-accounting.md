# Plan: Gate-Removal Closeout Accounting

Backlog origin: `docs/history/backlog/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md`
Backlog origin: `docs/history/backlog/2026-10-19-gate-removal-manifest-lookup-skips-branch-closeout.md`
Backlog origin: `docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md`
Backlog origin: `docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md`
Backlog origin: `docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md`
Driving force: code-quality + efficiency
Plan review record: `.ai-playbook/reviews/2026-10-19-plan-review-gate-removal-closeout-accounting-r*.md`
Execution budget: 3.0h total, largest task 1.5h

## Terms

- **PLAN_SLUG:** The execute-plan session directory name; for a date-prefixed plan file it is the filename after removing the leading date and extension, and for a dated plan directory containing `PLAN.md` it is the directory name after removing the leading date.
- **Destination history:** Commits reachable from the target branch being used to prove that branch content has landed.
- **Exact tree match:** A destination-history commit whose complete Git tree object is identical to the source branch tip's tree.
- **Completed-plan archive twin:** The archived completed-plan copy associated with the active source plan.
- **Legacy no-manifest skip:** The existing informational branch-closeout result when neither supported migration manifest filename is present.
- **Proven branch tip:** The branch commit OID captured once by `gate-removal` and rechecked after its content and worktree checks.
- **Ancestry-accounted branch:** A branch whose current tip is an ancestor of destination history, proving its content is landed.
- **Exact-tree-only branch:** A branch whose complete tree matches destination history but whose tip is not an ancestor; the content is accounted, but the branch is retained.
- **Branch disposition:** The gate's content-accounting result and branch-retention reason, carried with its proven OID.
- **Operator branch closeout:** A quiesced sequence for an ancestry-accounted or exact-tree-only branch with passing identity and artifact checks; it removes an on-disk candidate if present, then deletes the unchanged ref only after confirming no linked worktree remains.
- **Branch-only gate:** Branch accounting for a ref with no linked worktree, using an explicit branch and migration manifest instead of a worktree path.
- **Legacy changed-path proof:** The existing changed-path content-scope result; it can report landed content but never authorize deletion of a non-ancestor branch.
- **Reverse containment:** The worktree being removed resolves inside an absolute external reviews home.

## Why

The closeout gate can miss a dated plan's migration manifest, reject a citation that cannot be repaired by migration, and fail to recognize a branch snapshot already present in destination history. Its standalone command also repeats the subcommand in help output, while the documented header boundary does not match the code's actual rule. The reverse-containment residual is specifically a worktree located inside an absolute external reviews home; the existing refusal for a reviews home inside the worktree protects the only copy of review records and remains in force.

## Gist & Examples

TLDR: improve code-quality and efficiency by making closeout accounting follow the dated-plan slug contract and exact landed content, with actionable refusals and clear command output.

Before (today): An operator runs `gate-removal` for a dated plan and the default lookup builds a manifest directory from the dated filename, although the observed execute-plan manifest is under the undated plan slug. The producer docs say “basename without `.md`” and “slug from the plan filename,” leaving that behavior in conflict with the observed path. The gate can therefore take the legacy skip path. A branch whose entire tip tree already exists in destination history can also be preserved because no completed archive twin exists yet. A never-verifiable citation receives the same migrate remedy as missing records, and the standalone help repeats `gate-removal`.

After (this plan): Execute-plan's skill defines `PLAN_SLUG` for dated plan files and directories, and every producer and consumer uses that rule. Exact-tree, ancestry, and legacy content-scope proofs report what content has landed. Automated sweep preserves every branch ref and reports its current OID and reason. It removes only stale registrations with no on-disk directory, preserving on-disk worktrees and their artifacts. Normal and branch-only gate output can authorize operator cleanup only when ancestry or exact-tree accounting and identity/artifact checks pass. After quiescing sessions and writers, the operator checks linked worktrees; if a candidate exists, artifacts are preserved and the worktree is removed without force. The operator confirms no registration or linked worktree remains, then deletes the ref with an expected-OID compare while writers stay stopped. Any missing proof, failed guard, changed ref, dirty candidate, sibling worktree, or uncertainty leaves the on-disk worktree and ref retained. `done`, its setup wrapper, and execute-plan carry closeout results through final reporting. Unresolvable citations receive an attainable remedy; reverse containment is warning-only; help keeps the existing tool-error outcome.

Edge cases: Explicit manifest overrides and genuine legacy no-manifest skips remain supported. All automated sweep paths preserve branches, including exact-tree and ancestry-accounted refs; reports distinguish landed content from branch retention. A branch with neither proof, missing artifacts, a different identity, another live worktree, an unreadable ref, or a moved tip is retained and reported. The worktree-inside-external-reviews-home shape has no witnessed harmful catch and receives read-only warning visibility only; the existing refusal for a reviews home inside the worktree remains blocking because removal would erase the sole record copy.

## Outcome

Gate-removal accounts for the right migration records and landed content while preserving conservative removal decisions.

- Dated plans and `gate-removal` share the explicitly documented date-stripped manifest slug, and citation refusals explain an attainable repair.
- Exact branch-tip tree equality in destination history provides content accounting without requiring a completed archive twin.
- The gate captures one OID for its checks. Ancestry, exact-tree, and legacy proof account content; automated sweep retains every branch ref because existing deletion operations cannot bind proof and linked-worktree safety atomically.
- Containment diagnostics and parser output describe the actual safe behavior and existing command contract.

Gate delta: reports content disposition, branch OIDs, and worktree cleanup separately. Read-only branch-only accounting removes the archive-twin prerequisite for exact-tree proof and the required `--worktree` operand when no worktree exists. Sweep removes stale registrations only; worktrees and refs stay operator-controlled. Reverse containment remains warning-only.

## Assumptions

- The five grouped findings remain live on the authoring base; the plan review must recheck each before certification.
- Reverse-containment has no witnessed harmful occurrence. Keep any new visibility warning-only through 2027-01-19; reconsider promotion only after a true catch, a pre-registered registry-removal row, and all machinery-admission fields are present. Expected catch frequency is low based on the origin's no-witness report; false positives could create relocation noise. Review date: 2027-01-19.
- The complete tree is the accounting unit for the squash proof; commit ancestry and archive location are not substitutes for equality.
- The read-only branch-only gate addresses the three witnessed no-worktree squash cases in the exact-tree origin. Expected catch frequency is low beyond those cases; a false positive retains the ref for operator retry. Review by 2027-01-19; no automatic branch deletion or worktree-removal refusal is added.
Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Correct manifest discovery:** The execute-plan producer contract and `gate-removal` agree that a dated plan's leading `YYYY-MM-DD-` is stripped from `<PLAN_SLUG>`; explicit override, found manifest, absent manifest legacy skip, and citation-specific refusal are independently observable.
- **Conservative branch accounting:** Ancestry permits landed-content reporting; exact-tree and legacy content-scope proofs report their result; automated sweep retains all branch refs and names reasons such as identity mismatch, missing artifacts, unreadable tip, or a live sibling worktree.
- **Bounded machinery:** Reverse-containment visibility cannot block removal and names its review date and admission conditions.
- **CLI compatibility:** Help names the subcommand once, and malformed or invalid command use preserves `OUTCOME: tool_error`.

## Done when

The plan's implementation checklist is complete, the focused gate-removal checks and repository hygiene scan pass, and the final code supports every acceptance case in the plan.

## Ship when

The implementation is reviewed and merged through the repository's normal landing and worktree closeout process. No external release gate or human-owned prerequisite is introduced.

## Review Scope

- In scope: `scripts/worktree_closeout_migrate.py`, its gate-removal and `sweep --apply` behavior, `scripts/done_run.sh` sweep reporting, associated fixtures selected during execution, the `done` closeout instructions in `agents/skills/done/SKILL.md`, and the canonical execute-plan manifest naming and branch-retention contracts in `agents/skills/execute-plan/SKILL.md` plus its reference from `agents/skills/execute-plan/agent-logs.md`.
- Review concerns: exact slug derivation, legacy manifest compatibility, complete tree identity, captured-OID consistency through gate checks, refusal/remedy reachability, branch identity and artifact protections, shared-worktree protection, truthful reporting of retained squash-accounted branches, non-blocking reverse-containment visibility, header boundary semantics, parser usage, and outcome classification.
- Out of scope: unrelated closeout subcommands, changing the done-lock lifecycle, adding a gate or validator, and branch cleanup outside the exact proof and safeguards specified here.

## Validation Commands

- `python3 -m unittest discover -s scripts -p 'test_worktree_closeout_migrate.py'`
- `python3 scripts/worktree_closeout_migrate.py gate-removal --help`
- `bash scripts/scan-public-hygiene.sh`
- `bash scripts/check_maintenance_pins.sh`

### Task 1: Resolve manifests and citation refusals

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `build_gate_removal_parser` in `scripts/worktree_closeout_migrate.py`
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`
- `_gate_refusal_text` in `scripts/worktree_closeout_migrate.py`
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`

- [ ] Define the canonical `<PLAN_SLUG>` rule in `agents/skills/execute-plan/SKILL.md`: dated files strip the date and extension; dated directories with a charter strip the date from the directory name. Update bootstrap, session-manifest paths, transfer examples, and the agent logs guide; explicit override and legacy skip remain distinct. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the done gate invocation to pass the charter file inside a dated plan directory to `--plan`, so the gate can derive the directory slug. [class: IMPLEMENTATION_REQUIRED]
- [ ] Never-verifiable citations receive a citation-specific, attainable remedy, while missing migration records retain the migrate remedy. [class: IMPLEMENTATION_REQUIRED]
- [ ] The gate should resolve a date-prefixed plan named `2026-10-19-feature` to the `feature` execute-plan session directory. [class: REPOSITORY_TEST]
- [ ] The gate should resolve a dated directory plan's charter operand to the date-stripped session directory. [class: REPOSITORY_TEST]
- [ ] Execute-plan bootstrap and done's gate invocation should use the same date-stripped directory slug and charter-file operand for a dated directory plan. [class: REPOSITORY_TEST]
- [ ] Tests should resolve `<slug>` and link the agent log guide to the canonical slug definition. [class: REPOSITORY_TEST]
- [ ] The gate should use a present manifest and report the named legacy skip when absent; it should give missing citations a migrate remedy and never-verifiable citations a correction remedy. [class: REPOSITORY_TEST]
- [ ] The gate should use the explicit manifest when both derived and override paths exist. [class: REPOSITORY_TEST]
- [ ] The gate should use a valid override without a derived manifest; a missing override with a present derived manifest should produce a distinct skip without fallback. [class: REPOSITORY_TEST]
- [ ] The gate should report the named legacy skip when neither override nor default manifest exists. [class: REPOSITORY_TEST]
- [ ] The gate should accept the legacy `migration-manifest.json` filename and report the legacy no-manifest skip when neither supported name exists. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: resolve gate-removal inputs by plan slug`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Account for exact landed branch trees

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/done_run.sh`
- `agents/skills/done/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

Primary class anchors:
- `_branch_landing_content_scope` in `scripts/worktree_closeout_migrate.py`
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`
- `_remove_candidate` in `scripts/worktree_closeout_migrate.py`
- `cmd_sweep` in `scripts/worktree_closeout_migrate.py`
- `cmd_setup` in `scripts/done_run.sh`

- [ ] A tip matching any destination-history commit's full tree counts as landed without ancestry or an archive twin, but its non-ancestor branch remains retained. [class: IMPLEMENTATION_REQUIRED]
- [ ] The gate should retain the branch and report the reason when ancestry/exact-tree proof is absent or identity, artifact, or sibling-worktree checks fail. [class: IMPLEMENTATION_REQUIRED]
- [ ] Capture one branch OID for ancestry/tree checks and compare the ref; on mismatch or unreadable ref, report changed/unknown and retain the branch and any on-disk worktree for operator resolution. [class: IMPLEMENTATION_REQUIRED]
- [ ] Legacy changed-path scope is accounting evidence only; it never permits deleting a non-ancestor branch. [class: IMPLEMENTATION_REQUIRED]
- [ ] Sweep carries content disposition and proven OID; `--apply` removes only stale registrations, preserves on-disk worktrees and all branch refs, and never infers deletion from `OUTCOME: pass`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Document operator closeout: quiesce writers; clear stale registrations; use normal or branch-only gate; inventory tracked/untracked/ignored files and verify every item at destination; remove live candidates without force only after reconciliation; confirm no registration/worktree and unchanged OID; expected-OID delete while stopped. Any unverified item retains worktree/ref. [class: IMPLEMENTATION_REQUIRED]
- [ ] Report-only output separates worktree cleanup status from branch disposition; name retained refs, available OIDs, and reasons, and identify on-disk worktrees as operator-controlled. [class: IMPLEMENTATION_REQUIRED]
- [ ] `sweep --apply` removes only stale registrations with no on-disk directory; preserve and report every on-disk worktree and artifact because existing locks do not exclude ordinary writers. [class: IMPLEMENTATION_REQUIRED]
- [ ] `_run_gate_on_twin` passes the candidate's slug-resolved manifest via `--migration-manifest` alongside `--plan-identity`, and carries disposition and OID into sweep. [class: IMPLEMENTATION_REQUIRED]
- [ ] Setup and execute-plan closeout report every retained branch name, available OID, and reason through final closeout. [class: IMPLEMENTATION_REQUIRED]
- [ ] Fixtures cover exact-tree/no-match, protections, moved or unreadable refs, retained tips and registrations, and stale-registration cleanup with unchanged branch OID. [class: REPOSITORY_TEST]
- [ ] Apply fixtures cover exact-tree, legacy-only, advanced, and unreadable candidates; assert on-disk worktree/ref retention and reported disposition. [class: REPOSITORY_TEST]
- [ ] Fixtures should pass both manifest filenames for a twin whose temporary filename differs from its slug and preserve identity mismatch. [class: REPOSITORY_TEST]
- [ ] Apply should preserve on-disk worktrees/artifacts for moved refs, sibling checkout, dirty/active state, or ignored artifacts; stale absent registrations are removed with ref unchanged. [class: REPOSITORY_TEST]
- [ ] The operator-closeout fixture should retain the ref when a sibling worktree attaches after gate success but before quiescence. [class: REPOSITORY_TEST]
- [ ] Branch-only gate takes explicit `--branch` and `--migration-manifest` without `--worktree`; binds manifest identity, checks artifacts, ancestry/exact-tree proof and no linked worktree, captures/rechecks OID. Deletion in either mode requires all proof/identity/artifact/worktree checks to pass; otherwise retain ref. [class: IMPLEMENTATION_REQUIRED]
- [ ] Branch-only gate should report proof and expected OID for an accounted branch with no worktree; missing proof or any failed guard retains the ref. [class: REPOSITORY_TEST]
- [ ] Git fixtures clear inherited `GIT_*`, set fixture-local `HOME` and deterministic locale/timezone, and pass these to Git and CLI subprocesses. [class: REPOSITORY_TEST]
- [ ] Operator-closeout fixture should retain the worktree/ref when any inventoried ignored or untracked file lacks a verified destination. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: account for exact landed branch trees`. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Report containment safely and define the header boundary

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `_review_label_rest` in `scripts/worktree_closeout_migrate.py`
- `cmd_gate_removal` in `scripts/worktree_closeout_migrate.py`

- [ ] Reverse containment is surfaced as a read-only warning and cannot refuse or otherwise block removal; the output records the low expected catch frequency, false-positive cost, and 2027-01-19 review date. [class: IMPLEMENTATION_REQUIRED]
- [ ] The header extraction documentation states the exact implemented boundary: the first post-title line whose first character is `#`; test coverage distinguishes that from a general Markdown heading parser. [class: IMPLEMENTATION_REQUIRED]
- [ ] The gate should warn only when a worktree sits inside an absolute external reviews home, retain the existing refusal when the reviews home is inside the worktree, and extract labels at the documented header boundary. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: clarify gate-removal containment and header reporting`. [class: IMPLEMENTATION_REQUIRED]

### Task 4: Flatten parser usage without changing error outcomes

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `build_gate_removal_parser` in `scripts/worktree_closeout_migrate.py`
- `_GateRemovalUsageParser` in `scripts/worktree_closeout_migrate.py`
- `main` in `scripts/worktree_closeout_migrate.py`

- [ ] Standalone help presents `gate-removal` exactly once; `main` consumes the dispatch token before parsing flat options and routes the same operands and options. [class: IMPLEMENTATION_REQUIRED]
- [ ] The real `main` invocation should dispatch `--branch` with `--migration-manifest` and no `--worktree`; with passing guards, assert proof/OID output, and with a failed guard, assert ref retention. Malformed inputs retain `OUTCOME: tool_error` and the established exit status. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: flatten gate-removal command usage`. [class: IMPLEMENTATION_REQUIRED]
