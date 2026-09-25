# Plan: certified-plan prose residue sweep (r5 cosmetic Lows)

Backlog:
- docs/history/backlog/2026-09-02-summarizer-hardening-round-2-r5-residuals.md
- docs/history/backlog/2026-09-05-plan-readiness-migration-r5-residuals.md
- docs/history/backlog/2026-09-05-vrs-residuals-plan-r5-cosmetic-lows.md

## Assumptions

- assume the two plan-readiness-migration r5 residual items (Task 5 interim-gate scoping sentence; Task 2 anchor backticks) are OUT of this plan's scope and are folded by that plan's executing session instead; basis: at authoring time that plan's execution is in flight (the checkout carries uncommitted edits to `docs/plans/2026-09-05-plan-readiness-migration.md` and `scripts/plan_readiness.py`), which is exactly the de-duplication case the backlog prescribes.
- assume no `validate_review_staging.py` naming edit is needed for the summarizer r5 F1 residual; basis: the script's parameterized `_selftest_source_cli` docstring (around line 3642) already enumerates the union of cases per kind ("source_kind mismatch (r4 F1)") for all three flags, so the doc-family-only wording survives only in the archived plan text.
- assume editing `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md` (certified digest `7cc5e999091e0da49285377a0d1adc77e9ce2b669735bc0b55a4493feef3ac3d`) and `docs/plans/2026-09-05-validator-pass-r4-deferred-residuals.md` (certified digest `07832a2a90865f078aa2a4a658273545187af76a1e03e5cc0dd355ed6060c54d`) deliberately supersedes those digests; basis: precedent `docs/plans/completed/2026-09-02-r5-residuals-fixes.md` (post-certification wording amendments with the successor plan's review covering the edited text), all edits here are wording-only, and the summarizer plan is executed and archived so its digest gates nothing.
- assume the validator-residuals plan's own "Authoring-time RED-today record" paragraph stays accurate after these folds; basis: the record describes the validation probes' behavior against the pre-execution tree, and none of the three wording folds changes a probe, a gate, or the recorded failure modes.

Scope extensions (grilled): none proposed.

## Gist & Examples

Five Low, non-blocking, wording-class residuals from three certified plan review loops, folded now so the backlog trio closes. Two live in the archived summarizer-hardening-round-2 plan text; three live in the still-pending validator-pass-r4-deferred-residuals plan text. No script, gate, task ordering, or digest-relevant content changes beyond the prescribed wording; no review round is reopened for any of them (each origin round verified the findings non-blocking).

1. **Summarizer r5 F1 (union enumeration).** The archived plan's Task 7 checklist names "the doc family's source_kind-mismatch case" but not the rfc family's identical case; the union phrasing should name both (the executed script already does, per the Assumptions). Wording only.
2. **Summarizer r5 F2 (note-timing).** Task 2's "write a stderr note ... before the `anomalies` line" phrasing describes an untestable stdout/stderr interleaving; reword to place the emission in the recompute block. The note text itself stays byte-identical.
3. **Validator-residuals item 1 (annotation form).** The Task 2 helper snippet quotes the return annotation (`"Iterator[io.StringIO]"`); use the unquoted form with the `collections.abc` import home Task 1 already chose.
4. **Validator-residuals item 2 (redundant flag).** The Validation Commands' `grep -nq " ;"` carries a redundant `-n` under `-q`; drop it.
5. **Validator-residuals item 3 (fixture-coupled rationale).** Task 1's second checklist bullet carries a long fixture-classification digression; shorten it while keeping the gate-on-"at least one" instruction and the pointer to the direct-parse pin.

Example of fold 1, before and after (one span, one line of the archived plan):

```
before: ... AND the doc family's source_kind-mismatch case all survive (r4 F1))
after:  ... and the doc and rfc families' source_kind-mismatch cases all survive (r4 F1))
```

## Evaluation Criteria

**Quality dimensions:**
- correctness: every fold matches its backlog item's prescription exactly (five edits, no more); each prescribed replacement text appears exactly once in its target document after the task lands
- immutability: no gate, task ordering, checklist gate semantics, or digest-relevant content changes beyond the prescribed wording; the validator-residuals plan's Validation block still passes `bash -n`
- branch-agnosticism: this plan names no branch and constrains execution branching in no way

**Done when:**
- all Validation Commands pass end to end against the post-edit tree

**Ship when:**
- (none; all work is repository-local Markdown edits)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `docs/plans/2026-09-05-validator-pass-r4-deferred-residuals.md` (only the three spans prescribed in Task 1; all other content frozen)
- `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md` (only the two spans prescribed in Task 2; all other content frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; reason: the rfc-family case is already covered by the parameterized docstring (see Assumptions); the plan text is the only edit surface
- `scripts/plan_readiness.py` and `docs/plans/2026-09-05-plan-readiness-migration.md`; reason: owned by the in-flight execution of that plan (see Assumptions); foreign working-tree edits
- any other file under `docs/plans/` or `scripts/`; reason: this plan is a five-span wording sweep over exactly two named documents

## Validation Commands

```bash
set -euo pipefail
PL_DOC="docs/plans/2026-09-05-validator-pass-r4-deferred-residuals.md"
SUM_DOC="docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md"

# Task 1 prescribed spans: present exactly once after the fold.
test "$(grep -cF -- '-> Iterator[io.StringIO]:' "$PL_DOC")" -eq 1 || { echo 'FAIL: unquoted annotation missing'; exit 1; }
test "$(grep -cF 'from collections.abc import Iterator' "$PL_DOC")" -eq 1 || { echo 'FAIL: collections.abc import missing'; exit 1; }
test "$(grep -cF 'if grep -q " ;"' "$PL_DOC")" -eq 1 || { echo 'FAIL: -n-less grep line missing'; exit 1; }

# Task 1 superseded spans: absent (quoted annotation, redundant -n, typing import).
if grep -qF '"Iterator[io.StringIO]"' "$PL_DOC"; then echo 'FAIL: quoted annotation survives'; exit 1; fi
if grep -qF 'grep -nq' "$PL_DOC"; then echo 'FAIL: redundant -n survives'; exit 1; fi
if grep -qF 'from typing import Iterator' "$PL_DOC"; then echo 'FAIL: typing import survives'; exit 1; fi

# Task 2 prescribed spans: present exactly once after the fold.
test "$(grep -cF "the doc and rfc families' source_kind-mismatch cases" "$SUM_DOC")" -eq 1 || { echo 'FAIL: rfc-family union wording missing'; exit 1; }
test "$(grep -cF 'from the same refreshed-buffer recompute block' "$SUM_DOC")" -eq 1 || { echo 'FAIL: recompute-block wording missing'; exit 1; }

# Task 2 superseded spans: absent (doc-family-only enumeration, interleaving phrasing, old lead-in).
if grep -qF "the doc family's source_kind-mismatch case" "$SUM_DOC"; then echo 'FAIL: doc-family-only enumeration survives'; exit 1; fi
if grep -qF 'before the `anomalies` line' "$SUM_DOC"; then echo 'FAIL: note-timing interleaving phrasing survives'; exit 1; fi
if grep -qF 'and write a stderr note' "$SUM_DOC"; then echo 'FAIL: old lead-in survives'; exit 1; fi

# The note text itself stays byte-identical across the F2 reword.
test "$(grep -cF 'strict audit: retry-absorbed mutation; summary recomputed from refreshed buffers' "$SUM_DOC")" -ge 1 || { echo 'FAIL: note text lost'; exit 1; }

# Syntax check: extract this block from the plan file and bash -n it.
PLAN_FILE="docs/plans/2026-09-05-certified-plan-prose-residue-sweep.md"
mkdir -p docs/tmp
awk '/^```bash$/{f=1;next} /^```$/{f=0} f' "$PLAN_FILE" > docs/tmp/prose-sweep-validation-extract.sh
bash -n docs/tmp/prose-sweep-validation-extract.sh || { echo 'FAIL: validation block syntax'; exit 1; }
rm -f docs/tmp/prose-sweep-validation-extract.sh
```

Authoring-time RED-today record (2026-09-05, against the pre-edit tree): the required-span greps that can be green only post-edit were probed and returned 0 today (`-> Iterator[io.StringIO]:`, `from collections.abc import Iterator`, `if grep -q " ;"`, `the doc and rfc families' source_kind-mismatch cases`, `from the same refreshed-buffer recompute block` all absent; the targets carry only `! grep -q " ;"`, `grep -nq " ;"`, and the doc-family-only enumeration), while every superseded-span probe matched exactly once today (quoted annotation, `grep -nq`, `from typing import Iterator`, `the doc family's source_kind-mismatch case`, `before the \`anomalies\` line`, `and write a stderr note`), so each forbidden-match guard FIRES today and flips green exactly when its fold lands. The extraction + `bash -n` tail is inert during authoring only in the sense that the block does not yet exist inside itself until this plan file is saved; the executing session runs the block verbatim.

### Task 1: Fold the three cosmetic Lows into the validator-residuals plan

Files:
- `docs/plans/2026-09-05-validator-pass-r4-deferred-residuals.md`

- [x] Task 2 helper snippet: replace `def _stderr_captured() -> "Iterator[io.StringIO]":` with `def _stderr_captured() -> Iterator[io.StringIO]:` (unquoted return annotation)
- [x] Task 2 import sentence: replace `plus the matching \`from typing import Iterator\` import (or \`collections.abc.Iterator\`, matching whatever Task 1 chose; keep one import home)` with `plus the matching \`from collections.abc import Iterator\` import (matching Task 1's \`collections.abc\` import home; keep one import home)`
- [x] Validation Commands: replace `if grep -nq " ;" projects/.ai-playbook/python_guidelines.md; then` with `if grep -q " ;" projects/.ai-playbook/python_guidelines.md; then` (drop the redundant `-n` under `-q`)
- [x] Task 1 second checklist bullet: replace the rationale span `Gate on "at least one", not an exact count: a true current-v1 payload parses twice (pattern conservation and finding conservation) and yields two entries, but the \`_payload_with_findings\` fixture used here carries no \`schema_version\`, classifies \`legacy-panel-mode\`, and runs only the finding-conservation parse, so this exact fixture yields exactly ONE entry. The single-warning-per-parse contract is pinned by the direct-parse \`warn\` check above, not here.` with `Gate on "at least one", not an exact count: the entry count depends on how many parsing passes the fixture's payload triggers (one for a legacy payload without \`schema_version\`, two for a current-v1 payload). The single-warning-per-parse contract is pinned by the direct-parse \`warn\` check above, not here.`
- [x] Run → expect the Task 1 halves of the Validation Commands to flip (annotation/import/grep pins green; quoted-annotation, `grep -nq`, and typing-import guards no longer fire)
- [x] Commit: `plans: fold r5 cosmetic Lows into validator-residuals plan text`

### Task 2: Fold the two summarizer r5 residuals into the archived plan text

Files:
- `docs/plans/completed/2026-09-02-summarizer-hardening-round-2.md`

- [x] Task 7 union enumeration (r5 F1): replace `AND the doc family's source_kind-mismatch case all survive (r4 F1))` with `and the doc and rfc families' source_kind-mismatch cases all survive (r4 F1))`
- [x] Task 2 note-timing (r5 F2): replace `and write a stderr note \`strict audit: retry-absorbed mutation; summary recomputed from refreshed buffers\` before the \`anomalies\` line at ~:2130, but only when` with `and emit a stderr note \`strict audit: retry-absorbed mutation; summary recomputed from refreshed buffers\` from the same refreshed-buffer recompute block that derives the \`anomalies\` count (~:2130), but only when` (note text byte-identical; only the placement phrasing changes)
- [x] Run → expect the Task 2 halves of the Validation Commands to flip (union and recompute-block pins green; doc-family-only enumeration, interleaving phrasing, and old lead-in guards no longer fire; note-text keep-guard stays green)
- [x] Commit: `plans: fold summarizer-round-2 r5 residuals into archived plan text`

### Task 3: Mechanical audit and final commit

- [x] Pin-vs-prescription audit: every positive pin in the Validation Commands occurs exactly once in the prescribed target (already asserted by the `-eq 1` checks; confirm none regressed after the Task 1/2 edits)
- [x] Run → expect GREEN: the full Validation Commands block exits 0 end to end
- [x] Run the no-em-dash scan over this plan and the two edited documents → expect exit 0
- [x] Commit: `plans: certified-plan prose residue sweep (r5 cosmetic Lows)`
