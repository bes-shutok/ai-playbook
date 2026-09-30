# Plan: Skill description length gate

Backlog origin: docs/history/backlog/2026-09-29-skill-description-length-gate.md
Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-skill-description-length-gate-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A mechanical gate measures every SKILL.md frontmatter description's folded length at commit time, so an over-cap description fails the done pre-commit sweep with a named file instead of silently dropping the skill from the agent registry at runtime.

- The witnessed 2026-09-29 incident class (execute-plan at 1167 characters, vanishing from the skill list with no registry error) surfaces as a gate failure at authoring time from now on.
- Near-limit descriptions (over 950 characters) are reported as visible warnings before they trip.
- The corpus measures clean at gate go-live: no skill exceeds the cap, and the one warn-band entry (`agterm`, 956 folded characters, the origin's own named next candidate) is trimmed under the warning threshold in the same pass, clearing the origin's repeat-the-incident prediction.

Gate delta: one new mechanical check (a focused script plus one pre-commit sweep gate wired after instruction-size) is added. This is a refusal-path addition on a tooling-class origin carrying its pricing: the origin is a witnessed-incident capture whose completed-integrity failure is the silent registry drop (the incident paragraph), and whose Suggested fix prescribes exactly this shape (a sibling check wired into the done pre-commit sweep gate run, fail over 1024, warn over about 950). The class-default alternatives are addressed by the origin: there is no false positive to remove (the cap exists only as prose today) and no smaller exit exists (a prose restatement is the unenforced status quo the incident falsified).

## Terms

- **Folded description**: the frontmatter `description` value with folded block scalars (`>`/`|` forms) joined to single-spaced text, measured in characters against the cap.
- **Bounded frontmatter parse**: the parse binds to the closing `---` fence of the frontmatter block, so fenced code blocks in the document body are never swallowed by an indented-line match.
- **Description-length gate**: the `description-length` gate in the done pre-commit sweep, invoking `scripts/check_skill_description_length.py` and failing on any over-cap skill file.

## Assumptions

- assume the cap and warning thresholds are exactly the origin's numbers: fail over 1024 characters, warn over 950; basis: the origin's Suggested fix and the how-to-write-skills Frontmatter Requirements rule the item cites.
- assume the check walks every `SKILL.md` under the scanned skill tree (repo-root-relative `agents/skills/*/SKILL.md` when invoked from the skills repo; the done gate invokes it repo-rooted like the instruction-size gate), measuring the folded description with the bounded parse; basis: the origin's Expected bullet ("any SKILL.md frontmatter description") and its parse-bound warning.
- assume the authoring-time corpus measurement is current evidence, measured with a line-based bounded extraction and cross-checked against the origin's own recorded numbers: `agterm` at 956 folded characters (the origin's named near-limit candidate, warn band), `execute-plan` at 922, and no skill over 1024 (zero over-cap); basis: the authoring probe re-run on this tree immediately before authoring with the corrected parser (the probe's first folded-scalar regex swallowed the rest of the frontmatter block and reported a false 1310 for agterm - the same parse-bound trap the origin warns about, witnessed at authoring and corrected before the plan was finalized; measurement provenance recorded per the plans authoring rules).
- assume the origin's declared `Class: tooling` agrees with the fix-class routing (a missing enforcement artifact added per the origin's prescription, priced by the witnessed incident); basis: the origin header and body.
- assume the repository's pytest-runner contract applies to the new tests (venv interpreter first, ambient fallback with a version guard); basis: plan `docs/history/plans/completed/2026-09-30-done-sweep-closeout-baseline-exemption.md` Task 3 (Validation).
- assume adding one gate to the pre-commit phase is a deliberate contract change carried by this plan: the sweep-gate registry pins in `scripts/test_done_sweep_gates_lib.py` (the expected-order constant and the phase slices) are re-keyed in the wiring task, and done SKILL.md's gates-run-in-this-order prose gains the new gate; basis: the existing registry test's shape.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the done pre-commit sweep gains a description-length gate, and the corpus's one warn-band skill is trimmed back under the warning threshold; the driving force is automation (the cap stops being a comment and becomes a check that runs itself).

Before (today): a plan-landing commit grows a SKILL.md description past 1024 folded characters. Nothing measures it. At the next registration the runtime drops the skill silently; diagnosis needs a loaded-list-versus-disk diff and knowledge that the cap exists. This happened to execute-plan on 2026-09-29 (1167 characters, since trimmed to 922), and the corpus still carries the origin's named next candidate: `agterm` at 956 folded characters, one chronic edit away from the same silent drop, today visible to no check.

