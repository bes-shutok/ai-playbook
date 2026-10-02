# Script outcome contract

Decision-making scripts (scripts that classify or gate agent work: staging,
commits, restoration, cleanup, archival, review closure, landing, or other
workflow transitions) report exactly one of four outcomes:

- **pass** (exit 0): evidence satisfies the script's stated condition.
- **fail** (exit 1): evidence establishes a modeled violation; the offending
  evidence is identified in the script's output.
- **indeterminate** (exit 2): available evidence is insufficient,
  contradictory, partially parsed, or outside the modeled cases; the script
  reports what it observed and what it could not determine and leaves the
  decision to the agent.
- **tool error** (exit 3): the script could not perform its check reliably
  (missing inputs, unsupported data, internal failure, or an unheld
  operating-context assumption). A tool error is never represented as a pass
  or as a domain finding.

## The convention

The exit code and a final stdout line `OUTCOME: <pass|fail|indeterminate|tool_error>`
carry the outcome together; human-readable evidence lines precede the final
line. Callers parse the final `OUTCOME:` line and the exit code together, and
must not infer an outcome from anything else. For a migrated script, a run
that emits no final `OUTCOME:` line (a crash, an interruption, a truncated
capture) is not a pass: treat it as tool error, stop the dependent action,
and re-derive the state from disk. Help and version metadata exits (`--help`, `--version`) emit
no `OUTCOME:` line and sit outside the contract; callers must not invoke
scripts in metadata mode inside gated flows. When a single run classifies
multiple inputs and both regressed and indeterminate paths are observed, the
run reports `indeterminate` (exit 2) and still names every regressed path in
its evidence lines: uncertainty dominates, and the caller stops and
re-derives rather than acting on the definitive subset.

## Caller obligation

An agent must not treat `indeterminate` or `tool error` as pass or fail, and
must not continue a dependent destructive or landing action on such a result:
report the script's observed/could-not-determine or error lines and re-derive
the state from disk before proceeding. Known cases keep deterministic
behavior; escalation is for uncertainty, never a substitute for implementing
expected cases.

## Operating-context assumptions (per script)

An unheld assumption classifies as tool error (environment or invocation
unheld) or indeterminate (input outside the modeled cases), never as a domain
pass or fail.

