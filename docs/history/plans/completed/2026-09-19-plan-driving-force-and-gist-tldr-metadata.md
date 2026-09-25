# Plan: Plans declare a driving force; Gist opens with a TLDR

Backlog origin: docs/history/backlog/2026-09-18-plan-driving-force-and-gist-tldr-metadata.md (stays in place while this plan is open).
Driving force: external (Andrey's 2026-09-18 post-mortem requirement, captured in the backlog item: a plan's motivating force must be declared so triage and park decisions are mechanical). Justification for a non-principle force: the change is small metadata plumbing whose consumer is maintenance triage, park-guard classification, and review pricing; park-triage would not take it under either class: not process-cosmetic, because the declared force is the exact input the park-guard classifier and deferred/ triage read (the field changes triage outcomes, it does not only tidy them), and not machinery-growth, because it adds three prose lines and no runtime machinery while directly closing the mismatch that let the legacy verdict-grammar plan resist triage.

## Terms

- **Driving force**: the closed-taxonomy tag a plan declares for what motivates it (`efficiency` | `token-usage` | `simplicity` | `code-quality` | `new-capability` | `external`); compound forces are ranked primary + secondary.
- **Certified plan**: any plan whose latest review round's stats sidecar records a `source_digest` matching the plan's current bytes; the set the retrofit rule and the byte-stability claims protect.
- **Metadata block**: the group of declared header lines (Backlog origin, Driving force, External gate) that a plan declares once in its header region; this plan owns the block's membership definition.

## Assumptions

- assume the driving-force taxonomy is the backlog item's closed set (`efficiency` | `token-usage` | `simplicity` | `code-quality` | `new-capability` | `external`), compound forces allowed as ranked primary + secondary; basis: backlog item's suggested fix.
- assume validator enforcement in scripts/plan_readiness.py is OUT of scope for this first pass (skill text + review findings only); basis: backlog item's explicit enforcement note.
- assume the retrofit rule: existing certified plans are never rewritten solely to add the fields; they gain them at the next natural edit or deferred/ revival; basis: backlog item.
- assume the `External gate:` line from docs/plans/2026-09-19-maintenance-park-guard-externally-gated-plans.md joins this metadata block (one block, not two separately-owned lines): this plan defines the block's membership and the park-guard plan's Assumptions already declare its line folds here; basis: the park-guard plan's coordination assumption.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: plans declare one driving-force line and open the Gist with a one-line TLDR, so triage, pricing, and deferral for the `external`-forced work this plan carries read off the document instead of being inferred from prose.

What changes: the plans skill's plan template gains a `Driving force: <tag>` metadata line (beside Backlog origin) with a closed taxonomy and a justification rule for non-principle forces, and the `## Gist & Examples` section gains a required first line `TLDR: <what changes>, <why, naming the driving force>.`. The Step 1.4 confirmation renders both so the author confirms them; the maintenance authoring blueprint fills both without prompting; review-plan flags missing or incoherent declarations as ordinary findings. The `External gate:` line becomes a member of the same metadata block, so plans declare one block.

Example: this plan's own header carries `Driving force: external (...)` with a justification, and its Gist opens with the TLDR line above; a hypothetical `simplicity`-forced plan that in fact adds a new abstraction layer gets flagged by review-plan because the declared force contradicts the content.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every newly authored plan carries the force line (with justification when the force is not one of the four principles) and a Gist TLDR; the Step 1.4 confirmation renders both.
- consistency: one metadata block; the park-guard `External gate:` line is documented as a member, not a competing line.
- non-regression: no existing certified plan changes bytes solely because of this plan; scripts/plan_readiness.py is untouched.

**Done when:**
- All Task greps pass (fail-closed, per Validation Commands).
- Each task commit touches exactly its declared Files list (witnessed by the commit-scope gates); no validator or certified-plan bytes are touched by this execution's commits; concurrent peer commits on the shared branch are outside this plan's Done-when by construction.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] The field proves stable across several authored plans; a later pass may add a plan_readiness schema check. Evidence owner: Andrey; closure: a follow-up plan exists or the decision is recorded.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (plan template metadata block, Gist TLDR rule, Step 1.4 confirmation, retrofit rule)
- `agents/skills/maintenance/prompt-templates.md` (authoring blueprint fill-ins and documented-deviations entry)
- `agents/skills/review-plan/SKILL.md` (declaration findings and pricing rule)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: validator enforcement is explicitly out of scope for the first pass.
- Any file under `docs/plans/completed/` or `docs/plans/deferred/`; reason: the retrofit rule forbids byte-only rewrites of certified plans.

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)"
PLANS=agents/skills/plans/SKILL.md
TMPL=agents/skills/maintenance/prompt-templates.md
REV=agents/skills/review-plan/SKILL.md
fail() { echo "GATE FAIL: $1" >&2; exit 1; }

