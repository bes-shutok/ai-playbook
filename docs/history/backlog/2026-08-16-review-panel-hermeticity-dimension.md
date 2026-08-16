# Backlog: Add a hermeticity dimension to the review panel (plans + code review)

Status: backlog idea (pre-plan; promote via the `plans` skill when scheduled).
Workflow: when the implementing plan completes, move this file to `docs/history/backlog/completed/`.

Scope: this skill repo is **project-agnostic**. The defect CLASS and the skill changes below are
generic; project specifics live only in the case-study pointer at the end.

## Problem (generic)

Review panels and review loops can repeatedly approve test suites that are
**environment-dependent**: tests inherit ambient inputs from the developer's environment:
env vars, network reachability, cwd-relative paths, gitignored local files, clock/timezone,
locale, and therefore behave differently on the reviewing agent's machine than on the
developer's machine. "Suite green in the review environment" is silently mistaken for
"tests are hermetic". The failure mode has three costly shapes:

1. live external calls during tests (quota burn, flakiness, side effects),
2. reads of local personal/uncommitted data (privacy, non-reproducibility on fresh clones),
3. order-of-seconds stalls per affected test (developer-time loss, misdiagnosed as perf).

## Root causes (why review rounds miss it)

1. **No hermeticity charter anywhere in the panel.** The testing worker checks coverage,
   assertions, given/expects quality, right-layer placement, never "what ambient inputs can
   this test inherit?" No other worker owns the question either.
2. **Guards and reviews only ever run in the review environment.** A runtime guard that
   passes where the offending branch never executes (e.g. the gating env var is absent there)
   proves nothing; opt-in guards compound this because nobody runs them in the "clean" env.
3. **Narrow fixes without generalization.** When an instance IS caught (say, a personal-data
   path leak), the fix often addresses the instance (that path, that glob) without a
   `generalize` pass extracting the principle ("tests must not branch on ambient developer
   state"), so sibling defects (other env vars, network) survive later rounds.
4. **Diff-scoped review misses cross-age interactions.** A deliberate, previously-reviewed
   ambient-input gate in production code (env var enabling an optional live integration) plus
   individually-reasonable new tests that drive the entry point together produce the defect;
   neither side is in the diff's blame at once, so no reviewer re-audits the entry point's
  full ambient surface against the new tests' assumptions.

## Proposed changes (in this repo's skills)

1. **`review-panel-selection.md`**, extend the **testing worker** charter with a hermeticity lens:
   for every new/changed test (code review) or test-bearing plan task (plan review):
   - enumerate ambient inputs reachable from the code under test: `grep -rn "getenv\|environ"`
     over the call graph the test drives; network clients (`urlopen`, `requests`, `httpx`,
     socket use); cwd-relative and gitignored/uncommitted paths; clock/TZ/locale dependencies;
   - verify each is pinned (fixture), patched (seam), or injected (parameter), and name the
     mechanism in the review output;
   - flag any test driving an orchestration entry point (main/CLI) without explicit
     environment pinning.
2. **`review-agents/` quality + documentation checklists**, add the same enumeration as a
   checklist item so non-testing workers can raise it when they touch adjacent code.
3. **`severity-calibration.md`**, environment-dependent tests that can reach live services or
   personal data are at least **Medium** (side effects, flakiness, privacy), blocking when they
   can hit paid APIs or leak personal data.
4. **Generalize-on-fix hook** (review-loop / receiving-code-review): when a finding is accepted
   and fixed, the loop prompts a `generalize` pass to extract the principle family, prevents
   the narrow-fix recurrence of root cause 3.
5. **Canary validation** (acceptance test for this change): plant a deliberately
   hermeticity-violating plan fixture (a task whose test calls an entry point reading a
   fictional `X_API_KEY` env var) and verify a fresh panel run flags it.

## Acceptance sketch

- `review-panel-selection.md` testing-worker section carries the hermeticity enumeration questions.
- Canary plan review flags the planted violation as Medium+ with the ambient input named.
- A retro check against the case-study repo's review artifacts shows the questions would have
  caught the incident at plan-review time.

## Case study (evidence pointer)

Observed 2026-08-16 in the owner's local tax-reporting repo: tests calling an orchestration
entry point inherited a shell-exported API-key env var, causing live third-party API fetches +
reads of a gitignored personal registry, ~9s/test, invisible across five review rounds because
the reviewing agent's shell lacked the var. Full write-up: that repo's
`docs/history/plans/2026-08-16-test-hermeticity-guards.md` (+ r1–r4 review artifacts) and its
lessons corpus entry. The repo-side guards (env-pin fixture, socket guard, always-on audit-hook
path guard) are the instance fix; THIS item makes the review process catch the class.
