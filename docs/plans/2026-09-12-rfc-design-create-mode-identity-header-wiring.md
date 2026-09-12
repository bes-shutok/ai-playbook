# Plan: rfc-design create-mode identity Header wiring

Backlog item (scope of record): `docs/history/backlog/2026-09-10-rfc-design-create-mode-identity-header-wiring.md`
Origin context: `docs/plans/completed/2026-09-08-doc-ownership-lifecycle.md` (Task 6, closure step)
Provider spec: `agents/skills/doc-hierarchy/SKILL.md` "Document states" (ownership registry, identity derivation)

## Terms

- **Capability identity**: stable kebab-case concept identifier for an RFC's capability, independent of ticket, branch, or file path; ticket ids are provenance only, never the identity.
- **Ownership registry**: the Layer 2 Markdown table (one row per document identity) specified by `agents/skills/doc-hierarchy/SKILL.md` "Document states".
- **Closure (freeze transition)**: the user-declared accepted/superseded lifecycle action for an RFC (`rfc-design` Step 4): registry row, archive move where applicable, no body edits; always agent-prompted and user-confirmed.
- **Backfill derivation**: identity derivation for rows and RFCs without a Header identity: filename minus the leading `YYYY-MM-DD-` date prefix and `.md` extension, kebab-case.

## Assumptions

- assume `agents/skills/rfc-design/references/rfc-sections.md` Section 1 (Header) is an edit target alongside `agents/skills/rfc-design/SKILL.md`; basis: the item's Evidence line names both surfaces ("create/edit mode sections and `references/rfc-sections.md` define no identity field") and Goal bullet 1 requires recording the identity in the Header, whose template `rfc-sections.md` owns.
- assume `agents/skills/doc-hierarchy/SKILL.md` gets the one-sentence identity-derivation rewording; basis: that sentence cites this exact backlog item and frames derivation as "the live default until RFC creation emits the identity in the Header"; after this plan's wiring the framing is stale and the item path it cites moves to `docs/history/backlog/completed/`, leaving a dangling reference (repo convention: sweep moved and deleted paths after edits).
- assume edit mode gets NO new identity rule; basis: the item's Goal bullets prescribe create-mode assignment and the Step 4 preference only; RFCs created before this wiring are covered by the Step 4 backfill fallback; the item's Scope line names where the gap was observed, not an edit-mode mandate.
- assume the create-mode identity is assigned from the capability or feature concept by the author (kebab-case), not forcibly derived from the future filename; basis: the item's Problem section calls identity-independence from the file path the intent of the rule; the save step is only asked to prefer a filename consistent with the identity.
- assume a docs-only change: no test suite or validator code changes; verification is the Validation Commands block, the public-hygiene scan, and a standalone review loop on the change; basis: the work order prescribes exactly that evidence.
- assume the finishing commit split: the review loop's own cycle commits (wiring fixes, repo style) plus one final commit for the backlog item move, status edit, and registry row; basis: work order ordering (the move and commit finish the change) and the repo's one-logical-change-per-commit style.

Decision points requiring a grill: none remain.

## Gist & Examples

What changes: `rfc-design` create mode gains a capability-identity assignment step (Step 1), the RFC Header template gains the matching field (`rfc-sections.md` Section 1), and closure (Step 4 item 1) switches from filename derivation as the only path to Header-identity-first with filename derivation as the fallback. `doc-hierarchy`'s identity-derivation note is reworded from "the live default until" to fallback framing, and its citation of the (now-completed) backlog item path is dropped. The backlog item itself is completed with `Status: done`, a disposition line, a `git mv` to `docs/history/backlog/completed/`, and one ownership-registry row.

**Before (today):** an RFC is created through create mode (Steps 0, 0.1, 1, 2, 3). Nothing in the flow assigns a capability identity and the Header template has no identity field. The identity exists only at closure: Step 4 item 1 derives it from the filename (minus leading date prefix) and confirms with the user, so every closure lands in the filename-derivation path. A rename before closure changes the proposed identity unless the `git log --follow` workaround fires; this is the gap the backlog item records (r3 finding F7 residual).

**After (this plan):** create mode assigns a stable kebab-case capability identity when drafting begins and records it in the Header. Example: the user creates an RFC for an "invoice-export" feature. Before: the Header lists title, team, status, dates, links only; at closure the identity is proposed from the filename stem. After: the Header also carries `Capability identity: invoice-export` from creation; at closure the registry row keys on the Header value, and a pre-closure rename no longer moves the identity.

