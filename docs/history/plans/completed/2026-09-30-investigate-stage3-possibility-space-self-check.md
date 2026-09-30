# Plan: Investigate Stage 3 possibility-space self-check

Backlog origin: docs/history/backlog/2026-09-30-investigate-prompt-possibility-space-review.md
Driving force: correctness
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-investigate-stage3-possibility-space-self-check-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

An investigate log entry's possibility space becomes checkable instead of self-attested: Stage 3 dispositions must cite their evidence basis, the enumeration must span beyond the recommendation's own family, a contested entry loses its standing pre-authorization, and a validator enforces the structural minimum over the live log.

- After this plan, a Stage 3 rejected-alternative disposition names its evidence basis - a disk witness, a landed mechanism, or a witnessed incident - not a bare assertion, and the enumeration includes at least one alternative from outside the recommended mechanism's family (the two standing axes stay the minimum, not the whole space).
- An entry whose alternatives were contested on evidence carries no `Standing pre-authorization` line, or scopes it to the non-contested arms, so a contested recommendation gets a genuine authoring-side look instead of a rubber stamp.
- `scripts/check_investigate_entries.py` (shaped after `scripts/doc_registry_validator.py`) checks each log entry's structural minimum - rejected-alternatives list non-empty, every disposition line citing at least one evidence-basis marker - and investigate Stage 4 runs it before the entry's write is committed; wholesale template drift fails loudly. The same execution citation-fixes every live entry that fails the minimum (audited 2026-09-30: 46 of 53 disposition lines across all 13 entries carry no marker), so the corpus run reads green because the log is genuinely evidenced, not because the gate was scoped around it.
- The never-execute-or-dispatch hard gate is untouched, and no per-entry review panel is added (machinery cost-benefit adjudication 2026-09-28).

Gate delta: adds three Stage 3 requirement bullets, one Stage 4 validator run step, one new validator script, and evidence-basis citations across the live log's failing disposition lines (the entry-citation pass is the plan's priced mass surface); removes nothing; priced by the witnessed class - entries flow into pre-authorized authoring turns with self-attested possibility spaces, and the pruned survey-mode entry's five rejected alternatives were asserted without any mechanical check.

## Terms

- **Evidence basis**: the cited ground a disposition rests on - a repo-relative disk path, a landed mechanism (a file or section that exists), a commit, or a witnessed incident; the validator's marker list is the mechanical form.
- **Mechanism family**: the implementation family the recommended resolution belongs to (for example a pins-suite change versus a skill-text change); an out-of-family alternative proposes a different family, not a variant of the same one.
- **Contested on evidence**: an operator or peer correction, recorded in the entry or its origin, that argues against one of the entry's dispositions with evidence - the trigger that drops or scopes the `Standing pre-authorization` line.
- **Structural minimum**: what the validator enforces per entry: a non-empty rejected-alternatives list and every disposition line carrying at least one evidence-basis marker; the pre-authorization cap is an authoring-side rule (Stage 3), never a validator check.

## Assumptions

- assume the validator is a new small script rather than an extension of `scripts/doc_registry_validator.py`; basis: the doc-registry validator owns a different corpus with its own conventions, and the origin prescribes the SHAPE (fail-loud structural checks), not the file; the review-staging validator's per-round precedent shows per-corpus scripts are the house pattern.
- assume the validator reads the live log (`docs/history/backlog/PLAN-PROMPTS.md` by default, overridable for fixtures) and its corpus run is the test surface, mirroring `scripts/check_plan_origins_closed.py`'s corpus mode; no separate test file is added, and the plan's Validation block runs it over the live entries.
- assume the survey-mode entry's prune (the log no longer carries it) voids the origin's coordination arm - there is no open survey-mode plan to fold into, so this plan stands alone; basis: probed the live log on 2026-09-30, zero matches for the entry name.
- assume the standing axes' two bullets stay byte-untouched; the additions sit beside them as new requirements, never rewording the witnessed-case example.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: investigate entries now carry evidence-cited, family-spanning rejected alternatives with a contested-entry pre-authorization cap, and a validator fails loudly when an entry loses that shape - the correctness force closes the one-sided-entry-into-pre-authorized-authoring hole.

