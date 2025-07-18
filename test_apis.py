#!/usr/bin/env python3

"""
API Integration Test Runner for Regflow
Run this to verify your API credentials are working correctly.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the test runner
from tests.run_tests import run_all_tests

if __name__ == "__main__":
    print("Regflow API Integration Test Suite")
    print("=" * 40)
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Your APIs are ready to use.")
        print("\nYou can now run:")
        print("  uv run regflow domain.com --dry-run")
        print("  uv run regflow domain.com --setup-only")
    else:
        print("\n❌ Some tests failed. Please fix the issues before using the tool.")
        sys.exit(1)