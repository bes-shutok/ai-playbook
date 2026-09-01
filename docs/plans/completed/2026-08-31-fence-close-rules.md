# Plan: Fence scanner close-rule fixes + scanner simplification

Backlog origin: `docs/history/backlog/2026-08-29-fence-scanner-followups.md` (items 1-4; archived by Task 5).
Prior phase: `docs/plans/completed/2026-08-28-fence-scanner-consolidation.md` (Task 3 contracts deliberately superseded by this plan; see Design Invariants).
Review artifacts for this plan: `docs/reviews/2026-08-31-plan-review-fence-close-rules-r<N>.md` (prefix reference; rounds not enumerated here).

## Terms

- **The classifier**: `classify_fence_lines` (`scripts/validate_review_staging.py:299`), the single fence state machine shared by every Markdown scanner in the validator (consolidation r1 F3).
- **Close rule**: the test deciding whether a fence-regex-matching line closes the currently open fence. TODAY: an equal-or-longer delimiter run of EITHER fence character, info string allowed. NEW: same delimiter character as the opener + equal-or-longer run + bare line.
- **Bare close line**: a line whose stripped content is a run of ONLY the opener's delimiter character, length at least the opener's (a bare `~~~` line closes a `~~~` fence; `~~~x` and an inner ```` ```python ```` never close anything).
- **Openers**: fence-opening lines; keep CommonMark open semantics UNCHANGED: prefix match, info strings allowed (```` ```python ```` OPENS a fence), either character, run of 3 or more.
- **Reset axis**: today two parameters (`reset_at_headings: bool` + `is_reset_heading` predicate); NEW: predicate only and keyword-only (`classify_fence_lines(lines, *, is_reset_heading=None)`: `None` is content-preserving, a callable is heading-reset mode, and no positional second argument is accepted at all).
- **Fallback driver**: the duplicated shape "classify content-preserving; if a fence never closed, keep pre-opener first-pass results and re-classify the suffix with the consumer's reset predicate" (r6 F3), duplicated at `:416-433` and `:571-600`; NEW: one shared helper `classify_with_fallback`.
- **Fence fixture cluster**: the fence-related selftest checks inside `_selftest_versioned_schema_and_patterns` (def `:3838`), roughly `:4300-4725`: five slug-tagged check families (`# tilde-closed-example`, `# tilde-unclosed-containment`, `# classifier-guard`, `# fallback-preserves-fenced-example`, `# fallback-same-severity-group`) plus the earlier untagged fence checks (~`:4347-4456`: quoted-example, unclosed, fence-length, and fenced-heading pins).
- **Check slug**: the `(# <slug>)` suffix of a selftest `check()` first argument, used as a stable anchor.
- **Skill-gate marker**: `plans.<project>.<session>.marker` under `~/.ai-playbook/runtime/skill-invoked/`, refreshed before EVERY plan-file write via `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker` with `--session-id "$SID"` where `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; fail-loud if unwritable.
- **Session key**: the marker's session component; empty-after-strip becomes `no-session`, otherwise `sha1(value)[:16]` hex.

## Assumptions

- assume all four backlog items land in one plan; basis: user directive 2026-08-31 ("items 1 + 4, with 2 + 3 riding along ... one plan covers all four").
- assume branch base is main at 6ee756e (branch `2026-08-31-fence-close-rules`, push stays off); basis: v1 gate trio squash-merged to main as 6ee756e on 2026-08-31, clean tree, branch convention confirmed 2026-08-30.
- assume the new close contract is char-match + equal-or-longer + bare; basis: CommonMark fence spec, backlog items 1/4 suggested fixes, and probes A/B/E run against the real classifier (probe E pins that same-char equal-or-longer bare closes stay legal).
- assume openers keep info strings and prefix match; basis: CommonMark open rule; the existing tilde fixtures already rely on a `~~~python` OPENER.
- assume RED fixtures for the overwrite arm inject into the METADATA REGION (between the field bullets and the first `####` sub-heading); basis: probe C2 (metadata region misparses) vs probe C (a `#### Comment` placement is protected by the r3 F2 metadata-region gate, so it cannot demonstrate the overwrite).
- assume the two refactors (reset-axis collapse, driver extraction) are characterization-guarded GREEN work, not RED->GREEN; basis: plans skill pure-refactoring rule; the existing fixture cluster is the characterization net.
- assume the unclosed-example fallback promotion (quoted headings after an unclosed opener parse as live findings, ids `[1, 7]` for the probe shape) is pin-as-characterization only, never changed by this plan; basis: security-relaunch probe (identical output today and under the simulated new rule), pre-existing documented r4 F3 / r6 F3 tradeoff.
- assume no documentation updates in `agents/skills/`; basis: `agents/skills/review-staging/SKILL.md:245` (snippet-format paragraph) read and verified true post-change: it describes fence-aware splitting/re-parse generically and keys its producer rule on the severity-group scan, which stays fence-blind; documentation minimalism otherwise.

