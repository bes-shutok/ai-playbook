# Plan: SOT unification: living-doc capability names, wire SOT, and grill escalation

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-02-living-docs-capability-names-and-openapi-wire-sot.md`
- `docs/history/backlog/2026-09-04-sot-unification-review-and-plan-workflows.md`

## Terms

- **SOT (source of truth):** the one document that owns a rule; peers hold pointers or audience-specific deltas, never full restatements.
- **Authority role:** the distinct owner class of a statement: OpenAPI wire shape, workflow/domain Layer 2 rule, API example, glossary entry, ADR, historical (Layer 3) document. Cross-authority references are pointers, not second SOTs.
- **Capability name:** a durable name for a capability (plus optional RFC/ADR link) used in living Layer 1/2 prose instead of an issue key.
- **Ticket-as-gate:** living prose that gates behavior on an issue key (`PROJ-1234`); the key churns, the capability does not.
- **Thin-index:** a catalog surface that points at OpenAPI (pointer plus audience-specific delta) instead of restating wire schemas/enums/status maps.
- **Fan-out finding:** one staged finding naming the canonical home for a rule restated on N surfaces, instead of N sibling findings.
- **contract-docs:** the review worker that loads the `documentation` lens (plus `consistency` for plans/RFCs) per `review-panel-selection.md`.
- **grill-with-docs:** the shared escalation interview (`grilling` + inline `domain-modeling`) that resolves unclear points one question at a time while updating glossary/ADRs.

## Assumptions

- assume a single plan covers both backlog items; basis: user tasking 2026-09-04, same family with overlapping anchors.
- assume no mirror-sync task is needed; basis: `claude/skills -> ../agents/skills` symlink verified on disk 2026-09-04 (there is no copied skill tree to sync).
- assume `doing-code-review/SKILL.md` and `receiving-review/SKILL.md` need no edits; basis: verified 2026-09-04; receiving-review already carries the fan-out consolidation fix path and the sibling-doc-restatement backlog-by-default bound, doing-code-review §4.9.2 doc-scope rules are already pointer-based (the backlog item 1 touch there is explicitly conditional "only if residual wording still pushes fix every catalog table", which it does not).
- assume this is a docs/skills-only change, so tasks use concise `- [ ]` action items with fail-closed grep validation instead of RED/GREEN cycles; basis: plans skill non-behavior-change rule.
- assume the execute-plan ambiguity pause surfaces `grill-with-docs` to the user (interview is interactive); basis: backlog item text plus the existing Step 1.3b checkpoint pause semantics.
- assume both backlog items stay under `docs/history/backlog/` while this plan is open and move to `docs/history/backlog/completed/` only at plan completion; basis: plans skill Backlog origin rule.

## Design Invariants (CR Guard)

Decisions from the completed 2026-09-01 single-SOT item and its successors that this plan must not compromise:

1. **Fan-out staging stays one finding.** `review-agents/review-panel-selection.md` tiered-ownership section already requires: before staging multiple findings that one rule's restatement explains, list the living restatements and stage one fan-out finding naming the canonical home. This plan extends the example classes; it must not reintroduce per-surface findings.
2. **Address-side bound untouched.** `receiving-review` sibling-doc-restatement backlog-by-default and the fix path (canonical home first, peers become pointers) stay as they are; this plan only verifies them.
3. **Authority roles stay distinct.** Neither backlog item turns every documentation reference into a second SOT: wire-contract SOT, workflow/domain SOT, API examples, glossary, ADR, and historical-document roles remain separate authorities; legitimate audience-specific content is never flagged as duplication.
4. **Extend existing lenses, no new agent.** Both changes land in the existing `contract-docs` worker lenses (`documentation.md`, `consistency.md`); do not invent a separate doc-review agent (backlog item 1 non-goal).
5. **Public hygiene.** No real employer ticket prefixes, private service names, or concrete product endpoint paths in skill bodies; use `PROJ-1234` and generic capability labels.
6. **One escalation workflow.** `grill-with-docs` stays the single shared escalation contract for unclear SOT ownership; no parallel mechanism.

## Gist & Examples

The 2026-09-01 single-SOT work made review converge duplicate rule restatements onto one canonical home (fan-out staging in `review-panel-selection.md`, pointer-conversion fix path in `receiving-review`, Phase 3 backlog-by-default in `execute-plan`). Two residual failure modes still regenerate churn, and no workflow skill escalates unclear ownership:

1. **Ticket keys as living gates.** Layer 1/2 prose still uses issue keys ("undeployed until `PROJ-1234`"). When the ticket closes or renumbers, every living surface churns and review stages "stale ticket" findings that are not contract defects.
2. **Caller catalogs as a second wire SOT.** Rich request/response tables in maintenance catalogs duplicate OpenAPI. Review currently tends to stage "update the catalog table to match" (one finding per restated row) instead of collapsing the catalog to a thin index.
3. **No escalation path.** `plans` has a generic Phase 1 confidence gate (it can route to `grill-with-docs`), but SOT ownership / document role / content placement are not named as unclear points, and `execute-plan` has no ambiguity pause at its documentation checkpoint (Step 1.3b), so an unclear placement can be resolved by duplicating prose.

Example, before: catalog rows restate an enum; review stages five Medium "docs disagree" findings, one per row. After: the `documentation` lens recognizes the authority conflict and stages one finding: "catalog is second wire SOT; thin-index to OpenAPI" (pointer plus audience-specific delta), and `consistency` classifies the same shape as wire-contract duplication when reviewing artifacts. Example, before: a plan cannot tell whether a rate-limit rule belongs in OpenAPI or the Layer 2 domain topic, guesses, and duplicates prose. After: `plans` treats SOT ownership as a first-class unclear point (grill before writing), and `execute-plan` Step 1.3b pauses for `grill-with-docs` instead of editing docs on a guess.

Non-goals (from the backlog items): no deletion of caller catalogs; issue keys stay legal in Layer 3 history, plans, backlog, and tracker workflow; no new doc-review agent; no real ticket prefixes/service names/endpoint paths in skill bodies.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every touch-list row lands in its named file; each prescribed anchor span exists exactly once (Validation Commands block exits 0)
- consistency: integration points are bidirectional and verified against the peer skill's actual steps (`documentation.md` ↔ `review-confluence-doc`; `grill-with-docs` ↔ `execute-plan`)
- hygiene: `scan-public-hygiene.sh` exits 0; no machine-specific absolute paths; `PROJ-1234` placeholders only
- maintainability: no duplicated lens prose across orchestrators: `review-confluence-doc` points at `review-agents/documentation.md` gates instead of restating them

**Done when:**
- All task checkboxes `[x]`; Validation Commands block exits 0 from the repo root
- One fresh review of the final plan digest reports `ready=yes` with zero unresolved blocking findings

**Ship when:**
- A later real review/plan session demonstrates the behavior: a catalog-vs-OpenAPI or ticket-as-gate case produces one fan-out finding naming the canonical home, and an unclear-ownership case routes to `grill-with-docs` before documentation is written or edited. (Human-observed adoption; prose only.)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill/instruction files):**
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/consistency.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`
- `agents/skills/doc-hierarchy/company-decisions.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/grill-with-docs/SKILL.md`
- `agents/skills/review-confluence-doc/SKILL.md`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/doing-code-review/SKILL.md`, `agents/skills/receiving-review/SKILL.md`; reason: verified conformant 2026-09-04 (fan-out consolidation fix path, sibling-doc-restatement bound, §4.9.2 doc-scope rules already pointer-based); backlog item 1 marks them conditional and the condition is false.
- `README.md`; reason: no skill name, path, or usage change (no new skill, no renamed catalog entry).
- `agents/skills/docs-branch/SKILL.md`, `docs/plans/2026-09-03-docs-branch-temp-file-hygiene.md`, and any other file with uncommitted peer-session edits at execution time; reason: foreign in-flight work from a parallel session; never edit or commit.
- `claude/skills/`; reason: symlink to `../agents/skills` (verified 2026-09-04), not a copied tree; nothing to sync.

## Validation Commands

Run from inside the repo (the block re-anchors itself to the repo root). Fail-closed: a missing span, wrong count, missing region anchor, forbidden match, or hygiene failure aborts non-zero. Each pinned span is prescribed verbatim in the task that lands it; the `PROJ-1234` literal in prescribed prose is an intentional generic placeholder, and the `/Users/` sweep is a machine-specific-absolute-path ban.

```bash
#!/usr/bin/env bash
set -u
REPO="$(git rev-parse --show-toplevel)" || { echo "FATAL: not inside a git repo"; exit 1; }
cd "$REPO" || exit 1

