# Plan: VRS freshness round 2 (verdict-count masking + witness sidecar read consolidation)

Backlog origin (scope of record, two items, one target file):
`docs/history/backlog/2026-09-11-vrs-clean-verdict-staged-count-masking.md`,
`docs/history/backlog/2026-09-11-vrs-freshness-witness-sidecar-read-consolidation.md`

Both items are deferred findings of the VRS freshness pass, squash-merged as cfd29a7 (its plan: `docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md`, below "the freshness plan"). This round composes with that plan's landed helpers: it does not touch `_freshness_fence`, keeps the single `validate_witness_ledger_shape` call (relocated, not duplicated), and reruns the freshness plan's Validation Commands block unmodified as a regression contract.

## Terms

- **VRS**: `scripts/validate_review_staging.py` and its in-file `_selftest_*` canary suite (`python3 scripts/validate_review_staging.py --selftest`).
- **Masking shape**: a staging doc whose verdict section matches `CLEAN_VERDICT_RE` (any separator shape) while its `| Medium+ staged |` counts row declares a nonzero count.
- **Witness resolution**: the first-real-sha-wins selection feeding the single `validate_witness_ledger_shape` call: the sidecar value arms only when the payload classifies current-v1 (r3 F8 scoping), else the Metadata value.
- **Standalone sidecar gate**: a direct `validate_stats_sidecar(...)` call with no pre-read and no witness opt-in; the exact path `scripts/plan_readiness.py` uses.
- **Pre-read**: the single `_read_stats_sidecar` outcome computed once per `validate_staging_file` run and threaded into `validate_stats_sidecar`.
- **Skip shape**: a doc whose Metadata declares `Stats sidecar: skipped` with staged count 0, so the sidecar gate exits early.
- **r1 F9 disposition**: the recorded decision (comment block inside `validate_stats_sidecar`) that the readiness path does not enforce the witness-ledger shape; staging-time validation does.

## Assumptions

