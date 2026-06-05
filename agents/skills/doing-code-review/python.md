# Language Overlay: Python

Additional review context for Python projects. Append to each sub-agent prompt.

## Python-Specific Concerns

- **Type hints**: verify type annotations are consistent and correct. Flag `Any` used as a shortcut where a concrete type is known.
- **Mutable default arguments**: `def f(items=[])` shares the list across calls. Use `None` with conditional initialization.
- **Exception handling**:
  - Bare `except:` catches `SystemExit` and `KeyboardInterrupt`. Use `except Exception:` at minimum.
  - Overly broad `except Exception: pass` silently swallows errors. Log or re-raise.
  - Exception chaining: use `raise X from Y` to preserve cause.
- **Resource management**: use context managers (`with`) for files, connections, locks. Manual `open()`/`close()` leaks on exceptions.
- **Import side effects**: module-level code executes on import. Heavy initialization (DB connections, HTTP clients) should be lazy or in functions.
- **String formatting**: prefer f-strings for readability. Flag `.format()` or `%` in new code unless there is a reason (logging performance).

## Async Python

- **`async`/`await`**: verify async functions are awaited. Calling without `await` returns a coroutine object that never executes.
- **Blocking in async**: do not call blocking I/O (`requests`, `time.sleep`, file I/O) inside async functions. Use `asyncio.to_thread()` or async libraries.
- **Task cancellation**: verify `asyncio.Task` handles `CancelledError` properly — do not swallow it.

## Framework-Specific (Django/FastAPI/Flask)

- **Django ORM**: watch for N+1 queries. Use `select_related()`/`prefetch_related()`. Verify `QuerySet` evaluation timing.
- **FastAPI**: verify Pydantic models validate input correctly. Check response model does not leak internal fields.
- **Flask**: verify `app.config` secrets are not committed. Check debug mode is disabled in production settings.

## Testing

- **pytest**: verify fixtures have correct scope. `session`-scoped fixtures sharing mutable state between tests is a common bug.
- **Mocking**: `unittest.mock.patch` target must be the import path where the object is used, not where it is defined.
- **Async tests**: use `pytest-asyncio` with `@pytest.mark.asyncio`. Verify test runner supports async fixtures.

## Packaging and Dependencies

- **Virtual environments**: verify `requirements.txt` or `pyproject.toml` pins versions. Unpinned dependencies break reproducibility.
- **Security**: check newly added packages against known vulnerability databases. Verify packages are from PyPI (not typosquatting).

## Observability

- **Logging**: use `logging` module with named loggers. Do not use `print()` for operational output.
- **Structured logging**: prefer `structlog` or JSON formatters for production. Include correlation IDs.
- No PII in logs. System identifiers are not PII.
