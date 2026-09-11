# Plan: VRS freshness + prose dedup pass

Backlog origin (scope of record, one item family, six files):
`docs/history/backlog/2026-09-08-vrs-freshness-fence-single-helper.md`,
`docs/history/backlog/2026-09-08-vrs-freshness-value-gate-tails.md`,
`docs/history/backlog/2026-09-08-vrs-verdict-scoping-dedup.md`,
`docs/history/backlog/2026-09-08-vrs-witness-twin-single-call.md`,
`docs/history/backlog/2026-09-08-producer-template-freshness-contract.md`,
`docs/history/backlog/2026-09-08-skill-prose-dedup-pointers.md`

Source findings: `docs/reviews/2026-09-08-execute-plan-fresh-review-coverage-gaps-code-review-r1.md` (F14, F15), `-r2.md` (O1, O2), `-r4.md` (F8, F9), and the round-5 residual families recorded in `-r5.md`. Reviews for THIS plan live under the prefix `docs/reviews/2026-09-09-plan-review-vrs-freshness-prose-dedup-r1.md`, `-r2.md`, and so on for each later round.

## Terms

- **VRS**: `scripts/validate_review_staging.py`, the review-staging validator and its selftest suite.
- **Freshness fence**: the `EXTENDED_SIDECAR_MIN_DATE` (currently `2026-09-09`) grandfathering concept, enforced on two surfaces: the staging filename's leading date and the version-1 sidecar `date` field.
- **Effective freshness date**: the fence classification of a record (which side of the fence each surface sits on), computed by the single helper this plan introduces.
- **Witness twin**: the two `validate_witness_ledger_shape` call sites (Markdown Metadata path, sidecar path) that today deduplicate via a string match on the validator's own error text.
- **Clean-round shape**: the verdict text `CLEAN_VERDICT_RE` recognizes (`0 Medium+ findings; clear round` and `0 unresolved blocking findings; clear round` with the widened separator class).
- **Producer copy**: a consumer skill's inlined staging Metadata template (the review-plan template block is the model).
- **Pointer shape**: a one-line "see the owning skill" reference that replaces verbatim-restated prose (the shape rfc-design and review-confluence-doc already use).
- **Canary**: a named selftest check pinning a defect shape; RED before its fix, GREEN after.
- **Characterization check**: a GREEN-before check that pins today's behavior across a refactor and must stay GREEN after.

## Assumptions

- assume every defect across the six items is present exactly as the backlog texts describe; basis: source verification on 2026-09-09 at working tree `0ec98d3` with selftest exit 0 baseline: the empty `Review mode:` value bypass (presence regex needs only label plus colon, value regex needs `.+?`), the missing left digit boundary (`10 Medium+ findings; clear round` matches both clean-round regexes through the `0` of `10`), the string-match dedupe guard at `validate_witness_ledger_shape`, three copies of the last-fix extraction regex plus one inline `_last_fix_present` recompute, the `no-freshness-lines-before` canary staging fresh lines by default, the `UnicodeDecodeError` gaps on three file reads, both producer copies missing the six Metadata lines, the stale `undocumented top-level field` quote in doing-code-review and review-loop, the r4 F7 mirrored fence undocumented in review-staging, the verbatim witness-trigger copies in review-plan and plans, and the execute-plan Step 0.1c pointer-plus-restatement pair.
- assume micro-choices left open by the backlog texts take the recommended option under the standing pre-authorization on the authoring task (2026-09-09): an empty-valued gated freshness label is a named error (value-gate-tails item 1, option 1); the spelled-out zero verdict gate is a named warning, not an error (item 2 allows either; a negated phrasing such as "not a clear round" is an honest non-clean verdict and must not hard-fail); doing-code-review and review-loop get ONE combined prose edit covering producer-template item 2 and the F8 validator-refresh reduction together; the F8 recovery rule's owning sentence lands in review-staging (no skill carried it, and the reduced pointers need an owning target); the r3 O16 last-fix extraction block in `validate_stats_sidecar` routes through the shared helper (fifth copy of the same extraction).
- assume Tasks 3 and 4 are behavior-neutral: the selftest suite passes unchanged before and after, except for the new characterization checks those tasks add; basis: acceptance criteria in the fence-single-helper and witness-twin backlog items.
- assume `validate_stats_sidecar` may start returning the parsed payload dict; basis: the only external caller (`scripts/plan_readiness.py:718`) ignores the return value (verified 2026-09-09).
- assume `CLEAR_ROUND_RE` has no consumers outside the validator; basis: repo-wide grep on 2026-09-09 found its only use at `extract_medium_plus_count` plus one prose comment, both in `scripts/validate_review_staging.py`.
- assume the selftest is the test surface for all validator work (the VRS canary families live inside `scripts/validate_review_staging.py` itself); basis: the file's `_selftest_*` functions and every prior freshness plan used the same surface.

