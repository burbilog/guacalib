#!/bin/bash

# Enhanced test runner script with comprehensive test counting and result summaries
# Based on the original run_tests.sh but adds test counting and result aggregation

set -e

# Colors for output (fixed for better visibility on black terminals)
RED='\033[0;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Test files in execution order
declare -a TEST_FILES=(
    "tests/test_usergroup.bats"
    "tests/test_usergroup_ids.bats"
    "tests/test_user.bats"
    "tests/test_connection.bats"
    "tests/test_connection_modify.bats"
    "tests/test_conngroup.bats"
    "tests/test_conngroup_addconn_rmconn.bats"
    "tests/test_conngroup_permit_deny.bats"
    "tests/test_ids_feature.bats"
    "tests/test_dump.bats"
)

# Function to count tests in a file
count_tests_in_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        grep -c '^@test' "$file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Main execution
echo -e "${CYAN}=== Guacalib Test Suite Runner with Summary ===${NC}\n"

# Count total tests first
echo -e "${CYAN}Test Count Overview:${NC}"
total_test_count=0
for file in "${TEST_FILES[@]}"; do
    count=$(count_tests_in_file "$file")
    echo -e "${WHITE}$(basename "$file" .bats):${NC} $count tests"
    total_test_count=$((total_test_count + count))
done
echo -e "${CYAN}Total tests to run: $total_test_count${NC}\n"

# Source the setup and teardown functions
source tests/setup.bats
source tests/teardown.bats

# Track results
declare -a RESULTS=()
total_passed=0
total_failed=0

# Run setup once
echo -e "${YELLOW}Setting up test environment...${NC}"
setup

# Run individual test files in order
for file in "${TEST_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        test_name=$(basename "$file" .bats)

        echo -e "\n${YELLOW}=== Running $test_name tests ===${NC}"

        # Run bats with stdout/stderr directly to terminal for real-time output
        # Use stdbuf to unbuffer output if available
        if command -v stdbuf >/dev/null 2>&1; then
            if stdbuf -o0 -e0 bats -t --print-output-on-failure "$file" 2>&1; then
                echo -e "${GREEN}✓ $test_name tests PASSED${NC}"
                RESULTS+=("success:$test_name")
                total_passed=$((total_passed + 1))
            else
                echo -e "${RED}✗ $test_name tests FAILED${NC}"
                RESULTS+=("failed:$test_name")
                total_failed=$((total_failed + 1))
            fi
        else
            # Fallback without stdbuf
            if bats -t --print-output-on-failure "$file"; then
                echo -e "${GREEN}✓ $test_name tests PASSED${NC}"
                RESULTS+=("success:$test_name")
                total_passed=$((total_passed + 1))
            else
                echo -e "${RED}✗ $test_name tests FAILED${NC}"
                RESULTS+=("failed:$test_name")
                total_failed=$((total_failed + 1))
            fi
        fi

        # Add line break for better readability
        echo ""
    else
        echo -e "${RED}Warning: Test file $file not found, skipping...${NC}"
    fi
done

# Run teardown once
echo -e "${YELLOW}Tearing down test environment...${NC}"
teardown

# Run cleanup script to remove any remaining test entries
echo -e "${YELLOW}Running comprehensive cleanup of test entries...${NC}"
./tests/cleanup_test_entries.sh

# Final summary
echo -e "\n${CYAN}=== FINAL TEST SUMMARY ===${NC}"
echo -e "${CYAN}Total test files:${NC} ${#TEST_FILES[@]}"
echo -e "${CYAN}Total individual tests:${NC} $total_test_count"
echo -e "${GREEN}Test files passed:${NC} $total_passed"
echo -e "${RED}Test files failed:${NC} $total_failed"

if [[ $total_failed -eq 0 ]]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    exit 0
else
    echo -e "\n${RED}💥 SOME TESTS FAILED! 💥${NC}"

    # Show failed test details
    echo -e "\n${RED}Failed test files:${NC}"
    for result in "${RESULTS[@]}"; do
        status=$(echo "$result" | cut -d: -f1)
        test_name=$(echo "$result" | cut -d: -f2)
        if [[ "$status" == "failed" ]]; then
            echo -e "  ${RED}✗ $test_name${NC}"
        fi
    done

    exit 1
fi