**Before (today):** Stage 3 says "the recommendation must name what was rejected and why" and nothing checks the why. An entry like the pruned survey-mode one recommended keep-and-widen with five rejected alternatives whose dispositions were assertions; under `Standing pre-authorization: accept all recommended options`, the authoring turn consumes the whole space unchallenged - a strawmanned alternative flows straight into a plan.

**After (this plan):** The same entry must cite each disposition's basis (for example "rejected: a review panel per entry; basis: the machinery cost-benefit adjudication, docs/... 2026-09-28"), include at least one alternative outside the recommendation's family, and drop or scope the pre-authorization line when a disposition was contested on evidence. The validator turns a drifted or bare-asserted entry into a loud failure before the write commits, and the live log passes it at landing.

## Evaluation Criteria

**Quality dimensions:**

- fail-loud structure: a missing rejected-alternatives list, a bare-assertion disposition, or a drifted template fails the validator with the entry named; exit 0 means every live entry meets the structural minimum.
- no-chill: the requirements raise the evidence bar without adding a review panel, a second session, or any dispatch/execution behavior; the hard gates stay byte-untouched.
- by-reference discipline: the validator is referenced from Stage 4; the skill text never restates the marker list (the script owns it).

**Done when:**

- `python3 scripts/check_investigate_entries.py` exits 0 over the live log.
- The Validation Commands block below exits 0 end to end.
- The em-dash gate (`scripts/check-no-em-dash.sh touched`) exits 0 on the changed tree, and the hygiene scan named by `public_hygiene_scan_script` in the user facts exits 0.

**Ship when:**

- None; skill prose and a validator script only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/investigate/SKILL.md`
- `scripts/check_investigate_entries.py`
- `docs/history/backlog/PLAN-PROMPTS.md` (the citation-fix pass touches disposition lines only; entry prompts and scope arms stay byte-untouched)

**Tests:**

- the validator's corpus run over the live log is the test surface; no separate test file is added

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**. If the link is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- The Stage 3 standing-axes bullets; anchors, not rewording candidates.
- The log's standing write rules in Stage 4 (targeted edit, drift retry, same-turn commit); referenced, not restated.
- Any execute/dispatch behavior; the hard gates stay byte-untouched.

## Validation Commands

```bash
# Tasks 1-2: per-file wiring obligations (tokens verified absent from their files at authoring time, so a skipped task fails its grep)
grep -qF 'evidence basis' agents/skills/investigate/SKILL.md || { echo "FAIL: evidence-basis requirement missing"; exit 1; }
grep -qF 'outside the recommended mechanism' agents/skills/investigate/SKILL.md || { echo "FAIL: out-of-family requirement missing"; exit 1; }
grep -qF 'contested on evidence' agents/skills/investigate/SKILL.md || { echo "FAIL: pre-authorization cap missing"; exit 1; }
grep -qF 'check_investigate_entries.py' agents/skills/investigate/SKILL.md || { echo "FAIL: Stage 4 validator wiring missing"; exit 1; }

# Task 2: the validator passes the live corpus (the corpus run is the test surface)
python3 scripts/check_investigate_entries.py || { echo "FAIL: live log entries"; exit 1; }

# Task 2: the validator fails loudly on a drifted fixture (fail-closed demonstration)
WORK="$(mktemp -d)"
printf '# Rolling prompt log\n\n## p9000-fixture\n\nOrigins:\n- docs/history/backlog/2026-01-01-widget.md\n\nPrompt: fixture prompt body.\n' > "$WORK/PLAN-PROMPTS.md"
python3 scripts/check_investigate_entries.py --log "$WORK/PLAN-PROMPTS.md" >/dev/null 2>&1; [ $? -eq 1 ] || { echo "FAIL: missing rejected-alternatives must exit 1"; rm -rf "$WORK"; exit 1; }
printf '# Rolling prompt log\n\n## p9000-fixture\n\nOrigins:\n- docs/history/backlog/2026-01-01-widget.md\n\nPrompt: fixture prompt body.\n\nRejected alternatives:\n- none considered\n' > "$WORK/PLAN-PROMPTS.md"
python3 scripts/check_investigate_entries.py --log "$WORK/PLAN-PROMPTS.md" >/dev/null 2>&1; [ $? -eq 1 ] || { echo "FAIL: bare assertion must exit 1"; rm -rf "$WORK"; exit 1; }
rm -rf "$WORK"

