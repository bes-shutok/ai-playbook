# Plan: origin-independent eligibility regression witness

Backlog origin: docs/history/backlog/2026-10-06-investigate-origin-independent-eligibility.md
Driving force: code-quality
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-investigate-origin-independent-eligibility-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- pins suite: `scripts/check_maintenance_pins.sh`, the mechanical grep-pin suite for the maintenance skill and its cross-skill mirrors; outcome contract per `scripts/OUTCOME_CONTRACT.md`.
- eligibility contract: the rule that investigate eligibility never depends on where a defect's evidence originated; the only sanctioned skips are duplicate representation (an existing log entry's `Origins:` line) and plans-root coverage (a covering plan file).
- privacy emission contract: the rule that emitted log entries and cluster annotations omit personal data and foreign project identifiers, keeping repo-relative vocabulary only.
- anti-pattern pin: a pin that fails when a banned literal appears anywhere in a pinned file.
- presence pin: a pin that fails when a pinned contract sentence is missing (or, where count-gated, no longer exactly once) from a pinned file; the suite header's "guards an invariant" vocabulary.
- fixture fail-arm: the section's built-in synthetic-fixture selftest that proves the pins detect a seeded defect; failure of the fail-arm fails the suite (the suite header's "witnessed fail arm" / "per-section fixture seam").
- Detection scope: the witness bounds detection to deletion of pinned sentences, alteration that empties a pinned needle, and the frozen historical exclusion literals; a novel-worded origin exclusion that deletes no pinned sentence is outside the witness (accepted scope, stated here).

## Why

Commit 4a9ddba4 removed an origin-based ownership skip from the investigate and maintenance skills after it stopped investigation of a real defect in this repository's shared workflow. The correction is prose only, so a future edit could reintroduce an origin gate silently; no mechanical check would notice.

## Outcome

The landed eligibility and privacy emission contract is guarded by pins that fail the suite if an origin-based exclusion returns in either skill.

- Removing any landed eligibility or redaction sentence from `agents/skills/investigate/SKILL.md` or the monitor's matching skip rule from `agents/skills/maintenance/SKILL.md` fails `scripts/check_maintenance_pins.sh`.
- Reintroducing any of the three historical exclusion literals (`foreign-origin`, `ownership skip`, `never grouped, investigated, or dispatched`) into the file that bans it fails the suite (three banned literals across five file-scoped absence checks; the third literal is investigate-only).
- A synthetic fixture with an injected exclusion sentence is proven to trip the section's pins (the witnessed fail arm).

Gate delta: growth of an existing checked-condition set only: the pins suite gains one section (ten presence pins, three banned literals across five file-scoped absence checks, one section-local existence check, one fixture fail-arm); no new refusal class, gate, fence, protocol layer, or state field; paying witness: the completed integrity failure the origin row records (the origin gate stopped a qualifying investigation until operator correction 4a9ddba4); removals: none.

## Assumptions

- The witness lives in `scripts/check_maintenance_pins.sh`, not a new checker script; basis: the suite header already owns cross-skill pins (execute-plan and plans mirrors), `scripts/check_investigate_entries.py` validates log entries not skill prose, and the maintenance skill's Machinery regrowth guard consult surface (scripts/machinery_inventory.py --check, run read-only at authoring time) reports unregistered-script regrowth.
- Whole-file anti-pattern scans for `foreign-origin`, `ownership skip`, and `never grouped, investigated, or dispatched` over the two skill files are safe; basis: zero occurrences of each in both files at authoring time (post-4a9ddba4).
- The fail-arm follows the suite's per-section fixture seam (mktemp fixture, section-local check, selftest failure fails the suite); basis: the live-vs-archive section's existing built-in selftest shape.
- Both skill files' prose is retained byte-unchanged; basis: the dispatching log entry's prompt says "retain it and add the smallest durable check".
- `scripts/check_investigate_entries.py` stays untouched; basis: it validates entry structure (rejected alternatives, evidence citations), a different contract.

