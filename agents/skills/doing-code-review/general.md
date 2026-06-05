# Language Overlay: General (Fallback)

Additional review context for projects where no specific language overlay matches. Append to each sub-agent prompt.

## Universal Concerns

- **Error handling**: verify all error paths are handled. No silent swallowing of errors without logging.
- **Resource cleanup**: resources (files, connections, handles) must be released in all paths including error paths.
- **Input validation**: all external input validated at the boundary before use.
- **Null/nil safety**: verify null checks exist where values can be absent.
- **Immutability**: prefer immutable data structures for shared state.

## API Design

- **Consistency**: naming, response formats, and error shapes follow existing patterns in the codebase.
- **Backward compatibility**: changes to public APIs do not break existing consumers without versioning.
- **Error responses**: include enough context for the caller to understand and fix the issue.

## Testing

- **Coverage**: new code paths have corresponding tests.
- **Determinism**: tests do not depend on timing, network, or external state.
- **Isolation**: tests clean up after themselves and do not affect other tests.

## Observability

- **Logging**: meaningful log messages at appropriate levels. No sensitive data in logs.
- **Metrics**: key operations are instrumented.
- **Tracing**: correlation IDs propagate across boundaries.

## Documentation

- **User-visible changes** require documentation updates.
- **Internal architecture decisions** should be captured in project knowledge base.
