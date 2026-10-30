# Plan: Safe Local Tmp Sweep and Active Session Identity
Backlog origin: docs/history/backlog/2026-10-09-done-recursive-tmp-sweep-safety.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-27-plan-review-done-recursive-tmp-sweep-safety[-p<identity-token>]-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 3h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-09-done-recursive-tmp-sweep-safety.md (session 01a17c5c-b1b6-7c02-8203-5bc9bf7f9ab3)

## Terms

- **Active session slug**: The execute-plan identity derived by stripping a leading date from a dated plan filename or directory, as defined in execute-plan Step 0.4.
- **Dedicated tmp root**: A repository-contained scratch directory whose final component is `tmp` or `.tmp` and whose raw configured path reaches it without following symlinks.
- **Candidate identity**: The candidate object's device, inode, and file type recorded before quarantine and checked again before deletion.
- **Quarantine**: A short-lived, same-root private directory used to move a candidate atomically before its identity is checked again.
- **Content-confirmed marker**: A `run-start-*` marker accepted by the done sweep's existing session-window derivation.
- **Session window**: The interval anchored by the two newest content-confirmed `run-start-*` markers: the newest marks the current run and the strictly older marker is the previous-run anchor; the existing single-marker manifest-and-ledger witness remains governed by `derive_session_window`.
- **Closeout baseline**: The execute-plan session's run-start file that witnesses possible transfer-out. Its presence identifies a proof-family directory that remains protected independent of age. It may be in either the canonical-slug directory or its date-prefixed sibling (`<YYYY-MM-DD>-<slug>`); only the directory containing the baseline is protected.


## Why

The docs-tmp sweep compares pending plan filenames with execute-plan session directories using different identities, and a direct probe reproduced deletion of a live session's worker log. Its recursive path-based removal also has unresolved root and candidate replacement races that can target unverified local content.

## Gist & Examples

TLDR: Match active sessions by the canonical plan slug and make local tmp deletion verify root and candidate identity, protecting run evidence with the code-quality driving force.

Before: A pending `2026-10-10-live-plan.md` does not match `execute-plan/live-plan/`, so the sweep can remove its active worker and review logs as archived.
After: The sweep recognizes the date-stripped slug, only traverses a dedicated repository tmp root through pinned no-follow directory descriptors, and deletes a candidate only after an atomic quarantine step confirms the checked identity.
Edge cases: Broad, external, or symlinked roots are left untouched; an intermediate symlink or root replacement stops deletion; a replaced candidate is restored when safe or retained in quarantine and reported; unknown owners, both content-confirmed markers, and protected scratch remain; the gate still exits zero for retained candidates.

## Outcome

The existing docs-tmp sweep keeps active execute-plan evidence and removes only candidates it can prove eligible under a stable, dedicated scratch root.

- Date-bearing plan names resolve to the canonical date-stripped session slug, so every pending plan keeps its matching session regardless of state-file contents. Archived sessions with a closeout proof family remain protected independent of age; archived sessions without that proof family follow the existing archive rule.
- The configured repository tmp root is checked from its raw value and opened component by component without following symlinks; broad and external roots cause a report-only skip.
- Candidate deletion revalidates object identity after quarantine. Execute-plan directories follow pending-plan identity and local closeout proof-file eligibility; recognized ownerless standalone scratch follows existing docs-sync and session-window rules, while unknown or unclassified candidates remain reported.
- Existing markers, protected scratch, local bytes outside the eligible set, docs-branch separation, and zero-exit reporting remain intact.

Gate delta: none. The existing docs-tmp-sweep remains nonblocking and returns zero for retained or skipped candidates; no gate, validator, lock, ledger, ceremony, refusal class, schema field, or dispatch pause is added. Blocking review-layer duties: none added; the existing plan review remains.

## Assumptions

