#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Default settings
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
BACKEND_VENV="$BACKEND_DIR/venv"
DASHBOARD_DIR="$BACKEND_DIR/app/dashboard"
RUN_PYTHON_TESTS=true
RUN_JEST_TESTS=true
VERBOSE=false

# Function to print colored output
log() {
  local color=$1
  local msg=$2
  echo -e "${color}${msg}${NC}"
}

# Function to print section header
print_header() {
  local text=$1
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo -e "${CYAN}${BOLD} $text ${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --python-only)
        RUN_PYTHON_TESTS=true
        RUN_JEST_TESTS=false
        shift
        ;;
      --jest-only)
        RUN_PYTHON_TESTS=false
        RUN_JEST_TESTS=true
        shift
        ;;
      --verbose)
        VERBOSE=true
        shift
        ;;
      --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --python-only    Run only Python tests"
        echo "  --jest-only      Run only Jest tests"
        echo "  --verbose        Show verbose output"
        echo "  --help, -h       Show this help message"
        exit 0
        ;;
      *)
        log $RED "Unknown option: $1"
        echo "Run '$0 --help' for usage information"
        exit 1
        ;;
    esac
  done
}

# Function to run Python tests
run_python_tests() {
  print_header "Running Python Tests"
  
  # Check if Python venv exists
  if [ ! -d "$BACKEND_VENV" ]; then
    log $RED "ERROR: Python virtual environment not found at $BACKEND_VENV"
    log $YELLOW "Please run the startup script first: ./start_svs_application.sh"
    return 1
  fi
  
  # Activate virtual environment
  log $YELLOW "Activating Python virtual environment..."
  source "$BACKEND_VENV/bin/activate"
  
  # Check if pytest is installed
  if ! python -c "import pytest" 2>/dev/null; then
    log $YELLOW "Installing pytest..."
    pip install pytest pytest-cov
  fi
  
  # Find test directories
  log $YELLOW "Looking for Python test directories..."
  
  # Array to store test directories
  test_dirs=()
  
  # Check common test directories
  if [ -d "$BACKEND_DIR/tests" ]; then
    test_dirs+=("$BACKEND_DIR/tests")
  fi
  
  # Check app/tests directory
  if [ -d "$BACKEND_DIR/app/tests" ]; then
    test_dirs+=("$BACKEND_DIR/app/tests")
  fi
  
  # Check for test modules
  for module_dir in "$BACKEND_DIR/app"/*; do
    if [ -d "$module_dir/tests" ]; then
      test_dirs+=("$module_dir/tests")
    fi
  done
  
  # If no test directories found, try to find files
  if [ ${#test_dirs[@]} -eq 0 ]; then
    log $YELLOW "No test directories found. Looking for test files..."
    # Find all files matching test_*.py or *_test.py
    test_files=$(find "$BACKEND_DIR" -name "test_*.py" -o -name "*_test.py")
    
    if [ -z "$test_files" ]; then
      log $RED "No Python test files found."
      return 1
    else
      # Run pytest on individual files
      log $YELLOW "Running tests on individual files..."
      
      if [ "$VERBOSE" = true ]; then
        python -m pytest $test_files -v
      else
        python -m pytest $test_files
      fi
      
      test_result=$?
    fi
  else
    # Run tests in each directory
    log $YELLOW "Found ${#test_dirs[@]} test directories."
    
    test_result=0
    for test_dir in "${test_dirs[@]}"; do
      log $YELLOW "Running tests in $test_dir..."
      
      if [ "$VERBOSE" = true ]; then
        python -m pytest "$test_dir" -v
      else
        python -m pytest "$test_dir"
      fi
      
      # Capture the result but keep running tests
      this_result=$?
      if [ $this_result -ne 0 ]; then
        test_result=1
      fi
    done
  fi
  
  # Deactivate virtual environment
  deactivate
  
  # Final result
  if [ $test_result -eq 0 ]; then
    log $GREEN "All Python tests passed successfully!"
    return 0
  else
    log $RED "Some Python tests failed."
    return 1
  fi
}

# Function to run Jest tests
run_jest_tests() {
  print_header "Running Jest Tests"
  
  # Check for package.json
  if [ ! -f "$DASHBOARD_DIR/package.json" ]; then
    log $YELLOW "Checking alternative locations for package.json..."
    
    # Try finding any package.json with jest in it
    jest_package=$(find "$PROJECT_ROOT" -name "package.json" -exec grep -l "\"jest\":" {} \; | head -n 1)
    
    if [ -z "$jest_package" ]; then
      log $RED "ERROR: No package.json with Jest configuration found"
      log $RED "Jest tests will be skipped"
      return 1
    else
      # Set dashboard dir to the directory containing package.json
      DASHBOARD_DIR=$(dirname "$jest_package")
      log $YELLOW "Found Jest configuration in $DASHBOARD_DIR"
    fi
  fi
  
  # Check if Node.js is installed
  if ! command -v node &> /dev/null; then
    log $RED "ERROR: Node.js is not installed"
    log $RED "Please install Node.js to run Jest tests"
    return 1
  fi
  
  # Check if npm is installed
  if ! command -v npm &> /dev/null; then
    log $RED "ERROR: npm is not installed"
    log $RED "Please install npm to run Jest tests"
    return 1
  fi
  
  # Navigate to dashboard directory
  cd "$DASHBOARD_DIR" || {
    log $RED "ERROR: Could not navigate to $DASHBOARD_DIR"
    return 1
  }
  
  # Check if Jest is installed
  if ! npm list jest &> /dev/null; then
    log $YELLOW "Installing Jest..."
    npm install --no-save jest
  fi
  
  # Run Jest tests
  log $YELLOW "Running Jest tests..."
  
  if [ "$VERBOSE" = true ]; then
    npm test -- --verbose
  else
    npm test
  fi
  
  jest_result=$?
  
  # Navigate back to project root
  cd "$PROJECT_ROOT" || exit
  
  # Final result
  if [ $jest_result -eq 0 ]; then
    log $GREEN "All Jest tests passed successfully!"
    return 0
  else
    log $RED "Some Jest tests failed."
    return 1
  fi
}

# Function to generate test report
generate_report() {
  local python_result=$1
  local jest_result=$2
  
  print_header "SVS Test Report"
  
  echo "Test Run Summary:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  if [ "$RUN_PYTHON_TESTS" = true ]; then
    if [ $python_result -eq 0 ]; then
      echo -e "Python Tests: ${GREEN}PASSED${NC}"
    else
      echo -e "Python Tests: ${RED}FAILED${NC}"
    fi
  else
    echo -e "Python Tests: ${YELLOW}SKIPPED${NC}"
  fi
  
  if [ "$RUN_JEST_TESTS" = true ]; then
    if [ $jest_result -eq 0 ]; then
      echo -e "Jest Tests:   ${GREEN}PASSED${NC}"
    else
      echo -e "Jest Tests:   ${RED}FAILED${NC}"
    fi
  else
    echo -e "Jest Tests:   ${YELLOW}SKIPPED${NC}"
  fi
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  # Overall result
  local overall_result=0
  if [ "$RUN_PYTHON_TESTS" = true ] && [ $python_result -ne 0 ]; then
    overall_result=1
  fi
  
  if [ "$RUN_JEST_TESTS" = true ] && [ $jest_result -ne 0 ]; then
    overall_result=1
  fi
  
  if [ $overall_result -eq 0 ]; then
    log $GREEN "Overall Test Result: PASSED"
    echo ""
    log $GREEN "All tests completed successfully!"
  else
    log $RED "Overall Test Result: FAILED"
    echo ""
    log $RED "Some tests failed. Check the logs above for details."
  fi
  
  return $overall_result
}

# Main function
main() {
  print_header "SVS Test Runner"
  
  # Parse command line arguments
  parse_args "$@"
  
  # Variables to store test results
  python_result=0
  jest_result=0
  
  # Run Python tests if enabled
  if [ "$RUN_PYTHON_TESTS" = true ]; then
    run_python_tests
    python_result=$?
  fi
  
  # Run Jest tests if enabled
  if [ "$RUN_JEST_TESTS" = true ]; then
    run_jest_tests
    jest_result=$?
  fi
  
  # Generate and display report
  generate_report $python_result $jest_result
  exit $?
}

# Run the main function
main "$@" 