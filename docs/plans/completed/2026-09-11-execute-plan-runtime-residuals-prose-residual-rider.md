# Plan: execute-plan-runtime-residuals prose-residual rider fold

Backlog origin (scope of record; moved to `docs/history/backlog/completed/` at this plan's completion): `docs/history/backlog/2026-09-10-execute-plan-runtime-residuals-plan-prose-residuals.md`

Fold target: `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` (certified r8, digest `9e11e4f89a93ed661ea76a57a41785c84ccc56d134b116240191819596131470`, ready=yes zero blocking, not yet executing).

Finding source: `docs/reviews/2026-09-10-plan-review-execute-plan-runtime-residuals-r8.md` (findings F1-F5 plus one overflow row; all non-blocking, dispositioned to backlog per the backlog-capture rule because r8 was the single allowed fresh certification round).

Plan review: `docs/reviews/2026-09-11-plan-review-execute-plan-runtime-residuals-prose-residual-rider-r*.md` (latest staged round; findings folded before the next review).

Guidance: `projects/.ai-playbook/agent_workflow_guidelines.md` (plan quality sections).

## Terms

- **Rider**: a backlog item absorbed into an existing authored plan whose execution touches the same file or mechanism; folding into a digest-frozen certified plan costs one re-cert round.
- **Fold**: applying a review finding's prescribed fix as one precise text edit to the fold target, with the exact current span and its replacement pinned in the task.
- **Re-cert round**: one fresh blind review-plan round on the post-fold digest that restores the fold target's readiness binding.
- **Digest binding**: the readiness gate invariant that the latest review round's sidecar `source_digest` equals the sha256 of the current plan bytes; any fold breaks it until the re-cert round lands.
- **Policy anchor**: the out-of-tree 0600 per-run file the fold target's Task 2 adds under `~/.execute-plan/`; its per-run keying is the subject of finding F1.

## Assumptions

- assume the scope is exactly the six dispositioned residuals (r8 F1-F5 plus the overflow row); no other plan-text change enters this plan; basis: the rider item names the r8 round as its source, enumerates the findings, and is the scope of record.
- assume the fold lands pre-execution of the fold target; basis: authoring probes on 2026-09-11 (zero checked checkboxes in the fold target, no execution session logs for it under `docs/tmp/execute-plan/`, r8 is the latest round on disk, no r9 exists).
- assume the rider is NOT added to the fold target's backlog-origins list and the fold target's Task 12 five-origin close-out stays untouched; the rider's fix content is plan text only and its lifecycle (archive) is owned by this plan; basis: the rider item prescribes plan-text edits only, and the fold target's Task 12 enumerates exactly its five origins.
- assume the fold target's certified tree assumptions (RED-today sweeps, symbol locations) stay valid through this plan; basis: every prescribed edit targets plan prose or the plan's own Validation block, never production sources.
- assume `scripts/plan_readiness.py` takes the plan path positionally and the re-cert sidecar mirrors the r8 sidecar's schema_version 1 contract; basis: probe on 2026-09-11 (`python3 scripts/plan_readiness.py docs/plans/2026-09-10-execute-plan-runtime-residuals.md` printed `readiness OK` on the then-current bytes) and the r8 sidecar on disk.

Decision points requiring a grill: F1 anchor keying = add a manifest-path-digest component to the per-run anchor key and strengthen the existing cross-talk witness in place instead of adding a new witness bullet; source: the r8 review F1 comment option (b) plus the rider item's suggested fix wording, selected under the standing accept-recommended-options pre-authorization; date: 2026-09-11; affected sections: Task 2 and Gist & Examples of the fold target. Overflow disposition = extend the Validation sweep to the inventory file instead of rewording the implement bullet; source: the r8 overflow row plus the authoring probe showing `runtime-adapter:codex` present in the inventory today, so the extended sweep is RED-today and flips GREEN with the fold target's Task 5; date: 2026-09-11; affected sections: Validation Commands and Notes of the fold target.

## Design Invariants (CR Guard)

- Containment: the six prescribed edits are the only semantic changes to the fold target; every edit pins its exact current span; any other diff hunk in the fold target is a defect.
- Immutability: `docs/reviews/**` rounds r1 through r8 and `docs/plans/completed/**` stay byte-untouched; the only review write is this plan's own re-cert round artifact and sidecar.
- Gate integrity: the fold target's Validation block stays `bash -n` clean; its RED-today probes still fire on the pre-fold tree; the UL#264 pin-versus-prescription audit runs after the folds and before the re-cert round.
- Certification monotonicity: the re-cert round reviews the exact post-fold bytes; exit requires `ready=yes` with zero unresolved blocking findings on that digest and a green readiness gate on the same bytes; no exit on a pre-fold digest.
- Sibling-count safety: the F1 fold strengthens the existing cross-talk witness bullet in place and must not change any witness count, so the fold target's Task 2 GREEN count bullet and every other count-bearing sentence stay untouched.

## Gist & Examples

The fold target closed five backlog origins and certified at r8 (ready=yes, zero blocking) with six non-blocking residuals recorded to backlog instead of regenerating a ninth round past its reconciliation bound. This plan applies exactly those six as precise text folds, pre-execution, so the fold target's executor works from precise text, and then restores the digest binding with one fresh blind re-cert round.

Before (today): an implementer picks up the fold target to execute it. Task 3's GREEN gate says "the driver discovery command passes with the seven new witnesses" while the same task's RED bullet counts "the eight behaviors" and its implement bullet says "the eight fixes", so the implementer cannot tell whether a witness was dropped. Task 2's anchor keying claims "parallel sessions never share an anchor" on a repo-hash plus plan-slug key, but two sessions running the same plan slug on different manifests resolve the identical anchor file, and the cross-talk witness only exercises different slugs, so it cannot fail under the very collision the claim denies.

After (this plan): the GREEN bullet reads "passes with the eight new witnesses" and all three Task 3 count sentences agree on eight. The anchor key becomes repo-hash, plan-slug, plus a short digest of the resolved manifest path: the key-derivation line names the component, the cross-talk witness drives both a different-slug pair and a same-slug pair on different manifest paths, and the contract-doc bullet carries the same sharpened claim. Task 5's expected-ids update bullet scopes the update to the full compared shape; Task 4's receipt-skip step states the locked owner initialization still persists the owner when the write is skipped; Task 9 carries a migration note for old-shape done-lock session files; and the Validation block's `runtime-adapter:codex` sweep covers the inventory file as well as the module.

Worked example, one per finding. F1: today `test_anchor_scoped_per_run_no_cross_talk` is trivially green for different slugs because different slugs imply different anchor directories by construction; after the fold the same witness also drives two same-slug claim generations on different manifest paths and asserts each run's witnesses verify against the anchor derived from that run's own manifest path, so the sharpened keying claim has a witness that can fail. F2: the executor builds Task 3's GREEN checklist from the gate sentence; after the fold the gate says eight, matching the eight listed witnesses, and the checklist cannot under-count. F3: today the update bullet reads "so the canonical-id expectation matches the shrunken eligible set", which a literal implementer satisfies while leaving stale per-profile rows that fail `verify_activation`'s field comparison; after the fold the bullet enumerates the full compared shape (profiles shrunk to codex, aliases kept for all nine runtimes, deferred_ids grown to the eight-entry set). F4: today "skip the receipt write when no profile was supplied" is silently coupled to owner persistence because the receipt refresh is the only site that persists the derived owner; after the fold the bullet states the locked owner initialization still persists `manifest["owner"]` when the write is skipped. F5: today Task 9 rewrites the session-file field name with no word on in-flight locks; after the fold the bullet records that old-shape session files already carry the token, so the token-only release path reads them unchanged and `stale-clean` remains the operator escape.

## Evaluation Criteria

**Quality dimensions:**

- Correctness: each fold's replacement text delivers the finding's fix as dispositioned in r8 and the rider item; every presence probe matches its prescribed replacement span and was RED on the pre-fold bytes.
- Scope containment: the fold commits touch only the files each task names; the fold target's diff is exactly the pinned spans and nothing else.
- Gate integrity: the fold target's Validation block stays `bash -n` clean; the UL#264 pin-versus-prescription audit passes after the folds; the extended inventory sweep is RED pre-fold and flips GREEN with the fold target's Task 5.
- Certification: one fresh blind full-panel round on the post-fold digest reports `ready=yes` with zero unresolved blocking findings, and `scripts/plan_readiness.py` is green on the final bytes.

**Done when:**

- All tasks are checked off with their commits landed and each task's scoped gates green at its task point.
- The Validation Commands block exits 0 on the final tree.
- The re-cert round artifact and its v1 sidecar exist with `source_digest` equal to the sha256 of the final fold-target bytes, verdict `ready=yes`, zero unresolved blocking findings, and `python3 scripts/plan_readiness.py docs/plans/2026-09-10-execute-plan-runtime-residuals.md` exits 0 on those bytes.
- The rider item is moved to `docs/history/backlog/completed/` marked `Status: done` with a one-line disposition note, and this plan is archived per the plans lifecycle with ownership-registry rows appended in the same pass when the registry convention is present.

**Ship when:**

- The re-certified fold target proceeds to implementation under the execute-plan skill's normal Phase 0 branch setup; the fold target's own Ship-when items (staged-package re-activation, real-runtime exercise, human merge) remain the fold target's, not this plan's.
- A human reviews and merges this plan's changes; push and deploy remain explicit human actions.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Fold target and deliverables:**

- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md` (the six fold sites and the Validation block line)
- `docs/reviews/` re-cert round artifact `-r9.md` *(new; Task 3)* and its `.stats.json` sidecar *(new; Task 3)*
- `docs/history/backlog/2026-09-10-execute-plan-runtime-residuals-plan-prose-residuals.md` (completion move plus `Status: done`)
- `docs/plans/2026-09-11-execute-plan-runtime-residuals-prose-residual-rider.md` (this plan; checkbox updates and archive move)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract this plan changed. If the link to this plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `scripts/**` and `projects/**` production sources; this plan edits plan text only, and concerns about the behavior the fold target will implement belong to the fold target's own execution and reviews.
- `docs/plans/completed/**`; completed-history artifacts are body-immutable (doc-hierarchy refusal rule); this plan edits none of them.
- `docs/reviews/**` rounds r1 through r8; they are records, not edit targets.
- Peer-session files and any other dirty worktree content; classify before touching, and leave peer-owned work alone.

## Cleanup scope ledger

- Base ref: the execute-plan Phase 0 branch base current at execution start. All work lands as this plan's own commits.
- Task-owned paths: the four explicit must-fix paths above.
- Frozen areas: `docs/plans/completed/**`; `docs/reviews/**` except the Task 3 round artifact pair; peer-session files.
- Deletion permissions: none (the rider item move is a `git mv` plus a status-line edit, not a deletion).
- Mechanical check: each task's commit is name-only checked against that task's declared file list. Peers share the execution branch, so a repo-wide base-diff comparison is unsatisfiable by joint state and is deliberately not used; commit-scoped checks bind this plan's own work without pinning peer tree state.

## Validation Commands

```bash
set -u
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 1

PLAN="docs/plans/2026-09-10-execute-plan-runtime-residuals.md"

expect_match() {
  pattern="$1"; shift
  grep -q -F -- "$pattern" "$@" || { echo "required pattern absent: $pattern" >&2; exit 1; }
}

expect_no_match() {
  pattern="$1"; shift
  rc=0
  grep -q -F -- "$pattern" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then echo "forbidden pattern present: $pattern" >&2; exit 1; fi
  if [ "$rc" -ge 2 ]; then echo "grep error rc=$rc for: $pattern" >&2; exit 1; fi
}

# F1: sharpened keying probes removed 2026-09-11 - the anchor mechanism itself was
# deferred by the threat-model decision (guidelines section 64; fold target Task 2 now
# carries the launch-record snapshot instead), so the F1 span pins no longer apply.
# The two forbidden-span sweeps below are kept: both old forms stay absent.
expect_no_match 'so parallel sessions never share an anchor' "$PLAN"
expect_no_match '<plan-slug>/policy-anchor.json' "$PLAN"

# F2: witness count probe updated 2026-09-11 - the threat-model shrink removed the
# missing-baseline witness from Task 3, so the aligned count is now seven (five new
# behaviors plus two characterization pins).
expect_match 'with the seven new witnesses' "$PLAN"
expect_no_match 'eight new witnesses' "$PLAN"

# F3: expected-ids update scoped to the full compared shape.
expect_match 'keep `aliases` for all nine runtimes' "$PLAN"
expect_no_match 'so the canonical-id expectation matches the shrunken eligible set' "$PLAN"

# F4: owner persistence preserved under the receipt skip.
expect_match 'the locked owner initialization still persists' "$PLAN"

# F5: old-shape lock migration note present.
expect_match 'already carry `DONE_LOCK_TOKEN`' "$PLAN"
expect_match '`stale-clean` operator path' "$PLAN"

# Overflow: inventory sweep keyed alongside the module sweep.
expect_match "expect_no_match 'runtime-adapter:codex' projects/.ai-playbook/execute-plan-runtime-inventory.toml" "$PLAN"

# Re-cert: fresh round bound to the final bytes.
R9="$(ls docs/reviews/*plan-review-execute-plan-runtime-residuals-r9.md 2>/dev/null)"
[ -n "$R9" ] || { echo "missing re-cert round artifact (-r9.md)" >&2; exit 1; }
R9SIDECAR="$(ls docs/reviews/*plan-review-execute-plan-runtime-residuals-r9.stats.json 2>/dev/null)"
[ -n "$R9SIDECAR" ] || { echo "missing re-cert round sidecar (-r9.stats.json)" >&2; exit 1; }
LATEST_MD="$(ls docs/reviews/*plan-review-execute-plan-runtime-residuals-r*.md | sort -V | tail -1)"
grep -q 'Verdict: ready=yes' "$LATEST_MD" || { echo "latest round $LATEST_MD is not ready=yes" >&2; exit 1; }
python3 scripts/plan_readiness.py "$PLAN" || { echo "readiness gate failed on final bytes" >&2; exit 1; }

# Completion pass: rider archived out of the open backlog.
test -f docs/history/backlog/completed/2026-09-10-execute-plan-runtime-residuals-plan-prose-residuals.md || { echo "rider item not archived" >&2; exit 1; }
test ! -f docs/history/backlog/2026-09-10-execute-plan-runtime-residuals-plan-prose-residuals.md || { echo "rider item still in open backlog" >&2; exit 1; }
grep -q '^Status: done' docs/history/backlog/completed/2026-09-10-execute-plan-runtime-residuals-plan-prose-residuals.md || { echo "rider item not marked done" >&2; exit 1; }

bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

Notes: every presence probe is RED at authoring (each required span is absent from the pre-fold fold target; verified during this authoring) and flips GREEN exactly when its fold lands. Every forbidden-span sweep is intentionally RED at authoring (each fires on the pre-fold tree; verified during this authoring) and flips GREEN when its fold removes the span. The re-cert and completion probes stay RED until Tasks 3 and 4 land, so the full block is expected green only on the final tree at Task 4; earlier task gates run only their own scoped probes and state which probes are still expected RED at that task point. All fold-target sweeps are scoped to the fold target file only; this plan's own text quotes several of the patterns and is deliberately outside every sweep (intentional scope-based self-match immunity per the authoring rules, so a later editor must not widen the sweep targets).

### Task 1: Fold the five Low residuals (r8 F2, F3, F4, F5, overflow)

Files:
- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md`

- [x] F2 (r8 F2, Task 3 GREEN bullet): replace `passes with the seven new witnesses` with `passes with the eight new witnesses`. The RED bullet ("the eight behaviors") and the implement bullet ("the eight fixes") already say eight and stay untouched.
- [x] F3 (r8 F3, Task 5 implement bullet tail): replace `update \`scripts/testdata/execute-plan/expected-runtime-ids.json\` in the same commit so the canonical-id expectation matches the shrunken eligible set (the catalog test reads it from the repo root).` with `update \`scripts/testdata/execute-plan/expected-runtime-ids.json\` in the same commit to the full compared shape, not only the canonical-id list: shrink \`profiles\` to the single codex row carrying the new import-path entrypoint and the three receipt capabilities (\`parent_continuation\`, \`final_response\`, \`resume\`), keep \`aliases\` for all nine runtimes (the catalog test iterates them for every runtime including \`pi\`), and grow \`deferred_ids\` from the current \`pi\`-only list to the eight-entry deferral set (the seven newly deferred runtimes plus \`pi\`), because \`verify_activation\` compares \`canonical_ids\`, \`deferred_ids\`, and every \`profiles\` row's \`adapter_entrypoint\`, \`capabilities\`, and \`retry_budget\` fields (the catalog test reads the file from the repo root).`
- [x] F4 (r8 F4, Task 4 implement bullet): replace `skip the receipt write when no profile was supplied, and pass the loaded manifest through the authorization path.` with `skip the receipt write when no profile was supplied while the locked owner initialization still persists \`manifest["owner"]\` (the receipt refresh is the only owner-persistence site today, so the literal skip must not drop owner persistence for profile-less CLI runs and \`test_cli_two_processes_share_derived_owner_without_flag\` keeps passing), and pass the loaded manifest through the authorization path.`
- [x] F5 (r8 F5, Task 9 first bullet): append one sentence after `and the selftest covers release under the new shape.` reading: `Migration note: session files written by the current shape already carry \`DONE_LOCK_TOKEN\` (the generation name is written beside it as a tautological alias of the same value), so the token-only release path reads old-shape locks unchanged; any residue the new path cannot consume stays covered by the existing \`stale-clean\` operator path (age-bounded by \`DONE_LOCK_STALE_SECS\`), so no mid-session upgrade step is required.`
- [x] Overflow (r8 overflow row, Validation Commands): directly after the line `expect_no_match 'runtime-adapter:codex' scripts/runtime_capabilities.py` add the line `expect_no_match 'runtime-adapter:codex' projects/.ai-playbook/execute-plan-runtime-inventory.toml`; and append one sentence at the end of the Validation Notes paragraph reading: `The inventory \`runtime-adapter:codex\` sweep line (r8 overflow fold) was RED at this fold's own authoring and flips GREEN with Task 5 together with the module sweep.`
- [x] Run `bash -n` over the fold target's Validation Commands block (the overflow fold edits that block); expect clean.
- [x] Run → expect GREEN: the eight fold probes for F2, F3, F4, F5, and the overflow line (the `expect_match`/`expect_no_match` probe lines in the Validation Commands block above, excluding the seven F1 probes, the re-cert probes, and the completion probes), run scoped against the fold target.
- [x] Run → expect still RED at this task point: the seven F1 probes (Task 2 has not landed), the re-cert probes, and the completion probes.
- [x] Commit: `docs: fold r8 low residuals into execute-plan runtime residuals plan`

### Task 2: Fold F1, the anchor-keying sharpening (r8 F1) — SUPERSEDED 2026-09-11: the anchor mechanism this fold sharpened was deferred by the threat-model decision (guidelines section 64); the fold work landed (51fac72) and was then removed from the fold target by the deferral shrink; its Validation probes were removed accordingly

Files:
- `docs/plans/2026-09-10-execute-plan-runtime-residuals.md`

- [x] Gist & Examples, "After (this plan)" sentence: replace `a 0600 file under \`~/.execute-plan/<repo-hash>/<plan-slug>/\` holding` with `a 0600 file under \`~/.execute-plan/<repo-hash>/<plan-slug>-<manifest-hash>/\` (the per-run key adds a short digest of the resolved manifest path, so two sessions running the same plan slug on different manifests resolve distinct anchor files) holding`
- [x] `test_policy_anchor_written_at_claim` bullet: replace `<home>/.execute-plan/<repo-hash>/<plan-slug>/policy-anchor.json` with `<home>/.execute-plan/<repo-hash>/<plan-slug>-<manifest-hash>/policy-anchor.json`, and replace `<repo-hash>\` is a short sha256 of the resolved repo root;` with `<repo-hash>\` is a short sha256 of the resolved repo root; \`<manifest-hash>\` is a short sha256 of the resolved manifest path (same truncation as \`<repo-hash>\`);`
- [x] `test_anchor_scoped_per_run_no_cross_talk` bullet: replace `given two concurrent run identities (different plan slugs) in the same repo with different policy fields, expects each run's witnesses to verify against its own anchor file and neither` with `given two concurrent run identities in the same repo with different policy fields, one pair with different plan slugs and one pair with the SAME plan slug on different manifest paths, expects each run's witnesses to verify against its own anchor file (the manifest-path component discriminates same-slug runs) and neither`
- [x] Task 2 implement bullet: replace `(repo-hash plus plan-slug, so parallel sessions never share an anchor)` with `(repo-hash, plan-slug, and a short digest of the resolved manifest path, so same-slug sessions on different manifests resolve distinct anchors and the claim's witnesses verify against the anchor derived from that claim's own manifest path)`
- [x] Task 2 contract-doc bullet: replace `that the anchor is keyed per run so concurrent sessions do not interfere` with `that the anchor is keyed per run (repo-hash, plan-slug, manifest-path digest) so concurrent sessions on different manifests never share an anchor file and same-manifest sessions serialize on the manifest lock`
- [x] Sweep the whole fold target for the old path form and the old claim: `grep -c 'so parallel sessions never share an anchor'` must be 0 and `grep -c '<repo-hash>/<plan-slug>/'` must be 0 after this task; every other `plan-slug` mention stays accurate: the Terms entry is untouched, and the cross-talk bullet's rewritten text keeps the different-slugs pair alongside the new same-slug pair.
- [x] Run the UL#264 mechanical audit over the fold target: extract each Validation-pinned span and confirm it occurs in the plan's prescribed snippets exactly as pinned, plus `bash -n` over the Validation Commands block; fix both sides of any mismatch in the same edit.
- [x] Run → expect GREEN: all eight Low-fold probes from Task 1 plus all seven F1 probes, run scoped against the fold target.
- [x] Run → expect still RED at this task point: the re-cert probes and the completion probes; in particular `python3 scripts/plan_readiness.py docs/plans/2026-09-10-execute-plan-runtime-residuals.md` now FAILS because the digest binding is intentionally broken until Task 3's round lands.
- [x] Commit: `docs: sharpen policy anchor keying claim and witness in runtime residuals plan`

### Task 3: Blind re-cert round on the post-fold digest

Files:
- `docs/reviews/<execution-date>-plan-review-execute-plan-runtime-residuals-r9.md` *(new)*
- `docs/reviews/<execution-date>-plan-review-execute-plan-runtime-residuals-r9.stats.json` *(new)*

- [x] Compute and record the post-fold digest: `shasum -a 256 docs/plans/2026-09-10-execute-plan-runtime-residuals.md`.
- [x] Launch one fresh blind full-panel review-plan round (the recommended five-worker panel from review-panel-selection; prior findings NOT supplied as filter; the fold target is READ-ONLY for reviewers) on the post-fold bytes; write the round artifact as the next round number after the latest existing round for this plan (r9 at authoring) and produce its `.stats.json` sidecar in the same round, declaring schema_version 1 with `source_digest` equal to the post-fold sha256; copy the r8 sidecar as the nearest compliant example and edit it. (Executed as rounds r9 through r14, 2026-09-11; each round artifact and sidecar is schema-clean per validate_review_staging --hard.)
- [x] If the round reports blocking findings: fold them per the plans fold loop (a contract-term fold greps the whole plan for the superseded term and re-derives every matching bullet), recompute the digest, and launch the next fresh round; exit only on a fresh `ready=yes` zero-blocking round on the final bytes, never on a pre-fold digest. (NOT MET: the loop stopped at r14 under the ADR-0002 cap in fix-generates-findings non-convergence on the anchor/seed-token mechanism; rounds r9-r13 blocking folds landed as commits 51fac72, 4d3c7e1, b275a1a, 0c8d27a, 2c7d3a5; r14's five pending blocking findings plus the deferred design-alternative family are captured in `docs/history/backlog/2026-09-11-execute-plan-runtime-residuals-recert-nonconvergence.md` for a review-reconciliation pass. The fold target's latest round is r14, verdict ready=no, so the readiness gate on the fold target is intentionally red at this plan's stop state.)
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py docs/plans/2026-09-10-execute-plan-runtime-residuals.md` prints `readiness OK` on the final bytes. (Met 2026-09-11: the loop re-opened under the threat-model decision, ran r15-r17 blocking folds, and certified at r18 ready=yes zero blocking; gate exits 0.)
- [ ] Run → expect still RED at this task point: the completion probes (the rider item has not moved yet).
- [x] Commit: `docs: re-cert execute-plan runtime residuals plan after prose-residual fold` (landed as the r9-r17 fold-commit chain; final state 69b73fb)

### Task 4: Rider close-out and plan completion

Files:
- `docs/history/backlog/2026-09-10-execute-plan-runtime-residuals-plan-prose-residuals.md`
- `docs/plans/2026-09-11-execute-plan-runtime-residuals-prose-residual-rider.md`

- [x] `git mv` the rider item to `docs/history/backlog/completed/` and in the same edit mark `Status: done` plus a one-line disposition note: folded pre-execution via this plan; the fold target re-certified on the post-fold digest by the Task 3 round (completed 2026-09-11; the disposition also records the threat-model supersession of F1).
- [x] Complete this plan per the plans lifecycle: mark the remaining checkboxes, move this plan to `docs/plans/completed/`, and append the ownership-registry rows for this plan and the rider item in the same pass when the doc-hierarchy registry convention is present.
- [x] Run → expect GREEN: the full Validation Commands block on the final tree.

## Documentation Impact Assessment

- No new documentation files; no README or config section changes.
- The fold target's own documentation tasks (`runtime-contract.md`, hook READMEs, catalog) belong to the fold target's execution, not this plan; this plan only sharpens the prose that prescribes them.
- The only doc-adjacent surfaces are the fold target itself and the rider item's lifecycle move, both explicit must-fix paths above.
