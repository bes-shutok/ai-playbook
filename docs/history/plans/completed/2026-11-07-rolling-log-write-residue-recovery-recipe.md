# Plan: rolling-log write residue recovery recipe

Backlog origin: docs/history/backlog/2026-11-07-rolling-log-freeze-foreign-bytes-setaside-recipe.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-rolling-log-write-residue-recovery-recipe-p29d8406e-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 0.5h
Authoring claim: 2026-11-07-rolling-log-freeze-foreign-bytes-setaside-recipe.md (session sess_dd27a4f2-4e4e-414e-96d7-66bc6f0e731f)
Executed: yes (2c4d8d7b6e514924c92cd2fbf3038cff95cca5ad)

Design input (prose only, never a Backlog origin): the PLAN-PROMPTS entry `rolling-log-write-residue-recovery-recipe` in docs/history/backlog/PLAN-PROMPTS.md, which routes this item; its admission fields, scope arms, and rejected alternatives are adopted here.

## Terms

| Term | Definition | First use outside Terms |
|---|---|---|
| Acknowledgment-arm admission | A pre-registered proposal for a runner acknowledgment path that would let a rolling-log write proceed with a foreign staged path; it ships no code. It records one witnessed incident, unknown catch frequency, and the false-positive cost that the foreign path's worktree bytes could drift during the write window, bounded by the ride-along SHA check stopping the write before peer bytes are committed. Review date: 2026-12-02; reconsider implementation only after a second true catch. | Gate delta |
| Write boundary rule | The `Standing rules` bullet in `docs/history/backlog/PLAN-PROMPTS.md` that owns primary rolling-log writes and carries the operator-gated, blob-preserving remedy for foreign staged paths (steps (a) through (e), the pre-write snapshot, three-way re-apply, recovery journal, and acknowledgment-arm admission text). | Gist & Examples, TLDR |
| Two-path staged-delta check | `scripts/done_run.sh` `cmd_commit` refuses before staging when either rolling-log path already carries a staged delta; its trigger and behavior stay unchanged, and Task 4 changes only its refusal text. | Standing constraints |
| Staged-set enumeration | The second `cmd_commit` pre-stage refusal for a staged path outside the writer's declared owned-log set; guard ordering means it names only non-rolling-log paths, and Task 4 changes only its refusal text. | Validation Commands, Command 3 |
| Foreign staged path | Any shared-index path refused by either pre-stage guard, regardless of which session staged it or whether the writer declared it; the two-path check names rolling logs and staged-set enumeration names paths outside the declared set. | Gist & Examples, Example |
| Pre-CAS recovery clause | Validation Command 8 checks Task 2's early and post-stage refusal clauses; Command 9 compares the complete arm with its canonical text. | Outcome, third bullet |
| `run_base` | The Phase 0 commit OID recorded in the execution manifest; Task 5 uses it as the stable base for an added-lines scan limited to the plan-declared touched files. | Evaluation Criteria, Done when |
| Unstaged live delta | Worktree-only bytes on a rolling-log path that the index does not stage; this includes a peer's live emission whether or not the path also carries a foreign staged blob and whether or not the writer declared the path. Because the runner commits a declared log path's worktree bytes (project lesson 290), unstaged peer bytes on a declared path ride the writer's commit unless dispositioned first. | Gist & Examples, TLDR |
| Unstaged-live-delta set-aside arm | The Write boundary rule clause that automatically isolates worktree-only bytes on a declared path and uses the existing operator-gated recovery for staged foreign bytes, with one operation-scoped journal and post-commit peer re-application. | Gist & Examples, TLDR |
| Operation ID | A fresh UUID allocated for each recovery transaction and never reused, distinguishing repeated set-asides by the same session. | Task 2, Context surface |
| Operator direction witness | A journaled current-session operator direction bound to one operation, affected path, and allowed disposition; another session must obtain fresh direction before mutating that path. | Task 2, Context surface |
| Operation journal | One ref at refs/ai-playbook/recovery/<session-id>/<operation-id> points to a Git tree containing record.json and saved blobs; it holds the expected primary ref, starting HEAD, and ordered per-path transition rows with exact before/after HEAD/index/worktree IDs and modes and path-bound operator direction witnesses when required. Under the existing done lock, capture before the final log read or writer edit; create with a zero old OID before path mutation and compare-and-swap verified updates. The ref plus current HEAD/index/worktree are the sole recovery state before a run manifest exists. | Gist & Examples, TLDR |

Edge cases: symlinks and gitlinks remain untouched and use existing operator-gated parking; missing direction, mode drift, conflicts, journal failures, ID mismatch, ambiguous refs, or unverified output retain saved blobs and use existing parking; unattended writers stand down.

## Why

A blocked primary rolling-log write can stall maintenance even when a recovery procedure already exists: refusal messages do not direct the writer to it, and unstaged peer bytes on a declared log path can ride the writer's commit. This plan closes both gaps while keeping the existing operator gate for staged foreign bytes.

## Gist & Examples

**TLDR:** Direct refusals to the canonical Write boundary rule and preserve same-path peer bytes during declared-path writes.

**Before:** A writer encountering either pre-stage refusal lacks a direct recovery pointer; a live unstaged delta on the declared log path can be committed with the writer's change.

**After:** The canonical rule handles declared-path deltas automatically and retains operator direction for staged foreign bytes. Recovery records the operation, reapplies peer work after the appropriate write boundary, and verifies the resulting IDs.

**Examples:** For a staged foreign path, follow the existing operator-gated remedy. For worktree-only bytes on a declared path, set them aside before the writer edit and reapply after the compare-and-swap.

## Outcome

A blocked primary rolling-log write resolves through one named, operator-gated remedy instead of archaeology or improvisation.

- Both pre-stage refusal messages and pre-work procedures identify the consuming repository's canonical write-boundary rule and its operator gate.
- Each recovery transaction uses one operation ref to hold the expected primary ref, starting HEAD, captured IDs and modes, saved blobs, inputs/candidates, and per-path transition rows. Worktree-only deltas on declared paths are isolated automatically; staged foreign bytes retain the operator gate. The writer candidate stays worktree-only for runner staging, and re-apply outputs preserve peer work and are checked against their own IDs.
- Task 2 makes journal recovery resumable after pre- or post-CAS failure and before later primary log reads or edits. It adds no runner behavior, separate validator, lock, refusal gate, or operator prompt for worktree-only deltas.

