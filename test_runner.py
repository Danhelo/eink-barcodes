#!/usr/bin/env python3
"""
Test runner for E-ink display tests with parallel execution support.
"""
import unittest
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def discover_tests(test_dir: str = 'tests') -> List[unittest.TestSuite]:
    """Discover all tests in the test directory."""
    loader = unittest.TestLoader()
    suites = []

    # Discover test suites
    for path in Path(test_dir).rglob('test_*.py'):
        try:
            relative_path = path.relative_to(Path.cwd())
            module_path = str(relative_path).replace('/', '.').replace('\\', '.')[:-3]
            suite = loader.loadTestsFromName(module_path)
            if suite.countTestCases() > 0:
                suites.append(suite)
                logger.info(f"Discovered {suite.countTestCases()} tests in {module_path}")
        except Exception as e:
            logger.error(f"Error loading tests from {path}: {e}")

    return suites

def run_test_suite(suite: unittest.TestSuite) -> Tuple[int, int, float]:
    """Run a test suite and return results."""
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time

    return (
        len(result.failures),
        len(result.errors),
        duration
    )

def run_tests_parallel(suites: List[unittest.TestSuite], max_workers: Optional[int] = None) -> bool:
    """Run test suites in parallel."""
    total_tests = sum(suite.countTestCases() for suite in suites)
    logger.info(f"Running {total_tests} tests across {len(suites)} suites")

    start_time = time.time()
    failures = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_suite = {
            executor.submit(run_test_suite, suite): suite
            for suite in suites
        }

        for future in future_to_suite:
            suite = future_to_suite[future]
            try:
                suite_failures, suite_errors, duration = future.result()
                failures += suite_failures
                errors += suite_errors

                logger.info(
                    f"Suite {suite} completed in {duration:.2f}s with "
                    f"{suite_failures} failures and {suite_errors} errors"
                )
            except Exception as e:
                logger.error(f"Suite {suite} failed with error: {e}")
                errors += 1

    total_time = time.time() - start_time
    success = failures == 0 and errors == 0

    # Print summary
    logger.info("=" * 70)
    logger.info("Test Summary:")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Failures: {failures}")
    logger.info(f"Errors: {errors}")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info("=" * 70)

    return success

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run E-ink display tests")
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="Directory containing tests"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=None,
        help="Maximum number of parallel test suites"
    )
    parser.add_argument(
        "--pattern",
        default="test_*.py",
        help="Pattern for test files"
    )
    args = parser.parse_args()

    try:
        # Discover tests
        suites = discover_tests(args.test_dir)
        if not suites:
            logger.error("No tests discovered!")
            return 1

        # Run tests
        success = run_tests_parallel(suites, args.parallel)
        return 0 if success else 1

    except KeyboardInterrupt:
        logger.error("Test execution interrupted by user")
        return 2
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 3

if __name__ == "__main__":
    sys.exit(main())