Edge cases: an RFC created before this wiring has no Header identity, so Step 4 keeps the filename-derivation fallback (rename-handling parenthetical stays, attached to the fallback). A ticket id in the PRD stays provenance only, never the identity. The wiring text references the header by name, never by a commit- or environment-specific value.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the Validation Commands block exits 0 on the post-change tree (each prescribed span present exactly once at its site; the stale closure sentence and dangling item-path references absent).
- completeness: both backlog item Goal bullets verifiably done (create-mode assignment recorded in the Header; Step 4 prefers the Header identity with the backfill fallback intact).
- consistency: prescribed text matches the surrounding rule style, stays tool-agnostic, references the header by name (`### 1. Header`, `Capability identity:`), and pins no commit-, environment-, or path-specific identity value.
- hygiene: `bash scripts/scan-public-hygiene.sh` exits 0 and no em-dashes are introduced.

**Done when:**
- The Validation Commands block exits 0 after the edits and the item move.
- One fresh review-loop round over the post-fold change reports zero unresolved blocking findings (cheap Lows folded; expected 1-2 rounds).
- The backlog item sits at `docs/history/backlog/completed/` with `Status: done` and a disposition line; the staged destination content carries the status edit (UL#277 check in V6).
- The ownership registry carries one row for the completed item; changes are committed in repo style.

**Ship when:**
- Nothing beyond repository completion; this is a local docs and skill-text change with no deploy, cross-team, or external condition.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill and docs surfaces):**
- `agents/skills/rfc-design/SKILL.md` (Step 1 block and Step 4 item 1 only; all other sections frozen)
- `agents/skills/rfc-design/references/rfc-sections.md` (Section 1 Header must-include list only; rest frozen)
- `agents/skills/doc-hierarchy/SKILL.md` (identity-derivation sentence only; rest frozen)
- `docs/history/backlog/2026-09-10-rfc-design-create-mode-identity-header-wiring.md` (status edit plus git mv)
- `docs/history/backlog/completed/2026-09-10-rfc-design-create-mode-identity-header-wiring.md` *(new, via git mv)*
- `docs/maintenance/document-registry.md` (one appended row for the completed item only; no other row touched)

**Tests:**
- none; docs-only change (see Assumptions).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. Review staging docs produced under `{reviews_dir}/` by the loop are loop-owned artifacts.

**Out of scope; reject unless plan-related:**
- Any other section of the three skill files; reason: frozen spans keep the direct fix minimal, and peer sessions work in adjacent areas.
- `README.md` skill catalog; reason: no skill description or usage changes (the wiring is inside the skill body).
- Registry rows other than the item's own; reason: no other document freezes in this change.

## Validation Commands

Authoring-time proof (2026-09-12): every span below was executed against the pre-change tree. V2, V3, V4a, V4b, V5a pins: 0 occurrences today (each count gate flips to exactly 1 when the prescribed edit lands; each prescribed text P1-P4 carries its pin exactly once). V4c stale sentence: 1 match today (forbidden gate fires). V5b dangling-path sweep: matches `agents/skills/rfc-design/SKILL.md` and `agents/skills/doc-hierarchy/SKILL.md` today (forbidden gate fires). The V4c and V5b forbidden greps are one-line fixed-string matches on single-line source lines (no line-wrap blind spot).

