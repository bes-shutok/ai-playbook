# Plan: Align the Maintenance Pins with Their Current Sources

Backlog origin: `docs/history/backlog/2026-10-26-adhoc-global-pins-false-positive.md`
Driving force: efficiency + code-quality
Plan review record: the staging series `.ai-playbook/reviews/2026-10-26-plan-review-maintenance-pin-current-main-baseline-red-r*.md` (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: `docs/tmp/authoring-claims/maintenance-pin-current-main-baseline-red.md` (session `01a173fd-e065-7d41-a91d-8752a79627af`)

## Terms

- **Authoring contract pins:** the existing `authoring stand-down gate span` and `authoring payload re-verification gate` assertions.
- **Prompt-log receipt pin:** the existing `EXEC-PROMPTS receipt delta named in the log header` assertion, evaluated against only the newest `EXEC-PROMPTS-PRUNE:` row. Supported forms are a landing phrase, a direct commit hash optionally followed by a descriptive repair suffix, or a supersession cleanup.
- **Current sources:** the authoring checks in `agents/skills/maintenance/template-authoring.md` and the current receipt rows in `docs/history/backlog/EXEC-PROMPTS.md`.

## Why

The pins suite still expects three phrases that no longer match their current sources: two authoring checks changed when the contract moved and was rewritten, and the prompt-log receipt wording changed with the current log entries. These failures block unrelated reviewed work even though the reviewed change did not touch the pins or their sources.

## Gist & Examples

TLDR: Align the three stale assertions with the current authoring and prompt-log receipt text, so the existing blocker detects drift without rejecting a healthy tree.

**Before:** current `main` reports `PIN FAIL: authoring stand-down gate span`; correcting it exposes `authoring payload re-verification gate`, and correcting both exposes `EXEC-PROMPTS receipt delta named in the log header`. Each expected phrase is absent from its current source.
**After:** all three assertions match current source fragments. The full suite passes on a healthy tree, and each pin reports its named failure when its fragment disappears.

## Outcome

The existing maintenance pins suite passes on current source while continuing to block a genuine mismatch in any of the three corrected pins.

- A healthy current tree no longer inherits the three stale pin failures.
- The newest prompt-log receipt passes in each supported form, while an unknown or text-only repair form and a missing expected authoring fragment produce their named pin failures.

Gate delta: no gate, check, fence, refusal class, or review duty is added or removed; the existing suite remains blocking, with three expected phrases corrected to their sources.

## Assumptions

- assume the authoring template and current EXEC-PROMPTS receipt rows are authoritative and the three pins should match them; basis: the current source text and each pin's source operand.
- assume correcting the three stale expectations is simpler than adding changed-surface landing exceptions; basis: the bounded current-main inventory found exactly two outdated authoring literals and one outdated prompt-log receipt literal, and the disposable copy passes after those three corrections.
- assume the October 15 stale-worktree cleanup remains open outside this plan; basis: its backlog row includes a separate reviewed landing and branch/worktree cleanup not required to repair the current-main pin.
- Decision receipt: expand the frozen one-pin scope to the three stale assertions required for a green full-suite run, preserving the blocking suite; source: user approval after the bounded current-main inventory found only these three failures; implementation log and disposable-copy suite output; 2026-10-26; affected sections: Terms, Outcome, and Task 1.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: all three pin needles match distinctive fragments in their current source files.
- Regression detection: each named pin continues to fail when its expected fragment is absent; newest-row probes pass for every observed receipt form and reject unknown or text-only repair forms.
- Scope: no landing exception or new machinery is introduced.

**Done when:** the full maintenance pins suite passes on current source, newest-row probes pass for the landing phrase, bare hash, hash with each recorded repair suffix, and supersession cleanup, while unknown and text-only repair forms fail with the named pin; missing authoring fragments also fail, and hygiene checks pass.

**Ship when:** none; evidence owner: repository author; closure condition: the local validation commands pass.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Checker and regression test:**
- `scripts/check_maintenance_pins.sh` (Task 1)

**Plan-related extension:** findings may extend to files causally required to correct these three pins or preserve the suite behavior. Weak or speculative links are out of scope.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/SKILL.md`; the ad-hoc landing policy is unchanged.
- `docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery.md`; that row has separate landing and cleanup acceptance and remains independently open.
- `agents/skills/maintenance/template-authoring.md` and `docs/history/backlog/EXEC-PROMPTS.md`; their current text is the source being pinned and is not changed by this plan.
- other pins and landing gates; unrelated checks remain unchanged.

## Validation Commands

```bash
env -u PINS_RECORDED_RED_AS_OF -u PINS_RECORDED_RED_REGISTER TMPDIR=/tmp bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh --files scripts/check_maintenance_pins.sh
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/check_maintenance_pins.sh
```

### Task 1: Re-key the three stale maintenance pins

Execution estimate: 1.0h

Context surface: the plan's Terms and this task.

Files:
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `pin` in `scripts/check_maintenance_pins.sh`

- [x] Given the current sources, both authoring assertions and the prompt-log receipt assertion match distinctive source fragments and the full pins suite passes. [class: IMPLEMENTATION_REQUIRED]
- [x] Given any expected source fragment is absent in its own disposable Git copy, the suite reports the named pin failure; newest-row probes pass for each observed receipt form and reject unknown and text-only repair forms. [class: REPOSITORY_TEST]
- [x] Correct the nearby provenance comments to identify each current owning source and the reason its assertion checks that span. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the validation commands; the pins suite passes and the source hygiene checks are clean. [class: REPOSITORY_TEST]
- [x] Commit the repair as `fix: align maintenance and prompt-log pins with current sources`. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-26-adhoc-global-pins-false-positive.md` was the promoted origin. Its status was flipped to covered before the archive transition, and the origin file is deleted in this completion pass. The stale maintenance-pin expectations were aligned to current sources and the existing suite remains blocking.
- `docs/history/backlog/2026-10-15-codex-stale-worktree-pins-landing-recovery.md` was listed for context but remains open; its separate landing and worktree-cleanup acceptance was outside this plan.
