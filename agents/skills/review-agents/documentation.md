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

## Module README vs deployable README scope

When a doc finding covers how modules are composed or wired (Maven dependencies, Modulith `::api` boundaries, `ModuleBoundariesTest`, which module imports which):

- Prefer the **deployable/composition README** (e.g. `app/README.md`) as the comment target or fix location.
- Module READMEs should describe what that module owns and exposes (public API packages, domain boundaries), not duplicate composition mechanics already documented at the app layer.
- If a module README bullet repeats a Module boundaries section plus Modulith syntax, suggest removing the duplicate from the module README rather than expanding it.

## Module high-level tasks (implementation vs docs drift)

When review finds current code behavior that module docs, BFF contracts, or high-level tasks do not capture (narrower read path than another API, missing edge case, accepted tech debt):

- Flag the owning module high-level tasks file. Resolve path from `{guidelines_path}` / project guidelines — do not assume legacy `docs/<module>/` layout on migration-complete repos (legacy pattern: `docs/<module>/<service>-high-level-tasks.md`).
- Recommend a **tech debt** or **implementation fix** bullet under the relevant Task (or Core Concepts), with target task key when known.
- Do not treat gitignored `{reviews_dir}/` staging as sufficient backlog; module high-level tasks docs (path from project guidelines) are the durable tracker.


Report problems only. No positive observations.