After (this plan): the same commit fails the done pre-commit sweep with `description-length: agents/skills/<name>/SKILL.md folded description <n> > 1024` before it can land, and a growing description prints a warning past 950. `agterm` is trimmed under the warning threshold in this plan, leaving the corpus with zero over-cap and zero warn-band entries, and the gate holds it there.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the folded-length parse binds to the closing frontmatter fence (a body containing fenced code blocks measures correctly), handles folded block scalars and single-line values, and reports file plus measured length on failure.
- regression safety: the sweep-gate registry pins are re-keyed to the thirteen-gate order deliberately and the full lib suite stays green; the done SKILL.md gate list names the new gate in run order.
- maintainability: the script carries a `--selftest` mode with embedded fixtures (over-cap, near-cap warn, folded scalar, body-fence trap) runnable standalone, and the gate mirrors the instruction-size deployment-gap semantics (script absent at every resolved path is a named deployment gap, never a skip).

**Done when:**
- `scripts/check_skill_description_length.py` passes its selftest and the new test file; the `description-length` gate is wired into the pre-commit phase after `instruction-size` with the registry pins re-keyed; `agents/skills/agterm/SKILL.md` measures at or under 950 folded characters (out of the warning band); done SKILL.md documents the gate; all Validation Commands exit 0.

**Ship when:**
- The runtime twins of the touched scripts and skills are refreshed per the operators' normal vendored-asset sync (the lib twin `~/.ai-playbook/scripts/done_sweep_gates_lib.py` is a real copy refreshed at execution closeout with a digest receipt; `~/.agents/skills/` copies likewise); consumer repositories receive the gate through the sweep runner they already deploy.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_skill_description_length.py` *(new)*
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/agterm/SKILL.md`
- `agents/skills/done/SKILL.md`

**Tests:**
- `scripts/test_skill_description_length.py` *(new)*
- `scripts/test_done_sweep_gates_lib.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Other skills' SKILL.md files; reason: the authoring probe measured no other skill over 950; the gate itself guards the whole corpus going forward.
- The how-to-write-skills prose rule; reason: the canonical rule text already exists and the origin cites it as the standard, not as a change target.

## Validation Commands

```bash
# Runner contract: venv pytest interpreter first, ambient fallback with a loud guard.
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. The script's dedicated tests pass.
"$TEST_PY" -m pytest scripts/test_skill_description_length.py -q || { echo "FAIL: description-length script tests" >&2; exit 1; }

# 2. The script's standalone selftest passes.
python3 scripts/check_skill_description_length.py --selftest || { echo "FAIL: selftest" >&2; exit 1; }

# 3. The whole lib suite passes (registry re-key + gate tests included).
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo "FAIL: lib suite" >&2; exit 1; }

# 4. The live corpus measures clean: no skill over 1024, agterm at or under the cap (fail-closed presence check first).
[ -f agents/skills/agterm/SKILL.md ] || { echo "FAIL: agterm missing" >&2; exit 1; }
python3 scripts/check_skill_description_length.py agents/skills || { echo "FAIL: corpus has an over-cap description" >&2; exit 1; }

# 5. The sweep gate is wired (dedicated pins).
grep -qF '"description-length"' scripts/done_sweep_gates_lib.py || { echo "FAIL: gate not registered" >&2; exit 1; }
grep -qF 'description-length' agents/skills/done/SKILL.md || { echo "FAIL: gate missing from done gate list" >&2; exit 1; }

# 6. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the corpus probe ran before authoring with a line-based bounded extraction (measurement provenance per rule 39: agterm 956, execute-plan 922, zero over 1024, matching the origin's own recorded numbers; the probe's first regex-based parse swallowed the rest of the frontmatter and was corrected before finalization - the origin's parse-bound trap, witnessed at authoring). RED-today evidence, rule 19: Commands 1 and 2 cannot pass before Tasks 1-2 create the files; Command 4's corpus leg passes today (zero over-cap) and its Task 3 completion leg (no agterm warning) is measurable only after Tasks 2-3; Command 5's pins are absent from both files today (verified). Rule 22 mechanical audit: each Validation Command pin occurs once in its owning Task's prescription beside its Command occurrence (plan-wide mentions in Gist and Terms are not pin sites); `bash -n` over this block passed.

### Task 1: Pin the checker contract (RED)

Files:
- `scripts/test_skill_description_length.py` *(new)*

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_skill_description_length.py -q`; covers: the contract fixtures exist and fail while the checker is absent.