- assume both defect premises are present exactly as the backlog texts describe; basis: live behavioral probes executed 2026-09-11 against the working tree at cfd29a7 with the selftest green (probe record in Gist & Examples): the masking shape passes `validate_staging_file(hard=True)` with ok=True, zero errors and zero warnings, and waives the sidecar under a skip declaration; one validation run performs 2 sidecar reads and 2 parses (1 read on the skip shape); `validate_stats_sidecar` returns a 2-tuple; `scripts/plan_readiness.py` builds its own `ValidationResult`, ignores the return, and maps `errors[0]` to failure reasons.
- assume micro-choices take the recommended shape under the standing pre-authorization on the authoring task (2026-09-11): the mask fix gates the early return on the declared count (the backlog's first candidate; the named-contradiction-error alternative is not taken); the witness epilogue moves behind a keyword flag defaulting to off rather than moving unconditionally; helper and parameter names as prescribed in Task 2 (`_SidecarRead`, `_read_stats_sidecar`, `_validate_stats_sidecar_gates`, `sidecar_read`, `enforce_witness`).
- assume the selftest is the test surface for all validator work; basis: every canary family lives inside `scripts/validate_review_staging.py` and every prior freshness plan used the same surface.
- assume `scripts/plan_readiness.py` is a frozen caller and changes nowhere in this plan; basis: caller verified 2026-09-11 (passes no pre-read, no witness opt-in, ignores the return; its selftest is green and pinned in Validation Commands).
- assume the freshness plan's archived record is immutable; the witness call count stays def + 1 through the relocation, so its Validation Commands block stays green without updating that record (its "call count intentionally changes" escape hatch is not used).

Decision points requiring a grill: mask-fix candidate (gate the clean-verdict early return on the declared count, vs named contradiction error): resolved by the standing pre-authorization on the authoring task (2026-09-11), first-listed candidate taken, affects Task 1. witness-epilogue placement (unconditional inside `validate_stats_sidecar`, vs keyword-gated default-off): resolved by the live caller probe plus the r1 F9 disposition recorded in the validator, keyword-gated default-off chosen, affects Task 2.

## Gist & Examples

Two deferred Lows from one execution, one coherent pass over one file: Task 1 makes count extraction honest when the verdict claims clean, Task 2 reads the sidecar once and re-encapsulates witness selection. The mechanisms do not overlap: masking is a verdict-counting early return inside `extract_medium_plus_count`; consolidation is read-path dedup plus API encapsulation across `validate_staging_file` and `validate_stats_sidecar`. Disjoint functions, disjoint gates, disjoint canaries; no merged origin edit.

**Masking, before (today):** a staging doc whose verdict section reads `0 unresolved blocking findings - clear round` (a legal clean shape) while its `### Counts` table declares `| Medium+ staged | 3 |` extracts 0: the clean-round early return in `extract_medium_plus_count` fires before the counts-row fallback is ever consulted. With that row as the only count signal, `extract_staged_count` also returns 0 through its fallback, both counts are zero, every count-based conservation branch is skipped, and `validate_staging_file(hard=True)` returns ok=True with zero errors and zero warnings. With a `Stats sidecar: skipped` declaration the sidecar is waived on top (the staged count looks like 0). A self-contradictory document sails through silently.

**Masking, after (this plan):** two coupled changes inside `extract_medium_plus_count`, because gating the early return alone is not enough: the canonical clean shape's own prose (`0 Medium+ findings`) itself matches the prose-count regex, so a naively gated early return would fall through to that prose match and re-mask the count as 0. The prescribed logic computes the declared count first (the single hoisted counts-row search), then: a clean verdict with an absent or zero declared count still returns 0; a clean verdict with a nonzero declared count returns the declared count (the counts row is authoritative for clean verdicts, bypassing the prose regex that the clean shape's own `0` would satisfy); non-clean verdicts keep today's exact order (prose regex first, counts-row fallback, medium-only prose). The contradictory document now extracts 3 whatever the separator shape, `extract_staged_count` falls through to 3, and count conservation demands the claimed finding sections: the doc fails with a staged-count gap error, and the skip declaration now earns `skipped is not allowed when Staged findings > 0`. A clean verdict with no counts row, or with a zero row, still extracts 0 (both stay-green arms pinned); a non-clean verdict's prose count still wins over the counts row (precedence unchanged, so a doc counting through bullets plus a counts row only grows stricter); `is_clean_verdict` is untouched, so clean-keyed freshness gates keep reading the verdict text exactly as today. This plan changes the count, not the verdict classification.

**Consolidation, before (today):** one `validate_staging_file` run reads and `json.loads`-parses the sidecar twice: a best-effort silent read for the fence's `sidecar_date`, then the authoritative read inside `validate_stats_sidecar`. Witness selection lives in `validate_staging_file`, so the caller must know the v1-scoping rule (`sidecar_schema == "current-v1"`) that the callee already encodes, and consumes the `(payload, schema_class)` tuple: internal classification leaked into the module API surface.

**Consolidation, after (this plan):** one `_read_stats_sidecar` outcome feeds both consumers: `validate_staging_file` pre-reads once before the fence gate (same position, same silence for missing or malformed sidecars) and threads the outcome down; `validate_stats_sidecar` performs its own identical read only on the standalone path (no pre-read supplied). Witness selection and the single shape call move inside `validate_stats_sidecar` behind `enforce_witness` (default off), which returns the payload only. The standalone path is byte-identical by construction: same gates, same error text, no witness enforcement (r1 F9 disposition preserved), return value ignored as today.

**Probe record (executed at authoring time 2026-09-11, tree at cfd29a7, selftest green):**

