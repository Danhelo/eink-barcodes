# E-Ink Barcodes Project Guidelines

## Build & Test Commands
- Install dependencies: `pip install -e .`
- Run all tests: `python -m pytest --verbose --cov=src --cov-report=term-missing -v src/tests/`
- Run single test file: `python -m pytest -v src/tests/path/to/test_file.py`
- Run specific test: `python -m pytest -v src/tests/path/to/test_file.py::TestClass::test_method`
- Code linting: `python -m pylint src/`
- Type checking: `python -m mypy src/`
- Formatting: `python -m black src/`

## Code Style Guidelines
- **Imports**: Group imports by stdlib, third-party, local packages. Use absolute imports.
- **Formatting**: Follow Black code style (line length 88). Use docstrings for all modules, classes, methods.
- **Types**: Use type annotations for function arguments and return values.
- **Naming**: snake_case for variables/functions, PascalCase for classes, constants in UPPER_CASE.
- **Error handling**: Use explicit exception handling with specific exception types. Log errors appropriately.
- **UI Components**: Follow Qt naming conventions for widgets. Always connect signals in initialize methods.
- **Testing**: All new code should have unit tests. Maintain >= 85% code coverage.
- **Documentation**: Include docstrings with Args, Returns, and Raises sections for public APIs.