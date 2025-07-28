#!/usr/bin/env python3
"""
Global test runner for all tests in the KFC_Py project.
Automatically applies mocks to prevent GUI windows and sound playback.
"""

import unittest
import sys
import os
import glob
from pathlib import Path

# Import test mocks first to prevent any GUI/sound issues
import test_mocks

# Add parent directory to path for imports
sys.path.append('..')

def discover_and_run_tests(pattern="test_*.py", exclude_patterns=None):
    """Discover and run all tests matching the pattern."""
    if exclude_patterns is None:
        exclude_patterns = []
    
    print("🔍 Discovering tests...")
    
    # Discover all test files
    test_files = glob.glob(pattern)
    
    # Filter out excluded patterns
    filtered_tests = []
    for test_file in test_files:
        if not any(exclude in test_file for exclude in exclude_patterns):
            filtered_tests.append(test_file)
    
    print(f"📋 Found {len(filtered_tests)} test files:")
    for test_file in filtered_tests:
        print(f"  • {test_file}")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load tests from each file
    successful_loads = 0
    failed_loads = []
    
    for test_file in filtered_tests:
        try:
            # Remove .py extension to get module name
            module_name = test_file[:-3]
            
            # Import the test module
            test_module = __import__(module_name)
            
            # Add tests from the module
            module_suite = loader.loadTestsFromModule(test_module)
            suite.addTest(module_suite)
            successful_loads += 1
            print(f"✓ Loaded tests from {test_file}")
            
        except Exception as e:
            failed_loads.append((test_file, str(e)))
            print(f"✗ Failed to load {test_file}: {e}")
    
    print(f"\n📊 Test loading summary:")
    print(f"  ✓ Successfully loaded: {successful_loads}")
    print(f"  ✗ Failed to load: {len(failed_loads)}")
    
    if failed_loads:
        print(f"\n❌ Failed test files:")
        for test_file, error in failed_loads:
            print(f"  • {test_file}: {error}")
    
    # Run the tests
    print(f"\n🏃 Running tests...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print final summary
    print(f"\n{'='*60}")
    print("GLOBAL TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  • {test}")
            # Print only the last line of the traceback for brevity
            lines = traceback.strip().split('\n')
            if lines:
                print(f"    → {lines[-1]}")
    
    if result.errors:
        print(f"\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  • {test}")
            # Print only the last line of the traceback for brevity
            lines = traceback.strip().split('\n')
            if lines:
                print(f"    → {lines[-1]}")
    
    if result.wasSuccessful():
        print(f"\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n❌ Some tests failed. Check the output above for details.")
        return False

def run_specific_tests(test_names):
    """Run specific test files by name."""
    print(f"🎯 Running specific tests: {', '.join(test_names)}")
    
    # Add .py extension if not present
    test_files = []
    for name in test_names:
        if not name.endswith('.py'):
            name += '.py'
        test_files.append(name)
    
    return discover_and_run_tests(pattern=None, exclude_patterns=[])

def run_quick_tests():
    """Run a quick subset of tests for smoke testing."""
    print("⚡ Running quick test suite...")
    
    quick_tests = [
        'test_sound_manager.py',
        'test_sound_integration.py',
        'test_ui.py'
    ]
    
    return run_specific_tests(quick_tests)

if __name__ == "__main__":
    print("🧪 KFC Chess Global Test Runner")
    print("=" * 50)
    print("🔇 All GUI windows and sounds are mocked")
    print("=" * 50)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            success = run_quick_tests()
        elif sys.argv[1] == "--specific":
            if len(sys.argv) > 2:
                test_names = sys.argv[2:]
                success = run_specific_tests(test_names)
            else:
                print("❌ Please provide test names after --specific")
                sys.exit(1)
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python run_all_tests.py           # Run all tests")
            print("  python run_all_tests.py --quick   # Run quick test suite")
            print("  python run_all_tests.py --specific test1 test2  # Run specific tests")
            sys.exit(0)
        else:
            print(f"❌ Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # Run all tests
        exclude_patterns = ['run_', '__pycache__', 'test_mocks.py']
        success = discover_and_run_tests(exclude_patterns=exclude_patterns)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