- Masking shape (dash-clean verdict, `| Medium+ staged | 3 |` as the only count signal, valid fresh sidecar): `extract_medium_plus_count` = 0, `extract_staged_count` = 0, end-to-end ok=True, errors [], warnings []. With `- Stats sidecar: skipped (clear round)` added: ok=True (sidecar waived). Controls: verdict `2 Medium+ findings` with the same row extracts 2 and fires a conservation gap error; counts row `| Medium+ staged | 0 |` extracts 0 and validates ok (the fix must keep this green).
- Canonical clean shape (verdict `0 Medium+ findings; clear round`, same row): extraction 0 today as well, and a simulation of an early-return-only gate still yields 0 because the clean shape's own `0 Medium+ findings` prose matches the prose-count regex before the counts-row fallback; the declared-count bypass in Task 1 exists to close exactly this (round r1 review finding F1, fold verified against the live regexes).
- Read counts (counting wrappers over `Path.read_text` and `json.loads`, one run each): fresh valid doc, 2 sidecar reads, 2 parses; skip shape, 1 and 1; `validate_stats_sidecar(...)` direct returns a tuple of length 2 with schema current-v1.
- Missing sidecar (post-fence fresh doc, no sidecar file): exactly one error, `missing required stats sidecar: <name>`; the fence stays silent.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `python3 scripts/validate_review_staging.py --selftest` exits 0 before and after every task; the four masking canaries, the read-count canary's fresh-doc leg, and the standalone payload-shape check are RED first and GREEN after their fixes; the six characterization checks are GREEN before and after; the freshness plan's Validation Commands block reruns green on the finished tree without modification
- maintainability: the sidecar read and parse exist exactly once (`_read_stats_sidecar`); the witness resolution appears exactly once (inside `validate_stats_sidecar`); `validate_witness_ledger_shape(` appears exactly twice (def plus the one call); `scripts/plan_readiness.py` has no diff
- docs-consistency: the probe-recorded numbers in this plan match re-executed probes if the tree has moved since 2026-09-11; no stale cross-references to relocated code remain in the validator's comments (the moved witness comment and the rewritten `validate_stats_sidecar` docstring describe the new homes)

**Done when:**
- all Validation Commands pass on the finished tree
- backlog item 1's acceptance criteria are satisfied by Task 1: the masked shape no longer passes count-based conservation gates silently, a RED-first canary pins it, and the selftest exits 0
- backlog item 2's acceptance criteria are satisfied by Task 2: payload-only return with witness selection inside `validate_stats_sidecar`, at most one sidecar read and parse per validation run, selftest green, and the freshness plan's Validation Commands block stays green with no record edit
- the review loop exited on a fresh ready=yes round with zero unresolved blocking findings over the post-fold digest