```bash
# V1: public hygiene scan (anchored; exit 0 required)
( cd "$(git rev-parse --show-toplevel)" && bash scripts/scan-public-hygiene.sh )

# V2: Step 1 create-mode wiring present exactly once (prescribed text P1)
test "$(grep -oF 'when drafting begins, assign a stable kebab-case capability identity' agents/skills/rfc-design/SKILL.md | wc -l)" -eq 1 \
  || { echo 'Step 1 identity wiring missing or duplicated'; exit 1; }

# V3: Header template carries the identity field exactly once (prescribed text P2)
test "$(grep -oF 'Capability identity: stable kebab-case concept identifier' agents/skills/rfc-design/references/rfc-sections.md | wc -l)" -eq 1 \
  || { echo 'Header identity bullet missing or duplicated'; exit 1; }

# V4: Step 4 prefers the Header identity, fallback retained, stale sentence gone (prescribed text P3)
test "$(grep -oF 'Prefer the identity recorded in the RFC Header' agents/skills/rfc-design/SKILL.md | wc -l)" -eq 1 \
  || { echo 'Step 4 Header preference missing or duplicated'; exit 1; }
test "$(grep -oF 'derive it at closure the filename-derived way' agents/skills/rfc-design/SKILL.md | wc -l)" -eq 1 \
  || { echo 'Step 4 backfill fallback missing or duplicated'; exit 1; }
if grep -qF 'Current create mode does not yet emit' agents/skills/rfc-design/SKILL.md; then
  echo 'STALE closure default sentence still present'; exit 1
fi

# V5: doc-hierarchy fallback framing present exactly once, no dangling item path anywhere (prescribed text P4)
test "$(grep -oF 'the fallback for rows and RFCs without a Header identity' agents/skills/doc-hierarchy/SKILL.md | wc -l)" -eq 1 \
  || { echo 'doc-hierarchy fallback framing missing or duplicated'; exit 1; }
test -d agents || { echo 'agents/ missing'; exit 1; }
test -f README.md || { echo 'README.md missing'; exit 1; }
test -d docs/maintenance || { echo 'docs/maintenance/ missing'; exit 1; }
if grep -rqF 'docs/history/backlog/2026-09-10-rfc-design-create-mode-identity-header-wiring' agents/ README.md docs/maintenance/; then
  echo 'DANGLING reference to the pre-move item path'; exit 1
fi

# V6: item completed (run after the finish steps)
test -f docs/history/backlog/completed/2026-09-10-rfc-design-create-mode-identity-header-wiring.md \
  || { echo 'item not in completed/'; exit 1; }
test ! -f docs/history/backlog/2026-09-10-rfc-design-create-mode-identity-header-wiring.md \
  || { echo 'item still at the old path'; exit 1; }
git show :docs/history/backlog/completed/2026-09-10-rfc-design-create-mode-identity-header-wiring.md | grep -qF 'Status: done' \
  || { echo 'UL#277: staged destination content lacks the status edit'; exit 1; }
grep -qF 'rfc-design-create-mode-identity-header-wiring' docs/maintenance/document-registry.md \
  || { echo 'MISSING registry row for the completed item'; exit 1; }
```

Notes: V4c and V5b are forbidden-match greps over files this plan edits plus stable sibling surfaces only; neither pattern occurs in this plan file's own swept set, so no self-match escape is needed. V6's `git show :<path>` reads the staged (or committed) destination blob, which is exactly the UL#277 post-staging check.

### Task 1: Wire create-mode capability identity into rfc-design and complete the backlog item

