#!/bin/bash
source venv/bin/activate

# Default test to run
TEST_PATH="tests/test_integration.py::TestIntegration::test_summarization_workflow"

# If an argument is provided, use it as the test path
if [ $# -gt 0 ]; then
  TEST_PATH="$1"
fi

echo "Running test: ${TEST_PATH}"
python -m pytest ${TEST_PATH} -v | tee test_output.txt
echo "Test run completed. Results also saved to test_output.txt" 