# Backlog: plans declare a driving force; Gist opens with a TLDR

Status: open
Workflow: backlog
Source: 2026-09-18 post-mortem of the legacy verdict-grammar deletion plan (Andrey, same day): the plan was partly motivated by a security/fail-closed-integrity concern, which is NOT one of the implementation principles, and that mismatch is exactly what the 2026-09-11 triage parks on, but nothing in the plan declared it, so the mismatch had to be rediscovered by hand. Second observation from the same discussion: the Gist section opens with dense prose; a 1-2 phrase TLDR (what changes + why) was missing.
Severity: Low (process/metadata hygiene that makes triage, pricing, and deferral mechanical)
Scope: agents/skills/plans/SKILL.md (plan template: new metadata line; Gist section: TLDR requirement; Step 1.4 confirmation block), agents/skills/maintenance/prompt-templates.md (authoring blueprint fills both), agents/skills/review-plan/SKILL.md (missing/incoherent declarations are findings). Validator enforcement in scripts/plan_readiness.py is deliberately OUT of scope for the first pass.

## Problem

Two related gaps in the plan document contract:

1. **No declared driving force.** The corpus defines the arbiter,
   `projects/.ai-playbook/agent_workflow_guidelines.md` ("Driving principles
   for design and review until revised: efficiency, token usage, simplicity,
   and code quality, ranked in that order"; code quality never priced at zero,
   amendment 2026-09-12), and the deferred/ triage classes
   ("process-cosmetic, security-accepted, or machinery-growth work with no
   code-quality cost") are defined relative to it. But a plan never DECLARES
   which force drives it. Every consumer (maintenance selection, park triage,
   review pricing, human skim) must infer it from prose. The legacy
   verdict-grammar plan read like a robustness fix while its actual weight was
   hygiene/security-accepted machinery with zero observed defects, the exact
   profile the triage parks, and only a human asking "what is the benefit?"
   surfaced that. A declared force makes the mismatch visible at survey time
   instead of at challenge time.
2. **No TLDR in the Gist.** `## Gist & Examples` opens directly with a dense
   "What changes:" paragraph (the legacy plan's runs ~10 lines before the why
   appears). The section that exists precisely for skimming has no skim layer.
   Andrey's requirement: one or two phrases on top of the Gist saying what the
   plan is supposed to change and why.

## Suggested fix

One metadata block, declared once, consumed everywhere:

- **Driving force line** (near the plan header, beside Backlog origin):
  `Driving force: <tag>` with a closed taxonomy anchored to the existing
  principles: `efficiency` | `token-usage` | `simplicity` | `code-quality` |
  `new-capability` (function that serves none of the four but adds user-visible
  capability) | `external` (user request, incident, or deadline, must cite the
  source). A plan whose force is none of the four driving principles
  (`new-capability`/`external`, or a security-hardening plan with no observed
  defect) carries a one-line justification: why implement it anyway, and why
  park-triage would or would not take it (this mirrors the deferred/README
  classes and the standing scrutiny of Security labels whose exploit path
  reveals no new surface). Compound forces are allowed as primary + secondary,
  ranked.
- **Gist TLDR**: the first line of `## Gist & Examples` becomes
  `TLDR: <what changes>, <why, naming the driving force>.` One or two
  phrases; everything already in the section stays below it.
- **Producers:** the plans skill template gains both (with the taxonomy and the
  justification rule); the Step 1.4 confirmation renders the declared force so
  Andrey confirms it at authoring; the maintenance authoring blueprint fills
  both fields so scheduled authoring children produce them without prompting.
- **Consumers:** review-plan treats a missing TLDR, a missing force line, a
  force that contradicts the plan's actual content (a "simplicity" plan that
  adds machinery), or an unjustified non-principle force as findings; the
  maintenance park-guard item
  (docs/history/backlog/2026-09-18-maintenance-park-guard-externally-gated-plans.md)
  reads the force line as a triage input, coordinate the metadata block so
  plans declare one block, not two separate lines owned by different items.
- **Enforcement:** skill text + review findings only for the first pass. If the
  field proves stable, a later pass may add a plan_readiness schema check;
  do not gate certification on prose fields on day one.
- **Retrofit rule:** existing certified plans are NOT rewritten just to add the
  fields (byte stability protects review digests); they gain the lines at their
  next natural edit or at revival from deferred/ (which already mandates a
  fresh review round).

## Acceptance criteria

- Every newly authored plan carries the driving-force line (with justification
  when the force is not one of the four principles) and opens its Gist with the
  TLDR line; both appear in the Step 1.4 confirmation.
- The authoring blueprint produces both without extra prompting.
- review-plan flags missing or incoherent declarations; the flags are priced as
  ordinary findings (blocking only when the force contradicts the content).
- No existing certified plan changes bytes solely because of this item.