expect_span_once() { # <file> <fixed-string span pinned from the task prescription>
  local f="$1" s="$2" n
  if ! test -f "$f"; then echo "MISSING FILE: $f"; exit 1; fi
  n="$(grep -oF -- "$s" "$f" | wc -l | tr -d ' ')"
  if [ "$n" -ne 1 ]; then echo "SPAN COUNT $n (want 1) in $f: $s"; exit 1; fi
}

# Task 1: review-agents lenses
expect_span_once agents/skills/review-agents/documentation.md "prefer a durable capability name plus an optional RFC/ADR link"
expect_span_once agents/skills/review-agents/documentation.md "catalog is second wire SOT; thin-index to OpenAPI"
expect_span_once agents/skills/review-agents/documentation.md "cross-authority references are pointers, not second SOTs"
expect_span_once agents/skills/review-agents/documentation.md "stage one consolidation finding that names the proposed canonical owner"
expect_span_once agents/skills/review-agents/consistency.md "Ticket-as-gate drift"
expect_span_once agents/skills/review-agents/consistency.md "thin-indexes the catalog to the OpenAPI definition"
expect_span_once agents/skills/review-agents/review-panel-selection.md "OpenAPI-vs-catalog wire duplicates"

# Task 1 placement: Living-doc gates sits after gate 5 content, before Outdated heading
DG=agents/skills/review-agents/documentation.md
l_gate5="$(grep -nF '| **Plan / RFC prose** |' "$DG" | cut -d: -f1)"
l_living="$(grep -nF '### Living-doc gates: capability names, wire SOT, and consolidation' "$DG" | cut -d: -f1)"
l_outdated="$(grep -nF '### Outdated documentation: remove or freeze' "$DG" | cut -d: -f1)"
if { [ -n "$l_gate5" ] && [ -n "$l_living" ] && [ -n "$l_outdated" ] && [ "$l_gate5" -lt "$l_living" ] && [ "$l_living" -lt "$l_outdated" ]; }; then :; else
  echo "Living-doc gates placement wrong in $DG"; exit 1
