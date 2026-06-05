# Documentation Agent

Review code changes and identify missing documentation updates.

## README / User-Facing Documentation

Must document:
- New features or capabilities
- New CLI flags or command-line options
- New API endpoints or interfaces
- New configuration options
- Changed behavior that affects users
- New dependencies or system requirements
- Breaking changes

Skip:
- Internal refactoring with no user-visible changes
- Bug fixes that restore documented behavior
- Test additions
- Code style changes

## Project Knowledge Base (AGENTS.md, CLAUDE.md, etc.)

Must document:
- New architectural patterns established
- New conventions or coding standards
- New build/test commands
- New libraries or tools integrated
- Project structure changes
- Workflow changes
- Non-obvious debugging techniques

Skip:
- Standard code additions following existing patterns
- Simple bug fixes
- Test additions using existing patterns

## Plan and Tracking Files

If changes relate to an existing plan:
- Mark completed items as done
- Update plan status if needed
- Note which plan items this change addresses

## Module high-level tasks (implementation vs docs drift)

When review finds current code behavior that module docs, BFF contracts, or high-level tasks do not capture (narrower read path than another API, missing edge case, accepted tech debt):

- Flag the owning module high-level tasks file (crm-profile: `docs/profile/profile-service-high-level-tasks.md`, `docs/consent/consent-service-high-level-tasks.md`).
- Recommend a **tech debt** or **implementation fix** bullet under the relevant Task (or Core Concepts), with target task key when known.
- Do not treat gitignored `docs/reviews/` staging as sufficient backlog; high-level tasks is the durable tracker (crm-profile `project-guidelines.md` #77).


Report problems only. No positive observations.
