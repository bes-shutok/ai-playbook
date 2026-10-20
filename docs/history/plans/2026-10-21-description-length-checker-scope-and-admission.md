# Plan: Description Length Checker Scope and Admission Record

Backlog origin: docs/history/backlog/2026-10-20-description-length-checker-scans-gitignored-synced-cache.md
Related open backlog item: docs/history/backlog/2026-10-20-description-length-gate-true-catch-unledgered.md
Driving force: code-quality
Plan review record: .ai-playbook/reviews/2026-10-21-plan-review-description-length-checker-scope-and-admission-r*.md
Execution budget: 1.5h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-20-description-length-gate-true-catch-unledgered.md (session codex-maintenance-auth-20261021-0316-d2aceb2e)

## Terms

- **Tracked skill set**: skill description files under `agents/skills/` listed by Git for the current checkout, including a tracked file that matches an ignore rule.
- **Description-length gate**: the existing checker and landing-sweep gate that report folded descriptions over 1024 characters and warn above 950.
- **Warning posture**: a non-zero result is reported without refusing the landing.
- **Sunset commitment**: the review date and removal or re-demotion criteria recorded in the active machinery-registry entry; it is moved to the removals array only after the governed path is actually removed.

## Why

The checker recursively scans a gitignored synced cache, so it reports files this repository does not own. The gate also produced a real catch before a skill disappeared from a runtime, but warning posture allowed landings to continue and the firing was not recorded. The Machinery admission protocol prevents promoting the gate without a blocker retirement or explicit operator approval. Neither is evidenced for this authoring run, so this plan narrows its resolved outcome to scan ownership and admission evidence. The related true-catch backlog item remains open; this plan does not claim to resolve its requested landing-blocking behavior.

## Gist & Examples

TLDR: scan tracked skills, record the gate's admission and sunset criteria, and explicitly defer its requested blocking posture, driven by code-quality.

Before: the default scan descends into `agents/skills/synced/` and prints warnings for gitignored external files. A tracked description over 1024 characters is still detected, but the landing sweep reports the failure as a warning.

After: the default scan checks only tracked skill files inside a checkout, so the synced cache is silent while an over-cap tracked skill remains reported. Explicit paths and the selftest mode keep their current behavior. The gate remains warning-only. The related true-catch backlog item's blocking-posture request remains open for a separately reviewed decision that retires or demotes an existing blocker, or receives explicit operator approval for net growth; this plan does not satisfy that request.

## Outcome

The checker reports only repo-owned skill descriptions by default and its active registry entry carries reviewable admission and sunset evidence. Keep the cache-scope origin file in the backlog while this plan is active, marking it covered by this plan at landing; delete it with its disposition when implementation completes. Keep the related true-catch backlog item open for separately authorized blocking-posture and firing-capture work.

- An over-cap tracked description remains named with its measured length.
- Nested ignored and non-ignored, untracked over-cap skill descriptions are excluded by the default scan inside a checkout and do not appear in checker or gate output; tracked files remain in scope regardless of ignore status.
- Outside a checkout, the default scan retains recursive selection and reports an over-cap skill description.
- The checker registry entry identifies the true catch, expected frequency, false-positive cost, and review date.

Gate delta: no new gate, validator, lock, fence, protocol layer, or state field; default checker scope narrows to tracked files; the existing warning posture remains. No existing blocker is retired because the machinery registry has no witness-free candidate. Do not promote this gate in this plan. Keep the cache-scope origin file in the backlog while the plan remains active, marking it covered by this plan at landing and deleting it with its disposition when implementation completes. Keep the related true-catch backlog item open for separately authorized blocking-posture and firing-capture work.

## Assumptions

- assume the 1024-character cap and 950-character warning threshold remain unchanged; basis: the existing checker and the completed gate plan.
- assume tracked-file selection applies only to the default scan inside a checkout; basis: both backlog origins preserve explicit-path behavior and specify a recursive fallback outside a checkout.
- assume the blocker-promotion arm is deferred because no safe retirement candidate or explicit net-growth approval exists; basis: the Machinery admission protocol and the current registry evidence. This is an explicit partial disposition, not completion of the origin's blocking-posture outcome.
- Phase 1 posture disposition: no promotion is authorized in this run because no witness-supported retirement candidate or explicit net-growth approval is present. This records the authorization state under the Machinery admission rule, not an asserted user refusal. Keep the blocking-posture origin open for a later decision that names a retirement candidate or grants explicit net-growth approval.

