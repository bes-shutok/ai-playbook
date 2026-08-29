# Plan: fence-scanner consolidation (F3 + F7 + tilde fixtures + F11 wording)

Source: `docs/history/backlog/2026-08-28-fence-scanner-family.md` (r6 findings F3 + F7 and the overflow row `testing#tilde-fence-arm-untested`), plus the F11 wording fix from `docs/history/backlog/2026-08-28-review-doc-wording-fixes.md` (which mandates settling together with this item).

## Terms

- **Fence state machine**: the Markdown fenced-code-block tracker: a fence opens on a line matching `` ^\s*(`{3,}|~{3,}) `` and closes only on an equal-or-longer delimiter line (r5 F5 fence-length semantics).
- **Block splitter**: `split_finding_blocks` (`scripts/validate_review_staging.py` ~line 290); splits the `## Findings` section into per-finding blocks via `scan_boundaries`.
- **Finding parser**: the current-format parser's nested `scan(headings_reset_fence)` (~line 404); classifies finding-header and metadata lines.
- **Content-preserving first pass**: a scan that treats lines inside a legitimately open fence as quoted content, so a properly fenced staging-format example never yields findings.
- **Heading-reset containment**: a scan mode where a structural heading line resets fence state, used when a fence was never closed, so an unclosed fence cannot swallow later findings (r4 F3).
- **Full-discard fallback**: today's behavior: when the first pass ends with a fence open, the entire first-pass result is thrown away and the whole section is re-scanned with heading resets. This is the F3 defect.
- **Partial fallback**: the fix: keep first-pass results for the region before the unclosed-fence opener; apply heading-reset classification only from the opener line onward.
- **Staging-format example**: a fenced code block inside a finding body that quotes staging-format syntax (contains heading-like `#### F<N>.` lines) purely as illustration.
- **Skill-gate marker**: fresh per-(project, session) marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`, written via `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker [--session-id "$SID"]` (atomic write, mode 0600, `FileExistsError` benign) before every plan-file write; FAIL-LOUD if unwritable.
- **Session key**: `$SID` from `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`; emptiness check first: empty-after-strip → literal `no-session`; otherwise `sha1(value)[:16]` hex.

## Assumptions

- assume **partial fallback**, not a whole-document unclosed-fence hard error; basis: a hard error would flip the pinned r4 F3 containment selftest expectation ("unclosed fence before a later finding still parses both findings"), which is established contract; the backlog sanctions either shape.
- assume base branch = `main` (review-artifact-contracts work merged as 593d492); basis: git state at plan time; branch `2026-08-28-fence-scanner-consolidation` created from it.
- assume the F11 doc edit (`agents/skills/review-staging/SKILL.md` snippet-format paragraph) rides as this plan's final task; basis: the wording-fixes backlog item states F11 must be settled together with the fence-scanner item so the caveat text matches the consolidated scanner.

## Design Invariants (CR Guard)

Prior-phase decisions from the review-artifact-contracts work that must not be compromised:

- **r4 F3 containment**: an unclosed fence must not swallow later findings; findings after an unclosed fence still parse and count toward blocking conservation. The r6 fallback regression (F3) is fixed by narrowing the reset region, not by weakening containment.
- **r5 F5 fence-length semantics**: a fence closes only on an equal-or-longer delimiter line; a shorter delimiter run inside a fence stays content. Pinned by the existing r5 F5 selftest (~line 3726); must stay green.
- **r5 F8 fenced-example purity**: finding-header-like (`#### F<N>.`) and metadata-bullet-like lines inside a properly CLOSED fence are quoted content, never findings or metadata. Pinned by the existing r3 F2 and r5 F8 selftests (~lines 3648, 3678); must stay green.
- **Fail-closed posture**: every malformed-input path either rejects with a targeted error or contains the damage; no path may silently pass input the producer rules forbid.
- **Conservation/readiness contracts untouched**: blocking conservation, finding budget, readiness gating, and sidecar/markdown agreement checks are consumers of parser output; this plan changes only line classification, not their semantics.
- **Reset-region state seeding**: the partial fallback seeds the reset region's scan with the first pass's state at the opener index: current severity label, metadata-region flag, and the open finding `cur`. The finding open at the opener is flushed with its PRE-opener bullets (no double-append), and same-group later findings parse with their true severity. The contract must NOT claim recovery of the straddling finding's post-opener bullets: those lines are inside the unclosed fence and, under heading-reset classification, are skipped until the next heading, which starts the NEXT finding. Losing them matches today's full-discard behavior (no regression); fixtures must place a straddling finding's load-bearing metadata BEFORE the opener (r1 F1, r2 F1, r3 F1).
- **Per-consumer reset heading sets**: the reset-policy parameter takes the consumer's own reset-heading predicate, pinning today's behavior: the block splitter resets only on finding-header lines (`#### F<N>.`); the parser resets on severity-group headings (`### <Severity>`) and finding headers, not generic `####` headings (r3 F2).

## Gist & Examples

`scripts/validate_review_staging.py` carries two near-identical copies of the fence state machine: one in `split_finding_blocks`'s nested `scan_boundaries` (~line 305) and one in the finding parser's nested `scan` (~line 404/456). Both run a content-preserving first pass and, when a fence is left open at section end, fall back to a heading-reset re-scan that **discards the entire first-pass result** (F7 duplication; F3 phantom regression).

Why that fallback is wrong: consider a Findings section that contains (a) a properly fenced staging-format example with `#### F99. fake#y` inside, and (b) later, a stray unclosed fence opener in some finding's Comment. The first pass classifies both correctly. But because the stray fence never closes, `fence_open_at_end` is true and the whole first pass is discarded. The heading-reset re-scan resets fence state at every heading-like line, so the example's `#### F99.` line becomes a real finding boundary → phantom finding F99 → hard conservation error naming a finding that does not exist. A document that follows the producer rules except for one stray fence fails with a misleading error about content it correctly ignored in the first pass.

The fix: extract ONE shared fence-aware line classifier used by both consumers, and make the fallback partial: keep first-pass results before the unclosed-fence opener, heading-reset only from the opener line onward, seeding the reset region with the first pass's state at the opener (severity label, metadata-region flag) so a later finding in the same severity group still parses with its true severity. The fenced example (before the opener) keeps its correct content classification, so F99 never surfaces; the region after the opener retains r4 F3 containment. All prior-round behaviors (r3 scoping, r4 parity/containment, r5 fence-length, r6's own scoped fixes) stay pinned: the existing selftests run GREEN before and after.

