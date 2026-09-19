# Plan: check-lesson-scope residual evasion classes (degenerate blocks and h3 dilution)
> DEFERRED 2026-09-18 by user direction: adds detection coverage (extra checks) without fixing a live defect; deferred under the revised selection criteria (urgency x value-per-change; check-only plans wait). Human revival only.

Backlog origin: `docs/history/backlog/2026-09-13-check-lesson-scope-residual-evasion-classes.md` (scope of record; closeout r1 findings 2 and 4)
Language guidelines: `projects/.ai-playbook/python_guidelines.md`

## Terms

- **degenerate block**: a block whose non-heading body is whitespace-only after every fence-aware heading line (of any level) is stripped; its comparable content is empty. A block with real body text under `MIN_RULE_WORDS` is a witness pointer, never degenerate.
- **h3 dilution**: an h3 subsection present in only one copy of a duplicated rule, adding enough text to that block to dilute the `SequenceMatcher` ratio below `DUPLICATE_RATIO` (for pure-append dilution the whole-block ratio equals the cheap length bound, so the pair is skipped by the cheap bounds before SequenceMatcher runs).
- **h3-segmented fallback comparison**: for a block pair that passes the whole-block word floor and produces no whole-block report (whether rejected by the cheap bounds or by the SequenceMatcher gate), segment both blocks at fence-aware h3 boundaries and compare sub-block pairs with their own word floor, length bound, and ratio gate.
- **degenerate WARNING**: the exit-0 stderr WARNING emitted when a file parses to at least one block and every block is degenerate; joins the existing zero-block/missing-file cold-start WARNING family that done-gate consumers stop on.

## Design Invariants (CR Guard)

1. The whole-block per-pair comparison is unchanged and primary; the h3-segmented fallback only adds detections for pairs with no whole-block report.
2. `MIN_RULE_WORDS` (25), `DUPLICATE_RATIO` (0.90), the fence-aware h1/h2 heading detection, and the zero-block and missing-file WARNING contracts and messages are unchanged.
3. Witness pointers (real body text under the floor) never warn; only body-whitespace degeneracy warns, and only when every block of the file is degenerate (at least one block must exist, so zero-block files keep their own message).
4. Degeneracy is computed from raw lines at parse time (every fence-aware heading line of any level stripped before the whitespace test); it is never inferred from normalized `Block` fields, whose heading attribute masquerades on headingless files.
5. The 7 real h3-free corpora produce identical results: segmentation short-circuits when neither block contains an h3 line, so the fallback adds zero SequenceMatcher cost for them.

## Assumptions

