Ready ad-hoc entries, most urgent first, consumed by exec-mode sessions. Prompt-emission owner: `agents/skills/investigate/SKILL.md`, Stage 4.

## closeout-migrate-baseline-tracked-clobber

Added: 2026-11-01, learn Step 1.9 investigate over the 10:00 exec carrier session's closeout phase (landing `d61d76504`; corpus witness lesson 354)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): one bounded change to `scripts/worktree_closeout_migrate.py` (a pre-flight guard plus a post-run staged-set check) plus test pins - no open design choice, no dependency, no plan-scale surface; the repair-shaped arms follow the machinery admission protocol below for the one refusal gate they add.

Origins:
- docs/history/backlog/2026-11-01-closeout-migrate-baseline-tracked-clobber.md

Urgency: high - the witnessed clobber silently rewound two shared tracked corpus surfaces (the project lessons corpus and the document registry) and staged them in the primary checkout mid-run; undetected, a closeout of that shape lands peer-content reverts, and the only current protection is the operator noticing.

Scope arms: (1) pre-flight: when a baseline checkout is given, diff the baseline's versions of the destination's shared tracked surfaces against destination HEAD and refuse with a named remediation (re-capture the baseline at current HEAD) when any file would move backward; (2) post-run: after the carry, list staged entries and revert every tracked-path hunk the migration manifest's outputs do not own, reporting each as a prevented clobber. Machinery admission for arm (1)'s refusal gate: incident - the 2026-11-01 witnessed clobber (origin row + lesson 354, docs/maintenance/development_lessons.md); catch frequency - every baseline migrate whose baseline checkout predates a mid-run primary landing on a shared tracked file (witnessed once); false-positive cost - refuses an intentionally older baseline, bounded by the named re-capture retry; review - revisit alongside the zero-delta report arm's promotion criteria (`docs/history/backlog/2026-10-31-closeout-zero-delta-report-arm-coverage.md`).

Orientation: `scripts/worktree_closeout_migrate.py` (baseline mode introduced in commit `3b05b66a6`), `scripts/test_worktree_closeout_migrate.py`, lesson 354, and the origin row.

Rejected alternatives:
- Documentation-only remedy (skill-text warning in the closeout recipe): rejected - a prose warning cannot detect a stale baseline at run time, and the witnessed failure shipped rewound bytes into the staged index before any human read (origin row reproduction evidence; lesson 354)
- Remove the baseline mode entirely: rejected - the baseline-relative carry is the documented remedy for runs whose Phase 0 baseline is missing or stale (lesson 288's family and the covered missing-baseline plan), and the zero-delta report arm already depends on its captured baseline contract (`scripts/worktree_closeout_migrate.py` `_print_zero_delta_report`)
- Post-run ownership check alone, no pre-flight: rejected - reverting after the carry still routes rewound bytes through the index and risks a partial recovery when a peer commit lands between migrate and revert; the pre-flight refusal keeps the stale bytes out of the destination entirely (witnessed repair needed both restore --staged and restore from HEAD, origin row)
- Widen baseline mode to delta-carry tracked files instead of whole-file copies: rejected - a delta carrier is a new merge engine on the run's most dangerous path; the refusal-plus-recapture shape prices far less (machinery admission's smallest-arm rule, repository guidelines' Machinery admission protocol section; the whole-file copy is the current mechanism, scripts/worktree_closeout_migrate.py baseline mode, introduced in commit 3b05b66a6)


EXEC-PROMPTS-PRUNE: closeout-baseline-capture-placement-remedy -> landing in this commit (ad-hoc landing: scripts/worktree_closeout_migrate.py's migrate baseline-missing refusal gained the primary-checkout remedy clause - check the primary checkout's same-slug session dir for closeout-baseline.json and copy it in before recapturing, a recapture recorded as a late-baseline capture-failure deviation - and the capture success output now names the checkout it captured in so a wrong-checkout Phase 0 capture is visible; both message shapes pinned (focused migrate suite 288 passed + 17 subtests, wrapper suite 178 passed + 2 subtests), em-dash added-lines gate and public hygiene scan pass; origin row deleted per the covered-row rule with both Cluster pointers tidied and this entry section removed in the same change)

EXEC-PROMPTS-PRUNE: done-closeout-gates-trio -> landed ad-hoc (gate-removal's missing-destination guard no longer holds a branch on an expired done-session gate-report destination - the owning run's disposition, report-only - while every other missing destination keeps its fail-closed hold; done_run.sh declares FM_OUT local, routes an unreadable-manifest identity refusal to the refusal-specific held-lock disposition via --run-id, and scopes the env-lost advice to release-only re-runs; the parked branch 2026-10-31-done-finalize-manifest was disposed at its verified tip fae94c63a with its worktree removed; focused migrate suite 337 passed + 25 subtests, wrapper suite 193 passed + 2 subtests, em-dash gate and public hygiene scan pass; the three origin rows are deleted per the covered-row rule and this entry section is removed in the same change)

EXEC-PROMPTS-PRUNE: untrack-operand-residual-trio -> landed ad-hoc (both untrack ignore rescans in scripts/done_run.sh are fail-closed: `--` separator and rc>1 refusal on every check-ignore probe, `-z` NUL-delimited diff listings so C-quoted names resolve, a `[ -f ]` regular-file preflight arm, and the 1c captured-tree scan reads the head identity captured once at the untrack preflight; three new wrapper tests pin repeatable distinct operands, the parser usage guards (missing value, `--`-prefixed value, duplicate; exit 3), and the --untrack + --guard-firing preflight-before-ledger-append ordering; the race-injection docstrings now say during stage-operand processing; the usage print window extends one line to 2,196p; and --expected-ref beside --untrack refuses early with its own named message instead of the foreign guard's mislabel; focused untrack class 13 passed; origin rows deleted per the covered-row rule with this entry section removed in the same change)

EXEC-PROMPTS-PRUNE: plan-prompts-stub-rewrite-origin -> landed 5fd2cd482 (execute-plan: land plan-prompts-stub-writer-forensics; stub write attributed to a session tool write via direct-execution + hash-identity evidence; plan archived with backlog disposition fold, origin row deleted, registry row; Phase 3 r1 focused 0 blocking; monitor completion prune removed this served entry section after the landing)

EXEC-PROMPTS-PRUNE: plans-authoring-pre-review-text-gate-sweep -> landing in this commit (ad-hoc landing: the plans skill's authoring Plan Quality Gate gained the pre-review text-policy sweep - em-dash added-lines gate with an explicit base (bare added-lines scans nothing once the plan file is checkpoint-committed), the public hygiene scan, and the pins suite when pinned files are touched - gating the first review-plan round's launch, with the mirrored one-line duty in the maintenance authoring payload; focused docs panel r1 two workers one blocking Medium (vacuous bare added-lines) + one non-blocking Medium and three Lows folded in-change (explicit --base, hygiene script named, admission rationale as one-line citation), r2 confirm; em-dash gate, public hygiene scan, and pins suite pass; origin row deleted per the covered-row rule and this entry section removed in the same change)

## exec-review-producer-egress-digest-mint-gap

Added: 2026-11-01, learn Step 1.9 investigate over the plan-prompts-stub-writer-forensics landing (automation-7974d70c resume carrier session)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): one bounded change to `scripts/produce_exec_review_record.py` (or the guard's refusal text) plus one fixture pin - no open design choice, no dependency, no plan-scale surface; the fix removes a hand-edit family that has now cost landing refusals in three consecutive archive landings (lesson 287's witness series).

Origins:
- docs/history/backlog/2026-11-01-producer-egress-digest-mint-gap.md

Urgency: medium - every plans-root archive landing without a pre-minted egress digest requires a hand `cat >>` backfill into both reviews homes, the append has already been silently skipped once (an `&&`-chained failing probe), and the guard's own sanction list prices the failure at repeated landing refusals.

Scope arms: add a producer option (`--egress-digest <sha256>` or `--egress-path <path>` digested at mint time) that places the archive-egress digest into the minted record pair, with one fixture pin proving the minted pair satisfies `find_evidence_record` unchanged; the smaller alternative is a guard refusal-text remedy naming `grep -c <digest> <record>` in both homes as the retry pre-check.

Orientation: `scripts/produce_exec_review_record.py` (creation-only contract), `scripts/reverse_squash_guard.py` (`find_evidence_record`, the ack-is-alternative semantics), lesson 287 (third witness, docs/maintenance/development_lessons.md), and the origin row.

Rejected alternatives:
- Keep the hand-backfill route and only document it in lesson 287: rejected - the lesson documents the mechanics but no mechanical check verifies the digest landed, and the witnessed skip shipped stale bytes through a mirror into two homes (lesson 287 third witness, docs/maintenance/development_lessons.md)
- Pass `--ack-egress` alongside the backfilled evidence leg: rejected - the ack is an alternative exit, not an additive leg; once the evidence leg is satisfied the ack refuses as unused (the guard's unused-ack refusal, witnessed 2026-11-01 in the same landing; `scripts/reverse_squash_guard.py` check-archive)
- Move the record mint after the completion pass so the digest exists naturally: rejected - the mint input is the reviewed plan's live path and the record feeds the Phase 3 exit before the completion pass runs; reordering the run's phases to serve one digest is a larger change than the option arm (the execute-plan skill's Phase 3/4 ordering, agents/skills/execute-plan/SKILL.md)

## runtime-scripts-home-reconcile-follow-up

Added: 2026-11-01, investigate over the interactive exec max-2 run 2026-11-01 (pick 2 landing `f9533d93d`, runtime-scripts-home-reconcile-and-retire, whose Ship-when is OPERATIONS_FOLLOW_UP by design)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): one bounded deployment-home operation driven by an existing sync script and the manifest the landed plan registered (`scripts/runtime-scripts.list`) - no open design choice, no new surface, no dependency, no plan-scale scope; the removal-shaped cleanup needs no new machinery, so no admission wording applies.

Origins:
- docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md

Urgency: medium - the landed plan registered the manifest but deliberately left the physical deployed home divergent (real backup files, diverged home-only script copies, dangling symlinks recorded in the origin row's 2026-10-18 inventory), so a stale shadow copy can still execute at the facts-resolved home until the reconcile runs.

Scope arms: run the deployed-home reconcile through the sync script's rsync semantics over the manifest-admitted set (removing home-side real files and dangling links that shadow repository twins, redeploying the registered scripts), then re-derive the origin row's inventory classes on the reconciled home and require zero real files beside the symlinked majority and zero dangling links, recording the before/after inventory delta in the run report; the origin row is deleted in the same change per the covered-row rule once the expected state holds.

Orientation: docs/history/plans/completed/2026-10-28-runtime-scripts-home-reconcile-and-retire.md (the manifest registration, landed `f9533d93d`), `scripts/sync_runtime_scripts.sh` (the deployment roster), `scripts/runtime-scripts.list`, and the origin row (the 2026-10-18 inventory baseline and its 2026-10-25 contract-visible drift witness).

Rejected alternatives:
- Author a fresh plan for the physical-home cleanup: rejected - the operation has no design choices left once the manifest is registered; a plan would re-state the sync script's existing contract (the eligibility test's no-open-design-choice clause, `agents/skills/maintenance/decisions.md`)
- Widen the landed plan retroactively to include the cleanup: rejected - landed base-branch history is immutable; the follow-up rides additively as its own operation (the plan's Ship-when OPERATIONS_FOLLOW_UP sentence, docs/history/plans/completed/2026-10-28-runtime-scripts-home-reconcile-and-retire.md)
- Keep the home as-is with only the manifest registration: rejected - the origin row's driving force (no stale shadow copy can execute and no divergence hunt is needed) stays unsatisfied while the diverged home-only copies recorded in its inventory remain load-bearing paths (docs/history/backlog/2026-10-18-runtime-scripts-home-residue.md)

## project-corpus-lesson-number-derive-race

Added: 2026-11-01, learn Step 1.9 investigate over the same day's interactive authoring session (the collision surfaced during the run's Step 6.6 project-tier duplicate check)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the "body-named single-surface fix with no open design choice" clause admits it - a two-arm bounded change-set over tracked docs and skill text (corpus renumber repair plus one probe sentence in the learn derivation rule), with no dependency, no state-schema or guard change, no machinery, and no quarantine or profile-deferral record.

Origins:
- docs/history/backlog/2026-11-01-project-corpus-lesson-number-derive-race.md

Urgency: medium - the corpus carries two distinct lessons numbered 337 right now, so cross-reference resolution for either lesson's number is broken until the repair, while nothing blocks on it (the collision is detected post-hoc by a warn-only check and neither lesson's content is lost).

Scope arms: (1) repair - renumber the second `## 337.` heading in `docs/maintenance/development_lessons.md` to the next free number after a fresh max-heading read, re-grep same-corpus numeric citations of either lesson first and update any hits by hand (the 2026-11-01 sweep found no same-corpus citation of project 337; re-verify at execution), and re-run the Step 6.6 project-tier duplicate grep to zero; (2) skill text - the learn SKILL.md number-derivation rule gains one pre-write collision probe: immediately before the corpus write, re-grep the derived number; on a hit, re-derive from a fresh read and retry once, then report the drift as a manual follow-up. No validator, hook, or lock; the corpus file is skill-gate gated at edit time already.

Orientation: `agents/skills/learn/SKILL.md` (the number-derivation sentence in the opening block and its retry-once rule), `scripts/check_investigate_entries.py` (the marker-semantics pattern the probe's re-grep mirrors), the origin row (evidence and commit citations), and lesson 134's own-edit check class in `docs/maintenance/development_lessons.md` (the same parallel-session family on the staging side).

Rejected alternatives:
- Promote the Step 6.6 project-tier duplicate check to a blocking learn-finish validator: rejected - it runs after both writes have already landed, so it detects the collision without preventing it, and the sibling landed plan's machinery admission rejected runtime machinery for the adjacent commit-span arm on the same shared-checkout economics (docs/history/backlog/2026-11-01-learn-corpus-commit-sweep-concurrent-session.md)
- Serialize corpus writes with a lock keyed on the lessons file: rejected - one witnessed collision in a ~350-lesson corpus prices far below a lock's false-positive cost of serializing every learn run, and the pre-write probe with retry-once removes the same race window for the cost of one grep (the origin row's Fix shape; the repository guidelines' Machinery admission protocol smallest-arm rule)
- Per-session suffixed numbering (for example a session-keyed heading suffix): rejected - suffixes break the numeric recall chain the numbering exists for, since the recall tooling and cross-references anchor on the corpus's `## N.` heading convention (the skill-gate README's `PROJECT_CORPUS_REL` constant, agents/hooks/skill-gate/README.md)
- Leave the live collision unrepaired under the warn-only check: rejected - the duplicate number silently corrupts cross-reference resolution for both lessons' citations (the broken-anchor class the learn skill's verify-numbered-lesson-anchors rule exists for), witnessed by the two live headings and their landing commits (docs/history/backlog/2026-11-01-project-corpus-lesson-number-derive-race.md)

## stop-boundary-skill-text-growth-trim-deferral

Added: 2026-10-31, learn Step 1.9 investigate over the maintenance-stop-boundary-continuation execution run's backlogged r6 finding

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a single deferred trim pass over four named skill files with a stated trigger condition - no code surface, no open design choice, no dependency; the entry's scope is the trigger's bookkeeping, not an immediate edit.

Origins:
- docs/history/backlog/2026-10-31-stop-boundary-skill-text-growth-residual.md

Urgency: low - the ~1.3 KB net growth is review-time discipline today, the old unconditional-stop text was deleted in the same change, and the row names no harm beyond byte count until the byte-budget gate lands.

Scope arms: a trim pass over the four named maintenance skill files (`agents/skills/maintenance/template-authoring.md`, `template-execution.md`, `template-unblock.md`, `zcode.md`) that removes equivalent operative bytes while preserving the D-6 semantics landed 7bae9745a, executed when the repo-wide byte-budget gate lands and priced by that gate's own breach report - not before; until then the row stays open as the review-time finding-class record.