Also: tilde (`~~~`) fences are advertised by both regexes but no selftest fixture uses one (`rg -c '~~~'` is 0 today); a regression dropping tilde handling would fail no check. This plan adds tilde fixtures, including the fenced-example-plus-unclosed-fence combination that triggers the fallback.

Finally, the F11 doc fix: the snippet-format paragraph in `agents/skills/review-staging/SKILL.md` still claims "the `--hard` validator walks headings line-by-line without fence tracking", which is stale for block splitting and finding parsing. The paragraph is reworded to match the consolidated scanner; the severity-group heading scan (`content.find("### {severity}")`, ~line 1306) genuinely remains fence-blind, so that caveat stays.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the new fallback fixture (fenced staging-format example + later stray unclosed fence) produces no phantom-finding conservation error; full `--selftest` (15 families) green.
- maintainability: exactly one fence state machine and one fence-regex definition in the file (grep-countable); both consumers call the shared classifier.
- test coverage: tilde fixtures exist and pin both the closed-fence and unclosed-fence arms.
- doc-code consistency: the review-staging snippet-format paragraph names fence-aware splitting/parsing with the unclosed-fence and severity-scan caveats exactly as the code behaves.

**Done when:**
- `python3 scripts/validate_review_staging.py --selftest` exits 0 with the new fixtures registered.
- Fence-regex definition count in `scripts/validate_review_staging.py` is exactly 1 (was 2).
- The stale "without fence tracking" claim is gone from `agents/skills/review-staging/SKILL.md` and the replacement text is present.
- The fence-scanner backlog item is moved to `docs/history/backlog/completed/`; the wording-fixes item records F11 done with F6 still open.

**Ship when:**
- The branch passes its review loop with zero unresolved blocking findings and is merged to main by the user.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py` (restricted to: the shared fence classifier (new, module level), `split_finding_blocks`/`scan_boundaries` (~lines 290–350), the finding parser's `scan` (~lines 404–501), the fence-regex definitions, and the fence-related fixtures inside `_selftest_versioned_schema_and_patterns` (~lines 3620–3760). **All other methods and selftest families in this file are frozen; reject any review finding that touches them** (out-of-scope bugs there are tracked as backlog notes, not fixed in-place).

**Tests:**
- fence fixtures inside `_selftest_versioned_schema_and_patterns` in `scripts/validate_review_staging.py` (added/extended by this plan)

**Docs:**
- `agents/skills/review-staging/SKILL.md` (restricted to the "**Snippet format in finding bodies:**" paragraph. **Rest of the file frozen.**

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/summarize_review_stats.py`; reason: summarizer fixes (F4 race, TOCTOU) are separate backlog plans.
- `agents/skills/review-confluence-doc/SKILL.md` (F6 scratch-file digest scope); reason: separate backlog item, not coupled to scanner behavior.
- Source-digest CLI flag wiring and its selftest families (~line 4045); reason: F12 refactor is a separate backlog plan.

