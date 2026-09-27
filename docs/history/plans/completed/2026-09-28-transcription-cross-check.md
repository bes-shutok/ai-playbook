# Plan: Transcription cross-check skill (dedupe, verify from source, canonical values)

Backlog origin: docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md
Driving force: new-capability + code-quality
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-transcription-cross-check-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A new cross-project skill, `agents/skills/transcription-cross-check/`, that turns the witnessed data-entry correction class (form field swaps, double-fills, duplicate invoice entries, wrong amounts carried into summaries; personal-admin repos run roughly twice the correction rate of the skill repo) into a standing three-duty cross-check: dedupe source-identical entries before writing, verify every written field against its source region rather than from memory, and reuse persisted canonical values for repeated workflows. After this plan lands, any transcription-shaped task (forms, invoices, summaries, records) has a loadable skill that produces a dedupe-plus-verify receipt, and the next corrections-mining pass can measure the correction class against the skill's own recorded acceptance.

- The skill is the small verification skill the origin's disposition anticipated: the checklist duties live in a loadable, triggerable surface rather than one project's conventions, because the witnessed corrections cluster in personal-admin workflows that no existing skill covers.
- The receipt gives the correction-mining lane a concrete artifact shape to sample, and the canonical-values convention gives repeated workflows a place to stop re-deriving the same facts.
- The skill carries no new mechanical gates: it is a duty-and-receipt surface, and its acceptance is measured by the follow-through metrics the origin records (zero new duplicate-entry or wrong-field corrections).

## Assumptions

