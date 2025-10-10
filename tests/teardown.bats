#!/usr/bin/env bats

# Global teardown function - called once after all tests complete
teardown() {
    # Use the unified cleanup script for all cleanup operations (silent full cleanup)
    ./tests/cleanup_test_entries.sh silent "$TEST_CONFIG"
}