## Gist & Examples

The validator is the quality gate for every review artifact in this repo. Its shared fence classifier closes a fenced block on ANY equal-or-longer delimiter run, ignoring the delimiter character and ignoring whether the line is bare. Two verified consequences:

1. **Silent misparse (backlog item 1; probe-verified end-to-end).** A finding whose METADATA REGION contains a fenced example embedding a bare `~~~` line lets an in-example bullet overwrite real parsed metadata:

````markdown
#### F1.
- **Blocking**: false
- **Triage**: pending

```
text
~~~
- **Blocking**: true
```
````

Today the bare `~~~` closes the backtick fence (cross-char, length-only), the bullet lands OUTSIDE any fence inside F1's metadata region, and `parse_markdown_findings` returns a true blocking value for F1 while the real bullet says false; `is_review_ready` silently flips. After the fix the whole example stays fenced content, F1 keeps its real blocking value, and readiness is unchanged. The same promotion shape via an inner ```` ```python ```` line (backlog item 4) is killed by the same bareness requirement.

2. **Phantom finding from an inner info-string closer, properly closed examples (backlog item 4; probe-verified end-to-end).** A properly fenced staging-format example inside a `#### Comment` that quotes an inner ```` ```python ```` line followed by a quoted `#### F99.` header: today the inner line CLOSES the outer fence (equal length, info string ignored), the quoted header becomes a live finding, and the parse returns ids `[1, 99]` with `split_finding_blocks` producing 2 blocks (expected 1), tripping the conservation check with an error naming content that was never a finding. After the fix the quoted snippet stays fenced; ids are `[1]`; one block. Scope note: this suppression holds for PROPERLY CLOSED examples. For an UNCLOSED example, the documented r4 F3 / r6 F3 partial fallback deliberately re-classifies from the opener with the consumer's reset predicate, so quoted headings after the opener remain live structure by design; that residual is pre-existing, unchanged by this plan, and pinned as characterization (Task 4, `# phantom-unclosed-fallback`).

