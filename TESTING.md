# EVIL-JWT-FORCE Testing Documentation

This document explains the testing structure for the EVIL-JWT-FORCE project, a comprehensive JWT security testing toolkit.

## Test Structure

The project includes multiple test scripts to verify different functionality:

1. **Basic JWT Functions** (`test_jwt_simple.py`): Tests the core JWT utility functions like token generation, decoding, and analysis.

2. **Wordlist Generation** (`test_wordlist.py`): Tests the wordlist generation functionality used for dictionary attacks.

3. **Report Generation** (`test_report.py`): Tests the HTML report generation functionality.

4. **JWT Fuzzing** (`test_jwt_fuzzer.py`): Tests the JWT fuzzing capabilities, creating various mutated tokens to test security vulnerabilities.

5. **JWT Bruteforce** (`test_jwt_bruteforce.py`): Tests the JWT bruteforce functionality to crack JWT tokens with dictionary attacks.

## Running Tests

### Individual Tests

You can run each test individually:

```bash
python test_jwt_simple.py
python test_wordlist.py
python test_report.py
python test_jwt_fuzzer.py
python test_jwt_bruteforce.py
```

### Complete Test Suite

To run all tests at once, use the main test runner:

```bash
python run_tests.py
```

This will execute all the tests in sequence, report their status, and provide a summary at the end.

### Windows Batch File

For Windows users, there's also a batch file for running basic tests:

```bash
run_basic_tests.bat
```

## Test Output

All test results are saved to the `output` directory. Each test generates different output files:

- `test_results.json`: Results from the basic JWT functions test
- `test_wordlist.txt`: Generated wordlist from the wordlist generation test
- `test_report.html`: HTML report from the report generation test
- `jwt_fuzz_test.json`: Results from the JWT fuzzing test
- `jwt_bruteforce_results.json`: Results from the JWT bruteforce test

## Adding New Tests

To add a new test:

1. Create a new test script following the existing pattern
2. Add the test to `run_tests.py` by adding a new test block:

```python
# Test X: New Test
print_header("Test X: New Test")
test_result = run_command("python test_new_feature.py", "Testing new feature")
results["total"] += 1
if test_result:
    results["passed"] += 1
    results["tests"].append({"name": "New Test", "result": "PASSED"})
else:
    results["failed"] += 1
    results["tests"].append({"name": "New Test", "result": "FAILED"})
```

## Dependencies

The tests require the following Python packages:

- PyJWT
- requests
- colorama
- termcolor
- cryptography
- fake-useragent
- simplejson
- dnspython
- validators
- lxml
- aiohttp
- tabulate
- rich
- pyyaml

You can install these with:

```bash
pip install -r requirements.txt
```

## Test Environment

The tests are designed to work in an isolated environment. Before running tests, make sure:

1. The required directories exist (`output`, `logs`, etc.)
2. The required dependencies are installed
3. You have the proper permissions to create files in the output directory

## Test Reports

After running the complete test suite with `run_tests.py`, you'll get a summary showing:

- Total number of tests
- Number of passed tests
- Number of failed tests
- Detailed results for each test
- List of generated output files 