Gate delta: the prose adds automatic isolation of worktree-only bytes on a declared path within the already-authorized write, plus resumable, mode-aware recovery for existing staged-path refusals. Capture occurs under the existing done lock before the final log read or writer edit. One journal ref replaces per-path refs and manifest reports. Journal mismatch or incomplete post-CAS work uses the existing recovery parking outcome; no runner guard, refusal gate, operator prompt for the unstaged-only case, lock, or validator is added. The separate acknowledgment arm remains pre-registered only, with its incident, unknown catch frequency, bounded false-positive cost, and review date recorded in PLAN-PROMPTS.md; no runner behavior is promoted.

## Assumptions

- The origin's declared Class line matches its body: the plan removes a discoverability gap and a remedy-text gap while extending the existing operator-gated recovery path without adding an independent refusal path.
- The Write boundary rule's Standing rules bullet remains the single home; Task 1 specifies pre-read/pre-edit capture and automatic worktree-only declared-path isolation, and Task 2 adds one resumable Git-ref journal for both that path and existing operator-directed staged-path recovery.
- Task 4 extends both existing guard tests to compare exact before-and-after HEAD, staged entries including modes, and affected worktree bytes while preserving the full leading and trailing refusal text.

- User scope receipt (2026-11-09): after the recommendation to keep exactly two served-entry prunes, the user replied ok to that choice. This accepts only backlog-completed-dir-regrowth and test-suite-runtime-residual-optimization-path in Task 5. Lesson 318 and the served-origin audit explain their need for Command 7's maintenance-pin gate; this receipt also scopes Validation Command 7 and Evaluation Criteria. No other prompt entry or the active test-suite claim, worktree, or branch is included.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep the operator gate for existing staged-path refusals and the unattended stand-down-or-park default; automatically isolate worktree-only declared-path deltas without a new refusal or operator prompt.
- Use one operation ref as the sole durable recovery source for saved blobs, IDs, modes, and verified phases. Do not create a manifest report or per-path refs, and do not compare a merge output to a source blob ID.
- Capture declared-path state under the existing done lock before the final log read or writer edit. Create the journal and save blobs before path mutation; for a declared path, restore only a foreign staged index entry to captured HEAD and leave the writer candidate worktree-only. A mode mismatch, conflict, failed comparison, or journal error uses existing recovery parking and retains the ref.
- Re-apply peer work only to the worktree, after step (e) on an undeclared foreign path or after compare-and-swap on a declared path; retain the single ref until disposition is verified, including recovery from a post-CAS runner failure.
- Task 1's launch scope remains unchanged. Task 2 carries the hardening and same-file byte payment: Task 2 leaves PLAN-PROMPTS.md at or below its Task 1 boundary size.
- A gate-driven correction rides the owning task's next commit, never a separate silent edit.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the refusal and pre-work pointers name the same remedy; capture precedes final log reads and writer edits, worktree-only declared-path deltas are isolated without an added refusal, staged-path recovery preserves the existing operator gate, and peer work is re-applied and verified as a new merge output.
- Completeness: the operation ref captures the expected primary ref, starting HEAD, per-path IDs/modes, saved blobs, inputs/candidates, disposition classes, and ordered phases; automatic paths have a terminal witness, while operator-gated paths require a current-session path-bound direction and verified disposition; later sessions need fresh direction before mutation, and ambiguity or mismatch parks with the ref retained.
- Minimalism: the operative rule uses one Git-ref journal and the existing done lock and parking outcome, with no separate report, per-path refs, runner check, new lock, validator, refusal gate, or unstaged-only operator prompt; Task 2 pays for its text in the same file.

**Done when:**
- Both pre-stage refusal messages name the Write boundary rule's operator-gated remedy and its Standing rules home, with guard behavior unchanged; the wrapper suite proves byte-identical HEAD, full staged entries, and affected worktree bytes after each refusal.
- The Write boundary rule captures declared-path state before final log read/edit, automatically isolates worktree-only deltas without a new refusal/prompt, and covers both guards, one operation-ref journal, staged-path operator direction, candidate installation, declared and undeclared re-apply order, output verification, disposition, and pre/post-CAS resume or parking.
- Both pre-work procedures carry the repository-neutral pointer sentence verbatim.
- Task 5 prunes only the two user-approved served entries with exact receipts, leaves the active test-suite resources untouched, and clears the pins failure; Commands 1 through 10 and public hygiene pass, including the same-file byte budget against the Task 1 boundary commit and the run_base added-lines scan over only plan-touched paths.

**Ship when:**
- Not applicable (repository-internal prose and message text; no deployment step).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_maintenance_pins.sh` (Task 5): recalibrates the existing aggregate prefix count after Task 3's duplicate removal; all other predicates remain unchanged
- `scripts/done_run.sh` (Task 4)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 1)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 2)
- `agents/skills/maintenance/template-authoring.md` (Task 3)
- `agents/skills/execute-plan/worktree-first.md` (Task 3)

**Tests:**
- scripts/test_done_run_wrapper.py (Task 4): existing class-style wrapper suite; Task 4 extends `test_foreign_staged_path_refuses_before_git_add` and `_unverifiable_cleanup_case` to compare complete before-and-after snapshots; Command 2 pins the capture/equality calls and runs the suite.
- Read-only run input: docs/tmp/execute-plan/rolling-log-write-residue-recovery-recipe/manifest.md (Task 5 reads run_base and the Task 1 boundary commit for Validation Commands 7 and 10).

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates.sh` and `scripts/done_sweep_gates_lib.py`; reason: the sweep gates are not the refusing surface this plan points at
- `docs/history/backlog/EXEC-PROMPTS.md`; reason: the execution log's write discipline is unaffected by this plan
- `agents/skills/plans/SKILL.md` Entry freeze paragraph; reason: it already routes recovery to the Write boundary rule, and its span is pin-guarded (`prune_range_pin` in `scripts/check_maintenance_pins.sh`), so re-keying the pin for a redundant pointer is not warranted
- the two-path staged-delta check's trigger logic beyond the message string in `scripts/done_run.sh`; reason: the guard's behavior is unchanged by design

## Validation Commands