Decision points requiring a grill: none remain. The blocker-promotion question stays open for the separately authorized follow-up; this plan's scan-scope and admission-record tasks are executable without it.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the default scan includes tracked `SKILL.md` files, including tracked paths that match ignore rules, and excludes untracked files whether ignored or not.
- signal quality: over-cap tracked files remain findings, including tracked paths that match ignore rules; untracked ignored nested files produce no finding.
- maintainability: explicit-path and `--selftest` modes retain their current contracts.

**Done when:**
- the checker selftest and landing-sweep tests demonstrate that tracked over-cap descriptions are reported, including tracked paths that match ignore rules; untracked ignored and non-ignored descriptions are absent from the default in-checkout scan; explicit-directory mode still reports untracked descriptions; and the outside-checkout recursive fallback reports over-cap descriptions.
- the active registry entry contains the admission fields and sunset commitment specified below, `machinery_inventory.py --check` accepts its generic registry structure, and no removals-array row names a still-tracked path.
- the cache-scope origin remains in the backlog while this plan is active and is deleted with its disposition at implementation completion; the related true-catch backlog item remains open for the unresolved blocking-posture and firing-capture work.

**Ship when:**
- the plan is executed and lands through the repository's standard review and closeout gates.

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/check_skill_description_length.py`
- `scripts/machinery_registry.json`

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py` and `agents/skills/done/SKILL.md`; the gate keeps its warning posture in this plan.
- Any existing blocker, registry row, or landing gate not named above; no blocker retirement was justified by the current evidence.

## Validation Commands

```bash
python3 scripts/check_skill_description_length.py --selftest
python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
python3 scripts/machinery_inventory.py --check
```

### Task 1: Select tracked skills for the default scan

Files:
- `scripts/check_skill_description_length.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `check_tree` in `scripts/check_skill_description_length.py`, which selects and measures skill files.
- `gate_description_length` in `scripts/done_sweep_gates_lib.py`, which invokes the checker from the repository root.

Evidence:
- The checker currently uses recursive selection; the gitignored synced cache and its false warnings are documented in lesson 138.
- The checker has an embedded `--selftest`; the landing-sweep suite already exercises the description-length gate.

- [ ] The default scan inside a checkout selects only repository-tracked skill descriptions, including tracked files that match ignore rules; an over-cap nested gitignored but untracked file produces no finding. [class: IMPLEMENTATION_REQUIRED]
- [ ] Inside a checkout, an over-cap non-ignored untracked skill description is excluded from the default scan; outside a checkout, the default scan recursively reports an over-cap skill description. [class: IMPLEMENTATION_REQUIRED]
- [ ] An over-cap tracked skill still produces a finding with its path and folded length; explicit-directory mode still reports an untracked over-cap skill description, and `--selftest` retains its existing behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] The checker selftest and landing-sweep tests distinguish tracked over-cap descriptions, including tracked paths that match ignore rules, from untracked ignored and non-ignored descriptions in the default in-checkout scan, and preserve explicit-directory selection and the outside-checkout recursive fallback. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: scope description length scan to tracked skills` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Record admission and sunset evidence

Files:
- `scripts/machinery_registry.json`

Evidence:
- The 2026-10-19 to 2026-10-20 runtime omission is the true catch recorded by the related true-catch backlog item.
- The registry already owns `script:check_skill_description_length.py`; it has no admission fields or removals row for this gate.

Primary class anchors:
- `check_failures` in `scripts/machinery_inventory.py`, which validates active registry entries and removals records.

- [ ] The existing registry entry records the incident, expected frequency, false-positive cost after tracked-set selection, and the 2027-10-20 review date. [class: IMPLEMENTATION_REQUIRED]
- [ ] The active registry entry records re-demotion criteria that require a complete firing census plus no further catches; an empty ledger alone is not evidence of completeness, and if completeness cannot be established, preserve the warning posture and record an operator review. The entry also requires warning posture until a separately authorized blocker-promotion plan exists. [class: IMPLEMENTATION_REQUIRED]
- [ ] The machinery inventory validator accepts the updated active entry; do not add a removals-array row while the checker remains tracked. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: record description length gate admission criteria` [class: IMPLEMENTATION_REQUIRED]