Orientation: docs/history/plans/completed/2026-10-27-maintenance-stop-boundary-continuation.md (landed 7bae9745a, the growth's introduction), the repository guidelines' Skill text anti-growth rules section (the pricing discipline the trim obeys), and the origin row.

Rejected alternatives:
- Trim the four files now by hand: rejected - without the gate's breach report there is no equivalence measure, and the trim would risk cutting the just-landed D-6 operative semantics (directive D-6, docs/maintenance/operator-directives.md) to hit a byte count; the growth rule requires equivalent operative bytes, not semantic loss (repository guidelines, Skill text anti-growth rules)
- Land the repo-wide byte-budget gate immediately to unblock the trim: rejected, machinery arm - the anti-growth rules stage the gate's landing as its own change and price growth at review time until then; this 1.3 KB finding is the first data point, not the true catch the admission protocol wants (repository guidelines, Skill text anti-growth rules; Machinery admission protocol; docs/history/backlog/2026-10-31-stop-boundary-skill-text-growth-residual.md)
- Accept the growth as final: rejected - the row records a live review-time finding class; closing it without the trim or the gate leaves the growth unpaid (docs/history/backlog/2026-10-31-stop-boundary-skill-text-growth-residual.md)

EXEC-PROMPTS-PRUNE: done-interrupted-run-remedy-names-script -> landing in this commit (ad-hoc landing: scripts/done_sweep_gates_lib.py's dead-root interrupted-run remedy line now names the owning invocation verbatim (python3 scripts/done_sweep_gates_lib.py disposition-manifest --run-id <id>), matching the scripts/done_run.sh remedy-line convention; focused panel r1 one worker 0 code-blocking with the row-disposition rider folded in-change; sweep-gates lib suite 425 passed + 3 subtests, wrapper suite 9 passed at the branch tip; em-dash and hygiene pass; origin row deleted per the covered-row rule with the sibling Cluster pointer retargeted to this receipt and this entry section removed in the same change)

## adhoc-planless-worktree-closeout-arm

Added: 2026-11-01, learn Step 1.8 over the 11:00 WET exec run (automation-745a0751 session)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named documentation arm over tracked skill text - one plan-less closeout paragraph in the execute-plan canonical section pinning the exact-tree removal recipe ad-hoc sessions already apply - no code surface, no open design choice, no new gate, no guard-bearing path; the documented arm prefers the documentation shape over the script-input shape, so the script surface is untouched.

Origins:
- docs/history/backlog/2026-11-01-adhoc-planless-worktree-closeout-arm.md

Urgency: low - the friction is one improvised re-derivation per ad-hoc session and the improvised arms are currently consistent (two same-day sessions converged on the same recipe); the cost is precedent-dependence, not error.

Cluster: docs/history/backlog/2026-10-29-branch-only-closeout-terminal-state.md and docs/history/backlog/2026-10-31-plan-empty-diff-closeout-route.md share the gate-removal closeout surface; this entry owns only the plan-less invocation gap (`gate-removal --plan` is mandatory and plan-less ad-hoc runs have none).

Scope arms: one paragraph in the execute-plan worktree-first canonical closeout text (the Ad-hoc-worktree closeout section) naming the plan-less ad-hoc arm: branch tip tree equality against the landing squash commit, then worktree removal and branch deletion, with the evidence recorded in the run report - no `gate-removal` invocation (its `--plan` operand stays mandatory for plan-bearing runs).

Orientation: scripts/worktree_closeout_migrate.py (gate-removal usage, `--plan PLAN` required); agents/skills/execute-plan/SKILL.md Ad-hoc-worktree closeout paragraph; the witnessed improvisation in the 2026-11-01 exec run (both picks removed via exact-tree accounting after a synthesized-slug gate-removal invocation refused).

Rejected alternatives:
- Add a `--no-plan` input arm to gate-removal: rejected on the remove-or-keep axis - a new script surface to formalize a practice the sessions already perform correctly, and the machinery admission protocol prices a gate per witnessed incident; the witnessed cost is undocumented text, not a missing check (scripts/worktree_closeout_migrate.py usage; Machinery admission protocol, repository guidelines)
- Leave it to precedent: rejected - undocumented recipe dependence re-derives per session and drifts silently; the closeout paragraph is the single home the plan-centric arm already uses (agents/skills/execute-plan/SKILL.md)
- Route ad-hoc runs through a synthesized stub plan to satisfy gate-removal: rejected - fabricates a plan artifact no run owns, inverting the plan-bearing citation contract the gate reads (scripts/worktree_closeout_migrate.py gate-removal help)

## mask-certification-seal-diagnostics-embedded-paths

Added: 2026-10-30, learn Step 1.9 investigate over the hygiene-scanner-default-scope-parity execution run's backlogged review findings

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named single-document edit - mask the absolute home paths embedded in recorded validator stdout blocks in one landed diagnostics doc per the scanner's existing masking policy - no code surface, no design choice, no machinery; the landing constraint (never touch deny patterns or exclusions) is stated on the origin row.

Origins:
- docs/history/backlog/2026-10-30-mask-certification-seal-diagnostics-embedded-paths.md

Urgency: low - the doc fails the release hygiene gate and now surfaces on every default commit scan as a report-only record; masking removes the noise and restores the gate pass without weakening anything.

Scope arms: mask the embedded absolute home paths in the diagnostics doc per the current scanner masking policy; re-run both the release hygiene gate and the default scan to verify both pass clean.

Orientation: `docs/history/certification-seal-landing-diagnostics.md` (the embedded stdout blocks), `scripts/scan-public-hygiene.sh` (the masking policy being applied), and the origin row's witness.

Rejected alternatives:
- Exclude the doc from the scan: rejected - standing constraints forbid touching exclusions or deny patterns, and an exclusion would weaken the gate for any future path leak in the same file (docs/history/backlog/2026-10-30-mask-certification-seal-diagnostics-embedded-paths.md)
- Delete the diagnostics doc: rejected - it is a landed landing-diagnostics record of a completed run; its evidentiary value survives, only the paths need masking (docs/history/certification-seal-landing-diagnostics.md)

EXEC-PROMPTS-PRUNE: receipt-runner-summary-witness-and-dispatch-failed-pin -> landing in this commit (ad-hoc landing: scripts/test_quota_wall_doctrine.py gained the dispatch_failed tracking-list reader pin mirroring the launch-wave entry's shape - a _dispatch_failed_entry RED arm reading the Phase 3 tracking list bullet, a test-local dispatch_failed_fields parser whose shape vocabulary is asserted from the entry (typed line, closed reason-code set, the pre_restart pair, the bounded-retry budget pointer, the delegation clause; plus the timestamp-form gate and the other-code quoted-error-text gate, trailing tokens outside the other shape refused), and five witness tests (entry carries the contract; a fixture line parses; out-of-set reason code and missing pre-start refused; malformed timestamp refused; the other code's quoted provider error text parsed and an empty quote refused), so deleting the pinned entry line is a suite failure; and lesson 313's receipt-runner Rule now requires the passing-summary assertion to grep the FULL captured output, never just its tail (unittest's stderr OK block can flush before buffered stdout), with a per-row summary-witness recorded beside the rc so each green row is re-derivable from the receipt alone; focused suite scripts/test_quota_wall_doctrine.py re-run green at the landed head; em-dash added-lines gate and public hygiene scan pass; origin row deleted per the covered-row rule with the completed plan's citation retargeted to this receipt and this entry section removed in the same change)

## remaining-run-era-tmp-dirs-drain

Added: 2026-10-30, learn Step 1.9 investigate over the operator-directed docs/tmp drain session

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named bounded operational drain with existing tools applying the proven recipe (development_lessons.md #314), read-only classifier reads plus untracked-tree deletions, no open design choice (the recipe and its proof arms landed with the first drain pass), no guard-bearing path edit, no state schema, no machinery.

Origins:
- docs/history/backlog/2026-10-30-remaining-run-era-tmp-dirs-drain.md

Urgency: low - the named run-era dirs hold a few MB of October residue beside live staging corpora; the recipe is proven and the cost of waiting is growth at the run write rate, not risk.

Scope arms: one bounded drain session over the named directories applying the recipe: per-file producing-run classification, terminal proof through the run-record families, the 48-hour recency gate, the fixed-string plus prefix-form reference veto over docs/history and scheduler-state, wholesale exclusion of the live staging corpora (review-staging, reviews home, authoring), a sha256-sealed deletion manifest into the record home, and leave-in-place reasons recorded on the origin row.

Orientation: development_lessons.md #314 (the recipe and its witnessed gotchas); the landed drain receipt (EXEC-PROMPTS-PRUNE: docs-tmp-dead-residue-drains) as the proven precedent; the origin row. Disk re-derivation at the entry's write: the origin row exists in the working tree and at HEAD, and all eight named directories exist on disk (filesystem probe).

Rejected alternatives:
- Wholesale rmtree of the named directories: rejected because staging and cert-consuming corpora sit beside the residue and the covered safety plan prices exactly this unknown-ownership class (`docs/history/plans/2026-10-27-done-recursive-tmp-sweep-safety.md`)
- Defer to the retention-redesign plan's policy arms: rejected because those arms decide the sweep's standing policy (sync precondition, marker attribution, proof family) and none of them iterates these directories; the drain needs no policy decision (`docs/history/backlog/2026-10-30-docs-tmp-sweep-sync-precondition-catch-22.md`)
- Widen the landing sweep gate to iterate these directories: rejected because that is the guard-bearing policy change the plan entry owns; this run drains manually without editing the gate (`scripts/done_sweep_gates_lib.py`)

Prompt: Using the ad-hoc backlog arm, run the bounded drain over the named directories applying development_lessons.md #314's arms exactly; deletion only after the per-file terminal proof and both veto passes; never edit the sweep gate or any skill text; seal the manifest and record leave-in-place reasons; run the public hygiene scan; delete the origin row per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

## telemetry-pin-provenance-headers

Added: 2026-10-30, learn Step 1.9 investigate over the baseline-repair execution Task 1 intermediate review finding

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named comment-only edit to the provenance headers of one test file (`scripts/test_invocation_telemetry.py`) - no assertion bytes change, so no guard-bearing path; tracked script surface; no open design choice beyond wording the header admits.

Origins:
- docs/history/backlog/2026-10-29-telemetry-pin-provenance-headers.md

Urgency: low - provenance headers currently over-claim the capture base for re-baselined pins, so a provenance audit from headers alone misreads original versus re-captured literals; the cost is an audit false trail, not a behavioral defect.

Scope arms: amend the module-level and Task 3 closeout provenance headers to state which pins were re-captured at the 2026-10-29 re-baseline and which date from the historical bases, so provenance is derivable from the headers alone; keep the scattered inline re-capture comments or fold them into the headers, whichever nets fewer bytes.

Orientation: `scripts/test_invocation_telemetry.py` header comments (fresh read), the origin row's base list, and the 2026-10-29 re-baseline landing for the re-captured literal set.

Rejected alternatives:
- Move provenance out to a sidecar manifest keyed by pin name: rejected as new surface with a single consumer (the occasional provenance audit); the headers are where the auditor already reads (origin row's Direction, docs/history/backlog/2026-10-29-telemetry-pin-provenance-headers.md)
- Drop provenance headers entirely and rely on git blame: rejected because the headers record capture intent (which base certified the literal), which blame cannot distinguish from later formatting touches (origin row's Problem, docs/history/backlog/2026-10-29-telemetry-pin-provenance-headers.md)

## plan-delta-checkpoint-merge-commit-visibility

Added: 2026-11-01, learn Step 1.9 investigate anchored on the row (filed by the execute-plan run's intermediate review over the plan-delta-classifier-new-plan-baseline landing)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named single-surface code fix - one merge-aware flag on an existing history lookup plus one fixture - on `scripts/plan_delta_classifier.py`; no guard-bearing path, no new machinery, no open design choice beyond flag choice.

Origins:
- docs/history/backlog/2026-11-01-plan-delta-checkpoint-merge-commit-visibility.md

Urgency: low - behavior today errs safe (the lookup finds nothing and the named absent-baseline unclassified outcome routes the fold to fresh full review); the cost is only lost baseline reuse for a plan whose first checkpoint is merge-authored.

Scope arms: in `scripts/plan_delta_classifier.py` `first_checkpoint_bytes`, make the history lookup merge-aware (a `--diff-merges=first-parent`-style arm on the existing log invocation) so a first checkpoint authored only inside a merge commit is recovered, keeping the absent-baseline fallback for the genuinely absent case; add one merge-commit fixture to `scripts/test_plan_delta_classifier.py`; no new gate or validator (machinery admission: repair-shaped fix, no machinery arm recommended, so no admission fields are owed).

Orientation: the origin row whole; `scripts/plan_delta_classifier.py` `first_checkpoint_bytes` (introduced c23e4fff5); `scripts/test_plan_delta_classifier.py` `NewPlanBaselineCliTest` fixtures.

Rejected alternatives:
- Keep as-is and rely on the absent-baseline fallback: rejected on the remove-or-keep axis - safe but the lookup exists to recover baseline reuse, and a silent miss for merge-authored checkpoints defeats that purpose while reading as success (origin row Problem; witnessed empirically in a scratch repo 2026-11-01)
- Enumerate candidate blobs with a full walk over the path's history instead of the diff-filter log: rejected as over-scoped - a merge-aware diff on the existing log invocation is the smallest arm; a full walk changes the lookup's cost shape for every plan to cover one rare case (`scripts/plan_delta_classifier.py`)
- Add a new classified category for merge-authored checkpoints: rejected - the classifier's taxonomy classifies edit format, not authorship provenance; the fix restores input visibility rather than adding a class (`docs/history/plans/completed/2026-10-29-plan-delta-classifier-new-plan-baseline.md`)

## inventory-count-reconciliation

Added: 2026-10-30, learn Step 1.9 investigate over the baseline-repair execution Phase 3 round-2 backlogged findings

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): body-named docs-only text corrections across two backlog-row files - the record-range count in the sibling doctrine row and this row's own superseded-count concern - tracked docs surfaces, no guard path, no design choice.

Origins:
- docs/history/backlog/2026-10-30-inventory-count-reconciliation.md

Urgency: low - two stale counts: the sibling quota-doctrine row says the witness covers "records D-1..D-12" while `docs/maintenance/operator-directives.md` carries D-1..D-16 and the witness loop covers all of them (a future sanction-list fix would under-anchor four records); concern 2's plan checkbox totals are superseded authoring-time numbers in a plan now archived to `docs/history/plans/completed/`, so the "refresh when next touched" arm is moot post-archive and lands only as the origin row's own disposition note.

Scope arms: correct both D-1..D-12 mentions in `docs/history/backlog/2026-10-30-quota-doctrine-committed-rewrite-narrowing.md` to D-1..D-16 (re-derive the count fresh from operator-directives.md at landing); resolve concern 2 in the origin row as moot-by-archive with the disposition recorded at the row's covered-row deletion.

Orientation: `docs/maintenance/operator-directives.md` record census (fresh count), the sibling row's Skill-step line, and the origin row; the plan's completed twin for the archive fact.

Rejected alternatives:
- Edit the archived plan's checkbox counts to current values: rejected because the archived copy is the historical record of what the authoring-time plan claimed; annotating is the plan-archive convention, not rewriting (docs/history/plans/completed/2026-10-29-phase2-baseline-repair.md)
- Fold the D-1..D-16 correction into the quota-doctrine plan route only: rejected because the correction is a two-word docs edit admissible now; the plan route owns the witness semantics, not the row text (the sibling row docs/history/backlog/2026-10-30-quota-doctrine-committed-rewrite-narrowing.md carries the Cluster pairing)

## execute-plan-dispatch-blocked-panel-fallback-arm

Added: 2026-10-30, learn+investigate over the 2026-10-29/30 execution run (Phase 3 round whose every worker dispatch attempt was provider-refused; the round ran inline and the fallback was improvised)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a single-surface skill-text arm (one fallback paragraph plus one cross-reference in `agents/skills/execute-plan/SKILL.md` Phase 3), body-named, with no open design choice, no guard-bearing path, no state schema, and no machinery; the record-shaping contract it documents already exists and validated the witnessing round.

Origins:
- docs/history/backlog/2026-10-30-execute-plan-dispatch-blocked-panel-fallback-arm.md

Urgency: medium - a provider-side dispatch block can strand a mid-run review round with no documented in-skill path, and the witnessing session's recovery (inline two-lens round, mutation evidence per guarded mechanism, sidecar reshaped from the producer template's full-panel default to an honest focused claim) had to be assembled by trial and error against the staging validator; the next blocked round repeats that cost without the arm.

Scope arms:
1. Fallback paragraph in Phase 3 (after the dispatch procedure): when every worker dispatch attempt is refused by the provider (distinct from a worker timeout or a quota park), run the planned lenses inline in the parent session, keep mutation evidence per guarded mechanism (neuter, watch a named test fail, restore, cite the pair), and record the round as a focused panel whose fields describe what actually ran: the dispatch block named in the selection reason, workers launched equal to the lenses executed, and the material lens set scoped to those lenses; never accept the producer template's full-panel default over what happened.
2. Cross-reference: the fallback paragraph points at the review-record honesty grammar (panel mode, coverage vocabulary, lens-coverage and verdict coupling owned by `scripts/validate_review_staging.py`) instead of restating it.

Orientation: `agents/skills/execute-plan/SKILL.md` Phase 3 fresh-review procedure (dispatch-era text; latest structural landing 6458f4f75); the witnessing round's record shaping witnessed as project lesson #306 in `docs/maintenance/development_lessons.md`; the origin row for the full observed-versus-expected statement. Disk re-derivation at the entry's write: the origin row exists in the working tree and at the tip commit (`git cat-file -e HEAD:<path>`), and the Phase 3 text carries the dispatch vocabulary (7 hits at HEAD).

Prompt: Using the ad-hoc backlog arm, land both scope arms in one change to `agents/skills/execute-plan/SKILL.md`; skill text only, no machinery, so no admission wording is owed; keep the arm inside the skill text anti-growth rules (the cross-reference pays for the paragraph by naming the grammar's home instead of restating it); run the em-dash added-lines gate and the public hygiene scan; delete the origin row per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

Rejected alternatives:
- Validator-side fix rejecting full-panel records whose workers cannot be evidenced: rejected under the machinery admission protocol - the staging validator already enforces the honesty grammar (coverage vocabulary, lens coverage, verdict coupling) and the witnessed false claim was caught and reshaped by that validator's refusals, so a second gate adds surface with no witnessed incident of a false record passing (scripts/validate_review_staging.py, the witnessing round's validation trail)
- Do nothing (leave the fallback improvised per session): rejected because the fallback is multi-step and record-shape-sensitive; an improvised arm risks a dishonest full-panel claim passing no gate at authoring time and costing a round when the validator refuses it (docs/history/backlog/2026-10-30-execute-plan-dispatch-blocked-panel-fallback-arm.md, observed-versus-expected)
- Route the fallback through the quota-park/resume text instead: rejected because a dispatch block is not a quota wall - the session is alive and authorized, only the dispatch channel is refused; folding the arms would blur two distinct stop conditions with distinct resume recipes (agents/skills/execute-plan/SKILL.md pause records)

## machinery-inventory-baseline-red-repair

Added: 2026-10-30, learn+investigate over the 2026-10-28/29 exec-mandate closeout session (the two origin rows' shared red-baseline class re-witnessed during that run's validation legs)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the group classifies uniformly as a bounded data-alignment pass over `scripts/machinery_registry.json` and the witnesses it cites (register or disposition unregistered script/state-field regrowth rows, re-point stale witness refs, resolve one removals-guard row), single-surface, with no open design choice, no new dependency, no state-schema change, and no machinery added.

Origins:
- docs/history/backlog/2026-10-23-machinery-inventory-baseline-red-obscures-regrowth.md
- docs/history/backlog/2026-10-25-machinery-inventory-check-preexisting-red.md

Urgency: medium - the check exits 1 at every baseline (30 failures 2026-10-23; 25 at one base and 24 at the 2026-10-29 landing tip), so a landing cannot use it as a gate signal and genuinely new regrowth hides in the noise; the counts drift as peer landings touch the sets, so every session paying a validation leg re-adjudicates the same red.

Scope arms:
1. Register or explicitly exempt every unregistered script and state-field regrowth row the check names at dispatch time (the 2026-10-29 witness names the repository's own audit helper, runtime sync and deployment scripts, and one queued-execution state field among the set; re-derive the full set fresh rather than from this entry).
2. Re-point the stale witness references to their surviving durable homes per the guidelines' completed-row citation precedence.
3. Resolve the removals-guard row whose subject script still exists: either the row's removal prediction was wrong (flip the disposition to keep with the corrected witness) or the removal is scheduled in a reviewed change; never delete the live script to satisfy the row.
4. Assert the check exits 0 as the new baseline and its real-tree test arm passes, so later Validation Commands can name the bare check and reach green.

Orientation: read both origin rows whole, then the registry schema and the check's failure output at the current tip (`python3 scripts/machinery_inventory.py --check`), the inventory-upkeep plan that introduced the check (`docs/history/plans/completed/2026-10-02-machinery-inventory-upkeep.md`), and the guidelines' completed-row citation precedence for the witness re-pointing.

Prompt: Using the ad-hoc backlog arm, land the four scope arms in one grouped change; no gate, validator, lock, ledger, or ceremony is added, so the admission line below is the rejection record; run the em-dash added-lines gate and the public hygiene scan; delete both origin rows per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change and retargeting the sibling Cluster pointers to the receipt.

Rejected alternatives:
- A scoped or ignore-list mode for the check: rejected under the machinery admission protocol - the drift is stale registry data, not a checker defect, and no witnessed incident shows a legitimate need to suppress rows ("no witnessed incident" of a scoped-mode consumer; both origin rows)
- Skipping or permanently failing the check's real-tree test arm until the drift is repaired: rejected because that arm is the check's own regression signal; a permanent red hides exactly the regrowth the check exists to surface (scripts/test_machinery_inventory.py RealTreeCheck arm; the 2026-10-23 origin row's What is owed)
- Deleting the still-present enforcement script to satisfy the removals row: rejected because the script is a live enforcement layer with passing suites; row truth yields to disk truth (scripts/check_maintenance_pins.sh in the working tree versus the registry's removals entry)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the arms are registry-data alignment and witness re-pointing; the gate-shaped alternative is rejected above with the missing-incident absence named.


## release-sibling-report-orphan-branch-guard

Added: 2026-10-26, learn+investigate over the 2026-10-26 release run (Step 3 report output)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named single-surface fix (one guard clause in the report-only loop of `agents/skills/release/SKILL.md` Step 3) on a tracked skill surface; the loop runs after publish and reports only, so no guard-bearing path, state schema, or machinery is touched, and no design choice is open.

Origins:
- docs/history/backlog/2026-10-26-release-sibling-loop-flags-orphan-branch.md

Urgency: low - cosmetic noise in an otherwise clean release summary (one stray `fatal:` line and one false sibling report per release in any repository carrying the docs-branch skill's orphan branch); no decision depends on it.

Scope arms:
- Guard clause: in the Step 3 block's `while read -r ref sha` loop, compute `git merge-base "$sha" "$BACKUP_REF"` into a variable first; when it is empty (no common ancestor), `continue` or print one line naming the branch as unrelated history this release did not scan, and run the `--is-ancestor` check only on a non-empty value.
- Anti-growth: the loop's surrounding comment is tightened by the bytes the clause adds.

Orientation: `agents/skills/release/SKILL.md` Step 3 block (loop from ed4a0ff55); `agents/skills/docs-branch/SKILL.md` maintains the orphan `docs` branch that triggers the case on every release (disk re-derivation: `git merge-base docs main` exits non-zero at HEAD); the 2026-10-26 run's Step 3 output is quoted in the origin row.

Prompt: Using the ad-hoc backlog arm, land the one guard clause per the scope arms in `agents/skills/release/SKILL.md` Step 3; the change is skill text with no machinery, so no admission wording is owed; keep the Step 3 summary item 5 wording unchanged; run the em-dash added-lines gate and the public hygiene scan; delete the origin row per the covered-row rule.

Rejected alternatives:
- Leave the loop and read past the fatal: rejected because the skill asks the agent to relay the sibling list verbatim and the false report misstates what publishing the orphan branch would do (agents/skills/release/SKILL.md)
- Move the loop into `scripts/release-rewrite.sh` or the push script: rejected because the report is intentionally outside the gated scripts and the move would grow a guard-bearing path for a cosmetic fix (scripts/release-rewrite.sh)
- Exclude the `docs` branch by name: rejected because the defect is the missing no-ancestor case, which any orphan branch triggers (agents/skills/docs-branch/SKILL.md)

## closeout-operator-attribution-stale-phrase

Added: 2026-10-27, investigate over the two same-day rows below (both execute-plan Phase 3 review findings from the ad-hoc-worktree-lifecycle-owner-gap plan; same defect class: an operator-control attribution that the landed Terminal closeout ownership clause reassigned to the owning orchestrator)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): both members are body-named single-surface prose fixes (one shell comment reword, one consumer-prose mapping sentence) with no open design choice, no guard-bearing path (no gate reads the phrase; the canned gate lines stay untouched), no new dependency, no state-schema or machinery change; both classify uniformly, so the group routes as one entry to this log.

Origins:
- docs/history/backlog/2026-10-27-done-run-resweep-comment-operator-claim.md
- docs/history/backlog/2026-10-27-gate-held-lines-operator-phrase-mapping.md

Urgency: low - a comment and a reporting-prose attribution misdirect a closeout reader about who owns the next action; no gate consumes the phrase and the orchestrator-owned behavior itself is landed and correct.

Scope arms (urgency order):
1. done_run.sh comment reword: the residue-sweep comment at scripts/done_run.sh (~line 526, "on-disk worktrees, their artifacts, and every branch ref stay operator-controlled") is scoped to stand-alone runs and names the owning orchestrator for orchestrated runs, per the Worktree-first standard's Terminal closeout ownership clause and the ad-hoc-worktree closeout paragraph in agents/skills/execute-plan/SKILL.md (execute-plan-closeout gate region); comment-only, no behavior change.
2. Consumer-prose mapping line: the retained-branch reporting sentence in the same execute-plan closeout paragraph (or the done skill's branch-closeout paragraph, whichever reads as the consumer of the gate's canned output) gains one clause mapping the gate's canned "for operator resolution" / "stay for operator resolution" phrases to the owning-orchestrator runner on orchestrated runs, so a retention report quoting gate output verbatim does not contradict its own next-action owner.

Orientation: read both origin rows, then the landed Terminal closeout ownership clause (Worktree-first standard lifecycle step 6; plan docs/history/plans/completed/2026-10-24-ad-hoc-worktree-lifecycle-owner-gap.md, whose review residuals are these rows), the scripts/done_run.sh setup comment, the canned held/skip lines in scripts/worktree_closeout_migrate.py (untouched: consumers quote them verbatim), and the retained-branch reporting sentence in agents/skills/execute-plan/SKILL.md. Disk re-derivation at the entry's write: the stale comment exists at scripts/done_run.sh:526 (working-tree grep and git grep at the tip both hit), and the canned phrases exist in scripts/worktree_closeout_migrate.py.

Prompt: Using the ad-hoc backlog arm, land both scope arms in one change; prose-only on one shell comment and one skill paragraph, so no admission wording is owed; run the em-dash added-lines gate and the public hygiene scan; delete both origin rows per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

Rejected alternatives:
- Reword the canned gate lines in scripts/worktree_closeout_migrate.py instead of mapping them in consumer prose: rejected because the lines are read-only-anchored by the covering plan's constraint and consumers quote gate output verbatim, so changing them breaks the quoting contract the retained-branch reporting rule pins (docs/history/backlog/2026-10-27-gate-held-lines-operator-phrase-mapping.md)
- Delete the operator claim from the residue-sweep comment outright: rejected because on stand-alone runs the operator genuinely does control the retained branches; the defect is the missing scope qualifier, not the claim itself (scripts/done_run.sh, the plan docs/history/plans/2026-10-19-gate-removal-closeout-accounting the comment cites)
- A lint or validator flagging operator-attribution phrases in comments and prose: rejected under the machinery admission protocol - the witnessed cost is reader misdirection at closeout, not a wrong landing, and the false-positive surface is every legitimate stand-alone-run attribution ("no witnessed incident" of a script-catchable misfire)
- Leave the comment and quote the gate verbatim with no mapping: rejected because the retention report then carries a next action owned by the orchestrator beside an attribution naming the operator, the exact contradiction the row's driving force names (docs/history/backlog/2026-10-27-gate-held-lines-operator-phrase-mapping.md)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; both arms are prose; the gate alternative is rejected with the missing-incident absence named above.

## closeout-migrate-zero-delta-silence

Added: 2026-10-28, learn+investigate over the 2026-10-28 02:00 exec run (origin row below; single origin, no open siblings: the closest migration-family row is closed and its subject is a different gate)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the item is a single-surface reporting arm in one script's migrate leg with no open design choice, no new dependency, no state-schema change, and no gate-bearing path; the recommended arm is a warning-only output line, which the machinery admission protocol admits without promotion.

Origins:
- docs/history/backlog/2026-10-28-closeout-migrate-zero-delta-silence.md

Urgency: medium - a silent zero-result strands every run-era record in a worktree that the closeout then removes, the exact loss class the proof-record-retention work (cf2341ebf) paid down; the recovery is a manual delta carry that a trusting closeout never attempts.

Scope arms:
1. Zero-delta distinguishability report: when the migrate leg of scripts/worktree_closeout_migrate.py completes with zero migrated entries, print a report naming the baseline capture timestamp against the newest mtime among the configured dirs' files, so "correctly empty delta" and "baseline postdates the run edits" are distinguishable in the tool's own output; warning-only, exit code unchanged, selftest arms extended for both zero-result readings.
2. Companion skill-text sentence: the execute-plan (or done) closeout paragraph that directs the migrate leg gains one clause: a "Migrated 0" result is re-derived against the run's owned paths before teardown, the manual-delta-carry remedy applying when the baseline postdates the edits.

Orientation: read the origin row, then scripts/worktree_closeout_migrate.py (the baseline-relative transfer in _cmd_migrate_transfer and the "Migrated N" summary line), the covering lands b1f736fb1 (same-run mirror replacement) and cf2341ebf (stale-baseline removal retired) for the mechanism's introduction story, and the Worktree-first standard's closeout migration paragraphs. Disk re-derivation at the entry's write: the summary line exists at scripts/worktree_closeout_migrate.py (working-tree grep hit "Migrated {len(migrated)}"), and the origin row exists at the cited path (ls plus git cat-file -e at the tip both pass).

Prompt: Using the ad-hoc backlog arm, land both scope arms in one change; arm 1 carries the admission wording already in the origin row (warning-only, sunset on next true catch or after three closeouts); run the module selftests plus the em-dash added-lines gate and the public hygiene scan; delete the origin row per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

Rejected alternatives:
- Automatic re-baseline when the migrate leg finds a zero delta: rejected because a late capture that silently claims edits it never saw converts the stranding into a false completion; the report-only arm keeps the decision visible (docs/history/backlog/2026-10-28-closeout-migrate-zero-delta-silence.md, the origin row's pre-rejected arm)
- Make migrate a full-delta copy with no baseline: rejected because the baseline exists to avoid clobbering parallel or foreign edits in the primary checkout, the protection the same-run mirror replacement landing (b1f736fb1) built on; removal discards witnessed protective value
- Skill-text-only rule with no script arm: rejected under the missing-complement axis - the mechanism is correct but its success-shaped zero output is the defect; prose recall alone leaves the tool boundary silent (witnessed: the run's closeout trusted the clean "Migrated 0" and only a post-hoc owned-path comparison caught the strand)
- A pre-teardown validator hard-blocking any zero-result migrate: rejected under the machinery admission protocol as a first-landing blocker for a warning-priced signal - the incident's cost was a recovered manual carry, not a lost landing, and a hard block would false-positive every legitimately empty delta ("no witnessed incident" of a blocked-valid-closeout)

Machinery admission: arm 1 is warning-only output with its four admission fields carried in the origin row (incident: this entry's witnessed strand; catch frequency: every closeout whose baseline postdates owned edits; false-positive cost: one report line on a legitimately empty delta; sunset: promotion to a hard report on the next true catch or review after three closeouts); the validator arm is rejected with the missing-incident absence named above.

## zero-delta-report-defensive-arm-tests

Added: 2026-10-31, learn+investigate over the session that landed closeout-migrate-zero-delta-silence (origin row below; single open origin, no open siblings: the covered EXEC entry closeout-migrate-zero-delta-silence owns the report arm itself, this row owns only pinning its untested defensive branches, a different defect class on the same surface)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the item is test-only additions to one existing suite (scripts/test_worktree_closeout_migrate.py) against already-landed behavior, with no design choice, no new dependency, no state-schema change, and no gate-bearing path.

Origins:
- docs/history/backlog/2026-10-31-closeout-zero-delta-report-arm-coverage.md

Urgency: low - the report arm itself is landed, warning-only, and reviewed; the exposure is latent branch drift in three untested defensive arms (non-string `captured_at`, naive-timestamp read-as-UTC, `Path.resolve()` OSError exclusion fallbacks) that a future refactor could silently change with the suite staying green.

Scope arms:
1. Table-driven tests pinning the three defensive-arm classes named in the origin row: non-string `captured_at` renders as `unknown`, a naive (timezone-less) `captured_at` reads as UTC, and both `resolve()` OSError fallbacks exclude the offending path from the newest-mtime render without failing the report.
2. Delete the origin row per the covered-row rule when the tests land, with this entry's section removed in the same change.

Orientation: read the origin row, then `_print_zero_delta_report` in scripts/worktree_closeout_migrate.py and the existing zero-delta test arms in scripts/test_worktree_closeout_migrate.py (the landed report's introduction story is the covering plan docs/history/plans/completed/2026-10-28-closeout-migrate-zero-delta-silence.md and lesson 288 in docs/maintenance/development_lessons.md). Disk re-derivation at the entry's write: the origin row exists (ls plus git cat-file -e at the tip both pass), and `_print_zero_delta_report` exists at scripts/worktree_closeout_migrate.py:1169 (working-tree grep).

Prompt: Using the ad-hoc backlog arm, land the table-driven tests for the three defensive-arm classes and the origin-row deletion in one change; run the module selftest suite, the em-dash added-lines gate, and the public hygiene scan; remove this entry's section in the same change.

Rejected alternatives:
- Refactor the defensive arms out of the print helper into a pure function so they can be unit-tested directly: rejected as machinery churn for a test-only gain; the function's current output-capture-based tests already pin behavior at the seam consumers rely on, and a refactor widens the reviewed surface the covering plan just landed (scripts/worktree_closeout_migrate.py `_print_zero_delta_report`)
- Delete the defensive arms as unreachable (capture always writes a UTC string; `resolve()` on an existing path cannot fail): rejected because the arms carry defensive value against a legacy or hand-edited baseline file (non-string or naive `captured_at`) and against a file vanishing between the directory walk and the resolve call during closeout; removal converts a guarded report into a crash (docs/history/backlog/2026-10-31-closeout-zero-delta-report-arm-coverage.md)
- Leave the arms untested and rely on the next review to catch drift: rejected because the row's driving force is exactly the silent-drift class the suite exists to lock; the report arm is warning-only, so a silently changed arm produces no failure signal anywhere else (scripts/test_worktree_closeout_migrate.py)
- Property/fuzz testing over arbitrary `captured_at` values: rejected as overkill for three enumerated branches with enumerable inputs; table-driven cases pin each arm deterministically (scripts/worktree_closeout_migrate.py `_print_zero_delta_report`)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the change is tests plus a row deletion; the only machinery-shaped alternative (the pure-function refactor) is rejected above.




## gate-removal-adhoc-invocation-shape

Added: 2026-10-27, learn+investigate over the 2026-10-27 exec-mode max-2 run (origin row below, both of its facets)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): both arms are string-level help and remedy-text edits on one script surface (scripts/worktree_closeout_migrate.py) with no open design choice, no behavior change beyond the printed remedy line, no new dependency, no state-schema or machinery change; the origin is a singleton whose both facets (the unattainable remedy line, the undocumented ad-hoc invocation shape) the arms resolve together, so it routes as one entry to this log.

Origins:
- docs/history/plans/completed/2026-10-27-gate-removal-empty-owned-set-remedy.md

Stage 1 roster: the singleton origin above; the Stage 0 sweep found the one open sibling on this surface (2026-10-26-plan-authoring-stand-down-before-charter.md) already reciprocal-Cluster-annotated with the origin row and routed to its own entry, so no new annotations are owed.

Urgency: low - the witnessed cost is per-closeout improvisation of a fail-closed gate's invocation (a label-less --plan passthrough beside a --claims file, then a second branch-only invocation for the branch record), with no wrong-result incident: the passthrough satisfies the gate correctly and every check still runs; the remedy-text facet misdirects a stuck run toward an unattainable repair.

Scope arms:
1. Ad-hoc invocation shape in help: the gate-removal parser's description (build_gate_removal_parser) and the --plan help line (_add_gate_removal_arguments, scripts/worktree_closeout_migrate.py) gain the ad-hoc form: when the closing run has no plan (an ad-hoc maintenance landing), pass a label-less review record as --plan beside --claims listing the run's review-record paths, and expect the two-mode invocation (worktree mode for the sanctioned removal, then branch-only with an explicit --migration-manifest for the branch record). Help text only; no behavior change.
2. Remedy line: the empty-owned-set refusal arm gains its own attainable remedy line (add the header citation or pass --claims), mirroring the operand refusals' r2 remedy split, instead of printing the capture-and-migrate _GATE_REMEDY_LINE no such run can satisfy; update any suite pin asserting the old remedy line.

Orientation: read the origin row whole (both facets), then _add_gate_removal_arguments and build_gate_removal_parser in scripts/worktree_closeout_migrate.py (disk re-derivation at write time: --plan is required=True with plan-citation-only help, and neither the parser description nor the cmd_gate_removal docstring names an ad-hoc shape), then the empty-owned-set refusal site in the owned-set extraction and the _GATE_REMEDY_LINE constant beside the r2 operand-refusal remedy line, then the completed siblings on the origin row's Cluster lines (the citation/claims remedy split arm 2 mirrors landed with the gate-removal-closeout-accounting plan).

Prompt: Land both arms in one change per the scope arms (one script, string-level edits); run the focused suite (scripts/test_worktree_closeout_migrate.py) to prove no behavior drift beyond the pinned remedy-line update, plus the em-dash added-lines gate and the public hygiene scan; no machinery, so no admission wording is owed; delete the origin row per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

Rejected alternatives:
- Relax required=True so --claims alone admits a plan-less run: rejected - it changes a fail-closed gate's input contract and needs new test pins, while the witnessed cost is improvisation, not a refusal blocking a legal closeout; the documented passthrough keeps the contract closed (scripts/worktree_closeout_migrate.py, _add_gate_removal_arguments)
- A separate gate-removal-adhoc subcommand: rejected as surface duplication for one documented invocation - two parsers to keep in sync on one gate's contract, the nested-parser shape the standalone-parser refactor just removed (the build_gate_removal_parser docstring; plan docs/history/plans/completed/2026-10-19-gate-removal-closeout-accounting.md Task 4)
- Leave the shape improvised per run: rejected - the origin row now carries the witness, and per-run improvisation of a fail-closed gate's invocation is the recurring friction the row exists to end (docs/history/plans/completed/2026-10-27-gate-removal-empty-owned-set-remedy.md, the 2026-10-27 witness section)
- Remove-or-keep on the --plan requirement itself: keep - the plan-citation extraction is the gate's primary ownership model for plan runs (the machinery arrived with the gate family, f3894756d); the ad-hoc case is the minority shape served by the documented passthrough, never by opening the requirement (git log -S "empty owned set" over scripts/worktree_closeout_migrate.py)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; both arms are help and remedy text; the contract-relaxation alternative is rejected above and no admission wording is owed.

## hyphen-bounded-slug-non-match-unpinned (origins: docs/history/backlog/2026-10-27-hyphen-bounded-slug-non-match-unpinned.md)

Added: 2026-10-27, learn+investigate over the interactive exec max-2 run (the executing session; origin row below; the matcher widening's watchlist Low)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): one test pin in scripts/test_execution_claim.py (a single sweep case asserting the non-match) with no open design choice, no guard-bearing path, no new dependency, no state-schema or machinery change - the eligibility test's body-named single-surface-fix clause admits it.

Stage 1 roster: the singleton origin above.

Urgency: low - the guarantee holds at HEAD (two-command re-derivation at the write: no longer-token landing subject exists in the suite by working-tree grep and git grep at the tip, and the boundary regex is present at both) and no wrong-result incident is witnessed; the cost is prospective: a future loosening of the segment boundary keeps the suite green while a longer slug vouches for its prefix, the exact silent-drift class the grammar-form pins exist to lock.

Scope arms:
- Boundary pin: the gateway suite gains one sweep test committing a landing subject naming a longer slug that contains the claim slug as a prefix or suffix (the suite's SLUG constant embedded in a longer token) and asserting the fail-closed skip (the skip reason line and unchanged claim bytes), pinning the matcher's hyphen-bounded-segment guarantee beside the grammar-form pins.

Orientation: read the origin row, then sweep_landing_subject_names_slug in scripts/execution_claim.sh (the docstring states the guarantee; the boundary regex implements it), then the per-form pins and the unrecognized-prefix skip test in scripts/test_execution_claim.py (the pin composes beside them, reusing the scratch-repo sweep pattern including the per-iteration history isolation lesson 276 records).

Prompt: Land the one boundary pin per the scope arm in scripts/test_execution_claim.py; run the focused gateway suite (scripts/test_execution_claim.py) plus the em-dash added-lines gate and the public hygiene scan; no machinery is added, so no admission wording is owed beyond the rejection below; delete the origin row per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

Rejected alternatives:
- A generative test enumerating prefix/suffix tokens for every claim slug: rejected as a new fixture surface for one boundary; one concrete witness pins the guarantee at its own cost, and the suite's scratch-repo pattern has no generative harness to extend (scripts/test_execution_claim.py)
- A lint or validator asserting boundary regexes carry pinned non-match tests: rejected under the machinery admission protocol - no witnessed incident of the guarantee failing, and the false-positive surface is every boundary regex in scripts ("no witnessed incident" of a script-catchable misfire)
- Remove-or-keep on the hyphen-bounded guarantee itself: keep - the guarantee is load-bearing (a longer slug must not vouch for its prefix, the docstring's own statement) and the widening's panel confirmed the behavior live; the missing piece is the pin, not the mechanism (scripts/execution_claim.sh sweep_landing_subject_names_slug)
- Leave the gap on the landing receipt's watchlist only: rejected because a watchlist line is read at review time, not suite time, and the next loosening edit would pass the very suite that exists to stop it (the same lessons-corpus-only miss surface the grammar entry's rejected alternative names, docs/history/backlog/EXEC-PROMPTS.md)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the arm is one test pin; the gate-shaped alternative is rejected above with the missing-incident absence named.

## boundary-plan-write-persistence-verification

Added: 2026-10-26, learn+investigate over the 2026-10-26 03:34 exec run (three silent plan-file checkbox-write losses in one execution run; lesson 241 records the per-run remedy, this entry lands it as operative skill text)

Work-type verdict: ad-hoc-able because the member carries a body-named single-surface fix with no open design choice: one persistence-verification clause appended to the light boundary's plan-edit step in `agents/skills/execute-plan/SKILL.md` (Step 1.4, Light boundary, line ~494), a tracked skill surface, no guard-bearing path, no new dependency, no state-schema change, no machinery (the eligibility test's body-named-fix clause, the Ad-hoc backlog arm bullet in `agents/skills/maintenance/decisions.md`, admits it). Group split: the roster's second member (`2026-10-10-execute-plan-plan-digest-handoff-drift.md`) is plan-worthy - its expected fix is a receipt-backed manifest-transition mechanism in `scripts/execute_plan_runtime.py`, a validator-adjacent surface - so it does not ride this entry; its reciprocal Cluster line records the grouping.

Origins:
- docs/history/backlog/2026-10-26-boundary-plan-write-persistence-verification.md
- docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md (plan-worthy member, split out per the composition rule)

Urgency: low - the witnessed cost is one re-mark plus one re-commit per occurrence (three in one run), and lesson 241's per-boundary advice already bounds the damage; the residual cost is that the verification lives only in a lessons row a fresh implementer never reads.

Scope arms:
- Verification arm: the Step 1.4 light boundary's plan-edit step gains one clause: after the boundary commit, re-derive the plan's box state from disk and from the commit (`git show --stat HEAD` names the plan file; the unchecked-box count dropped by the number of boxes just marked), and on a mismatch re-apply the edit as its own verified commit before the boundary stands as resumable state.
- Mirror arm: where the boundary contract is restated by reference only, no text changes (the Reference contract rule); the clause lands once in the boundary's own home.

Orientation: read lesson 241 in `docs/maintenance/development_lessons.md`, then the light boundary's four legs at `agents/skills/execute-plan/SKILL.md` Step 1.4 (disk re-derivation: `grep -c '^### Step 1.4' agents/skills/execute-plan/SKILL.md` returns 1 at HEAD, and no persistence-verification wording exists there yet: `grep -c 'unchecked-box count' agents/skills/execute-plan/SKILL.md` returns 0). Introduction story: the boundary's commit leg trusts whatever the staging call picked up; the 2026-10-26 run witnessed three boundary calls where a successful in-call plan-file write produced a commit without the plan file and a clean worktree at HEAD, and the loss surfaced only at a Phase 3 review lens.

Prompt: Land the verification arm in `agents/skills/execute-plan/SKILL.md` Step 1.4 only; one clause, no narrative, no restatement of lesson 241's story; run the em-dash added-lines gate and the public hygiene scan over the changed file; pay growth by trimming one restated sentence in the same section; no admission wording is owed because no gate, validator, or ceremony is added.

Rejected alternatives:
- Move plan-file edits out of shell calls into the host write-tool path: rejected because the loss mechanism is unresolved (a plan-protection hook and a racing peer process are both unproven suspects), so rerouting the write path prices a workflow change against an unlocated cause; the verification clause catches the loss regardless of mechanism (witness: lesson 241, docs/maintenance/development_lessons.md)
- A post-commit plan-box counter validator gate on every boundary: rejected under the machinery admission protocol - no witnessed incident of a loss that survived the verification clause's detection, and the false-positive surface is every legitimate mid-run plan edit (docs/history/backlog/2026-10-26-boundary-plan-write-persistence-verification.md)
- Instrument the harness to root-cause the reverting mechanism first: rejected as premature pricing - one witnessed run, one pattern; the smallest arm that removes the witnessed cost (detect and re-apply at the boundary) outranks the architectural one; revisit if the loss re-witnesses after the clause lands (docs/maintenance/development_lessons.md lesson 241)
- Fix only the manifest projection (the plan-worthy sibling's shape): rejected for this member because the runtime manifest is not implicated in the witnessed losses - the boxes were lost from the plan bytes and the commit, not from `runtime_state.json` (docs/history/backlog/2026-10-10-execute-plan-plan-digest-handoff-drift.md, split disposition)

## investigate-cross-run-fix-recurrence

Added: 2026-10-26, operator-directed workflow-loop analysis

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/SKILL.md`): one clause in the existing Stage 2 text of `agents/skills/investigate/SKILL.md`, a single tracked skill surface with no open design choice; it adds no gate, validator, lock, ledger, or required ceremony.

Origins:
- docs/history/backlog/2026-10-26-investigate-cross-run-fix-recurrence.md

Stage 1 roster: the singleton origin above; the Stage 0 corpus survey found no open, uncovered sibling sharing this cross-run classification mechanism.

Urgency: low - the recent history contains adjacent follow-ups but does not prove a same-root recurrence; the October 26 lock-release change completed a missing recovery path after the October 25 closeout landing, while existing review-plan and execute-plan rules already handle recurrence within their respective runs.

Scope arms:
- Cross-run comparison: add one concise instruction to Stage 2 for cases where the new issue plausibly overlaps prior workflow work: compare the prior origin and landed fix with later incident or landing evidence, then record in the existing Orientation or recommendation whether the relationship is recurrence after a fix, regression from a fix, a missing complement, a separate root, or inconclusive. Cite the earlier fix and later witness for recurrence claims. Keep the comparison bounded to relevant history; add no record surface or ceremony. Pay for the added bytes by trimming equivalent wording in Stage 2.

Orientation: read the origin row; `agents/skills/investigate/SKILL.md` Stages 2-3; the covered review-plan nonconvergence origin and completed execute-plan recurrence plan; `docs/history/backlog/2026-10-19-dated-record-stamp-audit-arm.md`, `docs/history/backlog/2026-10-22-adhoc-landing-sentence-omits-land-squash-helper.md` (covered 2026-10-27 by EXEC entry `adhoc-arm-squash-helper-route`; trace via its EXEC-PROMPTS-PRUNE receipt), and `docs/history/backlog/2026-10-04-maintenance-doc-hygiene-review.md`; then inspect commits `058bbb7e0` and `3005cda9b`. The dated-stamp row owns a specific producer defect and the landing-route row (covered as above) owned a consumer defect, while the October 25/26 closeout pair is a missing recovery complement, not proof of the same bug recurring.

Prompt: Land the bounded cross-run comparison clause in `agents/skills/investigate/SKILL.md` Stage 2 only if the investigation confirms the current stage leaves the relationship decision materially implicit; otherwise record that Stage 2 is already adequate and leave the skill unchanged. Keep the instruction limited to plausibly related history and the existing Orientation or recommendation field. Add no machinery or required ceremony. Balance any skill-file growth by deleting equivalent bytes in the same change under the repository's skill text anti-growth rules. Run the public hygiene scan and the em-dash added-lines gate over touched files; do not broaden scope to the specific dated-stamp, landing-route, or maintenance-hygiene mechanisms.

Rejected alternatives:
- Add a cross-run recurrence ledger, validator, or gate: rejected under the Machinery admission protocol - no witnessed incident shows existing history cannot support the comparison, no repeated-root catch frequency is established, and the false-positive cost is durable classification noise on unrelated neighboring issues (origin: `docs/history/backlog/2026-10-26-investigate-cross-run-fix-recurrence.md`).
- Merge this item with the dated-stamp audit or landing-route omission: rejected because those rows name specific field and consumer-skill mechanisms with narrow remedies, while this item concerns how investigations relate potentially connected incidents across runs (`docs/history/backlog/2026-10-19-dated-record-stamp-audit-arm.md`; the landing-route row, covered 2026-10-27 by EXEC entry `adhoc-arm-squash-helper-route`)
- Rely only on the run-local recurrence policies: rejected because the review-plan and execute-plan policies scope their comparisons to one review or execution run and do not classify a later incident against an earlier landed fix (`agents/skills/review-plan/SKILL.md`; `agents/skills/execute-plan/SKILL.md`)

## duty-leg-primitive-precheck

Added: 2026-10-27, learn+investigate over the 2026-10-27 11:03 resume exec session (origin row below; project lesson 263)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the origin carries a body-named single-surface fix (one precheck clause in the Turn-start carrier re-arm duty of agents/skills/maintenance/zcode.md) with no open design choice, no guard-bearing edit path, no new dependency, and no machinery change; the eligibility test's body-named-fix clause admits it.

Origins:
- docs/history/backlog/2026-10-27-duty-leg-primitive-precheck.md

Urgency: low - the witnessed cost is three redundant listing calls and a plan stall in one fired session; no work was lost (no create was owed, so the delete leg was moot), and the loop guard's repeated-listing signature already surfaces the shape when it recurs.

Scope arms:
- Precheck clause: the Turn-start carrier re-arm duty in agents/skills/maintenance/zcode.md gains one clause after its delete-first ordering: a session whose prechecked toolset lacks the delete primitive records the proven-absent leg beside its re-arm decision (naming the duty and the missing primitive; the lingered spawner ages out and the automation-born cap never fires without a create) instead of planning the delete emission.

Orientation: read the origin row, then the Turn-start carrier re-arm duty bullet in agents/skills/maintenance/zcode.md (disk re-derivation: the duty orders the spawner delete "whatever its form" as the first primitive emission, and "lacks the delete primitive" is absent from the file at the tip by working-tree grep and git grep alike), the operator-ordered schedule surface paragraph of the same file (which already owns the "proven-absent deletion primitive" vocabulary for the cap-refused create path), project lesson #263 in docs/maintenance/development_lessons.md (the witness), and the reduced-toolset terminal rung of the Child dispatch ladder (which parks decided re-arm/dispatch actions, a different moment than delete-leg planning).

Prompt: Land the one clause per the scope arm in agents/skills/maintenance/zcode.md; prose only, no machinery, so no admission wording is owed; run the em-dash added-lines gate and the public hygiene scan; because zcode.md is a pinned module, also run bash scripts/check_maintenance_pins.sh and treat the pre-existing authoring stand-down gate span red as expected and unrelated; keep the byte change inside the duty bullet; delete the origin row per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

Rejected alternatives:
- Drop the spawner-delete leg for listing-only sessions outright: rejected on the remove-or-keep axis; the leg is load-bearing for create-needing sessions (the delete lifts the automation-born cap per the operator-ordered schedule surface ordering), so the correct shape is naming the proven-absent disposition where the leg is planned, not removing the leg (agents/skills/maintenance/zcode.md, the operator-ordered schedule surface paragraph)
- Extend the reduced-toolset terminal rung to own the delete-leg disposition: rejected because that rung parks decided re-arm/dispatch actions with paired payload copies, a heavier surface than a delete leg that is moot when no create is owed; the clause names the disposition at the duty the session is already reading (agents/skills/maintenance/zcode.md, the reduced-toolset terminal rung)
- Rely on project lesson #263 alone with no duty-text change: rejected because a fired session reads the duty text, not the lessons corpus, at the planning moment; the clause is the surface the loop actually loads (docs/maintenance/development_lessons.md #263, the why-line's planning-from-duty-text witness)
- A toolset-precheck gate refusing primitive-missing duty planning: rejected under the machinery admission protocol - no witnessed incident beyond redundant listings and a stalled plan, and the false-positive surface is every legitimately primitive-capable session's duty planning ("no witnessed incident" of script-catchable misfires)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the arm is one prose clause; the gate alternative is rejected with the missing-incident absence named above.

## weekly-workflow-loop-review
Frozen: ad-hoc worktree `2026-10-26-weekly-workflow-loop-review` (2026-10-26)

Added: 2026-10-26, operator-directed decision to make workflow reflection recurring

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): one body-named, single-surface change adding a tracked task procedure under `docs/maintenance/recurring-tasks/`, with the cadence, report location, read-only boundary, and pilot decision already chosen; the existing registry supplies scheduling and task state, so no guard, state-schema, dependency, or gate change is needed.

Origins:
- docs/history/backlog/2026-10-26-weekly-workflow-loop-review.md

Stage 1 roster: singleton origin above. The prior cross-run recurrence item is already represented in `EXEC-PROMPTS.md` and concerns classification within an individual investigation, so it is not a sibling of this portfolio-level report task.

Urgency: low - the user requested the review, but one manually requested reflection does not establish a recurring same-root failure; the audit is read-only, though each run consumes the existing audit dispatch and authoring-lane slot.

Scope arms:
- Weekly portfolio reflection: add one `kind = "audit"` task file at a seven-day cadence. It uses the registry's default per-task state and `next_due`, writes one dated report under the facts-resolved `metrics_dir`, and reads only repository backlog rows, both prompt logs, relevant plans/dispositions, and commit history. On cold start, analyze the prior 30 complete days; afterward, analyze the interval since the previous report. Count work by distinct origin groups and separately count associated or unclassified commits. Categorize work as new capability, defect fix, workflow follow-up, or unknown; for plausible follow-ups, record recurrence, regression, missing complement, separate root, or inconclusive with origin and landing witnesses. End with an evidence-rated conclusion of improving, repeat-root pattern, mixed, or insufficient evidence; compare counts only when their windows and denominators match. Never infer recurrence from timing alone. After four reports, include a pilot-usefulness recommendation for the operator; do not change priorities, file backlog items, or introduce a gate.

Orientation: read the origin; `docs/maintenance/recurring-tasks/weekly-skill-review.md` and `docs/maintenance/recurring-tasks/friction-audit.md`; the generic registry consult in `agents/skills/maintenance/survey-arms.md`; the registry's configuration and state defaults in `agents/skills/maintenance/SKILL.md`; completed plan `docs/history/plans/completed/2026-10-03-recurring-task-registry.md` (especially its weekly-skill-review registration decision); completed plan `docs/history/plans/completed/2026-09-23-ai-harness-friction-audit.md`; the per-item cross-run treatment in `docs/history/backlog/2026-10-26-investigate-cross-run-fix-recurrence.md`; and the standard `metrics_dir` key and `.ai-playbook/metrics/` fallback in `agents/skills/docs-branch/SKILL.md`. The registry's default state record already supplies the due anchor.

Prompt: Add only `docs/maintenance/recurring-tasks/weekly-workflow-loop-review.md` with the header `id = "weekly-workflow-loop-review"`, `cadence_days = 7`, and `kind = "audit"`; use the registry's default state record, whose `next_due` is the due anchor, and resolve the dated local report home from `metrics_dir`. Keep the first report's window to the prior 30 complete days and later windows to the time since the previous report. Read repository artifacts only, state denominators and unclassified work explicitly, and make every recurrence or regression claim cite the earlier origin/fix and later witness; mark unresolved relations inconclusive. End each report with an evidence-rated conclusion of improving, repeat-root pattern, mixed, or insufficient evidence; compare counts only when windows and denominators match. The report is read-only and report-only: at report four, recommend whether to keep, narrow, or remove the pilot task for the operator to decide; never alter priorities or create backlog items. Do not add a skill, script, scheduler field, separate ledger, gate, or task-specific runtime machinery; the generic registry already lists, schedules, and records task state. Run the public hygiene scan and em-dash added-lines gate on the task file. Do not broaden the task to skill-text audits or the separate ad-hoc review-path issue.

Rejected alternatives:
- Create a workflow-reflection skill called by every investigate run: rejected because investigate's existing unit is one backlog group and emits one dispatch prompt, so a corpus-wide reflection would be repeated per item instead of run on its own cadence (`agents/skills/investigate/SKILL.md`)
- Fold the reflection into weekly-skill-review: rejected because that task rotates a bounded skill-text corpus and reports skill defects, while this review needs a whole-portfolio time window and task/landing relationships; combining them couples distinct report scopes to the skill rotation cursor (`docs/maintenance/recurring-tasks/weekly-skill-review.md`)
- Add a separate trend ledger, database reader, or causal dashboard: rejected under the Machinery admission protocol - no witnessed incident shows the existing backlog, prompt logs, plans, commits, and task state cannot support this report, and the false-positive cost is durable causal labels from incomplete telemetry (`docs/history/plans/completed/2026-09-23-ai-harness-friction-audit.md`)
- Keep reflection on demand only: rejected because it leaves the requested weekly cadence dependent on the operator remembering to ask, while the existing registry already provides a weekly due signal (`agents/skills/maintenance/survey-arms.md`)

EXEC-PROMPTS-PRUNE: reduced-toolset-rearm-park-broadcast-clause -> landing in this commit (ad-hoc landing: the Reduced-toolset terminal rung in agents/skills/maintenance/zcode.md gained one sentence requiring a session parking pending_rearm on absent mutation primitives to also append one memory-index line naming the park and the missing primitives, so a primitive-capable session sees the discharge duty without reading the state file first; em-dash added-lines gate and public hygiene scan pass; pins suite fails at HEAD on the pre-existing authoring stand-down gate span pin, unrelated; focused panel (panel_mode: focused, docs-only normative prose) contract-docs + correctness-completeness, r1 ready=yes final 0 blocking, three Lows on the record watchlist; origin row deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: seal-receipt-placeholder-path-contract -> landing in this commit (ad-hoc landing: the Receipt content contract paragraph in docs/history/certification-seal-landing-diagnostics.md gained the masking contract sentence - every embedded path, command string, and captured output uses the procedure's placeholder tokens or a repo-relative path, never a resolved filesystem root, with malformed receipts expressed compliantly before appending; paid by trimming the warning-value parenthetical and compressing the fallback narration the outcome matrix owns, header net -39 bytes vs base; em-dash added-lines gate and public hygiene --files scan over the ledger pass; focused panel (panel_mode: focused, docs-only normative prose) contract-docs + correctness-completeness, r1 one blocking fold (write-failures routing collided with the fallback ledger's append-failure-only contract, replaced by the mask-before-append duty; token parenthetical made illustrative), r2 ready=yes final 0 blocking; origin row deleted per the covered-row rule and its two 2026-10-21 sibling Cluster pointers retargeted to this entry)

EXEC-PROMPTS-PRUNE: unattended-ambiguous-clock-ask-disposition -> landing in this commit (ad-hoc landing: the AGENTS.md clock-time confirmation bullet gained the unanswerable-operator disposition sentence - an automation-born or otherwise unattended session records the ambiguity, arms no carrier, and reports the ask as unscheduled per the section's convention; em-dash added-lines gate and public hygiene scan pass; focused panel (panel_mode: focused, docs-only normative prose) contract-docs + correctness-completeness, r1 ready=yes zero blocking, one minor fold (the covered annotation names itself as the candidate's requested wording pass) plus three Lows on the record watchlist; origin row 2026-10-23-scheduling-asks-rearm-wording-candidates.md stays open for candidates 1-3 with Candidate 4 annotated COVERED, no row deletion)

EXEC-PROMPTS-PRUNE: done-finalize-deferred-squash-silent-success -> landing in this commit (ad-hoc landing: the finalize leg in scripts/done_run.sh gained the deferred-squash honesty arms - a ledger landing commit not on the base branch (ancestry check or the squash-proof tree scan; base from the facts base_branch key, then origin/HEAD) prints the refusal-grade LANDING DEFERRED warning naming the merge-lock holder label and the resume duty with the branch tip, the landing summary names branch_commit= instead of landing_commit= while the squash pends (the child-commit corner prints the same deferral when the ledger's first line postdates the marking), the landing-cost telemetry line waits for the landed state, and the run manifest's complete marking is withheld with the checkpoint kept until the squash lands; a landed commit keeps the current success shape; wrapper suite regressions pin the held-lock deferral, the resume completion of the withheld state, the direct-base landed shape, and the squash-proof tree match, suite 151 passed; origin row deleted per the covered-row rule and the residuals row's stale Cluster pointer to it removed in the same change)

EXEC-PROMPTS-PRUNE: worktree-adhoc-provisioning-text-gaps -> landing in this commit (ad-hoc landing: the lifecycle step 1 survey arm gained the ad-hoc topic-key sentence (match each origin row name, the entry's own slug, and their abbreviated variants; a same-subject worktree holding uncommitted edits is a live peer hold, skip and report), the Transfer-in implementation block gained the mirror-skip sentence (a run writing its review records directly to the primary reviews home skips the fence's two copy legs while keeping its resolution and mkdir legs; the copy legs are for plan runs whose readiness gate and review workers read the worktree-side copy), and the lifecycle step 4 closeout-rider enumeration gained the receipt-paired removal clause (an EXEC-PROMPTS-PRUNE receipt lands in the same change that removes the entry section the receipt names) with its opening conditional widened to ad-hoc maintenance landings so the clause binds the class that appends the receipt; prose only, no machinery; em-dash added-lines gate and public hygiene scan pass; focused panel (panel_mode: focused, docs-only normative prose) contract-docs + correctness-completeness, r1 one blocking fold (the rider conditional excluded ad-hoc landings) plus one Medium and three Low wording folds, r2 confirm; all three origin rows deleted per the covered-row rule and this entry's section removed in the same change)

EXEC-PROMPTS-PRUNE: producer-record-digest-family-routing-note -> landing in this commit (ad-hoc landing: execute-plan Step 3.1 gained the Digest-family ownership paragraph naming the digest family each freshness instrument owns (producer = plan-family -plan-review- records over the plan-bytes SHA-256, plan-review record freshness owned by the review-plan mechanical gate's --source-plan check, the Phase 4 exec receipt sharing that digest domain; verify-digest = code-family over the git diff <base>...<head> bytes SHA-256, never accepting a producer record; exec rounds record code freshness through the Round-close seal), the Round-close seal paragraph's duplicated checker clause collapsed in the same file as the growth payment, and the producer module docstring states the same family boundary in one sentence; focused panel (panel_mode: focused, docs-only) contract-docs + correctness-completeness r1 6 raw / 4 staged (two echo pairs), all four folded (receipt clause recast to a shared-digest-domain statement, plan-family checker pointer restored, docstring exec-round prescription dropped, seal facts replaced by a Round-close-seal pointer), r2 both workers confirm all four resolved, verdict ready=yes final 0 blocking; validate_review_staging --selftest, em-dash added-lines gate, public hygiene scan pass; origin row 2026-10-22-producer-review-findings-followups.md stays open with its routing-note bullet annotated landed in the same change)

EXEC-PROMPTS-PRUNE: finalize-honesty-test-coverage-residuals -> landing in this commit (ad-hoc landing: scripts/done_run.sh landing_pending_state gained the content-form squash proof - the branch delta's patch-id compared against each scanned base commit's first-parent delta patch-id inside the same 500-commit window, the tree-identity match kept as the fast path - so a run branch rebased after its ledger lines were written still proves its squash; DoneRunFinalizeTest gained the five coverage regressions (rebase patch-id match, unresolvable-base fail-open, origin/HEAD fallback deferral, guard-child corner deferral, 500-commit window bound); wrapper suite 158 passed, em-dash added-lines gate and public hygiene scan pass; origin row deleted per the covered-row rule)

EXEC-PROMPTS-PRUNE: worktree-survey-live-peer-hold-clean-committed -> landing in this commit (ad-hoc landing: the survey arm's ad-hoc sentence in agents/skills/execute-plan/worktree-first.md widened - a same-subject worktree holding uncommitted edits, or whose HEAD commit postdates the worktree's creation and is not yet an ancestor of the base branch (project lesson 233's re-point witness), is a live peer hold, skip and report; em-dash added-lines gate and public hygiene scan pass; origin row deleted per the covered-row rule, this entry's section removed in the same change)

EXEC-PROMPTS-PRUNE: review-worker-scratch-worktree-cleanup-clause -> landing in this commit (ad-hoc landing: the read-only-tree clause in both review worker templates in agents/skills/execute-plan/subagent-prompts.md (Step 1.2b rule 4 and the Review lens template) gained the scratch-copy preference sentence - prefer a plain directory copy; when a separate `git worktree add` is genuinely needed, create it under the session's tmp directory so the run's own closeout sweep removes it, never under an untracked /tmp path; em-dash added-lines gate and public hygiene scan pass; origin row deleted per the covered-row rule, this entry's section removed in the same change)

EXEC-PROMPTS-PRUNE: java-guideline-rule-27-clarity-gaps -> landing in this commit (ad-hoc reviewed landing: rule 27 of projects/.ai-playbook/java_guidelines.md gained the multi-over-threshold binding sentence (prefer class-level @Builder, consolidation signal, builderClassName coexistence carve-out) and the finite-gauge **Verify:** line in the rules 20-25 shape, byte-paid by the exemption paragraph restated tail; focused docs panel (contract-docs + correctness-completeness) r1 two Medium folds (Verify hand-written scoping, ambiguous noun phrase) plus three Lows (one folded: builderClassName gauge branch; F4 validation-placement residual on the watchlist), r2 confirm ready=yes final 0 blocking; both origin rows deleted per the covered-row rule, this entry section removed in the same change; Ad-hoc-panel-pass: .ai-playbook/reviews/2026-10-27-java-rule27-adhoc-code-review-r2.md 73bd52eb540531dd32cb155d024bfc7a02b6f265662debbba4948e3df2109174)

EXEC-PROMPTS-PRUNE: state-file-schema-declaration-reconciliation -> landing in this commit (ad-hoc reviewed landing: agents/skills/maintenance/state-file.md schema declarations reconciled to live state - children[] outcome enum gains in_progress, the worktree field paragraph names the check-side first-observation backfill as its second writer per the failure-cap resolution order, and the schema-v4 example declares the top-level notes array with both observed key spellings (at+note, ts+note legacy tolerated) plus the Step 6 carry-forward clause; focused docs panel (contract-docs + correctness-completeness) r1 one blocking fold (notes shape missed live ts entries) + two Low folds, r2 one blocking fold (fold-introduced falsified date qualifier, prescribed minimal fix applied), r3 confirm ready=yes final 0 blocking; both origin rows deleted per the covered-row rule, this entry section removed in the same change; Ad-hoc-panel-pass: .ai-playbook/reviews/2026-10-27-statefile-schema-adhoc-code-review-r3.md 6bfc54f39b3f803e1b9ac8360d7761c273bd87d5efc80ac6db7eb455dc45e7e9)

EXEC-PROMPTS-PRUNE: strand-drain-rider-carry-duty -> landing in this commit (ad-hoc landing: the execution blueprint rider paragraph in agents/skills/maintenance/template-execution.md gained the pre-landing rider-verification duty - diff the run branch delta for the run closeout riders (the riders this paragraph names above, plus for ad-hoc maintenance landings the ad-hoc log receipt-paired entry removal and the panel-record annotation per lesson 267) and land any missing rider on the branch, since a later strand drain lands the branch as-is and the riders-ride-the-branch rule is spent once the branch lands - with the drainer-side See-also naming lesson 267 work-plus-riders rule; prose only, no machinery; em-dash added-lines gate and public hygiene scan pass, pins suite pass with advisory caps-gap and prune-range warn lines only; origin row deleted per the covered-row rule with both sibling rows stale Cluster pointers tidied in the same change, this entry section removed on the branch before the landing; focused panel (panel_mode: focused, docs-only normative prose) contract-docs + correctness-completeness, r1 two Medium folds (receipt-paired prune missing, rider set unenumerated), r2 confirm ready=yes final 0 blocking; Ad-hoc-panel-pass: .ai-playbook/reviews/2026-10-27-strand-drain-rider-carry-duty-adhoc-code-review-r2.md adec904752700733b099862435cdf4ce7304571d4e8f345a57492e66246752eb)

## closeout-mirror-family-residuals

Added: 2026-10-27, learn+investigate over the 4 am WET exec carrier run (automation-ea20ad59; the landing session; origin rows below)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md), applied per origin row: each row is a small arm in an existing script or skill-text surface (the failed-entry printer, the step 5 digest-verification route, the replace path's write ordering, one report-level cross-check, a consolidation pass over already-landed prose), with no open design choice, no guard-bearing edit path beyond naming the check, and no new machinery (the gate-shaped hardening alternative is rejected below) - the small-single-surface shape admits all three, so the group routes as one entry by the uniform verdict.

Origins:
- docs/history/backlog/2026-10-27-closeout-mirror-residuals.md
- docs/history/backlog/2026-10-27-execute-plan-skill-mirror-growth-unbalanced.md
- docs/history/backlog/2026-10-27-closeout-replacement-failure-print-labels.md

Stage 1 roster: the three rows above, grouped by shared surface: the closeout-migration boundary-mirror family the covering plan introduced (docs/history/plans/completed/2026-10-24-closeout-migration-same-run-mirror-replace.md, landed 2026-10-27); defect classes differ (residuals/hardening, text growth, printer labels) but the arms share the same two files, so one run can carry them. Two of the residuals row's five items are recorded-only acceptances and owe no work (stated under Scope arms).

Urgency: low - all three origins carry Priority: low, every residual is fail-safe (conservative staleness, bounded residue, or cosmetic stderr), and the family landed today with its 243-check suite green, so no closeout is blocked until an arm lands.

Scope arms:
- Printer labels (origin 3): branch the failed-entry printer and the summary line in scripts/worktree_closeout_migrate.py on replacement-class failures (staging/install), keeping the existing copy-verification wording for the plain copy class; a regression in the script's suite pins each class's label.
- Digest-route extension (origin 1 item 2): extend worktree-first.md step 5's per-record digest-verification route to the `replaced` disposition (verify the replaced record against the migration manifest's verified+incoming_state digests), so the route's letter covers a record with no migrated entry.
- Interrupt-window parity (origin 1 item 1): mirror the producer's append-before-install pattern into the migrate-side receipt replacement (record the manifest entry before installing staged bytes), closing the post-install pre-record KeyboardInterrupt window that strands the `.repl-*.prior-tmp` sibling; a regression simulates the interrupt ordering.
- Identity cross-check (origin 1 item 3): a report-level line in cmd_boundary_mirror comparing --worktree against the manifest's run_worktree identity line (a mismatch is printed and included in the summary; it does not refuse - see the rejected gate alternative).
- Growth consolidation (origin 2): one consolidation pass over agents/skills/execute-plan/SKILL.md Step 1.4 (legs 1-4 dedup, boundary-worker machinery remnants) trading bytes against the recorded +1.1 KB net growth, per the repository's pay-for-growth discipline.
- Recorded-only, no work owed (origin 1 items 4-5): the refused-acquire lock-free manifest write and the premortem un-timeout'd source read stay as recorded acceptances; this entry neither opens nor closes them.

Orientation: read the three origin rows and the covering plan's Phase 3 residual section, then the surfaces: the failed-list printer and summary line plus `_replace_receipt_proven`/`_append_manifest`/`cmd_boundary_mirror` in scripts/worktree_closeout_migrate.py, worktree-first.md step 5, and execute-plan SKILL.md Step 1.4 legs 3-4. Disk re-derivation at write time (working-tree probes plus git probes at the tip): the plan archive, the script, its test suite, and both skill files all exist at the tip; the legacy summary label ("N file(s) failed copy verification") is present at scripts/worktree_closeout_migrate.py:1291 in both probes; the manifest's run_worktree identity line resolves (9 hits in the script at the tip).

Prompt: Land the arms as separate commits in one ad-hoc run grouped by surface (script arms together, skill-text arms together); run the script's test suite (unittest discover form), the em-dash added-lines gate, and the public hygiene scan; the panel is the focused code+testing panel for the script arms and the focused docs panel for the skill-text arms; no machinery admission wording is owed (all arms extend existing behavior; the gate-shaped alternative is rejected below); delete all three origin rows per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line, tidying sibling Cluster pointers and removing this entry's section in the same change; record the two recorded-only acceptances as unchanged.

Rejected alternatives:
- A refusing gate on worktree/manifest identity divergence: rejected under the machinery admission protocol - no witnessed incident ("no witnessed incident": the residuals row itself records that divergence already mirrors foreign bytes visibly at boundary time, so the check adds no protection a visible report lacks); the report-level cross-check is the smaller arm (docs/history/backlog/2026-10-27-closeout-mirror-residuals.md item 3)
- Post-hoc sweep of stranded `.repl-*.prior-tmp` siblings as the interrupt-window fix: rejected as symptom-shaped - the sibling is the prior-bytes recovery copy and a sweep would delete it; write-ordering parity with the producer's append-before-install pattern removes the window instead (docs/history/plans/completed/2026-10-24-closeout-migration-same-run-mirror-replace.md, the producer-side pattern)
- Pay the growth debt by deleting the boundary-mirror delegation from Step 1.4: rejected - the delegation is consumed operative text (the landed exit-semantics sentence and transfer-out lock-span clause ride it), so the trade comes from in-section repetition and boundary-worker remnants, exactly the candidates the origin row names (docs/history/backlog/2026-10-27-execute-plan-skill-mirror-growth-unbalanced.md)
- Reword all copy failures generically instead of branching the printer: rejected - the generic label is accurate for the plain copy class, and blurring it loses the copy-precision the existing wording was pinned for (scripts/worktree_closeout_migrate.py failed-list printer, the class the covering plan's tests assert)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the identity cross-check is report-level, and the gate-shaped alternative is rejected above with the missing-incident absence named.

EXEC-PROMPTS-PRUNE: adhoc-arm-closeout-unowned-staged-entries -> landing in this commit (ad-hoc landing: the Ad-hoc backlog arm closeout in agents/skills/maintenance/decisions.md gained the staged-set re-derivation clause - re-derive the primary checkout's staged set before a landing or path-limited closeout commit in a shared checkout, stage only the run's own named paths, never a broad add, and take the landing class's own refusing shape on any staged entry at the landing commit, standing down and reporting instead of staging around foreign entries; prose only, no machinery; em-dash added-lines gate and public hygiene scan pass; origin row deleted per the covered-row rule and this entry section removed in the same change; focused docs panel contract-docs + correctness-completeness over the branch delta, record .ai-playbook/reviews/2026-10-27-adhoc-arm-closeout-staged-entries-adhoc-code-review-r3.md)

EXEC-PROMPTS-PRUNE: closeout-proof-record-retention -> landing in this commit (ad-hoc landing: gate_docs_tmp_sweep retains the execute-plan plan-slug proof family (closeout-baseline.json, closeout-baseline-skip.json, closeout-migration.json) with a per-member retained-and-reported line, superseding the retired age-bounded stale-baseline removal so a retry re-reads the predecessor's proof state and a later closeout's gate-removal keeps its manifest operand; done_run.sh's worktree arm copies the owned plan's cited review records from the primary reviews home into the run's reviews home through the new copy-cited-records helper subcommand before the verify-records leg (report-and-continue; containment unchanged); owning suites re-pinned (stale-baseline arms re-pinned to retention, skip-only and manifest-only retention regressions added, help catalog widened to seven commands): 576 passed, wrapper suite green, em-dash added-lines gate and public hygiene scan pass; both origin rows deleted per the covered-row rule, their sibling Cluster pointers retargeted to this entry)

## staging-preflight-shared-span-row-closeout

Added: 2026-10-27, maintenance investigation of the highest-priority uncovered row after the shared-span amendment and both executions were re-derived

Work-type verdict: ad-hoc-able because the original stale-anchor risk was resolved by amending the later plan before its execution, and the remaining work is exact backlog cleanup with no implementation choice or source change.

Origins:
- docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md

Stage 1 roster: singleton. The origin's only other backlog `Cluster:` target is already absent, its remaining backlog target is covered, and the two named plan peers are archived; no open sibling remains.

Urgency: low - the predicted collision was caught by the execution sequence, the second plan was re-anchored before its task ran, and no unresolved stale anchor remains; the open row is now a misleading duplicate-work candidate rather than an active blocker (the origin and both completed plans).

Scope arms:
- Retire the resolved origin row under the repository's ad-hoc covered-row rule and remove the exact stale `Cluster:` pointer from the completed backlog record that points to it; preserve historical plan citations and amendment evidence.
- Do not change skill text, validators, plans, or executable behavior; the intended record is already present in the completed plan's amendment and disposition.

Orientation: read the origin row; `docs/history/plans/completed/2026-10-06-authoring-staging-preflight-gates.md`'s seam disposition; `docs/history/plans/completed/2026-10-07-done-readiness-closeout-boundary.md`'s pre-execution amendment and Task 2; and `agents/skills/maintenance/prompt-templates.md`'s current assembled-series wording. Confirm the old quoted anchor is absent from the current payload template and the amended second-plan prescription is the one it executed.

Prompt: In one ad-hoc closeout, verify that the origin's expected outcome is already satisfied by the archived execution records: the staging-preflight plan landed first, the done-readiness plan's stale Task 2 anchor was amended before execution, and its amended Task 2 landed. Then delete `docs/history/backlog/2026-10-06-staging-preflight-done-readiness-shared-payload-span.md` per the covered-row rule and remove the exact `Cluster:` pointer to it from `docs/history/backlog/completed/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md`. Keep historical `Skill/step`, plan-body, and completion citations as evidence; do not edit operative skill text. Re-scan the backlog for remaining live Cluster pointers to the deleted path, run the normal documentation registry validation, and land the row deletion and pointer cleanup together with a commit subject naming the completed-plan witness. Remove this entry with its `EXEC-PROMPTS-PRUNE` receipt in the same landing.

Rejected alternatives:
- Author a new plan to prevent the stale-anchor collision: rejected because the later plan was amended before execution to match the first landing, and its amended Task 2 completed, as witnessed in `docs/history/plans/completed/2026-10-07-done-readiness-closeout-boundary.md` (Amendment record and Disposition).
- Add a shared-span scanner or execution-order gate: rejected because the witnessed seam was resolved by the existing plan amendment path; no recurring unresolved collision or independent blocking incident is evidenced by the origin or the two completed plans.
- Leave the high-priority row open as future work: rejected because it now describes the pre-amendment state and would continue to look actionable despite the exact remedy and execution already being recorded, as witnessed in the origin and archived amendment record.
- Delete the origin without tidying its `Cluster:` pointer: rejected because the completed backlog record would retain a dead Cluster target after the row is removed, as witnessed in `docs/history/backlog/completed/2026-10-09-dangling-cluster-pointer-staging-series-gate-slug.md`.

Machinery admission: no new gate, validator, lock, ledger, or ceremony is proposed; the remaining action is record cleanup after an already-landed amendment, and the scanner/gate alternative is rejected above for lack of an unresolved incident.

## execute-plan-phase3-panel-composition-residuals

Added: 2026-10-27, maintenance investigation of the low sibling discovered in the worker-capacity panel cluster

Work-type verdict: ad-hoc-able because the open residual is an exact three-surface wording consolidation with no design choice, implementation change, or guard-bearing path.

Origins:
- docs/history/backlog/2026-10-22-execute-plan-initial-pass-composition-drift-residuals.md

Stage 1 roster: this entry handles only the low text residual. The separate worker-capacity incident is already covered by execute-plan Phase 3's partial-panel and same-run resume clauses (`agents/skills/execute-plan/SKILL.md`).

Urgency: low - the composition source-of-truth deferral already landed and the remaining mismatch is wording that can reintroduce a five-worker default in three reader surfaces; the review finding rated it Low with no decision-authority loss (the residual origin and its cited review record).

Scope arms:
- In the worker template, defer initial panel composition to the supplied worker set and remove the restated five-worker default; in the fresh-review table, change `Initial full panel` to `Initial panel`; in the panel-selection orchestrator parenthetical, name the Phase 3 initial-pass deferral beside per-task intermediate selection.
- Keep the single source of composition authority in `agents/skills/review-agents/review-panel-selection.md`; pay any operative-text growth with equivalent deletion in the same files.
- Do not change retry, capacity, lens, or review-exit behavior; those are outside this residual.

Orientation: read the residual origin, its cited r1 review record, the completed panel-selection deferral, `agents/skills/execute-plan/subagent-prompts.md`'s Panel launch paragraph, `agents/skills/execute-plan/SKILL.md`'s Verify-fix vs fresh review table, and `agents/skills/review-agents/review-panel-selection.md`'s orchestrator list parenthetical.

Prompt: Make only the three exact wording consolidations in the origin's Expected section. Keep the panel-selection catalog as the single source of worker composition, preserve its focused-panel trigger, and balance operative-text growth with equivalent deletion in the touched skill files. Run the focused documentation review and the repository hygiene and text checks required for skill edits; do not alter worker execution, retry, or capacity policy. Delete the origin row under the ad-hoc covered-row rule, remove its `Cluster:` line from the medium worker-capacity origin, prune this entry with its `EXEC-PROMPTS-PRUNE` receipt, and commit those record changes with the prose edit.

Rejected alternatives:
- Change worker behavior or launch count to resolve the wording mismatch: rejected because the landed deferral already owns composition and the residual names only three stale statements, as witnessed in `docs/history/plans/completed/2026-10-22-execute-plan-phase3-initial-pass-panel-selection-reference.md`.
- Leave the three copies as-is: rejected because each still repeats or incompletely names the new composition source, which can restore a stale five-worker default in the worker template or fresh-review table, as witnessed in the residual origin's Expected section.
- Change worker retry or resume behavior while consolidating the prose: rejected because the existing bounded partial-panel and same-run resume clauses already cover the capacity incident, while this member is only a low prose consolidation, as witnessed in `agents/skills/execute-plan/SKILL.md`.

Machinery admission: no gate, validator, lock, ledger, or required ceremony is recommended; the wording consolidation changes no decision or execution behavior.

EXEC-PROMPTS-PRUNE: adhoc-arm-squash-helper-route -> landing in this commit (ad-hoc reviewed landing: the Ad-hoc backlog arm bullet's landing sentence names the sanctioned route by reference - the Worktree-first standard's lifecycle step 4 class-ownership paragraph (agents/skills/execute-plan/worktree-first.md), whose helper invocation (land-worktree for the worktree-complete class, land for the primary-checkout class) is the only sanctioned composition; one by-reference clause, no helper mechanics restated, small recorded growth; em-dash added-lines gate and public hygiene scan pass, pins suite pass; focused docs panel (panel_mode: focused, docs-only normative prose) contract-docs + correctness-completeness; origin row deleted per the covered-row rule, its two sibling Cluster pointers retargeted to this entry in the same change; the closeout prune audit reports REMOVED-WITHOUT-WITNESS for this removal structurally - the heading's slug carries the ' (origins: ...)' suffix no single-token receipt slug can match - recorded here as the named state instead of a clean audit, the matcher fix (first-token slug compare) owned as a follow-up outside this prose-only change)

EXEC-PROMPTS-PRUNE: registry-due-read-primary-root -> landing in this commit (ad-hoc landing: the registry-task consult's state-record read arm in agents/skills/maintenance/survey-arms.md gained the read-root sentence - the state record is read at the task's `state_file` override or default path resolved from the primary checkout's live filesystem, a missing record there is the only cold start, and a read keyed on the tracked tree or a worktree checkout reads the gitignored state home as missing and is never a due or cold-start verdict; prose only, no machinery; em-dash added-lines gate, public hygiene scan, and maintenance pins check pass; origin row deleted per the covered-row rule and this entry section removed in the same change with the two sibling rows' Cluster pointers tidied; focused docs panel contract-docs + correctness-completeness over the branch delta, r1 two rider folds folded, record .ai-playbook/reviews/2026-10-27-registry-due-read-primary-root-adhoc-code-review-r2.md)

EXEC-PROMPTS-PRUNE: claim-sweep-landing-subject-grammar-mismatch -> landing in this commit (ad-hoc landing: the sweep landedness matcher sweep_landing_subject_names_slug in scripts/execution_claim.sh accepts every recognized LANDING_CLAIM_PREFIXES form (`plans: land `, `done: execute `, `execute-plan: land `, `author: land `) beside the legacy `check: land ` form with the fail-closed skip unchanged, and its docstring and the sweep usage-header paragraph name the grammar's single source in scripts/reverse_squash_guard.py; per-form test pins in scripts/test_execution_claim.py made order-isolating by the r1 fold (per-iteration history reset); focused code+testing panel correctness-completeness + testing, r1 one Medium fold folded, one Low recorded on the watchlist (hyphen-bounded non-match unpinned, pre-existing debt); focused gateway suite 75 passed + 21 subtests, em-dash added-lines gate and public hygiene scan pass; origin row deleted per the covered-row rule and this entry section removed in the same change with the three sibling rows' Cluster pointers retargeted; record .ai-playbook/reviews/2026-10-27-claim-sweep-landing-subject-grammar-adhoc-code-review-r2.md)

EXEC-PROMPTS-PRUNE: prune-audit-first-token-slug-match -> landing in this commit (ad-hoc landing: the prune-audit receipt compare sites in scripts/check_prompt_log_origins.py match the receipt slug against the removed heading slug's first whitespace-delimited token (receipt_compare_slug at the commit-message, in-commit, and log-ledger receipt classes), removing the structural false negative that owed the named-state ceremony on every landing whose prune-audit window spans a legacy-form origins-suffixed heading removal; the fail-closed REMOVED-WITHOUT-WITNESS arm unchanged; two fixture pins plus the r1 fold's suffixed-form pins for the in-commit and ledger classes, focused checker suite 87 passed; em-dash added-lines gate and public hygiene scan pass; focused code+testing panel correctness-completeness + testing, r1 ready=yes final 0 blocking, one Medium folded (suffixed-form pins for the two remaining receipt classes), two Lows on the record watchlist; origin row deleted per the covered-row rule and the sibling row's Cluster pointer retargeted to this receipt in the same change; Ad-hoc-panel-pass: .ai-playbook/reviews/2026-10-27-prune-audit-first-token-slug-match-adhoc-code-review-r1.md 9ad383e79806142ac7c267ff971da8171fc3d6df9a9c81747f0a89eb2bd8ef07)

EXEC-PROMPTS-PRUNE: worktree-metrics-home-seeded-history -> landing in this commit (ad-hoc landing: the seeder arm re-derived with evidence - the docs-branch sync's branch-only restore leg (restore_files) materializes docs-tracked ledgers (landing-costs.jsonl rides the docs retention commits) into the resolving checkout, and done_run.sh step 13 runs the sync inside the ad-hoc run worktree, seeding the primary's ledger history into a fresh worktree's metrics home before the landing-cost append and the closeout migration carry it back; the migration and transfer-in candidates exonerated by code reading and the entry's other two named candidates exonerated live; remedy arm: scripts/docs_branch_sync.sh gains is_linked_worktree and skips the restore leg in a linked worktree with one named line, so run homes hold only their own lines (the entry's correct-the-seeding-path arm; the exact-duplicate filter alternative not needed), docs-branch SKILL.md names the worktree exception, lesson 262's why-line records the identified seeder; two suite pins plus the r1 folds' exact-line and worktree-own-archive pins, focused docs-branch suite 49 passed 1 skipped (pre-existing platform guard) 26 subtests; em-dash added-lines gate and public hygiene scan pass; focused code+testing panel correctness-completeness + testing, r1 ready=yes final 0 blocking, four Lows all folded; origin row deleted per the covered-row rule, no sibling Cluster pointers owed, this entry section removed in the same change; Ad-hoc-panel-pass: .ai-playbook/reviews/2026-10-27-worktree-metrics-seeded-history-adhoc-code-review-r1.md 9634a4bf691edde60ad86d37e35dc10c4e8860064d750e6c65692f7d603543ca)

## missing-plan-review-series-pd5c64f3c-witness

Added: 2026-10-28, maintenance investigation over the 00:21 exec run's pick-2 teardown finding

Work-type verdict: ad-hoc-able because the origin passes the maintenance skill's Ad-hoc backlog arm eligibility test's bounded-single-session clause: it is one evidence sweep plus one disposition record with no design choice, no operative-text change, and no guard-bearing path.

Origins:
- docs/history/backlog/2026-10-28-missing-plan-review-series-pd5c64f3c-witness.md

Stage 1 roster: singleton. The nearest cluster sibling (the 2026-10-16 series-token citation-grammar row) is covered and owns a different mechanism (a parser that cannot see existing records); this origin's series does not exist anywhere on disk or in reachable history. No open sibling shares the lost-record mechanism.

Urgency: low - the discovering run already recorded the witness note in its exec receipt and the affected plan is landed and archived; the residual is a durable disposition for a dangling citation, not an active blocker.

Scope arms:
- Sweep the durable channels (session-log forensics, archived plan-review sidecars, git history over the authoring date window) for any recoverable bytes of the cited authoring review series; restore any found records to the primary reviews home under their cited names.
- When recovery is impossible, land one disposition note durably beside the plan's citation (the archived plan's header region or the row itself) recording the loss as witnessed-and-accepted, then delete the origin row per the covered-row rule and remove this entry with its `EXEC-PROMPTS-PRUNE` receipt in the same landing.
- Never fabricate record content; a reconstruction that cannot cite recovered bytes is a disposition note, not a recreated record.

Orientation: read the origin row; the archived plan `docs/history/plans/completed/2026-10-24-machinery-registry-witness-home-convention.md` (header citation); the discovering receipt `.ai-playbook/reviews/2026-10-28-plan-review-machinery-registry-witness-home-convention-exec-r1.md`; and the record-durability lesson family in `docs/maintenance/development_lessons.md` (deciding-turn teardown ordering).

Prompt: In one ad-hoc pass, attempt recovery of the review series cited by the archived machinery-registry-witness-home-convention plan: search the durable channels named in the orientation for any `pd5c64f3c` round records or sidecars. Restore found bytes to `.ai-playbook/reviews/` under their cited names; if nothing is recoverable, land a disposition note recording the witnessed loss beside the plan's citation, delete the origin row per the covered-row rule, and remove this entry with its prune receipt in the same change. Never fabricate record content. Run the em-dash and public-hygiene gates over touched files and land under the standard ad-hoc arm (worktree, focused panel, squash).

Rejected alternatives:
- Author a plan to prevent future series losses (a mirror-time gate on worktree removal): rejected for missing machinery admission - the record-durability checkpoint machinery already owns this duty and its failure was discipline, not a missing validator, and no new incident class is named; the witness is the corpus's deciding-turn ordering lesson in docs/maintenance/development_lessons.md
- Reconstruct the series from the archived plan's review-scope text without recovered bytes: rejected because fabricated record content breaks the reviews home's role as the record of record, witnessed by the discovering receipt .ai-playbook/reviews/2026-10-28-plan-review-machinery-registry-witness-home-convention-exec-r1.md; the disposition-note arm is the honest closure.
- Leave the dangling citation undocumented: rejected because the archived plan's header would keep citing a series no reader can resolve, as witnessed by the discovering run's two-command probes (filesystem glob plus `git cat-file` at the tip, both absent).

Machinery admission: no new gate, validator, lock, ledger, or ceremony is proposed; the gate alternative is rejected above with the missing-incident absence named (the existing record-durability duty covers the prevention class).

## seal-file-parse-poisoning-diagnostic

Added: 2026-10-29, learn Step 1.8 witness + investigate over the 2026-10-29 window-dispatch-hardening certification closeout (the C8 witness in the origin row; the field-line shape is project lesson 32's re-witness)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the item carries a body-named single-surface fix (the seal-resolution reporting path - the staging validator's degraded-grading warning plus a parse-diagnostic detail feeding it) with no open design choice, no new dependency, no guard, lock, ledger, or state-schema change; the never-guard-bearing clause holds because the repair arm is the reporting surface only - parse_seal's fail-closed whole-file None stays byte-for-byte.

Origins:
- docs/history/backlog/2026-10-21-seal-landing-survival-review-residuals.md (residual C8)

Stage 1 roster: the singleton origin above; its Cluster sibling (landing-diagnostic-selects-foreign-plan) shares the landing-diagnostic surface family but carries its own defect and fix, so it stays outside these scope arms.

Urgency: low - the witnessed cost is one misdirected repair iteration per poisoned seal file (the validator's degraded warning reads identically for an unparsable file and a missing entry, so the first repair appended a seal instead of fixing the annotation grammar); annotations to existing seal blocks are rare edits, lesson 32's re-witness already documents the field-line shape, and the residual cost is diagnostic ambiguity only.

Scope arms:
- Reporting: the staging validator's seal-resolution warning (scripts/validate_review_staging.py, the "no certification seal entry resolves for round %d" emission) distinguishes the unparsable-file case (parse_seal returned None) from the absent-or-no-entry case, naming the seal file and the first offending line when derivable; the degraded-grading behavior for a resolvable-but-unresolvable-for-this-round shape is unchanged.
- Library detail: scripts/corrections_record.py parse_seal exposes the offending line to its caller without changing the fail-closed whole-file None contract (a side channel or exception field); the None contract itself is byte-preserved.
- Tests: the corrections/staging focused suites gain the poisoning case (a prose line inside a round block) asserting the new distinct warning; the existing degraded-grading warnings stay pinned.

Orientation: read the C8 witness in the origin row, then parse_seal in scripts/corrections_record.py (the line loop whose non-field, non-blank arm returns None for the whole file; the docstring's unparsable-marker contract), then the warning emission in scripts/validate_review_staging.py, then lesson 32's re-witness in docs/maintenance/development_lessons.md. Disk re-derivation at entry write: the non-field-line refusal arm exists at the tip by working grep and git grep (scripts/corrections_record.py:656), the warning text exists at the tip (scripts/validate_review_staging.py:4629), and the C8 line is present in the origin row's working tree.

Prompt: Using the ad-hoc backlog arm, land the distinct unparsable-file reporting per the scope arms; run the corrections and staging focused suites plus the em-dash added-lines gate and the public hygiene scan; no machinery is added, so the admission line below is the rejection record; mark the C8 residual fixed in the origin row (the row's other residuals stay open) with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section in the same change.

Rejected alternatives:
- Loosen parse_seal to skip malformed lines and parse the remainder (keep-and-widen): rejected - partial trust in a corrupt seal file could grade a certification against a stale entry; the fail-closed whole-file None is the parser's deliberate contract (scripts/corrections_record.py parse_seal docstring, the unparsable-marker clause)
- A standalone seal-file lint at authoring time (new machinery): rejected under the machinery admission protocol - no witnessed incident beyond the one diagnostic misdirection, the field-line rule is already documented (lesson 32's re-witness), and the lint's false-positive surface is every hand-edited seal ("no witnessed incident" of a corruption the lint would catch that the distinct warning would not)
- Silence the degraded-grading warning when the file is unparsable: rejected - the warning is load-bearing on the expected degradation path (seals that fail to resolve degrade to the exact-match rule and pass with a warning), and hiding it removes the signal that grading narrowed (evidence basis: docs/maintenance/development_lessons.md lesson 141)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the arms reshape one existing warning's text and expose a parse diagnostic; the gate-shaped alternative is rejected above with the missing-incident absence named.

## successor-dispatch-sha-echo-verify-reach

Added: 2026-10-29, learn + investigate over the 2026-10-29 interactive exec mandate closeout (the focused docs panel's second-producer residual; origin row below; the covering landing 35595ad5 added the duty and the consumer-side adjudication this entry extends to the second site)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the item carries a body-named single-surface fix (one clause at the successor-dispatch recording sentence in agents/skills/maintenance/template-execution.md), tracked skill text only, no new dependency, no state-schema or guard change, no machinery removal; the row's two named shapes (an inline echo-verify sentence vs a by-reference pointer) collapse to one under the repository guidelines' single-homing rule, so no open design choice remains.

Origins:
- docs/history/backlog/2026-10-29-dispatch-sha-second-recording-site.md

Stage 1 roster: the singleton origin above; no open sibling shares the dispatch-recording surface (the removed covering entry's other panel residual went to the review watchlist, not a row).

Urgency: low - the consumer side is already protected for any producer (the failure-cap conjunct's git-history adjudication names a phantom baseline a recording defect before failure credit is read), so the residual gap is prevention text at one rarely-exercised second site (successor-chained dispatches).

Scope arms:
- Single clause: the successor-dispatch duty's recording sentence in agents/skills/maintenance/template-execution.md ("the successor plan file's sha256 recorded at dispatch time") restates itself as a by-reference pointer to the Step 5/6 dispatch-recording conventions (the shape agents/skills/maintenance/decisions.md's chaining clause already uses, "per the Step 5 conventions"), carrying the echo-verify duty without duplicating its text.
- Gates: the maintenance pins suite beside the standard text gates (em-dash added-lines, public hygiene).

Orientation: the restated clause exists at the tip by working grep and git grep (agents/skills/maintenance/template-execution.md, one "recorded at dispatch time" hit each; introduced 867f8ed7e 2026-10-18, predating the duty); the duty exists at the tip (agents/skills/maintenance/scheduling.md, one "echo-verify" hit each, landed 35595ad5); the consumer adjudication exists at the tip (agents/skills/maintenance/failure-cap.md, one "recording defect" hit each).

Prompt: Using the ad-hoc backlog arm, land the by-reference pointer clause per the scope arms; run the pins suite and the standard text gates; delete the origin row per the covered-row rule and remove this entry's section in the same change with the EXEC-PROMPTS-PRUNE receipt line.

Rejected alternatives:
- Duplicate the full echo-verify sentence inline at the second site (keep-and-widen): rejected - duplicated producer-contract text drifts independently, and the by-reference form is the repo's established shape for a restated convention (evidence: the chaining clause's "per the Step 5 conventions" form in agents/skills/maintenance/decisions.md)
- A machine check that every recorded dispatch_plan_sha carries a same-turn echo witness (new machinery): rejected under the machinery admission protocol - no witnessed incident at this second site (the witnessed phantom baseline was the (idle)-dispatch site the landed duty already covers), the expected catch frequency is a successor dispatch that both skips the pointer and records an unverified sha, and the false-positive surface is every schema-valid historical entry ("no witnessed incident" at this site)
- Leave the clause as-is relying on the consumer-side adjudication: rejected - prevention absent at the site is the row's witnessed finding (the focused panel's unamended-second-recording-site pattern); the adjudication detects a phantom baseline only after a stand-down conjunct reads it

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the arms replace one restated sentence with a pointer; the machine-check alternative is rejected above with the missing-incident absence named.

## prune-audit-same-branch-receipt-rewrite-flag

Added: 2026-10-29, learn Step 1.9 witness + investigate over the 2026-10-29 exec-run session (the pick 1 landing's prune-audit flag; the composition practice is project lesson 301)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md): the item carries a body-named single-surface fix (one fixture reproduction plus the receipt-line class's excusal read in scripts/check_prompt_log_origins.py, ending in a recorded verdict) with no open design choice at entry time - the entry closes the design choice itself (reproduce first; a checker change only on a reproduced false positive), no new dependency, no guard, lock, ledger, or state-schema change; the never-guard-bearing clause holds because the diagnostic arm is read-only over the checker.

Origins:
- docs/history/backlog/2026-10-29-prune-audit-same-branch-receipt-rewrite-flag.md

Stage 1 roster: the singleton origin above; its Cluster sibling (2026-10-24-collateral-served-nul-origin-uncaught-valueerror) shares the checker surface but carries its own defect class (an uncaught ValueError in --collateral-served, not receipt-line flag semantics), so it stays outside these scope arms.

Urgency: low - the witnessed cost is one composition cycle per landing whose branch rewrites a receipt line mid-branch (one squash and an audit re-run); the audit behaved fail-closed (a flag costs a recomposition, never a lost receipt), the practice side is already landed (lesson 301), and the residual is the unresolved trigger question only.

Scope arms:
- Reproduction: a fixture branch adds a receipt-ledger line in one commit and rewrites its wording in a second; `scripts/check_prompt_log_origins.py --prune-audit --base` runs over it, and the flag's presence or absence is recorded against the excusal conditions in the receipt-line class (`_line_removals`, `newly_added_receipt_pairs`, `receipt_compare_slug`).
- Verdict: a reproduced flag on the same-commit re-add shape files the targeted excusal widening as its own follow-up (the fixing change carries the machinery admission fields); a clean run or a trigger traced to a different shape closes the row works-as-designed citing lesson 301's composition discipline.
- No checker edit inside this entry's own scope: the diagnostic is read-only; any widening lands separately with its own gates and panel.

Orientation: read the finding in the origin row, then the receipt-line removal class in scripts/check_prompt_log_origins.py (the pure receipt-line-deletion loop: the "retoken shape" comment, the `newly_added_receipt_pairs` excusal, and the RECEIPT-LINE-REMOVED-WITHOUT-WITNESS emission), then the promoting plan docs/history/plans/2026-10-28-pending-receipt-removal-audit-promotion.md (the correctness clause the excusal implements: deletions detected, later re-additions recognized; landed b6b0f7e21), then lesson 301 in docs/maintenance/development_lessons.md. Disk re-derivation at entry write: the flag class and the excusal exist at the tip by working grep and git grep, the promotion landing b6b0f7e21 exists and is dated 2026-10-29, and the origin row is present in the working tree and at HEAD.

Prompt: Using the ad-hoc backlog arm, run the reproduction and record the verdict per the scope arms; run the checker focused suite plus the em-dash added-lines gate and the public hygiene scan; no machinery is added, so the admission line below is the rejection record; delete the origin row per the covered-row rule (works-as-designed close) or mark it narrowed to the filed widening (reproduced-flag close) in the same change, with the EXEC-PROMPTS-PRUNE receipt line removing this entry's section.

Rejected alternatives:
- Widen the retoken excusal to same-branch introductions now, without the reproduction (keep-and-widen): rejected - the witnessed flag's precise trigger is not re-derived (the pre-squash branch commits are reflog-only), so the widening would edit a validator against an unverified shape, and an over-wide excusal masks real cross-commit receipt loss, the exact harm class the promotion formalized (evidence basis: docs/history/plans/2026-10-28-pending-receipt-removal-audit-promotion.md, the correctness clause)
- Remove the receipt-line removal class (remove): rejected - the class is the promoted arm of the witnessed same-day receipt-ledger losses that pre-registered its own promotion (docs/history/backlog/2026-10-28-pending-receipt-removal-warning-promotion.md, Status: covered; founding witnesses in the completed 2026-10-22 prune-audit row), so removal discards demonstrated protective value
- A pre-landing composition gate refusing land-worktree when branch deltas rewrite a receipt line (new machinery): rejected under the machinery admission protocol - one witnessed friction cycle, the practice already documented (lesson 301), and the false-positive surface is every legitimate mid-branch retoken ("no witnessed incident" of a loss the gate would prevent that the existing fail-closed flag does not)
- Rely on the net-diff view alone and drop the per-commit walk (remove): rejected - the per-commit walk is the promotion plan's own correctness layer (deletions detected per commit with one-for-one reconciliation), and the witnessed flag fired in its fail-closed direction, costing one recomposition rather than a lost receipt

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the arms are a read-only reproduction and a recorded verdict; the widening and gate-shaped alternatives are rejected above with the missing-incident absence named, and a reproduced-flag follow-up carries the four admission fields in its own fixing change.

## primary-rooted-orphan-done-manifest-drain

Added: 2026-10-30, learn+investigate over the window-dispatch-hardening resume-carrier session (origin row below)
Updated: 2026-11-01, learn Step 1.9 anchored re-investigation over the 2026-11-01 scheduler-turn drains (the witness-refused subclass scope arm and its rejected alternative below)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (agents/skills/maintenance/decisions.md), by the body-named single-surface-fix clause: the arm is a one-time bounded drain of runtime residue using only the existing remedy ladder (the classifier plus disposition-manifest, recover-manifest, finalize-manifest, and the boundary-side gate-removal), no open design choice (the adjudication recipe is canonical: development_lessons.md #45 root match plus the landed-work proof), no tracked-surface edit beyond the row deletion, no guard-bearing path, no new dependency, no machinery; the verdict survives the 2026-11-01 subclass witness because the witness-refused head is explicitly out of the arm's scope (scope arm below), keeping the drained set free of open design choices.

Origins:
- docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md

Stage 1 roster: the singleton origin above. The Stage 0 sweep found no open row sharing the orphan-manifest defect class: the nearest rows own different objects (2026-10-09-done-recursive-tmp-sweep-safety owns recursive-deletion safety; the gate-report-retention family owns report retention intervals), and the landed manifest-state classification plan owns the classifier, not the pool.

Urgency: low-medium - the witnessed cost is real but bounded: one primary done setup was blocked 2026-10-29 by the then-newest orphan and resolved through the printed remedy ladder within the same closeout; 43 orphan groups stand as of 2026-10-30 (10 primary-rooted, the class that surfaces to every future primary closeout whose marker chain reaches one).

Scope arms:
- Enumerate: re-derive the orphan set at run time with the classifier's group semantics (a run-id group is terminal when any of its files carries complete, adopted, or dispositioned); the 2026-10-30 count (43 groups, 10 primary-rooted) is orientation, not the worklist.
- Adjudicate per group: root match per development_lessons.md #45, holder liveness, worktree presence, and the landed-work probe (the run's owned paths at its start commit against the base branch history); disposition-manifest only for provably dead roots, exactly per its dead-root-only gate.
- Leave-in-place with a recorded reason for every live or unprovable group; a live holder's group is never touched.
- The persistent witness-refused head stays out of scope: `20261025T194856Z-75b095a82a7d` (dead root since 2026-10-25) refuses disposition-manifest on the deliverables witness (its owned plan path resolves through no witness arm), so the drain records it as park-for-operator (witness override adoption, missing-evidence supply, or a standing leave-in-place reason; the 2026-11-01 scheduler-turn witnesses and census are in the origin row) and spends no drain slot on it, per the tool's witness-first refusal behavior; an adoption-chain close is unavailable without a consuming adopter boundary. Census counts for this arm derive per development_lessons.md lesson 352 (the classifier's own three-field filter).
- Execution claims stay out of scope: that residue has its own stale-registration doctrine and lane.
- No machinery change of any kind: the drain uses the tools as they stand; the origin-row deletion is the only tracked-surface edit.

Orientation: read the origin row, then the classifier and remedy subcommands in scripts/done_sweep_gates_lib.py (classify_run_boundary, disposition-manifest, recover-manifest, finalize-manifest), the refusal-and-remedies site in scripts/done_run.sh setup, and development_lessons.md #45 for the live-root adjudication recipe. Disk re-derivation at entry write: the 2026-10-29 witness manifest carries its dispositioned record on disk (read back at write time) while git check-ignore confirms the whole manifest corpus is gitignored runtime state; the origin row exists in the working tree and at HEAD (3f66b26e1).

Prompt: Using the ad-hoc backlog arm, run the bounded drain per the scope arms (enumerate, adjudicate, disposition the provably dead, record the leaves), then delete the origin row per the covered-row rule with the EXEC-PROMPTS-PRUNE receipt line removing this entry's section in the same change; the public hygiene scan and the em-dash added-lines gate run over the run's changed tracked surfaces.

Rejected alternatives:
- An automated GC arm inside done setup (keep-and-widen the setup path): rejected under the machinery admission protocol - one witnessed friction block is the whole incident record, and a destructive sweep at setup time is the exact hazard class the recursive-tmp-sweep-safety row fences ("no witnessed incident" of residue harm beyond adjudication friction); the bounded human-adjudicated drain is the smaller arm (docs/history/plans/completed/2026-10-27-done-recursive-tmp-sweep-safety.md)
- Blanket-disposition every orphan past an age threshold (keep and narrow the pool by age): rejected - the dead-root-only gate exists for the witnessed live-root misadoption hazard, and age is not liveness (a hours-old group may hold a live session; development_lessons.md #45, the live-root classification)
- Widen disposition-manifest with a no-witness excusal arm for proven-dead roots (keep-and-widen the tool): rejected for this arm - the operator direction on the persistent head is owed and undecided (witness override adoption, missing-evidence supply, or a standing leave-in-place reason), and deciding a witness-override policy inside a drain run would be mid-lane gate editing, forbidden without a plan; witnessed 2026-11-01 in both scheduler turns (docs/history/backlog/2026-10-30-orphaned-done-run-manifest-pool.md)
- Drain the execution claims lane in the same run (widen scope): rejected - claims carry their own stale-registration doctrine with its own provably-dead bar and a fleet-wide blocking failure mode; mixing lanes doubles the blast radius of one misjudgment (docs/maintenance/development_lessons.md #224, the takeover liveness proof; #110, the claim ownership chain)
- Do nothing (keep): rejected - the witnessed block recurs at every primary closeout whose marker chain reaches an orphan, and the pool has grown monotonically since 2026-10-01 (the origin row's measurement)

Machinery admission: no gate, validator, lock, ledger, or ceremony is added; the drain is cleanup-shaped with existing tools, and the automation and age-threshold alternatives are rejected above with the missing-incident absence named.
## plan-readiness-deleted-files-path-vocabulary

Added: 2026-10-30, investigate pass over an origins-closure exec run (origin row below; fresh witness confirms the existence-check refusal)

Work-type verdict: exec-type; the remedy is a bounded validator-and-template edit with no open design choice: a planned-deletion marker in the plans `Files:` grammar recognized by `scripts/plan_readiness.py`'s existence check (check (c)) and coverage-warning leg, mirroring the existing `*(new)*` exemption.

Origins:
- docs/history/backlog/2026-10-30-plan-readiness-deleted-files-path-vocabulary.md

Urgency: medium - every future plan whose closure deletes a tracked file (origins closure, row removals) hits the same pre-round refusal after its task body lands and must improvise the same prose workaround; witnessed once 2026-10-30, cost one mid-run skill-gated plan repair.

Scope arms: a `*(deleted)*` marker exempting the existence check; the marker checked against the diff so a stale deletion record still fails; coverage-warning alignment; template documentation in the plans skill.

Orientation: read the existence check in scripts/plan_readiness.py (the Files-path loop and its `*(new)*` exemption), then the _plan_files_items grammar, then the witnessed run's repaired plan docs/history/plans/2026-10-25-review-plan-nonconvergence-disposition.md. The marker must stay a record of intent (the path must actually be deleted by the task's commit), never a silent escape from coverage.

Prompt: Implement the planned-deletion marker: extend the plans `Files:` grammar and `scripts/plan_readiness.py` so a `*(deleted)*` annotated path passes the existence check while a deletion annotation on a path the task's commits do not actually delete still fails; align the FILES-COVERAGE warning leg; add the marker to the plans template; focused validator selftest coverage for pass and stale-record refusal shapes; em-dash and hygiene gates; delete the origin row per the covered-row rule in the same change.

Rejected alternatives:
- Prose-only workaround as doctrine (keep-and-document): rejected - it was the witnessed remedy and it hides deletion intent from the validator's coverage checks (witness: the repaired Task 1 Files list)
- Exempt all Files paths from existence checking (remove): rejected - the check catches stale planned paths before implementation, demonstrated value across the plan corpus (witness: the existence check in scripts/plan_readiness.py)
- A separate Deletions: section (new grammar): rejected - duplicates the Files grammar's path-token machinery for one marker's worth of value; the marker rides the existing list shape (witness: the _plan_files_items grammar in scripts/plan_readiness.py)

Machinery admission: validator edit only, no new gate; the marker narrows a false-positive refusal class (one witnessed catch, the workaround as false-positive cost), sunset with the validator's own review cycle.

## review-plan-fresh-review-route-stop

Added: 2026-10-30, learn over the reauthorization-disposition execution (Task 1 disposition record landed on the run branch)

Work-type verdict: ad-hoc-able by the single-surface-fix clause: the witnessed defect is a completed execution noncompliance whose owning clauses were verified to already close the route; the residual is a recorded incident, not a machinery gap.

Origins:
- docs/history/plans/completed/2026-10-26-authoring-resume-after-operator-reauthorization.md (Task 1 disposition record)

Urgency: low - the clauses verified correct at the cited sites; a repeat would be a fresh noncompliance instance, already covered by Blocker recovery's record-and-continue duty.

Scope arms: none beyond the landed record; no skill edit, no validator, no gate.

Orientation: read the Task 1 disposition record in the completed plan, then the four owning clauses it cites (maintenance decisions.md Blocker recovery; review-reconciliation SKILL.md section 4; review-plan SKILL.md Step 5 and Step 2 launch precondition).

Prompt: no dispatch; the record itself is the artifact. If a second stop-after-authorization instance is witnessed against these same clauses, reopen with the new witness.

Rejected alternatives:
- Add a clarification clause (edit): rejected by the plan's own Task 2 gate - no proven gap, and the three surfaces already direct the authorized route (witness: docs/history/plans/completed/2026-10-26-authoring-resume-after-operator-reauthorization.md)
- File a standalone backlog row (duplicate): rejected - the disposition record in the completed plan is the durable home and the origin row is already closed covered (witness: docs/history/plans/completed/2026-10-26-authoring-resume-after-operator-reauthorization.md)

Machinery admission: nothing added.

## reauthorization-plan-annotation-precision-lows

Added: 2026-10-30, investigate over the session that executed the authoring-resume-after-operator-reauthorization plan (Phase 3 r1 review deferred the three Lows into the origin row)

Work-type verdict: ad-hoc-able by the single-surface-fix clause: the remedy edits annotation prose in one completed plan file and one backlog row, no code, skill, or validator surface.

Origins:
- docs/history/backlog/2026-10-30-reauthorization-plan-annotation-precision-lows.md

Urgency: low - no behavior surface; the cost is a history reader mis-resolving the checkbox's literal `(<completed plan path>)` + `Covered by:` shape against the attested row-convention citation, and the closure-of-record ambiguity between a subject-only branch commit and the true closure commit.

Scope arms: tighten Task 2's verify-annotations in the completed plan to cite the attested convention (living-path Status citation, no Covered-by line) explicitly beside the literal shape; name the PRUNE-receipt commit (893566f95) as the peer prune the "no other row or catalog edits" wording did not enumerate; annotate the subject-only closure-subject branch commit (daed83b02) as carrying no closure edit with the closure of record named.

Orientation: read the origin row's three deferred Lows and its durable witness (.ai-playbook/reviews/2026-10-30-authoring-resume-after-operator-reauthorization-code-review-r1.md), then the Task 2 disposition record in docs/history/plans/completed/2026-10-26-authoring-resume-after-operator-reauthorization.md; the tighten lands only "when next touching the archived plan or the row" per the row's own remedy clause, so the dispatch may record a defer disposition instead of editing if no touch is due.

Rejected alternatives:
- Add a validator enforcing the literal checkbox shape across completed plans (machinery arm): rejected - one witnessed instance, no recurring catch, and the attested convention deliberately differs from the literal shape, so enforcement would codify the wrong target; admission test fails ("no witnessed incident" beyond the single review note)
- Leave the annotations as written (remove/do-nothing): rejected - the reviewer-attested gap is exactly that a literal-shape reader cannot reach the attested basis; the tightening is the row's own suggested remedy and costs nothing (witness: docs/history/backlog/2026-10-30-reauthorization-plan-annotation-precision-lows.md)
- Retroactive commit-subject rewrite to move the closure subject onto the true closure commit (history arm): rejected - rewrites landed history for a readability nit the annotation resolves at zero risk (witness: docs/history/backlog/2026-10-30-reauthorization-plan-annotation-precision-lows.md)

Machinery admission: nothing added; the recommended arm removes ambiguity in existing prose.

## template-split-residual-pointers-and-labels

Added: 2026-10-31, investigate over the claim-procedure-pointer execution run's backlogged review residuals (operator-directed learn+investigate over the session)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): body-named single-surface docs and registry-text corrections - reword one machinery-registry note's blueprint citation, delete one dead test constant, add module paths to one dispatch-slice sentence, correct one stale field-line count, and reconcile one duty label with its owning module's wording - no code behavior, no open design choice, no new dependency, no gate or state change; every item is a pointer or count accuracy fix recorded on its origin row.

Origins:
- docs/history/backlog/2026-10-31-template-split-residual-pointers.md
- docs/history/backlog/2026-10-31-pre-execution-re-verification-label-mismatch.md

Urgency: medium - all five residuals are reference-accuracy defects introduced by the 2026-10-10 maintenance module split (git log -S witness: the split plan's Task 1 moved the operative paragraphs byte-verbatim); each one sends a reader or a deciding turn to a file that does not contain the cited procedure, but none blocks a gate today (the pins suite freezes only the one delegation sentence, already re-aimed by the covering landing 3f47241c5).

Scope arms: the registry-note reword and the dead-constant deletion as one scripts-scoped change (registry row plus `scripts/test_authoring_plans_liveness.py`), then the scheduling.md path-anchor and field-line count corrections and the state-file.md label reconciliation as one maintenance-docs change; re-run `bash scripts/check_maintenance_pins.sh` and the affected test files per change and expect only the tracked baseline red (`review-plan reads attempt state after resume`, own backlog row).

Orientation: `scripts/machinery_registry.json`, `scripts/test_authoring_plans_liveness.py`, `agents/skills/maintenance/scheduling.md`, `agents/skills/maintenance/state-file.md`, `agents/skills/maintenance/template-authoring.md`, and the two origin rows' per-item witnesses; the mechanism history lives in `docs/history/plans/completed/2026-10-10-maintenance-skill-size-refactor.md`.

Rejected alternatives:
- Fix the residuals in the covering run itself: rejected - all five predate that run and sit outside its plan's audited 10-file scope, so in-task fixes would have widened the boundary commit and hidden the deferral; durable rows were the sanctioned capture (docs/history/backlog/2026-10-31-template-split-residual-pointers.md)
- Widen the pins suite to freeze each corrected sentence: rejected on the machinery-admission axis - no witnessed incident of a corrected sentence re-drifting, the corrections are one-time accuracy fixes, and adding pins would price a permanent maintenance cost for no catch (no witnessed incident; evidence basis: `scripts/check_maintenance_pins.sh` currently freezes none of the affected sentences and no gate reads them)
- Leave the label mismatch unfixed and grep-train readers instead: rejected - the label is the referencing docs' own vocabulary, so renaming the label in the referencing text to the owning module's wording is a two-file edit with no behavioral risk (docs/history/backlog/2026-10-31-pre-execution-re-verification-label-mismatch.md)

Standing pre-authorization: the operator's standing maintenance exec mandate covers this entry's ad-hoc run; no contested recommendation stands.

## task-primary-capability-request-attach-disjunct

Added: 2026-10-31, learn/investigate over the task-primary-worktree-archive-refusal execute-plan session (operator-directed over the 03:00 WET one-shot run, landed b7b6afa41)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named single-clause wording widening in one skill file's already-landed paragraph - widen the capability request in `agents/skills/execute-plan/worktree-first.md` step 6's archival shape from "detach or rebind with a checkable postcondition" to also name unmanaged-primary-checkout attach as the second acceptable disjunct, paid from same-paragraph slack per the anti-growth rules - no code surface, no open design choice, no new dependency, no gate or state change.

Origins:
- docs/history/backlog/2026-10-31-task-primary-capability-request-attach-disjunct.md

Urgency: low - the operative text is narrower than, not contradictory to, the covering run's Task 1 disposition of record; the adjacent limit sentence ("attach refuses unmanaged checkouts") already keeps the gap inventory complete, so nothing misleads a reader today; the widening rides the next edit of the same paragraph.

Scope arms: one bounded docs-only edit to the step-6 archival-shape paragraph: insert the attach disjunct into the capability-request clause with a checkable postcondition named for it, byte-balanced within the paragraph; re-run the affected pins/test class after the edit and expect only tracked baseline red; the vendored/runtime twins land in the same change or leave a tracked landing path.

Orientation: `agents/skills/execute-plan/worktree-first.md` step 6 (the archival shape sentence of record, landed in b7b6afa41 together with the peer gate-removal wording); the origin row; docs/history/plans/completed/2026-10-27-task-primary-worktree-archive-refusal.md (the Task 1 disposition naming both disjuncts).

Rejected alternatives:
- Leave the skill text as-is and let the completed plan's disposition carry the disjunct: rejected on the remove-or-keep axis - the skill file is the operative lifecycle source the next executor reads, so a capability request narrower than the recorded evidence is the exact fidelity gap the covering plan's review targeted (witness: the origin row's problem statement; agents/skills/execute-plan/worktree-first.md step 6, verified by grep at HEAD)
- Fold the widening into the covering run's landing itself: rejected at review time to avoid a third fold-and-review cycle for a non-blocking fidelity item; the durable row plus this entry is the sanctioned deferral shape (docs/history/backlog/2026-10-31-task-primary-capability-request-attach-disjunct.md, Alternatives)
- Remove the "attach refuses unmanaged checkouts" limit sentence to resolve the tension by deletion: rejected - the sentence is a true capability statement of the app's current surface and deleting it would hollow the gap inventory the capability request depends on for context (witness: the paragraph's own attested operation list at `agents/skills/execute-plan/worktree-first.md` step 6)

Machinery admission: nothing added; the recommended arm removes no gate and adds none.

Disk re-derivation at the entry's write (2026-10-31): the origin row exists in the working tree and at HEAD (filesystem probe + `git cat-file -e`); the operative clause "detach or rebind with a checkable postcondition" and the limit sentence "attach refuses unmanaged checkouts" confirmed by grep at HEAD in `agents/skills/execute-plan/worktree-first.md`.

## lesson-139-empty-set-remedy-refresh

Added: 2026-10-31, learn/investigate over the gate-removal-empty-owned-set-remedy execute-plan run (landed 790096fcb)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a one-sentence corpus refresh in `docs/maintenance/development_lessons.md` lesson #139 - reword the remedy clause to match the gate's landed two-input remedy line and re-anchor the certified-plan caveat to the claims path - no code surface, no open design choice, no gate or state change.

Origins:
- docs/history/backlog/2026-10-31-lesson-139-empty-set-remedy-refresh.md

Urgency: low-medium - the corpus currently contradicts the gate's own printed remedy: lesson #139 says the only remedy is a `--claims` file and forbids a header edit, while the landed gate (`_GATE_EMPTY_SET_REMEDY_LINE` in `scripts/worktree_closeout_migrate.py`, printed at the empty-owned-set refusal) offers the header citation as the first attainable input; a stuck run following the lesson over the printed line mis-prices a legal repair.

Scope arms: one bounded docs-only edit to lesson #139's Rule sentence: name both attainable inputs exactly as the gate prints them (a `Plan review record:`/`Plan review:` header citation, or a `--claims` file listing review-record paths), and keep the digest caveat scoped to digest-bound certified plans where the claims path is the safe option; re-run the maintenance pins script after the edit and expect only tracked baseline red; the origin row is deleted per the covered-row rule in the same change with the EXEC-PROMPTS-PRUNE receipt line, removing this entry's section.

Orientation: `docs/maintenance/development_lessons.md` lesson #139 (Rule sentence), `_GATE_EMPTY_SET_REMEDY_LINE` and its print site in `scripts/worktree_closeout_migrate.py` (disk re-derivation at write time), the covering plan `docs/history/plans/completed/2026-10-27-gate-removal-empty-owned-set-remedy.md`, and the origin row.

Rejected alternatives:
- Refresh the lesson inside the covering run's own landing: rejected - the row was filed by that run's intermediate review as a deferred Low, and folding a corpus edit into the landing would have widened the audited boundary commit; the row-plus-entry is the sanctioned deferral shape (docs/history/backlog/2026-10-31-lesson-139-empty-set-remedy-refresh.md, Origin line)
- Pin the lesson's remedy sentence in the maintenance pins suite so it cannot re-drift: rejected on the machinery-admission axis - no witnessed incident of a refreshed lesson re-drifting, the refresh is a one-time accuracy fix, and a pin would price permanent maintenance for no catch (no witnessed incident; evidence basis: `scripts/check_maintenance_pins.sh` freezes none of lesson #139's sentences)
- Delete lesson #139 and let the gate's printed line be the single source: rejected on the remove-or-keep axis - the lesson carries the post-pass teardown verification rule and the printed-step ownership routing, which the gate does not print; deleting it would orphan that guidance (docs/maintenance/development_lessons.md lesson #139, Rule + Why)

Machinery admission: nothing added; the recommended arm is corpus prose; the pins alternative is rejected above with the missing-incident absence named.

Standing pre-authorization: the operator's standing maintenance exec mandate covers this entry's ad-hoc run; no contested recommendation stands.

Disk re-derivation at the entry's write (2026-10-31): the origin row exists in the working tree and at HEAD (filesystem cat + `git cat-file -e`); lesson #139's "empty owned set" text confirmed at HEAD by `git grep` (2 hits); the gate's two-input remedy line confirmed at HEAD by `git grep` in `scripts/worktree_closeout_migrate.py` (1 hit).

## boundary-mirror-transfer-in-gap-lesson-329

Added: 2026-10-31, learn/investigate over the 02:00 WET one-shot execute-plan run (teardown-staging-record-mirror, landed 374f75cfa)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the witnessed defect is already remedied by the durable record - lesson #329 in `docs/maintenance/development_lessons.md` (landed 5736d2449) captures the mechanism, trigger, rule, and witness - so no machinery, code, or skill-text surface remains; the residual is the lesson itself plus this entry as the second-witness dispatch marker.

Origins:
- docs/maintenance/development_lessons.md (lesson #329, Transfer Session Logs Into the Run Worktree Before Any Boundary Mirror)

Urgency: low - the rule is captured and the run's own remedy (copying the session dir into the worktree before each boundary mirror) cleared the leg on first retry every time; the only cost is the per-boundary first-attempt exit-1 noise, which the lesson's Rule sentence tells future runs to avoid up front.

Scope arms: none beyond the landed lesson; no skill edit, no script change, no gate. The Phase 0 transfer-in instruction already names the canonical transfer (Worktree-first standard, Transfer-in implementation); the lesson operationalizes it for the session directory specifically.

Orientation: `docs/maintenance/development_lessons.md` lesson #329; `scripts/worktree_closeout_migrate.py` `boundary-mirror` (worktree-side source reads); the Worktree-first standard's Transfer-in implementation (the canonical transfer the lesson points at); the sibling cluster row `docs/history/backlog/2026-10-15-execute-plan-closeout-remedy-mirror-wording.md` (shared boundary-mirror wording surface, distinct defect).

Prompt: no dispatch; the lesson is the artifact. If a future run witnesses the same all-paths-missing first mirror attempt despite the lesson's rule, reopen with the new witness.

Rejected alternatives:
- Teach `boundary-mirror` to fall back to primary-side sources when the worktree copy is missing: rejected on the remove-or-keep axis - the helper's worktree-side read is the identity bound that keeps receipts tied to the run worktree, and a silent fallback would mask the transfer-in gap the lesson exists to close (witness: the receipt identity binding in `scripts/worktree_closeout_migrate.py`, verified by grep at HEAD)
- File a backlog row for a Phase 0 transfer-in enforcement gate: rejected on the machinery-admission axis - no witnessed incident of a run proceeding past a failed mirror with data loss (every first attempt here was repaired within the boundary and receipts landed on retry), so no admission test passes (no witnessed incident; evidence basis: the run's manifest rows in `.ai-playbook` and lesson #329's Why)
- Fold the lesson into the Worktree-first standard's Transfer-in paragraph instead of the lessons corpus: rejected - the standard already owns the canonical transfer duty and the corpus is where per-mechanics incident witnesses live; duplicating the operational detail in operative skill text would grow the skill without a new rule (witness: the Transfer-in implementation paragraph in `agents/skills/execute-plan/worktree-first.md`)

Machinery admission: nothing added; both machinery-shaped arms are rejected above with the missing-incident absence named.

Disk re-derivation at the entry's write (2026-10-31): lesson #329 exists in the working tree and at HEAD (filesystem probe + `git cat-file -e 5736d2449:docs/maintenance/development_lessons.md`); the receipt identity binding confirmed in `scripts/worktree_closeout_migrate.py` by `git grep` at HEAD; the sibling row exists in the working tree and at HEAD (filesystem probe + `git cat-file -e`).

## docs-branch-floor-review-lessons-334-335

Added: 2026-10-31, learn/investigate over the interactive $maintenance exec run (docs-branch-supported-python-runtime, landed b3dcd1f62)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): both witnessed defects are already remedied by durable records - lesson #334 (bash octal `10#` version arithmetic, landed e6c09729e) and lesson #335 (author validator-valid review pairs from a passing twin) in `docs/maintenance/development_lessons.md` capture mechanism, trigger, rule, and witness - so no machinery, code, or skill-text surface remains; the residual is this entry as the second-witness dispatch marker, and the run's two non-blocking finding classes ride their own backlog rows (`docs/history/backlog/2026-10-31-docs-branch-floor-review-residuals.md`, `docs/history/backlog/2026-10-31-docs-branch-floor-doc-polish.md`).

Origins:
- docs/maintenance/development_lessons.md (lessons #334, #335)
- scripts/docs_branch_sync.sh (below-floor preflight, landed b3dcd1f62; the octal-degrade witness surface)

Re-witnesses: lesson #35 (lock exports die at the tool-call boundary) re-witnessed by the same run's landing - an acquire in one shell invocation left the next invocation's `land-worktree` refusing on missing `MERGE_LOCK_DIR`, and the abandoned own hold needed `merge-stale-clean` before the single-invocation acquire-land-release retry passed.

Urgency: low - both lessons are captured and landed; the run's own remedies cleared every gate on retry; residual cost is validator round-trip noise for future record authors, which lesson #335's Rule sentence collapses.

Scope arms: none beyond the landed lessons; no skill edit, no script change, no gate. The review-staging skill already owns the scaffold-first recipe (its SKILL.md drafting step); lesson #335 operationalizes it for the exec-record family and the mint key name.

Orientation: `docs/maintenance/development_lessons.md` lessons #334/#335; `scripts/validate_review_staging.py` `--scaffold`/`--hard` (the fence set that produced the round-trips); `scripts/review_usage_capture.py mint` (the `minted_at_ms` key); `scripts/docs_branch_sync.sh` preflight (the octal witness surface); the two backlog rows above (the deferred Low findings' durable home).

Prompt: no dispatch; the lessons are the artifacts. If a future run witnesses a zero-padded version component reaching production output, or another multi-round ERROR loop staging a record whose family already has a passing twin, reopen with the new witness.

Rejected alternatives:
- Fix BC-2 (octal `10#`) in the run instead of backlogging: rejected on the off-plan-findings axis - it was a non-blocking Low outside the plan's must-fix scope, and folding it would have invalidated the blocking-clean r1 digest and forced an r2 witnessed in the r1 record's calibration; the record lives under `.ai-playbook/reviews/2026-10-31-docs-branch-supported-python-runtime-code-review-r1.md` beside plan docs/history/plans/completed/2026-10-28-docs-branch-supported-python-runtime.md
- Backfill the archive-egress exec record by editing the landing message with `--ack-egress`: rejected - the operator had not directed that specific archive in-turn, so the acked-egress exception did not apply; the completion-record leg was the sanctioned evidence route and passed on retry (witness: the guard's sanctioned-exits text in the landing attempt output; `scripts/reverse_squash_guard.py` check-archive)
- Widen the review panel to a full lens set for the two-task plan: rejected on the budget-proportionality axis - the declared complexity was small, and the focused two-lens panel returned blocking-clean on the first round, witnessed in the r1 record's ### Panel counts beside plan docs/history/plans/completed/2026-10-28-docs-branch-supported-python-runtime.md

Machinery admission: nothing added; all machinery-shaped arms are rejected above with the missing-incident absence named (no witnessed incident of a blocking finding missed by the focused panel, nor of a zero-padded component reaching production output).

Disk re-derivation at the entry's write (2026-10-31): both backlog rows exist in the working tree and at HEAD (filesystem cat + `git cat-file -e`); lesson #334 confirmed at HEAD by `git grep` (1 hit); lesson #335 confirmed in the working tree at `## 335.` (filesystem probe; committed in the same turn's learn commit e6c-class, verified by `git log -1` before this write); the landed commit `b3dcd1f62` verified via `git log --oneline -1` at main.

## plan-doc-evidence-pointer-discrimination

Added: 2026-10-31, learn+investigate over the session-channel-zcode-runtime-derivation-empty execution run (anchored on the run's two backlogged Phase 3 rows)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): both origins name bounded guidance/text fixes with the shapes already prescribed in the rows (a house-style pass over plan-header review-series citations; a discriminating-needle rewrite of one plan family's Validation Commands or a plans-skill guidance tightening) - no open design choice, no new machinery, no guard or schema change; the second origin's option (a) spans are already rg-verified against the landed docs.

Origins:
- docs/history/backlog/2026-10-31-plan-review-record-glob-infix.md
- docs/history/backlog/2026-10-31-plan-validation-grep-needles.md

Urgency: low - both defects are informational today: the readiness gate locates review records by slug logic rather than the header glob, and the covering run completed with the doc paths additionally pinned by a discriminating selftest (37 arms), so a reader or a rerun is misled only in the narrow shapes the rows name; the cost recurs per new plan, not per existing one.

Scope arms: one bounded docs-and-guidance session: (1) settle the plan-header review-series citation house style together for both named shapes - the run-id infix (or the plans skill resolving a dateless citation itself) and the snapshot-exclusion shape (a dateless glob matches the `.backup-20261030T*` twins beside the genuine records), and normalize the two sibling plans the glob-infix row names; the citation form the closeout series primitive actually recognizes is the tokenless `*-plan-review-<slug>-r*.md` (optional `-p<8hex>` infix), witnessed by the landing-day citation fix e160db2d6 after a literal `-p*` infix form reported a present series missing; (2) reword the covering plan family's doc-path Validation Commands to the per-file discriminating spans option (a) the grep-needles row already verified, or tighten the plans skill's Validation Commands guidance so must-fix doc paths get non-pre-existing needles by construction; the family's plan is archived, so the digest-churn concern that parked the row no longer applies.

Orientation: both origin rows whole; docs/maintenance/development_lessons.md lessons 69 (derive a downstream match pattern from on-disk names, third witness 2026-10-31) and 335 (author a validator-valid review pair from a passing twin); the closeout series primitive in scripts/worktree_closeout_migrate.py `_series_members`; the archived plan docs/history/plans/completed/2026-10-30-session-channel-zcode-runtime-derivation-empty.md.

Rejected alternatives:
- Add a validator gate that checks every plan header's review-series citation against disk at readiness time: rejected for missing machinery admission - the witnessed catches (the landing-day gate-removal refusal and the informational glob mismatch) were both caught by existing machinery at zero added-gate cost and remedied citation-only, and a readiness-time glob validator's false-positive cost (churning plan digests mid-execution, the exact concern that parked the glob-infix row) is priced in the row itself (evidence basis: docs/history/backlog/2026-10-31-plan-review-record-glob-infix.md; docs/maintenance/development_lessons.md lesson 69).
- Fix the two sibling plans' header globs inside this investigation: rejected - the skill ends at the log entry and the rows' own remedy shape (a house-style pass) covers them with the infix-and-snapshot shape settled once rather than twice (evidence basis: the sibling paths named in docs/history/backlog/2026-10-31-plan-review-record-glob-infix.md)
- Retro-edit the archived plan's Validation Commands as part of the covering run: rejected on the record at capture time - the certified plan digest churned mid-run would have invalidated the executing review chain's binding; the row was the sanctioned capture (evidence basis: docs/history/backlog/2026-10-31-plan-validation-grep-needles.md, Why-not-fixed-now paragraph)

Machinery admission: nothing added; the machinery-shaped arm is rejected above with the missing-incident absence named (no witnessed incident of a readiness failure caused by an unchecked header citation; both catches rode existing gates).

## hard-mode-clause-pointer-residual-fix-trio

Added: 2026-10-31, learn+investigate over the hard-mode-clause-pointer-residuals exec closeout session (carrier-fired resume session; run landed a5024b396)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): all three origins name bounded, body-prescribed fixes to the freshly landed clause-pointer surface in `scripts/validate_review_staging.py` and `scripts/check_maintenance_pins.sh` - re-case one dead marker and re-derive its pin probe, add leader rows with byte-real pins from enumerated emit sites, sharpen a check's failure diagnostics, harden one `python3 -` herestring invocation; no open design choice, no new dependency, no new machinery (all removal/narrowing or existing-family extension), no gate or state change.

Origins:
- docs/history/backlog/2026-10-31-witness-ledger-pointer-marker-case-dead.md
- docs/history/backlog/2026-10-31-clause-pointer-residual-under-routing-families.md
- docs/history/backlog/2026-10-31-clause-pointer-r2-residual-improvements.md

Urgency: medium - the landed state routes a handful of real ERROR lines to the bare skill pointer or a wrong-but-existing section (advisory print-layer only, pinned behavior unaffected), and every future table edit pays the unenforced-invariant cost the r2 panel named; the fixes are each one row or one assertion.

Scope arms: one bounded validator-and-pins session: (1) re-case the `witness ledger` marker to the real emission prefix and re-derive its selftest probe from the emit site (respect the `post-fix round` ordering caveat); (2) add leader rows from the residual rows' enumerated families (`required top-level field` ahead of `source_digest`, the COVERAGE date-fence / hyphenated mint-pair / freshness Metadata variants, the full-panel composition siblings, a routing-neutral `severity disagrees` row) each with a byte-real pin; (3) make the set-equality failure diagnostic symmetric (both set differences plus counts); (4) harden the import-based live-count herestring against cwd stdlib shadowing (`-P`/`-I` or spec_from_file_location); (5) align the predicate docstring/comment precision notes from the r2 rows. Run the selftest and pins suite fresh; the extractor completeness assertion must stay green both directions.

Orientation: the three origin rows whole; `SKILL_CLAUSE_POINTERS` and `_skill_clause_pointer` in `scripts/validate_review_staging.py` (landed a5024b396); the r2 review record `.ai-playbook/reviews/2026-10-31-hard-mode-clause-pointer-residuals-code-review-r2.md` (findings F1-F7 carry the per-finding evidence).

Rejected alternatives:
- Fold the residuals into the run's own landing: rejected at review time - r2 certified clean with zero blocking findings, and the certification-residual routing requires durable backlog capture rather than a third review round; the r1 fix round already took the blocking share; witness: the r2 record's Summary verdict ready=yes and the r2-residual row's creation in the same change, .ai-playbook/reviews/2026-10-31-hard-mode-clause-pointer-residuals-code-review-r2.md, landed a5024b396
- Remove the quote-position anchoring to eliminate the quoted-only under-capture class: rejected on the remove-or-keep axis - the anchoring kills the C3 misroute class with mutation-proven pins and one uniform rule; removing it reintroduces the witnessed misroute to fix an advisory-only under-fire (witness: lesson in the r1 record F1, `docs/history/backlog/2026-10-31-clause-pointer-r2-residual-improvements.md` last bullet).
- Add `source_digest` to the quoted-template exemption set instead of a leader row: rejected - the exemption matches anywhere and would widen the misroute surface the r2 risk lens measured; the leader row routes the whole missing/null family by first-match-wins without reopening that window; witness: the r2 record's F1 Comment, probe-backed, .ai-playbook/reviews/2026-10-31-hard-mode-clause-pointer-residuals-code-review-r2.md, landed a5024b396

## execute-plan-review-panel-selection-reference-repoint

Added: 2026-10-31, learn+investigate over the same closeout session (Step 1.8 skill-usage issue capture)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a bounded three-reference re-point in one skill file - `agents/skills/execute-plan/SKILL.md` names `review-panel-selection.md` bare in three operative places while the real file lives at `agents/skills/review-agents/review-panel-selection.md`; no code surface, no open design choice, no new machinery.

Origins:
- docs/history/backlog/2026-10-31-execute-plan-missing-review-panel-selection.md

Urgency: medium - every execute-plan run's Step 1.2b and Phase 3 worker-set resolution silently falls back to deriving tiers when the reference does not resolve, so the tier-selection contract is undiscoverable at the moment of use and is re-derived (uncontrolled) run after run.

Scope arms: one docs-only edit: re-point the three references at the review-agents path in the form the skill set uses for cross-skill pointers, verify the linked sections exist (Per-task intermediate review selection; Targeted follow-ups), and confirm no other bare reference to the file remains in the executing skill set.

Orientation: the origin row whole; `agents/skills/execute-plan/SKILL.md` Step 1.2b, the Residual-acceptance exit row, and Phase 3 Step 3.1; `agents/skills/review-agents/review-panel-selection.md` (the real home, verified on disk).

Rejected alternatives:
- Copy `review-panel-selection.md` into `agents/skills/execute-plan/`: rejected - a duplicated file drifts from the review-agents home and violates the single-home rule for cross-cutting skill modules; the pointer re-point is the one-change fix; witness: the file exists and is maintained there, agents/skills/review-agents/review-panel-selection.md
- Inline the tier-selection rules into execute-plan's SKILL.md: rejected on the cost axis - the selection contract is shared across review consumers and inlining duplicates it into a second home with two update sites; witness: the file's shared-consumer structure at agents/skills/review-agents/review-panel-selection.md
- Leave the bare references and rely on executing sessions to derive tiers: rejected - the fallback is exactly the uncontrolled derivation this row witnessed twice in one run (witness: the origin row's problem statement).

## two-owner-race-corpus-residuals

Added: 2026-10-31, learn/investigate over the interactive $maintenance exec run (plan-authoring-stand-down-before-charter, landed 721e6cc21)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the race mechanics are captured by lessons #339 (discharge your armed resume carrier), #340 (record findings before a pause leg), #341 (verify the diff surface after a delegated reviewer returns), and #342 (an errored hand-back is liveness-unknown) - so no machinery, code, or skill-text surface remains; the residual is the corpus defect the race itself produced: the lessons corpus now carries two distinct lessons numbered `## 337.` (the run's fixture-derivation lesson and a peer's session-dir baseline lesson, landed concurrently by the two owners of the race), which breaks the fresh-read numbering rule (next number = max existing + 1) and every `#337` cross-reference's disambiguation.

Origins:
- docs/maintenance/development_lessons.md (the duplicate `## 337.` heading pair; verify by grep)

Urgency: medium - every future lesson numbers from a max() that now has a tie, and citation text like "lesson #337" is ambiguous until renumbered; the defect self-perpetuates with each new corpus write.

Scope arms: renumber the later `## 337.` heading (the session-dir baseline lesson at the higher line number) to the next free number with a recorded renumber note in its body, keeping the earlier #337 stable; grep and retarget every live `#337` citation that refers to the renumbered lesson; no machinery, no validator (the corpus gate already owns concision checks; a numbering-uniqueness gate is rejected below).

Orientation: docs/maintenance/development_lessons.md (both `## 337.` headings and their Why cross-references); lessons #339/#340/#341/#342 (the race's recorded sides); the lessons corpus numbering rule in agents/skills/learn/step-1-extract.md (fresh read, max + 1).

Prompt: in one ad-hoc closeout, renumber the duplicate lesson (rename the later `## 337.` heading to the next free number, add one line recording the renumber and the two-owner race witness), grep the corpus and repo for `#337` citations and retarget only those whose subject matches the renumbered lesson, run the lessons-corpus gates, and land in one commit. Delete this entry with its `EXEC-PROMPTS-PRUNE` receipt in the same landing.

Rejected alternatives:
- Add a numbering-uniqueness validator gate: rejected on the machinery-admission axis - no witnessed incident of the duplicate surviving a fresh-read numbering pass by an attentive writer; the defect was produced by the two-owner race itself (two sessions numbering concurrently), which the race lessons already address at the root, so a new blocker would price a one-off collision class (evidence basis: the duplicate's git history, both landed within minutes of each other by the race's two owners)
- Leave both as #337 and disambiguate citations by title: rejected - the corpus rule derives the next number from the max heading number, and a permanent tie makes every future `#337` citation ambiguous, which is worse than a one-line renumber (evidence basis: docs/maintenance/development_lessons.md `## 337.` duplicate headings and the fresh-read max-plus-one rule in agents/skills/learn/step-1-extract.md)

Machinery admission: nothing added; the validator arm is rejected above with the missing-incident absence named.

Disk re-derivation at the entry's write (2026-10-31): the duplicate confirmed by `grep -c '^## 337\.'` = 2 on the working tree; lessons #339-#342 confirmed present by grep; the run's landing commit 721e6cc21 and registry rider c63419139 confirmed on main via `git log`.

## corrections-record-operand-recursion-containment

Added: 2026-10-31, investigate over the interactive exec session that landed corrections-chain-recursion-refusal-and-pins (learn second witnesses already landed 56a84206e; anchored pass on the session's filed row)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): the origin row names a bounded, body-prescribed fix to one script and its test file - widening three except tuples and moving one `json.dumps` inside an existing guard in `scripts/corrections_record.py`, plus refusal-mapping tests mirroring the seven-test shape the sibling plan landed; no open design choice beyond the row's named MemoryError-arm decision, no new dependency, no gate, validator, lock, or state-schema change.

Origins:
- docs/history/backlog/2026-10-31-corrections-record-operand-recursion-unguarded.md

Urgency: low - the unguarded sites are fail-closed by construction (a crash never grants authority), the trigger needs write access to the primary checkout and an adversarially deep operand, and the residual is a traceback instead of the established named refusal family.

Scope arms: one bounded script-and-test session over `scripts/corrections_record.py` and `scripts/test_corrections_record.py`: add `RecursionError` to the two parse except tuples (`load_corrections`, `append_corrections`) AND to the append guard's tuple, move the append `dumps` inside that guard, map failures to the existing named refusal legs, and pin with tests mirroring the deep-state/serialization shape of the sibling plan; the same session decides the row's recorded MemoryError arm (widen the writer guard's class set, or record the indent-amplification as an accepted writer-contract risk) and, if touching the refusal text, renders the "not writable" trailing cause only for the OSError family per the row's false-prefix residual.

Orientation: the origin row whole; the sibling plan `docs/history/plans/completed/2026-10-29-corrections-chain-recursion-refusal-and-pins.md` (landed 7179bc995, the mirrored two-line shape and its seven tests); lesson #142 in `docs/maintenance/development_lessons.md` (the decode-error catch-tuple family); the row's Accepted residuals section.

Rejected alternatives:
- Widen only the two parse tuples and leave the append `dumps` outside the guard: rejected - the row's original suggested fix wording had exactly this hole; RecursionError is not an OSError, so a serialization-depth failure still escapes the un-widened append guard (evidence basis: docs/history/backlog/2026-10-31-corrections-record-operand-recursion-unguarded.md Origin paragraph, corrected by review finding F3)
- Route the MemoryError/giant-string class through a new size precheck validator before serialization: rejected on the machinery-admission axis - no witnessed incident of the giant-write firing (the risk panel's probe triggered allocation pressure only synthetically), so a new blocker lacks its incident, catch-frequency, and false-positive pricing; the row's fold-the-decision arm is the smallest step that removes the witnessed traceback class (evidence basis: .ai-playbook/reviews/2026-10-31-corrections-chain-recursion-refusal-and-pins-code-review-r1.md finding F5)
- Leave the sites unguarded as acceptable operational noise: rejected - the named-refusal family is the established contract at every adjacent boundary (lesson #142; the sibling plan's landed receipt legs), so the traceback is a contract outlier, not an accepted posture (evidence basis: docs/maintenance/development_lessons.md lesson #142)

Machinery admission: nothing added; the precheck-validator arm is rejected above with the missing-incident absence named.

Disk re-derivation at the entry's write (2026-10-31): the three sites confirmed by `grep -n "except (ValueError, UnicodeDecodeError)" scripts/corrections_record.py` (both parse sites) and `sed -n 1494,1498p scripts/corrections_record.py` (the `dumps` outside the `except OSError` guard); the sibling plan confirmed at `git cat-file -e main:docs/history/plans/completed/2026-10-29-corrections-chain-recursion-refusal-and-pins.md`; lesson #142 confirmed by grep in docs/maintenance/development_lessons.md.

## hygiene-scanner-accepted-residuals-durable-home

Added: 2026-11-01, investigate over the 22:58 exec carrier session that landed hygiene-scanner-frozen-arm-and-report-residuals (830119aff)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): a body-named single-document edit - restore the accepted-residual acceptance record into `scripts/scan-public-hygiene.sh`'s own comment block so the two standing residuals keep a durable home at HEAD; no code behavior change, no open design choice, no dependency, no gate or state change.

Origins:
- docs/history/backlog/2026-10-30-report-scope-degradation-and-toctou-residuals.md (deleted per the covered-row rule in 830119aff; its residuals 2 and 5 lost their durable home - recover the record text from `git show 830119aff^:<path>`)
- .ai-playbook/reviews/2026-10-31-hygiene-scanner-frozen-arm-code-review-r1.md (the landing's focused review record)

Urgency: low - both residuals are fail-visible by design and accepted, but a future editor scanning HEAD finds no record of the acceptance (the origin rows were consumed, the script carries no residual comment, the lessons corpus has zero hits), inviting accidental closure or re-litigation without the witnessed pricing.

Scope arms: one bounded single-document edit: a short accepted-residuals comment block at the report-scope functions in `scripts/scan-public-hygiene.sh` recording (a) the two TOCTOU windows (a tracked path entering or leaving the scope between the git enumeration and the rg open; the shared patterns file changing between the `-f`/`-r` gate and the read inside the process substitution) as fail-visible-by-design acceptances that closing would need an atomic snapshot the scan sizes do not justify, and (b) the message-channel half-pin (the gate-level pin asserts the ordinary stub row never becomes a warning but not that it stays out of the finding message); the split-debris acceptance stays recorded where it already lives (the done gate's report-forwarding comment in `scripts/done_sweep_gates_lib.py`). An optional same-session selftest comment line may point at the block; no behavioral pin required.

Orientation: `git show 830119aff^:docs/history/backlog/2026-10-30-report-scope-degradation-and-toctou-residuals.md` (the deleted row carrying the original acceptance wording and pricing); `scripts/scan-public-hygiene.sh` (the report-scope functions the block annotates); the split-debris acceptance comment in `scripts/done_sweep_gates_lib.py` (the recorded-residual shape to mirror).

Rejected alternatives:
- Re-create the deleted origin rows under new names: rejected on the covered-row rule axis - the rows were consumed by the landing, and re-creating them resurrects consumed state the same rule exists to prevent (evidence basis: repository guidelines, Commit & PR Guidelines covered-row rule; landing commit 830119aff)
- Fold the residuals into the lessons corpus as a lesson: rejected - they are design acceptances on one mechanism, not incident lessons; the code comment is the surface an editor of the mechanism actually reads (evidence basis: grep at write time finds zero TOCTOU or half-pin hits in docs/maintenance/development_lessons.md)
- Close the TOCTOU windows with an atomic scope snapshot instead of recording them: rejected, machinery arm - no witnessed incident of either window firing, both fail visible by design, and closing them needs an atomic snapshot the scan sizes do not justify; the deleted row records the acceptance explicitly (evidence basis: `git show 830119aff^:docs/history/backlog/2026-10-30-report-scope-degradation-and-toctou-residuals.md`, residual 2)

Machinery admission: nothing added; the atomic-snapshot arm is rejected above with the missing-incident absence named.

Disk re-derivation at the entry's write (2026-11-01): `grep -n "TOCTOU\|split-debris\|half-pin" scripts/scan-public-hygiene.sh scripts/done_sweep_gates_lib.py` returns only the split-debris acceptance comment in the gate lib (zero TOCTOU or half-pin hits); `git cat-file -e HEAD:docs/history/backlog/2026-10-30-report-scope-degradation-and-toctou-residuals.md` fails while `git show 830119aff^:...` succeeds, so the acceptance text survives only at the landing's parent; the lessons-corpus absence confirmed by the same grep over docs/maintenance/development_lessons.md.

## scheduler-state-notes-at-timestamp-shape

Added: 2026-11-01, learn Step 1.9 investigate over the automation-born author turn session ee6cde74 (parallel-carrier cycle, compaction-resumed)

Work-type verdict: ad-hoc-able under the Ad-hoc backlog arm eligibility test (`agents/skills/maintenance/decisions.md`): one bounded convention sentence in `agents/skills/maintenance/state-file.md`'s notes field line plus an optional same-change stamp correction on the two witnessed values; no code, no open design choice, no dependency, no gate (the machinery arm is rejected below).

Origins:
- docs/history/backlog/2026-11-01-scheduler-state-notes-at-timestamp-shape.md

Urgency: low - the structured notes `at` field is advisory (incident and residue records no script consumes mechanically: working-tree grep and tip git grep over scripts/ find no reader of the notes array), so nothing breaks today; the exposure is one wrong-shaped stamp per imprecise write, and the ISO-shaped hybrid reads as parseable to a future consumer until it fails at parse time.

Scope arms: (1) one sentence in the notes field contract: an `at` value must be either an exact parseable ISO-8601 timestamp or an explicitly human-readable dated label, never an ISO-shaped string carrying placeholder characters, and the stamp is derived from the current operation's clock at write time; (2) same-change correction of the two witnessed stamps where their true write times remain re-derivable from the state file's own surrounding records.

Orientation: `agents/skills/maintenance/state-file.md` (the notes field line and the decision-shape-drift contract's canonical-spelling clause, dac9da757); the schema reconciliation landing d7f0c47e6 (which declared the `<iso or dated label>` tolerance from live entries); the origin row.

Rejected alternatives:
- Add a schema validator refusing placeholder-shaped or future-dated `at` values at write time: rejected, machinery arm - no witnessed incident of a consumer failing (the field is advisory; the no-consumer absence is the evidence basis), catch frequency low, false-positive cost nonzero (a validator would block an urgent incident note over a stamp nit), so the admission protocol's smallest-arm rule keeps the remedy in contract wording plus writer discipline (repository guidelines, Machinery admission protocol section)
- Narrow the tolerance to exact ISO only, dropping the dated-label arm: rejected - the dated-label tolerance was the schema reconciliation landing's deliberate shape declared from observed live entries (d7f0c47e6), and retro-narrowing it would invalidate tolerated pre-existing entries for no witnessed harm beyond the hybrid this entry already excludes
- Leave the contract as-is and rely on corpus discipline alone: rejected - the tolerance line demonstrably produced the hybrid within the witnessed cycle (two wrong-shaped stamps from two peer sessions in one hour, origin row), so the ambiguity is active at the surface writers actually read, not a dormant wording nit (evidence basis: the origin row's Observed section)

Machinery admission: nothing added; the validator arm is rejected above with the missing-incident absence named.

Prompt: Apply the one-sentence contract clarification to the notes field line, run `bash scripts/check_maintenance_pins.sh` (the touched skill file sits in the pins-adjacent family) and expect only the tracked baseline red, correct the two witnessed stamps where re-derivable, and record the stamps' corrected values in the landing receipt.

Disk re-derivation at the entry's write (2026-11-01): the two witness values confirmed by reading the `notes` array of `.ai-playbook/scheduler-state.json` (gitignored runtime surface; the quoted stamps in the origin row are the durable evidence); the schema tolerance line confirmed by `grep -n 'dated label' agents/skills/maintenance/state-file.md`; the canonical-spelling clause confirmed by `grep -n 'canonical timestamp spelling' agents/skills/maintenance/state-file.md`; the no-consumer absence confirmed by working-tree grep and tip git grep over `scripts/` for notes-array readers (both empty).