# Task 1 gates: template metadata line, taxonomy, justification rule, TLDR, confirmation rendering.
grep -q "Driving force: <tag>" "$PLANS" || fail "template force line missing"
grep -q "new-capability" "$PLANS" || fail "taxonomy missing"
grep -q "one-line justification" "$PLANS" || fail "justification rule missing"
grep -q "TLDR: <what changes>" "$PLANS" || fail "Gist TLDR requirement missing"
grep -q "declared driving force and the TLDR" "$PLANS" || fail "Step 1.4 force/TLDR rendering missing"
grep -q "Backlog origin: <path>" "$PLANS" || fail "template backlog-origin line missing"
grep -q "between the title line and the first .## . heading" "$PLANS" || fail "header-region placement constraint missing"
grep -q "is a member of the same block" "$PLANS" || fail "External gate membership missing"
grep -q "never rewritten solely" "$PLANS" || fail "retrofit rule missing"

# Exactly-once count gates, scoped to the template block region (fail-closed extraction;
# no fence literal in this block per the no-triple-backtick rule). The placeholder
# literals land ONLY in the template block; other normative surfaces reword.
BT="$(printf '\140\140\140')"
TEMPLATE="$(awk -v bt="$BT" 'index($0, bt "markdown")==1 {f=1; next} f && $0==bt {exit} f' "$PLANS")"
test -n "$TEMPLATE" || fail "template block not found"
test "$(printf '%s\n' "$TEMPLATE" | grep -cF 'Driving force: <tag>')" -eq 1 || fail "force line not exactly once in template"
test "$(printf '%s\n' "$TEMPLATE" | grep -cF 'TLDR: <what changes>')" -eq 1 || fail "TLDR line not exactly once in template"

# Task 2 gates: authoring blueprint fills both, deviation registered.
grep -q "Driving force:" "$TMPL" || fail "blueprint force fill missing"
grep -q "TLDR:" "$TMPL" || fail "blueprint TLDR fill missing"
grep -q "Driving force: <tag>" "$TMPL" || fail "blueprint force literal missing"
grep -q "TLDR: <what changes>" "$TMPL" || fail "blueprint TLDR literal missing"
grep -q "driving-force and Gist-TLDR fill" "$TMPL" || fail "deviation entry missing"
grep -q "declared driving force that contradicts" "$REV" || fail "boundary sixth family missing"

# Task 3 gates: review findings with the pricing rule.
grep -q "a missing driving-force line" "$REV" || fail "review finding rule missing"
grep -q "non-blocking by default" "$REV" || fail "shape-defect default pricing missing"
grep -q "contradicts the plan" "$REV" || fail "contradiction pricing missing"

# Commit-scope witness for the Done-when criterion: each of this execution's three task
# commits touches exactly its declared Files list (attributable by subject; concurrent
# peer commits on the shared branch are invisible to this gate by construction).
BASE="$(cat docs/tmp/dfm-base-sha.txt)"
commit_scope_ok() {
  subj="$1"; shift
  c="$(git log -F --grep="$subj" --format=%H "$BASE"..HEAD | tail -1)"
  test -n "$c" || fail "task commit missing: $subj"
  for f in "$@"; do
    git show --name-only --format= "$c" | grep -qxF "$f" || fail "commit $c missing declared file $f"
  done
  EXTRA="$(git show --name-only --format= "$c" | grep -v '^$' | grep -vxF -f <(printf '%s\n' "$@") || true)"
  test -z "$EXTRA" || fail "commit $c touches undeclared files: $EXTRA"
}
commit_scope_ok "skills: plans declare driving force and Gist TLDR" agents/skills/plans/SKILL.md
commit_scope_ok "maintenance: authoring blueprint fills driving force and TLDR" agents/skills/maintenance/prompt-templates.md
commit_scope_ok "review-plan: price driving-force declaration defects" agents/skills/review-plan/SKILL.md