fi

# Task 2: doc-hierarchy upkeep + decisions
expect_span_once agents/skills/doc-hierarchy-upkeep/SKILL.md "thin-index caller catalogs"
expect_span_once agents/skills/doc-hierarchy-upkeep/SKILL.md "No new issue-key gates in Layer 1/2"
expect_span_once agents/skills/doc-hierarchy/company-decisions.md "caller catalogs thin-index to it"
expect_span_once agents/skills/doc-hierarchy/company-decisions.md "ticket churn never churns living docs"

# Task 3: plans authoring + confidence gate
expect_span_once agents/skills/plans/SKILL.md "SOT ownership is a first-class unclear point"
expect_span_once agents/skills/plans/SKILL.md "do not list every caller catalog as a full-text edit target"

# Task 4: execute-plan checkpoint pause + integration entry (region-scoped)
DOC=agents/skills/execute-plan/SKILL.md
grep -qF "### Step 1.3b:" "$DOC" || { echo "MISSING ANCHOR: Step 1.3b heading"; exit 1; }
grep -qF "### Step 1.4:" "$DOC" || { echo "MISSING ANCHOR: Step 1.4 heading"; exit 1; }
awk '/^### Step 1.3b:/{f=1} /^### Step 1.4:/{f=0} f' "$DOC" \
  | grep -qF "pause and run \`grill-with-docs\` with the user" \
  || { echo "Step 1.3b missing grill-with-docs pause"; exit 1; }
awk '/^### Step 1.3b:/{f=1} /^### Step 1.4:/{f=0} f' "$DOC" \
  | grep -qF "This pause applies on every repo" \
  || { echo "Step 1.3b missing repo-scope boundary for the grill pause"; exit 1; }
awk '/^## Integration Points/{f=1} f' "$DOC" \
  | grep -qF "pauses for the interview instead of allowing duplicated or contradictory documentation edits" \
  || { echo "execute-plan Integration Points missing grill-with-docs invocation/pause semantics"; exit 1; }
expect_span_once agents/skills/grill-with-docs/SKILL.md "(Layer 2 documentation checkpoint) invokes this skill"

# Task 5: review-confluence-doc consolidation finding
expect_span_once agents/skills/review-confluence-doc/SKILL.md "#### 4.4.1 Duplicated normative prose (SOT consolidation)"
expect_span_once agents/skills/review-confluence-doc/SKILL.md 'Full lens gates: `review-agents/documentation.md`'
expect_span_once agents/skills/review-confluence-doc/SKILL.md "replace peer copies with audience-specific pointers or deltas"