- assume the shape is a small skill with an embedded checklist rather than a bare checklist in one project's docs; basis: the origin's own growth path ("candidate to later grow into a small verification skill if the checklist proves stable") plus the witnessed stability evidence (the correction class recurred across two months and two repository families, 2026-07-17 through 2026-09-19), which is the proof of stability the growth path asked for, and the skill registry is the cross-project home the skill guidelines assign to workflow logic that travels.
- assume the dedupe key defaults to amount plus date plus merchant (or the workflow's equivalent identifying fields) rather than a stricter or looser key; basis: the verbatim duplicate-invoice correction ("these 2 invoices are the same 2026-09-10_bcp_dd_proof_46.82_a and b") shows source-identical entries sharing exactly those fields, and a workflow-specific equivalent-fields note keeps the key honest where merchants do not exist.
- assume canonical persistence lands as a facts-document section convention (Configuration from facts keys, per the skill guidelines) rather than a new storage format; basis: the repo guideline externalizes environment-specific values to a facts document, and the personal-finance and medical-data workflows already keep facts documents.
- assume the behavioral acceptance (a sample re-run receipt and zero new corrections in the next mining pass) is recorded as the skill's own acceptance section and measured by the follow-through friction-audit lane, not by this plan's validation commands; basis: the plan's validation is repository-verifiable structure, while the behavioral witness needs a live transcription task and the next corrections-mining pass.

Decision points requiring a grill: shape = small skill with embedded checklist over a bare checklist; source: the origin's stated growth path plus the two-month cross-repository recurrence as the stability evidence, 2026-09-28, Assumptions; dedupe key = amount+date+merchant with an equivalent-fields adaptation note over a universal key; source: the verbatim duplicate-invoice correction naming exactly those fields, 2026-09-28, Task 1; canonical persistence = facts-document section convention over a new storage format; source: the skill guidelines' facts-externalization rule, 2026-09-28, Task 1

## Gist & Examples

TLDR: one new skill makes every transcription into a three-step cross-check (dedupe on the identifying key, re-read each field from its source region at write time, reuse persisted canonical values) and requires a receipt listing what was deduped, what was verified, and what was reused, because eight witnessed corrections in two months came from writing extracted values from memory.

**Before (today).** Transcription-shaped tasks write extracted values straight into forms and summaries; the witnessed corrections are exactly the failure modes that follow: the same invoice listed twice, a country and id filled twice, a name written where the date belongs, an amount carried from a neighboring row ("sorry, not 37, the one of 32.9"). Personal-admin repos run 7.5 to 10.3 percent correction rates against the skill repo's 4.4 to 4.7 percent, and no loadable surface carries a counter-duty.

**After (this plan).** `agents/skills/transcription-cross-check/SKILL.md` loads for transcription into forms, invoices, summaries, or records and imposes the three duties in order: (1) dedupe the source entries on the amount+date+merchant key (or the workflow's equivalent identifying fields) and never write two entries with one key; (2) before writing each field, re-read its source region and copy from the re-read bytes, never from memory of the source; (3) for repeated workflows, copy canonical values (names, ids, addresses, recurring amounts) from the facts document's canonical-values section instead of re-deriving them, and extend that section when a new canonical value stabilizes. The run ends with a receipt: entries deduped (with their keys), fields verified (per-field, with exceptions flagged), and canonical values reused versus derived. Example: the duplicate-invoice task re-run under the skill dedupes the two identical entries on the shared amount-date-proof key, re-reads each invoice's amount from its source line before writing, and reports both in the receipt.

**Edge cases.** A near-duplicate (same key, a differing field) is not silently merged: the receipt flags it and the write stops for that entry rather than guessing which field is right. A workflow with no facts document degrades gracefully: duties one and two still apply, and the receipt notes canonical persistence as unavailable. The skill is tool-agnostic (it names no agent, product, or interface), carries no personal paths or project names, and its validation is structural; the behavioral acceptance lives in the skill's acceptance section for the friction-audit lane to measure.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the three duties are stated as enforceable imperatives with the receipt as the observable output; the near-duplicate stop and the no-facts-document degradation are pinned.
- consistency: the skill follows the registry's house rules (frontmatter with trigger phrases, Integration Points section, Configuration from facts keys, LICENSE.txt present, README catalog row whose path matches the file).
- compatibility: no existing skill or script is modified; the friction-audit lane's measurement habit continues unchanged.

**Done when:**
- The skill directory exists with SKILL.md and LICENSE.txt (MIT, byte-identical copyright form to the plans skill's license).
- The README catalog carries the skill row with the correct path.
- All Validation Commands below exit 0.

**Ship when:**
- None as a release gate; all criteria are repository-verifiable, and the behavioral acceptance is recorded for the follow-through lane.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Tests:**
- None (the deliverable is prose skill structure; the validation block below is the mechanical witness)

**Production code:**
- `agents/skills/transcription-cross-check/SKILL.md` *(new; the whole file)*
- `agents/skills/transcription-cross-check/LICENSE.txt` *(new; the whole file)*
- `README.md` *(only the new catalog row; every other row and section is frozen)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Any existing skill, script, or guard; reason: this plan adds one skill and one catalog row; the correction class's measurement tooling already exists and is not touched.
- The facts documents of any project; reason: the skill defines the section convention; populating a project's facts document belongs to that project's workflows.

## Validation Commands

Stage note: the authoring-time records this plan requires are recorded here: the pre-round structural gate ran clean before round 1 (pre-round exit 0), the RED-today executions ran against current bytes with measured outcomes (G1, G1b, and G2 RED-today: the skill directory, both files, and the catalog row are absent today, and G2's count grep reads 0 against the required 1), and the mechanical audit (pinned spans once each, bash -n over this block) ran before round 1. Round 1 folded four non-blocking findings into these bytes: G1b now enforces byte-identity with the plans license template (its fallback grep passed a non-identical MIT file), the G3 LICENSE.txt arm was removed (the em-dash scanner's file mode skips non-prose paths, so the arm was a no-op), G4 adds the repo-mandated public hygiene scan, and the driving-force tag moved into the closed taxonomy.

```bash
# G1: the skill file exists and carries the three duties, the receipt, and the
# house sections at their pinned anchors.
test -f agents/skills/transcription-cross-check/SKILL.md || { echo "G1 fail: SKILL.md missing"; exit 1; }
grep -qF "amount+date+merchant" agents/skills/transcription-cross-check/SKILL.md || { echo "G1 fail: dedupe key missing"; exit 1; }
grep -qF "re-read" agents/skills/transcription-cross-check/SKILL.md && grep -qF "source region" agents/skills/transcription-cross-check/SKILL.md || { echo "G1 fail: source-region verify duty missing"; exit 1; }
grep -qF "canonical" agents/skills/transcription-cross-check/SKILL.md || { echo "G1 fail: canonical values duty missing"; exit 1; }
grep -qF "## Integration Points" agents/skills/transcription-cross-check/SKILL.md || { echo "G1 fail: integration points missing"; exit 1; }
grep -qF "## Configuration (from facts document)" agents/skills/transcription-cross-check/SKILL.md || { echo "G1 fail: configuration section missing"; exit 1; }
grep -qF "## Acceptance" agents/skills/transcription-cross-check/SKILL.md || { echo "G1 fail: acceptance section missing"; exit 1; }
grep -qiE "claude|codex|cursor|zcode|opencode|copilot|gemini" agents/skills/transcription-cross-check/SKILL.md && { echo "G1 fail: tool-specific token present"; exit 1; } || true

# G1b: the license exists and is byte-identical to the plans skill's template
# (the task says copied byte-identical, so the gate enforces exactly that).
test -f agents/skills/transcription-cross-check/LICENSE.txt || { echo "G1b fail: LICENSE.txt missing"; exit 1; }
diff agents/skills/plans/LICENSE.txt agents/skills/transcription-cross-check/LICENSE.txt >/dev/null || { echo "G1b fail: license differs from the plans template"; exit 1; }

# G2: the README catalog row exists with the correct path, and the row count
# for the skill name is exactly one.
grep -qF "\`transcription-cross-check\` | \`agents/skills/transcription-cross-check/SKILL.md\`" README.md || { echo "G2 fail: catalog row missing or path wrong"; exit 1; }
test "$(grep -cF 'transcription-cross-check' README.md)" -eq 1 || { echo "G2 fail: catalog name count not one"; exit 1; }

# G3: SKILL.md is whole-file em-dash clean (the scanner's file mode covers
# prose files; the license is a fixed non-prose template and is not scanned).
bash scripts/check-no-em-dash.sh file agents/skills/transcription-cross-check/SKILL.md

# G4: the repo-mandated public hygiene scan passes (no hook runs it for a
# new-skill change class, so the validation block carries it).
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh >/dev/null 2>&1 || { echo "G4 fail: hygiene scan nonzero"; exit 1; }
```

### Task 1: the transcription-cross-check skill

Files:
- `agents/skills/transcription-cross-check/SKILL.md` *(new)*
- `agents/skills/transcription-cross-check/LICENSE.txt` *(new)*

- [ ] Create the directory with `LICENSE.txt` copied byte-identical from `agents/skills/plans/LICENSE.txt` [class: IMPLEMENTATION_REQUIRED]
- [ ] Write `SKILL.md` with YAML frontmatter (`name: transcription-cross-check` and a description with trigger phrases for transcription into forms, invoices, summaries, and records) and a body carrying, in order: a purpose paragraph naming the witnessed correction class in general terms (field swaps, double-fills, duplicate entries, wrong amounts; no personal data, no project names); the three duties as enforceable imperatives (dedupe on the amount+date+merchant key with an equivalent-identifying-fields adaptation note, verify each written field by re-reading its source region at write time rather than writing from memory, copy canonical values from the facts document's canonical-values section for repeated workflows and extend the section when a value stabilizes); the receipt requirement (entries deduped with keys, fields verified with exceptions flagged, canonical values reused versus derived, near-duplicates flagged and their writes stopped); the near-duplicate stop rule and the no-facts-document degradation; a `## Integration Points` section stating honestly that no first-party skill consumes it yet and the friction-audit lane is the measuring consumer; a `## Configuration (from facts document)` section (facts document path key, canonical-values section name key, fallback defaults: duties one and two apply without configuration); and an `## Acceptance` section recording the origin's two behavioral witnesses (a sample re-run produces the receipt; zero new duplicate-entry or wrong-field corrections in the next corrections-mining pass) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G1's structure greps and the tool-token negative → expect all found and the negative clean [class: REPOSITORY_TEST]
- [ ] Commit: `skills: add transcription-cross-check skill for data-entry verification` [class: IMPLEMENTATION_REQUIRED]

### Task 2: README catalog row

Files:
- `README.md`

- [ ] Add one catalog row for `transcription-cross-check` with the path `agents/skills/transcription-cross-check/SKILL.md`, a one-line purpose (cross-check duty for transcription into forms, invoices, summaries, and records: dedupe, verify from source, canonical values, receipt), and a notes cell carrying the receipt requirement and the acceptance follow-through (never a second catalog entry for the same name) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run G2's two greps → expect found and count exactly one [class: REPOSITORY_TEST]
- [ ] Commit: `readme: catalog the transcription-cross-check skill` [class: IMPLEMENTATION_REQUIRED]

### Task 3: final validation

- [ ] Run the full Validation Commands block from the repo root → expect every gate green; record the output in the task log [class: REPOSITORY_TEST]

## Origins dispositions

- `docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md` - folded into this plan at execution (main 0ce0c3f3: skill + catalog row landed, all validation gates green, exec review r1 zero blocking); origin file deleted.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-19-transcription-cross-check-before-write.md` was deliberately folded into this plan and its per-item file deleted at execution (main 0ce0c3f3). The behavioral acceptance (zero new duplicate-entry or wrong-field corrections in the next corrections-mining pass) is recorded in the skill's `## Acceptance` section and measured by the follow-through friction-audit lane.
