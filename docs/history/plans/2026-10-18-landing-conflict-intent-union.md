# Plan: Union-of-intents landing conflict discipline

Backlog origin: docs/history/backlog/2026-10-09-rebase-conflict-side-selection-no-delta-verification.md
Driving force: reliability
Justification: two witnessed conflict side-selection defects in the landing critical section in nine days, the second escaped to main and needed a post-landing repair, and nothing mechanical catches either; park-triage would not defer: the surface is the landing critical section shared by every lane.
Plan review record: the staging series .ai-playbook/reviews/2026-10-18-plan-review-landing-conflict-intent-union-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1h

Authoring claim: docs/tmp/authoring-claims/landing-conflict-intent-union.md (session sess_d7b16c2e-0ca5-4449-8d37-07e65ed62f54)

## Terms

- **Conflict block**: the conflicted hunk region a merge or rebase presents inside one file.
- **Side-pick**: resolving a conflict block by taking one side's bytes wholesale and discarding the other side's.
- **Union-of-intents resolution**: resolving each conflict block so both sides' stated intents survive: a branch-side removal stays removed, a base-side addition stays added, and overlapping edits merge line-by-line keeping foreign lines.
- **Destructive intent**: a resolution input whose intent is a removal: a pruned dispatch-log entry, a deleted file section, a dropped line.
- **Post-resolution re-verification**: after any merge or rebase whose result feeds the landing's gates, whether composed before lock acquisition or inside the critical section, and always before the landing gates next run, the direct evidence pass over the merged tree: each pruned heading or removed span re-grepped absent, each base-side addition re-grepped present, and the landing's receipt audits re-run against the post-merge bytes.
- **Landing critical section**: the merge-landing-lock-guarded window from acquire to release, whose operative home is the Worktree-first standard section in `agents/skills/execute-plan/SKILL.md`.
- **Prune receipt**: the `PLAN-PROMPTS-PRUNE: <slug> -> <witness>` content line a landing's rider writes into the rolling log beside the entry deletion.
- **Receipt-without-removal finding**: the new warning class in the prune audit: a base..HEAD commit that adds a receipt line to a rolling log while removing no entry from that same log.
- **Ordinary preservation**: the audit's existing fail classes and verdict lines, the sanctioned re-apply repair shape (a removal completing an earlier in-range commit's receipt classifies clean, while that receipt commit warning once is the class's priced shape, not a violation), and the reverse-squash and compare-and-swap gates keep their behavior and bytes.

## Why