# Negative guard: the hard gate and both standing axes stay byte-untouched (tokens match the live lines)
if git diff "$(git merge-base main HEAD)" -- agents/skills/investigate/SKILL.md | grep -qE '^-.*(Never execute or dispatch anything|remove-or-keep axis|missing-complement axis)'; then echo "FAIL: hard gate or axes reworded"; exit 1; fi

# Em-dash gate on the changed tree
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em dash in changed tree"; exit 1; }
```

### Task 1: Stage 3 hardening and Stage 4 wiring

Files:

- `agents/skills/investigate/SKILL.md`

Evidence:

- The Validation Commands block's skill greps; each covers one prescribed literal below.

- [x] Add to Stage 3, after the standing-axes bullets: an evidence-basis requirement bullet - every rejected-alternative disposition cites its evidence basis (a disk witness, a landed mechanism, a commit, or a witnessed incident), never a bare assertion [class: IMPLEMENTATION_REQUIRED]
- [x] Add to Stage 3: a family-span requirement bullet - the enumeration includes at least one alternative from outside the recommended mechanism's family; the two standing axes stay the minimum, not the whole space [class: IMPLEMENTATION_REQUIRED]
- [x] Add to Stage 3: a pre-authorization cap bullet - an entry whose alternatives were contested on evidence carries no `Standing pre-authorization` line, or scopes it to the non-contested arms, so a contested recommendation gets a genuine authoring-side look [class: IMPLEMENTATION_REQUIRED]
- [x] Add to Stage 4, before the write rule: a validator step - the entry passes `python3 scripts/check_investigate_entries.py` (the structural minimum the script owns) before the write is committed [class: IMPLEMENTATION_REQUIRED]

### Task 2: The structural-minimum validator

Files:

- `scripts/check_investigate_entries.py` *(new)*

Evidence:

- The Validation Commands block's corpus run and both fixture demonstrations; covers the fail-loud and no-chill criteria.

- [x] Create the validator shaped after `scripts/doc_registry_validator.py` (argparse, exit 0 clean / 1 violations named / 2 tool failure): default log path `docs/history/backlog/PLAN-PROMPTS.md`, `--log` override for fixtures [class: IMPLEMENTATION_REQUIRED]
- [x] The validator checks, per entry - a `## ` section outside the file's fenced blocks and after the preamble (the fenced entry-template block is not an entry): a non-empty `Rejected alternatives:` list, and every disposition line (a list item under `Rejected alternatives:` until the next field heading) carrying at least one evidence-basis marker - a repo-relative path (`docs/`, `agents/`, `scripts/`), a word-bounded 7-40 hex commit, or the tokens `witnessed`, `adjudication`, `plan docs/history/`, or a quoted operator correction; the markers are the mechanical floor, deliberate superset of the conceptual kinds, and review supplies the judgment above it [class: IMPLEMENTATION_REQUIRED]
- [x] The validator's failure output names the entry slug and the failing line so a drifted entry is actionable [class: IMPLEMENTATION_REQUIRED]
- [x] Run the validator over the live log and record its exit 0; every live entry that fails the structural minimum is citation-fixed in the same execution (each failing disposition line gains its evidence-basis marker - the basis these entries already name in their own prompt prose: the executed plan, the witnessed incident, the landed surface), with no residual branch: the corpus run reads green only when the whole log passes [class: IMPLEMENTATION_REQUIRED]

### Task 3: Validation execution

Files:

- none (execution-only task)

Evidence:

- The Validation Commands block, run end to end from the executing worktree root; covers every Done-when criterion.

- [ ] Run the Validation Commands block end to end and record its exit 0, then run the hygiene scan named by `public_hygiene_scan_script` in the user facts over the changed tree and record exit 0 [class: REPOSITORY_TEST]