| Script | Assumptions declared | Status |
| --- | --- | --- |
| `dirt_regression_gate.py` | invocation inside the repository; `--base` resolves to a commit and HEAD exists; listed paths exist in the worktree, are HEAD-tracked, or are staged deletions (an existing worktree path HEAD never tracked classifies clean by design: the gate models reversions of lines HEAD gained since the base, and a path HEAD does not track has no gained lines, so its classification is clean regardless of restored content, including base-era content of a file HEAD deleted; resurrection of such a path is the callers' enumeration and review discipline's responsibility); `git diff` output well-formed; blob content decodable as UTF-8 text (the decode codec is pinned utf-8 strict; non-decodable output is tool error) | migrated (this plan) |
| `landing_parentage_gate.py` | invocation inside a git repository with resolvable revs (the landing commit, the pre-landing tip, the default ref); a non-resolving origin ref is a modeled skip, not an assumption violation; pre-swap's optional `--source-branch` and `--expected-base` (the swap-time containment and base-pin legs) assume the provided refs resolve (an unresolvable source branch or expected base is tool error naming the ref) and that `--expected-base` arrives with its companion `--source-branch` (its absence is a usage tool error) | migrated (batch 1, 2026-10-03; the two optional pre-swap legs added by the squash-landing failure-path guard plan, 2026-10-03) |
| `land_squash.sh` | invocation inside a git repository whose primary checkout (the resolved git common dir minus `.git`, the same root done-lock keys the merge lock by) has a checked-out base branch (a detached primary HEAD is tool error naming the checked-out HEAD and the expected tip) and whose merge-lock environment is authentic: both `MERGE_LOCK_DIR` and `MERGE_LOCK_TOKEN` set and non-empty, the lock directory live, `meta.env` readable with a non-empty `lock_token` equal to `MERGE_LOCK_TOKEN`, and the record's `repo_root` equal to the helper's resolved primary checkout root (every deviation classifies tool error, so the lock is non-bypassable by a fabricated, stale-generation, meta-less, or foreign-repo environment); provided refs resolve (`--branch`, `--expected-tip`, `--expected-base`: an unresolvable ref is tool error naming it); the primary index is clean enough for the landing, modeled by the staged-state and dirty-intersection pre-refusals (a violating index is the modeled fail class, refused before the merge); git >= 2.38 for the probe's `git merge-tree --write-tree` conflict trial; the three test-only fault-seam values (`dirty-writer` with the test-only `LAND_SQUASH_TEST_FAULT_PATH` target variable, `backward-peer`, `diverge-origin`) are declared for fixtures and never set in production, and every honored seam prints a loud evidence line naming the value and its env; the full outcome mapping: a land-time merge failure and the interleaved-tip refusal classify indeterminate; the tree-equality assertion, the CAS refusal (the tip-moved fail class), and the probe-detected conflicts and the prechecks are the modeled fail classes; a mid-restore pipeline failure classifies indeterminate (partial mutations naming the unrestored paths, the agent re-derives), not tool error; the changed-since-snapshot writer block is a fixture-covered arm; the CAS-refusal and mid-restore arms are recorded as declared classes without dedicated fixtures at birth (the restore discipline is exercised by the merge-failure and gate-refusal fixtures; the CAS refusal reuses the tip-moved fail class) | born-conformant (the squash-landing failure-path guard plan, 2026-10-03) |
| `base_reflog_audit.py` | invoked inside the landing repository; the base branch resolves and carries at least one reflog entry; the walked reflog window is contiguous, since a gc or expiry gap inside the window can fabricate or mask a row and the script cannot detect the gap; `--since-sha` resolves else tool error; the anchor is reached within `--max-entries` else indeterminate; no base-branch root commit within `--max-commits` else indeterminate; subjects decodable as text | conformant at birth (this plan) |
| `plan_readiness.py` | a readable repository with resolvable facts keys for plans_dir and reviews_dir; a readable plan operand; the sibling modules importable and shape-compatible (a sibling-compatibility mismatch is tool error, never a readiness fail); a readiness run over readable inputs always reaches a verdict (exit 2 is not modeled) | migrated (batch 2, 2026-10-04) |
| `validate_review_staging.py` | readable input paths (the staging operand, when supplied, must be an openable file; an unreadable or missing path is tool error naming the path); invocation validating at most one staging record per run (one positional path, or one `--newest-for-branch` branch whose newest doc is selected, the miss being a modeled pass naming its reason); the library surfaces are recorded, not rewired: the done-sweep lib's `is_staging_review_path` scope helper and scripts/summarize_review_stats.py's module import (plus the sibling imports in plan_readiness.py and review_record_selection.py) sit outside the CLI contract; no indeterminate class exists (staging markdown bytes are readable or not, and a schema-violating record is the modeled violation); `--selftest` is a metadata-mode diagnostic (no OUTCOME line); `--json` runs carry the outcome as the JSON `outcome` field (the declared placement deviation) | migrated (batch 2, 2026-10-04) |
| `done_sweep_gates_lib.py` / `done_sweep_gates.sh` | invocation inside a readable repository: the repo anchor resolves through `DONE_SWEEP_REPO_ROOT` or the git toplevel of the working directory, and repo-relative paths resolve through the repo facts document's TOML keys with the conventional defaults backing a missing key; gate and validator scripts resolvable through the documented resolution order (env override, repo-local `scripts/`, runtime-home `scripts/` copy): a script absent at every resolved path while its run-when triggers are live keeps the frozen rc-1 deployment-gap refuse (the plan-readiness validator and the origins checker arms alike; an unheld environment assumption reported loud, awaiting its own row's remap); per-gate assumptions are inherited from each child's own row once that child migrates (the promoted-origins arm inherits `check_plan_origins_closed.py`'s readable backlog and plans directories; the review-staging child arm is a CLI-contract caller rewired in batch 2, Task 1, and the skills-repo hygiene child arm likewise in batch 2, Task 5); the plan-readiness child validator answers in the migrated four-outcome vocabulary (rewired in batch 2, Task 2): child exit 0 passes, exit 1 lands in the failed bucket with the child's first-failure line, exit 2 (a legacy or crash shape the migrated child never models) keeps an indeterminate bucket naming the child, exit 3 lands in a tool-error bucket carrying the child's error evidence, and a child run with no final OUTCOME line classifies tool error per the no-line rule winning over the exit code; phase runs emit the final `OUTCOME:` line on stdout (`--help` and `list-gates` are metadata exits; a usage error or a lib missing next to the runner is tool error with the line on stdout); the manifest subcommands (`write-manifest`, `finalize-manifest`, `disposition-manifest`, `list-interrupted-manifests`) are record flows outside the OUTCOME coverage: they emit no final `OUTCOME:` line and keep their legacy exits, so the contract's no-line rule must not be applied to them (a successful `write-manifest` is not a tool error); the post-landing-staging gate assumes the primary checkout is resolvable as the first `git worktree list --porcelain` worktree entry (an unresolvable worktree list or an unreadable primary checkout is tool error), inspects that checkout read-only (`git -C <primary>`), keeps the strict staged-empty check when the current-session run manifest does not resolve (the ownership narrowing is skipped, never the check, with an unresolvable-manifest warning line), and re-consults `done-lock.sh merge-status` before any refusal (residue observed while the lock is held reports indeterminate, never a residue refusal; an unrunnable merge-status consult with residue observed is likewise indeterminate; the record-only allowlist constant `projects/.ai-playbook/development_lessons.md` is owned by the gate) | migrated (batch 1, 2026-10-03) |
| `done-lock.sh` | invocation inside a git repository (the merge family keys on a resolvable git common dir); lock metadata readable and in the supported record shape (unsupported lock data is tool error); the holder's state classifiable from live evidence (a verified-live holder or a dead holder inside the grace window fails with holder evidence; a meta-less lock past the incomplete age or an unverifiable holder identity is indeterminate); the acquire subcommands' stdout stays eval-consumed exports only, so their final `OUTCOME:` line is on stderr (the declared placement deviation) | migrated (batch 1, 2026-10-03) |
| `check_plan_origins_closed.py` | a readable backlog directory (and completed/rejected archives), a readable plan file in plan and coverage modes, and a readable archived-plans directory for the corpus scan; the facts file resolving with conventional defaults is part of the operating context | migrated (batch 1, 2026-10-03) |
| `check_maintenance_pins.sh` | invocation inside the target git repository (a non-repo invocation is tool error); the suite reads the repository's own tracked files; no suite-wide fixture harness: the per-section fixture seam carries the outcome coverage (the in-repo run is the pass arm, the live-vs-archive built-in selftest is the witnessed fail arm, the non-repo probe is the tool-error arm) | migrated (batch 2, 2026-10-04) |
| `prestage_freshness_gate.py` | an existing repository; a resolvable head ref; readable candidate paths and a readable fresh-write list when provided | migrated (batch 1, 2026-10-03) |
| `review_thread_gate.py` | a readable, shape-conforming marker when present; a gh installation authenticated for `--live`; an unreadable or shape-violating marker or inventory is tool error | migrated (batch 2, 2026-10-04) |
| `revert_set_classifier.py` | invocation inside a git repository with a resolvable `--repo` and resolvable revs; git answering outside its 0/1 vocabulary is indeterminate | migrated (batch 2, 2026-10-04) |
| `check_cleanup_scope_baseline.py` | invocation inside a git repository (a non-repo root is tool error); a `--base` operand resolving to a commit (an unresolvable base ref is tool error); invocation with a `--base` operand (its absence is a usage tool error through the argparse override); git plumbing over the resolved inputs answering outside its vocabulary is indeterminate; `--selftest` is a metadata-mode diagnostic (no OUTCOME line) | migrated (batch 2, 2026-10-04) |
| `rearm_on_touch.py` | a readable scheduler state file at the resolved path; an unparseable state file is tool error; the verdict JSON is the decision payload and every classified verdict passes on the exit channel | migrated (batch 2, 2026-10-04) |
| public-hygiene scan (`scan-public-hygiene.sh`) | invocation from a readable repository root (`PUBLIC_HYGIENE_REPO_ROOT` or the working directory); a readable shared deny-patterns file (a missing file is tool error); readable named inputs in `--files` mode (an unreadable or invalid path argument is tool error); no indeterminate class exists (the scan's inputs are readable bytes or the run is a tool error); the runtime-home twin is a verified symlink into the canonical scripts directory, so it tracks the canonical bytes and inherits the migration at landing; `--selftest` is a metadata-mode diagnostic (no OUTCOME line) | migrated (batch 2, 2026-10-04) |

The ranking orders the table by the consequence of a wrong classification
(landing and closeout gates above advisory checks) and by assumption
volatility. The table is the migration register, not a claim of complete
coverage: a decision script absent from it is still outside the contract
until its own row lands. Assumptions are declared at each migration's
authoring, never pre-registered here. Scripts still on legacy semantics keep
their documented exit meanings (several use exit 2 as tool failure) until
their own migration lands; the contract's readings (exit-2-means-
indeterminate and the no-final-OUTCOME-line rule) apply only to migrated and
born-conformant scripts. A born-conformant script is held to the migrated
script's readings: the final `OUTCOME:` line, the four exit codes, and the
declared assumptions.