Preamble (authoring-time records, rule 29):
- R19 fold checkpoint: commit `89a4f2c8c4fdfbd4ca6034d90d30c5a144569b4a`, plan digest `e9f89a35c3ac428ee1ef384a0c17e866cf7ed35f7bb21e66eeb5e30d2dfe56f8`. The accepted Task 1 section digest, re-derived with `task_scope_digest`, is `4dde12d932f64943e2cd05de814693a465001ca554ce136f6c1568f5520496c8`, matching the recorded launch digest; reconcile the done-pending handoff only after a fresh ready review and full/pre-implementation readiness.
- The complete Validation Commands block exited 1 at Command 1 because its refusal messages are not yet changed; Commands 2–10 were not reached. Rule 19 RED evidence: Command 3 and Command 4's first pin each exited 1 on current `PLAN-PROMPTS.md` bytes.
- Rule 22 mechanical audit after the R19 fold corrections: 31 positive exact-text pins from Commands 4, 5, 8, and 9 passed 40 occurrence checks across their prescribed Task 1 or Task 2 text snippets; the Command 9 negative regression pin `every peer owner is paused` has zero occurrences in current `PLAN-PROMPTS.md`. The Task 2 text fences now label their text content correctly.
- Command 7 pre-Task 5 outcome: `check_maintenance_pins.sh` exited 1 on its all-served-stale prompt-log pin; the current origin checker identifies exactly the two approved Task 5 entries as stale, while `--prune-audit --base main@81f732f6bbbef41818efb87d831e147d428fa303` passes with zero removals. Command 10's lowercase selector fixture passed; the manifest has no Task 1 boundary row yet, so its live boundary leg remains pending Task 1.
- After rebase onto `main@81f732f6bbbef41818efb87d831e147d428fa303`, the Validation Commands `bash -n`, plan-touched added-lines em-dash scan, public hygiene scan, and `plan_readiness.py --pre-round` passed. Pre-round reported only the advisory five-task-over-four cap.
- Latest rebase: `main@37fdc520102796e8c1e15072addd6204feab0735`; HEAD and merge-base are verified at this tip, plan SHA-256 remains `3a2150e3c75d47c9e2e17a58acc1aff6555beddc714890f4574519bbc4722a4e`, and the accepted Task 1 scope digest is `4dde12d932f64943e2cd05de814693a465001ca554ce136f6c1568f5520496c8`.
- R19's historical pair passed hard validation and canonical review-name validation against its recorded source digest; R19 triage has zero pending findings. R20 passed hard source-digest validation at `3a2150e3c75d47c9e2e17a58acc1aff6555beddc714890f4574519bbc4722a4e`, but retains four blocking and three nonblocking findings; fold accepted changes and obtain a fresh R21 review before readiness or handoff reconciliation.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

# 1. Task 4: both refusal messages carry every required clause.
message_clause="resolve it through the Write boundary rule's operator-gated remedy (docs/history/backlog/PLAN-PROMPTS.md Standing rules; the remedy covers every staged path refused by either guard, regardless of who staged it or whether the writer declared it, with or without an unstaged live delta; an unattended writer stands down or parks without operator direction)"
test "$(grep -Fc "$message_clause" scripts/done_run.sh)" -eq 2 || fail "both refusal messages must carry the full remedy and stand-down clause"
# 2. Pin complete refusal tails and run the wrapper behavior witnesses.
python3 - <<'PY' || fail "complete refusal tails changed"
from pathlib import Path
source=Path('scripts/done_run.sh').read_text()
clause="resolve it through the Write boundary rule's operator-gated remedy (docs/history/backlog/PLAN-PROMPTS.md Standing rules; the remedy covers every staged path refused by either guard, regardless of who staged it or whether the writer declared it, with or without an unstaged live delta; an unattended writer stands down or parks without operator direction)"
two=r'''commit_die 1 "rolling-log pre-stage guard: a staged delta already exists on a rolling prompt log; ''' + clause + r'''; residue left untouched: $(printf '%s' "$rl_residue" | tr '\n' ' ')"'''
staged='commit_die 1 "rolling-log pre-stage guard: a staged path outside the declared owned log set refuses before staging; '+clause+'; bytes left untouched:$rl_foreign"'
if two not in source or staged not in source:
    raise SystemExit('complete refusal tail or residue operand changed')
PY
python3 - <<'PY' || fail "refusal snapshot gates are incomplete"
import ast
from pathlib import Path
tree = ast.parse(Path('scripts/test_done_run_wrapper.py').read_text())
funcs = {node.name: node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
for name in ('test_foreign_staged_path_refuses_before_git_add', '_unverifiable_cleanup_case'):
    node = funcs.get(name)
    if node is None:
        raise SystemExit(f'missing refusal witness: {name}')
    calls = [n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'capture_refusal_snapshot']
    if len(calls) != 2:
        raise SystemExit(f'{name} must capture before and after refusal')
    if not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'assertEqual' and len(n.args) >= 2 and all(isinstance(arg, ast.Name) for arg in n.args[:2]) and {n.args[0].id, n.args[1].id} == {'before', 'after'} for n in ast.walk(node)):
        raise SystemExit(f'{name} must compare the before and after snapshots')
helper = funcs.get('capture_refusal_snapshot')
if helper is None:
    raise SystemExit('missing full refusal snapshot helper')
helper_source = ast.get_source_segment(Path('scripts/test_done_run_wrapper.py').read_text(), helper) or ''
if 'self.git("ls-files", "-s", "-z")' not in helper_source or '.read_bytes()' not in helper_source:
    raise SystemExit('snapshot helper must capture exact index entries and affected worktree bytes')
if 'self.git("rev-parse", "HEAD")' not in helper_source:
    raise SystemExit('snapshot helper must capture the HEAD OID')