- The origin severity sentence is stale: its Source and Impact describe one verified 2026-10-10 deletion of active worker and review logs. Recurrence is unknown; retain medium severity because the witnessed effect was local run-evidence loss and only one occurrence is established. Evidence: `docs/history/backlog/2026-10-09-done-recursive-tmp-sweep-safety.md` and the direct probe recorded in the authoring requirements buffer.
- Current `tmp_dir` is `docs/tmp`. Permit repository-contained roots ending in `tmp` or `.tmp`; reject external roots until an explicit need and a mechanically enforceable designation are established. Adding an external-root attestation setting is more machinery than the current repository requires. Evidence: `.ai-playbook/facts.md` and the r9-r12 review findings summarized by the origin.
- Preserve current candidate eligibility and standalone scratch age/session-window rules. Execute-plan proof-family directories remain protected independent of age under the later landed retention contract. This plan repairs identity and deletion safety; it does not introduce a new lifetime policy. Evidence: `scripts/done_sweep_gates_lib.py` and the investigation prompt.
- For recognized standalone scratch, the existing synced-and-older-than-window rule is a point-in-time eligibility policy, not an open-descriptor liveness guarantee. The final post-quarantine mtime check is its snapshot; writes completed before the snapshot are retained, while this plan does not claim coordination with writes after it. The witnessed active execute-plan log loss is handled by plan identity and closeout-baseline ownership instead. Evidence: `scripts/done_sweep_gates_lib.py` and the 2026-10-10 origin reproduction.
- The newest two content-confirmed run-start markers, `review-loop*`, `code-review/`, and `handoff/` remain protected by their existing contracts. Evidence: `agents/skills/done/SKILL.md`.
- Root and candidate races can be tested deterministically at the sweep's filesystem-operation seam; the implementation will stop before deleting any object whose recorded identity no longer matches.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep local tmp deletion separate from docs-branch synchronization.
- Keep retained and skipped candidates informational with the existing zero-exit behavior. Do not add a new blocking gate, validator, lock, ledger, or required ceremony.
- Delete only recognized eligible content under a verified dedicated tmp root. Preserve unknown-owner content, symlinks, protected scratch, and any object whose identity cannot be confirmed.
- Reuse execute-plan Step 0.4's session identity contract and existing facts parsing; do not add a second identity registry or tmp-root configuration.

## Evaluation Criteria

- Active plan sessions use the canonical date-stripped slug and are never reported as archived when their plan remains pending.
- Broad roots, external roots, root ancestors, and raw paths that escape by symlink are rejected before traversal or deletion.
- Intermediate symlink insertion and root replacement leave replacement targets untouched.
- Candidate replacement after eligibility checking leaves replacement bytes intact, either restored to the source name or retained in the reported quarantine location. A same-inode update is retained while its canonical plan remains pending or that directory contains a closeout proof file; archived content in directories without proof files becomes removable only after the existing eligibility checks pass.
- Unknown owner and file type remain reported; both content-confirmed markers, protected scratch trees, and all local bytes outside the eligible set remain unchanged.
- Archived sessions without a closeout proof family remain removable under the existing archive rule; a closeout proof file keeps its own containing directory retained independent of age.
- Retained/skipped rows remain informational and `GateResult.rc` remains zero.

**Quality dimensions:**
- Correctness: pending-session identity and archive eligibility agree with the current plan and run contracts, including age-independent retention for the closeout proof family.
- Safety: every destructive operation remains beneath a qualified pinned root and applies only to a still-eligible candidate; pending-plan identity and closeout proof-family presence govern execute-plan session retention independent of age.
- Preservation: protected, unknown, replaced, and out-of-scope bytes survive unchanged and have a report reason.

**Done when:** the focused sweep suite covers the slug mismatch, root validation and replacement races, candidate replacement, unknown ownership, marker immunity, protected scratch, unchanged local bytes, and the informational zero-exit contract; the done skill describes the same behavior; plan readiness passes.

