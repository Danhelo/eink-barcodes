# E-ink Barcodes Project Guide

## Build & Test Commands
- Setup environment: `./run.sh` (GUI mode) or `./run.sh --cli` (CLI mode)
- Run all tests: `./run_tests.sh`
- Run specific test: `pytest tests/test_file.py::test_function -v`
- Run with coverage: `pytest tests/ --cov=src --cov-report=term`
- Run core test: `python run_core_test.py --rotation <angle> --scale <factor> --delay <seconds>`
- Virtual display mode: Add `--virtual` flag to commands

## Code Style Guidelines
- **Imports**: Standard library → third-party → local (relative)
- **Type hints**: Use typing module (Dict, List, Optional, Callable) consistently
- **Naming**: Classes=PascalCase, functions/variables=snake_case, constants=UPPER_CASE
- **Documentation**: Docstrings for classes/methods, inline comments for complex logic
- **Error handling**: Try-except with detailed messages, proper error propagation
- **Spacing**: 4-space indentation, blank lines between functions and logical sections
- **Architecture**: Maintain core/UI separation, use observer pattern for state changes
- **Async programming**: Use asyncio for display operations, mark tests with @pytest.mark.asyncio
- **Testing**: Write comprehensive tests with proper fixtures, favor unit tests

## Project Structure
Core functionality in src/core/, UI in src/ui/, tests mirror src/ structure