PY
bash -n scripts/done_run.sh || fail "done_run.sh syntax"
env -u AI_PLAYBOOK_TEST_VENV -u BASH_ENV PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_done_run_wrapper.py' || fail "existing wrapper behavior suite"
# 3. Task 1: the widened trigger names both pre-stage guards (unique span; whole-file pin).
test "$(grep -oF 'either the two-path staged-delta check or the staged-set enumeration' docs/history/backlog/PLAN-PROMPTS.md | wc -l | tr -d ' ')" -eq 1 || fail "Write boundary rule missing the widened trigger (or span duplicated)"
# 4. Task 1 and Task 2: automatic declared-path handling and staged-path ordering.
test "$(grep -oF 'Unstaged-live-delta set-aside arm' docs/history/backlog/PLAN-PROMPTS.md | wc -l | tr -d ' ')" -eq 1 || fail "set-aside arm label missing or duplicated"
if ! grep -qF "automatically isolates worktree-only declared-path deltas without a new refusal or operator prompt" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "Automatically isolate unstaged-only declared deltas" docs/history/backlog/PLAN-PROMPTS.md; then fail "unstaged-only declared-path handling is not automatic"; fi
if ! grep -qF "the stored blob id the only recovery source" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "blob IDs (only recovery source)" docs/history/backlog/PLAN-PROMPTS.md; then fail "arm missing its durable blob source"; fi
if ! grep -qF "after this set-aside, never before it" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "Check ride-along after set-aside" docs/history/backlog/PLAN-PROMPTS.md; then fail "ride-along ordering changed"; fi
if ! grep -qF "after the compare-and-swap on a path the writer declared" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "declared after CAS" docs/history/backlog/PLAN-PROMPTS.md; then fail "declared-path re-apply ordering missing"; fi
if ! grep -qF "after step (e) passes on a foreign path the writer did not declare" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "undeclared after (e)" docs/history/backlog/PLAN-PROMPTS.md; then fail "undeclared-path re-apply ordering missing"; fi
if ! grep -qF "the writer re-applies each recorded delta to the worktree only, never the index" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "Reapply worktree-only" docs/history/backlog/PLAN-PROMPTS.md; then fail "re-apply must stay out of the index"; fi
if ! grep -qF "On declared paths, steps (d) and (e) do not run for that path" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "Declared paths skip (d)/(e)" docs/history/backlog/PLAN-PROMPTS.md; then fail "declared-path exception missing"; fi
if ! grep -qF "the operator's explicit direction" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "staged bytes refused by either guard keep the operator gate" docs/history/backlog/PLAN-PROMPTS.md; then fail "staged-path operator gate wording lost"; fi
# 5. Task 1 and Task 2: mismatch parks and reports retained source identifiers.
if ! grep -qF "a verification mismatch, and any byte set the re-apply cannot verify, leaves the bytes unstaged and parks for the operator with every recorded blob id in the report" docs/history/backlog/PLAN-PROMPTS.md && ! grep -qF "A re-apply mismatch leaves bytes unstaged and parks for the operator with every recorded blob id" docs/history/backlog/PLAN-PROMPTS.md; then fail "mismatch park report missing"; fi
# 6. Task 3: both shared procedures carry the complete repository-neutral pointer.
pointer_sentence="After either pre-stage guard refuses a staged path in a primary rolling-log write, consult the consuming repository's canonical write-boundary rule and follow its operator-gated remedy, regardless of who staged it or whether the path was declared. For an unstaged-only live delta on a declared path, use the automatic set-aside arm without another prompt. If the rule is absent or does not cover the case, park. An unattended writer stands down or parks without operator direction."
test "$(grep -Fc "$pointer_sentence" agents/skills/maintenance/template-authoring.md)" -eq 1 || fail "template-authoring pointer sentence missing"
test "$(grep -Fc "$pointer_sentence" agents/skills/execute-plan/worktree-first.md)" -eq 1 || fail "worktree-first pointer sentence missing"
test "$(grep -Fc "FINAL STEP, after the report: apply directive D-17" agents/skills/maintenance/template-authoring.md)" -eq 1 || fail "template-authoring duplicate D-17 clause remains or final clause was removed"
grep -qF "Chaining guard: this payload is your whole task" agents/skills/maintenance/template-authoring.md || fail "template-authoring chaining guard was removed"
template_before="$(git cat-file -s HEAD:agents/skills/maintenance/template-authoring.md)" || fail "cannot read pre-task template size"
template_after="$(wc -c < agents/skills/maintenance/template-authoring.md | tr -d ' ')" || fail "cannot read edited template size"
test "$template_after" -le "$template_before" || fail "template-authoring.md grew instead of paying for the insertion"
echo "template-authoring.md bytes: $template_before -> $template_after"
worktree_first_before="$(git cat-file -s HEAD:agents/skills/execute-plan/worktree-first.md)" || fail "cannot read pre-task worktree-first size"
worktree_first_after="$(wc -c < agents/skills/execute-plan/worktree-first.md | tr -d ' ')" || fail "cannot read edited worktree-first size"
test "$worktree_first_after" -le "$worktree_first_before" || fail "worktree-first.md grew instead of paying for the insertion"
echo "worktree-first.md bytes: $worktree_first_before -> $worktree_first_after"
# 7. Repository gates over the touched set.
env -u PINS_DUPLICATE_ROOT -u PINS_RECORDED_RED_REGISTER -u PINS_RECORDED_RED_AS_OF bash scripts/check_maintenance_pins.sh || fail "pins suite"
manifest_path="docs/tmp/execute-plan/rolling-log-write-residue-recovery-recipe/manifest.md"
run_base_record="$(sed -n 's/^run_base: //p' "$manifest_path")"
run_base="$(printf '%s' "$run_base_record" | sed -E 's/.*@//')"
test -n "$run_base" || fail "run base missing"
git rev-parse --verify "$run_base^{commit}" >/dev/null 2>&1 || fail "run base invalid"
python3 - "$run_base" <<'PY' || fail "prompt-entry prune allowlist exceeded"
import re
import subprocess
import sys
base = sys.argv[1]
log = "docs/history/backlog/PLAN-PROMPTS.md"
diff = subprocess.run(["git", "diff", "--unified=0", base, "--", log], check=True, text=True, stdout=subprocess.PIPE).stdout
removed = set(value.strip() for value in re.findall(r"^-[ \t]*## (.+)$", diff, re.MULTILINE))
allowed = {"backlog-completed-dir-regrowth", "test-suite-runtime-residual-optimization-path"}
unexpected = sorted(removed - allowed)
if unexpected:
    raise SystemExit(f"removed prompt entries outside the approved allowlist: {unexpected}")