**Ship when:** none; no deployed or external release condition exists.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 1), (Task 2), and (Task 3); limit production edits to `gate_docs_tmp_sweep`, `_sweep_execute_plan_sessions`, and directly called helpers
- `agents/skills/done/SKILL.md` (Task 3); limit edits to the docs-tmp-sweep contract and its integration text

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 1), (Task 2), and (Task 3); add deterministic witnesses to the existing sweep coverage

**Plan-related extension:** only files required to complete a listed task or to close a direct contract inconsistency introduced by it. Report the path and reason before editing any other file.

**Out of scope; reject unless plan-related:**
- Docs-branch synchronization behavior and archive roots; this plan owns only local tmp cleanup.
- New blocking gates, validators, locks, ledgers, persistent quarantine records, or external-root configuration.
- Unrelated done gates, retention policies, execute-plan session formats, and other backlog rows.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh --files scripts/done_sweep_gates_lib.py scripts/test_done_sweep_gates_lib.py agents/skills/done/SKILL.md
python3 scripts/plan_readiness.py docs/history/plans/2026-10-27-done-recursive-tmp-sweep-safety.md
```

### Task 1: Match live execute-plan sessions by the canonical plan slug

Context surface: this task and the plan's Terms and Standing constraints; execute-plan Step 0.4 owns the canonical session slug.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `GateContext` in `scripts/done_sweep_gates_lib.py`

- [x] In `_sweep_execute_plan_sessions`, derive each pending plan's active session identity using the canonical date-stripped slug, including dated plan files and dated charter files, rather than comparing the raw filename stem. Reuse the existing date-prefix helper where it covers the supported shape; do not add an identity registry. [class: IMPLEMENTATION_REQUIRED] (already landed in `a91ad2c5b`)
- [x] Given a date-bearing pending plan and a session directory whose basename is its canonical date-stripped slug and which contains a worker log, expect the session and log to remain and the report to identify the plan as pending. [class: REPOSITORY_TEST]
- [x] Given an archived date-bearing plan and a canonical-slug log directory without a proof file, expect removal under the existing archive rule; given a separate date-prefixed sibling containing a proof file, expect that sibling and its bytes retained independent of age. Outcomes are independent of `runtime_state.json` and docs-branch presence. [class: REPOSITORY_TEST]
- [x] Given a pending plan whose filename has a date prefix and a canonical date-stripped session directory, expect the session and its evidence to remain regardless of `runtime_state.json`; the report names the matching pending plan. [class: REPOSITORY_TEST]
- [x] Keep nested pending-plan discovery and the landed closeout proof-family retention behavior: pending plan identity preserves the matching session, while archived directories containing proof files remain retained independent of age. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the implementation and regression as `fix: preserve active tmp sessions by canonical plan slug`. [class: IMPLEMENTATION_REQUIRED] (already landed in `a91ad2c5b`)

### Task 2: Qualify and pin the local tmp root

Context surface: this task and the plan's Terms and Standing constraints; `GateContext` supplies the configured root, and `facts_paths` owns raw and resolved facts parsing.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `GateContext` in `scripts/done_sweep_gates_lib.py`

- [x] Read the raw `tmp_dir` value through `facts_paths.resolve_toml_key_raw` and compare it with the facts-resolved path before destructive traversal. Accept only a repository-contained terminal `tmp` or `.tmp` directory; reject filesystem root, home, repository root or ancestors, broad documentation containers, external roots, and any raw in-repository path that resolves through a symlink. [class: IMPLEMENTATION_REQUIRED]
- [x] Open each component from a trusted repository descriptor using no-follow directory opens, verify its device/inode/type, and traverse relative to pinned descriptors. If root acquisition or a later identity check differs, stop deletion and report remaining candidates. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a broad-root value, an external root, or an intermediate symlink escape, expect no candidate or external sentinel to be changed; given the configured dedicated tmp root, expect normal eligible candidates to remain discoverable. [class: REPOSITORY_TEST]
- [x] Replace an intermediate component after validation and replace the root after acquisition; expect the replacement target to remain byte-identical and the report to state that cleanup was skipped. [class: REPOSITORY_TEST]
- [x] Keep each unsafe-root result informational with the existing zero-exit contract; add no new blocking path. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the root qualification and identity checks as `fix: constrain tmp sweep to pinned scratch root`. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Revalidate each deletion candidate and document the contract

Context surface: this task and the plan's Terms and Standing constraints; `GateResult` owns the informational result, and `agents/skills/done/SKILL.md` documents the cleanup boundary.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `GateResult` in `scripts/done_sweep_gates_lib.py`

- [x] For each otherwise-eligible candidate, atomically move it into a newly reserved private quarantine directory beneath the pinned root, then recheck device, inode, and file type before applying the candidate class's current eligibility rules. [class: IMPLEMENTATION_REQUIRED]
- [x] For recognized standalone scratch, recheck docs-sync state and session-window modification time after quarantine. A same-inode update observed before this final check makes the candidate ineligible; the final mtime observation is the policy snapshot, and this plan adds no writer lock or process-liveness probe for writes after that snapshot. [class: IMPLEMENTATION_REQUIRED]
- [x] For execute-plan directories, recheck canonical pending-plan identity and local closeout proof-file presence after quarantine. Docs-sync and standalone session-window rules do not apply to execute-plan directories. [class: IMPLEMENTATION_REQUIRED]
- [x] For execute-plan session directories, derive canonical date-stripped plan slugs. Preserve a session while its plan remains pending; after archive, retain each directory containing closeout proof files independent of age; directories without proof files remain eligible under the existing archive rule. `runtime_state.json` is not an eligibility signal. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the existing recognized one-off standalone scratch classes eligible under the current docs-sync and session-window checks even when they have no plan owner; preserve and report unknown file types, symlinks, and unclassified candidates. Do not add a liveness registry or lock. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a candidate replaced after its eligibility check, expect replacement bytes to survive at the original name or in the reported quarantine location. [class: REPOSITORY_TEST]
- [x] Given a same-inode candidate whose execute-plan owner is pending, expect retention after quarantine revalidation; after the plan is archived and its closeout proof family is absent, expect removal only if all other current eligibility checks pass. [class: REPOSITORY_TEST]
- [x] Given an otherwise-removable recognized standalone candidate whose same inode is updated after its first stale-eligibility check but before the final deletion decision, expect the post-quarantine mtime recheck to retain the updated bytes and report the reason. [class: REPOSITORY_TEST]
- [x] Given a recognized one-off standalone file that is docs-synced and outside the session window, expect removal; given the same class never synced, inside the window, or with uncertain sync state, expect retention; given an unknown file type, expect retention and a reason. [class: REPOSITORY_TEST]
- [x] Given an unknown owner, unknown filename type, or symlink candidate, expect it to remain and be reported without following the link. [class: REPOSITORY_TEST]
- [x] Given current and previous content-confirmed run-start markers and the protected review-loop, code-review, and handoff scratch trees, expect them to remain; given unrelated local bytes outside the eligible set, expect byte-for-byte preservation. [class: REPOSITORY_TEST]
- [x] Given an archived session directory containing a closeout proof file, expect that directory and its bytes retained independent of age; an associated directory without a proof file remains independently eligible under the archive rule. [class: REPOSITORY_TEST]
- [x] Verify eligible stale content still follows the existing rules and all retained, skipped, or failed candidates remain informational with exit zero. [class: REPOSITORY_TEST]
- [x] Update only the `done` docs-tmp-sweep contract to describe the qualified root, pinned traversal, candidate revalidation, retained-content reporting, and unchanged docs-branch separation. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit the implementation, tests, and contract as `fix: revalidate tmp sweep candidates before deletion`. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-09-done-recursive-tmp-sweep-safety.md`: implemented by this plan; the origin row was covered by this plan and is deleted in this completion pass.