3. **What stays legal (keep-valid, probe-verified).** A bare same-char run equal or longer closes (`~~~~~~` closes `~~~~`); trailing or leading whitespace does not block a close (`~~~ ` and `  ~~~` both close; the leading-whitespace allowance is wider than CommonMark's 3-space limit, inherited from the frozen FENCE_LINE_RE `^\s*` prefix and deliberately kept); a shorter run stays content; a non-bare line (`~~~x`) stays content; ```` ```python ```` at top level still OPENS a fence; the existing tilde fixtures (`~~~python` opener, `~~~` closer) stay green unchanged.

4. **Placement nuance the fixtures must respect.** The r3 F2 gate already protects `#### Comment`/`#### Analysis` bodies from ordinary-bullet overwrites (probe C: no misparse there). The overwrite arm is only reachable from the metadata region (probe C2). The RED fixtures therefore inject before the first `#### Comment` occurrence; the phantom arm (heading promotion) works from either placement and uses the Comment placement, matching the existing `fallback-preserves-fenced-example` fixture style.

5. **Documented behavior change on malformed fences (fail-open direction; security-relaunch probe).** Documents that today close a fence through a cross-character or non-bare line are malformed per CommonMark, and their today-parse is accidental. After this change those fences never close, and the r6 F3 fallback does not recover post-opener bullets, so a real field bullet sitting after such a false closer is swallowed (`blocking` stays unset, which `is_review_ready` documents as ready). A repo-corpus sweep (docs/reviews, docs/plans, docs/history, agents) found zero verdict changes; one artifact (doing-code-review/SKILL.md) changes its internal fence path from the fallback re-parse to the normal path with identical output. The direction of the change is recorded here so it is a documented tradeoff, not a surprise. A fail-loud diagnostic for unclosed fences is proposed as a backlog follow-up (Task 5), not built here.

Simplifications riding along (backlog items 2 + 3, same functions): the reset axis collapses to a single predicate parameter (`None` = content-preserving), making the half-configured `reset_at_headings=True` without a predicate mode unrepresentable, so the r2 `ValueError` guard and its selftest check are replaced by new-contract checks; the `fence_opener` event drops its `delimiter_length` payload (verified write-only: only the emit site `:362` and docstring `:312` mention it); and the duplicated partial-fallback driver is extracted into one shared helper so the classify-twice orchestration lives in one place (consumers keep their own offset/interpretation; see Design Invariant 1). One deliberate omission: the identical `## Findings` section-extraction prelude duplicated between the two consumers (~`:390-394` vs ~`:471-475`) is NOT consolidated here; it is recorded as a backlog follow-up (Task 5) so the omission is deliberate rather than unnoticed.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the new close-rule fixtures go RED->GREEN; the silent-misparse fixture returns a false blocking value and `is_review_ready(...) is True`; the phantom fixture returns ids `[1]` and one split block; probes A/B/C2/F shapes all covered.
- regression safety: full `--selftest` green at every GREEN/refactor commit; all pre-existing fence-cluster checks stay green except the deliberately replaced `# classifier-guard` (they are the characterization net for both refactors, including the new `# phantom-unclosed-fallback` pin of the documented fallback tradeoff).
- simplification: one reset axis (predicate-only), one fallback driver, no unread event payload; no new parameters or modes invented.
- fail-loud honesty: the docstring's close-rule sentence states the NEW contract and the supersession of the consolidation plan's length-only pin.

**Done when:**
- All tasks checked; `python3 scripts/validate_review_staging.py --selftest && echo "SELFTEST OK"` green.
- Stale-reference sweeps for `reset_at_headings`, `delimiter_length`, and the retired `# classifier-guard` check are zero-match (negated commands).
- `docs/history/backlog/2026-08-29-fence-scanner-followups.md` archived to `completed/` with `Status: done`, and the round-2 follow-up backlog item created.

**Ship when:**
- The branch merges to main by the user's decision (human-owned; push stays off until explicitly requested). No deploy or cross-team condition exists for this repo.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py` (PARTIAL): `classify_fence_lines` incl. docstring (~`:299-386`), `split_finding_blocks` (~`:389-451`), `parse_markdown_findings` (~`:454-603`), `classify_with_fallback` *(new; inserted after the classifier)*.

**Tests:**
- `scripts/validate_review_staging.py` (PARTIAL): the fence fixture cluster inside `_selftest_versioned_schema_and_patterns` (~`:4300-4725`; the five slug-tagged families named in Terms, the untagged early fence checks ~`:4347-4456`, plus the new slugs from Task 1 and Task 3).

**Documentation / backlog:**
- `docs/history/backlog/2026-08-29-fence-scanner-followups.md` (PARTIAL; Task 5 archival edit only).
- `docs/history/backlog/2026-08-31-fence-scanner-round-2.md` *(new)*; Task 5 follow-up capture.

**Freeze notes (partial-in-scope):** everything else in `scripts/validate_review_staging.py` is FROZEN: the v1 gate trio regions (`validate_version1_payload`, the findings loop, and their fixtures, merged as 6ee756e), `validate_finding_order`, conservation checks, stats-sidecar logic, CLI wiring, and the `FENCE_LINE_RE`/`HEADING_LINE_RE` definitions. Reject any review finding that touches frozen regions; a real bug in a frozen region becomes a backlog item, not an in-place fix.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by the close-rule or API changes, or contradicts a contract this plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/summarize_review_stats.py`; reason: untouched by this plan (no shared symbols; caller inventory verified).
- `agents/skills/**`; reason: `review-staging/SKILL.md:245` verified true post-change; no wording depends on the old close semantics.
- `docs/plans/completed/*`; reason: frozen history; the superseded consolidation contract is declared here, not edited there.
- Other `docs/history/backlog/` items (everything under `docs/history/backlog/` except the two Task 5 paths above) and `README.md`; reason: no catalog or sibling-item change.

## Design Invariants (CR Guard)

1. **Single fence state machine** (consolidation r1 F3): all fence tracking stays inside `classify_fence_lines`; consumers keep only their interpretation of events (boundary indices vs finding/metadata assembly). The new helper reuses the classifier; it does not re-implement tracking.
2. **Opener semantics unchanged**: prefix match, info strings allowed, either character, run >= 3. Only the CLOSE rule tightens.
3. **Close rule**: same delimiter character + equal-or-longer run + bare line. The r5 F5 length requirement is KEPT; its char-blindness and bareness gap are superseded (declared supersession of consolidation Task 3's length-only pin; do not "restore" the old rule in review).
4. **Partial fallback contract** (r6 F3): pre-opener first-pass results kept; suffix re-classified with the consumer's own reset predicate; parser state seeding unchanged (severity label, metadata flag, open finding flushed with pre-opener bullets, no double-append; post-opener bullets are not recovered). The parser's fallback branch applies ONLY the pre-opener prefix (`events[:unclosed_opener]`) of the first-pass events, never the full list; post-opener interpretation comes solely from `reset_events`. The unclosed-example promotion of quoted headings (F4 residual) is documented, pinned as characterization, and never changed here.
5. **r4 F3 containment preserved**: an unclosed fence cannot swallow later findings.
6. **r5 F8 fenced-example purity preserved**: heading-like lines inside a CLOSED fence are content.
7. **r2 guard purpose preserved structurally**: after the collapse, heading-reset mode REQUIRES an explicit predicate; the half-configured mode is unrepresentable. The `# classifier-guard` ValueError check is REPLACED by the `# reset-axis-contract` checks, not silently dropped.
8. **Event vocabulary**: kinds unchanged (`fence_opener`/`fence_close`/`in_fence_content`/`heading`/`ordinary`); the `fence_opener` payload becomes `None` (verified write-only). Consumer event interpretation untouched.
9. **r3 F2 metadata-region gate untouched**: it remains the second layer of defense (probe C); this plan must not weaken or bypass it.
10. **v1 gate trio regions frozen** (merged as 6ee756e): no fixture or production edits outside the Review Scope's named functions and cluster.

## Validation Commands

```bash
# Primary gate: full selftest (includes every fence-cluster fixture, old and new).
python3 scripts/validate_review_staging.py --selftest && echo "SELFTEST OK"

# Zero-match sweeps: all three are scripts/-scoped, and this plan file lives in
# docs/plans/ (outside scripts/), so its own text can never satisfy them; the
# bracket escapes on the first two are kept defensively, do not "normalize" them.
if grep -rn "reset_at_headin[g]" scripts/; then echo "STALE reset-axis parameter"; exit 1; fi
if grep -rn "delimiter_lengt[h]" scripts/; then echo "STALE fence_opener payload name"; exit 1; fi
if grep -rn "classifier-guard" scripts/; then echo "STALE retired guard check"; exit 1; fi

# Presence pins: shared driver exists, the new-contract docstring landed, and
# every new check slug landed.
grep -q "def classify_with_fallback" scripts/validate_review_staging.py || { echo "shared fallback driver missing"; exit 1; }
grep -q "same delimiter character" scripts/validate_review_staging.py || { echo "close-rule docstring missing"; exit 1; }
for slug in close-rule-in-reset-mode cross-char-close bare-close-info-string bare-close-keep-valid silent-misparse-metadata-region phantom-f99-info-string phantom-unclosed-fallback reset-axis-contract; do
  grep -q "(# $slug)" scripts/validate_review_staging.py || { echo "missing check slug: $slug"; exit 1; }
done
```

### Task 1: RED close-rule fixtures (behavior arm)

Files:
- `scripts/validate_review_staging.py` (fence fixture cluster of `_selftest_versioned_schema_and_patterns`, adjacent to the `# classifier-guard` block ~`:4537`)

Fixture assertion convention: Task 1 behavioral fixtures compare event KINDS plus `unclosed_opener` only (payload-agnostic), never full tuples; full-tuple comparison is reserved for the Task 3 `# reset-axis-contract` checks, which run after the payload drop.

- [x] `# cross-char-close` (classifier-direct); given `["```", "x = 1", "~~~", "- **Blocking**: true", "```"]` passed to `classify_fence_lines`, expects events `["fence_opener", "in_fence_content", "in_fence_content", "in_fence_content", "fence_close"]` and `unclosed_opener is None`, i.e. the bare `~~~` line does NOT close the backtick fence and the final bare ```` ``` ```` DOES. RED today (verified: today emits `[fence_opener, in_fence_content, fence_close, ordinary, fence_opener]` with unclosed 4). The load-bearing pins are the two middle `in_fence_content` events. Second arm, longer cross-char run: given `["~~~", "```", "text", "~~~"]`, expects `["fence_opener", "in_fence_content", "in_fence_content", "fence_close"]` and `unclosed_opener is None` (a longer run of the WRONG character still never closes). RED today (the inner ```` ``` ```` closes on length). Third arm, mixed-character line: given `["```", "```~~~", "```"]`, expects `["fence_opener", "in_fence_content", "fence_close"]` and `unclosed_opener is None` (a line mixing both characters is not bare, so it never closes). RED today (the mixed line closes on its backtick run's length).
- [x] `# bare-close-info-string` (classifier-direct); given `["```", "intro", "```python", "- **Blocking**: true", "```"]`, expects the ```` ```python ```` line to stay `in_fence_content` and only the final bare ` ``` ` to emit `fence_close`; given `["```", "~~~x", "```"]`, expects `~~~x` to stay `in_fence_content` (close requires a bare line); given `["~~~", "~~~x", "~~~"]`, expects `~~~x` to stay `in_fence_content` (same character, so bareness alone is isolated). RED today on all three arms (verified: info-string, cross-char non-bare, and same-char non-bare lines all emit `fence_close` today).
- [x] `# bare-close-keep-valid` (classifier-direct, GREEN today, must stay green through every later task). Implement as ONE check() per arm, all carrying the same `(# bare-close-keep-valid)` slug (the cluster's existing multi-check-per-slug idiom), so a failing arm is named by its own FAIL line: given `["~~~~", "x", "```", "y", "~~~~~~"]`, expects the final `~~~~~~` to emit `fence_close` with `unclosed_opener is None`; given `["~~~~", "~~~"]`, expects the shorter bare same-char run to stay `in_fence_content` with `unclosed_opener == 0` (the length rule is kept); given `["~~~", "~~~ "]`, expects the trailing-whitespace line to emit `fence_close` with `unclosed_opener is None`; given `["~~~", "x", "  ~~~"]`, expects the indented `  ~~~` to emit `fence_close` (leading whitespace allowed); given a top-level ```` ```python ```` line, expects `fence_opener` (openers keep info strings).
- [x] `# silent-misparse-metadata-region` (end-to-end); build F1 (`_current_finding(id=1, severity="High", blocking=False)` with `triage` pending) via `_current_findings_markdown`, then inject a fenced example into the METADATA REGION by replacing the first `#### Comment` occurrence with the example followed by `#### Comment` (the example: an outer ` ``` ` fence containing `text`, a bare `~~~` line, and a true blocking bullet); assert the injected fences are present (defang guard, same pattern as the tilde fixtures' asserts); expects `parse_markdown_findings` to return exactly one finding whose blocking is false and `is_review_ready(...) is True`. RED today (verified: parsed blocking true, readiness flips).
- [x] `# phantom-f99-info-string` (end-to-end); build F1 (`_current_finding(id=1, severity="High", blocking=True)`, triage pending) via `_current_findings_markdown`, then replace the first `#### Comment` occurrence with the injected example followed by `#### Comment`, where the example is a PROPERLY CLOSED outer ` ``` ` fence (in the Comment body) containing an inner ```` ```python ```` line, a quoted `#### F99.` header, and field bullets; defang asserts before the parse assertions, presence-based (the `fallback-preserves-fenced-example` idiom): `"```python" in md` and `"#### F99." in md`. Do NOT assert fence-marker parity: the fixture contributes exactly three fence-pattern lines (outer, inner info-string, closer), so a parity assert can never hold, and today's parse shape is deliberately not a closed pair. Expects `parse_markdown_findings` ids `== [1]` and `len(split_finding_blocks(...)) == 1`. RED today (verified: ids `[1, 99]`, 2 blocks).
- [x] Run `python3 scripts/validate_review_staging.py --selftest` -> expect RED exactly on the four new behavioral checks; `# bare-close-keep-valid` and every pre-existing cluster check stay green.
- [x] Commit: `test: RED fence close-rule fixtures (cross-char, bare close, silent misparse, phantom)` (deliberate TDD staging: this commit intentionally leaves the suite RED on exactly the four new checks; Task 2 lands GREEN)

### Task 2: GREEN close rule (char-match + bare)

Files:
- `scripts/validate_review_staging.py` (`classify_fence_lines` only)

- [x] At the opener branch, capture the delimiter character (`fence_match.group(1)[0]`) alongside `fence_len`; clear it wherever `fence_len` is cleared today (close branch, heading-reset branch).
- [x] Replace the close test: close iff `line.strip()` consists solely of the opener's character AND its length is >= `fence_len` (leading/trailing whitespace allowed; the FENCE_LINE_RE match continues to gate entry into the fence branch, and a bare 3+ run always matches it, so no candidate close line is missed). Regex-matching lines failing the bare/char test emit `in_fence_content`.
- [x] Rewrite the docstring close-rule sentence (the one citing "r5 F5; the delimiter character is not compared"): state that a fence closes only on a bare, equal-or-longer run of the same delimiter character, that openers keep prefix match with info strings, and that this supersedes the consolidation plan's length-only pin (the validation block greps for the exact span "same delimiter character", so keep that phrasing).
- [x] Align the second close-rule restatement: the r4 F3 comment in `parse_markdown_findings` (~`:487-489`, "the fence tracker is fence-length aware ...") describes the old length-only rule; update it to state the full rule or point at the classifier docstring, so the file does not carry two divergent close-rule descriptions.
- [x] Run Task 1 fixtures -> GREEN on all four; `# bare-close-keep-valid` and every pre-existing cluster check stay green; full `--selftest` green.
- [x] Commit: `fix: fence close requires matching delimiter character and bare line`

### Task 3: Refactor reset axis to predicate-only; drop unread payload

Files:
- `scripts/validate_review_staging.py` (`classify_fence_lines`, call sites `:416` `~:426-429` `:571` `~:593-596` `:4514` `:4539`, selftest `# classifier-guard` block)

- [x] Characterization first: run full `--selftest` -> green before touching anything (record the run).
- [x] Collapse the signature to `classify_fence_lines(lines, *, is_reset_heading=None)` (predicate keyword-only): `None` is content-preserving (r5 F8), a callable is heading-reset mode (r4 F3), and a positional second argument is rejected with TypeError at call time on ANY input, making the half-configured mode and its stragglers structurally unrepresentable rather than conventionally. Delete the `reset_at_headings` parameter and the `ValueError` guard (~`:338-342`). Rewrite the docstring reset-policy paragraph accordingly.
- [x] Change the opener event to `("fence_opener", None)` and update the docstring vocabulary line; the `delimiter_length` value has no readers (verified: emit site `:362` + docstring `:312` are its only mentions).
- [x] Rewire the reset-mode call sites: the `~:426-429` and `~:593-596` calls become `classify_fence_lines(lines[unclosed_opener:], is_reset_heading=<that consumer's predicate>)` (keyword form, already compatible with the keyword-only marker); `:416`, `:571`, `:4514` are unchanged (content-preserving). No call site may pass a positional second argument: the keyword-only marker now rejects it loudly at call time on any input; the `reset_at_headings` sweep and the `# reset-axis-contract` checks remain the straggler gates.
- [x] Replace the `# classifier-guard` block (the WHOLE block: header comment `# classifier-guard (r2 F1)` at ~`:4537` through the try/except at ~`:4547`) with `# reset-axis-contract` checks: (a) given `["~~~", "### High", "x"]` with NO predicate, expects `[("fence_opener", None), ("in_fence_content", None), ("in_fence_content", None)]` and `unclosed_opener == 0` (content-preserving default; probe-verified); (b) given `["~~~", "#### F2.", "y"]` with a finding-header predicate, expects `[("fence_opener", None), ("heading", "#### F2."), ("ordinary", "y")]` and `unclosed_opener is None` (reset activates by predicate alone). The `classifier-guard` stale sweep requires no residue of either the check or its header comment.
- [x] Run full `--selftest` -> green (the tilde/unclosed/fallback cluster checks are the characterization net for this signature change).
- [x] Commit: `refactor: collapse fence reset axis to predicate-only, drop unread opener payload`

### Task 4: Refactor shared fallback driver

Files:
- `scripts/validate_review_staging.py` (new `classify_with_fallback`; `split_finding_blocks` `:416-433`; `parse_markdown_findings` `:571-600`)

- [x] Add module-level `classify_with_fallback(lines, is_reset_heading)` immediately after the classifier, returning `(events, unclosed_opener, reset_events)`: first pass content-preserving over ALL lines; when a fence never closed, re-classify `lines[unclosed_opener:]` with `is_reset_heading` and return those events as `reset_events`, else `reset_events is None`. Docstring states the r6 F3 partial-fallback contract AND why the predicate is required here while the classifier's is optional (the helper only ever runs the reset mode, and reset mode must never run without its explicit predicate; an optional predicate here would recreate the half-configured mode the Task 3 collapse removes). The predicate is a required positional (both consumers always have one).
- [x] Rewire `split_finding_blocks`: `events, unclosed_opener, reset_events = classify_with_fallback(lines, is_finding_header)`; when `reset_events is not None`, boundaries = pre-opener filter (`i < unclosed_opener`) plus `[unclosed_opener + i for i in boundary_indices(reset_events)]`. The helper owns the two-pass orchestration (classify, detect the unclosed opener, re-classify the suffix); the consumers keep ownership of offset remapping and event interpretation.
- [x] Rewire `parse_markdown_findings`: same helper with its `is_reset_heading`; the `reset_events is None` branch applies events as today; the fallback branch applies `events[:unclosed_opener]` ONLY (never the full list), flushes the open finding, and applies `reset_events` with the seeded state; the event-interpreting `apply_events` code is untouched.
- [x] Characterization: add `# phantom-unclosed-fallback` (GREEN today, must stay green): an UNCLOSED outer fence in a finding's Comment body quoting `### Low`, a `#### F7.` header, and field bullets; expects `parse_markdown_findings` ids `== [1, 7]` with F7's severity `Low` (the documented r4 F3 / r6 F3 fallback promotion residual; probe-verified identical today and under the new close rule). Then run full `--selftest` -> green; the fallback path is exercised by `# tilde-unclosed-containment`, `# fallback-preserves-fenced-example`, `# unclosed`, and this new pin, which must all stay green.
- [x] Commit: `refactor: extract shared fence partial-fallback driver`

### Task 5: Backlog archival + follow-up capture

Files:
- `docs/history/backlog/2026-08-29-fence-scanner-followups.md` -> `docs/history/backlog/completed/2026-08-29-fence-scanner-followups.md`
- `docs/history/backlog/2026-08-31-fence-scanner-round-2.md` *(new)*

- [x] `git mv` the followups item to `completed/` and edit it: `Status: done`; closure note recording that items 1 and 4 are fixed by the char+length+bare close rule (with the verified silent-misparse and phantom repros), items 2 and 3 by the predicate-only axis and the shared driver; reference this plan filename.
- [x] Create `docs/history/backlog/2026-08-31-fence-scanner-round-2.md` (Status: open, Workflow: backlog, Source: this plan's r1 review) capturing two deliberate follow-ups: (a) `security#fail-open-swallowed-metadata-bullets`: a fail-loud diagnostic (warn or hard error) when `parse_markdown_findings` sees `unclosed_opener is not None`, converting the documented silent non-recovery of post-opener bullets into a signal; (b) `architecture#duplicate-consumer-contract`: the identical `## Findings` section-extraction prelude in `split_finding_blocks` (~`:390-394`) and `parse_markdown_findings` (~`:471-475`) could share a small helper beside `classify_with_fallback`.
- [x] Commit: `docs: close fence-scanner followups backlog item, capture round-2 follow-ups`

### Task 6: Final validation

Files:
- none (verification only)

- [x] Run the full `## Validation Commands` block -> all checks green (the slug loop is valid only here: every new slug exists by this point; earlier tasks ran scoped interim checks only).
- [x] Re-verify the stale sweeps fire by construction: `grep -rn "reset_at_headin[g]" scripts/`, `grep -rn "delimiter_lengt[h]" scripts/`, and `grep -rn "classifier-guard" scripts/` each return zero lines (the negated block above already fails otherwise).
- [x] Confirm working tree clean; no uncommitted fixture or doc residue.
