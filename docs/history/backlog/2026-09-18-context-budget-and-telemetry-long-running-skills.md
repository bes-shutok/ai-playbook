# Backlog: context budget and telemetry for long-running skills

Status: open
Workflow: backlog
Source: Andrey 2026-09-18: "another issue with maintenance as well as with other long running skills like execute-plan is that the context gets too big which leads to excessive expense in tokens and often missing important details. We should periodically measure context and keep it shorter than 300k. Also we might need to keep track of context size for later analysis."
Severity: Medium (recurring token cost on every long run; fidelity loss, early-phase details dropping out of attention or runtime auto-summarization, has already caused missed-detail rework in long review loops)
Scope: agents/skills/execute-plan/SKILL.md (checkpoint + ladder placement), agents/skills/review-loop/SKILL.md, agents/skills/maintenance/prompt-templates.md (both child blueprints are the long runners; the scheduler turn itself is short), agents/skills/maintenance/zcode.md (runtime primitives), .ai-playbook/facts.md (budget config key)

## Problem

The repository's longest-running flows accumulate context across hours with no
measurement, no budget, and no telemetry:

- An execute-plan run spans Phase 0 setup, one implement worker per task,
  Phase 2 validation, Phase 3 parent-orchestrated review rounds (observed
  loops of r1 through r18 in past runs), Phase 4 archive, and Phase 5, with
  zero context management anywhere in between.
- Maintenance child blueprints gained exactly one mitigation (2026-09-16
  revision): a post-completion compaction step, which runs ONCE at the END and
  therefore benefits only the NEXT scheduled payload, never the run that is
  already long.
- No skill measures context size at any point; nothing records the numbers.
  The runtime's own auto-summarization (when present) is uncontrolled and
  lossy, the "missing important details" symptom, and token expense scales
  with the accumulated transcript on every worker launch and tool round.

Two distinct failure modes, both observed: (1) cost, every re-read, worker
prompt assembly, and orchestrator decision re-carries the whole accumulated
context; (2) fidelity, details fixed early in the run (claim tokens, digest
rules, peer-safety fences) fall out of the working set precisely when the run
is long enough to need them.

## Suggested fix

Policy in the core skills (tool-agnostic), primitives in the runtime overlay,
numbers in gitignored telemetry:

- **Budget config**: a facts key (e.g. `context_budget_tokens = 300000`) with
  the threshold ladder expressed as fractions of it. One knob, one owner.
- **Checkpoints at safe boundaries only**, never mid-task (a compaction
  between a worker claim and its completion risks orphaning driver state;
  execute-plan's machine manifest mitigates but the boundary rule removes the
  exposure): execute-plan, after each worker return, each phase transition,
  each review round; review-loop, each round boundary; maintenance children,
  after each blueprint step block. The scheduler turn itself needs only its
  existing end-of-run compaction.
- **Threshold ladder**: at each checkpoint, measure. Below ~70% of budget:
  log and continue. 70-85%: cheap shedding first (drop superseded round
  payloads, applied diff snapshots, resolved quota chatter, several of these
  drops are already prescribed piecemeal; this consolidates them). Above 85%:
  full compaction via the runtime primitive or the `handoff` skill, with the
  machine manifest / handoff document as the authoritative state to reload.
  The 100% wall is never reached because checkpoints act first.
- **Measurement is runtime-specific**: the overlay names the primitive per
  runtime (session/transcript stats where exposed; otherwise a char-count
  proxy over the transcript file with a pinned chars-to-tokens ratio, e.g.
  ~4 chars/token, clearly labeled as an estimate). The core skill only states
  the policy so other runtimes can comply differently.
- **Telemetry**: append one JSONL record per checkpoint,
  `{ts, skill, run_slug, phase, est_tokens_before, action, est_tokens_after, compactions_to_date}`,
  to a gitignored per-run log beside the existing manifest
  (`{tmp_dir}/execute-plan/<PLAN_SLUG>/context.jsonl`; maintenance children:
  a sibling of the scheduler state file). The format is designed for later
  analysis (token cost per plan family, compaction count vs missed-detail
  incidents) but the analysis itself is out of scope here.
- **Survival of compaction**: the compaction/handoff procedure must pin the
  artifacts that MUST survive (machine manifest `runtime_state.json`, current
  round state, claim tokens, peer-safety fences), this list already exists
  implicitly in the handoff skill; reference it rather than duplicating.

## Acceptance criteria

- Every long-running skill measures context at its named checkpoints and logs
  a record per checkpoint (grep-able, gitignored, per-run).
- A run crossing 85% of the budget performs a documented compaction/handoff at
  a safe boundary and resumes from durable state; no run relies on the
  runtime's silent auto-summarization as its only mechanism.
- The budget is a single facts-backed constant; changing it needs no skill
  edits.
- Post-hoc, a completed run's context.jsonl answers: peak size, compactions
  performed, and tokens spent per phase, without reading the transcript.