# Forbidden: machine-specific absolute paths in the nine touched files
for f in \
  agents/skills/review-agents/documentation.md \
  agents/skills/review-agents/consistency.md \
  agents/skills/review-agents/review-panel-selection.md \
  agents/skills/doc-hierarchy-upkeep/SKILL.md \
  agents/skills/doc-hierarchy/company-decisions.md \
  agents/skills/plans/SKILL.md \
  agents/skills/execute-plan/SKILL.md \
  agents/skills/grill-with-docs/SKILL.md \
  agents/skills/review-confluence-doc/SKILL.md; do
  if ! test -f "$f"; then echo "MISSING FILE: $f"; exit 1; fi
  if grep -n "/Users/" "$f"; then echo "FORBIDDEN absolute path in $f"; exit 1; fi
done

# Public hygiene scan (exit 0 required), anchored to the repo root
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" )
rc=$?
if [ "$rc" -ne 0 ]; then echo "HYGIENE SCAN FAILED rc=$rc"; exit 1; fi

# Task 6: the five per-task commits exist on the current branch (fail-closed
# on a missing task commit subject; a foreign commit with a byte-identical
# subject would also satisfy this grep; accepted residual, subjects are
# specific enough that collision is not a practical risk)
for s in \
  "review-agents: stage ticket-as-gate and wire-catalog duplicates as SOT fan-out classes" \
  "doc-hierarchy: wire-ownership and capability-name upkeep rules" \
  "plans: SOT-ownership confidence trigger and contract Files: guidance" \
  "execute-plan: pause for grill-with-docs on unclear documentation SOT" \
  "review-confluence-doc: SOT consolidation finding for duplicated normative prose"; do
  git log --format=%s | grep -qF -- "$s" || { echo "MISSING COMMIT: $s"; exit 1; }
done

echo "ALL VALIDATION CHECKS PASSED"
```

Fold maintenance (applies when this plan is edited, not an implementer task): after any fold that edits a task prescription or a pinned span, re-run the mechanical pin-vs-prescription audit (every pinned span must occur exactly once in its target file (the block enforces this) and verbatim in its task text) plus `bash -n` on this block. Note: the two Task 5 body-span lines, the Task 1 placement ordering check, and the `grep -oF` occurrence-count change in `expect_span_once` were added by code-review r1 hardening, not by task folds; their pins are audited the same way. The Task 5 prescription body was superseded by the r1/r2 folds (authority-roles bullet removed; trigger bullet reworded to point at the Living-doc gates); the fenced block now mirrors the shipped 4.4.1 body and the pins remain valid. The Task 1 review-panel-selection prescription was synced to the shipped fan-out sentence at r3 (r1 canonical-citation clause plus r3 wording sync), so the plan quote and the shipped text stay verbatim-identical.

### Task 1: review-agents lenses: stage the two residual classes as fan-out

Files:
- `agents/skills/review-agents/documentation.md`
- `agents/skills/review-agents/consistency.md`
- `agents/skills/review-agents/review-panel-selection.md`

- [x] In `documentation.md` Phase 2, insert a new subsection **"Living-doc gates: capability names, wire SOT, and consolidation"** as a new `###` section located between gate 5 ("Language and doc-type conventions", ending with its doc-type table) and the existing `### Outdated documentation: remove or freeze` heading. Do not insert it inside the numbered Decision-order gate sequence 1–5: the gates are ordered and applied "stop at the first applicable outcome", so a new list between gates 3 and 4 would break that contract. The subsection carries these checks (pattern tags `documentation#prose-<slug>`):
  - **Ticket-as-gate:** "Living Layer 1/2 prose must not use an issue key (for example `PROJ-1234`) as the primary gate label; prefer a durable capability name plus an optional RFC/ADR link, and keep issue keys in Layer 3 history, plans, backlog, and tracker workflow surfaces."
  - **Second wire SOT:** "When a caller catalog restates OpenAPI schemas, enums, or status maps, stage `catalog is second wire SOT; thin-index to OpenAPI` (replace restated tables with a pointer plus audience-specific delta), not `update the catalog table to match`."
  - **Authority roles:** "OpenAPI wire shape, workflow/domain Layer 2 rules, API examples, glossary entries, ADRs, and historical documents are separate authorities; duplicated normative prose within one authority consolidates to its owning document, while cross-authority references are pointers, not second SOTs. Do not flag legitimate audience-specific content as duplication."
  - **Consolidation finding shape:** "When the same normative workflow rule appears in several living documents, stage one consolidation finding that names the proposed canonical owner from the documentation hierarchy and replaces peer copies with audience-specific pointers or deltas."
