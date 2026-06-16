#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Main Test Runner
This script runs all the basic tests for the EVIL-JWT-FORCE project.
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def print_header(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def run_command(command, desc=None):
    """Run a shell command and print the output"""
    if desc:
        print(f"\n>> {desc}")
    
    print(f"$ {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, 
                               capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed with exit code {e.returncode}")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    """Main test runner function"""
    start_time = time.time()
    
    print_header("EVIL-JWT-FORCE Test Suite")
    print(f"Starting tests at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Make sure output directory exists
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Keep track of test results
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    # Test 1: JWT Utility Functions
    print_header("Test 1: JWT Utility Functions")
    test_result = run_command("python test_jwt_simple.py", "Testing JWT utility functions")
    results["total"] += 1
    if test_result:
        results["passed"] += 1
        results["tests"].append({"name": "JWT Utility Functions", "result": "PASSED"})
    else:
        results["failed"] += 1
        results["tests"].append({"name": "JWT Utility Functions", "result": "FAILED"})
    
    # Test 2: Wordlist Generation
    print_header("Test 2: Wordlist Generation")
    test_result = run_command("python test_wordlist.py", "Testing wordlist generation")
    results["total"] += 1
    if test_result:
        results["passed"] += 1
        results["tests"].append({"name": "Wordlist Generation", "result": "PASSED"})
    else:
        results["failed"] += 1
        results["tests"].append({"name": "Wordlist Generation", "result": "FAILED"})
    
    # Test 3: Report Generation
    print_header("Test 3: Report Generation")
    test_result = run_command("python test_report.py", "Testing report generation")
    results["total"] += 1
    if test_result:
        results["passed"] += 1
        results["tests"].append({"name": "Report Generation", "result": "PASSED"})
    else:
        results["failed"] += 1
        results["tests"].append({"name": "Report Generation", "result": "FAILED"})
    
    # Test 4: JWT Fuzzing
    print_header("Test 4: JWT Fuzzing")
    test_result = run_command("python test_jwt_fuzzer.py", "Testing JWT fuzzing capabilities")
    results["total"] += 1
    if test_result:
        results["passed"] += 1
        results["tests"].append({"name": "JWT Fuzzing", "result": "PASSED"})
    else:
        results["failed"] += 1
        results["tests"].append({"name": "JWT Fuzzing", "result": "FAILED"})
    
    # Test 5: JWT Bruteforce
    print_header("Test 5: JWT Bruteforce")
    test_result = run_command("python test_jwt_bruteforce.py", "Testing JWT bruteforce capabilities")
    results["total"] += 1
    if test_result:
        results["passed"] += 1
        results["tests"].append({"name": "JWT Bruteforce", "result": "PASSED"})
    else:
        results["failed"] += 1
        results["tests"].append({"name": "JWT Bruteforce", "result": "FAILED"})
    
    # Summary
    elapsed_time = time.time() - start_time
    print_header("Test Summary")
    print(f"Tests completed in {elapsed_time:.2f} seconds")
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    print("\nDetailed results:")
    for test in results["tests"]:
        status = "[PASS]" if test["result"] == "PASSED" else "[FAIL]"
        print(f"  {status} {test['name']}: {test['result']}")
    
    # Output files generated
    print("\nOutput files generated:")
    output_files = [f for f in os.listdir("output") if os.path.isfile(os.path.join("output", f))]
    for file in output_files:
        file_path = os.path.join("output", file)
        file_size = os.path.getsize(file_path)
        print(f"  - {file} ({file_size} bytes)")
    
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 