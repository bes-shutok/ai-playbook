# Plan: Maintenance survey status reads bind to the committed tree

Backlog origin: docs/history/backlog/2026-10-02-maintenance-survey-head-bytes-rule.md
Driving force: reliability (fix-class repair of a recurring survey-freshness defect: unverified primary working-tree bytes misreport done corpus items as open and hide items HEAD carries, corrupting every maintenance survey's disk-truth base; the origin was witnessed twice in one survey and recurs every session)
Plan review record: the staging series docs/reviews/2026-10-02-plan-review-maintenance-survey-head-bytes-rule-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The maintenance skill's Step 1 survey opens with an explicit corpus freshness rule (status reads of tracked corpus files trust committed-tree bytes at HEAD, with a captured-tip, default-branch freshness verification as the sanctioned working-tree alternative; not-yet-landed listed paths, discovery listings, coverage greps, the rolling prompt log's own write discipline, claim files, and certification each routed explicitly), and the pins suite holds the rule's title and eight operative sub-spans in place region-scoped, so the phantom-open-item class cannot silently regress.

- Every fresh maintenance session reads tracked corpus status through `git show HEAD:<path>` or behind a captured-tip freshness verification, instead of trusting whatever bytes the primary working tree happens to hold when a peer landed after the last refresh; claim files keep their working-tree recency discipline at the authoritative checkout, and the log's own write-discipline reads ride the working tree.
- The rule's title and eight operative sub-spans (the read shape, the freshness verification, the trackedness routing, the listing reconciliation, the log carve-out, the claims carve-out, the fail-closed polarity, and the certification carve-out) are pinned region-scoped in the pins suite: deleting the bullet or any pinned operative span fails the suite even when the title phrase survives elsewhere in the region. The coverage-grep routing is check-witnessed (Validation check 5) rather than suite-pinned.
- No survey-runtime helper script bytes change; the only script touched is the pins suite itself, and only its pin and header comment. The fix is the skill's procedural discipline plus its pin, exactly the shape the origin's Suggested fix prescribes.

