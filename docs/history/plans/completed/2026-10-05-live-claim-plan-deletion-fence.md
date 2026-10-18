# Plan: fence plans-root deletion while a claim names the plan

Backlog origin: docs/history/backlog/2026-10-05-live-claim-plan-deletion-fence.md
Driving force: reliability (outside the five driving principles; justification: a witnessed peer commit deleted a certified in-execution plan outright while its claim was live, and a slightly later discovery would have stranded the plan's only copy in a worktree, so the fence ships rather than parks; park-triage would not take it: the guard extends an existing checker with pinned fixtures)
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-live-claim-plan-deletion-fence-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Plans-root file: a file under the plans home whose relative path is not inside one of the three archive state directories (completed, deferred, rejected); the protected class. The plans home resolves through the facts reader with silent fallback to the guard's hard-coded roots, stated as new code in the subcommand (the guard today imports stdlib only and hard-codes its roots).
- Claim: a claim file under the primary checkout's `docs/tmp/execution-claims/` or `docs/tmp/authoring-claims/` (the claim protocol writes claims at the primary checkout, resolved as the first `git worktree list --porcelain` worktree entry, the same resolution the post-landing-staging gate uses); the claim's stem is its basename minus `.md`. The claim read resolves the primary checkout independent of the scanned repository argument, so a boundary scan run from a run worktree still sees the live claims.
- Naming match: a claim names a deleted plans-root file when the claim's stem equals the file's basename minus `.md`, or equals the basename minus a leading dated prefix (`YYYY-MM-DD-`), following the guard's own record-stem matching rule (the shape its review-record match already uses); a claim stem that appears only as a strict subsequence of unrelated segments does not match (pinned as a non-match edge case).
- Claim-fence check: the new `check-claim-fence` subcommand of scripts/reverse_squash_guard.py; its diff source is a new `--base <ref> --head <ref>` pair (new vocabulary in the family, the nearest precedent being check-landing's source/target pair), enumerated per commit via rev-list with per-commit name-status and raw body.
- Four-outcome divergence: the subcommand adopts the repo's four-outcome contract (final `OUTCOME:` line, exits 0 pass, 1 refusal, 2 indeterminate, 3 tool error) as a named divergence from the guard family's 0/1/2-tool-failure convention (no OUTCOME: lines today); the module docstring's exit-code line documents the divergence in the same edit.
- Archive-in-same-commit: the same scanned commit that deletes a plans-root file also adds a file with the same basename under the completed archive directory (per-commit classification, so an archive landed by a later commit does not sanction the deleting commit; the witnessed recovery landing 9d6cdc75 passes its own scan while the deleting commit would have refused at its own boundary).
- Operator ack trailer: a `Plans-Deletion-Ack:` trailer in the scanned commit's message carrying the deleted path's plans-root relative path; a self-recorded committer direction in the Archive-egress-ack precedent's trust model (the committer records the direction; the check does not verify who issued it).
- Boundary scan: the fence's enforcement shape (the witnessed deletion was a direct commit no landing gate saw, and this repo carries no versioned commit hooks): every done closeout and every landing closeout runs the check over its own range before declaring completion. The done gate's range (`start_commit..HEAD`) is shared with peer commits, so its routing follows the battery's foreign-artifact treatment: a deletion inside a commit the done lib classifies foreign becomes a named report line (reported, never a gate failure; the peer's own closeout fences it), while a deletion in an own commit refuses. The landing closeout scans its own squash diff and refuses hard.
- Sanctioned exits: the three resolutions the fence's refusal names: archive the file in the same commit, stand down and restore the file, or record the operator ack trailer.

## Why

A peer commit deleted docs/history/plans/2026-10-04-review-cert-graded-binding.md outright (no archive destination) while the run's execution claim was live under the primary checkout's execution-claims directory; the landing recovered by carrying the authoritative bytes into the completed archive, but a slightly later discovery would have stranded a certified plan's only copy in a worktree. Nothing refuses that shape: the reverse-squash guard's archive check sees only the landing diff, and no commit-time or landing-time check consults the claim directories. The symmetric arm is the same hole: a queue-prune or triage edit that removes a plans-root file owes its archive-or-rejected disposition in the same commit, and nothing binds that either.

## Outcome

The claim-fence check exists in the reverse-squash guard as a per-commit range scan, and both boundary flows run it: a done closeout scans its run range with foreign-commit deletions reported and own-commit deletions refused, a landing closeout scans its squash diff and refuses hard, and every fencing refusal names the deleted path, its live claim file, and the sanctioned exits.

- scripts/reverse_squash_guard.py gains `check-claim-fence`: one subcommand in the existing family (check-staged, check-diff, check-commit, check-landing, check-single-commit, check-landed, check-archive), with the new `--base`/`--head` pair as its diff source and the four-outcome divergence documented in the module docstring's exit-code line.
- The check resolves the plans home and the tmp dir through the facts reader with silent fallback to the guard's existing hard-coded defaults, resolves the primary checkout for the claim read, and classifies per commit.
- The done sweep's gate battery gains `gate_plans_root_claim_fence` in scripts/done_sweep_gates_lib.py, a thin CLI-child gate over the run's `start_commit..HEAD` range with the foreign-commit report routing and the four-outcome child routing, registered in the GATES dict and the pre-commit phase list, with the done skill's pre-commit sweep gates enumeration amended and the registry test extended.
- The plans skill's landing closeout and the execute-plan landing paragraph's rider parenthetical gain the same invocation over the landing range with the closeout's real routing vocabulary, and the maintenance log duties' prune clause carries the symmetric arm (a pruning edit removing a plans-root file produces its archive-or-rejected disposition in the same commit and is scanned at the boundary).
- Every pin naming a reworded span updates in the same edit; fixtures land beside the mechanism.

Gate delta: one new guard subcommand with a documented contract divergence, one new done gate (a CLI-child thin gate over the checker, foreign-report routing included), two flow-text wiring spans, one battery-enumeration and registry-test amendment, and one guidance scoping. No state field, no validator change.

## Assumptions

- assume the check's home is the reverse-squash guard as a new subcommand rather than a new script; basis: the guard already owns plans-root deletion semantics (check-archive) and the archive-directory vocabulary, and the row names it as the closest existing guard.
- assume the boundary-scan shape (done closeout plus landing closeout) is the enforcement, with no host commit hook attempted; basis: the row's own fallback ("commit-time check where the host supports it, otherwise a boundary scan the done and landing flows run") and this repo's unversioned-hooks reality.
- assume the naming match follows the guard's own record-stem rule scoped to post-date-stem equality; basis: the guard's existing review-record stem match is the in-file grammar of record, the witnessed claim and plan basenames satisfy stem equality under date stripping, and a strict-subsequence rule would false-fence unrelated long basenames.
- assume the operator ack is a commit-message trailer with a self-recorded trust model; basis: the ack must survive in the artifact a boundary scan reads after the fact, and the Archive-egress-ack precedent sets the same self-recorded convention.
- assume claim presence at scan time is the liveness test, with no freshness window in the fence; basis: the claim protocol owns freshness (the stale-claim takeover path), and a stale claim still names a plan whose deletion deserves the named refusal.
- assume an absent claim directory passes silently while an unreadable git state is tool error; basis: the fence's purpose is the naming relation, and absence of claims is the normal case.
- assume the foreign-report routing for the done gate follows the battery's established foreign-artifact treatment (reported, never gate failures) and the landing flow's own-diff scan refuses hard; basis: the done lib's existing foreign classification in the shared `start_commit..HEAD` range and the foreign-artifacts-preserved-and-reported rule.
- assume the adjacency holds unchanged: this unit's file set is disjoint from the other frozen-entry units' except the gates lib, where anchors re-derive from live bytes at execution and a moved anchor re-keys its pin in the same edit; basis: the frozen entry's seam rule and the plans root.
- assume authoring runs under the standing D-4 authoring directive plus the live operator order to continue authoring without stops, so the plans skill's Phase 1 confirmation is satisfied by the frozen entry's validated record; basis: the maintenance loop's authoring blueprint under the standing operator directive.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: a plans-root file whose claim is live can no longer be deleted without its archive or an operator ack riding the same commit, a reliability fence against the witnessed data-loss near-miss.

Before (today): a peer session's queue-prune misfire deletes an in-execution plan outright; no gate sees a direct commit, and only luck (a landing that still finds the bytes) recovers them into the archive.

After (this plan): the deleting session's own done closeout, or the next landing closeout, names the deletion: the check reports it with the live claim file and the three sanctioned exits, refusing own-commit and landing-range deletions and reporting foreign-commit deletions at the done boundary; an archive move in the same commit passes, and an operator-acked deletion passes with the trailer in the message.

Edge cases pinned: a deletion whose completed-archive twin rides the same commit passes; a deletion with a live execution claim refuses naming the claim file; a deletion with a live authoring claim refuses identically; a deletion with no matching claim passes silently (the fence is the naming relation, not a general plans-root write lock); a claim stem matches a date-prefixed plan basename under post-date-stem equality, and a strict-subsequence stem does not match; a deletion whose commit message carries the ack trailer naming the path passes; an ack trailer naming a different path does not; a foreign-commit deletion at the done gate is a named report line, never a failure; an unresolvable diff source is indeterminate, never a pass; an absent claim directory passes silently; deletions inside the archive state directories are out of scope; an empty run range warning-skips at the done gate naming the reason, and an unresolvable plans home warning-skips the same gate naming its reason.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every own-commit or landing-range deletion of a protected plans-root file with a naming live claim is fenced unless the same-commit archive twin or the ack trailer is present; foreign-commit deletions are named report lines at the done gate; the witnessed 7b8d1bff shape refuses naming the claim; the sanctioned archive and ack shapes pass.
- fail-closed placement: the boundary gates route the four-outcome child contract exactly (refusal to failure, indeterminate and tool error to their buckets, a missing final line to tool error) and never read silence as a pass; the warning-skips are named, never silent.
- observability: each fenced deletion produces one refusal block naming the path, the claim file, and the three sanctioned exits; foreign-commit deletions and passes name their classification and sanction.
- maintainability: one subcommand in the existing guard family with its divergence documented in place, one thin gate over it, two sentence-scoped flow-text wirings, one enumeration amendment, fixtures beside the mechanism; the naming grammar follows the guard's own record-stem rule rather than a new grammar.

**Done when:**
- all task boxes checked; the guard suite and the sweep-gate suite pass under the venv pytest runner (`"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_reverse_squash_guard.py scripts/test_done_sweep_gates_lib.py -q` exits 0, bare `python3` off-venv fails rc 1 with a pytest import error, fail-closed); the pins suite exits 0 (OUTCOME: pass); the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-live-claim-plan-deletion-fence.md` exits 0 on the final bytes.

**Ship when:**
- a done or landing closeout in this repo refuses a plans-root deletion whose claim is live with the claim file and sanctioned exits named, and the witnessed archive-in-same-commit and operator-ack shapes pass.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reverse_squash_guard.py` (the new `check-claim-fence` subcommand and the module docstring's exit-code line only)
- `scripts/done_sweep_gates_lib.py` (the new `gate_plans_root_claim_fence` function and the gates registry and phase-list entries only)
- `agents/skills/done/SKILL.md` (the pre-commit sweep gates paragraph's new gate id insertion only)
- `agents/skills/plans/SKILL.md` (the landing closeout's pre-rider sentence span only)
- `agents/skills/execute-plan/SKILL.md` (the landing paragraph's rider parenthetical span only)
- `agents/skills/maintenance/SKILL.md` (the log duties' prune clause span only)

**Tests:**
- `scripts/test_reverse_squash_guard.py` (new claim-fence test classes)
- `scripts/test_done_sweep_gates_lib.py` (the new gate's fixture class and the registry-test amendment)
- `scripts/check_maintenance_pins.sh` (only if a re-derived anchor forces a pin re-key, in the same edit as the span move)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- the guard's seven existing subcommands: their verdicts and interfaces stay untouched (the module docstring's exit-code line is the only family-level edit).
- the claim protocol's freshness, takeover, and registration semantics: the fence reads claim presence, never judges it.
- the other execution-pipeline-friction units (read contract, early lens, done batching, continuity probe, sizing, directory shape): separate plans under the frozen entry's seam rule.
- the state schema and every other production script: no field grows, no tool changes beyond the named files.

## Validation Commands

```bash
# Guard suite (new claim-fence classes) and sweep-gate suite (the new
# gate's fixture; the venv runner is the canonical invocation; bare
# python3 off-venv fails rc 1 with a pytest import error, fail-closed)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_reverse_squash_guard.py scripts/test_done_sweep_gates_lib.py -q
# Pins: a moved anchor re-keys its pin in the same edit
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews, green from r1 on
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-live-claim-plan-deletion-fence.md
```

### Task 1: The check-claim-fence subcommand and its suite (TDD)

Files:
- `scripts/reverse_squash_guard.py`
- `scripts/test_reverse_squash_guard.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_reverse_squash_guard.py -q`; covers every criterion below at the task boundary (bare `python3` off-venv fails rc 1 with a pytest import error)
- `grep -c "check-claim-fence" scripts/reverse_squash_guard.py`; covers the subcommand presence (RED at authoring: zero hits)
- `grep -c "Plans-Deletion-Ack" scripts/reverse_squash_guard.py`; covers the ack-trailer presence (RED at authoring: zero hits)

- [x] Re-derive the anchors from live bytes: the guard's subcommand family and each member's argument shape (check-diff's `--against` plus stdin/file diff source, check-landing's source/target pair, check-archive's archive-directory handling), the module docstring's exit-code line, the guard's hard-coded plans roots and record-stem match rule, the facts reader's interface and the resolved-parent sys.path import pattern used by the sweep-gates lib, the primary-checkout resolution precedent, and the pins suite's guard surfaces; if any anchor moved from the bytes this plan quotes, update the owning pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Run → RED confirmed under the venv runner (the subcommand does not exist; the new tests fail on a missing subcommand) [class: REPOSITORY_TEST]
- [x] Implement `check-claim-fence` in scripts/reverse_squash_guard.py: a new `--base <ref> --head <ref>` pair as the diff source (new vocabulary in the family, the nearest precedent check-landing's pair shape; `--repo` keeping the family default), enumerating the range per commit via rev-list with per-commit name-status and the raw commit body; resolve the plans home and the tmp dir through the facts reader (imported over the resolved-parent sys.path pattern) with silent fallback to the guard's existing hard-coded defaults, and resolve the primary checkout (first `git worktree list --porcelain` worktree entry) for the claim read independent of `--repo`; scan per commit for deleted paths under the plans home excluding the three archive state directories; for each deleted basename, consult the primary checkout's `execution-claims/` and `authoring-claims/` for a claim whose stem equals the basename minus `.md` or the basename minus a leading dated prefix, per the guard's own record-stem rule; classify per commit: a completed-archive twin added by the same commit passes (named), a `Plans-Deletion-Ack:` trailer in that commit's message naming the path passes (named), a naming claim refuses (exit 1) with one block per deletion naming the path, the claim file, and the three sanctioned exits, a deletion with no naming claim passes silently; a missing claim directory passes; an unresolvable diff source exits 2 indeterminate; a git plumbing failure exits 3 tool error; every path prints the final `OUTCOME:` line per the four-outcome contract, and the module docstring's exit-code line documents this subcommand's divergence from the family convention in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: full suite OK [class: REPOSITORY_TEST]
- [x] Pin the fixtures in scripts/test_reverse_squash_guard.py, given/expects form, reusing the suite's scratch-repo and guard-run helpers: `test_claim_fence_witnessed_deletion_refuses` (given a re-derived 7b8d1bff shape, a plans-root deletion with a live execution claim, expects exit 1 naming the path, the claim file, and the three sanctioned exits); `test_claim_fence_archive_twin_same_commit_passes` (given the deletion's completed-twin added by the same commit, expects exit 0 naming the sanction); `test_claim_fence_retro_archive_in_later_commit_refuses` (given the twin landed by a later commit in the range, expects the deleting commit's scan to refuse, the witnessed recovery shape); `test_claim_fence_ack_trailer_passes` (given a commit message carrying `Plans-Deletion-Ack:` naming the path, expects exit 0); `test_claim_fence_ack_wrong_path_refuses` (given a trailer naming a different path, expects the refusal); `test_claim_fence_authoring_claim_refuses` (given a live authoring claim, expects the identical refusal); `test_claim_fence_date_prefix_stem_matches` (given a slug-keyed claim and a date-prefixed basename, expects the refusal); `test_claim_fence_strict_subsequence_does_not_match` (given a claim stem appearing only as a strict subsequence of unrelated segments, expects exit 0); `test_claim_fence_no_claim_passes_silently` (given no matching claim, expects exit 0 with zero blocks); `test_claim_fence_absent_claim_dir_passes_silently` (given no claim directories on the primary checkout, expects exit 0); `test_claim_fence_unresolvable_diff_indeterminate` (given an unresolvable base ref, expects exit 2 with OUTCOME: indeterminate); `test_claim_fence_tool_error_paths` (given a corrupted scratch repo, expects exit 3 with OUTCOME: tool_error) [class: REPOSITORY_TEST]
- [x] Commit: `feat: reverse-squash guard claim-fence check refuses plans-root deletion under a live claim` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Boundary wiring, battery amendment, guidance, and the done gate

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh` (conditional, pin re-key only)

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers the done-gate fixture and registry criteria
- `grep -c "gate_plans_root_claim_fence" scripts/done_sweep_gates_lib.py`; covers the done-gate presence (RED at authoring: zero hits)
- `grep -c "check-claim-fence" agents/skills/plans/SKILL.md`, `grep -c "check-claim-fence" agents/skills/execute-plan/SKILL.md`, `grep -c "check-claim-fence" agents/skills/maintenance/SKILL.md`, run as three separate invocations so each file's wiring gates on its own exit; covers the flow-text wiring presence (RED at authoring: zero hits in all three)
- `grep -c "gate_plans_root_claim_fence" agents/skills/done/SKILL.md`; covers the battery-enumeration amendment presence (RED at authoring: zero hits)

- [x] Add `gate_plans_root_claim_fence` to scripts/done_sweep_gates_lib.py as a thin CLI-child gate in the review-staging gate's pattern: it invokes the guard's `check-claim-fence --base <start_commit> --head HEAD` over the run manifest's range (repo-local lib resolution per the done skill's sweep-gates lib rule), routes the four-outcome child contract exactly (exit 0 passes with the sanction lines in the message; exit 1 failed bucket with the refusal blocks; exit 2 indeterminate naming the target; exit 3 or a missing final line tool error), classifies deletions inside foreign commits of the shared range as named report lines per the battery's foreign-artifact treatment (the gate classifies with the done lib's existing foreign-commit classification), warning-skips with a named reason when the range is empty or the plans home resolves to nothing; register the gate in the GATES dict and insert it into the pre-commit phase list directly after post-landing-staging, and extend `test_gate_registry_matches_absorbed_steps` for the seventeen-id registry and the shifted indices [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the done-gate fixture in scripts/test_done_sweep_gates_lib.py: `test_plans_root_claim_fence_gate_refusal_foreign_report_and_skip` (given a scratch run whose own range deletes a claimed plans-root file, expects the failed bucket naming the path and claim; given a foreign-commit deletion in the range, expects a named report line and no failure; given an empty range, expects the warning skip naming the reason) [class: REPOSITORY_TEST]
- [x] Amend the pre-commit sweep gates paragraph in `agents/skills/done/SKILL.md` (the battery enumeration of record for the pre-commit phase, where post-landing-staging is enumerated; the pre-docs paragraph enumerates the pre-docs gates only and has no insertion point for this pre-commit gate) to insert the plans-root claim fence gate id beside post-landing-staging, sentence-scoped to that single insertion point [class: IMPLEMENTATION_REQUIRED]
- [x] Wire the landing closeout in `agents/skills/plans/SKILL.md`: the landing closeout's pre-rider sentence span (the sentence carrying the rider-commit flip ordering literal) gains the check-claim-fence invocation over the landing range before the rider commit, with the closeout's real routing (exit 1 refuses the landing; exits 2 and 3 stop the landing for re-derivation, never read as a pass), amending only that sentence's span and keeping the pinned literal intact (pin 2203) or re-keying it in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Wire the execution landing in `agents/skills/execute-plan/SKILL.md`: the landing paragraph's rider parenthetical (the inline enumeration inside the numbered closeout step) gains the same scan as one enumeration member, amending only that parenthetical span [class: IMPLEMENTATION_REQUIRED]
- [x] Scope the queue-prune guidance in `agents/skills/maintenance/SKILL.md`: the log duties' prune clause gains the symmetric arm generalized to its subject (a pruning or triage edit that removes a plans-root file produces its archive-or-rejected disposition in the same commit and is scanned by the claim-fence check at the boundary), amending only that clause [class: IMPLEMENTATION_REQUIRED]
- [x] GREEN: both suites OK, the pins suite exits 0 with OUTCOME: pass, the em-dash added-lines scan exits 0, the public hygiene scan exits 0, and `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-live-claim-plan-deletion-fence.md` exits 0 on the final bytes [class: REPOSITORY_TEST]
- [x] Commit: `feat: claim-fence boundary scans wired into done and landing closeouts` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

The origin row `docs/history/backlog/2026-10-05-live-claim-plan-deletion-fence.md` (Filed 2026-10-05, witnessed concurrency near-miss: a peer commit deleted a certified in-execution plan outright while its claim was live) was covered in full by this plan and is deleted in the same completion pass; its Expected arm (the fence ships rather than parks) is delivered by the landed `check-claim-fence` subcommand, the done-battery gate `plans-root-claim-fence`, and the four boundary-flow wirings.