Decision points requiring a grill: none remain: the dispatching PLAN-PROMPTS entry is the confirmed design (operator-directed investigate pass with rejected alternatives recorded; live operator directive 2026-10-07); the witness-home choice resolved on repo evidence above.

## Standing constraints

- Repo-relative paths only; no machine-specific absolute paths in pinned or pinning content.
- The pins suite's outcome contract holds: one final `OUTCOME:` line per run, exit 0 pass / exit 1 fail / exit 3 tool error.

## Gist & Examples

TLDR: pins in the maintenance pins suite now hold the origin-independent eligibility and privacy emission contract across the investigate and maintenance skills, so the exclusion 4a9ddba4 removed cannot silently return; reliability of a corrected boundary.

The suite gains one section that greps the landed contract sentences in both skill files, bans the removed exclusion literals, and proves detection on a synthetic fixture. Example: a future edit that re-adds "a foreign-origin item ... is skipped" to the investigate skill fails the suite with a named pin, the same way a silently reworded lane cap fails today.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every pin needle matches the current tree (`git grep` green); the fixture fail-arm fails exactly when an exclusion literal is injected
- regression value: deleting any pinned sentence from either skill file turns the suite exit non-zero with a named `PIN FAIL` line
- simplicity: one suite section; no new scripts, no new state, no skill-prose edits

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0 with `OUTCOME: pass` on the current tree
- the section's selftest (fixture with injected exclusion) fails the section's pins and the suite reports it; with the injection removed the suite passes
- removing any one pinned needle's sentence from a fixture copy of a skill file fails the corresponding pin

