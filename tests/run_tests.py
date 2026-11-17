import unittest
import sys
import time
import os

# Ensure application package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_all_tests():
    print("=" * 80)
    print("  VEHICLE RENTAL MANAGEMENT SYSTEM (VRMS) - AUTOMATED TEST SUITE")
    print("  Software Engineering Lab (CIC-357) - MAIT, GGSIPU Delhi")
    print("=" * 80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load test cases
    from tests.test_vehicle_operations import TestVehicleOperations
    from tests.test_vrms_integration import TestVRMSIntegration
    from tests.test_data_flow import TestDataFlow
    
    suite.addTests(loader.loadTestsFromTestCase(TestVehicleOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestVRMSIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDataFlow))
    
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed_time = time.time() - start_time
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - (failures + errors)
    success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 80)
    print("                      TEST EXECUTION SUMMARY")
    print("=" * 80)
    print(f" Total Tests Executed : {total_tests}")
    print(f" Passed               : {passed} [PASS]")
    print(f" Failed               : {failures} [FAIL]")
    print(f" Errors               : {errors} [ERROR]")
    print(f" Success Rate         : {success_rate:.1f}%")
    print(f" Total Execution Time : {elapsed_time:.3f} seconds")
    print("-" * 80)
    print(" Test Suite Coverage Breakdown:")
    print("   1. TestVehicleOperations : TC-01..TC-05, ECP, Boundary & Exception tests")
    print("   2. TestVRMSIntegration   : TC-06..TC-08, Booking, Overlap, Rollback & Return")
    print("   3. TestDataFlow          : DF-01..DF-06, DU-Chains & Rate Multiplications")
    print("=" * 80)
    
    if failures == 0 and errors == 0:
        print(" *** ALL TESTS PASSED SUCCESSFULLY! SYSTEM READY FOR DEPLOYMENT ***\n")
        return 0
    else:
        print(" *** SOME TESTS FAILED. CHECK LOGS ABOVE. ***\n")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