- [ ] Create `scripts/test_skill_description_length.py` (pytest, subprocess invocation of the script at its repo-relative path, tmp_path fixture skills): `test_over_cap_fails` (a folded description at 1025 characters exits 1 naming the file and length), `test_at_cap_passes` (exactly 1024 exits 0), `test_near_cap_warns` (951-1024 exits 0 with a warning line on stderr or stdout), `test_folded_scalar_measured_folded` (a `>` block scalar spanning indented lines measures as single-spaced folded text), `test_body_fence_not_swallowed` (a body containing a fenced code block whose lines start with description-like indented text measures only the frontmatter), `test_missing_description_skipped` (a SKILL.md without a description key is skipped silently). [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the suite exits non-zero (the checker script does not exist; every invocation fails). [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin skill description length checker contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Implement the checker (GREEN)

Files:
- `scripts/check_skill_description_length.py` *(new)*

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_skill_description_length.py -q && python3 scripts/check_skill_description_length.py --selftest`; covers: every contract fixture and the standalone selftest.

- [ ] Implement `scripts/check_skill_description_length.py` (stdlib only): bounded frontmatter parse (bind to the closing `---`; no indented-line match beyond it), folded-scalar measurement, arguments `paths...` defaulting to the repo's `agents/skills` tree, exit 1 naming every over-cap file and length, warning lines for over-950 files, and a `--selftest` mode running the same fixture assertions embedded. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Task 1 suite and the selftest both exit 0. [class: REPOSITORY_TEST]
- [ ] Commit: `feat: folded skill description length checker with selftest` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Trim the warn-band skill (GREEN)

Files:
- `agents/skills/agterm/SKILL.md`

Evidence:
- `python3 scripts/check_skill_description_length.py agents/skills`; covers: the corpus exits 0 and agterm no longer appears in the warning band.

- [ ] Rewrite agterm's frontmatter description to at most 950 folded characters (clearing the warning band, not only the cap), preserving every trigger phrase and the skill's capability statement (drop redundancy, not triggers), and keeping the frontmatter shape otherwise unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the checker over the corpus exits 0 with no warning line for agterm (it exits 0 already after Task 2, with agterm warned; this task removes the warning). [class: REPOSITORY_TEST]
- [ ] Commit: `fix: trim agterm description under the warning band` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Wire the sweep gate (GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers: the re-keyed registry, the new gate tests, and the whole lib suite.

- [ ] Add `gate_description_length` to the lib mirroring `gate_instruction_size` (resolve `DESCRIPTION_LENGTH_CHECK_SCRIPT` / `check_skill_description_length.py`, deployment-gap failure naming the deploy remedy, invoke with the repo root, tail the output on failure) and register it under the exact registry key `"description-length"` in the pre-commit phase immediately after `instruction-size`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-key the sweep-gate registry pins in `scripts/test_done_sweep_gates_lib.py`: the expected-order constant gains `description-length` after `instruction-size`, the phase-slice assertions shift accordingly, the exact-count pins (`== 12` and siblings) in the registry test's body update to the new totals, and the constant's name is updated from its twelve-gate spelling to an order-neutral name recording the same contract (one deliberate rename, referenced everywhere it is used); sweep the lib docstring, CLI help text, and test comments for the stale twelve-gate count prose in the same edit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add a gate test (patterned on the existing gate tests with the `sweep_env` fixture) seeding a repo whose skills tree carries an over-cap fixture skill and asserting the gate returns rc 1 with the named file, plus an under-cap seed asserting rc 0. [class: REPOSITORY_TEST]
- [ ] Update `agents/skills/done/SKILL.md`: the gates-run-in-this-order prose and the per-gate fix guidance gain `description-length` (fix guidance: trim the folded description under 1024, keeping trigger phrases; a script absent from every resolved path is a rc 1 deployment gap, never a skip). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the lib suite exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `feat: wire description-length gate into the done pre-commit sweep` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Whole-plan validation gate

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- The full `## Validation Commands` block run from the worktree root; covers: every criterion in Done when (the new scripts are creation-owned by Tasks 1-2 and validated here by execution).

- [ ] Run the complete `## Validation Commands` block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for description length gate` [class: REPOSITORY_TEST]