**Ship when:**
- none; repository-verifiable only

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_maintenance_pins.sh` (a new section plus the one mandated clause in the suite header's guarded-invariant inventory comment; existing sections byte-unchanged)

**Tests:**
- the section's built-in fixture fail-arm inside `scripts/check_maintenance_pins.sh` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. The pinned files `agents/skills/investigate/SKILL.md` and `agents/skills/maintenance/SKILL.md` are read-only for this plan; a finding there is in scope only when it shows a pin needle is wrong against the landed bytes.

**Out of scope; reject unless plan-related:**
- `scripts/check_investigate_entries.py`; reason: entry-structure validator, different contract, untouched by design
- any edit to the two skill files' prose; reason: the contract text is retained per the dispatching entry

## Validation Commands

Authoring-time evidence (rule 29 pre-round): the em-dash touched scan and the public-hygiene scan answered pass over the plan bytes; the pre-round structural gate answered `OUTCOME: pass` with zero tolerated classes; the rule 19 RED-today probes ran the pin needles against the two skill files at the base tip with the expected match counts (ten presence needles 1 each including the extended skip-shape span and the Stage 0 redaction sentence, three banned literals 0 each), and the fixture fail-arm property was probed by injecting the exclusion literal into a scratch copy and confirming the needle set discriminates; `bash -n` accepted the extracted Validation Commands block. Round-start state for r1: authoring worktree ai-playbook-wt-ioie, branch authoring/investigate-origin-independent-eligibility, base main c0cb495c.

```bash
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Investigate-side eligibility and privacy pins with fixture fail-arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh` (new section plus the one mandated clause in the suite header's guarded-invariant inventory comment; existing sections byte-unchanged)

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers Done when items 1-3 (suite pass, selftest trip, per-needle failure)

- [x] Presence pins hold on the live tree: `agents/skills/investigate/SKILL.md` contains, one pin each: (a) `Origin repository or organization does not restrict investigation`; (b) ``Skip an origin only when it is already represented by an existing log entry's `Origins:` line or a plans-root plan file`` (the full skip-shape span, so both disjunction arms stay pinned; double-backtick fenced so the rendered span equals the byte span); (c) `origin repository and organization do not affect eligibility`; (d) `origin repository and organization do not exclude the input item or a relevant sibling`; (e) `redact foreign identifiers and personal data`; (f) `keep foreign identifiers, personal data, and details outside this repository out of cluster annotations and emitted entries`; (g) `Keep cluster annotations within this repository's safe, repo-relative vocabulary and omit foreign identifiers or personal data` (the Stage 0 redaction sentence) [class: IMPLEMENTATION_REQUIRED]
- [x] Anti-pattern pins hold: neither `foreign-origin` nor `ownership skip` nor `never grouped, investigated, or dispatched` appears in `agents/skills/investigate/SKILL.md`, checked with the wrap-tolerant flat form (the suite's `expect_absent_flat` / normalized whole-file literal counts, per the p57 Task 5 doctrine comment) so a line-wrapped reintroduction cannot evade the pin [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture fail-arm: a mktemp fixture root carrying byte-copies of BOTH skill files at their repo-relative paths, whose `agents/skills/investigate/SKILL.md` copy carries one injected exclusion sentence (containing `foreign-origin`), fails the section's pin function invoked at function level (never a whole-suite re-invocation, which would die with exit 3 for the wrong reason); the modeled refusal's output is captured and asserted to name the injected literal (no stray PIN FAIL lines in a passing run); the same fixture without the injection passes; cleanup (`rm -rf`) and the OUTCOME composition follow the live-vs-archive selftest exactly; the selftest runs in-suite and a selftest failure fails the suite (per-section fixture seam) [class: REPOSITORY_TEST]

### Task 2: Maintenance-side monitor pins

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_maintenance_pins.sh` (the same new section's second half)

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the monitor-rule pins and the anti-pattern guard on the maintenance file

- [x] Presence pins hold on the live tree: `agents/skills/maintenance/SKILL.md` contains, one pin each, count-gated at exactly 1 occurrence (`grep -oF | wc -l` form, vacuous-canary guard against a future Revisions-ledger quote): (a) `skip any ungrouped open backlog item whose origins intersect an existing log entry's` (the monitor's eligibility rule, Rolling prompt log duties (e)); (b) ``origins intersect an existing log entry's `Origins:` line or a plans-root plan file`` (the duplicate/covered skip shape; double-backtick fenced so the rendered span equals the byte span); (c) `repo-relative paths only` (the emission vocabulary rule, duty (e)) [class: IMPLEMENTATION_REQUIRED]
- [x] Anti-pattern pins hold: neither `foreign-origin` nor `ownership skip` appears in `agents/skills/maintenance/SKILL.md`, checked with the same wrap-tolerant flat form [class: IMPLEMENTATION_REQUIRED]
- [x] The maintenance anti-pattern pins share the Task 1 fixture seam: injecting an exclusion sentence into the fixture's maintenance skill copy trips them [class: REPOSITORY_TEST]
- [x] Section-local existence check: the new section verifies `agents/skills/investigate/SKILL.md` exists at its repo-relative path (mirroring the budget-gate seam's local check) so a missing pinned file fails loudly as missing; the suite's byte-pinned header existence loop stays byte-unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Checkpoint discipline: the section adds NO mid-suite checkpoint (its only exit path is the section-local selftest assertion plus the suite's final gate funnel); the suite header's guarded-invariant inventory comment gains one clause naming the new invariant and stating that the section's fixture fail-arm joins the witnessed-fail-arm family under the same per-section fixture seam; the contract's Batch 2 compatibility-note checkpoint sentence and the suite header's matching comment stay valid in their funnel semantics under the no-new-checkpoint choice (the pre-existing 38-versus-39 count drift those two literals carry against the tree's gate count predates this plan and stays untouched by name); `scripts/OUTCOME_CONTRACT.md` is not edited [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- No user-facing documentation changes. `README.md` catalogs skills, not scripts; the pins suite is internal machinery already covered by the maintenance skill's pins references. No doc-hierarchy surface owns pin inventories.