Gate delta: one new prose bullet in `agents/skills/maintenance/SKILL.md` Step 1 (survey), and one region-scoped needle loop (the title plus eight operative sub-spans) plus its header-comment family clause in `scripts/check_maintenance_pins.sh`. This is a refusal-path addition on a tooling-class origin carrying its pricing: the origin is a twice-witnessed recurring incident capture whose completed-integrity failure is the silent phantom-open-item corruption of every later survey, and whose Suggested fix prescribes exactly this shape (one sentence in the survey step, then a pins-suite pin). The class-default alternatives are addressed by the origin: there is no false positive to remove (the discipline exists only in session memory today; "zero matches for the HEAD-read discipline in the skill at HEAD", verified 2026-10-02 and re-derived by this plan's authoring), and no smaller exit exists (memory-only guidance is the unenforced status quo the origin falsified).

## Terms

- **Status read**: any survey read whose output decides an item's open/closed/claimed/done or covered/uncovered state, existence checks included; certification reads that verify a plan's digest against its bytes are not status reads and keep their current semantics.
- **Corpus file**: a status-bearing repository document the survey reads. Tracked corpus files (open backlog items, the rolling prompt log `PLAN-PROMPTS.md`, top-level plans) bind to the committed tree. A listed path is routed before any bytes read: a path whose basename appears nowhere in `git ls-tree -r HEAD --name-only` is not-yet-landed state (read from the working tree, never recorded absent, never counted as open queue depth, never proposed for dispatch); a path absent at HEAD whose basename HEAD carries at another corpus path is a duplicate or moved entry (the tracked twin is the item of record; the listed entry is reported as not-yet-landed or moved and skipped); a path HEAD carries at the listed path is tracked and the read-shape polarity and freshness verification govern its bytes. The claim files under `docs/tmp/authoring-claims/` and `docs/tmp/execution-claims/` are gitignored (`.gitignore` line 16), working-tree-only by construction, and the rule routes them through their own recency discipline at the authoritative checkout rather than the committed-tree bind.
- **Freshness verification**: the sanctioned working-tree alternative for tracked corpus reads: the checkout is at the resolved default branch and not mid-rebase or mid-merge; record `git rev-parse HEAD`, confirm `git status --porcelain --untracked-files=no` is clean, and treat working-tree bytes as committed bytes only while the recorded hash still equals the live tip and the porcelain check remains clean. A tip mismatch or a non-clean status observed on any later read re-triggers verification and invalidates the pass's earlier classifications, which re-run.
- **The pins suite**: `scripts/check_maintenance_pins.sh` (bash, exit 0 = all pins hold); its Step 1 region checks slice the skill between the `### Step 1: survey` and `### Step 2` anchors and run fixed-string needle checks against the slice.

## Assumptions

- assume the fix lands as skill prose plus a pin, not as a survey helper script; basis: the origin's Suggested fix prescribes exactly this shape, one sentence in the survey step naming the class and the required read shape, then a pin to the pins suite next to the existing survey-step pins, with the suite and the hygiene scan run before landing; and the machinery cost-benefit adjudication (2026-09-28) caps machinery growth, so a new enforcement script for a one-sentence discipline would need to clear a bar the origin does not raise.
- assume the pin is a region-scoped needle loop (the rule's title plus its eight operative sub-spans: the read shape, the freshness verification, the trackedness routing, the listing reconciliation, the log carve-out, the claims carve-out, the fail-closed polarity, and the certification carve-out) rather than a whole-file grep or a bare-title token; basis: the suite's own region-scoped-pin doctrine, quoted verbatim from the suite's pending_rearm comment ("a whole-file grep is satisfied by a stray copy, and deleting the Pending re-arm reader bullet empties the region and fails here", scripts/check_maintenance_pins.sh; the comment wraps this sentence across two lines, so the span is contiguous only when newlines are flattened), and its existing needle-loop pattern (the Step 3 quota needles), which the origin's placement next to the existing survey-step pins names.
- assume claim files are routed through their working-tree recency discipline rather than the committed-tree bind; basis: `.gitignore` line 16 ignores `/docs/tmp/`, so claim files cannot be committed-tree residents (`git ls-files docs/tmp/` is empty), and the Step 1 Authoring-claim consult already owns their recency semantics at the primary checkout (the consult's own wording).
- assume the rolling prompt log's own write-discipline reads ride the working tree rather than the committed-tree bind; basis: the Step 3 log duties are a same-turn read-modify-write flow (re-read and compare before every write, two sequential targeted edits, commit in the same turn) whose intermediate reads are of the flow's own uncommitted bytes, which neither sanctioned path can serve, and whose self-freeze visibility guarantee depends on prompt peer reads.
- assume directory listings stay find-based but are governed by the rule: listings that feed status decisions are discovery reads, and on a checkout whose freshness verification has not passed they reconcile against `git ls-tree HEAD --name-only <corpus-dir>` in both directions before use (an item HEAD carries that the listing lacks enters the surveyed set; an item's absence is treated as absence only after the reconciliation); basis: the freshness verification gates byte-trust, not path discovery (its fail branch leaves discovery stale, which is the origin's hiding half), the ls-tree reconciliation covers presence-at-HEAD from any checkout in both directions, and the trackedness clause governs the working-tree-only remainder.
- assume `git show HEAD:<path>` is the required read shape despite being git-specific; basis: it is the origin's own prescribed form, the suite's SKILL.md runtime-agnosticism pin guards against agent-runtime tools rather than version-control plumbing, and the skill's steps already name git and filesystem operations directly.
- Sources inspected: `agents/skills/maintenance/SKILL.md` Step 1 at main b2e63486 (read 2026-10-02: zero matches for the HEAD-read discipline, `### Step 1: survey` heading count 1, first bullet `- Open backlog items:`, the Step 2 heading's true shape `### Step 2: guards (fixed order)`, zero `git show HEAD:` and zero `--untracked-files=no` occurrences, two existing `git status --porcelain` sites, the Authoring-claim consult, the dirty-primary classification arm, the interrupted-manifest classification arm, the Step 3 rolling-log duties' re-read-compare and same-turn-commit discipline, and the landing read-back's `refs/heads/<default>` idiom); `scripts/check_maintenance_pins.sh` (read 2026-10-02: the pin/expect_absent helpers, the `need(s, "### Step 1: survey")` block with its substring-split step1 slice and region-scoped needle checks, the absence-pin corpus re-measured at base as 35 invocation lines (28 `expect_absent`, 7 `expect_absent_flat`; two five-file for-loop lines, 43 pin applications), the enforcer-form count 1 at base, and the absence-pin corpus checked phrase-by-phrase against the folded bullet's vocabulary with zero collisions); `.gitignore` (line 16, `/docs/tmp/`); the origin's own verification lines.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the maintenance survey keeps misreading corpus status from stale primary working-tree bytes because the HEAD-read discipline lives only in session memory; this plan writes the discipline into the survey step as one prose bullet and pins its title and operative spans region-scoped in the pins suite, so every fresh session inherits the rule and its loss is a suite failure instead of a silent regression (reliability force).

Before (today): a peer lands a backlog closeout between the checkout's last refresh and the survey; the survey reads the working tree, reports the done item as open (or misses an item HEAD carries), and the turn authors, dispatches, or stands down on phantom state. The origin witnessed this twice in one survey, and the correction existed only as session memory.

After (this plan): the same survey reads the Step 1 corpus freshness rule first: tracked corpus status reads go through `git show HEAD:<path>` (absence recorded only when HEAD resolved and the read then failed; any other read error reports the item unclassified), or the checkout proves itself fresh (default branch, no rebase or merge in progress, captured tip equal to the live tip, clean `git status --porcelain --untracked-files=no`) before working-tree bytes are trusted, with a moved tip invalidating the pass's earlier classifications; not-yet-landed listed paths are read from the working tree, never counted as queue depth, and never proposed for dispatch; unverified-checkout listings reconcile against `git ls-tree HEAD --name-only <corpus-dir>` in both directions and coverage greps run through `git grep <pattern> HEAD`; the log's write-discipline reads and the claim files keep their working-tree disciplines. If a later edit deletes or guts any pinned span, `bash scripts/check_maintenance_pins.sh` fails with the corpus freshness rule needle pin.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the bullet names the defect class, the required read shape, the failure polarity and its reporting state, and the sanctioned freshness verification with its branch precondition, and the pin's needles match the landed bytes inside the Step 1 region at the region's top (Validation checks 3 and 5).
- regression safety: the full pins suite stays green with the new pin in place (check 3), and the new needles demonstrably discriminate the base bytes from the landed bytes (check 4), so they are not vacuous canaries.
- scope: the changed-file set against main is exactly the skill file and the pins suite file (check 7).

**Done when:**
- The Step 1 survey opens with the corpus freshness rule bullet; the pins suite carries the region-scoped needle loop (title plus eight operative sub-spans) and its header family clause; every check-4 and check-5 arm passes with its diagnostic; the full suite exits 0 on the execution branch; all Validation Commands exit 0.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] The runtime twin of the touched skill is refreshed per the operators' normal vendored-asset sync (the `~/.agents/skills/` copy of the maintenance skill), so live maintenance sessions load the rule; owner: the execution session's closeout sync step as the preferred first arm, and unconditionally a vendored-sync backlog item naming `agents/skills/maintenance/SKILL.md` (left even when the sync step is claimed, closed only on the evidence); closure evidence: after the sync, `grep -c 'Corpus freshness rule' ~/.agents/skills/maintenance/SKILL.md` prints 1. Consumer repositories that run the skill receive it through their own sync.

## Review Scope

- `docs/history/plans/2026-10-02-maintenance-survey-head-bytes-rule.md`
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-10-02-maintenance-survey-head-bytes-rule.md`

## Validation Commands

Authoring-time records: (1) Rule 19 RED-today evidence: the rule is absent from both base files at main b2e63486, re-derived 2026-10-02 (`git show main:agents/skills/maintenance/SKILL.md | grep -c 'Corpus freshness rule'` prints 0; the same for `main:scripts/check_maintenance_pins.sh` prints 0); the pins suite exits 0 on the base tree (the base is green; this plan adds a pin, it does not repair a red one). (2) Baselines on the base tree, 2026-10-02: `bash scripts/check_maintenance_pins.sh` exit 0; the Step 1 heading count 1; the absence-pin corpus re-measured as 35 invocation lines (28 `expect_absent`, 7 `expect_absent_flat`; two five-file for-loop lines, 43 pin applications), checked phrase-by-phrase against the folded bullet's vocabulary (`git show HEAD:`, `git status --porcelain --untracked-files=no`, `committed tree`, `working-tree-only by construction`, `not-yet-landed`, `git ls-tree HEAD --name-only`, `the rolling prompt log's own write discipline`, `never records absence`, `keep their current semantics`, `Corpus freshness rule`, `corpus-freshness rule`) with zero collisions; the base skill's `git show HEAD:`, `--untracked-files=no`, `not-yet-landed`, `git ls-tree HEAD`, and `unclassified` counts are each 0, and the base suite's enforcer-form count is exactly 1, so every folded check arm is discriminating. (3) Rule 29 pre-round gates on the plan bytes: `bash scripts/check-no-em-dash.sh touched` exit 0; the public-hygiene scan exit 0; `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-02-maintenance-survey-head-bytes-rule.md` clean (the gate resolves facts from `.ai-playbook/facts.md`, which is untracked and primary-only, so a facts copy was placed in the authoring worktree before the run). (4) Rule 22 mechanical audit plus rule 44 extraction proof: the plan's fences were extracted mechanically (regex over the plan bytes, signature-keyed because the validation fence precedes the task fences) and applied to a scratch clone of main at b2e63486 with the plan committed onto the clone's main first (execution semantics: the authoring landing puts the plan on main before execution runs). The ENTIRE Validation block was then executed end to end from the extracted bytes: exit 0 (hygiene PASS; the pins suite reports all hold with the new pin firing green against the applied bullet; the byte-count and changed-file checks silent-passed under set -e). The flip probes then proved fail-closed semantics in both directions: removing the inserted bullet aborted the block at check 3 with the pin's own PIN FAIL line, and reverting the pins-script edits while keeping the bullet aborted at the check 5 arms, closing the partial-application paths. Both flips were restored and the block re-ran green (exit 0). One sim-harness defect was caught and corrected without touching the plan bytes: the first extraction pass keyed fences by position and mis-keyed the validation fence (the plan's fence order puts the bash block first); the signature-keyed extraction is the corrected harness. (5) r1 fold receipt: the full-panel round (five workers, two waves, 29 raw findings: 15 staged, 12 echo contributions merged, 1 overflow, 2 blocking) folded in one batch: the bullet rescoped to tracked corpus classes with claim files routed through their working-tree recency discipline and the certification carve-out carried into the landed bytes (F1, F3), the failed-read polarity made fail-closed and the freshness verification bound to a captured tip (F5, F6), HEAD inlined and the invented base-ref term deleted with the porcelain spelling adopted (F11, F14), the pin converted to a region-scoped needle loop over the title plus operative spans (F4), the region-witness awk terminator fixed in both places (F2), check 5 extended with the read-shape, freshness-shape, region-form, and header-clause arms plus base-discrimination arms for the new literals (F12, F13), the Outcome bullet 3 contradiction reworded and the Ship-when item given its class, owner, and closure evidence (F8, F9), the assumption quotes made verbatim or unquoted paraphrases with the r3-F10 label replaced by the doctrine's verifiable home (F10, overflow), and the absence-pin count restated on the re-measured basis (F15); after the fold the mechanical extraction, the full-block run, and the flip probes were re-executed on the folded bytes with the same GREEN and fail-closed outcomes. (6) r2 fold receipt: the fresh full-panel round (five workers, 16 raw findings: 11 staged, 2 echo contributions merged, 2 overflow, 3 blocking) folded in one batch: the rolling prompt log's own write-discipline reads carved out of the bind with their same-turn commit duty named and pinned (F1), the trackedness classification added for listed paths HEAD does not carry with the never-counted-as-queue-depth rule (F2), the adjacency arm added so the bullet must sit at the Step 1 region's top (F3), the listing-reconciliation clause added with Assumption 5's basis rewritten truthfully (F4), the tuple extended to the log carve-out and trackedness and listing spans with the Outcome guarantee reworded to the pin's actual coverage (F5), the captured-tip mismatch duty added on the freshness path (its both-paths extension landed with the r4 fold) (F6), the concurrent-operation recovery preamble added with the enforcer-count premise made re-derivable (F7, F9), per-arm diagnostics added to checks 4 and 5 (F8), the three missing base-discrimination arms added (F10), the twin-refresh owner made unconditional (F11), and the two overflow items folded (the default-branch, no-rebase freshness precondition; the stopped-read reporting state); after the fold the mechanical extraction, the full-block run, and the flip probes were re-executed on the folded bytes with the same GREEN and fail-closed outcomes. (7) r3 fold receipt: the fresh full-panel round (five workers, 9 raw findings: 7 staged, 2 echo contributions merged, 3 blocking) folded in one batch: the not-yet-landed predicate sharpened to basename-scoped absence with the polarity-and-reconciliation precedence stated and the dispatch guard added (F1, F6), the listing reconciliation made bidirectional so the presence half enters the surveyed set (F2), the coverage grep given its HEAD shape on unverified checkouts with the Status read definition widened to covered/uncovered (F3), the freshness later-read re-check keyed to both predicates, tip and cleanliness (F4), the suite tuple extended to the polarity and certification spans (nine needles) with the Outcome enumeration restated self-identifyingly and the coverage-grep routing named check-witnessed (F5, F7), and the check 4 and check 5 arms extended to the coverage-grep shape; after the fold the mechanical extraction, the full-block run, and the flip probes were re-executed on the folded bytes with the same GREEN and fail-closed outcomes. (8) r4 fold receipt: the fresh full-panel round (five workers, 10 raw findings: 8 staged, 1 discarded after orchestrator re-derivation, 2 overflow, 0 blocking, design-simplicity zero findings at the round-4 bar) folded in one batch: the mid-pass invalidation duty moved out of the freshness parenthetical into a both-arms pass-level sentence with the checkout-relative note and the off-default reporting state (F1, overflow O2), the freshness literal restored to its once-form with the Terms phrasing (F3), eight tuple mirror arms added so a partially-applied Task 2 cannot pass (F2), the validated bytes bound to the branch by a block-opening cleanliness arm (F5), the Archived-coverage origins scan's disposition decided in the bullet (F4), the doctrine quote annotated as spanning a wrapped comment line (F6), the recovery note corrected to three verbatim edits (F7), the trackedness precedence scoped to tracked items (F8), and the claims carve-out reworded to the primary checkout (overflow O1); during the round main moved from the branch base b2e63486 to 46a91c91 (three landings, one touching the pins suite at distant line ranges) and every check-arm base count (the enforcer-form count 1, both Task 2 anchors byte-intact, and every new literal's zero count) re-derived identical at the new tip, while the arm-free absence-pin corpus moved from 35 invocation lines (43 applications) at b2e63486 to 36 (44) at 46a91c91 because the unblock-landing rework added one expect_absent_flat pin; one finding was discarded with reason: the staged High claiming the doubled freshness literal aborts the block was disproven by the executed block (grep -c counts lines, the bullet is one line, the arm reads 1, the sim ran green end-to-end), and its verified kernel was re-staged as F3 at Low; after the fold the mechanical extraction, the full-block run, and the flip probes were re-executed on the folded bytes with the same GREEN and fail-closed outcomes.

```bash
set -e
# Executor note: run from the repository root. set -e makes the block fail
# closed: the first failing check aborts with its own non-zero status. Checks
# 1-3 are repository gates (exit status is their contract); checks 4-6 are
# byte-level discrimination and shape pins (each arm carries its own
# diagnostic); check 7 pins the changed-file set.
#
# Concurrent-operation recovery (run before check 1): if main moved since the
# branch was cut (a sibling landing), refresh onto the current main tip
# (re-cut the branch, re-apply the three verbatim edits: the Task 1 bullet
# insertion and Task 2's two suite edits) and re-derive the
# check 4 and check 5 counts from the rebased bytes before running; the
# enforcer-form arm's expected value is the base count (1) plus this block
# (1), so if a sibling plan landed another step1-scoped needle loop first,
# re-measure and update that expected count before running.

# 0) the validated bytes are the branch's bytes (bind the working tree to
#    HEAD before any arm reads it)
[ -z "$(git status --porcelain -- agents/skills/maintenance/SKILL.md scripts/check_maintenance_pins.sh)" ] || { echo "check 0: validation targets dirty against HEAD:"; git status --porcelain -- agents/skills/maintenance/SKILL.md scripts/check_maintenance_pins.sh; exit 1; }

# 1) public hygiene (exit 0 required)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

# 2) em-dash gate over the changed bytes against main
bash scripts/check-no-em-dash.sh added-lines --base main

# 3) the full pins suite, new pin included (exit 0 required)
bash scripts/check_maintenance_pins.sh

# 4) base discrimination: the rule's needles are absent from the base files
#    and the operative literals are new to their files, so every new check is
#    discriminating
[ "$(git show main:agents/skills/maintenance/SKILL.md | grep -c 'Corpus freshness rule')" -eq 0 ] || { echo "check 4: title not absent from base skill"; exit 1; }
[ "$(git show main:scripts/check_maintenance_pins.sh | grep -c 'Corpus freshness rule')" -eq 0 ] || { echo "check 4: title not absent from base suite"; exit 1; }
[ "$(git show main:agents/skills/maintenance/SKILL.md | grep -cF 'git show HEAD:')" -eq 0 ] || { echo "check 4: read shape not new to the base skill"; exit 1; }
[ "$(git show main:agents/skills/maintenance/SKILL.md | grep -cF 'untracked-files=no')" -eq 0 ] || { echo "check 4: freshness flag not new to the base skill"; exit 1; }
[ "$(git show main:agents/skills/maintenance/SKILL.md | grep -c 'working-tree-only by construction')" -eq 0 ] || { echo "check 4: claims span not new to the base skill"; exit 1; }
[ "$(git show main:scripts/check_maintenance_pins.sh | grep -c 'corpus-freshness rule')" -eq 0 ] || { echo "check 4: header clause not new to the base suite"; exit 1; }
[ "$(git show main:scripts/check_maintenance_pins.sh | grep -cF 'if needle not in step1:')" -eq 1 ] || { echo "check 4: base enforcer-form count is not exactly 1 (re-derive)"; exit 1; }
[ "$(git show main:agents/skills/maintenance/SKILL.md | grep -cF 'git grep <pattern> HEAD')" -eq 0 ] || { echo "check 4: coverage-grep shape not new to the base skill"; exit 1; }

# 5) landed bytes: the title appears exactly once in the skill, at the top of
#    the Step 1 region (adjacent above the Open backlog items bullet); every
#    pinned operative span lands exactly once; the suite file carries the
#    needle tuple once, exactly one added step1-scoped enforcer, and the
#    header clause once (so a skipped Task 2 edit, a de-regioned pin, a
#    watered bullet, or a misplaced bullet cannot pass checks 3-4 as green)
[ "$(grep -c 'Corpus freshness rule' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: title count in skill"; exit 1; }
[ "$(awk '/^### Step 1: survey$/{f=1;next} /^### Step 2/{f=0} f' agents/skills/maintenance/SKILL.md | grep -c 'Corpus freshness rule')" -eq 1 ] || { echo "check 5: title not in the Step 1 region"; exit 1; }
[ "$(grep -n -e '- Corpus freshness rule' agents/skills/maintenance/SKILL.md | head -1 | cut -d: -f1)" = "$(( $(grep -n -e '- Open backlog items:' agents/skills/maintenance/SKILL.md | head -1 | cut -d: -f1) - 1 ))" ] || { echo "check 5: bullet not directly above the Open backlog items bullet"; exit 1; }
[ "$(grep -cF 'git show HEAD:<path>' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: read-shape span count"; exit 1; }
[ "$(grep -cF 'git status --porcelain --untracked-files=no' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: freshness span count"; exit 1; }
[ "$(grep -c 'working-tree-only by construction' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: claims carve-out span count"; exit 1; }
[ "$(grep -c 'not-yet-landed' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: trackedness span count"; exit 1; }
[ "$(grep -cF 'git ls-tree HEAD --name-only' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: listing-reconciliation span count"; exit 1; }
[ "$(grep -c "the rolling prompt log's own write discipline" agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: log carve-out span count"; exit 1; }
[ "$(grep -c 'never records absence' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: polarity span count"; exit 1; }
[ "$(grep -c 'keep their current semantics' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: certification carve-out span count"; exit 1; }
[ "$(grep -cF 'git grep <pattern> HEAD' agents/skills/maintenance/SKILL.md)" -eq 1 ] || { echo "check 5: coverage-grep shape count"; exit 1; }
[ "$(grep -c 'Corpus freshness rule' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: suite needle-tuple count"; exit 1; }
[ "$(grep -cF 'if needle not in step1:' scripts/check_maintenance_pins.sh)" -eq 2 ] || { echo "check 5: enforcer-form count (base 1 + this block; re-derive if a sibling loop landed)"; exit 1; }
[ "$(grep -c 'corpus-freshness rule' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: header clause count"; exit 1; }
[ "$(grep -cF 'git show HEAD:<path>' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: read-shape needle missing from suite tuple"; exit 1; }
[ "$(grep -cF 'git status --porcelain --untracked-files=no' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: freshness needle missing from suite tuple"; exit 1; }
[ "$(grep -c 'not-yet-landed' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: trackedness needle missing from suite tuple"; exit 1; }
[ "$(grep -cF 'git ls-tree HEAD --name-only' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: listing needle missing from suite tuple"; exit 1; }
[ "$(grep -c "the rolling prompt log's own write discipline" scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: log carve-out needle missing from suite tuple"; exit 1; }
[ "$(grep -c 'working-tree-only by construction' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: claims needle missing from suite tuple"; exit 1; }
[ "$(grep -c 'never records absence' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: polarity needle missing from suite tuple"; exit 1; }
[ "$(grep -c 'keep their current semantics' scripts/check_maintenance_pins.sh)" -eq 1 ] || { echo "check 5: certification needle missing from suite tuple"; exit 1; }

# 6) the edited suite still parses
bash -n scripts/check_maintenance_pins.sh

# 7) changed-file scope: main is an ancestor of the execution branch at its
#    tip, and the branch differs from main in exactly the skill bullet file
#    and the pins suite (the plan bytes are already on main at execution)
[ "$(git rev-parse main)" = "$(git merge-base main HEAD)" ] || { echo "main is not an ancestor of the execution branch tip"; exit 1; }
[ "$(git diff --name-only main | sort)" = "$(printf 'agents/skills/maintenance/SKILL.md\nscripts/check_maintenance_pins.sh')" ] || { echo "unexpected changed-file set against main:"; git diff --name-only main; exit 1; }
```

### Task 1: the Step 1 survey opens with the corpus freshness rule

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- Validation block checks 4 and 5 (including the adjacency arm)

One verbatim insertion. The fenced block shows the anchor context (the `### Step 1: survey` heading line and its following blank line, which occur exactly once in the file, verified count 1 at authoring time) plus the one added line; the bullet line lands directly above the existing `- Open backlog items:` bullet with no blank line introduced between bullets, and the adjacency arm in check 5 pins that placement. The fence is the byte contract for the added line.

```
### Step 1: survey

- Corpus freshness rule (added 2026-10-02, the maintenance survey head-bytes origin): every status read of a tracked corpus file (open backlog items, the rolling prompt log, top-level plans) trusts only bytes that equal the committed tree at HEAD: read it through `git show HEAD:<path>`, recording absence only when HEAD itself resolved, the path read then failed, and `git ls-tree HEAD -- <path>` shows the path absent from HEAD's tree (a failed read on a path HEAD's tree carries is a read error, never absence; any other read error stops that item's read and never records absence: report the item unclassified with the read error in the survey output), or verify the checkout fresh first (the checkout is at the resolved default branch and not mid-rebase or mid-merge; record `git rev-parse HEAD`, confirm `git status --porcelain --untracked-files=no` is clean, and treat working-tree bytes as committed bytes only while the recorded hash still equals the live tip and the porcelain check remains clean); the pass captures the tip once (`git rev-parse HEAD` at the pass's start): every later status read on either path compares the live tip against the recorded hash, and a mismatch, or a non-clean porcelain observed on the freshness path, invalidates the pass's earlier classifications, which re-run (the HEAD read is checkout-relative by design: when the default-branch precondition fails, the pass still reports the checkout state, branch and tip, in the survey output instead of leaving the state silent); a listed path is routed before any bytes read: a path whose basename appears nowhere in `git ls-tree -r HEAD --name-only` is not-yet-landed state (read it from the working tree, never record it absent, never count it as open queue depth, and never propose it for dispatch: report it and skip until it lands at HEAD); a path absent at HEAD whose basename HEAD carries at another corpus path is a duplicate or moved entry (the item of record is the tracked twin: read its status at the tracked path, and report the listed entry as not-yet-landed or moved and skipped, never recorded absent and never counted as open queue depth); a path HEAD carries at the listed path is tracked: the read-shape polarity and the freshness verification govern its bytes, with the listing reconciliation deciding presence or absence first; directory listings that feed status decisions are discovery reads: when the freshness verification has not passed, reconcile them against `git ls-tree HEAD --name-only <corpus-dir>` in both directions before use (an item HEAD carries that the listing lacks enters the surveyed set; an item's absence is treated as absence only after the reconciliation); directory-content status reads (the Plan coverage filename grep) run through `git grep <pattern> HEAD -- <corpus-dir>` when the freshness verification has not passed; the Archived-coverage origins scan keeps its working-tree script consult (its warn token never changes skip semantics and never blocks the turn); reads that are part of the rolling prompt log's own write discipline, and re-reads of the flow's own same-turn commits, ride the working tree at the primary checkout, not the committed-tree bind; claim files under the gitignored tmp surfaces are working-tree-only by construction: read them from the primary checkout per their own recency discipline, never through `git show`; digest-verification reads that certify a plan's bytes are not status reads and keep their current semantics.
```

- [ ] Run → expect RED: `git show main:agents/skills/maintenance/SKILL.md | grep -c 'Corpus freshness rule'` prints 0 (re-derived on the base tree at main b2e63486, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Insert the fenced bullet (the heading and blank line are the anchor context; the bullet line is the one added line, single occurrence, directly above the existing `- Open backlog items:` bullet) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: all ten span greps return exactly 1 in the skill: `grep -c 'Corpus freshness rule'` (the title), `grep -cF 'git show HEAD:<path>'` (the read shape), `grep -cF 'git status --porcelain --untracked-files=no'` (the freshness verification), `grep -c 'working-tree-only by construction'` (the claims carve-out), `grep -c 'not-yet-landed'` (the trackedness routing), `grep -cF 'git ls-tree HEAD --name-only'` (the listing reconciliation), `grep -cF 'git grep <pattern> HEAD'` (the coverage-grep routing), `grep -c "the rolling prompt log's own write discipline"` (the log carve-out), `grep -c 'never records absence'` (the fail-closed polarity), and `grep -c 'keep their current semantics'` (the certification carve-out); the Step 1 region slice contains the title exactly once, and the bullet's line number equals the `- Open backlog items:` line number minus one (a bullet placed anywhere else in the region fails the adjacency witness) [class: REPOSITORY_TEST]

### Task 2: the pins suite holds the rule region-scoped

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- Validation block checks 3, 4, 5, and 6

Two verbatim edits. Edit (a) extends the header family list; replace the anchor:

```
# and the user-directed-payload-duties family (the re-arm-first duty and its
# liveness report for the user-directed payload class).
```

with:

```
# and the user-directed-payload-duties family (the re-arm-first duty and its
# liveness report for the user-directed payload class), and the Step 1
# corpus-freshness rule (status reads bind to the committed tree at HEAD).
```

Edit (b) inserts the region-scoped needle loop inside the existing python heredoc (which already propagates failure via its `|| fail=1`), immediately after the anchor block:

```
if "pending_dispatch" not in step1:
    print("PIN FAIL: pending_dispatch reader missing from the Step 1 list"); sys.exit(1)
```

inserting:

```
# the maintenance survey head-bytes rule (plan
# 2026-10-02-maintenance-survey-head-bytes-rule.md): the Step 1 corpus
# freshness rule needles, region-scoped per the suite's vacuous-canary
# doctrine ("a whole-file grep is satisfied by a stray copy, and deleting
# the Pending re-arm reader bullet empties the region and fails here";
# that sentence wraps across two comment lines in this file)
for needle in ("Corpus freshness rule",
               "git show HEAD:<path>",
               "git status --porcelain --untracked-files=no",
               "not-yet-landed",
               "git ls-tree HEAD --name-only",
               "the rolling prompt log's own write discipline",
               "working-tree-only by construction",
               "never records absence",
               "keep their current semantics"):
    if needle not in step1:
        print("PIN FAIL: Step 1 lacks the corpus freshness rule needle %r" % (needle,)); sys.exit(1)
```

- [ ] Run → expect RED: `git show main:scripts/check_maintenance_pins.sh | grep -c 'Corpus freshness rule'` prints 0 (re-derived on the base tree at main b2e63486, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Apply both verbatim edits (header tail replacement, one occurrence; region insertion after the pending_dispatch needle check, one occurrence) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash -n scripts/check_maintenance_pins.sh` exits 0, and `bash scripts/check_maintenance_pins.sh` exits 0 (the new needles fire green against Task 1's bullet; every pre-existing pin stays green) [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: survey status reads bind to the committed tree (pin included)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Residual findings (cap closure)

The loop reached its configured five-round cap; this section is the cap-closure terminal shape's in-plan home for the cap round's staged findings and their dispositions (the r5 round reported zero blocking findings; every finding below is non-blocking and was folded in the same pass, so no residual remains unresolved):

- F1 (Medium, risk, `security#head-read-conflates-unreadable-blob-with-absence`): the polarity treated every post-HEAD-resolution read failure as sanctioned absence, conflating an unreadable blob with a truly absent path. Disposition: folded (the polarity now requires `git ls-tree HEAD -- <path>` to show the path absent; a failed read on a path HEAD's tree carries is a read error reaching the stopped-read state).
- F2 (Medium, risk, `security#basename-trackedness-misroutes-colliding-untracked-draft`): the basename-scoped trackedness predicate misrouted an untracked draft whose basename matched a tracked twin into tracked handling, recording false absence. Disposition: folded (the listed path is now routed before any bytes read: basename-nowhere routes to not-yet-landed; basename-elsewhere with the path absent at HEAD routes to the duplicate-or-moved entry whose tracked twin is the item of record; only a path HEAD carries at the listed path is tracked).
- F3 (Low, correctness-completeness lead with testing echo, `testing#coverage-claim-unchecked`): the r4 receipt's "every base count re-derived identical" over-claimed while the arm-free absence-pin corpus had drifted at the new tip. Disposition: folded (the receipt scopes the identical-claim to the check-arm counts and records the corpus drift with its origin).
- F4 (Low, contract-docs, `consistency#diagnostic-naming-drift`): the check 4 diagnostic misspelled enforcer-form as enformer-form. Disposition: folded (corrected).

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-02-maintenance-survey-head-bytes-rule.md`: this plan's own promoted origin. On completion, fold disposition into the archived plan (rule landed, pin green, base discrimination verified) and delete the origin file in the same completion pass per the archive gate.
