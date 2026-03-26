"""
Performance Test Runner
Run all performance tests with proper setup
"""

import pytest
import sys

if __name__ == "__main__":
    # Run performance tests
    args = [
        "-v",
        "--tb=short",
        "-m", "performance",
        "--disable-warnings",
    ] + sys.argv[1:]

    sys.exit(pytest.main(args))