Files:
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/rfc-design/references/rfc-sections.md`
- `agents/skills/doc-hierarchy/SKILL.md`
- `docs/history/backlog/2026-09-10-rfc-design-create-mode-identity-header-wiring.md` (edit then git mv)
- `docs/history/backlog/completed/2026-09-10-rfc-design-create-mode-identity-header-wiring.md` *(new, via git mv)*
- `docs/maintenance/document-registry.md`

- [ ] Precondition: `git status --short agents/skills/rfc-design/SKILL.md agents/skills/rfc-design/references/rfc-sections.md agents/skills/doc-hierarchy/SKILL.md` shows no uncommitted edits from other sessions; if any target file carries uncommitted peer edits, stop and report
- [ ] `agents/skills/rfc-design/SKILL.md` Step 1: append the capability-identity rule paragraph (P1 below) after the existing Step 1 paragraph
- [ ] `agents/skills/rfc-design/references/rfc-sections.md` Section 1 Header: insert P2 into the Must-include list, directly after the RFC title bullet
- [ ] `agents/skills/rfc-design/SKILL.md` Step 4 item 1: replace the entire numbered item with P3 (the rename-handling parenthetical moves with the fallback derivation; the "Current create mode does not yet emit" sentence and the backlog-item pointer sentence are dropped)
- [ ] `agents/skills/doc-hierarchy/SKILL.md`: replace the full identity-derivation sentence (bold lead plus parenthetical) with P4 (the "live default until" framing and the backlog-item path citation are dropped)
- [ ] Run Validation Commands V1 through V5 -> expect GREEN (V6 is not runnable yet; the item move has not happened)
- [ ] Run the public hygiene scan -> exit 0
- [ ] Run a standalone review loop (the `review-loop` skill) on the change until one fresh review reports zero unresolved blocking findings; fold cheap Lows; expected 1-2 rounds; staging under `{reviews_dir}/` per `review-staging`; at the review cap without convergence, defer non-blocking residuals to a durable backlog item and take the smallest honest path
- [ ] After the loop exits clean: edit the backlog item at its current path, setting `Status: done` (from `Status: open`) and appending a `Disposition:` line recording completion via this plan and where the wiring landed (Step 1 rule, Header template field, Step 4 Header-first preference)
- [ ] `git mv docs/history/backlog/2026-09-10-rfc-design-create-mode-identity-header-wiring.md docs/history/backlog/completed/`
- [ ] Stage the destination path, then run the UL#277 check: the output of `git show :docs/history/backlog/completed/2026-09-10-rfc-design-create-mode-identity-header-wiring.md` contains `Status: done`
- [ ] Append one ownership-registry row for the completed item to `docs/maintenance/document-registry.md` (column order per the registry header): identity `rfc-design-create-mode-identity-header-wiring` (verify no collision exists first), `sot: no`, `state: completed`, `archived: <execution date>`, `reason: done, wiring landed in rfc-design create mode`, `src: docs/history/backlog/completed/2026-09-10-rfc-design-create-mode-identity-header-wiring.md`, empty `successor` and `aliases` cells, and the `audit` cell per the 2026-09-11 backlog-completion precedent rows: `user-approved <execution date>: origin header Status open->done plus one-line disposition at archive completion (plan Task 1, per the user work order)`
- [ ] Run Validation Commands V6 -> expect GREEN
- [ ] Commit the remaining changes (item move, status edit, registry row; plus the wiring if the loop ran without committing): repo style, e.g. `backlog: rfc-design create-mode identity header wiring done` (or `skills: rfc-design create mode emits capability identity in Header` when a single commit carries the wiring too)

Prescribed text P1 (rfc-design SKILL.md, Step 1, new paragraph):

```markdown
**Capability identity (create mode):** when drafting begins, assign a stable kebab-case capability identity and record it in the RFC Header (`### 1. Header`, `Capability identity:` bullet per `references/rfc-sections.md`). The identity keys the closure registry row (Step 4) and is independent of ticket, branch, or file path; ticket ids are provenance only, never the identity. When the RFC file is saved, prefer a filename consistent with the identity (see the Save location rules under Documentation paths).
```

Prescribed text P2 (rfc-sections.md, Section 1 Header, new list item after the RFC title bullet):

```markdown
- Capability identity: stable kebab-case concept identifier, independent of ticket, branch, or file path (assigned in create mode; ticket ids are provenance only, never the identity)
```

Prescribed text P3 (rfc-design SKILL.md, Step 4 item 1, full replacement):

```markdown
1. **Stable capability identity:** the closure row keys on a stable kebab-case capability identity, independent of ticket, branch, or file path; ticket ids are provenance only, never the identity. Prefer the identity recorded in the RFC Header (`Capability identity:` bullet, assigned at creation per Step 1). For an RFC without a Header identity (pre-existing files), derive it at closure the filename-derived way (filename minus leading date prefix, per the ownership-registry comment header) and confirm it with the user before freezing (if the file was renamed before closure, derive from the original creation-time filename, e.g. via git log --follow on the RFC path, and say so when proposing the identity; never silently derive from the current path, which the rename changed).
```

Prescribed text P4 (doc-hierarchy SKILL.md, identity-derivation sentence, full replacement):

```markdown
**Identity derivation** for backfilled rows and RFC closure (the fallback for rows and RFCs without a Header identity; create mode now records the identity in the Header, per `rfc-design` Step 1 and Step 4): filename minus the leading `YYYY-MM-DD-` date prefix and `.md` extension, kebab-case; collision handling is documented in the registry file's comment header.
```

## Design Invariants (CR Guard)

- The capability identity stays independent of ticket, branch, and file path; when a Header identity is present it always wins over filename derivation (item Goal bullet 2).
- The filename-derivation backfill is preserved for RFCs without a Header identity; its rename handling (`git log --follow`, confirm with the user) moves with it unchanged.
- Closure stays agent-prompted and user-confirmed; the identity confirmation at closure is not dropped (doc-ownership-lifecycle Task 6 requirement).
- No concrete identity value, example identity, or path-derived identity is pinned in the skill text; the wiring references the header by name (`Capability identity:`), never by commit- or environment-specific values.
- Completed-history immutability is untouched: this plan edits only Living SOT skill files and the item's own lifecycle metadata immediately before its archive move.
