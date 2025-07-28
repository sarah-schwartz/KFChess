#!/usr/bin/env python3
"""
Test Runner for Victory Timing and Message Display System

This script runs comprehensive tests to verify that:
1. Victory detection waits for pieces to finish moving
2. Victory messages are displayed correctly 
3. Message system integration works properly
4. All timing and fade effects work as expected
"""

import unittest
import sys
import os
from io import StringIO

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_test_suite():
    """Run all tests and return results."""
    print("🧪 Running Victory Timing and Message Display Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test modules
    test_modules = [
        'test_victory_timing',
        'test_message_system_integration', 
        'test_full_system_integration',
        'test_message_display'  # The existing one
    ]
    
    total_tests = 0
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            test_count = module_suite.countTestCases()
            total_tests += test_count
            print(f"✅ Loaded {test_count} tests from {module_name}")
        except ImportError as e:
            print(f"⚠️  Could not load {module_name}: {e}")
    
    print(f"\n📊 Total tests to run: {total_tests}")
    print("-" * 60)
    
    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream, 
        verbosity=2, 
        buffer=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    # Summary
    print("=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✨ Success rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED! Victory timing and message system working correctly.")
        return True
    else:
        print("🚨 SOME TESTS FAILED! Please check the issues above.")
        return False


def run_specific_category(category):
    """Run tests for a specific category."""
    print(f"🎯 Running {category} tests only")
    print("=" * 60)
    
    category_modules = {
        'victory': ['test_victory_timing'],
        'messages': ['test_message_display', 'test_message_system_integration'],
        'integration': ['test_full_system_integration'],
        'basic': ['test_message_display']
    }
    
    if category not in category_modules:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {list(category_modules.keys())}")
        return False
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module_name in category_modules[category]:
        try:
            module = __import__(module_name)
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            print(f"✅ Loaded tests from {module_name}")
        except ImportError as e:
            print(f"⚠️  Could not load {module_name}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def check_system_requirements():
    """Check that all required components are available."""
    print("🔍 Checking system requirements...")
    
    required_modules = [
        'MessageDisplay', 
        'MessageBroker', 
        'EventType', 
        'Game', 
        'GameFactory'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing modules: {missing}")
        print("Please ensure you're running from the correct directory and all files are present.")
        return False
    
    print("✅ All required modules found!")
    return True


if __name__ == '__main__':
    # Check if specific category requested
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        if category in ['victory', 'messages', 'integration', 'basic']:
            if check_system_requirements():
                success = run_specific_category(category)
                sys.exit(0 if success else 1)
        elif category in ['--help', '-h']:
            print("Victory Timing and Message Display Test Runner")
            print("\nUsage:")
            print("  python test_runner.py [category]")
            print("\nCategories:")
            print("  victory     - Victory timing tests only")
            print("  messages    - Message display tests only") 
            print("  integration - Full system integration tests")
            print("  basic       - Basic message display tests")
            print("  (no args)   - Run all tests")
            sys.exit(0)
        else:
            print(f"Unknown category: {category}")
            print("Use --help for available options")
            sys.exit(1)
    
    # Run all tests
    if check_system_requirements():
        success = run_test_suite()
        sys.exit(0 if success else 1)
    else:
        sys.exit(1)
