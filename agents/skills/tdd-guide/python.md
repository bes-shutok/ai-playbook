# Python TDD Specifics

## Test Execution

- pytest preferred: `pytest path/to/test_file.py -v`
- Run specific test: `pytest path/to/test_file.py::test_function_name`
- Run with keyword: `pytest -k "keyword"`
- Coverage: `pytest --cov=src --cov-report=term-missing`

## Naming Conventions

- Test file: `test_<module>.py`
- Test function: `test_should_do_something_when_condition`
- Test class (optional): `TestClassName`

## Frameworks

- pytest preferred over unittest
- Use `pytest` fixtures for setup/teardown
- `pytest-mock` for mocking (wraps `unittest.mock`)
- `httpx` or `TestClient` (FastAPI) / Django `TestCase` for API tests
- `factory_boy` for test data factories

## Django-Specific

- Use `TestCase` for DB tests, `SimpleTestCase` for non-DB
- `override_settings` decorator for config-dependent tests
- `RequestFactory` for unit-testing views without middleware

## FastAPI-Specific

- Use `TestClient` from `starlette.testclient`
- Override dependencies with `app.dependency_overrides` for isolation
- Use `httpx.AsyncClient` for async endpoint testing