**Ship when:**
- the symlinked runtime registry copy of the validator (`~/.ai-playbook/scripts/validate_review_staging.py`, a symlink into this repo, verified 2026-09-11) serves the landed file on its next validation run; no manual deploy step exists (environment-owned, prose only)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py`

**Tests:**
- the `_selftest_*` canary families live inside the validator file listed under Production code; there is no separate test file

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: frozen caller, verified compatible (no pre-read, no witness opt-in, return ignored); behavior preservation is pinned by characterization canaries and its own selftest, not by edits
- `docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md`; reason: the archived record is immutable; its Validation Commands are executed as a contract, never edited, and the witness-call count intentionally stays 2 so no record update is needed
- `docs/history/backlog/**`; reason: promoted backlog items stay in place until plan completion per the plans lifecycle
- `docs/reviews/**`; reason: historical review records are immutable context
- `agents/skills/**`; reason: no skill prose changes in this plan; the validator-adjacent consumer wording lives in review-staging and was already aligned by the freshness plan

## Design Invariants (CR Guard)

1. **The r1 F9 disposition stays.** The standalone sidecar gate never enforces the witness-ledger shape; the witness epilogue is keyword-gated (`enforce_witness`, default False) and only `validate_staging_file` opts in. `scripts/plan_readiness.py` maps `staging_result.errors[0]` to failure reasons, so a witness error leaking into that path would newly fail records that pass today.
2. **Error ordering is frozen.** Fence-gate errors precede sidecar-gate errors; the fence consumes the pre-read silently (a missing or malformed sidecar arms no fence error); a missing or malformed sidecar reports only through its own named gates (`missing required stats sidecar: <name>`, `invalid stats sidecar JSON: <exc>`), byte-identical text rendered from the same captured exception.
3. **The skip shape reads at most once.** The skip early exit stays ahead of every sidecar gate; skip-shape runs perform exactly one sidecar read (today's fence read, after this plan the pre-read), never two.
4. **Extraction precedence is unchanged for non-clean verdicts; the declared count is authoritative for clean ones.** For a verdict section the clean pattern does not match, the prose count regex still precedes the counts-row fallback. For a clean verdict, the early return survives only when the declared count is absent or zero, and a nonzero declared count bypasses the prose regex (whose `0 Medium+ findings` fragment is the clean shape's own prose and would re-mask the count). `is_clean_verdict` is untouched: clean-keyed freshness gates keep classifying on the verdict text; this plan changes the count, not the verdict classification.
5. **r3 F8 scoping stays.** The sidecar witness surface arms only for current-v1 payloads; legacy, unsupported, and versionless-current payloads never arm it; the existing scoping and incident-shape canaries stay green through the relocation.
6. **The freshness plan's file contract survives without editing that record.** `validate_witness_ledger_shape(` count is 2 (def plus the one call, relocated inside `validate_stats_sidecar`); no string-match dedupe guard fragment returns; no inline `and last_fix.strip()` recompute returns; exactly one `(\d{4}-\d{2}-\d{2})` fence parse (the pre-read does not parse dates); no `EXTENDED_SIDECAR_MIN_DATE` comparison outside `_freshness_fence` (the freshness plan's AST pin).

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
VRS="scripts/validate_review_staging.py"
ARCHIVED="docs/plans/completed/2026-09-09-vrs-freshness-prose-dedup.md"

fail() { echo "VALIDATION FAIL: $*" >&2; exit 1; }
expect_match() { grep -qF -- "$1" "$2" || fail "missing expected text in $2: $1"; }

# 1. Full canary suite.
python3 "$VRS" --selftest >/dev/null 2>&1 || fail "selftest not green"

# 2. Task 1 canaries, pinned by name (the exact strings the task prescribes).
expect_match "clean-round count masking: a dash-separated clean verdict with a nonzero | Medium+ staged | counts row extracts the declared count" "$VRS"
expect_match "clean-round count masking: the canonical clean shape with a nonzero | Medium+ staged | counts row extracts the declared count" "$VRS"
expect_match "clean-round count masking: a clean verdict with a nonzero Medium+ staged counts row fails count conservation end-to-end" "$VRS"
expect_match "clean-round count masking: a stats-skip declaration no longer waives the sidecar when the counts row is nonzero" "$VRS"
expect_match "clean-round count masking characterization: a counts row of 0 keeps the clean early return" "$VRS"
expect_match "clean-round count masking characterization: verdict-prose count still wins over the counts row" "$VRS"
expect_match "clean-round count masking characterization: a dash-separated clean verdict with no counts row still extracts 0" "$VRS"

# 3. Task 2 canaries, pinned by name.
expect_match "sidecar read consolidation: one validate_staging_file run reads and parses the sidecar at most once" "$VRS"
expect_match "sidecar read consolidation: the standalone sidecar gate returns the payload and keeps its contract with no pre-read" "$VRS"
expect_match "sidecar read consolidation: a missing sidecar reports only its named error" "$VRS"
expect_match "witness encapsulation: the standalone sidecar gate does not enforce the witness shape" "$VRS"
expect_match "witness encapsulation: staging-time validation still enforces the witness shape exactly once" "$VRS"

# 4. Encapsulation shape: payload-only return, keyword-gated epilogue, one read helper.
expect_match "sidecar_read: _SidecarRead | None = None" "$VRS"
expect_match "enforce_witness: bool = False" "$VRS"
expect_match "def _read_stats_sidecar(" "$VRS"
c=$(grep -c 'validate_witness_ledger_shape(' "$VRS")
[ "$c" -eq 2 ] || fail "witness shape call sites = $c, expected def + 1 call"

# 5. The freshness plan's file contract, rerun verbatim (archived record untouched).
BLOCK="$(mktemp /tmp/vrs-archived-validation.XXXXXX)"
sed -n '/^```bash$/,/^```$/p' "$ARCHIVED" | sed '1d;$d' > "$BLOCK"
bash "$BLOCK" || fail "archived freshness plan Validation Commands block"
rm -f "$BLOCK"

# 6. The frozen caller's own suite.
python3 scripts/plan_readiness.py --selftest >/dev/null 2>&1 || fail "plan_readiness selftest"

# 7. Repo hygiene gate.
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || fail "public hygiene scan"
```

Note: steps 2 to 4 are RED at authoring time (the canaries and the encapsulation shape do not exist yet; probed 2026-09-11) and turn GREEN exactly when Tasks 1 and 2 land. Step 5 is GREEN today and must stay green through both tasks.

### Task 1: Verdict-count masking fix (backlog item: vrs-clean-verdict-staged-count-masking)

Files:
- `scripts/validate_review_staging.py`

All checks join the `_selftest_extended_sidecar_freshness` family beside the digit-boundary block, reusing its local `stage` and `fresh_payload` helpers plus a new local `masking_md(verdict, counts_row=None, skip_decl=False)` builder with this exact fixture recipe: start from `_version1_markdown()`, replace `1 Medium+ findings accepted for fix` with the verdict under test; replace the ENTIRE existing `### Counts` section (from its heading through the line before `### Deduplication groups`) with `### Counts` followed by the single row line `| Medium+ staged | <counts_row> |` when `counts_row` is given, or by `### Counts` followed by `- Workers launched: 5` when it is not; remove every line matching `^-\s*(Findings|Staged findings):\s*\d+\s*$` (the base markdown carries the `- Staged findings: 1` bullet twice plus a `- Findings: 1` Metadata bullet, so all count-bullet signals are gone and the inserted row is the only count signal); replace `## Metadata` with `## Metadata` plus the four freshness lines (`- Review mode: fresh-adversarial`, `- Changed-risk signals: none`, `- Prior findings supplied as filter: no`, `- Last fix commit: none`); and when `skip_decl` is true add `- Stats sidecar: skipped (clear round)` under `- Panel mode: full`.

- [ ] RED: add check `clean-round count masking: a dash-separated clean verdict with a nonzero | Medium+ staged | counts row extracts the declared count`; given content whose verdict section reads `0 unresolved blocking findings - clear round` and whose only count signal is the `| Medium+ staged | 3 |` row, expects `extract_medium_plus_count(content) == 3`; run the selftest and expect this check FAIL (probed 2026-09-11: extracts 0 today)
- [ ] RED: add check `clean-round count masking: the canonical clean shape with a nonzero | Medium+ staged | counts row extracts the declared count`; given content whose verdict section reads `0 Medium+ findings; clear round` and whose only count signal is the `| Medium+ staged | 3 |` row, expects `extract_medium_plus_count(content) == 3`; run the selftest and expect this check FAIL (probed 2026-09-11: extracts 0 today, and it would STILL extract 0 if the fix only gated the early return, because the clean shape's own `0 Medium+ findings` prose matches the prose-count regex; this canary is what forces the declared-count bypass)
- [ ] RED: add check `clean-round count masking: a clean verdict with a nonzero Medium+ staged counts row fails count conservation end-to-end`; given `stage("mask", fresh_payload("2026-09-10"), masking_md(...))` for BOTH the canonical and the dash-separated clean verdict, expects `validate_staging_file(path, hard=True)` not ok for BOTH fixtures, each with a staged-count gap error mentioning `finding sections`; run the selftest and expect FAIL (probed: ok=True with zero errors today)
- [ ] RED: add check `clean-round count masking: a stats-skip declaration no longer waives the sidecar when the counts row is nonzero`; given the dash-shaped fixture with `skip_decl=True`, expects not ok with the error `Stats sidecar: skipped is not allowed when Staged findings > 0`; run the selftest and expect FAIL (probed: ok=True today)
- [ ] Characterization (GREEN before and after): add check `clean-round count masking characterization: a counts row of 0 keeps the clean early return`; given the dash-clean verdict with `| Medium+ staged | 0 |`, expects `extract_medium_plus_count == 0` and the staged doc validates ok (probed)
- [ ] Characterization (GREEN before and after): add check `clean-round count masking characterization: verdict-prose count still wins over the counts row`; given a NON-CLEAN verdict section reading `2 Medium+ findings` and a `| Medium+ staged | 3 |` row, expects `extract_medium_plus_count == 2` (probed)
- [ ] Characterization (GREEN before and after): add check `clean-round count masking characterization: a dash-separated clean verdict with no counts row still extracts 0`; given the dash-clean verdict and no counts signal, expects `extract_medium_plus_count == 0` (the canonical no-row shape is already pinned by the existing freshness-plan canary)
- [ ] Implement inside `extract_medium_plus_count`: hoist the existing single `| Medium+ staged |` counts-row search (same regex, same whole-content scope) above the clean early return into a `counts_declared` value; compute the clean match once; when the verdict section is clean and `counts_declared == 0`, return 0 (unchanged early return, now declared-count-gated); when the verdict section is clean and `counts_declared > 0`, return `counts_declared` immediately, bypassing the prose-count regex (the clean shape's own `0 Medium+ findings` prose would otherwise re-mask the count); non-clean verdicts keep today's exact order (prose regex, then the same single counts-row search as fallback, then medium-only prose); update the function comment to state both arms; no second regex copy anywhere
- [ ] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN (the four masking canaries, the three characterizations, and every existing canary including the digit-boundary family)
- [ ] Commit: `validator: gate the clean-verdict early return on the declared Medium+ staged count (count masking fix)`

### Task 2: One sidecar read per run and witness selection encapsulated (backlog item: vrs-freshness-witness-sidecar-read-consolidation)

Files:
- `scripts/validate_review_staging.py`

New checks join a new `_selftest_sidecar_read_consolidation(root, check)` family registered in `run_selftest` after `incident_shapes`. Unless a check says otherwise, the family stages valid docs with `_write_staging` from `_version1_markdown()` plus `_version1_payload()` under the pre-fence filename date `2026-07-17` (the versioned family's known-green shape, no freshness lines needed). The two witness characterizations use the post-fence freshness shape instead: filename date `2026-09-10`, sidecar `date` `2026-09-10`, the four freshness Metadata lines, sidecar `last_fix_commit` and Metadata `- Last fix commit:` both set to the same real 64-hex sha, and neither a `### Witness ledger` section nor the N/A line.

- [ ] RED: add check `sidecar read consolidation: one validate_staging_file run reads and parses the sidecar at most once`; given counting wrappers swapped over `Path.read_text` and `json.loads` for the duration of one call and restored in a finally block, one `validate_staging_file(hard=True)` run over a valid fresh doc expects exactly 1 sidecar-suffix read and 1 parse (probed: 2 and 2 today), and one run over the skip shape (a `2026-07-17` doc whose Metadata carries `- Stats sidecar: skipped (clear round)` with a clean verdict and no count signals) expects 1 and 1 (already true today; must stay); run the selftest and expect FAIL on the fresh-doc leg
- [ ] RED (the payload-shape half; the error halves are GREEN regression pins): add check `sidecar read consolidation: the standalone sidecar gate returns the payload and keeps its contract with no pre-read`; given a direct `validate_stats_sidecar(path, content, result)` with no keyword arguments on a valid doc, expects no errors and the returned value to be a dict (payload-only shape; probed: a 2-tuple today); given an invalid-JSON sidecar file, expects the named `invalid stats sidecar JSON` error and no exception
- [ ] Characterization (GREEN before and after): add check `sidecar read consolidation: a missing sidecar reports only its named error`; given a post-fence fresh doc with no sidecar file, expects exactly one error, `missing required stats sidecar: <name>` (probed 2026-09-11; the fence stays silent)
- [ ] Characterization (GREEN before and after): add check `witness encapsulation: the standalone sidecar gate does not enforce the witness shape`; given the witness-characterization doc, a direct `validate_stats_sidecar(path, content, result)` with no keyword arguments expects no error containing `Witness ledger` (the r1 F9 disposition; the readiness path depends on this exact shape)
- [ ] Characterization (GREEN before and after): add check `witness encapsulation: staging-time validation still enforces the witness shape exactly once`; given the same doc through `validate_staging_file(hard=True)`, expects not ok with exactly one error containing `Witness ledger`
- [ ] Implement a module-level `def _read_stats_sidecar(sidecar_path)` helper beside `stats_sidecar_path`, returning a frozen dataclass `_SidecarRead` with fields `payload: dict | None`, `error: Exception | None`, `exists: bool`: not a file returns `(None, None, False)`; `json.loads(read_text(encoding="utf-8"))` failing on `(OSError, json.JSONDecodeError, UnicodeDecodeError)` as `exc` returns `(None, exc, True)`; success returns `(payload, None, True)`
- [ ] Move the body of `validate_stats_sidecar` verbatim into `_validate_stats_sidecar_gates(staging_path, content, result, *, expected_digest, source_kind, sidecar_read)` returning `(payload, schema_class)` with the same early exits; its read block becomes: when `sidecar_read` is None, `sidecar_read = _read_stats_sidecar(stats_sidecar_path(staging_path))`; `not sidecar_read.exists` produces the same `missing required stats sidecar: {name}` error; `sidecar_read.error is not None` produces the same `invalid stats sidecar JSON: {exc}` f-string rendered from the captured exception; the payload is consumed from `sidecar_read.payload`; no other gate, order, or message change
- [ ] Make `validate_stats_sidecar` a wrapper with keyword-only `sidecar_read: _SidecarRead | None = None` and `enforce_witness: bool = False`, returning the payload only (`dict | None`); after the gates call, when `enforce_witness`, run the witness resolution moved verbatim from `validate_staging_file` (sidecar value only when `schema_class == "current-v1"`; `_last_fix_present` decides; the sidecar real sha wins, else the Metadata sha from `_metadata_last_fix(content)` arms; the single `validate_witness_ledger_shape(content, result, last_fix=..., source=...)` call); update the docstring: the tuple return and the caller-side selection are gone, the epilogue is staging-only
- [ ] Rewire `validate_staging_file`: delete the inline best-effort fence-read block and the `md_last_fix` local; compute `sidecar_read = _read_stats_sidecar(stats_sidecar_path(path))` once before `validate_date_keyed_freshness_lines` and derive `sidecar_date` exactly as today (a dict payload with a str `date` field yields the value, anything else None, silent); call `validate_stats_sidecar(path, content, result, expected_digest=expected_digest, source_kind=source_kind, sidecar_read=sidecar_read, enforce_witness=True)`; delete the witness resolution block
- [ ] Change nothing in `scripts/plan_readiness.py`; its behavior is preserved by construction (no pre-read, so the gates helper reads once itself; no `enforce_witness`, so no witness errors) and pinned by the standalone characterizations plus its selftest in Validation Commands
- [ ] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN (the new family green; every existing witness, fence, freshness, incident-shape, and digit-boundary canary green unchanged; `validate_witness_ledger_shape(` count still def plus 1)
- [ ] Commit: `validator: one sidecar read per run + witness selection encapsulated (readiness path unchanged)`

### Task 3: Full validation

Files: none (verification only)

- [ ] Run the entire `## Validation Commands` block from the repository root → expect every command GREEN (including the archived freshness plan's block rerun verbatim and the plan_readiness selftest)
- [ ] Run `python3 scripts/validate_review_staging.py --selftest` once more standalone → expect exit 0
