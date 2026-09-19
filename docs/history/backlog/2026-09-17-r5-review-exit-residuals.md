# R5 review-exit residuals: execute-plan integrity quad

Status: open
Origin: Phase 3 review round 5 (clean, zero blocking) of docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md; all findings valid, none fixed because the five-round budget was exhausted and the digest had to stay frozen. Deferred per the backlog-deferral default (ADR-0002).

## Hardening pair (do first)

- CC5-1 / R5-2: `_read_plan_bounded` regular-file gate is check-then-open; a FIFO swapped in inside the window still blocks in `open()`. Harden with `os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)` + `os.fstat` S_ISREG before reading. Reachability: local adversary racing a microsecond window only.
- CC5-2 / R5-1: terminal empty-artifact refusal stops at zero bytes; a whitespace-only (or sectionless checkbox-free) archived plan passes and writes a receipt. Refuse on `not plan_text.strip()`, optionally require at least one `### Task <N>:` heading (mirroring the readiness plan-shape guard).

## Fence/lease-adjacent

- R5-3: reclaim fences `workflow_state: aborted` but not `complete`/`terminal`; a hand-edited manifest could rotate a claim under a completed run. Treat complete/terminal like aborted in the reclaim precondition.

## Test pins

- T5-1: call-site token-argument swap into `_reclaim_evidence_lines` survives the suite (redaction makes envelope lines indistinguishable); pin via injectable evidence-lines parameter or document the residual in the helper docstring.
- T5-2: `test_readiness_refuses_plan_without_task_sections` should also assert `recovery_action == "stop-or-recovery"`.
- T5-3 / DS5-5: delete the tautological `assertNotEqual("seed-old-token", "rotated-new-token")` line in the reclaim pin test.
- T5-4: add a posix-conditional `os.mkfifo` refusal arm (safe: gate refuses before any open) or soften the comment to name the directory as the tested stand-in.
- R5-4: add an exact read-limit boundary pair (1,000,000 accepted / 1,000,001 refused), mirroring the lease-boundary arm pattern.

## Doc precision

- CD5-1: reword the mark_terminal save sentence: the manifest lock does not fence the external archived-plan and commit artifacts; drop or define "best-effort best-order".
- CD5-2: scope the readiness reason-code sentence: contention carries `stale-claim` and plan errors carry `precondition-unverified` as reason codes, with the decision in the `decision` field.
- CD5-3: terminal-path bullet gains "the manifest carries at least one task".
- CD5-4: recovery-action mapping gains `stop-or-recovery` for a plan with zero recognizable task sections.
- CD5-5: interruption table: "Each outcome names exactly one next action; take that one action, then re-classify the state."

## Polish

- DS5-1: strip once inside `_read_plan_bounded` (both call sites identical) and drop call-site `.strip()`s.
- DS5-2: keep the bounded-read policy prose in the helper docstring only; one-line pointers elsewhere.
- DS5-3: strip ephemeral review-round ids (r4 R4-1 style) from code comments; keep self-contained rationale.
- DS5-4: rename `TERMINAL_PLAN_READ_LIMIT` to `PLAN_READ_LIMIT` (both gates share it).
- R5-5: refusal evidence line numbers count Unicode line boundaries (splitlines vs \n); cosmetic.
