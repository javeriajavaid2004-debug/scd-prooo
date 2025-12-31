import unittest
import sys
import os

def run_all_tests():
    print("========================================")
    print("   Starting Devil Run Automated Tests   ")
    print("========================================")
    
    # Initialize the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests from files
    suite.addTests(loader.discover(start_dir='.', pattern='test_*.py'))
    
    # Initialize the runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(suite)
    
    # Summary
    print("\n========================================")
    print("            Test Summary                ")
    print(f"Tests Run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        print("\nSUCCESS: All tests passed!")
        sys.exit(0)
    else:
        print("\nFAILURE: Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