print("removed prompt entries within allowlist:", sorted(removed))
PY
python3 scripts/check_prompt_log_origins.py docs/history/backlog/PLAN-PROMPTS.md || fail "prompt-log origin check"
python3 scripts/check_prompt_log_origins.py --prune-audit --base "$run_base" docs/history/backlog/PLAN-PROMPTS.md || fail "prompt-log prune audit"
plan_touched=(
  docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md
  docs/history/backlog/PLAN-PROMPTS.md
  scripts/check_maintenance_pins.sh
  agents/skills/maintenance/template-authoring.md
  agents/skills/execute-plan/worktree-first.md
  scripts/done_run.sh
  scripts/test_done_run_wrapper.py
)
bash scripts/check-no-em-dash.sh added-lines --base "$run_base" -- "${plan_touched[@]}" || fail "em-dash added-lines gate over plan-touched paths"
# 8. Task 2: pre-CAS refusal retains the operation journal and does not retry.
grep -qF "Early pre-stage refusal before cleanup: re-read journal/state; never retry/succeed; keep peer bytes out of index; park with ref/state" docs/history/backlog/PLAN-PROMPTS.md || fail "early pre-stage refusal recovery missing"
grep -qF "runner-resume-prepared" docs/history/backlog/PLAN-PROMPTS.md || fail "runner retry intent is not journaled before index restore"
grep -qF 'candidate-index + candidate-worktree means repeat restore; HEAD-index + candidate-worktree means CAS `runner-resume-ready`' docs/history/backlog/PLAN-PROMPTS.md || fail "prepared recovery cannot distinguish the crash window"
grep -qF 'recorded subject, `--expected-ref` and `--expected-oid`; do not reread/edit' docs/history/backlog/PLAN-PROMPTS.md || fail "resume lost its captured subject/ref/HEAD pair or replays the writer edit"
# 9. Task 2: compare the implemented arm with its single canonical plan block.
python3 - <<'PY' || fail "Task 2 arm differs from its prescribed canonical text"
from pathlib import Path
bt = chr(96)
plan = Path('docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md').read_text()
task2_heading = "### " + "Task " + "2: isolate declared-path writer bytes and preserve them on pre-CAS refusal"
task2 = plan.split(task2_heading, 1)[1]
marker = "Replace Task 1's inserted arm with the exact journal-backed recovery procedure below;"
marker_at = task2.index(marker)
fence_start = task2.index(bt * 3 + 'text\n', marker_at) + len(bt * 3 + 'text\n')
fence_end = task2.index('\n' + bt * 3, fence_start)
expected = task2[fence_start:fence_end]
log = Path('docs/history/backlog/PLAN-PROMPTS.md').read_text()
if log.count('Unstaged-live-delta set-aside arm:') != 1:
    raise SystemExit('the implemented recovery arm is missing or duplicated')
start = log.index('Unstaged-live-delta set-aside arm:')
end = log.index('Ride-along precondition:', start)
actual = log[start:end].rstrip()
if actual != expected:
    raise SystemExit('the prompt-log recovery arm differs from Task 2 canonical text')
PY
# 9. Task 2: exact canonical equality above pins the complete arm; retain the negative regression guard.
if grep -qF "every peer owner is paused" docs/history/backlog/PLAN-PROMPTS.md; then fail "unpriced peer-pause precondition remains"; fi
# 10. Task 2: measure net same-file byte payment against the Task 1 draft.
select_task1_boundary() { printf '%s\n' "$1" | grep -i '^task_boundary:.*Task 1 ' | tail -n 1; }
lowercase_fixture="$(select_task1_boundary 'task_boundary: task 1 commit 0123456789abcdef')"
test "$lowercase_fixture" = 'task_boundary: task 1 commit 0123456789abcdef' || fail "shared Task 1 selector rejected the lowercase fixture"
task1_row="$(select_task1_boundary "$(cat "$manifest_path")")"
test -n "$task1_row" || fail "Task 1 boundary row is missing from the manifest"
task1_commit="$(printf '%s
' "$task1_row" | sed -E 's/.*commit ([[:xdigit:]]{7,40}).*/\1/')"
test "$task1_commit" != "$task1_row" || fail "Task 1 boundary commit cannot be read from the manifest"
git rev-parse --verify "$task1_commit^{commit}" >/dev/null 2>&1 || fail "Task 1 boundary commit is invalid"
task1_bytes="$(git cat-file -s "$task1_commit:docs/history/backlog/PLAN-PROMPTS.md")" || fail "Task 1 byte count unavailable"
post_task2_bytes="$(wc -c < docs/history/backlog/PLAN-PROMPTS.md | tr -d ' ')" || fail "post-Task 2 byte count unavailable"
test "$post_task2_bytes" -le "$task1_bytes" || fail "Task 2 grew the Write boundary rule beyond its Task 1 draft"
echo "PLAN-PROMPTS.md bytes: $task1_bytes -> $post_task2_bytes"
```

### Task 1: widen the Write boundary rule trigger and add the Unstaged-live-delta set-aside arm

Context surface: the plan's Terms and Standing constraints; referenced, never restated.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`