## Validation Commands

```bash
# Full selftest suite (all 15 families, includes every fence fixture)
python3 scripts/validate_review_staging.py --selftest

# Exactly ONE fence-regex definition remains (was 2: lines ~305 and ~456).
# Fixed-string count of the full regex literal (grep -cF does NOT anchor; r2 F2:
# the gate is count-based and fails loud). Docstring mentions with different
# phrasing cannot inflate the count; the reviewer re-checks placement inside the
# shared classifier during review.
n=$(grep -cF '^\s*(`{3,}|~{3,})' scripts/validate_review_staging.py) || { echo "grep failed"; exit 1; }
[ "$n" -eq 1 ] || { echo "expected 1 fence regex definition, found $n"; exit 1; }

# Tilde fixtures exist, anchored to comment-form fixture labels (r3 F3 + r4 F1:
# a bare `~~`-char grep can be satisfied by a docstring, and a bare label by a
# check() description string; the `# `-prefixed comment form only exists if the
# fixture comments were added)
grep -qF '# tilde-closed-example' scripts/validate_review_staging.py || { echo "tilde closed-fence fixture missing"; exit 1; }
grep -qF '# tilde-unclosed-containment' scripts/validate_review_staging.py || { echo "tilde unclosed-fence fixture missing"; exit 1; }

# F11: stale claim removed. The [-] escape is intentional (self-match immunity:
# the plan file embeds this pattern, its own escaped text must not match).
if tr '\n' ' ' < agents/skills/review-staging/SKILL.md | grep -q "line-by[-]line without fence tracking"; then
  echo "stale fence claim still present"; exit 1
fi

# F11: replacement wording present (fence-aware claim + severity caveat)
grep -q "fence-aware" agents/skills/review-staging/SKILL.md \
  || { echo "fence-aware wording missing"; exit 1; }
grep -q "severity-group heading scan" agents/skills/review-staging/SKILL.md \
  || { echo "severity-group caveat missing"; exit 1; }
```

### Task 1: Tilde-fence characterization fixtures (GREEN today)

Files:
- `scripts/validate_review_staging.py` (fixtures inside `_selftest_versioned_schema_and_patterns`)

- [x] `_selftest_versioned_schema_and_patterns#tilde-closed-example`; given a current-format Findings section containing a properly CLOSED tilde fence (`~~~`) around a staging-format example with `#### F99. fake#y` inside plus one real finding, expects validation passes with only the real finding counted (example headers are content)
- [x] `_selftest_versioned_schema_and_patterns#tilde-unclosed-containment`; given a section with an unclosed tilde fence in one finding's Comment followed by a later real finding, expects the later finding still parses and counts (tilde analog of the r4 F3 containment arm)
- [x] Run → expect GREEN (characterization: tilde support exists today but is pinned by no fixture (`rg -c '~~~'` is 0 before this task))
- [x] Each fixture carries its label (`# tilde-closed-example`, `# tilde-unclosed-containment`) as an inline comment in the script; the Validation Commands gate greps the `# `-prefixed labels (r3 F3 + r4 F1)
- [x] Run full `--selftest` → GREEN
- [x] Commit: `test: tilde-fence characterization fixtures for staging validator`

### Task 2: RED (partial-fallback regression fixture, r6 F3)

Files:
- `scripts/validate_review_staging.py` (fixtures inside `_selftest_versioned_schema_and_patterns`)