## Compatibility note

`dirt_regression_gate.py` migrated 2026-10-02: its former exit 2 (usage and
git-environment errors) became exit 3 (tool error) and exit 2 now means
indeterminate. No caller branched on the old exit 2 (both callers key on the
named `dirt REGRESSION` lines); the gate's output gained the final `OUTCOME:`
line additively.

Batch 1 (2026-10-03, the landing and closeout gates) migrated
`landing_parentage_gate.py`, `prestage_freshness_gate.py`,
`check_plan_origins_closed.py`, `done-lock.sh`, and the
`done_sweep_gates_lib.py` / `done_sweep_gates.sh` pair. The guard-family
contract (0 pass, 1 refuse, 2 tool failure) is retired on the three python
gates and their former exit-2 readings are gone: plumbing failures over
resolved revs are indeterminate (exit 2), while usage, argparse (overridden),
unresolvable-input, and unreadable-input failures are tool error (exit 3);
modeled refusals stay exit 1. done-lock remapped its held and max-wait
exhaustion arms from exit 2 to exit 1 (fail with holder evidence), classifies
ambiguous-holder and incomplete-too-new stale-clean shapes as indeterminate
(they already exited 2 and keep the code), and moved usage, not-a-git-repo,
and release-refusal arms to exit 3; its acquire subcommands emit the final
`OUTCOME:` line on stderr because their stdout is eval-consumed exports (the
declared placement deviation). The done-sweep pair moved its usage-error and
missing-lib arms from exit 2 to exit 3 (tool error on stdout), captures a
raising gate helper as an indeterminate run, and branches its origins
consumer on all four outcomes instead of collapsing any non-zero origins
result into a refuse. Two declared preservation exceptions introduce new
modeled arms: the prestage type-change case (previously a stale refuse or a
bogus byte-equality pass) and the origins unreadable-origin case (previously
a straggler refuse) both classify indeterminate, with indeterminate
dominating refuse in a multi-path run while every regressed path stays
named. Two scoping notes bound the batch: the sweep pair's manifest
subcommands (`write-manifest`, `finalize-manifest`, `disposition-manifest`,
`list-interrupted-manifests`) stay record flows outside the OUTCOME
coverage - they emit no final `OUTCOME:` line and keep their legacy exits,
so the no-line rule must not classify a successful `write-manifest` as a
tool error - and the sweep runner's deployment-gap arms (a plan-readiness
validator or an origins checker absent at every resolved path while its
run-when triggers are live) keep their frozen rc-1 refuses pending their own
rows' migrations.