The landing critical section carries no conflict-content rule in any skill text: no side-selection rule and no post-resolution verification exist on any lane (the undefined clause "resolve conflicts faithfully" survives only in project lesson 6's narrative, never in operative skill bytes). Two witnessed side-picks in nine days: a 2026-10-09 branch-side pick reverted a peer's landed line inside a kept shared file (caught only by a manual post-rebase diff), and a 2026-10-18 base-side pick resurrected the landing branch's own pruned dispatch entry, so the landing carried only the +1 receipt and the removal completed as the post-landing repair c3a283738. Nothing mechanical catches either shape: the prune audit enumerates removals only, so a resolution that drops the removal intent leaves it nothing to check. Design input beside the origin row: the dispatch entry `landing-conflict-intent-union` (docs/history/backlog/PLAN-PROMPTS.md, 2026-10-18), whose recommended arms this plan lands and whose rejected alternatives it carries; project lesson 93 (docs/maintenance/development_lessons.md) pins the corpus wording.

## Gist & Examples

TLDR: the landing critical section resolves merge conflicts by union of the two sides' intents and re-verifies every destructive intent on the merged tree before the landing continues, and the prune audit gains a warning-shaped receipt-without-removal finding, so a conflict resolution can no longer silently drop a prune or a peer's landed lines.

Before (today): no skill text states how a landing-path conflict block is resolved, and nothing re-verifies the resolution's surviving intents. A base-side hunk pick resurrects the branch's pruned entry (witnessed 2026-10-18: landing aca98a237 carried the receipt with no removal; repair c3a283738 completed it), a branch-side pick reverts a peer's landed line (witnessed 2026-10-09, caught by hand), and the prune audit is silent on both because it audits removals, not dropped removal intents.

After (this plan): the resolver keeps both intents per conflict block; after any merge or rebase whose result feeds the landing's gates (composed before lock acquisition or inside the critical section) it re-verifies the merged tree directly (each pruned heading absent, each base-side addition present) before the gates next run, and re-runs the receipt audits against the post-merge bytes; and the prune audit warns when a commit adds a receipt with no removal in the same log, whose firing surface on resolution paths is that re-run, so the witnessed intermediate shape becomes mechanically visible while the class stays warning-only.

Edge cases: the sanctioned re-apply repair shape stays accepted (the removal commit classifies clean via the ledger lookup while the repair window's receipt commit warns once, the priced shape); overlapping same-line edits merge line-by-line keeping foreign lines; the duty covers the designed re-land path (the still-held-lock merge) and the sanctioned pre-lock compositions alike; both skill homes carry one shared wording with execute-plan canonical and the plans closeout mirroring by reference.

## Outcome

Make the witnessed conflict-resolution failure mode a defined, verified discipline instead of an undefined clause and per-run manual luck.

- Every conflict block resolved inside the landing critical section preserves both sides' intents, and the resolver proves each destructive intent on the merged tree before the landing continues.
- The witnessed intermediate shape (a receipt added with no removal) becomes mechanically visible through the prune audit's warning class, warning-only per the machinery admission protocol, with the duty's post-resolution receipt-audit re-run as the warning's firing surface on resolution paths.
- Ordinary preservation holds: the audit's fail classes, the re-apply repair shape, the reverse-squash and compare-and-swap gates, and the helper's outcome contract keep their bytes and verdicts.

Gate delta: adds the union rule and the post-resolution re-verification duty as operative text in the landing critical section (canonical home `agents/skills/execute-plan/SKILL.md`, mirror reference in the plans skill's landing closeout), adds the audit's warning-only receipt-without-removal finding class, and revises the origin row's superseded Expected remedy in place; removes nothing from the skill texts (the landing critical section carries no existing conflict-content rule to replace; the undefined clause survives only in project lesson 6's narrative, whose cross-reference this plan refreshes as the corpus-side payment, declared in Review Scope), and the skill-text growth is priced by the entry's rejected alternatives and the second witness (base-side remedy superseded, status quo rejected at two witnesses, receipt-without-removal chosen over a new standalone validator as the smallest mechanical arm); the audit's existing fail classes and verdict lines keep their bytes.

Machinery admission: the text arms add no gate, validator, lock, ledger, or ceremony (they discipline an existing step and re-verify with direct greps); the warning class carries: incident link, the 2026-10-18 escape (landing aca98a237, repair c3a283738) plus the origin row's 2026-10-09 near-miss; expected catch, conflict-resolved landings carrying removals (two witnesses in nine days); false-positive cost, a spurious warning line on a log-touching commit, bounded by warning-only shaping (never blocks; the repair window's receipt-commit warning is the priced shape, fixture-pinned, while the removal commit classifies clean); sunset and review, the pre-registered registry-removal row (Task 3) names review by 2027-01-18 with promotion criteria (a true catch, then blocking promotion only with the operator's net-growth approval per the repository guidelines' Machinery admission protocol), and the row lands in the same change.

## Assumptions

- assume the discipline lands as operative text plus one warning-shaped audit class, not as a new script gate; basis: the smallest arm that removes the witnessed cost (the entry's price-the-witnessed-cost disposition), and the re-verification evidence is a direct grep needing no new tooling.
- assume the canonical home is the landing critical section paragraphs in `agents/skills/execute-plan/SKILL.md` and the plans skill's landing closeout carries a one-line mirror reference; basis: the repo's canonical-home-plus-mirror convention (the Budget gate precedent between the same two files).
- assume the orphan check is commit-scoped per log; basis: the audit already walks commit-by-commit over per-log diffs (prune_audit and walk_audit_commits read each commit's diff), so the repair shape and normal shape never false-flag.
- assume the origin row's Expected section is revised inside this plan's change; basis: the entry's scope arm, so no future reader follows the superseded base-side remedy while the row stays open.
- Sources inspected: not a tracker-linked request.
Decision points requiring a grill: the union-of-intents rule supersedes the origin row's base-side remedy on the second witness's evidence: user decision (the entry's Standing pre-authorization is none by design; this plan is the genuine authoring-side look; operator mandate via the investigated dispatch entry), docs/history/backlog/2026-10-09-rebase-conflict-side-selection-no-delta-verification.md plus docs/history/backlog/PLAN-PROMPTS.md entry landing-conflict-intent-union, 2026-10-18, Gist, Outcome, Tasks; the audit arm lands warning-only first: user decision (the machinery admission protocol's warning-only landing default), scripts/machinery_registry.json row in Task 3, 2026-10-18, Outcome, Tasks.

## Standing constraints

- No em dashes in committed files; the repository gate is `scripts/check-no-em-dash.sh`.
- Skill text stays tool-agnostic: describe behaviors by intent, never by tool names.
- The audit's existing output grammar keeps its bytes where this plan does not touch it: the PRUNE-OK, REMOVED-WITHOUT-WITNESS, and OUTCOME lines are unchanged; the summary line's only delta is an appended warnings count at line end; the warning class otherwise adds lines only.
- The reverse-squash gates, the merge-landing-lock mechanics, and `scripts/land_squash.sh` are untouched.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the audit test suite exits 0 with the new warning cases passing and every existing case passing unchanged.
- safety: the warning class never changes any exit code on its own; the duty's verification is evidence-positive (grep results), not judgment.
- clarity: one shared wording across both skill homes; the canonical home states the rule and the duty, the mirror routes to it.
- portability and hygiene: no tool-specific wording, no absolute personal paths, public-hygiene scan exits 0, em-dash scan exits 0 over the plan's added lines.

**Done when:**
- `agents/skills/execute-plan/SKILL.md` carries the union rule and the re-verification duty in the landing critical section, and `agents/skills/plans/SKILL.md`'s landing closeout carries the mirror reference.
- `scripts/check_prompt_log_origins.py` emits the receipt-without-removal warning, a warning-only run still exits 0 with `OUTCOME: pass`, and the existing suite passes unchanged.
- `scripts/machinery_registry.json` carries the pre-registered removals row and the origin row's Expected states the union rule.
- The full Validation Commands block exits 0.

**Ship when:**
- The next conflict-resolved landing in this repository applies the discipline and its run record names the post-resolution re-verification. Evidence owner: the user; closure: a live landing's record carries the re-verification line. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` *(edit: the landing critical section paragraphs only; all other regions frozen)*
- `agents/skills/plans/SKILL.md` *(edit: one mirror line in the landing closeout; all other regions frozen)*
- `scripts/check_prompt_log_origins.py` *(edit: the warning class)*
- `scripts/machinery_registry.json` *(edit: one pre-registered removals row)*
- `docs/history/backlog/2026-10-09-rebase-conflict-side-selection-no-delta-verification.md` *(edit: the Expected section only; all other regions frozen)*
- `docs/maintenance/development_lessons.md` *(edit: lesson 6's conflict-narrative sentence gains a pointer to the new operative rule, and lesson 93's scope and timing sentences widen to match it; all other regions frozen)*

**Tests:**
- `scripts/test_check_prompt_log_origins.py` *(edit: the warning-class cases)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`; reason: the helper's gates are untouched by design (Standing constraints), the discipline is text-level.
- `scripts/worktree_closeout_migrate.py`; reason: a different closeout gate, unaffected by the audit's log-diff walk.
- `docs/history/plans/completed/2026-09-26-release-skill.md`; reason: completed archive is immutable history, not a live contract.
- This plan file itself.

## Validation Commands

Pre-round gates at authoring: em-dash scan over the plan bytes 0 hits (fixer 0 substitutions), public-hygiene scan exit 0, `plan_readiness.py --pre-round` structural pass.

```bash
set -euo pipefail
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"

# 1. Declared files exist
test -f agents/skills/execute-plan/SKILL.md
test -f agents/skills/plans/SKILL.md
test -f scripts/check_prompt_log_origins.py
test -f scripts/test_check_prompt_log_origins.py
test -f scripts/machinery_registry.json

# 2. Full audit suite: new warning cases green, every existing case green
#    (the suite has no bare-python runner by design; run it through pytest)
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_prompt_log_origins.py -q

# 3. Warning class present (distinctive finding token; deleting the class
#    breaks this probe)
grep -qF 'RECEIPT-WITHOUT-REMOVAL' scripts/check_prompt_log_origins.py || { echo "FAIL: warning class missing"; exit 1; }

# 4. Union rule and duty in the canonical home (distinctive spans from the
#    normative rule lines; deleting either sentence breaks its probe)
grep -qF 'resolves by union of intents' agents/skills/execute-plan/SKILL.md || { echo "FAIL: union rule missing"; exit 1; }
grep -qF 'post-resolution re-verification' agents/skills/execute-plan/SKILL.md || { echo "FAIL: re-verification duty missing"; exit 1; }

# 5. Mirror reference in the plans closeout
grep -qF 'union-of-intents' agents/skills/plans/SKILL.md || { echo "FAIL: mirror reference missing"; exit 1; }

# 6. Origin row Expected states the union rule
grep -qF 'resolves by union of intents' docs/history/backlog/2026-10-09-rebase-conflict-side-selection-no-delta-verification.md || { echo "FAIL: origin row revision missing"; exit 1; }

# 7. Registry carries the pre-registered warning row (identity pin)
python3 - <<'PYEOF'
import json, sys
d = json.load(open("scripts/machinery_registry.json"))
rows = [r for r in d.get("removals", []) if r.get("id") == "script:check-prompt-log-origins-receipt-without-removal-warning"]
if not rows:
    print("FAIL: pre-registered warning removal row missing"); sys.exit(1)
r = rows[0]
if "2027-01-18" not in r.get("note", ""):
    print("FAIL: removal row lacks the review-by date"); sys.exit(1)
print("registry row ok")
PYEOF

# 8. Public hygiene over the full tree
bash scripts/scan-public-hygiene.sh

# 9. Em-dash ban over this change's added lines, scoped to the declared file
#    set (the repo-wide scan stays owned by the landing sweep's own gates;
#    the pathspec form fails closed on untracked or absent paths)
bash scripts/check-no-em-dash.sh added-lines --base main -- docs/history/plans/2026-10-18-landing-conflict-intent-union.md agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md scripts/check_prompt_log_origins.py scripts/test_check_prompt_log_origins.py scripts/machinery_registry.json docs/history/backlog/2026-10-09-rebase-conflict-side-selection-no-delta-verification.md docs/maintenance/development_lessons.md
```

### Task 1: Audit warning-class cases (RED first)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_check_prompt_log_origins.py` *(edit: new warning-class cases plus the fixture support they need)*

- [ ] Orphan-receipt fixture: a base..HEAD range whose one log-touching commit adds a `PLAN-PROMPTS-PRUNE:` receipt line and removes no entry expects a warning line naming the finding class and the log, exit 0, and the final `OUTCOME: pass` line unchanged [class: REPOSITORY_TEST]
- [ ] Summary-shape witness: the orphan fixture's output carries the warnings count appended at the summary line's end with every existing summary substring contiguous [class: REPOSITORY_TEST]
- [ ] Normal-shape witness: a commit carrying an entry removal plus its receipt expects no warning and the existing PRUNE-OK verdict line [class: REPOSITORY_TEST]
- [ ] Re-apply repair witness: a removal completing an earlier in-range commit's receipt expects the receipt-adding commit to warn once (the priced shape) and the repair commit's own classification to be PRUNE-OK via the ledger lookup with no warning attributable to the repair commit [class: REPOSITORY_TEST]
- [ ] Fail-class preservation: an existing removal-without-witness case still exits 1 with its verdict line unchanged [class: REPOSITORY_TEST]
- [ ] Per-log scoping: a receipt added to one rolling log while the same commit removes a sibling-log entry witnessed by that log's own ledger receipt expects exit 0, `OUTCOME: pass`, and exactly one warning naming the receipt's log [class: REPOSITORY_TEST]
- [ ] Run → expect RED through the venv pytest runner (`PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_prompt_log_origins.py -q`; a bare python3 run executes nothing by design): the warning-asserting cases (orphan-receipt, summary-shape, re-apply, per-log scoping) fail on the missing warning line while every existing case stays green [class: REPOSITORY_TEST]
- [ ] Commit: `test: prune-audit receipt-without-removal warning cases (RED)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Audit warning class (GREEN)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_prompt_log_origins.py` *(edit)*

Primary class anchors:
- `walk_audit_commits` in `scripts/check_prompt_log_origins.py`, the per-commit walk the orphan detection joins
- `prune_audit` in `scripts/check_prompt_log_origins.py`, the summary and exit owner the warning count extends

- [ ] Receipt-set computation in the walk: per log, the walk applies the unmodified ledger receipt regex to the per-log pre- and post-images it already loads (the diff helper's old and new text) and computes the added-receipt set [class: IMPLEMENTATION_REQUIRED]
- [ ] Orphan warning emission: a commit whose added-receipt set is non-empty while removing no entry from that same log appends one warning line naming the class `RECEIPT-WITHOUT-REMOVAL`, the commit, and the log; the check runs before the zero-removals early continue, whose existing classification stays byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] Warning-shaped exit: warnings alone keep exit 0 with `OUTCOME: pass`; the summary line gains the warnings count as an append at line end, keeping every existing summary substring contiguous; existing fail classes, verdict lines, and their bytes unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Grammar reuse: the receipt matcher is the existing ledger receipt regex applied to the per-log pre- and post-images, never a second pattern and never the raw patch text (the regex is line-start anchored) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN at this task point through the venv pytest runner: the full suite passes including the Task 1 cases [class: REPOSITORY_TEST]
- [ ] Commit: `feat: prune audit warns on receipt-without-removal commits` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Landing critical section text, registry row, origin row revision

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/SKILL.md` *(edit: the landing critical section paragraphs only)*
- `agents/skills/plans/SKILL.md` *(edit: one mirror line in the landing closeout)*
- `scripts/machinery_registry.json` *(edit: one pre-registered removals row)*
- `docs/history/backlog/2026-10-09-rebase-conflict-side-selection-no-delta-verification.md` *(edit: the Expected section only)*
- `docs/maintenance/development_lessons.md` *(edit: lesson 6's conflict-narrative pointer, and lesson 93's scope and timing sentences)*

- [ ] Union rule: the landing critical section paragraphs of both landing classes (the worktree-complete class and the primary-checkout class) gain the rule that each conflict block "resolves by union of intents", never by taking one side, with the branch-removal-stays-removed, base-addition-stays-added, and line-by-line-keeping-foreign-lines clauses [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-verification duty: the same paragraphs gain the "post-resolution re-verification" duty: after any merge or rebase whose result feeds the landing's gates, whether composed before lock acquisition or inside the critical section, and always before the landing gates next run, each pruned heading or removed span is re-grepped absent and each base-side addition present on the merged tree, citing project lesson 93 as the corpus home [class: IMPLEMENTATION_REQUIRED]
- [ ] Duty audit re-run and record: the same duty re-runs the landing's receipt audits against the post-merge bytes, and the landing record names the re-verification outcome whenever a conflict resolution composed with destructive intents in play [class: IMPLEMENTATION_REQUIRED]
- [ ] Lesson cross-reference payment: lesson 6's conflict-narrative sentence gains a pointer to the new operative rule, and lesson 93's scope and timing sentences widen to name pre-lock compositions and the gates-next-run timing, so the corpus wording and the operative rule stay on one wording (this is the corpus-side growth payment; no skill bytes are removed) [class: IMPLEMENTATION_REQUIRED]
- [ ] Mirror reference: the plans skill's landing closeout gains one line routing "union-of-intents" conflict resolutions to the canonical paragraphs (the canonical-home-plus-mirror convention) [class: IMPLEMENTATION_REQUIRED]
- [ ] Ordinary text preservation: the compare-and-swap, base-freshness, and reverse-squash sentences, and the pre-rider prune-audit invocation sentence, in the edited region keep their bytes [class: IMPLEMENTATION_REQUIRED]
- [ ] Pre-registered removals row: `scripts/machinery_registry.json` gains exactly one `removals` row with id `script:check-prompt-log-origins-receipt-without-removal-warning`, kind `script`, disposition `delete`, empty `paths` and `tests` lists (the pre-registration convention; the warned class lives on), and a witness block naming the incident refs; the JSON must still parse [class: IMPLEMENTATION_REQUIRED]
- [ ] Removals row note: the row's note carries the review-by date 2027-01-18 and the promotion criteria (a true catch, then blocking promotion only with the operator's net-growth approval) [class: IMPLEMENTATION_REQUIRED]
- [ ] Origin row Expected revision: the Expected section states that each conflict block "resolves by union of intents" plus the post-resolution re-verification duty in place of the superseded base-side remedy, with a one-line supersession witness naming the second witness and this plan [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: union-of-intents landing discipline, warning row pre-registration, origin row revision` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Full validation sweep

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none new; runs the Validation Commands block over the landed tree

- [ ] Run → expect GREEN at this task point (all earlier tasks landed): the complete Validation Commands block exits 0; record the outcome in the execution log [class: REPOSITORY_TEST]
- [ ] If the sweep required any tracked-file fixes, commit them as `test: landing conflict discipline validation sweep green`; on a first-pass green no commit is made and instead `git status --porcelain --untracked-files=no` restricted to this plan's declared file set must be empty [class: REPOSITORY_TEST]
