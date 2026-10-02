# Plan: Selection helper docstring precision: the full refusal taxonomy and the scoped alias quantifier

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-20-pair-grammar-alias-paragraph-scope.md`
- `docs/history/backlog/2026-09-20-selection-refused-docstring-enumeration-gap.md`

## Gist & Examples

TLDR: two docstring paragraphs in scripts/review_record_selection.py are corrected to say exactly what the pinned behavior is - the stated-once exit taxonomy enumerates the mark-superseded-side refusal families it currently omits, and the alias sentence scopes its begins-with quantifier to the four literal review-kind infixes while naming the guarded bare review- carve-out; documentation-precision driving force, because the taxonomy paragraph exists so a reader can predict every refusal's exit code from one place and currently trains selective mistrust, and the alias paragraph is the documented slug-spelling contract a future refactor could fix in the wrong direction.

Authoring re-derivation (recorded per the entry): the helper carries nine `SelectionRefused` raise sites on the current bytes; six sit in the families the taxonomy paragraph names (an unreadable sidecar, a sidecar with no source_digest, an orphaned half, a differing digest without a decision, and the two backup-target shapes), and exactly three sit in the mark-superseded-side shapes the paragraph omits - the duplicate-marker refusal (a prior record carrying multiple supersession labels), the different-successor re-mark refusal (a prior record already marked with a different recorded successor), and the missing-Metadata refusal (no Metadata section to host the marker line). The alias sentence's quantifier ("a slug that itself begins with an offered infix string") over-generates: the module's offered infixes are the four literal review-kind infixes plus the guarded bare `review-` kind, and only the four literal ones take the alias enumeration - the bare `review-` is the carve-out pinned by `test_pair_pattern_review_shape_stays_bare_owned` (a `review-`-prefixed full slug's inner spelling never enumerates its bare-shaped records).

## Terms

- **The exit taxonomy paragraph:** the class docstring passage stating, once, that usage errors exit 2 and environmental refusals (`SelectionRefused`) exit 1, with its enumeration of the refusal families.
- **The mark-superseded-side refusals:** the three `SelectionRefused` families on the supersession marking path: a prior record already marked with a different recorded successor, a prior record carrying duplicate supersession markers, and a prior record with no Metadata section to host the marker line.
- **The four literal review-kind infixes:** `plan-review-`, `branch-review-`, `code-review-`, `exec-review-` (the module's `REVIEW_KIND_INFIXES` tuple, the kinds the live corpus uses between the date stamp and the slug).
- **The guarded bare review- carve-out:** the bare `review-` kind is offered only to slugs that already begin with it (the module's `REVIEW_KIND_BARE_INFIX`), so a `review-`-prefixed full slug's inner spelling never enumerates its bare-shaped records; the carve-out is pinned by `test_pair_pattern_review_shape_stays_bare_owned`.
- **The committed-baseline em-dash gate:** the no-em-dash scan in its `added-lines --base main` form, which scans exactly this plan's inserted lines against main (the rule 29 committed-baseline form); the `--base HEAD` default is vacuous after the edited lines are committed, because re-scanning committed insertions is out of the default mode's scope by design.
- **The comment-only AST check:** the stdlib-only mechanical gate proving the zero-behavior claim: parse the module from `git show main:...` and from the working file, strip each parse tree's module/class/function docstring Expr statements, and assert the `ast.dump` forms are equal (comments never enter the AST, so equal dumps mean no executable line changed).

## Coordination (binding, not re-litigating)

- The scanner-validator-single-sourcing sibling plan (docs/history/plans/completed/2026-10-03-scanner-validator-single-sourcing.md, landed d3cba8a5) already touched scripts/review_record_selection.py; this plan authors against those post-landing bytes and sequences after it, so no fold of the docstring edits into that plan's seam work is needed.
- The pinned test `test_pair_pattern_review_shape_stays_bare_owned` (scripts/test_review_record_selection.py) is the contract the alias sentence must match; the docstring is the wrong side per the origin row, and the test is never edited.
- Comment-only, zero behavior change: no executable line moves, and the helper's own selftest suite plus the comment-only AST check are the no-regression net.
- The operator execution-lane closure (operator directive, 2026-10-02) means authoring only.

## Review Scope

Every task's Files path, inventoried:

- scripts/review_record_selection.py
- docs/history/plans/2026-10-03-selection-docstring-precision.md

Gates re-checked but not edited: scripts/test_review_record_selection.py (the no-regression net, never edited), scripts/validate_review_staging.py, scripts/check_maintenance_pins.sh (no pins over the two paragraphs). Harness touched: none (the existing suite and the AST check are the net; the edits are comment-only). Reviewers verify the re-derived nine-raise-site census against the current bytes, the three added families match the three uncovered sites exactly, the alias sentence's quantifier names the four literal infixes and the guarded carve-out with the pinned-test anchor in the docstring's backtick style, the em-dash gate runs in its committed-baseline form, and the comment-only AST check proves the zero-behavior claim.

## Tasks

### Task 1: the exit-taxonomy paragraph enumerates the mark-superseded-side refusals

Files:
- `scripts/review_record_selection.py`

Evidence:
- `$PY scripts/test_review_record_selection.py` GREEN after the edit (comment-only); the authoring nine-raise-site census recorded in this plan's Gist; `bash scripts/check-no-em-dash.sh touched` before the commit

- [x] RED: `grep -c "mark-superseded-side" scripts/review_record_selection.py` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Extend the taxonomy paragraph's `SelectionRefused` enumeration with the three mark-superseded-side families, keeping the stated-once shape: "covering a missing or damaged record target, an orphaned half, a differing digest without a decision, and the mark-superseded-side refusals on the supersession marking path (a prior record already marked with a different recorded successor, a prior record carrying duplicate supersession markers, or a prior record with no Metadata section to host the marker line)"; the three families correspond one-to-one to the three uncovered raise sites (the duplicate-marker check, the different-successor re-mark check, and the Metadata-host check on the marking path), re-derived at authoring against the current bytes [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: "mark-superseded-side" appears exactly once in the file [class: REPOSITORY_TEST]
- [x] Run `$PY scripts/test_review_record_selection.py` GREEN, then `bash scripts/check-no-em-dash.sh touched`, then commit [class: REPOSITORY_TEST]
- [x] Commit: `docs: selection taxonomy enumerates the mark-superseded-side refusals` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the alias sentence scopes its quantifier and names the carve-out

Files:
- `scripts/review_record_selection.py`

Evidence:
- `$PY scripts/test_review_record_selection.py` GREEN after the edit; `bash scripts/check-no-em-dash.sh touched` before the commit

- [x] RED: `grep -c "four literal review-kind infixes" scripts/review_record_selection.py` (expect 0 today) [class: REPOSITORY_TEST]
- [x] Reword the alias sentence's quantifier and name the carve-out in the same sentence, preserving the sentence's existing concrete detail in the docstring's backtick style: "Accepted residual alias, documented and tested but not guarded: a slug that itself begins with one of the four literal review-kind infixes (form ``<infix>Y``, e.g. ``plan-review-Y`` or ``branch-review-Y``) enumerates the same legacy-shaped ``<date>-<infix>Y-r<N>`` records as the bare ``Y`` slug, because the infix alternative and the slug spelling reach the same names; the guarded bare ``review-`` kind is the carve-out: it is offered only to slugs that already begin with it, and a ``review-``-prefixed full slug's inner spelling never enumerates its bare-shaped records (pinned by ``test_pair_pattern_review_shape_stays_bare_owned``); bare ``Y`` additionally owns the bare-shaped ``<date>-Y-r<N>`` records the infixed spelling never matches." The pinned test's decision (new-record, no prior, no supersedes for the inner spelling of a review--prefixed full slug) is the behavior the sentence must predict [class: IMPLEMENTATION_REQUIRED]
- [x] Count gate: "four literal review-kind infixes" appears exactly once in the file [class: REPOSITORY_TEST]
- [x] Run `$PY scripts/test_review_record_selection.py` GREEN, then `bash scripts/check-no-em-dash.sh touched`, then commit [class: REPOSITORY_TEST]
- [x] Commit: `docs: alias sentence scoped to the literal review-kind infixes with the carve-out named` [class: IMPLEMENTATION_REQUIRED]

### Task 3: whole-plan gates

Files:
- `docs/history/plans/2026-10-03-selection-docstring-precision.md`

Evidence:
- the full Validation Commands block

- [x] Run the full Validation Commands block GREEN (the suite, the grep count gates, the comment-only AST check in its committed-baseline em-dash form, the hygiene scan) [class: REPOSITORY_TEST]
- [x] Verify the comment-only record: the AST check's equal-dumps assertion passed, which is the plan's zero-behavior claim proven mechanically (docstrings and comments are invisible to the AST; any executable line change fails the equality) [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: selection docstring precision record` [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

```
PY=$HOME/.agents/venvs/ai-playbook-test/bin/python3
$PY scripts/test_review_record_selection.py
grep -c "mark-superseded-side" scripts/review_record_selection.py            # exactly 1
grep -c "four literal review-kind infixes" scripts/review_record_selection.py # exactly 1
$PY - <<'EOF'
import ast, subprocess
def without_docstrings(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                node.body = body[1:]
    return ast.dump(tree)
old = subprocess.run(["git", "show", "main:scripts/review_record_selection.py"], capture_output=True, text=True, check=True).stdout
new = open("scripts/review_record_selection.py").read()
assert without_docstrings(old) == without_docstrings(new), "executable tree changed: the edit is not comment-only"
print("comment-only OK")
EOF
bash scripts/check-no-em-dash.sh added-lines --base main -- scripts/review_record_selection.py
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

## Evaluation Criteria

1. The taxonomy paragraph's enumeration covers all nine raise sites' families: the six previously named plus the three mark-superseded-side shapes, one-to-one with the uncovered sites (count gate, Task 1).
2. The alias sentence scopes its quantifier to the four literal review-kind infixes and names the guarded bare review- carve-out with the pinned-test anchor, in the same sentence, preserving the composition form and examples, the legacy-shape template, the mechanism clause, and the docstring's backtick style (count gate, Task 2).
3. The edit is comment-only proven by the AST check's equal dumps, the em-dash gate runs in its committed-baseline form over exactly this plan's inserted lines, and the suite never went red except at the declared RED steps.

## Done When

- Every checkbox is `[x]`, the Validation Commands are GREEN, and the review rounds returned ready with zero blocking findings.
- The plan is landed; per the execution lane closure (operator directive, 2026-10-02) this plan is authored and landed, never executed.

## Assumptions

- The nine-raise-site census reflects the current post-d3cba8a5 bytes; a peer landing that adds a raise site before execution extends the taxonomy's enumeration in the same comment-only spirit without re-grilling.
- The suite is the complete no-regression net for a comment-only change; the AST check adds no new machinery (stdlib only) and no additional gate is priced.
- The usage-error side of the taxonomy keeps its existing membership enumeration; the review-kind grammar raise is CLI-unreachable (argparse choices reject first) and its omission is recorded as an advisory follow-up, not this plan's change.

Decision points requiring a grill: none remain.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-20-pair-grammar-alias-paragraph-scope.md`: the accepted-residual-alias sentence in the `_pair_pattern` docstring (scripts/review_record_selection.py) now scopes the alias to the four literal review-kind infixes and names the guarded bare `review-` carve-out in the same sentence, the shape the pinned test test_pair_pattern_review_shape_stays_bare_owned asserts; verified live 2026-10-04 during the backlog-root fold pass.
- `docs/history/backlog/2026-09-20-selection-refused-docstring-enumeration-gap.md`: the refused-record docstring enumeration gap closed by this plan's docstring pass; execution evidence docs/reviews/2026-10-03-exec-review-selection-docstring-precision-r1.md; both origins fold-deleted 2026-10-04 in the backlog-root fold pass.