- [x] The Write boundary rule delivers the widened trigger: given a pre-stage refusal naming a foreign staged path from either pre-stage guard, expects the remedy's opening clause to name both guards (the two-path staged-delta check and the staged-set enumeration) and to apply whether or not the writer declared the path [class: IMPLEMENTATION_REQUIRED]
- [x] The Write boundary rule delivers the Unstaged-live-delta set-aside arm: given a foreign staged path whose worktree bytes carry an unstaged live delta, or a declared log path carrying an unstaged live peer delta with no staged residue, expects the arm to prescribe recording each preserved byte set into the object store (`git hash-object -w`), holding it out of the committed tree across the transaction, and re-applying it after with byte-identical verification [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (ordering): given the same residue condition, expects the ride-along precondition to be evaluated after the set-aside, never before it, the re-apply on an undeclared foreign path to run after step (e) passes, and the re-apply on a declared path to run after the compare-and-swap, never before the transaction's commit [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (declared path): given a foreign staged blob on the writer's own declared log path, with or without an unstaged delta, expects the arm to activate, steps (d) and (e) not to run for that path, the precondition comparison not to apply, the staged blob never re-staged, and its blob id reported for the operator's disposition [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness (mismatch): given a re-apply verification mismatch, expects the bytes left unstaged and the run parked for the operator with every recorded blob id in the report [class: IMPLEMENTATION_REQUIRED]
- [x] Replace, in the Write boundary rule bullet, exactly the span `When the runner's pre-stage guard (the staged-set enumeration) refuses the transaction naming a foreign staged path (staged in the shared primary index by a session other than this writer, outside the writer's declared owned set), the remedy is operator-gated and blob-preserving` with the following span, keeping the following tail `: never stage, discard, or commit that path autonomously` byte-identical [class: IMPLEMENTATION_REQUIRED]:

```text
Unstaged-live-delta set-aside arm: Under the done lock, snapshot declared rolling-log paths before final read/edit. Automatically isolate unstaged-only declared deltas; staged bytes refused by either guard keep the operator gate. One UUID is the Operation ID; create one zero-old-OID ref `refs/ai-playbook/recovery/<session-id>/<operation-id>` to a Git tree of `record.json` and saved blobs. Record primary ref, starting HEAD and intended commit subject once; per path, journal `git hash-object -w` blob IDs (only recovery source), before/after HEAD/index/worktree IDs+modes, candidate/output IDs, class and ordered transitions. CAS phases: captured, index-set-aside, candidate-installed, runner-staged, runner-resume-prepared, runner-resume-ready, committed, peer-reapplied, disposition-verified. Before manifest, only ref/live paths recover; no manifest report or per-path refs. Byte recovery supports 100644/100755 only; other modes stay untouched and park without following symlinks or treating gitlinks as blobs. Declared: journal staged blob; set its index to HEAD; merge pre-write worktree/HEAD/post-edit as base/ours/theirs; install candidate worktree-only. Check ride-along after set-aside. Undeclared: restore only index to HEAD; install saved staged blob worktree-only; verify index ID/mode before (a)-(e). Reapply deltas worktree-only: undeclared after (e), declared after CAS, with HEAD/base, committed writer/ours, pre-write worktree/theirs. Hash each candidate, merge, and re-apply output; verify its output ID (never input); rederive clean merge. Declared paths skip (d)/(e), never re-add staged blobs, report IDs. Early pre-stage refusal before cleanup: re-read journal/state; never retry or report success, keep peer bytes out of index, park. Post-stage pre-CAS refusal: verify candidate index/worktree IDs+modes. Before unstage, CAS `runner-resume-prepared` with candidate-index and HEAD-index IDs/modes plus candidate-worktree ID/mode. Under lock recheck ref/HEAD; restore only candidate index entries to HEAD, keeping worktree. Resume from prepared: candidate-index + candidate-worktree means repeat restore; HEAD-index + candidate-worktree means CAS `runner-resume-ready`; any other state parks. From ready, rerun existing transaction with `--stage` paths, recorded subject, `--expected-ref` and `--expected-oid`; do not reread/edit. If retry fails with candidate staged, repeat prepared; cleanup never resets index. Post-CAS nonzero: prove the landed commit is the sole direct child of recorded starting HEAD, the target of the expected primary ref, has the recorded subject, and each declared path's committed tree entry ID/mode matches its journaled candidate output; only then finish peer re-application. Otherwise retain the ref and park. Before later primary read/edit under lock, resume unverified refs. Mismatch/conflict/journal error/ambiguous ref: leave bytes unstaged; retain ref, park, report every recorded blob ID. Automatic terminal requires output ID/mode match and unchanged committed index. Operator-gated terminal requires current-session path/operation direction and verified final IDs/modes; later mutation needs fresh direction. Verify final HEAD/index/worktree IDs/modes; retain ref through terminal paths, recheck under lock, remove only it.
```

- [x] Insert the following arm text into the Write boundary rule bullet immediately before the sentence beginning `Ride-along precondition:`, byte-identical [class: IMPLEMENTATION_REQUIRED]:

```text
Unstaged-live-delta set-aside arm: when the foreign staged path also carries an unstaged live delta, or the writer's declared log path carries a foreign staged blob (with or without an unstaged live delta) or an unstaged live peer delta with no staged residue, the plain steps cannot complete (the re-add stages the worktree bytes, the staged blob plus the delta, so the sha check can never match; and a declared path's transaction would commit foreign or peer bytes together with the writer's own). This arm automatically isolates worktree-only declared-path deltas without a new refusal or operator prompt; foreign staged bytes keep the existing pre-stage refusal and require the operator's explicit direction. The writer records each preserved byte set into the object store (`git hash-object -w`, the stored blob id the only recovery source) and then sets the path's worktree bytes so the transaction sees only the writer's own state: on a path the writer declared, exactly the writer's committed base plus the writer's own edit (the lesson 290 construction); on a foreign path the writer did not declare, the recorded staged blob. The ride-along precondition is evaluated after this set-aside, never before it; on a path the writer declared, the precondition's worktree-equals-staged-blob comparison does not apply (the set-aside construction carries the identity, and the recorded blob ids are the verification of record). The transaction then runs; the writer re-applies each recorded delta to the worktree only, never the index, after step (e) passes on a foreign path the writer did not declare, and after the compare-and-swap on a path the writer declared; the re-apply verifies the re-applied bytes hash to their recorded blob ids before reporting success; On declared paths, steps (d) and (e) do not run for that path: the writer's own commit already carries the path, the recorded delta re-applies as unstaged worktree bytes verified against their blob ids, and the recorded foreign staged blob stays out of the index, its blob id reported for the operator's disposition; a verification mismatch, and any byte set the re-apply cannot verify, leaves the bytes unstaged and parks for the operator with every recorded blob id in the report.
```

- [x] Run → expect RED: validation commands 3 and 4 fail on today's bytes (executed at authoring; recorded rc=1) [class: REPOSITORY_TEST]
- [x] Write both prescribed spans byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: validation commands 3, 4, and 5 pass [class: REPOSITORY_TEST]
- [x] Commit: `docs: widen the Write boundary rule trigger and add the set-aside arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: isolate declared-path writer bytes and preserve them on pre-CAS refusal

Context surface: Terms for the operation journal, operation ID, operator direction witness, pre-write snapshot, and Ride-along precondition; Task 1's Write boundary rule set-aside arm and runner transaction cleanup; referenced, never restated.

Files:
- docs/history/backlog/PLAN-PROMPTS.md

- [x] Journal witness: under done lock, snapshot declared paths before final read/edit; isolate unstaged-only deltas automatically; staged bytes use existing refusal/direction [class: IMPLEMENTATION_REQUIRED]
- [x] Operation cardinality: create one UUID and zero-old-OID ref before mutation; record primary ref, starting HEAD and commit subject once; journal each path's before/after HEAD/index/worktree IDs+modes and ordered CAS phases [class: IMPLEMENTATION_REQUIRED]
- [x] Declared-path isolation: merge captured pre-write worktree as base, captured HEAD as ours, and post-edit worktree as theirs; verify/install the writer candidate worktree-only. For staged residue, restore only the foreign index entry to captured HEAD and keep its blob in the journal [class: IMPLEMENTATION_REQUIRED]
- [x] Resume safety: after post-CAS nonzero, accept only the sole child of starting HEAD targeted by the expected primary ref, with recorded subject and declared candidate tree IDs/modes matched; otherwise retain the ref and park. Before later log reads/edits, resume incomplete operations under lock [class: IMPLEMENTATION_REQUIRED]
- [x] Hash witness: hash candidate, merge and re-apply outputs separately; verify installed bytes by output ID (not inputs) and rederive clean peer merge from journal [class: IMPLEMENTATION_REQUIRED]
- [x] Ref lifecycle: create one transaction-wide operation ref with a zero old OID before path mutation and CAS-update it after each verified phase. Automatic paths reach disposition-verified from recorded output bytes, mode, and unchanged index [class: IMPLEMENTATION_REQUIRED]
- [x] Operator-gated disposition: require current-session, operation- and path-bound direction, a confirmed disposition, and matching final HEAD/index/worktree IDs and modes. A later session needs fresh direction before mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Ref removal: retain one ref through every path's terminal disposition; recheck state under lock before removal [class: IMPLEMENTATION_REQUIRED]
- [x] Resume intent: before path-limited index restore, CAS `runner-resume-prepared` with candidate-index and HEAD-index IDs/modes plus candidate-worktree ID/mode [class: IMPLEMENTATION_REQUIRED]
- [x] Resume state: under lock restore only matching candidate index entries to HEAD; from prepared, repeat for candidate-index/worktree match or CAS ready for HEAD-index/candidate-worktree match; other state parks [class: IMPLEMENTATION_REQUIRED]
- [x] Runner retry: from ready, rerun with declared `--stage` paths and recorded subject/ref/HEAD pair; if refusal leaves candidate staged, return to prepared; never reread/replay or assume cleanup resets index [class: IMPLEMENTATION_REQUIRED]
- [x] Mode guard: before byte-oriented recovery, support only regular-file modes 100644 and 100755; otherwise leave HEAD, index, and worktree untouched, retain the ref, and use the existing operator-gated parking path without following a symlink or treating a gitlink as a blob [class: IMPLEMENTATION_REQUIRED]
- [x] Undeclared foreign-path set-aside: journal the staged blob and any unstaged delta; restore only that path’s index entry to captured HEAD, install the saved staged blob in the worktree, and verify the index ID/mode still match captured HEAD before steps (a)-(e); then re-apply any saved delta to the worktree only, never the index, and verify its output ID [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED: Validation Command 9 fails on Task 1's output; Command 10 passes on the Task 1 boundary, exercising the same lowercase-aware selector on its fixture and the manifest [class: REPOSITORY_TEST]
- [x] Replace Task 1's inserted arm with the exact journal-backed recovery procedure below; replace its Ride-along sentence with the mode-aware comparison below and preserve Task 1's launch scope [class: IMPLEMENTATION_REQUIRED]

```text
Unstaged-live-delta set-aside arm: Under done lock, snapshot declared logs before final read/edit. Automatically isolate unstaged-only declared deltas; staged bytes refused by either guard keep the operator gate. Create UUID and one zero-old-OID ref to record.json/blobs. Journal ref/start HEAD/subject; per path saved blob IDs (only recovery source), candidate/output IDs, class, before/after HEAD/index/worktree IDs+modes. CAS phases: captured, index-set-aside, candidate-installed, runner-staged, runner-resume-prepared, runner-resume-ready, committed, peer-reapplied, disposition-verified. Regular files 100644/100755 only; others park untouched; no symlink/gitlink following. Before mutation, recorded/current HEAD/index/worktree IDs+modes must match; else retain ref/park. Declared: save staged blob; set index to HEAD; merge captured worktree/HEAD/post-edit (base/ours/theirs); install candidate worktree-only. Undeclared: index=HEAD; install saved blob worktree-only; verify index before (a)-(e). Check ride-along after set-aside. Reapply worktree-only: undeclared after (e), declared after CAS; merge HEAD/base, committed writer/ours, saved worktree/theirs. Hash candidate/merge/reapply outputs separately; verify output IDs/modes, never inputs; rederive clean merge. Declared paths skip (d)/(e), never re-add staged blobs; report IDs. Early pre-stage refusal before cleanup: re-read journal/state; never retry/succeed; keep peer bytes out of index; park with ref/state. Post-stage refusal: verify candidate IDs/modes. Before restore, CAS runner-resume-prepared with candidate/HEAD index IDs+modes and worktree ID/mode; recheck ref/HEAD under lock; restore matching entries to HEAD, keep worktree. From prepared, candidate-index + candidate-worktree means repeat restore; HEAD-index + candidate-worktree means CAS `runner-resume-ready`; else park. From ready, rerun with declared `--stage` paths, recorded subject, `--expected-ref` and `--expected-oid`; do not reread/edit. Retry refusal with candidate staged returns to prepared; cleanup never resets index. Post-CAS: reapply only if landed commit is sole start-HEAD child and expected-ref target, with matching subject and declared tree IDs/modes; else retain/park. Before next primary read/edit, resume unverified refs under lock. A re-apply mismatch leaves bytes unstaged and parks for the operator with every recorded blob id. Automatic terminal: output ID/mode and unchanged index. Operator terminal: fresh current-session operation/path direction and confirmed final HEAD/index/worktree IDs+modes. Retain ref until terminal; recheck under lock and remove only it.
```

- [x] Replace the existing Ride-along precondition sentence with the following text, byte-identically [class: IMPLEMENTATION_REQUIRED]:

```text
Under lock, compare HEAD/index/worktree IDs+modes before each mutation; mismatch preserves bytes/ref and parks.
```

- [x] Run -> expect GREEN: Validation Commands 4, 5, 8, 9, and 10 pass on the Task 2 text; Command 10 reports PLAN-PROMPTS.md at or below its Task 1 boundary byte count [class: REPOSITORY_TEST]
- [x] Commit: docs: isolate writer bytes in rolling-log recovery arm [class: IMPLEMENTATION_REQUIRED]

### Task 3: point the pre-work procedures at the remedy

Context surface: the plan's Terms and Standing constraints; referenced, never restated.

Files:
- agents/skills/maintenance/template-authoring.md
- agents/skills/execute-plan/worktree-first.md

- [x] Both procedures direct any foreign staged path identified by either pre-stage guard, including paths outside the declared rolling-log set, to the canonical rule’s operator-gated remedy; unstaged-only declared-path deltas use the automatic arm without another prompt, missing coverage parks, and unattended writers stand down [class: IMPLEMENTATION_REQUIRED]
- [x] Balance the template insertion: remove the first duplicate D-17 FINAL STEP clause, preserve the final clause and adjacent Chaining guard, and show that the template does not grow [class: IMPLEMENTATION_REQUIRED]
- [x] Insert this exact sentence at the end of the existing pre-work paragraph in template-authoring.md [class: IMPLEMENTATION_REQUIRED]:

```
text
After either pre-stage guard refuses a staged path in a primary rolling-log write, consult the consuming repository's canonical write-boundary rule and follow its operator-gated remedy, regardless of who staged it or whether the path was declared. For an unstaged-only live delta on a declared path, use the automatic set-aside arm without another prompt. If the rule is absent or does not cover the case, park. An unattended writer stands down or parks without operator direction.
```

- [x] Replace the Pre-plan authoring arm paragraph in worktree-first.md with this shorter text, byte-identically; remove the redundant Phase 0 self-reference under Branch naming so the file does not grow [class: IMPLEMENTATION_REQUIRED]:

```
text
**Pre-plan authoring arm:** Before a plan exists, require a fresh docs/tmp/authoring-claims/<item>.md naming this session. Derive authoring/<claim-file-stem> from its filename; create a worktree with git worktree add -b authoring/<claim-file-stem> <worktree-root>/<claim-file-stem> <base-ref> and verify that branch is checked out, not detached. Missing or foreign claims refuse creation. If the branch exists, adopt only a live worktree bound to this claim through the survey and adoption arms, or deliberately remove the stale branch; never reuse blindly. Lifecycle step 4 owns landing; authoring-claim closeout owns claim deletion. After either pre-stage guard refuses a staged path in a primary rolling-log write, consult the consuming repository's canonical write-boundary rule and follow its operator-gated remedy, regardless of who staged it or whether the path was declared. For an unstaged-only live delta on a declared path, use the automatic set-aside arm without another prompt. If the rule is absent or does not cover the case, park. An unattended writer stands down or parks without operator direction.
```

- [x] Run -> expect RED: Validation Command 6 fails on today's bytes [class: REPOSITORY_TEST]
- [x] Write both pointers byte-identical and remove the duplicate D-17 clause; verify neither touched file grows [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: Validation Command 6 passes for both files [class: REPOSITORY_TEST]
- [x] Commit: docs: point the pre-work procedures at the set-aside remedy [class: IMPLEMENTATION_REQUIRED]

### Task 4: point both pre-stage refusal messages at the remedy

Context surface: the plan's Terms and Standing constraints; referenced, never restated.

Files:
- scripts/done_run.sh
- scripts/test_done_run_wrapper.py

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`

- [x] Both refusal messages name the remedy, its Standing rules home, declared-or-not and unstaged-delta coverage, and unattended stand-down-or-park default [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: add `capture_refusal_snapshot` for the HEAD OID, exact `self.git("ls-files", "-s", "-z")` entries, and affected worktree bytes via `read_bytes()`; both `test_foreign_staged_path_refuses_before_git_add` and `_unverifiable_cleanup_case` capture into `before`/`after` and assert equality after exit 1 before staging [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED: Validation Command 1 fails on today's bytes [class: REPOSITORY_TEST]
- [x] Replace only the two refusal messages with the following clause; preserve each guard, commit_die 1, and all leading and trailing residue text byte-identically [class: IMPLEMENTATION_REQUIRED]:

```
text
resolve it through the Write boundary rule's operator-gated remedy (docs/history/backlog/PLAN-PROMPTS.md Standing rules; the remedy covers every staged path refused by either guard, regardless of who staged it or whether the writer declared it, with or without an unstaged live delta; an unattended writer stands down or parks without operator direction)
```

- [x] Run -> expect GREEN: Validation Commands 1 and 2 pass, including the existing class-style wrapper suite [class: REPOSITORY_TEST]
- [x] Commit: fix: point both rolling-log pre-stage refusals at the operator-gated remedy [class: IMPLEMENTATION_REQUIRED]

### Task 5: repository gates and approved two-entry rider

Context surface: the Validation Commands block; scripts/check_prompt_log_origins.py supplies the read-only origin and prune audit.

Files:
- docs/history/backlog/PLAN-PROMPTS.md (exact rider)
- scripts/check_maintenance_pins.sh (Task 3 final-instruction count pin)
- docs/tmp/execute-plan/rolling-log-write-residue-recovery-recipe/manifest.md (read-only run_base)

- [x] Safety witness (stable scan base): use the valid run_base recorded in the manifest even if main advances, limit the added-lines scan to the plan-declared touched files, and reject every removed prompt-entry slug outside the exact two-entry allowlist [class: REPOSITORY_TEST]
- [x] For each of the two named entries still reported stale, verify all origins are served and its plan witness exists on current main; if an entry is already absent, record a skip; prune no other entry [class: IMPLEMENTATION_REQUIRED]
- [x] Prune allowlist: derive removed top-level entry slugs from the run_base-to-HEAD diff; permit only backlog-completed-dir-regrowth and test-suite-runtime-residual-optimization-path, even when another removal has a valid witness [class: REPOSITORY_TEST]
- [x] Reconcile the existing FINAL STEP prefix count with Task 3's committed removal: the three canonical template files each retain one prefix, so update the existing aggregate expected count from four to three and leave every other pin unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Remove only the two approved prompt texts; preserve all other bytes and prior receipts; map each removal to its actual current-main plan witness, preferring the completed archive twin when present and otherwise using the open plans-root path; never cite a future archive path [class: IMPLEMENTATION_REQUIRED]
- [x] Leave the active test-suite execution claim, worktree, and branch untouched; commit only the prompt-log rider through the canonical Step 1.4 explicit-path boundary. If done_run.sh refuses, preserve its refusal evidence and use Step 1.4 only under explicit operator recovery authorization, without changing or bypassing gates or claiming its sweep passed [class: IMPLEMENTATION_REQUIRED]
- [x] Run python3 scripts/check_prompt_log_origins.py docs/history/backlog/PLAN-PROMPTS.md and python3 scripts/check_prompt_log_origins.py --prune-audit --base "$run_base" docs/history/backlog/PLAN-PROMPTS.md; confirm no stale entry remains, then run Validation Commands 1 through 10 from the repository root; every command exits zero [class: REPOSITORY_TEST]
- [x] Run the public hygiene scan over the touched set; OUTCOME: pass [class: REPOSITORY_TEST]
