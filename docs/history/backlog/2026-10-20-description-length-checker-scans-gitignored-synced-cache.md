# Backlog: the description-length checker scans the gitignored synced skills cache and warns at every landing

- **Filed:** 2026-10-20, all-skills loader review after the execute-plan description fix (learn Step 1.8 capture)
- **Status:** covered (docs/history/plans/2026-10-21-description-length-checker-scope-and-admission.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed checker scope defect (recurring landing noise over files the repo does not author)
- **Class:** fix-class
- **Driving force:** simplicity (a warning-posture gate whose output is mostly noise about foreign files trains readers to skip it; lesson 135 names the cost of an unread warning)
- **Skill/step:** `scripts/check_skill_description_length.py` (file selection: `root.rglob("SKILL.md")`); `agents/skills/done/SKILL.md` Step 3 landing sweep, `description-length` gate (`scripts/done_sweep_gates_lib.py`)
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog text for `synced`, `gitignored path`, `check_skill_description_length`, `rglob`; the only hits are `2026-10-20-description-length-gate-true-catch-unledgered.md` (the same gate's posture, a sibling by mechanism) and unrelated em-dash scan notes; no open row owns the checker's file selection.
- **Cluster:** docs/history/backlog/2026-10-20-description-length-gate-true-catch-unledgered.md

- **Cluster:** docs/history/backlog/2026-10-18-done-plan-readiness-child-tool-error.md (shared mechanism: same runner or gate family; investigate 2026-10-20 roster)
## Problem

The checker selects files with a bare recursive glob over the skills root, so it also visits `agents/skills/synced/`, a gitignored directory that an external skills sync tool writes (a cache of third-party skills with its own manifest). Two of those cached files sit in the 950-character warning band (`pptx` 960, `xlsx` 952), so every landing sweep prints two description-length warnings about files this repository neither tracks nor authors. The runtime does not load them either: skills are discovered directly under each root, and these sit two levels down (lesson 138).

Hand-editing the cached copies is not a fix (the next sync overwrites them, and the Vendored Asset Sync Rules exclude autonomously managed trees), so the warnings are permanent noise on the one gate that should have been read on 2026-10-19 (the execute-plan over-cap landing).

## Expected

The checker reports only the repo-authored skill set: tracked `SKILL.md` files under the skills root. A gitignored or externally synced subtree produces no output.

## Suggested fix

Smallest form first:

1. Select files from `git ls-files -- agents/skills` (filtered to `SKILL.md`) when the root is inside a git checkout, falling back to the current glob otherwise; keep the explicit-paths and `--selftest` modes unchanged.
2. Add one selftest case: a nested gitignored `SKILL.md` over the cap produces no finding.

Rejected: trimming the cached descriptions (foreign files, overwritten on sync); deleting `agents/skills/synced/` (the external tool's cache, not repo state); raising the warning band above 962 (hides the early signal the band exists for); skipping by directory name `synced` (encodes one tool's layout; the tracked-set rule is the general form).
