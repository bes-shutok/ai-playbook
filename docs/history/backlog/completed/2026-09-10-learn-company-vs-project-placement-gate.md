# Learn: make company-versus-project placement explicit

Status: done

Completion note (2026-09-12): rider folded into the learn-company-scope-placement plan
(no standalone plan); residual-dependency receipt contract (5c), blocking placement
question, 4c ownership-boundary sentences, generalize entry-4 residual record, done
no-residual stop, and the rider acceptance probes all landed and are green in the plan's
Validation block at execution exit (see docs/plans/completed/2026-09-09-learn-company-scope-placement.md).
Workflow: backlog
Source: anonymized Learn placement review
Severity: Medium
Class: lesson-placement correctness

## Problem

Learn can correctly generalize an incident and identify its root-cause family,
but still place the resulting lesson in the wrong documentation tier. The
current placement guidance distinguishes universal, stack-specific,
cross-project, and project-specific rules, yet it does not force an explicit
company-versus-project decision before writing a project lesson.

This allows a reusable company workflow rule, such as an ownership boundary
between an infrastructure team and an application team, to be recorded in a
single service repository. The rule then looks project-specific because its
witness came from that repository, even though the residual rule does not
depend on that service, domain, language, or framework.

## Location

- `agents/skills/learn/SKILL.md`, placement and generalization workflow
- `agents/skills/generalize/SKILL.md`, routing fork and residual-domain test
- `agents/skills/done/SKILL.md`, project-corpus completion checks, if a final
  placement gate is needed there
- Company guideline path resolved from `company_guidelines_master` in user
  facts

## Suggested fix

Add an explicit placement decision before any project-corpus write:

1. **Company convention:** the rule governs multiple company repositories or
   teams, including ticket ownership, infrastructure boundaries, or shared
   delivery processes. Put the full rule in the canonical company guideline;
   keep only a short project witness or pointer when useful.
2. **Cross-project personal lesson:** the incident pattern is reusable across
   projects but is not a company convention. Put the concrete witness in the
   user-level lessons corpus.
3. **Project-specific lesson:** the rule retains a material dependency on the
   service domain, module contract, repository architecture, or project-only
   operational behavior. Put it in the repository lesson corpus.

Require the placement record to state the residual dependency that makes a
project lesson project-specific. If no such dependency remains, Learn must not
write the full lesson to the project corpus. It should either route the rule to
the company guideline or user-level corpus, or report the missing canonical
destination as a blocking placement question.

The company-scope check should inspect the existing company guideline source
when one is configured, so the workflow can extend or cross-reference an
existing rule instead of creating a duplicate lower-tier lesson.

## Acceptance

- Learn's placement checklist contains a separate company-convention branch
  before the project-specific branch.
- A generic fixture describing a team or infrastructure ownership rule routes
  to the company guideline and does not create a full project lesson.
- A fixture containing a service-only domain invariant still routes to the
  project corpus and records the residual dependency.
- A cross-project incident that is not company policy routes to the user-level
  lessons corpus with the required family tag.
- The workflow preserves a concrete witness through a pointer or short local
  note without duplicating the full canonical rule.
- A self-test or dry-run reports the selected tier and the evidence used for
  the decision.
- The implementation remains project-agnostic and contains no real company,
  service, ticket, customer, or infrastructure identifiers.

## Why not fixed now

The immediate placement correction requires coordinated changes to the Learn
and generalize skills, their self-tests, and possibly the done completion gate.
It should be implemented as a dedicated ai-playbook change so the routing
contract and negative cases can be reviewed together.