Batch 2 (2026-10-04, the review and maintenance advisory tier) migrated
`validate_review_staging.py`, `plan_readiness.py`, `review_thread_gate.py`,
`revert_set_classifier.py`, `check_maintenance_pins.sh`,
`rearm_on_touch.py`, `check_cleanup_scope_baseline.py`, and the
public-hygiene scan (`scan-public-hygiene.sh`), completing the register at
fourteen migrated rows plus the born-conformant `base_reflog_audit.py`. The
guard-family "tool failure" stderr prefix retires on the revert-set
classifier. The former exit-2 readings are gone on the five python CLIs
whose usage errors were argparse exits (validate_review_staging,
plan_readiness, review_thread_gate, revert_set_classifier, rearm_on_touch):
argparse is overridden so a usage violation is a tool error (exit 3) with
the final `OUTCOME: tool_error` row on stderr, and `--help` stays a
metadata exit. The named remapped arms are tool error now: the
plan-readiness sibling-compatibility mismatch (formerly a `return 1`
misfiled as a readiness fail), the pins suite's not-inside-a-git-repo arm
(formerly exit 1 masquerading as a findings-class failure; the 38 mid-suite
checkpoints keep exit 1, funneled through one emit helper so every run still
ends with exactly one final OUTCOME line), the review-thread gate's six read
and fetch arms (formerly exit 1 beside the unclosed-threads verdict; the
missing-marker skip stays a modeled pass at exit 0, and a malformed
inventory JSON joins the tool-error class), the rearm-on-touch
malformed-state and unexpected-exception arms (formerly exit 2; every
classified verdict keeps exit 0 with the verdict JSON still the parseable
payload and the OUTCOME line following it), the hygiene scan's own-error
class (formerly exit 2; clean 0 and findings 1 are unchanged), and the
release-rewrite privacy gate's `invoke_scanner` branch, re-keyed from the
scanner's old exit 2 to its new exit 3 with the findings fall-through kept
and scanner stdout still discarded, so the OUTCOME-line check is
inapplicable there. The witnessed indeterminate classes are the classifier
pair's plumbing-failure arms: a git plumbing failure over already-resolved
inputs is indeterminate (exit 2) on `revert_set_classifier.py` and on the
cleanup-scope checker, whose legacy internal-error class split accordingly
(the `cleanup-scope: internal error` prefix retires into the split arms).
The declared deviations: `validate_review_staging.py`'s `--json` runs carry
the outcome as the JSON `outcome` field and emit no stdout OUTCOME line, and
the three embedded selftest harnesses (`validate_review_staging.py
--selftest`, `check_cleanup_scope_baseline.py --selftest`, and the hygiene
scan's `--selftest`) are metadata-mode diagnostics emitting no OUTCOME line
(their verdicts ride their own assertions and exit codes). The done-sweep
pair's three CLI-child arms are rewired onto the migrated children's four
outcomes (review-staging in batch 2 Task 1, plan-readiness in Task 2,
skills-repo hygiene in Task 5), the no-line rule winning over the child exit
code in all three. No modeled pass, refusal, or findings class changed its
code on any of the eight; the caller recipes gate on every outcome plus the
missing-OUTCOME-line rule where they invoke these scripts.