- [x] In `consistency.md` "Source-of-truth drift", add two numbered classes:
  - "Ticket-as-gate drift: a living artifact gates behavior on an issue key (for example `PROJ-1234`) whose churn is unrelated to the capability it names; stage one SOT-drift finding proposing the durable capability name, not per-surface staleness findings."
  - "Wire-contract duplication: a caller catalog restates OpenAPI schemas, enums, or status maps; stage one fan-out finding that thin-indexes the catalog to the OpenAPI definition, not one finding per restated row."
- [x] In `review-panel-selection.md` tiered-ownership section, extend the fan-out staging paragraph (the one beginning "Before staging multiple findings") with: "Fan-out classes include sibling restatements of one rule, ticket-as-gate staleness repeated across living surfaces, and OpenAPI-vs-catalog wire duplicates; each is a single finding; the living-doc patterns are canonically defined in `documentation.md` Living-doc gates."
- [x] Check: run the Task 1 span lines of the Validation Commands block → expect those seven lines pass; later tasks' span and region lines may still fail at this stage; the final commit-subject section fails until all five tasks land; no forbidden-match line fails.
- [x] Run `bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"` from the repo root → expect exit 0.
- [x] Commit (staged paths limited to this task's three files): `review-agents: stage ticket-as-gate and wire-catalog duplicates as SOT fan-out classes`

### Task 2: doc-hierarchy: wire-ownership and capability-name upkeep rules

Files:
- `agents/skills/doc-hierarchy-upkeep/SKILL.md`
- `agents/skills/doc-hierarchy/company-decisions.md`

- [x] In `doc-hierarchy-upkeep/SKILL.md` Workflow, extend step 4 (the single-SOT bullet) with two terse operational checklist rows. Keep them imperative and pointer-style; do not restate principle 7's full wording; `content-ownership.md` makes company-decisions the canonical home for Layer rules and consumers link only:
  - "Wire change: update OpenAPI first; thin-index caller catalogs (pointer plus audience-specific delta only; rationale: [company-decisions.md](../doc-hierarchy/company-decisions.md) principle 7)."
  - "No new issue-key gates in Layer 1/2: cite a durable capability name (plus optional RFC/ADR link); issue keys stay in Layer 3, plans, backlog, and tracker workflow (rationale: [company-decisions.md](../doc-hierarchy/company-decisions.md) principle 7)."
- [x] In `doc-hierarchy/company-decisions.md`, add principle 7 under "Agreed principles" (the canonical wording the upkeep rows above point at): "OpenAPI is the single wire source of truth; caller catalogs thin-index to it. Living Layer 1/2 prose cites durable capability names (plus RFC/ADR links), not issue keys; issue keys belong to Layer 3, plans, backlog, and tracker workflow, so ticket churn never churns living docs." Directly after the new principle, add a one-line provenance note so the synthesized rule is not mistaken for a recorded decision of the original thread: "(Principle 7 provenance: synthesized 2026-09-04 from backlog item `2026-09-02-living-docs-capability-names-and-openapi-wire-sot`; not part of the May–June 2026 decision thread recorded above.)"
- [x] Check: run the Task 2 span lines of the Validation Commands block → expect those four lines pass; Task 1 lines still pass; Task 3–5 span and region lines may still fail; the final commit-subject section fails until all five tasks land; no forbidden-match line fails.
- [x] Run `bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"` from the repo root → expect exit 0.
- [x] Commit (staged paths limited to this task's two files): `doc-hierarchy: wire-ownership and capability-name upkeep rules`

### Task 3: plans: SOT-ownership confidence trigger and contract Files: guidance

Files:
- `agents/skills/plans/SKILL.md`

- [x] In the Phase 1 "Unclear points, confidence gate" intro paragraph (the sentence beginning "Throughout Phase 1, whenever a requirement point stays unclear"), append: "SOT ownership is a first-class unclear point: when the plan cannot tell which document owns a rule (wire contract versus Layer 2 topic versus glossary versus ADR versus history) or where new content belongs, treat the point as low confidence unless repo evidence (doc-hierarchy roles, the existing SOT) settles it."
- [x] In the plan-format Rules list, directly after the bullet "For non-behavior changes (config, docs, SQL): use concise `- [ ]` action items with exact file paths.", add: "**Cross-cutting/contract tasks:** in `Files:`, prefer the wire contract (OpenAPI) plus the one prose SOT home; do not list every caller catalog as a full-text edit target; peers point at the SOT."
- [x] Check: run the Task 3 span lines of the Validation Commands block → expect those two lines pass; Task 1–2 lines still pass; Task 4–5 span and region lines may still fail; the final commit-subject section fails until all five tasks land; no forbidden-match line fails.
- [x] Run `bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"` from the repo root → expect exit 0.
- [x] Commit (staged path limited to `agents/skills/plans/SKILL.md`): `plans: SOT-ownership confidence trigger and contract Files: guidance`

### Task 4: execute-plan + grill-with-docs: shared escalation at the documentation checkpoint

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/grill-with-docs/SKILL.md`

- [x] In `execute-plan/SKILL.md` Step 1.3b (Layer 2 documentation checkpoint), add a bullet: "If the correct SOT owner, document role, or placement for required documentation is genuinely unclear (not settled by the plan or doc-hierarchy roles), pause and run `grill-with-docs` with the user (one question at a time) before editing; never resolve the ambiguity by duplicating or contradicting existing documentation. This pause applies on every repo; it is not gated by the checkpoint's company-scope/migration-complete precondition, which gates only the upkeep run."
- [x] In `execute-plan/SKILL.md` "## Integration Points", add an entry for `grill-with-docs` following the section's existing entry format. The entry must include this sentence: "Step 1.3b (Layer 2 documentation checkpoint) invokes `grill-with-docs` when documentation SOT ownership or placement is genuinely unclear, and the checkpoint pauses for the interview instead of allowing duplicated or contradictory documentation edits."
- [x] In `grill-with-docs/SKILL.md` Integration Points, add:

  ```markdown
  ### With `execute-plan` skill
  `execute-plan` Step 1.3b (Layer 2 documentation checkpoint) invokes this skill when the correct SOT owner, document role, or placement for documentation touched during execution is genuinely unclear; the checkpoint pauses for the grill instead of duplicating or contradicting existing docs. Same one-question-at-a-time and inline glossary/ADR rules as the `plans` Phase 1 path.
  ```
- [x] Check: run the Task 4 anchor, region, and span lines of the Validation Commands block → expect all six Task 4 checks pass (two heading anchors, three region greps, one span); Task 1–3 lines still pass; the Task 5 span line may still fail; the final commit-subject section fails until all five tasks land; no forbidden-match line fails.
- [x] Run `bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"` from the repo root → expect exit 0.
- [x] Commit (staged paths limited to this task's two files): `execute-plan: pause for grill-with-docs on unclear documentation SOT`

### Task 5: review-confluence-doc: SOT consolidation finding for duplicated prose

Files:
- `agents/skills/review-confluence-doc/SKILL.md`

- [x] After subsection "#### 4.4 Structural Coherence", add:

  ```markdown
  #### 4.4.1 Duplicated normative prose (SOT consolidation)

  - When the same normative workflow or contract rule appears in several sections or child pages, stage one consolidation finding per the Living-doc gates: name the canonical owner and replace peer copies with audience-specific pointers or deltas.
  - Full lens gates: `review-agents/documentation.md` (Living-doc gates: authority roles, wire SOT, consolidation finding shape).
  ```
- [x] Check: run the Validation Commands block → expect every span, region, anchor, and forbidden-match line passes; the final commit-subject section passes only after this task's commit (the fifth) exists.
- [x] Run `bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"` from the repo root → expect exit 0.
- [x] Commit (staged path limited to `agents/skills/review-confluence-doc/SKILL.md`): `review-confluence-doc: SOT consolidation finding for duplicated normative prose`

### Task 6: final validation and certification readiness

Files: none (validation only)

- [x] Extract the `## Validation Commands` bash block from this plan file and run `bash -n` on it → expect syntax OK.
- [x] Run the full Validation Commands block from the repo root → expect exit 0 with `ALL VALIDATION CHECKS PASSED` (all five task commits exist by this point).
- [x] Verify each of the five per-task commit subjects matches `git log --format=%s` output; the block's Task 6 section already fails closed on a missing subject, so this is covered by the run above; additionally confirm `git status` shows no unstaged edits to the nine must-fix files.
- [x] No commit (no file changes in this task).

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-04-sot-unification-review-and-plan-workflows.md: disposition folded into 2026-09-04-sot-unification-living-docs-and-grill-escalation.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-05-plans-scope-extension-requires-grill-with-docs.md: disposition folded into 2026-09-04-sot-unification-living-docs-and-grill-escalation.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-02-living-docs-capability-names-and-openapi-wire-sot.md: disposition folded into 2026-09-04-sot-unification-living-docs-and-grill-escalation.md (2026-09-25); per-item file deleted.