- assume Fix A warns only on body-whitespace degeneracy, not on "all blocks under MIN_RULE_WORDS"; basis: the suite's `SHORT_POINTER` fixture is a legitimate witness-pointer-only file and the origin item's own caveat blocks a plain under-floor WARNING.
- assume Fix B uses fence-aware h3 segmentation (the item's option b family) rather than whole-file merged text; basis: segmentation reuses the existing fence machinery, keeps the whole-block pass primary, and directly targets the dilution shape.
- assume the residual (a duplicator crafting sub-0.90 fragments across h3 boundaries) stays a documented accepted boundary; basis: escalating arms race beyond the item's scope.
- assume the degenerate WARNING keeps the exit-0 + stderr contract of the existing cold-start family; basis: the consumer contract note in the docstring (gate consumers stop on any WARNING line), which is the intended loud behavior for a file that silently audited as clean.

Decision points requiring a grill: F2 fix = degenerate-block WARNING via raw-lines body-whitespace degeneracy (a third option beyond the item's document/merged-text pair); F4 fix = fence-aware h3-segmented fallback comparison gated on word floor + no whole-block report (not on the cheap bounds), with per-sub-pair bounds; source: the item's candidate options, the SHORT_POINTER witness contract, and three review workers' bound-arithmetic convergence; 2026-09-16; affects Gist, Tasks, Evaluation Criteria.

## Gist & Examples

What changes: two accepted-boundary evasion classes in the lesson-scope duplicate validator become detectable. First, a headed file whose only content is a degenerate block (heading plus whitespace-only body, at any heading depth) currently exits 0 with no output, so the done gate reads that as "audited clean" when the validator effectively compared nothing; after this plan such a file warns on stderr (exit 0, same cold-start contract) while files with any real body text keep silent. Second, when a duplicated rule's block pair produces no whole-block report, the validator falls back to comparing fence-aware h3-segmented sub-blocks of both blocks, so a rule duplicated with an extra h3 subsection diluting only one copy is still flagged.

Why: both classes were probed as real misses on 2026-09-13 (the origin item records the probes) and left as accepted boundaries. The dilution shape has a structural property that makes the naive fix wrong: for pure-append dilution the whole-block `SequenceMatcher` ratio equals the cheap length bound `2*min/(a+b)`, so the existing cheap bounds skip the pair before any comparison. The fallback must therefore run for pairs the bounds rejected, not only for pairs the bounds passed, and it restores cost discipline per sub-pair instead.

Before (today): corpus `# H` + whitespace vs a normal master exits 0 with empty stderr (silent clean pass). Corpus = rule + `### Notes` subsection vs master = the same rule alone exits 0 (the pair is bounds-skipped: bound = ratio = 0.844 < 0.90 on the probed fixture) - the duplicate is missed.

After (this plan): the same degenerate corpus exits 0 but prints a `WARNING: ... degenerate blocks (heading with no body content)` line on stderr, joining the zero-block cold-start family. The same dilution corpus exits 1 with a `DUPLICATE:` report from the h3-segmented fallback (the matching rule sub-block passes its own bounds: near-equal lengths give a bound near 1.0). A witness-pointer-only file still exits 0 silently, and the h3-free corpora produce identical results.

Edge cases that shaped the design: the warning must distinguish degenerate blocks (no real body after stripping every heading line, including `###` and deeper stubs) from legitimate short witness pointers (real body text), so the test keys on raw body content at parse time. The fallback comparison must be fence-aware (an h3 inside a code fence is body text) and must not re-open the original h3-split evasion: the whole-block pass still runs first and still flags whole-block duplicates.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the two probed fixtures flip exactly as specified; witness-pointer-only files stay silent; the existing 38-test suite stays green (final count 47 with the nine new tests); h3-free inputs produce identical results at zero fallback cost.
- invariants: whole-block pass, floors, ratio, fence-aware detection unchanged (existing suite is the witness).
- documentation: the docstring and the USAGE constant both document the degenerate WARNING family, the h3-dilution coverage, and the residual accepted boundary.

**Done when:**
- every task checkbox is checked; `python3 scripts/test_check_lesson_scope.py` exits 0 with the new tests present; the Validation Commands block exits 0.

**Ship when:**
- the runtime path `~/.ai-playbook/scripts/check_lesson_scope.py` is a per-file symlink into this repo (as README.md documents), so the done gate's default `LESSON_SCOPE_SCRIPT` path runs the committed bytes automatically once Tasks 1-3 land; Task 4 verifies the symlink resolution and byte-identity, and never converts the symlink into a copy.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_lesson_scope.py`

**Tests:**
- `scripts/test_check_lesson_scope.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation extension:** `README.md` (Scripts row, Task 3). 

**Out of scope; reject unless plan-related:**
- the 7 real corpora and the company guidelines master; reason: data, not code; the plan must not touch them
- `agents/skills/learn/` and the done skill; reason: consumers of the validator's exit contract (exit codes and stop-on-any-WARNING unchanged; the done gloss for exit 1 becomes incomplete once fragment-level matches fire, accepted because the " (segmented match)" suffix distinguishes the class)
- `docs/history/backlog/2026-09-13-check-lesson-scope-residual-evasion-classes.md` body edits beyond the completion move; reason: the item is the scope of record

## Validation Commands

```bash
set -u
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

python3 scripts/test_check_lesson_scope.py || fail "suite"

python3 - <<'PYEOF' || fail "python fixtures"
import subprocess, tempfile, os, sys
T = tempfile.mkdtemp()
rule = ("When a configuration rollout expands the pull request scope beyond its original title, "
        "update the title before merging so reviewers can rely on the title as the scope of record "
        "for later audits and incident tracing plus additional context words here to make the block "
        "substantial enough for the word floor to apply in comparison and keep the rule well above "
        "the minimum word floor for the duplicate gate to even consider the pair")
def run(a, b):
    return subprocess.run([sys.executable, "scripts/check_lesson_scope.py",
                           os.path.join(T, a), os.path.join(T, b)], capture_output=True, text=True)
open(os.path.join(T, "c.md"), "w").write(f"# Rule A\n\n{rule}\n\n### Notes\n\nSome internal notes about the rollout that only exist in this copy and add enough extra words to dilute the similarity score below the gate threshold.\n")
open(os.path.join(T, "m.md"), "w").write(f"# Rule A\n\n{rule}\n")
r = run("c.md", "m.md")
if r.returncode != 1 or "DUPLICATE" not in r.stdout:
    print("dilution fixture must exit 1 with a DUPLICATE report", file=sys.stderr); sys.exit(1)
open(os.path.join(T, "w.md"), "w").write("# Witness\n\nSee the company guidelines master for the rollout title scope rule.\n")
r = run("w.md", "m.md")
if r.returncode != 0 or r.stderr:
    print("witness-pointer-only corpus must stay silent", file=sys.stderr); sys.exit(1)
open(os.path.join(T, "d.md"), "w").write("# H\n\n   \n")
r = run("d.md", "m.md")
if r.returncode != 0 or "degenerate blocks (heading with no body content)" not in r.stderr:
    print("degenerate corpus must warn on stderr with exit 0", file=sys.stderr); sys.exit(1)
open(os.path.join(T, "deep.md"), "w").write("# T\n\n## Rule\n\n### Sub\n\n   \n")
r = run("deep.md", "m.md")
if r.returncode != 0 or "degenerate blocks (heading with no body content)" not in r.stderr:
    print("deeper-heading-only stubs must count as degenerate", file=sys.stderr); sys.exit(1)
print("python fixtures OK")
PYEOF
grep -q "identical h3 subsection" README.md || fail "README row gloss missing"
grep -q "degenerate blocks (heading with no body content)" scripts/check_lesson_scope.py || fail "docstring degenerate family missing"
grep -q "segmented match" scripts/check_lesson_scope.py || fail "USAGE segmented-match note missing"
echo "VALIDATION OK"
```

### Task 1: degenerate-block WARNING (Fix A, RED then GREEN)

Files:
- `scripts/check_lesson_scope.py`
- `scripts/test_check_lesson_scope.py`

- [ ] RED: add `test_headed_degenerate_block_warns`; given a corpus of `# H` plus whitespace-only body against a normal master, expects exit 0 with a stderr WARNING containing "degenerate blocks (heading with no body content)". Run → expect RED: the probe prints nothing today (authoring-time probe recorded: exit 0, empty stderr).
- [ ] RED-guard: add `test_witness_pointer_only_corpus_no_warning` in the HEADINGLESS single-block form (corpus text is just `SHORT_POINTER` with no heading line); given a normal master, expects exit 0 with empty stderr. This stays green today and must remain green: it is the invariant witness that catches the Block-model masquerade (a Block-derivable degeneracy predicate misreads the headingless file's whole text as a heading and would warn here).
- [ ] RED-guard: add `test_deeper_heading_only_stubs_warn`; given a corpus of `# T`, `## Rule`, `### Sub` lines with only whitespace body text, expects the degenerate WARNING. Run → expect RED today.
- [ ] GREEN (commit together with the RED tests so no intermediate commit leaves a stale WARNING-family comment on `test_warning_lines_only_in_documented_conditions`): compute degeneracy from raw lines at parse time: a block is degenerate when every line of the block, after stripping all fence-aware heading lines of any level (`#{1,6} `), is whitespace-only. Extend `_load_blocks` to warn with `WARNING: existing file parses only to degenerate blocks (heading with no body content): {path}` when the file parsed at least one block and every block is degenerate (zero-block files keep their existing message). Witness pointers do not warn. Existing suite fixtures with a standalone degenerate block among real blocks stay silent (the "every block" semantics).
- [ ] Update the stale WARNING-family comment on `test_warning_lines_only_in_documented_conditions` in this commit (it names only missing-file and zero-block families).
- [ ] Run → expect GREEN: the three Task-1 tests pass and the full suite stays green.
- [ ] Commit (staging exactly this task's Files list; leave unrelated dirty paths unstaged and report them): `check-lesson-scope: warn on headed degenerate-block files`

### Task 2: h3-segmented fallback comparison (Fix B, RED then GREEN)

Files:
- `scripts/check_lesson_scope.py`
- `scripts/test_check_lesson_scope.py`

- [ ] RED: add `test_h3_dilution_duplicate_flagged`; given a corpus block (rule + `### Notes` subsection present only in the corpus) against a master block (the same rule alone), expects exit 1 with a `DUPLICATE:` report naming the corpus parent block and containing " (segmented match)". Run → expect RED: exit 0 today (authoring-time probe recorded; the pair is bounds-skipped because for pure-append dilution the cheap bound equals the ratio).
- [ ] GREEN: FIRST extend `Block` with a raw source lines field as `tuple[str, ...]` populated in `_make_block` (which already receives them); THEN compute degeneracy and segmentation from those raw lines. Add a fence-aware h3 segmentation helper (populated in `_make_block`, which already receives them; normalization discards line structure, so segmentation NEVER runs on normalized `Block.text`), add a fence-aware h3 segmentation helper operating on those raw lines (splits at `### `-prefixed lines outside code fences, reusing the fence logic shape of `parse_blocks`) and restructure `find_duplicates`: after the whole-block `MIN_RULE_WORDS` floor, a pair with no whole-block report falls back to comparing all sub-block pairs of the two segmented blocks. Each sub-block pair is gated on its own `MIN_RULE_WORDS` floor, its own length bound `2*min/(a+b)`, and `DUPLICATE_RATIO`; the first matching sub-block pair reports with the parent block's line and heading suffixed " (segmented match)" (the suffix means matched via the segmented fallback, not that the h3 subsection itself matched - in the canonical append shape the matching sub-block is the pre-h3 rule head) and exits the sub-pair loop (one report per parent pair). Segmentation short-circuits when neither block contains an h3 line (h3-free pairs are zero-cost). The whole-block pass, its cheap bounds, and its reports are unchanged and primary; the whole-block length bound is NOT reused as a fallback-eligibility filter (that is the defect this task fixes: bounds-filtered pairs are exactly the dilution class).
- [ ] RED-guard: extend the existing `test_h3_split_duplicate_evasion_closed` with one assertion that the report line carries no " (segmented match)" suffix (pinning whole-block provenance); do not add a near-duplicate test.
- [ ] Coverage tests: `test_shared_boilerplate_multiple_reports` (two parent pairs sharing an identical h3 subsection, expects one DUPLICATE line per parent pair, pinning the amplification shape); `test_unrelated_rules_shared_h3_fragment_flagged` (two unrelated rules each carrying an identical >=25-word h3 subsection, expects exit 1 with the h3-subsection report; pins the by-design fragment-level widening the docstring documents); `test_master_only_h3_dilution_flagged` (the h3 subsection only in the master block; the fallback segments both sides); `test_h3_segmentation_fence_aware` (a `### `-prefixed line inside a code fence does not split; unit-level, mirroring the parse_blocks test precedent); `test_sub_block_under_floor_skipped` (a matching h3 sub-section under `MIN_RULE_WORDS` does not report).
- [ ] Run → expect GREEN: the dilution test flips to exit 1 with the report, the coverage tests pass, and the full suite stays green.
- [ ] Commit (staging exactly this task's Files list): `check-lesson-scope: h3-segmented fallback catches dilution misses`

### Task 3: docstring, USAGE, and comment documentation

Files:
- `scripts/check_lesson_scope.py`
- `scripts/test_check_lesson_scope.py`

- [ ] Docstring: document the degenerate-block WARNING in the consumer-contract note (update the "Mechanical-only scope" opening sentence, not the "Semantic scope judgment" sentence) (alongside the zero-block parenthetical); document the h3-dilution coverage of the fallback pass next to the h3 amendment note and update the opening semantic sentence (fragment-level matches on identical h3 subsections of otherwise-unrelated rules are flagged by design); state the residual accepted boundary: dilution remains undetected by design when the diluting text is crafted below `DUPLICATE_RATIO` across h3 boundaries OR when it uses non-h3 shapes the segmenter does not split (plain appended text with no heading, `####` and deeper subsections, fenced content); a heading-plus-bare-fence-lines body (fence markers count as content) stays a silent clean pass by the same operational predicate.
- [ ] USAGE constant: extend the WARNING condition list with the degenerate family and add the segmented-match operator note (verify a shared fragment is not mandated boilerplate before deduplicating).
- [ ] Test comment: update `test_warning_lines_only_in_documented_conditions` comment to name the three WARNING families (missing file, zero blocks, degenerate blocks) and add one assertion that a mixed file (a real rule plus a degenerate trailing block) keeps stderr empty.
- [ ] README Scripts row: extend the detection gloss ("flags a full rule body, or an identical h3 subsection inside an otherwise-divergent block, near-verbatim duplicated").
- [ ] Run → expect GREEN: the full suite still passes; the Validation Commands block exits 0.
- [ ] Commit (staging exactly this task's Files list, including the README row): `check-lesson-scope: document degenerate warning and dilution coverage`

### Task 4: runtime symlink verification and final validation

Files:
- none in the repository (verification only)

- [ ] Verify the runtime path `~/.ai-playbook/scripts/check_lesson_scope.py` is a per-file symlink resolving into this repo (`test -L` and `readlink -f` resolves to the committed file) and that `cmp` through the symlink reports byte-identity with the committed validator; record both checks. NEVER convert the symlink into a real-file copy (the repo's documented deployment contract is per-file symlinks; a second copy would silently desync every future validator fix from the done gate).
- [ ] Run → expect GREEN: the full Validation Commands block exits 0 through the runtime path; record the output.
- [ ] Commit: only if repository files have residue (diff restricted to this plan's touched files); the verification itself is recorded in the execution log.