Decision points requiring a grill: none remain.

## Gist & Examples

Six deferred Low findings from one execution, one coherent pass: two validator tasks add small fail-closed gates with canaries, two validator tasks consolidate duplicated logic without changing behavior, and two prose tasks align the skills that consume the validator. Same origin review, heavily overlapping files, one review context.

**Before (today):** a staging doc whose Metadata carries `- Review mode:` with nothing after the colon passes validation: the presence gate sees the label, every value gate stays silent (the value regex requires at least one character), and the fresh-adversarial twin is disarmed because the mode parsed to no enum value. A verdict line reading `No Medium+ findings; clear round.` reads as not-clean, silently disarming every clean-keyed freshness gate. Worse, `10 Medium+ findings; clear round` reads as CLEAN and its count extracts as 0, because both clean-round regexes match the `0` inside `10`.

**After (this plan):** the empty-valued label is a named error; the spelled-out zero earns a named warning pointing at the canonical shape; the `10 Medium+` verdict is not clean and its count is 10. Each new gate has a failing canary written first.

**Before (today):** the fence is one concept enforced as three coupled rules that each re-derive the two date keys inline (`validate_date_keyed_freshness_lines`, the sidecar extended-field exemption, the backdate refusal plus its r4 F7 mirror), the clean-round definition lives in two regexes and the verdict-section scoping in two regex copies, the last-fix extraction lives in three regex copies plus one inline recompute, and the witness twin deduplicates by string-matching its own error message.

**After (this plan):** each of those concepts exists exactly once: one fence helper classifies both surfaces, one `_verdict_section` helper scopes the verdict blob, one canonical clean-round pattern (with the digit boundary) serves every consumer, one `_metadata_last_fix` helper extracts the Metadata last-fix value, and the witness twin resolves the value once and calls the shape check exactly once. Public behavior is byte-identical for all four consolidations except the intended digit-boundary fix, pinned by characterization checks.

**Prose, before:** a staging doc built from the rfc-design or review-confluence-doc inlined Metadata template fails the very validator gate the same skill mandates (the templates predate the freshness contract). The witness-trigger and validator-refresh sentences are restated verbatim across four skills, and execute-plan Step 0.1c carries both a pointer to the plans truth table and a near-complete restatement of it.

**Prose, after:** both producer copies carry the six Metadata lines mirroring the review-plan template; the restated sentences collapse to the pointer shape those skills' siblings already use; review-staging gains the two owner sentences (mirrored fence direction, validator-copy refresh recovery with the correct emitted error text); execute-plan Step 0.1c keeps the pointer plus only the pinned trunk-condition literal.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `python3 scripts/validate_review_staging.py --selftest` exits 0 before and after every task; every new gate has a named canary that fails before its fix and passes after; Tasks 3 and 4 change no observable outcome except the intended digit-boundary fix
- maintainability: the fence comparison, the verdict-section scoping, the clean-round pattern, and the last-fix extraction each appear exactly once (grep-pinned in Validation Commands)
- docs-consistency: both producer copies carry the six Metadata lines; no stale `undocumented top-level field` quote remains anywhere under `agents/skills/`; review-staging documents both fence directions and owns the refresh-recovery rule

