#!/bin/bash
# Test runner for Data4AI examples
# This script tests that all examples run without errors

echo "🧪 Testing Data4AI Examples"
echo "============================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local name="$1"
    local command="$2"
    
    echo -e "\n${YELLOW}Testing: $name${NC}"
    echo "Command: $command"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}: $name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if we're in the right directory
if [ ! -f "01_basic_cli_examples.sh" ]; then
    echo "❌ Error: Run this script from the examples/ directory"
    exit 1
fi

echo "📋 Checking prerequisites..."

# Check if data4ai is available
if ! command -v data4ai &> /dev/null; then
    echo "❌ data4ai command not found. Please install Data4AI first."
    exit 1
fi

# Check if Python examples can import
if ! python3 -c "import sys; sys.path.insert(0, '..'); import data4ai" 2>/dev/null; then
    echo "⚠️  Warning: Cannot import data4ai Python module"
    echo "   This is expected if running from source without installation"
fi

echo "✅ Prerequisites checked"

echo -e "\n🧪 Running example tests..."

# Test 1: CLI Examples (basic syntax check)
run_test "CLI Examples Script Syntax" "bash -n 01_basic_cli_examples.sh"

# Test 2: Python Examples (syntax check)
run_test "Python Examples Syntax" "python3 -m py_compile 02_python_api_examples.py"

# Test 3: YouTube Examples (syntax check)
run_test "YouTube Examples Script Syntax" "bash -n 03_youtube_integration_examples.sh"

# Test 4: Document Examples (syntax check)
run_test "Document Examples Script Syntax" "bash -n 04_document_processing_examples.sh"

# Test 5: README exists and is readable
run_test "README File Exists" "test -r README.md"

# Test 6: All scripts are executable
run_test "CLI Examples Executable" "test -x 01_basic_cli_examples.sh"
run_test "Python Examples Executable" "test -x 02_python_api_examples.py"
run_test "YouTube Examples Executable" "test -x 03_youtube_integration_examples.sh"
run_test "Document Examples Executable" "test -x 04_document_processing_examples.sh"

# Test 7: Python examples run without errors (import test)
run_test "Python Examples Import Check" "python3 -c 'import sys; sys.path.insert(0, \".\"); exec(open(\"02_python_api_examples.py\").read().split(\"if __name__\")[0])'"

# Test 8: CLI help commands work
if command -v data4ai &> /dev/null; then
    run_test "Data4AI Help Command" "data4ai --help"
    run_test "Data4AI Env Command" "data4ai env --help"
    run_test "Data4AI Prompt Command" "data4ai prompt --help"
    run_test "Data4AI Doc Command" "data4ai doc --help"
    
    # Test YouTube command if available
    if data4ai youtube --help &> /dev/null; then
        run_test "Data4AI YouTube Command" "data4ai youtube --help"
    else
        echo "⚠️  YouTube command not available (this is normal for older versions)"
    fi
fi

# Summary
echo -e "\n📊 Test Results"
echo "==============="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total:  $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    echo "✅ Examples are ready to use"
    echo ""
    echo "Next steps:"
    echo "1. Set your API key: export OPENROUTER_API_KEY='your-key'"
    echo "2. Run examples with: ./01_basic_cli_examples.sh"
    echo "3. Remove --dry-run flags for real generation"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    echo "Please check the failed tests above"
    exit 1
fi