# Keep-green regression witness: the maintenance pins suite pins prompt-templates.md's
# authoring placeholder set exactly; the body-sentence form of Task 2 must not move it.
bash scripts/check_maintenance_pins.sh || fail "pins suite drifted"
```

Gate provenance: every new-string gate is RED today (none of the strings exist in the three files; first gate measured firing with exit 1 at authoring) and flips GREEN exactly when the tasks land; the membership, retrofit, and pricing greps are new-string gates of the same class; the count gates flip GREEN only under the single-landing-site prescription (placeholder literals land ONLY in the template block; the Step 1.4 rendering and Rules prose reword); the commit-scope gates run last and require BASE (recorded before Task 1's first commit) plus the three landed commits, so they are RED until execution completes them; the final pins-suite invocation is a keep-green witness, GREEN today and required to stay GREEN (it protects the authoring placeholder set the body-sentence form of Task 2 must not move). The gates deliberately measure committed history by subject, never working-tree state, so concurrent peer edits cannot fail it (r2 F2). The exactly-once count gates cover the template's header-and-Gist region (the extraction's covered sub-region, where both prescribed placeholder lines land); the whole-file presence needles cover the rest.

### Task 1: Plans skill metadata block and TLDR

Files:
- `agents/skills/plans/SKILL.md`

- [x] In the Plan Format template block, add the metadata line `Backlog origin: <path>` (promoting the existing prose convention into the template) and, beside it, the line `Driving force: <tag>` with the closed taxonomy (`efficiency` | `token-usage` | `simplicity` | `code-quality` | `new-capability` | `external`; `external` must cite its source), compound forces as ranked primary + secondary, and the justification rule: a plan whose force is not one of the four driving principles carries a one-line justification naming why it is implemented anyway and why park-triage would or would not take it. [class: IMPLEMENTATION_REQUIRED]
- [x] State the metadata block's placement constraint and membership in the template block: the block sits in the header region between the title line and the first `## ` heading (the region the maintenance park-guard classification scans), and the `External gate:` line is a member of the same block; plans declare one block, not separately-owned lines. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the Gist TLDR rule: the first line of `## Gist & Examples` is `TLDR: <what changes>, <why, naming the driving force>.` (one or two phrases); everything already in the section stays below it. The placeholder literals (`Driving force: <tag>`, `TLDR: <what changes>`) land ONLY in the template block; the Rules prose and Step 1.4 rendering reword so the count gates stay exactly-once. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Step 1.4 confirmation block to render the declared driving force and the TLDR so the author confirms them (prose wording; do not repeat the template placeholder literals). [class: IMPLEMENTATION_REQUIRED]
- [x] Add the retrofit rule: existing certified plans (see Terms) are never rewritten solely to add the fields; they gain them at the next natural edit or at deferred/ revival. [class: IMPLEMENTATION_REQUIRED]
- [x] Before the first commit, record the current HEAD sha to `docs/tmp/dfm-base-sha.txt` (one line, `git rev-parse HEAD`); the commit-scope gates read it as BASE. [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: the template's header-and-Gist region names each of the two new required lines exactly once; backed by the count gates in Validation Commands (`grep -cF ... -eq 1` over the extracted template region for `Driving force: <tag>` and `TLDR: <what changes>`); whole-file presence is covered by the dedicated greps. [class: REPOSITORY_TEST]
- [x] Commit: `skills: plans declare driving force and Gist TLDR` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Maintenance authoring blueprint fill-ins

Files:
- `agents/skills/maintenance/prompt-templates.md`

- [x] In the authoring blueprint, add instruction sentences INSIDE the fenced authoring body (not new `{placeholder}` field lines: the authoring section must gain no new placeholder tokens, because scripts/check_maintenance_pins.sh pins that placeholder set exactly), prescribed verbatim as: "Declare the plan's driving force as its `Driving force: <tag>` header line (closed taxonomy and the non-principle justification rule per the plans skill template) and open `## Gist & Examples` with the `TLDR: <what changes>, <why, naming the driving force>.` line, without prompting." [class: IMPLEMENTATION_REQUIRED]
- [x] Register the blueprint change in the documented-deviations header list with a one-line rationale (keeping the copied-verbatim provenance claim true); the entry names the change `driving-force and Gist-TLDR fill` so the validation gate can pin it. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: authoring blueprint fills driving force and TLDR` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Review-plan declaration findings

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] Add the finding rule: a missing driving-force line, a missing Gist TLDR, a force outside the taxonomy, a non-principle force without its one-line justification, or a force that contradicts the plan's actual content (declared `simplicity`, adds machinery) is a finding. Pricing: missing/coherent-shape defects are ordinary (non-blocking by default) findings; a force that contradicts the plan's content is blocking. [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the Plan-review boundary paragraph's closed blocker list to add the sixth family, verbatim: "a declared driving force that contradicts the plan's actual content" (so the Task 3 pricing and the boundary definition agree in one normative file). [class: IMPLEMENTATION_REQUIRED]
- [x] Witness: the rule names the pricing split explicitly (a force that contradicts the plan is blocking; shape defects are `non-blocking by default`) so the next review panel can apply it without inference; backed by the three dedicated Task 3 greps in Validation Commands (findings list, default pricing, contradiction pricing). [class: REPOSITORY_TEST]
- [x] Commit: `review-plan: price driving-force declaration defects` [class: IMPLEMENTATION_REQUIRED]

## Residual review findings (at-cap finalize, 2026-09-19)

Review loop r1-r5 (artifacts at docs/reviews/2026-09-19-plan-review-plan-driving-force-and-gist-tldr-metadata-r1..r5.md). Every blocking finding from r1-r4 and r5's two (F1 boundary-paragraph reconciliation: the sixth blocker family is now prescribed verbatim; F2 Task 2's instruction sentence is now prescribed verbatim with both pinned literals quoted) were folded. The cap was reached, so the final fold set has NOT been re-reviewed by a fresh round: the latest sidecar (r5) digest precedes the final plan bytes, so `plan_readiness.py` reports the sidecar stale and the execution PRE-STEP must run a fresh certification round before dispatch. No other residuals are open.

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-18-plan-driving-force-and-gist-tldr-metadata.md: disposition folded into 2026-09-19-plan-driving-force-and-gist-tldr-metadata.md (2026-09-25); per-item file deleted.