**Done when:**
- all Validation Commands pass on the finished tree
- each of the six backlog items' acceptance criteria is satisfied by a named task above
- the review loop exited on a fresh ready=yes round with zero unresolved blocking findings over the post-fold digest

**Ship when:**
- downstream skill consumers pick up the updated SKILL.md copies on their next sync (human-owned, outside this repository's execution)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py`

**Tests:**
- the `_selftest_*` canary families live inside the validator file listed under Production code; there is no separate test file

**Docs (producer copies and contract home):**
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: verified compatible caller, must not change (its `validate_stats_sidecar` call ignores the return value)
- `docs/history/backlog/**`; reason: backlog items stay in place until plan completion per the plans lifecycle
- `docs/reviews/**` (2026-09-08 coverage-gaps artifacts); reason: historical review records are immutable context
- `README.md` and `docs/maintenance/**`; reason: no catalog or guideline change in this plan

## Design Invariants (CR Guard)

1. **Fence semantics are frozen.** The r2 F3 backdate refusal (exemption claimed while the filename is post-fence: error plus exemption stripped), the r4 F7 mirrored direction (pre-fence filename with post-fence sidecar date: error), the r3 F11 dateless-filename fail-closed branch, and the silent grandfathering of a dateless filename with a pre-fence sidecar date each keep today's outcome. Task 3 may not change any of the four; the characterization checks pin them.
2. **Byte-identical wins over the backlog's shorthand.** The fence item's parenthetical ("a missing or malformed key on either surface counts as post-fence, fail-closed") describes the sidecar surface and the r3 F11 branch correctly, but a naive max() with missing-equals-post-fence would arm the Markdown gate for the dateless-name-plus-pre-fence-sidecar shape, which today is grandfathered silently. The helper encodes per-surface semantics; the new characterization check pins the silent shape.
3. **r4 F1 vocabulary stays.** `none`, `null`, and `n/a` are absent spellings on both surfaces. The witness resolution is first-real-sha-wins (sidecar preferred, Metadata fallback) under the r3 F8 scoping: the sidecar surface arms only for current-v1 payloads, so the gate fires for exactly the same records as today for every schema class; in the both-real shape the surviving error names the sidecar where it named Metadata before (wording delta only).
4. **No clean-round check-id or error-string changes.** Named check ids are pinned by failing canaries; Tasks 3 and 4 may not alter any canary's expected output strings.
5. **r2 F8 fallback stays retired.** `_verdict_section` returning None (absent verdict heading) means not-clean and whole-document count fallback only inside `extract_medium_plus_count`, exactly as today.
6. **Sibling handshake untouched.** `COMPAT_VERSION` stays 1; `VERDICT_VALUES` is unchanged; no consumer-shared constant value changes (the digit boundary tightens `CLEAN_VERDICT_RE` inside the validator; no script imports it).

## Validation Commands

```bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
VRS="scripts/validate_review_staging.py"

fail() { echo "VALIDATION FAIL: $*" >&2; exit 1; }

# Positive fixed-string presence in one file.
expect_match() {
  grep -qF -- "$1" "$2" || fail "missing expected text in $2: $1"
}

# Forbidden fixed-string sweep, recursive, case-insensitive, three-way split:
# rc 0 = forbidden match (fail), rc 1 = clean pass, rc >= 2 = tool error (fail).
expect_no_match() {
  local pattern="$1"; shift
  local rc=0
  grep -rniF -- "$pattern" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden text present: $pattern"
  elif [ "$rc" -ge 2 ]; then fail "grep error rc=$rc for: $pattern"; fi
}

# Wrap-tolerant forbidden phrase in one file (flattened, case-insensitive).
expect_no_phrase() {
  local pattern="$1" file="$2"
  local rc=0
  tr '\n' ' ' < "$file" | tr -s ' ' | grep -qiF -- "$pattern" || rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden phrase present in $file: $pattern"
  elif [ "$rc" -ge 2 ]; then fail "grep error rc=$rc for: $pattern"; fi
}

# 1. Selftest green (the whole canary suite).
python3 "$VRS" --selftest >/dev/null 2>&1 || fail "selftest not green"

# 2. Task 1 canaries and single-ownership pins.
expect_match "clean-round digit boundary: a 10 Medium+ findings clear-round verdict is not clean and extract_medium_plus_count returns 10" "$VRS"
expect_match "clean-round digit boundary: a 10 unresolved blocking findings clear-round verdict is not clean" "$VRS"
c=$(grep -cF '## Verdict for this round \(before fixes\)(.*?)(?:\n## |\Z)' "$VRS")
[ "$c" -eq 1 ] || fail "verdict-section scoping regex appears $c times, expected 1"
expect_no_match "CLEAR_ROUND_RE" scripts/

# 3. Task 2 canaries.
expect_match "freshness: an empty-valued gated Metadata label fails naming the label and the empty value" "$VRS"
expect_match "freshness: a clear-round phrase without a recognizable clean-round verdict warns" "$VRS"
expect_match "freshness: the canonical clean-round verdict does not warn" "$VRS"
expect_match "freshness: a non-UTF-8 stats sidecar reports a named error instead of a traceback" "$VRS"
expect_match "freshness: a non-UTF-8 staging file reports a named error instead of a traceback" "$VRS"

# 4. Task 3 pins: one fence parse, comparisons only inside the helper,
#    silent-grandfathering characterization check present.
c=$(grep -cF '(\d{4}-\d{2}-\d{2})' "$VRS")
[ "$c" -eq 1 ] || fail "leading-date fence parse appears $c times, expected 1"
python3 - "$VRS" <<'PYEOF' || fail "fence comparison outside _freshness_fence"
import ast, sys
tree = ast.parse(open(sys.argv[1]).read())
owners = {"_freshness_fence"}
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name in owners:
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Compare):
                for leaf in ast.walk(sub):
                    if isinstance(leaf, ast.Name) and leaf.id == "EXTENDED_SIDECAR_MIN_DATE":
                        sys.exit(1)
PYEOF
expect_match "freshness fence: a dateless staging filename with a pre-fence sidecar date stays grandfathered" "$VRS"

# 5. Task 4 pins: one extraction regex, recompute and guard gone, one call site.
c=$(grep -cF 'Last fix commit[ \t]*:[ \t]*(.+?)' "$VRS")
[ "$c" -eq 1 ] || fail "last-fix extraction regex appears $c times, expected 1"
expect_no_match "and last_fix.strip()" "$VRS"
expect_no_match "\"neither a populated '### Witness ledger'\" in e" "$VRS"
c=$(grep -c 'validate_witness_ledger_shape(' "$VRS")
[ "$c" -eq 2 ] || fail "witness shape call sites = $c, expected def + 1 call"
expect_match "witness: a real Metadata sha with a none-spelled sidecar last_fix_commit arms the witness gate naming Metadata" "$VRS"
expect_match "witness: both surfaces carrying the same missing-ledger defect report exactly one witness error" "$VRS"

# 6. Task 5 pins: six Metadata lines in both producer copies, mirrored-fence
#    sentence in review-staging.
for f in agents/skills/rfc-design/SKILL.md agents/skills/review-confluence-doc/SKILL.md; do
  for line in \
    "- Review mode: fresh-adversarial | targeted | verification-only" \
    "- Changed-risk signals: <comma list or none>" \
    "- Prior findings supplied as filter: no" \
    "- Last fix commit: <sha or none>" \
    "- Witness ledger: <populated | N/A (no public mutators)>" \
    "- Release-gate ledger: <rows or none>"; do
    expect_match "$line" "$f"
  done
done
expect_match "rejects either mixed-fence direction" agents/skills/review-staging/SKILL.md

# 7. Task 6 pins: stale quote gone, restatements gone, pointers and owners present.
expect_no_match "undocumented top-level field" agents/skills/
expect_match "rejects unknown top-level field" agents/skills/review-staging/SKILL.md
expect_match "the validator-copy refresh recovery" agents/skills/review-staging/SKILL.md
expect_no_phrase "in the skills repo before retrying" agents/skills/doing-code-review/SKILL.md
expect_no_phrase "in the skills repo before retrying" agents/skills/review-loop/SKILL.md
expect_match "the validator-copy refresh recovery" agents/skills/doing-code-review/SKILL.md
expect_match "the validator-copy refresh recovery" agents/skills/review-loop/SKILL.md
expect_no_phrase "plan reviews have no public mutators" agents/skills/review-plan/SKILL.md
expect_no_phrase "plan reviews have no public mutators" agents/skills/plans/SKILL.md
expect_match "carries the populated-or-N/A witness shape per" agents/skills/review-plan/SKILL.md
expect_match "carries the populated-or-N/A witness shape per" agents/skills/plans/SKILL.md
expect_match "review_mode" agents/skills/review-plan/SKILL.md
expect_match "review_mode" agents/skills/plans/SKILL.md
expect_match "same truth table as the \`plans\` skill Phase 0 Step 0.1" agents/skills/execute-plan/SKILL.md
expect_no_phrase "and every other case (dirty tracked content, existing destination, or any other condition in the plans truth table) keeps the explicit confirmation" agents/skills/execute-plan/SKILL.md

# 8. Repo hygiene gate.
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || fail "public hygiene scan"
```

Note on the forbidden sweeps: patterns that also appear in this plan file (`CLEAR_ROUND_RE`, `and last_fix.strip()`, the guard fragment, the stale quote, the restated phrases) are swept only over `scripts/` and `agents/skills/`, never over `docs/plans/`, so the plan's own checker literals cannot self-match. RED-today proof, executed at authoring time 2026-09-09 against the current tree: the verdict-scoping count is 2 (expected 1), the last-fix regex count is 3 (expected 1), `and last_fix.strip()` hits 2 lines (the one inline recompute block), the guard fragment hits 1 line, `CLEAR_ROUND_RE` hits 3 lines under `scripts/`, the stale quote hits 2 files, the witness-trigger parenthetical hits both files, the refresh-tail phrase hits both files, and the F9 dropped tail hits execute-plan once: every forbidden sweep fires today and flips GREEN only when its task lands.

### Task 1: Verdict-section scoping dedup and the canonical clean-round pattern (vrs-verdict-scoping-dedup)

Files:
- `scripts/validate_review_staging.py`

- [x] Add characterization checks (GREEN before, GREEN after): the canonical `0 Medium+ findings; clear round` verdict is still clean and counts 0; the dash-separated `0 unresolved blocking findings - clear round` shape is still clean (r2 F9 separator class); a `2 Medium+ findings` verdict still extracts 2
- [x] RED: add check `clean-round digit boundary: a 10 Medium+ findings clear-round verdict is not clean and extract_medium_plus_count returns 10`; given a staging doc whose verdict section reads `10 Medium+ findings; clear round`, expects `is_clean_verdict` False and `extract_medium_plus_count` 10; run `python3 scripts/validate_review_staging.py --selftest` and expect this check FAIL (both regexes match the `0` of `10` today)
- [x] RED: add check `clean-round digit boundary: a 10 unresolved blocking findings clear-round verdict is not clean`; given a verdict reading `10 unresolved blocking findings; clear round`, expects `is_clean_verdict` False; run selftest and expect FAIL
- [x] Extract `_verdict_section(content) -> str | None` returning the scoped blob after the `## Verdict for this round (before fixes)` heading, None when the heading is absent; rewire `is_clean_verdict` (None means not clean, r2 F8 semantics preserved) and `extract_medium_plus_count` (None falls back to the whole document for counting, exactly as today) to consume it
- [x] Add the negative lookbehind `(?<!\d)` to the leading `0` of `CLEAN_VERDICT_RE`; derive the clear-round early return in `extract_medium_plus_count` from `CLEAN_VERDICT_RE` (the superset pattern); delete `CLEAR_ROUND_RE` and update the comment that references it; verify the only behavior deltas are the canaried boundary fixes (a dash-separated clean phrase now early-returns 0 through the canonical pattern where it previously fell through to the same 0 via fallback)
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN (all checks, including the two new boundary canaries)
- [x] Commit: `validator: single verdict-section scoping + one canonical clean-round pattern with digit boundary`

### Task 2: Freshness value-gate tails (vrs-freshness-value-gate-tails)

Files:
- `scripts/validate_review_staging.py`

- [x] RED: add check `freshness: an empty-valued gated Metadata label fails naming the label and the empty value`; given a post-fence staging doc whose Metadata carries `- Review mode:` with an empty value side, expects a named error from `validate_freshness_metadata` naming the label and the empty value; run selftest and expect FAIL (the presence gate passes the line, every value gate stays silent)
- [x] Implement: inside the `gated_labels` loop of `validate_freshness_metadata`, after the duplicate-label check, a Metadata line matching `^-[ \t]*<label>[ \t]*:[ \t]*$` (nothing after the colon) is a named error; the three gated labels are `Review mode`, `Prior findings supplied as filter`, `Last fix commit`
- [x] RED: add check `freshness: a clear-round phrase without a recognizable clean-round verdict warns`; given a doc whose canonical verdict section reads `No Medium+ findings; clear round.`, expects a named warning; run selftest and expect FAIL
- [x] Add characterization check `freshness: the canonical clean-round verdict does not warn`; given a doc with `0 Medium+ findings; clear round`, expects no clear-round-phrase warning; GREEN before (no warning exists yet) and GREEN after (pins no false positive on the canonical shape; this check never has a RED state)
- [x] Implement: a new `validate_clear_round_phrase(content, result)` wired into `validate_staging_file` beside `validate_verdict_heading_grammar`: when the verdict-section blob (via `_verdict_section`, Task 1) contains the phrase `clear round` (case-insensitive) without a `CLEAN_VERDICT_RE` match, add a named warning advising the canonical shapes; warning severity is deliberate (a negated phrasing like "not a clear round" is an honest non-clean verdict and must not fail validation)
- [x] Restage the `no-freshness-lines-before` grandfathering canary with `clean_md(fresh_lines=False)` so it actually exercises the stripped pre-fence shape, and fix its comment to say the doc is stripped on both surfaces; the check stays GREEN (the stripped pre-fence doc passes today and after)
- [x] RED: add check `freshness: a non-UTF-8 stats sidecar reports a named error instead of a traceback`; given a staging doc whose sidecar file contains invalid UTF-8 bytes, expects a named validation error and no exception; run selftest and expect FAIL (uncaught `UnicodeDecodeError`)
- [x] RED: add check `freshness: a non-UTF-8 staging file reports a named error instead of a traceback`; given a staging file with invalid UTF-8 bytes, expects the named cannot-read error; run selftest and expect FAIL
- [x] Implement: extend the except tuple with `UnicodeDecodeError` on the best-effort sidecar read in `validate_staging_file`, the main sidecar read in `validate_stats_sidecar`, and the staging content read in `validate_staging_file`
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN
- [x] Commit: `validator: freshness value-gate tails (empty label error, clear-round warning, stripped pre-fence canary, UTF-8 guards)`

### Task 3: Freshness fence consolidation into one helper (vrs-freshness-fence-single-helper)

Files:
- `scripts/validate_review_staging.py`

- [x] Add characterization check `freshness fence: a dateless staging filename with a pre-fence sidecar date stays grandfathered`; given a dateless staging filename and a sidecar dated before `EXTENDED_SIDECAR_MIN_DATE`, expects validation to pass with no freshness gate armed (today's silent shape; this is the shape Design Invariant 2 protects); run selftest and expect GREEN before the refactor
- [x] Extract one helper (suggested shape `_freshness_fence(staging_name, sidecar_date)`) that owns every fence computation: the leading-date parse of the staging name, the parse of the sidecar date, and the comparisons against `EXTENDED_SIDECAR_MIN_DATE`; it exposes per-surface classifications (undated, pre-fence, post-fence for each surface), where a missing or malformed sidecar date classifies as undated, never silently pre-fence
- [x] Rewire the three consumers: `validate_date_keyed_freshness_lines` (presence gate arms on a post-fence filename; the r3 F11 error fires on undated name plus post-fence sidecar; undated name plus pre-fence sidecar stays silent), and `validate_version1_payload` (extended-field exemption keys on sidecar pre-fence, which already excludes undated; the r2 F3 backdate refusal and exemption strip; the r4 F7 mirrored direction); no consumer re-derives a date fence inline afterward; error-message interpolations of the constant stay byte-identical (the canaries pin those strings), and the AST pin counts only `Compare` nodes, so interpolated error text is exempt by construction
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN unchanged (every fence outcome byte-identical, including the new characterization check)
- [x] Commit: `validator: consolidate the freshness grandfathering fence into one helper (behavior-neutral)`

### Task 4: Witness twin single call and shared last-fix extraction (vrs-witness-twin-single-call)

Files:
- `scripts/validate_review_staging.py`

- [x] Add characterization check `witness: a real Metadata sha with a none-spelled sidecar last_fix_commit arms the witness gate naming Metadata`; given a post-fix doc with a real Metadata `Last fix commit` sha and a sidecar `last_fix_commit` of `none`, expects the witness error naming the Metadata surface (pins first-real-sha-wins; GREEN today via the Metadata-path call, must stay GREEN after the consolidation)
- [x] Add characterization check `witness: both surfaces carrying the same missing-ledger defect report exactly one witness error`; given a post-fix doc with the same real sha on both surfaces and neither ledger shape, expects exactly one witness error (GREEN today via the string-match guard, GREEN after via the single call)
- [x] Extract `_metadata_last_fix(content) -> str | None` owning the single copy of the Metadata last-fix extraction regex; route the three extraction sites through it: `validate_freshness_metadata` (the r1 F5 twin), `validate_staging_file` (the witness feed), and the r3 O16 cross-surface block in `validate_stats_sidecar`; every presence check routes through `_last_fix_present` or `_metadata_last_fix` (no inline strip-and-compare remains anywhere)
- [x] Replace the inline `_last_fix_present` recompute in `validate_version1_payload` with a call to the existing module-level `_last_fix_present` helper (identical semantics, verified 2026-09-09)
- [x] Make `validate_stats_sidecar` return the parsed payload dict (None on its early exits); delete the witness call inside it; delete the string-match dedupe guard from `validate_witness_ledger_shape` and its docstring mention
- [x] Resolve the value once in `validate_staging_file` after `validate_stats_sidecar` returns, preserving the r3 F8 scoping: use the sidecar value only when the payload classifies current-v1 (legacy, unsupported, and versionless-current payloads never arm the sidecar twin today and must not after; the existing r3 F8 scoping canary stays green); under that scoping, if the sidecar value is a real sha call the shape check once with source `sidecar`, elif the Metadata value is a real sha call it once with source `Metadata`; move the single call after the sidecar validation so the resolved payload is available
- [x] Run `python3 scripts/validate_review_staging.py --selftest` → expect GREEN unchanged (the incident-shape canaries for the witness gate stay green; gate outcomes are unchanged for every record; the only observable deltas are error wording: in the both-real-shas missing-ledger shape the surviving error names the sidecar instead of Metadata, and the single witness call may move the error later in the error list; no canary pins either wording)
- [x] Commit: `validator: resolve last fix commit once in the witness twin + shared extraction helper (behavior-neutral)`

### Task 5: Producer-template freshness contract alignment (producer-template-freshness-contract, items 1 and 3)

Files:
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/review-confluence-doc/SKILL.md`
- `agents/skills/review-staging/SKILL.md`

- [x] In the rfc-design inlined staging Metadata template (the `## Metadata` block in the review-staging example section), add the six lines mirroring the review-plan template: `- Review mode: fresh-adversarial | targeted | verification-only`, `- Changed-risk signals: <comma list or none>`, `- Prior findings supplied as filter: no`, `- Last fix commit: <sha or none>`, `- Witness ledger: <populated | N/A (no public mutators)>`, `- Release-gate ledger: <rows or none>`
- [x] Add the same six lines to the review-confluence-doc inlined Metadata template in Step 4.7's staging example
- [x] In the review-staging extended-field grandfathering paragraph, add one sentence stating the validator rejects either mixed-fence direction: a sidecar dated earlier than a post-fence staging filename cannot claim the exemption (and the exemption is stripped), and a pre-fence filename with a post-fence sidecar date fails the date-disagreement error; use the phrase `rejects either mixed-fence direction` verbatim (the Validation Command pins it)
- [x] Grep-check both templates carry all six lines and review-staging carries the sentence (the Task 5 commands in the Validation block); run them → expect GREEN
- [x] Commit: `skills: producer-template freshness contract alignment (rfc-design, review-confluence-doc, review-staging)`

### Task 6: Consumer-prose dedup to pointer shape (skill-prose-dedup-pointers F8 + F9, producer-template item 2)

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-staging/SKILL.md`

- [x] In review-staging, add the owning recovery sentence (near the extended-field contract): on a `rejects unknown top-level field` validator error naming a field the current contract defines, refresh the installed validator copy and retry; include the phrase `the validator-copy refresh recovery` in the pointer-facing wording so consumers can point at it (this is the owner sentence for the reduction below and carries the CORRECT emitted text, replacing the stale quote)
- [x] In doing-code-review and review-loop, replace the verbatim freshness-fields-plus-recovery sentence with the rfc-design pointer shape: keep the four freshness-field names inline, point at `review-staging` for the contract, the min-date fence, and the validator-copy refresh recovery; the stale `undocumented top-level field` quote disappears with the restatement (this one edit closes producer-template item 2 and the F8 validator-refresh half together)
- [x] In review-plan and plans, reduce the verbatim witness-trigger sentence to the pointer shape: `When last_fix_commit is non-null, the staging Markdown Metadata carries the populated-or-N/A witness shape per review-staging.`; keep the freshness-field name enumerations (the `review_mode` producer-copy pins must stay green)
- [x] In execute-plan Step 0.1c, trim the auto-path paragraph to the pointer plus the pinned trunk-condition literal: keep the existing pointer phrase ``same truth table as the `plans` skill Phase 0 Step 0.1`` verbatim, keep only the trunk condition (the current branch is exactly `master` or `main` with both porcelain checks empty) and a single short reworded everything-else sentence without the enumerated case list (for example: every other condition in the plans truth table keeps the explicit confirmation ask); the old enumerated tail is exactly what the forbidden-sweep pin targets
- [x] Re-check the frozen-region rule for each edited file against this plan's Review Scope (all six files are explicit must-fix here; edits are confined to the named sentences and the Step 0.1c paragraph)
- [x] Grep-check the Validation block's Task 6 commands → expect GREEN
- [x] Commit: `skills: dedup consumer prose to pointer shape (F8/F9) + correct unknown-field error quote`

### Task 7: Full validation

Files: none (verification only)

- [x] Run the entire `## Validation Commands` block from the repository root → expect every command GREEN
- [x] Run `python3 scripts/validate_review_staging.py --selftest` once more standalone → expect exit 0