- [x] `_selftest_versioned_schema_and_patterns#fallback-preserves-fenced-example`; given a section with a properly fenced staging-format example (`#### F99.` inside the fence) FOLLOWED by a stray unclosed fence opener inside a later real finding's Comment body (opener placement pinned: in-Comment, not top level, r4 F3) and a subsequent real finding, expects no phantom-finding conservation error naming F99 and exactly the real findings parsed
- [x] `_selftest_versioned_schema_and_patterns#fallback-same-severity-group`; given a section with a properly fenced staging-format example (`#### F99.` inside the fence), a stray unclosed fence opener in a real finding's Comment AFTER that finding's Blocking bullet, and a later real finding, all inside the SAME severity group (e.g. all under `### Medium`), expects the straddling finding keeps its pre-opener metadata (Blocking preserved via the flush, not lost, not double-appended) and the later finding parses with its true severity label (not `severity: None`), with no conservation error (r1 F1 + r2 F1 + r3 F1: the reset region inherits the first pass's severity and open-finding state at the opener; the fenced example is part of the given because a stray-fence-only same-group layout is GREEN today and would not pin the fix; load-bearing metadata sits BEFORE the opener because post-opener bullets are unrecoverable)
- [x] Both Task 2 fixtures assert the block splitter's output directly (like the r5 F8 precedent at ~3681 asserts parser output): `split_finding_blocks` on the fixture section returns exactly the real finding blocks and no block whose text contains the F99 example header (r4 F2: indirect end-to-end validation alone does not pin block splitting)
- [x] Run → expect RED (today the full-discard fallback re-scans with heading resets, the example's `#### F99.` becomes a phantom finding, and validation fails with a conservation error naming a nonexistent finding)
- [x] Commit: `test: r6 F3 fallback phantom-finding regression fixture (RED)`

### Task 3: GREEN (extract shared scanner + implement partial fallback)

Files:
- `scripts/validate_review_staging.py`

- [x] Add ONE module-level fence-aware line classifier with a SPECIFIED line-event vocabulary (r1 F3): for each line it yields one of `fence_opener(delimiter_length)` / `fence_close` / `in_fence_content` / `heading(raw_text)` / `ordinary`, under an explicit reset-policy parameter (content-preserving vs heading-reset), and it reports the unclosed-fence opener line index when a fence never closes. The classifier emits `heading(raw_text)`; it does NOT classify heading sub-kinds, and each consumer maps raw heading text to its own semantics (severity-group `### <Severity>` vs finding header `#### F<N>.` vs other `####`) (r2 F4). The classifier owns the single fence regex and the r5 F5 equal-or-longer close rule; the two consumers keep only their own interpretation of the events (boundary indices vs finding/metadata assembly); no consumer re-implements fence tracking
- [x] Rewire `split_finding_blocks`'s `scan_boundaries` and the finding parser's `scan` to call the shared classifier; delete both duplicated in-line state machines and the duplicate fence regex
- [x] Implement partial fallback in BOTH consumers: on fence-open-at-end, keep first-pass results for lines before the opener index; for the region from the opener onward, run the heading-reset classification seeded with the first pass's state at the opener index: for the parser that means the current severity label, the metadata-region flag, and the open finding `cur` carry over, with the finding open at the opener flushed with its pre-opener bullets (no double-append) so same-group later findings parse with their true severity; bullets after the opener are inside the unclosed fence and are not recovered (same as today's full-discard behavior; see the Reset-region state seeding invariant); replaces both full-discard fallbacks at ~339–340 and ~496–501; each consumer passes its own reset-heading predicate, pinning today's heading sets (splitter: finding headers only; parser: severity groups + finding headers)
- [x] Run Task 1 + Task 2 fixtures → GREEN
- [x] Characterization check: the existing r3 F2 (~3648), r4 F3 (~3698), and r5 F5 (~3726) fence fixtures run GREEN before and after the extraction (they pin scoping, containment, and fence-length semantics across the refactor)
- [x] Run full `--selftest` → GREEN
- [x] Commit: `refactor: consolidate fence scanners with partial unclosed-fence fallback`

### Task 4: F11 wording update (review-staging snippet-format paragraph)

Files:
- `agents/skills/review-staging/SKILL.md`

- [x] Reword the second sentence of the "**Snippet format in finding bodies:**" paragraph: replace "The `--hard` validator walks headings line-by-line without fence tracking, so a fenced block whose content contains a severity-heading-like (`### Medium`) or finding-heading-like (`#### F9.`) line corrupts block splitting and fails the gate." with text stating that finding-block splitting and metadata parsing are fence-aware (a properly fenced snippet is safe even if its content contains heading-like lines), that an UNCLOSED fence triggers a partial re-parse from the fence opener (content before it is preserved), and that the severity-group heading scan remains fence-blind, so keep fenced snippets free of heading-like lines as the simple producer rule
- [x] Verify the reworded paragraph against the actual post-consolidation code behavior (read `split_finding_blocks` and the parser fallback once more before finalizing the wording)
- [x] Run the F11 greps from `## Validation Commands` → GREEN
- [x] Commit: `docs: align review-staging snippet-format wording with consolidated fence scanner`

### Task 5: Final validation + backlog bookkeeping

Files:
- `docs/history/backlog/2026-08-28-fence-scanner-family.md`
- `docs/history/backlog/2026-08-28-review-doc-wording-fixes.md`

- [x] Run the full `## Validation Commands` block → all checks green
- [x] Move `docs/history/backlog/2026-08-28-fence-scanner-family.md` to `docs/history/backlog/completed/` (all three defects closed by this plan)
- [x] Edit `docs/history/backlog/2026-08-28-review-doc-wording-fixes.md` to record F11 fixed by this plan (with the plan filename) and that F6 remains open
- [x] Commit: `docs: close fence-scanner backlog item, record F11 fix`
